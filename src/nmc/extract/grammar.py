"""
Attribute extraction: turn a normalised description into typed, unit-canonical values.

Layer 1 of the three-layer cascade from the Phase 0 plan — a deterministic grammar.
It is deliberately the first thing that runs and the only thing that touches numbers:
a transformer must never be the component that decides whether 50 equals 50.

Every extracted value carries the rule that produced it, so the evidence panel can
show *why* a value was read the way it was — including when a unit was inferred
rather than stated, which is exactly the kind of quiet assumption that ought to be
visible to a reviewer.
"""
from __future__ import annotations

import re

from ..normalise.text import Normalised
from ..types import Categorical, MaterialRecord, Point, Quantity, ValueSet

# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------
# Pint is the right tool and is a project dependency, but a 4-entry lookup is faster
# to call in a tight loop and cannot raise on a malformed unit mid-request. Pint is
# used at template-definition time; this table is the hot path.
_TO_MM = {"MM": 1.0, "CM": 10.0, "M": 1000.0, "IN": 25.4}


def _to_mm(value: float, unit: str) -> tuple[float, str]:
    f = _TO_MM.get(unit.upper())
    return (value * f, "mm") if f else (value, unit.lower())


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

# R01 metric thread + length:  M10 X 50   /  M10X1.5 X 50
_R_METRIC_THREAD_LEN = re.compile(
    r"\bM(?P<dia>\d+(?:\.\d+)?)(?:\s*X\s*(?P<pitch>\d\.\d+))?\s*X\s*(?P<len>\d+(?:\.\d+)?)\s*(?P<unit>MM|CM|M|IN)?\b"
)
# R02 bare metric thread designator: M10
_R_METRIC_THREAD = re.compile(r"\bM(?P<dia>\d+(?:\.\d+)?)(?:\s*X\s*(?P<pitch>\d\.\d+))?\b")

# R03 explicit diameter phrase: 10 MM DIAMETER
_R_DIA_PHRASE = re.compile(
    r"\b(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>MM|CM|M|IN)?\s*(?:DIAMETER|DIA)\b"
)
# R04 explicit length phrase: 50 MM LENGTH
_R_LEN_PHRASE = re.compile(
    r"\b(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>MM|CM|M|IN)?\s*(?:LENGTH|LONG|LG)\b"
)
# R05 bare dimension pair: 10 MM X 50 MM
_R_DIM_PAIR = re.compile(
    r"\b(?P<a>\d+(?:\.\d+)?)\s*(?P<ua>MM|CM|M|IN)?\s*X\s*(?P<b>\d+(?:\.\d+)?)\s*(?P<ub>MM|CM|M|IN)?\b"
)
# R05b adjacent dimensions with the separator omitted: '10MM 50MM'.
# Storekeepers drop the 'x' constantly. Both sides must carry an explicit unit,
# which keeps this from firing on a quantity or a part number.
_R_DIM_ADJACENT = re.compile(
    r"\b(?P<a>\d+(?:\.\d+)?)\s*(?P<ua>MM|CM|IN)\s+(?P<b>\d+(?:\.\d+)?)\s*(?P<ub>MM|CM|IN)\b"
)

# R06 property class / grade
_R_GRADE = re.compile(r"\b(?:GRADE\s*)?(?P<g>(?:A[24]-\d{2})|(?:\d\.\d)|(?:8\.8|10\.9|12\.9))\b")
# R07 standards reference
_R_STANDARD = re.compile(r"\b(?P<s>(?:IS|DIN|ISO|ASTM|ANSI|BS|EN)\s*\d+[A-Z0-9\-]*)\b")
# R08 pressure class
_R_PRESSURE = re.compile(r"\b(?:PRESSURE\s+NOMINAL\s*|PN\s*|CLASS\s*|#)(?P<p>\d{2,4})\b")
# R09 bearing-style part number: 6205-2RS, 6205 2RS, 6205ZZ
_R_BEARING_PN = re.compile(r"\b(?P<pn>\d{4,5}\s*-?\s*(?:2RS|RS|ZZ|Z|2Z|C3|N|NR)?)\b")
# R10 nominal bore / pipe size
_R_NB = re.compile(r"\b(?P<v>\d+(?:\.\d+)?)\s*(?P<u>MM|IN)?\s*(?:NOMINAL BORE|NB|NOMINAL PIPE SIZE|NPS)\b")

MATERIAL_TERMS: dict[str, str] = {
    "STAINLESS STEEL": "STAINLESS_STEEL",
    "MILD STEEL": "MILD_STEEL",
    "CARBON STEEL": "CARBON_STEEL",
    "GALVANISED IRON": "GALVANISED_IRON",
    "CAST IRON": "CAST_IRON",
    "ALUMINIUM": "ALUMINIUM",
    "COPPER": "COPPER",
    "BRASS": "BRASS",
    "BRONZE": "BRONZE",
    "MONEL": "MONEL",
    "INCONEL": "INCONEL",
    "TITANIUM": "TITANIUM",
    "POLYVINYL CHLORIDE": "PVC",
    "NITRILE": "NITRILE",
    "GRAPHITE": "GRAPHITE",
}
# Grade suffixes that make a material genuinely different (SS304 != SS316).
_R_SS_GRADE = re.compile(r"\b(?:SS|STAINLESS STEEL)\s*(?P<g>2\d{2}|3\d{2}|4\d{2})\b")

HEAD_STYLES: dict[str, str] = {
    "HEXAGONAL": "HEX",
    "SOCKET": "SOCKET",
    "COUNTERSUNK": "COUNTERSUNK",
    "ROUND": "ROUND",
    "SQUARE": "SQUARE",
    "CHEESE": "CHEESE",
    "PAN": "PAN",
    "FLANGE": "FLANGE",
}

SURFACE_TERMS: dict[str, str] = {
    "GALVANISED": "GALVANISED",
    "ZINC PLATED": "ZINC_PLATED",
    "ZINC": "ZINC_PLATED",
    "CHROME": "CHROME_PLATED",
    "BLACK OXIDE": "BLACK_OXIDE",
    "PLAIN": "PLAIN",
}


def extract(rec: MaterialRecord, n: Normalised, item_name: str) -> MaterialRecord:
    """
    Fill `rec.attributes` from the normalised text.

    Only writes an attribute when a rule actually fires. An attribute that is absent
    is UNKNOWN, and UNKNOWN is never negative evidence downstream — so silence here is
    safe, whereas guessing is not.
    """
    t = n.text

    if item_name:
        rec.set("ITEM_NAME", Categorical(item_name, item_name), "gazetteer:item-name-v1", item_name)

    # --- thread + length, the veto attributes ------------------------------------
    m = _R_METRIC_THREAD_LEN.search(t)
    if m:
        dia = float(m.group("dia"))
        rec.set("THREAD_DIA", Point(Quantity(dia, "mm")), "rule:R01", m.group(0),
                inferred_unit="mm")           # 'M' prefix implies millimetres
        ln, unit = float(m.group("len")), (m.group("unit") or "MM")
        v, u = _to_mm(ln, unit)
        rec.set("LENGTH", Point(Quantity(v, u)), "rule:R01", m.group(0),
                inferred_unit="" if m.group("unit") else "mm")
        if m.group("pitch"):
            rec.set("THREAD_PITCH", Point(Quantity(float(m.group("pitch")), "mm")), "rule:R01", m.group(0))
    else:
        m2 = _R_METRIC_THREAD.search(t)
        if m2:
            rec.set("THREAD_DIA", Point(Quantity(float(m2.group("dia")), "mm")),
                    "rule:R02", m2.group(0), inferred_unit="mm")
            if m2.group("pitch"):
                rec.set("THREAD_PITCH", Point(Quantity(float(m2.group("pitch")), "mm")),
                        "rule:R02", m2.group(0))

    if not rec.attr("THREAD_DIA"):
        m3 = _R_DIA_PHRASE.search(t)
        if m3:
            v, u = _to_mm(float(m3.group("val")), m3.group("unit") or "MM")
            rec.set("THREAD_DIA", Point(Quantity(v, u)), "rule:R03", m3.group(0),
                    inferred_unit="" if m3.group("unit") else "mm")

    if not rec.attr("LENGTH"):
        m4 = _R_LEN_PHRASE.search(t)
        if m4:
            v, u = _to_mm(float(m4.group("val")), m4.group("unit") or "MM")
            rec.set("LENGTH", Point(Quantity(v, u)), "rule:R04", m4.group(0),
                    inferred_unit="" if m4.group("unit") else "mm")

    # bare '10 MM X 50 MM', then '10MM 50MM' — only if we still lack both, so neither
    # can override the explicit metric-thread reading from R01.
    if not rec.attr("THREAD_DIA") and not rec.attr("LENGTH"):
        m5 = _R_DIM_PAIR.search(t) or _R_DIM_ADJACENT.search(t)
        if m5:
            rule = "rule:R05" if _R_DIM_PAIR.match(m5.group(0)) else "rule:R05b"
            a, ua = _to_mm(float(m5.group("a")), m5.group("ua") or "MM")
            b, ub = _to_mm(float(m5.group("b")), m5.group("ub") or "MM")
            rec.set("THREAD_DIA", Point(Quantity(a, ua)), rule, m5.group(0),
                    inferred_unit="" if m5.group("ua") else "mm")
            rec.set("LENGTH", Point(Quantity(b, ub)), rule, m5.group(0),
                    inferred_unit="" if m5.group("ub") else "mm")

    # --- material: multi-valued by design ----------------------------------------
    mats: list[str] = []
    g = _R_SS_GRADE.search(t)
    if g:
        mats.append(f"STAINLESS_STEEL_{g.group('g')}")
    for term, code in MATERIAL_TERMS.items():
        if term in t:
            # a graded stainless entry supersedes the ungraded one
            if code == "STAINLESS_STEEL" and g:
                continue
            mats.append(code)
    if mats:
        rec.set("MATERIAL", ValueSet.of(mats), "gazetteer:material-v1", ", ".join(mats))

    # --- categorical trim ---------------------------------------------------------
    for term, code in HEAD_STYLES.items():
        if term in t:
            rec.set("HEAD_STYLE", Categorical(code, term), "gazetteer:head-v1", term)
            break
    for term, code in SURFACE_TERMS.items():
        if term in t:
            rec.set("SURFACE_TREATMENT", Categorical(code, term), "gazetteer:surface-v1", term)
            break

    mg = _R_GRADE.search(t)
    if mg:
        rec.set("GRADE", Categorical(mg.group("g")), "rule:R06", mg.group(0))
    ms = _R_STANDARD.search(t)
    if ms:
        rec.set("STANDARD", Categorical(re.sub(r"\s+", " ", ms.group("s"))), "rule:R07", ms.group(0))
    mp = _R_PRESSURE.search(t)
    if mp:
        rec.set("PRESSURE_CLASS", Categorical(mp.group("p")), "rule:R08", mp.group(0))
    mn = _R_NB.search(t)
    if mn:
        v, u = _to_mm(float(mn.group("v")), mn.group("u") or "MM")
        rec.set("NOMINAL_SIZE", Point(Quantity(v, u)), "rule:R10", mn.group(0))

    # bearings are identified by reference, not description
    if item_name.startswith("BEARING"):
        mb = _R_BEARING_PN.search(t)
        if mb:
            pn = re.sub(r"[\s-]", "", mb.group("pn"))
            rec.set("PART_NUMBER", Categorical(pn), "rule:R09", mb.group(0))
            if len(pn) >= 4 and pn[:4].isdigit():
                # ISO bearing designation: digits 3-4 x 5 = bore in mm, for 04 and up
                code = int(pn[2:4])
                if code >= 4:
                    rec.set("BORE", Point(Quantity(code * 5.0, "mm")), "rule:R09-bore", pn[:4],
                            inferred_unit="mm")

    return rec


def coverage(rec: MaterialRecord, codes: list[str]) -> float:
    """Fraction of the template this record actually populated — the extraction metric."""
    if not codes:
        return 0.0
    return sum(1 for c in codes if rec.attr(c) and rec.attr(c).known) / len(codes)
