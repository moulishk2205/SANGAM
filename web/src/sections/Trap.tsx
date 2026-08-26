import { Shell, Section, Lines, Eyebrow } from '../components/Primitives'
import { TRAP } from '../lib/content'
import { useGsap, gsap, snapIn, revealUp, DUR } from '../lib/motion'

/**
 * THE TRAP — 0.960 against 0.957.
 *
 * The visitor must fail to tell these apart before the veto is explained. If
 * the page explains first, the veto is a feature; if the visitor fails first,
 * the veto is a relief. Same information, opposite emotional value.
 *
 * The 600ms hold after the scores land is the most important timing on the
 * page. Nothing may move during it.
 */
export function Trap() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    const tl = gsap.timeline({
      scrollTrigger: { trigger: root, start: 'top 68%', toggleActions: 'play none none reverse' },
    })
    tl.add(revealUp(q('.js-pair'), { stagger: 0.1 }))
      .add(snapIn(q('.js-score'), { stagger: 0.12 }), '+=0.2')
      .add(snapIn(q('.js-delta')), '+=0.1')
      // The hold. Deliberate dead air while the visitor tries to spot it.
      .to({}, { duration: 0.6 })
      .add(
        gsap.fromTo(
          q('.js-turn .js-line'),
          { yPercent: 105, autoAlpha: 0 },
          { yPercent: 0, autoAlpha: 1, duration: DUR.slow, stagger: 0.08 },
        ),
      )
  }, [])

  return (
    <Section id="trap" labelledBy="trap-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Eyebrow>Where similarity stops working</Eyebrow>
          <Lines
            as="h2"
            id="trap-heading"
            lines={['A model scored these', 'three thousandths apart.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-20"
          />

          <div className="grid md:grid-cols-2 gap-px bg-white/10 border-y border-white/10">
            {[TRAP.source, TRAP.candidate].map((item, i) => (
              <div key={i} className="js-pair bg-void px-0 md:px-8 py-10 first:md:pl-0">
                <p className="t-datum text-mist text-[13px] mb-8 min-h-[3em]">{item.text}</p>
                <p className="js-score t-display tabular text-[clamp(3rem,9vw,6rem)] text-paper leading-none">
                  {item.score}
                </p>
                <p className="t-label text-graphite mt-4">Semantic similarity</p>
              </div>
            ))}
          </div>

          <p className="js-delta t-datum text-graphite mt-6">
            Difference <span className="text-paper tabular">{TRAP.delta}</span>
          </p>

          <div className="js-turn mt-20 max-w-[34ch]">
            <p className="t-headline text-[clamp(1.5rem,3.5vw,2.5rem)] text-paper">
              <span className="line-mask"><span className="js-line block">One is the same bolt.</span></span>
              <span className="line-mask"><span className="js-line block">One is a different bolt.</span></span>
            </p>
          </div>
        </div>
      </Shell>
    </Section>
  )
}
