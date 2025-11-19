# Database Schema Design - MVP

## 🎯 Mục tiêu
Thiết kế database schema cho MVP với multi-tenant support, đảm bảo data isolation và scalability.

---

## 📊 Current State Analysis

### Models hiện có:
- ✅ `Document` - Quản lý documents
- ✅ `DocumentChunk` - Chunks với embeddings
- ✅ `ChatMessage` - Chat messages
- ⚠️ Dùng default Django `User` model
- ❌ Chưa có `Organization` model (cần cho multi-tenant)
- ❌ Chưa có `Chatbot` model (hiện chat trực tiếp với document)

---

## 🗄️ MVP Database Schema

### 1. Organizations (Multi-tenant Core)

```python
class Organization(models.Model):
    """
    Organization model - Multi-tenant isolation
    Mỗi organization là một tenant riêng biệt
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # URL-friendly identifier
    domain = models.CharField(max_length=255, null=True, blank=True)  # Custom domain
    
    # Subscription info (MVP: simple, extend later)
    subscription_tier = models.CharField(
        max_length=50, 
        default='free',
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
        ]
    )
    subscription_status = models.CharField(
        max_length=50,
        default='active',
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('canceled', 'Canceled'),
        ]
    )
    
    # Limits (MVP: hard limits, extend to soft limits later)
    max_users = models.IntegerField(default=5)
    max_documents = models.IntegerField(default=100)
    max_storage_mb = models.IntegerField(default=1000)  # 1GB default
    
    # Settings
    settings = models.JSONField(default=dict)  # Flexible settings storage
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
```

### 2. Organization Members (Many-to-Many)

```python
class OrganizationMember(models.Model):
    """
    OrganizationMember - Join table giữa User và Organization
    Quản lý roles và permissions
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer')
    
    # Invitation tracking
    invited_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='invitations_sent'
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'organization_members'
        unique_together = [['organization', 'user']]
        indexes = [
            models.Index(fields=['organization', 'user']),
            models.Index(fields=['user', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
```

### 3. Documents (Updated for Multi-tenant)

```python
class Document(models.Model):
    """
    Document model - Updated với organization support
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Multi-tenant: Mỗi document thuộc về một organization
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    # Existing fields
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=500)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
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
    is_public = models.BooleanField(default=False)  # Public within org
    access_level = models.CharField(
        max_length=50,
        default='team',
        choices=[
            ('public', 'Public'),
            ('team', 'Team'),
            ('private', 'Private'),
        ]
    )
    metadata = models.JSONField(default=dict)  # Flexible metadata
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return self.name
```

### 4. Chatbots (New Model)

```python
class Chatbot(models.Model):
    """
    Chatbot model - Tạo chatbot từ documents
    MVP: Simple configuration
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='chatbots'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_chatbots'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    
    # Configuration
    system_prompt = models.TextField(
        default="You are a helpful assistant. Answer questions based on the provided context."
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
    
    # Sharing
    is_public = models.BooleanField(default=False)  # Public within org
    embed_code = models.TextField(null=True, blank=True)  # Generated embed code
    
    # Settings
    settings = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbots'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_public']),
        ]
    
    def __str__(self):
        return self.name
```

### 5. Chatbot Documents (Many-to-Many)

```python
class ChatbotDocument(models.Model):
    """
    ChatbotDocument - Join table giữa Chatbot và Document
    Quản lý documents nào được dùng trong chatbot nào
    """
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='chatbot_documents'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chatbot_documents'
    )
    priority = models.IntegerField(default=0)  # Higher = more important
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_documents'
        unique_together = [['chatbot', 'document']]
        indexes = [
            models.Index(fields=['chatbot', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.chatbot.name} - {self.document.name}"
```

### 6. Chat Sessions (New Model)

```python
class ChatSession(models.Model):
    """
    ChatSession - Quản lý chat sessions
    Mỗi conversation là một session
    """
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='chat_sessions'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    
    session_id = models.CharField(max_length=255, unique=True)  # UUID
    title = models.CharField(max_length=255, null=True, blank=True)  # Auto-generated from first message
    metadata = models.JSONField(default=dict)
    
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    message_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['organization', 'last_message_at']),
            models.Index(fields=['user', 'last_message_at']),
            models.Index(fields=['chatbot', 'last_message_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.chatbot.name}"
```

### 7. Chat Messages (Updated)

```python
class ChatMessage(models.Model):
    """
    ChatMessage - Updated với session support
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    chatbot = models.ForeignKey(
        Chatbot,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    # Keep document for backward compatibility (optional)
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Analytics
    tokens_used = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    sources = models.JSONField(default=list)  # Array of document chunks used
    
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['chatbot', 'created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"{self.role}: {content_preview}"
```

### 8. API Keys (New Model - MVP: Basic)

```python
class APIKey(models.Model):
    """
    APIKey - API authentication cho organizations
    MVP: Simple API keys, extend later với scopes
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='api_keys'
    )
    
    name = models.CharField(max_length=255)  # User-friendly name
    key_hash = models.CharField(max_length=255, unique=True)  # Hashed API key
    key_prefix = models.CharField(max_length=20)  # First 8 chars for display (e.g., "sk_live_")
    
    # Permissions (MVP: simple, extend later)
    permissions = models.JSONField(default=dict)
    rate_limit = models.IntegerField(default=100)  # Requests per hour
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_keys'
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['key_hash']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
```

---

## 🔗 Relationships Summary

```
Organization (1) ──< (N) OrganizationMember (N) >── (1) User
Organization (1) ──< (N) Document
Organization (1) ──< (N) Chatbot
Organization (1) ──< (N) ChatSession
Organization (1) ──< (N) APIKey

Document (1) ──< (N) DocumentChunk
Document (1) ──< (N) ChatbotDocument (N) >── (1) Chatbot

Chatbot (1) ──< (N) ChatSession
Chatbot (1) ──< (N) ChatMessage

ChatSession (1) ──< (N) ChatMessage
```

---

## 📊 Indexes Strategy

### Performance Indexes

```sql
-- Organization queries
CREATE INDEX idx_organization_members_org_user ON organization_members(organization_id, user_id);
CREATE INDEX idx_organization_members_user_role ON organization_members(user_id, role);

-- Document queries
CREATE INDEX idx_documents_org_status ON documents(organization_id, status);
CREATE INDEX idx_documents_org_created ON documents(organization_id, created_at);
CREATE INDEX idx_documents_hash ON documents(file_hash);

-- Vector search (pgvector)
CREATE INDEX idx_document_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Chat queries
CREATE INDEX idx_chat_sessions_org_date ON chat_sessions(organization_id, last_message_at);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_chatbot ON chat_messages(chatbot_id, created_at);

-- API keys
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_org_active ON api_keys(organization_id, is_active);
```

---

## 🔄 Migration Strategy

### Step 1: Add Organization Model
```python
# Migration 0003_add_organization.py
# - Create Organization model
# - Create OrganizationMember model
```

### Step 2: Update Existing Models
```python
# Migration 0004_add_organization_to_documents.py
# - Add organization FK to Document
# - Migrate existing documents to default organization
# - Add indexes
```

### Step 3: Add Chatbot Models
```python
# Migration 0005_add_chatbot_models.py
# - Create Chatbot model
# - Create ChatbotDocument model
# - Create ChatSession model
# - Update ChatMessage model
```

### Step 4: Add API Keys
```python
# Migration 0006_add_api_keys.py
# - Create APIKey model
```

---

## 🎯 Data Isolation Strategy

### Multi-tenant Isolation

**Approach**: Row-level security với organization_id

1. **All queries filter by organization_id**
   ```python
   # Always filter by organization
   documents = Document.objects.filter(organization=request.user.organization)
   ```

2. **Middleware to set organization context**
   ```python
   # Middleware to automatically filter by user's organization
   class OrganizationMiddleware:
       def process_request(self, request):
           if request.user.is_authenticated:
               org = request.user.organization_memberships.first().organization
               request.organization = org
   ```

3. **Model managers for automatic filtering**
   ```python
   class OrganizationManager(models.Manager):
       def get_queryset(self):
           # Auto-filter by organization from request context
           return super().get_queryset().filter(organization=...)
   ```

---

## 📝 Next Steps

1. ✅ Review và approve schema design
2. ✅ Create Django models
3. ✅ Create migrations
4. ✅ Test migrations với existing data
5. ✅ Update existing code to use new models

