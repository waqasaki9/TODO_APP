"""
LangGraph Agent for Todo Management.

This is the core orchestration module that implements the AI agent using LangGraph.
The agent follows a specific workflow:

1. FIRST LLM CALL: Reason about user query, decide on action
2. IF CRUD intent detected → Execute CRUD tool → Return result (1 LLM call total)
3. IF RAG/semantic intent detected → Retrieve context → SECOND LLM call → Return (2 LLM calls total)
4. IF general question → Respond directly (1 LLM call total)

ARCHITECTURE RULES ENFORCED:
- Single primary LLM agent (no separate intent classifier)
- CRUD operations require exactly 1 LLM call
- RAG operations require exactly 2 LLM calls
- Tools are LangChain tools registered with the agent
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
import json
import operator

from app.config import get_settings
from app.agent.tools import CRUD_TOOLS
from app.agent.rag import RAG_TOOLS

settings = get_settings()


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """
    State maintained throughout the agent workflow.
    
    Attributes:
        messages: Conversation history with user and agent messages
        pending_tool_calls: Tools the agent wants to invoke
        rag_context: Retrieved context from semantic search (if RAG used)
        needs_rag_synthesis: Flag indicating if second LLM call needed for RAG
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    pending_tool_calls: list
    rag_context: str
    needs_rag_synthesis: bool


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an intelligent Todo Manager AI assistant. Your job is to help users manage their todo list using natural language.

## Your Capabilities:
1. **CREATE** todos when users want to add new tasks
2. **READ** todos when users want to see their list
3. **UPDATE** todos when users want to modify existing tasks
4. **DELETE** todos when users want to remove tasks
5. **SEMANTIC SEARCH** for analytical or meaning-based queries

## Tool Selection Rules:
- For adding/creating tasks → use `create_todo`
- For listing/viewing all tasks → use `read_todos`
- For modifying/updating tasks → use `update_todo` (requires todo ID)
- For removing/deleting tasks → use `delete_todo` (requires todo ID)
- For semantic queries like "what tasks am I postponing?" → use `search_todos_semantic`

## Important Guidelines:
1. When user references a task without ID, first call `read_todos` to find it
2. For vague references like "my last todo" or "the milk task", search first to identify the correct ID
3. Always confirm actions with clear, friendly messages
4. For semantic/analytical queries, use `search_todos_semantic` to find relevant todos
5. If a user's request is unclear, ask for clarification

## Response Style:
- Be concise but helpful
- Use bullet points for listing multiple items
- Confirm successful operations
- Provide helpful suggestions when appropriate

You have access to these tools: create_todo, read_todos, update_todo, delete_todo, search_todos_semantic"""


# =============================================================================
# LLM INITIALIZATION
# =============================================================================

def get_llm():
    """Initialize and return the Groq LLM with streaming enabled."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.1,  # Low temperature for consistent tool calling
        streaming=True
    )


def get_llm_with_tools():
    """Get LLM bound with all available tools."""
    llm = get_llm()
    all_tools = CRUD_TOOLS + RAG_TOOLS
    return llm.bind_tools(all_tools)


# =============================================================================
# AGENT NODES
# =============================================================================

def agent_reasoning_node(state: AgentState) -> dict:
    """
    PRIMARY AGENT NODE: First LLM call for reasoning and tool selection.
    
    This node:
    1. Receives the user message
    2. Reasons about intent
    3. Decides whether to call a tool or respond directly
    
    This is the ONLY place where the main reasoning LLM call happens.
    """
    messages = state.get("messages", [])
    
    # Build prompt with system message
    prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    
    # Get LLM with tools bound
    llm = get_llm_with_tools()
    
    # Invoke LLM (this is the FIRST LLM call)
    response = llm.invoke(prompt_messages)
    
    return {"messages": [response]}


def tool_execution_node(state: AgentState) -> dict:
    """
    TOOL EXECUTION NODE: Execute tools called by the agent.
    
    Uses LangGraph's ToolNode for standardized tool execution.
    Tools interact directly with the database and return results.
    """
    all_tools = CRUD_TOOLS + RAG_TOOLS
    tool_node = ToolNode(all_tools)
    
    # Execute tools and return results
    result = tool_node.invoke(state)
    return result


def rag_synthesis_node(state: AgentState) -> dict:
    """
    RAG SYNTHESIS NODE: Second LLM call for semantic query responses.
    
    This node is ONLY called when:
    1. A semantic search tool was used
    2. The agent needs to synthesize/summarize the retrieved context
    
    This ensures RAG operations have exactly 2 LLM calls.
    """
    messages = state.get("messages", [])
    
    # Find the last tool message with RAG results
    rag_results = None
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            try:
                result = json.loads(msg.content)
                if result.get("action") == "semantic_search":
                    rag_results = result
                    break
            except (json.JSONDecodeError, KeyError):
                continue
    
    if not rag_results:
        # No RAG results found, continue without synthesis
        return {"needs_rag_synthesis": False}
    
    # Build synthesis prompt with retrieved context
    synthesis_prompt = f"""Based on the semantic search results, provide a helpful response to the user.

Search Query: {rag_results.get('query', 'Unknown')}

Retrieved Todos:
{json.dumps(rag_results.get('results', []), indent=2)}

Instructions:
- Summarize or analyze the retrieved todos based on the user's question
- Be concise and helpful
- If no relevant todos were found, say so politely
- Provide insights or suggestions if appropriate"""
    
    # Get LLM for synthesis (SECOND LLM call for RAG flows)
    llm = get_llm()
    
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=synthesis_prompt)
    ])
    
    return {
        "messages": [response],
        "needs_rag_synthesis": False
    }


# =============================================================================
# ROUTING LOGIC
# =============================================================================

def should_continue(state: AgentState) -> Literal["tool_node", "rag_synthesis", END]:
    """
    Routing function to determine next step after agent reasoning.
    
    Returns:
        - "tool_node": If agent wants to call a tool
        - "rag_synthesis": If RAG results need synthesis
        - END: If agent is done (direct response)
    """
    messages = state.get("messages", [])
    
    if not messages:
        return END
    
    last_message = messages[-1]
    
    # Check if the last message is an AI message with tool calls
    if isinstance(last_message, AIMessage):
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tool_node"
    
    return END


def after_tool_execution(state: AgentState) -> Literal["agent", "rag_synthesis", END]:
    """
    Routing function to determine next step after tool execution.
    
    Returns:
        - "rag_synthesis": If semantic search was performed, needs second LLM call
        - "agent": If the agent needs to process tool results
        - END: If done
    """
    messages = state.get("messages", [])
    
    # Check if the last tool call was a semantic search (RAG)
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            try:
                result = json.loads(msg.content)
                if result.get("action") == "semantic_search":
                    # RAG was used, need second LLM call for synthesis
                    return "rag_synthesis"
            except (json.JSONDecodeError, KeyError):
                pass
            break  # Only check the last tool message
    
    # For CRUD operations, go back to agent to formulate response
    return "agent"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def build_agent_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    
    Graph Structure:
    
    [START] → [agent_reasoning] → (has tool calls?) → [tool_execution]
                     ↑                    |                    |
                     |                    ↓                    ↓
                     |                  [END]           (was RAG?) 
                     |                                       |
                     |                     ↓ yes             ↓ no
                     |              [rag_synthesis]         back to agent
                     |                     |
                     └─────────────────────┘
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_reasoning_node)
    workflow.add_node("tool_node", tool_execution_node)
    workflow.add_node("rag_synthesis", rag_synthesis_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tool_node": "tool_node",
            "rag_synthesis": "rag_synthesis",
            END: END
        }
    )
    
    # Add conditional edges from tool execution
    workflow.add_conditional_edges(
        "tool_node",
        after_tool_execution,
        {
            "agent": "agent",
            "rag_synthesis": "rag_synthesis",
            END: END
        }
    )
    
    # RAG synthesis goes to END
    workflow.add_edge("rag_synthesis", END)
    
    # Compile the graph
    return workflow.compile()


# Create the compiled graph
agent_graph = build_agent_graph()


# =============================================================================
# AGENT INTERFACE
# =============================================================================

async def run_agent(user_message: str, conversation_history: list = None):
    """
    Run the agent with a user message and yield streaming responses.
    
    Args:
        user_message: The user's input message
        conversation_history: Optional list of previous messages
        
    Yields:
        Streaming tokens and final response
    """
    # Build initial state
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append(HumanMessage(content=user_message))
    
    initial_state = {
        "messages": messages,
        "pending_tool_calls": [],
        "rag_context": "",
        "needs_rag_synthesis": False
    }
    
    # Run the graph
    async for event in agent_graph.astream(initial_state):
        yield event


async def run_agent_sync(user_message: str, conversation_history: list = None) -> dict:
    """
    Run the agent synchronously and return the final response.
    
    Args:
        user_message: The user's input message
        conversation_history: Optional list of previous messages
        
    Returns:
        Final state with all messages
    """
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append(HumanMessage(content=user_message))
    
    initial_state = {
        "messages": messages,
        "pending_tool_calls": [],
        "rag_context": "",
        "needs_rag_synthesis": False
    }
    
    # Run the graph and get final state
    final_state = await agent_graph.ainvoke(initial_state)
    return final_state
