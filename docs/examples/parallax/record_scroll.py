#!/usr/bin/env python3
"""Record the parallax hero being scrolled, straight from the published page.

This is not an animation *of* the page -- it is the page, at a sequence of real scroll
offsets. `recreation.html#s=<px>` sets --s and shifts the document by the same amount, so
a frozen frame is pixel-identical to what a person scrolling would see at that offset.

    python3 docs/examples/parallax/record_scroll.py

Writes scroll.mp4 (the case-study video), scroll.gif (the gallery thumbnail) and
scroll-poster.jpg (shown before the video loads).
"""
import pathlib, shutil, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "recreation.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1280, 720
FPS = 30
SCROLL_END = 620          # the train has left the bridge by s=408; this carries past it


def smoothstep(k):
    return k * k * (3 - 2 * k)


def timeline():
    """(scroll_px,) per frame: a beat at rest, a hand-paced scroll, a beat at the end."""
    f = [0] * 12
    n = 66
    f += [round(SCROLL_END * smoothstep(i / (n - 1))) for i in range(n)]
    f += [SCROLL_END] * 12
    return f


TL = timeline()


def shot(args):
    i, tmp = args
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={tmp}/f{i:03d}.png", f"--window-size={W},{H}",
                    "--virtual-time-budget=900", f"file://{PAGE}#s={TL[i]}"],
                   capture_output=True)


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="motiscope-scroll-"))
    print(f"{len(TL)} frames @ {FPS}fps = {len(TL)/FPS:.2f}s  ->  {tmp}")
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(shot, [(i, tmp) for i in range(len(TL))]))
    missing = [i for i in range(len(TL)) if not (tmp / f"f{i:03d}.png").exists()]
    for i in missing:
        shot((i, tmp))
    assert not [i for i in range(len(TL)) if not (tmp / f"f{i:03d}.png").exists()], "frames missing"
    print(f"rendered {len(list(tmp.glob('*.png')))} frames (retried {len(missing)})")

    run = lambda c: subprocess.run(c, check=True, capture_output=True)
    run(["ffmpeg", "-v", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%03d.png",
         "-vf", "scale=1280:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "24", "-movflags", "+faststart", "-y", str(HERE / "scroll.mp4")])
    run(["ffmpeg", "-v", "error", "-i", f"{tmp}/f000.png", "-vf", "scale=1280:-2",
         "-q:v", "6", "-y", str(HERE / "scroll-poster.jpg")])
    # The gallery card is ~560px wide, so the gif is 640px at 10fps with a 48-colour palette.
    # Flat vector art dithers badly and needs few colours; this lands under 600 KB.
    pal = tmp / "pal.png"
    vf = "fps=10,scale=640:-1:flags=lanczos"
    run(["ffmpeg", "-v", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%03d.png",
         "-vf", f"{vf},palettegen=max_colors=48:stats_mode=diff", "-y", str(pal)])
    run(["ffmpeg", "-v", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%03d.png",
         "-i", str(pal), "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
         "-loop", "0", "-y", str(HERE / "scroll.gif")])
    shutil.rmtree(tmp)

    for n in ("scroll.mp4", "scroll.gif", "scroll-poster.jpg"):
        print(f"  {n:20s} {(HERE / n).stat().st_size / 1024:7.0f} KB")


if __name__ == "__main__":
    main()
