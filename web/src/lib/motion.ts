import { useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'

gsap.registerPlugin(ScrollTrigger, useGSAP)

/**
 * Motion system for the SIH26099 landing page.
 *
 * Two laws, applied everywhere:
 *
 *   PROSE EASES.  Sentences and headings travel, on power2.out.
 *   DATA SNAPS.   Codes, scores, counters and verdicts change with no travel
 *                 and no easing. A number that glides is a number being sold
 *                 to you; a number that snaps is a number being reported.
 *
 * Budget: exactly one continuous scrubbed animation on the whole page (the
 * thesis, in ConvergenceSection). Everything else is a discrete reveal, a
 * hover, or a state transition.
 */

export const EASE = 'power2.out'
export const EASE_INOUT = 'power2.inOut'

export const DUR = { fast: 0.2, base: 0.5, slow: 0.8 } as const
export const STAGGER = { tight: 0.03, lines: 0.06, hero: 0.14 } as const

export const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** Below this width the pinned thesis animation is replaced by discrete states.
 *  Pinning fights momentum scrolling on touch devices. */
export const MOBILE = 768
export const isMobile = () => typeof window !== 'undefined' && window.innerWidth < MOBILE

/**
 * Scoped GSAP animation with guaranteed cleanup.
 *
 * Uses GSAP's official `useGSAP` hook rather than a hand-rolled
 * `useEffect` + `gsap.context()`. Under React StrictMode the effect is invoked
 * twice, and a hand-rolled context leaves `fromTo` start-states applied after
 * the first cleanup, so entrance animations never complete and the element
 * stays at opacity 0. Observed and bisected on this page. `useGSAP` reverts
 * correctly across the double invocation, so StrictMode stays on.
 *
 * Under reduced motion the setup function never runs, so nothing is ever left
 * in a hidden pre-animation state. Elements marked `data-reveal` are forced
 * visible by CSS in that mode.
 */
export function useGsap(
  setup: (ctx: { root: HTMLElement }) => void,
  deps: unknown[] = [],
) {
  const ref = useRef<HTMLElement | null>(null)

  useGSAP(
    () => {
      const root = ref.current
      if (!root || prefersReducedMotion()) return
      setup({ root })
    },
    { scope: ref as React.RefObject<HTMLElement>, dependencies: deps },
  )

  return ref
}

/** PROSE: a plain rise. For blocks that are not type. */
export function revealUp(
  targets: gsap.TweenTarget,
  opts: { stagger?: number; trigger?: Element; start?: string; y?: number } = {},
) {
  return gsap.fromTo(
    targets,
    { y: opts.y ?? 24, autoAlpha: 0 },
    {
      y: 0,
      autoAlpha: 1,
      duration: DUR.base,
      ease: EASE,
      stagger: opts.stagger ?? STAGGER.tight,
      scrollTrigger: opts.trigger
        ? { trigger: opts.trigger, start: opts.start ?? 'top 82%', toggleActions: 'play none none reverse' }
        : undefined,
    },
  )
}

/** DATA: appears. No travel, no ease. A hard cut. */
export function snapIn(
  targets: gsap.TweenTarget,
  opts: { stagger?: number; trigger?: Element; start?: string; delay?: number } = {},
) {
  return gsap.fromTo(
    targets,
    { autoAlpha: 0 },
    {
      autoAlpha: 1,
      duration: 0.1,
      ease: 'none',
      delay: opts.delay ?? 0,
      stagger: opts.stagger ?? 0.05,
      scrollTrigger: opts.trigger
        ? { trigger: opts.trigger, start: opts.start ?? 'top 82%', toggleActions: 'play none none reverse' }
        : undefined,
    },
  )
}

export { gsap, ScrollTrigger }
