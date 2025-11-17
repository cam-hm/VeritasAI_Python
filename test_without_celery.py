#!/usr/bin/env python
"""
Test script để test document processing mà không cần Celery
Chạy processing synchronously để test
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veritasai_django.settings')
django.setup()

from app.models import Document
from app.tasks.document_tasks import process_document

def test_process_document(doc_id):
    """Test process document synchronously"""
    print(f"🔍 Processing document {doc_id}...")
    
    try:
        # Call task function directly (không dùng .delay())
        # This will run synchronously
        result = process_document(doc_id)
        print(f"✅ Processing completed!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_without_celery.py <document_id>")
        print("\nAvailable documents:")
        docs = Document.objects.all()[:10]
        for doc in docs:
            print(f"  ID: {doc.id}, Name: {doc.name}, Status: {doc.status}")
        sys.exit(1)
    
    doc_id = int(sys.argv[1])
    
    # Check document exists
    try:
        doc = Document.objects.get(id=doc_id)
        print(f"📄 Document: {doc.name}")
        print(f"📊 Status: {doc.status}")
        print(f"📁 Path: {doc.path}")
    except Document.DoesNotExist:
        print(f"❌ Document {doc_id} not found")
        sys.exit(1)
    
    # Process
    if test_process_document(doc_id):
        # Check result
        doc.refresh_from_db()
        print(f"\n✅ Final status: {doc.status}")
        print(f"📊 Chunks created: {doc.num_chunks}")
        if doc.status == 'failed':
            print(f"❌ Error: {doc.error_message}")
    else:
        print("\n❌ Processing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

