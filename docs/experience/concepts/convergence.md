# CONVERGENCE — creative direction for the SIH26099 landing page

**Status:** proposal, one of N competing directions. Written to be built or rejected, not admired.
**Scope:** landing page (hero → thesis → problem → scale → why matching fails → approach → veto → proof → honesty → transition). Platform screens inherit the system but are not storyboarded here.

---

## 1. THE ONE-LINE THESIS

> **Five organisations wrote five different names for the same bolt. This gives it one code — and keeps all five names attached to it, permanently, unbroken.**

Three seconds of the hero must land exactly that: *multiplicity is real, resolution is possible, nothing gets deleted.*

The third clause is not a nicety. It is the clause that decides whether a materials officer at CPCL trusts this or fears it. Standardisation projects die in Indian PSUs because the people who own the local codes believe standardisation means their records are about to be overwritten. The entire visual identity below is built to make "nothing was lost" a **visible, counted fact**, not a reassurance in a paragraph.

---

## 2. NAME AND IDENTITY

**Name: CONVERGENCE.**
**Identity law, one sentence: THE THREAD IS NEVER CUT.**

Every source record on this site stays connected to its canonical record by a literal 1px line. That line is drawn once, in the thesis animation, and it persists into the platform UI as the provenance rail. There is **exactly one cut thread in the entire experience** — the veto (§6). Because the site has spent the whole page establishing that lines don't break, the single break carries the force of a verdict. That is the structural spine of this direction and the thing I would fight hardest to keep.

### Emotional register: CLINICAL–MONUMENTAL

Not investigative. Investigative journalism-styling (the register the patternbreak.ing teardown lives in) says *someone did something wrong and we are exposing it*. That register is actively harmful here. The CPSEs did nothing wrong. NTPC's code for a bolt is not a scandal; it is the rational output of an organisation that procured independently for forty years. If the page's tone implies the audience's own catalogues are the villain, we lose the room in the first section. **Rejected register: investigative.**

Not playful, not "startup". Materials-management staff read a material master every working day. They have been shown many polished procurement pitches. Delight reads as inexperience.

**Clinical** means: mono for every datum, arithmetic shown rather than asserted, counters that reconcile, no adjectives on numbers, tolerances stated. It buys credibility with the person who knows the domain.

**Monumental** means: giant type at 0.86 line-height, absolute black inversions, whitespace as authority, one gesture per section. It buys attention from the judge who does not know the domain and is scoring "does this feel like national infrastructure or a college project?"

The blend is the register of a **standards document that happens to move**. Think of the physical artefact this page is imitating: a national register being drawn up, in public, at speed. That is a feeling a government judge already respects, and it is not a feeling any design portfolio site has, which is exactly why it is available to us.

---

## 3. HERO, IN EXTREME DETAIL

### 3.1 Composition (1440×900 reference)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SIH26099 · MINISTRY OF PETROLEUM & NATURAL GAS / CPCL      [ SYNTHETIC ] │  ← 40px from top,
│                                                                          │    mono 11/1.0, GRAPHITE
│                                                                          │
│      REF-SOUTH · MM-4471                                                 │
│        SS HEX BOLT M10 X 50                                              │  ← OPTICAL CENTRE
│                    PIPELINE-DIV · 100238841                              │    five rows, occupying
│                      STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM          │    y = 22%…52% of viewport
│   PETCHEM-WEST · B-HX-SS-1050                                            │    each on its OWN left origin
│     BOLT HEX SS M10*50                                                   │
│              TERMINAL-EAST · 55021907                                    │
│                HEX BOLT, S/S, M10 X 50 MM (OLD SPEC)                     │
│         REF-NORTH · 4471-A                                               │
│           BOLT,HEXAGON HEAD,STAINLESS,M10X50                             │
│                                                                          │
│  One bolt.                                                               │  ← h1, three lines,
│  Five names.                                                             │    Archivo Expanded 112px,
│  No code in common.                                                      │    line-height 0.86, INK
│                                                                          │
│  One Nation – One Material Code. Traceability to every CPSE code kept.   │  ← mono 15/1.42 GRAPHITE
│                                                                          │
│  SCROLL TO RESOLVE  ↓          34 TOKENS · 0 MAPPED · 0 DISCARDED        │  ← bottom rail, mono 11
└──────────────────────────────────────────────────────────────────────────┘
```

**What occupies the optical centre: the evidence, not the headline.** The five descriptions sit in the upper-middle third where the eye lands first. The h1 sits *below* them and functions as a caption to evidence already seen. This inversion is deliberate and is the hero's whole idea: a judge who reads nothing but the five rows already has the problem statement. The headline only names what they just noticed themselves. A hero that leads with a slogan and supports it with a screenshot is the default; this is the reverse, and it converts faster with a domain audience because domain audiences trust artefacts over claims.

**Why the rows are misaligned.** Each row has its own left origin (offsets from the container's left edge: +12px, +148px, 0px, +96px, +40px), its own org-code chip position, and its own optical type size (13px, 13px, 14px, 13px, 14px — small enough not to read as hierarchy, large enough that the block never looks like a tidy list). Five systems that never spoke to each other do not share a grid. The messiness is the argument. If these five rows were flush-left in a neat stack, the page would be showing a *list of synonyms*; misaligned, it shows *five institutions operating independently*.

**Synthetic labelling.** Org labels are functional, not corporate: `REF-SOUTH`, `PIPELINE-DIV`, `PETCHEM-WEST`, `TERMINAL-EAST`, `REF-NORTH`. No invented company names, no real CPSE names. One persistent `SYNTHETIC` chip pinned top-right of the viewport for the whole hero and thesis section — it is part of the chrome, always visible, never a footnote. Copy on hover/focus: *"Source records are synthetic, constructed for demonstration. Classification and attribute schema derive from the public FLIS/PUB LOG catalogue. Not CPSE data."*

### 3.2 Load choreography

Two laws govern all motion on this site, established here in the first 1.4 seconds:

> **PROSE EASES. DATA SNAPS.**
> Sentences and headings move on `power2.out`. Codes, counters, chips and verdicts change with no easing and no travel — a step cut, 90–120ms opacity or a stepped character reveal. A number that glides is a number being sold to you. A number that snaps is a number being reported.

| t (ms) | Element | Motion | Duration | Ease | Stagger |
|---|---|---|---|---|---|
| 0 | Ground, container, bottom rail | painted at rest, opacity 1 | — | — | — |
| 0 | Five description strings | present at final position, opacity 0 | — | — | — |
| 120 | h1, 3 lines, `SplitText {type:"lines", mask:"lines"}` | rise from y +100% of own line box | 700ms | power2.out | 80ms per line |
| 200 | Five description strings | opacity 0→1, y +12→0 | 500ms | power2.out | 60ms, **scrambled order** |
| 560 | Five org-code chips | opacity 0→1, no travel | 120ms each | none (step) | 90ms |
| 900 | Eyebrow + `SYNTHETIC` chip | opacity 0→0.85 | 300ms | power2.out | — |
| 1000 | Bottom rail counter | opacity 0→1, digits set to final values instantly | 300ms | none | — |
| ~1400 | settled | | | | |

**The scrambled stagger is the single most important detail in the hero.** The five rows do not animate top-to-bottom. They animate in the order 3 → 1 → 5 → 2 → 4. A top-to-bottom stagger reads as *a list being rendered*. A scrambled stagger reads as *five independent systems reporting in on their own schedule*. Same cost, opposite meaning. This is what "why does this animation exist" produces when you actually ask it.

**Nothing the judge needs waits on animation.** The evidence rows are in the DOM at final position from paint; only their opacity is animated, and it completes by 900ms. No 3-second ScrollTrigger delay (the teardown's worst failure). If GSAP fails to initialise for any reason, a `.js-failed` class on `<html>` renders every hero element at its final state — the hero is fully legible with zero JavaScript.

### 3.3 The first three seconds, as an eye path

1. **0–0.6s** — eye goes to the five rows because they are the largest mass and the only thing changing. It reads two, maybe three of them. It notices they are the *same object described differently* before any text says so. The scramble makes the block feel alive rather than rendered.
2. **0.6–1.4s** — eye drops to the h1 arriving underneath. "One bolt. Five names. No code in common." confirms what it just inferred. Confirmation of a self-made inference is far stickier than being told.
3. **1.4–3.0s** — eye sweeps the bottom rail: `34 TOKENS · 0 MAPPED · 0 DISCARDED`. Two things register: this system counts things, and the count starts at zero. The word DISCARDED, sitting at zero before anything has happened, plants the promise the thesis animation will pay off.

---

## 4. THE ONE THESIS ANIMATION — "THE RESOLUTION"

**This is the entire continuous-scroll budget for the landing page.** Every other motion on the page is a discrete reveal, a hover, a state change or a loading state. Justification for the spend: this is the only moment where the *transformation itself* — not the before, not the after — is the product. Standardisation is a process claim. A before/after pair asserts it. A scrubbed transformation lets the judge audit it at their own speed, stop mid-way, scroll back, and check that the machine did what it said. **Scrub gives the judge control of the evidence.** That is worth the whole budget and nothing else on the page needs it.

**Pin:** 420vh of scroll travel, `scrub: 1`, pin the section, no snap.
**Unpin:** at progress 1.0, when the canonical record and its five threads have settled. The pin releases and the record scrolls up normally into "THE SCALE".
**Carry-forward:** a 44px-tall docked strip (`5306-01-234-5678 · 5 SOURCES`) remains fixed to the bottom-left for the next two sections, then dismisses. Discrete, not scrubbed.
**Mobile (<768):** 300vh, checkpoints 40 and 50 merge, convergence axis rotates from horizontal to vertical (see §8 — this is a real loss).
**Reduced motion:** no pin. The section renders the 100% state immediately, plus a four-step keyboard/click stepper labelled `1 TOKENISE · 2 CLASSIFY · 3 RESOLVE · 4 LINK` that swaps between four static composites. See §8 for the honest cost.

### 4.1 What happens to the TEXT — the four fates

This is the heart of the direction, so it is specified as a taxonomy before the frames. Every one of the 34 tokens has exactly one fate. All four fates are visible on screen simultaneously and all four are legended in the left gutter.

| Fate | Applies to | What the token does | Example |
|---|---|---|---|
| **CARRIED** | token maps directly to a canonical attribute value | travels along a curved path to its destination row, lands, and re-typesets from the source's 13px mono into the canonical 16px mono at a heavier weight | `BOLT` → ITEM TYPE |
| **EXPANDED** | abbreviation resolved by the versioned gazetteer | travels, then on landing the token **box grows in width** while the original letters hold their position and the remainder arrives inside it | `SS` → `STAINLESS STEEL`; `S/S` → `STAINLESS STEEL` |
| **NORMALISED** | units, separators and dimension forms | travels, converts form on landing, and leaves a 9px ghost of its source form above the canonical value for ~8% of scroll before the ghost migrates into the provenance drawer | `50MM`, `10MM X 50MM`, `M10X50` → `50 mm` |
| **RETAINED** | surplus: separators, org-local noise | does **not** travel. Falls straight down, decelerating, into a bar at the base of the composition: `RETAINED IN SOURCE RECORD` | `X`, `*`, `(OLD SPEC)` |

**Explicitly rejected: strike-through.** A struck-out token says *this was wrong*. The five source descriptions are not wrong — they are local, correct-in-context, and written by the exact people sitting in the judging room. Striking them is an insult rendered as a design flourish. **Rejected.**
**Explicitly rejected: dissolve / particle-scatter.** Dissolving a token says *this ceased to exist*, which is the precise fear we are designing against, and it is also a lie: the source record persists in the database. **Rejected.**
**Explicitly rejected: per-character scramble on expansion.** The "hacker text" effect is illegible mid-flight, communicates "randomness" when the gazetteer is deterministic and versioned, and would misrepresent the engine. Width-growth with held letters communicates *lookup*. **Rejected.**

**How the viewer knows nothing was lost:** a live reconciling counter on the bottom rail, present since the hero, always summing to 34.

```
TOKENS 34   MAPPED 0→28   RETAINED 0→6   DISCARDED 0
```

`DISCARDED 0` never moves. It sits there for 420vh of scroll being zero. A number that visibly refuses to move is a stronger promise than a sentence.

### 4.2 The five source records and the canonical destination

```
REF-SOUTH     · MM-4471          SS HEX BOLT M10 X 50                        6 tokens
PIPELINE-DIV  · 100238841        STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM  7 tokens
PETCHEM-WEST  · B-HX-SS-1050     BOLT HEX SS M10*50                          6 tokens
TERMINAL-EAST · 55021907         HEX BOLT, S/S, M10 X 50 MM (OLD SPEC)       8 tokens
REF-NORTH     · 4471-A           BOLT,HEXAGON HEAD,STAINLESS,M10X50          7 tokens
                                                                        total 34
```

```
CANONICAL RECORD          5306-01-234-5678        [SYNTHETIC · ILLUSTRATIVE]
─────────────────────────────────────────────────────────────────────────────
ITEM TYPE         BOLT, MACHINE                                     critical
MATERIAL          STAINLESS STEEL                                   critical
THREAD            M10                                               critical
LENGTH            50 mm                          ± 0.5 mm           critical
CLASSIFICATION    FSC 5306 · BOLTS               FLIS/PUB LOG derived
SOURCES           5 records · 5 CPSE codes retained
─────────────────────────────────────────────────────────────────────────────
6 tokens retained in source records · 0 discarded
```

### 4.3 Frame by frame

---

**PROGRESS 0%** — *nothing has happened yet*

- **On screen:** the five rows, re-established at exactly the optical position the hero left them (visual continuity: the section reads as the hero continuing, not a new scene). Left gutter empty. Right gutter empty. Bottom rail: `TOKENS 34 · MAPPED 0 · RETAINED 0 · DISCARDED 0`.
- **Moving:** nothing. The first 3% of the pin is deliberately dead so the judge registers that the page has stopped and something is about to be shown to them.
- **Understands:** *this is the same five records I saw. The page has taken hold of them.*

---

**PROGRESS 10%** — *tokenisation*

- **Changed:** each row's text acquires token boundaries. Word spacing opens by +4px, and a 0.5px hairline box at 12% INK opacity draws around each token, left→right within each row.
- **Moving:** five simultaneous but **desynchronised** left-to-right draws. Row 3 completes at 7% progress, row 4 at 12%. Each row tokenises at its own rate.
- **Why desynchronised:** five independent systems, five independent parses. Same reason as the hero's scrambled stagger — synchrony would imply a single system, which is the thing that does not exist yet.
- **Understands:** *the machine is not reading these as sentences. It is reading them as parts.*

---

**PROGRESS 25%** — *classification, before any movement*

- **Changed:** each token box takes one of four visual states, by **border and mark, never by fill colour alone**: CARRIED = solid hairline; EXPANDED = solid hairline + a 6px chevron at the right edge; NORMALISED = solid hairline + a small `mm`/`×` unit tick below baseline; RETAINED = dashed hairline at 45% opacity. A four-line legend snaps into the left gutter (mono 11px, no easing, 80ms stagger — data snaps).
- **Moving:** only the legend. **The rows have still not moved.** This is a deliberate 15% of scroll spent on stillness.
- **Why the stillness:** the single most common failure of a "transformation" animation is that the viewer cannot tell what rule produced the outcome. By showing the *classification* fully, before a single token travels, we let the judge audit the decision independently of the choreography. When things start moving at 40%, they are watching a plan execute, not a magic trick.
- **Understands:** *it has already decided what every fragment is. I can check its work.*

---

**PROGRESS 40%** — *the destination appears; convergence begins*

- **Changed:** two things at once.
  1. The five rows begin translating toward a shared central vertical axis (each `x → 0`), scale 1.0 → 0.82, and compress to a single line each. They are converging in *position* while their contents have not yet moved.
  2. In the centre, an empty canonical frame draws: six label rows (`ITEM TYPE / MATERIAL / THREAD / LENGTH / CLASSIFICATION / SOURCES`), values blank, each blank value marked by a thin baseline rule. The frame's border is dashed at this stage — it is a form, not yet a record. Four of the rows carry a small `critical` tick in the right gutter.
- **Moving:** row translation (power2.inOut across 40→58%), frame draw (linear stroke, 40→46%).
- **Understands:** *there is a destination. It has exactly four critical slots, and it is empty. Something has to fill it.*

---

**PROGRESS 50%** — *migration, in attribute order*

- **Changed:** tokens detach from their rows and travel to the canonical frame along quadratic curves whose control point is pulled toward the centre axis — the flight paths are visibly the same family of curve as the threads that will be drawn at 90%.
- **The ordering rule:** tokens migrate **grouped by destination attribute, not by source row.** All five ITEM TYPE tokens leave first, from five different rows simultaneously. Then all MATERIAL tokens. Then THREAD. Then LENGTH. Within a group, 0.02 of progress stagger; between groups, 0.03.
- **Why that ordering is the whole point:** it re-cuts the data across the grain. The viewer has spent 50% of the animation seeing information organised *by organisation*. Watching it leave *by attribute* is the visual statement of what harmonisation actually is: the same facts, re-indexed on a shared axis. Row-by-row migration would communicate "five things got processed in turn" — an assembly line, not a standard.
- **Counter:** increments live as tokens land. `MAPPED 0 → 14` by 58%.
- **Understands:** *these five organisations were saying the same four things the entire time. The system reorganises across organisations, not inside them.*

---

**PROGRESS 65%** — *merge, expansion, and the fall*

- **Changed, three simultaneous events:**
  1. **Merge.** Arriving tokens stack on their destination row and collapse. Five variants of the item-type token (`BOLT` / `HEX BOLT` / `BOLT HEX` / `BOLT,HEXAGON HEAD`) compress into one value `BOLT, MACHINE` with a scale 1.06 → 1.00 landing — a slight over-scale that reads as *these pressed together*, not as bounce. No elastic easing anywhere on this site.
  2. **Expansion.** `SS` and `S/S` land on MATERIAL and grow into `STAINLESS STEEL`: the `S` holds its x-position, the box widens rightward over 180ms of scroll-equivalent, the remaining glyphs arrive inside the widening box at 60% opacity → 100%. A mono 10px note prints in the right gutter: `gazetteer v3 · SS → STAINLESS STEEL`. **Naming the gazetteer version is a credibility move**: it says a human maintains a versioned dictionary, which is exactly what a materials officer wants to hear and exactly what an LLM-only pitch cannot say.
  3. **The fall.** The six RETAINED tokens (`X`, `X`, `*`, `X`, `(OLD SPEC)`, `X`) drop straight down, decelerating on power2.out over 12% of progress, and land in a bar at the base: `RETAINED IN SOURCE RECORD — 6`. They stay legible. They are not greyed to invisibility; they sit at 60% opacity, readable.
- **Counter:** `MAPPED 28 · RETAINED 6 · DISCARDED 0`. Sums to 34 on screen.
- **Understands:** *nothing was thrown away. The abbreviations were resolved by a dictionary somebody maintains, not guessed at.*

---

**PROGRESS 75%** — *the record exists*

- **Changed:** every value cell is filled. The frame's dashed border goes solid 1px INK. A header bar appears and the canonical code types in per character with a stepped reveal, 40ms/char, no easing: `5306-01-234-5678`. The `SYNTHETIC · ILLUSTRATIVE` chip is attached to the code in the same header bar — physically adjacent, impossible to screenshot the code without the chip. The CLASSIFICATION row fills with `FSC 5306 · BOLTS` and a 10px note `derived from FLIS/PUB LOG public catalogue · not CPSE data`.
- **Moving:** only the code characters and the border stroke.
- **Understands:** *one code now exists. And the page is telling me, unprompted, what is real about it and what is not.*

---

**PROGRESS 90%** — *the satellites, and the threads*

- **Changed:** the five demoted source rows emerge from behind the canonical card and travel outward to fixed satellite positions — two in the left gutter (y = 22%, 62%), three in the right (y = 16%, 44%, 74%). Each shrinks to a single 12px mono line: `REF-SOUTH · MM-4471 · SS HEX BOLT M10 X 50`. Then five 1px threads draw, **from satellite to card**, at 0.35 opacity, terminating on the SOURCES row. The SOURCES row fills: `5 SOURCE RECORDS · 5 CPSE CODES RETAINED`.
- **Direction matters:** the threads draw *inward*, from the sources toward the standard. Provenance flows up into the canonical record. Drawing them outward from the card would read as the centre asserting authority over the periphery — the exact political reading we must avoid.
- **Understands:** **the whole thesis.** *One code. Five codes still there. Still readable. Still connected.*

---

**PROGRESS 100%** — *settle*

- **Changed:** threads reach full 0.35 opacity and stop. The retained-token bar collapses into a 24px strip docked to the base of the card: `6 tokens retained in source records · 0 discarded`. One mono line prints below the card, 13px, GRAPHITE:

  > `Every source code resolves to this record. This record resolves back to every source code.`

- **Moving:** nothing. Two percent of dead scroll before unpin, so the composition is held still and readable at rest before the page moves on.
- **Understands:** *this is bidirectional. I can go from my code to the standard and from the standard back to my code. My records are not going away.*
- **Unpin.**

### 4.4 Nothing is communicated by motion alone

Every state in the animation has a concurrent text equivalent that survives with animation disabled: the four-fate legend (text), the reconciling counter (text), the `critical` ticks (text), the gazetteer note (text), the SOURCES row (text), the retained strip (text), the closing bidirectional sentence (text). The static 100% composite is a complete, self-explanatory diagram. That is the acceptance test for the reduced-motion path, and it is also the acceptance test for a printed screenshot in a judging pack.

---

## 5. VISUAL SYSTEM

### 5.1 Palette — derived from IS 2379 pipeline identification colours

Seven values. The derivation matters: **IS 2379 is the Indian Standard for colour-coding pipelines in process plants.** Every one of our judges from CPCL has walked past those colours every working day for years. Building the palette from that source produces something that is (a) native to refineries, (b) not a design-trend palette, (c) impossible to arrive at by defaulting, and (d) not remotely the fast-fashion palette of the teardown. This is our strongest claim to owning the look.

| Name | Hex | Role |
|---|---|---|
| `GROUND` | `#F4F2EE` | Warm off-white. Default ground. Ledger paper, not screen-white. |
| `INK` | `#0B0D0C` | Off-black type on light grounds. Never pure black on light. |
| `VOID` | `#000000` | Pure black ground for inverted sections (veto, transition to platform). The asymmetry with INK is what makes inversion feel absolute. |
| `GRAPHITE` | `#6B6F6E` | IS 2379 smoke-grey. Secondary type, satellites, hairlines, all mono labels at rest. |
| `SEAGREEN` | `#1F6F5C` | IS 2379 water. **Role: CANONICAL / AGREE.** The one code, the threads, the resolved value. Institutional, not SaaS-blue. |
| `OXIDE` | `#8C2F17` | Refinery primer / seal ink. **Role: VETO / DISAGREE.** A stamp, not an error. |
| `CANARY` | `#E8B21A` | IS 2379 gases. **Role: UNKNOWN / REVIEW_REQUIRED / abstention.** |

The three-value mapping is not decoration — the comparator is genuinely three-valued (AGREE / DISAGREE / UNKNOWN) and needs three visually non-adjacent marks. UNKNOWN having its own colour, distinct from both success and failure, is the palette doing real semantic work.

**Contrast, checked honestly.** `SEAGREEN` and `OXIDE` on `GROUND` both clear WCAG AA for body text. **`CANARY` on `GROUND` does not** (≈2.1:1). Therefore CANARY is only ever used as a fill with INK type on top, or as a 4px marker rule; when UNKNOWN must appear as text, it uses `#8A6608` (AA-compliant) with the CANARY mark beside it. Stating this rather than discovering it in review is part of the register.

**No state is ever colour-only.** AGREE / DISAGREE / UNKNOWN each carry a word and a distinct glyph (`=` / `≠` / `?`) alongside the colour.

### 5.2 Type

Two families, both OFL-licensed, both self-hosted as subset woff2 — **no runtime font fetch, no Google Fonts, verified zero non-localhost requests.**

- **Grotesque: Archivo** (incl. Archivo Expanded for the giant display cut). Institutional, slightly squared, expandable to monumental widths without buying a licence.
- **Mono: IBM Plex Mono.** Every label, every code, every datum, every counter, every verdict.

**Subset requirement:** Latin basic plus `× ± ≥ ≤ · → ↓ ≠ ° §`. The `×` in `M10 × 50` and the `±` in `± 0.5 mm` are load-bearing — if the subset misses them the demo renders tofu with Wi-Fi off and there is no fallback. Flagging this explicitly because it is exactly the class of bug that only appears offline.

| Role | Family / cut | Size (desktop) | Line-height |
|---|---|---|---|
| GIANT display | Archivo Expanded, 600 | 112–128px (clamp 13vw) | **0.86** |
| DISPLAY / section head | Archivo, 600 | 64px | **1.02** |
| MID / sub-head, pull-quote | Archivo, 500 | 32px | **1.24** |
| BODY prose | Archivo, 400 | 18px | **1.42** |
| DATUM / record values | IBM Plex Mono, 500 | 16px | 1.30 |
| LABEL / chips / counters | IBM Plex Mono, 400 | 11–13px | 1.00, tracking +0.06em, uppercase |

The line-height curve tightening as size grows (1.42 → 1.24 → 1.02 → 0.86) is the single highest-yield typographic decision available and is adopted directly as a principle from the teardown analysis.

**Heading tree:** exactly one `<h1>` (the hero). Every section is `<h2>`. Sub-blocks are `<h3>`. Mono labels are `<dt>`/`<span>`, never headings. This is a direct correction of the teardown's 35-`<h1>` failure.

### 5.3 Layout skeleton — the register spine

Container 1200px, section padding 96px desktop / 56px mobile, centred column, **no 12-column grid.** But CONVERGENCE adds one structural element that the teardown does not have:

```
│← 140px →│←────────── 760px max ──────────→│← 140px →│
   LEFT              CENTRE                    RIGHT
   gutter            column                    gutter
   ─────────         ──────────                ─────────
   legends           prose                     counters
   satellites        headings                  tolerances
   step markers      the record                provenance notes
   section index     the veto                  gazetteer versions
```

The gutters are always populated with mono, always at 11–13px, always secondary. They are what make the page read as an *instrument* rather than a *pitch deck*. They are also where the honesty constraints live permanently: the synthetic chip, the FLIS attribution and the "uncalibrated ranking score" note are gutter furniture, present continuously, not confined to a disclaimer section.

Below 1024px the gutters collapse: left-gutter content becomes a strip above its section, right-gutter content becomes a strip below. Nothing is dropped.

### 5.4 What makes this OURS

1. **The never-cut thread**, and the single break at the veto.
2. **A palette derived from IS 2379 refinery pipeline colours** — subject-native, unavailable to anyone not building for this domain.
3. **The four-fate token taxonomy with a `DISCARDED 0` counter** that never moves for 420vh.
4. **Prose eases, data snaps** as an enforced two-law motion system.
5. **The register spine**, with honesty constraints as permanent gutter furniture rather than a disclaimer footer.

None of these are transferable to a fast-fashion essay, a SaaS landing page, or anything else. That is the test.

---

## 6. THE VETO MOMENT

Section: `WHY SIMPLE MATCHING FAILS`. Ground inverts to `VOID` — pure black, absolute. This is the only full inversion on the landing page before the platform transition.

**The setup.** The canonical record from the thesis animation is now at the top of the frame. Three candidates are presented as identical rows, each with its semantic similarity printed in mono at 24px:

```
STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM     semantic  0.960
SS HEX BOLT M10 X 75                           semantic  0.957
NUT HEX SS M10                                 semantic  0.895
```

All three enter identically — same rise, same duration, same easing, zero differentiation. The judge is given several seconds where 0.960 and 0.957 are visibly, arithmetically indistinguishable. **That stillness is the setup and it must not be rushed.** The whole thesis lives in the gap between two numbers that differ by 0.003.

### What changes at the instant of veto

Four things, and none of them is an error state.

1. **The score is replaced, not decayed.** `0.994` does not count down. It is cut to `0.000` in one 90ms step — no easing, no travel, no tween. A number that animates downward reads as *degrading*, as if a good match got worse. A number that is *replaced* reads as *a different rule applied*.
2. **The arithmetic prints.** Immediately below, in mono 15px, over 400ms:
   `score = veto × (0.85 · attribute_agreement + 0.15 · text) = 0 × (0.91) = 0.000`
   **Authority comes from showing the arithmetic, not from a colour.** A materials officer does not trust a red badge; they trust a multiplication by zero they can verify in their head. This single line is the most persuasive object on the entire site and it is a line of type, not an animation.
3. **The gate closes.** The disagreeing attribute row gains a solid OXIDE rule spanning the full record width, with the two values sitting either side of a hard vertical rule:
   `LENGTH   50 mm │ 75 mm   differs by 25 mm · tolerance 0.5 mm`
   The rule draws from the centre outward, 200ms, linear. A gate closing is horizontal and mechanical. It does not pulse, glow, shake or flash.
4. **The thread is cut.** The candidate's thread to the canonical record — drawn in the same 1px, same curve family as the five satellite threads — **breaks**, with a small 4px OXIDE square marking the break point. This is the only cut line in the entire experience. Because the site has spent 420vh of scroll and an entire identity law establishing that threads never break, the break lands with the force of a verdict rather than the noise of an alert.

**What deliberately does NOT happen:** no shake, no flash, no screen-wide red, no sound (the room is offline and full of people), no icon, no toast. Rejection is delivered the way an authoritative body delivers rejection — quietly, in writing, with the reasoning attached.

**Then the second veto,** on `NUT HEX SS M10`, runs the identical choreography at 60% duration. Repeating a mechanism at reduced ceremony converts a moment into a *rule*:
`ITEM TYPE   BOLT, MACHINE │ NUT, PLAIN, HEXAGON`

**Then the inversion of the assumption.** Static, discrete, one line of giant type on VOID:

> **The better the semantic model gets, the more necessary the veto becomes.**

supported by a two-bar static comparison — embeddings ON: 2,399 vetoed pairs at similarity ≥ 0.85; embeddings OFF: 133. Bars draw once, 600ms, power2.out, then never again. No odometer on the numbers (see §7).

---

## 7. WHY EACH ANIMATION EXISTS

| # | Animation | Type | What it communicates | What is lost if cut |
|---|---|---|---|---|
| 1 | Hero h1 line-mask rise | discrete | Establishes prose-eases law; gives the headline the feel of being *set*, like type in a register | The hero reads as a static poster; the two-law motion system has no first example |
| 2 | Hero five-row **scrambled** stagger | discrete | Five independent systems reporting on independent schedules — the problem itself | Becomes "a list rendering". The entire premise of independence collapses into tidiness |
| 3 | Org-code chips snapping (no ease) | discrete | Data snaps. Codes are reported, not performed | The prose/data distinction is never established, so the veto's step-cut at §6 has no grammar to land in |
| 4 | **THE RESOLUTION** (420vh scrubbed pin) | **the one continuous** | Fragmentation → single identity, auditable at the viewer's own pace, with conservation of every token | Everything. This is the product |
| 5 | Token fall to RETAINED bar | inside #4 | Nothing was discarded — the fear that kills standardisation projects | The convergence reads as deletion. Worst possible failure mode of this direction |
| 6 | Threads drawing satellite → card | inside #4 | Traceability to individual CPSE codes, as required by the problem statement, and its direction of flow | We *claim* traceability instead of *showing* it. The problem statement's second clause goes unanswered |
| 7 | Veto score step-cut to 0.000 | discrete state change | The veto is a gate, not a weight — a different rule, not a worse score | Reads as degradation. The gate-vs-weight distinction, which is the engineering thesis, is lost |
| 8 | Veto gate rule drawing centre-out | discrete | A mechanical, deliberate closure | Rejection reads as a UI error |
| 9 | The one cut thread | discrete | Authoritative rejection, paid for by the identity law | The veto is just red text |
| 10 | Section heading reveals (`SplitText` lines, mask) | discrete | Rhythm; nothing semantic | Nothing semantic — kept only because it costs one config property and carries the page's polish. **First thing cut under time pressure.** |
| 11 | Ground inversion GROUND → VOID at the veto | discrete | A change of jurisdiction: we have left explanation and entered adjudication | The veto section feels like more of the same page |

### Cut here, with reasons

| Cut | Why |
|---|---|
| **Odometer count-ups on 94.3% / 1.8M / 13ms** | Communicates "number goes up", not meaning. A rolling number is also a number you cannot read while it moves — actively hostile to a judge trying to note a figure. All statistics print at final value, instantly. |
| **WebGL / canvas particle field of 1,824,354 FLIS items for "THE SCALE"** | Tempting and wrong. Animating 1.8M points implies we processed 1.8M records live and implies they are CPSE records. Both overstate. Replaced by a static printed statement with its source labelled, plus one static ranked bar. **This cut is required by honesty constraint 2, not by taste.** |
| **Section-background parallax** | Communicates nothing. Costs scroll performance on an integrated-GPU judging laptop. |
| **Card hover tilt / magnetic cursor / custom cursor** | Register violation. This is a materials register, not a portfolio. |
| **A second scrubbed animation for the veto** | Budget. The veto is stronger as three hard state changes than as something the judge can scrub back and forth; a verdict you can rewind is not a verdict. |
| **Loading/skeleton shimmer** | The demo is precomputed and local. If anything shimmers, we have a performance problem to fix, not an animation to add. |

---

## 8. HONEST WEAKNESSES

**8.1 The direction demands that the storyboard match the engine, exactly.**
Thirty-four tokens each need a fate, a destination and a path. If the real pipeline tokenises `S/S` differently, or maps `HEAD` somewhere I have not anticipated, the animation becomes a beautiful fiction — and a judge from CPCL is precisely the person who will ask "is that what your code actually does?" **Mitigation: generate the token map from real engine output at build time and commit it as a JSON fixture.** If that cannot be done in the time available, the section must carry an `ILLUSTRATIVE` label and we lose some of the credibility the whole direction is built on. This is the highest-severity risk in the proposal.

**8.2 The reduced-motion path is genuinely weaker, and I will not pretend otherwise.**
The thesis of this direction is a *transformation*. A transformation shown statically is a before/after pair, which is exactly the weak form I argued against in §4. The four-step stepper is a real, keyboard-accessible, complete fallback — but it is a lesser experience, and a judge using reduced motion sees a good diagram rather than a compelling argument. Claiming parity would be dishonest. The mitigation is that the *static* composite must be strong enough to stand alone as a printed diagram, and it should be designed first, before the motion, so the motion is an enhancement of something already complete.

**8.3 Mobile changes the metaphor, not just the layout.**
The three-zone spine and a five-satellite ring do not fit 375px. Satellites become a stacked list below the record; threads become left-edge brackets; convergence rotates from horizontal (many organisations, one axis) to vertical (a list collapsing upward). **The vertical version means something weaker** — "a list got shorter" rather than "independent institutions met on a shared axis". I do not have a fix for this that preserves the metaphor. If the demo is judged on a phone, this direction is measurably worse than it is on a laptop. It should be pitched, and rehearsed, on a laptop.

**8.4 Performance is the build's main enemy.**
420vh pinned with ~34 individually-transformed elements is the most expensive thing on the page by a wide margin, on a judging laptop we do not control. Non-negotiable budget: transform and opacity only, never layout properties, no `filter`, no animated `box-shadow`; destination coordinates measured once on pin-enter and on resize only; hard cap of 34 animated nodes; the retained-token bar and the legend are static DOM, not per-frame updates. If it cannot hold 60fps on integrated graphics, the honest response is to cut the token count from 34 to 20 by shortening two of the source strings — **not** to reduce the pin length, because the animation's readability depends on the dead-scroll pauses at 0–3%, 25–40% and 98–100%.

**8.5 The synthetic-labelling requirement blunts the emotional punch.**
Honesty constraint 5 means the five organisations must be visibly synthetic. Every `SYNTHETIC` chip is a small withdrawal from the judge's immersion. Using functional labels (`REF-SOUTH`, `PIPELINE-DIV`) instead of invented company names softens this, but it does not eliminate it — a judge may still register the scenario as a toy. I accept the cost. The alternative loses the review outright.

**8.6 The IS 2379 palette derivation is a rationale, not a claim.**
Sea-green means *water* in IS 2379; it does not mean *canonical*. A judge who knows the standard cold could find our mapping arbitrary. Therefore the derivation stays in this design document and **never appears in the UI**. If we put "palette derived from IS 2379" on the site, we invite an argument we cannot win. It is a mnemonic for us, not a claim to them.

**8.7 The central fragility: convergence can read as erasure.**
Everything in §4 is defensive engineering against one sentence a judge might think: *"so my codes get deleted."* The retained counter, the never-cut threads, the rejection of strike-through and dissolve, the inward thread direction — all of it exists to prevent that reading. But it only takes **one frame** that looks like deletion to plant it, and once planted it is not recoverable in the same session. Before build, the 25%, 50% and 65% composites must be shown, static and silent, to someone who works in materials management, with exactly one question asked: *"what happened to the original descriptions?"* If the answer is not immediately "they're still there", the direction is not working and no amount of polish will fix it.

---

## APPENDIX — SCROLL BUDGET LEDGER

| Section | Motion type | Continuous budget used |
|---|---|---|
| Hero | discrete reveals (load choreography) | 0 |
| THE RESOLUTION | **pinned, scrub 1, 420vh** | **1 of 1** |
| THE PROBLEM / THE SCALE | discrete reveals, static statistics | 0 |
| WHY SIMPLE MATCHING FAILS (veto) | discrete state changes + ground inversion | 0 |
| OUR APPROACH / AI + ENGINEERING LOGIC | discrete reveals | 0 |
| PROOF | discrete reveals, static bars drawn once | 0 |
| TRUST / TRANSPARENCY (synthetic-corpus section) | no motion at all — deliberate | 0 |
| TRANSITION TO PLATFORM | discrete ground inversion + fade | 0 |
| **Total continuous** | | **1 of 1 — budget met** |

The honesty section having **zero motion** is itself the design decision: the one place on the page where nothing moves is the place where we tell the judge what our numbers do not prove.
