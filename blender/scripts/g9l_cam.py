"""XPeng G9L: photo readings and their conversion to model metres.

The flank's lines are written in PIXELS of the white car's side photograph (c1_0028.jpg,
3840 x 2880; camera "side_white" in g9l_ref_match: level, 1.057 m high, 681.5 px/m at the
hub plane, a grey studio) and turned into model coordinates at the plane they lie on (the
door skin, ~0.97 m off the centre plane). The reading stays checkable against the
photograph: `g9l_ref_match.overlay("side_white", tag)` draws the built panel lines over it.

    side_xz(u, v, y)    (x, z) of the pixel on the plane y
    zx(px, y)           [(z, x)] sorted by height (near-vertical lines)
    xz(px, y)           [(x, z)] sorted by x (lines along the car)
"""
import math

# the solved camera, as plain maths (no Blender needed): model coordinates, level but for a
# 0.38 degree roll, looking along -Y from y = D at the car's left side
D = 11.0
F = 681.5 * (D - 0.93)
CX, CZ = 0.0123, 1.057
ROLL = math.radians(0.38)
W, H = 3840, 2880


def side_xz(u, v, y=0.97):
    """(x, z) of the side photo's pixel (u, v) for a point on the plane y."""
    du = (u - 0.5 * W)
    dv = -(v - 0.5 * H)
    c, s = math.cos(ROLL), math.sin(ROLL)
    du, dv = c * du + s * dv, -s * du + c * dv
    depth = D - y
    return (CX - du * depth / F, CZ + dv * depth / F)


def zx(px, y=0.97):
    return sorted((z, x) for (x, z) in (side_xz(u, v, y) for (u, v) in px))


def xz(px, y=0.97):
    return sorted(side_xz(u, v, y) for (u, v) in px)


# ------------------------------------------------------------- the flank's lines
# front door's leading edge (cowl corner to the sill), on the skin (y 0.97)
DOOR_F_EDGE_PX = [(1176, 1353), (1162, 1400), (1153, 1450), (1151, 1520), (1152, 1600),
                  (1155, 1700), (1162, 1800), (1170, 1900), (1180, 1980)]
# the door split (front door's trailing edge)
DOOR_SPLIT_PX = [(1950, 1318), (1932, 1370), (1922, 1430), (1917, 1500), (1915, 1600),
                 (1914, 1700), (1914, 1800), (1914, 1900), (1914, 1972)]
# rear door's trailing edge, into the wheel arch
DOOR_R_EDGE_PX = [(2732, 1279), (2750, 1305), (2763, 1337), (2766, 1400), (2763, 1450),
                  (2760, 1505), (2755, 1560), (2750, 1600)]
# the belt: the doors' top edge = the glass's lower edge
BELT_PX = [(1176, 1350), (1263, 1347), (1526, 1337), (1737, 1329), (1950, 1318), (2216, 1308),
           (2479, 1296), (2742, 1279), (3000, 1250), (3174, 1229)]
# the greenhouse's dark region, upper boundary, A-pillar's foot to the quarter glass's tip
DLO_TOP_PX = [(1126, 1345), (1253, 1268), (1368, 1195), (1500, 1110), (1605, 1053), (1650, 1014),
              (1800, 1006), (1900, 1003), (2163, 997), (2426, 995), (2626, 1021), (2700, 1026),
              (2858, 1053), (3016, 1084), (3121, 1126), (3184, 1190), (3195, 1216)]
# hood / fender shut line from the lamp bar's outer end to the cowl
HOOD_SIDE_PX = [(531, 1458), (750, 1442), (950, 1429), (1003, 1421), (1066, 1389), (1118, 1353)]
# the fender's diagonal seam from the lamp bar's end to the arch's crown
FENDER_SEAM_PX = [(493, 1500), (540, 1540), (590, 1590), (623, 1640)]

# the greenhouse's vertical divisions (c1_0028, read on a 4.6x crop): the front door glass's rear
# edge, the B-pillar's black band (two lines) and the rear door glass's front edge, the rear door
# glass's rear edge, and the raked line that closes the rear door's vent glass (the C-pillar's edge)
GLASS_F_REAR_PX = [(1945, 1022), (1892, 1258), (1878, 1318)]
BPILLAR_PX = [(1996, 1015), (1958, 1255), (1950, 1318)]
GLASS_R_FRONT_PX = [(2038, 1025), (2020, 1262), (2015, 1315)]
GLASS_R_REAR_PX = [(2518, 1030), (2514, 1300)]
VENT_REAR_PX = [(2629, 1021), (2665, 1150), (2705, 1279)]


# ----------------------------------------------------------- the front photograph
# c1_0026.jpg, camera "front_white" (g9l_ref_match): 7.505 m ahead, 1.062 m high, 1.47 degrees nose-down
FRONT_CAM = dict(loc=(7.505, 0.0, 1.062), pitch=math.radians(1.53), f=6694.0)


def front_yz(u, v, x=2.50):
    """(y, z) of the front photo's pixel (u, v) for a point on the plane x (the nose's face stands
    at x 2.45-2.575; a lamp or intake is placed by the build's own cap lookup, so only y and z
    matter here). +y is the car's LEFT, the right of the picture."""
    cam = FRONT_CAM
    du = (u - 0.5 * W) / cam["f"]
    dv = -(v - 0.5 * H) / cam["f"]
    # camera looks along -X pitched down by p: forward d = (-cos p, 0, -sin p), up = (-sin p, 0, cos p)
    p = cam["pitch"]
    fx, fz = -math.cos(p), -math.sin(p)
    ux, uz = -math.sin(p), math.cos(p)
    d = (fx + dv * ux, du, fz + dv * uz)         # y: right = +y
    t = (x - cam["loc"][0]) / d[0]
    return (cam["loc"][1] + t * d[1], cam["loc"][2] + t * d[2])


# the front's lines, white car (left half = the car's RIGHT side; the picture's left)
# the painted fascia's lower edge (a shallow smile) from the outer slit to the plate
FASCIA_LOW_PX = [(832, 1730), (900, 1745), (1000, 1800), (1100, 1850), (1200, 1910), (1300, 1950),
                 (1400, 1960), (1500, 1962), (1603, 1963)]
# the lamp bar's top (the black bezel) and bottom edges from the outer end to the centre
BAR_TOP_PX = [(845, 1265), (900, 1290), (1000, 1305), (1100, 1315), (1250, 1328), (1500, 1335),
              (1920, 1340)]
BAR_BOT_PX = [(840, 1335), (900, 1362), (1000, 1385), (1250, 1405), (1500, 1412), (1920, 1418)]
# the headlamp module's lens (quad) and the outer slit (x range, top, bottom)
LAMP_LENS_PX = [(850, 1750), (985, 1840), (985, 2045), (850, 2050)]
SLIT_PX = dict(u=(790, 830), v=(1620, 2090))
# the intake panel (central black) and the chin
INTAKE_PX = dict(u=(1320, 2520), v=(1978, 2195))
CHIN_BOT_PX = [(830, 2085), (900, 2230), (1100, 2250), (1500, 2258), (1920, 2260)]
CHARGE_FLAP_PX = dict(u=(1320, 1415), v=(1805, 1905))


# ------------------------------------------------------------ the rear photograph
# c1_0030.jpg, camera "rear_white": 8.40 m behind, 1.428 m high, 4.24 degrees nose-down, f 7920
REAR_CAM = dict(loc=(-8.402, 0.0, 1.428), pitch=math.radians(4.24), f=7920.0)


def rear_yz(u, v, x=-2.54):
    """(y, z) of the rear photo's pixel (u, v) for a point on the plane x; +y is the car's LEFT, the
    LEFT of the picture (the camera looks forward along +X)."""
    cam = REAR_CAM
    du = (u - 0.5 * W) / cam["f"]
    dv = -(v - 0.5 * H) / cam["f"]
    p = cam["pitch"]
    fx, fz = math.cos(p), -math.sin(p)
    ux, uz = math.sin(p), math.cos(p)
    d = (fx + dv * ux, -du, fz + dv * uz)
    t = (x - cam["loc"][0]) / d[0]
    return (cam["loc"][1] + t * d[1], cam["loc"][2] + t * d[2])


# the rear's lines, white car (left half of the picture = the car's LEFT side; y >= 0)
GATE_LOW_PX = [(803, 1605), (880, 1640), (1000, 1700), (1100, 1730), (1250, 1748), (1500, 1760),
               (1922, 1768)]
LAMP_CAP_BOT_PX = [(880, 1245), (1000, 1236), (1500, 1232), (1922, 1230)]
REAR_BUMPER_TOP_PX = [(835, 1990), (860, 1935), (900, 1910), (990, 1900), (1400, 1897), (1922, 1897)]
REFLECTOR_PX = [(935, 1985), (1000, 1960), (1130, 1948), (1250, 1950), (1370, 1952), (1385, 1962),
                (1340, 1985), (1130, 1992), (960, 1995)]
REAR_VENT_PX = [(915, 2000), (962, 2005), (962, 2100), (925, 2110), (880, 2090), (880, 2010)]
LETTERS_U = (1576, 1753, 1931, 2108, 2285)
LETTERS_V = 1316
PLATE_PX = dict(u=(1613, 2256), v=(1513, 1699))
