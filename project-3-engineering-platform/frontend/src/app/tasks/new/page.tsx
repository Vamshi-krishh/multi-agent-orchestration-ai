"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/TopBar";
import { api } from "@/lib/api";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

export default function NewTaskPage() {
  const router = useRouter();
  const [services, setServices] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    service: "",
    task_type: "feature",
  });

  useEffect(() => {
    api.listServices()
      .then((r) => setServices(r.services))
      .catch(() => {});
  }, []);

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim() || !form.description.trim()) return;
    setLoading(true);
    try {
      const task = await api.createTask({
        title: form.title.trim(),
        description: form.description.trim(),
        service: form.service || undefined,
        task_type: form.task_type,
      });
      router.push(`/tasks/${task.id}`);
    } catch {
      alert("Failed to create task. Is the backend running?");
      setLoading(false);
    }
  }

  const TASK_TYPES = ["feature", "bug_fix", "refactor", "validation", "other"];

  return (
    <div className="flex flex-col h-screen bg-[#0f1117]">
      <TopBar />

      <div className="flex-1 overflow-y-auto">
        <header className="px-6 py-4 border-b border-gray-800 flex items-center gap-3">
          <Link href="/tasks" className="text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-white">New Implementation Task</h1>
            <p className="text-xs text-gray-500">Describe what you want to build or fix</p>
          </div>
        </header>

        <form onSubmit={submit} className="max-w-2xl mx-auto px-6 py-8 space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Task Title *</label>
            <input
              type="text"
              required
              placeholder="e.g. Add email validation to DlmsOrderService"
              className="w-full bg-[#161b27] border border-gray-700 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none transition-colors"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
            />
          </div>

          {/* Service + Type row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Service</label>
              <select
                className="w-full bg-[#161b27] border border-gray-700 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-colors"
                value={form.service}
                onChange={(e) => set("service", e.target.value)}
              >
                <option value="">— Select service —</option>
                {services.map((s) => (
                  <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Type</label>
              <select
                className="w-full bg-[#161b27] border border-gray-700 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-colors"
                value={form.task_type}
                onChange={(e) => set("task_type", e.target.value)}
              >
                {TASK_TYPES.map((t) => (
                  <option key={t} value={t}>{t.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Description / Requirements *
            </label>
            <textarea
              required
              rows={8}
              placeholder={`Describe the task in detail.\n\nExamples:\n- What should change and why\n- Acceptance criteria\n- Business rules\n- Edge cases to handle`}
              className="w-full bg-[#161b27] border border-gray-700 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none transition-colors resize-none"
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </div>

          {/* Note about file upload — coming soon */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-3 text-xs text-gray-500">
            📎 File attachments (PDF, markdown, screenshots) — coming soon
          </div>

          <div className="flex gap-3 pt-2">
            <Link
              href="/tasks"
              className="flex-1 text-center px-4 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-xl transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading || !form.title.trim() || !form.description.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</>
              ) : (
                "Create Task →"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
