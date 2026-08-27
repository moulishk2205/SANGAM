"""
HTTP surface over the matching engine.

Deliberately thin. Every number this returns is computed by `MatchingEngine`;
there is no scoring, no ranking and no explanation logic here. If a value
appears in the UI, it came out of the engine, which is the only way the
"no mocked AI responses" rule can actually be enforced rather than asserted.

    uvicorn src.nmc.api:app --port 8000
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .demo.corpus import build_corpus
from .types import MaterialRecord
from .match.engine import MODEL_VERSION, MatchingEngine
from .relate import build_map

# Held at module scope: the index is expensive to build and must be built once,
# at startup, not per request.
_engine: MatchingEngine | None = None
_truth: dict[str, str] = {}
_canonical: dict[str, dict] = {}      # nmc id -> canonical record
_by_record: dict[str, str] = {}       # source record id -> nmc id
_ready_ms = 0.0


def _build_canonical(engine: MatchingEngine, truth: dict[str, str]) -> None:
    """
    Group source records into canonical materials.

    Two records belong to the same canonical material when they were rendered
    from the same specification, so the grouping is correct by construction
    rather than asserted. The NMC id is derived deterministically from the spec
    key: the same corpus always mints the same identifiers, which is what makes
    a demo repeatable and a link shareable.

    The identifier is opaque on purpose. A significant code that encodes group
    and dimension breaks the moment an item is reclassified, and it encodes a
    taxonomy that will be wrong in five years.
    """
    groups: dict[str, list] = {}
    for rec in engine.records:
        groups.setdefault(truth[rec.id], []).append(rec)

    for key, recs in sorted(groups.items()):
        seq = 18426 + sum(ord(c) for c in key) % 60000
        nmc = f"NMC-{seq:08d}"
        while nmc in _canonical:              # collision on the derived seq
            seq += 1
            nmc = f"NMC-{seq:08d}"
        head = engine.prepare(recs[0])
        _canonical[nmc] = {
            "nmc_id": nmc,
            "item_name": head.item_name or "UNCLASSIFIED",
            "canonical_text": head.normalised,
            "attributes": [
                {"code": c, "label": c.replace("_", " ").title(), "value": str(a.value)}
                for c, a in head.attributes.items() if a.known
            ],
            "sources": [
                {"record_id": r.id, "org": r.org, "org_code": r.org_code,
                 "description": r.raw_description, "provenance": r.provenance}
                for r in recs
            ],
            "source_count": len(recs),
            "org_count": len({r.org for r in recs}),
        }
        for r in recs:
            _by_record[r.id] = nmc


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _engine, _truth, _ready_ms
    t0 = time.perf_counter()
    records, truth = build_corpus(limit_specs=600, variants_per_spec=3)
    engine = MatchingEngine(use_embeddings=True)
    engine.index(records)
    _engine, _truth = engine, truth
    _build_canonical(engine, truth)
    _ready_ms = (time.perf_counter() - t0) * 1000
    print(f"[api] indexed {len(records)} records into {len(_canonical)} canonical "
          f"materials in {_ready_ms:,.0f} ms "
          f"(dense channel: {'on' if engine.retriever.embeddings_enabled else 'off'})")
    yield
    _engine = None


app = FastAPI(title="SANGAM — Material Intelligence (SIH26099)", lifespan=lifespan)

# The frontend is served from a different origin in development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174",
                   "http://localhost:4173", "http://localhost:4174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def engine() -> MatchingEngine:
    if _engine is None:
        raise HTTPException(503, "engine still indexing")
    return _engine


class MatchRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    top_k: int = Field(default=5, ge=1, le=20)


class MapRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    # Capped at 60. Beyond that the projection stops being separable on screen
    # and the neighbour matrix stops being free; refusing is better than
    # degrading quietly into an unreadable cloud.
    top_k: int = Field(default=24, ge=4, le=60)


@app.get("/api/health")
def health() -> dict:
    e = _engine
    return {
        "ready": e is not None,
        "records": len(e.records) if e else 0,
        "dense_channel": bool(e and e.retriever.embeddings_enabled),
        "model_version": MODEL_VERSION,
        "index_build_ms": round(_ready_ms),
        # Stated at the source so the UI cannot quietly imply otherwise.
        "corpus": "synthetic, construction-derived",
        "calibrated": False,
    }


@app.post("/api/match")
def match(req: MatchRequest) -> dict:
    """
    Analyse a description and return ranked candidates with full evidence.

    Timings are measured around the real call, not estimated, because the
    honest headline for this engine is how fast it is.
    """
    eng = engine()

    t0 = time.perf_counter()
    probe, results = eng.check_before_create(req.description, top_k=req.top_k)
    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "query": req.description,
        "normalised": probe.normalised,
        "item_name": probe.item_name or None,
        "attributes": [
            {
                "code": code,
                "value": str(a.value),
                "source": a.source,
                "raw": a.raw,
                "inferred_unit": a.inferred_unit or None,
            }
            for code, a in probe.attributes.items()
            if a.known
        ],
        "candidates": [
            {
                **c.explanation.to_dict(),
                "org": c.record.org,
                "org_code": c.record.org_code,
                "record_id": c.record.id,
                "provenance": c.record.provenance,
                "nmc_id": _by_record.get(c.record.id),
            }
            for c in results
        ],
        "elapsed_ms": round(elapsed, 2),
        "model_version": MODEL_VERSION,
    }


@app.get("/api/material/{record_id}")
def material(record_id: str) -> dict:
    """One source record, with everything the engine extracted from it."""
    eng = engine()
    rec = eng.get(record_id)
    if rec is None:
        raise HTTPException(404, f"no record {record_id}")
    return {
        "id": rec.id,
        "org": rec.org,
        "org_code": rec.org_code,
        "raw_description": rec.raw_description,
        "normalised": rec.normalised,
        "item_name": rec.item_name or None,
        "provenance": rec.provenance,
        "attributes": [
            {"code": c, "value": str(a.value), "source": a.source, "raw": a.raw}
            for c, a in rec.attributes.items() if a.known
        ],
    }


# Example queries offered on the home screen.
#
# Each one is written the way a storekeeper would actually type it, and each
# exercises a different part of the pipeline. They are validated against the
# live index at startup rather than trusted: a sample that retrieves nothing is
# a worse demo than no sample at all, so `/api/samples` drops any entry whose
# item type the classifier cannot resolve.
_SAMPLES: list[dict] = [
    {"chip": "SS hex bolt", "query": "STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM",
     "note": "the long form — every word spelled out"},
    {"chip": "Same bolt, abbreviated", "query": "SS HEX BOLT M10 X 50",
     "note": "the same material, written the way it is actually typed"},
    {"chip": "Length near-miss", "query": "SS HEX BOLT M10 X 75",
     "note": "one critical attribute apart from the bolt above — watch the veto"},
    {"chip": "Carbon steel pipe", "query": "CARBON STEEL SEAMLESS PIPE 100MM NB SCH 40",
     "note": "bore and schedule both decide identity"},
    {"chip": "Pipe in inches", "query": "CS SEAMLESS PIPE 4 INCH SCH 40",
     "note": "NPS 4 is DN 100 — a designation, not a unit conversion"},
    {"chip": "Weld neck flange", "query": "CARBON STEEL WELD NECK FLANGE 150NB CLASS 300",
     "note": "flange type, bore and class are all critical"},
    {"chip": "Ball valve", "query": "STAINLESS STEEL BALL VALVE 2 INCH CLASS 150",
     "note": "a ball valve is not a gate valve of the same size"},
    {"chip": "Nut, not bolt", "query": "NUT HEX SS M10",
     "note": "same thread, same material, different item type"},
]


@app.get("/api/samples")
def samples() -> dict:
    """
    Seeded example queries for the demo, verified against the live corpus.

    Returned by the API rather than hard-coded in the UI so the examples are
    guaranteed to work against the index that is actually loaded, not against
    the one that existed when the UI was written.
    """
    eng = engine()
    usable = []
    for s in _SAMPLES:
        probe = eng.prepare(MaterialRecord(id="__sample__", raw_description=s["query"]))
        if probe.item_name:
            usable.append({**s, "item_name": probe.item_name})
    return {
        "samples": [s["query"] for s in usable],       # kept for existing callers
        "examples": usable,
        "corpus_size": len(eng.records),
        "organisations": sorted({r.org for r in eng.records if r.org}),
    }


@app.post("/api/visualization")
def visualization(req: MapRequest) -> dict:
    """
    The material relationship map.

    Runs the ordinary pipeline — the very same `check_before_create` the Analyse
    screen calls — and then describes the result as a graph. There is no second
    engine, no second scoring path and no cached layout: analyse a description
    here and on the Analyse screen and the two must agree, because they are one
    call.
    """
    return build_map(engine(), _by_record, req.description, top_k=req.top_k)


@app.get("/api/canonical")
def canonical_list(q: str = "", limit: int = 40) -> dict:
    """The standardized catalogue. Substring search over item name and text."""
    engine()
    needle = q.strip().upper()
    rows = [
        c for c in _canonical.values()
        if not needle
        or needle in c["canonical_text"].upper()
        or needle in c["item_name"].upper()
        or needle in c["nmc_id"]
    ]
    rows.sort(key=lambda c: (-c["source_count"], c["nmc_id"]))
    return {
        "total": len(_canonical),
        "matched": len(rows),
        "results": [
            {k: v for k, v in c.items() if k != "sources"} | {"orgs": sorted({s["org"] for s in c["sources"]})}
            for c in rows[:limit]
        ],
    }


@app.get("/api/canonical/{nmc_id}")
def canonical_detail(nmc_id: str) -> dict:
    """One canonical material with every source identity mapped to it."""
    engine()
    rec = _canonical.get(nmc_id.upper())
    if rec is None:
        raise HTTPException(404, f"no canonical material {nmc_id}")
    return rec


@app.get("/api/stats")
def stats() -> dict:
    """Headline counts for the home screen. Computed, never hard-coded."""
    eng = engine()
    multi = [c for c in _canonical.values() if c["org_count"] > 1]
    return {
        "source_records": len(eng.records),
        "canonical_materials": len(_canonical),
        "cross_org_materials": len(multi),
        "organisations": len({r.org for r in eng.records if r.org}),
        "collapse_ratio": round(len(eng.records) / max(len(_canonical), 1), 2),
    }
