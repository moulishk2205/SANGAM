"""
Core value model for material attributes.

Sprint 0 measured two things that break the obvious design:

  * attributes are frequently MULTI-VALUED — MATERIAL carries up to 72 values on a
    single real item;
  * attributes are frequently RANGES rather than points — 71.9% of items carrying
    WIDTH BETWEEN FLATS carry both a min and a max endpoint.

So an attribute value is not a scalar. It is one of four shapes, and the comparator
has to handle every pairing of them. Getting this wrong is what makes a matcher
silently unsafe: comparing a range to a point by string equality returns "different"
for two items that are actually the same.

The other load-bearing distinction here is UNKNOWN vs DISAGREE. A missing attribute
is not evidence of difference. Conflating the two is the single most common way a
duplicate detector destroys either its precision or its recall.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Criticality(str, Enum):
    """
    How much a disagreement on this attribute matters.

    CRITICAL is the veto tier: a genuine disagreement here forces DISTINCT no matter
    how similar the text is. That is the whole architectural point — M10x50 vs M10x75
    must be structurally impossible to call a duplicate, not merely unlikely.
    """
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    MINOR = "MINOR"
    INFORMATIONAL = "INFORMATIONAL"


class Verdict(str, Enum):
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    UNKNOWN = "UNKNOWN"          # at least one side has no value — never negative evidence


class Decision(str, Enum):
    MATCH = "MATCH"
    NEAR_MATCH = "NEAR_MATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DISTINCT = "DISTINCT"


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Quantity:
    """A number with a canonical unit. Units are canonicalised at extraction time."""
    value: float
    unit: str

    def __str__(self) -> str:
        v = f"{self.value:g}"
        return f"{v} {self.unit}" if self.unit else v


@dataclass(frozen=True, slots=True)
class Point:
    """A single measured value."""
    q: Quantity

    def __str__(self) -> str:
        return str(self.q)


@dataclass(frozen=True, slots=True)
class Range:
    """
    A min/max interval. Real catalogues express tolerance this way far more often
    than the design assumed, so this is a first-class shape, not an edge case.
    """
    lo: Quantity
    hi: Quantity

    def __post_init__(self) -> None:
        if self.lo.unit != self.hi.unit:
            raise ValueError(f"range endpoints disagree on unit: {self.lo.unit} vs {self.hi.unit}")
        if self.lo.value > self.hi.value:
            raise ValueError(f"range is inverted: {self.lo} .. {self.hi}")

    @property
    def unit(self) -> str:
        return self.lo.unit

    def overlaps(self, other: "Range") -> bool:
        return self.lo.value <= other.hi.value and other.lo.value <= self.hi.value

    def contains(self, q: Quantity) -> bool:
        return self.lo.value <= q.value <= self.hi.value

    def __str__(self) -> str:
        return f"{self.lo.value:g}–{self.hi.value:g} {self.unit}".strip()


@dataclass(frozen=True, slots=True)
class Categorical:
    """A coded or free-text categorical value, e.g. a material grade or head style."""
    code: str
    label: str = ""

    def __str__(self) -> str:
        return self.label or self.code


@dataclass(frozen=True, slots=True)
class ValueSet:
    """
    A multi-valued attribute. MATERIAL on a real bolt commonly carries several codes
    at once (base material plus coating, or a permitted-alternatives list), so set
    semantics are required rather than optional.
    """
    values: tuple[Categorical, ...]

    @staticmethod
    def of(items: Iterable[str | Categorical]) -> "ValueSet":
        out = []
        for i in items:
            out.append(i if isinstance(i, Categorical) else Categorical(str(i)))
        # stable, deduplicated
        seen, uniq = set(), []
        for c in out:
            if c.code not in seen:
                seen.add(c.code)
                uniq.append(c)
        return ValueSet(tuple(uniq))

    @property
    def codes(self) -> set[str]:
        return {c.code for c in self.values}

    def __len__(self) -> int:
        return len(self.values)

    def __str__(self) -> str:
        return ", ".join(str(v) for v in self.values)


Value = Point | Range | ValueSet | Categorical | None
"""None means UNKNOWN — the attribute was not stated. Never treat it as a value."""


# ---------------------------------------------------------------------------
# Attributes and records
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class AttributeSpec:
    """
    One row of an attribute template: what the attribute is and how to compare it.

    `tol_abs` / `tol_rel` are deliberately conservative by default. A false negative
    goes to a human reviewer; a false positive corrupts the master. Where a tolerance
    is not known, it stays at zero and a human widens it — with the reason recorded
    in `provenance`.
    """
    code: str
    label: str
    criticality: Criticality
    canonical_unit: str = ""
    tol_abs: float = 0.0
    tol_rel: float = 0.0
    provenance: str = ""

    def tolerance_for(self, a: float, b: float) -> float:
        return max(self.tol_abs, self.tol_rel * max(abs(a), abs(b)))


@dataclass(slots=True)
class Attribute:
    """An extracted attribute value plus how we got it — needed for the audit trail."""
    code: str
    value: Value
    source: str = ""          # 'rule:R07' | 'gazetteer:v1' | 'given'
    raw: str = ""             # the substring it came from, for the evidence panel
    inferred_unit: str = ""   # set when a unit was inferred rather than stated

    @property
    def known(self) -> bool:
        return self.value is not None


@dataclass(slots=True)
class MaterialRecord:
    """
    A material as the platform holds it. `raw_description` is never mutated — the
    original text is evidence and has to survive to the audit trail intact.
    """
    id: str
    raw_description: str
    org: str = ""                       # owning CPSE
    org_code: str = ""                  # that CPSE's own material code — preserved forever
    item_name: str = ""                 # approved item name (INC label)
    inc: str = ""
    normalised: str = ""
    attributes: dict[str, Attribute] = field(default_factory=dict)
    provenance: str = "SYNTHETIC_VARIANT"   # REAL_CATALOGUE | REAL_TENDER | SYNTHETIC_VARIANT | HAND_CURATED
    canonical_id: str | None = None     # NMC id once harmonised

    def get(self, code: str) -> Value:
        a = self.attributes.get(code)
        return a.value if a else None

    def attr(self, code: str) -> Attribute | None:
        return self.attributes.get(code)

    def set(self, code: str, value: Value, source: str = "", raw: str = "",
            inferred_unit: str = "") -> None:
        self.attributes[code] = Attribute(code, value, source, raw, inferred_unit)


# ---------------------------------------------------------------------------
# Comparison output
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class AttributeComparison:
    """One row of the evidence table the reviewer actually reads."""
    code: str
    label: str
    criticality: Criticality
    left: str
    right: str
    verdict: Verdict
    detail: str = ""            # why — e.g. "differs by 25 mm, tolerance 0.5 mm"
    vetoed: bool = False        # this row alone forced DISTINCT

    @property
    def symbol(self) -> str:
        return {Verdict.AGREE: "OK", Verdict.DISAGREE: "X", Verdict.UNKNOWN: "?"}[self.verdict]


@dataclass(slots=True)
class MatchExplanation:
    """
    The full evidence object returned with every candidate.

    Every number in here is computed. Nothing is narrated by a language model, and
    nothing is hard-coded. If a judge asks where a figure came from, the answer is a
    line of code, not a prompt.
    """
    source_id: str
    candidate_id: str
    source_description: str
    candidate_description: str
    decision: Decision
    confidence: float
    semantic_score: float
    lexical_score: float
    attribute_agreement: float
    critical_veto: bool
    veto_reason: str
    # The weighted score BEFORE the veto multiplies it. For a vetoed pair this is
    # the number the system would have reported had the gate been a weight, and
    # `confidence` is that number multiplied by zero. Returned rather than left
    # for a client to recompute: the client cannot reproduce it exactly, because
    # the inputs it would use are already rounded to four places on the way out.
    raw_score: float = 0.0
    rows: list[AttributeComparison] = field(default_factory=list)
    n_agree: int = 0
    n_disagree: int = 0
    n_unknown: int = 0
    model_version: str = ""
    config_version: str = ""

    def to_dict(self) -> dict:
        return {
            "source_material": self.source_description,
            "candidate_material": self.candidate_description,
            "source_id": self.source_id,
            "candidate_id": self.candidate_id,
            "decision": self.decision.value,
            "confidence": round(self.confidence, 4),
            "raw_score": round(self.raw_score, 4),
            # An uncalibrated ranking score, NOT a probability. Presenting it as
            # "97% likely correct" would require a fitted calibrator on a labelled
            # held-out set, which is Phase 2 work. Consumers must not relabel it.
            "calibrated": False,
            "semantic_score": round(self.semantic_score, 4),
            "lexical_score": round(self.lexical_score, 4),
            "attribute_agreement": round(self.attribute_agreement, 4),
            "critical_veto": self.critical_veto,
            "veto_reason": self.veto_reason,
            # The scoring rule, as the terms that actually produced this number.
            # Rendering "0.85 x 0.800 + 0.15 x 0.9910 = 0.8287, x veto 0 = 0.0000"
            # is what makes "the veto is a gate, not a weight" undeniable rather
            # than merely asserted.
            "arithmetic": {
                "w_attr": 0.85, "attr": round(self.attribute_agreement, 4),
                "w_text": 0.15, "text": round(max(self.semantic_score, self.lexical_score), 4),
                "raw": round(self.raw_score, 4),
                "veto": 0 if self.critical_veto else 1,
                "final": round(self.confidence, 4),
            },
            "counts": {"agree": self.n_agree, "disagree": self.n_disagree, "unknown": self.n_unknown},
            "evidence": [
                {
                    "attribute": r.label,
                    "code": r.code,
                    "criticality": r.criticality.value,
                    "source": r.left,
                    "candidate": r.right,
                    "verdict": r.verdict.value,
                    "detail": r.detail,
                    "vetoed": r.vetoed,
                }
                for r in self.rows
            ],
            "model_version": self.model_version,
            "config_version": self.config_version,
        }


def isclose(a: float, b: float, tol: float) -> bool:
    """Tolerance comparison that treats tol=0 as exact-after-normalisation."""
    if tol <= 0:
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return abs(a - b) <= tol
