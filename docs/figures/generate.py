#!/usr/bin/env python3
"""Draw the how-it-works figures from real pipeline output. Stdlib only.

    python3 docs/figures/generate.py

Every number plotted here came out of scripts/analyze_motion.py on a real clip, and is
checked in as curves.json so the figures are reproducible without re-running ffmpeg:
  energy-curve.svg  -> the ambient loop's localized motion-energy curve
  easing-fit.svg    -> tests/test-ease.mp4 (position proportional to t^2):
                       measured integral vs fitted bezier vs ground truth
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE
D = json.loads((HERE / "curves.json").read_text())

IND, FUC, CYA, GOOD = "#818cf8", "#e879f9", "#22d3ee", "#34d399"

HEAD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"
     role="img" aria-label="{alt}">
  <title>{alt}</title>
  <style>
    /* Embedded via an img element, so this SVG follows the OS colour scheme rather
       than the page theme toggle. Every colour must read on light and dark. */
    .ink   {{ fill:#8b90a3; font:11px ui-monospace,SFMono-Regular,Menlo,monospace }}
    .ink-b {{ fill:#a2a8bd; font:12px ui-monospace,SFMono-Regular,Menlo,monospace }}
    .ax    {{ stroke:rgba(129,140,248,.28); stroke-width:1 }}
    /* no stroke-width here: a CSS declaration would override the per-polyline
       stroke-width presentation attribute, flattening every curve to one weight. */
    .trace {{ fill:none; stroke-linejoin:round; stroke-linecap:round }}
    /* The trace is drawn solid by default. The draw-on is a pure enhancement: if the
       animation never runs, the figure must still show the curve, not an empty grid. */
    @media (prefers-reduced-motion:no-preference) {{
      .draw {{ stroke-dasharray:var(--len); stroke-dashoffset:var(--len);
               animation:draw 2.6s cubic-bezier(.4,0,.2,1) .2s forwards }}
    }}
    @keyframes draw {{ to {{ stroke-dashoffset:0 }} }}
  </style>
'''


def poly(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


# ---------------------------------------------------------------- energy curve
def energy_curve():
    a = D["ambient"]
    vals, dt = a["values"], a["dt"]
    W, H = 880, 300
    L, R, T, B = 52, 18, 26, 34
    pw, ph = W - L - R, H - T - B
    peak = max(vals)
    dur = len(vals) * dt
    thr = max(0.05, 0.18 * a["motion_ref"])

    def X(i): return L + pw * (i / (len(vals) - 1))
    def Y(v): return T + ph * (1 - v / (peak * 1.06))

    pts = [(X(i), Y(v)) for i, v in enumerate(vals)]
    ythr = Y(thr)
    # crude path length so the draw-on animation has a real dash length
    ln = sum(((pts[i][0]-pts[i-1][0])**2 + (pts[i][1]-pts[i-1][1])**2) ** .5
             for i in range(1, len(pts)))

    peak_i = max(range(len(vals)), key=lambda i: vals[i])
    s = HEAD.format(w=W, h=H, alt="Motion-energy curve of the ambient loop, with the hold threshold")
    s += f'  <rect x="{L}" y="{T}" width="{pw}" height="{ythr-T:.1f}" fill="{IND}" opacity=".04"/>\n'
    s += f'  <rect x="{L}" y="{ythr:.1f}" width="{pw}" height="{T+ph-ythr:.1f}" fill="{FUC}" opacity=".05"/>\n'
    s += f'  <line class="ax" x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}"/>\n'
    s += f'  <line class="ax" x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}"/>\n'
    s += (f'  <line x1="{L}" y1="{ythr:.1f}" x2="{L+pw}" y2="{ythr:.1f}" stroke="{FUC}"'
          f' stroke-width="1.5" stroke-dasharray="5 4" opacity=".85"/>\n')
    s += f'  <text class="ink" x="{L+6}" y="{ythr-7:.1f}" fill="{FUC}">hold threshold {thr:.2f}</text>\n'
    s += (f'  <polyline class="trace draw" style="--len:{ln:.0f}" points="{poly(pts)}"'
          f' stroke="{IND}" stroke-width="2"/>\n')
    s += f'  <circle cx="{X(peak_i):.1f}" cy="{Y(peak):.1f}" r="3.5" fill="{CYA}"/>\n'
    s += (f'  <text class="ink-b" x="{X(peak_i)+9:.1f}" y="{Y(peak)-8:.1f}">'
          f'peak {peak:.1f} @ {peak_i*dt:.2f}s</text>\n')
    s += f'  <text class="ink" x="{L-8}" y="{T+5}" text-anchor="end">{peak:.0f}</text>\n'
    s += f'  <text class="ink" x="{L-8}" y="{T+ph+4}" text-anchor="end">0</text>\n'
    s += f'  <text class="ink" x="{L}" y="{H-12}">0s</text>\n'
    s += f'  <text class="ink" x="{L+pw}" y="{H-12}" text-anchor="end">{dur:.2f}s</text>\n'
    s += f'  <text class="ink" x="{L+pw/2}" y="{H-12}" text-anchor="middle">{len(vals)} samples @ {1/dt:.0f}fps &#183; zero image tokens</text>\n'
    s += f'  <text class="ink" x="6" y="{T+ph/2}" transform="rotate(-90 6 {T+ph/2})" text-anchor="middle">energy</text>\n'
    return s + "</svg>\n"


# ---------------------------------------------------------------- easing fit
def bez(x1, y1, x2, y2, m=240):
    out = []
    for i in range(m + 1):
        t = i / m; u = 1 - t
        out.append((3*u*u*t*x1 + 3*u*t*t*x2 + t**3,
                    3*u*u*t*y1 + 3*u*t*t*y2 + t**3))
    return out


def y_at_x(curve, x):
    for i in range(1, len(curve)):
        if curve[i][0] >= x:
            x0, y0 = curve[i-1]; x1, y1 = curve[i]
            if x1 == x0: return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return curve[-1][1]


def easing_fit():
    e = D["ease"]
    vals, dt = e["values"], e["dt"]
    i0, i1 = int(e["start_ms"]/1000/dt), min(int(e["end_ms"]/1000/dt), len(vals))
    seg = vals[i0:i1] or vals
    # energy is speed; its running integral, normalised, is displacement vs time
    cum, run = [], 0.0
    for v in seg:
        run += v; cum.append(run)
    disp = [c / cum[-1] for c in cum]
    xs = [i / (len(disp) - 1) for i in range(len(disp))]

    W, H = 520, 380
    L, R, T, B = 52, 18, 22, 84
    pw, ph = W - L - R, H - T - B
    def X(x): return L + pw * x
    def Y(y): return T + ph * (1 - y)

    fit = bez(*e["bezier"])
    fitpts = [(X(i/120), Y(y_at_x(fit, i/120))) for i in range(121)]
    truth  = [(X(i/120), Y((i/120) ** 2)) for i in range(121)]
    meas   = [(X(x), Y(y)) for x, y in zip(xs, disp)]
    rmse = (sum((y_at_x(fit, x) - y) ** 2 for x, y in zip(xs, disp)) / len(xs)) ** .5

    s = HEAD.format(w=W, h=H, alt="Measured displacement vs the fitted cubic-bezier vs the ground truth")
    for g in range(1, 4):
        s += f'  <line class="ax" x1="{L}" y1="{T+ph*g/4:.1f}" x2="{L+pw}" y2="{T+ph*g/4:.1f}"/>\n'
    s += f'  <line class="ax" x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}"/>\n'
    s += f'  <line class="ax" x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}"/>\n'
    # ground truth sits underneath and widest: the measured curve should lie right on it
    s += (f'  <polyline class="trace" points="{poly(truth)}" stroke="{GOOD}"'
          f' stroke-width="9" opacity=".85"/>\n')
    s += f'  <polyline class="trace" points="{poly(meas)}" stroke="{CYA}" stroke-width="2"/>\n'
    s += (f'  <polyline class="trace" points="{poly(fitpts)}" stroke="{FUC}"'
          f' stroke-width="2" stroke-dasharray="6 4"/>\n')
    b = e["bezier"]
    bz = f"cubic-bezier({b[0]:g},{b[1]:g},{b[2]:g},{b[3]:g})"
    rows = [(GOOD, "ground truth", "x&#178; \u2014 how the clip was authored"),
            (CYA,  "measured", "running integral of the energy curve"),
            (FUC,  "fitted", f"{bz} \u00b7 rmse {rmse:.3f}")]
    for i, (col, lab, desc) in enumerate(rows):
        y = H - 56 + i * 17
        s += f'  <rect x="{L}" y="{y-7}" width="16" height="3" rx="1.5" fill="{col}"/>\n'
        s += f'  <text class="ink" x="{L+24}" y="{y}" fill="{col}">{lab}</text>\n'
        s += f'  <text class="ink" x="{L+118}" y="{y}">{desc}</text>\n'
    s += f'  <text class="ink" x="{L-8}" y="{T+5}" text-anchor="end">1</text>\n'
    s += f'  <text class="ink" x="{L-8}" y="{T+ph+4}" text-anchor="end">0</text>\n'
    s += f'  <text class="ink" x="{L+pw/2}" y="{T+ph+18}" text-anchor="middle">time &#8594;</text>\n'
    s += f'  <text class="ink" x="8" y="{T+ph/2}" transform="rotate(-90 8 {T+ph/2})" text-anchor="middle">displacement</text>\n'
    return s + "</svg>\n", rmse


(OUT / "energy-curve.svg").write_text(energy_curve())
svg, rmse = easing_fit()
(OUT / "easing-fit.svg").write_text(svg)
print(f"wrote {OUT}/energy-curve.svg")
print(f"wrote {OUT}/easing-fit.svg   (fit rmse {rmse:.4f})")
