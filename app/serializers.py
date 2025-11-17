"""
Django REST Framework Serializers
Tương đương với Laravel API Resources hoặc Form Requests

Serializers định nghĩa cách serialize/deserialize data
"""

from rest_framework import serializers
from .models import Document, DocumentChunk, ChatMessage


class DocumentSerializer(serializers.ModelSerializer):
    """
    Document serializer - tương đương với Laravel DocumentResource
    """
    formatted_file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'status', 'num_chunks', 
            'file_size', 'formatted_file_size',
            'processed_at', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']
    
    def get_formatted_file_size(self, obj):
        """Get formatted file size"""
        return obj.get_formatted_file_size()


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    ChatMessage serializer
    """
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

