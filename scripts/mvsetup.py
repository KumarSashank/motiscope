#!/usr/bin/env python3
"""Preflight + config scaffold for motiscope (the doctor skill's engine).

Required binaries: ffmpeg, ffprobe (no yt-dlp, no pip installs — the pipeline is
stdlib-only). This script NEVER auto-installs; the doctor skill asks consent and
runs the installer itself. It scaffolds ~/.config/motiscope/{config.json,.env}
with commented placeholders at 0600.

Usage:
  mvsetup.py --check   # exit 0 if ready (silent), 2 if binaries missing
  mvsetup.py --json    # structured status
  mvsetup.py           # scaffold config + print status/guidance
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import sys
from pathlib import Path

try:
    import config
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import config

REQUIRED = ("ffmpeg", "ffprobe")

CONFIG_TEMPLATE = {
    "default_target": "gsap",
    "frame_budget": 32,
    "resolution": 640,
    "frame_format": "png",
    "image_provider": "openai",
    "video_provider": "runway",
}

ENV_TEMPLATE = """# motiscope secrets — API keys for OPTIONAL asset generation.
# This file must stay private (chmod 600) and out of git. Keys are only read
# locally; motiscope never uploads them. Asset generation is STUBBED in v0.1
# (no network calls), so these are not required for analysis or code recreation.
#
# Image providers (uncomment + fill the one you use):
# OPENAI_API_KEY=
# STABILITY_API_KEY=
# REPLICATE_API_TOKEN=
# FAL_KEY=
#
# Video providers:
# RUNWAY_API_KEY=
"""


def missing_binaries() -> list[str]:
    return [b for b in REQUIRED if shutil.which(b) is None]


def install_hint() -> str:
    system = platform.system()
    if system == "Darwin":
        return "brew install ffmpeg"
    if system == "Linux":
        return "sudo apt-get install -y ffmpeg   # or: sudo dnf install ffmpeg"
    if system == "Windows":
        return "winget install Gyan.FFmpeg   # or: choco install ffmpeg"
    return "install ffmpeg (includes ffprobe) via your platform's package manager"


def scaffold_config() -> dict:
    d = config.config_dir()
    d.mkdir(parents=True, exist_ok=True)
    created = []
    cfg = config.config_path()
    if not cfg.exists():
        cfg.write_text(json.dumps(CONFIG_TEMPLATE, indent=2))
        created.append(str(cfg))
    env = config.global_env_path()
    if not env.exists():
        env.write_text(ENV_TEMPLATE)
        os.chmod(env, 0o600)
        created.append(str(env))
    else:
        # tighten perms if loose
        mode = stat.S_IMODE(env.stat().st_mode)
        if mode not in (0o600, 0o400):
            os.chmod(env, 0o600)
    return {"created": created, "config_dir": str(d)}


def status() -> dict:
    missing = missing_binaries()
    return {
        "status": "ready" if not missing else "needs_install",
        "can_proceed": not missing,
        "missing_binaries": missing,
        "install_hint": install_hint() if missing else None,
        "platform": platform.system(),
        "config_file": str(config.config_path()),
        "env_file": str(config.global_env_path()),
        "env_exists": config.global_env_path().exists(),
        "providers": config.provider_status(),
    }


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return 0 if not missing_binaries() else 2
    if "--json" in argv:
        print(json.dumps(status(), indent=2))
        return 0

    # bare invocation: scaffold + human-readable status
    result = scaffold_config()
    st = status()
    if result["created"]:
        print("Scaffolded: " + ", ".join(result["created"]))
    if st["missing_binaries"]:
        print(f"MISSING: {', '.join(st['missing_binaries'])}")
        print(f"  Install with: {st['install_hint']}")
        print("  (motiscope does not auto-install — run the command above yourself.)")
        return 2
    print("motiscope is ready: ffmpeg + ffprobe found.")
    print(f"  Config: {st['config_file']}")
    print(f"  Secrets (optional, for asset gen): {st['env_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
