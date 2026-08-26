import { Shell, Lines } from '../components/Primitives'
import { SOURCE_RECORDS, NORMALISED, CANONICAL } from '../lib/content'
import { useGsap, gsap, isMobile, EASE_INOUT, DUR, EASE, STAGGER } from '../lib/motion'

/**
 * HERO + RESOLUTION — the one continuous scrubbed animation on the page.
 *
 * Everything else in this experience is a discrete reveal. The budget is spent
 * here because this is the single idea a visitor must leave with: different
 * language, same material, and nothing was thrown away.
 *
 * The scrub, by progress:
 *   0.00  five records scattered on their own origins, paper ground
 *   0.10  headline drops away, records begin travelling to a shared axis
 *   0.25  records align for the first time; the thread draws through them
 *   0.40  text re-typesets to normalised form, house styles removed
 *   0.55  records collapse into four canonical attributes; sources dock left
 *   0.70  NMC identity stamps in
 *   0.85  ground reaches void, traceability count resolves
 *   1.00  pin releases
 *
 * On viewports under 768px the pin is not registered at all. Pinning fights
 * momentum scrolling on touch, so mobile receives the same narrative as three
 * discrete states instead of the same mechanism compressed.
 */
export function Thesis() {
  const root = useGsap(({ root }) => {
    const q = gsap.utils.selector(root)

    // ── Load choreography ────────────────────────────────────────────────
    // Disclosure arrives first, before any claim. Then the evidence, printed
    // as records. Then the headline, which is only a caption to what the
    // visitor has already noticed.
    const intro = gsap.timeline({ defaults: { ease: EASE } })
    intro
      .fromTo(q('.js-chrome'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.1, ease: 'none' }, 0.15)
      .fromTo(
        q('.js-record'),
        { autoAlpha: 0 },
        { autoAlpha: 1, duration: 0.1, ease: 'none', stagger: STAGGER.hero },
        0.25,
      )
      .fromTo(
        q('.js-hero-copy .js-line'),
        { yPercent: 105, autoAlpha: 0 },
        { yPercent: 0, autoAlpha: 1, duration: DUR.slow, stagger: STAGGER.lines },
        0.8,
      )
      .fromTo(q('.js-standfirst'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, 1.2)

    // Mobile gets the same narrative as static stacked states rather than the
    // same mechanism compressed: pinning fights momentum scrolling on touch.
    if (isMobile()) return

    // From here the scrub WILL run, so the resolved block becomes an overlay
    // and starts hidden. Doing this in JS rather than in the markup means that
    // with no JS, on mobile, or under reduced motion the resolved state stays
    // in normal flow and readable, instead of being permanently invisible.
    gsap.set(q('.js-resolved'), { position: 'absolute', inset: 0, autoAlpha: 0 })
    gsap.set(q('.js-trace'), { autoAlpha: 0 })
    gsap.set(q('.js-verdict'), { autoAlpha: 0 })

    // ── The scrub ────────────────────────────────────────────────────────
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: root,
        start: 'top top',
        end: '+=180%',
        scrub: 1,
        // Pin the trigger itself. Pinning a child while triggering off the
        // parent makes the growing pin-spacer alter the trigger's own height,
        // which feeds back into the progress calculation and makes the scrub
        // oscillate. Observed on this page before the fix.
        pin: true,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      },
      defaults: { ease: EASE_INOUT },
    })

    // The ground inverts once, here, and stays inverted for the rest of the
    // page. One deliberate switch, not section-level theme flipping.
    tl.to(root, { backgroundColor: '#000000', duration: 1 }, 0)
      .to(q('.js-hero-copy'), { yPercent: -40, autoAlpha: 0, duration: 0.12 }, 0)
      .to(q('.js-ink'), { color: '#f4f2ed', duration: 0.5 }, 0)
      .to(q('.js-dim'), { color: '#8a9096', duration: 0.5 }, 0)

    // 0.10 → 0.25  converge on a shared axis, then align.
    SOURCE_RECORDS.forEach((rec, i) => {
      tl.to(
        q(`[data-record="${rec.id}"]`),
        { x: -rec.offset, y: i * -4, duration: 0.15 },
        0.1,
      )
    })

    // 0.25  the thread draws through the newly shared origins.
    tl.to(q('.js-thread-path'), { strokeDashoffset: 0, duration: 0.12, ease: 'none' }, 0.25)

    // 0.40  normalisation. Text snaps to its resolved form token by token;
    // it does not crossfade, because data snaps.
    SOURCE_RECORDS.forEach((rec, i) => {
      tl.add(() => {
        const el = root.querySelector<HTMLElement>(`[data-record="${rec.id}"] .js-text`)
        if (el) el.textContent = NORMALISED[rec.id]
      }, 0.4 + i * 0.015)
    })

    // 0.55  collapse. The five rows give way to four canonical attributes,
    // and the sources dock into the left margin rather than disappearing.
    tl.to(q('.js-records'), { autoAlpha: 0, duration: 0.08 }, 0.55)
      .fromTo(q('.js-attrs'), { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.12 }, 0.58)
      .fromTo(q('.js-chip'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.08, stagger: 0.03 }, 0.6)
      .to(q('.js-thread-path'), { stroke: '#0e7c6b', duration: 0.1 }, 0.6)

    // 0.70  the identity is minted. A hard cut, no travel.
    tl.fromTo(q('.js-nmc'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.04, ease: 'none' }, 0.7)

    // 0.85  the clause the problem statement actually asked for.
    tl.fromTo(q('.js-trace'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.06 }, 0.85)
      .fromTo(q('.js-verdict'), { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.1 }, 0.9)
  }, [])

  return (
    <div
      ref={root as React.RefObject<HTMLDivElement>}
      className="relative min-h-[100dvh] overflow-hidden flex flex-col"
      style={{ backgroundColor: '#f4f2ed' }}
    >
      <>
        {/* Chrome. Disclosure is pinned here for the whole opening, never a footnote. */}
        <header className="js-chrome relative z-20 pt-8 md:pt-10">
          <Shell className="flex items-start justify-between gap-6">
            <p className="t-label js-ink text-ink">
              SIH26099 <span aria-hidden="true">·</span> MoP&amp;NG / CPCL
            </p>
            <p className="t-label border border-current/25 px-2.5 py-1.5 js-ink text-ink">
              Synthetic data
            </p>
          </Shell>
        </header>

        <div className="relative z-10 flex-1 flex items-center py-10">
          <Shell className="w-full">
            <div className="grid gap-12 md:gap-16">
              {/* The evidence sits above the headline and occupies the optical
                  centre. A visitor who reads only these five rows already has
                  the problem statement. */}
              <div className="relative">
                <ul className="js-records grid gap-4 md:gap-5 list-none p-0 m-0">
                  {SOURCE_RECORDS.map((rec) => (
                    <li
                      key={rec.id}
                      data-record={rec.id}
                      className="js-record relative"
                      style={{ '--offset': `${rec.offset}px` } as React.CSSProperties}
                    >
                      <span className="js-dim t-label text-slate block mb-1.5">
                        {rec.org} <span aria-hidden="true">·</span> {rec.code}
                      </span>
                      <span className="js-text t-datum block js-ink text-ink" style={{ fontSize: rec.size }}>
                        {rec.text}
                      </span>
                    </li>
                  ))}
                </ul>

                {/* Canonical attributes. Present in the DOM from the start so
                    screen readers and reduced-motion users get the resolution
                    without the animation. */}
                <div className="js-resolved js-attrs mt-14 md:mt-16 flex flex-col justify-center">
                  <p className="js-nmc t-datum text-live text-lg mb-6 tracking-wide">{CANONICAL.nmc}</p>
                  <dl className="grid gap-3 m-0">
                    {CANONICAL.attributes.map((a) => (
                      <div key={a.label} className="grid grid-cols-[7rem_1fr] gap-4 items-baseline">
                        <dt className="js-dim t-label text-slate">{a.label}</dt>
                        <dd className="js-ink t-datum m-0 text-ink">{a.value}</dd>
                      </div>
                    ))}
                  </dl>
                  <div className="js-trace mt-10">
                    <p className="js-dim t-label text-slate mb-4">
                      Traceability <span aria-hidden="true">·</span> 5 source codes retained
                    </p>
                    {/* The original records, kept. Each stays joined to the
                        canonical identity by the thread running down the left.
                        This is the clause the problem statement actually asks
                        for, and it is the reason the whole page exists. */}
                    <ul className="flex flex-wrap gap-x-6 gap-y-2 list-none p-0 m-0">
                      {SOURCE_RECORDS.map((rec) => (
                        <li key={rec.id} className="js-chip t-datum text-[11px]">
                          <span className="js-dim text-slate">{rec.org}</span>{' '}
                          <span className="js-ink text-ink">{rec.code}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Headline. A caption to evidence already seen, not a slogan. */}
              <div className="js-hero-copy">
                <Lines
                  as="h1"
                  id="thesis-heading"
                  lines={['One bolt.', 'Five names.', 'No code in common.']}
                  className="t-display js-ink text-ink text-[clamp(2.75rem,8vw,7rem)]"
                />
                <p className="js-standfirst js-dim t-datum text-slate mt-8 max-w-[52ch]">
                  One Nation, One Material Code. Every organisation keeps its own code, permanently.
                </p>
              </div>

              <p className="js-verdict js-ink t-headline text-ink text-[clamp(1.5rem,3.5vw,2.75rem)]">
                Different language. Same material.
              </p>
            </div>
          </Shell>
        </div>

        {/* The thread. One SVG path, drawn by stroke-dashoffset. Decorative in
            the accessibility tree; the relationship it depicts is stated in text. */}
        <svg
          className="pointer-events-none absolute left-[calc(var(--shell)-14px)] top-0 h-full w-8 z-0"
          aria-hidden="true"
          preserveAspectRatio="none"
          viewBox="0 0 32 1000"
        >
          <path
            className="js-thread-path"
            d="M16 0 L16 1000"
            stroke="#b9bec4"
            strokeWidth="1"
            fill="none"
            strokeDasharray="1000"
            strokeDashoffset="1000"
          />
        </svg>
      </>
    </div>
  )
}
