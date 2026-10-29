"""BYD Seal 19-inch five-spoke "turbine" alloy wheels (235/45 R19 front and rear), traced from the blue
car's side photograph (blender/reference/byd-seal-ev/exterior/c1_0513.jpg, REAR wheel, ellipse ratio
0.986 at (2945.5, 2038.9) px, the axle corrected -2, -3 px; scripts/wheel-trace, memory wheel-tracing-method).

What the wheel is: five repeats of a pinwheel face. Each spoke is a narrow arm from the hub that widens
into a flat paddle; the paddle's leading edges are machined silver (a "boomerang": up the arm to
r 0.64, swinging back toward the rim, then along the rim as an L round the paddle's black ribbed panel),
the panels and arms are gloss black, and between the arms near the hub the brake disc shows through five
open pockets. A plain machined ring is the rim's flange; a black roundel cap sits in the hub. The silver
outlines are the voted mean of the five repeats (segment.cjs lum 140-255); the pockets are read off the
mean picture (angle degrees counter-clockwise from 3 o'clock seen from outside, radius / the lip radius).
"""
import math
from carkit.geom import Curve
from carkit.parts import wheels as W

LIP = 0.2633        # the rim lip radius (m): the photograph's lip circle against the tyre (0.768 of its radius)
TAB = 0.975         # the face's edge: outside it the machined flange ring

CALIPER = dict(
    span_deg=34.0, span_rear=28.0, r_inner=0.118, d_out=0.028, steps=16, groove=True
)

DISH = Curve([
    (0.000, 0.045), (0.070, 0.045), (0.095, 0.036), (0.135, 0.024),
    (0.180, 0.014), (0.220, 0.008), (0.2633, 0.000),
], mode="pchip")

# the open pockets between the arms near the hub (the disc and caliper show through)
WINDOWS = [
    [(31.0, 0.58), (45.0, 0.60), (60.0, 0.60), (75.0, 0.59), (86.0, 0.585),
     (87.0, 0.40), (80.0, 0.345), (60.0, 0.335), (40.0, 0.345), (31.0, 0.39)],
]

# the machined edges: the boomerang (arm, swing, L round the panel) and the rim-ring segment
SILVER_L = [(25.6, 0.978), (24.5, 0.976), (23.9, 0.965), (24.3, 0.748), (24.7, 0.734), (27.6, 0.705), (28.2, 0.704),
            (28.7, 0.710), (28.4, 0.843), (28.1, 0.854), (28.3, 0.881), (27.9, 0.887), (28.1, 0.934), (28.6, 0.948),
            (31.2, 0.947), (33.2, 0.948), (36.5, 0.949), (40.1, 0.949), (49.9, 0.952), (52.4, 0.935), (52.8, 0.921),
            (53.8, 0.915), (53.9, 0.904), (55.1, 0.895), (55.8, 0.887), (55.9, 0.880), (59.6, 0.835), (67.4, 0.766),
            (76.5, 0.710), (80.5, 0.693), (90.4, 0.663), (92.6, 0.650), (93.2, 0.634), (93.6, 0.581), (94.4, 0.205),
            (95.3, 0.190), (95.5, 0.178), (98.8, 0.179), (99.8, 0.193), (99.2, 0.300), (98.8, 0.568), (98.2, 0.642),
            (92.6, 0.690), (84.2, 0.711), (79.6, 0.727), (74.4, 0.750), (68.2, 0.788), (62.8, 0.834), (58.8, 0.875),
            (51.6, 0.974), (38.1, 0.973), (35.0, 0.977)]
SILVER_RING = [(-10.6, 0.964), (-9.6, 0.957), (-8.1, 0.956), (9.9, 0.959), (14.0, 0.959), (18.8, 0.959),
               (19.9, 0.953), (20.2, 0.967), (19.7, 0.978), (18.4, 0.979), (4.5, 0.979), (-9.5, 0.974), (-10.6, 0.971)]

SPEC_SEAL_TURBINE_5 = W.preset(
    "blade_5",
    rim_d=2.0 * LIP,
    flange=(0.118, 0.125, 0.50),
    flange_face=(1.0 - TAB) * LIP,
    dish=DISH,
    pinstripe=False,
    roll_left=math.pi,
    tyre=dict(bulge=1.035, shoulder=0.014, ridge=True),
    hub=dict(depth=0.045, setback=0.006, cap_rise=0.004, cap_r=0.030),
    lugs=dict(count=5, pcd_r=0.0520, r=0.0090, deg=18.0, rise=0.003),
    disc=dict(style="plain", inner_r=0.115, thickness=0.028),
    caliper=CALIPER,
    mats=dict(
        tyre="rubber",
        rim="wheel_black",
        lip="machined",
        lugs="wheel_silver",
        cap="wheel_cap",
        disc="iron",
        barrel="wheel_black",
        accent="wheel_black",
        caliper="caliper",
    ),
)
SPEC_SEAL_TURBINE_5["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0016, mat="wheel_black",
    r_in=0.040, r_out=TAB * LIP, nr=18, seg=72, step_deg=2.0, step_r=0.025,
    windows=WINDOWS,
    inlay=dict(mat="machined", polys=[SILVER_L, SILVER_RING], lift=0.0005),
)

# ------------------------------------------------------------------------------------------ the Performance's 19 in
# The 650 km four-wheel-drive Performance (Autohome spec 56593) wears a different 19 in wheel with yellow calipers: five
# black Y spokes, each forking into two arms to the rim, edged by a thin machined chamfer, over open windows that show the
# drilled disc and the caliper. Traced from the front wheel of its side photograph (imgs-6394-56593-1-x/8327314: ellipse
# ratio 0.987, axle corrected +1, +1 px, period 72.0 degrees). The windows are the dark regions between the chamfer lines
# (segment.cjs invert=1 on lum 105-255); the black face is the second layer, cut back from each window by the chamfer's
# width so the machined face under it shows as the line round it (carkit.parts.wheels.grow).
LIP_P = LIP                                   # 19 in: the same lip radius as the turbine
CHAMFER = 0.0022                              # the machined line round each opening, metres (8 px of 1080 at 0.2633 m)
R_BOT = 0.17                                  # the windows stop above the hub (the face keeps a 5 mm ring at r_in)
WIN_BIG = [(2.0, 0.170), (50.8, 0.170), (51.2, 0.228), (51.4, 0.299), (51.6, 0.340), (46.6, 0.466), (43.3, 0.588),
           (40.4, 0.749), (38.2, 0.935), (37.8, 0.945), (35.9, 0.948), (18.3, 0.949), (16.1, 0.948), (15.2, 0.940),
           (14.8, 0.926), (13.7, 0.819), (12.2, 0.714), (9.3, 0.566), (6.8, 0.476), (4.2, 0.406), (2.6, 0.372),
           (1.0, 0.320), (1.1, 0.273), (1.8, 0.230)]
WIN_V = [(-28.4, 0.947), (-29.1, 0.943), (-29.7, 0.932), (-28.1, 0.816), (-24.4, 0.664), (-20.6, 0.559), (-15.8, 0.469),
         (-13.1, 0.432), (-11.6, 0.423), (-9.5, 0.421), (-7.4, 0.423), (-6.1, 0.428), (-2.8, 0.474), (0.4, 0.530),
         (2.4, 0.571), (5.2, 0.650), (6.7, 0.701), (8.9, 0.799), (10.8, 0.910), (10.7, 0.938), (9.8, 0.947),
         (-3.1, 0.947), (-4.4, 0.944), (-8.6, 0.944), (-9.1, 0.947), (-10.4, 0.944)]
WIN_BIG = [(a, max(r, R_BOT)) for (a, r) in WIN_BIG]
# the black face's windows: each opening grown by the chamfer; its top reaches past the face's edge (r_out), which it trims
_BLACK_WINS = [[(a, max(r, R_BOT)) for (a, r) in W.grow(w, CHAMFER, LIP_P)] for w in (WIN_BIG, WIN_V)]

SPEC_SEAL_PERF = W.preset(
    "blade_5",
    rim_d=2.0 * LIP_P,
    flange=(0.118, 0.125, 0.50),
    flange_face=(1.0 - TAB) * LIP_P,
    dish=DISH,
    pinstripe=False,
    roll_left=math.pi,
    tyre=dict(bulge=1.035, shoulder=0.014, ridge=True),
    hub=dict(depth=0.045, setback=0.006, cap_rise=0.004, cap_r=0.030),
    lugs=dict(count=5, pcd_r=0.0580, r=0.0090, deg=23.0, rise=0.003),
    # the Performance's discs are drilled in the photograph (a ring of dots at the rim)
    disc=dict(style="drilled", inner_r=0.115, thickness=0.028, rings=2, per_ring=28, hole_r=0.0030),
    caliper=CALIPER,
    mats=dict(
        tyre="rubber",
        rim="wheel_black",
        lip="machined",
        lugs="wheel_black",
        cap="wheel_cap",
        disc="iron",
        barrel="wheel_black",
        accent="wheel_black",
        caliper="caliper",
    ),
)
SPEC_SEAL_PERF["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0010, mat="machined",
    r_in=0.040, r_out=TAB * LIP_P, nr=18, seg=72, step_deg=2.0, step_r=0.025,
    windows=[WIN_BIG, WIN_V],
    layers=[dict(mat="wheel_black", dz=0.0010, depth=0.012, bevel=0.0006, r_out=0.955 * LIP_P,
                 windows=_BLACK_WINS)],
)

DESIGNS = {
    "turbine_5": ("BYDSeal_", SPEC_SEAL_TURBINE_5),
    "perf_5y": ("BYDSeal_Perf_", SPEC_SEAL_PERF),
}
DEFAULT = "turbine_5"


def corners(surface):
    """The 4 corners of the BYD Seal: 235/45 R19 front and rear."""
    r = surface.WHEEL_R
    y_f = surface.TRACK_F / 2.0 + 0.095
    y_r = surface.TRACK_R / 2.0 + 0.095
    return [
        ("FL", surface.FRONT_AXLE,  1, 0.235, r, 0.178, 176.0, y_f),
        ("FR", surface.FRONT_AXLE, -1, 0.235, r, 0.178, 184.0, y_f),
        ("RL", surface.REAR_AXLE,   1, 0.235, r, 0.170, 176.0, y_r),
        ("RR", surface.REAR_AXLE,  -1, 0.235, r, 0.170, 184.0, y_r),
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
