#!/usr/bin/env python3
"""Motion timeline analysis for motiscope.

Two passes:
  Pass A — a dense per-frame *motion-energy* curve + a coarse *motion grid*,
           decoded to tiny grayscale thumbnails at native/high fps (NOT capped
           at 2 fps). Pure numbers -> zero image tokens. Source of truth for
           timing, easing, beats, and stagger. The mean-abs-diff detector is
           extended from claude-video's dedup heuristic (MIT).
  Pass B — ffmpeg signal filters (scdet / blackdetect / freezedetect / siti /
           signalstats), ported from claude-video-vision's analyzers.ts (MIT),
           tuned for UI animation. Refines segment boundaries and fades.

Writes <out-dir>/motion.json and returns the analysis dict.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import mvlib
except ImportError:  # allow `python3 scripts/analyze_motion.py` from repo root
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mvlib

MAX_ANALYSIS_FPS = 60.0
DEFAULT_MAX_SAMPLES = 1200
DEFAULT_THUMB = 32
DEFAULT_GRID = 8
MIN_RUN_SECONDS = 0.10          # merge motion/still runs shorter than this
HOLD_INTERIOR_MIN = 0.12        # an interior still run this long is a real settle/hold
HOLD_BOUNDARY_MIN = 0.35        # a leading/trailing still run must be this long to be a hold
                                # (shorter boundary lulls are ease-in/out ramps, kept in the move)
NOISE_FLOOR = 0.05              # absolute per-pixel-diff noise floor (0-255 scale)
HOLD_ENERGY_FRACTION = 0.18     # frames below this fraction of peak energy are "still"
LOCALIZED_CELL_FRACTION = 0.10  # fraction of grid cells averaged for localized energy


def hold_threshold(motion_ref: float) -> float:
    """Energy below which a frame is 'still', relative to a reference motion level
    (see robust_motion_ref), with a small noise floor."""
    return max(NOISE_FLOOR, HOLD_ENERGY_FRACTION * motion_ref)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = min(len(s) - 1, max(0, int(pct / 100.0 * len(s))))
    return s[k]


def robust_motion_ref(energy: list[float]) -> float:
    """Reference motion level for thresholding, robust to cut/fade spikes. A hard cut or
    a fast full-screen fade produces enormous energy, and on scroll-heavy clips those
    transitions can be >10% of frames; using the max (or a high percentile) would inflate
    the threshold and hide the smaller in-section animations. The 75th percentile tracks
    the typical strong-motion level instead, floored only by the noise floor."""
    if not energy:
        return 0.0
    return max(_percentile(energy, 75), NOISE_FLOOR)


# --------------------------------------------------------------------------- #
# Pass A: motion-energy curve + motion grid
# --------------------------------------------------------------------------- #
def choose_fps(duration: float, native_fps: float | None, max_samples: int) -> float:
    native = native_fps or 30.0
    fps = min(native, MAX_ANALYSIS_FPS)
    if duration > 0 and fps * duration > max_samples:
        fps = max(1.0, max_samples / duration)
    return round(fps, 3)


def _seek_args(start: float | None, end: float | None) -> list[str]:
    """Fast input seek to a [start, end] window. Placed BEFORE -i. Output
    timestamps reset to ~0, so callers offset emitted times by `start`."""
    args: list[str] = []
    if start:
        args += ["-ss", f"{start:.3f}"]
    if end is not None:
        args += ["-t", f"{max(0.05, end - (start or 0.0)):.3f}"]
    return args


def _cell_layout(thumb: int, grid: int):
    """Map each pixel index (row-major, width=thumb) to a grid cell + count."""
    cell_of = [0] * (thumb * thumb)
    counts = [0] * (grid * grid)
    for p in range(thumb * thumb):
        row, col = divmod(p, thumb)
        cr = min(grid - 1, row * grid // thumb)
        cc = min(grid - 1, col * grid // thumb)
        cell = cr * grid + cc
        cell_of[p] = cell
        counts[cell] += 1
    return cell_of, counts


def sample_energy(video: str, fps: float, thumb: int, grid: int,
                  start: float | None = None, end: float | None = None) -> dict:
    """Decode the clip (or [start,end] window) to grayscale thumbnails and compute
    the per-frame global motion energy plus per-cell energy aggregates."""
    mvlib.require("ffmpeg")
    result = mvlib.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        *_seek_args(start, end),
        "-i", str(Path(video).resolve()),
        "-vf", f"fps={fps},scale={thumb}:{thumb},format=gray",
        "-f", "rawvideo", "-",
    ], text=False)
    if result.returncode != 0:
        raise mvlib.MotiscopeError("ffmpeg motion sampling failed")

    N = thumb * thumb
    data = result.stdout
    count = len(data) // N
    if count < 2:
        return {"fps": fps, "count": count, "energy": [], "cells": []}
    frames = [data[i * N:(i + 1) * N] for i in range(count)]

    cell_of, cell_px = _cell_layout(thumb, grid)
    G2 = grid * grid
    energy = [0.0]
    cell_series = [[0.0] for _ in range(G2)]  # per-cell energy over time

    prev = frames[0]
    for i in range(1, count):
        cur = frames[i]
        cell_sum = [0] * G2
        total = 0
        for p in range(N):
            d = cur[p] - prev[p]
            if d < 0:
                d = -d
            total += d
            cell_sum[cell_of[p]] += d
        energy.append(total / N)
        for c in range(G2):
            cell_series[c].append(cell_sum[c] / cell_px[c] if cell_px[c] else 0.0)
        prev = cur

    localized = _localized_energy(cell_series, count, G2)
    return {"fps": fps, "count": count, "energy": energy, "localized": localized,
            "cell_series": cell_series, "grid": grid, "cell_px": cell_px}


def _localized_energy(cell_series: list[list[float]], count: int, G2: int) -> list[float]:
    """Per-frame motion signal from the most-active grid cells only, so a small
    element moving on a large static canvas isn't diluted by the background.
    Averages the top-K cells each frame; for full-frame motion (all cells active)
    this equals the global mean, so there's no regression on big animations."""
    k = max(2, round(G2 * LOCALIZED_CELL_FRACTION))
    out = [0.0] * count
    for i in range(1, count):
        vals = sorted((cell_series[c][i] for c in range(G2)), reverse=True)
        out[i] = sum(vals[:k]) / k
    return out


def summarize_grid(cell_series: list[list[float]], fps: float, grid: int) -> dict:
    """Per-cell aggregates (onset / peak / centroid) + a stagger direction hint."""
    active = []
    cell_totals = [sum(s) for s in cell_series]
    max_total = max(cell_totals) if cell_totals else 0.0
    if max_total <= 0:
        return {"rows": grid, "cols": grid, "active_cells": [], "stagger_hint": None}

    for c, series in enumerate(cell_series):
        total = cell_totals[c]
        if total < 0.2 * max_total:
            continue
        r, col = divmod(c, grid)
        peak_val = max(series)
        peak_idx = series.index(peak_val)
        onset_idx = next((i for i, v in enumerate(series) if v > 0.15 * peak_val), peak_idx)
        centroid = (sum(i * v for i, v in enumerate(series)) / total) / fps if total else 0.0
        active.append({
            "row": r, "col": col,
            "total": round(total, 2),
            "onset_s": round(onset_idx / fps, 3),
            "peak_s": round(peak_idx / fps, 3),
            "centroid_s": round(centroid, 3),
        })

    hint = _stagger_hint(active)
    return {"rows": grid, "cols": grid, "active_cells": active, "stagger_hint": hint}


def _corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def _stagger_hint(active: list[dict]) -> dict | None:
    if len(active) < 3:
        return None
    cols = [a["col"] for a in active]
    rows = [a["row"] for a in active]
    t = [a["centroid_s"] for a in active]
    c_col, c_row = _corr(cols, t), _corr(rows, t)
    direction, strength = None, 0.0
    if abs(c_col) >= abs(c_row) and abs(c_col) > 0.35:
        direction = "left-to-right" if c_col > 0 else "right-to-left"
        strength = abs(c_col)
    elif abs(c_row) > 0.35:
        direction = "top-to-bottom" if c_row > 0 else "bottom-to-top"
        strength = abs(c_row)
    if not direction:
        return None
    span = max(t) - min(t)
    groups = max(1, len(set(cols if "right" in direction else rows)) - 1)
    return {
        "direction": direction,
        "confidence": round(strength, 2),
        "span_ms": round(span * 1000),
        "each_ms_estimate": round(span * 1000 / groups) if groups else 0,
    }


# --------------------------------------------------------------------------- #
# Easing classification (from the velocity/energy profile)
# --------------------------------------------------------------------------- #
def classify_easing(seg: list[float]) -> dict:
    """Classify a move segment's easing from its energy (≈ velocity) profile."""
    seg = [v for v in seg]
    n = len(seg)
    if n < 3:
        return {"ease": "linear", "confidence": "low", "stats": {}}
    peak = max(seg) or 1.0
    norm = [v / peak for v in seg]
    third = max(1, n // 3)
    f = sum(norm[:third]) / third
    m = sum(norm[third:2 * third]) / max(1, len(norm[third:2 * third]))
    l = sum(norm[-third:]) / third
    mean = sum(norm) / n
    cv = (sum((v - mean) ** 2 for v in norm) / n) ** 0.5 / mean if mean else 0.0
    # least-squares slope over normalized index
    xs = list(range(n))
    mx = sum(xs) / n
    slope = sum((x - mx) * (v - mean) for x, v in zip(xs, norm)) / (sum((x - mx) ** 2 for x in xs) or 1)
    slope *= n  # scale to a 0..1-ish range across the segment

    peak_idx = norm.index(max(norm))
    peak_pos = peak_idx / (n - 1)

    # Overshoot / spring: a secondary bump after a dip past the main peak.
    spring = False
    if peak_idx < n - 2:
        tail = norm[peak_idx:]
        tmin = min(tail)
        after_min_idx = tail.index(tmin)
        if tmin < 0.4 and after_min_idx < len(tail) - 1:
            rebound = max(tail[after_min_idx:])
            if rebound > tmin + 0.25:
                spring = True

    if spring:
        ease, conf = "spring", "estimated"
    elif cv < 0.28:
        ease, conf = "linear", "measured"
    elif m > f * 1.25 and m > l * 1.25 and 0.3 < peak_pos < 0.7:
        ease, conf = "ease-in-out", "measured"
    elif slope > 0.15:
        ease, conf = "ease-in", "measured"
    elif slope < -0.15:
        ease, conf = "ease-out", "measured"
    elif peak_pos < 0.4:
        ease, conf = "ease-out", "estimated"
    elif peak_pos > 0.6:
        ease, conf = "ease-in", "estimated"
    else:
        ease, conf = "ease-in-out", "estimated"

    return {"ease": ease, "confidence": conf,
            "stats": {"cv": round(cv, 3), "slope": round(slope, 3),
                      "peak_pos": round(peak_pos, 3),
                      "front": round(f, 3), "mid": round(m, 3), "back": round(l, 3)}}


# --------------------------------------------------------------------------- #
# Pass B: ffmpeg signal filters (parsers ported from analyzers.ts)
# --------------------------------------------------------------------------- #
def run_signal_pass(video: str, out_dir: Path,
                    start: float | None = None, end: float | None = None) -> dict:
    meta_file = out_dir / "video_meta.txt"
    vf = (
        "scdet=threshold=10,"
        "blackdetect=d=0.1:pic_th=0.98:pix_th=0.10,"
        "freezedetect=n=-50dB:d=0.15,"
        "siti=print_summary=1,"
        "signalstats,"
        f"metadata=mode=print:file={meta_file.as_posix()}"
    )
    result = mvlib.run([
        "ffmpeg", "-hide_banner", *_seek_args(start, end),
        "-i", str(Path(video).resolve()),
        "-vf", vf, "-an", "-f", "null", "-",
    ])
    if result.returncode != 0:
        return {"available": False, "scene_cuts": [], "black_intervals": [],
                "freezes": [], "brightness": None, "siti": {}, "content_profile": None}

    stderr = result.stderr or ""
    meta = meta_file.read_text() if meta_file.exists() else ""
    si = parse_siti(stderr)
    return {
        "available": True,
        "scene_cuts": parse_scdet(stderr),
        "black_intervals": parse_black(stderr),
        "freezes": parse_freeze(stderr),
        "brightness": parse_brightness(meta),
        "siti": si,
        "content_profile": derive_content_profile(si.get("si_avg"), si.get("ti_avg")),
    }


def parse_scdet(stderr: str) -> list[dict]:
    out = []
    for m in re.finditer(r"lavfi\.scd\.score[=:]\s*([\d.]+).*?lavfi\.scd\.time[=:]\s*([\d.]+)", stderr):
        score = float(m.group(1))
        if score >= 10.0:
            out.append({"time_s": round(float(m.group(2)), 3), "score": round(score, 2)})
    return out


def parse_black(stderr: str) -> list[dict]:
    out = []
    for m in re.finditer(r"black_start:([\d.]+)\s+black_end:([\d.]+)\s+black_duration:([\d.]+)", stderr):
        out.append({"start_s": round(float(m.group(1)), 3),
                    "end_s": round(float(m.group(2)), 3),
                    "duration": round(float(m.group(3)), 3)})
    return out


def parse_freeze(stderr: str) -> list[dict]:
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", stderr)]
    ends = [float(x) for x in re.findall(r"freeze_end:\s*([\d.]+)", stderr)]
    durs = [float(x) for x in re.findall(r"freeze_duration:\s*([\d.]+)", stderr)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s + (durs[i] if i < len(durs) else 0.0)
        out.append({"start_s": round(s, 3), "end_s": round(e, 3),
                    "duration": round(durs[i] if i < len(durs) else e - s, 3)})
    return out


def parse_siti(stderr: str) -> dict:
    si = re.search(r"Spatial Information:\s*\n\s*Average:\s*([\d.]+)", stderr)
    ti = re.search(r"Temporal Information:\s*\n\s*Average:\s*([\d.]+)", stderr)
    if si or ti:
        return {"si_avg": round(float(si.group(1)), 2) if si else None,
                "ti_avg": round(float(ti.group(1)), 2) if ti else None}
    siv = [float(x) for x in re.findall(r"lavfi\.siti\.si=([\d.]+)", stderr)]
    tiv = [float(x) for x in re.findall(r"lavfi\.siti\.ti=([\d.]+)", stderr)]
    avg = lambda a: round(sum(a) / len(a), 2) if a else None
    return {"si_avg": avg(siv), "ti_avg": avg(tiv)}


def parse_brightness(meta: str) -> dict | None:
    """Per-frame YAVG brightness (0-255) from the metadata print file."""
    times, vals = [], []
    blocks = re.split(r"(?m)^(?:# )?frame:", meta)
    for block in blocks:
        pm = re.search(r"pts_time:([\d.]+)", block)
        ym = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", block)
        if pm and ym:
            times.append(round(float(pm.group(1)), 3))
            vals.append(round(float(ym.group(1)), 2))
    if len(vals) < 2:
        return None
    return _downsample_series(times, vals, 300)


def derive_content_profile(si_avg, ti_avg) -> str:
    if si_avg is None and ti_avg is None:
        return "unknown (no motion analysis data)"
    si_cls = "unknown" if si_avg is None else "high" if si_avg > 50 else "moderate" if si_avg > 25 else "low"
    ti_cls = "unknown" if ti_avg is None else "high" if ti_avg > 30 else "moderate" if ti_avg > 10 else "low"
    table = {
        "high": {"high": "high visual complexity, high motion (busy scenes)",
                 "moderate": "high visual complexity, moderate motion",
                 "low": "high visual complexity, low motion (detailed static shots)",
                 "unknown": "high visual complexity, unknown motion"},
        "moderate": {"high": "moderate visual complexity, high motion",
                     "moderate": "moderate visual complexity, moderate motion",
                     "low": "moderate visual complexity, low motion",
                     "unknown": "moderate visual complexity, unknown motion"},
        "low": {"high": "low visual complexity, high motion (simple fast-moving UI/animation)",
                "moderate": "low visual complexity, moderate motion (simple scene with movement)",
                "low": "low visual complexity, low motion (simple static graphics)",
                "unknown": "low visual complexity, unknown motion"},
        "unknown": {"high": "unknown complexity, high motion", "moderate": "unknown complexity, moderate motion",
                    "low": "unknown complexity, low motion", "unknown": "unknown content profile"},
    }
    return table.get(si_cls, {}).get(ti_cls, "unknown content profile")


def _downsample_series(times: list[float], vals: list[float], cap: int) -> dict:
    n = len(vals)
    if n <= cap:
        return {"times": times, "values": vals}
    idx = mvlib.even_indices(n, cap)
    return {"times": [times[i] for i in idx], "values": [vals[i] for i in idx]}


# --------------------------------------------------------------------------- #
# Segmentation, fades, beats, salient timestamps
# --------------------------------------------------------------------------- #
def _runs(moving: list[bool]) -> list[tuple[bool, int, int]]:
    runs, start = [], 0
    for i in range(1, len(moving)):
        if moving[i] != moving[start]:
            runs.append((moving[start], start, i - 1))
            start = i
    runs.append((moving[start], start, len(moving) - 1))
    return runs


def _coalesce(runs):
    """Merge adjacent runs that share a flag."""
    if not runs:
        return runs
    out = [runs[0]]
    for flag, a, b in runs[1:]:
        pf, pa, pb = out[-1]
        if flag == pf:
            out[-1] = (pf, pa, b)
        else:
            out.append((flag, a, b))
    return out


def _merge_short(runs, min_frames):
    runs = list(runs)
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i, (flag, a, b) in enumerate(runs):
            if b - a + 1 < min_frames:
                if i > 0:
                    pf, pa, _ = runs[i - 1]
                    runs[i - 1] = (pf, pa, b)
                    del runs[i]
                else:
                    nf, _, nb = runs[i + 1]
                    runs[i + 1] = (nf, a, nb)
                    del runs[i]
                changed = True
                break
    return _coalesce(runs)


def _reclassify_holds(runs, fps):
    """A still run is only a genuine hold if it is long enough. Interior lulls need
    HOLD_INTERIOR_MIN; leading/trailing lulls need HOLD_BOUNDARY_MIN (otherwise they
    are the slow start/end of an ease and belong to the move). Short still runs are
    flipped to 'moving' and coalesced back into the neighbouring motion."""
    out = list(runs)
    for i, (flag, a, b) in enumerate(out):
        if flag:  # already moving
            continue
        dur = (b - a + 1) / fps
        boundary = i == 0 or i == len(out) - 1
        needed = HOLD_BOUNDARY_MIN if boundary else HOLD_INTERIOR_MIN
        if dur < needed:
            out[i] = (True, a, b)
    return _coalesce(out)


def detect_fades(brightness: dict | None, black_intervals: list[dict], duration: float) -> list[dict]:
    fades = []
    for bi in black_intervals:
        if bi["start_s"] <= 0.12:
            fades.append({"kind": "fade-in", "start_ms": 0, "end_ms": round(bi["end_s"] * 1000)})
        elif bi["end_s"] >= duration - 0.12:
            fades.append({"kind": "fade-out", "start_ms": round(bi["start_s"] * 1000),
                          "end_ms": round(duration * 1000)})
    if brightness and len(brightness["values"]) >= 4:
        t, v = brightness["times"], brightness["values"]
        hi = max(v)
        # fade-in from dark
        if v[0] < 40 and hi > 60:
            j = next((i for i, x in enumerate(v) if x >= 0.6 * hi), None)
            if j and j > 0:
                fades.append({"kind": "fade-in", "start_ms": 0, "end_ms": round(t[j] * 1000)})
        # fade-out to dark
        if v[-1] < 40 and hi > 60:
            j = next((i for i in range(len(v) - 1, -1, -1) if v[i] >= 0.6 * hi), None)
            if j is not None and j < len(v) - 1:
                fades.append({"kind": "fade-out", "start_ms": round(t[j] * 1000),
                              "end_ms": round(duration * 1000)})
    return fades


def build_segments(energy: list[float], fps: float, fades: list[dict],
                   freezes: list[dict], peak_energy: float) -> list[dict]:
    n = len(energy)
    if n < 2:
        return []
    hold_thr = hold_threshold(peak_energy)
    moving = [e > hold_thr for e in energy]
    min_frames = max(2, round(MIN_RUN_SECONDS * fps))
    runs = _reclassify_holds(_merge_short(_runs(moving), min_frames), fps)

    segs = []
    for flag, a, b in runs:
        start_ms, end_ms = round(a / fps * 1000), round(b / fps * 1000)
        if flag:
            info = classify_easing(energy[a:b + 1])
            segs.append({"kind": "move", "start_ms": start_ms, "end_ms": end_ms,
                         "ease": info["ease"], "ease_confidence": info["confidence"],
                         "peak_energy": round(max(energy[a:b + 1]), 3), "stats": info["stats"]})
        else:
            segs.append({"kind": "hold", "start_ms": start_ms, "end_ms": end_ms})

    # freezedetect only CONFIRMS existing holds — it must not convert a move to a
    # hold. freezedetect measures whole-frame stillness, so a small element moving on
    # a large static background reads as "frozen"; the localized energy above is the
    # authoritative motion signal, so we defer to it for move/hold and use freeze
    # only to annotate holds it agrees with.
    for fz in freezes:
        fs, fe = round(fz["start_s"] * 1000), round(fz["end_s"] * 1000)
        if fe - fs < HOLD_INTERIOR_MIN * 1000:
            continue
        for s in segs:
            if s["kind"] == "hold" and min(s["end_ms"], fe) - max(s["start_ms"], fs) > 0:
                s.setdefault("notes", "confirmed by freezedetect")

    # relabel fades over move segments
    for fd in fades:
        for s in segs:
            if s["kind"] != "move":
                continue
            overlap = min(s["end_ms"], fd["end_ms"]) - max(s["start_ms"], fd["start_ms"])
            if overlap > 0.5 * (s["end_ms"] - s["start_ms"]):
                s["kind"] = fd["kind"]
    return segs


def find_beats(energy: list[float], fps: float, peak_energy: float) -> dict:
    """Prominent local maxima (peak motion) and minima (settles/keyposes), spaced
    apart so noisy constant-velocity motion doesn't emit a beat every frame."""
    hold_thr = hold_threshold(peak_energy)
    win = max(1, round(0.05 * fps))          # ±window for a strict local extremum
    min_sep = max(1, round(0.20 * fps))      # minimum frames between beats of a kind
    peaks, keyposes = [], []
    last_peak = last_key = -10 ** 9
    n = len(energy)
    for i in range(1, n - 1):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        window = energy[lo:hi]
        e = energy[i]
        if e >= max(window) and e > 0.4 * peak_energy and i - last_peak >= min_sep:
            peaks.append(round(i / fps, 3)); last_peak = i
        elif e <= min(window) and e < hold_thr * 1.5 and i - last_key >= min_sep:
            keyposes.append(round(i / fps, 3)); last_key = i
    return {"peaks": peaks, "keyposes": keyposes}


LOOP_MIN_CORR = 0.7             # peak autocorrelation to call something a loop
LOOP_MIN_MOVING_FRACTION = 0.5  # a loop moves continuously, not mostly a hold


def detect_loop(energy: list[float], fps: float, peak_energy: float | None = None) -> dict:
    """Detect a looping animation by autocorrelating the motion-energy curve. A loop
    repeats, so its energy curve is periodic; the strongest autocorrelation lag above
    a minimum period is the candidate loop length. Guards against false positives:
    the clip must be mostly *moving* (not a hold with a periodic-looking blip), the
    peak correlation must be strong, and the second harmonic (2×period) must also
    correlate — a one-off burst won't repeat at 2×.

    Note: energy is speed-based, so back-and-forth (yoyo) motion produces a period
    that is HALF the visual cycle — the caller flags this so recreation can choose
    loop vs. yoyo. Steady constant-velocity loops (e.g. uniform rotation) have flat
    energy and are intentionally NOT detected here."""
    n = len(energy)
    if n < 24 or fps <= 0:
        return {"is_loop": False, "period_ms": None, "confidence": 0.0}
    if peak_energy is None:
        peak_energy = max(energy) if energy else 0.0
    thr = hold_threshold(peak_energy)
    if sum(1 for e in energy if e > thr) / n < LOOP_MIN_MOVING_FRACTION:
        return {"is_loop": False, "period_ms": None, "confidence": 0.0}

    mean = sum(energy) / n
    e = [x - mean for x in energy]
    denom = sum(x * x for x in e) or 1.0

    def autocorr(lag: int) -> float:
        return sum(e[i] * e[i + lag] for i in range(n - lag)) / denom

    min_lag = max(3, int(0.3 * fps))
    max_lag = n // 2                        # need at least two cycles to be sure
    best_lag, best_corr = 0, 0.0
    for lag in range(min_lag, max_lag):
        c = autocorr(lag)
        if c > best_corr:
            best_corr, best_lag = c, lag

    harmonic_ok = 2 * best_lag >= n or autocorr(2 * best_lag) >= 0.5 * best_corr
    is_loop = best_corr >= LOOP_MIN_CORR and harmonic_ok and best_lag > 0
    return {"is_loop": is_loop,
            "period_ms": round(best_lag / fps * 1000) if is_loop else None,
            "confidence": round(best_corr, 2)}


def salient_timestamps(duration: float, segments: list[dict], beats: dict,
                       cuts: list[dict], fades: list[dict]) -> list[dict]:
    pts: list[tuple[float, str]] = [(0.0, "start"), (round(duration, 3), "end")]
    for s in segments:
        pts.append((s["start_ms"] / 1000, {"hold": "holdstart", "move": "segstart",
                    "fade-in": "fadein", "fade-out": "fadeout"}.get(s["kind"], "segstart")))
    for t in beats["peaks"]:
        pts.append((t, "peak"))
    for t in beats["keyposes"]:
        pts.append((t, "keypose"))
    for c in cuts:
        pts.append((c["time_s"], "cut"))
    for f in fades:
        pts.append((f["end_ms"] / 1000, f["kind"]))
    # de-dup within 50ms, keep the more specific reason (non-generic wins)
    generic = {"segstart", "keypose"}
    pts.sort()
    out: list[dict] = []
    for t, reason in pts:
        t = max(0.0, min(round(t, 3), round(duration, 3)))
        if out and abs(out[-1]["t"] - t) < 0.05:
            if out[-1]["reason"] in generic and reason not in generic:
                out[-1]["reason"] = reason
            continue
        out.append({"t": t, "reason": reason})
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _apply_offset(result: dict, off: float) -> None:
    """Shift all window-relative timestamps to absolute source time (in place)."""
    if off <= 0:
        return
    r3 = lambda x: round(x + off, 3)
    result["energy"]["start_s"] = round(off, 3)
    pk = result["energy"].get("peak")
    if pk:
        pk["time_s"] = r3(pk["time_s"])
    for s in result["segments"]:
        s["start_ms"] = round(s["start_ms"] + off * 1000)
        s["end_ms"] = round(s["end_ms"] + off * 1000)
    result["beats"]["peaks"] = [r3(t) for t in result["beats"]["peaks"]]
    result["beats"]["keyposes"] = [r3(t) for t in result["beats"]["keyposes"]]
    for e in result["salient"]:
        e["t"] = r3(e["t"])
    sig = result.get("signal", {})
    for c in sig.get("scene_cuts", []):
        c["time_s"] = r3(c["time_s"])
    for b in sig.get("black_intervals", []):
        b["start_s"], b["end_s"] = r3(b["start_s"]), r3(b["end_s"])
    for f in sig.get("freezes", []):
        f["start_s"], f["end_s"] = r3(f["start_s"]), r3(f["end_s"])
    if sig.get("brightness"):
        sig["brightness"]["times"] = [r3(t) for t in sig["brightness"]["times"]]


def analyze(video: str, out_dir: Path, *, fps="auto", thumb: int = DEFAULT_THUMB,
            grid: int = DEFAULT_GRID, max_samples: int = DEFAULT_MAX_SAMPLES,
            start: float | None = None, end: float | None = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = mvlib.get_metadata(video)
    duration = meta["duration_seconds"]

    # Focus window (absolute source seconds). Analysis runs on the window in
    # relative time; timestamps are shifted back to absolute at the end.
    win_start = max(0.0, start) if start else 0.0
    win_end = min(end, duration) if end is not None else duration
    win_dur = max(0.05, win_end - win_start)
    windowed = win_start > 0 or (end is not None and win_end < duration)

    use_fps = choose_fps(win_dur, meta.get("fps"), max_samples) if fps == "auto" else float(fps)

    a = sample_energy(video, use_fps, thumb, grid,
                      start=win_start if windowed else None,
                      end=win_end if windowed else None)
    # Primary signal is the localized (top-K cell) energy — robust to small elements
    # on a large canvas. The global mean is kept for reference only.
    global_energy = a.get("energy", [])
    energy = a.get("localized") or global_energy
    peak_energy = max(energy) if energy else 0.0
    peak_idx = energy.index(peak_energy) if energy else 0

    signal = run_signal_pass(video, out_dir,
                             start=win_start if windowed else None,
                             end=win_end if windowed else None)
    fades = detect_fades(signal.get("brightness"), signal.get("black_intervals", []), win_dur)
    # Reference for thresholding is robust to brief cut/fade spikes so the smaller
    # in-section animations aren't swamped and mislabeled as holds.
    motion_ref = robust_motion_ref(energy)
    segments = build_segments(energy, use_fps, fades, signal.get("freezes", []), motion_ref)
    beats = find_beats(energy, use_fps, motion_ref) if energy else {"peaks": [], "keyposes": []}
    grid_summary = summarize_grid(a["cell_series"], use_fps, grid) if a.get("cell_series") else \
        {"rows": grid, "cols": grid, "active_cells": [], "stagger_hint": None}
    salient = salient_timestamps(win_dur, segments, beats, signal.get("scene_cuts", []), fades)

    loop = detect_loop(energy, use_fps, motion_ref) if energy else \
        {"is_loop": False, "period_ms": None, "confidence": 0.0}

    move_segs = [s for s in segments if s["kind"] == "move"]
    dominant = max(move_segs, key=lambda s: s["end_ms"] - s["start_ms"], default=None)
    dominant_ease = dominant["ease"] if dominant else "linear"

    energy_curve = {"dt": round(1 / use_fps, 4) if use_fps else 0,
                    "start_s": 0.0,
                    "signal": "localized-topk",
                    "values": [round(e, 3) for e in energy],
                    "peak": {"time_s": round(peak_idx / use_fps, 3) if use_fps else 0,
                             "value": round(peak_energy, 3)},
                    "mean": round(sum(energy) / len(energy), 3) if energy else 0,
                    "global_mean": round(sum(global_energy) / len(global_energy), 3) if global_energy else 0,
                    "motion_ref": round(motion_ref, 3),
                    "hold_threshold": round(hold_threshold(motion_ref), 3)}

    result = {
        "video": meta,
        "window": {"start_s": round(win_start, 3), "end_s": round(win_end, 3),
                   "duration_s": round(win_dur, 3), "focused": windowed},
        "sampling": {"fps": use_fps, "thumb": thumb, "grid": grid, "frame_count": a.get("count", 0)},
        "energy": energy_curve,
        "grid": grid_summary,
        "signal": signal,
        "segments": segments,
        "beats": beats,
        "salient": salient,
        "dominant_easing": dominant_ease,
        "loop": loop,
    }
    _apply_offset(result, win_start)
    result["summary"] = _summary(meta, result["segments"], dominant_ease, signal,
                                 grid_summary, result["window"], loop)
    (out_dir / "motion.json").write_text(json.dumps(result, indent=2))
    return result


def _summary(meta, segments, dominant_ease, signal, grid_summary, window=None, loop=None) -> str:
    dur = meta["duration_seconds"]
    kinds = [s["kind"] for s in segments]
    parts = [f"{dur:.2f}s clip at {meta.get('fps') or '?'}fps, {meta.get('width')}x{meta.get('height')}."]
    if window and window.get("focused"):
        parts.append(f"Focused on {window['start_s']:.2f}-{window['end_s']:.2f}s.")
    parts.append(f"{len(segments)} segment(s): {', '.join(kinds) if kinds else 'none detected'}.")
    parts.append(f"Dominant easing: {dominant_ease}.")
    if loop and loop.get("is_loop"):
        parts.append(f"Loops every ~{loop['period_ms']}ms (confidence {loop['confidence']}).")
    if signal.get("content_profile"):
        parts.append(f"Profile: {signal['content_profile']}.")
    hint = grid_summary.get("stagger_hint")
    if hint:
        parts.append(f"Stagger hint: {hint['direction']} (~{hint['each_ms_estimate']}ms each).")
    return " ".join(parts)


def _parse_args(argv: list[str]) -> dict:
    opts = {"fps": "auto", "thumb": DEFAULT_THUMB, "grid": DEFAULT_GRID,
            "max_samples": DEFAULT_MAX_SAMPLES, "json": False, "start": None, "end": None}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--fps":
            opts["fps"] = argv[i + 1]; i += 2
        elif arg == "--thumb":
            opts["thumb"] = int(argv[i + 1]); i += 2
        elif arg == "--grid":
            opts["grid"] = int(argv[i + 1]); i += 2
        elif arg == "--max-samples":
            opts["max_samples"] = int(argv[i + 1]); i += 2
        elif arg == "--start":
            opts["start"] = mvlib.parse_time(argv[i + 1]); i += 2
        elif arg == "--end":
            opts["end"] = mvlib.parse_time(argv[i + 1]); i += 2
        elif arg == "--json":
            opts["json"] = True; i += 1
        else:
            i += 1
    return opts


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: analyze_motion.py <video> <out-dir> [--fps auto|N] [--thumb 32] "
              "[--grid 8] [--max-samples 1200] [--start T] [--end T] [--json]", file=sys.stderr)
        return 2
    video, out_dir = argv[0], Path(argv[1])
    opts = _parse_args(argv[2:])
    try:
        result = analyze(video, out_dir, fps=opts["fps"], thumb=opts["thumb"],
                         grid=opts["grid"], max_samples=opts["max_samples"],
                         start=opts["start"], end=opts["end"])
    except mvlib.MotiscopeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if opts["json"]:
        print(json.dumps(result, indent=2))
    else:
        print(result["summary"])
        print(f"motion.json -> {out_dir / 'motion.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
