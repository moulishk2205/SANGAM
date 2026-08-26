import { Shell, Section, Lines } from '../components/Primitives'
import { VerdictMark } from '../components/Verdict'
import { useGsap, gsap, revealUp } from '../lib/motion'

/**
 * UNKNOWN — controlled uncertainty.
 *
 * The unknown state deliberately does not animate while the other two reveal.
 * Stillness is the point: this is the system declining to act.
 */
export function Unknown() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-state'), { trigger: root, start: 'top 72%', stagger: 0.1 })
  }, [])

  const states = [
    { v: 'agree' as const,    t: 'Both sides stated it, and the values match.' },
    { v: 'disagree' as const, t: 'Both sides stated it, and the values conflict. On a critical attribute this vetoes the match outright.' },
    { v: 'unknown' as const,  t: 'At least one side did not state it. This never counts as agreement, and it never vetoes.' },
  ]

  return (
    <Section id="unknown" labelledBy="unknown-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="unknown-heading"
            lines={['When the evidence is not enough,', 'the system does not guess.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-16"
          />

          <dl className="grid md:grid-cols-3 gap-px bg-white/10 border-y border-white/10 m-0">
            {states.map((s) => (
              <div key={s.v} className="js-state bg-void py-8 md:px-6 md:first:pl-0">
                <dt className="mb-4"><VerdictMark verdict={s.v} /></dt>
                <dd className="t-datum text-[13px] text-mist m-0 leading-relaxed">{s.t}</dd>
              </div>
            ))}
          </dl>

          <p className="t-body text-mist mt-14">
            A wrong merge can send the wrong part to a live refinery. A missed merge costs a
            reviewer thirty seconds. Those two errors are not symmetric, so the system is not
            symmetric either.
          </p>
        </div>
      </Shell>
    </Section>
  )
}
