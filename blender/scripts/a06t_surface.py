"""Avatr 06T body surface - the profile curves of its shooting-brake flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module defines
the Avatr 06T's exact dimensions and profile curves calibrated against the
Autohome 3600x2700 white-studio turnaround photos (c1_0001..c1_0007.jpg) and
official Avatr 06T studio renders (avatr.com/en/06T).

Real dimensions (Avatr official & MIIT 2026):
  - Length x Width x Height: 4940 x 1960 x 1455 mm (1475 mm on coil suspension; the photographed
    car stands at 1.50 m to the roof, 1.52 m over the rails)
  - Wheelbase: 2940 mm (overhangs measured off the silhouette: 900 mm front, 1100 mm rear)
  - Track: 1676 mm front / 1680 mm rear
  - Tyres: 255/45 R20 (OD 738 mm, loaded radius 0.365 m) or 255/40 R21

What makes an Avatr 06T, read off the side photograph c1_0004 through the solved camera (a06t_cam.py):
  - A low, wide-shouldered shooting brake (4.94 x 1.96 m, roof rails 1.52 m with the roof LiDAR) on a
    2.94 m wheelbase, cab-forward: 0.90 m front overhang, 1.10 m rear, the windscreen's base (cowl) at
    x 1.12 only 0.45 m behind the front axle
  - A short, low nose: the bonnet's centreline falls from the cowl to the nose cap's top edge (x 2.33,
    z 0.76) with a faint central crease; the lamps wrap the corners
  - A raked panoramic windscreen, a long roof (peak 1.503 m) and a raked backlight from the knee
    (x -1.95, z 1.33) down to the tail cap (x -2.33, z 1.09)
  - Taut, nearly flat flanks with a black rocker, tight painted arches and a narrow cabin that tucks
    in above the rear haunches
Everything the photographs do not fix (section shapes) is smooth and plain.
"""
from carkit.geom import Curve, Joined          # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 4.940, 1.960, 1.520
HALF_L = LENGTH / 2.0                        # 2.470
HALF_W = WIDTH / 2.0                         # 0.980
FRONT_OVERHANG = 0.900
FRONT_AXLE = HALF_L - FRONT_OVERHANG         # 1.570
REAR_AXLE = FRONT_AXLE - 2.940               # -1.370 (rear overhang 1.100 m)
WHEEL_R = 0.365                              # 255/45 R20 loaded radius
ARCH_R = 0.415                               # painted wheel opening (0.05 m over the tyre)

V_SHOULDER = 0.520

COWL_X = 1.120
KNEE_X = -1.950                              # the roof's end: the backlight starts here
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# All read from the side photograph c1_0004 through the solved camera (a06t_cam.py): the centreline
# silhouette gives the hood and windscreen, the rails' top minus the rail height gives the roof.
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # the glass's surface: a long shallow rake (~30 degrees) from the tailgate's top edge at x -2.33,
    # z 1.093 up under the roof's rear end (the spoiler overhangs it); c1_0004's black wedge edge
    (-HALF_L, 0.995), (-2.42, 1.003), (-2.39, 1.025), (-2.36, 1.060), (-2.33, 1.093),
    (-2.28, 1.123), (-2.21, 1.165), (-2.14, 1.207), (-2.07, 1.248), (-2.00, 1.292),
    (KNEE_X, 1.331),
]), Curve([
    # roof: peaks at 1.503 over the front seats (rail tops 1.516-1.527 in the photo), falls
    # to the spoiler; windscreen on the silhouette (x 0.42..1.12, rake 26 degrees)
    (KNEE_X, 1.331), (-1.92, 1.337), (-1.85, 1.349), (-1.77, 1.360), (-1.70, 1.369),
    (-1.62, 1.378), (-1.55, 1.392), (-1.47, 1.414), (-1.33, 1.442), (-1.18, 1.462),
    (-1.03, 1.478), (-0.88, 1.490), (-0.73, 1.496), (-0.58, 1.500), (-0.43, 1.503),
    (-0.28, 1.500), (-0.13, 1.494), (0.00, 1.482), (0.15, 1.452), (0.30, 1.412),
    (0.42, 1.368), (0.49, 1.331), (0.57, 1.298), (0.65, 1.263), (0.72, 1.222),
    (0.80, 1.184), (0.88, 1.145), (0.96, 1.102), (1.03, 1.058), (COWL_X, 1.015),
])), Curve([
    # hood centreline: the fender crowns stand 2 cm over it (Z_CREST), so this is the photo's
    # silhouette minus that
    (COWL_X, 1.015), (1.27, 0.986), (1.42, 0.972), (1.58, 0.958), (1.73, 0.944),
    (1.89, 0.921), (2.05, 0.887), (2.20, 0.838), (2.36, 0.757), (HALF_L, 0.665),
]))

# Underbody: the rocker's lower edge is z 0.216 (front) .. 0.23 (rear) in the photo
Z_FLOOR = Curve([
    (-HALF_L, 0.275), (-2.40, 0.262), (-2.25, 0.246), (-2.05, 0.232), (-1.75, 0.224),
    (REAR_AXLE, 0.221), (-0.60, 0.220), (0.0, 0.218), (0.80, 0.212), (FRONT_AXLE, 0.207),
    (1.90, 0.200), (2.15, 0.198), (2.35, 0.195), (HALF_L, 0.205),
])

# Hip line (widest point of the body flank)
Z_HIP = Curve([
    (-HALF_L, 0.580), (-2.15, 0.640), (-1.80, 0.700), (REAR_AXLE, 0.735),
    (-0.70, 0.755), (0.0, 0.765), (0.82, 0.765), (FRONT_AXLE, 0.765),
    (2.05, 0.710), (HALF_L, 0.620),
])

# Shoulder crease: the door surface turns up into the glass; sweeps down over the front arch
Z_SHOULDER = Curve([
    (-HALF_L, 0.955), (-2.30, 0.980), (-2.05, 1.008), (-1.75, 1.028),
    (REAR_AXLE, 1.040), (-1.15, 1.036), (-0.80, 1.015), (-0.40, 0.998),
    (0.00, 0.990), (0.40, 0.985), (0.80, 0.978), (COWL_X, 0.958), (1.40, 0.945),
    (FRONT_AXLE, 0.930), (1.85, 0.895), (2.15, 0.830), (2.32, 0.780),
    (HALF_L, 0.725),
])

# Crown of the roof / backlight and front fender tops relative to Z_ROOF
Z_CREST = Joined(COWL_X, Joined(-1.75, Curve([
    (-HALF_L, -0.052), (-2.35, -0.062), (-2.20, -0.066), (-2.05, -0.058),
    (-1.95, -0.042), (-1.85, -0.026), (-1.75, -0.018),
], mode="pchip"), Curve([
    (-HALF_L, 0.000), (-1.96, -0.012), (-1.60, -0.016), (-1.10, -0.016),
    (-0.50, -0.015), (0.00, -0.015), (0.42, -0.024), (0.80, -0.018),
    (COWL_X, 0.000),
])), Curve([
    # front fender crowns above the hood's centre
    (COWL_X, 0.000), (1.30, 0.016), (1.50, 0.022), (1.70, 0.024),
    (1.95, 0.020), (2.20, 0.010), (2.35, 0.003), (HALF_L, 0.000),
]))

# A faint power dome either side of the hood's centre (the photographs show a broad, taut hood
# with two soft ridges running back from the lamps' upper tips)
Z_DOME = Curve([
    (-HALF_L, 0.000), (COWL_X, 0.000), (1.30, 0.005), (1.55, 0.009),
    (1.85, 0.010), (2.05, 0.006), (2.25, 0.000), (HALF_L, 0.000),
], mode="pchip")

Y_DOME = Curve([
    (-HALF_L, 0.600), (COWL_X, 0.560), (1.40, 0.520), (1.75, 0.480),
    (2.05, 0.430), (2.25, 0.380), (HALF_L, 0.340),
])

# Half-widths: 1960 mm over the rear haunches; broad front fenders
Y_HIP = Curve([
    (-HALF_L, 0.805), (-2.38, 0.865), (-2.20, 0.910), (-1.95, 0.948),
    (-1.68, 0.955), (REAR_AXLE, 0.962), (-1.10, 0.955), (-0.65, 0.945),
    (0.00, 0.945), (0.60, 0.952), (1.15, 0.967), (FRONT_AXLE, 0.975),
    (1.85, 0.968), (2.05, 0.938), (2.24, 0.880), (2.36, 0.820),
    (HALF_L, 0.730),
])

# Shoulder half-width: tucked in over the rear haunches
Y_SHOULDER = Curve([
    (-HALF_L, 0.650), (-2.32, 0.715), (-2.15, 0.765), (-1.90, 0.805),
    (-1.65, 0.800), (REAR_AXLE, 0.806), (-1.15, 0.822), (-0.65, 0.850), (0.00, 0.875),
    (0.60, 0.885), (COWL_X, 0.905), (FRONT_AXLE, 0.930), (1.95, 0.912),
    (2.22, 0.860), (HALF_L, 0.785),
])

# Roof rail half-width (to x -2.0), the A-pillar's sweep out to the cowl, then the fender crown
Y_ROOF = Curve([
    (-HALF_L, 0.530), (-2.35, 0.535), (-2.05, 0.515), (-1.75, 0.530),
    (-1.35, 0.555), (-0.95, 0.575), (-0.50, 0.595), (0.00, 0.602),
    (0.30, 0.650), (0.45, 0.692), (0.60, 0.728), (0.80, 0.772), (1.00, 0.802),
    (COWL_X, 0.815), (1.30, 0.800), (1.65, 0.795), (2.05, 0.765), (2.32, 0.700),
    (HALF_L, 0.625),
])

# Greenhouse base half-width: the broad rear haunch deck under the quarter window and C-pillar
Y_GLASS = Curve([
    (-HALF_L, 1.200), (-2.38, 1.200), (-2.18, 0.715), (-1.95, 0.700),
    (-1.70, 0.700), (-1.42, 0.705), (-1.15, 0.735), (-0.90, 0.790),
    (-0.65, 0.845), (-0.40, 1.200), (HALF_L, 1.200),
], mode="pchip")

Z_STEP = Curve([
    (-HALF_L, 0.028), (-2.25, 0.042), (-2.00, 0.064), (-1.70, 0.066),
    (-1.42, 0.062), (-1.15, 0.042), (-0.90, 0.028), (HALF_L, 0.028),
], mode="pchip")
SOFT = Curve([(-HALF_L, 1.0), (-1.42, 1.0), (-0.90, 0.0), (HALF_L, 0.0)], mode="pchip")

Y_ROCKER = Curve([
    (-HALF_L, 0.780), (-2.25, 0.865), (-1.95, 0.905), (REAR_AXLE, 0.920),
    (-1.00, 0.922), (0.00, 0.925), (1.00, 0.920), (FRONT_AXLE, 0.915),
    (1.95, 0.910), (2.15, 0.885), (2.30, 0.845), (HALF_L, 0.770),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-1.85, 0.0), (-1.10, 0.016), (-0.60, 0.028),
    (0.45, 0.028), (0.90, 0.014), (1.35, 0.0), (HALF_L, 0.0),
], mode="pchip")


# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="Avatr 06T", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.110, core_z=0.66, crease="sharp", z_dome=Z_DOME, y_dome=Y_DOME,
    y_glass=Y_GLASS, z_step=Z_STEP, soft=SOFT,
    section=Section(step_in=0.046, step_max=0.028, tumble=(0.36, 0.64, 0.52, 0.40),
                    dome_groove=0.40, dome_flank=(0.76, 0.22)),
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
