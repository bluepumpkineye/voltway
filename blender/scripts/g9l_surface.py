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
from carkit.geom import Curve, Joined, smoothstep as _smooth
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.120, 1.999, 1.782
HALF_L = LENGTH / 2.0
HALF_W = WIDTH / 2.0
WHEELBASE = 3.100
FRONT_OVERHANG = 0.910
REAR_OVERHANG = LENGTH - WHEELBASE - FRONT_OVERHANG  # 1.110
FRONT_AXLE = HALF_L - FRONT_OVERHANG                 # 1.650
REAR_AXLE = FRONT_AXLE - WHEELBASE                   # -1.450
WHEEL_R = 0.380                                      # loaded hub height: 265/40 R22 (0.3854 free), ~5 mm sag
TRACK_F, TRACK_R = 1.662, 1.672
ARCH_R = 0.428                                       # taut painted arch opening (~48 mm clearance over 22 in tyre)

V_SHOULDER = 0.520

COWL_X = 1.200                                       # windscreen base
KNEE_X = -2.010                                      # roof spoiler's leading join / roofline trailing edge
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# fit:roof  (x, z) of the top centreline: tail, roof + windscreen, bonnet
TAIL_PTS = [
    (-2.555, 1.242), (-2.520, 1.275), (-2.460, 1.330), (-2.380, 1.402), (-2.300, 1.474),
    (-2.220, 1.545), (-2.140, 1.615), (-2.065, 1.678), (KNEE_X, 1.722),
]
ROOF_PTS = [
    (KNEE_X, 1.722), (-1.900, 1.734), (-1.700, 1.751), (-1.500, 1.764), (-1.300, 1.773),
    (-1.100, 1.779), (-0.900, 1.782), (-0.700, 1.782), (-0.500, 1.782), (-0.300, 1.780),
    (-0.100, 1.776), (0.100, 1.768), (0.250, 1.755), (0.400, 1.726), (0.600, 1.622),
    (0.800, 1.486), (1.000, 1.348), (1.100, 1.276), (COWL_X, 1.224),
]
HOOD_PTS = [
    (COWL_X, 1.218), (1.400, 1.202), (1.600, 1.192), (1.800, 1.176), (2.000, 1.150),
    (2.100, 1.135), (2.200, 1.116), (2.300, 1.092), (2.400, 1.055), (2.480, 1.000),
    (2.540, 0.935), (HALF_L, 0.885),
]
# /fit:roof
Z_ROOF = Joined(COWL_X, Joined(KNEE_X, Curve(TAIL_PTS, mode="pchip"), Curve(ROOF_PTS)), Curve(HOOD_PTS))

# Underbody centreline: athletic ground clearance + crisp upward rear departure sweep & tucked front chin
Z_FLOOR = Curve([
    (-HALF_L, 0.405), (-2.440, 0.365), (-2.240, 0.305), (-2.020, 0.258),
    (-1.850, 0.238), (-1.447, 0.232), (0.015, 0.230), (1.647, 0.232),
    (2.076, 0.245), (2.338, 0.268), (2.505, 0.295), (HALF_L, 0.312),
])

# Hip / widest point height:
Z_HIP = Curve([
    (-HALF_L, 0.710), (-2.331, 0.740), (-2.008, 0.760), (-1.447, 0.765),
    (-0.727, 0.765), (0.015, 0.760), (0.863, 0.755), (1.287, 0.745),
    (1.647, 0.725), (2.128, 0.685), (2.390, 0.640), (HALF_L, 0.595),
])

# Shoulder / beltline height: lowered ~42-55 mm to slim the painted flank slab and open the greenhouse
Z_SHOULDER = Curve([
    (-HALF_L, 1.140), (-2.400, 1.198), (-2.040, 1.268), (-1.820, 1.258), (-1.570, 1.232),
    (-1.200, 1.200), (-0.810, 1.174), (-0.030, 1.150), (0.590, 1.128), (1.100, 1.114),
    (1.250, 1.084), (1.420, 1.046), (1.556, 1.038), (1.769, 1.026), (1.949, 1.014), (2.081, 1.006),
    (2.200, 0.992), (2.300, 0.972), (2.400, 0.946), (2.500, 0.912), (HALF_L, 0.875),
])

# Roof crest offset (rail height under the centreline):
HOOD_ROLL = 0.120         # the hood's edge roll: a quarter ellipse, this wide (y), from the flat top down to the fender's top corner
HOOD_CROWN = 0.134        # its rail point (60 degrees round the roll) sits this share of the roll's height below the centreline
# 2026-10-26: the roof is CROWNED: the front and rear photographs' silhouettes (c1_0002/0006 through their solved cameras) drop 2 cm at
# 0.46 m, 6 cm at 0.64 m and 13 cm at 0.68 m from the centreline, the model's drooped 2 cm at 0.72 (a flat lid 10 cm too wide per side:
# the greenhouse read as a box). The rail now sits 6.5 cm under the centreline over the cabin (it was 4) and 0.675-0.725 out (it was 0.71-0.79).
Z_CREST = Curve([
    (-HALF_L, -0.040), (-2.331, -0.050), (-2.040, -0.050), (-1.469, -0.060),
    (-0.515, -0.065), (0.439, -0.065), (0.863, -0.060), (COWL_X, -0.020),
] + [(x, -HOOD_CROWN * (Z_ROOF(x) - Z_SHOULDER(x)))
     for x in (1.450, 1.600, 1.800, 2.000, 2.200, 2.400, 2.500, HALF_L)])

# Lateral widths (half). The photographs' outlines from front and rear: the widest section
# (0.9995) runs from the rear wheel arch's front edge to the front arch; the nose face is 1.64
# wide and the tailgate 1.55 wide at lamp height, so both ends turn in on big radii. The rear knots
# (x < -2.0) are tuned so the tail cap leaves its join in the flank's own plan direction (2-3 degrees
# instead of 14, the rear quarter's pleat); g9l_nose.JOIN_R and TAIL_WRAP go with them.
# The tail TAPERS from behind the rear arch (the old knots kept the full width to x -2.3: a box).
# The tail's plan (2026-10-27), read from the white car's straight rear photograph through its solved camera (c1_0030: 8.4 m, f 7920: its
# hip width comes out 1.985 against the published 1.999, so the scale is good). Two things come out of it. The silhouette: the hip is widest
# at the rear axle and every station behind it must stand inside y * scale(x) <= 574 px (1920 px frame): 0.971 at x -1.7, 0.943 at -1.9, 0.914
# at -2.1, 0.884 at -2.3, 0.870 at -2.4 - the old taper stood 2-3 cm outside that from x -2.1 forward, the tail 2-5 cm inside it. And the
# tailgate's side edges: |y| 0.784 at the lamp bar's height (z 1.2) and 0.829 at the plate's (z 0.95), the black bumper's ends at 0.83, where the
# model's stood at 0.76 / 0.784 / 0.80: a tail narrower than the haunches round the rear wheels, which read as a funnel from behind. (The
# earlier narrowing came from the rear three-quarter photograph c1_0005, whose camera is only qualitative: every outline in it sits ~40 px
# out, even the roof's.) A straight taper along the bound, then the tail's end closing in; `UPPER_DOOR_REAR` gives the barrel above the hip.
# The knots ease into the plateau over x -1.5 .. -1.1: with the taper meeting it at -1.5 the natural cubic spline overshot to 1.0135 at x -1.2
# (a hump 1.4 cm wide of the published 0.9995 over the rear doors). Knots every 0.1 m behind -2.1 and a mild end (0.76 at the tail's tip) keep the
# spline from ringing at the join with the tail cap (x -2.35): a first set wobbled +/-1 cm there, a plan kink in every reflection.
Y_HIP = Curve([
    (-2.600, 0.775), (-2.500, 0.810), (-2.400, 0.835), (-2.300, 0.858), (-2.200, 0.880), (-2.100, 0.905),
    (-1.900, 0.938), (-1.700, 0.970), (-1.500, 0.992), (-1.300, 0.9980), (-1.100, 0.9950), (-0.727, 0.9880), (0.015, 0.9850), (0.863, 0.9860),
    (1.287, 0.9850), (1.647, 0.9840), (1.950, 0.9680), (2.100, 0.9500), (2.200, 0.9280),
    (2.300, 0.9000), (2.400, 0.8580), (2.500, 0.7880), (HALF_L, 0.610),
])

# Sleeker shoulder & greenhouse base inside muscular wheel-arch haunches
Y_SHOULDER = Curve([
    (-HALF_L, 0.755), (-2.500, 0.770), (-2.400, 0.775), (-2.200, 0.766), (-2.000, 0.748),
    (-1.800, 0.758), (-1.500, 0.790), (-1.200, 0.812), (-0.800, 0.826), (-0.030, 0.842),
    (0.500, 0.862), (0.863, 0.882), (1.100, 0.908), (1.250, 0.938), (1.420, 0.956), (1.556, 0.965),
    (1.769, 0.958), (1.949, 0.922), (2.081, 0.858), (2.200, 0.808), (2.300, 0.762), (2.400, 0.712),
    (2.500, 0.652), (HALF_L, 0.575),
])

# Roof rail half-width: sleek teardrop greenhouse
Y_ROOF = Curve([
    (-HALF_L, 0.690), (-2.500, 0.680), (-2.330, 0.630), (-2.200, 0.592), (-2.040, 0.550), (-1.450, 0.585),
    (-1.000, 0.598), (-0.500, 0.618), (0.000, 0.636), (0.150, 0.642), (0.300, 0.652), (0.450, 0.715), (0.550, 0.740),
    (0.700, 0.770), (0.900, 0.795), (COWL_X, 0.845),
] + [(x, Y_SHOULDER(x) - 0.5 * HOOD_ROLL) for x in (1.450, 1.600, 1.800, 2.000, 2.200, 2.400, 2.500, HALF_L)])

# Tucked rocker sill & deeper athletic lower-door undercut
Y_ROCKER = Curve([
    (-HALF_L, 0.640), (-2.500, 0.770), (-2.331, 0.855), (-1.684, 0.922), (-0.727, 0.932),
    (0.015, 0.934), (0.863, 0.934), (1.647, 0.935), (2.233, 0.895),
    (2.442, 0.825), (HALF_L, 0.625),
], mode="pchip")

UNDERCUT = Curve([
    (-HALF_L, 0.0), (-2.062, 0.0), (-1.350, 0.022), (-0.800, 0.040),
    (0.450, 0.040), (0.950, 0.022), (1.420, 0.0), (HALF_L, 0.0),
], mode="pchip")

# ------------------------------------------------------------------ the loft
def _hood_blend(x):
    """0 over the greenhouse, 1 on the hood: how far the section recipe has changed to the crowned hood's."""
    return _smooth((x - 1.15) / 0.35)


# The recipe's own tumble behind the knee, (0.38, 0.58, 0.50, 0.38), put the point close to the rail and level with the middle of the headroom:
# the wall from the belt up to the rail ran in fast at the bottom and slowly at the top, a SCOOP 3-4 cm deep under the chord (the owner's
# "debossed C-pillar", 2026-10-27, a dent with its own shadow behind the quarter glass). Over the cabin the same wall is convex (+3 cm). The
# scoop is behind the quarter glass's tip (x < -1.9): there the tumble point stays out near the shoulder and low, a rounded shoulder blending
# into the backlight's rail (+1.5..2.4 cm). Ahead of the tip the blend to the cabin's is the old one: that is where the silhouette from behind
# is set, and a first try with the convex tumble all the way (0.80, 0.20, 0.37) put the greenhouse 4-5 cm per side outside the photograph's.
TUMBLE_TAIL_OLD = (0.38, 0.58, 0.50, 0.38)
TUMBLE_TAIL = (0.66, 0.34, 0.42, 0.38)
TUMBLE_CABIN = (0.58, 0.42, 0.50, 0.38)    # over the cabin: the tumble point stays at ~0.77 half-width at mid height while the rail is 8-10 cm narrower: ~25 degrees of lean

# The rear haunch (2026-10-27): from behind the photographs' body is a barrel, 0.97 at the hip, still 0.92 at z 1.06 and 0.89 at 1.13 before
# the shoulder rolls in (c1_0006 through its camera, row scans of the silhouette); the recipe's upper-door point (y blend, tuck, z fraction
# hip -> shoulder) sat at 45 % of the way out, a straight taper that stood 3-6 cm per side inside the photograph at z 0.95-1.15: the
# tail read as a funnel, thin on top and wide at the bumper.
UPPER_DOOR_FRONT = (0.42, 0.010, 0.62)
UPPER_DOOR_REAR = (0.62, 0.010, 0.60)


def SECTION_AT(x):
    """Section constants ahead of the cowl. The recipe's (a 3 cm step in above the crease, a tumble point
    well inside both the crease and the rail) is the glass leaning in; on the fender it folded the section
    back on itself, a groove under the hood's edge. The photographs (c1_0001's far silhouette and shut line,
    back-projected through camera f34_purple) show the hood as a FLAT top that rolls over a small quarter
    ellipse (about 12 cm wide, 12-16 cm high) into the fender's top corner, where the shut line runs on a
    vertical wall: hood z 1.12 at |y| 0.7-0.8 near the nose, 1.20 at |y| 0.8 at x 1.9, against the corner at
    z 1.04-1.08. With the roll's centre at (corner y - HOOD_ROLL, corner z) the recipe's points are the
    ellipse at 0, 30 and 60 degrees and its end: tumble (0.732, 0.268, 0.5, 0), rail_in 0.931."""
    t = _hood_blend(x)
    g = _smooth((x + 1.9) / 0.8)                    # 0 behind x -1.9, 1 ahead of -1.1: the cabin's lean fades in over the C-pillar
    old = tuple(a + (b - a) * g for a, b in zip(TUMBLE_TAIL_OLD, TUMBLE_CABIN))
    c = _smooth((-1.9 - x) / 0.30)                  # 0 ahead of the quarter glass's tip, 1 behind x -2.2: the convex tail's tumble fades in
    cabin = tuple(a + (b - a) * c for a, b in zip(old, TUMBLE_TAIL))
    rc = 0.34 + (0.15 - 0.34) * g                   # the roof's inboard point: 0.15 of the rail's drop over the cabin (a flatter crown), 0.34 behind
    h = 1.0 - _smooth((x + 1.5) / 0.6)              # the rear haunch: 1 behind x -1.5, 0 ahead of -0.9
    door = tuple(a + (b - a) * h for a, b in zip(UPPER_DOOR_FRONT, UPPER_DOOR_REAR))
    if t <= 0.0:
        return dict(tumble=cabin, rail_crest=rc, upper_door=door)
    lerp = lambda a, b: a + (b - a) * t
    k0 = cabin
    k1 = (0.732, 0.268, 0.5, 0.0)
    return dict(step_in=lerp(0.032, 0.003), step_max=lerp(0.030, 0.012),
                tumble=tuple(lerp(a, b) for a, b in zip(k0, k1)),
                rail_in=lerp(0.52, 0.931), rail_crest=lerp(rc, 0.45))


BODY = LoftBody(
    name="XPeng G9L", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.140, core_z=0.78, crease="soft",
    section=Section(step_in=0.032, step_max=0.030, tumble=TUMBLE_TAIL_OLD,
                    upper_door=UPPER_DOOR_FRONT),
    section_at=SECTION_AT,
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
