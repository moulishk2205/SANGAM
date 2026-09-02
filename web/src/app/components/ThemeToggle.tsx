import { useEffect, useState } from 'react'
import { Sun, Moon, Desktop } from '@phosphor-icons/react'

/* ══════════════════════════════════════════════════════════════════════════
   Theme control — three states, not two.

   A two-way switch has no way to say "follow the system", which is the setting
   most people actually want and the one a plain toggle silently overrides the
   first time it is touched. So: Light / System / Dark, with System the default
   until someone chooses otherwise.

   An explicit choice stamps `data-theme` on <html>. System stamps nothing and
   lets `prefers-color-scheme` decide, which is why the CSS has to carry the
   un-stamped case as well as both stamped ones.

   A segmented control rather than a sun/moon button: it shows the three states
   and which one is active, where a cycling icon button shows neither.
   ══════════════════════════════════════════════════════════════════════════ */

type Choice = 'light' | 'system' | 'dark'
const KEY = 'sangam-theme'

const OPTIONS: { v: Choice; Icon: typeof Sun; label: string }[] = [
  { v: 'light', Icon: Sun, label: 'Light' },
  { v: 'system', Icon: Desktop, label: 'Match system' },
  { v: 'dark', Icon: Moon, label: 'Dark' },
]

/** Reads the stored choice. Safe in every failure mode — a private window, a
 *  browser with site data blocked, or a first visit all fall back to system. */
export function storedChoice(): Choice {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

/**
 * Force the themed subtree to re-resolve.
 *
 * WebKit does not invalidate already-rendered nodes when a custom property
 * changes through an attribute selector on :root. Measured on this page: after
 * flipping data-theme the backgrounds repainted and every piece of text kept its
 * previous colour — nav labels ended at 2.77:1 against the new ground. A reflow
 * did not fix it and neither did rewriting the property inline; replacing the
 * DOM node did, which is what identifies this as an invalidation bug rather than
 * a cascade mistake.
 *
 * Detaching the subtree for one frame forces a full restyle on reattach. It is
 * cheaper than remounting the React tree, and unlike a remount it does not throw
 * away whatever the user had on screen — a half-finished analysis survives a
 * theme change, which it would not if this were keyed on the theme.
 */
function forceRestyle() {
  const app = document.querySelector<HTMLElement>('.app')
  if (!app) return
  const prev = app.style.display
  app.style.display = 'none'
  void app.offsetHeight          // reading layout is what flushes the restyle
  app.style.display = prev
}

/** System stamps nothing, so `prefers-color-scheme` is left to decide. */
export function applyChoice(c: Choice) {
  const root = document.documentElement
  if (c === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', c)
  forceRestyle()
  try {
    if (c === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, c)
  } catch { /* private mode throws rather than returning null */ }
}

export function ThemeToggle() {
  const [choice, setChoice] = useState<Choice>(storedChoice)

  useEffect(() => { applyChoice(choice) }, [choice])

  return (
    <div
      role="radiogroup"
      aria-label="Colour theme"
      className="inline-flex items-center gap-0.5 rounded-[var(--radius-pill)] p-0.5"
      style={{ background: 'var(--color-surface-3)' }}
    >
      {OPTIONS.map(({ v, Icon, label }) => {
        const on = choice === v
        return (
          <button
            key={v}
            role="radio"
            aria-checked={on}
            aria-label={label}
            title={label}
            onClick={() => setChoice(v)}
            className="press grid h-7 w-7 place-items-center rounded-[var(--radius-pill)] cursor-pointer"
            style={
              on
                ? { background: 'var(--color-surface)', color: 'var(--color-text)',
                    boxShadow: '0 1px 2px rgba(var(--shadow-tint), calc(0.10 * var(--shadow-strength)))' }
                : { background: 'transparent', color: 'var(--color-text-3)' }
            }
          >
            <Icon size={14} weight={on ? 'fill' : 'regular'} aria-hidden="true" />
          </button>
        )
      })}
    </div>
  )
}
