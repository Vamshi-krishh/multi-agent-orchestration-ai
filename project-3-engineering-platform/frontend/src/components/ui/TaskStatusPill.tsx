import { Task } from "@/lib/api";
import clsx from "clsx";

const STATUS_CONFIG = {
  in_progress: { label: "In Progress", dot: "bg-blue-400", text: "text-blue-400", bg: "bg-blue-400/10" },
  waiting_approval: { label: "Waiting Approval", dot: "bg-yellow-400", text: "text-yellow-400", bg: "bg-yellow-400/10" },
  review_failed: { label: "Review Failed", dot: "bg-red-400", text: "text-red-400", bg: "bg-red-400/10" },
  applied: { label: "Applied", dot: "bg-green-400", text: "text-green-400", bg: "bg-green-400/10" },
  cancelled: { label: "Cancelled", dot: "bg-gray-400", text: "text-gray-400", bg: "bg-gray-400/10" },
};

export function TaskStatusPill({ status }: { status: Task["status"] }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.in_progress;
  return (
    <span className={clsx("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium", cfg.bg, cfg.text)}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
