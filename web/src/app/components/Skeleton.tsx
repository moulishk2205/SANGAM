import { prefersReducedMotion } from '../../lib/motion'

/* ══════════════════════════════════════════════════════════════════════════
   Skeletons that match the shape of what is arriving.

   A centred spinner tells you to wait. A skeleton tells you what you are
   waiting for, and — because it occupies the same box the content will — the
   layout does not jump when the data lands. That reflow is the actual cost of a
   spinner, and it is why every one of these mirrors a real component's
   geometry rather than being a generic grey rectangle.

   The shimmer is a background-position sweep, which composites. It is also the
   one place a purely decorative animation earns its keep: a static grey block
   reads as broken, an animated one reads as pending.
   ══════════════════════════════════════════════════════════════════════════ */

function Bar({ w = '100%', h = 12, className = '' }: { w?: string | number; h?: number; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`skeleton block ${className}`}
      style={{ width: w, height: h, borderRadius: 6 }}
    />
  )
}

/** Wraps any skeleton so assistive tech announces the wait once, not per shape. */
function Region({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div role="status" aria-busy="true" aria-label={label}>
      {children}
      <span className="sr-only">{label}</span>
    </div>
  )
}

/** Matches StatTile: figure, label, note. */
export function StatSkeleton() {
  return (
    <div className="card px-4 py-4 h-full">
      <Bar w={72} h={22} />
      <Bar w={96} h={11} className="mt-3" />
      <Bar w={128} h={10} className="mt-2" />
    </div>
  )
}

export function StatRowSkeleton() {
  return (
    <Region label="Loading catalogue figures">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[0, 1, 2, 3].map((i) => <StatSkeleton key={i} />)}
      </div>
    </Region>
  )
}

/** Matches one row of the canonical list. */
export function ListSkeleton({ rows = 8 }: { rows?: number }) {
  const reduced = prefersReducedMotion()
  return (
    <Region label="Loading materials">
      <div className="card overflow-hidden">
        {Array.from({ length: rows }, (_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 px-4 py-3.5 border-b border-[var(--color-line)] last:border-0"
            // A touch of falloff down the list reads as "still arriving" rather
            // than as eight identical placeholders.
            style={{ opacity: reduced ? 1 : 1 - i * 0.07 }}
          >
            <Bar w={92} h={13} />
            <Bar w="42%" h={13} />
            <span className="ml-auto flex gap-2">
              <Bar w={44} h={16} />
              <Bar w={44} h={16} />
            </span>
          </div>
        ))}
      </div>
    </Region>
  )
}

/** Matches the canonical detail header + attribute grid. */
export function DetailSkeleton() {
  return (
    <Region label="Loading material">
      <div className="grid gap-6">
        <div>
          <Bar w={120} h={14} />
          <Bar w="62%" h={26} className="mt-3" />
          <Bar w="38%" h={13} className="mt-3" />
        </div>
        <div className="card p-5 grid gap-3">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="grid grid-cols-[8rem_1fr] gap-4 items-center">
              <Bar w={96} h={11} />
              <Bar w={`${58 - i * 6}%`} h={13} />
            </div>
          ))}
        </div>
      </div>
    </Region>
  )
}
