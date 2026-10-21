"use client";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md";
}

export function ScoreBadge({ score, size = "md" }: ScoreBadgeProps) {
  const label =
    score >= 80 ? "Priority" :
    score >= 60 ? "Strong" :
    score >= 40 ? "Review" : "Skip";

  const color =
    score >= 80 ? "bg-red-100 text-red-800 border-red-200" :
    score >= 60 ? "bg-orange-100 text-orange-800 border-orange-200" :
    score >= 40 ? "bg-yellow-100 text-yellow-800 border-yellow-200" :
    "bg-gray-100 text-gray-500 border-gray-200";

  const sizeClass = size === "sm" ? "text-xs px-1.5 py-0.5" : "text-sm px-2 py-1";

  return (
    <span className={`inline-flex items-center gap-1 rounded border font-medium ${color} ${sizeClass}`}>
      <span className="font-bold">{score.toFixed(0)}</span>
      <span className="opacity-70">{label}</span>
    </span>
  );
}
