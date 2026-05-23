"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/TopBar";
import { TaskStatusPill } from "@/components/ui/TaskStatusPill";
import { api, Task } from "@/lib/api";
import { Plus, ChevronRight, Clock, ListTodo } from "lucide-react";
import clsx from "clsx";

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const STAGE_LABEL: Record<string, string> = {
  created: "Created",
  research: "Researching",
  planning: "Planning",
  writing: "Writing Code",
  reviewing: "Reviewing",
  awaiting_approval: "Awaiting Approval",
  applying: "Applying",
  complete: "Complete",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.listTasks()
      .then(setTasks)
      .catch(() => setTasks([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#0f1117]">
      <TopBar />

      <div className="flex flex-1 overflow-hidden">
        {/* Left: task history panel */}
        <aside className="w-56 shrink-0 border-r border-gray-800 flex flex-col bg-[#0d1117]">
          <div className="p-3 border-b border-gray-800">
            <Link
              href="/tasks/new"
              className="flex items-center justify-center gap-2 w-full py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> New Task
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2">
            <p className="px-2 pt-1 pb-2 text-[10px] uppercase tracking-widest text-gray-600">History</p>
            {loading && <p className="px-2 text-xs text-gray-600">Loading...</p>}
            {!loading && tasks.length === 0 && (
              <p className="px-2 text-xs text-gray-600">No tasks yet</p>
            )}
            {tasks.map((t) => (
              <div
                key={t.id}
                onClick={() => router.push(`/tasks/${t.id}`)}
                className="group flex items-start gap-2 px-2.5 py-2.5 rounded-lg cursor-pointer transition-colors text-gray-400 hover:bg-gray-800/70 hover:text-gray-200"
              >
                <ListTodo className="w-3.5 h-3.5 shrink-0 mt-0.5 opacity-50" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs truncate leading-snug">{t.title}</p>
                  <p className="text-[10px] text-gray-600 mt-0.5">{STAGE_LABEL[t.stage] ?? t.stage}</p>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Right: task list */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <header className="px-6 py-4 border-b border-gray-800 shrink-0 flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-white">Implementation Tasks</h1>
              <p className="text-xs text-gray-500">Research → Plan → Generate → Review → Apply</p>
            </div>
            <Link
              href="/tasks/new"
              className="flex items-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" /> New Task
            </Link>
          </header>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            {!loading && tasks.length === 0 && (
              <div className="flex flex-col items-center justify-center py-24 text-center space-y-3">
                <div className="text-gray-600 text-5xl">📋</div>
                <p className="text-gray-400 font-medium">No tasks yet</p>
                <p className="text-gray-600 text-sm">Create your first implementation task</p>
                <Link
                  href="/tasks/new"
                  className="mt-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm rounded-lg"
                >
                  + New Task
                </Link>
              </div>
            )}

            <div className="space-y-3">
              {tasks.map((task) => (
                <Link key={task.id} href={`/tasks/${task.id}`} className="block group">
                  <div className="bg-[#161b27] border border-gray-800 hover:border-gray-700 rounded-xl px-5 py-4 transition-all">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {task.service && (
                            <span className="text-[11px] px-2 py-0.5 rounded bg-gray-700 text-gray-300 font-mono">
                              {task.service.toUpperCase()}
                            </span>
                          )}
                          <span className="text-[11px] text-gray-500">
                            {STAGE_LABEL[task.stage] ?? task.stage}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-white truncate">{task.title}</p>
                        <p className="text-xs text-gray-500 mt-1 truncate">{task.description}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        <TaskStatusPill status={task.status} />
                        <div className="flex items-center gap-1 text-[11px] text-gray-600">
                          <Clock className="w-3 h-3" />
                          {timeAgo(task.created_at)}
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 shrink-0 self-center" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
