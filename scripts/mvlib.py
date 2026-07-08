#!/usr/bin/env python3
"""Shared helpers for motiscope. Pure standard library; ffmpeg/ffprobe do all
pixel work. Several primitives here are ported from claude-video's frames.py
(MIT, Bradley Bonanno) — see ATTRIBUTION.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

# Frame extraction / Read-tool constraints.
MAX_READ_DIMENSION = 1998  # Claude Read tool downsizes very tall images; keep under this.
DEFAULT_RESOLUTION = 640

# Perceptual dedup: downscale each frame to DEDUP_THUMB x DEDUP_THUMB grayscale
# and treat two frames as near-identical when their mean per-pixel difference
# (0-255) is at or below DEDUP_THRESHOLD.
DEDUP_THUMB = 16
DEDUP_THRESHOLD = 2.0

SHOWINFO_TS_RE = re.compile(r"pts_time:([0-9.]+)")


class MotiscopeError(RuntimeError):
    """Raised for user-actionable failures (missing binaries, bad input)."""


# --------------------------------------------------------------------------- #
# ffmpeg plumbing
# --------------------------------------------------------------------------- #
def require(binary: str) -> None:
    if shutil.which(binary) is None:
        raise MotiscopeError(
            f"{binary} is not installed. Install with: brew install ffmpeg "
            "(macOS) — see /motiscope:doctor."
        )


def run(cmd: list[str], *, capture: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=capture, text=text)


def scale_filter(resolution: int) -> str:
    """Width-capped scale that preserves aspect ratio and keeps even dimensions,
    clamped to a Read-tool-safe max height. Ported from claude-video."""
    return (
        f"scale=w='min({resolution},iw)':h='min({MAX_READ_DIMENSION},ih)':"
        "force_original_aspect_ratio=decrease:force_divisible_by=2"
    )


# --------------------------------------------------------------------------- #
# time helpers
# --------------------------------------------------------------------------- #
def parse_time(value) -> float | None:
    """Parse SS, MM:SS, or HH:MM:SS (optional .ms) into seconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    raise MotiscopeError(f"Cannot parse time value: {value!r} (expected SS, MM:SS, HH:MM:SS)")


def format_time(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, sec = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def format_secs(seconds: float) -> str:
    """Compact seconds label used in frame filenames, e.g. 0.42 -> '0.42'."""
    return f"{seconds:.2f}".rstrip("0").rstrip(".") or "0"


# --------------------------------------------------------------------------- #
# metadata
# --------------------------------------------------------------------------- #
def _parse_fps(rate: str | None) -> float | None:
    if not rate:
        return None
    if "/" in rate:
        num, _, den = rate.partition("/")
        try:
            n, d = float(num), float(den)
            return n / d if d else None
        except ValueError:
            return None
    try:
        return float(rate)
    except ValueError:
        return None


def get_metadata(video_path: str) -> dict:
    require("ffprobe")
    src = str(Path(video_path).resolve())
    result = run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", src,
    ])
    if result.returncode != 0:
        raise MotiscopeError(f"ffprobe failed on {video_path}: {result.stderr.strip()}")

    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])
    fmt = data.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = float(fmt.get("duration") or video.get("duration") or 0.0)
    fps = _parse_fps(video.get("avg_frame_rate")) or _parse_fps(video.get("r_frame_rate"))
    return {
        "path": src,
        "duration_seconds": round(duration, 3),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": round(fps, 3) if fps else None,
        "codec": video.get("codec_name"),
        "size_bytes": int(fmt.get("size") or 0),
        "has_audio": audio is not None,
    }


def source_hash(video_path: str) -> str:
    """Stable short id from the first 64KB + file size (cheap, no full read)."""
    p = Path(video_path).resolve()
    h = hashlib.sha256()
    with p.open("rb") as fh:
        h.update(fh.read(64 * 1024))
    h.update(str(p.stat().st_size).encode())
    return h.hexdigest()[:8]


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-.")
    return slug[:48] or "clip"


def resolve_out_dir(video_path: str, base: str = ".motiscope") -> Path:
    """Per-video working dir: <base>/<stem>-<hash>/ (gitignored)."""
    p = Path(video_path)
    out = Path(base) / f"{slugify(p.stem)}-{source_hash(video_path)}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "frames").mkdir(exist_ok=True)
    return out


# --------------------------------------------------------------------------- #
# perceptual dedup (ported from claude-video frames.py)
# --------------------------------------------------------------------------- #
def frame_delta(a: bytes, b: bytes) -> float:
    """Mean absolute per-pixel difference (0-255) between two grayscale buffers.
    Mismatched lengths => treated as maximally different (fail-open)."""
    if not a or len(a) != len(b):
        return float("inf")
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def thumb_frames(paths: list[Path], thumb: int = DEDUP_THUMB) -> list[bytes]:
    """Decode a numbered image sequence to grayscale thumbnails in one ffmpeg
    pass. Returns [] on any mismatch so callers can skip dedup gracefully."""
    if not paths:
        return []
    paths = [Path(p) for p in paths]
    m = re.match(r"(.*?)(\d+)(\.[A-Za-z0-9]+)$", paths[0].name)
    if m is None:
        return []
    prefix, digits, ext = m.group(1), m.group(2), m.group(3)
    pattern = str(paths[0].parent / f"{prefix}%0{len(digits)}d{ext}")
    result = run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-start_number", str(int(digits)), "-i", pattern,
        "-vf", f"scale={thumb}:{thumb},format=gray", "-f", "rawvideo", "-",
    ], text=False)
    if result.returncode != 0:
        return []
    chunk = thumb * thumb
    data = result.stdout
    if len(data) != chunk * len(paths):
        return []
    return [data[i * chunk:(i + 1) * chunk] for i in range(len(paths))]


def dedupe_perceptual(candidates: list[dict], threshold: float = DEDUP_THRESHOLD,
                      thumb: int = DEDUP_THUMB) -> tuple[list[dict], int]:
    """Greedily drop frames within `threshold` mean per-pixel diff of the last
    kept frame. Deletes dropped files, reindexes survivors. Each candidate is a
    dict with a 'path' key. Fail-open: unchanged if thumbnails unavailable."""
    if len(candidates) <= 1:
        return candidates, 0
    thumbs = thumb_frames([Path(c["path"]) for c in candidates], thumb)
    if len(thumbs) != len(candidates):
        return candidates, 0
    kept = [candidates[0]]
    last = thumbs[0]
    dropped: list[dict] = []
    for cand, t in zip(candidates[1:], thumbs[1:]):
        if frame_delta(t, last) <= threshold:
            dropped.append(cand)
        else:
            kept.append(cand)
            last = t
    for cand in dropped:
        try:
            Path(cand["path"]).unlink()
        except OSError:
            pass
    for i, frame in enumerate(kept):
        frame["index"] = i
    return kept, len(dropped)


def even_indices(count: int, n: int) -> list[int]:
    """Indices of n evenly-spaced items out of count (first + last kept)."""
    if n >= count:
        return list(range(count))
    if n <= 1:
        return [0]
    return [round(i * (count - 1) / (n - 1)) for i in range(n)]


def even_sample(candidates: list[dict], n: int) -> list[dict]:
    """Keep n evenly-spaced candidates, delete the dropped files, reindex."""
    selected = [candidates[i] for i in even_indices(len(candidates), n)]
    keep = {s["path"] for s in selected}
    for cand in candidates:
        if cand["path"] not in keep:
            try:
                Path(cand["path"]).unlink()
            except OSError:
                pass
    for i, frame in enumerate(selected):
        frame["index"] = i
    return selected
