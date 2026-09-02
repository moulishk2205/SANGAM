"""
The fitted model, and the rule that survives it.

    p(match) = veto x calibrate(sigma(w . x + b))

`veto` is 0 or 1 and multiplies LAST. Not a feature, not a prior, not a strong
negative weight the model could learn to overcome — a multiplication by zero
applied after everything else has had its say. A vetoed pair reports exactly
0.0, always, whatever the twelve features say and whatever the calibrator would
have mapped them to.

That is the whole safety property of this system and it is now, if anything,
better defended than before: previously the veto guarded a formula whose weights
a person chose; it now guards a formula whose weights were fitted, and the guard
is identical because it never enters the fit at all.

WHY JSON AND NOT A PICKLE

The artifact is a JSON file of named coefficients. Anyone can open it, read the
weight on `attribute_agreement`, and check it is large and positive. A pickle
would be opaque, tied to a scikit-learn version, and an arbitrary-code-execution
hazard on load. For twelve coefficients and a monotone step function, JSON costs
nothing and buys auditability — which in a procurement context is the point.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .features import FEATURE_NAMES

SCORER_VERSION = "scorer-v1"
DEFAULT_PATH = Path(__file__).resolve().parents[3] / "models" / "scorer" / "scorer-v1.json"


@dataclass
class LearnedScorer:
    feature_names: list[str]
    coef: np.ndarray
    intercept: float
    # Isotonic calibration as a step function: sorted thresholds -> probabilities.
    calib_x: np.ndarray
    calib_y: np.ndarray
    thresholds: dict[str, float]
    metadata: dict

    # -- inference ---------------------------------------------------------------
    def margin(self, X: np.ndarray) -> np.ndarray:
        return X @ self.coef + self.intercept

    def raw(self, X: np.ndarray) -> np.ndarray:
        """Uncalibrated sigmoid output — a ranking score, not a probability."""
        return 1.0 / (1.0 + np.exp(-self.margin(X)))

    def calibrate(self, p: np.ndarray) -> np.ndarray:
        """
        Apply the fitted isotonic map.

        np.interp does piecewise-linear interpolation between the isotonic
        knots and clamps outside them, which is the standard way to evaluate a
        fitted isotonic regression on unseen points.
        """
        if self.calib_x.size == 0:
            return p
        return np.interp(p, self.calib_x, self.calib_y)

    def probability(self, X: np.ndarray, vetoed: np.ndarray) -> np.ndarray:
        """The number the product shows. Vetoed pairs are exactly zero."""
        p = self.calibrate(self.raw(X))
        return np.where(vetoed, 0.0, p)

    def decide(self, p: float, vetoed: bool) -> str:
        if vetoed:
            return "DISTINCT"
        if p >= self.thresholds["match"]:
            return "MATCH"
        if p >= self.thresholds["near"]:
            return "NEAR_MATCH"
        if p >= self.thresholds["review"]:
            return "REVIEW_REQUIRED"
        return "DISTINCT"

    # -- persistence -------------------------------------------------------------
    def to_json(self) -> dict:
        return {
            "version": SCORER_VERSION,
            "feature_names": self.feature_names,
            "coef": [float(c) for c in self.coef],
            "intercept": float(self.intercept),
            "calibration": {
                "method": "isotonic",
                "x": [float(v) for v in self.calib_x],
                "y": [float(v) for v in self.calib_y],
            },
            "thresholds": self.thresholds,
            "metadata": self.metadata,
        }

    def save(self, path: Path = DEFAULT_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2))
        return path


def load_scorer(path: Path = DEFAULT_PATH) -> LearnedScorer | None:
    """
    Returns None when the artifact is absent or stale rather than raising.

    The engine must start without it. A missing model means the deterministic
    scorer runs and the product still works, which is the correct degradation:
    an unavailable calibration is a reason to show an uncalibrated number, never
    a reason to refuse to answer.
    """
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    # A model fitted against a different feature contract is worse than none: it
    # would silently score the wrong columns.
    if d.get("feature_names") != FEATURE_NAMES:
        return None

    c = d.get("calibration", {})
    return LearnedScorer(
        feature_names=d["feature_names"],
        coef=np.array(d["coef"], dtype=np.float64),
        intercept=float(d["intercept"]),
        calib_x=np.array(c.get("x", []), dtype=np.float64),
        calib_y=np.array(c.get("y", []), dtype=np.float64),
        thresholds=d["thresholds"],
        metadata=d.get("metadata", {}),
    )
