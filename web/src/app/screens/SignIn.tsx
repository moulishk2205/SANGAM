import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowRight, ShieldCheck, Warning } from '@phosphor-icons/react'
import { Card, Button, DemoNote } from '../components/ui'
import { useSession } from '../Session'
import { ApiError } from '../api'

/* ══════════════════════════════════════════════════════════════════════════
   Sign in.

   The demo accounts are on the page, one click away, because this is a
   demonstration and hiding them behind a README nobody has open costs a
   reviewer thirty seconds every single time.

   They are listed with their *scope*, not just their name, because the scope is
   the interesting part: signing in as the CPSE-B reviewer and watching an
   approval get refused on a CPSE-A record is the fastest way to understand what
   the authority model actually does. The accounts are chosen to make that
   contrast available in two clicks.
   ══════════════════════════════════════════════════════════════════════════ */

const DEMO_PASSWORD = 'sangam-demo'

const ACCOUNTS = [
  {
    email: 'reviewer.a@sangam.gov.in', name: 'S. Nair', role: 'Reviewer', org: 'CPSE-A',
    scope: 'fastener · pipe · flange, certified PRESSURE',
    can: 'Approves within scope. The FIRED pipes in her queue are refused — '
       + 'she holds PRESSURE, not FIRED.',
  },
  {
    email: 'reviewer.b@sangam.gov.in', name: 'M. Banerjee', role: 'Reviewer', org: 'CPSE-B',
    scope: 'fastener',
    can: 'Cannot approve anything belonging to CPSE-A. That is the guarantee.',
  },
  {
    email: 'steward@sangam.gov.in', name: 'R. Iyer', role: 'Steward', org: 'CPSE-A',
    scope: 'every family, within CPSE-A only',
    can: 'A steward is above families, not above safety classes or '
       + 'organisations. Both of those still refuse.',
  },
  {
    email: 'requester.a@sangam.gov.in', name: 'K. Rao', role: 'Requester', org: 'CPSE-A',
    scope: 'may propose only',
    can: 'Proposes mappings. Every approval attempt is refused.',
  },
  {
    email: 'admin@sangam.gov.in', name: 'Registrar', role: 'Admin', org: 'CPSE-A',
    scope: 'users and organisations',
    can: 'Administers accounts — and is still not exempt from the org rule.',
  },
]

export function SignIn() {
  const { signIn } = useSession()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/platform/review'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const go = async (e: string, p: string) => {
    setBusy(true); setErr(null)
    try {
      await signIn(e, p)
      nav(next, { replace: true })
    } catch (x) {
      setErr(x instanceof ApiError ? x.message : 'Sign-in failed. Is the engine running?')
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1] }}
      className="grid gap-8 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] items-start"
    >
      {/* ── the form ─────────────────────────────────────────────────── */}
      <section aria-labelledby="signin-h">
        <h1 id="signin-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Sign in
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[42ch]">
          The catalogue, the analyser and the relationship map are readable without
          an account. Signing in is what lets you approve.
        </p>

        <Card className="mt-5 p-5" spotlight>
          <form
            onSubmit={(e) => { e.preventDefault(); go(email, password) }}
            className="grid gap-3.5"
          >
            <div className="grid gap-1.5">
              <label htmlFor="email" className="text-[12px] font-medium text-[var(--color-text-2)]">
                Email
              </label>
              <input
                id="email" type="email" autoComplete="username" value={email}
                onChange={(e) => setEmail(e.target.value)} required
                className="mono rounded-[var(--radius-control)] bg-[var(--color-surface-2)]
                           px-3 py-2.5 text-[13px] text-[var(--color-text)] outline-none
                           focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]"
              />
            </div>
            <div className="grid gap-1.5">
              <label htmlFor="password" className="text-[12px] font-medium text-[var(--color-text-2)]">
                Password
              </label>
              <input
                id="password" type="password" autoComplete="current-password" value={password}
                onChange={(e) => setPassword(e.target.value)} required
                className="mono rounded-[var(--radius-control)] bg-[var(--color-surface-2)]
                           px-3 py-2.5 text-[13px] text-[var(--color-text)] outline-none
                           focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]"
              />
            </div>

            {err && (
              <p role="alert" className="flex items-start gap-2 rounded-[var(--radius-control)] px-3 py-2.5 text-[12.5px]"
                 style={{ background: 'var(--color-distinct-soft)', color: 'var(--color-distinct)' }}>
                <Warning size={14} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
                {err}
              </p>
            )}

            <Button type="submit" disabled={busy || !email || !password}
                    icon={<ArrowRight size={15} weight="bold" />}>
              {busy ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </Card>

        <DemoNote>
          Passwords are hashed with PBKDF2-HMAC-SHA256 and a per-user salt. These are
          published demonstration credentials for a synthetic corpus and must never be
          reused anywhere.
        </DemoNote>
      </section>

      {/* ── the accounts ─────────────────────────────────────────────── */}
      <section aria-labelledby="demo-h">
        <div className="flex items-center gap-2 mb-1.5">
          <ShieldCheck size={15} weight="fill" aria-hidden="true" style={{ color: 'var(--color-brand)' }} />
          <h2 id="demo-h" className="text-[13px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
            Demo accounts — one click
          </h2>
        </div>
        <p className="text-[13px] text-[var(--color-text-2)] mb-4 max-w-[62ch]">
          Authority is a pair: <strong className="font-medium">organisation × commodity family</strong>.
          The quickest way to see it is to approve something as S. Nair, then try the
          same thing as M. Banerjee.
        </p>

        <div className="grid gap-2">
          {ACCOUNTS.map((a) => (
            <Card key={a.email} interactive spotlight
                  className="px-4 py-3.5 cursor-pointer"
                  onClick={() => go(a.email, DEMO_PASSWORD)}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[14px] font-semibold text-[var(--color-text)]">
                    {a.name}
                    <span className="ml-2 text-[11px] font-medium text-[var(--color-brand)]">{a.role}</span>
                    <span className="ml-1.5 text-[11px] text-[var(--color-text-3)]">{a.org}</span>
                  </p>
                  <p className="mono text-[11px] text-[var(--color-text-3)] mt-0.5 truncate">{a.email}</p>
                  <p className="text-[12px] text-[var(--color-text-2)] mt-1.5">{a.scope}</p>
                  <p className="text-[12px] text-[var(--color-text-3)] mt-1 leading-snug">{a.can}</p>
                </div>
                <ArrowRight size={14} weight="bold" aria-hidden="true"
                            className="mt-1 shrink-0 text-[var(--color-text-3)]" />
              </div>
            </Card>
          ))}
        </div>

        <p className="mono text-[11.5px] text-[var(--color-text-3)] mt-3">
          password for all: <span className="text-[var(--color-text-2)]">{DEMO_PASSWORD}</span>
        </p>
      </section>
    </motion.div>
  )
}
