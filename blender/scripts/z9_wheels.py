"""Denza Z9 wheels: the 21-inch machined multi-spoke (255/40 R21 front, 275/40 R21 rear), traced from the black
car's side photograph (blender/reference/denza-z9/exterior/c1_0036.jpg; rear wheel, ellipse ratio 0.98 at
(2940.5, 2043.4) px, the axle corrected -9, -1 px: scripts/wheel-trace, memory wheel-tracing-method).

What the wheel is: five repeats of a face of silver blades with twenty open slots between them (the brake disc and
caliper show through): in each 72 degrees two V-shaped slots either side of a slender spoke (they narrow from the
rim to the hub), a wide blade, two straight slots either side of a second slender spoke, and a second wide blade;
a plain machined ring is the rim's flange, and a white roundel cap sits in the hub. The slots' outlines are read
off the voted mean picture of the five repeats (z9_wheels.WINDOWS: degrees counter-clockwise from 3 o'clock seen
from outside, radius / the lip radius of the photograph's own fitted circle).
"""
import math
from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_21 = 0.2785     # 21-inch rim lip radius (m): the photograph's fitted circle
TAB = 0.953         # the face's edge: outside it the machined flange ring

CALIPER = dict(
    span_deg=40.0, span_rear=34.0, r_inner=0.135, d_out=0.032, steps=16, groove=True
)

DISH = Curve([
    (0.000, 0.052), (0.080, 0.052), (0.110, 0.042), (0.150, 0.028),
    (0.200, 0.016), (0.245, 0.009), (0.278, 0.000),
], mode="pchip")

# the twenty slots, four per repeat: the V-shaped pair (narrowing toward the hub) and the straight pair; each
# slot's lower corners run on as a thin gap toward the hub boss (the dark lines that outline the blades)
WINDOWS = [
    # V pair
    [(2.5, 0.945), (3.25, 0.85), (4.0, 0.80), (4.9, 0.70), (5.6, 0.62), (6.1, 0.56), (6.7, 0.515), (7.6, 0.498),
     (8.4, 0.502), (8.9, 0.45), (8.6, 0.38), (8.3, 0.30), (9.3, 0.30), (9.7, 0.34), (10.2, 0.40), (10.6, 0.47),
     (10.4, 0.60), (11.1, 0.70), (11.75, 0.80), (12.25, 0.945)],
    [(14.25, 0.945), (14.5, 0.80), (15.0, 0.70), (15.6, 0.60), (15.9, 0.47), (16.3, 0.40), (16.8, 0.34), (17.2, 0.30),
     (18.2, 0.30), (17.9, 0.38), (17.9, 0.45), (18.25, 0.50), (19.0, 0.55), (19.75, 0.60), (21.0, 0.70),
     (22.0, 0.80), (23.5, 0.945)],
    # straight pair
    [(39.0, 0.945), (39.4, 0.80), (39.75, 0.60), (39.9, 0.52), (41.5, 0.41), (43.2, 0.30), (44.2, 0.30),
     (40.9, 0.505), (45.8, 0.505), (45.5, 0.30), (46.4, 0.30), (46.75, 0.52), (47.1, 0.60), (47.5, 0.80),
     (47.75, 0.945)],
    [(50.25, 0.945), (50.5, 0.80), (51.25, 0.60), (51.5, 0.52), (51.6, 0.30), (52.5, 0.30), (52.2, 0.505),
     (57.1, 0.505), (53.8, 0.30), (54.8, 0.30), (57.5, 0.41), (58.0, 0.60), (58.5, 0.80), (58.75, 0.945)],
]
WINDOWS = [[(a, min(r, TAB - 0.004)) for (a, r) in poly] for poly in WINDOWS]

SPEC_LUXURY = W.preset(
    "blade_5",
    rim_d=2.0 * LIP_21,
    dish=DISH,
    pinstripe=False,
    flange_face=(1.0 - TAB) * LIP_21,
    roll_left=math.pi,
    tyre=dict(bulge=1.042, shoulder=0.015, ridge=True),
    hub=dict(depth=0.052, setback=0.008, cap_rise=0.005, cap_r=0.034),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0100, deg=18.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.118, thickness=0.032),
    caliper=CALIPER,
    mats=dict(
        rim="wheel_silver",
        lip="machined",
        lugs="wheel_silver",
        cap="wheel_cap",
        disc="iron",
        barrel="black_gloss",
        accent="black_gloss",
    ),
)
SPEC_LUXURY["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0018, mat="wheel_silver",
    r_in=0.040, r_out=TAB * LIP_21, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=WINDOWS,
)

# ------------------------------------------------------------------------------------------ the 20 in six-Y
# The Pro and Max trims (Autohome series 7838, specs 69563 / 69564; 255/45 R20 V XL on the Continental EcoContact) wear a
# 20 in wheel with six bright machined Y spokes: each spoke is a pair of arms from the hub with a thin dark slit between them
# that opens into a V towards the rim, and a triangular window lies between one spoke and the next (the disc and the silver
# caliper show through). Traced from the REAR wheel of the black Pro's side photograph (imgs-7838-69563-1-x/10963307, ellipse
# ratio 0.985, axle corrected +2, -1 px, period 60.0 degrees by period.cjs); the two windows per repeat are the dark regions of
# segment.cjs (lum 135-255, invert=1), the V with its slit and the triangle between spokes.
LIP_20 = 0.2713     # 20-inch rim lip radius (m)
DISH_20 = Curve([
    (0.000, 0.048), (0.080, 0.048), (0.110, 0.039), (0.150, 0.026),
    (0.200, 0.015), (0.245, 0.007), (0.2713, 0.000),
], mode="pchip")
WIN_TRI = [(-3.3, 0.939), (-5.6, 0.937), (-6.3, 0.925), (-7.9, 0.745), (-9.6, 0.619), (-12.1, 0.484), (-14.8, 0.383),
           (-14.9, 0.344), (-13.6, 0.309), (-14.3, 0.291), (-13.8, 0.281), (-11.8, 0.274), (-9.9, 0.249), (-8.1, 0.232),
           (-1.1, 0.219), (8.2, 0.220), (10.4, 0.223), (14.4, 0.240), (15.7, 0.251), (16.9, 0.276), (18.8, 0.281),
           (19.8, 0.288), (18.9, 0.306), (19.7, 0.325), (20.3, 0.371), (19.7, 0.407), (16.8, 0.519), (15.3, 0.600),
           (12.9, 0.789), (11.7, 0.926), (11.3, 0.935), (10.8, 0.938)]
WIN_VEE = [(-29.1, 0.191), (-27.4, 0.194), (-23.5, 0.193), (-22.9, 0.206), (-21.9, 0.214), (-23.2, 0.270), (-21.8, 0.286),
           (-23.2, 0.305), (-23.8, 0.359), (-23.9, 0.412), (-22.9, 0.453), (-18.9, 0.526), (-16.6, 0.583), (-13.4, 0.698),
           (-11.2, 0.813), (-9.8, 0.914), (-10.1, 0.936), (-11.8, 0.938), (-39.4, 0.939), (-43.8, 0.938), (-44.4, 0.936),
           (-44.8, 0.929), (-43.2, 0.804), (-40.3, 0.666), (-37.0, 0.560), (-35.0, 0.512), (-31.6, 0.451), (-30.6, 0.415),
           (-31.2, 0.309), (-31.4, 0.301), (-32.3, 0.293), (-33.6, 0.286), (-31.7, 0.270), (-32.6, 0.226), (-32.3, 0.214),
           (-32.6, 0.203), (-30.4, 0.198)]
# the segmentation's wobble at the bottoms (the lug-nut shadows): the windows stop at the hub's ring
WIN_TRI = [(a, min(r, TAB - 0.004)) for (a, r) in WIN_TRI]
WIN_VEE = [(a, min(r, TAB - 0.004)) for (a, r) in WIN_VEE]

SPEC_PRO20 = W.preset(
    "blade_5",
    rim_d=2.0 * LIP_20,
    dish=DISH_20,
    pinstripe=False,
    flange_face=(1.0 - TAB) * LIP_20,
    roll_left=math.pi,
    tyre=dict(bulge=1.042, shoulder=0.015, ridge=True),
    hub=dict(depth=0.048, setback=0.008, cap_rise=0.005, cap_r=0.040),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0100, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.118, thickness=0.032),
    caliper=CALIPER,
    mats=dict(
        rim="wheel_black",
        lip="machined",
        lugs="wheel_black",
        cap="wheel_cap",
        disc="iron",
        barrel="wheel_black",
        accent="wheel_black",
    ),
)
SPEC_PRO20["spokes"] = dict(
    style="traced", count=6, phase=0.0, depth=0.016, bevel=0.0016, mat="machined",
    r_in=0.040, r_out=TAB * LIP_20, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=[WIN_TRI, WIN_VEE],
)
SPEC_PRO20["tyre_w"] = (0.255, 0.255)

DESIGNS = {
    "luxury": ("DenzaZ9_", SPEC_LUXURY),
    "pro20": ("DenzaZ9_Pro_", SPEC_PRO20),
}
DEFAULT = "luxury"


def corners(surface, tyre_w=(0.255, 0.275)):
    """The 4 corners of the Denza Z9: the 21 in cars are staggered, 255 mm front, 275 mm rear (tyre_w = front, rear);
    the outer sidewall stays where it was (track / 2 + 0.118 and + 0.125)."""
    r = surface.WHEEL_R
    wf, wr = tyre_w
    return [
        ("FL", surface.FRONT_AXLE,  1, wf, r, 0.195, 176.0, surface.TRACK_F / 2.0 + 0.118),
        ("FR", surface.FRONT_AXLE, -1, wf, r, 0.195, 184.0, surface.TRACK_F / 2.0 + 0.118),
        ("RL", surface.REAR_AXLE,   1, wr, r, 0.185, 176.0, surface.TRACK_R / 2.0 + 0.125),
        ("RR", surface.REAR_AXLE,  -1, wr, r, 0.185, 184.0, surface.TRACK_R / 2.0 + 0.125),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface, spec.get("tyre_w", (0.255, 0.275))))


def build_all(collection, surface, lib):
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
