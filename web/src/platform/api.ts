/**
 * Typed client for the matching engine.
 *
 * Every field here is computed server-side by the engine. There is no scoring,
 * ranking or explanation logic on this side of the wire, which is what makes
 * "no mocked AI responses" enforceable rather than a claim.
 */

const BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

export type Verdict = 'AGREE' | 'DISAGREE' | 'UNKNOWN'
export type Decision = 'MATCH' | 'NEAR_MATCH' | 'REVIEW_REQUIRED' | 'DISTINCT'

export type EvidenceRow = {
  attribute: string
  code: string
  criticality: 'CRITICAL' | 'IMPORTANT' | 'MINOR' | 'INFORMATIONAL'
  source: string
  candidate: string
  verdict: Verdict
  detail: string
  vetoed: boolean
}

export type Candidate = {
  source_material: string
  candidate_material: string
  candidate_id: string
  record_id: string
  org: string
  org_code: string
  provenance: string
  decision: Decision
  confidence: number
  /** Uncalibrated ranking score. The API says so explicitly; never relabel it. */
  calibrated: false
  semantic_score: number
  lexical_score: number
  attribute_agreement: number
  critical_veto: boolean
  veto_reason: string
  counts: { agree: number; disagree: number; unknown: number }
  evidence: EvidenceRow[]
  model_version: string
}

export type ExtractedAttribute = {
  code: string
  value: string
  source: string
  raw: string
  inferred_unit: string | null
}

export type MatchResult = {
  query: string
  normalised: string
  item_name: string | null
  attributes: ExtractedAttribute[]
  candidates: Candidate[]
  elapsed_ms: number
  model_version: string
}

export type Health = {
  ready: boolean
  records: number
  dense_channel: boolean
  model_version: string
  index_build_ms: number
  corpus: string
  calibrated: boolean
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  health: () => get<Health>('/api/health'),
  samples: () => get<{ samples: string[]; corpus_size: number; organisations: string[] }>('/api/samples'),
  async match(description: string, topK = 6): Promise<MatchResult> {
    const r = await fetch(`${BASE}/api/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, top_k: topK }),
    })
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  },
}
