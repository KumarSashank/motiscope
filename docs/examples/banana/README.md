# Wake-up loop — tomato → banana

<p align="center">
  <img src="compare.gif" width="100%" alt="Left: the original tomato animation. Right: the banana recreated with motiscope — both playing the same beats in sync.">
</p>

<p align="center"><sub><b>Left:</b> the original. &nbsp;<b>Right:</b> recreated with motiscope. &nbsp;<i>Both panels are one clip, phase-aligned, so you can watch the beats land together.</i></sub></p>

- **Original:** the tomato character animation from SVGator's
  [website animation examples](https://www.svgator.com/blog/website-animation-examples-and-effects/)
  — all credit to the original creator.
- **Recreation:** [`banana-loop.svg`](banana-loop.svg) — an **original banana character**,
  built as an animated SVG on the motion motiscope measured from the tomato.

## The point

motiscope measured the **timing** — a 4.45s clock and the beats: a hold in the dark →
the light coming on and the character waking → a settle → the wave — with the easing
curves for each. The banana's character, colours, and shapes are **original**; only the
*motion* was taken.

> **The timing transfers; the artwork doesn't have to.** This isn't a clone of the
> source art — it's the same performance, played by a different character.

11 KB of animated SVG (CSS keyframes on one shared clock), with a
`prefers-reduced-motion` guard.

## Files

| File | What it is |
|---|---|
| [`source-tomato.gif`](source-tomato.gif) | the unedited source that was fed in (355 KB) |
| [`banana-loop.svg`](banana-loop.svg) | the recreation — crisp, scalable, 11 KB |
| [`compare.gif`](compare.gif) | the two above, phase-aligned into a single 4.4s clip |

The side-by-side is one file on purpose: two separate media elements start their loops
whenever they each finish loading, so the beats drift apart. One clip, one clock.
