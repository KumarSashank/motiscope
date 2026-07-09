# <example name>

> One line: what animation this is and where it's from (your own work / licensed source).

**Motion type:** entrance | stagger | loader/loop | scroll-driven | hover | text | svg-draw · **Target:** GSAP | CSS | Framer | Lottie · **Tier:** 1 | 2 | 3

## Source

![source](input.gif)  <!-- or embed/link input.mp4 -->

What was recorded, at what fps, any capture notes.

## What motiscope measured (raw)

See [`analysis/report.md`](analysis/report.md) and [`analysis/frames/`](analysis/frames/) — **unedited**.

Paste the key line from the report, e.g.:

```
2.00s clip at 60fps, 1280x720. 2 segment(s): fade-in, move. Dominant easing: ease-out.
Stagger hint: left-to-right (~80ms each).
```

## The recreation

Run [`output/index.html`](output/index.html). Built as: `/motiscope:recreate <target>`.

## Honest diff — what matched, what I tuned

- ✅ **Matched out of the box:** timing, easing, stagger direction …
- ✏️ **Tuned by hand:** exact colors, translate distance (estimated), …
- ⚠️ **Didn't capture:** (if anything) …

<!-- Optional: a side-by-side GIF of original (left) vs recreation (right). -->
