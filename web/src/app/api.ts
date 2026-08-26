/**
 * Client for the matching engine.
 *
 * Nothing here scores, ranks or explains. Every number this returns was
 * computed server-side by MatchingEngine, which is what makes "no mocked AI"
 * enforceable instead of merely claimed.
 */
const BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

export type Verdict = 'AGREE' | 'DISAGREE' | 'UNKNOWN'
export type Decision = 'MATCH' | 'NEAR_MATCH' | 'REVIEW_REQUIRED' | 'DISTINCT'

export type EvidenceRow = {
  attribute: string; code: string
  criticality: 'CRITICAL' | 'IMPORTANT' | 'MINOR' | 'INFORMATIONAL'
  source: string; candidate: string
  verdict: Verdict; detail: string; vetoed: boolean
}

export type Candidate = {
  candidate_material: string; record_id: string; nmc_id: string | null
  org: string; org_code: string; provenance: string
  decision: Decision; confidence: number; calibrated: false
  semantic_score: number; lexical_score: number; attribute_agreement: number
  critical_veto: boolean; veto_reason: string
  counts: { agree: number; disagree: number; unknown: number }
  evidence: EvidenceRow[]
}

export type ExtractedAttribute = {
  code: string; value: string; source: string; raw: string; inferred_unit: string | null
}

export type MatchResult = {
  query: string; normalised: string; item_name: string | null
  attributes: ExtractedAttribute[]; candidates: Candidate[]
  elapsed_ms: number; model_version: string
}

export type CanonicalSummary = {
  nmc_id: string; item_name: string; canonical_text: string
  attributes: { code: string; label: string; value: string }[]
  source_count: number; org_count: number; orgs: string[]
}

export type CanonicalDetail = Omit<CanonicalSummary, 'orgs'> & {
  sources: { record_id: string; org: string; org_code: string; description: string; provenance: string }[]
}

export type Stats = {
  source_records: number; canonical_materials: number
  cross_org_materials: number; organisations: number; collapse_ratio: number
}

export type Health = {
  ready: boolean; records: number; dense_channel: boolean
  model_version: string; index_build_ms: number; corpus: string; calibrated: boolean
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  health: () => get<Health>('/api/health'),
  stats: () => get<Stats>('/api/stats'),
  samples: () => get<{ samples: string[]; organisations: string[] }>('/api/samples'),
  canonicalList: (q = '', limit = 40) =>
    get<{ total: number; matched: number; results: CanonicalSummary[] }>(
      `/api/canonical?q=${encodeURIComponent(q)}&limit=${limit}`),
  canonical: (id: string) => get<CanonicalDetail>(`/api/canonical/${encodeURIComponent(id)}`),
  async match(description: string, topK = 8): Promise<MatchResult> {
    const r = await fetch(`${BASE}/api/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, top_k: topK }),
    })
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  },
}

/** Friendlier message than "Failed to fetch" when the engine is not running. */
export function readableError(e: unknown): string {
  const m = e instanceof Error ? e.message : String(e)
  return m.includes('Failed to fetch') || m.includes('NetworkError')
    ? 'Cannot reach the analysis engine. Start it with: uvicorn src.nmc.api:app --port 8000'
    : m
}
