#!/usr/bin/env python
"""
Script để update token_count cho documents cũ
Chạy: python scripts/update_token_counts.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veritasai_django.settings')
django.setup()

from app.models import DocumentChunk
from app.services.token_estimation_service import TokenEstimationService


def update_token_counts():
    """Update token_count cho tất cả chunks"""
    token_service = TokenEstimationService()
    
    # Get all chunks without token_count
    chunks = DocumentChunk.objects.filter(token_count=0)
    total = chunks.count()
    
    if total == 0:
        print("✅ All chunks already have token_count!")
        return
    
    print(f"🔍 Found {total} chunks without token_count")
    print("🚀 Updating token counts...")
    
    updated = 0
    for i, chunk in enumerate(chunks, 1):
        try:
            token_count = token_service.estimate_tokens(chunk.content)
            chunk.token_count = token_count
            chunk.save(update_fields=['token_count'])
            updated += 1
            
            if i % 10 == 0:
                print(f"   Progress: {i}/{total} ({int(i/total*100)}%)")
        except Exception as e:
            print(f"   ❌ Error updating chunk {chunk.id}: {e}")
    
    print(f"\n✅ Updated {updated}/{total} chunks successfully!")


if __name__ == "__main__":
    update_token_counts()

