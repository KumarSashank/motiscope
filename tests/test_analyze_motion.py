#!/usr/bin/env python3
"""Ground-truth tests for the motiscope analysis pipeline (stdlib unittest).

Clips are synthesized by make_test_clip.sh (regenerated if missing), each with a
KNOWN motion profile, so we can assert the analyzer recovers it:
  test-ease    -> ease-in translate
  test-linear  -> constant-velocity translate
  test-hold    -> move then hold
  test-fade    -> full-frame fade-in then hold

Run:  python3 -m unittest tests.test_analyze_motion   (from the repo root)
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TESTS = ROOT / "tests"

import sys
sys.path.insert(0, str(SCRIPTS))
import analyze_motion  # noqa: E402
import extract_frames  # noqa: E402
import ingest  # noqa: E402


def _ensure_clips():
    clips = ["test-ease.mp4", "test-linear.mp4", "test-hold.mp4", "test-fade.mp4",
             "test-10s.mp4", "test-loop.mp4"]
    if all((TESTS / c).exists() for c in clips):
        return
    subprocess.run(["bash", str(TESTS / "make_test_clip.sh")], check=True)


@unittest.skipIf(shutil.which("ffmpeg") is None, "ffmpeg not installed")
class TestMotionAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _ensure_clips()
        cls.tmp = tempfile.mkdtemp(prefix="mv-test-")
        cls.motion = {}
        for name in ("ease", "linear", "hold", "fade"):
            out = Path(cls.tmp) / name
            cls.motion[name] = analyze_motion.analyze(str(TESTS / f"test-{name}.mp4"), out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _segments(self, name):
        return self.motion[name]["segments"]

    def test_ease_in_detected(self):
        m = self.motion["ease"]
        self.assertEqual(m["dominant_easing"], "ease-in")
        moves = [s for s in m["segments"] if s["kind"] == "move"]
        self.assertTrue(any(s["ease"] == "ease-in" for s in moves))

    def test_ease_energy_curve_rises(self):
        v = self.motion["ease"]["energy"]["values"]
        third = len(v) // 3
        front = sum(v[:third]) / third
        back = sum(v[-third:]) / third
        self.assertGreater(back, front * 1.5, "ease-in energy should rise over time")

    def test_linear_is_linear(self):
        m = self.motion["linear"]
        self.assertEqual(m["dominant_easing"], "linear")
        moves = [s for s in m["segments"] if s["kind"] == "move"]
        self.assertTrue(moves, "linear clip should have a move segment")

    def test_hold_segment_detected(self):
        kinds = [s["kind"] for s in self._segments("hold")]
        self.assertIn("hold", kinds)
        self.assertIn("move", kinds)

    def test_fade_in_detected(self):
        kinds = [s["kind"] for s in self._segments("fade")]
        self.assertIn("fade-in", kinds)

    def test_manifest_and_frames_written(self):
        out = Path(self.tmp) / "e2e"
        manifest = ingest.ingest(str(TESTS / "test-ease.mp4"), frame_budget=12, base=str(out))
        work = Path(manifest["_out_dir"])
        self.assertTrue((work / "manifest.json").exists())
        self.assertTrue((work / "motion.json").exists())
        self.assertTrue((work / "report.md").exists())
        frames = list((work / "frames").glob("frame_*.png"))
        self.assertGreater(len(frames), 0)
        self.assertLessEqual(len(frames), 12, "curated frames must respect the budget")

    def test_dedup_collapses_static_tail(self):
        # test-hold is static for its final second. With dedup on, those identical
        # frames collapse, so the count is meaningfully lower than with dedup off.
        on = ingest.ingest(str(TESTS / "test-hold.mp4"), frame_budget=32,
                           base=str(Path(self.tmp) / "dedup-on"), dedup=True)
        off = ingest.ingest(str(TESTS / "test-hold.mp4"), frame_budget=32,
                            base=str(Path(self.tmp) / "dedup-off"), dedup=False)
        self.assertLess(len(on["frames"]), len(off["frames"]))

    def test_presets_scale_frame_count(self):
        counts = {}
        for preset in ("draft", "balanced", "detailed"):
            out = Path(self.tmp) / f"preset-{preset}"
            m = ingest.ingest(str(TESTS / "test-10s.mp4"), preset=preset, base=str(out))
            counts[preset] = len(m["frames"])
            self.assertLessEqual(counts[preset], ingest.PRESETS[preset][0])
        self.assertLessEqual(counts["draft"], counts["detailed"])

    def test_focus_window_absolute_timestamps(self):
        out = Path(self.tmp) / "win"
        m = ingest.ingest(str(TESTS / "test-10s.mp4"), preset="detailed",
                          start=1.0, end=3.0, base=str(out))
        # window recorded and frames fall inside [1,3] absolute seconds
        motion = analyze_motion.analyze(str(TESTS / "test-10s.mp4"),
                                        Path(self.tmp) / "win-motion", start=1.0, end=3.0)
        self.assertTrue(motion["window"]["focused"])
        self.assertAlmostEqual(motion["window"]["start_s"], 1.0, places=2)
        ts = [f["timestamp_seconds"] for f in m["frames"]]
        self.assertTrue(all(0.95 <= t <= 3.05 for t in ts), ts)
        # the move inside the window is an ease-in
        self.assertEqual(motion["dominant_easing"], "ease-in")

    def test_forced_fps_backbone_density(self):
        # --fps 20 over a 2s window with no dedup => a dense, evenly-spaced set
        out = Path(self.tmp) / "dense"
        m = ingest.ingest(str(TESTS / "test-10s.mp4"), frame_budget=48,
                          start=1.0, end=3.0, backbone_fps=20.0, dedup=False,
                          decompose=False, base=str(out))
        self.assertGreaterEqual(len(m["frames"]), 30)

    def test_decompose_concentrates_on_motion(self):
        # test-10s: the motion (ease-in) is ~1-3s; the rest is a long hold.
        # Decompose must spend frames on the motion, not the dead 3.5-9.9s hold.
        out = Path(self.tmp) / "decomp"
        m = ingest.ingest(str(TESTS / "test-10s.mp4"), frame_budget=32,
                          decompose=True, base=str(out))
        ts = [f["timestamp_seconds"] for f in m["frames"]]
        in_dead_hold = [t for t in ts if 3.5 <= t <= 9.9]
        self.assertLessEqual(len(in_dead_hold), 2, f"too many frames in the hold: {ts}")
        self.assertEqual(m["extraction"]["mode"], "decomposed")

    def test_localized_energy_detects_small_element_motion(self):
        # A small box moving on a large canvas must register as a MOVE (localized
        # energy), not wash out to a hold under the global mean.
        clip = TESTS / "test-ease.mp4"  # 120px box on 800x600 = ~3% of frame
        motion = analyze_motion.analyze(str(clip), Path(self.tmp) / "loc")
        self.assertTrue(any(s["kind"] == "move" for s in motion["segments"]))
        # localized peak should dwarf the global mean for a small element
        self.assertGreater(motion["energy"]["peak"]["value"],
                           motion["energy"]["global_mean"] * 3)

    def test_loop_detected_and_no_false_positives(self):
        loop = analyze_motion.analyze(str(TESTS / "test-loop.mp4"), Path(self.tmp) / "loopc")
        self.assertTrue(loop["loop"]["is_loop"])
        self.assertGreater(loop["loop"]["period_ms"], 200)  # sensible period
        # a play-once move+hold must NOT read as a loop
        self.assertFalse(self.motion["hold"]["loop"]["is_loop"])
        self.assertFalse(self.motion["ease"]["loop"]["is_loop"])

    def test_weighted_allocation_favors_intense_beats(self):
        # equal budget, a beat with 4x the weight should get more frames, within budget
        alloc = ingest._allocate_by_weight([1.0, 4.0], budget_for_motion=20)
        self.assertGreater(alloc[1], alloc[0])
        self.assertLessEqual(sum(alloc), 20)
        self.assertTrue(all(a >= 2 for a in alloc))

    def test_decompose_caps_transitions_not_moves(self):
        # A short move next to two high-energy fades: the fades must NOT hog the budget
        # (the exact bug the Alterfx clip hit — 33 frames on one fade). Deterministic.
        motion = {
            "video": {"duration_seconds": 10}, "window": {"start_s": 0, "end_s": 10},
            "salient": [],
            "segments": [
                {"kind": "move", "start_ms": 0, "end_ms": 500, "peak_energy": 8},
                {"kind": "fade-out", "start_ms": 600, "end_ms": 900, "peak_energy": 200},
                {"kind": "hold", "start_ms": 900, "end_ms": 3000},
                {"kind": "fade-out", "start_ms": 3000, "end_ms": 3300, "peak_energy": 200},
                {"kind": "hold", "start_ms": 3300, "end_ms": 10000},
            ],
        }
        entries, meta = ingest.decompose_timestamps(motion, budget=32)
        for pb in meta["per_beat"]:
            if pb["kind"] in ("fade-in", "fade-out"):
                self.assertLessEqual(pb["frames"], 3, f"transition over-allocated: {pb}")
        move_frames = sum(pb["frames"] for pb in meta["per_beat"] if pb["kind"] == "move")
        self.assertGreater(move_frames, 3, "the actual animation should get real coverage")

    def test_robust_motion_ref_ignores_spikes(self):
        # a curve dominated by a few huge spikes should reference the typical level, not the peak
        energy = [5.0] * 90 + [500.0] * 10          # 10% cut/fade spikes
        ref = analyze_motion.robust_motion_ref(energy)
        self.assertLess(ref, 100, "reference must not be dominated by the spikes")
        self.assertGreater(ref, 1)

    def test_fit_easing_recovers_curve(self):
        # constant speed -> linear; accelerating speed -> ease-in; decelerating -> ease-out
        self.assertEqual(analyze_motion.fit_easing([1.0] * 30)["ease"], "linear")
        self.assertEqual(analyze_motion.fit_easing([float(i) for i in range(1, 31)])["ease"], "ease-in")
        self.assertEqual(analyze_motion.fit_easing([float(i) for i in range(30, 0, -1)])["ease"], "ease-out")

    def test_measured_bezier_on_clips(self):
        seg = [s for s in self.motion["ease"]["segments"] if s["kind"] == "move"][0]
        self.assertEqual(len(seg["bezier"]), 4)
        self.assertEqual(seg["ease"], "ease-in")
        lin = [s for s in self.motion["linear"]["segments"] if s["kind"] == "move"][0]
        self.assertEqual(lin["bezier"], [0.0, 0.0, 1.0, 1.0])


class TestDarkClipIsNotAFade(unittest.TestCase):
    """A dark-mode UI animation is dark throughout. That is not a fade."""

    def test_black_interval_spanning_the_clip_is_ignored(self):
        black = [{"start_s": 0.0, "end_s": 2.36, "duration": 2.36}]
        fades = analyze_motion.detect_fades(None, black, duration=2.40)
        self.assertEqual(fades, [], "a clip that is dark throughout was reported as a fade")

    def test_a_real_fade_in_is_still_detected(self):
        black = [{"start_s": 0.0, "end_s": 0.40, "duration": 0.40}]
        fades = analyze_motion.detect_fades(None, black, duration=2.40)
        self.assertEqual(len(fades), 1)
        self.assertEqual(fades[0]["kind"], "fade-in")
        self.assertEqual(fades[0]["end_ms"], 400)

    def test_a_real_fade_out_is_still_detected(self):
        black = [{"start_s": 2.00, "end_s": 2.40, "duration": 0.40}]
        fades = analyze_motion.detect_fades(None, black, duration=2.40)
        self.assertEqual(len(fades), 1)
        self.assertEqual(fades[0]["kind"], "fade-out")

    def test_the_guard_is_a_fraction_of_the_clip_not_an_absolute(self):
        # 0.5s of black is a fade in a 5s clip, and the whole story in a 0.55s clip
        long_clip = analyze_motion.detect_fades(None, [{"start_s":0.0,"end_s":0.5,"duration":0.5}], 5.0)
        short_clip = analyze_motion.detect_fades(None, [{"start_s":0.0,"end_s":0.5,"duration":0.5}], 0.55)
        self.assertEqual(len(long_clip), 1)
        self.assertEqual(short_clip, [])


if __name__ == "__main__":
    unittest.main()
