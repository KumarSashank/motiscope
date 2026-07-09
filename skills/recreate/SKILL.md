---
name: recreate
description: Recreate an analyzed animation as working web code — GSAP (JavaScript), CSS/Web Animations, Framer Motion (React), or Lottie/SVG. Use after /motiscope:analyze, or when the user asks to "build/recreate this animation in <framework>". Reads the motiscope animation spec and emits a runnable component.
argument-hint: "[gsap|css|framer|lottie] [output-dir]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
user-invocable: true
---

# motiscope: recreate

Translate a motiscope **animation spec** into real, runnable animation code for one target framework. Timing and easing come from the measured spec; you render it faithfully.

## Resolve the plugin root

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-}"
[ -f "$ROOT/scripts/config.py" ] || ROOT="<absolute dir of this SKILL.md>/../.."   # skills/recreate -> plugin root
```

`SCRIPTS="$ROOT/scripts"`, `REFS="$ROOT/references"`. On Windows use `python` for `python3`.

## Step 1 — load the animation spec

- If `/motiscope:analyze` just produced a spec in this conversation, use it.
- Otherwise locate the most recent analysis and read it:
  ```bash
  ls -t .motiscope/*/manifest.json 2>/dev/null | head -1
  ```
  `Read` that `manifest.json` (and its sibling `motion.json` for the raw energy curve / segments). If there is none, run `/motiscope:analyze` first.

## Step 2 — choose the target

- From `$1` if given (`gsap` | `css` | `framer` | `lottie`).
- Otherwise read the default and ask:
  ```bash
  python3 "$SCRIPTS/config.py"   # prints config incl. default_target
  ```
  Use `AskUserQuestion` to confirm the target (offer all four; default from config).

Then `Read` the target guide and the easing map:
- `Read "$REFS/easing-map.md"` — maps each neutral ease token to a concrete value in every target.
- `Read "$REFS/targets/<target>.md"` — the rendering template for that target.

## Step 3 — generate the code

Map the neutral spec to the target using the easing map, one timeline entry at a time (per-element `from`/`to`, `dur_ms`, `start_ms`/position, ease token, stagger).

**GSAP defers to the official GSAP skills** — do not hand-roll GSAP guidance:
- Invoke **gsap-timeline** to build the sequence (position parameter, nesting).
- Invoke **gsap-core** for individual tweens, eases, and defaults.
- Invoke **gsap-scrolltrigger** *only if* the spec has `"scroll_driven": true`.
- Invoke **gsap-react** if the user's project is React/Next.
- Invoke **gsap-utils** for stagger / interpolation helpers.
Your job is to feed those skills the exact inputs from the spec; theirs is to produce idiomatic GSAP.

For **css**, **framer**, **lottie**, follow the corresponding `references/targets/<target>.md` template.

Always include a `prefers-reduced-motion: reduce` guard that drops the element(s) into their final state.

## Step 4 — asset check (consent flow)

If the spec references an image/video asset (a hero image, a looping background, a texture), resolve it **before** writing code with `AskUserQuestion`:
1. **Point at an existing file** the user already has (preferred) — wire its path in.
2. **Generate one** — check what's configured, then generate:
   ```bash
   python3 "$SCRIPTS/assetgen.py" --check
   python3 "$SCRIPTS/assetgen.py" generate --type image --provider <name> --prompt "<desc>" --out "<path>"
   ```
   If no key is configured, `AskUserQuestion` for the provider and hand off to `/motiscope:doctor` to store the key. **Image generation is real via the `gemini`/`imagen` provider** (Imagen through the Gemini API — set `GEMINI_API_KEY`); pass `--aspect-ratio 16:9|4:3|1:1|3:4|9:16`. Other providers still write a labeled placeholder — if you get one, tell the user to use `gemini` or swap in a real asset.
3. **Use a placeholder** — a neutral colored box, and note it.

Never write API keys into generated code or commit them.

## Step 5 — write the output

Write to `[output-dir]` (`$2`), default `./motiscope-output/<target>/`. Include a **minimal runnable harness** so the user can preview immediately:
- **gsap / css** → a self-contained `index.html` (CDN GSAP for the gsap target) that plays the animation on load.
- **framer** → a `.tsx` component plus a one-line usage note (and the `framer-motion` install command).
- **lottie** → the animated SVG (or `.json`) plus a note on how to embed/play it.

## Step 6 — tell the user how to preview + what to tune

- Give the exact preview step (e.g. "open `motiscope-output/css/index.html`").
- List which values are **exact** (timing, easing, sequence — measured) vs **estimated** (transform magnitudes, colors, overshoot — eyeballed from frames) so they know precisely what to nudge. Offer to iterate.
