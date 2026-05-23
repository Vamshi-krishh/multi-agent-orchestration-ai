# Note 01 — Setup & Python Basics
> Phase: Foundation | Project: phase-1-llm-basics

---

## Why Python?
Every AI tool in existence — LangChain, LangGraph, HuggingFace, FastAPI, MLflow — is Python.
There is no version of AI engineering that is not Python. No choice here.

Your Java background is an advantage:
- You already understand OOP, APIs, logic, data structures
- Python syntax will feel easy — it is just less verbose Java
- FastAPI (Python web framework) will feel exactly like Spring Boot

---

## Concept 1: Virtual Environment (venv)

### What it is
An isolated Python environment for each project.
Every project gets its own packages, its own versions. They never conflict.

### Java equivalent
Maven/Gradle per project — same idea.

### Commands
```powershell
# Create venv (do this once per project)
python -m venv venv

# Activate venv (do this EVERY TIME you open a new terminal)
venv\Scripts\activate

# You will see (venv) at the start of your terminal line
# (venv) PS C:\vamshi\AI_Projects\phase-1-llm-basics>

# Fix if Windows blocks scripts (one time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Rule
ALWAYS activate venv before installing packages or running code.
If you forget, packages install globally and things break.

---

## Concept 2: pip (Python Package Manager)

### What it is
pip = npm for Node.js = Maven for Java
It downloads and installs Python packages from the internet.

### Commands
```powershell
pip install package-name              # install one package
pip install package1 package2         # install multiple
pip install --timeout=120 package     # install with longer timeout (slow internet)
pip list                              # see all installed packages
```

---

## Concept 3: Packages We Installed

| Package | What it does | Java equivalent |
|---|---|---|
| `langchain` | Framework to build LLM applications | Spring Framework |
| `langchain-openai` | Connects LangChain to OpenAI GPT models | Spring adapter/connector |
| `python-dotenv` | Reads secrets from .env file | application.properties loader |

### Install command used
```powershell
pip install --timeout=120 langchain langchain-openai python-dotenv
```

---

## Concept 4: .env File (Environment Variables)

### What it is
A file that stores secret keys (API keys, passwords).
You NEVER hardcode secrets in your code. You NEVER push this file to GitHub.

### How it looks
```
OPENAI_API_KEY=sk-your-key-here
```

### How Python reads it
```python
from dotenv import load_dotenv
import os

load_dotenv()  # reads the .env file
api_key = os.getenv("OPENAI_API_KEY")  # gets the value
```

### Java equivalent
`application.properties` + `@Value("${key}")` annotation

---

## Concept 5: What is an LLM?

LLM = Large Language Model
Examples: GPT-4, Claude, Gemini, Llama

It is a model trained on massive text data that can:
- Answer questions
- Write code
- Summarize documents
- Follow instructions

### How you use it (as an engineer)
You do NOT train it. You call it via an API — same as calling any REST API in Java.

```
Your Python code → OpenAI API → GPT-4 model → Response back
```

### Key terms
| Term | Meaning |
|---|---|
| Token | A chunk of text (~4 characters). LLMs charge per token. |
| Context window | How much text the model can "see" at once |
| Temperature | How creative/random the response is (0=strict, 1=creative) |
| System prompt | Instructions you give the model before the conversation |
| API key | Your personal key to access the LLM. Keep it secret. |

---

## Concept 6: LangChain

### What it is
A Python framework that makes it easier to build applications with LLMs.

Without LangChain:
```python
# You manually handle API calls, prompts, parsing, chaining
import openai
client = openai.OpenAI()
response = client.chat.completions.create(model="gpt-4", messages=[...])
text = response.choices[0].message.content  # manual parsing
```

With LangChain:
```python
# Clean, structured, chainable
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("Your question here")
print(response.content)
```

LangChain handles: prompt templates, output parsing, memory, document loading,
vector stores, chains, agents — everything we will build.

---

## First Code — Calling an LLM from Python

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()  # load API key from .env file

llm = ChatOpenAI(model="gpt-4o-mini")  # create LLM instance

message = HumanMessage(content="In one sentence, what is an AI agent?")
response = llm.invoke([message])  # call the LLM

print(response.content)  # print the response
```

### Line by line
| Line | What it does |
|---|---|
| `load_dotenv()` | Reads .env file, loads OPENAI_API_KEY into environment |
| `ChatOpenAI(model=...)` | Creates a connection to OpenAI's GPT model |
| `HumanMessage(content=...)` | Wraps your text as a "user" message |
| `llm.invoke([message])` | Sends message to GPT, waits for response |
| `response.content` | Extracts the text from the response object |

---

## Project Structure So Far

```
AI_PROJECTS/
├── notes/                          ← You are reading this
│   └── 01-setup-and-python-basics.md
│
└── phase-1-llm-basics/
    ├── venv/                       ← Virtual environment (never touch manually)
    ├── agents/                     ← Will hold agent code later
    ├── tools/                      ← Will hold tool code later
    ├── data/                       ← Will hold documents/data later
    ├── .env                        ← Your API keys (never push to GitHub)
    └── main.py                     ← Your first Python + LLM code
```

---

## What Comes Next
- Get OpenAI API key
- Create .env file with the key
- Run main.py → first LLM call from your own code
- Then: build Project 1 — RAG Chatbot

---

## Concept 7: Hallucination

When an LLM does not know something, it does not say "I don't know".
It confidently makes something up. This is called hallucination.

Real example from our session:
- Asked: "What is RAG?"
- LLM said: "RAG = Reactor for Assembling Generation" ← completely invented

Why it happens: LLMs are trained to generate plausible-sounding text.
When they lack real data, they generate something that SOUNDS right but isn't.

Why it matters: Banks, hospitals, legal firms cannot use raw LLMs.
An AI that invents regulations or drug dosages is dangerous.

How RAG fixes it:
- Without RAG: User asks → LLM guesses → may hallucinate
- With RAG: User asks → system finds real documents → feeds to LLM → LLM answers from facts

---

## Concept 8: Conversation Memory (How LLMs "Remember")

LLMs have zero memory by default. Every call is completely fresh.

The trick: you keep a list of all messages and send the full list every time.
The LLM reads the transcript and APPEARS to remember.

Three message types:
- SystemMessage  → instructions/rules (set once at start)
- HumanMessage   → what the user says
- AIMessage      → what the AI replied

Java equivalent: Like passing a full chat log ArrayList to every API call.

---

## Session 1 — Completed Milestones
- [x] Python 3.11.4 installed
- [x] Virtual environment created and activated
- [x] Packages installed: langchain, langchain-groq, python-dotenv
- [x] .env file created with GROQ_API_KEY
- [x] .gitignore created
- [x] main.py written and executed
- [x] First successful LLM call from Python code

## Output of first LLM call
Question: "In one sentence, what is an AI agent?"
Answer: "An AI agent is a software program or system that perceives its 
environment, acts on that perception, and learns from the consequences 
of its actions to achieve a specific goal or set of goals."

---
*Last updated: Session 1 complete — First LLM call working*
