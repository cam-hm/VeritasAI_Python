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
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .models import Document, DocumentChunk, ChatMessage, ChatSession
from .serializers import (
    DocumentSerializer, 
    ChatMessageSerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserSerializer
)
import logging

logger = logging.getLogger(__name__)


# Web Views (tương đương với Laravel web routes)
def home(request):
    """
    Home page - tương đương với Route::view('/', 'welcome') trong Laravel
    """
    return render(request, 'home.html')


def login_page(request):
    """Login page"""
    return render(request, 'login.html')


def register_page(request):
    """Register page"""
    return render(request, 'register.html')


def documents_page(request):
    """
    Documents page - tương đương với DocumentController::index() trong Laravel
    """
    return render(request, 'documents.html')


def chat_page(request):
    """Chat page"""
    return render(request, 'chat.html')


def document_detail(request, document_id):
    """
    Document detail page với chat interface
    Tương đương với DocumentController::show() trong Laravel
    """
    document = get_object_or_404(Document, id=document_id)
    
    # Load chat messages nếu document đã completed
    chat_messages = []
    if document.status == 'completed':
        chat_messages = ChatMessage.objects.filter(
            document=document
        ).order_by('created_at')[:50]  # Last 50 messages
    
    return render(request, 'document_detail.html', {
        'document': document,
        'chat_messages': chat_messages
    })


# API Views với Django REST Framework (tương đương với Laravel API routes)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def documents_list(request):
    """
    List user's documents - tương đương với DocumentController::index() API
    GET /api/documents/
    """
    # Filter by authenticated user
    documents = Document.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.query_params.get('status')
    if status:
        documents = documents.filter(status=status)
    
    # Filter by category
    category = request.query_params.get('category')
    if category:
        documents = documents.filter(category=category)
    
    # Search in name
    search = request.query_params.get('search')
    if search:
        documents = documents.filter(name__icontains=search)
    
    # Pagination
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = int(request.query_params.get('page_size', 20))
    paginated_docs = paginator.paginate_queryset(documents, request)
    
    serializer = DocumentSerializer(paginated_docs, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_detail_api(request, document_id):
    """
    Show single document - tương đương với DocumentController::show() API
    GET /api/documents/{id}/
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
    serializer = DocumentSerializer(document)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def document_delete(request, document_id):
    """
    Delete document
    DELETE /api/documents/{id}/
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
    
    # Get optional fields
    category = request.data.get('category')
    tags = request.data.get('tags')
    if tags and isinstance(tags, str):
        try:
            import json
            tags = json.loads(tags)
        except:
            tags = []
    
    # Create Document record
    document = Document.objects.create(
        name=file_name,
        path=file_path,
        user=request.user,
        status='pending',
        file_hash=file_hash,
        file_size=file.size,
        category=category,
        tags=tags if tags else [],
    )
    
    # Trigger background job (tương đương ProcessDocument::dispatch() trong Laravel)
    # Lazy import để tránh circular import
    try:
        # Check if Celery worker is actually running
        # process_document.delay() doesn't raise error if worker is down!
        celery_available = False
        try:
            from app.celery_app import celery_app
            # Inspect active workers
            inspect = celery_app.control.inspect(timeout=1.0)
            active_workers = inspect.active()
            if active_workers:
                celery_available = True
                logger.info(f"Celery workers available: {list(active_workers.keys())}")
        except Exception as e:
            logger.warning(f"Celery not available: {e}")
        
        if celery_available:
            # Use Celery
            from app.tasks.document_tasks import process_document
            process_document.delay(document.id)
            logger.info(f"Document {document.id} submitted to Celery queue")
        else:
            # Fallback to subprocess
            logger.info(f"Using subprocess for document {document.id} (no Celery workers)")
            import subprocess
            import sys
            
            # Use Django management command (survives request end, proper Django setup)
            # Tương đương với php artisan queue:work trong Laravel
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Create log file for subprocess output
            log_file_path = os.path.join(project_root, 'storage', 'logs', f'process_{document.id}.log')
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            # Open log file (don't use context manager - subprocess needs it open)
            log_file = open(log_file_path, 'w')
            proc = subprocess.Popen(
                [sys.executable, 'manage.py', 'process_document', str(document.id)],
                cwd=project_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
                close_fds=False  # Don't close file descriptors
            )
            logger.info(f"Background process started for document {document.id}, PID: {proc.pid}, log: {log_file_path}")
    except Exception as e:
        logger.error(f"Error triggering document processing: {e}")
        document.status = 'failed'
        document.error_message = f"Failed to start processing: {str(e)}"
        document.save()
    
    serializer = DocumentSerializer(document)
    return Response({
        'message': 'File uploaded successfully',
        'document': serializer.data
    }, status=status.HTTP_201_CREATED)


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    User registration endpoint
    POST /api/auth/register
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': 'Validation failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User login endpoint
    POST /api/auth/login
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User logout endpoint
    POST /api/auth/logout
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


# Chat Session Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions_list(request):
    """
    List user's chat sessions
    GET /api/chat/sessions/
    """
    sessions = ChatSession.objects.filter(user=request.user).order_by('-last_message_at', '-started_at')
    
    # Pagination
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = int(request.query_params.get('page_size', 20))
    paginated_sessions = paginator.paginate_queryset(sessions, request)
    
    serializer = ChatSessionSerializer(paginated_sessions, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_sessions_create(request):
    """
    Create new chat session
    POST /api/chat/sessions/
    """
    title = request.data.get('title', 'New Conversation')
    
    session = ChatSession.objects.create(
        user=request.user,
        title=title
    )
    
    serializer = ChatSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions_detail(request, session_id):
    """
    Get chat session with messages
    GET /api/chat/sessions/{id}/
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    serializer = ChatSessionDetailSerializer(session)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def chat_sessions_update(request, session_id):
    """
    Update chat session
    PATCH /api/chat/sessions/{id}/
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    serializer = ChatSessionSerializer(session, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def chat_sessions_delete(request, session_id):
    """
    Delete chat session
    DELETE /api/chat/sessions/{id}/
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Chat Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_document(request, document_id):
    """
    Chat với document context - tương đương với ChatController::show() API
    GET /api/chat/{document_id}/
    """
    document = get_object_or_404(Document, id=document_id, user=request.user)
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
@permission_classes([IsAuthenticated])
def chat_stream(request):
    """
    Stream chat response với RAG
    POST /api/chat/stream/
    Supports both document-specific chat and central chat (session)
    """
    from django.http import StreamingHttpResponse
    from django.db.models import F
    from pgvector.django import VectorField
    from django.db import connection
    import json
    import httpx
    import time
    from django.conf import settings as django_settings
    from app.services.embedding_service import EmbeddingService
    from app.services.token_estimation_service import TokenEstimationService
    
    session_id = request.data.get('session_id')
    document_id = request.data.get('document_id')
    messages = request.data.get('messages', [])
    user = request.user
    
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
            start_time = time.time()
            session = None
            document = None
            
            # Determine chat type: session (central chat) or document-specific
            if session_id:
                # Central chat - uses all user documents
                session = get_object_or_404(ChatSession, id=session_id, user=user)
            elif document_id:
                # Document-specific chat
                document = get_object_or_404(Document, id=document_id, user=user)
                if document.status != 'completed':
                    error_data = json.dumps({
                        'error': 'Document not ready for chat',
                        'status': document.status
                    })
                    yield f"data: {error_data}\n\n"
                    return
            else:
                error_data = json.dumps({'error': 'Either session_id or document_id is required'})
                yield f"data: {error_data}\n\n"
                return
            
            # 1. Generate query embedding với cache
            from django.core.cache import cache
            import hashlib
            
            # Cache key based on question hash
            cache_key = f"embedding:{hashlib.md5(last_question.encode('utf-8')).hexdigest()}"
            query_embedding = cache.get(cache_key)
            
            if query_embedding is None:
                # Cache miss - generate embedding
                embedding_service = EmbeddingService()
                query_embedding = embedding_service.generate_embeddings([last_question])[0]
                # Cache for 1 hour
                cache.set(cache_key, query_embedding, timeout=3600)
            # else: Cache hit - use cached embedding
            
            # 2. Vector search - tìm relevant chunks
            if document:
                # Document-specific chat - search only in this document
                user_documents = [document]
            elif session:
                # Central chat - search in all user's completed documents
                user_documents = session.get_user_documents()
            else:
                error_data = json.dumps({'error': 'Invalid chat configuration'})
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
                    # Document-specific: search in single document
                    cursor.execute("""
                        SELECT dc.id, dc.content, d.id as doc_id, d.name as doc_name,
                               1 - (dc.embedding <=> %s::vector) as similarity
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.document_id = %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT 15
                    """, [embedding_str, document_id, embedding_str])
                elif session:
                    # Central chat: search in all user's documents
                    document_ids = [doc.id for doc in user_documents]
                    if not document_ids:
                        error_data = json.dumps({'error': 'No documents available for chat'})
                        yield f"data: {error_data}\n\n"
                        return
                    placeholders = ','.join(['%s'] * len(document_ids))
                    cursor.execute(f"""
                        SELECT dc.id, dc.content, d.id as doc_id, d.name as doc_name,
                               1 - (dc.embedding <=> %s::vector) as similarity
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE d.id IN ({placeholders})
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT 15
                    """, [embedding_str] + document_ids + [embedding_str])
                
                rows = cursor.fetchall()
                
                # Fix N+1 query: Fetch all chunks in one query
                chunk_ids = [row[0] for row in rows]
                chunks_dict = {
                    chunk.id: chunk 
                    for chunk in DocumentChunk.objects.filter(id__in=chunk_ids).select_related('document')
                }
                
                # Build candidate_chunks list with similarity scores and document info
                candidate_chunks = []
                sources_data = []  # For saving sources later
                for row in rows:
                    chunk = chunks_dict[row[0]]
                    chunk.similarity = float(row[4])  # Similarity is now 5th column (after doc_id, doc_name)
                    chunk.doc_id = row[2]  # Document ID
                    chunk.doc_name = row[3]  # Document name
                    candidate_chunks.append(chunk)
                    sources_data.append({
                        'document_id': row[2],
                        'document_name': row[3],
                        'chunk_id': row[0],
                        'relevance_score': float(row[4])
                    })
            
            # 3. Token management - select chunks fit trong context window
            token_service = TokenEstimationService()
            # Use session max_context_tokens if available
            if session:
                max_context_tokens = session.max_context_tokens
            else:
                max_context_tokens = 4000
            
            # Estimate tokens cho system prompt
            if document:
                scope = f"this document ('{document.name}')"
                system_prompt_text = "You are a helpful assistant. Answer questions based on the provided context."
            elif session:
                scope = "the user's uploaded documents"
                system_prompt_text = session.system_prompt
            else:
                scope = "the available documents"
                system_prompt_text = "You are a helpful assistant. Answer questions based on the provided context."
            
            system_prompt_base = f"{system_prompt_text}\n\nBased only on the following context from {scope}, answer the user's question. If you are not sure, say you are not sure and suggest where to look.\n\nContext:\n"
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
            # Use pre-computed token_count if available
            selected_chunks = []
            used_tokens = 0
            separator_tokens = token_service.estimate_tokens("\n\n---\n\n")
            
            for chunk in candidate_chunks:
                # Use pre-computed token_count if available, otherwise estimate
                if chunk.token_count > 0:
                    chunk_tokens = chunk.token_count
                else:
                    chunk_tokens = token_service.estimate_tokens(chunk.content)
                
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
            
            # 6. Generate response với LLM provider (streaming)
            from app.services.llm_service import get_provider_for_session
            
            # Get provider based on session or default
            llm_provider = get_provider_for_session(session)
            
            # Use session model settings if available, otherwise default
            if session:
                model_name = session.model_name
                temperature = float(session.temperature)
                max_tokens = session.max_tokens
            else:
                model_name = getattr(django_settings, 'OLLAMA_CHAT_MODEL', 'llama3.1')
                temperature = 0.7
                max_tokens = 2000
            
            full_response = ""
            # Use LLM provider chat với streaming
            # Handle different response formats from different providers
            provider_name = llm_provider.provider_name
            
            for data in llm_provider.chat(
                messages_for_ai, 
                model=model_name, 
                stream=True, 
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # Parse response based on provider format
                # LiteLLM normalizes responses, but format may vary
                content = None
                
                # Try OpenAI-compatible format first (most common)
                if 'choices' in data and len(data['choices']) > 0:
                    delta = data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                
                # Fallback to Ollama format
                if not content and 'message' in data:
                    message = data.get('message', {})
                    if isinstance(message, dict):
                        content = message.get('content', '')
                    elif hasattr(message, 'content'):
                        content = message.content
                
                if content:
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            # 7. Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 8. Save messages asynchronously (non-blocking)
            import threading
            
            def save_messages_async():
                """Save chat messages in background thread"""
                try:
                    # Save user message
                    user_msg = ChatMessage.objects.create(
                        session=session,
                        document=document,
                        user=user,
                        role='user',
                        content=last_question
                    )
                    
                    # Save assistant message with sources and analytics
                    assistant_msg = ChatMessage.objects.create(
                        session=session,
                        document=document,
                        user=user,
                        role='assistant',
                        content=full_response,
                        sources=sources_data[:5],  # Top 5 sources
                        tokens_used=token_service.estimate_tokens(full_response),
                        model_used=model_name,
                        response_time_ms=response_time_ms
                    )
                    
                    # Update session statistics
                    if session:
                        session.message_count = ChatMessage.objects.filter(session=session).count()
                        session.last_message_at = assistant_msg.created_at
                        # Auto-generate title from first message if not set or still default
                        first_message = ChatMessage.objects.filter(session=session).order_by('id').first()
                        if (not session.title or session.title == 'New Conversation') and first_message and first_message.id == user_msg.id:
                            # Use first 50 chars of first user message as title
                            title = last_question[:50].strip()
                            if len(last_question) > 50:
                                title += '...'
                            session.title = title if title else 'New Conversation'
                        session.save()
                except Exception as e:
                    logger.error(f"Error saving chat messages: {e}")
            
            # Run in background thread - user doesn't wait
            thread = threading.Thread(target=save_messages_async)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"Chat error: {error_msg}\n{error_trace}")
            error_data = json.dumps({'error': error_msg})
            yield f"data: {error_data}\n\n"
    
    response = StreamingHttpResponse(
        generate_response(),
        content_type='text/event-stream'
    )
    # Set headers (không dùng 'Connection: keep-alive' vì Django dev server không support)
    response['X-Accel-Buffering'] = 'no'
    response['Cache-Control'] = 'no-cache'
    return response

