"""
Functional equivalence — a relation that sits ABOVE identity, never inside it.

WHY THIS IS A SEPARATE LAYER

The matching engine answers "are these the same material?" and must keep
answering it strictly: an M10x50 A2-70 bolt and an M10x50 A4-80 bolt are
different materials, they get different national codes, and the engine is right
to call them DISTINCT. Nothing here changes that, and nothing here can: this
module never touches `engine.py`, never adjusts a threshold, and never produces
a MATCH.

But procurement does not buy identities, it buys things that will do the job.
If CPSE-A needs 10,000 A2-70 bolts and CPSE-B needs 15,000 A4-80 bolts of the
same size, a single tender for 25,000 A4-80 bolts satisfies both — because A4-80
covers everything A2-70 does. Demand aggregation, which is where the money in
this problem statement actually is, depends on that relation and not on identity.

THE THREE RULES THAT KEEP THIS HONEST

1. INTERFACE ATTRIBUTES MUST MATCH EXACTLY, NEVER APPROXIMATELY.
   Thread, length, pressure class, facing, valve type — these must be equal.
   Equivalence is never inferred from dimensional *similarity*; M10 and M12 are
   not "close enough" here any more than they are to the matcher.

2. SUBSTITUTION IS DIRECTIONAL.
   A4-80 substitutes for A2-70. A2-70 does NOT substitute for A4-80. Treating
   equivalence as symmetric is how a stronger requirement silently gets filled
   with a weaker part. Every result names which material covers which.

3. SAFETY-CRITICAL SERVICE REFUSES TO ANSWER.
   In SOUR service, NACE MR0175/ISO 15156 constrains materials by hardness,
   heat treatment and composition — facts a two-axis rank model does not hold.
   In FIRED service, OISD-STD-150 governs. This module returns NOT_EQUIVALENT
   with an explicit "requires a materials engineer" reason rather than guessing.
   Refusing is the correct output when the input cannot support a claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .extract.templates import ITEM_NAMES

EQUIVALENCE_VERSION = "equiv-v1"


class Equivalence(str, Enum):
    IDENTICAL = "IDENTICAL"                          # same identity
    FUNCTIONALLY_EQUIVALENT = "FUNCTIONALLY_EQUIVALENT"
    NOT_EQUIVALENT = "NOT_EQUIVALENT"                # differs in a way that blocks it
    UNDETERMINED = "UNDETERMINED"                    # safety class we will not rule on


# Attributes that define how the part physically fits and functions. Any
# difference here ends the analysis — no substitution rule can rescue it.
INTERFACE_ATTRIBUTES: frozenset[str] = frozenset({
    "ITEM_NAME", "THREAD_DIA", "THREAD_PITCH", "LENGTH", "NOMINAL_SIZE", "BORE",
    "PRESSURE_CLASS", "SCHEDULE", "VALVE_TYPE", "FLANGE_TYPE", "FACING",
    "HEAD_STYLE", "PART_NUMBER",
})

# Attributes where a better part may stand in for a lesser one.
SUBSTITUTABLE_ATTRIBUTES: frozenset[str] = frozenset({
    "MATERIAL", "GRADE", "SURFACE_TREATMENT", "STANDARD", "CONSTRUCTION",
})

# Two axes, not one. A single "quality" number would rank alloy steel above
# stainless on strength and hide that it corrodes, which is exactly the mistake
# that puts the wrong bolt in a coastal plant.
#                          strength, corrosion
MATERIAL_CAPABILITY: dict[str, tuple[int, int]] = {
    "MILD_STEEL":       (1, 1),
    "CARBON_STEEL":     (2, 1),
    "GALVANISED_IRON":  (2, 2),
    "ALLOY_STEEL":      (4, 1),
    "STAINLESS_STEEL":  (3, 4),
    "BRASS":            (1, 3),
    "COPPER":           (1, 3),
    "CAST_IRON":        (1, 1),
    "DUCTILE_IRON":     (2, 1),
    "ALUMINIUM":        (1, 2),
}

# Fastener property classes. A2/A4 are austenitic stainless per ISO 3506;
# 4.6/8.8/10.9/12.9 are carbon and alloy steel per ISO 898-1.
GRADE_CAPABILITY: dict[str, tuple[int, int]] = {
    "4.6": (1, 1), "5.8": (2, 1), "8.8": (3, 1), "10.9": (4, 1), "12.9": (5, 1),
    "A2-50": (1, 4), "A2-70": (2, 4), "A2-80": (3, 4),
    "A4-70": (2, 5), "A4-80": (3, 5),
}

# Pipe construction: seamless has no weld seam and is accepted where welded is,
# but not the reverse.
CONSTRUCTION_CAPABILITY: dict[str, tuple[int, int]] = {
    "WELDED": (1, 1), "ERW": (1, 1), "SEAMLESS": (2, 1),
}

# Service classes this module will rule on, and those it will not.
OPEN_SERVICE_CLASSES = {"GENERAL", "PRESSURE"}
RESTRICTED_SERVICE_CLASSES = {
    "SOUR": "NACE MR0175 / ISO 15156 constrains materials by hardness, heat "
            "treatment and composition. That cannot be decided from a "
            "capability rank — a materials engineer must rule on it.",
    "FIRED": "OISD-STD-150 governs fired-equipment service. Substitution here "
             "requires an engineering assessment, not a catalogue rule.",
}


@dataclass
class AttributeDelta:
    code: str
    left: str
    right: str
    kind: str                 # "interface" | "substitutable" | "informational"
    permitted: bool
    direction: str            # "left_covers_right" | "right_covers_left" | "" | "n/a"
    reason: str


@dataclass
class EquivalenceResult:
    verdict: Equivalence
    service_class: str
    summary: str
    covering: str | None = None      # which side can satisfy both, if either
    deltas: list[AttributeDelta] = field(default_factory=list)
    version: str = EQUIVALENCE_VERSION

    @property
    def aggregatable(self) -> bool:
        """Whether procurement may combine demand across these two materials."""
        return self.verdict in (Equivalence.IDENTICAL, Equivalence.FUNCTIONALLY_EQUIVALENT)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "service_class": self.service_class,
            "summary": self.summary,
            "covering": self.covering,
            "aggregatable": self.aggregatable,
            "version": self.version,
            "deltas": [
                {"code": d.code, "left": d.left, "right": d.right, "kind": d.kind,
                 "permitted": d.permitted, "direction": d.direction, "reason": d.reason}
                for d in self.deltas
            ],
        }


def _cap(table: dict[str, tuple[int, int]], value: str) -> tuple[int, int] | None:
    return table.get(str(value).strip().upper().replace(" ", "_"))


def _covers(cap_a: tuple[int, int], cap_b: tuple[int, int]) -> bool:
    """A covers B when it is at least as capable on BOTH axes."""
    return cap_a[0] >= cap_b[0] and cap_a[1] >= cap_b[1]


_TABLES = {
    "MATERIAL": MATERIAL_CAPABILITY,
    "GRADE": GRADE_CAPABILITY,
    "CONSTRUCTION": CONSTRUCTION_CAPABILITY,
}


def compare(left_item: str, left_attrs: dict[str, str],
            right_item: str, right_attrs: dict[str, str],
            service_class: str = "GENERAL") -> EquivalenceResult:
    """
    Can one of these two materials satisfy demand for the other?

    Deliberately NOT a similarity score. The output is a verdict, a direction
    and the list of attribute differences that produced it, so a procurement
    officer can see exactly which difference permitted or blocked aggregation.
    """
    sc = (service_class or "GENERAL").upper()
    la = {k: str(v) for k, v in (left_attrs or {}).items() if v not in (None, "")}
    ra = {k: str(v) for k, v in (right_attrs or {}).items() if v not in (None, "")}

    if left_item == right_item and la == ra:
        return EquivalenceResult(Equivalence.IDENTICAL, sc,
                                 "Same item and same attribute set — one identity.",
                                 covering="both")

    # A different item type is a different thing. No rule rescues a nut standing
    # in for a bolt.
    if left_item != right_item:
        return EquivalenceResult(
            Equivalence.NOT_EQUIVALENT, sc,
            f"Different item type: {left_item or '?'} vs {right_item or '?'}.",
            deltas=[AttributeDelta("ITEM_NAME", left_item, right_item, "interface",
                                   False, "n/a", "Item type must be identical.")])

    deltas: list[AttributeDelta] = []
    allowed = set(ITEM_NAMES.get(left_item, {}).get("attributes", [])) or set(la) | set(ra)

    # ── 1. interface: must be equal, never merely close ────────────────────
    for code in sorted(allowed & INTERFACE_ATTRIBUTES):
        lv, rv = la.get(code, ""), ra.get(code, "")
        if lv == rv:
            continue
        if not lv or not rv:
            deltas.append(AttributeDelta(
                code, lv or "(not stated)", rv or "(not stated)", "interface",
                False, "n/a",
                "Interface attribute unstated on one side — cannot confirm fit."))
            continue
        deltas.append(AttributeDelta(
            code, lv, rv, "interface", False, "n/a",
            "Interface attribute differs. Equivalence is never inferred from "
            "dimensional similarity."))

    if any(d.kind == "interface" for d in deltas):
        blocking = ", ".join(d.code for d in deltas if d.kind == "interface")
        return EquivalenceResult(
            Equivalence.NOT_EQUIVALENT, sc,
            f"Physical interface differs ({blocking}). These parts do not "
            f"interchange regardless of material.", deltas=deltas)

    # ── 2. restricted service: refuse rather than guess ────────────────────
    subs_differ = [c for c in sorted(allowed & SUBSTITUTABLE_ATTRIBUTES)
                   if la.get(c, "") != ra.get(c, "")]
    if sc in RESTRICTED_SERVICE_CLASSES and subs_differ:
        for c in subs_differ:
            deltas.append(AttributeDelta(
                c, la.get(c, "(not stated)"), ra.get(c, "(not stated)"),
                "substitutable", False, "n/a", RESTRICTED_SERVICE_CLASSES[sc]))
        return EquivalenceResult(
            Equivalence.UNDETERMINED, sc,
            f"{sc} service — this system will not rule on substitution. "
            + RESTRICTED_SERVICE_CLASSES[sc], deltas=deltas)

    # ── 3. substitutable attributes, directionally ─────────────────────────
    left_covers = right_covers = True
    for code in sorted(allowed & SUBSTITUTABLE_ATTRIBUTES):
        lv, rv = la.get(code, ""), ra.get(code, "")
        if lv == rv:
            continue

        table = _TABLES.get(code)
        if table is None:
            # STANDARD, SURFACE_TREATMENT: a difference is recorded but does not
            # block. Citing the same part against IS 1367 and DIN 933 is common
            # and is not a functional difference.
            deltas.append(AttributeDelta(
                code, lv or "(not stated)", rv or "(not stated)", "informational",
                True, "n/a",
                "Recorded for the reviewer; not treated as a functional difference."))
            continue

        cl, cr = _cap(table, lv), _cap(table, rv)
        if cl is None or cr is None:
            unknown = lv if cl is None else rv
            left_covers = right_covers = False
            deltas.append(AttributeDelta(
                code, lv or "(not stated)", rv or "(not stated)", "substitutable",
                False, "n/a",
                f"'{unknown or 'not stated'}' is not in the capability table — "
                f"no substitution claim can be made."))
            continue

        l_ok, r_ok = _covers(cl, cr), _covers(cr, cl)
        left_covers &= l_ok
        right_covers &= r_ok
        if l_ok and not r_ok:
            direction, reason = "left_covers_right", (
                f"{lv} meets or exceeds {rv} on strength {cl[0]}>={cr[0]} and "
                f"corrosion {cl[1]}>={cr[1]}.")
        elif r_ok and not l_ok:
            direction, reason = "right_covers_left", (
                f"{rv} meets or exceeds {lv} on strength {cr[0]}>={cl[0]} and "
                f"corrosion {cr[1]}>={cl[1]}.")
        elif l_ok and r_ok:
            direction, reason = "either", "Equal capability on both axes."
        else:
            direction, reason = "", (
                f"Neither covers the other: {lv} is {cl}, {rv} is {cr} "
                f"(strength, corrosion). Each is better on a different axis.")
        deltas.append(AttributeDelta(code, lv, rv, "substitutable",
                                     l_ok or r_ok, direction, reason))

    if not any(d.kind == "substitutable" for d in deltas):
        return EquivalenceResult(
            Equivalence.IDENTICAL, sc,
            "Identical on every attribute that affects fit or function.",
            covering="both", deltas=deltas)

    if left_covers or right_covers:
        covering = "both" if (left_covers and right_covers) else (
            "left" if left_covers else "right")
        moved = ", ".join(d.code for d in deltas if d.kind == "substitutable")
        return EquivalenceResult(
            Equivalence.FUNCTIONALLY_EQUIVALENT, sc,
            f"Interchangeable in {sc} service. Differs on {moved}, and the "
            f"{'either side' if covering == 'both' else covering + '-hand'} "
            f"material covers the other.", covering=covering, deltas=deltas)

    blocked = ", ".join(d.code for d in deltas if d.kind == "substitutable" and not d.permitted)
    return EquivalenceResult(
        Equivalence.NOT_EQUIVALENT, sc,
        f"Neither material covers the other on {blocked or 'the differing attributes'}.",
        deltas=deltas)
