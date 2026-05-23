"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { TaskStatusPill } from "@/components/ui/TaskStatusPill";
import { PipelineProgress } from "@/components/ui/PipelineProgress";
import { ConfidenceScore } from "@/components/ui/ConfidenceScore";
import { api, Task } from "@/lib/api";
import { ArrowLeft, GitBranch, FileText, Code2, ShieldCheck, Plus, ListTodo } from "lucide-react";
import clsx from "clsx";

const STAGE_LABEL: Record<string, string> = {
  created: "Created", research: "Researching", planning: "Planning",
  writing: "Writing", reviewing: "Reviewing", awaiting_approval: "Awaiting Approval",
  applying: "Applying", complete: "Complete",
};

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [task, setTask]   = useState<Task | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.getTask(id).then(setTask).catch(() => setTask(null)).finally(() => setLoading(false));
    api.listTasks().then(setTasks).catch(() => {});
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-[#0f1117]">
        <TopBar />
        <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
          Loading task...
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="flex flex-col h-screen bg-[#0f1117]">
        <TopBar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <p className="text-gray-400">Task not found</p>
            <Link href="/tasks" className="text-brand-500 text-sm hover:underline">← Back to tasks</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-[#0f1117]">
      <TopBar />

      <div className="flex flex-1 overflow-hidden">

      {/* Tasks history panel */}
      <div className="w-56 shrink-0 border-r border-gray-800 bg-[#0d1117] flex flex-col h-full">
        <div className="px-3 py-3 border-b border-gray-800">
          <Link
            href="/tasks/new"
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New Task
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          <p className="px-3 py-1 text-[10px] uppercase tracking-wider text-gray-600">History</p>
          {tasks.length === 0 && (
            <p className="px-3 py-2 text-xs text-gray-600">No tasks yet</p>
          )}
          {tasks.map((t) => (
            <div
              key={t.id}
              onClick={() => router.push(`/tasks/${t.id}`)}
              className={clsx(
                "flex items-start gap-2 px-3 py-2.5 mx-1 rounded-lg cursor-pointer transition-colors",
                t.id === id ? "bg-brand-500/10 text-white" : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
              )}
            >
              <ListTodo className="w-3.5 h-3.5 shrink-0 mt-0.5 opacity-60" />
              <div className="min-w-0">
                <p className="text-xs truncate">{t.title}</p>
                <p className="text-[10px] text-gray-600 mt-0.5">{STAGE_LABEL[t.stage] ?? t.stage}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 px-6 py-4 border-b border-gray-800 bg-[#0f1117] flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Link href="/tasks" className="text-gray-400 hover:text-white mt-1 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2 mb-1">
                {task.service && (
                  <span className="text-[11px] px-2 py-0.5 rounded bg-gray-700 text-gray-300 font-mono">
                    {task.service.toUpperCase()}
                  </span>
                )}
                <span className="text-[11px] text-gray-500 capitalize">{task.task_type?.replace("_", " ")}</span>
              </div>
              <h1 className="text-lg font-semibold text-white">{task.title}</h1>
            </div>
          </div>
          <TaskStatusPill status={task.status} />
        </header>

        <div className="px-6 py-6 space-y-6 max-w-4xl">
          {/* Pipeline Progress */}
          <div className="bg-[#161b27] border border-gray-800 rounded-xl px-6 py-5">
            <p className="text-xs text-gray-500 mb-4 uppercase tracking-wider">Pipeline</p>
            <PipelineProgress stage={task.stage} />
          </div>

          {/* Description */}
          <Section icon={<FileText className="w-4 h-4" />} title="Task Description">
            <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{task.description}</p>
          </Section>

          {/* Research Findings */}
          {task.research_findings && (
            <Section icon={<Code2 className="w-4 h-4" />} title="Research Findings">
              {task.confidence_score !== undefined && task.confidence_score !== null && (
                <div className="mb-3">
                  <ConfidenceScore score={task.confidence_score} />
                </div>
              )}
              <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                {task.research_findings}
              </p>
            </Section>
          )}

          {/* Implementation Plan */}
          {task.implementation_plan && (
            <Section icon={<FileText className="w-4 h-4" />} title="Implementation Plan">
              <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                {task.implementation_plan}
              </p>
              {task.stage === "planning" && (
                <div className="mt-4 flex gap-3">
                  <button className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm rounded-lg transition-colors">
                    Approve Plan →
                  </button>
                  <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors">
                    Request Changes
                  </button>
                </div>
              )}
            </Section>
          )}

          {/* Generated Code */}
          {task.suggested_code && (
            <Section icon={<Code2 className="w-4 h-4" />} title="Generated Code">
              <pre className="text-xs text-gray-300 bg-[#0f1117] rounded-lg p-4 overflow-x-auto leading-relaxed">
                <code>{task.suggested_code}</code>
              </pre>
            </Section>
          )}

          {/* Review Report */}
          {task.review_findings && (
            <Section icon={<ShieldCheck className="w-4 h-4" />} title="Review Report">
              <div className="flex items-center gap-2 mb-3">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                  task.review_verdict === "APPROVED"
                    ? "bg-green-500/10 text-green-400"
                    : task.review_verdict === "NEEDS_REVISION"
                    ? "bg-yellow-500/10 text-yellow-400"
                    : "bg-red-500/10 text-red-400"
                }`}>
                  {task.review_verdict ?? "PENDING"}
                </span>
                {task.revision_count > 0 && (
                  <span className="text-xs text-gray-500">Revision {task.revision_count}</span>
                )}
              </div>
              <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                {task.review_findings}
              </p>
              {task.stage === "awaiting_approval" && (
                <div className="mt-4 flex gap-3">
                  <button className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-sm rounded-lg transition-colors">
                    ✓ Approve & Apply
                  </button>
                  <button className="px-4 py-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 text-sm rounded-lg transition-colors">
                    Request Revision
                  </button>
                  <button className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm rounded-lg transition-colors">
                    Reject
                  </button>
                </div>
              )}
            </Section>
          )}

          {/* Git Branch */}
          {task.git_branch && (
            <Section icon={<GitBranch className="w-4 h-4" />} title="Applied — Branch Created">
              <div className="bg-green-500/5 border border-green-500/20 rounded-lg px-4 py-3 space-y-2">
                <p className="text-sm text-green-400 font-mono">{task.git_branch}</p>
                <p className="text-xs text-gray-500">
                  Run{" "}
                  <code className="bg-gray-800 px-1.5 py-0.5 rounded text-gray-300">
                    git checkout {task.git_branch}
                  </code>{" "}
                  inside your service folder to review changes.
                </p>
              </div>
            </Section>
          )}

          {/* Tests */}
          {task.suggested_tests && (
            <Section icon={<ShieldCheck className="w-4 h-4" />} title="Generated Tests">
              <pre className="text-xs text-gray-300 bg-[#0f1117] rounded-lg p-4 overflow-x-auto leading-relaxed">
                <code>{task.suggested_tests}</code>
              </pre>
            </Section>
          )}
        </div>
      </div>

      </div>
    </div>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#161b27] border border-gray-800 rounded-xl px-6 py-5">
      <div className="flex items-center gap-2 text-gray-400 mb-4">
        {icon}
        <p className="text-xs uppercase tracking-wider font-medium">{title}</p>
      </div>
      {children}
    </div>
  );
}
