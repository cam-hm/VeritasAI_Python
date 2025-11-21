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
        self.max_retries = max_retries or 3  # Maximum 3 retries as requested
        self.retry_delay = retry_delay or 2.0  # 2.0 seconds between retries
        # Dynamic concurrency: lower for large batches to avoid overwhelming Ollama
        # Will be adjusted based on chunk count
        self.concurrency = concurrency or 2  # Default: 2, but can be adjusted per request
        
        # Use LiteLLM provider (default: ollama)
        # For Ollama, we'll use direct OllamaClient to avoid LiteLLM's random port issues
        self.provider_name = getattr(django_settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
        self.embed_model = getattr(django_settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text')
        
        # For Ollama, prefer direct client over LiteLLM to avoid random port issues
        self.use_direct_ollama = (self.provider_name == 'ollama')
        
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
        
        # Dynamic concurrency: adjust based on total chunks
        # For large files (>200 chunks), use lower concurrency to avoid overwhelming Ollama
        # For smaller files, can use higher concurrency
        if total > 200:
            # Large file: use lower concurrency and longer delays
            effective_concurrency = 1  # Process one at a time for very large files
            batch_delay = 2.0  # Longer delay between batches
        elif total > 100:
            # Medium file: moderate concurrency
            effective_concurrency = 2
            batch_delay = 1.0
        else:
            # Small file: can use higher concurrency
            effective_concurrency = min(self.concurrency, 3)
            batch_delay = 0.5
        
        logger.info(
            f"Embedding configuration for {total} chunks",
            extra={
                'total_chunks': total,
                'concurrency': effective_concurrency,
                'estimated_batches': (total + effective_concurrency - 1) // effective_concurrency,
                'batch_delay': batch_delay,
            }
        )
        
        # Process in batches với dynamic concurrency
        batches = [
            chunks[i:i + effective_concurrency] 
            for i in range(0, total, effective_concurrency)
        ]
        
        # Process batches (no longer need httpx client)
        for batch_idx, batch in enumerate(batches):
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
            
            # Rate limiting: delay between batches (dynamic based on file size)
            # Skip delay for last batch
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(batch_delay)
        
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
                    # Exponential backoff with jitter to avoid thundering herd
                    import random
                    base_delay = self.retry_delay * (2 ** (attempts - 1))
                    jitter = random.uniform(0, 0.3 * base_delay)  # Add up to 30% jitter
                    delay = base_delay + jitter
                    logger.info(f"Retrying embedding after {delay:.2f}s (attempt {attempts + 1}/{self.max_retries})")
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
        Generate single embedding
        - For Ollama: Use direct OllamaClient (avoids LiteLLM random port issues)
        - For other providers: Use LiteLLM
        """
        loop = asyncio.get_event_loop()
        
        # For Ollama, use direct client to avoid LiteLLM's random port issues
        if self.use_direct_ollama:
            try:
                from app.services.ollama_client import get_ollama_client
                ollama_client = get_ollama_client()
                # Run sync embed() in thread pool
                embedding = await loop.run_in_executor(
                    None,
                    lambda: ollama_client.embed(chunk, self.embed_model)
                )
                return embedding
            except Exception as e:
                # If direct OllamaClient fails, try LiteLLM as fallback
                logger.warning(
                    f"Direct OllamaClient failed, trying LiteLLM as fallback",
                    extra={
                        'error': str(e),
                        'chunk_length': len(chunk),
                    }
                )
                try:
                    provider = get_llm_provider(self.provider_name)
                    embedding = await loop.run_in_executor(
                        None,
                        lambda: provider.embed(chunk, self.embed_model)
                    )
                    logger.info("Successfully used LiteLLM fallback")
                    return embedding
                except Exception as fallback_error:
                    logger.error(
                        f"Both OllamaClient and LiteLLM failed",
                        extra={
                            'ollama_error': str(e),
                            'litellm_error': str(fallback_error),
                        }
                    )
                    raise e
        else:
            # For non-Ollama providers, use LiteLLM directly
            try:
                provider = get_llm_provider(self.provider_name)
                embedding = await loop.run_in_executor(
                    None,
                    lambda: provider.embed(chunk, self.embed_model)
                )
                return embedding
            except Exception as e:
                logger.error(
                    f"LiteLLM embedding failed for {self.provider_name}",
                    extra={
                        'error': str(e),
                        'chunk_length': len(chunk),
                    }
                )
                raise e

