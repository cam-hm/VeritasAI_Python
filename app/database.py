"""
Database Connection
Tương đương với Laravel database.php và Eloquent connection
Sử dụng SQLAlchemy (ORM) - tương đương Eloquent
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Tạo database engine (tương đương DB connection trong Laravel)
engine = create_engine(
    settings.database_url,
    # Async support sẽ được thêm sau với asyncpg
    echo=settings.debug  # Log SQL queries khi debug
)

# Session factory (tương đương DB::table() hoặc Model::query())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho models (tương đương Model class trong Laravel)
Base = declarative_base()


# Dependency để inject database session vào FastAPI routes
# Tương đương với dependency injection trong Laravel
def get_db():
    """
    Dependency function để lấy database session
    Tương đương với DB::transaction() hoặc Model::query() trong Laravel
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

