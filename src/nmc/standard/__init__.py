"""
Standardisation: the national code, and the standard description.

Both are *derived* from the canonical attribute set rather than stored
independently, so neither can drift from the material it describes. Regenerate
either one from a canonical record and you must get the same string back — that
property is what makes the code checkable and the description trustworthy.
"""
from .codes import (                                              # noqa: F401
    NMC_VERSION, FSC, MATERIAL_CODE, build_nmc, parse_nmc, validate_nmc,
    describe_nmc, NmcParts,
)
from .describe import standard_description, description_parts     # noqa: F401
