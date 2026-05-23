import re
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.retriever import get_relevant_chunks
from src.rewriter import rewrite_query
from langsmith import traceable

load_dotenv()

COMPONENTS_ROOT = os.getenv("COMPONENTS_ROOT", r"C:\vamshi\COMPONENTS")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_ROOT = os.path.join(_PROJECT_ROOT, "data")

_MAX_FILE_CHARS = 2000
_file_cache: dict = {}

_FILE_VIEW_VERBS = {"view", "show", "display", "open", "read", "print", "give me", "get"}
_FILE_EXTENSIONS = r'\b[\w\-]+\.(?:yml|yaml|xml|properties|json|txt|md|java|py)\b'


def _is_file_view_query(question: str) -> bool:
    """True when the user just wants to see a specific file's raw contents."""
    lower = question.lower()
    has_file = bool(re.search(_FILE_EXTENSIONS, lower))
    has_verb = any(v in lower for v in _FILE_VIEW_VERBS)
    has_contents = "contents" in lower or "content" in lower
    return has_file and (has_verb or has_contents)


def _read_file_unlimited(documents, target_filename: str = None) -> tuple[str, str] | None:
    """
    For file-view queries: read the requested file with NO char limit.
    Sorts documents so the target filename comes first before trying others.
    Returns (label, full_content) or None if no file found.
    """
    if target_filename:
        target_lower = target_filename.lower()
        docs = sorted(
            documents,
            key=lambda d: 0 if target_lower in d.metadata.get("source", "").lower()
                              or d.metadata.get("file_name", "").lower() == target_lower
                          else 1
        )
    else:
        docs = documents

    for doc in docs:
        source = doc.metadata.get("source", "")
        service = doc.metadata.get("service", "")
        if not source or not service:
            continue

        source = source.replace("/", "\\")
        full_path = os.path.join(COMPONENTS_ROOT, service, source)

        if not os.path.exists(full_path):
            doc_path = _find_doc_path(os.path.basename(source), service)
            if doc_path:
                full_path = doc_path
            else:
                continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            filename = os.path.basename(source)
            label = f"{filename} ({service})"
            return label, content
        except Exception:
            continue
    return None


def _find_doc_path(filename: str, service: str) -> str | None:
    """Search for a feature doc file under data/{service}/."""
    service_data = os.path.join(_DATA_ROOT, service)
    if not os.path.isdir(service_data):
        return None
    for match in Path(service_data).rglob(filename):
        if match.is_file():
            return str(match)
    return None


def _read_full_files(documents, max_files: int = 2) -> dict:
    """
    Read complete source files for the top-ranked documents.
    Tries COMPONENTS_ROOT first (Java code), then DATA_ROOT (feature docs).
    Iterates all documents until max_files UNIQUE files are found.
    """
    global _file_cache
    result = {}

    for doc in documents:
        if len(result) >= max_files:
            break

        source = doc.metadata.get("source", "")
        service = doc.metadata.get("service", "")
        if not source or not service:
            continue

        source = source.replace("/", "\\")
        full_path = os.path.join(COMPONENTS_ROOT, service, source)

        # Fallback: feature docs live in data/, not COMPONENTS_ROOT
        if not os.path.exists(full_path):
            doc_path = _find_doc_path(os.path.basename(source), service)
            if doc_path:
                full_path = doc_path
            else:
                continue

        if full_path in result:
            continue

        if full_path in _file_cache:
            result[full_path] = _file_cache[full_path]
            continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            filename = os.path.basename(source)
            class_name = doc.metadata.get("class_name", "")
            language = doc.metadata.get("language", "")
            label = f"{filename}::{class_name} ({service})" if class_name else f"{filename} ({service})"

            entry = {"label": label, "content": content[:_MAX_FILE_CHARS], "language": language}
            _file_cache[full_path] = entry
            result[full_path] = entry
            print(f"Read: {label} ({len(content)}->{len(entry['content'])} chars)")
        except Exception as e:
            print(f"Error reading {full_path}: {e}")

    print(f"{len(result)} unique file(s) read")
    return result


@traceable(name="generate_answer", run_type="chain")
def generate_answer(question, conversation_history=None, documents=None, response_type="factual"):
    rewritten_for_return = question

    if documents is None:
        rewritten_for_return = rewrite_query(question, conversation_history)
        documents = get_relevant_chunks(rewritten_for_return, k=6)

    # Short-circuit: file view queries bypass retrieval and LLM entirely.
    # Search the filesystem directly so rewriter/ranking can't return wrong file.
    if _is_file_view_query(question):
        filenames = re.findall(_FILE_EXTENSIONS, question.lower())
        target = filenames[0] if filenames else None
        if target:
            _SKIP_IN_PATH = {"target", "node_modules", ".git", "build", "dist"}
            for match in Path(COMPONENTS_ROOT).rglob(target):
                if not match.is_file():
                    continue
                if any(skip in match.parts for skip in _SKIP_IN_PATH):
                    continue
                try:
                    content = match.read_text(encoding="utf-8", errors="ignore")
                    rel = match.relative_to(Path(COMPONENTS_ROOT))
                    service = rel.parts[0] if rel.parts else "unknown"
                    label = f"{match.name} ({service})"
                    ext = match.suffix.lstrip(".")
                    fence = ext if ext in ("yml", "yaml", "xml", "json", "java", "py", "properties") else "text"
                    answer = f"**{label}**\n\n```{fence}\n{content}\n```"
                    return answer, [label], rewritten_for_return
                except Exception:
                    continue

    # Separate Mermaid-bearing chunks from regular chunks.
    # These must be used as-is — reading the full file would truncate past the diagram.
    mermaid_chunks = [d for d in documents if "```mermaid" in d.page_content]
    non_mermaid_docs = [d for d in documents if "```mermaid" not in d.page_content]

    full_files = _read_full_files(non_mermaid_docs, max_files=2)

    context_parts = []
    sources = []
    shown_labels = set()

    # Mermaid diagram chunks go first so the LLM sees them before any other context
    if mermaid_chunks:
        context_parts.append("=== DIAGRAM CONTEXT (output these verbatim as ```mermaid blocks) ===\n")
        for chunk in mermaid_chunks:
            filename = chunk.metadata.get("source", "").split("\\")[-1].split("/")[-1]
            service = chunk.metadata.get("service", "")
            label = f"{filename} ({service})" if service else filename
            context_parts.append(f"[Diagram source: {label}]\n{chunk.page_content}")
            if label not in sources:
                sources.append(label)
            shown_labels.add(label)

    # Primary context: complete source files with clear header
    if full_files:
        context_parts.append("=== COMPLETE SOURCE FILES ===\n")
        for i, (_, info) in enumerate(full_files.items()):
            lang = info.get("language", "java").lower()
            fence = lang if lang in ("java", "python", "go", "yaml", "xml", "json") else "text"
            context_parts.append(
                f"[File {i+1}: {info['label']}]\n```{fence}\n{info['content']}\n```"
            )
            sources.append(info["label"])
            shown_labels.add(info["label"])

    # Supplementary context: remaining chunks not already covered
    chunk_added = False
    for i, chunk in enumerate(documents):
        source = chunk.metadata.get("source", "Unknown")
        page = chunk.metadata.get("page", 0)
        filename = source.split("\\")[-1].split("/")[-1]
        service = chunk.metadata.get("service", "")
        class_name = chunk.metadata.get("class_name", "")

        if class_name:
            source_label = f"{filename}::{class_name} ({service})" if service else f"{filename}::{class_name}"
        else:
            source_label = f"{filename} ({service})" if service else filename

        if source_label in shown_labels:
            continue

        if not chunk_added:
            context_parts.append("\n=== SUPPLEMENTARY CONTEXT ===\n")
            chunk_added = True

        context_parts.append(f"[Source {i+1}: {source_label}]\n{chunk.page_content[:800]}")
        source_entry = f"{source_label} — Page {page+1}"
        if source_entry not in sources:
            sources.append(source_entry)

    context = "\n\n".join(context_parts)

    if response_type == "flow":
        system_content = """You are a senior software engineer explaining how a feature works.

You may have been given:
- Markdown documentation files [File N: *.md] — business flow, rules, and context (the WHY)
  * Some markdown files contain Mermaid diagrams (```mermaid ... ```) — these are VISUAL FLOW DIAGRAMS
- Java source files [File N: *.java] — actual implementation (the HOW)
- Supplementary code chunks [Source N]

CRITICAL RULE FOR MERMAID DIAGRAMS:
If the context contains a Mermaid diagram (```mermaid ... sequenceDiagram ... ```), you MUST:
1. Display the Mermaid diagram FIRST in your response, exactly as it appears in the context
2. Copy the ENTIRE ```mermaid block verbatim (do NOT modify, summarize, or recreate it)
3. After the diagram, provide a brief explanation of what the flow shows
4. If code files are also provided, explain which classes/methods implement each step

FORMAT when Mermaid diagram is present:
```mermaid
[Copy exact Mermaid syntax from context]
```

**Flow Explanation:**
Step 1: ...
Step 2: ...

**Code Implementation:**
- Step 1 implemented by: ClassName.methodName()
- Step 2 implemented by: ...

FORMAT when NO Mermaid diagram (code-only context):
1. <Business step from docs>
   -> <exact method/class from code that implements it>

RULES:
- NEVER recreate or modify Mermaid diagrams — copy them EXACTLY
- Use EXACT method names, class names, and field names from Java files
- If only docs available (no code), describe steps and note code is in another file
- DO NOT say "it seems like", "methods missing", or "not shown in code"
- State only what you can see in the provided context"""
    else:
        system_content = """You are a helpful assistant for a Java microservices codebase.

You have been given:
1. COMPLETE SOURCE FILES [File N] — full files (Java, YAML, XML, etc.), your PRIMARY source of truth
2. SUPPLEMENTARY CONTEXT [Source N] — additional fragments from related files

CRITICAL RULE — MERMAID DIAGRAMS:
If the context contains a ```mermaid block, OUTPUT IT VERBATIM as a fenced ```mermaid code block.
Do NOT convert it to ASCII art. Do NOT redraw it as a text diagram. Copy it exactly as-is.

CRITICAL RULE — FILE DISPLAY:
If the user asks to "view", "show", "display", or "print" a file, you MUST output the raw file content from [File N] exactly as it appears. Do NOT write code to read the file. Do NOT explain how to open it. Just paste the content directly.

Other rules:
- Use complete files as your primary source of truth.
- When answering about enums, classes, or constants: read the complete file definition.
- If a class imports from another service (e.g., ICPS imports TenantType from iotcommon), explain that relationship.
- Reference which file your answer comes from using [File 1] or [Source N].
- If the answer is not in the context, say 'I don't have enough information.'
- Do not make up any information."""

    llm = ChatGroq(model="llama-3.1-8b-instant")
    messages = [SystemMessage(content=system_content)]

    if conversation_history:
        for msg in conversation_history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"))

    response = llm.invoke(messages)
    return response.content, sources, rewritten_for_return
