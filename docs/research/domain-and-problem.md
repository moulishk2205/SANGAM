# SIH26099 — Domain & Problem Research
**Phase 0 reference document. Planning only — no implementation.**
Author: technical architect (adversarial reviewer role)
Date: 2026-08-26

---

## 0. How to read this document

Every substantive claim carries one of three labels:

- **[VERIFIED]** — I fetched a source in this session. URL given inline. You can re-fetch it.
- **[JUDGMENT]** — my reasoned engineering opinion. Argue with it; it is not fact.
- **[ASSUMPTION]** — plausible but unchecked. Each one states *how to check it*.
- **UNVERIFIED — verify by X** — I could not confirm this exists. **Do not put it on a slide until you check.**

I have deliberately **not** invented a single dataset URL, record count, licence term or benchmark
number. Where I could not confirm something, it says so. Read section 11 (Verification Checklist)
before anyone writes a line of code or a line of a pitch deck.

---

## 1. SIH26099 — the actual problem statement

### 1.1 Official metadata [VERIFIED]

Retrieved from two independent community mirrors of `sih.gov.in/sih2026PS`, which agree verbatim:

- https://raw.githubusercontent.com/vedantchalke36/sih-2026-problem-statements/main/ps_2026/SIH26099.md
- https://raw.githubusercontent.com/Sourav112-droid/sih-2026-problem-statements/main/data/sih-2026.json

| Field | Value |
|---|---|
| PS Number | **SIH26099** |
| Title | **AI-Driven Standardization and Harmonization of Material Codes Across CPSEs** |
| Organization | **Ministry of Petroleum & Natural Gas** |
| Department | **Chennai Petroleum Corporation Limited (CPCL)** |
| Category | Software |
| Theme | Smart Automation |
| Idea submission deadline | **20 September 2026** |
| Dataset Link | *"CPSE Material Master Data / Sample Material Master Dataset — To be provided by participating CPSEs"* |
| Contact / YouTube | N/A |

**Verify by**: log in at https://sih.gov.in/sih2026PS and confirm the text byte-for-byte. Mirrors are
community scrapes (snapshot 2026-08-21, CC-BY-4.0 per the mirror's own footer); they are *very likely*
faithful but they are not the authority. Do this before the idea submission.

### 1.2 What the PS actually asks for [VERIFIED — quoted from the mirror text]

Eleven named capabilities:

1. AI-based matching of material descriptions and specifications across CPSEs
2. Identification of duplicate, near-duplicate and equivalent materials
3. Automated standardization of material descriptions and technical attributes
4. Intelligent classification and categorization of materials
5. Generation/recommendation of a **Common National Material Code**
6. Mapping of existing CPSE material codes to the common national code
7. Legacy material code rationalization and migration support
8. User validation and approval workflow for AI recommendations
9. Dashboard for material master analytics and duplicate detection
10. Audit trail and governance mechanism for material master changes
11. Integration capability with SAP/ERP systems of participating CPSEs

Tagline in the PS: **"One Nation – One Material Code"** for common materials, *"while maintaining
traceability to individual CPSE material codes."*

Stated expected impact includes demand aggregation, inventory optimisation and "reduced procurement
cost" — note the PS itself frames these as *expected impact*, not measured outcomes.

### 1.3 Critical observations about the PS

**(a) The dataset does not exist yet.** [VERIFIED from the PS text] The "Dataset Link" field literally
says *"To be provided by participating CPSEs."* There is no attached file. This is the single largest
project risk. **Plan on the assumption that no real CPSE material master will ever reach you.** If one
does arrive it is a bonus, not a dependency. See §8.

**(b) The sponsor is a refinery, not a generic PSU.** CPCL is a Chennai-based refining company under
the IOCL group. [VERIFIED — https://iocl.com/chennai-petroleum-corporation-limited ; CPCL was
classified a Navratna CPSE in June 2026 per https://cpcl.co.in/ and press coverage]. **[JUDGMENT]** Your
judges at the national round will very likely include CPCL materials-management or IS staff who look at
a refinery material master every working day. They will know instantly whether your demo commodities are
real. Build the demo around **refinery MRO**: pipes, flanges, fittings, gaskets, valves, bearings,
mechanical seals, electric motors, cables, instrumentation (transmitters, gauges), fasteners, lubricants,
PPE. Not "office chairs" and not only bolts.

**(c) The PS is heavier on governance than on ML.** Six of the eleven capabilities (5,6,7,8,10,11) are
identity/workflow/integration, not AI. **[JUDGMENT]** A team that builds a beautiful matcher and a thin
workflow will lose to a team that builds a good matcher and a credible codification + governance +
audit story, because the *stated* deliverable is a **material master framework**, not a duplicate detector.

**(d) Community difficulty scoring** rates SIH26099 as level 3/5, score 60/100, with
`mvp_feasibility_36h: 3`, `integration_breadth: 4`, `data_dependency: 3`
[VERIFIED — the Sourav112-droid JSON, but the mirror explicitly flags
`"difficulty_is_community_derived": true`]. Treat as a community opinion, not an official rating.

### 1.4 Prior SIH precedent

I searched for earlier SIH problem statements on material master / material code standardisation and
for how winners approached them. **I found none that match.** The closest adjacent items are in SIH 2026
itself: **SIH26100** (Ministry of Petroleum & Natural Gas — *AI-Powered Integrated Bid Compliance
Verification Platform for GeM Procurement*) and **SIH26108** (Ministry of Consumer Affairs — *AI-Powered
Recommendation Engine for Identifying Applicable Indian Standards for Procurement*)
[VERIFIED by grepping the mirrored 2026 PS corpus].

**UNVERIFIED — verify by** browsing sih.gov.in archives for SIH 2023/2024/2025 PS lists, or the Kaggle
"SIH Problem Dataset (2025–Present)". **Do not claim in your deck that "no one has attempted this before
at SIH"** — you cannot substantiate it and it adds nothing.

---

## 2. What a "material master" actually is

### 2.1 SAP MM — the structure you will be judged against

SAP is the dominant ERP in large Indian CPSEs. **[ASSUMPTION — verify by** checking annual reports /
IT tenders of ONGC, IOCL, BHEL, NTPC, SAIL for "SAP S/4HANA" mentions**]**. The PS itself says
"different ERP/SAP systems", so SAP fluency is table stakes.

Core tables [VERIFIED — https://leanx.eu/sap/table/mara/ and SAP Note 1630702 discussions]:

| Table | Scope | Notes |
|---|---|---|
| **MARA** | General (client-wide) | one row per material |
| **MAKT** | Descriptions | one row per material × language |
| **MARC** | Plant level | MRP type, procurement type, purchasing group |
| **MARD** | Storage-location stock | |
| **MBEW** | Valuation | |
| **MARM** | Alternative units of measure | conversion factors |
| **MEAN** | International article numbers (EAN/GTIN) | |

**MARA fields you should actually model** [VERIFIED — leanx.eu/sap/table/mara/]:

| Field | Meaning | Type/Len |
|---|---|---|
| `MATNR` | Material number | CHAR 18 |
| `MBRSH` | Industry sector | CHAR 1 |
| `MTART` | Material type (ROH/HALB/FERT/ERSA spare parts/HIBE consumables…) | CHAR 4 |
| `MEINS` | Base unit of measure | UNIT 3 |
| `MATKL` | **Material group** — the classification field | CHAR 9 |
| `BISMT` | **Old material number** — legacy code, the migration scar | CHAR 18 |
| `SPART` | Division | CHAR 2 |
| `NORMT` | **Industry standard description** (e.g. "DIN 933", "ASTM A193") | CHAR 18 |
| `GROES` | Size / dimensions (free text) | CHAR 32 |
| `WRKST` | **Basic material** (e.g. "SS316", "CARBON STEEL") | CHAR 48 |
| `ZEINR` | **Document/drawing number** | CHAR 22 |
| `EXTWG` | External material group | CHAR 18 |
| `BRGEW`/`NTGEW`/`GEWEI` | Gross/net weight + unit | QUAN 13,3 / UNIT 3 |
| `VOLUM` | Volume | QUAN 13,3 |

**MAKT.MAKTX — material short description — is CHAR 40.** [VERIFIED — SAP KBA 1630702 "Extend the
Length of Field MAKT-MAKTX (Material Description) in the Material Master";
https://userapps.support.sap.com/sap/support/knowledge/en/1630702 ; the field uses domain TEXT40 and SAP
does not support lengthening it.]

> **This 40-character limit is the single most important domain fact in this entire document.**
> Every abbreviation catastrophe in your brief (`SS HEX BOLT M10X50`, `BOLT HEX SS M10*50`) exists
> *because a storekeeper had 40 characters and a full specification to express*. Different sites
> abbreviate differently, drop different words, and reorder differently. Longer text lives in
> "Basic Data Text" (a long-text object, table STXH/STXL) which is often empty, often not migrated,
> and almost never extracted for analytics.
> **Design consequence:** your normaliser must be an *abbreviation expander operating under a
> 40-char generation constraint*, and your canonical description generator must emit **both** a
> ≤40-char SAP-compatible short text **and** a full-length canonical text. Nobody else at SIH will
> think of this. It is free credibility with a CPCL judge.

SAP also has **Classification (CLASS/CABN/AUSP)** — class types 001/023/300 with characteristics —
which is SAP's native attribute mechanism. **[JUDGMENT]** In practice it is patchily populated in
brownfield CPSE systems; that is precisely why "extract attributes from the description" is the
problem being posed. Mention SAP Classification in your architecture as the *write-back target*
for extracted attributes — that is the credible ERP integration story (§9).

### 2.2 Oracle EBS / Fusion

[VERIFIED — https://oraclebytes.com/mtl_system_items_b-columns-indexes-few-tricks/ and
https://etrm.live/etrm-12.2.2/... ]

- `MTL_SYSTEM_ITEMS_B` — item master, one row per item × organization. Item number is `SEGMENT1`
  (VARCHAR2(40)); `SEGMENT2..N` exist for multi-segment item keys.
- Description lives in `MTL_SYSTEM_ITEMS_TL` (translatable), keyed by `INVENTORY_ITEM_ID`,
  `ORGANIZATION_ID`, `LANGUAGE`.
- Attributes come from **Item Catalog Groups** + **descriptive elements** (Oracle's analogue of SAP
  Classification).
- Fusion equivalent of `MTL_SYSTEM_ITEMS_B` is `EGP_SYSTEM_ITEMS_B`.

**[JUDGMENT]** Model your ingestion schema as a **superset that both map onto**, not as "an SAP
importer". Two mapping profiles (SAP, Oracle) + a generic CSV profile is enough. Do not build ERP
connectors.

### 2.3 Why duplicates actually arise (operational causes)

**[JUDGMENT, grounded in the standard MDM literature and vendor case material]** — worth stating in your
deck because it shows you understand the *cause*, which motivates capability 12 (prevention):

1. **Decentralised creation.** Each plant/unit/depot has code-creation rights. A storekeeper under
   time pressure searches "BOLT", finds nothing (because the existing record says "BLT HEX"), and
   creates a new code. This is the dominant mechanism.
2. **Search that cannot find what exists.** SAP's standard material search is a `LIKE` on a
   40-char string. If you cannot find it, you create it. **Duplicate creation is a search failure,
   not a discipline failure.** This reframing is your strongest argument for capability 12/15.
3. **Urgency of procurement.** Plant down, need part today, code creation is the fast path.
4. **Legacy migration.** Multiple legacy systems merged into one SAP client, each contributing its own
   code series. `MARA-BISMT` (old material number) is the fossil record of this.
5. **Mergers / restructuring.** e.g. CPCL sits within the IOCL group; ONGC/HPCL; each brings a master.
6. **No governance role.** Many CPSEs have no dedicated data steward for material master.
7. **Vendor-driven descriptions.** Description copied verbatim from whichever vendor quoted first,
   so the same physical item gets three vendors' three naming conventions.
8. **Unit-of-measure ambiguity.** Same item stocked as EA at one plant, as SET or BOX-100 at another —
   creating a "different" material by definition even though it is physically identical.

---

## 3. Indian public-sector procurement context

### 3.1 CPSEs and DPE

- The **Department of Public Enterprises (DPE)** is the nodal body for CPSEs and publishes the annual
  **Public Enterprises Survey**. DPE now sits under the **Ministry of Finance**
  [VERIFIED — https://www.dpe.gov.in/documents/reports/public-enterprises-survey-2024-25-cDO4IjMtQWa
  and the Ministry of Finance social post announcing the PE Survey 2024-25 launch].
- Press coverage of PE Survey 2024-25 reports **226 profit-making and 63 loss-making operating CPSEs**
  in FY25 [VERIFIED via https://indianpsu.com/cpsu-profit-2024-25-public-enterprises-survey/ — a
  secondary source; **verify by** downloading the PE Survey PDF from dpe.gov.in before quoting].
- **Do not quote a CPSE count on a slide without pulling it from the DPE PDF yourself.** It is the
  easiest fact in your deck to get wrong and the easiest for a judge to correct you on.

Named CPSEs relevant to this PS (Oil & Gas / Power / Steel / Mining / Heavy Engineering, per the PS
text): ONGC, IOCL, BPCL, HPCL, GAIL, OIL, CPCL, NRL, MRPL, EIL (Oil & Gas); NTPC, NHPC, PGCIL, PFC, REC
(Power); SAIL, RINL (Steel); CIL, NMDC, NLC (Mining); BHEL, BEL, HAL, BEML (Heavy Engineering).
**[ASSUMPTION]** that these are the intended "participating CPSEs" — the PS names sectors, not companies.

### 3.2 GeM (Government e-Marketplace)

- GeM is the national public procurement portal for common-use goods and services, covering central and
  state ministries, PSUs, autonomous institutions and local bodies
  [VERIFIED — https://gem.gov.in/].
- Its catalogue is organised as **product categories** each with a defined set of category
  **specification parameters** (the seller must fill category-specific attributes to list a product);
  categories are grouped into "quadrants" (Q1–Q6) that determine seller eligibility.
  [VERIFIED for the general structure — https://gem.gov.in/landing/index/Catalogue_Management ;
  the quadrant framing is from a secondary source, https://www.bidz365.com/blog/exploring-the-six-quadrants-on-the-gem]
- Category counts of "10,900+ product categories / 330 service categories" appear in secondary sources
  only. **UNVERIFIED — verify by** reading GeM's own annual report or the category browser before
  quoting a number.

**[JUDGMENT] Why GeM matters to you far more than you think:** GeM already solved a *narrow* slice of
this problem. A GeM category is effectively an item-name + a mandated attribute template, and sellers
are forced to fill it. That is exactly the "class + characteristics" model of NCS/ISO 22745. Your
platform is *not* competing with GeM; the honest positioning is:

> "GeM standardises what CPSEs **buy on GeM**. It does nothing for the tens of millions of legacy
> material master records **inside** CPSE ERPs, and nothing for cross-CPSE identity. We standardise the
> master, and we can emit GeM-category-shaped output so that a harmonised material is GeM-ready."

That is a defensible, non-overlapping claim and it will land with a MoP&NG panel.

### 3.3 DGS&D legacy

DGS&D (Directorate General of Supplies & Disposals) was the central procurement organisation that GeM
replaced. DGS&D maintained its own catalogue and codification. **[ASSUMPTION]** that a DGS&D catalogue
with codes is still obtainable. **UNVERIFIED — verify by** searching the National Archives / GeM
transition documents. **Do not assert a DGS&D code structure in your deck.** One secondary source
(https://theintactone.com/2018/12/16/codification-and-standardization/) states that "railways and
DGS&D" historically used codification schemes of eight to thirteen digits, with the first two digits
for major group, next two for sub-group, and further digits for dimensional characteristics — treat
this as *illustrative of Indian practice*, not as an authoritative spec.

### 3.4 MESC — the codification system actually used in oil & gas

**MESC = Material and Equipment Standards and Code.** Created by Shell in 1932 and licensed widely
through the oil, gas, chemical and power sectors.

Structure [VERIFIED — https://www.verdantis.com/mesc-code/ ; corroborated in outline by
https://panemu.com/blog/asset-management-24/mesc-code-the-backbone-of-material-and-equipment-standards-in-oil-and-gas-403
and https://www.ifxsoftware.com/trip/material-equipment-standards-code-mesc]:

```
10 digits:  XX . XX . XX . XXX . X
            │    │    │     │     └─ code type indicator (1 = central standard, 9 = local variant)
            │    │    │     └─────── "buying description" (3 digits) — the specific variant
            │    │    └───────────── sub-sub-group (material/pressure class/config)
            │    └────────────────── sub-group (e.g. 74.16 = ball valves)
            └─────────────────────── main group (e.g. 74 = piping & valves)
```
Example given by the source: `74.16.01.015.1` = piping & valves / ball valves / SS 150 PSI / 2-inch
variant / central standard. The same source states MESC covers roughly 110,000 standardised items.

**Caveats you must respect:**
- **MESC is proprietary to Shell and licensed.** Do **not** ship MESC data, do **not** claim your
  system "uses MESC". **UNVERIFIED — verify by** looking for Shell's MESC licensing terms if you want to
  reference it at all. **[JUDGMENT]** Reference MESC *as prior art and as an example of a hierarchical
  significant code*, and then explain why you deliberately did **not** copy that design (§4.4).
- Whether ONGC / IOCL / CPCL specifically use MESC-derived codes today is **UNVERIFIED — verify by**
  reading ONGC's *Integrated Materials Management Manual* (linked from
  https://www.ongcindia.com/wps/wcm/connect/en/about-ongc/interface/material-management/tenders-booklets/tenders-booklets)
  or by inspecting material codes printed in public CPSE tender documents (§8.3).

### 3.5 Is there an existing Indian national material codification standard?

**Short answer: I found no evidence of a general-purpose national material codification standard for
civil CPSEs.** What exists:

- **BIS (Bureau of Indian Standards)** is the national standards body. There are IS standards for
  *classification and codification of specific material families* — e.g. **IS 8730** *"Classification
  and Codification of Bulk Materials for Continuous Material Handling Equipment"*
  [VERIFIED that this standard exists — https://law.resource.org/pub/in/bis/S08/is.8730.1997.pdf and
  the 2023 revision at https://archive.org/details/gov.in.is.8730.2023]. That is bulk solids handling,
  **not** an MRO material master standard. Do not overstate it.
- **NCB (India)** — India's National Codification Bureau, under the Directorate of Standardisation,
  Department of Defence Production, operating the NATO Codification System for defence items
  [VERIFIED — https://ddpdos.gov.in/ncb-india/nato-codification/codification-system]. See §4.
- Individual CPSEs, Indian Railways (PL numbers) and DGS&D each maintain their **own** schemes.

**[JUDGMENT] This is your strongest strategic finding.** The gap the PS is pointing at is real: **India
has a rigorous national codification system for defence materiel (NCB India / NCS) and no equivalent for
civil CPSE MRO.** Your pitch should say exactly that, and position the Common National Material Code as
"the civil-CPSE analogue of what NCB India already does for defence." That is accurate, verifiable,
politically resonant, and nobody can accuse you of inventing it.

---

## 4. The NATO Codification System — the precedent you should mine hardest

### 4.1 What NCS is

A single, multinational system for uniquely identifying, classifying and cataloguing every item of
supply used by member and partner nations. Governed by **AC/135** (Group of National Directors on
Codification) with **NSPA** (NATO Support and Procurement Agency) providing the tooling; the manual is
**ACodP-1**. [VERIFIED — https://eportal.nspa.nato.int/ac135/data/pdf/ACodP1_E.pdf ;
https://www.dla.mil/Working-With-DLA/Federal-and-International-Cataloging/NATO/ ;
mirror of ACodP-1 hosted by India's DDP at https://ddpdos.gov.in/sites/default/files/documents/ACodP1_E_2019.pdf]

Scale: NSPA describes NMCRL (NATO Master Catalogue of References for Logistics) as covering on the order
of **17 million NSNs** [VERIFIED as a claim on https://www.nato.int/structur/AC/135 — treat the exact
figure as the organisation's own statement].

### 4.2 The NSN — 13 digits

[VERIFIED — https://en.wikipedia.org/wiki/NATO_Stock_Number ;
https://docs.ifs.com/ifsclouddocs/26r1/lang/en/DefNATOCodeStd/AboutNATOStockNumber.htm ;
https://odysseydcs.com/anatomy-of-an-nsn/]

```
NSN   =  1234 - 56 - 789 - 0123        (13 digits, printed as 4-2-3-4)
         └─┬┘   └┬┘  └───┬───┘
           │     │       └──────  7-digit non-significant serial (item number)
           │     └──────────────  NCB code: which nation's bureau codified it
           └────────────────────  NSC (NATO Supply Classification): 2-digit group + 2-digit class
NIIN  =  digits 5–13  (NCB code + 7-digit serial) = the actual unique identity
```

**The essential design lesson: only the first four digits carry meaning.** The identity itself (NIIN)
is a **non-significant** number. Classification is a *separate attribute*, not baked into the identifier.

### 4.3 The attribute machinery — this is what you actually want

[VERIFIED — https://haystack.ihserc.com/help/haystack/webhelp/content/INC.htm ;
https://www.iso-group.com/Information/MRC/ ; https://www.parttarget.com/nsn_glossary.html ;
ACodP-1 as above]

| Concept | What it is |
|---|---|
| **Item Name / Approved Item Name** | The controlled canonical noun-phrase for a kind of item. Agreed across participating nations. |
| **INC (Item Name Code)** | A **five-digit** code identifying each approved item name. Non-approved names get INC `77777`. |
| **FIIG (Federal Item Identification Guide)** | Per-item-name template listing *which characteristics must be recorded* and in what form. |
| **MRC (Master Requirement Code)** | A code assigned to each distinct FIIG requirement — i.e. a **stable identifier for one attribute** ("thread diameter", "material", "pressure rating"). Characteristics requirements carry a four-position alpha code within a FIIG. |
| **Reference Number + NCAGE** | Manufacturer part/drawing number + the coded identity of the manufacturer. |

**Two identification methods** — this is the part your brief completely misses
[VERIFIED — ACodP-1, Type II Code DRN 4820; summarised at
https://www.gov.br/caslode/pt-br/catalogacao/codsp/ACodP1_EJan2025.pdf]:

- **Descriptive method** (Type 1 / Type 4): identity is established by **technical and performance
  characteristics**. Items grouped under the same NSN must be *functionally interchangeable*.
- **Reference method** (Type 2): identity is established **indirectly**, by
  **manufacturer (NCAGE) + reference/drawing number**, with only an item name attached.

Real catalogues are a *mixture* of both, per item.

### 4.4 What you can legitimately borrow

**[JUDGMENT] — this is the core architectural recommendation of this document.**

1. **Copy the identifier philosophy: non-significant national ID + separate classification.**
   Your `NMC-0001842` from the brief is *correct*. **Do not** build a "smart" hierarchical
   Common National Material Code where digits encode group/subgroup/dimension (the MESC/DGS&D style).
   Significant codes are a maintenance disaster: they break when an item is reclassified, they run out
   of ranges, they encode a taxonomy that will be wrong in five years, and they will burn two weeks of
   your six. Emit a **checksum-bearing opaque ID** plus classification/attributes as data.
   You can *display* a classification prefix for human comfort; do not make it part of identity.
2. **Copy INC: an approved-item-name dictionary.** Your canonical noun-phrase vocabulary. This is the
   single highest-leverage artefact you can build in Phase 1 — a curated list of ~300–800 approved item
   names for refinery MRO, each with synonyms/abbreviations. Everything downstream (classification,
   normalisation, attribute extraction, search) hangs off it.
3. **Copy FIIG: per-item-name attribute templates.** For item name "BOLT, MACHINE" the mandatory
   attributes are {thread series, nominal thread diameter, thread length, head style, material,
   finish, standard}. For "VALVE, BALL": {nominal size, pressure class, body material, trim material,
   end connection, operation, port}. This is *the* mechanism that solves your `M10x50 vs M10x75`
   problem, and it solves it **deterministically**, not statistically.
4. **Copy MRC: stable attribute IDs.** Give every attribute a permanent code (e.g. `ATTR.THRD.DIA`)
   with a datatype, a canonical unit, an enum domain where applicable, and a *discriminating weight*.
   Your explainability table (brief §8) is then a join over MRC codes, not free-form text. This makes
   the XAI panel trivially implementable *and* auditable.
5. **Copy the two-method model — build BOTH matchers.**
   - **Reference matcher**: normalised manufacturer + normalised part number / drawing number.
     Exact or near-exact match on a normalised MPN is near-certain identity.
   - **Descriptive matcher**: item name + attribute vector.
   Then fuse. **This is the single biggest correction to your brief's architecture.** See §10, Myth 3.
6. **Copy the "codification is a service with a national bureau" framing** for your governance and RBAC
   design. Central authority mints the code; member organisations submit; the bureau adjudicates. That
   maps 1:1 onto your central-admin / CPSE-admin / reviewer roles and gives your workflow a real-world
   pedigree instead of a made-up one.

### 4.5 India's status in NCS

India participates as a **Tier 2 sponsored partner** of the NATO Codification System, with **NCB (India)**
run by the Directorate of Standardisation, Department of Defence Production. Tier 2 implies a
nationally-certified NCS-compliant system, two-way data exchange, and participation in AC/135 Panel A
technical work.

[VERIFIED that NCB (India) exists and hosts NCS material —
https://ddpdos.gov.in/ncb-india/nato-codification/codification-system and
https://ddpdos.gov.in/sites/default/files/2017-10/NCS_guide_en.5-17.pdf ]
[The **Tier 2** designation specifically: reported in NSPA/DLA tier charts
(https://eportal.nspa.nato.int/ac135/data/pdf/NCS_codes_chart.pdf) and secondary sources.
**UNVERIFIED at the level of "India = Tier 2 as of 2026" — verify by** fetching the current NCS tier
chart PDF from the NSPA eportal and finding India in it. **Do not state India's tier on a slide until
you have that PDF open.**]

**[JUDGMENT]** One line in your pitch: *"India already operates a NATO-compliant codification bureau for
defence. SIH26099 is asking for the civil-industry equivalent. We are building the reference
architecture for it, borrowing NCS's proven separation of identity, classification and characteristics."*
That is a strong, true, checkable claim.

---

## 5. Classification & data-quality standards

| Standard | What it is | Free? | Usable as your backbone? |
|---|---|---|---|
| **UNSPSC** | 4-level, 8-digit hierarchy (Segment/Family/Class/Commodity) for products & services, owned by UNDP | Codeset **use is free**; a **PDF** of the current version is downloadable by non-subscribers; **Excel** requires purchase or subscription | Good for **category** labels. Weak for MRO attributes — it classifies, it does not describe. |
| **ECLASS** | ~**48,000 product classes**, **>23,000 properties**, 4-level, 8-digit code | Free **browsing/search** only. Full dataset needs a **Single / Concordance / Pay-per-IRDI licence or association membership**, priced by company size | Technically the best fit for industrial MRO attributes. **Licensing makes it unusable for a hackathon prototype you might open-source.** |
| **ISO 8000** (esp. -110, -115, -116) | Master data quality: -110 = exchange of characteristic data (syntax, semantic encoding, conformance to a data specification); -115 = quality identifiers (syntactic, semantic and resolution requirements) | ISO standards are **paid** | Use as a **conformance vocabulary and design frame**, not as data. Cite it for your quality-score design. |
| **ISO 22745** | Open technical dictionaries; XML encoding of item descriptions that is application-independent | Paid standard; the **dictionary it points to (eOTD) is free** | Yes — as the conceptual model for "class + property + value + unit, all identified by stable concept IDs". |
| **ECCMA eOTD** | ISO 22745-compliant **open technical dictionary**: classes (approved item names), properties, units of measure, currencies, enumerated values. ECCMA states **concept identifiers are in the public domain** and describes eOTD as free to use | **Free** to use / free identifier resolution web services | **Strongest free candidate for your attribute backbone.** |
| **GS1 GPC** | Segment → Family → Class → **Brick** → Brick Attribute; GPC Browser is public and offers Excel/XML schema download | Free public browser + published standards | Good, but retail/CPG-oriented. Poor MRO coverage. |

Sources [VERIFIED]:
- UNSPSC: https://www.unspsc.org/faqs (states codeset use is free and embeddable), and the
  non-subscriber quick-start guide https://www.unspsc.org/content/dam/unspsc/unspsc-qsg-codeset-download-nonsubscribers.pdf ;
  downloads page https://www.unspsc.org/codeset-downloads . *Note*: unspsc.org's FAQ page returned
  unrelated content through one fetch path — **verify the exact free/paid split yourself before relying on it.**
- ECLASS counts and licence tiers: https://eclass.eu/en/eclass-standard/introduction and
  https://eclass.eu/en/eclass-standard/licenses (Single licence, Concordance licence, Pay-per-IRDI,
  association membership includes all licences; prices tiered by company size, published in a separate PDF).
- ISO 8000 parts / ISO 22745 / ECCMA role: https://eccma.org/what-is-iso-8000/ and
  https://en.wikipedia.org/wiki/ISO_8000
- eOTD: https://eccma.org/eotd-eccma-open-technical-dictionary/ (states "public domain concept
  identifiers", "free identifier resolution … (web services)", and cites *around 2,000,000 records*;
  a separate ECCMA page cites *over 400,000 concepts* of class/property/UoM/currency/enumerated value —
  **the two figures disagree; do not quote either without re-checking**). Live search UI:
  https://www.eotd.org/ (HTTP 200 confirmed this session).
- GS1 GPC: https://gpc-browser.gs1.org/ (HTTP 200 confirmed), https://www.gs1.org/standards/gpc/get-started

**[JUDGMENT] Recommendation for the backbone:**

Do **not** adopt any single external taxonomy as your master schema. Instead:

- **Your own item-name dictionary (INC-style)** is the primary key of classification — ~300–800 names,
  hand-curated for refinery MRO, each with a FIIG-style attribute template. This is the thing you own,
  it is small enough to build in 2 weeks, and it is what makes your demo actually work.
- **Map** each item name to **UNSPSC commodity code** (free, universally recognised, gives you an
  8-digit category everyone in procurement knows) and, where a mapping exists, to **eOTD concept IDs**
  (free, ISO 22745, gives you standards credibility and a public-domain identifier to cite).
- Mention ECLASS as the "production-grade path when a licence is procured." Do not ship it.
- Cite ISO 8000-110/-115 as the conformance frame for your data-quality score and your identifier design.

This gives you *"standards-anchored, licence-clean"* — a strong answer to the inevitable judge question
"why not just use UNSPSC / ECLASS?"

---

## 6. Commercial competitive landscape

This market exists, is mature, and is worth real money. **Pretending otherwise will get you destroyed
in Q&A.** Address it head-on.

### 6.1 Who sells this

| Vendor | Product | Verified claims |
|---|---|---|
| **Verdantis** (India-founded, MRO-focused) | **Harmonize** (bulk cleansing/normalisation of historical data from ERP migrations & multi-site) + **Integrity** (ongoing governance: business rules, validation, change workflow). Also markets *MRO Data Cleansing* services and UNSPSC-based governance | Claims algorithms that identify duplicates despite spelling errors, abbreviations and multiple languages; "L1 and L2 duplicates" flagged; semantic/attribute-based search; "Agentic AI" for extraction from engineering documents, spare-part identification across vendor catalogues, multilingual localisation, AI attribute enrichment. **Pricing not published.** [VERIFIED — https://www.verdantis.com/harmonize/ , https://www.verdantis.com/integrity/ , https://www.verdantis.com/mro-data-cleansing/ , https://www.verdantis.com/materials-master-data-management/ ] |
| **Prospecta** | **MDO** — SAP-certified AI master data platform for Material Master, Business Partner, EAM, Finance, Reference Data; "KAI" agentic AI steward; Data Intelligence Workbench (DIW) + XFuse for pre-S/4HANA remediation | [VERIFIED — https://www.prospecta.com/mdo/ , https://www.prospecta.com/mdo-sap , https://www.prospecta.com/mdo-mro-data/ ] |
| **SPARETECH** | MRO/spare-parts master data; duplicate finding against a manufacturer-data reference database | [VERIFIED — https://sparetech.io/mro-master-data-management/master-data-cleansing , https://sparetech.io/en/blog/find-and-remove-duplicates-material-master ] |
| **Verusen** | AI for duplicate MRO material identification across complex enterprises | [VERIFIED — https://verusen.com/mro-data-master-data/how-ai-identifies-duplicate-mro-materials-across-complex-enterprises/ ] |
| **SAP MDG** | SAP's own Master Data Governance, incl. duplicate check via Data Quality Management | **[ASSUMPTION]** — I did not fetch SAP documentation this session. **Verify by** reading help.sap.com on MDG-M duplicate check before describing it. |
| **Informatica MDM, Stibo Systems, Enterworks, Aptean, Innovapptive, OptimizeMRO, ShareCat, ai2coe** | General MDM / PIM / MRO data services | Existence VERIFIED via search-result titles only; **capabilities and pricing UNVERIFIED — verify individually** before naming any of them in a comparison slide. |

Note also **EY** publishes an MRO material-master transformation case study
[VERIFIED that the page exists — https://www.ey.com/en_us/insights/energy-resources/oil-gas/transforming-mro-material-master-data-case-study ;
contents not read this session].

### 6.2 Their common technique stack

**[JUDGMENT], inferred from public marketing language — not from any vendor's engineering docs:**
rules + dictionaries + fuzzy/phonetic matching + a reference manufacturer database + increasingly
LLM/embedding-based extraction, wrapped in workflow and ERP connectors. The **reference manufacturer
database is the real moat** — Verdantis, SPARETECH and Verusen all lean on having tens of millions of
OEM part records to match against. You cannot replicate that.

### 6.3 The honest gap you can claim

**Do not claim you beat Verdantis on matching quality.** You cannot measure that and it is probably false.

Claim these instead — each is true and none requires a benchmark you cannot run:

1. **Cross-organisational, not intra-organisational.** Every commercial tool cleanses *one enterprise's*
   master (or migrates it to S/4HANA). None of them mints a **shared national identity across
   independently-governed enterprises with a central adjudicating authority and per-CPSE sovereignty
   over its own codes.** That federated-identity + custody model is the genuinely novel part, and it is
   exactly what the PS asks for.
2. **Licence-clean and sovereignty-preserving.** Commercial MDM is proprietary, often SaaS, often
   US/EU-hosted. A national CPSE material master is arguably sensitive procurement data. An
   open, self-hostable, air-gap-capable reference implementation with local model inference is a real
   differentiator for a government buyer.
3. **Explainability as a first-class artefact, not a confidence number.** Attribute-by-attribute
   evidence tables tied to stable attribute codes, versioned model IDs, and an append-only decision log
   — because a public-sector merge decision must survive audit. Vendors sell confidence scores; the CAG
   wants reasons.
4. **Zero-cost to a CPSE that wants to try it.** No licence negotiation to run a pilot.

### 6.4 Data-quality statistics — handle with tongs

Widely-cited figures such as *"10–20% of MRO stock in multi-site networks is duplicated"* and
*"duplicate purchases run 5–7% of MRO spend"* come from **vendor marketing and vendor-run surveys**
[seen at https://verusen.com/... , https://reliamag.com/guides/mro-spare-parts-inventory-statistics/ ,
https://sparetech.io/... — none of these is a peer-reviewed or government source].

**Rule for the team: if you use any of these numbers, cite the vendor by name on the slide and say
"vendor-reported".** Never present them as measured facts about Indian CPSEs. A judge from CPCL knows
their own duplicate rate and will not enjoy hearing a made-up one. Better: show the duplicate rate
*measured on your own demo corpus*, clearly labelled as demo data.

ECCMA publishes an annual "Procurement Master Data Quality Analysis"
[VERIFIED that the PDF exists at
https://eccma.org/wpeccma/wp-content/uploads/2024/12/2024-12-18-ECCMA-Procurement-Master-Data-Quality-Analysis-2025.pdf
— I could not extract its text this session (image-based PDF). **Verify by** opening it manually if you
want a non-vendor-marketing statistic.]

---

## 7. Literature

Everything below is a **real paper** — I confirmed title, authors and venue this session. I have **not**
reproduced benchmark numbers except where the search result stated them; treat any figure as
"verify against the PDF before quoting."

| Work | Why it matters to you |
|---|---|
| **Ditto — "Deep Entity Matching with Pre-Trained Language Models"**, Li, Li, Suhara, Doan, Tan. **PVLDB 13(12), 2020**. arXiv:2004.00584, https://arxiv.org/pdf/2004.00584 , DOI 10.14778/3421424.3421431 | The reference architecture for transformer-based entity matching: serialise the pair, fine-tune as sequence-pair classification, plus domain-knowledge injection (span highlighting) and string summarisation for long inputs. **This is your cross-encoder stage.** The "inject domain knowledge by highlighting spans" trick maps directly onto highlighting extracted attribute spans. |
| **DeepMatcher — "Deep Learning for Entity Matching: A Design Space Exploration"**, Mudgal et al., **SIGMOD 2018** | The pre-transformer baseline and the standard framing of the EM design space. Cite as the lineage. |
| **"Supervised Contrastive Learning for Product Matching"**, Peeters & Bizer. https://arxiv.org/pdf/2202.02098 | Contrastive training for product entity matching — directly relevant to your bi-encoder retrieval stage and your positive/negative pair strategy. |
| **WDC Products** benchmark, Univ. Mannheim. https://webdatacommons.org/largescaleproductcorpus/wdc-products/ | **[VERIFIED]** 11,715 product offers / 2,162 entities, extracted 2020 from 3,259 e-shops via schema.org markup; 27 variants across corner-case ratio (80/50/20%), unseen-entity ratio (0/50/100%) and dev-set size; pair-wise and multi-class formulations; direct zip downloads listed on the page (e.g. `80pair.zip` ~21.5 MB). **No licence stated on that page — verify before redistributing.** Consumer products, not MRO — useful as a *methodology* sanity-check dataset, not as your domain corpus. |
| **"Text-Based Product Matching — Semi-Supervised Clustering Approach"**, arXiv:2402.10091 | Relevant if you go the clustering route rather than pairwise. |
| **"Multilingual Transformers for Product Matching"**, arXiv:2205.15712 | Relevant to your multilingual/transliteration concern. |
| **"Entity Matching using Large Language Models"**, arXiv:2310.11244 ; **"Cost-Efficient Prompt Engineering for Unsupervised Entity Resolution"**, arXiv:2310.06174 ; **PromptEM**, arXiv:2207.04802 | The honest state of LLM-based EM — read these *before* deciding where an LLM belongs, so you can defend "we use the LLM here and deliberately not there." |
| **ROTOM** (meta-learned data augmentation for EM and data cleaning) | Directly relevant to your §6 augmentation strategy. **UNVERIFIED citation details — verify by** searching for the ROTOM paper (SIGMOD 2021, Miao et al.) before citing. |

**[JUDGMENT] The gap in the literature that is genuinely yours:** almost all product-matching research
is on **consumer e-commerce offers** with brand + model number + rich text. **Industrial MRO short-text
matching with hard numeric-specification constraints and a "wrong match is a safety event" cost
asymmetry is materially under-studied.** You can say that honestly. What you cannot say is that nobody
has built a system for it — see §6.

---

## 8. Data acquisition — the reality

The PS's dataset is a promise, not a file (§1.3a). Here is the honest ranking of what you can actually get.

### 8.1 Verified-usable now

| Source | What | Status |
|---|---|---|
| **GSA National Stock Number Extract** (data.gov) | **[VERIFIED — I downloaded it this session.]** XLSX, ~989 KB, **12,455 rows including header (12,454 items)**, columns: `NSN, rep_office, common_name, Description, Price, UI, AAC`. Licence stated on the catalog page as **CC0 / public domain**. Direct file: https://inventory.data.gov/dataset/67567804-073d-40ad-a710-2b0bed8b84e2/resource/3b7ed6b7-7dce-42f1-852d-6465e3e790e4/download/nsn-extract-2-21-23.xls.xlsx (catalog page: https://catalog.data.gov/dataset/national-stock-number-extract) | Real, small, prose-y descriptions, GSA-consumer-flavoured. Useful for the **NSN/FSC structure demo** and as a small real corpus. **Not** a substitute for MRO data. |
| **WDC Products** | 11,715 offers / 2,162 entities, see §7 | Real, free, method benchmark only. |
| **UNSPSC codeset (PDF)** | Free for non-subscribers | Category backbone. |
| **eOTD** | Free ISO 22745 dictionary, public-domain concept IDs | Attribute/class backbone. Web search UI confirmed live. **Bulk download availability UNVERIFIED — verify by** emailing ECCMA or testing their web services. |
| **GS1 GPC** | Free browser + published Excel/XML schemas | Secondary category mapping. |

### 8.2 Large and free but unverified access path

**DLA PUB LOG (Public Logistics Data)** — publicly-releasable FLIS data: NSN records, Federal Supply
Classification data, CAGE code listings, **decoded characteristics data**, and MCRL (Master Cross
Reference List). Described as free, updated monthly, no CAC or subscription, distributed via the
"FLIS Data Electronic Reading Room."
[Sources: https://www.dla.mil/Portals/104/Documents/J3LogisticOperations/Brochures/J3_PUB%20LOG%20Brochure_240126.pdf
and https://www.dla.mil/Working-With-DLA/Applications/Details/Article/2897071/pub-log-public-logistics-data/ ]

**Both dla.mil pages returned HTTP 403 to my fetcher this session, and
`public.logisticsinformationservice.dla.mil` returned 403.**

> **UNVERIFIED — verify by**: opening https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/
> in a normal browser from an Indian IP, and attempting an actual download. **If PUB LOG's decoded
> characteristics data is downloadable, it is by far the best training corpus available to you** — it
> is literally item-name + MRC-coded attribute-value pairs for millions of industrial items, i.e.
> exactly the structure this project needs, in the public domain. **If it is US-IP-restricted, you must
> know that in week 1, not week 5.** Assign this to one person on day one.

### 8.3 Real Indian CPSE material data hiding in plain sight

**[VERIFIED — I downloaded and parsed one this session.]** Indian CPSEs publish tender enquiry documents
containing **live material master rows**: material code, item description, drawing number, quantity, unit.

Example confirmed: a BHEL Haridwar open tender PDF hosted by the Indian Embassy in Bern —
https://www.indembassybern.gov.in/content/1704361338_2567_E.pdf — whose table header is literally
`SL | MATERIAL CODE | ITEM DESCRIPTION | QUANTITY | UNIT | LOT QTY | DELIVERY SCHEDULE` and whose rows
read e.g.

```
W973105250 43   2  NO   ...  DRG: 010525 5634 1  REV: 04   PISTON RING   MATERIAL: COCR20W15NI
W973105250 51   2  NO   ...  DRG: 310525 5634 2  REV: 04   SPRING RING   MATERIAL: NICR20CO18TI
W973105250 60   4  NO   ...  DRG: 410525 5605 1  REV: 02   SPRING RING   MATERIAL: ~X10CRNI18-8
```

This single sample already demonstrates the domain's real texture: **noun-modifier item names, a
`MATERIAL:` attribute embedded in free text, and a drawing number as the true identity anchor.**
Note that the "description" is *not* a clean spec string — it is a multi-line blob.

**Where to harvest more** (all public, no login for the documents themselves):
- ONGC: https://tenders.ongc.co.in/ and https://etender.ongc.co.in/ ; ONGC tender booklets & the
  *Integrated Materials Management Manual* at
  https://www.ongcindia.com/wps/wcm/connect/en/about-ongc/interface/material-management/tenders-booklets/tenders-booklets
- Central Public Procurement Portal: https://etenders.gov.in/eprocure/app (ONGC now publishes here)
- IREPS (Indian Railways e-procurement, CRIS-operated): https://www.ireps.gov.in/ — Railways use
  **PL numbers** as material codes. **[ASSUMPTION]** that PL-numbered stores tenders with descriptions
  are publicly downloadable. **Verify by** browsing IREPS stores tenders directly.
- BHEL unit sites (e.g. bhelhwr.co.in), SAIL, NTPC, GAIL e-procurement portals.

**Legal/ethical rules you must follow and must state in your deck:**
- These are **published tender documents**, intended for public bidder consumption. Reading them is fine.
- **Respect robots.txt and terms of use on each portal. Do not hammer government servers.** Rate-limit
  hard (≤1 request/second), identify your user-agent, and cache.
- **Do not** attempt to access anything behind a login, and do not use scraped vendor names or prices
  in any published artefact.
- **Do not** claim in your pitch that you "have CPSE material master data." You have *tender line items*.
  Say exactly that. **[JUDGMENT]** Being precise here is a credibility *asset*, not a weakness.

### 8.4 Synthetic data — necessary, and must be labelled

You will not obtain 50,000 real cross-CPSE records. **Plan a hybrid corpus and label every row's
provenance in the database** (`provenance: REAL_TENDER | REAL_PUBLIC_CATALOG | SYNTHETIC_VARIANT | HAND_CURATED`).
Show that column in the UI. Judges respect it; the alternative (getting caught) is fatal.

**[JUDGMENT] on generation strategy** — detailed design belongs to the ML agent, but two domain
constraints must be honoured:
- Variants must be generated **from a canonical attribute record downward**, never by perturbing
  strings blindly. Generate the attribute set, then render it through N different "CPSE house style"
  templates (abbreviation dictionary, attribute ordering, unit style, separator style, 40-char truncation).
  This guarantees the positive label is correct by construction.
- **Hard negatives must be generated by perturbing exactly one discriminating attribute** (M10→M12,
  50mm→75mm, SS316→SS304, PN16→PN40, bolt→nut), keeping every other token identical. Those are the
  pairs that a plain embedding model gets wrong and that your judges will test live.

---

## 9. SAP/ERP integration — what "integration capability" should mean in a 6-week prototype

The PS asks for it (capability 11). **[JUDGMENT] Do not attempt real SAP integration.** You have no SAP
system, no licence, and no time. What you *can* deliver, and what a CPCL judge will accept:

1. **A documented integration contract**, not code: define the inbound material extract (SAP:
   MARA+MAKT+MARC+MARM join, or an LTMC/LSMW-style flat file; Oracle: `MTL_SYSTEM_ITEMS_B` +
   `_TL` extract) and the outbound mapping feed.
2. **Two concrete outbound mechanisms named correctly**: (a) an **OData / REST** service for
   synchronous "does this material already exist?" checks at creation time — this is the hook for
   capability 12/15 in your brief; (b) a **batch mapping file** (CPSE code → NMC ID) for
   `MARA-BISMT`/custom-Z-field write-back or an SAP Classification (CLASS/CABN/AUSP) load.
   Mentioning **IDoc `MATMAS`** as the classical alternative shows you know the landscape.
   **[ASSUMPTION on MATMAS naming — verify by** a quick check of SAP help before you say it aloud.**]**
3. **A mock ERP** in your demo: a tiny "CPSE-B SAP" screen that posts a new material to your
   `POST /match` endpoint and gets back "possible existing material NMC-0001842, 0.94". That *shows*
   integration without faking it.

Say on the slide: *"Integration-ready, not integrated. Here is the contract; here is a working mock;
real connector is a post-prototype engagement."* Honest and unattackable.

---

## 10. MYTHS IN THE BRIEF

These are things the brief gets wrong or misses about the *domain*. Architecture/ML critiques belong to
the other Phase 0 agents; these are domain-truth corrections.

### Myth 1 — "Fasteners are a good representative example."
The brief's running example is `SS HEX BOLT M10 X 50`. **Fasteners are the easiest possible case** —
fully parameterised by a public standard (DIN/ISO/ASTM), tiny attribute set, no OEM identity, no
certification. Building and demoing only on bolts will look naive to a refinery panel. **Your demo needs
at least 5–6 commodity families of graded difficulty**: fasteners (easy) → pipes/flanges/gaskets
(medium, standards-driven: NPS, schedule, pressure class, facing) → valves (harder: size + class +
body/trim material + end connection + operation) → bearings (OEM-number-driven: `6205-2RS` vs `6205 2RS C3`)
→ electric motors (kW + frame + pole + mounting + enclosure + hazardous-area cert) → instrumentation
(range + output + process connection + certification). **A judge will ask "what about valves?" Have the answer.**

### Myth 2 — "Fuzzy string matching is unreliable; embeddings are the answer."
Half-right, and the wrong lesson. Fuzzy matching is unreliable **as a decision rule**. It is excellent
**as a cheap recall-oriented blocker** and it will be a strong baseline you must beat honestly.
More importantly: **the winning system is not "better text similarity", it is "stop comparing text."**
The correct pipeline converts free text into `(item_name, {attribute → normalised value + unit})` and
then compares **structured records with typed, per-attribute rules**. Text similarity is a *retrieval*
mechanism; attribute agreement is the *decision* mechanism. Your brief's stage list gets close to this
but still treats "Hybrid Scoring" as a blend of two similarity numbers. It should be: retrieval by text
+ **decision by attribute logic with learned weights**, where a mismatch on a *discriminating* attribute
is a **hard veto**, not a score penalty.

### Myth 3 — the brief has **no manufacturer part number or drawing number anywhere in it.** ⚠️
This is the most serious domain omission in the brief. In real MRO masters, the strongest identity
signal is not the description — it is **manufacturer + manufacturer part number**, and for
fabricated/engineered items, **drawing number + revision**. NCS formalises this as the **reference
method of identification** (§4.3), and the BHEL tender sample in §8.3 shows `DRG: 0105255634 1 REV: 04`
sitting right next to the description in real Indian CPSE data.
**Add to the data model and to the matcher:**
- `manufacturer_name_raw`, `manufacturer_normalised`, `mpn_raw`, `mpn_normalised` (strip separators,
  case-fold, strip common suffixes), `drawing_number`, `drawing_revision`, `vendor_catalog_ref`.
- A **reference matcher** that fires before the descriptive matcher. Normalised-MPN equality between
  two records from different CPSEs is close to proof of identity — and it produces a spectacular demo
  moment because it catches duplicates whose *descriptions share almost no words*.
- Note the trap: **drawing-number equality with different revisions is NOT identity** (`REV: 02` vs
  `REV: 04` may be a genuinely different part). Model revision explicitly.

### Myth 4 — "Unit normalisation = unit conversion."
Dimensional conversion (mm↔inch, kg↔lb, bar↔psi) is the easy 20%. The real UoM problem in a material
master is **issue-unit and pack-size semantics**: `EA` vs `NO` vs `PC` vs `NOS` vs `U` all mean "each";
`SET` / `PR` (pair) / `BOX` / `PKT` / `RL` (roll) / `MTR` / `RMT` are *quantities of an item*, not the
item. Two records differing only in `EA` vs `BOX-100` are **the same material with different stocking
conventions** — which is exactly the kind of duplicate you should catch and exactly the kind your brief's
"unit conversion" framing would miss. Build a **UoM synonym + packaging-semantics table** (SAP `MARM`
holds the alternative-unit conversion factors, which is where a real system would look).

### Myth 5 — "Functionally equivalent" is a safe output class.
In petroleum refining, declaring two items interchangeable has **statutory and safety consequences**:
pressure class (ASME B16.5), material certification (ASTM/NACE MR0175 for sour service), hazardous-area
certification (ATEX/IECEx/PESO), fire-safe design, OEM warranty. **A system that autonomously asserts
functional equivalence is a liability, and a CPCL judge will spot it.**
**Rename the class.** `EQUIVALENCE_CANDIDATE — requires engineering review`, never
`FUNCTIONALLY EQUIVALENT`. Make the UI refuse to auto-approve it at any confidence. Make that refusal a
**feature you demo on purpose**: *"the AI is deliberately not allowed to make this call."* That single
design decision converts your biggest weakness into your most mature-sounding slide.

### Myth 6 — "Preserve original CPSE codes" is a footnote.
It is the **central political requirement**, and it should shape the data model, not be a column.
No CPSE will surrender its material numbering — it is embedded in decades of purchase orders, contracts,
stock records, drawings and vendor systems. The PS says so explicitly ("while maintaining traceability
to individual CPSE material codes"). The model is **federated identity**: NMC ID is an *additional*
identity layer with a **many-to-one mapping table carrying its own lifecycle** (proposed → approved →
superseded → retired), never a replacement. Also: **the mapping must be reversible and versioned**, and a
CPSE must be able to *dispute and unmap*. Build the unmap path. Nobody else will, and it is the first
thing a materials manager will ask about.

### Myth 7 — "Generate a Common National Material Code" means designing a clever code format.
No. See §4.4.1. **Non-significant opaque identifier + separate classification attributes.** If you spend
a week designing a 14-digit semantic national code you have spent a week on the least valuable artefact
in the project. Format proposal, and then stop thinking about it:
`NMC-<8 digits>-<1 check digit>` (e.g. `NMC-00018426`), with UNSPSC commodity code and item-name code
carried as *attributes*, displayed alongside.

### Myth 8 — the brief's scope is roughly 3× the problem statement.
The PS lists 11 capabilities. The brief lists ~35 sections including a supplier relationship graph,
procurement intelligence with cost-saving estimates, six RBAC roles, notifications & alerts, malware
scanning, multilingual descriptions, and a material relationship graph.

**CUT LIST — build none of these before the matcher and the master are excellent:**

| Cut | Why |
|---|---|
| **Supplier / procurement relationship graph (§16)** | You have no supplier data and no legal way to get reliable supplier–material links. A graph over data you invented is a graph of nothing. If you want the visual, render the *material↔CPSE↔code* mapping as a graph — that data is real (it's your own mapping table) and needs no graph database. |
| **Neo4j / any graph DB** | Your graph is a 3-level star. Postgres + a recursive CTE renders it. Adding a second datastore costs a week and buys a logo on a slide. |
| **Procurement intelligence / cost-savings analytics (§17)** | Without real procurement volumes and prices, every number is fabricated. The brief already warns about this — take your own warning seriously and **cut the module**, keeping only "aggregation opportunity: N CPSEs hold this material" which is computable from your own mapping table and is honest. |
| **Notifications & alerts (§21)** | Pure plumbing, zero demo value. A "pending approvals" count on the dashboard is sufficient. |
| **Six RBAC roles (§22)** | Build **three**: `central_admin` (mints/approves NMC), `cpse_reviewer` (approves mappings for own CPSE), `viewer`. Auditor = viewer + audit page. |
| **Malware scanning, rate limiting, secrets management (§28)** | Document them in the security architecture. Do not implement. |
| **Multilingual descriptions** | Indian CPSE material masters are overwhelmingly English (often with Indian-English/Hinglish abbreviations and transliterated vendor names). **[ASSUMPTION — verify by** looking at any real CPSE tender line items you harvest.**]** Handle *abbreviations and transliteration noise*, not translation. Cut the multilingual model. |
| **Cryptographic / blockchain audit trail (§19)** | The brief already asks whether it's actually useful. **[JUDGMENT] It is not, for this problem.** An append-only Postgres table with a per-row `prev_hash` chain gives you tamper-evidence in ~30 lines and is defensible as "hash-chained append-only ledger". A blockchain adds a distributed-consensus solution to a problem with a single trusted central authority — which is the *definition* of an unnecessary blockchain. Say this out loud in your deck; judges have started to reward that answer. |
| **"Scalable to millions" as an engineering deliverable** | It is an *architecture* deliverable. Show the ANN index, the batching, the blocking strategy and one benchmark at your real corpus size, plus a costed extrapolation. Do not build for millions. |

### Myth 9 — "Demo numbers must be clearly labelled as demo data" is sufficient disclosure.
It is necessary, not sufficient. **Label provenance per record, not per dashboard.** A judge will click
into a material. If the detail page says "Source: synthetic variant, generated from canonical
NMC-00018426", you have won a credibility point at the exact moment other teams lose one.

### Myth 10 — the brief never mentions the 40-character constraint, noun-modifier naming, or
`MARA-BISMT`.
All three are core domain mechanics (§2.1, §2.3). Their absence is the clearest signal that the brief
was written from first principles rather than from the material-master domain. Fix that in Phase 0 and
the whole document reads differently.

---

## 11. WHAT THIS MEANS FOR THE TEAM

Concrete, costed against 6–10 weeks × 4–6 part-time people.

### 11.1 The five decisions that determine whether you win

1. **Adopt the NCS model explicitly**: approved item names (INC-style) + per-name attribute templates
   (FIIG-style) + stable attribute codes (MRC-style) + non-significant national ID + dual
   reference/descriptive identification. It is a real national system, India already runs one for
   defence, and it gives you a defensible answer to every "why did you design it that way?" question.
   *Cost: ~1 week of one person to define the model; the dictionary build is ongoing.*
2. **Build the item-name dictionary and attribute templates for 6 commodity families before any model
   training.** ~300–500 approved item names, ~150–250 attributes with canonical units and enum domains,
   ~1,500–3,000 abbreviation/synonym entries. This is boring, unglamorous, and it is the actual product.
   *Cost: 2 people × 2 weeks, heavily AI-assisted. This is where Claude earns its keep.*
3. **Add MPN / drawing number to everything** (Myth 3). *Cost: near zero if done now, expensive later.*
4. **Make attribute mismatch a veto, not a score** (Myth 2). Per-attribute `discriminating: bool` in the
   template. `M10x50` vs `M10x75` must be structurally impossible to call a duplicate. Demo this.
   *Cost: a day, and it is your single most persuasive live demo moment.*
5. **Rename FUNCTIONALLY_EQUIVALENT → EQUIVALENCE_CANDIDATE and refuse to auto-approve it** (Myth 5).
   *Cost: zero. Value: high.*

### 11.2 Data plan (assign in week 1)

| Owner | Task | Deadline |
|---|---|---|
| Person A | **Confirm SIH26099 text on sih.gov.in.** Ask the PS contact channel whether the CPSE sample dataset will actually be released, and by when. | Day 2 |
| Person A | **Test DLA PUB LOG download from India.** Binary outcome, changes everything. | Day 3 |
| Person B | Harvest 300–1,000 real material line items from public CPSE tender PDFs (BHEL/ONGC/IOCL/Railways), rate-limited, provenance-tagged. This is your **real** evaluation set. | Week 2 |
| Person B | Download GSA NSN extract (verified working), UNSPSC PDF codeset, GS1 GPC schema; evaluate eOTD bulk access. | Week 1 |
| Person C | Build the canonical item-name + attribute-template dictionary for 6 families. | Weeks 1–3 |
| Person C | Build the synthetic variant generator **from canonical records downward** with per-CPSE house styles + 40-char truncation + hard negatives. | Weeks 3–4 |

**Target corpus shape** (state this honestly everywhere): ~500–2,000 **real** harvested records used as a
held-out evaluation set with **hand-labelled** duplicate pairs (this is the number that matters and it
should be *small and real*), plus 20,000–50,000 **synthetic** records for training, generated from
~2,000–5,000 canonical seeds. **Do not train on your real evaluation set.** Report metrics separately
for real vs synthetic — the real number will be lower, and reporting both is what a serious team does.

### 11.3 Demo commodity families (recommended)

| Family | Why it earns its place |
|---|---|
| Fasteners | The clean textbook case; establishes the mechanism |
| Pipes / flanges / gaskets | Standards-driven, NPS+schedule+class+facing — shows engineering-attribute handling |
| Valves | The family a refinery judge cares about; multi-attribute, high consequence |
| Bearings | Shows the **reference method** — `6205-2RS` matching across totally different descriptions |
| Electric motors / cables | Shows hazardous-area certification as a **veto** attribute |
| Lubricants / chemicals | Shows brand-vs-spec equivalence and why you *refuse* to auto-equate |

### 11.4 Framing for the pitch (all claims here are checkable)

- **The gap**: India has a NATO-compliant national codification bureau for defence materiel; there is no
  civil-CPSE equivalent. (§3.5, §4.5)
- **The mechanism**: duplicates are a *search failure* caused by a 40-character description field and
  decentralised code creation. (§2.1, §2.3)
- **The design**: identity ≠ classification ≠ characteristics; non-significant national ID; federated
  custody where CPSEs keep their own codes forever. (§4.4, Myth 6)
- **The discipline**: attribute vetoes, no auto-approved equivalence, provenance on every record,
  hash-chained audit, honest metrics on a small real held-out set.
- **The gap vs vendors**: cross-organisational federated identity + sovereignty + explainability, not
  "better matching than Verdantis". (§6.3)

### 11.5 The three questions you will be asked, and the answers you need ready

1. *"Where did your data come from?"* → provenance column, live, on screen. Real tender line items +
   labelled synthetic. Never bluff.
2. *"What about valves / motors / instruments — not just bolts?"* → six families, demo two live.
3. *"Verdantis and Prospecta already sell this. Why you?"* → §6.3, verbatim.

---

## 12. Verification checklist — do these before anything is claimed publicly

| # | Claim | How to verify | Owner | Status |
|---|---|---|---|---|
| 1 | SIH26099 official text | sih.gov.in/sih2026PS, byte-compare with §1.2 | | ☐ |
| 2 | CPSE sample dataset will/won't be provided | Ask via the SIH PS channel | | ☐ |
| 3 | DLA PUB LOG downloadable from India, and its characteristics files | Browser + actual download | | ☐ |
| 4 | India's NCS tier status (Tier 2?) as of 2026 | NSPA NCS codes chart PDF, find India | | ☐ |
| 5 | eOTD bulk access + exact licence wording | ECCMA site / email ECCMA | | ☐ |
| 6 | UNSPSC free-vs-paid split (PDF free, Excel paid?) | unspsc.org codeset-downloads + the non-subscriber QSG | | ☐ |
| 7 | ECLASS licence cost for a student/OSS project | eclass.eu price PDF | | ☐ |
| 8 | WDC Products licence terms | webdatacommons.org page + any LICENSE in the zips | | ☐ |
| 9 | Number of operating CPSEs | DPE Public Enterprises Survey 2024-25 PDF | | ☐ |
| 10 | GeM product-category count | GeM annual report or category browser | | ☐ |
| 11 | Whether ONGC/IOCL/CPCL use MESC-derived codes | ONGC Integrated Materials Management Manual; tender-document code formats | | ☐ |
| 12 | SAP `MATMAS` IDoc / MDG duplicate-check naming | help.sap.com | | ☐ |
| 13 | robots.txt / ToS for every portal you harvest | each portal | | ☐ |
| 14 | Any prior SIH PS on material codification | sih.gov.in archives / SIH Kaggle dataset | | ☐ |
| 15 | ROTOM citation details | Google Scholar | | ☐ |

---

## 13. Source index

**Problem statement**
- https://raw.githubusercontent.com/vedantchalke36/sih-2026-problem-statements/main/ps_2026/SIH26099.md
- https://raw.githubusercontent.com/Sourav112-droid/sih-2026-problem-statements/main/data/sih-2026.json
- https://sih.gov.in/sih2026PS (authority — not fetched this session)

**ERP / material master**
- https://leanx.eu/sap/table/mara/
- https://userapps.support.sap.com/sap/support/knowledge/en/1630702 (MAKTX = CHAR 40, domain TEXT40)
- https://oraclebytes.com/mtl_system_items_b-columns-indexes-few-tricks/
- https://etrm.live/etrm-12.2.2/etrm.oracle.com/pls/trm1222/etrm_pnav27af.html

**NATO Codification System**
- https://eportal.nspa.nato.int/ac135/data/pdf/ACodP1_E.pdf (ACodP-1)
- https://ddpdos.gov.in/ncb-india/nato-codification/codification-system (NCB India)
- https://ddpdos.gov.in/sites/default/files/2017-10/NCS_guide_en.5-17.pdf
- https://ddpdos.gov.in/sites/default/files/documents/ACodP1_E_2019.pdf
- https://eportal.nspa.nato.int/ac135/data/pdf/NCS_codes_chart.pdf (tier chart)
- https://en.wikipedia.org/wiki/NATO_Stock_Number
- https://haystack.ihserc.com/help/haystack/webhelp/content/INC.htm (INC = 5 digits, 77777)
- https://www.iso-group.com/Information/MRC/ (MRC)
- https://www.parttarget.com/nsn_glossary.html
- https://www.dla.mil/Working-With-DLA/Federal-and-International-Cataloging/NATO/
- https://www.gov.br/caslode/pt-br/catalogacao/codsp/ACodP1_EJan2025.pdf (descriptive vs reference method)

**Standards / dictionaries**
- https://www.unspsc.org/codeset-downloads ; https://www.unspsc.org/content/dam/unspsc/unspsc-qsg-codeset-download-nonsubscribers.pdf
- https://eclass.eu/en/eclass-standard/introduction ; https://eclass.eu/en/eclass-standard/licenses
- https://eccma.org/what-is-iso-8000/ ; https://en.wikipedia.org/wiki/ISO_8000
- https://eccma.org/eotd-eccma-open-technical-dictionary/ ; https://www.eotd.org/
- https://gpc-browser.gs1.org/ ; https://www.gs1.org/standards/gpc/get-started
- https://law.resource.org/pub/in/bis/S08/is.8730.1997.pdf (IS 8730)

**India procurement context**
- https://gem.gov.in/ ; https://gem.gov.in/landing/index/Catalogue_Management
- https://www.dpe.gov.in/documents/reports/public-enterprises-survey-2024-25-cDO4IjMtQWa
- https://iocl.com/chennai-petroleum-corporation-limited ; https://cpcl.co.in/
- https://www.ongcindia.com/wps/wcm/connect/en/about-ongc/interface/material-management/tenders-booklets/tenders-booklets
- https://tenders.ongc.co.in/ ; https://etenders.gov.in/eprocure/app ; https://www.ireps.gov.in/
- https://www.indembassybern.gov.in/content/1704361338_2567_E.pdf (real BHEL material codes — parsed this session)
- https://www.verdantis.com/mesc-code/ ; https://panemu.com/blog/asset-management-24/mesc-code-the-backbone-of-material-and-equipment-standards-in-oil-and-gas-403

**Data sources**
- https://catalog.data.gov/dataset/national-stock-number-extract → https://inventory.data.gov/dataset/67567804-073d-40ad-a710-2b0bed8b84e2/resource/3b7ed6b7-7dce-42f1-852d-6465e3e790e4/download/nsn-extract-2-21-23.xls.xlsx (**downloaded, 12,454 items, CC0**)
- https://www.dla.mil/Information-Operations/FLIS-Data-Electronic-Reading-Room/ (403 this session)
- https://webdatacommons.org/largescaleproductcorpus/wdc-products/

**Vendors**
- https://www.verdantis.com/harmonize/ ; /integrity/ ; /mro-data-cleansing/ ; /materials-master-data-management/ ; /unspsc/
- https://www.prospecta.com/mdo/ ; /mdo-sap ; /mdo-mro-data/
- https://sparetech.io/mro-master-data-management/master-data-cleansing
- https://verusen.com/mro-data-master-data/how-ai-identifies-duplicate-mro-materials-across-complex-enterprises/
- https://www.ey.com/en_us/insights/energy-resources/oil-gas/transforming-mro-material-master-data-case-study

**Literature**
- https://arxiv.org/pdf/2004.00584 (Ditto) ; https://dl.acm.org/doi/10.14778/3421424.3421431
- https://arxiv.org/pdf/2202.02098 (Supervised Contrastive Learning for Product Matching)
- https://arxiv.org/pdf/2402.10091 ; https://arxiv.org/pdf/2205.15712 ; https://arxiv.org/pdf/2310.11244 ; https://arxiv.org/pdf/2310.06174 ; https://arxiv.org/pdf/2207.04802
