"""Zeekr 7X reference cameras: the photo measurements and the solves behind
zx_ref_match.py.

Photographs: Autohome series 7777 (blender/reference/zeekr-7x, local only), the
2026 Ultra (spec 75350) in canyon-stone blue on a white studio floor, 3840 x 2880.

Known geometry (Autohome spec table for 75350, MIIT 2027 filing): 4825 x 1930 x 1656
mm, wheelbase 2925, track 1649 front / 1654 rear, tyres 265/40 R21 all round (the
21 in option). Hub height = tyre radius (0.3727 free) less ~8 mm of load.

Coordinates are photo pixels (u right, v down) and "axle coordinates": model metres
with the FRONT AXLE AT x = 0, +X forward, +Y to the car's left. zx_ref_match shifts
the result into model coordinates once the overhangs are known.
"""
import math

from carkit.qa import refmatch as R

WB = 2.925
RF = RR = 0.3647                 # loaded hub height (265/40 R21: 0.3727 free, 8 mm sag)
RL = 0.2845                      # visible rim lip radius (21 in bead seat 0.2667 + flange)
YL = 0.930                       # rim lip plane: track/2 (0.825) + ~105 mm
SIDE_SIZE = (3840, 2880)

# Rim lip edge points of the side photograph (side_left_studio.jpg), found by a radial
# bright-to-dark edge search and a robust ellipse fit (rms 0.27 / 0.24 px; ratios
# 0.996 / 0.9965, i.e. the camera is ~5 deg off-normal to each wheel)
RIM_F = [
    (1097.4, 2026.0), (1097.3, 2005.8), (1092.7, 1986.1), (1087.5, 1966.7),
    (1080.3, 1947.9), (1071.2, 1930.0), (1060.3, 1913.2), (1048.0, 1897.3),
    (1034.1, 1882.6), (1017.8, 1870.7), (1001.0, 1859.8), (983.1, 1850.7), (964.3, 1843.5),
    (944.9, 1838.3), (925.1, 1835.2), (905.0, 1834.1), (884.9, 1835.2), (865.1, 1838.3),
    (845.7, 1843.5), (826.7, 1850.2), (808.8, 1859.4), (792.2, 1870.7), (776.6, 1883.4),
    (762.0, 1897.3), (749.3, 1912.9), (737.9, 1929.5), (728.8, 1947.5), (721.5, 1966.4),
    (716.3, 1985.9), (712.7, 2005.8), (711.6, 2026.0), (712.7, 2046.2), (716.5, 2071.3),
    (721.8, 2090.9), (729.1, 2109.9), (738.8, 2127.8), (750.4, 2144.6), (763.3, 2160.5),
    (782.0, 2177.9), (798.6, 2189.9), (816.1, 2200.5), (834.8, 2208.9), (854.3, 2215.2),
    (874.4, 2219.5), (894.7, 2221.6), (915.3, 2221.6), (935.6, 2219.0), (955.6, 2214.7),
    (974.8, 2208.0), (993.5, 2199.7), (1015.1, 2186.2), (1031.3, 2173.8), (1045.7, 2159.5),
    (1058.8, 2144.0), (1069.9, 2127.1), (1079.6, 2109.3), (1086.8, 2090.4),
    (1092.6, 2071.0), (1095.8, 2051.1), (1097.3, 2031.0)
]
RIM_R = [
    (3079.7, 2015.0), (3078.6, 1994.9), (3075.5, 1974.9), (3070.3, 1955.5),
    (3063.0, 1936.6), (3054.3, 1918.4), (3043.3, 1901.4), (3030.9, 1885.4),
    (3008.9, 1864.5), (2992.8, 1852.1), (2975.2, 1842.0), (2956.6, 1833.7),
    (2937.4, 1826.9), (2917.5, 1822.7), (2897.2, 1820.6), (2876.8, 1820.6),
    (2851.5, 1823.6), (2831.6, 1827.8), (2807.6, 1836.7), (2789.4, 1846.0),
    (2772.3, 1857.1), (2756.4, 1869.9), (2741.9, 1884.4), (2729.9, 1900.9),
    (2715.9, 1922.1), (2707.1, 1940.5), (2700.8, 1959.8), (2695.7, 1984.7),
    (2693.1, 2004.8), (2693.6, 2025.1), (2695.7, 2045.3), (2699.9, 2065.1),
    (2706.2, 2084.4), (2714.9, 2102.7), (2725.0, 2120.2), (2736.9, 2136.6),
    (2750.7, 2151.3), (2765.7, 2164.8), (2782.0, 2176.6), (2799.5, 2186.7),
    (2817.9, 2194.9), (2837.1, 2201.1), (2856.9, 2205.3), (2876.9, 2207.4),
    (2897.1, 2207.4), (2917.1, 2205.3), (2936.9, 2201.1), (2955.9, 2194.4),
    (2974.3, 2186.3), (2991.7, 2176.2), (3008.0, 2164.4), (3022.9, 2150.9),
    (3036.4, 2136.0), (3047.8, 2119.4), (3058.3, 2102.3), (3066.4, 2083.9),
    (3072.7, 2064.7), (3076.3, 2045.0), (3079.4, 2025.1)
]
RIM_F_CENTRE = (904.41, 2027.80)
RIM_R_CENTRE = (2886.27, 2013.81)

CF = R.circle((0.0, YL, RF), RL)
CR = R.circle((-WB, YL, RR), RL)


def side_pairs():
    return [(p, CF) for p in RIM_F] + [(p, CR) for p in RIM_R]


# ------------------------------------------------------------- photo -> model
# The solved side camera (axle coordinates, f 12650 px fixed from the roof height)
# as plain maths, so panel data can be written in side-photo pixels and converted
# where it is used (no Blender needed): side_xz(u, v, y) is the model's (x, z) of
# the point seen at pixel (u, v) when it lies on the plane y (a door skin 0.88-0.92,
# the roof's centreline 0.0). x is returned in MODEL coordinates (front axle at
# +1.5425, i.e. zx_surface.FRONT_AXLE).
SIDE_CAM = dict(loc=(-1.5007, 19.6008, 1.1009), rot=(90.3701, 0.4034, 179.9898), f=12650.0)
FRONT_AXLE_MODEL = 1.5425


def _rot_xyz(rx, ry, rz):
    a, b, c = (math.radians(t) for t in (rx, ry, rz))
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    # R = Rz * Ry * Rx (Blender's XYZ euler)
    return [[cc * cb, cc * sb * sa - sc * ca, cc * sb * ca + sc * sa],
            [sc * cb, sc * sb * sa + cc * ca, sc * sb * ca - cc * sa],
            [-sb, cb * sa, cb * ca]]


def side_xz(u, v, y=0.0, size=SIDE_SIZE):
    cam = SIDE_CAM
    Rm = _rot_xyz(*cam["rot"])
    dx = (u - 0.5 * size[0]) / cam["f"]
    dy = -(v - 0.5 * size[1]) / cam["f"]
    d = (dx, dy, -1.0)
    w = [sum(Rm[i][j] * d[j] for j in range(3)) for i in range(3)]
    t = (y - cam["loc"][1]) / w[1]
    return (cam["loc"][0] + t * w[0] + FRONT_AXLE_MODEL, cam["loc"][2] + t * w[2])


# The solved straight-on front camera (zx_ref_match "front": model coordinates), as
# maths: front_yz(u, v, x) is the model's (y, z) of the point seen at pixel (u, v) of
# front_studio.jpg when it lies on the plane x (the nose's face stands at x 2.38-2.40;
# a lamp or intake further back or round a corner is placed by the build's radial
# cast, so only (y, z) matters here).
FRONT_CAM = dict(loc=(20.83, 0.0, 0.464), rot=(91.37, 0.0, 90.0), f=17272.0)
FRONT_SIZE = (3840, 2880)


def front_yz(u, v, x=2.38):
    cam = FRONT_CAM
    Rm = _rot_xyz(*cam["rot"])
    d = ((u - 0.5 * FRONT_SIZE[0]) / cam["f"], -(v - 0.5 * FRONT_SIZE[1]) / cam["f"], -1.0)
    w = [sum(Rm[i][j] * d[j] for j in range(3)) for i in range(3)]
    t = (x - cam["loc"][0]) / w[0]
    return (cam["loc"][1] + t * w[1], cam["loc"][2] + t * w[2])


# The straight-on rear camera: from behind (looking along +x); rear_yz(u, v, x) is the
# model's (y, z) of the point seen at pixel (u, v) of rear_studio.jpg on the plane x (the
# tail's face stands at x -2.33 .. -2.42).
REAR_CAM = dict(loc=(-20.83, 0.0, 0.755), rot=(90.53, 0.0, 270.0), f=17293.0)


def rear_yz(u, v, x=-2.38):
    cam = REAR_CAM
    Rm = _rot_xyz(*cam["rot"])
    d = ((u - 0.5 * FRONT_SIZE[0]) / cam["f"], -(v - 0.5 * FRONT_SIZE[1]) / cam["f"], -1.0)
    w = [sum(Rm[i][j] * d[j] for j in range(3)) for i in range(3)]
    t = (x - cam["loc"][0]) / w[0]
    return (cam["loc"][1] + t * w[1], cam["loc"][2] + t * w[2])
