import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import type { Stats } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const db = getDb();

    const counts = db.prepare(`
      SELECT
        (SELECT COUNT(*) FROM businesses) as total_businesses,
        (SELECT COUNT(*) FROM businesses WHERE website IS NOT NULL) as with_website,
        (SELECT COUNT(DISTINCT business_id) FROM audits) as audited,
        (SELECT COUNT(DISTINCT business_id) FROM scores) as scored,
        SUM(CASE WHEN composite_score >= 80 THEN 1 ELSE 0 END) as priority,
        SUM(CASE WHEN composite_score >= 60 AND composite_score < 80 THEN 1 ELSE 0 END) as strong,
        SUM(CASE WHEN composite_score >= 40 AND composite_score < 60 THEN 1 ELSE 0 END) as review,
        SUM(CASE WHEN composite_score < 40 THEN 1 ELSE 0 END) as skip
      FROM scores
    `).get() as any;

    const byTrade = db.prepare(`
      SELECT b.trade_category, COUNT(*) as count
      FROM businesses b
      JOIN scores s ON s.business_id = b.id
      GROUP BY b.trade_category
      ORDER BY count DESC
    `).all() as { trade_category: string; count: number }[];

    return NextResponse.json<Stats>({
      total_businesses: counts.total_businesses ?? 0,
      with_website: counts.with_website ?? 0,
      audited: counts.audited ?? 0,
      scored: counts.scored ?? 0,
      priority: counts.priority ?? 0,
      strong: counts.strong ?? 0,
      review: counts.review ?? 0,
      skip: counts.skip ?? 0,
      by_trade: byTrade,
    });
  } catch (err) {
    console.error("GET /api/stats error:", err);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
