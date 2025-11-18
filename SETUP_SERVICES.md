# 🚀 Setup Services để Test

## Vấn đề hiện tại

Document không được process vì:
- ❌ Redis không chạy
- ❌ Celery worker không chạy

## Giải pháp

### Option 1: Start Redis và Celery (Recommended)

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Django server (đã chạy)
python manage.py runserver
```

### Option 2: Test không cần Celery (Quick test)

```bash
# Process document synchronously (không cần Celery)
source venv/bin/activate
python test_without_celery.py <document_id>

# Ví dụ:
python test_without_celery.py 2
```

## Kiểm tra Services

### Check Redis
```bash
redis-cli ping
# Should return: PONG
```

### Check Celery
```bash
celery -A app.celery_app inspect active
# Should show active tasks
```

### Check Document Status
```bash
python manage.py shell -c "
from app.models import Document
for doc in Document.objects.all()[:5]:
    print(f'ID: {doc.id}, Name: {doc.name}, Status: {doc.status}, Chunks: {doc.num_chunks}')
"
```

## Test Flow với Services

1. **Start services:**
   ```bash
   # Terminal 1
   redis-server
   
   # Terminal 2
   celery -A app.celery_app worker --loglevel=info
   
   # Terminal 3 (đã chạy)
   python manage.py runserver
   ```

2. **Upload file:**
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload/ \
     -F "file=@test.pdf"
   ```

3. **Check processing:**
   - Xem Celery worker logs
   - Check document status: `curl http://localhost:8000/api/documents/1/`

4. **Chat:**
   ```bash
   curl -X POST http://localhost:8000/api/chat/stream/ \
     -H "Content-Type: application/json" \
     -d '{"document_id": 1, "messages": [{"role": "user", "content": "What is this about?"}]}'
   ```

## Troubleshooting

### Redis không chạy
```bash
# Install Redis (macOS)
brew install redis

# Start Redis
brew services start redis
# hoặc
redis-server
```

### Celery không connect được Redis
```bash
# Check Redis URL trong settings
python manage.py shell -c "
from django.conf import settings
print('CELERY_BROKER_URL:', getattr(settings, 'CELERY_BROKER_URL', 'Not set'))
"
```

### Document stuck ở "pending"
- Check Celery worker logs
- Check Redis connection
- Hoặc dùng `test_without_celery.py` để process manually

