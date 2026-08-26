# Sprint 0 findings

Measured on **2026-08-26**. Every number here was produced by a script in this repo
against real data on this machine — nothing is quoted from research or estimated.

Reproduce with:

    python scripts/fetch_flis.py --core
    python scripts/slice_flis.py

---

## 1. The #1 project risk is closed

The Phase 0 plan named FLIS access as the top risk, on the basis that `dla.mil`
returned 403 to scripted fetchers and might be US-IP-restricted.

**It is not restricted. The data is downloadable from this machine.**

| Client | Result |
|---|---|
| plain `curl` | 403 |
| `curl` + full browser header set | **200** |
| Python `urllib` + byte-identical headers | 403 |

The WAF fingerprints below the header layer, so `scripts/fetch_flis.py` shells out to
`curl` on purpose. All five core archives are downloaded, SHA-256 hashed into
`data/raw/flis/MANIFEST.json`, and every byte size matches the research figures exactly.

**Contingency F2 (BOLTS + UNSPSC + GSA) is no longer on the critical path.** It stays
documented as a fallback but should not consume effort.

---

## 2. The catalogue slice — real volumes

Seven Federal Supply Classes covering the six demo commodity families:
`5305` screws · `5306` bolts · `5310` nuts and washers · `4730` pipe fittings ·
`3110` bearings · `4820` valves · `6145` wire and cable.

| Measure | Value |
|---|---|
| NIINs scanned across the whole catalogue | 17,005,582 |
| **NIINs in our commodity slice** | **1,824,354** |
| Manufacturer part-number rows in slice | 2,396,581 |
| **NIINs carrying more than one part number** | **492,965** |
| Attribute assertions in slice | 8,183,475 |
| Distinct (item-name × attribute) combinations | 21,409 |
| Slice runtime, streaming ~5 GB | **103 s** |

### Duplicate ground truth is abundant — but the headline number is a trap

492,965 NIINs carry multiple manufacturer part numbers, implying **15,973,381**
positive pairs by combinatorics. **Do not quote that number.** It is dominated by a
few items with enormous reference lists — one ordinary bolt, NIIN `002061914`, carries
**377 part numbers**, which alone yields 70,876 pairs.

> **Design consequence.** Pair sampling must cap contributions per NIIN (suggest ≤10
> pairs per item, sampled) or a handful of items will dominate training and every
> metric will be about them. Target the plan's 50k–150k labelled pairs by
> *sampling breadth*, not by taking the Cartesian product.

### Equivalence ground truth is real, but skewed

The plan flagged this as unmeasured, with a threshold: below ~2,000 pairs, equivalence
becomes a derived rule rather than an observed decision.

| Measure | Value |
|---|---|
| Standardization rows in slice | 1,871,574 |
| **With a non-empty `RELATED_NSN`** | **23,610** ✅ above threshold |

Item Standardization Code distribution among those pairs:

| ISC | Count | Meaning (secondary source — **verify against DoD 4100.39-M**) |
|---|---|---|
| `3` | 23,523 | Not authorised for procurement — item was superseded |
| `E` | 62 | Superseded |
| `2` | 24 | Authorised, in a reduction study |
| `1` | 1 | Approved replacement for other items |

**Honest reading:** the relation is real and human-decided, but it is almost entirely
the *deprecated* side of the decision (ISC 3). The "this is the approved replacement"
direction (ISC 1) is essentially absent — one row. So we can say *"item X was retired
in favour of item Y by a standardization decision"*, which is a genuine equivalence
signal, but we cannot claim a balanced bidirectional interchangeability dataset.

This **reinforces** the Phase 0 decision to make `EQUIVALENCE_CANDIDATE` a
human-asserted relation the AI never auto-approves.

---

## 3. The attribute template works — with a correction

The design hangs on being able to answer *"which attributes are decisive for this kind
of item?"* from real data.

### The dictionary alone is not enough

`MRD06P1` + `MRD0500` give INC `01847` (BOLT,MACHINE) only **13 attributes**, and
**none of them is thread diameter or length** — the very attributes the veto needs.

Cause: the MRD tables describe attributes with *coded reply tables*. Dimensional
attributes carry numeric replies and so never appear there. **The MRD dictionary is
not the schema.** Anyone building from the dictionary alone would have discovered this
in week 6.

### The empirical template does work

Deriving the template from what is actually recorded against real items —
31,411 bolts carrying attributes:

| MRC | Coverage | Requirement |
|---|---|---|
| `MATT` | 127.8%* | MATERIAL |
| `AATB` | 91.6% | WIDTH BETWEEN FLATS |
| `AASU` | 87.7% | HEAD HEIGHT |
| **`AASB`** | **82.7%** | **FASTENER LENGTH** |
| **`AASA`** | **79.1%** | **THREAD LENGTH** |
| `MDCL` | 65.0% | MATERIAL DOCUMENT AND CLASSIFICATION |
| **`AHYM`** | **61.3%** | **NOMINAL THREAD DIAMETER** |
| `AAJF` | 61.0% | THREAD DIRECTION |
| `THSD` | 60.8% | THREAD SERIES DESIGNATOR |
| `AASK` | 59.9% | HEAD STYLE |
| `CMLP` | 56.7% | THREAD QUANTITY PER INCH |
| `AAJD` | 54.1% | THREAD CLASS |

\* over 100% because the attribute is multi-valued — see §4.

**The veto attributes exist in real data at usable coverage.** The architecture holds.

> **Design change.** `attribute_frequency.csv` — the empirical template — becomes a
> first-class build artefact, generated from item data and *cross-checked* against the
> MRD dictionary rather than derived from it. Coverage percentage feeds directly into
> criticality assignment: an attribute recorded on 82% of items is a candidate veto
> attribute; one recorded on 3% cannot be.

---

## 4. Three things the plan did not anticipate

Found by reading real values rather than assuming their shape. Each changes the
comparator design, and all three are cheap now and expensive in week 6.

### (a) Attributes are multi-valued

`MATT` (material) carries up to **72 values** on a single item. `HUES` up to 28,
`MDCL` up to 27. A real bolt shows four material codes at once (`CU0098`–`CU0101`).

The plan assumed scalar `AGREE / DISAGREE / UNKNOWN` per attribute. That is wrong for
a large class of attributes.

**Needed:** set-comparison semantics — *identical set*, *overlapping*, *subset*,
*disjoint* — and a policy for which of those counts as agreement. Disjoint material
sets on two candidate bolts should almost certainly veto; overlapping sets should not.

### (b) Attributes are frequently ranges, not points

Values carry a letter prefix. For `AATB` (width between flats), **71.9% of items carry
both an `AB` and an `AC` value** — min and max endpoints of a tolerance range:

```
AATB = AB0.195   AATB = AC0.211     -> range 0.195 … 0.211
AASA = AB0.889   AASA = AC1.000     -> range 0.889 … 1.000
AHYM = A0.312                       -> single value
```

**Needed:** the comparator must handle point-vs-point, point-vs-range and
range-vs-range, with an explicit policy (overlap? containment? midpoint within
tolerance?). This is *good news* — it means engineering tolerance is already in the
source data rather than something we have to invent — but it must be designed, not
bolted on.

### (c) Values are prefix-coded and unit-ambiguous

`AHYM` values are `A0.312` (147,303 rows) and `L…` (8,102 rows). Mode codes across the
slice are `J` 3.43M, `D` 2.90M, `A` 0.70M, `L` 0.65M, `G` 0.47M.

The prefix and mode code together encode how the reply is expressed — and the values
above are imperial (0.312 in = 5/16 in), so **unit interpretation is not optional**.

> **OPEN ITEM — highest priority for the next work block.** Decode the prefix and mode
> code semantics from the PUB LOG layout PDFs (`Characteristics FOIA Layout.pdf`,
> `New_MRD.pdf`, both on the reading-room page) or DoD 4100.39-M. Until this is
> decoded, no numeric comparison is trustworthy. Everything downstream of the
> comparator is blocked on it.

### (d) Reference numbers need quality filtering

Part numbers include entries like `5-2BALT1PC6` — drawing-derived references, not
clean manufacturer part numbers. `V_FLIS_PART` carries `RNCC` and `RNVC` codes
(reference number category and variation) precisely to distinguish these.

**Needed:** filter on `RNCC`/`RNVC` before treating a part-number match as identity
evidence, or the reference matcher will generate false positives on drawing fragments.

---

## 5. Status against the Sprint 0 exit criteria

| Criterion | Status |
|---|---|
| FLIS archives downloaded and hashed | ✅ 5 archives, 904 MB, manifest written |
| Commodity slice built | ✅ 1.82M items, 103 s |
| Equivalence-pair yield measured | ✅ 23,610 — above the 2,000 threshold |
| Duplicate-pair yield measured | ✅ 492,965 multi-part NIINs (sample, don't multiply) |
| Empirical attribute template derived | ✅ 21,409 INC×MRC rows |
| Attribute value semantics understood | ⚠️ **partially — prefix/mode decode is open** |
| Regex extraction coverage on 500 real descriptions | ⬜ not started |
| Cross-encoder benchmarked on demo laptop | ⬜ not started |
| Pair completeness measured | ⬜ not started |
| 300 Indian tender lines collected | ⬜ **human task — not started** |
| Idea submitted (20 Sep) | ⬜ **human task — owner not yet named** |

---

## 6. Next work block

1. **Decode the value prefix and mode codes.** Blocks the comparator. Start with the
   layout PDFs on the reading-room page.
2. **Build the canonical-record renderer** — item name + decisive attributes → a
   canonical description string, plus the ≤40-char SAP-compatible short text.
3. **Sample the labelled pair set** with the per-NIIN cap, entity-level split.
4. **Extraction spike** — 30 regex rules over the GSA prose descriptions
   (already downloaded, CC0) and measure coverage. If below 70%, escalate.
5. **Human tasks, unblocked and unstarted:** name an owner for the 20 Sep idea
   submission; begin collecting Indian CPSE tender lines.
