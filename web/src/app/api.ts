/**
 * Client for the matching engine.
 *
 * Nothing here scores, ranks or explains. Every number this returns was
 * computed server-side by MatchingEngine, which is what makes "no mocked AI"
 * enforceable instead of merely claimed.
 */
const BASE = import.meta.env.DEV ? 'http://localhost:8001' : ''

export type Verdict = 'AGREE' | 'DISAGREE' | 'UNKNOWN'
export type Decision = 'MATCH' | 'NEAR_MATCH' | 'REVIEW_REQUIRED' | 'DISTINCT'

export type EvidenceRow = {
  attribute: string; code: string
  criticality: 'CRITICAL' | 'IMPORTANT' | 'MINOR' | 'INFORMATIONAL'
  source: string; candidate: string
  verdict: Verdict; detail: string; vetoed: boolean
}

export type Arithmetic = {
  w_attr: number; attr: number; w_text: number; text: number
  raw: number; veto: 0 | 1; final: number
}

export type Candidate = {
  candidate_material: string; record_id: string; nmc_id: string | null
  org: string; org_code: string; provenance: string
  decision: Decision; confidence: number; calibrated: false; raw_score: number
  arithmetic: Arithmetic
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
  samples: () => get<{
    samples: string[]
    examples: { chip: string; query: string; note: string; item_name: string }[]
    corpus_size: number
    organisations: string[]
  }>('/api/samples'),
  canonicalList: (q = '', limit = 40) =>
    get<{ total: number; matched: number; results: CanonicalSummary[] }>(
      `/api/canonical?q=${encodeURIComponent(q)}&limit=${limit}`),
  canonical: (id: string) => get<CanonicalDetail>(`/api/canonical/${encodeURIComponent(id)}`),
  async materialMap(description: string, topK = 20): Promise<MaterialMap> {
    const r = await fetch(`${BASE}/api/visualization`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, top_k: topK }),
    })
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  },
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
/**
 * Friendlier message than the browser's own when the engine is not running.
 *
 * Every engine browser words this differently, and matching only Chrome's
 * phrasing meant Safari and the WebKit-based preview showed a bare "Load
 * failed" — which tells the reader nothing and looks like the app is broken
 * rather than like a service is down.
 */
const OFFLINE = [
  'Failed to fetch',      // Chrome, Edge
  'NetworkError',         // Firefox
  'Load failed',          // Safari / WebKit
  'network error',        // some WebKit builds, lowercased
  'ERR_CONNECTION',       // Chromium surfacing the net error directly
  'Could not connect',
]

export function readableError(e: unknown): string {
  const m = e instanceof Error ? e.message : String(e)
  const offline = OFFLINE.some((s) => m.toLowerCase().includes(s.toLowerCase()))
  return offline
    ? 'Cannot reach the SANGAM engine. Start it from the repository root with: '
      + 'python -m uvicorn src.nmc.api:app --port 8001'
    : m
}


/* ══════════════════════════════════════════════════════════════════════════
   Visualization — the relationship map.

   Same engine, same call. `/api/visualization` runs `check_before_create`, the
   entry point the Analyse screen uses, so the two screens cannot disagree about
   a candidate.
   ══════════════════════════════════════════════════════════════════════════ */

export type Relation = 'EQUIVALENT' | 'PROBABLE' | 'REVIEW' | 'SIMILAR' | 'REJECTED'

export type EvidenceCell = {
  code: string; label: string; source: string; candidate: string
  criticality: 'CRITICAL' | 'IMPORTANT' | 'MINOR' | 'INFORMATIONAL'
  detail: string
}

export type Blocker = { code: string; label: string; source: string; candidate: string; detail: string }

export type MapNode = {
  record_id: string; nmc_id: string | null
  description: string; normalised: string
  org: string; org_code: string; provenance: string
  item_name: string; family: string
  decision: Decision; relation: Relation
  confidence: number; raw_score: number
  semantic_score: number; lexical_score: number; attribute_agreement: number
  text_score: number
  vetoed: boolean; veto_reason: string
  blockers: Blocker[]; unstated_critical: string[]
  counts: { agree: number; disagree: number; unknown: number }
  agree: EvidenceCell[]; disagree: EvidenceCell[]; unknown: EvidenceCell[]
  arithmetic: Arithmetic
  channels: string[]
  px?: number; py?: number; cx?: number; cy?: number
}

export type RejectionGroup = {
  code: string; label: string; value: string; source_value: string; detail: string
  count: number; also_disagrees: number
  records: { record_id: string; description: string; org: string; org_code: string; text: number }[]
}

export type MaterialMap = {
  query: string; normalised: string; item_name: string | null; family: string
  reference: {
    attributes: { code: string; label: string; value: string; critical: boolean
                  source: string; inferred_unit: string | null }[]
    critical_codes: string[]; unstated_critical: string[]; xy: [number, number]
  }
  nodes: MapNode[]
  catalogue: { record_id: string; item_name: string; family: string; cx: number; cy: number }[]
  evidence_stats: {
    accepted: number; rejected: number
    threshold_floor: number; veto_ceiling: number; inversions: number
    score_spread: number; flat_field: boolean
    inversion_examples: { description: string; text: number; blockers: string[] }[]
    closest_accepted: { description: string; text: number } | null
  }
  gates: { code: string; label: string; count: number; also: number; stated_by_query: boolean }[]
  rejection_groups: RejectionGroup[]
  refine: { code: string; label: string; values: { value: string; count: number }[] }[]
  projection: {
    method: string; available: boolean; fidelity: number; rank_fidelity: number
    verdict: string; note: string; catalogue_fidelity: number; catalogue_size: number
    reference_cxy?: [number, number]
  }
  facets: Record<'family' | 'item_name' | 'org' | 'relation', { value: string; count: number }[]>
  relations: Record<Relation, { label: string; meaning: string; tone: string }>
  thresholds: { match: number; near: number; review: number }
  dense_channel: boolean; elapsed_ms: number; model_version: string; calibrated: false
}
