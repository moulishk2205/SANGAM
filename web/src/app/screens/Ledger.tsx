import { useEffect, useState } from 'react'
import { motion } from 'motion/react'
import { SealCheck, Warning, Link as LinkIcon } from '@phosphor-icons/react'
import { ledger, ApiError, type DecisionRow, type Certificate } from '../api'
import { Card, SectionTitle, DemoNote } from '../components/ui'
import { ListSkeleton } from '../components/Skeleton'

/* ══════════════════════════════════════════════════════════════════════════
   The decision ledger.

   Every decision the platform has made, newest first, with its certificate
   openable. The chain verification runs on load and is shown whatever it says —
   an audit feature that only reports success is not an audit feature.

   The wording is careful and stays careful: tamper-EVIDENT, never tamper-proof.
   The chain lives in a database we control, so on its own it proves the rows
   are self-consistent. It becomes evidence when the head is anchored somewhere
   we do not, and the screen says so rather than implying more.
   ══════════════════════════════════════════════════════════════════════════ */

const KIND_TONE: Record<string, string> = {
  APPROVE: 'var(--color-brand)',
  PROPOSE: 'var(--color-info)',
  REJECT: 'var(--color-distinct)',
  UNMAP: 'var(--color-distinct)',
  SUPERSEDE: 'var(--color-unknown)',
  MERGE: 'var(--color-unknown)',
  SPLIT: 'var(--color-unknown)',
}

export function Ledger() {
  const [rows, setRows] = useState<DecisionRow[]>([])
  const [chain, setChain] = useState<{ ok: boolean; checked: number; head?: string; note: string } | null>(null)
  const [open, setOpen] = useState<Certificate | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  // A failed certificate fetch used to be swallowed by a bare catch, so the
  // row simply did nothing when clicked and the screen looked inert. A dead
  // click with no explanation is worse than an error message.
  const [certErr, setCertErr] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([ledger.decisions(60), ledger.verify()])
      .then(([d, v]) => { setRows(d.decisions); setChain(v) })
      .catch((e) => setErr(e instanceof ApiError ? e.message : String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="grid gap-6">
      <section aria-labelledby="ledger-h">
        <h1 id="ledger-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Decision ledger
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[66ch]">
          Every decision, with the evidence frozen as it stood. A certificate records the
          comparison, the gazetteer and template versions, the model, the person, and the
          competence scope they held at that moment — not what any of those are now.
        </p>
      </section>

      {chain && (
        <Card className="p-4" style={{
          background: chain.ok ? 'var(--color-brand-ambient)' : 'var(--color-distinct-ambient)',
        }}>
          <div className="flex items-start gap-3">
            {chain.ok
              ? <SealCheck size={18} weight="fill" aria-hidden="true"
                           className="mt-0.5 shrink-0" style={{ color: 'var(--color-brand)' }} />
              : <Warning size={18} weight="fill" aria-hidden="true"
                         className="mt-0.5 shrink-0" style={{ color: 'var(--color-distinct)' }} />}
            <div className="min-w-0">
              <p className="text-[14px] font-semibold"
                 style={{ color: chain.ok ? 'var(--color-brand)' : 'var(--color-distinct)' }}>
                {chain.ok
                  ? `Chain intact across ${chain.checked} certificates`
                  : 'Chain broken — a certificate does not link to its predecessor'}
              </p>
              {chain.head && (
                <p className="mono text-[11.5px] text-[var(--color-text-3)] mt-1 break-all">
                  head {chain.head}
                </p>
              )}
              <p className="text-[12px] text-[var(--color-text-2)] mt-2 max-w-[70ch] leading-relaxed">
                {chain.note}
              </p>
            </div>
          </div>
        </Card>
      )}

      {err && (
        <Card className="p-4">
          <p role="alert" className="text-[13.5px]" style={{ color: 'var(--color-distinct)' }}>{err}</p>
        </Card>
      )}

      {loading && <ListSkeleton rows={6} />}

      {!loading && rows.length === 0 && !err && (
        <Card className="p-8 text-center">
          <p className="text-[14.5px] font-semibold">No decisions yet</p>
          <p className="text-[13px] text-[var(--color-text-2)] mt-1.5 max-w-[46ch] mx-auto">
            Approve or reject something in the review queue and it will appear here with
            its certificate.
          </p>
        </Card>
      )}

      {rows.length > 0 && (
        <section aria-labelledby="dec-h">
          <SectionTitle hint={`${rows.length} shown`}>
            <span id="dec-h">Decisions</span>
          </SectionTitle>
          <Card className="overflow-hidden">
            {rows.map((d) => (
              <button
                key={d.id}
                onClick={() => {
                  setCertErr(null)
                  ledger.certificate(d.id)
                    .then((c) => { setOpen(c); setCertErr(null) })
                    .catch((e) => {
                      setOpen(null)
                      setCertErr(e instanceof ApiError
                        ? `Certificate ${d.id}: ${e.message}`
                        : `Certificate ${d.id} could not be opened.`)
                    })
                }}
                className="row press w-full text-left flex flex-wrap items-center gap-x-4 gap-y-1
                           px-4 py-3 border-b border-[var(--color-line)] last:border-0 cursor-pointer"
              >
                <span className="mono text-[11.5px] text-[var(--color-text-3)] w-10 shrink-0">
                  #{d.seq}
                </span>
                <span className="text-[12.5px] font-semibold w-[6.5rem] shrink-0"
                      style={{ color: KIND_TONE[d.kind] || 'var(--color-text-2)' }}>
                  {d.kind}
                </span>
                <span className="mono text-[12px] text-[var(--color-text-2)] min-w-0 flex-1 truncate">
                  {d.canonical_id || d.mapping_id || '—'}
                </span>
                <span className="text-[11.5px] text-[var(--color-text-3)]">{d.actor_role || 'system'}</span>
                <span className="mono text-[11px] text-[var(--color-text-3)] hidden sm:inline">
                  {d.hash.slice(0, 12)}…
                </span>
                <span className="mono text-[11px] text-[var(--color-text-3)]">
                  {new Date(d.at).toLocaleString()}
                </span>
              </button>
            ))}
          </Card>
        </section>
      )}

      {certErr && (
        <Card className="p-4">
          <p role="alert" className="text-[13.5px]" style={{ color: 'var(--color-distinct)' }}>
            {certErr}
          </p>
        </Card>
      )}

      {/* ── the certificate ───────────────────────────────────────────── */}
      {open && (
        <motion.div
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, ease: [0.23, 1, 0.32, 1] }}
        >
          <SectionTitle hint={<button onClick={() => setOpen(null)} className="link cursor-pointer">Close</button>}>
            Certificate {open.id}
          </SectionTitle>
          <Card className="p-5 grid gap-4">
            <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-2.5 text-[12.5px]">
              {[
                ['Decision', open.kind],
                ['Sequence', `#${open.seq}`],
                ['Mapping', open.mapping_id || '—'],
                ['Canonical', open.canonical_id || '—'],
                ['Signed by', open.actor ? `${open.actor.name} (${open.actor.role})` : 'system'],
                ['At', new Date(open.at).toLocaleString()],
                ['Gazetteer', open.versions.gazetteer],
                ['Template', open.versions.template],
                ['Model', open.versions.model],
              ].map(([k, v]) => (
                <div key={k} className="grid grid-cols-[8rem_1fr] gap-3">
                  <dt className="text-[var(--color-text-3)]">{k}</dt>
                  <dd className="m-0 mono text-[var(--color-text)] break-all">{v}</dd>
                </div>
              ))}
            </dl>

            {open.note && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1">
                  Justification given
                </p>
                <p className="text-[13px] text-[var(--color-text)]">{open.note}</p>
              </div>
            )}

            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1.5">
                Scope held at the moment of signing
              </p>
              <p className="mono text-[12px] text-[var(--color-text-2)] break-all">
                {JSON.stringify(open.actor?.scope_at_decision ?? {})}
              </p>
            </div>

            <div>
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1.5">
                <LinkIcon size={11} weight="bold" aria-hidden="true" /> Chain
              </p>
              <p className="mono text-[11.5px] text-[var(--color-text-3)] break-all">
                prev {open.chain.prev_hash || '(genesis)'}
              </p>
              <p className="mono text-[11.5px] text-[var(--color-text)] break-all">
                this {open.chain.hash}
              </p>
            </div>

            {Object.keys(open.evidence || {}).length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-1.5">
                  Evidence, frozen
                </p>
                <pre className="mono text-[11.5px] text-[var(--color-text-2)] overflow-x-auto
                                rounded-[var(--radius-control)] bg-[var(--color-surface-2)] p-3">
{JSON.stringify(open.evidence, null, 2)}
                </pre>
              </div>
            )}
          </Card>
        </motion.div>
      )}

      <DemoNote>
        Tamper-evident, not tamper-proof. The chain proves these rows are internally
        consistent; it becomes evidence when the head is anchored outside this database.
        Demonstration corpus throughout.
      </DemoNote>
    </div>
  )
}
