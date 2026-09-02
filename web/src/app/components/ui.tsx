import { useRef, type ReactNode, type MouseEvent, type CSSProperties } from 'react'
import { motion } from 'motion/react'
import { CheckCircle, XCircle, Question, Prohibit } from '@phosphor-icons/react'
import type { Decision, Verdict } from '../api'

/* ══════════════════════════════════════════════════════════════════════════
   Shared UI. Small, boring, and used everywhere, which is what keeps a dense
   application feeling like one product rather than a set of pages.
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Card with a cursor-tracking highlight.
 *
 * The radial follows the pointer via CSS custom properties written on
 * mousemove. Deliberately not React state: storing pointer position in state
 * re-renders the tree on every frame and collapses on a long list.
 */
export function Card({
  children, className = '', interactive = false, spotlight = false, onClick, as = 'div', style,
}: {
  children: ReactNode; className?: string; interactive?: boolean
  spotlight?: boolean; onClick?: () => void; as?: 'div' | 'article' | 'li'
  /** Used for ambient semantic surfaces, e.g. a selected candidate. */
  style?: CSSProperties
}) {
  const ref = useRef<HTMLDivElement>(null)
  const track = (e: MouseEvent) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    el.style.setProperty('--mx', `${e.clientX - r.left}px`)
    el.style.setProperty('--my', `${e.clientY - r.top}px`)
  }
  const Tag = as as 'div'
  return (
    <Tag
      ref={ref}
      onMouseMove={spotlight ? track : undefined}
      onClick={onClick}
      style={style}
      className={`card ${interactive ? 'card-interactive' : ''} ${spotlight ? 'spotlight' : ''} ${className}`}
    >
      {children}
    </Tag>
  )
}

export function SectionTitle({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 mb-3">
      <h2 className="text-[13px] font-semibold tracking-[0.06em] uppercase text-[var(--color-text-3)]">
        {children}
      </h2>
      {hint && <span className="text-[12px] text-[var(--color-text-3)]">{hint}</span>}
    </div>
  )
}

const DECISION = {
  MATCH:           { label: 'Match',           fg: 'var(--color-brand)',    bg: 'var(--color-brand-soft)',    bd: 'var(--color-brand-line)',    Icon: CheckCircle },
  NEAR_MATCH:      { label: 'Near match',      fg: 'var(--color-unknown)',  bg: 'var(--color-unknown-soft)',  bd: 'var(--color-unknown-line)',  Icon: Question },
  REVIEW_REQUIRED: { label: 'Review required', fg: 'var(--color-unknown)',  bg: 'var(--color-unknown-soft)',  bd: 'var(--color-unknown-line)',  Icon: Question },
  DISTINCT:        { label: 'Distinct',        fg: 'var(--color-distinct)', bg: 'var(--color-distinct-soft)', bd: 'var(--color-distinct-line)', Icon: XCircle },
} as const

/**
 * Decision pill.
 *
 * Icon, word and colour together. Colour is the third signal and never the
 * only one, so the verdict survives colour-blindness, a bad projector and a
 * screen reader.
 */
export function DecisionBadge({ decision, size = 'md' }: { decision: Decision; size?: 'sm' | 'md' }) {
  const d = DECISION[decision]
  const pad = size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-1 text-[12px] gap-1.5'
  return (
    <span
      className={`inline-flex items-center rounded-full border font-semibold ${pad}`}
      style={{ color: d.fg, background: d.bg, borderColor: d.bd }}
    >
      <d.Icon size={size === 'sm' ? 12 : 14} weight="fill" aria-hidden="true" />
      {d.label}
    </span>
  )
}

const VERDICT = {
  AGREE:    { fg: 'var(--color-brand)',    Icon: CheckCircle, word: 'Agree' },
  DISAGREE: { fg: 'var(--color-distinct)', Icon: XCircle,     word: 'Disagree' },
  UNKNOWN:  { fg: 'var(--color-text-3)',    Icon: Question,    word: 'Not stated' },
} as const

export function VerdictMark({ verdict }: { verdict: Verdict }) {
  const v = VERDICT[verdict]
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium" style={{ color: v.fg }}>
      <v.Icon size={14} weight="fill" aria-hidden="true" />
      {v.word}
    </span>
  )
}

/** A copyable canonical identifier. Mono, because it is a machine identifier. */
export function NmcTag({ id, size = 'md' }: { id: string; size?: 'sm' | 'md' }) {
  return (
    <span
      className={`mono inline-flex items-center rounded-md border font-medium
                  ${size === 'sm' ? 'px-1.5 py-0.5 text-[11px]' : 'px-2 py-1 text-[12px]'}`}
      style={{
        color: 'var(--color-info)',
        background: 'var(--color-info-soft)',
        borderColor: 'var(--color-info-line)',
      }}
    >
      {id}
    </span>
  )
}

export function OrgChip({ org }: { org: string }) {
  return (
    <span className="inline-flex items-center rounded-md bg-[var(--color-surface-3)] px-1.5 py-0.5
                     text-[11px] font-semibold text-[var(--color-text-2)]">
      {org}
    </span>
  )
}

export function Button({
  children, onClick, type = 'button', variant = 'primary', disabled, className = '', icon,
}: {
  children: ReactNode; onClick?: () => void; type?: 'button' | 'submit'
  variant?: 'primary' | 'ghost' | 'quiet'; disabled?: boolean; className?: string; icon?: ReactNode
}) {
  const styles = {
    // Not text-white: on the dark theme the accent lightens and white on it
    // measures 2.62:1. The token carries dark ink there instead.
    primary: 'border-transparent',
    ghost: 'bg-[var(--color-surface)] text-[var(--color-text)] border-[var(--color-line-strong)] hover:bg-[var(--color-surface-2)]',
    quiet: 'bg-transparent text-[var(--color-text-2)] border-transparent hover:bg-[var(--color-surface-3)]',
  }[variant]
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={variant === 'primary'
        ? { background: 'var(--color-brand)', color: 'var(--color-on-brand)' }
        : undefined}
      className={`press inline-flex items-center justify-center gap-2 rounded-lg border
                  px-4 py-2.5 text-[14px] font-semibold cursor-pointer ${styles} ${className}`}
      onMouseEnter={(e) => {
        if (variant === 'primary') e.currentTarget.style.background = 'var(--color-brand-hover)'
      }}
      onMouseLeave={(e) => {
        if (variant === 'primary') e.currentTarget.style.background = 'var(--color-brand)'
      }}
    >
      {children}
      {icon}
    </button>
  )
}

/** A single figure. Used on the home screen; never with an invented number. */
export function StatTile({
  value, label, note, tone = 'neutral', delay = 0,
}: {
  value: string; label: string; note?: string
  tone?: 'neutral' | 'brand' | 'info'; delay?: number
}) {
  const fg = tone === 'brand' ? 'var(--color-brand)' : tone === 'info' ? 'var(--color-info)' : 'var(--color-text)'
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.34, delay, ease: [0.23, 1, 0.32, 1] }}
    >
      <Card spotlight className="px-4 py-4 h-full">
        <p className="mono text-[26px] leading-none font-semibold" style={{ color: fg }}>{value}</p>
        <p className="text-[13px] font-medium text-[var(--color-text)] mt-2">{label}</p>
        {note && <p className="text-[12px] text-[var(--color-text-3)] mt-0.5">{note}</p>}
      </Card>
    </motion.div>
  )
}

export function VetoNotice({ reason }: { reason: string }) {
  return (
    <div
      className="flex items-start gap-2.5 rounded-lg border px-3.5 py-3"
      style={{
        background: 'var(--color-distinct-soft)',
        borderColor: 'var(--color-distinct-line)',
        color: 'var(--color-distinct)',
      }}
    >
      <Prohibit size={16} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
      <div>
        <p className="text-[13px] font-semibold">Rejected by critical attribute check</p>
        <p className="text-[13px] mt-0.5 opacity-90">{reason}</p>
      </div>
    </div>
  )
}

/** Demo-data disclosure. Present on every screen that shows figures. */
export function DemoNote({ children }: { children: ReactNode }) {
  return (
    <p className="text-[12px] leading-relaxed text-[var(--color-text-3)] max-w-[76ch]">
      {children}
    </p>
  )
}
