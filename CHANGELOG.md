# Changelog

All notable changes to motiscope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

## [0.4.0] — unreleased

Refocus: the numbers measure *time*; the model does the *perception*.

The pipeline was drifting into re-implementing perception (classifying animation types,
per-element clustering, motion direction) that a vision model already does better from
frames. Sharpened the division of labor:

### Changed
- **The numeric layer now owns only what a still can't show — timing.** It measures
  durations, the per-segment easing **cubic-bezier** (from the velocity profile),
  beat/segment boundaries, stagger *timing*, and loop period, and it curates the right
  frames. That's the moat.
- **Perception is handed to the model.** The spec and the `analyze`/`recreate` skills
  are rewritten so Claude identifies the elements and — from the frames — *what kind of
  animation* each is, with an **open vocabulary** (fade, slide, scale, mask reveal, path
  draw, morph, 3D, text effect, particles, …). motiscope no longer classifies animation
  types, so there's no fixed list to limit recreation.

### Removed
- In-code motion **direction** detection (perception the model reads better from frames).
- The abandoned per-element clustering experiment (a sweep and a stagger are
  indistinguishable in frame-differencing — needs optical flow, which is out of scope).

## [0.3.0] — unreleased

Deeper motion measurement (sharpening the core recreate-a-single-animation use).

### Added
- **Measured easing.** Each move segment now carries a fitted **`cubic-bezier`** — the
  running integral of the speed curve matched to a real easing curve — not just a
  coarse class. `recreate` uses the exact bezier (CSS `cubic-bezier`, Framer array,
  GSAP `CustomEase`) instead of a token default.
- **Motion direction.** Each move/fade segment gets a travel direction
  (`up`/`down`/`left`/`right`/diagonal/`in-place`) from the motion-grid energy centroid,
  so the recreation gets the sign of the translate (and knows `in-place` scale/fade vs a
  real move) rather than guessing from frames.
- Report shows a `cubic-bezier` and `dir` column per segment; the spec schema and the
  easing map are updated to prefer the measured values.

## [0.2.0] — unreleased

Fixes from the first real-world landing-page test (a Dribbble concept walkthrough).

### Fixed
- **Transitions no longer hide the real animations.** A hard cut or full-screen fade
  produced near-maximal energy that inflated the motion threshold, so the actual
  in-section element animations were mislabeled as `hold`. The threshold now uses a
  spike-robust reference (75th-percentile of energy), surfacing those animations.
- **Auto-decompose no longer burns the budget on transitions.** Fades/cuts are capped
  at ~2–3 frames each (they're monotonic — endpoints are enough); the budget goes to
  the actual `move` beats and each content section gets a representative frame.
  (Previously a single 0.27s fade could grab 33 of 48 frames.)

### Added
- **`landing` preset** (44 frames / 1280px) for web/landing walkthroughs — cover each
  section's design at readable resolution plus the in-section motion.
- **Real image generation** for the `gemini` / `imagen` provider (Imagen via the Gemini
  API) in `assetgen.py` — the asset-key + consent flow now actually produces images.
  Other providers (video, etc.) still write a labeled placeholder.

## [0.1.0] — unreleased

Initial release.

### Added
- `/motiscope:analyze` — extract an animation-tuned motion analysis (per-frame
  motion-energy curve, motion grid, scene/freeze/black/siti/brightness signals) and
  a curated set of PNG keyframes from a local screen recording, then characterize
  the animation as a target-agnostic spec.
- **Frame/cost controls:** presets (`draft` 12 / `balanced` 32 / `detailed` 48
  frames), a focus window (`--start`/`--end`, timestamps returned absolute), and a
  density control (`--fps` uniform backbone, `--no-dedup`) so fast content between
  keyposes isn't missed. Frame count is capped by the preset and tracks motion
  complexity, not video length.
- **Localized motion energy:** the primary motion signal is derived from the most-
  active grid cells (top-K), so a small element moving on a large static canvas
  registers as real motion instead of being diluted by the background. `freezedetect`
  is demoted to confirmation-only (it can no longer override a detected move, since it
  measures whole-frame stillness).
- **Auto-decompose:** for clips ≥8s with ≥2 motion beats, extraction concentrates
  frames on each motion segment (drilled densely) and gives holds a single frame, so
  the budget follows the motion. Frames are allocated **per beat in proportion to
  motion magnitude** (duration × peak energy), so fast/intense beats get more frames
  than slow ones. `--decompose` / `--no-decompose` to force.
- **Loop detection:** looping animations are detected via energy-curve autocorrelation
  (with guards against false positives on mostly-static clips and one-off bursts) and
  reported with a period + confidence. The period may be a half-cycle for back-and-
  forth motion; recreation guidance covers `repeat` vs. `yoyo`.
- `/motiscope:recreate` — turn the analysis into working code for GSAP,
  CSS/Web Animations, Framer Motion (React), or Lottie/SVG.
- `/motiscope:doctor` — verify `ffmpeg`/`ffprobe` and scaffold the optional
  API-key config used for (stubbed) asset generation.
- Python pipeline (stdlib only): `mvlib`, `analyze_motion`, `extract_frames`,
  `ingest`, `config`, `assetgen`, `mvsetup`.
- `SessionStart` hook that reports missing dependencies and videos waiting in
  `animations/`.
- Reference guides: an easing map and per-target rendering notes.
- Test harness: ffmpeg-synthesized ground-truth clips and stdlib unit tests.
