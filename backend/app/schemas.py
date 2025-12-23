"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")


class TodoUpdate(BaseModel):
    """Schema for updating an existing todo."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title")
    description: Optional[str] = Field(None, description="New description")


class TodoResponse(BaseModel):
    """Schema for todo response."""
    id: int
    title: str
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for chat messages."""
    message: str = Field(..., min_length=1, description="User message")


class AgentResponse(BaseModel):
    """Schema for agent responses."""
    type: str = Field(..., description="Response type: 'token', 'complete', 'error', 'tool_result'")
    content: str = Field(..., description="Response content")
    todos: Optional[list] = Field(None, description="Updated todo list if applicable")
