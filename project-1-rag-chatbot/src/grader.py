from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

def grade_document(question: str, document: str) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant")
    messages = [
        SystemMessage(content="""You are a relevance grader for a Java codebase knowledge base.
Assess whether this code chunk is RELATED to answering the question.

A chunk is relevant if it contains ANY of:
- The class, method, field, or entity mentioned in the question
- Business logic or data structures related to the topic
- Context needed to understand the answer (e.g. a DTO used by the method)

Be GENEROUS — code often needs surrounding context to make sense.
Only mark as 'not relevant' if the chunk is clearly about a completely different feature or service.

Reply with ONLY 'relevant' or 'not relevant'. Nothing else."""),
        HumanMessage(content=f"Question: {question}\n\nDocument: {document[:1500]}")
    ]
    response = llm.invoke(messages)
    result = response.content.strip().lower()
    return "not relevant" if "not" in result else "relevant"


def grade_answer(question: str, answer: str) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant")
    messages = [
        SystemMessage(content="""You are an answer quality grader.
Assess whether the answer actually addresses the question asked.
Reply with ONLY the word 'useful' or 'not useful'. Nothing else."""),
        HumanMessage(content=f"Question: {question}\n\nAnswer: {answer}")
    ]
    response = llm.invoke(messages)
    result = response.content.strip().lower()
    return "not useful" if "not" in result else "useful"


def detect_response_type(question: str) -> str:
    flow_keywords = [
        "how does", "how do", "explain the flow", "walk me through",
        "what happens when", "step by step", "process of", "flow of",
        "sequence", "pipeline", "workflow", "trace", "end to end"
    ]
    question_lower = question.lower()
    if any(keyword in question_lower for keyword in flow_keywords):
        return "flow"
    return "factual"
