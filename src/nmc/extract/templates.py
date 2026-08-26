"""
Attribute templates: which attributes exist, and which of them decide identity.

This is the FIIG/MRC idea from the NATO Codification System, reduced to what the MVP
needs. The important property is that criticality is a *property of the item type*,
not a global constant: thread diameter is decisive for a bolt and meaningless for a
gasket, so the template is selected by approved item name first.

Sprint 0 note on provenance
---------------------------
The attribute *structure* here mirrors what FLIS actually records — the empirical
template for BOLT,MACHINE over 31,411 real items shows FASTENER LENGTH at 82.7%,
THREAD LENGTH at 79.1% and NOMINAL THREAD DIAMETER at 61.3% coverage, which is what
justifies making those the veto attributes.

The *values* in the MVP demo corpus are NOT taken from FLIS. FLIS numeric replies are
prefix/mode-coded (`A0.312`, `AB0.889`) and that encoding is not yet decoded, so
comparing them numerically would be unsound. Until the decode is done, the MVP
operates on values whose units we control end to end. That limitation is deliberate
and is recorded in docs/SPRINT0-FINDINGS.md §4(c).
"""
from __future__ import annotations

from ..types import AttributeSpec, Criticality as C

CONFIG_VERSION = "template-v1"

# ---------------------------------------------------------------------------
# Attribute registry
# ---------------------------------------------------------------------------

ATTRIBUTES: dict[str, AttributeSpec] = {
    "ITEM_NAME": AttributeSpec(
        "ITEM_NAME", "Item type", C.CRITICAL,
        provenance="a bolt is not a nut; noun-head disagreement is never a duplicate",
    ),
    "MATERIAL": AttributeSpec(
        "MATERIAL", "Material", C.CRITICAL,
        provenance="SS304 vs SS316 vs carbon steel are different materials, not variants",
    ),
    "THREAD_DIA": AttributeSpec(
        "THREAD_DIA", "Nominal thread diameter", C.CRITICAL, canonical_unit="mm",
        tol_abs=0.0,
        provenance="thread sizes are discrete, not continuous — no tolerance permitted",
    ),
    "LENGTH": AttributeSpec(
        "LENGTH", "Length", C.CRITICAL, canonical_unit="mm",
        tol_abs=0.5,
        provenance="0.5 mm covers rounding between imperial and metric statements of the same part",
    ),
    "THREAD_PITCH": AttributeSpec(
        "THREAD_PITCH", "Thread pitch", C.IMPORTANT, canonical_unit="mm", tol_abs=0.01,
        provenance="coarse vs fine thread is a real difference but often simply unstated",
    ),
    "HEAD_STYLE": AttributeSpec(
        "HEAD_STYLE", "Head style", C.IMPORTANT,
        provenance="hex vs socket vs countersunk changes the tool and the seat",
    ),
    "GRADE": AttributeSpec(
        "GRADE", "Grade / property class", C.IMPORTANT,
        provenance="A2-70 vs A4-80 differ in strength and corrosion behaviour",
    ),
    "NOMINAL_SIZE": AttributeSpec(
        "NOMINAL_SIZE", "Nominal size", C.CRITICAL, canonical_unit="mm", tol_abs=0.5,
        provenance="pipe/valve/flange nominal bore",
    ),
    "PRESSURE_CLASS": AttributeSpec(
        "PRESSURE_CLASS", "Pressure class", C.CRITICAL,
        provenance="pressure rating is a safety characteristic in refinery service",
    ),
    "BORE": AttributeSpec(
        "BORE", "Bore diameter", C.CRITICAL, canonical_unit="mm", tol_abs=0.05,
        provenance="bearing bore is a fit dimension",
    ),
    "STANDARD": AttributeSpec(
        "STANDARD", "Standard", C.MINOR,
        provenance="often the same part cited against different equivalent standards",
    ),
    "PART_NUMBER": AttributeSpec(
        "PART_NUMBER", "Manufacturer part number", C.IMPORTANT,
        provenance="the reference method of identification; strong positive evidence when present",
    ),
    "SURFACE_TREATMENT": AttributeSpec(
        "SURFACE_TREATMENT", "Surface treatment", C.MINOR,
        provenance="plating usually does not change identity but is worth showing",
    ),
}


# ---------------------------------------------------------------------------
# Approved item names
# ---------------------------------------------------------------------------
# Canonical noun-phrase -> the tokens that indicate it, and the attributes that
# decide identity for that item type. Kept small and hand-curated on purpose: this is
# the artefact a materials engineer reviews and signs off.

ITEM_NAMES: dict[str, dict] = {
    "BOLT, MACHINE": {
        "tokens": ["BOLT"],
        "attributes": ["ITEM_NAME", "MATERIAL", "THREAD_DIA", "LENGTH",
                       "THREAD_PITCH", "HEAD_STYLE", "GRADE", "STANDARD", "SURFACE_TREATMENT"],
        "family": "fastener",
    },
    "SCREW, CAP, HEXAGON HEAD": {
        "tokens": ["SCREW", "CAPSCREW"],
        "attributes": ["ITEM_NAME", "MATERIAL", "THREAD_DIA", "LENGTH",
                       "THREAD_PITCH", "HEAD_STYLE", "GRADE", "STANDARD"],
        "family": "fastener",
    },
    "NUT, PLAIN, HEXAGON": {
        "tokens": ["NUT"],
        "attributes": ["ITEM_NAME", "MATERIAL", "THREAD_DIA", "THREAD_PITCH",
                       "GRADE", "STANDARD"],
        "family": "fastener",
    },
    "WASHER, FLAT": {
        "tokens": ["WASHER"],
        "attributes": ["ITEM_NAME", "MATERIAL", "NOMINAL_SIZE", "STANDARD"],
        "family": "fastener",
    },
    "STUD": {
        "tokens": ["STUD"],
        "attributes": ["ITEM_NAME", "MATERIAL", "THREAD_DIA", "LENGTH", "GRADE"],
        "family": "fastener",
    },
    "BEARING, BALL, ANNULAR": {
        "tokens": ["BEARING"],
        "attributes": ["ITEM_NAME", "PART_NUMBER", "BORE", "MATERIAL"],
        "family": "bearing",
    },
    "VALVE, GATE": {
        "tokens": ["VALVE"],
        "attributes": ["ITEM_NAME", "MATERIAL", "NOMINAL_SIZE", "PRESSURE_CLASS", "STANDARD"],
        "family": "valve",
    },
    "GASKET": {
        "tokens": ["GASKET"],
        "attributes": ["ITEM_NAME", "MATERIAL", "NOMINAL_SIZE", "PRESSURE_CLASS"],
        "family": "pipe",
    },
    "FLANGE, PIPE": {
        "tokens": ["FLANGE"],
        "attributes": ["ITEM_NAME", "MATERIAL", "NOMINAL_SIZE", "PRESSURE_CLASS", "STANDARD"],
        "family": "pipe",
    },
}

# token -> canonical item name, longest token first so CAPSCREW beats SCREW
_TOKEN_TO_NAME: list[tuple[str, str]] = sorted(
    ((tok, name) for name, d in ITEM_NAMES.items() for tok in d["tokens"]),
    key=lambda p: len(p[0]), reverse=True,
)


def classify_item_name(tokens: list[str]) -> tuple[str, str]:
    """
    Return (canonical item name, matched token) or ("", "").

    Deliberately dumb and deterministic: a gazetteer lookup over the noun head. An
    embedding model could do this, but then a bolt/nut confusion would be a model
    error instead of a dictionary entry a human can fix.
    """
    upper = [t.upper() for t in tokens]
    for tok, name in _TOKEN_TO_NAME:
        if tok in upper:
            return name, tok
    return "", ""


def template_for(item_name: str) -> list[str]:
    """Attribute codes that matter for this item type, in display order."""
    d = ITEM_NAMES.get(item_name)
    return list(d["attributes"]) if d else ["ITEM_NAME", "MATERIAL"]


def family_for(item_name: str) -> str:
    d = ITEM_NAMES.get(item_name)
    return d["family"] if d else "unknown"


def spec(code: str) -> AttributeSpec:
    return ATTRIBUTES[code]


def critical_codes(item_name: str) -> list[str]:
    return [c for c in template_for(item_name) if ATTRIBUTES[c].criticality is C.CRITICAL]
