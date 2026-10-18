"""Nio ES8 wheels: 22-inch 10-twin-spoke forged luxury wheel (265/40 R22) with
Brembo 6-piston front calipers and ventilated brake discs.

Reference: blender/reference/nio-es8/official/color_grey.jpg, ext_side.jpg, lanyue_wheel.jpg
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP = 0.2985                    # 22-inch rim lip radius (m) for 265/40 R22 (OD 0.770 m)
TAB = 0.962                     # outer machined flange ring boundary

CALIPER = dict(span_deg=42.0, span_rear=36.0, r_inner=0.148, d_out=0.035, steps=16)

DISH = Curve([
    (0.000, 0.0580), (0.085, 0.0580), (0.115, 0.0520), (0.150, 0.0400),
    (0.190, 0.0270), (0.230, 0.0155), (0.265, 0.0065), (0.290, 0.0018),
    (0.2985, 0.0),
], mode="pchip")


def _sym(axis, rows):
    left = [(axis - hw, r) for (r, hw) in rows]
    right = [(axis + hw, r) for (r, hw) in reversed(rows)]
    return left + right


# 10-fold repeat (36 deg period):
# - Axis 0 deg: narrow V-window inside each twin-spoke pair (r = 0.34..0.945)
# - Axis 18 deg: wider U-window between adjacent twin-spoke pairs (r = 0.29..0.948)
WIN_NARROW = _sym(0.0, [
    (0.350, 3.2), (0.420, 3.8), (0.550, 4.4), (0.700, 4.8),
    (0.840, 5.0), (0.925, 4.6), (0.946, 3.8),
])

WIN_WIDE = _sym(18.0, [
    (0.295, 4.6), (0.360, 5.6), (0.480, 6.4), (0.640, 6.9),
    (0.800, 7.2), (0.915, 6.8), (0.948, 5.6),
])

# Machined face bars on the two arms of each twin spoke (centred at ±9 deg around axis 0)
def _twin_bars():
    bars = []
    for sgn in (-1.0, 1.0):
        c = sgn * 8.9
        bars.append(_sym(c, [
            (0.265, 2.8), (0.350, 2.6), (0.550, 2.3),
            (0.780, 2.1), (0.955, 2.4), (0.985, 2.8),
        ]))
    return bars


SPEC_STAR = W.preset(
    "blade_5", rim_d=2.0 * LIP, dish=DISH, pinstripe=False,
    flange_face=(1.0 - TAB) * LIP, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0580, setback=0.008, cap_rise=0.0055, cap_r=0.036),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss", accent="machined"),
)
SPEC_STAR["spokes"] = dict(
    style="traced", count=10, phase=0.0, depth=0.016, bevel=0.0016, mat="black_gloss",
    r_in=0.038, r_out=TAB * LIP, nr=16, seg=80, step_deg=1.5, step_r=0.025,
    windows=[WIN_NARROW, WIN_WIDE],
    inlay=dict(mat="machined", polys=_twin_bars(), lift=0.0005),
)

SPEC = SPEC_STAR
DESIGNS = {
    "star": ("ES8_", SPEC_STAR),
}
DEFAULT = "star"


def corners(surface):
    """4 wheel corners (FL, FR, RL, RR) with ES8 track and axle positions."""
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE,  1, 0.265, r, 0.192, 176.0, surface.TRACK_F / 2.0 + 0.1325),
        ("FR", surface.FRONT_AXLE, -1, 0.265, r, 0.192, 184.0, surface.TRACK_F / 2.0 + 0.1325),
        ("RL", surface.REAR_AXLE,   1, 0.265, r, 0.182, 176.0, surface.TRACK_R / 2.0 + 0.1325),
        ("RR", surface.REAR_AXLE,  -1, 0.265, r, 0.182, 184.0, surface.TRACK_R / 2.0 + 0.1325),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
