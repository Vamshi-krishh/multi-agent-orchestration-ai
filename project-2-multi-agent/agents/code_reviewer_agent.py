from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def run_code_reviewer_agent(task: str, suggested_code: str, revision_count: int = 0) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant")

    final_pass_note = (
        "\n\nNOTE: This is the final review pass (revision limit reached). "
        "Use REJECT: only if the code is completely broken."
        if revision_count >= 2 else ""
    )

    messages = [
        SystemMessage(content=f"""You are a senior code reviewer.
Review the code strictly and report findings in these categories:
1. Bugs — logic errors, null pointer risks, incorrect assumptions
2. Security — injection risks, exposed secrets, auth issues
3. Performance — inefficient loops, unnecessary DB calls, memory issues
4. Code quality — naming, readability, SOLID violations
5. Missing edge cases — what inputs could break this?

For each issue: state the problem, the line/section, and the suggested fix.

IMPORTANT: Your very first line must be exactly one of these verdict prefixes:
  APPROVED: (code is acceptable, minor notes only — proceed to tests)
  NEEDS_REVISION: (real bugs or significant issues found — rewrite needed)
  REJECT: (approach is fundamentally wrong — start over with new design)
{final_pass_note}"""),
        HumanMessage(content=f"Task: {task}\n\nCode to review:\n{suggested_code}")
    ]

    response = llm.invoke(messages)
    return response.content
