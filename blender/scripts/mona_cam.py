"""XPeng Mona L05 (小鹏MONA L05, Autohome series 8662): photo readings and conversion to model metres.

The studio turntable set (blender/reference/xpeng-mona-l05/exterior, 3840 x 2880, local only):

    c1_0003  purple car, LEFT side, nose to the left       (camera "side")
    c1_0007  purple car, RIGHT side, nose to the right     (mirror check)
    c1_0001  purple front 3/4, c1_0005 purple rear head-on, c1_0004 / c1_0006 rear 3/4
    c1_0009  white front head-on, c1_0011 white left side, c1_0013 white rear, c1_0010 / c1_0012 3/4
    c1_0017  black front head-on, c1_0019 black side, c1_0021 black rear

Solved camera constants (2026-11-17):
    rim lips (photo_tools.fit_rim on c1_0003): front (918.54, 2036.88), rear (2871.19, 2037.79); 20 in rims,
        lip semi-axes 184-186 px
    wheelbase 2.940 m (MIIT / Autohome) -> 664.2 px/m at the hub plane (y 0.89), roll 0.027 deg
    tyre bottoms at v 2272.5 -> loaded wheel radius 0.354 m (245/45 R20, unloaded 0.364 m)
    studio turntable distance D 24.5 m: the silhouette tips give 4.883 m against the filed 4.870 m
    overhangs from the silhouette tips: 0.930 m front, 1.000 m rear (length 4.870 m)
    front/rear cameras: same rig height as the side camera (1.2535 m); the rear tyres' outer walls span
        1706 px = 1.885 m (track 1.640 + tyre 0.245) at 23.065 m -> f = 20874 px; the ground sits at v 2275
        -> principal point shifted -299 px (Voyah's: -298 / -310, the same studio)

Model coordinates: +X forward, +Y to the car's left, Z up, length centred on x = 0
(front axle +1.505, rear axle -1.435).

    side_xz(u, v, y)   (x, z) of the side photo's pixel on the plane y
    side_uv(x, z, y)   its inverse
"""
import math

W, H = 3840, 2880
D = 24.5                          # camera distance from the centre plane (y = 0)
Y_HUB = 0.89                      # outer wheel-face plane where the hub scale is read
WHEELBASE = 2.940
FRONT_OVERHANG = 0.930
REAR_OVERHANG = 1.000
LENGTH = WHEELBASE + FRONT_OVERHANG + REAR_OVERHANG      # 4.870
FRONT_AXLE = LENGTH / 2.0 - FRONT_OVERHANG                # 1.505
REAR_AXLE = FRONT_AXLE - WHEELBASE                        # -1.435
HUB_Z = 0.354                     # loaded wheel-centre height (245/45 R20)


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


SIDE = SideCam((918.54, 2036.88), (2871.19, 2037.79))
CAMS = {"side": SIDE}


def side_xz(u, v, y=0.0, cam="side"):
    return CAMS[cam].side_xz(u, v, y)


def side_uv(x, z, y=0.0, cam="side"):
    return CAMS[cam].side_uv(x, z, y)


def zx(px, y=0.0, cam="side"):
    return sorted((z, x) for (x, z) in (side_xz(u, v, y, cam) for (u, v) in px))


def xz(px, y=0.0, cam="side"):
    return sorted(side_xz(u, v, y, cam) for (u, v) in px)


# ------------------------------------------------- front and rear studio photos
# Turntable camera 24.5 m from the car's centre at the side camera's height; the rig is the same for
# every colour set. f from the rear tyres' outer walls; the front lens is taken 0.4 % shorter as on the
# Voyah set (both refined against the model by overlay).
CAM_Z = SIDE.cz
# The front shots (c1_0009 white, c1_0017 black) are a longer zoom from a low camera: tyre outer walls span
# 2243 px = 1.885 m at 22.995 m -> f 27400; roof edge v 567 and tyre bottoms v ~2430 -> camera 0.70 m high,
# principal point +156 px.
FRONT_CAM = dict(loc=(24.5, 0.0, 0.70), f=27400.0, pp=(0.0, 155.9))
REAR_CAM = dict(loc=(-24.5, 0.0, CAM_Z), f=20874.0, pp=(0.0, -299.0))


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
