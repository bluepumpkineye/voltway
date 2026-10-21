"""BYD Seal EV (比亚迪 海豹, Autohome Series 6394, 2025/2026/2027) body surface.

The section maths lives in carkit.body.loft (LoftBody). This module defines the
BYD Seal's DATA: dimensions and profile curves for the Ocean X electric sports sedan,
calibrated to Autohome Series 6394 studio turnarounds and technical specs.

Real dimensions (Autohome Series 6394, BYD Seal 650 Smart Driving / 600 AWD Performance):
    4800 x 1875 x 1460 mm
    wheelbase 2920 mm
    track 1620 mm front / 1625 mm rear
    tyres 235/45 R19 front & rear
    overhangs: 880 mm front / 1000 mm rear
    loaded hub height: ~0.3470 m
"""
from carkit.geom import Curve, Joined
from carkit.body import LoftBody, Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 4.800, 1.875, 1.460
HALF_L = LENGTH / 2.0                # 2.4000
HALF_W = WIDTH / 2.0                 # 0.9375
WHEELBASE = 2.900
FRONT_OVERHANG = 0.860
REAR_OVERHANG = LENGTH - WHEELBASE - FRONT_OVERHANG  # 1.0400 (lengthened rear overhang for balanced sedan-coupe proportions)
FRONT_AXLE = HALF_L - FRONT_OVERHANG                 # 1.5400
REAR_AXLE = FRONT_AXLE - WHEELBASE                   # -1.3600
WHEEL_R = 0.3470                                     # loaded hub height (235/45 R19)
TRACK_F, TRACK_R = 1.620, 1.625
ARCH_R = 0.3740                                      # muscular wheelhouse opening radius

V_SHOULDER = 0.530

# Cab-rearward sports sedan proportions: extended hood-to-windshield ratio (COWL_X = 0.850)
# and lengthened rear deck for authentic sedan-coupe balance (KNEE_X = -1.960)
COWL_X = 0.8500                                      # windscreen base / A-pillar foot
KNEE_X = -1.9600                                     # fastback backlight base / lengthened rear deck
BACKLIGHT_X = KNEE_X

# Longitudinal profile calibrated to BYD Seal Ocean X coupe-fastback silhouette:
# - Extended, low-plunging shark-nose hood from cowl (x = 0.850, z = 0.956) down to x = 2.305 m (z = 0.686)
# - Smooth, single continuous flowing roofline arc (zero bubble/hump) peaking smoothly at 1.442 m (x = -0.12)
#   and flowing into the lengthened sedan-coupe rear deck (x = -1.960.. -2.400 m)
Z_ROOF = Joined(COWL_X, Curve([
    (-2.4000, 0.9680), (-2.2800, 0.9800), (-2.1200, 0.9940), (-1.9600, 1.0100),
    (-1.7200, 1.0760), (-1.4500, 1.1680), (-1.1800, 1.2620), (-0.9200, 1.3420),
    (-0.6600, 1.4000), (-0.4000, 1.4320), (-0.1200, 1.4420), ( 0.1200, 1.4250),
    ( 0.3400, 1.3720), ( 0.5400, 1.2780), ( 0.7200, 1.1250), ( 0.8500, 0.9560),
], mode="pchip"), Curve([
    ( 0.8500, 0.9560), ( 1.0200, 0.9400), ( 1.2200, 0.9200), ( 1.4400, 0.8940),
    ( 1.6500, 0.8620), ( 1.8500, 0.8180), ( 2.0300, 0.7660), ( 2.1800, 0.7220),
    ( 2.2600, 0.6980), ( 2.3050, 0.6860),
], mode="pchip"))

Z_FLOOR = Curve([
    (-2.4000, 0.2520), (-2.2400, 0.2380), (-2.0400, 0.2180), (-1.8200, 0.1860),
    (-1.5800, 0.1640), (-1.3600, 0.1520), ( 0.0000, 0.1440), ( 1.5400, 0.1520),
    ( 1.8000, 0.1580), ( 1.9800, 0.1550), ( 2.1500, 0.1500), ( 2.2600, 0.1420),
    ( 2.3050, 0.1380),
])

# Taut, athletic arch-hugging hip line
Z_HIP = Curve([
    (-2.4000, 0.6380), (-2.0400, 0.6800), (-1.6400, 0.7220), (-1.3600, 0.7360),
    (-1.0200, 0.7100), (-0.5000, 0.6940), ( 0.0000, 0.6920), ( 0.6500, 0.7020),
    ( 1.1800, 0.7260), ( 1.5400, 0.7400), ( 1.8200, 0.7160), ( 2.0600, 0.6680),
    ( 2.3050, 0.5950),
])

# Taut, athletic 'Ocean Wave' beltline / shoulder crease sweeping from front fender to rear haunch
Z_SHOULDER = Curve([
    (-2.4000, 0.9640), (-2.2200, 0.9700), (-1.9600, 0.9740), (-1.6800, 0.9680),
    (-1.3600, 0.9620), (-0.9800, 0.9440), (-0.4200, 0.9200), ( 0.2500, 0.9020),
    ( 0.8500, 0.8900), ( 1.1200, 0.8780), ( 1.3800, 0.8660), ( 1.5600, 0.8540),
    ( 1.7900, 0.8220), ( 1.9900, 0.7840), ( 2.1700, 0.7360), ( 2.2600, 0.7020),
    ( 2.3050, 0.6840),
])

# Centerline crest with subtle hood center power-dome spine from windshield base to front edge
Z_CREST = Joined(COWL_X, Curve([
    (-2.4000,  0.0060), (-2.1000,  0.0080), (-1.8000,  0.0080), (-1.5000,  0.0020),
    (-1.1200, -0.0120), (-0.5000, -0.0180), ( 0.0000, -0.0180), ( 0.3500, -0.0220),
    ( 0.6000, -0.0220), ( 0.7600, -0.0080), ( 0.8500,  0.0060),
]), Curve([
    ( 0.8500,  0.0060), ( 1.0200,  0.0140), ( 1.2800,  0.0220), ( 1.5600,  0.0250),
    ( 1.8200,  0.0220), ( 2.0400,  0.0160), ( 2.2000,  0.0100), ( 2.3050,  0.0040),
]))

# Tightened, muscular front & rear fender flares with taut athletic waist tuck at mid-door
Y_HIP = Curve([
    (-2.4000, 0.8120), (-2.2400, 0.8460), (-2.0000, 0.8880), (-1.7400, 0.9260),
    (-1.5200, 0.9440), (-1.3600, 0.9480), (-1.1200, 0.9300), (-0.8000, 0.9020),
    (-0.4000, 0.8900), ( 0.0500, 0.8900), ( 0.5500, 0.9000), ( 1.0500, 0.9240),
    ( 1.3600, 0.9440), ( 1.5400, 0.9470), ( 1.7400, 0.9360), ( 1.9000, 0.9120),
    ( 2.0400, 0.8650), ( 2.1500, 0.8120), ( 2.2400, 0.7520), ( 2.3050, 0.7080),
], mode="pchip")

Y_SHOULDER = Curve([
    (-2.4000, 0.7680), (-2.1000, 0.8000), (-1.7800, 0.8360), (-1.3600, 0.8800),
    (-1.0000, 0.8580), (-0.4500, 0.8400), ( 0.1000, 0.8400), ( 0.6000, 0.8500),
    ( 0.9500, 0.8600), ( 1.5000, 0.8750), ( 1.8000, 0.8560), ( 2.0600, 0.8260),
    ( 2.3050, 0.7920),
], mode="pchip")

# Narrowed, tapered coupe-sedan greenhouse roof rail + muscular front fender crowns
Y_ROOF = Curve([
    (-2.4000, 0.6550), (-2.2600, 0.6780), (-2.0800, 0.7050), (-1.7900, 0.7120),
    (-1.4900, 0.6620), (-1.1600, 0.5980), (-0.8400, 0.5480), (-0.4700, 0.5220),
    (-0.1000, 0.5180), ( 0.2500, 0.5450), ( 0.5200, 0.6250), ( 0.7400, 0.7050),
    ( 0.8500, 0.7280), ( 1.1500, 0.7480), ( 1.5200, 0.7600), ( 1.8800, 0.7420),
    ( 2.1800, 0.6620), ( 2.3050, 0.6020),
])

# Tapered cabin greenhouse base over broad rear haunches (creates muscular rear fender shoulder deck)
Y_GLASS = Curve([
    (-2.4000, 0.6900), (-2.0800, 0.7200), (-1.7500, 0.7420), (-1.4000, 0.7680),
    (-1.0200, 0.7980), (-0.5000, 0.8220), ( 0.1000, 0.8300), ( 0.6500, 0.8380),
    ( 0.8500, 0.8450), ( 2.4000, 0.8500),
], mode="pchip")

# Sculpted twin hood power domes inboard of the fender crowns
Z_DOME = Curve([
    (-2.4000, 0.0000), ( 0.8500, 0.0000), ( 1.0000, 0.0060), ( 1.3000, 0.0150),
    ( 1.6500, 0.0180), ( 1.9500, 0.0140), ( 2.1800, 0.0060), ( 2.3050, 0.0000),
], mode="pchip")

Y_DOME = Curve([
    (-2.4000, 0.5200), ( 0.8500, 0.5400), ( 1.2500, 0.5000), ( 1.6500, 0.4400),
    ( 2.0000, 0.3600), ( 2.3050, 0.2600),
], mode="pchip")

Y_ROCKER = Curve([
    (-2.4000, 0.7350), (-2.1400, 0.8120), (-1.9000, 0.8380), (-1.4000, 0.8520),
    (-0.8900, 0.8520), ( 0.0000, 0.8540), ( 1.0500, 0.8520), ( 1.5200, 0.8520),
    ( 1.8900, 0.8480), ( 2.0200, 0.8350), ( 2.1100, 0.8080), ( 2.3050, 0.7320),
], mode="pchip")

# Deep BYD Seal sculpted lower-door undercut (Ocean wave side scallop)
UNDERCUT = Curve([
    (-2.4000, 0.0000), (-1.7000, 0.0000), (-1.0500, 0.0220), (-0.5200, 0.0360),
    ( 0.0000, 0.0380), ( 0.5900, 0.0340), ( 1.0800, 0.0180), ( 1.5200, 0.0000),
    ( 2.4000, 0.0000),
], mode="pchip")

# Custom section recipe with organic arch-to-shoulder tension and crisp Ocean Wave beltline
SEAL_SECTION = Section(
    upper_door=(0.78, 0.006, 0.64),
    step_max=0.034,
    step_in=0.016,
    glass_mid=0.42,
)

# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="BYD Seal", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    y_glass=Y_GLASS, z_dome=Z_DOME, y_dome=Y_DOME,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.145, core_z=0.625, crease="sharp", section=SEAL_SECTION,
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
