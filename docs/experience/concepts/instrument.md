# CONCEPT — "GAUGE BLOCK"

A creative direction for the SIH26099 landing page.
Register: metrology. The page does not illustrate an instrument. It *behaves* like one.

---

## 1. THE ONE-LINE THESIS

> **Nearly identical is not identical — and only measurement knows the difference.**

In three seconds the visitor sees a graduated scale, a headline that says NEARLY IDENTICAL
IS NOT IDENTICAL, and a status panel reading `RESOLUTION 0.5 mm`. They understand, before
reading a paragraph, that this is a thing that measures material descriptions and tells
apart two records that look the same.

The proof of the thesis is the 0.960 / 0.957 pair. The page is built so that everything
before that moment sets up a measurement, and everything after it lives with the result.

---

## 2. NAME AND IDENTITY

### Name: **GAUGE BLOCK** (short handle: **GAUGE**)

A gauge block is a lapped steel rectangle of certified length. It is not a tool that does
work — it is the *reference* against which working tools are set. Every caliper in every
workshop in a country traces back, through a chain of comparisons, to a national set of
gauge blocks held by the national standards body.

That is structurally identical to what this product claims:

    One Nation - One Material Code       =  one national reference standard
    traceability to individual CPSE codes =  the metrological traceability chain

This is why the metaphor is not decoration. The product *is* a reference standard with a
traceability chain. We are naming what it already is, not dressing it up.

### Emotional register: **calibrated authority**

Not clinical (clinical means hospital, means anxiety). Not monumental (monumental means
government stock photography, means nobody believes it). Not investigative (investigative
implies we are accusing someone, and we are not — CPSEs did nothing wrong; they just
described things differently).

The feeling is a **metrology lab**: evenly lit, quiet, no drama, no shadows, everything
labelled with its unit and its uncertainty. The emotional payload is *trust through
disclosure*. The page is confident specifically because it tells you the limits of what it
measured.

### Why this register wins THIS audience

**Materials-management staff at a refinery.** They open a material master every working
day. They have been burned by systems that presented a confident number and were wrong.
They read specifications for a living — `M10 x 50, A2-70, DIN 933`. Unit-bearing,
tolerance-bearing type is their native language, not a stylistic choice. A page that
writes `50.0 mm ± 0.5` instead of "highly accurate matching" is speaking to them directly.
They will also spot a wrong unit instantly, which is the risk we accept (see §8).

**Government judges.** They respond to *governance*, not to visuals. Traceability, method,
provenance, and stated limits are the vocabulary of a defensible national system. The
provenance notation in §5 — where every figure on the page carries a superscript letter
naming its method — reads to a judge as an audit trail. That is the single most persuasive
thing we can put in front of an evaluator from a ministry.

**Neither group is a designer.** So the direction spends its budget on legibility and
disclosure rather than on delight. Nothing here needs design literacy to decode. A tick is
a tick. A band is a band. A gap is a gap.

### The anti-gimmick doctrine — five things we will NOT draw

The failure mode of this direction is skeuomorphism: a page that looks like a photograph
of a caliper. Explicitly forbidden:

| forbidden | why |
|---|---|
| A drawn caliper, micrometer or dial-gauge illustration | Literal, decorative, and instantly dates the page. It would be a picture of the metaphor instead of the metaphor. |
| A dial face with a sweeping needle | Implies an analogue continuous reading. Our verdict is discrete and our confidence is uncalibrated — a needle would lie. |
| Seven-segment / LCD display typefaces | Costume. Also poor legibility, and it makes real numbers look fake. |
| Brushed metal, noise texture, drop shadows, bevels | Texture is the tell of skeuomorphism. Our grounds are flat and uniform. |
| Machine-shop sound design, click-tick audio | Wi-Fi is off, a judge may be in a noisy hall, and audio communicates nothing a label cannot. |

What we draw instead are **instrument behaviours**, which are abstract and free:

1. **The page has a zero.** A datum line exists and everything registers to it.
2. **Every number carries a unit and a method.** No naked digits anywhere on the page.
3. **Readouts settle; they do not fly.** Numbers arrive by counting to rest, never by
   sliding in from off-screen.
4. **Tolerance is visible.** Any claim with uncertainty renders its band.
5. **Nothing is deleted, only marked.** A rejected candidate stays on screen as a
   dimmed reading with its reason. Instruments do not erase data.

Those five rules are the whole identity. They are enforceable in code review.

---

## 3. HERO, IN EXTREME DETAIL

### 3.1 Composition — first viewport, 1440 x 900

```
 96px rail |<------------------ 1200px container ------------------>| 96px rail
+----------+---------------------------------------------------------+---------+
|          |                                                         |         |
| 01       |                                                         |  00.0 % |
| SPEC     |                                                         |         |
|          |   NEARLY IDENTICAL                                      |         |
|  ·       |   IS NOT                                                |         |
|  ·       |   IDENTICAL.                                            |    ᴹ ˢ  |
|  ·       |                                                         |    ᶠ ᴱ  |
|==========|=========================================================|=========|  <- DATUM, 44% vh
|  ' ' ' ' | ' ' ' ' | ' ' ' ' | ' ' ' ' | ' ' ' ' | ' ' ' ' | ' ' ' |         |  <- graduated ticks
|          |  0        10        20        30        40        50     |        |
|          |                                                         |         |
|          |  SIH26099 · MATERIAL CODE STANDARDISATION · MoPNG / CPCL |         |
|          |                                                         |         |
|          |  A material-identity engine that reads a free-text       |         |
|          |  description, extracts its measurable attributes, and    |         |
|          |  refuses to merge two records when any critical          |         |
|          |  attribute disagrees.          GAUGE   hybrid + veto     |         |
|          |                                RESOLUTION  0.5 mm        |         |
|          |                                CORPUS  1,800 records ˢ   |         |
|          |                                LATENCY p50 13 ms ᴹ       |         |
|          |                                STATUS  prototype ·      |         |
|          |                                        offline · local  |         |
+----------+---------------------------------------------------------+---------+
```

**The optical centre is the datum line**, a 1px full-bleed horizontal rule at 44% of
viewport height — slightly above true centre, which is where the resting eye actually sits.
It is not a divider. It is the page's zero, and it returns as the spine of the thesis
animation and the proof section. Below it hangs a graduated scale: minor ticks every 20px
at 6px height, major ticks every 100px at 14px height with a mono numeral beneath.

**The H1 sits ON the datum.** The baseline of its last line is exactly the datum line — not
near it, on it. Type resting precisely on a rule is the single most instrument-like gesture
available in typography and it costs nothing. Set left, aligned to the same tick the rail
numbers use.

**The specification readout** sits lower-right, mono, five rows, right-aligned values in a
tabular-figure column. It is the object that makes the page read as equipment rather than
marketing, and it is where the honesty constraints appear *as a feature*: `STATUS
prototype · offline · localhost` is a field on a panel, not an apology in a footnote.

**The left rail** carries `01 / SPEC` and the tick column. It is never empty on any section
of the page. **The right rail** carries the live scroll readout `00.0 %` and the permanent
provenance legend (ᴹ ˢ ᶠ ᴱ — see §5.5).

### 3.2 The copy — real words

**H1** (three lines, caps):

> NEARLY IDENTICAL
> IS NOT
> IDENTICAL.

**Deck** (mono, one line, above the paragraph):

> SIH26099 · AI STANDARDISATION & HARMONISATION OF MATERIAL CODES ACROSS CPSEs
> · MINISTRY OF PETROLEUM & NATURAL GAS / CPCL

**Paragraph** (Archivo 400, 46ch measure):

> A material-identity engine that reads a free-text description, extracts its measurable
> attributes, and refuses to merge two records when any critical attribute disagrees.

**Readout panel** (mono, label column STEEL, value column GRAPHITE, tabular figures):

    GAUGE         hybrid retrieval + critical-attribute veto
    RESOLUTION    0.5 mm tolerance on LENGTH
    CORPUS        1,800 records · 600 canonical specs ˢ
    LATENCY       p50 13 ms · p95 17 ms ᴹ
    STATUS        prototype · offline · localhost

**Scroll affordance** (mono, 11px, right rail, STEEL): `00.0 %` — nothing else. See the cut
in §7 for why there is no arrow.

Note what the hero does **not** say. It does not say "AI-powered." It does not say
"revolutionising procurement." It does not claim a deployment. It states an instrument, its
resolution, its corpus and its status. That restraint is the brand.

### 3.3 Load sequence — timings, order, stagger

Total time to settled: **1,340 ms**. Every tween uses the `power2` family; nothing else is
permitted anywhere on the page.

| t (ms) | element | motion | duration / ease | why it exists |
|---|---|---|---|---|
| 0 | PLATE ground | painted, no animation | — | Fonts are self-hosted and preloaded from disk; there is no FOUT to hide. |
| 0 → 420 | datum line | horizontal scale from left margin tick to full bleed, origin left | 420ms power2.out | The instrument finds its zero before any content exists. Nothing else moves during this — the page's first act is establishing a reference. |
| 180 → 640 | 46 tick marks | each scales down from the datum, origin top, staggered left-to-right so each tick appears just behind the advancing datum line | 160ms each, stagger 6ms, power2.out | Converts a line into a **scale**. A line is decoration; a graduated line is an instrument. The causal stagger reads as the axis graduating itself. |
| 520 → 1040 | H1, 3 lines | SplitText lines with line masks; each line translates up from its own mask, appearing to be extruded upward out of the datum | 520ms each, stagger 90ms, power2.out | Highest polish-per-config gesture available. The upward direction ties the headline to the measurement axis it rests on. |
| 760 → 1180 | deck + paragraph | line-masked reveal, y 24px → 0, opacity 0 → 1 | 420ms, stagger 60ms, power2.out | Standard supporting reveal. Enters from below, consistent with every other reveal on the page. |
| 900 → 1240 | readout rows (5) | opacity 0 → 1, y 12px → 0 | 300ms, stagger 55ms, power2.out | Rows arrive top-down like a panel powering up field by field. |
| 940 → 1340 | readout **numerals** (13, 17, 1,800, 600, 0.5) | count from 0 and **settle** — monotonic approach, no overshoot, no bounce | 640ms, power2.out, tabular figures locked so column width never jitters | **Readouts settle; they do not fly.** This is the single micro-gesture that most establishes the register, and it is one tween. Tabular figures are load-bearing: without them the count-up reflows and the "instrument" read collapses into "web animation." |
| 1340 | `00.0 %` readout | appears, then tracks scroll for the rest of the page | — | Scroll affordance and progress indication in one, carrying real information. |

**Reduced motion:** the datum, ticks, H1, deck, paragraph and readout render in final state
at t=0. The numerals show their final values. Nothing is lost, because nothing in the hero
is communicated by motion alone.

### 3.4 What the eye does in the first three seconds

    0.0 - 0.4s   A single line draws left to right. The eye follows it. There is
                 nothing else to look at, so it follows it completely.
    0.2 - 0.6s   Ticks stamp beneath the line, just behind the eye's position.
                 The eye stays on the axis and now reads it as graduated.
    0.5 - 1.0s   Three lines of large type erupt upward off the left end of the
                 axis. The eye jumps up and reads top-down: NEARLY IDENTICAL /
                 IS NOT / IDENTICAL. It lands back on the datum, because the
                 last baseline is the datum.
    0.8 - 1.2s   Directly below the landing point, the deck and paragraph
                 appear. The eye reads the sentence without moving far.
    0.9 - 1.4s   Motion in the lower right pulls the eye across: numbers
                 settling. It reads RESOLUTION 0.5 mm and STATUS prototype.

The path is a Z that **begins and ends on the datum**. The eye is taught the page's
organising line in the first half-second and never has to be taught it again.

---

## 4. THE ONE THESIS ANIMATION — "THE COMPARATOR SWEEP"

**This is the only scrubbed, scroll-coupled animation on the entire landing page.** Every
other motion in the product is a discrete reveal, a hover, a state transition or a loading
state. The spend is justified below.

### 4.1 Why this and nothing else gets the pin

The claim `0.957 and 0.960 are indistinguishable, and their verdicts are opposite` cannot
be made in a static image, because the whole point is a *sequence*: first similarity is
measured and fails to separate, then attributes are measured and separate decisively. The
argument has an order, and scroll-scrubbing is the only mechanism that gives the viewer
control of that order — including the ability to scrub **backwards** and watch the veto
again, which is exactly what a sceptical judge will do. No other section on the page has an
argument whose meaning depends on sequence. So no other section gets a pin.

### 4.2 Stage geometry

The pinned stage inherits the hero's datum, now graduated in **millimetres, 0 to 90 mm
across the container width**. This is a real coordinate system: 50 mm and 75 mm are actual
positions, correctly spaced. It is the same scale object the visitor already learned in the
hero — continuity, not a new toy.

```
   left rail            0    10   20   30   40   50   60   70   80   90 mm
  +-------+  SOURCE  SS HEX BOLT M10 X 50
  | 05    |
  | mm    |  ========|====|====|====|====|====|====|====|====|====|====  <- mm axis
  |       |
  | STAGE |  CAND A  STAINLESS STEEL HEXAGONAL BOLT 10MM X 50MM   0.960
  | MEAS  |  CAND B  SS HEX BOLT M10 X 75                         0.957
  |       |  CAND C  NUT HEX SS M10                               0.895
  +-------+
             STATION   [ TYPE ]  [ MATERIAL ]  [ THREAD ]  [ LENGTH ]
```

**Pin length: 280vh.** `pinSpacing: true`, `scrub: 1`, `end: "+=280%"`. At Lenis-smoothed
scroll speed this is roughly six to eight seconds of deliberate scrolling — the right length
for a five-beat argument. It is *not* 400vh: the pin releases the instant the verdict lands,
so nobody is held captive after the payoff. **What unpins it:** the verdict stamps complete
at 100% progress and the ScrollTrigger end is reached; the following section is pre-painted
on pure black so the release reads as continuous ground rather than a snap.

A **stage readout** runs along the bottom of the pinned viewport throughout: mono, 12px,
`PIN 000.0 %` and the current beat name — `SCORE / SORT / EXTRACT / TIE / MEASURE / VETO /
VERDICT`. This is not decoration: it names the pipeline stages, tells the viewer where they
are in a pinned section (the classic pinned-scroll disorientation problem), and gives a
judge a vocabulary for asking to see a specific moment again.

### 4.3 Frame by frame

---

**SCROLL 0 % — beat: `SCORE` (pre-roll)**

*On screen:* PLATE ground. The mm axis is drawn but **unlabelled and dim** (STEEL at 30%
opacity) — an instrument that has not been zeroed. SOURCE line above the axis, mono,
GRAPHITE. Three candidate lines below, equal weight, unsorted, no scores. Left rail reads
`05 / mm`. Section head, Archivo 600, above everything: **"The eye cannot separate these."**

*Moving:* nothing. The stage holds still on entry so the viewer can read four lines of text.

*Changed:* n/a.

*Understands:* one source description, three candidates, no verdict yet. Reading them, they
cannot themselves tell which is the same bolt.

---

**SCROLL 10 % — beat: `SCORE`**

*Moving:* a semantic score appears at the right of each candidate row and **counts from
0.000 to its value**, settling. Because the timeline is scrubbed, the stagger is expressed
as scroll offset rather than delay: A occupies 10→16%, B occupies 12→18%, C occupies 14→20%.
Tabular figures; the column does not shift.

*Changed:* three numbers now exist that did not exist at 0%.

*Understands:* the model has scored all three candidates by meaning. The numbers are close.

---

**SCROLL 25 % — beat: `SORT`**

*Moving:* the three candidate rows translate vertically into score order (0.960 / 0.957 /
0.895), 22→30% progress, power2.out, staggered 40ms by row. Simultaneously a **similarity
bar** grows rightward from each score along a fixed 360px track.

The track is deliberately **zoomed: it maps 0.850 → 1.000 across its full 360px span.** A
mono annotation sits beneath it:

    SCALE  0.850 → 1.000   ·   FULL SPAN 360 px   ·   Δ(A,B) = 3 px

*Changed:* the field is ordered, and the near-identity of the top two is now geometry rather
than digits. C is visibly shorter and falls out of contention.

*Understands:* **We magnified the difference as far as the screen allows and it is still
three pixels.** This is the strongest single frame in the direction, because it does the
honest thing — it tells you the scale has been stretched — and the argument survives the
disclosure. A judge who suspects a chart trick finds the trick already labelled.

---

**SCROLL 40 % — beat: `EXTRACT`**

*Moving:* candidate C (0.895) translates down 40px and fades to 18% opacity. **It is not
removed.** It remains on stage as a dimmed reading for the rest of the animation, because
instruments do not erase data and neither do we.

A and B move to straddle the mm axis — SOURCE above, A and B below as two rows. Their mono
text then **decomposes**: SplitText by characters, and the substrings that are attribute
values (`SS`, `HEX`, `M10`, `50` / `STAINLESS STEEL`, `HEXAGONAL`, `10MM`, `50MM` / `75`)
hold GRAPHITE at full weight while every other character desaturates to STEEL at 40%.
Characters only — the strings are short labels, which is the correct use of character
splitting; prose elsewhere on the page always splits by lines.

*Changed:* the field narrowed to two, and the *measurable* portions of the text are now
visually separated from the connective prose.

*Understands:* the engine is about to stop reading and start measuring. It has found the
parts of the sentence that carry values.

---

**SCROLL 50 % — beat: `EXTRACT` → `TIE`**

*Moving:* the highlighted substrings **detach and travel** from their positions inside the
sentences to four labelled stations along the mm axis — `TYPE`, `MATERIAL`, `THREAD`,
`LENGTH`. Each token moves on a **straight path**, never an arc. Arcs are decorative;
instruments move on rails. Travel occupies 50→62% progress, staggered by station order
left-to-right, 60ms apart. As each token leaves, the residual prose in its sentence fades to
STEEL 25% and holds there.

*Changed:* both sentences are now hollowed out. Twelve tokens sit in four stations, three
deep (source / A / B).

*Understands:* two sentences written in completely different English produced the same
structured attributes. Standardisation is not rewriting the text — it is extracting what the
text was measuring.

---

**SCROLL 65 % — beat: `TIE`**

*Moving:* three of the four stations **resolve to AGREE**. Each agreement is drawn as a
short vertical **tie line in DYE blue**, connecting the source token through the axis to the
candidate token, scaling from the axis outward in both directions (origin centre, scaleY
0→1), 90ms each, staggered left-to-right.

Six ties are drawn: TYPE(A), TYPE(B), MATERIAL(A), MATERIAL(B), THREAD(A), THREAD(B).
`SS` ties to `STAINLESS STEEL`. `M10` ties to `10MM`. The **LENGTH station draws nothing.**
Its three tokens sit unconnected, with visible empty space where five other ties just
appeared.

*Changed:* agreement now has a visual form, and exactly one station is conspicuously untied.

*Understands:* on three of four measurements, these two candidates behave identically. The
tension is at maximum — nothing yet distinguishes A from B. And there is one measurement
still outstanding, which the eye has already found because it is the only gap in a row of
ties.

---

**SCROLL 75 % — beat: `MEASURE`** *(the longest beat, deliberately)*

*Moving:* the LENGTH station expands to occupy the stage. The mm axis, quietly present since
0%, **becomes the active instrument**: it brightens from STEEL 30% to GRAPHITE 100% and its
numerals fade in across 0–90 mm, 72→78% progress.

Three markers drop onto the axis (y −24px → 0, 220ms, power2.out, staggered 60ms):
SOURCE at **50**, A at **50**, B at **75**.

A **tolerance band** fades in around the source marker: a VELLUM-filled rectangle spanning
49.5 → 50.5 mm with 1px DYE edges, labelled in mono `TOL ± 0.5 mm`. It is 1 mm wide on a
90 mm scale — genuinely, visibly narrow. A lands coincident with SOURCE, inside the band.
B sits a quarter of the screen away, outside everything.

A dimension line with arrow terminators spans 50 → 75 with the readout **`Δ 25.0 mm`** in
OUT red, drawn from both ends toward the centre, 260ms.

Then a **hold**: from 84% to 88% progress, nothing moves at all. A held frame is an
instrument settling, and it gives a judge four percent of scroll to read `Δ 25.0 mm` and say
it out loud to the person next to them.

*Changed:* the abstract argument became a physical distance across the screen.

*Understands:* **what similarity could not see at three pixels, measurement sees at a
quarter of a screen.** That inversion of scale — the difference that was invisible in the
similarity view is enormous in the measurement view — is the entire thesis, delivered
geometrically, in one frame, without a sentence of explanation.

---

**SCROLL 90 % — beat: `VETO`**

*Moving:*

1. **The ground inverts.** PLATE → ZERO (pure black), wiped outward horizontally from the
   LENGTH station's centre line in both directions. 260ms of scrub, `power2.inOut` — the
   only inOut easing anywhere on the page, permitted because a gate closing is a symmetric
   event with a beginning and an end.
2. **B's ties retract.** The three DYE ties belonging to B scale back to 0 from the axis
   outward — exactly reversing how they were drawn. Retraction is more violent than a fade
   because it visibly *undoes an earned thing*.
3. **B's row and remaining marks snap to OUT red.** No transition; one frame.
4. **B's score is replaced, not decremented.** The readout that has said `0.957` since the
   10% mark is struck through and becomes `0.000` **instantaneously**.
5. **The tolerance band does not move.** It stays lit, in place, at the same width. The
   standard does not move when a part fails.
6. One line of mono type appears beneath B, in OUT red on black:

       VETO · LENGTH · 50 mm vs 75 mm · differs by 25 mm · tolerance 0.5 mm

*Changed:* a candidate that scored 0.957 for the entire animation now scores exactly zero,
with a named attribute, two values with units, a difference with a unit and a tolerance with
a unit.

*Understands:* **the veto is a gate, not a weight.** It did not reduce the score by some
amount — it zeroed it. Point 4 above is the most important motion decision on the whole
page: counting `0.957` down to `0.000` would *depict a weight* and would be a lie about our
own architecture. Instantaneous replacement depicts a gate. The motion is the argument.

---

**SCROLL 100 % — beat: `VERDICT`**

*Moving:* verdict slugs stamp in — scale 0.94 → 1.00 with opacity, 180ms each, power2.out,
staggered 80ms:

    CAND A   MATCH      0.994     (PLATE ink in a solid DYE slug)
    CAND B   DISTINCT   0.000     (OUT red type in an OUT-outlined slug)
    CAND C   DISTINCT   0.000     (OUT red, outlined)

Candidate C — dimmed since 40% — returns to full opacity for the final 6% of progress and
receives its own veto line, so the viewer sees the engine accounted for it too:

    VETO · ITEM TYPE · BOLT, MACHINE vs NUT, PLAIN, HEXAGON

A closing mono footer line, STEEL on black:

    3 CANDIDATES · 1 MATCH · 2 VETOED · TOTAL 13 ms ᴹ

Then the pin releases. The next section begins on the same pure black.

*Understands:* the complete result, including the reasons, including the case that never
came close. And that it took thirteen milliseconds.

### 4.4 Reduced-motion path for the pin

**The pin does not exist.** The section renders as a **static measurement report** — five
captioned figures in document order, each in final state, each with real prose beneath it:

1. The score table with the zoomed similarity bars and the `Δ = 3 px` annotation.
2. The four-station attribute table (source / A / B, twelve cells, agreement marked with a
   DYE rule rather than a drawn tie).
3. The mm axis with all three markers, the tolerance band, and `Δ 25.0 mm`.
4. The veto card on black, with both veto reasons.
5. The verdict table.

This is honestly a second design of the same section, and I count it as a real cost in §8.
But it satisfies the rule absolutely: **every number, every tie, every veto reason exists as
text in the DOM in both branches.** Nothing on this page is communicated by animation alone.

---

## 5. VISUAL SYSTEM

### 5.1 Palette — seven values

| token | hex | role |
|---|---|---|
| **PLATE** | `#EDEBE5` | The light ground for the whole upper page. A warm-neutral off-white — granite surface plate, drafting vellum. Never pure white; white is a browser default and reads as unconsidered. |
| **VELLUM** | `#DAD7CE` | Second light tone. The fill of every tolerance band, inset panel and table zebra. Bands need a fill that is neither white nor grey-blue. |
| **GRAPHITE** | `#0A0C0D` | Ink on light grounds. Off-black, warm-neutral, never `#000`. |
| **ZERO** | `#000000` | Pure black. Used **only** as the ground for inverted sections — the veto and the platform transition. The asymmetry (off-black ink on light, pure black ground on dark) is what makes inversion feel absolute rather than like a theme toggle. |
| **STEEL** | `#767C7E` | Rules, ticks, scale graduations, secondary and label type. The colour of a gauge block. |
| **DYE** | `#12386B` | Deep layout-dye blue. **Meaning: measured, agreeing, canonical.** Every tie line, every AGREE state, every canonical record. Machinists coat a part in blue dye and scribe measurement lines through it — which is precisely what this product does to a description. The accent has a story, not a mood board. |
| **OUT** | `#C2312B` on light / `#E8695C` on ZERO | Out-of-tolerance red. **Meaning: DISAGREE, vetoed, non-conforming.** Oxidised, not fire-engine. Two ground-bound renderings, one role — `#C2312B` on black is only 3.6:1 and fails AA, so the dark-ground value is mandatory, not optional. |

**UNKNOWN has no colour.** This is a deliberate and important decision. UNKNOWN is a
first-class state in our three-valued comparator and it is *not a warning* — it is the
absence of a reading. Colouring it amber would make missing data look like a problem with
the data rather than a fact about the data. UNKNOWN renders as STEEL at 55% with the em-dash
glyph in an open span. It never gets an icon and never gets red.

**Colour discipline:** the only saturated colour on the page is DYE and OUT, and both are
*semantic* — they mean AGREE and DISAGREE respectively and are never used for emphasis,
branding, buttons or hover states. If a colour appears, a comparison happened.

### 5.2 Type pairing

**Grotesque: Archivo** (variable, SIL OFL, self-hosted as a subset WOFF2). Chosen over Inter
because Inter is the default of everything and reads as unconsidered; chosen over the
licensed neo-grotesques for obvious reasons. Archivo has a genuine width axis, which matters
here: **type width is itself a measurement device**, and we use it — the D1 headline is set
at a width that exactly fills its measured span at each breakpoint. (Static per breakpoint.
Animating the width axis is cut — see §7.)

**Mono: IBM Plex Mono** (SIL OFL, self-hosted subset). Designed for engineering and
technical documentation, which is the register exactly. Its superfamily includes Plex
Devanagari, which gives us a real path for Hindi labels in the platform without introducing
a third type family. **Mono carries every label, every unit, every datum, every code, every
veto reason.** If a string is a value or a name of a value, it is mono. No exceptions.

Both fonts are bundled in the repo and preloaded. Zero runtime font requests. Verified with
Wi-Fi off.

### 5.3 Hierarchy and the line-height curve

Line-height is a **function of size, never chosen per element**. It tightens monotonically as
size grows — this is most of why large type reads as designed rather than as large.

| role | family / weight | size | line-height | tracking | case |
|---|---|---|---|---|---|
| D1 — hero H1 | Archivo Expanded 700 | clamp 64 → 132px | **0.86** | −0.02em | UPPER |
| D2 — section heads | Archivo 600 | 40 → 64px | **1.02** | −0.015em | sentence |
| H3 — sub-heads | Archivo 600 | 24 → 28px | **1.18** | −0.005em | sentence |
| Body | Archivo 400 | 18 → 19px | **1.44** | 0 | sentence |
| Label / datum | Plex Mono 500 | 12 → 13px | **1.30** | +0.08em | UPPER |
| Numeral readout | Plex Mono 400/500, **tabular figures** | 15 → 72px | **1.00** | 0 | — |

Curve: `1.44 → 1.30 → 1.18 → 1.02 → 0.86`. Measure: 62ch for prose, 46ch for the hero
paragraph and any pull statement.

**Tabular figures are mandatory on every numeral.** Any number that can change — a count-up,
a scrubbed value, a live readout — will jitter its column width without them, and column
jitter is the exact opposite of a precision instrument. This is a one-property decision that
carries a disproportionate share of the register.

### 5.4 Layout skeleton

```
+--------+--------------------------------------------------+--------+
| LEFT   |                                                   | RIGHT  |
| RAIL   |            CONTENT COLUMN, max 1200px             | RAIL   |
| 96px   |            single centred column                  | 96px   |
|        |            no 12-col grid                         |        |
| sect # |                                                   | scroll |
| unit   |            section padding:                       | %      |
| ticks  |              96px top/bottom desktop              |        |
|        |              56px top/bottom mobile               | prov.  |
|        |                                                   | legend |
+--------+--------------------------------------------------+--------+
```

**The registration rule — this is the mechanism that makes the page feel measured without
drawing a single instrument.** The left rail carries a continuous tick column: minor ticks
every 8px, major every 40px. **Every block's top edge aligns to a tick.** Every one. A
heading, a paragraph, a table, a figure — all of them land on a graduation. The effect is
subliminal on first read and unmistakable on second: nothing on this page is placed by
feel; everything is registered to a scale.

The left rail also carries the section number and its **unit label** — `05 / mm`, `07 /
count`, `09 / ms`. Sections are named by what they measure.

**Axis discipline:** the datum/mm axis appears in only **four of eleven sections** — hero,
the comparator sweep, the veto, and proof. If every section used it, it would stop
signifying. The other seven sections have the rail and the registration but no axis.

### 5.5 Point / Range / Set / Unknown as the visual system

The value model is not backend trivia. It is the notation system for the entire product —
landing page, platform, tables, everywhere a value appears. **Four marks, one axis.**

| kind | mark | rendering | example |
|---|---|---|---|
| **Point** | a tick | 2px GRAPHITE tick on the local value axis; value in mono with its unit in STEEL | `50.0 mm` ▮ |
| **Range** | a band | VELLUM fill with 1px DYE edges spanning min→max, drawn to scale on the local axis | `45.0 – 55.0 mm` ▭ |
| **Set** | a bracket | one bracket containing N ticks, one per member, evenly placed | `{ A2, A4 }` ⟦▮ ▮⟧ |
| **Unknown** | a gap | two tick stubs with a dashed span and a centred em-dash, STEEL 55% | `—` ▮---▮ |

    Point is a tick.  Range is a band.  Set is a bracket.  Unknown is a gap.

Everything closes onto this. The tolerance band in the thesis animation *is* the Range mark.
The four stations *are* Point marks. When the platform's Material Detail screen shows an
attribute with no reading, it is a Unknown gap and looks the same as it did on the landing
page. One notation, learned once, used everywhere. That is a design system rather than a
style.

**And the honesty constraint becomes notation.** Because `confidence` is an uncalibrated
ranking score and not a probability, **it may never be drawn as a Point.** It is drawn as a
Range with an unbounded right edge and labelled:

    CONFIDENCE  0.994    ▭ ---->    RANK · UNCALIBRATED · NOT A PROBABILITY

A calibrated probability would be a Point. Ours is not, so the grammar refuses to draw it as
one. The caveat lives in the mark, not in a footnote nobody reads.

### 5.6 The provenance notation

Every figure on the page carries a **superscript method letter**, with the legend permanently
resident in the right rail:

    ᴹ  measured on our own harness, reproducible
    ˢ  synthetic, construction-derived evaluation corpus
    ᶠ  FLIS / PUB LOG derived reference data — NOT CPSE data
    ᴱ  estimated or illustrative

So the page reads `94.3 %ˢ`, `13 msᴹ`, `1,824,354ᶠ`. A judge can never mistake one class of
number for another, and the distinction is *structural* rather than a paragraph of caveats
that a skimmer misses. Constraints 1, 2 and 4 of the honesty rules are satisfied by the
typography itself.

The synthetic-corpus section then has somewhere to stand: it is not an apology, it is the
legend entry for ˢ, expanded. Headline for that section: **"What 100 % precision actually
measures."** Body states plainly that the corpus was generated from specs we defined,
extracted by rules we wrote, labelled from those same specs, and that the result
demonstrates the pipeline is correct — it is not evidence of real-world accuracy. In this
direction that paragraph reads as *calibration disclosure*, which in a metrology register is
the mark of a serious instrument rather than a weak one.

### 5.7 What makes this OURS

Nothing in this system could be lifted from an essay about fast fashion:

1. **Datum + tick registration** as the layout mechanism.
2. **Four value marks** (tick / band / bracket / gap) derived from our own value model.
3. **Provenance superscripts** turning honesty constraints into notation.
4. **Layout-dye blue** as the accent, with a machinist's justification rather than a mood.
5. **The zoomed-and-still-3px bar** — an argument that survives disclosing its own trick.
6. **UNKNOWN has no colour** — a stance about missing data that most products get wrong.

---

## 6. THE VETO MOMENT — section 08, in this direction's language

The comparator sweep *shows* the veto. Section 08 *explains* it. It must feel authoritative
rather than like an error.

### The core move: a certificate, not an alert

Error states use icons, triangles, exclamation marks, toast animation and the word "failed."
All of those say *something went wrong with the system*. A veto is the system working
perfectly. So the veto card is typeset as a **certificate of non-conformance** — a document
type that exists in real quality-assurance practice, that a refinery materials person has
held in their hand, and that carries authority precisely because it is boring.

```
+------------------------------------------------------------------+
|  CRITICAL ATTRIBUTE GATE                          RULE crit_gate  |
|  ================================================================ |
|  ATTRIBUTE        LENGTH                                          |
|  SOURCE VALUE     50.0 mm                          ▮  Point       |
|  CANDIDATE VALUE  75.0 mm                          ▮  Point       |
|  DIFFERENCE       25.0 mm                                         |
|  TOLERANCE        ± 0.5 mm                         ▭  Range       |
|  COMPARATOR       DISAGREE                                        |
|  ================================================================ |
|  GATE             CLOSED                                          |
|  SCORE            0.000        (gate x weighted score)            |
|  METHOD           deterministic · v1 · no model involvement       |
+------------------------------------------------------------------+
```

No icon. No colour except the OUT rule at the gate line. Every field labelled. Both values
carry units. The difference carries a unit. The tolerance carries a unit and renders as a
Range mark. The method line says `no model involvement` — which is the reassurance that
actually lands with this audience: *the thing that rejected your material was arithmetic,
not a neural network having an opinion.*

### What changes visually at the instant of veto

Six simultaneous changes, in this order within a 260ms window:

| # | change | why |
|---|---|---|
| 1 | Ground inverts PLATE → ZERO, wiping outward from the failing attribute | The failure has a location, and the page darkens *from* it. |
| 2 | The score is **replaced**, not decremented: `0.957` → `0.000` in one frame | A gate is discrete. A count-down would depict a weight and misrepresent the architecture. |
| 3 | The agreeing tie lines **retract** to zero from the axis outward | Undoing an earned connection is more forceful than fading it, and it is literally what `score = veto × (...)` does — the accumulated agreement is annulled, not subtracted from. |
| 4 | The candidate's marks switch DYE → OUT with no transition | Instant, because the comparator result is instant. |
| 5 | **The tolerance band does not move.** It stays lit, same position, same width | The standard does not move when a part fails. This is the authority. |
| 6 | Weight increases, size does not | The veto line is set in mono 500 rather than mono 400 — one weight step. It never scales up. Things that shout are errors; things that hold their size and gain weight are rulings. |

### The one thing the veto must never do

It must never suggest the candidate is *bad*. `SS HEX BOLT M10 X 75` is a perfectly good
bolt. It is simply a **different** material. The copy says DISTINCT, never REJECTED, never
FAILED, never INVALID. The section head is:

> **A different bolt is not a worse bolt. It is a different bolt.**

That sentence is also the whole product's ethics in one line, and it is the sentence I would
most want a CPCL materials manager to remember.

---

## 7. WHY EACH ANIMATION EXISTS

### Kept

| # | animation | what it communicates | what is lost if cut |
|---|---|---|---|
| 1 | Hero datum line draw, 420ms | The page has a zero and it is established before content | The datum reads as a decorative divider rather than a reference; the whole registration system loses its origin story |
| 2 | Hero tick stamp, staggered behind the datum | A line becomes a **scale**; the instrument graduates itself | Ticks read as texture instead of graduation; the causal relationship between axis and ticks is never taught |
| 3 | Hero H1 line-mask reveal, 3 lines, 90ms stagger | Nothing semantic — this one is **polish**, and it earns its place because it is the highest perceived-quality-per-config gesture available and it costs one property | Page reads as unfinished on first impression. Honest assessment: this is the one kept animation that communicates no information, and it stays only because first impressions are a real currency with judges. If build time is short, cut this before anything else. |
| 4 | Hero numeral **settle** (count with damped approach), 640ms | Readouts settle. This is the gesture that most establishes "instrument" | The panel becomes a static table; the equipment metaphor loses its only piece of behavioural evidence in the first viewport |
| 5 | Scroll `%` readout tracking continuously | Position in a long page; a shared vocabulary for a judge to reference a moment | The visitor has no progress feedback in a page with a 280vh pin — a genuine usability failure, not a stylistic one |
| 6 | **The comparator sweep** (the single scrub, 280vh) | The entire thesis: similarity fails to separate at 3px, measurement separates at a quarter-screen, the gate zeroes rather than reduces | The product's central claim becomes a paragraph. The 0.960/0.957 contrast has an inherent order and cannot be made statically. |
| 7 | Veto ground inversion, 260ms `power2.inOut` | A gate closing — a symmetric, bounded event with a location | Veto reads as a colour change rather than a state change |
| 8 | Tie-line **retraction** at veto | Accumulated agreement is annulled, not subtracted — the multiply-by-zero, visualised | The gate-vs-weight distinction, which is our core architectural claim, has no visual form |
| 9 | Verdict slug stamp, scale 0.94→1.00, 180ms, 80ms stagger | Discrete adjudication; three separate rulings, not one blended result | Verdicts appear all at once and read as a rendered table rather than as decisions |
| 10 | Section reveals: line-masked, y+, `power2.out`, `play none none reverse` | Reading order and section boundaries | Sections arrive flat; the eye loses the entry point. Cheap, reversible, uniform — nine of these, and they are all the same tween. |
| 11 | Hover on any value mark → its notation label appears in the rail | Teaches the four-mark grammar on demand | The notation must be learned from a legend alone. Keyboard focus does the same thing — this is not hover-only. |

### Cut, with reasons

| cut | why |
|---|---|
| Bobbing scroll arrow | Communicates "scroll" and nothing else. Replaced by the `%` readout, which communicates "scroll" **and** position **and** register. Strictly dominated. |
| Section background parallax | Communicates nothing. Costs continuous paint. Fights the registration rule, since a parallaxing block cannot align to a tick. |
| Magnetic / tilting buttons and cards | Communicate nothing, reduce pointer accuracy, and are the exact gesture that would make a materials manager decide this is a design exercise. |
| **Counting the vetoed score down from 0.957 to 0.000** | Actively misleading. It would depict a weight. Our architecture is a gate. Cut on correctness grounds, not taste. |
| Animated variable-font width on the H1 | Continuous reflow, guaranteed jank next to a pinned scrub, and it would make the type look like it is breathing — an organic quality that fights precision. Widths are static per breakpoint. |
| A dial or needle sweeping to the confidence value | Would imply a calibrated continuous reading. Confidence is an uncalibrated rank. This animation would break honesty constraint 4. Cut for honesty. |
| Marquee / ticker of CPSE logos or names | We have no CPSE data and no CPSE partners. It would fabricate relationships. Cut for honesty. |
| Count-up on every statistic across the page | Count-ups appear exactly twice: the hero readout and the thesis scores. Repeated everywhere they become wallpaper and the settle stops meaning anything. |
| Any `@keyframes`, `clip-path`, `mask`, `mix-blend-mode` decoration | Not needed. All motion is JS-driven and therefore reversible, scrubable and disableable from one place — which is what makes the reduced-motion branch tractable. |
| Loading skeleton shimmer | The demo is local and precomputed. If a shimmer is ever visible, the real bug is latency. Loading states render the four value marks in their Unknown form — a gap — which is honest and on-system. |

---

## 8. HONEST WEAKNESSES

I am arguing against my own direction here, because a direction that cannot name its own
failure modes has not been thought through.

**1. It demands unit-bearing copy for roughly forty micro-labels, and one wrong unit kills
the whole premise.** This direction's authority rests entirely on every figure being
correct, unit-carrying and method-tagged. A poster that is vague can be slightly wrong and
survive. An instrument that is wrong is worthless. If `p95 17 ms` appears next to `p50 13
ms` with the labels swapped, or a tolerance is written as `0.5mm` in one place and `0.50 mm`
in another, a materials manager notices in under a second and every other claim on the page
becomes suspect. **This direction has a lower error tolerance than any alternative.** It
needs a copy freeze and a units audit as an actual scheduled task, not an afterthought.

**2. The thesis SVG must be a real coordinate system, and that is 1.5–2 days of build on its
own.** The mm axis, the four stations, the markers and the tolerance band have to be
authored from one numeric mapping where 50 mm and 75 mm are *actually* at the right
positions. Eyeballed geometry will read as fine to a designer and as wrong to a refinery
engineer, who will glance at the axis, see that the 75 marker is not where 75 should be, and
stop trusting the page. This is the single highest-risk item on the schedule and it cannot
be parallelised or faked.

**3. The reduced-motion path is expensive here, not cheap.** For most directions,
reduced-motion means "render final states." Ours cannot, because the pinned section's
meaning *is* its sequence — a single final frame would show a verdict without showing why
the similarity view failed first. So the fallback is five separate captioned figures, which
is effectively a second design and a second build of the most complex section on the page.
I estimate the reduced-motion branch at 30–35% of the pinned section's total cost. It is
non-negotiable and it is not free, and any schedule that treats it as a checkbox will ship
it broken.

**4. Mobile genuinely degrades the thesis, and I will not pretend otherwise.** The four
horizontal stations and the 90 mm axis do not fit 375px. Rotating the axis to vertical turns
the `Δ 25.0 mm` read from a horizontal distance (which the eye compares instantly) into a
vertical one (which it compares less well), and stacking the four stations as rows destroys
the "one gap in a row of ties" moment at 65% — the gap becomes just another row. My honest
recommendation is that mobile drops the scrub entirely and uses the five-figure stepped
sequence with tap-to-advance, i.e. the reduced-motion build with a next button. **That means
the mobile experience is measurably weaker than desktop.** Acceptable only because judging
happens on a laptop; unacceptable if the page is expected to travel by phone link
afterwards, which it probably is.

**5. The register risks reading as bloodless.** "One Nation – One Material Code" is an
emotional line about national capability, and this direction answers it with a metrology
traceability chain rather than a flag. That is the *right* answer for a technical panel and
possibly the wrong one for a political one. If the judging panel skews toward officials who
want to feel national ambition, a warmer, more monumental direction beats this one on the
day. My defence is that the traceability argument *is* the national argument — one reference
standard, every CPSE code traceable to it — but it is an argument that has to be read, not
felt, and reading takes longer than three seconds.

**6. DYE `#12386B` is one bad execution away from looking like a bank.** Deep navy plus grey
plus off-white plus mono labels is also the palette of every fintech dashboard. What
separates us is density: the tick registration, the four value marks, and the provenance
superscripts. If those get diluted during build — if someone "cleans up" the ticks, or drops
the superscripts because they are fiddly — the direction collapses into generic corporate
minimalism and we will have spent our differentiation budget on nothing. The tick rail and
the superscripts are load-bearing and must be protected in review.

**7. Instrument fatigue is a real risk across eleven sections.** If the axis appears
everywhere it stops signifying. I have ruled it to four sections, but that rule will be
under constant pressure during build because the axis is the most attractive thing in the
system and every section will want one. Discipline required, and it is the kind of
discipline that erodes at 2 a.m.

**8. Archivo Expanded at 132px caps needs manual optical tracking per breakpoint.** Variable
grotesques at display size loosen visibly without per-size tracking correction. Budget an
hour for it, and know that if it is skipped the hero will read as slightly amateur to
exactly the design-literate subset of judges we are otherwise not designing for.

---

## APPENDIX — motion budget, enforced

    SCRUBBED / SCROLL-COUPLED     1   (the comparator sweep, 280vh)
    DISCRETE REVEALS              ~11 (all identical: line mask, y+, power2.out,
                                       play none none reverse)
    HOVER / FOCUS STATES          2   (value-mark notation label; nav link underline)
    STATE TRANSITIONS             4   (veto inversion, verdict stamp, tie draw,
                                       tie retract)
    LOADING STATES                1   (Unknown-gap marks, no shimmer)
    EASING FAMILIES               1   (power2; a single power2.inOut at the veto)
    ENTRY DIRECTIONS              1   (from below, always)
    KEYFRAMES / CLIP-PATH / BLEND 0
    NETWORK REQUESTS AT RUNTIME   0
