"""
Tests for the five closed gaps.

The load-bearing ones are the refusals: that equivalence never widens on a
dimensional difference, that it declines to rule in SOUR and FIRED service, and
that a bad import writes nothing. Those are the properties a procurement officer
is trusting, and they are the ones that would fail silently if broken.
"""
from __future__ import annotations

import pytest

from src.nmc.equivalence import Equivalence, compare
from src.nmc.integration import SCHEMAS, describe_schemas, validate_rows
from src.nmc.standard import build_nmc, standard_description, validate_nmc
from src.nmc.standard.codes import FSC, parse_nmc

BOLT = "BOLT, MACHINE"


def bolt(grade="A2-70", material="STAINLESS_STEEL", dia="10 mm", length="50 mm"):
    return {"ITEM_NAME": BOLT, "MATERIAL": material, "THREAD_DIA": dia,
            "LENGTH": length, "GRADE": grade}


# ── GAP 1: functional equivalence ──────────────────────────────────────────

def test_identical_attributes_are_identical():
    r = compare(BOLT, bolt(), BOLT, bolt(), "GENERAL")
    assert r.verdict is Equivalence.IDENTICAL
    assert r.aggregatable


def test_different_grade_is_still_a_distinct_identity_but_equivalent():
    """The whole point: distinct materials, aggregatable demand."""
    r = compare(BOLT, bolt("A2-70"), BOLT, bolt("A4-80"), "GENERAL")
    assert r.verdict is Equivalence.FUNCTIONALLY_EQUIVALENT
    assert r.aggregatable
    assert r.covering == "right", "A4-80 covers A2-70, not the reverse"
    assert any(d.code == "GRADE" for d in r.deltas)


def test_substitution_is_directional():
    """Reversing the arguments must reverse the covering side, never symmetrise."""
    a = compare(BOLT, bolt("A2-70"), BOLT, bolt("A4-80"), "GENERAL")
    b = compare(BOLT, bolt("A4-80"), BOLT, bolt("A2-70"), "GENERAL")
    assert a.covering == "right" and b.covering == "left"


def test_dimensional_difference_is_never_equivalent():
    """Equivalence must not be inferred from dimensional similarity."""
    r = compare(BOLT, bolt(length="50 mm"), BOLT, bolt(length="75 mm"), "GENERAL")
    assert r.verdict is Equivalence.NOT_EQUIVALENT
    assert not r.aggregatable
    assert any(d.kind == "interface" and d.code == "LENGTH" for d in r.deltas)


def test_neither_covers_when_each_is_better_on_a_different_axis():
    """Alloy steel wins strength, stainless wins corrosion. Neither substitutes."""
    r = compare(BOLT, bolt("A2-70", "STAINLESS_STEEL"),
                BOLT, bolt("10.9", "ALLOY_STEEL"), "GENERAL")
    assert r.verdict is Equivalence.NOT_EQUIVALENT
    assert not r.aggregatable


@pytest.mark.parametrize("service", ["SOUR", "FIRED"])
def test_safety_critical_service_refuses_to_rule(service):
    r = compare(BOLT, bolt("A2-70"), BOLT, bolt("A4-80"), service)
    assert r.verdict is Equivalence.UNDETERMINED
    assert not r.aggregatable, "an undetermined verdict must never aggregate"
    assert "MR0175" in r.summary or "OISD" in r.summary


def test_different_item_type_is_never_equivalent():
    r = compare(BOLT, bolt(), "NUT, PLAIN, HEXAGON", bolt(), "GENERAL")
    assert r.verdict is Equivalence.NOT_EQUIVALENT


def test_unknown_grade_blocks_rather_than_guesses():
    r = compare(BOLT, bolt("A2-70"), BOLT, bolt("ZZ-99"), "GENERAL")
    assert r.verdict is Equivalence.NOT_EQUIVALENT
    assert any("capability table" in d.reason for d in r.deltas)


# ── GAP 2: intelligent national code ───────────────────────────────────────

def test_code_is_deterministic():
    assert build_nmc(BOLT, "fastener", bolt()) == build_nmc(BOLT, "fastener", bolt())


def test_code_carries_classification():
    code = build_nmc(BOLT, "fastener", bolt())
    p = parse_nmc(code)
    assert p is not None
    assert p.fsc == FSC[BOLT] == "5306"
    assert p.material == "SS"
    assert p.size_mm == 10.0


def test_code_validates_and_catches_a_typo():
    code = build_nmc(BOLT, "fastener", bolt())
    assert validate_nmc(code)[0] is True
    wrong = code[:-1] + ("Z" if code[-1] != "Z" else "Y")
    assert validate_nmc(wrong)[0] is False


def test_different_materials_get_different_codes():
    codes = {
        build_nmc(BOLT, "fastener", bolt(grade=g, dia=d))
        for g in ("A2-70", "A4-80", "8.8") for d in ("10 mm", "12 mm", "16 mm")
    }
    assert len(codes) == 9, "distinct specifications collided"


def test_legacy_code_still_validates():
    ok, reason = validate_nmc("NMC-00022499")
    assert ok and "Legacy" in reason


def test_malformed_code_is_rejected():
    for bad in ("", "NMC", "NMC-XX-YY", "5306-SS-0100-K7Q", "NMC-530-SS-0100-K7Q"):
        assert validate_nmc(bad)[0] is False


# ── GAP 4: generated standard description ──────────────────────────────────

def test_description_is_deterministic_and_source_independent():
    """
    Two records worded completely differently must produce ONE description,
    because the description is generated from the attributes and not inherited.
    """
    a = standard_description(BOLT, bolt())
    b = standard_description(BOLT, dict(reversed(list(bolt().items()))))
    assert a == b
    assert a.startswith("BOLT, MACHINE")
    assert "STAINLESS STEEL" in a and "M10 × 50" in a and "A2-70" in a


def test_description_omits_missing_attributes_rather_than_leaving_a_gap():
    d = standard_description(BOLT, {"ITEM_NAME": BOLT, "MATERIAL": "MILD_STEEL"})
    assert "—  —" not in d and not d.rstrip().endswith("—")
    assert "MILD STEEL" in d


def test_description_normalises_material_vocabulary():
    assert "GALVANISED IRON" in standard_description(
        BOLT, {"ITEM_NAME": BOLT, "MATERIAL": "GALVANISED_IRON", "THREAD_DIA": "8 mm"})


# ── GAP 5: integration schemas ─────────────────────────────────────────────

def test_schemas_declare_sap_field_mappings():
    d = describe_schemas()
    assert d["sap_status"] == "SAP_INTEGRATION_READY"
    assert "No live SAP connection exists" in d["sap_status_note"]
    for s in SCHEMAS.values():
        mapped = [c for c in s.columns if c.sap_field]
        assert mapped, f"{s.key} declares no SAP field mapping"


def test_valid_rows_pass():
    rep = validate_rows("procurement_history_import", [
        {"org_id": "CPSE-A", "material_code": "MAT-1", "quantity": "100",
         "unit_price": "42.50", "order_date": "2025-04-17"},
    ])
    assert rep.ok and rep.valid_rows == 1


def test_invalid_rows_are_reported_per_row_and_column():
    rep = validate_rows("procurement_history_import", [
        {"org_id": "CPSE-A", "material_code": "M1", "quantity": "abc",
         "unit_price": "10", "order_date": "17/04/2025"},
        {"org_id": "", "material_code": "M2", "quantity": "-5",
         "unit_price": "10", "order_date": "2025-04-17", "service_class": "NOPE"},
    ])
    assert not rep.ok and rep.valid_rows == 0
    cols = {(e.row, e.column) for e in rep.errors}
    assert (1, "quantity") in cols and (1, "order_date") in cols
    assert (2, "org_id") in cols and (2, "quantity") in cols
    assert (2, "service_class") in cols


def test_a_row_with_any_error_is_rejected_whole():
    """A half-imported material record is a corrupted one."""
    rep = validate_rows("material_master_import", [
        {"org_id": "CPSE-A", "material_code": "M1", "description": "BOLT"},
        {"org_id": "CPSE-A", "material_code": "", "description": "NUT"},
    ])
    assert rep.valid_rows == 1 and len(rep.parsed) == 1


def test_unknown_schema_raises():
    with pytest.raises(KeyError):
        validate_rows("no_such_schema", [])
