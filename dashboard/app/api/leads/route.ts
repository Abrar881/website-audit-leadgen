import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import type { LeadsResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1"));
  const pageSize = Math.min(100, Math.max(1, parseInt(searchParams.get("pageSize") ?? "25")));
  const offset = (page - 1) * pageSize;
  const trade = searchParams.get("trade");
  const minScore = parseFloat(searchParams.get("minScore") ?? "0");
  const maxScore = parseFloat(searchParams.get("maxScore") ?? "100");
  const postcode = searchParams.get("postcode");
  const status = searchParams.get("status");

  const conditions: string[] = [
    "s.composite_score >= ?",
    "s.composite_score <= ?",
  ];
  const params: (string | number)[] = [minScore, maxScore];

  if (trade) {
    conditions.push("b.trade_category = ?");
    params.push(trade);
  }
  if (postcode) {
    conditions.push("b.postcode LIKE ?");
    params.push(`${postcode.toUpperCase()}%`);
  }
  if (status) {
    conditions.push("COALESCE(ls.status, 'new') = ?");
    params.push(status);
  }

  const where = `WHERE ${conditions.join(" AND ")}`;

  try {
    const db = getDb();

    const total = (db.prepare(`
      SELECT COUNT(*) as count
      FROM businesses b
      JOIN scores s ON s.business_id = b.id
      LEFT JOIN lead_status ls ON ls.business_id = b.id
      ${where}
    `).get(...params) as { count: number }).count;

    const leads = db.prepare(`
      SELECT
        b.id, b.place_id, b.name, b.trade_category, b.address, b.postcode,
        b.phone, b.website, b.google_rating, b.review_count, b.business_status,
        s.composite_score, s.website_score, s.activity_score, s.budget_score, s.score_breakdown,
        a.psi_performance, a.psi_accessibility, a.lcp_ms, a.has_ssl,
        a.is_mobile_friendly, a.estimated_design_year, a.cms_name, a.broken_links,
        COALESCE(ls.status, 'new') as status
      FROM businesses b
      JOIN scores s ON s.business_id = b.id
      LEFT JOIN audits a ON a.id = s.audit_id
      LEFT JOIN lead_status ls ON ls.business_id = b.id
      ${where}
      ORDER BY s.composite_score DESC
      LIMIT ? OFFSET ?
    `).all(...params, pageSize, offset);

    return NextResponse.json<LeadsResponse>({
      leads: leads as any,
      total,
      page,
      pageSize,
    });
  } catch (err) {
    console.error("GET /api/leads error:", err);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
