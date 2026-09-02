import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  IdentificationCard, Buildings, ShieldWarning, CheckCircle, Prohibit,
  SignOut, Package, Lock,
} from '@phosphor-icons/react'
import { ledger, work, ApiError, type DecisionRow } from '../api'
import { Card, SectionTitle, DemoNote, OrgChip } from '../components/ui'
import { useSession } from '../Session'

/* ══════════════════════════════════════════════════════════════════════════
   Your account.

   This screen exists because of a specific failure: a reviewer clicks Approve,
   the server refuses, and the refusal — however well worded — arrives as a
   surprise. "S. Nair is not certified on 'valve'" is only useful if you
   already knew a certification existed.

   So this is not a profile page. It is the authority model, stated for one
   person, before they hit it. Everything on it is read from the server's own
   answer about who you are; nothing is inferred client-side, because a screen
   that guesses at your permissions and guesses wrong is worse than no screen.

   THE HONEST PART IS THE "CANNOT" COLUMN

   Most account screens list what you can do. The refusals are the interesting
   half here, and they are the half that explains the product: authority is a
   pair — organisation × commodity family — with safety classes layered on top,
   and none of the three is a role. Showing the limits is showing the design.
   ══════════════════════════════════════════════════════════════════════════ */

const ROLE_NOTE: Record<string, string> = {
  REQUESTER: 'May propose a mapping for someone else to decide. Every approval '
           + 'and rejection is refused, whatever the commodity.',
  REVIEWER: 'May approve and reject within their own organisation, and only in '
          + 'the commodity families listed below.',
  STEWARD: 'Owns the dictionary: merges and splits identities across every '
         + 'family — but only within their own organisation.',
  ADMIN: 'Administers accounts and organisations. Deliberately NOT exempt from '
       + 'the cross-organisation rule.',
}

export function Account() {
  const { user, signOut } = useSession()
  const [mine, setMine] = useState<DecisionRow[] | null>(null)
  const [queueCount, setQueueCount] = useState<number | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    ledger.decisions(200)
      .then((d) => setMine(d.decisions.filter((r) => r.actor_id === user.id).slice(0, 12)))
      .catch((e) => setErr(e instanceof ApiError ? e.message : String(e)))
    work.queue(200).then((q) => setQueueCount(q.queue.length)).catch(() => {})
  }, [user])

  // RequireAuth guarantees a user, but the type does not — and an optional
  // chain everywhere below would be noise.
  if (!user) return null

  const families = user.commodity_scope
  const certs = user.class_certifications
  const isReviewer = user.role === 'REVIEWER'
  const boundByFamily = isReviewer   // stewards and admins are above families

  const CAN: string[] = []
  const CANNOT: string[] = []

  CAN.push(`Read the catalogue, the analyser and the relationship map`)
  if (user.role === 'REQUESTER') {
    CAN.push('Propose a mapping for a reviewer to decide')
    CANNOT.push('Approve or reject anything — refused on role, before scope is even considered')
  } else {
    CAN.push(`Approve and reject records belonging to ${user.org_id}`)
    if (boundByFamily) {
      CAN.push(families.length
        ? `Act on these commodity families: ${families.join(', ')}`
        : 'Nothing — your account holds no commodity families')
      CANNOT.push('Act on any commodity family not listed above — an empty scope '
                + 'means none, never all')
    } else {
      CAN.push(`Act on every commodity family, within ${user.org_id}`)
    }
    if (certs.length) {
      CAN.push(`Approve items in these controlled safety classes: ${certs.join(', ')}`)
    } else {
      CANNOT.push('Approve any item in a controlled safety class — you hold no '
                + 'class certifications, so PRESSURE, SOUR and FIRED all refuse')
    }
    if (certs.length) {
      const missing = ['PRESSURE', 'SOUR', 'FIRED'].filter((c) => !certs.includes(c))
      if (missing.length) {
        CANNOT.push(`Approve items in ${missing.join(', ')} — you are not certified for `
                  + `${missing.length > 1 ? 'those classes' : 'that class'}`)
      }
    }
  }
  CANNOT.push(`Touch any record belonging to another organisation — ${user.org_id} is `
            + 'the boundary, and no role is exempt from it')

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: [0.23, 1, 0.32, 1] }}
      className="grid gap-6"
    >
      <section aria-labelledby="acct-h">
        <h1 id="acct-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Your account
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[64ch] leading-relaxed">
          What you may do here is not your role alone. It is your organisation, your
          commodity families and your safety-class certifications together — which is
          why a reviewer can be refused on a record that another reviewer approves.
        </p>
      </section>

      {/* ── identity ──────────────────────────────────────────────────── */}
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="flex items-start gap-3.5 min-w-0">
            <span
              className="grid h-11 w-11 shrink-0 place-items-center rounded-full text-[15px] font-bold"
              style={{ background: 'var(--color-brand-soft)', color: 'var(--color-brand)' }}
              aria-hidden="true"
            >
              {user.name.split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="text-[17px] font-semibold text-[var(--color-text)] leading-tight">
                {user.name}
              </p>
              <p className="mono text-[12px] text-[var(--color-text-3)] mt-0.5 break-all">
                {user.email}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-2.5">
                <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold"
                      style={{ background: 'var(--color-brand-soft)', color: 'var(--color-brand)' }}>
                  <IdentificationCard size={11} weight="fill" aria-hidden="true" />
                  {user.role}
                </span>
                <OrgChip org={user.org_id} />
                <span className="inline-flex items-center gap-1.5 text-[11.5px] text-[var(--color-text-3)]">
                  <Buildings size={11} weight="fill" aria-hidden="true" />
                  {user.org_name}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => signOut()}
            className="press inline-flex items-center gap-2 rounded-[var(--radius-control)]
                       border border-[var(--color-line-strong)] bg-[var(--color-surface)]
                       px-3.5 py-2 text-[13px] font-medium text-[var(--color-text)]
                       hover:bg-[var(--color-surface-2)] cursor-pointer shrink-0"
          >
            <SignOut size={14} weight="bold" aria-hidden="true" />
            Sign out
          </button>
        </div>

        <p className="mt-4 pt-4 border-t border-[var(--color-line)] text-[12.5px] text-[var(--color-text-2)] leading-relaxed">
          {ROLE_NOTE[user.role]}
        </p>
      </Card>

      {/* ── the authority pair ────────────────────────────────────────── */}
      <section aria-labelledby="scope-h">
        <SectionTitle><span id="scope-h">Your authority</span></SectionTitle>
        <div className="grid gap-3 sm:grid-cols-2">
          <Card className="p-5">
            <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
              <Package size={12} weight="fill" aria-hidden="true" />
              Commodity families
            </p>
            {boundByFamily ? (
              families.length ? (
                <div className="flex flex-wrap gap-1.5 mt-2.5">
                  {families.map((f) => (
                    <span key={f}
                          className="rounded-[var(--radius-control)] px-2.5 py-1 text-[12px] font-medium"
                          style={{ background: 'var(--color-surface-3)', color: 'var(--color-text)' }}>
                      {f}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[13px] mt-2.5" style={{ color: 'var(--color-distinct)' }}>
                  None. An empty scope means no families, not all of them — nothing will
                  ever reach your review queue.
                </p>
              )
            ) : (
              <p className="text-[13px] text-[var(--color-text-2)] mt-2.5 leading-relaxed">
                Every family, within {user.org_id}. A {user.role.toLowerCase()} is not
                bound by commodity — but is still bound by organisation.
              </p>
            )}
          </Card>

          <Card className="p-5">
            <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
              <ShieldWarning size={12} weight="fill" aria-hidden="true" />
              Safety-class certifications
            </p>
            {certs.length ? (
              <>
                <div className="flex flex-wrap gap-1.5 mt-2.5">
                  {certs.map((c) => (
                    <span key={c}
                          className="inline-flex items-center gap-1 rounded-[var(--radius-control)] px-2.5 py-1 text-[12px] font-semibold"
                          style={{ background: 'var(--color-unknown-soft)',
                                   color: 'var(--color-unknown)',
                                   border: '1px solid var(--color-unknown-line)' }}>
                      <ShieldWarning size={10} weight="fill" aria-hidden="true" />
                      {c}
                    </span>
                  ))}
                </div>
                <p className="text-[12px] text-[var(--color-text-3)] mt-2.5 leading-relaxed">
                  A controlled class also requires a written justification on every
                  approval. No role grants these — not steward, not administrator.
                </p>
              </>
            ) : (
              <p className="text-[13px] text-[var(--color-text-2)] mt-2.5 leading-relaxed">
                None. Items in PRESSURE, SOUR or FIRED service will refuse your approval
                regardless of your role or your families.
              </p>
            )}
          </Card>
        </div>
      </section>

      {/* ── can / cannot ──────────────────────────────────────────────── */}
      <section aria-labelledby="perm-h">
        <SectionTitle><span id="perm-h">What that means in practice</span></SectionTitle>
        <div className="grid gap-3 sm:grid-cols-2">
          <Card className="p-5">
            <p className="flex items-center gap-2 text-[12.5px] font-semibold mb-3"
               style={{ color: 'var(--color-brand)' }}>
              <CheckCircle size={14} weight="fill" aria-hidden="true" />
              You may
            </p>
            <ul className="grid gap-2 list-none p-0 m-0">
              {CAN.map((c) => (
                <li key={c} className="text-[12.5px] text-[var(--color-text-2)] leading-relaxed
                                       pl-3.5 relative before:content-[''] before:absolute
                                       before:left-0 before:top-[0.5em] before:h-1 before:w-1
                                       before:rounded-full before:bg-[var(--color-brand)]">
                  {c}
                </li>
              ))}
            </ul>
          </Card>

          <Card className="p-5">
            <p className="flex items-center gap-2 text-[12.5px] font-semibold mb-3"
               style={{ color: 'var(--color-distinct)' }}>
              <Prohibit size={14} weight="fill" aria-hidden="true" />
              The server will refuse
            </p>
            <ul className="grid gap-2 list-none p-0 m-0">
              {CANNOT.map((c) => (
                <li key={c} className="text-[12.5px] text-[var(--color-text-2)] leading-relaxed
                                       pl-3.5 relative before:content-[''] before:absolute
                                       before:left-0 before:top-[0.5em] before:h-1 before:w-1
                                       before:rounded-full before:bg-[var(--color-distinct)]">
                  {c}
                </li>
              ))}
            </ul>
          </Card>
        </div>
        <p className="mt-3 flex items-start gap-2 text-[12px] text-[var(--color-text-3)] leading-relaxed">
          <Lock size={12} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
          These are the server's rules, not this screen's. Hiding a button has never
          stopped anything — every one of these is enforced in the API and would refuse
          an identical request sent directly to it.
        </p>
      </section>

      {/* ── activity ──────────────────────────────────────────────────── */}
      <section aria-labelledby="act-h">
        <SectionTitle hint={queueCount !== null ? `${queueCount} waiting for you` : undefined}>
          <span id="act-h">Your decisions</span>
        </SectionTitle>
        {err && (
          <Card className="p-4">
            <p role="alert" className="text-[13.5px]" style={{ color: 'var(--color-distinct)' }}>{err}</p>
          </Card>
        )}
        {!err && mine && mine.length === 0 && (
          <Card className="p-6 text-center">
            <p className="text-[13.5px] text-[var(--color-text-2)]">
              You have not decided anything yet.{' '}
              {queueCount ? (
                <Link to="/platform/review" className="link">Open your review queue</Link>
              ) : 'Nothing is waiting in your queue.'}
            </p>
          </Card>
        )}
        {!err && mine && mine.length > 0 && (
          <Card className="overflow-hidden">
            {mine.map((d) => (
              <div key={d.id}
                   className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3
                              border-b border-[var(--color-line)] last:border-0">
                <span className="mono text-[11.5px] text-[var(--color-text-3)] w-10 shrink-0">
                  #{d.seq}
                </span>
                <span className="text-[12.5px] font-semibold w-[5.5rem] shrink-0"
                      style={{ color: d.kind === 'APPROVE' ? 'var(--color-brand)'
                                     : d.kind === 'REJECT' ? 'var(--color-distinct)'
                                     : 'var(--color-text-2)' }}>
                  {d.kind}
                </span>
                <span className="mono text-[12px] text-[var(--color-text-2)] min-w-0 flex-1 truncate">
                  {d.canonical_id || d.mapping_id || '—'}
                </span>
                <span className="mono text-[11px] text-[var(--color-text-3)]">
                  {new Date(d.at).toLocaleString()}
                </span>
              </div>
            ))}
          </Card>
        )}
      </section>

      <DemoNote>
        A demonstration account on a synthetic corpus. The authority above is real and
        enforced — the organisations and materials it governs are not.
      </DemoNote>
    </motion.div>
  )
}
