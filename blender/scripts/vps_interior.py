"""Voyah Passion S (岚图追光S) cabin — calibrated to Autohome Series 8534 interior photos.

Default trim built: Black / Light Cloud Beige (黑色/浅云米, seen on the Rosy Mist Pink studio
car c1_0002.jpg and cabin_tail_1.jpg #58-60):
  - Crisp warm off-white perforated Nappa leather (`INT_Leather_White`) on seats, lower dash
    band, high bridge console, steering wheel outer rim, and door card centre panels
  - Warm amber-tan piping & diagonal door stripes (`INT_Leather_Accent`, `INT_Thread_Accent`)
  - Matte charcoal upper dashboard (`INT_Dash_Top`), dark suede pillars & panoramic-framed
    headliner (`INT_Headliner`), and satin-black lower door pockets
  - Recolourable in the web configurator to Black / Danxia Red (黑色/丹霞红, cabin_1.jpg #1-24)

Key cockpit features (hmi_1.jpg #1-24):
  - Conjoined floating dual 15.6" displays: central HarmonySpace 5 (`screen_main`) + front
    passenger entertainment display (`screen_passenger`) in one continuous slim bezel
  - Huawei Sound central acoustic dome tweeter behind `screen_main`
  - Recessed slim letterbox driver digital cluster (`screen_cluster`) + AR-HUD aperture
  - 3-spoke flat-bottom D-ring steering wheel with column shifter stalk & VRS paddles
  - High floating bridge console with dual wireless phone pads, twin cupholders, split armrest
    over the heating/cooling box, and rear touch climate panel
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

import vps_surface as S
import vps_panels as PN
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "VPS_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.420                 # SUV cabin floor above 800V battery pack (underbody 0.252)
DRIVER_Y = 0.410
PASS_Y = -0.410

# Conjoined floating dual 15.6" screens (hmi_1.jpg #1-5, #21-24)
SCREEN_TILT = math.radians(10.0)
SCREEN_W, SCREEN_H = 0.345, 0.204
SCREEN_BORDER = 0.007
SCREEN_C = (0.494, 0.025, 1.115)          # 15.6" 2.5K central HarmonySpace 5 screen
PASS_SCREEN_C = (0.494, -0.335, 1.115)    # 15.6" co-pilot entertainment screen
DUAL_SLAB_C = (0.495, -0.155, 1.115)
DUAL_SLAB_W = 0.722

# Recessed slim letterbox driver instrument cluster (hmi_1.jpg #16-19)
CLUSTER_C = (0.606, DRIVER_Y, 1.118)
CLUSTER_W, CLUSTER_H = 0.275, 0.076
CLUSTER_TILT = math.radians(12.0)

WHEEL_C = (0.355, DRIVER_Y, 1.095)
WHEEL_TILT = math.radians(20.0)

DASH_HALF = 0.738
FRONT_BIGHT_X, FRONT_BIGHT_Z = -0.240, 0.655
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.160, 0.675, 0.375

MIRROR_C = (0.235, 0.000, 1.445)

# Light Cloud Beige (浅云米) + warm amber-tan contrast piping
CLOUD_BEIGE = (0.715, 0.700, 0.675)
ACCENT_TAN = (0.480, 0.255, 0.085)


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_glass(x, y):
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.68)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def _perf_image(name, color, maps):
    import numpy as np
    from carkit.textures import TEX_DIR
    msk = maps["perf_vps_mask"]
    w, h = msk.size
    a = np.array(msk.pixels[:], np.float32).reshape(h, w, 4)
    out = np.ones_like(a)
    for c in range(3):
        lin = color[c] * a[..., 0]
        out[..., c] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    im = bpy.data.images.get(name) or bpy.data.images.new(name, w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    im.pixels.foreach_set(out.ravel())
    im.filepath_raw = os.path.join(TEX_DIR, name.lower() + ".png")
    im.file_format = 'PNG'
    im.save()
    return im


def _mapped_image(nt, bsdf, img, tile, socket):
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    k = 1.0 / tile
    mp.inputs["Scale"].default_value = (k, k, k)
    nt.links.new(coord.outputs["UV"], mp.inputs["Vector"])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs[socket])
    return tex


def perforation_maps(size=512, pitch_px=32, radius=0.14, strength=10.0):
    import numpy as np
    from carkit import surfacemaps as SM
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.04, 0.0, 1.0)
    nrm = SM._image("T_PerfVPS_Normal", SM.height_to_normal(-hole, strength / size * 60.0),
                    filename="t_perf_vps_normal.png")
    mask = np.repeat((1.0 - 0.80 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_PerfVPS_Mask", mask, non_color=True, filename="t_perf_vps_mask.png")
    return nrm, msk


def perforated(name, color, maps, tile=0.064):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.44, specular=0.5, coat=0.10,
                  coat_rough=0.30, ior=1.45, sheen=0.0)
    IM._textured(nt, b, maps["perf_vps"], tile, 0.7)
    _mapped_image(nt, b, _perf_image("T_Perf_VPS_" + name[4:], color, maps), tile, "Base Color")
    return m


def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    maps["perf_vps"], maps["perf_vps_mask"] = perforation_maps()
    lib = IM.build_library(accent=ACCENT_TAN, maps=maps)
    lib["leather_white"] = perforated("INT_Leather_White", CLOUD_BEIGE, maps)
    lib["wheel_leather"] = lib["leather_black"]
    lib["headliner"] = IM.alcantara("INT_Headliner", (0.028, 0.028, 0.031), maps, sheen=0.6)

    m, nt, b = MB.mat("INT_Charge_Grey")
    MB.set_inputs(b, base=(0.12, 0.12, 0.125), metallic=0.0, roughness=0.55, specular=0.35)
    lib["charge"] = m

    m, nt, b = MB.mat("INT_Dash_Top")
    MB.set_inputs(b, base=(0.018, 0.018, 0.020), metallic=0.0, roughness=0.76, specular=0.35,
                  coat=0.0, sheen=0.14)
    IM._textured(nt, b, maps["leather"], 0.10, 0.6)
    lib["dash_top"] = m

    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.005, 0.005, 0.006), metallic=0.0, roughness=0.10, coat=0.5,
                  coat_rough=0.08, ior=1.5)
    lib["band_glass"] = m
    return lib


# ------------------------------------------------------------------- dash
DASH_SECTION = [
    (0.840, None), (0.770, None), (0.715, None), (0.685, None),
    (0.658, 1.196), (0.636, 1.174), (0.622, 1.160),
    (0.612, 1.116), (0.602, 1.072),
    (0.594, 1.048), (0.584, 1.022), (0.576, 1.004),
    (0.580, 0.990), (0.588, 0.974),
    (0.614, 0.916), (0.656, 0.835), (0.728, 0.745), (0.820, 0.670), (0.965, 0.610),
]
DASH_COUNTS = [8, 6, 4, 4, 4, 3, 5, 5, 3, 3, 3, 2, 2, 5, 6, 6, 6, 8]
DASH_PANELS = [("TopPad", 0, 6, "dash_top"), ("Band", 6, 8, "band_glass"),
               ("White", 8, 11, "leather_white"), ("Recess", 11, 13, "satin"),
               ("Lower", 13, 18, "leather_white")]
GLASS_GAP = (0.016, 0.014, 0.014, 0.020)


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    out = []
    for k, (x, z) in enumerate(DASH_SECTION):
        if z is None:
            z = z_glass(x, y) - GLASS_GAP[k]
            if k == 3:
                z = max(z, 1.188)
        out.append((x, z))
    return out


def build_band_vents(col, lib, sw):
    made = []
    ys = [sw.spine[i][1] for i in range(len(sw.spine))]
    for side in (1.0, -1.0):
        ya, yb = side * 0.655, side * 0.735
        ia = min(range(len(ys)), key=lambda i: abs(ys[i] - ya))
        ib = min(range(len(ys)), key=lambda i: abs(ys[i] - yb))
        i0, i1 = min(ia, ib), max(ia, ib)
        j0, j1 = sw.col(6) + 1, sw.col(8) - 1
        made.append(sw.mesh("int_dash_Vent%s" % ("L" if side > 0 else "R"), col, lib["satin"],
                            i0=i0, i1=i1, j0=j0, j1=j1, offset=0.0010))
        loop = ([sw.pts[i][j0] for i in range(i0, i1 + 1)] +
                [sw.pts[i1][j] for j in range(j0, j1 + 1)] +
                [sw.pts[i][j1] for i in range(i1, i0 - 1, -1)] +
                [sw.pts[i0][j] for j in range(j1, j0 - 1, -1)])
        loop = [tuple(Vector(q) + Vector((-0.0022, 0.0, 0.0))) for q in loop]
        made.append(tube("int_dash_VentRim%s" % ("L" if side > 0 else "R"), loop,
                         ellipse(0.0022, 0.0022, 6), col, lib["chrome"], lateral=(1.0, 0.0, 0.0)))
    return made


def build_dash_ends(col, lib, sw):
    return [F.ngon_cap(col, "int_dash_End" + tag, list(sw.pts[idx]), lib["leather_black"],
                       (0.0, s, 0.0))
            for idx, tag, s in ((0, "L", 1.0), (len(sw.pts) - 1, "R", -1.0))]


def build_dash_speaker(col, lib):
    """Central Voyah / Huawei Sound acoustic dome tweeter behind screen_main (hmi_1.jpg #22-24)."""
    made = []
    xd, yd, zb = 0.642, 0.025, 1.196
    made += F.disc(col, "int_dash_Dome", (xd, yd, zb + 0.032), (-0.35, 0.0, 0.94), 0.030,
                   lib["speaker"], dome=0.008, rim=0.0030, rim_mat=lib["chrome"])
    made.append(tube("int_dash_DomeBody", [(xd, yd, zb - 0.010 + 0.042 * t / 6.0) for t in range(7)],
                     ellipse(0.032, 0.032, 24), col, lib["satin"], lateral=(1.0, 0.0, 0.0)))
    return made


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 96, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    p, _n = sw.iso_col(sw.col(8), lift=0.0012)
    made.append(piping("int_dash_Chrome", p, col, lib["chrome"], r=0.0018,
                       lateral=(1.0, 0.0, 0.0)))
    # Warm amber-tan stitched welt across the dash + ambient light guide under it
    roll = [(0.568, y, 0.994) for y in [DASH_HALF - 2 * DASH_HALF * k / 80.0 for k in range(81)]]
    made.append(tube("int_dash_Roll", roll, ellipse(0.0095, 0.0100, 14), col,
                     lib["leather_accent"], lateral=(1.0, 0.0, 0.0)))
    made.append(tube("int_dash_Ambient", [(0.580, y, 0.980) for (_, y, _) in roll],
                     ellipse(0.0016, 0.0016, 6), col, lib["ambient"], lateral=(1.0, 0.0, 0.0)))
    # AR-HUD aperture ahead of the driver (hmi_1.jpg #20)
    ys = [sw.spine[i][1] for i in range(len(sw.spine))]
    i0 = min(range(len(ys)), key=lambda i: abs(ys[i] - 0.545))
    i1 = min(range(len(ys)), key=lambda i: abs(ys[i] - 0.275))
    made.append(sw.mesh("int_dash_HUD", col, lib["screen_glass"], i0=i0, i1=i1,
                        j0=sw.col(2) + 1, j1=sw.col(4) - 1, offset=0.0015))
    made += build_band_vents(col, lib, sw)
    made += build_dash_ends(col, lib, sw)
    made += build_dash_speaker(col, lib)
    return made, sw


# ---------------------------------------------------------------- screens
def _passenger_material():
    """Backlit Voyah mountain-sunrise wallpaper for the 15.6" passenger screen (hmi_1.jpg #1-4)."""
    import numpy as np
    from carkit.textures import TEX_DIR
    w, h = 640, 380
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / float(w), yy / float(h)
    sky_top = np.array([0.16, 0.34, 0.56], np.float32)
    sky_hor = np.array([0.62, 0.44, 0.36], np.float32)
    img = sky_top * (1.0 - v[..., None]) + sky_hor * v[..., None]
    # Stylized golden mountain peak (matching hmi_1.jpg #22 wallpaper)
    peak = 0.42 + 0.36 * np.abs(u - 0.50) * 2.1
    mtn = v > peak
    sun = np.clip(1.0 - np.abs(u - 0.48) * 3.5, 0.0, 1.0) * np.clip((0.68 - v) * 4.0, 0.0, 1.0)
    img[mtn] = (np.array([0.10, 0.09, 0.12], np.float32) +
                sun[..., None][mtn] * np.array([0.55, 0.22, 0.08], np.float32))
    # Subtle glass dock bar along bottom
    dock = (v > 0.84) & (v < 0.94) & (u > 0.08) & (u < 0.92)
    img[dock] = img[dock] * 0.45 + np.array([0.12, 0.16, 0.22], np.float32)

    im = bpy.data.images.get("T_Passenger_VPS") or bpy.data.images.new("T_Passenger_VPS", w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(img[::-1], 0.0, 1.0)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = os.path.join(TEX_DIR, "passenger_vps.png")
    im.file_format = 'PNG'
    im.save()

    m, nt, b = MB.mat("INT_Screen_Passenger")
    MB.set_inputs(b, base=(0.02, 0.02, 0.03), metallic=0.0, roughness=0.08,
                  coat=1.0, coat_rough=0.02, emission_strength=0.95)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = im
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if "Emission Color" in b.inputs:
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    return m


def cluster_image(path=None, w=720, h=200):
    """Slim letterbox driver cluster graphic (hmi_1.jpg #16-19: light/clean ADAS view + speed + range)."""
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.012, 0.016, 0.024)
    img += (0.015 * (1.0 - yy / h))[..., None] * np.array([0.65, 0.80, 1.0])
    white = np.array([0.88, 0.90, 0.94])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c

    gx, gy, s = 0.10 * w, 0.28 * h, 0.055 * h
    rect(gx, gx + s * 0.55, gy, gy + 7 * s, white)
    rect(gx, gx + 3 * s, gy, gy + s * 0.55, white)
    rect(gx, gx + 3 * s, gy + 3.2 * s, gy + 3.75 * s, white)
    rect(gx + 2.45 * s, gx + 3 * s, gy, gy + 3.75 * s, white)

    sx = 0.24 * w
    rect(sx, sx + 3 * s, gy, gy + s * 0.55, white)
    rect(sx, sx + 3 * s, gy + 6.45 * s, gy + 7 * s, white)
    rect(sx, sx + s * 0.55, gy, gy + 7 * s, white)
    rect(sx + 2.45 * s, sx + 3 * s, gy, gy + 7 * s, white)
    rect(0.10 * w, 0.36 * w, 0.82 * h, 0.82 * h + 4, (0.18, 0.72, 0.48))

    cx, cy = 0.62 * w, 0.56 * h
    body = (((xx - cx) / (0.13 * w)) ** 2 + ((yy - cy) / (0.11 * h)) ** 2 < 1.0) & (yy < cy + 0.06 * h)
    roof = (((xx - cx - 0.008 * w) / (0.07 * w)) ** 2 + ((yy - cy + 0.07 * h) / (0.09 * h)) ** 2 < 1.0)
    img[body | roof] = np.array([0.78, 0.62, 0.64])

    out = path or os.path.join(TEX_DIR, "cluster_vps.png")
    im = bpy.data.images.get("T_Cluster_VPS") or bpy.data.images.new("T_Cluster_VPS", w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = img[::-1]
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = out
    im.file_format = 'PNG'
    im.save()
    return out


def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    # Conjoined floating dual-screen slab (centre + passenger 15.6" displays)
    made.append(F.slab("int_dualscreen_body", DUAL_SLAB_C, DUAL_SLAB_W + 2 * b, SCREEN_H + 2 * b,
                       0.018, 0.012, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col, lift=0.0012))
    made[-1].data.materials.append(F.screen_material())

    pq = F.screen_quad("screen_passenger", PASS_SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col, lift=0.0012)
    pq.data.materials.append(_passenger_material())
    made.append(pq)

    ct, st = math.cos(SCREEN_TILT), math.sin(SCREEN_TILT)
    for ym in (0.02, -0.32):
        back = Vector((DUAL_SLAB_C[0] + 0.018 * ct, ym, DUAL_SLAB_C[2] - 0.018 * st))
        made.append(F.box(col, "int_screen_arm_%s" % ("C" if ym > -0.1 else "P"),
                          tuple(back.lerp(Vector((0.610, ym, 1.105)), 0.5)),
                          (0.610 - back.x, 0.085, 0.055), lib["piano"], r=0.010))

    # Recessed slim letterbox driver digital cluster
    made.append(F.slab("int_cluster_body", CLUSTER_C, CLUSTER_W + 0.016, CLUSTER_H + 0.014,
                       0.012, 0.008, CLUSTER_TILT, col, lib["piano"]))
    cq = F.screen_quad("screen_cluster", CLUSTER_C, CLUSTER_W, CLUSTER_H, CLUSTER_TILT, col, lift=0.0012)
    cq.data.materials.append(F.screen_material())
    made.append(cq)
    return made


# ---------------------------------------------------------- steering wheel & seats
VOYAH_PASSION_S_WHEEL = dict(
    radius=0.176, flat_bottom=-0.144, flat_top=0.158, section=(0.0170, 0.0205),
    grip_swell=0.12,
    segments=[(30.0, 150.0, "leather_white"), (150.0, 210.0, "leather_black"),
              (210.0, 330.0, "leather_white"), (330.0, 390.0, "leather_black")],
    marker=None,
    hub=dict(w=0.118, h=0.106, sides=4, r_corner=0.026, dome=0.008, depth=0.050),
    spokes=dict(v=-0.004, h=0.048, t=0.024, u_in=0.052, pad=(0.064, 0.038)),
    lower_spoke=dict(v_top=-0.050, half_gap=0.016, width=0.014),
    buttons=[],
    logo="VOYAH",
)


def build_wheel(col, lib):
    from carkit.interior import steering as ST
    made, fr = ST.wheel(col, lib, VOYAH_PASSION_S_WHEEL, WHEEL_C, WHEEL_TILT)
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        a = Vector(fr.p(side * -0.045, 0.030, -0.070))
        b = Vector(fr.p(side * -0.128, 0.036, -0.045))
        made.append(tube("int_wheel_stalk" + tag, [tuple(a.lerp(b, t / 8.0)) for t in range(9)],
                         ellipse(0.0068, 0.0068, 10), col, lib["piano"], lateral=tuple(fr.A),
                         scale=lambda s: (1.0 - 0.22 * s, 1.0 - 0.22 * s)))
        # VRS sport shift paddles behind the horizontal spokes (hmi_1.jpg #14-15)
        pc = fr.p(side * -0.112, 0.022, -0.032)
        made.append(F.box(col, "int_wheel_paddle" + tag, pc, (0.008, 0.036, 0.052),
                          lib["piano"], r=0.003))
    return made


def _rear_spec():
    import copy
    from carkit.interior import seat as SE
    sp = copy.deepcopy(SE.LUXEED_RX_FRONT)
    sp["backrest"]["spine"] = [(x * 0.95, z * 0.85) for (x, z) in sp["backrest"]["spine"]]
    return sp


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        parts, _cush, _back = SE.seat(col, lib, SE.LUXEED_RX_FRONT,
                                      (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), name="int_seat_" + tag)
        made += parts
        made.append(SE.base(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), FLOOR_Z,
                            name="int_seat_%s_base" % tag))
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, _cush, _back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                      name="int_seat_" + tag)
        made += parts
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.20, 0.0, REAR_BIGHT_Z - 0.03),
                      (0.46, 0.21, 0.12), lib["leather_white"], r=0.03))
    made.append(F.box(col, "int_rear_centre_back",
                      (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.27), (0.12, 0.21, 0.50),
                      lib["leather_white"], r=0.03, pitch=math.radians(-18)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.15, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.56, 1.32, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["satin"], r=0.02))
    return made


# ---------------------------------------------------------------- console
CONSOLE_TOP = Curve([
    (-0.455, 0.770), (-0.445, 0.855), (-0.430, 0.888), (-0.405, 0.900), (-0.095, 0.904),
    (-0.035, 0.902), (-0.018, 0.892), (-0.008, 0.875), (0.000, 0.872),
    (0.145, 0.872), (0.155, 0.876), (0.165, 0.892), (0.180, 0.902),
    (0.250, 0.916), (0.340, 0.930), (0.430, 0.942), (0.485, 0.948),
    (0.495, 0.962), (0.505, 0.985), (0.525, 0.994), (0.640, 0.996),
], mode="pchip")
CONSOLE_HW = 0.130
CUPS = [(0.072, 0.056, 0.041), (0.072, -0.056, 0.041)]


def _console_stations():
    xs = []
    x = -0.455
    while x < 0.640:
        xs.append(x)
        dense = (-0.46 < x < -0.40) or (-0.04 < x < 0.18) or (0.48 < x < 0.54)
        x += 0.005 if dense else 0.014
    xs.append(0.640)
    return xs


def _console_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = CONSOLE_HW, 0.016
    pts = [(-hw, FLOOR_Z), (-hw, zt - 0.10), (-hw, zt - r)]
    for k in range(1, n_arc):
        a = math.pi - 0.5 * math.pi * k / n_arc
        pts.append((-hw + r + r * math.cos(a), zt - r + r * math.sin(a)))
    ny = 36
    for k in range(ny + 1):
        y = -hw + r + (2 * (hw - r)) * k / ny
        pts.append((y, zt + 0.001 * (1.0 - (y / (hw - r)) ** 2)))
    for k in range(1, n_arc):
        a = 0.5 * math.pi - 0.5 * math.pi * k / n_arc
        pts.append((hw - r + r * math.cos(a), zt - r + r * math.sin(a)))
    pts += [(hw, zt - r), (hw, zt - 0.10), (hw, FLOOR_Z)]
    return pts


def build_console(col, lib):
    import bmesh
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _console_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_white"])
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.z > 0.85 and any((c.x - cx) ** 2 + (c.y - cy) ** 2 < (r - 0.0015) ** 2
                              for (cx, cy, r) in CUPS):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.76)))
    made.append(ob)

    # Rear console face with touch climate control screen & dual AC vents (cabin_2.jpg #28-30)
    rr = _console_section(xs[0])
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in rr],
                           lib["leather_black"], (-1.0, 0.0, 0.0)))
    made.append(F.box(col, "int_console_rear_screen", (xs[0] - 0.004, 0.0, 0.785),
                      (0.006, 0.180, 0.068), lib["screen_glass"], r=0.008))
    zv = 0.715
    made.append(F.box(col, "int_console_rear_vent", (xs[0] - 0.004, 0.0, zv), (0.006, 0.178, 0.036),
                      lib["satin"], r=0.004))
    rim = [(xs[0] - 0.0075, y, z) for (y, z) in
           F.round_rect_xy(-0.094, 0.094, zv - 0.022, 0.825, 0.012)]
    made.append(tube("int_console_rear_vent_rim", rim + [rim[0]], ellipse(0.0022, 0.0022, 6), col,
                     lib["chrome"], lateral=(1.0, 0.0, 0.0)))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.001 * (1.0 - (y / (CONSOLE_HW - 0.016)) ** 2) + lift)

    # Dual wireless phone charging pads (hmi_1.jpg #1-5) + central divider + piano cupholder bezel
    for name, x0, x1, role, lift in (("int_console_charge", 0.220, 0.468, "charge", 0.0014),
                                     ("int_console_cup_deck", -0.008, 0.155, "piano", 0.0008)):
        rows = [[top(x0 + (x1 - x0) * i / 16.0, y, lift) for y in
                 [0.106 - 0.212 * j / 20.0 for j in range(21)]] for i in range(17)]
        pn = grid_mesh(name, rows, col, lib[role])
        M.orient(pn.data, lambda c: (0.0, 0.0, 1.0))
        made.append(pn)

    # Central wireless-pad divider ridge
    div = [top(0.225 + 0.238 * t / 12.0, 0.0, 0.0055) for t in range(13)]
    made.append(tube("int_console_charge_div", div, ellipse(0.0045, 0.0040, 8), col, lib["chrome"],
                     lateral=(0.0, 0.0, 1.0)))

    # Chrome surround framing wireless pads & cupholders
    frame = ([top(0.472, y, 0.0025) for y in [-0.106 + 0.212 * k / 12.0 for k in range(13)]] +
             [top(x, 0.106, 0.0025) for x in [0.472 - 0.482 * k / 18.0 for k in range(1, 19)]] +
             [top(-0.010, y, 0.0025) for y in [0.106 - 0.212 * k / 12.0 for k in range(1, 13)]] +
             [top(x, -0.106, 0.0025) for x in [-0.010 + 0.482 * k / 18.0 for k in range(1, 19)]])
    made.append(tube("int_console_frame", frame, ellipse(0.0028, 0.0028, 8), col, lib["chrome"],
                     lateral=(0.0, 0.0, 1.0)))

    for k, (cx, cy, r) in enumerate(CUPS):
        rings = []
        for d, s in ((0.0, 1.0), (0.004, 0.99), (0.060, 0.96), (0.074, 0.90), (0.076, 0.0)):
            rings.append([(cx + r * s * math.cos(2 * math.pi * j / 32),
                           cy + r * s * math.sin(2 * math.pi * j / 32), 0.8725 - d) for j in range(32)])
        well = grid_mesh("int_console_cup%d" % k, rings, col, lib["satin"], wrap_t=True)
        M.orient(well.data, lambda c, cx=cx, cy=cy: (cx - c[0], cy - c[1], 0.5))
        made.append(well)
        ring = [(cx + r * math.cos(2 * math.pi * j / 32), cy + r * math.sin(2 * math.pi * j / 32), 0.8735)
                for j in range(33)]
        made.append(tube("int_console_cup_rim%d" % k, ring, ellipse(0.0035, 0.0028, 8), col,
                         lib["chrome"], lateral=(0.0, 0.0, 1.0)))
    return made


# ------------------------------------------------------------- door cards
def _belt_z(x):
    return PN.BELT_Z(max(PN.X_DLO_TIP, min(PN.BELT_X_MAX, x)))


DOOR_TH = Curve([(0.48, 0.110), (0.68, 0.148), (0.85, 0.168), (1.00, 0.160), (1.10, 0.135),
                 (1.18, 0.095), (1.26, 0.068)], mode="pchip")


def _v_top_front():
    return max(PN.V_BELT(x) for x in (-0.20, 0.10, 0.45, 0.80)) + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: PN._DOOR_F_EDGE(z) - 0.022,
                    lambda z: PN._DOOR_SPLIT_EDGE(z) + 0.010, 0.495, _belt_z, DOOR_TH,
                    v_top=_v_top_front(), side=side)


def _rear_top_z(x):
    return _belt_z(x)


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.48, 0.095), (0.68, 0.125), (0.85, 0.138), (1.00, 0.125), (1.14, 0.096),
                (1.24, 0.070), (1.32, 0.058)], mode="pchip")
    return DoorCard(S.BODY, lambda z: PN._DOOR_SPLIT_EDGE(z) - 0.010,
                    lambda z: PN._DOOR_R_EDGE(z) + 0.012, 0.495, _rear_top_z, th,
                    v_top=max(PN.V_BELT(x) for x in (-1.28, -0.85, -0.30)) + 0.015, side=side)


def _door_armrest(dc, name, col, lib, side, path_xz, width=0.068, height=0.048, n=36):
    from carkit.interior.sweep import cr_segments
    path = smooth_path([(x, 0.0, z) for (x, z) in path_xz], n + 1)
    rows, edge = [], []
    for k, p in enumerate(path):
        s = k / float(n)
        e = min(1.0, min(s, 1.0 - s) * 7.0)
        e = e * e * (3 - 2 * e)
        w = 0.004 + (width - 0.004) * e
        x, z = p[0], p[2]
        y0 = dc.skin_y(x, z) - dc.th(z)
        prof = [(0.0, -height), (w * 0.55, -height * 0.92), (w * 0.95, -height * 0.55),
                (w, -0.012), (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)]
        sec = cr_segments(prof, 4)
        rows.append([(x, side * (y0 - a), z + b) for (a, b) in sec])
        edge.append((x, side * (y0 - w * 0.80), z + 0.0002))
    ob = grid_mesh(name, rows, col, lib["leather_white"])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    nrm = [(0.0, 0.0, 1.0)] * len(edge)
    st = stitches(name + "Stitch", edge[3:-3], nrm[3:-3], col, lib["thread_accent"])
    return [ob, st]


def build_doors(col, lib):
    """Front & rear door cards styled after cabin_tail_1.jpg #60 and cabin_1.jpg #3-10."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr, xf = dc.xr, dc.xf
        rail_bot = lambda x: _belt_z(x) - 0.058
        white_bot = lambda x: 0.815 + 0.030 * _smooth((x - 0.10) / 0.65)
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(1.21) + 0.004, xf(1.19) - 0.004, _belt_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.495,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.495, white_bot,
                            x0=xr, x1=xf, nx=52, nz=18, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"], rail_bot,
                            lambda x: _belt_z(x) - 0.002, proud=-0.003, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        made.append(dc.band(pre + "White", col, lib["leather_white"], white_bot,
                            lambda x: rail_bot(x) - 0.002, proud=0.006, x0=xr, x1=xf,
                            nx=52, nz=14, mirror=False))
        # Electronic door release chrome push-button [D] on upper trim (cabin_1.jpg #5)
        xb, zb = 0.240, 1.075
        yb = side * (dc.skin_y(xb, zb) - dc.th(zb) - 0.008)
        made.append(F.box(col, pre + "EButton", (xb, yb, zb), (0.044, 0.012, 0.024),
                          lib["chrome"], r=0.005))
        # Twin diagonal accent piping stripes + ambient light guide (cabin_tail_1.jpg #60)
        for si, xoff in enumerate((0.0, -0.14)):
            p_diag = dc.curve([(0.05 + xoff + 0.24 * k / 12.0, 0.86 + 0.14 * k / 12.0)
                               for k in range(13)], proud=0.009)
            made.append(piping(pre + "Stripe%d" % si, p_diag, col, lib["leather_accent"],
                               r=0.0028, lateral=(0.0, 0.0, 1.0)))
        pts = dc.curve([(0.78 - 0.88 * k / 24.0, rail_bot(0.78 - 0.88 * k / 24.0) - 0.004)
                        for k in range(25)], proud=0.007)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
        # Voyah Sound speaker grille at front-lower corner (cabin_1.jpg #9)
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.56, lambda x: 0.76,
                            proud=0.004, x0=lambda z: 0.54, x1=lambda z: 0.82,
                            nx=18, nz=8, mirror=False))
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-0.08, 0.805), (0.16, 0.822), (0.42, 0.842), (0.64, 0.862)])
        for k in range(3):
            xk = 0.44 + 0.048 * k
            yk = side * (dc.skin_y(xk, 0.855) - dc.th(0.855) - 0.036)
            made.append(F.box(col, pre + "Switch%d" % k, (xk, yk, 0.860), (0.028, 0.016, 0.008),
                              lib["piano"], r=0.002))

    # Rear door cards
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        rb = lambda x: _rear_top_z(x) - 0.056
        wb = lambda x: 0.835 + 0.040 * _smooth((-0.30 - x) / 0.85)
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(1.27) + 0.008, xf(1.21) - 0.004,
                                _rear_top_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.495,
                               lambda x: _rear_top_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.495, wb,
                            x0=xr, x1=xf, nz=16, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"], rb,
                            lambda x: _rear_top_z(x) - 0.002, proud=-0.003, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        made.append(dc.band(pre + "White", col, lib["leather_white"], wb,
                            lambda x: rb(x) - 0.002, proud=0.006, x0=xr, x1=xf, nz=12, mirror=False))
        pts = dc.curve([(-0.26 - 0.82 * k / 20.0, rb(-0.26 - 0.82 * k / 20.0) - 0.004)
                        for k in range(21)], proud=0.006)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-1.02, 0.815), (-0.74, 0.825), (-0.42, 0.835)], width=0.060)
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.56, lambda x: 0.72,
                            proud=0.004, x0=lambda z: -0.60, x1=lambda z: -0.34,
                            nx=14, nz=6, mirror=False))
    return made


# ---------------------------------------------------------------- the shell
X_OPEN_F, X_OPEN_R = -0.040, -1.520      # panoramic glass roof opening in the suede headliner
Y_OPEN = 0.465
X_HEADLINER_R = -1.745


def v_head_edge(x):
    return S.v_along(x, PN.V_GT(max(x, PN.X_DLO_TIP)), 0.050)


def _head_rows(x0, x1, nx, v_in, v_out=v_head_edge, inset=0.045, nv=22):
    rows = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / float(nx)
        a, b = v_out(x), v_in(x)
        rows.append([S.surface_offset(x, a + (b - a) * j / float(nv), -inset) for j in range(nv + 1)])
    return rows


def build_headliner(col, lib):
    """Dark suede headliner framing the full panoramic glass roof, joined into `int_headliner`."""
    from carkit import export as X
    parts = []
    centre = lambda x: 0.9995
    open_v = lambda x: S.v_at_y_upper(x, Y_OPEN)
    for name, x0, x1, nx in (("int_headliner_F", PN.X_ROOF_F + 0.030, X_OPEN_F, 16),
                             ("int_headliner_R", X_OPEN_R, X_HEADLINER_R, 28)):
        rows = _head_rows(x0, x1, nx, centre)
        for r in rows:
            r[-1] = (r[-1][0], 0.0, r[-1][2])
        ob = grid_mesh(name, rows, col, lib["headliner"])
        M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
        M.mirror_y(ob)
        parts.append(ob.name)
    rows = _head_rows(X_OPEN_F + 0.002, X_OPEN_R - 0.002, 48, open_v, nv=10)
    ob = grid_mesh("int_headliner_side", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
    M.mirror_y(ob)
    parts.append(ob.name)

    loop = [(X_OPEN_F + (X_OPEN_R - X_OPEN_F) * k / 39.0,
             open_v(X_OPEN_F + (X_OPEN_R - X_OPEN_F) * k / 39.0)) for k in range(40)]
    rv = grid_mesh("int_headliner_reveal",
                   [[S.surface_offset(x, v, -0.045), S.surface_offset(x, v, -0.004)] for (x, v) in loop],
                   col, lib["headliner"])
    M.orient(rv.data, lambda c: (0.0, -1.0 if c[1] > 0 else 1.0, 0.0))
    M.mirror_y(rv)
    parts.append(rv.name)

    for x, nm in ((X_OPEN_F, "F"), (X_OPEN_R, "R")):
        v0 = open_v(x)
        r_end = [[S.surface_offset(x, v0 + (0.9995 - v0) * j / 12.0, -0.045),
                  S.surface_offset(x, v0 + (0.9995 - v0) * j / 12.0, -0.004)] for j in range(13)]
        r_end[-1] = [(p[0], 0.0, p[2]) for p in r_end[-1]]
        ev = grid_mesh("int_headliner_reveal" + nm, r_end, col, lib["headliner"])
        M.orient(ev.data, lambda c, s=(-1.0 if nm == "F" else 1.0): (s, 0.0, 0.0))
        M.mirror_y(ev)
        parts.append(ev.name)
    return [X.join("int_headliner", parts)]


def build_roof_fittings(col, lib):
    made = []
    w, h, t = 0.225, 0.062, 0.016
    made.append(F.round_slab(col, "int_rvmirror", MIRROR_C, w, h, t, 0.024, lib["piano"],
                             tilt=math.radians(8.0)))
    mg = bpy.data.materials.get("INT_Mirror") or bpy.data.materials.new("INT_Mirror")
    mg.use_nodes = True
    bm = next(n for n in mg.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bm.inputs["Base Color"].default_value = (0.30, 0.31, 0.32, 1.0)
    bm.inputs["Metallic"].default_value = 1.0
    bm.inputs["Roughness"].default_value = 0.05
    made.append(F.round_slab(col, "int_rvmirror_glass",
                             (MIRROR_C[0] - t * 0.5 - 0.0008, 0.0, MIRROR_C[2]), w - 0.006,
                             h - 0.006, 0.0008, 0.021, mg, tilt=math.radians(8.0)))
    zg = z_glass(MIRROR_C[0] + 0.07, 0.0) - 0.006
    stem = smooth_path([(MIRROR_C[0] + 0.02, 0.0, MIRROR_C[2] + 0.02),
                        (MIRROR_C[0] + 0.045, 0.0, 0.5 * (MIRROR_C[2] + zg) + 0.01),
                        (MIRROR_C[0] + 0.07, 0.0, zg)], 8)
    made.append(tube("int_rvmirror_stem", stem, ellipse(0.011, 0.008, 10), col, lib["satin"],
                     lateral=(0.0, 1.0, 0.0)))

    # Overhead console & visors (cabin_2.jpg #46-48, cabin_tail_1.jpg #49)
    xs = [0.16 - 0.16 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.12 * (1 - 2 * j / 10.0), zr - 0.015 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["piano"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)

    for side in (1.0, -1.0):
        rows = []
        for i in range(9):
            x = PN.X_ROOF_F + 0.02 - 0.17 * i / 8.0
            zr = S.surface_offset(x, S.v_at_y_upper(x, 0.35), -0.046)[2]
            rows.append([(x, side * (0.150 + 0.40 * j / 8.0),
                          zr - 0.002 * math.sin(math.pi * j / 8) - 0.020 * (j / 8.0) ** 2)
                         for j in range(9)])
        vz = grid_mesh("int_visor_%s" % ("L" if side > 0 else "R"), rows, col, lib["headliner"])
        M.orient(vz.data, lambda c: (0.0, 0.0, -1.0))
        M.solidify(vz, 0.012, 1.0)
        M.bevel(vz, 0.004, 2, 40)
        made.append(vz)
    return made


def build_shell(col, lib):
    made = build_headliner(col, lib)
    xs = [0.760 - (0.760 - (PN.X_ROOF_F - 0.03)) * k / 28.0 for k in range(29)]

    def a_door(x):
        return (x, S.v_along(x, PN.v_up(x, max(PN.BELT_Z(0.68), PN.z_a(min(x, PN.A_FOOT[0])))), -0.020))

    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs, a_door,
                             lambda x: (x, S.v_along(x, PN.V_A(x), 0.018)),
                             depth=0.010, bulge=0.034, name="int_apillar"))
    # Driver A-pillar DMS camera pod + tweeter (cabin_tail_1.jpg #50)
    made.append(F.box(col, "int_apillar_dms", (0.560, 0.675, 1.295), (0.046, 0.032, 0.058),
                      lib["satin"], r=0.006))

    xs = [PN.X_ROOF_F + 0.04 - (PN.X_ROOF_F + 0.04 - PN.X_DLO_TIP) * k / 44.0 for k in range(45)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs,
                             lambda x: (x, S.v_along(x, PN.V_GT(x), -0.010)),
                             lambda x: (x, S.v_along(x, PN.V_GT(x), 0.070)),
                             depth=0.012, bulge=0.020, name="int_roofrail"))

    vb0 = PN.V_BELT(PN.X_BPILLAR) - 0.006
    vb1 = PN.V_GT(PN.X_BPILLAR) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], vs,
                             lambda v: (PN.GB_F + 0.012, v), lambda v: (PN.GB_R - 0.012, v),
                             depth=0.012, bulge=0.032, name="int_bpillar"))

    xs = [PN.X_DLO_TIP + 0.030 - (PN.X_DLO_TIP + 0.030 + 2.42) * k / 24.0 for k in range(25)]

    def c_lo(x):
        z = max(1.12, min(_belt_z(x) - 0.06, 1.24))
        z += (1.08 - z) * _smooth((-1.70 - x) / 0.15)
        return S.v_at_z(x, z, 0.30, 0.99)

    def c_hi(x):
        a = v_head_edge(max(x, X_HEADLINER_R)) + 0.010
        if x >= PN.X_KNEE:
            return a
        b = PN.V_REARGLASS(x) + 0.012
        return a + (b - a) * _smooth((PN.X_KNEE - x) / 0.05)

    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.030,
                               bulge=0.020, nt=16, name="int_cpillar", overlap=0.010))
    x0 = xs[0]
    a, b = S.v_along(x0, c_lo(x0), -0.010), S.v_along(x0, c_hi(x0), 0.010)
    fl = grid_mesh("int_cpillar_flange",
                   [[S.surface_offset(x0, a + (b - a) * (j / 16.0),
                                      -(0.030 + 0.020 * math.sin(math.pi * j / 16.0) ** 0.7)),
                     S.surface_offset(x0, a + (b - a) * (j / 16.0), -0.004)] for j in range(17)],
                   col, lib["headliner"])
    M.orient(fl.data, lambda c: (1.0, 0.0, 0.0))
    M.mirror_y(fl)
    made.append(fl)

    xs_q = [PN.X_DOOR_R_TOP + 0.010 - (PN.X_DOOR_R_TOP + 0.010 - (PN.X_DLO_TIP - 0.020)) * k / 10.0
            for k in range(11)]
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs_q,
                               lambda x: S.v_at_z(x, 1.160, 0.30, 0.99),
                               lambda x: PN.V_BELT(x), inset=0.014, bulge=0.004, nt=16,
                               name="int_qtr_lower", overlap=0.008))
    made += build_roof_fittings(col, lib)
    made.append(CB.floor(col, lib["carpet"], -1.60, 0.80, 1.02, FLOOR_Z, 0.72,
                         lambda x: 0.73 - 0.05 * _smooth((x - 0.84) / 0.06), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.32, 0.84, 0.72, 0.86, FLOOR_Z, 0.498,
                        name="int_sill"))
    return made


# ------------------------------------------------------------ closing trims & pedals
def build_closures(col, lib):
    made = []
    vh = _v_top_front() + 0.10
    xs = [PN.X_BPILLAR - 0.035 + 0.070 * k / 6.0 for k in range(7)]
    rows = [[(x, CB.skin_offset_y(S.BODY, x, z, 0.030, vh), z)
             for z in [0.495 + (_belt_z(x) - 0.495) * k / 12.0 for k in range(13)]] for x in xs]
    seal = grid_mesh("int_bpillar_seal", rows, col, lib["satin"])
    M.orient(seal.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(seal)
    made.append(seal)

    yk = 0.748
    x_open = PN._DOOR_F_EDGE(0.65) - 0.010
    kick_y = Curve([(x_open, yk), (0.94, yk), (1.00, 0.685), (1.08, 0.680)], mode="pchip")
    made.append(CB.wall(col, lib["leather_black"],
                        [(x_open + (1.08 - x_open) * k / 16.0,
                          kick_y(x_open + (1.08 - x_open) * k / 16.0)) for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.99, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["leather_black"],
                        [(x_open, yk + (0.865 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.04 + 0.05 * _smooth((y - 0.78) / 0.04),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))

    rc = rear_card(1.0)
    vq = max(PN.V_BELT(x) for x in (-1.28, -1.45)) + 0.10
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_black"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.80,
        FLOOR_Z + 0.02, 0.672, 1.015, 1.250, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)

    import vps_rear as RR
    pane = RR.pane()

    def pane_z_at(y):
        x_of, z_a = pane.column(y)
        cols = [(pane.corner(x_of(z), y, z, z_a), z) for z in
                [pane.z_bot(y) + (pane.z_top(y) - pane.z_bot(y)) * k / 24.0 for k in range(25)]]
        return Curve(cols, mode="pchip")

    pane_zs = [pane_z_at(0.0), pane_z_at(0.20)]
    pts = []
    for k in range(17):
        x = -1.54 - (2.40 - 1.54) * k / 16.0
        z = 1.115 + 0.095 * (k / 16.0) ** 1.8
        pts.append((x, min([z] + [f(x) - 0.016 for f in pane_zs]) if x < -2.02 else z))
    made.append(CB.bulkhead(col, lib["headliner"], pts,
                            lambda x, z: CB.skin_offset_y(S.BODY, x, z, 0.070, 0.80),
                            name="int_parcel_shelf", facing=(0.0, 0.0, 1.0)))

    rows = []
    for j in range(17):
        y = min(0.52, pane.y_w - 0.015) * j / 16.0
        x_of, z_a = pane.column(y)
        zb = pane.z_bot(y) + 0.004
        xb = pane.corner(x_of(zb), y, zb, z_a) + 0.014
        xa, za = -2.160, 1.175
        rows.append([(xa + (xb - xa) * t, y, za + (zb - za) * (t ** 0.6)) for t in
                     [k / 6.0 for k in range(7)]])
    sl = grid_mesh("int_rear_sill", rows, col, lib["headliner"])
    M.orient(sl.data, lambda c: (0.3, 0.0, 1.0))
    M.mirror_y(sl)
    made.append(sl)

    made.append(CB.bulkhead(col, lib["satin"],
                            [(-1.555, FLOOR_Z + (1.115 - FLOOR_Z) * k / 10.0) for k in range(11)],
                            lambda x, z: 0.70 if z < 0.86 else CB.skin_offset_y(S.BODY, x, z, 0.075, 0.80),
                            name="int_rear_bulkhead", facing=(1.0, 0.0, 0.0)))
    return made


def build_pedals(col, lib):
    made = []
    p = math.radians(40.0)
    a = Vector((math.sin(p), 0.0, math.cos(p)))
    n = Vector((-math.cos(p), 0.0, math.sin(p)))
    for name, y, x, z, w, h, strips in (("rest", 0.640, 0.860, 0.530, 0.075, 0.210, 5),
                                        ("brake", 0.390, 0.835, 0.560, 0.092, 0.078, 3),
                                        ("accel", 0.235, 0.880, 0.510, 0.055, 0.200, 0)):
        c = Vector((x, y, z))
        made.append(F.box(col, "int_pedal_" + name, tuple(c), (0.010, w, h), lib["rubber"],
                          r=0.003, pitch=p))
        for k in range(strips):
            q = (c + n * 0.006 + Vector((0.0, (k - 2) * w * 0.18, 0.0)) if name == "rest"
                 else c + n * 0.006 + a * ((k - 1) * h * 0.28))
            sz = (0.004, 0.006, h * 0.85) if name == "rest" else (0.004, w * 0.82, 0.008)
            made.append(F.box(col, "int_pedal_%s_s%d" % (name, k), tuple(q), sz,
                              lib["satin"], r=0.0015, pitch=p))
    return made


def cabin_lights(col):
    return F.lights(col, [
        ("int_L_Roof", (-0.30, 0.0, 1.48), (-0.30, 0.0, 0.45), (1.7, 1.25), 10.0,
         (0.92, 0.95, 1.00), True),
        ("int_L_Back", (-1.15, 0.0, 1.38), (0.60, 0.0, 0.90), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.50, 1.32), (0.0, 0.0, 0.86), (2.2, 0.6), 2.5,
         (0.86, 0.91, 1.00), True),
        ("int_L_Right", (0.0, -1.50, 1.32), (0.0, 0.0, 0.86), (2.2, 0.6), 2.5,
         (0.86, 0.91, 1.00), True),
    ])


def main(lights=True):
    col = bpy.data.collections.get(COLLECTION)
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(col)
    col = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(col)
    lib = build_library()
    build_shell(col, lib)
    build_dash(col, lib)
    build_screens(col, lib)
    build_wheel(col, lib)
    build_seats(col, lib)
    build_console(col, lib)
    build_doors(col, lib)
    build_closures(col, lib)
    build_pedals(col, lib)
    if lights:
        cabin_lights(col)
    from carkit import build as B
    skip_uv = {"INT_Screen", "INT_Screen_Passenger"}
    B.ensure_uvs([col], force=tuple(m.name for m in bpy.data.materials
                                    if m.name.startswith("INT_") and m.name not in skip_uv))
    assert bpy.data.objects.get("screen_main"), "screen_main is the HMI anchor"
    meshes = [o for o in col.objects if o.type == 'MESH']
    print("interior: %d meshes, %d tris" % (len(meshes), M.tri_count(meshes)))
    return col
