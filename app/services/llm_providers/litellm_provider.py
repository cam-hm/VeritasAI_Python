"""
LiteLLM Provider - Unified interface for all LLM providers
LiteLLM supports 100+ providers with unified API
"""

from typing import List, Dict, Optional, Iterator, Union
from django.conf import settings
from .base import LLMProvider

try:
    import litellm
    from litellm import completion, embedding
except ImportError:
    raise ImportError("LiteLLM is not installed. Run: pip install litellm")


class LiteLLMProvider(LLMProvider):
    """
    LiteLLM provider implementation
    Supports all providers that LiteLLM supports:
    - openai, anthropic, deepseek, together, groq, etc.
    - ollama (local)
    """
    
    def __init__(
        self,
        provider_name: str,
        default_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize LiteLLM provider
        
        Args:
            provider_name: 'openai', 'deepseek', 'together', 'ollama', etc.
            default_model: Default chat model (e.g., 'gpt-4', 'deepseek-chat')
            embed_model: Default embedding model
            api_key: API key (from settings if not provided)
            base_url: Custom base URL (for OpenAI-compatible APIs)
        """
        self.provider_name = provider_name.lower()
        self.default_model = default_model or self._get_default_model()
        self.embed_model = embed_model or self._get_default_embed_model()
        
        # Set API key from settings if not provided
        if api_key:
            self._set_api_key(api_key)
        else:
            self._load_api_key_from_settings()
        
        # Set base URL for OpenAI-compatible providers
        if base_url:
            self._set_base_url(base_url)
        elif self.provider_name == 'ollama':
            # For Ollama, set base URL from settings
            self._set_ollama_base_url()
    
    def _get_default_model(self) -> str:
        """Get default model based on provider"""
        defaults = {
            'ollama': 'llama3.1',
            'openai': 'gpt-3.5-turbo',
            'deepseek': 'deepseek-chat',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'together': 'meta-llama/Llama-2-70b-chat-hf',
            'groq': 'llama-3.1-70b-versatile',
        }
        return defaults.get(self.provider_name, 'gpt-3.5-turbo')
    
    def _get_default_embed_model(self) -> str:
        """Get default embedding model based on provider"""
        defaults = {
            'ollama': 'nomic-embed-text',
            'openai': 'text-embedding-3-small',
            'anthropic': None,  # Anthropic doesn't have embeddings
            'deepseek': None,  # DeepSeek doesn't have embeddings
        }
        return defaults.get(self.provider_name)
    
    def _load_api_key_from_settings(self):
        """Load API key from Django settings"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'groq': 'GROQ_API_KEY',
        }
        
        if self.provider_name in key_mapping:
            key_name = key_mapping[self.provider_name]
            api_key = getattr(settings, key_name, None)
            if api_key:
                self._set_api_key(api_key)
    
    def _set_api_key(self, api_key: str):
        """Set API key in environment for LiteLLM"""
        import os
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'groq': 'GROQ_API_KEY',
        }
        
        if self.provider_name in key_mapping:
            env_key = key_mapping[self.provider_name]
            os.environ[env_key] = api_key
    
    def _set_base_url(self, base_url: str):
        """Set custom base URL for OpenAI-compatible providers"""
        if self.provider_name in ['openai', 'deepseek', 'together']:
            # LiteLLM uses custom_llm_provider for custom base URLs
            # This is handled in the model name format: "custom_provider/model_name"
            pass  # Will be handled in model name
    
    def _set_ollama_base_url(self):
        """Set Ollama base URL for LiteLLM"""
        import os
        from django.conf import settings as django_settings
        ollama_url = getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        # Set environment variable for LiteLLM to use
        os.environ['OLLAMA_API_BASE'] = ollama_url
        # Also set in litellm config
        import litellm
        if not hasattr(litellm, '_ollama_base_url_set'):
            litellm.api_base = ollama_url
            litellm._ollama_base_url_set = True
    
    @property
    def provider_name(self) -> str:
        return self._provider_name
    
    @provider_name.setter
    def provider_name(self, value: str):
        self._provider_name = value
    
    def _format_model_name(self, model: Optional[str] = None) -> str:
        """
        Format model name for LiteLLM
        Format: "provider/model_name" for most providers
        """
        model = model or self.default_model
        
        # For Ollama, LiteLLM uses format: "ollama/model_name"
        if self.provider_name == 'ollama':
            return f"ollama/{model}"
        
        # For other providers, LiteLLM auto-detects from model name
        # But we can explicitly specify provider if needed
        # Format: "provider/model" or just "model" (LiteLLM will auto-detect)
        return model
    
    def embed(
        self,
        prompt: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """Generate embedding(s) using LiteLLM"""
        model = model or self.embed_model
        if not model:
            raise ValueError(f"Embedding model not configured for provider: {self.provider_name}")
        
        # Format model name
        formatted_model = self._format_model_name(model)
        
        # Call LiteLLM embedding with error handling and timeout
        try:
            import litellm
            import os
            from django.conf import settings as django_settings
            
            # Set timeout for Ollama (default is 60s, but can be too short for large chunks)
            original_timeout = getattr(litellm, 'request_timeout', 60)
            if self.provider_name == 'ollama':
                litellm.request_timeout = 120  # 2 minutes for Ollama
                # Ensure Ollama base URL is set - this is critical for correct connection
                ollama_url = getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
                # Set environment variable for LiteLLM
                os.environ['OLLAMA_API_BASE'] = ollama_url
                # Also pass api_base explicitly in embedding call to ensure correct URL
                # This prevents LiteLLM from using random internal ports
                response = embedding(
                    model=formatted_model,
                    input=prompt,
                    api_base=ollama_url
                )
            else:
                response = embedding(
                    model=formatted_model,
                    input=prompt
                )
            
            # Restore original timeout
            if self.provider_name == 'ollama':
                litellm.request_timeout = original_timeout
                
        except Exception as e:
            # Log detailed error for debugging
            import logging
            logger = logging.getLogger(__name__)
            error_msg = str(e)
            logger.error(
                f"LiteLLM embedding failed",
                extra={
                    'model': formatted_model,
                    'provider': self.provider_name,
                    'error': error_msg,
                    'error_type': type(e).__name__,
                    'prompt_length': len(prompt) if isinstance(prompt, str) else len(str(prompt)),
                },
                exc_info=True
            )
            # Provide more helpful error message
            from django.conf import settings as django_settings
            ollama_url = getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
            
            if 'EOF' in error_msg or 'Connection' in error_msg or 'refused' in error_msg.lower():
                raise RuntimeError(f"Connection to Ollama failed. Please check if Ollama is running at {ollama_url}. Error: {error_msg}")
            elif '500' in error_msg or 'Internal Server Error' in error_msg:
                raise RuntimeError(f"Ollama server error. The model '{model}' may not be available or Ollama is experiencing issues. Error: {error_msg}")
            elif 'timeout' in error_msg.lower():
                raise RuntimeError(f"Request timeout. The embedding request took too long. Try reducing chunk size or check Ollama performance.")
            else:
                raise RuntimeError(f"Failed to generate embedding: {error_msg}")
        
        # Handle different response formats from LiteLLM
        # LiteLLM may return object or dict depending on provider
        if isinstance(response, dict):
            # Dict format (some providers)
            data = response.get('data', [])
            if isinstance(prompt, str):
                # Single embedding
                if len(data) > 0:
                    return data[0].get('embedding', [])
                return []
            else:
                # Batch embeddings
                return [item.get('embedding', []) for item in data]
        else:
            # Object format (OpenAI-compatible)
            data = response.data if hasattr(response, 'data') else []
            if isinstance(prompt, str):
                # Single embedding
                if len(data) > 0:
                    item = data[0]
                    # Handle both object and dict
                    if hasattr(item, 'embedding'):
                        return item.embedding
                    elif isinstance(item, dict):
                        return item.get('embedding', [])
                return []
            else:
                # Batch embeddings
                embeddings = []
                for item in data:
                    if hasattr(item, 'embedding'):
                        embeddings.append(item.embedding)
                    elif isinstance(item, dict):
                        embeddings.append(item.get('embedding', []))
                return embeddings
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Union[Dict, Iterator[Dict]]:
        """Chat using LiteLLM"""
        model = self._format_model_name(model)
        
        # Prepare parameters
        params = {
            'model': model,
            'messages': messages,
            'stream': stream
        }
        
        if temperature is not None:
            params['temperature'] = temperature
        
        if max_tokens is not None:
            params['max_tokens'] = max_tokens
        
        if stream:
            return self._chat_stream(params)
        else:
            response = completion(**params)
            # Convert to dict format
            return {
                'id': response.id if hasattr(response, 'id') else None,
                'choices': [{
                    'message': {
                        'role': choice.message.role if hasattr(choice.message, 'role') else 'assistant',
                        'content': choice.message.content if hasattr(choice.message, 'content') else ''
                    }
                } for choice in response.choices]
            }
    
    def _chat_stream(self, params: Dict) -> Iterator[Dict]:
        """Handle streaming chat responses"""
        response = completion(**params)
        
        for chunk in response:
            # Convert chunk to dict format compatible with OpenAI format
            chunk_dict = {
                'id': chunk.id if hasattr(chunk, 'id') else None,
                'choices': []
            }
            
            if hasattr(chunk, 'choices') and chunk.choices:
                for choice in chunk.choices:
                    delta_content = ''
                    if hasattr(choice, 'delta'):
                        if hasattr(choice.delta, 'content'):
                            delta_content = choice.delta.content or ''
                        elif isinstance(choice.delta, dict):
                            delta_content = choice.delta.get('content', '')
                    
                    chunk_dict['choices'].append({
                        'delta': {
                            'content': delta_content
                        }
                    })
            
            yield chunk_dict
    
    def list_models(self) -> List[Dict]:
        """List available models (LiteLLM doesn't have a unified list_models)"""
        # Return default models for this provider
        defaults = {
            'ollama': [
                {'id': 'llama3.1', 'name': 'Llama 3.1'},
                {'id': 'mistral', 'name': 'Mistral'},
            ],
            'openai': [
                {'id': 'gpt-4', 'name': 'GPT-4'},
                {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo'},
            ],
            'deepseek': [
                {'id': 'deepseek-chat', 'name': 'DeepSeek Chat'},
                {'id': 'deepseek-coder', 'name': 'DeepSeek Coder'},
            ],
        }
        return defaults.get(self.provider_name, [])

