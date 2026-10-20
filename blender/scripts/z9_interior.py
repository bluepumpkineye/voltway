"""Denza Z9 cabin: the Pamir Brown (帕米尔棕) Nappa interior, built with carkit.interior from
hardpoints read off Autohome's cabin photographs (series 7838).

References (blender/reference/denza-z9/, spec 69559 the black car with the brown cabin):

    hmi/c10_0001-5     the dash straight on from the rear seats (A-pillars, mirror, the glass band,
                       the floating screen, the console, the pedals)
    hmi/c10_0006       the driver's binnacle and the wheel seen from the door
    hmi/c10_0048       the dash and console from the passenger side
    hmi/c10_0043-47    the console: key row, felt wireless pad, cup holders
    interior/c3_0001   the driver's seat from the open door; c3_0036 the cockpit from the passenger
                       side; c3_0003 the front door card; c3_0016/17 the rear seats

What the photographs show:

    colours      mocha-brown Nappa seats (a deeper red-brown), a lighter mauve-grey leather on the
                 dash, door cards and console, plush mauve carpet, a grey-brown suede headliner;
                 brushed rose-bronze wood-like strips with fine diagonal lines, chrome edge lines
    dash         a long, low, wide dash: a thin top pad over a continuous black glass band from
                 pillar to pillar (the 13.2 in cluster behind the wheel, a wide co-pilot display on
                 the passenger side, the side-mirror monitors in its ends), the brushed strip under
                 the band with a chrome line, a leather face that runs down into the console
    screen       a 17.3 in display floating on a slim stand over the console, tilted back
    console      a tall tower under the screen: a vent slot, a row of crystal keys, a grey felt
                 wireless pad with a bronze pen, two cup holders, a padded armrest; chrome edge lines
                 sweeping down both sides
    wheel        a squarish two-spoke wheel in mocha leather, chrome-edged spokes with button pods,
                 the round Denza mark on the hub
    seats        deep bucket seats with a separate headrest pillow, a smaller neck pillow, perforated
                 centre panels with diamond stitching

Hardpoints are in the build's axes: +X forward, +Y left (China is LHD), +Z up, the car's centre at
x = 0. They are first-pass readings checked by overlay (blender/scripts/z9_cabin.py compare).
"""
import math

import bpy
from mathutils import Vector

import z9_surface as S
import z9_panels as PN
import cabin_parts as CP
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "Z9_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.300
DRIVER_Y = 0.360
PASS_Y = -0.360

# the 17.3 in floating display (16:10): the plane of its front face, tilted back 9 degrees
SCREEN_W, SCREEN_H = 0.3727, 0.2329
SCREEN_C = (0.800, 0.000, 1.000)
SCREEN_TILT = math.radians(9.0)
SCREEN_BORDER = 0.0070

WHEEL_Y = 0.360
WHEEL_C = (0.600, WHEEL_Y, 0.930)
WHEEL_TILT = math.radians(21.0)

# the glass band across the dash: its front face stands at x BAND_X
BAND_X = 0.870
BAND_TOP, BAND_BOT = 1.056, 0.920
CLUSTER_C = (BAND_X - 0.004, WHEEL_Y, 0.985)
CLUSTER_W, CLUSTER_H = 0.330, 0.100
PASS_C = (BAND_X - 0.004, -0.340, 0.982)
PASS_W, PASS_H = 0.440, 0.118

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.080, 0.520
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.020, 0.500, 0.380

DASH_HALF = 0.765                  # the dash's ends, at the door cards
MIRROR_C = (0.360, 0.000, 1.345)   # the frameless rear-view mirror, hung from the header

# linear RGB, read off the photographs' lit patches (sRGB 118-131 on the seats, 140-150 on the
# dash leather, 75-80 on the carpet)
SEAT = (0.112, 0.064, 0.058)       # mocha-brown Nappa
DASH_LEATHER = (0.185, 0.148, 0.145)   # mauve-grey leather of the dash, doors and console
DOOR_LOWER = (0.150, 0.106, 0.100)
CARPET = (0.092, 0.075, 0.078)
SUEDE = (0.150, 0.134, 0.130)      # the headliner
WOOD = (0.205, 0.150, 0.160)       # the brushed rose-bronze strips
BRONZE = (0.55, 0.36, 0.27)
FELT = (0.030, 0.031, 0.034)


def z_glass(x, y):
    """Height of the windscreen (the body's upper surface) at (x, |y|)."""
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.68)))
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
    MB.set_inputs(b, base=(0.20, 0.15, 0.13), metallic=0.0, roughness=0.55, sheen=0.3)
    lib["thread"] = m
    m, nt, b = MB.mat("INT_Carpet_Mauve")
    MB.set_inputs(b, base=CARPET, metallic=0.0, roughness=0.96, specular=0.2, sheen=0.4)
    IM._textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m
    # the brushed rose-bronze strips: a satin metal-like surface with a fine streak
    m, nt, b = MB.mat("INT_Wood_Strip")
    MB.set_inputs(b, base=WOOD, metallic=0.0, roughness=0.36, coat=0.35, coat_rough=0.18, ior=1.5)
    IM._textured(nt, b, maps["brushed"], SM.TILE["brushed"], 0.7)
    lib["wood"] = m
    m, nt, b = MB.mat("INT_Bronze")
    MB.set_inputs(b, base=BRONZE, metallic=1.0, roughness=0.22)
    lib["bronze"] = m
    m, nt, b = MB.mat("INT_Felt")                       # the wireless pad: dark grey felt
    MB.set_inputs(b, base=FELT, metallic=0.0, roughness=0.97, specular=0.2, sheen=0.6)
    IM._textured(nt, b, maps["alcantara"], SM.TILE["alcantara"], 1.0)
    lib["felt"] = m
    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.10, coat=0.5,
                  coat_rough=0.08, ior=1.5)
    lib["band_glass"] = m
    m, nt, b = MB.mat("INT_Crystal")                    # the crystal keys and selector
    MB.set_inputs(b, base=(0.55, 0.56, 0.58), metallic=0.0, roughness=0.06, coat=1.0,
                  coat_rough=0.02, ior=1.52)
    lib["crystal"] = m
    # the mirrored bronze of the key tray and the pad's frame, the clear glass of the keys
    # (c10_0043), the wheel mark's two blues (c10_0009)
    m, nt, b = MB.mat("INT_Bronze_Mirror")
    MB.set_inputs(b, base=(0.62, 0.48, 0.40), metallic=1.0, roughness=0.09)
    lib["bronze_mirror"] = m
    m, nt, b = MB.mat("INT_Key_Glass")
    MB.set_inputs(b, base=(0.26, 0.28, 0.30), metallic=0.0, roughness=0.03, coat=1.0,
                  coat_rough=0.01, ior=1.52)
    lib["key_glass"] = m
    m, nt, b = MB.mat("INT_Mark_Navy")
    MB.set_inputs(b, base=(0.010, 0.018, 0.080), metallic=0.0, roughness=0.20, coat=0.6)
    lib["mark_navy"] = m
    m, nt, b = MB.mat("INT_Mark_Blue")
    MB.set_inputs(b, base=(0.045, 0.140, 0.520), metallic=0.0, roughness=0.20, coat=0.6)
    lib["mark_blue"] = m
    m, nt, b = MB.mat("INT_Wheel_Panel")                # the control panel on the wheel's pods
    MB.set_inputs(b, base=(0.050, 0.050, 0.055), metallic=0.6, roughness=0.35)
    lib["pod_panel"] = m
    m, nt, b = MB.mat("INT_Wheel_Roller")               # the knurled roller
    MB.set_inputs(b, base=(0.12, 0.12, 0.13), metallic=1.0, roughness=0.30)
    lib["roller"] = m
    return lib


# ------------------------------------------------------------------- dash
def _hood(y):
    """1 over the driver's cluster, 0 elsewhere: the binnacle's lip stands a little farther out."""
    return 1.0 - CP.smooth((abs(y - WHEEL_Y) - 0.205) / 0.045)


# top pad height over the band, a long low shelf
Z_PAD = 1.068


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    h = _hood(y)
    zg = z_glass(0.985, y) - 0.003
    zt = Z_PAD + 0.012 * h
    bx = BAND_X
    return [
        (0.985, zg),                                 # 0 glass base
        (0.945, zt - 0.014), (0.912, zt),            # 1,2 top pad
        (bx + 0.020, zt + 0.003),                    # 3 over the band
        (bx + 0.004 - 0.012 * h, zt - 0.013),        # 4 lip, rolling under
        (bx - 0.002 - 0.012 * h, BAND_TOP),          # 5 band top
        (bx - 0.002 - 0.012 * h, BAND_BOT),          # 6 band bottom (glass 5..6)
        (bx + 0.003, BAND_BOT - 0.003),              # 7 strip top
        (bx + 0.006, BAND_BOT - 0.068),              # 8 strip bottom (strip 7..8)
        (bx + 0.010, BAND_BOT - 0.074),              # 9 chrome line
        (bx + 0.014, 0.800), (bx + 0.030, 0.720), (bx + 0.062, 0.640), (bx + 0.110, 0.560),
        (bx + 0.185, 0.470), (bx + 0.260, 0.410),    # 10.. face down to the footwell
    ]


DASH_COUNTS = [4, 3, 4, 3, 3, 4, 2, 5, 2, 3, 4, 4, 4, 4, 4]
# panels by control point: the top pad (0..4), the glass band (5..6), the strip (7..8), the face
DASH_PANELS = [("TopPad", 0, 5, "leather_dash"), ("Band", 5, 6, "band_glass"),
               ("Strip", 6, 9, "wood"), ("Face", 9, 15, "leather_dash")]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 120, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    # the chrome line under the strip, and a thin one on the lip
    p, n = sw.iso_col(sw.col(9), lift=0.0008)
    made.append(piping("int_dash_Chrome", p, col, lib["chrome"], r=0.0013, lateral=(1.0, 0.0, 0.0)))
    p, n = sw.iso_col(sw.col(4), lift=0.0006)
    made.append(piping("int_dash_Lip", p, col, lib["leather_dash"], r=0.0016, lateral=(1.0, 0.0, 0.0)))
    # the stitch along the face's upper third
    p, n = sw.iso_col(sw.col(10) + 2, int(len(sw.pts) * 0.04), int(len(sw.pts) * 0.96))
    for sd in (0.0035,):
        made.append(stitches("int_dash_Stitch", p, n, col, lib["thread"], side=sd))
    made.append(F.ngon_cap(col, "int_dash_EndL", list(sw.pts[0]), lib["leather_dash"], (0.0, 1.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndR", list(sw.pts[-1]), lib["leather_dash"], (0.0, -1.0, 0.0)))
    made += build_dash_details(col, lib, sw)
    return made, sw


def build_dash_details(col, lib, sw):
    """On the glass band: the passenger side's two air vents at its end, a vent slot above the
    console under the screen, the speaker grille on the top pad and the HUD's window."""
    made = []
    bx = BAND_X
    # the two small vents at the band's passenger end, each a dark slot with a chrome frame (c10_0004)
    for k, zc in enumerate((1.003, 0.955)):
        made.append(F.box(col, "int_dash_PVent%d" % k, (bx - 0.006, -0.680, zc), (0.012, 0.075, 0.030),
                          lib["piano"], r=0.004))
        for j in range(6):
            made.append(F.box(col, "int_dash_PVent%d_v%d" % (k, j),
                              (bx - 0.013, -0.680 + 0.026 - 0.0105 * j, zc), (0.004, 0.003, 0.024),
                              lib["gunmetal"], r=0.001))
    # the centre speaker grille on the top pad at the glass
    made += F.disc(col, "int_dash_Tweeter", (0.950, 0.0, Z_PAD - 0.006), (0.0, 0.0, 1.0), 0.032,
                   lib["speaker"], dome=0.0, rim=0.003, rim_mat=lib["chrome"])
    # the HUD's window in the top pad ahead of the driver
    made.append(F.box(col, "int_dash_HUD", (0.946, WHEEL_Y, Z_PAD - 0.008), (0.100, 0.230, 0.0016),
                      lib["screen_glass"], r=0.0008))
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b + 0.012,
                       0.020, 0.012, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())
    # the stand: a slim blade from the screen's lower middle down into the console's vent frame
    made.append(F.box(col, "int_screen_stand", (SCREEN_C[0] + 0.040, 0.0, SCREEN_C[2] - 0.160),
                      (0.040, 0.100, 0.130), lib["satin"], r=0.008))
    # the cluster: a wide strip behind the wheel; and the co-pilot display across the passenger side
    q = F.screen_quad("screen_cluster", CLUSTER_C, CLUSTER_W, CLUSTER_H, 0.0, col, lift=0.0010)
    q.data.materials.append(F.screen_material())
    made.append(q)
    q = F.screen_quad("screen_passenger", PASS_C, PASS_W, PASS_H, 0.0, col, lift=0.0010)
    q.data.materials.append(F.screen_material())
    made.append(q)
    return made


def cluster_image(path=None, w=1024, h=310):
    """The cluster's resting display, laid out as c10_0015/16 show it: dark, the speed and gear
    letter at the centre, tyre figures at the left, range at the right. Generated pixels."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.008, 0.012, 0.020)
    white = np.array([0.80, 0.84, 0.90])
    green = np.array([0.10, 0.60, 0.30])
    blue = np.array([0.08, 0.30, 0.55])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c
    s = 0.018 * h
    sx, sy = 0.47 * w, 0.20 * h
    rect(sx, sx + 3 * s, sy, sy + s * 0.5, white)
    rect(sx, sx + 3 * s, sy + 6.5 * s, sy + 7 * s, white)
    rect(sx, sx + s * 0.5, sy, sy + 7 * s, white)
    rect(sx + 2.5 * s, sx + 3 * s, sy, sy + 7 * s, white)
    gx, gy = 0.62 * w, 0.20 * h
    rect(gx, gx + s * 0.45, gy, gy + 3.4 * s, white * 0.85)
    rect(gx, gx + 2.0 * s, gy, gy + s * 0.45, white * 0.85)
    rect(gx, gx + 2.0 * s, gy + 1.5 * s, gy + 1.95 * s, white * 0.85)
    rect(gx + 1.55 * s, gx + 2.0 * s, gy, gy + 1.95 * s, white * 0.85)
    # the car in the middle, a bar of range at the bottom, four tyre figures at the left
    cx, cy = 0.50 * w, 0.62 * h
    img[(((xx - cx) / (0.035 * w)) ** 2 + ((yy - cy) / (0.20 * h)) ** 2) < 1.0] = blue
    rect(0.10 * w, 0.30 * w, 0.84 * h, 0.88 * h, green)
    for (fx, fy) in ((0.08, 0.28), (0.20, 0.28), (0.08, 0.52), (0.20, 0.52)):
        rect(fx * w, fx * w + 0.07 * w, fy * h, fy * h + 0.05 * h, white * 0.6)
    for (fx, fy) in ((0.78, 0.30), (0.78, 0.55)):
        rect(fx * w, fx * w + 0.14 * w, fy * h, fy * h + 0.05 * h, white * 0.55)
    import os
    out = path or os.path.join(TEX_DIR, "cluster_z9.png")
    return CP.image_from_pixels("T_Cluster_Z9", img, out)


def passenger_image(path=None, w=1024, h=275):
    """The co-pilot display at rest: a near-black glass with a soft blue glow and the maker's name."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.006, 0.008, 0.014)
    g = np.exp(-(((xx - 0.45 * w) / (0.22 * w)) ** 2 + ((yy - 0.62 * h) / (0.10 * h)) ** 2))
    img += g[..., None] * np.array([0.02, 0.07, 0.16], np.float32)
    out = path or os.path.join(TEX_DIR, "passenger_z9.png")
    return CP.image_from_pixels("T_Passenger_Z9", img, out)


# ---------------------------------------------------------- steering wheel
# the rim's centreline (u right, v up) traced off c10_0002 with a pixel grid: an oval 0.396 wide and
# 0.374 tall, its upper half a true ellipse and its lower half a squarer superellipse (exponent 2.45),
# so the wheel is round over the top and runs straighter along the bottom
def _z9_loop(a=0.183, b_top=0.1751, b_low=0.1757):
    pts = []
    for k in range(0, 360, 12):
        t = math.radians(k)
        c, s_ = math.cos(t), math.sin(t)
        n, b = (2.0, b_top) if s_ >= 0.0 else (2.45, b_low)
        pts.append((a * math.copysign(abs(c) ** (2.0 / n), c), b * math.copysign(abs(s_) ** (2.0 / n), s_)))
    return pts


Z9_LOOP = _z9_loop()
HUB_DV = -0.023            # the airbag pad's centre sits this far below the rim's


def _hub_outline(a=0.088, b=0.0692, n=3.2, k=56):
    """The airbag cover: a rounded square, wider along its top than its bottom (c10_0002)."""
    pts = []
    for i in range(k):
        t = 2.0 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        u = a * math.copysign(abs(c) ** (2.0 / n), c)
        v = b * math.copysign(abs(s) ** (2.0 / n), s)
        pts.append((u * (0.90 + 0.10 * v / b), v))
    return pts


DENZA_WHEEL = dict(
    radius=0.180, loop=dict(pts=Z9_LOOP),
    flat_bottom=-0.1757, flat_top=None, section=(0.0150, 0.0170),
    grip_swell=0.05,
    segments=[(0.0, 180.0, "wheel_leather"), (180.0, 360.0, "wheel_leather")],
    marker=None,
    hub=dict(w=0.170, h=0.139, sides=36, r_corner=0.0, dome=0.006, depth=0.05,
             pad_role="leather_seat", housing_role="leather_seat", outline=_hub_outline()),
)


def _wheel_pods(fr, col, lib):
    """The two side pods (c10_0009): a grey satin wedge from the hub out to the rim, tall at the hub
    and thin at the rim, a dark panel with the knurled roller toward the rim and three slot keys
    toward the hub."""
    made = []
    pitch = WHEEL_TILT
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        rows = []
        for k in range(13):
            t = k / 12.0
            u = side * (0.072 + 0.104 * t)
            hh = 0.5 * (0.057 - 0.035 * t)
            vc = -0.003 - 0.004 * t
            prof = [(-hh, -0.004), (-hh * 0.97, 0.0075), (-hh * 0.82, 0.0120), (-hh * 0.35, 0.0138),
                    (hh * 0.35, 0.0138), (hh * 0.82, 0.0120), (hh * 0.97, 0.0075), (hh, -0.004),
                    (hh * 0.8, -0.022), (-hh * 0.8, -0.022)]
            rows.append([fr.p(u, vc + a, b) for (a, b) in prof])
        ob = grid_mesh("int_wheel_pod" + tag, rows, col, lib["gunmetal"], wrap_t=True)
        M.orient(ob.data, lambda c: tuple(fr.A))
        made.append(ob)
        made.append(F.box(col, "int_wheel_panel" + tag, fr.p(side * 0.136, 0.0000, 0.0142),
                          (0.0030, 0.052, 0.027), lib["pod_panel"], r=0.0010, pitch=pitch))
        made.append(F.box(col, "int_wheel_roller" + tag, fr.p(side * 0.134, 0.0000, 0.0160),
                          (0.0036, 0.013, 0.017), lib["roller"], r=0.0012, pitch=pitch))
        for j, vk in enumerate((0.0070, -0.0040, -0.0150)):
            made.append(F.box(col, "int_wheel_slot%s%d" % (tag, j), fr.p(side * 0.100, vk, 0.0146),
                              (0.0030, 0.0170, 0.0050), lib["piano"], r=0.0008, pitch=pitch))
    return made


def _wheel_legs(fr, col, lib):
    """The two legs from under the pods down to the rim's lower corners (c10_0002): a grey satin
    bar with a chrome edge on the hub side, leaning outward as it descends."""
    made = []
    pts = [(0.080, -0.036, 0.007), (0.096, -0.090, 0.006), (0.115, -0.138, 0.004)]
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        leg = smooth_path([fr.p(side * u, v, w) for (u, v, w) in pts], 14)
        made.append(tube("int_wheel_leg" + tag, leg, ellipse(0.0070, 0.0125, 12), col, lib["gunmetal"],
                         lateral=tuple(fr.A)))
        edge = smooth_path([fr.p(side * (u - 0.0125), v, w + 0.0035) for (u, v, w) in pts], 14)
        made.append(tube("int_wheel_legedge" + tag, edge, ellipse(0.0030, 0.0032, 8), col, lib["chrome"],
                         lateral=tuple(fr.A)))
    return made


def _rim_inlay(fr, col, lib):
    """A thin chrome line down the rim's inner face from each pod to its leg (c10_0002)."""
    made = []
    loop = smooth_path([(u, v, 0.0) for (u, v) in Z9_LOOP], 192, closed=True)
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        pts = sorted([p for p in loop if side * p[0] > 0.0 and -0.138 < p[1] < -0.024],
                     key=lambda p: -p[1])
        if len(pts) < 4:
            continue
        path = []
        for (x, y, _) in pts:
            k = 1.0 - 0.0146 / math.hypot(x, y)
            path.append(fr.p(x * k, y * k, 0.0))
        made.append(tube("int_wheel_inlay" + tag, path, ellipse(0.0030, 0.0020, 8), col, lib["chrome"],
                         lateral=tuple(fr.A)))
    return made


def _wheel_mark(frh, col, lib):
    """The maker's mark on the pad (c10_0009): a silver disc in a chrome ring with a navy and blue
    hourglass, and the pad's stitched seam."""
    made = []
    lift = 0.0262
    c = (0.0, 0.018)
    made += F.disc(col, "int_wheel_mark", frh.p(c[0], c[1], lift), tuple(frh.A), 0.029, lib["brushed"],
                   dome=0.0, rim=0.0021, rim_mat=lib["chrome"])

    def tri(name, uv, mat):
        verts = [frh.p(u, v, lift + 0.0006) for (u, v) in uv]
        ob = M.obj(name, verts, [[0, 1, 2]], col, mat, smooth=False)
        M.orient(ob.data, lambda q: tuple(frh.A))
        return ob
    made.append(tri("int_wheel_mark_top", [(-0.0125, 0.0335), (0.0125, 0.0335), (0.0, 0.0185)],
                    lib["mark_navy"]))
    made.append(tri("int_wheel_mark_bot", [(0.0, 0.0175), (-0.0165, 0.0010), (0.0165, 0.0010)],
                    lib["mark_blue"]))
    seam = [frh.p(u * 0.92, v * 0.92, 0.0219) for (u, v) in _hub_outline()]
    seam.append(seam[0])
    made.append(tube("int_wheel_seam", seam, ellipse(0.0008, 0.0008, 6), col, lib["thread"],
                     lateral=tuple(frh.A)))
    return made


def build_wheel(col, lib):
    from carkit.interior import steering as ST
    fr = ST.WheelFrame(WHEEL_C, WHEEL_TILT)
    frh = ST.WheelFrame(tuple(Vector(WHEEL_C) + fr.V * HUB_DV), WHEEL_TILT)
    made = ST.rim(fr, DENZA_WHEEL, col, lib)
    made += ST.hub(frh, DENZA_WHEEL, col, lib)
    made += _wheel_pods(fr, col, lib)
    made += _wheel_legs(fr, col, lib)
    made += _rim_inlay(fr, col, lib)
    made += ST.column(fr, col, lib)
    made += _wheel_mark(frh, col, lib)
    return made


# ------------------------------------------------------------------ seats
def _seat_spec(k=1.0):
    """The front bucket (the SU7's, carkit.interior.seat) in mocha Nappa: deep cushion, tall
    backrest, a separate headrest pillow on two posts (c3_0001, c3_0036). `k` scales the backrest's
    height: 1.0 is the spine as drawn from the SU7; the front seats use FRONT_BACK_K."""
    from carkit.interior import seat as SE
    import copy
    sp = copy.deepcopy(SE.SU7_ULTRA_FRONT)
    base = [(0.0, 0.0), (-0.045, 0.0957), (-0.13, 0.286), (-0.20, 0.4576),
            (-0.240, 0.556), (-0.272, 0.640), (-0.288, 0.676), (-0.294, 0.694), (-0.297, 0.700)]
    sp["backrest"]["spine"] = [(x * k, z * k) for (x, z) in base]
    sp["backrest"]["end_cap"] = True        # the spine stops at the shoulders; a dome closes the open tube
    sp["backrest"]["half_w"] = Curve([(0.0, 0.262), (0.45, 0.272), (0.78, 0.262), (0.90, 0.244),
                                      (1.0, 0.200)], mode="pchip")
    sp["backrest"]["bolster"] = Curve([(0.0, 0.55), (0.30, 1.0), (0.58, 0.75), (0.80, 0.35),
                                       (1.0, 0.0)], mode="pchip")
    sp["backrest"]["centre_half"] = Curve([(0.0, 0.135), (0.8, 0.130), (1.0, 0.100)], mode="pchip")
    sp["cushion"]["bolster_h"] = 0.046
    sp["backrest"]["bolster_h"] = 0.080
    sp["mats"] = dict(centre="leather_seat", crown="leather_seat", face="leather_seat",
                      shell="leather_seat", piping="leather_seat", stitch="thread",
                      base="leather_seat")
    sp["stitch_half_gap"] = 0.012
    sp["headrest"] = dict(w=0.318, h=0.235, t=0.098, r=0.058, gap=0.045, top=(-0.297 * k, 0.700 * k))
    return sp


# the backrest's height against the SU7-drawn spine. The Z9's roof is only 1.50 m high, so at 1.0 the front headrests'
# tops (z 1.503) stood through the glass roof (1.496) and the side headliner (1.456), and the rear ones (the spine drawn
# 12 % shorter, z 1.335) 4 cm through the sloping rear headliner (1.306). 0.86 puts the front headrest's top at z 1.405,
# 0.885 m above the bight like the 7X's, 5 cm under the side headliner and 9 cm under the glass; 0.76 puts the rear's at
# z 1.251, 4 cm under the headliner (the rear photographs, c3_0016/0017, show a short back and a small headrest).
FRONT_BACK_K = 0.86
REAR_BACK_K = 0.76


def _rear_spec():
    """The rear seats: the front seat as drawn, backrest shortened to REAR_BACK_K (24 %), the headrest a smaller pillow."""
    import copy
    sp = copy.deepcopy(_seat_spec(1.0))
    sp["backrest"]["spine"] = [(x * 1.02, z * REAR_BACK_K) for (x, z) in sp["backrest"]["spine"]]
    hr = sp["headrest"]
    sp["headrest"] = dict(w=0.285, h=0.175, t=0.086, r=0.050, gap=0.040,
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
    # the centre rear place: a narrow cushion between the two, its backrest folded to an armrest
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.22, 0.0, REAR_BIGHT_Z - 0.035),
                      (0.50, 0.30, 0.12), lib["leather_seat"], r=0.035))
    made.append(F.box(col, "int_rear_centre_back", (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.25),
                      (0.14, 0.28, 0.50), lib["leather_seat"], r=0.04, pitch=math.radians(-18)))
    made.append(CP.pillow(col, "int_rear_centre_head",
                          (REAR_BIGHT_X - 0.19 - 0.04, 0.0, REAR_BIGHT_Z + 0.56), 0.24, 0.16, 0.080,
                          0.046, lib["leather_seat"], -math.radians(18)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.18, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.62, 1.30, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["leather_seat"], r=0.02))
    return made


# ---------------------------------------------------------------- console
# Top centreline height, rear to front: the armrest, the step down to the cup holders, the felt pad
# deck, the key row and the vent frame under the screen (c10_0043-48).
CONSOLE_TOP = Curve([
    (-0.235, 0.700), (-0.222, 0.740), (-0.205, 0.756), (-0.170, 0.762), (0.060, 0.764),
    (0.150, 0.760), (0.185, 0.745), (0.215, 0.705), (0.250, 0.696), (0.430, 0.696),
    (0.470, 0.700), (0.495, 0.722), (0.515, 0.742), (0.560, 0.748), (0.700, 0.750),
    (0.748, 0.757), (0.764, 0.771), (0.780, 0.7745), (0.800, 0.7755), (0.806, 0.800),
    (0.811, 0.860),
], mode="pchip")
CONSOLE_HW = 0.112
CONSOLE_X0, CONSOLE_X1 = -0.235, 0.811
Z_TRAY = 0.7765                    # the key tray's top, a step above the felt deck (c10_0043)


def _console_stations():
    xs = []
    x = CONSOLE_X0
    while x < CONSOLE_X1:
        xs.append(x)
        dense = (x < -0.19) or (0.17 < x < 0.26) or (0.45 < x < 0.53) or (0.74 < x < 0.82)
        x += 0.004 if dense else 0.014
    xs.append(CONSOLE_X1)
    return xs


def _console_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = CONSOLE_HW, 0.020
    pts = [(-hw, FLOOR_Z), (-hw, zt - 0.10), (-hw, zt - r)]
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
    pts += [(hw, zt - r), (hw, zt - 0.10), (hw, FLOOR_Z)]
    return pts


KEY_Y = [0.0857, 0.0612, 0.0367, 0.0122, -0.0122, -0.0367, -0.0612, -0.0857]


def _kp(c, p, s, t, n):
    """A point on a pitched key: centre c, pitch p (F.box's), s along the key's length, t across,
    n out of its face."""
    cp, sp = math.cos(p), math.sin(p)
    return (c[0] + s * cp + n * sp, c[1] + t, c[2] - s * sp + n * cp)


def _console_controls(col, lib):
    """What sits under the screen (c10_0043, c10_0047): a black gloss bezel round a bronze mirror
    tray with eight keys, three crystal rockers either side of the start/stop and hazard blocks, and
    above it the vent chamber, a deep recess with vertical louvers and one slat, a bronze lip."""
    made = []
    made.append(F.box(col, "int_console_bezel", (0.783, 0.0, Z_TRAY - 0.0035), (0.058, 0.212, 0.007),
                      lib["piano"], r=0.0025))
    made.append(F.box(col, "int_console_tray", (0.7845, 0.0, Z_TRAY + 0.0008), (0.036, 0.198, 0.0020),
                      lib["bronze_mirror"], r=0.0005))
    zt = Z_TRAY + 0.0018
    for j, y in enumerate(KEY_Y):
        if j in (3, 4):
            # the start/stop and hazard keys: a clear block with a dark plate on its face
            c, p, h = (0.7835, y, zt + 0.0048), -0.25, 0.0095
            made.append(F.box(col, "int_console_key%d" % j, c, (0.0185, 0.0205, h), lib["key_glass"],
                              r=0.0015, pitch=p))
            made.append(F.box(col, "int_console_plate%d" % j, _kp(c, p, 0.0, 0.0, h / 2 + 0.0006),
                              (0.0145, 0.0165, 0.0012), lib["piano"], r=0.0003, pitch=p))
            if j == 4:
                verts = [_kp(c, p, s, t, h / 2 + 0.0014) for (s, t) in
                         ((0.0040, 0.0), (-0.0030, 0.0046), (-0.0030, -0.0046))]
                tri = M.obj("int_console_hazard", verts, [[0, 1, 2]], col, lib["button_red"], smooth=False)
                M.orient(tri.data, lambda q: (math.sin(p), 0.0, math.cos(p)))
                made.append(tri)
            else:
                ring = [_kp(c, p, 0.0050 * math.cos(2 * math.pi * k / 20), 0.0050 * math.sin(2 * math.pi * k / 20),
                            h / 2 + 0.0014) for k in range(21)]
                made.append(tube("int_console_start", ring, ellipse(0.0004, 0.0004, 6), col, lib["crystal"],
                                 lateral=(math.sin(p), 0.0, math.cos(p))))
        else:
            # a crystal rocker: a clear bar on a mirrored wedge that faces the driver
            made.append(F.box(col, "int_console_base%d" % j, (0.7803, y, zt + 0.0042), (0.0120, 0.0205, 0.0090),
                              lib["bronze_mirror"], r=0.0015, pitch=-0.30))
            made.append(F.box(col, "int_console_key%d" % j, (0.7870, y, zt + 0.0075), (0.0100, 0.0190, 0.0070),
                              lib["key_glass"], r=0.0030, pitch=-0.30))
    # the vent chamber: a black gloss box with a dark recess, louvers and a slat
    xv, zc = 0.7955, 0.834
    made.append(F.box(col, "int_console_vent", (xv + 0.0090, 0.0, zc), (0.016, 0.214, 0.062), lib["piano"],
                      r=0.004))
    made.append(F.box(col, "int_console_ventback", (xv, 0.0, zc), (0.0030, 0.198, 0.042), lib["satin"],
                      r=0.0008))
    for j in range(11):
        made.append(F.box(col, "int_console_fin%d" % j, (xv - 0.0040, 0.0880 - 0.0176 * j, zc),
                          (0.0075, 0.0022, 0.040), lib["gunmetal"], r=0.0006))
    made.append(F.box(col, "int_console_slat", (xv - 0.0035, 0.0, zc), (0.0060, 0.196, 0.0035),
                      lib["gunmetal"], r=0.0006))
    lip = [(xv - 0.0010, y, z) for (y, z) in F.round_rect_xy(-0.104, 0.104, zc - 0.023, zc + 0.023, 0.008)]
    lip.append(lip[0])
    made.append(tube("int_console_ventlip", lip, ellipse(0.0014, 0.0014, 6), col, lib["bronze_mirror"],
                     lateral=(1.0, 0.0, 0.0)))
    return made


def build_console(col, lib):
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _console_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_dash"])
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.70)))
    made.append(ob)
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in
                                                      _console_section(xs[0])],
                           lib["leather_dash"], (-1.0, 0.0, 0.0)))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.0015 * (1.0 - (y / (CONSOLE_HW - 0.020)) ** 2) + lift)

    # the felt pad's deck with its bronze frame, and the bronze pen across it (c10_0045)
    outer = F.round_rect_xy(0.508, 0.760, -0.098, 0.098, 0.018)
    frame = [top(x, y, 0.0014) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0014)]
    made.append(tube("int_console_frame", frame, ellipse(0.0030, 0.0026, 8), col, lib["bronze_mirror"],
                     lateral=(0.0, 0.0, 1.0)))
    # the felt is a grid that follows the deck (a flat fan sank into the curved leather)
    made.append(F.plate_with_hole("int_console_pad", F.round_rect_xy(0.510, 0.758, -0.096, 0.096, 0.016),
                                  [], lambda x, y: top(x, y, 0.0007)[2], col, lib["felt"], nx=62, ny=40))
    pen = [top(0.560 + 0.160 * t / 6.0, -0.002 + 0.004 * t / 6.0, 0.0040) for t in range(7)]
    made.append(tube("int_console_pen", pen, ellipse(0.0035, 0.0035, 8), col, lib["bronze_mirror"],
                     lateral=(0.0, 1.0, 0.0)))
    made += _console_controls(col, lib)
    # the cup holders: two round recesses in a chrome-edged deck (c10_0044)
    for k, yc in enumerate((0.058, -0.058)):
        ring = [top(0.330 + 0.046 * math.cos(2 * math.pi * j / 28), yc + 0.046 * math.sin(2 * math.pi * j / 28),
                    0.0016) for j in range(29)]
        made.append(tube("int_console_cup%d" % k, ring, ellipse(0.0024, 0.0024, 8), col, lib["chrome"],
                         lateral=(0.0, 0.0, 1.0)))
        made += F.disc(col, "int_console_cupwell%d" % k, top(0.330, yc, -0.006), (0.0, 0.0, 1.0), 0.043,
                       lib["rubber"], rim=None)
    # the chrome edge lines down both sides of the tower (c10_0045: they sweep down the flanks)
    for sd in (1.0, -1.0):
        line = [(x, sd * (CONSOLE_HW - 0.006), CONSOLE_TOP(x) - 0.030) for x in
                [CONSOLE_X0 + 0.04 + (CONSOLE_X1 - CONSOLE_X0 - 0.08) * t / 40.0 for t in range(41)]]
        made.append(tube("int_console_edge%s" % ("L" if sd > 0 else "R"), line,
                         ellipse(0.0016, 0.0016, 6), col, lib["bronze_mirror"], lateral=(0.0, 1.0, 0.0)))
    # the armrest lid's seam and the dark frame round it
    frame = [top(x, y, 0.0012) for (x, y) in F.round_rect_xy(-0.218, 0.150, -0.104, 0.104, 0.030)]
    frame.append(frame[0])
    made.append(tube("int_console_lid_frame", frame, ellipse(0.0016, 0.0016, 6), col, lib["thread"],
                     lateral=(0.0, 0.0, 1.0)))
    return made
