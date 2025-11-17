"""
Models Package - Re-export từ app/models.py
Django models được định nghĩa trong app/models.py (Django ORM)
Thư mục này là từ SQLAlchemy cũ, nhưng cần re-export để import hoạt động
"""
# Re-export Django models từ models.py
import sys
import os

# Import từ parent directory (app/models.py)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import Django models
from app.models import Document, DocumentChunk, ChatMessage

__all__ = ["Document", "DocumentChunk", "ChatMessage"]

