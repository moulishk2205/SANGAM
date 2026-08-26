import { useEffect } from 'react'
import Lenis from 'lenis'
import { ScrollTrigger, prefersReducedMotion } from './lib/motion'

import { Thesis } from './sections/Thesis'
import { Scale } from './sections/Scale'
import { Trap } from './sections/Trap'
import { Veto } from './sections/Veto'
import { Engine } from './sections/Engine'
import { Unknown } from './sections/Unknown'
import { Validation } from './sections/Validation'
import { Disclosure } from './sections/Disclosure'
import { Foundation } from './sections/Foundation'
import { Future } from './sections/Future'
import { Cta } from './sections/Cta'
import { Platform } from './platform/Platform'

export default function App() {
  // Two routes, no router. The platform is not built yet, so a dependency for
  // one path is not warranted; this gets replaced by a real router when the
  // platform lands.
  const onPlatform =
    typeof window !== 'undefined' && window.location.pathname.startsWith('/platform')

  useEffect(() => {
    if (onPlatform) return
    // Reduced motion gets the native scroller. Smooth scrolling is motion.
    if (prefersReducedMotion()) return

    const lenis = new Lenis({ autoRaf: true })
    lenis.on('scroll', ScrollTrigger.update)

    // Layout settles after fonts load; stale pin measurements are the most
    // common cause of a pinned section jumping on first scroll.
    const onFonts = () => ScrollTrigger.refresh()
    document.fonts?.ready.then(onFonts)

    return () => {
      lenis.destroy()
      ScrollTrigger.getAll().forEach((t) => t.kill())
    }
  }, [onPlatform])

  if (onPlatform) return <Platform />

  return (
    <>
      <a href="#scale" className="skip-link">Skip the opening animation</a>

      {/* The page's only h1 lives in Thesis: "One bolt. Five names. No code in
          common." It is the real headline, so there is no second hidden one. */}
      <main id="main">
        <Thesis />
        <Scale />
        <Trap />
        <Veto />
        <Engine />
        <Unknown />
        <Validation />
        <Disclosure />
        <Foundation />
        <Future />
        <Cta />
      </main>
    </>
  )
}
