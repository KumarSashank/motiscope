# motiscope

**Recreate any web animation from a screen recording.** Drop a video of an
animation you like — captured from a website, an app, a dribbble shot, anywhere —
and motiscope measures its motion (timing, easing, sequencing) and helps Claude
rebuild it as working **GSAP, CSS, Framer Motion, or Lottie/SVG** code.

A Claude Code plugin dedicated to motion design. Pure Python (standard library) +
`ffmpeg`. No cloud, no npm, no accounts required.

> "I want this animation on my site." — drop the clip, run `/motiscope:analyze`,
> then `/motiscope:recreate gsap`.

## How it works

motiscope splits the problem into two artifacts with very different cost:

1. **A dense, numeric motion analysis** — a per-frame *motion-energy curve* (sampled
   at native/high fps, **not** capped at 2 fps) plus ffmpeg signal analysis
   (`scdet`, `freezedetect`, `blackdetect`, `siti`, `signalstats`). This is pure
   numbers — effectively free — and it is the source of truth for **timing, easing,
   holds, fades, and stagger**.
2. **A small set of curated PNG keyframes** (~24–48) chosen at motion-curve extrema,
   segment boundaries, and fades. Claude *sees* these with its native vision to
   estimate **which elements move and by how much**.

So easing shape is *measured*; transform magnitudes are *visually estimated*. The
result is a target-agnostic **animation spec** that `recreate` renders into code.

## Install

```
/plugin marketplace add github:KumarSashank/motiscope
/plugin install motiscope
```

Requires `ffmpeg` + `ffprobe`. Run `/motiscope:doctor` to check and (with your
consent) install them (`brew install ffmpeg` on macOS).

> Update the marketplace repo URL above to wherever you host this plugin.

## Usage

```
/motiscope:doctor                      # verify deps, scaffold config (first run)
/motiscope:analyze animations/hero.mp4 # analyze a recording -> animation spec
/motiscope:recreate gsap               # emit GSAP code (or css | framer | lottie)
```

Or just drop a recording into an `animations/` folder in your project and run
`/motiscope:analyze` — it will find it.

**Local files only.** Supported: `.mp4 .mov .webm .mkv .m4v .avi`. To capture a
web animation, screen-record it and save the file.

## Commands

| Command | What it does |
|---|---|
| `/motiscope:analyze [path] [notes]` | Extract the motion analysis + curated frames, then characterize the animation as a spec. |
| `/motiscope:recreate [gsap\|css\|framer\|lottie] [out-dir]` | Turn the spec into runnable code for a target framework. |
| `/motiscope:doctor` | Verify `ffmpeg`/`ffprobe`; scaffold `~/.config/motiscope/{config.json,.env}`. |

GSAP output leans on the official GSAP skills (timeline / core / scrolltrigger /
react / utils) for idiomatic results.

## Controlling frames & token cost

Only the curated frames Claude *sees* cost tokens (~300–400 each); the numeric
analysis is free. Frame count tracks **motion complexity**, capped by a preset — it
does **not** grow with video length (a 10s clip typically yields ~10 frames).

| Preset | Frame cap | Resolution | Use when |
|---|---|---|---|
| `draft` | 12 | 512px | quick look, tight budget |
| `balanced` *(default)* | 32 (usually 8–20 after dedup) | 640px | most cases |
| `detailed` | 48 | 960px | dense sequences / reading text |

- **Focus a section** of a longer video: `--start 0:12 --end 0:15` (timestamps come
  back in absolute source time).
- **Sample fast content densely**: `--fps 20` lays a uniform backbone (a frame every
  ~50ms) across the window; near-identical frames still collapse unless `--no-dedup`.
- **Auto-decompose** (default for clips ≥8s with ≥2 motion beats): finds the beats,
  drills each motion segment densely, and skips holds — the budget follows the motion
  instead of spreading thin. Frames are allocated **per beat by motion magnitude**
  (a fast/intense beat gets more frames than a slow one). Force with `--decompose` /
  disable with `--no-decompose`.
- **Loop detection**: looping animations are detected (energy-curve autocorrelation)
  and reported with a period, so recreation can set `repeat` / `yoyo` and optionally
  re-analyze a single cycle.

Small elements register correctly: the primary motion signal is *localized* (built
from the most-active regions), so a small button/card/icon moving on a large page is
detected as real motion rather than washing out in a whole-frame average.

```
python3 scripts/ingest.py video.mp4 --preset detailed --start 0:12 --end 0:15 --fps 20
```

## Output layout

Per-video working files land in a gitignored `.motiscope/<slug>/`:

```
.motiscope/<slug>/
  manifest.json   # video meta + timeline + frame index (machine artifact)
  motion.json     # raw motion timeline: energy curve, grid, segments, beats, signals
  report.md       # human-readable summary (energy sparkline, segment table)
  frames/         # curated PNGs, e.g. frame_003_t0.42s_keypose.png
```

Recreated code is written to `motiscope-output/<target>/` by default.

## Asset generation (optional, stubbed)

If a recreation needs an image or video asset, `recreate` will ask whether to point
at your own file, generate one, or use a placeholder. Generation is a **mechanism
only in v0.1**: the API-key config and consent flow are wired up, but the provider
call is stubbed (it writes a labeled placeholder and makes no network request).
Keys live in `~/.config/motiscope/.env` (mode `0600`), are never printed or
written into generated code, and are never committed.

Supported provider slots: image — OpenAI, Stability, Replicate, fal; video —
Runway, Replicate, fal.

## Limitations (what's measured vs. estimated)

- **Measured (reliable):** duration, fps, segment boundaries, easing *shape*,
  hold/fade detection, stagger *direction*.
- **Estimated (from frames):** which elements move, transform magnitudes (px / scale
  / rotation / opacity), colors under compression, exact overshoot, spring stiffness.
- **Not recoverable from frames:** exact cubic-bezier control points (only the class),
  sub-pixel / sub-frame motion, true 3D / z-order, authored Lottie vector data.
  For production Lottie, author in After Effects.
- A very gentle **ease-in**'s opening can read as a short hold because sub-pixel
  motion is invisible in the analysis thumbnails — the dominant easing is still
  recovered; check the first frames.

**For best results:** capture at a high frame rate and avoid heavy compression.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Run the test suite:

```
python3 -m unittest tests.test_analyze_motion
```

## Credits & license

MIT. See [LICENSE](LICENSE). motiscope adapts frame-analysis techniques from two
MIT projects — [claude-video](https://github.com/bradautomates/claude-video) and
[claude-video-vision](https://github.com/jordanrendric/claude-video-vision) — with
gratitude; see [ATTRIBUTION.md](ATTRIBUTION.md).
