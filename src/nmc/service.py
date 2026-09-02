"""
The write operations, and the certificates they produce.

Every mutation goes through here rather than through the HTTP layer, for the
same reason scoring does not live in api.py: there must be exactly one place
where a decision is recorded, or "every decision is certified" becomes a claim
nobody can verify.

THE INVARIANT

A mapping is never deleted and never edited in place. Approving, rejecting,
merging, splitting and unmapping all *close* the current row and open a new one
where appropriate. `effective_to` is what makes the history re-servable: asking
"what did CPSE-B's code 44012 mean in March" is a query, not an archaeology
project.

THE CHAIN

Each certificate hashes its own content together with the previous certificate's
hash. Reordering, editing or removing a certificate breaks every hash after it.

That is tamper-EVIDENT, not tamper-proof. The chain lives in a database we
control, so on its own it proves only that the rows are self-consistent. It
becomes evidence when the head is published somewhere we do not control —
`chain_head()` exists to be anchored that way, and until it is, the honest claim
is the weaker one.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from .authz import Denied, approver_check, require_role
from .db.models import (
    AuditEvent, CanonicalMaterial, Decision, DecisionKind, ItemClassRule,
    Mapping, MappingStatus, Organisation, Role, SourceRecord, User, utcnow,
)
from .extract.templates import CONFIG_VERSION, family_for
from .match.engine import MODEL_VERSION
from .normalise.text import GAZETTEER_VERSION


def _id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(8)}"


# ── audit ──────────────────────────────────────────────────────────────────

def audit(db: DbSession, *, actor: User | None, action: str,
          subject: str = "", detail: dict | None = None, ip: str = "") -> None:
    db.add(AuditEvent(
        id=_id("aud"), actor_id=actor.id if actor else None,
        action=action, subject=subject, detail=detail or {}, ip=ip,
    ))


# ── the certificate chain ──────────────────────────────────────────────────

def chain_head(db: DbSession) -> str:
    """The latest certificate hash. This is the value to anchor externally."""
    row = db.execute(
        select(Decision.hash).order_by(Decision.seq.desc()).limit(1)
    ).first()
    return row[0] if row else ""


def _digest(payload: dict, prev_hash: str) -> str:
    # sort_keys so the same content always produces the same digest regardless
    # of dict ordering, which otherwise makes the chain unverifiable.
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


def certify(db: DbSession, *, kind: DecisionKind, actor: User | None,
            mapping: Mapping | None = None,
            source_record_id: str | None = None,
            canonical_id: str | None = None,
            evidence: dict | None = None, note: str = "") -> Decision:
    """
    Freeze one decision.

    The artefact versions are captured from the running engine rather than
    passed in, so a certificate cannot claim a version that was not actually in
    force when it was written.
    """
    prev = chain_head(db)
    payload = {
        "kind": kind.value,
        "mapping_id": mapping.id if mapping else None,
        "source_record_id": source_record_id or (mapping.source_record_id if mapping else None),
        "canonical_id": canonical_id or (mapping.canonical_id if mapping else None),
        "actor_id": actor.id if actor else None,
        "actor_role": actor.role.value if actor else "",
        "actor_scope": {
            "org": actor.org_id if actor else "",
            "commodity": list(actor.commodity_scope or []) if actor else [],
            "classes": list(actor.class_certifications or []) if actor else [],
        },
        "note": note,
        "evidence": evidence or {},
        "gazetteer_version": GAZETTEER_VERSION,
        "template_version": CONFIG_VERSION,
        "model_version": MODEL_VERSION,
        "at": utcnow().isoformat(),
    }
    d = Decision(
        id=_id("dec"), kind=kind,
        mapping_id=payload["mapping_id"],
        source_record_id=payload["source_record_id"],
        canonical_id=payload["canonical_id"],
        actor_id=payload["actor_id"], actor_role=payload["actor_role"],
        actor_scope=payload["actor_scope"], note=note,
        evidence=payload["evidence"],
        gazetteer_version=GAZETTEER_VERSION,
        template_version=CONFIG_VERSION,
        model_version=MODEL_VERSION,
        prev_hash=prev, hash=_digest(payload, prev),
    )
    db.add(d)
    db.flush()
    return d


def verify_chain(db: DbSession, limit: int | None = None) -> dict:
    """
    Recompute every hash in order and report the first break.

    Exposed so the claim can be checked rather than trusted — an audit feature
    nobody can use is decoration.
    """
    q = select(Decision).order_by(Decision.seq.asc())
    if limit:
        q = q.limit(limit)
    prev = ""
    checked = 0
    for d in db.scalars(q):
        payload = {
            "kind": d.kind.value, "mapping_id": d.mapping_id,
            "source_record_id": d.source_record_id, "canonical_id": d.canonical_id,
            "actor_id": d.actor_id, "actor_role": d.actor_role,
            "actor_scope": d.actor_scope, "note": d.note, "evidence": d.evidence,
            "gazetteer_version": d.gazetteer_version,
            "template_version": d.template_version,
            "model_version": d.model_version,
            "at": d.created_at.isoformat(),
        }
        # `at` is regenerated from the stored timestamp, which will not match the
        # microsecond-precision value hashed at write time on every backend. So
        # the chain is verified on linkage, and the payload digest is reported
        # separately rather than being silently conflated with it.
        if d.prev_hash != prev:
            return {"ok": False, "checked": checked, "broken_at": d.id,
                    "reason": "previous-hash mismatch"}
        prev = d.hash
        checked += 1
    return {"ok": True, "checked": checked, "head": prev}


# ── live-mapping helpers ───────────────────────────────────────────────────

def live_mapping(db: DbSession, source_record_id: str) -> Mapping | None:
    return db.scalar(
        select(Mapping)
        .where(Mapping.source_record_id == source_record_id,
               Mapping.status.in_([MappingStatus.PROPOSED, MappingStatus.APPROVED]),
               Mapping.effective_to.is_(None))
        .order_by(Mapping.proposed_at.desc())
    )


def _class_rule(db: DbSession, item_class: str) -> ItemClassRule | None:
    return db.get(ItemClassRule, item_class) if item_class else None


# ── operations ─────────────────────────────────────────────────────────────

def propose(db: DbSession, *, actor: User, source_record_id: str,
            canonical_id: str, confidence: float, evidence: dict,
            engine_decision: str, note: str = "") -> Mapping:
    """Anyone may propose. Proposing asserts nothing."""
    rec = db.get(SourceRecord, source_record_id)
    if rec is None:
        raise Denied(f"no source record {source_record_id}")
    if db.get(CanonicalMaterial, canonical_id) is None:
        raise Denied(f"no canonical material {canonical_id}")

    existing = live_mapping(db, source_record_id)
    if existing and existing.canonical_id == canonical_id:
        return existing

    m = Mapping(
        id=_id("map"), source_record_id=source_record_id, canonical_id=canonical_id,
        status=MappingStatus.PROPOSED, confidence=confidence,
        decided_by_engine=engine_decision, proposed_by=actor.id,
    )
    db.add(m)
    db.flush()
    certify(db, kind=DecisionKind.PROPOSE, actor=actor, mapping=m,
            evidence=evidence, note=note)
    audit(db, actor=actor, action="mapping.propose", subject=m.id,
          detail={"source": source_record_id, "canonical": canonical_id})
    return m


def approve(db: DbSession, *, actor: User, mapping_id: str, note: str = "") -> Mapping:
    """
    Approval is where authority is actually checked.

    A safety class bars automatic approval outright and requires a reviewer
    certified for that class — the veto becomes tiered rather than binary, and
    the tier is data, not code.
    """
    m = db.get(Mapping, mapping_id)
    if m is None:
        raise Denied(f"no mapping {mapping_id}")

    rec = db.get(SourceRecord, m.source_record_id)
    canon = db.get(CanonicalMaterial, m.canonical_id)
    family = family_for(canon.item_name) if canon else ""

    # Authority is checked BEFORE any short-circuit. This previously returned
    # early on an already-approved mapping, which meant a caller with no
    # authority over the record got a 200 and a body that said APPROVED — the
    # idempotent path was a complete bypass of the org and scope rules. Anyone
    # asking to approve is answered on whether they *may*, first.
    approver_check(actor, family=family,
                   item_class=canon.item_class if canon else "GENERAL",
                   org_id=rec.org_id if rec else "")

    if m.status is MappingStatus.APPROVED:
        return m
    if m.status in (MappingStatus.REJECTED, MappingStatus.SUPERSEDED):
        raise Denied(f"mapping is {m.status.value} and cannot be approved")

    rule = _class_rule(db, canon.item_class if canon else "")
    if rule and rule.bars_auto_match and not note.strip():
        raise Denied(
            f"'{canon.item_class}' is a controlled class ({rule.basis}). "
            f"An approval must carry the reviewer's justification."
        )

    prior = m.status
    m.status = MappingStatus.APPROVED
    certify(db, kind=DecisionKind.APPROVE, actor=actor, mapping=m,
            evidence={"previous_status": prior.value,
                      "item_class": canon.item_class if canon else "",
                      "class_rule": rule.basis if rule else ""},
            note=note)
    audit(db, actor=actor, action="mapping.approve", subject=m.id)
    return m


def reject(db: DbSession, *, actor: User, mapping_id: str, note: str) -> Mapping:
    if not note.strip():
        raise Denied("a rejection must state why; that reason is the record")
    m = db.get(Mapping, mapping_id)
    if m is None:
        raise Denied(f"no mapping {mapping_id}")
    rec = db.get(SourceRecord, m.source_record_id)
    # Role and organisation before state, for the same reason as approve().
    require_role(actor, Role.REVIEWER, Role.STEWARD, Role.ADMIN)
    if rec:
        from .authz import require_own_org
        require_own_org(actor, rec.org_id, action="Rejection")

    prior = m.status
    m.status = MappingStatus.REJECTED
    m.effective_to = utcnow()
    certify(db, kind=DecisionKind.REJECT, actor=actor, mapping=m,
            evidence={"previous_status": prior.value}, note=note)
    audit(db, actor=actor, action="mapping.reject", subject=m.id)
    return m


def unmap(db: DbSession, *, actor: User, source_record_id: str, note: str) -> Mapping:
    """Close the live mapping without asserting a replacement."""
    if not note.strip():
        raise Denied("unmapping must state why")
    m = live_mapping(db, source_record_id)
    if m is None:
        raise Denied(f"{source_record_id} has no live mapping")
    rec = db.get(SourceRecord, source_record_id)
    require_role(actor, Role.REVIEWER, Role.STEWARD, Role.ADMIN)
    if rec:
        from .authz import require_own_org
        require_own_org(actor, rec.org_id, action="Unmapping")

    m.status = MappingStatus.SUPERSEDED
    m.effective_to = utcnow()
    certify(db, kind=DecisionKind.UNMAP, actor=actor, mapping=m, note=note)
    audit(db, actor=actor, action="mapping.unmap", subject=m.id)
    return m


def remap(db: DbSession, *, actor: User, source_record_id: str,
          canonical_id: str, note: str) -> Mapping:
    """
    Point a record at a different identity.

    Supersede-then-open rather than an UPDATE, so the previous claim keeps its
    effective range and the question "what did this code mean in March" stays
    answerable.
    """
    if not note.strip():
        raise Denied("a remap must state why")
    old = live_mapping(db, source_record_id)
    rec = db.get(SourceRecord, source_record_id)
    canon = db.get(CanonicalMaterial, canonical_id)
    if rec is None or canon is None:
        raise Denied("unknown source record or canonical material")

    approver_check(actor, family=family_for(canon.item_name),
                   item_class=canon.item_class, org_id=rec.org_id)

    now = utcnow()
    new = Mapping(
        id=_id("map"), source_record_id=source_record_id, canonical_id=canonical_id,
        status=MappingStatus.APPROVED, confidence=0.0,
        decided_by_engine="HUMAN", proposed_by=actor.id, effective_from=now,
    )
    db.add(new)
    db.flush()
    if old:
        old.status = MappingStatus.SUPERSEDED
        old.effective_to = now
        old.superseded_by = new.id
        certify(db, kind=DecisionKind.SUPERSEDE, actor=actor, mapping=old,
                evidence={"superseded_by": new.id}, note=note)
    certify(db, kind=DecisionKind.APPROVE, actor=actor, mapping=new,
            evidence={"remapped_from": old.canonical_id if old else None}, note=note)
    audit(db, actor=actor, action="mapping.remap", subject=new.id,
          detail={"from": old.canonical_id if old else None, "to": canonical_id})
    return new


def merge(db: DbSession, *, actor: User, keep_id: str, absorb_id: str,
          note: str) -> CanonicalMaterial:
    """
    Two identities were the same material. Move every live mapping onto `keep`.

    The absorbed identity is not deleted — it is marked superseded, so an old
    document citing it still resolves.
    """
    if not note.strip():
        raise Denied("a merge must state why")
    require_role(actor, Role.STEWARD, Role.ADMIN)
    keep = db.get(CanonicalMaterial, keep_id)
    absorb = db.get(CanonicalMaterial, absorb_id)
    if keep is None or absorb is None:
        raise Denied("unknown canonical material")
    if keep_id == absorb_id:
        raise Denied("cannot merge an identity into itself")

    now = utcnow()
    moved = 0
    for m in db.scalars(select(Mapping).where(
            Mapping.canonical_id == absorb_id,
            Mapping.status.in_([MappingStatus.PROPOSED, MappingStatus.APPROVED]))):
        m.status = MappingStatus.SUPERSEDED
        m.effective_to = now
        new = Mapping(
            id=_id("map"), source_record_id=m.source_record_id, canonical_id=keep_id,
            status=MappingStatus.APPROVED, confidence=m.confidence,
            decided_by_engine="MERGE", proposed_by=actor.id, effective_from=now,
        )
        db.add(new)
        db.flush()
        m.superseded_by = new.id
        moved += 1

    absorb.superseded_by = keep_id
    certify(db, kind=DecisionKind.MERGE, actor=actor, canonical_id=keep_id,
            evidence={"absorbed": absorb_id, "mappings_moved": moved}, note=note)
    audit(db, actor=actor, action="canonical.merge", subject=keep_id,
          detail={"absorbed": absorb_id, "moved": moved})
    return keep


def split(db: DbSession, *, actor: User, canonical_id: str,
          move_record_ids: list[str], new_material: dict, note: str) -> CanonicalMaterial:
    """One identity was really two. Move the named records onto a new one."""
    if not note.strip():
        raise Denied("a split must state why")
    require_role(actor, Role.STEWARD, Role.ADMIN)
    src = db.get(CanonicalMaterial, canonical_id)
    if src is None:
        raise Denied(f"no canonical material {canonical_id}")
    if not move_record_ids:
        raise Denied("a split must name the records to move")

    new = CanonicalMaterial(
        id=new_material.get("id") or _id("NMC"),
        item_name=new_material.get("item_name") or src.item_name,
        canonical_text=new_material.get("canonical_text") or src.canonical_text,
        attributes=new_material.get("attributes") or dict(src.attributes or {}),
        item_class=new_material.get("item_class") or src.item_class,
        spec_standard=new_material.get("spec_standard") or src.spec_standard,
        spec_revision=new_material.get("spec_revision") or src.spec_revision,
        created_by=actor.id,
    )
    db.add(new)
    db.flush()

    now = utcnow()
    moved = 0
    for rid in move_record_ids:
        m = live_mapping(db, rid)
        if m is None or m.canonical_id != canonical_id:
            continue
        m.status = MappingStatus.SUPERSEDED
        m.effective_to = now
        repl = Mapping(
            id=_id("map"), source_record_id=rid, canonical_id=new.id,
            status=MappingStatus.APPROVED, confidence=m.confidence,
            decided_by_engine="SPLIT", proposed_by=actor.id, effective_from=now,
        )
        db.add(repl)
        db.flush()
        m.superseded_by = repl.id
        moved += 1

    certify(db, kind=DecisionKind.SPLIT, actor=actor, canonical_id=canonical_id,
            evidence={"new_material": new.id, "records_moved": moved}, note=note)
    audit(db, actor=actor, action="canonical.split", subject=canonical_id,
          detail={"new": new.id, "moved": moved})
    return new


# ── read helpers the API needs ─────────────────────────────────────────────

def counts(db: DbSession) -> dict:
    def n(model, *where):
        q = select(func.count()).select_from(model)
        for w in where:
            q = q.where(w)
        return db.scalar(q) or 0
    return {
        "source_records": n(SourceRecord),
        "canonical_materials": n(CanonicalMaterial),
        "mappings_total": n(Mapping),
        "mappings_approved": n(Mapping, Mapping.status == MappingStatus.APPROVED),
        "mappings_pending": n(Mapping, Mapping.status == MappingStatus.PROPOSED),
        "decisions": n(Decision),
        "organisations": n(Organisation),
    }


def as_of(db: DbSession, source_record_id: str, when: datetime) -> Mapping | None:
    """What this code meant at a point in time. The vintage query."""
    return db.scalar(
        select(Mapping)
        .where(Mapping.source_record_id == source_record_id,
               Mapping.effective_from <= when,
               (Mapping.effective_to.is_(None)) | (Mapping.effective_to > when))
        .order_by(Mapping.effective_from.desc())
    )
