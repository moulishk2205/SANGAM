# Platform / Engineering Research — SIH26099
### Phase 0, research track: infrastructure, storage, backend, frontend, serving, deployment
**Date: 2026-08-26.** Everything below is labelled `[VERIFIED]` (I fetched a source this session, URL given), `[JUDGMENT]` (my engineering opinion, no source), `[CALC]` (arithmetic from a verified formula — still needs measuring), or `[ASSUMPTION]` (unchecked; I say how to check it).

**Nothing in this document is an invented benchmark, dataset link, or API endpoint.** Where I do not know, I write UNVERIFIED and give the exact command to check.

---

## 0. TL;DR — the verdicts, in one table

| Decision | Verdict | Confidence |
|---|---|---|
| Primary datastore | **Postgres 18 + pgvector 0.8.6, single instance. Nothing else.** | High |
| Dedicated vector DB (Qdrant/Milvus/Weaviate) | **CUT.** Not warranted below ~10M vectors. | High |
| OpenSearch / Elasticsearch | **CUT.** 2 GB+ JVM heap, second data copy, sync logic, zero payoff at this scale. | High |
| Lexical search | `tsvector` + GIN, plus `pg_trgm` GIN. **Fuse with RRF, not with tuned score weights.** | High |
| ParadeDB `pg_search` (real BM25) | **Optional upgrade, not baseline.** Only if measured lexical recall is the bottleneck. | Medium |
| Backend | FastAPI + **SQLAlchemy 2.0 (not SQLModel)** + Alembic + Pydantic v2 | High |
| Background jobs | **Hand-rolled Postgres queue** (`FOR UPDATE SKIP LOCKED`) — you need the job table anyway. Second choice: Procrastinate. **Celery: CUT.** | High |
| Frontend | **Vite + React + TypeScript SPA. NOT Next.js.** | High |
| Component kit | shadcn/ui (Radix + Tailwind) + **TanStack Table pinned to v8** | High |
| Charts | Recharts. **visx/D3: CUT.** | High |
| Graph render | Cytoscape.js, capped at ~300 visible nodes (ego-graphs) | High |
| Graph database (Neo4j / AGE / Memgraph) | **CUT.** Recursive CTE over an edge table is enough for 2–3 hops. | High |
| ETL | Polars (or pandas+pyarrow if nobody knows Polars). **Spark: CUT, absolutely.** | High |
| Excel reading | `calamine` engine, not openpyxl | High |
| Embedding serving | ONNX Runtime int8, **in the worker process**, not a separate service | High |
| Separate inference service (Triton/TorchServe/vLLM) | **CUT.** | High |
| Demo topology | **One laptop, docker-compose, localhost, zero network. Identical hot-spare laptop.** | Very high |
| Cloud free tiers as the demo | **CUT as primary.** Cold starts + venue Wi-Fi = the single most likely way you lose. | Very high |
| Auth | Hand-rolled JWT (PyJWT) or FastAPI-Users. **Keycloak: CUT.** | High |
| Audit | Append-only table + hash chain + role-level `INSERT`-only GRANT | High |
| Blockchain | **Theatre. CUT.** Hash chain gives you 95% of the honest claim for 30 lines. | Very high |

---

## 1. Postgres as the single spine

### 1.1 Version baseline

- **PostgreSQL 18.6** is current (released 2026-08-13). `[VERIFIED]` https://www.postgresql.org/docs/current/index.html and https://www.postgresql.org/about/news/postgresql-183-179-1613-1517-and-1422-released-3246/
- **pgvector 0.8.6** is the current release; supports Postgres 13+. `[VERIFIED]` https://github.com/pgvector/pgvector
- Official image tags exist: `pgvector/pgvector:pg18`, `0.8.6-pg18-trixie`, `linux/amd64` + `linux/arm64` (so it runs natively on Apple Silicon laptops — matters for this team). `[VERIFIED]` https://hub.docker.com/r/pgvector/pgvector/tags

**Use `pgvector/pgvector:pg18` and pin the digest.** Do not use `:latest`. A silent base-image bump the week of the final is a self-inflicted wound.

Two Postgres 18 features you should actually use `[VERIFIED]` https://www.postgresql.org/docs/current/release-18.html:
- **`uuidv7()`** — timestamp-ordered UUIDs. Use for all surrogate PKs. You get global uniqueness (needed if CPSE instances ever federate) *without* the B-tree write amplification of UUIDv4. Note: your human-facing `NMC-0001842` canonical ID is a *separate* display column from a sequence, not the PK.
- **`RETURNING old.* , new.*`** — a single `UPDATE ... RETURNING old.status, new.status` gives you before/after in one statement, no trigger, no race. This is exactly the primitive your audit trail wants.

### 1.2 pgvector: types, indexes, and what they cost

Storage, from the README `[VERIFIED]` https://github.com/pgvector/pgvector:

| Type | Bytes/row | Index dim limit (HNSW & IVFFlat) |
|---|---|---|
| `vector` | 4·d + 8 | 2,000 |
| `halfvec` | 2·d + 8 | 4,000 |
| `bit` | d/8 + 8 | 64,000 |
| `sparsevec` | 8·nnz + 16 | 1,000 nnz (HNSW) |

`[CALC]` For a 384-dim model (MiniLM class), per row: `vector` = 1,544 B; `halfvec` = 776 B; `bit(384)` = 56 B.
For a 1024-dim model (static-retrieval-mrl-en-v1) truncated by Matryoshka to 256: `halfvec(256)` = 520 B.

**Index size and build cost.** pgvector's HNSW stores the *full vector inside the index*, plus neighbour lists. So index size ≈ rows × (vector bytes + ~200–300 B of link/page overhead at `m=16`). `[CALC]` — this is arithmetic on the documented storage formula plus a judgment on graph overhead, **not a measured benchmark. Measure it with `\di+` / `pg_relation_size()` before you quote it.**

| Rows | `halfvec(384)` table cost | HNSW index (est.) | Verdict |
|---|---|---|---|
| 100k | ~78 MB | ~100 MB | Trivial. Fits in shared_buffers on any laptop. |
| 1M | ~780 MB | ~1.0 GB | Fine on a 16 GB laptop. |
| 10M | ~7.8 GB | ~10 GB | Needs a real server (32–64 GB) or quantisation. |

Measured data points I did find, for calibration (different dimensionality, so do **not** extrapolate blindly): on 4 vCPU / 8 GB, PG 18, pgvector 0.8.1, **25,000 rows at 3,072 dims** → HNSW build **29 s**, index **193 MB**, query 2–6 ms; IVFFlat build **5 s**. `[VERIFIED]` https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/

**Build-time levers (these are the ones that matter, in order):**
1. `SET maintenance_work_mem = '8GB'` (or as much as you can spare). If the HNSW graph does not fit, pgvector falls back to a disk-based build. The README explicitly recommends 8 GB. `[VERIFIED]` https://github.com/pgvector/pgvector. Secondary sources put the disk-fallback penalty at **10–50×**. `[ASSUMPTION]` — verify by building the same index twice with `maintenance_work_mem` at 64 MB vs 4 GB and timing it.
2. `SET max_parallel_maintenance_workers = 7;` — parallel HNSW builds landed in pgvector 0.6.0 and Neon reported a **30×** improvement on 10M × 1536-dim on a 64 vCPU / 512 GB box. `[VERIFIED]` https://neon.com/blog/pgvector-30x-faster-index-build-for-your-vector-embeddings
3. **Build the index AFTER the bulk load, never before.** Insert 100k rows into an unindexed table, then `CREATE INDEX`. Inserting into a live HNSW index is dramatically slower.

**halfvec vs binary quantisation.** Use `halfvec`. It halves storage and index build time with essentially unchanged recall at reasonable `ef_construction`. `[VERIFIED, secondary]` https://neon.com/blog/dont-use-vector-use-halvec-instead-and-save-50-of-your-storage-cost. Binary quantisation (`bit` + Hamming) did **not** hold recall on 1536-dim embeddings in reported experiments `[VERIFIED, secondary]` same source. **For this project binary quantisation is premature optimisation — you are at 100k rows, not 100M. CUT it from Phase 1.**

**Concrete DDL to write down now:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;   -- lets you put tenant_id INTO a GIN index

ALTER TABLE material_record ADD COLUMN embedding halfvec(384);

-- build AFTER load:
SET maintenance_work_mem = '4GB';
SET max_parallel_maintenance_workers = 7;
CREATE INDEX idx_mr_emb ON material_record
  USING hnsw (embedding halfvec_cosine_ops)
  WITH (m = 16, ef_construction = 200);
```

**How to pick `ef_search`:** it is a *query-time* knob (`SET hnsw.ef_search = 100`). Default 40. Sweep it on your labelled eval set: 40 → 64 → 100 → 200, plot recall@50 vs p95 latency, pick the knee. `[VERIFIED]` — the DBA guide notes the planner starts flip-flopping above ~200 https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/. **Do not hardcode a number from a blog post. This is a measurable thing; measure it and put the curve in your evaluation deck — judges love a curve that shows you actually ran experiments.**

**A trap you WILL hit:** HNSW + a `WHERE` filter (e.g. `WHERE cpse_id != 3`) is a *post-filter* in pgvector. If your filter is selective, the index returns `ef_search` candidates and then throws most away, and your recall silently craters. Mitigations, in order of preference:
1. **Over-fetch**: retrieve `LIMIT 500` from the vector index, filter in the outer query, keep top 50.
2. **Partial indexes** per category if you must filter by a low-cardinality column.
3. Do not filter in the vector query at all — filter in the rerank stage.

### 1.3 pg_trgm for fuzzy text

`[VERIFIED]` https://www.postgresql.org/docs/18/pgtrgm.html:
- `%` operator, default `pg_trgm.similarity_threshold = 0.3`
- `<%` / `%>` word similarity, default `word_similarity_threshold = 0.6`
- `<<%` / `%>>` strict word similarity, default `strict_word_similarity_threshold = 0.5`
- Distance operators `<->`, `<<->`, `<<<->` (= 1 − similarity)
- GIN vs GiST: **GiST supports efficient distance-ordered `ORDER BY ... <-> ... LIMIT n`; GIN does not.** GIN is faster for containment-style lookups.
- Accelerates `LIKE`/`ILIKE`/regex. **Caveat straight from the docs: "A pattern with no extractable trigrams will degenerate to a full-index scan."**

`[JUDGMENT]` For your workload — "give me the 50 most string-similar descriptions to this one" — that is a distance-ordered top-N, which is the **GiST** case. But GIN is better for the `%` boolean prefilter. Pragmatic answer for a prototype at 100k rows: **build the GIN index, use `%` as a cheap prefilter, and let the outer query rank.** At 100k rows a GiST distance scan is also fine. Do not agonise; benchmark both with `EXPLAIN (ANALYZE, BUFFERS)` and move on. This is 20 minutes of work, not a design decision.

`[JUDGMENT] — important for THIS domain:` raw trigram similarity on material descriptions is a **weak** signal and will embarrass you. `SS HEX BOLT M10 X 50` vs `SS HEX BOLT M10 X 75` scores extremely high on trigrams — they differ by two characters — and they are **different materials**. Trigram is useful for exactly two things here:
1. Recall augmentation in the candidate-retrieval stage (catch typos/abbreviations the embedding misses).
2. Matching *original CPSE codes* (`MAT-78291` vs `MAT 78291`).
It must never be a large weight in the final scorer. That is a design point the ML track needs to hear.

### 1.4 Full-text search and the BM25 question

`[JUDGMENT, high confidence]` **Postgres `ts_rank` / `ts_rank_cd` is not BM25.** It has no corpus-level IDF term and no document-length normalisation of the BM25 form. It ranks by weighted term frequency and (for `ts_rank_cd`) cover density. For short, keyword-dense strings like material descriptions this matters less than for prose — but you should not claim "BM25" in your deck if you are using `ts_rank`. **Say what you actually do.** That kind of precision is what separates you from the other 40 teams.

Options:

**(a) Baseline — stock Postgres.** `tsvector` generated column + GIN. Free, zero ops. Use `simple` dictionary, **not `english`** — you do not want "bolts"→"bolt" stemming to also mangle `M10` or `SS304`, and English stemming is actively wrong on Indian-language tokens.

```sql
ALTER TABLE material_record
  ADD COLUMN ts tsvector
  GENERATED ALWAYS AS (to_tsvector('simple', coalesce(description_norm,''))) STORED;
CREATE INDEX idx_mr_ts ON material_record USING gin (ts);
```
(Note: PG18 defaults generated columns to VIRTUAL; you must write `STORED` explicitly for an indexable tsvector. `[VERIFIED]` https://www.postgresql.org/docs/current/release-18.html)

**(b) Upgrade — ParadeDB `pg_search`.** Real BM25, built on Tantivy (Rust Lucene equivalent) via pgrx. Ships as a Docker image or prebuilt binaries for Debian 12/13, Ubuntu 22.04/24.04, RHEL 9/10, macOS 14/15, PG15+. `[VERIFIED]` https://github.com/paradedb/paradedb and https://docs.paradedb.com/deploy/third-party-extensions
  - **Cost:** you swap the stock `pgvector/pgvector:pg18` image for the ParadeDB image, i.e. you now depend on ParadeDB's release cadence for both extensions.
  - **Note for anyone reaching for managed Postgres:** Neon dropped `pg_search` for new projects as of 2026-03-19. `[VERIFIED, secondary]` https://neon.com/docs/extensions/pg_search
  - **Verdict `[JUDGMENT]`: not in the baseline.** Adopt only if you *measure* that lexical recall@100 is your retrieval bottleneck. Budget: half a day to swap the image, half a day to port queries. Do it in week 6, not week 1.

**(c) Fusion.** Do **not** hand-tune `0.6*semantic + 0.3*bm25 + 0.1*trgm`. Those scores live on incomparable scales and your weights will be overfit to whatever three examples you looked at. Use **Reciprocal Rank Fusion**: `score(d) = Σ_r 1/(k + rank_r(d))`, `k = 60`. The original authors chose 60 from a pilot study and noted the optimum is flat across `k ∈ [20, 100]`. `[VERIFIED]` https://bigdataboutique.com/blog/reciprocal-rank-fusion-how-it-works-and-when-to-use-it and https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking

RRF is one SQL CTE, has one hyperparameter that barely matters, and is defensible in a viva. It is used for **candidate retrieval only** — the final duplicate/near-duplicate decision comes from your attribute-aware scorer, which is a separate, learned stage.

```sql
WITH sem AS (
  SELECT id, row_number() OVER (ORDER BY embedding <=> $1) AS r
  FROM material_record WHERE tenant_id <> $2 ORDER BY embedding <=> $1 LIMIT 200
), lex AS (
  SELECT id, row_number() OVER (ORDER BY ts_rank_cd(ts, q) DESC) AS r
  FROM material_record, plainto_tsquery('simple',$3) q
  WHERE ts @@ q LIMIT 200
), trg AS (
  SELECT id, row_number() OVER (ORDER BY description_norm <-> $3) AS r
  FROM material_record WHERE description_norm % $3 LIMIT 200
)
SELECT id, SUM(1.0/(60+r)) AS rrf
FROM (SELECT * FROM sem UNION ALL SELECT * FROM lex UNION ALL SELECT * FROM trg) u
GROUP BY id ORDER BY rrf DESC LIMIT 50;
```

### 1.5 JSONB for flexible attributes

You have a genuine schema problem: a bolt has `{diameter_mm, length_mm, thread, grade}`; a cable has `{cores, csa_sqmm, voltage_v, insulation}`. Three options:

| Option | Verdict |
|---|---|
| One wide table with 60 nullable typed columns | **CUT.** Unmaintainable, and every new category is a migration. |
| EAV (`attribute_value` rows) | **CUT.** Every query becomes a pivot. Death by JOIN. |
| **JSONB `attributes` column + a small set of promoted typed columns** | **This one.** |

`[JUDGMENT]` Concrete design:

```sql
CREATE TABLE material_record (
  id            uuid PRIMARY KEY DEFAULT uuidv7(),
  tenant_id     int  NOT NULL REFERENCES cpse(id),
  source_code   text NOT NULL,             -- original CPSE code, NEVER mutated
  description_raw  text NOT NULL,
  description_norm text NOT NULL,
  uom_raw       text,
  uom_canonical text,                       -- after unit normalisation
  category_id   int  REFERENCES category(id),
  attributes    jsonb NOT NULL DEFAULT '{}'::jsonb,
  embedding     halfvec(384),
  -- PROMOTED, typed, indexed. These are the ones the scorer actually gates on:
  attr_nominal_size_mm numeric,
  attr_length_mm       numeric,
  attr_material_grade  text,
  ingest_job_id uuid REFERENCES ingest_job(id),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source_code)
);
CREATE INDEX idx_mr_attrs ON material_record USING gin (attributes jsonb_path_ops);
CREATE INDEX idx_mr_dims  ON material_record (category_id, attr_nominal_size_mm, attr_length_mm);
```

Key points:
- **`jsonb_path_ops`, not the default `jsonb_ops`.** Smaller index, faster for `@>` containment, which is 95% of what you will query. It does *not* support key-existence (`?`) operators — you do not need them.
- **Promote the numerics you compare on.** JSONB numeric range queries are slow and awkward; a plain `numeric` column with a B-tree is instant. The rule: *if the matching engine gates on it, it is a column; if it is only displayed, it stays in JSONB.*
- Store both the parsed value **and** the source span in JSONB, e.g. `{"length_mm": {"v": 50, "unit": "mm", "src": "X 50", "conf": 0.94}}`. Your explainability screen (brief §8) needs the provenance, and retrofitting it later is painful.

### 1.6 Row-Level Security for multi-CPSE isolation

RLS is the right tool. Cross-CPSE harmonisation means the central role legitimately sees everything while a CPSE role sees only its own rows — that is precisely a policy problem, not an app-layer `WHERE` clause problem.

```sql
ALTER TABLE material_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_record FORCE ROW LEVEL SECURITY;  -- applies to table owner too

CREATE POLICY tenant_read ON material_record FOR SELECT
  USING (
    current_setting('app.role', true) = 'central'
    OR tenant_id = current_setting('app.tenant_id', true)::int
  );
```

**The four footguns, all verified as the commonly-reported failure modes** `[VERIFIED, secondary]` https://queryplane.com/blog/postgres-row-level-security-in-practice/ , https://patotski.com/blog/postgres-row-level-security-multi-tenant/ :

1. **`SET LOCAL`, never `SET`.** Plain `SET` persists for the life of the pooled connection; the next request on that connection inherits the previous tenant's context. This is *the* classic multi-tenant data leak. Wrap every request in a transaction and issue `SET LOCAL app.tenant_id = ...` as its first statement — a FastAPI dependency that yields an `AsyncSession` after doing this is ~15 lines.
2. **RLS does not apply to superusers or roles with `BYPASSRLS`.** Your app must connect as a dedicated non-superuser role. If you connect as `postgres`, RLS silently does nothing and you will not notice until a judge asks.
3. **Index `tenant_id` as the leading column of composite indexes.** Reported as the #1 RLS performance killer; without it the policy predicate forces scans.
4. **Do not trust the session variable blindly.** Any DB user can `SET` an arbitrary GUC. It is only safe because *your app* is the only thing that sets it, and the app derives it from a verified JWT. Say that out loud in your security section; it is the honest framing.

**Also add `ALTER TABLE ... FORCE ROW LEVEL SECURITY`** — without it, the table *owner* bypasses policies, and in a dev setup the app role is very often the owner.

### 1.7 Verdict: is "just Postgres" enough?

**Yes. Decisively, and it is not close.** `[JUDGMENT]`

The reasoning, stated so you can defend it:
- Your prototype target is 5k–50k records (brief §5), stretch 100k. The hard ceiling before pgvector genuinely hurts is widely put at **5–20M vectors on a single instance**. `[VERIFIED, secondary]` https://open-techstack.com/blog/pgvector-vs-qdrant-2026/ , https://encore.dev/articles/pgvector-vs-qdrant. You are **2–3 orders of magnitude** below that.
- Your queries are *not* pure vector search. Every retrieval is `vector similarity ∧ category ∧ tenant ∧ attribute range ∧ approval status`. That is a relational query with a vector predicate. Splitting the vectors into a separate store means you either (a) dual-write and reconcile, or (b) fetch 500 IDs from Qdrant and then `WHERE id = ANY($1)` back into Postgres — at which point you have added a network hop, a consistency problem, and a second thing that can be down on stage, to buy latency you do not need.
- **The one-database property is itself a feature you can pitch:** transactional consistency between the material record, its embedding, its approval, and its audit row. A CPSE CIO cares about that. "We have no eventual-consistency window between an approval and the record it approves" is a real enterprise answer.

**Write the crossover point into your architecture doc explicitly** — it turns "we used Postgres because it was easy" into "we used Postgres because we costed the alternative." Suggested wording: *"We migrate the vector tier to a dedicated ANN store when (a) `>10M` vectors, or (b) p95 retrieval latency exceeds 200 ms at recall@50 ≥ 0.95, or (c) HNSW rebuild time exceeds the maintenance window. None of these hold at national-pilot scale; all are monitored."*

---

## 2. Alternatives, and when the switch actually pays

| System | Deploy cost | When it actually pays | Verdict for you |
|---|---|---|---|
| **Qdrant** | Single Rust binary / one container. Genuinely the easiest of the four. | Tens of millions of vectors; heavy metadata filtering where you need *pre*-filtering (Qdrant filters during graph traversal, so recall does not collapse — this is its real technical edge over pgvector). Reported 2–3× lower query latency at 1M+. `[VERIFIED, secondary]` https://rivestack.io/blog/pgvector-vs-qdrant | **CUT now. Name it as the documented migration target.** If you ever need it, it is a 1–2 day swap behind a repository interface. |
| **Milvus** | etcd + MinIO + proxy + query/data/index nodes. Milvus Lite exists for embedded use. | Billions of vectors, GPU indexing, multi-node. | **CUT.** The full deployment is a distributed system. You do not have a distributed-systems budget. |
| **Weaviate** | One container, but opinionated schema + its own module system. | You want built-in hybrid search and vectoriser modules and are happy to live in its data model. | **CUT.** You already own your ML pipeline; the modules are the value prop and you do not need them. |
| **OpenSearch / Elasticsearch** | JVM. Realistically 2 GB+ heap minimum, plus a second full copy of your data, plus index-mapping management, plus sync. | You need real BM25 at scale, aggregations, and analyst-facing search across many indices. | **CUT, hardest of all.** This is the one people add because "enterprise search" sounds right. It doubles your operational surface for a BM25 implementation you can approximate with `ts_rank_cd` + RRF, or get properly via `pg_search` in one image swap. |

`[JUDGMENT]` **Design the abstraction, not the migration.** One Python protocol:

```python
class CandidateRetriever(Protocol):
    async def retrieve(self, q: Query, k: int) -> list[Candidate]: ...
```
with `PgvectorRetriever` as the only implementation. That is your entire "vector-store portability" story and it costs an afternoon. Writing a second implementation now is waste.

---

## 3. Backend

### 3.1 The stack

**FastAPI + SQLAlchemy 2.0 (async) + Alembic + Pydantic v2.** `[JUDGMENT]`

**SQLModel: do not use it.** It is a thin layer over SQLAlchemy + Pydantic that reliably lags both, and the moment you need a window function, a CTE, a `jsonb_path_ops` containment operator, or a `hnsw` order-by — all of which you need on day one — you drop to raw SQLAlchemy anyway and now you have two mental models. Reported consensus is that SQLModel "seems a little behind the curve in keeping up with the latest developments in either SQLAlchemy or Pydantic" and that advanced work requires dropping down. `[VERIFIED, secondary]` https://testdriven.io/blog/fastapi-sqlmodel/ and the 2026 comparison round-up. **The DRY-ness it buys is one class definition per table. That is not worth a second abstraction.**

Instead: SQLAlchemy 2.0 `DeclarativeBase` + `Mapped[]` annotations for the ORM, and separate Pydantic v2 models for request/response. The duplication is real and it is fine — your API shape *should* be allowed to diverge from your table shape, especially for the explainability payloads.

**A large fraction of your queries should be hand-written SQL** (`text()` with bound params, or SQLAlchemy Core). The retrieval CTE above is not expressible pleasantly in ORM and you will fight it. This is a search product; own your SQL.

### 3.2 Async patterns — where teams lose two days

`[JUDGMENT]`, but these are the exact bugs:

1. **`asyncpg` driver, `postgresql+asyncpg://` URL.** Alembic runs sync — configure it with a *separate* sync URL (`psycopg`). Do not try to make Alembic async; it is a documented pain and buys nothing.
2. **Never call blocking code in an `async def` endpoint.** `model.encode(...)`, `pl.read_excel(...)`, `requests.get(...)` — every one of these freezes the entire event loop and your whole app stops answering, including `/health`. Either make the endpoint `def` (FastAPI runs it in a threadpool automatically) or push it to the worker. **On stage this manifests as "the UI froze during the demo" and you will not know why.**
3. **`NullPool` if you sit behind PgBouncer in transaction mode**, otherwise prepared-statement caching breaks with asyncpg. For a docker-compose demo you do not need PgBouncer at all — skip it.
4. **One transaction per request, opened by a dependency**, because RLS needs `SET LOCAL` inside it (§1.6).

### 3.3 Background jobs — the actual decision

The question is not "which queue library is best." It is: **what does a 5-person team operate reliably at 10 a.m. on demo day?**

The landscape as of now:
- **arq is in maintenance-only mode** — stated in its own README. `[VERIFIED]` https://github.com/python-arq/arq. **Do not start a new project on it.**
- **Celery** — the default answer, and the wrong one here. Redis/RabbitMQ broker, a result backend, worker pools, `beat` for periodicity, and a genuinely fiddly config surface. Its failure modes (silently swallowed tasks, serialization surprises, worker pool deadlocks with forked processes + PyTorch) are exactly the ones that eat a student team's last week.
- **Dramatiq** — Celery-alternative with better defaults, Redis/RabbitMQ. Legitimate choice if you want a library.
- **SAQ** — active, Redis Streams, positioned as arq's successor. `[VERIFIED, secondary]` https://aleksul.space/posts/choosing-python-task-queue-library/
- **Procrastinate** — Postgres-only broker using `LISTEN/NOTIFY` + `FOR UPDATE SKIP LOCKED`. Python 3.10+, Postgres 13+, async, retries, periodic tasks, locks. Actively developed (3,500+ commits). **Caveat: the README says the project "is looking for additional maintainers."** `[VERIFIED]` https://github.com/procrastinate-org/procrastinate
- **PgQueuer** — same family, Postgres-backed, transactional enqueue. `[VERIFIED]` https://github.com/janbjorge/pgqueuer
- **FastAPI `BackgroundTasks`** — runs in the *same process* after the response. No persistence, no retry, no progress, dies with the process. **Fine for "send a notification". Catastrophic for "ingest 100k rows".**

**VERDICT `[JUDGMENT]`: hand-roll a Postgres job table with `FOR UPDATE SKIP LOCKED`, and run one separate worker process.**

The reasoning is not "libraries are bad." It is that **you must build the job table anyway.** Brief §11 requires an import-statistics screen showing records processed / valid / missing descriptions / duplicate candidates / invalid units / unmapped categories, live, with a progress bar. No generic queue gives you that; you would end up writing a `ingest_job` table *alongside* Celery and syncing two sources of truth. Given the table exists, the worker is ~120 lines.

```sql
CREATE TABLE ingest_job (
  id             uuid PRIMARY KEY DEFAULT uuidv7(),
  tenant_id      int NOT NULL,
  filename       text NOT NULL,
  status         text NOT NULL DEFAULT 'queued'
                 CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
  stage          text,                    -- 'parsing'|'normalising'|'embedding'|'matching'
  rows_total     int  NOT NULL DEFAULT 0,
  rows_done      int  NOT NULL DEFAULT 0,
  stats          jsonb NOT NULL DEFAULT '{}'::jsonb,
  error          text,
  attempts       int  NOT NULL DEFAULT 0,
  locked_by      text,
  locked_at      timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now(),
  finished_at    timestamptz
);
CREATE INDEX ON ingest_job (status, created_at) WHERE status = 'queued';
```

Worker claim loop — this is the whole trick:

```sql
UPDATE ingest_job SET status='running', locked_by=$1, locked_at=now(), attempts=attempts+1
WHERE id = (
  SELECT id FROM ingest_job
  WHERE status='queued'
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

Plus: a `LISTEN/NOTIFY` channel so the worker wakes instantly instead of polling (fall back to a 1 s poll — with 1 worker this is free); a reaper that requeues rows where `status='running' AND locked_at < now() - interval '10 minutes'`; and `rows_done` updated every 500 records so the UI progress bar moves.

**Frontend progress: use Server-Sent Events, not WebSockets.** SSE is one `EventSourceResponse`, survives proxies, auto-reconnects, and you only need server→client. WebSockets add a protocol, a connection lifecycle, and a class of demo-day bug for zero benefit here. `[JUDGMENT]`

Fallback if the team genuinely does not want to write the loop: **Procrastinate** (still no Redis, still transactional enqueue) with the `ingest_job` table kept as your own progress store. **Never Celery.**

### 3.4 "What happens when a 100k-row upload is processed live on stage?"

Answer honestly, with arithmetic. `[CALC]` on 100k rows:

| Stage | Est. wall time (8-core laptop) | Notes |
|---|---|---|
| Parse XLSX (calamine) | 5–20 s | ~10–50× faster than openpyxl (§5) |
| Normalise + attribute extract (regex/rules, Polars) | 10–60 s | Dominated by regex, not IO |
| Embed 100k short strings (ONNX int8 MiniLM) | **~40–330 s** | See §6 for the range and how to measure |
| `COPY` into Postgres | 5–15 s | Use `COPY`, not row-by-row `INSERT` |
| Build HNSW index | 30–120 s | See §1.2 |
| Blocking + candidate retrieval for 100k sources | **minutes to tens of minutes** | This is the real cost — see below |
| Cross-encoder rerank top-25 × 100k | **hours on CPU** | See below |

**The candidate-retrieval stage is the one that will surprise you.** 100k ANN queries at even 3 ms each = 300 s single-threaded, and that assumes no rerank. Add a cross-encoder over 25 candidates each = 2.5M pairs; at an optimistic 500 pairs/s on CPU that is **~83 minutes**. `[CALC]` — measure before you trust it.

**Therefore, the verdict on the demo `[JUDGMENT], and this is the single most important operational recommendation in this document`:**

> **DO NOT process a 100k-row upload live on stage. Ever.**
>
> Pre-ingest the 100k baseline corpus (3 CPSEs) into a seeded database *before* the demo. On stage, upload a **500–2,000 row delta file** representing "CPSE-D's new quarter of materials". That runs end-to-end in **10–40 seconds** — long enough for the progress UI to look real and impressive, short enough that you are not standing in silence.

This is not cheating and you should say so out loud: *"The 240,000-record baseline was ingested overnight, as it would be in production. What you are watching now is the incremental daily flow, which is the actual steady-state workload."* That framing is **more** credible than pretending a national dataset loads in 30 seconds, and it pre-empts the judge who was going to ask.

Second-order protections:
- A **hard cap** on live-upload size (e.g. 5,000 rows) with a clear UI message, so nobody drags in the wrong file under pressure.
- The worker must **stream**, never `read_excel()` a 500 MB file into RAM. Chunk at 5,000 rows.
- **Idempotency**: a re-upload of the same file must not double-insert. `UNIQUE (tenant_id, source_code)` + `ON CONFLICT DO UPDATE`, plus a content hash on `ingest_job`.

---

## 4. Frontend

### 4.1 Next.js vs Vite SPA — pick Vite

**VERDICT: Vite + React 19 + TypeScript SPA. Do not use Next.js.** `[JUDGMENT], high confidence.`

Next.js 16.3 is current (released 2026-08-03) and is a fine framework. `[VERIFIED]` https://nextjs.org/blog/next-16-3 . It is the wrong tool here:

1. **You have zero SEO requirement.** Every screen is behind auth. SSR's headline benefit does not apply.
2. **App Router forces you to reason about Server Components, the client/server boundary, and an opt-in caching model** (Next 16 made Cache Components opt-in, which helps, but the boundary questions remain). Every hour a student spends debugging "why is this a Server Component and why can't I use `useState`" is an hour not spent on the matching engine. **The AI-assisted development the team is relying on makes this worse, not better** — model output mixes App Router and Pages Router idioms constantly.
3. **Deployment.** A Vite build is a folder of static files. You mount it with `StaticFiles` inside the *same* FastAPI container. Result: **one container, one port, one origin, no CORS, no reverse-proxy config, no Node runtime in production.** Next.js needs a Node server (or Vercel). For a demo that must not fail, one process is worth a lot.
4. **Offline.** Static assets served from your own FastAPI mean no `_next/` chunk fetched from a CDN, no font hitting Google, no telemetry call. See §7.

Router: **TanStack Router** (type-safe, excellent search-param handling — you will want filter state in the URL for a data-dense tool) or **React Router v7 in declarative mode**. Either is fine; TanStack Router's typed search params are genuinely useful for "share a link to this filtered review queue."

Server state: **TanStack Query**, non-negotiable. Caching, background refetch, and optimistic updates for the Approve/Reject actions come free.

### 4.2 Component library

**shadcn/ui** (Radix primitives + Tailwind, copied into your repo). `[JUDGMENT]`
- You own the code, so the "premium enterprise" look the brief demands (§31) is achievable by editing tokens, not by fighting a theme system.
- Radix gives you real accessibility (focus management, ARIA) for free — and the brief explicitly asks for accessible.
- Ant Design would get you further faster on dense enterprise widgets, but it looks unmistakably like Ant Design, and "looks like every other admin template" is precisely the failure mode §31 warns against. Mantine is a reasonable middle path if the team wants batteries.

**⚠️ CRITICAL LANDMINE — TanStack Table v9.** `[VERIFIED]` https://www.infoq.com/news/2026/07/tanstack-table-v9-beta/ and https://github.com/shadcn-ui/ui/issues/11389 :
- `@tanstack/react-table` v9.0.0 is now the `latest` npm tag. The API changed substantially: `useReactTable` → `useTable`; `get*RowModel` options → a `features` object; `flexRender` became a component.
- **The shadcn/ui docs migrated to v9 in August 2026, but the change was not announced in the changelog** — so essentially every tutorial, StackOverflow answer, blog post, and (critically) **every LLM's training data** shows v8, and **v8 code does not run on v9.**
- **ACTION: pin `"@tanstack/react-table": "^8"` in `package.json` on day one and write a comment saying why.** A `useLegacyTable` shim and a `stockFeatures` import exist if you end up on v9 by accident. This one line will save your team half a day of AI-generated code that does not compile.

Virtualisation: **TanStack Virtual** for any list over ~200 rows. Your review queue and material master will have thousands. Do not render 5,000 `<tr>` elements; the browser will not thank you.

### 4.3 Charting

**Recharts.** `[JUDGMENT]` Declarative, React-native, composable, covers 100% of what the dashboards in brief §10/§18 need (bar, line, area, pie, stacked bar). It gets slow above roughly 5–10k SVG points — you will never approach that, because a dashboard chart with 10k points is unreadable anyway.

- **visx / D3: CUT.** They are toolkits, not chart libraries. You will spend a week building axes.
- **ECharts: only** if you end up wanting a genuinely large scatter (e.g. 50k materials in embedding space via UMAP) — its canvas renderer handles that where Recharts will not. Treat as a single-chart exception, not a library decision.
- **Observable Plot:** elegant, but React integration is imperative (render-into-a-ref) and the ecosystem is thinner. CUT.

**One genuinely valuable non-obvious chart:** a **UMAP/t-SNE scatter of the embedding space, coloured by category, with confirmed duplicate pairs joined by a line.** It is the single most persuasive "the AI actually learned something" visual you can put in front of a judge, it takes an afternoon (compute offline, store 2 floats per row), and it is *evidence*, not decoration.

### 4.4 Graph visualisation

Honest sizing first: **what graph are you actually drawing?**
- A unified material + its 3–8 CPSE codes + a few suppliers = **~15 nodes.**
- A category cluster ("all fasteners") = **a few hundred nodes.**
- "The whole national material graph" = 100k+ nodes = **an unreadable grey hairball that communicates nothing.**

`[JUDGMENT]` **Never render the hairball.** It looks impressive for four seconds and then a judge asks "what am I looking at?" and you have no answer. Render **ego-graphs capped at ~300 nodes** with expand-on-click.

Library comparison `[VERIFIED, secondary]` https://www.pkgpulse.com/guides/cytoscape-vs-vis-network-vs-sigma-graph-visualization-2026 and https://www.cylynx.io/blog/a-comparison-of-javascript-graph-network-visualisation-libraries/ :

| Library | Renderer | Reported ceiling | Verdict |
|---|---|---|---|
| **Cytoscape.js** | Canvas | reported sluggish past ~10k on-screen nodes | **USE THIS.** Rich styling, built-in layouts (`fcose`, `cola`, `dagre`), mature, well documented, graph-theory algorithms included. |
| sigma.js + graphology | WebGL | reported practical ceiling ~100k–500k depending on edge density/hardware | Only if you insist on the hairball. You do not. |
| react-force-graph | Canvas/WebGL/3D | — | Fine, prettier defaults, less styling/event control. The 3D mode is pure theatre. |
| D3-force | SVG | low thousands | CUT. You will hand-build everything. |

**The source I checked is explicit that universal node-count benchmarks should not be trusted** — they depend on edge density, labels, and layout. `[VERIFIED]` same source. So: **build a 300-node and a 2,000-node fixture in week 3 and click around on the actual demo laptop.** Do not discover this in week 9.

`[JUDGMENT]` **Precompute layouts server-side for the demo.** Running `fcose` on 2,000 nodes in the browser during a presentation is a visible 3–8 second freeze. Store `(x, y)` per node in Postgres, pass `layout: {name: 'preset'}`. The graph then appears instantly. This is a five-line change that transforms how the demo feels.

---

## 5. Data processing

### 5.1 Pandas vs Polars vs DuckDB vs (please no) Spark

**The blunt truth `[JUDGMENT]`: at 10k–1M rows on a laptop, all three work, and this is not where your project succeeds or fails.** Anyone telling you the DataFrame library is the critical decision is optimising the wrong thing. The hard part of your ingestion layer is dirty Excel and messy strings, and none of these three solves that for you.

Reported figures for calibration `[VERIFIED, secondary]` https://codecut.ai/pandas-vs-polars-vs-duckdb-comparison/ , https://www.danilchenko.dev/posts/polars-vs-pandas/ : Polars roughly **5–10× faster than pandas** above 1M rows on aggregations/joins/filters; **~7.7× faster CSV reads** at 10M rows. Guidance from the same sources: under ~1M rows, pandas with Arrow dtypes is fine; over ~100M on one machine, use Polars lazy or DuckDB.

> ⚠️ I saw one widely-shared blog claiming Polars uses "11,791,583× less memory than pandas." That is nonsense from a broken benchmark (it compares peak RSS of a streaming aggregation to a full materialisation). **Do not cite it.** If a number looks like that, it is wrong.

**Recommendation `[JUDGMENT]`:**
1. **Polars** if anyone on the team already knows it. Its strict typing and explicit null handling catch exactly the class of bug you will hit ("this column is int in file A and str in file B"), where pandas silently coerces to `object` and you find out three stages later.
2. **pandas + `dtype_backend="pyarrow"`** if nobody does. Don't learn a new library in week 2.
3. **DuckDB** as a *complement*, not a replacement: it is superb for the exploratory/EDA phase (`SELECT * FROM 'data/*.csv'` with zero loading) and for generating your evaluation metrics. It also reads Parquet/CSV directly, which makes your dataset-generation notebooks pleasant.

**SPARK: NO. `[JUDGMENT], stated as bluntly as the brief asked.`** Spark on 100k rows is slower than pandas because JVM startup, serialisation, and shuffle overhead dominate a workload that fits in L3 cache. It is a distributed-computing framework and you have one laptop. Putting it on your architecture slide invites exactly one question — *"how many nodes is your cluster?"* — and there is no good answer. **If you want the scalability story, say: "the ingestion stage is embarrassingly parallel by CPSE and by category; the current implementation is single-node Polars, and the same transformations lift to Spark or Ray without change if volumes reach hundreds of millions." That is a correct, defensible, unfalsifiable-in-a-good-way statement. Do not actually build it.**

### 5.2 File parsing: the risks that will actually bite you

**Excel.** Use the **`calamine`** engine (Rust, via `python-calamine`; supported by `pandas.read_excel(engine="calamine")` since pandas 2.2.0, and by Polars via `fastexcel`). Reported **~5–6× faster** on typical files and **20–50× on large XLSX**. `[VERIFIED, secondary]` https://hakibenita.com/fast-excel-python and https://github.com/pandas-dev/pandas/issues/50395 . Caveat from the same source: openpyxl/pyxlsb are faster when reading *a few rows* from a large file, because they iterate lazily.

The Excel quirks that will corrupt your material codes `[JUDGMENT], all of these are standard, well-known Excel behaviours`:

| Quirk | What breaks | Mitigation |
|---|---|---|
| Leading-zero truncation: `00123` → `123` | **Material codes silently change identity.** | Read *all* code columns as `str`. Never let a code column be inferred. |
| Scientific notation: `1234567890123456` → `1.23457E+15` | Long numeric codes lose precision **irreversibly** | Same. And *validate*: if a code column contains `E+`, reject the file loudly. |
| Date auto-conversion: `MAR-10`, `1-2`, `SEP 5` → dates | Size designations become 2026-03-10 | Read as `str`; if a code cell arrives as a `datetime`, flag it in the data-quality report. |
| Merged cells | `None` in all but the top-left cell | Forward-fill header rows explicitly; reject merged cells in the data body. |
| Multi-row / multi-level headers | Column mapping fails | Require a header-row index in the upload UI. Preview the first 20 rows before committing. |
| Trailing spaces, non-breaking space (U+00A0), zero-width space (U+200B) | Two "identical" strings that are not equal | Unicode-normalise (NFKC), map U+00A0→space, strip control chars, collapse whitespace. **Put this in the normaliser, and log how many rows it changed — it makes a great data-quality stat.** |
| Multiple sheets; the real data is on sheet 3 | Silent empty import | Let the user pick the sheet; show row counts per sheet. |
| Legacy `.xls` (BIFF binary) | openpyxl cannot read it at all | calamine handles xls/xlsx/xlsb/ods. Another reason to use it. |
| Formula cells | You import `=A2&" "&B2` instead of the text | Read values, not formulas (calamine gives cached values). |

**Encoding (CSV).** Do not guess with a bare `open()`. Order of attack: (1) BOM sniff — a UTF-8 BOM is common from Excel exports; (2) try `utf-8`; (3) try `utf-8-sig`; (4) try `cp1252`; (5) fall back to `charset-normalizer` detection and **tell the user what you guessed**. Indian CPSE files will contain Devanagari, `°`, `Ø`, `µ`, `±`, `×` — all of which mojibake differently per codepage. `Ø` (diameter symbol) becoming `Ã˜` is a real failure that will corrupt your attribute extraction. `[JUDGMENT]`

**CSV injection (a.k.a. formula injection).** This is an **export** vulnerability, not an import one. If a cell you write to a CSV/XLSX starts with `=`, `+`, `-`, `@`, TAB (0x09) or CR (0x0D), Excel may execute it when the file is opened. Since you will absolutely build "export the harmonised master to Excel", sanitise on the way out: prefix such cells with `'`, or quote and prefix with a space. `[JUDGMENT], standard OWASP guidance — verify by searching "OWASP CSV Injection" if you want a citation for the report.` Do **not** strip these characters on import — `-` is legitimately part of material codes.

**Huge files / DoS.**
- Stream uploads to disk; never `await file.read()` into memory. FastAPI's `UploadFile` spools to disk above a threshold, but set an explicit `Content-Length` cap in the reverse proxy or a middleware.
- **Zip bombs:** `.xlsx` is a ZIP. A 1 MB file can expand to gigabytes. Check the ZIP central directory's declared uncompressed size *before* extracting and reject above a ratio (e.g. 100×) or absolute size (e.g. 1 GB).
- **XXE / external entities:** `.xlsx` contains XML. Use `defusedxml` if you ever parse the XML yourself; calamine/openpyxl handle this, but do not roll your own.
- Validate by **content sniffing** (magic bytes: `PK\x03\x04` for xlsx, `\xD0\xCF\x11\xE0` for legacy xls), not by file extension.
- Malware scanning (ClamAV): **name it in the security architecture, do not build it in the prototype.** It is a container and a config, and it adds nothing demonstrable.

---

## 6. Serving the ML model

### 6.1 Architecture verdict

**In-process, in the worker. `[JUDGMENT], high confidence.`**

- Load the ONNX Runtime `InferenceSession` **once** at worker startup, keep it in module scope.
- **Do not load it in the API process.** A 90 MB model × 4 uvicorn workers = 360 MB of duplicated RAM and 4 copies fighting over cores. The API should never embed anything synchronously except a single query string during interactive search — and for that, one small session in the API process is acceptable *if* you call it via `run_in_threadpool`.
- **Set `intra_op_num_threads` explicitly.** ONNX Runtime defaults to all cores; with a multi-process worker you get catastrophic oversubscription (N processes × N threads). Rule of thumb: 1 worker process, `intra_op_num_threads = physical_cores`.
- **Separate inference service (Triton, TorchServe, Ray Serve, KServe): CUT.** You gain a network hop and a second thing that can be down. The only real argument is GPU sharing, and you do not have a GPU on stage.
- **But keep the seam:** `class Embedder(Protocol): def encode(self, texts: list[str]) -> np.ndarray`. One afternoon, and it makes "we can deploy inference on-premise inside the CPSE's boundary" (brief §29) a true statement rather than a slide.

### 6.2 Throughput — real numbers and honest ranges

**Verified anchors:**
- ONNX Runtime int8 dynamic quantisation: commonly cited **2–4× CPU speedup** with minimal accuracy loss; quantised 12-layer BERT with Intel VNNI reported up to **2.9×**, DistilBERT up to **3.3×**. `[VERIFIED, secondary]` https://opensource.microsoft.com/blog/2021/03/01/optimizing-bert-model-for-intel-cpu-cores-using-onnx-runtime-default-execution-provider/
- Sentence Transformers' own efficiency page reports, on short-text STSb: ONNX **1.35×**, OpenVINO **1.24×**, **ONNX int8 3.23×** over PyTorch on CPU. `[VERIFIED, secondary — retrieved via search snippet attributed to]` https://sbert.net/docs/sentence_transformer/usage/efficiency.html — **verify by opening that page directly; my direct fetch of it did not surface these numbers.**
- Dynamic quantisation is **CPU-only** and needs no calibration dataset. `[VERIFIED, secondary]` https://www.philschmid.de/optimize-sentence-transformers

**Reported all-MiniLM-L6-v2 CPU throughput varies wildly across sources — ~50 sentences/s single-threaded (PyTorch) up to ~237/s.** `[VERIFIED that these figures are reported; UNVERIFIED as reliable]` — they come from low-quality blog aggregation and do not state batch size or sequence length, which change the answer by 10×.

**So here is my honest estimate, clearly labelled `[JUDGMENT]`, with the exact way to check it:**

Material descriptions are *short* — roughly 8–20 tokens. That is the best case for a small encoder (attention is quadratic in sequence length, and you are nowhere near the 256-token default). With `max_seq_length=32`, `batch_size=128`, ONNX int8, on a modern 8-core laptop CPU:

| Setup | Est. throughput | 100k strings |
|---|---|---|
| PyTorch fp32, MiniLM-L6, batch 128, seq 32 | 300–800 /s | 2–6 min |
| ONNX int8, MiniLM-L6, batch 128, seq 32 | **1,000–2,500 /s** | **40–100 s** |
| T4 GPU, fp16, batch 256 | 5,000–15,000 /s | 7–20 s |
| **Static embedding model (see below)** | **10⁵ /s** | **~1 s** |

**Do not put these in your report. Run this and put the real numbers in:**
```
python -c "..."  # time model.encode(descriptions[:10000], batch_size=128) on the demo laptop
```
Ten minutes of work, and it converts four rows of guesses into measured evidence, which is exactly what brief §26/§27 demand.

### 6.3 The static-embedding option — worth a serious look

`[VERIFIED]` https://huggingface.co/blog/static-embeddings :
- `sentence-transformers/static-retrieval-mrl-en-v1` is **397× faster on CPU** and 24× on GPU than all-MiniLM-L6-v2, achieving **87.4% of all-mpnet-base-v2's NanoBEIR performance** (NDCG@10 0.5032).
- Multilingual sibling `static-similarity-mrl-multilingual-v1`: ~125× faster on CPU vs multilingual-e5-small, retaining 92.3% (STS) / 95.5% (pair classification) / 86.5% (classification).
- Both are 1024-dim with **Matryoshka truncation to 512/256/128/64/32**.
- Benchmarks on an i7-13700K + RTX 3090 + 32 GB — i.e. consumer hardware comparable to a good laptop.
- Related: **Model2Vec** distils any sentence transformer into a static model, reported up to 500× faster / 50× smaller, distillable in about a minute on CPU. `[VERIFIED, secondary]` https://github.com/MinishLab/model2vec

**`[JUDGMENT]` — and this is a real critique the ML track needs:** static embedding models are essentially **weighted bags of token embeddings with no attention**. They are **order-insensitive**. `M10 X 50` and `M50 X 10` may produce near-identical vectors. For a domain where token order encodes engineering meaning, that is a genuine limitation.

**But it may not matter, and here is why:** in your architecture, the embedding's job is *candidate retrieval* (recall), not the final decision. Order-sensitive discrimination is supposed to come from the **structured attribute comparison stage** (`length_mm=50` vs `length_mm=75`), which is deterministic and exact. If retrieval recall@100 with static embeddings is within a point or two of MiniLM's — **and you should measure exactly that** — then you get a ~100× speedup and a "we embed the full national corpus in under a minute on a laptop, no GPU" claim, which is a *much* better scalability story than a GPU requirement.

**Concrete action for the ML track: make static-vs-transformer a measured ablation row in your evaluation table (recall@50, recall@100, embed throughput). Either result is a good slide.** Fine-tuning still argues for a small transformer (you can fine-tune a static model too, but the contrastive-learning story is stronger with an encoder). My guess is you end up fine-tuning a MiniLM/BGE-small and keeping the static model as the "cold-start / on-prem-CPU-only" tier — but *guess* is the operative word; measure it.

### 6.4 Cross-encoder budget

Cross-encoders are ~K× more expensive than bi-encoders per query (one forward pass per pair). `[CALC]` At K=25 candidates and an estimated 300–800 pairs/s for a MiniLM-class cross-encoder on CPU (`[JUDGMENT]`, measure it): **31–83 ms per source record** for interactive use — perfectly fine. For a 100k batch: **~1–2.5 hours.** That is why §3.4 says pre-ingest the corpus.

**Design consequence:** the cross-encoder runs (a) interactively when a reviewer opens a record, and (b) in the batch job. Cache its output in a `match_candidate` table keyed by `(source_id, target_id, model_version)` so the interactive path is usually a cache hit. **Pre-warm this cache for the demo records before you walk on stage.**

---

## 7. Deployment — the demo that must not fail

### 7.1 Network risk at an SIH venue

`[JUDGMENT], and I want to be emphatic:` **Venue Wi-Fi at a hackathon final is a hostile network.** Hundreds of teams, hundreds of laptops, captive portals, saturated uplinks, and IT policies that block outbound ports. I have no citation for SIH specifically and will not fabricate one — but **assume it is unusable and you lose nothing; assume it works and you can lose everything.**

Concrete failure modes, all of which have killed demos:
- Captive portal re-auth mid-presentation.
- DNS resolution failure for your cloud host.
- A free-tier service cold-starting because nobody hit it in 15 minutes.
- `huggingface.co` unreachable when your code tries to download a model on first use.
- Google Fonts / a CDN script blocked → your UI renders unstyled.

### 7.2 The free tiers — verified, and mostly disqualified

| Platform | Verified facts | Verdict as demo primary |
|---|---|---|
| **Render** | Free web services **spin down after 15 min idle** (reduced from 30 in Sept 2025); spin-up takes **~1 minute**. 750 free instance-hours/workspace/month. **Free Postgres is capped at 1 GB and EXPIRES 30 DAYS after creation**, then a 14-day grace period before deletion. `[VERIFIED, secondary]` https://unanswered.io/guide/render-free-tier-details , https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026 | **DISQUALIFIED.** A 1-minute cold start on stage is a demo-ending event. The 30-day DB expiry will silently delete your seeded data at the worst possible moment. |
| **Neon** | Free: **0.5 GB storage/project**, **100 CU-hours/project**, up to 100 projects/org, **compute suspends after 5 min idle** (scale-to-zero on by default). pgvector included. `[VERIFIED]` https://neon.com/pricing | Storage is *just* enough for a 100k-row demo `[CALC: ~78 MB halfvec + ~100 MB index + text ≈ 250–350 MB]` but the **5-minute autosuspend** is the same cold-start problem. Usable as a *backup mirror* if you keep it warm with a cron ping. |
| **Hugging Face Spaces** | **CPU Basic (2 vCPU / 16 GB / 50 GB non-persistent) is $0/hr, BUT: "Gradio and Docker Spaces run on compute and require a paid plan to create: PRO for personal accounts, Team or Enterprise for organizations."** Static Spaces remain free. Free personal accounts may host up to 2 Gradio Spaces **on ZeroGPU only**. Free hardware sleeps after **48 h** idle. Outbound network restricted to ports 80/443/8080. `[VERIFIED]` https://huggingface.co/docs/hub/en/spaces-overview | **DISQUALIFIED as a free option.** ⚠️ **This is a change from what most people assume — if anyone on the team was planning "we'll just host it on HF Spaces for free", that plan is dead unless someone buys PRO.** |
| **Fly.io / Railway** | Pricing/limits change frequently. **UNVERIFIED this session — check https://fly.io/docs/about/pricing/ and https://railway.com/pricing before relying on either.** | Not recommended as primary regardless (same cold-start class of risk). |
| **Vercel + Neon/Supabase** | Only relevant if you chose Next.js, which §4.1 says not to. | N/A. |
| **A single small VPS** (Hetzner CX-series, DigitalOcean, Oracle Cloud Always-Free ARM) | **UNVERIFIED pricing this session.** Hetzner's cheapest shared-vCPU x86 instance has historically been in the €4–5/month range — **verify at https://www.hetzner.com/cloud before quoting.** Oracle's Always-Free ARM tier (4 OCPU / 24 GB) is generous but availability-constrained. | **This is the right cloud option** — always-on, no cold start, full root, you control everything. But still not the *primary*. |

### 7.3 THE RECOMMENDED DEMO TOPOLOGY

`[JUDGMENT], and this is the recommendation I'd defend hardest:`

```
┌─────────────────────────────────────────────────────────────┐
│ PRIMARY:  Demo Laptop A  —  ZERO NETWORK DEPENDENCY         │
│                                                             │
│   docker compose up                                         │
│     ├── db      : pgvector/pgvector:pg18@sha256:...          │
│     │             (seeded volume, pre-built HNSW index)     │
│     ├── api     : FastAPI + worker + ONNX model BAKED IN    │
│     │             + built React SPA served via StaticFiles  │
│     └── (that's it. two containers.)                        │
│                                                             │
│   Browser → http://localhost:8000 → everything              │
│   Wi-Fi: TURNED OFF. Airplane mode. On purpose.             │
└─────────────────────────────────────────────────────────────┘
        │
        ├── HOT SPARE: Laptop B, byte-identical images + volume,
        │              already running, browser already open on
        │              the first screen. Swap the HDMI cable.
        │
        └── MIRROR: one always-on VPS at a memorable URL, kept
                    warm, used ONLY to answer "is it deployed?"
                    Never the thing on screen.
```

**The rules that make this work:**

1. **Bake the model weights into the Docker image.** `COPY ./models /app/models`, and set `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` in the Dockerfile. If your code can reach `huggingface.co` at runtime, it *will* try to, and one day it will fail. **Test this by running the whole stack with the network disconnected. If it works, you are done. If it does not, you just found your demo-day bug in week 6 instead of on stage.**
2. **No external assets in the frontend.** Self-host fonts (`@fontsource/*` npm packages). No CDN `<script>`. No Google Analytics. No remote images. Vite bundles everything; verify with the browser devtools Network tab in airplane mode — **zero requests to any host that is not localhost.**
3. **Pin image digests, not tags.** `pgvector/pgvector:pg18@sha256:...`.
4. **Export the images.** `docker save` both images to a `.tar` on two USB drives. If Docker Hub is unreachable and Laptop B needs a rebuild, you can `docker load`.
5. **`docker compose up` must be the entire runbook.** Write it on an index card. Under stage lights, at 9:55 a.m., nobody remembers a 6-step sequence.
6. **Practise the full cold start**, timed, at least five times, including the "it crashed, restart it" path.

**Why not just the VPS?** Because if the venue network drops, a laptop-hosted demo does not care, and a VPS-hosted demo is over. The asymmetry is total. The VPS exists so you can say "yes, it's deployed, here's the URL" — which is a slide, not a demo.

### 7.4 The offline fallback below the fallback

**Record a 3–4 minute screen capture of the perfect run, with narration, and keep it on both laptops and a phone.** `[JUDGMENT]` If everything is on fire, you play it and talk over it. Judges have seen this; nobody is impressed, but you finish your slot, which is infinitely better than 4 minutes of `docker compose logs`. It costs one afternoon. Do it in week 8.

---

## 8. Graph: do you need a graph database?

**VERDICT: NO. `[JUDGMENT], high confidence. Cut Neo4j, Memgraph, and Apache AGE.`**

The argument, in order:

1. **Your traversals are 2–3 hops, not 8.** `unified_material → cpse_mapping → cpse` and `unified_material → supplier`. These are joins. Calling them "graph traversal" does not change the query plan.
2. **A recursive CTE handles the deep cases fine.** Your only genuinely recursive structure is category hierarchy and merge lineage ("this unified material absorbed those three, one of which had earlier absorbed two others"). A `WITH RECURSIVE` over a `material_link(parent_id, child_id, link_type, decided_at)` table is ~15 lines and indexes normally.
3. **A second database means a second source of truth.** Your approvals are transactional. If a merge commits in Postgres and the Neo4j write fails, your graph screen lies. Fixing that properly means CDC or an outbox pattern — **a week of work you do not have, to solve a problem you created.**
4. **Apache AGE is the tempting middle ground and I still say no.** It genuinely supports PG 11–18 and added RLS support in a Jan 2026 release; the team is finalising PG18 as master. `[VERIFIED, secondary]` https://github.com/apache/age/discussions/2305 , https://age.apache.org/release-notes/ . But: you must build a custom Postgres image with both AGE and pgvector; you introduce openCypher as a second query language nobody on the team knows; and AGE's PG-version support has historically lagged (there are open issues titled "PostgreSQL 17 not supported" and "Support: PostgreSQL 18"). **The moment your demo depends on an extension whose PG18 support is described as "being finalised", you have taken a risk with no upside.**
5. **The user-visible product is a graph *visualisation*, not a graph *database*.** Nobody in the room can tell which backend produced the JSON that Cytoscape rendered.

**What to build instead:**

```sql
CREATE TABLE material_link (
  src_id     uuid NOT NULL,
  dst_id     uuid NOT NULL,
  link_type  text NOT NULL,   -- 'mapped_to'|'merged_into'|'equivalent'|'supplied_by'|'variant_of'
  confidence numeric,
  created_by text,            -- 'model:v3'|'user:1042'
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (src_id, dst_id, link_type)
);
CREATE INDEX ON material_link (dst_id, link_type);
```
Plus one endpoint `GET /graph/ego/{id}?depth=2&limit=300` returning `{nodes:[{id,label,type,x,y}], edges:[{source,target,type,weight}]}` — Cytoscape's native shape. Depth-2 is a two-level `WITH RECURSIVE` with a `LIMIT`.

**One legitimate graph-flavoured feature worth building:** connected components over confirmed-duplicate edges, to detect **transitive duplicate clusters** (A≈B, B≈C, but A vs C was never scored). This is genuinely valuable, is a real graph algorithm, and is one recursive CTE or a 10-line union-find in Python over the edge list. **That is your "graph intelligence" claim, and it is honest.** Present *that*, not a hairball.

---

## 9. Auth, RBAC, and audit

### 9.1 Auth — what to build

`[JUDGMENT]` Six roles are specified (brief §22). That is a small, closed set. **You need ~200 lines of code, not an identity platform.**

| Option | Verdict |
|---|---|
| **Hand-rolled: `PyJWT` + `passlib[argon2]` + FastAPI dependencies** | **RECOMMENDED.** Full control, no framework to fight, trivially explainable in a viva. |
| **FastAPI-Users** | Reasonable alternative. Actively maintained (updated 2026-07-20), FastAPI-native, async, SQLAlchemy support, JWT + cookie strategies, OAuth2 providers built in. `[VERIFIED, secondary]` https://workos.com/blog/top-authentication-solutions-fastapi-2026 . Cost: you inherit its user model and its opinions about registration flows you do not want. |
| **Authlib** | Only if you must integrate a real OIDC provider (NIC/Parichay-style SSO). **Do not build this for the prototype — name it as the integration path.** |
| **Keycloak** | **CUT.** A JVM identity server, a realm to configure, another container, another failure point. For six hardcoded roles this is absurd. |
| **Supabase Auth** | **CUT.** Ties you to Supabase and to network access. Contradicts §7.3. |

**⚠️ `python-jose` — do not use it.** FastAPI's own documentation moved to **PyJWT**. `[VERIFIED, secondary]` https://workos.com/blog/top-authentication-solutions-fastapi-2026 . `python-jose` has had unmaintained periods and known advisories. Use `PyJWT`. `[ASSUMPTION on the CVE specifics — verify at https://github.com/advisories?query=python-jose if you want to cite it.]`

**JWT vs sessions.** `[JUDGMENT]` For a single-origin app where the SPA is served by the same FastAPI process (§4.1), **sessions in an httpOnly, SameSite=Strict cookie are simpler and safer than JWT in localStorage** — no XSS token exfiltration, trivial revocation (delete the row), and revocation is something an *auditor* will ask about in a government context. But your API layer (brief §23) will want bearer tokens for machine-to-machine. **Do both: cookie session for the browser UI, and separate API keys / short-lived service JWTs for ERP integration.** Say this explicitly in the security section — the fact that you distinguished the two cases is itself the sophisticated answer.

**RBAC implementation:** a `permission` enum, a `role_permission` table, one `require(perm)` FastAPI dependency. **Enforce authorisation server-side on every endpoint.** Hiding a button in React is not access control, and a judge who knows security will ask.

### 9.2 Audit — and the blockchain question

**Brief §19 asks whether cryptographically verifiable audit is "ACTUALLY useful." Here is a straight answer.**

**Layer 1 — the append-only table. This is where the real value is.**

```sql
CREATE TABLE audit_log (
  seq          bigserial PRIMARY KEY,
  ts           timestamptz NOT NULL DEFAULT clock_timestamp(),
  actor        text NOT NULL,
  actor_role   text NOT NULL,
  action       text NOT NULL,           -- 'match.approve'|'match.reject'|'merge'|'unmerge'|...
  entity_type  text NOT NULL,
  entity_id    uuid NOT NULL,
  before       jsonb,                    -- from RETURNING old.*
  after        jsonb,                    -- from RETURNING new.*
  model_version text,                    -- REQUIRED for AI decisions
  ai_confidence numeric,
  ai_explanation jsonb,
  request_id   uuid,
  prev_hash    bytea,
  row_hash     bytea NOT NULL
);
```

**The control that actually makes it append-only is a GRANT, not a hash:**
```sql
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_user;
GRANT INSERT, SELECT ON audit_log TO app_user;
```
Combine with a `BEFORE UPDATE OR DELETE` trigger that raises an exception, so even a mistaken migration cannot mutate history. **This is the honest, high-value, ten-minute control. Ship it.**

**Layer 2 — hash chaining.** `row_hash = sha256(prev_hash || canonical_json(row_without_hashes))`. Compute it in a `BEFORE INSERT` trigger. Cost: ~30 lines. Benefit: **any modification or deletion of a historical row breaks the chain and is detectable by re-walking it.** A `/audit/verify` endpoint that re-walks the chain and reports "12,481 entries verified, chain intact" is a genuinely good 15 seconds of demo.

**Be precise about what this does and does not prove**, because a sharp judge will probe it:
> Hash chaining gives **tamper-evidence against a party who can modify rows but cannot recompute and republish the whole chain.** An attacker with full DB write access *can* rewrite every subsequent hash. The chain becomes meaningful only when the head hash is periodically **anchored** somewhere the DBA does not control — printed in a daily compliance report, emailed to an auditor, signed with a key held outside the DB, or written to append-only object storage (S3 Object Lock / WORM).

**Recommend: hash chain + a daily signed anchor.** That is a complete, honest, government-appropriate story.

**Layer 3 — blockchain. `[JUDGMENT]: THEATRE. CUT IT.`**

Say this out loud to your team, because someone will suggest it:
- A blockchain solves **Byzantine agreement among mutually distrusting parties with no common authority.** CPSEs are all under a common ministry. There *is* a trusted authority. The problem the technology solves does not exist here.
- A "private/permissioned blockchain" run by one operator is a hash-chained append-only log with extra containers and a consensus protocol you do not need — **exactly Layer 2, plus operational risk.**
- It costs you: Hyperledger/Fabric or an EVM node in your compose file, chaincode, wallets, gas or ordering config, and a new class of demo-day failure. **Week(s) of effort.**
- It buys you: one bullet on a slide.
- **And it is a liability.** If a technically strong judge asks "what is your consensus mechanism and who are the validators?", the honest answer exposes that it is decorative. **You will lose more credibility than the bullet gains.**

**The winning move is to raise and dismiss it yourself.** Put one slide up: *"We evaluated blockchain for audit integrity and rejected it. CPSEs share a trust anchor, so Byzantine consensus is unnecessary. We implement hash-chained append-only audit with external anchoring, which provides equivalent tamper-evidence at a fraction of the operational cost."* **That single slide will impress a serious judge more than an actual blockchain would.** It demonstrates engineering judgment, which is the rarest thing in the room.

**`pgaudit`:** an extension that logs statements to the Postgres server log at the session/object level. `[ASSUMPTION on current version/PG18 support — verify at https://github.com/pgaudit/pgaudit before including it.]` `[JUDGMENT]` It answers "what SQL ran", not "who approved what and why". **Your application-level `audit_log` is the one that matters for this problem. Mention pgaudit as a defence-in-depth item in the security architecture; do not spend prototype time on it.**

**Temporal tables / `system_versioning`:** Postgres has no built-in SQL:2011 temporal tables. Options are the `temporal_tables` extension or a hand-rolled history table via triggers. `[JUDGMENT]` **You do not need general row-versioning — you need decision-level audit, which is what `audit_log` is. Skip it.**

---

## 10. Observability and demo reliability

`[JUDGMENT]` throughout this section. Ruthlessly scoped: this is about *not losing*, not about production SRE.

### 10.1 Deterministic, seeded demo data

- **One seed script, one fixed RNG seed, checked into git.** `random.seed(42)`, `numpy.random.seed(42)`. Every synthetic variant, every "AI decision" timestamp, every demo user must be reproducible byte-for-byte.
- **Freeze the model.** Pin the model version, the ONNX file's SHA-256, and the exact thresholds. Store `model_version` on every stored prediction so a re-run cannot silently change what the reviewer sees.
- **Pin the demo clock.** If your dashboard says "last 30 days", seed the data relative to a fixed `DEMO_EPOCH` env var, not `now()`, or your charts will drift empty over time.
- **Label demo data in the UI.** The brief demands this twice (§10, §18). One persistent badge: `DEMO DATASET — synthetic + public-source records; figures are illustrative`. **This *increases* credibility. Judges have seen a hundred teams quote fabricated crore-value savings; a team that visibly refuses to is memorable.**

### 10.2 Snapshot / restore between demo runs

**The best trick in this document, and it is three lines `[JUDGMENT]`:** use a Postgres **template database.**

```sql
-- built once, during image build / seed:
CREATE DATABASE nmi_seed TEMPLATE template0;  -- then load everything into it

-- reset, in < 2 seconds even at 100k rows:
DROP DATABASE IF EXISTS nmi WITH (FORCE);     -- PG13+ FORCE kills connections
CREATE DATABASE nmi TEMPLATE nmi_seed;
```
`CREATE DATABASE ... TEMPLATE` is a **file-level copy** — it does not replay a dump, does not re-run migrations, and **does not rebuild the HNSW index.** A `pg_restore` of the same data would take minutes and rebuild indexes. This is the difference between "we can reset between judging panels" and "we can't."

Wire it to a `POST /admin/demo/reset` endpoint behind a role check + a confirm dialog, **and hide it behind an env flag so it cannot exist in a non-demo build.** Practise using it.

Alternative, if you prefer: snapshot the Docker volume (`docker run --rm -v pgdata:/v -v $PWD:/b alpine tar czf /b/pgdata.tgz /v` with the DB stopped). Slower, but bulletproof and portable to the spare laptop.

### 10.3 Pre-warmed caches

Postgres reads from disk on a cold start and your first query after `docker compose up` will be the slowest one you ever run — on stage, in front of everyone.

- `CREATE EXTENSION pg_prewarm; SELECT pg_prewarm('idx_mr_emb');` on the vector index and the hot tables, in an init hook.
- **Set `shared_buffers` to ~25% of the laptop's RAM** (default 128 MB is absurd for a demo box). On 16 GB: `shared_buffers=4GB`, `work_mem=64MB`, `effective_cache_size=8GB`.
- **Warm the application:** a startup task that loads the ONNX session and runs one dummy `encode(["warmup"])`. First-call ORT graph optimisation is not free.
- **Warm the browser:** open every demo screen once before you present, so TanStack Query has cached and every lazy chunk is loaded.
- **Pre-compute the demo path**: the specific `SS HEX BOLT M10 X 50` record's candidates, its cross-encoder scores, its explanation payload, and its graph layout should all already be in the DB. **Nothing on the golden path should be computed for the first time in front of a judge.**

### 10.4 Logging and health

- `structlog` → JSON to stdout, with a `request_id` bound per request and propagated into `audit_log.request_id`. When something breaks mid-demo, you grep one id.
- `GET /health` returning `{db: ok, model_loaded: true, worker_heartbeat_age_s: 3}`. Put a tiny status dot in the UI header. It is 20 lines and it looks like a real product.
- **`pg_stat_statements`** enabled from day one. When a screen is slow in week 8, this tells you which query in 30 seconds.
- **OpenTelemetry / Jaeger / Prometheus / Grafana: CUT.** Distributed tracing for a two-container app is cosplay. *One* exception with a real cost/benefit: if you want a "system monitoring" screenshot for the slide deck, Grafana + `postgres_exporter` is about 90 minutes of compose config. Cheap theatre, clearly labelled as such, and only in week 9 if you are ahead. **You will not be ahead.**

### 10.5 Testing that pays for itself

Given 6–10 weeks part-time, do not chase coverage. Write exactly these:
1. **Golden-file tests on the normaliser.** ~50 real messy input strings → expected normalised output + extracted attributes. This is where regressions hurt most and are hardest to spot by eye.
2. **One end-to-end test**: upload fixture CSV → job completes → expected N candidates → approve one → unified master has the mapping → audit chain verifies. If this passes, your demo works.
3. **A `pytest` fixture using the template-database trick** so each test gets a clean seeded DB in ~1 second.

---

## 11. Consolidated stack (copy this into the Phase 0 approval doc)

```
LAYER          CHOICE                                    WHY (one line)
─────────────────────────────────────────────────────────────────────────────
DB             PostgreSQL 18.6                           uuidv7, RETURNING old/new
Vector         pgvector 0.8.6, halfvec(d), HNSW m=16     one DB, no sync layer
Lexical        tsvector/GIN ('simple') + pg_trgm/GIN     free, adequate; RRF-fused
Fusion         Reciprocal Rank Fusion, k=60              one hyperparameter, and it's flat
Attributes     JSONB (jsonb_path_ops) + promoted numerics gated fields must be typed
Tenancy        RLS + SET LOCAL in a per-request txn      policy, not app-layer WHERE
Backend        FastAPI + SQLAlchemy 2.0 async + Alembic  no SQLModel
Validation     Pydantic v2                               separate from ORM models
Jobs           own ingest_job table + FOR UPDATE SKIP LOCKED  you need the table anyway
Realtime       Server-Sent Events                        no WebSocket lifecycle
Frontend       Vite + React 19 + TS + TanStack Router/Query   static build, no Node in prod
UI kit         shadcn/ui (Radix+Tailwind)                own the code; a11y free
Tables         @tanstack/react-table ^8  ← PIN IT        v9 broke the API in Aug 2026
Virtual        @tanstack/react-virtual                   >200 rows
Charts         Recharts                                  sufficient; visx/D3 cut
Graph          Cytoscape.js, preset layout, ≤300 nodes   layouts precomputed server-side
ETL            Polars (or pandas+pyarrow) + calamine     Spark is cut, permanently
Embedding      ONNX Runtime int8, in-worker, batch 128   +static-embedding ablation
Auth           PyJWT + argon2 + httpOnly session cookie  NOT python-jose, NOT Keycloak
Audit          append-only + GRANT + hash chain + anchor NOT blockchain
Container      docker compose, 2 services, pinned digests one command runbook
Demo           localhost on Laptop A, Wi-Fi OFF          hot spare + recorded video
```

---

## 12. Things in the brief this research contradicts or qualifies

1. **§24 lists Redis.** You do not need it. The queue is Postgres; caching is Postgres + TanStack Query. Redis is a third container and a third failure mode for zero demonstrated benefit at this scale. **Add it only if you measure a cache-miss problem, which you will not.**
2. **§24 lists FAISS *and* pgvector *and* Qdrant *and* Elasticsearch.** Pick one: pgvector. FAISS is worth keeping in the *offline ML notebooks* for fast experimentation over an in-memory index during evaluation sweeps — that is a legitimate, separate use. It should not be in the serving path.
3. **§30's demo sketch has you upload three CPSE datasets live and find "thousands of duplicates" on stage.** Arithmetic (§3.4) says this takes minutes to hours. **Restructure: pre-ingest the baseline, live-upload a small delta.** This is the highest-priority change to the demo plan.
4. **§16 asks whether to recommend graph technology.** The answer is no, and the reasoning (§8) is worth a slide of its own.
5. **§19's blockchain question**: no, and the *refusal* is a stronger asset than the implementation.
6. **§25 mentions "distributed processing if necessary."** It is not necessary. Say so, with the scale-out path named but unbuilt.
7. **The brief's implied "cloud demo" assumption** (§24 "Deployment: Docker, cloud, local") should be inverted: **local is primary, cloud is the backup.** Free tiers are worse than they were — HF Spaces now requires a paid plan for Docker/Gradio Spaces, and Render's free Postgres deletes itself after 30 days.

---

## 13. Open items a later agent must resolve

| # | Item | How to close it |
|---|---|---|
| 1 | Real HNSW build time & index size at 100k/1M on the **actual demo laptop** | Load synthetic data, `\timing`, `pg_relation_size()`. 1 hour. |
| 2 | Real embedding throughput (torch vs ONNX vs ONNX-int8 vs static) on the demo laptop | Time `encode()` on 10k real descriptions at batch 128, seq 32. 1 hour. |
| 3 | `ef_search` recall/latency curve | Sweep 40/64/100/200 against the labelled eval set. Goes straight into the eval deck. |
| 4 | Whether static embeddings hold retrieval recall on **this** domain | Ablation row: recall@50 / recall@100, static vs fine-tuned MiniLM. |
| 5 | Fly.io / Railway current free-tier limits | UNVERIFIED — check https://fly.io/docs/about/pricing/ , https://railway.com/pricing |
| 6 | VPS pricing (Hetzner / Oracle Always-Free ARM availability) | UNVERIFIED — check https://www.hetzner.com/cloud |
| 7 | `pgaudit` current version / PG18 support | UNVERIFIED — check https://github.com/pgaudit/pgaudit |
| 8 | The exact sbert ONNX/OpenVINO speedup figures (1.35× / 1.24× / 3.23×) | Retrieved via search snippet; **open https://sbert.net/docs/sentence_transformer/usage/efficiency.html directly to confirm before quoting.** |
| 9 | Cytoscape.js behaviour at 300 / 2,000 nodes on the demo laptop | Build the fixture in week 3, not week 9. |
| 10 | Whether `pg_search` (ParadeDB) is needed | Only after lexical recall@100 is measured against semantic recall@100. |
