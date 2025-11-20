"""
Tests for Django REST Framework Serializers
Tương đương với Form Request tests trong Laravel
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from app.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    DocumentSerializer,
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    ChatMessageSerializer
)
from app.models import Document, ChatSession, ChatMessage

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.serializers
class TestRegisterSerializer:
    """Test RegisterSerializer"""
    
    def test_register_valid_data(self):
        """Test registration with valid data"""
        data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is True
        
        user = serializer.save()
        assert user.email == 'newuser@example.com'
        assert user.username == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.check_password('password123') is True
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch"""
        data = {
            'email': 'user@example.com',
            'password': 'password123',
            'password_confirm': 'different123'
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors
    
    def test_register_duplicate_email(self, user):
        """Test registration with duplicate email"""
        data = {
            'email': user.email,
            'password': 'password123',
            'password_confirm': 'password123'
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'email' in serializer.errors
    
    def test_register_short_password(self):
        """Test registration with short password"""
        data = {
            'email': 'user@example.com',
            'password': 'short',
            'password_confirm': 'short'
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors


@pytest.mark.django_db
@pytest.mark.serializers
class TestLoginSerializer:
    """Test LoginSerializer"""
    
    def test_login_valid_credentials(self, user):
        """Test login with valid credentials"""
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data['user'] == user
    
    def test_login_invalid_email(self):
        """Test login with invalid email"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
    
    def test_login_invalid_password(self, user):
        """Test login with invalid password"""
        data = {
            'email': user.email,
            'password': 'wrongpassword'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False


@pytest.mark.django_db
@pytest.mark.serializers
class TestDocumentSerializer:
    """Test DocumentSerializer"""
    
    def test_document_serialization(self, document):
        """Test serializing a document"""
        serializer = DocumentSerializer(document)
        data = serializer.data
        
        assert data['id'] == document.id
        assert data['name'] == document.name
        assert data['status'] == document.status
        assert data['category'] == document.category
        assert data['tags'] == document.tags
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_document_deserialization(self, user):
        """Test deserializing document data"""
        data = {
            'name': 'test.pdf',
            'path': 'storage/documents/test.pdf',
            'status': 'pending',
            'category': 'legal',
            'tags': ['contract', 'important']
        }
        serializer = DocumentSerializer(data=data)
        assert serializer.is_valid() is True
        
        # Note: DocumentSerializer might not have create method
        # This test verifies validation works


@pytest.mark.django_db
@pytest.mark.serializers
class TestChatSessionSerializer:
    """Test ChatSessionSerializer"""
    
    def test_chat_session_serialization(self, chat_session):
        """Test serializing a chat session"""
        serializer = ChatSessionSerializer(chat_session)
        data = serializer.data
        
        assert data['id'] == chat_session.id
        assert data['session_id'] == chat_session.session_id
        assert data['title'] == chat_session.title
        assert data['model_name'] == chat_session.model_name
        assert float(data['temperature']) == float(chat_session.temperature)
        assert data['max_tokens'] == chat_session.max_tokens
        assert 'started_at' in data
    
    def test_chat_session_create(self, user):
        """Test creating a chat session via serializer"""
        data = {
            'title': 'New Session',
            'model_name': 'llama3.1',
            'temperature': '0.8',
            'max_tokens': 3000
        }
        serializer = ChatSessionSerializer(data=data)
        assert serializer.is_valid() is True
        
        session = serializer.save(user=user)
        assert session.title == 'New Session'
        assert session.user == user
    
    def test_chat_session_update(self, chat_session):
        """Test updating a chat session"""
        data = {
            'title': 'Updated Title',
            'temperature': '0.9'
        }
        serializer = ChatSessionSerializer(chat_session, data=data, partial=True)
        assert serializer.is_valid() is True
        
        updated = serializer.save()
        assert updated.title == 'Updated Title'
        assert float(updated.temperature) == 0.9


@pytest.mark.django_db
@pytest.mark.serializers
class TestChatSessionDetailSerializer:
    """Test ChatSessionDetailSerializer (with nested messages)"""
    
    def test_chat_session_with_messages(self, chat_session, user):
        """Test serializing session with messages"""
        # Create some messages
        ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='user',
            content='Hello'
        )
        ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='assistant',
            content='Hi there!'
        )
        
        serializer = ChatSessionDetailSerializer(chat_session)
        data = serializer.data
        
        assert 'messages' in data
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][1]['role'] == 'assistant'


@pytest.mark.django_db
@pytest.mark.serializers
class TestChatMessageSerializer:
    """Test ChatMessageSerializer"""
    
    def test_chat_message_serialization(self, chat_message):
        """Test serializing a chat message"""
        serializer = ChatMessageSerializer(chat_message)
        data = serializer.data
        
        assert data['id'] == chat_message.id
        assert data['role'] == chat_message.role
        assert data['content'] == chat_message.content
        assert 'created_at' in data
    
    def test_chat_message_with_analytics(self, chat_session, user):
        """Test serializing message with analytics"""
        message = ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='assistant',
            content='Response',
            tokens_used=150,
            model_used='llama3.1',
            response_time_ms=1250,
            sources=[{'chunk_id': 1, 'score': 0.95}]
        )
        
        serializer = ChatMessageSerializer(message)
        data = serializer.data
        
        assert data['tokens_used'] == 150
        assert data['model_used'] == 'llama3.1'
        assert data['response_time_ms'] == 1250
        assert data['sources'] == [{'chunk_id': 1, 'score': 0.95}]


@pytest.mark.django_db
@pytest.mark.serializers
class TestUserSerializer:
    """Test UserSerializer"""
    
    def test_user_serialization(self, user):
        """Test serializing a user"""
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert data['id'] == user.id
        assert data['email'] == user.email
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
        # Password should not be in serialized data
        assert 'password' not in data

