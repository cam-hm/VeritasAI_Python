"""
ChatMessage Model
Tương đương với app/Models/ChatMessage.php trong Laravel
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ChatMessage(Base):
    """
    ChatMessage model - tương đương Laravel ChatMessage model
    
    Trong Laravel:
    - protected $fillable = ['document_id', 'user_id', 'role', 'content']
    - role: 'user' or 'ai'
    """
    __tablename__ = "chat_messages"
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'ai'
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # document = relationship("Document", back_populates="chat_messages")
    # user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{content_preview}')>"

