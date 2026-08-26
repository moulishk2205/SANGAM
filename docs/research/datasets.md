# SIH26099 — Phase 0 Research: REAL, LEGALLY USABLE TRAINING & DEMO DATA

Author: technical architect review. Date of research session: **2026-08-26**.
Scope: find data that actually exists, can actually be downloaded, and can legally be used
to train and demo an AI material-code harmonization system.

## EPISTEMIC LABELS USED IN THIS DOCUMENT

- **[VERIFIED]** — I fetched it in this session. URL and observed evidence given.
- **[JUDGMENT]** — my reasoned engineering opinion, not a fact.
- **[ASSUMPTION]** — plausible but unchecked. Every one states how to check it.
- **UNVERIFIED** — I could not confirm; do not repeat it as fact.

Nothing in the "verified" column was invented. Record counts marked *estimated* were derived
by decompressing a real sample of the real file and extrapolating; that arithmetic is shown.

---

# 0. EXECUTIVE VERDICT (read this if you read nothing else)

**The data problem is SOLVED, and it is solved better than the brief assumes.**

The single highest-value source is the **US DLA PUB LOG / FLIS public data release**. It is free,
it is downloadable right now without registration, it is refreshed monthly, and — critically —
it contains not just item names and classifications but **machine-readable structured attributes
with controlled vocabularies, AND two independent real ground-truth relations for the exact
matching problem in SIH26099**:

1. `V_FLIS_PART.CSV` — many manufacturer part numbers / CAGE codes → one canonical NIIN.
   This is literally "many organisations' codes for the same physical item".
2. `V_FLIS_STANDARDIZATION.CSV` — NIIN → RELATED_NSN with an Item Standardization Code
   recording an official human standardization decision (item X is replaced by / is the
   authorised replacement for item Y). This is literally "functionally equivalent, human-approved".

That means the team **does not have to invent its labels**. It can report precision/recall against
labels produced by a real national codification authority, on real catalogue data, at a scale of
millions — then generate Indian-CPSE-style *surface noise* on top of those true identities.

**Second key finding, and it is bad news that contradicts the brief:** there is essentially
**no Indian public item-level material master data**. `data.gov.in` has none. GeM's terms
explicitly forbid reproduction of site content. CPPP/eprocure sits behind a CAPTCHA. The brief's
Section 5 optimism about "public government procurement datasets / public CPSE material catalogs"
is **wrong on the facts** and should be corrected before the SIH presentation, where a judge from
a CPSE will know it is wrong.

**Recommended corpus composition (defensible, honest):**
- ~100% of *item identity and equivalence ground truth*: REAL (FLIS/PUB LOG).
- ~100% of *Indian-CPSE-style surface descriptions*: SYNTHETIC, generated from real identities.
- Independent published benchmarks (WDC Products, Abt-Buy, Amazon-Google, Walmart-Amazon,
  PriceRunner) used to report **real numbers against real published baselines**.

---

# 1. NSN / FLIS / NATO CODIFICATION  — **THE PRIMARY SOURCE. USE.**

## 1.1 DLA FLIS Data Electronic Reading Room (PUB LOG monthly CSV release)

- **Name:** Federal Logistics Information Services (FLIS) Data Electronic Reading Room / PUB LOG data files
- **URL:** https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/
- **[VERIFIED]** Page loaded 2026-08-26. Page text states: *"The FLIS Legacy Files were replaced on
  1 Apr 2023. The PUB LOG® files below provide data in an easy to use .CSV format that can be
  consumed by most DB applications. All PUB LOG® data files will be updated monthly and will be
  available on the first business day of every month."* Files listed as **Last Updated 8/24/2026**.
- **Access:** direct HTTP download, **no login, no registration, no payment**.
- **Format:** ZIP → CSV, quoted fields, `\r\n` line endings, header row present.

### 1.1.1 File inventory — [VERIFIED] by HTTP Range requests + ZIP central-directory parse

Base path: `https://www.dla.mil/Portals/104/Documents/InformationOperations/LogisticsInformationServices/FOIA/PUBLOG/`
(each link on the page carries a `?ver=` query token; **re-read the page for the current token —
do not hardcode the ones below, they rotate on republish**).

| ZIP | ZIP size (bytes, verified) | Contents (verified) | Uncompressed (verified) |
|---|---|---|---|
| `IDENTIFICATION.zip` | 362,388,239 | `P_FLIS_NSN.CSV`, `V_FLIS_IDENTIFICATION.CSV`, `V_FLIS_CANCELLED_NIIN.CSV`, `V_COLLOQUIAL_NAME.CSV`, `V_FLIS_STANDARDIZATION.CSV`, `P_HELP.CSV` | 985 MB / 1.61 GB / 49 MB / 1.3 MB / 614 MB |
| `CHARACTERISTICS.zip` | 524,457,993 | `V_CHARACTERISTICS.CSV` | ≈3.37 GB |
| `FLISV.zip` | 385,014,308 | `FLISV.CSV` (coded characteristics, quarterly) | ≈2.36 GB |
| `REFERENCE.zip` | 180,204,468 | `V_FLIS_PART.CSV` | 1.28 GB |
| `H-SERIES.zip` | 14,627,973 | 15 CSVs (item-name & classification dictionaries) | see below |
| `MRD.zip` | 4,184,480 | `MRD0107/0300/0500/06P1/06P2.CSV` (attribute schema) | see below |
| `MANAGEMENT.zip` | 140,408,388 | `V_FLIS_MANAGEMENT.CSV` + per-service tables | 1.50 GB |
| `CAGE.zip`, `FREIGHT_PACKAGING.zip`, `HISTORY.zip`, `MOE_RULE.zip` | — | supplier / packaging / inactive-NSN / service-usage | — |

**Total download if you take everything: ≈1.6 GB compressed, ≈11 GB uncompressed.**
[JUDGMENT] Do **not** take everything. See §11 for the exact slice to take (≈600 MB download).

### 1.1.2 Exact column layouts — [VERIFIED] by decompressing each file's first bytes

```
P_FLIS_NSN.CSV               FSC, NIIN, INC, ITEM_NAME, SOS, END_ITEM_NAME, CANCELLED_NIIN
V_FLIS_IDENTIFICATION.CSV    NIIN, INC, PINC, CRIT_CD, II, DMIL, DMIL_INT_CD, NIIN_ASGMT, PMIC,
                             ADP, HMIC, ESD_EMI, HCC, SCHEDULE_B, ENAC, IUID_INDICATOR,
                             LST_KWN_SOS, FEDMALL
V_FLIS_STANDARDIZATION.CSV   NIIN, RELATED_NSN, ISC, ORIG_STDZN_DEC, DT_STDZN_DEC, NIIN_STAT_CD
V_COLLOQUIAL_NAME.CSV        INC, RELATED_INC, COLLOQUIAL_NAME
V_CHARACTERISTICS.CSV        NIIN, MRC, REQUIREMENTS_STATEMENT, CLEAR_TEXT_REPLY
FLISV.CSV                    NIIN, MRC, MODE_CODE, SEC_ADD_IND_CD, SAC, AND_OR, CODED_CLEAR_REPLY
V_FLIS_PART.CSV              NIIN, PART_NUMBER, CAGE_CODE, CAGE_STATUS, RNCC, RNVC, DAC, RNAAC,
                             RNFC, RNSC, RNJC, SADC, HCC, MSDS, MEDALS
P_H6_PICK.CSV                INC, ITEM_NAME, FSC, IMM
V_H6_NAME_INC.CSV            INC, INC_STATUS, CONCEPT_NO, APP_KEY, COND_CODE, TYPE_CODE,
                             DT_ESTB_CANC, DEFINITION
V_H6_MODIFIER.CSV            INC, FSC, MODIFIER, FSC_TITLE
V_H6_RELATED.CSV             INC, RELATED_INC, ITEM_NAME
V_H2_FSC.CSV                 FSC, FSC_TITLE, FSC_NOTES, FSC_INCLUSIONS, FSC_EXCLUSIONS
V_H2_FSC_INC.CSV             FSC, INC, ITEM_NAME
MRD0107.CSV                  MRC_3445, MODE_CD_4735, MRC_USG_DESI_0847, MRD_STATUS_CD_0816,
                             PRT_SKLTN_CD_0368, KEYWRD_GRP_CD_2034, KEYWRD_MOD_ST_2033,
                             RQMT_STMT_3614, RQMT_STMT_DEF_5027, RQMT_RPY_INST_2648,
                             CD_F_LGT_RPLY_0365_1..8, RPLY_TBL_MRD_8254_1..8
MRD0300.CSV                  RPLY_TBL_MRD_8254, CDD_RPLY_3465, RPLY_STAT_IND_2498, DCOD_RPLY_ST_3864
MRD0500.CSV                  INC_4080, FIIG_4065, MRC_3445, STYL_NBR_FIIG_0768, PHYS_DWG_ID_5037,
                             DCOD_STYL_RPY_2309
MRD06P1.CSV                  FIIG_4065, INC_4080, MRC_3445, RPLY_TBL_DCOD_3845
MRD06P2.CSV                  RPLY_TBL_DCOD_3845, SEC_AD_IND_CD_9485, SAC_8990, DCOD_ISAC_RPY_2308
```

### 1.1.3 Record counts

**[VERIFIED] — exact line counts obtained by fully decompressing the small files:**

| File | Data rows (header excluded) | What it is |
|---|---|---|
| `P_H6_PICK.CSV` / `V_H6_NAME_INC.CSV` | **79,883** | Approved Item Names (INC) — each with an English **definition** |
| `V_H2_FSC.CSV` | **676** | Federal Supply Classes with title, inclusions, exclusions |
| `V_H2_FSC_INC.CSV` | **6,877,262** | valid (FSC, INC) combinations |
| `V_H6_MODIFIER.CSV` | **54,604** | item-name modifiers per (INC, FSC) |
| `V_H6_RELATED.CSV` | **33,930** | INC ↔ related INC (near-synonym graph) |
| `MRD0107.CSV` | **27,552** | **MRC attribute dictionary** — attribute code → requirement statement → definition |
| `MRD0300.CSV` | **164,926** | **controlled-vocabulary reply values** for coded attributes |
| `MRD0500.CSV` | **211,397** | INC × FIIG × MRC style/skeleton rows |
| `MRD06P1.CSV` | **45,305** | **which MRCs apply to which INC** (i.e. the attribute schema per item type) |
| `MRD06P2.CSV` | **36,959** | decoded ISAC reply values |

**[VERIFIED-ESTIMATE] — large files, extrapolated from a real decompressed 8 MB sample:**

| File | Sample | bytes/row | Est. rows |
|---|---|---|---|
| `P_FLIS_NSN.CSV` | 8,010,192 B → 151,757 rows | 53 | **≈18.7 M** (active + cancelled NIINs) |
| `V_FLIS_STANDARDIZATION.CSV` | 8,064,758 B → 243,549 rows | 33 | **≈18.6 M** |
| `V_CHARACTERISTICS.CSV` | 8,059,200 B → 105,131 rows | 77 | **≈44 M** attribute assertions |
| `FLISV.CSV` | 8,007,365 B → 174,687 rows | 46 | **≈51 M** coded attribute assertions |
| `V_FLIS_PART.CSV` | not sampled | — | UNVERIFIED — count by `wc -l` after download |

[JUDGMENT] Treat the extrapolations as ±20%. **Never quote them in the SIH deck.** After download,
run `wc -l` and quote the true number.

### 1.1.4 Why this dataset is a near-perfect fit for SIH26099

The problem statement is: *many organisations, many codes, many descriptions, one physical item.*
FLIS is exactly that, at national scale, with the answer key attached.

| Brief's AI output class (§7) | Real FLIS label you can derive | Source |
|---|---|---|
| EXACT / IDENTICAL | same (CAGE, PART_NUMBER) pair | `V_FLIS_PART` |
| DUPLICATE | different (CAGE, PART_NUMBER) rows sharing one NIIN | `V_FLIS_PART` |
| NEAR-DUPLICATE | same INC, same FSC, attribute vectors differ in ≥1 MRC | `FLISV` + `MRD06P1` |
| FUNCTIONALLY EQUIVALENT | NIIN ↔ RELATED_NSN where ISC encodes a replacement decision | `V_FLIS_STANDARDIZATION` |
| DISTINCT | different INC, or same INC with conflicting key-dimension MRCs | `P_FLIS_NSN` + `FLISV` |

**Item Standardization Code (ISC) semantics** — [VERIFIED via https://www.iso-group.com/Information/ISC/ ,
a commercial FLIS reseller's reference page; **this is a secondary source**]:
`1` = approved for procurement as the formal replacement for one or more unauthorised items;
`2` = authorised procurement item included in a reduction study, not itself a replacement;
`3` = determined by standardization study as **not** authorised for procurement;
`5` = authorised, not yet subject to standardization;
`6` = authorised, unique characteristics limit elimination potential;
`7`/`8` = NATO-only codes; `B`, `C`, `E` = revised-specification / insufficient-data / superseded.
**[ASSUMPTION] the authoritative definition is DoD 4100.39-M (FLIS Procedures Manual) Vol. 10.
Verify by downloading the manual, e.g. https://apps.dtic.mil/sti/tr/pdf/ADA325591.pdf , before
you put ISC semantics on a slide.** Do not cite iso-group.com in an academic-style report.

Also directly useful:
- `V_COLLOQUIAL_NAME.CSV` (1,339,890 B) — a **real, curated alias dictionary**: colloquial name ↔ INC.
  This is exactly the "learn abbreviations / trade names" resource the brief asks for in §4, and
  you get it for free instead of hand-building it.
- `V_H6_NAME_INC.DEFINITION` — 79,883 natural-language definitions of item types. Excellent for
  (a) zero-shot classification prompts, (b) building an INC-embedding index, (c) explanation text.
- `V_H2_FSC.FSC_INCLUSIONS / FSC_EXCLUSIONS` — human-written scope rules per class. Rare and valuable.

### 1.1.5 Licence / terms

- **[VERIFIED]** The files are published in a **FOIA Electronic Reading Room** by a US federal agency,
  free, with no click-through licence and no registration.
- **[JUDGMENT]** Works of the US federal government are not subject to domestic copyright
  (17 U.S.C. §105), and FOIA reading-room material is released for public use. For an Indian
  student research prototype this is about as clean as data gets.
- **[VERIFIED CAVEAT]** The page carries a notice: *"Beginning April 1, 2026, the following fields
  will no longer be distributed in FED LOG or PUB LOG®: FIIG, FIIG_TITLE, DELT_RSN_CD, ACTY_CD,
  QNTV_EXPRSN, SUPP_RCVR, AUTH_RCVR, SUBMTR, and NATO_FMSN."* → **FIIG is being removed from the
  live extracts.** `MRD0500`/`MRD06P1` still carry `FIIG_4065` today (files dated 6/4/2026), but
  **do not architect a hard dependency on FIIG**. Key everything on **INC**, which is not affected.
- **[VERIFIED CAVEAT]** The page also states the hard-copy version prevails over the electronic one.
  Irrelevant for ML, relevant if you ever claim authoritativeness.

### 1.1.6 Effort to use — [JUDGMENT]

**Low-to-moderate. ~2 engineer-days to a queryable local corpus.**
- Download ≈600 MB (recommended slice), unzip, `COPY` into Postgres with explicit `text` columns.
- The two multi-GB files (`V_CHARACTERISTICS`, `FLISV`) should be **filtered on the fly while
  streaming** to only the NIINs in your chosen FSCs — never load them whole.
- Watch out: leading-zero NIINs (`000000042`) must stay `text`, never `int`.
- `V_CHARACTERISTICS.CSV` is ≈3.4 GB; `zcat | awk` filtering is fine, Pandas `read_csv` whole-file is not.

### 1.1.7 ⚠ Download blocker you WILL hit — [VERIFIED]

From this research environment, `curl`/server-side fetchers received **HTTP 403** from
`www.dla.mil` for both the HTML page and the ZIPs, while a real browser session downloaded them
fine (I verified byte sizes over `fetch()` inside a live browser page on the dla.mil origin).
**[JUDGMENT] dla.mil sits behind a WAF that fingerprints non-browser clients.**

Mitigations, in order:
1. Download **manually in a normal desktop browser** from India and keep the ZIPs. It's a
   one-time 600 MB–1.6 GB action. **Do this in week 1 and archive the ZIPs — do not build a
   pipeline that re-fetches from dla.mil at demo time.**
2. If scripted fetch is needed, use a real browser automation (Playwright) with a genuine UA,
   or `curl` with full browser header set — **[ASSUMPTION], test it**.
3. **Never** let the live demo depend on a network call to dla.mil.

### 1.1.8 VERDICT: **USE — PRIMARY SOURCE, RANK 1.**

---

## 1.2 Other NSN routes (for completeness)

| Source | Status | Verdict |
|---|---|---|
| **WebFLIS** (https://www.dla.mil/Information-Operations/Services/Applications/WebFLIS/) | Interactive single-item query UI, not bulk. | **REJECT** — no bulk export; use PUB LOG instead. |
| **FED LOG** | [VERIFIED via DLA page text] Free but distributed **via FedMall to authorised DoD / DoD-sponsored customers**. Not open to an Indian student team. | **REJECT** — access restricted. |
| **PUB LOG DVD** | [VERIFIED via DLA search snippets] Portable-media subscription product. Superseded for our purposes by the free CSV reading room. | **REJECT** — unnecessary. |
| **GSA "National Stock Number Extract"** (data.gov) https://catalog.data.gov/dataset/national-stock-number-extract | **[VERIFIED — I downloaded it, 989,217 bytes XLSX, 12,454 data rows.]** Columns: `NSN, rep_office, common_name, Description, Price, UI, AAC`. Licence stated as **CC0**. Descriptions are real vendor prose, e.g. *"Nickel-coated copper alloy safety pin with blunt point is designed specifically for closing laundry bags."* Metadata says last updated **2017** — it is stale. | **USE — SMALL BUT REAL.** 12.4k real commercial-style descriptions already keyed to NSN. This is your only real, free bridge between NSN identity and *commercial marketing prose*. Perfect as a held-out realism test set. |
| **nsncenter.com** | **[VERIFIED-ish]** Crunchbase lists NSN Center as **permanently closed**. UNVERIFIED whether the site still serves data — check by loading https://www.nsncenter.com . | **REJECT** — dead/unreliable; also a reseller, ToS would forbid bulk reuse. |
| **iso-group.com, OpenFLIS, Niinja, ParttTarget, LogTool** | Commercial FLIS resellers with paid APIs. They repackage the same public data you can get free. | **REJECT** for data. **Reference-only** for code-table documentation (and cite them as secondary, not authoritative). |
| **NSPA NMCRL** (NATO Master Catalogue of References for Logistics) | UNVERIFIED — believed to be a paid subscription product. Verify at https://www.nspa.nato.int/ . | **REJECT** unless verified free. |

---

## 1.3 The Indian angle you should absolutely use — [VERIFIED]

India's **Directorate of Standardisation (DDP, Ministry of Defence)** is **India's National
Codification Bureau** and operates the NATO Codification System domestically.
- https://ddpdos.gov.in/ncb-india/overview
- https://ddpdos.gov.in/ncb-india/nato-codification/codification-system
- https://ddpdos.gov.in/ncb-india/nato-codification/nsn
- [VERIFIED from search-result content] the Directorate signed an agreement with **AC/135**
  (the apex body of the NATO Codification System) on **10 Jun 2008**, making India a member.
- **[VERIFIED via WebFetch of the overview page]** the site itself lists standardization documents
  (JSS/JSG/JSPR/JSRL) but the NCB detail page reads *"To be uploaded"* — **there is no public
  downloadable Indian item catalogue here.**

**[JUDGMENT] This is a strategic gift for the presentation.** It converts "we trained on an
American dataset" into: *"We train on the world's largest publicly released codified item
catalogue, built on the very NATO Codification System that India's own National Codification
Bureau adopted in 2008. Our canonical item model is FSC + Approved Item Name + MRC attributes —
the same conceptual model an Indian CPSE material master would migrate toward."*
That is defensible, true, and much stronger than a hand-waved synthetic dataset.

**[ASSUMPTION]** India's NCB code within NSN is believed to be **26**, which would make Indian-origin
NSNs look like `XXXX-26-XXX-XXXX`. **Verify at https://ddpdos.gov.in/ncb-india/nato-codification/nsn
before stating it.** Do not put it on a slide unverified.

---

# 2. GeM (Government e-Marketplace) — **REJECT**

- **URLs:** https://gem.gov.in/ , https://mkp.gem.gov.in/market , https://bidplus.gem.gov.in/
- **Content:** millions of product listings across thousands of Indian procurement categories.
  On paper, the single most relevant corpus in existence for this problem.
- **Open data / API:** **none found.** No GeM dataset on data.gov.in, no documented public API.
- **Legal position — [VERIFIED, decisive]:** GeM's own Website Policies state:
  *"Contents of this website may not be reproduced partially or fully without due permission in
  writing in advance from the GeM SPV."* and *"framing or deep-linking of GeM web pages or content
  is not allowed."* Source: https://gem.gov.in/websitePolicies
- `robots.txt` — **[VERIFIED]** `gem.gov.in/robots.txt` is permissive (`User-agent: * / Disallow:`
  with only `/cgi-bin/` and `/resources/` blocked); `bidplus.gem.gov.in/robots.txt` blocks
  `/resources/` and some EMD/PBG endpoints. **[JUDGMENT] A permissive robots.txt does NOT override
  an explicit copyright clause forbidding reproduction.** Commercial "GeM scraper" products exist
  on Apify etc.; their existence is not a legal opinion.
- **[JUDGMENT] VERDICT: REJECT for data collection.** Scraping GeM and then presenting the result
  to a panel that includes Government of India procurement officials is a catastrophic own-goal.
  A judge asking *"whose data is that?"* ends your presentation.
- **How to still use GeM honestly:** cite it as the **integration target** and the **motivation**
  ("harmonized codes would let GeM aggregate demand across CPSEs"). Use publicly stated,
  attributable GeM statistics from press releases if you need scale numbers — and attribute them.

---

# 3. data.gov.in / NDSAP — **REJECT as training data**

- **Portal:** https://www.data.gov.in/ ; **Licence:** Government Open Data Licence – India (GODL),
  https://www.data.gov.in/Godl — [VERIFIED via search content] grants a worldwide, royalty-free,
  non-exclusive licence to use, adapt, publish and create derivative works for lawful commercial
  and non-commercial purposes, **conditional on explicit attribution** (provider, source, licence,
  DOI/URL). Excellent licence. **Nothing useful under it.**
- **[VERIFIED by running searches on the live portal 2026-08-26]:**
  - query `material code` → All India Pincode Directory, IPC cognizable-offence tables, hospital
    directories, ITC(HS) import-export classification, "Census houses by predominant material of roof".
  - query `procurement` → paddy procurement centres, "Assam Public Procurement Data 2016-17",
    Rajya Sabha answer tables on defence procurement share. **All aggregate statistics.
    Zero item-level material descriptions.**
- The one mildly interesting item: **ITC(HS) code and Import Policy** — a real Indian
  goods-classification hierarchy with descriptions. **[JUDGMENT] Useful as a *third* classification
  taxonomy to demonstrate cross-standard mapping (FSC ↔ UNSPSC ↔ ITC-HS), not as material data.**
- **VERDICT: REJECT for training. BACKUP (ITC-HS only) for taxonomy-crosswalk demo.
  USE the GODL attribution wording as a model for your own data-provenance page.**

---

# 4. CPSE tenders / BOQs (CPPP, IREPS) — **REJECT as a pipeline; BACKUP as a tiny hand-curated set**

- **CPPP / eprocure.gov.in** — https://eprocure.gov.in/eprocure/app , https://eprocure.gov.in/cppp/
- **[VERIFIED 2026-08-26]** The Central "Active Tenders" search page displays:
  *"Enter Captcha … Provide Captcha and click on Search button to list all active tenders."*
  **The tender listing is CAPTCHA-gated.**
- **[VERIFIED]** The public organisation dropdown does contain exactly the CPSEs the problem
  statement is about — BHEL, BPCL, BSNL, BEML, Bharat Coking Coal, Bharat Electronics, and so on.
  So the *content* is right; the *access path* is wrong.
- **IREPS (Indian Railways)** — https://www.ireps.gov.in/ireps.html — **[VERIFIED]** exposes
  anonymous entry points `Search E-Tenders` and `Supply Contracts` (`anonymSearchPO()`), i.e. some
  public purchase-order search exists. **[ASSUMPTION]** those results include item description +
  **PL No.** (the Indian Railways 8-digit semi-significant stores code, 76 major groups —
  [VERIFIED as a described system via railnewscenter.com, a secondary source; verify against an
  official Indian Railways Stores Code document]). **Check by manually running one anonymous
  Supply Contracts search and looking at the columns.**
- **Legal/ethical:** [JUDGMENT] Defeating a CAPTCHA to bulk-harvest a government portal is
  unacceptable — technically, ethically, and in front of SIH judges. Rate-limited automated
  harvesting of a CAPTCHA-protected government site is not something you can defend on stage.
- **VERDICT: REJECT as an automated data source.**
  **BACKUP (and genuinely valuable):** have 2 team members **manually** open ~30–60 real CPSE
  stores/BOQ tender documents, and hand-copy **200–500 real Indian material description lines**
  into a CSV. Purpose is **not** training. Purpose is:
  1. To **calibrate the synthetic noise generator** against real Indian description style
     (real abbreviation frequencies, real unit spellings "MM"/"mm"/"m.m", real ordering,
     real vendor/make suffixes, real Hindi/transliterated tokens).
  2. To serve as a small **REAL held-out realism check** in the evaluation section.
  3. To let you say on stage, truthfully: *"we validated our variant generator against real
     Indian CPSE tender line items."* That single sentence defuses the biggest judge objection.
  Effort: ~1 person-day. Payoff: disproportionate.
  Record for each line: source org, tender ID, date, URL, raw text. Keep provenance.

---

# 5. Classification standards — UNSPSC / eCl@ss / eOTD

## 5.1 UNSPSC — **USE (with a warning)**

- **⚠ [VERIFIED, IMPORTANT] `https://www.unspsc.org/` is no longer the UNSPSC site.**
  On 2026-08-26 both WebFetch and a live browser load of `https://www.unspsc.org/codeset-downloads`
  returned a page titled **"List of Sweepstakes Casinos in the USA 2026"**. The domain appears to
  have lapsed and been re-registered. **Do not link unspsc.org in your report or your code.**
- **Working alternative — [VERIFIED, I downloaded it]:**
  **UNGM UNSPSC export.** Page: https://www.ungm.org/public/unspsc ;
  file: **https://www.ungm.org/Public/UNSPSC/Excel**
  → HTTP 200, 469,231 bytes, XLSX, **13,335 rows**, columns `Key, Parent key, Code, Title`.
  10 top-level segment letters + **13,325 eight-digit UNSPSC codes** with English titles and an
  explicit parent-key hierarchy (segment → family → class → commodity).
- **Licence — mixed:** [VERIFIED via search content] UNSPSC is described as free to use and
  embeddable, with **commercial** embedding requiring an addendum to terms; non-subscribers get
  a free PDF/browse, Excel historically sold. UNGM (a UN entity) publishes the Excel export openly.
  **[JUDGMENT] Using the codeset internally in a non-commercial student prototype is fine.
  Do NOT redistribute the XLSX file in your GitHub repo — reference the UNGM URL instead.**
- **[JUDGMENT] Use for:** the "map any CPSE category to an international standard taxonomy" feature,
  and to demonstrate multi-standard crosswalk (FSC ↔ UNSPSC). It has **no attributes**, so it is
  useless for specification-aware matching. Do not oversell it.
- **VERDICT: USE (taxonomy only). Do not redistribute the file.**

## 5.2 eCl@ss — **REJECT**

- https://eclass.eu/ . [VERIFIED] `https://eclass.eu/en/eclass-standard/download` returns HTTP 404,
  so I could not confirm current terms. Search evidence indicates the historically free download
  is no longer free and that ECLASS e.V. operates a membership/licence model.
- **[JUDGMENT] REJECT.** eCl@ss has the best property/attribute model of any commercial standard
  (which is exactly what you'd want), but licensing risk is real and the team cannot afford a
  procurement negotiation inside 6–10 weeks. FLIS MRC gives you the same capability for free.
- **UNVERIFIED — verify current terms at https://eclass.eu/ if anyone insists.**

## 5.3 ECCMA eOTD (ISO 22745) — **BACKUP, verify first**

- https://www.eotd.org/ (search UI) ; https://eccma.org/eotd-eccma-open-technical-dictionary/
- Described as a **free-to-use ISO 22745-compliant open technical dictionary** of cataloguing
  concepts (item names, properties, values, in multiple languages), historically derived from the
  NATO Codification System.
- **[VERIFIED]** The eotd.org page I fetched exposes only a search interface. **I could not find a
  bulk download or a stated licence.**
- **VERDICT: BACKUP.** Verify by (a) reading https://www.eotd.org/assets/docs/eOTD_User_Manual_Final.html,
  (b) emailing ECCMA for a bulk export and licence statement. **Do not build on it.**
  Its main content overlaps FLIS INC/MRC, which you already have unconditionally.

---

# 6. Open entity/product-matching benchmarks — **USE. THIS IS YOUR CREDIBILITY.**

These come **with ground-truth labels and published baseline scores**, which means you can report
**real, comparable, non-fabricated metrics in week 3** — before any domain data exists. Judges and
(more importantly) any ML-literate evaluator will take this far more seriously than a self-graded
number on your own synthetic set.

## 6.1 DeepMatcher / Magellan benchmark suite — **[VERIFIED all URLs live 2026-08-26]**

Index: https://github.com/anhaidgroup/deepmatcher/blob/master/Datasets.md

| Dataset | Domain | Labelled pairs | Positives | Download (HTTP 200 verified) |
|---|---|---|---|---|
| Walmart-Amazon (Structured) | electronics | 10,242 | 962 | `.../Structured/Walmart-Amazon/walmart_amazon_exp_data.zip` (1,007,282 B) |
| Amazon-Google (Structured) | software | 11,460 | 1,167 | `.../Structured/Amazon-Google/amazon_google_exp_data.zip` (146,540 B) |
| Abt-Buy (Textual) | product | 9,575 | 1,028 | `.../Textual/Abt-Buy/abt_buy_exp_data.zip` (147,291 B) |
| DBLP-Scholar | citation | 28,707 | 5,347 | `.../Structured/DBLP-GoogleScholar/dblp_scholar_exp_data.zip` |
| DBLP-ACM | citation | 12,363 | 2,220 | `.../Structured/DBLP-ACM/dblp_acm_exp_data.zip` |
| Company | company | 112,632 | 28,200 | `.../Textual/Company/company_exp_data.zip` |
| iTunes-Amazon, Fodors-Zagats, BeerAdvo-RateBeer | misc | 450–946 | — | see index |
| **Dirty** variants of iTunes-Amazon, DBLP-ACM, DBLP-Scholar, Walmart-Amazon | — | same sizes | — | `.../Dirty/...` |

Host prefix: `http://pages.cs.wisc.edu/~anhai/data1/deepmatcher_data/`
- **Licence:** **[VERIFIED] no explicit licence is stated in the index.** [JUDGMENT] These are the
  de-facto academic EM benchmarks, used in dozens of published papers (Ditto, Magellan, DeepMatcher).
  Research use with citation is normal and accepted. **Cite the papers, don't republish the files.**
- **[JUDGMENT] Why they matter to you:** the **Dirty** variants specifically model attribute-value
  injection/misplacement — the closest public analogue to messy ERP material masters.
  Reporting your model's F1 on Dirty/Walmart-Amazon next to published Ditto/DeepMatcher numbers is
  the single cheapest way to prove your matcher is a real matcher.

## 6.2 WDC Products — **USE**

- https://webdatacommons.org/largescaleproductcorpus/wdc-products/ ; code + build:
  https://github.com/wbsg-uni-mannheim/wdcproducts ; paper: https://arxiv.org/abs/2301.09521 (EDBT 2024)
- **Content [VERIFIED via the WDC page]:** 11,715 product offers describing **2,162 product entities**
  from 3,259 e-shops using schema.org markup; attributes `title, description, price, priceCurrency, brand`.
  **27 benchmark variants** crossing three dimensions: share of corner cases (80/50/20%), share of
  unseen entities in test (0/50/100%), and training-set size. Both **pair-wise and multi-class**
  formulations of the same task.
- **Downloads [VERIFIED — `80pair.zip` returned HTTP 200, 21,985,075 bytes]:**
  `https://data.dws.informatik.uni-mannheim.de/largescaleproductcorpus/data/wdc-products/`
  → `80pair.zip` (21.5 MB), `50pair.zip` (21.6 MB), `20pair.zip` (20 MB), `80multi.zip` (2.4 MB),
  `50multi.zip`, `20multi.zip`; plus `wdcproducts_corpus_with_url.json.gz` (**4.3 GB** — skip it).
- **Licence:** **[VERIFIED] none stated on the page**; the page directs licence questions to the
  Web Data Commons Google Group. [JUDGMENT] Research use with citation is the norm for WDC.
- **[JUDGMENT] Why it matters most:** the **"unseen entities in test"** dimension is *exactly* your
  real deployment condition — a new CPSE uploads materials your model has never seen. If you report
  performance on the 100%-unseen variant, you have empirically answered the hardest technical
  question a judge can ask. **This is the most strategically valuable benchmark for you.**
- **VERDICT: USE — headline benchmark.**

## 6.3 PriceRunner product matching (Lakritidis) — **USE**

- HF: https://huggingface.co/datasets/lakritidis/product-matching
  Kaggle mirror: https://www.kaggle.com/datasets/lakritidis/product-clustering-matching-classification
- **[VERIFIED via HF API]** licence tag **`gpl`**; description: **35,311 products from 10 categories,
  306 vendors**, from PriceRunner, with product IDs, titles and categories; explicitly framed as
  "ideal ground for evaluating product matching algorithms and clustering/classification models".
  Kaggle listing: 22,794,103 bytes, licence "GPL 2".
- **[JUDGMENT] Structurally the closest public analogue to your problem:** *many vendors' messy titles
  → one canonical product cluster → a category*. It is a three-in-one: **clustering + matching +
  classification** ground truth, which mirrors your pipeline exactly (retrieve → match → classify).
- **VERDICT: USE — secondary benchmark, and a good sanity check for your clustering/canonicalisation step.**

## 6.4 Alaska / DI2KG — **BACKUP, host currently unreachable**

- Paper: https://arxiv.org/pdf/2101.11259 ("Alaska: A Flexible Benchmark for Data Integration Tasks").
  Content per the paper/search: `alaska_cameras` ≈ **29.8K specification records** scraped from
  e-commerce sites, plus monitors; supports **entity resolution AND schema matching** with
  attribute-level ground truth.
- **[VERIFIED FAILURE]** `http://di2kg.inf.uniroma3.it/datasets.html` — **DNS resolution failed
  (ENOTFOUND) on 2026-08-26.** The host may be retired.
- **[JUDGMENT]** Alaska is the *most conceptually similar* benchmark to your problem — real products
  described by heterogeneous sources with heterogeneous attribute schemas, i.e. exactly the "attribute
  ordering and naming differ across CPSEs" issue. Worth 30 minutes to chase.
  **Verify by:** searching Zenodo / the SIGMOD Programming Contest 2020–2022 archives / emailing the
  authors. **Do not plan around it.**
- **VERDICT: BACKUP.**

## 6.5 Other benchmarks — noted, lower priority

- **Machamp** (generalized EM benchmark), https://arxiv.org/pdf/2106.08455 — UNVERIFIED availability.
- **MWPD / SWC product matching challenges** — UNVERIFIED availability; largely superseded by WDC Products.
- **Amazon ESCI Shopping Queries** — https://github.com/amazon-science/esci-data ,
  **[VERIFIED via GitHub API: Apache-2.0, 389 stars]**. It is *query→product relevance*, not
  product↔product matching. **[JUDGMENT] Not a fit for your matcher; it IS a fit if you want to
  demonstrate the "intelligent search" feature (§20 of the brief) on real data.** Optional.

---

# 7. Industrial / MRO catalogues — **REJECT (all commercial ones)**

| Source | Finding | Verdict |
|---|---|---|
| **McMaster-Carr** | **[VERIFIED]** `https://www.mcmaster.com/robots.txt` explicitly contains `Disallow: /catalog/*`, `Disallow: /Catalog/*`, `Disallow: /*/SpecSrch.aspx`, `Disallow: /*/ProdPageWebPart/ProdPageWebPart.aspx`, `Disallow: /*/WebSrchEng.aspx`, `Disallow: /*/pdf`. The catalogue and search are **explicitly off-limits to crawlers**. | **REJECT — unambiguous.** |
| **Grainger** | **[VERIFIED]** `https://www.grainger.com/robots.txt` returned a custom 404 page ("Whoops, we couldn't find that."). No permission granted by absence; commercial ToS applies. | **REJECT.** |
| **Fastenal** | **[VERIFIED]** `https://www.fastenal.com/robots.txt` → **Access Denied** (Akamai edge block). Bot traffic is actively blocked. | **REJECT.** |
| **RS Components (in.rsdelivers.com), Misumi (in.misumi-ec.com)** | **[VERIFIED]** both returned empty robots.txt responses to my request. Commercial catalogues, standard ToS. | **REJECT.** |
| **IndiaMART** | **[VERIFIED]** `https://www.indiamart.com/robots.txt` disallows `/pd/`, `/proddetail1`, `/proddetail2`, `/company/<letter>/`, `/mdc/` and more — i.e. **the product-detail paths are disallowed**. | **REJECT.** |

**[JUDGMENT]** Scraping a commercial MRO catalogue would give you beautiful attribute-rich data and
would be indefensible. It also creates a demo-day failure mode (site blocks you the morning of).
Do not do it. Everything you would gain, FLIS + BOLTS already give you legally.

## 7.1 Open engineering / standard-parts data — **USE**

### BOLTS (Open Library of Technical Specifications) — **USE**
- Repo: https://github.com/boltsparts/BOLTS_archive — **[VERIFIED via GitHub API: 293 stars,
  licence GPL-3.0 on the repo, last push 2023-05-01]**. The **data files themselves carry an explicit
  header: `license: LGPL 2.1+ <http://www.gnu.org/licenses/lgpl-2.1>`** [VERIFIED by reading
  `data/hex.blt` and `data/bearings.blt`].
- **Contents [VERIFIED — 21 files in `/data`]:** `hex.blt` (23,099 B), `hex_socket.blt` (18,922 B),
  `nut.blt` (18,075 B), `washer.blt` (12,863 B), `bearings.blt` (29,851 B), `flanges.blt` (7,201 B),
  `pipes.blt` (10,164 B), `extrusions.blt` (8,568 B), `profile_i/c/l/z/hollow.blt`,
  `connecting_bars.blt`, `vacuum.blt`, `batteries.blt`.
- **Structure [VERIFIED]:** YAML. Each class carries a **standard body + standard number**
  (e.g. `body: DIN`, `standard: DIN 933`), a **canonical naming template**
  (`nice: Hexagon head screw DIN 933 %(key)s%(pitch_name)s - %(l)s`), a **typed parameter schema**
  with units and human descriptions (`d1: threaded shaft diameter`, `k: head length`,
  `s: width across flats`, `e: head diameter`, `pitch: thread pitch`), and **enumerated valid
  value tables** (`[[M3], [8,10,12,14,16,18,20,22,25], ["coarse","fine I"]]`).
- **[JUDGMENT] This is the perfect synthetic-generation seed and it is legally clean.** It gives you,
  for free: a canonical name template, a standard reference, a typed attribute schema with units,
  and the *legal* value combinations — so every synthetic canonical item you generate is a real
  engineering part that actually exists, not a hallucination.
- **Yield [JUDGMENT/ASSUMPTION]:** across hex screws/socket screws/nuts/washers/bearings/flanges/
  pipes/profiles, the enumerated (size × length × standard × variant) product plausibly yields
  **20,000–60,000 distinct valid canonical items**. **Verify by parsing the .blt files and counting
  the Cartesian product** — that is a 2-hour task and you should do it in week 1 before committing.
- **Licence obligation:** LGPL-2.1+ on the data. [JUDGMENT] Using it to *generate* a derived dataset
  is fine for a prototype; **attribute BOLTS explicitly** in your data-provenance section.
- **VERDICT: USE — primary synthetic seed for the fastener/pipe/bearing demo categories.**

### FreeCAD Fasteners Workbench — **BACKUP**
- https://github.com/shaise/FreeCAD_FastenersWB — **[VERIFIED: GPL-2.0, 411 stars, actively
  maintained (last push 2026-08-07)]**. Contains `screw_maker.py` (40,950 B), `ScrewMaker.py`,
  `FSScrewCalc.py` with embedded ISO/DIN/ANSI dimension tables.
- **[JUDGMENT]** Broader standard coverage than BOLTS and still maintained, but the tables are
  embedded in Python source rather than a clean data format → higher extraction effort.
- **VERDICT: BACKUP — use if BOLTS' coverage proves too narrow.**

### Wikidata / DBpedia / OpenStreetMap — **REJECT for this problem**
- **[JUDGMENT]** Wikidata has excellent coverage of *notable* entities and almost none of
  *industrial commodity items* (there is no Wikidata item for "SS 304 hex bolt M10×50"). OSM is
  geospatial. **Not worth the effort.** UNVERIFIED as a matter of exhaustive search — if someone
  insists, check by running a SPARQL query on query.wikidata.org for instances of `screw (Q13580)`
  and see how few there are.

### GS1 sample data — **REJECT / UNVERIFIED**
- GS1 GDSN sample files exist per member organisation but are small, scattered, and licence-unclear.
  **[JUDGMENT] Not worth the search cost within a 6–10 week budget.**

---

# 8. Kaggle / Hugging Face — **mostly REJECT; two useful items**

I queried both platform APIs directly on 2026-08-26.

**[VERIFIED — HF dataset search API results]** for `product matching`, `entity matching`,
`maintenance work order`, `spare parts`, `material master`, `product titles`, `ecommerce catalog`:
the only substantive hits were `lakritidis/product-matching` (see §6.3),
`lighteval/EntityMatching`, `zidcenek/GLAMI-Entity-Matching-Dataset`, `deepakkumar07/spare-parts-ner`,
and a cluster of `qazisaad/llama_2_product_titles-esci*` derivative sets.
**`material master` returned ZERO results.**

**[VERIFIED — Kaggle dataset list API]**: `product matching` → the same Lakritidis/PriceRunner set
(GPL 2, 22.8 MB). `spare parts` → "Vehicle Spare Parts Index" (543 bytes — a price index, useless).
`material master` → nothing relevant. `maintenance work orders` → `tinhban/maintenance-work-orders-dataset`
(231,056 B, licence "Other (specified in description)", usability rating 0.35 — **low quality, licence
unclear → REJECT**).

**[JUDGMENT] Conclusion: there is no public "material master" dataset. Stop looking for one.**
This is itself a finding worth stating in the SIH deck — it is *why* the problem is hard and *why*
your synthetic-from-real-identity strategy is the correct engineering answer, not a shortcut.

## 8.1 MaintIE — **USE (small but uniquely relevant)**
- https://github.com/nlp-tlp/maintie — **[VERIFIED via GitHub API: licence MIT, 22 stars,
  last push 2024-06-29]**. Data files present: `data/gold_release.json` (817,880 B),
  `data/silver_release.json` (4,607,249 B), `data/scheme.json` (134,144 B).
- **Content [VERIFIED via search content]:** a fine-grained annotated corpus of **1,076 gold** +
  **~7,000 coarse/silver** real **maintenance work-order short texts**, with an entity/relation
  annotation scheme (physical object, activity, state, property).
- **[JUDGMENT] Why it matters:** this is the **only real, openly licensed corpus of genuinely terse,
  abbreviated, industrial free-text** I found. MWO text ("repl pmp brg", "chg out v/v seal") has the
  same pathologies as CPSE material descriptions: heavy abbreviation, no grammar, inconsistent units,
  domain jargon. Use it to (a) mine a real abbreviation/expansion distribution, (b) sanity-check that
  your normalizer handles real industrial noise, (c) cite as evidence that your noise model is
  empirically grounded rather than invented.
- **Caveat [JUDGMENT]:** it is *maintenance activity* text, not *material description* text. Do not
  claim it is a material master. Use it for the noise model only.
- **VERDICT: USE — for abbreviation mining and noise-model calibration. MIT licence, no friction.**

---

# 9. SYNTHETIC GENERATION FROM STANDARDS — **USE, but only in the right role**

## 9.1 The honest scientific position

**[JUDGMENT] Synthetic data is defensible if and only if the *identity* is real and only the
*surface form* is synthetic.** The distinction matters enormously:

- ❌ **Indefensible:** invent items, invent which pairs match, train, report 97% F1.
  The model has only learned your generator. Any competent evaluator will say so, and they will be right.
- ✅ **Defensible:** take a **real canonical item** with a **real code, real classification and real
  attribute values** (from FLIS or BOLTS); apply a **surface-form transformation** that provably
  preserves identity (abbreviate, reorder, change unit spelling, drop a redundant token); the pair is
  a positive **because the underlying entity is provably the same**, not because you asserted it.
  Hard negatives come from **real neighbouring items in the same real catalogue** with one real
  attribute changed.

That second framing is standard practice — it is exactly the augmentation logic behind supervised
contrastive product matching (see e.g. https://arxiv.org/pdf/2202.02098). You are not doing anything
unusual; you are doing what the literature does.

## 9.2 The one thing that makes it rigorous — [JUDGMENT, and this is the key recommendation]

**Never let the same generator produce both your training data and your test data.**

Concretely:
- **Train / val**: synthetic variants from generator G1 (rule-based abbreviation, unit, ordering,
  separator, spelling transforms), seeded from FLIS/BOLTS canonical items.
- **Test set A (surface-shift)**: variants from a *deliberately different* generator G2 — e.g. an LLM
  asked to rewrite each canonical item as an Indian CPSE storekeeper would, with **no overlap** in
  transformation rules, and with **entity-disjoint** items (no canonical item appears in both splits).
- **Test set B (100% REAL, no synthesis at all)**: the real `V_FLIS_PART` multi-part-number groups
  and the real `V_FLIS_STANDARDIZATION` ISC replacement pairs. Real text, real labels, zero synthesis.
- **Test set C (real Indian realism)**: the 200–500 hand-collected CPSE tender description lines from §4,
  hand-labelled by the team against the canonical set.
- **Test set D (external)**: WDC Products (100%-unseen variant), Abt-Buy, Walmart-Amazon-Dirty, PriceRunner.

**Report all four separately, always.** A single blended headline number is the fastest way to lose
credibility with a technical judge. Four honest numbers beat one impressive one.

## 9.3 Hard-negative generation, grounded in real data

The brief (§6) correctly demands hard negatives. Ground them in the catalogue rather than inventing them:

| Negative type | How to mine it from REAL data |
|---|---|
| One dimension differs (M10×50 vs M10×75) | Same INC, same FSC; `FLISV` coded replies differ in exactly one *dimensional* MRC |
| Material differs (SS vs CS bolt) | Same INC; differs only on the material MRC (`MRD0300` gives the legal material vocabulary) |
| Wrong item type (bolt vs nut) | Different INC within the same FSC — e.g. FSC 5306 vs 5310 |
| Near-synonym trap | INC pairs listed in `V_H6_RELATED.CSV` (33,930 real near-synonym links) — these are the pairs *humans* find confusable, so they are perfect hard negatives |
| Same name, different class | Same `ITEM_NAME` string appearing under two different FSCs in `V_H2_FSC_INC.CSV` |

**[JUDGMENT] `V_H6_RELATED.CSV` is a hidden gem: 33,930 pairs of item names that a national
codification authority thought were confusable enough to cross-reference. That is a curated hard-negative
mine you could not buy.**

## 9.4 Where an LLM belongs in generation (and where it does not)

- ✅ **Use an LLM to generate surface variants** of a canonical item (Test set A / G2), because the
  identity is fixed by construction and the LLM only rewords.
- ✅ **Use an LLM to propose abbreviation candidates** which you then *validate* against MaintIE and
  against your hand-collected CPSE lines.
- ❌ **Do NOT use an LLM to decide whether two items match** to create training labels. That is
  label-laundering: your model then learns the LLM's errors and your metrics measure agreement with a
  language model, not correctness. If a judge asks "where did your labels come from?", "an LLM said so"
  is a losing answer; "the US DLA's Item Standardization Code" is a winning one.

## 9.5 VERDICT: **USE — as the surface-form layer only. Identity and labels must come from real catalogues.**

---

# 10. QUICK-REFERENCE VERDICT TABLE

| # | Source | Real? | Downloadable now? | Licence | Verdict |
|---|---|---|---|---|---|
| 1 | **DLA PUB LOG / FLIS CSVs** | REAL | ✅ VERIFIED (browser; WAF blocks curl) | US federal FOIA release, effectively public domain | **USE — RANK 1** |
| 2 | **GSA NSN Extract (data.gov)** | REAL | ✅ VERIFIED downloaded (989 KB, 12,454 rows) | CC0 | **USE — RANK 4** |
| 3 | **BOLTS_archive .blt files** | REAL specs | ✅ VERIFIED (GitHub raw) | LGPL-2.1+ (data) | **USE — RANK 2** |
| 4 | **WDC Products** | REAL | ✅ VERIFIED (80pair.zip 21.9 MB) | unstated; academic norm | **USE — RANK 3** |
| 5 | **DeepMatcher suite** | REAL | ✅ VERIFIED (3 URLs, HTTP 200) | unstated; academic norm | **USE — RANK 3** |
| 6 | **PriceRunner / lakritidis** | REAL | ✅ VERIFIED via HF+Kaggle API | GPL-2 | **USE — RANK 5** |
| 7 | **MaintIE** | REAL | ✅ VERIFIED (GitHub, files present) | MIT | **USE — RANK 6** |
| 8 | **UNSPSC via UNGM** | REAL | ✅ VERIFIED downloaded (13,335 rows) | free to use; don't redistribute | **USE — RANK 7 (taxonomy only)** |
| 9 | Hand-collected CPSE tender lines | REAL | manual only | public docs, cite source | **USE — RANK 8 (200–500 lines, manual)** |
| 10 | Alaska / DI2KG | REAL | ❌ host DNS failed | unknown | **BACKUP** |
| 11 | ECCMA eOTD | REAL | ❓ no bulk export found | unknown | **BACKUP** |
| 12 | ITC(HS) on data.gov.in | REAL | ✅ | GODL-India | **BACKUP (crosswalk demo only)** |
| 13 | data.gov.in (material/procurement) | REAL | ✅ | GODL-India | **REJECT — no item-level data exists** |
| 14 | **GeM** | REAL | — | **"may not be reproduced… without permission in writing"** | **REJECT — legal** |
| 15 | **CPPP / eprocure** | REAL | CAPTCHA-gated | — | **REJECT as pipeline** |
| 16 | eCl@ss | REAL | ❌ 404; paid model | restrictive | **REJECT** |
| 17 | McMaster / Grainger / Fastenal / RS / Misumi / IndiaMART | REAL | robots.txt blocks / edge-blocks | commercial ToS | **REJECT** |
| 18 | FED LOG, PUB LOG DVD, NMCRL, nsncenter, OpenFLIS/Niinja | REAL | restricted / paid / dead | — | **REJECT** |
| 19 | Wikidata / DBpedia / OSM / GS1 samples | REAL | ✅ | open | **REJECT — no coverage** |
| 20 | Random Kaggle/HF "spare parts" sets | mixed | ✅ | mixed/unclear | **REJECT — junk** |

---

# 11. THE DATA ACQUISITION PLAN (ranked, costed, concrete)

## Step 0 — Choose the demo scope FIRST (½ day, week 1)

**[JUDGMENT] Do not download 11 GB and then decide what to do with it.** Pick 6–10 Federal Supply
Classes that (a) exist in every CPSE store, (b) have rich dimensional attributes, and (c) demo well.

Recommended FSC slice:
```
FSG 53 Hardware & Abrasives : 5305 screws, 5306 bolts, 5307 studs, 5310 nuts & washers,
                              5315 pins/keys, 5330 gaskets & packings, 5340 misc hardware
FSG 47 Pipe/Tube/Hose/Fitting: 4710 pipe & tube, 4720 hose & flexible tubing, 4730 fittings
FSG 48 Valves               : 4810 valves powered, 4820 valves non-powered
FSG 31 Bearings             : 3110 antifriction bearings, 3120 plain bearings, 3130 bearing housings
FSG 61 Electric Wire & Power: 6105 motors, 6145 wire & cable, 6150 wiring devices
FSG 43 Pumps & Compressors  : 4310 compressors, 4320 pumps
FSG 51 Hand Tools           : 5120, 5130, 5133
```
[JUDGMENT] 5306/5310/4730/3110/6145 alone will carry the whole demo, and they are precisely the
categories where "M10×50 vs M10×75" arguments are visceral and obvious to a non-technical judge.

**[ASSUMPTION] I did not count NIINs per FSC. Verify immediately after download with:**
`awk -F'","' 'NR>1{print $1}' P_FLIS_NSN.CSV | sort | uniq -c | sort -rn | head -50`

## Step 1 — Download and freeze the FLIS slice (1 day, week 1) — **DO THIS FIRST, IT UNBLOCKS EVERYTHING**

Manually, in a real desktop browser, from https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/ :
1. `H-SERIES.zip` (14.6 MB) — dictionaries. **Download first; it's tiny and immediately useful.**
2. `MRD.zip` (4.2 MB) — attribute schema + controlled vocabularies. **Also tiny.**
3. `IDENTIFICATION.zip` (346 MB) — the NSN/INC/name backbone + standardization ground truth.
4. `REFERENCE.zip` (172 MB) — part-number → NIIN duplicate ground truth.
5. `FLISV.zip` (367 MB) — **coded** attributes. Prefer this over `CHARACTERISTICS.zip`: it is
   smaller *and* the values are coded against `MRD0300`, so they are machine-comparable without NLP.
6. `CHARACTERISTICS.zip` (500 MB) — **optional**, only if you want free-text attribute replies for
   an extraction-model training set. **[JUDGMENT] Take it: `REQUIREMENTS_STATEMENT` +
   `CLEAR_TEXT_REPLY` is a ready-made supervised attribute-extraction dataset, and you will want it.**

**Total: ~1.4 GB. Then immediately: `sha256sum *.zip > MANIFEST.txt`, record the download date,
and put the ZIPs in a team drive. Treat dla.mil as a one-time source, never a runtime dependency.**

## Step 2 — Build the canonical layer (2–3 days, week 1–2)

Load into Postgres:
```sql
inc_dictionary(inc PK, item_name, definition, inc_status, type_code)          -- 79,883 rows [VERIFIED]
fsc_dictionary(fsc PK, fsc_title, fsc_notes, fsc_inclusions, fsc_exclusions)  -- 676 rows    [VERIFIED]
fsc_inc(fsc, inc, item_name)                                                  -- 6,877,262   [VERIFIED]
inc_related(inc, related_inc, item_name)                                      -- 33,930      [VERIFIED]
colloquial_name(inc, related_inc, colloquial_name)                            -- alias dict  [VERIFIED file]
mrc_dictionary(mrc PK, requirement_statement, definition, reply_table_ids[])  -- 27,552      [VERIFIED]
mrc_reply_values(reply_table, code, decoded_value)                            -- 164,926     [VERIFIED]
inc_mrc_schema(inc, mrc, reply_table)                                         -- 45,305      [VERIFIED]
nsn_item(fsc, niin PK, inc, item_name, sos, end_item_name)                    -- filtered slice
nsn_attribute(niin, mrc, mode_code, coded_clear_reply)                        -- filtered slice
nsn_part(niin, part_number, cage_code, rncc, rnvc)                            -- filtered slice
nsn_standardization(niin, related_nsn, isc, orig_stdzn_dec, dt_stdzn_dec)     -- filtered slice
```
**[JUDGMENT] `inc_mrc_schema` is the single most important table in the whole system.** It tells you,
for a given item type, *which attributes are decisive*. That is precisely how you avoid the brief's
stated failure mode ("M10×50 and M10×75 are semantically near-identical but different") — you compare
on the attributes the codification standard itself says matter for that item type, not on cosine similarity.

## Step 3 — Extract the REAL labelled pairs (1–2 days, week 2)

- **Duplicates (real):** group `nsn_part` by `niin` → every pair of distinct `(cage_code, part_number)`
  under one NIIN is a **real** positive. Expected yield: **large** — UNVERIFIED count, measure it.
- **Functional equivalents (real):** `nsn_standardization` rows where `related_nsn` is non-empty and
  `isc` encodes a replacement relation (ISC 1↔2, 3/E → replacement). **Expected yield: UNVERIFIED —
  most rows in my sample had empty `RELATED_NSN`. MEASURE THIS BEFORE PROMISING IT.**
  Check with: `awk -F'","' 'NR>1 && $2!=""' V_FLIS_STANDARDIZATION.CSV | wc -l`
  **[FLAG] If this yields < 2,000 pairs inside your FSC slice, the "functionally equivalent" class
  must fall back to a rule over `inc_mrc_schema` (same INC, all decisive MRCs equal, non-decisive
  MRCs differ) and you must say so openly.**
- **Near-duplicates (real):** same INC, attribute vectors from `nsn_attribute` differing in exactly
  one MRC.
- **Distinct (real):** sampled across different INCs, weighted toward `inc_related` pairs (hard).

Target: **50,000–150,000 real labelled pairs** across the four classes within the chosen FSC slice.
[JUDGMENT] This is 3–30× the brief's stated ambition of 5,000–50,000 *records*, and it is real.

## Step 4 — Generate the CPSE surface layer (3–4 days, week 2–3)

For each canonical item in the slice, render a **canonical description** from
(`item_name` + decisive MRC values), then emit **6–12 CPSE-style variants** per item via:
abbreviation (STAINLESS STEEL→SS, HEXAGON→HEX), token reordering, separator swaps
(`M10 X 50` / `M10X50` / `M10*50` / `10MM X 50MM`), unit-form changes, redundant-token insertion
(make/vendor/legacy code suffixes), typos at a measured rate, and occasional
Hindi/transliterated tokens. Assign each variant a fake CPSE code in a per-CPSE format
(`MAT-#####`, `BLT-#####`, `XJ-#####`, numeric-only) — this is what makes the demo legible.

**Calibrate every transform against §4's hand-collected real lines and against MaintIE.**
Log the transform chain per record so every synthetic row is auditable and reversible.

Expected corpus: **canonical items × ~8 = 200,000–500,000 description rows** across 3–5 simulated CPSEs.
[JUDGMENT] Cap the demo database at ~50,000–100,000 rows. Bigger is not more impressive; a demo that
lags is less impressive. Keep the full set for offline training/eval only.

## Step 5 — External benchmarks (1 day, week 3)

Download and run baselines on WDC Products (`80pair`, and the 100%-unseen variant),
Abt-Buy, Walmart-Amazon (Structured + **Dirty**), PriceRunner. Report your numbers beside published
baselines from the WDC Products (EDBT 2024) and Ditto (https://arxiv.org/pdf/2004.00584) papers.
**[JUDGMENT] This one day buys more credibility than any UI feature in the entire brief.**

## Step 6 — Realism evidence (1 day, week 3–4)

Hand-collect 200–500 real CPSE tender/BOQ description lines (§4). Hand-label a subset. Report as
Test set C. **Record source org / tender ID / URL / date for every line.**

---

## REAL vs SYNTHETIC — the honest accounting

| Layer | REAL | SYNTHETIC |
|---|---|---|
| Item identity (what the thing is) | **100%** (FLIS NIIN/INC, BOLTS standards) | 0% |
| Classification (FSC/INC/UNSPSC) | **100%** | 0% |
| Attribute schema (which attributes matter) | **100%** (FLIS MRC / `inc_mrc_schema`) | 0% |
| Attribute values | **100%** for FLIS items; real enumerated values for BOLTS items | 0% |
| Match/no-match labels | **~100%** — from `V_FLIS_PART` and `V_FLIS_STANDARDIZATION` | 0% (labels are *derived*, never asserted) |
| **Description surface text** | ~1–3% (GSA extract, hand-collected CPSE lines, MaintIE) | **~97%** |
| CPSE org identity & internal codes | 0% | **100% — simulated, explicitly labelled** |
| Dashboard figures | 0% | **100% — must be labelled "demo data" on every screen** |

## The sentence to say on stage — [JUDGMENT, and say it *before* anyone asks]

> "Our canonical items, their classification, their attribute schema and every match label come from
> the US Defense Logistics Agency's publicly released FLIS/PUB LOG catalogue — roughly 80,000 approved
> item names, 27,000 attribute definitions, and real human standardization decisions, built on the
> same NATO Codification System that India's own National Codification Bureau adopted in 2008.
> What we generate synthetically is only the *surface text* — the messy, abbreviated way five
> different CPSEs would each write down the same real item — because no Indian CPSE material master
> is public, and we will not scrape one. Our reported accuracy separates the two: we report on real
> catalogue pairs, on synthetic CPSE-style pairs, on real Indian tender description lines we collected
> by hand, and on four published academic benchmarks where other people's numbers exist to compare against."

**[JUDGMENT] Volunteering the provenance limitation, with this level of specificity, converts your
biggest vulnerability into your strongest credibility signal.** Teams that hide it get destroyed in Q&A.

---

# 12. FALLBACK PLAN

**Trigger: FLIS/PUB LOG becomes unavailable (WAF blocks you from India, files pulled, DLA restructures again).**

**F1 — Immediate (0 cost, do it anyway):** you already downloaded and hashed the ZIPs in week 1.
**This is why Step 1 is Step 1.** The fallback for the primary source is *having already taken it*.
**[JUDGMENT] If you do only one thing after reading this document, download those files today.**

**F2 — If you never got them:** pivot the canonical layer to **BOLTS + UNSPSC + GSA NSN extract**.
- BOLTS gives real standards-backed canonical items with typed attributes (LGPL, on GitHub, mirrored).
- UNSPSC (UNGM XLSX) gives the classification taxonomy.
- GSA NSN extract (CC0, already downloaded, 12,454 rows) gives real prose descriptions keyed to NSNs.
- **Cost:** you lose the real duplicate/equivalence labels. Match labels then become *derived from
  attribute equality on real standards data* rather than *observed human decisions*.
  **You must state that change of provenance explicitly.** It is weaker but still honest.
- **Effort:** ~3 extra days. **[JUDGMENT] The system still demos. The scientific claim weakens
  from "we reproduce real standardization decisions" to "we reproduce standards-defined identity".**

**F3 — Benchmark-only credibility floor:** even in total domain-data failure, WDC Products +
DeepMatcher suite + PriceRunner still let you report **real measured F1 against published baselines**.
This floor is unremovable and costs one day. **[JUDGMENT] It is your insurance policy: secure it
in week 3, not week 9.**

**F4 — What you must NOT do under pressure:** scrape GeM, defeat the CPPP CAPTCHA, scrape McMaster/
IndiaMART, or generate labels with an LLM and present them as ground truth. Every one of these
converts a recoverable data problem into an unrecoverable credibility problem.

---

# 13. THINGS IN THE BRIEF THAT THIS RESEARCH CONTRADICTS

1. **§5 "public government procurement datasets, public CPSE material catalogs, GeM/public
   procurement data where legally usable"** — [VERIFIED] none of these yield item-level material
   data that is both accessible and legally usable. **Correct this in the Phase 0 approval document.**
2. **§5 "Initial 5,000-50,000+ records"** — this target is **too low and mis-framed**. FLIS makes
   *millions* of real records available; the binding constraint is not availability, it is
   **choosing a coherent slice and keeping the demo DB fast**. Reframe as: *millions available,
   ~100k-row curated demo corpus, 50k–150k real labelled pairs for training/eval.*
3. **§6 "generate realistic variants"** — right instinct, but the brief does not say where the
   *identities* come from. Without §9.1's real-identity anchor, the whole augmentation strategy is
   circular. **This is the most important correction in this document.**
4. **§7 output classes** — all four map onto real FLIS relations (§1.1.4), **except**
   FUNCTIONALLY EQUIVALENT, whose real-label yield is **unmeasured**. Measure before promising.
5. **§30 demo strategy "AI finds thousands of potential duplicates"** — achievable and real, but
   the duplicates will be *synthetic-surface over real identity*. The dashboard must label this.
   [JUDGMENT] Put a persistent, non-apologetic "Demo dataset — synthetic CPSE surface forms over
   real DLA/FLIS catalogue identities" badge in the UI chrome. It reads as rigour, not weakness.

---

# 14. IMMEDIATE ACTIONS (this week, in order)

1. **Download the 6 PUB LOG ZIPs manually in a browser. Hash them. Archive them.** (1 person, 2 hours)
   — *this is the single highest-value action in the entire Phase 0.*
2. Unzip `H-SERIES.zip` and `MRD.zip` (19 MB combined) and eyeball
   `P_H6_PICK.CSV`, `MRD0107.CSV`, `MRD06P1.CSV`. **Understanding INC + MRC + reply tables is
   understanding this entire problem domain.** (whole team, 2 hours — do it together)
3. Count NIINs per FSC; finalise the FSC slice. (1 person, 2 hours)
4. Measure the real yield of `V_FLIS_STANDARDIZATION` non-empty `RELATED_NSN` in your slice.
   **This decides whether "functionally equivalent" is a real class or a derived one.** (1 person, 1 hour)
5. Download WDC Products `80pair.zip` + Walmart-Amazon Dirty + Abt-Buy + PriceRunner. (1 person, 1 hour)
6. Clone `boltsparts/BOLTS_archive`, parse `hex.blt`/`nut.blt`/`bearings.blt`, and **count the actual
   Cartesian yield.** (1 person, 3 hours)
7. Start the manual CPSE tender-line collection — 2 people, ~1 day, target 300 lines with provenance.
8. Verify India's NCB code and the AC/135 membership date from `ddpdos.gov.in` before anyone drafts a slide.

---

# 15. FULL SOURCE LIST (every URL I touched this session)

Verified reachable and used:
- https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/
- https://www.dla.mil/Portals/104/Documents/InformationOperations/LogisticsInformationServices/FOIA/PUBLOG/ (ZIP + layout PDF directory)
- https://catalog.data.gov/dataset/national-stock-number-extract
- https://inventory.data.gov/dataset/67567804-073d-40ad-a710-2b0bed8b84e2/resource/3b7ed6b7-7dce-42f1-852d-6465e3e790e4/download/nsn-extract-2-21-23.xls.xlsx
- https://www.ungm.org/public/unspsc  •  https://www.ungm.org/Public/UNSPSC/Excel
- https://webdatacommons.org/largescaleproductcorpus/wdc-products/
- https://data.dws.informatik.uni-mannheim.de/largescaleproductcorpus/data/wdc-products/80pair.zip
- https://github.com/wbsg-uni-mannheim/wdcproducts  •  https://arxiv.org/abs/2301.09521
- https://github.com/anhaidgroup/deepmatcher/blob/master/Datasets.md
- http://pages.cs.wisc.edu/~anhai/data1/deepmatcher_data/ (Structured / Textual / Dirty)
- https://huggingface.co/datasets/lakritidis/product-matching
- https://www.kaggle.com/datasets/lakritidis/product-clustering-matching-classification
- https://github.com/nlp-tlp/maintie
- https://github.com/boltsparts/BOLTS_archive  •  https://github.com/shaise/FreeCAD_FastenersWB
- https://github.com/amazon-science/esci-data
- https://www.data.gov.in/  •  https://www.data.gov.in/Godl
- https://gem.gov.in/websitePolicies  •  https://gem.gov.in/robots.txt  •  https://bidplus.gem.gov.in/robots.txt
- https://eprocure.gov.in/eprocure/app  •  https://eprocure.gov.in/cppp/
- https://www.ireps.gov.in/ireps.html
- https://ddpdos.gov.in/ncb-india/overview
- https://www.mcmaster.com/robots.txt  •  https://www.indiamart.com/robots.txt  •  https://www.fastenal.com/robots.txt
- https://www.iso-group.com/Information/ISC/  (secondary source, ISC semantics)

Verified UNREACHABLE / DEAD / CHANGED (do not cite):
- **https://www.unspsc.org/** → now serves sweepstakes-casino content
- **http://di2kg.inf.uniroma3.it/datasets.html** → DNS ENOTFOUND
- https://eclass.eu/en/eclass-standard/download → HTTP 404
- https://catalog.data.gov/dataset/federal-item-identification-guide-fiig → HTTP 404

Referenced but NOT verified in this session (marked UNVERIFIED in text):
- https://apps.dtic.mil/sti/tr/pdf/ADA325591.pdf (DoD 4100.39-M FLIS Procedures Manual)
- https://www.nspa.nato.int/ (NMCRL)  •  https://www.eotd.org/ bulk export  •  https://arxiv.org/pdf/2101.11259 (Alaska)
