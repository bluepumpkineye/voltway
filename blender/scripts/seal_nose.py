"""BYD Seal EV nose and tail caps - the curves of its two WrapCaps.

The cap maths lives in carkit.body.caps (WrapCap).
BYD Seal EV dimensions: 4800 x 1875 x 1460 mm, Wheelbase 2920 mm.
"""
import seal_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
JOIN_F = Curve([
    (0.0000, 2.0900), (0.0800, 2.0700), (0.1800, 2.0300), (0.3000, 1.9850),
    (0.4200, 1.9550), (0.5250, 1.9480), (0.6200, 1.9680), (0.7200, 2.0150),
    (0.8200, 2.0700), (0.9000, 2.1700), (0.9600, 2.2500), (1.0000, 2.2900),
])

JOIN_R = Curve([
    (0.0000, -2.0600), (0.1000, -2.0350), (0.2200, -1.9900), (0.3400, -1.9550),
    (0.4600, -1.9300), (0.5600, -1.9250), (0.6600, -1.9420), (0.7600, -1.9800),
    (0.8600, -2.0350), (0.9400, -2.0850), (1.0000, -2.1200),
])

# Centreline profiles, x given z (BLUE c1_0513 silhouette read in metres: seal_cam.BLUE, y = 0)
# The Seal's nose is a nearly vertical face (x 2.36 at the chin lip to 2.41 at the BYD badge) under
# a hood that dives to z 0.69 at its leading edge.
NOSE_X_OF_Z = Curve([
    (0.1200, 2.3600), (0.1700, 2.3720), (0.2500, 2.3880), (0.3400, 2.4000),
    (0.4500, 2.4090), (0.5500, 2.4080), (0.6200, 2.3980), (0.6650, 2.3720),
    (0.6900, 2.3350),
], mode="pchip")
NOSE_Z_LO, NOSE_Z_HI = 0.1200, 0.6900

# The tail: a flat boot-lid face (x -2.33 at the duck-tail lip, z 1.02, to -2.36 low down), the
# bumper standing out to -2.404 at z 0.45, a diffuser tucked back to -2.345 at the bottom.
TAIL_X_OF_Z = Curve([
    (0.1700, -2.3450), (0.2500, -2.3720), (0.3400, -2.3950), (0.4500, -2.4040),
    (0.5500, -2.4000), (0.6500, -2.3800), (0.7500, -2.3620), (0.8500, -2.3500),
    (0.9400, -2.3380), (1.0000, -2.3320), (1.0200, -2.3300),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.1700, 1.0200

# ------------------------------------------------------------- wrap blending
# plan-view roundness g(w): flat across most of the width, turning hard at the corners
# (the tail face is flat across the boot lid; the nose is a broad shield)
WRAP = Curve([
    (0.0000, 0.0000), (0.3000, 0.0200), (0.5000, 0.0700), (0.6500, 0.1500),
    (0.7800, 0.2800), (0.8800, 0.4600), (0.9500, 0.7000), (1.0000, 1.0000),
])

TAIL_WRAP = Curve([
    (0.0000, 0.0000), (0.3500, 0.0100), (0.5500, 0.0300), (0.7000, 0.0900),
    (0.8000, 0.1900), (0.8800, 0.3500), (0.9400, 0.5800), (0.9800, 0.8200),
    (1.0000, 1.0000),
])

_SLOPE = {}
NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP, slope_cache=_SLOPE)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP, slope_cache=_SLOPE)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.28, 2.24))


def _cap(front):
    return NOSE if front else TAIL


def tip_at(v, front=True):
    return _cap(front).tip_at(v)


def cap_point(w, v, front=True):
    return _cap(front).point(w, v)


def cap_normal(w, v, front=True, h=2.5e-3):
    return _cap(front).normal(w, v, h)


def cap_offset(w, v, dist, front=True):
    return _cap(front).offset(w, v, dist)


def v_at_cap_z(z, front=True, w=0.0, iters=30):
    return _cap(front).v_at_z(z, w, iters)


def cap_wv_at(y, z, front=True, passes=5):
    return _cap(front).wv_at(y, z, passes)


def cap_x_at(y, z, front=True):
    return _cap(front).x_at(y, z)


def cap_half_width(z, front=True):
    return _cap(front).half_width(z)


def dims_report():
    return BODY.dims_report()
