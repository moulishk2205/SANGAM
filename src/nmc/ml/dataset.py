"""
Turning the corpus into labelled pairs — and splitting it without lying.

TWO THINGS HERE ARE EASY TO GET WRONG, AND BOTH INFLATE THE SCORE

1. SPLITTING BY RECORD INSTEAD OF BY IDENTITY.

   The corpus renders each canonical specification into three surface forms. Split
   the 1,800 records at random and two renderings of the same bolt land on
   opposite sides of the wall: the model meets that exact identity in training and
   is then tested on it. The reported number goes up and means nothing.

   So the split is on the SPEC KEY. An identity is wholly in train, or wholly in
   validation, or wholly in test. `assert_no_leakage()` proves it afterwards
   rather than trusting the code above it.

2. SAMPLING NEGATIVES AT RANDOM.

   A random non-match is a bolt against a bearing. Any model separates those, and
   the resulting accuracy describes a problem nobody has. The negatives that
   matter are the ones retrieval actually surfaces — `SS HEX BOLT M10X75` against
   `MS HEX BOLT M10X75` — so negatives are mined from the retriever's own top-k.
   These are the pairs the system will really be asked about, and they are hard.

The labels themselves are correct by construction: two records match iff they
were rendered from the same specification. That is the only defensible way to
claim a label on generated text, and it is why the corpus is generated downward
from specs rather than by perturbing strings.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from ..match.engine import MatchingEngine
from ..types import MaterialRecord
from .features import featurise

SPLIT_SEED = 20260902


@dataclass
class Pairs:
    """A split. X is (n, d), y is (n,) in {0, 1}, meta carries what X cannot."""
    X: np.ndarray
    y: np.ndarray
    vetoed: np.ndarray          # bool per row — the gate, kept OUT of X
    source_ids: list[str]
    candidate_ids: list[str]
    spec_keys: list[str]        # the source's identity, for leakage checks

    def __len__(self) -> int:
        return len(self.y)

    @property
    def positives(self) -> int:
        return int(self.y.sum())


def split_identities(truth: dict[str, str], *, seed: int = SPLIT_SEED,
                     ratios: tuple[float, float, float] = (0.6, 0.2, 0.2),
                     ) -> tuple[set[str], set[str], set[str]]:
    """Partition the SPEC KEYS — never the records — into train/val/test."""
    keys = sorted(set(truth.values()))
    rng = random.Random(seed)
    rng.shuffle(keys)
    n = len(keys)
    a = int(n * ratios[0])
    b = a + int(n * ratios[1])
    return set(keys[:a]), set(keys[a:b]), set(keys[b:])


def build_pairs(engine: MatchingEngine, records: list[MaterialRecord],
                truth: dict[str, str], keys: set[str], *,
                top_k: int = 12, pool: int = 50) -> Pairs:
    """
    Every record whose identity is in `keys` is used as a probe; the retriever's
    top-k become the candidate pairs.

    Candidates are NOT filtered to the split. A held-out probe may legitimately
    retrieve a training-set record — that is exactly what happens in production,
    where the index contains everything and only the query is new. Filtering the
    index per split would measure a system nobody would ever run. What must not
    leak is the *identity being decided*, and that is what the probe-side filter
    guarantees.
    """
    X, y, vetoed, srcs, cands, spec = [], [], [], [], [], []

    for src in records:
        if truth[src.id] not in keys:
            continue
        for r in engine.match(src, top_k=top_k, pool=pool):
            if r.record.id == src.id:
                continue                      # a record is not its own evidence
            e = r.explanation
            X.append(featurise(e, same_item_name=src.item_name == r.record.item_name))
            y.append(1 if truth[r.record.id] == truth[src.id] else 0)
            vetoed.append(bool(e.critical_veto))
            srcs.append(src.id)
            cands.append(r.record.id)
            spec.append(truth[src.id])

    return Pairs(
        X=np.array(X, dtype=np.float64).reshape(len(X), -1),
        y=np.array(y, dtype=np.int64),
        vetoed=np.array(vetoed, dtype=bool),
        source_ids=srcs, candidate_ids=cands, spec_keys=spec,
    )


def assert_no_leakage(*splits: Pairs) -> None:
    """
    Prove the identities are disjoint rather than assume it.

    Cheap, and the one check that would catch a refactor quietly turning an
    honest 90% into a meaningless 99%.
    """
    sets = [set(s.spec_keys) for s in splits]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            overlap = sets[i] & sets[j]
            if overlap:
                raise AssertionError(
                    f"identity leakage between split {i} and split {j}: "
                    f"{len(overlap)} shared spec keys, e.g. {sorted(overlap)[:3]}"
                )
