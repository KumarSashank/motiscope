#!/usr/bin/env python3
"""docs/how-it-works.md promises that its constants match the code.

    "If they drift, the code is right and this file is wrong."

That is a promise, and a promise nobody checks is a lie with a delay. This module reads
the real values out of the pipeline modules and fails if the doc disagrees — so changing
`HOLD_ENERGY_FRACTION` without updating the doc breaks the build, exactly like the
integrations drift check.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_motion as am  # noqa: E402
import ingest  # noqa: E402
import mvlib  # noqa: E402

DOC = (ROOT / "docs" / "how-it-works.md").read_text()
SRC = (ROOT / "scripts" / "analyze_motion.py").read_text()

# (module, attribute, how the doc spells the value)
CONSTANTS = [
    (am, "MAX_ANALYSIS_FPS", "60.0"),
    (am, "DEFAULT_MAX_SAMPLES", "1200"),
    (am, "DEFAULT_THUMB", "32"),
    (am, "DEFAULT_GRID", "8"),
    (am, "NOISE_FLOOR", "0.05"),
    (am, "HOLD_ENERGY_FRACTION", "0.18"),
    (am, "LOCALIZED_CELL_FRACTION", "0.10"),
    (am, "MIN_RUN_SECONDS", "0.10"),
    (am, "HOLD_INTERIOR_MIN", "0.12"),
    (am, "HOLD_BOUNDARY_MIN", "0.35"),
    (am, "DARK_CLIP_FRACTION", "0.85"),
    (am, "LOOP_MIN_CORR", "0.7"),
    (am, "LOOP_MIN_MOVING_FRACTION", "0.5"),
    (ingest, "DECOMPOSE_MIN_DURATION", "8.0"),
    (mvlib, "DEDUP_THRESHOLD", "2.0"),
    (mvlib, "DEDUP_THUMB", "16"),
]

WINDOW = 110  # chars after a constant's name in which its value must appear


def _documented(name: str, literal: str) -> bool:
    """True if `literal` shows up close enough to `name` to be describing it."""
    return any(literal in DOC[m.start():m.start() + WINDOW]
               for m in re.finditer(re.escape(name), DOC))


class TestDocumentedConstants(unittest.TestCase):
    def test_doc_literals_equal_the_code(self):
        for mod, name, literal in CONSTANTS:
            with self.subTest(constant=name):
                actual = getattr(mod, name)
                self.assertEqual(float(literal), float(actual),
                                 f"docs/how-it-works.md says {name} = {literal}, "
                                 f"code says {actual}")

    def test_every_constant_is_actually_in_the_doc(self):
        for _, name, literal in CONSTANTS:
            with self.subTest(constant=name):
                self.assertTrue(_documented(name, literal),
                                f"{name} = {literal} is not documented near its name in "
                                f"docs/how-it-works.md")

    def test_ffmpeg_filter_chain_matches(self):
        """Pull the filter strings straight out of the source; the doc must contain each."""
        filters = re.findall(r'"((?:scdet|blackdetect|freezedetect|siti)=[^,"]+)', SRC)
        self.assertGreaterEqual(len(filters), 4, f"expected 4 filters, found {filters}")
        for f in filters:
            with self.subTest(filter=f):
                self.assertIn(f, DOC, f"ffmpeg filter {f!r} is in the code but not the doc")

    def test_ease_library_matches(self):
        for name, (bez, _token) in am.EASE_LIB.items():
            with self.subTest(ease=name):
                self.assertIn(f'"{name}"', DOC, f"EASE_LIB entry {name!r} missing from doc")
                for n in bez:
                    self.assertIn(f"{n}", DOC, f"{name}: control point {n} missing from doc")
        # and nothing invented: every quoted ease in the doc's block exists in the code
        block = DOC.split("EASE_LIB` holds seven:")[1].split("```")[1]
        for quoted in re.findall(r'"([a-z-]+)":', block):
            self.assertIn(quoted, am.EASE_LIB, f"doc lists ease {quoted!r} that the code lacks")

    def test_presets_match(self):
        for name, (budget, res) in ingest.PRESETS.items():
            with self.subTest(preset=name):
                row = next((l for l in DOC.splitlines()
                            if l.startswith("|") and f"`{name}`" in l), None)
                self.assertIsNotNone(row, f"preset {name!r} has no row in the doc")
                self.assertIn(str(budget), row, f"{name}: frame budget {budget} not in its row")
                self.assertIn(f"{res}px", row, f"{name}: resolution {res}px not in its row")

    def test_transition_cap_matches_the_doc(self):
        short = ingest._transition_frames({"start_ms": 0, "end_ms": 400})
        long_ = ingest._transition_frames({"start_ms": 0, "end_ms": 600})
        self.assertEqual((short, long_), (2, 3))
        self.assertIn("capped at 2 frames", DOC)
        self.assertIn("0.5s", DOC)

    def test_percentile_anchor_is_still_the_75th(self):
        """The doc's central claim about the hold threshold."""
        self.assertIn("percentile_75", DOC)
        # a spike must not drag the reference up the way a max would
        flat = [1.0] * 90 + [100.0] * 10
        self.assertLess(am.robust_motion_ref(flat), 2.0)


if __name__ == "__main__":
    unittest.main()
