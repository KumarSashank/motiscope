# motiscope analysis report

**Source:** `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/rec/scroll.mp4`  
**Duration:** 1.60s · **fps:** 25.0 · **size:** 800×450 · **codec:** h264

> 1.60s clip at 25.0fps, 800x450. 2 segment(s): hold, move. Dominant easing: ease-out. Profile: moderate visual complexity, moderate motion. Stagger hint: bottom-to-top (~99ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▁▁▁▁▁▁▁▁▂▂▄▆▆▇▇█▇▇▆▇▇▆▇▇▇▇▆▇▆▄▃▂▂▁▁▁▁▁▁
```
peak 37.938 @ 0.64s · mean 17.762 · hold threshold 6.199

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | hold | 0.00s | 0.40s | 0.40s | — | — | — |
| 1 | move | 0.44s | 1.56s | 1.12s | ease-out | `0.0,0.0,0.58,1.0` | measured |

**Dominant easing:** `ease-out`

**Stagger hint:** bottom-to-top — ~99ms between elements (confidence 0.98).

**Content profile (SI/TI):** moderate visual complexity, moderate motion

**Freezes/holds:** 0.0–0.4s, 1.32–1.32s

## Curated frames

16 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **holdstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_000_t0s_holdstart.png`
- `t=0.44s` **segstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_001_t0.44s_segstart.png`
- `t=0.488s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_002_t0.49s_uniform.png`
- `t=0.56s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_003_t0.56s_peak.png`
- `t=0.585s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_004_t0.58s_uniform.png`
- `t=0.634s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_005_t0.63s_uniform.png`
- `t=0.682s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_006_t0.68s_uniform.png`
- `t=0.731s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_007_t0.73s_uniform.png`
- `t=0.829s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_008_t0.83s_uniform.png`
- `t=0.878s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_009_t0.88s_uniform.png`
- `t=0.926s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_010_t0.93s_uniform.png`
- `t=0.975s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_011_t0.97s_uniform.png`
- `t=1.04s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_012_t1.04s_peak.png`
- `t=1.073s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_013_t1.07s_uniform.png`
- `t=1.121s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_014_t1.12s_uniform.png`
- `t=1.219s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/final/scroll-a6defc5d/frames/frame_015_t1.22s_uniform.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
