#!/usr/bin/env bash
# SessionStart hook for motiscope. One actionable line when something needs
# attention; silent when ready (to avoid per-session spam). Adapted from
# claude-video's check-setup.sh (MIT).
set -euo pipefail

CONFIG_FILE="$HOME/.config/motiscope/.env"

# Warn if the secrets file has loose permissions.
if [[ -f "$CONFIG_FILE" ]]; then
  perms=$(stat -c '%a' "$CONFIG_FILE" 2>/dev/null || stat -f '%Lp' "$CONFIG_FILE" 2>/dev/null || echo "")
  if [[ -n "$perms" && "$perms" != "600" && "$perms" != "400" ]]; then
    echo "motiscope: WARNING — $CONFIG_FILE has permissions $perms (should be 600). Fix: chmod 600 $CONFIG_FILE"
  fi
fi

HAS_FFMPEG=""; HAS_FFPROBE=""
command -v ffmpeg  >/dev/null 2>&1 && HAS_FFMPEG="yes"
command -v ffprobe >/dev/null 2>&1 && HAS_FFPROBE="yes"

if [[ -z "$HAS_FFMPEG" || -z "$HAS_FFPROBE" ]]; then
  echo "motiscope: needs ffmpeg + ffprobe. Run /motiscope:doctor (installs on macOS via 'brew install ffmpeg')."
  exit 0
fi

# Count droppable videos in the conventional folder.
if [[ -d "animations" ]]; then
  count=$(find animations -maxdepth 1 -type f \
      \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.webm' -o -iname '*.mkv' \
         -o -iname '*.m4v' -o -iname '*.avi' \) 2>/dev/null | wc -l | tr -d ' ')
  if [[ "${count:-0}" -gt 0 ]]; then
    echo "motiscope: found $count video(s) in animations/ — run /motiscope:analyze to recreate one."
    exit 0
  fi
fi

# Ready and nothing waiting → stay silent.
exit 0
