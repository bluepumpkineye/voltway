"""Zeekr 7X nose and tail caps - the curves of its two WrapCaps.

The cap maths is carkit.body.caps (WrapCap); see su7_nose.py for what each
curve means.

    C(w, v)     v = the body loft's section parameter
                w = 1 at the shut line where the cap meets the loft, 0 on
                    the centreline

First pass (the side photograph through its solved camera, zx_camsolve): the
nose is a near-vertical wall at x 2.38-2.40 from the lip (z 0.26, x 2.4175) to
the hood's edge (z 0.89); the tail's rear outline runs -2.36 .. -2.42.
"""
import zx_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
# Given as (z, x) read off the side photograph (zx_panels has the reading's
# pixels) and turned into x(v) on the built loft, so they follow any later change
# to the sections.
def _by_v(pts_zx, top=None):
    out = []
    for (z, x) in pts_zx:
        v = S.BODY.v_at_z(x, z, 0.0, 1.0)
        if out and v <= out[-1][0] + 1e-4:
            continue
        out.append((v, x))
    if top is not None:
        while out and out[-1][0] > 0.985:
            out.pop()
        out.append((1.0, top))
    return Curve(out)


# Front: the bumper meets the fender along the front arch's lip (its edge is at
# x 2.04 at hub height) and the short seam from the arch top to the lamp's base
# (sA: (480,1750) - (580,1768) px, x 2.17 - 2.03, z 0.78), then the lamp's top.
JOIN_F = _by_v([(0.19, 2.250), (0.27, 2.120), (0.37, 2.052), (0.50, 2.030),
                (0.62, 2.022), (0.72, 2.030), (0.77, 2.060), (0.80, 2.130),
                (0.84, 2.190), (0.89, 2.240), (0.93, 2.285)], top=2.345)

# Rear: round the arch's lip (rear edge x -1.88), over its top and up the
# diagonal shut line to the lamp bar's end (sC: (3225,1577) - (3005,1685) px).
JOIN_R = _by_v([(0.20, -2.060), (0.30, -1.940), (0.37, -1.905), (0.50, -1.862),
                (0.60, -1.824), (0.70, -1.745), (0.78, -1.660), (0.83, -1.575),
                (0.86, -1.575), (0.93, -1.730), (1.006, -1.890), (1.060, -2.060),
                (1.100, -2.300)], top=-2.345)

# ------------------------------------------- centreline profiles, x given z
NOSE_X_OF_Z = Curve([
    (0.262, 2.4175), (0.300, 2.395), (0.360, 2.385), (0.450, 2.398),
    (0.550, 2.398), (0.660, 2.390), (0.740, 2.382), (0.790, 2.372),
    (0.820, 2.360), (0.835, 2.352), (0.845, 2.345),
])
NOSE_Z_LO, NOSE_Z_HI = 0.262, 0.845

TAIL_X_OF_Z = Curve([
    (0.280, -2.300), (0.300, -2.318), (0.360, -2.389), (0.430, -2.417),
    (0.500, -2.405), (0.620, -2.360), (0.750, -2.333), (0.890, -2.362),
    (1.000, -2.394), (1.080, -2.385), (1.118, -2.376),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.280, 1.118

# ------------------------------------------------------------- wrap blending
WRAP = Curve([
    (0.00, 0.0000), (0.10, 0.0087), (0.20, 0.0274), (0.30, 0.0614),
    (0.40, 0.1109), (0.50, 0.1739), (0.55, 0.2107), (0.60, 0.2515),
    (0.65, 0.2967), (0.70, 0.3472), (0.75, 0.4041), (0.80, 0.4689),
    (0.84, 0.5285), (0.88, 0.5968), (0.91, 0.6544), (0.94, 0.7260),
    (0.955, 0.7756), (0.97, 0.8305), (0.98, 0.8580), (0.99, 0.8878),
    (0.995, 0.9300), (1.00, 1.0000),
])
TAIL_WRAP = Curve([
    (0.00, 0.000), (0.20, 0.004), (0.40, 0.016), (0.55, 0.034),
    (0.68, 0.062), (0.78, 0.105), (0.86, 0.170), (0.92, 0.270),
    (0.96, 0.420), (0.985, 0.640), (0.996, 0.840), (1.00, 1.000),
])

NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.25, 2.20))


def dims_report():
    return BODY.dims_report()
