from src.generator import generate_answer

question = "What is load balancing?"
answer = generate_answer(question)

print("="*50)
print(f"Question: {question}")
print("="*50)
print(f"Answer: {answer}")
