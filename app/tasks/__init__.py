"""
Celery Tasks Package
Tương đương với app/Jobs/ trong Laravel

Celery là distributed task queue - tương đương Laravel Queue
"""

from app.tasks.document_tasks import process_document

__all__ = ["process_document"]

