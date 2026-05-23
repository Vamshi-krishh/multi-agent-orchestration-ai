import streamlit as st
from graph.rag_graph import rag_graph
from src.grader import detect_response_type
from src.loader import load_and_split_pdf
from src.embedder import create_vector_store

st.set_page_config(page_title="RAG Chatbot", layout="wide")
st.title("Document Q&A — Agentic RAG")

GREETINGS = {"hi", "hello", "hey", "sup", "good morning", "good evening", "good afternoon", "howdy"}
WELCOME_MESSAGE = "Hello! I'm your Knowledge Assistant. Choose a topic below or type your own question."

QUICK_ACTIONS = [
    "What is system design?",
    "How does load balancing work step by step?",
    "Explain microservices architecture",
    "What is the difference between SQL and NoSQL?",
    "How does authentication flow work?",
    "What are SOLID principles?",
]

def is_greeting(text: str) -> bool:
    return text.strip().lower().rstrip("!.,?") in GREETINGS

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type="pdf",
        accept_multiple_files=True
    )
    if uploaded_files:
        if st.button("Process Documents"):
            with st.spinner("Processing..."):
                all_chunks = []
                for file in uploaded_files:
                    save_path = f"data/{file.name}"
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())
                    chunks = load_and_split_pdf(save_path)
                    all_chunks.extend(chunks)
                create_vector_store(all_chunks)
                st.success(f"Processed {len(all_chunks)} chunks!")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "sources" in message:
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# Show quick action buttons when chat is empty or after a greeting
show_buttons = (
    len(st.session_state.messages) == 0 or
    st.session_state.get("show_quick_actions", False)
)
if show_buttons:
    cols = st.columns(2)
    for i, action in enumerate(QUICK_ACTIONS):
        if cols[i % 2].button(action, use_container_width=True, key=f"btn_{i}"):
            st.session_state.pending_question = action
            st.session_state.show_quick_actions = False
            st.rerun()

# chat_input must be called unconditionally so Streamlit always renders it
typed_input = st.chat_input("Ask a question about your documents...")

# Resolve prompt from button click or text input
prompt = None
if st.session_state.get("pending_question"):
    prompt = st.session_state.pending_question
    st.session_state.pending_question = None
elif typed_input:
    prompt = typed_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        if is_greeting(prompt):
            answer = WELCOME_MESSAGE
            sources = []
            st.write(answer)
            st.session_state.show_quick_actions = True
        else:
            with st.spinner("Thinking..."):
                response_type = detect_response_type(prompt)
                history = st.session_state.messages[:-1]

                result = rag_graph.invoke({
                    "question": prompt,
                    "rewritten_question": "",
                    "documents": [],
                    "generation": "",
                    "sources": [],
                    "web_search_needed": False,
                    "conversation_history": history,
                    "retry_count": 0,
                    "response_type": response_type
                })

            answer = result["generation"]
            sources = result["sources"]
            rewritten = result["rewritten_question"]

            st.write(answer)
            st.caption(f"Search query used: _{rewritten}_")
            if sources:
                with st.expander("Sources"):
                    for source in sources:
                        st.write(f"- {source}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
