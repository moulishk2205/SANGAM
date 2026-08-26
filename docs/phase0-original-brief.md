# MASTER BRIEF — SIH26099, PHASE 0 (PLANNING ONLY)

Team: final-year CSE students, Smart India Hackathon 2026.
Problem statement: **SIH26099 — AI Standardization & Harmonization of Material Codes Across CPSEs**
Tooling: Claude Pro / Claude Code, heavy AI-assisted development.

## HARD CONSTRAINT
PHASE 0 = PLANNING ONLY. No implementation code. No project files. Understand the problem,
challenge the team's assumptions, design the solution, find weaknesses, produce a reviewable plan.

## 1. THE REAL PROBLEM
Different CPSEs maintain separate material masters. The same physical/functional material has different
material codes, descriptions, abbreviations, naming conventions, units, specifications, classifications,
attribute ordering, legacy identifiers, procurement terminology.

Example:
- CPSE A: `SS HEX BOLT M10 X 50` -> code `MAT-78291`
- CPSE B: `STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM` -> code `BLT-10922`
- CPSE C: `BOLT HEX SS M10*50` -> code `XJ-55291`

A human engineer sees one material. A database cannot. Fuzzy string matching is unreliable.
Plain embedding similarity is insufficient because `M10 x 50` and `M10 x 75` are semantically near-identical
but are DIFFERENT materials. The solution must understand semantic meaning AND engineering specifications /
structured attributes.

## 2. PRODUCT VISION
Not "an AI duplicate detector". A **NATIONAL MATERIAL INTELLIGENCE & HARMONIZATION PLATFORM** that lets CPSEs:
1 ingest existing material data; 2 clean+normalize; 3 understand descriptions; 4 extract engineering attributes;
5 identify duplicates; 6 identify near-duplicates; 7 identify functional equivalents; 8 recommend standardized
mappings; 9 generate/use a unified material master; 10 preserve original CPSE codes; 11 human expert
approve/reject; 12 prevent future duplicate creation; 13 analytics + procurement intelligence; 14 complete
auditability; 15 future enterprise-system integration.
The AI is the intelligence layer, not the whole product.

## 3. THE AI MATCHING ENGINE IS CRITICAL
No fake "LLM + prompt + similarity score". A real ML/AI system, designed to eventually operate on millions of
records. Prototype: build/train/evaluate on at least several thousand records, preferably tens of thousands.

## 4. MULTI-STAGE ENGINE (PROPOSED — CRITIQUE IT, DO NOT ACCEPT BLINDLY)
RAW RECORD -> Data Cleaning -> Text Normalization -> Unit Normalization -> Attribute/Spec Extraction ->
Material Classification -> Semantic Embedding -> Candidate Retrieval -> Specification-Aware Comparison ->
Hybrid Scoring -> Duplicate/Equivalent Classification -> Confidence Score -> Explainable Recommendation ->
Human Approval -> Unified Material Master

Answer explicitly: what to change / add / remove; which ML models; transformer embeddings?; fine-tune a
sentence-transformer?; contrastive learning?; cross-encoders?; two-stage retrieval?; RAG?; should an LLM be
involved and where?; where deterministic engineering rules vs ML; handling numerical specifications; unit
conversion; missing attributes; conflicting attributes; multilingual descriptions; learning abbreviations;
confidence calibration.

## 5. TRAINING DATA
Genuine ML pipeline. Initial 5,000-50,000+ records if realistically obtainable/generatable from legitimate
sources; architecture scalable to millions. DO NOT recommend claiming training on millions if untrue.
Pipeline: Initial Dataset -> Cleaning -> Normalization -> Label Generation/Expert Labels -> Train/Val/Test ->
Training -> Evaluation -> Error Analysis -> Improvement.
Where can we LEGALLY and PRACTICALLY get data? Investigate: public government procurement datasets, public CPSE
material catalogs, GeM/public procurement data where legally usable, industrial catalogs, public product
catalogs, open datasets, synthetic variations from legitimate source records, domain dictionaries, engineering
standards where licensing permits, manually curated examples. Clearly separate REAL vs SYNTHETIC data.

## 6. DATASET GENERATION & AUGMENTATION
Generate realistic variants preserving material identity, e.g.
`STAINLESS STEEL HEX BOLT M10 X 50` / `SS HEX BOLT M10X50` / `SS HEX BOLT M10 x 50` /
`HEXAGONAL BOLT - SS - 10MM DIA - 50MM LG` / `BOLT HEX SS M10 50MM`.
Augmentation must not introduce incorrect equivalences. Need HARD NEGATIVES: M10x50 vs M10x75; M10 bolt vs
M10 nut; SS bolt vs carbon steel bolt. Teach: semantic similarity != material identity. Design a proper
positive/negative pair generation strategy.

## 7. AI OUTPUT CLASSES (evaluate sufficiency + define technically)
EXACT/IDENTICAL; DUPLICATE; NEAR-DUPLICATE (>=1 important attribute differs); FUNCTIONALLY EQUIVALENT
(interchangeable for a defined use case); DISTINCT.

## 8. EXPLAINABLE AI
Not "MATCH = 97.4%". Attribute-by-attribute comparison table: Material / Type / Diameter / Length each with
source value -> target value and agreement mark, plus semantic similarity, attribute agreement, final
confidence. Propose the methodology.

## 9. UNIFIED MATERIAL MASTER
Canonical record, e.g. Unified Material ID `NMC-0001842`, canonical name, specifications (diameter/length/
material/type), and mapped CPSE records (ONGC -> MAT-78291, NTPC -> BLT-10922, IOCL -> XJ-55291, BHEL -> 440918).
Original codes must NEVER disappear. Canonical identity + original org-specific identity.

## 10. PLATFORM FEATURES — DASHBOARD
total materials; unified materials; duplicate candidates; harmonization %; pending approvals; CPSE stats;
category stats; potential procurement opportunities; recent AI decisions. Demo numbers must be clearly labelled
as demo data.

## 11. INGESTION
CSV, Excel, JSON, API. Future: SAP, Oracle ERP, other ERPs, legacy DBs.
UPLOAD -> VALIDATION -> DATA QUALITY CHECK -> NORMALIZATION -> AI ANALYSIS -> MATCHING -> REVIEW.
Show import statistics (records processed, valid, missing descriptions, duplicate candidates, invalid units,
unmapped categories).

## 12. MATERIAL MASTER SCREEN
Search by material ID, description, specification, CPSE, category, original code, and semantically. Detail view:
canonical ID, canonical description, specs, category, standards, original CPSE codes, suppliers, confidence,
mapping history, audit history.

## 13. AI HARMONIZATION WORKSPACE (primary screen)
Source material panel (CPSE, code, description) + ranked AI candidates with confidence. Click a candidate ->
full explanation. Actions: Approve, Reject, Edit, Merge, Mark as distinct, Flag for expert review.

## 14. HUMAN-IN-THE-LOOP GOVERNANCE
AI recommends, humans govern. AI Recommendation -> Human Review -> Approve/Reject/Modify -> Unified Master.
Every decision recorded.

## 15. CONTINUOUS HARMONIZATION
Prevent NEW duplicates: new material created in CPSE ERP -> platform detects similar existing material ->
"possible existing material found" + confidence -> human review -> use existing Unified Material ID.
Turns duplicate cleanup into continuous material governance.

## 16. MATERIAL RELATIONSHIP GRAPH
Unified material -> CPSEs -> codes -> supplier relationships. Explore whether it reveals duplicate suppliers,
material clusters, cross-CPSE common materials, fragmented procurement, category relationships. Recommend graph
technology if appropriate.

## 17. PROCUREMENT INTELLIGENCE
duplicate procurement; material fragmentation; common materials across CPSEs; category consolidation
opportunities; supplier overlap; inventory optimization; standardization progress; potential cost savings.
DO NOT invent financial savings as fact. Use "potential opportunity" unless validated procurement data exists.

## 18. CPSE DASHBOARD
Per-CPSE: total materials, standardized, duplicate rate, pending mappings, most fragmented categories,
standardization progress. Prototype figures clearly labelled demo data.

## 19. AUDIT & VERSION CONTROL
Record per decision: material, old mapping, proposed mapping, AI confidence, explanation, model version,
timestamp, reviewer, reviewer decision, changes. Investigate whether append-only or cryptographically
verifiable audit is ACTUALLY useful. Do not add blockchain because it sounds impressive.

## 20. SEARCH
Intelligent search; "stainless bolt 10 50" should work. Modes: exact, keyword, semantic, specification-aware,
CPSE-specific, unified-master.

## 21. NOTIFICATIONS & ALERTS
new duplicate detected; approval pending; data-quality problem; new material conflicts with master; failed
integration; model confidence below threshold.

## 22. ADMINISTRATION
RBAC: CPSE administrator, central administrator, reviewer, auditor, read-only, system administrator.

## 23. API / INTEGRATION LAYER
Eventually: POST /materials, POST /match, GET /materials/{id}, GET /matches/{id}, POST /approvals,
GET /analytics. Determine the proper API architecture first. Implement nothing yet.

## 24. TECH STACK — RECOMMEND A REALISTIC ONE
Frontend candidates: Next.js, React, TypeScript, Tailwind, component library, charts, graph visualization.
Backend candidates: FastAPI, Python, PostgreSQL, Redis, background workers.
AI/ML candidates: sentence-transformers, BGE, E5, cross-encoders, fine-tuning, PyTorch, Hugging Face, FAISS,
pgvector, Qdrant, Elasticsearch/OpenSearch.
Data processing: Pandas, Polars, Spark (only if justified), ETL.
Deployment: Docker, cloud, local, GPU requirements.
Choose on prototype speed, scalability, cost, maintainability, ML performance, deployment complexity — not
fashion.

## 25. SCALABILITY
Prototype: thousands -> tens of thousands. Future: hundreds of thousands -> millions. Explain vector indexing,
batch processing, incremental matching, caching, DB indexing, async jobs, inference optimization, candidate
retrieval, ANN search, distributed processing if necessary.

## 26. MODEL EVALUATION
No "our AI is 95% accurate". Define metrics: Precision, Recall, F1, Accuracy where appropriate, ROC-AUC where
meaningful, Precision@K, Recall@K, retrieval recall, FPR, FNR, calibration, human approval rate. Weigh the cost
of false positives — a government procurement system must be conservative about declaring two materials equal.

## 27. BASELINE VS OUR MODEL
Compare: exact string matching; fuzzy matching; basic embedding similarity; our hybrid (semantic + structured
attributes + engineering rules + retrieval + learned model + confidence). Report F1 per approach. Only use real
measured numbers once experiments are actually run.

## 28. SECURITY
authentication, RBAC, encryption, API security, tenant isolation, audit logs, data privacy, secure uploads,
malware scanning, rate limiting, secrets management, model/data security.

## 29. DATA PRIVACY
CPSE material data may be sensitive. Cloud vs private cloud vs on-premise vs hybrid inference. Future-ready
architecture where sensitive enterprise data need not leave the organization's controlled environment.

## 30. DEMO STRATEGY
Spectacular but credible end-to-end demo. Sketch: upload 3 CPSE datasets -> data-quality analysis -> AI finds
thousands of potential duplicates -> select a material -> AI explains top matches -> show M10x50 matches
10MMx50MM but NOT M10x75 -> human approves -> unified material created -> graph updates -> analytics update ->
simulate a new duplicate -> platform catches it before it enters the master. Must feel like a real enterprise
product, not a student project.

## 31. UX / UI
Premium enterprise/government platform, not a generic dashboard: clean, professional, information-dense, highly
usable, modern, responsive, accessible, clear hierarchy, excellent data visualization. No flashy animation
overuse. Communicate Trust + Intelligence + Government-scale infrastructure.

## 32. REQUIRED PHASE 0 DELIVERABLES (A-P)
A problem understanding; B assumption audit (what are we misunderstanding?); C solution architecture;
D AI architecture in technical detail; E training strategy incl. scaling to millions; F model strategy
(models, fine-tuning, embeddings, retrieval, ranking, rules); G data architecture (DB, vector DB, storage,
ETL); H platform architecture (all modules and screens); I UX flow; J enterprise integration (SAP/ERP/API);
K security architecture for government-grade deployment; L evaluation strategy proving the AI works;
M demo strategy for first review and final demo; N innovation — what makes this different from
"upload CSV -> embeddings -> duplicate detection"; O risks (technical, data, ML, UX, integration,
SIH-presentation); P simplifications — what NOT to build, with MUST HAVE / SHOULD HAVE / NICE TO HAVE /
DO NOT BUILD YET.

## 33. CHALLENGE US
Do not agree with everything. If an idea is bad, say so. If something is technically unrealistic, say so. If a
feature is unnecessary, remove it. If the ML strategy is weak, replace it. If there is a better architecture,
propose it. If something impresses judges but adds no real value, call it out. We want an experienced technical
architect, not a yes-man.

## 35. APPROVAL GATE — PHASE 0 APPROVAL DOCUMENT must contain
1 final recommended architecture; 2 final recommended tech stack; 3 AI/ML strategy; 4 dataset strategy;
5 complete feature list; 6 screen list; 7 database architecture; 8 API architecture; 9 development phases;
10 risk register; 11 evaluation plan; 12 demo strategy; 13 what NOT to build; 14 estimated development effort;
15 dependencies; 16 questions requiring our decision.
Do not proceed to Phase 1 without explicit approval.

## 36. MINDSET
Not a college AI project. A prototype that looks like the foundation of real national-scale CPSE material
intelligence infrastructure. The AI must be real. The matching engine must be measurable. The platform must be
coherent. The architecture must be scalable. Outputs must be explainable. Humans must remain in control.
Every major claim must be demonstrable.
