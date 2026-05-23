# RAG — Retrieval-Augmented Generation

---

## What Problem Does RAG Solve?

LLMs hallucinate. When they don't know something, they don't say "I don't know."
They confidently make something up.

Real example from our session:
- Asked the LLM: "What is RAG?"
- It said: "RAG = Reactor for Assembling Generation" — completely invented.

Companies cannot use raw LLMs for business:
- A bank cannot have AI inventing financial regulations
- A hospital cannot have AI inventing drug dosages
- A legal firm cannot have AI inventing contract clauses

**RAG fixes this by grounding the LLM in real documents.**

```
Without RAG:
User asks → LLM guesses from training data → may hallucinate

With RAG:
User asks → System finds real documents → gives to LLM → LLM answers from facts
```

---

## RAG vs Fine-tuning — Senior Interview Answer

This question comes up in every senior AI interview.

| | RAG | Fine-tuning |
|---|---|---|
| What it does | Retrieves fresh knowledge at query time | Bakes knowledge into model permanently |
| Cost | Cheap | Expensive |
| Speed to update | Instant (just update documents) | Slow (retrain the model) |
| Stays up to date | Yes | Goes stale when data changes |
| Best for | Factual questions on changing data | Teaching style and behavior |

**Production answer:** Use both. RAG for facts, fine-tuning for behavior.

---

## The 7 Types of RAG

### 1. Naive RAG (Basic RAG)
The simplest form.

Pipeline: Load document → chunk → embed → retrieve → answer

**Problem:** Retrieves based on keyword similarity only.
If you ask "what is the company's time off policy?" and the document says
"annual leave entitlement" — it may miss it because the words don't match.

**Used for:** Internal demos, prototypes, toy projects.
**Resume value:** Zero. Every bootcamp graduate has built this.

---

### 2. Advanced RAG
Adds intelligence before and after retrieval.

- **Pre-retrieval:** Rewrites the user's question to be clearer before searching
- **Post-retrieval:** Re-ranks the retrieved chunks by relevance before sending to LLM

Result: Much higher accuracy than Naive RAG.

**Used for:** Production chatbots, enterprise document search.
**Resume value:** Medium.

---

### 3. Modular RAG
Each component (loader, retriever, ranker, generator) is independently swappable.
Like microservices — replace the vector DB, swap the LLM, change retrieval strategy
without rebuilding everything.

**Used for:** Scalable enterprise systems.
**Resume value:** High — shows system design thinking.

---

### 4. Agentic RAG
The retriever is not a fixed pipeline — it is an agent that DECIDES how to retrieve.

```
Naive RAG:    Question → retrieve → answer  (fixed, no thinking)

Agentic RAG:  Question → agent thinks → decides what to retrieve
                       → evaluates quality → retries if needed → answers
```

The agent can:
- Search multiple sources
- Ask a follow-up question before answering
- Decide retrieved results are not good enough and retry
- Use tools dynamically (web search, database, API)

**Used at:** Goldman Sachs, JP Morgan, Google — anywhere wrong answers have consequences.
**Resume value:** Extremely high. This is what gets 40-60 LPA interviews.

---

### 5. Graph RAG (Microsoft, 2024)
Instead of treating documents as flat chunks, builds a knowledge graph —
entities, relationships, connections between concepts.

```
Naive RAG:   "Find chunks similar to this question"
Graph RAG:   "Find all entities related to this concept and their relationships"
```

Example — Legal document:
Graph RAG understands "clause 4.2" references "clause 1.1" which references
"Schedule B" — and pulls all three together automatically.

**Used for:** Legal tech, medical records, complex enterprise knowledge bases.
**Resume value:** Very high — rare, cutting edge.

---

### 6. Corrective RAG (CRAG)
After retrieving, a grader agent checks if retrieved documents are actually relevant.
If not relevant enough — automatically searches the web or other sources to supplement.

```
Retrieve → Grade quality →
  If good:  generate answer
  If poor:  search web → combine sources → generate answer
```

**Resume value:** High — shows you understand production failure modes.

---

### 7. Self-RAG
The LLM itself decides WHETHER it needs to retrieve at all.
For simple questions it answers from its own knowledge.
For specific or factual questions it triggers retrieval.

```
"What is Python?"                      → LLM answers directly (no retrieval)
"What does page 47 of this contract say?" → triggers retrieval
```

**Resume value:** High — shows understanding of efficiency and cost optimization.

---

## What We Are Building (Not a Toy)

### Junior project (gets ignored):
> "Built a RAG chatbot using LangChain"
> Every bootcamp graduate has this.

### Our project (gets interviews):
> "Built a production Agentic RAG system with:
> - Query rewriting for improved retrieval accuracy
> - Relevance grading to filter poor retrievals
> - Corrective retrieval fallback to web search
> - Self-reflection loop for answer quality control
> - Deployed on AWS with LangSmith observability"

We are building **Agentic RAG + Corrective RAG combined.**
LangGraph is the orchestrator.

---

## The Learning Order — Why This Sequence

```
Naive RAG first      → understand the foundation
Advanced RAG         → query rewriting, re-ranking
Agentic RAG          → LangGraph orchestration (the real project)
```

You do not build a skyscraper without understanding why foundations exist.
Naive RAG is the foundation. Agentic RAG is the skyscraper.

---

## How the RAG Pipeline Works (Full Flow)

```
YOUR DOCUMENT (PDF, text, etc.)
   │
   ▼
[1. LOAD]       Read the document into Python

[2. SPLIT]      Cut into small chunks (~500 words each)
                Because LLMs cannot read 500 pages at once

[3. EMBED]      Convert each chunk into numbers (vectors)
                "machine learning" → [0.2, 0.8, 0.1, 0.4, ...]
                Captures MEANING, not just words

[4. STORE]      Save all vectors in a vector database (ChromaDB)

──── User asks a question ────

[5. RETRIEVE]   Convert question to vector → find similar chunk vectors
                "What is the leave policy?" → finds 3 most relevant chunks

[6. GENERATE]   Send: question + relevant chunks → LLM
                LLM answers FROM the chunks, not from guessing
```

### Java Analogy
```
Traditional search:  SQL WHERE clause → exact keyword match
RAG retrieval:       Semantic search  → finds by meaning, not exact words
```

---

## Key Terms

| Term | What It Means |
|---|---|
| Embedding | Converting text into a list of numbers that capture meaning |
| Vector | That list of numbers |
| Vector Database | A database optimised to search vectors by similarity |
| Chunk | A small piece of the original document |
| Retrieval | Finding the most relevant chunks for a given question |
| Grounding | Giving the LLM real facts instead of letting it guess |
| Hallucination | When LLM confidently states something false |

---

*Concept added: Session 2 — Project 1 RAG Chatbot phase*
