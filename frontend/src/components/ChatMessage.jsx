/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with appropriate styling
 * based on the message role (user, assistant, error).
 */
import React from 'react';
import './ChatMessage.css';

/**
 * Format timestamp for display
 */
function formatTime(date) {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/**
 * ChatMessage Component
 * 
 * @param {Object} props
 * @param {string} props.role - Message role: 'user', 'assistant', or 'error'
 * @param {string} props.content - Message content
 * @param {Date} props.timestamp - Message timestamp
 */
function ChatMessage({ role, content, timestamp }) {
  const isUser = role === 'user';
  const isError = role === 'error';

  return (
    <div className={`chat-message ${role}`}>
      <div className="message-avatar">
        {isUser ? '👤' : isError ? '⚠️' : '🤖'}
      </div>
      <div className="message-content-wrapper">
        <div className="message-header">
          <span className="message-sender">
            {isUser ? 'You' : isError ? 'Error' : 'AI Assistant'}
          </span>
          {timestamp && (
            <span className="message-time">{formatTime(timestamp)}</span>
          )}
        </div>
        <div className="message-content">
          {/* Render content with line breaks preserved */}
          {content.split('\n').map((line, index) => (
            <React.Fragment key={index}>
              {line}
              {index < content.split('\n').length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * StreamingMessage Component
 * 
 * Shows the currently streaming response with typing indicator.
 * 
 * @param {Object} props
 * @param {string} props.content - Current streaming content
 */
export function StreamingMessage({ content }) {
  return (
    <div className="chat-message assistant streaming">
      <div className="message-avatar">🤖</div>
      <div className="message-content-wrapper">
        <div className="message-header">
          <span className="message-sender">AI Assistant</span>
          <span className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </div>
        <div className="message-content">
          {content || 'Thinking...'}
          <span className="cursor">|</span>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
