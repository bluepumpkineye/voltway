"""Avatr 06T cabin cameras: the photo measurements and the solves behind the cabin's hardpoints.

The photographs are Autohome's (blender/reference/avatr-06t/interior, series 8538, the Misty Purple /
Cotton White cabin). Coordinates are photo pixels (u right, v down) of the 3840 x 2880 originals; model
metres are the build's own (x forward, y left, z up, car centre at x = 0).

    dash_front   c10_0001.jpg: straight down the cabin from behind the console on the centreline, wide
                 lens (both A-pillars, the header, the 35.4 in display, the 15.6 in screen, the wheel)

Known in 3D: the windscreen's side edge up each A-pillar (a06t_panels.V_A) and its top edge
(a06t_panels._x_header). The centre screen's outer frame gives the depth; its centre, tilt and size are
solved with the camera.

    blender -b --factory-startup --python run.py -- a06t_cabinsolve "M.show('dash_front', M.solve_front())"
"""
import math

from carkit.qa import refmatch as R

CABIN_SIZE = (3840, 2880)

# c10_0001: where the bright windscreen meets the black frit band along each A-pillar (read on 1.92x grid crops)
A_IN_L = [(78, 731), (138, 796), (218, 879), (294, 962), (385, 1040), (468, 1111)]
A_IN_R = [(3720, 726), (3679, 778), (3611, 858), (3549, 931), (3471, 1025), (3414, 1082), (3351, 1134)]
# the windscreen's top edge where the headliner starts, near each pillar
HEADER_L = [(60, 717), (260, 712), (520, 705)]
HEADER_R = [(3320, 700), (3600, 710)]
# the 15.6 in screen's outer frame (sharp corners, extrapolated from the rounded ones): TL TR BL BR
SCREEN = [((1451, 1386), 1, 1), ((2315, 1386), -1, 1), ((1447, 1899), 1, -1), ((2316, 1907), -1, -1)]


class _Path(R.Circle):
    """An open 3D polyline for solve_camera's curve matching (out and back, so the loop's closing
    segment is degenerate)."""

    def __init__(self, pts):
        from mathutils import Vector
        self.pts = [Vector(p) for p in pts]

    def points(self):
        return self.pts + self.pts[::-1]


def _curves(d_in=0.020, depth=0.015):
    import a06t_panels as PN
    import a06t_surface as S

    def a_edge(side):
        out = []
        x0, x1 = PN.X_ROOF_F + 0.01, PN.A_FOOT[0] - 0.01
        for k in range(31):
            x = x0 + (x1 - x0) * k / 30.0
            p = S.surface_offset(x, S.v_along(x, PN.V_A(x), d_in), -depth)
            out.append((p[0], side * p[1], p[2]))
        return _Path(out)

    def header(side):
        out = []
        v0 = PN.V_A(PN.X_ROOF_F) + 0.010
        for k in range(21):
            v = v0 + (0.999 - v0) * k / 20.0
            x = PN._x_header(v) - 0.030          # the headliner's front edge, 30 mm behind the glass's top
            p = S.surface_offset(x, v, -0.020)
            out.append((p[0], side * p[1], p[2]))
        return _Path(out)

    return dict(a_in=[a_edge(1.0), a_edge(-1.0)], header=[header(1.0), header(-1.0)])


STARTS = [(lx, lz, pit, f) for lx in (-1.4, -1.0, -0.6) for lz in (1.20, 1.40)
          for pit in (76.0, 86.0) for f in (1800.0, 2600.0)]


def solve_front(starts=STARTS, use_header=True, fix=("y", "ry"), d_in=0.020, size=None):
    """dash_front: the camera and, as extras, the screen's (x, z, tilt deg, width, height); with size=(W, H) the
    screen's size is held instead."""
    c = _curves(d_in=d_in)

    def corner(cu, cv):
        def f(e):
            t = math.radians(e[2])
            W, H = (e[3], e[4]) if size is None else size
            return (e[0] + cv * H / 2 * math.sin(t), cu * W / 2, e[1] + cv * H / 2 * math.cos(t))
        return f

    pairs = [(p, c["a_in"][0]) for p in A_IN_L] + [(p, c["a_in"][1]) for p in A_IN_R]
    if use_header:
        pairs += [(p, c["header"][0]) for p in HEADER_L] + [(p, c["header"][1]) for p in HEADER_R]
    pairs += [(uv, corner(cu, cv)) for (uv, cu, cv) in SCREEN]
    extra = (0.45, 1.05, 10.0) + ((0.352, 0.220) if size is None else ())
    best = None
    for (lx, lz, pitch, f) in starts:
        s = R.solve_camera(CABIN_SIZE, pairs, (lx, 0.0, lz), (pitch, 0.0, -90.0), f,
                           fix=fix, extra=extra, iters=300)
        if best is None or s["rms"] < best["rms"]:
            best = s
    return best


def show(name, s):
    print("%s: loc %s rot %s f %.1f (%.1f mm) rms %.2f px" % (
        name, tuple(round(c, 4) for c in s["loc"]), tuple(round(c, 3) for c in s["rot"]),
        s["f_px"], s["lens_mm"], s["rms"]))
    if s.get("extra"):
        print("   extra:", tuple(round(c, 4) for c in s["extra"]))
    for k, (du, dv) in enumerate(s["resid"]):
        print("   %2d  %6.1f %6.1f" % (k, du, dv))
