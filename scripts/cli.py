#!/usr/bin/env python3
"""motiscope — the platform-neutral command line.

Claude Code reaches the pipeline through ${CLAUDE_PLUGIN_ROOT}/scripts/*.py. Every
other agent (Codex, Cursor, anything that can run a shell) reaches it through this
single `motiscope` command, so no agent has to know where motiscope is installed.

    motiscope analyze <video> [--preset ...]   measure motion, curate keyframes
    motiscope doctor  [--check|--json]         verify ffmpeg/ffprobe, scaffold config
    motiscope assets  --check | generate ...   optional image generation
    motiscope config                           print resolved config + provider status
    motiscope home                             print the motiscope install root
    motiscope install <platform>               install agent instructions for a platform
    motiscope version

Stdlib only. `recreate` and `rebuild-site` have no subcommand on purpose: they are
agent work (write code from the spec), not scripts.
"""
from __future__ import annotations

import os
import runpy
import shutil
import sys
from pathlib import Path

__version__ = "1.0.0"

# Markers used to keep an appended AGENTS.md block idempotently updatable.
BLOCK_START = "<!-- motiscope:start -->"
BLOCK_END = "<!-- motiscope:end -->"


def home() -> Path:
    """The motiscope install root (the repo/plugin directory containing scripts/)."""
    env = os.environ.get("MOTISCOPE_HOME")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "scripts" / "ingest.py").exists():
            return p
        raise SystemExit(f"MOTISCOPE_HOME={env} does not contain scripts/ingest.py")
    # cli.py lives at <root>/scripts/cli.py. resolve() follows the bin/ symlink.
    return Path(__file__).resolve().parent.parent


def _scripts() -> Path:
    return home() / "scripts"


def _delegate(module: str, argv: list[str]) -> int:
    """Run one of the pipeline scripts in-process, so tracebacks stay readable."""
    sys.path.insert(0, str(_scripts()))
    mod = __import__(module)
    if hasattr(mod, "main"):
        return int(mod.main(argv) or 0)
    # config.py has no main() — it just prints on __main__.
    sys.argv = [module] + argv
    runpy.run_path(str(_scripts() / f"{module}.py"), run_name="__main__")
    return 0


# --------------------------------------------------------------------------- install

def _targets() -> dict:
    """Where each agent looks for skills. The SKILL.md files themselves are identical —
    only the mount point differs.

    Codex  ~/.agents/skills/    https://developers.openai.com/codex/skills
    Cursor <project>/.cursor/skills/  https://cursor.com/help/customization/skills
    """
    ints = home() / "integrations"
    return {
        "codex": {
            "blurb": "portable skills -> ~/.agents/skills/",
            "skills": Path.home() / ".agents" / "skills",
            "after": ["Codex picks skills up implicitly, or mention one with $motiscope-analyze.",
                      "Codex moved this directory between versions. If it doesn't see the",
                      "skills, copy them to ~/.codex/skills/ or <repo>/.codex/skills/ —",
                      "or re-run with: motiscope install skills --dir <path>"],
        },
        "cursor": {
            "blurb": "portable skills + project rule -> ./.cursor/",
            "skills": "{dest}/.cursor/skills",
            "copy": [(ints / "cursor" / "rules", "{dest}/.cursor/rules")],
            "after": ["Invoke with /motiscope-analyze, or @-mention a skill."],
        },
        "agents": {
            "blurb": "AGENTS.md block -> ./AGENTS.md (Zed, Amp, opencode, Gemini CLI, ...)",
            "block": (ints / "agents" / "AGENTS.motiscope.md", "{dest}/AGENTS.md"),
            "after": ["Read by ~20 agents. Use this when your agent has no skills directory."],
        },
        "skills": {
            "blurb": "portable skills -> --dir <path> (any agent-skills directory)",
            "skills": None,  # requires --dir
        },
    }


def _install_block(src: Path, dest: Path, dry: bool) -> list[str]:
    """Insert or replace the motiscope block in an AGENTS.md, leaving the rest alone."""
    body = f"{BLOCK_START}\n{src.read_text().strip()}\n{BLOCK_END}\n"
    if dest.exists():
        cur = dest.read_text()
        if BLOCK_START in cur and BLOCK_END in cur:
            head, _, tail = cur.partition(BLOCK_START)
            _, _, tail = tail.partition(BLOCK_END)
            new, verb = head + body + tail.lstrip("\n"), "updated block in"
        else:
            new, verb = cur.rstrip("\n") + "\n\n" + body, "appended block to"
    else:
        new, verb = body, "created"
    if not dry:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(new)
    return [f"{verb} {dest}"]


def _copy_tree(src: Path, dst: Path, force: bool, dry: bool) -> list[str]:
    if dst.exists() and not force:
        return [f"skipped {dst} (exists; --force to overwrite)"]
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    return [f"wrote {dst}/"]


def _install(platform: str, dest: Path, skills_dir: Path | None, force: bool, dry: bool) -> int:
    targets = _targets()
    if platform in ("list", "help"):
        print("Install motiscope's instructions into an agent:\n")
        for name, spec in targets.items():
            print(f"  motiscope install {name:<7} {spec['blurb']}")
        print("\n  Claude Code: install as a plugin instead —")
        print("    /plugin marketplace add github:KumarSashank/motiscope")
        print("    /plugin install motiscope@motiscope")
        return 0
    if platform not in targets:
        print(f"error: unknown platform {platform!r}. Try: {', '.join(targets)}, list",
              file=sys.stderr)
        return 2

    spec, done = targets[platform], []
    src_skills = home() / "integrations" / "skills"

    if "skills" in spec:
        target = skills_dir or spec["skills"]
        if target is None:
            print("error: 'install skills' needs --dir <path>", file=sys.stderr)
            return 2
        target = Path(str(target).format(dest=dest)).expanduser()
        if not src_skills.is_dir():
            print(f"error: missing {src_skills} — run scripts/build_integrations.py",
                  file=sys.stderr)
            return 1
        for skill in sorted(p for p in src_skills.iterdir() if p.is_dir()):
            done += _copy_tree(skill, target / skill.name, force, dry)

    if "block" in spec:
        src, dst = spec["block"]
        done += _install_block(src, Path(str(dst).format(dest=dest)), dry)

    for src_dir, dst_tpl in spec.get("copy", []):
        dst_dir = Path(str(dst_tpl).format(dest=dest)).expanduser()
        for src in sorted(src_dir.iterdir()):
            dst = dst_dir / src.name
            if dst.exists() and not force:
                done.append(f"skipped {dst} (exists; --force to overwrite)")
                continue
            if not dry:
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            done.append(f"wrote {dst}")

    for line in done:
        print(("[dry-run] " if dry else "") + line)
    if not dry:
        print(f"\nmotiscope installed for {platform}. Restart the agent to pick it up.")
        for line in spec.get("after", []):
            print(f"  {line}")
    return 0


# --------------------------------------------------------------------------- main

USAGE = """motiscope — see the motion, recreate the animation.

usage: motiscope <command> [args]

  analyze <video> [flags]     measure motion + extract curated keyframes
                              flags: --preset draft|balanced|detailed|landing
                                     --start T --end T --fps N --frame-budget N
                                     --resolution W --format png|jpg --out DIR
                                     --decompose | --no-decompose | --no-dedup
  doctor [--check|--json]     verify ffmpeg/ffprobe, scaffold config
  assets --check              show which provider keys are set (booleans only)
  assets generate ...         --type image --provider gemini --prompt P --out F
                                     [--aspect-ratio 1:1|3:4|4:3|9:16|16:9]
  config                      print resolved config + provider status
  install <platform>          teach an agent the workflows
                              codex | cursor | agents | skills --dir P | list
                              flags: --dest DIR --force --dry-run
  home                        print the motiscope install root
  version

`recreate` and `rebuild-site` are agent workflows, not scripts — they live in your agent
as skills. Run `motiscope install list` to add them.

Docs: https://github.com/KumarSashank/motiscope"""


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd, rest = argv[0], argv[1:]

    if cmd in ("-V", "--version", "version"):
        print(f"motiscope {__version__}")
        return 0
    if cmd == "home":
        print(home())
        return 0
    if cmd == "install":
        dest, force, dry, platform, skills_dir = Path.cwd(), False, False, None, None
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "--dest":
                dest = Path(rest[i + 1]).expanduser(); i += 2
            elif a == "--dir":
                skills_dir = Path(rest[i + 1]).expanduser(); i += 2
            elif a == "--force":
                force = True; i += 1
            elif a == "--dry-run":
                dry = True; i += 1
            elif not a.startswith("-"):
                platform = a; i += 1
            else:
                print(f"error: unknown flag {a!r}", file=sys.stderr); return 2
        return _install(platform or "list", dest, skills_dir, force, dry)

    delegates = {"analyze": "ingest", "doctor": "mvsetup", "assets": "assetgen",
                 "config": "config", "frames": "extract_frames", "motion": "analyze_motion"}
    if cmd in delegates:
        return _delegate(delegates[cmd], rest)

    print(f"error: unknown command {cmd!r}\n\n{USAGE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
