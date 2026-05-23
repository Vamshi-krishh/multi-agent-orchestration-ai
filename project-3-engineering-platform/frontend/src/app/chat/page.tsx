"use client";
import { useState, useRef, useEffect } from "react";
import { TopBar } from "@/components/TopBar";
import { ConfidenceScore } from "@/components/ui/ConfidenceScore";
import { api, ChatMessage } from "@/lib/api";
import { Send, Pencil, RotateCcw, Bot, User, Plus, Trash2, MessageSquare } from "lucide-react";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import { GreetingCard } from "@/components/ui/GreetingCard";
import clsx from "clsx";

const GREETINGS    = /^(hi|hello|hey|howdy|good\s*(morning|evening|afternoon)|what'?s up|hiya|sup)\s*[!?.]*$/i;
const SESSIONS_KEY = "keystream_chat_sessions";
const ACTIVE_KEY   = "keystream_active_session";

interface Message extends ChatMessage {
  id: string;
  sources?: string[];
  confidence_score?: number;
  loading?: boolean;
  variant?: "greeting";
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

function newSession(): ChatSession {
  return { id: crypto.randomUUID(), title: "New Chat", messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ChatPage() {
  const [sessions, setSessions]   = useState<ChatSession[]>([]);
  const [activeId, setActiveId]   = useState("");
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText]   = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeId) ?? null;
  const messages      = activeSession?.messages ?? [];
  const textareaRef   = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  // Load
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SESSIONS_KEY);
      const savedActive = localStorage.getItem(ACTIVE_KEY);
      if (saved) {
        const parsed: ChatSession[] = JSON.parse(saved);
        const clean = parsed.map((s) => ({ ...s, messages: s.messages.filter((m) => !m.loading) }));
        setSessions(clean);
        const match = savedActive && clean.find((s) => s.id === savedActive);
        setActiveId(match ? savedActive! : clean[0]?.id ?? "");
      } else {
        const s = newSession();
        setSessions([s]);
        setActiveId(s.id);
      }
    } catch {
      const s = newSession();
      setSessions([s]);
      setActiveId(s.id);
    }
  }, []);

  useEffect(() => { if (sessions.length) localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions)); }, [sessions]);
  useEffect(() => { if (activeId) localStorage.setItem(ACTIVE_KEY, activeId); }, [activeId]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  function createNewChat() {
    const s = newSession();
    setSessions((p) => [s, ...p]);
    setActiveId(s.id);
    setInput("");
  }

  function deleteSession(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      if (!next.length) { const s = newSession(); setActiveId(s.id); return [s]; }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  }

  function updateActive(patch: Partial<ChatSession>) {
    setSessions((p) => p.map((s) => s.id === activeId ? { ...s, ...patch, updatedAt: new Date().toISOString() } : s));
  }

  function setMessages(fn: (prev: Message[]) => Message[]) {
    setSessions((p) => p.map((s) => s.id === activeId ? { ...s, messages: fn(s.messages), updatedAt: new Date().toISOString() } : s));
  }

  const buildHistory = (upToIndex: number): ChatMessage[] =>
    messages.slice(0, upToIndex).filter((m) => !m.loading).map((m) => ({ role: m.role, content: m.content }));

  async function sendMessage(question: string, replaceFromIndex?: number) {
    if (!question.trim() || loading || !activeId) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: question };

    if (messages.filter((m) => m.role === "user").length === 0)
      updateActive({ title: question.length > 42 ? question.slice(0, 42) + "…" : question });

    if (GREETINGS.test(question.trim())) {
      setMessages((p) => [...(replaceFromIndex !== undefined ? p.slice(0, replaceFromIndex) : p), userMsg,
        { id: crypto.randomUUID(), role: "assistant", content: "", variant: "greeting" }]);
      setInput("");
      return;
    }

    const pid = crypto.randomUUID();
    setMessages((p) => [...(replaceFromIndex !== undefined ? p.slice(0, replaceFromIndex) : p), userMsg,
      { id: pid, role: "assistant", content: "", loading: true }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(question, buildHistory(replaceFromIndex ?? messages.length));
      setMessages((p) => p.map((m) => m.id === pid
        ? { ...m, content: res.answer, sources: res.sources, confidence_score: res.confidence_score, loading: false }
        : m));
    } catch {
      setMessages((p) => p.map((m) => m.id === pid
        ? { ...m, content: "Error reaching the API. Is the backend running?", loading: false }
        : m));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#0f1117]">
      <TopBar />

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left: sessions panel ── */}
        <aside className="w-48 shrink-0 border-r border-gray-800 flex flex-col bg-[#0d1117]">
          <div className="p-3 border-b border-gray-800">
            <button
              onClick={createNewChat}
              className="flex items-center justify-center gap-2 w-full py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2">
            <p className="px-2 pt-1 pb-2 text-[10px] uppercase tracking-widest text-gray-600">History</p>
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => setActiveId(s.id)}
                className={clsx(
                  "group flex items-start gap-2 px-2.5 py-2.5 rounded-lg cursor-pointer transition-colors",
                  s.id === activeId ? "bg-brand-500/15 text-white" : "text-gray-400 hover:bg-gray-800/70 hover:text-gray-200"
                )}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0 mt-0.5 opacity-50" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs truncate leading-snug">{s.title}</p>
                  <p className="text-[10px] text-gray-600 mt-0.5">{timeAgo(s.updatedAt)}</p>
                </div>
                <button
                  onClick={(e) => deleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all mt-0.5 shrink-0"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Right: chat area ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5 min-w-0">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
                <Bot className="w-12 h-12 text-gray-700" />
                <p className="text-gray-400 text-sm font-medium">Ask anything about your codebase</p>
                <p className="text-gray-600 text-xs">e.g. "Explain MICA creation flow" · "Show me kos.yml" · "What does ICPS do?"</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={msg.id} className={clsx("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-brand-500/10 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-3.5 h-3.5 text-brand-500" />
                  </div>
                )}

                <div className={clsx("max-w-[72%] min-w-0 space-y-1", msg.role === "user" && "flex flex-col items-end")}>
                  {editingId === msg.id ? (
                    <div className="space-y-2 w-full">
                      <textarea autoFocus rows={3} value={editText} onChange={(e) => setEditText(e.target.value)}
                        className="w-full bg-gray-800 border border-brand-500 rounded-xl px-4 py-3 text-sm text-white resize-none focus:outline-none" />
                      <div className="flex gap-2">
                        <button onClick={() => { setEditingId(null); sendMessage(editText, i); }} className="px-3 py-1.5 bg-brand-500 hover:bg-brand-600 text-white text-xs rounded-lg">Resend</button>
                        <button onClick={() => setEditingId(null)} className="px-3 py-1.5 bg-gray-700 text-white text-xs rounded-lg">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div className={clsx("px-4 py-3 rounded-2xl text-sm",
                      msg.role === "user" ? "bg-brand-500 text-white rounded-br-sm" : "bg-[#1a1f2e] text-gray-100 rounded-bl-sm",
                      msg.loading && "animate-pulse"
                    )}>
                      {msg.loading ? <span className="text-gray-500">Searching codebase...</span>
                        : msg.variant === "greeting" ? <GreetingCard onQuery={(q) => sendMessage(q)} />
                        : msg.role === "assistant" ? <MarkdownRenderer content={msg.content} />
                        : <span className="whitespace-pre-wrap leading-relaxed">{msg.content}</span>}
                    </div>
                  )}

                  {!msg.loading && msg.role === "assistant" && msg.variant !== "greeting" && (
                    <div className="px-1 space-y-0.5">
                      {msg.confidence_score !== undefined && <ConfidenceScore score={msg.confidence_score} size="sm" />}
                      {!!msg.sources?.length && <p className="text-[11px] text-gray-600">Sources: {msg.sources.slice(0, 3).join(" · ")}</p>}
                    </div>
                  )}

                  {!msg.loading && msg.role === "user" && editingId !== msg.id && (
                    <div className="flex gap-2 px-1">
                      <button onClick={() => { setEditingId(msg.id); setEditText(msg.content); }} className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-300 transition-colors">
                        <Pencil className="w-3 h-3" /> Edit
                      </button>
                      <button onClick={() => sendMessage(msg.content, i)} className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-300 transition-colors">
                        <RotateCcw className="w-3 h-3" /> Resend
                      </button>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-3.5 h-3.5 text-gray-300" />
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-4 py-4 border-t border-gray-800 shrink-0">
            <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} className="flex gap-3 items-end">
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
                placeholder="Ask about your codebase... (Shift+Enter for new line)"
                className="flex-1 bg-[#1a1f2e] border border-gray-700 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-white resize-none focus:outline-none transition-colors overflow-y-auto"
                style={{ minHeight: "44px", maxHeight: "160px" }}
              />
              <button type="submit" disabled={loading || !input.trim()}
                className="p-3 bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-colors shrink-0">
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
