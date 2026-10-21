"use client";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-800",
  reviewed: "bg-purple-100 text-purple-800",
  contacted: "bg-indigo-100 text-indigo-800",
  qualified: "bg-green-100 text-green-800",
  rejected: "bg-gray-100 text-gray-500",
};

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? STATUS_COLORS.new;
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium capitalize ${color}`}>
      {status}
    </span>
  );
}
