import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import {
  ArrowRight, ArrowCounterClockwise, Prohibit, CheckCircle, Question,
  XCircle, Circle, Info, Warning,
} from '@phosphor-icons/react'
import {
  api, readableError,
  type MaterialMap, type MapNode, type Relation, type RejectionGroup, type EvidenceCell,
} from '../api'
import { Card, Button, SectionTitle, DemoNote, NmcTag, OrgChip } from '../components/ui'

/* ══════════════════════════════════════════════════════════════════════════
   04 — Visualization.

   THE ONE DECISION THIS SCREEN IS BUILT AROUND

   The obvious design is a network graph where distance means similarity. On
   this data that design is not merely imperfect, it is inverted. Measured on
   the live engine, for the query `SS HEX BOLT M10 X 50`:

       SS HEX BOLT M20X50                          text 0.9860   REJECTED
       STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM  text 0.9604   EQUIVALENT

   A wholly different bolt is more textually similar to the query than the
   correct duplicate is. Any layout that places nodes by similarity therefore
   draws the wrong material nearer than the right one, and a caption cannot
   revoke what a layout asserts. So similarity is not a position channel here.

   What is drawn instead: one vertical axis carrying the engine's score, with
   the real decision thresholds as horizontal rules, and a gate at the bottom.
   A vetoed candidate is drawn TWICE — a hollow ghost at the score it would
   have had if the veto were a weight, and a mark at the gate where it actually
   landed. The line between them is the length of the veto. That counterfactual
   is permanently on screen next to the real answer rather than behind a toggle,
   so there is no state of this screen that can be screenshotted misleadingly.

   Horizontal position is ordinal — candidates ordered by text corroboration,
   left to right. Ordinal because the real span is often narrower than 0.05, and
   stretching 0.05 across the full width would manufacture structure out of
   noise. The true span is printed underneath instead.
   ══════════════════════════════════════════════════════════════════════════ */

const COUNTS = [10, 20, 40] as const

const TONE: Record<Relation, { fg: string; soft: string; line: string }> = {
  EQUIVALENT: { fg: 'var(--color-brand)',    soft: 'var(--color-brand-soft)',    line: 'var(--color-brand-line)' },
  PROBABLE:   { fg: 'var(--color-info)',     soft: 'var(--color-info-soft)',     line: 'var(--color-info-line)' },
  REVIEW:     { fg: 'var(--color-unknown)',  soft: 'var(--color-unknown-soft)',  line: 'var(--color-unknown-line)' },
  SIMILAR:    { fg: 'var(--color-text-3)',   soft: 'var(--color-surface-3)',     line: 'var(--color-line-strong)' },
  // Red is reserved for exactly one meaning on this screen: a critical
  // attribute refused this pair. Nothing else is allowed to use it.
  REJECTED:   { fg: 'var(--color-distinct)', soft: 'var(--color-distinct-soft)', line: 'var(--color-distinct-line)' },
}

const RELATION_ORDER: Relation[] = ['EQUIVALENT', 'PROBABLE', 'REVIEW', 'SIMILAR', 'REJECTED']

/** Container width, measured. The SVG is drawn in real pixels rather than
 *  scaled through a viewBox, because a scaled viewBox shrinks the type with the
 *  chart and the axis labels stop being readable well before 380px. */
function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width))
    ro.observe(el)
    setW(el.getBoundingClientRect().width)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

/** The engine's own text term, returned by the API. Never recomputed here:
 *  a client cannot reproduce it exactly from values already rounded on the way out. */
const textOf = (n: MapNode) => n.text_score
const fmt = (v: number) => v.toFixed(4)

/* ────────────────────────────────────────────────────────────────────────
   The field
   ──────────────────────────────────────────────────────────────────────── */

type FieldProps = {
  map: MaterialMap
  nodes: MapNode[]
  selected: string | null
  onSelect: (id: string | null) => void
  reduced: boolean
}

function Field({ map, nodes, selected, onSelect, reduced }: FieldProps) {
  const [wrap, W] = useWidth<HTMLDivElement>()
  const [hover, setHover] = useState<MapNode | null>(null)

  const narrow = W > 0 && W < 560
  const H = narrow ? 400 : 468
  const PAD_L = narrow ? 44 : 56
  const PAD_R = 14
  const PAD_T = 22
  const GATE_H = narrow ? 30 : 34
  const AXIS_H = 30

  const fieldTop = PAD_T
  const fieldBot = H - AXIS_H - GATE_H - 14
  const gateTop = fieldBot + 14

  const y = useCallback(
    (s: number) => fieldBot - Math.max(0, Math.min(1, s)) * (fieldBot - fieldTop),
    [fieldBot, fieldTop],
  )

  // Ordinal x. Sorted once, by the real text corroboration, so the ordering is
  // information even though the spacing is not.
  const ordered = useMemo(
    () => [...nodes].sort((a, b) => textOf(a) - textOf(b)),
    [nodes],
  )
  const x = useCallback(
    (i: number) => {
      const inner = Math.max(W - PAD_L - PAD_R, 10)
      return PAD_L + ((i + 0.5) * inner) / Math.max(ordered.length, 1)
    },
    [W, PAD_L, ordered.length],
  )

  const gates = map.gates
  const gateX = useCallback(
    (code: string) => {
      const i = gates.findIndex((g) => g.code === code)
      const inner = Math.max(W - PAD_L - PAD_R, 10)
      const n = Math.max(gates.length, 1)
      return PAD_L + ((i < 0 ? 0 : i) + 0.5) * (inner / n)
    },
    [gates, W, PAD_L],
  )

  const span = useMemo(() => {
    if (!nodes.length) return null
    const vals = nodes.map(textOf)
    return { lo: Math.min(...vals), hi: Math.max(...vals) }
  }, [nodes])

  if (W === 0) return <div ref={wrap} className="h-[420px]" />

  const rules = [
    { s: map.thresholds.match, label: 'Match', tone: TONE.EQUIVALENT.fg },
    { s: map.thresholds.near, label: 'Near', tone: TONE.PROBABLE.fg },
    { s: map.thresholds.review, label: 'Review', tone: TONE.REVIEW.fg },
  ]

  return (
    <div ref={wrap} className="relative w-full">
      <p className="mono mb-1 text-[10px] uppercase tracking-[0.06em] text-[var(--color-text-3)]">
        ↑ score (see the note below on what this number is)
      </p>
      <svg
        width={W}
        height={H}
        role="img"
        aria-label={
          `Score field. ${nodes.length} candidates. ` +
          `${nodes.filter((n) => !n.vetoed).length} scored above zero, ` +
          `${nodes.filter((n) => n.vetoed).length} rejected at the critical attribute gate.`
        }
        style={{ display: 'block', overflow: 'visible' }}
      >
        {/* decision bands, faintest possible wash */}
        <rect x={PAD_L} y={y(1)} width={W - PAD_L - PAD_R} height={y(map.thresholds.match) - y(1)}
              fill="var(--color-brand-ambient)" />
        <rect x={PAD_L} y={y(map.thresholds.match)} width={W - PAD_L - PAD_R}
              height={y(map.thresholds.near) - y(map.thresholds.match)}
              fill="var(--color-info-soft)" opacity={0.45} />
        <rect x={PAD_L} y={y(map.thresholds.near)} width={W - PAD_L - PAD_R}
              height={y(map.thresholds.review) - y(map.thresholds.near)}
              fill="var(--color-unknown-soft)" opacity={0.4} />

        {/* the thresholds ARE the geometry: these are the engine's own constants */}
        {rules.map((r) => (
          <g key={r.label}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(r.s)} y2={y(r.s)}
                  stroke={r.tone} strokeWidth={1} strokeDasharray="3 3" opacity={0.6} />
            <text x={PAD_L - 8} y={y(r.s) + 3.5} textAnchor="end"
                  className="mono" fontSize={10.5} fill="var(--color-text-3)">
              {r.s.toFixed(2)}
            </text>
          </g>
        ))}
        <line x1={PAD_L} x2={W - PAD_R} y1={y(0)} y2={y(0)} stroke="var(--color-line-strong)" strokeWidth={1} />
        <text x={PAD_L - 8} y={y(1) + 3.5} textAnchor="end" className="mono"
              fontSize={10.5} fill="var(--color-text-3)">1.00</text>
        <text x={PAD_L - 8} y={y(0) + 3.5} textAnchor="end" className="mono"
              fontSize={10.5} fill="var(--color-text-3)">0.00</text>

        {/* ── vetoed candidates: ghost at the counterfactual, fall to the gate ── */}
        {ordered.map((n, i) => {
          if (!n.vetoed) return null
          const cx = x(i)
          const gy = y(n.raw_score)
          const gx = gateX(n.blockers[0]?.code ?? '')
          const on = selected === n.record_id || hover?.record_id === n.record_id
          return (
            <g
              key={`fall-${n.record_id}`}
              opacity={on ? 1 : 0.55}
              tabIndex={0}
              role="button"
              aria-label={
                `${n.description}. Rejected on specification. ` +
                `${n.blockers.map((b) => `${b.label}, ${b.source} versus ${b.candidate}`).join('; ')}. ` +
                `Would have scored ${fmt(n.raw_score)}; gated to zero. From ${n.org}.`
              }
              onFocus={() => setHover(n)}
              onBlur={() => setHover(null)}
              onMouseEnter={() => setHover(n)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect(selected === n.record_id ? null : n.record_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelect(selected === n.record_id ? null : n.record_id)
                }
              }}
              style={{ cursor: 'pointer', outline: 'none' }}
            >
              {/* generous invisible hit area: the ring itself is 11px across and
                  a fall line is barely a pixel, neither of which is a target */}
              <circle cx={cx} cy={gy} r={13} fill="transparent" />
              {on && <circle cx={cx} cy={gy} r={12} fill="var(--color-distinct-soft)" />}
              <motion.path
                d={`M ${cx} ${gy} L ${cx} ${gy + (gateTop - gy) * 0.55} L ${gx} ${gateTop}`}
                fill="none"
                stroke="var(--color-distinct)"
                strokeWidth={on ? 1.9 : 1.1}
                strokeLinejoin="round"
                initial={reduced ? false : { pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: 0.25 + i * 0.02, ease: [0.23, 1, 0.32, 1] }}
              />
              <circle cx={cx} cy={gy} r={5.5} fill="var(--color-bg)"
                      stroke="var(--color-distinct)" strokeWidth={1.2} strokeDasharray="2.5 2" />
            </g>
          )
        })}

        {/* ── the gate ─────────────────────────────────────────────────────── */}
        <rect x={PAD_L} y={gateTop} width={W - PAD_L - PAD_R} height={GATE_H}
              fill="var(--color-gate)" rx={3} />
        {gates.map((g, i) => {
          const inner = Math.max(W - PAD_L - PAD_R, 10)
          const cw = inner / Math.max(gates.length, 1)
          const gx = PAD_L + i * cw
          return (
            <g key={g.code}>
              {i > 0 && (
                <line x1={gx} x2={gx} y1={gateTop + 5} y2={gateTop + GATE_H - 5}
                      stroke="var(--color-gate-ink)" strokeOpacity={0.22} strokeWidth={1} />
              )}
              <text x={gx + cw / 2} y={gateTop + GATE_H / 2 - 2} textAnchor="middle"
                    className="mono" fontSize={narrow ? 8 : 9} fill="var(--color-gate-ink)" fillOpacity={0.72}
                    letterSpacing="0.04em">
                {(narrow ? g.label.split(' ')[0] : g.label).toUpperCase()}
              </text>
              <text x={gx + cw / 2} y={gateTop + GATE_H / 2 + 10} textAnchor="middle"
                    className="mono" fontSize={narrow ? 9 : 10.5}
                    fill={g.count ? 'var(--color-distinct)' : 'var(--color-gate-ink)'}
                    fillOpacity={g.count ? 1 : 0.4}>
                {g.count}{g.also > 0 ? ` +${g.also}` : ''}
              </text>
            </g>
          )
        })}

        {/* ── surviving candidates, at their real score ─────────────────────── */}
        {ordered.map((n, i) => {
          if (n.vetoed) return null
          const cx = x(i)
          const cy = y(n.confidence)
          const t = TONE[n.relation]
          const on = selected === n.record_id || hover?.record_id === n.record_id
          const gaps = n.unstated_critical.length
          return (
            <motion.g
              key={n.record_id}
              tabIndex={0}
              role="button"
              aria-label={
                `${n.description}. ${map.relations[n.relation].label}. ` +
                `Score ${fmt(n.confidence)} uncalibrated. ` +
                `${n.counts.agree} attributes agree, ${n.counts.disagree} disagree, ` +
                `${n.counts.unknown} not stated. From ${n.org}.`
              }
              onFocus={() => setHover(n)}
              onBlur={() => setHover(null)}
              onMouseEnter={() => setHover(n)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onSelect(selected === n.record_id ? null : n.record_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelect(selected === n.record_id ? null : n.record_id)
                }
              }}
              style={{ cursor: 'pointer', outline: 'none' }}
              initial={reduced ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.34, delay: i * 0.018, ease: [0.23, 1, 0.32, 1] }}
            >
              {on && <circle cx={cx} cy={cy} r={12} fill={t.soft} />}
              <circle
                cx={cx} cy={cy} r={n.relation === 'SIMILAR' ? 4.5 : 6}
                fill={n.relation === 'EQUIVALENT' ? t.fg : 'var(--color-surface)'}
                stroke={t.fg}
                strokeWidth={n.relation === 'EQUIVALENT' ? 0 : 1.8}
                strokeDasharray={n.relation === 'REVIEW' ? '3 2.4' : undefined}
              />
              {/* an unstated critical attribute is drawn as a literal hole, never
                  as a third colour: "not stated" is an absence, not a weak agree */}
              {gaps > 0 && <circle cx={cx} cy={cy} r={1.7} fill={t.fg} />}
            </motion.g>
          )
        })}

        {/* ── axis caption ─────────────────────────────────────────────────── */}
        <text x={PAD_L} y={H - 12} className="mono" fontSize={10}
              fill={map.evidence_stats.flat_field ? 'var(--color-unknown)' : 'var(--color-text-3)'}>
          {map.evidence_stats.flat_field
            ? `score cannot separate these — spread ${fmt(map.evidence_stats.score_spread)}`
            : `${ordered.length} candidates, ordered by text corroboration →`}
        </text>
        {span && !narrow && (
          <text x={W - PAD_R} y={H - 12} textAnchor="end" className="mono" fontSize={10}
                fill="var(--color-text-3)">
            span {fmt(span.lo)} – {fmt(span.hi)}
          </text>
        )}
      </svg>


      {/* ── hover card ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {hover && (
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.14 }}
            className="pointer-events-none absolute z-20 w-[262px] rounded-lg border p-3 shadow-lg"
            style={{
              background: 'var(--color-surface)',
              borderColor: TONE[hover.relation].line,
              left: Math.min(Math.max(x(ordered.indexOf(hover)) - 131, 0), Math.max(W - 262, 0)),
              top: (hover.vetoed ? y(hover.raw_score) : y(hover.confidence)) + 16,
            }}
          >
            <p className="text-[11px] font-semibold" style={{ color: TONE[hover.relation].fg }}>
              {map.relations[hover.relation].label}
            </p>
            <p className="mono mt-1 text-[12px] leading-snug text-[var(--color-text)]">
              {hover.description}
            </p>
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[11px]">
              <dt className="text-[var(--color-text-3)]">Item type</dt>
              <dd className="m-0 text-[var(--color-text-2)]">{hover.item_name}</dd>
              <dt className="text-[var(--color-text-3)]">Held by</dt>
              <dd className="m-0 mono text-[var(--color-text-2)]">{hover.org} · {hover.org_code}</dd>
              <dt className="text-[var(--color-text-3)]">Score</dt>
              <dd className="m-0 mono text-[var(--color-text-2)]">{fmt(hover.confidence)}</dd>
              <dt className="text-[var(--color-text-3)]">Text</dt>
              <dd className="m-0 mono text-[var(--color-text-2)]">{fmt(textOf(hover))}</dd>
              <dt className="text-[var(--color-text-3)]">Attributes</dt>
              <dd className="m-0 text-[var(--color-text-2)]">
                {hover.counts.agree} agree · {hover.counts.disagree} differ · {hover.counts.unknown} not stated
              </dd>
            </dl>
            {hover.vetoed && (
              <p className="mt-2 text-[11px] leading-snug" style={{ color: 'var(--color-distinct)' }}>
                {hover.veto_reason}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   Below the gate: rejections grouped by the value that caused them
   ──────────────────────────────────────────────────────────────────────── */

function Floor({ map, groups, onPick }: {
  map: MaterialMap; groups: RejectionGroup[]; onPick: (id: string) => void
}) {
  if (!groups.length) {
    return (
      <p className="mt-3 rounded-lg border border-dashed border-[var(--color-line-strong)]
                    px-4 py-6 text-center text-[13px] text-[var(--color-text-3)]">
        Nothing was rejected on this query. Every candidate retrieved cleared all
        {' '}{map.gates.length} critical attribute checks.
      </p>
    )
  }
  const byGate = map.gates.map((g) => ({
    gate: g,
    groups: groups.filter((r) => r.code === g.code),
  }))
  return (
    <div className="mt-3 grid gap-2"
         style={{ gridTemplateColumns: `repeat(${Math.max(map.gates.length, 1)}, minmax(0,1fr))` }}>
      {byGate.map(({ gate, groups: gs }) => (
        <div key={gate.code} className="min-w-0 grid gap-2 content-start">
          {gs.length === 0 ? (
            <p className="mono text-[10px] leading-tight text-[var(--color-text-3)] opacity-70 pt-1">
              stopped nobody
            </p>
          ) : gs.map((g) => (
            <button
              key={`${g.code}-${g.value}`}
              onClick={() => onPick(g.records[0].record_id)}
              className="press min-w-0 rounded-lg border px-2.5 py-2 text-left cursor-pointer"
              style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)' }}
            >
              <p className="mono text-[11px] font-semibold leading-tight truncate"
                 style={{ color: 'var(--color-distinct)' }}>
                {g.value}
              </p>
              <p className="text-[11px] text-[var(--color-text-2)] mt-0.5">
                {g.count} record{g.count > 1 ? 's' : ''}
              </p>
              {g.also_disagrees > 0 && (
                <p className="text-[10px] text-[var(--color-text-3)] mt-0.5 leading-tight">
                  {g.also_disagrees} also differ elsewhere
                </p>
              )}
            </button>
          ))}
        </div>
      ))}
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   Inspector
   ──────────────────────────────────────────────────────────────────────── */

function Row({ c, verdict }: { c: EvidenceCell; verdict: 'AGREE' | 'DISAGREE' | 'UNKNOWN' }) {
  const Icon = verdict === 'AGREE' ? CheckCircle : verdict === 'DISAGREE' ? XCircle : Question
  const fg = verdict === 'AGREE' ? 'var(--color-brand)'
    : verdict === 'DISAGREE' ? 'var(--color-distinct)' : 'var(--color-text-3)'
  return (
    <li className="flex items-start gap-2 py-1.5 border-b border-[var(--color-line)] last:border-0">
      <Icon size={13} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" style={{ color: fg }} />
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-medium text-[var(--color-text)]">
          {c.label}
          {c.criticality === 'CRITICAL' && (
            <span className="mono ml-1.5 text-[10px] uppercase tracking-wide text-[var(--color-text-3)]">
              critical
            </span>
          )}
        </p>
        <p className="mono text-[11px] text-[var(--color-text-2)] mt-0.5 break-words">
          {c.source} <span className="text-[var(--color-text-3)]">vs</span> {c.candidate}
        </p>
        {c.detail && <p className="text-[11px] text-[var(--color-text-3)] mt-0.5">{c.detail}</p>}
      </div>
    </li>
  )
}

function Inspector({ map, node }: { map: MaterialMap; node: MapNode }) {
  const t = TONE[node.relation]
  const a = node.arithmetic

  // Union of every attribute compared, for the side-by-side table. An attribute
  // neither side stated says so; it never gets an invented value.
  const table = useMemo(() => {
    const all = [
      ...node.agree.map((c) => ({ c, v: 'AGREE' as const })),
      ...node.disagree.map((c) => ({ c, v: 'DISAGREE' as const })),
      ...node.unknown.map((c) => ({ c, v: 'UNKNOWN' as const })),
    ]
    const rank = { CRITICAL: 0, IMPORTANT: 1, MINOR: 2, INFORMATIONAL: 3 }
    return all.sort((p, q) =>
      (rank[p.c.criticality] - rank[q.c.criticality]) || p.c.label.localeCompare(q.c.label))
  }, [node])

  return (
    <div className="grid gap-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
          Selected candidate
        </p>
        <p className="mono text-[13px] text-[var(--color-text)] mt-1.5 leading-snug">
          {node.description}
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          <span className="inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold"
                style={{ color: t.fg, background: t.soft, borderColor: t.line }}>
            {map.relations[node.relation].label}
          </span>
          <OrgChip org={node.org} />
          <span className="mono text-[11px] text-[var(--color-text-3)]">{node.org_code}</span>
          {node.nmc_id && <NmcTag id={node.nmc_id} size="sm" />}
        </div>
        <p className="text-[12px] leading-relaxed text-[var(--color-text-2)] mt-2">
          {map.relations[node.relation].meaning}
        </p>
      </div>

      {/* THE ARITHMETIC. The scoring rule as the numbers that produced it. For a
          vetoed pair the multiplication by zero is written out, because that is
          what makes "a gate, not a weight" a fact rather than a claim. */}
      <div className="rounded-lg border px-3 py-2.5"
           style={{ background: 'var(--color-surface-2)', borderColor: 'var(--color-line)' }}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1.5">
          How this score was produced
        </p>
        <p className="mono text-[12px] leading-relaxed text-[var(--color-text)] break-words">
          {a.w_attr} × {fmt(a.attr)} + {a.w_text} × {fmt(a.text)} = {fmt(a.raw)}
        </p>
        <p className="mono text-[12px] leading-relaxed break-words"
           style={{ color: node.vetoed ? 'var(--color-distinct)' : 'var(--color-text-2)' }}>
          {fmt(a.raw)} × veto {a.veto} = <strong>{fmt(a.final)}</strong>
        </p>
        <p className="text-[11px] text-[var(--color-text-3)] mt-1.5 leading-relaxed">
          {node.vetoed
            ? 'The veto is a multiplier of zero, not a penalty. No text similarity can recover this pair.'
            : 'Uncalibrated ranking score, not a probability.'}
        </p>
      </div>

      {node.vetoed && (
        <div className="flex items-start gap-2.5 rounded-lg border px-3 py-2.5"
             style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)',
                      color: 'var(--color-distinct)' }}>
          <Prohibit size={15} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-[12px] font-semibold">
              First critical failure: {node.blockers[0]?.label}
              {node.blockers.length > 1 && ` (+${node.blockers.length - 1} more)`}
            </p>
            <p className="text-[12px] mt-0.5 opacity-90">{node.veto_reason}</p>
          </div>
        </div>
      )}

      {node.disagree.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1">
            What differs
          </p>
          <ul className="list-none p-0 m-0">
            {node.disagree.map((c) => <Row key={c.code} c={c} verdict="DISAGREE" />)}
          </ul>
        </div>
      )}

      {node.agree.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1">
            What agrees
          </p>
          <ul className="list-none p-0 m-0">
            {node.agree.map((c) => <Row key={c.code} c={c} verdict="AGREE" />)}
          </ul>
        </div>
      )}

      {node.unknown.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1">
            Not stated
          </p>
          <ul className="list-none p-0 m-0">
            {node.unknown.map((c) => <Row key={c.code} c={c} verdict="UNKNOWN" />)}
          </ul>
          <p className="text-[11px] text-[var(--color-text-3)] mt-1.5 leading-relaxed">
            Silence is never read as agreement. Where a critical attribute is unstated the
            engine abstains rather than asserting identity.
          </p>
        </div>
      )}

      {/* side-by-side comparison */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1.5">
          Side by side
        </p>
        <div className="overflow-x-auto -mx-1 px-1">
          <table className="w-full min-w-[320px] border-collapse text-[12px]">
            <thead>
              <tr className="text-left text-[var(--color-text-3)]">
                <th className="font-medium pb-1.5 pr-3">Attribute</th>
                <th className="font-medium pb-1.5 pr-3">Reference</th>
                <th className="font-medium pb-1.5">Candidate</th>
              </tr>
            </thead>
            <tbody>
              {table.map(({ c, v }) => (
                <tr key={c.code} className="row border-t border-[var(--color-line)]"
                    style={{
                      background: v === 'AGREE' ? 'var(--color-agree-row)'
                        : v === 'DISAGREE' ? 'var(--color-disagree-row)'
                        : 'var(--color-neutral-ambient)',
                    }}>
                  <td className="py-1.5 pr-3 text-[var(--color-text)]">{c.label}</td>
                  <td className="mono py-1.5 pr-3 text-[var(--color-text-2)]">
                    {c.source === '—' ? <em className="not-italic text-[var(--color-text-3)]">Not available</em> : c.source}
                  </td>
                  <td className="mono py-1.5 text-[var(--color-text-2)]">
                    {c.candidate === '—' ? <em className="not-italic text-[var(--color-text-3)]">Not available</em> : c.candidate}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] leading-relaxed text-[var(--color-text-3)]">
        Retrieved by the {node.channels.join(' and ') || 'lexical'} channel.
        {' '}SANGAM decides identity, not substitutability. Nothing here is an approved alternative.
      </p>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────────────────── */

export function Visualize() {
  const [params, setParams] = useSearchParams()
  const initial = params.get('q') ?? 'STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM'

  const [q, setQ] = useState(initial)
  const [topK, setTopK] = useState<number>(20)
  const [map, setMap] = useState<MaterialMap | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [hidden, setHidden] = useState<Set<Relation>>(new Set())
  const [org, setOrg] = useState<string>('')
  const [minText, setMinText] = useState(0)
  const runId = useRef(0)

  const reduced = typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const run = useCallback(async (text: string, k: number) => {
    const id = ++runId.current
    setBusy(true); setErr(null); setSelected(null)
    try {
      const res = await api.materialMap(text, k)
      if (id !== runId.current) return
      setMap(res)
      setHidden(new Set())
      setOrg(''); setMinText(0)
    } catch (e) {
      if (id !== runId.current) return
      setErr(readableError(e)); setMap(null)
    } finally {
      if (id === runId.current) setBusy(false)
    }
  }, [])

  useEffect(() => { run(initial, 20) }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  const submit = (text: string, k = topK) => {
    const v = text.trim()
    if (!v) return
    setParams({ q: v }, { replace: true })
    run(v, k)
  }

  const visible = useMemo(() => {
    if (!map) return []
    return map.nodes.filter((n) =>
      !hidden.has(n.relation)
      && (!org || n.org === org)
      && n.text_score >= minText)
  }, [map, hidden, org, minText])

  const visibleGroups = useMemo(() => {
    if (!map) return []
    const ids = new Set(visible.map((n) => n.record_id))
    return map.rejection_groups
      .map((g) => ({ ...g, records: g.records.filter((r) => ids.has(r.record_id)) }))
      .filter((g) => g.records.length > 0)
      .map((g) => ({ ...g, count: g.records.length }))
  }, [map, visible])

  const node = useMemo(
    () => map?.nodes.find((n) => n.record_id === selected) ?? null,
    [map, selected],
  )

  const toggle = (r: Relation) => setHidden((prev) => {
    const next = new Set(prev)
    next.has(r) ? next.delete(r) : next.add(r)
    return next
  })

  const reset = () => { setHidden(new Set()); setOrg(''); setMinText(0); setSelected(null) }
  const filtered = hidden.size > 0 || !!org || minText > 0

  return (
    <div className="grid gap-6">
      {/* ── query ──────────────────────────────────────────────────────── */}
      <section aria-labelledby="viz-h">
        <h1 id="viz-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Where this material sits
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[68ch]">
          Every candidate the engine retrieved, placed by the score it was actually given.
          Position is never a claim about similarity — the horizontal axis is an ordering,
          and the vertical axis is the decision.
        </p>

        <Card className="mt-4 p-1.5" spotlight>
          <form onSubmit={(e) => { e.preventDefault(); submit(q) }}
                className="flex flex-col sm:flex-row gap-2">
            <label htmlFor="viz-q" className="sr-only">Material description</label>
            <input
              id="viz-q" value={q} onChange={(e) => setQ(e.target.value)}
              autoComplete="off" spellCheck={false}
              placeholder="Describe a material"
              className="mono flex-1 bg-transparent px-4 py-3 text-[14px] text-[var(--color-text)]
                         placeholder:text-[var(--color-text-3)] outline-none rounded-lg"
            />
            <Button type="submit" disabled={!q.trim() || busy}
                    icon={<ArrowRight size={15} weight="bold" />}>
              {busy ? 'Mapping…' : 'Map material'}
            </Button>
          </form>
        </Card>
      </section>

      {err && (
        <Card className="p-5" >
          <div className="flex items-start gap-3">
            <Warning size={18} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0"
                     style={{ color: 'var(--color-distinct)' }} />
            <div>
              <p className="text-[14px] font-semibold text-[var(--color-text)]">SANGAM engine unavailable</p>
              <p className="text-[13px] text-[var(--color-text-2)] mt-1 max-w-[62ch]">{err}</p>
              <p className="text-[12px] text-[var(--color-text-3)] mt-2">
                No graph is shown rather than a placeholder one. Nothing on this screen is
                drawn without the engine.
              </p>
              <div className="mt-3"><Button variant="ghost" onClick={() => submit(q)}>Try again</Button></div>
            </div>
          </div>
        </Card>
      )}

      {busy && !map && (
        <Card className="p-8">
          <div className="flex items-center gap-3">
            <span className="stage-pulse" aria-hidden="true" />
            <p className="text-[14px] text-[var(--color-text-2)]">
              Building material relationship map…
            </p>
          </div>
        </Card>
      )}

      {map && (
        <>
          {/* ── reference ───────────────────────────────────────────────── */}
          <Card className="p-4" spotlight>
            <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                Reference material
              </p>
              <p className="mono text-[11px] text-[var(--color-text-3)]">
                {map.item_name ?? 'unclassified'} · {map.elapsed_ms.toFixed(1)} ms
              </p>
            </div>
            <p className="mono text-[14px] text-[var(--color-text)] mt-1.5">{map.normalised}</p>
            <div className="flex flex-wrap gap-x-5 gap-y-1.5 mt-3">
              {map.reference.attributes.map((a) => (
                <span key={a.code} className="text-[12px]">
                  <span className="text-[var(--color-text-3)]">{a.label}</span>{' '}
                  <span className="mono font-medium text-[var(--color-text)]">{a.value}</span>
                  {a.critical && (
                    <span className="mono ml-1 text-[10px] uppercase tracking-wide"
                          style={{ color: 'var(--color-brand)' }}>crit</span>
                  )}
                </span>
              ))}
            </div>
            {map.reference.unstated_critical.length > 0 && (
              <p className="text-[12px] text-[var(--color-text-2)] mt-2.5 flex items-start gap-1.5">
                <Info size={13} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0"
                      style={{ color: 'var(--color-unknown)' }} />
                Your description does not state{' '}
                <strong className="font-medium">
                  {map.reference.unstated_critical.map((c) =>
                    map.gates.find((g) => g.code === c)?.label ?? c).join(', ')}
                </strong>. Until it does, the engine cannot assert identity — only shortlist.
              </p>
            )}
          </Card>

          {/* ── controls ────────────────────────────────────────────────── */}
          <section aria-labelledby="viz-controls">
            <SectionTitle hint={filtered ? `${visible.length} of ${map.nodes.length} shown` : undefined}>
              <span id="viz-controls">Filters</span>
            </SectionTitle>
            <Card className="p-3">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-[12px] text-[var(--color-text-3)]">Candidates</span>
                  <div className="flex rounded-lg border border-[var(--color-line)] overflow-hidden">
                    {COUNTS.map((c) => (
                      <button key={c} onClick={() => { setTopK(c); submit(q, c) }}
                        aria-pressed={topK === c}
                        className="press mono px-2.5 py-1 text-[12px] cursor-pointer border-r
                                   border-[var(--color-line)] last:border-r-0"
                        style={topK === c
                          ? { background: 'var(--color-brand)', color: 'var(--color-on-brand)' }
                          : { background: 'var(--color-surface)', color: 'var(--color-text-2)' }}>
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-[12px] text-[var(--color-text-3)]">Show</span>
                  {RELATION_ORDER.filter((r) => map.nodes.some((n) => n.relation === r)).map((r) => {
                    const on = !hidden.has(r)
                    const t = TONE[r]
                    const n = map.nodes.filter((x) => x.relation === r).length
                    return (
                      <button key={r} onClick={() => toggle(r)} aria-pressed={on}
                        className="press inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
                                   text-[11px] font-medium cursor-pointer"
                        style={on
                          ? { color: t.fg, background: t.soft, borderColor: t.line }
                          : { color: 'var(--color-text-3)', background: 'transparent',
                              borderColor: 'var(--color-line)', opacity: 0.65 }}>
                        {on ? <CheckCircle size={11} weight="fill" aria-hidden="true" />
                            : <Circle size={11} aria-hidden="true" />}
                        {map.relations[r].label} <span className="mono">{n}</span>
                      </button>
                    )
                  })}
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="viz-org" className="text-[12px] text-[var(--color-text-3)]">Organisation</label>
                  <select id="viz-org" value={org} onChange={(e) => setOrg(e.target.value)}
                    className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface)]
                               px-2 py-1 text-[12px] text-[var(--color-text)] cursor-pointer">
                    <option value="">All</option>
                    {map.facets.org.map((o) => (
                      <option key={o.value} value={o.value}>{o.value} ({o.count})</option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="viz-sim" className="text-[12px] text-[var(--color-text-3)]">
                    Text ≥ <span className="mono">{minText.toFixed(2)}</span>
                  </label>
                  <input id="viz-sim" type="range" min={0} max={0.99} step={0.01} value={minText}
                         onChange={(e) => setMinText(Number(e.target.value))}
                         className="w-28 cursor-pointer" />
                </div>

                {filtered && (
                  <Button variant="quiet" onClick={reset}
                          icon={<ArrowCounterClockwise size={13} weight="bold" />}>
                    Reset
                  </Button>
                )}
              </div>
            </Card>
          </section>

          {/* ── field + inspector ───────────────────────────────────────── */}
          <div className="grid lg:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)] gap-5 items-start">
            <div className="min-w-0 grid gap-3">
              <Card className="p-4 min-w-0">
                {visible.length === 0 ? (
                  <div className="py-14 text-center">
                    <p className="text-[14px] font-semibold text-[var(--color-text)]">
                      No comparable materials found
                    </p>
                    <p className="text-[13px] text-[var(--color-text-2)] mt-1.5 max-w-[46ch] mx-auto">
                      {map.nodes.length === 0
                        ? 'The engine retrieved nothing for this description. Try a broader material description.'
                        : 'Every candidate is hidden by the current filters. Nothing is invented to fill the space.'}
                    </p>
                    {filtered && <div className="mt-4 inline-block"><Button variant="ghost" onClick={reset}>Clear filters</Button></div>}
                  </div>
                ) : (
                  <>
                    <Field map={map} nodes={visible} selected={selected}
                           onSelect={setSelected} reduced={!!reduced} />
                    <div className="mt-3 border-t border-[var(--color-line)] pt-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                        Rejected below the gate
                      </p>
                      <Floor map={map} groups={visibleGroups} onPick={setSelected} />
                    </div>
                  </>
                )}
              </Card>

              {/* legend */}
              <Card className="p-3.5">
                <div className="flex flex-wrap gap-x-5 gap-y-2">
                  {RELATION_ORDER.map((r) => (
                    <span key={r} className="inline-flex items-center gap-2 text-[11px]">
                      <svg width={16} height={16} aria-hidden="true" className="shrink-0">
                        {r === 'REJECTED'
                          ? <circle cx={8} cy={8} r={5.5} fill="none" stroke={TONE[r].fg}
                                    strokeWidth={1.2} strokeDasharray="2.5 2" />
                          : <circle cx={8} cy={8} r={r === 'SIMILAR' ? 4.5 : 6}
                                    fill={r === 'EQUIVALENT' ? TONE[r].fg : 'var(--color-surface)'}
                                    stroke={TONE[r].fg}
                                    strokeWidth={r === 'EQUIVALENT' ? 0 : 1.8}
                                    strokeDasharray={r === 'REVIEW' ? '3 2.4' : undefined} />}
                      </svg>
                      <span className="text-[var(--color-text-2)]">{map.relations[r].label}</span>
                    </span>
                  ))}
                </div>
                <p className="text-[11px] leading-relaxed text-[var(--color-text-3)] mt-2.5">
                  A rejected candidate is drawn as a hollow ring at the score it would have
                  had if the veto were a weight, with a line falling to the attribute that
                  stopped it. The gap between ring and gate is the veto, at scale.
                </p>
              </Card>
            </div>

            {/* inspector */}
            <div className="min-w-0 lg:sticky lg:top-6">
              <Card className="p-4 min-w-0">
                {node ? (
                  <Inspector map={map} node={node} />
                ) : (
                  <div className="py-8 text-center">
                    <p className="text-[13px] font-medium text-[var(--color-text)]">
                      Select a candidate
                    </p>
                    <p className="text-[12px] text-[var(--color-text-2)] mt-1.5 max-w-[36ch] mx-auto leading-relaxed">
                      Click any mark in the field, or a rejection below the gate, to see every
                      attribute that was compared and the arithmetic that produced its score.
                    </p>
                  </div>
                )}
              </Card>
            </div>
          </div>

          {/* ── the measurement that justifies the layout ───────────────── */}
          <section aria-labelledby="viz-evidence">
            <SectionTitle><span id="viz-evidence">Why position is not similarity</span></SectionTitle>
            <div className="grid md:grid-cols-2 gap-3">
              <Card className="p-4">
                <p className="text-[13px] leading-relaxed text-[var(--color-text-2)]">
                  Measured on this result set, not stored:
                </p>
                <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5 mt-2.5 text-[12px]">
                  <dt className="text-[var(--color-text-2)]">Lowest text similarity among accepted</dt>
                  <dd className="m-0 mono text-[var(--color-text)]">
                    {fmt(map.evidence_stats.threshold_floor)}
                  </dd>
                  <dt className="text-[var(--color-text-2)]">Highest text similarity among rejected</dt>
                  <dd className="m-0 mono" style={{ color: 'var(--color-distinct)' }}>
                    {fmt(map.evidence_stats.veto_ceiling)}
                  </dd>
                </dl>
                {map.evidence_stats.inversions > 0 ? (
                  <>
                    <p className="text-[13px] leading-relaxed text-[var(--color-text)] mt-3 font-medium">
                      Any text-similarity threshold that admits the correct material also admits{' '}
                      <span style={{ color: 'var(--color-distinct)' }}>
                        {map.evidence_stats.inversions} different material
                        {map.evidence_stats.inversions > 1 ? 's' : ''}
                      </span>.
                    </p>
                    <ul className="list-none p-0 m-0 mt-2 grid gap-1">
                      {map.evidence_stats.inversion_examples.map((x) => (
                        <li key={x.description} className="text-[11px] leading-snug">
                          <span className="mono text-[var(--color-text-2)]">{fmt(x.text)}</span>{' '}
                          <span className="mono text-[var(--color-text)]">{x.description}</span>{' '}
                          <span className="text-[var(--color-text-3)]">— differs on {x.blockers.join(', ')}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="text-[13px] leading-relaxed text-[var(--color-text-2)] mt-3">
                    On this particular query no rejected candidate outranks an accepted one on
                    text alone. That is a property of this result set, not a guarantee.
                  </p>
                )}
                <p className="text-[11px] text-[var(--color-text-3)] mt-3 leading-relaxed">
                  Stated against SANGAM&rsquo;s own verdict, not against ground truth. The engine
                  is not entitled to grade itself and report the grade as fact.
                </p>
              </Card>

              <Card className="p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                  Embedding projection audit
                </p>
                <p className="text-[13px] leading-relaxed text-[var(--color-text-2)] mt-1.5">
                  A two-dimensional projection of this neighbourhood was computed and measured,
                  then deliberately not drawn.
                </p>
                <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5 mt-2.5 text-[12px]">
                  <dt className="text-[var(--color-text-2)]">Variance retained by two axes</dt>
                  <dd className="m-0 mono text-[var(--color-text)]">
                    {(map.projection.fidelity * 100).toFixed(1)}%
                  </dd>
                  <dt className="text-[var(--color-text-2)]">Distance-order fidelity (Spearman)</dt>
                  <dd className="m-0 mono text-[var(--color-text)]">
                    {map.projection.rank_fidelity.toFixed(3)}
                  </dd>
                </dl>
                <p className="mono text-[12px] mt-3 font-semibold"
                   style={{
                     color: map.projection.verdict === 'USABLE' ? 'var(--color-brand)'
                       : map.projection.verdict === 'WEAK' ? 'var(--color-unknown)'
                       : 'var(--color-distinct)',
                   }}>
                  {map.projection.verdict}
                </p>
                <p className="text-[12px] leading-relaxed text-[var(--color-text-2)] mt-1">
                  {map.projection.note}
                </p>
                <p className="text-[11px] text-[var(--color-text-3)] mt-3 leading-relaxed">
                  {map.projection.method}. Recomputed for every query, and reported whether or
                  not it flatters the result.
                </p>
              </Card>
            </div>
          </section>

          <DemoNote>
            Demonstration corpus of {map.nodes.length ? '1,800' : '0'} synthetic source records
            across 4 invented organisations. Organisation names and material codes are not the
            records of any real enterprise. Scores come from the engine's fitted scorer, not
            probabilities. SANGAM decides identity, not substitutability — nothing on this
            screen is an approved alternative.
          </DemoNote>
        </>
      )}
    </div>
  )
}
