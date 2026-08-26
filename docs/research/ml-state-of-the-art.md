# ML State of the Art — Entity Resolution / Product Matching / Short-Text Industrial Matching

**For:** SIH26099 Phase 0. **Date:** 2026-08-26. **Status:** research input, not a design doc.
**Audience:** the engineers who will implement the matching engine.

### Epistemic labelling convention used throughout

- `[VERIFIED]` — I fetched a source this session. URL is given inline.
- `[JUDGMENT]` — my reasoned engineering opinion. No citation. Argue with it.
- `[ASSUMPTION]` — plausible but unchecked. I say how to check it.
- `UNVERIFIED — verify by <action>` — I believe this exists but did not confirm it. **Do not put it in a slide until someone confirms it.**

Nothing in this document contains a dataset URL, record count, or benchmark score that I did not
either fetch this session or explicitly mark as unverified. If you find one, treat it as a bug in
this document and tell me.

---

## 0. The single most important finding, stated up front

**The brief frames this as an entity-matching problem. It is mostly a normalisation-and-structured-key
problem wearing an entity-matching costume.** `[JUDGMENT]`

The research literature the brief is implicitly reaching for (DeepMatcher, DITTO, WDC Products) is about
matching *dirty, long, redundant* records — e-commerce product offers with titles, descriptions, brands,
prices. Those records have lots of redundant text signal, so a transformer that reads both records and
says "same/different" works well.

Your records are the opposite: **terse, abbreviation-dense, and dominated by a small number of
load-bearing tokens**, most of which are numeric or alphanumeric. `SS HEX BOLT M10 X 50` is ~5 units of
information, and 2 of them (`M10`, `50`) are the entire difference between a match and a catastrophic
false positive. There is almost no redundancy to absorb an error.

That has three hard consequences:

1. **A learned semantic model cannot be the arbiter of identity.** It can be the arbiter of *candidacy*.
   The literature is explicit that transformers are weak exactly where you are strong-signal-dependent
   (numerics — see §2.4, verified quote from the DITTO authors).
2. **The highest-leverage ML in this project is extraction + normalisation, not matching.** If you can
   turn `BOLT HEX SS M10*50` into `{noun: BOLT, modifier: HEX, material: SS/A2, thread: M10, length_mm: 50}`
   with high reliability, then matching is a *deterministic key comparison* and is 100% explainable,
   100% auditable, and trivially fast. That is also what makes the demo work: you can show the attribute
   table the brief asks for in §8 because you actually have attributes.
3. **This aligns with how the real industry solves it.** Master-data practice for material short
   descriptions is the "noun–modifier–attributes" structured description model. The relevant standards
   family is ISO 8000 (data quality / master data, incl. ISO 8000-110 syntax+semantic encoding and the
   ISO 22745 open technical dictionary / eOTD concept identifiers), plus classification schemes
   UNSPSC, eCl@ss, and NATO codification (NSN / NATO Stock Number).
   **UNVERIFIED — verify by** having one team member pull the ISO catalogue pages for ISO 8000-110 and
   ISO 22745-30 and the UNSPSC/eCl@ss licence pages, and record exactly what is free to use. Do **not**
   claim conformance to any of these in the SIH deck until that is done; several are paid standards and
   eCl@ss in particular is licensed. `[JUDGMENT]` that citing the *methodology* ("noun-modifier-attribute
   structured descriptions, as used in NATO codification and ISO 8000 practice") is safe and impressive
   to judges; claiming *compliance* is not.

**Recommendation:** re-centre the AI story on "we learn to read messy industrial shorthand into a
structured engineering identity, then we match on that identity with auditable rules, with learned
models doing recall and ranking." That is both more honest and more defensible under a judge who knows ML.

---

## 1. Classical entity resolution — what it is and what still beats deep learning

### 1.1 The canonical pipeline

Every serious ER system, from 1969 to 2026, is:

```
records -> [standardisation] -> [blocking / candidate generation] -> [pairwise comparison]
        -> [classification: match / non-match / possible-match] -> [clustering / transitive closure]
        -> [clerical review]
```

Note that **"possible match" is a first-class output class in the original Fellegi–Sunter formulation**
— an explicit clerical-review band. Your brief's human-in-the-loop design is not an innovation; it is
the 1969 design. `[JUDGMENT]` Say so in the deck — showing you know the lineage reads as competence,
not as lack of novelty.

### 1.2 Blocking / candidate generation

You cannot compare N² pairs. At N=50,000 that is 1.25e9 pairs; at N=1,000,000 it is 5e11.
Blocking reduces candidates to a tractable set while trying to keep **pair completeness (recall of
true matches surviving blocking)** near 1.0.

Standard families `[VERIFIED]` — Papadakis, Skoutas, Thanos, Palpanas, *Blocking and Filtering Techniques
for Entity Resolution: A Survey*, ACM Computing Surveys 53(2), 2020.
https://arxiv.org/pdf/1905.06167 and https://helios2.mi.parisdescartes.fr/~themisp/publications/csur20-blockingfiltering.pdf

- **Standard blocking** — exact match on a blocking key (e.g. first 4 chars of noun + material code).
  Cheap, brittle to the very typos you are trying to fix.
- **Token/inverted-index blocking** — candidate = shares ≥1 (or ≥k) rare token.
- **Q-gram / character n-gram blocking** — robust to spelling, explodes in size.
- **Sorted neighbourhood** — sort by a key, slide a window of size w. O(N log N). Good for ordinal keys.
- **MinHash + LSH** — Jaccard-similarity-preserving; provably tunable recall. The survey notes MinHash
  blocking "allows a fuzzy match on attributes, but often ends up with unaffordably many candidate pairs."
- **Meta-blocking** — build a blocking graph over candidate pairs and prune low-weight edges; "significantly
  increase precision at a limited cost in recall."
- **Embedding/ANN blocking** — kNN in a dense space (this is what you'll add; it is just another blocker).

`[JUDGMENT]` **For you: use a union of 3–4 cheap blockers, not one clever one.** Concretely:
`block = union( ANN-top-50 on dense embedding, BM25-top-50, exact-normalised-noun+material, exact-spec-key )`.
Union-of-blockers is how you get pair completeness ≥0.99 without any single blocker being brilliant.
**Measure pair completeness explicitly** — it is the single number that caps your end-to-end recall, and
almost no student project measures it. Reporting "our candidate generation achieves 99.4% pair completeness
at 42 candidates per record" is worth more to a technical judge than any F1 you can quote.

### 1.3 Fellegi–Sunter probabilistic record linkage

The model: for each comparison field *i*, define an agreement pattern γ. Estimate
- **m_i = P(field i agrees | pair is a true match)**
- **u_i = P(field i agrees | pair is a non-match)**

Match weight = Σ log2(m_i/u_i) for agreeing fields, Σ log2((1-m_i)/(1-u_i)) for disagreeing fields, plus a
prior log-odds. Two thresholds split match / possible-match / non-match. m and u are typically estimated
by EM without labels.

**Why this matters to you even though it looks ancient** `[JUDGMENT]`:
- It is **naturally calibrated in log-odds** and each field's contribution is a number you can print in
  the explanation table. The brief's §8 explainability requirement is *native* to Fellegi–Sunter and
  *bolted on* to a neural matcher.
- It handles **missing attributes** correctly and principledly (a missing field contributes 0 weight —
  it neither confirms nor denies), which the brief lists as an open question.
- **u_i is estimable from the data with no labels** (random pairs are almost all non-matches), which
  matters enormously when you have no gold labels on day 1.

**Splink** `[VERIFIED]` https://github.com/moj-analytical-services/splink — MIT licence, Splink 4 is
current, backends DuckDB / Spark / PostgreSQL, README claim: "capable of linking a million records on a
laptop in around a minute." Docs: https://moj-analytical-services.github.io/splink/topic_guides/theory/fellegi_sunter.html
Also see Linacre's write-up: https://www.robinlinacre.com/probabilistic_linkage/

Other tooling `[VERIFIED]` (existence + broad characterisation; I did not benchmark them):
- **dedupe / dedupe.io** — Fellegi–Sunter + active learning + hierarchical agglomerative clustering with
  centroid linkage. Note: the `dedupe` Python library is open source; dedupe.io is the paid hosted product.
  **UNVERIFIED — verify by** checking the licence file in the dedupe GitHub repo before depending on it.
- **Zingg** (https://github.com/zinggAI/zingg) — Spark-based, active-learning training-data builder,
  learned blocking; claims comparisons of "0.05–1% of the possible problem space."
- **Magellan / py_entitymatching** — academic ER framework, ML classifiers over hand-designed similarity
  features; noted limitation: no integrated clustering step, so you must supply your own transitive closure.
- **RapidFuzz / recordlinkage** — string-similarity and comparison-vector utilities.
  **UNVERIFIED — verify by** `pip index` / GitHub before pinning versions.

### 1.4 What still beats deep learning, and why

`[JUDGMENT]`, supported by the DITTO gains being *largest on dirty/textual datasets* (§2.3):

| Situation | Winner | Why |
|---|---|---|
| Clean, aligned, structured attributes; identity determined by a few discrete fields | Fellegi–Sunter / GBDT over similarity features | The signal is already structured. A transformer has to re-derive alignment that you already have, and adds no information. |
| Numeric/dimensional identity (M10×50 vs M10×75) | Deterministic comparator with tolerance | Transformers do not do numeric comparison reliably (§2.4). This is not a tuning problem. |
| Long, dirty, misaligned free text; identity spread over many tokens | DITTO-style cross-encoder | Transformers excel at alignment and paraphrase. |
| Very few labels | Fellegi–Sunter (EM, unsupervised u/m) or LLM zero-shot | Neither needs a labelled training set. |
| Explanation is a hard requirement | Fellegi–Sunter / feature-based GBDT with SHAP | Per-field weights fall out of the model. |

`[JUDGMENT]` **Also: gradient-boosted trees (LightGBM/XGBoost) over a hand-built feature vector are an
underrated, near-free baseline that a lot of published deep-EM work fails to beat by much on structured
data.** For you, the pairwise feature vector is obvious and cheap:
dense cosine, BM25 score, Jaccard over normalised tokens, token-sort ratio, per-attribute agreement flags,
per-numeric relative difference, unit-compatibility flag, material-family match, class-code match, count
of numerics present in one record and absent in the other. ~25–40 features. LightGBM trains in seconds on
50k pairs on a CPU. **Build this first. It is your real baseline and it may well be your final model.**

---

## 2. Deep entity matching

### 2.1 DeepMatcher (2018)

Mudrov, Li, Doan et al., *Deep Learning for Entity Matching: A Design Space Exploration*, SIGMOD 2018.
Attribute-aligned RNN/attention encoders, attribute summarisation, then comparison + classifier.
Established the "SIF / RNN / Attention / Hybrid" design space and the ER-Magellan benchmark suite
(Structured / Dirty / Textual variants of Amazon-Google, Walmart-Amazon, DBLP-ACM, DBLP-Scholar,
Abt-Buy, Beer, iTunes-Amazon, Fodors-Zagats).
`[VERIFIED]` existence and role via https://www.researchgate.net/publication/325374535_Deep_Learning_for_Entity_Matching_A_Design_Space_Exploration
and via the DITTO paper's baseline tables.

### 2.2 DITTO (Li, Li, Suciu, Tan, Tang — VLDB 2021) — the recipe you should actually copy

`[VERIFIED]` https://arxiv.org/abs/2004.00584 , full text via https://ar5iv.labs.arxiv.org/html/2004.00584

The recipe, exactly:

1. **Serialise** each record: `[COL] attribute [VAL] value [COL] attribute2 [VAL] value2 ...`
2. **Pair** them: `[CLS] serialize(e1) [SEP] serialize(e2) [SEP]`
3. Fine-tune a pretrained LM (BERT / DistilBERT / RoBERTa) as a binary cross-encoder classifier.
4. Three domain optimisations:
   - **Domain knowledge / span typing** — user-supplied recognisers tag important spans so the model
     learns to align like with like. The paper's own example: tagging the last 4 digits of phone
     numbers with a `[LAST]` token. **This is the hook you want** — it is the sanctioned mechanism for
     injecting `[DIA]`, `[LEN]`, `[THREAD]`, `[GRADE]` tags into your serialisation.
   - **Summarisation** — TF-IDF-based truncation to keep the informative tokens within the length budget.
   - **Data augmentation** — span/attribute deletion, shuffling, etc.

### 2.3 What accuracy do these actually achieve

`[VERIFIED]` numbers from the DITTO paper (F1, higher is better). DeepMatcher+ = best of DeepMatcher and
its published variants, as reported by the DITTO authors.

| Benchmark | DeepMatcher+ | DITTO | Δ |
|---|---|---|---|
| Structured Amazon-Google | 70.7 | **75.58** | +4.88 |
| Structured Beer | 78.8 | **94.37** | +15.57 |
| Structured Walmart-Amazon | 73.6 | **86.76** | +13.16 |
| Dirty Walmart-Amazon | 53.8 | **85.69** | +31.89 |
| Textual Abt-Buy | 62.8 | **89.33** | +26.53 |
| WDC Product Matching (xLarge) | 90.16 | **94.08** | +3.92 |

DITTO at *half* the WDC training data (Large) scored **93.05**, beating DeepMatcher's full-data 90.16.
Abstract claim: up to 29 F1 improvement over prior SOTA; 96.5 F1 on a real-world company-matching task.

**Read the shape of that table.** `[JUDGMENT]` The transformer's advantage is enormous on *Dirty* and
*Textual* (+27 to +32) and modest on *Structured* (+5). Your problem, after your extraction stage runs,
is a **Structured** problem. Expect single-digit gains from a cross-encoder over a good feature-based
model — not the 30-point miracle the headline suggests.

Also note: **Structured Amazon-Google tops out at 75.6 F1.** `[JUDGMENT]` This is the number to
internalise. Product matching on genuinely hard, short, spec-laden text is *not* a solved problem, and
anyone claiming 97% end-to-end on a realistic industrial catalogue is either evaluating on an easy split,
leaking augmentation between train and test, or lying. Plan your evaluation so you are not accidentally
the third case (see §12).

### 2.4 The numeric weakness — VERIFIED, and it is central to your project

`[VERIFIED]` Direct quote from the DITTO authors (https://ar5iv.labs.arxiv.org/html/2004.00584):

> "Currently, the LMs that we have tested in Ditto are pre-trained on general English text corpora and
> thus might not capture well EM tasks with a lot of numeric data."

They propose as future work a hybrid network combining specialised numeric models with transformer LMs.

Corroborating: *Deep Entity Matching: Challenges and Opportunities* (ACM JDIQ) —
https://dl.acm.org/doi/fullHtml/10.1145/3431816 — notes deep learning models "are known not to perform
numerical comparisons well." `[VERIFIED]` via search snippet; **verify by** reading the paper's section on
numerics directly before quoting it in the deck.

Dedicated work exists but is thin (see §9):
- **JointMatcher** (Ye, Ji, Zhang, Wang, Sun, Wang, Du; *Knowledge-Based Systems* 251, 2022) —
  adds a **relevance-aware encoder** and a **numerically-aware encoder** that concentrate attention on
  similar segments and number-containing segments. Claims new SOTA on structured + textual datasets with
  small/medium training sets, without injected domain knowledge. `[VERIFIED]` existence, abstract claims,
  venue: https://dl.acm.org/doi/10.1016/j.knosys.2022.109033 and https://dblp.org/rec/journals/kbs/YeJZWSWD22.html
  I could **not** retrieve its per-dataset F1 table (ScienceDirect returned 403).
  **UNVERIFIED — verify by** obtaining the PDF through your college library / ACM DL access before citing
  any specific JointMatcher number.

**Practical implication `[JUDGMENT]`, and this is the design decision of the whole project:**

> Never let a transformer decide whether `M10×50` equals `M10×75`. Extract the numbers, compare them
> arithmetically with an explicit tolerance policy, and let that comparison **veto** the neural score.
> Structure this as a hard gate, not a feature: `final = neural_score × Π(gate_i)` where gate_i ∈ {0,1}
> for each critical dimension. A vetoed pair is not "low confidence", it is *rejected*, and the
> explanation names the attribute that vetoed it.

That single sentence is your differentiator versus every "we used embeddings" submission, and it is
directly supported by a verified quote from the authors of the leading deep-EM system. Put the quote on a slide.

### 2.5 Other architectures worth knowing (briefly)

- **HierGAT** — hierarchical graph attention transformer; models interdependence between ER decisions and
  between attributes rather than treating each pair independently. `[VERIFIED]` characterisation only, via
  search snippets. **UNVERIFIED — verify by** locating the primary paper (it is in the VLDB/ICDE family)
  before citing numbers. `[JUDGMENT]` **Cut it.** Marginal gains, real implementation cost.
- **JointBERT** — dual-objective BERT for product matching: binary match head + multi-class entity-identifier
  head, so the model learns entity identity, not just pair similarity. `[ASSUMPTION]` on the exact
  formulation; **verify by** finding the Peeters/Bizer JointBERT paper. `[JUDGMENT]` The *idea* — add an
  auxiliary "which canonical entity is this" classification head — is worth stealing even if you never
  read the paper, because you are building a canonical master anyway and it gives you free supervision.
- **Sudowoodo** (Wang, Li, Tan; ICDE 2023) `[VERIFIED]` https://arxiv.org/abs/2207.04122 — contrastive
  **self-supervised** pretraining (SimCLR-style, RoBERTa-base backbone) over unlabelled records, then a
  small labelled fine-tune. Reported "up to 16% gain in F1 vs SOTA with one-third fewer labelled instances."
  `[JUDGMENT]` **This is the most relevant advanced technique for you**, because your bottleneck is labels,
  and you will have a large pile of unlabelled CPSE-like records. Cheap version: contrastively pretrain on
  (record, augmented-record) pairs from your augmentation engine — you're already building that per brief §6.
- **AnyMatch** (2024) `[VERIFIED]` existence https://arxiv.org/html/2409.04073v1 — zero-shot EM with a
  *small* LM instead of GPT-4, on cost grounds. **UNVERIFIED** numbers.
- **ComEM / "Match, Compare, or Select?"** (COLING 2025) `[VERIFIED]`
  https://aclanthology.org/2025.coling-main.8/ , code https://github.com/tshu-w/ComEM — compares three LLM
  strategies over 8 ER datasets and 10 LLMs; finds the **selecting** strategy (give the LLM the candidate
  set and ask it to *select*, rather than judging pairs independently) superior and more cost-effective.
  `[JUDGMENT]` If you use an LLM anywhere in matching, use it in *select* mode over your top-k candidates —
  one call per source record instead of k calls. That is a 10–20× cost reduction with better accuracy,
  which is a rare free lunch. Verified finding, act on it.

### 2.6 WDC Products — the benchmark whose *methodology* you should copy

`[VERIFIED]` Peeters, Der, Bizer, *WDC Products: A Multi-Dimensional Entity Matching Benchmark*, EDBT 2024.
https://arxiv.org/abs/2301.09521

Three evaluation dimensions:
1. **Amount of corner cases** — hard positives (textually dissimilar but matching) and hard negatives
   (textually similar but non-matching). A hard variant contains **80% corner cases**.
2. **Generalisation to unseen entities** — and the paper's key result: *"the performance of all matchers
   significantly drops for unseen entities."*
3. **Development set size.**

`[JUDGMENT]` **Copy this benchmark design wholesale for your own evaluation.** Specifically:
- Build a **hard slice** of your test set that is ~80% corner cases (M10×50 vs M10×75, SS vs MS bolt,
  bolt vs nut of the same size). Report F1 on the hard slice separately and prominently. A model that
  scores 0.98 overall and 0.61 on the hard slice is the model you are about to build if you don't measure this.
- Build an **unseen-material split**: hold out entire canonical materials, not random pairs. If you split
  randomly you will leak augmented variants of the same material across train and test and your F1 will be
  fiction. **This is the #1 way student ML projects produce fake numbers.** Make it a code-review checklist item.

---

## 3. Embedding models available in 2026

### 3.1 Leaderboard reality check

`[JUDGMENT]` **MTEB rank is close to useless for your decision, and you should say why in the deck.**
Reasons: (a) MTEB is dominated by long-document retrieval and STS tasks that look nothing like a 6-token
industrial short description; (b) the top of the board is contaminated by LLM-backbone models (7B+) you
cannot serve; (c) leaderboard overfitting is a known and openly discussed problem. One of the sources I
read makes the same point: "MTEB scores don't always translate to real-world performance."
`[VERIFIED]` (as a claim made in secondary sources): https://modal.com/blog/mteb-leaderboard-article ,
https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/

I attempted to fetch the live leaderboard at https://huggingface.co/spaces/mteb/leaderboard and **could
not read the table** (it is a JS-rendered Gradio Space; WebFetch returned only chrome).
**UNVERIFIED — verify by** opening that Space in a browser, filtering to the English (or Multilingual)
retrieval task subset, adding the "Number of Parameters" and "Embedding Dimensions" columns, and
screenshotting it with the date. Do this once, in week 1, and put the dated screenshot in the repo.
**Do not put an MTEB number in your slides that nobody on the team has seen with their own eyes.**

`[VERIFIED]` datapoint from secondary sources: Qwen3-Embedding-8B was reported at **70.58 on the MTEB
multilingual leaderboard as of 2025-06-05**, ranked #1 at that time
(https://github.com/QwenLM/Qwen3-Embedding , https://arxiv.org/pdf/2506.05176). That is a June-2025 fact
and is certainly stale by August 2026 — treat it as historical, not current.

### 3.2 The shortlist, with verified specs

| Model | Params | Dim | Max seq | Licence | Verified at |
|---|---|---|---|---|---|
| **bge-small-en-v1.5** | ~33M `[ASSUMPTION]` | **384** | **512** | **MIT** | HF card (dim/seq/licence) |
| **bge-base-en-v1.5** | **0.1B** | **768** | **512** | **MIT** | https://huggingface.co/BAAI/bge-base-en-v1.5 |
| **bge-large-en-v1.5** | ~0.335B `[ASSUMPTION]` | **1024** | **512** | **MIT** | HF card table |
| **BGE-M3** | ~0.568B `[ASSUMPTION]`* | 1024 | **8192** | MIT `[ASSUMPTION]` | https://bge-model.com/bge/bge_m3.html |
| **Qwen3-Embedding-0.6B** | **0.6B, 28 layers** | **up to 1024, MRL 32–1024** | **32k** | **Apache-2.0** | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B |
| **Qwen3-Embedding-4B / 8B** | 4B / 8B | — | — | **Apache-2.0** | https://github.com/QwenLM/Qwen3-Embedding |
| **EmbeddingGemma-300m** | **308M** | **768, MRL 512/256/128** | — | Gemma licence (open weights, commercial use permitted) | https://huggingface.co/google/embeddinggemma-300m , https://developers.googleblog.com/en/introducing-embeddinggemma/ |
| **jina-embeddings-v3** | **570M** | **1024, truncatable to 32** | — | **CC-BY-NC-4.0 — NON-COMMERCIAL** | https://huggingface.co/jinaai/jina-embeddings-v3 |
| **nomic-embed-text-v1.5** | ~137M `[ASSUMPTION]` | 768 w/ MRL `[ASSUMPTION]` | — | **Apache-2.0** | secondary sources |
| **potion-base-8M** (Model2Vec) | 8M, **static** | — | n/a | MIT `[ASSUMPTION]` | https://huggingface.co/minishlab/potion-base-8M |

\* the 568M figure appeared in a search snippet attached ambiguously to bge-large-en-v1.5 and to BGE-M3;
I do not trust it. **UNVERIFIED — verify by** reading `config.json` / the safetensors size on the HF page.

Notes on specific models:

- **Qwen3-Embedding-0.6B** `[VERIFIED]` from its HF card: Apache-2.0, 28 layers, 32k context, MRL output
  dims 32–1024, MTEB-Multilingual mean **64.33**, MTEB-English-v2 mean **70.70**, C-MTEB **66.33**.
  It is **instruction-aware**: the card states omitting the task instruction costs roughly **1–5%**
  retrieval performance. If you use it, you must prepend a consistent instruction to queries and you must
  remember to do the same at inference time. `[JUDGMENT]` That footgun alone is a reason a student team
  might prefer BGE.
- **EmbeddingGemma-300m** `[VERIFIED]` 308M params, output dim 768 with MRL to 512/256/128, trained on
  100+ languages, runs in <200MB RAM quantised, described by Google as the highest-ranking open
  multilingual text embedding model under 500M params on MTEB *at its September-2025 release*.
  `[JUDGMENT]` Strong candidate for an on-premise/air-gapped story (brief §29). **Licence caveat:** it is
  the Gemma Terms of Use, not Apache/MIT — it permits commercial use but carries use restrictions and a
  redistribution obligation. **Verify by** reading https://ai.google.dev/gemma/terms before you promise a
  government deployment. `[JUDGMENT]` For a government procurement platform, an actual MIT/Apache licence
  is worth a couple of MTEB points.
- **jina-embeddings-v3** `[VERIFIED]` — **CC-BY-NC-4.0 on the weights.** Non-commercial.
  **Do not use it.** Not because of the hackathon, but because "we built national procurement
  infrastructure on non-commercially-licensed weights" is exactly the kind of question a sharp judge asks
  and you cannot answer. Its architecture is interesting (task-specific LoRA adapters), but licence kills it.
- **Model2Vec / potion-base-8M** `[VERIFIED]` https://github.com/MinishLab/model2vec — distils a sentence
  transformer into a **static** (lookup-table) embedding model; claims up to **50× smaller and up to 500×
  faster inference on CPU**, distillation in ~30 seconds on CPU with no dataset, potion-base-{2M,4M,8M}
  distilled from `bge-base-en-v1.5`, integrated into sentence-transformers. `[JUDGMENT]` **Genuinely
  interesting for you as a first-stage blocker on a CPU-only deployment** — a static embedding is
  order-invariant and loses word order, which is usually terrible but is *nearly harmless* for
  bag-of-attributes short descriptions. Cheap experiment, potentially a great "runs on a CPSE's existing
  hardware" story. Treat the 500× as a vendor claim; **verify by** benchmarking on your own data.

### 3.3 What I recommend `[JUDGMENT]`

**Start with `bge-base-en-v1.5`. 768-dim, 512 tokens, MIT, 0.1B params.**

Rationale: MIT licence (cleanest possible story for a government platform); 768 dims is a good
memory/quality point; it is the most-fine-tuned model in the sentence-transformers ecosystem so every
tutorial and Stack Overflow answer applies to it; 0.1B runs on CPU at usable speed and fine-tunes
comfortably on a free T4. **Your fine-tuned bge-base will beat an off-the-shelf Qwen3-8B on your data**,
and that comparison is a great slide.

Keep `bge-small-en-v1.5` (384-dim) as the fallback if memory or CPU latency bites — half the memory,
and on short domain-specific text the quality gap after fine-tuning is usually small. `[ASSUMPTION]` —
**verify by** running both in your own retrieval eval; it's a 1-hour experiment.

**Multilingual (brief §4 asks about it):** if Hindi/regional descriptions turn out to be real rather than
hypothetical, switch to **BGE-M3** or **multilingual-e5-base**, both of which are multilingual and
permissively licensed `[ASSUMPTION]` on e5's licence — **verify by** reading
https://huggingface.co/intfloat/multilingual-e5-base . `[JUDGMENT]` **But first: check whether any real
CPSE material master actually contains non-English descriptions.** My strong prior is that Indian
enterprise material masters are in English (often mangled English, which is a different problem).
Multilingual support may be a feature you are inventing a need for. Ask a domain contact before spending
a week on it.

---

## 4. Fine-tuning for retrieval

### 4.1 The loss you will use

**MultipleNegativesRankingLoss (MNRL)**, a.k.a. InfoNCE / in-batch-negatives contrastive loss.
`[VERIFIED]` https://sbert.net/ and the sentence-transformers source
(https://github.com/huggingface/sentence-transformers/blob/main/sentence_transformers/losses/MultipleNegativesRankingLoss.py):
given a batch of (anchor, positive) pairs, every other positive in the batch is treated as a negative.

Key mechanics `[JUDGMENT]` + `[VERIFIED]` where noted:
- **Bigger batch = more negatives = better model.** This is the dominant hyperparameter, more than LR or epochs.
- **`CachedMultipleNegativesRankingLoss`** `[VERIFIED]` — GradCache-style two-pass computation
  (embed-and-cache, then compute loss) that gives you very large *virtual* batch sizes without OOM.
  **This is how you get batch 512+ on a 16GB T4.** Use it. It is slower per step but strictly better per
  unit of GPU memory.
- The triplet form `(anchor, positive, hard_negative)` is supported: the explicit hard negatives are added
  to the in-batch negative pool.
- Recent versions expose a **`hardness_mode`** parameter adding hardness weighting to in-batch negatives
  inside the softmax `[VERIFIED]` via sbert docs/release notes. **UNVERIFIED — verify by** checking the
  installed version's docstring; API surface here moves fast.

### 4.2 Hard-negative mining

`[VERIFIED]` sentence-transformers ships **`mine_hard_negatives()`** with parameters for number of
negatives, margin, similarity range, sampling strategy, and batch size
(https://sbert.net/ , release notes: https://github.com/huggingface/sentence-transformers/releases —
v5.2.0 improved hard-negative mining and added Transformers v5 support; v5.2.1 keeps v4/v5 compatibility).

The **critical parameter is `margin` / `max_score`**: mining top-k nearest non-positives will hand you
**false negatives** — records that are actually matches but unlabelled. In your domain this is guaranteed,
because your positives come from augmentation and your corpus contains genuine near-duplicates.
Training on false negatives actively degrades the model.
`[VERIFIED]` this is a recognised problem with a published mitigation write-up:
https://huggingface.co/blog/dragonkue/mitigating-false-negatives-in-retriever-training

`[JUDGMENT]` **For your domain you do not need ANCE or TAS-B.** Those (ANCE = periodically re-index the
corpus with the current checkpoint and re-mine; TAS-B = topic-aware balanced batch sampling with a
cross-encoder teacher for margin distillation) are heavyweight techniques for web-scale retrieval.
You have something far better and free: **you can generate hard negatives deterministically by mutating
the spec.**

Your hard-negative generator, concretely:

| Mutation | Example | What it teaches |
|---|---|---|
| Perturb one dimension | M10×50 → M10×**75** | length matters |
| Perturb the other dimension | M10×50 → M**12**×50 | diameter matters |
| Swap material family | SS → **MS** / carbon steel | material matters |
| Swap the noun, keep specs | BOLT → **NUT** M10 | noun matters |
| Swap the modifier | HEX → **ALLEN** / SOCKET | head type matters |
| Swap grade/standard | A2-70 → **A4-80**, IS 1367 → **IS 1364** | grade matters |
| Unit-trap | 50 MM vs 50 **CM** vs 50 **IN** | units matter |
| Near-miss numeric | 50 mm vs 50.8 mm (= 2 in) | tolerance boundary |

These are *labelled by construction* and are exactly the errors your system must not make. This is
strictly better than mined negatives for the numeric axis, and it costs you a Python script, not a GPU day.
**Mix both**: ~50% constructed spec-mutation negatives, ~50% mined-from-corpus negatives (mined ones teach
you about lexical confusables you didn't think of, e.g. `WASHER SPRING` vs `WASHER PLAIN`).

`[JUDGMENT]` **Danger, and this is the subtle one:** if your positives all come from augmentation and your
negatives all come from spec mutation, the model can learn the *artefacts of your generator* rather than
the semantics — e.g. it learns "sentences that differ by exactly one integer are negatives." Guard against
this with (a) a held-out test set of **hand-labelled real pairs**, even just 300–500 of them, and (b) an
ablation where you test on real pairs only. Budget one person-week for the manual labelling. This is the
highest-value week in the whole project and the one most likely to get cut. Do not cut it.

### 4.3 Matryoshka (MRL)

`[VERIFIED]` concept and support: models are trained so that truncated prefixes of the embedding remain
useful — 768 → 512/256/128/64 — via a loss summed over multiple truncation lengths. Supported natively in
sentence-transformers (`MatryoshkaLoss`), and natively by Qwen3-Embedding (32–1024) and EmbeddingGemma
(768/512/256/128).

`[JUDGMENT]` **Worth doing, low cost, real benefit for you**: train `bge-base` with `MatryoshkaLoss` at
[768, 256, 64]. Then run a **two-tier retrieval**: ANN over the 64-dim prefix (12× less memory, much faster)
to get top-200, rerank with the full 768-dim exact cosine, then cross-encode the top-20. This is a real,
demonstrable scalability story for brief §25 that costs you one extra loss wrapper.

### 4.4 LoRA / PEFT for embedding models

`[VERIFIED]` LoRA reduces trainable parameters to <0.5% of the model; PEFT + LoRA runs on a T4 16GB
(https://huggingface.co/blog/peft). jina-embeddings-v3 uses task-specific LoRA adapters at 570M params
(https://arxiv.org/html/2409.10173v3).

`[JUDGMENT]` **For a 0.1B model, skip LoRA — just full-finetune it.** LoRA earns its keep at ≥1B params.
Adding PEFT to a bge-base run buys you nothing but a dependency and a class of subtle bugs (forgetting to
merge adapters at inference). If you later want Qwen3-Embedding-0.6B or 4B, LoRA becomes the right answer.

### 4.5 What is realistically trainable on a free Colab/Kaggle T4

The honest arithmetic `[JUDGMENT]`, calibrate by measuring on day 1:

- Hardware: Kaggle gives 2× T4 (16GB each) with a weekly GPU-hours quota; Colab free gives a T4 with
  aggressive preemption. **UNVERIFIED — verify by** checking Kaggle's current quota page in week 1;
  it changes. `[JUDGMENT]` **Use Kaggle, not Colab free.** Session persistence and the weekly quota are
  much friendlier to a team of 5 sharing one training job.
- **bge-base-en-v1.5 (0.1B), fp16, max_seq_len 64** (your descriptions are short — do **not** leave it at
  512; this is a ~8× speedup and the single biggest free win available to you):
  batch 128 real / 512 virtual with CachedMNRL. 50k pairs × 3 epochs ≈ **1,200 steps**.
  `[JUDGMENT]` **estimate 20–50 minutes.** One verified anecdote in the wild reports an embedding
  fine-tune with batch 64 × 3 epochs finishing in **under 10 minutes**
  (https://medium.com/@kelvin.lu.au/fine-tuning-embedding-model-with-peft-and-lora-3b6f08987c24) —
  treat as directional, not as a spec.
- **bge-small (33M)**: roughly 3× faster than base. Minutes.
- **A cross-encoder reranker on top of bge-base or MiniLM**: similar order, ~1–2× the bi-encoder cost per
  step because you process concatenated pairs.
- **Qwen3-Embedding-0.6B with LoRA, seq 64, fp16 or 4-bit**: feasible on a T4 but tight. `[JUDGMENT]`
  a few hours for the same data. **Not worth it for a first iteration.**

**Bottom line `[JUDGMENT]`: fine-tuning is not your bottleneck. You can do 5 training runs in an evening.
Your bottleneck is labelled evaluation data and the extraction stage. Allocate accordingly** — the team's
instinct will be to spend weeks on training tricks; that instinct is wrong here.

---

## 5. Rerankers (cross-encoders)

### 5.1 The models

`[VERIFIED]` licences and rough characterisation:
- **bge-reranker-v2-m3** (BAAI) — Apache-2.0, multilingual (100+ languages), cross-encoder.
- **mxbai-rerank-base-v2 (0.5B) / mxbai-rerank-large-v2 (1.5B)** (mixedbread) — Apache-2.0, built on the
  Qwen-2.5 architecture, trained with an RL stage. https://www.mixedbread.com/blog/mxbai-rerank-v2
  Vendor claim: the 1.5B is "8× faster than bge-reranker-v2-gemma while delivering higher accuracy."
- **MonoT5** — seq2seq reranker; scores a pair by the probability of generating "true"/"false".
  `[ASSUMPTION]` on details; **verify by** reading Nogueira et al. before citing. `[JUDGMENT]` **Cut it** —
  older, slower, no advantage for you.
- **ColBERT / late interaction** — per-token embeddings with MaxSim scoring. Much better than a bi-encoder
  at exact-token matching (relevant to `M10X50`!), much cheaper than a cross-encoder, but the index is
  **~100× larger** than a single-vector index because you store a vector per token.
  `[JUDGMENT]` **Cut it for the prototype**, note it in "future work". The storage blowup is not worth it
  when hybrid BM25 already gives you the exact-token signal for free (§7). **UNVERIFIED** on the exact
  storage multiplier — **verify by** reading the ColBERTv2 paper if you decide to pursue it.

### 5.2 Cost per pair — the number that governs your architecture

Published latency figures are all over the place and none of them are measured on your hardware.
`[VERIFIED]` as *reported claims*, from https://mixpeek.com/curated-lists/best-rerankers and
https://futureagi.com/blog/best-rerankers-for-rag-2026/ — bge-reranker-v2-m3 at ~50 ms per (query,passage)
pair on an L40S; ~241 ms average latency in another benchmark; mxbai-rerank-large-v2 ~0.70 s per query.
`[JUDGMENT]` **These are not comparable to each other and you should not quote any of them.** They differ
in passage length, batch size, precision, and hardware.

**Do this instead** `[JUDGMENT]` — the arithmetic you actually need, using *your* text lengths (~32 tokens
per record, so ~72 tokens per pair, which is 7× shorter than the ~512-token RAG passages every one of those
benchmarks used):

```
Let C = pairs/second for your reranker on your hardware, measured with your own token lengths.
Online single-record match:  k candidates -> latency = k/C.
                             Target: k=20, need latency < 300ms  =>  C >= 67 pairs/s.
Batch job, N records, k cands: total = N*k/C.
                             N=50,000, k=20 => 1e6 pairs. At C=200/s => 83 min. At C=2000/s => 8 min.
```

`[JUDGMENT]` A **MiniLM-L6-size cross-encoder (22M params) at 72 tokens/pair, batched on a T4, should
comfortably exceed 1,000 pairs/s**, and on CPU should manage low hundreds. A 0.5B model will be ~20× slower.
**Start small.** Benchmark this in week 2 with a 20-line script; it decides whether your reranker can be
online or must be a batch job, and that decision changes your whole backend architecture (sync API vs
Celery/RQ worker queue).

### 5.3 What a reranker actually buys you

`[JUDGMENT]` In a two-stage pipeline the bi-encoder governs **recall@k** and the reranker governs
**precision@1..5**. A reranker cannot recover a match the retriever never returned. So:
- Tune the retriever for **recall@50 ≥ 0.99** and don't care about its precision at all.
- Tune the reranker for precision in the top few.
- **Measure and report recall@k for k ∈ {1,5,10,20,50,100} as a curve.** Where the curve flattens is your k.
  That curve is a genuinely good slide and takes 20 minutes to produce.

`[JUDGMENT]` **And the DITTO-style cross-encoder *is* your reranker.** Do not build "an embedding model"
and "a DITTO model" as two separate things — the reranker in stage 2 is a DITTO-style cross-encoder over
`[COL]/[VAL]`-serialised record pairs with your own `[DIA]`/`[LEN]`/`[GRADE]` span tags. That is one
component, described two ways, and collapsing them saves you weeks.

---

## 6. ANN / vector search

### 6.1 Memory arithmetic — do this before choosing anything

Per-vector raw storage:

| dim | float32 (4B) | float16/halfvec (2B) | int8 (1B) | binary (1 bit) |
|---|---|---|---|---|
| 384 | 1,536 B | 768 B | 384 B | 48 B |
| 768 | 3,072 B | 1,536 B | 768 B | 96 B |
| 1024 | 4,096 B | 2,048 B | 1,024 B | 128 B |

Total raw vector memory (768-dim):

| N | float32 | halfvec | int8 | binary |
|---|---|---|---|---|
| 10,000 | 30 MB | 15 MB | 7.7 MB | 0.96 MB |
| 1,000,000 | **3.07 GB** | 1.54 GB | 768 MB | 96 MB |
| 10,000,000 | **30.7 GB** | 15.4 GB | 7.7 GB | **960 MB** |

**HNSW graph overhead on top of that.** With `M` neighbours per node, layer 0 stores `2M` links of 4 bytes
each, plus upper layers contributing roughly another `M×4×(1/(m_L))` bytes; total ≈ `M×~10` bytes/vector as
a working rule. `[JUDGMENT]` At M=16 that is **~130–200 bytes/vector**, i.e. ~5% overhead at 768-dim
float32 but ~2× overhead at binary. Published rules of thumb `[VERIFIED]` as claims:
"HNSW typically requires 1.5–2× the memory of the raw vector data" and "HNSW uses 2–5× more memory than
IVFFlat" (https://zilliz.com/ai-faq/how-much-memory-overhead-is-typically-introduced-by-indexes-like-hnsw-or-ivf-for-a-given-number-of-vectors-and-how-can-this-overhead-be-managed-or-configured ,
https://bigdataboutique.com/blog/hnsw-vs-ivfflat-how-to-choose-the-right-vector-index).
`[JUDGMENT]` The "1.5–2×" figures assume low dimensions or high M; at 768-dim float32 with M=16 the graph
is genuinely a small fraction. **Verify by** building the index and reading the actual index size — with
pgvector, `SELECT pg_size_pretty(pg_relation_size('idx_name'));`. One SQL query, do it in week 3.

A concrete verified datapoint for pgvector `[VERIFIED]`: HNSW on `halfvec(3072)` measured at 193 MB for
25k rows, extrapolating to **~77 GB at 10M rows**
(https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/).
Note what that implies: 3072-dim halfvec = 6,144 B/vector raw = 154 MB for 25k, so the measured 193 MB is
**~1.25× raw**. That is a real number from a real index and it supports the "graph overhead is modest at
high dim" reading.

### 6.2 HNSW vs IVF-PQ

`[VERIFIED]` as reported claims:
- **HNSW** — graph-based, high recall out of the box (95%+), higher memory, slower build, good with active
  writes. Recommended for workloads under ~10M vectors.
- **IVFFlat** — cluster into `lists`, probe `nprobe` of them. Minimal memory overhead, fast build,
  **requires the data to exist before you build the index** (needs to learn centroids), degrades when data
  distribution shifts after build.
- **IVF-PQ** — IVF + product quantisation. IVF4096+PQ8 reported to reduce memory by ~99% vs raw float32,
  but "lossy PQ compression introduces significant approximation error and causes the recall to saturate
  around 90% (small datasets) and 85% (large datasets)."
  (https://www.abhik.ai/concepts/embeddings/ann-comparison)

`[JUDGMENT]` **A recall ceiling of 85–90% is disqualifying for you.** You are using ANN as a *blocker*;
every match it misses is a match your whole system can never find, and in a government dedup system a
missed duplicate is a permanent silent failure. **Use HNSW. If memory becomes a problem, use binary
quantisation with a full-precision rerank** (retrieve top-500 by Hamming distance on 96-byte binary
vectors, rescore those 500 with the float32 vectors). That gets you ~32× memory reduction with recall
recoverable to near-exact, which PQ cannot offer. `[ASSUMPTION]` on the exact recall recovery — **verify by**
measuring recall@50 of `binary→rescore` against exact brute force on 10k of your own vectors. That is a
30-line script and it is a great experiment to have in the appendix.

### 6.3 Which system

`[VERIFIED]` pgvector capabilities:
- **HNSW and IVFFlat** index types; `halfvec` (float16) type, and `halfvec` is what you use for >2,000
  dimensions since the standard `vector` index has a 2,000-dim limit.
- **pgvector 0.8.0 added iterative index scans** (`hnsw.iterative_scan`), which fixes the long-standing
  problem where a `WHERE` filter applied *after* the index scan returned fewer rows than requested.
  Modes: `strict_order` (exact distance ordering preserved) and `relaxed_order` (slight reordering, better
  recall). Bounded by `hnsw.max_scan_tuples` (default **20,000**) and `hnsw.scan_mem_multiplier` (default 1).
  Sources: https://github.com/pgvector/pgvector , https://www.thenile.dev/blog/pgvector-080 ,
  https://supabase.com/docs/guides/ai/vector-indexes/hnsw-indexes

**This matters enormously for you** `[JUDGMENT]`: your queries are *always* filtered — by CPSE, by
category, by "not already merged", by tenant. Pre-0.8.0 pgvector was genuinely bad at filtered vector
search. With iterative scans it is fine at your scale. **Set `hnsw.iterative_scan = relaxed_order` and
raise `max_scan_tuples` if you see short result sets.** Also: put a partial index or a category column in
the same table so Postgres can use a plain btree pre-filter when selectivity is high.

Comparative latency numbers exist but are unreliable `[VERIFIED]` as reported claims from secondary
sources: Qdrant ~4ms p50 and ~12ms p99 at 10M vectors; Milvus ~6ms p50 with optional GPU acceleration;
pgvector HNSW 5–8ms at scale; one benchmark reporting a 10× QPS gap between Qdrant and pgvectorscale at a
99% recall target (https://www.firecrawl.dev/blog/best-vector-databases ,
https://medium.com/@wasowski.jarek/i-benchmarked-6-vector-databases-for-rag-none-wins-everywhere-in-2026-900971966b7d).
Every one of those sources says "run your own benchmark." `[JUDGMENT]` **They are right and you should not
quote any of these numbers in your deck.** The differences are configuration artefacts at your scale.

`[JUDGMENT]` **Decision: use pgvector. Full stop. Do not add a vector database.**

Reasoning, and this is a hill worth dying on:
- Your prototype corpus is 10k–200k vectors. At 768-dim halfvec that is **15–300 MB**. It fits in RAM on a
  laptop with room to spare. Every vector DB is fast at this scale; the difference between 4 ms and 8 ms
  is invisible next to your 50 ms cross-encoder.
- You need **transactional consistency between the vector and the approval/audit record**. A separate
  vector store means a two-phase-commit problem, an eventual-consistency bug in your audit trail, and a
  question you cannot answer when a judge asks "what happens if the merge commits but the reindex fails?"
  Postgres solves this by being one database.
- **Every hour spent operating a second datastore is an hour not spent on the extraction model**, which is
  where your actual value is.
- Adding Qdrant/Milvus for a 50k-row prototype is precisely the "impressive on a slide, no value" pattern
  the brief told me to call out. **Call it out.**

The honest slide is: *"pgvector with HNSW to 5M+ vectors on a single node; the retrieval layer is behind
an interface, and Qdrant/Milvus is a drop-in swap if we exceed single-node capacity."* That is a
scalability answer that demonstrates judgment rather than tool-collecting.

**Elasticsearch/OpenSearch** `[JUDGMENT]`: the one real argument for it is that it gives you BM25 and kNN
and RRF in one engine (§7). But Postgres gives you BM25-ish full-text search (`tsvector`/`ts_rank`) plus
pgvector plus your relational data in one engine, which is a better trade for you.
`[ASSUMPTION]` Postgres FTS `ts_rank` is not true BM25 (it is a different ranking function) —
**verify by** reading the Postgres textsearch-controls docs, and if BM25 specifically matters, either
compute BM25 yourself over a token table (easy at your scale — it's ~30 lines of SQL/Python) or evaluate
the `pg_search`/ParadeDB BM25 extension. **UNVERIFIED** that ParadeDB is a good fit — verify before adopting.

---

## 7. Lexical / hybrid retrieval — and why this is not optional for you

### 7.1 The core problem: dense embeddings are bad at exact alphanumeric tokens

`[VERIFIED]` as the consensus framing across hybrid-search sources: "BM25 [is] good at exact-token
matches — error codes, identifiers, abbreviations — and dense vector search [is] good at semantics —
synonyms, paraphrasing"
(https://ashutoshkumars1ngh.medium.com/hybrid-search-done-right-fixing-rag-retrieval-failures-using-bm25-hnsw-reciprocal-rank-fusion-a73596652d22 ,
https://denser.ai/blog/hybrid-search-for-rag/).

`[JUDGMENT]` **The mechanism, so you can explain it to a judge:** `M10X50` is not in any pretrained
tokenizer's vocabulary. BPE shatters it into something like `M`, `10`, `X`, `50` — and `M10X75` shatters
into `M`, `10`, `X`, `75`, sharing 3 of 4 subword tokens. In a dense space trained on natural language,
those two strings are nearly identical, because *for natural language they should be*. The embedding model
is not broken; it is correctly doing a job that is the wrong job. This is the same root cause as the DITTO
numeric weakness in §2.4, and it is why **you need a channel that treats `M10X50` as an atomic symbol.**
BM25 over a character-n-gram or a spec-aware tokenizer is that channel, and it is nearly free.

### 7.2 What to actually build

1. **BM25 / lexical channel over a domain tokenizer.** Do not use the default whitespace tokenizer.
   Emit, per record: normalised word tokens, **plus** extracted spec tokens as atomic units
   (`thread=M10`, `len_mm=50`, `mat=SS304`), **plus** 3–4-grams of the raw string for typo robustness.
   `[JUDGMENT]` This makes `M10X50` an indexed atom that cannot be confused with `M10X75`. This is a
   ~50-line change that will do more for your retrieval than any amount of embedding fine-tuning.
2. **Dense channel** over the fine-tuned bge-base.
3. **Fuse with Reciprocal Rank Fusion.** `[VERIFIED]` `score(d) = Σ_r 1/(k + rank_r(d))`, k default **60**.
   The reason to use RRF rather than a weighted score sum: "BM25 scores are unbounded positive numbers,
   while cosine similarity ranges from -1 to 1" — the scales are incompatible, so naive averaging is
   meaningless. (https://blog.serghei.pl/posts/reciprocal-rank-fusion-explained/)
   `[JUDGMENT]` RRF is also **hyperparameter-free in practice** (k=60 is fine and everyone uses it), which
   means one fewer thing to tune and one fewer thing to justify. Use it.
4. **Optional third channel: exact spec-key lookup.** If both records extract to the identical
   canonical spec key, that is a candidate regardless of what any model says. Free, deterministic, and
   catches the cases where both text channels fail.

### 7.3 SPLADE

`[VERIFIED]` SPLADE-v3 is "statistically significantly more effective than both BM25 and SPLADE++" and
improves out-of-domain BEIR results by ~2%; SPLADE-v3-DistilBERT reported at **81.4 average out-of-domain
recall vs 76.9 for BM25**. Efficient-SPLADE variants reach "latency on par with BM25."
Sources: https://github.com/naver/splade , https://www.emergentmind.com/papers/2403.06789 ,
https://dl.acm.org/doi/10.1145/3634912

`[JUDGMENT]` **Cut SPLADE from the prototype.** It's a real technique and those are real gains, but: it
needs an inference pass to build the sparse vector (so it is not free like BM25), it needs an inverted
index that supports learned term weights (extra infrastructure), its vocabulary expansion is trained on
natural language and will do nothing useful for `M10X50`, and the ~2% BEIR gain is measured on
document retrieval, not 6-token part descriptions. **Put it in "future work" and spend the week on
extraction instead.** If someone asks, the answer "we evaluated SPLADE and judged BM25-over-a-spec-aware-
tokenizer to dominate it for alphanumeric part codes" is a strong answer.

---

## 8. Attribute / spec extraction from short product text

This is where your ML effort should go. It is also the least-glamorous part, which is why teams skip it.

### 8.1 The three approaches

**(a) Rules / regex / grammar.** A tokenizer plus a small grammar over dimension expressions.
`[JUDGMENT]` For metric fasteners the entire dimension space is essentially:
`M<d>` `[×x*]` `<L>` with optional pitch, optional units, optional `DIA`/`LG`/`LONG` keywords, optional
fractional/imperial forms. That is maybe 30 regex rules covering, I'd estimate, **85–95% of fastener
dimension strings** — `[ASSUMPTION]`, **verify by** writing the rules against 500 real descriptions and
measuring coverage. Do this in week 2; the measured number is a slide.

**(b) Sequence labelling (BERT-NER / BIO tagging).**
`[VERIFIED]` **OpenTag** (2018) — open attribute value extraction from product profiles, one model per
attribute; ADOpenTag extends to all attributes in one model.
`[VERIFIED]` **AVEQA** — reframes extraction as QA: each attribute is a question, the model finds the
answer span in the product text. **MAVEQA** extends it to multi-source and long sequences and "performs
slightly better than AVEQA."
`[VERIFIED]` **MAVE** (Yang et al., 2022) — a product dataset for multi-source attribute value extraction,
**2.2 million products** across e-commerce domains with titles, categories and attribute-value annotations.
https://arxiv.org/pdf/2112.08663
`[VERIFIED]` **ImplicitAVE** (ACL Findings 2024) — first public multimodal dataset for *implicit* attribute
value extraction, derived from MAVE, **68k train / 1.6k test across five domains**.
https://arxiv.org/html/2404.15592v2

`[JUDGMENT]` **MAVE is worth looking at for pretraining/transfer, but it is consumer e-commerce, not
industrial MRO.** Do not claim it is representative of CPSE material masters. Its value to you is as a
source of *pretraining signal* for a span-tagger and as a citation showing you know the field.
**UNVERIFIED — verify by** finding MAVE's actual licence and download location on its GitHub before
depending on it. (It is a Google Research dataset; **do not assume** it is redistributable.)

**(c) LLM structured extraction.**
`[VERIFIED]` — this is the most directly relevant paper I found, and it is very relevant:
Brinkmann, Shraga, Bizer, *Using LLMs for the Extraction and Normalization of Product Attribute Values*
(ADBIS 2024), https://arxiv.org/pdf/2403.02130 :
- Introduces **WDC-PAVE**, product offers from **59 websites** across **5 categories**, with manually
  verified attribute-value pairs in **both extracted and normalized forms**.
- Normalisation operations covered: **name expansion, generalisation, unit conversion, and string wrangling.**
- **GPT-4 achieved 91% F1 for extraction+normalisation combined, ~10 percentage points above the
  fine-tuned baselines** (SU-OpenTag, AVEQA, MAVEQA).
- GPT-4 was noted as particularly strong at "string wrangling and name expansion."

**This is close to a direct precedent for your problem** `[JUDGMENT]`: a paper that specifically studies
extraction *plus normalisation including unit conversion* from short product text, and finds LLMs beat
fine-tuned span-taggers by ~10 F1. Cite it. It justifies putting an LLM in your extraction stage in a way
that is defensible rather than lazy.

### 8.2 What wins for terse, abbreviation-heavy industrial descriptions

`[JUDGMENT]`, and I want to be clear that this is opinion, extrapolating from the WDC-PAVE result and from
the structure of your data:

**A three-layer cascade, in this order:**

```
1. GRAMMAR/REGEX      -> dimensions, threads, units, standards codes, grades.
                         High precision. Deterministic. Fast. Free. Fully explainable.
                         Emits a confidence of 1.0 and a matched-rule id for the audit trail.
2. GAZETTEER + FUZZY  -> noun, modifier, material family, expanded abbreviations.
                         Backed by a curated dictionary (SS->STAINLESS STEEL, HEX->HEXAGONAL,
                         HHB->HEX HEAD BOLT, DIA->DIAMETER, LG->LENGTH, THD->THREAD).
                         The dictionary is a first-class, versioned, reviewable artefact.
3. LEARNED FALLBACK   -> a small BIO tagger (fine-tuned bert-base or even DistilBERT) for whatever
                         layers 1-2 leave untagged, trained on labels bootstrapped by an LLM (see 8.3).
```

Why this order rather than LLM-first:
- Layers 1–2 handle the *load-bearing* fields (the numbers), where you need determinism and where
  an LLM's non-determinism is an unacceptable risk. **Never let an LLM decide that 50 mm is 50 mm.**
- The gazetteer is the artefact a domain expert can actually review and correct. That is a real
  human-in-the-loop story, better than "the model learned it."
- The learned layer only handles the residual, so its errors are bounded and its training set is small.
- Every extracted value carries a provenance tag (`rule:R17` / `gazetteer:v3` / `model:v1.2@0.83`) which
  feeds directly into your §19 audit requirement and your §8 explanation table. **This is a genuinely
  strong design and it is cheap.**

`[JUDGMENT]` **Measure extraction separately from matching.** Report per-attribute precision/recall/F1 on
a hand-labelled set of ~500 descriptions. Most teams report only end-to-end matching F1 and then cannot
explain their failures. Per-attribute extraction metrics are what turn your error analysis from guessing
into engineering, and the brief's deliverable L explicitly asks you to prove the AI works.

### 8.3 Where the LLM belongs in extraction — offline

`[JUDGMENT]` Use an LLM **at build time, not at request time**:
- **Bootstrap the gazetteer.** Feed it 5,000 distinct descriptions, ask for candidate abbreviation→expansion
  pairs, then have a human accept/reject. You get a domain dictionary in a day instead of a month.
- **Bootstrap BIO labels** for the learned tagger. LLM proposes spans, human spot-checks a sample, you
  train a 66M-param DistilBERT on the result. This is textbook weak supervision and it works.
- **Mine the residual.** After layers 1–2, cluster the untagged token spans and ask the LLM what they are.
  This surfaces attributes you didn't know existed.

The resulting artefacts (dictionary, tagger weights) are **static, versioned, inspectable, and run offline**
— which is exactly what brief §29 (data privacy / on-prem) requires. This is the honest answer to "where
does the LLM add value": it compresses months of domain-expert time into days, at build time, with a human
gate. Say that instead of "we use GenAI."

---

## 9. Numeric and unit handling — the literature is thin, be honest about it

### 9.1 What exists

- **DITTO's own admission** of the numeric weakness (§2.4) `[VERIFIED]`.
- **JointMatcher** (2022) — numerically-aware encoder + attention concentration `[VERIFIED]` existence,
  numbers unverified.
- **"Fine-grained entity disambiguation through numeric pattern awareness in transformer models"**,
  *Complex & Intelligent Systems* (2025), https://link.springer.com/article/10.1007/s40747-025-01936-3
  `[VERIFIED]` existence only. **UNVERIFIED** content — verify by reading it; it is open-access at Springer.
- **WDC-PAVE** covers **unit conversion** as an explicit normalisation operation `[VERIFIED]` (§8.1c).
- There is a **US patent** titled "Numeric embeddings for entity-matching"
  (https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11615120) `[VERIFIED]` that it exists as
  a search result. `[JUDGMENT]` Worth a 20-minute read for prior-art awareness — a patent existing in this
  space is itself a data point that the problem is real and commercially valued. **Do not implement from a
  patent** without thinking about it; note it and move on.

### 9.2 The honest assessment

`[JUDGMENT]` **The published ER literature does not seriously address tolerances, ranges, or engineering
unit semantics.** Papers treat numbers as either (a) tokens, or (b) a scalar with an ad-hoc similarity like
`1 - |a-b|/max(a,b)`. Nobody in the mainstream ER literature is modelling "M10×50 and M10×50.8 might be the
same part sourced in imperial" or "a 10.2 mm shaft is not interchangeable with a 10.0 mm shaft."

**This is good news for you.** It means:
1. You cannot copy a solution, so you have to design one — and a well-designed one is a legitimate,
   defensible contribution to point at in the "innovation" deliverable (brief §32 N).
2. Nobody will out-cite you, because there is nothing to cite.
3. You must build it from engineering first principles, not from a paper. That is fine; it is not hard.

### 9.3 What to build

`[JUDGMENT]` A **typed numeric comparator with an explicit, per-attribute, versioned tolerance policy.**

```
Attribute schema entry:
  name:            thread_diameter_mm
  dtype:           quantity
  canonical_unit:  mm
  criticality:     CRITICAL        # CRITICAL | IMPORTANT | MINOR | INFORMATIONAL
  tol_abs:         0.0             # absolute tolerance in canonical units
  tol_rel:         0.0             # relative tolerance
  compare:         exact_after_normalisation
  provenance:      "engineering rule: thread sizes are discrete, not continuous"

  name:            length_mm
  dtype:           quantity
  canonical_unit:  mm
  criticality:     CRITICAL
  tol_abs:         0.5
  tol_rel:         0.0
  compare:         within_tolerance

  name:            weight_kg
  dtype:           quantity
  canonical_unit:  kg
  criticality:     MINOR
  tol_rel:         0.05
```

Rules `[JUDGMENT]`:
- **Convert to canonical units before comparing, always.** Use **Pint** `[VERIFIED]`
  (https://pint.readthedocs.io/) — a mature Python units library with a comprehensive unit registry and
  dimensional-analysis-checked arithmetic. If you want a standards-backed unit code system, **UCUM** is the
  formalism and **ucumvert** (https://github.com/dalito/ucumvert , https://pypi.org/project/ucumvert/)
  parses UCUM strings and converts them into Pint units, shipping all UCUM units from spec v2.2 (June 2024)
  `[VERIFIED]`. **Important gotcha, verified:** *"UCUM does not provide a canonical representation, for
  example m/s and m.s-1 are expressing the same unit in two ways"* — so UCUM alone does not give you a
  comparable key; you still normalise through Pint. `[JUDGMENT]` **Recommendation: use Pint. Add UCUM only
  if you want the standards-conformance talking point**, and if you do, say "UCUM-coded units, normalised
  via Pint" — that is accurate and defensible.
- **Dimension mismatch is a hard reject, not a low score.** `50 mm` vs `50 kg` must be a veto with the
  explanation "incomparable dimensions (length vs mass)". Pint gives you this for free by raising on
  incompatible units. This one behaviour will look extremely competent in a demo.
- **Missing ≠ mismatched.** Three-valued logic per attribute: `AGREE / DISAGREE / UNKNOWN`. UNKNOWN must
  never contribute negative evidence, and must never be silently treated as agreement. It should reduce
  *confidence* (widening the interval) without moving the *point estimate*. This is exactly the
  Fellegi–Sunter treatment of missing fields (§1.3) and it is one of the brief's open questions —
  answered, and answered with a 1969 citation.
- **Criticality drives the veto, not the weight.** A DISAGREE on a CRITICAL attribute → class is at best
  NEAR-DUPLICATE and the match confidence is capped, regardless of a 0.99 cosine. A DISAGREE on a MINOR
  attribute → confidence penalty only.
- **Tolerance defaults must be conservative and per-attribute, and their provenance must be recorded.**
  Do not invent a global "±5%". Where you don't know, set tolerance to 0 (exact) and let a human widen it —
  a false negative goes to a human reviewer, a false positive corrupts the national master.
- **Unit-inference for bare numbers.** `M10 X 50` has no units. You infer mm from context (metric thread
  prefix `M`). **Record that this was inferred, with the rule that inferred it**, and surface it in the
  explanation as `length: 50 (unit inferred: mm, rule THREAD_METRIC_IMPLIES_MM)`. Judges love this and it
  is honest.

### 9.4 How the numeric gate composes with the neural score

`[JUDGMENT]` Concretely, the scoring function:

```
gates       = [g_a for a in CRITICAL attributes]        # g_a in {0, 1}, 1 if AGREE or UNKNOWN
veto        = min(gates)                                 # 0 if any critical attribute DISAGREES
s_neural    = cross_encoder(serialised_pair)             # in [0,1]
s_attr      = weighted attribute agreement over IMPORTANT/MINOR   # in [0,1]
s_lex       = normalised lexical similarity              # in [0,1]
s_raw       = calibrator( [s_neural, s_attr, s_lex, n_unknown, n_critical_known, ...] )
score       = veto * s_raw
class       = decide(score, veto, which attributes disagreed)
```

Note that the **calibrator is a model over features, not a hand-tuned weighted sum**. Fit logistic
regression or LightGBM on your labelled pairs. This gives you learned weights (defensible), calibrated
probabilities (see §10), and per-feature contributions for the explanation table (§8 of the brief).
`[JUDGMENT]` Keep the top-level model small and interpretable — logistic regression over ~15 features is
almost certainly enough and is trivially explainable. Reach for LightGBM only if LR underperforms measurably.

**On the brief's output classes** `[JUDGMENT]`:
- `EXACT`, `DUPLICATE`, `NEAR-DUPLICATE`, `DISTINCT` are all well-defined by the above and are learnable/decidable.
- **`FUNCTIONALLY EQUIVALENT` is not.** Interchangeability depends on the *application* (a 8.8-grade bolt
  substitutes for a 4.6 in some assemblies and not others), needs engineering judgment your labels won't
  encode, and carries real safety liability if a government system asserts it wrongly.
  **Cut it, or demote it to a human-assertable relationship** that the system stores and displays but never
  predicts. That is the right call and it is also a *better story*: "we deliberately do not let the AI
  assert functional equivalence, because that is an engineering judgment with safety implications; the
  platform records expert-asserted equivalences instead." That answer wins a hard question from a judge.

---

## 10. Confidence calibration — how to make "97%" actually mean 97%

### 10.1 The methods

- **Platt scaling** — fit a 1-D logistic regression `P = σ(a·s + b)` on held-out scores.
  Two parameters, data-efficient.
- **Isotonic regression** — fit a non-parametric monotone step function. More flexible, needs more data.
- **Temperature scaling** — divide logits by a scalar T fitted on held-out data. The standard method for
  neural nets; preserves the argmax so accuracy is unchanged, only confidence moves.
- **Conformal prediction** — distribution-free, gives *finite-sample coverage guarantees*.

`[VERIFIED]` on the Platt-vs-isotonic sample-size tradeoff, from Niculescu-Mizil & Caruana,
*Predicting Good Probabilities With Supervised Learning*, ICML 2005
(https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf) and secondary summaries:
**with ≥1000 calibration points isotonic regression is as good as or better than Platt scaling; below
that, isotonic overfits and Platt's 2-parameter fit is more sample-efficient.**

`[VERIFIED]` on ER specifically: *Confidence Calibration in LLM-Based Entity Matching* (UncertaiNLP 2025
workshop @ EMNLP), https://arxiv.org/abs/2509.19557 — RoBERTa-based matchers are **slightly overconfident**
across Abt-Buy, DBLP-ACM, iTunes-Amazon and Company, with **ECE between 0.0043 and 0.0552**; they compared
**temperature scaling, MC dropout, and ensembles**, and found **temperature scaling most effective,
reducing ECE by up to 23.83%**.

`[JUDGMENT]` **Directly actionable for you:** the ER-specific evidence says (a) your fine-tuned encoder
will be overconfident, (b) it is only *mildly* miscalibrated (ECE ~0.005–0.055), and (c) a one-parameter
temperature fix recovers most of it. So: **fit a temperature on a held-out set. It costs 10 lines and one
scalar.** Cite this paper for the choice. That is a properly grounded methodological decision, which is
rare in student submissions.

### 10.2 The recipe that produces the sentence the brief wants

The brief wants: *"97% of matches I call at this score are truly correct."* That is **precision at a
threshold with a statistical guarantee**, not a calibrated probability. They are different things and you
should build both.

```
STEP 1  Hold out a calibration set. Sample it the way production data arrives — random over records,
        NOT random over pairs, and NOT balanced. Class balance matters: precision is prevalence-dependent,
        so a 50/50 calibration set will lie to you about production precision. Log the prevalence.

STEP 2  Fit the calibrator on the calibration set only.
          - Neural score -> temperature scaling  (ER-specific evidence, §10.1)
          - Final ensemble -> Platt if n_cal < 1000, isotonic if n_cal >= 1000  (ICML'05 evidence)

STEP 3  Verify calibration on a SEPARATE test set:
          - Reliability diagram (10-20 bins, predicted prob vs empirical accuracy)
          - Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
          - Brier score
        Put the reliability diagram in the deck. Almost nobody does, and it is instantly legible as rigour.

STEP 4  Pick the auto-approve threshold by TARGET PRECISION, not by F1:
          for t in sorted(unique_scores):
              prec, n = precision_above(t), count_above(t)
              lower = clopper_pearson_lower_bound(prec, n, alpha=0.05)
              if lower >= 0.99: t_auto = t; break
        Report: "at threshold t_auto, precision >= 99% with 95% confidence, n=<N> pairs above threshold,
        covering <X>% of true duplicates."
        THIS is the sentence that survives a hostile question. A raw point estimate is not.

STEP 5  Two thresholds, three zones (this is Fellegi-Sunter, §1.3):
          score >= t_auto   -> auto-approve candidate (still logged; still human-reversible)
          t_rej < s < t_auto-> REVIEW QUEUE  (the human-in-the-loop band)
          score <= t_rej    -> auto-reject
        Report the REVIEW RATE. "We auto-decide 71% of pairs at >=99% precision and route 29% to a human"
        is the actual product claim, and it is far more compelling than an F1.
```

`[JUDGMENT]` **Step 5 reframes your whole evaluation story from "how accurate is the model" to "how much
expert time does the platform save at a guaranteed error rate."** That is the framing a government buyer
cares about and it is the framing that makes your human-in-the-loop design a feature rather than an
admission of weakness. Build the deck around it.

### 10.3 Conformal prediction — worth it, but keep it simple

The mechanism (Mondrian / split conformal for selective classification):
1. Define a nonconformity score, e.g. `α = 1 - p̂(true class)`.
2. On a calibration set of size n, compute all α_i.
3. Let `q̂ = the ⌈(n+1)(1-ε)⌉-th smallest α_i`.
4. Predict the set `{y : 1 - p̂(y) ≤ q̂}`. **Abstain whenever the set is not a singleton.**
5. Guarantee: the true label is in the set with probability ≥ 1-ε, **distribution-free, finite-sample**,
   requiring only exchangeability between calibration and test data.

`[VERIFIED]` the field is active and the abstention framing is standard practice:
https://www.emergentmind.com/topics/conformal-abstention ,
https://arxiv.org/abs/2607.27143 (cost-sensitive conformal prediction + human-in-the-loop abstention for
imbalanced high-stakes decisions, multi-domain benchmark) — **UNVERIFIED** on that paper's contents, I only
read the listing; **verify by** reading the abstract if you cite it.
Also relevant: https://www.nature.com/articles/s41598-026-40637-w (conformal selective prediction with
cost-aware deferral under distribution shift) — `[VERIFIED]` existence only.
Note also that class imbalance is a documented weak point: "standard marginal conformal prediction severely
under-covers rare, costly minority classes" `[VERIFIED]` as a claim from the 2607.27143 listing.
**That applies to you** — true duplicates are the rare class. Use **class-conditional (Mondrian) conformal
prediction**, calibrating a separate q̂ per class, not marginal conformal.

`[JUDGMENT]` **Verdict: implement split conformal with class-conditional calibration. It is ~40 lines of
numpy and gives you a defensible, distribution-free guarantee on your abstention rate.** That is a real
differentiator for a government system, it directly supports the brief's human-in-the-loop governance
model, and it is far cheaper than it sounds. **Do not** attempt adaptive/online/weighted conformal
variants — the exchangeability assumption is already shaky when a new CPSE uploads a differently-distributed
catalogue, and you should note that limitation honestly rather than paper over it with a more complex method.

`[JUDGMENT]` **The honest caveat to state out loud:** conformal guarantees hold under exchangeability. A
new CPSE with a different naming convention breaks that assumption. The mitigation is to **re-calibrate
per-tenant on a small labelled sample at onboarding** — which is also a natural product feature
("calibration wizard: label 200 pairs, we'll tune your thresholds"). Stating the limitation *and* the
mitigation is what separates an architect from a student.

---

## 11. Where LLMs genuinely add value in ER — and where they are a liability

### 11.1 The 2024–2026 evidence

`[VERIFIED]` Peeters, Steiner, Bizer, *Entity Matching using Large Language Models*, EDBT 2025
(https://arxiv.org/abs/2310.11244 , acceptance: https://www.sowi.uni-mannheim.de/en/news/paper-accepted-at-edbt-2025/):
- "The best LLMs require no or only a few training examples to perform comparably to PLMs that were
  fine-tuned using thousands of examples."
- LLM matchers show **higher robustness to unseen entities** — which connects directly to the WDC Products
  finding (§2.6) that all matchers degrade on unseen entities.
- **"There is no single best prompt"** — prompt performance must be optimised per model and per dataset.
- **"GPT-4 can generate structured explanations for matching decisions and can automatically identify
  potential causes of matching errors by analysing explanations of wrong decisions."**

`[VERIFIED]` *Match, Compare, or Select?* / ComEM, COLING 2025 (https://aclanthology.org/2025.coling-main.8/):
across 8 ER datasets and 10 LLMs, the **selecting** strategy (LLM picks from a candidate set) beats
independent pairwise matching, and the compound ComEM framework improves both effectiveness and
cost-efficiency.

`[VERIFIED]` *AnyMatch* (https://arxiv.org/html/2409.04073v1) — zero-shot EM with a small LM, motivated
explicitly by the cost of GPT-4-class APIs. Existence verified; numbers unverified.

`[VERIFIED]` WDC-PAVE (§8.1c): GPT-4 at **91% F1 on combined extraction+normalisation, ~10 points above
fine-tuned baselines.**

### 11.2 Where LLMs genuinely earn their place, for you

`[JUDGMENT]`, ordered by value:

1. **Offline normalisation & abbreviation-dictionary bootstrapping** (§8.3). Highest ROI in the project.
   Strongly supported by the WDC-PAVE result. Human-gated. Runs once. Zero online cost or risk.
2. **Weak supervision / label bootstrapping.** LLM proposes labels for ambiguous pairs; humans audit a
   sample; you train a small model. Directly supported by the Peeters "comparable to PLMs fine-tuned on
   thousands of examples" finding. This is how you get past the cold-start-with-no-labels problem.
3. **Explanation generation — with a hard constraint.** The LLM may **narrate** the attribute-comparison
   table into fluent English; it must **never compute** the decision. Template the facts, let the LLM
   phrase them, and make the raw table always visible next to the prose. `[JUDGMENT]` If the LLM is
   unavailable, the system must degrade to the template, not fail. Peeters' explanation finding supports
   the value; determinism requires the constraint.
4. **Error analysis during development.** Feed misclassified pairs to an LLM and ask it to cluster the
   failure modes. Directly supported by the verified Peeters finding. This is a *developer tool*, not a
   product feature, and it is genuinely useful.
5. **Cold-start matching for a brand-new category** where you have no fine-tuned model yet — in
   **select mode over top-k**, per ComEM. `[JUDGMENT]` Fine as a fallback, not as the main path.

### 11.3 Where LLMs are a liability — say this out loud in the deck

`[JUDGMENT]`:

| Risk | Why it matters here |
|---|---|
| **Non-determinism** | The same pair can get different answers on two runs. Your §19 audit trail becomes unreproducible. A government auditor asking "why did the system decide this?" must get the same answer in 2029 as in 2026. This alone disqualifies an LLM from the decision path. |
| **Cost at scale** | 1M records × 20 candidates = 20M LLM calls per full pass. At *any* per-call price this is not a national-scale architecture. ComEM's select-mode reduces it ~20×, which makes it 1M calls — still not viable as the default path. |
| **Latency** | Hundreds of ms to seconds per call vs ~1 ms for a cross-encoder over short text. Your §15 "catch the duplicate at ERP creation time" feature needs sub-second synchronous response. |
| **Hallucination** | An LLM asked to compare `M10×50` and `M10×75` will sometimes assert they match, confidently, with a plausible explanation. See §2.4 — this is the *same* numeric weakness, with better prose. |
| **Data privacy** | Brief §29 says CPSE material data may be sensitive. Sending a national procurement master to a third-party API is a governance problem you cannot argue your way out of. |
| **Prompt sensitivity** | Verified: "no single best prompt." You would be shipping a system whose accuracy depends on an unversioned string that anyone can edit. |
| **Version drift** | The provider silently updates the model; your calibration, thresholds and evaluation are all invalidated with no notification. |

**The line to hold** `[JUDGMENT]`: **an LLM may never be on the online decision path.** Offline, human-gated,
and as an explanation renderer only. Write that as an explicit architectural constraint in the Phase 0
approval document, with the reasons above. It is the kind of constraint that makes a judge believe you have
built production systems.

**Optional strong story** `[JUDGMENT]`: if you want a "GenAI" line without the liability, run a **local**
small model (e.g. a Qwen3 or Gemma instruct model in the 1–4B range, quantised) for the offline
normalisation and explanation tasks. Then the answer to "does data leave the CPSE?" is "no, ever" — which
for a government platform is worth more than GPT-4's extra few points, and it directly satisfies brief §29.
**UNVERIFIED** on which specific local model is best for this in 2026 — **verify by** benchmarking 2–3
candidates on 100 of your own descriptions against a human-labelled key. That is a one-day experiment.

---

## 12. Synthesis: the architecture the evidence supports

`[JUDGMENT]` throughout this section.

```
INGEST
  |
NORMALISE           deterministic: case, punctuation, separators (X/x/*/×), whitespace,
                    gazetteer abbreviation expansion (LLM-bootstrapped, human-approved, versioned)
  |
EXTRACT             cascade: regex/grammar -> gazetteer -> small BIO tagger
                    output: typed attribute dict + per-attribute provenance + confidence
  |
CANONICALISE        Pint unit conversion to canonical units; canonical spec key;
                    class code assignment (UNSPSC-like segment/family/class)
  |
INDEX               (a) HNSW over fine-tuned bge-base embeddings of the CANONICAL string  [pgvector]
                    (b) BM25 over spec-aware tokens + char n-grams                        [postgres]
                    (c) btree on exact canonical spec key                                 [postgres]
  |
RETRIEVE            union of (a) top-50, (b) top-50, (c) exact  -> RRF fuse -> top-20
                    METRIC: pair completeness / recall@k  (this caps everything downstream)
  |
COMPARE             per-attribute AGREE / DISAGREE / UNKNOWN with tolerance policy
                    + DITTO-style cross-encoder over [COL]/[VAL]-serialised pair with spec span tags
  |
SCORE               veto = 0 if any CRITICAL attribute DISAGREES
                    s_raw = logistic-regression / LightGBM over [neural, attr, lexical, unknown-counts]
                    score = veto * s_raw
  |
CALIBRATE           temperature scaling on the neural head; Platt/isotonic on the ensemble
                    class-conditional split conformal -> abstention band
  |
DECIDE              EXACT | DUPLICATE | NEAR-DUPLICATE | DISTINCT | ABSTAIN->REVIEW
                    (FUNCTIONALLY EQUIVALENT: human-asserted only, never predicted)
  |
EXPLAIN             attribute table (deterministic, always) + optional LLM narration (local, offline-safe)
  |
HUMAN REVIEW -> UNIFIED MASTER (append-only decision log, model version, thresholds version,
                                gazetteer version, tolerance-policy version)
```

**Note the versioning of the tolerance policy and gazetteer alongside the model version.** Your §19 audit
requirement is only meaningful if a decision can be *replayed*, and replaying needs every artefact that
influenced it — not just model weights. Most teams version only the model. Versioning the rules too is a
small change with a large credibility payoff.

### 12.1 Explicit CUT list

| Cut | Why |
|---|---|
| Qdrant / Milvus / Elasticsearch | pgvector covers your entire realistic scale. Second datastore = consistency bugs + ops time, zero user-visible benefit at 50k–200k rows. |
| SPLADE | Real gains on document retrieval, ~zero on 6-token part codes. BM25 over spec-aware tokens dominates it here. |
| ColBERT / late interaction | ~100× index blowup for a benefit hybrid BM25 already delivers. |
| HierGAT | Marginal published gains, high implementation cost, not on the critical path. |
| MonoT5 | Superseded; slower; no advantage. |
| LoRA/PEFT on a 0.1B model | Pointless below ~1B params. Full fine-tune is simpler and better. |
| ANCE / TAS-B hard-negative pipelines | You can *construct* better hard negatives deterministically. |
| Spark | You have <1M rows. Polars or plain pandas. Spark on 50k rows is a joke a judge will get. |
| LLM in the online decision path | Non-determinism + cost + privacy + numeric hallucination. Non-negotiable. |
| `FUNCTIONALLY EQUIVALENT` as a predicted class | Not learnable from your labels; carries safety liability. Make it human-asserted. |
| Multilingual embeddings | Probably solving a problem you don't have. Verify with a domain contact first. |
| Graph database (Neo4j etc.) for §16 | Your graph is small; a `mappings` table + recursive CTE + a JS force-graph gives the same demo. Revisit only if a query is genuinely graph-shaped and slow in SQL. |

### 12.2 Week-1 experiments that de-risk everything

1. Write 30 regex rules for dimension extraction; measure coverage on 500 real descriptions. **(Decides
   whether the whole architecture is viable.)**
2. Benchmark a MiniLM-size cross-encoder at 72 tokens/pair on your hardware. **(Decides online vs batch,
   which decides your backend architecture.)**
3. Build the union-of-blockers and measure **pair completeness**. **(Caps everything downstream.)**
4. Hand-label 300 real pairs. **(Without this you have no honest number, ever.)**
5. Open the MTEB leaderboard, filter to <500M params, screenshot with the date. **(Kills a whole class of
   fabricated claims.)**

If experiment 1 gives <70% coverage, the extraction-first architecture is in trouble and you should find
that out in week 1, not week 8.

---

## Appendix A — Complete source list (fetched or search-verified this session)

**Deep entity matching**
- DITTO: https://arxiv.org/abs/2004.00584 , full text https://ar5iv.labs.arxiv.org/html/2004.00584 (F1 tables + numeric-limitation quote + COL/VAL serialisation — FETCHED)
- Deep EM: Challenges and Opportunities: https://dl.acm.org/doi/fullHtml/10.1145/3431816
- Sudowoodo: https://arxiv.org/abs/2207.04122
- JointMatcher: https://dl.acm.org/doi/10.1016/j.knosys.2022.109033 (ScienceDirect 403 — abstract only)
- WDC Products benchmark: https://arxiv.org/abs/2301.09521
- AnyMatch: https://arxiv.org/html/2409.04073v1
- Numeric pattern awareness: https://link.springer.com/article/10.1007/s40747-025-01936-3

**Classical ER**
- Blocking survey (Papadakis et al., CSUR 2020): https://arxiv.org/pdf/1905.06167
- Splink: https://github.com/moj-analytical-services/splink (MIT, Splink 4, DuckDB/Spark/Postgres — FETCHED)
- Fellegi-Sunter explainer: https://moj-analytical-services.github.io/splink/topic_guides/theory/fellegi_sunter.html
- Zingg: https://github.com/zinggAI/zingg

**Embeddings**
- bge-base-en-v1.5: https://huggingface.co/BAAI/bge-base-en-v1.5 (768-dim, 512 seq, 0.1B, MIT — FETCHED)
- Qwen3-Embedding-0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B (Apache-2.0, MRL 32-1024, 32k — FETCHED)
- Qwen3-Embedding repo/paper: https://github.com/QwenLM/Qwen3-Embedding , https://arxiv.org/pdf/2506.05176
- EmbeddingGemma: https://huggingface.co/google/embeddinggemma-300m , https://developers.googleblog.com/en/introducing-embeddinggemma/ , https://arxiv.org/abs/2509.20354
- jina-embeddings-v3 (CC-BY-NC): https://huggingface.co/jinaai/jina-embeddings-v3 , https://arxiv.org/html/2409.10173v3
- Model2Vec: https://github.com/MinishLab/model2vec , https://huggingface.co/minishlab/potion-base-8M
- MTEB leaderboard (COULD NOT READ — JS-rendered): https://huggingface.co/spaces/mteb/leaderboard

**Training**
- sentence-transformers: https://sbert.net/ , releases https://github.com/huggingface/sentence-transformers/releases
- MNRL source: https://github.com/huggingface/sentence-transformers/blob/main/sentence_transformers/losses/MultipleNegativesRankingLoss.py
- False negatives in retriever training: https://huggingface.co/blog/dragonkue/mitigating-false-negatives-in-retriever-training
- PEFT: https://huggingface.co/blog/peft

**Rerankers**
- mxbai-rerank-v2: https://www.mixedbread.com/blog/mxbai-rerank-v2
- reranker roundups (claims only): https://mixpeek.com/curated-lists/best-rerankers , https://futureagi.com/blog/best-rerankers-for-rag-2026/

**Vector search**
- pgvector: https://github.com/pgvector/pgvector , https://www.thenile.dev/blog/pgvector-080
- pgvector DBA guide (index size measurements): https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/
- HNSW vs IVFFlat: https://bigdataboutique.com/blog/hnsw-vs-ivfflat-how-to-choose-the-right-vector-index
- ANN comparison / PQ recall ceiling: https://www.abhik.ai/concepts/embeddings/ann-comparison
- Index memory overhead: https://zilliz.com/ai-faq/how-much-memory-overhead-is-typically-introduced-by-indexes-like-hnsw-or-ivf-for-a-given-number-of-vectors-and-how-can-this-overhead-be-managed-or-configured

**Hybrid / lexical**
- RRF explainer: https://blog.serghei.pl/posts/reciprocal-rank-fusion-explained/
- Hybrid search: https://denser.ai/blog/hybrid-search-for-rag/
- SPLADE: https://github.com/naver/splade , https://dl.acm.org/doi/10.1145/3634912 , https://www.emergentmind.com/papers/2403.06789

**Attribute extraction**
- LLMs for extraction+normalisation / WDC-PAVE: https://arxiv.org/pdf/2403.02130
- MAVE: https://arxiv.org/pdf/2112.08663
- ImplicitAVE: https://arxiv.org/html/2404.15592v2

**Units**
- Pint: https://pint.readthedocs.io/
- ucumvert: https://github.com/dalito/ucumvert , https://pypi.org/project/ucumvert

**Calibration / conformal**
- Niculescu-Mizil & Caruana ICML 2005: https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Calibration in LLM-based EM (ECE, temperature scaling): https://arxiv.org/abs/2509.19557
- Conformal abstention: https://www.emergentmind.com/topics/conformal-abstention
- Cost-sensitive conformal + HITL abstention: https://arxiv.org/abs/2607.27143
- Conformal selective prediction w/ deferral: https://www.nature.com/articles/s41598-026-40637-w

**LLMs for ER**
- Peeters/Steiner/Bizer EDBT 2025: https://arxiv.org/abs/2310.11244
- ComEM (COLING 2025): https://aclanthology.org/2025.coling-main.8/ , https://github.com/tshu-w/ComEM

---

## Appendix B — Everything I could NOT verify (read this before writing any slide)

1. **MTEB leaderboard current state.** Space is JS-rendered; WebFetch got only chrome. All leaderboard
   claims here are second-hand or dated (Qwen3-8B @ 70.58 is a June-2025 fact). **VERIFY IN A BROWSER.**
2. **JointMatcher's per-dataset F1 numbers.** ScienceDirect 403. Abstract claims only.
3. **ISO 8000-110 / ISO 22745 / eOTD / UNSPSC / eCl@ss content and licensing.** Not fetched at all.
   Do not claim conformance or reuse rights.
4. **MAVE licence and download location.** Not checked. Do not build a pipeline on it before checking.
5. **Parameter counts** for bge-small (~33M), bge-large (~335M), BGE-M3 (~568M), nomic-v1.5 (~137M) —
   from memory/ambiguous snippets. Check `config.json` on HF.
6. **BGE-M3 licence** — assumed MIT by analogy with the BGE family. Check its own model card.
7. **multilingual-e5 licence** — not checked.
8. **EmbeddingGemma licence terms** — "open weights, commercial use permitted" is Google's marketing
   phrasing. Read https://ai.google.dev/gemma/terms for the actual restrictions.
9. **dedupe library licence.** Check the repo before depending on it.
10. **All reranker latency numbers.** Vendor/blog claims on unrelated hardware and passage lengths.
    Not comparable. Benchmark your own.
11. **All vector-DB latency/QPS comparisons.** Configuration-dependent; every source says so.
12. **Kaggle/Colab current GPU quotas.** These change; check in week 1.
13. **ColBERT's index-size multiplier (~100×).** Recalled, not verified.
14. **AnyMatch's reported numbers.** Existence verified, results not.
15. **Whether CPSE material masters actually contain non-English text.** Pure assumption on my part,
    driving a "cut multilingual" recommendation. Check with a domain contact — if I'm wrong, that
    recommendation flips.
16. **arXiv IDs with 26xx prefixes** appearing in my search results (e.g. 2607.27143, 2603.23710) are
    2026 papers surfaced by the search tool. I read listing snippets only, not full texts. Treat all of
    them as existence-verified and content-unverified.
