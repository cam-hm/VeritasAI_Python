# Database Schema Design - MVP

## 🎯 Mục tiêu
Thiết kế database schema cho MVP - Single service như ChatGPT, user đăng ký và sử dụng dịch vụ.

---

## 📊 MVP Requirements

### Core Features:
1. ✅ User đăng ký/đăng nhập
2. ✅ User quản lý documents
3. ✅ Chat trên từng document (giữ như hiện tại)
4. ✅ Central chat place với conversations (như ChatGPT)
   - Mỗi conversation tự động dùng TẤT CẢ documents của user
   - User có thể tạo nhiều conversations

---

## 🗄️ MVP Database Schema

### 1. User (Django Default)

**Decision**: Dùng Django default User model, có thể extend sau nếu cần.

**Fields** (Django default):
- `id`, `username`, `email`, `password`, `first_name`, `last_name`
- `is_active`, `is_staff`, `is_superuser`
- `date_joined`, `last_login`

**Note**: Có thể tạo custom User model sau nếu cần thêm fields (subscription tier, limits, etc.)

---

### 2. Document (Updated - Keep existing)

```python
class Document(models.Model):
    """
    Document model - User's uploaded documents
    Giữ nguyên structure hiện tại, chỉ cần user FK
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    num_chunks = models.IntegerField(default=0)
    embedding_model = models.CharField(max_length=100, null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True, unique=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    # New fields for MVP
    category = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(default=list)  # Array of tags
    metadata = models.JSONField(default=dict)  # Flexible metadata
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_formatted_file_size(self):
        """Get formatted file size (e.g., "2.5 MB")"""
        if not self.file_size:
            return "Unknown"
        
        bytes = self.file_size
        units = ["B", "KB", "MB", "GB"]
        
        for i in range(len(units) - 1):
            if bytes < 1024:
                break
            bytes /= 1024
        
        return f"{round(bytes, 2)} {units[i]}"
```

---

### 3. DocumentChunk (Keep existing)

```python
class DocumentChunk(models.Model):
    """
    DocumentChunk model - Chunks với embeddings
    Giữ nguyên như hiện tại
    """
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='chunks'
    )
    content = models.TextField()
    embedding = VectorField(dimensions=768, null=True, blank=True)  # 768 dimensions cho nomic-embed-text
    token_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['created_at']
        indexes = [
            # Vector search index (pgvector)
            # Will be created via migration
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Chunk {self.id}: {content_preview}"
```

---

### 4. ChatSession (New Model)

```python
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
    
    # Session identification
    session_id = models.CharField(max_length=255, unique=True)  # UUID
    title = models.CharField(max_length=255, null=True, blank=True)  # Auto-generated from first message
    
    # Configuration
    system_prompt = models.TextField(
        default="You are a helpful assistant. Answer questions based on the user's uploaded documents."
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
        ]
    
    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.title or 'Untitled'}"
    
    def get_user_documents(self):
        """
        Get all completed documents of the user
        Used for RAG retrieval in this conversation
        """
        return Document.objects.filter(
            user=self.user,
            status='completed'
        )
```

---

### 5. ChatMessage (Updated)

```python
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
```

---

## 🔗 Relationships Summary

```
User (1) ──< (N) Document
User (1) ──< (N) ChatSession
User (1) ──< (N) ChatMessage

Document (1) ──< (N) DocumentChunk
Document (1) ──< (N) ChatMessage (document-specific chat)

ChatSession (1) ──< (N) ChatMessage (central chat)
```

---

## 📊 Indexes Strategy

### Performance Indexes

```sql
-- Document queries
CREATE INDEX idx_documents_user_status ON documents(user_id, status);
CREATE INDEX idx_documents_user_created ON documents(user_id, created_at);
CREATE INDEX idx_documents_hash ON documents(file_hash);

-- Vector search (pgvector)
CREATE INDEX idx_document_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Chat queries
CREATE INDEX idx_chat_sessions_user_date ON chat_sessions(user_id, last_message_at);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_document ON chat_messages(document_id, created_at);
CREATE INDEX idx_chat_messages_user ON chat_messages(user_id, created_at);
```

---

## 🔄 Migration Strategy

### Step 1: Update Document Model
```python
# Migration 0003_update_document_user.py
# - Change user FK from SET_NULL to CASCADE
# - Add category, tags, metadata fields
# - Add indexes
```

### Step 2: Create ChatSession Model
```python
# Migration 0004_create_chat_session.py
# - Create ChatSession model
```

### Step 3: Update ChatMessage Model
```python
# Migration 0005_update_chat_message.py
# - Add session FK
# - Update role choices (add 'assistant', 'system')
# - Add analytics fields (tokens_used, model_used, etc.)
# - Add sources field
# - Add validation (session OR document, not both)
```

---

## 🎯 Data Flow

### Central Chat (ChatGPT-like)
```
User → ChatSession → ChatMessage
                    ↓
            RAG Retrieval từ TẤT CẢ documents của user
                    ↓
            Generate response với context
```

### Document-Specific Chat
```
User → Document → ChatMessage
                  ↓
          RAG Retrieval từ document đó
                  ↓
          Generate response với context
```

---

## 📝 Notes

- **No multi-tenant**: Single service, mỗi user có data riêng
- **Central chat**: Mỗi conversation tự động dùng tất cả documents của user
- **Document chat**: Vẫn giữ như hiện tại, chat với 1 document cụ thể
- **Flexible**: Có thể extend sau (subscription tiers, limits, etc.)
