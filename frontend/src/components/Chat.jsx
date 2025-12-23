/**
 * Chat Component
 * 
 * Main chat interface that displays messages and handles user input.
 * Integrates with WebSocket for real-time communication.
 */
import React, { useEffect, useRef } from 'react';
import ChatMessage, { StreamingMessage } from './ChatMessage';
import ChatInput from './ChatInput';
import './Chat.css';

/**
 * Chat Component
 * 
 * @param {Object} props
 * @param {Array} props.messages - Array of chat messages
 * @param {boolean} props.isStreaming - Whether response is being streamed
 * @param {string} props.streamingContent - Current streaming content
 * @param {Function} props.onSendMessage - Callback when user sends message
 * @param {boolean} props.isConnected - WebSocket connection status
 * @param {Function} props.onClearChat - Callback to clear chat history
 */
function Chat({ 
  messages, 
  isStreaming, 
  streamingContent, 
  onSendMessage, 
  isConnected,
  onClearChat 
}) {
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent]);

  return (
    <div className="chat-container">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-title">
          <span className="chat-icon">🤖</span>
          <h2>AI Todo Assistant</h2>
        </div>
        <button 
          className="clear-chat-button"
          onClick={onClearChat}
          disabled={messages.length === 0}
          title="Clear chat history"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages Container */}
      <div className="messages-container" ref={messagesContainerRef}>
        {/* Welcome message when empty */}
        {messages.length === 0 && !isStreaming && (
          <div className="welcome-message">
            <div className="welcome-icon">👋</div>
            <h3>Welcome to AI Todo Manager!</h3>
            <p>I can help you manage your todo list using natural language.</p>
            <div className="example-prompts">
              <p><strong>Try saying:</strong></p>
              <ul>
                <li>"Add a task to buy groceries"</li>
                <li>"Show all my todos"</li>
                <li>"Update task 1 to include eggs"</li>
                <li>"Delete my last todo"</li>
                <li>"What tasks have I been postponing?"</li>
              </ul>
            </div>
          </div>
        )}

        {/* Chat Messages */}
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />
        ))}

        {/* Streaming Message */}
        {isStreaming && (
          <StreamingMessage content={streamingContent} />
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <ChatInput 
        onSend={onSendMessage}
        disabled={isStreaming}
        isConnected={isConnected}
      />
    </div>
  );
}

export default Chat;
