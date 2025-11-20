"""
Django REST Framework Serializers
Tương đương với Laravel API Resources hoặc Form Requests

Serializers định nghĩa cách serialize/deserialize data
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Document, DocumentChunk, ChatMessage, ChatSession


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
            'category', 'tags', 'metadata',
            'processed_at', 'error_message', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']
    
    def get_formatted_file_size(self, obj):
        """Get formatted file size"""
        return obj.get_formatted_file_size()


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    ChatMessage serializer
    """
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'sources',
            'tokens_used', 'model_used', 'response_time_ms',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    ChatSession serializer
    """
    document = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_id', 'title', 'document',
            'system_prompt', 'model_provider', 'model_name',
            'temperature', 'max_tokens', 'max_context_tokens',
            'message_count', 'started_at', 'last_message_at'
        ]
        read_only_fields = ['id', 'session_id', 'started_at', 'message_count']


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """
    ChatSession detail serializer with messages
    """
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_id', 'title',
            'system_prompt', 'model_provider', 'model_name',
            'temperature', 'max_tokens', 'max_context_tokens',
            'message_count', 'started_at', 'last_message_at',
            'messages'
        ]
        read_only_fields = ['id', 'session_id', 'started_at', 'message_count']


# Authentication Serializers
class RegisterSerializer(serializers.ModelSerializer):
    """
    User registration serializer
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_email(self, value):
        """Check if email is already registered"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user with email as username
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    User login serializer
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """Validate credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")
            
            # Authenticate user
            user = authenticate(username=user.username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials.")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer for responses
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

