import { Task } from "@/lib/api";
import clsx from "clsx";

const STAGES = [
  { key: "research", label: "Research" },
  { key: "planning", label: "Planning" },
  { key: "writing", label: "Writing Code" },
  { key: "reviewing", label: "Reviewing" },
  { key: "awaiting_approval", label: "Awaiting Approval" },
  { key: "applying", label: "Applying" },
  { key: "complete", label: "Done" },
];

const STAGE_ORDER = STAGES.map((s) => s.key);

function getStageIndex(stage: string) {
  return STAGE_ORDER.indexOf(stage);
}

export function PipelineProgress({ stage }: { stage: Task["stage"] }) {
  const current = getStageIndex(stage);

  return (
    <div className="flex items-center gap-0">
      {STAGES.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={s.key} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  "w-3 h-3 rounded-full border-2 transition-all",
                  done && "bg-brand-500 border-brand-500",
                  active && "bg-brand-500 border-brand-500 ring-4 ring-brand-500/20",
                  !done && !active && "bg-transparent border-gray-600"
                )}
              />
              <span
                className={clsx(
                  "text-[10px] mt-1 whitespace-nowrap",
                  active ? "text-brand-500 font-semibold" : done ? "text-gray-400" : "text-gray-600"
                )}
              >
                {s.label}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div
                className={clsx(
                  "h-0.5 w-8 mx-1 mb-4",
                  i < current ? "bg-brand-500" : "bg-gray-700"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
