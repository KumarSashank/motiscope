#!/usr/bin/env python3
"""Render 1200x630 Open Graph cards for each page, in the motiscope theme.

Unfurlers (Slack, X, WhatsApp, LinkedIn, iMessage) want a *static* image at roughly
1200x630. The old og:image was a 640x360 animated GIF on raw.githubusercontent, which is
why previews were absent or downgraded to a small card.
"""
import subprocess, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "og"
OUT.mkdir(parents=True, exist_ok=True)
TMP = pathlib.Path(tempfile.mkdtemp(prefix="motiscope-og-"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SHELL = """<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face {{ font-family: x; src: local("Inter"), local("Helvetica Neue"); }}
  * {{ box-sizing: border-box; margin: 0; }}
  html, body {{ width:1200px; height:630px; overflow:hidden; }}
  body {{
    background:#0a0c12; color:#e7e9f2; position:relative;
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    display:flex; flex-direction:column; justify-content:space-between;
    padding:64px 68px;
  }}
  .glow {{ position:absolute; inset:-40% -10% auto -10%; height:120%;
    background:radial-gradient(60% 55% at 22% 12%, rgba(129,140,248,.30), transparent 62%),
               radial-gradient(50% 45% at 88% 8%,  rgba(232,121,249,.22), transparent 60%),
               radial-gradient(45% 40% at 60% 100%,rgba(34,211,238,.14), transparent 62%);
    pointer-events:none; }}
  .brand {{ display:flex; align-items:center; gap:14px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size:26px; font-weight:600; letter-spacing:.5px; position:relative; }}
  .dot {{ width:18px; height:18px; border-radius:50%;
    background:conic-gradient(from 0deg,#818cf8,#e879f9,#22d3ee,#818cf8);
    box-shadow:0 0 22px rgba(232,121,249,.65); }}
  .mid {{ position:relative; }}
  .eyebrow {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:19px; letter-spacing:3.4px;
    text-transform:uppercase; color:#e879f9; margin-bottom:22px; }}
  h1 {{ font-size:{size}px; line-height:1.05; letter-spacing:-2px; font-weight:700; max-width:{w}ch; }}
  h1 em {{ font-style:normal; color:#22d3ee; }}
  p {{ margin-top:24px; font-size:26px; line-height:1.42; color:#9aa0b4; max-width:30ch; }}
  .foot {{ display:flex; align-items:center; justify-content:space-between; position:relative;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:19px; color:#5c6380; }}
  .pills {{ display:flex; gap:10px; }}
  .pill {{ border:1px solid rgba(129,140,248,.30); border-radius:8px; padding:6px 13px; color:#9aa0b4; font-size:17px; }}
  .art {{ position:absolute; right:0; bottom:6px; width:{aw}px; border-radius:14px; overflow:hidden;
    border:1px solid rgba(129,140,248,.22); box-shadow:0 30px 80px -30px rgba(0,0,0,.85); line-height:0; }}
  .art img {{ width:100%; display:block; }}
</style></head><body>
  <div class="glow"></div>
  <div class="brand"><span class="dot"></span>motiscope</div>
  <div class="mid">
    <div class="eyebrow">{eyebrow}</div>
    <h1>{title}</h1>
    <p>{sub}</p>
    {art}
  </div>
  <div class="foot">
    <div class="pills">{pills}</div>
    <div>{url}</div>
  </div>
</body></html>"""


def card(name, eyebrow, title, sub, pills, url, size=64, w=17, art=None, aw=430):
    art_html = ""
    if art:
        art_html = f'<div class="art" style="width:{aw}px"><img src="file://{art}"></div>'
    html = SHELL.format(eyebrow=eyebrow, title=title, sub=sub, size=size, w=w,
                        pills="".join(f'<span class="pill">{p}</span>' for p in pills),
                        url=url, art=art_html, aw=aw)
    src = TMP / f"{name}.html"
    src.write_text(html)
    png = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={png}", "--window-size=1200,630",
                    "--force-prefers-reduced-motion", "--virtual-time-budget=1500",
                    f"file://{src}"], capture_output=True)
    return png


CURVE_SVG = ROOT / "docs" / "figures" / "energy-curve.svg"
curve = TMP / "curve.png"
subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                "--force-prefers-reduced-motion", "--default-background-color=10131cff",
                f"--screenshot={curve}", "--window-size=880,300",
                f"file://{CURVE_SVG}"], capture_output=True)

AMB = ROOT / "docs" / "examples" / "ambient" / "compare.gif"
# a still frame of the ambient loop for the art inset
still = TMP / "amb.png"
subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "docs/examples/ambient/ambient-loop.svg"),
                "-frames:v", "1", "-y", str(still)], capture_output=True)
if not still.exists() or still.stat().st_size < 1000:
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(AMB), "-vf",
                    "select=eq(n\\,10),crop=420:252:420:0", "-frames:v", "1", "-y", str(still)],
                   capture_output=True)

cards = [
    card("home", "see the motion, recreate the animation",
         "Drop a video.<br><em>Get animation code.</em>",
         "A screen recording in, working GSAP / CSS / Framer / Lottie out.",
         ["Claude Code", "Codex", "Cursor", "MIT"],
         "kumarsashank.github.io/motiscope", size=66, w=16, art=still, aw=400),
    card("how-it-works", "under the hood",
         "A screenshot has<br><em>no time axis.</em>",
         "The numbers measure the WHEN. The frames carry the WHAT.",
         ["energy curve", "fitted bezier", "ground truth"],
         "kumarsashank.github.io/motiscope/how-it-works", size=64, w=16,
         art=curve, aw=470),
    card("gallery", "gallery",
         "Real recordings in.<br><em>Real code out.</em>",
         "Every build shows the full chain — source, raw analysis, output, and what we got wrong.",
         ["transparent", "reproducible"],
         "kumarsashank.github.io/motiscope/gallery", size=62, w=17, art=still, aw=390),
    card("ambient", "example · animated svg",
         "Fifteen tiles.<br><em>One 0.75s beat.</em>",
         "Recreated from a 2.28s recording as 14 KB of animated SVG. Same motion, new palette.",
         ["measured", "verified", "14 KB"],
         "kumarsashank.github.io/motiscope/examples/ambient", size=60, w=17, art=still, aw=400),
]
for c in cards:
    print(f"  {c.name:<20} {c.stat().st_size:>7} bytes")
