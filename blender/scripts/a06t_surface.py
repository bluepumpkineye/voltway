"""Avatr 06T body surface - the profile curves of its shooting-brake flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module defines
the Avatr 06T's exact dimensions and profile curves calibrated against the
Autohome 3600x2700 white-studio turnaround photos (c1_0001..c1_0007.jpg) and
official Avatr 06T studio renders (avatr.com/en/06T).

Real dimensions (Avatr official & MIIT 2026):
  - Length x Width x Height: 4940 x 1960 x 1455 mm (Air Suspension stance;
    1475 mm on coil suspension / over roof rails)
  - Wheelbase: 2940 mm (front overhang 950 mm, rear overhang 1050 mm)
  - Track: 1676 mm front / 1680 mm rear
  - Tyres: 255/45 R20 (OD 738 mm, loaded radius 0.365 m) or 255/40 R21

What makes an Avatr 06T, from the photographs:
  - A low-slung, wide-shouldered shooting brake (1.34x W/H ratio, 3.0x L/H)
  - A diving peregrine-falcon nose with twin outer hood power domes over the
    F-type flying-wing headlamps and a low central valley
  - A raked panoramic windshield (x 0.82 to header at 0.04), a long shooting-
    brake roof peaking at 1.455 m and extending back to x -1.96 at z 1.365
    before dropping down a raked backlight to a sculpted ducktail at z 1.035
  - Broad, muscular painted wheel arches (no plastic SUV arch cladding) and a
    narrow cabin greenhouse that tapers inward above the rear haunches
"""
from carkit.geom import Curve, Joined          # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 4.940, 1.960, 1.455
HALF_L = LENGTH / 2.0                        # 2.470
HALF_W = WIDTH / 2.0                         # 0.980
FRONT_OVERHANG = 0.950
FRONT_AXLE = HALF_L - FRONT_OVERHANG         # 1.520
REAR_AXLE = FRONT_AXLE - 2.940               # -1.420 (rear overhang 1.050 m)
WHEEL_R = 0.365                              # 255/45 R20 loaded radius
ARCH_R = 0.442                               # sculpted painted wheel opening

V_SHOULDER = 0.520

COWL_X = 0.820
KNEE_X = -1.960                              # shooting-brake roof spoiler edge
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # backlight: from the sculpted ducktail decklid up to the shooting-brake
    # roof spoiler lip (c1_0004.jpg, c1_0006.jpg)
    (-HALF_L, 1.035), (-2.42, 1.060), (-2.33, 1.115), (-2.22, 1.190),
    (-2.10, 1.275), (KNEE_X, 1.365),
]), Curve([
    # long shooting-brake roof: stays high over the rear passengers and luggage
    # bay before peaking at 1.455 m over the front seats
    (KNEE_X, 1.365), (-1.75, 1.396), (-1.50, 1.424), (-1.20, 1.444),
    (-0.85, 1.453), (-0.55, 1.455), (-0.25, 1.442), (0.04, 1.392),
    (0.28, 1.310), (0.55, 1.175), (0.72, 1.080), (COWL_X, 1.025),
])), Curve([
    # hood centreline: low valley between twin outer power domes, diving
    # smoothly toward the falcon nose cap
    (COWL_X, 1.025), (1.05, 0.985), (1.30, 0.955), (1.52, 0.928),
    (1.75, 0.895), (1.98, 0.852), (2.18, 0.800), (2.34, 0.742),
    (HALF_L, 0.675),
]))

# Underbody: low shooting-brake ground clearance (~165 mm between axles)
Z_FLOOR = Curve([
    (-HALF_L, 0.255), (-2.35, 0.232), (-2.15, 0.200), (-1.85, 0.175),
    (-1.42, 0.165), (0.0, 0.162), (1.52, 0.165), (1.85, 0.170),
    (2.15, 0.165), (2.35, 0.150), (HALF_L, 0.140),
])

# Hip line (widest point of the body flank)
Z_HIP = Curve([
    (-HALF_L, 0.560), (-2.15, 0.630), (-1.80, 0.700), (-1.42, 0.735),
    (-0.70, 0.740), (0.0, 0.730), (0.82, 0.730), (1.52, 0.730),
    (2.05, 0.680), (HALF_L, 0.600),
])

# Shoulder crease: rises along the doors into the muscular rear haunch over the
# rear wheel, and sweeps forward over the front wheel arch into the DRL wing
Z_SHOULDER = Curve([
    (-HALF_L, 0.955), (-2.30, 0.980), (-2.05, 1.008), (-1.75, 1.028),
    (-1.42, 1.040), (-1.15, 1.036), (-0.80, 1.015), (-0.40, 0.998),
    (0.00, 0.990), (0.40, 0.985), (COWL_X, 0.972), (1.15, 0.945),
    (1.52, 0.920), (1.85, 0.875), (2.15, 0.810), (2.32, 0.762),
    (HALF_L, 0.715),
])

# Crown of the roof / backlight and front fender tops relative to Z_ROOF
Z_CREST = Joined(COWL_X, Joined(-1.75, Curve([
    (-HALF_L, -0.052), (-2.35, -0.062), (-2.20, -0.066), (-2.05, -0.058),
    (-1.95, -0.042), (-1.85, -0.026), (-1.75, -0.018),
], mode="pchip"), Curve([
    (-HALF_L, 0.000), (-1.96, -0.012), (-1.60, -0.018), (-1.10, -0.022),
    (-0.50, -0.022), (0.00, -0.022), (0.45, -0.025), (0.68, -0.014),
    (COWL_X, 0.000),
])), Curve([
    # front fender crowns above the lowered hood valley
    (COWL_X, 0.000), (0.98, 0.010), (1.20, 0.022), (1.48, 0.034),
    (1.70, 0.036), (1.92, 0.030), (2.08, 0.016), (2.20, 0.004),
    (2.35, 0.000), (HALF_L, 0.000),
]))

# Twin outer hood power domes inboard of the hood shut lines
Z_DOME = Curve([
    (-HALF_L, 0.000), (COWL_X, 0.000), (0.98, 0.006), (1.20, 0.018),
    (1.48, 0.029), (1.70, 0.031), (1.92, 0.025), (2.08, 0.012),
    (2.20, 0.000), (HALF_L, 0.000),
], mode="pchip")

Y_DOME = Curve([
    (-HALF_L, 0.620), (COWL_X, 0.640), (1.05, 0.620), (1.45, 0.595),
    (1.75, 0.575), (1.95, 0.545), (2.10, 0.495), (2.25, 0.450),
    (HALF_L, 0.420),
])

# Half-widths: 1960 mm (0.980 m) over the sculpted rear haunches, tucked waist
# along the doors, and broad front fenders over the 20/21-inch wheels.
Y_HIP = Curve([
    (-HALF_L, 0.805), (-2.38, 0.865), (-2.20, 0.910), (-1.95, 0.948),
    (-1.68, 0.972), (-1.42, 0.978), (-1.10, 0.962), (-0.65, 0.940),
    (0.00, 0.938), (0.60, 0.948), (1.15, 0.965), (1.52, 0.974),
    (1.82, 0.966), (2.05, 0.935), (2.24, 0.875), (2.36, 0.815),
    (HALF_L, 0.730),
])

# Shoulder half-width: tucked inward over the rear haunches to create the
# signature wide-hipped shooting-brake shoulder shelf (c1_0005..0007.jpg)
Y_SHOULDER = Curve([
    (-HALF_L, 0.650), (-2.32, 0.725), (-2.15, 0.785), (-1.90, 0.842),
    (-1.65, 0.868), (-1.42, 0.878), (-1.15, 0.885), (0.00, 0.882),
    (COWL_X, 0.888), (1.52, 0.905), (1.95, 0.890), (2.22, 0.845),
    (HALF_L, 0.780),
])

# Roof rail half-width (longer shooting-brake roof carried back to KNEE_X)
Y_ROOF = Curve([
    (-HALF_L, 0.530), (-2.35, 0.535), (-2.05, 0.515), (-1.75, 0.530),
    (-1.35, 0.555), (-0.95, 0.575), (-0.50, 0.595), (0.00, 0.610),
    (0.45, 0.675), (COWL_X, 0.745), (1.25, 0.775), (1.65, 0.780),
    (2.05, 0.755), (2.32, 0.695), (HALF_L, 0.625),
])

# Greenhouse base half-width: creates the broad rear haunch deck under the
# shooting-brake quarter window and C-pillar
Y_GLASS = Curve([
    (-HALF_L, 1.200), (-2.38, 1.200), (-2.18, 0.715), (-1.95, 0.700),
    (-1.70, 0.685), (-1.42, 0.688), (-1.15, 0.720), (-0.90, 0.780),
    (-0.65, 0.845), (-0.40, 1.200), (HALF_L, 1.200),
], mode="pchip")

Z_STEP = Curve([
    (-HALF_L, 0.028), (-2.25, 0.042), (-2.00, 0.064), (-1.70, 0.066),
    (-1.42, 0.062), (-1.15, 0.042), (-0.90, 0.028), (HALF_L, 0.028),
], mode="pchip")
SOFT = Curve([(-HALF_L, 1.0), (-1.42, 1.0), (-0.90, 0.0), (HALF_L, 0.0)], mode="pchip")

Y_ROCKER = Curve([
    (-HALF_L, 0.780), (-2.25, 0.865), (-1.95, 0.905), (-1.42, 0.920),
    (-1.00, 0.922), (0.00, 0.925), (1.00, 0.920), (1.52, 0.915),
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
