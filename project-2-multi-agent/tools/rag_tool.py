import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")


def query_knowledge_base_raw(question: str, conversation_history: list = None) -> dict:
    """Returns full response dict: answer, sources list, rewritten_question."""
    try:
        response = requests.post(
            f"{RAG_API_URL}/query/simple",
            json={"question": question, "conversation_history": conversation_history or []},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "sources": [], "rewritten_question": question}


def query_knowledge_base(question: str, conversation_history: list = None) -> str:
    try:
        response = requests.post(
            f"{RAG_API_URL}/query/simple",
            json={"question": question, "conversation_history": conversation_history or []},
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer", "No answer returned")
        sources = data.get("sources", [])
        if sources:
            source_text = "\n".join([f"- {s}" for s in sources])
            return f"{answer}\n\nSources:\n{source_text}"
        return answer
    except requests.exceptions.ConnectionError:
        return "RAG service is not running. Start Project 1 with: uvicorn api.main:app --reload"
    except requests.exceptions.Timeout:
        return "RAG service is not running. Request timed out — start Project 1 with: uvicorn api.main:app --reload"
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"
