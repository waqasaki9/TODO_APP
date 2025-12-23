# Todo Agent (AI-Powered)

A small project I built to manage todos with a friendly chat UI. You can type things like add buy milk or show my tasks and the agent will figure it out. Under the hood it uses FastAPI, React, a LangGraph agent, PostgreSQL, and ChromaDB for semantic search. It's simple to run locally and easy to tweak.

GitHub: https://github.com/WAQASAKI/TODO_APP

## What's Inside

- FastAPI backend with REST and a `/ws/chat` WebSocket
- LangGraph + Groq LLM for intent + tool selection
- PostgreSQL for storing todos (async SQLAlchemy)
- ChromaDB for semantic search (RAG)
- React + Vite frontend with live updates

## Quick Start (Windows)

- Open two terminals (backend and frontend).
- Make sure PostgreSQL is running locally.

Backend

```powershell
cd backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt



uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend

```powershell
cd frontend
npm install
npm run dev


Open http://localhost:5173 and start chatting.

## How It Works

- The frontend opens a WebSocket to `ws://localhost:8000/ws/chat`.
- You type a message, the agent decides whether to call a CRUD tool (create/read/update/delete) or perform a RAG search.
- For CRUD, its usually a single LLM call + a tool execution.
- For semantic queries, it does retrieval + a follow-up LLM call to synthesize an answer.
- The UI streams tokens for a nice typing effect and refreshes the todo list when tools run.

## API Overview

- WebSocket: `ws://localhost:8000/ws/chat`
- REST (all under `/api/todos`):
  - GET `/`  list todos
  - GET `/{id}`  get one
  - POST `/`  create
  - PUT `/{id}`  update
  - DELETE `/{id}`  delete

## Typical Prompts

- Add a task to buy groceries
- Show all my todos
- Update todo 3 to say buy eggs and milk
- Delete todo 1
- Find todos related to exams

## Configuration

Backend `.env` in `backend/` (use lowercase keys):

CORS is already set to allow `http://localhost:5173` in the backend.



## Tech Stack

- Backend: FastAPI, SQLAlchemy (async), Uvicorn
- AI: LangChain/LangGraph, Groq
- Search: ChromaDB + sentence-transformers
- Frontend: React + Vite


