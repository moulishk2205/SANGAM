import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowLeft, MagnifyingGlass, Stack, Graph } from '@phosphor-icons/react'
import { Card } from '../components/ui'

/* ══════════════════════════════════════════════════════════════════════════
   404.

   Wayfinding asks four questions of every screen: where am I, where can I go,
   what is there, how do I get out. A dead route previously answered none of
   them — it rendered the shell with an empty content area, which reads as a
   broken build rather than as a wrong address.

   So this says plainly what happened, prints the path that failed (a reader who
   mistyped can see where), and offers the three real destinations by name. No
   apology, no "Oops".
   ══════════════════════════════════════════════════════════════════════════ */

const PLACES = [
  { to: '/platform',                Icon: Stack,           t: 'Overview',      d: 'Catalogue figures and the place to start an analysis' },
  { to: '/platform/analyse',        Icon: MagnifyingGlass, t: 'Analyse',       d: 'Run a description through the engine, stage by stage' },
  { to: '/platform/visualization',  Icon: Graph,           t: 'Relationships', d: 'How one material sits against everything retrieved' },
]

export function NotFound() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: [0.23, 1, 0.32, 1] }}
      className="grid gap-8 max-w-[64ch]"
    >
      <div>
        <p className="mono text-[12px] uppercase tracking-[0.08em] text-[var(--color-text-3)]">
          404
        </p>
        <h1 className="mt-2 text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          There is nothing at this address.
        </h1>
        <p className="mt-3 text-[14px] text-[var(--color-text-2)]">
          The link may be out of date, or the path may be mistyped. Nothing has gone wrong
          with the engine — it is still running.
        </p>
        <p className="mono mt-3 text-[12px] text-[var(--color-text-3)] break-all">
          {typeof window !== 'undefined' ? window.location.pathname : ''}
        </p>
      </div>

      <div className="grid gap-2">
        {PLACES.map(({ to, Icon, t, d }) => (
          <Link key={to} to={to} className="press block">
            <Card interactive spotlight className="flex items-center gap-3.5 px-4 py-3.5">
              <span
                className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px]"
                style={{ background: 'var(--color-brand-soft)', color: 'var(--color-brand)' }}
                aria-hidden="true"
              >
                <Icon size={17} weight="fill" />
              </span>
              <span className="min-w-0">
                <span className="block text-[14px] font-semibold text-[var(--color-text)]">{t}</span>
                <span className="block text-[12px] text-[var(--color-text-3)] mt-0.5">{d}</span>
              </span>
              <ArrowLeft
                size={14} weight="bold" aria-hidden="true"
                className="ml-auto shrink-0 rotate-180 text-[var(--color-text-3)]"
              />
            </Card>
          </Link>
        ))}
      </div>
    </motion.div>
  )
}
