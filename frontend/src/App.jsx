/**
 * App Component
 * 
 * Main application component that combines Chat and TodoList.
 * Manages WebSocket connection and state.
 */
import React from 'react';
import { Chat, TodoList } from './components';
import { useWebSocket, ConnectionState } from './hooks/useWebSocket';
import './App.css';

function App() {
  // WebSocket hook manages all real-time communication
  const {
    connectionState,
    messages,
    todos,
    isStreaming,
    streamingContent,
    sendMessage,
    clearChat,
  } = useWebSocket();

  const isConnected = connectionState === ConnectionState.CONNECTED;

  return (
    <div className="app">
      {/* App Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 AI Todo Manager</h1>
          <p>Manage your tasks using natural language</p>
        </div>
        <div className={`connection-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          {connectionState === ConnectionState.CONNECTING && '🔄 Connecting...'}
          {connectionState === ConnectionState.CONNECTED && '✅ Connected'}
          {connectionState === ConnectionState.DISCONNECTED && '❌ Disconnected'}
          {connectionState === ConnectionState.ERROR && '⚠️ Error'}
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="panel chat-panel">
          <Chat
            messages={messages}
            isStreaming={isStreaming}
            streamingContent={streamingContent}
            onSendMessage={sendMessage}
            isConnected={isConnected}
            onClearChat={clearChat}
          />
        </div>
        <div className="panel todo-panel">
          <TodoList todos={todos} />
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          Built with React, FastAPI, LangGraph & Groq • 
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
