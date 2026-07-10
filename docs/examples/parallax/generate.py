#!/usr/bin/env python3
"""Generate the parallax recreation — traced terrain, measured layer speeds, a moving train.

    python3 docs/examples/parallax/generate.py > docs/examples/parallax/recreation.html

MEASURED from parallax.mov (1400x804, 60fps, 2.25s):

  Layer speeds, by mask alignment over the window where every layer is on screen,
  run at two independent scales:
      orange hills   0.72x  (0.72 / 0.72)
      crimson hills  0.86x  (0.85 / 0.87)
      purple hills   0.97x  (0.97 / 1.00)
      foreground     1.00x  (reference)
      sky / far      NOT RECOVERABLE (-0.03 .. 0.63 across methods; a smooth
                     gradient has no stable colour mask)

  Bridge: tracked directly -- the deck is the sharpest rigid feature in the clip.
      0.80x +/- 0.04 against the two foreground tree apexes, consistent within noise
      with the crimson hill it sits in, so it rides that layer.

  Train: tail tracked across frames 96..124 (the nose is hidden behind a foreground tree
      for the whole clip and would report 16 px/s). 1501 px/s, left -> right, length ~708px,
      height ~58px, riding the deck at y=498. Per-4-frame estimates scatter 1080..1800 px/s
      with no trend, so constant speed is within noise and no easing is claimed.
      In the source the train is TIME-driven. Here it is bound to the SCROLL: during the
      recording it covered 1501/419 = 3.58 units for every pixel the page scrolled, and that
      ratio is what drives it now. Scroll down, it runs left->right; scroll up, it reverses.

  Terrain: the four hill ridgelines are TRACED from the final frame, one y per column
      (see ridges.json). Occluders -- trees, bushes -- always sit above the terrain and
      pull a first-occurrence ridge upward, so the terrain is the upper quantile of the
      raw trace, not its median.

CHOSEN, not measured: the sky and the far hills share one factor (0.30), inside the
unrecoverable range -- they are a single pale mask and were never separable. The sky itself is
not a layer at all: it is the hero's CSS background. A featureless gradient has no measurable
parallax, and -- the part that actually bit us -- a sky drawn as a <rect> inside a sinking layer
has a TOP EDGE that eventually slides into frame. A backdrop with no edge cannot be uncovered.
COMPOSITION, not measured: the traced land fills 93% of the canvas (so does the source's), which
leaves no room for a sky at any viewport. cy() compresses the land toward the horizon by 0.78.
It is affine, so ridge shapes and layer factors survive untouched. Binding the train to scroll is a deliberate departure from the source
(there it runs on a clock); the 3.58 ratio is measured, the binding is a design decision.
The ground line is derived from the purple ridge -- in the source it is almost entirely
hidden behind foreground trees. Palette: a warm sunset became a cool dawn.
"""
import json, math, pathlib, sys

W, H = 1400, 804
R = json.load(open(pathlib.Path(__file__).resolve().parent / "ridges.json"))

# --- palette: cool alpine dawn (the source was a warm sunset) -------------------
SKY_TOP, SKY_MID, SKY_LOW = "#EAF7F1", "#A7DFD4", "#4FB0AF"
SUN = "#FFE3AC"
GOLD_A, GOLD_B = "#CFEBE0", "#A9DCD2"
ORNG_A, ORNG_B = "#7FCCC2", "#5CB6AF"
CRIM_A, CRIM_B = "#38869A", "#2A6E85"
NAVY_A, NAVY_B = "#1E5570", "#173E56"
INK = "#08192A"
RAIL = "#F2603C"
ACC1, ACC2 = "#FFB347", "#F2603C"
TRAIN_ROOF, TRAIN_WIN, TRAIN_BODY = "#FFFFFF", "#12253A", "#FBE3B8"

# The sky and the far hills are the same pale mask -- the measurement could never separate
# them (estimates -0.03..0.63). Pinning the sky at 0.00 while the far hills climbed at 0.30
# meant the hills ate the sky band and left a hard edge. They are one backdrop plane.
F_SKY, F_GOLD, F_ORNG, F_CRIM, F_NAVY, F_INK = 0.30, 0.30, 0.72, 0.86, 0.97, 1.00

# --- composition ------------------------------------------------------------------
# The traced terrain fills 93% of the canvas. That is faithful: the source's own rest
# frame has ~7% literal sky, and its upper hills only READ as sky because they are
# pale-yellow on pale-yellow. A bottom-anchored, width-scaled artwork shows exactly
# `heroH * 1400/heroW` canvas rows, so with a 745-row terrain there is nowhere for a
# sky to go -- no amount of canvas padding creates one. The land has to shrink.
#
# cy() is affine, so the ridge SHAPES and the measured layer FACTORS are untouched;
# only the vertical composition moves. This is a design decision, not a measurement.
LAND_K = 0.78               # terrain height x this, about the canvas bottom
PROP_K = 0.82               # trees/bushes/tulips shrink with the vista, keeping aspect
SUN_CY = 168                # the sun now has sky to sit in


LAND_ROWS = H - (H - min(R["gold"])) * LAND_K   # 581: the terrain's own height, in canvas rows
LAND_ROWS = H - LAND_ROWS                       # rows the land occupies, measured from the bottom


def cy(y):
    """Map a traced y onto the recomposed canvas: y' = H - (H - y) * LAND_K."""
    return H - (H - y) * LAND_K

DECK_Y, DECK_T = 498, 36
PIER_PITCH, ARCH_W = 194, 180
BRIDGE_X0, BRIDGE_X1 = 116, 1300
TRAIN_LEN, TRAIN_H = 708, 58
TRAIN_PXS = 1500.0          # measured: 1501 px/s (tail, frames 96..124)
SCROLL_PXS = 419.0          # measured: the recorder's scroll speed (both tree apexes)
TRAIN_PER_SCROLL = round(TRAIN_PXS / SCROLL_PXS, 2)   # 3.58 units of train per px of scroll
TRAIN_X0 = -60              # resting offset, so the train sits on the bridge at scrollY=0


def ridge_path(name, step=8):
    ys = R[name]
    pts = [(x, cy(ys[x])) for x in range(0, len(ys), step)]
    if pts[-1][0] != len(ys) - 1:
        pts.append((len(ys) - 1, cy(ys[-1])))
    d = f"M0,{H} L0,{pts[0][1]:.1f} " + " ".join(f"L{x},{y:.1f}" for x, y in pts[1:])
    return d + f" L{W},{pts[-1][1]:.1f} L{W},{H} Z"


def grad(gid, a, b):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')


def hill(name, gid, factor, a, b, extra=""):
    return (f'<svg class="ly" style="--f:{factor}" viewBox="0 0 {W} {H}" '
            f'preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
            f'<defs>{grad(gid, a, b)}</defs>'
            f'<path d="{ridge_path(name)}" fill="url(#{gid})"/>{extra}</svg>')


DECK_C = cy(DECK_Y)              # the deck, reseated on the recomposed terrain
DECK_TC = DECK_T * LAND_K        # deck slab and arch rise compress with the land
RAIL_TC = 7 * LAND_K


def bridge():
    base = DECK_C + 165 * LAND_K
    parts = [f'<rect x="{BRIDGE_X0}" y="{DECK_C:.1f}" width="{BRIDGE_X1-BRIDGE_X0}" '
             f'height="{base-DECK_C:.1f}" fill="{INK}"/>']
    x = BRIDGE_X0 + 14
    while x + ARCH_W <= BRIDGE_X1 - 14:
        r = ARCH_W / 2
        top = DECK_C + DECK_TC + 30 * LAND_K
        parts.append(f'<path d="M{x},{base:.1f} L{x},{top:.1f} A{r},{r} 0 0 1 {x+ARCH_W},{top:.1f} '
                     f'L{x+ARCH_W},{base:.1f} Z" fill="url(#gcrim)"/>')
        x += PIER_PITCH
    parts.append(f'<rect x="{BRIDGE_X0-16}" y="{DECK_C:.1f}" width="{BRIDGE_X1-BRIDGE_X0+32}" '
                 f'height="{DECK_TC:.1f}" fill="{INK}"/>')
    parts.append(f'<rect x="{BRIDGE_X0-16}" y="{DECK_C-RAIL_TC:.1f}" width="{BRIDGE_X1-BRIDGE_X0+32}" '
                 f'height="{RAIL_TC:.1f}" fill="{RAIL}"/>')
    return "".join(parts)


def car(x, w, nose=False):
    """A rounded car: white shell, navy window band with gold dividers, cream lower body."""
    t = DECK_C - TRAIN_H - RAIL_TC
    b = DECK_C - RAIL_TC
    r = 16
    if nose:
        # travelling left -> right, so the swept nose is the leading (right) end
        d = (f"M{x+r},{t} L{x+w-42},{t} L{x+w},{t+32} L{x+w},{b-r} "
             f"A{r},{r} 0 0 1 {x+w-r},{b} L{x+r},{b} A{r},{r} 0 0 1 {x},{b-r} "
             f"L{x},{t+r} A{r},{r} 0 0 1 {x+r},{t} Z")
    else:
        d = (f"M{x+r},{t} L{x+w-r},{t} A{r},{r} 0 0 1 {x+w},{t+r} L{x+w},{b-r} "
             f"A{r},{r} 0 0 1 {x+w-r},{b} L{x+r},{b} A{r},{r} 0 0 1 {x},{b-r} "
             f"L{x},{t+r} A{r},{r} 0 0 1 {x+r},{t} Z")
    out = [f'<clipPath id="c{x}"><path d="{d}"/></clipPath>',
           f'<path d="{d}" fill="{TRAIN_ROOF}"/>',
           f'<g clip-path="url(#c{x})">',
           f'<rect x="{x}" y="{t+13}" width="{w}" height="19" fill="{TRAIN_WIN}"/>',
           f'<rect x="{x}" y="{t+32}" width="{w}" height="{b-t-32}" fill="{TRAIN_BODY}"/>']
    for wx in range(x + 52, x + w - 22, 62):
        out.append(f'<rect x="{wx}" y="{t+13}" width="4" height="19" fill="{ACC1}" opacity=".8"/>')
    out.append("</g>")
    return "".join(out)


def train():
    return f'<g class="train" aria-hidden="true">{car(0,215)}{car(224,215)}{car(448,260,nose=True)}</g>'


def leaf_tree(x, y, h, col=INK):
    w = h * 0.5
    return (f'<rect x="{x-3}" y="{y-h*0.44}" width="6" height="{h*0.44}" fill="{col}"/>'
            f'<path d="M{x},{y-h} C{x+w/2},{y-h*0.74} {x+w/2},{y-h*0.36} {x},{y-h*0.30} '
            f'C{x-w/2},{y-h*0.36} {x-w/2},{y-h*0.74} {x},{y-h} Z" fill="{col}"/>'
            f'<path d="M{x},{y-h*0.96} L{x},{y-h*0.32}" stroke="#16304a" stroke-width="2.5"/>')


def fir(x, y, h, col=INK):
    w = h * 0.4
    return (f'<path d="M{x},{y-h} L{x+w/2},{y} L{x-w/2},{y} Z" fill="{col}"/>'
            f'<rect x="{x-2}" y="{y-3}" width="4" height="{h*0.1}" fill="{col}"/>')


def bush(x, y, r, col=INK):
    return (f'<circle cx="{x-r*0.7}" cy="{y}" r="{r*0.7}" fill="{col}"/>'
            f'<circle cx="{x+r*0.7}" cy="{y}" r="{r*0.64}" fill="{col}"/>'
            f'<circle cx="{x}" cy="{y-r*0.34}" r="{r}" fill="{col}"/>')


def tulip(x, y, s, col):
    return (f'<rect x="{x-1.7}" y="{y-s*1.7}" width="3.4" height="{s*1.7}" fill="{col}"/>'
            f'<path d="M{x-s*0.6},{y-s*1.7} L{x-s*0.6},{y-s*2.5} L{x},{y-s*2.0} '
            f'L{x+s*0.6},{y-s*2.5} L{x+s*0.6},{y-s*1.7} Z" fill="{col}"/>')


def gy(x):
    i = max(0, min(len(R["ink"]) - 1, int(x)))
    return cy(R["ink"][i])


fore = "".join([
    "".join(bush(x, gy(x) + 26 * LAND_K, r * PROP_K) for x, r in
            [(300, 46), (470, 36), (660, 52), (830, 40), (1000, 48), (1150, 34)]),
    "".join(leaf_tree(x, gy(x) + 40 * LAND_K, h * PROP_K) for x, h in
            [(44, 420), (140, 310), (232, 226), (1196, 236), (1290, 340), (1372, 448)]),
    fir(1108, gy(1108) + 36 * LAND_K, 300 * PROP_K),
    fir(1058, gy(1058) + 36 * LAND_K, 214 * PROP_K),
    fir(322, gy(322) + 36 * LAND_K, 208 * PROP_K),
    "".join(tulip(x, max(gy(x) + 34 * LAND_K, cy(726)), 17 * PROP_K, ACC2 if i % 2 else ACC1)
            for i, x in enumerate(range(80, W - 40, 96))),
])

# The sky gradient is a CSS background on .hero, not a layer. A featureless gradient has
# no measurable parallax -- and, more to the point, a sky that is a rect inside a sinking
# layer has a TOP EDGE. That edge is what used to slide into frame and "cut the sky". A
# backdrop with no edge cannot be cut, at any viewport, at any travel.
sky = (f'<svg class="ly" style="--f:{F_SKY}" viewBox="0 0 {W} {H}" '
       f'preserveAspectRatio="xMidYMax slice" aria-hidden="true"><defs>'
       f'<radialGradient id="glow"><stop offset="0" stop-color="{SUN}" stop-opacity=".95"/>'
       f'<stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient></defs>'
       f'<circle cx="700" cy="{SUN_CY}" r="330" fill="url(#glow)"/>'
       f'<circle cx="700" cy="{SUN_CY}" r="118" fill="{SUN}"/></svg>')

gold = hill("gold", "ggold", F_GOLD, GOLD_A, GOLD_B,
            "".join(fir(x, cy(R["gold"][x]) + 9 * LAND_K, (24 + (x % 29) * 0.5) * PROP_K, GOLD_B)
                    for x in range(24, W, 57)))
orng = hill("orange", "gorng", F_ORNG, ORNG_A, ORNG_B)
crim = (f'<svg class="ly" style="--f:{F_CRIM}" viewBox="0 0 {W} {H}" '
        f'preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
        f'<defs>{grad("gcrim", CRIM_A, CRIM_B)}</defs>'
        f'<path d="{ridge_path("crimson")}" fill="url(#gcrim)"/>{bridge()}{train()}</svg>')
navy = hill("purple", "gnavy", F_NAVY, NAVY_A, NAVY_B)
near = (f'<svg class="ly" style="--f:{F_INK}" viewBox="0 0 {W} {H}" '
        f'preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
        f'<path d="{ridge_path("ink")}" fill="{INK}"/>{fore}</svg>')

BH = 270
band_trees = "".join(leaf_tree(x, BH - 4, 175 + (x % 61)) for x in range(46, W, 168))
band_pops = "".join(
    f'<rect x="{x-2}" y="{BH-4-h}" width="4" height="{h}" fill="{NAVY_A}"/>'
    f'<circle cx="{x}" cy="{BH-4-h}" r="{h*0.2}" fill="{ACC1 if i%2 else ACC2}"/>'
    for i, (x, h) in enumerate((x, 118 + (x % 47)) for x in range(112, W, 152)))
band_hill = " ".join(f"L{x},{150+26*math.sin(x/165.0):.1f}" for x in range(0, W + 20, 20))
band = (f'<svg class="band" viewBox="0 0 {W} {BH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
        f'<path d="M0,{BH} L0,150 {band_hill} L{W},{BH} Z" fill="{NAVY_A}"/>{band_trees}{band_pops}</svg>')

HTML = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beyond Limits — a parallax landscape, recreated with motiscope</title>
<meta name="description" content="A scroll-driven parallax landscape recreated from a 2.25s screen recording. Traced terrain, measured layer speeds, and a train crossing the viaduct at a measured 1500 px/s.">
<meta property="og:site_name" content="motiscope">
<meta property="og:type" content="website">
<meta property="og:title" content="Beyond Limits — a parallax landscape, recreated with motiscope">
<meta property="og:description" content="Six depth layers and a train. The ridgelines are traced from the recording and the layer speeds are measured. The sky, honestly, is not recoverable.">
<meta property="og:url" content="https://kumarsashank.github.io/motiscope/examples/parallax/recreation.html">
<meta property="og:image" content="https://kumarsashank.github.io/motiscope/og/parallax.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="A layered dawn landscape: hills, a viaduct with a train crossing it, and dark foreground trees.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Beyond Limits — a parallax landscape, recreated with motiscope">
<meta name="twitter:description" content="Traced terrain, measured layer speeds, and a train at a measured 1500 px/s.">
<meta name="twitter:image" content="https://kumarsashank.github.io/motiscope/og/parallax.png">
<meta name="twitter:image:alt" content="A layered dawn landscape: hills, a viaduct with a train crossing it, and dark foreground trees.">
<link rel="canonical" href="https://kumarsashank.github.io/motiscope/examples/parallax/recreation.html">
<style>
  :root {{ --ink:{INK}; --paper:#EAF7F1; --acc1:{ACC1}; --s:0px;
           /* Travel used to be clamped at 240px -- a third of one screen -- because the
              sky was a rect inside a sinking layer, and its top edge slid into frame.
              The sky is now the hero's own background, so nothing can uncover it. The
              clamp only exists to bound the transform once the hero has left. */
           --pmax:900px; }}
  * {{ box-sizing:border-box; margin:0; }}
  html {{ scroll-behavior:smooth; }}
  body {{ background:var(--ink); color:var(--paper); overflow-x:hidden;
         font:16px/1.65 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}

  /* The sky is the backdrop, not a layer: it spans the hero, has no top edge, and never
     moves. The hills sink across it. This is what a sky at infinity actually does. */
  /* Sky as a guarantee, not an accident. The art is bottom-anchored and width-scaled, so the
     hero shows exactly heroH*1400/heroW canvas rows and the terrain is {LAND_ROWS:.0f} of them. Sky
     therefore exists only while heroH > {LAND_ROWS/W:.3f}*heroW -- true on any display 16:9 or taller,
     false on a short wide window, which is how the old build showed no sky at all there.
     Sizing the hero FROM the terrain makes the band deterministic: >= 96px wherever the
     130svh cap does not bind. Past that (a deliberately squat window) the art overscans
     and the sky is gone -- `slice` is cover, and cover must crop one axis.
     The plain 100vh comes first: a browser that does not know `svh` drops the whole clamp,
     and a hero with no height collapses to nothing. */
  .hero {{ position:relative; overflow:hidden; min-height:560px;
          height:100vh;
          height:clamp(100svh, calc(100vw * {LAND_ROWS/W:.4f} + 96px), 130svh);
          background:linear-gradient(180deg, #F4FCF8 0%, {SKY_TOP} 16%,
                                     {SKY_MID} 52%, {SKY_LOW} 100%); }}
  .ly {{ position:absolute; inset:0; width:100%; height:100%; display:block;
         transform:translate3d(0, calc(min(var(--s), var(--pmax)) * (1 - var(--f))), 0);
         will-change:transform; }}

  /* The train is bound to the scroll, not to a clock.
     In the recording the train ran at {TRAIN_PXS:.0f} px/s while the page scrolled at
     {SCROLL_PXS:.0f} px/s, so it covers {TRAIN_PER_SCROLL} units for every pixel you scroll.
     Scroll down -> it runs left to right. Scroll back up -> it reverses. */
  .train {{ transform-box:view-box;
            transform:translateX(calc({TRAIN_X0}px + var(--s) * {TRAIN_PER_SCROLL})); }}

  .hero-copy {{ position:absolute; inset:0; display:grid; place-content:start center; text-align:center;
      z-index:5; padding:16vh 24px 0; transform:translate3d(0, calc(var(--s) * -0.35), 0);
      opacity:clamp(0, calc(1 - var(--s) / 420), 1); }}
  .kicker {{ font:600 15px/1 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.42em;
      text-transform:uppercase; color:var(--ink); opacity:.72; }}
  .hero-copy h1 {{ margin:20px 0 0; font-size:clamp(44px,8.5vw,104px); line-height:.95;
      letter-spacing:-.03em; font-weight:800; color:#17405A; text-shadow:0 2px 0 rgba(255,255,255,.18); }}
  .scrollcue {{ position:absolute; left:50%; bottom:64px; z-index:6; translate:-50% 0;
      font:12px/1 ui-monospace,monospace; letter-spacing:.28em; text-transform:uppercase;
      color:var(--paper); opacity:.7; animation:bob 2.4s ease-in-out infinite; }}
  @keyframes bob {{ 50% {{ transform:translateY(7px); }} }}

  .band {{ display:block; width:100%; height:270px; margin-bottom:-2px; }}
  .prose {{ background:var(--ink); padding:26px 24px 110px; }}
  .prose .in {{ max-width:760px; margin:0 auto; text-align:center; }}
  .rule {{ width:170px; height:2px; background:var(--paper); opacity:.5; margin:0 auto 26px; }}
  .rule.b {{ margin:26px auto 0; width:118px; }}
  .prose h2 {{ font-size:clamp(26px,4vw,40px); letter-spacing:-.02em; font-weight:700; }}
  .prose p {{ margin-top:34px; color:#9FC3C0; font-size:17px; }}
  .cards {{ background:var(--ink); padding:0 24px 110px; }}
  .cards .in {{ max-width:1000px; margin:0 auto; display:grid; gap:16px; grid-template-columns:repeat(4,1fr); }}
  @media (max-width:860px) {{ .cards .in {{ grid-template-columns:1fr 1fr; }} }}
  .card {{ background:#0D2437; border:1px solid #17405A; border-radius:14px; padding:20px; }}
  .card h3 {{ font-size:15px; margin-bottom:8px; }}
  .card p {{ color:#8FB6B4; font-size:13.5px; }}
  .card b {{ color:var(--acc1); font:600 13px ui-monospace,monospace; }}
  footer {{ background:#061421; border-top:1px solid #143348; padding:28px 24px; color:#7EA3A6;
    font:13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace; text-align:center; }}
  footer a {{ color:var(--acc1); }}

  @media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior:auto; }}
    .ly, .hero-copy {{ transform:none !important; }}
    .hero-copy {{ opacity:1 !important; }}
    .scrollcue {{ animation:none; }}
    /* --s never advances, so the train simply rests on the bridge */
    .train {{ transform:translateX({TRAIN_X0}px); }}
  }}
</style>
</head>
<body>

<header class="hero">
  {sky}{gold}{orng}{crim}{navy}{near}
  <div class="hero-copy">
    <div class="kicker">Creative animation journey</div>
    <h1>Beyond Limits</h1>
  </div>
  <div class="scrollcue">scroll</div>
</header>

{band}
<section class="prose">
  <div class="in">
    <div class="rule"></div>
    <h2>Bring your design to the next level</h2>
    <div class="rule b"></div>
    <p>Six layers, one scroll, and a train. The hills behind you drift slower than the trees
      beside you, and that difference is the whole illusion of depth. Every ridgeline here was
      traced out of a 2.25-second recording; every speed below was measured from it. Scroll back
      up and the train reverses — it is a function of where you are, not of what time it is.</p>
  </div>
</section>

<section class="cards">
  <div class="in">
    <div class="card"><b>0.72&times;</b><h3>Mid hills</h3>
      <p>Mask alignment, reproduced at two independent scales.</p></div>
    <div class="card"><b>0.86&times;</b><h3>Deep hills</h3>
      <p>0.85&times; and 0.87&times; from two runs. The viaduct rides this layer.</p></div>
    <div class="card"><b>3.58 &times; scroll</b><h3>The train</h3>
      <p>1501&nbsp;px/s train against 419&nbsp;px/s scroll in the recording. Here it is bound to your scroll, so it runs left&nbsp;&rarr;&nbsp;right as you go down.</p></div>
    <div class="card"><b>not recoverable</b><h3>The sky</h3>
      <p>A smooth gradient has no stable mask. Estimates ran &minus;0.03 to 0.63, so we don&rsquo;t claim one.</p></div>
  </div>
</section>

<footer>
  Recreated with <a href="https://github.com/KumarSashank/motiscope">motiscope</a> from a 2.25s screen recording.
  Traced terrain, measured speeds, new palette.<br>
  Original animation from <a href="https://www.svgator.com/blog/website-animation-examples-and-effects/">SVGator&rsquo;s website-animation examples</a> — all credit to the original creator.
</footer>

<script>
  // One rAF-coalesced scroll write. CSS does the rest: translate3d(0, s*(1-f), 0).
  (function () {{
    var root = document.documentElement, ticking = false;
    function apply(y) {{ root.style.setProperty('--s', y + 'px'); }}
    // #s=600 freezes a scroll state: it sets --s AND shifts the document, so the frame
    // looks exactly like a real scroll. Used for verification and for rendering the video.
    var m = location.hash.match(/^#s=(\\d+)/);
    if (m) {{
      apply(+m[1]);
      document.body.style.transform = 'translateY(-' + m[1] + 'px)';
      return;
    }}
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    addEventListener('scroll', function () {{
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {{ apply(scrollY); ticking = false; }});
    }}, {{ passive: true }});
    apply(scrollY);
  }})();
</script>
</body>
</html>
'''
sys.stdout.write(HTML)
