"""
Demo corpus generator.

Provenance, stated plainly
--------------------------
Every record this produces is SYNTHETIC. It is generated downward from a canonical
specification we define, then rendered through per-CPSE "house styles". That makes the
positive labels correct *by construction* — two variants are the same material because
they were rendered from the same spec, not because anyone asserted it.

The CPSE names and codes are invented. They are not ONGC/NTPC/IOCL data and must never
be presented as such.

Why not FLIS values here
------------------------
FLIS supplies the real item-name vocabulary and the evidence that these attributes are
the ones a codification authority records. It does not yet supply usable numerics: its
replies are prefix/mode-coded (`A0.312`, `AB0.889`) and that encoding is undecoded, so
numeric comparison against it would be unsound. The MVP therefore uses values whose
units we control end to end. See docs/SPRINT0-FINDINGS.md §4(c).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..types import MaterialRecord

# Invented organisations. Named generically so nobody mistakes them for real CPSEs.
ORGS = [
    ("CPSE-A", "MAT-{:05d}"),
    ("CPSE-B", "BLT-{:05d}"),
    ("CPSE-C", "XJ-{:05d}"),
    ("CPSE-D", "{:06d}"),
]


@dataclass(frozen=True)
class Spec:
    """A canonical material specification. The ground truth for everything below it."""
    family: str
    noun: str
    material: str
    dia_mm: float | None = None
    length_mm: float | None = None
    head: str = ""
    grade: str = ""
    standard: str = ""
    nominal_mm: float | None = None
    pressure: str = ""
    part_number: str = ""
    # piping fields, added alongside the pipe / flange / ball-valve families
    schedule: str = ""
    valve_type: str = ""
    flange_type: str = ""
    facing: str = ""
    construction: str = ""

    def key(self) -> str:
        return "|".join(str(x) for x in (
            self.noun, self.material, self.dia_mm, self.length_mm, self.head,
            self.grade, self.nominal_mm, self.pressure, self.part_number,
            self.schedule, self.valve_type, self.flange_type, self.facing,
            self.construction))


# --- surface-form renderers: the same spec, five storekeepers ------------------
# Each renderer is an identity-preserving transformation. None of them changes a
# value; they only change how it is written.

_MAT_SHORT = {
    "STAINLESS STEEL": "SS", "MILD STEEL": "MS", "CARBON STEEL": "CS",
    "GALVANISED IRON": "GI", "BRASS": "BR", "ALUMINIUM": "AL",
}
_HEAD_SHORT = {"HEXAGONAL": "HEX", "SOCKET": "SKT", "COUNTERSUNK": "CSK", "SQUARE": "SQ"}
_FLANGE_SHORT = {"WELD NECK": "WN", "SLIP ON": "SO", "BLIND": "BLIND",
                 "SOCKET WELD": "SW", "THREADED": "THREADED"}
_FACING_SHORT = {"RAISED FACE": "RF", "FLAT FACE": "FF", "RING TYPE JOINT": "RTJ"}
_CONSTRUCTION_SHORT = {"SEAMLESS": "SMLS", "WELDED": "WELDED",
                       "ELECTRIC RESISTANCE WELDED": "ERW"}

# DN -> NPS, the inverse of the designation table the extractor uses. Rendering a
# size in inches is not a unit conversion: DN 100 is written 4", never 3.94".
_DN_TO_NPS: dict[float, str] = {
    15: "1/2", 20: "3/4", 25: "1", 32: "1.1/4", 40: "1.1/2", 50: "2", 65: "2.1/2",
    80: "3", 100: "4", 150: "6", 200: "8", 250: "10", 300: "12",
}


def _fastener_styles(s: Spec) -> list[str]:
    mat_l, mat_s = s.material, _MAT_SHORT.get(s.material, s.material)
    head_l, head_s = s.head, _HEAD_SHORT.get(s.head, s.head)
    d, L = s.dia_mm, s.length_mm
    di = f"{d:g}" if d and d == int(d) else f"{d}"
    # A nut has no length. Interpolating it unguarded emitted the literal string
    # "None" into the description ("NUT HEX GI M20 X None MM"), which then broke
    # the metric-thread rule and left THREAD_DIA — a CRITICAL attribute —
    # unextracted on every nut written that way.
    if L is None:
        return ([
            f"{mat_s} {head_s} {s.noun} M{di}",
            f"{mat_l} {head_l} {s.noun} {di}MM",
            f"{s.noun} {head_s} {mat_s} M{di}",
            f"{head_l} {s.noun} - {mat_s} - {di}MM DIA",
        ] + ([f"{mat_s} {head_s} {s.noun} M{di} GR {s.grade}"] if s.grade else [])
           + ([f"{s.noun} {head_s} {mat_s} {s.standard} M{di}"] if s.standard else []))
    Li = f"{L:g}" if L == int(L) else f"{L}"
    out = [
        f"{mat_s} {head_s} {s.noun} M{di} X {Li}",
        f"{mat_l} {head_l} {s.noun} {di}MM X {Li}MM",
        f"{s.noun} {head_s} {mat_s} M{di}*{Li}",
        f"{head_l} {s.noun} - {mat_s} - {di}MM DIA - {Li}MM LG",
        f"{s.noun} {head_s} {mat_s} M{di} X {Li} MM",
        f"{mat_s} {head_s} {s.noun} M{di}X{Li}",
    ]
    if s.grade:
        out.append(f"{mat_s} {head_s} {s.noun} M{di} X {Li} GR {s.grade}")
    if s.standard:
        out.append(f"{s.noun} {head_s} {mat_s} {s.standard} M{di} X {Li}")
    return out


def _valve_styles(s: Spec) -> list[str]:
    mat_s = _MAT_SHORT.get(s.material, s.material)
    n = f"{s.nominal_mm:g}"
    vt = s.valve_type or "GATE"
    out = [
        f"{s.noun} {vt} {mat_s} {n}MM NB PN{s.pressure}",
        f"{s.material} {vt} {s.noun} {n} MM NOMINAL BORE CLASS {s.pressure}",
        f"{s.noun} {mat_s} {vt} {n}NB #{s.pressure}",
        f"{vt} {s.noun} - {mat_s} - {n} MM NB - PN {s.pressure}",
    ]
    nps = _DN_TO_NPS.get(s.nominal_mm)
    if nps:
        out.append(f"{mat_s} {vt} {s.noun} {nps} INCH CLASS {s.pressure}")
        out.append(f'{s.noun} {vt} {mat_s} {nps}" #{s.pressure}')
    return out


def _pipe_styles(s: Spec) -> list[str]:
    """
    One pipe spec, six requisition styles.

    Identity-preserving like every other renderer here: bore, schedule and
    construction survive all six unchanged. Only the spelling moves.
    """
    mat_s = _MAT_SHORT.get(s.material, s.material)
    con_s = _CONSTRUCTION_SHORT.get(s.construction, s.construction)
    n = f"{s.nominal_mm:g}"
    out = [
        f"{mat_s} {con_s} PIPE {n}MM NB SCH {s.schedule}",
        f"{s.material} {s.construction} PIPE {n} MM NOMINAL BORE SCHEDULE {s.schedule}",
        f"PIPE {mat_s} {n}NB SCH{s.schedule} {con_s}",
        f"PIPE - {mat_s} - {n} MM NB - SCH {s.schedule} - {s.construction}",
    ]
    nps = _DN_TO_NPS.get(s.nominal_mm)
    if nps:
        out.append(f"{mat_s} {con_s} PIPE {nps} INCH SCH {s.schedule}")
        out.append(f'PIPE {mat_s} {nps}" SCHEDULE {s.schedule} {con_s}')
    return out


def _flange_styles(s: Spec) -> list[str]:
    mat_s = _MAT_SHORT.get(s.material, s.material)
    ft_s = _FLANGE_SHORT.get(s.flange_type, s.flange_type)
    fc_s = _FACING_SHORT.get(s.facing, s.facing)
    n = f"{s.nominal_mm:g}"
    tail = f" {fc_s}" if fc_s else ""
    tail_l = f" {s.facing}" if s.facing else ""
    out = [
        f"{mat_s} {ft_s}{tail} FLANGE {n}NB CL{s.pressure}",
        f"{s.material} {s.flange_type}{tail_l} FLANGE {n} MM NOMINAL BORE CLASS {s.pressure}",
        f"FLANGE {ft_s} {mat_s} {n} MM NB #{s.pressure}{tail}",
        f"FLANGE - {mat_s} - {s.flange_type} - {n} NB - CLASS {s.pressure}{tail_l}",
    ]
    nps = _DN_TO_NPS.get(s.nominal_mm)
    if nps:
        out.append(f"{mat_s} {ft_s} FLANGE {nps} INCH CLASS {s.pressure}{tail}")
    return out


def _bearing_styles(s: Spec) -> list[str]:
    return [
        f"{s.noun} BALL {s.part_number}",
        f"BALL {s.noun} {s.part_number}",
        f"{s.noun} DEEP GROOVE BALL {s.part_number}",
        f"{s.noun} BALL NO {s.part_number}",
    ]


def render(s: Spec) -> list[str]:
    if s.family == "fastener":
        return _fastener_styles(s)
    if s.family == "valve":
        return _valve_styles(s)
    if s.family == "pipe":
        return _pipe_styles(s)
    if s.family == "flange":
        return _flange_styles(s)
    if s.family == "bearing":
        return _bearing_styles(s)
    return [f"{s.material} {s.noun}"]


# --- canonical seed specs ------------------------------------------------------

_DIAS = [6, 8, 10, 12, 16, 20, 24]
_LENS = [20, 25, 30, 40, 50, 60, 75, 100]
_MATS = ["STAINLESS STEEL", "MILD STEEL", "CARBON STEEL", "GALVANISED IRON"]
_HEADS = ["HEXAGONAL", "SOCKET", "COUNTERSUNK"]
_NOUNS = ["BOLT", "SCREW", "NUT", "STUD"]


# The specs the demo narrative depends on. Random sampling of the spec space
# does not guarantee these are present: at limit=600 the stainless 10x50 bolt
# was absent, so the platform could not resolve the very material the landing
# page resolves. They are prepended, never sampled away.
#
# These are ordinary specs from the same generator, not special-cased records.
# Guaranteeing their presence makes the demo deterministic; it does not make
# the match any less computed.
DEMO_SPECS: list["Spec"] = [
    # the canonical material the whole story is about
    Spec(family='fastener', noun='BOLT', material='STAINLESS STEEL',
         dia_mm=10.0, length_mm=50.0, head='HEXAGONAL'),
    # the near miss: one critical attribute differs, text almost identical
    Spec(family='fastener', noun='BOLT', material='STAINLESS STEEL',
         dia_mm=10.0, length_mm=75.0, head='HEXAGONAL'),
    # wrong item type, same everything else
    Spec(family='fastener', noun='NUT', material='STAINLESS STEEL',
         dia_mm=10.0, length_mm=None, head='HEXAGONAL'),
    # wrong material, same dimensions
    Spec(family='fastener', noun='BOLT', material='MILD STEEL',
         dia_mm=10.0, length_mm=50.0, head='HEXAGONAL'),
    # a valve and a bearing so the other families are reachable in the demo
    Spec(family='valve', noun='VALVE', material='STAINLESS STEEL',
         nominal_mm=50.0, pressure='16', valve_type='GATE'),
    Spec(family='bearing', noun='BEARING', material='STEEL', part_number='6205-2RS'),

    # --- piping demo pairs ----------------------------------------------------
    # Each pair below is one attribute apart, and that attribute is CRITICAL. They
    # exist so the veto can be demonstrated on something other than a bolt: a
    # reviewer from a refinery recognises these immediately.
    #
    # schedule veto: same bore, same material, same construction, different wall
    Spec(family='pipe', noun='PIPE', material='CARBON STEEL',
         nominal_mm=100.0, schedule='40', construction='SEAMLESS'),
    Spec(family='pipe', noun='PIPE', material='CARBON STEEL',
         nominal_mm=100.0, schedule='80', construction='SEAMLESS'),
    # valve type veto: same bore, same class, same material, ball vs gate
    Spec(family='valve', noun='VALVE', material='STAINLESS STEEL',
         nominal_mm=50.0, pressure='150', valve_type='BALL'),
    Spec(family='valve', noun='VALVE', material='STAINLESS STEEL',
         nominal_mm=50.0, pressure='150', valve_type='GATE'),
    # flange, and its pressure-class near miss
    Spec(family='flange', noun='FLANGE', material='CARBON STEEL',
         nominal_mm=150.0, pressure='300', flange_type='WELD NECK', facing='RAISED FACE'),
    Spec(family='flange', noun='FLANGE', material='CARBON STEEL',
         nominal_mm=150.0, pressure='150', flange_type='WELD NECK', facing='RAISED FACE'),
]


def seed_specs(limit: int = 600, seed: int = 20260826) -> list[Spec]:
    """
    Enumerate canonical specs deterministically.

    Fixed seed so the demo is byte-identical every run — a demo that shuffles between
    rehearsal and performance is a demo that surprises you on stage.
    """
    rng = random.Random(seed)
    specs: list[Spec] = []

    for noun in _NOUNS:
        for mat in _MATS:
            for d in _DIAS:
                for L in _LENS:
                    if noun == "NUT" and L != _LENS[0]:
                        continue          # nuts have no length
                    specs.append(Spec(
                        family="fastener", noun=noun, material=mat,
                        dia_mm=float(d), length_mm=None if noun == "NUT" else float(L),
                        head="HEXAGONAL" if noun in ("BOLT", "NUT") else rng.choice(_HEADS),
                        grade=rng.choice(["", "", "8.8", "A2-70"]),
                        standard=rng.choice(["", "", "IS 1367", "DIN 933"]),
                    ))

    for mat in ["STAINLESS STEEL", "CARBON STEEL"]:
        for n in [25, 50, 80, 100, 150, 200]:
            for p in ["16", "40", "150", "300"]:
                for vt in ["GATE", "BALL", "GLOBE", "CHECK"]:
                    specs.append(Spec(family="valve", noun="VALVE", material=mat,
                                      nominal_mm=float(n), pressure=p, valve_type=vt))

    # Pipe. Schedule is the wall thickness, so bore alone does not identify a pipe —
    # which is exactly why SCHEDULE is a veto attribute.
    for mat in ["CARBON STEEL", "STAINLESS STEEL", "GALVANISED IRON"]:
        for n in [25, 50, 80, 100, 150, 200, 250, 300]:
            for sch in ["10", "40", "80", "160"]:
                for con in ["SEAMLESS", "WELDED"]:
                    specs.append(Spec(family="pipe", noun="PIPE", material=mat,
                                      nominal_mm=float(n), schedule=sch, construction=con))

    for mat in ["CARBON STEEL", "STAINLESS STEEL"]:
        for n in [25, 50, 80, 100, 150, 200]:
            for cls in ["150", "300", "600"]:
                for ft in ["WELD NECK", "SLIP ON", "BLIND"]:
                    for fc in ["RAISED FACE", "FLAT FACE"]:
                        specs.append(Spec(family="flange", noun="FLANGE", material=mat,
                                          nominal_mm=float(n), pressure=cls,
                                          flange_type=ft, facing=fc))

    for pn in ["6205-2RS", "6206-2RS", "6205ZZ", "6304", "6308-C3", "6202"]:
        specs.append(Spec(family="bearing", noun="BEARING", material="STEEL", part_number=pn))

    rng.shuffle(specs)
    # Drop any sampled spec that duplicates a demo spec, then prepend the demo
    # set so it survives the limit.
    demo_keys = {d.key() for d in DEMO_SPECS}
    sampled = [s for s in specs if s.key() not in demo_keys]
    return DEMO_SPECS + sampled[: max(limit - len(DEMO_SPECS), 0)]


def build_corpus(limit_specs: int = 600, variants_per_spec: int = 3,
                 seed: int = 20260826) -> tuple[list[MaterialRecord], dict[str, str]]:
    """
    Returns (records, truth) where truth maps record id -> canonical spec key.

    `truth` is the evaluation ground truth: two records match iff their spec keys are
    equal. It is correct by construction, which is the only honest way to claim a
    label on generated data.
    """
    rng = random.Random(seed)
    specs = seed_specs(limit_specs, seed)
    records: list[MaterialRecord] = []
    truth: dict[str, str] = {}
    counter = 1

    for s in specs:
        styles = render(s)
        rng.shuffle(styles)
        for text in styles[:variants_per_spec]:
            org, fmt = ORGS[counter % len(ORGS)]
            rid = f"R{counter:06d}"
            records.append(MaterialRecord(
                id=rid,
                raw_description=text,
                org=org,
                org_code=fmt.format(rng.randint(10000, 99999)),
                provenance="SYNTHETIC_VARIANT",
            ))
            truth[rid] = s.key()
            counter += 1

    return records, truth
