#!/usr/bin/env python3
"""
Print the attribute template for an item type, derived entirely from real FLIS data.

This is the artefact the whole matching design hangs on. For a given approved item
name (INC), it answers: *which attributes does a national codification authority say
are decisive for this kind of item?* That is what makes `M10x50` vs `M10x75` a
deterministic, explainable rejection rather than a similarity judgement.

    python scripts/show_template.py --fsc 5306
    python scripts/show_template.py --search "BOLT, MACHINE"
    python scripts/show_template.py --inc 00815 --values

Joins:
    P_H6_PICK    INC -> item name, FSC
    V_H6_NAME_INC INC -> English definition
    MRD06P1      INC -> the MRCs (attributes) that apply
    MRD0107      MRC -> requirement statement + definition + reply-table refs
    MRD0300      reply table -> controlled vocabulary of legal values
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "interim" / "flis"


def load(name: str) -> list[dict]:
    p = DATA / name
    if not p.exists():
        sys.exit(f"missing {p}\nRun: python scripts/fetch_flis.py --small  (then unzip into data/interim/flis)")
    with open(p, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fsc", help="list item names in a supply class, e.g. 5306 (bolts)")
    ap.add_argument("--search", help="substring search over approved item names")
    ap.add_argument("--inc", help="show the full attribute template for one INC")
    ap.add_argument("--values", action="store_true", help="also print controlled vocabularies")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    pick = load("P_H6_PICK.CSV")

    if args.search:
        q = args.search.upper()
        hits = [r for r in pick if q in r["ITEM_NAME"].upper()]
        print(f"{len(hits)} item names matching {args.search!r}\n")
        for r in hits[: args.limit]:
            print(f"  INC {r['INC']}  FSC {r['FSC']}  {r['ITEM_NAME']}")
        return

    if args.fsc:
        hits = [r for r in pick if r["FSC"] == args.fsc]
        fscs = {r["FSC"]: r for r in load("V_H2_FSC.CSV")}
        meta = fscs.get(args.fsc)
        if meta:
            print(f"FSC {args.fsc} — {meta['FSC_TITLE']}")
            if meta["FSC_INCLUSIONS"]:
                print(f"  includes: {meta['FSC_INCLUSIONS'][:200]}")
            if meta["FSC_EXCLUSIONS"]:
                print(f"  excludes: {meta['FSC_EXCLUSIONS'][:200]}")
        print(f"\n{len(hits)} approved item names in this class\n")
        for r in hits[: args.limit]:
            print(f"  INC {r['INC']}  {r['ITEM_NAME']}")
        if len(hits) > args.limit:
            print(f"  ... and {len(hits)-args.limit} more")
        return

    if not args.inc:
        ap.error("give --fsc, --search or --inc")

    inc = args.inc.zfill(5)
    row = next((r for r in pick if r["INC"] == inc), None)
    if not row:
        sys.exit(f"INC {inc} not found")

    defs = {r["INC"]: r["DEFINITION"] for r in load("V_H6_NAME_INC.CSV")}
    mrcs = {r["MRC_3445"]: r for r in load("MRD0107.CSV")}

    schema = [r for r in load("MRD06P1.CSV") if r["INC_4080"] == inc]
    # one INC can appear under several FIIGs; dedupe on MRC, keep first reply table
    seen: dict[str, str] = {}
    for r in schema:
        seen.setdefault(r["MRC_3445"], r["RPLY_TBL_DCOD_3845"])

    print("=" * 78)
    print(f"INC {inc}   {row['ITEM_NAME']}   (FSC {row['FSC']})")
    print("=" * 78)
    d = defs.get(inc, "")
    if d:
        print("\nDEFINITION")
        for i in range(0, min(len(d), 600), 76):
            print("  " + d[i : i + 76])

    print(f"\nATTRIBUTE TEMPLATE — {len(seen)} attributes the codification standard records\n")
    print(f"  {'MRC':<6} {'REQUIREMENT':<34} {'REPLY TBL':<10} MODE")
    print(f"  {'-'*6} {'-'*34} {'-'*10} ----")
    vocab_needed: dict[str, str] = {}
    for mrc, tbl in sorted(seen.items()):
        m = mrcs.get(mrc, {})
        stmt = (m.get("RQMT_STMT_3614") or "?")[:34]
        mode = m.get("MODE_CD_4735", "")
        print(f"  {mrc:<6} {stmt:<34} {tbl or '-':<10} {mode}")
        for i in range(1, 9):
            t = m.get(f"RPLY_TBL_MRD_8254_{i}")
            if t:
                vocab_needed[t] = mrc

    if args.values and vocab_needed:
        by_tbl = defaultdict(list)
        for r in load("MRD0300.CSV"):
            if r["RPLY_TBL_MRD_8254"] in vocab_needed:
                by_tbl[r["RPLY_TBL_MRD_8254"]].append(r["DCOD_RPLY_ST_3864"])
        print("\nCONTROLLED VOCABULARIES")
        for tbl, vals in sorted(by_tbl.items()):
            print(f"\n  table {tbl}  (attribute {vocab_needed[tbl]})  — {len(vals)} legal values")
            print("    " + ", ".join(v for v in vals[:22] if v))
            if len(vals) > 22:
                print(f"    ... and {len(vals)-22} more")

    print("\n" + "-" * 78)
    print("This template is REAL DATA, not our invention. It is what makes the veto")
    print("defensible: we compare on the attributes the standard says matter for this")
    print("item type, not on cosine similarity.")


if __name__ == "__main__":
    main()
