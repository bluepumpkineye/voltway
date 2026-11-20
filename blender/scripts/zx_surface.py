"""Zeekr 7X body surface - the profile curves of its flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module is the 7X's
DATA: its dimensions and the profile curves every section is built from, read
off the camera-matched photographs (zx_ref_match.py; the photo readings behind
every value are in zx_camsolve.py).

Real dimensions (Autohome spec table, 2026 Ultra; MIIT 2027 filing): 4825 x 1930
x 1656 mm (the RWD cars 1666), wheelbase 2925, track 1649 front / 1654 rear,
tyres 265/40 R21 all round (255/50 R19 and 265/45 R20 are the options). The
overhangs are not published: 870 front / 1030 rear is what the side photograph
gives, solved through its camera (the nose lip at 0.875 m ahead of the front
axle with the plate, the tail's bumper corner 1.042 behind the rear one; the
published length less the plate's 15 mm).

What makes a 7X, from the photographs:
  - a cab-forward silhouette: the windscreen's base stands right behind the
    front wheel (x 1.2, 0.34 m behind the front axle), the hood is short and
    nearly flat at 1.085 m, rolling down over a vertical nose to a lip at 0.24
  - a windscreen at 29 degrees to a roof that peaks at 1.656 m at x -0.5 and
    falls gently to a roof spoiler at x -1.92, z 1.50 (the blade overhangs the
    backlight, which slopes to the tail at 61 degrees from the vertical)
  - a belt rising from 1.106 at the A-pillar to 1.265 at the quarter glass's tip
  - big wheel openings with black cladding, a black sill with a silver strip

    S(x, v)   x = station along the car in metres, +X forward, centre of the
                  car at x = 0 (the front axle is at +1.5425)
              v = 0 at the underbody centreline, 1 at the roof centreline,
                  V_SHOULDER at the crease
"""
from carkit.geom import Curve, Joined, smoothstep as _smooth          # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 4.825, 1.930, 1.656
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
WHEELBASE = 2.925
FRONT_OVERHANG = 0.870
FRONT_AXLE = HALF_L - FRONT_OVERHANG        # 1.5425
REAR_AXLE = FRONT_AXLE - WHEELBASE          # -1.3825
WHEEL_R = 0.3647             # loaded hub height: 265/40 R21 (0.3727 free), 8 mm of sag
TRACK_F, TRACK_R = 1.649, 1.654
# The PAINTED opening (first pass: the photographs' painted edge sits ~0.5 m
# from the hub, outside the black cladding lip).
ARCH_R = 0.500

V_SHOULDER = 0.520

COWL_X = 1.200               # windscreen base
KNEE_X = -1.930              # the roof spoiler's trailing edge: backlight below
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# Top centreline (the side photograph's top outline cast onto the plane y = 0.05,
# the camera solved in zx_camsolve; the roof peaks at 1.649 there, 1.656
# published). The lidar pod (x 0.25-0.37) is left out.
def _smooth_z(pts, x_lo, x_hi, passes=3):
    """[1 2 1]/4 filter on the heights of the samples strictly inside (x_lo, x_hi): the photograph's
    outline was read a pixel at a time and its noise (a few mm) became ripples along the roof's
    paint, rail and glass. The ends and the steep parts are kept as read."""
    pts = [tuple(p) for p in pts]
    for _ in range(passes):
        out = list(pts)
        for i in range(1, len(pts) - 1):
            if x_lo < pts[i][0] < x_hi:
                out[i] = (pts[i][0], 0.25 * pts[i - 1][1] + 0.5 * pts[i][1] + 0.25 * pts[i + 1][1])
        pts = out
    return pts


Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # the backlight, spoiler lip to the tail: a 29-degree slope (rear glass)
    (-HALF_L, 1.118), (-2.342, 1.150), (-2.250, 1.196), (-2.157, 1.249),
    (-2.065, 1.302), (-1.990, 1.345), (KNEE_X, 1.395),
]), Curve(_smooth_z([
    # the roof, spoiler lip to windscreen header
    (KNEE_X, 1.395), (-1.905, 1.480), (-1.881, 1.514), (-1.789, 1.530),
    (-1.696, 1.546), (-1.603, 1.561), (-1.511, 1.584), (-1.418, 1.600),
    (-1.326, 1.612), (-1.233, 1.622), (-1.140, 1.629), (-1.047, 1.635),
    (-0.862, 1.640), (-0.677, 1.646), (-0.491, 1.649), (-0.306, 1.645),
    (-0.120, 1.639), (-0.027, 1.632), (0.066, 1.624), (0.159, 1.610),
    (0.251, 1.592), (0.344, 1.570), (0.437, 1.542), (0.530, 1.498),
    (0.623, 1.448), (0.716, 1.395), (0.810, 1.340), (0.903, 1.285),
    (0.996, 1.226), (1.089, 1.168), (1.182, 1.110), (COWL_X, 1.098),
], -1.84, 0.30, passes=5))), Curve([
    # the hood: nearly flat at 1.085, then over the nose
    (COWL_X, 1.098), (1.275, 1.089), (1.368, 1.090), (1.460, 1.086),
    (1.553, 1.085), (1.646, 1.079), (1.739, 1.069), (1.831, 1.053),
    (1.924, 1.032), (2.017, 1.005), (2.110, 0.970), (2.203, 0.927),
    (2.296, 0.875), (2.360, 0.835), (HALF_L, 0.790),
]))

# Underbody: the sill's tray at 0.20 (ground clearance 160-197 mm), a chin
# lip at the nose (0.24 at x 2.42) and the diffuser's edge at the tail.
Z_FLOOR = Curve([
    (-HALF_L, 0.275), (-2.30, 0.250), (-2.10, 0.222), (-1.90, 0.205),
    (-1.38, 0.200), (0.0, 0.198), (1.54, 0.200), (1.95, 0.208),
    (2.20, 0.222), (2.36, 0.240), (HALF_L, 0.262),
])

# The widest point of the PAINTED body and how high it sits. The rear photograph
# (rows z 0.72-0.95) puts the painted flank at only +/-0.845 at the tail; the arch
# cladding and the black bumper corners carry the car out to +/-0.93 below z 0.70
# (zx_side builds them), and the front fenders are ~0.89 at the lamps.
Z_HIP = Curve([
    (-HALF_L, 0.620), (-2.20, 0.760), (-1.90, 0.800), (-1.38, 0.800), (-0.70, 0.790),
    (0.0, 0.760), (0.80, 0.730), (1.20, 0.720), (1.54, 0.700), (2.00, 0.620),
    (2.25, 0.580), (HALF_L, 0.520),
])

# Beltline: ~40 mm under the window's lower edge (side photo: the glass bottom
# at 1.106 at the A-pillar, 1.146 at x -0.7, 1.22 at -1.27, 1.265 at the quarter
# glass's tip). Ahead of the cowl it runs along the fender top into the lamp.
Z_SHOULDER = Curve([
    (-HALF_L, 1.010), (-2.30, 1.050), (-2.00, 1.150), (-1.70, 1.200), (-1.40, 1.215),
    (-1.10, 1.150), (-0.70, 1.105), (-0.10, 1.082), (0.60, 1.066), (0.98, 1.060),
    (1.20, 1.066), (1.54, 1.036), (1.90, 0.960), (2.15, 0.885), (2.30, 0.825), (HALF_L, 0.760),
])

HOOD_ROLL = 0.080
HOOD_CROWN = 0.134

# Rail height relative to the centreline: the roof has a gentle ~4.2-4.6 cm crown across its width
# (matching the side, front and front-3/4 studio photographs; the earlier -0.100 drop sagged the
# A-pillar and header 6 cm below the photograph's outline).
Z_CREST = Curve([
    (-HALF_L, -0.040), (-2.20, -0.042), (-1.93, -0.045), (-1.40, -0.046),
    (-0.90, -0.046), (-0.50, -0.045), (0.40, -0.042), (0.80, -0.036), (COWL_X, -0.012),
] + [(x, -HOOD_CROWN * (Z_ROOF(x) - Z_SHOULDER(x)))
     for x in (1.40, 1.60, 1.80, 2.00, 2.20, 2.30, HALF_L)])

# 2026-11-16 refit: the painted flank was 0.85-0.89 from the centreline (a 1.80 m wide car, the
# published width 1.93) and black flares stood 6-7 cm proud of it to carry the car out to the
# tyres' walls (0.957). The front and rear photographs' outlines put the painted fender flush with
# the tyre, so the hips now reach 0.955 over the axles and 0.94 between them, and the flares
# (zx_side) became a flush trim. The nose and tail ends are as they were.
Y_HIP = Curve([
    (-HALF_L, 0.775), (-2.30, 0.860), (-2.00, 0.915), (-1.70, 0.942), (-1.38, 0.955),
    (-0.70, 0.945), (0.0, 0.940), (0.80, 0.945), (1.20, 0.950), (1.54, 0.955),
    (2.00, 0.935), (2.25, 0.895), (HALF_L, 0.800),
])
Y_SHOULDER = Curve([
    (-HALF_L, 0.640), (-2.30, 0.730), (-2.00, 0.775), (-1.40, 0.810), (-0.70, 0.850),
    (0.0, 0.860), (0.80, 0.845), (1.20, 0.838), (1.54, 0.835), (1.90, 0.835),
    (2.15, 0.805), (2.28, 0.760), (HALF_L, 0.690),
])
# Roof rail half-width: solved across the windscreen (0.43..1.12) so the A-pillar's outer and inner
# edges follow a smooth convex arc in plan matching the front and side studio photographs, and ahead
# of the cowl lies inside Y_SHOULDER so the fender crown rolls cleanly into the hood without folding.
Y_ROOF = Curve([
    (-HALF_L, 0.560), (-2.20, 0.610), (-1.90, 0.620), (-1.40, 0.618), (-0.50, 0.618),
    (0.00, 0.624), (0.30, 0.638), (0.43, 0.654), (0.55, 0.672), (0.65, 0.688),
    (0.75, 0.705), (0.85, 0.722), (0.98, 0.745), (1.05, 0.758), (1.12, 0.772),
    (COWL_X, 0.785),
] + [(x, Y_SHOULDER(x) - 0.5 * HOOD_ROLL) for x in (1.40, 1.60, 1.80, 2.00, 2.15, 2.28, HALF_L)])
Y_ROCKER = Curve([
    (-HALF_L, 0.700), (-2.20, 0.800), (-1.75, 0.900), (-1.38, 0.950), (-1.00, 0.925),
    (-0.70, 0.895), (0.00, 0.885), (0.80, 0.890), (1.20, 0.915), (1.54, 0.950),
    (1.95, 0.925), (2.10, 0.885), (2.30, 0.830), (HALF_L, 0.740),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-1.95, 0.0), (-1.20, 0.014), (-0.70, 0.024),
    (0.40, 0.024), (0.85, 0.012), (1.30, 0.0), (HALF_L, 0.0),
], mode="pchip")


# ------------------------------------------------------------------ the loft
def SECTION_AT(x):
    """Section constants ahead of the cowl (matching G9L and ES8): the greenhouse recipe's step and
    tumble lean the glass in above the beltline crease, which ahead of the cowl folded the fender
    back on itself under the hood's edge. Ahead of x = 1.10 the section transitions to a quarter-ellipse
    roll from the flat hood top into the fender crown."""
    t = _smooth((x - 1.10) / 0.25)
    if t <= 0.0:
        return None
    lerp = lambda a, b: a + (b - a) * t
    k0 = (0.40, 0.60, 0.52, 0.40)
    k1 = (0.732, 0.268, 0.50, 0.0)
    return dict(step_in=lerp(0.030, 0.003), step_max=lerp(0.028, 0.014),
                shoulder_below_roof=lerp(0.045, 0.024),
                tumble=tuple(lerp(a, b) for a, b in zip(k0, k1)),
                rail_in=lerp(0.52, 0.931), rail_crest=lerp(0.34, 0.45))


BODY = LoftBody(
    name="Zeekr 7X", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.130, core_z=0.72, crease="soft",
    section=Section(step_in=0.030, step_max=0.028, tumble=(0.40, 0.60, 0.52, 0.40)),
    section_at=SECTION_AT,
    smooth_v=True,
)

z_rocker = BODY.z_rocker
section = BODY.section
section_v = BODY.section_v
surface = BODY.surface
arch_top_z = BODY.arch_top_z
arch_v = BODY.arch_v
upper_length = BODY.upper_length
v_rail = BODY.v_rail
v_along = BODY.v_along
v_at_y_upper = BODY.v_at_y_upper
v_at_z = BODY.v_at_z
nearest_on_section = BODY.nearest_on_section
surface_normal = BODY.surface_normal
surface_offset = BODY.surface_offset
dims_report = BODY.dims_report
