"""
The standard description.

WHAT WAS WRONG BEFORE

The canonical text was inherited from whichever member record happened to be
first in its group. So the national standard description for a material was, in
effect, one CPSE's house style — `BOLT HEX MS M10*75` — promoted to national
status by an accident of sort order. Two identical materials discovered in a
different order would have been described differently.

WHAT THIS IS

A description generated from the canonical attributes in a fixed order, with
normalised vocabulary and units:

    BOLT, MACHINE — STAINLESS STEEL — M10 × 50 — A2-70 — IS 1364

The order is the item's own template order, filtered to the attributes worth
printing, so it is consistent within a family without being hand-maintained per
family. Missing attributes are omitted rather than printed empty: a description
with a gap in it is worse than a shorter description, because the gap reads as
a value nobody filled in.

The guarantee that matters: the same canonical attribute set always yields the
same string, whatever the source records said. That is what makes it usable as
a procurement-facing description on a tender document.
"""
from __future__ import annotations

import re

from ..extract.templates import ITEM_NAMES, template_for

# Storage form -> printed form. The extractor normalises to underscored upper
# case because that is a good key; nobody wants to read it on an indent.
MATERIAL_TEXT: dict[str, str] = {
    "STAINLESS_STEEL": "STAINLESS STEEL", "CARBON_STEEL": "CARBON STEEL",
    "MILD_STEEL": "MILD STEEL", "GALVANISED_IRON": "GALVANISED IRON",
    "ALLOY_STEEL": "ALLOY STEEL", "BRASS": "BRASS", "CAST_IRON": "CAST IRON",
    "DUCTILE_IRON": "DUCTILE IRON", "COPPER": "COPPER", "ALUMINIUM": "ALUMINIUM",
}

# Attributes printed, and how. Order here is the print order within a family;
# anything not listed is omitted from the description even if it is extracted,
# because a description is a label, not a data dump.
_PRINT_ORDER: list[str] = [
    "MATERIAL", "VALVE_TYPE", "FLANGE_TYPE", "CONSTRUCTION", "HEAD_STYLE",
    "THREAD_DIA", "LENGTH", "NOMINAL_SIZE", "BORE", "SCHEDULE",
    "PRESSURE_CLASS", "FACING", "GRADE", "SURFACE_TREATMENT",
    "PART_NUMBER", "STANDARD",
]

_SEP = " — "


def _mm(value: object) -> str | None:
    """A millimetre magnitude, printed without trailing zeros. 10.0 -> '10'."""
    if value is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not m:
        return None
    f = float(m.group())
    return f"{f:g}"


def description_parts(item_name: str, attributes: dict[str, str]) -> list[tuple[str, str]]:
    """
    (label, printed value) in canonical order.

    Returned as pairs rather than a joined string so the UI can render the same
    decomposition it uses everywhere else, and so a reviewer can see which
    attribute produced which fragment.
    """
    a = {k: str(v) for k, v in (attributes or {}).items() if v not in (None, "")}
    allowed = set(template_for(item_name) or []) | {"ITEM_NAME"}
    out: list[tuple[str, str]] = [("Item", item_name or "UNCLASSIFIED")]

    dia = _mm(a.get("THREAD_DIA"))
    length = _mm(a.get("LENGTH"))

    for code in _PRINT_ORDER:
        if code not in allowed or code not in a:
            continue
        raw = a[code]

        if code == "MATERIAL":
            out.append(("Material", MATERIAL_TEXT.get(raw.upper(), raw.replace("_", " "))))
        elif code == "THREAD_DIA":
            # Thread and length read as one dimension to an engineer, so they
            # print as one: "M10 × 50", never "M10 — 50".
            out.append(("Size", f"M{dia} × {length}" if length else f"M{dia}"))
        elif code == "LENGTH":
            if not dia:                       # already folded into Size above
                out.append(("Length", f"{length} MM"))
        elif code in ("NOMINAL_SIZE", "BORE"):
            v = _mm(raw)
            out.append(("Nominal size" if code == "NOMINAL_SIZE" else "Bore",
                        f"DN{v}" if code == "NOMINAL_SIZE" else f"{v} MM"))
        elif code == "PRESSURE_CLASS":
            out.append(("Pressure class", f"CLASS {raw}"))
        elif code == "SCHEDULE":
            out.append(("Schedule", f"SCH {raw}"))
        else:
            label = code.replace("_", " ").title()
            out.append((label, raw.replace("_", " ")))
    return out


def standard_description(item_name: str, attributes: dict[str, str]) -> str:
    """
    The procurement-facing description. Deterministic for a given attribute set.

    `SS HEX BOLT M10X50` and `Stainless steel machine bolt M10x50 A2-70` resolve
    to the same canonical attributes and therefore to the same string here —
    which is the whole point, and what makes this safe to print on a tender.
    """
    parts = description_parts(item_name, attributes)
    return _SEP.join(v for _, v in parts)


def item_family(item_name: str) -> str:
    d = ITEM_NAMES.get(item_name)
    return d["family"] if d else "unknown"
