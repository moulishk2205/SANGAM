"""
Populate an empty database.

The corpus used to be regenerated into RAM on every boot, which meant nothing a
user did could survive a restart. It is now generated once, written here, and
read from storage thereafter — the generator becomes a fixture rather than the
runtime.

Everything written is still synthetic and still labelled as such. Seeding does
not make the data real; it makes it persistent.

Idempotent: seeding an already-seeded database is a no-op, so it is safe to call
on every startup.
"""
from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..authz import hash_password
from ..demo.corpus import build_corpus
from ..extract.templates import ITEM_NAMES
from ..match.engine import MODEL_VERSION, MatchingEngine
from ..normalise.text import GAZETTEER_VERSION
from ..extract.templates import CONFIG_VERSION
from .models import (
    CanonicalMaterial, ItemClassRule, Mapping, MappingStatus, Organisation,
    Release, Role, SourceRecord, User,
)

# The four invented CPSEs, named generically so nobody mistakes them for real
# organisations. Matches the corpus generator's ORGS.
ORGS = [
    ("CPSE-A", "Refinery Division A", "MAT-"),
    ("CPSE-B", "Pipeline Division B", "BLT-"),
    ("CPSE-C", "Petrochemical West C", "XJ-"),
    ("CPSE-D", "Terminal East D", ""),
]

# Demo accounts. Passwords are hashed, never stored plain — but these are
# published credentials for a demonstration and must never be reused anywhere.
USERS = [
    # email, name, role, org, commodity scope, class certifications
    ("admin@sangam.gov.in",    "Registrar",        Role.ADMIN,     "CPSE-A", [], []),
    ("steward@sangam.gov.in",  "R. Iyer",          Role.STEWARD,   "CPSE-A", [], []),
    ("reviewer.a@sangam.gov.in", "S. Nair",        Role.REVIEWER,  "CPSE-A",
     ["fastener", "pipe", "flange"], ["PRESSURE"]),
    ("reviewer.b@sangam.gov.in", "M. Banerjee",    Role.REVIEWER,  "CPSE-B",
     ["fastener"], []),
    ("requester.a@sangam.gov.in", "K. Rao",        Role.REQUESTER, "CPSE-A", [], []),
]
DEMO_PASSWORD = "sangam-demo"

# The safety class lock, as configuration. OISD operates under the Ministry of
# Petroleum and Natural Gas and audits every Indian refinery on a 2-3 year
# cycle, which is what makes these classes worth barring from auto-approval.
CLASS_RULES = [
    ("GENERAL", "General service", [], False, False, ""),
    ("PRESSURE", "Pressure-retaining service",
     ["PRESSURE_CLASS", "MATERIAL", "NOMINAL_SIZE"], True, True, "ASME B16.5"),
    ("SOUR", "Sour service (H2S)",
     ["MATERIAL", "GRADE"], True, True, "NACE MR0175 / ISO 15156"),
    ("FIRED", "Fired-equipment service",
     ["MATERIAL", "SCHEDULE"], True, True, "OISD-STD-150"),
]

# Which item names sit in which class. Anything not named here is GENERAL.
_CLASS_BY_ITEM = {
    "VALVE": "PRESSURE",
    "FLANGE, PIPE": "PRESSURE",
    "PIPE": "FIRED",
    "GASKET": "PRESSURE",
}


def is_seeded(db: DbSession) -> bool:
    return (db.scalar(select(func.count()).select_from(SourceRecord)) or 0) > 0


def seed(db: DbSession, *, limit_specs: int = 600, variants: int = 3) -> dict:
    """Write the demonstration corpus and the accounts that operate on it."""
    if is_seeded(db):
        return {"seeded": False, "reason": "already populated"}

    for oid, name, prefix in ORGS:
        if db.get(Organisation, oid) is None:
            db.add(Organisation(id=oid, name=name, code_prefix=prefix))
    db.flush()

    for item_class, label, extra, bars, cert, basis in CLASS_RULES:
        if db.get(ItemClassRule, item_class) is None:
            db.add(ItemClassRule(item_class=item_class, label=label,
                                 extra_critical=extra, bars_auto_match=bars,
                                 requires_certification=cert, basis=basis))

    for email, name, role, org, scope, certs in USERS:
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(User(
                id=f"usr-{secrets.token_hex(6)}", email=email, name=name, role=role,
                org_id=org, commodity_scope=scope, class_certifications=certs,
                password_hash=hash_password(DEMO_PASSWORD),
            ))

    db.add(Release(
        id=f"rel-{secrets.token_hex(6)}",
        gazetteer_version=GAZETTEER_VERSION, template_version=CONFIG_VERSION,
        model_version=MODEL_VERSION, notes="Initial seed",
    ))
    db.flush()

    # ── the corpus ─────────────────────────────────────────────────────────
    # The engine runs once here to derive normalised text and attributes so the
    # catalogue can be listed without loading the model. Embeddings are off:
    # seeding needs the deterministic layers, not retrieval.
    records, truth = build_corpus(limit_specs=limit_specs, variants_per_spec=variants)
    engine = MatchingEngine(use_embeddings=False)
    for r in records:
        engine.prepare(r)

    # One canonical identity per spec key. Correct by construction, which is the
    # only honest way to claim a label on generated data.
    groups: dict[str, list] = {}
    for r in records:
        groups.setdefault(truth[r.id], []).append(r)

    canon_by_key: dict[str, str] = {}
    for key, recs in sorted(groups.items()):
        head = recs[0]
        seq = 18426 + sum(ord(c) for c in key) % 60000
        nmc = f"NMC-{seq:08d}"
        while db.get(CanonicalMaterial, nmc) is not None or nmc in canon_by_key.values():
            seq += 1
            nmc = f"NMC-{seq:08d}"
        item = head.item_name or "UNCLASSIFIED"
        db.add(CanonicalMaterial(
            id=nmc, item_name=item, canonical_text=head.normalised,
            attributes={c: str(a.value) for c, a in head.attributes.items() if a.known},
            item_class=_CLASS_BY_ITEM.get(item, "GENERAL"),
        ))
        canon_by_key[key] = nmc
    db.flush()

    for r in records:
        db.add(SourceRecord(
            id=r.id, org_id=r.org or "CPSE-A", org_code=r.org_code,
            raw_description=r.raw_description, normalised=r.normalised,
            item_name=r.item_name or "",
            attributes={c: str(a.value) for c, a in r.attributes.items() if a.known},
            provenance=r.provenance,
        ))
    db.flush()

    # Seeded mappings are APPROVED, because in this corpus the grouping is
    # correct by construction rather than by anyone's judgement. Each carries
    # decided_by_engine="SEED" so it is never mistaken for an adjudicated
    # decision — there is no certificate for these, and there should not be:
    # nobody decided them.
    for r in records:
        db.add(Mapping(
            id=f"map-{secrets.token_hex(8)}", source_record_id=r.id,
            canonical_id=canon_by_key[truth[r.id]],
            status=MappingStatus.APPROVED, confidence=1.0,
            decided_by_engine="SEED",
        ))
    db.commit()

    return {
        "seeded": True,
        "organisations": len(ORGS),
        "users": len(USERS),
        "class_rules": len(CLASS_RULES),
        "canonical_materials": len(canon_by_key),
        "source_records": len(records),
        "item_names": len(ITEM_NAMES),
    }
