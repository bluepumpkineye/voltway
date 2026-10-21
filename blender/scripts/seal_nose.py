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
    (0.8200, 2.0750), (0.9100, 2.1350), (1.0000, 2.1850),
])

JOIN_R = Curve([
    (0.0000, -2.0600), (0.1000, -2.0350), (0.2200, -1.9900), (0.3400, -1.9550),
    (0.4600, -1.9300), (0.5600, -1.9250), (0.6600, -1.9420), (0.7600, -1.9800),
    (0.8600, -2.0350), (0.9400, -2.0850), (1.0000, -2.1200),
])

# Centreline profiles, x given z
# Front Ocean X shark-nose prow reaches x = +2.4000 m at z = 0.5450 m with dramatic lower undercut
NOSE_X_OF_Z = Curve([
    (0.1380, 2.2350), (0.2050, 2.2750), (0.3000, 2.3180), (0.3950, 2.3680),
    (0.4750, 2.3920), (0.5450, 2.4000), (0.6000, 2.3860), (0.6400, 2.3560),
    (0.6700, 2.3180), (0.6860, 2.2820),
], mode="pchip")
NOSE_Z_LO, NOSE_Z_HI = 0.1380, 0.6860

# Rear profile reaches x = -2.4000 m at ducktail (z = 0.9550..0.9680 m) and through-type tail lamp
TAIL_X_OF_Z = Curve([
    (0.1520, -2.1950), (0.2300, -2.2400), (0.3250, -2.2850), (0.4200, -2.3250),
    (0.5350, -2.3580), (0.6500, -2.3820), (0.7700, -2.3960), (0.8850, -2.3980),
    (0.9550, -2.4000), (0.9680, -2.3950),
], mode="pchip")
TAIL_Z_LO, TAIL_Z_HI = 0.1520, 0.9680

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
