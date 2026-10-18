"""Avatr 06T wheels: the complete 20" and 21" wheel/rim range of the production car,
derived from Autohome specifications and official Avatr configuration options.

    twin5      20 in: 5-twin-spoke, five spokes each split into two fingers by a thin
               slot, diamond-cut machined face over gloss black pockets; 255/45 R20
    aero       20 in: Aero Blade low-drag aerodynamic wheel, enclosed face with five
               swept directional turbine vents for optimal drag efficiency; 255/50 R20
    cyclone    21 in: Cyclone 5-spoke sport wheel, swept directional whirlwind blades
               with machined aerodynamic leading face and gloss black flank; 265/45 R21
    multi      21 in: Radiant multi-spoke sport wheel, 15 fine radiating turbine beams
               with machined face and deep ventilated barrel; 265/45 R21

Build only the default (build_all) for the car; the other three are built for
the export (build_options) and swapped in the showroom configurator.
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

# ------------------------------------------------------------------ sizes
LIP_20 = 0.2713      # 20 in rim flange radius (m), tyre loaded radius 0.369 m
LIP_21 = 0.2840      # 21 in rim flange radius (m), tyre loaded radius 0.375 m

CALIPER = dict(span_deg=43.0, span_rear=39.0, r_inner=0.14, d_out=0.034, steps=16)

DISH = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
              (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0110), (0.250, 0.0045),
              (0.2713, 0.0)], mode="pchip")
DISH_21 = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                 (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0110), (0.250, 0.0040),
                 (0.2840, 0.0)], mode="pchip")
TAB = 0.965

# ------------------------------------------------------------------ 1. twin5 (20 in)
WIN_BIG = [
    (106.5, 0.26), (105.5, 0.44), (104.5, 0.65), (105.5, 0.84), (109.0, 0.92), (126.0, 0.93),
    (143.0, 0.92), (146.5, 0.84), (147.5, 0.65), (146.5, 0.44), (145.5, 0.26), (126.0, 0.24),
]
WIN_SLOT = [
    (88.0, 0.30), (88.2, 0.55), (88.5, 0.78), (88.8, 0.92),
    (91.2, 0.92), (91.5, 0.78), (91.8, 0.55), (92.0, 0.30),
    (90.0, 0.26),
]
INLAY_L = [(77.5, 0.96), (77.5, 0.32), (86.5, 0.32), (86.5, 0.96)]
INLAY_R = [(93.5, 0.96), (93.5, 0.32), (102.5, 0.32), (102.5, 0.96)]

SPEC_TWIN5 = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron"))
SPEC_TWIN5["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="black_gloss",
    r_in=0.034, r_out=TAB * LIP_20, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[WIN_BIG, WIN_SLOT],
    inlay=dict(mat="machined", polys=[INLAY_L, INLAY_R], lift=0.0004))

# ------------------------------------------------------------------ 2. aero (20 in)
SPEC_AERO = W.preset(
    "aero_5window", rim_d=2.0 * LIP_20, dish=DISH, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    spokes=dict(style="aero", count=5, phase=0.0, depth=0.012, bevel=0.0018,
                params=dict(r_in=0.065, r_win0=0.125, r_win1=0.235, half_angle=0.28, corner=0.35)),
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss", disc="iron"))

# ------------------------------------------------------------------ 3. cyclone (21 in)
SPEC_CYCLONE = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    spokes=dict(style="blade", count=5, phase=math.pi / 2.0, depth=0.032, bevel=0.0022,
                params=dict(r_hub=0.096, r_rim=0.270, w_hub=0.055, w_rim=0.118, twist=0.22, split=0.55),
                face_mat="machined"),
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss", disc="iron"))

# ------------------------------------------------------------------ 4. multi (21 in)
SPEC_MULTI = W.preset(
    "multi_10", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    spokes=dict(style="straight", count=15, phase=math.pi / 2.0, depth=0.026, bevel=0.0020,
                params=dict(r_hub=0.096, r_rim=0.272, w_hub=0.016, w_rim=0.012)),
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss", disc="iron"))

# ------------------------------------------------------------------ the set
DESIGNS = {
    "twin5": ("A06T_", SPEC_TWIN5),
    "aero": ("A06T_Aero_", SPEC_AERO),
    "cyclone": ("A06T_Cyclone_", SPEC_CYCLONE),
    "multi": ("A06T_Multi_", SPEC_MULTI),
}
DEFAULT = "twin5"


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius, caliper deg,
    # outer sidewall y (track/2 + tyre width/2: 1676/1680 mm track, 255 mm tyres)
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.255, 0.369, 0.190, 176.0, 0.9655),
        ("FR", surface.FRONT_AXLE, -1, 0.255, 0.369, 0.190, 184.0, 0.9655),
        ("RL", surface.REAR_AXLE, 1, 0.255, 0.369, 0.180, 176.0, 0.9675),
        ("RR", surface.REAR_AXLE, -1, 0.255, 0.369, 0.180, 184.0, 0.9675),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    """The car's own wheels: the default design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    """The other designs, on top of the first: for export."""
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
