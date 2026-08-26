import { Shell, Section, Lines, Provenance } from '../components/Primitives'
import { useGsap, gsap, revealUp } from '../lib/motion'

/**
 * DATA FOUNDATION — trust.
 *
 * Answers the second question every judge asks: where did the data come from?
 * Stated plainly, including the part that is a limitation.
 */
export function Foundation() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-layer'), { trigger: root, start: 'top 74%', stagger: 0.08 })
  }, [])

  const layers = [
    { k: 'Public catalogue',        v: 'DLA FLIS and PUB LOG, a US federal FOIA release, built on the NATO Codification System' },
    { k: 'Approved item names',     v: '79,883 names, each with an English definition' },
    { k: 'Attribute dictionary',    v: '27,552 attribute definitions with controlled vocabularies' },
    { k: 'Canonical representation',v: 'Item name plus typed attributes, with units resolved and tolerances stated' },
  ]

  return (
    <Section id="foundation" labelledBy="foundation-heading">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <Lines
            as="h2"
            id="foundation-heading"
            lines={['Built on a real', 'codification standard.']}
            className="t-headline text-[clamp(1.75rem,4.5vw,3.5rem)] text-paper mb-16"
          />

          <dl className="grid gap-px bg-white/10 border-y border-white/10 m-0">
            {layers.map((l) => (
              <div key={l.k} className="js-layer bg-void grid md:grid-cols-[16rem_1fr] gap-2 md:gap-8 py-6">
                <dt className="t-datum text-[14px] text-paper m-0">{l.k}</dt>
                <dd className="t-datum text-[13px] text-mist m-0">{l.v}</dd>
              </div>
            ))}
          </dl>

          <p className="t-body text-mist mt-14">
            India already operates a codification bureau on this system for defence materiel.
            There is no civil equivalent for public sector enterprises. That gap is the opportunity.
          </p>

          <Provenance>
            FLIS-derived reference data. Not CPSE data. The organisation names and material codes
            shown on this page are synthetic, generated over real catalogue identities.
          </Provenance>
        </div>
      </Shell>
    </Section>
  )
}
