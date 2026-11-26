# Datasets

Two kinds of data live around SANGAM, and they are kept apart on purpose.

| | What | Where | Real or synthetic |
|---|---|---|---|
| **Training data** | The labelled pairs the match scorer learns from | [`training/`](training/) — in git | Synthetic, labels correct by construction |
| **Reference data** | DLA FLIS / PUB LOG catalogue + GSA NSN extract | `data-v1` GitHub release, restored by [`scripts/fetch_data.sh`](../scripts/fetch_data.sh) | Real, public domain / CC0 |

Full provenance and licences: [`docs/DATA_PROVENANCE.md`](../docs/DATA_PROVENANCE.md).

---

## `training/` — the scorer's training set

Exported by [`scripts/export_training_data.py`](../scripts/export_training_data.py)
with exactly the arguments and seeds [`scripts/train_scorer.py`](../scripts/train_scorer.py)
uses, so these files are the train / validation / test split behind
[`models/scorer/scorer-v1.json`](../models/scorer/scorer-v1.json). Row counts match
[`models/scorer/report.json`](../models/scorer/report.json).

| File | Rows | Positives | What a row is |
|---|---:|---:|---|
| `corpus.csv` | 1,800 | — | One material record as a CPSE wrote it, with its true identity and split |
| `pairs_train.csv` | 12,960 | 1,932 | A (probe, candidate) pair the retriever surfaced, featurised and labelled |
| `pairs_val.csv` | 4,320 | 640 | Same, used to fit the isotonic calibrator and set the band thresholds |
| `pairs_test.csv` | 4,320 | 653 | Same, read exactly once at the end of training |
| `manifest.json` | — | — | Versions, seeds, counts and SHA-256 of every file |

### How it was made

1. **600 canonical specifications** (bolts, nuts, studs, pipe, flanges, valves,
   gaskets, bearings…) are defined in [`src/nmc/demo/corpus.py`](../src/nmc/demo/corpus.py).
2. Each is **rendered three times** through per-organisation "house styles":
   `SS HEX BOLT M10X50`, `BOLT HEX SS M10*50`,
   `STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM`. Two records match **iff** they
   were rendered from the same spec — so every positive label is true by
   construction, never asserted.
3. Identities (`spec_key`), **not records**, are split 60 / 20 / 20 with seed
   `20260902`. A bolt is wholly in train, wholly in validation or wholly in test;
   `assert_no_leakage()` proves it after the fact.
4. Negatives are **mined from the retriever's own top-12**, not sampled at random:
   `SS HEX BOLT M10X75` against `MS HEX BOLT M10X75`, never a bolt against a
   bearing. These are the pairs the system is really asked about.

### Columns in `pairs_*.csv`

| Column | Meaning |
|---|---|
| `source_id`, `candidate_id` | Record ids from `corpus.csv` |
| `spec_key` | The probe's true identity |
| `label` | 1 if both records were rendered from the same spec |
| `vetoed` | 1 if a CRITICAL attribute disagreed — the gate, kept **out** of the features |
| `attribute_agreement` | Share of comparable attributes that agree, in [0, 1] |
| `text_max` | Strongest text channel |
| `semantic` | Dense channel (`bge-small-en-v1.5` cosine) |
| `lexical` | Character 4-gram TF-IDF cosine |
| `text_gap` | \|semantic − lexical\| — the channels disagreeing is itself evidence |
| `frac_agree`, `frac_disagree`, `frac_unknown` | Shape of the evidence table |
| `crit_known_frac` | How much of the discriminating set was stated at all |
| `crit_agree_frac` | Of the critical attributes that were stated, how many agree |
| `n_rows` | Template width, scaled |
| `same_item_name` | 1 when both classified to the same approved item name |

```python
import pandas as pd
tr = pd.read_csv("datasets/training/pairs_train.csv")
X, y = tr.iloc[:, 5:], tr["label"]          # 12 features, 1 label
```

> [!IMPORTANT]
> Every number measured on this set is a statement about the engine **on this
> corpus**. It is not a claim about a real CPSE material master — none is public,
> and none was used. The pipeline is what would be pointed at real data; the
> numbers would then have to be re-earned.

---

## Reference data (`data-v1` release)

| Asset | Size | Licence | Used for |
|---|---:|---|---|
| `H-SERIES.zip` | 14.6 MB | US federal, 17 U.S.C. §105 | ~80k approved item names with definitions, supply classes |
| `MRD.zip` | 4.2 MB | US federal | Attribute dictionary, controlled vocabularies |
| `IDENTIFICATION.zip` | 362 MB | US federal | NIIN/INC backbone, standardization decisions |
| `REFERENCE.zip` | 180 MB | US federal | Manufacturer part numbers per NIIN |
| `FLISV.zip` | 385 MB | US federal | Coded attribute assertions per NIIN |
| `flis-slice.zip` | 82 MB | derived | The demo families, pre-sliced by `scripts/slice_flis.py` |
| `nsn-extract.xlsx` | 1 MB | CC0 (data.gov) | 12,454 real prose descriptions — realism check |

SHA-256 of every DLA archive is pinned in [`flis/MANIFEST.json`](flis/MANIFEST.json);
`fetch_data.sh` refuses any file that does not match.
