from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def run_code_writer_agent(task: str, research_findings: str, human_feedback: str = "") -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant")

    feedback_section = f"\n\nHuman feedback to incorporate:\n{human_feedback}" if human_feedback else ""

    messages = [
        SystemMessage(content="""You are a senior software engineer.
Your job is to write clean, production-quality code based on the task and research provided.
Follow these rules:
- Write complete, working code
- Add brief comments only where logic is non-obvious
- Follow SOLID principles
- Handle edge cases
- Return ONLY the code with a short explanation of key decisions"""),
        HumanMessage(content=f"Task: {task}\n\nResearch findings:\n{research_findings}{feedback_section}")
    ]

    response = llm.invoke(messages)
    return response.content
