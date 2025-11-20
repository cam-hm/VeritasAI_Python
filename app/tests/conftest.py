"""
Pytest configuration and shared fixtures
Tương đương với Laravel TestCase và factories
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.db import connection
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import Document, ChatSession, ChatMessage

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Setup test database with pgvector extension
    """
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            # Enable pgvector extension for test database
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception:
                # Extension might already exist or not available
                pass


@pytest.fixture
def user(db):
    """
    Create a test user
    Tương đương với User::factory()->create() trong Laravel
    """
    return User.objects.create_user(
        username='testuser@example.com',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def another_user(db):
    """Create another test user for isolation testing"""
    return User.objects.create_user(
        username='another@example.com',
        email='another@example.com',
        password='testpass123',
        first_name='Another',
        last_name='User'
    )


@pytest.fixture
def authenticated_client(user):
    """
    API client with JWT authentication
    Tương đương với $this->actingAs($user) trong Laravel
    """
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def unauthenticated_client():
    """API client without authentication"""
    return APIClient()


@pytest.fixture
def django_client():
    """Django test client for web views"""
    return Client()


@pytest.fixture
def document(user, db):
    """
    Create a test document
    Tương đương với Document::factory()->create() trong Laravel
    """
    return Document.objects.create(
        user=user,
        name='test.pdf',
        file_hash='test_hash_123',
        path='storage/documents/test_hash_123.pdf',
        file_size=1024,
        status='completed',
        category='general',
        tags=['test', 'sample']
    )


@pytest.fixture
def chat_session(user, db):
    """
    Create a test chat session
    """
    return ChatSession.objects.create(
        user=user,
        title='Test Chat Session',
        model_name='llama3.1',
        temperature=0.7,
        max_tokens=2000
    )


@pytest.fixture
def chat_message(chat_session, user, db):
    """
    Create a test chat message
    """
    return ChatMessage.objects.create(
        session=chat_session,
        user=user,
        role='user',
        content='Hello, this is a test message'
    )


@pytest.fixture
def sample_pdf_file():
    """
    Create a sample PDF file for upload testing
    """
    from io import BytesIO
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    # Create a minimal PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000245 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
337
%%EOF"""
    
    return SimpleUploadedFile(
        "test.pdf",
        pdf_content,
        content_type="application/pdf"
    )


@pytest.fixture
def sample_text_file():
    """
    Create a sample text file for upload testing
    """
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    content = b"This is a test text file.\nIt contains multiple lines.\nFor testing purposes."
    
    return SimpleUploadedFile(
        "test.txt",
        content,
        content_type="text/plain"
    )

