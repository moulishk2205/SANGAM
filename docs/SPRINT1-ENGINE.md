# Sprint 1 — the matching engine

Measured 2026-08-26 on this machine. Reproduce with:

    PYTHONPATH=. .venv/bin/python scripts/evaluate.py
    PYTHONPATH=. .venv/bin/python scripts/evaluate.py --no-embeddings
    .venv/bin/python -m pytest tests/ -q

---

## Read this before quoting any number below

**These results are close to circular, and the headline F1 should not be presented as
evidence that the matcher is accurate.**

The corpus is generated from specifications we define. The attributes are extracted by
rules we wrote. The labels are derived from those same specifications. So the
evaluation largely measures whether the extractor can invert the generator — which it
can, hence 100% precision.

This is exactly the failure mode the Phase 0 risk register flagged as
*"Circular evaluation — metrics measure the generator"*, rated likelihood High,
impact High. It has not been mitigated yet; it has only been documented.

**What these numbers legitimately show:** the pipeline is wired correctly end to end,
the veto fires where it must, unknowns never veto, and the system abstains rather than
guessing. That is what a first review needs to see.

**What they do not show:** performance on real material descriptions. The honest
statement is *"measured on a synthetic corpus with construction-derived labels"*, said
out loud, before anyone asks.

Fixing it requires a test set the generator never touched — the ~300 hand-collected
Indian tender lines, plus the FLIS part-number groups once the prefix/mode encoding is
decoded. Both are post-review work.

---

## Results

Corpus: 1,800 records rendered from 600 canonical specs across fasteners, valves and
bearings. 300 probe records, retrieval pool 50.

### Extraction

| | |
|---|---|
| Item type classified | **1,800 / 1,800 (100.0%)** |
| Critical attributes present | **99.0%** mean coverage |

### Retrieval and decision

| | With embeddings | Lexical only |
|---|---:|---:|
| recall@1 | **94.33%** | 79.67% |
| recall@3 | 96.00% | 81.00% |
| recall@5 | 96.67% | 81.33% |
| recall@10 | **97.00%** | 82.00% |
| MATCH precision | 100.00% | 100.00% |
| MATCH recall | 95.83% | 96.16% |
| F1 | 97.87% | 98.04% |
| p50 latency | 13.1 ms | 4.2 ms |
| p95 latency | 17.0 ms | 4.6 ms |

### The ablation that justifies the embedding model

Removing the dense channel costs **14.7 points of recall@1** (94.33% → 79.67%) while
leaving decision precision untouched. That is a measured reason to include embeddings,
not an aesthetic one — and it lands exactly where the architecture predicts: the dense
channel improves *which candidates get considered*, and changes the *verdict* on those
candidates not at all.

That separation is the architecture working as designed: retrieval proposes,
specification decides.

### The veto — the architectural claim, quantified

Across the 300 probes, **2,408 candidates were rejected on a critical attribute**, and
**2,399 of them carried text similarity ≥ 0.85**.

Those 2,399 are pairs that a similarity-threshold matcher — the "upload CSV →
embeddings → duplicates" design — would have merged. They are different materials.
Under this architecture the merge is not unlikely; it is unreachable.

Note the contrast in the lexical-only run: only 133 vetoed pairs cleared 0.85 text
similarity, because char-n-gram similarity separates `M10 X 50` from `M10 X 75` more
than embeddings do. **The better the semantic model, the more essential the veto
becomes.** That is worth saying out loud — it inverts the usual assumption that a
stronger embedding model reduces the need for engineering rules.

---

## What is built

| Component | Module | State |
|---|---|---|
| Value model — Point / Range / ValueSet / Unknown | `src/nmc/types.py` | done |
| Normaliser + abbreviation gazetteer (versioned) | `src/nmc/normalise/text.py` | done |
| Attribute templates + criticality | `src/nmc/extract/templates.py` | done |
| Extraction grammar (11 rules) | `src/nmc/extract/grammar.py` | done |
| Hybrid retrieval, RRF-fused | `src/nmc/match/retrieve.py` | done |
| Three-valued comparator + veto | `src/nmc/match/compare.py` | done |
| Scoring, decision bands, abstention | `src/nmc/match/engine.py` | done |
| Check-before-create | `src/nmc/match/engine.py` | done |
| Demo corpus generator | `src/nmc/demo/corpus.py` | done |
| Evaluation harness | `scripts/evaluate.py` | done |
| Demo-moment tests (11) | `tests/test_demo_moments.py` | passing |
| REST API | — | **not started** |
| Persistence / canonical master | — | **not started** |
| Frontend | — | **awaiting UI specification** |

## Design decisions worth defending

1. **Veto is a gate, not a weight.** `score = veto × (0.85·attribute_agreement +
   0.15·text)`. A vetoed pair scores exactly 0. Asserted by a test that hands the
   scorer a semantic similarity of 1.0 and still requires DISTINCT.
2. **MATCH requires every critical attribute known and agreeing.** `SS HEX BOLT` and
   `SS HEX BOLT M10 X 50` agree on everything they both mention, and are not the same
   material. The system returns REVIEW_REQUIRED rather than guessing.
3. **Text can only raise a score, never lower it.** Text is retrieval evidence, not
   identity evidence; a badly-worded description of the right material must not lose
   to a well-worded description of the wrong one.
4. **UNKNOWN never vetoes and never counts as agreement.** It is excluded from the
   agreement denominator and forces abstention when it lands on a critical attribute.
5. **The dense channel is optional.** If the model fails to load the engine degrades
   to lexical and says so. A demo that cannot start because a model file is missing is
   a worse failure than a slightly weaker ranking.
6. **`confidence` is not calibrated** and the payload carries `"calibrated": false`.
   Calling it a probability needs a fitted calibrator on a labelled held-out set.

## Known gaps

- **Circular evaluation** (above). The most important open item.
- **FLIS numerics still undecoded**, so the MVP deliberately uses values whose units
  we control end to end. Unchanged from Sprint 0.
- **Item-name classification is a gazetteer lookup**, not a model. Deliberate — a
  bolt/nut confusion should be a dictionary entry a human fixes, not a model error —
  but it will not generalise to item types absent from the dictionary.
- **Range-vs-range comparison is implemented and unit-tested but unexercised by the
  demo corpus**, because the generator emits points. It will matter as soon as real
  catalogue values arrive.
- **No persistence.** The engine is in-memory; canonical IDs are not yet minted or
  stored.
