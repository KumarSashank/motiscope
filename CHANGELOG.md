# Changelog

All notable changes to motiscope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

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
