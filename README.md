# SIH26099 — National Material Code Harmonization

Prototype for Smart India Hackathon 2026 problem **SIH26099**
(Ministry of Petroleum & Natural Gas / Chennai Petroleum Corporation Limited).

**Phase 0 plan:** `docs/SIH26099-Phase0-Plan.pdf` — approved. Read it before contributing.

## Core design constraint

Semantic similarity proposes candidates. **Structured attributes decide identity.**
A mismatch on a discriminating attribute is a hard veto, not a score penalty.
`M10x50` vs `M10x75` must be structurally impossible to call a duplicate.

## Data

No dataset is committed. Everything is fetched by `scripts/`, and every source's
licence and provenance is recorded in `docs/DATA_PROVENANCE.md`.

## Setup

    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python scripts/fetch_flis.py --small
