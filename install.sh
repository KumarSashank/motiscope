#!/usr/bin/env sh
# motiscope installer — puts the `motiscope` command on your PATH.
#
#   git clone https://github.com/KumarSashank/motiscope.git ~/.motiscope
#   ~/.motiscope/install.sh
#
# No sudo, no package manager, no network. It creates one symlink.
# Claude Code users don't need this — install motiscope as a plugin instead.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR=${MOTISCOPE_BIN_DIR:-$HOME/.local/bin}

[ -f "$ROOT/scripts/cli.py" ] || { echo "error: run this from a motiscope checkout" >&2; exit 1; }

command -v python3 >/dev/null 2>&1 || { echo "error: python3 is required" >&2; exit 1; }

mkdir -p "$BIN_DIR"
chmod +x "$ROOT/bin/motiscope"
ln -sf "$ROOT/bin/motiscope" "$BIN_DIR/motiscope"
echo "linked $BIN_DIR/motiscope -> $ROOT/bin/motiscope"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo
    echo "$BIN_DIR is not on your PATH. Add it:"
    echo "  echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc   # or ~/.bashrc"
    ;;
esac

echo
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  echo "ffmpeg + ffprobe found."
else
  echo "Missing ffmpeg/ffprobe — motiscope needs both. Install, then run 'motiscope doctor'."
fi

echo
echo "Next, teach your agent the commands:"
echo "  motiscope install codex     # ~/.codex/prompts/"
echo "  motiscope install cursor    # ./.cursor/commands/ + rules"
echo "  motiscope install agents    # ./AGENTS.md block"
