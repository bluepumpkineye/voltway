"""XPeng G9L wheels: the 22 in five-spoke "Aero" of the 755 Ultra (265/40 R22), traced from the white
car's side photograph (blender/reference/xpeng-g9l/exterior/c1_0028.jpg; front-left wheel, ellipse
ratio 0.992 at the axle (803.9, 1910.2) px).

Method as for the 7X (docs/3d-pipeline.md, scripts/wheel-trace): the photograph is unwarped so the
lip is a circle, the axle corrected (-4, +2 px: centrefit), unrolled into polar coordinates, and the
five repeats voted over each other (segment.cjs); the machined shapes' outlines are polygons of (angle
deg CCW from 3 o'clock seen from outside, radius / the lip radius read from the photograph's own fitted
circle). That circle came out 2.5 % larger than the true lip (the machined ring stands at 0.93-0.975 in
it), so every radius is scaled by 1 / 0.975 below.

What the wheel is: five slim spokes, each a dark gloss blade (2.5 cm wide at mid radius) outlined by a
machined chamfer that runs up both its sides, round a rounded bright cap at the hub end, and forks into
two diamond-cut arms that reach the rim; the five windows between the spokes are open (the disc and the
grey caliper show through them), and a plain machined ring is the rim's flange.
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

K = 1.0 / 0.975                 # photograph's circle -> the true lip
LIP = 0.2985                    # the 22 in rim's lip radius (m): the photograph's 204 px at 681.5 px/m
TAB = 0.956                     # the face's edge: outside it the machined flange ring (0.953 to 1.0)

CALIPER = dict(span_deg=40.0, span_rear=36.0, r_inner=0.150, d_out=0.034, steps=16)

# depth of the face below the flange plane, by radius (m): a dished face, the hub 62 mm down
DISH = Curve([(0.000, 0.0620), (0.090, 0.0620), (0.115, 0.0560), (0.150, 0.0440),
              (0.190, 0.0310), (0.230, 0.0190), (0.265, 0.0090), (0.290, 0.0025),
              (0.2985, 0.0)], mode="pchip")


def _k(pts):
    return [(a, r * K) for (a, r) in pts]


# the open window between spoke k (its right edge) and spoke k+1 (its left edge): outside the right band's
# outer edge up to the arm's tip, along the rim ring, down the next spoke's left band's outer edge
WINDOW = _k([
    (77.0, 0.300), (76.5, 0.360), (76.9, 0.395), (75.6, 0.556), (75.2, 0.746), (77.3, 0.790),
    (83.1, 0.868), (88.5, 0.935),
    (121.3, 0.935), (125.5, 0.882), (133.8, 0.767), (134.9, 0.729), (134.1, 0.563), (132.2, 0.379),
    (130.9, 0.300),
])
WINDOW = [(a, min(r, TAB - 0.004)) for (a, r) in WINDOW]

# the spoke's machined outline: a U (round cap at the hub, a leg up each side) flaring into the arms
# that reach the rim; the dark blade lies in the gap between the legs. The U's OUTER edges overrun the
# window's edges by 1.5 degrees: the skin is trimmed by the windows (wheels._traced_inlay), and two
# boundaries that coincide empty the boolean.
def _over(pts, sgn):
    out = []
    for (a, r) in pts:
        out.append((a + sgn * 1.5 * max(0.0, min(1.0, (r - 0.25) / 0.08)), r))
    return out


_LEFT_OUT = [(55.5, 0.205), (58.9, 0.305), (60.2, 0.379), (61.8, 0.470), (62.3, 0.563), (62.9, 0.729),
             (61.8, 0.767), (53.5, 0.882), (49.3, 0.973)]
_RIGHT_OUT = [(87.8, 0.973), (83.1, 0.868), (77.3, 0.790), (75.2, 0.746), (75.6, 0.556), (76.9, 0.395),
              (76.4, 0.360), (77.6, 0.224)]
SPOKE_U = [(a, min(r * K, TAB)) for (a, r) in (
    _over(_LEFT_OUT, -1.0)
    # the arm's end, then down its inner edge to the gap
    + [(55.3, 0.973), (60.6, 0.895), (65.4, 0.831), (65.4, 0.685), (64.8, 0.525), (64.3, 0.440),
       (63.4, 0.340), (62.7, 0.300),
       # round the bottom of the gap
       (63.4, 0.262), (66.0, 0.246), (69.0, 0.243), (72.0, 0.248), (74.0, 0.262), (74.6, 0.300),
       # up the right leg's inner edge to its arm
       (73.4, 0.393), (72.7, 0.564), (72.4, 0.834), (82.5, 0.973), (87.8, 0.973)]
    + _over(_RIGHT_OUT, +1.0)
    # round the outside of the cap
    + [(76.0, 0.205), (72.0, 0.188), (68.0, 0.183), (63.0, 0.188), (58.0, 0.196)])]

SPEC_AERO = W.preset(
    "blade_5", rim_d=2.0 * LIP, dish=DISH, pinstripe=False,
    flange_face=(1.0 - TAB) * LIP, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0620, setback=0.008, cap_rise=0.0055, cap_r=0.034),
    lugs=dict(count=5, pcd_r=0.0600, r=0.0120, deg=18.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="cap_black",
              disc="iron", barrel="black_gloss", accent="black_gloss"),
)
SPEC_AERO["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0018, mat="black_gloss",
    r_in=0.040, r_out=TAB * LIP, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=[WINDOW],
    inlay=dict(mat="machined", polys=[SPOKE_U], lift=0.0005),
)
SPEC = SPEC_AERO

DESIGNS = {
    "aero": ("G9L_", SPEC_AERO),
}
DEFAULT = "aero"


def corners(surface):
    """The 4 corners of the car: FL, FR, RL, RR with exact track and axle positions."""
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.265, r, 0.185, 176.0, surface.TRACK_F / 2.0 + 0.1325),
        ("FR", surface.FRONT_AXLE, -1, 0.265, r, 0.185, 184.0, surface.TRACK_F / 2.0 + 0.1325),
        ("RL", surface.REAR_AXLE, 1, 0.265, r, 0.175, 176.0, surface.TRACK_R / 2.0 + 0.1325),
        ("RR", surface.REAR_AXLE, -1, 0.265, r, 0.175, 184.0, surface.TRACK_R / 2.0 + 0.1325),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    """The car's own wheels: the default 22-inch aero design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
