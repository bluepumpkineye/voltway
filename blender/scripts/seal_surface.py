"""BYD Seal (比亚迪 海豹, Autohome Series 6394, the 2022-2024 body) body surface.

The section maths lives in carkit.body.loft (LoftBody). This module defines the BYD Seal's DATA:
dimensions and profile curves of the Ocean X electric sports sedan, READ FROM PHOTOGRAPHS (see
seal_cam.py: the side camera is solved from the blue car's c1_0513.jpg rim lips and the 2.920 m
wheelbase; the roof/hood/deck centreline below is that photo's silhouette in metres).

Real dimensions (Autohome Series 6394):
    4800 x 1875 x 1460 mm, wheelbase 2920 mm, track 1620 / 1625 mm, tyres 235/45 R19
    overhangs 880 / 1000 mm (read off the photo: 0.892 / 0.996)
"""
from carkit.geom import Curve, Joined
from carkit.body import LoftBody, Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 4.800, 1.875, 1.460
HALF_L = LENGTH / 2.0                # 2.4000
HALF_W = WIDTH / 2.0                 # 0.9375
WHEELBASE = 2.920
FRONT_OVERHANG = 0.880
REAR_OVERHANG = LENGTH - WHEELBASE - FRONT_OVERHANG  # 1.000
FRONT_AXLE = HALF_L - FRONT_OVERHANG                 # +1.520
REAR_AXLE = FRONT_AXLE - WHEELBASE                   # -1.400
WHEEL_R = 0.343                                      # loaded hub height (235/45 R19: 0.347 free)
TRACK_F, TRACK_R = 1.620, 1.625
ARCH_R = 0.390                                       # wheelhouse opening radius (arch crown z 0.733)

V_SHOULDER = 0.530

# windscreen base on the centreline (the hood meets the screen at x 1.07, z 0.966 in the photo) and
# the backlight's foot where the glass hands over to the short boot lid
COWL_X = 1.0700
KNEE_X = -2.0000
BACKLIGHT_X = KNEE_X

# Centreline of the roof, read from c1_0513 (the blue car's side silhouette, y = 0 plane):
# hood 0.97 -> 0.70 over 1.2 m, screen at ~29 degrees, one flat arc peaking at x -0.36 (z 1.446),
# a long fastback glass (23 degrees) that eases to a short boot lid, ending in the duck-tail lip.
Z_ROOF = Joined(COWL_X, Curve([
    (-2.4000, 1.0150), (-2.3300, 1.0200), (-2.2600, 1.0270), (-2.1840, 1.0360),
    (-2.0620, 1.0660), (-1.9410, 1.1040), (-1.8200, 1.1550), (-1.6980, 1.2070),
    (-1.5770, 1.2560), (-1.4560, 1.3010), (-1.3340, 1.3400), (-1.2130, 1.3740),
    (-1.0920, 1.3980), (-0.9700, 1.4150), (-0.8490, 1.4280), (-0.7280, 1.4360),
    (-0.6060, 1.4420), (-0.4850, 1.4450), (-0.3640, 1.4460), (-0.2420, 1.4440),
    (-0.1210, 1.4360), ( 0.0000, 1.4220), ( 0.1220, 1.4040), ( 0.2430, 1.3770),
    ( 0.3640, 1.3370), ( 0.4860, 1.2920), ( 0.6070, 1.2360), ( 0.7280, 1.1740),
    ( 0.8500, 1.1070), ( 0.9700, 1.0370), ( 1.0700, 0.9660),
], mode="pchip"), Curve([
    ( 1.0700, 0.9660), ( 1.1530, 0.9610), ( 1.2740, 0.9520), ( 1.3950, 0.9430),
    ( 1.5170, 0.9320), ( 1.6380, 0.9140), ( 1.7600, 0.8920), ( 1.8800, 0.8630),
    ( 2.0000, 0.8230), ( 2.0600, 0.8050), ( 2.1500, 0.7750), ( 2.2500, 0.7250),
    ( 2.3050, 0.6950),
], mode="pchip"))

# underbody: the black sill's top edge is z 0.25-0.29 (c1_0506), sill_height 0.15 below it
Z_FLOOR = Curve([
    (-2.4000, 0.2000), (-2.2400, 0.1850), (-2.0400, 0.1700), (-1.8200, 0.1450),
    (-1.5800, 0.1250), (-1.3600, 0.1180), ( 0.0000, 0.1050), ( 1.5400, 0.1150),
    ( 1.8000, 0.1250), ( 1.9800, 0.1300), ( 2.1500, 0.1300), ( 2.2600, 0.1250),
    ( 2.3050, 0.1200),
])

# widest point over the arches. On the doors it IS the Ocean Wave crease: the sharp ridge across
# both doors (c1_0513 with contrast stretched: z 0.75 at the fender gill, peaking at 0.862 over the
# door split, falling to 0.80 at the rear door's edge), the surface under it a dark concave scoop
Z_HIP = Curve([
    (-2.4000, 0.5200), (-2.0400, 0.5400), (-1.7000, 0.5400), (-1.4500, 0.5400),
    (-1.2500, 0.6400), (-1.0000, 0.8200), (-0.6000, 0.8620), (-0.3000, 0.8600),
    ( 0.1000, 0.8300), ( 0.5500, 0.7900), ( 1.0000, 0.7400), ( 1.1800, 0.7000),
    ( 1.5400, 0.6600), ( 1.8200, 0.6500), ( 2.0600, 0.6200), ( 2.3050, 0.5700),
])

# the crease below the glass: the belt (glass base) read on the doors is z 0.965 at the A-pillar
# foot (x 0.93) rising to 1.073 at the rear door's tail (x -1.19); the section's step adds ~0.03
Z_SHOULDER = Curve([
    (-2.4000, 0.9550), (-2.2600, 0.9600), (-2.0000, 1.0000), (-1.6000, 1.0380),
    (-1.1900, 1.0420), (-0.6300, 1.0220), (-0.1800, 1.0020), ( 0.3700, 0.9750),
    ( 0.9300, 0.9350), ( 1.1000, 0.9000), ( 1.3800, 0.8780), ( 1.5600, 0.8560),
    ( 1.7900, 0.8220), ( 1.9900, 0.7840), ( 2.1700, 0.7360), ( 2.2600, 0.7020),
    ( 2.3050, 0.6840),
])

# centreline crest: the roof is gently crowned, the hood has a low central ridge
Z_CREST = Joined(COWL_X, Curve([
    (-2.4000,  0.0060), (-2.1000,  0.0080), (-1.8000,  0.0000), (-1.5000, -0.0100),
    (-1.1200, -0.0220), (-0.5000, -0.0300), ( 0.0000, -0.0300), ( 0.3500, -0.0280),
    ( 0.6000, -0.0200), ( 0.7600, -0.0100), ( 1.0700,  0.0060),
]), Curve([
    ( 1.0700,  0.0000), ( 1.2800, -0.0040), ( 1.5600, -0.0080), ( 1.8200, -0.0100),
    ( 2.0400, -0.0090), ( 2.2000, -0.0060), ( 2.3050, -0.0030),
]))

# half-width over the arches: 1875 mm overall
Y_HIP = Curve([
    (-2.4000, 0.7900), (-2.2400, 0.8200), (-2.0000, 0.8600), (-1.7400, 0.9050),
    (-1.5200, 0.9340), (-1.3600, 0.9375), (-1.1200, 0.9200), (-0.8000, 0.8920),
    (-0.4000, 0.8800), ( 0.0500, 0.8800), ( 0.5500, 0.8900), ( 1.0500, 0.9140),
    ( 1.3600, 0.9340), ( 1.5400, 0.9375), ( 1.7400, 0.9260), ( 1.9000, 0.9020),
    ( 2.0400, 0.8560), ( 2.1500, 0.8030), ( 2.2400, 0.7440), ( 2.3050, 0.7000),
], mode="pchip")

Y_SHOULDER = Curve([
    (-2.4000, 0.7400), (-2.1000, 0.7700), (-1.7800, 0.8100), (-1.3600, 0.8550),
    (-1.0000, 0.8580), (-0.4500, 0.8400), ( 0.1000, 0.8400), ( 0.6000, 0.8500),
    ( 0.9500, 0.8600), ( 1.5000, 0.8750), ( 1.8000, 0.8560), ( 2.0600, 0.8260),
    ( 2.3050, 0.7920),
], mode="pchip")

# roof rail half-width / fender crowns
Y_ROOF = Curve([
    (-2.4000, 0.5200), (-2.2600, 0.5400), (-2.0800, 0.5600), (-1.7900, 0.5750),
    (-1.4900, 0.5750), (-1.1600, 0.5800), (-0.8400, 0.5850), (-0.4700, 0.5850),
    (-0.1000, 0.5850), ( 0.2500, 0.5750), ( 0.5200, 0.6200), ( 0.7400, 0.6750),
    ( 0.8500, 0.7000), ( 1.1500, 0.7400), ( 1.5200, 0.7600), ( 1.8800, 0.7420),
    ( 2.1800, 0.6620), ( 2.3050, 0.6020),
])

# greenhouse base over the broad rear haunches
Y_GLASS = Curve([
    (-2.4000, 0.6500), (-2.0800, 0.6750), (-1.7500, 0.6950), (-1.4000, 0.7200),
    (-1.0200, 0.7650), (-0.5000, 0.8000), ( 0.1000, 0.8300), ( 0.6500, 0.8380),
    ( 0.8500, 0.8450), ( 2.4000, 0.8500),
], mode="pchip")

# no hood domes on the Seal: one smooth bonnet with a soft central crown
Z_DOME = None
Y_DOME = None

Y_ROCKER = Curve([
    (-2.4000, 0.7350), (-2.1400, 0.8120), (-1.9000, 0.8380), (-1.4000, 0.8520),
    (-0.8900, 0.8520), ( 0.0000, 0.8540), ( 1.0500, 0.8520), ( 1.5200, 0.8520),
    ( 1.8900, 0.8480), ( 2.0200, 0.8350), ( 2.1100, 0.8080), ( 2.3050, 0.7320),
], mode="pchip")

# lower-door concavity: the scoop under the Ocean Wave crease
UNDERCUT = Curve([
    (-2.4000, 0.0000), (-1.7000, 0.0000), (-1.3000, 0.0200), (-1.0000, 0.0400),
    (-0.5000, 0.0500), ( 0.0000, 0.0500), ( 0.5000, 0.0450), ( 0.9500, 0.0300),
    ( 1.3000, 0.0100), ( 1.5200, 0.0000), ( 2.4000, 0.0000),
], mode="pchip")

SEAL_SECTION = Section(
    upper_door=(0.55, 0.006, 0.64),
    step_max=0.030,
    step_in=0.016,
    glass_mid=0.42,
    tumble=(0.50, 0.50, 0.56, 0.40),
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
    sill_height=0.150, core_z=0.625, crease="sharp", section=SEAL_SECTION,
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
