"""
RAG (Retrieval Augmented Generation) module for semantic todo queries.

This module provides vector-based semantic search over todos,
enabling analytical and reasoning queries that go beyond simple CRUD.

RAG is OPTIONAL and only used for:
- Semantic search (e.g., "tasks related to exams")
- Analytical queries (e.g., "what have I been postponing?")
- Summarization (e.g., "summarize my work tasks")

RAG is NOT used for CRUD operations.
"""
import os
from typing import List, Optional
import chromadb
from langchain_core.tools import tool
import json

from app.database import SyncSessionLocal
from app.models.todo import Todo
from app.config import get_settings

settings = get_settings()

# Initialize ChromaDB client with persistence (new API)
chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_directory
)

# Create or get the todos collection
COLLECTION_NAME = "todos_collection"


def get_or_create_collection():
    """Get or create the ChromaDB collection for todos."""
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception:
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Todo items for semantic search"}
        )
    return collection


def sync_todos_to_vectorstore():
    """
    Synchronize all todos from PostgreSQL to the vector store.
    Called periodically to keep vectors up to date.
    """
    session = SyncSessionLocal()
    try:
        todos = session.query(Todo).all()
        collection = get_or_create_collection()
        
        # Clear existing entries
        try:
            existing = collection.get()
            if existing and existing['ids']:
                collection.delete(ids=existing['ids'])
        except Exception:
            pass
        
        if not todos:
            return {"synced": 0, "message": "No todos to sync"}
        
        # Prepare documents for embedding
        documents = []
        metadatas = []
        ids = []
        
        for todo in todos:
            # Combine title and description for better semantic matching
            doc_text = f"{todo.title}"
            if todo.description:
                doc_text += f". {todo.description}"
            
            documents.append(doc_text)
            metadatas.append({
                "id": todo.id,
                "title": todo.title,
                "description": todo.description or "",
                "created_at": todo.created_at.isoformat() if todo.created_at else ""
            })
            ids.append(f"todo_{todo.id}")
        
        # Add to collection (ChromaDB auto-embeds using default model)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return {"synced": len(todos), "message": f"Synced {len(todos)} todos to vector store"}
    finally:
        session.close()


def semantic_search_todos(query: str, n_results: int = 5) -> List[dict]:
    """
    Perform semantic search over todos.
    
    Args:
        query: Natural language query
        n_results: Maximum number of results to return
        
    Returns:
        List of matching todos with relevance scores
    """
    # First sync todos to ensure vector store is up to date
    sync_todos_to_vectorstore()
    
    collection = get_or_create_collection()
    
    # Check if collection has any documents
    count = collection.count()
    if count == 0:
        return []
    
    # Perform semantic search
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, count)
    )
    
    # Format results
    formatted_results = []
    if results and results['metadatas'] and results['metadatas'][0]:
        for i, metadata in enumerate(results['metadatas'][0]):
            result = {
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "created_at": metadata.get("created_at"),
                "relevance_score": 1 - results['distances'][0][i] if results['distances'] else 0
            }
            formatted_results.append(result)
    
    return formatted_results


@tool
def search_todos_semantic(query: str) -> str:
    """
    Search todos using semantic/meaning-based matching.
    
    Use this tool ONLY for semantic queries, analytical questions, or when
    the user wants to find todos based on meaning rather than exact matches.
    
    Examples of when to use:
    - "What tasks have I been postponing?"
    - "Show todos related to exams"
    - "Summarize my work tasks"
    - "Find tasks about shopping"
    
    DO NOT use for simple CRUD operations like create, update, delete, or list all.
    
    Args:
        query: Natural language query describing what to search for
        
    Returns:
        JSON string with matching todos and their relevance scores
    """
    try:
        results = semantic_search_todos(query)
        
        if not results:
            return json.dumps({
                "success": True,
                "action": "semantic_search",
                "results": [],
                "count": 0,
                "message": "No matching todos found",
                "query": query
            })
        
        return json.dumps({
            "success": True,
            "action": "semantic_search",
            "results": results,
            "count": len(results),
            "message": f"Found {len(results)} relevant todo(s)",
            "query": query
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"Semantic search failed: {str(e)}"
        })


# Export RAG tools
RAG_TOOLS = [search_todos_semantic]
