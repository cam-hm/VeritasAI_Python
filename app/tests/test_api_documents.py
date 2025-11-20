"""
Tests for Documents API Endpoints
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from app.models import Document

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.api
class TestDocumentsAPI:
    """Test Documents API endpoints"""
    
    def test_list_documents_authenticated(self, authenticated_client, user):
        """Test listing documents when authenticated"""
        # Create some documents
        Document.objects.create(
            user=user,
            name='doc1.pdf',
            file_hash='hash1',
            path='storage/documents/hash1.pdf',
            file_size=1024,
            status='completed'
        )
        Document.objects.create(
            user=user,
            name='doc2.pdf',
            file_hash='hash2',
            path='storage/documents/hash2.pdf',
            file_size=2048,
            status='processing'
        )
        
        response = authenticated_client.get('/api/documents/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2
    
    def test_list_documents_unauthenticated(self, unauthenticated_client):
        """Test listing documents without authentication"""
        response = unauthenticated_client.get('/api/documents/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_documents_filter_by_status(self, authenticated_client, user):
        """Test filtering documents by status"""
        Document.objects.create(
            user=user,
            name='doc1.pdf',
            file_hash='hash1',
            path='storage/documents/hash1.pdf',
            file_size=1024,
            status='completed'
        )
        Document.objects.create(
            user=user,
            name='doc2.pdf',
            file_hash='hash2',
            path='storage/documents/hash2.pdf',
            file_size=2048,
            status='processing'
        )
        
        response = authenticated_client.get('/api/documents/?status=completed')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'completed'
    
    def test_get_document_detail(self, authenticated_client, document):
        """Test getting document detail"""
        response = authenticated_client.get(f'/api/documents/{document.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == document.id
        assert response.data['name'] == document.name
    
    def test_get_document_detail_other_user(self, authenticated_client, another_user):
        """Test getting document from another user (should fail)"""
        document = Document.objects.create(
            user=another_user,
            name='other_doc.pdf',
            file_hash='other_hash',
            path='storage/documents/other_hash.pdf',
            file_size=1024
        )
        
        response = authenticated_client.get(f'/api/documents/{document.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_document(self, authenticated_client, document):
        """Test deleting a document"""
        document_id = document.id
        response = authenticated_client.delete(f'/api/documents/{document_id}/delete/')
        
        # DELETE typically returns 204 No Content
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
        assert Document.objects.filter(id=document_id).exists() is False
    
    def test_delete_document_other_user(self, authenticated_client, another_user):
        """Test deleting document from another user (should fail)"""
        document = Document.objects.create(
            user=another_user,
            name='other_doc.pdf',
            file_hash='other_hash',
            path='storage/documents/other_hash.pdf',
            file_size=1024
        )
        
        response = authenticated_client.delete(f'/api/documents/{document.id}/delete/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

