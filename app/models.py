"""
Django Models
Tương đương với app/Models/ trong Laravel

Django ORM tương đương với Eloquent ORM trong Laravel
"""

from django.db import models
# Tạm thời dùng default Django User (auth.User)
# Có thể customize sau bằng cách tạo custom User model
try:
    from pgvector.django import VectorField
except ImportError:
    # Fallback nếu pgvector chưa được cài đặt
    VectorField = models.TextField


class Document(models.Model):
    """
    Document model - tương đương Laravel Document model
    
    Trong Laravel:
    - protected $fillable = ['name', 'path', 'user_id', 'status', ...]
    - public function chunks(): HasMany
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=500)  # File path trong storage
    user = models.ForeignKey(
        'auth.User',  # Dùng default Django User model
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='documents'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    num_chunks = models.IntegerField(default=0)
    embedding_model = models.CharField(max_length=100, null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # Size in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
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


class ChatMessage(models.Model):
    """
    ChatMessage model - tương đương Laravel ChatMessage model
    
    Trong Laravel:
    - protected $fillable = ['document_id', 'user_id', 'role', 'content']
    - role: 'user' or 'ai'
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_messages'
    )
    user = models.ForeignKey(
        'auth.User',  # Dùng default Django User model
        on_delete=models.CASCADE, 
        related_name='chat_messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
    
    def __str__(self):
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"{self.role}: {content_preview}"

