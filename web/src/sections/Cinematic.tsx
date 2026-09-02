import { useEffect, useRef, useState } from 'react'
import { Shell } from '../components/Primitives'
import { useGsap, ScrollTrigger, prefersReducedMotion } from '../lib/motion'

/* ══════════════════════════════════════════════════════════════════════════
   THE CINEMATIC HERO — six stages, one continuous transformation.

   The screw is a real rendered asset, not a generated stand-in, and the six
   narrative stages are mapped to the moments that actually occur in it. The
   frame map, read off the source at 24fps:

       f000        clean metallic screw
       f010–f088   cyan scanning plane travels head → tip
       f085–f098   plane exits; granular internal structure fully exposed
       f100–f145   structure resolves into a connected node network
       f148–f185   green energy propagates through the shaft
       f188–f240   collapses back to a clean physical screw

   SCROLL → VIDEO IS NOT LINEAR, AND THAT IS DELIBERATE

   A 1:1 map would give PHYSICAL 4% of the scroll and SCAN 32%. The opening
   beat would be gone before it could be read and the scan would outstay its
   welcome. So each stage owns exactly one sixth of the scroll and is remapped
   onto its own video range (`toVideo` below). The video is still the single
   source of truth for what is on screen — only the rate changes, the way a
   film editor holds a frame without repainting it.

   NOTHING SNAPS

   Scroll writes a *target* time. A rAF loop eases the real time toward it with
   a framerate-independent factor, so a 144Hz and a 60Hz display produce the
   same motion. That damping is also what hides decoder seek latency: the
   playhead is always chasing, so a late frame reads as weight rather than
   as a stall.

   NO PER-FRAME REACT STATE

   The playhead runs entirely through refs and direct DOM writes. React state
   changes exactly six times in the whole sequence — once per stage. The
   progress rail is written imperatively for the same reason.
   ══════════════════════════════════════════════════════════════════════════ */

type Stage = {
  key: string
  n: string
  title: string
  lead: string
  body: string
  /** Where this stage sits in the source video, measured from the frame map. */
  v0: number
  v1: number
  /** Real artefacts of the engine. Nothing here is invented for the visual. */
  signals: string[]
}

const STAGES: Stage[] = [
  {
    key: 'physical', n: '01', title: 'PHYSICAL MATERIAL',
    lead: 'Every material arrives as words.',
    body:
      'A component exists physically, but it enters the system as a line of text somebody typed — ' +
      'a description carrying its geometry, its material and its manufacturing context, in whatever ' +
      'house style that organisation happens to use.',
    v0: 0.000, v1: 0.045,
    signals: ['SOURCE RECORD', 'FREE TEXT', 'AS WRITTEN'],
  },
  {
    key: 'scan', n: '02', title: 'SCAN',
    lead: 'See beyond the spelling.',
    body:
      'Abbreviations expand, units resolve, separators unify. SS becomes STAINLESS STEEL and 4" ' +
      'becomes 4 IN — from a reviewable gazetteer a materials engineer can read and correct, not ' +
      'from weights nobody can audit.',
    v0: 0.045, v1: 0.360,
    signals: ['GAZETTEER v2', 'UNIT RESOLUTION', 'NPS → DN TABLE'],
  },
  {
    key: 'reveal', n: '03', title: 'REVEAL',
    lead: 'Understand what the words hide.',
    body:
      'The description becomes typed engineering attributes — item type, material, thread diameter, ' +
      'length, schedule, pressure class. Each value carries the rule that produced it, so a reviewer ' +
      'can see why it was read that way.',
    v0: 0.360, v1: 0.415,
    signals: ['ITEM TYPE', 'MATERIAL', 'THREAD DIA', 'LENGTH', 'SCHEDULE'],
  },
  {
    key: 'intelligence', n: '04', title: 'INTELLIGENCE',
    lead: 'Material becomes data.',
    body:
      'Two retrieval channels run in parallel. A character n-gram index treats M10X50 as an ' +
      'indivisible symbol; a dense embedding model understands that SS and STAINLESS STEEL mean the ' +
      'same thing. Their ranks are fused — neither alone is sufficient.',
    v0: 0.415, v1: 0.610,
    signals: ['CHAR 4-GRAM TF-IDF', 'bge-small-en-v1.5', 'RECIPROCAL RANK FUSION'],
  },
  {
    key: 'verdict', n: '05', title: 'VERDICT',
    lead: 'Know what it really is.',
    body:
      'Attributes are compared with real tolerances, three-valued: agree, disagree, or not stated. ' +
      'A disagreement on a critical attribute is a gate, not a penalty — it multiplies the score by ' +
      'zero. No amount of text similarity can recover it.',
    v0: 0.610, v1: 0.780,
    signals: ['CRITICAL ATTRIBUTE CHECK', 'AGREE / DISAGREE / UNKNOWN', 'VETO × 0'],
  },
  {
    key: 'decision', n: '06', title: 'DECISION',
    lead: 'Turn intelligence into action.',
    body:
      'One canonical identity, with every original organisation code still attached to it. ' +
      'Nothing is discarded, nothing is overwritten — the master gains a shared identity and each ' +
      'organisation keeps the code it has always used.',
    v0: 0.780, v1: 1.000,
    signals: ['MATCH ≥ 0.86', 'NEAR ≥ 0.70', 'REVIEW ≥ 0.45'],
  },
]

/** Scroll position → video position. Piecewise linear: equal scroll per stage. */
function toVideo(p: number): number {
  const n = STAGES.length
  const clamped = Math.min(Math.max(p, 0), 0.99999)
  const i = Math.min(Math.floor(clamped * n), n - 1)
  const local = clamped * n - i
  const s = STAGES[i]
  return s.v0 + (s.v1 - s.v0) * local
}

/* Asymmetric on purpose. Measured on the asset, the screw occupies 7%–91% of
   the frame horizontally but only 26%–85% vertically, so the top and bottom
   bands are empty and can be feathered hard — which is what actually dissolves
   the rectangle, since the clip's own vignette leaves its centre lighter than
   its corners. The horizontal feather stays tight or it eats the head and tip. */
const EDGE_MASK =
  'linear-gradient(to right, transparent 0%, #000 5%, #000 95%, transparent 100%),' +
  'linear-gradient(to bottom, transparent 0%, #000 15%, #000 88%, transparent 100%)'

const stageIndex = (p: number) =>
  Math.min(Math.max(Math.floor(p * STAGES.length), 0), STAGES.length - 1)

export function Cinematic() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const railRef = useRef<HTMLDivElement>(null)
  const [active, setActive] = useState(0)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)

  // Playhead lives here, never in state. `target` is written by scroll,
  // `eased` is what actually reaches the video element.
  const play = useRef({ target: 0, eased: 0, last: -1 })
  const activeRef = useRef(0)

  // Resolved once, synchronously, so the element is created with a real src.
  // `<source media>` children are not used: React appends them after the media
  // element has already run its resource-selection algorithm, which fires an
  // error event and drops the hero to its poster fallback on a perfectly good
  // connection. Observed on this page.
  const [src] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches
      ? '/hero/screw.mp4'
      : '/hero/screw-sm.mp4',
  )

  const root = useGsap(({ root }) => {
    if (prefersReducedMotion()) return
    // Not returned for cleanup: useGSAP reverts everything created in its
    // scope, ScrollTriggers included, across StrictMode's double invocation.
    ScrollTrigger.create({
      trigger: root,
      start: 'top top',
      end: 'bottom bottom',
      scrub: true,
      onUpdate: (self) => {
        play.current.target = self.progress
        const i = stageIndex(self.progress)
        if (i !== activeRef.current) {
          activeRef.current = i
          setActive(i)           // six times per sequence, not sixty per second
        }
        const rail = railRef.current
        if (rail) rail.style.setProperty('--fill', String(self.progress))
      },
    })
  }, [])

  // The playhead loop. Independent of React's render cycle by design.
  useEffect(() => {
    if (prefersReducedMotion()) return
    let raf = 0
    let prev = performance.now()

    const tick = (now: number) => {
      raf = requestAnimationFrame(tick)
      const dt = Math.min((now - prev) / 1000, 0.1)
      prev = now

      const p = play.current
      // Framerate-independent damping: identical motion at 60Hz and 144Hz.
      const f = 1 - Math.pow(1 - 0.12, dt * 60)
      p.eased += (p.target - p.eased) * f

      const v = videoRef.current
      if (!v || !v.duration || Number.isNaN(v.duration)) return
      const t = toVideo(p.eased) * v.duration
      // Only seek on a real change. Writing currentTime every frame thrashes
      // the decoder and produces the stutter this whole approach exists to avoid.
      if (Math.abs(t - p.last) > 1 / 60) {
        p.last = t
        try { v.currentTime = t } catch { /* seek raced a load; next frame retries */ }
      }
    }
    raf = requestAnimationFrame(tick)

    // Browsers pause rAF on a hidden tab, so a user who switches away and comes
    // back would watch the playhead ease in from wherever it froze. Snap the
    // eased value to the target on return: the correct frame is already known,
    // and easing toward it from a stale position is animation for its own sake.
    const onVisible = () => {
      if (document.hidden) return
      play.current.eased = play.current.target
      prev = performance.now()
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      cancelAnimationFrame(raf)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [])

  const stage = STAGES[active]
  const reduced = prefersReducedMotion()

  /* Reduced motion gets a genuinely different component, not the scrubbed one
     with its animation disabled. Suppressing the scrub alone would leave
     `active` pinned at 0 and the other five stages at display:none — the reader
     would lose five sixths of the content, which is a far worse outcome than
     the motion they asked to avoid. So: the poster frame once, then all six
     stages as a plain readable list. Nothing is withheld. */
  if (reduced) {
    return (
      <div className="relative bg-void" data-cinematic>
        <Shell className="py-20">
          <img
            src="/hero/screw-poster.jpg"
            alt="A steel screw, the component SANGAM analyses through its six-stage pipeline"
            className="mx-auto w-[min(92vw,680px)]"
            style={{ maskImage: EDGE_MASK, WebkitMaskImage: EDGE_MASK,
                     maskComposite: 'intersect', WebkitMaskComposite: 'source-in' }}
          />
          <div className="mt-14">
            <p className="t-display text-paper text-[clamp(1.4rem,3vw,2.2rem)] tracking-[0.04em] leading-none">
              SANGAM
            </p>
            <p className="t-label text-graphite mt-2 mb-12">
              Material Intelligence · from physical material to intelligent decisions
            </p>
            <ol className="grid gap-10 list-none p-0 m-0">
              {STAGES.map((st) => (
                <li key={st.key} className="border-t border-white/10 pt-6">
                  <p className="t-label text-live mb-2">{st.n} <span className="text-graphite">/ 06</span></p>
                  <h2 className="t-display text-paper text-[clamp(1.3rem,2.4vw,1.9rem)] leading-tight">
                    {st.title}
                  </h2>
                  <p className="t-headline text-paper/90 mt-2 text-[1.05rem]">{st.lead}</p>
                  <p className="t-datum text-graphite mt-3 max-w-[62ch] text-[13px] leading-relaxed">
                    {st.body}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {st.signals.map((sig) => (
                      <span key={sig} className="t-label text-[10.5px] tracking-[0.14em] text-graphite
                                                 border border-white/10 px-2.5 py-1.5">
                        {sig}
                      </span>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </Shell>
      </div>
    )
  }

  return (
    <div
      ref={root as React.RefObject<HTMLDivElement>}
      className="relative bg-void"
      style={{ height: '600vh' }}
    >
      <div className="sticky top-0 h-[100dvh] w-full overflow-hidden flex flex-col md:block">
        {/* Ambient wash. Always the full viewport — scoped to the video box it
            becomes a visible lit rectangle at mobile widths, which is the exact
            container edge this design exists to avoid. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(58% 45% at 50% 42%, rgba(31,158,134,0.10), transparent 70%),' +
              'radial-gradient(40% 30% at 50% 42%, rgba(79,216,232,0.08), transparent 72%)',
          }}
        />

        {/* ── the object ────────────────────────────────────────────────────
            Desktop: absolutely centred, with the narrative overlaid in the
            outer thirds. Mobile: in normal flow at the top of a stacked column,
            because three columns do not fit in 375px and overlaying the copy on
            the screw makes both unreadable. */}
        <div className="relative shrink-0 md:absolute md:inset-0 grid place-items-center pt-[9vh] md:pt-0">
          {!failed ? (
            <video
              ref={videoRef}
              className="relative w-[min(94vw,560px)] md:w-[min(58vw,760px)] max-w-none"
              style={{
                // No blend mode. The ground is set to the asset's own letterbox
                // black instead, so the rectangle disappears by matching rather
                // than by compositing. A soft edge mask absorbs the residual
                // few-unit variance across the clip.
                maskImage: EDGE_MASK,
                WebkitMaskImage: EDGE_MASK,
                maskComposite: 'intersect',
                WebkitMaskComposite: 'source-in',
                opacity: ready ? 1 : 0,
                transition: 'opacity 900ms cubic-bezier(0.22,1,0.36,1)',
              }}
              muted
              playsInline
              preload="auto"
              poster="/hero/screw-poster.jpg"
              onLoadedData={() => setReady(true)}
              onError={() => setFailed(true)}
              disablePictureInPicture
              disableRemotePlayback
              src={src}
            />
          ) : (
            <img
              src="/hero/screw-poster.jpg"
              alt="A steel screw with its internal material structure exposed"
              className="relative w-[min(94vw,560px)] md:w-[min(58vw,760px)] max-w-none"
              style={{
                maskImage: EDGE_MASK, WebkitMaskImage: EDGE_MASK,
                maskComposite: 'intersect', WebkitMaskComposite: 'source-in',
              }}
            />
          )}
        </div>

        {/* ── narrative ────────────────────────────────────────────────────
            Left column carries the story, right column the instrumentation.
            Both are pointer-transparent so the object is never occluded by an
            invisible box. */}
        <Shell className="relative flex-1 md:h-full md:pointer-events-none">
          <div className="flex flex-col justify-start gap-6 pt-6 md:pt-0
                          md:grid md:h-full md:grid-cols-12 md:items-center md:gap-8">
            {/* LEFT */}
            <div className="md:col-span-3 md:col-start-1">
              {STAGES.map((s, i) => (
                <div
                  key={s.key}
                  aria-hidden={i !== active}
                  className="transition-all duration-[700ms] ease-[cubic-bezier(0.22,1,0.36,1)]"
                  style={{
                    gridArea: '1 / 1',
                    display: i === active ? 'block' : 'none',
                    opacity: i === active ? 1 : 0,
                    filter: i === active ? 'blur(0px)' : 'blur(6px)',
                  }}
                >
                  <p className="t-label text-live mb-3">
                    {s.n} <span className="text-graphite">/ 06</span>
                  </p>
                  <h2 className="t-display text-paper text-[clamp(1.45rem,2.55vw,2.05rem)] leading-[0.98] tracking-[-0.02em]">
                    {s.title}
                  </h2>
                  <p className="t-headline text-paper/90 mt-3.5 text-[clamp(0.98rem,1.35vw,1.22rem)] leading-snug max-w-[20ch]">
                    {s.lead}
                  </p>
                  <p className="t-datum text-graphite mt-5 max-w-[30ch] text-[12.5px] leading-relaxed">
                    {s.body}
                  </p>
                </div>
              ))}
            </div>

            <div className="hidden md:block md:col-span-6" aria-hidden="true" />

            {/* RIGHT — instrumentation, not decoration. Every label is a real
                artefact of the running engine. */}
            <div className="md:col-span-3 md:col-start-10 md:text-right">
              <div className="inline-flex flex-col gap-2 md:items-end">
                {stage.signals.map((sig, k) => (
                  <span
                    key={sig}
                    className="t-label text-[10.5px] tracking-[0.14em] text-graphite
                               border border-white/10 px-2.5 py-1.5 bg-white/[0.02]"
                    style={{
                      animation: reduced ? undefined : `sig-in 620ms ${k * 90}ms both cubic-bezier(0.22,1,0.36,1)`,
                    }}
                  >
                    {sig}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Shell>

        {/* ── progress rail ────────────────────────────────────────────── */}
        <div
          ref={railRef}
          className="pointer-events-none absolute right-4 md:right-8 top-1/2 -translate-y-1/2
                     hidden sm:flex flex-col gap-3"
          style={{ ['--fill' as string]: '0' }}
          aria-hidden="true"
        >
          {STAGES.map((s, i) => (
            <div key={s.key} className="flex items-center gap-2.5 justify-end">
              <span
                className="t-label text-[9.5px] tracking-[0.16em] transition-colors duration-500"
                style={{ color: i === active ? 'var(--color-paper)' : 'transparent' }}
              >
                {s.title}
              </span>
              <span
                className="block h-[2px] transition-all duration-500"
                style={{
                  width: i === active ? 26 : 12,
                  background: i === active ? 'var(--color-live)' : 'rgba(255,255,255,0.22)',
                }}
              />
            </div>
          ))}
        </div>

        {/* ── intro, first screen only ─────────────────────────────────── */}
        <div
          className="pointer-events-none absolute inset-x-0 bottom-4 md:bottom-14
                     transition-opacity duration-700 hidden sm:block"
          style={{ opacity: active === 0 ? 1 : 0 }}
        >
          <Shell className="flex items-end justify-between gap-6">
            <div>
              <p className="t-display text-paper text-[clamp(1.4rem,3vw,2.2rem)] tracking-[0.04em] leading-none">
                SANGAM
              </p>
              <p className="t-label text-graphite mt-2">Material Intelligence</p>
            </div>
            <p className="t-datum text-graphite text-[12px] max-w-[26ch] text-right hidden sm:block">
              From physical material to intelligent decisions.
              <br />
              <span className="text-paper/50">Scroll to begin ↓</span>
            </p>
          </Shell>
        </div>
      </div>
    </div>
  )
}
