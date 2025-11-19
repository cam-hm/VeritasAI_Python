"""
Tests for EmbeddingService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from app.services.embedding_service import EmbeddingService


@pytest.mark.unit
@pytest.mark.services
class TestEmbeddingService:
    """Test EmbeddingService"""
    
    def test_initialization(self):
        """Test service initialization"""
        service = EmbeddingService()
        assert service.batch_size == 10
        assert service.max_retries == 3
        assert service.retry_delay == 1.0
        assert service.concurrency == 5
        assert service.provider_name == 'ollama'
        assert service.embed_model == 'nomic-embed-text'
    
    def test_initialization_custom_config(self):
        """Test service initialization with custom config"""
        service = EmbeddingService(
            batch_size=20,
            max_retries=5,
            retry_delay=2.0,
            concurrency=10
        )
        assert service.batch_size == 20
        assert service.max_retries == 5
        assert service.retry_delay == 2.0
        assert service.concurrency == 10
    
    def test_generate_embeddings_empty_list(self):
        """Test generating embeddings for empty list"""
        service = EmbeddingService()
        result = service.generate_embeddings([])
        assert result == []
    
    def test_generate_embeddings_empty_chunks(self):
        """Test generating embeddings for empty chunks"""
        service = EmbeddingService()
        result = service.generate_embeddings(['', '   ', 'a'])
        # Should filter out empty chunks
        assert len(result) == 0  # 'a' is too short (< 5 chars)
    
    @patch('app.services.embedding_service.get_llm_provider')
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, mock_get_provider):
        """Test generating single embedding"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.embed.return_value = [0.1, 0.2, 0.3]
        mock_get_provider.return_value = mock_provider
        
        service = EmbeddingService()
        result = await service._generate_single_embedding(None, "test chunk")
        
        assert result == [0.1, 0.2, 0.3]
        mock_provider.embed.assert_called_once_with("test chunk", service.embed_model)
    
    @patch('app.services.embedding_service.get_llm_provider')
    @pytest.mark.asyncio
    async def test_generate_single_embedding_with_retry_success(self, mock_get_provider):
        """Test retry logic on success"""
        mock_provider = MagicMock()
        mock_provider.embed.return_value = [0.1, 0.2, 0.3]
        mock_get_provider.return_value = mock_provider
        
        service = EmbeddingService(max_retries=3)
        result = await service._generate_single_embedding_with_retry(None, "test chunk")
        
        assert result == [0.1, 0.2, 0.3]
        assert mock_provider.embed.call_count == 1
    
    @patch('app.services.embedding_service.get_llm_provider')
    @pytest.mark.asyncio
    async def test_generate_single_embedding_with_retry_failure_then_success(self, mock_get_provider):
        """Test retry logic on failure then success"""
        mock_provider = MagicMock()
        mock_provider.embed.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            [0.1, 0.2, 0.3]  # Success on third try
        ]
        mock_get_provider.return_value = mock_provider
        
        service = EmbeddingService(max_retries=3, retry_delay=0.01)
        result = await service._generate_single_embedding_with_retry(None, "test chunk")
        
        assert result == [0.1, 0.2, 0.3]
        assert mock_provider.embed.call_count == 3
    
    @patch('app.services.embedding_service.get_llm_provider')
    @pytest.mark.asyncio
    async def test_generate_single_embedding_with_retry_all_fail(self, mock_get_provider):
        """Test retry logic when all attempts fail"""
        mock_provider = MagicMock()
        mock_provider.embed.side_effect = Exception("Always fails")
        mock_get_provider.return_value = mock_provider
        
        service = EmbeddingService(max_retries=2, retry_delay=0.01)
        
        with pytest.raises(RuntimeError, match="Failed to generate embedding after 2 attempts"):
            await service._generate_single_embedding_with_retry(None, "test chunk")
        
        assert mock_provider.embed.call_count == 2
    
    @patch('app.services.embedding_service.get_llm_provider')
    @pytest.mark.asyncio
    async def test_generate_embeddings_async_batch(self, mock_get_provider):
        """Test generating embeddings for batch"""
        # Mock provider
        mock_provider = MagicMock()
        mock_provider.embed.side_effect = [
            [0.1, 0.2],  # First chunk
            [0.3, 0.4],  # Second chunk
            [0.5, 0.6]   # Third chunk
        ]
        mock_get_provider.return_value = mock_provider
        
        service = EmbeddingService(concurrency=2)
        chunks = ["chunk1", "chunk2", "chunk3"]
        result = await service._generate_embeddings_async(chunks)
        
        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert result[2] == [0.5, 0.6]
    
    @patch('app.services.embedding_service.get_llm_provider')
    def test_generate_embeddings_with_progress_callback(self, mock_get_provider):
        """Test generating embeddings with progress callback"""
        mock_provider = MagicMock()
        mock_provider.embed.return_value = [0.1, 0.2]
        mock_get_provider.return_value = mock_provider
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        service = EmbeddingService(concurrency=2)
        chunks = ["chunk1", "chunk2", "chunk3"]
        result = service.generate_embeddings(chunks, progress_callback=progress_callback)
        
        assert len(result) == 3
        assert len(progress_calls) > 0
        # Check that progress was reported
        assert progress_calls[-1][0] == 3  # All processed
        assert progress_calls[-1][1] == 3  # Total
    
    def test_generate_embeddings_filters_short_chunks(self):
        """Test that short chunks are filtered out"""
        service = EmbeddingService()
        chunks = ["", "   ", "ab", "valid chunk with enough text"]
        
        # Should only process chunks with >= 5 characters
        with patch.object(service, '_generate_embeddings_async', return_value=[[0.1, 0.2]]):
            result = service.generate_embeddings(chunks)
            # Only 1 valid chunk
            assert len(result) == 1

