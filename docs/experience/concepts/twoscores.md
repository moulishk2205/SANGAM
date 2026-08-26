# CREATIVE DIRECTION — "THREE THOUSANDTHS"
## The two-numbers direction for SIH26099

> One of three competing directions. This one bets the entire landing page on the single
> most arresting fact we own: **0.960 and 0.957 are the same number to any reasonable eye,
> and they produce opposite verdicts.** No hero object, no photograph, no illustration.
> Typography, a hairline, and two words.

---

## 1. THE ONE-LINE THESIS

**Two material descriptions scored three thousandths apart by an AI model — one is the
same bolt, one is a different bolt, and no similarity threshold can tell you which.**

What the visitor holds in their head after 3 seconds is not a claim, it is a **question
they cannot dismiss**: *why are these two answers opposite?* A question is a stronger
3-second payload than a statement, because a statement can be agreed with and abandoned,
while an unresolved question pulls the scroll. The entire page is the resolution of that
question, and the resolution is: *because we compare attributes under a veto gate, not
text under a threshold.*

---

## 2. NAME AND IDENTITY

### Name

**THREE THOUSANDTHS** — internal direction name. `0.960 − 0.957 = 0.003`. The gap that
separates a correct match from an expensive mistake is three thousandths of a
dimensionless score. The name is also the page's central image: a gap so small it has to
be drawn as a hairline, and the whole page is the act of widening it.

The public-facing page never uses the name as a wordmark. The wordmark stays
**SIH26099 · One Nation – One Material Code**. "Three thousandths" is the *idea*, not the
branding — it lives in the h1 and nowhere else.

### The emotional register: **instrument-grade / forensic metrology**

Not clinical (clinical reads as medical, cold, and slightly hostile). Not monumental
(monumental overclaims, and we have honesty constraints that make monumentality a lie).
Not investigative-journalism (that register accuses; we are not accusing CPSEs of
anything, we are handing them a tool).

The register is **the calibration certificate**. The mill test report. The gauge
inspection sheet. The document a materials engineer already trusts because it states a
measured value, a tolerance, and a pass/fail, and signs its name to the method.

Concretely, that means:
- Warm off-white paper stock, not startup white and not essay black.
- Tabular mono numerals as the display face — *readouts*, not headlines.
- Every number carries its unit and, where relevant, its tolerance.
- Every claim carries a superscript provenance marker that resolves in the margin.
- A verdict is stamped, never flashed. Nothing shakes. Nothing bounces.

### Why this register, for THIS audience

**The materials-management officer from CPCL.** They open a material master every working
day. They have been burned by an M10×50 that arrived as an M10×75. Their professional
vocabulary is *nominal value, tolerance, deviation, criticality, specification*. Show them
a bouncing card with a gradient and they file the project under "students." Show them
`Length: 50 mm vs 75 mm — differs by 25 mm, tolerance 0.5 mm` in a monospaced readout on
paper stock, and they recognise their own instrument. **The register is not decoration; it
is the fastest available credibility signal to the one person in the room who can actually
validate us.**

**The government judge.** Wants to know: is this a record or a pitch? Instrument-grade
design reads as a record. The margin rail carrying `PROTOTYPE · SYNTHETIC EVALUATION
CORPUS` in the very first viewport is a design decision that says *these people disclose
before they are asked*. That is worth more to a MoP&NG panel than any amount of polish.

**Neither of them is a designer.** So the direction must never depend on a design-literate
reader noticing a clever thing. Every clever thing here is also a functional thing: the
hairline is the subject, the mono is the unit system, the margin is the citation apparatus.

### The feeling in one sentence

*Someone put an instrument on this problem and is showing me the reading, including the
readings that are inconvenient.*

---

## 3. HERO — FIRST VIEWPORT, IN EXTREME DETAIL

### 3.1 The composition problem, stated honestly

A hero with no object has to answer three questions in the first 800ms:
1. What is the biggest thing on screen? (scale)
2. Where does the eye rest? (optical centre)
3. What single word tells me the stakes? (verdict)

Our answers: **the numerals** are the biggest thing; **the gap between them** is the
optical centre; **MATCH / DISTINCT** are the stakes.

The critical move — and it is the strongest single idea in this direction — is that
**the optical centre is not either number. It is the 1px vertical rule between them,
carrying the label `Δ 0.003`.** The subject of the hero is the *difference*, and the
difference is drawn as a literal hairline. Everything downstream is that hairline getting
wider until it is the whole argument.

### 3.2 Static composition (1440 × 900 desktop)

```
┌──┬────────────────────────────────────────────────────────────────────────┬──┐
│  │                                                                        │  │
│S │            SEMANTIC SIMILARITY · ONE SOURCE RECORD · TWO CANDIDATES     │  │  ← eyebrow, mono 12/1.2,
│I │                            (GRAPHITE, centred)                         │  │    +0.14em, GRAPHITE
│H │                                                                        │  │
│2 │                                        │                               │  │
│6 │       0.960                            │            0.957              │  │  ← D0 GIANT, JetBrains
│0 │                                  Δ 0.003                               │  │    Mono 500, 220px,
│9 │                                        │                               │  │    lh 0.80, tabular
│9 │        MATCH                           │           DISTINCT            │  │  ← LABEL, mono 500, 15px,
│  │       (GAUGE)                          │            (OXIDE)            │  │    +0.16em, uppercase
│· │                                        │                               │  │
│C │                                                                        │  │
│P │        Three thousandths apart. Opposite answers.                      │  │  ← h1, Archivo 600, 64px,
│C │                                                                        │  │    lh 1.00, INK, LEFT-aligned
│L │        An embedding model scored two material descriptions almost      │  │    to content column edge
│  │        identically. One of them is the same bolt. One of them is a     │  │
│· │        different bolt. Deciding which is not a similarity problem —    │  │  ← LEAD, Archivo 400, 21px,
│  │        and a threshold cannot fix it.                                  │  │    lh 1.30, 58ch max
│P │                                                                        │  │
│R │        SCROLL TO SEE WHY   │                                           │  │  ← mono 11px + 24px
│O │                            ╵                                           │  │    animated hairline cue
└──┴────────────────────────────────────────────────────────────────────────┴──┘
   ↑ 96px instrument rail                                          right rail ↑
     (vertical mono, top: SIH26099 · CPCL · MoP&NG                   (empty in hero;
      bottom: PROTOTYPE · SYNTHETIC EVALUATION CORPUS)                carries footnote
                                                                      markers below)
```

**Deliberate hierarchy inversion.** The h1 is *smaller than* and *below* the numbers. The
numbers are the image; the h1 is the caption on the image. This is correct for a page
whose subject is a reading, and it is still one semantic `<h1>` in a real heading tree.

**Alignment logic.** The numeral pair and the Δ rule are centred on the content column's
optical axis. The h1, lead and scroll cue are left-aligned to the content column's left
edge. The asymmetry is intentional: centred = the instrument reading, left = the human
speaking. Two voices, two alignments, held for the whole page.

**Vertical rhythm.** Numeral baseline sits at 44% viewport height (slightly above true
centre — the classic optical-centre correction). Eyebrow 120px above the numeral cap
height. Verdicts 56px below numeral baseline. h1 top at 62% viewport height. Nothing
touches the bottom 8% except the scroll cue.

### 3.3 The actual copy — final words, not placeholders

| Slot | Copy |
|---|---|
| Eyebrow | `SEMANTIC SIMILARITY · ONE SOURCE RECORD · TWO CANDIDATES` |
| Left numeral | `0.960` |
| Left verdict | `MATCH` |
| Centre label | `Δ 0.003` |
| Right numeral | `0.957` |
| Right verdict | `DISTINCT` |
| h1 | `Three thousandths apart. Opposite answers.` |
| Lead | `An embedding model scored two material descriptions almost identically. One of them is the same bolt. One of them is a different bolt. Deciding which is not a similarity problem — and a threshold cannot fix it.` |
| Scroll cue | `SCROLL TO SEE WHY` |
| Rail, top | `SIH26099 · CPCL · MINISTRY OF PETROLEUM & NATURAL GAS` |
| Rail, bottom | `PROTOTYPE · SYNTHETIC EVALUATION CORPUS · FLIS-DERIVED REFERENCE DATA` |
| Skip control (rail, appears on focus or after 2s) | `SKIP TO RESULT` |

The lead's last clause — *"and a threshold cannot fix it"* — is load-bearing. Without it,
a fast reader concludes "0.960 > 0.957, so the threshold sits between them," which is
exactly the misconception the page exists to destroy. We pre-empt it in the first
viewport and spend the pin proving it.

### 3.4 Load choreography — what moves, in what order

**Frame 1 (0ms) the numerals are already there.** No count-up, no fade, no mask. They are
painted at final position and full opacity in the first paint. This is the single most
important timing decision in the direction: the 3-second read starts at 0ms, not at
whenever an entrance finishes. Fonts are self-hosted `woff2`, latin-subset, `<link
rel=preload>`, `font-display: block` with a ≤100ms block window — a fallback-figure reflow
of 220px tabular numerals would be the ugliest possible first impression, so we accept a
sub-100ms block instead.

| t (ms) | Element | Motion | Duration | Ease | Why it exists |
|---|---|---|---|---|---|
| 0 | `0.960`, `0.957` | none — painted final | — | — | Meaning available at first paint |
| 0–120 | — | **held silence** | 120 | — | A beat. Motion that starts instantly reads as a loading state; a held beat reads as composure. |
| 120 | Δ hairline | scales from centre outward, top and bottom simultaneously, `scaleY 0→1`, origin centre | 340 | power2.out | Directs the eye to the gap. The gap is the subject. |
| 300 | `Δ 0.003` | opacity 0→1 + 4px rise | 200 | power2.out | Names the gap once the eye is already on it |
| 420 | `MATCH` | line-mask reveal from below | 380 | power2.out | Verdicts arrive *after* the numbers — they are consequences, not properties |
| 510 | `DISTINCT` | line-mask reveal from below (stagger +90) | 380 | power2.out | The 90ms stagger makes the pair read as sequential judgements, not a symmetric graphic |
| 760 | h1 (2 lines) | line-mask, stagger 70 | 420 | power2.out | Caption the image |
| 1000 | eyebrow | opacity 0→1 | 260 | power2.out | Context, last, because it is the least urgent |
| 1000 | lead (3 lines) | line-mask, stagger 60 | 400 | power2.out | Runs concurrent with eyebrow — no reason to serialise low-priority text |
| 1400 | scroll cue hairline | extend/retract loop, 24px, 2.4s cycle | loop | sine.inOut | The only looping element on the page. Justified: the next scroll does something unusual (a 320vh pin) and the visitor needs to know the page continues. |
| **1660** | — | **entrance complete** | — | — | |

Total entrance 1.66s; **the thesis is legible at 0ms and confirmed at 890ms.**

Everything enters **from below only**, one easing family (`power2`), matching the
discipline from the teardown. Nothing enters from the side. Nothing scales except the
hairline, and the hairline scales only along its own axis.

### 3.5 What the eye actually does in 3 seconds

```
 0.0s   two large numerals — scale contrast (220px vs 12px) captures fixation
 0.3s   motion at the centre pulls the eye to the hairline → "Δ 0.003"
 0.5s   arithmetic happens involuntarily: 0.960 vs 0.957, these are the same
 0.8s   MATCH / DISTINCT arrive → colour dyad (GAUGE / OXIDE) → contradiction registers
 1.2s   eye drops to h1, which names the contradiction it just felt
 2.0s   lead sentence: "the same bolt / a different bolt" — the abstraction acquires a
        physical referent. This is the sentence that saves the direction.
 2.6s   "a threshold cannot fix it" — the promise
 3.0s   scroll cue
```

**Answer to "what carries the first viewport if not an object":** four things, in order of
strength — (1) **scale contrast**, 220px against 12px on a single ground; (2) **the drawn
gap**, the only moving thing at 300ms; (3) **two words anyone can read**, MATCH and
DISTINCT, which need no domain knowledge; (4) **one concrete noun in the lead**, *bolt*,
which converts the decimals into a physical object without putting a photograph on screen.

The abstraction lands because **the verdicts are not abstract.** Nobody needs to understand
cosine similarity to understand that two identical-looking numbers got opposite answers.

---

## 4. THE ONE SCRUBBED ANIMATION — "THE UNPACKING"

**This is the entire continuous-scroll budget for the page.** Everything else on the
landing page is a discrete reveal, a hover, a controlled toggle, or a loading state.

### 4.1 Spec

| Property | Value |
|---|---|
| Trigger | Hero section, `start: "top top"` |
| Pin | Hero viewport pinned |
| Pinned scroll distance | **320vh** (`end: "+=320vh"`) |
| Scrub | `1` (Lenis-smoothed) |
| Section total height | 420vh (100vh hero + 320vh pin travel) |
| Unpin | Pin releases at 100% progress; the composed final panel then scrolls away **fully formed, at full opacity** |
| Reduced motion | Pin disabled entirely; the eight acts render as eight stacked static figures (§4.4) |
| Viewport < 768px | Pin disabled; same stacked-figure fallback |

**Why 320vh and not 120vh.** The teardown's hero pin was 120vh for a single
transformation. Ours carries eight discrete comprehension steps and one scale change. At
120vh each act gets 15vh — roughly 150ms of natural scrolling — which is below the
threshold at which a viewer can read a four-row attribute table. 320vh gives each act
32–48vh. This is the most expensive decision on the page and it is defended in §8.3.

**Act budget:**

```
 0%          10%        25%        40%    50%        65%      75%        90%   100%
 ├───────────┼──────────┼──────────┼──────┼──────────┼────────┼──────────┼─────┤
 │  CLEAR    │ THE THREE│ EXTRACT  │COMPARE│  VETO    │ REASON │ CORPUS   │SETTLE│
 │   32vh    │  48vh    │   48vh   │ 32vh │   48vh   │  32vh  │   48vh   │ 32vh │
```

### 4.2 Frame by frame

---

#### **SCROLL 0%** — the hero, at rest

```
        0.960          │          0.957
                   Δ 0.003
        MATCH          │         DISTINCT

  Three thousandths apart. Opposite answers.
  An embedding model scored two material descriptions...
  SCROLL TO SEE WHY ╵
```

**On screen:** the full hero as loaded.
**Moving:** only the scroll-cue hairline loop.
**Changed since:** —
**Viewer understands:** two near-identical scores, opposite verdicts. Nothing about why.

---

#### **SCROLL 10%** — CLEAR THE STAGE

```
        0.960          │          0.957
                   Δ 0.003
        MATCH          │         DISTINCT
```

**On screen:** numerals, Δ rule, verdicts. Everything else gone.
**Moving:** h1 and lead exiting upward through their line masks (stagger 40ms, reverse
order — last line leaves first). Scroll cue fades. The numeral pair rises 6% of viewport
height to true optical centre and grows 220px → 248px.
**Changed since 0%:** all prose removed; the reading is now alone on the ground.
**Viewer understands:** *the numbers are the subject; the page is about to work on them.*
**Why this act exists:** you cannot stage a discovery in a crowded frame. Clearing is not
a transition, it is the page saying *watch this*.

---

#### **SCROLL 25%** — THE THREE RECORDS

```
   SOURCE ─────────────────────────────────────────────────────
   SS HEX BOLT M10 X 50
   ──────────────────────────────────────────────────────────────
   CANDIDATE A                    │          CANDIDATE B
   STAINLESS STEEL HEXAGONAL      │          SS HEX BOLT M10 X 75
   BOLT 10MM X 50MM               │
                                  │
        0.960                     │              0.957
        MATCH                     │             DISTINCT
```

**On screen:** a three-part frame — the source record on a full-width band at top, two
candidate columns below it split by the Δ rule (now full-height, floor to ceiling).
**Moving:** the numeral pair translates outward to the left and right column axes and
shrinks 248px → 96px (they are becoming *data in a table*, not a headline). The source
string masks down from the top band. The two candidate strings mask up beneath their
columns, stagger 120ms. `Δ 0.003` migrates to sit on the rule at the vertical midpoint of
the score row.
**Changed since 10%:** the numbers acquired referents. There is now a *source*.
**Viewer understands:** *these scores measure two candidates against one record. The
left one is verbose and different-looking; the right one looks almost identical to the
source.* — and this is the trap the page wants them in. The **right** candidate looks more
like the source, and the right candidate is the rejection.
**Why this act exists:** it converts the hero's abstraction into a comparison the viewer
can perform themselves, and it plants the counterintuition (surface similarity is
misleading) before naming it.

---

#### **SCROLL 40%** — EXTRACTION

```
   SOURCE   SS HEX BOLT M10 X 50
   ┌ TYPE      BOLT, MACHINE ┐
   │ MATERIAL  STAINLESS STEEL│
   │ THREAD    M10            │
   └ LENGTH    50 mm          ┘
   ────────────────────────────────────────────────────────────
   CANDIDATE A                     │   CANDIDATE B
   STAINLESS STEEL HEXAGONAL...    │   SS HEX BOLT M10 X 75
   TYPE      BOLT, MACHINE         │   TYPE      BOLT, MACHINE
   MATERIAL  STAINLESS STEEL       │   MATERIAL  STAINLESS STEEL
   THREAD    M10                   │   THREAD    M10
   LENGTH    50 mm                 │   LENGTH    75 mm
        0.960                      │        0.957
```

**On screen:** three columns, each string now with a four-row attribute readout beneath
it. Attribute keys in mono GRAPHITE `+0.12em`; values in mono INK.
**Moving:** rows extrude downward out of each string — the string acts as a lintel and the
rows drop from under it. Source column first (rows stagger 90ms), then A, then B (column
stagger 220ms). Each row: `clip-path`-free — a mask element translating down, opacity
tied to the same tween. `LENGTH 75 mm` on candidate B renders in **INK, not OXIDE**. It is
not highlighted. It is simply true, and on screen, and available to anyone who looks.
**Changed since 25%:** free text has become structure.
**Viewer understands:** *the system doesn't compare sentences, it compares four named
attributes.* And — if they are paying attention — *hold on, 75.*
**Why this act exists:** this is the mechanism reveal. Without it the veto looks like
magic. With it, the veto looks like arithmetic. It also plants the discovery: the answer is
on screen a full 25% of the pin before the page names it. **The page rewards the person who
looked.**

---

#### **SCROLL 50%** — COMPARISON, AND THE STALL

```
   SOURCE                          │
   TYPE      BOLT, MACHINE ════════╪════════ BOLT, MACHINE       AGREE
   MATERIAL  STAINLESS STEEL ══════╪════════ STAINLESS STEEL     AGREE
   THREAD    M10 ══════════════════╪════════ M10                 AGREE
   LENGTH    50 mm ════════─ ─ ─ ─ ╪                             ▓▓▓▓
                                   │
   (candidate A column: all four connectors complete, all AGREE)
```

**On screen:** horizontal connector rules drawn from the source column's attribute rows
across to each candidate column's matching row. `AGREE` chips in GAUGE at each terminus.
**Moving:** connectors draw left-to-right — no, **outward from the source column in both
directions simultaneously**, top row to bottom row, 110ms stagger. Candidate A: all four
complete, four GAUGE `AGREE` chips land. Candidate B: TYPE, MATERIAL, THREAD complete and
land AGREE. **The LENGTH connector to candidate B draws to 55% of its span and stops.**
**Changed since 40%:** relationships are now visible, and one of them is unfinished.
**Viewer understands:** *three out of four agree on both sides. Something is wrong with
the fourth on the right, and nothing has told me what.*
**Why this act exists:** the stall. This is the discovery mechanism. **The viewer perceives
an anomaly before the page names it.** They scroll and every other line completed; this one
did not. The unfinished stroke is a question mark drawn in the negative.

---

#### **SCROLL 65%** — THE VETO

```
   ╔══════════════════════════════════════════════════════════════╗
   ║  LENGTH   50 mm ══════════╪══════════  75 mm      ▐ VETO ▌   ║  ← OXIDE rule
   ╚══════════════════════════════════════════════════════════════╝
   CANDIDATE A                     │   CANDIDATE B  (GRAPHITE, desaturated)
   ...                             │   ... (all rows now GRAPHITE)
                                   │
        0.960                      │        0.957   ← UNCHANGED. INK. Full contrast.
        MATCH                      │        0.000   ← new row, OXIDE
                                   │        DISTINCT
```

**On screen:** the same diagram, with candidate B's entire column reduced to GRAPHITE
except its score `0.957`, which remains at full INK contrast. A 1px OXIDE rule runs across
the LENGTH row. A 1px OXIDE rule runs down the full height of candidate B's column. A
stamped block `VETO — CRITICAL ATTRIBUTE — LENGTH` sits at the intersection.
**Moving:** the stalled LENGTH connector completes its remaining 45% of span — but in
OXIDE, not GAUGE, over 220ms `power2.out`. Then the horizontal OXIDE rule extends across
the row (260ms), then the vertical OXIDE rule drops down the column (180ms). Then the
stamp block appears: opacity + 2px settle, 160ms, no scale, no rotation. Concurrently
candidate B's rows desaturate to GRAPHITE over 300ms. The `0.000` row masks up beneath
`0.957`.
**Changed since 50%:** the anomaly is named, and the verdict is applied.
**Viewer understands:** *the score didn't change. The score is still 0.957. Something
outside the score overruled it.* — which is the exact mental model of a gate.
**Why this act exists:** this is the thesis. It is the only moment on the entire page where
a stroke draws left-to-right, and the only moment OXIDE appears at scale. Reserving both
means this moment cannot be confused with anything else on the page.

---

#### **SCROLL 75%** — THE REASON

```
   ▐ VETO ▌ CRITICAL ATTRIBUTE — LENGTH
     50 mm vs 75 mm  ·  differs by 25 mm  ·  tolerance 0.5 mm

     score = veto × (0.85 · attribute agreement  +  0.15 · text)
     score =   0   × (0.85 ·        0.75         +  0.15 · 0.957)  =  0.000
```

**On screen:** beneath the stamp, the reason line in mono GRAPHITE; beneath that, the
scoring identity written out with the veto factor as a literal `0`.
**Moving:** reason line masks up (single line, 300ms). Then, 400ms of scroll later, the
formula masks up in two lines, stagger 90ms. The `0` in the second line lands last, alone,
in OXIDE.
**Changed since 65%:** the verdict acquired a defensible, unit-bearing justification, and
the arithmetic is shown rather than asserted.
**Viewer understands:** *it can explain itself in my units, and the zero is not a low score
— it is a multiplication by zero.*
**Why this act exists:** authority requires a reason in the reader's vocabulary. `differs
by 25 mm, tolerance 0.5 mm` is the sentence that a CPCL materials officer recognises as
their own. And showing `0 × (…) = 0.000` kills the misreading that the veto is a heavy
negative weight.

---

#### **SCROLL 90%** — THE CORPUS *(the scale jump)*

```
   1.00 ┤ ● ●●● ●●●●●●●● ●●●●●●●●●●●●●● ●●●●●●●●●● ●●●● ●●
        │ ●●●●●●● ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
        │ ●●● ●●●●●●●●●●●● ●●●●●●●●●●●●●●● ●●●●●●●●● ●●●●●●
        │ ●●●●●●●●●●●●●●●●●●●●●●●●● ●●●●●● ●●●●●●●●●●●●●●●●
   0.85 ┼─────────────────────────────────────────────────── ← threshold line
        │  ●        ●          ●    ●        ●   ●
   0.70 ┤
        └───────────────────────────────────────────────────
          2,408 pairs our veto rejected, plotted by the semantic
          score that would have accepted them.
          2,399 of 2,408 scored ≥ 0.85.
```

**On screen:** the two-column diagram has collapsed to a single dot pair at the far left of
a scatter field. 2,408 OXIDE dots fill the plot. A GRAPHITE horizontal rule at 0.85. Axis
label `SEMANTIC SIMILARITY` on the vertical.
**Moving:** the whole composed diagram scales down (~0.06×) and translates to the plot's
left edge, becoming one dot pair, over 40% of this act. Then the remaining 2,406 dots
render progressively, drawn by scroll progress on a single `<canvas>` from a precomputed
position array — **not** individually animated DOM nodes. The 0.85 rule draws last.
**Changed since 75%:** the anecdote became a distribution.
**Viewer understands:** *this was not one clever example. Two thousand four hundred times
in this corpus, the similarity score said "same" and the attributes said "different."*
**Why this act exists:** **this is what makes 320vh a correct spend.** Scale change over
continuous scroll is precisely the thing scrubbing does better than any discrete reveal.
Without this act, the pin resolves to "one bolt was 75mm not 50mm," which is a 20vh idea
wearing a 320vh coat. With it, the pin resolves to "the failure mode is systemic," which
justifies the whole page.

> **HONESTY GUARDRAIL — build requirement R1.** The scatter must be generated from the
> actual array of 2,408 similarity values exported from the evaluation harness. **If that
> array cannot be exported, the scatter is cut and replaced by a two-segment stacked bar
> showing 2,399 / 9 with the same motion grammar (scale-down, then fill).** A plausible-
> looking cloud of invented dot positions is a fabricated distribution and is forbidden,
> however good it looks.
>
> **HONESTY GUARDRAIL — no phantom second distribution.** It is very tempting to also plot
> the true-match similarities in the same space to show overlap. We have not measured that
> distribution. Plot only what we measured. The caption states exactly what the dots are.

---

#### **SCROLL 100%** — SETTLE

```
   ┌────────────────────────────────────────────────────────────┐
   │ FIG. 01                                                    │
   │ 1.00 ┤ ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●   │
   │      │ ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●   │
   │ 0.85 ┼───────────────────────────────────────────────────  │
   │      │  ●    ●     ●   ●    ●  ●                           │
   │      └───────────────────────────────────────────────────  │
   │ Critical-attribute vetoes, plotted by semantic similarity. │
   │ 2,399 of 2,408 scored ≥ 0.85 — high enough that a          │
   │ similarity threshold would have accepted them.             │
   │ Synthetic evaluation corpus · 1,800 records · 300 probes ¹ │
   └────────────────────────────────────────────────────────────┘
```

**On screen:** the finished figure, framed, captioned, numbered `FIG. 01`, with a
superscript provenance marker resolving in the right rail.
**Moving:** axis labels and caption mask up (stagger 80ms). Nothing else. The last 32vh is
deliberately quiet — motion ends before the pin does, so the viewer reaches the release
point with a settled image, not a moving one.
**Changed since 90%:** the animation became a document.
**Viewer understands:** *this is a finding, and it is sourced.*
**Unpin:** ScrollTrigger releases at 100%. **The figure does not fade, shrink or dismantle
on exit.** It scrolls away at full opacity as an ordinary block. Pins that undo themselves
on exit make the viewer feel the work was taken back.

**Immediately after the pin**, in normal flow, one static line at 96px Archivo:

> `A threshold could not have separated these. Attributes could.`

That sentence is the insurance policy for every visitor who scrolled the pin too fast to
read it (§8.3).

### 4.3 The discovery-versus-explanation mechanism, stated as a rule

Three techniques, applied in this exact order at 40% / 50% / 65%:

1. **Plant before reveal.** `LENGTH 75 mm` is on screen, unhighlighted, in ordinary INK,
   from 40% — a full 25% of the pin before the veto. Anyone who looks finds it themselves.
2. **Anomaly before name.** At 50% the stall is the only unfinished element in a field of
   completed ones. The viewer *perceives* the problem while the page is still silent.
3. **Motion first, word second, never simultaneous.** At every checkpoint the visual
   change leads the label by ≥400ms of scroll-equivalent. The page never says a thing at
   the same instant it shows the thing. Simultaneity reads as explanation; delay reads as
   confirmation of something you already suspected — which is the physiology of discovery.

**Corollary rule for the whole site:** never animate an element and its caption together.

### 4.4 The reduced-motion / small-viewport path

Not a degradation — a second, honest layout of the same argument.

The pin is not registered. The eight acts become **eight stacked figures in document
flow**, each 1 viewport tall or less, each with a real `<h3>`, a static composed diagram
(the act's end state), and a one-sentence caption which is the "viewer understands" line
from §4.2 rewritten as prose. Figures numbered `FIG. 01/08` … `FIG. 08/08`.

Opacity-only fades (≤120ms) are permitted; `prefers-reduced-motion: reduce` reduces
vestibular triggers, it does not require absolute stillness. No transforms, no draws, no
scrubbing, no parallax.

**Cost, stated plainly:** this is roughly a second layout of the page's most complex
section. See §8.4.

---

## 5. VISUAL SYSTEM

### 5.1 Palette — seven values

| Token | Hex | Role |
|---|---|---|
| `PAPER` | `#F4F2ED` | Primary ground. Warm off-white — the stock of an inspection certificate or mill test report. Not `#FFFFFF`: pure white reads as an unstyled document. |
| `INK` | `#0A0C0E` | Primary type on PAPER. Slightly blue-black, never brown-black. |
| `VOID` | `#000000` | The inversion ground. Used at the platform transition and nowhere else on the landing page. **Pure black against an off-white paper — the asymmetry is what makes inversion feel absolute.** |
| `CHALK` | `#E5E1D8` | Hairlines, section rules, table zebra, card fills on PAPER. **The Δ rule is CHALK.** |
| `GRAPHITE` | `#565C63` | Mono labels, axis lines, captions, UNKNOWN state, desaturated/vetoed content. ~5.4:1 on PAPER — verify at build; used at ≥12px only. |
| `GAUGE` | `#1B4D7A` | The instrument accent. AGREE connectors, MATCH verdicts, active data, links, focus ring. A deep steel-blue that sits one respectful nod from the national blue without cosplaying the flag. |
| `OXIDE` | `#C0442A` | **The veto, and only the veto.** Industrial oxide-red / marking paint, not `#FF0000` browser-error red. |

**Scarcity discipline.** OXIDE appears on the entire landing page in exactly four places:
the hero `DISTINCT` verdict; the veto act inside the pin; the corpus dots; the veto rows
in the operational results table. Nowhere else. Not on buttons, not on links, not on hover.
**Its authority is entirely a function of how rarely it appears.**

**Not the teardown's palette.** That site's black-and-white essay ground belongs to a
polemic about fast fashion. Ours is document stock with two instrument inks. Different
subject, different physics.

### 5.2 Type

Two families, both self-hosted `woff2`, latin subset, preloaded, zero network calls.

- **Grotesque: Archivo** — 400 / 500 / 600, plus italic for captions. Industrial
  proportions, tight apertures, doesn't read as a startup default.
- **Mono: JetBrains Mono** — 400 / 500 / 700. True tabular figures, slashed zero,
  unambiguous `1/l/I`. **Every number, unit, code, label and verdict on the site is set in
  it.** Mono is not a "code" signal here — it is the unit system.

| Role | Family / weight | Size | Line-height | Tracking | Use |
|---|---|---|---|---|---|
| D0 GIANT | Mono 500, tabular | 96–248px (clamp) | **0.80** | −0.04em | The hero numerals. Nothing else on the site is ever this size. |
| D1 DISPLAY | Archivo 600 | 56–96px | **1.00** | −0.02em | Section openers (`h2`), the post-pin insurance line |
| H3 | Archivo 600 | 28–36px | **1.10** | −0.01em | Sub-sections, figure headings |
| LEAD | Archivo 400 | 20–24px | **1.30** | 0 | Section lead paragraphs, hero lead. Max 58ch. |
| BODY | Archivo 400 | 17–18px | **1.45** | 0 | Prose. Max 62ch. |
| DATUM | Mono 500 | 13–15px | 1.20 | +0.12em | Values, verdicts, scores in tables |
| LABEL | Mono 500 uppercase | 11–12px | 1.20 | +0.16em | Attribute keys, eyebrows, rail, axis labels |
| CAPTION | Archivo 400 italic | 14px | 1.50 | 0 | Figure captions, provenance, disclosure notes — GRAPHITE |

**Line-height curve:** `1.45 → 1.30 → 1.10 → 1.00 → 0.80`. It tightens monotonically as
size grows. This single curve is most of why the big type will read as designed rather than
as large.

`SplitText` policy, from the teardown: `{type: "lines", mask: "lines"}` for all prose.
**Characters only for the two hero numerals and the two verdict words** — short labels
only, never sentences. Screen-reader text is preserved via `aria-label` on the split
container; the split spans are `aria-hidden`.

### 5.3 Layout skeleton — the instrument frame

```
│←96px→│←──────────── 1000px content column ────────────→│←96px→│
│      │                                                 │      │
│ LEFT │  Everything the visitor reads                   │RIGHT │
│ RAIL │                                                 │ RAIL │
│      │  centred axis: instrument readings, figures     │      │
│      │  left edge:   human voice, prose, headings      │      │
│      │                                                 │      │
│ §nn  │                                                 │  ¹²³ │
│ mono │                                                 │ prov │
│ vert │                                                 │ notes│
```

- Container `1192px` max, content column `1000px`, two `96px` rails.
- **Left rail** carries the persistent instrument bezel: rotated mono, section index
  (`§03 / WHY SIMPLE MATCHING FAILS`), a scroll-position readout, and the `SKIP TO RESULT`
  control during the pin. It is sticky and always present.
- **Right rail** carries superscript provenance markers. Every measured claim on the page
  gets one, resolving in the margin: `¹ Synthetic corpus, 1,800 records from 600 canonical
  specs. Internal harness, reproducible.` `² FLIS / PUB LOG public catalogue. Not CPSE
  data.` **The citation apparatus is part of the layout, not a footer.**
- Section padding `120px` vertical. Sections separated by a **1px CHALK rule** — the same
  object as the hero's Δ rule.
- Centred flex columns. **No 12-column grid.** The page has one column and two margins,
  like a document.
- `< 900px`: rails collapse — left rail becomes a 40px sticky top bar with the section
  index, provenance markers become inline expandable footnotes at the end of each section.

### 5.4 What makes this OURS

1. **Numerals are the display face.** Mono tabular figures at 248px as the primary
   typographic voice. Prose is subordinate to readings.
2. **The hairline is the subject and the connective tissue.** The Δ rule in the hero, the
   1px section rules, the connectors in the pin, the 0.85 threshold line, the veto stroke —
   one object at different jobs. The page is built from a single mark.
3. **Certificate stock, not essay black.** Warm PAPER with pure-black reserved as an event.
4. **Marking-paint OXIDE reserved for exactly one meaning**, four appearances.
5. **The margin citation apparatus.** Disclosure is architectural. `PROTOTYPE · SYNTHETIC
   EVALUATION CORPUS` is visible in the first viewport, in the rail, before any claim.
6. **Two alignments, two voices.** Centred = the instrument. Left = the people.

---

## 6. THE VETO MOMENT, IN THIS DIRECTION'S LANGUAGE

The veto appears twice: as **cinema** inside the pin (§4.2, 50–75%) and as **operation** in
its own later section. They must not use the same choreography or the second feels like a
rerun. The rules below govern both.

### 6.1 The seven rules of an authoritative rejection

1. **Nothing shakes.** No jitter, no bounce, no oscillation, no elastic ease, no flash.
   Error UI shakes because it is apologising for the user. An instrument does not
   apologise. Every veto tween uses `power2.out` and travels in one direction.
2. **Nothing disappears.** The rejected candidate remains fully on screen and fully
   readable. **Rejection is not deletion.** A materials officer needs to see what was
   rejected in order to trust that it was rejected correctly.
3. **The semantic score does not change.** `0.957` stays `0.957`, at full INK contrast,
   while everything around it desaturates. This is the visual proof of *gate, not weight* —
   the model's opinion is preserved and overruled, not revised.
4. **Colour subtracts before it adds.** The candidate column desaturates to GRAPHITE
   *first* (300ms), and only then does the single OXIDE stroke arrive. The dominant
   sensation is withdrawal of endorsement, not the arrival of an alarm.
5. **The verdict is drawn, not flashed.** Two strokes: a horizontal OXIDE 1px rule across
   the offending attribute row (260ms), then a vertical OXIDE 1px rule down the full
   candidate column (180ms). Two strokes read as a stamp being applied by a hand. A fill
   or a flash reads as a system error.
6. **The reason speaks the operator's units.** `50 mm vs 75 mm · differs by 25 mm ·
   tolerance 0.5 mm`. Never `attribute mismatch`. Never `confidence low`. Always the
   nominal values, the deviation, and the tolerance that was exceeded.
7. **Silence.** No sound. The demo room is quiet and Wi-Fi is off; audio would be a
   liability and adds nothing.

### 6.2 What changes visually at the instant of veto

| Element | Before | At veto | Duration |
|---|---|---|---|
| Candidate column type | INK | GRAPHITE | 300ms |
| AGREE chips on that column | GAUGE | GRAPHITE | 300ms, same tween |
| The stalled connector | GAUGE, 55% drawn | OXIDE, 100% drawn | 220ms |
| Attribute row | no rule | 1px OXIDE horizontal rule | 260ms |
| Column | no border | 1px OXIDE left border, full height | 180ms |
| Stamp block | absent | `▐ VETO ▌ CRITICAL ATTRIBUTE — LENGTH`, OXIDE on PAPER, 1px OXIDE box | 160ms, opacity + 2px settle |
| Score readout | `0.957` | `0.957` **unchanged**, plus new row `0.000` in OXIDE | 240ms |
| Verdict | `DISTINCT` | `DISTINCT` unchanged | — |
| Ground | PAPER | PAPER **unchanged** | — |

**The ground does not change.** A page-wide colour shift at veto would make rejection feel
like a system state. It is not a system state — it is a finding about one pair.

### 6.3 Never by colour alone

Every veto carries, independently of colour: the literal word `VETO`, the attribute name,
the two values, the deviation, the tolerance, a `1px` border (a shape change), and the
`0.000` decision score. Remove all colour from the page and the rejection is still
unambiguous. This satisfies both WCAG 1.4.1 and the ~8% of male judges with deuteranopia,
for whom OXIDE against GRAPHITE is a weak signal.

### 6.4 The operational veto (later section, not the pin)

No cinema. A static results table: source record at top, all three candidates as rows
(`0.960 MATCH`, `0.957 DISTINCT`, `0.895 DISTINCT`), each rejection row carrying its own
reason line. One control: `SHOW THE ARITHMETIC`, a discrete toggle that expands the scoring
identity per row. This is where the third candidate — `NUT HEX SS M10`, vetoed on
`Item type: BOLT, MACHINE vs NUT, PLAIN, HEXAGON` — finally appears, proving the veto is a
general gate over critical attributes and not a length special case.

---

## 7. WHY EACH ANIMATION EXISTS

### 7.1 Kept

| # | Animation | Type | What it communicates | Lost if cut |
|---|---|---|---|---|
| 1 | Hero entrance (§3.4) | one-time load | Verdicts are *consequences* of the numbers; the gap is the subject | The hero becomes a static poster; the Δ hairline never earns the eye and the optical centre collapses to whitespace |
| 2 | **The Unpacking** (§4) | **the one scrubbed pin** | The whole argument: text → attributes → comparison → gate → reason → systemic scale | The page has a thesis and no proof of it. This is the deliverable. |
| 3 | Three descriptions → one canonical record (PROBLEM) | discrete, `play none none reverse` | Three identities, one material — the problem statement in one gesture | The problem section becomes a paragraph nobody reads |
| 4 | FLIS scale counter, `1,824,354` | discrete count-up, **one on the whole page**, 900ms | Magnitude via duration — a number that takes 900ms to arrive *feels* large in a way a static glyph does not | The only place magnitude is the point loses its only tool. **One count-up is a decision; seven is a habit.** |
| 5 | Threshold explorer (WHY SIMPLE MATCHING FAILS) | user-dragged, not autoplay | Drag a threshold across the real harness output: false positives and false negatives trade off, never both zero | The page *asserts* that thresholds fail instead of letting the judge fail at it personally. Strongest interactive moment on the site. |
| 6 | Embeddings ON / OFF (PROOF) | user-toggled crossfade, 320ms | `2,399 → 133` vetoed pairs above 0.85. **The better the semantic model, the more necessary the veto.** Reuses the pin's exact dot-field vocabulary, so it costs nothing to teach | Our strongest conceptual claim becomes a table row |
| 7 | Operational veto table row expand (§6.4) | discrete height + opacity, 200ms | The arithmetic, on demand, per row | Judges who want to audit have to be told instead of shown |
| 8 | **HONESTY section: no animation at all** | *deliberate stillness* | The one place the page stops performing is the place it admits its limits. Absence is the design decision. | Disclosure animated like every other section reads as another sales beat. **This is the most credible moment on the page and it is credible because it is still.** |
| 9 | PAPER → VOID inversion (platform transition) | discrete, 480ms `power2.inOut`, background + ink swap | Mode change: argument → instrument. Pure black against off-white makes the switch feel absolute | The platform feels like more landing page instead of a different tool |
| 10 | Platform skeletons + latency readout | loading state, real `p50 13ms / p95 17ms` | The system is fast, and it says how fast | The speed claim is unwitnessed |
| 11 | Focus rings, hover underlines, row highlights | state, ≤120ms | Interactivity and keyboard position | Accessibility failure |
| 12 | Scroll cue hairline loop | loop, 2.4s, **only loop on the page** | The page continues, and the next scroll behaves unusually | With a 320vh pin ahead, some visitors will not scroll at all |

### 7.2 Cut, with reasons

| Cut | Why |
|---|---|
| **Odometer / count-up on the hero numerals** | Implies the scores are being computed live (they are not — this is a recorded engine output) and delays the 3-second read by ~1.2s. The numbers must exist at first paint. This is the most tempting cut on the list and it is the most necessary. |
| **Background particle / dot field in the hero** | Communicates nothing, costs GPU, and destroys the certificate register instantly. |
| **Text scramble / decode effect on labels** | The obvious "AI" move. It signals *hacker*, which is the wrong register for a ministry panel, and it emits garbage to screen readers. |
| **Marquee / ticker of material descriptions** | Vaguely communicates "lots of stuff"; precisely communicates nothing. Continuous horizontal auto-motion is also a reduced-motion and cognitive-load problem. |
| **Magnetic buttons, cursor followers, hover tilt** | Zero relationship to material identity. Portfolio reflexes. |
| **Preloader with a percentage** | "Never make a judge wait." A preloader manufactures a wait in order to decorate it. |
| **Page-wide background crossfade between every section** | Colour change must mean something. If it happens six times it means nothing, and the one place it *does* mean something (the platform inversion) is devalued. |
| **Parallax on figures** | Depth we do not have, implying dimensionality the subject does not possess. Also the most common source of scrub jank. |
| **Animating the Δ hairline anywhere after the hero** | It is established once. Re-animating the page's core mark cheapens it. |
| **Number transitions on the platform (score morphing between queries)** | On a real tool, a value that animates between states is a value you cannot read mid-flight. Platform numbers snap. |

---

## 8. HONEST WEAKNESSES

I am arguing against this direction, not defending it.

### 8.1 The hero is an abstraction and the audience is not

A refinery materials officer wants to see a bolt. We show them two decimals. Every other
direction can put a physical object in the first viewport; this one deliberately cannot,
because the moment you add a bolt photograph the numbers stop being the subject.

**Residual risk after mitigation:** the lead sentence — *"One of them is the same bolt. One
of them is a different bolt."* — converts the abstraction at ~2.0s. That is 2 seconds of
exposure with no physical referent. If a judge glances at the screen from across a room and
looks away, they took away nothing. **A photograph-led direction survives the glance; this
one does not.** That is a real, unfixable cost of the choice.

### 8.2 The highest copy dependency of the three directions

There is no image to fall back on. If the h1 is mediocre, the page is mediocre — there is
literally nothing else in the first viewport doing work. `Three thousandths apart.
Opposite answers.` has to carry a national-level submission on eleven syllables. Every
other direction can survive weak copy behind a strong asset. This one cannot.

**It also hard-couples the brand to two literals.** If the model or the corpus is
regenerated before the demo and the scores shift to `0.961 / 0.953`, the h1 becomes false
and the direction's name becomes false. **Build requirement R2: freeze the demo artefact
and the hero copy together, with a build-time assertion that fails the build if the
exported scores differ from the hero literals.** No other direction needs a CI check to
protect its headline. That is a genuine structural fragility.

### 8.3 320vh of scrub in a room full of fast scrollers

Demo rooms are rushed. A judge who flicks the trackpad blows through 320vh in ~1.2
seconds and sees a blur, then arrives at a scatter plot with no idea how they got there.
Scrub punishes speed.

Mitigations, and their limits:
- `SKIP TO RESULT` in the left rail, present from 2s and on first keyboard focus, jumps to
  the pin's end state. **Limit:** most people will not use it.
- The pin's final panel is a self-explanatory captioned figure, so arriving there
  disoriented still yields the finding. **Limit:** yields the *finding*, not the *reasoning*.
- The static line immediately after the pin — *"A threshold could not have separated these.
  Attributes could."* — restates the conclusion for anyone who saw nothing. **This is the
  real insurance and it should be treated as mandatory, not optional.**
- I considered ScrollTrigger `snap` to act boundaries. **Rejected:** snapping fights fast
  scrollers by seizing their input, which feels broken and hostile on a laptop trackpad.
  Better to lose the argument to speed than to take control of the scroll away from a judge.

### 8.4 The reduced-motion path is genuinely expensive here

In a direction where animation is decorative, `prefers-reduced-motion` means "render final
states" and costs almost nothing. **Here the scrubbed animation carries the argument**, so
"render the final state" would produce a single frame with eight acts overlapping — an
unreadable smear. The honest answer (§4.4) is eight static, captioned, individually-headed
figures in document flow.

**That is a second layout of the most complex section on the site**, with its own captions,
its own eight composed diagrams, and its own heading tree. Realistically it is 25–35% of
the total build time for the landing page. **Any direction whose motion is decorative gets
its reduced-motion branch nearly free. This one pays full price.** If the build schedule
compresses, this is the thing that will be tempting to skip, and skipping it is an
accessibility failure we have already declared non-negotiable. Budget it first, not last.

### 8.5 Mobile is a different page, not a smaller one

Two 248px numerals side by side do not fit 375px. Stacking them vertically with the Δ
hairline rotated 90° between them actually works — arguably reads better — but the pin's
25–65% acts are a **two-column horizontal comparison** with no horizontal room to exist on
a phone. There is no responsive rearrangement that preserves the choreography.

The honest decision: **below 768px the pin is disabled and mobile receives the
reduced-motion stacked-figure layout by default.** Defensible because judging happens on a
laptop, but it means a judge who checks the site on a phone that evening sees a materially
different, less persuasive page — and we will not be in the room to explain why.

### 8.6 Two colour and contrast liabilities

- OXIDE `#C0442A` on PAPER at 11–13px mono needs contrast verification; it may need
  darkening to ~`#A83A22` for LABEL sizes, which weakens it as marking paint. Verify early.
- Desaturation-to-GRAPHITE as a rejection signal is weak for deuteranopic viewers. §6.3
  covers this with redundant text and shape cues, but the *cinematic* veto at 65% relies on
  a desaturation sweep for its emotional beat, and that beat is diminished for those
  viewers. There is no full fix; the redundant signals ensure nothing is *lost*, only that
  the drama is quieter.

### 8.7 It can be mistaken for a data-visualisation portfolio piece

Instrument-grade design done well looks like an award-winning chart essay. A ministry panel
comparing us against a team with a screenshot of a working dashboard may read our elegance
as *this is a website, where is the product?* Mitigations: the platform transition must
arrive early enough in the scroll to be reached, the operational veto table (§6.4) must
look like an enterprise tool and not like cinema, and the rail must carry the ministry
attribution from the first viewport. **Residual risk: real.** This direction bets that
craft reads as competence. That bet is usually right and is not always right.

### 8.8 The poetry may outrun the mandate

"Three thousandths" is a better story than "One Nation – One Material Code," and the story
is not the mandate. If the page becomes about a beautiful epistemological point about
embeddings, a judge can walk away impressed and unsure what we built for CPCL. **The
official tagline must appear as the D1 opener of the very first section after the pin**,
and the transition to the platform must not be deferred past ~60% of total page scroll.

### 8.9 The one-sentence case against

*It asks a room full of non-designers to care about two decimals for two seconds before it
gives them anything they can hold.*

### 8.10 The one-sentence case for

*It is the only direction where the first thing on screen is the actual thing we
discovered, and every visitor who scrolls once will understand something about AI systems
that most of the people building them do not.*

---

## 9. BUILD REQUIREMENTS THIS DIRECTION CREATES

| ID | Requirement | Consequence if unmet |
|---|---|---|
| R1 | Export the array of 2,408 vetoed-pair similarity values from the evaluation harness as a bundled JSON artefact | The 90% corpus act degrades to an honest two-segment stacked bar (2,399 / 9). **Fabricated dot positions are forbidden.** |
| R2 | Freeze the demo artefact and hero copy together; build-time assertion that `0.960` / `0.957` / `Δ 0.003` match the exported scores | Hero headline can silently become false |
| R3 | Export the 300-probe harness output for the threshold explorer | The threshold explorer is **cut, not faked** |
| R4 | Self-host Archivo + JetBrains Mono as latin-subset woff2, preloaded, `font-display: block` ≤100ms | Tabular-numeral reflow on first paint — worst possible first impression, and a network call with Wi-Fi off |
| R5 | Corpus scatter drawn on one `<canvas>` from a precomputed position array, redrawn per scrub tick; DPR-capped at 2 and sized to the actual element, never a fixed 1440px backing store | 2,408 DOM nodes will destroy scrub performance; a fixed-size canvas is the teardown's exact mobile failure |
| R6 | Eight-figure static fallback authored as first-class content, not generated | Reduced-motion and mobile visitors get an unreadable overlap |
| R7 | Every measured claim carries a margin provenance marker; `PROTOTYPE · SYNTHETIC EVALUATION CORPUS · FLIS-DERIVED REFERENCE DATA` visible in the first viewport | Honesty constraints violated by omission |
| R8 | Zero non-localhost requests; verify with the network panel offline before the demo | Blank fonts, missing figure, dead demo |
