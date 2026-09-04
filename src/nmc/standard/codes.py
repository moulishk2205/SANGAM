"""
The Common National Material Code.

WHAT WAS WRONG WITH THE OLD ONE

`NMC-00022499` was a serial. It was unique and stable and told a procurement
officer nothing: two codes one apart could be a bolt and a pipe flange, and no
part of the string could be checked without a database round trip.

WHAT THIS IS

    NMC-5306-SS-0100-K7Q
        │    │  │    │
        │    │  │    └── discriminator (2) + check character (1)
        │    │  └─────── primary dimension, tenths of a millimetre
        │    └────────── material class
        └─────────────── Federal Supply Classification

The FSC values are REAL NATO Federal Supply Classification codes — 5306 Bolts,
4730 Pipe Fittings, 3110 Antifriction Bearings. They are not invented, and that
is deliberate: India's Directorate of Standardisation is the National
Codification Bureau (NCB code 72) and already codifies defence items under the
NATO Codification System. A civil national code that borrows the same class
spine is one a government reviewer already knows how to read, and it makes the
scheme extensible to the ~600 FSCs rather than to a taxonomy we made up.

PROPERTIES

  deterministic  the same canonical attributes always produce the same string
  meaningful     family, material and size are readable without a lookup
  validatable    the check character catches a single-character transcription
                 error offline, which matters when codes travel in spreadsheets
                 and on paper indents
  stable         it is derived from the identity-defining attributes only, so
                 correcting a MINOR attribute does not renumber the material
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

NMC_VERSION = "nmc-code-v2"

# Real NATO Federal Supply Classification codes. Anything unmapped falls to 9999
# ("unclassified"), which is honest: a made-up class is worse than an admitted
# gap, because it looks authoritative and is not.
FSC: dict[str, str] = {
    "BOLT, MACHINE":            "5306",   # Bolts
    "SCREW, CAP, HEXAGON HEAD": "5305",   # Screws
    "NUT, PLAIN, HEXAGON":      "5310",   # Nuts and Washers
    "WASHER, FLAT":             "5310",
    "STUD":                     "5307",   # Studs, Insert Screws
    "BEARING, BALL, ANNULAR":   "3110",   # Bearings, Antifriction
    "VALVE":                    "4820",   # Valves, Nonpowered
    "GASKET":                   "5330",   # Packing and Gasket Materials
    "FLANGE, PIPE":             "4730",   # Fittings, Hose/Pipe/Tube
    "PIPE":                     "4710",   # Pipe, Tube and Rigid Tubing
}
FSC_LABEL: dict[str, str] = {
    "5306": "Bolts", "5305": "Screws", "5310": "Nuts and washers",
    "5307": "Studs", "3110": "Bearings, antifriction",
    "4820": "Valves, nonpowered", "5330": "Packing and gasket materials",
    "4730": "Pipe fittings and specialties", "4710": "Pipe and rigid tubing",
    "9999": "Unclassified",
}

MATERIAL_CODE: dict[str, str] = {
    "STAINLESS_STEEL": "SS", "CARBON_STEEL": "CS", "MILD_STEEL": "MS",
    "GALVANISED_IRON": "GI", "ALLOY_STEEL": "AS", "BRASS": "BR",
    "CAST_IRON": "CI", "DUCTILE_IRON": "DI", "COPPER": "CU", "ALUMINIUM": "AL",
}
MATERIAL_LABEL = {v: k.replace("_", " ").title() for k, v in MATERIAL_CODE.items()}
MATERIAL_LABEL["XX"] = "Unspecified"

# Which attribute carries the size that identifies the item, per family. A bolt
# is identified by its thread; a flange by its bore. Using one attribute for all
# of them would put a meaningless number in the code for most families.
PRIMARY_DIM: dict[str, tuple[str, ...]] = {
    "fastener": ("THREAD_DIA", "NOMINAL_SIZE"),
    "bearing":  ("BORE",),
    "valve":    ("NOMINAL_SIZE",),
    "gasket":   ("NOMINAL_SIZE",),
    "flange":   ("NOMINAL_SIZE",),
    "pipe":     ("NOMINAL_SIZE",),
}

# Crockford-style: no I, L, O, U — the characters people misread on a printout.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

_PATTERN = re.compile(r"^NMC-(\d{4})-([A-Z]{2})-(\d{4})-([0-9A-Z]{2})([0-9A-Z])$")
_LEGACY = re.compile(r"^NMC-\d{8}$")


@dataclass(frozen=True)
class NmcParts:
    fsc: str
    fsc_label: str
    material: str
    material_label: str
    size_tenths_mm: int
    size_mm: float
    discriminator: str
    check: str
    legacy: bool = False

    @property
    def code(self) -> str:
        return (f"NMC-{self.fsc}-{self.material}-{self.size_tenths_mm:04d}"
                f"-{self.discriminator}{self.check}")


def _num(value: object) -> float | None:
    """Pull a millimetre magnitude out of whatever the extractor produced."""
    if value is None:
        return None
    s = str(value)
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def _check_char(body: str) -> str:
    """
    One character over the rest of the code.

    Position-weighted so a transposition (5306 typed as 5036) changes it, which
    a plain sum would not catch. Not cryptographic and not meant to be — it
    catches fingers, not adversaries.
    """
    total = sum((i + 1) * (ord(c) % 37) for i, c in enumerate(body))
    return _ALPHABET[total % len(_ALPHABET)]


def _discriminator(attributes: dict[str, str], item_name: str) -> str:
    """
    Two characters separating materials that share a class, material and size.

    Derived from the full identity-defining attribute set, so it is reproducible
    from the material rather than assigned by a counter. A bolt and a screw of
    the same size and steel differ here because their attribute sets differ.
    """
    payload = "|".join(
        f"{k}={attributes[k]}" for k in sorted(attributes) if attributes[k] not in ("", None)
    )
    h = hashlib.blake2s(f"{item_name}|{payload}".encode(), digest_size=8).digest()
    n = int.from_bytes(h, "big")
    return _ALPHABET[n % 32] + _ALPHABET[(n // 32) % 32]


def build_nmc(item_name: str, family: str, attributes: dict[str, str]) -> str:
    """
    Canonical attributes -> national code. Pure: no database, no counter.

    Collisions are possible in principle (two materials in the same class with
    the same size whose hashes agree in 10 bits). They are resolved by the
    caller against storage — see seed.py — because only storage knows what
    already exists. This function stays deterministic.
    """
    fsc = FSC.get(item_name, "9999")
    mat = MATERIAL_CODE.get(str(attributes.get("MATERIAL", "")).upper(), "XX")

    size_tenths = 0
    for code in PRIMARY_DIM.get(family, ("NOMINAL_SIZE",)):
        v = _num(attributes.get(code))
        if v is not None:
            size_tenths = max(0, min(9999, int(round(v * 10))))
            break

    body = f"{fsc}{mat}{size_tenths:04d}"
    disc = _discriminator(attributes, item_name)
    return f"NMC-{fsc}-{mat}-{size_tenths:04d}-{disc}{_check_char(body + disc)}"


def parse_nmc(code: str) -> NmcParts | None:
    """Structure of a code, without touching the database. None if malformed."""
    code = (code or "").strip().upper()
    if _LEGACY.match(code):
        return NmcParts(fsc="9999", fsc_label="Legacy serial code", material="XX",
                        material_label="Unspecified", size_tenths_mm=0, size_mm=0.0,
                        discriminator="--", check="-", legacy=True)
    m = _PATTERN.match(code)
    if not m:
        return None
    fsc, mat, size, disc, chk = m.groups()
    return NmcParts(
        fsc=fsc, fsc_label=FSC_LABEL.get(fsc, "Unclassified"),
        material=mat, material_label=MATERIAL_LABEL.get(mat, "Unspecified"),
        size_tenths_mm=int(size), size_mm=int(size) / 10.0,
        discriminator=disc, check=chk,
    )


def validate_nmc(code: str) -> tuple[bool, str]:
    """(ok, reason). Structure AND check character, so a typo is caught offline."""
    parts = parse_nmc(code)
    if parts is None:
        return False, "Malformed. Expected NMC-<FSC:4>-<MAT:2>-<SIZE:4>-<XX><C>."
    if parts.legacy:
        return True, "Legacy serial code — valid but carries no classification."
    body = f"{parts.fsc}{parts.material}{parts.size_tenths_mm:04d}{parts.discriminator}"
    if _check_char(body) != parts.check:
        return False, f"Check character failed — expected {_check_char(body)}, got {parts.check}."
    return True, "Valid."


def describe_nmc(code: str) -> dict:
    """What the code says about the material, for the UI. No lookup required."""
    parts = parse_nmc(code)
    ok, reason = validate_nmc(code)
    if parts is None:
        return {"code": code, "valid": False, "reason": reason, "segments": []}
    if parts.legacy:
        return {"code": code, "valid": ok, "reason": reason, "legacy": True,
                "segments": [{"label": "Serial", "value": code.split("-")[-1],
                              "meaning": "Legacy identifier, no classification"}]}
    return {
        "code": code, "valid": ok, "reason": reason, "legacy": False,
        "segments": [
            {"label": "FSC", "value": parts.fsc, "meaning": parts.fsc_label,
             "note": "NATO Federal Supply Classification"},
            {"label": "Material", "value": parts.material, "meaning": parts.material_label},
            {"label": "Size", "value": f"{parts.size_tenths_mm:04d}",
             "meaning": (f"{parts.size_mm:g} mm nominal" if parts.size_tenths_mm
                         else "not dimensioned")},
            {"label": "Discriminator", "value": parts.discriminator,
             "meaning": "separates materials sharing class, material and size"},
            {"label": "Check", "value": parts.check,
             "meaning": "detects a single-character transcription error"},
        ],
    }
