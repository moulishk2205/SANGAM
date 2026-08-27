"""
Text normalisation: the stage that does most of the real work.

The insight from Sprint 0 research is that this is not a matching problem wearing a
normalisation costume — it is a normalisation problem wearing a matching costume.
`SS HEX BOLT M10 X 50` and `STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM` share almost
no tokens as written. After normalisation they share nearly all of them. Every
downstream stage gets easier in proportion to how well this stage works.

The abbreviation gazetteer is a versioned, reviewable artefact rather than knowledge
baked into a model. A materials engineer can read it, correct it, and sign it off —
which is a real human-in-the-loop story, and it is auditable in a way that
"the model learned it" is not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

GAZETTEER_VERSION = "gaz-v2"

# Expansion is applied on whole tokens only, longest-first, so SS -> STAINLESS STEEL
# never fires inside a word. Sourced from common Indian CPSE / MRO storekeeper usage
# and cross-checked against FLIS colloquial names.
ABBREVIATIONS: dict[str, str] = {
    # materials
    "SS": "STAINLESS STEEL",
    "S/S": "STAINLESS STEEL",
    "STLS": "STAINLESS STEEL",
    "MS": "MILD STEEL",
    "CS": "CARBON STEEL",
    "GI": "GALVANISED IRON",
    "CI": "CAST IRON",
    "AL": "ALUMINIUM",
    "ALU": "ALUMINIUM",
    "CU": "COPPER",
    "BR": "BRASS",
    "PVC": "POLYVINYL CHLORIDE",
    "EN8": "EN8 STEEL",
    # forms / heads
    "HEX": "HEXAGONAL",
    "HEXA": "HEXAGONAL",
    "HEXAGON": "HEXAGONAL",
    "HH": "HEXAGONAL HEAD",
    "HHB": "HEXAGONAL HEAD BOLT",
    "CSK": "COUNTERSUNK",
    "SKT": "SOCKET",
    "SOC": "SOCKET",
    "RND": "ROUND",
    "SQ": "SQUARE",
    "CYL": "CYLINDRICAL",
    # items
    "BLT": "BOLT",
    "SCR": "SCREW",
    "SCRW": "SCREW",
    "WSHR": "WASHER",
    "WASH": "WASHER",
    "BRG": "BEARING",
    "BRNG": "BEARING",
    "VLV": "VALVE",
    "GSKT": "GASKET",
    "GKT": "GASKET",
    "FLG": "FLANGE",
    "FLNG": "FLANGE",
    "NPL": "NIPPLE",
    "CPLG": "COUPLING",
    "ELB": "ELBOW",
    "MTR": "MOTOR",
    "CBL": "CABLE",
    # dimensions / qualifiers
    "DIA": "DIAMETER",
    "DIAM": "DIAMETER",
    "LG": "LENGTH",
    "LGTH": "LENGTH",
    "LNG": "LENGTH",
    "LONG": "LENGTH",
    "THK": "THICKNESS",
    "THD": "THREAD",
    "THRD": "THREAD",
    "PTCH": "PITCH",
    "OD": "OUTSIDE DIAMETER",
    "ID": "INSIDE DIAMETER",
    "NB": "NOMINAL BORE",
    "NPS": "NOMINAL PIPE SIZE",
    # ratings
    "PN": "PRESSURE NOMINAL",
    "SCH": "SCHEDULE",
    "SCHD": "SCHEDULE",
    "CL": "CLASS",
    "GR": "GRADE",
    "GRD": "GRADE",
    # pipe / flange / valve trade shorthand. Added in gaz-v2 alongside the pipe,
    # flange and ball-valve item families; these are the forms a refinery
    # storekeeper actually types.
    "SMLS": "SEAMLESS",
    "SEEMLESS": "SEAMLESS",          # a real and very common misspelling
    "ERW": "ELECTRIC RESISTANCE WELDED",
    "WN": "WELD NECK",
    "SO": "SLIP ON",
    "WNRF": "WELD NECK RAISED FACE",
    "SORF": "SLIP ON RAISED FACE",
    "SW": "SOCKET WELD",
    "BLRF": "BLIND RAISED FACE",
    "RF": "RAISED FACE",
    "FF": "FLAT FACE",
    "RTJ": "RING TYPE JOINT",
    "BV": "BALL VALVE",
    "GV": "GATE VALVE",
    "NRV": "CHECK VALVE",
    # noise words that carry no identity
    "NOS": "",
    "NO.": "",
    "QTY": "",
    "MAKE": "",
}

# Unit spellings seen in real Indian material masters, mapped to a canonical token.
UNIT_SYNONYMS: dict[str, str] = {
    "MM": "MM", "M.M": "MM", "M.M.": "MM", "MILLIMETER": "MM", "MILLIMETRE": "MM", "MMS": "MM",
    "CM": "CM", "C.M": "CM", "CENTIMETER": "CM", "CENTIMETRE": "CM",
    "M": "M", "MTR": "M", "MTRS": "M", "METER": "M", "METRE": "M",
    "IN": "IN", "INCH": "IN", "INCHES": "IN", '"': "IN",
    "KG": "KG", "KGS": "KG", "GM": "G", "GMS": "G", "G": "G",
    "BAR": "BAR", "PSI": "PSI", "KW": "KW", "HP": "HP", "V": "V", "A": "A",
}

# Separators that mean "by" between two dimensions.
#
# CAREFUL: 'x' and 'X' are letters. A naive [xX] substitution turns HEX into "HE X",
# which silently destroys the single most common token in the fastener domain. So the
# ASCII forms only count as separators when they sit between digits, or stand alone
# as their own token. The typographic forms are never letters, so they always count.
_SEP_SYMBOL = re.compile(r"[×✕✖*]")
_SEP_BETWEEN_DIGITS = re.compile(r"(?<=\d)\s*[xX]\s*(?=\d)")
_SEP_STANDALONE = re.compile(r"(?<![A-Z0-9])[xX](?![A-Z0-9])")
_PUNCT = re.compile(r"[,;:/\\()\[\]{}]+")
_LONE_DASH = re.compile(r"(?<!\S)-+(?!\S)")     # ' - ' separator, but keeps A2-70 and 6205-2RS
_WS = re.compile(r"\s+")
_DOTTED_UNIT = re.compile(r"\b([A-Z])\.([A-Z])\.?(?![A-Z])")   # M.M. -> MM

# Split a number glued to a unit: 50MM -> 50 MM. Built from the known unit vocabulary
# so it never fires on a part number like 6205-2RS or a grade like A2-70.
_UNIT_ALTS = "|".join(sorted((re.escape(u) for u in UNIT_SYNONYMS if u.isalpha()),
                             key=len, reverse=True))
_NUM_UNIT = re.compile(rf"(?<=\d)({_UNIT_ALTS})\b")

# Size codes written glued to the number: 150NB, 4NPS. Kept separate from the unit
# splitter above because these are not units — they are size-system markers, and
# adding them to UNIT_SYNONYMS would let them be read as dimensions.
_NUM_SIZECODE = re.compile(r"(?<=\d)(NB|NPS|ND)\b")

# The inch mark written against a number: 4" -> 4 IN. It is the single most common
# way a size is written on a pipe requisition and it is not a letter, so the unit
# splitter above cannot reach it.
_NUM_QUOTE = re.compile(r'(?<=\d)\s*["\u2033\u201d]')

# Rating codes written glued to the number, the other way round: SCH40, PN16,
# CLASS150, CL300. Without this, `PN16` survives as a single unknown token and the
# pressure class of every valve written that way is silently never extracted.
_CODE_NUM = re.compile(r"\b(SCHEDULE|SCHD|SCH|PN|CLASS|CL)(\d{1,4}S?)\b")


@dataclass(frozen=True, slots=True)
class Normalised:
    text: str
    tokens: tuple[str, ...]
    applied: tuple[str, ...]        # which expansions fired — shown in the evidence panel
    version: str = GAZETTEER_VERSION


def _expand_token(tok: str) -> tuple[str, str | None]:
    up = tok.upper()
    if up in ABBREVIATIONS:
        exp = ABBREVIATIONS[up]
        return exp, f"{up}->{exp or '(dropped)'}"
    if up in UNIT_SYNONYMS:
        canon = UNIT_SYNONYMS[up]
        return canon, (f"{up}->{canon}" if canon != up else None)
    return up, None


def normalise(text: str) -> Normalised:
    """
    Deterministic, order-preserving normalisation.

    Deliberately NOT doing: stemming, stopword removal, or token sorting. Token order
    carries engineering meaning here (`M10 X 50` is not `M50 X 10`), and the
    extraction stage that follows depends on the original ordering.
    """
    s = text.upper()

    # M.M. -> MM before punctuation stripping, or the dots destroy the unit
    s = _DOTTED_UNIT.sub(r"\1\2", s)

    # Unify dimension separators to a single ' X '. Order matters: symbols first,
    # then digit-flanked ASCII x, then standalone x. Never a bare [xX] substitution.
    s = _SEP_SYMBOL.sub(" X ", s)
    s = _SEP_BETWEEN_DIGITS.sub(" X ", s)
    s = _SEP_STANDALONE.sub(" X ", s)

    s = _PUNCT.sub(" ", s)
    s = _LONE_DASH.sub(" ", s)

    # 50MM -> 50 MM, using the known unit vocabulary only
    s = _NUM_UNIT.sub(r" \1", s)
    # 150NB -> 150 NB, SCH40 -> SCH 40, PN16 -> PN 16
    s = _NUM_SIZECODE.sub(r" \1", s)
    s = _NUM_QUOTE.sub(" IN", s)
    s = _CODE_NUM.sub(r"\1 \2", s)

    # Metric thread designators are one symbol: M 10 -> M10
    s = re.sub(r"\bM\s+(\d+(?:\.\d+)?)\b", r"M\1", s)

    out, applied = [], []
    for tok in _WS.split(s.strip()):
        if not tok:
            continue
        exp, note = _expand_token(tok)
        if note:
            applied.append(note)
        if exp:
            out.extend(exp.split())

    tokens = tuple(out)
    return Normalised(" ".join(tokens), tokens, tuple(applied))


def spec_tokens(n: Normalised) -> list[str]:
    """
    Atomic tokens for the lexical channel.

    A dense embedding shatters `M10X50` into subwords it shares with `M10X75`, so the
    lexical channel has to treat engineering symbols as indivisible. This is the cheap
    fix that does more for retrieval quality than any amount of embedding fine-tuning.
    """
    toks = list(n.tokens)
    text = n.text
    # metric thread designators as single symbols
    toks += re.findall(r"\bM\d+(?:\.\d+)?\b", text)
    # dimension pairs, e.g. '10 X 50' -> '10X50'
    for a, b in re.findall(r"\b(\d+(?:\.\d+)?)\s+X\s+(\d+(?:\.\d+)?)\b", text):
        toks.append(f"{a}X{b}")
    # standards references
    toks += re.findall(r"\b(?:IS|DIN|ISO|ASTM|ANSI|BS|EN)\s*\d+[A-Z0-9\-]*\b", text)
    return toks
