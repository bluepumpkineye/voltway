"""Denza Z9 nose and tail caps - the curves of its two WrapCaps.

The cap maths lives in carkit.body.caps (WrapCap).
Denza Z9 dimensions: 5220 x 1990 x 1500 mm, Wheelbase 3125 mm.
"""
import z9_surface as S
from carkit.geom import Curve
from carkit.body import WrapCap, CarBody

# ---------------------------------------------------------------- shut lines
JOIN_F = Curve([
    (0.0000, 2.2953), (0.0800, 2.2717), (0.1800, 2.2263), (0.3000, 2.1751),
    (0.4200, 2.1416), (0.5200, 2.1338), (0.6200, 2.1554), (0.7200, 2.2047),
    (0.8200, 2.2697), (0.9100, 2.3367), (1.0000, 2.3780),
])

JOIN_R = Curve([
    (0.0000, -2.2660), (0.1000, -2.2402), (0.2200, -2.1944), (0.3400, -2.1565),
    (0.4600, -2.1327), (0.5600, -2.1287), (0.6600, -2.1466), (0.7600, -2.1864),
    (0.8600, -2.2402), (0.9400, -2.2919), (1.0000, -2.3218),
])

# Centreline profiles, x given z (calibrated to Attachment 1 side view & Attachment 4 rear view)
# Front prow reaches x = +2.6220 m at z = 0.5850 m with sleek, sharp forward-pointing shark prow
NOSE_X_OF_Z = Curve([
    (0.1433, 2.4100), (0.2200, 2.4600), (0.3200, 2.5200), (0.4200, 2.5750),
    (0.5000, 2.6050), (0.5850, 2.6220), (0.6400, 2.6020), (0.6800, 2.5650),
    (0.7100, 2.5200), (0.7300, 2.4750),
], mode="pchip")
NOSE_Z_LO, NOSE_Z_HI = 0.1433, 0.7300

# Rear profile reaches x = -2.6100 m at ducktail (z = 0.995..1.008 m) and taillight (z = 0.805 m),
# and smoothly rounds forward and down to x = -2.4000 m at z = 0.1600 m
TAIL_X_OF_Z = Curve([
    (0.1600, -2.4000), (0.2400, -2.4450), (0.3400, -2.4850), (0.4400, -2.5250),
    (0.5600, -2.5600), (0.6800, -2.5850), (0.8050, -2.6080), (0.9200, -2.6050),
    (0.9950, -2.6100), (1.0080, -2.6050),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.1600, 1.0080

# ------------------------------------------------------------- wrap blending
WRAP = Curve([
    (0.0000, 0.0000), (0.1500, 0.0450), (0.3000, 0.1250), (0.4500, 0.2450),
    (0.6000, 0.3850), (0.7200, 0.5100), (0.8200, 0.6300), (0.9000, 0.7500),
    (0.9600, 0.8800), (1.0000, 1.0000),
])

TAIL_WRAP = Curve([
    (0.0000, 0.0000), (0.1500, 0.0550), (0.3000, 0.1550), (0.4500, 0.2850),
    (0.6000, 0.4350), (0.7200, 0.5750), (0.8200, 0.7000), (0.9000, 0.8150),
    (0.9600, 0.9200), (1.0000, 1.0000),
])

_SLOPE = {}
NOSE = WrapCap(S.BODY, front=True, join=JOIN_F, x_of_z=NOSE_X_OF_Z,
               z_lo=NOSE_Z_LO, z_hi=NOSE_Z_HI, wrap=WRAP, slope_cache=_SLOPE)
TAIL = WrapCap(S.BODY, front=False, join=JOIN_R, x_of_z=TAIL_X_OF_Z,
               z_lo=TAIL_Z_LO, z_hi=TAIL_Z_HI, wrap=TAIL_WRAP, slope_cache=_SLOPE)
BODY = CarBody(S.BODY, NOSE, TAIL, flank_x_range=(-2.50, 2.45))


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
