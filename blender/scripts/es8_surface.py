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

V_SHOULDER = 0.520
COWL_X = 1.320               # base of windshield
KNEE_X = -2.180              # roof spoiler trailing edge (SUV full-length roof)
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------------- silhouette (Z)
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # SUV raked backlight from roof spoiler lip (-2.180, z=1.640) directly to tail lightbar shelf (-2.640, z=1.115)
    (-HALF_L, 1.115), (-2.550, 1.165), (-2.460, 1.265), (-2.360, 1.395),
    (-2.260, 1.530), (KNEE_X, 1.640),
]), Curve([
    # Long, majestic 3-row SUV roof crown (peaking at 1.800 m) + smooth 30-deg windshield down to cowl (1.320, z=1.120)
    (KNEE_X, 1.640), (-2.120, 1.695), (-2.020, 1.728), (-1.850, 1.752),
    (-1.550, 1.775), (-1.150, 1.790), (-0.650, 1.798), (-0.250, 1.800),
    (0.150, 1.792), (0.420, 1.770), (0.550, 1.740), (0.680, 1.655),
    (0.840, 1.525), (1.000, 1.385), (1.160, 1.245), (1.280, 1.145),
    (COWL_X, 1.120),
])), Curve([
    # Clamshell hood from cowl (+1.320, z=1.120) forward to Shark-Nose X-Bar apex (+2.640)
    (COWL_X, 1.120), (1.480, 1.108), (1.720, 1.090), (1.960, 1.062),
    (2.180, 1.025), (2.360, 0.978), (2.480, 0.935), (HALF_L, 0.875),
]))

Z_FLOOR = Curve([
    (-HALF_L, 0.310), (-2.450, 0.268), (-2.150, 0.228),
    (REAR_AXLE, 0.212), (-1.100, 0.198), (0.000, 0.195),
    (1.100, 0.198), (FRONT_AXLE, 0.212), (2.150, 0.225),
    (2.450, 0.245), (HALF_L, 0.268),
])

Z_HIP = Curve([
    (-HALF_L, 0.660), (-2.350, 0.760), (-1.950, 0.805),
    (REAR_AXLE, 0.810), (-0.800, 0.790), (0.000, 0.770),
    (0.900, 0.750), (COWL_X, 0.735), (FRONT_AXLE, 0.720),
    (2.150, 0.660), (2.450, 0.610), (HALF_L, 0.560),
])

# Signature Nio ES8 horizontal 16 mm belt/shoulder line ("宽舷肩线")
Z_SHOULDER = Curve([
    (-HALF_L, 1.060), (-2.400, 1.100), (-2.050, 1.140),
    (REAR_AXLE, 1.135), (-0.800, 1.125), (0.000, 1.115),
    (0.850, 1.105), (COWL_X, 1.085), (FRONT_AXLE, 1.050),
    (2.050, 0.990), (2.380, 0.935), (HALF_L, 0.865),
])

Z_CREST = Curve([
    (-HALF_L, -0.045), (-2.350, -0.065), (KNEE_X, -0.085),
    (-1.400, -0.090), (-0.400, -0.092), (0.450, -0.088),
    (0.900, -0.068), (COWL_X, -0.032), (1.800, -0.030),
    (2.300, -0.025), (HALF_L, 0.000),
])

Y_HIP = Curve([
    (-HALF_L, 0.760), (-2.420, 0.855), (-2.100, 0.920),
    (REAR_AXLE, 0.935), (-0.800, 0.935), (0.000, 0.940),
    (0.900, 0.935), (COWL_X, 0.920), (FRONT_AXLE, 0.915),
    (2.100, 0.915), (2.420, 0.885), (HALF_L, 0.800),
])

Y_SHOULDER = Curve([
    (-HALF_L, 0.680), (-2.400, 0.765), (-2.050, 0.815),
    (REAR_AXLE, 0.855), (-0.800, 0.885), (0.000, 0.895),
    (0.850, 0.880), (COWL_X, 0.850), (FRONT_AXLE, 0.835),
    (2.100, 0.805), (2.420, 0.765), (HALF_L, 0.690),
])

Y_ROOF = Curve([
    (-HALF_L, 0.570), (-2.400, 0.580), (KNEE_X, 0.595),
    (-1.600, 0.625), (-0.600, 0.650), (0.350, 0.660),
    (0.850, 0.715), (COWL_X, 0.815), (1.650, 0.845),
    (2.150, 0.820), (2.450, 0.765), (HALF_L, 0.680),
])

Y_ROCKER = Curve([
    (-HALF_L, 0.730), (-2.350, 0.825), (-1.750, 0.895),
    (-0.800, 0.920), (0.000, 0.925), (0.850, 0.920),
    (FRONT_AXLE, 0.910), (2.150, 0.880), (2.420, 0.835), (HALF_L, 0.740),
], mode="pchip")

UNDERCUT = Curve([
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
    section=Section(step_in=0.028, step_max=0.026, tumble=(0.38, 0.58, 0.50, 0.38)),
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
