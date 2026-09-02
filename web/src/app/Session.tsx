import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { auth, SESSION_LOST, type CurrentUser, type Role } from './api'

/* ══════════════════════════════════════════════════════════════════════════
   Who is signed in, available everywhere.

   The platform is readable signed out — the catalogue, the analyser and the
   relationship map are all public reads, and gating them behind a login would
   make the demo worse without making anything safer. What signing in changes is
   what you may *do*: the review queue, and every write.

   `loading` is a distinct third state, not `user === null`. Treating "still
   asking" as "signed out" flashes the login screen at someone who is in fact
   authenticated, every single reload.
   ══════════════════════════════════════════════════════════════════════════ */

type Ctx = {
  user: CurrentUser | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  /** Whether this user may act at all. Approval additionally needs scope. */
  can: (action: 'review' | 'steward' | 'admin') => boolean
}

const SessionContext = createContext<Ctx | null>(null)

const RANK: Record<Role, number> = { REQUESTER: 0, REVIEWER: 1, STEWARD: 2, ADMIN: 3 }

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // The cookie is httponly, so the only way to know who we are is to ask.
    auth.me()
      .then((r) => setUser(r.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  // A session can end while the tab is open — expiry, revocation, or the engine
  // restarted against a fresh database. api.ts raises this on any 401, and
  // clearing the user here is what makes the route gate fire instead of leaving
  // a signed-in-looking shell around screens that can no longer load.
  useEffect(() => {
    const onLost = () => setUser(null)
    window.addEventListener(SESSION_LOST, onLost)
    return () => window.removeEventListener(SESSION_LOST, onLost)
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const r = await auth.login(email, password)
    setUser(r.user)
  }, [])

  const signOut = useCallback(async () => {
    try { await auth.logout() } finally { setUser(null) }
  }, [])

  const can = useCallback((action: 'review' | 'steward' | 'admin') => {
    if (!user) return false
    const need = action === 'review' ? 1 : action === 'steward' ? 2 : 3
    return RANK[user.role] >= need
  }, [user])

  const value = useMemo(() => ({ user, loading, signIn, signOut, can }),
    [user, loading, signIn, signOut, can])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): Ctx {
  const c = useContext(SessionContext)
  if (!c) throw new Error('useSession must be used inside SessionProvider')
  return c
}
