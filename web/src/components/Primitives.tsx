import type { ReactNode } from 'react'

/** Page gutter + max measure. One container rule for the whole page. */
export function Shell({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`mx-auto w-full max-w-[1240px] px-[var(--shell)] ${className}`}>{children}</div>
  )
}

/**
 * A section. Every section is a landmark with its own heading, so the page has
 * a real document outline rather than 35 h1s.
 */
export function Section({
  id,
  labelledBy,
  children,
  className = '',
  ground = 'void',
}: {
  id: string
  labelledBy: string
  children: ReactNode
  className?: string
  ground?: 'void' | 'raised' | 'paper'
}) {
  const bg =
    ground === 'paper' ? 'bg-paper text-ink' : ground === 'raised' ? 'bg-raised' : 'bg-void'
  return (
    <section
      id={id}
      aria-labelledby={labelledBy}
      className={`relative py-24 md:py-36 ${bg} ${className}`}
    >
      {children}
    </section>
  )
}

/**
 * Masked line reveal. Each line sits in its own clipping box so type rises
 * from behind a hard edge. Lines are passed explicitly, which keeps the break
 * points deterministic instead of depending on measurement after font load.
 */
export function Lines({
  lines,
  className = '',
  as: Tag = 'p',
  id,
}: {
  lines: string[]
  className?: string
  as?: 'h1' | 'h2' | 'h3' | 'p'
  id?: string
}) {
  return (
    <Tag id={id} className={className} data-reveal>
      {lines.map((line, i) => (
        <span key={i} className="line-mask">
          <span className="block js-line" style={{ willChange: 'transform' }}>
            {line}
          </span>
        </span>
      ))}
    </Tag>
  )
}

/**
 * Small uppercase mono label above a heading.
 *
 * Deliberately rationed. An eyebrow on every section produces the templated
 * rhythm that makes generated pages recognisable, so this is used on three
 * sections out of twelve and nowhere else.
 */
export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="t-label text-graphite mb-6" data-reveal>{children}</p>
}

/** A provenance note. Every measured figure on the page carries one. */
export function Provenance({ children }: { children: ReactNode }) {
  return (
    <p className="t-datum text-[11px] text-graphite mt-8 max-w-[60ch] leading-relaxed" data-reveal>
      {children}
    </p>
  )
}
