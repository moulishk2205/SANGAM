import { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import { ArrowRight, ArrowClockwise, CheckCircle, Circle, Lightning, ArrowSquareOut } from '@phosphor-icons/react'
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

/**
 * The seven stages, in the order the engine actually runs them.
 *
 * `waitsForEngine` marks the stage gated on the real HTTP call rather than on a
 * timer. It sits on normalization because that is the first stage whose output
 * this client can actually hold: the response carries normalization, extraction,
 * retrieval and the decision together, so nothing before it can be substantiated
 * and nothing after it needs to wait. Gating later looked reasonable but left
 * stages 02 and 03 completing with no content to show, which is exactly the
 * disconnect this change exists to remove.
 */
const STAGES = [
  { key: 'input',      label: 'Input received',           ms: 160, waitsForEngine: false },
  { key: 'normalise',  label: 'Normalization',            ms: 220, waitsForEngine: true  },
  { key: 'extract',    label: 'Attribute extraction',     ms: 220, waitsForEngine: false },
  { key: 'retrieve',   label: 'Hybrid retrieval',         ms: 220, waitsForEngine: false },
  { key: 'compare',    label: 'Critical attribute check', ms: 200, waitsForEngine: false },
  { key: 'veto',       label: 'Veto evaluation',          ms: 180, waitsForEngine: false },
  { key: 'decide',     label: 'Decision',                 ms: 180, waitsForEngine: false },
] as const

/** Index of a stage by key, so reveal gates read as intent rather than magic numbers. */
const AT = Object.fromEntries(STAGES.map((s, i) => [s.key, i])) as Record<typeof STAGES[number]['key'], number>

type Phase = 'idle' | 'running' | 'done'
type StageState = 'pending' | 'active' | 'complete'

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export function Analyse() {
  const [params, setParams] = useSearchParams()
  const initial = params.get('q') ?? ''
  const [q, setQ] = useState(initial)
  const [res, setRes] = useState<MatchResult | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [sel, setSel] = useState(0)

  const [phase, setPhase] = useState<Phase>('idle')
  /** Index of the stage currently executing. -1 once every stage is complete. */
  const [stage, setStage] = useState(-1)
  /** True once the HTTP call has resolved. After this point no stage may be
   *  described as computing, because the engine has finished. */
  const [engineDone, setEngineDone] = useState(false)
  const [replaying, setReplaying] = useState(false)

  /** Guards against an in-flight run writing state after a newer run started. */
  const runId = useRef(0)

  const reduced =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const run = useCallback(async (text: string) => {
    if (!text.trim()) return
    const id = ++runId.current
    const alive = () => runId.current === id

    setErr(null); setRes(null); setSel(0)
    setEngineDone(false); setReplaying(false)
    setPhase('running')
    setStage(reduced ? -1 : 0)

    // The request goes out immediately, in parallel with the stage walk. The
    // presentation never delays the engine.
    const request = api.match(text, 8)

    if (reduced) {
      // No walk: the progression is still legible from the completed list, and
      // nothing is withheld.
      try {
        const r = await request
        if (!alive()) return
        setRes(r); setEngineDone(true); setPhase('done'); setStage(-1)
      } catch (e) {
        if (!alive()) return
        setErr(readableError(e)); setPhase('idle'); setStage(-1)
      }
      return
    }

    try {
      for (let i = 0; i < STAGES.length; i++) {
        if (!alive()) return
        setStage(i)

        if (STAGES[i].waitsForEngine) {
          // Hold here until the engine actually answers. If it is quick this
          // is a brief beat; if it is slow the user is watching the stage that
          // is genuinely responsible for the wait.
          const [r] = await Promise.all([request, sleep(STAGES[i].ms)])
          if (!alive()) return
          setRes(r)
          setEngineDone(true)
        } else {
          await sleep(STAGES[i].ms)
        }
      }
      if (!alive()) return
      setStage(-1)
      setPhase('done')
    } catch (e) {
      if (!alive()) return
      setErr(readableError(e)); setRes(null); setPhase('idle'); setStage(-1)
    }
  }, [reduced])

  useEffect(() => { if (initial) void run(initial) }, [initial, run])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setParams({ q })
    void run(q)
  }

  /**
   * Replay walks the same stages again once everything has finished. It is a
   * presentation of work that is already complete and says so, which is the
   * distinction that keeps the first run honest.
   */
  const doReplay = async () => {
    if (phase !== 'done' || reduced) return
    const id = ++runId.current
    setReplaying(true)
    for (let i = 0; i < STAGES.length; i++) {
      if (runId.current !== id) return
      setStage(i)
      await sleep(STAGES[i].ms)
    }
    if (runId.current !== id) return
    setStage(-1)
    setReplaying(false)
  }

  const stageState = (i: number): StageState => {
    if (phase === 'idle') return 'pending'
    if (phase === 'done' && stage === -1) return 'complete'
    if (stage === -1) return 'complete'
    return i < stage ? 'complete' : i === stage ? 'active' : 'pending'
  }

  /** Content for a stage is shown once that stage has finished. */
  const done = (key: keyof typeof AT) =>
    phase === 'done' || (phase === 'running' && (stage === -1 || stage > AT[key]))

  const busy = phase === 'running'

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

      {(res || busy) && (
        <>
          {/* ── 03 Analysis ─────────────────────────────────────────────── */}
          <section aria-labelledby="ana">
            <SectionTitle
              hint={
                <button onClick={doReplay} disabled={phase !== 'done'}
                  className="press link inline-flex items-center gap-1.5 text-[12px] font-medium cursor-pointer
                             disabled:opacity-40 disabled:cursor-not-allowed">
                  <ArrowClockwise size={12} weight="bold" aria-hidden="true" /> Replay analysis
                </button>
              }
            >
              <span id="ana">Analysis</span>
            </SectionTitle>

            <Card className="overflow-hidden">
              <div
                className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 border-b border-[var(--color-line)]
                           transition-colors duration-300"
                style={{ background: phase === 'done' ? 'var(--color-brand-soft)' : 'var(--color-neutral-ambient)' }}
                aria-live="polite"
              >
                {phase === 'done' ? (
                  <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold"
                        style={{ color: 'var(--color-brand)' }}>
                    <CheckCircle size={15} weight="fill" aria-hidden="true" />
                    Analysis complete
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-2 text-[13px] font-semibold text-[var(--color-text-2)]">
                    <span className="stage-pulse" aria-hidden="true" />
                    {engineDone ? 'Presenting completed stages' : 'Analysing'}
                  </span>
                )}

                {/* The measured time appears only once the engine has actually
                    answered, and it is always the engine's own figure. */}
                {engineDone && res && (
                  <span className="mono inline-flex items-center gap-1 text-[12.5px]"
                        style={{ color: phase === 'done' ? 'var(--color-brand)' : 'var(--color-text-2)' }}>
                    <Lightning size={12} weight="fill" aria-hidden="true" />
                    {res.elapsed_ms.toFixed(1)} ms
                  </span>
                )}

                {done('decide') && res && (
                  <span className="text-[12.5px] text-[var(--color-text-2)]">
                    {res.candidates.length} candidates · {matches} match · {vetoed} rejected
                  </span>
                )}
              </div>

              <div className="grid md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] min-w-0">
                {/* stages */}
                <ol className="list-none m-0 p-3 border-b md:border-b-0 md:border-r border-[var(--color-line)]">
                  {STAGES.map((st, i) => {
                    const state = stageState(i)
                    return (
                      <li
                        key={st.key}
                        aria-current={state === 'active' ? 'step' : undefined}
                        className="flex items-center gap-2.5 px-2 py-1.5 rounded-md transition-colors duration-200"
                        style={{ background: state === 'active' ? 'var(--color-brand-ambient)' : undefined }}
                      >
                        {state === 'complete' ? (
                          <CheckCircle size={14} weight="fill" aria-hidden="true"
                                       style={{ color: 'var(--color-brand)' }} />
                        ) : state === 'active' ? (
                          <span className="stage-pulse" aria-hidden="true" />
                        ) : (
                          <Circle size={14} weight="regular" aria-hidden="true"
                                  style={{ color: 'var(--color-line-strong)' }} />
                        )}
                        <span className="mono text-[10.5px] text-[var(--color-text-3)]">
                          {String(i + 1).padStart(2, '0')}
                        </span>
                        <span
                          className="text-[13px] transition-colors duration-200"
                          style={{
                            color: state === 'pending' ? 'var(--color-text-3)' : 'var(--color-text)',
                            fontWeight: state === 'active' ? 600 : 400,
                          }}
                        >
                          {st.label}
                        </span>
                        {/* Never claim a stage is computing once the engine has
                            answered: after that point the walk is presentation. */}
                        <span className="sr-only">
                          {state === 'complete' ? 'complete'
                            : state === 'active' ? (engineDone ? 'presenting' : 'processing')
                            : 'pending'}
                        </span>
                      </li>
                    )
                  })}
                  {(replaying || (phase === 'running' && engineDone)) && (
                    <li className="px-2 pt-2 text-[11px] text-[var(--color-text-3)]">
                      {replaying
                        ? 'Replay of stages that already ran. Not a live computation.'
                        : `Engine finished in ${res?.elapsed_ms.toFixed(1)} ms. Presenting the remaining stages.`}
                    </li>
                  )}
                </ol>

                {/* what was read */}
                <div className="p-4">
                  {/* Each block appears only once its stage has finished, so the
                      panel is the pipeline's output rather than a preview of it. */}
                  <p className="text-[12px] text-[var(--color-text-3)] mb-1">Input</p>
                  <p className="mono text-[13.5px] mb-4 text-[var(--color-text-2)]">{res?.query ?? q}</p>

                  {done('normalise') && res && (
                    <motion.div
                      initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
                    >
                      <p className="text-[12px] text-[var(--color-text-3)] mb-1">Normalized</p>
                      <p className="mono text-[13.5px] mb-4">{res.normalised}</p>
                      {res.item_name && (
                        <>
                          <p className="text-[12px] text-[var(--color-text-3)] mb-1">Item type</p>
                          <p className="text-[13.5px] font-medium mb-4">{res.item_name}</p>
                        </>
                      )}
                    </motion.div>
                  )}

                  {done('extract') && res && (
                  <>
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
                  </>
                  )}

                  {/* Placeholder while earlier stages are still running. Sized
                      to the content it replaces so nothing jumps when it fills. */}
                  {!done('extract') && (
                    <p className="text-[12.5px] text-[var(--color-text-3)]">
                      {stage >= 0 ? `${STAGES[stage].label}…` : 'Waiting for the engine…'}
                    </p>
                  )}
                </div>
              </div>
            </Card>
          </section>

          {/* ── 04 Match results ───────────────────────────────────────── */}
          {done('retrieve') && res && (
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
                    {/* Selection is an ambient surface, not an outline. A
                        coloured perimeter competes with the badge and the score
                        for the same signal; a faint wash of the verdict's own
                        hue says "this is the one you are reading" without
                        shouting, and leaves the semantic colour to the badge. */}
                    <Card
                      as="div" interactive spotlight
                      onClick={() => setSel(i)}
                      className="p-3.5 transition-colors duration-250"
                      style={
                        i === sel
                          ? {
                              background: c.critical_veto
                                ? 'var(--color-distinct-ambient)'
                                : 'var(--color-brand-ambient)',
                            }
                          : undefined
                      }
                    >
                      <div>
                        <div className="flex items-start justify-between gap-3 mb-1.5">
                          <div className="flex items-center gap-1.5">
                            <OrgChip org={c.org} />
                            <span className="mono text-[11.5px] text-[var(--color-text-3)]">{c.org_code}</span>
                          </div>
                          {done('decide') ? (
                            <span className="mono text-[15px] font-semibold"
                                  style={{ color: c.critical_veto ? 'var(--color-distinct)' : 'var(--color-brand)' }}>
                              {c.confidence.toFixed(3)}
                            </span>
                          ) : (
                            <span className="mono text-[15px] font-semibold text-[var(--color-text-3)]">–––</span>
                          )}
                        </div>
                        <p className="mono text-[13px] leading-snug mb-2.5">{c.candidate_material}</p>
                        <div className="flex items-center justify-between gap-3 min-h-[22px]">
                          {/* The verdict is authoritative only after the decision
                              stage. Until then the row shows that it is still
                              being evaluated rather than a provisional answer. */}
                          {done('decide') ? (
                            <DecisionBadge decision={c.decision} size="sm" />
                          ) : (
                            <span className="text-[11.5px] text-[var(--color-text-3)]">Evaluating</span>
                          )}
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
                                  className="row border-t border-[var(--color-line)] align-top
                                             transition-colors duration-250"
                                  style={{
                                    /* Ambient surface per verdict. A vetoed row keeps
                                       the louder -soft tint so the attribute that
                                       actually rejected the pair still stands out
                                       from an ordinary disagreement. */
                                    background: r.vetoed
                                      ? 'var(--color-distinct-soft)'
                                      : r.verdict === 'AGREE'
                                        ? 'var(--color-agree-row)'
                                        : r.verdict === 'DISAGREE'
                                          ? 'var(--color-disagree-row)'
                                          : 'var(--color-neutral-ambient)',
                                  }}>
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
          )}

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
