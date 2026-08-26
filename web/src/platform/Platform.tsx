import { ArrowLeft } from '@phosphor-icons/react'
import { Shell } from '../components/Primitives'
import { Check } from './Check'
import './platform.css'

/**
 * Platform shell.
 *
 * No sidebar. A persistent navigation rail for a surface with one primary
 * action is furniture, and furniture is what makes enterprise software feel
 * heavy. The top bar carries identity, state and the way back; everything else
 * is the work.
 */
export function Platform() {
  return (
    <div className="min-h-[100dvh] bg-void flex flex-col">
      <header className="border-b border-[var(--color-line-soft)] sticky top-0 z-10 bg-void/95 backdrop-blur-sm">
        <Shell className="flex items-center justify-between gap-6 h-16">
          <div className="flex items-baseline gap-4">
            <span className="t-datum text-[11px] uppercase tracking-[0.14em] text-paper">
              Material Intelligence
            </span>
            <span className="t-datum text-[10px] text-graphite hidden sm:inline">SIH26099</span>
          </div>
          <a
            href="/"
            className="pressable focus-ring t-datum text-[10px] uppercase tracking-[0.12em]
                       text-mist hover:text-paper inline-flex items-center gap-2"
          >
            <ArrowLeft size={12} weight="bold" aria-hidden="true" />
            <span className="hidden sm:inline">Back to the story</span>
            <span className="sm:hidden">Back</span>
          </a>
        </Shell>
      </header>

      <main id="main" className="flex-1 py-10 md:py-14">
        <Shell>
          <h1 className="visually-hidden">Material Intelligence Platform, material check</h1>
          <Check />
        </Shell>
      </main>
    </div>
  )
}
