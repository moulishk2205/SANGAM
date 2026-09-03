import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

/**
 * Dev server config.
 *
 * THE PROXY IS THE WHOLE POINT
 *
 * The browser must only ever see ONE origin. Everything under /api is proxied
 * from this dev server to the engine on :8001, so as far as the browser is
 * concerned the API is part of this site.
 *
 * That single decision removes three separate failure modes rather than
 * patching them one at a time:
 *
 *   - CORS stops applying. There is no cross-origin request left to preflight,
 *     so no allowlist has to be kept in sync with anything.
 *   - The session cookie becomes first-party. `SameSite=Lax` is then correct
 *     and sufficient; nothing has to be relaxed to `None` to make a demo work.
 *   - Only ONE port needs forwarding. Port 8001 does not have to be exposed at
 *     all, and no tunnel URL appears anywhere in the code or the environment.
 *
 * That last point is what actually broke this setup. A dev-tunnel ID is
 * ephemeral: the URL hardcoded into web/.env.local and into the backend CORS
 * allowlist had already stopped existing by the time it was debugged, and both
 * were returning the tunnel service's 404. Any fix that writes the tunnel ID
 * into a file is a fix with an expiry date. This one has none, because the
 * frontend only ever calls a relative path.
 *
 * VITE_API_BASE still overrides it (see web/src/app/api.ts) for the case where
 * the API genuinely is on another origin — a deployed backend, say. It is an
 * escape hatch, not the default path.
 */

// The engine. Override when it is not on this machine or not on 8001.
const ENGINE = process.env.VITE_ENGINE_ORIGIN || 'http://127.0.0.1:8001'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // A tunnel reaches this server with a Host header Vite has never seen, and
    // Vite rejects unknown hosts by default. Allowing the dev-tunnel and
    // Codespaces suffixes keeps the DNS-rebinding protection in place for every
    // other host while letting a forwarded port through.
    allowedHosts: ['.devtunnels.ms', '.githubpreview.dev', '.app.github.dev', 'localhost'],
    proxy: {
      '/api': {
        target: ENGINE,
        changeOrigin: false,   // keep the browser's Host so cookie scope is unambiguous
        // Forward the original protocol so the engine can tell whether the
        // browser is on https (a tunnel) or http (localhost) and set the
        // cookie's Secure flag accordingly.
        xfwd: true,
      },
    },
  },
  build: { target: 'es2022' },
})
