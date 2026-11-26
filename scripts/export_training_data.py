#!/usr/bin/env python3
"""
Export the exact dataset the learned scorer is trained on, as plain CSV.

    python scripts/export_training_data.py              # writes datasets/training/
    python scripts/export_training_data.py --no-embeddings

The corpus is generated, not collected, so in principle it never needs to be
shipped: `scripts/train_scorer.py` rebuilds it bit-for-bit from a seed. It is
exported anyway because a dataset you can open in a spreadsheet is auditable
in a way a generator is not. The arguments and seeds below are the ones
`train_scorer.py` uses by default, so these files are the train / validation /
test split behind `models/scorer/scorer-v1.json`.

Files
-----
corpus.csv          every synthetic material record, its identity and its split
pairs_train.csv     labelled (probe, candidate) pairs mined from the retriever
pairs_val.csv       ... used for calibration and threshold setting
pairs_test.csv      ... read exactly once, at the end of training
manifest.json       row counts, versions, seeds and SHA-256 of every file
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nmc.demo.corpus import build_corpus
from nmc.extract.templates import CONFIG_VERSION
from nmc.match.engine import MODEL_VERSION, MatchingEngine
from nmc.ml.dataset import SPLIT_SEED, assert_no_leakage, build_pairs, split_identities
from nmc.ml.features import FEATURE_NAMES
from nmc.normalise.text import GAZETTEER_VERSION

OUT = ROOT / "datasets" / "training"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_pairs(path: Path, P) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "candidate_id", "spec_key", "label", "vetoed", *FEATURE_NAMES])
        for i in range(len(P)):
            w.writerow([
                P.source_ids[i], P.candidate_ids[i], P.spec_keys[i],
                int(P.y[i]), int(P.vetoed[i]),
                *(f"{v:.6g}" for v in P.X[i]),
            ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", type=int, default=600)
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--no-embeddings", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    records, truth = build_corpus(limit_specs=args.specs, variants_per_spec=args.variants)
    engine = MatchingEngine(use_embeddings=not args.no_embeddings)
    engine.index(records)
    dense = engine.retriever.embeddings_enabled

    tr_k, va_k, te_k = split_identities(truth)
    split_of = {k: "train" for k in tr_k} | {k: "val" for k in va_k} | {k: "test" for k in te_k}

    with (OUT / "corpus.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record_id", "org", "org_code", "raw_description",
                    "item_name", "spec_key", "split", "provenance"])
        for r in records:
            k = truth[r.id]
            w.writerow([r.id, r.org, r.org_code, r.raw_description,
                        r.item_name, k, split_of[k], r.provenance])

    splits = {}
    for name, keys in (("train", tr_k), ("val", va_k), ("test", te_k)):
        P = build_pairs(engine, records, truth, keys, top_k=args.top_k)
        splits[name] = P
        write_pairs(OUT / f"pairs_{name}.csv", P)
        print(f"  pairs_{name}.csv  {len(P):6,d} pairs  ({P.positives:,} positive)")
    assert_no_leakage(*splits.values())

    files = ["corpus.csv", "pairs_train.csv", "pairs_val.csv", "pairs_test.csv"]
    manifest = {
        "description": "Training data for the SANGAM learned match scorer. "
                       "Synthetic; labels correct by construction.",
        "generator": "scripts/export_training_data.py",
        "args": vars(args),
        "split_seed": SPLIT_SEED,
        "split_ratios": [0.6, 0.2, 0.2],
        "split_unit": "identity (spec_key), never record",
        "dense_channel": bool(dense),
        "engine_version": MODEL_VERSION,
        "gazetteer_version": GAZETTEER_VERSION,
        "template_version": CONFIG_VERSION,
        "records": len(records),
        "identities": len(set(truth.values())),
        "features": FEATURE_NAMES,
        "pairs": {k: {"rows": len(P), "positives": P.positives,
                      "vetoed": int(P.vetoed.sum())} for k, P in splits.items()},
        "sha256": {f: sha256(OUT / f) for f in files},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  corpus.csv       {len(records):6,d} records over {manifest['identities']:,} identities")
    print(f"  leakage check PASSED · dense channel {'on' if dense else 'off'} · wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
