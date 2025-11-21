"""
Tests for Django Models
Tương đương với Model tests trong Laravel
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.models import Document, ChatSession, ChatMessage

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.models
class TestDocument:
    """Test Document model"""
    
    def test_create_document(self, user):
        """Test creating a document"""
        document = Document.objects.create(
            user=user,
            name='test.pdf',
            file_hash='unique_hash_123',
            path='storage/documents/unique_hash_123.pdf',
            file_size=1024,
            status='processing'
        )
        
        assert document.id is not None
        assert document.user == user
        assert document.name == 'test.pdf'
        assert document.status == 'processing'
        assert document.category is None  # Optional field
        assert document.tags == []  # Default empty list
    
    def test_document_unique_file_hash_same_user(self, user):
        """Test that file_hash must be unique per user - same user cannot upload duplicate"""
        # User uploads a file
        Document.objects.create(
            user=user,
            name='test1.pdf',
            file_hash='same_hash',
            path='storage/documents/same_hash.pdf',
            file_size=1024
        )
        
        # User cannot upload the same file again (same user, same hash)
        with pytest.raises(IntegrityError):
            Document.objects.create(
                user=user,
                name='test2.pdf',
                file_hash='same_hash',
                path='storage/documents/same_hash_2.pdf',
                file_size=2048
            )
    
    def test_document_unique_file_hash_different_users(self, user, another_user):
        """Test that different users can upload files with the same hash"""
        # User 1 uploads a file
        doc1 = Document.objects.create(
            user=user,
            name='test1.pdf',
            file_hash='same_hash',
            path='storage/documents/same_hash.pdf',
            file_size=1024
        )
        assert doc1.id is not None
        
        # User 2 can upload the same file (different user, same hash is OK)
        doc2 = Document.objects.create(
            user=another_user,
            name='test1.pdf',
            file_hash='same_hash',
            path='storage/documents/same_hash_user2.pdf',
            file_size=1024
        )
        assert doc2.id is not None
        assert doc2.user == another_user
        assert doc2.file_hash == doc1.file_hash  # Same hash, different users
    
    def test_document_cascade_delete(self, user):
        """Test that document is deleted when user is deleted"""
        document = Document.objects.create(
            user=user,
            name='test.pdf',
            file_hash='cascade_test_hash',
            path='storage/documents/cascade_test_hash.pdf',
            file_size=1024
        )
        
        document_id = document.id
        user.delete()
        
        assert Document.objects.filter(id=document_id).exists() is False
    
    def test_document_with_category_and_tags(self, user):
        """Test document with category and tags"""
        document = Document.objects.create(
            user=user,
            name='test.pdf',
            file_hash='category_test_hash',
            path='storage/documents/category_test_hash.pdf',
            file_size=1024,
            category='legal',
            tags=['contract', 'important']
        )
        
        assert document.category == 'legal'
        assert document.tags == ['contract', 'important']


@pytest.mark.django_db
@pytest.mark.models
class TestChatSession:
    """Test ChatSession model"""
    
    def test_create_chat_session(self, user):
        """Test creating a chat session"""
        session = ChatSession.objects.create(
            user=user,
            title='Test Session',
            model_name='llama3.1',
            temperature=0.7,
            max_tokens=2000
        )
        
        assert session.id is not None
        assert session.user == user
        assert session.session_id is not None  # Auto-generated UUID
        assert session.title == 'Test Session'
        assert session.model_name == 'llama3.1'
        assert session.temperature == 0.7
        assert session.max_tokens == 2000
        assert session.message_count == 0
    
    def test_chat_session_auto_generate_session_id(self, user):
        """Test that session_id is auto-generated if not provided"""
        session = ChatSession.objects.create(
            user=user,
            title='Auto ID Session'
        )
        
        assert session.session_id is not None
        assert len(session.session_id) > 0
    
    def test_chat_session_get_user_documents(self, user):
        """Test get_user_documents method"""
        # Create completed documents
        doc1 = Document.objects.create(
            user=user,
            name='doc1.pdf',
            file_hash='doc1_hash',
            path='storage/documents/doc1_hash.pdf',
            file_size=1024,
            status='completed'
        )
        
        doc2 = Document.objects.create(
            user=user,
            name='doc2.pdf',
            file_hash='doc2_hash',
            path='storage/documents/doc2_hash.pdf',
            file_size=2048,
            status='completed'
        )
        
        # Create processing document (should not be included)
        Document.objects.create(
            user=user,
            name='doc3.pdf',
            file_hash='doc3_hash',
            path='storage/documents/doc3_hash.pdf',
            file_size=3072,
            status='processing'
        )
        
        session = ChatSession.objects.create(user=user)
        user_docs = session.get_user_documents()
        
        assert user_docs.count() == 2
        assert doc1 in user_docs
        assert doc2 in user_docs
    
    def test_chat_session_cascade_delete(self, user):
        """Test that session is deleted when user is deleted"""
        session = ChatSession.objects.create(user=user, title='Test')
        session_id = session.id
        
        user.delete()
        
        assert ChatSession.objects.filter(id=session_id).exists() is False


@pytest.mark.django_db
@pytest.mark.models
class TestChatMessage:
    """Test ChatMessage model"""
    
    def test_create_chat_message_with_session(self, chat_session, user):
        """Test creating a chat message with session"""
        message = ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='user',
            content='Hello, this is a test'
        )
        
        assert message.id is not None
        assert message.session == chat_session
        assert message.document is None
        assert message.user == user
        assert message.role == 'user'
        assert message.content == 'Hello, this is a test'
    
    def test_create_chat_message_with_document(self, document, user):
        """Test creating a chat message with document"""
        message = ChatMessage.objects.create(
            document=document,
            user=user,
            role='assistant',
            content='This is a response'
        )
        
        assert message.id is not None
        assert message.document == document
        assert message.session is None
        assert message.user == user
        assert message.role == 'assistant'
    
    def test_chat_message_validation_both_session_and_document(self, chat_session, document, user):
        """Test that message cannot have both session and document"""
        message = ChatMessage(
            session=chat_session,
            document=document,
            user=user,
            role='user',
            content='Invalid message'
        )
        
        with pytest.raises(ValidationError):
            message.clean()
    
    def test_chat_message_validation_neither_session_nor_document(self, user):
        """Test that message must have either session or document"""
        message = ChatMessage(
            user=user,
            role='user',
            content='Invalid message'
        )
        
        with pytest.raises(ValidationError):
            message.clean()
    
    def test_chat_message_with_analytics(self, chat_session, user):
        """Test chat message with analytics fields"""
        message = ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='assistant',
            content='Response with analytics',
            tokens_used=150,
            model_used='llama3.1',
            response_time_ms=1250,
            sources=[{'chunk_id': 1, 'score': 0.95}]
        )
        
        assert message.tokens_used == 150
        assert message.model_used == 'llama3.1'
        assert message.response_time_ms == 1250
        assert message.sources == [{'chunk_id': 1, 'score': 0.95}]
    
    def test_chat_message_cascade_delete_with_session(self, chat_session, user):
        """Test that messages are deleted when session is deleted"""
        message = ChatMessage.objects.create(
            session=chat_session,
            user=user,
            role='user',
            content='Test message'
        )
        message_id = message.id
        
        chat_session.delete()
        
        assert ChatMessage.objects.filter(id=message_id).exists() is False
    
    def test_chat_message_cascade_delete_with_document(self, document, user):
        """Test that messages are deleted when document is deleted"""
        message = ChatMessage.objects.create(
            document=document,
            user=user,
            role='user',
            content='Test message'
        )
        message_id = message.id
        
        document.delete()
        
        assert ChatMessage.objects.filter(id=message_id).exists() is False

