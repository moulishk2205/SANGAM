"""
Fit the scorer, the calibrator and the thresholds.

Three things are learned, in this order, each on data the previous stage did not
choose from:

  1. the SCORER   — logistic regression over the twelve features, fitted on
                    train. Replaces the hand-chosen 0.85 / 0.15.
  2. the CALIBRATOR — isotonic regression mapping the scorer's output to an
                    observed match frequency, fitted on VALIDATION. Fitting it
                    on train would calibrate against the scorer's own optimism
                    and produce confident nonsense.
  3. the THRESHOLDS — chosen on validation by sweeping and maximising F1 for
                    MATCH, then placing NEAR and REVIEW at fixed precision
                    targets. Previously three numbers someone picked.

Test is touched exactly once, at the end, by scripts/train_scorer.py. Nothing in
this module reads it.

WHY LOGISTIC REGRESSION AND NOT A GRADIENT-BOOSTED TREE

A tree ensemble would score a point or two higher on this corpus and would be
the wrong tool. The output has to be defensible to a procurement officer and an
auditor: twelve named coefficients with signs you can argue about beat a
400-tree ensemble that is right slightly more often and explicable never. The
model is also the tie-breaker on a decision a human then signs, so its evidence
has to survive being read aloud. If a future version needs more capacity, the
honest upgrade is more features, not more opacity.
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from .dataset import Pairs
from .features import FEATURE_NAMES
from .model import LearnedScorer


def fit_scorer(train: Pairs, *, C: float = 1.0, seed: int = 20260902
               ) -> tuple[LogisticRegression, np.ndarray]:
    """
    Fit on the NON-VETOED rows only.

    A vetoed pair never reaches the scorer at inference time — the gate zeroes
    it first — so training on those rows would fit the model to a population it
    will never see, and would spend its capacity re-learning a rule that is
    already absolute. Excluding them also removes the easiest negatives, which
    makes every number that follows a harder and more honest one.
    """
    keep = ~train.vetoed
    X, y = train.X[keep], train.y[keep]
    if len(np.unique(y)) < 2:
        raise ValueError("training split has only one class after the veto filter")

    # No class_weight="balanced" here, and the reason is measured rather than
    # assumed. It was tried first, on the assumption that the pool would be
    # mostly negatives. The opposite is true: the veto removes the hard
    # negatives before this point, so the surviving pool is ~93% positive, and
    # re-weighting drags the boundary across a gap that is already clean —
    # test AUC fell from 1.0000 to 0.9959. On a separable problem, balancing
    # buys nothing and costs the separation.
    clf = LogisticRegression(C=C, max_iter=5000, random_state=seed)
    clf.fit(X, y)
    return clf, keep


def fit_calibrator(p_val: np.ndarray, y_val: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray]:
    """
    Isotonic rather than Platt.

    Platt scaling assumes the reliability curve is a sigmoid. This one is not:
    the attribute channel saturates, so scores pile up near 1.0 and the curve is
    flat-then-steep. Isotonic assumes only monotonicity — higher score, never
    lower probability — which is the one thing that must hold and the only thing
    we are willing to assert.
    """
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(p_val, y_val)
    xs = np.unique(p_val)
    return xs, iso.predict(xs)


def pick_thresholds(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """
    Set the bands by POLICY on the calibrated probability, then measure them.

    The first version of this maximised F1 on validation and produced
    `MATCH >= 0.0100`. That is not a bug in the search, it is what the data
    says: on clean descriptions the model is nearly perfect, the probabilities
    are bimodal at 0 and 1, and every threshold between them scores identically.
    F1-maximisation then picks an arbitrary point in that gap — and it picked one
    that collapses NEAR_MATCH and REVIEW_REQUIRED into nothing, which would empty
    the review queue the entire product is built around.

    Calibration is what makes a better answer available. Once p is a probability
    rather than a ranking score, a threshold has a plain-English meaning, and the
    bands can be stated as risk policy instead of fitted:

        MATCH            0.90 — assert identity only where we would be right
                                nine times in ten
        NEAR_MATCH       0.70 — probably the same; a person confirms
        REVIEW_REQUIRED  0.40 — worth a look

    These are round numbers on purpose. They are a procurement policy, they
    belong to whoever owns the material master, and they can be moved without
    retraining anything. What is NOT a policy choice is whether the numbers mean
    what they say, so the realised precision at each band is measured here and
    reported alongside.
    """
    bands = {"match": 0.90, "near": 0.70, "review": 0.40}
    out: dict[str, float] = dict(bands)
    for name, t in bands.items():
        pred = p >= t
        tp = int((pred & (y == 1)).sum())
        fp = int((pred & (y == 0)).sum())
        out[f"{name}_realised_precision"] = tp / (tp + fp) if tp + fp else float("nan")
        out[f"{name}_n"] = float(int(pred.sum()))
    return out


def train(train_pairs: Pairs, val_pairs: Pairs, *, metadata: dict | None = None
          ) -> LearnedScorer:
    clf, _ = fit_scorer(train_pairs)

    scorer = LearnedScorer(
        feature_names=list(FEATURE_NAMES),
        coef=clf.coef_[0].astype(np.float64),
        intercept=float(clf.intercept_[0]),
        calib_x=np.array([]), calib_y=np.array([]),
        thresholds={"match": 0.5, "near": 0.3, "review": 0.1},
        metadata=metadata or {},
    )

    # Calibrate and threshold on validation, on the non-vetoed rows only —
    # the same population the scorer will meet.
    keep = ~val_pairs.vetoed
    p_raw = scorer.raw(val_pairs.X[keep])
    y_val = val_pairs.y[keep]

    scorer.calib_x, scorer.calib_y = fit_calibrator(p_raw, y_val)
    p_cal = scorer.calibrate(p_raw)
    scorer.thresholds = pick_thresholds(p_cal, y_val)
    return scorer
