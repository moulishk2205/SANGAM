/**
 * All page content in one place.
 *
 * Two rules govern everything here:
 *  1. Source records are SYNTHETIC and labelled as such in the UI. Organisation
 *     labels are functional (REF-SOUTH), never invented company names and never
 *     real CPSE names.
 *  2. Every measured figure comes from our own evaluation harness or from the
 *     public DLA FLIS catalogue, and carries a provenance note. Nothing here is
 *     invented to look impressive.
 */

export type SourceRecord = {
  id: string
  org: string
  code: string
  text: string
  /** px offset from the container's left edge. Five systems that never spoke
   *  to each other do not share a grid; the misalignment is the argument. */
  offset: number
  /** Slight optical size variation so the block never reads as a tidy list. */
  size: number
}

export const SOURCE_RECORDS: SourceRecord[] = [
  { id: 'r1', org: 'REF-SOUTH',    code: 'MM-4471',      text: 'SS HEX BOLT M10 X 50',                        offset: 12,  size: 13 },
  { id: 'r2', org: 'PIPELINE-DIV', code: '100238841',    text: 'STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM',  offset: 148, size: 13 },
  { id: 'r3', org: 'PETCHEM-WEST', code: 'B-HX-SS-1050', text: 'BOLT HEX SS M10*50',                          offset: 0,   size: 14 },
  { id: 'r4', org: 'TERMINAL-EAST',code: '55021907',     text: 'HEX BOLT, S/S, M10 X 50 MM (OLD SPEC)',       offset: 96,  size: 13 },
  { id: 'r5', org: 'REF-NORTH',    code: '4471-A',       text: 'BOLT,HEXAGON HEAD,STAINLESS,M10X50',          offset: 40,  size: 14 },
]

/** What each record normalises to. Same five records, house styles removed. */
export const NORMALISED: Record<string, string> = {
  r1: 'STAINLESS STEEL HEXAGONAL BOLT M10 X 50',
  r2: 'STAINLESS STEEL HEXAGONAL BOLT M10 X 50',
  r3: 'BOLT HEXAGONAL STAINLESS STEEL M10 X 50',
  r4: 'HEXAGONAL BOLT STAINLESS STEEL M10 X 50 MM',
  r5: 'BOLT HEXAGON HEAD STAINLESS M10 X 50',
}

export const CANONICAL = {
  nmc: 'NMC-00018426',
  attributes: [
    { label: 'TYPE',     value: 'BOLT, MACHINE' },
    { label: 'MATERIAL', value: 'STAINLESS STEEL' },
    { label: 'THREAD',   value: 'M10 · 10.0 mm' },
    { label: 'LENGTH',   value: '50.0 mm ± 0.5' },
  ],
}

/** Measured on the public DLA FLIS / PUB LOG catalogue, 2026-08-26. */
export const SCALE = {
  headline: { value: '1,824,354', label: 'items in the six commodity families we indexed' },
  supporting: [
    { value: '492,965',   label: 'NIINs carrying more than one manufacturer part number' },
    { value: '23,610',    label: 'recorded standardization decisions' },
    { value: '8,183,475', label: 'attribute assertions' },
  ],
  provenance: 'Measured from the public DLA FLIS / PUB LOG catalogue, a US federal FOIA release. Not CPSE data.',
}

/** Real output from our engine. Reproducible with scripts/evaluate.py. */
export const TRAP = {
  source:    { text: 'STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM', score: '0.960' },
  candidate: { text: 'SS HEX BOLT M10 X 75',                       score: '0.957' },
  delta: '0.003',
}

export type Verdict = 'agree' | 'disagree' | 'unknown'

export const EVIDENCE: {
  attribute: string
  source: string
  candidate: string
  verdict: Verdict
  detail?: string
  critical: boolean
}[] = [
  { attribute: 'Item type',        source: 'BOLT, MACHINE',   candidate: 'BOLT, MACHINE',   verdict: 'agree',    critical: true },
  { attribute: 'Material',         source: 'STAINLESS STEEL', candidate: 'STAINLESS STEEL', verdict: 'agree',    critical: true },
  { attribute: 'Thread diameter',  source: '10.0 mm',         candidate: '10.0 mm',         verdict: 'agree',    critical: true },
  { attribute: 'Length',           source: '50.0 mm',         candidate: '75.0 mm',         verdict: 'disagree', critical: true,
    detail: 'differs by 25.0 mm, tolerance 0.5 mm' },
]

export const PIPELINE = [
  { stage: 'Normalise',        note: 'house styles removed, abbreviations expanded' },
  { stage: 'Extract',          note: 'type · material · thread · length' },
  { stage: 'Retrieve',         note: 'lexical and dense channels, fused by reciprocal rank' },
  { stage: 'Compare',          note: 'agree · disagree · unknown, per attribute' },
  { stage: 'Veto',             note: 'a gate, not a weight' },
  { stage: 'Score',            note: '0.85 attribute agreement + 0.15 text' },
  { stage: 'Decide',           note: 'match · near · review · distinct' },
]

/** Measured by scripts/evaluate.py on the synthetic corpus. */
export const VALIDATION = {
  corpus: [
    { value: '1,800', label: 'evaluation records' },
    { value: '600',   label: 'canonical specifications' },
    { value: '300',   label: 'probe descriptions' },
  ],
  recall: { hybrid: 94.3, lexical: 79.7, gain: '+14.7' },
  veto: { total: '2,408', similar: '2,399' },
}

export const FUTURE = [
  'Canonical material identities across participating organisations',
  'Duplicate detection over existing material masters',
  'Check before create, at the point a new code would be minted',
  'Procurement normalisation and demand aggregation',
  'Supplier and specification comparison',
  'Cross-organisation harmonisation with local codes retained',
]
