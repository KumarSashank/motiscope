# motiscope analysis report

**Source:** `/Users/kumarsashank/dev/Motion Vision/examples/source-videos/parallax.mov`  
**Duration:** 2.25s · **fps:** 60.0 · **size:** 1400×804 · **codec:** h264

> 2.25s clip at 60.0fps, 1400x804. 2 segment(s): hold, fade-in. Dominant easing: linear. Profile: high visual complexity, moderate motion. Stagger hint: top-to-bottom (~61ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▃▃▃▃▃▄▄▄▆▅▅▂▄▅▃▅█▅▄▆▄▄▁▅▂▂▂▂▁▂
```
peak 28.531 @ 1.4s · mean 8.17 · hold threshold 2.692

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | hold | 0.00s | 0.77s | 0.77s | — | — | — |
| 1 | fade-in | 0.78s | 2.23s | 1.45s | spring | `0.34,1.56,0.64,1.0` | estimated |

**Dominant easing:** `linear`

**Stagger hint:** top-to-bottom — ~61ms between elements (confidence 0.35).

**Content profile (SI/TI):** high visual complexity, moderate motion

**Freezes/holds:** 0.0–0.583s

## Curated frames

29 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **holdstart** → `.motiscope/parallax-b707b6ac/frames/frame_000_t0s_holdstart.png`
- `t=0.75s` **fadein** → `.motiscope/parallax-b707b6ac/frames/frame_001_t0.75s_fadein.png`
- `t=0.817s` **peak** → `.motiscope/parallax-b707b6ac/frames/frame_002_t0.82s_peak.png`
- `t=0.921s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_003_t0.92s_uniform.png`
- `t=0.967s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_004_t0.97s_uniform.png`
- `t=1.059s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_005_t1.06s_uniform.png`
- `t=1.151s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_006_t1.15s_uniform.png`
- `t=1.197s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_007_t1.2s_uniform.png`
- `t=1.243s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_008_t1.24s_uniform.png`
- `t=1.283s` **peak** → `.motiscope/parallax-b707b6ac/frames/frame_009_t1.28s_peak.png`
- `t=1.335s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_010_t1.33s_uniform.png`
- `t=1.381s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_011_t1.38s_uniform.png`
- `t=1.427s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_012_t1.43s_uniform.png`
- `t=1.473s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_013_t1.47s_uniform.png`
- `t=1.533s` **peak** → `.motiscope/parallax-b707b6ac/frames/frame_014_t1.53s_peak.png`
- `t=1.583s` **fade-in** → `.motiscope/parallax-b707b6ac/frames/frame_015_t1.58s_fade-in.png`
- `t=1.611s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_016_t1.61s_uniform.png`
- `t=1.657s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_017_t1.66s_uniform.png`
- `t=1.704s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_018_t1.7s_uniform.png`
- `t=1.75s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_019_t1.75s_uniform.png`
- `t=1.783s` **peak** → `.motiscope/parallax-b707b6ac/frames/frame_020_t1.78s_peak.png`
- `t=1.842s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_021_t1.84s_uniform.png`
- `t=1.888s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_022_t1.89s_uniform.png`
- `t=1.98s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_023_t1.98s_uniform.png`
- `t=2.026s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_024_t2.03s_uniform.png`
- `t=2.083s` **peak** → `.motiscope/parallax-b707b6ac/frames/frame_025_t2.08s_peak.png`
- `t=2.118s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_026_t2.12s_uniform.png`
- `t=2.183s` **keypose** → `.motiscope/parallax-b707b6ac/frames/frame_027_t2.18s_keypose.png`
- `t=2.21s` **uniform** → `.motiscope/parallax-b707b6ac/frames/frame_028_t2.21s_uniform.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
