"""
The feature contract.

One place defines what a (source, candidate) pair looks like to a learned model,
because a feature order that drifts between training and inference is a silent
accuracy loss that no test catches — the model still returns a number, it is
just the wrong one. `FEATURE_NAMES` is written into the model artifact at fit
time and checked on load.

WHAT IS DELIBERATELY NOT A FEATURE: THE VETO

`critical_veto` does not appear below, and must not be added. It is not evidence
to be weighed, it is a gate applied after scoring — see model.py. A model given
the veto as an input can learn to overrule it whenever the text is similar
enough, which is precisely the failure the whole architecture exists to prevent.
Keeping it out of the feature vector makes that impossible rather than unlikely.
"""
from __future__ import annotations

import numpy as np

from ..types import Criticality, MatchExplanation, Verdict

FEATURE_NAMES: list[str] = [
    "attribute_agreement",   # the specification signal, in [0, 1]
    "text_max",              # strongest text channel — what the old score used
    "semantic",              # dense channel alone
    "lexical",               # char-ngram channel alone
    "text_gap",              # |semantic - lexical|; the channels disagreeing is
                             # itself informative — it flags surface forms that
                             # look alike lexically but not in embedding space
    "frac_agree",            # shape of the evidence table, independent of which
    "frac_disagree",         # attributes happen to be present
    "frac_unknown",
    "crit_known_frac",       # how much of the discriminating set was stated at
                             # all. Low means "we cannot assert identity", which
                             # is different from "they differ".
    "crit_agree_frac",       # of the critical attributes that WERE stated
    "n_rows",                # template width, scaled — a 9-attribute flange and
                             # a 4-attribute washer are not equally decidable
    "same_item_name",        # 1.0 when both classified to the same item type
]


def _safe(n: float, d: float) -> float:
    return float(n) / float(d) if d else 0.0


def featurise(e: MatchExplanation, *, same_item_name: bool) -> np.ndarray:
    """
    One pair -> one feature row, in FEATURE_NAMES order.

    Takes the explanation the engine already computed rather than recomputing
    anything, so training and inference see byte-identical inputs. The engine is
    the single source of truth for what a comparison means; this only reshapes it.
    """
    total = len(e.rows) or 1
    crit = [r for r in e.rows if r.criticality is Criticality.CRITICAL]
    crit_known = [r for r in crit if r.verdict is not Verdict.UNKNOWN]
    crit_agree = [r for r in crit_known if r.verdict is Verdict.AGREE]

    text_max = max(e.semantic_score, e.lexical_score)

    return np.array([
        e.attribute_agreement,
        text_max,
        e.semantic_score,
        e.lexical_score,
        abs(e.semantic_score - e.lexical_score),
        _safe(e.n_agree, total),
        _safe(e.n_disagree, total),
        _safe(e.n_unknown, total),
        _safe(len(crit_known), len(crit)),
        _safe(len(crit_agree), len(crit_known)),
        min(total, 12) / 12.0,
        1.0 if same_item_name else 0.0,
    ], dtype=np.float64)
