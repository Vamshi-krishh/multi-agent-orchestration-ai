import clsx from "clsx";

interface Props {
  score: number;
  size?: "sm" | "md";
}

export function ConfidenceScore({ score, size = "md" }: Props) {
  const color =
    score >= 75 ? "text-green-400" :
    score >= 50 ? "text-yellow-400" :
    "text-red-400";

  const barColor =
    score >= 75 ? "bg-green-400" :
    score >= 50 ? "bg-yellow-400" :
    "bg-red-400";

  if (size === "sm") {
    return (
      <span className={clsx("text-xs font-medium", color)}>
        {score}% confidence
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400">Confidence</span>
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden w-24">
        <div
          className={clsx("h-full rounded-full transition-all", barColor)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={clsx("text-xs font-semibold", color)}>{score}%</span>
    </div>
  );
}
