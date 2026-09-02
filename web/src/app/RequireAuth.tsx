import { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useSession } from './Session'
import { ScreenSkeleton } from './components/Skeleton'

/* ══════════════════════════════════════════════════════════════════════════
   The gate.

   Every platform route sits behind this. The catalogue, the analyser and the
   relationship map used to be readable signed out; they are not any more. This
   is a system of record for another organisation's material master, and "you
   may look but not touch" is the wrong default for one.

   THREE STATES, NOT TWO

   `loading` is not `signed out`. Treating "still asking the server" as "no
   session" bounces an authenticated user to the login screen on every reload,
   for the fraction of a second it takes /api/auth/me to answer — and because
   the redirect is real navigation, they land on the login screen and stay
   there. So loading renders a skeleton and decides nothing.

   THE DESTINATION SURVIVES

   A gate that forgets where you were going is a gate that makes people
   navigate twice. The full path, including its query string, is carried
   through as `next` and restored after sign-in.

   THIS IS CONVENIENCE, NOT ENFORCEMENT

   The server refuses anyway — every endpoint but login, logout, me and health
   requires a session. If this component were deleted the data would still be
   safe; the screens would just fail unhelpfully instead of redirecting. Client
   routing is never the security boundary and nothing here should be read as
   though it were.
   ══════════════════════════════════════════════════════════════════════════ */

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useSession()
  const loc = useLocation()

  // The tab title is the only signal a backgrounded tab can give that the
  // session ended. It must be restored on the way back in, or every screen
  // after a sign-in keeps announcing "Sign in" to the tab strip and to screen
  // readers that read the document title on navigation.
  useEffect(() => {
    if (loading) return
    document.title = user ? 'SANGAM — Material Intelligence' : 'Sign in — SANGAM'
  }, [loading, user])

  if (loading) return <ScreenSkeleton />

  if (!user) {
    const next = loc.pathname + loc.search
    // replace: the blocked URL must not sit in history, or Back from the login
    // screen lands on it again and bounces straight back here.
    return <Navigate to={`/platform/signin?next=${encodeURIComponent(next)}`} replace />
  }

  return <>{children}</>
}
