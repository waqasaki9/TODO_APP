"""
Todo model for PostgreSQL database.
Defines the schema for storing todo items.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Todo(Base):
    """
    Todo model representing a task in the database.
    
    Attributes:
        id: Unique identifier for the todo
        title: Short title/name of the task
        description: Detailed description of the task
        created_at: Timestamp when todo was created
        updated_at: Timestamp when todo was last modified
    """
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Todo(id={self.id}, title='{self.title}')>"
