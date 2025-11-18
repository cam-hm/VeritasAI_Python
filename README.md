# VeritasAI Python - RAG System

A Retrieval-Augmented Generation (RAG) system built with Django and Python, demonstrating how Python compares to PHP/Laravel for AI applications.

## 🎯 What is RAG?

**RAG** (Retrieval-Augmented Generation) combines:
- **Retrieval**: Smart search to find relevant information from your documents
- **Generation**: LLM to generate natural answers based on retrieved context

**Why RAG?**
- ✅ AI answers based on **your private documents** (not just training data)
- ✅ Reduces hallucination (AI making things up)
- ✅ Update knowledge without retraining models
- ✅ Cite sources (know where information comes from)

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG SYSTEM ARCHITECTURE                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   USER INTERFACE     │         │   ADMIN INTERFACE    │
│  (Chat, Documents)   │         │ (Upload, Manage)     │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                │
           │                                │
┌──────────▼────────────────────────────────▼───────────────┐
│                    WEB APPLICATION                         │
│                  (Django - Views/URLs)                     │
└──────┬────────────────────────────────────────┬───────────┘
       │                                        │
       │ ┌──────── TWO MAIN FLOWS ─────────┐  │
       │ │                                  │  │
       │ │  1️⃣  INDEXING (Document Upload) │  │
       │ │  2️⃣  QUERYING (Chat with AI)    │  │
       │ └──────────────────────────────────┘  │
       │                                        │
┌──────▼────────────────┐           ┌──────────▼─────────────┐
│  BACKGROUND JOBS      │           │   SERVICES LAYER       │
│  (Celery/Subprocess)  │           │  (Business Logic)      │
└───────────────────────┘           └────────────────────────┘
       │                                        │
┌──────▼────────────────────────────────────────▼───────────┐
│                    DATA STORAGE                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PostgreSQL  │  │   pgvector   │  │  File System │     │
│  │ (Metadata)  │  │  (Vectors)   │  │  (Documents) │     │
│  └─────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
       │                                        │
┌──────▼────────────────────────────────────────▼───────────┐
│                    EXTERNAL SERVICES                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Ollama    │  │    Redis     │  │    Celery    │     │
│  │(Embeddings, │  │   (Cache)    │  │   Workers    │     │
│  │    LLM)     │  │              │  │  (Optional)  │     │
│  └─────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

## 📤 Flow 1: INDEXING (Document Upload & Processing)

**Purpose**: Convert documents into searchable vectors

```
USER
  │
  │ Upload PDF/DOCX/TXT
  ▼
┌─────────────────────────────────────────────────────────┐
│ 1. UPLOAD ENDPOINT                                      │
│    - Validate file type and size                        │
│    - Check duplicates (SHA-256 hash)                    │
│    - Save to file system                                │
│    - Create Document record (status: pending)          │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Trigger background job
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. BACKGROUND PROCESSING                                │
│    - Celery worker (if available)                       │
│    - OR subprocess: python manage.py process_document   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. TEXT EXTRACTION (TextExtractionService)             │
│    - PDF → PyPDF2.PdfReader                            │
│    - DOCX → python-docx                                 │
│    - TXT/MD → Plain text                                │
│    → Output: Raw text string                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. TEXT CHUNKING (RecursiveChunkingService)            │
│    - Split by semantic units: \n\n → \n → . → space   │
│    - Chunk size: ~300 words (1500 chars)               │
│    - Overlap: 200 chars (13%) for context preservation │
│    → Output: ["chunk1", "chunk2", ...]                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. EMBEDDING GENERATION (EmbeddingService)             │
│    - Batch process chunks (10 at a time)               │
│    - Call Ollama API: POST /api/embeddings             │
│    - Model: nomic-embed-text                            │
│    - Each chunk → 768-dimensional vector                │
│    → Output: [[0.123, -0.456, ...], [...]]            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. VECTOR STORAGE (PostgreSQL + pgvector)              │
│    - Store in DocumentChunk table:                      │
│      • content (text)                                   │
│      • embedding (vector(768))                          │
│      • token_count (int, pre-computed)                  │
│    - Create vector index for fast similarity search    │
│    - Update Document.status = 'completed'              │
└─────────────────────────────────────────────────────────┘
```

**Result**: Document is now indexed and ready for semantic search!

## 💬 Flow 2: QUERYING (Chat with AI)

**Purpose**: Answer questions based on indexed documents

```
USER
  │
  │ "What does the document say about Python?"
  ▼
┌─────────────────────────────────────────────────────────┐
│ 1. CHAT ENDPOINT                                        │
│    - Receive user question                              │
│    - Get document_id                                    │
│    - Load chat history (last 10 messages)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. QUERY EMBEDDING (EmbeddingService + Redis Cache)    │
│    - Check Redis cache first (key: hash(question))     │
│    - If miss: Generate embedding via Ollama            │
│    - Cache result for 1 hour                            │
│    → Output: [0.234, -0.567, ...] (768-dim vector)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. VECTOR SIMILARITY SEARCH (pgvector)                 │
│    - SQL: SELECT * FROM chunks                          │
│           WHERE document_id = ?                         │
│           ORDER BY embedding <=> query_vector           │
│           LIMIT 10                                      │
│    - Operator <=> : Cosine distance                     │
│    → Returns top 10 most similar chunks                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. CONTEXT BUILDING (RagPromptService)                 │
│    - Filter chunks by similarity threshold              │
│    - Sort by relevance score                            │
│    - Build context within token limit (~4000 tokens)   │
│    - Format prompt with context + question              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. LLM GENERATION (OllamaClient)                       │
│    - Call Ollama: POST /api/chat (streaming)           │
│    - Model: llama3.1                                    │
│    - Stream response token by token                     │
│    → Output: "The document mentions Python..."         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. STREAMING RESPONSE                                   │
│    - Stream to frontend via Server-Sent Events (SSE)   │
│    - Save messages to DB (async, background thread)    │
│    - Display to user in real-time                       │
└─────────────────────────────────────────────────────────┘
```

## 🔄 RAG vs Traditional Search

### Traditional Search (Keyword-based):
```
Query: "Python programming"
Search: WHERE content LIKE '%Python%' AND '%programming%'
❌ Problem: Only matches exact words, no semantic understanding
```

### RAG (Semantic Search):
```
Query: "Ngôn ngữ lập trình Python" (Vietnamese)
Embedding: [0.23, -0.45, ...]
Search: Vector similarity (cosine distance)
✅ Result: Finds chunks about Python even without exact words!
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.2.8
- **Language**: Python 3.13
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis 7+
- **Task Queue**: Celery 5.4 (optional, auto-fallback to subprocess)

### AI/ML
- **LLM**: Ollama (llama3.1 for chat)
- **Embeddings**: nomic-embed-text (768 dimensions)
- **Vector Search**: pgvector with cosine distance

### Frontend
- **Templates**: Django Templates
- **JavaScript**: Alpine.js 3.x
- **CSS**: Tailwind CSS 3.x
- **Icons**: Heroicons

### Services
- **Text Extraction**: PyPDF2, python-docx
- **Chunking**: Custom recursive splitter
- **Embeddings**: Batch processing with retry logic

## 📊 Key Features

### Performance Optimizations
1. **Database Connection Pooling** - Reuse connections (CONN_MAX_AGE)
2. **Redis Caching** - Cache query embeddings for 1 hour
3. **Pre-computed Token Counts** - Stored in DB, no recalculation
4. **N+1 Query Fix** - Batch fetch with proper ORM usage
5. **Async Message Saving** - Background threads for non-blocking writes
6. **Batch Embeddings** - Process 10 chunks at once

### Chunking Strategy
- **Chunk Size**: ~300 words (1500 characters)
- **Overlap**: 200 characters (13%)
- **Splitters**: Semantic units (paragraphs → sentences → words)
- **Optimal for**: 1K - 100K word documents

### Error Handling
- Auto-fallback from Celery to subprocess if workers unavailable
- Retry logic for embedding API calls (3 attempts)
- Clear error messages for different failure scenarios
- Graceful handling of scanned PDFs (image-based, needs OCR)

## 🔧 Quick Start

### Prerequisites
```bash
# System requirements
Python 3.13+
PostgreSQL 16+ with pgvector
Redis 7+
Ollama (local LLM server)
```

### Installation
```bash
# Clone repository
git clone https://github.com/cam-hm/VeritasAI_Python.git
cd VeritasAI_Python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start services (see SETUP_SERVICES.md for details)
# 1. PostgreSQL with pgvector
# 2. Redis server
# 3. Ollama with models
ollama pull llama3.1
ollama pull nomic-embed-text

# Start Django server
python manage.py runserver

# (Optional) Start Celery worker
celery -A app.celery_app worker -l info
```

### Usage
1. Open http://127.0.0.1:8000
2. Upload a document (PDF, DOCX, TXT, MD)
3. Wait for processing to complete
4. Navigate to document detail page
5. Chat with AI about your document!

## 📁 Project Structure

```
VeritasAI_Python/
├── app/
│   ├── management/
│   │   └── commands/
│   │       └── process_document.py    # Django management command
│   ├── models.py                      # Django ORM models
│   ├── views.py                       # HTTP endpoints
│   ├── urls.py                        # URL routing
│   ├── services/
│   │   ├── text_extraction_service.py
│   │   ├── chunking_service.py
│   │   ├── embedding_service.py
│   │   ├── rag_prompt_service.py
│   │   ├── token_estimation_service.py
│   │   └── ollama_client.py           # Ollama API wrapper
│   ├── tasks/
│   │   └── document_tasks.py          # Celery tasks
│   └── templates/                     # Django templates
├── veritasai_django/
│   ├── settings.py                    # Django settings
│   └── urls.py                        # Root URL config
├── storage/
│   ├── documents/                     # Uploaded files
│   └── logs/                          # Processing logs
├── requirements.txt                   # Python dependencies
├── manage.py                          # Django management script
├── README.md                          # This file
├── TESTING.md                         # Testing guide
└── SETUP_SERVICES.md                  # Services setup guide
```

## 🔄 Django vs Laravel Comparison

| Component | Django (Python) | Laravel (PHP) |
|-----------|----------------|---------------|
| **Web Framework** | Django Views | Controllers |
| **ORM** | Django Models | Eloquent |
| **Background Jobs** | Celery + Redis | Laravel Queue |
| **Routing** | urls.py | routes/web.php |
| **Templates** | Django Templates | Blade |
| **Migrations** | Django Migrations | Laravel Migrations |
| **Admin Panel** | Django Admin | Laravel Nova |
| **Cache** | Redis/LocMem | Laravel Cache |
| **CLI** | manage.py | php artisan |
| **Package Manager** | pip | composer |

### Architectural Patterns
- **Django**: MTV (Model-Template-View) - variation of MVC
- **Laravel**: MVC (Model-View-Controller)

**Key Similarity**: Both provide full-stack web frameworks with built-in ORM, routing, templating, and admin interfaces.

## 🚀 Performance Metrics

### Document Processing
- **Small document** (1K words): ~5-10 seconds
- **Medium document** (10K words): ~30-60 seconds
- **Large document** (100K words): ~5-10 minutes

### Chat Response
- **Time to First Token (TTFT)**: ~500ms - 1s
- **Streaming Speed**: ~20-50 tokens/second (depends on Ollama model)

### Optimizations Impact
- **Redis cache hit**: 200ms saved per query
- **Pre-computed tokens**: 50ms saved per chunk
- **N+1 fix**: 80% reduction in DB queries
- **Connection pooling**: 30% reduction in query latency

## 🧪 Testing

See [TESTING.md](TESTING.md) for detailed testing instructions.

```bash
# Run all tests
python manage.py test

# Test specific app
python manage.py test app

# Monitor upload status
./monitor_upload.sh

# Debug upload process
./debug_upload.sh
```

## 📚 Documentation

- **[SETUP_SERVICES.md](SETUP_SERVICES.md)**: How to setup PostgreSQL, Redis, Ollama
- **[TESTING.md](TESTING.md)**: Testing guide and troubleshooting
- **[Django Documentation](https://docs.djangoproject.com/)**: Official Django docs
- **[pgvector](https://github.com/pgvector/pgvector)**: Vector similarity search
- **[Ollama](https://ollama.ai/)**: Local LLM server

## 🤝 Contributing

This project is a learning exercise comparing Python/Django with PHP/Laravel for AI applications.

Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

**Hoàng Mạnh Cầm**
- GitHub: [@cam-hm](https://github.com/cam-hm)
- Project: Learning Python for AI applications

## 🙏 Acknowledgments

- Django team for the excellent web framework
- Ollama team for local LLM capabilities
- pgvector team for vector similarity search in PostgreSQL
- LangChain community for RAG patterns and best practices

---

**Note**: This is a learning project to compare Python's advantages over PHP for AI applications. The codebase includes detailed comments explaining Django concepts in relation to Laravel equivalents.
