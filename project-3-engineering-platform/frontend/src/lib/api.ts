const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  rewritten_question: string;
  confidence_score: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  service: string | null;
  task_type: string;
  status: "in_progress" | "waiting_approval" | "review_failed" | "applied" | "cancelled";
  stage: "created" | "research" | "planning" | "writing" | "reviewing" | "awaiting_approval" | "applying" | "complete";
  research_findings: string | null;
  confidence_score: number | null;
  implementation_plan: string | null;
  suggested_code: string | null;
  review_findings: string | null;
  review_verdict: string | null;
  suggested_tests: string | null;
  git_branch: string | null;
  revision_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description: string;
  service?: string;
  task_type?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  chat: (question: string, history: ChatMessage[]) =>
    request<ChatResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ question, conversation_history: history }),
    }),

  createTask: (payload: TaskCreate) =>
    request<Task>("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listTasks: () => request<Task[]>("/tasks"),

  getTask: (id: string) => request<Task>(`/tasks/${id}`),

  listServices: () =>
    request<{ services: string[] }>("/tasks/services/list"),
};
