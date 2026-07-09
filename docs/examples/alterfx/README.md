# Alterfx — design-to-code recreation

A **live recreation** of an "Alterfx / AI videography coach" landing-page **concept
from Dribbble**, rebuilt from a 10-second screen recording with
[motiscope](https://kumarsashank.github.io/motiscope/).

- **Live recreation:** [`index.html`](./index.html) → <https://kumarsashank.github.io/motiscope/examples/alterfx/>
- **Source:** a screen recording of the Dribbble shot (`source.gif` shows the first 5s).
- **Original concept:** _Dribbble — link to be added; all credit to the original designer._

> This is a **design-to-code study**, not a product. It is **not affiliated with**
> the original designer or any company named "Alterfx." All credit for the visual
> design goes to the original Dribbble author; motiscope + the code here only
> recreate it from a recording.

## The workflow (what motiscope did)

1. `/motiscope:analyze landing_check_1.mp4 --end 10 --preset detailed` → measured:
   - 5 segments across the first 10s: hold → fade-out → hold → fade-out → hold
   - a hard cut at 1.55s (the zoom-into-phone transition)
   - a **top-to-bottom stagger, ~456ms** between elements
   - fade transitions at ~6.6s and ~9.2s (the sparkle-logo wipe)
2. Read the curated frames to recover layout, copy, and the dark-teal design system.
3. `/motiscope:recreate` → GSAP + ScrollTrigger, timing anchored to those beats.

## Measured vs. recreated (honest diff)

- ✅ **Measured (from motiscope):** the sequence, section timing, the stagger, the
  fade/transition beats, the dark-teal aesthetic.
- ✏️ **Recreated / crafted:** exact easing and scroll choreography (scroll-scrubbed
  zoom), the phone camera-UI (rebuilt in CSS/SVG), and the copy.
- 🖼️ **Generated:** the photographic shots (hands+phone hero, cinematic scenes,
  feature photos) were generated with **Imagen 4** — the original used stock/photo
  assets that aren't ours to redistribute.
- 🔤 Display font: **Martian Mono** (OFL).
