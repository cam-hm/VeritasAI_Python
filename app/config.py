"""
Configuration Management
Tương đương với Laravel config/ files và .env
Sử dụng pydantic-settings để quản lý settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings - tương đương Laravel config files"""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/veritasai_python"
    
    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_batch_size: int = 10
    ollama_embed_concurrency: int = 5
    ollama_max_retries: int = 3
    ollama_retry_delay: float = 1.0
    
    # OpenAI (Optional)
    openai_api_key: Optional[str] = None
    openai_embed_model: str = "text-embedding-3-small"
    
    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # File Storage
    storage_path: str = "./storage"
    max_file_size: int = 10485760  # 10MB
    
    # App
    debug: bool = True
    app_name: str = "VeritasAI Python"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Tạo instance settings (tương đương Config::get() trong Laravel)
settings = Settings()

