"""
Django Views
Tương đương với app/Http/Controllers/ trong Laravel

Django views có thể là:
- Function-based views (giống Laravel controllers)
- Class-based views (giống Laravel resource controllers)
- API views với DRF (Django REST Framework)
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .models import Document, DocumentChunk, ChatMessage
from .serializers import DocumentSerializer, ChatMessageSerializer
import logging

logger = logging.getLogger(__name__)


# Web Views (tương đương với Laravel web routes)
def home(request):
    """
    Home page - tương đương với Route::view('/', 'welcome') trong Laravel
    """
    return render(request, 'home.html')


def documents_page(request):
    """
    Documents page - tương đương với DocumentController::index() trong Laravel
    """
    documents = Document.objects.all().order_by('-created_at')
    return render(request, 'documents.html', {'documents': documents})


def document_detail(request, document_id):
    """
    Document detail page - tương đương với DocumentController::show() trong Laravel
    """
    document = get_object_or_404(Document, id=document_id)
    return render(request, 'document_detail.html', {'document': document})


# API Views với Django REST Framework (tương đương với Laravel API routes)
@api_view(['GET'])
def documents_list(request):
    """
    List all documents - tương đương với DocumentController::index() API
    """
    documents = Document.objects.all().order_by('-created_at')
    serializer = DocumentSerializer(documents, many=True)
    return Response({
        'documents': serializer.data
    })


@api_view(['GET'])
def document_detail_api(request, document_id):
    """
    Show single document - tương đương với DocumentController::show() API
    """
    document = get_object_or_404(Document, id=document_id)
    serializer = DocumentSerializer(document)
    return Response(serializer.data)


@api_view(['POST'])
def document_upload(request):
    """
    Upload document - tương đương với DocumentController::store() API
    """
    import hashlib
    import os
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings as django_settings
    
    # Validate file
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    
    # Validate file type
    allowed_types = ['pdf', 'docx', 'txt', 'md']
    file_name = file.name
    extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    if extension not in allowed_types:
        return Response({
            'error': f'Unsupported file type: {extension}. Allowed types: {", ".join(allowed_types)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file size (10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return Response({
            'error': f'File too large. Maximum size: 10MB'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Read file content để tính hash
    file_content = file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Check duplicate
    existing = Document.objects.filter(file_hash=file_hash).first()
    if existing:
        return Response({
            'message': 'File already exists',
            'document_id': existing.id,
            'document': DocumentSerializer(existing).data
        })
    
    # Save file
    storage_path = getattr(django_settings, 'STORAGE_PATH', os.path.join(django_settings.BASE_DIR, 'storage'))
    os.makedirs(storage_path, exist_ok=True)
    
    file_path = f"documents/{file_hash}.{extension}"
    full_path = os.path.join(storage_path, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'wb') as f:
        f.write(file_content)
    
    # Create Document record
    user = request.user if request.user.is_authenticated else None
    document = Document.objects.create(
        name=file_name,
        path=file_path,
        user=user,
        status='pending',
        file_hash=file_hash,
        file_size=file.size,
    )
    
    # Trigger background job (tương đương ProcessDocument::dispatch() trong Laravel)
    # Lazy import để tránh circular import
    from app.tasks.document_tasks import process_document
    process_document.delay(document.id)
    
    serializer = DocumentSerializer(document)
    return Response({
        'message': 'File uploaded successfully',
        'document': serializer.data
    }, status=status.HTTP_201_CREATED)


# Chat Views
@api_view(['GET'])
def chat_general(request):
    """
    General chat - tương đương với ChatController::general() API
    """
    # TODO: Implement general chat
    return Response({'message': 'General chat - to be implemented'})


@api_view(['GET'])
def chat_document(request, document_id):
    """
    Chat với document context - tương đương với ChatController::show() API
    """
    document = get_object_or_404(Document, id=document_id)
    messages = ChatMessage.objects.filter(document=document).order_by('created_at')
    serializer = ChatMessageSerializer(messages, many=True)
    
    return Response({
        'document': {
            'id': document.id,
            'name': document.name,
        },
        'messages': serializer.data,
    })


@api_view(['POST'])
def chat_stream(request):
    """
    Stream chat response với RAG
    Tương đương với StreamController::stream() API trong Laravel
    """
    from django.http import StreamingHttpResponse
    from django.db.models import F
    from pgvector.django import VectorField
    import json
    import httpx
    from django.conf import settings as django_settings
    from app.services.embedding_service import EmbeddingService
    from app.services.token_estimation_service import TokenEstimationService
    
    document_id = request.data.get('document_id')
    messages = request.data.get('messages', [])
    user = request.user if request.user.is_authenticated else None
    
    # Get last user message
    last_question = None
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            last_question = msg.get('content', '')
            break
    
    if not last_question:
        return Response({'error': 'No user message found'}, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_response():
        try:
            # Get document nếu có
            document = None
            if document_id:
                document = get_object_or_404(Document, id=document_id)
                if document.status != 'completed':
                    error_data = json.dumps({
                        'error': 'Document not ready for chat',
                        'status': document.status
                    })
                    yield f"data: {error_data}\n\n"
                    return
            
            # 1. Generate query embedding
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_embeddings([last_question])[0]
            
            # 2. Vector search - tìm relevant chunks
            query = DocumentChunk.objects.all()
            
            if document:
                # Chat với specific document
                query = query.filter(document=document)
            elif user:
                # General chat - chỉ search trong user's documents
                query = query.filter(document__user=user)
            else:
                # No user, no document - return error
                error_data = json.dumps({'error': 'Authentication required'})
                yield f"data: {error_data}\n\n"
                return
            
            # Vector similarity search (tương đương nearestNeighbors trong Laravel)
            # Top 15 chunks ban đầu
            # Sử dụng raw SQL với pgvector cosine distance
            from django.db import connection
            import json as json_module
            
            # Convert embedding to string format for PostgreSQL
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Use raw SQL for vector similarity search
            with connection.cursor() as cursor:
                if document:
                    cursor.execute("""
                        SELECT id, content, 
                               1 - (embedding <=> %s::vector) as similarity
                        FROM document_chunks
                        WHERE document_id = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT 15
                    """, [embedding_str, document_id, embedding_str])
                elif user:
                    cursor.execute("""
                        SELECT dc.id, dc.content,
                               1 - (dc.embedding <=> %s::vector) as similarity
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE d.user_id = %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT 15
                    """, [embedding_str, user.id, embedding_str])
                else:
                    cursor.execute("""
                        SELECT id, content,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM document_chunks
                        ORDER BY embedding <=> %s::vector
                        LIMIT 15
                    """, [embedding_str, embedding_str])
                
                rows = cursor.fetchall()
                candidate_chunks = []
                for row in rows:
                    chunk = DocumentChunk.objects.get(id=row[0])
                    chunk.similarity = float(row[2])  # Add similarity as attribute
                    candidate_chunks.append(chunk)
            
            # 3. Token management - select chunks fit trong context window
            token_service = TokenEstimationService()
            max_context_tokens = 4000
            
            # Estimate tokens cho system prompt
            if document:
                scope = f"this document ('{document.name}')"
            else:
                scope = "the available documents"
            system_prompt_base = f"Based only on the following context from {scope}, answer the user's question. If you are not sure, say you are not sure and suggest where to look.\n\nContext:\n"
            base_tokens = token_service.estimate_tokens(system_prompt_base)
            
            # Estimate tokens cho user messages
            user_tokens = sum(
                token_service.estimate_tokens(msg.get('content', ''))
                for msg in messages if msg.get('role') == 'user'
            )
            
            # Reserve tokens
            reserved = base_tokens + user_tokens + int(max_context_tokens * 0.2)
            available = max_context_tokens - reserved
            
            # Select chunks fit trong token limit
            selected_chunks = []
            used_tokens = 0
            
            for chunk in candidate_chunks:
                chunk_tokens = token_service.estimate_tokens(chunk.content)
                separator_tokens = token_service.estimate_tokens("\n\n---\n\n")
                
                if used_tokens + chunk_tokens + separator_tokens > available:
                    break
                
                selected_chunks.append(chunk)
                used_tokens += chunk_tokens + separator_tokens
            
            # 4. Build context
            context = "\n\n---\n\n".join([chunk.content for chunk in selected_chunks])
            
            if not context.strip():
                system_prompt = "You are a helpful assistant. If the context is empty or insufficient, answer based on your general knowledge."
            else:
                system_prompt = system_prompt_base + context
            
            # 5. Prepare messages for LLM
            messages_for_ai = messages.copy()
            messages_for_ai.insert(0, {'role': 'system', 'content': system_prompt})
            
            # 6. Generate response với Ollama (streaming)
            ollama_url = f"{getattr(django_settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/chat"
            # Use llama3.1 if llama3.2 not available
            ollama_model = getattr(django_settings, 'OLLAMA_CHAT_MODEL', 'llama3.1')
            
            full_response = ""
            with httpx.stream(
                'POST',
                ollama_url,
                json={
                    'model': ollama_model,
                    'messages': messages_for_ai,
                    'stream': True
                },
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                                full_response += content
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue
            
            # 7. Save messages
            if document and user:
                ChatMessage.objects.create(
                    document=document,
                    user=user,
                    role='user',
                    content=last_question
                )
                ChatMessage.objects.create(
                    document=document,
                    user=user,
                    role='ai',
                    content=full_response
                )
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"Chat error: {error_msg}\n{error_trace}")
            error_data = json.dumps({'error': error_msg})
            yield f"data: {error_data}\n\n"
    
    return StreamingHttpResponse(
        generate_response(),
        content_type='text/event-stream',
        headers={
            'X-Accel-Buffering': 'no',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

