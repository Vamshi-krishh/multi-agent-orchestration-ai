from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

load_dotenv()

@traceable(name="rewrite_query", run_type="llm")
def rewrite_query(question, conversation_history=None):
    llm = ChatGroq(model="llama-3.1-8b-instant")

    history_text = ""
    if conversation_history:
        for msg in conversation_history[-4:]:
            history_text += f"{msg['role']}: {msg['content']}\n"

    messages = [
        SystemMessage(content="""You are a search query optimizer for a Java microservices codebase.
Rewrite the user's question to be better for semantic search in a vector database.

Rules:
- Make it standalone — replace pronouns like 'it', 'that', 'those' with the actual concept
- If the question explicitly names a service (e.g. ICPS, ILPS, IADS, KOS, ICMS), use THAT service — do not substitute or add a different one from history
- Only carry forward domain context from history if the new question does NOT already name a specific service or domain
- ONLY include a service or class name if it is explicitly mentioned in the question or conversation history — never invent one
- Expand known DLMS acronyms only when the question itself mentions DLMS, DAC, or MICA:
  DAC → add "DlmsDacsRequest DlmsDac createDlmsDacsOrder"
  MICA → add "DlmsMicaRequest DlmsMicaIdentity createDlmsMicaOrder"
- Keep it concise — one or two sentences maximum
- Return ONLY the rewritten question. Nothing else."""),
        HumanMessage(content=f"Conversation history:\n{history_text}\n\nQuestion: {question}\n\nRewritten question:")
    ]

    response = llm.invoke(messages)
    return response.content.strip()
