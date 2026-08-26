#!/usr/bin/env python3
"""
Slice the multi-GB FLIS archives down to the commodity families we actually demo.

The archives decompress to ~11 GB. Nothing here is ever loaded whole: every file is
streamed straight out of its zip, filtered against a NIIN set, and written to
data/interim/slice/. Peak memory is the NIIN set plus one line.

Produces, for the chosen Federal Supply Classes:
  nsn_item.csv          NIIN -> FSC, INC, item name
  nsn_attribute.csv     NIIN -> MRC, coded reply          (from FLISV)
  nsn_part.csv          NIIN -> manufacturer part number   GROUND TRUTH for duplicates
  nsn_standardization.csv NIIN -> related NSN + ISC        GROUND TRUTH for equivalence
  attribute_frequency.csv  INC x MRC x count               THE EMPIRICAL TEMPLATE

The last one matters most. The MRD dictionary only describes attributes with *coded*
reply tables, so dimensional attributes (thread size, length) are absent from it.
The attributes that are actually recorded against real items are the honest schema,
and they come from the item data, not the dictionary.

    python scripts/slice_flis.py                 # default demo families
    python scripts/slice_flis.py --fsc 5306 4820
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "flis"
OUT = ROOT / "data" / "interim" / "slice"

# The six demo families from the Phase 0 plan, as Federal Supply Classes.
DEFAULT_FSC = [
    "5305",  # screws
    "5306",  # bolts
    "5310",  # nuts and washers
    "4730",  # pipe fittings
    "3110",  # antifriction bearings
    "4820",  # valves, non-powered
    "6145",  # wire and cable
]


def stream_csv(zip_path: Path, member: str):
    """Yield dict rows from a CSV inside a zip without materialising it."""
    if not zip_path.exists():
        sys.exit(f"missing {zip_path} — run: python scripts/fetch_flis.py --core")
    with zipfile.ZipFile(zip_path) as z:
        names = {n.upper(): n for n in z.namelist()}
        real = names.get(member.upper())
        if real is None:
            sys.exit(f"{member} not in {zip_path.name}: {sorted(names.values())}")
        with z.open(real) as fh:
            yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace", newline=""))


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path.name:<28} {len(rows):>10,} rows")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fsc", nargs="+", default=DEFAULT_FSC)
    ap.add_argument("--skip-attrs", action="store_true", help="skip the 2.4 GB FLISV pass")
    args = ap.parse_args()

    fsc = set(args.fsc)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"slicing FSC {' '.join(sorted(fsc))}\n")

    # ---- pass 1: NIIN backbone -------------------------------------------------
    print("pass 1  P_FLIS_NSN.CSV  (986 MB)")
    items, niin_inc = [], {}
    seen = 0
    for r in stream_csv(RAW / "IDENTIFICATION.zip", "P_FLIS_NSN.CSV"):
        seen += 1
        if r.get("FSC") in fsc:
            n = r["NIIN"]
            niin_inc[n] = r.get("INC", "")
            items.append(r)
    print(f"        scanned {seen:,} NIINs -> kept {len(items):,}")
    write(OUT / "nsn_item.csv", items, ["FSC", "NIIN", "INC", "ITEM_NAME", "SOS", "END_ITEM_NAME"])
    del items
    keep = set(niin_inc)

    # ---- pass 2: manufacturer part numbers = duplicate ground truth -------------
    print("\npass 2  V_FLIS_PART.CSV  (1.3 GB)   <- duplicate ground truth")
    parts, seen = [], 0
    for r in stream_csv(RAW / "REFERENCE.zip", "V_FLIS_PART.CSV"):
        seen += 1
        if r.get("NIIN") in keep:
            parts.append(r)
    print(f"        scanned {seen:,} rows -> kept {len(parts):,}")
    write(OUT / "nsn_part.csv", parts, ["NIIN", "PART_NUMBER", "CAGE_CODE", "RNCC", "RNVC"])

    per_niin = Counter(r["NIIN"] for r in parts)
    multi = {n: c for n, c in per_niin.items() if c > 1}
    pairs = sum(c * (c - 1) // 2 for c in multi.values())
    print(f"        NIINs with >1 part number : {len(multi):,}")
    print(f"        implied REAL positive pairs: {pairs:,}")
    del parts

    # ---- pass 3: standardization decisions = equivalence ground truth -----------
    print("\npass 3  V_FLIS_STANDARDIZATION.CSV  (614 MB)   <- equivalence ground truth")
    std, seen, with_rel = [], 0, 0
    for r in stream_csv(RAW / "IDENTIFICATION.zip", "V_FLIS_STANDARDIZATION.CSV"):
        seen += 1
        if r.get("NIIN") in keep:
            std.append(r)
            if (r.get("RELATED_NSN") or "").strip():
                with_rel += 1
    print(f"        scanned {seen:,} rows -> kept {len(std):,}")
    print(f"        with a non-empty RELATED_NSN: {with_rel:,}   <-- decides whether")
    print(f"        'equivalence' is a real observed class or a derived rule")
    write(OUT / "nsn_standardization.csv", std, ["NIIN", "RELATED_NSN", "ISC", "ORIG_STDZN_DEC", "DT_STDZN_DEC"])
    isc = Counter(r.get("ISC", "") for r in std if (r.get("RELATED_NSN") or "").strip())
    if isc:
        print("        ISC distribution among related pairs: " +
              ", ".join(f"{k or '-'}={v:,}" for k, v in isc.most_common(8)))
    del std

    # ---- pass 4: the empirical attribute template -------------------------------
    if args.skip_attrs:
        print("\npass 4  skipped")
    else:
        print("\npass 5  FLISV.CSV  (2.4 GB)   <- empirical attribute template")
        attrs, seen = [], 0
        inc_mrc: dict[str, Counter] = defaultdict(Counter)
        inc_items: Counter = Counter()
        for r in stream_csv(RAW / "FLISV.zip", "FLISV.CSV"):
            seen += 1
            n = r.get("NIIN")
            if n in keep:
                attrs.append(r)
                inc_mrc[niin_inc[n]][r.get("MRC", "")] += 1
        print(f"        scanned {seen:,} rows -> kept {len(attrs):,}")
        write(OUT / "nsn_attribute.csv", attrs, ["NIIN", "MRC", "MODE_CODE", "CODED_CLEAR_REPLY"])
        for n in {r["NIIN"] for r in attrs}:
            inc_items[niin_inc[n]] += 1
        del attrs

        freq = []
        for inc, c in inc_mrc.items():
            n_items = max(inc_items[inc], 1)
            for mrc, cnt in c.most_common():
                freq.append({"INC": inc, "MRC": mrc, "ITEMS_WITH_ATTR": cnt,
                             "ITEMS_IN_INC": n_items,
                             "COVERAGE": f"{cnt / n_items:.4f}"})
        freq.sort(key=lambda r: (r["INC"], -int(r["ITEMS_WITH_ATTR"])))
        write(OUT / "attribute_frequency.csv", freq,
              ["INC", "MRC", "ITEMS_WITH_ATTR", "ITEMS_IN_INC", "COVERAGE"])

    print(f"\ndone in {time.time()-t0:,.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
