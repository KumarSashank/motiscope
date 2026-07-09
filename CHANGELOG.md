# Changelog

All notable changes to motiscope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses semver.

## [Unreleased]

### Added
- **Example: parallax landscape** — a scroll-driven hero (sky, far hills, mid hills, deep
  hills with a viaduct, foreground trees) recreated from a 2.25s screen recording as one
  self-contained page: hand-drawn SVG layers, ~20 lines of JS, `prefers-reduced-motion`
  honoured. Live at `docs/examples/parallax/`.
  - A parallax is **scroll-driven**, so the clip's seconds belong to whoever scrolled. What
    is intrinsic is each layer's *speed ratio*. Recovered by mask alignment over the window
    where every layer is on screen: **0.72×** (mid hills) and **0.86×** (deep hills), each
    reproduced at two independent scales.
  - The sky/far backdrop is reported as **not recoverable** — a smooth gradient has no stable
    colour mask, and four estimators disagreed from −0.03 to 0.63. Its two coefficients are
    stated as design choices, not measurements.
  - Verified in a real browser: at `scrollY=300`, every layer's on-screen speed equals the
    factor it was given (`implied_f` = 0.000 / 0.300 / 0.720 / 0.860 / 1.000).
- **How it works** — a deep explainer of the analysis, published two ways: a narrated
  live page at `docs/how-it-works.html` (site theme, figures drawn from real pipeline
  output) and `docs/how-it-works.md` with the exact constants, ffmpeg filter strings, and
  limits. Covers the localized energy signal (4× amplification on the ambient loop:
  `1.763` whole-frame vs `6.998` top-K), the percentile-anchored hold threshold and the
  bug that motivated it, easing recovery by integrating the energy curve (verified against
  a clip authored as position ∝ t²), auto-decompose, loop-detection guards, and what
  motiscope deliberately refuses to do.
- Two figures generated from real data: `docs/figures/energy-curve.svg` and
  `docs/figures/easing-fit.svg`. Both readable on light and dark, and both render fully
  when animations are disabled.
- **Example: ambient geometric loop** — a 15-tile Bauhaus grid recreated from a 2.28s screen
  recording as a **14 KB animated SVG** (no JavaScript). Ships as a **live page** in the site
  theme at `docs/examples/ambient/`, not just a GIF: the page renders the actual output SVG,
  and links the unedited `report.md` and the `generate.py` that built it.
  Same shapes, same motion, new palette.
  - The measured beat is **0.75s** (burst peaks 0.317 / 1.067 / 1.817s, agreeing across three
    independent tiles), with easing whose peak angular speed is ~3.6× the mean.
  - A worked demonstration of the project's thesis: the whole-frame readout says
    `linear`, but per tile the velocity drops to near zero and ramps again. The numbers give
    you the timing; you read the frames.
  - Verified rather than asserted — the recreation was rendered back to video and re-measured
    with the same code, reproducing the 0.75s beat.

## [1.0.0] — 2026-07-09

**The first stable release, and the one that stops being Claude-Code-only.**

The measurement pipeline, the frame curation, the fitted easing curves, and the four
recreation targets have all been exercised on real recordings (see the
[gallery](https://kumarsashank.github.io/motiscope/gallery.html)). The public surface —
the `motiscope` CLI, the `.motiscope/<slug>/` output contract, and the four workflows —
is now stable and will follow semver.

### Added
- **A platform-neutral `motiscope` CLI** (`bin/motiscope`, `bin/motiscope.cmd`). Any agent
  that can run a shell can now drive the pipeline without knowing where motiscope lives:
  `analyze`, `doctor`, `assets`, `config`, `home`, `install`. There is deliberately no
  `recreate` subcommand — recreation is the model writing code, not a script.
- **Portable agent skills.** `integrations/skills/motiscope-*/SKILL.md` carry only the
  `name` + `description` frontmatter that both [Codex](https://developers.openai.com/codex/skills)
  and [Cursor](https://cursor.com/help/customization/skills) read, so the same workflows
  run on either.
- **`motiscope install <platform>`** mounts those skills where each agent looks —
  `codex` (`~/.agents/skills/`), `cursor` (`./.cursor/skills/` + a project rule),
  `agents` (a marked, re-updatable block in `AGENTS.md`, read by ~20 tools), or
  `skills --dir <path>` for anything else. `--dry-run`, `--force`, `--dest` supported;
  nothing is overwritten without `--force`.
- **`install.sh`** — one symlink into `~/.local/bin`, no sudo, no network.
- **[PLATFORMS.md](PLATFORMS.md)** — the support matrix, the CLI reference, and an honest
  list of version caveats (Codex's skills directory moved between versions; its custom
  prompts are deprecated; Cursor's slash-argument grammar is unspecified).
- **CI** — tests, a stdlib-only import guard, a CLI smoke test, and the drift check below.

### Changed
- **`skills/*/SKILL.md` is now the single source of truth.** Everything under
  `integrations/` is generated from it by `scripts/build_integrations.py`, which strips
  the Claude-Code-only preamble, swaps Claude-only blocks for portable equivalents (Claude
  Code ships the official `gsap-*` skills; no other agent has them), and rewrites bundled
  script paths into `motiscope ...` commands. The generator then **asserts no
  Claude-specific token survived**, so an unmapped `$SCRIPTS/foo.py` fails the build
  instead of shipping an instruction other agents can't follow.
- Asset generation is described accurately as *optional* rather than "stubbed in v0.1".

### Notes
- The four workflows are named `motiscope-analyze`, `motiscope-recreate`,
  `motiscope-rebuild-site`, and `motiscope-doctor` outside Claude Code (Codex mentions
  them with `$name`, Cursor with `/name`).
- Agents that cannot open a PNG can still report the measured timing, but the workflows
  instruct them to say so rather than guess what is animating.

---

Everything below shipped during pre-1.0 development and is included in 1.0.0.

## [0.6.0] — pre-release

### Added
- **`.gif` inputs.** Screen recordings of web animations are very often GIFs; `analyze`
  now accepts them alongside the video formats.
- **Example: tomato → banana.** A character wake-up loop recorded from
  [SVGator's website-animation examples](https://www.svgator.com/blog/website-animation-examples-and-effects/),
  recreated as an 11 KB animated SVG — with an **original banana character** built on the
  motion motiscope measured from the tomato. Featured in the README and the gallery.
  *The timing transfers; the artwork doesn't have to.*

## [0.5.0] — pre-release

### Added
- **`/motiscope:rebuild-site`** — a workflow that rebuilds a *whole landing page* from a
  walkthrough recording, not just one animation. It orchestrates: analyze the walkthrough
  (measured section timing + transitions + curated frames) → reconstruct the site plan
  (sections, copy, design system) from the frames → generate the photographic assets
  (Imagen) → build a full multi-section page with scroll-driven motion wired to the
  measured timing. Includes an attribution/rights step for design-to-code studies. This is
  the Alterfx example, generalized into one command.

## [0.4.0] — pre-release

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

## [0.3.0] — pre-release

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

## [0.2.0] — pre-release

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

## [0.1.0] — pre-release

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
