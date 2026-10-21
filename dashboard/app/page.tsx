import { Suspense } from "react";
import { LeadsTable } from "@/components/LeadsTable";
import { Filters } from "@/components/Filters";
import { Pagination } from "@/components/Pagination";
import { StatsOverview } from "@/components/StatsOverview";
import type { LeadsResponse, Stats } from "@/lib/types";

interface PageProps {
  searchParams: Promise<{
    page?: string;
    pageSize?: string;
    trade?: string;
    minScore?: string;
    maxScore?: string;
    postcode?: string;
    status?: string;
  }>;
}

async function fetchLeads(searchParams: Awaited<PageProps["searchParams"]>): Promise<LeadsResponse> {
  const params = new URLSearchParams();
  if (searchParams.page) params.set("page", searchParams.page);
  if (searchParams.pageSize) params.set("pageSize", searchParams.pageSize);
  if (searchParams.trade) params.set("trade", searchParams.trade);
  if (searchParams.minScore) params.set("minScore", searchParams.minScore);
  if (searchParams.maxScore) params.set("maxScore", searchParams.maxScore);
  if (searchParams.postcode) params.set("postcode", searchParams.postcode);
  if (searchParams.status) params.set("status", searchParams.status);

  const base = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
  const res = await fetch(`${base}/api/leads?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) return { leads: [], total: 0, page: 1, pageSize: 25 };
  return res.json();
}

async function fetchStats(): Promise<Stats> {
  const base = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
  const res = await fetch(`${base}/api/stats`, { cache: "no-store" });
  if (!res.ok) return { total_businesses: 0, with_website: 0, audited: 0, scored: 0, priority: 0, strong: 0, review: 0, skip: 0, by_trade: [] };
  return res.json();
}

export default async function HomePage({ searchParams }: PageProps) {
  const sp = await searchParams;
  const [data, stats] = await Promise.all([fetchLeads(sp), fetchStats()]);

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Website Audit Lead Gen</h1>
            <p className="text-sm text-gray-500 mt-1">Businesses with weak websites — scored and ready to contact</p>
          </div>
          <a
            href="/api/leads/export.csv"
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Export CSV
          </a>
        </div>

        <StatsOverview stats={stats} />

        <div className="space-y-3">
          <Suspense>
            <Filters />
          </Suspense>

          <LeadsTable leads={data.leads} />

          <Suspense>
            <Pagination
              page={data.page}
              pageSize={data.pageSize}
              total={data.total}
            />
          </Suspense>
        </div>
      </div>
    </main>
  );
}
