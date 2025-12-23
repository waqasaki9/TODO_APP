"""
LangChain Tools for CRUD operations on Todos.

These tools are registered with the LangGraph agent and perform
direct database operations. Each tool returns structured results
that the agent uses to formulate responses.

IMPORTANT: These tools execute synchronously within the agent workflow.
"""
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import SyncSessionLocal
from app.models.todo import Todo


def get_db_session() -> Session:
    """Get a new database session for tool operations."""
    return SyncSessionLocal()


@tool
def create_todo(title: str, description: Optional[str] = None) -> str:
    """
    Create a new todo item in the database.
    
    Use this tool when the user wants to add a new task, create a todo,
    or add something to their list.
    
    Args:
        title: The title/name of the todo task (required)
        description: Optional detailed description of the task
        
    Returns:
        JSON string with the created todo details or error message
    """
    session = get_db_session()
    try:
        # Create new todo instance
        new_todo = Todo(
            title=title,
            description=description
        )
        session.add(new_todo)
        session.commit()
        session.refresh(new_todo)
        
        result = {
            "success": True,
            "action": "created",
            "todo": new_todo.to_dict(),
            "message": f"Successfully created todo: '{title}'"
        }
        return json.dumps(result)
    except Exception as e:
        session.rollback()
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Failed to create todo: {str(e)}"
        })
    finally:
        session.close()


@tool
def read_todos() -> str:
    """
    Read and return all todos from the database.
    
    Use this tool when the user wants to see their tasks, list todos,
    view all items, or check what's on their list.
    
    Returns:
        JSON string with list of all todos or error message
    """
    session = get_db_session()
    try:
        todos = session.query(Todo).order_by(Todo.created_at.desc()).all()
        todos_list = [todo.to_dict() for todo in todos]
        
        result = {
            "success": True,
            "action": "read",
            "todos": todos_list,
            "count": len(todos_list),
            "message": f"Found {len(todos_list)} todo(s)"
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Failed to read todos: {str(e)}"
        })
    finally:
        session.close()


@tool
def update_todo(
    todo_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update an existing todo item in the database.
    
    Use this tool when the user wants to modify, change, edit, or update
    an existing task. Requires the todo ID and at least one field to update.
    
    Args:
        todo_id: The ID of the todo to update (required)
        title: New title for the todo (optional)
        description: New description for the todo (optional)
        
    Returns:
        JSON string with the updated todo details or error message
    """
    session = get_db_session()
    try:
        todo = session.query(Todo).filter(Todo.id == todo_id).first()
        
        if not todo:
            return json.dumps({
                "success": False,
                "error": "Todo not found",
                "message": f"No todo found with ID {todo_id}"
            })
        
        # Update fields if provided
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
            
        session.commit()
        session.refresh(todo)
        
        result = {
            "success": True,
            "action": "updated",
            "todo": todo.to_dict(),
            "message": f"Successfully updated todo ID {todo_id}"
        }
        return json.dumps(result)
    except Exception as e:
        session.rollback()
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Failed to update todo: {str(e)}"
        })
    finally:
        session.close()


@tool
def delete_todo(todo_id: int) -> str:
    """
    Delete a todo item from the database.
    
    Use this tool when the user wants to remove, delete, or get rid of
    a task from their list.
    
    Args:
        todo_id: The ID of the todo to delete (required)
        
    Returns:
        JSON string confirming deletion or error message
    """
    session = get_db_session()
    try:
        todo = session.query(Todo).filter(Todo.id == todo_id).first()
        
        if not todo:
            return json.dumps({
                "success": False,
                "error": "Todo not found",
                "message": f"No todo found with ID {todo_id}"
            })
        
        todo_title = todo.title
        session.delete(todo)
        session.commit()
        
        result = {
            "success": True,
            "action": "deleted",
            "deleted_id": todo_id,
            "deleted_title": todo_title,
            "message": f"Successfully deleted todo: '{todo_title}' (ID: {todo_id})"
        }
        return json.dumps(result)
    except Exception as e:
        session.rollback()
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Failed to delete todo: {str(e)}"
        })
    finally:
        session.close()


# Export all tools as a list for easy registration with the agent
CRUD_TOOLS = [create_todo, read_todos, update_todo, delete_todo]
