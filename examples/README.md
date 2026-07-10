# Examples — built with motiscope

Real recordings in, real code out — **with the whole workflow shown**. The thing
people never share when they post a cool animation is *how they built it*. Every
example here fixes that.

## The transparency standard (non-negotiable)

Trust is earned by showing the unedited chain. Every example folder must include:

1. **The real source** — the screen recording (or a GIF/link) that was fed in. Use
   content you have the rights to (your own work, or licensed/permitted).
2. **motiscope's raw analysis** — the *unedited* `report.md` and the curated frames
   it actually produced (`analysis/`). No cherry-picking.
3. **The output** — the recreated, runnable code (`output/`).
4. **An honest diff** — a short "what matched out of the box / what I tuned" note, and
   ideally a side-by-side of the original vs the recreation.

If motiscope got something wrong, **show it**. Honest examples teach more than perfect ones.

## Folder shape

```
examples/<name>/
  README.md        # the story: what to record, the command used, measured vs tuned
  input.mp4        # (or input.gif / a link in README) — the real source
  analysis/
    report.md      # motiscope's raw report, unedited
    frames/        # the curated PNGs it actually used
  output/
    index.html     # or a component — the runnable recreation
```

Copy [`_template/`](_template/) to start.

## Index

| Example | Motion type | Target | Source |
|---|---|---|---|
| [ground truth: four UI basics](../docs/examples/basics/) | hero entrance, stagger, loop, scroll reveal | CSS ([live](https://kumarsashank.github.io/motiscope/examples/basics/)) | **our own** — authored constants, published error |
| [parallax landscape](../docs/examples/parallax/) | scroll-driven parallax, 5 depth layers | SVG + CSS ([live](https://kumarsashank.github.io/motiscope/examples/parallax/)) | [SVGator examples](https://www.svgator.com/blog/website-animation-examples-and-effects/) |
| [ambient geometric loop](../docs/examples/ambient/) | 15-tile grid, eased ticks on a 0.75s beat | animated SVG ([live](https://kumarsashank.github.io/motiscope/examples/ambient/)) | [SVGator examples](https://www.svgator.com/blog/website-animation-examples-and-effects/) |
| [tomato → banana](../docs/examples/banana/) | character wake-up loop | animated SVG | [SVGator examples](https://www.svgator.com/blog/website-animation-examples-and-effects/) |
| [Cadence landing](../docs/examples/landing/) | whole-page walkthrough: hero entrance, scroll-zoom, stagger, wipe | CSS ([live](https://kumarsashank.github.io/motiscope/examples/landing/site.html)) | **our own** — original page, authored constants |

## Contribute one

1. Record a real animation you have the rights to (screen recording).
2. Run `/motiscope:analyze` then `/motiscope:recreate <target>`.
3. Copy `_template/`, drop in your input, the raw `analysis/`, and the `output/`, and
   fill the README.
4. Open a PR — or post it in [**Show & tell**](https://github.com/KumarSashank/motiscope/discussions)
   and we'll help bring the best ones into the gallery.

See the [gallery](https://kumarsashank.github.io/motiscope/gallery.html) for the live showcase.
