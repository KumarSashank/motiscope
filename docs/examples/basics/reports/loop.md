# motiscope analysis report

**Source:** `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/loop6.mp4`  
**Duration:** 7.20s · **fps:** 25.0 · **size:** 800×450 · **codec:** h264

> 7.20s clip at 25.0fps, 800x450. 11 segment(s): move, hold, move, hold, move, hold, move, hold, move, hold, move. Dominant easing: linear. Loops every ~1200ms (confidence 0.83). Profile: low visual complexity, low motion (simple static graphics). Stagger hint: left-to-right (~7ms each).

## Motion-energy curve

Per-frame motion magnitude (mean pixel change vs previous frame). This is the source of truth for **timing and easing** — read the shape per segment rather than eyeballing frames.

```
▁▃▇▇▁▄▇▄▁▂▇▇▃▃▇▅▂▁▅▇▄▃▇▇▂▁▄▇▆▁▇▇▃▁▃▇▆▁▆▇▄▁▂▇▇▃▄█▅▁
```
peak 2.958 @ 4.48s · mean 1.587 · hold threshold 0.478

## Segments (beats)

| # | kind | start | end | dur | easing | cubic-bezier | conf |
|---|------|-------|-----|-----|--------|--------------|------|
| 0 | move | 0.00s | 1.12s | 1.12s | linear | `0.0,0.0,1.0,1.0` | estimated |
| 1 | hold | 1.16s | 1.28s | 0.12s | — | — | — |
| 2 | move | 1.32s | 2.32s | 1.00s | linear | `0.0,0.0,1.0,1.0` | measured |
| 3 | hold | 2.36s | 2.48s | 0.12s | — | — | — |
| 4 | move | 2.52s | 3.52s | 1.00s | linear | `0.0,0.0,1.0,1.0` | measured |
| 5 | hold | 3.56s | 3.68s | 0.12s | — | — | — |
| 6 | move | 3.72s | 4.72s | 1.00s | linear | `0.0,0.0,1.0,1.0` | measured |
| 7 | hold | 4.76s | 4.88s | 0.12s | — | — | — |
| 8 | move | 4.92s | 5.92s | 1.00s | linear | `0.0,0.0,1.0,1.0` | measured |
| 9 | hold | 5.96s | 6.08s | 0.12s | — | — | — |
| 10 | move | 6.12s | 7.16s | 1.04s | linear | `0.0,0.0,1.0,1.0` | estimated |

**Dominant easing:** `linear`

**Stagger hint:** left-to-right — ~7ms between elements (confidence 0.56).

**Loop:** repeats every ~1200ms (confidence 0.83). Set `loop: true` in the spec; consider re-analyzing just one period (`--start 0 --end 1.20`) for the cleanest keyframes. _Energy is speed-based, so for back-and-forth motion this may be a **half**-cycle — check the frames: same-direction repeat ⇒ `repeat: -1`; out-and-back ⇒ `yoyo` at this period._

**Content profile (SI/TI):** low visual complexity, low motion (simple static graphics)

**Freezes/holds:** 0.0–0.32s, 0.44–0.88s, 0.88–1.08s, 1.08–1.52s, 1.64–2.08s, 2.08–2.32s, 2.32–2.72s, 2.84–3.28s, 3.28–3.48s, 3.48–3.92s, 4.04–4.48s, 4.48–4.68s, 4.68–5.12s, 5.24–5.68s, 5.68–5.88s, 5.88–6.32s, 6.44–6.88s, 6.88–7.08s

## Curated frames

1 PNG frame(s). Read them in order; the filename encodes timestamp + why it was picked.

- `t=0.0s` **start** → `/private/tmp/claude-501/-Users-kumarsashank-dev-Motion-Vision/b3fcaa87-332f-4983-97b5-8fffcda286db/scratchpad/f6/loop6-ac9b03db/frames/frame_000_t0s_start.png`

## Confidence

- **Measured** (reliable): duration, fps, segment boundaries, easing shape, stagger direction, holds/fades.
- **Visually estimated** (from the frames): which elements move, transform magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these as estimates when you build the spec.
