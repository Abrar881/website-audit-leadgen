"use client";

import Link from "next/link";
import type { Lead } from "@/lib/types";
import { ScoreBadge } from "./ScoreBadge";
import { StatusBadge } from "./StatusBadge";

interface LeadsTableProps {
  leads: Lead[];
}

export function LeadsTable({ leads }: LeadsTableProps) {
  if (leads.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 p-12 text-center text-gray-400">
        No leads found. Run the pipeline to scrape and score businesses.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Business</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Trade</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Postcode</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Score</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">PSI</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Reviews</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Website</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {leads.map((lead) => (
            <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <Link
                  href={`/leads/${lead.id}`}
                  className="font-medium text-gray-900 hover:text-blue-600 hover:underline"
                >
                  {lead.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-gray-600 capitalize">
                {lead.trade_category}
              </td>
              <td className="px-4 py-3 text-gray-600">{lead.postcode ?? "—"}</td>
              <td className="px-4 py-3">
                <ScoreBadge score={lead.composite_score} size="sm" />
              </td>
              <td className="px-4 py-3">
                {lead.psi_performance != null ? (
                  <span
                    className={
                      lead.psi_performance < 50
                        ? "text-red-600 font-medium"
                        : lead.psi_performance < 90
                        ? "text-orange-600"
                        : "text-green-600"
                    }
                  >
                    {lead.psi_performance}
                  </span>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-600">
                {lead.review_count}
                {lead.google_rating != null && (
                  <span className="text-gray-400"> · ★{lead.google_rating.toFixed(1)}</span>
                )}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={lead.status ?? "new"} />
              </td>
              <td className="px-4 py-3">
                {lead.website ? (
                  <a
                    href={lead.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline truncate max-w-[160px] inline-block"
                    title={lead.website}
                  >
                    {lead.website.replace(/^https?:\/\/(www\.)?/, "")}
                  </a>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
