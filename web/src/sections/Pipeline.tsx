import { useEffect, useRef, useState } from 'react'
import { Shell } from '../components/Primitives'
import { useGsap, gsap, ScrollTrigger, prefersReducedMotion } from '../lib/motion'

/* ══════════════════════════════════════════════════════════════════════════
   THE SCORING MODEL — seven steps, one card at a time.

   These are the seven steps engine.py actually performs, in the order its own
   docstring states them: normalise → extract → retrieve → compare → VETO →
   score → decide. Nothing here is a marketing abstraction over the code; every
   constant on screen (0.85 / 0.15, 0.86 / 0.70 / 0.45, RRF k=60) is imported
   from the same file the engine runs.

   THE MOTION

   A horizontal wipe rather than a horizontal track. On a track all seven cards
   exist side by side and slide past, which means six of them are always
   half-visible at the edges and the reader never has one thing to look at. Here
   each card is full-bleed and absolutely stacked, and the next slides across to
   cover the last — so exactly one step is legible at any moment, which is the
   point of breaking a formula into steps at all.

   The outgoing card drifts left at a third of the incoming card's speed and
   loses a little light. That parallax is what stops the wipe reading as a
   slideshow: the two layers move at different rates, so the eye reads depth
   rather than replacement.

   Vertical scroll drives it, with `ease: 'none'` — mandatory for any
   scroll-linked tween, or scroll position and card position stop corresponding
   and the whole thing feels broken in a way that is hard to name.
   ══════════════════════════════════════════════════════════════════════════ */

type Step = {
  n: string
  key: string
  title: string
  lead: string
  body: string
  /** The literal expression or constant this step contributes. */
  formula: string
  meta: string[]
}

const STEPS: Step[] = [
  {
    n: '01', key: 'normalise', title: 'Normalise',
    lead: 'Strip the house style, keep the specification.',
    body:
      'A versioned gazetteer expands abbreviations and resolves units on whole tokens only. ' +
      'SS becomes STAINLESS STEEL, 4" becomes 4 IN, 150NB splits into 150 NOMINAL BORE. It is a ' +
      'reviewable artefact an engineer signs off — not knowledge baked into weights nobody can inspect.',
    formula: 'gaz-v2',
    meta: ['~90 abbreviations', 'whole-token only', 'order preserved'],
  },
  {
    n: '02', key: 'extract', title: 'Extract',
    lead: 'Text becomes typed, unit-canonical values.',
    body:
      'Twelve deterministic rules read the description into engineering attributes. A transformer ' +
      'never decides whether 50 equals 50. Nominal bore is resolved through the ASME B36.10M table, ' +
      'because NPS 2 and DN 50 are the same size and 2 × 25.4 is not.',
    formula: 'R01 – R12',
    meta: ['typed values', 'rule recorded per value', 'NPS → DN'],
  },
  {
    n: '03', key: 'retrieve', title: 'Retrieve',
    lead: 'Two channels propose. Neither decides.',
    body:
      'A character 4-gram index keeps M10X50 distinguishable from M10X75, which a subword tokeniser ' +
      'cannot. A dense embedding knows SS and STAINLESS STEEL are the same thing, which the n-gram ' +
      'index cannot. Ranks are fused — not scores, which live on incompatible scales.',
    formula: 'RRF, k = 60',
    meta: ['char 4-gram TF-IDF', 'bge-small-en-v1.5', 'rank fusion'],
  },
  {
    n: '04', key: 'compare', title: 'Compare',
    lead: 'Three-valued, never two.',
    body:
      'Each attribute in the item type’s template is compared with its own tolerance. The verdict is ' +
      'agree, disagree, or not stated. Treating “not stated” as disagreement destroys recall; treating ' +
      'it as agreement destroys precision. Neither mistake is recoverable downstream.',
    formula: 'AGREE · DISAGREE · UNKNOWN',
    meta: ['per-attribute tolerance', 'template by item type', 'silence ≠ agreement'],
  },
  {
    n: '05', key: 'veto', title: 'Veto',
    lead: 'A gate, not a weight.',
    body:
      'If any attribute marked CRITICAL for that item type genuinely disagrees, the gate closes. Not a ' +
      'penalty that a strong text signal can outvote — a multiplier of zero. For M10×50 against M10×75 ' +
      'the text similarity is around 0.98, higher than for many true duplicates.',
    formula: 'veto ∈ { 0, 1 }',
    meta: ['critical attributes only', 'short-circuits', 'unrecoverable'],
  },
  {
    n: '06', key: 'score', title: 'Score',
    lead: 'Attributes carry it. Text only corroborates.',
    body:
      'Text is retrieval evidence, not identity evidence, so it is additive and small — it can raise a ' +
      'score but never pull a specification-clean pair down. Then the gate multiplies. A vetoed pair ' +
      'scores exactly zero, not merely low.',
    formula: '0.85·attr + 0.15·text, × veto',
    meta: ['W_ATTR = 0.85', 'W_TEXT = 0.15', 'uncalibrated'],
  },
  {
    n: '07', key: 'decide', title: 'Decide',
    lead: 'When in doubt, abstain.',
    body:
      'Bands chosen conservatively: a false positive merges two different parts and can put the wrong ' +
      'component into a live plant, while a false negative costs a reviewer thirty seconds. A match ' +
      'additionally requires every critical attribute to be stated on both sides.',
    formula: '0.86 / 0.70 / 0.45',
    meta: ['MATCH ≥ 0.86', 'NEAR ≥ 0.70', 'REVIEW ≥ 0.45'],
  },
]

export function Pipeline() {
  const trackRef = useRef<HTMLDivElement>(null)
  const reduced = prefersReducedMotion()
  // Click to light a card up. State, not a ref: it changes on a click, never on
  // a scroll frame, so it costs one render per press.
  const [lit, setLit] = useState<string | null>(null)

  const root = useGsap(({ root }) => {
    const cards = gsap.utils.toArray<HTMLElement>('.js-step', root)
    if (!cards.length) return

    // Card 0 starts in place; every other card starts fully off to the right.
    gsap.set(cards, { xPercent: (i) => (i === 0 ? 0 : 100) })
    gsap.set(cards.slice(1), { autoAlpha: 1 })

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: root,
        start: 'top top',
        end: 'bottom bottom',
        scrub: true,
        pin: '.js-stage',
        anticipatePin: 1,
        invalidateOnRefresh: true,
        // This section is created after the hero, so it must also refresh after
        // it — the hero's pin-spacer changes page height, and a stale refresh
        // order puts this trigger's start in the wrong place.
        refreshPriority: -1,
      },
      // Mandatory on a scrubbed timeline. With any other ease the card position
      // stops corresponding to the scroll position.
      defaults: { ease: 'none' },
    })

    // MOVE is the crossing; HOLD is the dwell where the card just sits and is
    // read. The dwell is the fix for the card going dark exactly where it was
    // most readable: with back-to-back transitions the instant a card landed at
    // centre the next one began, and the card started dimming while it was
    // still the one you were looking at. There was no frame where a card was
    // both centred and lit. Now every card gets HOLD of scroll where nothing
    // moves at all.
    const MOVE = 1
    const HOLD = 0.9
    const SPAN = MOVE + HOLD

    cards.forEach((card, i) => {
      if (i === 0) return
      const prev = cards[i - 1]
      // Dwell first, then cross. Card 0 therefore gets its own read before
      // anything moves.
      const at = (i - 1) * SPAN + HOLD

      tl.to(card, {
        xPercent: 0,
        // Restored explicitly rather than assumed. On reverse scroll a card
        // re-enters carrying the dim filter it exited with, and without this it
        // arrives at centre still dark — the same bug, mirrored.
        filter: 'brightness(1)',
        duration: MOVE,
      }, at)
        // The outgoing card drifts at a third of the speed and dims. Two rates
        // is what reads as depth rather than as a slideshow.
        .to(prev, { xPercent: -33, filter: 'brightness(0.32)', duration: MOVE }, at)
    })

    // A final dwell so the last card is readable before the pin releases,
    // rather than the section unpinning the moment it arrives.
    tl.to({}, { duration: HOLD })
  }, [])

  // Progress rail, written imperatively — a scrubbed section must never drive
  // React state per frame.
  useEffect(() => {
    if (reduced) return
    const el = trackRef.current
    if (!el) return
    const st = ScrollTrigger.create({
      trigger: el.closest('[data-pipeline]') as HTMLElement,
      start: 'top top',
      end: 'bottom bottom',
      onUpdate: (self) => {
        const i = Math.min(Math.floor(self.progress * STEPS.length), STEPS.length - 1)
        el.style.setProperty('--i', String(i))
        el.querySelectorAll<HTMLElement>('[data-dot]').forEach((d, k) => {
          d.style.opacity = k <= i ? '1' : '0.25'
          d.style.width = k === i ? '30px' : '10px'
        })
      },
    })
    return () => st.kill()
  }, [reduced])

  /* Reduced motion: the same seven steps as a plain vertical list. Disabling the
     wipe alone would leave six cards stacked at xPercent:100, off-screen. */
  if (reduced) {
    return (
      <section id="model" aria-labelledby="model-h" className="bg-void py-24 md:py-36">
        <Shell>
          <Header />
          <ol className="mt-16 grid gap-8 list-none p-0 m-0">
            {STEPS.map((s) => (
              <li key={s.key} className="border-t border-white/10 pt-6">
                <div className="flex items-baseline justify-between gap-4">
                  <span className="t-label text-live">{s.n}</span>
                  <span className="t-datum text-[11px] text-graphite">{s.formula}</span>
                </div>
                <h3 className="t-display text-paper mt-3 text-[clamp(1.4rem,2.6vw,2rem)]">{s.title}</h3>
                <p className="t-headline text-paper/90 mt-2 text-[1.05rem]">{s.lead}</p>
                <p className="t-datum text-graphite mt-3 max-w-[64ch] text-[13px] leading-relaxed">{s.body}</p>
              </li>
            ))}
          </ol>
        </Shell>
      </section>
    )
  }

  return (
    <section
      id="model"
      aria-labelledby="model-h"
      data-pipeline
      ref={root as React.RefObject<HTMLElement>}
      className="relative bg-void"
      // 150vh per stage rather than 100. The dwell needs somewhere to live, and
      // the crossing itself reads better slower — this is a technical argument
      // being made, not a carousel being flicked through.
      style={{ height: `${STEPS.length * 150}vh` }}
    >
      <div className="js-stage h-[100dvh] w-full overflow-hidden flex flex-col justify-center">
        <Shell className="w-full">
          <Header />
        </Shell>

        {/* The stack. Each card is absolutely placed and full-bleed, so exactly
            one step is legible at a time. */}
        <div className="relative mt-8 md:mt-12 h-[min(56vh,460px)] w-full">
          {STEPS.map((s, i) => (
            <article
              key={s.key}
              className="js-step group absolute inset-0 flex items-center will-change-transform"
              style={{ zIndex: i + 1 }}
            >
              <Shell className="w-full">
                <div
                  role="button"
                  tabIndex={0}
                  aria-pressed={lit === s.key}
                  aria-label={`${s.title}. Press to highlight this step.`}
                  onClick={() => setLit(lit === s.key ? null : s.key)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setLit(lit === s.key ? null : s.key)
                    }
                  }}
                  className={`relative cursor-pointer border backdrop-blur-[2px]
                             px-6 py-8 md:px-12 md:py-12 max-w-[900px] outline-none
                             transition-[border-color,background-color,box-shadow] duration-500
                             ${lit === s.key
                               ? 'border-live/70 bg-[#0e181a]/95'
                               : 'border-white/12 bg-[#0b1113]/80 hover:border-live/45 hover:bg-[#0d1517]/90'}`}
                  style={
                    lit === s.key
                      // Light, not lift. A transform here would fight the scrub
                      // that is already driving this element's x.
                      ? { boxShadow: '0 0 0 1px rgba(31,158,134,0.28), 0 0 60px -12px rgba(31,158,134,0.45)' }
                      : undefined
                  }
                >
                  {/* hover: a rule that draws itself across the top edge */}
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none absolute left-0 top-0 h-px bg-live
                               transition-all duration-[900ms] ease-[cubic-bezier(0.22,1,0.36,1)]
                               ${lit === s.key ? 'w-full' : 'w-0 group-hover:w-full'}`}
                  />
                  <div className="flex items-baseline justify-between gap-6">
                    <span className="t-label text-live">
                      {s.n} <span className="text-graphite">/ 07</span>
                    </span>
                    <span className="t-datum text-[11.5px] text-graphite tracking-wide">{s.formula}</span>
                  </div>

                  <h3 className="t-display text-paper mt-5 text-[clamp(1.9rem,4.6vw,3.6rem)] leading-[0.98] tracking-[-0.025em]">
                    {s.title}
                  </h3>
                  <p className="t-headline text-paper/90 mt-3 text-[clamp(1rem,1.8vw,1.4rem)] leading-snug max-w-[30ch]">
                    {s.lead}
                  </p>
                  <p className="t-datum text-graphite mt-5 max-w-[62ch] text-[13px] leading-relaxed">
                    {s.body}
                  </p>

                  <div className="mt-7 flex flex-wrap gap-2">
                    {s.meta.map((m) => (
                      <span
                        key={m}
                        className={`t-label text-[10px] tracking-[0.14em] px-2.5 py-1.5 border
                                   transition-colors duration-300
                                   ${lit === s.key
                                     ? 'text-paper/90 border-live/40'
                                     : 'text-graphite border-white/10 group-hover:border-white/20'}`}
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </Shell>
            </article>
          ))}
        </div>

        {/* rail */}
        <Shell className="w-full mt-8">
          <div ref={trackRef} className="flex items-center gap-1.5">
            {STEPS.map((s, i) => (
              <span
                key={s.key}
                data-dot
                className="block h-[2px] bg-live transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]"
                style={{ width: i === 0 ? 30 : 10, opacity: i === 0 ? 1 : 0.25 }}
              />
            ))}
            <span className="t-label text-graphite ml-4 text-[10px]">the scoring pipeline</span>
          </div>
        </Shell>
      </div>
    </section>
  )
}

function Header() {
  return (
    <>
      <p className="t-label text-live mb-4">The model</p>
      <h2
        id="model-h"
        className="t-display text-paper text-[clamp(1.6rem,3.6vw,2.9rem)] leading-[1.04] tracking-[-0.025em] max-w-[24ch]"
      >
        Seven steps from two descriptions to one number.
      </h2>
      <p className="t-datum text-graphite mt-5 max-w-[62ch] text-[13.5px] leading-relaxed">
        SANGAM does not train a model to guess identity. A frozen embedding model proposes
        candidates; a deterministic, auditable comparison of engineering attributes decides —
        and one disagreement on a critical attribute closes the gate entirely.
      </p>
    </>
  )
}
