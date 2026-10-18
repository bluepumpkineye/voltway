"""Nio ES8 wheels: the complete official and Autohome wheel range for the all-new ES8 (NT2 platform):

    lanyue   22" Lanyue Forged High-Gloss Diamond-Cut (265/40 R22) - Flagship 10-twin-spoke forged wheel
             with machined face, gloss black pockets, and always-upright floating centre cap. (Default)
    sail     20" 7-Spoke Star Sail Aero (255/50 R20) - Aerodynamic 7-blade sail design with low-drag cutouts.
             Standard executive wheel.
    glow     21" Multi-Spoke Star Glow (265/45 R21) - 15-spoke fine radial turbine executive wheel with
             machined silver face over dark grey barrel.
    carbon   21" Carbon Blade Star Edge (265/45 R21) - 5-split Y-spoke sport wheel with aerodynamic blade inserts.
    shine    22" Forged Star Shine Diamond-Cut (265/40 R22) - 10-spoke forged luxury wheel with sharp
             diamond-cut face contrast over deep gloss black.

Brakes: Brembo 6-piston front calipers (Air Glow Orange, Silver Grey, or Competition Red) with ventilated discs.
References: Autohome ES8 specification series 3954, NIO official ES8 configurator.
"""
import copy
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_20 = 0.2713                 # 20-inch rim lip radius (m) for 255/50 R20 (OD ~0.763 m)
LIP_21 = 0.2840                 # 21-inch rim lip radius (m) for 265/45 R21 (OD ~0.772 m)
LIP_22 = 0.2985                 # 22-inch rim lip radius (m) for 265/40 R22 (OD ~0.770 m)
TAB_22 = 0.962                  # outer machined flange ring boundary on 22" Lanyue

CALIPER = dict(span_deg=42.0, span_rear=36.0, r_inner=0.148, d_out=0.035, steps=16)

# Dishes (face depth below flange plane by radius)
DISH_22 = Curve([
    (0.000, 0.0580), (0.085, 0.0580), (0.115, 0.0520), (0.150, 0.0400),
    (0.190, 0.0270), (0.230, 0.0155), (0.265, 0.0065), (0.290, 0.0018),
    (LIP_22, 0.0),
], mode="pchip")

DISH_21 = Curve([
    (0.000, 0.0480), (0.085, 0.0480), (0.120, 0.0360), (0.170, 0.0220),
    (0.220, 0.0110), (0.265, 0.0030), (LIP_21, 0.0),
], mode="pchip")

DISH_20 = Curve([
    (0.000, 0.0380), (0.080, 0.0380), (0.120, 0.0280), (0.170, 0.0160),
    (0.220, 0.0080), (0.255, 0.0020), (LIP_20, 0.0),
], mode="pchip")


def _sym(axis, rows):
    left = [(axis - hw, r) for (r, hw) in rows]
    right = [(axis + hw, r) for (r, hw) in reversed(rows)]
    return left + right


# ========================================================================= 1. 22" Lanyue
WIN_NARROW = _sym(0.0, [
    (0.350, 3.2), (0.420, 3.8), (0.550, 4.4), (0.700, 4.8),
    (0.840, 5.0), (0.925, 4.6), (0.946, 3.8),
])

WIN_WIDE = _sym(18.0, [
    (0.295, 4.6), (0.360, 5.6), (0.480, 6.4), (0.640, 6.9),
    (0.800, 7.2), (0.915, 6.8), (0.948, 5.6),
])


def _twin_bars():
    bars = []
    for sgn in (-1.0, 1.0):
        c = sgn * 8.9
        bars.append(_sym(c, [
            (0.265, 2.8), (0.350, 2.6), (0.550, 2.3),
            (0.780, 2.1), (0.955, 2.4), (0.985, 2.8),
        ]))
    return bars


SPEC_LANYUE = W.preset(
    "blade_5", rim_d=2.0 * LIP_22, dish=DISH_22, pinstripe=False,
    flange_face=(1.0 - TAB_22) * LIP_22, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0580, setback=0.008, cap_rise=0.0055, cap_r=0.036),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss", accent="machined"),
)
SPEC_LANYUE["spokes"] = dict(
    style="traced", count=10, phase=0.0, depth=0.016, bevel=0.0016, mat="black_gloss",
    r_in=0.038, r_out=TAB_22 * LIP_22, nr=16, seg=80, step_deg=1.5, step_r=0.025,
    windows=[WIN_NARROW, WIN_WIDE],
    inlay=dict(mat="machined", polys=_twin_bars(), lift=0.0005),
)
SPEC_LANYUE["tyre_w"] = 0.265


# ========================================================================= 2. 20" Star Sail Aero
SPEC_SAIL = W.preset(
    "aero_5window", rim_d=2.0 * LIP_20, dish=DISH_20, pinstripe=False,
    flange_face=0.011, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018),
    hub=dict(depth=0.038, setback=0.006, cap_rise=0.004, cap_r=0.034),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="dark_grey", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="dark_grey", accent="machined"),
)
SPEC_SAIL["spokes"] = dict(
    style="aero", count=7, phase=math.pi / 7.0, depth=0.012, bevel=0.0016,
    mat="dark_grey",
    params=dict(r_in=0.068, r_win0=0.130, r_win1=0.230, half_angle=0.22, corner=0.25),
)
SPEC_SAIL["tyre_w"] = 0.255


# ========================================================================= 3. 21" Multi-Spoke Star Glow
SPEC_GLOW = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False,
    flange_face=0.010, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.048, setback=0.006, cap_rise=0.004, cap_r=0.035),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="dark_grey", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="dark_grey", accent="machined"),
)
SPEC_GLOW["spokes"] = dict(
    style="straight", count=15, phase=0.0, depth=0.020, bevel=0.0018,
    mat="dark_grey", face_mat="machined",
    params=dict(r_hub=0.088, r_rim=0.265, w_hub=0.016, w_rim=0.012, twist=0.0),
)
SPEC_GLOW["tyre_w"] = 0.265


# ========================================================================= 4. 21" Carbon Blade Star Edge
SPEC_CARBON = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False,
    flange_face=0.010, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.050, setback=0.006, cap_rise=0.004, cap_r=0.035),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss", accent="machined"),
)
SPEC_CARBON["spokes"] = dict(
    style="split_y", count=5, phase=math.pi / 2.0, depth=0.024, bevel=0.0022,
    mat="black_gloss", face_mat="machined",
    params=dict(r_hub=0.092, r_split=0.160, r_rim=0.268, spread=0.18, w_stem=0.038, w_leg=0.018),
)
SPEC_CARBON["tyre_w"] = 0.265


# ========================================================================= 5. 22" Forged Star Shine
SPEC_SHINE = W.preset(
    "blade_5", rim_d=2.0 * LIP_22, dish=DISH_22, pinstripe=False,
    flange_face=0.010, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.056, setback=0.008, cap_rise=0.005, cap_r=0.036),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss", accent="machined"),
)
SPEC_SHINE["spokes"] = dict(
    style="straight", count=10, phase=0.0, depth=0.022, bevel=0.0020,
    mat="black_gloss", face_mat="machined",
    params=dict(r_hub=0.094, r_rim=0.282, w_hub=0.025, w_rim=0.018, twist=0.0),
)
SPEC_SHINE["tyre_w"] = 0.265


# Map internal design ID -> (object prefix, spec dict)
DESIGNS = {
    "lanyue": ("ES8_", SPEC_LANYUE),
    "sail":   ("ES8_Sail_", SPEC_SAIL),
    "glow":   ("ES8_Glow_", SPEC_GLOW),
    "carbon": ("ES8_Carbon_", SPEC_CARBON),
    "shine":  ("ES8_Shine_", SPEC_SHINE),
}
DEFAULT = "lanyue"
SPEC = SPEC_LANYUE


def corners(surface, tyre_w=0.265):
    """4 wheel corners (FL, FR, RL, RR) with ES8 track and axle positions."""
    r = surface.WHEEL_R
    outer_f = surface.TRACK_F / 2.0 + tyre_w / 2.0
    outer_r = surface.TRACK_R / 2.0 + tyre_w / 2.0
    return [
        ("FL", surface.FRONT_AXLE,  1, tyre_w, r, 0.192, 176.0, outer_f),
        ("FR", surface.FRONT_AXLE, -1, tyre_w, r, 0.192, 184.0, outer_f),
        ("RL", surface.REAR_AXLE,   1, tyre_w, r, 0.182, 176.0, outer_r),
        ("RR", surface.REAR_AXLE,  -1, tyre_w, r, 0.182, 184.0, outer_r),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    tyre_w = spec.get("tyre_w", 0.265)
    return W.build_set(collection, prefix, lib, spec, corners(surface, tyre_w=tyre_w))


def build_all(collection, surface, lib):
    """Build the car's default wheels."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    """Build every non-default wheel design into the collection for multi-wheel export."""
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
