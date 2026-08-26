"""
The three demo moments, as executable tests.

If any of these fail, tomorrow's demo fails. They run without the embedding model so
they stay fast and deterministic in CI; the dense channel only affects ranking, never
the veto, and that separation is itself worth asserting.
"""
from __future__ import annotations

import pytest

from src.nmc.match.engine import MatchingEngine
from src.nmc.types import Decision, MaterialRecord, Verdict


@pytest.fixture(scope="module")
def engine() -> MatchingEngine:
    e = MatchingEngine(use_embeddings=False)
    e.index([
        MaterialRecord("R1", "SS HEX BOLT M10 X 50", org="CPSE-A", org_code="MAT-78291"),
        MaterialRecord("R2", "STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM", org="CPSE-B", org_code="BLT-10922"),
        MaterialRecord("R3", "SS HEX BOLT M10 X 75", org="CPSE-C", org_code="XJ-55291"),
        MaterialRecord("R4", "NUT HEX SS M10", org="CPSE-D", org_code="440918"),
        MaterialRecord("R5", "MS HEX BOLT M10 X 50", org="CPSE-B", org_code="BLT-11001"),
        MaterialRecord("R6", "BOLT HEX SS M10*50", org="CPSE-D", org_code="440919"),
    ])
    return e


def _pair(engine: MatchingEngine, a: str, b: str):
    return engine.explain(engine.get(a), engine.get(b))


# --- DEMO 1: same material, different description ------------------------------

def test_demo1_same_material_different_wording(engine):
    """`SS HEX BOLT M10 X 50` and `STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM` are one material."""
    ex = _pair(engine, "R1", "R2")
    assert ex.decision is Decision.MATCH, ex.to_dict()
    assert ex.critical_veto is False
    assert ex.attribute_agreement == 1.0
    # and the evidence table actually contains the comparison, not just a number
    codes = {r.code: r for r in ex.rows}
    assert codes["THREAD_DIA"].verdict is Verdict.AGREE
    assert codes["LENGTH"].verdict is Verdict.AGREE
    assert codes["MATERIAL"].verdict is Verdict.AGREE


def test_demo1_separator_variant_also_matches(engine):
    """`BOLT HEX SS M10*50` is the same material written a third way."""
    ex = _pair(engine, "R1", "R6")
    assert ex.decision is Decision.MATCH
    assert ex.critical_veto is False


# --- DEMO 2: the money shot ----------------------------------------------------

def test_demo2_length_mismatch_is_vetoed(engine):
    """
    M10x50 vs M10x75. Nearly identical text, different material.

    This is the assertion the whole architecture exists to satisfy.
    """
    ex = _pair(engine, "R1", "R3")
    assert ex.critical_veto is True, "length mismatch MUST veto"
    assert ex.decision is Decision.DISTINCT
    assert ex.confidence == 0.0, "a vetoed pair scores zero, not merely low"
    assert "Length" in ex.veto_reason and "50" in ex.veto_reason and "75" in ex.veto_reason

    row = next(r for r in ex.rows if r.code == "LENGTH")
    assert row.verdict is Verdict.DISAGREE
    assert row.vetoed is True
    # everything else still agrees — that is what makes it a hard negative
    assert next(r for r in ex.rows if r.code == "THREAD_DIA").verdict is Verdict.AGREE
    assert next(r for r in ex.rows if r.code == "MATERIAL").verdict is Verdict.AGREE


def test_demo2_veto_survives_high_text_similarity(engine):
    """
    The veto must not be a weight that a strong text signal can outvote.

    Even if we hand the scorer a semantic similarity of 1.0, the pair stays DISTINCT.
    """
    ex = engine.explain(engine.get("R1"), engine.get("R3"), semantic=1.0, lexical=1.0)
    assert ex.decision is Decision.DISTINCT
    assert ex.confidence == 0.0


def test_bolt_is_not_a_nut(engine):
    """Item-type disagreement vetoes before any dimension is compared."""
    ex = _pair(engine, "R1", "R4")
    assert ex.critical_veto is True
    assert ex.decision is Decision.DISTINCT
    assert "Item type" in ex.veto_reason


def test_different_material_is_vetoed(engine):
    """Stainless vs mild steel is a different material, not a variant."""
    ex = _pair(engine, "R1", "R5")
    assert ex.critical_veto is True
    assert ex.decision is Decision.DISTINCT
    assert "Material" in ex.veto_reason


# --- ranking -------------------------------------------------------------------

def test_match_ranks_true_duplicate_first_and_keeps_the_veto(engine):
    """
    Retrieval surfaces the near-miss; scoring puts it last with the reason attached.

    Vetoed candidates are deliberately returned rather than filtered out — showing the
    rejection is more persuasive than hiding it.
    """
    results = engine.match(engine.get("R1"), top_k=5)
    assert results, "retrieval returned nothing"
    assert results[0].decision is Decision.MATCH
    assert results[0].record.id in {"R2", "R6"}

    vetoed = [r for r in results if r.explanation.critical_veto]
    assert any(r.record.id == "R3" for r in vetoed), "M10x75 should be retrieved and vetoed"
    # every vetoed candidate sorts after every non-vetoed one
    flags = [r.explanation.critical_veto for r in results]
    assert flags == sorted(flags), "vetoed candidates must rank last"


# --- DEMO 3: check-before-create -----------------------------------------------

def test_demo3_check_before_create_finds_existing_material(engine):
    """A storekeeper types a new description; the platform recognises it."""
    probe, results = engine.check_before_create("STAINLESS STEEL HEX BOLT 10MM 50MM", org="CPSE-E")
    assert probe.item_name == "BOLT, MACHINE"
    assert results, "no candidates returned"
    top = results[0]
    assert top.decision is Decision.MATCH, top.explanation.to_dict()
    assert top.record.id in {"R1", "R2", "R6"}


def test_demo3_genuinely_new_material_is_not_forced_to_match(engine):
    """
    The system must be willing to say "this is new".

    Forcing a match is the failure mode that corrupts a national master.
    """
    _, results = engine.check_before_create("SS HEX BOLT M24 X 200")
    assert all(r.decision is not Decision.MATCH for r in results), \
        "an unseen size must not be reported as an existing material"


# --- safety --------------------------------------------------------------------

def test_unknown_attribute_never_vetoes():
    """A missing attribute is not evidence of difference."""
    e = MatchingEngine(use_embeddings=False)
    e.index([
        MaterialRecord("A", "SS HEX BOLT M10 X 50"),
        MaterialRecord("B", "SS HEX BOLT"),          # no dimensions stated at all
    ])
    ex = e.explain(e.get("A"), e.get("B"))
    assert ex.critical_veto is False, "unknown must never veto"
    assert ex.decision is Decision.REVIEW_REQUIRED, "insufficient evidence -> abstain, not match"
    assert any(r.verdict is Verdict.UNKNOWN for r in ex.rows)


def test_confidence_is_not_claimed_to_be_calibrated(engine):
    """We must not present an uncalibrated score as a probability."""
    ex = _pair(engine, "R1", "R2")
    d = ex.to_dict()
    assert 0.0 <= d["confidence"] <= 1.0
    assert "evidence" in d and len(d["evidence"]) > 0, "a score without evidence is not acceptable"
