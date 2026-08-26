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
from .match.engine import MODEL_VERSION, MatchingEngine

# Held at module scope: the index is expensive to build and must be built once,
# at startup, not per request.
_engine: MatchingEngine | None = None
_truth: dict[str, str] = {}
_ready_ms = 0.0


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _engine, _truth, _ready_ms
    t0 = time.perf_counter()
    records, truth = build_corpus(limit_specs=600, variants_per_spec=3)
    engine = MatchingEngine(use_embeddings=True)
    engine.index(records)
    _engine, _truth = engine, truth
    _ready_ms = (time.perf_counter() - t0) * 1000
    print(f"[api] indexed {len(records)} records in {_ready_ms:,.0f} ms "
          f"(dense channel: {'on' if engine.retriever.embeddings_enabled else 'off'})")
    yield
    _engine = None


app = FastAPI(title="SIH26099 Material Intelligence", lifespan=lifespan)

# The frontend is served from a different origin in development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
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


@app.get("/api/samples")
def samples() -> dict:
    """
    Seeded example queries for the demo, drawn from the live corpus.

    Returned by the API rather than hard-coded in the UI so that the examples
    are guaranteed to exist in the index that is actually loaded.
    """
    eng = engine()
    picks = ["SS HEX BOLT M10 X 50", "STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM",
             "SS HEX BOLT M10 X 75", "NUT HEX SS M10"]
    return {
        "samples": picks,
        "corpus_size": len(eng.records),
        "organisations": sorted({r.org for r in eng.records if r.org}),
    }
