import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ArrowRight, ShieldCheck, Warning, Lock, Cube, Info,
} from '@phosphor-icons/react'
import { Card, Button } from '../components/ui'
import { useSession } from '../Session'
import { ApiError } from '../api'

/* ══════════════════════════════════════════════════════════════════════════
   Sign in — the only door.

   Nothing in the platform is readable without a session any more, so this is
   not a gate in front of the write actions; it is the entrance. That changes
   what the screen has to do: it has to establish, in about two seconds, whose
   system this is and what kind of system it is.

   WHY IT LOOKS LIKE A GOVERNMENT SCREEN

   Because it is one, and the audience knows the genre. A CPSE procurement
   officer has signed into a dozen departmental systems and reads the
   vocabulary instantly: the tricolour rule, the bilingual ministry line, the
   restricted-use notice, the sober type. Borrowing that vocabulary is not
   decoration — it is the fastest way to say "this governs your material
   master" without a paragraph of explanation.

   WHAT IS DELIBERATELY ABSENT: THE STATE EMBLEM

   No Ashoka pillar. Use of the State Emblem of India is restricted by the
   State Emblem of India (Prohibition of Improper Use) Act, 2005, to the
   authorities the Act names; a hackathon entry is not one of them, and
   rendering it would be an offence rather than a flourish. The SANGAM mark
   stands in its place, which is also more honest: this is a proposal, and the
   mark should be the proposal's own.

   AND WHY IT SAYS "DEMONSTRATION" ABOVE THE FOLD

   The same authenticity that makes the screen legible would make it a
   convincing forgery, so the demonstration banner is not a disclaimer buried
   in a footer — it sits before the form, in the highest contrast the palette
   allows. A viewer must never be able to mistake this for a live government
   portal, and looking too real is the one failure mode this screen has that
   the others do not.
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

/** Saffron, white, green. A 3px rule, not a decorative band. */
function Tricolour() {
  return (
    <div aria-hidden="true" className="flex h-[3px] w-full overflow-hidden rounded-full">
      <span className="flex-1" style={{ background: '#FF9933' }} />
      <span className="flex-1" style={{ background: '#FFFFFF' }} />
      <span className="flex-1" style={{ background: '#138808' }} />
    </div>
  )
}

export function SignIn() {
  const { signIn } = useSession()
  const nav = useNavigate()
  const [params] = useSearchParams()
  // Only ever an in-app path. An absolute URL here would make the sign-in
  // screen an open redirect: ?next=https://elsewhere would send a freshly
  // authenticated user off-site on someone else's link.
  const raw = params.get('next') || '/platform'
  const next = raw.startsWith('/platform') ? raw : '/platform'

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

  const field = `mono rounded-[var(--radius-control)] bg-[var(--color-surface-2)]
                 border border-[var(--color-line)]
                 px-3 py-2.5 text-[13.5px] text-[var(--color-text)] outline-none
                 focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]
                 focus-visible:border-transparent`

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1] }}
      className="grid gap-7"
    >
      {/* ── national identity strip ──────────────────────────────────────
          The bilingual line first, the tricolour beneath it: this is the
          arrangement every departmental portal uses, and getting the order
          wrong is the tell that someone copied the look without knowing it. */}
      <header className="grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
          <div className="min-w-0">
            <p className="text-[12.5px] font-medium text-[var(--color-text-2)] leading-snug">
              <span lang="hi">भारत सरकार</span>
              <span aria-hidden="true" className="mx-2 text-[var(--color-text-3)]">·</span>
              Government of India
            </p>
            <p className="text-[15px] font-semibold text-[var(--color-text)] leading-snug mt-0.5"
               lang="hi">
              पेट्रोलियम एवं प्राकृतिक गैस मंत्रालय
            </p>
            <p className="text-[13px] text-[var(--color-text-2)] leading-snug">
              Ministry of Petroleum and Natural Gas
              <span aria-hidden="true" className="mx-1.5 text-[var(--color-text-3)]">·</span>
              Chennai Petroleum Corporation Limited
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <span
              className="grid h-10 w-10 place-items-center rounded-lg"
              style={{ background: 'var(--color-brand)', color: 'var(--color-on-brand)' }}
              aria-hidden="true"
            >
              <Cube size={20} weight="fill" />
            </span>
            <span className="leading-tight">
              <span className="block text-[16px] font-bold tracking-[0.02em] text-[var(--color-text)]">
                SANGAM
              </span>
              <span className="block text-[11px] text-[var(--color-text-3)]">
                Material Intelligence · SIH26099
              </span>
            </span>
          </div>
        </div>
        <Tricolour />
      </header>

      {/* ── the honesty banner ───────────────────────────────────────────
          Above the fold and before the form, because the screen's whole job
          below this line is to look convincingly official. */}
      <div
        className="flex items-start gap-2.5 rounded-[var(--radius-control)] px-4 py-3"
        style={{
          background: 'var(--color-unknown-soft)',
          border: '1px solid var(--color-unknown-line)',
        }}
      >
        <Info size={15} weight="fill" aria-hidden="true"
              className="mt-0.5 shrink-0" style={{ color: 'var(--color-unknown)' }} />
        <p className="text-[12.5px] leading-relaxed" style={{ color: 'var(--color-unknown)' }}>
          <strong className="font-semibold">Demonstration system.</strong> Built for Smart
          India Hackathon 2026, problem statement SIH26099. It is not a live Government
          of India service, holds no real procurement data, and issues no credential that
          means anything outside this prototype. Every organisation, material and account
          below is synthetic.
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,25rem)_minmax(0,1fr)] items-start">
        {/* ── the form ───────────────────────────────────────────────── */}
        <section aria-labelledby="signin-h">
          <h1 id="signin-h"
              className="text-[clamp(1.4rem,3vw,1.85rem)] font-bold tracking-[-0.02em] leading-tight">
            Authorised sign-in
          </h1>
          <p className="mt-2 text-[13.5px] text-[var(--color-text-2)] max-w-[40ch] leading-relaxed">
            Access to the material catalogue, the analyser and the decision ledger
            requires an account. There is no anonymous view.
          </p>

          <Card className="mt-5 p-5" spotlight>
            <form
              onSubmit={(e) => { e.preventDefault(); go(email, password) }}
              className="grid gap-3.5"
            >
              <div className="grid gap-1.5">
                <label htmlFor="email" className="text-[12px] font-medium text-[var(--color-text-2)]">
                  Registered email
                </label>
                <input
                  id="email" type="email" autoComplete="username" value={email}
                  onChange={(e) => setEmail(e.target.value)} required
                  autoCapitalize="none" spellCheck={false}
                  className={field}
                />
              </div>
              <div className="grid gap-1.5">
                <label htmlFor="password" className="text-[12px] font-medium text-[var(--color-text-2)]">
                  Password
                </label>
                <input
                  id="password" type="password" autoComplete="current-password" value={password}
                  onChange={(e) => setPassword(e.target.value)} required
                  className={field}
                />
              </div>

              {err && (
                <p role="alert"
                   className="flex items-start gap-2 rounded-[var(--radius-control)] px-3 py-2.5 text-[12.5px]"
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

          {/* ── restricted-use notice ─────────────────────────────────
              Conventional furniture on a departmental system, and true of
              this one: every action really is written to an audit trail. */}
          <div className="mt-4 flex items-start gap-2.5">
            <Lock size={13} weight="fill" aria-hidden="true"
                  className="mt-0.5 shrink-0" style={{ color: 'var(--color-text-3)' }} />
            <p className="text-[11.5px] leading-relaxed text-[var(--color-text-3)]">
              Restricted system. Access is limited to authorised personnel of the
              participating organisations. All sign-ins, approvals and rejections are
              recorded against your account in an audit trail you cannot edit. Do not
              share credentials.
            </p>
          </div>

          <p className="mt-3 text-[11.5px] leading-relaxed text-[var(--color-text-3)]">
            Passwords are stored as PBKDF2-HMAC-SHA256 digests with a per-account salt,
            never in plain text. The credentials opposite are published demonstration
            logins for a synthetic corpus and must never be reused anywhere.
          </p>
        </section>

        {/* ── the demo accounts ────────────────────────────────────────── */}
        <section aria-labelledby="demo-h">
          <div className="flex items-center gap-2 mb-1.5">
            <ShieldCheck size={15} weight="fill" aria-hidden="true"
                         style={{ color: 'var(--color-brand)' }} />
            <h2 id="demo-h"
                className="text-[13px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)]">
              Demonstration accounts — one click
            </h2>
          </div>
          <p className="text-[13px] text-[var(--color-text-2)] mb-4 max-w-[62ch] leading-relaxed">
            Authority here is a pair: <strong className="font-medium">organisation ×
            commodity family</strong>, with safety classes on top. The quickest way to
            see it is to approve something as S. Nair, then try the same thing as
            M. Banerjee.
          </p>

          <ul className="grid gap-2 list-none p-0 m-0">
            {ACCOUNTS.map((a) => (
              <li key={a.email}>
                <Card interactive spotlight
                      className="px-4 py-3.5 cursor-pointer"
                      onClick={() => go(a.email, DEMO_PASSWORD)}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-[var(--color-text)]">
                        {a.name}
                        <span className="ml-2 text-[11px] font-medium text-[var(--color-brand)]">
                          {a.role}
                        </span>
                        <span className="ml-1.5 text-[11px] text-[var(--color-text-3)]">{a.org}</span>
                      </p>
                      <p className="mono text-[11px] text-[var(--color-text-3)] mt-0.5 truncate">
                        {a.email}
                      </p>
                      <p className="text-[12px] text-[var(--color-text-2)] mt-1.5">{a.scope}</p>
                      <p className="text-[12px] text-[var(--color-text-3)] mt-1 leading-snug">{a.can}</p>
                    </div>
                    <ArrowRight size={14} weight="bold" aria-hidden="true"
                                className="mt-1 shrink-0 text-[var(--color-text-3)]" />
                  </div>
                </Card>
              </li>
            ))}
          </ul>

          <p className="mono text-[11.5px] text-[var(--color-text-3)] mt-3">
            password for all: <span className="text-[var(--color-text-2)]">{DEMO_PASSWORD}</span>
          </p>
        </section>
      </div>

      {/* ── footer furniture ─────────────────────────────────────────── */}
      <footer className="border-t border-[var(--color-line)] pt-4 mt-1">
        <p className="text-[11.5px] text-[var(--color-text-3)] leading-relaxed">
          SANGAM · Smart India Hackathon 2026 · Problem statement SIH26099 ·
          Ministry of Petroleum and Natural Gas / Chennai Petroleum Corporation Limited.
          A student prototype, unaffiliated with and not endorsed by any Government of
          India body.
        </p>
      </footer>
    </motion.div>
  )
}
