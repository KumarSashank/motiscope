#!/usr/bin/env python3
"""Generate the portable agent instructions from skills/*/SKILL.md.

The Claude Code SKILL.md files are the single source of truth. Everything else is
derived from them, so a fix to the analysis workflow lands everywhere at once instead
of drifting across a copy per platform.

    python3 scripts/build_integrations.py            # write integrations/
    python3 scripts/build_integrations.py --check    # exit 1 if anything is stale

Why one portable skill set instead of per-platform command files: Codex and Cursor both
consume the same `<name>/SKILL.md` shape (the vendor-neutral agentskills.io convention),
reading only `name` + `description` from the frontmatter. They differ solely in *where*
the directory is mounted, which is `motiscope install`'s job — not this script's.
  Codex  https://developers.openai.com/codex/skills
  Cursor https://cursor.com/help/customization/skills

Three things are rewritten on the way out:
  1. The Claude-Code-only preamble (<!-- motiscope:preamble:* -->) becomes a portable
     "how to run motiscope" note built on the `motiscope` CLI.
  2. Claude-only blocks (<!-- motiscope:claude-only:<key>:* -->) are swapped for the
     text in PORTABLE — e.g. Claude Code ships official gsap-* skills; nothing else does.
  3. Claude tool names and `/motiscope:x` command syntax are neutralized.

The drift check then asserts no Claude-specific token survived, so if someone adds a new
`$SCRIPTS/foo.py` call and forgets to map it, the build fails loudly instead of shipping
an instruction no other agent can follow.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
OUT = ROOT / "integrations"
ORDER = ["analyze", "recreate", "rebuild-site", "doctor"]

PREAMBLE_RE = re.compile(
    r"<!-- motiscope:preamble:start -->.*?<!-- motiscope:preamble:end -->\n?", re.S)
CLAUDE_ONLY_RE = re.compile(
    r"<!-- motiscope:claude-only:([\w-]+):start -->\n?.*?"
    r"<!-- motiscope:claude-only:\1:end -->\n?", re.S)

PORTABLE = {
    # Claude Code ships the official gsap-* skills; no other agent has them.
    "gsap-skills": (
        "For **GSAP**, write idiomatic GSAP yourself: build the sequence with a "
        "`gsap.timeline()` and the position parameter, register a `CustomEase` for each "
        "measured `cubic-bezier`, use `stagger` for the measured `each_ms`, and reach for "
        "`ScrollTrigger` **only if** the spec has `\"scroll_driven\": true`. The rendering "
        "template in `$(motiscope home)/references/targets/gsap.md` has the patterns.\n"),
}

# Turns the bundled-script calls into the portable CLI. Applied in order.
SCRIPT_SUBS = [
    ('python3 "$SCRIPTS/ingest.py"', "motiscope analyze"),
    ('python3 "$SCRIPTS/mvsetup.py"', "motiscope doctor"),
    ('python3 "$SCRIPTS/assetgen.py"', "motiscope assets"),
    ('python3 "$SCRIPTS/config.py"', "motiscope config"),
    ('"$REFS/', '"$(motiscope home)/references/'),
    ("$REFS/", "$(motiscope home)/references/"),
]

# Nothing from this list may survive into a generated file.
FORBIDDEN = ["CLAUDE_PLUGIN_ROOT", "$SCRIPTS", "$REFS", "`Read`", "AskUserQuestion",
             "/motiscope:", "motiscope:claude-only", "motiscope:preamble",
             "gsap-timeline", "gsap-scrolltrigger", 'Read "']

RUN_NOTE = """## Running motiscope

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
"""


def _yaml_quote(s: str) -> str:
    """Single-quoted YAML scalar — the descriptions contain `:` and `"`."""
    return "'" + s.replace("'", "''") + "'"


def parse_skill(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        raise SystemExit(f"{path}: missing frontmatter")
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return {"name": meta["name"], "description": meta["description"],
            "hint": meta.get("argument-hint", ""), "body": body.strip()}


def strip_claude_only(text: str) -> str:
    def sub(m):
        key = m.group(1)
        if key not in PORTABLE:
            raise SystemExit(f"error: claude-only block {key!r} has no PORTABLE "
                             f"replacement in build_integrations.py")
        return PORTABLE[key]
    return CLAUDE_ONLY_RE.sub(sub, text)


def retarget(text: str) -> str:
    """Rewrite Claude-Code tool names, command syntax, and bundled script paths."""
    # `Read "$REFS/x.md"` is a Claude tool call, not a shell command — unwrap it so it
    # doesn't survive as a bogus backticked command.
    text = re.sub(r'`Read "\$REFS/([^"]+)"`',
                  r'read `$(motiscope home)/references/\1`', text)
    for old, new in SCRIPT_SUBS:
        text = text.replace(old, new)
    # `/motiscope:recreate` -> `motiscope-recreate` (Codex says $name, Cursor says /name,
    # so name the skill and let RUN_NOTE explain each platform's prefix).
    text = re.sub(r"/motiscope:([a-z-]+)", r"`motiscope-\1`", text)
    # AskUserQuestion is annotated parenthetically in the skills precisely so that
    # deleting it here always leaves a grammatical sentence.
    text = re.sub(r" ?\(`AskUserQuestion`\)", "", text)
    # "Read" is plain English everywhere; only the Claude tool name is backticked.
    text = text.replace("`Read`", "Read")
    return text


def render_skill(skill: dict) -> str:
    body = PREAMBLE_RE.sub("", skill["body"])
    body = strip_claude_only(body)
    body = re.sub(r"^#\s+motiscope:.*?\n+", "", body, count=1)  # we re-add the header
    body = retarget(body)
    body = body.replace(
        "On **Windows** use `python` instead of `python3` in every command below.", "")

    desc = retarget(skill["description"])
    hint = skill["hint"]
    args = (f"**Arguments** (`{hint}`): take them from the user's message. If they're "
            f"missing, infer them or ask.\n" if hint else "")
    return (f"---\nname: motiscope-{skill['name']}\ndescription: {_yaml_quote(desc)}\n---\n\n"
            f"# motiscope: {skill['name']}\n\n> {desc}\n\n{args}\n{RUN_NOTE}\n{body.strip()}\n")


def render_agents_md(skills: list[dict]) -> str:
    rows = "\n".join(
        f"| `motiscope-{s['name']}` | {retarget(s['description']).split('.')[0].strip()}. |"
        for s in skills)
    return f"""## motiscope — recreate animations from screen recordings

[motiscope](https://github.com/KumarSashank/motiscope) turns a screen recording of an
animation into working web-animation code. It measures the one thing a screenshot cannot
show — **time** — and leaves perception to you.

### The division of labor

- **The numbers measure the WHEN.** `motiscope analyze` emits exact durations, per-segment
  easing as a real `cubic-bezier` fitted from the velocity profile, beat boundaries,
  stagger timing, and loop period. Copy these verbatim; never re-estimate them from frames.
- **You supply the WHAT.** motiscope curates a handful of keyframe PNGs and deliberately
  does **not** classify animation types. Look at the frames and name what you actually
  see — a mask reveal, a path draw, a morph, a 3D flip, a text split, particles, anything.

### Commands

```bash
motiscope doctor                       # verify ffmpeg + ffprobe (the only dependencies)
motiscope analyze <video> [--preset balanced|draft|detailed|landing]
motiscope home                         # reference guides live under $(motiscope home)/references/
```

`analyze` writes `.motiscope/<slug>/` containing `report.md` (the measured timing),
`motion.json` (the raw energy curve), and `frames/*.png`. Read the report, then **look at
every frame**, then build the animation. Local video files only — motiscope never
downloads URLs.

### Workflows

| Skill | What it does |
|---|---|
{rows}

Only the frames cost image tokens (~300–400 each); the numeric analysis is free. Frame
count tracks motion complexity, not video length. Recreation targets: GSAP, CSS/Web
Animations, Framer Motion, Lottie/SVG. Always include a `prefers-reduced-motion` guard.
"""


def render_cursor_rule(skills: list[dict]) -> str:
    # alwaysApply: false + description (no globs) = Cursor's "Apply Intelligently" mode.
    # https://cursor.com/docs/context/rules
    return (f"---\ndescription: motiscope — measure and recreate animations from screen "
            f"recordings\nalwaysApply: false\n---\n\n{render_agents_md(skills).strip()}\n")


def build() -> dict[Path, str]:
    skills = [parse_skill(SKILLS / n / "SKILL.md") for n in ORDER]
    files: dict[Path, str] = {}
    for s in skills:
        files[OUT / "skills" / f"motiscope-{s['name']}" / "SKILL.md"] = render_skill(s)
    files[OUT / "agents" / "AGENTS.motiscope.md"] = render_agents_md(skills)
    files[OUT / "cursor" / "rules" / "motiscope.mdc"] = render_cursor_rule(skills)
    return files


def main(argv: list[str]) -> int:
    files = build()

    problems = [f"{p.relative_to(ROOT)}: leaked {t!r}"
                for p, c in files.items() for t in FORBIDDEN if t in c]
    if problems:
        print("error: generated files contain Claude-Code-specific tokens:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\nAdd a mapping in SCRIPT_SUBS/PORTABLE/retarget() in build_integrations.py.",
              file=sys.stderr)
        return 1

    if "--check" in argv:
        stale = [str(p.relative_to(ROOT)) for p, c in files.items()
                 if not p.exists() or p.read_text() != c]
        if stale:
            print("error: integrations are stale — run scripts/build_integrations.py",
                  file=sys.stderr)
            for s in stale:
                print(f"  {s}", file=sys.stderr)
            return 1
        print(f"integrations up to date ({len(files)} files)")
        return 0

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    print(f"wrote {len(files)} files under {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
