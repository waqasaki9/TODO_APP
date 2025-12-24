"""
FastAPI Main Application Entry Point.

This is the main FastAPI application that:
1. Sets up CORS for frontend communication
2. Registers WebSocket and REST API routers
3. Initializes database on startup
4. Provides health check endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import websocket_router, todos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database tables
    print("🚀 Starting Todo Agent API...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown: Cleanup if needed
    print("👋 Shutting down Todo Agent API...")


# Create FastAPI application
app = FastAPI(
    title="AI Todo Manager API",
    description="""
    An AI-powered Todo Manager that uses natural language processing.
    
    ## Features
    - Natural language task management
    - Real-time WebSocket communication
    - Semantic search with RAG
    - CRUD operations via REST or AI agent
    
    ## WebSocket Endpoint
    Connect to `/ws/chat` for real-time AI interactions.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://todo-app-1-rngz.onrender.com",  # Render frontend
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # CRA default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(websocket_router)
app.include_router(todos_router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API info."""
    return {
        "name": "AI Todo Manager API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/chat"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
