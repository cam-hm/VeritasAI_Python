"""
FastAPI Main Application
Tương đương với routes/web.php và app/Http/Kernel.php trong Laravel

FastAPI là web framework tương đương Laravel
- Routes được define bằng decorators (@app.get, @app.post)
- Dependency injection tự động
- Automatic API documentation (Swagger/OpenAPI)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request
from jinja2 import Template
from app.config import settings
import os

# Tạo FastAPI app (tương đương với Route:: trong Laravel)
app = FastAPI(
    title=settings.app_name,
    description="RAG System built with Python/FastAPI",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware (tương đương với Laravel CORS config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, nên specify origins cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files (tương đương với Laravel public/ folder)
# Serve static files từ app/static/ directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import và include routers (tương đương với Route::group() trong Laravel)
from app.api import documents, chat
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


# Health check endpoint (API)
@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "ok"}


# Serve HTML pages (tương đương với Route::view() trong Laravel)
@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Home page - serve static HTML với Alpine.js
    Tương đương với Route::view('/', 'welcome') trong Laravel
    """
    html_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Welcome to VeritasAI Python</h1>")


@app.get("/documents", response_class=HTMLResponse)
async def documents_page():
    """
    Documents page - serve static HTML
    Tương đương với Route::view('/documents', 'documents') trong Laravel
    """
    html_file = os.path.join(os.path.dirname(__file__), "static", "documents.html")
    if os.path.exists(html_file):
        with open(html_file, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Documents</h1>")


if __name__ == "__main__":
    """
    Chạy server (tương đương với php artisan serve)
    Command: uvicorn app.main:app --reload
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)

