# Technical Decisions - MVP

## 🎯 Mục tiêu
Ghi lại tất cả các quyết định kỹ thuật quan trọng cho MVP, đảm bảo consistency và tránh technical debt.

---

## 🏗️ Architecture Decisions

### 1. Multi-tenant Strategy

**Decision**: Row-level security với `organization_id`

**Rationale**:
- Đơn giản, dễ implement
- Phù hợp với MVP
- Có thể scale lên schema-per-tenant sau nếu cần

**Implementation**:
- Tất cả models có `organization` ForeignKey
- Middleware tự động filter queries theo organization
- Model managers tự động thêm organization filter

**Alternatives considered**:
- Schema-per-tenant: Phức tạp hơn, không cần cho MVP
- Database-per-tenant: Overkill cho MVP

---

### 2. Authentication Strategy

**Decision**: JWT với refresh tokens

**Rationale**:
- Stateless, scalable
- Phù hợp với API-first architecture
- Dễ implement với Django REST Framework

**Implementation**:
- Use `djangorestframework-simplejwt`
- Access token: 15 minutes
- Refresh token: 7 days
- Store refresh tokens in database (blacklist support)

**Alternatives considered**:
- Session-based: Không phù hợp với API
- OAuth2: Phức tạp hơn, có thể thêm sau

---

### 3. File Storage Strategy

**Decision**: Local filesystem (MVP) → S3/MinIO (later)

**Rationale**:
- Đơn giản cho MVP
- Dễ migrate lên S3 sau
- Không cần setup thêm service

**Implementation**:
- Store files in `storage/documents/`
- Use Django `FileField` hoặc custom storage
- File naming: `{hash}.{extension}`

**Migration path**:
- Abstract storage layer
- Easy to switch to S3/MinIO later

---

### 4. Background Job Processing

**Decision**: Celery với Redis broker

**Rationale**:
- Đã có trong project
- Reliable và scalable
- Good error handling

**Implementation**:
- Celery tasks cho document processing
- Redis làm message broker
- Fallback to subprocess nếu Celery không available

**Alternatives considered**:
- Django-Q: Simpler nhưng ít features
- RQ: Simpler nhưng ít features
- Pure subprocess: Không scalable

---

### 5. Vector Search Strategy

**Decision**: PostgreSQL + pgvector

**Rationale**:
- Đã có trong project
- Integrated với Django ORM
- Good performance cho MVP scale

**Implementation**:
- Use `pgvector` extension
- IVFFlat index cho performance
- Cosine distance cho similarity

**Alternatives considered**:
- Pinecone: External service, cost
- Weaviate: External service, complexity
- Qdrant: External service, complexity

---

### 6. LLM Provider Strategy

**Decision**: Ollama (default) với support cho OpenAI/Anthropic

**Rationale**:
- Ollama: Free, self-hosted, good for development
- OpenAI/Anthropic: Better quality, paid
- Flexible: Users can choose

**Implementation**:
- Abstract LLM client interface
- Support multiple providers
- Configurable per chatbot

**Alternatives considered**:
- OpenAI only: Lock-in, cost
- Ollama only: Lower quality

---

### 7. Frontend Strategy

**Decision**: Server-side rendering với Alpine.js (MVP) → React/Vue (later)

**Rationale**:
- Đơn giản cho MVP
- Không cần separate frontend project
- Fast development

**Implementation**:
- Django templates
- Tailwind CSS
- Alpine.js cho interactivity

**Migration path**:
- API-first design
- Easy to build separate frontend later

**Alternatives considered**:
- React from start: Phức tạp hơn, slower development
- Next.js: Overkill cho MVP

---

### 8. API Design Pattern

**Decision**: RESTful API với Django REST Framework

**Rationale**:
- Standard, well-understood
- Good tooling support
- Easy to document

**Implementation**:
- Use DRF ViewSets
- Serializers cho request/response
- Pagination, filtering, sorting

**Alternatives considered**:
- GraphQL: Phức tạp hơn, không cần cho MVP
- gRPC: Overkill cho MVP

---

### 9. Error Handling Strategy

**Decision**: Standardized error responses với error codes

**Rationale**:
- Consistent API responses
- Easy to handle on client
- Good debugging

**Implementation**:
- Custom exception classes
- Exception handler middleware
- Standard error format:
  ```json
  {
    "error": "Error message",
    "code": "ERROR_CODE",
    "details": {}
  }
  ```

---

### 10. Testing Strategy

**Decision**: pytest với coverage goal 80%+

**Rationale**:
- Better than Django's default test framework
- Good fixtures support
- Good coverage tools

**Implementation**:
- Unit tests cho models, services
- Integration tests cho API endpoints
- E2E tests cho critical flows

**Coverage goals**:
- Models: 90%+
- Services: 85%+
- Views/API: 80%+
- Overall: 80%+

---

### 11. Code Organization

**Decision**: Django app structure với service layer

**Structure**:
```
app/
├── models.py          # Database models
├── serializers.py     # DRF serializers
├── views.py           # API views
├── urls.py            # URL routing
├── services/          # Business logic
│   ├── document_service.py
│   ├── chatbot_service.py
│   ├── chat_service.py
│   └── embedding_service.py
├── tasks/             # Celery tasks
└── management/         # Django commands
```

**Rationale**:
- Clear separation of concerns
- Business logic in services
- Views chỉ handle HTTP
- Easy to test

---

### 12. Database Migration Strategy

**Decision**: Django migrations với backward compatibility

**Rationale**:
- Standard Django approach
- Version controlled
- Reversible

**Best practices**:
- Always make migrations backward compatible
- Test migrations với production-like data
- Never edit existing migrations

---

### 13. Logging Strategy

**Decision**: Python logging với structured logging

**Implementation**:
- Use Python `logging` module
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Structured format: JSON cho production
- Log to files + stdout

**What to log**:
- API requests/responses (INFO)
- Errors với stack traces (ERROR)
- Background job status (INFO)
- Performance metrics (INFO)

**What NOT to log**:
- Passwords, API keys
- Sensitive user data
- Full request bodies (chỉ log metadata)

---

### 14. Security Decisions

#### 14.1 Password Hashing
**Decision**: Django's default (PBKDF2) → Argon2 (later)

**Rationale**:
- Django default is secure enough for MVP
- Can upgrade to Argon2 later

#### 14.2 API Key Storage
**Decision**: Hash API keys (bcrypt) với prefix display

**Rationale**:
- Security: Never store plain API keys
- UX: Show prefix for identification

#### 14.3 CORS
**Decision**: Restrictive CORS, configurable per environment

**Rationale**:
- Security best practice
- Configurable for development

---

### 15. Performance Decisions

#### 15.1 Caching Strategy
**Decision**: Redis caching với TTL

**What to cache**:
- Query embeddings (1 hour)
- Document metadata (5 minutes)
- User sessions (default Django)

#### 15.2 Database Queries
**Decision**: Use select_related/prefetch_related, avoid N+1

**Rationale**:
- Performance critical
- Django ORM best practices

#### 15.3 Background Jobs
**Decision**: Async processing cho heavy operations

**What to process async**:
- Document processing
- Embedding generation
- Email sending

---

### 16. Deployment Strategy (Future)

**Decision**: Docker + Docker Compose (dev) → Kubernetes (prod)

**Rationale**:
- Docker: Easy local development
- Kubernetes: Production scalability

**MVP**: Docker Compose đủ
**Production**: Kubernetes với Helm charts

---

## 📋 Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2025-11-18 | Multi-tenant: Row-level | Simple, scalable | ✅ Approved |
| 2025-11-18 | Auth: JWT | Stateless, API-friendly | ✅ Approved |
| 2025-11-18 | Storage: Local → S3 | Simple MVP, easy migration | ✅ Approved |
| 2025-11-18 | Jobs: Celery | Reliable, scalable | ✅ Approved |
| 2025-11-18 | Vector: pgvector | Integrated, performant | ✅ Approved |
| 2025-11-18 | LLM: Multi-provider | Flexible, not locked-in | ✅ Approved |
| 2025-11-18 | Frontend: SSR → SPA | Fast MVP, easy migration | ✅ Approved |

---

## 🔄 Revisit Decisions

Các decisions này sẽ được review lại khi:
- Scale requirements change
- New requirements emerge
- Performance issues
- Security concerns

---

## 📝 Notes

- **Keep it simple**: MVP nên đơn giản, có thể extend sau
- **Migration path**: Luôn có plan để migrate lên solution tốt hơn
- **Document decisions**: Ghi lại lý do để team hiểu
- **Review regularly**: Revisit decisions khi có thay đổi

