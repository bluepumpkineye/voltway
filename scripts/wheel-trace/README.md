# Tracing a wheel from a photograph

How the faces of the Luxeed RX's three wheels and the SU7 Ultra's were read off
the Autohome photographs (`blender/reference/*/wheels`, local only). The tools
need only `sharp`, already a dependency. The wider story (what the traced style
builds, its pitfalls and assumptions) is in `docs/3d-pipeline.md`, "Wheel
designs".

1. **Unwarp.** Fit an ellipse to the wheel's lip (the bright ring against the dark
   tyre) and resample the photo so the ellipse is a circle of radius 0.45 of the
   image. Pick a photograph whose ratio (printed: minor / major axis) is above
   0.99; a tilted one shifts the deep parts by `depth x sin(tilt)`.

       node scripts/wheel-trace/unwarp.cjs photo.jpg <cx> <cy> <lip radius px> out.jpg 2400 bright 0.85 1.15

   `cx cy` and the radius are a rough guess in the photo's pixels; `bright` finds
   a bright-to-dark edge going outward (`dark` the other way).

2. **Lift the shadows.** Dark gloss paint, flanks and openings are unreadable at
   photographic exposure; trace from a gamma 2 to 2.6 copy.

       node scripts/wheel-trace/lift.cjs out.jpg out_g.jpg 2.4 1.1 -8

3. **Read it in polar coordinates.** Angle runs left to right, radius bottom to
   top, as fractions of the lip radius, with a labelled grid:

       node scripts/wheel-trace/polar.cjs out_g.jpg strip.jpg 15 105 0.12 1.02 12 1100

   (`theta0 theta1 r0 r1 px/deg px/unit`). One repeat of the five (72 deg) is
   enough; `grid.cjs` draws the same grid over the round picture.

4. **Trace the outlines** as polygons of `(angle deg, radius)` (counter-clockwise
   from 3 o'clock, seen from outside) in a JSON `{"period": 72, "polys": [{"pts":
   [[a, r], ...], "reps": [0, 1, 2, 3, 4]}]}`. Pass it as the last argument of
   `polar.cjs` to see the polygons, repeated every 72 deg, over the strip, or draw
   them over the round photograph, cropped and scaled:

       node scripts/wheel-trace/polyover.cjs out_g.jpg polys.json over.jpg 120 120 2160 2160 1500

   (`x0 y0 w h outW [gamma] [nogrid]`). Trace the SILHOUETTES of ribs, where the
   flank meets the gap: forged legs have sloped flanks the camera sees. Read a
   symmetric wheel as half-widths by radius, left and right averaged.

5. **Check the build against the photo.** Render the face alone as a mask with
   `blender/scripts/wheel_preview.py` (`face_on(design, out, only=('Spokes',),
   flat=True)`: the same size and convention; `only=('Inlay',)` for a second
   material's skin) and draw its outline over the unwarped photograph:

       node scripts/wheel-trace/maskedge.cjs unwarped.jpg mask.png overlay.jpg 1400

6. **Measure what is not an outline.** `colorarc.cjs` prints the angular
   intervals of a caliper's colour (yellow, orange, red) at each radius, which
   gave the calipers' spans and where they sit:

       node scripts/wheel-trace/colorarc.cjs out.jpg yellow 0.45,0.55,0.65,0.75

The polygons live in `blender/scripts/rx_wheels.py` and `su7_wheels.py`;
`carkit.parts.wheels` cuts them from a dished face (the `traced` spoke style).

## Centre the photograph on the axle first (added with the 7X's 20 in wheels)

`unwarp.cjs` centres the picture on the ellipse it fits to the lip ring, and that fit is biased by the
ring's lighting: the 7X photographs' axles sat 12 and 19 px below the middle of a 2400 px picture. It
is a tenth of a percent of the lip radius and a degree of angle at the windows beside the horizontal:
the first overlay of the twin-fork's traced bands lay about 10 px off at the side windows and fine at
the top one. Do not read it as a depth effect (parallax moves a deep hub, not the lip).

- `centrefit.cjs <uw.jpg> <repeats> [r0 r1 range]` finds the axle: a pattern of n identical repeats is
  a ruler, and the luminance at (angle + k * 360 / n) agrees across k only when the polar origin is the
  axle. It prints the shift in source pixels and the variance there and at the middle (the 7X
  twin-fork's halved: 1895 to 1051).
- `shift.cjs <in> <out> dx dy` moves the picture so that point is the middle. Make the copy, lift it
  (`lift.cjs`) and trace from the copies: the strips and `segment.cjs`'s voted pictures come out sharp.
  Read the corrected copy's half-widths: a symmetric window's half-width by radius is the same as the
  uncorrected vote's within 0.3 deg, but the angular phase of the side repeats was off by about a degree.
- Check a trace by laying the built face over the corrected photograph filled (`maskedge.cjs ... 0.5`):
  a band that matches in all the repeats is right; one that matches only at the top is the centre.

## Finding the repeat and reading outlines automatically (added with the Zeekr 7X)

- `period.cjs <uw.jpg> <r1,r2,...>` prints the dominant repeat (the circular autocorrelation of the
  luminance round those radii): the 7X's wheels came out 14-fold (25.7 deg), 5-fold and 5-fold; count by
  eye and you will be wrong on a 14-spoke wheel.
- `segment.cjs <uw.jpg> <out.json> key=value ...` lays the n repeats over each other, keeps a pixel in a
  class (a luminance and saturation range) only if more than half of the repeats agree - glare and tyre
  lettering on one spoke are voted out - traces and simplifies the outlines of the class and writes them
  as polygons of (angle, radius) for `polyover.cjs` and `carkit.parts.wheels`; `preview=` writes the mean
  picture of one repeat with the outlines over it, `lum=300:300 outlines=0` the clean mean picture alone,
  to read a shape off by eye. Works for bright shapes on dark (machined faces, the chrome disc); a window
  with the brake disc seen through it has no single luminance, read those off the mean picture.
