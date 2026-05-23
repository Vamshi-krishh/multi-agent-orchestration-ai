from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    task: str                          # original task from user
    research_findings: str             # output from Research Agent
    suggested_code: str                # output from Code Writer Agent
    review_findings: str               # output from Code Reviewer Agent
    review_verdict: str                # "APPROVED" | "NEEDS_REVISION" | "REJECT"
    revision_count: int                # number of write_code iterations completed
    suggested_tests: str               # output from Test Writer Agent
    human_approved_research: bool      # human checkpoint 1
    human_approved_code: bool          # human checkpoint 2
    human_approved_review: bool        # human checkpoint 3
    human_feedback: str                # feedback given at human checkpoints or by reviewer
    current_stage: str                 # which stage we are at
    messages: List[dict]               # full conversation log
