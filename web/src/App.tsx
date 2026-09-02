import { useEffect } from 'react'
import Lenis from 'lenis'
import { ScrollTrigger, prefersReducedMotion } from './lib/motion'

import { Cinematic } from './sections/Cinematic'
import { Product } from './sections/Product'
import { Cta } from './sections/Cta'
import { Platform } from './app/Platform'

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
      <a href="#product" className="skip-link">Skip the opening sequence</a>

      <main id="main">
        {/* The page's only h1. The cinematic sequence carries h2s per stage, so
            the document outline is one heading deep rather than six competing
            top-level headings. */}
        <h1 className="sr-only">
          SANGAM — Material Intelligence. From physical material to intelligent decisions.
        </h1>
        <Cinematic />
        <Product />
        <Cta />
      </main>
    </>
  )
}
