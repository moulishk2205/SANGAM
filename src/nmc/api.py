"""
HTTP surface over the matching engine and the material master.

Deliberately thin. Every number this returns is computed by `MatchingEngine`,
and every mutation goes through `service`, which is the only place a decision
certificate is written. If a value appears in the UI it came out of one of those
two, which is how "no mocked AI" and "every decision is certified" stay
enforceable by reading two files rather than by trusting a claim.

WHERE THE DATA LIVES NOW

The corpus used to be regenerated into module-level dicts on every boot, so
nothing a user did survived a restart. It is now in the database. The retrieval
index is still built in memory at startup, but it is a derived cache over what
storage holds — not the source of truth. That distinction is what makes writes
possible at all.

    uvicorn src.nmc.api:app --port 8001
"""
from __future__ import annotations

import csv
import io
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as DbSession

from . import service
from .authz import (
    Denied, find_user_by_email, open_session, resolve_session, revoke_session,
    verify_password,
)
from .db.models import (
    CanonicalMaterial, Decision, IngestJob, ItemClassRule, JobStatus, Mapping,
    MappingStatus, Organisation, Role, SourceRecord, User, utcnow,
)
from .db.seed import seed
from .db.session import SessionLocal, describe, engine as db_engine, get_session
from .db.models import Base
from .match.engine import MODEL_VERSION, MatchingEngine
from .relate import build_map
from .types import MaterialRecord

SESSION_COOKIE = "sangam_session"

# The retrieval index. Expensive to build and rebuilt only at startup or after a
# reindex — a derived cache over the database, never the system of record.
_engine: MatchingEngine | None = None
_ready_ms = 0.0
_indexed = 0


def _load_index() -> None:
    """Build the in-memory index from what storage actually holds."""
    global _engine, _ready_ms, _indexed
    t0 = time.perf_counter()
    with SessionLocal() as db:
        rows = db.scalars(select(SourceRecord)).all()
        records = [
            MaterialRecord(id=r.id, raw_description=r.raw_description,
                           org=r.org_id, org_code=r.org_code, provenance=r.provenance)
            for r in rows
        ]
    eng = MatchingEngine(use_embeddings=True)
    eng.index(records)
    _engine, _indexed = eng, len(records)
    _ready_ms = (time.perf_counter() - t0) * 1000


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_all is a convenience for a fresh checkout; `alembic upgrade head`
    # is the real path and the one CI should use. Both converge on the same
    # schema, and create_all is a no-op once the migration has run.
    Base.metadata.create_all(bind=db_engine)
    with SessionLocal() as db:
        info = seed(db)
    _load_index()
    print(f"[api] storage {describe()['backend']} · indexed {_indexed:,} records "
          f"in {_ready_ms:,.0f} ms "
          f"(dense channel: {'on' if _engine and _engine.retriever.embeddings_enabled else 'off'})"
          + (f" · seeded {info.get('source_records', 0):,} records" if info.get("seeded") else ""))
    yield


app = FastAPI(title="SANGAM — Material Intelligence (SIH26099)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174",
                   "http://localhost:4173", "http://localhost:4174"],
    allow_credentials=True,   # the session cookie needs this
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── error taxonomy ─────────────────────────────────────────────────────────
# Every failure carries a machine-readable code and a sentence a person can act
# on. A bare 404 tells a reviewer nothing about what to do next.

def fail(status: int, code: str, message: str, **extra):
    raise HTTPException(status, {"code": code, "message": message, **extra})


@app.exception_handler(Denied)
async def _denied(_: Request, exc: Denied):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=403,
                        content={"code": "not_permitted", "message": exc.reason})


def matching_engine() -> MatchingEngine:
    if _engine is None:
        fail(503, "engine_indexing", "The engine is still building its index.")
    return _engine


# ── identity ───────────────────────────────────────────────────────────────

def current_user(request: Request, db: DbSession = Depends(get_session)) -> User:
    user = resolve_session(db, request.cookies.get(SESSION_COOKIE))
    if user is None:
        fail(401, "not_authenticated", "Sign in to continue.")
    return user


def optional_user(request: Request, db: DbSession = Depends(get_session)) -> User | None:
    return resolve_session(db, request.cookies.get(SESSION_COOKIE))


# WHAT IS PUBLIC, AND WHY SO LITTLE
#
# Exactly four endpoints answer without a session: the two auth verbs, `me`
# (which must be able to say "nobody"), and `health` (a liveness probe has to
# work before anyone signs in).
#
# Everything else — including the reads — requires one. The catalogue is
# another organisation's material master, the analyser is the engine itself,
# and the ledger is an internal audit record; none of those are public
# information. Gating only the UI would have left all of it answering on
# :8001 to anyone who knew the path, which is a curtain, not a control.


def _user_out(u: User, db: DbSession) -> dict:
    org = db.get(Organisation, u.org_id)
    return {
        "id": u.id, "email": u.email, "name": u.name, "role": u.role.value,
        "org_id": u.org_id, "org_name": org.name if org else u.org_id,
        "commodity_scope": u.commodity_scope or [],
        "class_certifications": u.class_certifications or [],
    }


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response, db: DbSession = Depends(get_session)) -> dict:
    user = find_user_by_email(db, req.email)
    # Same message either way: distinguishing "no such user" from "wrong
    # password" tells an attacker which half they got right.
    if user is None or not user.active or not verify_password(req.password, user.password_hash):
        fail(401, "bad_credentials", "That email and password do not match an account.")
    s = open_session(db, user)
    service.audit(db, actor=user, action="auth.login")
    response.set_cookie(SESSION_COOKIE, s.token, httponly=True, samesite="lax",
                        max_age=int((s.expires_at - utcnow()).total_seconds()))
    return {"user": _user_out(user, db), "expires_at": s.expires_at.isoformat()}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db: DbSession = Depends(get_session)) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        revoke_session(db, token)
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/auth/me")
def me(db: DbSession = Depends(get_session), user: User | None = Depends(optional_user)) -> dict:
    return {"user": _user_out(user, db) if user else None}


# ── health and figures ─────────────────────────────────────────────────────

@app.get("/api/health")
def health(db: DbSession = Depends(get_session)) -> dict:
    e = _engine
    return {
        "ready": e is not None,
        "records": _indexed,
        "dense_channel": bool(e and e.retriever.embeddings_enabled),
        "model_version": MODEL_VERSION,
        "index_build_ms": round(_ready_ms),
        "storage": describe(),
        "chain_head": service.chain_head(db),
        "corpus": "synthetic, construction-derived",
        "calibrated": bool(_engine and _engine.scorer is not None),
    }


@app.get("/api/stats")
def stats(db: DbSession = Depends(get_session),
          _u: User = Depends(current_user)) -> dict:
    c = service.counts(db)
    cross = db.scalar(
        select(func.count()).select_from(
            select(Mapping.canonical_id)
            .join(SourceRecord, SourceRecord.id == Mapping.source_record_id)
            .where(Mapping.status == MappingStatus.APPROVED)
            .group_by(Mapping.canonical_id)
            .having(func.count(func.distinct(SourceRecord.org_id)) > 1)
            .subquery()
        )
    ) or 0
    return {
        "source_records": c["source_records"],
        "canonical_materials": c["canonical_materials"],
        "cross_org_materials": cross,
        "organisations": c["organisations"],
        "collapse_ratio": round(c["source_records"] / max(c["canonical_materials"], 1), 2),
        "mappings_approved": c["mappings_approved"],
        "mappings_pending": c["mappings_pending"],
        "decisions": c["decisions"],
    }


# ── matching (unchanged behaviour, records now from storage) ───────────────

class MatchRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    top_k: int = Field(default=5, ge=1, le=20)


class MapRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    top_k: int = Field(default=24, ge=4, le=60)


def _canonical_for_record(db: DbSession, record_id: str) -> str | None:
    m = service.live_mapping(db, record_id)
    return m.canonical_id if m else None


@app.post("/api/match")
def match(req: MatchRequest, db: DbSession = Depends(get_session),
          _u: User = Depends(current_user)) -> dict:
    eng = matching_engine()
    t0 = time.perf_counter()
    probe, results = eng.check_before_create(req.description, top_k=req.top_k)
    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "query": req.description,
        "normalised": probe.normalised,
        "item_name": probe.item_name or None,
        "attributes": [
            {"code": code, "value": str(a.value), "source": a.source, "raw": a.raw,
             "inferred_unit": a.inferred_unit or None}
            for code, a in probe.attributes.items() if a.known
        ],
        "candidates": [
            {**c.explanation.to_dict(), "org": c.record.org, "org_code": c.record.org_code,
             "record_id": c.record.id, "provenance": c.record.provenance,
             "nmc_id": _canonical_for_record(db, c.record.id)}
            for c in results
        ],
        "elapsed_ms": round(elapsed, 2),
        "model_version": MODEL_VERSION,
        # Whether these scores are probabilities or ranking numbers. Per-candidate
        # too, but the UI needs it before it has a candidate to look at.
        "calibrated": bool(eng.scorer is not None),
    }


@app.post("/api/visualization")
def visualization(req: MapRequest, db: DbSession = Depends(get_session),
                  _u: User = Depends(current_user)) -> dict:
    eng = matching_engine()
    by_record = {
        r.source_record_id: r.canonical_id
        for r in db.scalars(select(Mapping).where(
            Mapping.status.in_([MappingStatus.PROPOSED, MappingStatus.APPROVED]),
            Mapping.effective_to.is_(None)))
    }
    return build_map(eng, by_record, req.description, top_k=req.top_k)


# ── catalogue ──────────────────────────────────────────────────────────────

@app.get("/api/canonical")
def canonical_list(
    q: str = "", limit: int = Query(default=40, ge=1, le=200),
    cursor: str | None = None, item_class: str | None = None,
    db: DbSession = Depends(get_session),
    _u: User = Depends(current_user),
) -> dict:
    """
    Cursor pagination, not offset.

    OFFSET re-scans everything it skips and silently shifts rows when a write
    lands mid-listing, which for a catalogue people page through while others
    are adjudicating means duplicates and gaps. The cursor is the last id seen.
    """
    stmt = select(CanonicalMaterial)
    needle = q.strip().upper()
    if needle:
        stmt = stmt.where(or_(
            func.upper(CanonicalMaterial.canonical_text).contains(needle),
            func.upper(CanonicalMaterial.item_name).contains(needle),
            CanonicalMaterial.id.contains(needle),
        ))
    if item_class:
        stmt = stmt.where(CanonicalMaterial.item_class == item_class)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    if cursor:
        stmt = stmt.where(CanonicalMaterial.id > cursor)

    rows = db.scalars(stmt.order_by(CanonicalMaterial.id).limit(limit + 1)).all()
    more = len(rows) > limit
    rows = rows[:limit]

    ids = [r.id for r in rows]
    counts: dict[str, tuple[int, set]] = {i: (0, set()) for i in ids}
    if ids:
        for cid, org in db.execute(
            select(Mapping.canonical_id, SourceRecord.org_id)
            .join(SourceRecord, SourceRecord.id == Mapping.source_record_id)
            .where(Mapping.canonical_id.in_(ids),
                   Mapping.status == MappingStatus.APPROVED)
        ):
            n, orgs = counts[cid]
            counts[cid] = (n + 1, orgs | {org})

    return {
        "total": db.scalar(select(func.count()).select_from(CanonicalMaterial)) or 0,
        "matched": total,
        "next_cursor": rows[-1].id if more and rows else None,
        "results": [
            {"nmc_id": r.id, "item_name": r.item_name, "canonical_text": r.canonical_text,
             "item_class": r.item_class,
             "attributes": [{"code": k, "label": k.replace("_", " ").title(), "value": v}
                            for k, v in (r.attributes or {}).items()],
             "source_count": counts[r.id][0], "org_count": len(counts[r.id][1]),
             "orgs": sorted(counts[r.id][1])}
            for r in rows
        ],
    }


@app.get("/api/canonical/{nmc_id}")
def canonical_detail(nmc_id: str, db: DbSession = Depends(get_session),
                     _u: User = Depends(current_user)) -> dict:
    rec = db.get(CanonicalMaterial, nmc_id.upper())
    if rec is None:
        fail(404, "not_found", f"No canonical material {nmc_id}.")
    rule = db.get(ItemClassRule, rec.item_class)
    sources = db.execute(
        select(SourceRecord, Mapping)
        .join(Mapping, Mapping.source_record_id == SourceRecord.id)
        .where(Mapping.canonical_id == rec.id,
               Mapping.status == MappingStatus.APPROVED)
    ).all()
    return {
        "nmc_id": rec.id, "item_name": rec.item_name, "canonical_text": rec.canonical_text,
        "item_class": rec.item_class,
        "class_rule": {"label": rule.label, "basis": rule.basis,
                       "bars_auto_match": rule.bars_auto_match} if rule else None,
        "spec_standard": rec.spec_standard, "spec_revision": rec.spec_revision,
        "superseded_by": rec.superseded_by,
        "attributes": [{"code": k, "label": k.replace("_", " ").title(), "value": v}
                       for k, v in (rec.attributes or {}).items()],
        "sources": [
            {"record_id": s.id, "org": s.org_id, "org_code": s.org_code,
             "description": s.raw_description, "provenance": s.provenance,
             "mapping_id": m.id, "mapped_at": m.effective_from.isoformat()}
            for s, m in sources
        ],
        "source_count": len(sources),
        "org_count": len({s.org_id for s, _ in sources}),
    }


@app.get("/api/material/{record_id}")
def material(record_id: str, db: DbSession = Depends(get_session),
             _u: User = Depends(current_user)) -> dict:
    rec = db.get(SourceRecord, record_id)
    if rec is None:
        fail(404, "not_found", f"No record {record_id}.")
    m = service.live_mapping(db, record_id)
    return {
        "id": rec.id, "org": rec.org_id, "org_code": rec.org_code,
        "raw_description": rec.raw_description, "normalised": rec.normalised,
        "item_name": rec.item_name or None, "provenance": rec.provenance,
        "attributes": [{"code": k, "value": v} for k, v in (rec.attributes or {}).items()],
        "mapping": {"id": m.id, "canonical_id": m.canonical_id, "status": m.status.value,
                    "confidence": m.confidence} if m else None,
    }


@app.get("/api/material/{record_id}/history")
def material_history(record_id: str, db: DbSession = Depends(get_session),
                     _u: User = Depends(current_user)) -> dict:
    """Every claim ever made on this code, with its effective range."""
    if db.get(SourceRecord, record_id) is None:
        fail(404, "not_found", f"No record {record_id}.")
    rows = db.scalars(
        select(Mapping).where(Mapping.source_record_id == record_id)
        .order_by(Mapping.effective_from.asc())).all()
    return {"record_id": record_id, "history": [
        {"mapping_id": m.id, "canonical_id": m.canonical_id, "status": m.status.value,
         "from": m.effective_from.isoformat(),
         "to": m.effective_to.isoformat() if m.effective_to else None,
         "superseded_by": m.superseded_by, "engine": m.decided_by_engine}
        for m in rows]}


@app.get("/api/material/{record_id}/as-of")
def material_as_of(record_id: str, at: str, db: DbSession = Depends(get_session),
                   _u: User = Depends(current_user)) -> dict:
    """What this code meant at a moment. The vintage query."""
    try:
        when = datetime.fromisoformat(at)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    except ValueError:
        fail(400, "bad_timestamp", "`at` must be an ISO-8601 timestamp.")
    m = service.as_of(db, record_id, when)
    return {"record_id": record_id, "at": when.isoformat(),
            "canonical_id": m.canonical_id if m else None,
            "status": m.status.value if m else None}


# ── the review queue and the write path ────────────────────────────────────

@app.get("/api/review/queue")
def review_queue(limit: int = Query(default=25, ge=1, le=100),
                 cursor: str | None = None,
                 db: DbSession = Depends(get_session),
                 user: User = Depends(current_user)) -> dict:
    """
    What this reviewer may actually act on.

    Scoped by organisation and commodity family, so the queue is not a list of
    work someone else has to do. A reviewer with no scope sees nothing, which is
    correct — an empty scope means no families, not all of them.
    """
    from .extract.templates import family_for
    stmt = (select(Mapping, SourceRecord, CanonicalMaterial)
            .join(SourceRecord, SourceRecord.id == Mapping.source_record_id)
            .join(CanonicalMaterial, CanonicalMaterial.id == Mapping.canonical_id)
            .where(Mapping.status == MappingStatus.PROPOSED,
                   SourceRecord.org_id == user.org_id))
    if cursor:
        stmt = stmt.where(Mapping.id > cursor)
    rows = db.execute(stmt.order_by(Mapping.id).limit(limit * 3)).all()

    out = []
    for m, s, c in rows:
        fam = family_for(c.item_name)
        from .authz import certified_for_class, in_commodity_scope
        if not in_commodity_scope(user, fam):
            continue
        out.append({
            "mapping_id": m.id, "record_id": s.id, "org": s.org_id, "org_code": s.org_code,
            "description": s.raw_description, "canonical_id": c.id,
            "canonical_text": c.canonical_text, "item_name": c.item_name,
            "item_class": c.item_class, "family": fam,
            "confidence": m.confidence, "engine": m.decided_by_engine,
            "you_may_approve": certified_for_class(user, c.item_class),
        })
        if len(out) >= limit:
            break
    return {"queue": out, "next_cursor": out[-1]["mapping_id"] if len(out) == limit else None,
            "scope": {"org": user.org_id, "commodity": user.commodity_scope or []}}


class ProposeRequest(BaseModel):
    source_record_id: str
    canonical_id: str
    confidence: float = 0.0
    engine_decision: str = "HUMAN"
    evidence: dict = Field(default_factory=dict)
    note: str = ""


class NoteRequest(BaseModel):
    note: str = ""


class RemapRequest(BaseModel):
    canonical_id: str
    note: str


class MergeRequest(BaseModel):
    keep_id: str
    absorb_id: str
    note: str


class SplitRequest(BaseModel):
    move_record_ids: list[str]
    new_material: dict = Field(default_factory=dict)
    note: str


def _mapping_out(m: Mapping) -> dict:
    return {"mapping_id": m.id, "source_record_id": m.source_record_id,
            "canonical_id": m.canonical_id, "status": m.status.value,
            "confidence": m.confidence,
            "effective_from": m.effective_from.isoformat(),
            "effective_to": m.effective_to.isoformat() if m.effective_to else None}


@app.post("/api/mappings/propose")
def propose(req: ProposeRequest, db: DbSession = Depends(get_session),
            user: User = Depends(current_user)) -> dict:
    m = service.propose(db, actor=user, source_record_id=req.source_record_id,
                        canonical_id=req.canonical_id, confidence=req.confidence,
                        evidence=req.evidence, engine_decision=req.engine_decision,
                        note=req.note)
    return _mapping_out(m)


@app.post("/api/mappings/{mapping_id}/approve")
def approve(mapping_id: str, req: NoteRequest, db: DbSession = Depends(get_session),
            user: User = Depends(current_user)) -> dict:
    return _mapping_out(service.approve(db, actor=user, mapping_id=mapping_id, note=req.note))


@app.post("/api/mappings/{mapping_id}/reject")
def reject(mapping_id: str, req: NoteRequest, db: DbSession = Depends(get_session),
           user: User = Depends(current_user)) -> dict:
    return _mapping_out(service.reject(db, actor=user, mapping_id=mapping_id, note=req.note))


@app.post("/api/records/{record_id}/unmap")
def unmap(record_id: str, req: NoteRequest, db: DbSession = Depends(get_session),
          user: User = Depends(current_user)) -> dict:
    return _mapping_out(service.unmap(db, actor=user, source_record_id=record_id, note=req.note))


@app.post("/api/records/{record_id}/remap")
def remap(record_id: str, req: RemapRequest, db: DbSession = Depends(get_session),
          user: User = Depends(current_user)) -> dict:
    return _mapping_out(service.remap(db, actor=user, source_record_id=record_id,
                                      canonical_id=req.canonical_id, note=req.note))


@app.post("/api/canonical/merge")
def merge(req: MergeRequest, db: DbSession = Depends(get_session),
          user: User = Depends(current_user)) -> dict:
    kept = service.merge(db, actor=user, keep_id=req.keep_id,
                         absorb_id=req.absorb_id, note=req.note)
    return {"kept": kept.id, "absorbed": req.absorb_id}


@app.post("/api/canonical/{canonical_id}/split")
def split(canonical_id: str, req: SplitRequest, db: DbSession = Depends(get_session),
          user: User = Depends(current_user)) -> dict:
    new = service.split(db, actor=user, canonical_id=canonical_id,
                        move_record_ids=req.move_record_ids,
                        new_material=req.new_material, note=req.note)
    return {"from": canonical_id, "new": new.id}


# ── the audit trail ────────────────────────────────────────────────────────

@app.get("/api/decisions")
def decisions(limit: int = Query(default=50, ge=1, le=200),
              mapping_id: str | None = None,
              db: DbSession = Depends(get_session),
              _u: User = Depends(current_user)) -> dict:
    stmt = select(Decision).order_by(Decision.seq.desc()).limit(limit)
    if mapping_id:
        stmt = select(Decision).where(Decision.mapping_id == mapping_id).order_by(Decision.seq.desc())
    rows = db.scalars(stmt).all()
    return {"decisions": [
        {"id": d.id, "seq": d.seq, "kind": d.kind.value, "mapping_id": d.mapping_id,
         "canonical_id": d.canonical_id, "actor_id": d.actor_id,
         "actor_role": d.actor_role, "actor_scope": d.actor_scope, "note": d.note,
         "gazetteer_version": d.gazetteer_version, "template_version": d.template_version,
         "model_version": d.model_version, "hash": d.hash, "prev_hash": d.prev_hash,
         "at": d.created_at.isoformat()}
        for d in rows]}


@app.get("/api/decisions/{decision_id}")
def decision_certificate(decision_id: str, db: DbSession = Depends(get_session),
                         _u: User = Depends(current_user)) -> dict:
    """The certificate, served verbatim — including the evidence as frozen."""
    # Not db.get(): Decision's primary key is `seq`, because SQLite only
    # auto-increments an INTEGER PRIMARY KEY. `id` is the public handle and
    # carries its own unique index, so it has to be queried by column — a
    # db.get() here silently looks up seq == "dec-…" and 404s every time.
    d = db.scalar(select(Decision).where(Decision.id == decision_id))
    if d is None:
        fail(404, "not_found", f"No decision {decision_id}.")
    actor = db.get(User, d.actor_id) if d.actor_id else None
    return {
        "id": d.id, "seq": d.seq, "kind": d.kind.value,
        "mapping_id": d.mapping_id, "source_record_id": d.source_record_id,
        "canonical_id": d.canonical_id,
        "actor": {"id": actor.id, "name": actor.name, "role": d.actor_role,
                  "scope_at_decision": d.actor_scope} if actor else None,
        "note": d.note, "evidence": d.evidence,
        "versions": {"gazetteer": d.gazetteer_version, "template": d.template_version,
                     "model": d.model_version},
        "chain": {"prev_hash": d.prev_hash, "hash": d.hash},
        "at": d.created_at.isoformat(),
    }


@app.get("/api/decisions/chain/verify")
def verify_chain(db: DbSession = Depends(get_session),
                 _u: User = Depends(current_user)) -> dict:
    r = service.verify_chain(db)
    return {**r, "note": "Tamper-evident only. The chain proves internal "
                         "consistency; it becomes evidence when the head is "
                         "anchored outside this database."}


@app.get("/api/audit")
def audit_log(limit: int = Query(default=100, ge=1, le=500),
              db: DbSession = Depends(get_session),
              user: User = Depends(current_user)) -> dict:
    from .authz import require_role
    require_role(user, Role.ADMIN, Role.STEWARD)
    from .db.models import AuditEvent
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.at.desc()).limit(limit)).all()
    return {"events": [
        {"id": e.id, "at": e.at.isoformat(), "actor_id": e.actor_id,
         "action": e.action, "subject": e.subject, "detail": e.detail}
        for e in rows]}


# ── bulk ───────────────────────────────────────────────────────────────────

@app.post("/api/ingest")
async def ingest(file: UploadFile, db: DbSession = Depends(get_session),
                 user: User = Depends(current_user)) -> dict:
    """
    Bulk upload of a material master.

    CSV with a `description` column; `code` is optional. Rows land as source
    records owned by the uploader's organisation — never another's, for the same
    reason approval cannot cross organisations.
    """
    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    job = IngestJob(id=f"job-{secrets.token_hex(6)}", org_id=user.org_id,
                    filename=file.filename or "upload.csv",
                    status=JobStatus.RUNNING, created_by=user.id)
    db.add(job)
    db.flush()

    eng = matching_engine()
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or "description" not in [f.lower().strip() for f in reader.fieldnames]:
        job.status, job.error = JobStatus.FAILED, "no `description` column"
        fail(400, "bad_file", "The file needs a `description` column.")

    key = next(f for f in reader.fieldnames if f.lower().strip() == "description")
    code_key = next((f for f in reader.fieldnames if f.lower().strip() in ("code", "org_code")), None)

    accepted = 0
    for i, row in enumerate(reader):
        desc = (row.get(key) or "").strip()
        job.total += 1
        if not desc:
            job.rejected += 1
            continue
        rid = f"ING-{job.id[-6:]}-{i:06d}"
        rec = MaterialRecord(id=rid, raw_description=desc, org=user.org_id,
                             org_code=(row.get(code_key) or "").strip() if code_key else "",
                             provenance="UPLOADED")
        eng.prepare(rec)
        db.add(SourceRecord(
            id=rid, org_id=user.org_id, org_code=rec.org_code, raw_description=desc,
            normalised=rec.normalised, item_name=rec.item_name or "",
            attributes={c: str(a.value) for c, a in rec.attributes.items() if a.known},
            provenance="UPLOADED", ingest_job_id=job.id))
        accepted += 1
        job.processed += 1

    job.accepted = accepted
    job.status = JobStatus.DONE
    job.finished_at = utcnow()
    service.audit(db, actor=user, action="ingest.upload", subject=job.id,
                  detail={"file": job.filename, "accepted": accepted})
    db.commit()
    # The index is a derived cache; new rows are invisible to retrieval until it
    # is rebuilt, so say so rather than letting a reviewer wonder.
    return {"job_id": job.id, "accepted": accepted, "rejected": job.rejected,
            "total": job.total,
            "note": "Records are stored. Call /api/reindex to make them retrievable."}


@app.get("/api/ingest/{job_id}")
def ingest_status(job_id: str, db: DbSession = Depends(get_session),
                  _u: User = Depends(current_user)) -> dict:
    j = db.get(IngestJob, job_id)
    if j is None:
        fail(404, "not_found", f"No job {job_id}.")
    return {"job_id": j.id, "status": j.status.value, "filename": j.filename,
            "total": j.total, "processed": j.processed, "accepted": j.accepted,
            "rejected": j.rejected, "error": j.error,
            "created_at": j.created_at.isoformat(),
            "finished_at": j.finished_at.isoformat() if j.finished_at else None}


@app.post("/api/reindex")
def reindex(db: DbSession = Depends(get_session), user: User = Depends(current_user)) -> dict:
    from .authz import require_role
    require_role(user, Role.ADMIN, Role.STEWARD)
    _load_index()
    service.audit(db, actor=user, action="index.rebuild", detail={"records": _indexed})
    return {"indexed": _indexed, "ms": round(_ready_ms)}


@app.get("/api/export")
def export(db: DbSession = Depends(get_session), user: User = Depends(current_user)):
    """Approved mappings, as CSV, scoped to the caller's organisation."""
    rows = db.execute(
        select(SourceRecord, Mapping, CanonicalMaterial)
        .join(Mapping, Mapping.source_record_id == SourceRecord.id)
        .join(CanonicalMaterial, CanonicalMaterial.id == Mapping.canonical_id)
        .where(Mapping.status == MappingStatus.APPROVED,
               SourceRecord.org_id == user.org_id)
    ).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["org", "org_code", "source_record_id", "description",
                "nmc_id", "canonical_text", "item_class", "effective_from"])
    for s, m, c in rows:
        w.writerow([s.org_id, s.org_code, s.id, s.raw_description, c.id,
                    c.canonical_text, c.item_class, m.effective_from.isoformat()])
    service.audit(db, actor=user, action="export.csv", detail={"rows": len(rows)})
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="sangam-{user.org_id}-mappings.csv"'})


# ── samples ────────────────────────────────────────────────────────────────

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
def samples(db: DbSession = Depends(get_session),
            _u: User = Depends(current_user)) -> dict:
    eng = matching_engine()
    usable = []
    for s in _SAMPLES:
        probe = eng.prepare(MaterialRecord(id="__sample__", raw_description=s["query"]))
        if probe.item_name:
            usable.append({**s, "item_name": probe.item_name})
    return {
        "samples": [s["query"] for s in usable],
        "examples": usable,
        "corpus_size": _indexed,
        "organisations": sorted(o.id for o in db.scalars(select(Organisation))),
    }
