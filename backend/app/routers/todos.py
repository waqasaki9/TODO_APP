"""
REST API endpoints for todos.
Provides direct CRUD operations for the frontend Todo list UI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_async_session
from app.models.todo import Todo
from app.schemas import TodoCreate, TodoUpdate, TodoResponse

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=List[TodoResponse])
async def get_all_todos(session: AsyncSession = Depends(get_async_session)):
    """Get all todos."""
    result = await session.execute(
        select(Todo).order_by(Todo.created_at.desc())
    )
    todos = result.scalars().all()
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, session: AsyncSession = Depends(get_async_session)):
    """Get a specific todo by ID."""
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo


@router.post("/", response_model=TodoResponse)
async def create_todo(
    todo_data: TodoCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new todo."""
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update an existing todo."""
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    if todo_data.title is not None:
        todo.title = todo_data.title
    if todo_data.description is not None:
        todo.description = todo_data.description
    
    await session.commit()
    await session.refresh(todo)
    return todo


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a todo."""
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    await session.delete(todo)
    await session.commit()
    
    return {"message": "Todo deleted successfully", "id": todo_id}
