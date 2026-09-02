import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { House, MagnifyingGlass, Cube, ArrowLeft, Stack, Graph } from '@phosphor-icons/react'
import './tokens.css'

import { Home } from './screens/Home'
import { Analyse } from './screens/Analyse'
import { Canonical } from './screens/Canonical'
import { Explorer } from './screens/Explorer'
import { Visualize } from './screens/Visualize'
import { NotFound } from './screens/NotFound'

/**
 * Application shell.
 *
 * A left rail rather than a top bar: this is a tool someone keeps open, and a
 * persistent rail makes the four places you can be visible at all times
 * without spending vertical space, which is the scarce axis on a dense screen.
 */

// Labelled for contents, not as umbrellas. "Home" said nothing about the
// catalogue figures and search entry that live there; "Visualization" named a
// technique rather than the relationships it shows.
const NAV = [
  { to: '/platform',              label: 'Overview',      Icon: House,           end: true },
  { to: '/platform/analyse',      label: 'Analyse',       Icon: MagnifyingGlass, end: false },
  { to: '/platform/explorer',     label: 'Explorer',      Icon: Stack,           end: false },
  { to: '/platform/visualization', label: 'Relationships', Icon: Graph,           end: false },
]

function Rail() {
  return (
    <nav
      aria-label="Sections"
      // Below lg the rail is a horizontal row, and four labels do not fit a
      // 375px viewport — it needed 486px and pushed the whole page sideways.
      // The row scrolls itself instead, which is the platform-native answer and
      // keeps the page from ever scrolling horizontally. Snap points stop it
      // resting mid-label.
      className="flex lg:flex-col gap-1 lg:gap-0.5
                 -mx-4 px-4 lg:mx-0 lg:px-0
                 overflow-x-auto lg:overflow-visible rail-scroll
                 snap-x snap-mandatory lg:snap-none"
    >
      {NAV.map(({ to, label, Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `press group relative flex shrink-0 snap-start items-center gap-3 rounded-[var(--radius-control)] px-3 py-2.5 text-[14px] font-medium
             ${isActive
               ? 'bg-[var(--color-brand-soft)] text-[var(--color-brand)]'
               : 'text-[var(--color-text-2)] hover:bg-[var(--color-surface-3)] hover:text-[var(--color-text)]'}`
          }
        >
          {({ isActive }) => (
            <>
              <Icon size={18} weight={isActive ? 'fill' : 'regular'} aria-hidden="true" />
              {label}
              {isActive && (
                <motion.span
                  layoutId="rail-active"
                  className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full"
                  style={{ background: 'var(--color-brand)' }}
                  transition={{ type: 'spring', duration: 0.4, bounce: 0.15 }}
                />
              )}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

function Chrome() {
  const loc = useLocation()
  return (
    <div className="app">
      <a href="#content" className="skip-link">Skip to content</a>

      <div className="mx-auto max-w-[1360px] px-4 sm:px-6 lg:px-8">
        <header
          className="material-chrome scroll-edge sticky top-0 z-30 -mx-4 sm:-mx-6 lg:-mx-8
                     px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-6 py-4"
        >
          <Link to="/platform" className="flex items-center gap-2.5 group">
            <span
              className="grid h-8 w-8 place-items-center rounded-lg text-white"
              style={{ background: 'var(--color-brand)' }}
              aria-hidden="true"
            >
              <Cube size={17} weight="fill" />
            </span>
            <span className="leading-tight">
              <span className="block text-[15px] font-bold tracking-[0.02em] text-[var(--color-text)]">
                SANGAM
              </span>
              <span className="block text-[11px] text-[var(--color-text-3)]">
                SIH26099 · MoP&amp;NG / CPCL
              </span>
            </span>
          </Link>

          <a href="/" className="press link text-[13px] font-medium inline-flex items-center gap-1.5">
            <ArrowLeft size={13} weight="bold" aria-hidden="true" />
            Back to the story
          </a>
        </header>

        <div className="grid lg:grid-cols-[190px_minmax(0,1fr)] gap-6 lg:gap-8 py-6 min-w-0">
          {/* min-w-0: a grid child defaults to min-width:auto, so without this the
              aside sizes to its content and the rail's overflow-x-auto has
              nothing to clip against — the page scrolls sideways instead. */}
          <aside className="min-w-0 lg:sticky lg:top-6 lg:self-start">
            <Rail />
          </aside>

          <main id="content" className="min-w-0 pb-16">
            <AnimatePresence mode="wait">
              <motion.div
                key={loc.pathname}
                // Enters from below and leaves back down the way it came. It
                // previously entered at y:8 and exited at y:-4 — in from the
                // bottom, out through the top, and at different magnitudes.
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
              >
                <Routes location={loc}>
                  <Route path="/platform" element={<Home />} />
                  <Route path="/platform/analyse" element={<Analyse />} />
                  <Route path="/platform/material/:nmc" element={<Canonical />} />
                  <Route path="/platform/explorer" element={<Explorer />} />
                  <Route path="/platform/visualization" element={<Visualize />} />
                  {/* Every unmatched path previously rendered the shell with an
                      empty content area, which reads as a broken build. */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </div>
  )
}

export function Platform() {
  // The document body is painted dark for the landing page; repaint it for
  // the application so overscroll and the area behind the layout match.
  useEffect(() => {
    const prev = document.body.style.background
    document.body.style.background = '#f4f2ee'
    return () => { document.body.style.background = prev }
  }, [])

  return (
    <BrowserRouter>
      <Chrome />
    </BrowserRouter>
  )
}
