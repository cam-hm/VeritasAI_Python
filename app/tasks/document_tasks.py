"""
Document Processing Tasks
Tương đương với app/Jobs/ProcessDocument.php trong Laravel

Celery tasks chạy background jobs - tương đương Laravel Queue Jobs
"""

import os
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings as django_settings
from app.models import Document, DocumentChunk
from app.services.text_extraction_service import TextExtractionService
from app.services.chunking_service import RecursiveChunkingService
from app.services.embedding_service import EmbeddingService
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _process_document_internal(document_id: int):
    """
    Internal function để process document (không phải Celery task)
    Được gọi bởi cả Celery task và synchronous processing
    
    Process document: extract text, chunk, generate embeddings
    Tương đương với ProcessDocument::handle() trong Laravel
    
    Args:
        document_id: ID của document cần process
    """
    # Import Django models và setup
    import django
    django.setup()
    
    try:
        # Get document
        document = Document.objects.get(id=document_id)
        
        # Mark as processing
        document.status = "processing"
        document.error_message = None
        document.save()
        
        # Get absolute path
        storage_path = getattr(django_settings, 'STORAGE_PATH', os.path.join(django_settings.BASE_DIR, 'storage'))
        file_path = os.path.join(storage_path, document.path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Initialize services
        extractor = TextExtractionService()
        chunker = RecursiveChunkingService()
        embedding_service = EmbeddingService()
        
        # Extract text
        logger.info(f"Extracting text from document {document_id}")
        text = extractor.extract(file_path)
        
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
            raise RuntimeError("No valid chunks found after processing document")
        
        # Generate embeddings
        logger.info(
            f"Starting batch embedding generation for document {document_id}",
            extra={
                'document_id': document_id,
                'chunk_count': len(chunk_contents),
            }
        )
        
        embeddings = embedding_service.generate_embeddings(
            chunk_contents,
            progress_callback=lambda processed, total: logger.debug(
                f"Embedding progress for document {document_id}",
                extra={
                    'document_id': document_id,
                    'processed': processed,
                    'total': total,
                    'percentage': round((processed / total) * 100, 2),
                }
            )
        )
        
        # Store chunks with embeddings
        count = 0
        
        for index, chunk_content in enumerate(chunk_contents):
            if index < len(embeddings) and embeddings[index]:
                DocumentChunk.objects.create(
                    document=document,
                    content=chunk_content,
                    embedding=embeddings[index],
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

