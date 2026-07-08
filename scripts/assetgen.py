#!/usr/bin/env python3
"""Asset-generation MECHANISM for motiscope — the network call is STUBBED.

This wires up the pluggable API-key config and the consent surface, and writes a
clearly-labeled placeholder so recreation can proceed without real generation.
Real provider calls are intentionally not implemented; a single TODO below marks
the one place to add them.

Usage:
  assetgen.py --check
  assetgen.py generate --type image|video --provider NAME --prompt "..." --out PATH
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

try:
    import config
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import config


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
    tspans = "".join(
        f'<tspan x="480" dy="{28 if i else 0}">{ln}</tspan>' for i, ln in enumerate(lines[:8]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
  <rect width="960" height="540" fill="#12141a"/>
  <rect x="12" y="12" width="936" height="516" fill="none" stroke="#3a3f52" stroke-width="2" stroke-dasharray="10 8"/>
  <text x="480" y="180" fill="#8a90a6" font-family="system-ui, sans-serif" font-size="22"
        text-anchor="middle" font-weight="600">motiscope · {kind} placeholder</text>
  <text x="480" y="214" fill="#5c627a" font-family="system-ui, sans-serif"
        font-size="15" text-anchor="middle">provider: {html.escape(provider)} · generation stubbed</text>
  <text x="480" y="280" fill="#c9cfe0" font-family="system-ui, sans-serif" font-size="18"
        text-anchor="middle">{tspans}</text>
</svg>'''


def generate(kind: str, provider: str, prompt: str, out: str) -> dict:
    registry = config.IMAGE_PROVIDERS if kind == "image" else config.VIDEO_PROVIDERS
    if provider not in registry:
        return {"ok": False, "error": f"unknown {kind} provider '{provider}'. "
                f"Known: {', '.join(registry)}"}
    if not config.has_key(provider):
        return {"ok": False, "error": f"no API key for '{provider}'. Set {registry[provider]} "
                f"in {config.global_env_path()} (run /motiscope:doctor)."}

    # TODO: real provider call here — POST the prompt to `provider`'s API using the
    # configured key and download the returned asset to `out`. Until then we write a
    # labeled placeholder so recreation is not blocked.
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder = out_path.with_suffix(".placeholder.svg")
    placeholder.write_text(_placeholder_svg(kind, provider, prompt))
    return {"ok": True, "stub": True, "provider": provider, "type": kind,
            "prompt": prompt, "placeholder": str(placeholder),
            "note": "STUB — no network call was made. Replace the placeholder with a real "
                    "asset, or implement the provider call in assetgen.py."}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--check":
        print(json.dumps(config.provider_status(), indent=2))
        return 0
    if argv[0] == "generate":
        opts = {"type": None, "provider": None, "prompt": "", "out": None}
        rest, i = argv[1:], 0
        while i < len(rest):
            a = rest[i]
            if a in ("--type", "--provider", "--prompt", "--out"):
                opts[a[2:]] = rest[i + 1]; i += 2
            else:
                i += 1
        if not all([opts["type"], opts["provider"], opts["out"]]):
            print("error: generate requires --type, --provider, --out", file=sys.stderr)
            return 2
        result = generate(opts["type"], opts["provider"], opts["prompt"], opts["out"])
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    print(f"error: unknown command {argv[0]!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
