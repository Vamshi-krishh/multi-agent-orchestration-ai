# Prompt Engineering

---

## What Is Prompt Engineering?

Prompt engineering is the skill of writing instructions to an LLM in a way that gets the best possible output.

The same LLM gives completely different answers based on how you phrase the question.
This is not a soft skill — it is a technical skill that directly affects system accuracy and cost.

---

## Why It Matters For Senior AI Engineers

At companies like Goldman Sachs, Google, and Microsoft, prompt engineering affects:
- Accuracy of AI systems (wrong prompt = wrong answer = business risk)
- Cost (a well-written prompt uses fewer tokens = cheaper at scale)
- Reliability (a precise prompt gives consistent outputs)
- Safety (a well-designed system prompt prevents misuse)

---

## The 5 Types You Must Know

### 1. Query Engineering (RAG-specific)
Improving how users phrase retrieval questions before searching the vector database.

Real example from our project:
```
Bad:  "list me topics in system design"
      → matched system design concepts → wrong chunks → incomplete answer

Good: "what are chapter titles or post titles in this document?"
      → matched table of contents → right chunks → full answer
```

The embedding model searches by MEANING. Your question must be semantically close
to the text you want to find — not what you logically think the answer is about.

---

### 2. System Prompt Design
Instructions you give the LLM before the conversation starts.
Sets the role, rules, tone, and constraints.

Bad system prompt:
```
"You are a helpful assistant."
→ Vague. LLM will hallucinate freely.
```

Good system prompt:
```
"You are a helpful assistant.
Answer ONLY from the context provided below.
If the answer is not in the context, say 'I don't have enough information.'
Do not make up any information."
→ Prevents hallucination. Forces grounding in real data.
```

This is what we use in our RAG system. Without this, the LLM ignores the context
and answers from its training data — which may be wrong.

Java equivalent: Think of the system prompt as the configuration file for your LLM service.

---

### 3. Chain-of-Thought Prompting
Forcing the LLM to reason step by step before giving an answer.
Used heavily in agent systems.

Without chain-of-thought:
```
Question: "Should I cache this database query?"
Answer:   "Yes" or "No" — no reasoning shown
```

With chain-of-thought:
```
Question: "Should I cache this database query? Think step by step."
Answer:   "Step 1: Check query frequency — this runs 10,000 times/day
           Step 2: Check data freshness — data changes every hour
           Step 3: Check cache TTL — 1 hour TTL would be acceptable
           Conclusion: Yes, cache with 1 hour TTL"
```

The LLM that reasons out loud makes far fewer mistakes than one that jumps to answers.
Used in: LangGraph agents, complex decision-making, multi-step reasoning.

---

### 4. Structured Output Prompting
Forcing the LLM to return data in a specific format (JSON, XML, table).
Critical for production systems where the output feeds into other code.

Bad:
```
"Summarise this document"
→ Returns a paragraph. Your code can't parse a paragraph.
```

Good:
```
"Summarise this document and return as JSON:
{
  'title': string,
  'key_points': list of strings,
  'sentiment': 'positive' | 'negative' | 'neutral'
}"
→ Returns parseable JSON. Your code can process it reliably.
```

Used in: MLOps pipelines, data extraction, API responses, agent tool outputs.

---

### 5. Few-Shot Prompting
Giving the LLM examples of what you want before asking your question.
The LLM learns the pattern from examples and applies it to your input.

Zero-shot (no examples):
```
"Classify this review as positive or negative: 'The product broke on day 1'"
→ LLM guesses based on training
```

Few-shot (with examples):
```
"Classify reviews as positive or negative.

Examples:
Review: 'Great product, works perfectly' → positive
Review: 'Terrible quality, waste of money' → negative
Review: 'Decent but overpriced' → negative

Now classify:
Review: 'The product broke on day 1' → ?"
→ LLM learns your specific definition of positive/negative
```

Used in: Fine-tuning preparation, classification tasks, consistent formatting.

---

## Where Each Type Is Used In Our Projects

| Project | Prompt Engineering Type |
|---|---|
| Project 1: RAG Chatbot | Query engineering, System prompt design |
| Project 1: Advanced RAG | Query rewriting (automatic query engineering) |
| Project 2: LangGraph Agents | Chain-of-thought, System prompt per agent |
| Project 3: MLOps | Structured output (JSON responses) |
| Project 4: Fine-tuning | Few-shot prompting for training data |
| Project 5: Fraud Detection | Structured output, explanation prompts |

---

## Key Rules

**Rule 1: Be specific, not vague**
Vague: "explain databases"
Specific: "explain databases to a Java developer, using JDBC as a comparison point"

**Rule 2: Tell the LLM what NOT to do**
"Do not make up information. Do not use external knowledge."
LLMs respond well to explicit restrictions.

**Rule 3: Give context before questions**
Always put context (retrieved chunks, background info) BEFORE the question.
LLMs attend more to recent text — question at the end gets better answers.

**Rule 4: Specify output format**
"Answer in 3 bullet points" / "Return as JSON" / "Explain in one sentence"
Unspecified format = unpredictable output = unreliable system.

**Rule 5: Test prompts like you test code**
A prompt is not done until you have tested it on 10+ inputs.
One prompt that works once is not a production prompt.

---

## The Senior Interview Answer

Question: "How do you ensure LLM output quality in production?"

Answer:
"Three layers: First, system prompt design — explicit instructions on what to do
and what not to do, grounding the LLM in provided context only.
Second, query engineering — rewriting user inputs before retrieval to improve
semantic match with stored chunks.
Third, structured output — enforcing JSON schemas so downstream systems
can parse responses reliably. Combined with LangSmith tracing to monitor
prompt performance over time and catch regressions."

---

*Concept added: Session 3 — Project 1 RAG Chatbot, Naive RAG complete*
