---
name: motiscope-doctor
description: 'Check and configure motiscope — verify ffmpeg/ffprobe are installed and scaffold the API-key config used for optional (stubbed) asset generation. Use for first-time setup, "motiscope isn''t working", dependency errors, or `motiscope-doctor`.'
---

# motiscope: doctor

> Check and configure motiscope — verify ffmpeg/ffprobe are installed and scaffold the API-key config used for optional (stubbed) asset generation. Use for first-time setup, "motiscope isn't working", dependency errors, or `motiscope-doctor`.


## Running motiscope

`motiscope` is a shell command. If it isn't found it isn't on your PATH — see
https://github.com/KumarSashank/motiscope#install. The reference guides live under
`$(motiscope home)/references/`.

**Invoking the sibling skills.** In Codex, mention a skill with `$motiscope-recreate`. In
Cursor, use `/motiscope-recreate`. Elsewhere, just follow that skill's `SKILL.md`.

**Seeing the frames — do not skip this.** The curated keyframes are PNG files on disk, and
you must actually look at them. Codex: use the `view_image` tool (if it's unavailable,
enable `tools.view_image = true` in `~/.codex/config.toml`, or have the user relaunch with
`codex -i frame1.png,frame2.png`). Cursor: the file-reading tool accepts `.png` and puts
the image in context. If you genuinely cannot open images, **say so** — you can still
report the measured timing, but you cannot know *what* is animating, and you must not
guess it from the filenames.

Verify dependencies and scaffold config. motiscope's pipeline is pure Python
standard library, so the only hard dependencies are **ffmpeg** and **ffprobe**.


## Run status

```bash
motiscope doctor --json
```

The JSON reports `status`, `missing_binaries`, `install_hint`, `platform`, `config_file`, `env_file`, and per-provider key presence.

## If ffmpeg/ffprobe are missing

Do **not** install silently. Ask the user for permission, then run the platform command:

- **macOS (Homebrew):** `brew install ffmpeg`
- **Linux:** `sudo apt-get install -y ffmpeg` (or `sudo dnf install ffmpeg`)
- **Windows:** `winget install Gyan.FFmpeg` (or `choco install ffmpeg`)

Re-run `mvsetup.py --check` afterward to confirm (exit 0 = ready).

## Scaffold config

```bash
motiscope doctor
```

This creates, if absent:
- `~/.config/motiscope/config.json` — non-secret preferences (`default_target`, `frame_budget`, `resolution`, `frame_format`, `image_provider`, `video_provider`).
- `~/.config/motiscope/.env` (mode `0600`) — **optional** API keys for asset generation, commented out by default.

## API keys (optional)

Asset generation (creating an image an animation needs) is **optional** — no key is required for analysis or code recreation. Image generation is real for **Gemini/Imagen**; the other providers write a labeled placeholder until wired. To configure one, ask the user which provider, and write the key into `~/.config/motiscope/.env`:

| Purpose | Providers (env var) |
|---|---|
| Image | **Gemini/Imagen (`GEMINI_API_KEY`) — implemented**; OpenAI (`OPENAI_API_KEY`), Stability (`STABILITY_API_KEY`), Replicate (`REPLICATE_API_TOKEN`), fal (`FAL_KEY`) |
| Video | Runway (`RUNWAY_API_KEY`), Replicate (`REPLICATE_API_TOKEN`), fal (`FAL_KEY`) |

Image generation works today with **`gemini`** (Imagen). Other providers write a
labeled placeholder until wired.

Reassure the user: keys stay in a local `0600` file, are never printed, never written into generated code, and never committed (the repo `.gitignore` excludes `.env`).

## Report back

Summarize: dependency status, what was scaffolded, and whether any provider keys are configured. If everything is ready, say so in one line and point them at ``motiscope-analyze``.
