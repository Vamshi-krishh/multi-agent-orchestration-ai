from typing import TypedDict, List
from langchain_core.documents import Document


class GraphState(TypedDict):
    question: str
    rewritten_question: str
    documents: List[Document]
    generation: str
    sources: List[str]
    web_search_needed: bool
    conversation_history: List[dict]
    retry_count: int
    response_type: str
