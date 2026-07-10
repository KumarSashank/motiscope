# Measurement traps

Every trap below was hit while building the examples in this repo. Each one produced a
clean number with a tidy residual, and each one was wrong. None of them announce themselves.

> The failure mode of an automated measurement is not a crash. It is a confident float.

## 1. The curated frames are not an inventory of the scene

Frames are chosen by the **motion-energy signal**. Anything that is small, low-contrast,
briefly visible, or mostly occluded barely moves that signal, so it may not appear in a
single curated frame — while still being a headline feature of the animation.

In the parallax example, a **train crossing a bridge** never appeared in any curated frame.
It rides a viaduct that is off-screen for most of the clip, and it is dark-on-dark. The
curation was working exactly as designed; it was being asked a question it does not answer.

**Do this:**
- Treat the frames as *evidence*, never as *coverage*.
- Before you finalise a spec, ask: **is anything else moving?** Scan the full clip, not just
  the frames. `ffmpeg`-diff a region, or sample uniformly at a rate the curation ignored.
- If the user names something you cannot see (a train, a cursor, a badge), **believe them and
  go look**. Do not conclude it isn't there because it isn't in the frames.

## 2. An occluded feature reports a confident, wrong constant

If the thing you are tracking is hidden behind something else, its coordinate stops changing.
Nothing about the resulting number says "I am pinned."

Tracking the parallax train's **nose** gives `16 px/s`. Tracking its **tail** gives `1500 px/s`.
The nose sits behind a foreground tree for the entire clip, so it reads a constant `x=1223`
and fits a beautiful, almost-flat line.

**Do this:**
- Before fitting, check whether the tracked value is **clamped** — pinned at a frame edge, or
  constant while everything else moves.
- Prefer the end of an object that stays in the open. Prefer features that are *interior* to
  the frame over ones that touch its border.
- A residual near zero on a feature you expect to move is a red flag, not a green one.

## 3. Two estimators, or you have none

Three of four methods for the parallax layer speeds were wrong, and all three looked fine:

| Method | What it actually measured |
|---|---|
| fixed viewport bands | the page scroll, not the layer |
| topmost ridge row | whichever hill peak was tallest that frame; clamped at the screen edge |
| textured-patch tracking | the purple **headline text**, mistaken for a purple hill |
| mask alignment over a common window | the layer |

They were caught only because they disagreed **by up to 6×**. Any one of them, run alone,
would have shipped.

**Do this:**
- Measure the same quantity **two independent ways** — a different scale, a different feature,
  a different algorithm.
- When they agree, believe them. `0.72 / 0.72` and `0.85 / 0.87` are results.
- When they disagree, **say so**. `-0.03 .. 0.63` across methods is not a number to average
  into `0.30` — it is the finding *"not recoverable from this clip"*.

## 4. Objects that enter the frame corrupt any extent-based statistic

If a layer, element or object is **entering or leaving** the viewport during the window you
measure, then its topmost row, its centroid, its bounding box and its pixel count all change
for reasons that have nothing to do with the motion you want.

**Do this:**
- Restrict to the window where **everything you're comparing is fully on screen at once**, and
  accumulate the *same number of steps* for each thing. Cumulative sums over different step
  counts are not comparable, and the bug is invisible in the output.

## 5. Occlusion bias has a direction — exploit it, don't filter it

Occluders sit **in front**, which in a landscape means **above**. So a first-occurrence trace
of a hill ridge is pulled *upward* wherever a tree crosses it. The error is one-sided.

A median filter does **not** fix this: a tree crown spans 200 columns, and the median follows
it. The terrain is the **upper quantile** of the raw trace over a wide window.

**Do this:** ask which way the contamination pushes, then pick a statistic that is robust in
*that direction*. Reason about the artifact's physics before reaching for a filter.

## 6. A staggered group's aggregate energy is a bell, not its elements' curve

Four elements, each `ease-out`, fired 90ms apart, produce an energy curve that ramps up as
elements join and down as they finish. That is a bell. A bell fits `ease-in-out`.

**Every element is ease-out; their sum is not.** motiscope reported `ease-in-out` for a hero
entrance whose every member was `cubic-bezier(.16,1,.3,1)`, and it was describing the aggregate
faithfully.

**Do this:** per-element easing is *not* recoverable from aggregate energy. Take the segment's
timing from the numbers and the per-element curve from the frames — or from a focused
`--start/--end` window over a single element.

The same clip's **stagger hint** read `342ms, right-to-left`. That was the page scrolling, not
the 90ms hero stagger. On a walkthrough the dominant motion is the scroll, and the hint reports
the dominant motion.

## 7. Brightness is not intent

A page whose footer is darker than its hero will make a *scroll into the footer* look exactly
like a `fade-out`: brightness ramps down, `blackdetect` fires, and the segment gets a beautifully
fitted easing curve that is real and irrelevant.

The **timing** was exact — the segment began on the authored millisecond. Only the **label** was
wrong. No amount of signal processing fixes this; something has to look at the frames and say
"that is a scroll."

**Do this:** treat `fade-in` / `fade-out` as a hypothesis about *brightness*, not about *intent*.
Check it against a frame before you build a fade.

## 8. Scroll-driven is not time-driven

A parallax, a scroll-zoom, a pinned section: these are functions of **scroll position**. The
seconds in the recording belong to whoever moved the wheel.

- `duration`, `hold`, and the easing of a scroll capture describe **the recorder**, not the design.
- What *is* intrinsic is a **ratio**: layer speed ÷ page-scroll speed.
- A recording can contain **both kinds of clock**. In the parallax example the layers are
  scroll-driven while the train runs on a real timer — one clip, two different kinds of number.

**Do this:** set `"scroll_driven": true` in the spec, report ratios rather than seconds, and
say plainly which quantities are the recorder's. If you need to bind a time-driven object to
scroll, derive the constant from the recorded ratio and label the binding a design decision.

## 9. Verify in the substrate, not in your own render

Re-measuring pixels of your own output is a second chance to be wrong the same way. A
pixel-diff of the finished parallax page reported a mismatch — it was measuring occlusion and
the page background, not motion.

**Do this:** ask the runtime directly. In a browser that means `getBoundingClientRect`,
`getComputedStyle`, `getBBox`, `DOMMatrix` — the values the engine actually resolved:

```
scrollY=300
set_f=0.72  top=-216.0  implied_f=0.720
set_f=0.86  top=-258.0  implied_f=0.860
```

A layer's on-screen speed relative to the page **is** its parallax factor. That is a proof,
not a screenshot.

## 10. Beware caches when a test contradicts the file in front of you

Python validates a `.pyc` by source **mtime and size**. Change a constant to another of the
same byte length, restore it within the same second, and the stale bytecode is still
considered valid. A test will report a value the file does not contain.

**Do this:** if a measurement disagrees with the source you are reading, clear the cache
before you believe either of them.

---

## The one-line version

**Disagreement is the only evidence you have that a number is right.** Everything else is a
float with a plausible residual.
