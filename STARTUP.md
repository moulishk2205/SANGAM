# STARTUP — how to run SANGAM

Everything you need to start the landing page, the platform, the ML engine and
the database, from a fresh clone, in VS Code.

Written to be self-contained: if you hand this file to another person or another
AI with no other context, it should be enough to get the whole system running
and to understand how the pieces fit.

> For *why* the system is built this way — the design constraints, the
> governance model, the data provenance — read `MEMORY.md`.

---

## 0. TL;DR

Two servers. Both must be running.

```bash
# terminal 1 — the engine (Python, port 8001)
cd /path/to/sih26099
source .venv/bin/activate
python -m uvicorn src.nmc.api:app --port 8001 --reload
```

```bash
# terminal 2 — the web app (Node, port 5173)
cd /path/to/sih26099/web
npm run dev
```

Then open **http://localhost:5173** — landing page.
The platform is at **http://localhost:5173/platform**, and it will send you to
sign-in. Click any demo account card. Password for all of them: `sangam-demo`.

---

## 1. What the system is made of

There are **three** runnable things and **one** database. There is no separate
"ML service" — the model lives inside the Python engine process.

```
┌──────────────────────────────┐        ┌────────────────────────────────┐
│  BROWSER  localhost:5173     │        │  ENGINE  localhost:8001        │
│                              │        │                                │
│  Vite dev server serves      │  HTTP  │  FastAPI (uvicorn)             │
│  ONE React bundle:           │ ─────► │    ├── matching engine         │
│    /          landing page   │ cookie │    │     └── bge-small-en-v1.5 │
│    /platform  the app        │ ◄───── │    │         (in-process)      │
│                              │        │    ├── auth + sessions         │
└──────────────────────────────┘        │    └── SQLAlchemy              │
                                        └───────────────┬────────────────┘
                                                        │
                                                ┌───────▼────────┐
                                                │  sangam.db     │
                                                │  SQLite, WAL   │
                                                └────────────────┘
```

| Piece | Language | Port | Started by |
|---|---|---|---|
| Web app (landing + platform) | TypeScript / React 19 | 5173 | `npm run dev` |
| Engine (API + ML + DB access) | Python 3.12 | 8001 | `uvicorn` |
| Embedding model | PyTorch, loaded in-process | — | automatic on engine boot |
| Database | SQLite file | — | created automatically |

**The landing page and the platform are the same bundle.** `web/src/App.tsx`
checks `window.location.pathname`: anything starting with `/platform` renders
the application, everything else renders the scroll landing page. There is no
second build and no second server.

**The landing page makes zero API calls.** It works with the engine switched
off. The platform does not — every screen needs the engine.

---

## 2. File structure

```
sih26099/
│
├── src/nmc/                    ◄── THE ENGINE. All Python lives here.
│   ├── api.py                      FastAPI app — 29 endpoints. Entry point.
│   ├── authz.py                    roles, sessions, password hashing
│   ├── service.py                  the write path + decision certificates
│   ├── relate.py                   relationship-map builder
│   ├── types.py                    core dataclasses
│   ├── normalise/text.py           abbreviation gazetteer
│   ├── extract/                    attribute extraction (regex + templates)
│   ├── match/                      retrieval, comparison, scoring
│   │   └── retrieve.py             ◄── loads the embedding model
│   ├── db/                         SQLAlchemy models, session, seeding
│   └── demo/corpus.py              synthetic corpus generator
│
├── web/                        ◄── THE FRONTEND. All TypeScript lives here.
│   ├── package.json                npm scripts
│   ├── vite.config.ts              dev server on port 5173
│   ├── index.html                  the single HTML entry
│   └── src/
│       ├── main.tsx                React root
│       ├── App.tsx                 landing-vs-platform switch
│       ├── index.css               design tokens (light + dark)
│       ├── sections/               landing page sections
│       ├── components/             landing page primitives
│       ├── lib/                    GSAP helpers, landing copy
│       └── app/                    THE PLATFORM
│           ├── Platform.tsx        shell + route table
│           ├── RequireAuth.tsx     the auth gate
│           ├── Session.tsx         who is signed in
│           ├── api.ts              typed HTTP client
│           ├── components/         shared UI
│           └── screens/            one file per screen
│
├── models/bge-small-en-v1.5/   ◄── THE MODEL. 128 MB, downloaded, not trained.
├── scripts/evaluate.py             the measurement harness
├── tests/                          24 pytest tests
├── migrations/                     Alembic
├── .vscode/                        tasks, debug configs, settings
├── requirements.txt                Python dependencies
├── sangam.db                       SQLite database (gitignored, auto-created)
├── MEMORY.md                       full project context and design rationale
└── STARTUP.md                      this file
```

---

## 3. First-time setup

Do this once. Skip to §4 if you have already done it.

### 3.1 Prerequisites

| Need | Version used here | Check |
|---|---|---|
| Python | 3.12.14 | `python3 --version` |
| Node.js | 25.9.0 (any ≥ 20 works) | `node -v` |
| npm | 11.12.1 | `npm -v` |
| git | any | `git --version` |

### 3.2 Python environment

From the repository root:

```bash
python3.12 -m venv .venv
```

```bash
source .venv/bin/activate
```

On Windows PowerShell the activate line is `.\.venv\Scripts\Activate.ps1`.

```bash
pip install --upgrade pip && pip install -r requirements.txt
```

This pulls **torch** and **sentence-transformers**, which are large — expect a
few hundred MB and several minutes on a first run.

### 3.3 Node dependencies

```bash
cd web && npm install
```

### 3.4 The embedding model

The engine looks for `models/bge-small-en-v1.5` **relative to the working
directory**. If it is missing, `sentence-transformers` downloads it from Hugging
Face on first boot — which needs the network and adds ~30 s.

To pre-download it (do this before an offline demo), from the repository root:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5').save('models/bge-small-en-v1.5')"
```

> **This is the single most common startup mistake:** starting uvicorn from a
> directory other than the repository root. The relative path then misses, and
> the model is silently re-downloaded every boot. Always start the engine from
> the repo root.

### 3.5 The database

**Nothing to do.** On first boot the engine creates `sangam.db`, builds the
schema, and seeds it: 4 organisations, 5 users, 600 canonical materials, 1,800
source records, 1,800 mappings (22 of them left `PROPOSED` so the review queue
has work in it).

Seeding is idempotent — it no-ops on every subsequent boot.

---

## 4. Starting it in VS Code

### 4.1 The one-command way (recommended)

`Cmd/Ctrl + Shift + P` → **Tasks: Run Task** → **SANGAM: start everything**

Or just press `Cmd/Ctrl + Shift + B` — it is the default build task.

That opens both servers in their own dedicated terminal panes. **Neither ever
prints "done"** — they are long-running servers. That is correct, not a hang.

Other tasks in the same menu:

| Task | What it does |
|---|---|
| `SANGAM: engine (API on :8001)` | just the backend |
| `SANGAM: web (Vite dev server)` | just the frontend |
| `SANGAM: run engine tests` | `pytest tests/ -q` |
| `SANGAM: evaluate the engine` | prints the real accuracy numbers |
| `SANGAM: pre-download the embedding model` | for offline demos |

The tasks use `${command:python.interpreterPath}`, so VS Code uses whichever
interpreter you selected — see §4.3.

### 4.2 The manual way (two terminals)

Split the VS Code terminal with the split icon, or `` Cmd/Ctrl + Shift + 5 ``.

**Terminal 1 — the engine.** From the repository root:

```bash
source .venv/bin/activate && python -m uvicorn src.nmc.api:app --port 8001 --reload
```

Wait for this line before using the platform:

```
[api] storage sqlite · indexed 1,800 records in 4,750 ms (dense channel: on) · seeded 1,800 records
INFO:     Uvicorn running on http://127.0.0.1:8001
```

The `· seeded 1,800 records` suffix appears only on a boot that actually seeded
— a first run, or the first run after you deleted the database. On every later
boot the line ends at the closing bracket.

`dense channel: on` means the embedding model loaded. `off` means it did not,
and the engine has degraded to lexical-only retrieval — accuracy drops but it
still runs. Boot takes ~25 s: most of it is building the index.

**Terminal 2 — the web app:**

```bash
cd web && npm run dev
```

```
VITE ready in 300 ms
➜  Local: http://localhost:5173/
```

### 4.3 Selecting the Python interpreter

`Cmd/Ctrl + Shift + P` → **Python: Select Interpreter** → choose the one inside
`.venv`. Without this the tasks and the debugger use the system Python, which
does not have the dependencies.

### 4.4 Debugging

`.vscode/launch.json` has ready configurations — press `F5`:

- **SANGAM: debug the engine** — uvicorn under the debugger, breakpoints work
- **SANGAM: debug the current Python file**

### 4.5 Recommended extensions

VS Code will offer these from `.vscode/extensions.json`: Python, Pylance, Ruff,
Tailwind CSS IntelliSense, oxlint.

---

## 5. Signing in

Open **http://localhost:5173**, scroll to the end, click **Open SANGAM**. Or go
straight to **http://localhost:5173/platform**.

Either way you land on the sign-in screen. **There is no anonymous access** —
every route and every API endpoint except `/api/health` and the auth endpoints
requires a session.

Five demo accounts are on the screen as one-click cards. Password for all:
**`sangam-demo`**

| Email | Role | Org | What it demonstrates |
|---|---|---|---|
| `reviewer.a@sangam.gov.in` | Reviewer | CPSE-A | Approves fastener/pipe/flange. Certified PRESSURE, so the FIRED pipes in her queue are refused. |
| `reviewer.b@sangam.gov.in` | Reviewer | CPSE-B | Cannot touch CPSE-A at all. Her queue contains different items. |
| `steward@sangam.gov.in` | Steward | CPSE-A | Above commodity families — still bound by organisation and safety class. |
| `requester.a@sangam.gov.in` | Requester | CPSE-A | Every approval attempt is refused on role. |
| `admin@sangam.gov.in` | Admin | CPSE-A | Administers accounts, and is still not exempt from the org rule. |

`/platform/account` shows the signed-in user's full authority and, more usefully,
exactly what the server will refuse them.

---

## 6. A five-minute demo path

1. **Analyse** — paste `MS HEX BOLT M10 X 75`. Watch it normalise the text,
   extract the attributes, retrieve candidates, then score them.
2. **This one query is the whole argument.** It returns eight candidates: three
   genuine matches, and five scored **exactly 0.0000** despite text similarity
   above 0.95 — each vetoed on a single critical attribute:

   | Candidate | Text similarity | Score | Vetoed because |
   |---|---|---|---|
   | `BOLT HEX MS M10*75` | 0.9904 | **0.9986** | — genuine match |
   | `MS HEX BOLT M12 X 75` | 0.9898 | **0.0000** | thread Ø 10 mm vs 12 mm |
   | `MS HEX BOLT M10 X 50` | 0.9711 | **0.0000** | length 75 mm vs 50 mm |
   | `CS HEX BOLT M10X75` | 0.9631 | **0.0000** | MILD_STEEL vs CARBON_STEEL |
   | `SS HEX BOLT M10X75` | 0.9585 | **0.0000** | MILD_STEEL vs STAINLESS_STEEL |

   A similarity-threshold matcher would have merged all five. Every one is a
   different physical part. The veto is a gate (`0` or `1`), not a penalty —
   which is why the score is zero and not merely reduced. Open the evidence
   table on any row to see the per-attribute AGREE/DISAGREE/UNKNOWN breakdown.
3. **Explorer** — browse the 600 canonical identities.
4. **Relationships** — the relationship map for one material.
5. **Review** (as S. Nair) — approve a fastener. Note the certificate count move.
6. Try approving a **FIRED** pipe in the same queue. Refused, with the reason.
7. **Ledger** — open the certificate you just wrote. Evidence frozen, versions
   recorded, hash chained to its predecessor.
8. Sign out, sign in as **M. Banerjee**, and see that CPSE-A's items are not
   merely greyed out — they are absent.

---

## 7. Verifying it works

```bash
python scripts/evaluate.py
```

Real measured numbers on the synthetic corpus — nothing estimated:

```
retrieval    recall@1 96.33%   recall@10 97.67%
decision     precision 99.44%   recall 98.69%   F1 99.06%
veto         2,392 candidates vetoed on a critical attribute,
             all 2,392 with text similarity >= 0.85
latency      p50 13.0 ms   p95 16.9 ms
```

```bash
python -m pytest tests/ -q
```

Expect `24 passed`.

---

## 8. The database

SQLite by default. The path and backend come from `DATABASE_URL`; unset, it is a
file beside the repository.

```bash
# inspect it
sqlite3 sangam.db ".tables"
sqlite3 sangam.db "select status, count(*) from mappings group by 1;"
```

**Reset to a clean seeded state** — do this if the review queue is empty because
you approved everything:

```bash
rm -f sangam.db sangam.db-wal sangam.db-shm
```

Then restart the engine; it reseeds automatically.

**Point at Postgres instead** (the schema is portable, same migrations):

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@localhost/sangam"
```

**Migrations** (Alembic; `create_all` on boot is a convenience for fresh
checkouts, `alembic` is the real path):

```bash
alembic upgrade head
```

---

## 9. Ports, and what to do when one is taken

| Port | Service |
|---|---|
| 5173 | Vite dev server |
| 8001 | FastAPI engine |

The engine's CORS allowlist is **exactly** `5173`, `5174`, `4173`, `4174`, and
it sends credentials — so the web app must be on one of those, or the session
cookie is rejected and every call fails as anonymous.

If Vite says the port is in use, do not let it pick another one silently. Find
and kill the process:

```bash
lsof -ti:5173 | xargs kill
```

```bash
lsof -ti:8001 | xargs kill
```

On Windows: `netstat -ano | findstr :5173` then `taskkill /PID <pid> /F`.

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Every screen says "Could not reach the engine" | engine not running | start terminal 1; check `curl localhost:8001/api/health` |
| Signed in, then everything 401s | web app on a port outside the CORS allowlist | run Vite on 5173 |
| `dense channel: off` in the boot line | `sentence-transformers`/`torch` missing, or model path missed | reinstall requirements; start uvicorn from the repo root |
| Boot re-downloads the model every time | uvicorn started from the wrong directory | `cd` to the repository root first |
| Review queue is empty | you approved all 22 seeded proposals | delete `sangam.db*` and restart |
| `ModuleNotFoundError: nmc` | venv not activated, or wrong cwd | `source .venv/bin/activate`, run from repo root |
| Landing page scroll feels broken | GSAP/Lenis need a real reload after a hot edit | hard-refresh the tab |
| Sign-in accepts nothing | database not seeded | check the boot log; delete `sangam.db*` and restart |

---

## 11. Building for production

```bash
cd web && npm run build
```

Output lands in `web/dist/`. `npm run preview` serves it on 4173, which is in
the CORS allowlist.

The engine in production drops `--reload`:

```bash
python -m uvicorn src.nmc.api:app --host 0.0.0.0 --port 8001
```

> Not deployment-ready as it stands: no CSRF tokens, no rate limiting, no HTTPS
> enforcement, and the demo credentials are published in the source. It is a
> hackathon prototype and `MEMORY.md` §12 lists what is missing.

---

## 12. Quick command reference

| Goal | Command |
|---|---|
| Start engine | `python -m uvicorn src.nmc.api:app --port 8001 --reload` |
| Start web app | `cd web && npm run dev` |
| Run tests | `python -m pytest tests/ -q` |
| Measure accuracy | `python scripts/evaluate.py` |
| Lexical-only comparison | `python scripts/evaluate.py --no-embeddings` |
| Typecheck the frontend | `cd web && npx tsc --noEmit` |
| Lint the frontend | `cd web && npm run lint` |
| Lint Python | `ruff check src/ tests/ scripts/` — see the note below |
| Production build | `cd web && npm run build` |
| Reset the database | `rm -f sangam.db sangam.db-wal sangam.db-shm` |
| Pre-download the model | see §3.4 |
| Free port 5173 / 8001 | `lsof -ti:5173 \| xargs kill` |

> **On `ruff`:** the project has no `pyproject.toml`, so ruff runs with its full
> default rule set and currently reports ~89 style nits (`EXE001` shebangs,
> `F541` f-strings without placeholders, line lengths). None are defects —
> Python style has never been gated here. The gates that *are* enforced and
> currently clean are `pytest` (24 passed), `tsc --noEmit`, and `npm run lint`
> (0 errors).
