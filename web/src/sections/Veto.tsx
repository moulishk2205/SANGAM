import { Shell, Section, Lines } from '../components/Primitives'
import { VerdictMark } from '../components/Verdict'
import { EVIDENCE } from '../lib/content'
import { useGsap, gsap, revealUp, snapIn, DUR, EASE } from '../lib/motion'

/**
 * THE VETO — the one destructive event in the whole experience.
 *
 * Every thread on this page holds. This one breaks, once, and the page has
 * spent nine screens earning that break. The severing runs 240ms total: the
 * gap opens in 90ms, the lower segment falls in 150ms on power2.in. It is the
 * only inward ease on the page, because things fall, they do not ease out of
 * falling.
 *
 * No explosion, no particles, no shake. The restraint is what makes it read
 * as a verdict rather than an error.
 */
export function Veto() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    const tl = gsap.timeline({
      scrollTrigger: { trigger: root, start: 'top 62%', toggleActions: 'play none none reverse' },
    })

    tl.add(revealUp(q('.js-evrow'), { stagger: 0.14 }))
      .add(snapIn(q('.js-mark'), { stagger: 0.14 }), '<0.2')
      // The sever.
      .to(q('.js-thread-live'), { scaleY: 0.52, transformOrigin: 'top', duration: 0.09, ease: 'none' }, '+=0.15')
      .fromTo(
        q('.js-thread-dead'),
        { autoAlpha: 0, y: 0 },
        { autoAlpha: 1, y: 8, duration: 0.15, ease: 'power2.in' },
        '<0.09',
      )
      .add(snapIn(q('.js-verdict-block')), '<0.1')
      .add(
        gsap.fromTo(
          q('.js-close .js-line'),
          { yPercent: 105, autoAlpha: 0 },
          { yPercent: 0, autoAlpha: 1, duration: DUR.slow, ease: EASE, stagger: 0.08 },
        ),
        '+=0.2',
      )
  }, [])

  return (
    <Section id="veto" labelledBy="veto-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="veto-heading"
            lines={['So we stop comparing text', 'and compare the specification.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-16"
          />

          <div className="relative grid lg:grid-cols-[2.5rem_1fr] gap-0">
            {/* The thread, in two segments so it can visibly part. */}
            <div className="hidden lg:block relative" aria-hidden="true">
              <div className="js-thread-live absolute left-1/2 top-0 h-full w-px bg-live" />
              <div className="js-thread-dead absolute left-1/2 top-[52%] h-[48%] w-px bg-graphite opacity-0" />
            </div>

            <div className="overflow-x-auto -mx-[var(--shell)] px-[var(--shell)] lg:mx-0 lg:px-0">
            <table className="w-full border-collapse text-left min-w-[34rem]">
              <caption className="visually-hidden">
                Attribute comparison between the source material and the candidate. The length
                attribute disagrees, which vetoes the match.
              </caption>
              <thead>
                <tr className="border-b border-white/15">
                  <th scope="col" className="t-label text-graphite py-3 font-medium">Attribute</th>
                  <th scope="col" className="t-label text-graphite py-3 font-medium">Source</th>
                  <th scope="col" className="t-label text-graphite py-3 font-medium">Candidate</th>
                  <th scope="col" className="t-label text-graphite py-3 font-medium text-right">Result</th>
                </tr>
              </thead>
              <tbody>
                {EVIDENCE.map((row) => (
                  <tr key={row.attribute} className="js-evrow border-b border-white/8 align-top">
                    <th scope="row" className="t-datum text-[13px] text-mist py-5 font-normal">
                      {row.attribute}
                      {row.critical && (
                        <span className="t-label text-graphite ml-2 border border-current/30 px-1.5 py-0.5">
                          critical
                        </span>
                      )}
                    </th>
                    <td className="t-datum text-[13px] text-paper py-5">{row.source}</td>
                    <td className={`t-datum text-[13px] py-5 ${row.verdict === 'disagree' ? 'text-cut' : 'text-paper'}`}>
                      {row.candidate}
                    </td>
                    <td className="py-5 text-right">
                      <span className="js-mark inline-block">
                        <VerdictMark verdict={row.verdict} />
                      </span>
                      {row.detail && (
                        <span className="block t-datum text-[11px] text-graphite mt-1.5">{row.detail}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>

          <div className="js-verdict-block mt-14 grid md:grid-cols-2 gap-10 border-t border-cut/40 pt-10">
            <div>
              <p className="t-display text-[clamp(2rem,6vw,4rem)] text-cut leading-none">DISTINCT</p>
              <p className="t-datum text-graphite mt-4">
                Confidence <span className="text-paper tabular">0.000</span>
              </p>
            </div>
            <div className="self-end">
              <p className="t-datum text-mist text-[13px]">
                Semantic similarity <span className="text-paper tabular">0.957</span>
              </p>
              <p className="t-datum text-mist text-[13px] mt-1">
                Length <span className="text-cut">50.0 mm is not 75.0 mm</span>
              </p>
            </div>
          </div>

          <div className="js-close mt-20 max-w-[38ch]">
            <p className="t-headline text-[clamp(1.375rem,3vw,2.25rem)] text-paper">
              <span className="line-mask"><span className="js-line block">The text similarity was higher</span></span>
              <span className="line-mask"><span className="js-line block">than for the match we accepted.</span></span>
              <span className="line-mask"><span className="js-line block">It did not matter.</span></span>
            </p>
          </div>
        </div>
      </Shell>
    </Section>
  )
}
