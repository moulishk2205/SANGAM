# Running SANGAM

**SANGAM — Material Intelligence Platform**
SIH26099 · Ministry of Petroleum & Natural Gas / Chennai Petroleum Corporation Limited

This file gets the whole thing running on a machine that has never seen it: the
landing page, the platform, and the matching engine behind both.

There are **two processes**. Nothing works with only one of them:

| | What it is | Port |
| --- | --- | --- |
| **Engine** | FastAPI + the matching pipeline + the embedding model | `8001` |
| **Web** | Vite dev server — landing page *and* platform | `5173` |

The web app calls the engine at `http://localhost:8001` during development
(`web/src/app/api.ts`). **Port 8001 is not a suggestion** — start the engine on
any other port and every screen will show *"Cannot reach the SANGAM engine."*

---

## 1. Prerequisites

| Tool | Version used here | Check |
| --- | --- | --- |
| Python | 3.12 | `python3 --version` |
| Node.js | 20 or newer | `node --version` |
| npm | ships with Node | `npm --version` |
| Git | any | `git --version` |

Python 3.11 or 3.13 will work. Below 3.11 will not — the code uses `X | Y`
type syntax throughout.

---

## 2. One-time setup

Run these once, from the repository root. In VS Code: **Terminal → New Terminal**
(`` Ctrl+` ``), which already opens at the repository root.

### 2.1 Python environment

**macOS / Linux**

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

This installs PyTorch, so expect a few hundred megabytes and a few minutes.

### 2.2 Frontend packages

```bash
cd web && npm install
```

### 2.3 Tell VS Code which Python to use

`Cmd/Ctrl+Shift+P` → **Python: Select Interpreter** → choose the one inside
`.venv`. It should read something like `Python 3.12.14 ('.venv': venv)`.

`.vscode/settings.json` already points at `.venv`, so VS Code usually picks it
up on its own. If imports show red squiggles, this is why — set it manually.

### 2.4 Install the recommended extensions

VS Code will offer them when you open the folder (they are listed in
`.vscode/extensions.json`). Or `Cmd/Ctrl+Shift+P` → **Extensions: Show
Recommended Extensions**.

Python · Pylance · Ruff · Tailwind CSS IntelliSense · ESLint · Prettier

---

## 3. The ML model — read this before your first run

The dense retrieval channel uses **`bge-small-en-v1.5`** (BAAI, ~130 MB). It is
a **pre-trained, off-the-shelf model, used unmodified. Nothing in this project
was trained or fine-tuned.**

`models/` is in `.gitignore`, so a fresh clone does **not** have it. On first
start the engine looks for `models/bge-small-en-v1.5` and, not finding it,
downloads it from Hugging Face. That needs internet and takes a minute.

**Two things to know:**

**The path is relative.** `src/nmc/match/retrieve.py` looks for
`models/bge-small-en-v1.5` relative to the *current working directory*. Start
the engine from anywhere but the repository root and it will quietly re-download
the model instead of using your copy. Always start it from the repo root.

**Pre-download it before a demo.** Venue wifi fails at the worst moment. Do this
once, while you still have a good connection:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5').save('models/bge-small-en-v1.5')"
```

After that the engine starts fully offline. In VS Code this is also available as
**Run Task → SANGAM: pre-download the embedding model**.

If the model cannot be loaded at all, the engine still starts — it degrades to
lexical-only retrieval and prints `dense channel: off`. The demo will work but
the accuracy numbers will not match the ones we report.

---

## 3b. The database

State lives in a real database now, not in memory. `DATABASE_URL` selects the
backend; the default is a SQLite file, `sangam.db`, beside the repository.

SQLite is deliberate. A demo that cannot start without a Postgres server is a
demo that fails at the venue, and nothing in the schema is SQLite-specific —
point `DATABASE_URL` at Postgres and the same migrations apply.

**You do not need to do anything.** On first start the engine creates the schema
and seeds the demonstration corpus (~1 second), then reads from storage on every
start after that. The file is gitignored, so a fresh clone builds its own.

To run the migration explicitly, or to inspect where the schema stands:

```bash
python -m alembic upgrade head
```

To start over from an empty database, delete the file and restart:

```bash
rm -f sangam.db && python -m alembic upgrade head
```

### Demo accounts

Seeded with hashed passwords. The password for all of them is `sangam-demo`,
and these are demonstration credentials — never reuse them anywhere.

| Email | Role | Organisation | Scope |
| --- | --- | --- | --- |
| `reviewer.a@sangam.gov.in` | Reviewer | CPSE-A | fastener, pipe, flange · certified PRESSURE |
| `reviewer.b@sangam.gov.in` | Reviewer | CPSE-B | fastener |
| `steward@sangam.gov.in` | Steward | CPSE-A | every family, CPSE-A only |
| `requester.a@sangam.gov.in` | Requester | CPSE-A | may propose, never approve |
| `admin@sangam.gov.in` | Admin | CPSE-A | users and organisations |

Authority is a pair, not a role: **organisation × commodity family**. A CPSE-B
reviewer cannot approve a CPSE-A mapping, and no role — administrator included —
is exempt from that. It is the guarantee the whole product rests on.

Sign in from `/platform/signin`. The five accounts are on that page as one-click
cards, so a reviewer never has to come back here to find a password.

### The review queue is seeded on purpose

Seeding holds back 22 of the 1,800 mappings as `PROPOSED` rather than
`APPROVED`, so the review queue has work in it on a fresh database. An empty
queue would be the honest result of a fully-adjudicated corpus and a useless
demonstration — the reviewer would sign in, read "nothing waiting for you", and
never reach the part of the product that matters.

The 22 are chosen, not sampled, so that each account teaches a different rule:

| Sign in as | What you see | What happens |
| --- | --- | --- |
| S. Nair | 12 items, CPSE-A only | The 3 CPSE-A valves never appear — `valve` is not one of her families |
| S. Nair → a fastener | GENERAL class | Approves, writes a certificate, chain length moves |
| S. Nair → a flange | PRESSURE class | Approves — she holds PRESSURE — but only with a written justification |
| S. Nair → a pipe | FIRED class | Refused: she holds PRESSURE, not FIRED |
| M. Banerjee | 5 items, CPSE-B only | Nair's 12 are invisible, not greyed out |
| M. Banerjee → a CPSE-A id | — | Refused on the organisation rule |
| K. Rao (requester) | — | Refused on role, before any scope is considered |

Every refusal message is shown verbatim next to the item rather than as a toast,
because the reason is the interesting output. Approvals write a real row: restart
the engine and the decision, its certificate and its hash chain are all still
there. To get the queue back, delete `sangam.db` and restart the engine.

---

## 4. Starting it

### The VS Code way (one command)

`Cmd/Ctrl+Shift+P` → **Tasks: Run Task** → **SANGAM: start everything**

That launches both servers in their own terminal panes. Since both are
long-running servers, neither ever prints "done" — that is correct, not a hang.

`Cmd/Ctrl+Shift+B` runs the same task, since it is the default build task.

### The manual way (two terminals)

You need **two** terminals. In VS Code, click the split icon in the terminal
panel, or `Cmd/Ctrl+Shift+5`.

**Terminal 1 — the engine.** From the repository root:

```bash
python -m uvicorn src.nmc.api:app --port 8001 --reload
```

Wait for both of these lines before touching the browser:

```
[api] indexed 1800 records into 600 canonical materials in 4,202 ms (dense channel: on)
INFO:     Application startup complete.
```

The index is built at startup, which takes roughly 4 seconds. Until you see
`Application startup complete`, the API returns `503 engine still indexing`.

`dense channel: on` confirms the embedding model loaded. If it says `off`, see
§3.

**Terminal 2 — the web app:**

```bash
cd web && npm run dev
```

Vite prints the URL it chose. It is normally `http://localhost:5173`; if that
port is busy it will pick another and say so. Ports 5173, 5174, 4173 and 4174
are all pre-approved in the engine's CORS settings — anything else will be
blocked by the browser.

---

## 5. Where to go

| URL | What it is |
| --- | --- |
| `http://localhost:5173/` | **Landing page** — the scroll narrative. Start here. |
| `http://localhost:5173/platform` | **Home** — the console. Type a material, or pick an example. |
| `http://localhost:5173/platform/analyse` | **Analyse** — the full pipeline, stage by stage, with evidence. |
| `http://localhost:5173/platform/explorer` | **Explorer** — the standardized catalogue. |
| `http://localhost:5173/platform/visualization` | **Visualization** — the relationship map. |
| `http://localhost:8001/docs` | Interactive API docs (FastAPI's built-in Swagger UI). |

The landing page's **Open SANGAM** button leads into the platform.

---

## 6. Check it actually works

Paste this into a third terminal. Every line should say `200`:

```bash
for p in /api/health /api/stats /api/samples; do printf "%-16s " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "localhost:8001$p"; done
```

Then prove the engine really runs — this is the demo's central claim, that a
disagreement on a critical attribute is a veto and not a penalty:

```bash
curl -s -X POST localhost:8001/api/match -H 'Content-Type: application/json' -d '{"description":"SS HEX BOLT M10 X 50","top_k":5}' | python -m json.tool | head -40
```

The first three come back `MATCH` — the same bolt written three ways. The rest
come back `DISTINCT` with `confidence` **exactly `0.0`** and a `veto_reason`
naming the attribute that stopped them:

```
MATCH     1.0     SS HEX BOLT M10X50
MATCH     0.9988  BOLT HEX SS M10*50
MATCH     0.9941  STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM
DISTINCT  0.0     SS HEX BOLT M10X25    Length: 50 mm vs 25 mm — differs by 25 mm
DISTINCT  0.0     MS HEX BOLT M10 X 50  Material: STAINLESS_STEEL vs MILD_STEEL
```

Zero, not merely low. That is the whole architecture in one column: the veto is
a multiplier of zero, so no amount of text similarity can recover a pair whose
specification disagrees. The corpus is generated from a fixed seed, so you will
see these same rows.

### In the browser

1. Open `/platform`, click the **Ball valve** example. It fills the field and
   does **not** run — press **Analyse material** yourself.
2. The Analyse screen walks the seven pipeline stages and shows the extracted
   attributes, candidates and evidence.
3. Open **Visualization**. Three teal dots sit at the top; the rejected
   candidates hang below as hollow rings with lines falling into the gate.

---

## 7. Useful commands

| What | Command |
| --- | --- |
| Engine tests | `python -m pytest tests/ -q` |
| Full evaluation (recall, F1, veto, latency) | `python scripts/evaluate.py` |
| Frontend type-check | `cd web && npx tsc --noEmit` |
| Frontend lint | `cd web && npm run lint` |
| Production build | `cd web && npm run build` |
| Preview the production build | `cd web && npm run preview` |

The evaluation script takes about a minute and prints the numbers we quote:
recall@1 96.33%, F1 99.06%, p95 latency 14.5 ms, and the veto counts.

In VS Code, tests are also available under the beaker icon in the sidebar, and
`Run Task → SANGAM: evaluate the engine`.

---

## 8. When it does not work

**Every screen says "Cannot reach the SANGAM engine."**
The engine is not running, or not on 8001. Check Terminal 1 for
`Application startup complete`. Confirm with `curl localhost:8001/api/health`.

**`ModuleNotFoundError: No module named 'src'`**
You are not in the repository root. `cd` there and try again — `conftest.py` is
what makes `src` importable, and it only applies from the root.

**`ModuleNotFoundError: No module named 'fastapi'` (or torch, numpy…)**
The venv is not active, or dependencies were never installed. Re-run §2.1. In
VS Code, check the interpreter shown in the bottom-right status bar.

**`[Errno 48] Address already in use` / `EADDRINUSE`**
Something is already on that port — often an older copy of this app.

```bash
lsof -ti:8001 | xargs kill -9
```

On Windows: `netstat -ano | findstr :8001`, then `taskkill /PID <pid> /F`.

**The engine prints `dense channel: off`**
`sentence-transformers` or `torch` failed to import, or the model could not be
fetched. The app still runs on lexical retrieval alone, but the reported
accuracy assumes the dense channel. See §3.

**Browser console shows a CORS error**
Vite is on a port the engine does not allow. Use 5173 or 5174, or add yours to
`allow_origins` in `src/nmc/api.py`.

**First engine start hangs for a minute**
It is downloading the model. Watch the terminal for progress. See §3 to avoid
this on demo day.

**Breakpoints in the engine never hit**
Use **Run and Debug → SANGAM: debug the engine**, not `--reload`. The reloader
runs the app in a child process, so breakpoints set in the parent never bind.

---

## 9. What the demo data actually is

State this plainly if anyone asks; it is in the product UI too.

- The corpus is **1,800 synthetic records** collapsing to **600 canonical
  materials** across **4 invented organisations**. It is generated from
  specifications we define, so the labels are correct by construction.
- The organisation names and material codes are **invented**. They are not the
  records of ONGC, IOCL, NTPC, CPCL or any real enterprise.
- **No model was trained.** `bge-small-en-v1.5` is used off the shelf,
  unmodified. There is no training code in this repository.
- FLIS (the public US Defense Logistics Agency catalogue) informed the
  *attribute structure* and item-name vocabulary. Its **values are not used**,
  and FLIS is not CPSE data.
- `confidence` is an **uncalibrated ranking score, not a probability.** The API
  carries `calibrated: false` on every response so nothing downstream can
  quietly relabel it.

Full provenance: `docs/DATA_PROVENANCE.md`. Engine design: `docs/SPRINT1-ENGINE.md`.

---

## 10. Stopping

`Ctrl+C` in each terminal. Or, in VS Code, the bin icon on each terminal pane.
Nothing is persisted between runs — the index is rebuilt at every startup — so
there is no cleanup to do.
