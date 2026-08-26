# Forensic teardown — patternbreak.ing

Investigated 2026-08-26. Reference material for the SIH26099 landing page.
**Nothing here is to be copied.** No branding, copy, illustrations, assets or visual
identity. What we extract are techniques and principles.

## Evidence labels

- **[V] VERIFIED** — read directly from source, live DOM, computed style, or a live
  library instance in the page.
- **[SI] STRONGLY INFERRED** — not directly readable, supported by several observations.
- **[VI] VISUAL INFERENCE** — from rendered behaviour only.
- **[X] UNVERIFIABLE** — could not be determined from public access.

## Access note

`patternbreak.ing` sits behind Cloudflare with `cf-mitigated: challenge`. `curl` receives
a 403 interstitial. **I did not attempt to defeat that challenge** — bypassing bot
protection is off-limits regardless of intent. Everything below was obtained by loading
the page in a real browser and reading the live document, which is ordinary visiting.
Consequence: no raw-HTML diffing and no source-map archaeology; the DOM read is
post-hydration, so server-rendered vs client-rendered markup cannot be separated. [X]

---

# 01 · Executive summary

A single-page, black-first scrollytelling essay about deceptive patterns in ultra-fast
fashion. Roughly **20,474 px tall at 1440×900** [V]. Built in **Webstudio** and shipped
as a **Remix** app [V], with **all motion hand-written in a 21 KB inline GSAP script** —
not by the visual builder [V].

The defining move is the **hero light→dark inversion**: the first viewport is pinned for
120% of viewport height while scroll progress drives a simultaneous background-colour
interpolation, a paired image crossfade, and a headline swap. The page literally turns
the lights off on you before the argument starts. Everything after is a comparatively
conventional stack of reveal-on-enter sections.

Three things are worth stealing. The **pinned tonal inversion** as a thesis statement.
The **paired light/dark asset crossfade** instead of filters. And the **`mask: "lines"`
SplitText reveal**, which is one line of config and carries most of the perceived polish.

Three things are worth *not* stealing: the accessibility model (35 `<h1>`, zero
`<h2>`, all 47 images `alt=""`), the mobile WebGL handling (canvases stay 1440 px wide on
a 375 px viewport), and the 1-second blocking delay before any content animates.

---

# 02 · Technology stack

## Verified

| Layer | Finding | Evidence |
|---|---|---|
| **Site builder** | **Webstudio** | `<html data-ws-project="bbdbff41-be2e-4b3c-919a-a0b78b50441c" data-ws-last-published="2026-02-05T14:35:21.785Z">` [V] |
| **Framework** | **Remix** | `window.__remixContext` present; `/assets/entry.client-*.js`, `root-*.js`, `manifest-*.js`, `_index-*.js` modulepreloaded [V] |
| **Bundler** | Vite | Remix + hashed `assets/*.js` naming [SI] |
| **Animation** | **GSAP 3.13.0** | `cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js`; `gsap.version === "3.13.0"` [V] |
| | **ScrollTrigger 3.13.0** | script tag + `ScrollTrigger.getAll()` returns 10 live instances [V] |
| | **SplitText 3.13.0** | script tag + 85 `.line` elements in the DOM at rest [V] |
| **Smooth scroll** | **Lenis 1.3.11** | `unpkg.com/lenis@1.3.11/dist/lenis.min.js`; `new Lenis({autoRaf:true})` in source [V] |
| **WebGL** | **UnicornStudio 2.0.4 + 2.0.2** | 3 script tags, 2 `<canvas>`, `data-us-project` IDs [V] |
| **Counter widget** | `drevo.b-cdn.net/.../counting-to-v1.0.js` | third-party module [V] |
| **Analytics** | **Cabin** (`scripts.withcabin.com/hello.js`) | privacy-focused, cookieless [V] |
| **CDN / WAF** | Cloudflare | `server: cloudflare`, `cf-ray` [V] |
| **Attribution** | "Made by Driftime®" in footer | [V] |

## Verified absent

No React on the page surface, no Vue, no Svelte, no Three.js global, no Lottie, no Rive,
no jQuery, no Webflow runtime, no Framer [V — probed `window` for each]. No `<video>`
elements at all [V]. **Zero `@keyframes` in the stylesheet** [V] — CSS contributes no
animation whatsoever.

The third-party claim that this is Webstudio is **confirmed**, and the `data-ws-*`
attributes are unambiguous.

## Notable defects

1. **UnicornStudio is loaded three times** — twice at v2.0.4, once at v2.0.2 [V].
   Two full copies of a WebGL runtime plus a version conflict.
2. **15 `<link rel="preload" as="image">` tags with empty `href`** [V]. They fetch
   nothing and cost a console warning each. Build artefact.
3. **Fonts ship as `.woff`, not `.woff2`** [V] — roughly 30% larger for no reason.

---

# 03 · Page architecture

Measured at 1440×900, scroll top [V]. Section tops are absolute document offsets.

| # | Top px | Height | Background | Content |
|---:|---:|---:|---|---|
| 00 | 0 | 1229 | `#F8F9F6` → `#000` | **Hero** — pinned, tonal inversion |
| 01 | 1229 | 1024 | `#000` | "Online / Deceptive / Shopping / Patterns" — 16 images |
| 02 | 2253 | 1235 | inherit black | "Attention deficit" |
| 03 | 3488 | 1440 | inherit black | "…clothes we throw away has doubled" — 5 images |
| 04 | 4928 | 1702 | **`#CA9FFF`** | Garbage-truck statistic — **1 WebGL canvas** |
| 05 | 6734 | 1168 | black | Fast vs ultra-fast fashion argument |
| 06 | 7902 | 1184 | black | Atacama satellite imagery — 3 images |
| 07 | 9086 | 2048 | black | Deceptive-pattern specimens — **12 SVGs** |
| 08 | 11134 | 1232 | black | "4×" statistic block |
| 09 | 12366 | 1184 | black | "deceptive pattern characteristics" — card stack |
| 10 | 13550 | 1024 | **`#F8F9F6`** | "LOOKING AHEAD" — **tonal flip back to light** |
| 11 | 14574 | 1024 | `#F8F9F6` | Light continuation |
| 12 | 15598 | 1024 | `#F8F9F6` | "Progress is being made" |
| 13 | 16622 | 2636 | `#F8F9F6` | "What can be done" — 9 images, 15 SVGs |
| 14 | 19258 | 1216 | black | **CTA / footer** — 1 WebGL canvas |

**The macro-structure is a tonal three-act**: light hero → long black middle (the
problem) → light resolution → black close. Colour carries the argument, not decoration.

Totals: 47 `<img>`, 31 `<svg>`, 2 `<canvas>`, 0 `<video>`, 25 links, 11 buttons [V].

---

# 04 · DOM / HTML structure

Webstudio emits **atomic hashed classes** on every element: `w-box c1jy6eh c4rc2a0
c16f186c c1islxtd c13zmog1` [V]. Each `cXXXXX` is one generated rule. `w-box` /
`w-element` are the framework primitives.

Alongside them are **hand-authored semantic classes** the inline script targets:
`.hero-section`, `.hero-image-light`, `.hero-image-dark`, `.hero-header-light`,
`.hero-header-dark`, `.dither-light`, `.dither-dark`, `.main-nav`, `.section`,
`.section-heading`, `.burn-badge`, `.stack-card`, `.button`, `.preloader`,
`.preloader-column`, `#tagsSlider`, `#prevBtn`, `#nextBtn`, `[data-tag]`,
`[hoverstagger="text"]` [V].

**This dual-class system is the key structural lesson.** The builder owns layout; a
hand-written class layer owns behaviour. The two never collide, and the animation script
is readable because it targets intent (`.hero-image-dark`) rather than generated hashes.

Landmarks: `<main>` ×1, `<section>` ×14, **`<nav>` ×0, `<header>` ×0, `<footer>` ×0** [V].

---

# 05 · CSS architecture

Single stylesheet, `/assets/index-Dbal2D25.css`, **44,163 bytes** [V].

| Feature | Count |
|---|---:|
| Custom properties declared | **524** |
| `clamp()` | 24 |
| `vw` units | 53 |
| `@media` blocks | **4** |
| `display:grid` | 3 |
| `display:flex` | 2 |
| `position:sticky` | 1 |
| `position:fixed` | 1 |
| `transition` | 8 |
| `transform` | 5 |
| **`@keyframes`** | **0** |
| **`clip-path`** | **0** |
| **`mask`** | **0** |
| **`mix-blend-mode`** | **0** |
| **`will-change`** | **0** |

The custom-property names — `--size-1..15`, `--size-px-*`, `--font-size-0..8`,
`--font-size-fluid-0..3`, `--font-lineheight-00..5`, `--font-letterspacing-0..7` — are
**Open Props** [V], which Webstudio ships by default.

Two conclusions. **All motion is JavaScript** — zero keyframes. And the masked line
reveals are **not** CSS masks; SplitText generates the wrapper elements at runtime.

Breakpoints: `max-width: 991px`, `767px`, `479px` [V] — the classic Webflow set,
inherited by Webstudio.

---

# 06 · Typography

## Faces [V]

| Family | Weights | Format | `font-display` |
|---|---|---|---|
| **Neue Montreal** | 400, 500, 700 | `.woff` | `swap` |
| **IBM Plex Mono** | 500 | `.woff` | `swap` |

All four preloaded via `<link rel="preload" as="font">` [V]. The whole system runs on
**two families** — a neo-grotesque for everything editorial, a mono for every label,
caption, tag and datum. That binary is the entire typographic idea.

## Measured scale @1440 [V]

| Role | Font | Weight | Size | Line-height | Transform |
|---|---|---:|---:|---:|---|
| Giant statistic | Neue Montreal | 500 | **160 px** | 128 px (0.80) | uppercase |
| Section display | Neue Montreal | 500 | 64 px | 89.6 px (1.40) | none |
| Hero words | Neue Montreal | **700** | 60.8 px | 60.8 px (**1.00**) | uppercase |
| Body-large / narrative | Neue Montreal | 500 | 32 px | 38.4 px (1.20) | none |
| Card heading | Neue Montreal | 500 | 24 px | 28.8 px (1.20) | none |
| Logotype | Neue Montreal | 700 | 22.4 px | 20.16 px (0.90) | uppercase |
| Body | Neue Montreal | 400 | 16 px | 22.4 px (1.40) | none |
| **Mono label** | IBM Plex Mono | 400 | 16 px | 22.4 px | **uppercase** |
| Caption | Neue Montreal | 400/500 | 12 px | 16.8 px (1.40) | none |
| **Mono micro-label** | IBM Plex Mono | 400 | **12 px** | 16.8 px | **uppercase** |

Line-height tightens as size grows — **1.40 at body, 1.20 at 32 px, 1.00 at hero,
0.80 at 160 px** [V]. That single ratio curve is most of why the display type reads as
designed rather than merely large.

`letter-spacing` is `normal` everywhere measured [V]. No optical tracking compensation —
arguably a miss at 160 px.

## Mobile @375 [V]

Hero words stay at **60.8 px** — no downscale. Section headings go **32 px → 33.75 px**,
i.e. very slightly *larger*, consistent with a `clamp()` whose `vw` term is still rising
at 375 px. Body stays 16 px.

**Assessment:** the fluid system is doing very little work. The hero survives because the
words are short ("Online", "Shopping"). A longer word would overflow. For SIH26099, where
strings like "Harmonization" are unavoidable, we need a genuinely fluid hero scale.

---

# 07 · Colour system

Extracted from computed styles across every element [V]:

| Hex | RGB | Uses | Role |
|---|---|---:|---|
| **`#FDFF6D`** | 253,255,109 | 29 | **Acid yellow** — most-used background; alert/urgency badges |
| **`#CA9FFF`** | 202,159,255 | 26 | **Lavender** — section 04 ground + accents |
| `#000000` | 0,0,0 | 14 | Dark ground |
| **`#F8F9F6`** | 248,249,246 | 12 | **Bone** — light ground |
| `#FFFFFF` | 255,255,255 | 5 + 473 text | White |
| `#030507` | 3,5,7 | 1 + 491 text | **Near-black ink** (not pure black) |
| `#26291E` | 38,41,30 | 2 | Dark olive |
| `#D9D9D9` | 217,217,217 | 5 | Grey — secondary captions |
| `rgba(255,255,255,.1)` | — | 9 | Hairline borders on dark |
| `rgba(16,16,16,.3)` | — | 4 | Scrim |

Two disciplined choices worth copying:

1. **Text ink is `#030507`, not `#000`, while grounds *are* pure black.** Ink slightly
   lifted off black reads softer on light grounds; the ground going fully black makes the
   inversion feel absolute. The asymmetry is deliberate.
2. **Exactly two chromatic accents**, both high-value, both used as *fills* behind
   near-black text rather than as text colour. Acid yellow and lavender are the
   vocabulary of the thing being criticised — sale badges and app UI — which is why the
   palette feels editorial rather than arbitrary.

No gradients, no blend modes, no filters [V].

---

# 08 · Grid and layout

- Inner container **`max-width: 1200px`**, centred [V].
- Section vertical rhythm: **`padding: 80px 0`** [V], consistent across sections.
- One measured section uses **`gap: 120px`** between major blocks [V].
- Sections are **`display:flex; flex-direction:column; align-items:center;
  justify-content:center`** [V].
- Real CSS Grid appears **twice**: one 10-column track of `28px 28px …` with `gap: 0`
  (a fixed micro-grid, likely a dither or tick strip) [V].

**So there is no 12-column grid.** The layout is centred flex columns with a 1200 px cap
and absolute positioning for the scattered hero specimens. For an editorial page this is
sufficient and much simpler than a grid system. Mobile: containers go full-bleed 375 px,
`max-width` never engages [V].

---

# 09 · Assets

All media is served through a **`/cgi/image/` transform endpoint** with query params
`?width=640&quality=80&format=auto` and `srcset` for widths [V].

- **47 images, all with `srcset`** [V] — genuinely responsive.
- **32 lazy / 15 eager** [V] — eager set is the hero.
- `format=auto` implies WebP/AVIF negotiation [SI].
- Mixed types behind one endpoint: `.png`, `.svg`, and **`.gif`** (`Phone_(12)….gif`,
  437×437 — an animated phone mock) [V].
- `object-fit` observed: `contain` for specimens, `fill` for the dither strips [V].

The **light/dark asset pairing** is the notable pattern: `dither-light` / `dither-dark`,
`discount-light` / `discount-dark`, `hero-image-light` / `hero-image-dark` [V]. Two
separately authored artworks per element, crossfaded — **not** a CSS filter inversion.
More bytes, far better control, and the dark variants are genuinely redrawn.

---

# 10 · SVG

31 inline `<svg>` [V], concentrated in section 07 (12) and section 13 (15). Used as
**iconography and diagram content**, not as animation targets: no `stroke-dasharray`
animation, no path morphing, no SMIL, and no CSS keyframes exist to drive them [V].
Some "SVGs" are served as `<img src="….svg">` through the image endpoint [V], so they are
opaque to CSS styling.

---

# 11 · Animation system

All of it lives in **one 20,965-character inline `<script>`** [V], plus a 7,294-character
second script for the card stack. Structure:

```js
gsap.registerPlugin(SplitText, ScrollTrigger);
document.fonts.ready.then(() => {
  /* preloader — runs immediately */
  gsap.delayedCall(1, () => {
    /* Lenis + intro timeline + hover systems + slider */
    gsap.delayedCall(2, () => { /* ScrollTriggers */ });
  });
});
```

**`document.fonts.ready` gating** [V] is correct and worth copying — SplitText measures
line boxes, and splitting before webfonts land produces wrong line breaks.

The **nested `delayedCall(1)` then `delayedCall(2)`** is not [V]. It hard-codes a
**3-second wait before ScrollTriggers exist**. A fast scroller reaches section 2 before
its animations are registered. The comment says "DELAYED to avoid conflicts", which is a
race condition papered over with a timer.

## Verified parameters

| Effect | Parameters |
|---|---|
| Preloader columns | `scaleY: 1→0`, `transformOrigin: "top center"`, `duration: 0.7`, `ease: power2.inOut`, `stagger: {amount: 0.8, from: "start"}`, `delay: 0.3`, then `display:none` |
| Hero section in | `opacity → 1`, `duration: 0.6`, `power2.out` |
| Hero specimens in | `opacity 0→1`, `y: 50→0`, `duration: 0.8`, `stagger: 0.15`, `power2.out`, offset `-=0.3` |
| Dither in | `duration: 0.6`, `power2.out`, offset `-=0.5` |
| Hero headline | SplitText `{type:"lines", linesClass:"line", mask:"lines"}`; `y:100→0`, `autoAlpha:0→1`, `stagger: 0.15`, `duration: 0.8`, `power2.out` |
| Section headings | same split; `stagger: 0.05`, `start: "top 80%"`, `toggleActions: "play none none reverse"` |
| Main nav | `gsap.set(y:"100%", autoAlpha:0)` → `y:"0%"` on `.hero-section start:"bottom top"`, `duration: 0.8` |

`ease: "power2.out"` / `"power2.inOut"` appears **33 times** [V]. There is exactly one
easing idea in the whole site.

---

# 12 · Scroll system

**Lenis drives everything** [V]:

```js
const lenis = new Lenis({ autoRaf: true });
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.lagSmoothing(0);
```

`lagSmoothing(0)` disables GSAP's frame-drop compensation so scrub stays locked to scroll
position rather than wall-clock [V]. Correct for scrubbed animation.

## The hero pin — the one scrubbed animation

```js
scrollTrigger: {
  trigger: ".hero-section",
  start: "top top",
  end: "+=120%",
  scrub: 1,
  pin: true,
  anticipatePin: 1,
  refreshPriority: -1
}
```

Live instance confirms `start: -0.001, end: 860, pin: true` at a 720 px viewport
(860 ≈ 120% × 720) [V].

**Measured scrub states** — I stepped scroll and read computed styles [V]:

| scrollY | `.hero-section` bg | light img | dark img | light hdr `y` | position |
|---:|---|---:|---:|---:|---|
| 0 | `#F8F9F6` | 1.000 | 0.000 | 0 | `fixed` |
| 300 | `rgb(227,228,225)` | 0.957 | 0.043 | −0.21 px | `fixed` |
| 600 | `rgb(88,88,87)` | 0.322 | 0.679 | −18.17 px | `fixed` |
| 900 | `rgb(5,5,5)` | 0.002 | 0.998 | −25 px | `fixed` |
| 1200 | `#000000` | 0 | 1 | −25 px | `relative` |

This is the answer to the question the brief asks: **scroll progress continuously
controls animation progress** for the hero, and **only** for the hero. Every other
ScrollTrigger on the page is a discrete `toggleActions: "play none none reverse"` trigger
with no scrub [V — all 10 live instances inspected].

That is a deliberate and smart budget: **one scrubbed set-piece, everything else a
cheap reveal.** Scrubbed animation is expensive to tune and to run; spending it once,
on the thesis moment, is the right allocation.

## Live ScrollTrigger inventory [V]

| # | Trigger | Start px | End px | Pin | Scrub |
|---:|---|---:|---:|:-:|:-:|
| 1 | `.hero-section` | −0.001 | 860 | **yes** | **1** |
| 2–9 | section headings | 1100 / 1982 / 3074 / 4663 / 6452 / 9681 / 11580 / 12511 | +~800–1150 | no | no |
| 10 | `.hero-section` (nav) | 1576.99 | 1577.00 | no | no |

---

# 13 · Text animation

**Lines, never characters, for anything the reader reads** [V]:

```js
SplitText.create(".section-heading", { type: "lines", linesClass: "line", mask: "lines" })
```

85 `.line` elements exist in the DOM at rest; **0 `.char` elements** [V].

`mask: "lines"` is a GSAP 3.13 feature that wraps each line in an
`overflow:hidden` container automatically, so `y: 100 → 0` reads as type rising from
behind a hard edge. **One config property produces the entire effect.** No CSS masks, no
manual wrapper markup.

**Characters are used only on button hover** [V]:

```js
const split  = new SplitText(titleA, { type: "chars" });
const splitb = new SplitText(titleB, { type: "chars" });
tl.fromTo(split.chars,  { y: 0  }, { y: -20, duration: 0.5, stagger: 0.05 })
  .fromTo(splitb.chars, { y: 38 }, { y: -20, duration: 0.5, stagger: 0.05 }, "<");
```

Two stacked label copies rolling as one — a classic, and correctly limited to a
4–12 character target where per-char staggering costs nothing.

**The principle: split granularity should match reading intent.** Lines for prose,
characters for labels. Character-animating a paragraph is the most common way this
technique gets misused.

---

# 14 · Micro-interactions

## Specimen hover — light/dark swap [V]

```js
container.on('mouseenter'):
  [light, dark] → y: -4,        duration 0.3, power2.out   (t=0)
  light         → autoAlpha: 0, duration 0.25, power2.inOut (t=0.05)
  dark          → autoAlpha: 1, duration 0.25, power2.inOut (t=0.05)
```
Lift and invert together, with the crossfade lagging the lift by 50 ms. Guarded by an
`isHovering` flag and `hoverTl.kill()` so re-entry cannot stack timelines [V] — a detail
most implementations get wrong.

## Tag "gravity shake" [V]

Six chained rotations, `transformOrigin: "top center"`:
`+10° → −8° → +6° → −4° → +2° → 0°`, durations `0.4 / 0.5 / 0.5 / 0.5 / 0.5 / 0.6`.
A hand-authored damped oscillation. Suppressed on mobile and while dragging [V]. Source
comments show every value was reduced from a louder first pass (`12°→10°`, `−10°→−8°`)
— the restraint was iterated into it.

## Fire-emoji emitter [V]

`.burn-badge` hover spawns a `🔥` div every **100 ms** at the tracked cursor position,
±40 px jitter; each rises `−80 to −160 px` with ±15 px drift over 1.2 s and is removed on
complete. `setInterval` cleared on `mouseleave`.

Cheap, disposable DOM particles. Fine at one emitter; would need pooling at scale.

---

# 15 · Cards, statistics, data visualisation

## Card stack [V]

```js
const cardRotations = [-3, 2, -1.5, 1, -2];      // per-card, not per-position
scale    = 1 - stackIndex * 0.03
yOffset  = stackIndex * 8
zIndex   = total - stackIndex
opacity  = stackIndex < 4 ? 1 : 0                 // only 4 rendered
```

Each card keeps **its own** rotation regardless of stack position, so the deck looks
hand-shuffled rather than mechanically fanned [V]. Only four cards are ever visible.

The `goNext()` throw is a three-step timeline whose middle step is the trick [V]:

| Step | x | rotation | zIndex | dur |
|---|---:|---:|---:|---:|
| 1 slide out | 200 | base + 30° | **1000** | 0.2 |
| 2 pass behind | 250 | — | **−1** | 0.1 |
| 3 tuck back | 0 | base | 0 | 0.2 |

The z-index flips to −1 **while the card is still travelling**, so it visibly passes
*behind* the deck instead of teleporting. `transformOrigin: "80% 100%"` for right-throws,
`"20% 100%"` for left [V]. Content is swapped at +150 ms behind a 0.2 s opacity dip.

## Slider [V]

3 cards desktop / 1 mobile, breakpoint 768. Horizontal `wheel` (`deltaX > deltaY`),
touch with **0.3 rubber-band resistance** past bounds, 30 px swipe threshold,
`cursor: grab` desktop only.

## Statistics

The `137` figure renders at **160 px / 128 px line-height** [V]. Counters animate via the
third-party `counting-to-v1.0.js` module [V]; internals not inspected [X].

---

# 16 · Responsive behaviour

| | Desktop 1440 | Mobile 375 |
|---|---|---|
| Doc height | 20,474 px | 17,230 px |
| Hero words | 60.8 px | **60.8 px** (unchanged) |
| Section heading | 32 px | 33.75 px |
| Section padding | 80 px | 80 px |
| Container | 1200 px cap | full-bleed |
| Slider | 3 cards | 1 card |
| Tag shake | on | **suppressed** |
| Drag cursor | `grab` | none |

**Bug [V]:** both UnicornStudio canvases remain `style="width:1440px"` with backing
store 2160×1350 on a 375 px viewport. They do not resize. That is ~2.9 M pixels of WebGL
rendered off-screen on a phone.

Motion is reduced but not redesigned: the pinned hero scrub still runs on mobile [V].

---

# 17 · Performance

**Good:** `document.fonts.ready` gating; `srcset` on all 47 images with an auto-format
transform endpoint; 32/47 lazy; font preloads; `lagSmoothing(0)`; animation restricted to
`transform` / `opacity` / `backgroundColor` — no layout-triggering properties animated
[V]; a 44 KB stylesheet.

**Bad:**
1. UnicornStudio loaded **3×**, two versions [V].
2. Canvases at fixed 1440 px on mobile [V].
3. 15 empty `preload as=image` [V].
4. `.woff` not `.woff2` [V].
5. **3-second hard delay** before ScrollTriggers register [V].
6. `will-change` used **zero** times [V] — GSAP handles most of this, but the pinned
   hero would benefit.
7. Fire emitter creates unpooled DOM nodes at 10/s [V].

---

# 18 · Accessibility

The weakest area, and measured rather than assumed [V]:

| Check | Result |
|---|---|
| `<h1>` count | **35** |
| `<h2>` / `<h3>` | **0 / 0** |
| Images with meaningful `alt` | **0 of 47** |
| Images with `alt=""` | **47** |
| `<nav>` / `<header>` / `<footer>` | **0 / 0 / 0** |
| `<main>` | 1 |
| Buttons with no accessible name | 2 |
| `aria-*` / `role` attributes | 334 |
| `prefers-reduced-motion` in CSS | **none** |

35 `<h1>` with no `<h2>` is not a heading hierarchy — it is 35 top-level documents. Every
image is marked decorative, including the Atacama satellite imagery that carries the
argument. There is **no `prefers-reduced-motion` handling anywhere** [V], on a site whose
primary mechanic is a pinned scroll-scrubbed inversion.

The 334 `aria-*`/`role` attributes are largely Webstudio defaults plus
`role="img" aria-label="Unicorn Studio Scene"` on the canvases [V] — so the WebGL is
labelled while the photographs are not.

**For SIH26099 this is a hard fail state.** A government-facing platform must ship one
`<h1>`, a real heading tree, real alt text, landmarks, and a reduced-motion path.

---

# 19 · Animation inventory

| ID | Element | Trigger | Property | Dur | Ease | Scrubbed |
|---|---|---|---|---:|---|:-:|
| A01 | `.preloader-column` | load | `scaleY 1→0` | 0.7 | power2.inOut | no |
| A02 | `.hero-section` | +1 s | `opacity→1` | 0.6 | power2.out | no |
| A03 | `.hero-image-light` | intro | `opacity`, `y 50→0` | 0.8 | power2.out | no |
| A04 | `.dither-light` | intro | `opacity` | 0.6 | power2.out | no |
| A05 | `.hero-header-light` lines | intro | `y 100→0`, `autoAlpha` | 0.8 | power2.out | no |
| A06 | `.section` | intro | `opacity`, `y 30→0` | 0.8 | power2.out | no |
| **A07** | **hero bg** | **pin 0→120vh** | **`backgroundColor`** | — | power2.inOut | **yes** |
| **A08** | **light↔dark images** | **pin** | **`autoAlpha`** | — | power2.inOut | **yes** |
| **A09** | **light↔dark headers** | **pin** | **`autoAlpha`, `y→−25`** | — | power2.inOut | **yes** |
| A10 | `.main-nav` | hero bottom | `y 100%→0` | 0.8 | power2.out | no |
| A11 | `.section-heading` lines | top 80% | `y 100→0` | 0.8 | power2.out | no |
| A12 | specimen hover | mouseenter | `y −4`, crossfade | 0.3/0.25 | power2 | no |
| A13 | `.button` chars | hover | `y` roll | 0.5 | default | no |
| A14 | `[data-tag]` | hover | 6× `rotation` | 0.4–0.6 | power2 | no |
| A15 | fire emoji | hover | `y`, `scale`, `opacity` | 1.2 | power2.out | no |
| A16 | `.stack-card` | button | `x`, `rotation`, `zIndex` | 0.5 | power2 | no |
| A17 | `#tagsSlider` | wheel/touch | `x` | 0.4–0.6 | power2.inOut | no |

**Three scrubbed animations out of seventeen** — and all three are the same moment.

---

# 20 · Component inventory

```
Page
├── Preloader            (column wipe, one-shot)
├── HeroInversion        ← the only pinned, scrubbed component
│   ├── HeroWordmark     (light/dark pair)
│   ├── SpecimenCard[]   (light/dark pair, hover-swap, absolute)
│   └── DitherStrip      (light/dark pair)
├── MainNav              (hidden until hero exits)
├── NarrativeSection[]   (masked-line heading + prose)   ← the workhorse
├── StatBlock            (160px numeral + mono caption)
├── ImageStory           (full-bleed + mono attribution)
├── WebGLPanel           (UnicornStudio canvas)
├── TagSlider            (3/1 cards, wheel + touch)
├── CardStack            (5 cards, throw-to-back)
├── PatternSpecimen[]    (SVG deceptive-pattern examples)
└── CTA + Footer
```

Genuinely reusable: `NarrativeSection`, `StatBlock`, `SpecimenCard`, `ImageStory`.
One-offs: `HeroInversion`, `CardStack`, `TagSlider`, `Preloader`.

**Ratio worth noting: one spectacular one-off, four repeating workhorses.** The page feels
rich because the workhorse is well-made, not because everything is bespoke.

---

# 21 · Scroll storyboard

```
0–860px      HERO PINNED. Bone ground, black type, "ONLINE / SHOPPING"
             wrapping a hand holding a phone, surrounded by floating
             specimens — fake countdown, "SELLING FAST", cookie ACCEPT ALL,
             "POPULAR", review popup. It reads as an ordinary shopping page.
             ↓ scrub: ground drains bone → grey → black; every specimen
               crossfades to its dark twin; headline swaps beneath a mask.
             The lights go out on the reader. Same page, different meaning.

860–1229     Unpin. Nav rises from y:100%.

1229–2253    "Online / Deceptive / Shopping / Patterns" — the four words
             from the hero, now reordered into an accusation. 16 specimens.

2253–4928    "Attention deficit" → clothing-waste doubling. Masked-line
             reveals at top-80%. Pure black, prose-led, no set-piece.

4928–6734    LAVENDER BREAK (#CA9FFF). Garbage-truck statistic + WebGL.
             First colour interruption after 3700px of black — the palette
             is used as punctuation.

6734–9086    Fast vs ultra-fast argument → Atacama satellite imagery.

9086–12366   Specimen gallery (12 SVGs) → "4×" stat → card stack of six
             deceptive-pattern definitions.

13550        TONAL FLIP TO BONE. "LOOKING AHEAD".
             Light returns = the argument turns constructive.

13550–19258  Regulation, progress, "What can be done". 9 images, 15 SVGs.

19258–20474  Black CTA + WebGL close. Returns to the hero's end state.
```

**The structural idea: the hero's inversion is a promise, and the section-10 flip back to
light is its resolution.** Colour is the narrative spine.

---

# 22 · Design tokens

```
COLOUR
  ground.light   #F8F9F6      ground.dark    #000000
  ink.dark       #030507      ink.light      #FFFFFF
  ink.muted      #D9D9D9      olive          #26291E
  accent.acid    #FDFF6D      accent.lilac   #CA9FFF
  hairline       rgba(255,255,255,0.10)
  scrim          rgba(16,16,16,0.30)

TYPE
  display   Neue Montreal 700 · uppercase · lh 1.00
  headline  Neue Montreal 500 · lh 1.20–1.40
  body      Neue Montreal 400 · 16/22.4 (1.40)
  label     IBM Plex Mono 400/500 · 12–16 · uppercase
  scale     12 · 16 · 22.4 · 24 · 32 · 60.8 · 64 · 160
  lh curve  1.40 → 1.20 → 1.00 → 0.80 as size rises

SPACE
  section-y 80px      block-gap 120px      container 1200px

MOTION
  ease.default  power2.out
  ease.inout    power2.inOut
  dur.fast 0.25 · dur.base 0.5 · dur.slow 0.8 · dur.pre 0.7
  stagger.tight 0.02 · .line 0.05 · .hero 0.15
  scrub 1 · pin-length 120vh · reveal-start "top 80%"

BREAKPOINTS  991 · 767 · 479   (mobile logic threshold 768)
Z-INDEX      preloader 99999 · sticky 99 · nav 10 · card-throw 1000/−1
```

---

# 23 · Motion language

**Subtle, unidirectional, damped, and almost monotonous by choice.**

- **One easing family.** `power2` appears 33 times; nothing elastic, nothing bouncy.
- **One direction.** Content enters from below (`y: 100`, `y: 50`, `y: 30`), never from
  the sides. Reading direction is respected.
- **Opacity + transform only.** No layout properties animated anywhere.
- **Physical connection is rationed.** Exactly one scrubbed set-piece. Everything else
  fires and completes on its own clock, so the page does not feel gimmicky.
- **Reversibility.** `toggleActions: "play none none reverse"` everywhere — scrolling up
  un-reveals. The page has no "used up" state.
- **Deliberate friction exists in one place only:** the 120 vh pin. The reader must push
  through it, and that resistance *is* the message.

The one aggressive gesture — the tag shake — was demonstrably toned down during
development, and is disabled on touch [V].

---

# 24 · Information architecture

Cognitive load is managed by **withholding the thesis**. The first viewport is disguised
as the thing being criticised: a normal shopping page with normal manipulative furniture.
The reader is placed inside the problem before being told there is one.

Sequence: **recognition** (hero) → **naming** (Online/Deceptive/Shopping/Patterns) →
**scale** (waste statistics) → **mechanism** (fast vs ultra-fast) → **evidence**
(Atacama, specimen gallery) → **taxonomy** (six named patterns) → **resolution**
(regulation, light ground) → **action** (CTA).

Statistics arrive *after* the emotional setup, not before. The CTA appears only at
20,474 px, after the full argument. This is an essay, not a landing page — **confirmed
against the actual section structure**, not assumed.

---

# 25 · Implementation blueprint for SIH26099

Original stack: Webstudio + Remix + GSAP + Lenis + UnicornStudio.
**Ours should be React/Vite + GSAP + Lenis.** We already chose Vite over Next in Phase 0
and nothing here changes that.

## Adopt

1. **One pinned scrubbed set-piece, everything else discrete reveals.** For us the
   inversion is thematically perfect: open on **fragmented material identity** — the same
   bolt described five different ways across five CPSE cards — then scrub to reveal them
   collapsing into one canonical NMC identity. Same mechanic, our meaning.
2. **`SplitText {type:"lines", mask:"lines"}`** at `start:"top 80%"`,
   `toggleActions:"play none none reverse"`, `stagger 0.05`. Highest polish-per-line
   of anything on that site.
3. **Two-family type system** — one grotesque, one mono. Mono for material codes,
   attribute names, confidences and provenance labels. This is not decorative for us:
   `MAT-78291` and `M10 × 50` genuinely need tabular mono.
4. **The line-height curve** — 1.4 body → 1.2 mid → 1.0 display.
5. **Lenis + `lagSmoothing(0)` + `lenis.on('scroll', ScrollTrigger.update)`.**
6. **`document.fonts.ready`** before any split.
7. **Paired light/dark assets** rather than filter inversion, if we invert anything.
8. **Dual class system** — layout classes from our component library, separate semantic
   hooks (`.veto-row`, `.evidence-table`) for GSAP. Never animate a utility class.

## Reject

1. **The 3-second `delayedCall` chain.** Register ScrollTriggers immediately after
   `fonts.ready`; use `ScrollTrigger.refresh()` and `refreshPriority`, not timers.
2. **The accessibility model, entirely.** One `<h1>`, real `<h2>`/`<h3>`, real alt text,
   `<nav>`/`<header>`/`<footer>`, and a genuine `prefers-reduced-motion` branch that
   disables the pin and renders final states.
3. **Fixed-size WebGL canvases.** If we use any, they resize with a `ResizeObserver`.
4. **Loading a runtime three times.**
5. **UnicornStudio.** A third-party WebGL SaaS with project IDs is an external dependency
   and a network call. Our demo runs airplane-mode — that is a Phase 0 hard constraint.
   Any ambient graphic must be local canvas or SVG.
6. **`.woff`.** Ship `.woff2`.

## Constraint that overrides all of it

Phase 0 fixed the demo topology: **localhost, Wi-Fi off, zero external requests.** So no
jsDelivr, no unpkg, no CDN fonts, no analytics. GSAP, Lenis and fonts get bundled and
self-hosted. Verify in devtools airplane mode: **zero requests to any non-localhost
host.** A landing page that needs the network is a landing page that fails on stage.

---

# 26 · Verified vs inferred

**Verified** — builder and framework identity; every library and version; all font faces,
weights, formats and `font-display`; the complete measured type scale at two viewports;
every colour value and its usage count; container width, section padding, block gap;
all CSS feature counts including the zeros; all 10 live ScrollTrigger configs with pixel
start/end; the full hero scrub state table at five scroll positions; every animation
parameter quoted from source; SplitText config and `.line`/`.char` counts; card-stack
maths; slider behaviour; all accessibility counts; image loading strategy; the
three defects.

**Strongly inferred** — Vite as bundler; WebP/AVIF negotiation from `format=auto`;
Open Props as the token source (naming is conclusive, the import is not visible).

**Visual inference** — the hero's narrative intent; the psychological reading of the
tonal three-act.

# 27 · Not determinable from public access

- Server-rendered vs client-rendered markup split (DOM read post-hydration) [X].
- Webstudio project source, component tree, or CMS bindings [X].
- Source maps — not checked for the Remix bundles; `index-*.css` and `assets/*.js` may
  have them [X].
- `counting-to-v1.0.js` internals [X].
- UnicornStudio scene definitions — server-side under project IDs
  `Xcj72Hg0NkN659wmJX8J` and `KQ3n2rdnHAj9pjBF12Nt` [X].
- Real-device performance, CLS, INP [X].
- Whether `prefers-reduced-motion` is handled in JS rather than CSS — no CSS branch
  exists, and I did not emulate the media feature [X].
- Raw pre-hydration HTML — Cloudflare challenge blocks non-browser fetch, and I did not
  attempt to defeat it [X].
