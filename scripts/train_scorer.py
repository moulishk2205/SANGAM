#!/usr/bin/env python3
"""
Train the learned scorer, calibrate it, and report honestly.

    python scripts/train_scorer.py                # train, evaluate, save
    python scripts/train_scorer.py --no-save      # evaluate without writing
    python scripts/train_scorer.py --specs 300    # smaller/faster run

WHAT THIS DOES AND DOES NOT CLAIM

It fits a model on labelled pairs drawn from a SYNTHETIC corpus whose labels are
correct by construction. That makes every number below a statement about this
engine on this corpus. It is not a claim about performance on a real CPSE
material master, because no real CPSE material master is public and none was
used. The pipeline is what would be pointed at real data on the day there is
any; the numbers would then have to be re-earned.

The test split is read exactly once, at the end. Nothing selects against it.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from nmc.demo.corpus import build_corpus
from nmc.extract.templates import CONFIG_VERSION
from nmc.match.engine import MODEL_VERSION, T_MATCH, W_ATTR, W_TEXT, MatchingEngine
from nmc.ml.dataset import assert_no_leakage, build_pairs, split_identities
from nmc.ml.features import FEATURE_NAMES
from nmc.ml.metrics import brier, prf, reliability, roc_auc
from nmc.ml.model import DEFAULT_PATH
from nmc.ml.robustness import stress
from nmc.ml.train import train
from nmc.normalise.text import GAZETTEER_VERSION


def baseline_scores(P) -> np.ndarray:
    """
    The current shipped formula, recomputed from the same features.

    attribute_agreement is column 0 and text_max is column 1, so the hand-tuned
    score is reproducible exactly — which is what makes the comparison fair
    rather than a comparison against a straw man.
    """
    i_attr = FEATURE_NAMES.index("attribute_agreement")
    i_text = FEATURE_NAMES.index("text_max")
    raw = W_ATTR * P.X[:, i_attr] + W_TEXT * P.X[:, i_text]
    return np.where(P.vetoed, 0.0, raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", type=int, default=600)
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--no-embeddings", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    print("Building corpus and index…")
    records, truth = build_corpus(limit_specs=args.specs, variants_per_spec=args.variants)
    engine = MatchingEngine(use_embeddings=not args.no_embeddings)
    engine.index(records)
    dense = engine.retriever.embeddings_enabled
    print(f"  {len(records):,} records over {len(set(truth.values())):,} identities "
          f"(dense channel: {'on' if dense else 'off'})")

    tr_k, va_k, te_k = split_identities(truth)
    print(f"  identities  train {len(tr_k)}  val {len(va_k)}  test {len(te_k)}")

    print("Mining pairs from the retriever's own top-k…")
    tr = build_pairs(engine, records, truth, tr_k, top_k=args.top_k)
    va = build_pairs(engine, records, truth, va_k, top_k=args.top_k)
    te = build_pairs(engine, records, truth, te_k, top_k=args.top_k)
    assert_no_leakage(tr, va, te)
    print(f"  pairs  train {len(tr):,} ({tr.positives:,}+)  "
          f"val {len(va):,} ({va.positives:,}+)  test {len(te):,} ({te.positives:,}+)")
    print("  leakage check: PASSED (no shared identity between splits)")

    meta = {
        "trained_at_specs": args.specs,
        "n_train_pairs": len(tr), "n_val_pairs": len(va), "n_test_pairs": len(te),
        "dense_channel": bool(dense),
        "gazetteer_version": GAZETTEER_VERSION,
        "template_version": CONFIG_VERSION,
        "engine_version": MODEL_VERSION,
        "corpus": "synthetic; labels correct by construction",
    }
    scorer = train(tr, va, metadata=meta)

    # ── the single read of test ───────────────────────────────────────────
    keep = ~te.vetoed
    Xte, yte = te.X[keep], te.y[keep]
    p_learned = scorer.probability(te.X, te.vetoed)
    p_base = baseline_scores(te)

    lr = prf(p_learned, te.y, scorer.thresholds["match"])
    bl = prf(p_base, te.y, T_MATCH)

    auc_l = roc_auc(scorer.calibrate(scorer.raw(Xte)), yte)
    auc_b = roc_auc(p_base[keep], yte)

    rows_raw, ece_raw = reliability(scorer.raw(Xte), yte)
    rows_cal, ece_cal = reliability(scorer.calibrate(scorer.raw(Xte)), yte)
    ece_base = reliability(p_base[keep], yte)[1]

    W = 74
    print("\n" + "=" * W)
    print("LEARNED SCORER — TEST SET".center(W))
    print("=" * W)

    print("\nLEARNED COEFFICIENTS  (positive = evidence for a match)")
    for n, c in sorted(zip(scorer.feature_names, scorer.coef),
                       key=lambda kv: -abs(kv[1])):
        bar = "#" * min(int(abs(c) * 3), 34)
        print(f"  {n:22s} {c:+8.3f}  {bar}")
    print(f"  {'(intercept)':22s} {scorer.intercept:+8.3f}")

    print("\nBANDS                 risk policy on a calibrated probability,")
    print("                        with the realised precision measured on validation")
    print(f"  {'band':18s} {'threshold':>10s} {'realised prec':>14s} {'pairs':>8s}")
    for b, label in (("match", "MATCH"), ("near", "NEAR_MATCH"), ("review", "REVIEW_REQUIRED")):
        t = scorer.thresholds[b]
        rp = scorer.thresholds.get(f"{b}_realised_precision", float("nan"))
        n = int(scorer.thresholds.get(f"{b}_n", 0))
        print(f"  {label:18s} {t:10.2f} {rp*100:13.2f}% {n:8,d}")
    print(f"  the hand-tuned engine used {T_MATCH} / 0.70 / 0.45 on an UNcalibrated")
    print(f"  score, where a threshold had no interpretable meaning at all")

    print("\nDECISION QUALITY      MATCH verdict, all test pairs")
    print(f"  {'':22s} {'learned':>10s}  {'hand-tuned':>10s}   delta")
    for k in ("precision", "recall", "f1"):
        d = (lr[k] - bl[k]) * 100
        print(f"  {k:22s} {lr[k]*100:9.2f}%  {bl[k]*100:9.2f}%  {d:+7.2f}")
    print(f"  {'ROC AUC':22s} {auc_l:9.4f}   {auc_b:9.4f}  {auc_l-auc_b:+7.4f}")
    print(f"  {'false positives':22s} {lr['fp']:9,d}  {bl['fp']:9,d}  {lr['fp']-bl['fp']:+7,d}")
    print(f"  {'false negatives':22s} {lr['fn']:9,d}  {bl['fn']:9,d}  {lr['fn']-bl['fn']:+7,d}")

    # A miss at the MATCH band is only a real loss if it falls out of the
    # workflow entirely. Where the true matches actually land matters more than
    # the recall number on its own.
    print("\nWHERE THE TRUE MATCHES LAND    all test pairs with y=1")
    tp_all = te.y == 1
    tt = scorer.thresholds
    bands = [
        ("MATCH            (auto-assert)", p_learned >= tt["match"]),
        ("NEAR_MATCH       (person confirms)",
         (p_learned >= tt["near"]) & (p_learned < tt["match"])),
        ("REVIEW_REQUIRED  (person looks)",
         (p_learned >= tt["review"]) & (p_learned < tt["near"])),
        ("DISTINCT         (dropped)", p_learned < tt["review"]),
    ]
    n_true = int(tp_all.sum())
    for label, m in bands:
        c = int((m & tp_all).sum())
        print(f"  {label:36s} {c:6,d}  {c/n_true*100:5.1f}%")
    reachable = int(((p_learned >= tt["review"]) & tp_all).sum())
    print(f"  reaches a human or better: {reachable:,}/{n_true:,} "
          f"({reachable/n_true*100:.2f}%)")

    print("\nCALIBRATION           does 0.9 mean 'right nine times in ten'?")
    print(f"  Brier  hand-tuned {brier(p_base[keep], yte):.4f}"
          f"   uncalibrated {brier(scorer.raw(Xte), yte):.4f}"
          f"   calibrated {brier(scorer.calibrate(scorer.raw(Xte)), yte):.4f}")
    print(f"  ECE    hand-tuned {ece_base:.4f}"
          f"   uncalibrated {ece_raw:.4f}"
          f"   calibrated {ece_cal:.4f}")
    print(f"\n  {'bucket':>13s} {'n':>7s} {'predicted':>11s} {'observed':>10s}   gap")
    for r in rows_cal:
        if not r["n"]:
            continue
        gap = abs(r["predicted"] - r["observed"])
        print(f"  [{r['lo']:.1f}, {r['hi']:.1f}) {r['n']:7,d} {r['predicted']:10.3f} "
              f"{r['observed']:9.3f}   {gap:.3f}")

    print("\nTHE VETO              unchanged, and still absolute")
    nv = int(te.vetoed.sum())
    leaked = int((p_learned[te.vetoed] > 0).sum()) if nv else 0
    missed = int(te.y[te.vetoed].sum()) if nv else 0
    print(f"  vetoed test pairs                         {nv:,}")
    print(f"  vetoed pairs given a non-zero probability {leaked:,}   (must be 0)")
    print(f"  true matches lost to the veto             {missed:,}")
    print(f"  veto is a gate applied after scoring, and is not a model feature")

    # ── robustness: the experiment the clean corpus cannot run ──────────
    print("\nROBUSTNESS            token dropout on the probe description")
    print("  The clean split is saturated — after the veto, true matches sit at")
    print("  attribute agreement 1.0 and non-matches at 0.8, so any monotone")
    print("  function of that one feature separates them. Real descriptions are")
    print("  not clean, so the probes are degraded on purpose below.")
    print("  A false MATCH corrupts the master permanently; a false DISTINCT")
    print("  costs a reviewer thirty seconds. They are not symmetric, so")
    print("  precision is reported apart from recall rather than blended into F1.")
    print(f"\n  {'':>8s} {'':>6s} {'--- learned ---':>24s} {'-- hand-tuned --':>24s}")
    print(f"  {'dropout':>8s} {'retr.':>6s} {'prec':>7s} {'rec':>7s} {'ECE':>7s}"
          f" {'prec':>7s} {'rec':>7s} {'ECE':>7s}")
    stressed = stress(engine, records, truth, te_k, top_k=args.top_k)
    for rate, d in sorted(stressed.items()):
        if not len(d["y"]):
            continue
        pl = scorer.probability(d["X"], d["vetoed"])
        i_a = FEATURE_NAMES.index("attribute_agreement")
        i_t = FEATURE_NAMES.index("text_max")
        pb = np.where(d["vetoed"], 0.0,
                      W_ATTR * d["X"][:, i_a] + W_TEXT * d["X"][:, i_t])
        ml = prf(pl, d["y"], scorer.thresholds["match"])
        mb = prf(pb, d["y"], T_MATCH)
        k = ~d["vetoed"]
        e_l = reliability(pl[k], d["y"][k])[1] if k.any() else float("nan")
        e_b = reliability(pb[k], d["y"][k])[1] if k.any() else float("nan")
        print(f"  {rate*100:6.0f}% {d['retrieval_recall']*100:5.1f}%"
              f" {ml['precision']*100:6.1f}% {ml['recall']*100:6.1f}% {e_l:7.3f}"
              f" {mb['precision']*100:6.1f}% {mb['recall']*100:6.1f}% {e_b:7.3f}")
    print("  (retr. = recall@k — the ceiling; a scorer cannot rank what")
    print("   retrieval never returned)")

    print("\nSCOPE")
    print("  Synthetic corpus; labels correct by construction. These numbers")
    print("  describe this engine on this corpus and are NOT a claim about")
    print("  performance on real CPSE data. No real material master was used.")
    print("=" * W)

    if not args.no_save:
        meta.update({
            "test_precision": lr["precision"], "test_recall": lr["recall"],
            "test_f1": lr["f1"], "test_auc": auc_l,
            "test_ece_calibrated": ece_cal, "test_ece_uncalibrated": ece_raw,
            "baseline_f1": bl["f1"], "baseline_ece": ece_base,
        })
        scorer.metadata = meta
        p = scorer.save(DEFAULT_PATH)
        print(f"\nsaved {p}  ({p.stat().st_size:,} bytes)")
        (p.parent / "report.json").write_text(json.dumps(
            {"thresholds": scorer.thresholds, "metrics": meta,
             "reliability_calibrated": rows_cal}, indent=2, default=float))

    print(f"\ntotal {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
