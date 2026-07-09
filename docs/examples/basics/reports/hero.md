# motiscope analysis report

**Source:** `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/rec/hero.mp4`  
**Duration:** 1.60s · **fps:** 25.0 · **size:** 800×450 · **codec:** h264

> 1.60s clip at 25.0fps, 800x450. 4 segment(s): move, hold, move, hold. Dominant easing: ease-out. Profile: high visual complexity, low motion (detailed static shots).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▇█▆▆▄▃▃▁▂▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
```
peak 16.448 @ 0.08s · mean 2.154 · hold threshold 0.307

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | move | 0.00s | 0.52s | 0.52s | ease-out | `0.0,0.0,0.58,1.0` | estimated |
| 1 | hold | 0.56s | 0.64s | 0.08s | — | — | — |
| 2 | move | 0.68s | 0.72s | 0.04s | linear | `0.0,0.0,1.0,1.0` | low |
| 3 | hold | 0.76s | 1.56s | 0.80s | — | — | — |

**Dominant easing:** `ease-out`

**Content profile (SI/TI):** high visual complexity, low motion (detailed static shots)

**Freezes/holds:** 0.4–0.72s, 0.72–0.72s

## Curated frames

4 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **start** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/hero-fb8773d4/frames/frame_000_t0s_start.png`
- `t=0.049s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/hero-fb8773d4/frames/frame_001_t0.05s_uniform.png`
- `t=0.146s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/hero-fb8773d4/frames/frame_002_t0.15s_uniform.png`
- `t=0.244s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/hero-fb8773d4/frames/frame_003_t0.24s_uniform.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
