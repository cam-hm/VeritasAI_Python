# API Specification - MVP

## 🎯 Mục tiêu
Định nghĩa tất cả API endpoints cần thiết cho MVP với request/response schemas chi tiết.

---

## 🔐 Authentication

### JWT-based Authentication

**Base URL**: `/api/auth/`

#### 1. Register
```http
POST /api/auth/register
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "My Company"  // Auto-create organization
}

Response 201:
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "organization": {
    "id": 1,
    "name": "My Company",
    "slug": "my-company"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

Error 400:
{
  "error": "Validation failed",
  "details": {
    "email": ["This field is required."],
    "password": ["Password must be at least 8 characters."]
  }
}
```

#### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "organizations": [
      {
        "id": 1,
        "name": "My Company",
        "role": "admin"
      }
    ]
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

Error 401:
{
  "error": "Invalid credentials"
}
```

#### 3. Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

Request:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Logout
```http
POST /api/auth/logout
Authorization: Bearer {access_token}

Response 200:
{
  "message": "Logged out successfully"
}
```

---

## 🏢 Organizations

**Base URL**: `/api/organizations/`

**Authentication**: Required (JWT)

### List Organizations
```http
GET /api/organizations/
Authorization: Bearer {access_token}

Response 200:
{
  "organizations": [
    {
      "id": 1,
      "name": "My Company",
      "slug": "my-company",
      "role": "admin",  // User's role in this org
      "subscription_tier": "free",
      "member_count": 5,
      "document_count": 12,
      "created_at": "2025-11-18T10:00:00Z"
    }
  ]
}
```

### Get Organization
```http
GET /api/organizations/{id}/
Authorization: Bearer {access_token}

Response 200:
{
  "id": 1,
  "name": "My Company",
  "slug": "my-company",
  "subscription_tier": "free",
  "subscription_status": "active",
  "max_users": 5,
  "max_documents": 100,
  "max_storage_mb": 1000,
  "current_users": 3,
  "current_documents": 12,
  "current_storage_mb": 250,
  "settings": {},
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:00:00Z"
}

Error 403:
{
  "error": "You don't have permission to access this organization"
}
```

### Update Organization
```http
PATCH /api/organizations/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "name": "Updated Company Name",
  "settings": {
    "theme": "dark"
  }
}

Response 200:
{
  "id": 1,
  "name": "Updated Company Name",
  ...
}
```

### List Members
```http
GET /api/organizations/{id}/members/
Authorization: Bearer {access_token}

Response 200:
{
  "members": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "role": "admin",
      "joined_at": "2025-11-18T10:00:00Z"
    }
  ]
}
```

### Invite Member
```http
POST /api/organizations/{id}/members/invite
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "email": "newuser@example.com",
  "role": "editor"
}

Response 201:
{
  "message": "Invitation sent",
  "invitation": {
    "id": 1,
    "email": "newuser@example.com",
    "role": "editor",
    "invited_at": "2025-11-18T10:00:00Z"
  }
}
```

---

## 📄 Documents

**Base URL**: `/api/documents/`

**Authentication**: Required (JWT)

### List Documents
```http
GET /api/documents/
Authorization: Bearer {access_token}
Query Parameters:
  - organization_id (optional, default: user's org)
  - status (optional): pending|processing|completed|failed
  - category (optional)
  - search (optional): search in name
  - page (optional, default: 1)
  - page_size (optional, default: 20)

Response 200:
{
  "count": 50,
  "next": "http://api.example.com/api/documents/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "document.pdf",
      "file_size": 1024000,
      "formatted_file_size": "1.0 MB",
      "status": "completed",
      "num_chunks": 15,
      "category": "policies",
      "tags": ["important", "hr"],
      "created_at": "2025-11-18T10:00:00Z",
      "updated_at": "2025-11-18T10:05:00Z"
    }
  ]
}
```

### Upload Document
```http
POST /api/documents/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

Form Data:
  - file: (binary)
  - organization_id: (optional, default: user's org)
  - category: (optional)
  - tags: (optional, JSON array)

Response 201:
{
  "message": "File uploaded successfully",
  "document": {
    "id": 1,
    "name": "document.pdf",
    "status": "pending",
    "file_size": 1024000,
    "created_at": "2025-11-18T10:00:00Z"
  }
}

Error 400:
{
  "error": "File too large. Maximum size: 10MB"
}
```

### Get Document
```http
GET /api/documents/{id}/
Authorization: Bearer {access_token}

Response 200:
{
  "id": 1,
  "name": "document.pdf",
  "file_size": 1024000,
  "formatted_file_size": "1.0 MB",
  "status": "completed",
  "num_chunks": 15,
  "category": "policies",
  "tags": ["important", "hr"],
  "organization": {
    "id": 1,
    "name": "My Company"
  },
  "uploaded_by": {
    "id": 1,
    "email": "user@example.com"
  },
  "processed_at": "2025-11-18T10:05:00Z",
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:05:00Z"
}
```

### Delete Document
```http
DELETE /api/documents/{id}/
Authorization: Bearer {access_token}

Response 204: No Content

Error 403:
{
  "error": "You don't have permission to delete this document"
}
```

---

## 🤖 Chatbots

**Base URL**: `/api/chatbots/`

**Authentication**: Required (JWT)

### List Chatbots
```http
GET /api/chatbots/
Authorization: Bearer {access_token}
Query Parameters:
  - organization_id (optional)
  - is_public (optional): true|false

Response 200:
{
  "chatbots": [
    {
      "id": 1,
      "name": "HR Assistant",
      "description": "Answers HR questions",
      "model_provider": "ollama",
      "model_name": "llama3.1",
      "is_public": true,
      "document_count": 5,
      "created_at": "2025-11-18T10:00:00Z"
    }
  ]
}
```

### Create Chatbot
```http
POST /api/chatbots/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "name": "HR Assistant",
  "description": "Answers HR questions",
  "organization_id": 1,
  "system_prompt": "You are a helpful HR assistant...",
  "model_provider": "ollama",
  "model_name": "llama3.1",
  "temperature": 0.7,
  "max_tokens": 2000,
  "document_ids": [1, 2, 3]  // Documents to use
}

Response 201:
{
  "id": 1,
  "name": "HR Assistant",
  "description": "Answers HR questions",
  "system_prompt": "You are a helpful HR assistant...",
  "model_provider": "ollama",
  "model_name": "llama3.1",
  "temperature": 0.7,
  "max_tokens": 2000,
  "document_count": 3,
  "embed_code": "<script>...</script>",
  "created_at": "2025-11-18T10:00:00Z"
}
```

### Update Chatbot
```http
PATCH /api/chatbots/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "name": "Updated HR Assistant",
  "document_ids": [1, 2, 3, 4]  // Update documents
}

Response 200:
{
  "id": 1,
  "name": "Updated HR Assistant",
  ...
}
```

### Delete Chatbot
```http
DELETE /api/chatbots/{id}/
Authorization: Bearer {access_token}

Response 204: No Content
```

---

## 💬 Chat

**Base URL**: `/api/chat/`

**Authentication**: Required (JWT hoặc API Key)

### Stream Chat (Server-Sent Events)
```http
POST /api/chat/stream/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "chatbot_id": 1,
  "messages": [
    {
      "role": "user",
      "content": "What is our vacation policy?"
    }
  ],
  "session_id": "optional-uuid"  // Optional: continue existing session
}

Response 200 (Stream):
Content-Type: text/event-stream

data: {"content": "Based"}
data: {"content": " on"}
data: {"content": " the"}
...

Error 400:
data: {"error": "Chatbot not found"}

Error 400:
data: {"error": "Document not ready for chat"}
```

### List Chat Sessions
```http
GET /api/chat/sessions/
Authorization: Bearer {access_token}
Query Parameters:
  - chatbot_id (optional)
  - page (optional)
  - page_size (optional)

Response 200:
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "session_id": "uuid-here",
      "chatbot": {
        "id": 1,
        "name": "HR Assistant"
      },
      "title": "Vacation policy question",
      "message_count": 5,
      "last_message_at": "2025-11-18T10:00:00Z",
      "started_at": "2025-11-18T09:55:00Z"
    }
  ]
}
```

### Get Chat Session
```http
GET /api/chat/sessions/{id}/
Authorization: Bearer {access_token}

Response 200:
{
  "id": 1,
  "session_id": "uuid-here",
  "chatbot": {
    "id": 1,
    "name": "HR Assistant"
  },
  "title": "Vacation policy question",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What is our vacation policy?",
      "created_at": "2025-11-18T09:55:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Based on the document...",
      "sources": [
        {
          "document_id": 1,
          "document_name": "HR Policy.pdf",
          "chunk_id": 5
        }
      ],
      "created_at": "2025-11-18T09:55:05Z"
    }
  ],
  "message_count": 5,
  "started_at": "2025-11-18T09:55:00Z",
  "last_message_at": "2025-11-18T10:00:00Z"
}
```

### Delete Chat Session
```http
DELETE /api/chat/sessions/{id}/
Authorization: Bearer {access_token}

Response 204: No Content
```

---

## 🔑 API Keys

**Base URL**: `/api/api-keys/`

**Authentication**: Required (JWT, Admin/Editor role)

### List API Keys
```http
GET /api/api-keys/
Authorization: Bearer {access_token}

Response 200:
{
  "api_keys": [
    {
      "id": 1,
      "name": "Production API Key",
      "key_prefix": "sk_live_",
      "rate_limit": 100,
      "last_used_at": "2025-11-18T10:00:00Z",
      "is_active": true,
      "created_at": "2025-11-18T09:00:00Z"
    }
  ]
}
```

### Create API Key
```http
POST /api/api-keys/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "name": "Production API Key",
  "rate_limit": 100,
  "expires_at": "2026-11-18T10:00:00Z"  // Optional
}

Response 201:
{
  "id": 1,
  "name": "Production API Key",
  "api_key": "sk_live_abc123xyz...",  // Only shown once!
  "key_prefix": "sk_live_",
  "rate_limit": 100,
  "created_at": "2025-11-18T10:00:00Z"
}

⚠️ IMPORTANT: API key chỉ hiển thị 1 lần khi tạo!
```

### Delete API Key
```http
DELETE /api/api-keys/{id}/
Authorization: Bearer {access_token}

Response 204: No Content
```

---

## 📊 Error Responses

### Standard Error Format

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    // Additional error details
  }
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success, no content
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_REQUIRED`: Need to login
- `PERMISSION_DENIED`: Don't have permission
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `ORGANIZATION_LIMIT_EXCEEDED`: Organization limit reached
- `FILE_TOO_LARGE`: File exceeds size limit
- `INVALID_FILE_TYPE`: File type not supported

---

## 🔒 Rate Limiting

### Default Limits (MVP)

- **Authenticated users**: 100 requests/hour
- **API keys**: Configurable per key (default: 100/hour)
- **File upload**: 10 uploads/hour per user
- **Chat**: 50 messages/hour per user

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1637251200
```

---

## 📝 Next Steps

1. ✅ Review và approve API specification
2. ✅ Implement API endpoints
3. ✅ Create API documentation (Swagger/OpenAPI)
4. ✅ Write API tests
5. ✅ Create API client examples

