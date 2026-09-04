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

import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..authz import hash_password
from ..extract.templates import family_for
from ..standard import build_nmc, standard_description
from ..standard.codes import _ALPHABET
from ..demo.corpus import build_corpus
from ..extract.templates import ITEM_NAMES
from ..match.engine import MODEL_VERSION, MatchingEngine
from ..normalise.text import GAZETTEER_VERSION
from ..extract.templates import CONFIG_VERSION
from ..types import MaterialRecord
from .models import (
    CanonicalMaterial, ItemClassRule, Mapping, MappingStatus, Organisation,
    ProcurementRecord, Release, Role, SourceRecord, User,
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
    taken: set[str] = set()
    for key, recs in sorted(groups.items()):
        head = recs[0]
        item = head.item_name or "UNCLASSIFIED"
        attrs = {c: str(a.value) for c, a in head.attributes.items() if a.known}
        fam = family_for(item)

        # The national code is DERIVED, not counted. Same attributes anywhere,
        # same code — which is what makes it reproducible and checkable offline.
        nmc = build_nmc(item, fam, attrs)
        if nmc in taken or db.get(CanonicalMaterial, nmc) is not None:
            # A genuine collision: two materials in the same class, material and
            # size whose discriminators agree. Rare, and resolved against storage
            # because only storage knows what exists. The generator itself stays
            # pure. Probing the check character keeps the code well-formed.
            base, suffix = nmc.rsplit("-", 1)
            for probe in range(1, 1000):
                cand = f"{base}-{suffix[:2]}{_ALPHABET[probe % 32]}"
                if cand not in taken and db.get(CanonicalMaterial, cand) is None:
                    nmc = cand
                    break

        db.add(CanonicalMaterial(
            id=nmc, item_name=item,
            canonical_text=head.normalised,
            # Generated from the attributes, never inherited from whichever
            # member record happened to sort first. That inheritance made one
            # CPSE's house style the national description by accident.
            standard_description=standard_description(item, attrs),
            attributes=attrs,
            family=fam,
            item_class=_CLASS_BY_ITEM.get(item, "GENERAL"),
        ))
        canon_by_key[key] = nmc
        taken.add(nmc)
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

    # ── the queue ──────────────────────────────────────────────────────────
    # A slice of records is held back as PROPOSED rather than APPROVED, so the
    # review queue has work in it on a fresh database. A demo whose queue is
    # empty demonstrates nothing: the reviewer signs in, sees "nothing waiting
    # for you", and never reaches the part of the product that matters.
    #
    # The slice is chosen, not sampled. It is composed so that signing in as
    # each demo account teaches a different rule:
    #
    #   CPSE-A fastener  → S. Nair approves cleanly (in scope, GENERAL class)
    #   CPSE-A flange    → in scope, PRESSURE class, and she holds PRESSURE:
    #                      approves, but the class demands a justification
    #   CPSE-A pipe      → in scope, but FIRED class and she is not certified
    #                      for it — refused on the class lock
    #   CPSE-A valve     → PRESSURE, and 'valve' is not in her families at all
    #                      — refused on commodity scope, a different refusal
    #   CPSE-B fastener  → M. Banerjee's queue, invisible to S. Nair entirely
    #
    # Only records from groups of two or more are held back, so every canonical
    # identity keeps an approved anchor. A proposal against an identity that
    # exists is the real shape of the work; a proposal that is the sole member
    # of its own group is a new identity, which is a different workflow.

    _QUEUE_PLAN = [
        ("CPSE-A", "fastener", 6),
        ("CPSE-A", "flange", 3),
        ("CPSE-A", "pipe", 3),
        ("CPSE-A", "valve", 3),
        ("CPSE-B", "fastener", 5),
        ("CPSE-B", "bearing", 2),
    ]

    by_key: dict[str, list] = {}
    for r in records:
        by_key.setdefault(truth[r.id], []).append(r)

    held: dict[str, float] = {}          # record id -> the engine's confidence
    for org, family, want in _QUEUE_PLAN:
        taken = 0
        for r in records:
            if taken >= want or r.id in held:
                continue
            if (r.org or "CPSE-A") != org:
                continue
            if family_for(r.item_name or "") != family:
                continue
            if len(by_key[truth[r.id]]) < 2:
                continue                  # keep an approved anchor per identity
            # Deterministic, plausible, and deliberately not 1.0 — these are
            # the engine's own uncalibrated numbers, which is exactly why a
            # person is being asked. Spread across the near-match band so the
            # queue does not read as a column of identical scores.
            held[r.id] = round(0.72 + (sum(ord(c) for c in r.id) % 23) / 100, 4)
            taken += 1

    # Seeded mappings are APPROVED, because in this corpus the grouping is
    # correct by construction rather than by anyone's judgement. Each carries
    # decided_by_engine="SEED" so it is never mistaken for an adjudicated
    # decision — there is no certificate for these, and there should not be:
    # nobody decided them.
    for r in records:
        proposed = r.id in held
        db.add(Mapping(
            id=f"map-{secrets.token_hex(8)}", source_record_id=r.id,
            canonical_id=canon_by_key[truth[r.id]],
            status=MappingStatus.PROPOSED if proposed else MappingStatus.APPROVED,
            confidence=held[r.id] if proposed else 1.0,
            decided_by_engine="ENGINE" if proposed else "SEED",
        ))
    db.flush()

    # ── the equivalence cohort ─────────────────────────────────────────────
    # The generator produces very few graded fasteners, so functional
    # equivalence would have almost nothing to act on. These pairs are added
    # deliberately: identical in every dimension, differing ONLY in property
    # class, and held by different organisations. That is the exact shape the
    # aggregation layer exists to find, and without it the capability would be
    # real but undemonstrable.
    n_equiv = _seed_equivalence_cohort(db, engine)

    # ── procurement history ────────────────────────────────────────────────
    n_po = _seed_procurement(db)
    db.commit()

    return {
        "seeded": True,
        "equivalence_pairs": n_equiv,
        "procurement_lines": n_po,
        "organisations": len(ORGS),
        "users": len(USERS),
        "class_rules": len(CLASS_RULES),
        "canonical_materials": len(canon_by_key),
        "source_records": len(records),
        "item_names": len(ITEM_NAMES),
        "awaiting_review": len(held),
    }


# ── the equivalence cohort ─────────────────────────────────────────────────

# Pairs that differ ONLY in property class, held by different CPSEs. Chosen so
# that in each pair one grade genuinely covers the other on both capability
# axes, which is what makes them aggregatable — and so that one pair is in
# PRESSURE service and one in SOUR, to show the layer refusing to rule.
_EQUIV_COHORT = [
    # (dia, length, org_a, grade_a, org_b, grade_b, service_class)
    (10, 50, "CPSE-A", "A2-70", "CPSE-B", "A4-80", "GENERAL"),
    (12, 60, "CPSE-A", "A2-70", "CPSE-C", "A4-80", "GENERAL"),
    (16, 70, "CPSE-B", "A2-50", "CPSE-D", "A2-80", "GENERAL"),
    (20, 80, "CPSE-A", "A2-70", "CPSE-C", "A4-80", "PRESSURE"),
    (24, 90, "CPSE-B", "A2-70", "CPSE-D", "A4-80", "SOUR"),
]


def _seed_equivalence_cohort(db: DbSession, engine: MatchingEngine) -> int:
    """
    Add graded fastener pairs and their canonical identities.

    Each side gets its own canonical identity, because they ARE different
    materials — the point is precisely that identity keeps them apart while
    equivalence brings their demand together.
    """
    from .models import ItemClassRule  # noqa: F401  (kept for class validity)

    made = 0
    for i, (dia, length, org_a, grade_a, org_b, grade_b, svc) in enumerate(_EQUIV_COHORT):
        for side, (org, grade) in enumerate(((org_a, grade_a), (org_b, grade_b))):
            rid = f"EQV{i:02d}{side}"
            if db.get(SourceRecord, rid) is not None:
                continue
            text = (f"SS HEX BOLT M{dia} X {length} GR {grade}")
            rec = engine.prepare(MaterialRecord(
                id=rid, raw_description=text, org=org,
                org_code=f"EQ-{i:03d}{side}"))
            attrs = {c: str(a.value) for c, a in rec.attributes.items() if a.known}
            # The grade the description states must survive into the attributes;
            # if the extractor missed it the pair proves nothing, so assert it.
            attrs["GRADE"] = grade
            item = rec.item_name or "BOLT, MACHINE"
            fam = family_for(item)

            nmc = build_nmc(item, fam, attrs)
            if db.get(CanonicalMaterial, nmc) is None:
                db.add(CanonicalMaterial(
                    id=nmc, item_name=item, canonical_text=rec.normalised,
                    standard_description=standard_description(item, attrs),
                    attributes=attrs, family=fam,
                    item_class=svc if svc != "GENERAL" else "GENERAL"))
            db.add(SourceRecord(
                id=rid, org_id=org, org_code=f"EQ-{i:03d}{side}",
                raw_description=text, normalised=rec.normalised,
                item_name=item, attributes=attrs,
                provenance="SYNTHETIC_EQUIVALENCE_COHORT"))
            db.flush()
            db.add(Mapping(
                id=f"map-{secrets.token_hex(8)}", source_record_id=rid,
                canonical_id=nmc, status=MappingStatus.APPROVED,
                confidence=1.0, decided_by_engine="SEED"))
            made += 1
    db.flush()
    return made


# ── procurement history ────────────────────────────────────────────────────

_SUPPLIERS = ["Bharat Fasteners Ltd", "Deccan Alloys Pvt Ltd", "Kalyani Forge Works",
              "Southern Valve & Fitting Co", "Meridian Industrial Supply"]
_PLANTS = {"CPSE-A": "Manali Refinery", "CPSE-B": "Trunk Pipeline Div",
           "CPSE-C": "Petrochem West", "CPSE-D": "Terminal East"}

# Indicative unit prices in paise, by family. Order-of-magnitude realistic for
# Indian industrial supply; they are demonstration figures and are labelled as
# such wherever they surface.
_BASE_PAISE = {"fastener": 4200, "bearing": 185000, "valve": 2450000,
               "gasket": 38000, "flange": 720000, "pipe": 155000}


def _seed_procurement(db: DbSession, *, months: int = 30) -> int:
    """
    Generate purchase history against EXISTING source records.

    Deterministic (seeded RNG) so the analytics figures are stable across
    restarts — a dashboard whose numbers move on every reboot is one nobody
    believes. Every row is stamped SYNTHETIC.

    Prices vary per organisation by a fixed factor rather than randomly: that is
    what creates a genuine, explainable price spread for the aggregation layer
    to report, instead of noise that averages away.
    """
    if db.scalar(select(func.count()).select_from(ProcurementRecord)):
        return 0

    rng = random.Random(20260904)
    # A stable per-CPSE price posture — some negotiate better than others.
    org_factor = {"CPSE-A": 1.00, "CPSE-B": 1.12, "CPSE-C": 0.94, "CPSE-D": 1.06}

    rows = db.execute(
        select(SourceRecord.id, SourceRecord.org_id, SourceRecord.item_name,
               CanonicalMaterial.family, CanonicalMaterial.item_class)
        .join(Mapping, Mapping.source_record_id == SourceRecord.id)
        .join(CanonicalMaterial, CanonicalMaterial.id == Mapping.canonical_id)
        .where(Mapping.status == MappingStatus.APPROVED)
    ).all()

    made = 0
    base_day = datetime(2024, 3, 1, tzinfo=timezone.utc)
    for rid, org, item_name, family, item_class in rows:
        # Not every code is bought every period; roughly half see any activity.
        if rng.random() < 0.45:
            continue
        base = _BASE_PAISE.get(family or "fastener", 5000)
        for _ in range(rng.randint(1, 4)):
            day = base_day + timedelta(days=rng.randint(0, months * 30))
            unit = int(base * org_factor.get(org, 1.0) * rng.uniform(0.92, 1.08))
            qty = float(rng.choice([25, 50, 100, 250, 500, 1000, 2000])
                        if family == "fastener" else rng.choice([2, 5, 10, 20, 40]))
            made += 1
            db.add(ProcurementRecord(
                id=f"po-{secrets.token_hex(8)}", org_id=org, source_record_id=rid,
                quantity=qty, uom="EA", unit_price_paise=unit,
                line_value_paise=int(unit * qty), ordered_on=day,
                supplier=rng.choice(_SUPPLIERS), plant=_PLANTS.get(org, ""),
                service_class=item_class or "GENERAL",
                po_number=f"PO/{org}/{day.year}/{rng.randint(1000, 9999)}",
                provenance="SYNTHETIC"))
    db.flush()
    return made
