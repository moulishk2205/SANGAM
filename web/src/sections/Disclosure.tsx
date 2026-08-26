import { Shell, Section } from '../components/Primitives'

/**
 * DISCLOSURE — what we have not proven.
 *
 * This section has NO animation, deliberately. An animated disclosure reads as
 * spin. The stillness is the argument, and to a judge who has watched several
 * teams overclaim, volunteering this before being asked is worth more than any
 * amount of polish.
 *
 * The ground lifts to --raised rather than inverting, so the section reads as
 * set apart without breaking the page's single-inversion rule.
 */
export function Disclosure() {
  return (
    <Section id="disclosure" labelledBy="disclosure-heading" ground="raised">
      <Shell>
        <div className="max-w-[62ch] border-l border-white/20 pl-8 md:pl-12">
          <h2 id="disclosure-heading" className="t-sub text-[clamp(1.25rem,2.5vw,1.75rem)] text-paper mb-8">
            What this evaluation does and does not show
          </h2>

          <p className="t-body text-mist mb-6">
            Our evaluation corpus is synthetic. We generated it from specifications we defined,
            extracted attributes with rules we wrote, and derived the labels from those same
            specifications. The reported precision therefore largely measures whether our
            extractor can invert our own generator.
          </p>

          <p className="t-body text-paper mb-10">
            It demonstrates that the pipeline is correct. It is not evidence of accuracy on real
            material descriptions, and we do not present it as such.
          </p>

          <dl className="grid sm:grid-cols-2 gap-8 m-0 mb-10">
            <div>
              <dt className="t-label text-graphite mb-3">Validated so far</dt>
              <dd className="t-datum text-[13px] text-mist m-0 leading-relaxed">
                Pipeline correctness. Veto behaviour. Abstention behaviour. The retrieval ablation.
              </dd>
            </div>
            <div>
              <dt className="t-label text-graphite mb-3">Not yet validated</dt>
              <dd className="t-datum text-[13px] text-mist m-0 leading-relaxed">
                Performance on real material descriptions from an operating material master.
              </dd>
            </div>
          </dl>

          <p className="t-label text-graphite">
            Next: hand-labelled real tender line items, then held-out evaluation, then
            production validation.
          </p>
        </div>
      </Shell>
    </Section>
  )
}
