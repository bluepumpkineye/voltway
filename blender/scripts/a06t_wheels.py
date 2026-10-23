"""Avatr 06T wheels. The default is the wheel the car is photographed on (Autohome series 8538, the
studio turntable set), traced from the REAR wheel of c1_0004.jpg (circle-corrected: the lip's best
fit at (2847.1, 2024.9) px, radius 184.8 px = 0.2713 m at the wheelbase scale; five repeats, 71.25
degrees by period.cjs). The other three designs are earlier stand-ins that no photograph backs.

    turbine5   20 in: a five-blade turbine. Black face; five long open windows of constant width
               (0.32 R) that sweep in from the rim, each outlined in machined silver (an inverted U:
               the blade's leading edge, the rim band across its top, the trailing edge); a thin
               machined line on each spoke; the disc and caliper show through the windows. 255/45 R20
    aero       20 in: Aero Blade low-drag wheel (stand-in)
    cyclone    21 in: Cyclone 5-spoke (stand-in)
    multi      21 in: Radiant multi-spoke (stand-in)

Polygons are (angle in degrees counter-clockwise from 3 o'clock, seen from outside, radius / lip radius).
Build only the default (build_all) for the car; the other three are built for the export
(build_options) and swapped in the showroom configurator.
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

# ------------------------------------------------------------------ sizes
LIP_20 = 0.2713      # 20 in rim flange radius (m), tyre loaded radius 0.369 m
LIP_21 = 0.2840      # 21 in rim flange radius (m), tyre loaded radius 0.375 m

CALIPER = dict(span_deg=43.0, span_rear=39.0, r_inner=0.14, d_out=0.034, steps=16)

DISH = Curve([(0.000, 0.0560), (0.090, 0.0560), (0.105, 0.0510), (0.130, 0.0390),
              (0.160, 0.0260), (0.190, 0.0160), (0.220, 0.0085), (0.250, 0.0035),
              (0.2713, 0.0)], mode="pchip")
DISH_21 = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                 (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0110), (0.250, 0.0040),
                 (0.2840, 0.0)], mode="pchip")
TAB = 0.965

# ------------------------------------------------------------------ 1. turbine5 (20 in)
# One window: between the blade's leading edge A (left) and trailing edge B (right, the next repeat's
# B = +72), under the rim band at r 0.94, closed at the hub ring r 0.31.
_A_CENTRE = [(58.5, 0.950), (57.0, 0.833), (55.2, 0.722), (53.0, 0.633), (50.5, 0.533), (47.0, 0.444),
             (42.0, 0.367), (36.0, 0.306), (28.0, 0.256), (20.0, 0.222), (11.0, 0.202)]
_B_CENTRE = [(80.5, 0.950), (80.8, 0.911), (82.0, 0.811), (83.5, 0.722), (85.5, 0.633), (88.0, 0.556),
             (91.0, 0.478), (94.5, 0.417), (98.5, 0.372), (102.0, 0.344)]
HW_A, HW_B = 1.6, 1.5          # half-widths of the machined bands, degrees


def _shift(pts, dth):
    return [(a + dth, r) for (a, r) in pts]


# window outline: A's right edge down, the hub ring across, B's left edge up, the rim band back
WIN_BIG = (_shift(_A_CENTRE[:8], HW_A + 0.1)
           + [(50.0, 0.314), (70.0, 0.318), (90.0, 0.332)]
           + list(reversed(_shift(_B_CENTRE, -HW_B))) + [(70.0, 0.940)])
# the machined inverted U: A (long, spiralling to the hub), the rim band, B
INLAY_U = (list(reversed(_shift(_A_CENTRE, -HW_A)))                 # A's left edge, hub -> rim
           + [(56.9, 0.995), (65.0, 0.997), (75.0, 0.997), (82.3, 0.995)]   # the rim band's outer edge
           + _shift(_B_CENTRE[1:], HW_B) + [(102.5, 0.335)]               # B's right edge, rim -> hub
           + list(reversed(_shift(_B_CENTRE, -HW_B)))                      # B's left edge, hub -> rim
           + [(79.0, 0.944), (70.0, 0.944)]                                # the band's lower edge
           + _shift(_A_CENTRE, HW_A) + [(10.0, 0.190)])                    # A's right edge, rim -> hub
# the thin machined line on each spoke
_C_CENTRE = [(41.0, 0.989), (42.8, 0.889), (44.5, 0.778), (46.3, 0.678), (47.2, 0.611)]
INLAY_C = (_shift(_C_CENTRE, -0.7) + [(47.2, 0.598)] + list(reversed(_shift(_C_CENTRE, 0.7))))

SPEC_TURBINE5 = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0560, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="graphite", lugs="black_gloss", cap="black_gloss",
              disc="iron"))
SPEC_TURBINE5["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0018, mat="black_gloss",
    r_in=0.034, r_out=0.995 * LIP_20, nr=18, seg=72, step_deg=2.0, step_r=0.025,
    windows=[WIN_BIG],
    inlay=dict(mat="machined", polys=[INLAY_U, INLAY_C], lift=0.0004))

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
    "turbine5": ("A06T_", SPEC_TURBINE5),
    "aero": ("A06T_Aero_", SPEC_AERO),
    "cyclone": ("A06T_Cyclone_", SPEC_CYCLONE),
    "multi": ("A06T_Multi_", SPEC_MULTI),
}
DEFAULT = "turbine5"


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius, caliper deg,
    # outer sidewall y, less the tyre's 7 mm bulge: the photographs' tyre walls are at 0.9655 / 0.9675
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.255, 0.369, 0.190, 176.0, 0.9585),
        ("FR", surface.FRONT_AXLE, -1, 0.255, 0.369, 0.190, 184.0, 0.9585),
        ("RL", surface.REAR_AXLE, 1, 0.255, 0.369, 0.180, 176.0, 0.9605),
        ("RR", surface.REAR_AXLE, -1, 0.255, 0.369, 0.180, 184.0, 0.9605),
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
