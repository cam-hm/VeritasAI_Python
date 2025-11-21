"""
Document Processing Tasks
Tương đương với app/Jobs/ProcessDocument.php trong Laravel

Celery tasks chạy background jobs - tương đương Laravel Queue Jobs
"""

import os
import logging
import time
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings as django_settings
from app.models import Document, DocumentChunk
from app.services.text_extraction_service import TextExtractionService
from app.services.chunking_service import RecursiveChunkingService
from app.services.embedding_service import EmbeddingService
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _check_ollama_health():
    """
    Check if Ollama is available and ready
    Returns True if Ollama is healthy, False otherwise
    """
    try:
        ollama_url = getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        
        # Simple health check - try to list models
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False


def _process_document_internal(document_id: int):
    """
    Internal function để process document (không phải Celery task)
    Được gọi bởi cả Celery task và synchronous processing
    
    Process document: extract text, chunk, generate embeddings
    Tương đương với ProcessDocument::handle() trong Laravel
    
    Args:
        document_id: ID của document cần process
    """
    # No need for django.setup() - Django is already configured
    # when this is called from management command or Celery
    
    try:
        # Get document
        document = Document.objects.get(id=document_id)
        
        # Health check Ollama before processing
        from django.conf import settings as django_settings
        provider = getattr(django_settings, 'DEFAULT_LLM_PROVIDER', 'ollama')
        if provider == 'ollama':
            if not _check_ollama_health():
                error_msg = "Ollama is not available or not responding. Please check if Ollama is running."
                logger.error(error_msg, extra={'document_id': document_id})
                document.status = "failed"
                document.error_message = error_msg
                document.save()
                raise RuntimeError(error_msg)
        
        # Mark as processing
        document.status = "processing"
        document.error_message = None
        document.save()
        
        # Get absolute path
        storage_path = getattr(django_settings, 'STORAGE_PATH', os.path.join(django_settings.BASE_DIR, 'storage'))
        file_path = os.path.join(storage_path, document.path)
        
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg, extra={'document_id': document_id, 'file_path': file_path})
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Processing file: {file_path}", extra={'document_id': document_id})
        
        # Initialize services
        extractor = TextExtractionService()
        chunker = RecursiveChunkingService()
        embedding_service = EmbeddingService()
        
        # Extract text
        logger.info(f"Extracting text from document {document_id}")
        try:
            text = extractor.extract(file_path)
        except Exception as e:
            error_msg = f"Failed to extract text from document: {str(e)}"
            logger.error(error_msg, extra={'document_id': document_id, 'error': str(e)})
            raise RuntimeError(error_msg)
        
        # Validate extracted text
        if not text or len(text.strip()) < 10:
            error_msg = (
                "Failed to extract text from document. "
                "Possible reasons: scanned PDF (needs OCR), encrypted PDF, or corrupted file. "
                f"Extracted only {len(text)} characters."
            )
            logger.error(error_msg, extra={'document_id': document_id})
            raise RuntimeError(error_msg)
        
        logger.info(
            f"Successfully extracted text from document",
            extra={'document_id': document_id, 'text_length': len(text)}
        )
        
        # Chunk text
        logger.info(f"Chunking text for document {document_id}")
        chunks = chunker.chunk(text)
        
        # Prepare chunks for embedding
        chunk_contents = []
        for chunk in chunks:
            chunk_content = chunk.get('content', chunk) if isinstance(chunk, dict) else chunk
            trimmed_chunk = chunk_content.strip()
            if trimmed_chunk and len(trimmed_chunk) >= 5:
                chunk_contents.append(trimmed_chunk)
        
        if not chunk_contents:
            error_msg = (
                f"No valid chunks found after processing document. "
                f"Total chunks: {len(chunks)}, but all were too short (< 5 chars)."
            )
            logger.error(error_msg, extra={'document_id': document_id})
            raise RuntimeError(error_msg)
        
        # Generate embeddings
        logger.info(
            f"Starting batch embedding generation for document {document_id}",
            extra={
                'document_id': document_id,
                'chunk_count': len(chunk_contents),
                'provider': embedding_service.provider_name,
                'model': embedding_service.embed_model,
                'max_retries': embedding_service.max_retries,
            }
        )
        
        # Add small delay before embedding to avoid overwhelming Ollama when multiple docs process simultaneously
        # This helps when multiple documents are uploaded at the same time
        time.sleep(2)  # 2 second delay to stagger requests
        
        try:
            embeddings = embedding_service.generate_embeddings(
                chunk_contents,
                progress_callback=lambda processed, total: logger.info(
                    f"Embedding progress for document {document_id}: {processed}/{total}",
                    extra={
                        'document_id': document_id,
                        'processed': processed,
                        'total': total,
                        'percentage': round((processed / total) * 100, 2),
                    }
                )
            )
        except Exception as e:
            error_msg = f"Failed to generate embeddings after {embedding_service.max_retries} retries: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    'document_id': document_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'chunk_count': len(chunk_contents),
                    'max_retries': embedding_service.max_retries,
                },
                exc_info=True
            )
            raise RuntimeError(error_msg)
        
        # Store chunks with embeddings and pre-computed token counts
        count = 0
        
        # Import token service for pre-computing token counts
        from app.services.token_estimation_service import TokenEstimationService
        token_service = TokenEstimationService()
        
        for index, chunk_content in enumerate(chunk_contents):
            if index < len(embeddings) and embeddings[index]:
                # Pre-compute token count for performance optimization
                token_count = token_service.estimate_tokens(chunk_content)
                
                DocumentChunk.objects.create(
                    document=document,
                    content=chunk_content,
                    embedding=embeddings[index],
                    token_count=token_count,  # Store pre-computed token count
                )
                count += 1
            else:
                logger.warning(
                    f"Missing embedding for chunk",
                    extra={
                        'document_id': document_id,
                        'chunk_index': index,
                    }
                )
        
        if count == 0:
            raise RuntimeError("No chunks were successfully embedded")
        
        # Update document
        document.status = "completed"
        document.num_chunks = count
        document.processed_at = timezone.now()
        document.embedding_model = embedding_service.embed_model
        document.save()
        
        logger.info(
            f"Document processing completed",
            extra={
                'document_id': document_id,
                'chunks_created': count,
            }
        )
        
    except Document.DoesNotExist:
        error_message = f"Document {document_id} not found"
        logger.error(error_message)
        raise ValueError(error_message)
        
    except Exception as e:
        # Update document to failed state
        error_message = str(e)
        if len(error_message) > 10000:
            error_message = error_message[:10000] + "... (truncated)"
        
        try:
            document = Document.objects.get(id=document_id)
            document.status = "failed"
            document.error_message = error_message
            document.save()
        except Exception as update_error:
            logger.error(
                "Failed to update document status after exception",
                extra={
                    'document_id': document_id,
                    'exception': error_message,
                    'update_error': str(update_error),
                }
            )
        
        logger.error(
            "Document processing failed",
            extra={
                'document_id': document_id,
                'error': error_message,
                'exception_class': type(e).__name__,
            }
        )
        
        # Re-raise exception để Celery có thể retry
        raise e


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: int):
    """
    Celery task wrapper - gọi _process_document_internal
    """
    try:
        return _process_document_internal(document_id)
    except Exception as e:
        # Retry nếu còn attempts
        raise self.retry(exc=e, countdown=60)  # Retry sau 60 giây


def process_document_sync(document_id: int):
    """
    Process document synchronously (không dùng Celery)
    Dùng khi Celery không available
    """
    import django
    django.setup()
    return _process_document_internal(document_id)

