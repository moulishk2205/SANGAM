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
  decision: Decision; confidence: number; calibrated: boolean; raw_score: number
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
  /** True when the engine has a fitted scorer loaded, so confidence is a probability. */
  calibrated: boolean
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

/**
 * The session is an httponly cookie, so every request has to opt in to sending
 * it. Without `credentials: 'include'` the browser omits the cookie on a
 * cross-origin request and every authenticated call fails as anonymous — with a
 * 401 that looks like a broken login rather than a missing flag.
 */
const CREDS: RequestInit = { credentials: 'include' }

/** The backend answers failures with a code and a sentence meant for a person. */
export class ApiError extends Error {
  // Declared explicitly rather than as constructor parameter properties: this
  // project builds with `erasableSyntaxOnly`, which forbids TS syntax that
  // emits runtime code.
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/**
 * Fired when the server says the session is gone.
 *
 * A session can end while a tab sits open — it expires, it is revoked, the
 * engine is restarted against a fresh database. The next call then 401s, and
 * without this the screen would render "Sign in to continue." as though it
 * were a data error, on a page whose nav still shows the signed-in user. The
 * event lets SessionProvider clear its user, which makes the route gate fire
 * and lands the person on the sign-in screen with their destination kept.
 *
 * A CustomEvent rather than an import: api.ts is imported *by* Session.tsx, so
 * calling into it directly would be a cycle.
 */
export const SESSION_LOST = 'sangam:session-lost'

async function unwrap<T>(r: Response): Promise<T> {
  if (r.ok) return r.json()
  let code = 'error'
  let message = `${r.status} ${r.statusText}`
  try {
    const body = await r.json()
    const d = body?.detail ?? body
    if (d?.code) code = d.code
    if (d?.message) message = d.message
  } catch { /* a non-JSON error body; the status line stands */ }

  // 401 means the session is gone, not that this particular request was bad.
  // `me` is exempt: it answers 200 with a null user when signed out, so a 401
  // from it would be something else entirely — and re-broadcasting during the
  // provider's own boot call would loop.
  if (r.status === 401 && !r.url.endsWith('/api/auth/me')) {
    window.dispatchEvent(new CustomEvent(SESSION_LOST))
  }

  throw new ApiError(r.status, code, message)
}

async function get<T>(path: string): Promise<T> {
  return unwrap<T>(await fetch(`${BASE}${path}`, CREDS))
}

async function send<T>(path: string, body: unknown, method = 'POST'): Promise<T> {
  return unwrap<T>(await fetch(`${BASE}${path}`, {
    ...CREDS,
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }))
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
    return send<MaterialMap>('/api/visualization', { description, top_k: topK })
  },
  async match(description: string, topK = 8): Promise<MatchResult> {
    return send<MatchResult>('/api/match', { description, top_k: topK })
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
  dense_channel: boolean; elapsed_ms: number; model_version: string; calibrated: boolean
}


/* ══════════════════════════════════════════════════════════════════════════
   Identity, the review queue, and the write path.
   ══════════════════════════════════════════════════════════════════════════ */

export type Role = 'REQUESTER' | 'REVIEWER' | 'STEWARD' | 'ADMIN'

export type CurrentUser = {
  id: string; email: string; name: string; role: Role
  org_id: string; org_name: string
  commodity_scope: string[]
  class_certifications: string[]
}

export type QueueItem = {
  mapping_id: string; record_id: string; org: string; org_code: string
  description: string; canonical_id: string; canonical_text: string
  item_name: string; item_class: string; family: string
  confidence: number; engine: string
  you_may_approve: boolean
}

export type MappingOut = {
  mapping_id: string; source_record_id: string; canonical_id: string
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED'
  confidence: number; effective_from: string; effective_to: string | null
}

export type DecisionRow = {
  id: string; seq: number; kind: string; mapping_id: string | null
  canonical_id: string | null; actor_id: string | null; actor_role: string
  actor_scope: Record<string, unknown>; note: string
  gazetteer_version: string; template_version: string; model_version: string
  hash: string; prev_hash: string; at: string
}

export type Certificate = DecisionRow & {
  actor: { id: string; name: string; role: string; scope_at_decision: Record<string, unknown> } | null
  evidence: Record<string, unknown>
  versions: { gazetteer: string; template: string; model: string }
  chain: { prev_hash: string; hash: string }
}

export type HistoryRow = {
  mapping_id: string; canonical_id: string; status: string
  from: string; to: string | null; superseded_by: string | null; engine: string
}

export const auth = {
  me: () => get<{ user: CurrentUser | null }>('/api/auth/me'),
  login: (email: string, password: string) =>
    send<{ user: CurrentUser; expires_at: string }>('/api/auth/login', { email, password }),
  logout: () => send<{ ok: boolean }>('/api/auth/logout', {}),
}

export const work = {
  queue: (limit = 25) => get<{
    queue: QueueItem[]; next_cursor: string | null
    scope: { org: string; commodity: string[] }
  }>(`/api/review/queue?limit=${limit}`),

  propose: (source_record_id: string, canonical_id: string,
            opts: { confidence?: number; engine_decision?: string; evidence?: unknown; note?: string } = {}) =>
    send<MappingOut>('/api/mappings/propose', { source_record_id, canonical_id, ...opts }),

  approve: (mappingId: string, note: string) =>
    send<MappingOut>(`/api/mappings/${mappingId}/approve`, { note }),
  reject: (mappingId: string, note: string) =>
    send<MappingOut>(`/api/mappings/${mappingId}/reject`, { note }),
  unmap: (recordId: string, note: string) =>
    send<MappingOut>(`/api/records/${recordId}/unmap`, { note }),
  remap: (recordId: string, canonical_id: string, note: string) =>
    send<MappingOut>(`/api/records/${recordId}/remap`, { canonical_id, note }),

  history: (recordId: string) =>
    get<{ record_id: string; history: HistoryRow[] }>(`/api/material/${recordId}/history`),
}

export const ledger = {
  decisions: (limit = 50) => get<{ decisions: DecisionRow[] }>(`/api/decisions?limit=${limit}`),
  certificate: (id: string) => get<Certificate>(`/api/decisions/${id}`),
  verify: () => get<{ ok: boolean; checked: number; head?: string; broken_at?: string; note: string }>(
    '/api/decisions/chain/verify'),
}
