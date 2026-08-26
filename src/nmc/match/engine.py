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

    @property
    def confidence(self) -> float:
        return self.explanation.confidence

    @property
    def decision(self) -> Decision:
        return self.explanation.decision


class MatchingEngine:
    """Build once with a corpus, then call `match()` or `check_before_create()`."""

    def __init__(self, use_embeddings: bool = True) -> None:
        self.retriever = Retriever(use_embeddings=use_embeddings)
        self.records: list[MaterialRecord] = []
        self._by_id: dict[str, MaterialRecord] = {}

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
                semantic: float | None = None, lexical: float | None = None) -> MatchExplanation:
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
        scored = [
            ScoredCandidate(h.record,
                            self.explain(source, h.record, h.semantic_score, h.lexical_score))
            for h in hits
        ]
        # veto'd last, then by score
        scored.sort(key=lambda s: (s.explanation.critical_veto, -s.confidence))
        return scored[:top_k]

    def check_before_create(self, description: str, org: str = "", org_code: str = "",
                            top_k: int = 3) -> tuple[MaterialRecord, list[ScoredCandidate]]:
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
        return probe, self.match(probe, top_k=top_k)
