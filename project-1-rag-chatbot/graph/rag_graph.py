from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document
from graph.state import GraphState
from src.retriever import get_relevant_chunks
from src.rewriter import rewrite_query
from src.grader import grade_document, grade_answer, detect_response_type
from src.generator import generate_answer

load_dotenv()


# --- NODES ---

def retrieve(state: GraphState) -> dict:
    question = state["question"]
    history = state.get("conversation_history", [])
    rewritten = rewrite_query(question, history)
    chunks = get_relevant_chunks(rewritten, k=5)
    return {"rewritten_question": rewritten, "documents": chunks}


def grade_documents(state: GraphState) -> dict:
    question = state["rewritten_question"]
    documents = state["documents"]
    relevant_docs = [
        doc for doc in documents
        if grade_document(question, doc.page_content) == "relevant"
    ]
    return {
        "documents": relevant_docs,
        "web_search_needed": len(relevant_docs) == 0
    }


def web_search(state: GraphState) -> dict:
    question = state["rewritten_question"]
    search = TavilySearchResults(max_results=3)
    results = search.invoke(question)
    web_docs = [
        Document(
            page_content=r["content"],
            metadata={"source": r["url"], "page": 0}
        )
        for r in results
    ]
    return {"documents": web_docs, "web_search_needed": False}


def generate(state: GraphState) -> dict:
    answer, sources, _ = generate_answer(
        question=state["question"],
        conversation_history=state.get("conversation_history", []),
        documents=state["documents"],
        response_type=state.get("response_type", "factual")
    )
    return {"generation": answer, "sources": sources}


def transform_query(state: GraphState) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1}


# --- CONDITIONAL EDGES ---

def route_after_grading(state: GraphState) -> str:
    return "web_search" if state["web_search_needed"] else "generate"


def route_after_generation(state: GraphState) -> str:
    if state.get("retry_count", 0) >= 2:
        return "end"
    grade = grade_answer(state["question"], state["generation"])
    return "end" if grade == "useful" else "transform_query"


# --- BUILD GRAPH ---

def build_rag_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {"web_search": "web_search", "generate": "generate"}
    )
    workflow.add_edge("web_search", "generate")
    workflow.add_conditional_edges(
        "generate",
        route_after_generation,
        {"end": END, "transform_query": "transform_query"}
    )
    workflow.add_edge("transform_query", "retrieve")

    return workflow.compile()


rag_graph = build_rag_graph()
