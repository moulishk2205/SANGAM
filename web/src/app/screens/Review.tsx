import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'motion/react'
import {
  CheckCircle, XCircle, ShieldWarning, Prohibit, ArrowClockwise, Info,
} from '@phosphor-icons/react'
import { work, ledger, ApiError, type QueueItem } from '../api'
import { Card, Button, DemoNote, NmcTag, OrgChip } from '../components/ui'
import { ListSkeleton } from '../components/Skeleton'
import { useSession } from '../Session'

/* ══════════════════════════════════════════════════════════════════════════
   The review queue.

   This is the screen that separates a matcher from a system: somewhere a person
   is accountable for what the engine proposed. Everything else in the platform
   reads; this is where a decision is made and a certificate is written.

   THE QUEUE IS SCOPED, NOT FILTERED

   The server returns only what this reviewer may act on — their organisation,
   their commodity families. It is not a global list with the rest greyed out,
   because a queue you cannot clear is not a queue. A reviewer with no scope
   correctly sees nothing.

   REFUSALS ARE THE INTERESTING OUTPUT

   When the server refuses, the reason is shown verbatim next to the item rather
   than as a toast that disappears. "S. Nair is not certified on 'valve'. Scope
   held: fastener, pipe, flange." is the product explaining its own authority
   model, and it is worth more on screen than a red X.
   ══════════════════════════════════════════════════════════════════════════ */

type Outcome = { kind: 'approved' | 'rejected' | 'refused'; message: string }

export function Review() {
  const { user } = useSession()

  const [items, setItems] = useState<QueueItem[]>([])
  const [scope, setScope] = useState<{ org: string; commodity: string[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [outcome, setOutcome] = useState<Record<string, Outcome>>({})
  const [chain, setChain] = useState<{ ok: boolean; checked: number } | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    work.queue(25)
      .then((r) => { setItems(r.queue); setScope(r.scope); setErr(null) })
      .catch((e) => setErr(e instanceof ApiError ? e.message : String(e)))
      .finally(() => setLoading(false))
  }, [])

  // No redirect here any more: RequireAuth wraps this route, so by the time
  // the screen renders there is a user. The hand-rolled bounce that used to
  // live here also hardcoded its own `next`, which meant arriving from
  // anywhere else lost the destination.
  useEffect(() => {
    load()
    ledger.verify().then((v) => setChain({ ok: v.ok, checked: v.checked })).catch(() => {})
  }, [load])

  const act = async (item: QueueItem, kind: 'approve' | 'reject') => {
    const note = (notes[item.mapping_id] || '').trim()
    setBusy(item.mapping_id)
    try {
      if (kind === 'approve') await work.approve(item.mapping_id, note)
      else await work.reject(item.mapping_id, note)
      setOutcome((o) => ({ ...o, [item.mapping_id]: {
        kind: kind === 'approve' ? 'approved' : 'rejected',
        message: kind === 'approve'
          ? 'Approved. A certificate has been written.'
          : 'Rejected. The reason is on the record.',
      } }))
      // Refresh the chain length so the certificate count visibly moves.
      ledger.verify().then((v) => setChain({ ok: v.ok, checked: v.checked })).catch(() => {})
    } catch (e) {
      setOutcome((o) => ({ ...o, [item.mapping_id]: {
        kind: 'refused',
        message: e instanceof ApiError ? e.message : 'That did not work.',
      } }))
    } finally {
      setBusy(null)
    }
  }

  if (!user) return <ListSkeleton rows={4} />   // unreachable behind the gate; satisfies the type

  return (
    <div className="grid gap-6">
      <section aria-labelledby="review-h">
        <h1 id="review-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Review queue
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[64ch]">
          Proposals awaiting a decision, scoped to what you may actually act on. Every
          approval and rejection writes a certificate that freezes the evidence, the
          artefact versions and the scope you held at that moment.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12.5px]">
          <span className="text-[var(--color-text-3)]">
            Signed in as <strong className="font-medium text-[var(--color-text)]">{user.name}</strong>
            {' · '}{user.role}{' · '}{user.org_id}
          </span>
          {scope && (
            <span className="text-[var(--color-text-3)]">
              Families: {scope.commodity.length
                ? scope.commodity.join(', ')
                : <em className="not-italic">none — nothing will appear below</em>}
            </span>
          )}
          {user.class_certifications.length > 0 && (
            <span className="inline-flex items-center gap-1.5 text-[var(--color-text-3)]">
              <ShieldWarning size={13} weight="fill" aria-hidden="true"
                             style={{ color: 'var(--color-unknown)' }} />
              Certified: {user.class_certifications.join(', ')}
            </span>
          )}
          {chain && (
            <span className="mono text-[11.5px]"
                  style={{ color: chain.ok ? 'var(--color-brand)' : 'var(--color-distinct)' }}>
              chain {chain.ok ? 'verified' : 'BROKEN'} · {chain.checked} certificates
            </span>
          )}
          <button onClick={load}
                  className="press link inline-flex items-center gap-1.5 text-[12.5px] cursor-pointer">
            <ArrowClockwise size={12} weight="bold" aria-hidden="true" /> Refresh
          </button>
        </div>
      </section>

      {err && (
        <Card className="p-4">
          <p role="alert" className="text-[13.5px]" style={{ color: 'var(--color-distinct)' }}>{err}</p>
        </Card>
      )}

      {loading && <ListSkeleton rows={5} />}

      {!loading && items.length === 0 && !err && (
        <Card className="p-8 text-center">
          <p className="text-[14.5px] font-semibold">Nothing waiting for you</p>
          <p className="text-[13px] text-[var(--color-text-2)] mt-1.5 max-w-[52ch] mx-auto leading-relaxed">
            {scope && scope.commodity.length === 0
              ? 'Your account holds no commodity families, so no proposal can reach this queue. '
                + 'An empty scope means no families, not all of them.'
              : 'Every proposal in your scope has been decided. Run an analysis and propose '
                + 'a mapping to put something here.'}
          </p>
          <div className="mt-4 inline-block">
            <Link to="/platform/analyse"><Button variant="ghost">Go to Analyse</Button></Link>
          </div>
        </Card>
      )}

      <div className="grid gap-3">
        <AnimatePresence initial={false}>
          {items.map((it) => {
            const res = outcome[it.mapping_id]
            const done = res && res.kind !== 'refused'
            return (
              <motion.div
                key={it.mapping_id}
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.24, ease: [0.23, 1, 0.32, 1] }}
              >
                <Card spotlight className="p-4 md:p-5"
                      style={done ? { background: res.kind === 'approved'
                        ? 'var(--color-brand-ambient)' : 'var(--color-distinct-ambient)' } : undefined}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <OrgChip org={it.org} />
                        <span className="mono text-[11.5px] text-[var(--color-text-3)]">{it.org_code}</span>
                        <span className="text-[11px] text-[var(--color-text-3)]">{it.family}</span>
                        {it.item_class !== 'GENERAL' && (
                          <span className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10.5px] font-semibold"
                                style={{ color: 'var(--color-unknown)',
                                         background: 'var(--color-unknown-soft)',
                                         borderColor: 'var(--color-unknown-line)' }}>
                            <ShieldWarning size={10} weight="fill" aria-hidden="true" />
                            {it.item_class}
                          </span>
                        )}
                      </div>
                      <p className="mono text-[13.5px] text-[var(--color-text)] mt-2">{it.description}</p>
                      <p className="text-[12px] text-[var(--color-text-3)] mt-1.5">
                        proposed as{' '}
                        <Link to={`/platform/material/${it.canonical_id}`} className="link">
                          {it.canonical_id}
                        </Link>
                        {' — '}<span className="mono">{it.canonical_text}</span>
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <NmcTag id={it.canonical_id} size="sm" />
                      <p className="mono text-[11.5px] text-[var(--color-text-3)] mt-1.5">
                        {it.confidence.toFixed(4)}
                      </p>
                      <p className="text-[10.5px] text-[var(--color-text-3)]">uncalibrated</p>
                    </div>
                  </div>

                  {!done && (
                    <div className="mt-4 grid gap-2.5">
                      <label htmlFor={`n-${it.mapping_id}`} className="sr-only">
                        Reason for this decision
                      </label>
                      <input
                        id={`n-${it.mapping_id}`}
                        value={notes[it.mapping_id] || ''}
                        onChange={(e) => setNotes((n) => ({ ...n, [it.mapping_id]: e.target.value }))}
                        placeholder={it.item_class !== 'GENERAL'
                          ? `${it.item_class} class — a justification is required`
                          : 'Reason (required to reject; recorded on the certificate)'}
                        className="rounded-[var(--radius-control)] bg-[var(--color-surface-2)]
                                   px-3 py-2.5 text-[13px] text-[var(--color-text)] outline-none
                                   focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]"
                      />
                      <div className="flex flex-wrap items-center gap-2">
                        <Button onClick={() => act(it, 'approve')}
                                disabled={busy === it.mapping_id}
                                icon={<CheckCircle size={14} weight="fill" />}>
                          Approve
                        </Button>
                        <Button variant="ghost" onClick={() => act(it, 'reject')}
                                disabled={busy === it.mapping_id}
                                icon={<XCircle size={14} weight="fill" />}>
                          Reject
                        </Button>
                        {!it.you_may_approve && (
                          <span className="inline-flex items-center gap-1.5 text-[12px]"
                                style={{ color: 'var(--color-unknown)' }}>
                            <Info size={12} weight="fill" aria-hidden="true" />
                            You are not certified for {it.item_class}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {res && (
                    <p className="mt-3 flex items-start gap-2 text-[12.5px] leading-relaxed"
                       style={{ color: res.kind === 'refused' ? 'var(--color-distinct)'
                         : res.kind === 'approved' ? 'var(--color-brand)' : 'var(--color-text-2)' }}>
                      {res.kind === 'refused'
                        ? <Prohibit size={13} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
                        : <CheckCircle size={13} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />}
                      {res.message}
                    </p>
                  )}
                </Card>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      <DemoNote>
        Demonstration corpus. Approving here writes a real row and a real certificate —
        restart the engine and the decision is still there. Authority is enforced server
        side: the buttons are not what stops an out-of-scope approval.
      </DemoNote>
    </div>
  )
}
