import type { Stats } from "@/lib/types";

interface StatsOverviewProps {
  stats: Stats;
}

function Stat({ label, value, color = "text-gray-900" }: { label: string; value: number; color?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value.toLocaleString()}</p>
    </div>
  );
}

export function StatsOverview({ stats }: StatsOverviewProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Businesses" value={stats.total_businesses} />
        <Stat label="With website" value={stats.with_website} />
        <Stat label="Audited" value={stats.audited} />
        <Stat label="Scored" value={stats.scored} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Priority (80+)" value={stats.priority} color="text-red-600" />
        <Stat label="Strong (60-79)" value={stats.strong} color="text-orange-600" />
        <Stat label="Review (40-59)" value={stats.review} color="text-yellow-600" />
        <Stat label="Skip (<40)" value={stats.skip} color="text-gray-400" />
      </div>
    </div>
  );
}
