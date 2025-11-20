"""
Embedding Service
Tương đương với app/Services/EmbeddingService.php trong Laravel

Generate embeddings cho text chunks sử dụng LiteLLM (supports multiple providers)
"""

import asyncio
from typing import List, Callable, Optional
import logging
from django.conf import settings as django_settings
from .llm_service import get_llm_provider

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service để generate embeddings cho text chunks
    Tương đương với EmbeddingService trong Laravel
    
    Trong Laravel:
    - Sử dụng Camh\\Ollama\\Facades\\Ollama
    - Batch processing với parallel HTTP requests
    - Retry logic
    
    Trong Python:
    - Sử dụng httpx cho async HTTP requests
    - asyncio cho concurrent processing
    """
    
    def __init__(
        self,
        batch_size: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        concurrency: Optional[int] = None
    ):
        """
        Initialize service với config
        Tương đương với constructor trong Laravel EmbeddingService
        """
        self.batch_size = batch_size or 10
        self.max_retries = max_retries or 3
        self.retry_delay = retry_delay or 1.0
        self.concurrency = concurrency or 3  # Reduced from 5 to avoid overwhelming Ollama
        
        # Use LiteLLM provider (default: ollama)
        self.provider_name = getattr(django_settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
        self.embed_model = getattr(django_settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text')
        
        # Log configuration for debugging
        logger.info(
            f"EmbeddingService initialized",
            extra={
                'provider': self.provider_name,
                'model': self.embed_model,
                'base_url': getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
            }
        )
    
    def generate_embeddings(
        self, 
        chunks: List[str], 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Generate embeddings cho multiple chunks trong parallel batches
        
        Args:
            chunks: List of chunk content strings
            progress_callback: Optional callback cho progress updates (current, total)
            
        Returns:
            List of embeddings trong cùng order với input chunks
        """
        if not chunks:
            return []
        
        # Filter out empty chunks
        valid_chunks = [
            chunk for chunk in chunks 
            if chunk and chunk.strip() and len(chunk.strip()) >= 5
        ]
        
        if not valid_chunks:
            return []
        
        # Sử dụng async để generate embeddings
        return asyncio.run(self._generate_embeddings_async(valid_chunks, progress_callback))
    
    async def _generate_embeddings_async(
        self,
        chunks: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Async function để generate embeddings
        """
        total = len(chunks)
        embeddings = []
        processed = 0
        
        # Process in batches với concurrency limit
        batches = [
            chunks[i:i + self.concurrency] 
            for i in range(0, total, self.concurrency)
        ]
        
        # Process batches (no longer need httpx client)
        for batch in batches:
            # Create tasks cho batch
            tasks = [
                self._generate_single_embedding_with_retry(None, chunk)
                for chunk in batch
            ]
            
            # Execute concurrently
            batch_embeddings = await asyncio.gather(*tasks)
            embeddings.extend(batch_embeddings)
            
            processed += len(batch)
            if progress_callback:
                progress_callback(processed, total)
            
            # Rate limiting: delay between batches to avoid overwhelming Ollama
            if batch != batches[-1]:
                await asyncio.sleep(0.2)  # Increased from 0.05 to 0.2
        
        return embeddings
    
    async def _generate_single_embedding_with_retry(
        self,
        client,  # Kept for compatibility but not used
        chunk: str
    ) -> List[float]:
        """
        Generate single embedding với retry logic
        """
        attempts = 0
        last_exception = None
        
        while attempts < self.max_retries:
            try:
                return await self._generate_single_embedding(client, chunk)
            except Exception as e:
                attempts += 1
                last_exception = e
                logger.warning(
                    f"Embedding attempt {attempts} failed",
                    extra={
                        'error': str(e),
                        'chunk_length': len(chunk),
                    }
                )
                
                if attempts < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** (attempts - 1))
                    logger.info(f"Retrying embedding after {delay}s (attempt {attempts + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
        
        # Nếu tất cả retries failed
        logger.error(
            'Failed to generate embedding after all retries',
            extra={
                'chunk_length': len(chunk),
                'error': str(last_exception) if last_exception else 'Unknown error',
            }
        )
        
        raise RuntimeError(
            f"Failed to generate embedding after {self.max_retries} attempts: "
            f"{str(last_exception) if last_exception else 'Unknown error'}"
        )
    
    async def _generate_single_embedding(
        self,
        client,  # Kept for compatibility but not used
        chunk: str
    ) -> List[float]:
        """
        Generate single embedding sử dụng LiteLLM provider
        Tương đương với Ollama::embed($chunk) trong Laravel
        
        Note: Sử dụng LiteLLM để support multiple providers
        """
        # Use LiteLLM provider (sync call in async context)
        # LiteLLM embed() is synchronous, so we run it in executor
        loop = asyncio.get_event_loop()
        provider = get_llm_provider(self.provider_name)
        
        # Run sync embed() in thread pool
        embedding = await loop.run_in_executor(
            None,
            lambda: provider.embed(chunk, self.embed_model)
        )
        
        return embedding

