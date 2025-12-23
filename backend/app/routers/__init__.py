"""Routers package initialization."""
from app.routers.websocket import router as websocket_router
from app.routers.todos import router as todos_router

__all__ = ["websocket_router", "todos_router"]
