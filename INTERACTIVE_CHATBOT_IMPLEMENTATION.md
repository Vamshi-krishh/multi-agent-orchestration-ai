# Interactive Chatbot Implementation Guide

**Created:** May 18, 2026  
**Purpose:** Transform RAG chatbot into interactive component explorer

---

## 🎯 **Goal**

Instead of:

```
User: "Hi"
Bot: "It seems you didn't ask a question..."
```

We want:

```
User: "Hi"
Bot: "👋 Hi! Hope you're doing great!

What would you like to explore?
[Components Button] [Features Button]"
```

Then guide users through:

1. **Components Path:** List all services → Select one → Show details
2. **Features Path:** Select component → Show features → Explain feature

---

## 📦 **What We Have Now**

### **Current Project Structure:**

```
c:\vamshi\AI_Projects\project-1-rag-chatbot\
├── app.py                    # Streamlit frontend
├── generator.py              # Answer generation
├── retriever.py              # Hybrid search (BM25 + semantic)
├── ingestion.py              # ChromaDB ingestion
├── chroma_db/                # Vector database
└── .env                      # API keys
```

### **New Knowledge Base:**

```
c:\vamshi\COMPONENTS\knowledge-base\
├── COMPONENT_ARCHITECTURE.md  # ✅ Just created! (1000+ lines)
├── components/
│   └── kos/
│       └── features/
│           ├── dlms-orders.md           # ✅ Already ingested
│           └── dlms-code-mapping.md     # ✅ Already ingested
└── README.md
```

---

## 🚀 **Implementation Plan**

### **Phase 1: Ingest Component Architecture** ⏱️ 5 minutes

**Goal:** Add `COMPONENT_ARCHITECTURE.md` to ChromaDB

**File:** `ingestion.py`

**Changes:**

```python
# In ingest_knowledge_base() function
# Current: Only ingests knowledge-base/components/**/features/*.md
# New: ALSO ingest knowledge-base/*.md (root level files)

def ingest_knowledge_base(knowledge_base_path: str, collection):
    """Ingest business documentation from knowledge-base/"""
    print("\n=== Ingesting Knowledge Base Documentation ===")

    # NEW: Ingest root-level architecture docs
    root_docs = glob.glob(os.path.join(knowledge_base_path, "*.md"))
    for doc_path in root_docs:
        if "README" not in doc_path:  # Skip READMEs
            print(f"Processing: {doc_path}")
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chunks = markdown_splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "source": os.path.basename(doc_path),
                        "file_name": os.path.basename(doc_path),
                        "service": "MULTI",  # Multi-service document
                        "source_type": "architecture",
                        "layer": "documentation",
                        "chunk_id": f"{os.path.basename(doc_path)}_chunk_{i}"
                    }],
                    ids=[f"arch_{os.path.basename(doc_path)}_{i}"]
                )

    # EXISTING: Ingest component-specific feature docs
    feature_docs = glob.glob(os.path.join(knowledge_base_path, "components/**/features/*.md"), recursive=True)
    # ... (rest stays the same)
```

**Run:**

```bash
cd c:\vamshi\AI_Projects\project-1-rag-chatbot
python ingestion.py
```

**Expected Output:**

```
Processing: c:\vamshi\COMPONENTS\knowledge-base\COMPONENT_ARCHITECTURE.md
✅ Ingested 25 chunks from COMPONENT_ARCHITECTURE.md
```

---

### **Phase 2: Update Generator for Greetings** ⏱️ 15 minutes

**Goal:** Detect greetings and return interactive response

**File:** `generator.py`

**Changes:**

```python
# Add at top of file
GREETING_KEYWORDS = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]

COMPONENT_LIST = {
    "Core Services": [
        {"name": "KOS", "icon": "🔑", "desc": "Certificate order orchestration"},
        {"name": "ICPS", "icon": "📜", "desc": "Certificate provisioning"},
        {"name": "ICMS", "icon": "🏛️", "desc": "CA & CRL management"},
        {"name": "FPCS", "icon": "🔐", "desc": "Cryptographic operations"}
    ],
    "Security & Access": [
        {"name": "IAM", "icon": "👤", "desc": "Authentication"},
        {"name": "IAZS", "icon": "🛡️", "desc": "Authorization (RBAC)"},
        {"name": "IDPS", "icon": "🔒", "desc": "Data protection"},
        {"name": "DPEP", "icon": "🔐", "desc": "Encryption proxy"}
    ],
    "Inventory & Discovery": [
        {"name": "IADS", "icon": "🔍", "desc": "Asset discovery"},
        {"name": "IDI", "icon": "📋", "desc": "Device inventory"}
    ],
    "Import & Distribution": [
        {"name": "SRKI", "icon": "📥", "desc": "Bulk key import"},
        {"name": "FKMS", "icon": "🗝️", "desc": "Field key management"},
        {"name": "ILPS", "icon": "⏱️", "desc": "Late provisioning"},
        {"name": "BDS", "icon": "🔄", "desc": "Batch processing"}
    ],
    "Connectivity & Gateway": [
        {"name": "IGW", "icon": "🌐", "desc": "API gateway"},
        {"name": "KCMS", "icon": "📡", "desc": "Connectivity manager"},
        {"name": "KVS", "icon": "✅", "desc": "Key verification"}
    ]
}

def is_greeting(query: str) -> bool:
    """Check if query is a greeting"""
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in GREETING_KEYWORDS)

def generate_greeting_response():
    """Generate interactive greeting with buttons"""
    return {
        "type": "greeting",
        "message": """👋 **Hi! Hope you're doing great!**

I'm your COMPONENTS assistant. I can help you explore 19 microservices and their features.

**What would you like to know about?**""",
        "options": [
            {"label": "🔧 Components", "action": "list_components", "description": "Explore all 19 microservices"},
            {"label": "📚 Features", "action": "list_features", "description": "Browse features by component"}
        ]
    }

def generate_component_list():
    """Generate component list organized by category"""
    message = "# 📦 COMPONENTS Microservices\n\n**Select a component to learn more:**\n\n"

    for category, components in COMPONENT_LIST.items():
        message += f"## {category}\n\n"
        for comp in components:
            message += f"**{comp['icon']} {comp['name']}** - {comp['desc']}\n\n"

    return {
        "type": "component_list",
        "message": message,
        "components": COMPONENT_LIST
    }

# Modify generate_answer() function
def generate_answer(query: str, k: int = 20, max_full_files: int = 2):
    """Generate answer with interactive greeting support"""

    # Check for greeting first
    if is_greeting(query):
        return generate_greeting_response()

    # Check for special commands
    if query.lower() == "list components":
        return generate_component_list()

    if query.lower().startswith("explain ") and any(comp["name"].lower() in query.lower() for category in COMPONENT_LIST.values() for comp in category):
        # Extract component name
        for category in COMPONENT_LIST.values():
            for comp in category.values():
                if comp["name"].lower() in query.lower():
                    return generate_component_details(comp["name"])

    # EXISTING: Regular RAG query processing
    # ... (rest of existing code stays the same)
```

---

### **Phase 3: Update Streamlit Frontend** ⏱️ 20 minutes

**Goal:** Display buttons and handle user interactions

**File:** `app.py`

**Changes:**

```python
import streamlit as st
from generator import generate_answer, generate_component_list

st.set_page_config(page_title="COMPONENTS Assistant", page_icon="🔧")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"  # "chat" | "component_list" | "component_detail"

st.title("🔧 COMPONENTS Knowledge Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display buttons if present
        if "options" in message:
            cols = st.columns(len(message["options"]))
            for idx, option in enumerate(message["options"]):
                if cols[idx].button(f"{option['label']}", key=f"btn_{message['id']}_{idx}"):
                    # Handle button click
                    handle_button_action(option["action"])

# Chat input
if prompt := st.chat_input("Ask about COMPONENTS..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_answer(prompt)

            if isinstance(response, dict) and "type" in response:
                # Interactive response
                st.markdown(response["message"])

                # Store options for button rendering
                message_data = {
                    "role": "assistant",
                    "content": response["message"],
                    "id": len(st.session_state.messages)
                }

                if "options" in response:
                    message_data["options"] = response["options"]

                    # Display buttons
                    cols = st.columns(len(response["options"]))
                    for idx, option in enumerate(response["options"]):
                        if cols[idx].button(f"{option['label']}", key=f"new_btn_{idx}"):
                            handle_button_action(option["action"])

                st.session_state.messages.append(message_data)
            else:
                # Regular text response
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

def handle_button_action(action: str):
    """Handle button click actions"""
    if action == "list_components":
        response = generate_component_list()
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["message"],
            "type": "component_list",
            "id": len(st.session_state.messages)
        })
        st.rerun()

    elif action == "list_features":
        # Show feature selector
        st.session_state.messages.append({
            "role": "assistant",
            "content": "**Select a component to see its features:**\n\n(Feature list coming soon)",
            "id": len(st.session_state.messages)
        })
        st.rerun()

    elif action.startswith("show_"):
        # Component details
        component_name = action.replace("show_", "").upper()
        response = generate_answer(f"Explain {component_name} in detail")
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "id": len(st.session_state.messages)
        })
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")

    if st.button("🏠 Reset Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("📦 List All Components"):
        handle_button_action("list_components")

    if st.button("📚 Browse Features"):
        handle_button_action("list_features")

    st.divider()
    st.caption("COMPONENTS Knowledge Base v2.0")
```

---

### **Phase 4: Enhanced Retrieval for Component Queries** ⏱️ 10 minutes

**Goal:** Boost component architecture docs for component-specific queries

**File:** `retriever.py`

**Changes:**

```python
# Add component detection
COMPONENT_NAMES = ["kos", "icps", "icms", "fpcs", "iam", "iazs", "iads", "idi",
                   "idps", "igw", "ilps", "fkms", "kcms", "kvs", "srki", "bds", "dpep"]

def detect_query_type(query: str):
    """Detect if query is asking about component architecture"""
    query_lower = query.lower()

    # Component explanation query
    if any(kw in query_lower for kw in ["what is", "what does", "explain", "describe", "tell me about"]):
        for comp in COMPONENT_NAMES:
            if comp in query_lower:
                return {"type": "component_explanation", "component": comp}

    # Multi-component query
    if any(kw in query_lower for kw in ["how do", "communicate", "integrate", "flow", "interaction"]):
        return {"type": "architecture_flow"}

    # Feature query
    if "feature" in query_lower or "capability" in query_lower:
        return {"type": "feature_explanation"}

    return {"type": "code_query"}

# Modify hybrid_search() function
def hybrid_search(query: str, k: int = 20, service: str = None):
    """Hybrid search with query type detection"""

    query_info = detect_query_type(query)

    # Boost architecture docs for component/architecture queries
    if query_info["type"] in ["component_explanation", "architecture_flow"]:
        # Search architecture docs with higher weight
        arch_results = collection.query(
            query_texts=[query],
            n_results=10,
            where={"source_type": "architecture"}
        )

        # Also search regular docs
        regular_results = collection.query(
            query_texts=[query],
            n_results=k - 10
        )

        # Merge results (architecture docs first)
        combined_docs = arch_results["documents"][0] + regular_results["documents"][0]
        combined_metadatas = arch_results["metadatas"][0] + regular_results["metadatas"][0]

        # Continue with hybrid scoring...
        # ... (rest of existing code)

    else:
        # EXISTING: Regular hybrid search for code queries
        # ... (existing code stays the same)
```

---

## 🧪 **Testing Plan**

### **Test 1: Greeting Response**

```
Input: "Hi"
Expected:
  ✅ Greeting message
  ✅ Two buttons: [Components] [Features]
  ✅ No "insufficient information" message
```

### **Test 2: Component List**

```
Input: Click [Components]
Expected:
  ✅ Shows all 19 components organized by category
  ✅ Each component has icon, name, description
  ✅ Clickable component names
```

### **Test 3: Component Details**

```
Input: Click "KOS"
Expected:
  ✅ Detailed KOS description
  ✅ Port, APIs, integrations
  ✅ Sample flows
  ✅ Links to related features
```

### **Test 4: Feature Exploration**

```
Input: Click [Features] → Select KOS → Click DLMS
Expected:
  ✅ DLMS feature documentation
  ✅ MICA, DAC, QD explanations
  ✅ Business flows
  ✅ Code locations
```

### **Test 5: Architecture Query**

```
Input: "How does KOS communicate with ICPS?"
Expected:
  ✅ Communication pattern explained
  ✅ REST API details
  ✅ Sample request/response flow
  ✅ Referenced from COMPONENT_ARCHITECTURE.md
```

---

## 📋 **Implementation Checklist**

- [ ] **Phase 1:** Ingest COMPONENT_ARCHITECTURE.md
  - [ ] Update `ingestion.py`
  - [ ] Run ingestion
  - [ ] Verify 25+ chunks added to ChromaDB

- [ ] **Phase 2:** Update generator.py
  - [ ] Add greeting detection
  - [ ] Add component list generation
  - [ ] Add component details generation
  - [ ] Test with direct function calls

- [ ] **Phase 3:** Update app.py
  - [ ] Add button rendering
  - [ ] Add button click handlers
  - [ ] Add sidebar quick actions
  - [ ] Test in Streamlit

- [ ] **Phase 4:** Update retriever.py
  - [ ] Add query type detection
  - [ ] Boost architecture docs for component queries
  - [ ] Test retrieval accuracy

- [ ] **Testing:**
  - [ ] Test greeting flow
  - [ ] Test component list
  - [ ] Test component details
  - [ ] Test feature exploration
  - [ ] Test architecture queries

---

## 🎨 **UI Mockups**

### **Greeting View:**

```
┌────────────────────────────────────────────┐
│  COMPONENTS Knowledge Assistant            │
├────────────────────────────────────────────┤
│                                            │
│  User: Hi                                  │
│                                            │
│  Assistant:                                │
│  👋 Hi! Hope you're doing great!           │
│                                            │
│  What would you like to know about?        │
│                                            │
│  ┌──────────────┐  ┌──────────────┐       │
│  │ 🔧 Components│  │ 📚 Features  │       │
│  │              │  │              │       │
│  └──────────────┘  └──────────────┘       │
│                                            │
└────────────────────────────────────────────┘
```

### **Component List View:**

```
┌────────────────────────────────────────────┐
│  📦 COMPONENTS Microservices               │
├────────────────────────────────────────────┤
│                                            │
│  🔑 Core Services                          │
│  • KOS - Certificate order orchestration   │
│  • ICPS - Certificate provisioning         │
│  • ICMS - CA & CRL management              │
│  • FPCS - Cryptographic operations         │
│                                            │
│  🔐 Security & Access                      │
│  • IAM - Authentication                    │
│  • IAZS - Authorization (RBAC)             │
│  • IDPS - Data protection                  │
│  • DPEP - Encryption proxy                 │
│                                            │
│  ... (more categories)                     │
│                                            │
│  [Click any component for details]         │
└────────────────────────────────────────────┘
```

### **Component Details View:**

```
┌────────────────────────────────────────────┐
│  🔑 KOS - Key Operating System             │
├────────────────────────────────────────────┤
│  Port: 39016                               │
│  Purpose: Multi-protocol certificate order │
│           orchestration & provisioning     │
│                                            │
│  Key Features:                             │
│  ✅ General Orders (Device certs, CAs)     │
│  ✅ DLMS Orders (MICA, DAC, QD)            │
│  ✅ Matter Orders (PAI, DAC)               │
│  ✅ Reel Management (Bulk manufacturing)   │
│  ✅ Product Management                     │
│  ✅ LoRaWAN Key Retrieval                  │
│  ✅ Audit & Analytics                      │
│                                            │
│  Top APIs:                                 │
│  • POST /dm/{uuid}/orders                  │
│  • POST /dm/{uuid}/dlms/mica               │
│  • POST /dm/{uuid}/reels/{id}              │
│  • GET /dm/{uuid}/orders/statistics        │
│                                            │
│  Integrations:                             │
│  → ICPS (provisioning)                     │
│  → FPCS (signing)                          │
│  → ICMS (CRL management)                   │
│  → CAPS (DLMS external CA)                 │
│  → S3 (package storage)                    │
│                                            │
│  ┌─────────────┐  ┌─────────────┐         │
│  │Browse       │  │See All      │         │
│  │Features     │  │APIs         │         │
│  └─────────────┘  └─────────────┘         │
└────────────────────────────────────────────┘
```

│ • POST /orders/dlms/dac │
│ • GET /orders/{orderId} │
│ │
│ Integrations: │
│ → ICPS (provisioning) │
│ → FPCS (signing) │
│ → ICMS (CRL management) │
│ │
│ ┌────────────┐ ┌────────────┐ │
│ │Learn DLMS │ │See APIs │ │
│ └────────────┘ └────────────┘ │
└────────────────────────────────────────────┘

````

---

## 🚀 **Quick Start Commands**

```bash
# Step 1: Ingest new architecture docs
cd c:\vamshi\AI_Projects\project-1-rag-chatbot
python ingestion.py

# Step 2: Test in Python console
python
>>> from generator import generate_answer
>>> response = generate_answer("Hi")
>>> print(response)
# Should show greeting with options

# Step 3: Start Streamlit
streamlit run app.py
````

---

## 🔮 **Future Enhancements**

### **Phase 5: Feature-Specific Docs** (Next Sprint)

- Create feature docs for each component:
  - `kos-features.md`
  - `icps-features.md`
  - `icms-features.md`
  - etc.

### **Phase 6: Code Examples** (Future)

- Link features to actual code:
  - "Show me KOS DLMS order code"
  - Returns: Full file from `DlmsOrderService.java`

### **Phase 7: Mermaid Diagrams** (Future)

- Generate diagrams for flows:
  - "Show me DLMS order flow diagram"
  - Returns: Mermaid flowchart

### **Phase 8: Multi-Turn Conversations** (Future)

- Maintain conversation context:
  - User: "Tell me about KOS"
  - Bot: "KOS is..."
  - User: "What about its DLMS feature?"
  - Bot: "KOS DLMS feature..." (remembers we're talking about KOS)

---

## 📞 **Support**

If you need help:

1. Check existing documentation in `knowledge-base/`
2. Review ingestion logs for errors
3. Test queries in Python console before Streamlit
4. Use LangSmith to debug RAG pipeline

---

**Ready to implement?**

Start with Phase 1 (5 min) → Phase 2 (15 min) → Phase 3 (20 min) → Phase 4 (10 min)

**Total time:** ~50 minutes for complete interactive chatbot! 🎉
