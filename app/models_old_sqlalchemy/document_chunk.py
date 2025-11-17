"""
DocumentChunk Model
Tương đương với app/Models/DocumentChunk.php trong Laravel
"""

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base


class DocumentChunk(Base):
    """
    DocumentChunk model - tương đương Laravel DocumentChunk model
    
    Trong Laravel:
    - protected $fillable = ['document_id', 'content', 'embedding']
    - protected $casts = ['embedding' => Vector::class]
    - use HasNeighbors; (cho vector search)
    """
    __tablename__ = "document_chunks"
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # Vector dimension (adjust based on embedding model)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, content='{content_preview}')>"

