import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  House, MagnifyingGlass, Cube, ArrowLeft, Stack, Graph, ClipboardText, Seal,
  SignOut, SignIn as SignInIcon,
} from '@phosphor-icons/react'
import './tokens.css'
import { ThemeToggle } from './components/ThemeToggle'

import { Home } from './screens/Home'
import { Analyse } from './screens/Analyse'
import { Canonical } from './screens/Canonical'
import { Explorer } from './screens/Explorer'
import { Visualize } from './screens/Visualize'
import { NotFound } from './screens/NotFound'
import { SignIn } from './screens/SignIn'
import { Review } from './screens/Review'
import { Ledger } from './screens/Ledger'
import { Account } from './screens/Account'
import { SessionProvider, useSession } from './Session'
import { RequireAuth } from './RequireAuth'

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
  { to: '/platform',               label: 'Overview',      Icon: House,           end: true,  needsReview: false },
  { to: '/platform/analyse',       label: 'Analyse',       Icon: MagnifyingGlass, end: false, needsReview: false },
  { to: '/platform/explorer',      label: 'Explorer',      Icon: Stack,           end: false, needsReview: false },
  { to: '/platform/visualization', label: 'Relationships', Icon: Graph,           end: false, needsReview: false },
  // Hidden rather than disabled when signed out. A rail full of things you
  // cannot use is worse than a shorter one, and the server refuses regardless —
  // the nav is a convenience, never the enforcement.
  { to: '/platform/review',        label: 'Review',        Icon: ClipboardText,   end: false, needsReview: true },
  { to: '/platform/ledger',        label: 'Ledger',        Icon: Seal,            end: false, needsReview: true },
]

function Rail({ canReview }: { canReview: boolean }) {
  const items = canReview ? NAV : NAV.filter((n) => !n.needsReview)
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
      {items.map(({ to, label, Icon, end }) => (
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

/** Alias, so the route table below reads as a table rather than as JSX. */
const G = RequireAuth

function Chrome() {
  const loc = useLocation()
  const { user, signOut } = useSession()
  const canReview = !!user
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

          <div className="flex items-center gap-3 sm:gap-4">
            {user ? (
              <div className="flex items-center gap-2.5">
                {/* The chip was inert, which wasted the one piece of chrome a
                    person actually looks at to answer "who am I signed in as,
                    and what may I do?". It is now the way to the answer. */}
                <Link
                  to="/platform/account"
                  className="press flex items-center gap-2.5 rounded-[var(--radius-control)]
                             px-2 py-1 -mx-2 hover:bg-[var(--color-surface-3)]"
                  title="Your account and authority"
                >
                  <span className="hidden sm:block text-right leading-tight">
                    <span className="block text-[12.5px] font-semibold text-[var(--color-text)]">
                      {user.name}
                    </span>
                    <span className="block text-[11px] text-[var(--color-text-3)]">
                      {user.role} · {user.org_id}
                    </span>
                  </span>
                  <span
                    className="grid h-7 w-7 shrink-0 place-items-center rounded-full text-[11px] font-bold"
                    style={{ background: 'var(--color-brand-soft)', color: 'var(--color-brand)' }}
                    aria-hidden="true"
                  >
                    {user.name.split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase()}
                  </span>
                </Link>
                <button
                  onClick={() => signOut()}
                  title="Sign out"
                  aria-label="Sign out"
                  className="press grid h-8 w-8 place-items-center rounded-[var(--radius-control)]
                             text-[var(--color-text-3)] hover:bg-[var(--color-surface-3)]
                             hover:text-[var(--color-text)] cursor-pointer"
                >
                  <SignOut size={15} weight="bold" aria-hidden="true" />
                </button>
              </div>
            ) : loc.pathname !== '/platform/signin' ? (
              <Link to="/platform/signin"
                    className="press link inline-flex items-center gap-1.5 text-[13px] font-medium">
                <SignInIcon size={13} weight="bold" aria-hidden="true" />
                Sign in
              </Link>
            ) : null}
            <ThemeToggle />
            <a href="/" className="press link text-[13px] font-medium inline-flex items-center gap-1.5">
              <ArrowLeft size={13} weight="bold" aria-hidden="true" />
              <span className="hidden sm:inline">Back to the story</span>
            </a>
          </div>
        </header>

        {/* Signed out there is exactly one reachable route, so the rail would be
            a column of links that all bounce back to this screen. It collapses
            to a single column instead, which also gives the sign-in screen the
            full width its two panels want. */}
        <div className={`grid gap-6 lg:gap-8 py-6 min-w-0 ${
          user ? 'lg:grid-cols-[190px_minmax(0,1fr)]' : ''}`}>
          {/* min-w-0: a grid child defaults to min-width:auto, so without this the
              aside sizes to its content and the rail's overflow-x-auto has
              nothing to clip against — the page scrolls sideways instead. */}
          {user && (
            <aside className="min-w-0 lg:sticky lg:top-6 lg:self-start">
              <Rail canReview={canReview} />
            </aside>
          )}

          <main id="content" className="min-w-0 pb-16">
            {/* No AnimatePresence here, deliberately. `mode="wait"` holds the
                incoming route until the outgoing one finishes exiting, which
                costs 220ms of dead screen on every single nav click — and if
                the tab is backgrounded mid-navigation, rAF is paused, the exit
                never completes, and the URL changes while the screen does not.
                A keyed motion.div still replays the enter animation on every
                route change; the outgoing screen simply leaves at once. The
                deliberate `mode="wait"` lives in Analyse, where the pause is
                the point. */}
            <motion.div
              key={loc.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
            >
              <Routes location={loc}>
                {/* The only ungated route. Everything else is wrapped, and the
                    server refuses anyway — see RequireAuth. */}
                <Route path="/platform/signin" element={<SignIn />} />

                <Route path="/platform" element={<G><Home /></G>} />
                <Route path="/platform/analyse" element={<G><Analyse /></G>} />
                <Route path="/platform/material/:nmc" element={<G><Canonical /></G>} />
                <Route path="/platform/explorer" element={<G><Explorer /></G>} />
                <Route path="/platform/visualization" element={<G><Visualize /></G>} />
                <Route path="/platform/review" element={<G><Review /></G>} />
                <Route path="/platform/ledger" element={<G><Ledger /></G>} />
                <Route path="/platform/account" element={<G><Account /></G>} />

                {/* Gated too. An unknown path should not be a way to learn
                    whether this deployment exists without signing in. */}
                <Route path="*" element={<G><NotFound /></G>} />
              </Routes>
            </motion.div>
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
    // Follows the token so overscroll and the area behind the layout match the
    // active theme, instead of staying the light ground forever.
    document.body.style.background = 'var(--color-bg)'
    return () => { document.body.style.background = prev }
  }, [])

  return (
    <BrowserRouter>
      <SessionProvider>
        <Chrome />
      </SessionProvider>
    </BrowserRouter>
  )
}
