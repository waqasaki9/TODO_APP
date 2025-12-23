/**
 * WebSocket Hook for managing connection to the AI agent.
 * 
 * Handles:
 * - Connection lifecycle
 * - Message sending
 * - Streaming responses
 * - Reconnection logic
 */
import { useState, useEffect, useCallback, useRef } from 'react';

// Resolve API and WS base URLs from env
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? window.location.origin : 'http://localhost:8000');
const WS_BASE = import.meta.env.VITE_WS_URL || API_BASE.replace(/^http/, 'ws');
// Final WebSocket URL
const WS_URL = `${WS_BASE}/ws/chat`;

/**
 * Connection states
 */
export const ConnectionState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
};

/**
 * Custom hook for WebSocket connection to AI agent
 */
export function useWebSocket() {
  const [connectionState, setConnectionState] = useState(ConnectionState.DISCONNECTED);
  const [messages, setMessages] = useState([]);
  const [todos, setTodos] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState(ConnectionState.CONNECTING);

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnectionState(ConnectionState.CONNECTED);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionState(ConnectionState.ERROR);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setConnectionState(ConnectionState.DISCONNECTED);
        wsRef.current = null;
        attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionState(ConnectionState.ERROR);
      attemptReconnect();
    }
  }, []);

  /**
   * Attempt to reconnect with exponential backoff
   */
  const attemptReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
    reconnectAttemptsRef.current += 1;

    console.log(`Attempting reconnection in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((data) => {
    const { type, content, todos: updatedTodos } = data;

    switch (type) {
      case 'token':
        // Streaming token - append to current streaming content
        setIsStreaming(true);
        setStreamingContent((prev) => prev + content);
        break;

      case 'thinking':
        // Agent is processing - show thinking indicator
        setIsStreaming(true);
        setStreamingContent('');
        break;

      case 'complete':
        // Response complete
        setIsStreaming(false);
        setStreamingContent('');
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content, timestamp: new Date() }
        ]);
        // Update todos if provided
        if (updatedTodos) {
          setTodos(updatedTodos);
        }
        break;

      case 'todos_update':
        // Todos list update (e.g., on initial connection)
        if (updatedTodos) {
          setTodos(updatedTodos);
        }
        break;

      case 'error':
        // Error occurred
        setIsStreaming(false);
        setStreamingContent('');
        setMessages((prev) => [
          ...prev,
          { role: 'error', content, timestamp: new Date() }
        ]);
        break;

      default:
        console.log('Unknown message type:', type);
    }
  }, []);

  /**
   * Send message to the AI agent
   */
  const sendMessage = useCallback((message) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return false;
    }

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: message, timestamp: new Date() }
    ]);

    // Send to server
    wsRef.current.send(JSON.stringify({ message }));
    return true;
  }, []);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionState(ConnectionState.DISCONNECTED);
  }, []);

  /**
   * Clear chat history
   */
  const clearChat = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionState,
    messages,
    todos,
    isStreaming,
    streamingContent,
    sendMessage,
    connect,
    disconnect,
    clearChat,
  };
}

export default useWebSocket;
