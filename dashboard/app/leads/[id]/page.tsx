import Link from "next/link";
import { notFound } from "next/navigation";
import { ScoreBadge } from "@/components/ScoreBadge";
import { StatusBadge } from "@/components/StatusBadge";
import type { LeadDetail } from "@/lib/types";

async function fetchLead(id: string): Promise<LeadDetail | null> {
  const base = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
  const res = await fetch(`${base}/api/leads/${id}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch lead");
  return res.json();
}

function AuditRow({ label, value, bad }: { label: string; value: React.ReactNode; bad?: boolean }) {
  return (
    <tr className="border-b border-gray-100 last:border-0">
      <td className="py-2 pr-4 text-sm text-gray-500 w-48">{label}</td>
      <td className={`py-2 text-sm font-medium ${bad ? "text-red-600" : "text-gray-900"}`}>{value ?? "—"}</td>
    </tr>
  );
}

export default async function LeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const lead = await fetchLead(id);
  if (!lead) notFound();

  const breakdown = lead.score_breakdown ? JSON.parse(lead.score_breakdown) : null;

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-blue-600">← Leads</Link>
          <span>/</span>
          <span>{lead.name}</span>
        </div>

        {/* Header */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900">{lead.name}</h1>
              <p className="text-gray-500 capitalize mt-0.5">{lead.trade_category}</p>
              <p className="text-gray-400 text-sm mt-1">{lead.address ?? lead.postcode}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <ScoreBadge score={lead.composite_score} />
              <StatusBadge status={lead.status ?? "new"} />
            </div>
          </div>

          <div className="flex flex-wrap gap-3 mt-4">
            {lead.website && (
              <a href={lead.website} target="_blank" rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                {lead.website}
              </a>
            )}
            {lead.phone && <span className="text-sm text-gray-600">{lead.phone}</span>}
            {lead.google_rating != null && (
              <span className="text-sm text-gray-600">
                ★ {lead.google_rating.toFixed(1)} · {lead.review_count} reviews
              </span>
            )}
          </div>
        </div>

        {/* Score breakdown */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Score Breakdown</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Website Quality", score: lead.website_score, pct: "40%" },
              { label: "Business Activity", score: lead.activity_score, pct: "35%" },
              { label: "Budget Potential", score: lead.budget_score, pct: "25%" },
            ].map(({ label, score, pct }) => (
              <div key={label} className="text-center p-4 rounded-lg bg-gray-50">
                <p className="text-xs text-gray-400 mb-1">{label} ({pct})</p>
                <p className="text-3xl font-bold text-gray-900">{score.toFixed(0)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Audit report */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Website Audit</h2>
          <table className="w-full">
            <tbody>
              <AuditRow label="PageSpeed (mobile)" value={lead.psi_performance} bad={lead.psi_performance != null && lead.psi_performance < 50} />
              <AuditRow label="LCP (ms)" value={lead.lcp_ms != null ? `${lead.lcp_ms.toLocaleString()} ms` : null} bad={lead.lcp_ms != null && lead.lcp_ms > 4000} />
              <AuditRow label="SSL / HTTPS" value={lead.has_ssl ? "✓ Valid" : "✗ Missing"} bad={!lead.has_ssl} />
              <AuditRow label="Mobile friendly" value={lead.is_mobile_friendly ? "✓ Yes" : "✗ No"} bad={!lead.is_mobile_friendly} />
              <AuditRow label="Design age (est.)" value={lead.estimated_design_year ? `~${lead.estimated_design_year}` : null} bad={lead.estimated_design_year != null && lead.estimated_design_year < 2018} />
              <AuditRow label="CMS" value={lead.cms_name} />
              <AuditRow label="Broken links" value={lead.broken_links != null ? `${lead.broken_links} found` : null} bad={(lead.broken_links ?? 0) > 0} />
            </tbody>
          </table>
        </div>

        {/* Notes */}
        {lead.notes?.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Notes</h2>
            <ul className="space-y-2">
              {lead.notes.map((n) => (
                <li key={n.id} className="text-sm text-gray-700 border-l-2 border-gray-200 pl-3">
                  <span className="text-gray-400 text-xs block">{n.created_at.slice(0, 10)}</span>
                  {n.note}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}
