# motiscope — Quickstart

Recreate a web animation from a screen recording, in ~2 minutes.

## 1. Install

In a Claude Code session:

```
/plugin marketplace add github:KumarSashank/motiscope
/plugin install motiscope@motiscope
```

If the `/motiscope:*` commands don't appear, run `/plugin` to confirm it's enabled,
or restart the session.

## 2. Check dependencies

```
/motiscope:doctor
```

motiscope needs `ffmpeg` + `ffprobe` (nothing else — the pipeline is pure Python
stdlib). On macOS the doctor installs them with your consent (`brew install ffmpeg`).

## 3. Give it a video

**Option A — a real animation:** screen-record an animation you like (any
`.mp4/.mov/.webm/.mkv/.m4v/.avi`), then:

```
/motiscope:analyze path/to/recording.mp4
```

**Option B — try the built-in sample clips first:**

```
bash "$(dirname "$(command -v motiscope 2>/dev/null)")"/tests/make_test_clip.sh   # or just run tests/make_test_clip.sh from a clone
/motiscope:analyze tests/test-ease.mp4
```

**Tip:** drop recordings into an `animations/` folder in your project and just run
`/motiscope:analyze` — it finds them, and the session hook announces them.

## 4. Recreate it as code

```
/motiscope:recreate gsap      # or: css | framer | lottie
```

Open the generated file (e.g. `motiscope-output/css/index.html`) to preview.

## Controlling frames & token cost

The frames the model *sees* are the only token cost; the motion analysis is free.
Frame count tracks motion complexity (not video length) and is capped by a preset:

| Preset | Frames | Resolution | Use when |
|---|---|---|---|
| `draft` | 12 | 512px | quick look |
| `balanced` (default) | 32 | 640px | most cases |
| `detailed` | 48 | 960px | dense sequences / reading text |

- **Long clip?** Focus a section: `--start 0:12 --end 0:15` (auto-decompose also
  spends frames on the motion beats and skips holds).
- **Fast motion?** Sample densely: `--fps 20` within a short window.

(These flags pass through `/motiscope:analyze`, e.g. `… --preset detailed --start 0:12 --end 0:15`.)

## Troubleshooting

- **"needs ffmpeg + ffprobe"** → run `/motiscope:doctor`.
- **Commands missing after install** → `/plugin` to verify enabled; restart session.
- **A gentle ease-in shows a short leading hold** → expected; very slow sub-pixel
  motion is invisible in the analysis thumbnails. The dominant easing is still correct.
- **PNG frames look huge / gradient-heavy clip** → add `--format jpg`.

Full docs in [README.md](README.md).
