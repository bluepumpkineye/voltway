"""Avatr 06T (阿维塔 06T, Autohome series 8538): photo readings and their conversion to model metres.

The studio turntable set (blender/reference/avatr-06t/exterior, 3840 x 2880, local only):

    c1_0004  light-blue car, LEFT side, nose to the left       (camera "side")
    c1_0002  front, c1_0006 rear, c1_0001/0003 front 3/4, c1_0005/0007 rear 3/4

Certain (nothing is fitted to the model):
    rim lips (photo_tools.fit_rim): front (849.99, 2030.25), rear (2847.08, 2024.87), lip radius 184 px
    wheelbase 2.940 m (Autohome / MIIT) -> 679.3 px/m at the hub plane (y 0.85), roll -0.15 degrees
    the picture is a long lens: D 16 m (f = k * (D - y_hub))
    overhangs from the silhouette tips (u 298 / 3522): 0.90 m front, 1.10 m rear (length 4.940)

Model coordinates: +X forward, +Y to the car's left, Z up, length centred on x = 0
(front axle +1.570, rear axle -1.370).

    side_xz(u, v, y)   (x, z) of the side photo's pixel on the plane y
    side_uv(x, z, y)   its inverse
"""
import math

W, H = 3840, 2880
D = 16.0                          # camera distance from the centre plane (y = 0)
Y_HUB = 0.85                      # the plane the hub scale is read on
WHEELBASE = 2.940
FRONT_AXLE = 1.570
HUB_Z = 0.365                     # loaded wheel-centre height (255/45 R20)


class SideCam:
    """A level side camera (nose to the LEFT of the picture) from the two hub centres."""

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


SIDE = SideCam((849.99, 2030.25), (2847.08, 2024.87))
CAMS = {"side": SIDE}


def side_xz(u, v, y=0.0, cam="side"):
    return CAMS[cam].side_xz(u, v, y)


def side_uv(x, z, y=0.0, cam="side"):
    return CAMS[cam].side_uv(x, z, y)


def zx(px, y=0.0, cam="side"):
    return sorted((z, x) for (x, z) in (side_xz(u, v, y, cam) for (u, v) in px))


def xz(px, y=0.0, cam="side"):
    return sorted(side_xz(u, v, y, cam) for (u, v) in px)


# ------------------------------------------------- the front and rear photographs (c1_0002 / c1_0006)
# The turntable set is one camera 16 m from the car's centre; each end view has its own zoom and
# height. Front: tyre outer walls u 1057 / 2790 (1.931 m at the axle plane x 1.57 -> 897 px/m ->
# f 12950), the 480 mm sign (453 px -> 0.474 m: the 16 m distance fits), tyre contact v 2284 and the
# LiDAR housing top (v 1017, x 0.28, z 1.447 from the side photo): camera 1.02 m up, picture shifted
# 70 px up. Rear: tyre walls u 1047 / 2790 (1.935 m at x -1.37 -> 901 px/m -> f 13181), contacts 2284.
FRONT_CAM = dict(loc=(16.0, 0.0, 1.02), f=12950.0, pp=(3.5, -70.5))
REAR_CAM = dict(loc=(-16.0, 0.0, 1.02), f=13181.0, pp=(-2.0, -75.0))


# ------------------------------------------------------------ the side photograph's lines (c1_0004, pixels)
# Read off gridded crops of the left side. Convert with side_xz / xz / zx at the plane the line lies on:
# y 0.93 on the door skin, ~0.8 at the glass base, ~0.7 at the roof edge.
Y_SKIN = 0.93
# front door's leading edge, belt corner down to the sill
DOOR_F_EDGE_PX = [(1259, 1595), (1235, 1625), (1214, 1657), (1207, 1733), (1205, 1802), (1210, 1871),
                  (1217, 1974), (1223, 2078)]
# the door split (front door's trailing edge): belt to sill
DOOR_SPLIT_PX = [(2045, 1563), (2027, 1636), (2007, 1733), (2003, 1871), (2009, 1995)]
# rear door's trailing edge: the quarter glass's lower tip down, bulging back, into the arch
DOOR_R_EDGE_PX = [(2681, 1509), (2736, 1553), (2750, 1609), (2743, 1678), (2729, 1747)]
# top of the black rocker cladding: the doors' (and fender's, quarter's) lower edge
ROCKER_TOP_PX = [(1224, 2078), (1396, 2029), (1652, 2009), (1996, 1991), (2157, 1987), (2364, 2009),
                 (2500, 2043), (2560, 2053)]
# glass lower edge (belt): front door, rear door, then the quarter window's lower edge rising to its tip
BELT_PX = [(1262, 1592), (1514, 1581), (1652, 1574), (1859, 1567), (2045, 1562), (2226, 1557),
           (2433, 1543), (2640, 1526), (2709, 1505), (2812, 1488), (2874, 1470), (2945, 1447)]
# the A-pillar's outer line, belt corner up to the roof edge
A_LINE_PX = [(1262, 1588), (1376, 1509), (1486, 1450), (1583, 1409), (1686, 1367), (1790, 1327)]
# roof edge: where the painted roof strip meets the black glass frame, A-pillar top to the quarter tip
ROOF_EDGE_PX = [(1790, 1327), (1859, 1318), (1962, 1312), (2058, 1309), (2136, 1320), (2300, 1317),
                (2433, 1316), (2540, 1322), (2640, 1330), (2778, 1360), (2867, 1405), (2945, 1440)]
# B-pillar glass: front door glass's rear edge and rear door glass's front edge (top, bottom)
B_FRONT_PX = [(2053, 1336), (1964, 1560)]
B_REAR_PX = [(2136, 1336), (2102, 1560)]
# C-pillar black band between the rear door glass and the quarter window (top, bottom)
C_BAND_PX = [(2536, 1353), (2622, 1512)]


def front_yz(u, v, x=2.40):
    """(y, z) of the front photo's pixel (u, v) for a point on the plane x. +y is the car's LEFT,
    the right of the picture."""
    cam = FRONT_CAM
    pu, pv = cam["pp"]
    depth = 16.0 - x
    y = (u - 0.5 * W - pu) * depth / cam["f"]
    z = cam["loc"][2] - (v - 0.5 * H - pv) * depth / cam["f"]
    return (y, z)


def rear_yz(u, v, x=-2.40):
    """(y, z) of the rear photo's pixel for a point on the plane x; +y is the car's LEFT, the LEFT of
    the picture (the camera looks forward along +X)."""
    cam = REAR_CAM
    pu, pv = cam["pp"]
    depth = x + 16.0
    y = -(u - 0.5 * W - pu) * depth / cam["f"]
    z = cam["loc"][2] - (v - 0.5 * H - pv) * depth / cam["f"]
    return (y, z)


# ------------------------------------------------------------ the front photograph's lines (c1_0002, pixels)
# The car's RIGHT half (the left of the picture) is read and mirrored.
# bonnet's leading edge across the nose, outer corner to the centre
HOOD_EDGE_PX = [(1467, 1583), (1573, 1603), (1700, 1612), (1933, 1617)]
# upper "eyebrow" lamp: a tapered wedge from the outer end to the inner tip (outline, clockwise)
EYEBROW_PX = [(1143, 1566), (1200, 1561), (1280, 1580), (1360, 1603), (1417, 1632), (1405, 1634),
              (1350, 1623), (1290, 1608), (1240, 1597), (1200, 1591), (1160, 1598), (1148, 1582)]
# the main lamp blade (DRL): rounded outer end, pointed inner tip
DRL_PX = [(1172, 1656), (1182, 1648), (1260, 1661), (1350, 1678), (1420, 1692), (1478, 1707),
          (1483, 1714), (1440, 1714), (1350, 1703), (1250, 1688), (1190, 1675), (1172, 1666)]
# the dark lamp pocket: a tall kite hugging the corner, widest at the inner apex (1258, 1838)
KITE_PX = [(1128, 1598), (1152, 1606), (1153, 1660), (1160, 1692), (1190, 1720), (1220, 1765),
           (1248, 1810), (1258, 1838), (1248, 1880), (1222, 1925), (1190, 1962), (1165, 1985),
           (1140, 1962), (1124, 1920), (1118, 1850), (1118, 1750), (1122, 1650)]
# painted bumper's lower edge: outer corner, along the winglet, up the grille opening's diagonal, across
PAINT_EDGE_PX = [(1068, 2052), (1100, 2058), (1200, 2064), (1300, 2068), (1328, 2068), (1360, 2055),
                 (1400, 2030), (1440, 2000), (1480, 1965), (1520, 1935), (1560, 1912), (1600, 1905),
                 (1700, 1904), (1933, 1904)]
# chin pin-stripe (chrome), outer end curling down, to the centre side
CHIN_PX = [(1070, 2060), (1082, 2092), (1110, 2102), (1200, 2101), (1300, 2103), (1400, 2105), (1462, 2098)]
PLATE_PX = (1697, 1760, 2150, 1895)         # the 480 x 140 mm sign: left, top, right, bottom
EMBLEM_PX = (1923, 1655)                    # the prism badge's centre (33 x 37 px)
CAMERA_PX = (1924, 1741)
TOWCAP_PX = (1536, 1800, 1600, 1857)
SENSORS_PX = [(1267, 1929), (1600, 1888)]

# the same two lamps as (upper edge, lower edge) polylines, outer end to inner tip
EYEBROW_UP_PX = [(1143, 1566), (1200, 1561), (1280, 1580), (1360, 1603), (1417, 1632)]
EYEBROW_LO_PX = [(1148, 1582), (1160, 1598), (1200, 1591), (1240, 1597), (1290, 1608), (1350, 1623),
                 (1405, 1634), (1417, 1632)]
DRL_UP_PX = [(1182, 1648), (1260, 1661), (1350, 1678), (1420, 1692), (1478, 1707)]
DRL_LO_PX = [(1172, 1666), (1190, 1675), (1250, 1688), (1350, 1703), (1440, 1714), (1483, 1714)]

# the black "AVATR" blade on the fender and the door's front corner, front tip first (left of the picture)
BLADE_PX = [(1096, 1787), (1146, 1779), (1217, 1773), (1329, 1766), (1317, 1787), (1167, 1800), (1117, 1800)]
