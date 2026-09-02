# SANGAM — project memory

A single file that carries the whole project's context. If you are an assistant
opening this repository in a fresh session with no history, read this first and
you will know what exists, why it was built that way, and what is deliberately
absent.

Last updated: **2026-09-02**, at commit `d94f6b8`.

---

## 1. What this is

**SANGAM** — a material-code harmonization platform for **Smart India Hackathon
2026, problem statement SIH26099**, set by the **Ministry of Petroleum & Natural
Gas** with **Chennai Petroleum Corporation Limited**.

The problem: every Central Public Sector Enterprise writes the same physical
item differently. `MS HEX BOLT M10 X 50`, `BOLT HEXAGONAL MILD STEEL M10X50`,
and `HEX HD BOLT-MS-M10-50MM` are one bolt with three codes across three
organisations. Nobody can answer "do we already own this?", so the same item is
bought repeatedly under different codes.

The product resolves many source codes to one canonical identity (an `NMC-…`
number), keeps the evidence for every resolution, and makes a named person
accountable for each decision.

### The one design constraint that governs everything

> Semantic similarity **proposes** candidates. Structured attributes **decide**
> identity. A mismatch on a discriminating attribute is a hard veto, not a score
> penalty.

`M10x50` vs `M10x75` must be *structurally impossible* to call a duplicate.
Every architectural choice below follows from that sentence.

---

## 2. Repository layout

```
sih26099/
├── src/nmc/                  the engine and the API (Python)
│   ├── api.py                FastAPI app, ~29 endpoints, session auth
│   ├── authz.py              roles, sessions, PBKDF2, authority checks
│   ├── service.py            the write path: propose/approve/reject/merge/split
│   │                         + hash-chained decision certificates
│   ├── relate.py             relationship-map builder (PCA + rank fidelity)
│   ├── types.py              MaterialRecord, MatchExplanation, AttributeSpec
│   ├── normalise/text.py     gazetteer + abbreviation expansion  (gaz-v2)
│   ├── extract/
│   │   ├── grammar.py        regex attribute extraction           (rules R12)
│   │   └── templates.py      per-item attribute templates    (template-v2)
│   ├── match/
│   │   ├── retrieve.py       hybrid retrieval, TF-IDF + dense, fused by RRF
│   │   ├── compare.py        three-valued attribute comparison
│   │   └── engine.py         scoring, veto, decision bands
│   ├── db/
│   │   ├── models.py         11 SQLAlchemy tables
│   │   ├── session.py        engine, DATABASE_URL, SQLite pragmas
│   │   └── seed.py           idempotent seeding of the demo corpus
│   └── demo/corpus.py        the synthetic corpus generator
├── web/                      React 19 + Vite + Tailwind v4
│   └── src/
│       ├── App.tsx           picks landing vs platform by pathname
│       ├── sections/         the cinematic scroll landing page
│       │   ├── Cinematic.tsx   600vh scroll-scrubbed hero video
│       │   ├── Pipeline.tsx    7-step full-bleed wipe
│       │   ├── Product.tsx
│       │   └── Cta.tsx         "Open SANGAM" → /platform/signin
│       ├── app/              the platform application
│       │   ├── Platform.tsx    shell, rail, header, route table
│       │   ├── RequireAuth.tsx the auth gate on every route but sign-in
│       │   ├── Session.tsx     SessionProvider / useSession
│       │   ├── api.ts          typed client, credentials + 401 handling
│       │   └── screens/        Home Analyse Explorer Visualize Canonical
│       │                       SignIn Review Ledger Account NotFound
│       └── index.css         design tokens, light + dark
├── scripts/evaluate.py       the measurement harness — real numbers only
├── tests/                    24 tests
├── migrations/               Alembic
├── docs/                     provenance, sprint findings, research
├── models/bge-small-en-v1.5  the embedding model, downloaded not trained
└── sangam.db                 SQLite (gitignored)
```

---

## 3. How the engine actually works

Five stages, all deterministic except the embedding lookup.

1. **Normalise** (`normalise/text.py`) — uppercase, strip punctuation, expand a
   hand-built gazetteer of trade abbreviations: `SS`→`STAINLESS STEEL`,
   `SMLS`→`SEAMLESS`, `WN`→`WELD NECK`, `RF`→`RAISED FACE`. Also splits glued
   tokens (`150NB` → `150 NB`, `SCH40` → `SCH 40`), which regexes downstream
   cannot recover from if missed. Version `gaz-v2`.

2. **Classify + extract** (`extract/`) — identify the item type, then apply that
   type's attribute template. Ten item names across six commodity families:
   fastener, bearing, valve, gasket, flange, pipe. Attributes carry a
   criticality: `CRITICAL` / `IMPORTANT` / `MINOR` / `INFORMATIONAL`. Version
   `template-v2`, rules `R12`.

3. **Retrieve** (`match/retrieve.py`) — two channels, deliberately not averaged:
   - lexical: character 4-gram TF-IDF
   - dense: `bge-small-en-v1.5` embeddings (frozen, downloaded, **not trained**)

   Fused with **Reciprocal Rank Fusion**, `RRF_K = 60`. RRF because BM25-style
   scores are unbounded positives and cosine similarity is in [-1, 1]; averaging
   two incompatible scales is meaningless. The dense channel is imported lazily,
   so a missing install degrades to lexical-only rather than failing to boot.

4. **Compare** (`match/compare.py`) — **three-valued**, never boolean:
   `AGREE` / `DISAGREE` / `UNKNOWN`. "Not stated" is not "different". Units are
   compared with `pint`, so `1/2 INCH` and `DN15` reconcile.

5. **Decide** (`match/engine.py`)

   ```
   score = veto × (0.85 × attribute_agreement + 0.15 × text_corroboration)
   ```

   `veto` is **0 or 1** — a gate, not a weight. Any `DISAGREE` on a `CRITICAL`
   attribute sets it to 0 and the pair scores exactly zero, however similar the
   text. Bands: `T_MATCH = 0.86`, `T_NEAR = 0.70`, `T_REVIEW = 0.45`.

6. **Score** (`ml/model.py`) — when a fitted scorer is on disk:

   ```
   p(match) = veto x calibrate(sigma(w . x + b))
   ```

   The veto multiplies LAST and is not one of the twelve features, so it cannot
   be outvoted — `test_veto_is_not_a_feature` asserts on the contract itself. A
   second gate demotes MATCH to REVIEW_REQUIRED whenever a CRITICAL attribute is
   unstated on either side. Bands are policy on a calibrated probability: MATCH
   0.90, NEAR 0.70, REVIEW 0.40. With no artifact present the engine falls back
   to stage 5 and reports `calibrated: false`.

### Measured, on the synthetic corpus (`python scripts/evaluate.py`)

```
extraction   item type classified 1,800/1,800 (100.0%)
retrieval    recall@1 96.33%   recall@3 97.33%   recall@10 97.67%
decision     precision 99.44%  recall 98.69%  F1 99.06%
veto         2,392 candidates vetoed on a critical attribute
             ALL 2,392 had text similarity ≥ 0.85
latency      p50 13.0 ms   p95 16.9 ms
```

That last block is the architectural claim, measured: 2,392 pairs a pure
similarity-threshold matcher would have merged, that the attribute veto caught.

---

## 4. Data provenance — read this before answering any question about it

**Two different things, and the distinction matters.**

*The embedding model is NOT trained.* `bge-small-en-v1.5` is downloaded frozen
and used for retrieval only. Nobody fine-tuned it and there is no fine-tuning
code in this repository.

*The decision layer IS trained.* `src/nmc/ml/` fits a 12-feature logistic
regression plus an isotonic calibrator on labelled pairs —
`python scripts/train_scorer.py`. Train/validation/test split **by canonical
identity**, never by record, so two renderings of the same bolt cannot straddle
the wall. Negatives are mined from the retriever's own top-k rather than sampled
at random, because a random non-match is a bolt against a bearing and separating
those describes a problem nobody has.

If asked "how did you train it": the retrieval model was not trained at all; the
decision layer was, on ~23k labelled pairs from the synthetic corpus, with the
veto deliberately held out of the feature set.

- **Canonical items, classification, attribute schema, match labels** — derived
  from the US **Defense Logistics Agency FLIS / PUB LOG** public catalogue,
  which is built on the same NATO Codification System India's National
  Codification Bureau adopted in 2008. Research reference only.
- **The surface text** — **synthetic**, generated by `demo/corpus.py`: 600
  canonical specs rendered into 1,800 messy descriptions across four invented
  CPSEs. Ground truth is *correct by construction* — two records match iff they
  came from the same spec. That is the only defensible way to claim labels on
  generated data.
- **No Indian CPSE material master is public, and none was scraped.**

Never claim: "we trained on millions of CPSE records", or "FLIS is CPSE data".
Full detail in `docs/DATA_PROVENANCE.md`.

---

## 5. The governance model (what makes this more than a matcher)

Four features were chosen from ten candidates. The other six were cut.

### Authority is a **pair**, never a role

`organisation × commodity family`, with safety-class certifications layered on
top. Enforced in `authz.py`:

- `require_role` — REQUESTER < REVIEWER < STEWARD < ADMIN
- `require_own_org` — **ADMIN is deliberately NOT exempt.** An administrator who
  can silently rewrite another CPSE's material master is exactly what stops
  CPSEs from joining.
- `in_commodity_scope` — an empty scope means **no** families, not all of them.
  STEWARD and ADMIN bypass this (they are above families); nobody bypasses org.
- `certified_for_class` — **no role grants this.** A controlled class
  (`PRESSURE`, `SOUR`, `FIRED`) needs a named certification plus a written
  justification on every approval.

### Decision certificates, hash-chained

Every approval/rejection writes a `Decision` row: the evidence frozen as it
stood, the gazetteer/template/model versions, the actor, and the competence
scope they held **at that moment** — not what it is now. Each row hashes its
predecessor.

Wording is careful and must stay careful: **tamper-evident, never
tamper-proof.** The chain lives in a database we control, so alone it proves
internal consistency. It becomes evidence when the head is anchored somewhere we
do not control.

### Effective-dated, supersedable mappings

Nothing is deleted. `effective_to` closes and a new row opens, so "this code
meant that material until March, and something else after" is answerable.

### Safety-class lock

`item_class_rules` is configuration, not code. OISD operates under MoP&NG and
audits every Indian refinery on a 2–3 year cycle, which is what makes these
classes worth barring from auto-approval.

---

## 6. Database

SQLite by default via `DATABASE_URL`, schema portable to Postgres, same
migrations. Pragmas: WAL, `foreign_keys=ON`, `busy_timeout`.

| Table | Rows (seeded) | Purpose |
|---|---|---|
| `organisations` | 4 | the invented CPSEs |
| `users` | 5 | demo accounts, PBKDF2 hashes |
| `sessions` | — | httponly cookie tokens |
| `source_records` | 1,800 | the messy input codes |
| `canonical_materials` | 600 | the resolved identities |
| `mappings` | 1,800 | source → canonical claims, effective-dated |
| `decisions` | — | the hash-chained certificates |
| `audit_events` | — | every login and action |
| `item_class_rules` | 4 | GENERAL / PRESSURE / SOUR / FIRED |
| `releases` | 1 | artefact version sets |
| `ingest_jobs` | — | bulk upload status |

**Gotcha, already fixed twice:** `Decision.seq` is the **primary key**, because
SQLite only auto-increments an `INTEGER PRIMARY KEY`. `Decision.id` is the
public handle with its own unique index. Never use `db.get(Decision, id)` — it
looks up `seq == "dec-…"` and 404s. Query the column.

### Seeding

Idempotent, runs on every startup, no-ops once seeded. **22 of the 1,800
mappings are held back as `PROPOSED`** so the review queue has work in it on a
fresh database — an empty queue is the honest result of a fully-adjudicated
corpus and a useless demonstration. The 22 are chosen, not sampled, so each demo
account hits a different rule.

To reset: delete `sangam.db` and restart the engine.

---

## 7. Authentication and the gate

- Passwords: **PBKDF2-HMAC-SHA256**, stdlib, 240k iterations, per-user salt,
  `hmac.compare_digest`.
- Session: httponly cookie, `SameSite=Lax`, `Max-Age` 12h, stored in the DB.
- **The whole platform requires a session.** Only four endpoints answer without
  one: `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/health`.
- The frontend gate is `RequireAuth`, wrapping every `/platform` route but
  sign-in. It treats `loading` as a distinct third state — treating "still
  asking" as "signed out" bounces authenticated users to login on every reload.
- A 401 mid-session raises a `SESSION_LOST` event; `SessionProvider` clears the
  user, the gate fires, and the destination is preserved as `?next=`.
- Client routing is **never** the security boundary. The server refuses anyway.

### Demo accounts — password `sangam-demo` for all

| Email | Role | Org | Scope |
|---|---|---|---|
| `reviewer.a@sangam.gov.in` | Reviewer | CPSE-A | fastener, pipe, flange · certified PRESSURE |
| `reviewer.b@sangam.gov.in` | Reviewer | CPSE-B | fastener |
| `steward@sangam.gov.in` | Steward | CPSE-A | every family, CPSE-A only |
| `requester.a@sangam.gov.in` | Requester | CPSE-A | may propose only |
| `admin@sangam.gov.in` | Admin | CPSE-A | users and organisations |

They are one-click cards on the sign-in screen. Published demonstration
credentials for a synthetic corpus — never reuse them anywhere.

---

## 8. The frontend

**Landing page** (`web/src/sections/`) — a cinematic scroll experience. A 600vh
hero pins a video and scrubs it against scroll through six measured stages
(`Cinematic.tsx`); a seven-step full-bleed wipe explains the scoring model
(`Pipeline.tsx`); `RollingNumber` animates the corpus figures. GSAP ScrollTrigger
+ Lenis. Scrubbed tweens use `ease: 'none'` — mandatory. The landing page makes
**zero API calls**; every figure is hardcoded in `lib/content.ts`.

**Platform** (`web/src/app/`) — left rail, sticky translucent header, ten
screens. Design language follows Apple HIG principles: interruptible motion,
springs, `backdrop-filter` materials, size-specific tracking, scroll edge
effects rather than hard dividers.

**Sign-in** is styled as an Indian government system: bilingual identity
(भारत सरकार / पेट्रोलियम एवं प्राकृतिक गैस मंत्रालय), a saffron/white/green
tricolour rule, a restricted-use notice.

> **No State Emblem of India, ever.** Its use is restricted by the *State Emblem
> of India (Prohibition of Improper Use) Act, 2005* to the authorities that Act
> names. A hackathon entry is not one. The SANGAM cube mark takes that position.

**Account screen** (`/platform/account`) states the authority model for one
person — organisation, families, certifications, and what each causes the server
to **refuse**. It is the screen that explains a refusal before you hit it.

### Frontend traps discovered the hard way

- **Tailwind v4 statically resolves `var()` inside `@theme` arbitrary values**,
  which breaks runtime theming. App tokens live in plain `:root`, not `@theme`.
- **WebKit does not invalidate rendered nodes** when a `:root` custom property
  changes via an attribute selector. `ThemeToggle` calls `forceRestyle()` —
  detach the subtree for one frame.
- **`AnimatePresence mode="wait"` on route transitions is a trap**: it costs
  220ms of dead screen per click, and if the tab is backgrounded mid-navigation
  rAF pauses, the exit never completes, and the URL changes while the screen
  does not. Routes use a keyed `motion.div` with no exit. The **one deliberate**
  `mode="wait"` is in `Analyse.tsx`, where the pause shows the engine working.
- A grid child defaults to `min-width: auto`; without `min-w-0` on the aside,
  the rail's `overflow-x-auto` has nothing to clip and the page scrolls sideways.

---

## 9. Honesty rules — these are product decisions, not style

The system is careful about what it does **not** claim. Preserve this.

- **No calibration.** Confidence numbers are labelled `uncalibrated` in the UI.
- **SANGAM does not predict** stress, thermal behaviour, corrosion, fatigue or
  lifetime. A stage once called "PROPERTY PREDICTION" was renamed to the
  relationship map for exactly this reason.
- **The relationship map's PCA scatter is reported as text, not drawn**, because
  it was measured that in embedding space the *wrong* answer sometimes sits
  closer than the right one (`SS HEX BOLT M20X50` at 0.9860 vs the correct
  duplicate at 0.9604). Similarity is therefore never used as a position
  channel. `rank_fidelity()` reports USABLE / WEAK / NOT A DISTANCE MAP.
- Relationship bands say "Close — not confirmed", not "probable alternative".
- Every screen carries a `DemoNote` saying the corpus is synthetic.
- NPS↔DN is a **designation table** (ASME B36.10M), never a ×25.4 conversion.

---

## 10. Commit history

| Commit | What landed |
|---|---|
| `aea5702` | Sprint 0: skeleton, FLIS acquisition, commodity slice |
| `3cff1dc` | Sprint 1: working matching engine with critical-attribute veto |
| `1038c87` | Forensic teardown of patternbreak.ing as landing reference |
| `9970b6c` | Landing page + platform experience plan |
| `d33b9dd` | Landing page: CONVERGENCE direction, twelve sections |
| `12767a1` | Platform: material check wired to the real engine |
| `e726a0e` | Rebuild the platform as an application, not a terminal |
| `96266c5` | Analyse: first run as animation, ambient semantic surfaces |
| `f850b47` | SANGAM: relationship map, piping families, product rebrand |
| `833dd0c` | STARTUP.md + fix the requirements file it depends on |
| `ddf8f43` | Landing: rebuild as a scroll-scrubbed cinematic hero |
| `bb6ff30` | Landing: capability grid → seven-step scoring model |
| `5cfa4c4` | Pipeline: card dwell, restored light, slower scroll |
| `99c0c1a` | Platform: rebuild against Apple's interface principles |
| `4e73795` | Platform: dark theme, accent and ink re-derived |
| `173c63f` | Persistence and the write path — the platform stops forgetting |
| `60bb865` | RBAC front end: sign-in, review queue, decision ledger |
| `d94f6b8` | Require a session for everything; government sign-in, account screen |

---

## 11. Bugs already found and fixed — do not reintroduce

1. **`\b#` never matches after a space.** `#150` pressure class was never
   extracted, silently un-vetoing a CRITICAL attribute. `#` must sit *outside*
   the leading `\b`.
2. **`db.get(Decision, id)`** — see §6. 404s on every certificate.
3. **`approve()` returned early before the authority check**, so a CPSE-B
   reviewer and a REQUESTER both got `200 APPROVED` on a CPSE-A record.
   Authorisation now runs *ahead* of the idempotent return.
   Regression test: `test_approve_checks_authority_before_state`.
4. **No request sent `credentials: 'include'`** — the session cookie was never
   transmitted, so every authenticated call would have failed.
5. Nut renderer emitted the literal string `"None"`, breaking thread extraction.
6. Bearing template required `MATERIAL`; no bearing description states one.
7. `readableError` missed WebKit's `"Load failed"` offline string.
8. White on the dark-theme accent measured 2.62:1 — hence `--color-on-brand`.
9. A bare `.catch(() => {})` turned a failed certificate fetch into a dead click.

---

## 12. What is NOT built

Be accurate about this; do not imply otherwise.

Objection ledger · release-gate replay · dictionary desk · evidence tiers ·
demand window · emergency lane · MPN fast path ·
validation against real CPSE data · CI · Docker · rate limiting · CSRF tokens ·
password reset · account self-registration.

---

## 13. Working agreements

- Never commit datasets, `.env`, credentials, or `sangam.db`.
- Never run a broad `git add -A` from the home directory.
- Commits are authored `Claude <noreply@anthropic.com>` (repo convention; git
  identity is unset, so pass `-c user.name=… -c user.email=…` per command).
- Verify claims by running things. The numbers in §3 come from
  `scripts/evaluate.py`, not from memory.
