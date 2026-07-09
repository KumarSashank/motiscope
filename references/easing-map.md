# Easing map

How to turn a measured motion-energy profile into an easing token, and how to
translate that neutral token into each target framework.

## Reading the energy curve

The per-frame **motion-energy** value (in `motion.json` → `energy.values`) is the
mean pixel change between consecutive frames — a proxy for **velocity**. Within a
single `move` segment, the *shape* of that curve is the easing:

| Energy shape across the segment | Velocity meaning | Neutral token |
|---|---|---|
| starts high, decays toward zero | fast then slowing | `ease-out` |
| starts near zero, rises          | slow then speeding up | `ease-in` |
| low → high → low (bell)          | accelerate then decelerate | `ease-in-out` |
| roughly flat                     | constant velocity | `linear` |
| main peak, dips, small rebound   | overshoot then settle | `spring` |
| near-zero plateau                | not moving | `hold` |

`analyze_motion.py` already classifies each segment (`segments[].ease`) and reports
a `dominant_easing`. Trust those for timing; use the frames only to confirm the
element's start/end transform values.

## Prefer the measured bezier

Each move segment now carries a **fitted `cubic-bezier`** (in `motion.json` →
`segments[].bezier`, and the report's `cubic-bezier` column) — the running integral of
the speed curve matched to a real easing curve. **Use it directly** when the target
supports arbitrary cubic-beziers:

- **CSS / Web Animations:** `animation-timing-function: cubic-bezier(x1,y1,x2,y2)` — use the exact values.
- **GSAP:** `CustomEase.create("m", "M0,0 C…")` from the bezier, or the mapped token below.
- **Framer:** `ease: [x1, y1, x2, y2]` (Framer accepts a bezier array).
- **Lottie:** derive the keyframe `i`/`o` handles from the control points.

Fall back to the neutral-token → named-ease table below when the target needs a named
ease, or for `spring` (which a single bezier can't represent — use the target's spring).

*(The bezier is a **timing** measurement. The animation's **direction** and type — up/down,
scale, morph, draw, etc. — you read from the frames, not from the numbers.)*

## Neutral token → target value

| Neutral | GSAP `ease` | CSS `cubic-bezier` | Framer Motion | Lottie (bezier out/in) |
|---|---|---|---|---|
| `ease-out`    | `power2.out`   | `cubic-bezier(0.16, 1, 0.3, 1)`    | `ease: "easeOut"` | out `[0.3,1]`, in `[0.16,0]` |
| `ease-in`     | `power2.in`    | `cubic-bezier(0.5, 0, 0.75, 0)`    | `ease: "easeIn"`  | out `[0.75,1]`, in `[0.5,0]` |
| `ease-in-out` | `power2.inOut` | `cubic-bezier(0.65, 0, 0.35, 1)`   | `ease: "easeInOut"` | symmetric |
| `linear`      | `none`         | `linear`                            | `ease: "linear"`  | linear |
| `spring`      | `back.out(1.7)` or `elastic.out(1, 0.4)` | approximate: `cubic-bezier(0.34, 1.56, 0.64, 1)` | `type: "spring", stiffness, damping` | bake keyframes (no native spring) |
| `hold`        | timeline gap / `delay` | `animation-delay` or a flat keyframe range | `delay` | repeated (still) keyframes |

## Looping

If the analysis reports a loop (`motion.loop.is_loop`), the animation repeats with a
detected `period_ms`. Because the energy signal is speed-based, that period can be a
**half-cycle** for back-and-forth motion — decide from the frames:

- **Same-direction repeat** (returns to start, plays again): loop the full timeline.
  GSAP `repeat: -1`; CSS `animation-iteration-count: infinite`; Framer
  `transition: { repeat: Infinity }`; Lottie `loop: true`.
- **Out-and-back (yoyo/ping-pong)**: animate one half at `period_ms`, then reverse.
  GSAP `{ repeat: -1, yoyo: true }`; CSS `animation-direction: alternate` (with
  `iteration-count: infinite`); Framer `{ repeat: Infinity, repeatType: "reverse" }`.

Set the spec's `loop` accordingly, and use `period_ms` as the (half-)cycle duration.

### Notes
- Strength/overshoot amount is **estimated** — `back.out(1.7)` and the springy
  bezier are reasonable defaults; tell the user to tune the overshoot.
- `power2` is a sensible middle; a very sharp decay reads better as `power3`/`power4`,
  a very gentle one as `power1` / `sine`. Pick from how steep the energy curve is.
- A `spring` from frames alone cannot recover true physics — offer both a spring and
  a baked-bezier version and let the user choose.
- Durations, delays (from `hold` segments), and stagger `each_ms` come straight from
  the measured timeline in milliseconds.
