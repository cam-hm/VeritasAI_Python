"""
Django Models
Tương đương với app/Models/ trong Laravel

Django ORM tương đương với Eloquent ORM trong Laravel
"""

from django.db import models
import uuid
# Tạm thời dùng default Django User (auth.User)
# Có thể customize sau bằng cách tạo custom User model
try:
    from pgvector.django import VectorField
except ImportError:
    # Fallback nếu pgvector chưa được cài đặt
    VectorField = models.TextField


class Document(models.Model):
    """
    Document model - User's uploaded documents
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # User ownership
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,  # Changed from SET_NULL
        related_name='documents'
    )
    
    # Existing fields
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=500)  # File path trong storage
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    num_chunks = models.IntegerField(default=0)
    embedding_model = models.CharField(max_length=100, null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)  # Removed unique=True, now unique per user
    file_size = models.IntegerField(null=True, blank=True)  # Size in bytes
    
    # New fields for MVP
    category = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(default=list)  # Array of tags
    metadata = models.JSONField(default=dict)  # Flexible metadata
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['file_hash']),
        ]
        # Ensure file_hash is unique per user (not globally)
        unique_together = [['user', 'file_hash']]
    
    def __str__(self):
        return self.name
    
    def get_formatted_file_size(self):
        """
        Get formatted file size (e.g., "2.5 MB")
        Tương đương với getFormattedFileSizeAttribute() trong Laravel
        """
        if not self.file_size:
            return "Unknown"
        
        bytes = self.file_size
        units = ["B", "KB", "MB", "GB"]
        
        for i in range(len(units) - 1):
            if bytes < 1024:
                break
            bytes /= 1024
        
        return f"{round(bytes, 2)} {units[i]}"


class DocumentChunk(models.Model):
    """
    DocumentChunk model - tương đương Laravel DocumentChunk model
    
    Trong Laravel:
    - protected $fillable = ['document_id', 'content', 'embedding']
    - protected $casts = ['embedding' => Vector::class]
    - use HasNeighbors; (cho vector search)
    """
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='chunks'
    )
    content = models.TextField()
    embedding = VectorField(dimensions=768, null=True, blank=True)  # 768 dimensions cho nomic-embed-text
    token_count = models.IntegerField(default=0)  # Pre-computed token count for performance
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['created_at']
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Chunk {self.id}: {content_preview}"


class ChatSession(models.Model):
    """
    ChatSession - Central chat conversations (like ChatGPT)
    Mỗi conversation tự động dùng TẤT CẢ documents của user
    """
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    
    # Optional: Link to a specific document (for document-specific chats)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_sessions'
    )
    
    # Session identification
    session_id = models.CharField(max_length=255, unique=True)  # UUID
    title = models.CharField(max_length=255, null=True, blank=True)  # Auto-generated from first message
    
    # Configuration
    system_prompt = models.TextField(
        default="You are a helpful assistant. Answer questions clearly and comprehensively. When the user asks about their uploaded documents, use the provided context. For general questions, use your knowledge to provide helpful answers."
    )
    model_provider = models.CharField(
        max_length=50,
        default='ollama',
        choices=[
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('ollama', 'Ollama'),
        ]
    )
    model_name = models.CharField(max_length=100, default='llama3.1')
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)
    max_tokens = models.IntegerField(default=2000)
    max_context_tokens = models.IntegerField(default=4000)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Statistics
    message_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-last_message_at', '-started_at']
        indexes = [
            models.Index(fields=['user', 'last_message_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['document', 'user']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.title or 'Untitled'}"
    
    def save(self, *args, **kwargs):
        """Auto-generate session_id (UUID) if not provided"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def get_user_documents(self):
        """
        Get all completed documents of the user
        Used for RAG retrieval in this conversation
        """
        return Document.objects.filter(
            user=self.user,
            status='completed'
        )


class ChatMessage(models.Model):
    """
    ChatMessage - Messages trong conversations hoặc document-specific chats
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    # Can belong to either a session (central chat) or document (document-specific chat)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='messages'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_messages'
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Analytics
    tokens_used = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # RAG context (sources used)
    sources = models.JSONField(default=list)  # Array of document chunks used
    # Format: [{"document_id": 1, "document_name": "doc.pdf", "chunk_id": 5, "relevance_score": 0.85}]
    
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['document', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"{self.role}: {content_preview}"
    
    def clean(self):
        """Ensure message belongs to either session OR document, not both"""
        from django.core.exceptions import ValidationError
        if not self.session and not self.document:
            raise ValidationError("Message must belong to either a session or a document")
        if self.session and self.document:
            raise ValidationError("Message cannot belong to both session and document")

