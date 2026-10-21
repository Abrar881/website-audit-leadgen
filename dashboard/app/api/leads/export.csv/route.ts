import { NextRequest } from "next/server";
import { getDb } from "@/lib/db";

export const dynamic = "force-dynamic";

const FIELDS = [
  "name", "trade_category", "postcode", "address", "phone", "website",
  "google_rating", "review_count",
  "composite_score", "website_score", "activity_score", "budget_score",
  "psi_performance", "lcp_ms", "has_ssl", "is_mobile_friendly",
  "estimated_design_year", "cms_name", "broken_links", "status",
];

function escapeCsv(val: unknown): string {
  if (val == null) return "";
  const s = String(val);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const minScore = parseFloat(searchParams.get("minScore") ?? "0");
  const trade = searchParams.get("trade");

  const conditions = ["s.composite_score >= ?"];
  const params: (string | number)[] = [minScore];
  if (trade) { conditions.push("b.trade_category = ?"); params.push(trade); }

  const where = `WHERE ${conditions.join(" AND ")}`;

  try {
    const db = getDb();
    const rows = db.prepare(`
      SELECT
        b.name, b.trade_category, b.postcode, b.address, b.phone, b.website,
        b.google_rating, b.review_count,
        s.composite_score, s.website_score, s.activity_score, s.budget_score,
        a.psi_performance, a.lcp_ms, a.has_ssl, a.is_mobile_friendly,
        a.estimated_design_year, a.cms_name, a.broken_links,
        COALESCE(ls.status, 'new') as status
      FROM businesses b
      JOIN scores s ON s.business_id = b.id
      LEFT JOIN audits a ON a.id = s.audit_id
      LEFT JOIN lead_status ls ON ls.business_id = b.id
      ${where}
      ORDER BY s.composite_score DESC
    `).all(...params) as Record<string, unknown>[];

    const lines = [
      FIELDS.join(","),
      ...rows.map((r) => FIELDS.map((f) => escapeCsv(r[f])).join(",")),
    ];

    return new Response(lines.join("\r\n"), {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="leads-${new Date().toISOString().slice(0, 10)}.csv"`,
      },
    });
  } catch (err) {
    console.error("GET /api/leads/export.csv error:", err);
    return new Response("Database error", { status: 500 });
  }
}
