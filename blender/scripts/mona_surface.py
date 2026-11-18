"""XPeng Mona L05 (小鹏MONA L05, Autohome series 8662) body surface - profile curves of its fastback-SUV loft.

First pass (2026-11-17): the Voyah Passion S curves morphed onto the Mona's published hardpoints
(carkit.body.morph.station_map through rear end / rear axle / front axle / front end), then edited
curve by curve against the camera-matched studio photographs (mona_cam.py). The section maths lives
in carkit.body.loft (LoftBody).

Real dimensions (MIIT filing / Autohome series 8662):
  - Length x Width x Height: 4870 x 1930 x 1636 mm
  - Wheelbase: 2940 mm (overhangs read off the side silhouette: 930 mm front, 1000 mm rear)
  - Track: about 1640 mm front / 1658 mm rear
  - Tyres: 245/45 R20 (loaded radius 0.354 m)
"""
from carkit.geom import Curve, Joined, smoothstep  # noqa: F401  (re-exported)
from carkit.body import LoftBody
from carkit.body.loft import Section

# --------------------------------------------------------------- dimensions
LENGTH, WIDTH, HEIGHT = 5.010, 1.930, 1.636
FRONT_OVERHANG = 1.070                       # +15% over 0.930 m -> nose tip at x = 2.575
REAR_OVERHANG = 1.000                        # rear tip at x = -2.435
FRONT_AXLE = 1.505                           # wheelbase 2.940 m unchanged
REAR_AXLE = FRONT_AXLE - 2.940               # -1.435
X_FRONT = FRONT_AXLE + FRONT_OVERHANG        # 2.575
HALF_L = X_FRONT                             # forward bound for surface_normal & cutters
HALF_W = WIDTH / 2.0                         # 0.965
WHEEL_R = 0.354                              # 245/45 R20 loaded radius
ARCH_R = 0.505                               # painted wheel opening radius (cladding laps outside it)

V_SHOULDER = 0.520

COWL_X = 1.0297
KNEE_X = -1.6683
BACKLIGHT_X = KNEE_X

# ------------------------------------------------------- longitudinal profile
# Centreline profile = the traced silhouette of c1_0003 (top edge per column, gradient method, 2026-11-17), through
# mona_cam.SIDE at y = 0: the roof peaks at 1.641 m (filed 1.636), the roof's trailing lip ends at x -1.985, z 1.515 and
# falls steeply to the glass line (-2.096, 1.348), the glass rakes 33 degrees to the lamp bar at the tail.
Z_ROOF = Joined(1.0297, Joined(-1.6683, Curve([
    (-2.4350, 1.1750), (-2.3731, 1.1900), (-2.3100, 1.2080), (-2.2210, 1.2670), (-2.1100, 1.3380),
    (-2.0550, 1.4050), (-2.0200, 1.4650), (-1.9850, 1.5150), (-1.8500, 1.5400), (-1.6683, 1.5660),
]), Curve([
    (-1.6683, 1.5660), (-1.5300, 1.5850), (-1.3800, 1.6020), (-1.2200, 1.6150), (-1.0600, 1.6240),
    (-0.9100, 1.6330), (-0.7500, 1.6370), (-0.6000, 1.6370), (-0.4400, 1.6370), (-0.2800, 1.6320),
    (-0.1300, 1.6280), (0.0300, 1.6140), (0.1900, 1.5910), (0.3400, 1.5470), (0.5000, 1.4840),
    (0.6500, 1.4080), (0.8100, 1.3250), (0.9200, 1.2550), (0.9800, 1.2150), (1.0297, 1.1580),
])), Curve([
    (1.0297 + (X_FRONT - 1.0297) * i / 16.0,
     1.1580 - 0.082 * (i / 16.0) - 0.296 * (i / 16.0) ** 2)
    for i in range(17)
], mode="c2"))

Y_FENDER_CROWN = Curve([
    (0.6965, 0.8114), (0.8729, 0.8150), (1.0297, 0.8160), (1.2845, 0.8110),
    (1.6000, 0.7970), (1.9200, 0.7740), (2.1800, 0.7420), (2.3650, 0.7000), (X_FRONT, 0.6300),
], mode="pchip")

# Flush coplanar continuation of the gently convex hood crown onto the upper fenders (zero bowl/cliff).
Z_FENDER_CROWN = Curve([
    (0.6965, 1.1860), (0.8729, 1.1820), (1.0297, 1.1492), (1.2500, 1.1285),
    (1.5050, 1.0911), (1.8000, 1.0301), (2.0500, 0.9624), (2.2500, 0.8976),
    (2.3800, 0.8501), (X_FRONT, 0.7706),
], mode="c2")

Z_FLOOR = Curve([
    (-2.4350, 0.3550), (-2.3350, 0.3400), (-2.1731, 0.3120), (-1.9826, 0.2820),
    (-1.7921, 0.2680), (-1.4350, 0.2640), (-0.7735, 0.2640), (0.0105, 0.2620),
    (0.8435, 0.2600), (1.5050, 0.2560), (1.9600, 0.2540), (2.2200, 0.2600),
    (2.4200, 0.2660), (X_FRONT, 0.2700),
])

Z_HIP = Curve([
    (-2.4350, 0.6400), (-2.1445, 0.7200), (-1.8207, 0.7900), (-1.4350, 0.8200),
    (-0.7245, 0.8300), (0.0105, 0.8200), (0.8435, 0.8200), (1.5050, 0.8150),
    (2.0600, 0.7600), (2.3000, 0.6950), (X_FRONT, 0.6300),
])

Z_SHOULDER = Curve([
    (-2.4350, 1.0650), (-2.2683, 1.0900), (-2.0493, 1.1150), (-1.7921, 1.1320),
    (-1.4350, 1.1450), (-1.1655, 1.1600), (-0.8715, 1.1520), (-0.4795, 1.1420),
    (0.0105, 1.1380), (0.4515, 1.1340), (0.8435, 1.1260), (1.0297, 1.1160),
    (1.2355, 1.1020), (1.5050, 1.0720), (1.8200, 1.0000), (2.0800, 0.9020),
    (2.2600, 0.8020), (2.4200, 0.7680), (X_FRONT, 0.7250),
], mode="pchip")

# Negative Z_CREST across the hood produces a gentle convex crown with no sunk bowl.
Z_CREST = Joined(1.0297, Curve([
    (-2.4350, -0.0580), (-2.2969, -0.0680), (-2.1255, -0.0700), (-1.9350, -0.0560),
    (-1.7636, -0.0360), (-1.6302, -0.0240), (-1.4105, -0.0200), (-0.9695, -0.0200),
    (-0.4305, -0.0180), (0.0105, -0.0180), (0.4025, -0.0240), (0.7455, -0.0180),
    (0.8925, -0.0080), (1.0297, -0.0080),
], mode="pchip"), Curve([
    (1.0297, -0.0080), (1.2800, -0.0110), (1.5500, -0.0125), (1.8500, -0.0120),
    (2.1500, -0.0105), (2.3650, -0.0090), (X_FRONT, -0.0080),
], mode="c2"))

Y_HIP = Curve([
    (-2.4350, 0.7969), (-2.2969, 0.8549), (-2.1255, 0.8935), (-1.8874, 0.9254),
    (-1.6493, 0.9409), (-1.4350, 0.9466), (-1.1165, 0.9351), (-0.6265, 0.9225),
    (0.0105, 0.9225), (0.5985, 0.9293), (1.1375, 0.9409), (1.5050, 0.9466),
    (1.8500, 0.9380), (2.0800, 0.9100), (2.2800, 0.8580), (2.4300, 0.7900), (X_FRONT, 0.6900),
])

Y_SHOULDER = Curve([
    (-2.4350, 0.6520), (-2.2683, 0.7196), (-2.1064, 0.7776), (-1.8874, 0.8356),
    (-1.6493, 0.8616), (-1.4350, 0.8742), (-1.1655, 0.8771), (-0.6265, 0.8742),
    (0.0105, 0.8742), (0.5985, 0.8790), (1.0297, 0.8839), (1.5050, 0.8935),
    (1.9200, 0.8780), (2.1800, 0.8420), (2.3650, 0.7900), (2.4800, 0.7350), (X_FRONT, 0.6600),
])

Y_ROOF = Curve([
    (-2.4350, 0.5265), (-2.2969, 0.5313), (-2.0302, 0.5168), (-1.6969, 0.5361),
    (-1.3125, 0.5603), (-0.9205, 0.5776), (-0.4795, 0.5912), (0.0105, 0.5970),
    (0.2849, 0.6134), (0.4809, 0.6617), (0.6769, 0.7167), (0.8729, 0.7631),
    (1.0297, 0.7776), (1.2845, 0.7730), (1.6000, 0.7580), (1.9200, 0.7350),
    (2.1800, 0.7000), (2.3650, 0.6550), (X_FRONT, 0.5800),
], mode="pchip")

Y_GLASS = Curve([
    (-2.4350, 1.2000), (-2.2969, 1.2000), (-2.1255, 0.7100), (-1.8874, 0.6955),
    (-1.6302, 0.6907), (-1.3615, 0.7003), (-1.1165, 0.7293), (-0.8715, 0.7824),
    (-0.6265, 0.8452), (-0.3815, 1.2000), (X_FRONT, 1.2000),
], mode="pchip")

Z_STEP = Curve([
    (-2.4350, 0.0280), (-2.2017, 0.0420), (-1.9540, 0.0640), (-1.6683, 0.0660),
    (-1.3811, 0.0620), (-1.1165, 0.0420), (-0.8715, 0.0280), (0.7357, 0.0280),
    (0.8729, 0.0190), (1.0297, 0.0180), (X_FRONT, 0.0120),
], mode="pchip")

SOFT = Curve([(-2.4350, 1.0000), (-1.3811, 1.0000), (-0.8715, 0.0000), (X_FRONT, 0.0000)], mode="pchip")

Y_ROCKER = Curve([
    (-2.4350, 0.7728), (-2.2017, 0.8501), (-1.9160, 0.8887), (-1.4350, 0.9032),
    (-0.9695, 0.9061), (0.0105, 0.9099), (0.9905, 0.9061), (1.5050, 0.9003),
    (1.9600, 0.8920), (2.1700, 0.8660), (2.3600, 0.8220), (X_FRONT, 0.7400),
], mode="pchip")

UNDERCUT = Curve([
    (-2.4350, 0.0000), (-1.8398, 0.0000), (-1.1165, 0.0160), (-0.6265, 0.0260),
    (0.4515, 0.0260), (0.8925, 0.0140), (1.3335, 0.0000), (X_FRONT, 0.0000),
], mode="pchip")


# ------------------------------------------------------------------ the loft
def SECTION_AT(x):
    """Ahead of the A-pillar foot (x >= 0.880), pin upper[2] to the smooth C2 fender crown
    (Y_FENDER_CROWN, Z_FENDER_CROWN) so the front fender and hood form one flush convex sheet."""
    t = smoothstep((x - 0.740) / 0.140)
    if t <= 0.0:
        return None
    th_hood = smoothstep((x - 0.960) / 0.070)
    lerp = lambda a, b: a + (b - a) * t
    lerp_h = lambda a, b: a + (b - a) * th_hood
    sbr = lerp(0.045, 0.020)
    zs = min(max(Z_SHOULDER(x), Z_HIP(x) + 0.08), Z_ROOF(x) - sbr)
    head = max(1e-4, Z_ROOF(x) - zs)
    crest = Z_CREST(x)
    tc = lerp(0.40, 1.00)
    th_target = (Z_FENDER_CROWN(x) - zs - crest * tc) / head
    th = lerp(0.52, th_target)
    ys, yrf = Y_SHOULDER(x), Y_ROOF(x)
    ts_target = (Y_FENDER_CROWN(x) - yrf) / max(1e-4, ys - yrf)
    ts = lerp(0.36, ts_target)
    tr = 1.0 - ts
    return dict(
        step_in=lerp(0.045, 0.028),
        step_max=lerp(0.028, 0.019),
        tumble=(ts, tr, th, tc),
        shoulder_below_roof=sbr,
        rail_in=lerp_h(0.52, 0.50),
        rail_crest=lerp_h(0.34, 0.25),
    )


BODY = LoftBody(
    name="XPeng Mona L05", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.125, core_z=0.72, crease="sharp", z_dome=None, y_dome=None,
    y_glass=Y_GLASS, z_step=Z_STEP, soft=SOFT,
    section=Section(step_in=0.045, step_max=0.028, tumble=(0.36, 0.64, 0.52, 0.40)),
    section_at=SECTION_AT,
)
BODY.HALF_L = X_FRONT

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
