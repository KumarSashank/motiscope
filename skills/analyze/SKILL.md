---
name: analyze
description: Analyze a screen recording of an animation to characterize its motion — timing, easing, transforms, and sequencing — so it can be recreated as web code. Use when the user drops or points at a video of an animation (.mp4/.mov/.webm/.mkv/.m4v/.avi/.gif) and says things like "I want this animation on my site", "recreate this motion", "how is this animated", or runs /motiscope:analyze.
argument-hint: "[path-to-video] [notes]"
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# motiscope: analyze

Turn a screen recording of an animation into a precise, target-agnostic **animation spec** you can hand to `/motiscope:recreate`. A bundled Python pipeline measures the motion (a dense per-frame motion-energy curve + ffmpeg signal analysis — this is the source of truth for timing and easing) and extracts a small set of curated PNG keyframes for you to *see*. You combine the two into the spec.

<!-- motiscope:preamble:start -->
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
<!-- motiscope:preamble:end -->

## Step 0 — preflight (silent on success)

```bash
python3 "$SCRIPTS/mvsetup.py" --check
```

Exit 0 → proceed silently. Non-zero → `ffmpeg`/`ffprobe` are missing; hand off to `/motiscope:doctor` (don't try to analyze without them).

## Step 1 — resolve the input video

- If the user gave a path (in `$1` or their message), use it.
- Otherwise scan the drop folder and project root:
  ```bash
  ls -t animations/*.{mp4,mov,webm,mkv,m4v,avi,gif} *.{mp4,mov,webm,mkv,m4v,avi,gif} 2>/dev/null | head
  ```
  - Several candidates → ask the user (`AskUserQuestion`) which one.
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
| `--preset landing` | 44 | 1280px | **web/landing walkthroughs** — cover each section's design at readable resolution + its in-section motion |

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

**The division of labor is the whole point:**
- **The numbers give you the WHEN.** `report.md` measured the *timing* you can't see in a still: exact durations, the per-segment **easing curve** (a real cubic-bezier fitted from the velocity profile), the beat/segment boundaries, the stagger *timing* (~ms between items), and any loop period. Trust these — a screenshot has no time axis, so this is the one thing that isn't guessable.
- **You give the WHAT.** The frames are yours to read with full vision. Identify the elements and — crucially — **what *kind* of animation each one is.** motiscope does **not** classify animation types, and you are **not** limited to fade/slide/scale: name whatever you actually see — a mask reveal, a path/line draw, a morph, a rotate/skew, a 3D flip, a text split/typewriter, a blur, a color shift, a parallax, a physics/spring bounce, particles, a clip-path wipe, anything. The pipeline deliberately leaves this to your perception because you're better at it than any hand-coded classifier.

Steps:
1. `Read` the printed `report.md` for the measured timing (energy sparkline, segment/beat table with the fitted `cubic-bezier`, stagger timing, loop).
2. `Read` **every curated frame in one message** (parallel Reads) so you see them in order. Filenames encode `t=<seconds>` + why each was picked, so you can line frames up against the measured timeline.

**Read timing from the numbers; read everything else from the frames.**

### The frames are evidence, not an inventory

Frames are chosen by the **motion-energy signal**. Anything small, low-contrast, briefly
visible, or mostly occluded barely moves that signal and **may not appear in a single curated
frame** — while still being a headline feature of the animation. A train crossing a bridge was
missed exactly this way.

Before you commit to a spec:

- Ask **"is anything else moving?"** and go check the clip, not just the frames. Diff a region
  across the whole video, or sample uniformly at a rate the curation skipped.
- If the user names something you cannot see, **believe them and go look**. Its absence from
  the frames is not evidence of its absence from the animation.

### Before you trust a number

A failed automated measurement does not crash. It returns a **confident float**.

- **Two estimators, or you have none.** Measure the same quantity a second, independent way
  (different scale, different feature, different algorithm). Agreement is a result; a
  disagreement of 6× means at least one is lying, and you cannot tell which by looking.
- **Say "not recoverable"** when methods disagree. Averaging `-0.03 .. 0.63` into `0.30`
  invents a fact. Reporting the range *is* the finding.
- **Occluded features report clamped constants.** A value that is pinned at a frame edge, or
  that stays put while everything around it moves, is not a measurement.
- **Scroll-driven ≠ time-driven.** For a parallax, scroll-zoom or pinned section, the seconds
  in the recording are *the recorder's*. Only **ratios** (layer speed ÷ scroll speed) are
  intrinsic. One clip can contain both kinds of clock.

The full list, with the real failures behind each one, is in
`references/measurement-traps.md`. Read it before reporting any velocity, easing or ratio you
derived yourself rather than reading out of `report.md`.

## Step 4 — produce the animation spec

Emit a target-agnostic spec: a **timing skeleton (measured) + your visual reading (what each element is and does)**. Schema:

```json
{
  "duration_ms": 2000,
  "canvas": { "w": 800, "h": 600, "bg": "#ffffff" },
  "loop": false,
  "scroll_driven": false,
  "elements": [{ "id": "card", "role": "card" }],
  "timeline": [
    { "target": "card", "start_ms": 0, "dur_ms": 400,
      "ease": "ease-out", "bezier": [0.16, 1, 0.3, 1],
      "animation": "fade + slide up",
      "props": { "opacity": [0, 1], "y": [24, 0] },
      "source": { "timing": "measured", "everything_else": "seen" } }
  ],
  "stagger": { "children": "card", "each_ms": 80 },
  "notes": "e.g. 'headline does a per-word mask reveal'; 'logo path draws in'"
}
```

Rules:
- **`start_ms`, `dur_ms`, `ease`, `bezier`, stagger `each_ms`, loop `period_ms` are MEASURED** — copy them from `report.md`/`motion.json` verbatim. Especially: use the fitted **`cubic-bezier`** directly (CSS `cubic-bezier(...)`, Framer `[..]`, GSAP `CustomEase`) — it's the real curve, not a guess.
- **`animation`, `elements`, `props` (magnitudes/direction/colors), and the animation *type* are YOURS from the frames** — describe the actual effect in the free-text `animation` field (open vocabulary), and put your best-estimate property values in `props`. Direction, scale, rotation, opacity, morph, draw, etc. all come from what you see, not from the numbers.
- Be honest about a leading `hold`: a gentle ease-in's slow start can read as a short hold (sub-pixel motion is invisible in the analysis thumbnails). Check the first frames — if the element already moved slightly, treat it as the start of the ease, not a delay.
- **Loops:** if the report flags a loop, set `"loop": true` with `period_ms`. It can be a *half*-cycle for back-and-forth motion — decide loop-vs-yoyo from the frames.
- If an effect can't be reduced to `props` (a complex morph, a particle system, a shader), say so in `animation`/`notes` and let `recreate` build it directly from your description — don't force it into simple props.
- **Scroll-driven captures:** set `"scroll_driven": true` and do **not** copy `duration_ms` into the spec as if it were the design's. Report **ratios** (layer speed ÷ page-scroll speed) and note which quantities belong to the recorder. A clip can be scroll-driven *and* contain a time-driven object (a train, a spinner, a looping badge) — measure that object's speed separately.
- **Label every number you derived yourself** (a velocity, a ratio, a period) as measured, estimated, or **not recoverable**. Never let a chosen value read as a measured one.

## Step 5 — offer to recreate

Summarize the animation in one or two sentences, then offer:

> Recreate this as **GSAP**, **CSS**, **Framer Motion**, or **Lottie/SVG**? Run `/motiscope:recreate <target>`.

The spec you just built is saved in `.motiscope/<slug>/manifest.json`; `recreate` will reload it (plus `motion.json`) if you don't hand it over directly.

## Notes

- **Token cost** lives entirely in the frames (~24–48 PNGs). The motion curve is numbers — effectively free. If you already analyzed this clip in the session, don't re-run; reason from what you have.
- Best results come from high-fps, lightly-compressed captures. Warn the user if a recording is heavily compressed or very low frame rate.
