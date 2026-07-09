# motiscope analysis report

**Source:** `/Users/kumarsashank/dev/Motion Vision/examples/source-videos/ambient_loop.mov`  
**Duration:** 2.28s · **fps:** 60.0 · **size:** 1386×830 · **codec:** h264

> 2.28s clip at 60.0fps, 1386x830. 1 segment(s): move. Dominant easing: linear. Profile: high visual complexity, moderate motion. Stagger hint: top-to-bottom (~41ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▄▃▂▁▂▃█▅▃▂▂▂▁▁▁▁▁▁▁▁▁▁▇▅▄▂▂▂▂▂▂▂▄▄▃▂▁▃▅▆▂▄▂▂▁▁▁▁▁
```
peak 25.26 @ 1.083s · mean 6.998 · hold threshold 1.746

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | move | 0.00s | 2.27s | 2.27s | linear | `0.0,0.0,1.0,1.0` | measured |

**Dominant easing:** `linear`

**Stagger hint:** top-to-bottom — ~41ms between elements (confidence 0.61).

**Content profile (SI/TI):** high visual complexity, moderate motion

## Curated frames

38 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **start** → `.motiscope/ambient_loop-dda6115e/frames/frame_000_t0s_start.png`
- `t=0.067s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_001_t0.07s_peak.png`
- `t=0.14s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_002_t0.14s_uniform.png`
- `t=0.187s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_003_t0.19s_uniform.png`
- `t=0.25s` **keypose** → `.motiscope/ambient_loop-dda6115e/frames/frame_004_t0.25s_keypose.png`
- `t=0.28s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_005_t0.28s_uniform.png`
- `t=0.333s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_006_t0.33s_peak.png`
- `t=0.374s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_007_t0.37s_uniform.png`
- `t=0.421s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_008_t0.42s_uniform.png`
- `t=0.467s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_009_t0.47s_uniform.png`
- `t=0.533s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_010_t0.53s_peak.png`
- `t=0.607s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_011_t0.61s_uniform.png`
- `t=0.701s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_012_t0.7s_uniform.png`
- `t=0.841s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_013_t0.84s_uniform.png`
- `t=0.935s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_014_t0.94s_uniform.png`
- `t=1.028s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_015_t1.03s_uniform.png`
- `t=1.083s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_016_t1.08s_peak.png`
- `t=1.168s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_017_t1.17s_uniform.png`
- `t=1.215s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_018_t1.22s_uniform.png`
- `t=1.262s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_019_t1.26s_uniform.png`
- `t=1.308s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_020_t1.31s_uniform.png`
- `t=1.402s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_021_t1.4s_uniform.png`
- `t=1.449s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_022_t1.45s_uniform.png`
- `t=1.495s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_023_t1.5s_uniform.png`
- `t=1.542s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_024_t1.54s_uniform.png`
- `t=1.567s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_025_t1.57s_peak.png`
- `t=1.636s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_026_t1.64s_uniform.png`
- `t=1.682s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_027_t1.68s_uniform.png`
- `t=1.717s` **keypose** → `.motiscope/ambient_loop-dda6115e/frames/frame_028_t1.72s_keypose.png`
- `t=1.776s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_029_t1.78s_uniform.png`
- `t=1.833s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_030_t1.83s_peak.png`
- `t=1.869s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_031_t1.87s_uniform.png`
- `t=1.916s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_032_t1.92s_uniform.png`
- `t=1.963s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_033_t1.96s_uniform.png`
- `t=2.009s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_034_t2.01s_uniform.png`
- `t=2.067s` **peak** → `.motiscope/ambient_loop-dda6115e/frames/frame_035_t2.07s_peak.png`
- `t=2.15s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_036_t2.15s_uniform.png`
- `t=2.243s` **uniform** → `.motiscope/ambient_loop-dda6115e/frames/frame_037_t2.24s_uniform.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
