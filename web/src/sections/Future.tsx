import { Shell, Section, Lines } from '../components/Primitives'
import { FUTURE } from '../lib/content'
import { useGsap, gsap, revealUp } from '../lib/motion'

/** FUTURE SCALE — what the engine makes possible. Stated as direction, not promise. */
export function Future() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-item'), { trigger: root, start: 'top 76%', stagger: 0.05 })
  }, [])

  return (
    <Section id="future" labelledBy="future-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="future-heading"
            lines={['A resolved identity', 'is the foundation, not the product.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-16"
          />
          <ul className="grid md:grid-cols-2 gap-x-16 gap-y-6 list-none p-0 m-0">
            {FUTURE.map((f) => (
              <li key={f} className="js-item t-datum text-[14px] text-mist border-t border-white/10 pt-5">
                {f}
              </li>
            ))}
          </ul>
        </div>
      </Shell>
    </Section>
  )
}
