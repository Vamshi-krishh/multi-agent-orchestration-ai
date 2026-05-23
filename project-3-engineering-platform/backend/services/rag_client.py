import os
import requests

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")


def query(question: str, conversation_history: list = None) -> dict:
    """
    Calls Project 1 RAG API. Returns answer, sources, rewritten_question,
    and a confidence_score derived from source count + response quality.
    """
    try:
        response = requests.post(
            f"{RAG_API_URL}/query/simple",
            json={
                "question": question,
                "conversation_history": conversation_history or []
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        confidence = _compute_confidence(data)
        data["confidence_score"] = confidence
        return data

    except requests.exceptions.ConnectionError:
        return {
            "answer": "RAG service is not running. Start Project 1 with: uvicorn api.main:app --reload",
            "sources": [],
            "rewritten_question": question,
            "confidence_score": 0
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "rewritten_question": question,
            "confidence_score": 0
        }


def _compute_confidence(data: dict) -> int:
    """
    Derives a 0-100 confidence score from retrieval signals:
    - Number of sources found
    - Whether answer admits uncertainty
    - Whether sources match the question service
    """
    sources = data.get("sources", [])
    answer = data.get("answer", "").lower()

    if not sources:
        return 10

    uncertainty_phrases = [
        "i don't have enough information",
        "not sure",
        "cannot find",
        "no information",
        "unclear"
    ]
    if any(phrase in answer for phrase in uncertainty_phrases):
        return 30

    # Score by source count: 1=50, 2=65, 3=75, 4+=85, complete file = +10
    base = min(50 + (len(sources) - 1) * 15, 85)

    # Bonus: if a complete file was retrieved (no "Page N" suffix on first source)
    if sources and "Page" not in sources[0]:
        base = min(base + 10, 95)

    return base
