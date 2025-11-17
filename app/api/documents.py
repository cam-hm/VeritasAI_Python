"""
Documents API Routes
Tương đương với app/Http/Controllers/DocumentController.php trong Laravel
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.document import Document

# Tạo router (tương đương với Route::group() trong Laravel)
router = APIRouter()


@router.get("/")
async def index(db: Session = Depends(get_db)):
    """
    List all documents
    Tương đương với DocumentController::index() trong Laravel
    """
    documents = db.query(Document).all()
    return {
        "documents": [
            {
                "id": doc.id,
                "name": doc.name,
                "status": doc.status,
                "num_chunks": doc.num_chunks,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}")
async def show(document_id: int, db: Session = Depends(get_db)):
    """
    Show single document
    Tương đương với DocumentController::show() trong Laravel
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "name": document.name,
        "status": document.status,
        "num_chunks": document.num_chunks,
        "file_size": document.get_formatted_file_size(),
        "processed_at": document.processed_at.isoformat() if document.processed_at else None,
        "error_message": document.error_message,
    }


@router.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload document
    Tương đương với DocumentController::store() trong Laravel
    
    TODO: Implement file upload và trigger background job
    """
    # TODO: Implement file upload logic
    return {"message": "Upload endpoint - to be implemented"}

