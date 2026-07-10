# motiscope analysis report

**Source:** `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/landing.mp4`  
**Duration:** 4.85s · **fps:** 20.0 · **size:** 1280×720 · **codec:** h264

> 4.85s clip at 20.0fps, 1280x720. 9 segment(s): move, hold, move, hold, move, hold, move, hold, fade-out. Dominant easing: ease-out. Profile: high visual complexity, moderate motion. Stagger hint: right-to-left (~342ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁█▅▅▁▃▃▁▁▁▂▃▃▃▃▄▂▁▁▁▄▃▃▄▃▁▁▂▂▂▂▁▁▁▁
```
peak 81.583 @ 1.55s · mean 14.131 · hold threshold 4.536

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | move | 0.00s | 0.40s | 0.40s | ease-in-out | `0.42,0.0,0.58,1.0` | measured |
| 1 | hold | 0.45s | 1.45s | 1.00s | — | — | — |
| 2 | move | 1.50s | 2.10s | 0.60s | ease-out | `0.0,0.0,0.58,1.0` | estimated |
| 3 | hold | 2.15s | 2.40s | 0.25s | — | — | — |
| 4 | move | 2.45s | 3.05s | 0.60s | linear | `0.0,0.0,1.0,1.0` | measured |
| 5 | hold | 3.10s | 3.35s | 0.25s | — | — | — |
| 6 | move | 3.40s | 3.80s | 0.40s | linear | `0.0,0.0,1.0,1.0` | estimated |
| 7 | hold | 3.85s | 4.05s | 0.20s | — | — | — |
| 8 | fade-out | 4.10s | 4.80s | 0.70s | ease-out | `0.16,1.0,0.3,1.0` | estimated |

**Dominant easing:** `ease-out`

**Stagger hint:** right-to-left — ~342ms between elements (confidence 0.76).

**Content profile (SI/TI):** high visual complexity, moderate motion

**Freezes/holds:** 0.0–0.15s, 0.5–1.5s, 2.1–2.45s, 3.05–3.4s, 3.8–4.1s, 4.5–4.5s

## Curated frames

22 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **start** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_000_t0s_start.png`
- `t=0.219s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_001_t0.22s_uniform.png`
- `t=0.45s` **holdstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_002_t0.45s_holdstart.png`
- `t=1.5s` **segstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_003_t1.5s_segstart.png`
- `t=1.64s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_004_t1.64s_uniform.png`
- `t=1.749s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_005_t1.75s_uniform.png`
- `t=1.858s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_006_t1.86s_uniform.png`
- `t=1.95s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_007_t1.95s_peak.png`
- `t=2.077s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_008_t2.08s_uniform.png`
- `t=2.514s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_009_t2.51s_uniform.png`
- `t=2.624s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_010_t2.62s_uniform.png`
- `t=2.7s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_011_t2.7s_peak.png`
- `t=2.842s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_012_t2.84s_uniform.png`
- `t=2.95s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_013_t2.95s_peak.png`
- `t=3.1s` **holdstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_014_t3.1s_holdstart.png`
- `t=3.4s` **segstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_015_t3.4s_segstart.png`
- `t=3.498s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_016_t3.5s_uniform.png`
- `t=3.607s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_017_t3.61s_uniform.png`
- `t=3.7s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_018_t3.7s_peak.png`
- `t=3.85s` **holdstart** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_019_t3.85s_holdstart.png`
- `t=4.15s` **peak** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_020_t4.15s_peak.png`
- `t=4.263s` **uniform** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/lan/landing-57a2d6b9/frames/frame_021_t4.26s_uniform.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
