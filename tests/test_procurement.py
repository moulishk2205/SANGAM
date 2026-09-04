"""
Gap 3 — historical procurement analytics.

The assertions that matter are the arithmetic ones: that spend foots, that
demand is attributed through the LIVE mapping, that aggregation widens only
where equivalence permits, and that the opportunity figure is exactly the
formula it claims to be rather than a modelled percentage.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.nmc import procure
from src.nmc.db.models import (
    Base, CanonicalMaterial, Mapping, MappingStatus, Organisation,
    ProcurementRecord, SourceRecord,
)

DAY = datetime(2025, 4, 17, tzinfo=timezone.utc)


def _bolt(grade: str) -> dict:
    return {"ITEM_NAME": "BOLT, MACHINE", "MATERIAL": "STAINLESS_STEEL",
            "THREAD_DIA": "10 mm", "LENGTH": "50 mm", "GRADE": grade}


@pytest.fixture()
def db():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, expire_on_commit=False)()
    for oid in ("CPSE-A", "CPSE-B"):
        s.add(Organisation(id=oid, name=oid))

    # Two DISTINCT identities that are functionally equivalent in GENERAL
    # service: same size, A4-80 covers A2-70.
    s.add(CanonicalMaterial(id="NMC-A", item_name="BOLT, MACHINE",
                            canonical_text="A2-70 bolt", standard_description="BOLT A2-70",
                            attributes=_bolt("A2-70"), family="fastener", item_class="GENERAL"))
    s.add(CanonicalMaterial(id="NMC-B", item_name="BOLT, MACHINE",
                            canonical_text="A4-80 bolt", standard_description="BOLT A4-80",
                            attributes=_bolt("A4-80"), family="fastener", item_class="GENERAL"))
    # A third that differs dimensionally, so it must never join the group.
    s.add(CanonicalMaterial(id="NMC-C", item_name="BOLT, MACHINE",
                            canonical_text="A2-70 long", standard_description="BOLT A2-70 LONG",
                            attributes={**_bolt("A2-70"), "LENGTH": "75 mm"},
                            family="fastener", item_class="GENERAL"))
    for rid, org, cid in (("R-A", "CPSE-A", "NMC-A"), ("R-B", "CPSE-B", "NMC-B"),
                          ("R-C", "CPSE-B", "NMC-C")):
        s.add(SourceRecord(id=rid, org_id=org, org_code=f"C-{rid}",
                           raw_description=rid, item_name="BOLT, MACHINE"))
        s.add(Mapping(id=f"m-{rid}", source_record_id=rid, canonical_id=cid,
                      status=MappingStatus.APPROVED, confidence=1.0))

    # CPSE-A: 10,000 @ ₹100.00   CPSE-B: 15,000 @ ₹105.00
    s.add(ProcurementRecord(id="po-1", org_id="CPSE-A", source_record_id="R-A",
                            quantity=10000, unit_price_paise=10000,
                            line_value_paise=10000 * 10000, ordered_on=DAY,
                            service_class="GENERAL"))
    s.add(ProcurementRecord(id="po-2", org_id="CPSE-B", source_record_id="R-B",
                            quantity=15000, unit_price_paise=10500,
                            line_value_paise=15000 * 10500, ordered_on=DAY,
                            service_class="GENERAL"))
    s.add(ProcurementRecord(id="po-3", org_id="CPSE-B", source_record_id="R-C",
                            quantity=500, unit_price_paise=9000,
                            line_value_paise=500 * 9000, ordered_on=DAY,
                            service_class="GENERAL"))
    s.commit()
    yield s
    s.close()


def test_demand_is_attributed_through_the_live_mapping(db):
    d = procure.load_demand(db)
    assert set(d) == {"NMC-A", "NMC-B", "NMC-C"}
    assert d["NMC-A"].quantity == 10000
    assert d["NMC-A"].by_org["CPSE-A"]["qty"] == 10000


def test_spend_foots(db):
    s = procure.summary(db)
    expected = (10000 * 10000 + 15000 * 10500 + 500 * 9000) / 100
    assert s["spend"] == pytest.approx(expected)
    assert s["lines"] == 3
    assert s["organisations"] == 2


def test_summary_labels_its_data_as_synthetic(db):
    assert "SYNTHETIC" in procure.summary(db)["provenance"]


def test_aggregation_combines_equivalent_demand(db):
    r = procure.aggregation(db, service_class="GENERAL")
    assert r["aggregation_opportunities"] == 1
    g = r["groups"][0]
    # 10,000 + 15,000 — and NOT the 500 of the dimensionally different bolt.
    assert g["aggregatable_quantity"] == 25000
    assert {m["canonical_id"] for m in g["members"]} == {"NMC-A", "NMC-B"}
    assert set(g["organisations"]) == {"CPSE-A", "CPSE-B"}


def test_dimensionally_different_material_never_joins_a_group(db):
    g = procure.aggregation(db, service_class="GENERAL")["groups"][0]
    assert "NMC-C" not in {m["canonical_id"] for m in g["members"]}


def test_opportunity_is_exactly_the_stated_formula(db):
    """
    SUM over buyers of qty x (paid - best observed). Nothing modelled.
    A paid 10000, B paid 10500, best is 10000 -> 15000 x 500 paise = ₹75,000.
    """
    g = procure.aggregation(db, service_class="GENERAL")["groups"][0]
    assert g["best_observed_unit_price"] == 100.0
    assert g["estimated_opportunity"] == pytest.approx(75000.0)
    assert "no saving is promised" in g["basis"]


def test_safety_critical_service_yields_no_aggregation(db):
    for svc in ("SOUR", "FIRED"):
        r = procure.aggregation(db, service_class=svc)
        assert r["aggregation_opportunities"] == 0, f"{svc} must not aggregate"


def test_single_organisation_demand_is_not_an_opportunity(db):
    """A CPSE's own duplicates are a data-quality finding, not aggregation."""
    r = procure.aggregation(db, service_class="GENERAL", min_organisations=3)
    assert r["aggregation_opportunities"] == 0


def test_price_trend_reports_the_spread(db):
    t = procure.price_trend(db, "NMC-A")
    assert t["orders"] == 1
    assert t["min_unit_price"] == 100.0
