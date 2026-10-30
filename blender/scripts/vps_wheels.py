"""Voyah Passion S (岚图追光S) wheels: both official 21-inch wheel options on 255/50 R21 tyres.

  feichi      21英寸飞驰轮毂 (default studio turnaround car, c1_0004 / c12_0029):
              forged 5-U/Y-twin-spoke wheel in satin gunmetal over Voyah amber-yellow calipers
  starlight   21英寸星芒黑曜轮毂 (standard wheel, c1_0107):
              gloss obsidian black 15-blade (5 twin + 5 spear) starburst wheel

In carkit.parts.wheels, local 0 deg maps to world +X (forward of the axle). Left wheels have
Rx(-90) so local -deg (360 - deg) tilts UP; right wheels have Rx(+90) so local +deg tilts UP.
Passion S mounts both front and rear calipers AHEAD of the axles (~10 deg above horizontal front,
~6 deg above horizontal rear -> FL 350.0, FR 10.0, RL 354.0, RR 6.0).
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_21 = 0.2840

CALIPER = dict(span_deg=42.0, span_rear=36.0, r_inner=0.138, d_out=0.035, steps=16, groove=True)

DISH_21 = Curve([
    (0.000, 0.0680), (0.088, 0.0680), (0.105, 0.0610), (0.132, 0.0450),
    (0.162, 0.0290), (0.195, 0.0165), (0.228, 0.0080), (0.258, 0.0025),
    (0.2840, 0.0),
], mode="pchip")

# ------------------------------------------------------------------ 1. Feichi 21" (飞驰轮毂)
# Traced off feichi_face_fit2.png: 5 lug bolts at 20.5 deg (+72*k); each 72-deg sector has a
# wide U-window (36.5..76.5 deg) and a narrow split-Y V-window (82.8..102.2 deg) over the 92.5-deg lug.
FEICHI_TAB = 0.968
FEICHI_WINDOWS = [
    # Wide forged U-window between adjacent Y-spoke pairs
    [
        (35.8, 0.922), (39.8, 0.930), (56.5, 0.932), (73.2, 0.930), (77.2, 0.922),
        (77.8, 0.850), (77.0, 0.740), (75.6, 0.620), (73.5, 0.500), (70.8, 0.390),
        (67.2, 0.302), (62.0, 0.252), (56.5, 0.240), (51.0, 0.252), (45.8, 0.302),
        (42.2, 0.390), (39.5, 0.500), (37.4, 0.620), (36.0, 0.740), (35.2, 0.850),
    ],
    # Narrow split-Y V-window centred at 92.5 deg above the lug pocket
    [
        (82.0, 0.930), (85.5, 0.936), (99.5, 0.936), (103.0, 0.930),
        (102.8, 0.830), (101.6, 0.710), (100.0, 0.585), (97.9, 0.465),
        (95.4, 0.376), (92.5, 0.355), (89.6, 0.376), (87.1, 0.465),
        (85.0, 0.585), (83.4, 0.710), (82.2, 0.830),
    ],
]

SPEC_FEICHI = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False,
    flange_face=(1.0 - FEICHI_TAB) * LIP_21, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018),
    hub=dict(depth=0.0680, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=20.5, rise=0.004),
    disc=dict(style="plain", inner_r=0.118, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="gunmetal", lip="gunmetal", lugs="black_gloss", cap="gunmetal", disc="iron"),
)
SPEC_FEICHI["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.019, bevel=0.0022, mat="gunmetal",
    r_in=0.034, r_out=FEICHI_TAB * LIP_21, nr=16, seg=60, step_deg=2.4, step_r=0.03,
    windows=FEICHI_WINDOWS,
    lug_holes=dict(deg=20.5, pcd=0.05715, r=0.0165, count=5),
)

# ------------------------------------------------------------------ 2. Starlight Obsidian 21" (星芒黑曜轮毂)
# Traced off std_wheel_fit.png: 5 lug bolts at 54.0 deg (+72*k); 5 parallel twin-spoke pairs at 90 deg
# alternating with 5 sculpted spear spokes at 54 deg (15 blades total) in gloss obsidian black.
STAR_TAB = 0.970
STARLIGHT_WINDOWS = [
    # Narrow parallel slot between the twin spokes at 90.0 deg
    [
        (87.4, 0.942), (92.6, 0.942), (92.5, 0.780), (92.2, 0.600),
        (91.6, 0.450), (90.0, 0.405), (88.4, 0.450), (87.8, 0.600), (87.5, 0.780),
    ],
    # Left window between spear spoke (54 deg) and first twin spoke (85 deg)
    [
        (58.2, 0.940), (63.0, 0.946), (78.5, 0.946), (82.8, 0.940),
        (83.2, 0.820), (82.6, 0.660), (81.4, 0.500), (79.2, 0.375),
        (74.0, 0.335), (67.0, 0.338), (62.8, 0.390), (60.2, 0.520),
        (58.8, 0.680), (58.0, 0.820),
    ],
    # Right window between second twin spoke (95 deg) and next spear spoke (126 deg)
    [
        (97.2, 0.940), (101.5, 0.946), (117.0, 0.946), (121.8, 0.940),
        (122.0, 0.820), (121.2, 0.680), (119.8, 0.520), (117.2, 0.390),
        (113.0, 0.338), (106.0, 0.335), (100.8, 0.375), (98.6, 0.500),
        (97.4, 0.660), (96.8, 0.820),
    ],
]

SPEC_STARLIGHT = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_21, pinstripe=False,
    flange_face=(1.0 - STAR_TAB) * LIP_21, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018),
    hub=dict(depth=0.0680, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=54.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.118, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="obsidian", lip="obsidian", lugs="black_gloss", cap="obsidian", disc="iron"),
)
SPEC_STARLIGHT["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.019, bevel=0.0020, mat="obsidian",
    r_in=0.034, r_out=STAR_TAB * LIP_21, nr=16, seg=60, step_deg=2.4, step_r=0.03,
    windows=STARLIGHT_WINDOWS,
    lug_holes=dict(deg=54.0, pcd=0.05715, r=0.0165, count=5),
)

DESIGNS = {
    "feichi": ("VPS_", SPEC_FEICHI),
    "starlight": ("VPS_Starlight_", SPEC_STARLIGHT),
}
DEFAULT = "feichi"


def corners(surface):
    # 1720 mm front track, 1723 mm rear track, 255/50 R21 tyres (loaded radius 0.375 m)
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.255, surface.WHEEL_R, 0.192, 350.0, 0.9875),
        ("FR", surface.FRONT_AXLE, -1, 0.255, surface.WHEEL_R, 0.192, 10.0, 0.9875),
        ("RL", surface.REAR_AXLE, 1, 0.255, surface.WHEEL_R, 0.184, 354.0, 0.9890),
        ("RR", surface.REAR_AXLE, -1, 0.255, surface.WHEEL_R, 0.184, 6.0, 0.9890),
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
