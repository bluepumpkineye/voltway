"""Nio ES8 parametric flank surface: a carkit.body.LoftBody configured with the
third-generation Nio ES8 (NT3.0, 5280 x 2010 x 1800 mm, 3130 mm wheelbase) profile,
plan, and cross-section laws.

Dimensions from https://www.nio.cn/es8:
  Length:    5280 mm  ->  x in [-2.640, +2.640]
  Width:     2010 mm  ->  y in [-1.005, +1.005]
  Height:    1800 mm  ->  z in [ 0.000,  1.800]
  Wheelbase: 3130 mm  ->  axles at x = +/- 1.565
  Track:     1720 mm (front) / 1733 mm (rear)
  Tyres:     265/40 R22 (OD 771 mm -> R = 0.385 m)

Second pass (2026-10-30): laid over the maker's side render (blender/reference/nio-es8/official/color_white.jpg, the one
level, long-lens picture: its wheelbase and height agree with the published 3130 and 1800 to 1 %) and over the Autohome
showroom photographs (series 4427, spec 74331, c1_0034), the first build read as an estate: its nose stood 0.25 m too far
forward (the render's front overhang is 0.83 m, ours was 1.08; the tail agrees to 1 cm), its hood 8 to 10 cm low, its
windscreen steeper (39 against 31 degrees) with the base 0.12 m too far forward, its roof flat and 5 to 10 cm too high over
the front seats, and its beltline 8 cm low, so the glass was a tall band over a shallow body. The numbers below are read off
that render (scale from the wheels and the height, 362 px/m). The published 5280 mm length is not what the photographs show
(they put the car at about 5.05 m for a 3130 mm wheelbase); the build follows the photographs.
"""
from carkit.geom import Curve, Joined
from carkit.body import LoftBody
from carkit.body.loft import Section

# ------------------------------------------------------------------ dimensions
LENGTH, WIDTH, HEIGHT = 5.280, 2.010, 1.800
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
WHEELBASE = 3.130
AXLE_X = 1.565
FRONT_AXLE = 1.565
REAR_AXLE = -1.565

WHEEL_R = 0.385
TYRE_W = 0.265
TRACK_F, TRACK_R = 1.720, 1.733
ARCH_R = 0.485

# The nose stands 0.83 m ahead of the front axle (the build had 1.075). Everything ahead of the front wheelhouse is
# squeezed in x: a point at x > X_SQ goes to X_SQ + (x - X_SQ) * K_SQ, so the front-most point (HALF_L) lands on X_FRONT.
X_FRONT = 2.400
X_SQ = 2.050
K_SQ = (X_FRONT - X_SQ) / (HALF_L - X_SQ)


def fx(x):
    return x if x <= X_SQ else X_SQ + (x - X_SQ) * K_SQ


def FC(points, **kw):
    """A Curve whose points ahead of the wheelhouse are squeezed by fx."""
    return Curve([(fx(x), z) for (x, z) in points], **kw)


V_SHOULDER = 0.520
COWL_X = 1.200               # base of windshield (the render: the hood meets the screen at x 1.15 to 1.2, z 1.22)
KNEE_X = -2.180              # roof spoiler trailing edge (SUV full-length roof)
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------------- silhouette (Z)
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # the backlight, from the roof spoiler's lip down to the tail lightbar shelf; read off the render (the glass runs
    # ~0.06 m further back than the first build's, the bumper end is where it was)
    (-HALF_L, 1.115), (-2.600, 1.170), (-2.550, 1.235), (-2.470, 1.330),
    (-2.390, 1.440), (-2.310, 1.570), (-2.240, 1.660), (KNEE_X, 1.700),
]), Curve([
    # the roof crowns gently from the screen header (z 1.67 at x 0.42) to its peak (1.80, x -0.65 to -0.95) and falls
    # to the spoiler; then the screen at 31 degrees to the cowl (1.20, z 1.222)
    (KNEE_X, 1.700), (-2.100, 1.725), (-2.000, 1.738), (-1.850, 1.756),
    (-1.550, 1.780), (-1.250, 1.796), (-0.950, 1.802), (-0.650, 1.802),
    (-0.350, 1.796), (-0.050, 1.774), (0.150, 1.745), (0.300, 1.716),
    (0.420, 1.665), (0.550, 1.585), (0.650, 1.535), (0.750, 1.480),
    (0.850, 1.424), (0.950, 1.364), (1.050, 1.300), (1.120, 1.255),
    (COWL_X, 1.222),
])), Curve([
    # the hood: flat from the cowl, rolling over at the nose (z 0.95 at the front-most point, X_FRONT)
    (COWL_X, 1.222), (1.350, 1.206), (1.500, 1.196), (1.650, 1.182),
    (1.800, 1.166), (1.950, 1.146), (2.050, 1.124), (2.150, 1.094),
    (2.250, 1.050), (2.330, 1.000), (X_FRONT, 0.950), (2.500, 0.900), (HALF_L, 0.840),
]))

Z_FLOOR = FC([
    (-HALF_L, 0.310), (-2.450, 0.268), (-2.150, 0.228),
    (REAR_AXLE, 0.212), (-1.100, 0.198), (0.000, 0.195),
    (1.100, 0.198), (FRONT_AXLE, 0.212), (2.150, 0.225),
    (2.450, 0.245), (HALF_L, 0.268),
])

Z_HIP = FC([
    (-HALF_L, 0.660), (-2.350, 0.760), (-1.950, 0.805),
    (REAR_AXLE, 0.810), (-0.800, 0.790), (0.000, 0.770),
    (0.900, 0.750), (COWL_X, 0.735), (FRONT_AXLE, 0.720),
    (2.150, 0.660), (2.450, 0.610), (HALF_L, 0.560),
])

# Signature Nio ES8 horizontal 16 mm belt/shoulder line ("宽舷肩线")
# (the front half follows the higher hood: shoulder = hood - 0.045, as the first build had it)
Z_SHOULDER = Curve([
    (-HALF_L, 1.060), (-2.400, 1.100), (-2.050, 1.140),
    (REAR_AXLE, 1.135), (-0.800, 1.125), (0.000, 1.115),
    (0.850, 1.115), (COWL_X, 1.177), (FRONT_AXLE, 1.143),
    (2.050, 1.079), (2.250, 1.005), (2.330, 0.955), (X_FRONT, 0.905),
    (2.500, 0.860), (HALF_L, 0.800),
])

Z_CREST = FC([
    (-HALF_L, -0.045), (-2.350, -0.065), (KNEE_X, -0.085),
    (-1.400, -0.090), (-0.400, -0.092), (0.450, -0.088),
    (0.900, -0.068), (COWL_X, -0.032), (1.800, -0.030),
    (2.300, -0.025), (HALF_L, 0.000),
])

Y_HIP = FC([
    (-HALF_L, 0.760), (-2.420, 0.855), (-2.100, 0.920),
    (REAR_AXLE, 0.935), (-0.800, 0.935), (0.000, 0.940),
    (0.900, 0.935), (COWL_X, 0.920), (FRONT_AXLE, 0.915),
    (2.100, 0.915), (2.420, 0.885), (HALF_L, 0.800),
])

Y_SHOULDER = FC([
    (-HALF_L, 0.680), (-2.400, 0.765), (-2.050, 0.815),
    (REAR_AXLE, 0.855), (-0.800, 0.885), (0.000, 0.895),
    (0.850, 0.880), (COWL_X, 0.850), (FRONT_AXLE, 0.835),
    (2.100, 0.805), (2.420, 0.765), (HALF_L, 0.690),
])

Y_ROOF = FC([
    (-HALF_L, 0.570), (-2.400, 0.580), (KNEE_X, 0.595),
    (-1.600, 0.625), (-0.600, 0.650), (0.350, 0.660),
    (0.850, 0.715), (COWL_X, 0.815), (1.650, 0.800),
    (2.150, 0.760), (2.350, 0.710), (2.450, 0.650), (HALF_L, 0.580),
])

Y_ROCKER = FC([
    (-HALF_L, 0.730), (-2.350, 0.825), (-1.750, 0.895),
    (-0.800, 0.920), (0.000, 0.925), (0.850, 0.920),
    (FRONT_AXLE, 0.910), (2.150, 0.880), (2.420, 0.835), (HALF_L, 0.740),
], mode="pchip")

UNDERCUT = FC([
    (-HALF_L, 0.000), (-2.100, 0.000), (-1.250, 0.015),
    (-0.650, 0.024), (0.450, 0.024), (1.000, 0.012),
    (1.400, 0.000), (HALF_L, 0.000),
], mode="pchip")

# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="Nio ES8", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.135, core_z=0.75, crease="soft",
    section=Section(step_in=0.008, step_max=0.015, tumble=(0.50, 0.50, 0.50, 0.38)),
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
