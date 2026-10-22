"""BYD Seal cabin cameras: the photo measurements and the solves behind the cabin cameras.

The photographs are Autohome's (blender/reference/byd-seal-ev/interior/full, series 6394, the
orange "Sardine Coral" cabin). Coordinates are photo pixels (u right, v down) of the 3840 x 2880
originals; model metres are the build's own (x forward, y left, z up, car centre at x = 0).

    cabin_over   d0126.jpg: straight down the cabin from behind the console, wide lens (both
                 A-pillars, the headliner, the screen, the wheel, the seats)

Known in 3D: the windscreen's side edge and the door glass's front edge up the A-pillar. The
centre screen (15.6 in, 2560 x 1600 = 16:10; its outer frame measured 0.352 x 0.224 m) fixes the
depth; its centre and tilt are solved with the camera.

    blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts');
        import seal_cabinsolve as CB; CB.show('cabin_over', CB.solve_over())"
"""
import math

from carkit.qa import refmatch as R

CABIN_SIZE = (3840, 2880)

A_IN_L = [(336, 511), (422, 633), (489, 722), (533, 778), (589, 878), (644, 989), (700, 1067),
          (756, 1117)]
A_IN_R = [(3483, 509), (3422, 578), (3367, 678), (3311, 767), (3256, 878), (3200, 989),
          (3139, 1083), (3106, 1117)]
A_OUT_L = [(200, 745), (250, 822), (311, 930), (355, 1000)]
A_OUT_R = [(3840, 600), (3611, 822), (3522, 956), (3483, 1011)]
# the windscreen's header: where the glass meets the headliner, a line in the plane x = 0.22
HEADER_L = [(350, 500), (700, 497), (1000, 495), (1300, 495)]
HEADER_R = [(2517, 467), (2800, 470), (3100, 480), (3433, 483)]
# the centre screen's outer frame: TL TR BL BR (image left = the car's left, +y)
SCREEN = [((1538, 1108), 1, 1), ((2280, 1110), -1, 1), ((1548, 1565), 1, -1),
          ((2282, 1565), -1, -1)]
SCREEN_W, SCREEN_H = 0.352, 0.224


class _Path(R.Circle):
    """An open 3D polyline for solve_camera's curve matching (out and back, so the loop's
    closing segment is degenerate)."""

    def __init__(self, pts):
        from mathutils import Vector
        self.pts = [Vector(p) for p in pts]

    def points(self):
        return self.pts + self.pts[::-1]


def _curves():
    import seal_panels as PN
    import seal_surface as S

    def edge(side, v_fn, x0, x1, d_in, depth=0.015):
        out = []
        for k in range(31):
            x = x0 + (x1 - x0) * k / 30.0
            p = S.surface_offset(x, S.v_along(x, v_fn(x), d_in), -depth)
            out.append((p[0], side * p[1], p[2]))
        return _Path(out)

    v_door = lambda x: min(PN.V_A(x) - 0.020, PN.V_GT(x))
    hdr = []
    for side in (1.0, -1.0):
        for k in range(21):
            v0 = PN.V_A(PN.X_ROOF_F) + 0.020
            v = v0 + (0.9995 - v0) * k / 20.0
            p = S.surface_offset(PN.X_ROOF_F, v, -0.012)
            hdr.append((p[0], side * p[1], p[2]))
    header = _Path(hdr[:21] + hdr[21:][::-1][:0] + [(q[0], -q[1], q[2]) for q in hdr[:21]][::-1])
    return dict(header=header, a_in=[edge(s, PN.V_A, PN.X_ROOF_F, PN.X_COWL - 0.010, 0.020) for s in (1.0, -1.0)],
                a_out=[edge(s, v_door, PN.X_ROOF_F, PN.X_COWL - 0.030, -0.015) for s in (1.0, -1.0)])


STARTS = [(lx, lz, pit, f) for lx in (-1.6, -1.2, -0.8) for lz in (1.15, 1.35)
          for pit in (78.0, 88.0) for f in (1800.0, 2600.0)]


def solve_over(starts=STARTS, use_out=False, use_header=True, fix=("y",)):
    """cabin_over: the camera and, as extras, the screen's (x, z, tilt)."""
    c = _curves()
    W, H = SCREEN_W, SCREEN_H

    def corner(cu, cv):
        def f(e):
            t = math.radians(e[2])
            return (e[0] + cv * H / 2 * math.sin(t), cu * W / 2, e[1] + cv * H / 2 * math.cos(t))
        return f

    pairs = ([(p, c["a_in"][0]) for p in A_IN_L] + [(p, c["a_in"][1]) for p in A_IN_R])
    if use_header:
        pairs += [(p, c["header"]) for p in HEADER_L + HEADER_R]
    if use_out:
        pairs += ([(p, c["a_out"][0]) for p in A_OUT_L] + [(p, c["a_out"][1]) for p in A_OUT_R])
    pairs += [(uv, corner(cu, cv)) for (uv, cu, cv) in SCREEN]
    best = None
    for (lx, lz, pitch, f) in starts:
        s = R.solve_camera(CABIN_SIZE, pairs, (lx, 0.0, lz), (pitch, 0.0, -90.0), f,
                           fix=fix, extra=(0.90, 0.95, 12.0), iters=300)
        if best is None or s["rms"] < best["rms"]:
            best = s
    return best


def show(name, s):
    print("%s: loc %s rot %s f %.1f (%.0f mm) rms %.2f px" % (
        name, tuple(round(c, 4) for c in s["loc"]), tuple(round(c, 3) for c in s["rot"]),
        s["f_px"], s["lens_mm"], s["rms"]))
    if s.get("extra"):
        print("   extra:", tuple(round(c, 4) for c in s["extra"]))
    for k, (du, dv) in enumerate(s["resid"]):
        print("   %2d  %6.1f %6.1f" % (k, du, dv))
