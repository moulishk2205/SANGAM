# SIH26099 — Landing page plan, then platform

Decision document. **No code.** Build order and per-scroll behaviour for the landing
page, followed by the platform. Read top to bottom; it is written in the order it gets
built.

---

# 0 · The decision

**Direction: CONVERGENCE.** Identity law: **THE THREAD IS NEVER CUT.**

Every source record on this site is joined to its canonical record by a literal 1px line.
The line is drawn during the thesis animation and persists into the platform as the
provenance rail. **There is exactly one broken thread in the entire experience — the
veto.** The page spends nine screens establishing that lines do not break, so the single
break reads as a verdict rather than an error.

Chosen over the two runners-up because its central image *is* the problem statement's
own clause — "One Nation – One Material Code, while maintaining traceability to individual
CPSE codes" — and because it answers the fear that actually kills standardisation projects
in PSUs: *are you going to overwrite my codes?* The page's answer is visible and counted.

### Grafted in

| From | What | Why it survives |
|---|---|---|
| GAUGE BLOCK | **Anti-gimmick doctrine** — a written forbidden list | Prevents the drift into generic AI-startup visuals |
| GAUGE BLOCK | **Unit- and tolerance-bearing type**: `50.0 mm ± 0.5`, never "highly accurate" | Speaks the CPCL officer's native language |
| THREE THOUSANDTHS | **Provenance superscripts** resolving in a margin rail | Reads to a ministry judge as an audit trail |
| THREE THOUSANDTHS | **`SYNTHETIC` chip in the first viewport**, not a footnote | Disclosure before being asked |
| CONVERGENCE | **PROSE EASES · DATA SNAPS** | The single best motion law in the three proposals |

### Rejected

- THREE THOUSANDTHS' abstraction-first hero. Opening on two bare numbers is the highest
  ceiling and the highest risk; a non-designer judge given 3 seconds needs an artefact,
  not a riddle. The 0.960/0.957 pair is kept — it moves to §S3 where it is set up.
- GAUGE BLOCK's full metrology-lab visual world. It competes with the thread for the
  role of central image, and two central images means none.

---

# 1 · The system

## Palette

Chosen for a national engineering register — not the fast-fashion palette from the
teardown, and deliberately not "AI blue" or startup violet.

```
--paper     #F4F2ED   warm off-white ground. Paper stock, not screen white.
--bone      #E8E4DB   secondary surface, card fills on paper
--ink       #14161A   primary text on paper (off-black, never pure)
--void      #000000   inversion ground — pure, so inversion feels absolute
--graphite  #6B7076   mono labels, captions, chrome
--thread    #B9BEC4   the provenance line at rest
--live      #0E7C6B   the thread carrying identity. Industrial teal.
--cut       #A8321F   the single broken thread. Oxide red, not alarm red.
```

Ink is off-black on paper while grounds go pure black — the asymmetry (borrowed
principle, not values) makes the inversion feel total.

`--live` and `--cut` are the only two chromatic values. They mean exactly one thing each
and are never used decoratively.

## Type

| Role | Family | Weight | Line-height | Use |
|---|---|---|---|---|
| Display | **Archivo Expanded** | 600 | **0.86** | Hero, section thesis lines |
| Headline | Archivo | 600 | 1.00 | Section titles |
| Sub | Archivo | 500 | 1.20 | Standfirsts, card headings |
| Body | Archivo | 400 | **1.45** | Prose |
| Datum | **IBM Plex Mono** | 400/500 | 1.40 | Every code, unit, score, label, verdict |

Both OFL, both self-hosted as WOFF2. **Mono is not decoration** — `MAT-78291`,
`M10 × 50`, `0.957` and `50.0 mm ± 0.5` need tabular figures, and the mono/grotesque split
is what makes data legible as data.

Line-height tightens as size grows: `1.45 → 1.20 → 1.00 → 0.86`.

## Motion laws

1. **PROSE EASES · DATA SNAPS.** Sentences and headings move on `power2.out`. Codes,
   counters, chips and verdicts change with **no travel and no easing** — a 90–120 ms
   opacity step or a stepped character reveal. *A number that glides is being sold to you;
   a number that snaps is being reported.*
2. **One easing family.** `power2.out` for entrances, `power2.inOut` for scrubbed states.
   Nothing elastic, nothing bouncing, ever.
3. **Entry from below or along the thread.** Never from the sides.
4. **Exactly one scrubbed animation** (§S1). Everything else is discrete.
5. **Everything reverses.** Scroll up un-reveals; the page has no consumed state.
6. **Durations:** fast 0.2 s · base 0.5 s · slow 0.8 s. Stagger: tight 0.03 · lines 0.06 ·
   hero 0.14.

## Forbidden — the anti-gimmick list

Glowing nodes · particle fields · gradient meshes · "AI brain" imagery · neural-network
diagrams · floating cards with no referent · typewriter effects on prose · counters that
ease · drop shadows · bevels · noise texture · drawn calipers · dial gauges · seven-segment
display fonts · parallax on decorative imagery · anything that moves when the user is
reading.

---

# 2 · Landing page — section by section

Twelve sections. Page height ≈ **9.5 viewports**. Percentages below are of total page
scroll.

---

## S0 · HERO — "One bolt. Five names."
**0 – 8%** · Ground `--paper` · Height 1.0 vp (pinned, see S1)

### Purpose
Deliver the problem as an artefact before delivering it as a sentence.

### User question forming
*"Wait — are those all the same thing?"*

### Composition (1440×900)

```
┌────────────────────────────────────────────────────────────────────────┐
│ SIH26099 · MoP&NG / CPCL                    [ SYNTHETIC DATA ]  [?]   │  mono 11
│                                                                        │
│      REF-SOUTH · MM-4471                                               │
│        SS HEX BOLT M10 X 50                                            │
│                   PIPELINE-DIV · 100238841                             │  ← optical
│                     STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM         │    centre,
│   PETCHEM-WEST · B-HX-SS-1050                                          │    y 22–52%
│     BOLT HEX SS M10*50                                                 │
│              TERMINAL-EAST · 55021907                                  │
│                HEX BOLT, S/S, M10 X 50 MM (OLD SPEC)                   │
│         REF-NORTH · 4471-A                                             │
│           BOLT,HEXAGON HEAD,STAINLESS,M10X50                           │
│                                                                        │
│  One bolt.                                                             │  Archivo
│  Five names.                                                           │  Expanded
│  No code in common.                                                    │  112px/0.86
│                                                                        │
│  One Nation – One Material Code. Every CPSE code kept, permanently.    │  mono 15
│                                                                        │
│  SCROLL TO RESOLVE ↓         34 TOKENS · 0 MAPPED · 0 DISCARDED        │  mono 11
└────────────────────────────────────────────────────────────────────────┘
```

**The evidence occupies the optical centre; the headline sits below it as a caption.**
A judge who reads only the five rows already has the problem statement. The h1 names what
they just noticed themselves. This inversion is the hero's whole idea — domain audiences
trust artefacts over claims.

**The rows are deliberately misaligned.** Left origins at +12, +148, 0, +96, +40 px; type
sizes 13/13/14/13/14 px. Five systems that never spoke to each other do not share a grid.
Flush-left they would read as *a list of synonyms*; misaligned they read as *five
institutions operating independently*. **The mess is the argument.**

**Org labels are functional, never corporate:** `REF-SOUTH`, `PIPELINE-DIV`. No invented
company names, no real CPSE names. The `SYNTHETIC DATA` chip is pinned chrome for the
whole hero and thesis — always visible, never a footnote. Its `[?]` opens: *"Source
records are synthetic, constructed for demonstration. Classification and attribute schema
derive from the public FLIS/PUB LOG catalogue. Not CPSE data."*

### Animation — load choreography (1.4 s total)

| t | What | Class | Why it exists |
|---|---|---|---|
| 0.00 | Paper ground present. Nothing else. | — | No preloader. A preloader on a demo is a second of nothing. |
| 0.15 | Chrome rail + `SYNTHETIC` chip snap in, opacity only | D | Disclosure arrives *first*, before any claim |
| 0.25 | Five rows reveal, **stepped character reveal**, mono, stagger 0.14, tight | B | Reads as records being *printed*, not animated in |
| 0.80 | h1 three lines rise `y:64→0`, `autoAlpha 0→1`, stagger 0.06, `power2.out`, masked lines | B | Prose eases. The caption arrives after the evidence. |
| 1.20 | Standfirst + bottom rail fade, 0.3 s | B | Least important, arrives last |
| 1.40 | `SCROLL TO RESOLVE` begins a 3 s / 6 px vertical breath | B | The only looping motion on the page; it is an affordance, not decoration |

**Reduced motion:** all of the above renders in final state at 0.2 s opacity. The breath
does not run.

---

## S1 · THE RESOLUTION — the one scrubbed animation
**8 – 26%** · Pinned **180 vh** · `--paper` → `--void` · **THE THESIS**

This is the single class-A animation in the entire experience. Everything else on the page
is a discrete reveal. It is spent here because this is the one idea the visitor must leave
with: **different language, same material — and nothing was thrown away.**

### Scroll-by-scroll

**0%** — Hero final state. Five misaligned rows, headline below, paper ground.
Bottom rail: `34 TOKENS · 0 MAPPED · 0 DISCARDED`.

**10%** — The headline drops away first (`y:0→-40`, `autoAlpha→0`). The five rows begin
drifting toward a **shared vertical axis at x = 38%** of the viewport. They are still
misaligned but converging. Ground begins its interpolation, paper → bone.
*Communicates: something is pulling these together.*

**25%** — Rows reach the axis and **left-align for the first time in the page's life**.
The instant they align, a **1px `--thread` line** draws downward through all five origin
points, top to bottom, 0.4 s. Ground now mid-grey.
*Communicates: they were always related — nobody could see it.*

**40%** — **Normalisation.** Each row's text re-typesets in place, token by token, using a
stepped character swap (data snaps — no morphing, no crossfade):
`SS` → `STAINLESS STEEL`, `HEX` → `HEXAGONAL`, `M10*50` → `M10 × 50`, `L50` → `50 MM`.
Tokens that are noise — `(OLD SPEC)`, `,` separators, `S/S` punctuation — **strike through
and fade to `--graphite`, but do not disappear.** Bottom rail counter begins:
`34 TOKENS · 12 MAPPED · 0 DISCARDED`.
*Communicates: the machine is reading, not guessing. And it discards nothing silently.*

**50%** — **Attribute extraction.** The five normalised rows collapse vertically into
**one four-row attribute block**, mono, right-aligned values:

```
TYPE       BOLT, MACHINE
MATERIAL   STAINLESS STEEL
THREAD     M10  ·  10.0 mm
LENGTH     50.0 mm  ± 0.5
```

The five source rows do not vanish — they **shrink to 11px mono chips and dock to the
left margin**, each still joined to the attribute block by its own thread, which turns
`--live`. Ground is now near-black. Rail: `34 TOKENS · 34 MAPPED · 0 DISCARDED`.
*Communicates: this is what the machine actually compares. And every source is still
attached.*

**65%** — The canonical identity **stamps** in above the attribute block — no travel, no
fade-in, a hard 100 ms cut, mono, `--live`:

```
NMC-00018426
```

*Communicates: one code now exists. It was minted, not guessed.*

**75%** — Ground reaches `--void`. The five docked chips brighten to full opacity in the
left margin under a mono header `TRACEABILITY · 5 SOURCE CODES RETAINED`. Threads hold.
*Communicates: **the clause the problem statement asked for, made visible.***

**90%** — Everything holds. A single line of prose masks in beneath:
**"Different language. Same material."**

**100%** — Pin releases. The attribute block and NMC identity scroll away upward
naturally; the five chips and their threads **remain fixed to the left margin and persist
for the next three sections.** The thread rail is now a permanent page element.

### Why this animation exists
It is the product's entire claim in one continuous gesture, and it is the only place where
continuous scroll-coupling is justified: the viewer's own scrolling performs the
harmonisation. Cutting it would leave the page arguing in paragraphs.

**Implementation:** GSAP timeline + ScrollTrigger, `pin: true`, `end: "+=180%"`,
`scrub: 1`, `anticipatePin: 1`. Rows are DOM elements on transforms; the thread is one
inline SVG `<path>` animated by `stroke-dashoffset`. No canvas, no WebGL.

**Reduced motion:** pin disabled entirely. The section renders as three static stacked
states — *fragmented → normalised → canonical* — each with its caption, separated by
rules. All meaning preserved, no scroll coupling.

**Mobile:** pin **disabled**. See §5.

---

## S2 · THE SCALE — one becomes a system
**26 – 36%** · `--void`

### User question
*"Fine — but how big is this really?"*

One number is made dominant. The other three support it. Dumping four large numbers
flattens all of them.

**Dominant:** `1,824,354` — Archivo Expanded 200px, `--paper` on void, tabular.
Label beneath, mono 12: `ITEMS IN THE SIX COMMODITY FAMILIES WE INDEXED`
Superscript `ᴬ` resolving in the right margin rail to:
`ᴬ measured from the public DLA FLIS/PUB LOG catalogue, 2026-08-26`.

**Supporting**, three mono rows below, 24px:
```
492,965      NIINs carrying more than one manufacturer part number
23,610       recorded standardization decisions
8,183,475    attribute assertions
```

### Animation
The dominant number **assembles from the previous section's identity**: the `NMC-00018426`
chip scales up and its digits are replaced, stepped, into `1,824,354` over 0.5 s.
*This is not a counter.* Counters that tick up read as a slot machine and imply the number
is being generated. **The digits are replaced, not incremented** — data snaps.
The three supporting rows reveal on stagger 0.06 at `top 80%`.

**Why:** the transition from *one material* to *a national scale* has to be shown as the
same object growing, not as a new slide. That is the argument — this is one instance of a
systemic problem.

---

## S3 · THE TRAP — 0.960 vs 0.957
**36 – 48%** · `--void` · **the setup for the money shot**

### User question
*"Surely an AI can just tell these apart?"*

Two descriptions enter, left and right, mono 20px:

```
STAINLESS STEEL HEXAGONAL BOLT      SS HEX BOLT
10MM × 50MM                          M10 × 75
```

Beneath each, a semantic score stamps in: **`0.960`** and **`0.957`**.
Between them a hairline and one mono label: `Δ 0.003`.

Then the headline masks in:
**"An AI model scored these three thousandths apart."**

Then, after a deliberate 600 ms hold with nothing moving:
**"One is the same bolt. One is a different bolt."**

### Animation
Scores **stamp** (100 ms, no travel). The 600 ms dead hold is the most important timing on
the page — it is the beat where the visitor tries to spot the difference and fails.
Nothing may move during it.

**Why:** the visitor must *experience* the trap before it is explained. If the page
explains first, the veto in S4 is a feature. If the visitor fails first, the veto is a
relief. Same information, opposite emotional value.

---

## S4 · THE VETO — the one cut thread
**48 – 58%** · `--void` · **THE MONEY SHOT**

The evidence table builds row by row, mono, stagger 0.06, both candidates side by side:

```
                     SOURCE            CANDIDATE
ITEM TYPE            BOLT, MACHINE     BOLT, MACHINE        ✓ AGREE
MATERIAL             STAINLESS STEEL   STAINLESS STEEL      ✓ AGREE
THREAD DIAMETER      10.0 mm           10.0 mm              ✓ AGREE
LENGTH               50.0 mm           75.0 mm              ✗ DISAGREE
```

The first three rows resolve `✓` in `--live`. The page has taught the viewer to expect
threads to hold.

**Then the LENGTH row.** The `✗` stamps in `--cut`. Simultaneously — and this is the
payoff the whole page has been building — **the thread running down the left margin
visibly severs at this row.** A 2px gap opens. The severed lower segment falls 8 px and
goes `--graphite`.

The verdict stamps beneath, no travel, `--cut`:
```
DISTINCT
Length: 50.0 mm vs 75.0 mm — differs by 25.0 mm, tolerance 0.5 mm
CONFIDENCE 0.000
```

And beside it, held from S3:
```
SEMANTIC SIMILARITY 0.957
```

Final line, masked in:
**"The text similarity was higher than for the match we accepted. It did not matter."**

### Animation
The severing is **the only destructive motion in the experience**. Total duration 240 ms:
gap opens 90 ms, segment falls 150 ms, `power2.in` (the one inward ease on the page —
things fall, they do not ease out of falling).

**Why:** nine screens have established that the thread never breaks. Breaking it once,
here, converts an architectural decision into a visceral event. This is why the identity
law exists.

**Never colour alone:** every verdict carries a glyph (`✓ ✗ ?`), a word (`AGREE`
`DISAGREE` `UNKNOWN`), and a position. Colour is the third signal, not the first.

---

## S5 · THE ENGINE — how it actually works
**58 – 66%** · `--void` → `--paper` (tonal return begins)

The real pipeline, drawn as a **vertical rail with the source description pinned at the
top of the viewport for the whole section** so the viewer never loses the referent:

```
  SS HEX BOLT M10 X 50          ← stays visible, sticky
  ─────────────────────────
  NORMALISE          →  STAINLESS STEEL HEXAGONAL BOLT M10 × 50
  EXTRACT            →  TYPE · MATERIAL · THREAD · LENGTH
  RETRIEVE  ┌ lexical   char n-gram, exact symbols
            └ dense     bge-small-en-v1.5
            → fused by reciprocal rank, k=60
  COMPARE            →  AGREE / DISAGREE / UNKNOWN
  VETO               →  gate, not weight
  SCORE              →  0.85 × attributes + 0.15 × text
  DECIDE             →  MATCH / NEAR / REVIEW / DISTINCT
```

### Animation
Stages reveal on scroll, stagger 0.06. **The two retrieval channels render differently on
purpose** — lexical as discrete stepped ticks (it matches symbols), dense as a continuous
fade (it matches meaning). They then converge into one row.

**Why:** the two channels genuinely behave differently, and showing them identically would
misrepresent the architecture. This is the section that proves we are not a wrapper.

**Explicitly not drawn:** glowing nodes, animated particles travelling along the lines, a
brain, a neural net. Forbidden list, §1.

---

## S6 · UNKNOWN — controlled uncertainty
**66 – 73%** · `--paper`

Three states, equal visual weight, on paper:

```
✓  AGREE        both sides stated it, and they match
✗  DISAGREE     both sides stated it, and they differ
?  UNKNOWN      at least one side did not state it
```

Then:
**"UNKNOWN is not a failure. It is the system declining to guess."**

And the consequence, mono:
`A wrong merge can send the wrong part to a live refinery. A missed merge costs a reviewer thirty seconds.`

### Animation
The `?` state renders in `--graphite` and — deliberately — **does not animate at all**
while the other two reveal. Stillness is the point.

**Why:** for a government system, restraint is a feature and must be presented as one.
This is also the section that pre-empts "what happens when it doesn't know?"

---

## S7 · THE PROOF — validation
**73 – 82%** · `--paper`

```
1,800 records   ·   600 canonical specifications   ·   300 probes

RECALL @ 1        HYBRID          94.3%
                  LEXICAL ONLY    79.7%
                                  ────────
                                  +14.7 points
```

Then the finding that matters:
```
2,408   candidates rejected on a critical attribute
2,399   of them carried text similarity ≥ 0.85
```
**"The better the semantic model gets, the more necessary the veto becomes."**

### Animation
The 94.3 / 79.7 comparison draws as **two horizontal bars from a shared left origin**,
scrubbed on entry, 0.6 s, `power2.out`. The gap between their endpoints is then bracketed
and labelled `+14.7`. Numbers stamp; **bars ease** — the bar is prose, the number is data.

**Why:** this is the ablation, and it is the single most credible thing we own — a measured
result that justifies an architectural choice.

---

## S8 · THE DISCLOSURE — what we have not proven
**82 – 88%** · `--bone` (a deliberate tonal shift; this section must not look like the
others)

**On-screen copy, verbatim:**

> ### What this evaluation does and does not show
>
> Our evaluation corpus is **synthetic**. We generated it from specifications we defined,
> extracted attributes with rules we wrote, and derived the labels from those same
> specifications. The reported precision therefore largely measures whether our extractor
> can invert our own generator.
>
> **It demonstrates that the pipeline is correct.** It is not evidence of accuracy on real
> material descriptions, and we do not present it as such.
>
> **Validated so far:** pipeline correctness · veto behaviour · abstention behaviour ·
> retrieval ablation
>
> **Not yet validated:** performance on real CPSE descriptions
>
> **Next:** hand-labelled real tender line items → held-out evaluation → production
> validation

### Animation
**None beyond a line reveal.** No number animation, no emphasis, no colour.

**Why:** an animated disclosure reads as spin. The absence of motion here is a design
decision and it is the most persuasive thing on the page to a judge who has watched five
teams overclaim. Volunteering this before being asked converts our biggest vulnerability
into a credibility signal.

---

## S9 · THE FOUNDATION — where the data comes from
**88 – 93%** · `--paper`

```
FLIS / PUB LOG           public US federal catalogue, FOIA release
        ↓                built on the NATO Codification System
APPROVED ITEM NAMES      79,883 with English definitions
ATTRIBUTE DICTIONARY     27,552 attribute definitions
        ↓
CANONICAL REPRESENTATION
```

One line of prose: **"India's National Codification Bureau adopted the same system for
defence materiel in 2008. There is no civil-CPSE equivalent. That gap is the opportunity."**

Provenance note, mono, `--graphite`:
`FLIS-derived reference data. Not CPSE data. Synthetic CPSE surface descriptions generated over real catalogue identities.`

**Why:** trust. It also pre-empts "where did your data come from?", which is the second
question every judge asks.

---

## S10 · CTA — the transition
**93 – 100%** · `--void`

Display, Archivo Expanded:
**"Stop matching names.
Start resolving materials."**

Then, mono, and this is the bridge:
```
The bolt you just watched resolve is loaded and waiting.

        [  ENTER THE PLATFORM  →  ]

NMC-00018426 · 5 source codes retained
```

### Animation
On click: the CTA does **not** navigate to a blank page. The `NMC-00018426` chip and its
five threads **fly to their final position in the platform's Material Detail header**
(FLIP transform, 0.6 s, `power2.inOut`) while the platform chrome fades in around them.

**Why:** the visitor entered a machine they just learned about, carrying the object they
watched being made. It costs one transition and it is the difference between "a landing
page linking to an app" and "one product."

---

# 3 · Master scroll table

| % | Section | Visitor sees | Motion | Message |
|---|---|---|---|---|
| 0 | Hero | 5 misaligned records, paper | stepped reveal | Five names, no shared code |
| 5 | Hero | Headline settled | — | The problem, named |
| 10 | Resolution | Headline drops, rows drift to axis | **scrub** | Something is pulling these together |
| 25 | Resolution | Rows align; thread draws | **scrub** | They were always related |
| 40 | Resolution | Text re-typesets; noise struck | **scrub** | The machine reads, and discards nothing |
| 50 | Resolution | Four canonical attributes; sources dock left | **scrub** | This is what is actually compared |
| 65 | Resolution | `NMC-00018426` stamps | **scrub** | One code now exists |
| 75 | Resolution | `5 SOURCE CODES RETAINED` | **scrub** | Nothing was lost |
| 90 | Resolution | "Different language. Same material." | mask | The thesis |
| 100→ | unpin | Threads persist to left margin | — | The rail is permanent |
| 30 | Scale | `1,824,354` dominant | digit swap | One instance of a systemic problem |
| 40 | Trap | Two descriptions, `0.960` / `0.957` | stamp + **600 ms hold** | You cannot tell them apart |
| 52 | Veto | Table builds; **thread severs at LENGTH** | stamp + 240 ms cut | Specification decides, not text |
| 56 | Veto | `DISTINCT · 0.000` beside `0.957` | stamp | Similarity did not matter |
| 62 | Engine | Pipeline rail, source sticky | stagger | Not a wrapper |
| 70 | Unknown | Three states; `?` still | none | Restraint is a feature |
| 78 | Proof | Two bars, `+14.7` bracket | ease + stamp | The ablation |
| 85 | Disclosure | Bone ground, plain text | **none** | What we have not proven |
| 90 | Foundation | FLIS provenance chain | stagger | Where this comes from |
| 97 | CTA | `NMC-00018426` waiting | FLIP on click | Enter the machine |

---

# 4 · Animation budget

| Class | Count | Notes |
|---|---:|---|
| **A — continuous scrubbed** | **1** | S1 Resolution only |
| B — scroll-triggered reveal | 14 | line masks, staggers, bar draws |
| C — hover | 3 | source chip → highlights its thread; provenance superscript → margin note; CTA |
| D — state transition | 4 | verdict stamps, thread sever, ground inversions, FLIP to platform |
| E — loading/processing | 2 | platform only |

### Cut list — considered and rejected

| Cut | Why |
|---|---|
| Particles travelling along the threads | Decorative. The thread's meaning is *persistence*, not flow. |
| Counter tick-up on the scale numbers | Implies generation. Digits are replaced, not counted. |
| Parallax on any section | Communicates nothing here; costs scroll jank. |
| A second pinned section for the veto | Budget violation. The veto is stronger as a fast stamp than a slow scrub. |
| 3D/WebGL bolt render | Offline constraint, build cost, and it would make an engineering page look like a product ad. |
| Animated pipeline "data packets" in S5 | Generic AI-diagram cliché; forbidden list. |
| Typewriter effect on prose | Slows reading, communicates nothing. |

---

# 5 · Responsive

| | Desktop ≥1200 | Tablet 768–1199 | Mobile <768 |
|---|---|---|---|
| Hero rows | 5, misaligned | 4, reduced offsets | **3, stacked flush** — misalignment is illegible at 375px |
| Display type | 112 px | 72 px | 44 px |
| **S1 Resolution** | **pinned, scrubbed, 180vh** | pinned, 140vh | **NOT pinned** — becomes 3 discrete stacked states, each revealing on entry |
| Thread rail | left margin, persistent | left margin | **inline between blocks**, not a margin rail |
| S4 evidence table | 2 columns side by side | 2 columns | **stacked pairs**, one attribute per block |
| S7 bars | horizontal | horizontal | horizontal, full width |

**The mobile decision that matters:** the scrubbed pin does **not** run below 768px.
Pinning fights momentum scrolling on touch, and the teardown found the reference site
shipping a 1440px canvas onto a 375px viewport. Mobile gets the same *narrative* as three
authored states, not the same *mechanism* compressed.

---

# 6 · Accessibility

- **Exactly one `<h1>`** (the hero). Real `<h2>` per section, `<h3>` within. The teardown
  found 35 `<h1>` and zero `<h2>` — we do the opposite.
- Landmarks: `<header>`, `<nav>`, `<main>`, `<footer>`. All present.
- **No meaning from colour or motion alone.** Every verdict = glyph + word + colour.
  Every scrubbed state has a static equivalent.
- **`prefers-reduced-motion`**: the pin is disabled, S1 renders as three static captioned
  states, all stamps become 0.2 s opacity, the CTA FLIP becomes a plain navigation.
  This is a real branch, not a `transition: none` blanket.
- **Keyboard**: the pinned section is skippable — a focusable "Skip the animation" control
  is the first tab stop inside S1 and jumps to S2. Scroll-driven narrative must never trap
  a keyboard user.
- Alt text: the five hero records are real text, not images. The thread SVG is
  `aria-hidden` with the relationship stated in adjacent text. The evidence table is a real
  `<table>` with `<caption>` and scope'd headers — a screen reader reads the verdicts.
- Contrast: `--ink` on `--paper` ≈ 15:1. `--live` and `--cut` on `--void` both verified
  ≥ 4.5:1 before build.

---

# 7 · Performance and demo safety

- **Zero non-localhost requests.** GSAP, Lenis, both fonts bundled and self-hosted as
  WOFF2. No CDN, no analytics, no third-party WebGL. Verified in devtools in airplane mode.
- Only `transform` and `opacity` animated. The ground inversion animates
  `background-color` on one element, which is acceptable and measured.
- The thread is one inline SVG path animated by `stroke-dashoffset` — no canvas.
- No images in the first two sections; the hero is pure text and one SVG.
- Deterministic seeded demo content. Same bytes every run.
- Landing page target: **< 400 KB total**, first paint < 1 s on the demo laptop.

---

# 8 · THE PLATFORM

Different register. The landing page is editorial, cinematic, narrative. The platform is
**precise, structured, technical, dense where density earns it.** It shares the palette,
both typefaces, the spacing scale and the motion laws — and inherits **none** of the
editorial scale or drama. No section is taller than the viewport. Nothing is pinned.
Nothing is scrubbed.

The thread survives as the **provenance rail** — the one visual element carried across.

## Screens

### P1 · Home
Not a vanity dashboard. Four tiles only, every figure labelled `DEMONSTRATION DATA`:
materials indexed · canonical identities · pending review · vetoes recorded.
Primary action dominant: **`CHECK A MATERIAL`**. Recent checks list beneath.

### P2 · Material Check — the primary interaction
One input, one button. Placeholder is a real example. Calls the **real engine** — no
mocked responses anywhere in this flow.

### P3 · Analysis
**The honest problem: the engine's p50 is 13 ms. It finishes before a progress animation
can render.** We will not pad it with fake delay.

Solution: run it, get the real result, then offer **`▷ REPLAY ANALYSIS`** — a
user-controlled 4 s stepped replay of the *actual* stage outputs (normalised text,
extracted attributes, candidates retrieved, comparisons, verdict). Labelled
`REPLAY OF COMPLETED ANALYSIS · 13 ms`. The speed is a feature; the replay is for humans.
Nothing is invented, nothing is delayed.

### P4 · Match Results
Ranked candidates. **Vetoed candidates are shown, ranked last, with the reason attached** —
they are the most persuasive output the system produces. Each row: candidate, semantic
score, attribute agreement, decision chip, expand → evidence table.

### P5 · Material Detail
Canonical identity, normalised attributes, **mapped CPSE codes with the provenance rail
visible**, relationships, confidence (labelled *uncalibrated ranking score*), per-record
provenance tag, decision history.

### P6 · Check-Before-Create
The flow that reframes the product from cleanup to governance. Type a new material →
system intercepts → `POSSIBLE EXISTING MATERIAL · NMC-00018426 · 0.94` with full evidence
→ `USE EXISTING` or `CONTINUE ANYWAY` (which records the override).

### P7 · Evaluation
Tabs: Performance · Ablation · Veto Analysis · Corpus. **The synthetic-corpus caveat sits
inline at the top of every tab**, not in a footnote.

### P8 · Provenance
Source table, licences, per-record provenance counts, the FLIS/NCS chain. The trust screen.

## Demo Mode
Entered by `?demo=1`. It **pre-warms** the engine and index, **pre-seeds** a known corpus,
enables keyboard jumps to each demo beat, and adds a reset. It **never fabricates an engine
result** — every score shown in Demo Mode is computed live by the real engine on seeded
input. That line is not negotiable.

---

# 9 · Build order

The first three items are the demo. Everything after is upside.

| # | Item | Why first |
|---|---|---|
| 1 | **S0 Hero + S1 Resolution** | The thesis. Without it there is no story. |
| 2 | **S3 Trap + S4 Veto** | The money shot. This is what wins the review. |
| 3 | **P2 Material Check + P4 Match Results, wired to the real engine** | Proves it is not a film |
| 4 | REST API — `/match`, `/check-before-create`, `/material/{id}`, `/evaluation` | Unblocks 3 |
| 5 | S7 Proof + S8 Disclosure | Credibility, cheap to build (static) |
| 6 | P6 Check-Before-Create | The governance story |
| 7 | S2, S5, S6, S9, S10 | Narrative completion |
| 8 | P1, P3, P5, P7, P8 | Platform completion |

**If time runs out after item 3, we still have a winning demo** and can narrate the rest.
