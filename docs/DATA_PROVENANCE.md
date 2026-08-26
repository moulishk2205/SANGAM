# Data provenance

Every dataset this project touches, where it came from, what it may legally be used
for, and whether it is real or generated. **No dataset is committed to this repository.**

This file is not paperwork. In a government procurement context the first serious
question is "whose data is that?", and the answer has to be specific.

Last verified: **2026-08-26**

---

## The one-paragraph answer

> Our canonical items, their classification, their attribute schema and every match
> label come from the US Defense Logistics Agency's publicly released FLIS / PUB LOG
> catalogue, built on the same NATO Codification System that India's own National
> Codification Bureau adopted in 2008. What we generate synthetically is only the
> *surface text* — the messy, abbreviated way five different CPSEs would each write
> down the same real item — because no Indian CPSE material master is public and we
> will not scrape one. Reported accuracy separates the two.

---

## 1. Primary source — DLA FLIS / PUB LOG

| | |
|---|---|
| **Source** | https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/ |
| **Publisher** | US Defense Logistics Agency, Logistics Information Services |
| **Licence** | US federal FOIA reading-room release. Works of the US government are not subject to US domestic copyright (17 U.S.C. §105). No click-through licence, no registration, no fee. |
| **Retrieved** | 2026-08-26 — SHA-256 of every archive in `data/raw/flis/MANIFEST.json` |
| **Fetched by** | `scripts/fetch_flis.py` |
| **Real or synthetic** | **REAL** |

### Access note

`www.dla.mil` sits behind a WAF that fingerprints non-browser HTTP clients. Verified
this session:

| Client | Result |
|---|---|
| plain `curl` | **403** |
| `curl` + full browser header set | **200** |
| Python `urllib` + identical headers | **403** |

The WAF is fingerprinting below the header layer, so `scripts/fetch_flis.py` shells
out to `curl` deliberately. Do not "clean this up" into `requests`.

**The archives are downloaded once and kept.** `dla.mil` is never a build-time or
demo-time dependency. If DLA restructures again, we already hold the data.

### Archives used

| Archive | Size | Contents |
|---|---|---|
| `H-SERIES` | 14.6 MB | Item-name (INC) and supply-class dictionaries |
| `MRD` | 4.2 MB | Attribute (MRC) dictionary and controlled vocabularies |
| `IDENTIFICATION` | 346 MB | NIIN/INC backbone + standardization decisions |
| `REFERENCE` | 172 MB | Manufacturer part numbers per NIIN |
| `FLISV` | 367 MB | Coded attribute assertions per NIIN |

### Verified record counts

Counted directly, not quoted from anywhere:

| Table | Rows | Use |
|---|---|---|
| `P_H6_PICK` / `V_H6_NAME_INC` | 79,883 | Approved item names, each with an English definition |
| `MRD0107` | 27,552 | Attribute dictionary |
| `MRD0300` | 164,926 | Controlled-vocabulary reply values |
| `MRD0500` | 211,397 | INC × FIIG × MRC style rows |
| `MRD06P1` | 45,305 | Which coded attributes apply per item name |
| `V_H6_RELATED` | 33,930 | Confusable item-name pairs — a curated hard-negative mine |
| `V_H6_MODIFIER` | 54,604 | Item-name modifiers |
| `V_H2_FSC` | 676 | Supply classes with inclusion/exclusion scope rules |
| `V_H2_FSC_INC` | 6,877,262 | Valid (class, item-name) combinations |

### Ground truth derived from it

Two real relations, neither of them asserted by us:

1. **Duplicates** — distinct `(CAGE_CODE, PART_NUMBER)` rows sharing one NIIN.
   Different manufacturers' codes for one physical item. This is literally the
   SIH26099 problem with the answer key attached.
2. **Equivalence** — `NIIN → RELATED_NSN` in `V_FLIS_STANDARDIZATION`, carrying an
   Item Standardization Code recording a human decision that one item replaces
   another.

> **Open measurement.** The real yield of relation 2 inside our commodity slice is
> being measured by `scripts/slice_flis.py`. If it comes in below ~2,000 pairs, the
> equivalence class becomes a *derived rule* rather than an *observed decision*, and
> we say so openly. Recorded in `docs/SPRINT0-FINDINGS.md`.

### ISC semantics — treat with care

The Item Standardization Code meanings currently cited come from a commercial FLIS
reseller's reference page — a **secondary source**. The authority is DoD 4100.39-M
(FLIS Procedures Manual). **Do not put ISC semantics in the deck until someone has
opened the manual.**

---

## 2. Supporting sources

| Source | Licence | Real? | Use | Status |
|---|---|---|---|---|
| **BOLTS** (`boltsparts/BOLTS_archive`) | Data files **LGPL-2.1+**; repo GPL-3.0 | REAL specs | Fastener/pipe/bearing dimension tables with typed attribute schemas and enumerated legal values. Fallback canonical seed. | Attribute BOLTS explicitly if used |
| **UNSPSC** via UNGM export | Free to use; **do not redistribute the file** | REAL | Category crosswalk (13,335 codes). No attributes — do not oversell. | Reference the UNGM URL, never commit the XLSX |
| **GSA NSN Extract** (data.gov) | **CC0** | REAL | 12,454 real prose descriptions keyed to NSNs. Realism check. | Freely usable |
| **WDC Products** | None stated; academic norm | REAL | Published baselines, incl. the 100%-unseen-entity variant | Cite the paper, do not republish |
| **DeepMatcher / Magellan suite** | None stated; academic norm | REAL | Published baselines incl. *Dirty* variants | Cite the papers |
| **PriceRunner** (`lakritidis/product-matching`) | **GPL-2** | REAL | Clustering + matching + classification ground truth | Note the copyleft |
| **MaintIE** | **MIT** | REAL | Real terse industrial maintenance text. Calibrates the noise model — **not** a material master. | Freely usable |
| **Indian CPSE tender line items** | Public tender documents | REAL | ~300 hand-collected lines. Realism test set + noise calibration. | **Manual only.** Rate-limit ≤1 req/s, honour robots.txt, no login-gated content, never republish vendor names or prices |

---

## 3. Explicitly rejected

Recorded so nobody re-litigates them under deadline pressure.

| Source | Why rejected |
|---|---|
| **GeM** | Website policy: *"Contents of this website may not be reproduced partially or fully without due permission in writing in advance from the GeM SPV."* A permissive `robots.txt` does not override an explicit copyright clause. Scraping GeM and presenting it to a panel including Government of India procurement officials is a catastrophic own-goal. |
| **CPPP / eprocure.gov.in** | Tender listing is CAPTCHA-gated. Defeating a CAPTCHA on a government portal is indefensible technically, ethically, and on stage. |
| **data.gov.in** | Excellent licence (GODL-India), but **zero item-level material data exists**. Verified by search. |
| **eCl@ss** | Best attribute model of any commercial standard, but licence-gated. Cannot be shipped. |
| **McMaster-Carr, Grainger, Fastenal, RS, Misumi, IndiaMART** | `robots.txt` disallows catalogue paths, or edge-blocks bots outright. Commercial ToS applies. |
| **FED LOG, PUB LOG DVD, NMCRL, nsncenter** | Access-restricted, paid, or defunct. |
| **LLM-generated match labels** | Label laundering. Metrics would measure agreement with a language model, not correctness. |

---

## 4. Real vs synthetic — the honest accounting

| Layer | Real | Synthetic |
|---|---|---|
| Item identity | **100%** | 0% |
| Classification | **100%** | 0% |
| Attribute schema | **100%** | 0% |
| Attribute values | **100%** | 0% |
| Match / no-match labels | **~100%** derived | 0% asserted |
| Description surface text | ~1–3% | **~97%** |
| CPSE identity and internal codes | 0% | **100%** — simulated, labelled |
| Dashboard figures | 0% | **100%** — demo data |

Every generated record carries a `provenance` value of `REAL_CATALOGUE`,
`REAL_TENDER`, `SYNTHETIC_VARIANT` or `HAND_CURATED`, and the UI shows it on the
record detail page. Per-record, not per-dashboard — a judge will click in.

---

## 5. Rules

1. **Never claim to hold CPSE material master data.** We hold public tender line
   items and a US federal catalogue. Say exactly that.
2. **Never present vendor duplicate-rate statistics as measured fact.** Figures like
   "10–20% of MRO stock is duplicated" are vendor marketing. Cite the vendor by name
   and say "vendor-reported", or use the rate measured on our own labelled corpus.
3. **Never let a demo depend on a network fetch.** Archives are local and hashed.
4. **Volunteer the provenance limitation before anyone asks.** Specificity here is a
   credibility asset. Teams that hide it get destroyed in Q&A.
