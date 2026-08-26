import { Shell, Section, Lines, Eyebrow } from '../components/Primitives'
import { PIPELINE } from '../lib/content'
import { useGsap, gsap, revealUp } from '../lib/motion'

/**
 * THE ENGINE — the real pipeline.
 *
 * The source description stays pinned at the top of the list while the stages
 * reveal, so the visitor never loses the referent. Deliberately not drawn as
 * glowing nodes, travelling particles, or a neural net: those are the generic
 * AI-diagram vocabulary and they would misrepresent a deterministic pipeline.
 */
export function Engine() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-stage'), { trigger: root, start: 'top 70%', stagger: 0.07 })
  }, [])

  return (
    <Section id="engine" labelledBy="engine-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Eyebrow>How the decision is made</Eyebrow>
          <Lines
            as="h2"
            id="engine-heading"
            lines={['Retrieval proposes.', 'Specification decides.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-4"
          />
          <p className="t-body text-mist mb-16">
            Embeddings answer which materials could plausibly be related. They never answer
            whether two materials are the same. That question is settled by comparing typed
            attributes under a gate.
          </p>

          <p className="t-datum text-[13px] text-paper border border-white/15 px-4 py-3 inline-block mb-10">
            SS HEX BOLT M10 X 50
          </p>

          <ol className="grid gap-px bg-white/10 border-y border-white/10 list-none p-0 m-0">
            {PIPELINE.map((s, i) => (
              <li key={s.stage} className="js-stage bg-void grid md:grid-cols-[3rem_10rem_1fr] gap-2 md:gap-6 py-5 items-baseline">
                <span className="t-label text-graphite tabular">{String(i + 1).padStart(2, '0')}</span>
                <span className="t-datum text-paper text-[15px]">{s.stage}</span>
                <span className="t-datum text-mist text-[13px]">{s.note}</span>
              </li>
            ))}
          </ol>
        </div>
      </Shell>
    </Section>
  )
}
