import re
import streamlit as st
import uuid
from tools.rag_tool import query_knowledge_base_raw
from agents.research_agent import run_research_agent

_KNOWN_SERVICES = {'icps', 'kos', 'icms', 'iads', 'ilps', 'igw', 'iam'}


def _parse_service_scope(question: str) -> str | None:
    lower = question.lower()
    found = set()
    for svc in _KNOWN_SERVICES:
        if re.search(rf'\bin\s+{svc}\b', lower):
            found.add(svc)
        elif re.search(rf'\b{svc}\s+service\b', lower):
            found.add(svc)
        elif re.search(rf'\b{svc.upper()}\b', question):
            found.add(svc)
    return found.pop() if len(found) == 1 else None


def _has_specific_class(question: str) -> bool:
    """True if the query names a PascalCase class like TenantType or DlmsMicaRequest.
    A specific class name is just as precise as a service name — skip disambiguation."""
    return bool(re.search(r'\b[A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+\b', question))


def _dominant_service(grouped: dict) -> bool:
    """True if one service has 3+ matched files AND at least 2x more than any other.
    Avoids disambiguation when the retriever clearly converged on one service."""
    if not grouped:
        return False
    counts = {svc: len(files) for svc, files in grouped.items()}
    top = max(counts.values())
    others = [v for v in counts.values() if v != top]
    return top >= 3 and (not others or top >= 2 * max(others))


_FILE_VIEW_VERBS = {"view", "show", "display", "open", "read", "print", "give me", "get"}
_FILE_EXT_PATTERN = re.compile(r'\b[\w\-]+\.(?:yml|yaml|xml|properties|json|txt|md|java|py)\b', re.IGNORECASE)


def _is_file_view_query(question: str) -> bool:
    """True when the user just wants to see a specific file's raw contents."""
    lower = question.lower()
    has_file = bool(_FILE_EXT_PATTERN.search(lower))
    has_verb = any(v in lower for v in _FILE_VIEW_VERBS)
    has_contents = "contents" in lower or "content" in lower
    return has_file and (has_verb or has_contents)

st.set_page_config(page_title="Codebase Assistant", layout="wide")


def new_chat():
    session_id = str(uuid.uuid4())
    st.session_state.sessions[session_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_session_id = session_id


def group_sources_by_service(sources: list[str]) -> dict[str, list[str]]:
    grouped = {}
    for source in sources:
        match = re.search(r'^(.+?)\s*\(([^)]+)\)', source)
        if match:
            filename = match.group(1).strip()
            service = match.group(2).strip()
            grouped.setdefault(service, [])
            if filename not in grouped[service]:
                grouped[service].append(filename)
    return grouped


if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if st.session_state.current_session_id is None:
    new_chat()

# --- Sidebar ---
with st.sidebar:
    st.title("Codebase Assistant")
    if st.button("+ New Chat", use_container_width=True, type="primary"):
        new_chat()
        st.rerun()

    st.divider()
    st.caption("Recent chats")

    for session_id in reversed(list(st.session_state.sessions.keys())):
        session = st.session_state.sessions[session_id]
        label = session["title"]
        is_active = session_id == st.session_state.current_session_id
        if st.button(label, key=f"btn_{session_id}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_session_id = session_id
            st.rerun()

# --- Main chat area ---
current = st.session_state.sessions[st.session_state.current_session_id]

st.title("Codebase Assistant")
st.caption("Ask anything about your microservices codebase — powered by your RAG knowledge base")

for msg in current["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about your codebase..."):
    if current["title"] == "New Chat":
        current["title"] = prompt[:45] + "..." if len(prompt) > 45 else prompt

    current["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history = [{"role": m["role"], "content": m["content"]}
                   for m in current["messages"][:-1]]

        with st.spinner("Searching codebase..."):
            raw = query_knowledge_base_raw(prompt, conversation_history=history)

        sources = raw.get("sources", [])
        grouped = group_sources_by_service(sources)

        # Skip disambiguation when the query is already specific enough:
        # - names a service ("in ICPS") → retriever already boosted that service
        # - names a PascalCase class ("TenantType") → only one definition exists
        service_scope = _parse_service_scope(prompt)
        specific_class = _has_specific_class(prompt)
        already_specific = service_scope is not None or specific_class or _dominant_service(grouped)

        multi_service = len(grouped) > 1 and not already_specific
        multi_flow = not already_specific and any(
            len([f for f in files if f.endswith("Service.java") or f.endswith("Resource.java")]) > 1
            for files in grouped.values()
        )

        if multi_service or multi_flow:
            service_lines = []
            examples = []
            for svc, files in grouped.items():
                file_list = ", ".join([f"`{f}`" for f in files])
                service_lines.append(f"- **{svc}** — {file_list}")
                # Generate a dynamic example from the first meaningful file in this service
                for f in files:
                    if f.endswith("Service.java") or f.endswith("Resource.java"):
                        examples.append(f"*'{prompt.strip('?')} in {svc} {f.replace('.java', '')}'*")
                        break
                else:
                    if files:
                        examples.append(f"*'{prompt.strip('?')} in {svc}'*")

            service_list = "\n".join(service_lines)
            example_lines = "\n".join([f"- {e}" for e in examples[:3]])
            disambiguation = (
                f"I found matches across multiple services:\n\n{service_list}\n\n"
                f"Could you be more specific? For example:\n{example_lines}"
            )
            st.markdown(disambiguation)
            current["messages"].append({"role": "assistant", "content": disambiguation})
        elif _is_file_view_query(prompt):
            # File view — project-1 already returned the verbatim content.
            # Skip research agent entirely so no LLM rewrites the file.
            raw_answer = raw.get("answer", "")
            source_text = "\n".join([f"- {s}" for s in sources])
            full_answer = f"{raw_answer}\n\n**Sources:**\n{source_text}" if sources else raw_answer
            st.markdown(full_answer)
            current["messages"].append({"role": "assistant", "content": full_answer})
        else:
            with st.spinner("Reading source files and analysing..."):
                answer = run_research_agent(prompt, raw=raw, conversation_history=history)

            if sources and not re.search(r'\bsources?\s*:', answer, re.IGNORECASE):
                source_text = "\n".join([f"- {s}" for s in sources])
                full_answer = f"{answer}\n\n**Sources:**\n{source_text}"
            else:
                full_answer = answer

            st.markdown(full_answer)
            current["messages"].append({"role": "assistant", "content": full_answer})

    st.rerun()
