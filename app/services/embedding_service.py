"""
Embedding Service
Tương đương với app/Services/EmbeddingService.php trong Laravel

Generate embeddings cho text chunks sử dụng Ollama hoặc OpenAI
"""

import asyncio
import httpx
from typing import List, Callable, Optional
import logging
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service để generate embeddings cho text chunks
    Tương đương với EmbeddingService trong Laravel
    
    Trong Laravel:
    - Sử dụng Camh\Ollama\Facades\Ollama
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
        self.concurrency = concurrency or 5
        self.ollama_base = getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        self.embed_model = getattr(django_settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text')
    
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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for batch in batches:
                # Create tasks cho batch
                tasks = [
                    self._generate_single_embedding_with_retry(client, chunk)
                    for chunk in batch
                ]
                
                # Execute concurrently
                batch_embeddings = await asyncio.gather(*tasks)
                embeddings.extend(batch_embeddings)
                
                processed += len(batch)
                if progress_callback:
                    progress_callback(processed, total)
                
                # Rate limiting: small delay between batches
                if batch != batches[-1]:
                    await asyncio.sleep(0.05)
        
        return embeddings
    
    async def _generate_single_embedding_with_retry(
        self,
        client: httpx.AsyncClient,
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
                    await asyncio.sleep(self.retry_delay)
        
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
        client: httpx.AsyncClient,
        chunk: str
    ) -> List[float]:
        """
        Generate single embedding từ Ollama API
        Tương đương với Ollama::embed($chunk) trong Laravel
        """
        url = f"{self.ollama_base}/api/embeddings"
        payload = {
            "model": self.embed_model,
            "prompt": chunk,
        }
        
        response = await client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "embedding" in data and isinstance(data["embedding"], list):
            return data["embedding"]
        else:
            raise ValueError(f"Invalid embedding response structure: {data}")

