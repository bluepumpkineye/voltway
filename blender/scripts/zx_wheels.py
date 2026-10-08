"""Zeekr 7X wheels: the 21 in design of the Ultra (265/40 R21 all round), traced from
the Autohome studio photograph (blender/reference/zeekr-7x/side_left_studio.jpg).

A machined-face wheel of SIX Y-shaped spokes, alternately leaning left and right (a
3-fold pattern, 120 deg to the repeat): each spoke is a stem from the hub that
widens and forks at 0.80 of the lip radius into two arms, with a black triangular
pocket between them; between two spokes lies a big window onto the disc and the
orange calipers (Brembo-style, "ZEEKR" lettered). Method as for the RX's wheels
(docs/3d-pipeline.md, scripts/wheel-trace): the photograph's wheel is unwarped so the
lip is a circle, unrolled into polar coordinates, and the outlines are read as
polygons of (angle deg CCW from 3 o'clock seen from outside, radius / lip radius).
The silver intervals the polygons come from were measured round the circle at nine
radii (silver.cjs); the left front wheel of the photograph is built as photographed,
the right wheels are the same wheel (an OEM wheel is not handed).

Sizes: the lip is the J flange, 17.3 mm above the 21 in bead seat: 0.2840 m.
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP = 0.2840
TAB = 0.945                       # the face's edge; outside it the machined flange's band

CALIPER = dict(span_deg=40.0, span_rear=36.0, r_inner=0.14, d_out=0.034, steps=16)

# depth of the face below the flange plane, by radius (m): the SU7's measured profile
DISH = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
              (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0105), (0.250, 0.0035),
              (0.285, 0.0)], mode="pchip")

# One repeat (120 deg) holds spoke A (stem at ~40 deg, leaning to lower angles outward),
# spoke B (stem at ~100 deg, leaning the other way) and the windows after each.
# window between A and B (the one the red caliper shows through on the front left)
WINDOW_AB = [(41.5, 0.300), (43.0, 0.350), (43.5, 0.450), (44.0, 0.550), (44.0, 0.650),
             (44.5, 0.750), (45.0, 0.820), (49.5, 0.880), (52.0, 0.920), (55.0, 0.945),
             (86.0, 0.945), (88.5, 0.920), (91.0, 0.880), (95.0, 0.820), (95.5, 0.750),
             (96.0, 0.650), (96.0, 0.550), (96.5, 0.450), (97.5, 0.350), (99.0, 0.300)]
# window between B and the next A (centred ~130 deg)
WINDOW_BA = [(104.5, 0.300), (101.5, 0.350), (100.0, 0.450), (103.5, 0.550), (107.5, 0.650),
             (110.5, 0.750), (112.0, 0.820), (113.0, 0.880), (114.0, 0.920), (116.0, 0.945),
             (144.0, 0.945), (145.0, 0.920), (146.0, 0.880), (147.0, 0.820), (148.5, 0.750),
             (152.0, 0.650), (156.0, 0.550), (159.5, 0.450), (158.0, 0.350), (156.0, 0.300)]
# the black pocket between each spoke's two arms (apex at 0.80)
POCKET_A = [(34.5, 0.795), (30.0, 0.820), (28.5, 0.880), (28.0, 0.920), (27.8, 0.945),
            (51.0, 0.945), (48.5, 0.920), (45.5, 0.880), (39.0, 0.820)]
POCKET_B = [(105.5, 0.800), (102.0, 0.820), (95.5, 0.880), (92.0, 0.920), (90.5, 0.945),
            (112.5, 0.945), (111.5, 0.920), (110.5, 0.880), (109.0, 0.820)]

SPEC = W.preset(
    "blade_5", rim_d=2.0 * LIP, dish=DISH, pinstripe=False,
    flange_face=(1.0 - TAB) * LIP, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0120, deg=22.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="machined", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss"))
SPEC["spokes"] = dict(
    style="traced", count=3, phase=0.0, depth=0.018, bevel=0.0020, mat="machined",
    r_in=0.034, r_out=TAB * LIP, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[WINDOW_AB, WINDOW_BA],
    inlay=dict(mat="black_gloss", polys=[POCKET_A, POCKET_B], lift=0.0004))


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius, caliper deg (local: 180
    # straight back; the left wheel's +Y is down, the right's up, so 176 and 184 are both
    # 4 degrees below the horizontal), outer sidewall y (track/2 + tyre width/2)
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.265, r, 0.190, 176.0, surface.TRACK_F / 2.0 + 0.1325),
        ("FR", surface.FRONT_AXLE, -1, 0.265, r, 0.190, 184.0, surface.TRACK_F / 2.0 + 0.1325),
        ("RL", surface.REAR_AXLE, 1, 0.265, r, 0.180, 176.0, surface.TRACK_R / 2.0 + 0.1325),
        ("RR", surface.REAR_AXLE, -1, 0.265, r, 0.180, 184.0, surface.TRACK_R / 2.0 + 0.1325),
    ]


def build_all(collection, surface, lib):
    return W.build_set(collection, "ZX_", lib, SPEC, corners(surface))
