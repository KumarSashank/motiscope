---
name: analyze
description: Analyze a screen recording of an animation to characterize its motion — timing, easing, transforms, and sequencing — so it can be recreated as web code. Use when the user drops or points at a video of an animation (.mp4/.mov/.webm/.mkv/.m4v/.avi) and says things like "I want this animation on my site", "recreate this motion", "how is this animated", or runs /motiscope:analyze.
argument-hint: "[path-to-video] [notes]"
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# motiscope: analyze

Turn a screen recording of an animation into a precise, target-agnostic **animation spec** you can hand to `/motiscope:recreate`. A bundled Python pipeline measures the motion (a dense per-frame motion-energy curve + ffmpeg signal analysis — this is the source of truth for timing and easing) and extracts a small set of curated PNG keyframes for you to *see*. You combine the two into the spec.

## Resolve the scripts directory (do this first)

Every command below runs a bundled script. Set `SCRIPTS`:

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT:-}/scripts"
# Fallback for harnesses that don't export CLAUDE_PLUGIN_ROOT: this SKILL.md lives at
# <plugin>/skills/analyze/SKILL.md, so scripts are two levels up. Use the absolute
# path of the directory containing the SKILL.md you just Read.
if [ ! -f "$SCRIPTS/ingest.py" ]; then
  SCRIPTS="<absolute dir of this SKILL.md>/../../scripts"
fi
if [ ! -f "$SCRIPTS/ingest.py" ]; then
  echo "ERROR: cannot find ingest.py — check the plugin install." >&2; exit 1
fi
```

On **Windows** use `python` instead of `python3` in every command below.

## Step 0 — preflight (silent on success)

```bash
python3 "$SCRIPTS/mvsetup.py" --check
```

Exit 0 → proceed silently. Non-zero → `ffmpeg`/`ffprobe` are missing; hand off to `/motiscope:doctor` (don't try to analyze without them).

## Step 1 — resolve the input video

- If the user gave a path (in `$1` or their message), use it.
- Otherwise scan the drop folder and project root:
  ```bash
  ls -t animations/*.{mp4,mov,webm,mkv,m4v,avi} *.{mp4,mov,webm,mkv,m4v,avi} 2>/dev/null | head
  ```
  - Several candidates → `AskUserQuestion` which one.
  - Exactly one → use it.
  - None → tell the user to drop a recording into `animations/` (or pass a path) and stop.

**Local files only.** motiscope does not download URLs. If the user pastes a URL, ask them to screen-record it and drop the file in.

## Step 2 — run the pipeline

```bash
python3 "$SCRIPTS/ingest.py" "<video>" --preset balanced
```

It writes to `.motiscope/<slug>/` and prints a summary, the `report.md` path, and the ordered curated frame list.

### Choose a preset (this is the main token dial)

The number of frames you `Read` is what costs tokens (~300–400 tokens/frame); the numeric analysis is free. Frame count tracks *motion complexity*, capped by the preset — it does **not** grow with video length.

| Preset | Frame cap | Resolution | Use when |
|---|---|---|---|
| `--preset draft` | 12 | 512px | quick look, tight token budget |
| `--preset balanced` *(default)* | 32 (usually lands 8–20 after dedup) | 640px | most cases |
| `--preset detailed` | 48 | 960px | dense multi-beat sequences, or reading on-screen text |

Start with `balanced`. Only reach for `detailed` if the animation is intricate or you couldn't read a label; use `draft` for a fast first pass. If the user hasn't said, pick `balanced` and mention they can ask for more detail.

### Focus a section of a longer video (`--start` / `--end`)

For anything longer than ~15s, or when the user points at a specific moment ("the part around 0:12", "the last second"), analyze just that window instead of a sparse whole-clip scan. Times accept `SS`, `MM:SS`, or `HH:MM:SS`; frame/segment timestamps come back in **absolute** source time.

```bash
python3 "$SCRIPTS/ingest.py" "<video>" --preset detailed --start 0:12 --end 0:15
```

### Capture fast content densely (`--fps`)

Within a (short) focus window you can force a uniform sample rate so nothing between keyposes is missed — e.g. `--fps 20` gives up to a frame every ~50ms. Near-identical frames are still collapsed unless you pass `--no-dedup`. Combine with a short window so the budget isn't blown:

```bash
python3 "$SCRIPTS/ingest.py" "<video>" --start 1.0 --end 3.0 --fps 20 --frame-budget 48
```

### Complex / long animations: auto-decompose

For clips ≥8s with two or more motion beats, `ingest.py` **auto-decomposes** by default: it finds the beats, then concentrates frames on each *motion* segment (drilling densely) and gives each *hold* just one representative frame — so the budget is spent on motion, not dead air. A 10s clip with a 5s hold in the middle spends ~0 frames on the hold. The report notes when this happened.

Control it with `--decompose` (force on) / `--no-decompose` (force the flat single-pass). Auto is the right default; force it off only if you specifically want even coverage across the whole timeline.

Other flags: `--frame-budget N` / `--resolution W` override the preset; `--format jpg` for gradient-heavy recordings that bloat as PNG; `--no-dedup` to keep every sampled frame; `--out DIR` (default `.motiscope/`).

> **Small elements register now.** The primary motion signal is *localized* (built from the most-active regions of the frame), so a small button/card/icon moving on a large page reads as real motion instead of washing out. The stagger direction in the report tells you the sequencing (e.g. `left-to-right, ~200ms each`) — use it when building the spec's `stagger`.

## Step 3 — read the analysis, then the frames

1. `Read` the printed `report.md`. It contains the **motion-energy curve** (a sparkline), the **segment/beat table** (move / hold / fade with start/end and measured easing), the **stagger hint**, and the **content profile**.
2. `Read` **every curated frame path in a single message** (parallel Read calls) so you see them together and in order. Each filename encodes `t=<seconds>` and why it was picked (`start`, `peak`, `keypose`, `holdstart`, `fadein`, `end`, …), so you can line each image up against the timeline.

**Read easing from the curve, not the frames.** The per-segment energy shape (rising / decaying / bell / flat / overshoot) already tells you the easing — see `references/easing-map.md`. Use the frames to determine *what* moves and *by how much*, not the timing.

## Step 4 — produce the animation spec

Emit a normalized, target-agnostic spec and show it to the user. Schema:

```json
{
  "duration_ms": 2000,
  "canvas": { "w": 800, "h": 600, "bg": "#ffffff" },
  "loop": false,
  "scroll_driven": false,
  "elements": [{ "id": "card", "role": "card", "confidence": "estimated" }],
  "timeline": [
    { "target": "card", "start_ms": 0, "dur_ms": 400, "ease": "power2.out",
      "props": { "opacity": [0, 1], "y": [24, 0], "scale": [0.9, 1] },
      "source": { "easing": "measured", "props": "visual-estimate" } }
  ],
  "stagger": { "children": "card", "each_ms": 80, "from": "start" },
  "notes": "hold 0.4-0.7s; brightness ramp 0-0.4s => global fade-in"
}
```

Rules:
- **Timing, segment boundaries, easing shape, stagger direction, holds and fades are measured** — take them from `manifest.json` / `report.md`.
- **Which elements move, and transform magnitudes (px / scale / rotation / opacity), colors, and exact overshoot are visually estimated** — read them off the frames and mark them `"visual-estimate"` in `source`.
- Be honest about a leading `hold`: a gentle ease-in's slow start can read as a short hold because sub-pixel motion is invisible in the analysis thumbnails. Check the first two frames — if the element already moved a little, treat it as the start of the ease, not a hard delay.
- Keep `ease` values as neutral tokens (`ease-in`, `ease-out`, `ease-in-out`, `linear`, `spring`, `hold`); `recreate` maps them per target.
- **Loops:** if the report flags a loop, set `"loop": true` and use `period_ms` as the cycle length. The detected period can be a *half*-cycle for back-and-forth motion — check the frames: returns-to-start-then-repeats ⇒ a full loop; out-and-back ⇒ yoyo at that period. For a clean recreation of a long looping clip, re-run analyze focused on a single period (`--start 0 --end <period>`).

## Step 5 — offer to recreate

Summarize the animation in one or two sentences, then offer:

> Recreate this as **GSAP**, **CSS**, **Framer Motion**, or **Lottie/SVG**? Run `/motiscope:recreate <target>`.

The spec you just built is saved in `.motiscope/<slug>/manifest.json`; `recreate` will reload it (plus `motion.json`) if you don't hand it over directly.

## Notes

- **Token cost** lives entirely in the frames (~24–48 PNGs). The motion curve is numbers — effectively free. If you already analyzed this clip in the session, don't re-run; reason from what you have.
- Best results come from high-fps, lightly-compressed captures. Warn the user if a recording is heavily compressed or very low frame rate.
