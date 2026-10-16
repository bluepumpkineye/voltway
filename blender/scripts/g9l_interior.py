"""XPeng G9L cabin: the Bordeaux Red (波尔多红) Nappa interior, built with carkit.interior from
hardpoints read off Autohome's cabin photographs (series 8659, spec 77790, the purple car).

References (blender/reference/xpeng-g9l/, 1600 px, c3 = category 3 cabin, c10 = category 10 dash):

    hmi/c10_0001-5     the dash straight on from the rear (A-pillars, wheel, the cluster strip, the
                       floating screen, the star-lit band under it, the floating console)
    hmi/c10_0006,8     the binnacle and the wheel seen from the door and from the axis
    hmi/c10_0009-13    the wheel's pods and dials, the column stalks
    hmi/c10_0014-17    the cluster strip
    interior/c3_0001   the driver's seat from the open door; c3_0003 the front door card;
                       c3_0015 the console; c3_0020 the rear bench; c3_0030-32 the rear console

What the photographs show:

    colours      bordeaux-red Nappa on the dash, doors, console and seats; a dark grey top pad and
                 grey wheel rim; black carpet and black lower door cards; a black suede headliner
    dash         a wide flat dash: a grey top pad over a slim vent slot lit purple, a red upper face
                 with a very slim cluster strip behind the wheel, a floating screen, and a black
                 glass band with a field of small lights ("star ceiling") across the dash below it
                 with a chrome line above it; a red face down to the knees
    wheel        a rounded-square wheel with a grey rim, a red hub with the maker's X, two chrome-framed
                 button pods and two dials at the lower sides
    console      a floating bridge: an armrest box with a lid over a cup-holder bay, standing on a
                 pedestal; a small screen on its rear face
    seats        tall bordeaux seats, deep bolsters, separate headrests; a rear bench of three with
                 contoured outer seats and three headrests

Hardpoints are in the build's axes: +X forward, +Y left (China is LHD), +Z up, the car's centre at
x = 0; first-pass readings checked by overlay (g9l_cabin.compare).
"""
import math

import bpy
from mathutils import Vector

import g9l_surface as S
import g9l_panels as PN
import cabin_parts as CP
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "G9L_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.380
DRIVER_Y = 0.375
PASS_Y = -0.375

# the floating centre display (15.6 in): the plane of its front face, tilted back 8 degrees. The photos show a
# 16:9 panel; the showroom's HMI is a 1280 x 800 page that the viewer pins to this quad, so it is built 16:10
# (a few per cent taller than the car's) rather than stretching or cropping the page.
SCREEN_W, SCREEN_H = 0.3500, 0.2188
SCREEN_C = (1.070, -0.020, 1.075)
SCREEN_TILT = math.radians(8.0)
SCREEN_BORDER = 0.0090

WHEEL_Y = DRIVER_Y
WHEEL_C = (0.870, WHEEL_Y, 1.040)
WHEEL_TILT = math.radians(22.0)

# the dash: the pad's height and the faces' x
Z_TOP = 1.150
FACE_X = 1.120
CLUSTER_C = (FACE_X - 0.003, WHEEL_Y, 1.085)
CLUSTER_W, CLUSTER_H = 0.330, 0.062

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.200, 0.690
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.020, 0.710, 0.385

DASH_HALF = 0.790                  # the dash's ends, at the door cards
MIRROR_C = (0.700, 0.000, 1.640)   # the frameless rear-view mirror, hung from the header

# linear RGB: the swatch #7E2530 is the red; the lit photographs read pinker than it
RED = (0.205, 0.040, 0.052)        # bordeaux Nappa
RED_DASH = (0.185, 0.034, 0.046)
GREY_RIM = (0.060, 0.062, 0.066)   # the wheel's rim and the dash's top pad
BLACK_SUEDE = (0.018, 0.018, 0.020)
CARPET = (0.020, 0.020, 0.022)
LOWER_CARD = (0.032, 0.032, 0.036)  # the black plastic of the lower door cards
THREAD = (0.30, 0.10, 0.12)


def z_glass(x, y):
    """Height of the windscreen (the body's upper surface) at (x, |y|)."""
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.74)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    lib = IM.build_library(accent=RED, maps=maps)
    lib["leather_seat"] = IM.leather("INT_Leather_Seat", RED, maps, roughness=0.40, coat=0.10)
    lib["leather_accent"] = lib["leather_seat"]
    lib["leather_dash"] = IM.leather("INT_Leather_Dash", RED_DASH, maps, roughness=0.46, coat=0.08,
                                     strength=0.8)
    lib["leather_door"] = lib["leather_dash"]
    lib["wheel_leather"] = lib["leather_seat"]
    lib["pad_grey"] = IM.leather("INT_Pad_Grey", GREY_RIM, maps, roughness=0.55, coat=0.04, strength=0.8)
    lib["headliner"] = IM.alcantara("INT_Headliner", BLACK_SUEDE, maps, sheen=0.5)
    m, nt, b = MB.mat("INT_Thread_Seat")
    MB.set_inputs(b, base=THREAD, metallic=0.0, roughness=0.55, sheen=0.3)
    lib["thread"] = m
    m, nt, b = MB.mat("INT_Carpet_Black")
    MB.set_inputs(b, base=CARPET, metallic=0.0, roughness=0.96, specular=0.2, sheen=0.4)
    IM._textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m
    m, nt, b = MB.mat("INT_Lower_Card")
    MB.set_inputs(b, base=LOWER_CARD, metallic=0.0, roughness=0.62, specular=0.35)
    lib["lower_card"] = m
    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.004, 0.004, 0.006), metallic=0.0, roughness=0.10, coat=0.5,
                  coat_rough=0.08, ior=1.5)
    lib["band_glass"] = m
    m, nt, b = MB.mat("INT_Mesh_Silver")                # the door's metal speaker mesh
    MB.set_inputs(b, base=(0.55, 0.55, 0.57), metallic=1.0, roughness=0.30)
    IM._textured(nt, b, maps["perforation"], SM.TILE["perforation"], 1.0)
    lib["mesh_silver"] = m
    m, nt, b = MB.mat("INT_Pad_Light")                  # the cup holder bay's pale lining
    MB.set_inputs(b, base=(0.30, 0.10, 0.12), metallic=0.0, roughness=0.5)
    lib["bay"] = m
    return lib


# ------------------------------------------------------------------- dash
def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    zg = z_glass(1.285, y) - 0.003
    fx = FACE_X
    zt = Z_TOP
    return [
        (1.285, zg),                                 # 0 glass base
        (1.235, zt - 0.006), (1.175, zt + 0.003),    # 1,2 top pad
        (fx + 0.012, zt - 0.004),                    # 3 the lip
        (fx + 0.002, zt - 0.022),                    # 4 lip underside
        (fx - 0.004, zt - 0.030),                    # 5 slot top (the lit vent slot)
        (fx - 0.004, zt - 0.042),                    # 6 slot bottom
        (fx, zt - 0.052), (fx + 0.001, 1.000),       # 7,8 upper red face
        (fx + 0.002, 0.985),                         # 9 chrome line
        (fx + 0.001, 0.978), (fx + 0.001, 0.925),    # 10,11 the lit glass band
        (fx + 0.006, 0.918),                         # 12 below the band
        (fx + 0.018, 0.840), (fx + 0.040, 0.740), (fx + 0.075, 0.650), (fx + 0.135, 0.560),
        (fx + 0.215, 0.480), (fx + 0.290, 0.420),    # 13.. the face down to the footwell
    ]


DASH_COUNTS = [4, 4, 3, 3, 2, 3, 2, 4, 2, 2, 5, 2, 4, 4, 4, 4, 4, 4]
DASH_PANELS = [("TopPad", 0, 4, "leather_dash"), ("Lip", 4, 5, "gunmetal"), ("Slot", 5, 6, "ambient"),
               ("Upper", 6, 9, "leather_dash"), ("Band", 10, 11, "band_glass"),
               ("Face", 12, 18, "leather_dash")]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 120, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    # the filler between the upper face and the lit band, and between the band and the face
    made.append(sw.mesh("int_dash_Fill1", col, lib["leather_dash"], j0=sw.col(9), j1=sw.col(10)))
    made.append(sw.mesh("int_dash_Fill2", col, lib["leather_dash"], j0=sw.col(11), j1=sw.col(12)))
    # the chrome line above the band, a thin one on the lip
    p, n = sw.iso_col(sw.col(9), lift=0.0008)
    made.append(piping("int_dash_Chrome", p, col, lib["chrome"], r=0.0013, lateral=(1.0, 0.0, 0.0)))
    # a field of small lights in the band: points of the ambient material along it
    import random
    rng = random.Random(9)
    pts = []
    for k in range(260):
        i = rng.randrange(6, len(sw.pts) - 6)
        j = sw.col(10) + rng.random() * (sw.col(11) - sw.col(10))
        j = min(sw.col(11), max(sw.col(10), int(round(j))))
        n_ = sw.normal(i, j)
        q = Vector(sw.pts[i][j]) + n_ * 0.0007
        pts.append((q, n_))
    made.append(_dots("int_dash_Stars", pts, col, lib["ambient"], r=0.0016))
    # the stitch along the face's upper third
    p, n = sw.iso_col(sw.col(13) + 2, int(len(sw.pts) * 0.04), int(len(sw.pts) * 0.96))
    made.append(stitches("int_dash_Stitch", p, n, col, lib["thread"], side=0.0035))
    made.append(F.ngon_cap(col, "int_dash_EndL", list(sw.pts[0]), lib["leather_dash"], (0.0, 1.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndR", list(sw.pts[-1]), lib["leather_dash"], (0.0, -1.0, 0.0)))
    made += build_dash_details(col, lib, sw)
    return made, sw


def _dots(name, pts, col, mat, r=0.0015):
    """Small facing discs at points on a surface (a field of lights)."""
    verts, faces = [], []
    for q, n in pts:
        t = n.cross(Vector((0.0, 0.0, 1.0)))
        if t.length < 1e-4:
            t = n.cross(Vector((1.0, 0.0, 0.0)))
        t.normalize()
        b = n.cross(t)
        base = len(verts)
        verts.append(tuple(q))
        for k in range(6):
            a = 2 * math.pi * k / 6.0
            verts.append(tuple(q + t * (r * math.cos(a)) + b * (r * math.sin(a))))
        for k in range(6):
            faces.append([base, base + 1 + k, base + 1 + (k + 1) % 6])
    return M.obj(name, verts, faces, col, mat, smooth=False)


def build_dash_details(col, lib, sw):
    made = []
    # the HUD's window on the top pad ahead of the driver
    made.append(F.box(col, "int_dash_HUD", (1.205, WHEEL_Y, Z_TOP + 0.002), (0.110, 0.240, 0.0016),
                      lib["screen_glass"], r=0.0008))
    # the speaker grille at the middle of the top pad
    made += F.disc(col, "int_dash_Tweeter", (1.230, -0.020, Z_TOP - 0.004), (0.0, 0.0, 1.0), 0.030,
                   lib["speaker"], dome=0.0, rim=0.003, rim_mat=lib["chrome"])
    # the round light in the red face on the driver's side (c10_0006: a pale button)
    made += F.disc(col, "int_dash_Pearl", (FACE_X + 0.018, 0.560, 0.880), (-1.0, 0.0, 0.0), 0.012,
                   lib["chrome"], dome=0.002)
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b + 0.012,
                       0.020, 0.012, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())
    # its stand: a slim blade down into the dash
    made.append(F.box(col, "int_screen_stand", (SCREEN_C[0] + 0.045, SCREEN_C[1], SCREEN_C[2] - 0.125),
                      (0.040, 0.110, 0.100), lib["satin"], r=0.008))
    # the cluster: a slim strip in a black glass window behind the wheel
    made.append(F.box(col, "int_cluster_window", (FACE_X - 0.001, WHEEL_Y, CLUSTER_C[2]),
                      (0.006, CLUSTER_W + 0.030, CLUSTER_H + 0.026), lib["band_glass"], r=0.012))
    q = F.screen_quad("screen_cluster", CLUSTER_C, CLUSTER_W, CLUSTER_H, 0.0, col, lift=0.0010)
    q.data.materials.append(F.screen_material())
    made.append(q)
    return made


def cluster_image(path=None, w=1024, h=192):
    """The cluster strip's resting display, laid out as c10_0014-17 show it: dark, round icons at the
    left, the gear letter P in the middle, range figures at the right, a purple glow along its lower
    edge. Generated pixels."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.010, 0.008, 0.022)
    glow = np.exp(-((yy - 0.95 * h) / (0.30 * h)) ** 2)
    img += glow[..., None] * np.array([0.22, 0.10, 0.52], np.float32) * 0.8
    white = np.array([0.85, 0.86, 0.92])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c
    s = 0.020 * h
    for k in range(3):                               # three round icons
        cx, cy = (0.07 + 0.045 * k) * w, 0.42 * h
        img[(((xx - cx) ** 2 + (yy - cy) ** 2) < (0.11 * h) ** 2) & (((xx - cx) ** 2 + (yy - cy) ** 2) > (0.085 * h) ** 2)] = white * 0.6
    gx, gy = 0.490 * w, 0.22 * h
    rect(gx, gx + 0.9 * s, gy, gy + 8.0 * s, white)
    rect(gx, gx + 4.2 * s, gy, gy + 1.0 * s, white)
    rect(gx, gx + 4.2 * s, gy + 3.8 * s, gy + 4.8 * s, white)
    rect(gx + 3.3 * s, gx + 4.2 * s, gy, gy + 4.8 * s, white)
    for (fx, fy, ww) in ((0.80, 0.22, 0.05), (0.80, 0.45, 0.07), (0.80, 0.68, 0.06)):
        rect(fx * w, fx * w + ww * w, fy * h, fy * h + 0.10 * h, white * 0.65)
    out = path or os.path.join(TEX_DIR, "cluster_g9l.png")
    return CP.image_from_pixels("T_Cluster_G9L", img, out)


# ---------------------------------------------------------- steering wheel
# a rounded-square rim, 0.37 wide and 0.35 tall (c10_0002, c10_0008): a superellipse with a slightly
# flatter bottom
G9L_LOOP = [(0.185, 0.0), (0.183, 0.058), (0.172, 0.105), (0.148, 0.136), (0.105, 0.151),
            (0.0, 0.155), (-0.105, 0.151), (-0.148, 0.136), (-0.172, 0.105), (-0.183, 0.058),
            (-0.185, 0.0), (-0.183, -0.058), (-0.172, -0.103), (-0.148, -0.134), (-0.105, -0.149),
            (0.0, -0.153), (0.105, -0.149), (0.148, -0.134), (0.172, -0.103), (0.183, -0.058)]
G9L_WHEEL = dict(
    radius=0.182, loop=dict(pts=G9L_LOOP),
    flat_bottom=-0.153, flat_top=0.155, section=(0.0195, 0.0210),
    grip_swell=0.04,
    segments=[(0.0, 180.0, "pad_grey"), (180.0, 360.0, "pad_grey")],
    marker=None,
    hub=dict(w=0.250, h=0.108, sides=36, r_corner=0.0, dome=0.012, depth=0.05,
             pad_role="leather_seat", housing_role="leather_seat"),
    spokes=dict(v=0.004, h=0.070, t=0.026, u_in=0.110, pad=(0.050, 0.044), frame="chrome",
                pad_role="leather_seat", body_role="leather_seat"),
    lower_spoke=None,
    buttons=[(0.118, -0.098, 0.0140, "satin", "chrome"), (-0.118, -0.098, 0.0140, "satin", "chrome")],
    logo=None,
)


def build_wheel(col, lib):
    from carkit.interior import steering as ST
    made, fr = ST.wheel(col, lib, G9L_WHEEL, WHEEL_C, WHEEL_TILT)
    lift = 0.0215 + G9L_WHEEL["hub"]["dome"] * 0.97
    # the maker's X on the hub: two crossed slim chrome bars (c10_0009)
    w, h = 0.046, 0.024
    for k, (a, b) in enumerate((((-w, h), (w, -h)), ((w, h), (-w, -h)))):
        A, B = Vector(fr.p(a[0], a[1], lift)), Vector(fr.p(b[0], b[1], lift))
        made.append(tube("int_wheel_X%d" % k, [tuple(A.lerp(B, t / 8.0)) for t in range(9)],
                         ellipse(0.0022, 0.0022, 6), col, lib["chrome"], lateral=tuple(fr.A)))
    return made


# ------------------------------------------------------------------ seats
def _seat_spec():
    """The front bucket (the SU7's, carkit.interior.seat) in bordeaux Nappa: tall backrest, deep
    bolsters, a separate headrest on two posts (c3_0001, c3_0019)."""
    from carkit.interior import seat as SE
    import copy
    sp = copy.deepcopy(SE.SU7_ULTRA_FRONT)
    sp["backrest"]["spine"] = [(0.0, 0.0), (-0.045, 0.0957), (-0.13, 0.286), (-0.20, 0.4576),
                               (-0.245, 0.570), (-0.285, 0.665), (-0.308, 0.705), (-0.314, 0.722),
                               (-0.316, 0.730), (-0.315, 0.720), (-0.311, 0.700)]
    sp["backrest"]["half_w"] = Curve([(0.0, 0.268), (0.45, 0.280), (0.78, 0.270), (0.90, 0.250),
                                      (1.0, 0.205)], mode="pchip")
    sp["backrest"]["bolster"] = Curve([(0.0, 0.55), (0.30, 1.0), (0.58, 0.80), (0.80, 0.35),
                                       (1.0, 0.0)], mode="pchip")
    sp["backrest"]["centre_half"] = Curve([(0.0, 0.135), (0.8, 0.130), (1.0, 0.100)], mode="pchip")
    sp["cushion"]["bolster_h"] = 0.050
    sp["backrest"]["bolster_h"] = 0.082
    sp["mats"] = dict(centre="leather_seat", crown="leather_seat", face="leather_seat",
                      shell="leather_seat", piping="leather_seat", stitch="thread",
                      base="leather_seat")
    sp["stitch_half_gap"] = 0.012
    sp["headrest"] = dict(w=0.300, h=0.220, t=0.090, r=0.060, gap=0.045, top=(-0.316, 0.730))
    return sp


def _rear_spec():
    """The rear bench's outer seats: the front seat, backrest 14 % shorter, a smaller headrest."""
    import copy
    sp = copy.deepcopy(_seat_spec())
    sp["backrest"]["spine"] = [(x * 1.02, z * 0.86) for (x, z) in sp["backrest"]["spine"]]
    hr = sp["headrest"]
    sp["headrest"] = dict(w=0.270, h=0.185, t=0.082, r=0.052, gap=0.040,
                          top=(hr["top"][0] * 1.02, hr["top"][1] * 0.86))
    return sp


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        parts, cush, back = SE.seat(col, lib, _seat_spec(), (FRONT_BIGHT_X, y, FRONT_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += CP.headrest(col, lib, _seat_spec(), (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_" + tag)
        made += CP.seat_shroud(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_%s_base" % tag,
                               FLOOR_Z, role="lower_card")
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, cush, back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += CP.headrest(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z), "int_seat_" + tag)
    # the centre place: a narrower cushion and backrest between the two, its own headrest
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.24, 0.0, REAR_BIGHT_Z - 0.03),
                      (0.52, 0.30, 0.12), lib["leather_seat"], r=0.035))
    made.append(F.box(col, "int_rear_centre_back", (REAR_BIGHT_X - 0.15, 0.0, REAR_BIGHT_Z + 0.31),
                      (0.14, 0.30, 0.62), lib["leather_seat"], r=0.04, pitch=math.radians(-16)))
    made.append(CP.pillow(col, "int_rear_centre_head",
                          (REAR_BIGHT_X - 0.18 - 0.04, 0.0, REAR_BIGHT_Z + 0.68), 0.25, 0.17, 0.080,
                          0.050, lib["leather_seat"], -math.radians(16)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.18, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.64, 1.32, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["leather_seat"], r=0.02))
    return made


# ---------------------------------------------------------------- console
# The floating bridge (c3_0015, c10_0002): an armrest box with a lid, a cup-holder bay at its front
# and a wireless pad under a flat lid, standing on pedestals. Top centreline height, rear to front.
CONSOLE_TOP = Curve([
    (-0.345, 0.775), (-0.330, 0.815), (-0.300, 0.836), (-0.240, 0.842), (0.050, 0.844),
    (0.210, 0.840), (0.260, 0.820), (0.285, 0.790), (0.330, 0.776), (0.640, 0.776),
    (0.700, 0.778), (0.760, 0.790), (0.820, 0.802), (0.880, 0.808),
], mode="pchip")
CONSOLE_HW = 0.130
CONSOLE_X0, CONSOLE_X1 = -0.345, 0.880
CONSOLE_BOTTOM = 0.560                   # the bridge's underside; below it are the pedestals


def _console_stations():
    xs = []
    x = CONSOLE_X0
    while x < CONSOLE_X1:
        xs.append(x)
        dense = (x < -0.30) or (0.20 < x < 0.34) or (0.82 < x < 0.88)
        x += 0.004 if dense else 0.016
    xs.append(CONSOLE_X1)
    return xs


def _bridge_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = CONSOLE_HW, 0.024
    zb = CONSOLE_BOTTOM
    pts = [(-hw + 0.02, zb), (-hw, zb + 0.02), (-hw, zt - r)]
    for k in range(1, n_arc):
        a = math.pi - 0.5 * math.pi * k / n_arc
        pts.append((-hw + r + r * math.cos(a), zt - r + r * math.sin(a)))
    ny = 30
    for k in range(ny + 1):
        y = -hw + r + (2 * (hw - r)) * k / ny
        pts.append((y, zt + 0.0015 * (1.0 - (y / (hw - r)) ** 2)))
    for k in range(1, n_arc):
        a = 0.5 * math.pi - 0.5 * math.pi * k / n_arc
        pts.append((hw - r + r * math.cos(a), zt - r + r * math.sin(a)))
    pts += [(hw, zt - r), (hw, zb + 0.02), (hw - 0.02, zb)]
    return pts


def build_console(col, lib):
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _bridge_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_dash"])
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.70)))
    made.append(ob)
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in
                                                      _bridge_section(xs[0])],
                           lib["leather_dash"], (-1.0, 0.0, 0.0)))
    made.append(F.ngon_cap(col, "int_console_front", [(xs[-1] + 0.0005, y, z) for (y, z) in
                                                       _bridge_section(xs[-1])],
                           lib["leather_dash"], (1.0, 0.0, 0.0)))
    # the underside: a flat panel closing the bridge's bottom
    under = []
    for x in (xs[0], xs[-1]):
        under.append([(x, -CONSOLE_HW + 0.02, CONSOLE_BOTTOM), (x, CONSOLE_HW - 0.02, CONSOLE_BOTTOM)])
    ub = grid_mesh("int_console_under", under, col, lib["lower_card"])
    M.orient(ub.data, lambda c: (0.0, 0.0, -1.0))
    made.append(ub)
    # the pedestals: a front one rising out of the floor into the dash, a rear one under the armrest
    for nm, x0, x1, hw in (("F", 0.700, 0.990, 0.105), ("R", -0.250, -0.050, 0.085)):
        made.append(F.box(col, "int_console_ped" + nm, (0.5 * (x0 + x1), 0.0, 0.5 * (FLOOR_Z + CONSOLE_BOTTOM)),
                          (x1 - x0, 2 * hw, CONSOLE_BOTTOM - FLOOR_Z), lib["lower_card"], r=0.030))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.0015 * (1.0 - (y / (CONSOLE_HW - 0.024)) ** 2) + lift)

    # the cup-holder bay: a rounded recess with a chrome rim (c3_0015), two cups side by side
    outer = F.round_rect_xy(0.232, 0.456, -0.092, 0.092, 0.040)
    frame = [top(x, y, 0.0012) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0012)]
    made.append(tube("int_console_bay", frame, ellipse(0.0030, 0.0026, 8), col, lib["chrome"],
                     lateral=(0.0, 0.0, 1.0)))
    for k, yc in enumerate((0.047, -0.047)):
        made += F.disc(col, "int_console_cupwell%d" % k, top(0.344, yc, -0.004), (0.0, 0.0, 1.0), 0.036,
                       lib["bay"], rim=None)
    # the flat lid over the wireless pad at the front, with its slim pen
    outer = F.round_rect_xy(0.500, 0.800, -0.100, 0.100, 0.022)
    frame = [top(x, y, 0.0012) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0012)]
    made.append(tube("int_console_lid", frame, ellipse(0.0016, 0.0016, 6), col, lib["thread"],
                     lateral=(0.0, 0.0, 1.0)))
    pen = [top(0.610 + 0.080 * t / 6.0, -0.004 + 0.008 * t / 6.0, 0.0030) for t in range(7)]
    made.append(tube("int_console_pen", pen, ellipse(0.0030, 0.0030, 8), col, lib["chrome"],
                     lateral=(0.0, 1.0, 0.0)))
    # the armrest lid's seam
    frame = [top(x, y, 0.0010) for (x, y) in F.round_rect_xy(-0.325, 0.190, -0.118, 0.118, 0.034)]
    frame.append(frame[0])
    made.append(tube("int_console_armrest_seam", frame, ellipse(0.0014, 0.0014, 6), col, lib["thread"],
                     lateral=(0.0, 0.0, 1.0)))
    # the screen on the bridge's rear face: a small tablet (c3_0030/31)
    made.append(F.box(col, "int_console_rearscreen", (CONSOLE_X0 - 0.008, 0.0, CONSOLE_TOP(CONSOLE_X0) - 0.085),
                      (0.014, 0.160, 0.110), lib["piano"], r=0.008))
    return made
