/**
 * TodoList Component
 * 
 * Displays the current list of todos.
 * Updates automatically when the AI agent modifies todos.
 */
import React from 'react';
import './TodoList.css';

/**
 * Format date for display
 */
function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

/**
 * TodoItem Component
 * 
 * @param {Object} props
 * @param {Object} props.todo - Todo object
 */
function TodoItem({ todo }) {
  return (
    <div className="todo-item">
      <div className="todo-header">
        <span className="todo-id">#{todo.id}</span>
        <span className="todo-date">{formatDate(todo.created_at)}</span>
      </div>
      <h4 className="todo-title">{todo.title}</h4>
      {todo.description && (
        <p className="todo-description">{todo.description}</p>
      )}
    </div>
  );
}

/**
 * TodoList Component
 * 
 * @param {Object} props
 * @param {Array} props.todos - Array of todo objects
 */
function TodoList({ todos }) {
  return (
    <div className="todo-list-container">
      <div className="todo-list-header">
        <h2>📝 My Todos</h2>
        <span className="todo-count">
          {todos.length} {todos.length === 1 ? 'task' : 'tasks'}
        </span>
      </div>
      
      <div className="todo-list">
        {todos.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <p>No todos yet!</p>
            <span>Ask the AI to add some tasks.</span>
          </div>
        ) : (
          todos.map((todo) => (
            <TodoItem key={todo.id} todo={todo} />
          ))
        )}
      </div>
    </div>
  );
}

export default TodoList;
