# 🧪 Testing Guide - Phase 1

## ✅ Đã implement

1. ✅ File upload endpoint (`POST /api/documents/upload/`)
2. ✅ Celery task xử lý document (Django ORM)
3. ✅ Token estimation service
4. ✅ Vector search với pgvector
5. ✅ Chat với RAG (vector search + LLM streaming)

## 🚀 Test Flow

### Bước 1: Start Services

```bash
# Terminal 1: Django server
source venv/bin/activate
python manage.py runserver

# Terminal 2: Celery worker
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Redis (nếu chưa chạy)
redis-server
```

### Bước 2: Upload File

```bash
# Test upload với curl
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@/path/to/your/document.pdf"

# Hoặc với Python requests
python -c "
import requests
files = {'file': open('test.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/documents/upload/', files=files)
print(response.json())
"
```

**Expected Response:**
```json
{
  "message": "File uploaded successfully",
  "document": {
    "id": 1,
    "name": "test.pdf",
    "status": "pending",
    ...
  }
}
```

### Bước 3: Check Processing Status

```bash
# Check document status
curl http://localhost:8000/api/documents/1/

# Hoặc check trong admin panel
# http://localhost:8000/admin/app/document/
```

**Wait for status = "completed"** (check Celery worker logs)

### Bước 4: Chat với Document

```bash
# Test chat với curl (Server-Sent Events)
curl -X POST http://localhost:8000/api/chat/stream/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "messages": [
      {"role": "user", "content": "What is this document about?"}
    ]
  }'
```

**Expected Response (Streaming):**
```
data: {"content": "Based"}
data: {"content": " on"}
data: {"content": " the"}
...
```

### Bước 5: Test với Python Script

```python
# test_rag.py
import requests
import json

# 1. Upload file
with open('test.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/documents/upload/',
        files={'file': f}
    )
    doc = response.json()['document']
    doc_id = doc['id']
    print(f"Uploaded document ID: {doc_id}")

# 2. Wait for processing (poll status)
import time
while True:
    response = requests.get(f'http://localhost:8000/api/documents/{doc_id}/')
    status = response.json()['status']
    print(f"Status: {status}")
    if status == 'completed':
        break
    elif status == 'failed':
        print("Processing failed!")
        break
    time.sleep(2)

# 3. Chat với document
response = requests.post(
    'http://localhost:8000/api/chat/stream/',
    json={
        'document_id': doc_id,
        'messages': [
            {'role': 'user', 'content': 'What is this document about?'}
        ]
    },
    stream=True
)

print("\nChat Response:")
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        if 'content' in data:
            print(data['content'], end='', flush=True)
        elif 'error' in data:
            print(f"\nError: {data['error']}")
            break
print("\n")
```

## 🔍 Check Logs

### Django Server Logs
```bash
# Xem logs trong terminal running Django server
```

### Celery Worker Logs
```bash
# Xem logs trong terminal running Celery worker
# Sẽ thấy:
# - "Extracting text from document X"
# - "Chunking text for document X"
# - "Starting batch embedding generation"
# - "Document processing completed"
```

### Database Check
```bash
# Check documents
psql -d veritasai_python -c "SELECT id, name, status, num_chunks FROM documents;"

# Check chunks
psql -d veritasai_python -c "SELECT COUNT(*) FROM document_chunks WHERE document_id = 1;"

# Check chat messages
psql -d veritasai_python -c "SELECT role, content FROM chat_messages WHERE document_id = 1;"
```

## ⚠️ Troubleshooting

### 1. Celery không chạy
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check Celery worker
celery -A app.celery_app inspect active
```

### 2. Ollama không chạy
```bash
# Check Ollama
curl http://127.0.0.1:11434/api/tags

# Pull models nếu chưa có
ollama pull nomic-embed-text
ollama pull llama3.2
```

### 3. Vector search không hoạt động
```bash
# Check pgvector extension
psql -d veritasai_python -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check embeddings
psql -d veritasai_python -c "SELECT id, array_length(embedding::float[], 1) as dims FROM document_chunks LIMIT 1;"
```

### 4. File upload lỗi
- Check storage directory permissions
- Check file size (< 10MB)
- Check file type (PDF, DOCX, TXT, MD only)

## 📝 Test Checklist

- [ ] Upload PDF file
- [ ] Upload DOCX file
- [ ] Upload TXT file
- [ ] Check document processing (status: pending → processing → completed)
- [ ] Check chunks created in database
- [ ] Chat với document (vector search hoạt động)
- [ ] Check chat messages saved
- [ ] Test với multiple documents
- [ ] Test error handling (invalid file, missing document, etc.)

## 🎯 Success Criteria

Phase 1 hoàn thành khi:
1. ✅ Upload file thành công
2. ✅ Document được process (extract → chunk → embed)
3. ✅ Chat với document trả về response dựa trên content
4. ✅ Vector search tìm được relevant chunks
5. ✅ Streaming response hoạt động

Sau đó có thể commit và push lên GitHub! 🚀

