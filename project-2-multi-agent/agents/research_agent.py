import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langsmith import traceable
from tools.rag_tool import query_knowledge_base_raw

load_dotenv()


def _extract_camel_identifiers(text: str) -> list[str]:
    matches = re.findall(r'\b([a-z][a-z]+(?:[A-Z][a-zA-Z0-9]+)+)\b', text)
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


@traceable(name="research_agent", run_type="chain")
def run_research_agent(task: str, raw: dict = None, conversation_history: list = None) -> str:
    if raw is None:
        raw = query_knowledge_base_raw(task)

    answer = raw.get("answer", "")
    sources = raw.get("sources", [])
    rewritten = raw.get("rewritten_question", task)

    if not answer or "not running" in answer or answer.startswith("Error"):
        return "Cannot reach the knowledge base. Please ensure the RAG service is running."

    # Extract method names from the rewritten query for a focused target hint.
    # The rewriter adds terms like "createDlmsDacsOrder" — tell the LLM to focus there.
    identifiers = _extract_camel_identifiers(rewritten)
    target_hint = (
        f"\n\nYou are answering specifically about: {', '.join(identifiers[:3])}"
        if identifiers else ""
    )

    source_text = "\n".join([f"- {s}" for s in sources]) if sources else "None"
    context = f"RAG Answer:\n{answer}\n\nSources:\n{source_text}"

    llm = ChatGroq(model="llama-3.3-70b-versatile")

    messages = [
        SystemMessage(content=f"""You are an expert Java developer analysing a microservices codebase.

You have been given a RAG-retrieved answer and its source list. Your job is to enhance and expand it.{target_hint}

Rules:
- Answer ONLY what was asked. DAC question → DAC method. MICA question → MICA method.
- Reference exact method names, class names, and field names from the provided context.
- Trace method call sequences step by step where relevant.
- If the context contains conflicting information, trust source labels — the method name in the question wins.
- If the context is insufficient, say so clearly rather than guessing.""")
    ]

    if conversation_history:
        for msg in conversation_history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=f"Question: {task}\n\n{context}"))

    response = llm.invoke(messages)
    return response.content
