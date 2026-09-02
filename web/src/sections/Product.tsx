import { Shell, Section, Lines } from '../components/Primitives'
import { useGsap, gsap, revealUp } from '../lib/motion'

/* ══════════════════════════════════════════════════════════════════════════
   After the cinematic: what SANGAM actually is.

   The hero establishes the metaphor. This section has to cash it, which means
   every capability named here is one the running engine performs. The brief
   asked for a "PROPERTY PREDICTION" card — behaviour under thermal, corrosion
   and fatigue load. SANGAM does not model any of that, and a card claiming it
   would not survive the first question from a materials engineer. What the
   engine does instead is decide *identity*, which is the harder half of the
   problem it was actually set: the same bolt written five ways in five
   organisations is one material, and nothing in the master knows that yet.
   ══════════════════════════════════════════════════════════════════════════ */

const CARDS = [
  {
    n: '01',
    title: 'Check before you create',
    body:
      'Before a new code is minted, the description is run against the whole master. ' +
      'If the material already exists under another organisation’s spelling, it is found ' +
      'and shown with its evidence — prevention rather than a cleanup project later.',
    tag: 'check_before_create',
  },
  {
    n: '02',
    title: 'Structured identity',
    body:
      'Free text becomes typed engineering attributes with units resolved and tolerances ' +
      'attached. Every value carries the rule that read it, so a reviewer can audit the ' +
      'reading rather than trusting it.',
    tag: 'extract · normalise',
  },
  {
    n: '03',
    title: 'Comparative intelligence',
    body:
      'Candidates are placed against the decision that was actually made about them — what ' +
      'agreed, what differed, and which critical attribute rejected the pair. Similarity ' +
      'proposes; the specification decides.',
    tag: 'relationship map',
  },
  {
    n: '04',
    title: 'Engineering decision',
    body:
      'One canonical identity per material, with every original organisation code still ' +
      'attached to it. The master gains a shared identity and nobody loses the code they ' +
      'have used for twenty years.',
    tag: 'canonical · traceable',
  },
]

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
    revealUp(q('.js-card'), { trigger: q('.js-cards')[0], start: 'top 82%', stagger: 0.09 })
    revealUp(q('.js-metric'), { trigger: q('.js-metrics')[0], start: 'top 85%', stagger: 0.07 })
  }, [])

  return (
    <Section id="product" labelledBy="product-h" ground="void">
      <Shell>
        <div ref={root as React.RefObject<HTMLDivElement>}>
          <p className="js-lede t-label text-live mb-5">Material Intelligence</p>
          <Lines
            as="h2"
            id="product-h"
            lines={['From material description', 'to engineering decision.']}
            className="t-display text-paper text-[clamp(2rem,5.4vw,4.2rem)] leading-[1.02] tracking-[-0.025em]"
          />
          <p className="js-lede t-datum text-graphite mt-7 max-w-[58ch] text-[14.5px] leading-relaxed">
            Different organisations describe the same material differently, and no master
            record knows they are the same thing. SANGAM resolves those descriptions into one
            canonical identity — deciding on the specification rather than on the spelling,
            and keeping every original code attached.
          </p>

          {/* ── capabilities ─────────────────────────────────────────── */}
          <div className="js-cards mt-16 md:mt-24 grid gap-px bg-white/10 sm:grid-cols-2 border border-white/10">
            {CARDS.map((c) => (
              <article
                key={c.n}
                className="js-card group relative bg-void p-7 md:p-9 transition-colors duration-500
                           hover:bg-raised"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <span className="t-label text-live">{c.n}</span>
                  <span className="t-datum text-[10.5px] text-graphite/70 tracking-wide">{c.tag}</span>
                </div>
                <h3 className="t-headline text-paper mt-4 text-[clamp(1.15rem,2vw,1.55rem)] leading-tight">
                  {c.title}
                </h3>
                <p className="t-datum text-graphite mt-3 text-[13.5px] leading-relaxed max-w-[42ch]">
                  {c.body}
                </p>
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-0 h-px w-0 bg-live transition-all duration-700
                             ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:w-full"
                />
              </article>
            ))}
          </div>

          {/* ── measured, with provenance ────────────────────────────── */}
          <div className="js-metrics mt-16 md:mt-24">
            <p className="t-label text-graphite mb-6">Measured on the demonstration corpus</p>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 border border-white/10">
              {METRICS.map((m) => (
                <div key={m.l} className="js-metric bg-void p-6">
                  <p className="t-datum text-paper text-[clamp(1.4rem,3vw,2rem)] leading-none">{m.v}</p>
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
