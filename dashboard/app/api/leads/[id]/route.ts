import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/lib/db";
import type { LeadDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const businessId = parseInt(id);
  if (isNaN(businessId)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }

  try {
    const db = getDb();

    const lead = db.prepare(`
      SELECT
        b.id, b.place_id, b.name, b.trade_category, b.address, b.postcode,
        b.phone, b.website, b.google_rating, b.review_count, b.business_status,
        s.composite_score, s.website_score, s.activity_score, s.budget_score, s.score_breakdown,
        a.psi_performance, a.psi_accessibility, a.lcp_ms, a.has_ssl,
        a.is_mobile_friendly, a.estimated_design_year, a.cms_name, a.broken_links,
        a.raw_psi_json, a.tech_stack_json, a.audit_duration_s,
        COALESCE(ls.status, 'new') as status
      FROM businesses b
      JOIN scores s ON s.business_id = b.id
      LEFT JOIN audits a ON a.id = s.audit_id
      LEFT JOIN lead_status ls ON ls.business_id = b.id
      WHERE b.id = ?
    `).get(businessId);

    if (!lead) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    const notes = db.prepare(`
      SELECT id, note, created_at FROM lead_notes
      WHERE business_id = ? ORDER BY created_at DESC
    `).all(businessId);

    return NextResponse.json<LeadDetail>({ ...(lead as any), notes });
  } catch (err) {
    console.error(`GET /api/leads/${id} error:`, err);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const businessId = parseInt(id);
  if (isNaN(businessId)) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }

  const body = await req.json();
  const { status, note } = body;

  const VALID_STATUSES = ["new", "reviewed", "contacted", "qualified", "rejected"];

  try {
    // need write connection for PATCH
    const Database = (await import("better-sqlite3")).default;
    const path = (await import("path")).default;
    const dbPath = process.env.DB_PATH || path.join(process.cwd(), "..", "data", "leads.db");
    const writeDb = new Database(dbPath);
    writeDb.pragma("journal_mode = WAL");

    if (status) {
      if (!VALID_STATUSES.includes(status)) {
        return NextResponse.json({ error: "Invalid status" }, { status: 400 });
      }
      writeDb.prepare(`
        INSERT INTO lead_status (business_id, status, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(business_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at
      `).run(businessId, status);
    }

    if (note && typeof note === "string" && note.trim()) {
      writeDb.prepare(`
        INSERT INTO lead_notes (business_id, note, created_at)
        VALUES (?, ?, datetime('now'))
      `).run(businessId, note.trim());
    }

    writeDb.close();
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error(`PATCH /api/leads/${id} error:`, err);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
