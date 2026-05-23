# Note 02 — Project 1: RAG Chatbot
> Project: project-1-rag-chatbot | Stage: Agentic RAG complete

---

## Project Structure

```
project-1-rag-chatbot/
├── src/
│   ├── loader.py       ← loads PDFs, splits into chunks
│   ├── embedder.py     ← converts chunks to vectors, stores in ChromaDB
│   ├── retriever.py    ← finds relevant chunks for a question
│   ├── rewriter.py     ← rewrites user question before retrieval
│   ├── grader.py       ← scores chunk relevance + answer quality
│   └── generator.py    ← builds answer from chunks + history (factual or flow format)
├── graph/
│   ├── __init__.py
│   ├── state.py        ← GraphState TypedDict (shared data structure)
│   └── rag_graph.py    ← LangGraph nodes + edges (the full agent logic)
├── api/
│   ├── __init__.py
│   └── main.py         ← FastAPI endpoint /query (for Project 2 agents to call)
├── data/               ← PDF files go here
├── chroma_db/          ← vector database (auto-created, never touch manually)
├── app.py              ← Streamlit web UI
├── .env                ← API keys (GROQ_API_KEY, TAVILY_API_KEY)
└── .gitignore
```

---

## Evolution: Naive → Advanced → Agentic RAG

### Naive RAG
```
question → retrieve → generate → answer
```
Problem: no memory, no grading, no fallback, hallucination risk.

### Advanced RAG
```
question → rewrite → retrieve → generate (with history) → answer + sources
```
Fixed: follow-up questions, query quality, source citations.

### Agentic RAG (current — LangGraph)
```
question
   ↓
[retrieve]         rewrite query → fetch top 5 chunks from ChromaDB
   ↓
[grade_documents]  LLM scores each chunk: relevant or not relevant
   ↓
relevant? ──────→ [generate]    factual or step-by-step flow format
                       ↓
not relevant? ──→ [web_search]  Tavily fetches live web results
                       ↓
               [grade_answer]   LLM checks: does answer address the question?
                       ↓
         useful? → show answer
     not useful? → [transform_query] → retry (max 2 attempts)
```

---

## Key Concepts Learned

### Chunking
- chunk_size=1000: each chunk is max 1000 characters
- chunk_overlap=200: last 200 chars of chunk 1 repeated at start of chunk 2
- Why overlap: prevents meaning from being cut in half at chunk boundaries

### Embeddings
- Model: all-MiniLM-L6-v2 (free, runs locally, ~90MB download once)
- Converts text to 384 numbers that capture semantic meaning
- Similar meaning = similar numbers = found together in search

### ChromaDB
- Local vector database stored in chroma_db/ folder
- Run once to embed → load instantly every time after
- add_documents() appends to existing store (does not overwrite)
- Chroma.from_documents() creates new store (overwrites — avoid this)

### LangGraph — Core Concepts
- **State**: TypedDict that travels through every node. Each node reads from it and writes back to it. Java equivalent: DTO passed through a pipeline.
- **Nodes**: functions that do one job (retrieve, grade, generate, search)
- **Edges**: fixed connections between nodes (always go here next)
- **Conditional edges**: routing logic — if relevant → generate, else → web_search
- **Entry point**: where the graph starts (`retrieve`)
- **END**: terminal state — graph stops here

### Grader Design — Critical Bug Found
The grader checks LLM output with string containment:
```python
# WRONG — "not relevant" contains "relevant" → always returns "relevant"
return "relevant" if "relevant" in result else "not relevant"

# CORRECT — check for "not" first
return "not relevant" if "not" in result else "relevant"
```
This bug silently broke the entire grading system — no errors, but web search never triggered.
Lesson: always test the negative case when parsing LLM string outputs.

### Response Type Detection (Explainable Flow)
- `detect_response_type(question)` → "flow" or "factual"
- "how does", "walk me through", "step by step" → "flow" → numbered steps with source refs
- All other questions → "factual" → bullet points/paragraphs
- Generator uses different system prompt per type

### Web Search Fallback (Corrective RAG)
- Tavily API called when ALL chunks are graded not relevant
- Returns live web results as Document objects
- Sources show as URLs instead of PDF file names
- Triggered for: questions about recent events, things not in loaded documents

### FastAPI Endpoint
- `POST /query` — accepts question + conversation_history, returns answer + sources
- `GET /health` — liveness check
- Purpose: Project 2 agents call this endpoint to get knowledge
- Run with: `uvicorn api.main:app --reload`

### Greeting Detection
- Greetings bypass the graph entirely — no LLM call, no retrieval
- Returns welcome message + quick action buttons
- `st.chat_input` must be called unconditionally in Streamlit — if inside an `elif`, it won't render

---

## Production Architecture Design

This RAG is designed as a **knowledge hub** for a larger multi-agent system:

```
Layer 1 — RAG (this project)
  Ingests: PDFs, Confluence pages, raw text, code files (future)
  Exposes: FastAPI /query endpoint
  Answers: feature explanations, code flows, requirements

Layer 2 — Agents (Project 2)
  Calls /query to get knowledge
  Takes actions: writes code, creates tickets, runs tests

Layer 3 — Capstone
  New feature request → RAG understands it → Agents build it
```

Multi-source metadata tagging (for future):
```python
{"source_type": "confluence", "project": "payments-service"}
{"source_type": "code", "file": "PaymentController.java"}
{"source_type": "requirement", "feature": "refund-flow"}
```

---

## Packages Used

| Package | Purpose |
|---|---|
| langchain-community | PyPDFLoader, TavilySearchResults |
| langchain-text-splitters | RecursiveCharacterTextSplitter |
| langchain-huggingface | HuggingFaceEmbeddings |
| langchain-chroma | Chroma vector store |
| langchain-groq | ChatGroq LLM connection |
| langgraph | StateGraph, nodes, conditional edges |
| tavily-python | Web search fallback |
| fastapi | REST API for agent communication |
| uvicorn | ASGI server for FastAPI |
| streamlit | Web UI |
| pypdf | PDF text extraction |
| sentence-transformers | Embedding model (all-MiniLM-L6-v2) |
| python-dotenv | Read .env API keys |

---

## Commands

```powershell
# Run the chatbot UI
streamlit run app.py

# Run the FastAPI server (for agents)
uvicorn api.main:app --reload

# Test individual components
python test_loader.py
```

---

## Session Progress

- [x] Packages installed
- [x] .env and .gitignore created
- [x] src/loader.py — PDF loading and chunking
- [x] src/embedder.py — embedding and ChromaDB storage
- [x] src/retriever.py — similarity search
- [x] src/generator.py — LLM answer generation (factual + flow modes)
- [x] app.py — Streamlit chat UI with quick action buttons
- [x] 527 chunks embedded from 2 PDFs
- [x] src/rewriter.py — query rewriting with conversation history
- [x] src/grader.py — document + answer grading (fixed string bug)
- [x] graph/state.py — GraphState TypedDict
- [x] graph/rag_graph.py — full LangGraph (5 nodes, conditional routing)
- [x] api/main.py — FastAPI /query endpoint
- [x] Agentic RAG working — grading, web search fallback, flow responses
- [ ] Push to GitHub

---

## What Comes Next — Project 2

Project 1 is the knowledge retrieval layer.
Project 2 builds the action layer — LangGraph multi-agent system that:
- Calls the RAG /query endpoint to understand requirements
- Takes actions: writes code, creates PRs, runs tests
- Agents communicate through a shared orchestrator

Skills needed before Project 2: LangGraph (already learned here), tool use, agent memory.

---

*Last updated: Session 4 — Agentic RAG complete (LangGraph + web search + FastAPI + explainable flow)*
