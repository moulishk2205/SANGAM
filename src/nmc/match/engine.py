"""
The matching engine — orchestration and the scoring/decision policy.

Pipeline, in order:

    normalise -> extract -> retrieve -> compare -> VETO -> score -> decide -> explain

The scoring rule is deliberately simple and deliberately asymmetric:

    score = veto * (0.85 * attribute_agreement + 0.15 * text_corroboration)

`veto` is 0 or 1. Nothing recovers a pair once a CRITICAL attribute disagrees. The
weighted term only orders the survivors.

On confidence
-------------
The number this returns is a *score*, not a calibrated probability. Calling it a
probability would require a labelled calibration set and a fitted calibrator, which is
Phase 2 work. The field is named `confidence` because that is the product vocabulary,
but `calibrated=False` is carried in the payload so nobody downstream mistakes it for
one. Reporting an uncalibrated score as "97% likely correct" is exactly the kind of
false AI claim that loses a technical review.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..extract.grammar import extract
from ..extract.templates import CONFIG_VERSION, classify_item_name, critical_codes
import numpy as np

from ..normalise.text import GAZETTEER_VERSION, normalise
from ..types import Decision, MatchExplanation, MaterialRecord, Verdict
from .compare import agreement, compare, veto
from .retrieve import Retriever, text_similarity

MODEL_VERSION = f"nmc-mvp-0.1/{GAZETTEER_VERSION}/{CONFIG_VERSION}"

# Attribute agreement carries the score; text similarity is a small additive
# corroboration term.
#
# The split matters and is not arbitrary. Text is *retrieval* evidence, not identity
# evidence, so it must never be able to pull a specification-clean pair down — that
# would let a badly-worded description of the right material lose to a well-worded
# description of the wrong one. Because the text term is non-negative it can only ever
# raise a score, and because MATCH additionally requires every CRITICAL attribute to
# be known and agreeing, it can only reorder pairs that are already specification-clean.
W_ATTR, W_TEXT = 0.85, 0.15

# Decision bands. Chosen conservatively: in procurement a false positive merges two
# different parts and can put the wrong component into a live plant, while a false
# negative costs a reviewer thirty seconds. When in doubt the system must abstain.
T_MATCH = 0.86
T_NEAR = 0.70
T_REVIEW = 0.45


@dataclass
class ScoredCandidate:
    record: MaterialRecord
    explanation: MatchExplanation
    # Which retrieval channel proposed this candidate. Computed in retrieve.py and,
    # until now, discarded here — it is the only signal that answers "why was this
    # ever a candidate at all", and lexical-only and dense-only misses are visibly
    # different kinds of wrong.
    channels: tuple[str, ...] = ()

    @property
    def confidence(self) -> float:
        return self.explanation.confidence

    @property
    def decision(self) -> Decision:
        return self.explanation.decision


class MatchingEngine:
    """Build once with a corpus, then call `match()` or `check_before_create()`."""

    def __init__(self, use_embeddings: bool = True, use_scorer: bool = True) -> None:
        self.retriever = Retriever(use_embeddings=use_embeddings)
        self.records: list[MaterialRecord] = []
        self._by_id: dict[str, MaterialRecord] = {}
        # The learned scorer is optional and loaded late. Absent, every number
        # below is the deterministic one and `calibrated` stays False — which is
        # the correct degradation: a missing calibration is a reason to show an
        # uncalibrated score, never a reason to refuse to answer. Training it is
        # `python scripts/train_scorer.py`.
        self.scorer = None
        if use_scorer:
            from ..ml.model import load_scorer
            self.scorer = load_scorer()

    # -- corpus ----------------------------------------------------------------
    def prepare(self, record: MaterialRecord) -> MaterialRecord:
        """Normalise, classify and extract. Idempotent."""
        n = normalise(record.raw_description)
        record.normalised = n.text
        item_name, _ = classify_item_name(list(n.tokens))
        record.item_name = item_name
        record.attributes = {}
        extract(record, n, item_name)
        return record

    def index(self, records: list[MaterialRecord]) -> None:
        norms = []
        for r in records:
            self.prepare(r)
            norms.append(normalise(r.raw_description))
        self.records = records
        self._by_id = {r.id: r for r in records}
        self.retriever.build(records, norms)

    def get(self, record_id: str) -> MaterialRecord | None:
        return self._by_id.get(record_id)

    # -- scoring ---------------------------------------------------------------
    def _decide(self, score: float, vetoed: bool, n_crit_known: int,
                n_crit_total: int) -> Decision:
        if vetoed:
            return Decision.DISTINCT
        # MATCH requires every CRITICAL attribute to be stated on both sides and to
        # agree. If a discriminating attribute is simply unstated we cannot assert
        # identity however similar the text is — `SS HEX BOLT` and
        # `SS HEX BOLT M10 X 50` agree on everything they both mention, and are not
        # the same material. Abstaining here costs a reviewer thirty seconds;
        # asserting it corrupts the master.
        if n_crit_total and n_crit_known < n_crit_total:
            return Decision.REVIEW_REQUIRED
        if score >= T_MATCH:
            return Decision.MATCH
        if score >= T_NEAR:
            return Decision.NEAR_MATCH
        if score >= T_REVIEW:
            return Decision.REVIEW_REQUIRED
        return Decision.DISTINCT

    def explain(self, source: MaterialRecord, candidate: MaterialRecord,
                semantic: float | None = None, lexical: float | None = None,
                channels: list[str] | None = None) -> MatchExplanation:
        """Full comparison of one pair. This is what the evidence panel renders."""
        rows = compare(source, candidate)
        vetoed, reason = veto(rows)
        attr_agree, n_a, n_d, n_u = agreement(rows)

        if semantic is None:
            semantic = self.retriever.semantic_similarity(source.normalised, candidate.normalised)
        if lexical is None:
            # Pair opened directly (evidence panel) rather than reached through
            # retrieval, so there is no corpus-relative score to inherit. Compute one.
            lexical = text_similarity(source.normalised, candidate.normalised)

        # Text corroboration = the strongest available text channel, or 0 if neither is
        # present. Taking the max rather than a weighted blend keeps the score stable
        # whether or not the embedding model loaded: a missing channel weakens the
        # corroboration slightly instead of silently capping the achievable score and
        # making the decision thresholds meaningless.
        text_signals = [s for s in (semantic, lexical) if s is not None]
        text = max((max(s, 0.0) for s in text_signals), default=0.0)

        raw = W_ATTR * attr_agree + W_TEXT * text
        score = 0.0 if vetoed else raw

        crit = critical_codes(source.item_name) or []
        crit_known = sum(
            1 for r in rows
            if r.code in crit and r.verdict is not Verdict.UNKNOWN
        )

        # The learned path. `raw_score` stays the deterministic number either
        # way, so the evidence panel can always show the arithmetic a person can
        # check by hand — the model replaces the verdict, not the audit trail.
        calibrated = False
        if self.scorer is not None:
            from ..ml.features import featurise
            probe = MatchExplanation(
                source_id=source.id, candidate_id=candidate.id,
                source_description=source.raw_description,
                candidate_description=candidate.raw_description,
                decision=Decision.DISTINCT, confidence=0.0,
                semantic_score=max(semantic or 0.0, 0.0),
                lexical_score=max(lexical or 0.0, 0.0),
                attribute_agreement=attr_agree, critical_veto=vetoed,
                veto_reason=reason, rows=rows,
                n_agree=n_a, n_disagree=n_d, n_unknown=n_u,
            )
            X = featurise(probe, same_item_name=source.item_name == candidate.item_name)
            # The veto multiplies last, exactly as it did before. It is not a
            # feature and cannot be outvoted.
            p = float(self.scorer.probability(X.reshape(1, -1),
                                              np.array([vetoed], dtype=bool))[0])
            score = p
            calibrated = True
            decision = Decision[self.scorer.decide(p, vetoed)]

            # SECOND GATE: insufficient evidence cannot be scored around.
            #
            # The deterministic path has always refused to assert MATCH unless
            # every CRITICAL attribute was stated on BOTH sides. The learned
            # path bypassed it and asserted MATCH at p=0.97 on
            # `SS HEX BOLT M10 X 50` vs `SS HEX BOLT` — a description that
            # states no dimensions at all. Agreement is computed over what both
            # sides mention, so a description that mentions almost nothing
            # agrees with almost everything, and the model had no reason to
            # learn otherwise: the training corpus always states its criticals,
            # so it never saw the case.
            #
            # The right response to a gap the data cannot cover is a rule, not
            # more data. This one demotes and never promotes, so the model still
            # decides everything it is competent to decide.
            if n_crit_total := len(crit):
                if crit_known < n_crit_total and decision is Decision.MATCH:
                    decision = Decision.REVIEW_REQUIRED
        else:
            decision = self._decide(score, vetoed, crit_known, len(crit))

        return MatchExplanation(
            source_id=source.id,
            candidate_id=candidate.id,
            source_description=source.raw_description,
            candidate_description=candidate.raw_description,
            decision=decision,
            confidence=round(score, 4),
            semantic_score=round(max(semantic, 0.0), 4) if semantic is not None else 0.0,
            lexical_score=round(max(lexical, 0.0), 4) if lexical is not None else 0.0,
            attribute_agreement=round(attr_agree, 4),
            critical_veto=vetoed,
            veto_reason=reason,
            raw_score=round(raw, 4),
            calibrated=calibrated,
            rows=rows,
            n_agree=n_a, n_disagree=n_d, n_unknown=n_u,
            model_version=MODEL_VERSION,
            config_version=CONFIG_VERSION,
        )

    # -- public API ------------------------------------------------------------
    def match(self, source: MaterialRecord, top_k: int = 5,
              pool: int = 50) -> list[ScoredCandidate]:
        """
        Rank candidates for an existing record.

        Vetoed candidates are deliberately KEPT and returned, ranked last. They are the
        most instructive thing the system produces — a candidate the text says is a
        near-certain match and the specification says is not.
        """
        if not source.normalised:
            self.prepare(source)
        hits = self.retriever.retrieve(source.normalised, top_k=pool, pool=pool,
                                       exclude_id=source.id)
        # `lexical` is deliberately NOT taken from the retriever.
        #
        # Candidate.lexical_score is the raw TF-IDF query score: unbounded and
        # relative to the corpus, useful for ranking and meaningless as a
        # similarity. explain() computes a pairwise char-ngram similarity in
        # [0, 1] instead. Passing the retrieval score here made the SAME PAIR
        # carry different numbers depending on whether it was reached through
        # match() or opened directly in the evidence panel — 0.2579 one way and
        # 0.8250 the other. The old formula hid it behind a 0.15 weight on a
        # score that attribute agreement already dominated; a fitted model does
        # not, because the value is a feature. Passing None makes explain()
        # compute the pairwise number on both paths.
        #
        # semantic_score IS passed: it is already a cosine similarity, so it is
        # the same quantity explain() would compute, and reusing it avoids
        # re-encoding text the retriever has just encoded.
        scored = [
            ScoredCandidate(h.record,
                            self.explain(source, h.record, h.semantic_score, None),
                            channels=tuple(h.channels))
            for h in hits
        ]
        # veto'd last, then by score
        scored.sort(key=lambda s: (s.explanation.critical_veto, -s.confidence))
        return scored[:top_k]

    def check_before_create(self, description: str, org: str = "", org_code: str = "",
                            top_k: int = 3, pool: int = 50) -> tuple[MaterialRecord, list[ScoredCandidate]]:
        """
        The prevention path: is this proposed new material already in the master?

        Same engine, same evidence, no separate code path — so what the reviewer sees
        at creation time is exactly what the harmonisation workspace would have shown.
        """
        probe = MaterialRecord(
            id="__probe__", raw_description=description, org=org, org_code=org_code,
            provenance="HAND_CURATED",
        )
        self.prepare(probe)
        return probe, self.match(probe, top_k=top_k, pool=max(pool, top_k * 2))
