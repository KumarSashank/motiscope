#!/usr/bin/env python3
"""Asset generation for motiscope.

Real image generation is implemented for the **gemini / imagen** provider (Imagen
via the Gemini API); other providers still write a labeled placeholder until wired.
Keys come from the pluggable config (never printed/committed).

Usage:
  assetgen.py --check
  assetgen.py generate --type image --provider gemini --prompt "..." --out PATH [--aspect-ratio 16:9]
"""
from __future__ import annotations

import base64
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import config
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import config

# Imagen accepts only these aspect ratios; anything else is a 400.
VALID_ASPECT = {"1:1", "3:4", "4:3", "9:16", "16:9"}
DEFAULT_IMAGE_MODEL = "imagen-4.0-generate-001"


def _placeholder_svg(kind: str, provider: str, prompt: str) -> str:
    safe = html.escape(prompt)
    words, lines, cur = safe.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 46:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    tspans = "".join(f'<tspan x="480" dy="{28 if i else 0}">{ln}</tspan>' for i, ln in enumerate(lines[:8]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
  <rect width="960" height="540" fill="#12141a"/>
  <rect x="12" y="12" width="936" height="516" fill="none" stroke="#3a3f52" stroke-width="2" stroke-dasharray="10 8"/>
  <text x="480" y="180" fill="#8a90a6" font-family="system-ui, sans-serif" font-size="22"
        text-anchor="middle" font-weight="600">motiscope · {kind} placeholder</text>
  <text x="480" y="214" fill="#5c627a" font-family="system-ui, sans-serif"
        font-size="15" text-anchor="middle">provider: {html.escape(provider)} · not yet implemented</text>
  <text x="480" y="280" fill="#c9cfe0" font-family="system-ui, sans-serif" font-size="18"
        text-anchor="middle">{tspans}</text>
</svg>'''


def _gemini_imagen(prompt: str, out_path: Path, key: str, aspect_ratio: str, model: str) -> str:
    """Generate one image with Imagen (Gemini API :predict) and write it to out_path.
    Returns the mime type. Raises on API/HTTP error."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={key}"
    body = json.dumps({"instances": [{"prompt": prompt}],
                       "parameters": {"sampleCount": 1, "aspectRatio": aspect_ratio}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    preds = data.get("predictions", [])
    if not preds or "bytesBase64Encoded" not in preds[0]:
        raise RuntimeError("no image in Imagen response")
    out_path.write_bytes(base64.b64decode(preds[0]["bytesBase64Encoded"]))
    return preds[0].get("mimeType", "image/png")


def generate(kind: str, provider: str, prompt: str, out: str, aspect_ratio: str = "1:1") -> dict:
    registry = config.IMAGE_PROVIDERS if kind == "image" else config.VIDEO_PROVIDERS
    if provider not in registry:
        return {"ok": False, "error": f"unknown {kind} provider '{provider}'. Known: {', '.join(registry)}"}
    key = config.get_secret(registry[provider])
    if not key:
        return {"ok": False, "error": f"no API key for '{provider}'. Set {registry[provider]} in "
                f"{config.global_env_path()} (run /motiscope:doctor)."}

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Implemented: image generation via Gemini/Imagen.
    if kind == "image" and provider in ("gemini", "imagen"):
        if aspect_ratio not in VALID_ASPECT:
            return {"ok": False, "error": f"aspect_ratio '{aspect_ratio}' invalid — "
                    f"Imagen accepts {sorted(VALID_ASPECT)}."}
        model = os.environ.get("MOTISCOPE_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)
        try:
            mime = _gemini_imagen(prompt, out_path, key, aspect_ratio, model)
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": f"Imagen HTTP {e.code}: {e.read().decode()[:200]}"}
        except Exception as e:  # noqa: BLE001 - surface any failure to the caller
            return {"ok": False, "error": f"generation failed: {e}"}
        return {"ok": True, "provider": provider, "type": kind, "prompt": prompt,
                "out": str(out_path), "model": model, "mime": mime, "aspect_ratio": aspect_ratio}

    # Not yet implemented (video, other image providers) -> labeled placeholder.
    placeholder = out_path.with_suffix(".placeholder.svg")
    placeholder.write_text(_placeholder_svg(kind, provider, prompt))
    return {"ok": True, "stub": True, "provider": provider, "type": kind, "prompt": prompt,
            "placeholder": str(placeholder),
            "note": f"'{provider}' {kind} generation is not implemented yet — wrote a placeholder. "
                    "Implemented today: gemini/imagen (image)."}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--check":
        print(json.dumps(config.provider_status(), indent=2))
        return 0
    if argv[0] == "generate":
        opts = {"type": None, "provider": None, "prompt": "", "out": None, "aspect-ratio": "1:1"}
        rest, i = argv[1:], 0
        while i < len(rest):
            a = rest[i]
            if a in ("--type", "--provider", "--prompt", "--out", "--aspect-ratio"):
                opts[a[2:]] = rest[i + 1]; i += 2
            else:
                i += 1
        if not all([opts["type"], opts["provider"], opts["out"]]):
            print("error: generate requires --type, --provider, --out", file=sys.stderr)
            return 2
        result = generate(opts["type"], opts["provider"], opts["prompt"], opts["out"], opts["aspect-ratio"])
        # never echo the key; result contains none
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    print(f"error: unknown command {argv[0]!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
