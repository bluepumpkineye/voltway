"""BYD Seal 07 EV cabin: Morning Shimmer Grey (晨粼灰) cool-grey Nappa interior,
built with carkit.interior from hardpoints read off Autohome Series 8462 photographs
(hmi/c10_0001..0010, cabin/c3_0001..0012).

What the photographs show:
    colours      Light cool grey (Morning Shimmer Grey 晨粼灰) Nappa leather seats,
                 door cards and floating console, contrasted with dark charcoal upper
                 dash pad, dark plush carpet, and light grey headliner.
    dash         Ocean wave dashboard with glossy black central fascia band spanning
                 across the cluster and center (c10_0004), 10.25-inch recessed instrument
                 cluster, integrated AC vent ribbon, and soft-touch padded lower dash.
    screen       15.6-inch floating rotating DiLink 100 center touchscreen tilted 8 deg.
    console      Floating Ocean bridge console with dual central AC vents, dual 50W
                 wireless phone charging pads with cooling vents, physical silver toggle/
                 roller bar (drive mode, volume, defog, hazards), dual cupholders, and
                 split padded armrest.
    wheel        4-spoke Ocean D-cut steering wheel in cool grey/charcoal leather with
                 silver spoke accents, control pods, chrome "BYD" wordmark hub emblem,
                 and right-side column shifter (怀挡).
    seats        Ocean wave sculpted bucket seats with integrated headrest geometry,
                 lumbar bolster wings, and breathable perforated centre inserts.

Hardpoints are in the build's axes: +X forward, +Y left (LHD), +Z up.
"""
import math
import bpy
from mathutils import Vector

import seal_surface as S
import seal_panels as PN
import cabin_parts as CP
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "Seal_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.295
DRIVER_Y = 0.345
PASS_Y = -0.345

# 15.6-inch floating center touchscreen (16:9 ratio): 354 x 222 mm, tilted back 8 deg
SCREEN_W, SCREEN_H = 0.354, 0.222
SCREEN_C = (0.700, 0.000, 0.965)
SCREEN_TILT = math.radians(8.0)
SCREEN_BORDER = 0.0065

WHEEL_Y = 0.345
WHEEL_C = (0.540, WHEEL_Y, 0.910)
WHEEL_TILT = math.radians(22.0)

# 10.25-inch recessed instrument cluster in the dash fascia
BAND_X = 0.770
BAND_TOP, BAND_BOT = 1.015, 0.890
CLUSTER_C = (BAND_X - 0.004, WHEEL_Y, 0.950)
CLUSTER_W, CLUSTER_H = 0.265, 0.105

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.075, 0.510
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -0.960, 0.490, 0.360

DASH_HALF = 0.725                  # dash ends at front door cards
MIRROR_C = (0.340, 0.000, 1.330)   # frameless rear-view mirror

# Linear RGB palette for Morning Shimmer Grey (晨粼灰)
SEAT = (0.380, 0.395, 0.415)           # cool light grey Nappa leather
DASH_LEATHER = (0.040, 0.042, 0.046)   # dark charcoal soft-touch upper dash pad
DOOR_LOWER = (0.360, 0.375, 0.395)     # matching cool grey on door lower & console
CARPET = (0.035, 0.036, 0.040)         # dark charcoal plush carpet
SUEDE = (0.320, 0.330, 0.345)          # cool grey headliner
OCEAN_TRIM = (0.120, 0.130, 0.145)     # dark satin metallic trim accents
BRONZE = (0.52, 0.53, 0.56)            # satin silver / brushed aluminium accents
FELT = (0.030, 0.031, 0.034)


def z_glass(x, y):
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.65)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    lib = IM.build_library(accent=SEAT, maps=maps)
    lib["leather_seat"] = IM.leather("INT_Leather_Seat", SEAT, maps, roughness=0.42, coat=0.10)
    lib["leather_accent"] = lib["leather_seat"]
    lib["leather_dash"] = IM.leather("INT_Leather_Dash", DASH_LEATHER, maps, roughness=0.50,
                                     coat=0.06, strength=0.8)
    lib["leather_door"] = IM.leather("INT_Leather_Door", DOOR_LOWER, maps, roughness=0.46, coat=0.08)
    lib["wheel_leather"] = lib["leather_seat"]
    lib["headliner"] = IM.alcantara("INT_Headliner", SUEDE, maps, sheen=0.55)

    m, nt, b = MB.mat("INT_Thread_Seat")
    MB.set_inputs(b, base=(0.42, 0.44, 0.47), metallic=0.0, roughness=0.55, sheen=0.3)
    lib["thread"] = m

    m, nt, b = MB.mat("INT_Carpet_Dark")
    MB.set_inputs(b, base=CARPET, metallic=0.0, roughness=0.96, specular=0.2, sheen=0.4)
    IM._textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m

    m, nt, b = MB.mat("INT_Ocean_Trim")
    MB.set_inputs(b, base=OCEAN_TRIM, metallic=0.3, roughness=0.32, coat=0.3, coat_rough=0.15)
    lib["wood"] = m

    m, nt, b = MB.mat("INT_Silver_Satin")
    MB.set_inputs(b, base=BRONZE, metallic=0.95, roughness=0.20)
    lib["bronze"] = m

    m, nt, b = MB.mat("INT_Felt")
    MB.set_inputs(b, base=FELT, metallic=0.0, roughness=0.97, specular=0.2, sheen=0.6)
    IM._textured(nt, b, maps["alcantara"], SM.TILE["alcantara"], 1.0)
    lib["felt"] = m

    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.005, 0.005, 0.006), metallic=0.0, roughness=0.08, coat=0.8,
                  coat_rough=0.04, ior=1.52)
    lib["band_glass"] = m

    m, nt, b = MB.mat("INT_Crystal")
    MB.set_inputs(b, base=(0.60, 0.62, 0.65), metallic=0.0, roughness=0.05, coat=1.0,
                  coat_rough=0.02, ior=1.52)
    lib["crystal"] = m

    m, nt, b = MB.mat("INT_Chrome_Mirror")
    MB.set_inputs(b, base=(0.86, 0.88, 0.90), metallic=0.98, roughness=0.08)
    lib["bronze_mirror"] = m

    m, nt, b = MB.mat("INT_Key_Glass")
    MB.set_inputs(b, base=(0.28, 0.30, 0.32), metallic=0.0, roughness=0.04, coat=1.0,
                  coat_rough=0.02, ior=1.52)
    lib["key_glass"] = m

    m, nt, b = MB.mat("INT_BYD_Logo")
    MB.set_inputs(b, base=(0.90, 0.92, 0.95), metallic=1.0, roughness=0.12)
    lib["mark_navy"] = m
    lib["mark_blue"] = m
    lib["logo_chrome"] = lib["chrome"]

    m, nt, b = MB.mat("INT_Wheel_Panel")
    MB.set_inputs(b, base=(0.045, 0.045, 0.050), metallic=0.4, roughness=0.30)
    lib["pod_panel"] = m

    m, nt, b = MB.mat("INT_Wheel_Roller")
    MB.set_inputs(b, base=(0.80, 0.82, 0.85), metallic=0.95, roughness=0.22)
    lib["roller"] = m

    return lib


# ------------------------------------------------------------------- dash
def _hood(y):
    return 1.0 - CP.smooth((abs(y - WHEEL_Y) - 0.175) / 0.040)


Z_PAD = 1.015


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    h = _hood(y)
    zg = z_glass(0.835, y) - 0.004
    zt = Z_PAD + 0.010 * h
    bx = BAND_X
    return [
        (0.835, zg),                                 # 0 glass base inside cowl
        (0.810, zt - 0.014), (0.785, zt),            # 1,2 top pad
        (bx + 0.020, zt + 0.003),                    # 3 over the band
        (bx + 0.004 - 0.010 * h, zt - 0.012),        # 4 lip
        (bx - 0.002 - 0.010 * h, BAND_TOP),          # 5 band top
        (bx - 0.002 - 0.010 * h, BAND_BOT),          # 6 band bottom
        (bx + 0.003, BAND_BOT - 0.003),              # 7 trim strip top
        (bx + 0.006, BAND_BOT - 0.062),              # 8 trim strip bottom
        (bx + 0.010, BAND_BOT - 0.068),              # 9 silver accent line
        (bx + 0.014, 0.770), (bx + 0.030, 0.690), (bx + 0.060, 0.610), (bx + 0.105, 0.530),
        (bx + 0.178, 0.450), (bx + 0.250, 0.390),    # 10.. lower knee bolster down to footwell
    ]


DASH_COUNTS = [4, 3, 4, 3, 3, 4, 2, 5, 2, 3, 4, 4, 4, 4, 4]
DASH_PANELS = [("TopPad", 0, 5, "leather_dash"), ("Band", 5, 6, "band_glass"),
               ("Strip", 6, 9, "wood"), ("Face", 9, 15, "leather_door")]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 120, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))

    p, n = sw.iso_col(sw.col(9), lift=0.0008)
    made.append(piping("int_dash_Chrome", p, col, lib["chrome"], r=0.0013, lateral=(1.0, 0.0, 0.0)))
    p, n = sw.iso_col(sw.col(4), lift=0.0006)
    made.append(piping("int_dash_Lip", p, col, lib["leather_dash"], r=0.0016, lateral=(1.0, 0.0, 0.0)))

    p, n = sw.iso_col(sw.col(10) + 2, int(len(sw.pts) * 0.04), int(len(sw.pts) * 0.96))
    for sd in (0.0035,):
        made.append(stitches("int_dash_Stitch", p, n, col, lib["thread"], side=sd))
    made.append(F.ngon_cap(col, "int_dash_EndL", list(sw.pts[0]), lib["leather_door"], (0.0, 1.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndR", list(sw.pts[-1]), lib["leather_door"], (0.0, -1.0, 0.0)))
    made += build_dash_details(col, lib, sw)
    return made, sw


def build_dash_details(col, lib, sw):
    made = []
    bx = BAND_X
    for k, yc in enumerate((0.640, -0.640)):
        made.append(F.box(col, "int_dash_SideVent%d" % k, (bx - 0.006, yc, 0.940), (0.012, 0.068, 0.038),
                          lib["piano"], r=0.004))
        for j in range(5):
            made.append(F.box(col, "int_dash_SideVent%d_v%d" % (k, j),
                              (bx - 0.012, yc + 0.022 - 0.011 * j, 0.940), (0.004, 0.003, 0.030),
                              lib["gunmetal"], r=0.001))
    made += F.disc(col, "int_dash_Tweeter", (0.805, 0.0, Z_PAD - 0.006), (0.0, 0.0, 1.0), 0.030,
                   lib["speaker"], dome=0.0, rim=0.003, rim_mat=lib["chrome"])
    made.append(F.box(col, "int_dash_HUD", (0.800, WHEEL_Y, Z_PAD - 0.008), (0.095, 0.215, 0.0016),
                      lib["screen_glass"], r=0.0008))
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    # 15.6-inch center touchscreen
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b + 0.010,
                       0.018, 0.012, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())

    # Slim center screen swivel stand
    made.append(F.box(col, "int_screen_stand", (SCREEN_C[0] + 0.036, 0.0, SCREEN_C[2] - 0.145),
                      (0.036, 0.090, 0.118), lib["satin"], r=0.008))

    # 10.25-inch recessed instrument cluster
    q = F.screen_quad("screen_cluster", CLUSTER_C, CLUSTER_W, CLUSTER_H, 0.0, col, lift=0.0010)
    q.data.materials.append(F.screen_material())
    made.append(q)
    return made


def cluster_image(path=None, w=1024, h=384):
    """The BYD Seal cluster resting display: speed, battery %, DiPilot ADAS, energy stats."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.006, 0.010, 0.018)
    white = np.array([0.84, 0.88, 0.94])
    cyan = np.array([0.08, 0.58, 0.72])
    blue = np.array([0.06, 0.28, 0.52])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c

    s = 0.018 * h
    sx, sy = 0.46 * w, 0.22 * h
    rect(sx, sx + 3 * s, sy, sy + s * 0.5, white)
    rect(sx, sx + 3 * s, sy + 6.5 * s, sy + 7 * s, white)
    rect(sx, sx + s * 0.5, sy, sy + 7 * s, white)
    rect(sx + 2.5 * s, sx + 3 * s, sy, sy + 7 * s, white)

    cx, cy = 0.50 * w, 0.65 * h
    img[(((xx - cx) / (0.038 * w)) ** 2 + ((yy - cy) / (0.20 * h)) ** 2) < 1.0] = blue
    rect(0.12 * w, 0.32 * w, 0.82 * h, 0.86 * h, cyan)
    for (fx, fy) in ((0.10, 0.30), (0.22, 0.30), (0.10, 0.54), (0.22, 0.54)):
        rect(fx * w, fx * w + 0.07 * w, fy * h, fy * h + 0.05 * h, white * 0.6)
    for (fx, fy) in ((0.75, 0.32), (0.75, 0.56)):
        rect(fx * w, fx * w + 0.14 * w, fy * h, fy * h + 0.05 * h, white * 0.55)

    out = path or os.path.join(TEX_DIR, "cluster_seal.png")
    return CP.image_from_pixels("T_Cluster_Seal", img, out)


# ---------------------------------------------------------- steering wheel
# BYD Seal 4-spoke D-cut steering wheel loop (c10_0001, c10_0002)
def _seal_loop(a=0.178, b_top=0.172, b_low=0.165):
    pts = []
    for k in range(0, 360, 12):
        t = math.radians(k)
        c, s_ = math.cos(t), math.sin(t)
        n, b = (2.0, b_top) if s_ >= 0.0 else (2.40, b_low)
        pts.append((a * math.copysign(abs(c) ** (2.0 / n), c), b * math.copysign(abs(s_) ** (2.0 / n), s_)))
    return pts


SEAL_LOOP = _seal_loop()
HUB_DV = -0.020


def _hub_outline(a=0.082, b=0.065, n=2.8, k=56):
    pts = []
    for i in range(k):
        t = 2.0 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** (2.0 / n), c)
        v = b * math.copysign(abs(s) ** (2.0 / n), s)
        pts.append((u * (0.92 + 0.08 * v / b), v))
    return pts


BYD_SEAL_WHEEL = dict(
    radius=0.175, loop=dict(pts=SEAL_LOOP),
    flat_bottom=-0.165, flat_top=None, section=(0.0145, 0.0165),
    grip_swell=0.045,
    segments=[(0.0, 180.0, "wheel_leather"), (180.0, 360.0, "wheel_leather")],
    marker=None,
    hub=dict(w=0.160, h=0.130, sides=36, r_corner=0.0, dome=0.005, depth=0.048,
             pad_role="leather_seat", housing_role="leather_seat", outline=_hub_outline()),
)


def _wheel_pods(fr, col, lib):
    made = []
    pitch = WHEEL_TILT
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        rows = []
        for k in range(13):
            t = k / 12.0
            u = side * (0.068 + 0.098 * t)
            hh = 0.5 * (0.054 - 0.032 * t)
            vc = -0.002 - 0.004 * t
            prof = [(-hh, -0.004), (-hh * 0.97, 0.0075), (-hh * 0.82, 0.0120), (-hh * 0.35, 0.0138),
                    (hh * 0.35, 0.0138), (hh * 0.82, 0.0120), (hh * 0.97, 0.0075), (hh, -0.004),
                    (hh * 0.8, -0.022), (-hh * 0.8, -0.022)]
            rows.append([fr.p(u, vc + a, b) for (a, b) in prof])
        ob = grid_mesh("int_wheel_pod" + tag, rows, col, lib["gunmetal"], wrap_t=True)
        M.orient(ob.data, lambda c: tuple(fr.A))
        made.append(ob)
        made.append(F.box(col, "int_wheel_panel" + tag, fr.p(side * 0.128, 0.0000, 0.0140),
                          (0.0030, 0.048, 0.026), lib["pod_panel"], r=0.0010, pitch=pitch))
        made.append(F.box(col, "int_wheel_roller" + tag, fr.p(side * 0.126, 0.0000, 0.0155),
                          (0.0036, 0.012, 0.016), lib["roller"], r=0.0012, pitch=pitch))
        for j, vk in enumerate((0.0065, -0.0035, -0.0140)):
            made.append(F.box(col, "int_wheel_slot%s%d" % (tag, j), fr.p(side * 0.095, vk, 0.0142),
                              (0.0030, 0.0160, 0.0050), lib["piano"], r=0.0008, pitch=pitch))
    return made


def _wheel_legs(fr, col, lib):
    made = []
    pts = [(0.075, -0.034, 0.007), (0.090, -0.085, 0.006), (0.108, -0.130, 0.004)]
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        leg = smooth_path([fr.p(side * u, v, w) for (u, v, w) in pts], 14)
        made.append(tube("int_wheel_leg" + tag, leg, ellipse(0.0065, 0.0118, 12), col, lib["gunmetal"],
                         lateral=tuple(fr.A)))
        edge = smooth_path([fr.p(side * (u - 0.0120), v, w + 0.0035) for (u, v, w) in pts], 14)
        made.append(tube("int_wheel_legedge" + tag, edge, ellipse(0.0028, 0.0030, 8), col, lib["chrome"],
                         lateral=tuple(fr.A)))
    return made


def _wheel_mark(frh, col, lib):
    """Chrome 'BYD' emblem on the steering wheel hub."""
    made = []
    inter = _font("Inter.woff2")
    p = frh.p(0.0, 0.016, 0.0245)
    t = M.text_mesh("int_wheel_byd", "BYD", 0.024, col, lib["logo_chrome"], extrude=0.0012, font=inter, resolution=4)
    pitch = WHEEL_TILT
    from mathutils import Matrix
    t.matrix_world = Matrix.Translation(Vector(p) - Vector((0.020, 0.0, 0.0))) @ Matrix.Rotation(pitch, 4, 'Y')
    made.append(t)
    return made


def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_wheel(col, lib):
    from carkit.interior import steering as ST
    fr = ST.WheelFrame(WHEEL_C, WHEEL_TILT)
    frh = ST.WheelFrame(tuple(Vector(WHEEL_C) + fr.V * HUB_DV), WHEEL_TILT)
    made = ST.rim(fr, BYD_SEAL_WHEEL, col, lib)
    made += ST.hub(frh, BYD_SEAL_WHEEL, col, lib)
    made += _wheel_pods(fr, col, lib)
    made += _wheel_legs(fr, col, lib)
    made += ST.column(fr, col, lib)
    made += _wheel_mark(frh, col, lib)
    # Right-side column shifter (怀挡, c10_0001, c10_0002)
    p_stalk = tuple(Vector(WHEEL_C) + fr.U * 0.115 - fr.V * 0.010 - fr.A * 0.060)
    made.append(F.box(col, "int_column_shifter", p_stalk, (0.014, 0.082, 0.016), lib["piano"],
                      r=0.003, pitch=WHEEL_TILT))
    return made


# ------------------------------------------------------------------ seats
def _seat_spec(k=0.86):
    from carkit.interior import seat as SE
    import copy
    sp = copy.deepcopy(SE.SU7_ULTRA_FRONT)
    base = [(0.0, 0.0), (-0.045, 0.0957), (-0.13, 0.286), (-0.20, 0.4576),
            (-0.240, 0.556), (-0.272, 0.640), (-0.288, 0.676), (-0.294, 0.694), (-0.297, 0.700)]
    sp["backrest"]["spine"] = [(x * k, z * k) for (x, z) in base]
    sp["backrest"]["end_cap"] = True
    sp["backrest"]["half_w"] = Curve([(0.0, 0.252), (0.45, 0.262), (0.78, 0.252), (0.90, 0.235),
                                      (1.0, 0.192)], mode="pchip")
    sp["backrest"]["bolster"] = Curve([(0.0, 0.55), (0.30, 1.0), (0.58, 0.75), (0.80, 0.35),
                                       (1.0, 0.0)], mode="pchip")
    sp["backrest"]["centre_half"] = Curve([(0.0, 0.130), (0.8, 0.125), (1.0, 0.095)], mode="pchip")
    sp["cushion"]["bolster_h"] = 0.044
    sp["backrest"]["bolster_h"] = 0.076
    sp["mats"] = dict(centre="leather_seat", crown="leather_seat", face="leather_seat",
                      shell="leather_seat", piping="leather_seat", stitch="thread",
                      base="leather_seat")
    sp["stitch_half_gap"] = 0.012
    sp["headrest"] = dict(w=0.305, h=0.225, t=0.094, r=0.055, gap=0.042, top=(-0.297 * k, 0.700 * k))
    return sp


FRONT_BACK_K = 0.85
REAR_BACK_K = 0.75


def _rear_spec():
    import copy
    sp = copy.deepcopy(_seat_spec(1.0))
    sp["backrest"]["spine"] = [(x * 1.02, z * REAR_BACK_K) for (x, z) in sp["backrest"]["spine"]]
    hr = sp["headrest"]
    sp["headrest"] = dict(w=0.275, h=0.168, t=0.082, r=0.048, gap=0.038,
                          top=(hr["top"][0] * 1.02, hr["top"][1] * REAR_BACK_K))
    return sp


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        front = _seat_spec(FRONT_BACK_K)
        parts, cush, back = SE.seat(col, lib, front, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += CP.headrest(col, lib, front, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_" + tag)
        made += CP.seat_shroud(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_%s_base" % tag,
                               FLOOR_Z)
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, cush, back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += CP.headrest(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z), "int_seat_" + tag)
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.22, 0.0, REAR_BIGHT_Z - 0.035),
                      (0.48, 0.28, 0.12), lib["leather_seat"], r=0.035))
    made.append(F.box(col, "int_rear_centre_back", (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.24),
                      (0.14, 0.27, 0.48), lib["leather_seat"], r=0.04, pitch=math.radians(-18)))
    made.append(CP.pillow(col, "int_rear_centre_head",
                          (REAR_BIGHT_X - 0.19 - 0.04, 0.0, REAR_BIGHT_Z + 0.54), 0.23, 0.15, 0.078,
                          0.044, lib["leather_seat"], -math.radians(18)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.18, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.60, 1.25, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["leather_seat"], r=0.02))
    return made


# ---------------------------------------------------------------- console
CONSOLE_TOP = Curve([
    (-0.220, 0.690), (-0.210, 0.730), (-0.195, 0.748), (-0.160, 0.755), (0.050, 0.758),
    (0.140, 0.752), (0.175, 0.738), (0.205, 0.698), (0.240, 0.690), (0.420, 0.690),
    (0.460, 0.694), (0.485, 0.716), (0.505, 0.736), (0.550, 0.742), (0.680, 0.745),
    (0.725, 0.752), (0.742, 0.765), (0.758, 0.768), (0.776, 0.770), (0.782, 0.792),
    (0.788, 0.850),
], mode="pchip")
CONSOLE_HW = 0.108
CONSOLE_X0, CONSOLE_X1 = -0.220, 0.788
Z_TRAY = 0.771


def _console_stations():
    xs = []
    x = CONSOLE_X0
    while x < CONSOLE_X1:
        xs.append(x)
        dense = (x < -0.18) or (0.16 < x < 0.25) or (0.44 < x < 0.52) or (0.72 < x < 0.80)
        x += 0.004 if dense else 0.014
    xs.append(CONSOLE_X1)
    return xs


def _console_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = CONSOLE_HW, 0.018
    pts = [(-hw, FLOOR_Z), (-hw, zt - 0.095), (-hw, zt - r)]
    for k in range(1, n_arc):
        a = math.pi - 0.5 * math.pi * k / n_arc
        pts.append((-hw + r + r * math.cos(a), zt - r + r * math.sin(a)))
    ny = 36
    for k in range(ny + 1):
        y = -hw + r + (2 * (hw - r)) * k / ny
        pts.append((y, zt + 0.0015 * (1.0 - (y / (hw - r)) ** 2)))
    for k in range(1, n_arc):
        a = 0.5 * math.pi - 0.5 * math.pi * k / n_arc
        pts.append((hw - r + r * math.cos(a), zt - r + r * math.sin(a)))
    pts += [(hw, zt - r), (hw, zt - 0.095), (hw, FLOOR_Z)]
    return pts


KEY_Y = [0.082, 0.058, 0.035, 0.012, -0.012, -0.035, -0.058, -0.082]


def _kp(c, p, s, t, n):
    cp, sp = math.cos(p), math.sin(p)
    return (c[0] + s * cp + n * sp, c[1] + t, c[2] - s * sp + n * cp)


def _console_controls(col, lib):
    """Ocean console toggle bar with physical roller / toggle keys (c10_0004)."""
    made = []
    made.append(F.box(col, "int_console_bezel", (0.760, 0.0, Z_TRAY - 0.0035), (0.055, 0.204, 0.007),
                      lib["piano"], r=0.0025))
    made.append(F.box(col, "int_console_tray", (0.7615, 0.0, Z_TRAY + 0.0008), (0.034, 0.190, 0.0020),
                      lib["bronze_mirror"], r=0.0005))
    zt = Z_TRAY + 0.0018
    for j, y in enumerate(KEY_Y):
        if j in (3, 4):
            c, p, h = (0.7605, y, zt + 0.0048), -0.25, 0.0090
            made.append(F.box(col, "int_console_key%d" % j, c, (0.0180, 0.0195, h), lib["key_glass"],
                              r=0.0015, pitch=p))
            made.append(F.box(col, "int_console_plate%d" % j, _kp(c, p, 0.0, 0.0, h / 2 + 0.0006),
                              (0.0140, 0.0155, 0.0012), lib["piano"], r=0.0003, pitch=p))
        else:
            made.append(F.box(col, "int_console_base%d" % j, (0.7575, y, zt + 0.0040), (0.0115, 0.0195, 0.0085),
                              lib["bronze_mirror"], r=0.0015, pitch=-0.30))
            made.append(F.box(col, "int_console_key%d" % j, (0.7640, y, zt + 0.0072), (0.0095, 0.0180, 0.0068),
                              lib["key_glass"], r=0.0028, pitch=-0.30))
    xv, zc = 0.772, 0.825
    made.append(F.box(col, "int_console_vent", (xv + 0.0085, 0.0, zc), (0.015, 0.205, 0.058), lib["piano"],
                      r=0.004))
    for j in range(9):
        made.append(F.box(col, "int_console_fin%d" % j, (xv - 0.0035, 0.080 - 0.020 * j, zc),
                          (0.0070, 0.0022, 0.038), lib["gunmetal"], r=0.0006))
    made.append(F.box(col, "int_console_slat", (xv - 0.0030, 0.0, zc), (0.0055, 0.188, 0.0035),
                      lib["gunmetal"], r=0.0006))
    return made


def build_console(col, lib):
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _console_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_door"])
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.70)))
    made.append(ob)
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in
                                                      _console_section(xs[0])],
                           lib["leather_door"], (-1.0, 0.0, 0.0)))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.0015 * (1.0 - (y / (CONSOLE_HW - 0.018)) ** 2) + lift)

    # Dual 50W wireless phone charging pads with cooling vents (c10_0004)
    for k, yc in enumerate((0.052, -0.052)):
        outer = F.round_rect_xy(0.490, 0.725, yc - 0.042, yc + 0.042, 0.014)
        frame = [top(x, y, 0.0014) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0014)]
        made.append(tube("int_console_frame%d" % k, frame, ellipse(0.0024, 0.0022, 8), col, lib["bronze_mirror"],
                         lateral=(0.0, 0.0, 1.0)))
        made.append(F.plate_with_hole("int_console_pad%d" % k, F.round_rect_xy(0.492, 0.723, yc - 0.040, yc + 0.040, 0.012),
                                      [], lambda x, y: top(x, y, 0.0007)[2], col, lib["felt"], nx=40, ny=24))

    made += _console_controls(col, lib)

    for k, yc in enumerate((0.052, -0.052)):
        ring = [top(0.315 + 0.042 * math.cos(2 * math.pi * j / 28), yc + 0.042 * math.sin(2 * math.pi * j / 28),
                    0.0016) for j in range(29)]
        made.append(tube("int_console_cup%d" % k, ring, ellipse(0.0022, 0.0022, 8), col, lib["chrome"],
                         lateral=(0.0, 0.0, 1.0)))
        made += F.disc(col, "int_console_cupwell%d" % k, top(0.315, yc, -0.006), (0.0, 0.0, 1.0), 0.039,
                       lib["rubber"], rim=None)

    for sd in (1.0, -1.0):
        line = [(x, sd * (CONSOLE_HW - 0.006), CONSOLE_TOP(x) - 0.028) for x in
                [CONSOLE_X0 + 0.04 + (CONSOLE_X1 - CONSOLE_X0 - 0.08) * t / 40.0 for t in range(41)]]
        made.append(tube("int_console_edge%s" % ("L" if sd > 0 else "R"), line,
                         ellipse(0.0015, 0.0015, 6), col, lib["bronze_mirror"], lateral=(0.0, 1.0, 0.0)))

    frame = [top(x, y, 0.0012) for (x, y) in F.round_rect_xy(-0.205, 0.140, -0.098, 0.098, 0.026)]
    frame.append(frame[0])
    made.append(tube("int_console_lid_frame", frame, ellipse(0.0015, 0.0015, 6), col, lib["thread"],
                     lateral=(0.0, 0.0, 1.0)))
    return made
