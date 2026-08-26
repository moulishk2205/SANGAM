import { ArrowLeft } from '@phosphor-icons/react'
import { Shell } from '../components/Primitives'
import { CANONICAL } from '../lib/content'

/**
 * Placeholder for the Material Intelligence Platform.
 *
 * The platform is deliberately not built yet. This exists so the landing page's
 * CTA resolves to something honest instead of a 404 during a demo, and so the
 * route is already claimed when the platform lands. It states plainly what is
 * and is not built rather than showing a fake dashboard.
 */
export function PlatformStub() {
  return (
    <main className="min-h-[100dvh] bg-void flex items-center py-24">
      <Shell>
        <p className="t-label text-graphite mb-8">Material Intelligence Platform</p>
        <h1 className="t-headline text-[clamp(1.75rem,4.5vw,3rem)] text-paper mb-8 max-w-[24ch]">
          Not built yet. This route is reserved.
        </h1>
        <p className="t-body text-mist mb-10">
          The matching engine behind the landing page is real and tested, and runs today from the
          command line. The interface that will drive it, material check, ranked candidates,
          evidence tables and check before create, is the next piece of work.
        </p>
        <dl className="grid sm:grid-cols-2 gap-8 border-t border-white/10 pt-8 m-0 mb-12">
          <div>
            <dt className="t-label text-graphite mb-3">Carried over</dt>
            <dd className="t-datum text-[13px] text-mist m-0">
              <span className="text-live">{CANONICAL.nmc}</span>, with all five source codes retained.
            </dd>
          </div>
          <div>
            <dt className="t-label text-graphite mb-3">Engine status</dt>
            <dd className="t-datum text-[13px] text-mist m-0">
              Normalise, extract, retrieve, compare, veto, decide. Eleven tests passing.
            </dd>
          </div>
        </dl>
        <a
          href="/"
          className="group inline-flex items-center gap-3 border border-paper/70 px-6 py-4 text-paper
                     transition-colors duration-200 hover:bg-paper hover:text-ink
                     focus-visible:bg-paper focus-visible:text-ink"
        >
          <ArrowLeft size={15} weight="bold" aria-hidden="true"
            className="transition-transform duration-200 group-hover:-translate-x-1" />
          <span className="t-label">Back to the story</span>
        </a>
      </Shell>
    </main>
  )
}
