"""BYD Seal cabin (the 2025 Seal in Sardine Coral Orange, 沙丁瑚橙): hardpoints, materials, the dash
and its screens. The wheel, seats and console live in seal_wheel / seal_seats / seal_console and the
door cards in seal_interior_doors; seal_interior_shell assembles them.

Read from Autohome series 6394's interior photographs (blender/reference/byd-seal-ev/interior/full:
d0126 straight down the cabin, d0127 the driver's view, d0069 the wheel, d0108 the dash from the
passenger side, c0086-c0095 the open door) and positioned through the solved overhead camera
(seal_cabinsolve: both A-pillars' glass edges and the screen's outer frame).

What the photographs show:
    dash        a long, deep dark top pad; under it ONE wide glossy-black glass band from door to door
                (the cluster sits in its driver end, the passenger end is blank); under the band a
                fat orange leather shelf that runs into both door cards; under that a charcoal lower
                dash with the glovebox on the passenger side and ribbon vents at the band's ends
    screen      15.6 in (2560 x 1440) rotating centre screen floating ahead of the shelf, its frame
                0.352 x 0.225 m, nearly upright
    cluster     10.25 in (1920 x 720), 0.244 x 0.092 m, in the band behind the wheel
    wheel       seal_wheel
    seats       seal_seats
    console     seal_console: a black bridge with orange flanks

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
DRIVER_Y = 0.360
PASS_Y = -0.360

# 15.6 in centre screen: active area 16:10 (the web HMI is 1280 x 800), frame 7 mm round it
SCREEN_W, SCREEN_H = 0.338, 0.211
SCREEN_C = (0.530, 0.000, 0.930)
SCREEN_TILT = math.radians(3.0)
SCREEN_BORDER = 0.007

WHEEL_Y = 0.392
WHEEL_C = (0.457, WHEEL_Y, 0.929)
WHEEL_TILT = math.radians(25.0)

# the 10.25 in cluster, flush in the band's face
CLUSTER_W, CLUSTER_H = 0.244, 0.092
CLUSTER_TILT = math.radians(28.0)

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.030, 0.510
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -0.960, 0.490, 0.360

DASH_HALF = 0.745                  # the dash runs door to door
MIRROR_C = (0.340, 0.000, 1.330)   # frameless rear-view mirror

# linear RGB
ORANGE_HEX = "#C8623A"
THREAD_HEX = "#E27C55"


def _lin(hexs):
    h = hexs.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


ORANGE = _lin(ORANGE_HEX)
THREAD = _lin(THREAD_HEX)
CARPET = (0.030, 0.031, 0.034)
SUEDE = (0.034, 0.034, 0.038)          # dark grey headliner cloth
CHARCOAL = (0.020, 0.020, 0.023)       # soft-touch lower dash and trim
GRAPHITE = (0.060, 0.058, 0.058)


def z_glass(x, y):
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.65)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
PERF_TILE = 0.070          # one tile of the hole field: 16 holes across, a 4.4 mm pitch


def _perf_images():
    """A tileable hex field of round holes: a normal map and a darkening mask (16 holes across, 18 rows, so
    both axes repeat without a seam)."""
    import numpy as np
    from carkit import surfacemaps as SM
    size, cols, rows, radius = 512, 16, 18, 0.22
    pitch, rh = size / float(cols), size / float(rows)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / rh)
    cx = (xx + (row % 2) * pitch * 0.5) % pitch - pitch * 0.5
    cy = (yy % rh) - rh * 0.5
    d = np.sqrt(cx * cx + (cy * pitch / rh) ** 2) / pitch
    hole = np.clip((radius - d) / 0.05, 0.0, 1.0)
    nrm = SM._image("T_Perf_Normal", SM.height_to_normal(-hole, 10.0 / size * 60.0))
    mask = np.repeat((1.0 - 0.70 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_Perf_Mask", mask, non_color=False, filename="t_perf_mask.png")
    return nrm, msk


def _perf_normal(nt, bsdf, img, tile, rot_deg=0.0, strength=1.0):
    """The hole field as a normal map on the BSDF, its mapping rotated rot_deg about the surface normal."""
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    k = 1.0 / tile
    mp.inputs["Scale"].default_value = (k, k, k)
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rot_deg))
    nt.links.new(coord.outputs["UV"], mp.inputs["Vector"])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mp


def _perforated(name, color, maps):
    from carkit import surfacemaps as SM
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.44, specular=0.5, coat=0.10, coat_rough=0.25,
                  ior=1.45)
    mp = _perf_normal(nt, b, maps["perf_n"], PERF_TILE, 0.0, 1.0)
    try:
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = maps["perf_m"]
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = (color[0], color[1], color[2], 1.0)
        nt.links.new(tex.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    except Exception as e:
        print("perforation mask skipped:", e)
    return m


def build_library():
    from carkit import surfacemaps as SM
    from carkit import textures
    maps = SM.build_all()
    maps["perf_n"], maps["perf_m"] = _perf_images()
    lib = IM.build_library(accent=ORANGE, maps=maps)
    # the three trim slots the showroom recolours by name (byd-seal.ts trims)
    lib["leather_seat"] = IM.leather("INT_Leather_Seat", ORANGE, maps, roughness=0.44, coat=0.10)
    lib["leather_door"] = IM.leather("INT_Leather_Door", ORANGE, maps, roughness=0.47, coat=0.08)
    lib["leather_accent"] = lib["leather_seat"]
    lib["wheel_leather"] = lib["leather_door"]
    # perforated panel: the same orange with a hex field of holes pressed in (normal) and darkened (a
    # multiply mask on the colour, which the showroom's trim recolouring keeps: colour factor x texture)
    lib["leather_perf"] = _perforated("INT_Leather_Perf", ORANGE, maps)
    m, nt, b = MB.mat("INT_Thread_Seat")
    MB.set_inputs(b, base=THREAD, metallic=0.0, roughness=0.55, sheen=0.3)
    lib["thread"] = m
    lib["thread_seat"] = m
    m, nt, b = MB.mat("INT_Thread_Light")             # light grey stitching on the black parts
    MB.set_inputs(b, base=(0.36, 0.36, 0.37), metallic=0.0, roughness=0.55, sheen=0.2)
    lib["thread_light"] = m

    lib["headliner"] = IM.alcantara("INT_Headliner", SUEDE, maps, sheen=0.5)
    m, nt, b = MB.mat("INT_Suede_Grey")               # the wireless charger's grey felt
    MB.set_inputs(b, base=(0.20, 0.205, 0.215), metallic=0.0, roughness=0.97, specular=0.2, sheen=0.6)
    IM._textured(nt, b, maps["alcantara"], SM.TILE["alcantara"], 1.0)
    lib["suede"] = m

    m, nt, b = MB.mat("INT_Carpet_Dark")
    MB.set_inputs(b, base=CARPET, metallic=0.0, roughness=0.96, specular=0.2, sheen=0.4)
    IM._textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m

    m, nt, b = MB.mat("INT_Soft_Touch")               # matte moulded plastic: the dash top and lower dash
    MB.set_inputs(b, base=CHARCOAL, metallic=0.0, roughness=0.62, specular=0.35, sheen=0.25)
    IM._textured(nt, b, maps["alcantara"], SM.TILE["alcantara"], 0.6)
    lib["soft"] = m

    m, nt, b = MB.mat("INT_Band_Glass")               # the dash's black glass band
    MB.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.05, coat=1.0,
                  coat_rough=0.02, ior=1.52)
    lib["band_glass"] = m

    m, nt, b = MB.mat("INT_Plastic_Grey")               # the console's moulded dark-grey plastic
    MB.set_inputs(b, base=(0.046, 0.045, 0.046), metallic=0.15, roughness=0.50, specular=0.4, sheen=0.1)
    lib["plastic"] = m

    m, nt, b = MB.mat("INT_Graphite")                  # steering-wheel spokes, console frame
    MB.set_inputs(b, base=GRAPHITE, metallic=0.7, roughness=0.38)
    lib["graphite"] = m

    m, nt, b = MB.mat("INT_Carbon")                    # the door cards' gloss lattice trim
    MB.set_inputs(b, base=(0.021, 0.021, 0.023), metallic=0.0, roughness=0.26, coat=1.0,
                  coat_rough=0.07, ior=1.5)
    try:
        textures.apply_carbon(m, uv_scale=34.0)
    except Exception as e:
        print("carbon weave skipped:", e)
    lib["carbon"] = m

    m, nt, b = MB.mat("INT_Crystal")                   # the gear selector's glass
    MB.set_inputs(b, base=(0.012, 0.012, 0.014), metallic=0.0, roughness=0.04, coat=1.0,
                  coat_rough=0.02, ior=1.55)
    lib["crystal"] = m

    m, nt, b = MB.mat("INT_Logo_Silver")
    MB.set_inputs(b, base=(0.80, 0.81, 0.83), metallic=1.0, roughness=0.18)
    lib["logo_chrome"] = m
    lib["mark_navy"] = m
    lib["mark_blue"] = m

    m, nt, b = MB.mat("INT_Key_Black")                 # switch caps
    MB.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.34, coat=0.5,
                  coat_rough=0.1)
    lib["key"] = m
    m, nt, b = MB.mat("INT_Key_Knurl")                 # the steering roller and console rollers
    MB.set_inputs(b, base=(0.10, 0.10, 0.11), metallic=1.0, roughness=0.30)
    lib["knurl"] = m
    m, nt, b = MB.mat("INT_Mesh_Speaker")              # the door speakers' diamond mesh
    MB.set_inputs(b, base=(0.014, 0.014, 0.016), metallic=0.7, roughness=0.38)
    _perf_normal(nt, b, maps["perf_n"], 0.050, 45.0, 1.0)
    lib["mesh"] = m
    m, nt, b = MB.mat("INT_Perf_Dot")                  # the perforations' shadow, as dots on the seats
    MB.set_inputs(b, base=(0.060, 0.016, 0.008), metallic=0.0, roughness=0.8)
    lib["perf_dot"] = m
    return lib


# ------------------------------------------------------------------- dash
X_BASE = 1.040


def _wrap(y):
    """The face curls back toward the doors at both ends."""
    return -0.050 * CP.smooth((abs(y) - 0.42) / 0.30)


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    w = _wrap(y)
    zg = z_glass(X_BASE, y) - 0.010
    return [
        (X_BASE, zg),                              # 0 glass base, tucked under the cowl
        (0.930 + 0.3 * w, max(0.987, z_glass(0.930 + 0.3 * w, y) - 0.004)),   # 1 top pad, up to the skin at the ends
        (0.800 + 0.7 * w, 1.002),                  # 2 crest
        (0.745 + w, 1.008),                        # 3 band's top rim
        (0.727 + w, 1.003),                        # 4 rim, rolled over
        (0.682 + w, 0.918),                        # 5 band's lower edge
        (0.668 + w, 0.906),                        # 6 dark lip (the ambient strip)
        (0.650 + w, 0.898),                        # 7 under the shelf's rear
        (0.632 + w, 0.893),                        # 8 shelf top
        (0.614 + w, 0.880),                        # 9
        (0.607 + w, 0.858),                        # 10 shelf front
        (0.610 + w, 0.828),                        # 11 rounded under
        (0.622 + w, 0.800),                        # 12 lower dash face
        (0.624 + w, 0.700),
        (0.645 + w, 0.600),
        (0.700 + w, 0.500),
        (0.790 + w, 0.400),                        # 16 knee, down to the footwell
    ]


DASH_COUNTS = [6, 5, 3, 2, 5, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
DASH_PANELS = [("TopPad", 0, 4, "soft"), ("Band", 4, 6, "band_glass"), ("Lip", 6, 7, "soft"),
               ("Under", 7, 8, "soft"), ("Shelf", 8, 12, "leather_door"), ("Lower", 12, 16, "soft")]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 150, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    n = len(sw.pts)
    # ambient light guide in the lip under the band, a fine silver line on its rim
    p, nrm = sw.iso_col(sw.col(6), int(n * 0.03), int(n * 0.97), lift=0.0010)
    made.append(piping("int_dash_Ambient", p, col, lib["ambient"], r=0.0016, lateral=(1.0, 0.0, 0.0)))
    p, nrm = sw.iso_col(sw.col(4), int(n * 0.02), int(n * 0.98), lift=0.0006)
    made.append(piping("int_dash_Rim", p, col, lib["gunmetal"], r=0.0012, lateral=(1.0, 0.0, 0.0)))
    # the shelf's seam, a fine stitch under its front edge
    p, nrm = sw.iso_col(sw.col(11), int(n * 0.04), int(n * 0.96))
    made.append(stitches("int_dash_Stitch", p, nrm, col, lib["thread"], side=0.0))
    made.append(F.ngon_cap(col, "int_dash_EndL", list(sw.pts[0]), lib["soft"], (0.0, 1.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndR", list(sw.pts[-1]), lib["soft"], (0.0, -1.0, 0.0)))
    made += build_dash_details(col, lib, sw)
    return made, sw


def _face_point(sw, y, ctrl_a, ctrl_b, t, lift=0.0):
    """A point on the sweep between two section control points at lateral y."""
    s = (DASH_HALF - y) / (2.0 * DASH_HALF)
    i = max(0, min(len(sw.pts) - 1, int(round(s * (len(sw.pts) - 1)))))
    j = int(round(sw.col(ctrl_a) + (sw.col(ctrl_b) - sw.col(ctrl_a)) * t))
    p = Vector(sw.pts[i][j])
    return p + sw.normal(i, j) * lift, sw.normal(i, j)


def build_dash_details(col, lib, sw):
    made = []
    # ribbon vents at the band's two ends: fine slats in a slot under the lip
    for k, yc in enumerate((0.640, -0.640)):
        for j in range(9):
            y = yc + 0.060 * (j - 4) / 4.0
            p, nn = _face_point(sw, y, 7, 8, 0.0, lift=0.0)
            made.append(F.box(col, "int_dash_Slat%d_%d" % (k, j), (p.x - 0.004, y, p.z + 0.001),
                              (0.014, 0.0028, 0.016), lib["satin"], r=0.0006))
    # window-demist vents on the pad beside each A-pillar
    for k, yc in enumerate((0.640, -0.640)):
        x0 = 0.960
        zc = z_glass(x0, yc) - 0.065
        made.append(F.box(col, "int_dash_Demist%d" % k, (x0, yc, 0.978), (0.050, 0.070, 0.006),
                          lib["satin"], r=0.004))
        for j in range(4):
            made.append(F.box(col, "int_dash_Demist%d_s%d" % (k, j),
                              (x0 + 0.004, yc + 0.020 - 0.0135 * j, 0.9835), (0.030, 0.0016, 0.003),
                              lib["gunmetal"], r=0.0004))
    # glovebox lid on the passenger side of the lower dash: a shut line and a recessed pull
    made += _glovebox(col, lib, sw)
    return made


def _glovebox(col, lib, sw):
    made = []
    # outline of the lid on the lower face (x from the section: ~0.623 over z 0.60..0.78)
    ys = [-0.100 - 0.540 * k / 24.0 for k in range(25)]
    top = [(0.6225 + _wrap(y), y, 0.780) for y in ys]
    bot = [(0.6285 + _wrap(y), y, 0.605) for y in ys]
    loop = top + [(0.6225 + _wrap(-0.640), -0.640, 0.780 - (0.780 - 0.605) * k / 8.0)
                  for k in range(1, 8)] + bot[::-1] + \
        [(0.6225 + _wrap(-0.100), -0.100, 0.605 + (0.780 - 0.605) * k / 8.0) for k in range(1, 8)]
    loop.append(loop[0])
    made.append(tube("int_dash_GloveLine", loop, ellipse(0.0009, 0.0009, 6), col, lib["satin"],
                     lateral=(1.0, 0.0, 0.0)))
    # the pull: a recess with a thin lip under the lid's top edge
    made.append(F.box(col, "int_dash_GlovePull", (0.620, -0.300, 0.752), (0.012, 0.150, 0.016),
                      lib["key"], r=0.005))
    made.append(F.box(col, "int_dash_GlovePullLip", (0.617, -0.300, 0.7435), (0.006, 0.150, 0.0025),
                      lib["gunmetal"], r=0.0012))
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    # 15.6 in centre screen: frame slab, glass quad (screen_main is the web HMI's anchor), swivel arm
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b, 0.016, 0.010,
                       SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())
    # the arm that carries it up from the shelf
    made.append(F.box(col, "int_screen_stand", (SCREEN_C[0] + 0.045, 0.0, SCREEN_C[2] - 0.130),
                      (0.060, 0.100, 0.100), lib["soft"], r=0.010))
    made.append(F.box(col, "int_screen_neck", (SCREEN_C[0] + 0.016, 0.0, SCREEN_C[2] - 0.108),
                      (0.020, 0.150, 0.026), lib["satin"], r=0.008))

    # the cluster: a quad flush in the band's face (screen_cluster takes the cluster image)
    cx, cy, cz = _cluster_centre()
    q = F.screen_quad("screen_cluster", (cx, WHEEL_Y, cz), CLUSTER_W, CLUSTER_H, CLUSTER_TILT, col,
                      lift=0.0012)
    q.data.materials.append(F.screen_material())
    made.append(q)
    return made


def _cluster_centre():
    """The band face runs from (0.727, 1.003) to (0.682, 0.918): the cluster sits on it at z 0.953."""
    z = 0.953
    x = 0.682 + (z - 0.918) / (1.003 - 0.918) * (0.727 - 0.682)
    return x, WHEEL_Y, z


def cluster_image(path=None, w=1536, h=576):
    """The Seal's cluster at rest (light theme, as in the photographs): the top status line with the
    speed and gear, tyre pressures to the left of a car on pale road, a media tile to the right."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sky = np.array([0.82, 0.90, 0.95], np.float32)
    ground = np.array([0.92, 0.95, 0.98], np.float32)
    t = np.clip(yy / h, 0, 1)[..., None]
    img = sky * (1.0 - t) + ground * t
    ink = np.array([0.14, 0.18, 0.24], np.float32)
    ice = np.array([0.55, 0.72, 0.86], np.float32)
    red = np.array([0.82, 0.18, 0.18], np.float32)

    def rect(x0, x1, y0, y1, c, a=1.0):
        m = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
        img[m] = img[m] * (1 - a) + np.asarray(c, np.float32) * a

    def disc(cx, cy, rx, ry, c, a=1.0):
        m = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) < 1.0
        img[m] = img[m] * (1 - a) + np.asarray(c, np.float32) * a

    # top status strip
    rect(0, w, 0, 0.11 * h, (1, 1, 1), 0.35)
    # speed: a hollow "0" and unit
    s = 0.020 * h
    cx, cy = 0.50 * w, 0.20 * h
    disc(cx, cy, 0.016 * w, 0.075 * h, ink)
    disc(cx, cy, 0.009 * w, 0.050 * h, (0.90, 0.95, 0.98))
    rect(cx - 0.02 * w, cx + 0.02 * w, 0.30 * h, 0.305 * h, ink, 0.5)
    # gear P
    rect(0.62 * w, 0.625 * w, 0.14 * h, 0.27 * h, ink)
    rect(0.62 * w, 0.64 * w, 0.14 * h, 0.155 * h, ink)
    rect(0.62 * w, 0.64 * w, 0.20 * h, 0.215 * h, ink)
    rect(0.635 * w, 0.64 * w, 0.14 * h, 0.215 * h, ink)
    # tyre pressure car (top view) with four labels
    disc(0.17 * w, 0.52 * h, 0.040 * w, 0.20 * h, ice, 0.9)
    for (fx, fy) in ((0.115, 0.38), (0.115, 0.68), (0.225, 0.38), (0.225, 0.68)):
        rect(fx * w, fx * w + 0.05 * w, fy * h, fy * h + 0.04 * h, ink, 0.45)
    # the road and the car ahead
    disc(0.50 * w, 0.78 * h, 0.12 * w, 0.045 * h, (1, 1, 1), 0.55)
    disc(0.50 * w, 0.70 * h, 0.045 * w, 0.085 * h, (0.96, 0.96, 0.98))
    rect(0.468 * w, 0.532 * w, 0.76 * h, 0.775 * h, red, 0.8)
    for (fx, fy, ww) in ((0.40, 0.58, 0.026), (0.60, 0.50, 0.03), (0.66, 0.60, 0.034)):
        disc(fx * w, fy * h, ww * w, 0.04 * h, (0.70, 0.55, 0.50), 0.8)
    # media tile
    rect(0.80 * w, 0.93 * w, 0.40 * h, 0.72 * h, (1, 1, 1), 0.7)
    disc(0.865 * w, 0.54 * h, 0.022 * w, 0.075 * h, ink, 0.8)
    # range and efficiency line
    rect(0.07 * w, 0.30 * w, 0.88 * h, 0.90 * h, ink, 0.4)
    rect(0.70 * w, 0.93 * w, 0.88 * h, 0.90 * h, ink, 0.4)

    out = path or os.path.join(TEX_DIR, "cluster_seal.png")
    return CP.image_from_pixels("T_Cluster_Seal", np.clip(img, 0, 1), out)


# ------------------------------------------------------- delegated parts
def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_wheel(col, lib):
    import seal_wheel as W
    return W.build(col, lib)


def build_seats(col, lib):
    import seal_seats as SE
    return SE.build(col, lib)


def build_console(col, lib):
    import seal_console as C
    return C.build(col, lib)
