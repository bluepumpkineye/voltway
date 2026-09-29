"""Luxeed RX body surface - the profile curves of its flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module is the
RX's DATA: its dimensions and the profile curves every section is built
from, read off the camera-matched photographs (rx_ref_match.py; the photo
readings behind every value are in rx_camsolve.py and rx_trace.py).

Real dimensions (MIIT filing 2026): 5020 x 2007 x 1585 (1600) mm, wheelbase
3000 mm, track 1710/1713 front and 1715/1725 rear, 255/45 R21 front and
275/45 R21 rear (or 255/40 R22 / 275/40 R22). The overhangs are not
published: 1080 front / 940 rear is between what the side photograph
(nose outline, <= ~1.07-1.11) and the blue car's front 3/4 (plate face
1.131 ahead of the front axle) give.

What makes an RX, from the photographs:
  - a long, high, nearly flat hood: 1.11 m at the cowl, still 1.03 over
    the front axle, rolling down to a nose whose front is at z ~0.5
  - a fast screen from x 0.80 to a header at ~0.05, a roof peaking at
    1.593 m at x -0.9 and staying high to a roof spoiler at x -2.2, z 1.41,
    then a steep backlight down to a ducktail at 1.15
  - a belt rising from 1.12 at the A-pillar to 1.27 at the window's tip
  - big wheel openings with gloss black cladding (the painted edge 0.52-0.57
    m from the hub), a black side skirt z 0.21-0.32

    S(x, v)   x = station along the car in metres, +X forward
              v = 0 at the underbody centreline, 1 at the roof centreline,
                  V_SHOULDER at the crease
"""
from carkit.geom import Curve, Joined          # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.020, 2.007, 1.585
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
FRONT_OVERHANG = 1.080
FRONT_AXLE = HALF_L - FRONT_OVERHANG        # 1.430
REAR_AXLE = FRONT_AXLE - 3.000              # -1.570
WHEEL_R = 0.372              # 21 in, 255/45 front (0.381) and 275/45 rear (0.390), loaded
# The PAINTED opening: the side photograph's painted edge sits 0.52-0.57 m
# from the hub, outside a ~60 mm gloss black cladding lip (rx_side).
ARCH_R = 0.535

V_SHOULDER = 0.520

COWL_X = 0.800
KNEE_X = -2.200              # roof spoiler: roof above, backlight below
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# Top centreline. Roof values are the side photograph's top outline cast onto
# the centreline plane (the camera is at 1.20 m, so above that height the
# centreline, not the rail, forms the outline).
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve([
    # backlight: ducktail lip to the roof spoiler (rear photo: glass
    # z 1.14 - 1.41)
    (-HALF_L, 1.150), (-2.46, 1.170), (-2.40, 1.203), (-2.33, 1.255),
    (-2.26, 1.310), (KNEE_X, 1.358),
]), Curve([
    # both the side and the front 3/4 outline put the rear roof ~40 mm
    # under the first reading
    (KNEE_X, 1.358), (-2.05, 1.396), (-1.86, 1.446), (-1.53, 1.514),
    (-1.21, 1.572), (-0.90, 1.587), (-0.71, 1.584), (-0.40, 1.563),
    (-0.19, 1.540), (0.01, 1.494), (0.21, 1.412), (0.45, 1.298),
    (0.66, 1.180), (COWL_X, 1.112),
])), Curve([
    # hood centreline: a valley between two domes (front_silver: the hood's
    # outer thirds rise into domes over the lamps, the centre lies flat and
    # low). Lowered by the domes' rise over it (Z_CREST) so the domes - which
    # form the side outline - stay where the side photograph put them.
    (COWL_X, 1.112), (1.03, 1.051), (1.23, 1.031), (1.42, 1.012),
    (1.62, 0.992), (1.81, 0.962), (2.00, 0.921), (2.19, 0.877),
    (2.35, 0.811), (HALF_L, 0.730),
]))

# Underbody. The approach and departure angles (14 / 18-19 deg) put the
# lowest points at the ends above ~0.25 m front and ~0.28 m rear.
Z_FLOOR = Curve([
    (-HALF_L, 0.300), (-2.40, 0.278), (-2.20, 0.240), (-1.95, 0.212),
    (-1.57, 0.200), (0.0, 0.195), (1.43, 0.200), (1.80, 0.210),
    (2.10, 0.225), (2.35, 0.245), (HALF_L, 0.262),
])

# The haunch is widest low, at 0.7-0.8 m (rear photograph), with the body
# tucking in hard above it toward the narrow rear shoulder.
Z_HIP = Curve([
    (-HALF_L, 0.600), (-2.20, 0.680), (-1.90, 0.760), (-1.57, 0.800), (-0.70, 0.810),
    (0.0, 0.800), (0.80, 0.800), (1.43, 0.800), (2.00, 0.745),
    (HALF_L, 0.660),
])

# Beltline crease, ~35 mm under the window's lower edge (side photo: 1.119
# at x 0.28 rising to 1.266 at the window's tip, x -1.46). Behind the rear
# door it leaves the rising window line and becomes the top of the rear
# haunch, falling to the lamp; ahead of the cowl it runs along the fender
# top into the headlamp.
# Over the rear wheel it once rose with the window to 1.185: from behind
# (rear.jpg, solved camera, the silhouette under the mirrors) that crease
# stood up to 16 cm outside the photo at z 1.12-1.19, a flat shelf that hid
# both mirrors and made the tail read heavy. The photo's haunch tops out at
# ~1.10 and a deck slopes from it, 25-30 deg, up to the C-pillar's foot at
# (0.72, 1.16) - see Z_STEP and SOFT.
Z_SHOULDER = Curve([
    (-HALF_L, 1.030), (-2.35, 1.055), (-2.15, 1.082), (-1.90, 1.100),
    (-1.60, 1.112), (-1.40, 1.122), (-1.20, 1.135), (-1.00, 1.130), (-0.70, 1.108),
    (-0.40, 1.092), (0.00, 1.085), (0.30, 1.082), (COWL_X, 1.060),
    (1.10, 1.020), (1.43, 0.990), (1.80, 0.940), (2.10, 0.870),
    (2.30, 0.815), (HALF_L, 0.760),
])

# Behind the roof spoiler the top is crowned: the side photo's outline from
# the spoiler's end down to the ducktail (u 863-910, formed at the top's
# outer edge) stood 4-13 px (2-7 cm) under a flat-topped section - the
# rail drops ~7 cm below the centreline over the backlight.
Z_CREST = Joined(COWL_X, Joined(-1.85, Curve([
    (-HALF_L, -0.060), (-2.40, -0.072), (-2.30, -0.078), (-2.20, -0.078),
    (-2.10, -0.062), (-2.03, -0.040), (-1.97, -0.025), (-1.85, -0.019),
], mode="pchip"), Curve([
    (-HALF_L, 0.000), (-2.20, -0.010), (-1.80, -0.020), (-1.20, -0.024),
    (-0.60, -0.025), (0.00, -0.025), (0.40, -0.030), (0.65, -0.018),
    (COWL_X, 0.000),
])), Curve([
    # the fender crowns: where the side and front 3/4 outlines put them -
    # over the hood's lowered centreline by the valley's depth
    (COWL_X, 0.000), (0.95, 0.010), (1.15, 0.022), (1.40, 0.033),
    (1.60, 0.038), (1.85, 0.038), (2.00, 0.028), (2.10, 0.014),
    (2.19, 0.004), (2.35, 0.000), (HALF_L, 0.000),
]))

# The hood's domes (front_silver: the hood's outer thirds rise into domes
# over the lamps, inboard of its shut lines; the fender crowns stand outboard
# of them): 4 mm under the crowns, fading out at the windscreen's corners and
# before the nose, so the valley does not run into the nose cap.
Z_DOME = Curve([
    (-HALF_L, 0.000), (COWL_X, 0.000), (0.95, 0.006), (1.15, 0.018),
    (1.40, 0.029), (1.60, 0.034), (1.85, 0.034), (2.00, 0.024),
    (2.10, 0.010), (2.19, 0.000), (HALF_L, 0.000),
], mode="pchip")
# (the hood's shut line, rx_panels Y_HOOD, runs in the groove between a
# dome and its fender crown - drawing in towards the lamps)
Y_DOME = Curve([
    (-HALF_L, 0.640), (COWL_X, 0.660), (1.00, 0.640), (1.40, 0.612),
    (1.70, 0.595), (1.90, 0.570), (2.05, 0.522), (2.20, 0.472), (HALF_L, 0.450),
])

# Half-widths. 2007 mm over the rear haunches (rear photograph: the widest
# point, z ~0.86); the doors are the waist.
# Behind the rear wheel the body tapers in plan to a broad, square tail: the
# front 3/4 outline (surface facing ~24 deg rearward) is 0.1 m inside a
# straight haunch, the side one (~62 deg rearward) needs the tail's corners
# right out at x -2.5.
# From behind (rear.jpg, solved camera) the PAINTED haunch is only ~0.94
# m: the rear tyres' walls stand out past it and the gloss black arch
# cladding (rx_side) carries the car to its 2007 mm.
Y_HIP = Curve([
    (-HALF_L, 0.830), (-2.40, 0.880), (-2.25, 0.910), (-2.05, 0.932),
    (-1.85, 0.942), (-1.57, 0.948), (-1.20, 0.945), (-0.70, 0.942), (0.00, 0.945),
    (0.60, 0.955), (1.10, 0.972), (1.43, 0.980), (1.75, 0.978),
    (2.00, 0.955), (2.20, 0.905), (2.35, 0.850), (HALF_L, 0.760),
])

# Over the rear wheel the shoulder tucks in hard above the haunch: through
# the front 3/4 camera the C-pillar and the lamp's side end are 35-50 px
# inside a shoulder carried at 0.88 to x -2.2; from behind the haunch's top
# is inside 0.87 at z 1.09 (rear.jpg).
Y_SHOULDER = Curve([
    (-HALF_L, 0.665), (-2.35, 0.735), (-2.20, 0.790), (-2.00, 0.848),
    (-1.80, 0.868), (-1.57, 0.880), (-1.35, 0.890),
    (-1.20, 0.897), (0.00, 0.895), (COWL_X, 0.900), (1.43, 0.915),
    (1.90, 0.905), (2.20, 0.870), (HALF_L, 0.820),
])

# Roof rail half-width (rear photograph: the roof's top is +/-0.54 wide,
# the backlight +/-0.63 at its base; its top outline's rays put the rail
# ~2 cm further in over the rear door, x -0.8 to -1.4, than first built;
# with Y_GLASS every rear-view silhouette ray is met within 2 cm);
# ahead of the cowl, the fender crowns
# (the hood's domes are Z_DOME / Y_DOME, inboard of them).
Y_ROOF = Curve([
    (-HALF_L, 0.545), (-2.40, 0.545), (-2.20, 0.515), (-1.90, 0.525),
    (-1.40, 0.548), (-1.00, 0.560), (-0.80, 0.585), (-0.20, 0.615), (0.20, 0.630),
    (0.50, 0.690), (COWL_X, 0.760), (1.20, 0.790), (1.60, 0.795),
    (2.00, 0.780), (2.30, 0.720), (HALF_L, 0.650),
])

# The greenhouse's base half-width (LoftBody y_glass). From behind (rear.jpg,
# solved camera; the tyre track sets the scale at this depth) the cabin
# tapers rearward on broad haunches: the silhouette rays put the rear door
# glass and the C-pillar up to 14 cm inside the plain step at z 1.22-1.30
# (x -1.2 to -1.9), 6-8 cm at z 1.30, ~2 cm at 1.40 - a shoulder deck ~20 cm
# wide (rear_high.jpg shows it from above). Behind the wheel the C-pillar's
# foot stays in at ~0.72 to x -2.25 (the saddle under the mirrors); ahead of
# the B-pillar and at the backlight the plain step stands (1.2 = no inset).
Y_GLASS = Curve([
    (-HALF_L, 1.200), (-2.40, 1.200), (-2.25, 0.735), (-2.10, 0.735),
    (-2.00, 0.715), (-1.90, 0.700), (-1.70, 0.690), (-1.50, 0.690),
    (-1.20, 0.720), (-1.00, 0.780),
    (-0.80, 0.830), (-0.55, 0.900), (-0.40, 1.200), (HALF_L, 1.200),
], mode="pchip")

# Behind the rear doors (LoftBody z_step, soft): the deck between the
# haunch's top and the C-pillar's foot rises 6-7 cm (the recipe's step is
# 28 mm), and the crease that is crisp along the doors rounds off into the
# haunch - from behind the photo's outline turns smoothly from the haunch
# into the deck, with no corner.
Z_STEP = Curve([
    (-HALF_L, 0.028), (-2.30, 0.040), (-2.10, 0.066), (-1.80, 0.068),
    (-1.50, 0.065), (-1.25, 0.045), (-1.00, 0.028), (HALF_L, 0.028),
], mode="pchip")
SOFT = Curve([(-HALF_L, 1.0), (-1.50, 1.0), (-1.00, 0.0), (HALF_L, 0.0)], mode="pchip")

Y_ROCKER = Curve([
    (-HALF_L, 0.800), (-2.30, 0.880), (-2.05, 0.915), (-1.57, 0.925),
    (-1.10, 0.930), (0.00, 0.935), (1.00, 0.930), (1.43, 0.920),
    (1.90, 0.925), (2.10, 0.910), (2.25, 0.880), (HALF_L, 0.800),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-1.95, 0.0), (-1.20, 0.014), (-0.70, 0.024),
    (0.40, 0.024), (0.85, 0.012), (1.30, 0.0), (HALF_L, 0.0),
], mode="pchip")


# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="Luxeed RX", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.120, core_z=0.72, crease="sharp", z_dome=Z_DOME, y_dome=Y_DOME,
    y_glass=Y_GLASS, z_step=Z_STEP, soft=SOFT,
    # From behind the greenhouse is narrow on a broad shoulder: +/-0.65 m at
    # z 1.4 over a +/-0.90 shoulder at 1.1. A wider ledge above the crease
    # and a straighter, steeper side glass than the SU7's.
    section=Section(step_in=0.045, step_max=0.028, tumble=(0.36, 0.64, 0.52, 0.40),
                    # front_silver: each dome's inner edge at y ~0.43 - a compact
                    # dome with a steep inner flank over a flat valley
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
