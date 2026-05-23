# Multi-Agent Orchestration AI

A portfolio of three progressively complex AI engineering projects — from RAG-based retrieval to multi-agent LLM orchestration — built on top of a real Java microservices codebase.

---

## Projects

### Project 1 — RAG Chatbot
A production-grade Retrieval-Augmented Generation chatbot that answers questions about a Java microservices codebase.

**Key features:**
- Hybrid BM25 + semantic search over indexed codebase documentation
- LangGraph-based agentic pipeline (rewrite → retrieve → grade → generate)
- Query rewriting for standalone questions using conversation history
- Document relevance grading to filter noise before generation
- Mermaid diagram rendering for architecture and flow queries
- Multi-collection ChromaDB (per-service + general architecture)
- FastAPI backend, Groq LLM (`llama-3.1-8b-instant`), LangSmith tracing

**Stack:** Python · LangChain · LangGraph · ChromaDB · BM25 · FastAPI · Groq · LangSmith

---

### Project 2 — Multi-Agent Code Assistant
A LangGraph-powered multi-agent system that takes a coding task and autonomously researches, writes, reviews, and tests code changes.

**Agent pipeline:**
1. **Research Agent** — queries the RAG chatbot to understand relevant files and patterns
2. **Code Writer Agent** — generates code changes based on research context
3. **Code Reviewer Agent** — reviews the output and loops back if quality is insufficient
4. **Test Writer Agent** — writes unit tests for the approved code

**Key features:**
- Reviewer loop with configurable max iterations and `AUTO_APPROVE` mode
- Each agent is independently traceable via LangSmith
- RAG tool shared with Project 1 for codebase context

**Stack:** Python · LangGraph · LangChain · Groq · FastAPI

---

### Project 3 — Engineering Platform (Frontend + Backend)
A full-stack internal developer platform that surfaces the AI capabilities from Projects 1 and 2 through a polished UI.

**Features:**
- Chat interface with multi-session history, message editing, and resend
- Markdown rendering with syntax-highlighted code blocks and copy buttons
- Mermaid diagram rendering for architecture queries
- Task management with AI-assisted pipeline execution
- Confidence score display per answer
- Source attribution for retrieved chunks

**Stack:** Next.js 14 (App Router) · TypeScript · Tailwind CSS · FastAPI · SQLite

---

## Architecture

```
projects/
├── project-1-rag-chatbot/       # RAG pipeline + FastAPI
├── project-2-multi-agent/       # LangGraph multi-agent orchestrator
├── project-3-engineering-platform/
│   ├── backend/                 # FastAPI, bridges Projects 1 & 2
│   └── frontend/                # Next.js 14 UI
└── notes/                       # Learning notes and concepts
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free tier at console.groq.com)
- LangSmith API key (optional, for tracing)

### Project 1 — RAG Chatbot
```bash
cd project-1-rag-chatbot
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your keys
python ingest_all.py   # index your codebase
uvicorn api.main:app --reload --port 8000
```

### Project 2 — Multi-Agent
```bash
cd project-2-multi-agent
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### Project 3 — Platform
```bash
# Backend
cd project-3-engineering-platform/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# Frontend
cd project-3-engineering-platform/frontend
npm install
npm run dev
```

---

## Key Concepts Covered

- Retrieval-Augmented Generation (RAG)
- Hybrid search (dense + sparse / BM25)
- LangGraph agent orchestration
- Multi-agent reviewer loops
- Prompt engineering for query rewriting and grading
- Vector databases (ChromaDB)
- LLM observability (LangSmith)
- Full-stack AI application development

---

## Author

Built as a structured learning path from zero AI/ML knowledge to production-grade multi-agent systems.
