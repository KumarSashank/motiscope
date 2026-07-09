#!/usr/bin/env python3
"""Generate the parallax recreation — a scroll-driven landscape site.

Layer speeds recovered from parallax.mov by mask-alignment over the window where every
layer is on screen, at two independent scales:

    orange hills   0.72x  (0.72 / 0.72)   <- reproduced
    crimson hills  0.86x  (0.85 / 0.87)   <- reproduced
    purple hills   1.00x  (0.97 / 1.00)   <- moves with the foreground
    foreground     1.00x  (reference)
    sky / far      NOT RECOVERABLE - a smooth gradient has no stable mask;
                   estimates ranged -0.03..0.63 across methods.

Sky is pinned (0.00) and the far hills set to 0.30 -- both design choices inside the
measurement's uncertainty, stated as such in the README.

Same terrain, same depth stack, new palette.
"""
import math, sys

W, HH = 1600, 900          # hero SVG viewBox

# --- palette: cool alpine dawn (source was a warm sunset) ---------------------
SKY_TOP = "#EAF7F1"; SKY_MID = "#9BDCD0"; SKY_LOW = "#3AA3A8"
SUN     = "#FFE0A3"
FAR     = "#C6E9DF"        # was #FAE086 pale yellow
MID     = "#6AC6BC"        # was #FC7541 orange
DEEP    = "#2A7288"        # was #C9234C crimson
NAVY    = "#1B4C66"        # was #5B0081 purple
INK     = "#08192A"        # was #170433
ACC1    = "#FFB347"
ACC2    = "#F2603C"

# measured / chosen layer speeds
F_SKY, F_FAR, F_MID, F_DEEP, F_NEAR = 0.00, 0.30, 0.72, 0.86, 1.00


def ridge(y0, amp, terms, phase, w=W, step=16):
    """A smooth hill silhouette: a sum of sines, closed to the bottom of the box."""
    pts = []
    for x in range(0, w + step, step):
        t = x / w
        y = y0
        for k, (a, f) in enumerate(terms):
            y += a * amp * math.sin(2 * math.pi * (f * t + phase + 0.17 * k))
        pts.append((x, y))
    d = f"M0,{HH} L0,{pts[0][1]:.1f} "
    # Catmull-ish: straight segments at 16px are smooth enough at this scale
    d += " ".join(f"L{x},{y:.1f}" for x, y in pts[1:])
    d += f" L{w},{HH} Z"
    return d


def fir(x, y, h, col, w=None):
    w = w or h * 0.42
    return (f'<path d="M{x},{y-h} L{x+w/2},{y} L{x-w/2},{y} Z" fill="{col}"/>'
            f'<rect x="{x-1.5}" y="{y}" width="3" height="{h*0.12}" fill="{col}"/>')


def leaf_tree(x, y, h, col):
    """The source's foreground tree: a pointed leaf shape with a centre vein."""
    w = h * 0.52
    return (f'<g>'
            f'<rect x="{x-2.5}" y="{y-h*0.42}" width="5" height="{h*0.42}" fill="{col}"/>'
            f'<path d="M{x},{y-h} C{x+w/2},{y-h*0.72} {x+w/2},{y-h*0.36} {x},{y-h*0.30} '
            f'C{x-w/2},{y-h*0.36} {x-w/2},{y-h*0.72} {x},{y-h} Z" fill="{col}"/>'
            f'<path d="M{x},{y-h*0.95} L{x},{y-h*0.32}" stroke="{INK}" stroke-opacity=".35" stroke-width="2"/>'
            f'</g>')


def lollipop(x, y, h, col, cap):
    return (f'<rect x="{x-2}" y="{y-h}" width="4" height="{h}" fill="{col}"/>'
            f'<circle cx="{x}" cy="{y-h}" r="{h*0.22}" fill="{cap}"/>')


def tulip(x, y, s, col):
    return (f'<g><rect x="{x-1.6}" y="{y-s*1.7}" width="3.2" height="{s*1.7}" fill="{col}"/>'
            f'<path d="M{x-s*0.62},{y-s*1.7} L{x-s*0.62},{y-s*2.5} L{x},{y-s*2.0} '
            f'L{x+s*0.62},{y-s*2.5} L{x+s*0.62},{y-s*1.7} Z" fill="{col}"/></g>')


def bush(x, y, r, col):
    return (f'<circle cx="{x-r*0.7}" cy="{y}" r="{r*0.72}" fill="{col}"/>'
            f'<circle cx="{x+r*0.7}" cy="{y}" r="{r*0.66}" fill="{col}"/>'
            f'<circle cx="{x}" cy="{y-r*0.35}" r="{r}" fill="{col}"/>')


def viaduct(y, col, behind):
    """A viaduct is a solid deck with arches *punched out of it* -- the hill behind shows
    through the openings. Drawing the arches as filled shapes turns it into a row of blocks."""
    deck_h, span, gap = 22, 132, 26
    base = y + 150
    parts = [f'<rect x="150" y="{y}" width="1300" height="{base-y}" fill="{col}"/>']
    x = 176
    while x + span < 1450:
        r = span / 2
        cy = y + deck_h + 54
        parts.append(f'<path d="M{x},{base} L{x},{cy} A{r},{r} 0 0 1 {x+span},{cy} '
                     f'L{x+span},{base} Z" fill="{behind}"/>')
        x += span + gap
    parts.append(f'<rect x="140" y="{y}" width="1320" height="{deck_h}" fill="{col}"/>')
    return "".join(parts)


# ---------------------------------------------------------------- layers
sky = f'''<svg class="ly" style="--f:{F_SKY}" viewBox="0 0 {W} {HH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{SKY_TOP}"/><stop offset=".55" stop-color="{SKY_MID}"/>
    <stop offset="1" stop-color="{SKY_LOW}"/></linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="{SUN}" stop-opacity=".95"/>
    <stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient></defs>
  <rect width="{W}" height="{HH}" fill="url(#sky)"/>
  <circle cx="800" cy="428" r="400" fill="url(#glow)"/>
  <circle cx="800" cy="428" r="146" fill="{SUN}"/>
</svg>'''

far_firs = "".join(fir(x, 432 + 26 * math.sin(x / 190.0), 26 + (x % 31) * 0.6, FAR)
                   for x in range(30, W, 58))
far = f'''<svg class="ly" style="--f:{F_FAR}" viewBox="0 0 {W} {HH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <path d="{ridge(432, 58, [(1,1.1),(.45,2.3),(.2,4.1)], .12)}" fill="{FAR}"/>
  {far_firs}
</svg>'''

mid = f'''<svg class="ly" style="--f:{F_MID}" viewBox="0 0 {W} {HH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <path d="{ridge(520, 74, [(1,.9),(.4,2.1),(.22,3.7)], .55)}" fill="{MID}"/>
</svg>'''

deep = f'''<svg class="ly" style="--f:{F_DEEP}" viewBox="0 0 {W} {HH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <path d="{ridge(612, 64, [(1,.75),(.42,1.9),(.18,3.3)], .8)}" fill="{DEEP}"/>
  {viaduct(636, INK, DEEP)}
</svg>'''

near_trees = "".join(
    leaf_tree(x, 905, h, INK)
    for x, h in [(58, 470), (168, 350), (262, 250),
                 (1352, 262), (1452, 372), (1556, 486)])
near_firs = (fir(1240, 905, 330, INK) + fir(1300, 905, 240, INK)
             + fir(352, 905, 230, INK))
near_bushes = "".join(bush(x, 905, r, INK) for x, r in
                      [(430, 62), (600, 50), (760, 70), (930, 54), (1090, 66), (1180, 44)])
near_tulips = "".join(tulip(x, 890, 19, ACC2 if i % 2 else ACC1)
                      for i, x in enumerate(range(90, W - 60, 104)))
near = f'''<svg class="ly" style="--f:{F_NEAR}" viewBox="0 0 {W} {HH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <path d="{ridge(718, 50, [(1,.7),(.4,1.7)], .3)}" fill="{NAVY}"/>
  <path d="{ridge(806, 34, [(1,.6),(.35,1.5)], .9)}" fill="{INK}"/>
  {near_bushes}{near_trees}{near_firs}{near_tulips}
</svg>'''

# forest band that crowns the next section, as in the source
BH = 270
band_trees = "".join(leaf_tree(x, BH-4, 175 + (x % 61), INK) for x in range(46, W, 168))
# lollipops last, so their heads aren't chewed by the trees
band_pops = "".join(lollipop(x, BH-4, 118 + (x % 47), NAVY, ACC1 if i % 2 else ACC2)
                    for i, x in enumerate(range(112, W, 152)))
band_hill = ' '.join(f'L{x},{150+26*math.sin(x/165.0):.1f}' for x in range(0, W+20, 20))
band = f'''<svg class="band" viewBox="0 0 {W} {BH}" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
  <path d="M0,{BH} L0,150 {band_hill} L{W},{BH} Z" fill="{NAVY}"/>
  {band_trees}{band_pops}
</svg>'''

HTML = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beyond Limits — a parallax landscape, recreated with motiscope</title>
<meta name="description" content="A scroll-driven parallax landscape recreated from a 2.25s screen recording. Same terrain, same depth stack, measured layer speeds, new palette.">
<meta property="og:site_name" content="motiscope">
<meta property="og:type" content="website">
<meta property="og:title" content="Beyond Limits — a parallax landscape, recreated with motiscope">
<meta property="og:description" content="Five layers, one scroll. motiscope measured how much slower each ridge drifts — 0.72x and 0.86x, reproduced at two scales — and this page was rebuilt from those numbers.">
<meta property="og:url" content="https://kumarsashank.github.io/motiscope/examples/parallax/">
<meta property="og:image" content="https://kumarsashank.github.io/motiscope/og/parallax.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="A layered sunrise landscape with hills, a viaduct and dark foreground trees.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Beyond Limits — a parallax landscape, recreated with motiscope">
<meta name="twitter:description" content="Five layers, one scroll. Measured layer speeds, rebuilt as a scroll-driven page.">
<meta name="twitter:image" content="https://kumarsashank.github.io/motiscope/og/parallax.png">
<meta name="twitter:image:alt" content="A layered sunrise landscape with hills, a viaduct and dark foreground trees.">
<link rel="canonical" href="https://kumarsashank.github.io/motiscope/examples/parallax/">
<style>
  :root {{
    --ink:{INK}; --navy:{NAVY}; --deep:{DEEP}; --mid:{MID}; --far:{FAR};
    --acc1:{ACC1}; --acc2:{ACC2}; --paper:#EAF7F1;
    --s: 0px;                      /* scrollY, written by the rAF loop below */
  }}
  * {{ box-sizing:border-box; margin:0; }}
  html {{ scroll-behavior:smooth; }}
  body {{ background:var(--ink); color:var(--paper); overflow-x:hidden;
         font:16px/1.65 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}

  /* ---- the hero: every layer is a full-bleed SVG translated by scroll x (1 - f) ---- */
  .hero {{ position:relative; height:100vh; min-height:560px; overflow:hidden; }}
  .ly {{ position:absolute; inset:0; width:100%; height:100%; display:block;
         transform: translate3d(0, calc(var(--s) * (1 - var(--f))), 0);
         will-change: transform; }}
  .hero-copy {{ position:absolute; inset:0; display:grid; place-content:center;
      text-align:center; z-index:5; padding:0 24px;
      transform: translate3d(0, calc(var(--s) * -0.35), 0);
      opacity: clamp(0, calc(1 - var(--s) / 420), 1); }}
  .kicker {{ font:600 15px/1 ui-monospace,SFMono-Regular,Menlo,monospace;
      letter-spacing:.42em; text-transform:uppercase; color:var(--ink); opacity:.72; }}
  .hero-copy h1 {{ margin:20px 0 0; font-size:clamp(44px,8.5vw,104px); line-height:.95;
      letter-spacing:-.03em; font-weight:800; color:var(--navy);
      text-shadow:0 2px 0 rgba(255,255,255,.16); }}
  .scrollcue {{ position:absolute; left:50%; bottom:64px; z-index:6; translate:-50% 0;
      font:12px/1 ui-monospace,monospace; letter-spacing:.28em; text-transform:uppercase;
      color:var(--paper); opacity:.7; animation:bob 2.4s ease-in-out infinite; }}
  @keyframes bob {{ 50% {{ transform:translateY(7px); }} }}

  /* ---- the section the source scrolls down into ---- */
  .band {{ display:block; width:100%; height:270px; margin-bottom:-2px; }}
  .prose {{ background:var(--ink); padding:26px 24px 120px; }}
  .prose .in {{ max-width:760px; margin:0 auto; text-align:center; }}
  .rule {{ width:170px; height:2px; background:var(--paper); opacity:.55; margin:0 auto 26px; }}
  .rule.b {{ margin:26px auto 0; width:118px; }}
  .prose h2 {{ font-size:clamp(26px,4vw,40px); letter-spacing:-.02em; font-weight:700; }}
  .prose p {{ margin-top:34px; color:#9FC3C0; font-size:17px; }}

  .cards {{ background:var(--ink); padding:0 24px 120px; }}
  .cards .in {{ max-width:960px; margin:0 auto; display:grid; gap:18px;
                grid-template-columns:repeat(3,1fr); }}
  @media (max-width:760px) {{ .cards .in {{ grid-template-columns:1fr; }} }}
  .card {{ background:#0D2437; border:1px solid #17405A; border-radius:14px; padding:22px; }}
  .card h3 {{ font-size:16px; margin-bottom:8px; }}
  .card p {{ color:#8FB6B4; font-size:14px; }}
  .card b {{ color:var(--acc1); font:600 13px ui-monospace,monospace; }}

  footer {{ background:#061421; border-top:1px solid #143348; padding:28px 24px;
    color:#7EA3A6; font:13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace; text-align:center; }}
  footer a {{ color:var(--acc1); }}

  @media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior:auto; }}
    .ly, .hero-copy {{ transform:none !important; }}
    .hero-copy {{ opacity:1 !important; }}
    .scrollcue {{ animation:none; }}
  }}
</style>
</head>
<body>

<header class="hero">
  {sky}
  {far}
  {mid}
  {deep}
  {near}
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
    <p>Five layers, one scroll. The hills behind you drift slower than the trees beside you,
      and that difference is the whole illusion of depth. motiscope measured how much slower —
      then this page was rebuilt from those numbers.</p>
  </div>
</section>

<section class="cards">
  <div class="in">
    <div class="card"><b>0.72&times;</b><h3>Mid hills</h3>
      <p>Measured by mask alignment, and reproduced at two independent scales.</p></div>
    <div class="card"><b>0.86&times;</b><h3>Deep hills &amp; viaduct</h3>
      <p>0.85&times; and 0.87&times; from two runs. The bridge rides this layer.</p></div>
    <div class="card"><b>1.00&times;</b><h3>Foreground</h3>
      <p>Trees, bushes and tulips travel with the page. The reference layer.</p></div>
  </div>
</section>

<footer>
  Recreated with <a href="https://github.com/KumarSashank/motiscope">motiscope</a> from a 2.25s screen recording.
  Same terrain, same depth stack, new palette.<br>
  Original animation from <a href="https://www.svgator.com/blog/website-animation-examples-and-effects/">SVGator&rsquo;s website-animation examples</a> — all credit to the original creator.
</footer>

<script>
  // One rAF-coalesced scroll write. CSS does the rest via translate3d(0, s*(1-f), 0).
  (function () {{
    var root = document.documentElement, ticking = false;
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function apply(y) {{ root.style.setProperty('--s', y + 'px'); }}
    // #s=600 renders a fixed scroll state -- used to screenshot the page for verification
    var m = location.hash.match(/^#s=(\\d+)/);
    if (m) {{ apply(+m[1]); return; }}
    if (reduce) return;
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
