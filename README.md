# VeritasAI Python - RAG System

Hệ thống RAG (Retrieval-Augmented Generation) được xây dựng với Django, tương đương với Laravel version.

## 🎯 Phase 1 - Hoàn thành!

✅ Upload file và process document  
✅ Chat với AI về thông tin trong file đó

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
createdb veritasai_python
psql -d veritasai_python -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 2. Start Services

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Redis (nếu chưa chạy)
redis-server
```

### 3. Test

```bash
# Upload file
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@test.pdf"

# Check status
curl http://localhost:8000/api/documents/1/

# Chat với document
curl -X POST http://localhost:8000/api/chat/stream/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "messages": [{"role": "user", "content": "What is this about?"}]
  }'
```

## 📚 Documentation

- `FEATURES.md` - Tổng quan tính năng
- `FEATURES_DETAILED.md` - Chi tiết với code examples
- `FLOW_DIAGRAM.md` - Flow diagram
- `TESTING.md` - Testing guide
- `PHASE1_COMPLETE.md` - Phase 1 summary

## 🔄 So sánh với Laravel

| Feature | Laravel | Django | Status |
|---------|---------|--------|--------|
| Framework | Laravel | Django | ✅ |
| ORM | Eloquent | Django ORM | ✅ |
| Migrations | `php artisan migrate` | `python manage.py migrate` | ✅ |
| Queue | Laravel Queue | Celery | ✅ |
| Admin | Laravel Nova (paid) | Django Admin (free) | ✅ |
| RAG | Custom | Custom | ✅ |

## 🛠️ Tech Stack

- **Framework**: Django 5.1
- **Database**: PostgreSQL + pgvector
- **Background Jobs**: Celery + Redis
- **Embeddings**: Ollama (nomic-embed-text)
- **LLM**: Ollama (llama3.2)
- **Vector Search**: pgvector

## 📝 API Endpoints

### Documents
- `GET /api/documents/` - List documents
- `GET /api/documents/{id}/` - Document detail
- `POST /api/documents/upload/` - Upload file

### Chat
- `GET /api/chat/{document_id}/` - Get chat messages
- `POST /api/chat/stream/` - Chat với RAG (streaming)

## 🎯 Next Steps

- [ ] Authentication & Authorization
- [ ] User management
- [ ] Multiple document chat
- [ ] Chat history UI
- [ ] File management UI

## 📄 License

MIT
