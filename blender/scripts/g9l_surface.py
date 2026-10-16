"""XPeng G9L body surface - the profile curves of its flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module is the G9L's DATA: its
dimensions and the profile curves every section is built from, fitted to the camera-matched
photographs (g9l_ref_match.py; the blocks between `fit:` markers are rewritten by
g9l_fit.py, which compares the model's outline through each photo's camera with the
photograph's outline and moves the knots).

Real dimensions (Autohome spec table, MIIT filing, XPeng): 5120 x 1999 x 1782 mm, wheelbase
3100 mm, track 1725 front / 1749 rear, tyres 265/40 R22 on the 755 Ultra (255/50 R20 and
265/45 R21 are the options: the photographed car wears the 22 in "Aero" five-spoke), overhangs
910 / 1110 mm (the side photograph's nose and tail through its camera give 0.92 / 1.11).

What makes a G9L, from the photographs:
  - a long, level roof (peak 1.782 at x -0.45, 1.69 at the spoiler) over a tall slab flank:
    the beltline rises from 1.21 at the A-pillar's foot to 1.35 at the quarter glass's tip
  - a raked windscreen (34 degrees) and a bonnet at 1.23 / 1.15 rolling over the lamp bar
    onto a blunt, nearly flat front face
  - a raked backlight under a roof spoiler, a short upright tailgate, an air-vented bumper

    S(x, v)   x = station along the car in metres, +X forward, centre of the car at x = 0
              v = 0 at the underbody centreline, 1 at the roof centreline, V_SHOULDER at
                  the crease
"""
from carkit.geom import Curve, Joined
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.120, 1.999, 1.795
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
WHEELBASE = 3.100
FRONT_OVERHANG = 0.910
REAR_OVERHANG = LENGTH - WHEELBASE - FRONT_OVERHANG  # 1.110
FRONT_AXLE = HALF_L - FRONT_OVERHANG                 # 1.650
REAR_AXLE = FRONT_AXLE - WHEELBASE                   # -1.450
WHEEL_R = 0.377                                      # loaded hub height: 265/40 R22 (0.3854 free), 8 mm of sag
TRACK_F, TRACK_R = 1.725, 1.749
ARCH_R = 0.445                                       # painted opening radius (c1_0028: the arch crown at z 0.82)

V_SHOULDER = 0.520

COWL_X = 1.200                                       # windscreen base
KNEE_X = -1.970                                      # roof spoiler's trailing edge
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# fit:roof  (x, z) of the top centreline: tail, roof + windscreen, bonnet
TAIL_PTS = [
    (-2.560, 1.180), (-2.545, 1.265), (-2.480, 1.320), (-2.400, 1.385), (-2.320, 1.445),
    (-2.240, 1.505), (-2.160, 1.565), (-2.080, 1.620), (-2.020, 1.665), (KNEE_X, 1.705),
]
ROOF_PTS = [
    (KNEE_X, 1.705), (-1.900, 1.715), (-1.700, 1.738), (-1.500, 1.757), (-1.300, 1.773),
    (-1.100, 1.787), (-0.900, 1.797), (-0.700, 1.802), (-0.500, 1.805), (-0.300, 1.803),
    (-0.100, 1.798), (0.100, 1.789), (0.250, 1.775), (0.400, 1.742), (0.600, 1.640),
    (0.800, 1.508), (1.000, 1.372), (1.100, 1.300), (COWL_X, 1.262),
]
HOOD_PTS = [
    (COWL_X, 1.255), (1.400, 1.240), (1.600, 1.232), (1.800, 1.216), (2.000, 1.190),
    (2.100, 1.176), (2.200, 1.158), (2.300, 1.135), (2.400, 1.100), (2.480, 1.040),
    (2.540, 0.960), (HALF_L, 0.900),
]
# /fit:roof
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve(TAIL_PTS), Curve(ROOF_PTS)), Curve(HOOD_PTS))

# Underbody centreline:
Z_FLOOR = Curve([
    (-HALF_L, 0.296), (-2.439, 0.269), (-2.223, 0.239), (-2.008, 0.221),
    (-1.447, 0.215), (0.015, 0.213), (1.647, 0.215), (2.076, 0.224),
    (2.338, 0.239), (2.505, 0.258), (HALF_L, 0.282),
])

# Hip / widest point height:
Z_HIP = Curve([
    (-HALF_L, 0.640), (-2.331, 0.720), (-2.008, 0.760), (-1.447, 0.770),
    (-0.727, 0.770), (0.015, 0.765), (0.863, 0.760), (1.287, 0.750),
    (1.647, 0.730), (2.128, 0.690), (2.390, 0.640), (HALF_L, 0.580),
])

# Shoulder / beltline height: the belt (the glass's lower edge and the doors' top, read in
# g9l_cam.BELT_PX: 1.196 at the cowl, 1.235 at the split, 1.293 at the rear door's edge, 1.353 at
# the quarter glass's tip) less 40 mm for the crease under the step. Ahead of the cowl it is the
# fender's top (the hood's side line: z 1.13 at x 1.5, 1.054 at 2.03, 1.03 at the lamp's end).
Z_SHOULDER = Curve([
    (-HALF_L, 1.150), (-2.400, 1.225), (-2.040, 1.322), (-1.820, 1.313), (-1.570, 1.284),
    (-1.200, 1.250), (-0.810, 1.222), (-0.030, 1.195), (0.590, 1.171), (1.100, 1.156),
    (1.400, 1.120), (1.750, 1.065), (2.050, 1.015), (2.300, 0.965), (2.500, 0.920), (HALF_L, 0.890),
])

# Roof crest offset (rail height under the centreline):
Z_CREST = Curve([
    (-HALF_L, -0.040), (-2.331, -0.050), (-2.040, -0.050), (-1.469, -0.045),
    (-0.515, -0.040), (0.439, -0.040), (0.863, -0.040), (COWL_X, -0.020),
    (1.710, -0.015), (2.128, -0.010), (2.442, 0.0), (HALF_L, 0.0),
])

# Lateral widths (half). The photographs' outlines from front and rear: the widest section
# (0.9995) runs from the rear wheel arch's front edge to the front arch; the nose face is 1.64
# wide and the tailgate 1.55 wide at lamp height, so both ends turn in on big radii.
Y_HIP = Curve([
    (-HALF_L, 0.620), (-2.500, 0.800), (-2.400, 0.900), (-2.300, 0.940), (-2.100, 0.980),
    (-1.900, 0.995), (-1.600, 0.9995), (-0.727, 0.9995), (0.015, 0.9995), (0.863, 0.9970),
    (1.287, 0.9900), (1.647, 0.9800), (1.950, 0.9700), (2.100, 0.9550), (2.200, 0.9350),
    (2.300, 0.9100), (2.400, 0.8700), (2.500, 0.8000), (HALF_L, 0.620),
])

# The shoulder narrows hard over the rear quarter (the sail leans in: the rear photograph's body edge
# at the belt's height is 0.77 half-wide at x -2.0, against 0.9995 at the hip).
Y_SHOULDER = Curve([
    (-HALF_L, 0.560), (-2.500, 0.690), (-2.400, 0.742), (-2.200, 0.775), (-2.000, 0.805),
    (-1.800, 0.845), (-1.500, 0.900), (-1.200, 0.945), (-0.800, 0.965), (-0.727, 0.968),
    (0.015, 0.972), (0.863, 0.965), (1.287, 0.950), (1.647, 0.935), (1.950, 0.920),
    (2.100, 0.905), (2.200, 0.885), (2.300, 0.860), (2.400, 0.820), (2.500, 0.750),
    (HALF_L, 0.600),
])

Y_ROOF = Curve([
    (-HALF_L, 0.540), (-2.500, 0.590), (-2.330, 0.650), (-2.040, 0.700), (-1.450, 0.735),
    (-0.500, 0.760), (0.333, 0.770), (0.863, 0.790), (COWL_X, 0.850),
    (1.605, 0.880), (2.128, 0.860), (2.442, 0.760), (HALF_L, 0.560),
])

Y_ROCKER = Curve([
    (-HALF_L, 0.650), (-2.500, 0.800), (-2.331, 0.900), (-1.684, 0.950), (-0.727, 0.965),
    (0.015, 0.970), (0.863, 0.970), (1.647, 0.965), (2.233, 0.925),
    (2.442, 0.850), (HALF_L, 0.640),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-2.062, 0.0), (-1.257, 0.015), (-0.727, 0.025),
    (0.439, 0.025), (0.916, 0.012), (1.393, 0.0), (HALF_L, 0.0),
], mode="pchip")

# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="XPeng G9L", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.140, core_z=0.78, crease="soft",
    section=Section(step_in=0.032, step_max=0.030, tumble=(0.38, 0.58, 0.50, 0.38)),
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
