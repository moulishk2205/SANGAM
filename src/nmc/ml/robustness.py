"""
Does the learned scorer hold up when the description degrades?

The clean corpus is saturated: after the veto, true matches sit at attribute
agreement 1.0 and the survivors at 0.8, and any monotone function of that one
feature separates them perfectly. Reporting only that number would be reporting
a solved problem, and would hide the question that actually matters for
deployment.

Real material masters are not clean. A code is written by a storekeeper in a
hurry: `HEX BOLT MS 10` for a bolt whose full specification names a thread, a
length, a grade and a finish. Attributes go missing, and when they do the
specification channel loses its edge — agreement is computed over whatever both
sides happened to state, so a description that states almost nothing agrees with
almost everything.

That is where a fitted model can beat a fixed blend, because it has features the
blend does not: how much of the CRITICAL set was stated at all, how the two text
channels disagree, how wide the template was. This module degrades descriptions
on purpose and measures whether that advantage is real.

Degradation is token dropout on the raw description, which is a fair model of
the failure: the terse forms in a real master are not corrupted strings, they
are strings with words missing.
"""
from __future__ import annotations

import random

import numpy as np

from ..match.engine import MatchingEngine
from ..types import MaterialRecord
from .features import featurise


def degrade(text: str, rate: float, rng: random.Random) -> str:
    """
    Drop `rate` of the whitespace tokens, always keeping at least two.

    The first token is retained deliberately: it is almost always the noun that
    drives item classification, and dropping it changes the task from "score a
    hard pair" to "the extractor could not tell what this is", which is a
    different experiment.
    """
    toks = text.split()
    if len(toks) <= 2:
        return text
    keep_n = max(2, int(round(len(toks) * (1.0 - rate))))
    idx = sorted(rng.sample(range(1, len(toks)), min(keep_n - 1, len(toks) - 1)))
    return " ".join([toks[0]] + [toks[i] for i in idx])


def stress(engine: MatchingEngine, records: list[MaterialRecord],
           truth: dict[str, str], keys: set[str], *,
           rates: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6),
           top_k: int = 12, seed: int = 20260902) -> dict[float, dict]:
    """
    For each dropout rate, re-probe with degraded text and collect scored pairs.

    Returns rate -> {X, y, vetoed, found} where `found` is retrieval recall@k:
    the ceiling on everything, because a scorer cannot rank a candidate the
    retriever never returned.
    """
    groups: dict[str, list[str]] = {}
    for r in records:
        groups.setdefault(truth[r.id], []).append(r.id)

    probes = [r for r in records
              if truth[r.id] in keys and len(groups[truth[r.id]]) > 1]

    out: dict[float, dict] = {}
    for rate in rates:
        rng = random.Random(seed + int(rate * 1000))
        X, y, vetoed = [], [], []
        found = 0
        for src in probes:
            text = degrade(src.raw_description, rate, rng) if rate else src.raw_description
            probe = engine.prepare(MaterialRecord(id="__probe__", raw_description=text,
                                                  org=src.org, org_code=src.org_code))
            expected = set(groups[truth[src.id]]) - {src.id}
            results = engine.match(probe, top_k=top_k, pool=50)
            ranked = [r.record.id for r in results if r.record.id != src.id]
            if expected & set(ranked):
                found += 1
            for r in results:
                if r.record.id == src.id:
                    continue
                X.append(featurise(r.explanation,
                                   same_item_name=probe.item_name == r.record.item_name))
                y.append(1 if truth[r.record.id] == truth[src.id] else 0)
                vetoed.append(bool(r.explanation.critical_veto))

        out[rate] = {
            "X": np.array(X, dtype=np.float64).reshape(len(X), -1),
            "y": np.array(y, dtype=np.int64),
            "vetoed": np.array(vetoed, dtype=bool),
            "retrieval_recall": found / len(probes) if probes else 0.0,
            "n_probes": len(probes),
        }
    return out
