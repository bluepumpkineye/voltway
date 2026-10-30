"""Voyah Passion S (岚图追光S, Autohome series 8534): photo readings and conversion to model metres.

The studio turntable set (blender/reference/voyah-passion-s/exterior, 3840 x 2880, local only):

    c1_0004  Rosy Mist Pink car, LEFT side, nose to the left     (camera "side")
    c1_0002  front, c1_0006 rear, c1_0001/0003 front 3/4, c1_0005/0007 rear 3/4

Solved camera constants:
    rim lips (photo_tools.fit_rim): front (987.01, 2039.95), rear (2900.98, 2032.33)
    wheelbase 3.000 m (Autohome / MIIT) -> 637.995 px/m at the hub plane (y 0.94), roll -0.2281 deg
    studio turntable distance D 24.5 m (f = k * (D - y_hub) = 15031.16 px)
    overhangs from the silhouette tips: 1.000 m front, 1.050 m rear (length 5.050 m)

Model coordinates: +X forward, +Y to the car's left, Z up, length centred on x = 0
(front axle +1.525, rear axle -1.475).

    side_xz(u, v, y)   (x, z) of the side photo's pixel on the plane y
    side_uv(x, z, y)   its inverse
"""
import math

W, H = 3840, 2880
D = 24.5                          # camera distance from the centre plane (y = 0)
Y_HUB = 0.94                      # outer wheel-face plane where the hub scale is read
WHEELBASE = 3.000
FRONT_AXLE = 1.525
REAR_AXLE = FRONT_AXLE - WHEELBASE  # -1.475
HUB_Z = 0.375                     # loaded wheel-centre height (255/50 R21)


class SideCam:
    """A level side camera (nose to the LEFT of the picture) solved from the two hub centres."""

    def __init__(self, front, rear, d=D, y_hub=Y_HUB, front_axle=None):
        (uf, vf), (ur, vr) = front, rear
        fa = FRONT_AXLE if front_axle is None else front_axle
        self.d, self.y_hub = d, y_hub
        self.k = math.hypot(ur - uf, vr - vf) / WHEELBASE
        self.roll = math.atan2(vr - vf, ur - uf)
        self.f = self.k * (d - y_hub)
        c, s = math.cos(self.roll), math.sin(self.roll)
        self._c, self._s = c, s
        du, dv = uf - 0.5 * W, vf - 0.5 * H
        duf, dvf = c * du + s * dv, -s * du + c * dv
        depth = d - y_hub
        self.cx = fa + duf * depth / self.f
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


SIDE = SideCam((987.01, 2039.95), (2900.98, 2032.33))
CAMS = {"side": SIDE}


def side_xz(u, v, y=0.0, cam="side"):
    return CAMS[cam].side_xz(u, v, y)


def side_uv(x, z, y=0.0, cam="side"):
    return CAMS[cam].side_uv(x, z, y)


def zx(px, y=0.0, cam="side"):
    return sorted((z, x) for (x, z) in (side_xz(u, v, y, cam) for (u, v) in px))


def xz(px, y=0.0, cam="side"):
    return sorted(side_xz(u, v, y, cam) for (u, v) in px)


# ------------------------------------------------- front and rear studio photos (c1_0002 / c1_0006)
# Turntable camera at 24.5 m from the car's centre, height 1.3095 m; solved from tyre outer walls
# (1720 / 1723 mm track + 255 mm tyres = 1.975 / 1.978 m outer tyre span) and ground contact / roof LiDAR.
FRONT_CAM = dict(loc=(24.5, 0.0, 1.3095), f=19973.7, pp=(-0.5, -298.0))
REAR_CAM = dict(loc=(-24.5, 0.0, 1.3095), f=20045.0, pp=(-1.0, -310.1))


def front_yz(u, v, x=2.40):
    """(y, z) of the front photo's pixel (u, v) on the plane x (+y is the car's LEFT, right of photo)."""
    cam = FRONT_CAM
    pu, pv = cam["pp"]
    depth = D - x
    y = (u - 0.5 * W - pu) * depth / cam["f"]
    z = cam["loc"][2] - (v - 0.5 * H - pv) * depth / cam["f"]
    return (y, z)


def rear_yz(u, v, x=-2.40):
    """(y, z) of the rear photo's pixel (u, v) on the plane x (+y is the car's LEFT, left of photo)."""
    cam = REAR_CAM
    pu, pv = cam["pp"]
    depth = D + x
    y = -(u - 0.5 * W - pu) * depth / cam["f"]
    z = cam["loc"][2] - (v - 0.5 * H - pv) * depth / cam["f"]
    return (y, z)


# ------------------------------------------------------------ side photograph lines (c1_0004, pixels)
Y_SKIN = 0.94
DOOR_F_EDGE_PX = [
    (1362, 1495), (1338, 1535), (1322, 1580), (1314, 1675),
    (1318, 1775), (1328, 1875), (1340, 2005), (1345, 2070),
]
DOOR_SPLIT_PX = [
    (2065, 1482), (2038, 1580), (2024, 1680), (2018, 1780),
    (2020, 1880), (2022, 1945), (2024, 2068),
]
DOOR_R_EDGE_PX = [
    (2700, 1448), (2742, 1485), (2755, 1545), (2746, 1625), (2732, 1698),
]
ROCKER_TOP_PX = [
    (1340, 2005), (1515, 1984), (1765, 1962), (2018, 1945),
    (2165, 1942), (2365, 1960), (2545, 1988),
]
BELT_PX = [
    (1375, 1495), (1565, 1491), (1815, 1486), (2060, 1480),
    (2315, 1474), (2565, 1460), (2690, 1444), (2785, 1422), (2875, 1394),
]
DLO_TOP_PX = [
    (1375, 1495), (1515, 1405), (1665, 1328), (1815, 1272),
    (1965, 1248), (2068, 1242), (2215, 1245), (2365, 1256),
    (2515, 1274), (2665, 1306), (2785, 1346), (2875, 1394),
]
