# Contributing to motiscope

Thanks for your interest! motiscope is a set of agent workflows backed by small
Python scripts and `ffmpeg`. It ships as a Claude Code plugin and as portable agent
skills for Codex, Cursor, and anything that reads `AGENTS.md` — see
[PLATFORMS.md](PLATFORMS.md).

## Ground rules

- **Python is standard-library only.** No `pip` dependencies. All pixel work goes
  through `ffmpeg`/`ffprobe` shelled out from Python. This keeps installation to
  "have ffmpeg". If you think you need a dependency, open an issue first.
- **Keys and media are never committed.** `.gitignore` excludes `.env`, video files,
  `.motiscope/`, and `motiscope-output/`. Never print or log API keys.
- **Match the measured/estimated split.** Anything derived from the numeric motion
  curve is "measured"; anything read off frames is "estimated". Keep that honest in
  outputs and docs.
- **`skills/*/SKILL.md` is the single source of truth.** Everything under
  `integrations/` is generated from it. Never hand-edit a generated file — change the
  skill and run `python3 scripts/build_integrations.py`. CI fails on drift.

## Layout

```
.claude-plugin/     plugin.json + marketplace.json      (Claude Code)
skills/             analyze, recreate, rebuild-site, doctor (SKILL.md each) -- SOURCE OF TRUTH
integrations/       GENERATED: portable skills, AGENTS.md block, Cursor rule
bin/                motiscope launcher (+ .cmd for Windows)
install.sh          symlinks bin/motiscope onto PATH
scripts/            cli, mvlib, analyze_motion, extract_frames, ingest, config,
                    assetgen, mvsetup, build_integrations
references/         easing-map.md + targets/{gsap,css,framer,lottie}.md
agents/             motion-analyst.md                   (Claude Code)
hooks/              hooks.json + scripts/check-setup.sh (Claude Code)
tests/              make_test_clip.sh, test_analyze_motion.py, test_integrations.py
```

## Dev loop

1. Install `ffmpeg` (`brew install ffmpeg` on macOS).
2. Generate ground-truth clips: `bash tests/make_test_clip.sh`.
3. Run a clip through the pipeline:
   `python3 scripts/ingest.py tests/test-ease.mp4 --frame-budget 16`
   and inspect `.motiscope/<slug>/report.md`.
4. Run the tests: `python3 -m unittest tests.test_analyze_motion tests.test_integrations`.
5. If you touched a `SKILL.md`, regenerate: `python3 scripts/build_integrations.py`
   (verify with `--check`; CI runs it).
6. Test the plugin live in Claude Code from a checkout:
   `claude --plugin-dir .` then `/motiscope:analyze tests/test-ease.mp4`.
7. Test the portable path: `./install.sh && motiscope install cursor --dest /tmp/x --dry-run`.

## Adding a recreation target

1. Add `references/targets/<name>.md` describing how to map the neutral spec.
2. Extend `easing-map.md` with the target's easing column.
3. Teach `skills/recreate/SKILL.md` to recognize `<name>` and read the new guide.

## Tuning the analyzer

Key knobs live at the top of `scripts/analyze_motion.py`: `HOLD_ENERGY_FRACTION`,
`HOLD_INTERIOR_MIN`, `HOLD_BOUNDARY_MIN`, `MAX_ANALYSIS_FPS`, and the `classify_easing`
thresholds. If you change segmentation or easing behavior, add or update a
ground-truth clip + assertion in `tests/` so the change is pinned.

## Pull requests

Keep PRs focused, include a note on how you verified behavior (which clip, what the
analysis produced), and update `CHANGELOG.md`.
