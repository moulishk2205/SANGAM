"""
The persistence and governance layer, as executable tests.

These are the assertions that make the governance claims checkable rather than
asserted. The most important one is `test_approve_checks_authority_before_state`:
that bug shipped in the first draft of this layer and returned 200 APPROVED to a
caller with no authority over the record, because the idempotent early-return
ran ahead of the authorisation check.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.nmc.authz import Denied, hash_password, verify_password
from src.nmc.db.models import (
    Base, CanonicalMaterial, Decision, ItemClassRule, Mapping, MappingStatus,
    Organisation, Role, SourceRecord, User, utcnow,
)
from src.nmc import service


@pytest.fixture()
def db():
    """A fresh in-memory database per test. No fixture bleeds into another."""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, expire_on_commit=False)()
    for oid in ("CPSE-A", "CPSE-B"):
        s.add(Organisation(id=oid, name=oid))
    s.add(ItemClassRule(item_class="PRESSURE", label="Pressure",
                        bars_auto_match=True, requires_certification=True,
                        basis="ASME B16.5"))
    s.add(CanonicalMaterial(id="NMC-1", item_name="BOLT, MACHINE",
                            canonical_text="SS HEX BOLT M10 X 50", item_class="GENERAL"))
    s.add(CanonicalMaterial(id="NMC-2", item_name="BOLT, MACHINE",
                            canonical_text="SS HEX BOLT M10 X 75", item_class="GENERAL"))
    s.add(CanonicalMaterial(id="NMC-P", item_name="VALVE",
                            canonical_text="SS BALL VALVE 50 MM", item_class="PRESSURE"))
    s.add(SourceRecord(id="R1", org_id="CPSE-A", org_code="MAT-1",
                       raw_description="SS HEX BOLT M10 X 50", item_name="BOLT, MACHINE"))
    s.add(SourceRecord(id="RP", org_id="CPSE-A", org_code="MAT-9",
                       raw_description="SS BALL VALVE 2 INCH", item_name="VALVE"))
    s.commit()
    yield s
    s.close()


def _user(db, uid, role, org, scope=(), certs=()):
    u = User(id=uid, email=f"{uid}@x.test", name=uid, role=role, org_id=org,
             commodity_scope=list(scope), class_certifications=list(certs),
             password_hash=hash_password("pw"))
    db.add(u)
    db.commit()
    return u


# ── passwords ──────────────────────────────────────────────────────────────

def test_password_round_trip_and_rejection():
    h = hash_password("correct horse")
    assert verify_password("correct horse", h)
    assert not verify_password("Correct horse", h)
    assert "correct horse" not in h          # never stored in the clear
    assert h.startswith("pbkdf2_sha256$")


def test_same_password_hashes_differently():
    """Per-user salt: two accounts with the same password must not collide."""
    assert hash_password("same") != hash_password("same")


# ── authority ──────────────────────────────────────────────────────────────

def test_cross_org_approval_is_refused(db):
    """The guarantee: nobody maps another organisation's code."""
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    b = _user(db, "b", Role.REVIEWER, "CPSE-B", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied) as e:
        service.approve(db, actor=b, mapping_id=m.id, note="ok")
    assert "CPSE-A" in e.value.reason


def test_admin_is_not_exempt_from_cross_org(db):
    """
    Deliberate: an administrator who can rewrite another CPSE's master is
    exactly what stops CPSEs from joining.
    """
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    root = _user(db, "root", Role.ADMIN, "CPSE-B")
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied):
        service.approve(db, actor=root, mapping_id=m.id, note="ok")


def test_requester_cannot_approve(db):
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    r = _user(db, "r", Role.REQUESTER, "CPSE-A", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied):
        service.approve(db, actor=r, mapping_id=m.id, note="ok")


def test_empty_commodity_scope_grants_nothing(db):
    """An empty scope means no families, not all of them."""
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", [])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied) as e:
        service.approve(db, actor=a, mapping_id=m.id, note="ok")
    assert "not certified" in e.value.reason


def test_safety_class_needs_certification_and_a_note(db):
    """A controlled class requires an explicitly certified reviewer."""
    plain = _user(db, "p", Role.REVIEWER, "CPSE-A", ["valve"])
    m = service.propose(db, actor=plain, source_record_id="RP", canonical_id="NMC-P",
                        confidence=0.99, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied) as e:
        service.approve(db, actor=plain, mapping_id=m.id, note="fine")
    assert "certification" in e.value.reason

    cert = _user(db, "c", Role.REVIEWER, "CPSE-A", ["valve"], ["PRESSURE"])
    # certified, but a controlled class still cannot be waved through silently
    with pytest.raises(Denied) as e2:
        service.approve(db, actor=cert, mapping_id=m.id, note="   ")
    assert "justification" in e2.value.reason

    ok = service.approve(db, actor=cert, mapping_id=m.id, note="Verified to B16.5.")
    assert ok.status is MappingStatus.APPROVED


def test_approve_checks_authority_before_state(db):
    """
    Regression. The idempotent early-return on an already-approved mapping used
    to run BEFORE the authority check, so an unauthorised caller received 200
    and a body saying APPROVED — a complete bypass of the org and scope rules.
    """
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    b = _user(db, "b", Role.REVIEWER, "CPSE-B", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    service.approve(db, actor=a, mapping_id=m.id, note="ok")
    assert m.status is MappingStatus.APPROVED

    with pytest.raises(Denied):
        service.approve(db, actor=b, mapping_id=m.id, note="ok")


# ── history is never destroyed ─────────────────────────────────────────────

def test_remap_supersedes_rather_than_updating(db):
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    first = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                            confidence=0.9, evidence={}, engine_decision="MATCH")
    service.approve(db, actor=a, mapping_id=first.id, note="ok")
    second = service.remap(db, actor=a, source_record_id="R1",
                           canonical_id="NMC-2", note="reclassified")

    rows = db.scalars(select(Mapping).where(Mapping.source_record_id == "R1")).all()
    assert len(rows) == 2, "the old claim must survive, not be overwritten"
    old = next(r for r in rows if r.id == first.id)
    assert old.status is MappingStatus.SUPERSEDED
    assert old.effective_to is not None
    assert old.superseded_by == second.id
    assert second.effective_to is None


def test_as_of_answers_what_a_code_meant_earlier(db):
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    first = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                            confidence=0.9, evidence={}, engine_decision="MATCH")
    service.approve(db, actor=a, mapping_id=first.id, note="ok")
    midpoint = utcnow()
    service.remap(db, actor=a, source_record_id="R1", canonical_id="NMC-2", note="x")

    assert service.as_of(db, "R1", midpoint).canonical_id == "NMC-1"
    assert service.as_of(db, "R1", utcnow()).canonical_id == "NMC-2"


# ── the certificate chain ──────────────────────────────────────────────────

def test_every_decision_is_certified_and_chained(db):
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={"rows": []}, engine_decision="MATCH")
    service.approve(db, actor=a, mapping_id=m.id, note="ok")

    decs = db.scalars(select(Decision).order_by(Decision.seq)).all()
    assert [d.kind.value for d in decs] == ["PROPOSE", "APPROVE"]
    assert decs[0].prev_hash == ""              # genesis
    assert decs[1].prev_hash == decs[0].hash    # linked
    # the scope held at that moment is frozen, not looked up later
    assert decs[1].actor_scope["commodity"] == ["fastener"]
    assert decs[1].gazetteer_version and decs[1].model_version


def test_chain_verification_detects_tampering(db):
    """An audit feature nobody can check is decoration."""
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    service.approve(db, actor=a, mapping_id=m.id, note="ok")
    assert service.verify_chain(db)["ok"] is True

    # edit a certificate the way someone covering their tracks would
    first = db.scalars(select(Decision).order_by(Decision.seq)).first()
    first.hash = "0" * 64
    db.flush()
    assert service.verify_chain(db)["ok"] is False


def test_rejection_must_state_a_reason(db):
    a = _user(db, "a", Role.REVIEWER, "CPSE-A", ["fastener"])
    m = service.propose(db, actor=a, source_record_id="R1", canonical_id="NMC-1",
                        confidence=0.9, evidence={}, engine_decision="MATCH")
    with pytest.raises(Denied):
        service.reject(db, actor=a, mapping_id=m.id, note="")
