#!/usr/bin/env python3
"""motiscope ingest orchestrator — the single entry point the analyze skill runs.

Pipeline: resolve per-video work dir -> analyze_motion (motion.json) ->
extract_frames curated (frames/*.png) -> assemble manifest.json -> render
report.md -> print a compact summary, the report path, and the ordered frame list.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import mvlib
    import analyze_motion
    import extract_frames
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mvlib
    import analyze_motion
    import extract_frames

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi", ".flv", ".wmv"}
_SPARK = "▁▂▃▄▅▆▇█"

# Presets: (frame_budget, resolution). Explicit --frame-budget/--resolution override.
PRESETS = {
    "draft":    (12, 512),   # cheapest — quick look
    "balanced": (32, 640),   # default — most cases
    "detailed": (48, 960),   # dense sequences / reading on-screen text
}


def _sparkline(values: list[float], width: int = 50) -> str:
    if not values:
        return ""
    idx = mvlib.even_indices(len(values), min(width, len(values)))
    sample = [values[i] for i in idx]
    lo, hi = min(sample), max(sample)
    span = (hi - lo) or 1.0
    return "".join(_SPARK[min(7, int((v - lo) / span * 7))] for v in sample)


def _segment_table(segments: list[dict]) -> str:
    if not segments:
        return "_No segments detected._\n"
    rows = ["| # | kind | start | end | dur | easing | conf |",
            "|---|------|-------|-----|-----|--------|------|"]
    for i, s in enumerate(segments):
        dur = (s["end_ms"] - s["start_ms"]) / 1000
        rows.append(f"| {i} | {s['kind']} | {s['start_ms']/1000:.2f}s | {s['end_ms']/1000:.2f}s "
                    f"| {dur:.2f}s | {s.get('ease','—')} | {s.get('ease_confidence','—')} |")
    return "\n".join(rows) + "\n"


def render_report(motion: dict, frames: list[dict], extraction: dict | None = None) -> str:
    v = motion["video"]
    e = motion["energy"]
    sig = motion.get("signal", {})
    win = motion.get("window", {})
    hint = motion.get("grid", {}).get("stagger_hint")
    lines = [
        "# motiscope analysis report", "",
        f"**Source:** `{v['path']}`  ",
        f"**Duration:** {v['duration_seconds']:.2f}s · **fps:** {v.get('fps') or '?'} · "
        f"**size:** {v.get('width')}×{v.get('height')} · **codec:** {v.get('codec')}", "",
    ]
    if win.get("focused"):
        lines += [f"**Focus window:** {win['start_s']:.2f}s → {win['end_s']:.2f}s "
                  f"({win['duration_s']:.2f}s). Timestamps below are absolute source time.", ""]
    lines += [
        f"> {motion['summary']}", "",
        "## Motion-energy curve", "",
        "Per-frame motion magnitude (mean pixel change vs previous frame). "
        "This is the source of truth for **timing and easing** — read the shape "
        "per segment rather than eyeballing frames.", "",
        f"```\n{_sparkline(e['values'])}\n```",
        f"peak {e['peak']['value']} @ {e['peak']['time_s']}s · mean {e['mean']} · "
        f"hold threshold {e['hold_threshold']}", "",
        "## Segments (beats)", "",
        _segment_table(motion["segments"]),
        f"**Dominant easing:** `{motion['dominant_easing']}`", "",
    ]
    if hint:
        lines += [f"**Stagger hint:** {hint['direction']} — ~{hint['each_ms_estimate']}ms between "
                  f"elements (confidence {hint['confidence']}).", ""]
    loop = motion.get("loop") or {}
    if loop.get("is_loop"):
        lines += [f"**Loop:** repeats every ~{loop['period_ms']}ms (confidence {loop['confidence']}). "
                  f"Set `loop: true` in the spec; consider re-analyzing just one period "
                  f"(`--start 0 --end {loop['period_ms']/1000:.2f}`) for the cleanest keyframes. "
                  f"_Energy is speed-based, so for back-and-forth motion this may be a **half**-cycle "
                  f"— check the frames: same-direction repeat ⇒ `repeat: -1`; out-and-back ⇒ `yoyo` "
                  f"at this period._", ""]
    if sig.get("content_profile"):
        lines += [f"**Content profile (SI/TI):** {sig['content_profile']}", ""]
    if sig.get("scene_cuts"):
        cuts = ", ".join(f"{c['time_s']}s" for c in sig["scene_cuts"])
        lines += [f"**Hard cuts:** {cuts}", ""]
    if sig.get("freezes"):
        lines += ["**Freezes/holds:** " + ", ".join(
            f"{f['start_s']}–{f['end_s']}s" for f in sig["freezes"]), ""]

    lines += ["## Curated frames", ""]
    if extraction and extraction.get("mode") == "decomposed":
        how = ("frames allocated by motion magnitude" if extraction.get("allocation") == "weighted"
               else "uniform sampling")
        lines += [f"_Auto-decomposed ({how}): frames concentrated on {extraction.get('motion_segments')} "
                  f"motion beat(s); each hold gets one frame._", ""]
        for pb in extraction.get("per_beat", []):
            lines.append(f"- beat {pb['start_s']:.2f}–{pb['end_s']:.2f}s ({pb['kind']}): "
                         f"{pb['frames']} frames @ ~{pb['fps']}fps")
        lines.append("")
    lines += [f"{len(frames)} PNG frame(s). Read them in order; the filename encodes "
              "timestamp + why it was picked.", ""]
    for f in frames:
        lines.append(f"- `t={f['timestamp_seconds']}s` **{f['reason']}** → `{f['path']}`")
    lines += ["", "## Confidence", "",
              "- **Measured** (reliable): duration, fps, segment boundaries, easing shape, "
              "stagger direction, holds/fades.",
              "- **Visually estimated** (from the frames): which elements move, transform "
              "magnitudes (px/scale/rotation/opacity), colors, exact overshoot. Flag these "
              "as estimates when you build the spec.", ""]
    return "\n".join(lines)


# Auto-decompose kicks in for clips this long (or longer) with real structure.
DECOMPOSE_MIN_DURATION = 8.0
_SALIENT_KEEP = {"peak", "keypose", "cut", "fadein", "fadeout", "fade-in", "fade-out",
                 "holdstart", "start", "end"}


def _allocate_by_weight(weights: list[float], budget_for_motion: int,
                        min_per_beat: int = 3) -> list[int]:
    """Split a frame budget across beats in proportion to their motion weight, with a
    per-beat floor. Fast/intense beats (higher weight) get more frames. Never exceeds
    the budget: if the floors alone overflow, the largest allocations are trimmed."""
    total = sum(weights) or 1.0
    alloc = [max(min_per_beat, round(budget_for_motion * w / total)) for w in weights]
    # trim to fit without dropping any beat below 2 frames
    while sum(alloc) > budget_for_motion and any(a > 2 for a in alloc):
        j = alloc.index(max(alloc))
        alloc[j] -= 1
    return alloc


def decompose_timestamps(motion: dict, budget: int, drill_fps: float | None = None):
    """Build a timestamp list that spends frames on MOTION and skips dead holds.

    Frames are allocated across motion beats **in proportion to each beat's motion
    magnitude** (duration × peak energy), so a fast/intense beat gets more frames than
    a slow one, with a per-beat floor. Each hold gets a single representative frame and
    meaningful salient beats are kept. If `drill_fps` is given, falls back to a uniform
    rate per beat instead of weighted allocation. Returns (entries, meta).
    """
    segs = motion.get("segments", [])
    win = motion.get("window") or {}
    lo = win.get("start_s", 0.0)
    hi = win.get("end_s", motion["video"]["duration_seconds"])
    motion_segs = [s for s in segs if s["kind"] != "hold"]
    holds = [s for s in segs if s["kind"] == "hold"]

    pts: dict[float, str] = {round(lo, 3): "start", round(hi, 3): "end"}
    per_beat = []

    if drill_fps is not None:
        allocs = [max(2, int((s["end_ms"] - s["start_ms"]) / 1000 * drill_fps) + 1) for s in motion_segs]
        mode = "uniform"
    else:
        reserved = 2 + len(holds)
        for_motion = max(len(motion_segs) * 3, budget - reserved)
        weights = [max(1e-6, (s["end_ms"] - s["start_ms"]) / 1000 * float(s.get("peak_energy", 1.0)))
                   for s in motion_segs]
        allocs = _allocate_by_weight(weights, for_motion)
        mode = "weighted"

    for s, k in zip(motion_segs, allocs):
        a, b = s["start_ms"] / 1000, s["end_ms"] / 1000
        for i in range(k):
            t = round(a + (b - a) * (i / (k - 1) if k > 1 else 0.5), 3)
            pts.setdefault(t, s["kind"])
        per_beat.append({"start_s": round(a, 3), "end_s": round(b, 3), "kind": s["kind"],
                         "peak_energy": s.get("peak_energy"), "frames": k,
                         "fps": round(k / max(b - a, 1e-3), 1)})

    for s in holds:
        pts.setdefault(round(s["start_ms"] / 1000, 3), "holdstart")
    for e in motion.get("salient", []):
        if e["reason"] in _SALIENT_KEEP:
            pts[round(e["t"], 3)] = e["reason"]

    entries = [{"t": t, "reason": r} for t, r in sorted(pts.items())]
    meta = {"mode": "decomposed", "allocation": mode, "motion_segments": len(motion_segs),
            "holds": len(holds), "per_beat": per_beat}
    return entries, meta


def build_manifest(motion: dict, frames: list[dict], out_dir: Path, video: str,
                   preset: str) -> dict:
    return {
        "generated_by": "motiscope",
        "schema": 1,
        "source_hash": mvlib.source_hash(video),
        "preset": preset,
        "video": motion["video"],
        "window": motion.get("window"),
        "sampling": motion["sampling"],
        "dominant_easing": motion["dominant_easing"],
        "loop": motion.get("loop"),
        "segments": motion["segments"],
        "beats": motion["beats"],
        "stagger_hint": motion.get("grid", {}).get("stagger_hint"),
        "content_profile": motion.get("signal", {}).get("content_profile"),
        "summary": motion["summary"],
        "frames": frames,
        "motion_json": str(out_dir / "motion.json"),
        "report": str(out_dir / "report.md"),
    }


def ingest(video: str, *, preset: str = "balanced", frame_budget: int | None = None,
           resolution: int | None = None, base: str = ".motiscope", fmt: str = "png",
           start: float | None = None, end: float | None = None,
           backbone_fps: float | None = None, dedup: bool = True,
           decompose: object = "auto") -> dict:
    src = Path(video)
    if not src.exists():
        raise mvlib.MotiscopeError(f"video not found: {video}")
    if src.suffix.lower() not in VIDEO_EXTS:
        raise mvlib.MotiscopeError(
            f"unsupported file type: {src.suffix} (expected one of {sorted(VIDEO_EXTS)})")

    pb, pr = PRESETS.get(preset, PRESETS["balanced"])
    budget = frame_budget if frame_budget is not None else pb
    res = resolution if resolution is not None else pr

    out_dir = mvlib.resolve_out_dir(video, base)
    motion = analyze_motion.analyze(video, out_dir, start=start, end=end)

    # Decide whether to auto-decompose: drill each motion beat densely and skip
    # holds, instead of one flat pass. Auto = on for longer clips with >=2 moves.
    motion_segs = [s for s in motion["segments"] if s["kind"] != "hold"]
    if decompose == "auto":
        decompose = motion["video"]["duration_seconds"] >= DECOMPOSE_MIN_DURATION and len(motion_segs) >= 2
    decomposed = bool(decompose) and len(motion_segs) >= 1
    decomp_meta = None

    if decomposed:
        entries, decomp_meta = decompose_timestamps(motion, budget, drill_fps=backbone_fps)
        extraction = extract_frames.extract_curated(
            video, out_dir / "frames", entries,
            resolution=res, budget=budget, fmt=fmt, dedup=dedup, backbone_fps=0)
    else:
        extraction = extract_frames.extract_curated(
            video, out_dir / "frames", motion["salient"],
            resolution=res, budget=budget, fmt=fmt, dedup=dedup,
            start=start, end=end, backbone_fps=backbone_fps)
    frames = extraction["frames"]

    manifest = build_manifest(motion, frames, out_dir, video, preset)
    manifest["extraction"] = decomp_meta or {"mode": "flat", "backbone_fps": backbone_fps,
                                             "motion_segments": len(motion_segs)}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out_dir / "report.md").write_text(render_report(motion, frames, manifest["extraction"]))
    manifest["_out_dir"] = str(out_dir)
    manifest["_deduped"] = extraction["deduped"]
    return manifest


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: ingest.py <video> [--preset draft|balanced|detailed] [--frame-budget N] "
              "[--resolution W] [--start T] [--end T] [--fps N] [--decompose|--no-decompose] "
              "[--no-dedup] [--out .motiscope] [--format png|jpg]", file=sys.stderr)
        return 2
    video = argv[0]
    preset, budget, resolution, base, fmt = "balanced", None, None, ".motiscope", "png"
    start = end = backbone_fps = None
    dedup = True
    decompose = "auto"
    i, rest = 0, argv[1:]
    while i < len(rest):
        a = rest[i]
        if a == "--preset": preset = rest[i + 1]; i += 2
        elif a == "--frame-budget": budget = int(rest[i + 1]); i += 2
        elif a == "--resolution": resolution = int(rest[i + 1]); i += 2
        elif a == "--start": start = mvlib.parse_time(rest[i + 1]); i += 2
        elif a == "--end": end = mvlib.parse_time(rest[i + 1]); i += 2
        elif a == "--fps": backbone_fps = float(rest[i + 1]); i += 2
        elif a == "--decompose": decompose = True; i += 1
        elif a == "--no-decompose": decompose = False; i += 1
        elif a == "--no-dedup": dedup = False; i += 1
        elif a == "--out": base = rest[i + 1]; i += 2
        elif a == "--format": fmt = rest[i + 1]; i += 2
        else: i += 1

    try:
        m = ingest(video, preset=preset, frame_budget=budget, resolution=resolution,
                   base=base, fmt=fmt, start=start, end=end, backbone_fps=backbone_fps,
                   dedup=dedup, decompose=decompose)
    except mvlib.MotiscopeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(m["summary"])
    print(f"\nreport:   {m['report']}")
    print(f"manifest: {m['motion_json'].replace('motion.json', 'manifest.json')}")
    print(f"\ncurated frames ({len(m['frames'])}):")
    for f in m["frames"]:
        print(f"  t={f['timestamp_seconds']}s  {f['reason']:<12}  {f['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
