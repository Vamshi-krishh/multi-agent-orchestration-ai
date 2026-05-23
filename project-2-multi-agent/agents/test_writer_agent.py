from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def run_test_writer_agent(task: str, suggested_code: str, review_findings: str) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant")

    messages = [
        SystemMessage(content="""You are a senior QA engineer.
Write comprehensive unit tests for the provided code.
Cover:
1. Happy path — expected inputs produce expected outputs
2. Edge cases — empty inputs, nulls, boundary values
3. Error cases — invalid inputs, failure scenarios
4. Any issues flagged in the code review

Use the same language as the code. Write complete, runnable tests.
Add a brief comment on what each test verifies."""),
        HumanMessage(content=f"Task: {task}\n\nCode:\n{suggested_code}\n\nReview findings:\n{review_findings}")
    ]

    response = llm.invoke(messages)
    return response.content
