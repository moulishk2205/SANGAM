import { ArrowRight } from '@phosphor-icons/react'
import { Shell, Lines } from '../components/Primitives'
import { CANONICAL } from '../lib/content'
import { useGsap, gsap, revealUp, snapIn } from '../lib/motion'

/**
 * CTA — the bridge into the platform.
 *
 * The identity the visitor watched resolve is named here and carried through,
 * so entering the platform reads as stepping into the machine just described
 * rather than clicking to an unrelated site.
 */
export function Cta() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-cta'), { trigger: root, start: 'top 78%', stagger: 0.1 })
    snapIn(q('.js-carry'), { trigger: root, start: 'top 74%' })
  }, [])

  return (
    <section id="enter" aria-labelledby="cta-heading" className="relative py-32 md:py-48 bg-void">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="cta-heading"
            lines={['Stop matching names.', 'Start resolving materials.']}
            className="t-display text-[clamp(2.25rem,7vw,5.5rem)] text-paper mb-16"
          />

          <div className="js-cta flex flex-col sm:flex-row sm:items-center gap-8">
            <a
              href="/platform"
              className="group inline-flex items-center gap-4 border border-paper/70 px-8 py-5 text-paper
                         transition-colors duration-200 hover:bg-paper hover:text-ink
                         focus-visible:bg-paper focus-visible:text-ink"
            >
              <span className="t-label">Enter the platform</span>
              <ArrowRight size={16} weight="bold" aria-hidden="true"
                className="transition-transform duration-200 group-hover:translate-x-1" />
            </a>

            <p className="js-carry t-datum text-[13px] text-graphite">
              <span className="text-live">{CANONICAL.nmc}</span> is loaded and waiting.
              <br />5 source codes retained.
            </p>
          </div>
        </div>
      </Shell>

      <footer className="mt-32">
        <Shell>
          <div className="border-t border-white/10 pt-8 flex flex-col sm:flex-row gap-3 sm:justify-between">
            <p className="t-label text-graphite">
              SIH26099 <span aria-hidden="true">·</span> Smart India Hackathon 2026
            </p>
            <p className="t-label text-graphite">
              Ministry of Petroleum and Natural Gas <span aria-hidden="true">·</span> CPCL
            </p>
          </div>
        </Shell>
      </footer>
    </section>
  )
}
