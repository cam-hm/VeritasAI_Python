"""
Celery Application Configuration
Tương đương với config/queue.php trong Laravel
"""

import os
from celery import Celery
from django.conf import settings as django_settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veritasai_django.settings')

# Tạo Celery instance
celery_app = Celery(
    "veritasai",
    broker=getattr(django_settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=getattr(django_settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Auto-discover tasks (tương đương với auto-loading jobs trong Laravel)
celery_app.autodiscover_tasks(["app.tasks"])

