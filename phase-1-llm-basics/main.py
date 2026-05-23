from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant")

conversation_history = [
    SystemMessage(content="You are a helpful AI engineering mentor.")
]

print("Chat started. Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break
    
    conversation_history.append(HumanMessage(content=user_input))
    response = llm.invoke(conversation_history)
    conversation_history.append(AIMessage(content=response.content))
    
    print(f"AI: {response.content}\n")
