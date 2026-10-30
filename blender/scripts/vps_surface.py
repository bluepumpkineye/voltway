"""Voyah Passion S (岚图追光S) body surface - profile curves of its coupe-SUV flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module defines
the Voyah Passion S's dimensions and profile curves calibrated directly against
the Autohome 3840x2880 studio turnaround photos (c1_0001..c1_0008.jpg, c1_0009..c1_0016.jpg)
through the solved cameras in vps_cam.py.

Real dimensions (Autohome Series 8534 / MIIT 2026):
  - Length x Width x Height: 5050 x 1998 x 1636 mm (AWD Ultra+ on Magic Carpet air suspension;
    coil-sprung RWD Max / RWD Ultra stands at 1656 mm)
  - Wheelbase: 3000 mm (overhangs measured off the side silhouette: 1000 mm front, 1050 mm rear)
  - Track: 1720 mm front / 1723 mm rear
  - Tyres: 255/50 R21 (loaded radius 0.375 m)

Key proportion and surface traits read off c1_0004 / c1_0002 / c1_0006:
  - Sculpted coupe-SUV bonnet with outer power domes flanking a recessed centre valley, meeting
    the full-width black nose channel and winged DRLs at x 2.360, z 0.892
  - Fast raked windscreen from cowl x 1.040, z 1.158 up past the 896-line roof LiDAR to a sleek
    panoramic roof peaking at 1.636 m over the B-pillar (x -0.35..-0.51)
  - Raked liftback backlight from the roof knee (x -1.720, z 1.532, overhung by the twin-pod
    aero spoiler to x -1.875) straight down to the ducktail deck at x -2.400, z 1.218
  - Broad SUV wheel arches (painted opening r 0.522 m, framed by gloss-black cladding flaring to
    1998 mm overall width) and muscular rear haunches under a tucked-in greenhouse
"""
from carkit.geom import Curve, Joined          # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.050, 1.998, 1.636
HALF_L = LENGTH / 2.0                        # 2.525
HALF_W = WIDTH / 2.0                         # 0.999
FRONT_OVERHANG = 1.000
FRONT_AXLE = HALF_L - FRONT_OVERHANG         # 1.525
REAR_AXLE = FRONT_AXLE - 3.000               # -1.475 (rear overhang 1.050 m)
WHEEL_R = 0.375                              # 255/50 R21 loaded radius
# Painted wheel opening radius: gloss-black arch cladding (vps_side) laps 10 mm outside
# this edge (r_out 0.532 m) and steps inward 56 mm (r_in 0.466 m) over the tyre.
ARCH_R = 0.522

V_SHOULDER = 0.520

COWL_X = 1.040
KNEE_X = -1.720                              # roof rear header under the twin-pod spoiler
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # Liftback backlight: straight ~25-deg glass rake from the roof header under the twin-pod
    # spoiler (x -1.720, z 1.532) down to the ducktail foot (x -2.400, z 1.218, matching vps_nose).
    (-HALF_L, 1.175), (-2.460, 1.192), (-2.400, 1.218), (-2.310, 1.255),
    (-2.220, 1.298), (-2.140, 1.338), (-2.060, 1.375), (-1.980, 1.412),
    (-1.890, 1.454), (-1.800, 1.495), (KNEE_X, 1.532),
]), Curve([
    # Panoramic roof & windscreen: peaks at 1.636 m over x -0.35..-0.51, sweeps smoothly under
    # the roof LiDAR pod (x 0.16..0.37) and down the raked windscreen to COWL_X = 1.040.
    (KNEE_X, 1.532), (-1.620, 1.554), (-1.490, 1.574), (-1.330, 1.592),
    (-1.170, 1.605), (-1.000, 1.617), (-0.840, 1.626), (-0.680, 1.633),
    (-0.510, 1.636), (-0.350, 1.636), (-0.190, 1.633), (-0.050, 1.622),
    (0.100, 1.602), (0.260, 1.564), (0.380, 1.518), (0.465, 1.478),
    (0.550, 1.440), (0.630, 1.395), (0.710, 1.349), (0.790, 1.304),
    (0.870, 1.252), (0.955, 1.207), (COWL_X, 1.158),
])), Curve([
    # Bonnet centreline valley: sits 24-32 mm below the outer fender crowns / hood domes (Z_CREST)
    # and meets the nose cap's top edge at (2.360, 0.892).
    (COWL_X, 1.158), (1.150, 1.114), (1.350, 1.109), (1.550, 1.098),
    (1.750, 1.074), (1.950, 1.036), (2.150, 0.971), (2.280, 0.924),
    (2.360, 0.892), (HALF_L, 0.780),
]))

# Underbody / rocker lower edge (read off side_grid_mid/nose/tail: z 0.258-0.268 along the sills,
# rising into the rear diffuser behind the rear wheel).
Z_FLOOR = Curve([
    (-HALF_L, 0.355), (-2.420, 0.340), (-2.250, 0.312), (-2.050, 0.282),
    (-1.850, 0.268), (REAR_AXLE, 0.264), (-0.800, 0.264), (0.000, 0.262),
    (0.850, 0.260), (FRONT_AXLE, 0.256), (1.950, 0.252), (2.200, 0.256),
    (2.380, 0.264), (HALF_L, 0.275),
])

# Hip line (widest elevation of the flank haunches, front/rear grid z ~0.76-0.84)
Z_HIP = Curve([
    (-HALF_L, 0.640), (-2.220, 0.720), (-1.880, 0.790), (REAR_AXLE, 0.820),
    (-0.750, 0.830), (0.000, 0.820), (0.850, 0.820), (FRONT_AXLE, 0.815),
    (2.050, 0.760), (HALF_L, 0.675),
])

# Shoulder crease: ~45 mm under the window belt along the doors, rounding over the rear haunch
# toward the full-width smoked taillight and sweeping forward along the front fender into the DRL.
Z_SHOULDER = Curve([
    (-HALF_L, 1.065), (-2.350, 1.090), (-2.120, 1.115), (-1.850, 1.132),
    (REAR_AXLE, 1.145), (-1.200, 1.160), (-0.900, 1.152), (-0.500, 1.142),
    (0.000, 1.138), (0.450, 1.134), (0.850, 1.130), (COWL_X, 1.110),
    (1.300, 1.078), (FRONT_AXLE, 1.055), (1.850, 1.015), (2.150, 0.945),
    (2.360, 0.885), (HALF_L, 0.820),
])

# Crown of the roof / backlight and front fender tops relative to Z_ROOF
Z_CREST = Joined(COWL_X, Curve([
    (-HALF_L, -0.058), (-2.380, -0.068), (-2.200, -0.070), (-2.000, -0.056),
    (-1.820, -0.036), (-1.680, -0.024), (-1.450, -0.020), (-1.000, -0.020),
    (-0.450, -0.018), (0.000, -0.018), (0.400, -0.024), (0.750, -0.016),
    (COWL_X, 0.000),
], mode="pchip"), Curve([
    # Outer fender crowns standing 24-32 mm proud of the recessed bonnet centreline
    (COWL_X, 0.000), (1.150, 0.022), (1.350, 0.030), (1.550, 0.032),
    (1.750, 0.030), (1.950, 0.024), (2.150, 0.014), (2.280, 0.004),
    (2.360, 0.000), (HALF_L, 0.000),
]))

# Sculpted outer bonnet power domes (front_grid.png u 1260..1460 / 2380..2580)
Z_DOME = Curve([
    (-HALF_L, 0.000), (COWL_X, 0.000), (1.150, 0.018), (1.350, 0.026),
    (1.550, 0.028), (1.750, 0.026), (1.950, 0.020), (2.150, 0.010),
    (2.280, 0.000), (HALF_L, 0.000),
], mode="pchip")

Y_DOME = Curve([
    (-HALF_L, 0.620), (COWL_X, 0.640), (1.250, 0.610), (1.550, 0.585),
    (1.850, 0.555), (2.100, 0.505), (2.280, 0.455), (HALF_L, 0.420),
])

# Half-widths: painted haunches reach 0.980 m, with gloss-black arch cladding flaring ~19 mm to
# 0.999 m (1998 mm overall width across front/rear arches, matching front_grid & rear_grid).
Y_HIP = Curve([
    (-HALF_L, 0.825), (-2.380, 0.885), (-2.200, 0.925), (-1.950, 0.958),
    (-1.700, 0.974), (REAR_AXLE, 0.980), (-1.150, 0.968), (-0.650, 0.955),
    (0.000, 0.955), (0.600, 0.962), (1.150, 0.974), (FRONT_AXLE, 0.980),
    (1.850, 0.972), (2.060, 0.945), (2.240, 0.895), (2.380, 0.840),
    (HALF_L, 0.755),
])

# Shoulder half-width: muscular rear haunch tucking in above z 1.05 (rear_grid y 0.92 at z 1.11)
Y_SHOULDER = Curve([
    (-HALF_L, 0.675), (-2.350, 0.745), (-2.180, 0.805), (-1.950, 0.865),
    (-1.700, 0.892), (REAR_AXLE, 0.905), (-1.200, 0.908), (-0.650, 0.905),
    (0.000, 0.905), (0.600, 0.910), (COWL_X, 0.915), (FRONT_AXLE, 0.925),
    (1.920, 0.910), (2.200, 0.870), (HALF_L, 0.805),
])

# Roof rail half-width (rear_grid: +/-0.60 at z 1.53; front_grid: +/-0.615 at header, +/-0.83 at cowl)
Y_ROOF = Curve([
    (-HALF_L, 0.545), (-2.380, 0.550), (-2.100, 0.535), (-1.750, 0.555),
    (-1.350, 0.580), (-0.950, 0.598), (-0.500, 0.612), (0.000, 0.618),
    (0.280, 0.635), (0.480, 0.685), (0.680, 0.742), (0.880, 0.795),
    (COWL_X, 0.825), (1.300, 0.815), (1.650, 0.805), (2.020, 0.775),
    (2.300, 0.715), (HALF_L, 0.640),
])

# Greenhouse base half-width: broad rear haunch deck under the C-pillar and quarter glass
# (rear_grid v 1165: y 0.734 at z 1.27 over a 0.980 haunch).
Y_GLASS = Curve([
    (-HALF_L, 1.200), (-2.380, 1.200), (-2.200, 0.735), (-1.950, 0.720),
    (-1.680, 0.715), (-1.400, 0.725), (-1.150, 0.755), (-0.900, 0.810),
    (-0.650, 0.875), (-0.400, 1.200), (HALF_L, 1.200),
], mode="pchip")

Z_STEP = Curve([
    (-HALF_L, 0.028), (-2.280, 0.042), (-2.020, 0.064), (-1.720, 0.066),
    (-1.420, 0.062), (-1.150, 0.042), (-0.900, 0.028), (HALF_L, 0.028),
], mode="pchip")
SOFT = Curve([(-HALF_L, 1.0), (-1.420, 1.0), (-0.900, 0.0), (HALF_L, 0.0)], mode="pchip")

Y_ROCKER = Curve([
    (-HALF_L, 0.800), (-2.280, 0.880), (-1.980, 0.920), (REAR_AXLE, 0.935),
    (-1.000, 0.938), (0.000, 0.942), (1.000, 0.938), (FRONT_AXLE, 0.932),
    (1.950, 0.925), (2.150, 0.900), (2.320, 0.860), (HALF_L, 0.790),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-1.900, 0.0), (-1.150, 0.016), (-0.650, 0.026),
    (0.450, 0.026), (0.900, 0.014), (1.350, 0.0), (HALF_L, 0.0),
], mode="pchip")


# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="Voyah Passion S", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.125, core_z=0.72, crease="sharp", z_dome=Z_DOME, y_dome=Y_DOME,
    y_glass=Y_GLASS, z_step=Z_STEP, soft=SOFT,
    section=Section(step_in=0.045, step_max=0.028, tumble=(0.36, 0.64, 0.52, 0.40),
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
