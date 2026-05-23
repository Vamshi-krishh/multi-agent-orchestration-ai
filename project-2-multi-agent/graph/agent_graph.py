import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from agents.research_agent import run_research_agent
from agents.code_writer_agent import run_code_writer_agent
from agents.code_reviewer_agent import run_code_reviewer_agent
from agents.test_writer_agent import run_test_writer_agent


def _auto_approve() -> bool:
    return os.getenv("AUTO_APPROVE", "false").lower() == "true"


# --- NODES ---

def research(state: AgentState) -> dict:
    findings = run_research_agent(state["task"])
    return {
        "research_findings": findings,
        "current_stage": "awaiting_research_approval"
    }


def write_code(state: AgentState) -> dict:
    code = run_code_writer_agent(
        task=state["task"],
        research_findings=state["research_findings"],
        human_feedback=state.get("human_feedback", "")
    )
    return {
        "suggested_code": code,
        "current_stage": "awaiting_code_approval",
        "human_feedback": "",
        "revision_count": state.get("revision_count", 0) + 1
    }


def review_code(state: AgentState) -> dict:
    review = run_code_reviewer_agent(
        task=state["task"],
        suggested_code=state["suggested_code"],
        revision_count=state.get("revision_count", 0)
    )

    # Parse verdict from the first line of the reviewer response
    first_line = review.split('\n')[0].strip().upper()
    if first_line.startswith("APPROVED"):
        verdict = "APPROVED"
    elif first_line.startswith("NEEDS_REVISION"):
        verdict = "NEEDS_REVISION"
    elif first_line.startswith("REJECT"):
        verdict = "REJECT"
    else:
        verdict = "APPROVED"  # safe default if LLM forgets the prefix

    result = {
        "review_findings": review,
        "review_verdict": verdict,
        "current_stage": "awaiting_review_approval"
    }

    # When revision is needed, pass the review findings as feedback for the next write
    if verdict in ("NEEDS_REVISION", "REJECT"):
        result["human_feedback"] = review

    return result


def write_tests(state: AgentState) -> dict:
    tests = run_test_writer_agent(
        task=state["task"],
        suggested_code=state["suggested_code"],
        review_findings=state["review_findings"]
    )
    return {
        "suggested_tests": tests,
        "current_stage": "complete"
    }


# --- ROUTING ---

def route_after_research(state: AgentState) -> str:
    return "write_code" if (_auto_approve() or state.get("human_approved_research")) else END


def route_after_code(state: AgentState) -> str:
    return "review_code" if (_auto_approve() or state.get("human_approved_code")) else END


def route_after_review(state: AgentState) -> str:
    verdict = state.get("review_verdict", "APPROVED")
    revision_count = state.get("revision_count", 0)

    # Auto feedback loop: reviewer says revise and we have attempts remaining
    if verdict in ("NEEDS_REVISION", "REJECT") and revision_count < 3:
        return "write_code"

    # Approved (or max revisions reached) — proceed or wait for human gate
    return "write_tests" if (_auto_approve() or state.get("human_approved_review")) else END


# --- BUILD GRAPH ---

def build_agent_graph():
    memory = MemorySaver()
    workflow = StateGraph(AgentState)

    workflow.add_node("research", research)
    workflow.add_node("write_code", write_code)
    workflow.add_node("review_code", review_code)
    workflow.add_node("write_tests", write_tests)

    workflow.set_entry_point("research")

    workflow.add_conditional_edges("research", route_after_research,
                                   {"write_code": "write_code", END: END})
    workflow.add_conditional_edges("write_code", route_after_code,
                                   {"review_code": "review_code", END: END})
    workflow.add_conditional_edges("review_code", route_after_review,
                                   {"write_code": "write_code", "write_tests": "write_tests", END: END})
    workflow.add_edge("write_tests", END)

    return workflow.compile(checkpointer=memory)


agent_graph = build_agent_graph()
