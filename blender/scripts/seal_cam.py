"""BYD Seal (海豹, Autohome series 6394, the 2022-2024 body): photo readings and their conversion to
model metres.

Two side cameras, both from near-orthographic long-lens photographs (3840 x 2880) of the same
studio-less car park: BLUE c1_0513.jpg (silhouette, colour) and WHITE c1_0506.jpg (the shut lines
read cleanly on white paint; the car stands 0.9 % further away). Everything below is written in
PIXELS of those photographs and turned into model coordinates at the plane the feature lies on,
so a reading stays checkable (`seal_ref_match.overlay` draws the built panel lines over the photo).

What is certain (nothing is fitted to the model):
    rim lips (photo_tools.fit_rim, axis ratio 0.996): BLUE front (895.7, 2037.2) rear (2945.5, 2038.9),
    WHITE front (895.95, 2035.25) rear (2928.2, 2045.5); lip radius 183 px
    wheelbase 2.920 m (Autohome) -> 702.0 / 696.0 px/m at the hub plane (y 0.85)
    rolls 0.05 / 0.29 degrees; the camera is 1.195 m high
    f and D are set by the car's length (4.800 m: nose tip u 370, tail tip u 3540 -> D 14.0 m)
    overhangs from it: 0.892 m front, 0.996 m rear (Autohome: 880 / 1000)

Model coordinates: +X forward, +Y to the car's left, Z up, the length centred on x = 0
(front axle +1.520, rear axle -1.400).

    side_xz(u, v, y, cam)   (x, z) of the side photo's pixel on the plane y
    side_uv(x, z, y, cam)   its inverse
    xz(px, y, cam)          [(x, z)] sorted by x (lines along the car)
    zx(px, y, cam)          [(z, x)] sorted by height (near-vertical lines)
"""
import math

W, H = 3840, 2880
D = 14.0                          # camera distance from the centre plane (y = 0)
Y_HUB = 0.85                      # the plane the hub scale is read on
WHEELBASE = 2.920
FRONT_AXLE = 1.520
HUB_Z = 0.343                     # loaded hub height (235/45 R19: 0.347 free)


class SideCam:
    """A level side camera (nose to the LEFT of the picture) from the two hub centres."""

    def __init__(self, front, rear, d=D, y_hub=Y_HUB):
        (uf, vf), (ur, vr) = front, rear
        self.d, self.y_hub = d, y_hub
        self.k = math.hypot(ur - uf, vr - vf) / WHEELBASE
        self.roll = math.atan2(vr - vf, ur - uf)
        self.f = self.k * (d - y_hub)
        c, s = math.cos(self.roll), math.sin(self.roll)
        self._c, self._s = c, s
        du, dv = uf - 0.5 * W, vf - 0.5 * H
        duf, dvf = c * du + s * dv, -s * du + c * dv
        depth = d - y_hub
        self.cx = FRONT_AXLE + duf * depth / self.f
        self.cz = HUB_Z + dvf * depth / self.f

    def side_xz(self, u, v, y=0.0):
        du, dv = u - 0.5 * W, v - 0.5 * H
        du, dv = self._c * du + self._s * dv, -self._s * du + self._c * dv
        depth = self.d - y
        return (self.cx - du * depth / self.f, self.cz - dv * depth / self.f)

    def side_uv(self, x, z, y=0.0):
        depth = self.d - y
        du = -(x - self.cx) * self.f / depth
        dv = -(z - self.cz) * self.f / depth
        c, s = self._c, self._s
        du, dv = c * du - s * dv, s * du + c * dv
        return (0.5 * W + du, 0.5 * H + dv)


BLUE = SideCam((895.7, 2037.15), (2945.5, 2038.9))
WHITE = SideCam((895.95, 2035.25), (2928.17, 2045.47))
CAMS = {"blue": BLUE, "white": WHITE}


def side_xz(u, v, y=0.0, cam="white"):
    return CAMS[cam].side_xz(u, v, y)


def side_uv(x, z, y=0.0, cam="white"):
    return CAMS[cam].side_uv(x, z, y)


def zx(px, y=0.0, cam="white"):
    return sorted((z, x) for (x, z) in (side_xz(u, v, y, cam) for (u, v) in px))


def xz(px, y=0.0, cam="white"):
    return sorted(side_xz(u, v, y, cam) for (u, v) in px)


# ------------------------------------------------------------- the flank's lines (WHITE car, y ~ 0.92 skin)
Y_SKIN = 0.92
# front door's leading edge, cowl corner to the sill
DOOR_F_EDGE_PX = [(1318, 1603), (1296, 1650), (1290, 1700), (1287, 1760), (1286, 1850), (1290, 1950),
                  (1296, 2050), (1300, 2105)]
# the door split (front door's trailing edge), top at the roof edge to the sill
DOOR_SPLIT_PX = [(2140, 1320), (2105, 1500), (2075, 1640), (2058, 1800), (2060, 2000), (2065, 2085)]
# rear door's trailing edge: from the quarter glass tip down, then forward into the wheel arch
DOOR_R_EDGE_PX = [(2800, 1540), (2835, 1600), (2825, 1650), (2790, 1720), (2740, 1790), (2690, 1850)]
# the belt: the doors' top edge = the glass's lower edge (front door, then rear door)
BELT_PX = [(1305, 1605), (1400, 1597), (1540, 1588), (1700, 1578), (1900, 1568), (2080, 1562),
           (2200, 1553), (2400, 1550), (2600, 1546), (2790, 1537)]
# glass openings (inner edge of the black frame)
GLASS_F_PX = [(1530, 1585), (1510, 1490), (1600, 1445), (1700, 1405), (1800, 1375), (1900, 1352),
              (2000, 1342), (2090, 1335), (2050, 1450), (2010, 1562)]
GLASS_R_PX = [(2185, 1330), (2300, 1327), (2400, 1325), (2500, 1330), (2560, 1340), (2640, 1365),
              (2725, 1530), (2600, 1545), (2400, 1550), (2200, 1553), (2165, 1555)]
GLASS_Q_PX = [(2690, 1360), (2800, 1395), (2900, 1440), (2990, 1485), (2790, 1535), (2735, 1532)]
# the doors' lower edge (top of the black rocker strip)
DOOR_BOTTOM_PX = [(1300, 2105), (1500, 2098), (1800, 2090), (2065, 2083)]
# the fender's black gill (the arrow behind the front wheel)
GILL_PX = [(1150, 1722), (1262, 1722), (1262, 1760), (1215, 1790), (1260, 1838), (1150, 1838)]
# tail lamp, a teardrop on the quarter's corner (WHITE c1_0506 / c1_0513 agree within 5 px)
TAIL_LAMP_PX = [(3225, 1635), (3330, 1618), (3490, 1610), (3495, 1690), (3430, 1688), (3330, 1668)]
# quarter/bumper diagonal shut line from the lamp's tip down into the rear wheel arch
QTR_BUMPER_PX = [(3240, 1650), (3200, 1710), (3160, 1780), (3130, 1840)]


# ----------------------------------------------------------- the front photograph (BLUE c1_0511.jpg)
# Long lens, nearly level. Solved from: the front tyres' outer walls (u 1025 / 2818: 1.855 m at the
# axle -> 966.6 px/m), the Autohome plate sign (467 px = the 440 mm plate -> 1061 px/m at the nose,
# so f 9890 and the camera 11.75 m ahead of the centre), the roof crest (v 1008, x -0.36, z 1.446)
# and the screen's base (v 1344, x 1.07, z 0.985): the camera is 0.615 m high, pitched UP 1.43
# degrees. Checks: the tyre contact line reads v 2280 (seen 2269), the BYD badge z 0.634.
FRONT_CAM = dict(loc=(11.75, 0.0, 0.615), pitch=math.radians(-1.43), f=9890.0)


def front_yz(u, v, x=2.35):
    """(y, z) of the front photo's pixel (u, v) for a point on the plane x. +y is the car's LEFT,
    the right of the picture."""
    cam = FRONT_CAM
    du = (u - 0.5 * W) / cam["f"]
    dv = -(v - 0.5 * H) / cam["f"]
    p = cam["pitch"]
    fx, fz = -math.cos(p), -math.sin(p)
    ux, uz = -math.sin(p), math.cos(p)
    d = (fx + dv * ux, du, fz + dv * uz)
    t = (x - cam["loc"][0]) / d[0]
    return (cam["loc"][1] + t * d[1], cam["loc"][2] + t * d[2])


# ------------------------------------------------------------ the rear photograph (BLUE c1_0515.jpg)
# Solved like the front one: the rear tyres' outer walls (u 1029 / 2832: 1.860 m -> 969 px/m at the
# axle), the plate sign (468 px = 440 mm -> 1063 px/m at x -2.38: the camera stands 12.5 m behind,
# f 10755), the roof crest (v 936) and the backlight's foot (v 1191, x -2.0, z 1.086): the camera is
# 0.624 m high, pitched UP 1.19 degrees. Checks: tyre bottoms v 2270 (seen 2272), plate z 0.43.
REAR_CAM = dict(loc=(-12.5, 0.0, 0.624), pitch=math.radians(-1.19), f=10755.0)
REAR_U0 = 1930.5                  # the car's centre column (the tyres' walls at 1029 / 2832)


def rear_yz(u, v, x=-2.36):
    """(y, z) of the rear photo's pixel (u, v) for a point on the plane x; +y is the car's LEFT, the
    LEFT of the picture (the camera looks forward along +X)."""
    cam = REAR_CAM
    du = (u - REAR_U0) / cam["f"]
    dv = -(v - 0.5 * H) / cam["f"]
    p = cam["pitch"]
    fx, fz = math.cos(p), -math.sin(p)
    ux, uz = math.sin(p), math.cos(p)
    d = (fx + dv * ux, -du, fz + dv * uz)
    t = (x - cam["loc"][0]) / d[0]
    return (cam["loc"][1] + t * d[1], cam["loc"][2] + t * d[2])
