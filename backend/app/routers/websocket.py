"""
WebSocket endpoint for real-time chat with the AI agent.

Handles:
- WebSocket connection lifecycle
- Message streaming from agent to frontend
- Conversation state management per session
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import json
import asyncio

from app.agent import run_agent_sync
from app.agent.tools import CRUD_TOOLS
from app.database import SyncSessionLocal
from app.models.todo import Todo

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and conversation state.
    Each connection maintains its own conversation history.
    """
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.conversation_histories: dict[str, list] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept connection and initialize conversation state."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.conversation_histories[client_id] = []
    
    def disconnect(self, client_id: str):
        """Clean up connection and state on disconnect."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.conversation_histories:
            del self.conversation_histories[client_id]
    
    def get_history(self, client_id: str) -> list:
        """Get conversation history for a client."""
        return self.conversation_histories.get(client_id, [])
    
    def add_to_history(self, client_id: str, message):
        """Add a message to conversation history."""
        if client_id in self.conversation_histories:
            self.conversation_histories[client_id].append(message)
            # Keep only last 20 messages to prevent context overflow
            if len(self.conversation_histories[client_id]) > 20:
                self.conversation_histories[client_id] = self.conversation_histories[client_id][-20:]
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send JSON message to client."""
        await websocket.send_json(message)


manager = ConnectionManager()


def get_all_todos() -> list:
    """Fetch all todos from database for UI refresh."""
    session = SyncSessionLocal()
    try:
        todos = session.query(Todo).order_by(Todo.created_at.desc()).all()
        return [todo.to_dict() for todo in todos]
    finally:
        session.close()


def extract_response_content(state: dict) -> tuple[str, bool]:
    """
    Extract the final response content from agent state.
    
    Returns:
        Tuple of (response_text, was_tool_used)
    """
    messages = state.get("messages", [])
    tool_was_used = False
    response_content = ""
    
    # Look through messages to build response
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_was_used = True
        elif isinstance(msg, AIMessage):
            # If AI message has content (not just tool calls), use it
            if msg.content and isinstance(msg.content, str) and msg.content.strip():
                response_content = msg.content
    
    # If tool was used but no final AI response, construct one from tool results
    if tool_was_used and not response_content:
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                try:
                    result = json.loads(msg.content)
                    if result.get("success"):
                        response_content = result.get("message", "Operation completed successfully.")
                        
                        # Add details for read operations
                        if result.get("action") == "read":
                            todos = result.get("todos", [])
                            if todos:
                                response_content += "\n\nHere are your todos:\n"
                                for todo in todos:
                                    response_content += f"• [{todo['id']}] {todo['title']}"
                                    if todo.get('description'):
                                        response_content += f" - {todo['description']}"
                                    response_content += "\n"
                            else:
                                response_content = "Your todo list is empty. Would you like to add a task?"
                        
                        # Add details for semantic search
                        elif result.get("action") == "semantic_search":
                            results = result.get("results", [])
                            if results:
                                response_content += "\n\nRelevant todos:\n"
                                for todo in results:
                                    response_content += f"• [{todo['id']}] {todo['title']}"
                                    if todo.get('description'):
                                        response_content += f" - {todo['description']}"
                                    response_content += f" (relevance: {todo.get('relevance_score', 0):.2f})\n"
                    else:
                        response_content = result.get("message", "Operation failed.")
                except (json.JSONDecodeError, KeyError):
                    response_content = msg.content
                break
    
    # Fallback
    if not response_content:
        response_content = "I processed your request but couldn't generate a response. Please try again."
    
    return response_content, tool_was_used


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with the AI agent.
    
    Message Protocol:
    - Client sends: {"message": "user's message"}
    - Server sends: {"type": "token|complete|error|todos_update", "content": "...", "todos": [...]}
    
    Streaming:
    - Tokens are sent as they're generated
    - Final "complete" message includes updated todo list
    """
    # Generate unique client ID
    client_id = str(id(websocket))
    
    await manager.connect(websocket, client_id)
    
    # Send initial todos
    try:
        initial_todos = get_all_todos()
        await manager.send_message(websocket, {
            "type": "todos_update",
            "content": "Connected to Todo Agent",
            "todos": initial_todos
        })
    except Exception as e:
        await manager.send_message(websocket, {
            "type": "error",
            "content": f"Failed to load todos: {str(e)}"
        })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            
            if not user_message:
                await manager.send_message(websocket, {
                    "type": "error",
                    "content": "Please enter a message"
                })
                continue
            
            # Add user message to history
            manager.add_to_history(client_id, HumanMessage(content=user_message))
            
            # Send acknowledgment
            await manager.send_message(websocket, {
                "type": "thinking",
                "content": "Processing your request..."
            })
            
            try:
                # Get conversation history
                history = manager.get_history(client_id)
                
                # Run the agent
                final_state = await run_agent_sync(user_message, history[:-1])  # Exclude the message we just added
                
                # Extract response
                response_content, tool_was_used = extract_response_content(final_state)
                
                # Add AI response to history
                manager.add_to_history(client_id, AIMessage(content=response_content))
                
                # Stream the response token by token for effect
                # (In production with true streaming, you'd yield actual tokens)
                tokens = response_content.split()
                for i, token in enumerate(tokens):
                    await manager.send_message(websocket, {
                        "type": "token",
                        "content": token + (" " if i < len(tokens) - 1 else "")
                    })
                    await asyncio.sleep(0.02)  # Small delay for streaming effect
                
                # Get updated todos if a tool was used
                updated_todos = get_all_todos() if tool_was_used else None
                
                # Send completion message
                await manager.send_message(websocket, {
                    "type": "complete",
                    "content": response_content,
                    "todos": updated_todos
                })
                
            except Exception as e:
                error_msg = f"Agent error: {str(e)}"
                await manager.send_message(websocket, {
                    "type": "error",
                    "content": error_msg
                })
                # Add error to history for context
                manager.add_to_history(client_id, AIMessage(content=f"Error occurred: {error_msg}"))
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
        # Connection already closed, can't send error message
