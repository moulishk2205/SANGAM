"""
Specification-aware comparison: the component that decides identity.

This is the architectural heart of the project. Everything upstream proposes; this
decides. The rule it enforces:

    A genuine disagreement on a CRITICAL attribute forces DISTINCT, regardless of
    how similar the text is.

Not a penalty, not a weight — a gate. A weighted blend can always be overwhelmed by a
strong text signal, and for `M10x50` vs `M10x75` the text signal is overwhelming
(cosine ~0.98, higher than for many true duplicates). Under a gate the wrong answer is
not unlikely, it is unreachable.

Three-valued by construction: AGREE / DISAGREE / UNKNOWN. UNKNOWN is what a missing
attribute produces, and it never vetoes and never counts as agreement. Conflating
UNKNOWN with DISAGREE destroys recall on sparse records; conflating it with AGREE
destroys precision. Both mistakes are common and neither is recoverable downstream.
"""
from __future__ import annotations

from ..extract.templates import ATTRIBUTES, spec, template_for
from ..types import (
    AttributeComparison,
    Categorical,
    Criticality,
    MaterialRecord,
    Point,
    Quantity,
    Range,
    ValueSet,
    Value,
    Verdict,
    isclose,
)


def _fmt(v: Value) -> str:
    return "—" if v is None else str(v)


def _num_verdict(a: Quantity, b: Quantity, code: str) -> tuple[Verdict, str]:
    """Point vs point, with the attribute's own tolerance policy."""
    if a.unit != b.unit:
        # Dimensional incompatibility is a hard difference, not a near miss.
        return Verdict.DISAGREE, f"incomparable units ({a.unit} vs {b.unit})"
    tol = spec(code).tolerance_for(a.value, b.value)
    if isclose(a.value, b.value, tol):
        return Verdict.AGREE, (f"equal within {tol:g} {a.unit}" if tol else "exactly equal")
    delta = abs(a.value - b.value)
    return Verdict.DISAGREE, (
        f"differs by {delta:g} {a.unit}" + (f", tolerance {tol:g} {a.unit}" if tol else "")
    )


def _compare_values(left: Value, right: Value, code: str) -> tuple[Verdict, str]:
    """
    Compare two attribute values of any shape.

    Handles the four shapes Sprint 0 found in real data — point, range, set,
    categorical — plus every mixed pairing, because real catalogues mix them freely.
    """
    if left is None or right is None:
        return Verdict.UNKNOWN, "not stated on one side"

    # --- numeric shapes ---------------------------------------------------------
    if isinstance(left, Point) and isinstance(right, Point):
        return _num_verdict(left.q, right.q, code)

    if isinstance(left, Range) and isinstance(right, Range):
        if left.unit != right.unit:
            return Verdict.DISAGREE, f"incomparable units ({left.unit} vs {right.unit})"
        if left.overlaps(right):
            return Verdict.AGREE, "tolerance ranges overlap"
        return Verdict.DISAGREE, f"ranges are disjoint ({left} vs {right})"

    # A point against a range: the point has to fall inside the interval. This is the
    # common real case — one CPSE records a nominal, another records the tolerance band.
    if isinstance(left, Point) and isinstance(right, Range):
        return ((Verdict.AGREE, f"{left} lies within {right}")
                if right.contains(left.q) else (Verdict.DISAGREE, f"{left} outside {right}"))
    if isinstance(left, Range) and isinstance(right, Point):
        return ((Verdict.AGREE, f"{right} lies within {left}")
                if left.contains(right.q) else (Verdict.DISAGREE, f"{right} outside {left}"))

    # --- set shapes -------------------------------------------------------------
    # Multi-valued attributes (MATERIAL carries up to 72 values on a real item) need
    # set semantics. Disjoint sets are a real difference; any overlap is treated as
    # agreement because catalogues routinely list permitted alternatives.
    if isinstance(left, ValueSet) or isinstance(right, ValueSet):
        ls = left.codes if isinstance(left, ValueSet) else {left.code} if isinstance(left, Categorical) else set()
        rs = right.codes if isinstance(right, ValueSet) else {right.code} if isinstance(right, Categorical) else set()
        if not ls or not rs:
            return Verdict.UNKNOWN, "not stated on one side"
        if ls == rs:
            return Verdict.AGREE, "identical"
        inter = ls & rs
        if inter:
            return Verdict.AGREE, f"overlapping ({', '.join(sorted(inter))})"
        return Verdict.DISAGREE, f"disjoint ({', '.join(sorted(ls))} vs {', '.join(sorted(rs))})"

    # --- categorical ------------------------------------------------------------
    if isinstance(left, Categorical) and isinstance(right, Categorical):
        if left.code == right.code:
            return Verdict.AGREE, "identical"
        return Verdict.DISAGREE, f"{left.code} vs {right.code}"

    return Verdict.UNKNOWN, "not comparable"


def compare(source: MaterialRecord, candidate: MaterialRecord) -> list[AttributeComparison]:
    """
    Build the evidence table.

    The template is chosen by the source's item type, unioned with the candidate's, so
    a bolt-vs-nut comparison still shows ITEM_NAME as the row that fired the veto
    rather than silently comparing nothing.
    """
    codes = template_for(source.item_name)
    for c in template_for(candidate.item_name):
        if c not in codes:
            codes.append(c)

    rows: list[AttributeComparison] = []
    for code in codes:
        sp = ATTRIBUTES.get(code)
        if sp is None:
            continue
        lv, rv = source.get(code), candidate.get(code)
        verdict, detail = _compare_values(lv, rv, code)
        vetoed = verdict is Verdict.DISAGREE and sp.criticality is Criticality.CRITICAL
        rows.append(AttributeComparison(
            code=code, label=sp.label, criticality=sp.criticality,
            left=_fmt(lv), right=_fmt(rv),
            verdict=verdict, detail=detail, vetoed=vetoed,
        ))
    return rows


def veto(rows: list[AttributeComparison]) -> tuple[bool, str]:
    """
    Did any CRITICAL attribute genuinely disagree?

    Returns the reason in the reviewer's language, because "why was this rejected" is
    the question the evidence panel exists to answer.
    """
    for r in rows:
        if r.vetoed:
            return True, f"{r.label}: {r.left} vs {r.right} — {r.detail}"
    return False, ""


def agreement(rows: list[AttributeComparison]) -> tuple[float, int, int, int]:
    """
    Attribute agreement over the attributes that are actually KNOWN on both sides.

    Unknowns are excluded from the denominator rather than counted against the pair.
    A record that states three attributes and agrees on all three scores 1.0, and the
    uncertainty shows up as a low known-count, which the scorer handles separately.
    """
    agree = sum(1 for r in rows if r.verdict is Verdict.AGREE)
    dis = sum(1 for r in rows if r.verdict is Verdict.DISAGREE)
    unk = sum(1 for r in rows if r.verdict is Verdict.UNKNOWN)
    known = agree + dis
    return (agree / known if known else 0.0), agree, dis, unk
