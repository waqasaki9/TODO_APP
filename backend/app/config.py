"""
Configuration module for the Todo Agent application.
Loads environment variables and provides settings across the app.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/todo_agent_db"
    
    # Groq LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Vector Store (ChromaDB for RAG)
    chroma_persist_directory: str = "./chroma_db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cache and return settings singleton."""
    return Settings()
