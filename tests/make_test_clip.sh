#!/usr/bin/env bash
# Synthesize ground-truth animation clips with ffmpeg lavfi so the pipeline can be
# tested without any real screen recording. Each clip has a KNOWN motion profile.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 1) test-ease.mp4 — box translates left->right, x ∝ (t/2)^2  => velocity rises => EASE-IN.
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=white:s=800x600:r=60:d=2 \
  -f lavfi -i color=c=0x3366ff:s=120x120:r=60:d=2 \
  -filter_complex "[1]format=rgba[fg];[0][fg]overlay=x='(W-w)*(t/2)*(t/2)':y='(H-h)/2':eval=frame" \
  -frames:v 120 -c:v libx264 -pix_fmt yuv420p -y test-ease.mp4

# 2) test-linear.mp4 — box translates at constant velocity => LINEAR.
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=white:s=800x600:r=60:d=2 \
  -f lavfi -i color=c=0xff5533:s=120x120:r=60:d=2 \
  -filter_complex "[1]format=rgba[fg];[0][fg]overlay=x='(W-w)*(t/2)':y='(H-h)/2':eval=frame" \
  -frames:v 120 -c:v libx264 -pix_fmt yuv420p -y test-linear.mp4

# 3) test-hold.mp4 — box moves during 0-1s (linear) then holds still 1-2s => MOVE + HOLD.
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=white:s=800x600:r=60:d=2 \
  -f lavfi -i color=c=0x22aa66:s=120x120:r=60:d=2 \
  -filter_complex "[1]format=rgba[fg];[0][fg]overlay=x='(W-w)*min(t\,1)':y='(H-h)/2':eval=frame" \
  -frames:v 120 -c:v libx264 -pix_fmt yuv420p -y test-hold.mp4

# 4) test-fade.mp4 — full-frame fade-in from black over 0.5s then static => FADE-IN + HOLD.
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=0x3366ff:s=800x600:r=60:d=2 \
  -vf "fade=t=in:st=0:d=0.5" \
  -frames:v 120 -c:v libx264 -pix_fmt yuv420p -y test-fade.mp4

# 5) test-10s.mp4 — 10s, 1280x720: fade-in, then an ease-in translate during 1-3s,
#    then a long hold. Exercises focus-window + preset behavior on a longer clip.
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=white:s=1280x720:r=60:d=10 \
  -f lavfi -i color=c=0x3366ff:s=160x160:r=60:d=10 \
  -filter_complex "[1]format=rgba,fade=t=in:st=0:d=0.5:alpha=1[fg];[0][fg]overlay=x='200+900*(clip(t-1\,0\,2)/2)*(clip(t-1\,0\,2)/2)':y='(H-h)/2':eval=frame" \
  -frames:v 600 -c:v libx264 -pix_fmt yuv420p -y test-10s.mp4

# 6) test-loop.mp4 — box oscillates horizontally, visual period 1s over 4s (4 cycles).
#    A continuous back-and-forth => a real LOOP (energy period is the 0.5s half-cycle).
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i color=c=white:s=1280x720:r=60:d=4 \
  -f lavfi -i color=c=0x3366ff:s=160x160:r=60:d=4 \
  -filter_complex "[0][1]overlay=x='560+400*sin(2*PI*t)':y='(H-h)/2':eval=frame" \
  -frames:v 240 -c:v libx264 -pix_fmt yuv420p -y test-loop.mp4

echo "Wrote: test-ease/linear/hold/fade/10s/loop .mp4 (in $DIR)"
