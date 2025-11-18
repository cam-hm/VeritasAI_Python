"""
Management command để process document
Tương đương với php artisan queue:work trong Laravel

Usage:
    python manage.py process_document <document_id>
"""

from django.core.management.base import BaseCommand
from app.tasks.document_tasks import process_document_sync


class Command(BaseCommand):
    help = 'Process a document by ID'

    def add_arguments(self, parser):
        parser.add_argument('document_id', type=int, help='Document ID to process')

    def handle(self, *args, **options):
        document_id = options['document_id']
        self.stdout.write(f'Processing document {document_id}...')
        
        try:
            process_document_sync(document_id)
            self.stdout.write(self.style.SUCCESS(f'Successfully processed document {document_id}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing document {document_id}: {e}'))
            raise

