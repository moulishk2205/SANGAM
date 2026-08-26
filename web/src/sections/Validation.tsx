import { Shell, Section, Lines, Eyebrow, Provenance } from '../components/Primitives'
import { VALIDATION } from '../lib/content'
import { useGsap, gsap, revealUp, snapIn } from '../lib/motion'

/**
 * VALIDATION — the ablation.
 *
 * Bars ease because a bar is prose. Numbers snap because a number is data.
 * The measured result is that removing the dense retrieval channel costs 14.7
 * points of recall while leaving decision precision untouched, which is the
 * retrieval-proposes / specification-decides split behaving as designed.
 */
export function Validation() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-corpus'), { trigger: root, stagger: 0.07 })
    const tl = gsap.timeline({
      scrollTrigger: { trigger: q('.js-bars')[0], start: 'top 78%', toggleActions: 'play none none reverse' },
    })
    tl.fromTo(q('.js-bar'), { scaleX: 0 }, { scaleX: 1, transformOrigin: 'left', duration: 0.6, ease: 'power2.out', stagger: 0.12 })
      .add(snapIn(q('.js-pct'), { stagger: 0.12 }), '<0.35')
      .add(snapIn(q('.js-gain')), '+=0.1')
    revealUp(q('.js-vetostat'), { trigger: q('.js-vetostat')[0], start: 'top 80%', stagger: 0.08 })
  }, [])

  const rows = [
    { name: 'Hybrid retrieval', pct: VALIDATION.recall.hybrid },
    { name: 'Lexical only',     pct: VALIDATION.recall.lexical },
  ]

  return (
    <Section id="validation" labelledBy="validation-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Eyebrow>What we measured</Eyebrow>
          <Lines
            as="h2"
            id="validation-heading"
            lines={['The better the semantic model,', 'the more the veto matters.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-16"
          />

          <ul className="grid sm:grid-cols-3 gap-8 list-none p-0 m-0 mb-20">
            {VALIDATION.corpus.map((c) => (
              <li key={c.label} className="js-corpus">
                <p className="t-datum tabular text-3xl text-paper">{c.value}</p>
                <p className="t-datum text-[12px] text-graphite mt-1">{c.label}</p>
              </li>
            ))}
          </ul>

          <div className="js-bars">
            <p className="t-label text-graphite mb-8">Recall at rank 1</p>
            {rows.map((r) => (
              <div key={r.name} className="mb-8">
                <div className="flex items-baseline justify-between mb-2.5">
                  <span className="t-datum text-[13px] text-mist">{r.name}</span>
                  <span className="js-pct t-datum tabular text-2xl text-paper">{r.pct}%</span>
                </div>
                <div className="h-px w-full bg-white/12">
                  <div
                    className="js-bar h-px bg-live"
                    style={{ width: `${r.pct}%` }}
                  />
                </div>
              </div>
            ))}
            <p className="js-gain t-datum text-live text-lg tabular mt-6">
              {VALIDATION.recall.gain} points from the dense channel
            </p>
          </div>

          <div className="js-vetostat mt-20 grid sm:grid-cols-2 gap-10 border-t border-white/10 pt-10">
            <div>
              <p className="t-datum tabular text-3xl text-paper">{VALIDATION.veto.total}</p>
              <p className="t-datum text-[12px] text-graphite mt-1">candidates rejected on a critical attribute</p>
            </div>
            <div>
              <p className="t-datum tabular text-3xl text-paper">{VALIDATION.veto.similar}</p>
              <p className="t-datum text-[12px] text-graphite mt-1">of those carried text similarity of 0.85 or higher</p>
            </div>
          </div>

          <Provenance>
            Measured by our own evaluation harness on the synthetic corpus described below.
            Reproducible with scripts/evaluate.py.
          </Provenance>
        </div>
      </Shell>
    </Section>
  )
}
