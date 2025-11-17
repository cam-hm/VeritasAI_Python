"""
Document Model
Tương đương với app/Models/Document.php trong Laravel
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """
    Document model - tương đương Laravel Document model
    
    Trong Laravel:
    - protected $fillable = ['name', 'path', 'user_id', 'status', ...]
    - public function chunks(): HasMany
    """
    __tablename__ = "documents"
    
    # Columns (tương đương $fillable trong Laravel)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)  # File path trong storage
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    num_chunks = Column(Integer, default=0)
    embedding_model = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Timestamps (tương đương $timestamps trong Laravel)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (tương đương hasMany() trong Laravel)
    # chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    # chat_messages = relationship("ChatMessage", back_populates="document")
    # user = relationship("User", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def get_formatted_file_size(self) -> str:
        """
        Get formatted file size (e.g., "2.5 MB")
        Tương đương với getFormattedFileSizeAttribute() trong Laravel
        """
        if not self.file_size:
            return "Unknown"
        
        bytes = self.file_size
        units = ["B", "KB", "MB", "GB"]
        
        for i in range(len(units) - 1):
            if bytes < 1024:
                break
            bytes /= 1024
        
        return f"{round(bytes, 2)} {units[i]}"

