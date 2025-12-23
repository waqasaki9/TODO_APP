/**
 * ChatInput Component
 * 
 * Text input for sending messages to the AI agent.
 * Supports Enter to send and Shift+Enter for new lines.
 */
import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

/**
 * ChatInput Component
 * 
 * @param {Object} props
 * @param {Function} props.onSend - Callback when message is sent
 * @param {boolean} props.disabled - Whether input is disabled
 * @param {boolean} props.isConnected - WebSocket connection status
 */
function ChatInput({ onSend, disabled, isConnected }) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [message]);

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    const trimmedMessage = message.trim();
    if (!trimmedMessage || disabled) return;
    
    onSend(trimmedMessage);
    setMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = (e) => {
    // Enter to send, Shift+Enter for new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isConnected 
              ? "Type a message... (Enter to send, Shift+Enter for new line)" 
              : "Connecting to AI agent..."
          }
          disabled={disabled || !isConnected}
          rows={1}
          className="chat-textarea"
        />
        <button
          type="submit"
          disabled={!message.trim() || disabled || !isConnected}
          className="send-button"
          aria-label="Send message"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            width="20"
            height="20"
          >
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
      <div className="input-hints">
        <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </span>
        <span className="hint-text">
          Try: "Add a task to buy groceries" or "Show my todos"
        </span>
      </div>
    </form>
  );
}

export default ChatInput;
