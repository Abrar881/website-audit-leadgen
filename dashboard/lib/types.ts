export interface Lead {
  id: number;
  place_id: string;
  name: string;
  trade_category: string;
  address: string | null;
  postcode: string | null;
  phone: string | null;
  website: string | null;
  google_rating: number | null;
  review_count: number;
  business_status: string;
  // scores
  composite_score: number;
  website_score: number;
  activity_score: number;
  budget_score: number;
  score_breakdown: string | null;
  // audit
  psi_performance: number | null;
  psi_accessibility: number | null;
  lcp_ms: number | null;
  has_ssl: number | null;
  is_mobile_friendly: number | null;
  estimated_design_year: number | null;
  cms_name: string | null;
  broken_links: number | null;
  // lead management
  status: string | null;
}

export interface LeadDetail extends Lead {
  raw_psi_json: string | null;
  tech_stack_json: string | null;
  audit_duration_s: number | null;
  notes: { id: number; note: string; created_at: string }[];
}

export interface Stats {
  total_businesses: number;
  with_website: number;
  audited: number;
  scored: number;
  priority: number;
  strong: number;
  review: number;
  skip: number;
  by_trade: { trade_category: string; count: number }[];
}

export interface LeadsResponse {
  leads: Lead[];
  total: number;
  page: number;
  pageSize: number;
}
