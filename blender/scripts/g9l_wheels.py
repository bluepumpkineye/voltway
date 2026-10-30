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

CALIPER = dict(span_deg=40.0, span_rear=36.0, r_inner=0.150, d_out=0.034, steps=16, groove=True)

# depth of the face below the flange plane, by radius (m): a dished face, the hub 62 mm down
DISH = Curve([(0.000, 0.0620), (0.090, 0.0620), (0.115, 0.0560), (0.150, 0.0440),
              (0.190, 0.0310), (0.230, 0.0190), (0.265, 0.0090), (0.290, 0.0025),
              (0.2985, 0.0)], mode="pchip")


def _k(pts):
    return [(a, r * K) for (a, r) in pts]


def _bar(p, q, w):
    """A flat bar of half-width w from p to q (metres): one quad of an emblem."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * w, dx / ln * w
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


# the XPeng mark on the hub cap: an X (two crossing bars) in bright metal on the black cap
CAP_LOGO = dict(mat="logo_chrome", h=0.0118, quads=[_bar((-0.0105, -0.0105), (0.0105, 0.0105), 0.0016),
                                                    _bar((-0.0105, 0.0105), (0.0105, -0.0105), 0.0016)])


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
    tyre=dict(bulge=1.045, shoulder=0.016, ridge=True),
    hub=dict(depth=0.0620, setback=0.008, cap_rise=0.0055, cap_r=0.034, cap_logo=CAP_LOGO),
    lugs=dict(count=5, pcd_r=0.0600, r=0.0120, deg=18.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER,
    mats=dict(rim="wheel_black", lip="machined", lugs="wheel_black", cap="cap_black",
              disc="iron", barrel="wheel_black", accent="wheel_black"),
)
SPEC_AERO["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0018, mat="wheel_black",
    r_in=0.040, r_out=TAB * LIP, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=[WINDOW],
    inlay=dict(mat="machined", polys=[SPOKE_U], lift=0.0005),
)

# ------------------------------------------------------------------------------------------ the 21 in turbine
# The showroom cars' second wheel (c1_0033-59: the green, white, purple and grey cars on 265/45 R21): a black gloss five-arm turbine
# with a machined band round the rim and a thin machined chamfer on each window's far edge. Traced (2026-10-29, second pass) from the
# WHITE car's left front wheel (c1_0043.jpg, ellipse ratio 0.956 at (691.6, 1832.3) px, the best of the showroom set; the first pass read
# the purple car's, ratio 0.915, and its windows came out a third too small): unwarped, centre-corrected (-16, -5 px), lifted, read in
# polar coordinates (angle deg CCW from 3 o'clock seen from outside the LEFT wheel, radius / the lip's). The silver outlines are
# segment.cjs (lum 150-255) on that picture; the window is read off the strip against them. The right wheels are the MIRROR IMAGE
# (c1_0053, the purple car's right front: the same pads, the swirl the other way), built from the outlines reflected (_mirror).
LIP21 = 0.2858                  # the 21 in rim's lip radius (m): the bead seat 266.7 mm + the 19.1 mm flange
OUT21 = 1.02                    # the inlay's outer arc overruns the face's edge (coincident boundaries empty the boolean)
TAB21 = 0.995                   # the face runs to the lip (the lip's ring is black between the pads and swooshes: they are inlays)

# the open window between two arms: its rim side is the silver band's inner edge (pushed 0.006 into it, so the band's visible edge is
# the window's and the two never coincide), its swirl side the swoosh's lower edge, its far side the arm's leading chamfer (also pushed
# in), its inner end the hub web (r 0.41-0.44)
WINDOW21 = [
    (32.4, 0.945), (36.0, 0.950), (57.0, 0.950), (60.8, 0.947), (63.8, 0.921), (68.3, 0.862), (72.4, 0.811), (78.6, 0.752),
    (82.9, 0.721), (88.8, 0.687), (89.7, 0.640), (89.7, 0.550), (89.0, 0.470), (84.0, 0.436), (77.0, 0.420), (70.0, 0.413),
    (60.5, 0.429), (56.5, 0.446), (52.5, 0.465), (47.9, 0.497), (43.0, 0.538), (39.6, 0.573), (37.2, 0.602), (34.4, 0.644),
    (33.0, 0.700), (32.5, 0.780), (32.3, 0.860),
]
# the silver of one repeat: the pad at the rim (12-25 deg), the band along the rim, and the swoosh that turns in from it down to
# r 0.68 at 91 deg (its tip passes 14 mm clear of the next repeat's pad)
BAND21 = [
    (16.9, 0.970), (14.8, 0.884), (12.3, 0.797), (13.4, 0.779), (19.0, 0.747), (20.5, 0.750), (20.9, 0.755), (23.6, 0.875),
    (24.6, 0.935), (24.9, 0.946), (25.6, 0.955), (30.5, 0.956), (31.9, 0.958), (34.8, 0.958), (35.8, 0.959), (38.4, 0.962),
    (57.4, 0.957), (60.3, 0.946), (63.3, 0.919), (67.8, 0.858), (71.9, 0.807), (78.1, 0.748), (82.4, 0.717), (88.3, 0.683),
    (89.5, 0.678), (90.9, 0.684), (91.6, 0.698), (91.4, 0.701), (86.3, 0.728), (82.0, 0.757), (76.6, 0.803), (73.1, 0.841),
    (68.6, 0.901), (65.9, 0.944), (64.3, OUT21), (17.4, OUT21),
]
# the arm's leading chamfer, the thin arc on the window's lower-left edge, and a short stroke on the web below it
ARC21 = [
    (33.3, 0.651), (32.8, 0.649), (32.7, 0.640), (37.1, 0.576), (41.1, 0.528), (45.9, 0.489), (52.3, 0.449), (58.0, 0.420),
    (62.1, 0.404), (67.1, 0.389), (68.4, 0.388), (69.4, 0.393), (69.7, 0.404), (69.3, 0.408), (60.5, 0.435), (56.5, 0.452),
    (52.5, 0.471), (47.9, 0.503), (43.0, 0.544), (39.6, 0.579), (37.2, 0.608), (34.4, 0.650),
]
# (a second stroke on the web, from (22, 0.54) to (42, 0.33), is not built: with the other outlines in one INTERSECT the exact solver returned
# the complement of the right wheel's silver for two of the five repeats, though every outline alone is fine and the left wheel is too)
STROKE_B = [(55.5, 0.408), (56.1, 0.395), (70.2, 0.349), (69.7, 0.362)]


def _mirror(polys):
    """The right wheel's polygons: the photographed left wheel reflected about the vertical (angle -> 180 - angle, the winding kept).
    The right wheel is built with no roll; the left one (the traced outlines as they are) with the half turn every left wheel needs."""
    return [[(180.0 - a, r) for (a, r) in reversed(p)] for p in polys]


CALIPER21 = dict(span_deg=40.0, span_rear=36.0, r_inner=0.150, d_out=0.034, steps=16, groove=True)
SPEC_TURBINE_L = W.preset(
    "blade_5", rim_d=2.0 * LIP21, dish=DISH, pinstripe=False,
    flange_face=(1.0 - TAB21) * LIP21, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016, ridge=True),
    hub=dict(depth=0.0620, setback=0.008, cap_rise=0.0055, cap_r=0.040, cap_logo=CAP_LOGO),
    lugs=dict(count=5, pcd_r=0.0600, r=0.0120, deg=18.0, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.125, thickness=0.034),
    caliper=CALIPER21,
    # the barrel seen through the windows is satin: glossy black mirrored the white studio and the five openings read as chrome
    mats=dict(rim="wheel_black", lip="wheel_black", lugs="wheel_black", cap="cap_black",
              disc="iron", barrel="black_trim", accent="wheel_black"),
)
SPEC_TURBINE_L["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0028, mat="wheel_black",
    r_in=0.040, r_out=TAB21 * LIP21, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=[WINDOW21],
    inlay=dict(mat="machined", polys=[BAND21, ARC21, STROKE_B], lift=0.0005),
)
SPEC_TURBINE = dict(SPEC_TURBINE_L)
SPEC_TURBINE["spokes"] = dict(SPEC_TURBINE_L["spokes"], windows=_mirror([WINDOW21]),
                              inlay=dict(mat="machined", polys=_mirror([BAND21, ARC21, STROKE_B]), lift=0.0005))

SPEC = SPEC_AERO

DESIGNS = {
    "aero": ("G9L_", SPEC_AERO),
    "turbine": ("G9L_Turbine_", SPEC_TURBINE, SPEC_TURBINE_L),
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
    """One design on the four corners. A design with a third entry has left-hand wheels of its own (the turbine's swirl is
    mirrored from side to side): the left corners are built from it, the right from the second."""
    prefix, spec, *left = DESIGNS[name]
    cs = corners(surface)
    if not left:
        return W.build_set(collection, prefix, lib, spec, cs)
    made = W.build_set(collection, prefix, lib, spec, [c for c in cs if c[2] < 0])
    return made + W.build_set(collection, prefix, lib, left[0], [c for c in cs if c[2] > 0])


def build_all(collection, surface, lib):
    """The car's own wheels: the default 22-inch aero design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
