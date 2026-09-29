"""Xiaomi SU7 Ultra body surface - the profile curves of its flank loft.

The section maths lives in carkit.body.loft (LoftBody): two centripetal
Catmull-Rom segments meeting at a hard shoulder crease, sampled by arc length.
This module is the SU7's DATA - its dimensions and the profile curves every
section is built from, read off the camera-matched reference photographs -
plus the module-level function API (section, section_v, surface, ...) that the
other su7_* modules and the interior are written against.

Surface parameterisation
------------------------
    S(x, v)   x = station along the car in metres, +X forward
              v = 0 at the underbody centreline, 1 at the roof centreline,
                  V_SHOULDER at the crease

Real dimensions: 5070 x 1970 x 1465 mm, 3000 mm wheelbase, overhangs 1007
front / 1063 rear (MIIT). LENGTH below is the loft's construction length,
not the car's: the splitter reaches +2.5575 and the tail cap is profiled to
end at -2.5125 (su7_nose.TAIL_X_OF_Z), 5070 mm overall.
"""
from carkit.geom import Curve, Joined          # noqa: F401  (re-exported)
from carkit.body import LoftBody

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.115, 1.970, 1.465
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
FRONT_AXLE = 1.5575          # 1000 mm front overhang
REAR_AXLE = -1.4425          # 1115 mm rear overhang
WHEEL_R = 0.3595             # 21 in rim, 265/35 front and 305/30 rear
ARCH_R = 0.405               # measured opening radius about the wheel centre

V_SHOULDER = 0.520           # where the crease sits in section parameter space

# Cabin extent: cowl (base of windscreen) back to the base of the backlight.
# Camera-matched against the side photograph the A-pillar foot sits at
# x = 0.93, z = 0.97 - 145 mm further forward and 105 mm lower than the first
# build had it, which is most of why that front end read long and tall.
COWL_X = 0.945
BACKLIGHT_X = -1.905


# ------------------------------------------------------- longitudinal profile
# Read off the official side and 3/4 photography. Values in metres.

Z_ROOF = Joined(COWL_X, Curve([      # top centreline: screen, roof, deck
    # Fitted through the camera-matched side photograph (ref_match.py). The
    # roof from x = +0.3 to -1.3 already matched to 2 px; the backlight and
    # deck come down up to 30 mm, and the screen now runs straight down to a
    # cowl 145 mm further forward.
    (-HALF_L, 0.950), (-2.45, 0.970), (-2.30, 0.998), (-2.10, 1.046),
    (-1.90, 1.100), (-1.65, 1.172), (-1.40, 1.272), (-1.15, 1.350),
    (-0.90, 1.408), (-0.65, 1.446), (-0.40, 1.4650), (-0.20, 1.4635),
    (0.00, 1.4480), (0.20, 1.4050), (0.40, 1.3180), (0.62, 1.1800),
    (0.80, 1.0630), (COWL_X, 0.9720),
]), Curve([                            # hood centreline, cowl to nose
    # The nose is LOW: the side photograph puts the top of the car 0.73 m
    # off the ground at the headlamps, level with the top of the front tyre.
    # The first build carried the hood forward at 0.90 and stood the nose up
    # as a tall face, which is what read as a long, heavy snout.
    (COWL_X, 0.9720), (1.10, 0.9450), (1.30, 0.9210), (1.50, 0.9020),
    (1.70, 0.8760), (1.90, 0.8320), (2.10, 0.7820), (2.25, 0.7520),
    (2.40, 0.7330), (HALF_L, 0.7220),
]))

Z_FLOOR = Curve([                     # underbody, sweeping up into the overhangs
    # Ahead of the front wheel this is the bottom of the bumper corner, which the
    # reference puts at z 0.16 - the splitter's outer wing sits right under it.
    (-HALF_L, 0.262), (-2.42, 0.252), (-2.24, 0.232), (-2.02, 0.196),
    (-1.78, 0.172), (-1.4425, 0.156), (0.0, 0.148), (1.5575, 0.156),
    (1.88, 0.162), (2.05, 0.160), (2.238, 0.1560), (2.36, 0.150),
    (HALF_L, 0.140),
])

Y_HIP = Curve([                       # widest point, over the arches
    # Measured: maximum half-width 0.985 at (1.700, z 0.720). Ahead of the
    # front wheel the flank now turns in at ~19 deg by the bumper joint, so
    # the nose cap can carry the corner round instead of meeting a straight
    # flank at 30 deg - the crease the zebra render showed past the lamp.
    (-HALF_L, 0.874), (-2.45, 0.896), (-2.25, 0.930), (-2.00, 0.958),
    (-1.72, 0.978), (-1.4425, 0.9850), (-1.10, 0.9720), (-0.60, 0.9600),
    (0.0, 0.9540), (0.60, 0.9620), (1.20, 0.9760), (1.700, 0.9850),
    (1.95, 0.9680), (2.05, 0.9460), (2.15, 0.9120), (2.25, 0.8700),
    (2.322, 0.8350), (HALF_L, 0.7600),
])

Z_HIP = Curve([
    (-HALF_L, 0.572), (-2.10, 0.636), (-1.4425, 0.690), (-0.60, 0.700),
    (0.0, 0.702), (0.80, 0.706), (1.30, 0.714), (1.700, 0.720),
    (2.15, 0.660), (HALF_L, 0.560),
])

Z_SHOULDER = Curve([                  # the beltline crease, rising to the rear
    # Forward of the A-pillar the crease drops with the hood and runs into the
    # upper rear corner of the headlamp, as on the car.
    (-HALF_L, 0.952), (-2.20, 0.974), (-1.90, 0.972), (-1.65, 0.964),
    (-1.10, 0.950), (-0.50, 0.936), (0.30, 0.920), (COWL_X, 0.902),
    (1.20, 0.884), (1.45, 0.862), (1.65, 0.838), (1.85, 0.800),
    (2.05, 0.750), (2.20, 0.716), (2.322, 0.698), (HALF_L, 0.680),
])

Y_SHOULDER = Curve([
    (-HALF_L, 0.824), (-2.30, 0.850), (-2.00, 0.872), (-1.4425, 0.914),
    (-1.10, 0.907), (0.0, 0.900), (0.60, 0.902), (1.005, 0.905),
    (1.5575, 0.909), (1.90, 0.898), (2.20, 0.876), (HALF_L, 0.856),
])

Y_ROOF = Curve([                      # half-width at the very top of the section
    # Forward of the cowl this is the line of the fender crowns, measured at
    # y = 0.790 over the front axle - it is where the hood's twin highlight
    # streaks run, so it is a feature line, not a construction value.
    (-HALF_L, 0.712), (-2.42, 0.736), (-2.20, 0.768), (-1.95, 0.780),
    (-1.65, 0.730), (-1.30, 0.662), (-0.95, 0.604), (-0.55, 0.574),
    (-0.15, 0.570), (0.25, 0.600), (0.55, 0.682), (0.80, 0.760),
    (1.20, 0.782), (1.62, 0.790), (2.00, 0.778), (2.322, 0.700),
    (HALF_L, 0.640),
])

Y_ROCKER = Curve([                    # side-sill outer face
    # Roughly in line with the tyre's outer face, which is where a real sill
    # sits. 206 mm inboard of the hip rounded the whole lower body under like a
    # hull and made the car read as a submarine. Ahead of the front wheel and
    # behind the rear one this is the lower corner of the bumper, which the
    # reference puts at 0.905 all the way down to the splitter.
    (-HALF_L, 0.780), (-2.30, 0.860), (-2.05, 0.884), (-1.4425, 0.890),
    (-1.00, 0.900), (0.0, 0.905), (1.10, 0.900), (1.5575, 0.890),
    (2.00, 0.900), (2.15, 0.888), (2.25, 0.860), (HALF_L, 0.780),
], mode="pchip")

UNDERCUT = Curve([                    # concavity of the lower door, metres
    # Measured at ~20 mm amidships, running out to nothing at the arches where
    # the fender flares are full. This is the SU7's lower-door scoop - it is
    # what catches a dark band of reflection and lifts the car visually.
    (-HALF_L, 0.0), (-1.85, 0.0), (-1.10, 0.011), (-0.60, 0.020),
    (0.60, 0.020), (1.10, 0.011), (1.60, 0.0), (HALF_L, 0.0),
], mode="pchip")

Z_CREST = Joined(COWL_X, Curve([
    # Negative over the screen: it is a wraparound screen, so the A-pillars
    # sit ~30 mm below the centreline - that is what brought the A-pillar
    # silhouette down onto the photograph.
    (-HALF_L, 0.006), (-2.30, 0.013), (-2.00, 0.016), (-1.70, 0.007),
    (-1.30, -0.013), (-0.60, -0.020), (0.0, -0.021), (0.35, -0.028),
    (0.65, -0.030), (0.85, -0.012), (COWL_X, 0.002),
]), Curve([
    # Twin fender crowns over the front wheels, rolling over to a domed nose
    # ahead of them where the fenders run down into the headlamps.
    (COWL_X, 0.002), (1.10, 0.010), (1.30, 0.016), (1.60, 0.018),
    (1.80, 0.013), (2.00, 0.002), (2.20, -0.010), (2.40, -0.014),
    (HALF_L, -0.014),
]))

V_HOOD_SPLIT = Curve([                # hood/fender shut line, in section parameter
    # The SU7's hood is a clamshell that includes the fender tops: forward of
    # the cowl the shut line drops until it meets the top edge of the headlamp.
    (-HALF_L, 0.800), (0.0, 0.800), (0.80, 0.800), (1.30, 0.752),
    (1.75, 0.700), (2.10, 0.664), (HALF_L, 0.650),
])


# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="SU7 Ultra", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.150, core_z=0.62, crease="sharp",
)

# The module's function API, bound to the SU7 loft.
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
