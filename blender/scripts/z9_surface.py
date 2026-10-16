"""Denza Z9 body surface - the profile curves of its flank loft.

The section maths lives in carkit.body.loft (LoftBody). This module is the Z9's
DATA: its dimensions and the profile curves every section is built from,
morphed from Xiaomi SU7 Ultra donor geometry and refined against Autohome series
7838 studio turnarounds (c1_0001..0008, c1_0040, c1_0042, c1_0046).

Real dimensions (Autohome spec 69564, Denza Z9 630km Max AWD BEV):
    5220 x 1990 x 1500 mm
    wheelbase 3125 mm
    track 1710 mm front / 1715 mm rear
    tyres 255/45 R20 front, 275/45 R20 rear (21-inch optional: 255/40 R21 / 275/40 R21)
    overhangs: 985 mm front / 1110 mm rear
    loaded hub height: ~0.3620 m
"""
from carkit.geom import Curve, Joined
from carkit.body import LoftBody

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.220, 1.990, 1.500
HALF_L = LENGTH / 2.0                # 2.610
HALF_W = WIDTH / 2.0                 # 0.995
WHEELBASE = 3.125
FRONT_OVERHANG = 0.985
REAR_OVERHANG = LENGTH - WHEELBASE - FRONT_OVERHANG  # 1.110
FRONT_AXLE = HALF_L - FRONT_OVERHANG                 # 1.6250
REAR_AXLE = FRONT_AXLE - WHEELBASE                   # -1.5000
WHEEL_R = 0.3620                                     # loaded hub height
TRACK_F, TRACK_R = 1.710, 1.715
ARCH_R = 0.4080                                      # wheelhouse opening radius

V_SHOULDER = 0.520

COWL_X = 0.9870                                      # windscreen base / A-pillar foot
KNEE_X = -2.2600                                     # fastback backlight base / short ducktail deck
BACKLIGHT_X = KNEE_X

# Longitudinal profile calibrated to Denza Z9 studio turnaround (c1_0004.jpg, c1_0042.jpg, c1_0046.jpg)
# and side reference (attachments 1 & 2):
# - Pointy forward-projecting prow with hood sloping continuously down to x = 2.505 m at z ≈ 0.730 m
# - High front fender crowns (z ≈ 0.85-0.88 m) well above the wheel arch (top = 0.770 m)
# - Executive fastback roofline peaking at 1.500 m with wide, elongated backlight down to x = -2.260 m
# - Compact rear decklid with integrated ducktail spoiler shelf reaching x = -2.610 m
Z_ROOF = Joined(COWL_X, Curve([
    (-2.6100, 0.9950), (-2.5500, 1.0080), (-2.4200, 1.0250), (-2.2600, 1.0550),
    (-2.0000, 1.1200), (-1.7066, 1.2150), (-1.4557, 1.3180), (-1.1953, 1.3980),
    (-0.9349, 1.4520), (-0.6745, 1.4850), (-0.4141, 1.5000), (-0.2057, 1.4985),
    ( 0.0026, 1.4840), ( 0.2109, 1.4400), ( 0.4193, 1.3510), ( 0.6484, 1.2100),
    ( 0.8359, 1.0900), ( 0.9870, 0.9952),
]), Curve([
    ( 0.9870, 0.9952), ( 1.1484, 0.9780), ( 1.3568, 0.9580), ( 1.5651, 0.9380),
    ( 1.7654, 0.9100), ( 1.9624, 0.8650), ( 2.1594, 0.8150), ( 2.3200, 0.7700),
    ( 2.4200, 0.7450), ( 2.5050, 0.7300),
]))

Z_FLOOR = Curve([
    (-2.6100, 0.2683), (-2.4731, 0.2580), (-2.2939, 0.2375), (-2.0749, 0.2007),
    (-1.8360, 0.1761), (-1.5000, 0.1597), ( 0.0026, 0.1515), ( 1.6250, 0.1597),
    ( 1.9427, 0.1659), ( 2.1101, 0.1638), ( 2.2953, 0.1597), ( 2.4500, 0.1500),
    ( 2.5050, 0.1433),
])

Z_HIP = Curve([
    (-2.6100, 0.6400), (-2.3000, 0.6800), (-1.5000, 0.7120), (-0.6224, 0.7180),
    ( 0.0026, 0.7188), ( 0.8359, 0.7250), ( 1.3568, 0.7380), ( 1.7654, 0.7450),
    ( 2.2086, 0.7000), ( 2.5050, 0.6200),
])

Z_SHOULDER = Curve([
    (-2.6100, 0.9950), (-2.4800, 1.0020), (-2.2541, 1.0050), (-1.9554, 0.9980),
    (-1.7066, 0.9900), (-1.1432, 0.9750), (-0.5182, 0.9600), ( 0.3151, 0.9430),
    ( 0.9870, 0.9320), ( 1.2526, 0.9150), ( 1.5130, 0.8980), ( 1.7161, 0.8800),
    ( 1.9500, 0.8520), ( 2.1600, 0.8180), ( 2.3600, 0.7750), ( 2.4500, 0.7450),
    ( 2.5050, 0.7250),
])

Z_CREST = Joined(COWL_X, Curve([
    (-2.6100,  0.0080), (-2.3537,  0.0100), (-2.0550,  0.0100), (-1.7563,  0.0050),
    (-1.3516, -0.0120), (-0.6224, -0.0200), ( 0.0026, -0.0210), ( 0.3672, -0.0280),
    ( 0.6797, -0.0300), ( 0.8880, -0.0120), ( 0.9870,  0.0010),
]), Curve([
    ( 0.9870,  0.0010), ( 1.1484,  0.0050), ( 1.3568,  0.0080), ( 1.6669,  0.0120),
    ( 1.8639,  0.0120), ( 2.0609,  0.0100), ( 2.2579,  0.0080), ( 2.4549,  0.0050),
    ( 2.5050,  0.0020),
]))

Y_HIP = Curve([
    (-2.6100, 0.8829), (-2.5030, 0.9051), (-2.3039, 0.9394), (-2.0550, 0.9677),
    (-1.7763, 0.9879), (-1.5000, 0.9950), (-1.1432, 0.9819), (-0.6224, 0.9697),
    ( 0.0026, 0.9637), ( 0.6276, 0.9718), ( 1.2526, 0.9859), ( 1.7654, 0.9950),
    ( 2.0116, 0.9778), ( 2.1101, 0.9556), ( 2.2086, 0.9213), ( 2.3071, 0.8788),
    ( 2.3780, 0.8435), ( 2.5050, 0.7677),
])

Y_SHOULDER = Curve([
    (-2.6100, 0.8324), (-2.3537, 0.8586), (-2.0550, 0.8809), (-1.5000, 0.9233),
    (-1.1432, 0.9162), ( 0.0026, 0.9091), ( 0.6276, 0.9112), ( 1.0495, 0.9142),
    ( 1.6250, 0.9182), ( 1.9624, 0.9071), ( 2.2579, 0.8849), ( 2.5050, 0.8647),
])

Y_ROOF = Curve([
    (-2.6100, 0.7192), (-2.4731, 0.7435), (-2.2541, 0.7758), (-2.0052, 0.7879),
    (-1.7066, 0.7374), (-1.3516, 0.6687), (-0.9870, 0.6101), (-0.5703, 0.5798),
    (-0.1536, 0.5758), ( 0.2630, 0.6061), ( 0.5755, 0.6889), ( 0.8359, 0.7677),
    ( 1.2526, 0.7899), ( 1.6866, 0.7980), ( 2.0609, 0.7859), ( 2.3780, 0.7071),
    ( 2.5050, 0.6465),
])

Y_ROCKER = Curve([
    (-2.6100, 0.7879), (-2.3537, 0.8687), (-2.1048, 0.8930), (-1.5000, 0.8990),
    (-1.0391, 0.9091), ( 0.0026, 0.9142), ( 1.1484, 0.9091), ( 1.6250, 0.8990),
    ( 2.0609, 0.9091), ( 2.2086, 0.8970), ( 2.3071, 0.8687), ( 2.5050, 0.7879),
], mode="pchip")

# Denza Z9 sculpted lower-door undercut ("Z" side channel)
UNDERCUT = Curve([
    (-2.6100, 0.0000), (-1.9057, 0.0000), (-1.1432, 0.0160), (-0.6224, 0.0260),
    ( 0.6276, 0.0260), ( 1.1484, 0.0150), ( 1.6669, 0.0000), ( 2.6100, 0.0000),
], mode="pchip")

# ------------------------------------------------------------------ the loft
BODY = LoftBody(
    name="Denza Z9", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.150, core_z=0.64, crease="sharp",
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
