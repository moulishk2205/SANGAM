"""
Tests for the learned layer.

The important one is `test_veto_survives_the_model`. Everything else here
protects accuracy; that one protects the guarantee the product is sold on, and
it is the test that should fail loudly if someone ever decides the veto would
make a useful feature.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from src.nmc.match.engine import MatchingEngine
from src.nmc.ml.dataset import Pairs, assert_no_leakage, split_identities
from src.nmc.ml.features import FEATURE_NAMES, featurise
from src.nmc.ml.metrics import brier, reliability, roc_auc
from src.nmc.ml.model import LearnedScorer, load_scorer
from src.nmc.ml.robustness import degrade
from src.nmc.ml.train import pick_thresholds
from src.nmc.types import MaterialRecord


@pytest.fixture(scope="module")
def engine() -> MatchingEngine:
    e = MatchingEngine(use_embeddings=False)
    e.index([
        MaterialRecord("R1", "SS HEX BOLT M10 X 50", org="CPSE-A", org_code="MAT-78291"),
        MaterialRecord("R2", "STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM", org="CPSE-B", org_code="BLT-10922"),
        MaterialRecord("R3", "SS HEX BOLT M10 X 75", org="CPSE-C", org_code="XJ-55291"),
        MaterialRecord("R5", "MS HEX BOLT M10 X 50", org="CPSE-B", org_code="BLT-11001"),
    ])
    return e


# --- the guarantee -------------------------------------------------------------

def test_veto_is_not_a_feature():
    """
    The veto must be structurally absent from the feature contract.

    A model that can see the veto can learn to overrule it. Keeping it out of
    FEATURE_NAMES makes that impossible rather than merely unlikely, so this
    asserts on the contract itself and not on a fitted model's behaviour.
    """
    for banned in ("veto", "critical_veto", "vetoed"):
        assert banned not in FEATURE_NAMES


def test_veto_survives_the_model(engine):
    """A vetoed pair reports exactly 0.0, whatever the features say."""
    if engine.scorer is None:
        pytest.skip("no trained scorer on disk")
    # M10x50 vs M10x75 — near-identical text, different length.
    ex = engine.explain(engine.get("R1"), engine.get("R3"))
    assert ex.critical_veto is True
    assert ex.confidence == 0.0
    assert ex.decision.value == "DISTINCT"
    # and the text really was similar enough to fool a similarity matcher
    assert max(ex.semantic_score, ex.lexical_score) >= 0.80


def test_veto_zeroes_every_row_regardless_of_features():
    """Directly: a hostile feature vector cannot buy a non-zero probability."""
    s = LearnedScorer(
        feature_names=list(FEATURE_NAMES),
        coef=np.ones(len(FEATURE_NAMES)) * 50.0,   # absurdly confident
        intercept=50.0,
        calib_x=np.array([0.0, 1.0]), calib_y=np.array([0.0, 1.0]),
        thresholds={"match": 0.9, "near": 0.7, "review": 0.4}, metadata={},
    )
    X = np.ones((4, len(FEATURE_NAMES)))
    p = s.probability(X, np.array([True, False, True, False]))
    assert list(p[[0, 2]]) == [0.0, 0.0]
    assert (p[[1, 3]] > 0.9).all()


def test_learned_path_still_abstains_on_unstated_criticals():
    """
    REGRESSION. The learned scorer asserted MATCH at p=0.97 on a description
    that states no dimensions at all.

    `SS HEX BOLT` leaves THREAD_DIA and LENGTH unstated, and both are CRITICAL.
    Attribute agreement is computed over what both sides mention, so a
    description that mentions almost nothing agrees with almost everything —
    and the training corpus always states its criticals, so the model never met
    the case and had no reason to learn caution. The deterministic path had
    always refused this; the learned path bypassed the rule until the gate was
    applied to it as well.
    """
    e = MatchingEngine(use_embeddings=False)
    e.index([MaterialRecord("A", "SS HEX BOLT M10 X 50"),
             MaterialRecord("B", "SS HEX BOLT")])
    ex = e.explain(e.get("A"), e.get("B"))
    assert ex.critical_veto is False, "unknown is not disagreement"
    assert ex.decision.value != "MATCH", (
        f"asserted identity on an incomplete description at p={ex.confidence}"
    )


# --- the feature contract ------------------------------------------------------

def test_featurise_matches_the_contract(engine):
    ex = engine.explain(engine.get("R1"), engine.get("R2"))
    x = featurise(ex, same_item_name=True)
    assert x.shape == (len(FEATURE_NAMES),)
    assert np.isfinite(x).all()
    # every feature is a ratio, a similarity or a flag
    assert (x >= -1.0).all() and (x <= 1.0).all()


def test_loader_rejects_a_stale_contract(tmp_path):
    """A model fitted on different columns must not silently score the wrong ones."""
    p = tmp_path / "scorer.json"
    p.write_text(json.dumps({
        "feature_names": ["something", "else"],
        "coef": [1.0, 1.0], "intercept": 0.0,
        "calibration": {"x": [], "y": []},
        "thresholds": {"match": 0.9, "near": 0.7, "review": 0.4},
    }))
    assert load_scorer(p) is None


def test_loader_returns_none_when_absent(tmp_path):
    """A missing model degrades to the deterministic path, never an exception."""
    assert load_scorer(tmp_path / "nope.json") is None


def test_engine_runs_without_a_scorer(engine):
    """The deterministic path still works and says so."""
    e = MatchingEngine(use_embeddings=False, use_scorer=False)
    e.index([MaterialRecord("A", "SS HEX BOLT M10 X 50"),
             MaterialRecord("B", "STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM")])
    ex = e.explain(e.get("A"), e.get("B"))
    assert ex.calibrated is False
    assert ex.to_dict()["calibrated"] is False


# --- splits --------------------------------------------------------------------

def test_splits_are_disjoint_by_identity():
    truth = {f"R{i}": f"spec-{i // 3}" for i in range(300)}
    a, b, c = split_identities(truth)
    assert a and b and c
    assert not (a & b) and not (a & c) and not (b & c)
    assert len(a | b | c) == len(set(truth.values()))


def test_leakage_check_actually_catches_leakage():
    """The guard has to fail when it should, or it is decoration."""
    def mk(keys):
        n = len(keys)
        return Pairs(X=np.zeros((n, 2)), y=np.zeros(n, dtype=np.int64),
                     vetoed=np.zeros(n, dtype=bool),
                     source_ids=list(keys), candidate_ids=list(keys),
                     spec_keys=list(keys))
    assert_no_leakage(mk(["a", "b"]), mk(["c", "d"]))          # fine
    with pytest.raises(AssertionError, match="leakage"):
        assert_no_leakage(mk(["a", "b"]), mk(["b", "c"]))


# --- metrics -------------------------------------------------------------------

def test_roc_auc_matches_sklearn():
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(7)
    y = rng.integers(0, 2, 400)
    p = rng.random(400) * 0.5 + y * 0.25
    assert roc_auc(p, y) == pytest.approx(roc_auc_score(y, p), abs=1e-9)


def test_reliability_is_perfect_on_perfect_predictions():
    y = np.array([0, 0, 1, 1] * 40)
    rows, ece = reliability(y.astype(float), y)
    assert ece == pytest.approx(0.0, abs=1e-12)
    assert brier(y.astype(float), y) == pytest.approx(0.0)


def test_thresholds_are_policy_and_ordered():
    p = np.linspace(0, 1, 200)
    y = (p > 0.5).astype(np.int64)
    t = pick_thresholds(p, y)
    assert t["match"] > t["near"] > t["review"]
    # realised precision is measured, not asserted
    assert 0.0 <= t["match_realised_precision"] <= 1.0


# --- robustness ----------------------------------------------------------------

def test_degrade_keeps_the_head_token_and_shrinks():
    rng_out = degrade("BOLT HEX SS M10 X 50 GR A2-70 ZINC", 0.5, __import__("random").Random(1))
    assert rng_out.split()[0] == "BOLT"
    assert len(rng_out.split()) < len("BOLT HEX SS M10 X 50 GR A2-70 ZINC".split())


def test_degrade_never_destroys_a_short_string():
    assert degrade("BOLT M10", 0.9, __import__("random").Random(1)) == "BOLT M10"
