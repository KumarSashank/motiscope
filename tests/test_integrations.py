#!/usr/bin/env python3
"""Tests for the portable CLI and the generated per-platform instructions.

The point of these: the generated files are the *only* thing agents other than Claude
Code ever read. If a Claude-only token leaks into them, that agent gets an instruction
it cannot follow — and nothing at runtime would catch it.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_integrations as bi  # noqa: E402
import cli  # noqa: E402

MOTISCOPE = [sys.executable, str(ROOT / "bin" / "motiscope")]


def run(*args, **kw):
    return subprocess.run(MOTISCOPE + list(args), capture_output=True, text=True, **kw)


class TestGeneratedIntegrations(unittest.TestCase):
    def test_committed_files_match_the_skills(self):
        """integrations/ is generated — a SKILL.md edit must be rebuilt and committed."""
        self.assertEqual(bi.main(["--check"]), 0,
                         "run: python3 scripts/build_integrations.py")

    def test_no_claude_only_tokens_leak(self):
        for path, content in bi.build().items():
            for token in bi.FORBIDDEN:
                self.assertNotIn(token, content, f"{path.name} leaked {token!r}")

    def test_every_skill_is_rendered(self):
        names = {p.parent.name for p in bi.build() if p.name == "SKILL.md"}
        self.assertEqual(names, {f"motiscope-{n}" for n in bi.ORDER})

    def test_portable_skill_frontmatter(self):
        """Codex and Cursor read only `name` + `description`; both must be present."""
        for path, content in bi.build().items():
            if path.name != "SKILL.md":
                continue
            self.assertTrue(content.startswith("---\n"), path)
            fm = content.split("---", 2)[1]
            self.assertIn("name: motiscope-", fm)
            self.assertIn("description: ", fm)
            self.assertEqual(fm.count("\nname:"), 1, f"{path}: duplicate name key")

    def test_claude_only_block_without_replacement_fails_loudly(self):
        with self.assertRaises(SystemExit):
            bi.strip_claude_only(
                "<!-- motiscope:claude-only:nonexistent:start -->x"
                "<!-- motiscope:claude-only:nonexistent:end -->")

    def test_retarget_rewrites_scripts_and_commands(self):
        out = bi.retarget('python3 "$SCRIPTS/ingest.py" v.mp4 then /motiscope:recreate')
        self.assertIn("motiscope analyze v.mp4", out)
        self.assertIn("`motiscope-recreate`", out)
        self.assertNotIn("$SCRIPTS", out)

    def test_askuserquestion_annotation_leaves_grammar_intact(self):
        self.assertEqual(bi.retarget("Ask the user (`AskUserQuestion`) which one."),
                         "Ask the user which one.")

    def test_read_refs_becomes_a_path_not_a_shell_command(self):
        out = bi.retarget('- `Read "$REFS/easing-map.md"` — the map.')
        self.assertIn("read `$(motiscope home)/references/easing-map.md`", out)


class TestCli(unittest.TestCase):
    def test_version_and_home(self):
        self.assertEqual(run("version").stdout.strip(), f"motiscope {cli.__version__}")
        self.assertEqual(Path(run("home").stdout.strip()), ROOT)

    def test_unknown_command_exits_2(self):
        self.assertEqual(run("bogus").returncode, 2)

    def test_help_lists_the_commands(self):
        out = run("--help").stdout
        for cmd in ("analyze", "doctor", "assets", "install", "home"):
            self.assertIn(cmd, out)

    def test_bad_motiscope_home_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(MOTISCOPE + ["home"], capture_output=True, text=True,
                               env={"MOTISCOPE_HOME": tmp, "PATH": "/usr/bin:/bin"})
            self.assertNotEqual(r.returncode, 0)

    def test_install_skills_requires_a_dir(self):
        self.assertEqual(run("install", "skills").returncode, 2)

    def test_install_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("install", "cursor", "--dest", tmp, "--dry-run")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_install_cursor_lands_skills_and_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("install", "cursor", "--dest", tmp).returncode, 0)
            root = Path(tmp) / ".cursor"
            self.assertTrue((root / "skills" / "motiscope-analyze" / "SKILL.md").is_file())
            self.assertTrue((root / "rules" / "motiscope.mdc").is_file())

    def test_install_agents_block_is_idempotent_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            agents.write_text("# Mine\n\nKeep me.\n")
            for _ in range(2):
                self.assertEqual(run("install", "agents", "--dest", tmp).returncode, 0)
            text = agents.read_text()
            self.assertIn("Keep me.", text)
            self.assertEqual(text.count(cli.BLOCK_START), 1)
            self.assertEqual(text.count(cli.BLOCK_END), 1)

    def test_install_does_not_clobber_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("install", "cursor", "--dest", tmp)
            skill = Path(tmp) / ".cursor" / "skills" / "motiscope-analyze" / "SKILL.md"
            skill.write_text("EDITED")
            run("install", "cursor", "--dest", tmp)
            self.assertEqual(skill.read_text(), "EDITED")
            run("install", "cursor", "--dest", tmp, "--force")
            self.assertNotEqual(skill.read_text(), "EDITED")


if __name__ == "__main__":
    unittest.main()
