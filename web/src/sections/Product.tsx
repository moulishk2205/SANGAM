import { Shell, Section, Lines } from '../components/Primitives'
import { useGsap, gsap, revealUp } from '../lib/motion'
import { RollingNumber } from '../components/RollingNumber'

/* ══════════════════════════════════════════════════════════════════════════
   The evidence, after the model.

   The hero gives the metaphor and the model section gives the mechanism; this
   is where both get held to a number. Every figure is produced by
   scripts/evaluate.py against the demonstration corpus, and the paragraph under
   them says exactly what that corpus is — because a metric without its
   provenance is a claim, not a measurement.
   ══════════════════════════════════════════════════════════════════════════ */

/** Measured by scripts/evaluate.py on the demonstration corpus. Not estimates. */
const METRICS = [
  { v: '96.33%', l: 'recall@1', n: 'hybrid retrieval, 300 probes' },
  { v: '99.06%', l: 'F1', n: 'match verdict vs construction ground truth' },
  { v: '2,392', l: 'vetoes', n: 'all at text similarity ≥ 0.85' },
  { v: '14.5 ms', l: 'p95 latency', n: 'end-to-end, per record' },
]

export function Product() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)
    revealUp(q('.js-lede'), { trigger: root, start: 'top 76%', stagger: 0.08 })
    revealUp(q('.js-metric'), { trigger: q('.js-metrics')[0], start: 'top 85%', stagger: 0.07 })
  }, [])

  return (
    <Section id="product" labelledBy="product-h" ground="void">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <p className="js-lede t-label text-live mb-5">Evaluation</p>
          <Lines
            as="h2"
            id="product-h"
            lines={['Held to a number,', 'not to an adjective.']}
            className="t-display text-paper text-[clamp(2rem,5.4vw,4.2rem)] leading-[1.02] tracking-[-0.025em]"
          />
          <p className="js-lede t-datum text-graphite mt-7 max-w-[58ch] text-[14.5px] leading-relaxed">
            Every figure below is produced by the evaluation harness against the corpus the
            engine actually indexes — and every one carries what it was measured on. A metric
            without its provenance is a claim, not a measurement.
          </p>

          {/* ── measured, with provenance ────────────────────────────── */}
          <div className="js-metrics mt-16 md:mt-24">
            <p className="t-label text-graphite mb-6">Measured on the demonstration corpus</p>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 border border-white/10">
              {METRICS.map((m, i) => (
                <div key={m.l} className="js-metric bg-void p-6">
                  <RollingNumber
                    value={m.v}
                    delay={i * 130}
                    className="t-datum block text-paper text-[clamp(1.4rem,3vw,2rem)] leading-none"
                  />
                  <p className="t-label text-live mt-3">{m.l}</p>
                  <p className="t-datum text-graphite mt-1.5 text-[11px] leading-snug">{m.n}</p>
                </div>
              ))}
            </div>
            <p className="t-datum text-graphite/80 mt-6 max-w-[72ch] text-[12px] leading-relaxed">
              The corpus is <span className="text-paper/80">synthetic and construction-derived</span>:
              1,800 records generated from specifications we define, across four invented
              organisations. Labels are correct by construction. Organisation names and material
              codes are not the records of any real enterprise, and these figures describe the
              engine on that corpus — they are not a claim about performance on live CPSE data.
              Scores are uncalibrated ranking scores, never probabilities.
            </p>
          </div>
        </div>
      </Shell>
    </Section>
  )
}
