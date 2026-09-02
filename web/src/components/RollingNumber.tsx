import { useEffect, useRef } from 'react'
import { prefersReducedMotion } from '../lib/motion'

/* ══════════════════════════════════════════════════════════════════════════
   A figure that arrives by settling rather than by fading in.

   Every digit spins through random values, then locks — left to right, the way
   a mechanical counter or a departure board resolves. Non-digits (%, comma,
   decimal point, "ms") never scramble: they are the shape of the number, and
   shuffling them turns a measurement into noise.

   Left-to-right lock order is the whole trick. Locking all digits at once is a
   fade with extra steps; locking randomly reads as a glitch. Left to right
   reads as *resolving*, because the most significant digit settling first is
   what tells you the magnitude is already known and only the precision is
   still arriving.

   Written straight to the DOM. A 60fps counter driven through React state
   re-renders the subtree on every frame for no benefit — the text node is the
   only thing that changes.

   Reduced motion gets the final value immediately. There is no information in
   the spin; it is pure presentation, so removing it costs the reader nothing.
   ══════════════════════════════════════════════════════════════════════════ */

const GLYPHS = '0123456789'

export function RollingNumber({
  value,
  duration = 1500,
  delay = 0,
  className = '',
}: {
  /** The final string, formatted exactly as it should read: "96.33%", "2,392", "14.5 ms". */
  value: string
  duration?: number
  delay?: number
  className?: string
}) {
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    if (prefersReducedMotion()) {
      el.textContent = value
      return
    }

    const chars = value.split('')
    const digitIdx = chars.map((c, i) => (/\d/.test(c) ? i : -1)).filter((i) => i >= 0)
    if (!digitIdx.length) {
      el.textContent = value
      return
    }

    let raf = 0
    let start = 0
    let done = false

    const frame = (now: number) => {
      if (!start) start = now
      const t = (now - start - delay) / duration

      if (t < 0) {                       // still in the stagger delay
        raf = requestAnimationFrame(frame)
        return
      }
      if (t >= 1) {
        el.textContent = value
        done = true
        return
      }

      // Ease the lock front so digits settle quickly at first and the last
      // couple linger — the same shape as a counter losing momentum.
      const front = (1 - Math.pow(1 - t, 3)) * digitIdx.length
      const out = [...chars]
      digitIdx.forEach((idx, k) => {
        if (k < front) return           // locked
        out[idx] = GLYPHS[(Math.random() * 10) | 0]
      })
      el.textContent = out.join('')
      raf = requestAnimationFrame(frame)
    }

    // Only run when it is actually on screen. A figure that has already spun
    // before the reader arrives has not been seen.
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !done && !raf) {
          raf = requestAnimationFrame(frame)
          io.disconnect()
        }
      },
      { threshold: 0.4 },
    )
    io.observe(el)

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
    }
  }, [value, duration, delay])

  return (
    <span
      ref={ref}
      className={className}
      // Reserved by the real string so the row cannot reflow mid-spin, and
      // tabular figures so the digits do not jitter horizontally as they change.
      style={{ fontVariantNumeric: 'tabular-nums', fontFeatureSettings: '"tnum"' }}
    >
      {value}
    </span>
  )
}
