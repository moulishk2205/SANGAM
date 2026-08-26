import { Shell, Section, Lines, Provenance } from '../components/Primitives'
import { SCALE } from '../lib/content'
import { useGsap, gsap, snapIn, revealUp } from '../lib/motion'

/**
 * SCALE — one material becomes a systemic problem.
 *
 * One number is dominant; three support it. Four equally-sized large numbers
 * would flatten all of them.
 *
 * The digits are replaced, not counted up. A ticking counter reads as a slot
 * machine and implies the figure is being generated rather than reported.
 */
export function Scale() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-lede'), { trigger: root })
    snapIn(q('.js-big'), { trigger: root, start: 'top 70%' })
    revealUp(q('.js-row'), { trigger: root, start: 'top 68%', stagger: 0.08 })
  }, [])

  return (
    <Section id="scale" labelledBy="scale-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="scale-heading"
            lines={['That was one material.']}
            className="js-lede t-headline text-[clamp(1.75rem,4vw,3rem)] text-paper mb-16"
          />

          <p className="js-big t-display tabular text-[clamp(3.5rem,13vw,11rem)] text-paper leading-none">
            {SCALE.headline.value}
          </p>
          <p className="js-big t-datum text-mist mt-4 max-w-[46ch]">{SCALE.headline.label}</p>

          <dl className="mt-20 grid gap-px bg-white/10 border-y border-white/10 m-0">
            {SCALE.supporting.map((s) => (
              <div key={s.value} className="js-row bg-void grid md:grid-cols-[13rem_1fr] gap-2 md:gap-8 py-6">
                <dt className="t-datum tabular text-2xl md:text-3xl text-paper m-0">{s.value}</dt>
                <dd className="t-datum text-mist m-0 self-center">{s.label}</dd>
              </div>
            ))}
          </dl>

          <Provenance>{SCALE.provenance}</Provenance>
        </div>
      </Shell>
    </Section>
  )
}
