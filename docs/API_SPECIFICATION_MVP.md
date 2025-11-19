# API Specification - MVP

## 🎯 Mục tiêu
Định nghĩa API endpoints cho MVP - Single service như ChatGPT.

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
  "last_name": "Doe"
}

Response 201:
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
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
    "last_name": "Doe"
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

## 📄 Documents

**Base URL**: `/api/documents/`

**Authentication**: Required (JWT)

### List Documents
```http
GET /api/documents/
Authorization: Bearer {access_token}
Query Parameters:
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
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:05:00Z"
}
```

### Delete Document
```http
DELETE /api/documents/{id}/
Authorization: Bearer {access_token}

Response 204: No Content
```

---

## 💬 Chat Sessions (Central Chat)

**Base URL**: `/api/chat/sessions/`

**Authentication**: Required (JWT)

### List Chat Sessions
```http
GET /api/chat/sessions/
Authorization: Bearer {access_token}
Query Parameters:
  - page (optional)
  - page_size (optional)

Response 200:
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "session_id": "uuid-here",
      "title": "Vacation policy question",
      "message_count": 5,
      "last_message_at": "2025-11-18T10:00:00Z",
      "started_at": "2025-11-18T09:55:00Z"
    }
  ]
}
```

### Create Chat Session
```http
POST /api/chat/sessions/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "title": "New Conversation"  // Optional, auto-generated if not provided
}

Response 201:
{
  "id": 1,
  "session_id": "uuid-here",
  "title": "New Conversation",
  "message_count": 0,
  "started_at": "2025-11-18T10:00:00Z"
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
          "chunk_id": 5,
          "relevance_score": 0.85
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

### Update Chat Session
```http
PATCH /api/chat/sessions/{id}/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "title": "Updated title"
}

Response 200:
{
  "id": 1,
  "title": "Updated title",
  ...
}
```

### Delete Chat Session
```http
DELETE /api/chat/sessions/{id}/
Authorization: Bearer {access_token}

Response 204: No Content
```

---

## 💬 Chat Messages

**Base URL**: `/api/chat/`

**Authentication**: Required (JWT)

### Stream Chat (Server-Sent Events)

#### Central Chat (uses all user documents)
```http
POST /api/chat/stream/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "session_id": "uuid-here",  // Required for central chat
  "messages": [
    {
      "role": "user",
      "content": "What is our vacation policy?"
    }
  ]
}

Response 200 (Stream):
Content-Type: text/event-stream

data: {"content": "Based"}
data: {"content": " on"}
data: {"content": " the"}
...

Error 400:
data: {"error": "Session not found"}
```

#### Document-Specific Chat
```http
POST /api/chat/stream/
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "document_id": 1,  // Required for document-specific chat
  "messages": [
    {
      "role": "user",
      "content": "What is in this document?"
    }
  ]
}

Response 200 (Stream):
Content-Type: text/event-stream

data: {"content": "This"}
data: {"content": " document"}
...

Error 400:
data: {"error": "Document not ready for chat"}
```

**Note**: 
- `session_id` = Central chat (uses ALL user documents)
- `document_id` = Document-specific chat (uses only that document)
- Cannot use both at the same time

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
- `FILE_TOO_LARGE`: File exceeds size limit
- `INVALID_FILE_TYPE`: File type not supported

---

## 🔒 Rate Limiting

### Default Limits (MVP)

- **Authenticated users**: 100 requests/hour
- **File upload**: 10 uploads/hour per user
- **Chat**: 50 messages/hour per user

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1637251200
```

---

## 📝 Notes

- **Single service**: No multi-tenant, each user has their own data
- **Central chat**: Automatically uses ALL user's documents for RAG
- **Document chat**: Still available for document-specific queries
- **Simple**: Focus on core features, can extend later
