#!/usr/bin/env python3
"""
Measure the matching engine. Real numbers only — nothing here is estimated.

Ground truth is correct by construction: two records match iff they were rendered
from the same canonical specification. That is the only defensible way to claim a
label on generated data, and it is why the corpus is generated downward from specs
rather than by perturbing strings.

Reported separately, because they answer different questions:

  * retrieval recall@k — the ceiling on everything. A match the retriever never
    returns is one the system can never make.
  * decision precision / recall / F1 — the quality of the MATCH verdict.
  * veto behaviour — how often the specification layer overrules the text layer,
    which is the whole architectural claim.

    python scripts/evaluate.py                 # with embeddings
    python scripts/evaluate.py --no-embeddings # lexical only, for comparison
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import random
import time
from collections import defaultdict

from src.nmc.demo.corpus import build_corpus
from src.nmc.match.engine import MatchingEngine
from src.nmc.types import Decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", type=int, default=600)
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--probes", type=int, default=300)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--no-embeddings", action="store_true")
    args = ap.parse_args()

    records, truth = build_corpus(args.specs, args.variants)
    groups: dict[str, list[str]] = defaultdict(list)
    for rid, key in truth.items():
        groups[key].append(rid)

    print(f"corpus       {len(records):,} records from {len(groups):,} canonical specs")
    print(f"dense channel{'  OFF (lexical only)' if args.no_embeddings else ' ON (bge-small-en-v1.5)'}")

    t0 = time.time()
    engine = MatchingEngine(use_embeddings=not args.no_embeddings)
    engine.index(records)
    print(f"index built  {time.time()-t0:,.1f}s")

    # extraction coverage — how often the veto attributes are actually populated
    from src.nmc.extract.grammar import coverage
    from src.nmc.extract.templates import critical_codes
    cov = [coverage(r, critical_codes(r.item_name)) for r in records if r.item_name]
    unclassified = sum(1 for r in records if not r.item_name)
    print(f"\nEXTRACTION")
    print(f"  item type classified   {len(records)-unclassified:,}/{len(records):,} "
          f"({(len(records)-unclassified)/len(records)*100:.1f}%)")
    print(f"  critical attrs present {sum(cov)/max(len(cov),1)*100:.1f}% mean coverage")

    # only probe records that actually have a true partner in the corpus
    rng = random.Random(20260826)
    probeable = [r for r in records if len(groups[truth[r.id]]) > 1]
    rng.shuffle(probeable)
    probes = probeable[: args.probes]

    hits_at = {1: 0, 3: 0, 5: 0, 10: 0}
    tp = fp = fn = 0
    vetoed_total = 0
    vetoed_would_have_passed = 0
    latencies: list[float] = []

    for src in probes:
        expected = set(groups[truth[src.id]]) - {src.id}
        t = time.time()
        results = engine.match(src, top_k=args.top_k, pool=50)
        latencies.append((time.time() - t) * 1000)

        ranked = [r.record.id for r in results]
        for k in hits_at:
            if expected & set(ranked[:k]):
                hits_at[k] += 1

        for r in results:
            is_true = r.record.id in expected
            said_match = r.decision is Decision.MATCH
            if said_match and is_true:
                tp += 1
            elif said_match and not is_true:
                fp += 1
            elif not said_match and is_true:
                fn += 1

            if r.explanation.critical_veto:
                vetoed_total += 1
                # would the text signal alone have called this a match?
                if r.explanation.semantic_score >= 0.85 or r.explanation.lexical_score >= 0.85:
                    vetoed_would_have_passed += 1

    n = len(probes)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    latencies.sort()

    print(f"\nRETRIEVAL   ({n} probes, pool 50)")
    for k in sorted(hits_at):
        print(f"  recall@{k:<3} {hits_at[k]/n*100:6.2f}%")

    print(f"\nDECISION    (MATCH verdict vs construction ground truth)")
    print(f"  precision   {prec*100:6.2f}%     tp={tp:,} fp={fp:,}")
    print(f"  recall      {rec*100:6.2f}%     fn={fn:,}")
    print(f"  F1          {f1*100:6.2f}%")

    print(f"\nVETO        (the architectural claim)")
    print(f"  candidates vetoed on a critical attribute   {vetoed_total:,}")
    print(f"  of those, text similarity >= 0.85           {vetoed_would_have_passed:,}")
    print(f"  -> pairs a similarity-threshold matcher would")
    print(f"     have wrongly merged, and the veto caught  {vetoed_would_have_passed:,}")

    print(f"\nLATENCY     (end-to-end match, per source record)")
    print(f"  p50 {latencies[len(latencies)//2]:6.1f} ms")
    print(f"  p95 {latencies[int(len(latencies)*0.95)]:6.1f} ms")
    print(f"  max {latencies[-1]:6.1f} ms")

    print("\nNOTE  Corpus is SYNTHETIC surface text over specs we defined; labels are")
    print("      correct by construction. These numbers describe the engine on that")
    print("      corpus and are NOT a claim about performance on real CPSE data.")


if __name__ == "__main__":
    main()
