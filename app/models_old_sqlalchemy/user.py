"""
User Model
Tương đương với app/Models/User.php trong Laravel
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model - tương đương Laravel User model
    """
    __tablename__ = "users"
    
    # Columns (tương đương $fillable trong Laravel)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (tương đương hasMany() trong Laravel)
    # documents = relationship("Document", back_populates="user")
    # chat_messages = relationship("ChatMessage", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

