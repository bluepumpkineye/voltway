"""Zeekr 7X wheels: the three designs the maker's configuration page offers with the car
(Autohome lists 255/50 R19, 265/45 R20 and 265/40 R21; the 19 in aero cover is not built):

    y        21 in six-Y, machined face over black, 265/40 R21 - the Ultra's, the default,
             traced from the studio photograph (blender/reference/zeekr-7x/side_left_studio.jpg)
    multi    20 in multi-spoke, 265/45 R20 - a polished chrome disc inside 14 slim machined
             spokes split by a black groove, 14 U-shaped windows, a chrome-ringed cap
    fork     20 in twin-fork, 265/45 R20 - five narrow V windows and five wider pockets in a
             black face edged with machined bands, five domed lug caps; two finishes of ONE
             model: the bands are the accent material, silver (two-tone) or gloss black

Method as for the RX's wheels (docs/3d-pipeline.md, scripts/wheel-trace): each design's
photograph (Autohome series 7777, blender/reference/zeekr-7x/wheels/candidates) is unwarped so
the lip is a circle, unrolled into polar coordinates, the repeats voted over each other
(scripts/wheel-trace/segment.cjs) and the outlines read as polygons of (angle deg CCW from
3 o'clock seen from outside, radius / lip radius). The photographs show the car's left side,
the left front wheel is built as photographed and the right wheels are the same wheel (an OEM
wheel is not handed).

Both new faces are mirror symmetric about the axis of each window, so their outlines are built
from half-width tables (_sym) and cannot lean. The hub of a photograph is deeper than its lip,
so the camera's tilt moves it: the twin-fork photograph's lug-nut pentagon is 15 px (0.014 of
the lip radius) below the lip's centre, which turns the angles of features near the hub by up
to 4 degrees; the foot of the silver U was read from a copy shifted to the hub's centre.

Sizes: the lip is the J flange, 17.3 mm above the bead seat: 0.2840 m on a 21 in rim, 0.2713 m
on a 20 in. The overall diameters agree (0.7454 m and 0.7465 m), so the corner table is shared.
The bolt circle is 5 x 108 (54 mm radius: the photograph's lug nuts measure 53.9).
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP = 0.2840                      # the 21 in rim's lip
LIP_20 = 0.2713
TAB = 0.945                       # the six-Y face's edge; outside it the machined flange's band

CALIPER = dict(span_deg=40.0, span_rear=36.0, r_inner=0.14, d_out=0.034, steps=16)

# depth of the face below the flange plane, by radius (m): the SU7's measured profile
DISH = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
              (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0105), (0.250, 0.0035),
              (0.285, 0.0)], mode="pchip")


def _mirror(axis, pts):
    """The points reflected about the angle `axis` (the order is kept)."""
    return [(2.0 * axis - t, r) for (t, r) in pts]


def _sym(axis, rows):
    """A closed outline symmetric about `axis` from rows [(radius, half-width deg), ...] in
    ascending radius: up the left side, across the top, down the right side, across the
    bottom (the edges between two points of one radius are arcs once densified)."""
    left = [(axis - hw, r) for (r, hw) in rows]
    right = [(axis + hw, r) for (r, hw) in reversed(rows)]
    return left + right


# ====================================================================== y: 21 in six-Y
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

SPEC_Y = W.preset(
    "blade_5", rim_d=2.0 * LIP, dish=DISH, pinstripe=False,
    flange_face=(1.0 - TAB) * LIP, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0120, deg=22.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="machined", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron", barrel="black_gloss"))
SPEC_Y["spokes"] = dict(
    style="traced", count=3, phase=0.0, depth=0.018, bevel=0.0020, mat="machined",
    r_in=0.034, r_out=TAB * LIP, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[WINDOW_AB, WINDOW_BA],
    inlay=dict(mat="black_gloss", polys=[POCKET_A, POCKET_B], lift=0.0004))
SPEC = SPEC_Y                     # wheel_preview and older callers


# ============================================================== multi: 20 in multi-spoke
# 14-fold (the autocorrelation of the photograph's rim: 13.98), one repeat = 25.714 deg.
# Traced from the white-and-black car's left front wheel, 12_75351_40 (ellipse ratio 0.989).
P_M = 360.0 / 14.0
TH_S = 1.8                        # the spoke between two windows (the groove's axis)
TH_W = TH_S + P_M / 2.0           # a window's axis
TAB_M = 0.979                     # the face's edge: the bars run up to the lip's flange
DISH_M = Curve([(0.000, 0.0520), (0.080, 0.0520), (0.110, 0.0490), (0.140, 0.0450),
                (0.165, 0.0400), (0.190, 0.0330), (0.220, 0.0220), (0.250, 0.0100),
                (0.268, 0.0020), (0.2713, 0.0)], mode="pchip")
# the chrome disc's edge round a window (|degrees from its axis|, radius): the black band's outer
# U, a wide flat bottom at 0.478 that climbs steeply near +-8 degrees to the line at 0.5877
# under the spokes (read from the photograph centred on the axle)
CHROME_EDGE = [(0.0, 0.478), (2.1, 0.482), (3.4, 0.487), (4.6, 0.495), (5.9, 0.508), (6.5, 0.519),
               (7.0, 0.529), (7.5, 0.543), (7.9, 0.565), (8.2, 0.583), (8.45, 0.5875)]


def _multi_window():
    """The U-shaped window the brake disc shows through: straight radial sides 6.9 deg either
    side of the axis from r 0.60 to the top at 0.958, rounded top corners, a half-ellipse
    bottom down to 0.52. The black band round it (to 8.6 deg and r 0.478) is the face."""
    hw, rt, rb, rm, c = 6.9, 0.958, 0.520, 0.600, 1.3
    left = [(TH_W - hw, rm), (TH_W - hw, rt - 0.018), (TH_W - hw + 0.25, rt - 0.0075),
            (TH_W - hw + 0.70, rt - 0.0022), (TH_W - hw + c, rt)]
    right = _mirror(TH_W, left)[::-1]
    arc = [(TH_W + hw * math.cos(math.pi * i / 8.0), rm - (rm - rb) * math.sin(math.pi * i / 8.0))
           for i in range(1, 8)]
    return left + right + arc


def _multi_bars():
    """The machined bars of each spoke: two, 2.8 deg wide, a 3.2 deg black groove between them,
    from the black line at 0.62 (the chrome disc ends at 0.5877) to the lip."""
    bars = []
    for a, b in ((TH_S - 4.4, TH_S - 1.6), (TH_S + 1.6, TH_S + 4.4)):
        bars.append([(a, 0.620), (a, 1.05), (b, 1.05), (b, 0.620)])
    return bars


def _multi_patch():
    """The chrome disc's edge: 0.5877 under a spoke, round each window the U of its black band
    - one repeat, starting at the spoke's axis."""
    left = [(TH_W - d, r) for (d, r) in CHROME_EDGE[1:]][::-1]
    right = [(TH_W + d, r) for (d, r) in CHROME_EDGE]
    return [(TH_S, 0.5877)] + left + right


def _strip(path, w):
    """The quads of a strip of width w along a polyline, mitred at the corners: [(x, y) x 4] per
    segment (left, right, right, left)."""
    h = 0.5 * w
    n = len(path)
    normals = []
    for i in range(n - 1):
        dx, dy = path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]
        length = math.hypot(dx, dy)
        normals.append((-dy / length, dx / length))
    left, right = [], []
    for i in range(n):
        if i == 0 or i == n - 1:
            m, k = normals[0 if i == 0 else -1], 1.0
        else:
            a, b = normals[i - 1], normals[i]
            m, k = (a[0] + b[0], a[1] + b[1]), 1.0 / (1.0 + a[0] * b[0] + a[1] * b[1])
        left.append((path[i][0] + h * k * m[0], path[i][1] + h * k * m[1]))
        right.append((path[i][0] - h * k * m[0], path[i][1] - h * k * m[1]))
    return [[left[i], right[i], right[i + 1], left[i + 1]] for i in range(n - 1)]


def _multi_logo(size=0.0441, tau=0.10, w=0.095, rot=13.5):
    """The emblem on the multi-spoke's cap (a square outline with a bent divider): size 44 mm,
    its stroke 4.4 mm, turned 13.5 deg anticlockwise in the photographed frame (the corrected
    face-on photograph: the box's edges 175 px of 1080, its up at 103.5 deg). Flat quads."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(u, t):                                   # box (u right, t down, 0..1) -> the cap, m
        x, y = (u - 0.5) * size, (0.5 - t) * size
        return (x * c - y * s, x * s + y * c)

    quads = []
    for (u0, t0, u1, t1) in ((0, 0, 1, tau), (0, 1 - tau, 1, 1), (0, tau, tau, 1 - tau),
                             (1 - tau, tau, 1, 1 - tau)):
        quads.append([P(u0, t0), P(u1, t0), P(u1, t1), P(u0, t1)])
    # the divider: down from the top bar, a 45 degree step to the right, down to the bottom bar
    for q in _strip([(0.385, tau), (0.385, 0.375), (0.635, 0.625), (0.635, 1 - tau)], w):
        quads.append([P(*pt) for pt in q])
    return quads


SPEC_MULTI = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH_M, pinstripe=False,
    flange_face=(1.0 - TAB_M) * LIP_20, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    # the cap's ring is 71.6 mm in radius (0.264 of the lip's) round a black plate of 43.7 mm: a
    # chrome ring that crests at 9 mm and dips to the plate (the close-up c34), the lug nuts under
    # it; the plate carries the emblem
    hub=dict(depth=0.0440, setback=0.008,
             cap_pts=[(0.0, 0.0050), (0.0410, 0.0050), (0.0437, 0.0056), (0.0480, 0.0072),
                      (0.0580, 0.0090), (0.0650, 0.0078), (0.0693, 0.0048), (0.0716, 0.0014)],
             cap_inner=dict(r=0.0437, h=0.0058, mat="cap_black"),
             cap_logo=dict(quads=_multi_logo(), h=0.0062, mat="logo_grey")),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0120, deg=16.9, rise=0.004, hidden=True),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="chrome_polish",
              disc="iron", barrel="black_gloss"))
SPEC_MULTI["spokes"] = dict(
    style="traced", count=14, phase=0.0, depth=0.016, bevel=0.0015, mat="black_gloss",
    r_in=0.034, r_out=TAB_M * LIP_20, nr=18, seg=84, step_deg=1.0, step_r=0.02,
    windows=[_multi_window()],
    inlay=[dict(mat="chrome_polish", patch=_multi_patch(), lift=0.0004),
           dict(mat="machined", polys=_multi_bars(), lift=0.0006)])


# ============================================================== fork: 20 in twin-fork
# 5-fold (period 72). Traced from the green car's left front wheel, 12_75351_324 (ratio 0.992).
# A big narrow-necked V window on axis TH_B (the lug nuts sit on these axes) and a wider pocket
# between the two arms of a twin-fork spoke on axis TH_P, both mirror symmetric; a silver band
# on each arm's outer edge that runs into a U under the pocket, and a silver spike on the
# inside of each arm. Features near the hub were read from a copy of the photograph shifted
# to the hub's centre (module docstring).
TH_B = 16.6
TH_P = TH_B + 36.0
TAB_F = 0.979                      # where the face ends and the lip's silver band begins
DISH_F = DISH                      # the six-Y's profile: a deep hub, the arms rising to the lip

# the big window's half-widths, bottom to top (r, degrees): a bottle, widest at 0.51
FORK_BW = [(0.369, 11.6), (0.373, 12.55), (0.379, 13.3), (0.399, 14.2), (0.426, 15.45), (0.466, 16.8),
           (0.492, 17.43), (0.514, 17.5), (0.537, 17.26), (0.625, 15.6), (0.719, 14.3), (0.869, 12.83),
           (0.955, 12.1), (0.967, 11.7), (0.976, 11.0)]
# the pocket's, from the bottom to the lip: the spikes' inner edges make its neck
FORK_SW = [(0.372, 7.2), (0.385, 8.4), (0.400, 9.0), (0.450, 10.0), (0.550, 10.4), (0.650, 10.5),
           (0.700, 10.8), (0.740, 11.4), (0.7777, 11.2), (0.8669, 9.3), (0.960, 7.8), (0.969, 7.4),
           (0.976, 6.5)]


def _bw_edge(r):
    """The big window's half-width at radius r (a linear read of FORK_BW)."""
    for (r0, h0), (r1, h1) in zip(FORK_BW, FORK_BW[1:]):
        if r0 <= r <= r1:
            return h0 + (h1 - h0) * (r - r0) / (r1 - r0)
    return FORK_BW[-1][1] if r > FORK_BW[-1][0] else FORK_BW[0][1]


def _fork_u():
    """The silver U round a pocket: the arm's band on the big window's edge (window side:
    the window's own edge pushed 0.3 deg into it, so the window trims it exactly; pocket
    side: read), flaring into the foot, closed under the pocket by a bar 0.1875 to 0.211."""
    out = []
    for r in (1.05, 0.976, 0.955, 0.869, 0.719, 0.625, 0.537, 0.514, 0.492, 0.466, 0.426, 0.399, 0.379):
        out.append((TH_B + _bw_edge(min(r, 0.976)) - 0.3, r))
    # below the window the band flares into the foot (read from the photograph centred on the axle)
    out += [(29.22, 0.356), (29.32, 0.345), (31.01, 0.304), (33.47, 0.2615), (35.44, 0.236),
            (37.13, 0.218), (38.63, 0.2055), (40.31, 0.1973), (42.19, 0.1927), (46.06, 0.1888)]
    inner = [(45.94, 0.2104), (43.94, 0.2142), (42.94, 0.2204), (42.45, 0.2285), (41.51, 0.2523),
             (41.07, 0.2646), (40.47, 0.2954), (39.66, 0.3385), (38.53, 0.4108), (37.47, 0.5138),
             (35.72, 0.5831), (34.47, 0.6415), (32.78, 0.7462), (31.59, 0.8446), (30.84, 0.9223),
             (30.34, 0.9931), (30.13, 1.0), (30.0, 1.05)]
    left_leg_out = out                                  # top to bottom
    right_leg_out = _mirror(TH_P, out)[::-1]            # bottom to top
    right_in = _mirror(TH_P, inner)                     # bar top to the top
    return (left_leg_out + right_leg_out + right_in[::-1] + inner)


def _fork_spikes():
    """The two silver spikes on the inner edges of a spoke's arms, from the lip to a rounded
    tip at 0.743; the inner edge is pushed 0.4 deg into the pocket, which trims it."""
    left = [(42.37, 1.05), (42.37, 1.0), (40.47, 0.8477), (39.22, 0.7723), (39.41, 0.7546),
            (39.81, 0.7435), (40.37, 0.7427), (40.97, 0.7454), (41.81, 0.7777), (43.68, 0.8669),
            (45.24, 0.96), (45.62, 0.9692), (46.46, 0.9765), (46.6, 1.05)]
    return [left, _mirror(TH_P, left)[::-1]]


SPEC_FORK = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH_F, pinstripe=False,
    flange_face=(1.0 - TAB_F) * LIP_20, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055, cap_r=0.0334),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0133, deg=16.8, rise=0.004, dome=0.0095),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="accent", accent="accent", lugs="lug_grey", cap="cap_black",
              disc="iron", barrel="black_gloss"))
SPEC_FORK["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="black_gloss",
    r_in=0.034, r_out=TAB_F * LIP_20, nr=18, seg=60, step_deg=1.0, step_r=0.02,
    windows=[_sym(TH_B, FORK_BW), _sym(TH_P, FORK_SW)],
    lug_holes=dict(deg=16.8, pcd=0.0540, r=0.0165, count=5),
    inlay=dict(mat="accent", polys=[_fork_u(), *_fork_spikes()], lift=0.0005))


# ======================================================================== the set
# name -> (object prefix, spec). The default keeps the build's own "ZX_" names.
DESIGNS = {
    "y": ("ZX_", SPEC_Y),
    "multi": ("ZX_Multi_", SPEC_MULTI),
    "fork": ("ZX_Fork_", SPEC_FORK),
}
DEFAULT = "y"


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius, caliper deg (local: 180
    # straight back; the left wheel's +Y is down, the right's up, so 176 and 184 are both
    # 4 degrees below the horizontal), outer sidewall y (track/2 + tyre width/2). The overall
    # diameter is the same for every design, so is the table.
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.265, r, 0.190, 176.0, surface.TRACK_F / 2.0 + 0.1325),
        ("FR", surface.FRONT_AXLE, -1, 0.265, r, 0.190, 184.0, surface.TRACK_F / 2.0 + 0.1325),
        ("RL", surface.REAR_AXLE, 1, 0.265, r, 0.180, 176.0, surface.TRACK_R / 2.0 + 0.1325),
        ("RR", surface.REAR_AXLE, -1, 0.265, r, 0.180, 184.0, surface.TRACK_R / 2.0 + 0.1325),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    """The car's own wheels: the default design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    """The other designs, on top of the first: for the export (each is split into a node
    of its own), never for a render."""
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
