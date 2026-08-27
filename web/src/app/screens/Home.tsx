import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowRight, Sparkle } from '@phosphor-icons/react'
import { api, readableError, type Stats, type Health } from '../api'
import { Card, Button, StatTile, SectionTitle, DemoNote } from '../components/ui'

/**
 * 01 — Home.
 *
 * Not a repeat of the landing page. The landing page explains why the problem
 * exists; this is the console that does something about it, so the first
 * action has to be unmissable: type a description, analyse it.
 *
 * Every figure is fetched from the engine. Nothing on this screen is a
 * hard-coded number.
 */
export function Home() {
  const nav = useNavigate()
  const [q, setQ] = useState('')
  const [stats, setStats] = useState<Stats | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  type Example = { chip: string; query: string; note: string; item_name: string }
  const [samples, setSamples] = useState<Example[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setErr(readableError(e)))
    api.health().then(setHealth).catch(() => {})
    api.samples().then((s) => setSamples(s.examples ?? [])).catch(() => {})
  }, [])

  const go = (text: string) => {
    if (text.trim()) nav(`/platform/analyse?q=${encodeURIComponent(text.trim())}`)
  }

  return (
    <div className="grid gap-8">
      {/* ── Primary action ─────────────────────────────────────────────── */}
      <section aria-labelledby="start">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        >
          <h1 id="start" className="text-[clamp(1.7rem,3.4vw,2.5rem)] font-bold tracking-[-0.02em] leading-[1.1]">
            Standardize material identity
            <br className="hidden sm:block" /> across organisations.
          </h1>
          <p className="mt-3 text-[15.5px] text-[var(--color-text-2)] max-w-[60ch]">
            Enter any material description. The engine extracts its engineering attributes,
            retrieves candidates, and decides identity on the specification rather than on
            how the words are spelled.
          </p>

          <Card className="mt-6 p-1.5" spotlight>
            <form
              onSubmit={(e) => { e.preventDefault(); go(q) }}
              className="flex flex-col sm:flex-row gap-2"
            >
              <label htmlFor="home-q" className="sr-only">Material description</label>
              <input
                id="home-q"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM"
                autoComplete="off"
                spellCheck={false}
                className="mono flex-1 bg-transparent px-4 py-3.5 text-[14.5px] text-[var(--color-text)]
                           placeholder:text-[var(--color-text-3)] outline-none rounded-lg"
              />
              <Button type="submit" disabled={!q.trim()} icon={<ArrowRight size={15} weight="bold" />}>
                Analyse material
              </Button>
            </form>
          </Card>

          {/* Examples load the field; they do not run. The primary action stays
              the one the visitor presses, so nothing happens that they did not
              ask for and they can read the description before analysing it. */}
          {samples.length > 0 && (
            <div className="mt-4">
              <p className="text-[12px] text-[var(--color-text-3)] inline-flex items-center gap-1.5 mb-2">
                <Sparkle size={12} weight="fill" aria-hidden="true" />
                Try an example — loads the field above, does not run
              </p>
              <div className="flex flex-wrap gap-2">
                {samples.map((s, i) => (
                  <motion.button
                    key={s.query}
                    onClick={() => { setQ(s.query); document.getElementById('home-q')?.focus() }}
                    title={s.note}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.04 * i, ease: [0.23, 1, 0.32, 1] }}
                    className="press group rounded-lg border border-[var(--color-line)] bg-[var(--color-surface)]
                               px-3 py-2 text-left cursor-pointer max-w-full
                               hover:border-[var(--color-brand-line)] hover:bg-[var(--color-brand-soft)]
                               transition-colors duration-200"
                  >
                    <span className="block text-[12.5px] font-semibold text-[var(--color-text)]
                                     group-hover:text-[var(--color-brand)]">
                      {s.chip}
                    </span>
                    <span className="mono block text-[11px] text-[var(--color-text-3)] mt-0.5 truncate max-w-[30ch]">
                      {s.query}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </section>

      {err && (
        <p role="alert" className="rounded-lg border px-4 py-3 text-[13.5px]"
           style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)', color: 'var(--color-distinct)' }}>
          {err}
        </p>
      )}

      {/* ── What is in the catalogue ───────────────────────────────────── */}
      {stats && (
        <section aria-labelledby="cat">
          <SectionTitle hint={`${stats.collapse_ratio}× collapse`}>
            <span id="cat">Catalogue</span>
          </SectionTitle>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatTile delay={0}    value={stats.source_records.toLocaleString()} label="Source records" note="as the organisations wrote them" />
            <StatTile delay={0.05} value={stats.canonical_materials.toLocaleString()} label="Canonical materials" note="after standardization" tone="info" />
            <StatTile delay={0.1}  value={stats.cross_org_materials.toLocaleString()} label="Held by more than one" note="the harmonisation opportunity" tone="brand" />
            <StatTile delay={0.15} value={String(stats.organisations)} label="Organisations" note="in this demonstration corpus" />
          </div>
        </section>
      )}

      {/* ── How a decision is reached ──────────────────────────────────── */}
      <section aria-labelledby="how">
        <SectionTitle><span id="how">How a decision is reached</span></SectionTitle>
        <div className="grid sm:grid-cols-3 gap-3">
          {[
            { n: '01', t: 'Read the specification',
              d: 'Abbreviations expand, units resolve, and the description becomes typed attributes: item type, material, thread, length.' },
            { n: '02', t: 'Retrieve, do not decide',
              d: 'A lexical channel and a dense channel each propose candidates. Retrieval only narrows the field; it never settles identity.' },
            { n: '03', t: 'Compare, then veto',
              d: 'Attributes are compared with tolerances. A disagreement on a critical attribute rejects the pair outright, whatever the text similarity says.' },
          ].map((s, i) => (
            <motion.div key={s.n}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.34, delay: 0.05 * i, ease: [0.23, 1, 0.32, 1] }}>
              <Card spotlight className="p-4 h-full">
                <span className="mono text-[11px] font-semibold text-[var(--color-brand)]">{s.n}</span>
                <h3 className="mt-1.5 text-[14.5px] font-semibold">{s.t}</h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--color-text-2)]">{s.d}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Provenance ─────────────────────────────────────────────────── */}
      {health && (
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mb-2">
            <span className="inline-flex items-center gap-1.5 text-[12.5px] font-medium">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--color-brand)' }} aria-hidden="true" />
              Engine ready
            </span>
            <span className="mono text-[12px] text-[var(--color-text-3)]">{health.model_version}</span>
            <span className="text-[12px] text-[var(--color-text-3)]">
              dense retrieval {health.dense_channel ? 'on' : 'off'}
            </span>
            <span className="text-[12px] text-[var(--color-text-3)]">
              indexed in {(health.index_build_ms / 1000).toFixed(1)}s
            </span>
          </div>
          <DemoNote>
            Demonstration corpus: {health.corpus}. Organisation names and material codes are
            invented and are not the records of any real enterprise. Scores shown throughout are
            uncalibrated ranking scores, not probabilities.
          </DemoNote>
        </Card>
      )}
    </div>
  )
}
