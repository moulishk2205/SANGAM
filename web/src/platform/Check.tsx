import { useEffect, useRef, useState, useCallback } from 'react'
import { ArrowRight, ArrowsClockwise, Warning } from '@phosphor-icons/react'
import { api, type MatchResult, type Candidate, type Health } from './api'
import { EvidenceTable, VerdictSummary } from './Evidence'

/**
 * Material Check — the platform's primary interaction.
 *
 * Calls the real engine. Every score, verdict and explanation on this screen
 * was computed by `MatchingEngine`, not by anything in this file.
 *
 * On the progress problem
 * -----------------------
 * The engine's median is around 13 ms and a full HTTP round trip lands near
 * 90 ms. That is faster than any progress animation can honestly render, so
 * there is no progress bar and no staged fake pipeline. The result appears,
 * and the measured time is printed next to it. A user who wants to watch the
 * stages can press Replay, which steps through the stages that actually ran
 * using their real outputs. The speed is the feature; padding it would be a
 * lie about the system.
 */

const STAGES = [
  { key: 'normalise', label: 'Normalise' },
  { key: 'extract',   label: 'Extract attributes' },
  { key: 'retrieve',  label: 'Retrieve candidates' },
  { key: 'compare',   label: 'Compare specifications' },
  { key: 'decide',    label: 'Apply veto and decide' },
] as const

export function Check() {
  const [query, setQuery] = useState('SS HEX BOLT M10 X 50')
  const [result, setResult] = useState<MatchResult | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [samples, setSamples] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState(0)
  const [swapping, setSwapping] = useState(false)
  const [replayStage, setReplayStage] = useState(-1)
  const listRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
    api.samples().then((s) => setSamples(s.samples)).catch(() => {})
  }, [])

  const run = useCallback(async (q: string) => {
    if (!q.trim()) return
    setBusy(true); setError(null); setReplayStage(-1)
    try {
      const r = await api.match(q, 6)
      setResult(r)
      setSelected(0)
    } catch (e) {
      setError(
        e instanceof Error && e.message.includes('Failed to fetch')
          ? 'Cannot reach the engine. Start it with: uvicorn src.nmc.api:app --port 8000'
          : String(e),
      )
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => { void run(query) /* seed the demo state */ // eslint-disable-next-line
  }, [])

  /**
   * Keyboard navigation through candidates.
   *
   * Deliberately unanimated. A reviewer moves through this list continuously,
   * and an action repeated that often should never animate: the transition
   * reads as latency rather than polish.
   */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!result || (e.target as HTMLElement)?.tagName === 'INPUT') return
      const n = result.candidates.length
      if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); setSelected((s) => Math.min(s + 1, n - 1)) }
      if (e.key === 'k' || e.key === 'ArrowUp')   { e.preventDefault(); setSelected((s) => Math.max(s - 1, 0)) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [result])

  /** Swap the evidence panel under a brief blur so the eye reads one object
   *  changing rather than two tables trading places. */
  const select = (i: number) => {
    if (i === selected) return
    setSwapping(true)
    setSelected(i)
    window.setTimeout(() => setSwapping(false), 60)
  }

  const replay = () => {
    setReplayStage(0)
    STAGES.forEach((_, i) => window.setTimeout(() => setReplayStage(i + 1), (i + 1) * 620))
  }

  const active: Candidate | undefined = result?.candidates[selected]

  return (
    <div className="grid gap-10">
      {/* ── Query ─────────────────────────────────────────────────────── */}
      <section aria-labelledby="check-h">
        <h2 id="check-h" className="t-datum text-[11px] uppercase tracking-[0.14em] text-graphite mb-4">
          Check a material
        </h2>

        <form
          onSubmit={(e) => { e.preventDefault(); void run(query) }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <label htmlFor="q" className="visually-hidden">Material description</label>
          <input
            id="q"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            spellCheck={false}
            autoComplete="off"
            placeholder="Type a material description"
            className="flex-1 bg-panel border border-[var(--color-line-hard)] px-4 py-3.5
                       t-datum text-[14px] text-paper placeholder:text-graphite
                       focus-ring transition-colors duration-150
                       hover:border-[var(--color-line-hard)] focus:border-live"
          />
          <button
            type="submit"
            disabled={busy || !query.trim()}
            className="pressable focus-ring inline-flex items-center justify-center gap-3
                       border border-paper/70 bg-transparent px-6 py-3.5 text-paper
                       hover:bg-paper hover:text-ink"
          >
            <span className="t-datum text-[11px] uppercase tracking-[0.14em]">
              {busy ? 'Analysing' : 'Analyse'}
            </span>
            <ArrowRight size={14} weight="bold" aria-hidden="true" />
          </button>
        </form>

        {samples.length > 0 && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3">
            <span className="t-datum text-[10px] uppercase tracking-[0.12em] text-graphite">Try</span>
            {samples.map((s) => (
              <button
                key={s}
                onClick={() => { setQuery(s); void run(s) }}
                className="pressable focus-ring t-datum text-[11px] text-mist hover:text-paper
                           border-b border-transparent hover:border-[var(--color-line-hard)] pb-0.5 cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </section>

      {error && (
        <p role="alert" className="t-datum text-[12px] text-cut border border-cut/40 bg-cut/[0.06] px-4 py-3
                                    inline-flex items-start gap-2">
          <Warning size={15} weight="bold" aria-hidden="true" className="mt-px shrink-0" />
          {error}
        </p>
      )}

      {/* ── What the engine read ──────────────────────────────────────── */}
      {result && (
        <section aria-labelledby="read-h" className="enter">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-4">
            <h2 id="read-h" className="t-datum text-[11px] uppercase tracking-[0.14em] text-graphite">
              What the engine read
            </h2>
            <div className="flex items-center gap-5">
              <span className="t-datum tabular text-[11px] text-graphite">
                {result.elapsed_ms.toFixed(1)} ms
              </span>
              <button
                onClick={replay}
                className="pressable focus-ring t-datum text-[10px] uppercase tracking-[0.12em]
                           text-mist hover:text-paper inline-flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowsClockwise size={12} weight="bold" aria-hidden="true" />
                Replay stages
              </button>
            </div>
          </div>

          <div className="border border-[var(--color-line-soft)] bg-panel">
            <div className="px-4 py-3 border-b border-[var(--color-line-soft)]">
              <p className="t-datum text-[12px] text-mist">
                <span className="text-graphite">normalised </span>{result.normalised}
              </p>
              {result.item_name && (
                <p className="t-datum text-[12px] text-mist mt-1">
                  <span className="text-graphite">item name </span>{result.item_name}
                </p>
              )}
            </div>

            <dl className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-[var(--color-line-soft)] m-0">
              {result.attributes.map((a) => (
                <div key={a.code} className="bg-panel px-4 py-3">
                  <dt className="t-datum text-[10px] uppercase tracking-[0.12em] text-graphite">
                    {a.code.replace(/_/g, ' ')}
                  </dt>
                  <dd className="t-datum text-[13px] text-paper m-0 mt-1">{a.value}</dd>
                  <dd className="t-datum text-[10px] text-graphite m-0 mt-0.5">
                    {a.source}
                    {a.inferred_unit && ` · unit inferred: ${a.inferred_unit}`}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Replay of the stages that actually ran, on demand. Not a loader. */}
          {replayStage >= 0 && (
            <ol className="mt-4 grid gap-1.5 list-none p-0 m-0" aria-live="polite">
              {STAGES.map((s, i) => (
                <li
                  key={s.key}
                  className={`t-datum text-[11px] flex items-center gap-3 transition-colors duration-200
                              ${i < replayStage ? 'text-live' : 'text-graphite'}`}
                >
                  <span className="tabular w-5">{String(i + 1).padStart(2, '0')}</span>
                  {s.label}
                  {i < replayStage && <span className="text-graphite">done</span>}
                </li>
              ))}
              <li className="t-datum text-[10px] text-graphite mt-1">
                Replay of the stages that ran in {result.elapsed_ms.toFixed(1)} ms. Not a live computation.
              </li>
            </ol>
          )}
        </section>
      )}

      {/* ── Candidates + evidence ─────────────────────────────────────── */}
      {result && result.candidates.length > 0 && (
        <section aria-labelledby="cand-h" className="grid lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] gap-px overflow-hidden
                                                     bg-[var(--color-line-soft)] border border-[var(--color-line-soft)]">
          <div className="bg-void">
            <h2 id="cand-h" className="t-datum text-[11px] uppercase tracking-[0.14em] text-graphite px-4 py-3
                                        border-b border-[var(--color-line-soft)]">
              Candidates
              <span className="text-graphite ml-2 normal-case tracking-normal hidden sm:inline">
                j and k to move
              </span>
            </h2>
            <ul ref={listRef} className="list-none p-0 m-0">
              {result.candidates.map((c, i) => (
                <li key={c.record_id}>
                  <button
                    onClick={() => select(i)}
                    aria-current={i === selected}
                    className={`w-full text-left px-4 py-3 border-b border-[var(--color-line-soft)]
                                focus-ring cursor-pointer row-hover
                                ${i === selected ? 'kbd-selected' : ''}`}
                  >
                    <span className="flex items-baseline justify-between gap-3 mb-1">
                      <span className="t-datum text-[10px] text-graphite">
                        {c.org} {c.org_code}
                      </span>
                      <span className={`t-datum tabular text-[12px]
                                        ${c.critical_veto ? 'text-cut' : 'text-live'}`}>
                        {c.confidence.toFixed(3)}
                      </span>
                    </span>
                    <span className="t-datum text-[12px] text-paper block leading-snug">
                      {c.candidate_material}
                    </span>
                    <span className={`t-datum text-[10px] uppercase tracking-[0.1em] mt-1.5 block
                                      ${c.critical_veto ? 'text-cut' : 'text-mist'}`}>
                      {c.decision.replace('_', ' ')}
                      <span className="text-graphite normal-case tracking-normal ml-2">
                        semantic {c.semantic_score.toFixed(3)}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className={`bg-void p-5 lg:p-6 ${swapping ? 'swapping' : 'swapped'}`}>
            {active && (
              <>
                <p className="t-datum text-[10px] uppercase tracking-[0.12em] text-graphite mb-1">
                  {active.org} {active.org_code}
                  <span className="ml-3 normal-case tracking-normal">{active.provenance.toLowerCase().replace(/_/g, ' ')}</span>
                </p>
                <p className="t-datum text-[13px] text-paper mb-6">{active.candidate_material}</p>
                <EvidenceTable rows={active.evidence} />
                <VerdictSummary c={active} />
              </>
            )}
          </div>
        </section>
      )}

      {/* Provenance. Stated on the surface, not in a footnote. */}
      {health && (
        <p className="t-datum text-[10px] text-graphite leading-relaxed max-w-[70ch]">
          {health.records.toLocaleString()} records indexed in {(health.index_build_ms / 1000).toFixed(1)} s.
          Dense retrieval channel {health.dense_channel ? 'on' : 'off'}. Model {health.model_version}.
          Corpus is {health.corpus}: organisation names and codes are invented, and the score shown is an
          uncalibrated ranking score, not a probability.
        </p>
      )}
    </div>
  )
}
