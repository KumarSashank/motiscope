# Parallax landscape — recreated with motiscope

**Live page:** [kumarsashank.github.io/motiscope/examples/parallax/](https://kumarsashank.github.io/motiscope/examples/parallax/)

A scroll-driven parallax hero — sky, far hills, mid hills, deep hills with a viaduct, and a
near-black foreground of trees, bushes and tulips. Recreated from a **2.25s screen
recording**. Same terrain, same depth stack, **new palette**.

- **Original:** a parallax landing page from SVGator's
  [website animation examples](https://www.svgator.com/blog/website-animation-examples-and-effects/)
  — all credit to the original creator.
- **Recreation:** [`index.html`](index.html) — one self-contained file. Hand-drawn SVG layers,
  ~20 lines of JavaScript, no dependencies, `prefers-reduced-motion` honoured.

## What "measuring a parallax" actually means

A parallax is **scroll-driven**, not time-driven. So the timing motiscope reports for this
clip — a 0.77s hold, then 1.45s of motion — describes *the person who did the scrolling*,
not the design. Replaying those seconds would recreate the recording, not the website.

What *is* intrinsic to the design is the **ratio** of each layer's speed to the page scroll.
That's the number worth recovering, and it survives however fast you happened to scroll.

## How the layer speeds were recovered

Each layer is a flat colour, so each layer is a binary mask. For a pair of frames, the
vertical shift `dy` that minimises mask disagreement is that layer's displacement. Sum it
over a window and you have its velocity.

The trap is that layers **enter the viewport** during the scroll. Any statistic that depends
on a layer's visible extent — its topmost row, its centroid, a fixed viewport band — moves
for reasons that have nothing to do with translation. Four estimators were tried, and the
first three disagreed by up to 6× on the middle layers:

| Method | Verdict |
|---|---|
| fixed viewport bands | measures the page scroll, not the layer |
| topmost ridge row | jumps between hill peaks; clamps at the screen edge |
| textured-patch tracking | latched onto the headline text instead of the hills |
| **mask alignment over a common window** | **stable, and reproduced at two scales** |

The fix was to restrict to the window where **every** layer is on screen at once
(frames 97–134, `1.62s–2.23s`) and accumulate identical numbers of steps for each.

## The result

Run twice — at quarter and half resolution, which halves the quantisation of `dy`:

| Layer | quarter-scale | half-scale | verdict |
|---|:--:|:--:|---|
| mid hills | 0.72× | 0.72× | **measured** |
| deep hills + viaduct | 0.85× | 0.87× | **measured** |
| near hills | 0.97× | 1.00× | moves with the foreground |
| foreground | 1.00× | 1.00× | reference layer |
| sky / far hills | −0.03× / 0.10× | 0.63× / 0.33× | **not recoverable** |

Two coefficients reproduce independently. **The backdrop does not**, and the reason is
honest rather than mysterious: the sky is a smooth gradient, so its colour mask isn't stable
between frames. Estimates ranged from −0.03 to 0.63 depending on scale. Any single number
quoted for it would be invented.

So in the recreation: `0.72` and `0.86` are **measured**. `1.00` for the foreground is
measured. `0.00` (pinned sky) and `0.30` (far hills) are **design choices inside the
measurement's uncertainty** — a pinned sky is what a designer would do, and 0.30 sits within
the estimate range.

## Verified, not asserted

The page was probed in a real browser: scroll to 300px, then read each layer's on-screen
position. A layer's on-screen speed relative to the page **is** its parallax factor.

```
scrollY=300
set_f=0.00  top=   0.0  implied_f=0.000
set_f=0.30  top= -90.0  implied_f=0.300
set_f=0.72  top=-216.0  implied_f=0.720
set_f=0.86  top=-258.0  implied_f=0.860
set_f=1.00  top=-300.0  implied_f=1.000
```

Every layer moves at exactly the factor it was given.

## How it's built

One CSS declaration does all the work:

```css
.ly { transform: translate3d(0, calc(var(--s) * (1 - var(--f))), 0); }
```

`--s` is `scrollY`, written once per frame from a rAF-coalesced scroll listener. `--f` is the
layer's factor. A layer at `f = 0` translates down exactly as fast as the page scrolls up, so
it is pinned. A layer at `f = 1` doesn't translate at all, so it rides the page. Everything
between is parallax.

Under `prefers-reduced-motion: reduce` the transforms are dropped entirely and the scene
renders as a flat, correct illustration.

## Only the palette changed

| Source | Here | |
|---|---|---|
| `#FBE9AE` pale gold | `#EAF7F1` mint | sky top |
| `#FAE086` sand | `#C6E9DF` pale aqua | far hills |
| `#FC7541` orange | `#6AC6BC` teal | mid hills |
| `#C9234C` crimson | `#2A7288` deep cyan | deep hills |
| `#5B0081` purple | `#1B4C66` navy | near hills |
| `#170433` near-black plum | `#08192A` near-black navy | foreground |

A warm sunset became a cool dawn. The terrain, the viaduct, the tree shapes, the tulips and
the depth order are the source's.

## What's approximate

- **The hill silhouettes are not traced.** They're sums of sines with the source's rough
  ridge heights and amplitudes. The shapes rhyme; they don't match curve-for-curve.
- **The sky and far-hill speeds are chosen**, as above.
- **Absolute scroll distance is meaningless** — it depends on viewport height, and the
  recording's scroll speed was the recorder's, not the design's.

*The timing transfers; the artwork doesn't have to.*
