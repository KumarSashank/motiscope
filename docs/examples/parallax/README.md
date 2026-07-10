# Parallax landscape — recreated with motiscope

**Live page:** [kumarsashank.github.io/motiscope/examples/parallax/](https://kumarsashank.github.io/motiscope/examples/parallax/)

A scroll-driven parallax hero — sky, far hills, mid hills, deep hills, a viaduct with a
**train crossing it**, and a near-black foreground of trees, bushes and tulips. Recreated
from a **2.25s screen recording**. Traced terrain, measured speeds, **new palette**.

![scrolling the recreation: the layers separate by depth and the train crosses the viaduct](scroll.gif)

*Every frame rendered at a fixed scroll offset — this is the page itself, scrolled. Full
video: [`scroll.mp4`](scroll.mp4).*

- **Original:** a parallax landing page from SVGator's
  [website animation examples](https://www.svgator.com/blog/website-animation-examples-and-effects/)
  — all credit to the original creator.
- **Recreation:** [`index.html`](index.html) — one self-contained file. Traced SVG ridgelines,
  ~20 lines of JavaScript, no dependencies, `prefers-reduced-motion` honoured.
- **Terrain data:** [`ridges.json`](ridges.json) — one `y` per column, per layer.
- **Build script:** [`generate.py`](generate.py).

## Two clocks in one recording

A parallax is **scroll-driven**. The timing motiscope reports for this clip — a 0.77s hold,
then 1.45s of motion — describes *the person who did the scrolling*, not the design. Replay
those seconds and you recreate the recording, not the website.

The **train, in the source, is time-driven**: it runs on a clock at a speed that survives
however fast you happened to scroll. So one clip carries two different kinds of number:

| Quantity | Kind | Recoverable? |
|---|---|---|
| Layer speed **ratios** | scroll-intrinsic | yes, for four of six layers |
| Train speed | time-intrinsic | yes — **1501 px/s** |
| Scroll duration / hold | the recorder's | meaningless for the design |
| Train repeat period | time-intrinsic | **no** — one pass in 2.25s tells you nothing |

**Here the train is bound to the scroll instead.** That is a deliberate departure from the
source: scroll down and it runs left → right; scroll back up and it reverses. It is a function
of *where you are*, not of *what time it is*, so it can never be missed and never loops
awkwardly on a page nobody is looking at.

The constant is not invented. During the recording the train covered **1501 px/s** while the
page scrolled at **419 px/s** — so it travels **3.58 units for every pixel you scroll**:

```css
.train { transform: translateX(calc(-60px + var(--s) * 3.58)); }
```

The ratio is measured; the *binding* is the design decision. Crossing the viewport takes
~589px of scroll.

## Layer speeds

Each layer is a flat colour, so each layer is a binary mask. The vertical shift `dy` that
minimises mask disagreement between two frames is that layer's displacement.

The trap is that layers **enter the viewport** during a scroll, so any statistic depending on
a layer's visible extent — topmost row, centroid, a fixed viewport band — moves for reasons
that have nothing to do with translation. Four estimators were tried; three failed:

| Method | Verdict |
|---|---|
| fixed viewport bands | measured the page scroll, not the layer |
| topmost ridge row | jumped between hill peaks, clamped at the screen edge |
| textured-patch tracking | latched onto the purple **headline text**, not the purple hills |
| **mask alignment over a common window** | **stable, reproduced at two scales** |

Restricting to the window where **every** layer is on screen (frames 97–134) and accumulating
identical step counts, run at quarter and half resolution:

| Layer | quarter | half | verdict |
|---|:--:|:--:|---|
| mid hills | 0.72× | 0.72× | **measured** |
| deep hills | 0.85× | 0.87× | **measured** |
| near hills | 0.97× | 1.00× | **measured** |
| foreground | 1.00× | 1.00× | reference |
| sky / far hills | −0.03× / 0.10× | 0.63× / 0.33× | **not recoverable** |

**The backdrop is not recoverable**, and the reason is honest rather than mysterious: the sky
is a smooth gradient, so its colour mask isn't stable between frames. Estimates ranged from
−0.03 to 0.63. Any single number quoted for it would be invented.

In the recreation the **sky and the far hills share one factor (`0.30`)** — a design choice
inside the uncertainty. They are the same pale mask, and the measurement could never separate
them. Pinning the sky at `0.00` while the far hills climbed at `0.30` was the first attempt,
and it was wrong: the hills ate the sky band and left a hard edge across the top of the hero.
One backdrop plane is both more coherent and what the pixels actually support.

### The sky is a backdrop, not a layer

We once clamped parallax travel to 240px and blamed a **depth inversion**: near hills climbing
over far ones. That diagnosis was wrong. A near hill sweeping up over a far one is what parallax
*is* — scrolling down moves the camera down, and near things climb the frame faster. Nothing ever
changed depth.

What actually broke: the sky was a `<rect>` inside a layer that sinks at `0.70 × scroll`, and a
rect **has a top edge**. Its only protection was the overhang that `slice` happens to leave above
the hero — measured at 474px on one viewport and **14px** on another, where the sky is cut after
20px of scroll. The clamp hid the edge by freezing the parallax after a third of one screen.

```css
.hero { background: linear-gradient(180deg, ...); }   /* no edge, so nothing to uncover */
.ly   { transform: translate3d(0, calc(min(var(--s), var(--pmax)) * (1 - var(--f))), 0); }
```

`--pmax` is now `900px` — the hero's own height — and exists only to bound the transform after the
hero has left. The factors resolve **exactly** at every offset; ask `DOMMatrix`, not a screenshot.

### The composition is ours; the ridges are the source's

The traced land fills 93% of the canvas — and so does the source's. Its upper hills only *read* as
sky because they are pale-yellow on pale-yellow. A bottom-anchored, width-scaled artwork shows
exactly `heroH × 1400/heroW` canvas rows, so a 745-row terrain leaves nowhere for a sky to be, at
any viewport. Padding the canvas cannot invent one; the land has to shrink. `cy()` compresses it
toward the horizon by `LAND_K = 0.78`. The map is affine, so ridge shapes and layer factors are
untouched. Sky: 7% of the canvas → 28%.

### The viaduct

The bridge deck is the sharpest rigid feature in the whole clip, so it was tracked directly
against the two foreground tree apexes:

```
bridge deck      4.69 px/frame  (resid 3.5)
left tree apex   5.88 px/frame  (resid 4.4)
right tree apex  5.82 px/frame  (resid 4.4)
  -> bridge parallax factor = 0.80x ± 0.04
```

That is consistent within noise with the deep hills it sits in (0.86×), so it rides that layer.

## The train

Tracked by its **tail**, because the nose spends the whole clip hidden behind a foreground
tree — a clamped nose would have reported a speed of 16 px/s instead of 1500.

| Property | Value |
|---|---|
| Direction | left → right (nose leading) |
| Speed in the source | **1501 px/s** (tail, frames 96–124) |
| Scroll speed in the source | **419 px/s** (both tree apexes) |
| Bound here as | **3.58 units of train per pixel of scroll** |
| Length | ~708 px |
| Height | ~58 px, riding the deck at `y=498` |
| Easing | **none claimed** |

Per-4-frame velocity estimates scatter from 1080 to 1800 px/s with no clean trend — that's
measurement noise from car gaps breaking the colour run, not an ease. Constant speed is within
noise, so the recreation uses `linear`.

The **repeat period is not observable**: the clip shows exactly one pass. That question
disappears entirely once the train is bound to scroll — there is no period, only position.

## Terrain: traced, not approximated

The four hill ridgelines are traced out of the final frame, one `y` per column, into
[`ridges.json`](ridges.json).

The subtlety: occluders — trees, bushes — always sit **above** the terrain, so a naive
first-occurrence ridge gets pulled *upward* wherever a tree crosses it. The terrain is
therefore the **upper quantile** of the raw trace over a wide window, not its median. A median
still follows a tree crown that spans 200 columns; the 70–80th percentile does not.

The ground line is the one exception — it is almost entirely hidden behind foreground trees in
the source, so it is derived from the purple ridge rather than traced.

## Verified, not asserted

Probed in a real browser: scroll to 300px, then read each layer's on-screen position. A
layer's on-screen speed relative to the page **is** its parallax factor.

```
scrollY=200 (inside --pmax)     train: animation-name = none (it is pure geometry)
set_f=0.30  implied_f=0.300     train translateX = 656.0  (expect -60 + 3.58*200 = 656.0)
set_f=0.30  implied_f=0.300
set_f=0.72  implied_f=0.720     scrolling 300 -> 100: dx = -716.0  (the train reverses)
set_f=0.86  implied_f=0.860
set_f=0.97  implied_f=0.970
set_f=1.00  implied_f=1.000
```

## How it's built

One CSS declaration does the parallax:

```css
.ly { transform: translate3d(0, calc(var(--s) * (1 - var(--f))), 0); }
```

`--s` is `scrollY`, written once per frame from a rAF-coalesced listener. A layer at `f = 0`
translates down exactly as fast as the page scrolls up, so it is pinned. A layer at `f = 1`
doesn't translate at all, so it rides the page. Everything between is parallax.

The train is a `<g>` inside the deep-hills SVG, so it inherits that layer's vertical parallax
for free and only needs its own horizontal term. It has **no animation at all** — its position
is a pure function of `--s`, which is why it reverses when you scroll back up.

Under `prefers-reduced-motion: reduce` the transforms are dropped, `--s` never advances, and the
train simply rests on the bridge — a still, correct illustration.

## Only the palette changed

| Source | Here | |
|---|---|---|
| `#FBE9AE` pale gold | `#EAF7F1` mint | sky top |
| `#FAE086` sand | `#CFEBE0` pale aqua | far hills |
| `#FC7541` orange | `#7FCCC2` teal | mid hills |
| `#C9234C` crimson | `#38869A` deep cyan | deep hills |
| `#5B0081` purple | `#1E5570` navy | near hills |
| `#170433` near-black plum | `#08192A` near-black navy | foreground |

A warm sunset became a cool dawn. The terrain, the viaduct, the train, the tree shapes and the
depth order are the source's.

## What's still approximate

- **The sky and far hills share a chosen factor** (`0.30`), as above — they were never separable.
- **The vertical composition is a design choice**: the traced land is compressed ×0.78 toward the
  horizon so there is a sky. Ridge shapes and layer factors are untouched.
- **Binding the train to scroll is a departure from the source**, where it runs on a clock.
  The 3.58 ratio it uses is measured; the binding is a choice.
- **The ground line is derived**, not traced.
- **Trees, bushes, tulips and the train's car divisions are our own drawings**, positioned to
  match the source. Only the terrain is traced.

*The timing transfers; the artwork doesn't have to.*
