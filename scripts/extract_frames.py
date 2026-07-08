#!/usr/bin/env python3
"""Animation-tuned frame extraction for motiscope.

Default `curated` mode consumes motion.json and extracts one PNG at each salient
timestamp (segment boundaries, energy-curve extrema, holds, fades), then perceptually
de-dupes and even-samples down to a frame budget. Filenames encode the timestamp
and reason so the images align to the motion timeline without cross-referencing.

Scene / keyframe / uniform modes are ported from claude-video's frames.py (MIT).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import mvlib
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mvlib

DEFAULT_BUDGET = 32
SCENE_THRESHOLD = 0.20


def _clean(reason: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", reason.lower()).strip("-") or "frame"


def _clear(frames_dir: Path, ext: str) -> None:
    for pat in ("cand_*.png", "cand_*.jpg", "frame_*.png", "frame_*.jpg"):
        for f in frames_dir.glob(pat):
            f.unlink()


def _seek_one(video: str, dst: Path, t: float, resolution: int, fmt: str) -> bool:
    q = ["-q:v", "3"] if fmt == "jpg" else []
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(Path(video).resolve()), "-ss", f"{t:.3f}", "-frames:v", "1",
           "-vf", mvlib.scale_filter(resolution), *q, str(dst)]
    return mvlib.run(cmd).returncode == 0 and dst.exists()


def _finalize(cands: list[dict], frames_dir: Path, budget: int, ext: str, dedup: bool) -> dict:
    dropped = 0
    if dedup:
        cands, dropped = mvlib.dedupe_perceptual(cands)
    if len(cands) > budget:
        cands = mvlib.even_sample(cands, budget)
    final = []
    for i, c in enumerate(cands):
        new = frames_dir / f"frame_{i:03d}_t{mvlib.format_secs(c['t'])}s_{_clean(c['reason'])}.{ext}"
        Path(c["path"]).rename(new)
        final.append({"index": i, "timestamp_seconds": round(c["t"], 3),
                      "reason": c["reason"], "path": str(new)})
    return {"frames": final, "deduped": dropped, "count": len(final)}


def extract_curated(video: str, frames_dir: Path, salient: list[dict], *,
                    resolution: int = mvlib.DEFAULT_RESOLUTION, budget: int = DEFAULT_BUDGET,
                    fmt: str = "png", dedup: bool = True,
                    start: float | None = None, end: float | None = None,
                    backbone_fps: float | None = None) -> dict:
    """Extract PNGs at the union of salient timestamps and a uniform backbone across
    the [start, end] window, then perceptually de-dupe and cap to `budget`.

    The backbone guarantees even temporal coverage so fast content between keyposes
    isn't missed. Its density is `backbone_fps` (auto = budget/window, ≤24fps) unless
    forced (e.g. --fps 20 for a "see every ~50ms" pass on a short focus window).
    """
    mvlib.require("ffmpeg")
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    ext = "jpg" if fmt == "jpg" else "png"
    _clear(frames_dir, ext)

    duration = mvlib.get_metadata(video)["duration_seconds"]
    s = max(0.0, start) if start else 0.0
    e = min(end, duration) if end is not None else duration
    e = min(e, max(0.0, duration - 0.04))
    window = max(0.05, e - s)
    if backbone_fps is None:
        backbone_fps = max(1.0, min(24.0, budget / window))

    # candidate timestamp -> reason (salient reasons take precedence over 'uniform')
    cand: dict[float, str] = {}
    for entry in salient:
        t = float(entry["t"])
        if s - 1e-6 <= t <= e + 1e-6:
            cand[round(min(max(t, s), e), 3)] = entry["reason"]
    # backbone_fps == 0 => no uniform backbone (caller supplied its own density,
    # e.g. auto-decompose). Otherwise lay a uniform backbone across the window.
    if backbone_fps and backbone_fps > 0:
        n_bb = max(2, int(window * backbone_fps) + 1)
        for i in range(n_bb):
            t = round(s + window * i / (n_bb - 1), 3)
            cand.setdefault(t, "uniform")
        min_gap = 0.5 / backbone_fps
    else:
        min_gap = 0.02

    # sort + collapse timestamps closer than min_gap,
    # preferring a specific reason over a generic 'uniform' one.
    entries: list[dict] = []
    for t in sorted(cand):
        reason = cand[t]
        if entries and t - entries[-1]["t"] < min_gap:
            if entries[-1]["reason"] == "uniform" and reason != "uniform":
                entries[-1] = {"t": t, "reason": reason}
            continue
        entries.append({"t": t, "reason": reason})

    # cap extraction count up front (keep first + last), so we never over-extract
    if len(entries) > budget:
        entries = [entries[i] for i in mvlib.even_indices(len(entries), budget)]

    cands = []
    for i, ent in enumerate(entries):
        dst = frames_dir / f"cand_{i:04d}.{ext}"
        if _seek_one(video, dst, ent["t"], resolution, fmt):
            cands.append({"index": i, "t": ent["t"], "reason": ent["reason"], "path": str(dst)})
    return _finalize(cands, frames_dir, budget, ext, dedup)


def _showinfo_extract(video: str, frames_dir: Path, vf_prefix: str, reason: str,
                      resolution: int, fmt: str) -> list[dict]:
    ext = "jpg" if fmt == "jpg" else "png"
    q = ["-q:v", "3"] if fmt == "jpg" else []
    pattern = str(frames_dir / f"cand_%04d.{ext}")
    vf = f"{vf_prefix},{mvlib.scale_filter(resolution)},showinfo"
    res = mvlib.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-y",
                     "-i", str(Path(video).resolve()), "-vf", vf, "-vsync", "vfr",
                     *q, pattern])
    if res.returncode != 0:
        raise mvlib.MotiscopeError("ffmpeg frame extraction failed")
    ts = [round(float(m.group(1)), 3) for m in mvlib.SHOWINFO_TS_RE.finditer(res.stderr)]
    files = sorted(frames_dir.glob(f"cand_*.{ext}"))
    out = []
    for i, p in enumerate(files):
        out.append({"index": i, "t": ts[i] if i < len(ts) else 0.0,
                    "reason": "first-frame" if i == 0 else reason, "path": str(p)})
    return out


def extract_scene(video, frames_dir, *, resolution=mvlib.DEFAULT_RESOLUTION,
                  budget=DEFAULT_BUDGET, fmt="png", dedup=True) -> dict:
    mvlib.require("ffmpeg")
    frames_dir = Path(frames_dir); frames_dir.mkdir(parents=True, exist_ok=True)
    _clear(frames_dir, fmt)
    cands = _showinfo_extract(video, frames_dir,
                              f"select='eq(n\\,0)+gt(scene\\,{SCENE_THRESHOLD})'",
                              "scene-change", resolution, fmt)
    return _finalize(cands, frames_dir, budget, "jpg" if fmt == "jpg" else "png", dedup)


def extract_keyframe(video, frames_dir, *, resolution=mvlib.DEFAULT_RESOLUTION,
                     budget=DEFAULT_BUDGET, fmt="png", dedup=True) -> dict:
    mvlib.require("ffmpeg")
    frames_dir = Path(frames_dir); frames_dir.mkdir(parents=True, exist_ok=True)
    _clear(frames_dir, fmt)
    ext = "jpg" if fmt == "jpg" else "png"
    q = ["-q:v", "3"] if fmt == "jpg" else []
    pattern = str(frames_dir / f"cand_%04d.{ext}")
    res = mvlib.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-y",
                     "-skip_frame", "nokey", "-i", str(Path(video).resolve()),
                     "-vf", f"{mvlib.scale_filter(resolution)},showinfo", "-vsync", "vfr",
                     *q, pattern])
    if res.returncode != 0:
        raise mvlib.MotiscopeError("ffmpeg keyframe extraction failed")
    ts = [round(float(m.group(1)), 3) for m in mvlib.SHOWINFO_TS_RE.finditer(res.stderr)]
    files = sorted(frames_dir.glob(f"cand_*.{ext}"))
    cands = [{"index": i, "t": ts[i] if i < len(ts) else 0.0, "reason": "keyframe", "path": str(p)}
             for i, p in enumerate(files)]
    return _finalize(cands, frames_dir, budget, ext, dedup)


def extract_uniform(video, frames_dir, *, resolution=mvlib.DEFAULT_RESOLUTION,
                    budget=DEFAULT_BUDGET, fmt="png", dedup=True) -> dict:
    mvlib.require("ffmpeg")
    frames_dir = Path(frames_dir); frames_dir.mkdir(parents=True, exist_ok=True)
    _clear(frames_dir, fmt)
    ext = "jpg" if fmt == "jpg" else "png"
    q = ["-q:v", "3"] if fmt == "jpg" else []
    duration = mvlib.get_metadata(video)["duration_seconds"] or 1.0
    fps = max(0.5, min(30.0, budget / duration))
    pattern = str(frames_dir / f"cand_%04d.{ext}")
    res = mvlib.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-i", str(Path(video).resolve()),
                     "-vf", f"fps={fps},{mvlib.scale_filter(resolution)}",
                     "-frames:v", str(budget * 2), *q, pattern])
    if res.returncode != 0:
        raise mvlib.MotiscopeError("ffmpeg uniform extraction failed")
    files = sorted(frames_dir.glob(f"cand_*.{ext}"))
    cands = [{"index": i, "t": round(i / fps, 3), "reason": "uniform", "path": str(p)}
             for i, p in enumerate(files)]
    return _finalize(cands, frames_dir, budget, ext, dedup)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: extract_frames.py <video> <frames-dir> [--mode curated|scene|keyframe|uniform] "
              "[--motion motion.json] [--resolution 640] [--budget 32] [--format png|jpg] "
              "[--start T] [--end T] [--fps N] [--no-dedup]",
              file=sys.stderr)
        return 2
    video, frames_dir = argv[0], Path(argv[1])
    mode, motion_path, resolution, budget, fmt, dedup = "curated", None, mvlib.DEFAULT_RESOLUTION, DEFAULT_BUDGET, "png", True
    start = end = backbone_fps = None
    i = 0
    rest = argv[2:]
    while i < len(rest):
        a = rest[i]
        if a == "--mode": mode = rest[i + 1]; i += 2
        elif a == "--motion": motion_path = rest[i + 1]; i += 2
        elif a == "--resolution": resolution = int(rest[i + 1]); i += 2
        elif a == "--budget": budget = int(rest[i + 1]); i += 2
        elif a == "--format": fmt = rest[i + 1]; i += 2
        elif a == "--start": start = mvlib.parse_time(rest[i + 1]); i += 2
        elif a == "--end": end = mvlib.parse_time(rest[i + 1]); i += 2
        elif a == "--fps": backbone_fps = float(rest[i + 1]); i += 2
        elif a == "--no-dedup": dedup = False; i += 1
        else: i += 1

    kw = dict(resolution=resolution, budget=budget, fmt=fmt, dedup=dedup)
    try:
        if mode == "curated":
            if not motion_path:
                # derive from analyze if not supplied
                import analyze_motion
                motion = analyze_motion.analyze(video, frames_dir.parent, start=start, end=end)
            else:
                motion = json.loads(Path(motion_path).read_text())
            result = extract_curated(video, frames_dir, motion["salient"],
                                     start=start, end=end, backbone_fps=backbone_fps, **kw)
        elif mode == "scene":
            result = extract_scene(video, frames_dir, **kw)
        elif mode == "keyframe":
            result = extract_keyframe(video, frames_dir, **kw)
        else:
            result = extract_uniform(video, frames_dir, **kw)
    except mvlib.MotiscopeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
