#!/usr/bin/env python3
"""Config + secrets for motiscope.

Precedence for secrets: process env > project ./.motiscope/.env >
~/.config/motiscope/.env. Non-secret prefs live in
~/.config/motiscope/config.json. Keys are NEVER written to config.json,
printed, or committed. The .env parser is adapted from claude-video (MIT).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

APP = "motiscope"

# Provider registries: provider name -> env var holding its key.
IMAGE_PROVIDERS = {
    "gemini": "GEMINI_API_KEY",      # Imagen via the Gemini API (implemented)
    "imagen": "GEMINI_API_KEY",      # alias
    "openai": "OPENAI_API_KEY",
    "stability": "STABILITY_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
    "fal": "FAL_KEY",
}
VIDEO_PROVIDERS = {
    "runway": "RUNWAY_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
    "fal": "FAL_KEY",
}

DEFAULT_CONFIG = {
    "default_target": "gsap",
    "frame_budget": 32,
    "resolution": 640,
    "frame_format": "png",
    "image_provider": "gemini",
    "video_provider": "runway",
}


def config_dir() -> Path:
    return Path(os.path.expanduser("~")) / ".config" / APP


def global_env_path() -> Path:
    return config_dir() / ".env"


def project_env_path() -> Path:
    return Path(".motiscope") / ".env"


def config_path() -> Path:
    return config_dir() / "config.json"


def read_env_file(path: Path) -> dict:
    """Parse KEY=VALUE lines, stripping quotes and inline comments. Tolerant."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        # strip a trailing inline comment only when the value isn't quoted
        if val[:1] not in ("'", '"') and " #" in val:
            val = val.split(" #", 1)[0].strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        out[key] = val
    return out


def get_secret(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    for p in (project_env_path(), global_env_path()):
        val = read_env_file(p).get(name)
        if val:
            return val
    return None


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(json.loads(config_path().read_text()))
    except (OSError, ValueError):
        pass
    return cfg


def has_key(provider: str) -> bool:
    env = IMAGE_PROVIDERS.get(provider) or VIDEO_PROVIDERS.get(provider)
    return bool(env and get_secret(env))


def provider_status() -> dict:
    return {
        "image": {p: has_key(p) for p in IMAGE_PROVIDERS},
        "video": {p: has_key(p) for p in VIDEO_PROVIDERS},
    }


if __name__ == "__main__":
    print(json.dumps({"config": load_config(), "providers": provider_status(),
                      "config_file": str(config_path()), "env_file": str(global_env_path())}, indent=2))
