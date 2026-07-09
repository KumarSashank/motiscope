#!/usr/bin/env python3
"""Generate the ambient-loop recreation as a self-contained animated SVG.

Geometry + motion recreated from motiscope's analysis of ambient_loop.mov:
  grid      5x3 tiles of 267px at offset (18,9)  -> normalised to 200px tiles
  beat      0.75s (measured: burst peaks 0.317 / 1.067 / 1.817 on three tiles)
  loop      4 beats = 3.0s
  easing    strong ease-in-out per tick (velocity bursts, not constant velocity)
  stagger   ~41ms top-to-bottom (motiscope stagger hint)

Palette is deliberately NOT the source palette; shapes and motion are.
"""
import math, sys

T = 200                      # tile size
BEAT = 0.75
LOOP = 4 * BEAT              # 3.0s
ROT = 2 * BEAT               # 1.5s  (a full eased turn / two conveyor ticks)

# --- new palette (source colour -> ours) --------------------------------------
PAPER = "#FBF8F1"   # #FCFCFC white
TEAL  = "#17A2A2"   # #295EEF blue
PLUM  = "#37244F"   # #2F386F navy
SAGE  = "#BFDCC6"   # #E6C0E2 lilac
SAND  = "#FBE3B8"   # #FBEDAE cream
AMBER = "#F5B335"   # #FBD346 yellow
CORAL = "#F2584B"   # #F946A8 pink


def pt(cx, cy, r, a):
    return (cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))


def sector(cx, cy, r, a0, a1):
    """Pie sector, CCW from a0 to a1 (degrees, 0 = east)."""
    da = (a1 - a0) % 360
    large = 1 if da > 180 else 0
    x0, y0 = pt(cx, cy, r, a0)
    x1, y1 = pt(cx, cy, r, a1)
    return (f"M{cx:.1f},{cy:.1f} L{x0:.1f},{y0:.1f} "
            f"A{r},{r} 0 {large} 0 {x1:.1f},{y1:.1f} Z")


def tri(pts, fill, cls="", style=""):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{fill}"{cls}{style}/>'


def A(cls, origin=None, delay=None):
    """class + transform-origin (absolute user units) + own delay as --d.

    The delay is a custom property, not `animation-delay`, so the freeze harness
    can offset every element by a shared --t without destroying per-element phase.
    """
    s = f' class="{cls}"'
    st = []
    if origin:
        st.append(f"transform-origin:{origin[0]:.1f}px {origin[1]:.1f}px")
    if delay:
        st.append(f"--d:{delay}")
    if st:
        s += f' style="{";".join(st)}"'
    return s


tiles = []


def tile(r, c, body):
    ox, oy = c * T, r * T
    stagger = f"{r * 0.041:.3f}s"
    tiles.append(f'''  <g clip-path="url(#k{r}{c})" style="--stag:{stagger}">
{body(ox, oy)}
  </g>''')


# ---------------------------------------------------------------- row 0
def t00(ox, oy):                                  # target: rocking square + ripple
    h = T / 2
    rings = ""
    cols = [PLUM, SAND, PLUM, SAND]
    for i, col in enumerate(cols):                # d0 = backmost = most elapsed
        d = -(3 - i) * BEAT
        rings += (f'\n    <circle cx="{ox+100}" cy="{oy+100}" r="95" fill="{col}"'
                  f'{A("ring", (ox+100, oy+100), f"{d}s")}/>')
    return f'''    <rect x="{ox}" y="{oy}" width="{h}" height="{h}" fill="{CORAL}"/>
    <rect x="{ox+h}" y="{oy}" width="{h}" height="{h}" fill="{SAND}"/>
    <rect x="{ox}" y="{oy+h}" width="{h}" height="{h}" fill="{AMBER}"/>
    <rect x="{ox+h}" y="{oy+h}" width="{h}" height="{h}" fill="{CORAL}"/>
    <g{A("rock", (ox+100, oy+100))}>
      <rect x="{ox+25}" y="{oy+25}" width="150" height="150" fill="{PAPER}"/>
      <g clip-path="url(#sq00)">
        <rect x="{ox+36}" y="{oy+36}" width="128" height="128" fill="{SAND}"{A("bg2")}/>{rings}
      </g>
    </g>'''


def t01(ox, oy):                                  # rotating half-disc in a circle
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    {tri([(ox,oy),(ox+88,oy),(ox,oy+88)], AMBER)}
    {tri([(ox,oy+T),(ox+88,oy+T),(ox,oy+T-88)], AMBER)}
    {tri([(ox+T,oy+T),(ox+T-88,oy+T),(ox+T,oy+T-88)], AMBER)}
    <circle cx="{ox+100}" cy="{oy+100}" r="95" fill="{SAND}"/>
    <path d="{sector(ox+100, oy+100, 95, 0, 180)}" fill="{TEAL}"{A("spin-cw", (ox+100, oy+100))}/>'''


def t02(ox, oy):                                  # L collapses, square blooms
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <rect x="{ox}" y="{oy}" width="{T}" height="100" fill="{SAGE}"{A("shrinkY", (ox, oy))}/>
    <rect x="{ox}" y="{oy}" width="100" height="{T}" fill="{SAGE}"{A("shrinkX", (ox, oy))}/>
    <rect x="{ox+100}" y="{oy+100}" width="100" height="100" fill="{SAGE}"{A("bloom", (ox+T, oy+T))}/>'''


def t03(ox, oy):                                  # rotating pac-man
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{TEAL}"/>
    <path d="{sector(ox+100, oy+95, 88, 30, 330)}" fill="{PLUM}"{A("tick-cw", (ox+100, oy+95))}/>
    <circle cx="{ox+100}" cy="{oy+95}" r="41" fill="{PAPER}"/>
    <circle cx="{ox+100}" cy="{oy+95}" r="17" fill="{SAGE}"/>'''


def t04(ox, oy):                                  # triangle conveyor (scrolls up)
    body = ""
    for k in range(-2, 4):
        y = oy + k * 100
        col = AMBER if k % 2 == 0 else CORAL
        body += "\n    " + tri([(ox, y+100), (ox+T, y+100), (ox+100, y)], col)
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{TEAL}"/>
    <g{A("conv-up")}>{body}
    </g>'''


# ---------------------------------------------------------------- row 1
def t10(ox, oy):                                  # rotating half-plane
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <rect x="{ox-200}" y="{oy+100}" width="600" height="400" fill="{SAGE}"{A("spin-cw-half", (ox+100, oy+100))}/>'''


def t11(ox, oy):                                  # rocking square + circle
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{SAND}"/>
    <rect x="{ox+20}" y="{oy+20}" width="160" height="160" fill="{AMBER}"/>
    <g{A("rock-b", (ox+100, oy+100))}>
      <rect x="{ox+32}" y="{oy+32}" width="136" height="136" fill="{CORAL}"/>
      <circle cx="{ox+100}" cy="{oy+100}" r="48" fill="{SAGE}"/>
    </g>'''


def t12(ox, oy):                                  # dome conveyor (scrolls down)
    body = ""
    for k in range(-2, 4):
        y = oy + k * 100
        col = PLUM if k % 2 == 0 else TEAL
        body += f'\n    <path d="{sector(ox+100, y, 100, 180, 360)}" fill="{col}"/>'
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <g{A("conv-down")}>{body}
    </g>'''


def t13(ox, oy):                                  # rotating pie wedge + corners
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <circle cx="{ox}" cy="{oy}" r="105" fill="{AMBER}"/>
    <circle cx="{ox+T}" cy="{oy}" r="105" fill="{TEAL}"/>
    <circle cx="{ox}" cy="{oy+T}" r="105" fill="{PLUM}"/>
    <circle cx="{ox+T}" cy="{oy+T}" r="105" fill="{AMBER}"/>
    <circle cx="{ox+100}" cy="{oy+100}" r="95" fill="{PAPER}"/>
    <path d="{sector(ox+100, oy+100, 95, 40, 130)}" fill="{AMBER}"{A("spin-ccw-half", (ox+100, oy+100))}/>'''


def t14(ox, oy):                                  # scaling quarter-disc
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <circle cx="{ox+T}" cy="{oy+T}" r="205" fill="{SAND}"{A("pulse-a", (ox+T, oy+T))}/>'''


# ---------------------------------------------------------------- row 2
def t20(ox, oy):                                  # circle + rotating half + ring
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PLUM}"/>
    {tri([(ox,oy+T),(ox+90,oy+T),(ox,oy+T-90)], TEAL)}
    <circle cx="{ox+100}" cy="{oy+100}" r="95" fill="{PAPER}"/>
    <path d="{sector(ox+100, oy+100, 95, 90, 270)}" fill="{SAGE}"{A("spin-cw", (ox+100, oy+100))}/>
    <circle cx="{ox+95}" cy="{oy+105}" r="34" fill="none" stroke="{AMBER}" stroke-width="24"/>'''


def t21(ox, oy):                                  # four pulsing triangles
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    {tri([(ox,oy),(ox+T,oy),(ox+100,oy+100)], SAND, A("pulse-b", (ox+100, oy)))}
    {tri([(ox,oy+T),(ox+T,oy+T),(ox+100,oy+100)], CORAL, A("pulse-b", (ox+100, oy+T)))}
    {tri([(ox,oy),(ox,oy+T),(ox+100,oy+100)], TEAL, A("pulse-a", (ox, oy+100)))}
    {tri([(ox+T,oy),(ox+T,oy+T),(ox+100,oy+100)], PLUM, A("pulse-a", (ox+T, oy+100)))}'''


def t22(ox, oy):                                  # expanding ripple rings
    cols = [TEAL, PAPER, AMBER, PLUM]
    rings = ""
    for i, col in enumerate(cols):
        d = -(3 - i) * BEAT
        rings += (f'\n    <circle cx="{ox+100}" cy="{oy+100}" r="145" fill="{col}"'
                  f'{A("ring", (ox+100, oy+100), f"{d}s")}/>')
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PLUM}"{A("bg4")}/>{rings}'''


def t23(ox, oy):                                  # four corner discs -> star
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{CORAL}"/>
    <circle cx="{ox}" cy="{oy}" r="118" fill="{AMBER}"{A("pulse-a", (ox, oy))}/>
    <circle cx="{ox+T}" cy="{oy}" r="118" fill="{SAND}"{A("pulse-b", (ox+T, oy))}/>
    <circle cx="{ox}" cy="{oy+T}" r="118" fill="{SAND}"{A("pulse-b", (ox, oy+T))}/>
    <circle cx="{ox+T}" cy="{oy+T}" r="118" fill="{SAGE}"{A("pulse-a", (ox+T, oy+T))}/>'''


def t24(ox, oy):                                  # rocking square
    return f'''    <rect x="{ox}" y="{oy}" width="{T}" height="{T}" fill="{PAPER}"/>
    <rect x="{ox+28}" y="{oy+28}" width="144" height="144" fill="{PLUM}"{A("rock-c", (ox+100, oy+100))}/>'''


for (r, c, fn) in [(0,0,t00),(0,1,t01),(0,2,t02),(0,3,t03),(0,4,t04),
                   (1,0,t10),(1,1,t11),(1,2,t12),(1,3,t13),(1,4,t14),
                   (2,0,t20),(2,1,t21),(2,2,t22),(2,3,t23),(2,4,t24)]:
    tile(r, c, fn)

clips = "\n".join(
    f'    <clipPath id="k{r}{c}"><rect x="{c*T}" y="{r*T}" width="{T}" height="{T}"/></clipPath>'
    for r in range(3) for c in range(5))

EASE = "cubic-bezier(.83,0,.17,1)"    # peak/mean angular speed ~3.6x -> a sharp snap
SOFT = "cubic-bezier(.45,0,.55,1)"

CSS = f"""
    * {{ transform-box: view-box; }}
    .spin-cw       {{ animation: spin {ROT}s {EASE} infinite; }}
    .spin-cw-half  {{ animation: spinh {LOOP}s {EASE} infinite; }}
    .spin-ccw-half {{ animation: spinhr {LOOP}s {EASE} infinite; }}
    .tick-cw       {{ animation: tick {LOOP}s {EASE} infinite; }}
    .conv-up       {{ animation: convup {ROT}s {EASE} infinite; }}
    .conv-down     {{ animation: convdn {ROT}s {EASE} infinite; }}
    .ring          {{ animation: grow {LOOP}s {EASE} infinite; }}
    .bg4           {{ animation: bg4 {LOOP}s step-end infinite; }}
    .bg2           {{ animation: bg2 {LOOP}s step-end infinite; }}
    .pulse-a       {{ animation: pulsea {ROT}s {EASE} infinite; }}
    .pulse-b       {{ animation: pulseb {ROT}s {EASE} infinite; }}
    .shrinkY       {{ animation: shrinky {LOOP}s {EASE} infinite; }}
    .shrinkX       {{ animation: shrinkx {LOOP}s {EASE} infinite; }}
    .bloom         {{ animation: bloom {LOOP}s {EASE} infinite; }}
    .rock          {{ animation: rock {LOOP}s {SOFT} infinite; }}
    .rock-b        {{ animation: rockb {LOOP}s {SOFT} infinite; }}
    .rock-c        {{ animation: rockc {LOOP}s {SOFT} infinite; }}
    /* every animated element: own phase + measured ~41ms row stagger - freeze offset.
       fill-mode: both is load-bearing -- a positive stagger delay would otherwise show
       the element un-transformed (a ripple ring at full radius) until its turn came. */
    [class] {{ animation-delay: calc(var(--d, 0s) + var(--stag, 0s) - var(--t, 0s));
               animation-fill-mode: both; }}

    @keyframes spin   {{ to {{ transform: rotate(-360deg); }} }}
    @keyframes spinh  {{ 0%{{transform:rotate(0)}} 50%{{transform:rotate(-180deg)}}
                         100%{{transform:rotate(-360deg)}} }}
    @keyframes spinhr {{ 0%{{transform:rotate(0)}} 50%{{transform:rotate(180deg)}}
                         100%{{transform:rotate(360deg)}} }}
    @keyframes tick   {{ 0%{{transform:rotate(0)}} 25%{{transform:rotate(-90deg)}}
                         50%{{transform:rotate(-180deg)}} 75%{{transform:rotate(-270deg)}}
                         100%{{transform:rotate(-360deg)}} }}
    @keyframes convup {{ 0%{{transform:translateY(0)}} 50%{{transform:translateY(-100px)}}
                         100%{{transform:translateY(-200px)}} }}
    @keyframes convdn {{ 0%{{transform:translateY(0)}} 50%{{transform:translateY(100px)}}
                         100%{{transform:translateY(200px)}} }}
    @keyframes grow   {{ 0%{{transform:scale(0)}} 25%{{transform:scale(.25)}}
                         50%{{transform:scale(.5)}} 75%{{transform:scale(.75)}}
                         100%{{transform:scale(1)}} }}
    @keyframes bg4    {{ 0%{{fill:{PLUM}}} 25%{{fill:{TEAL}}} 50%{{fill:{PAPER}}} 75%{{fill:{AMBER}}} }}
    @keyframes bg2    {{ 0%{{fill:{SAND}}} 25%{{fill:{PLUM}}} 50%{{fill:{SAND}}} 75%{{fill:{PLUM}}} }}
    @keyframes pulsea {{ 0%{{transform:scale(1)}} 50%{{transform:scale(.62)}} 100%{{transform:scale(1)}} }}
    @keyframes pulseb {{ 0%{{transform:scale(.62)}} 50%{{transform:scale(1)}} 100%{{transform:scale(.62)}} }}
    @keyframes shrinky{{ 0%,10%{{transform:scaleY(1)}} 22%,58%{{transform:scaleY(0)}}
                         70%,100%{{transform:scaleY(1)}} }}
    @keyframes shrinkx{{ 0%,10%{{transform:scaleX(1)}} 22%,58%{{transform:scaleX(0)}}
                         70%,100%{{transform:scaleX(1)}} }}
    @keyframes bloom  {{ 0%,10%{{transform:scale(0)}} 22%,58%{{transform:scale(1)}}
                         70%,100%{{transform:scale(0)}} }}
    @keyframes rock   {{ 0%{{transform:rotate(-9deg)}} 50%{{transform:rotate(9deg)}}
                         100%{{transform:rotate(-9deg)}} }}
    @keyframes rockb  {{ 0%{{transform:rotate(8deg)}} 50%{{transform:rotate(-8deg)}}
                         100%{{transform:rotate(8deg)}} }}
    @keyframes rockc  {{ 0%{{transform:rotate(-14deg)}} 50%{{transform:rotate(6deg)}}
                         100%{{transform:rotate(-14deg)}} }}

    /* Reduced motion: freeze on a real frame of the loop, don't disable the animations.
       `animation: none` would drop every transform, blowing each ripple ring up to its
       full radius -- the tiles would render as flat discs, not concentric rings. */
    @media (prefers-reduced-motion: reduce) {{
      svg {{ --t: 0.35s; }}
      [class] {{ animation-play-state: paused !important; }}
    }}
"""

# A frozen render at time t (for verification): pause everything at a chosen offset.
freeze = ""
if len(sys.argv) > 2 and sys.argv[1] == "--freeze":
    t = float(sys.argv[2])
    freeze = f"""
    svg {{ --t: {t}s; }}
    [class] {{ animation-play-state: paused !important; }}
"""

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600"
     role="img" aria-label="Ambient geometric loop: a 5x3 grid of Bauhaus tiles, each rotating, scaling or scrolling on a 0.75s beat.">
  <title>Ambient loop — recreated with motiscope</title>
  <style>{CSS}{freeze}  </style>
  <defs>
{clips}
    <clipPath id="sq00"><rect x="36" y="36" width="128" height="128"/></clipPath>
  </defs>
  <rect width="1000" height="600" fill="{PAPER}"/>
{chr(10).join(tiles)}
</svg>
'''
sys.stdout.write(svg)
