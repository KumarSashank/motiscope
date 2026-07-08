# Attribution

motiscope builds on techniques from two MIT-licensed open-source projects.
Both license texts are reproduced below, as MIT requires. Thank you to their
authors.

## Techniques ported / adapted

From **claude-video** (`skills/watch/scripts/frames.py`):

- The perceptual frame-dedup detector: decode frames to a small grayscale
  thumbnail in one ffmpeg pass and drop frames whose mean absolute per-pixel
  difference from the last kept frame is below a threshold. motiscope reuses
  this both as a dedup pass and, extended to the whole timeline, as its core
  per-frame **motion-energy** signal.
- Scene-change frame selection (`select='gt(scene,…)'` + `showinfo` / `pts_time`
  parsing), keyframe extraction (`-skip_frame nokey`), the width-capped scale
  filter, and the "detect all, then even-sample to a budget" pattern.
- The `SessionStart` dependency-check hook pattern and the `.env` config loader.

From **claude-video-vision** (`mcp-server/src/extractors/analyzers.ts`):

- The ffmpeg signal-analysis filter set and its stderr/metadata parsers:
  `scdet` (scene cuts), `blackdetect` (fades), `freezedetect` (holds),
  `siti` (spatial/temporal information), and `signalstats` (brightness).
- The `deriveContentProfile` spatial/temporal-information bucketing.

motiscope's contribution on top of these is motion-design-specific: a dense
per-frame motion-energy curve and motion grid (sampled at native fps, not capped
at 2 fps), easing/timing inference from the velocity profile, and translation of
the resulting animation spec into GSAP / CSS / Framer Motion / Lottie code.

---

## claude-video

<https://github.com/bradautomates/claude-video>

```
MIT License

Copyright (c) 2026 Bradley Bonanno

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## claude-video-vision

<https://github.com/jordanrendric/claude-video-vision>

```
MIT License

Copyright (c) 2026 Jordan Vasconcelos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
