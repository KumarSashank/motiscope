# motiscope analysis report

**Source:** `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/rec/stagger.mp4`  
**Duration:** 1.80s · **fps:** 25.0 · **size:** 800×450 · **codec:** h264

> 1.80s clip at 25.0fps, 800x450. 2 segment(s): move, hold. Dominant easing: linear. Profile: low visual complexity, low motion (simple static graphics). Stagger hint: top-to-bottom (~117ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▆▆▂▇▅▃▇▅▃▆▅▃▇▅▃█▄▃▃▁▂▁▁▂▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
```
peak 4.51 @ 0.64s · mean 1.25 · hold threshold 0.379

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | move | 0.00s | 0.84s | 0.84s | linear | `0.0,0.0,1.0,1.0` | estimated |
| 1 | hold | 0.88s | 1.76s | 0.88s | — | — | — |

**Dominant easing:** `linear`

**Stagger hint:** top-to-bottom — ~117ms between elements (confidence 0.73).

**Content profile (SI/TI):** low visual complexity, low motion (simple static graphics)

**Freezes/holds:** 0.0–0.16s, 0.16–0.32s, 0.68–0.68s

## Curated frames

3 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **start** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/stagger-6957c3c8/frames/frame_000_t0s_start.png`
- `t=0.28s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/stagger-6957c3c8/frames/frame_001_t0.28s_peak.png`
- `t=0.52s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/stagger-6957c3c8/frames/frame_002_t0.52s_peak.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
