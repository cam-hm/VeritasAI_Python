# Prototype to SAAS Migration Plan

## 📊 Current State Analysis

### Code hiện tại = Prototype/Proof of Concept

**Đặc điểm của prototype hiện tại:**
- ✅ Single-user: Dùng Django default User, không có Organization
- ✅ Direct document chat: Chat trực tiếp với document, không có Chatbot abstraction
- ✅ Simple authentication: Chưa có JWT, chưa có API keys
- ✅ No multi-tenant: Tất cả documents trong cùng một pool
- ✅ Basic features: Upload, process, chat - đủ để test concept

**Giá trị của prototype:**
- ✅ Validate RAG concept hoạt động
- ✅ Test technical stack (Django, pgvector, Ollama)
- ✅ Core services đã implement (embedding, chunking, chat)
- ✅ Có thể reuse một phần code

---

## 🎯 SAAS MVP Requirements

### Khác biệt chính:

| Aspect | Prototype | SAAS MVP |
|--------|-----------|----------|
| **Users** | Single user | Multi-user với organizations |
| **Data Isolation** | None | Organization-based isolation |
| **Chat** | Direct với document | Chatbot abstraction |
| **Authentication** | Django default | JWT + API keys |
| **Permissions** | None | Role-based (admin/editor/viewer) |
| **API** | Basic | Full RESTful API |
| **Security** | Basic | Enterprise-grade |

---

## 🔄 Migration Strategy

### Option 1: Refactor Existing Code (Recommended)

**Pros:**
- Reuse existing services (embedding, chunking, chat logic)
- Faster development
- Less risk (đã test được)

**Cons:**
- Cần refactor nhiều
- Có thể có technical debt

**Approach:**
1. Keep services layer (embedding_service, chunking_service, etc.)
2. Refactor models (add Organization, Chatbot, etc.)
3. Refactor views (add authentication, permissions)
4. Update templates (add multi-tenant UI)

### Option 2: Start Fresh

**Pros:**
- Clean codebase
- No legacy code
- Better architecture from start

**Cons:**
- Slower (phải rewrite everything)
- Risk of losing working code

**Approach:**
- Copy services code
- Build new models/views from scratch
- Reference prototype for logic

---

## 📋 Recommended Approach: Hybrid

### Phase 1: Keep & Refactor Core Services

**Services to keep (minimal changes):**
- ✅ `embedding_service.py` - Logic tốt, chỉ cần config
- ✅ `chunking_service.py` - Logic tốt, reusable
- ✅ `text_extraction_service.py` - Logic tốt, reusable
- ✅ `token_estimation_service.py` - Logic tốt, reusable
- ✅ `ollama_client.py` - Logic tốt, có thể extend cho multi-provider

**Services to refactor:**
- ⚠️ Chat logic - Cần refactor để support Chatbot abstraction
- ⚠️ Document processing - Cần add organization context

### Phase 2: New Models & Database

**New models to create:**
- ✅ `Organization` - Multi-tenant core
- ✅ `OrganizationMember` - User-Organization relationship
- ✅ `Chatbot` - Chatbot abstraction
- ✅ `ChatbotDocument` - Many-to-many
- ✅ `ChatSession` - Session management
- ✅ `APIKey` - API authentication

**Models to update:**
- ⚠️ `Document` - Add organization FK
- ⚠️ `ChatMessage` - Add session, chatbot FKs

### Phase 3: New API Layer

**New API endpoints:**
- ✅ Authentication (JWT)
- ✅ Organizations management
- ✅ Chatbots management
- ✅ Chat sessions
- ✅ API keys

**Views to refactor:**
- ⚠️ Document views - Add organization filtering
- ⚠️ Chat views - Support chatbot abstraction

---

## 🗂️ Code Organization Plan

### New Structure

```
app/
├── models.py                    # All models (new + updated)
├── serializers.py               # DRF serializers
├── views/                       # Split views by domain
│   ├── auth_views.py
│   ├── organization_views.py
│   ├── document_views.py
│   ├── chatbot_views.py
│   └── chat_views.py
├── urls.py                      # URL routing
├── services/                    # Keep & refactor
│   ├── embedding_service.py    # ✅ Keep
│   ├── chunking_service.py     # ✅ Keep
│   ├── text_extraction_service.py  # ✅ Keep
│   ├── token_estimation_service.py # ✅ Keep
│   ├── ollama_client.py        # ✅ Keep, extend
│   ├── document_service.py     # ⚠️ New: Business logic
│   ├── chatbot_service.py      # ⚠️ New: Business logic
│   └── chat_service.py         # ⚠️ Refactor: Support chatbot
├── tasks/                       # Celery tasks
│   └── document_tasks.py       # ⚠️ Update: Add org context
├── permissions.py              # ⚠️ New: Custom permissions
├── middleware.py               # ⚠️ New: Organization middleware
└── management/commands/         # Keep
```

---

## 🔧 Migration Steps

### Step 1: Database Migration

1. Create new models (Organization, Chatbot, etc.)
2. Create migrations
3. Migrate existing data:
   - Create default organization
   - Assign existing documents to default org
   - Create default chatbot for each document (optional)

### Step 2: Authentication

1. Install `djangorestframework-simplejwt`
2. Implement JWT authentication
3. Create auth endpoints
4. Update existing views to use JWT

### Step 3: Multi-tenant

1. Add Organization middleware
2. Update all queries to filter by organization
3. Add organization context to services
4. Test data isolation

### Step 4: Chatbot Abstraction

1. Create Chatbot model
2. Refactor chat logic to use Chatbot
3. Update chat endpoints
4. Migrate existing chat messages (optional)

### Step 5: API Layer

1. Create serializers
2. Create ViewSets
3. Add permissions
4. Add API documentation

---

## 📊 Code Reusability Analysis

### High Reusability (Keep as-is)
- ✅ `embedding_service.py` - 90% reusable
- ✅ `chunking_service.py` - 95% reusable
- ✅ `text_extraction_service.py` - 90% reusable
- ✅ `token_estimation_service.py` - 100% reusable
- ✅ `ollama_client.py` - 80% reusable (extend for multi-provider)

### Medium Reusability (Refactor)
- ⚠️ `chat_stream` view - 60% reusable (need chatbot abstraction)
- ⚠️ `document_upload` view - 70% reusable (need org context)
- ⚠️ Document processing task - 70% reusable (need org context)

### Low Reusability (Rewrite)
- ❌ Current models - Need complete rewrite for multi-tenant
- ❌ Current views structure - Need RESTful API structure
- ❌ Templates - Need multi-tenant UI

---

## 🎯 Action Plan

### Week 1: Foundation
- [ ] Create new models (Organization, Chatbot, etc.)
- [ ] Create migrations
- [ ] Migrate existing data
- [ ] Setup JWT authentication

### Week 2: Multi-tenant
- [ ] Add Organization middleware
- [ ] Update Document model với organization
- [ ] Update all queries
- [ ] Test data isolation

### Week 3: Chatbot & Chat
- [ ] Create Chatbot model
- [ ] Refactor chat logic
- [ ] Update chat endpoints
- [ ] Test chatbot functionality

### Week 4: API & Polish
- [ ] Create RESTful API endpoints
- [ ] Add permissions
- [ ] API documentation
- [ ] Testing

---

## 💡 Recommendations

### 1. Branch Strategy
```
main (production-ready SAAS)
  └── develop (SAAS development)
      └── feature/modern-chat-ui (current prototype)
```

**Action**: 
- Keep prototype code in `feature/modern-chat-ui` branch
- Create new `develop` branch for SAAS MVP
- Merge reusable services từ prototype

### 2. Incremental Migration
- Don't delete prototype code ngay
- Build SAAS MVP alongside
- Gradually migrate features
- Test thoroughly before removing prototype

### 3. Code Reuse Priority
1. **Services layer** - Highest priority (business logic)
2. **Utilities** - Medium priority (helpers)
3. **Views** - Low priority (need rewrite for API)
4. **Models** - Need rewrite (multi-tenant)

---

## ✅ Summary

**Prototype code = Foundation, không phải waste:**
- ✅ Core services có thể reuse
- ✅ Technical decisions đã validate
- ✅ Architecture patterns đã test
- ✅ RAG logic đã proven

**SAAS MVP = Production-ready version:**
- ✅ Multi-tenant architecture
- ✅ Enterprise security
- ✅ Scalable design
- ✅ Full API

**Next step**: Bắt đầu implement SAAS MVP với foundation từ prototype!

