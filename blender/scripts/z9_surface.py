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
# 2026-11-15: the roof is the PHOTOGRAPHED car's (c1_0036 through the solved side camera: its roof peaks at 1.453 m, 4-5 cm
# under the published 1.50, and the deck falls to the ducktail at x -2.40, not -2.61): old knots in the comment below.
#   (-2.61, 0.995) (-2.55, 1.008) (-2.42, 1.025) (-2.26, 1.055) (-2.00, 1.120) (-1.7066, 1.215) (-1.4557, 1.318)
#   (-1.1953, 1.398) (-0.9349, 1.452) (-0.6745, 1.485) (-0.4141, 1.500) (-0.2057, 1.4985) (0.0026, 1.484) (0.2109, 1.44)
#   (0.4193, 1.351)
Z_ROOF = Joined(COWL_X, Curve([
    (-2.6100, 0.9750), (-2.5000, 0.9800), (-2.4000, 0.9880), (-2.2600, 1.0130),
    (-2.0000, 1.0900), (-1.7066, 1.1900), (-1.4557, 1.2880), (-1.1953, 1.3630),
    (-0.9349, 1.4170), (-0.6745, 1.4450), (-0.4141, 1.4500), (-0.2057, 1.4470),
    ( 0.0026, 1.4340), ( 0.2109, 1.4020), ( 0.4193, 1.3360), ( 0.6484, 1.2100),
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

# 2026-11-15: the rear haunches come IN by up to 5 cm (the black car's rear photograph c1_0038: the tyres' outer walls
# stand 3.5-6 cm proud of the body at the hip, the model's hips were as wide as its tyres). Old: (-2.61, 0.8829)
# (-2.503, 0.9051) (-2.3039, 0.9394) (-2.055, 0.9677) (-1.7763, 0.9879) (-1.5, 0.995) (-1.1432, 0.9819) (-0.6224, 0.9697)
Y_HIP = Curve([
    (-2.6100, 0.8400), (-2.5030, 0.8650), (-2.3039, 0.8980), (-2.0550, 0.9200),
    (-1.7763, 0.9300), (-1.5000, 0.9330), (-1.1432, 0.9400), (-0.6224, 0.9590),
    ( 0.0026, 0.9637), ( 0.6276, 0.9718), ( 1.2526, 0.9859), ( 1.7654, 0.9950),
    ( 2.0116, 0.9778), ( 2.1101, 0.9556), ( 2.2086, 0.9213), ( 2.3071, 0.8788),
    ( 2.3780, 0.8435), ( 2.5050, 0.7677),
])

Y_SHOULDER = Curve([
    (-2.6100, 0.7950), (-2.3537, 0.8200), (-2.0550, 0.8350), (-1.5000, 0.8700),
    (-1.1432, 0.8900), ( 0.0026, 0.9060), ( 0.6276, 0.9112), ( 1.0495, 0.9142),
    ( 1.6250, 0.9182), ( 1.9624, 0.9071), ( 2.2579, 0.8849), ( 2.5050, 0.8647),
])

# 2026-11-15: more tumblehome behind the B-pillar: the rear greenhouse is narrower than the model's was (c1_0038: the
# roof/C-pillar edge reads 0.58 m half-width at z 1.35, 0.63 at 1.25, 0.67 at 1.18; the model's were 6-10 cm wider)
Y_ROOF = Curve([
    (-2.6100, 0.6500), (-2.4731, 0.6650), (-2.2541, 0.6800), (-2.0052, 0.6850),
    (-1.7066, 0.6550), (-1.3516, 0.6250), (-0.9870, 0.5950), (-0.5703, 0.5780),
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
# (2026-11-15: the old 26 mm undercut centred at z 0.47 is now the channel's job: 8 mm left, so the door's belly is not
# dented twice)
UNDERCUT = Curve([
    (-2.6100, 0.0000), (-1.9057, 0.0000), (-1.1432, 0.0060), (-0.6224, 0.0080),
    ( 0.6276, 0.0080), ( 1.1484, 0.0050), ( 1.6669, 0.0000), ( 2.6100, 0.0000),
], mode="pchip")

# 2026-11-15: TUMBLEHOME. Seen from behind (c1_0038) the cabin above the shoulder is much narrower than the haunches: the
# envelope reads 0.867 m at z 0.98 but only 0.695 m at z 1.11 (x -1.5), the model's was 0.81. Behind the front doors the
# beltline steps further in (step_in 0.014 -> 0.075) and the roof's lean starts lower (tumble shares 0.60/0.40 -> 0.50/0.50).
def _section_at(x):
    t = min(1.0, max(0.0, (-0.55 - x) / 0.80))
    t = t * t * (3.0 - 2.0 * t)
    if t <= 0.0:
        return None
    return dict(step_in=0.014 + (0.075 - 0.014) * t,
                tumble=(0.60 - 0.10 * t, 0.40 + 0.10 * t, 0.56, 0.40))


# 2026-11-15: the LOWER-DOOR CHANNEL. The photographed car (c1_0036, c1_0040) has a convex tall door that ends in a sharp
# lip - a diagonal edge from the fender vent's rear corner sweeping down to the sill, then horizontal along both doors at
# z ~ 0.42 - and under that lip a recessed, dark sill panel. The model had a 3 mm crease at z 0.31 (10 cm too low). The lip's
# path, read off the clean side photograph (hub-plane scale 322 px/m, hubs (520, 1065) and (1527, 1065)), and the depth the
# recess steps in.
LIP_PTS = [(-1.30, 0.540), (-1.15, 0.490), (-0.90, 0.446), (-0.60, 0.428), (-0.20, 0.418), (0.20, 0.416), (0.45, 0.420),
           (0.575, 0.428), (0.70, 0.485), (0.90, 0.600), (1.08, 0.735)]
LIP = Curve(LIP_PTS, mode="pchip")
CHANNEL_DEPTH = 0.034
CHANNEL_FILLET = 0.030          # the lip's step: how far below it the surface has gone in
CHANNEL_X = (-1.32, 1.10)


def _sstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def channel_depth(x):
    """How far in the recess is at station x (m): full along the doors, fading out at its two ends."""
    a, b = CHANNEL_X
    return CHANNEL_DEPTH * _sstep((x - a) / 0.16) * _sstep((b - x) / 0.10)


class Z9Loft(LoftBody):
    """The Z9's flank loft: LoftBody plus the lower-door channel, applied to every section's points (the lip at LIP(x); below
    it the skin steps in by channel_depth(x) over CHANNEL_FILLET and holds that to the sill, where it fades out)."""

    def section(self, x, n_lower=None, n_upper=None):
        n_lower = self.n_lower if n_lower is None else n_lower
        n_upper = self.n_upper if n_upper is None else n_upper
        key = (round(x, 4), n_lower, n_upper)
        hit = self._chan_cache.get(key)
        if hit is not None:
            return hit
        pts = LoftBody.section(self, x, n_lower, n_upper)
        d0 = channel_depth(x)
        if d0 > 1e-5:
            zl, zr = LIP(min(max(x, LIP_PTS[0][0]), LIP_PTS[-1][0])), self.z_rocker(x)
            out = []
            for (y, z) in pts:
                if z < zl and z > zr:
                    k = _sstep((zl - z) / CHANNEL_FILLET) * _sstep((z - zr) / 0.07)
                    y = y - d0 * k
                out.append((y, z))
            pts = out
        if len(self._chan_cache) > 40000:
            self._chan_cache.clear()
        self._chan_cache[key] = pts
        return pts

    _chan_cache = {}


# ------------------------------------------------------------------ the loft
BODY = Z9Loft(
    name="Denza Z9", length=LENGTH, width=WIDTH, height=HEIGHT,
    front_axle=FRONT_AXLE, rear_axle=REAR_AXLE, wheel_r=WHEEL_R, arch_r=ARCH_R,
    z_roof=Z_ROOF, z_floor=Z_FLOOR, y_hip=Y_HIP, z_hip=Z_HIP,
    z_shoulder=Z_SHOULDER, y_shoulder=Y_SHOULDER, y_roof=Y_ROOF,
    y_rocker=Y_ROCKER, undercut=UNDERCUT, z_crest=Z_CREST,
    v_shoulder=V_SHOULDER, cowl_x=COWL_X, backlight_x=BACKLIGHT_X,
    sill_height=0.150, core_z=0.64, crease="sharp", section_at=_section_at, n_lower=64,
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
