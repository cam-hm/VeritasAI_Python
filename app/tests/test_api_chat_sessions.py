"""
Tests for Chat Sessions API Endpoints
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from app.models import ChatSession, ChatMessage

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.api
class TestChatSessionsAPI:
    """Test Chat Sessions API endpoints"""
    
    def test_list_sessions(self, authenticated_client, user):
        """Test listing chat sessions"""
        ChatSession.objects.create(user=user, title='Session 1')
        ChatSession.objects.create(user=user, title='Session 2')
        
        response = authenticated_client.get('/api/chat/sessions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2
    
    def test_create_session(self, authenticated_client, user):
        """Test creating a chat session"""
        data = {
            'title': 'New Chat Session',
            'model_name': 'llama3.1',
            'temperature': '0.7',
            'max_tokens': 2000
        }
        response = authenticated_client.post('/api/chat/sessions/create/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Chat Session'
        assert response.data['session_id'] is not None
    
    def test_get_session_detail(self, authenticated_client, chat_session):
        """Test getting session detail"""
        response = authenticated_client.get(f'/api/chat/sessions/{chat_session.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == chat_session.id
        assert response.data['title'] == chat_session.title
    
    def test_get_session_with_messages(self, authenticated_client, chat_session, user):
        """Test getting session with messages"""
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
        
        response = authenticated_client.get(f'/api/chat/sessions/{chat_session.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'messages' in response.data
        assert len(response.data['messages']) == 2
    
    def test_update_session(self, authenticated_client, chat_session):
        """Test updating a chat session"""
        data = {
            'title': 'Updated Title',
            'temperature': '0.9'
        }
        # Try PATCH first (more RESTful), fallback to POST if needed
        response = authenticated_client.patch(
            f'/api/chat/sessions/{chat_session.id}/update/',
            data,
            format='json'
        )
        
        # If PATCH not allowed, try POST
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            response = authenticated_client.post(
                f'/api/chat/sessions/{chat_session.id}/update/',
                data,
                format='json'
            )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
    
    def test_delete_session(self, authenticated_client, chat_session):
        """Test deleting a chat session"""
        session_id = chat_session.id
        response = authenticated_client.delete(f'/api/chat/sessions/{session_id}/delete/')
        
        # DELETE typically returns 204 No Content
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert ChatSession.objects.filter(id=session_id).exists() is False
    
    def test_session_isolation(self, authenticated_client, another_user):
        """Test that users can only see their own sessions"""
        # Create session for another user
        other_session = ChatSession.objects.create(
            user=another_user,
            title='Other User Session'
        )
        
        # Try to access it
        response = authenticated_client.get(f'/api/chat/sessions/{other_session.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

