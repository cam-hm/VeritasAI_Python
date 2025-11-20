"""
Tests for LLM Providers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.llm_providers import LLMProviderFactory, LiteLLMProvider
from app.services.llm_providers.base import LLMProvider


@pytest.mark.unit
@pytest.mark.services
class TestLLMProviderFactory:
    """Test LLMProviderFactory"""
    
    def test_register_provider(self):
        """Test registering a provider"""
        class TestProvider(LLMProvider):
            @property
            def provider_name(self):
                return 'test'
            
            def embed(self, prompt, model=None):
                pass
            
            def chat(self, messages, model=None, stream=False, **kwargs):
                pass
            
            def list_models(self):
                pass
        
        LLMProviderFactory.register('test', TestProvider)
        assert 'test' in LLMProviderFactory._providers
    
    def test_create_provider(self):
        """Test creating a provider instance"""
        provider = LLMProviderFactory.create('ollama')
        assert isinstance(provider, LiteLLMProvider)
        assert provider.provider_name == 'ollama'
    
    def test_create_invalid_provider(self):
        """Test creating invalid provider raises error"""
        with pytest.raises(ValueError, match="Provider 'invalid' not found"):
            LLMProviderFactory.create('invalid')
    
    def test_get_default_provider(self):
        """Test getting default provider"""
        provider = LLMProviderFactory.get_default()
        assert isinstance(provider, LiteLLMProvider)


@pytest.mark.unit
@pytest.mark.services
class TestLiteLLMProvider:
    """Test LiteLLMProvider"""
    
    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = LiteLLMProvider(provider_name='ollama')
        assert provider.provider_name == 'ollama'
        assert provider.default_model == 'llama3.1'
        assert provider.embed_model == 'nomic-embed-text'
    
    def test_provider_initialization_openai(self):
        """Test OpenAI provider initialization"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = LiteLLMProvider(
                provider_name='openai',
                api_key='test-key'
            )
            assert provider.provider_name == 'openai'
            assert provider.default_model == 'gpt-3.5-turbo'
            assert provider.embed_model == 'text-embedding-3-small'
    
    def test_format_model_name_ollama(self):
        """Test model name formatting for Ollama"""
        provider = LiteLLMProvider(provider_name='ollama')
        formatted = provider._format_model_name('llama3.1')
        assert formatted == 'ollama/llama3.1'
    
    def test_format_model_name_openai(self):
        """Test model name formatting for OpenAI"""
        provider = LiteLLMProvider(provider_name='openai')
        formatted = provider._format_model_name('gpt-4')
        assert formatted == 'gpt-4'  # No prefix needed
    
    def test_list_models(self):
        """Test listing models"""
        provider = LiteLLMProvider(provider_name='ollama')
        models = provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'id' in models[0]
    
    @patch('app.services.llm_providers.litellm_provider.embedding')
    def test_embed_single(self, mock_embedding):
        """Test embedding single text (object format)"""
        # Mock LiteLLM response (object format)
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_embedding.return_value = mock_response
        
        provider = LiteLLMProvider(provider_name='ollama')
        result = provider.embed("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_embedding.assert_called_once()
    
    @patch('app.services.llm_providers.litellm_provider.embedding')
    def test_embed_single_dict_format(self, mock_embedding):
        """Test embedding single text (dict format)"""
        # Mock LiteLLM response (dict format)
        mock_embedding.return_value = {
            'data': [{'embedding': [0.1, 0.2, 0.3]}]
        }
        
        provider = LiteLLMProvider(provider_name='ollama')
        result = provider.embed("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_embedding.assert_called_once()
    
    @patch('app.services.llm_providers.litellm_provider.embedding')
    def test_embed_batch(self, mock_embedding):
        """Test embedding batch texts (object format)"""
        # Mock LiteLLM response (object format)
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4])
        ]
        mock_embedding.return_value = mock_response
        
        provider = LiteLLMProvider(provider_name='ollama')
        result = provider.embed(["text1", "text2"])
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
    
    @patch('app.services.llm_providers.litellm_provider.embedding')
    def test_embed_batch_dict_format(self, mock_embedding):
        """Test embedding batch texts (dict format)"""
        # Mock LiteLLM response (dict format)
        mock_embedding.return_value = {
            'data': [
                {'embedding': [0.1, 0.2]},
                {'embedding': [0.3, 0.4]}
            ]
        }
        
        provider = LiteLLMProvider(provider_name='ollama')
        result = provider.embed(["text1", "text2"])
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
    
    def test_embed_no_model(self):
        """Test embedding without model raises error"""
        provider = LiteLLMProvider(
            provider_name='deepseek',
            embed_model=None
        )
        
        with pytest.raises(ValueError, match="Embedding model not configured"):
            provider.embed("test")
    
    @patch('app.services.llm_providers.litellm_provider.completion')
    def test_chat_non_stream(self, mock_completion):
        """Test non-streaming chat"""
        # Mock LiteLLM response
        mock_response = MagicMock()
        mock_response.id = 'test-id'
        mock_choice = MagicMock()
        mock_choice.message.role = 'assistant'
        mock_choice.message.content = 'Hello!'
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response
        
        provider = LiteLLMProvider(provider_name='ollama')
        messages = [{'role': 'user', 'content': 'Hi'}]
        result = provider.chat(messages, stream=False)
        
        assert result['id'] == 'test-id'
        assert len(result['choices']) == 1
        assert result['choices'][0]['message']['content'] == 'Hello!'
    
    @patch('app.services.llm_providers.litellm_provider.completion')
    def test_chat_stream(self, mock_completion):
        """Test streaming chat"""
        # Mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.id = 'chunk1'
        mock_chunk1.choices = [MagicMock(delta=MagicMock(content='Hello'))]
        
        mock_chunk2 = MagicMock()
        mock_chunk2.id = 'chunk2'
        mock_chunk2.choices = [MagicMock(delta=MagicMock(content=' World'))]
        
        mock_completion.return_value = iter([mock_chunk1, mock_chunk2])
        
        provider = LiteLLMProvider(provider_name='ollama')
        messages = [{'role': 'user', 'content': 'Hi'}]
        result = list(provider.chat(messages, stream=True))
        
        assert len(result) == 2
        assert result[0]['choices'][0]['delta']['content'] == 'Hello'
        assert result[1]['choices'][0]['delta']['content'] == ' World'
    
    @patch('app.services.llm_providers.litellm_provider.completion')
    def test_chat_with_parameters(self, mock_completion):
        """Test chat with temperature and max_tokens"""
        mock_response = MagicMock()
        mock_response.id = 'test-id'
        mock_response.choices = [MagicMock(message=MagicMock(role='assistant', content='Response'))]
        mock_completion.return_value = mock_response
        
        provider = LiteLLMProvider(provider_name='ollama')
        messages = [{'role': 'user', 'content': 'Hi'}]
        provider.chat(
            messages,
            model='llama3.1',
            temperature=0.8,
            max_tokens=1000
        )
        
        # Verify completion was called with correct parameters
        call_args = mock_completion.call_args
        assert call_args[1]['temperature'] == 0.8
        assert call_args[1]['max_tokens'] == 1000

