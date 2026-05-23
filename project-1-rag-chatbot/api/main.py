from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from graph.rag_graph import rag_graph
from src.grader import detect_response_type
from src.retriever import get_relevant_chunks
from src.generator import generate_answer
from langsmith import traceable

app = FastAPI(title="RAG Knowledge API", version="1.0")


class QueryRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = []


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    rewritten_question: str
    response_type: str


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    response_type = detect_response_type(request.question)

    result = rag_graph.invoke({
        "question": request.question,
        "rewritten_question": "",
        "documents": [],
        "generation": "",
        "sources": [],
        "web_search_needed": False,
        "conversation_history": request.conversation_history,
        "retry_count": 0,
        "response_type": response_type
    })

    return QueryResponse(
        answer=result["generation"],
        sources=result["sources"],
        rewritten_question=result["rewritten_question"],
        response_type=response_type
    )


@app.post("/query/simple", response_model=QueryResponse)
@traceable(name="rag_pipeline", run_type="chain")
def query_simple(request: QueryRequest):
    from src.answer_validator import validate_answer
    response_type = detect_response_type(request.question)
    answer, sources, rewritten = generate_answer(
        question=request.question,
        conversation_history=request.conversation_history,
        response_type=response_type
    )
    validation = validate_answer(request.question, answer, sources)
    if not validation.get('valid'):
        answer = f"⚠️ {validation['reason']}\n\n{answer}"
    return QueryResponse(
        answer=answer,
        sources=sources,
        rewritten_question=rewritten,
        response_type=response_type
    )


@app.get("/health")
def health():
    return {"status": "ok"}
