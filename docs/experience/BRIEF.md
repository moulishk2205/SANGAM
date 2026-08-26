# SIH26099 — Product Experience Blueprint: shared brief

You are designing (NOT coding) the complete visitor experience for a Smart India
Hackathon 2026 project. Output is a written blueprint. **Write no code — no React, no
CSS, no HTML, no component files.** Prose, tables, storyboards and ASCII diagrams only.

## The product

**SIH26099 — AI Standardization & Harmonization of Material Codes Across CPSEs.**
Owner: Ministry of Petroleum & Natural Gas / Chennai Petroleum Corporation Limited (CPCL),
a refinery. Judges will likely include materials-management staff who look at a refinery
material master every working day.

The problem: different Central Public Sector Enterprises describe the same physical
material completely differently. `SS HEX BOLT M10 X 50` / `STAINLESS STEEL HEXAGONAL BOLT
10MM X 50MM` / `BOLT HEX SS M10*50` are one material with three identities and three
codes. Nobody can aggregate demand, detect duplicates, or standardise procurement.

Tagline from the official problem statement: **"One Nation – One Material Code"**, while
maintaining traceability to individual CPSE codes.

## The engine that already exists and works

Built, tested (11 passing tests), committed. Pipeline:

    normalise -> extract attributes -> hybrid retrieve -> compare -> VETO -> score
    -> decide (with abstention) -> explain

- Value model handles **Point / Range / ValueSet / Unknown** (real catalogues carry
  min-max ranges and multi-valued attributes).
- Versioned abbreviation gazetteer; 11-rule extraction grammar.
- Hybrid retrieval: char-n-gram lexical + `bge-small-en-v1.5` dense, fused by RRF k=60.
- **Three-valued comparator**: AGREE / DISAGREE / UNKNOWN.
- **Critical-attribute veto is a GATE, not a weight.** `score = veto x (0.85*attribute
  agreement + 0.15*text)`. A vetoed pair scores exactly 0.
- MATCH requires EVERY critical attribute known AND agreeing; otherwise REVIEW_REQUIRED.
- UNKNOWN never vetoes and never counts as agreement.
- `check_before_create()` — same engine, same evidence, no separate code path.

### Measured numbers (real, reproducible, from our own harness)

    corpus            1,800 records from 600 canonical specs, 300 probes
    recall@1          94.3%  (hybrid)   vs  79.7%  (lexical only)   -> +14.7 points
    recall@10         97.0%
    MATCH precision   100%   MATCH recall 95.8%   F1 97.9%
    critical vetoes   2,408  of which 2,399 carried text similarity >= 0.85
    latency           p50 13 ms, p95 17 ms

### The live demo moment (actual engine output, not staged)

    source     SS HEX BOLT M10 X 50
    candidate  STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM   semantic 0.960  -> MATCH (0.994)
    candidate  SS HEX BOLT M10 X 75                          semantic 0.957  -> DISTINCT (0.000)
               veto: "Length: 50 mm vs 75 mm - differs by 25 mm, tolerance 0.5 mm"
    candidate  NUT HEX SS M10                                semantic 0.895  -> DISTINCT (0.000)
               veto: "Item type: BOLT, MACHINE vs NUT, PLAIN, HEXAGON"

**0.957 vs 0.960 — statistically indistinguishable semantic scores, opposite verdicts.**
That contrast is the entire thesis and must be the centre of the experience.

### The insight worth building the validation section around

With embeddings ON, 2,399 vetoed pairs carried similarity >= 0.85. With embeddings OFF,
only 133 did. **The better the semantic model gets, the more necessary the veto becomes.**
That inverts the usual assumption and is our strongest conceptual claim.

## Real data foundation

Canonical items, classification, attribute schema and match labels derive from the US
DLA **FLIS / PUB LOG** public catalogue (a FOIA release, effectively public domain), built
on the NATO Codification System that India's own National Codification Bureau adopted in
2008. We measured: 1,824,354 items across our commodity families, 492,965 NIINs with
multiple manufacturer part numbers, 23,610 standardization relationships, 8,183,475
attribute assertions.

## NON-NEGOTIABLE HONESTY CONSTRAINTS

These are hard rules. Violating them loses the review.

1. **The evaluation corpus is SYNTHETIC and construction-derived.** The corpus is
   generated from specs we defined, extracted by rules we wrote, labelled from those same
   specs. The 100% precision largely measures whether the extractor inverts the generator.
   It demonstrates the *pipeline is correct*; it is NOT evidence of real-world accuracy.
   The site must say this plainly, as a section, framed as engineering discipline.
2. **FLIS is not CPSE data.** Never present it as ONGC/NTPC/IOCL data. Label it
   "FLIS-derived reference data" or "prototype research dataset".
3. **Never claim** nationwide deployment, real CPSE integration, procurement savings,
   millions of CPSE records trained on, or perfect accuracy.
4. `confidence` is an **uncalibrated ranking score**, not a probability.
5. Any invented CPSE names/codes in the demo must be visibly labelled synthetic.

## Lessons from the patternbreak.ing teardown (already completed)

Verified findings we are adapting, NOT copying. No branding, copy, illustrations or
assets from that site may be reused.

- **Exactly ONE scrubbed/continuous scroll animation on the whole page** (their hero pin,
  120vh, scrub 1). All nine other ScrollTriggers were discrete `play none none reverse`
  reveals. Spend continuous scroll-coupling once, on the thesis moment.
- **`SplitText {type:"lines", mask:"lines"}`** produces most of the perceived polish for
  one config property. Lines for prose, characters only for short labels.
- Their CSS had **zero @keyframes / clip-path / mask / mix-blend-mode / will-change** —
  all motion was JS (GSAP + Lenis).
- Line-height curve tightens as size grows: ~1.40 body -> 1.20 mid -> 1.00 display ->
  0.80 giant. Most of why big type reads as designed.
- Two-family type system: one grotesque + one mono. Mono for every label/datum.
- Ink slightly off-black (#030507) on light grounds while grounds go pure black — the
  asymmetry makes inversion feel absolute.
- Container max-width 1200px, section padding 80px, centred flex columns. No 12-col grid.
- One easing family throughout (power2). Content enters from below only. Reversible.
- Their failures we must NOT reproduce: 35 <h1> and zero <h2>/<h3>; all 47 images
  alt=""; no nav/header/footer landmarks; **no prefers-reduced-motion anywhere**; a
  hard 3-second delay before ScrollTriggers registered; a WebGL runtime loaded 3x;
  canvases stuck at 1440px on a 375px viewport.

## HARD TECHNICAL CONSTRAINTS (from the approved Phase 0 plan)

- **The demo runs on localhost with Wi-Fi OFF.** Therefore: no CDN, no jsDelivr/unpkg,
  no Google Fonts at runtime, no third-party WebGL SaaS (UnicornStudio is out), no
  analytics. Everything bundled and self-hosted. Verify zero non-localhost requests.
- Stack already chosen: **Vite + React + TypeScript SPA**, FastAPI backend, Postgres.
  GSAP + Lenis self-hosted. No Next.js.
- Accessibility is a requirement, not a nicety: one h1, real heading tree, real alt text,
  landmarks, visible focus, WCAG AA contrast, and a genuine reduced-motion branch that
  disables the pin and renders final states.
- The demo must feel fast. Precompute where possible. Never make a judge wait.

## What the deliverable must cover

Landing page (editorial, cinematic, narrative) that ends by transitioning into the
Platform (precise, technical, enterprise/government-grade). Journey:

    LANDING -> SCROLL STORY -> THE PROBLEM -> THE SCALE -> WHY SIMPLE MATCHING FAILS
    -> OUR APPROACH -> AI + ENGINEERING LOGIC -> THE VETO MOMENT -> PROOF
    -> TRUST/TRANSPARENCY -> TRANSITION -> MATERIAL INTELLIGENCE PLATFORM

Platform screens: Home, Material Check, Analysis, Match Results, Material Detail,
Check-Before-Create, Evaluation/Model Insights, Data/Provenance.

## THE STANDARD

Generic is failure. Not "add animations to make it engaging" but:

> "At approximately 35-55% scroll progress, the five description cards translate toward a
> shared central axis while their individual typography progressively collapses into a
> normalised attribute representation, exposing TYPE / MATERIAL / THREAD / LENGTH as four
> canonical attributes. This is the thesis animation because it visually demonstrates the
> transformation from fragmented descriptions to standardised material identity."

**Every animation must answer: WHY DOES THIS ANIMATION EXIST? What does it communicate?**
An animation that communicates nothing must be cut.
