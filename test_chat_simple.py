#!/usr/bin/env python
"""
Simple test script để test chat endpoint
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veritasai_django.settings')
django.setup()

from app.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.token_estimation_service import TokenEstimationService
from django.db import connection
import httpx
from django.conf import settings

def test_chat_flow(doc_id):
    """Test chat flow step by step"""
    print(f"🔍 Testing chat flow for document {doc_id}...")
    
    try:
        # 1. Get document
        document = Document.objects.get(id=doc_id)
        print(f"✅ Document: {document.name}, Status: {document.status}")
        
        if document.status != 'completed':
            print(f"❌ Document not ready (status: {document.status})")
            return False
        
        # 2. Generate query embedding
        query = "What is this document about?"
        print(f"🔍 Generating embedding for query: {query}")
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.generate_embeddings([query])[0]
        print(f"✅ Embedding generated: {len(query_embedding)} dimensions")
        
        # 3. Vector search
        print("🔍 Searching for relevant chunks...")
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, content, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """, [embedding_str, doc_id, embedding_str])
            rows = cursor.fetchall()
        
        print(f"✅ Found {len(rows)} chunks")
        selected_chunks = []
        for row in rows:
            chunk = DocumentChunk.objects.get(id=row[0])
            chunk.similarity = float(row[2])
            selected_chunks.append(chunk)
            print(f"  - Similarity: {chunk.similarity:.4f}, Content: {chunk.content[:50]}...")
        
        # 4. Build context
        context = "\n\n---\n\n".join([chunk.content for chunk in selected_chunks])
        system_prompt = f"Based only on the following context from this document ('{document.name}'), answer the user's question.\n\nContext:\n{context}"
        
        # 5. Test Ollama API
        print("🔍 Testing Ollama chat API...")
        ollama_url = f"{getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/chat"
        ollama_model = getattr(settings, 'OLLAMA_CHAT_MODEL', 'llama3.1')
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query}
        ]
        
        response = httpx.post(
            ollama_url,
            json={
                'model': ollama_model,
                'messages': messages,
                'stream': False
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('message', {}).get('content', '')
            print(f"✅ Ollama response: {ai_response[:200]}...")
            return True
        else:
            print(f"❌ Ollama error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_chat_simple.py <document_id>")
        sys.exit(1)
    
    doc_id = int(sys.argv[1])
    test_chat_flow(doc_id)

