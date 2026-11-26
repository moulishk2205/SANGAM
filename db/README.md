# Database

| File | What |
|---|---|
| [`schema.sql`](schema.sql) | DDL for all 12 tables, generated from [`src/nmc/db/models.py`](../src/nmc/db/models.py) |
| `sangam_seed.db` | A clean SQLite snapshot right after seeding — 1,810 source records, 610 canonical materials, 2,441 purchase lines, 5 demo users, **no sessions, no audit history** |

You do not need either to run SANGAM. On startup the API creates the schema and
seeds a fresh `sangam.db` in the repository root (see `lifespan` in
[`src/nmc/api.py`](../src/nmc/api.py)). The snapshot exists so the data model can be
browsed without running anything:

```bash
sqlite3 db/sangam_seed.db "select id, standard_description from canonical_materials limit 5;"
```

or opened in any SQLite browser.

To run the platform against the snapshot instead of a fresh seed:

```bash
cp db/sangam_seed.db sangam.db
```

To use PostgreSQL, install a driver (`pip install "psycopg[binary]"`) and set
`DATABASE_URL` — nothing in the schema is SQLite-specific:

```bash
export DATABASE_URL=postgresql+psycopg://user:pass@localhost/sangam
```

Demo accounts in the snapshot all use the published password `sangam-demo`.
They exist for a synthetic corpus and must never be reused anywhere real.
