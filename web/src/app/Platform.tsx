import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { House, MagnifyingGlass, Cube, ArrowLeft, Stack } from '@phosphor-icons/react'
import './tokens.css'

import { Home } from './screens/Home'
import { Analyse } from './screens/Analyse'
import { Canonical } from './screens/Canonical'
import { Explorer } from './screens/Explorer'

/**
 * Application shell.
 *
 * A left rail rather than a top bar: this is a tool someone keeps open, and a
 * persistent rail makes the four places you can be visible at all times
 * without spending vertical space, which is the scarce axis on a dense screen.
 */

const NAV = [
  { to: '/platform',           label: 'Home',     Icon: House,           end: true },
  { to: '/platform/analyse',   label: 'Analyse',  Icon: MagnifyingGlass, end: false },
  { to: '/platform/explorer',  label: 'Explorer', Icon: Stack,           end: false },
]

function Rail() {
  return (
    <nav aria-label="Sections" className="flex lg:flex-col gap-1 lg:gap-0.5">
      {NAV.map(({ to, label, Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `press group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium
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
        <header className="flex items-center justify-between gap-6 py-4 border-b border-[var(--color-line)]">
          <Link to="/platform" className="flex items-center gap-2.5 group">
            <span
              className="grid h-8 w-8 place-items-center rounded-lg text-white"
              style={{ background: 'var(--color-brand)' }}
              aria-hidden="true"
            >
              <Cube size={17} weight="fill" />
            </span>
            <span className="leading-tight">
              <span className="block text-[14.5px] font-bold text-[var(--color-text)]">
                Material Intelligence
              </span>
              <span className="block text-[11.5px] text-[var(--color-text-3)]">
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
          <aside className="lg:sticky lg:top-6 lg:self-start">
            <Rail />
          </aside>

          <main id="content" className="min-w-0 pb-16">
            <AnimatePresence mode="wait">
              <motion.div
                key={loc.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
              >
                <Routes location={loc}>
                  <Route path="/platform" element={<Home />} />
                  <Route path="/platform/analyse" element={<Analyse />} />
                  <Route path="/platform/material/:nmc" element={<Canonical />} />
                  <Route path="/platform/explorer" element={<Explorer />} />
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
