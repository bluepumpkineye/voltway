"""Zeekr 7X cabin cameras: the photo measurements and the solves behind the cabin
cameras in zx_ref_match.

The cabin photographs are Autohome's (blender/reference/zeekr-7x/interior, series 7777,
the 2026 103 kWh Ultra with the cream-white / taupe cabin). Coordinates are photo pixels
(u right, v down) of the 3840 x 2880 originals; model metres are the build's own
(x forward, y left, z up, car centre at x = 0).

    cabin_over   c10_0001.jpg: straight down the cabin from behind the console, wide lens
                 (both A-pillars, the headliner, the screen, the wheel, the seats)

Known in 3D: the windscreen's side edge (the trim hides the last ~20 mm: the glass edge
is read 20 mm in from V_A and 15 mm under the skin) and the door glass's front edge up
the A-pillar. The centre screen (16 in, 16:10; its outer frame 0.359 x 0.236 m) fixes the
depth; its centre and tilt are solved with the camera.

    import zx_cabinsolve as CB
    CB.show("cabin_over", CB.solve_over())
"""
import math

from carkit.qa import refmatch as R

CABIN_SIZE = (3840, 2880)

# windscreen glass edge up the A-pillar (the black line between the trim and the glass)
A_IN_L = [(406, 581), (442, 668), (487, 767), (525, 850), (571, 942), (621, 1025),
          (667, 1096), (717, 1142)]
A_IN_R = [(3433, 583), (3383, 692), (3333, 783), (3283, 883), (3242, 958), (3183, 1050),
          (3117, 1117), (3067, 1150)]
# the door glass's front edge, the outer edge of the A-pillar trim
A_OUT_L = [(0, 554), (50, 608), (125, 700), (200, 800), (275, 900), (333, 992), (375, 1050)]
A_OUT_R = [(3840, 579), (3800, 629), (3733, 700), (3658, 783), (3592, 858), (3525, 942),
           (3467, 1008)]
# the centre screen's outer frame: TL TR BL BR (image left = the car's left, +y)
SCREEN = [((1559, 1240), 1, 1), ((2283, 1240), -1, 1), ((1557, 1717), 1, -1),
          ((2286, 1717), -1, -1)]
SCREEN_W, SCREEN_H = 0.359, 0.236
# the door mirrors' inboard edges, seen through the side glass: the rear glass face's
# inboard rim (zx_side.MIRROR_REAR x, y 0.950 - 0.075, z): points 0.5 m ahead of the
# camera's neighbours in depth, which pin the focal length against the pillars
MIRRORS = [((280, 1170), (0.691, 0.875, 1.168)), ((3560, 1170), (0.691, -0.875, 1.168))]


class _Path(R.Circle):
    """An open 3D polyline for solve_camera's curve matching (out and back, so the
    loop's closing segment is degenerate)."""

    def __init__(self, pts):
        from mathutils import Vector
        self.pts = [Vector(p) for p in pts]

    def points(self):
        return self.pts + self.pts[::-1]


def _curves():
    import zx_panels as PN
    import zx_surface as S

    def edge(side, v_fn, x0, x1, d_in, depth=0.015):
        out = []
        for k in range(31):
            x = x0 + (x1 - x0) * k / 30.0
            p = S.surface_offset(x, S.v_along(x, v_fn(x), d_in), -depth)
            out.append((p[0], side * p[1], p[2]))
        return _Path(out)

    return dict(a_in=[edge(s, PN.V_A, 0.50, 1.17, 0.020) for s in (1.0, -1.0)],
                a_out=[edge(s, PN.V_GT, 0.66, 1.17, -0.015) for s in (1.0, -1.0)])


def solve_over(f0=2200.0):
    """cabin_over: the camera and, as extras, the screen's (x, z, tilt)."""
    c = _curves()
    W, H = SCREEN_W, SCREEN_H

    def corner(cu, cv):
        def f(e):
            t = math.radians(e[2])
            return (e[0] + cv * H / 2 * math.sin(t), cu * W / 2, e[1] + cv * H / 2 * math.cos(t))
        return f

    pairs = ([(p, c["a_in"][0]) for p in A_IN_L] + [(p, c["a_in"][1]) for p in A_IN_R]
             + [(p, c["a_out"][0]) for p in A_OUT_L] + [(p, c["a_out"][1]) for p in A_OUT_R]
             + [(uv, corner(cu, cv)) for (uv, cu, cv) in SCREEN]
             + [(uv, X) for (uv, X) in MIRRORS])
    wts = [1.0] * (len(pairs) - 2) + [3.0, 3.0]
    best = None
    for f in (f0, 1600.0, 3000.0):
        s = R.solve_camera(CABIN_SIZE, pairs, (-1.20, 0.0, 1.30), (80.0, 0.0, -90.0), f,
                           fix=("ry",), extra=(0.60, 1.00, 12.0), iters=400, weights=wts)
        if best is None or s["rms"] < best["rms"]:
            best = s
    return best


def show(name, s):
    print("%s: loc %s rot %s f %.1f (%.0f mm) rms %.2f px" % (
        name, tuple(round(c, 4) for c in s["loc"]), tuple(round(c, 3) for c in s["rot"]),
        s["f_px"], s["lens_mm"], s["rms"]))
    if s.get("extra"):
        print("   extra:", tuple(round(c, 4) for c in s["extra"]))
