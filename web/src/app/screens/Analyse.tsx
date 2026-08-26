import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { ArrowRight, ArrowClockwise, CheckCircle, Lightning, ArrowSquareOut } from '@phosphor-icons/react'
import { api, readableError, type MatchResult, type Candidate } from '../api'
import {
  Card, Button, SectionTitle, DecisionBadge, VerdictMark, NmcTag, OrgChip, VetoNotice, DemoNote,
} from '../components/ui'

/**
 * 02 + 03 + 04 — Check, Analysis and Match Results.
 *
 * These are one route rather than three because the analysis genuinely
 * completes in milliseconds. Routing a user to a dedicated "processing" page
 * for something that has already finished would mean inventing latency, and an
 * invented loading state is the fastest way to make a real engine look fake.
 * The pipeline is shown as a completed record with a replay control instead.
 */

const STAGES = [
  { key: 'input',      label: 'Input received' },
  { key: 'extract',    label: 'Attribute extraction' },
  { key: 'normalise',  label: 'Normalization' },
  { key: 'retrieve',   label: 'Hybrid retrieval' },
  { key: 'compare',    label: 'Critical attribute check' },
  { key: 'veto',       label: 'Veto evaluation' },
  { key: 'decide',     label: 'Decision' },
] as const

export function Analyse() {
  const [params, setParams] = useSearchParams()
  const initial = params.get('q') ?? ''
  const [q, setQ] = useState(initial)
  const [res, setRes] = useState<MatchResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [sel, setSel] = useState(0)
  const [replay, setReplay] = useState(-1)

  const run = useCallback(async (text: string) => {
    if (!text.trim()) return
    setBusy(true); setErr(null); setReplay(-1)
    try {
      const r = await api.match(text, 8)
      setRes(r); setSel(0)
    } catch (e) {
      setErr(readableError(e)); setRes(null)
    } finally { setBusy(false) }
  }, [])

  useEffect(() => { if (initial) void run(initial) }, [initial, run])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setParams({ q })
    void run(q)
  }

  /** Replays the stages that actually ran. Explicitly labelled as a replay so
   *  nobody mistakes it for live computation. */
  const doReplay = () => {
    setReplay(0)
    STAGES.forEach((_, i) => setTimeout(() => setReplay(i + 1), (i + 1) * 380))
  }

  const active: Candidate | undefined = res?.candidates[sel]
  const matches = res?.candidates.filter((c) => !c.critical_veto).length ?? 0
  const vetoed = res?.candidates.filter((c) => c.critical_veto).length ?? 0

  return (
    <div className="grid gap-7">
      {/* ── 02 Input ───────────────────────────────────────────────────── */}
      <section aria-labelledby="inp">
        <h1 id="inp" className="text-[24px] font-bold tracking-[-0.015em] mb-1">Analyse a material</h1>
        <p className="text-[14px] text-[var(--color-text-2)] mb-4">
          Any description, in any organisation&rsquo;s house style.
        </p>
        <Card className="p-1.5" spotlight>
          <form onSubmit={submit} className="flex flex-col sm:flex-row gap-2">
            <label htmlFor="aq" className="sr-only">Material description</label>
            <input
              id="aq" value={q} onChange={(e) => setQ(e.target.value)}
              autoComplete="off" spellCheck={false}
              placeholder="SS HEX BOLT M10 X 50"
              className="mono flex-1 bg-transparent px-4 py-3.5 text-[14.5px] outline-none rounded-lg
                         placeholder:text-[var(--color-text-3)]"
            />
            <Button type="submit" disabled={busy || !q.trim()} icon={<ArrowRight size={15} weight="bold" />}>
              {busy ? 'Analysing' : 'Analyse'}
            </Button>
          </form>
        </Card>
      </section>

      {err && (
        <p role="alert" className="rounded-lg border px-4 py-3 text-[13.5px]"
           style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)', color: 'var(--color-distinct)' }}>
          {err}
        </p>
      )}

      {res && (
        <>
          {/* ── 03 Analysis ─────────────────────────────────────────────── */}
          <section aria-labelledby="ana">
            <SectionTitle
              hint={
                <button onClick={doReplay}
                  className="press link inline-flex items-center gap-1.5 text-[12px] font-medium cursor-pointer">
                  <ArrowClockwise size={12} weight="bold" aria-hidden="true" /> Replay analysis
                </button>
              }
            >
              <span id="ana">Analysis</span>
            </SectionTitle>

            <Card className="overflow-hidden">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 border-b border-[var(--color-line)]"
                   style={{ background: 'var(--color-brand-soft)' }}>
                <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold"
                      style={{ color: 'var(--color-brand)' }}>
                  <CheckCircle size={15} weight="fill" aria-hidden="true" />
                  Analysis complete
                </span>
                <span className="mono inline-flex items-center gap-1 text-[12.5px]" style={{ color: 'var(--color-brand)' }}>
                  <Lightning size={12} weight="fill" aria-hidden="true" />
                  {res.elapsed_ms.toFixed(1)} ms
                </span>
                <span className="text-[12.5px] text-[var(--color-text-2)]">
                  {res.candidates.length} candidates · {matches} match · {vetoed} rejected
                </span>
              </div>

              <div className="grid md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] min-w-0">
                {/* stages */}
                <ol className="list-none m-0 p-3 border-b md:border-b-0 md:border-r border-[var(--color-line)]">
                  {STAGES.map((s, i) => {
                    const lit = replay < 0 || i < replay
                    return (
                      <li key={s.key}
                          className="flex items-center gap-2.5 px-2 py-1.5 rounded-md transition-colors duration-200"
                          style={{ background: replay >= 0 && i === replay - 1 ? 'var(--color-brand-soft)' : undefined }}>
                        <CheckCircle
                          size={14} weight="fill" aria-hidden="true"
                          style={{ color: lit ? 'var(--color-brand)' : 'var(--color-line-strong)' }}
                        />
                        <span className="mono text-[10.5px] text-[var(--color-text-3)]">
                          {String(i + 1).padStart(2, '0')}
                        </span>
                        <span className="text-[13px]" style={{ color: lit ? 'var(--color-text)' : 'var(--color-text-3)' }}>
                          {s.label}
                        </span>
                      </li>
                    )
                  })}
                  {replay >= 0 && (
                    <li className="px-2 pt-2 text-[11px] text-[var(--color-text-3)]">
                      Replay of stages that already ran. Not a live computation.
                    </li>
                  )}
                </ol>

                {/* what was read */}
                <div className="p-4">
                  <p className="text-[12px] text-[var(--color-text-3)] mb-1">Normalized</p>
                  <p className="mono text-[13.5px] mb-4">{res.normalised}</p>
                  {res.item_name && (
                    <>
                      <p className="text-[12px] text-[var(--color-text-3)] mb-1">Item type</p>
                      <p className="text-[13.5px] font-medium mb-4">{res.item_name}</p>
                    </>
                  )}
                  <p className="text-[12px] text-[var(--color-text-3)] mb-2">Extracted attributes</p>
                  <div className="flex flex-wrap gap-2">
                    {res.attributes.map((a, i) => (
                      <motion.div key={a.code}
                        initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.26, delay: 0.04 * i, ease: [0.23, 1, 0.32, 1] }}
                        className="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2">
                        <p className="text-[10.5px] uppercase tracking-[0.08em] text-[var(--color-text-3)]">
                          {a.code.replace(/_/g, ' ')}
                        </p>
                        <p className="mono text-[13px] font-medium mt-0.5">{a.value}</p>
                        <p className="text-[10.5px] text-[var(--color-text-3)] mt-0.5">
                          {a.source}{a.inferred_unit ? ` · unit inferred` : ''}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </section>

          {/* ── 04 Match results ───────────────────────────────────────── */}
          <section aria-labelledby="mr" className="grid lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] gap-4 min-w-0">
            <div>
              <SectionTitle hint="highest first">
                <span id="mr">Candidates</span>
              </SectionTitle>
              <ul className="list-none m-0 p-0 grid gap-2">
                {res.candidates.map((c, i) => (
                  <motion.li key={c.record_id}
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.035 * i, ease: [0.23, 1, 0.32, 1] }}>
                    <Card
                      as="div" interactive spotlight
                      onClick={() => setSel(i)}
                      className={`p-3.5 ${i === sel ? 'ring-2' : ''}`}
                    >
                      <div
                        style={i === sel ? { boxShadow: `0 0 0 2px ${c.critical_veto ? 'var(--color-distinct-line)' : 'var(--color-brand-line)'}`, borderRadius: 8, margin: -2, padding: 2 } : undefined}
                      >
                        <div className="flex items-start justify-between gap-3 mb-1.5">
                          <div className="flex items-center gap-1.5">
                            <OrgChip org={c.org} />
                            <span className="mono text-[11.5px] text-[var(--color-text-3)]">{c.org_code}</span>
                          </div>
                          <span className="mono text-[15px] font-semibold"
                                style={{ color: c.critical_veto ? 'var(--color-distinct)' : 'var(--color-brand)' }}>
                            {c.confidence.toFixed(3)}
                          </span>
                        </div>
                        <p className="mono text-[13px] leading-snug mb-2.5">{c.candidate_material}</p>
                        <div className="flex items-center justify-between gap-3">
                          <DecisionBadge decision={c.decision} size="sm" />
                          <span className="text-[11.5px] text-[var(--color-text-3)]">
                            semantic <span className="mono">{c.semantic_score.toFixed(3)}</span>
                          </span>
                        </div>
                      </div>
                    </Card>
                  </motion.li>
                ))}
              </ul>
            </div>

            {/* ── Compare panel ────────────────────────────────────────── */}
            <div className="min-w-0">
              <SectionTitle hint={active?.nmc_id ? <NmcTag id={active.nmc_id} size="sm" /> : undefined}>
                Comparison
              </SectionTitle>
              <AnimatePresence mode="wait">
                {active && (
                  <motion.div
                    key={active.record_id}
                    initial={{ opacity: 0, filter: 'blur(3px)' }}
                    animate={{ opacity: 1, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, filter: 'blur(3px)' }}
                    transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
                  >
                    <Card className="overflow-hidden">
                      <div className="px-4 py-3 border-b border-[var(--color-line)] flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="mono text-[13px]">{active.candidate_material}</p>
                          <p className="text-[11.5px] text-[var(--color-text-3)] mt-0.5">
                            {active.org} · {active.org_code} · {active.provenance.toLowerCase().replace(/_/g, ' ')}
                          </p>
                        </div>
                        <DecisionBadge decision={active.decision} />
                      </div>

                      <div className="overflow-x-auto min-w-0">
                        <table className="w-full border-collapse text-left min-w-[26rem]">
                          <caption className="sr-only">
                            Attribute comparison between the queried material and this candidate.
                          </caption>
                          <thead>
                            <tr className="bg-[var(--color-surface-2)]">
                              {['Attribute', 'Query', 'Candidate', 'Result'].map((h, i) => (
                                <th key={h} scope="col"
                                    className={`px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.06em]
                                                text-[var(--color-text-3)] ${i === 3 ? 'text-right' : ''}`}>
                                  {h}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {active.evidence.map((r) => (
                              <tr key={r.code}
                                  className="row border-t border-[var(--color-line)] align-top"
                                  style={r.vetoed ? { background: 'var(--color-distinct-soft)' } : undefined}>
                                <th scope="row" className="px-3 py-2.5 text-[13px] font-medium text-[var(--color-text-2)] whitespace-nowrap">
                                  {r.attribute}
                                  {r.criticality === 'CRITICAL' && (
                                    <span className="ml-1.5 rounded px-1 py-px text-[9.5px] font-bold tracking-wide"
                                          style={{ background: 'var(--color-surface-3)', color: 'var(--color-text-3)' }}>
                                      CRITICAL
                                    </span>
                                  )}
                                </th>
                                <td className="mono px-3 py-2.5 text-[13px]">{r.source}</td>
                                <td className="mono px-3 py-2.5 text-[13px] font-medium"
                                    style={r.vetoed ? { color: 'var(--color-distinct)' } : undefined}>
                                  {r.candidate}
                                </td>
                                <td className="px-3 py-2.5 text-right whitespace-nowrap">
                                  <VerdictMark verdict={r.verdict} />
                                  {r.detail && r.verdict !== 'AGREE' && (
                                    <span className="block text-[11px] text-[var(--color-text-3)] mt-0.5">{r.detail}</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <div className="p-4 grid gap-3">
                        {active.critical_veto && <VetoNotice reason={active.veto_reason} />}
                        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                          {[
                            ['Score', active.confidence.toFixed(3)],
                            ['Semantic similarity', active.semantic_score.toFixed(3)],
                            ['Attributes agreed', `${active.counts.agree} of ${active.counts.agree + active.counts.disagree}`],
                            ['Not stated', String(active.counts.unknown)],
                          ].map(([k, v]) => (
                            <span key={k} className="text-[12px] text-[var(--color-text-3)]">
                              {k} <span className="mono text-[13px] font-semibold text-[var(--color-text)]">{v}</span>
                            </span>
                          ))}
                        </div>
                        {active.nmc_id && !active.critical_veto && (
                          <Link to={`/platform/material/${active.nmc_id}`}
                                className="press link inline-flex items-center gap-1.5 text-[13px] font-semibold w-fit">
                            Open canonical record
                            <ArrowSquareOut size={13} weight="bold" aria-hidden="true" />
                          </Link>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </section>

          <DemoNote>
            The score is an uncalibrated ranking score, not a probability. A candidate rejected by
            the critical attribute check scores exactly zero regardless of how similar the text is,
            which is why a rejected candidate can carry a higher semantic similarity than an
            accepted one.
          </DemoNote>
        </>
      )}
    </div>
  )
}
