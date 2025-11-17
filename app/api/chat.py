"""
Chat API Routes
Tương đương với app/Http/Controllers/ChatController.php trong Laravel
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chat_message import ChatMessage
from app.models.document import Document

# Tạo router
router = APIRouter()


@router.get("/")
async def general(db: Session = Depends(get_db)):
    """
    General chat (không có document context)
    Tương đương với ChatController::general() trong Laravel
    """
    # TODO: Implement general chat
    return {"message": "General chat - to be implemented"}


@router.get("/{document_id}")
async def show(document_id: int, db: Session = Depends(get_db)):
    """
    Chat với document context
    Tương đương với ChatController::show() trong Laravel
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chat messages for this document
    messages = db.query(ChatMessage).filter(
        ChatMessage.document_id == document_id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "document": {
            "id": document.id,
            "name": document.name,
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


@router.post("/stream")
async def stream():
    """
    Stream chat response
    Tương đương với StreamController::stream() trong Laravel
    
    TODO: Implement streaming với Server-Sent Events (SSE)
    """
    # TODO: Implement streaming
    return {"message": "Stream endpoint - to be implemented"}

