# Running motiscope on any agent

motiscope is two things:

1. **A measurement tool** — `motiscope`, a stdlib-only Python CLI that shells out to
   `ffmpeg`. It measures the *timing* of an animation and curates the keyframes worth
   looking at. It has no idea which agent is calling it.
2. **A set of workflows** — instructions telling an agent how to use that output: read
   the measured timing, look at the frames, write the animation code.

Only the second part is platform-specific, and only because each agent keeps its
instructions in a different directory. The workflows themselves are one set of files,
generated from `skills/*/SKILL.md`, mounted wherever your agent looks.

## Support matrix

| Platform | Install | Invoke | Can it see the frames? |
|---|---|---|---|
| **Claude Code** | `/plugin install motiscope@motiscope` | `/motiscope:analyze` | Yes — the `Read` tool |
| **Codex CLI** | `motiscope install codex` | implicit, or `$motiscope-analyze` | Yes — the `view_image` tool |
| **Cursor** | `motiscope install cursor` | `/motiscope-analyze` | Yes — its file-read tool accepts `.png` |
| **Anything reading `AGENTS.md`**<br>(Zed, Amp, opencode, Gemini CLI, Copilot, Aider, …) | `motiscope install agents` | ask in plain language | Depends on the agent |
| **Any other agent-skills dir** | `motiscope install skills --dir <path>` | per that agent | Depends on the agent |

**Seeing the frames is not optional.** motiscope measures *when* things happen; only the
model can see *what* is happening. An agent that can't open a PNG can still report the
measured timing, but it cannot identify the elements or the kind of animation — and the
workflows tell it to say so rather than guess.

## Requirements

`python3` (3.8+), `ffmpeg` + `ffprobe`, and an agent that can run shell commands. No npm,
no pip, no server, no account. Run `motiscope doctor` to check.

## Install the CLI

```sh
git clone https://github.com/KumarSashank/motiscope.git ~/.motiscope
~/.motiscope/install.sh          # symlinks bin/motiscope into ~/.local/bin
motiscope doctor                 # verify ffmpeg + ffprobe
```

`install.sh` creates exactly one symlink and never uses sudo. Set `MOTISCOPE_BIN_DIR` to
link somewhere else, or skip it and put `~/.motiscope/bin` on your `PATH` yourself.
Windows: use `bin\motiscope.cmd`.

**Claude Code users don't need this.** The plugin bundles the scripts; install it with
`/plugin marketplace add github:KumarSashank/motiscope`.

## Then teach your agent

```sh
motiscope install list                    # show every target
motiscope install codex                   # -> ~/.agents/skills/
motiscope install cursor                  # -> ./.cursor/skills/ + ./.cursor/rules/
motiscope install agents                  # -> ./AGENTS.md (a marked, re-updatable block)
motiscope install skills --dir <path>     # -> anywhere else

# flags: --dest DIR (project root, default cwd) --force (overwrite) --dry-run
```

`install agents` writes between `<!-- motiscope:start -->` / `<!-- motiscope:end -->`
markers, so re-running it updates the block and leaves the rest of your `AGENTS.md`
untouched. Nothing else is overwritten without `--force`.

## The CLI

```
motiscope analyze <video> [--preset draft|balanced|detailed|landing]
                          [--start T] [--end T] [--fps N] [--frame-budget N]
                          [--resolution W] [--format png|jpg] [--out DIR]
                          [--decompose|--no-decompose] [--no-dedup]
motiscope doctor [--check|--json]      verify deps; scaffold ~/.config/motiscope/
motiscope assets --check               which provider keys are set (booleans only)
motiscope assets generate --type image --provider gemini --prompt P --out F
motiscope config                       resolved config + provider status
motiscope home                         install root (references/ lives here)
motiscope install <platform>           see above
```

`analyze` writes `.motiscope/<slug>/`: `report.md` (measured timing), `motion.json` (the
raw energy curve and segments), and `frames/*.png`. That directory is the whole contract
between the tool and the agent — any agent that can read a file and view a PNG can do the
rest.

There is no `motiscope recreate` subcommand, and that's deliberate: recreation is the
model writing code, not a script. It lives in the workflows.

## Version caveats (read this before filing a bug)

These are moving targets. motiscope reports what the official docs said when it shipped;
your installed version may differ.

- **Codex's skills directory moved.** The current docs describe `.agents/skills/`
  (scanned from the working directory up, plus `~/.agents/skills/`), while the `openai/codex`
  repo itself uses `.codex/skills/`. `motiscope install codex` writes to `~/.agents/skills/`.
  If Codex doesn't see the skills, copy them: `motiscope install skills --dir ~/.codex/skills`.
- **Codex custom prompts (`~/.codex/prompts/`) are deprecated** in favour of skills, and
  had a loading regression around `codex-cli` 0.117.0. motiscope does not use them.
- **Codex's `view_image` default is undocumented.** If the agent says it can't open the
  frames, set `tools.view_image = true` in `~/.codex/config.toml`, or relaunch with
  `codex -i frame1.png,frame2.png "..."`.
- **Cursor's slash-command argument grammar isn't specified** (only a `/fix-issue [number]`
  example). The workflows therefore take arguments from your message rather than relying
  on substitution.
- **`AGENTS.md` precedence differs per tool.** The standard says "nearest file wins";
  Codex concatenates root→cwd and adds its own `~/.codex` layer. If motiscope's block
  seems ignored, check for a closer `AGENTS.md`.

Sources: [Codex skills](https://developers.openai.com/codex/skills),
[Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
[Cursor skills](https://cursor.com/help/customization/skills),
[Cursor rules](https://cursor.com/docs/context/rules),
[agents.md](https://agents.md/).

## Adding a platform

Don't hand-write instruction files — they'd drift from the skills within a release.
`skills/*/SKILL.md` is the single source of truth; `scripts/build_integrations.py`
generates everything under `integrations/`.

```sh
python3 scripts/build_integrations.py           # regenerate
python3 scripts/build_integrations.py --check   # fail if stale (runs in CI)
```

The generator strips the Claude-Code-only preamble, swaps blocks marked
`<!-- motiscope:claude-only:<key> -->` for portable equivalents (Claude Code ships the
official `gsap-*` skills; nothing else does), rewrites `${CLAUDE_PLUGIN_ROOT}` script
calls into `motiscope ...` commands, and then **asserts that no Claude-specific token
survived**. If you add a new bundled-script call and forget to map it, the build fails
rather than shipping an instruction other agents can't follow.

To add a platform, most of the time you only need a new entry in `_targets()` in
`scripts/cli.py` pointing at that agent's skills directory. Add a new generated *format*
only if the agent can't read a `name` + `description` `SKILL.md`.
