"""Zeekr 7X cabin: the Ultra's cream-white and taupe ("purple/white") interior, built with
carkit.interior from hardpoints read off Autohome's cabin photographs.

References (blender/reference/zeekr-7x/interior/, Autohome series 7777, spec 75350):

    c10_0001   the dash from behind the console, wide (both A-pillars, the screen, the wheel)
    c10_0002   the driver's view: wheel, cluster, screen, console, pedals, door switches
    c10_0048   the dash and console from the passenger's side
    c3_0001/2  the driver's seat and the door opening from outside
    c3_0003    the front door card from outside
    c3_0018    the rear seats through the rear door; c3_0017 the roof from the passenger seat

What the photographs show of the cabin:

    colours      cream-white leather, perforated, with taupe ("mocha") for the dash top, the
                 door cards' upper rail and lower card, the seat shrouds and carpet; a dark
                 glossy strip with a thin rose-gold line along the dash and the door cards;
                 cream suede headliner; black piano trim round the console pad
    dash         a low taupe top with a hood over the cluster, a cream face with a slim
                 dark strip and chrome-dark line, a floating 16 in screen (16:10) over a row
                 of knurled buttons, a wide vent slot and a tweeter dome at the glass
    wheel        a squircle (flat top and bottom) rim, taupe over cream, a round hub with the
                 Z mark, two framed button pods, a U-shaped lower spoke
    console      a cream stack with a black-framed wireless pad, a crystal selector, the
                 armrest lid behind it
    doors        taupe rail and lower card, a cream upper panel, a pod-shaped armrest and
                 pull, a black gloss switch pack, a speaker grille bar

Hardpoints are in the build's axes: +X forward, +Y left (China is LHD), +Z up, the car's
centre at x = 0. The numbers are first-pass readings (the cabin cameras are not solved to
the millimetre: see zx_cabinsolve) and are checked by overlay against c10_0002.
"""
import math

import bpy
from mathutils import Vector

import zx_surface as S
import zx_panels as PN
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "ZX_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.340
DRIVER_Y = 0.370
PASS_Y = -0.370

# 9 mm toward the passenger: from the driver's eye (0.74 m from the wheel) the wheel's right rim
# stood in front of the screen's left bezel; with the wheel 1.2 cm and 4 mm narrower the plan gap
# between them is 3.9 cm and a thin strip of the dash shows between them (c10_0002)
SCREEN_Y = -0.009
SCREEN_C = (0.930, SCREEN_Y, 0.990)           # the floating 16 in display's front plane
SCREEN_W, SCREEN_H = 0.3445, 0.2153           # 16 in, 16:10 active area
SCREEN_TILT = math.radians(3.0)
SCREEN_BORDER = 0.0072

# The wheel is read from c10_0001 (a centre camera, both the wheel and the screen at ~1.7 m: the
# screen's width is the ruler): 0.392 wide, 0.372 tall, its top 7 cm above the screen's top edge
# (z 1.18), its centre 2 cm nearer the door than the seat (y 0.392) and ~3 cm higher than the
# first reading. The cluster sits under the visor with its top edge level with the screen's.
WHEEL_Y = 0.404
WHEEL_C = (0.846, WHEEL_Y, 1.006)
WHEEL_TILT = math.radians(17.0)

CLUSTER_C = (0.958, WHEEL_Y - 0.009, 1.062)
CLUSTER_W, CLUSTER_H = 0.322, 0.098
CLUSTER_TILT = math.radians(22.0)

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.220, 0.585
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -0.900, 0.640, 0.390

DASH_HALF = 0.760                  # the dash's ends, at the door cards
MIRROR_C = (0.560, 0.000, 1.430)   # the frameless rear-view mirror, hung from the header

CREAM = (0.560, 0.545, 0.495)      # cream Nappa, perforated
TAUPE = (0.150, 0.118, 0.112)      # mocha leather (door rails, seat shrouds)
TAUPE_TOP = (0.168, 0.140, 0.134)  # the dash top's finer grain, a shade lighter
SUEDE = (0.430, 0.418, 0.380)      # the headliner
CARPET = (0.088, 0.066, 0.060)
ROSE_GOLD = (0.62, 0.36, 0.27)


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_glass(x, y):
    """Height of the windscreen (the body's upper surface) at (x, |y|)."""
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.68)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def _perf_image(name, color, maps):
    """Perforated Nappa's base colour: the colour with the holes darkened (the
    perforation mask), baked to pixels so it survives glTF."""
    import numpy as np
    from carkit.textures import TEX_DIR
    import os
    msk = maps["perf_zx_mask"]
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


def perforation_maps(size=512, pitch_px=32, radius=0.13, strength=9.0):
    """The cream leather's perforation: ~1 mm round holes on a ~4 mm hex pitch (the seat
    photographs show a fine regular dot field)."""
    import numpy as np
    from carkit import surfacemaps as SM
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.04, 0.0, 1.0)
    nrm = SM._image("T_PerfZX_Normal", SM.height_to_normal(-hole, strength / size * 60.0),
                    filename="t_perf_zx_normal.png")
    mask = np.repeat((1.0 - 0.78 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_PerfZX_Mask", mask, non_color=True, filename="t_perf_zx_mask.png")
    return nrm, msk


def perforated(name, color, maps, tile=0.064):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.46, specular=0.5, coat=0.10,
                  coat_rough=0.30, ior=1.45, sheen=0.0)
    IM._textured(nt, b, maps["perf_zx"], tile, 0.7)
    _mapped_image(nt, b, _perf_image("T_Perf_" + name[4:], color, maps), tile, "Base Color")
    return m


def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    maps["perf_zx"], maps["perf_zx_mask"] = perforation_maps()
    lib = IM.build_library(accent=CREAM, maps=maps)
    lib["leather_white"] = perforated("INT_Leather_White", CREAM, maps)
    # smooth taupe leather (the seat shrouds, door rails and lower cards)
    lib["leather_taupe"] = IM.leather("INT_Leather_Taupe", TAUPE, maps, roughness=0.46, coat=0.08)
    lib["leather_accent"] = lib["leather_taupe"]
    lib["wheel_leather"] = lib["leather_white"]
    lib["headliner"] = IM.alcantara("INT_Headliner", SUEDE, maps, sheen=0.55)
    lib["dash_top"] = IM.leather("INT_Dash_Top", TAUPE_TOP, maps, roughness=0.52, coat=0.04,
                                 strength=0.7)
    m, nt, b = MB.mat("INT_Carpet_Taupe")
    MB.set_inputs(b, base=CARPET, metallic=0.0, roughness=0.96, specular=0.2, sheen=0.4)
    IM._textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m
    # the dark trim strip along the dash and the door cards: a glossy near-black with a fine
    # horizontal line pattern (the photographs: black with faint ribs), rose-gold edged
    m, nt, b = MB.mat("INT_Trim_Dark")
    MB.set_inputs(b, base=(0.012, 0.011, 0.011), metallic=0.0, roughness=0.20, coat=0.6,
                  coat_rough=0.10, ior=1.5)
    IM._textured(nt, b, maps["brushed"], SM.TILE["brushed"], 0.5)
    lib["trim_dark"] = m
    m, nt, b = MB.mat("INT_Rose_Gold")
    MB.set_inputs(b, base=ROSE_GOLD, metallic=1.0, roughness=0.20)
    lib["rose"] = m
    m, nt, b = MB.mat("INT_Charge_Pad")                # the wireless pad: a soft cream rubber
    MB.set_inputs(b, base=(0.36, 0.35, 0.31), metallic=0.0, roughness=0.70, specular=0.3)
    lib["charge"] = m
    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.10, coat=0.5,
                  coat_rough=0.08, ior=1.5)
    lib["band_glass"] = m
    m, nt, b = MB.mat("INT_Thread_Cream")
    MB.set_inputs(b, base=(0.42, 0.40, 0.35), metallic=0.0, roughness=0.55, sheen=0.3)
    lib["thread_cream"] = m
    return lib


# ------------------------------------------------------------------- dash
def _hood(y):
    """1 over the driver's cluster, 0 elsewhere, smooth: the dash's top rises into a visor
    over the cluster. It covers the cluster's body (|y - c| < 0.170) and is gone by 0.200, so
    it ends 2 cm short of the screen's left edge."""
    c = CLUSTER_C[1]
    return 1.0 - _smooth((abs(y - c) - 0.172) / 0.030)


DASH_COUNTS = [6, 6, 5, 6, 4, 4, 4, 2, 3, 5, 4, 4, 4, 4, 4]
# the panels, by section control point: the taupe top pad, the dark strip, the cream face,
# the lower dash (cream, then taupe at the knees)
DASH_PANELS = [("TopPad", 0, 6, "dash_top"), ("Band", 6, 8, "trim_dark"),
               ("Face", 8, 11, "leather_white"), ("Lower", 11, 15, "leather_white")]


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    h = _hood(y)
    zg = z_glass(1.195, y) - 0.003
    return [
        # over the cluster the top rises to a thin visor whose tip stands 3 cm above the display's
        # top edge, and its underside runs forward to a wall parallel to the display, so the
        # whole panel shows (the first visor's lip hung 4 cm down in front of it)
        (1.195, zg), (1.130, 1.092), (1.050, 1.086), (0.995 + 0.010 * h, 1.080 + 0.024 * h),
        (0.972 - 0.060 * h, 1.068 + 0.075 * h), (0.962 + 0.028 * h, 1.044 + 0.076 * h),
        (0.957, 1.002), (0.953, 0.960),
        (0.957, 0.936), (0.963, 0.860), (0.973, 0.760), (0.992, 0.690),
        (1.030, 0.625), (1.100, 0.555), (1.190, 0.470), (1.270, 0.400),
    ]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 112, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    # the rose-gold line along the dark strip's top edge
    p, n = sw.iso_col(sw.col(6), lift=0.0010)
    made.append(piping("int_dash_Rose", p, col, lib["rose"], r=0.0012, lateral=(1.0, 0.0, 0.0)))
    # a slim dark line along the cream face at the lower edge of the strip
    p, n = sw.iso_col(sw.col(9), lift=0.0008)
    made.append(piping("int_dash_Line", p, col, lib["trim_dark"], r=0.0016, lateral=(1.0, 0.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndL", list(sw.pts[0]), lib["leather_white"], (0.0, 1.0, 0.0)))
    made.append(F.ngon_cap(col, "int_dash_EndR", list(sw.pts[-1]), lib["leather_white"], (0.0, -1.0, 0.0)))
    made += build_dash_details(col, lib, sw)
    return made, sw


def build_dash_details(col, lib, sw):
    """The vent slot and the tweeter dome on the top pad at the glass, the HUD's window."""
    made = []
    # the vent: a wide curved slot centred on the car (c10_0048: an eyebrow with fine vanes)
    xv, zv = 1.065, 1.090
    rows = []
    for t in range(5):
        x = xv + 0.045 * (t / 4.0 - 0.5)
        rows.append([(x, 0.115 - 0.230 * j / 24.0, zv + 0.0030 * math.sin(math.pi * j / 24.0))
                     for j in range(25)])
    vt = grid_mesh("int_dash_Vent", rows, col, lib["satin"])
    M.orient(vt.data, lambda c: (0.0, 0.0, 1.0))
    made.append(vt)
    loop = [(xv - 0.026, 0.118 - 0.236 * j / 30.0, zv + 0.0042 * math.sin(math.pi * j / 30.0) + 0.0012)
            for j in range(31)]
    loop += [(xv + 0.026, 0.118 - 0.236 * (30 - j) / 30.0,
              zv + 0.0042 * math.sin(math.pi * (30 - j) / 30.0) + 0.0012) for j in range(31)]
    loop.append(loop[0])
    made.append(tube("int_dash_VentRim", loop, ellipse(0.0016, 0.0016, 6), col, lib["rose"],
                     lateral=(0.0, 0.0, 1.0)))
    # the tweeter dome at the glass (a chrome dome with a perforated cap)
    xd, yd = 1.150, -0.020
    made += F.disc(col, "int_dash_Tweeter", (xd, yd, 1.100 + 0.010), (0.0, 0.0, 1.0), 0.028,
                   lib["speaker"], dome=0.012, rim=0.0030, rim_mat=lib["chrome"])
    # the HUD window ahead of the driver, flush in the top pad
    made.append(F.box(col, "int_dash_HUD", (1.045, CLUSTER_C[1], 1.0905), (0.090, 0.200, 0.0016),
                      lib["screen_glass"], r=0.0008))
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b + 0.010,
                       0.020, 0.010, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())
    # the floating screen's mount: a slim arm to the dash face behind it
    made.append(F.box(col, "int_screen_arm", (SCREEN_C[0] + 0.030, SCREEN_Y, SCREEN_C[2] - 0.060),
                      (0.060, 0.120, 0.080), lib["satin"], r=0.010))
    # the cluster, a wide curved panel under the hood behind the wheel
    q = F.screen_quad("screen_cluster", CLUSTER_C, CLUSTER_W, CLUSTER_H, CLUSTER_TILT, col,
                      lift=0.0010)
    q.data.materials.append(F.screen_material())
    made.append(q)
    made.append(F.slab("int_cluster_body", CLUSTER_C, CLUSTER_W + 0.024, CLUSTER_H + 0.018, 0.026,
                       0.030, CLUSTER_TILT, col, lib["piano"]))
    # the button row under the screen: a slim black bar with five knurled keys (c10_0046)
    zb = SCREEN_C[2] - SCREEN_H / 2 - 0.030
    made.append(F.box(col, "int_screen_keys", (SCREEN_C[0] + 0.008, SCREEN_Y, zb), (0.030, 0.205, 0.026),
                      lib["piano"], r=0.008))
    for k in range(5):
        yk = SCREEN_Y + 0.080 - 0.040 * k
        made.append(F.box(col, "int_screen_key%d" % k, (SCREEN_C[0] - 0.010, yk, zb), (0.012, 0.030, 0.016),
                          lib["brushed"], r=0.003))
    return made


def cluster_image(path=None, w=800, h=240):
    """The cluster's resting display, laid out as c10_0002 shows it: dark, speed and a gear
    letter on the left, the car and range figures on the right. Generated pixels."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.010, 0.012, 0.018)
    white = np.array([0.86, 0.88, 0.92])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c
    s = 0.045 * h
    sx, sy = 0.08 * w, 0.28 * h
    # "0" for the speed
    rect(sx, sx + 3 * s, sy, sy + s * 0.55, white)
    rect(sx, sx + 3 * s, sy + 6.45 * s, sy + 7 * s, white)
    rect(sx, sx + s * 0.55, sy, sy + 7 * s, white)
    rect(sx + 2.45 * s, sx + 3 * s, sy, sy + 7 * s, white)
    # the gear letter P
    gx = 0.08 * w
    gy = 0.80 * h
    rect(gx, gx + s * 0.40, gy, gy + 3.0 * s, white * 0.8)
    rect(gx, gx + 1.8 * s, gy, gy + s * 0.40, white * 0.8)
    rect(gx, gx + 1.8 * s, gy + 1.3 * s, gy + 1.7 * s, white * 0.8)
    rect(gx + 1.4 * s, gx + 1.8 * s, gy, gy + 1.7 * s, white * 0.8)
    # the car, from above-behind, in the middle
    cx, cy = 0.50 * w, 0.52 * h
    body = (((xx - cx) / (0.07 * w)) ** 2 + ((yy - cy) / (0.28 * h)) ** 2 < 1.0)
    img[body] = white * 0.55
    # four figures at the right (tyre pressures)
    for (fx, fy) in ((0.70, 0.30), (0.88, 0.30), (0.70, 0.62), (0.88, 0.62)):
        rect(fx * w, fx * w + 0.08 * w, fy * h, fy * h + 0.05 * h, white * 0.70)
    out = path or os.path.join(TEX_DIR, "cluster_zx.png")
    im = bpy.data.images.get("T_Cluster_ZX") or bpy.data.images.new("T_Cluster_ZX", w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = img[::-1]
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = out
    im.file_format = 'PNG'
    im.save()
    return out


# ---------------------------------------------------------- steering wheel
ZEEKR_7X_WHEEL = dict(
    # a squircle rim, 0.386 x 0.372 outside (c10_0001, c10_0002): a superellipse of exponent 3 on
    # the centreline (half-sizes a, b) with a 35 mm thick rim all round; "radius" is the spokes'
    # reach, and flat_top/flat_bottom the plate under the hub's
    radius=0.175, loop=dict(a=0.175, b=0.1685, n=3.0),
    flat_bottom=-0.1685, flat_top=0.1685, section=(0.0175, 0.0205),
    grip_swell=-0.03,
    # taupe over the top from 37 to 144 degrees, cream down the sides and bottom (c10_0002)
    segments=[(37.0, 144.0, "leather_taupe"), (144.0, 397.0, "leather_white")],
    marker=None,                 # the top is taupe already: a taupe 12 o'clock band is invisible
    # the hub and the two pods are taupe leather (c10_0006-8), the pods edged in a chrome bezel
    hub=dict(w=0.114, h=0.114, sides=36, r_corner=0.0, dome=0.009, depth=0.05,
             pad_role="leather_taupe", housing_role="leather_taupe"),
    spokes=dict(v=0.0, h=0.064, t=0.026, u_in=0.056, pad=(0.092, 0.058), frame="chrome",
                pad_role="leather_taupe", body_role="leather_taupe"),
    lower_spoke=None,            # the U plate below the hub is built here (build_wheel)
    buttons=[],
    logo=None,
)


def _tube_path(fr, pts, w, name, col, mat, r):
    """A tube of radius r through wheel-plane points (u, v), at height w over the hub plane,
    densified so the bevel of a corner reads."""
    path = []
    for i in range(len(pts) - 1):
        A, B = Vector(fr.p(pts[i][0], pts[i][1], w)), Vector(fr.p(pts[i + 1][0], pts[i + 1][1], w))
        path += [tuple(A.lerp(B, t / 6.0)) for t in range(6)]
    path.append(tuple(fr.p(pts[-1][0], pts[-1][1], w)))
    return tube(name, path, ellipse(r, r, 6), col, mat, lateral=tuple(fr.A))


def build_wheel(col, lib):
    from carkit.interior import steering as ST
    from carkit.interior import fittings as F
    made, fr = ST.wheel(col, lib, ZEEKR_7X_WHEEL, WHEEL_C, WHEEL_TILT)
    pitch = WHEEL_TILT
    dome = ZEEKR_7X_WHEEL["hub"]["dome"]
    lift = 0.0215 + dome * 0.97
    # the maker's mark on the hub: a silver block-letter frame with the Z-step inside (c10_0006)
    hw, hh = 0.025, 0.031
    frame = [(-hw, hh), (hw, hh), (hw, -hh), (-hw, -hh), (-hw, hh)]
    made.append(_tube_path(fr, frame, lift, "int_wheel_mark", col, lib["chrome"], 0.0021))
    zz = [(-0.013, 0.018), (0.014, 0.018), (-0.014, -0.018), (0.013, -0.018)]
    made.append(_tube_path(fr, zz, lift, "int_wheel_mark_Z", col, lib["chrome"], 0.0017))
    # the pods: a dark recess in the bezel, the rocker plate with its knurled roller nearest the
    # hub, two small keys toward the rim (c10_0006, c10_0007)
    for s, tag in ((1.0, "R"), (-1.0, "L")):
        uc = s * 0.110
        w0 = 0.0198

        def at(u, v, w):
            return fr.p(u, v, w)
        made.append(F.box(col, "int_wheel_recess" + tag, at(uc, 0.0, w0 + 0.0008), (0.0016, 0.082, 0.048),
                          lib["piano"], r=0.0, pitch=pitch))
        made.append(F.box(col, "int_wheel_rocker" + tag, at(s * 0.098, 0.0, w0 + 0.0030),
                          (0.0044, 0.056, 0.036), lib["leather_taupe"], r=0.0035, pitch=pitch))
        made.append(F.box(col, "int_wheel_roller" + tag, at(s * 0.098, 0.0, w0 + 0.0060),
                          (0.0060, 0.016, 0.020), lib["piano"], r=0.0025, pitch=pitch))
        for k, vk in enumerate((0.0105, -0.0105)):
            made.append(F.box(col, "int_wheel_key%s%d" % (tag, k), at(s * 0.139, vk, w0 + 0.0028),
                              (0.0040, 0.022, 0.017), lib["leather_taupe"], r=0.0030, pitch=pitch))
    # the lower spoke: a taupe plate from under the hub to the rim's flat bottom, a chrome U in it
    # (c10_0002)
    top, bot = -0.060, ZEEKR_7X_WHEEL["flat_bottom"] + 0.006
    rows = []
    for i in range(9):
        t = i / 8.0
        v = top + (bot - top) * t
        hw_ = 0.052 + 0.018 * t * t
        row = []
        for j in range(9):
            u = -hw_ + 2.0 * hw_ * j / 8.0
            row.append(fr.p(u, v, 0.0105 + 0.004 * (1.0 - (u / hw_) ** 2) * (1.0 - 0.4 * t)))
        rows.append(row)
    plate = grid_mesh("int_wheel_lower", rows, col, lib["leather_taupe"])
    M.orient(plate.data, lambda c: tuple(fr.A))
    made.append(plate)
    u_half = 0.030
    arc = [(u_half * math.cos(math.pi * (1.0 - k / 8.0)), -0.108 - 0.022 * math.sin(math.pi * (1.0 - k / 8.0)))
           for k in range(9)]
    pts = [(-u_half, -0.080), (-u_half, -0.108)] + arc[1:-1] + [(u_half, -0.108), (u_half, -0.080)]
    made.append(_tube_path(fr, pts, 0.0150, "int_wheel_U", col, lib["chrome"], 0.0022))
    # the stalks either side of the column
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        a0 = Vector(fr.p(side * -0.045, 0.030, -0.070))
        b0 = Vector(fr.p(side * -0.125, 0.036, -0.045))
        made.append(tube("int_wheel_stalk" + tag, [tuple(a0.lerp(b0, t / 8.0)) for t in range(9)],
                         ellipse(0.0065, 0.0065, 10), col, lib["leather_taupe"], lateral=tuple(fr.A),
                         scale=lambda s: (1.0 - 0.25 * s, 1.0 - 0.25 * s)))
    return made


# ------------------------------------------------------------------ seats
def _seat_spec(k=1.0):
    """The front bucket (the SU7's, carkit.interior.seat) in cream with a taupe shell: the
    cushion and backrest in perforated cream Nappa. The 7X's headrest is a separate pillow on
    two posts above the shoulders (c3_0002), so the backrest's spine stops at the shoulders
    (the SU7's carries its headrest on over the top) and the open top is capped (`end_cap`).

    `k` scales the backrest's height: 1.0 is the spine as drawn from the SU7 (shoulders 0.70 m above the bight, which put the
    front headrest's top at z 1.568, through the headliner at 1.553); the front seats use FRONT_BACK_K, the rear ones
    (_rear_spec) their own 0.86."""
    from carkit.interior import seat as SE
    import copy
    sp = copy.deepcopy(SE.SU7_ULTRA_FRONT)
    base = [(0.0, 0.0), (-0.045, 0.0957), (-0.13, 0.286), (-0.20, 0.4576), (-0.240, 0.556),
            (-0.272, 0.640), (-0.288, 0.676), (-0.294, 0.694), (-0.297, 0.700)]
    sp["backrest"]["spine"] = [(x * k, z * k) for (x, z) in base]
    sp["backrest"]["end_cap"] = True
    sp["backrest"]["half_w"] = Curve([(0.0, 0.262), (0.45, 0.272), (0.78, 0.262), (0.90, 0.244),
                                      (1.0, 0.200)], mode="pchip")
    sp["backrest"]["bolster"] = Curve([(0.0, 0.55), (0.30, 1.0), (0.58, 0.75), (0.80, 0.35),
                                       (1.0, 0.0)], mode="pchip")
    sp["backrest"]["centre_half"] = Curve([(0.0, 0.135), (0.8, 0.130), (1.0, 0.100)], mode="pchip")
    sp["cushion"]["bolster_h"] = 0.040
    sp["backrest"]["bolster_h"] = 0.075
    sp["mats"] = dict(centre="leather_white", crown="leather_white", face="leather_white",
                      shell="leather_taupe", piping="leather_white", stitch="thread_cream",
                      base="leather_taupe")
    sp["stitch_half_gap"] = 0.012
    # the headrest pillow, in seat-local coordinates (x back negative, z up from the bight)
    sp["headrest"] = dict(w=0.318, h=0.235, t=0.098, r=0.058, gap=0.045, top=(-0.297 * k, 0.700 * k))
    return sp


# the front backrest's height against the SU7-drawn spine: the headrest's top then stands 0.89 m above the bight
# (z 1.473), 8 cm under the headliner (1.553) as a real seat's does, instead of 0.98 m through it
FRONT_BACK_K = 0.88


def _rear_spec():
    """The rear seats: the full-height seat spine, backrest 14 % shorter, the headrest a smaller pillow."""
    import copy
    sp = copy.deepcopy(_seat_spec(1.0))
    sp["backrest"]["spine"] = [(x * 0.95, z * 0.86) for (x, z) in sp["backrest"]["spine"]]
    hr = sp["headrest"]
    sp["headrest"] = dict(w=0.285, h=0.175, t=0.086, r=0.050, gap=0.040,
                          top=(hr["top"][0] * 0.95, hr["top"][1] * 0.86))
    return sp


POLE = 0.04          # a pillow's pole ring, as a fraction of its rim


def pillow(col, name, c, w, h, t, r, mat, tilt, n_in=6):
    """A puffed rounded-rectangle cushion (a headrest) centred at c, facing +x tilted by
    `tilt` (negative: its face looks up as the seat reclines): rings from a centre point out
    to the rim and back."""
    loop = F.round_rect_xy(-w / 2, w / 2, -h / 2, h / 2, r)
    ct, st = math.cos(tilt), math.sin(tilt)

    def ring(s, d):
        return [(c[0] + d * ct + v * s * st, c[1] - u * s, c[2] - d * st + v * s * ct)
                for (u, v) in loop]
    half = 0.5 * t
    rings = []
    for k in range(n_in + 1):                       # front: centre -> rim
        s = k / float(n_in)
        rings.append(ring(s, half * (0.62 + 0.38 * (1.0 - s * s))))
    rings[0] = ring(POLE, half * (0.62 + 0.38 * (1.0 - POLE * POLE)))      # a tiny ring, closed below by a polygon
    rings.append(ring(1.012, 0.20 * half))
    rings.append(ring(1.016, 0.0))
    rings.append(ring(1.012, -0.20 * half))
    for k in range(n_in + 1):                       # back: rim -> centre
        s = 1.0 - k / float(n_in)
        rings.append(ring(s, -half * (0.62 + 0.38 * (1.0 - s * s))))
    rings[-1] = ring(POLE, -half * (0.62 + 0.38 * (1.0 - POLE * POLE)))
    ob = grid_mesh(name, rings, col, mat, wrap_t=True)
    # the two poles are polygons, not points: a point makes a fan of zero-area quads whose tangents are undefined, and the
    # normal map there drew a smooth, dot-free square on the back of every headrest
    import bmesh
    n = len(loop)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    last = len(bm.verts) - n
    bm.faces.new([bm.verts[j] for j in reversed(range(n))])
    bm.faces.new([bm.verts[last + j] for j in range(n)])
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda q: (q[0] - c[0], q[1] - c[1], q[2] - c[2]))
    return ob


def _headrest(col, lib, spec, origin, name):
    """A seat's separate headrest: the pillow, two posts to the backrest."""
    hr = spec["headrest"]
    xt, zt = hr["top"]
    recline = math.radians(22.0)
    dz = hr["gap"] + 0.5 * hr["h"]
    cx, cz = xt - dz * math.tan(recline), zt + dz
    c = (origin[0] + cx, origin[1], origin[2] + cz)
    made = [pillow(col, name + "_Head", c, hr["w"], hr["h"], hr["t"], hr["r"], lib["leather_white"],
                   -recline)]
    for k, sy in enumerate((-1.0, 1.0)):
        z0 = zt - 0.03
        z1 = cz - 0.5 * hr["h"] + 0.03
        q = (origin[0] + xt - 0.5 * (z1 + z0 - 2 * zt) * math.tan(recline) - 0.005,
             origin[1] + sy * 0.060, origin[2] + 0.5 * (z0 + z1))
        made.append(F.box(col, "%s_Post%d" % (name, k), q, (0.014, 0.014, z1 - z0), lib["piano"],
                          r=0.004, pitch=recline))
    return made


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        front = _seat_spec(FRONT_BACK_K)
        parts, cush, back = SE.seat(col, lib, front, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += _headrest(col, lib, front, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_" + tag)
        made += _seat_shroud(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), "int_seat_%s_base" % tag)
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, cush, back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
        made += _headrest(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z), "int_seat_" + tag)
    # the centre rear place: a narrower cushion and backrest between the two
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.22, 0.0, REAR_BIGHT_Z - 0.035),
                      (0.50, 0.30, 0.12), lib["leather_white"], r=0.035))
    made.append(F.box(col, "int_rear_centre_back", (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.27),
                      (0.14, 0.28, 0.54), lib["leather_white"], r=0.04, pitch=math.radians(-18)))
    # its headrest, a smaller pillow
    hr = rear["headrest"]
    made.append(pillow(col, "int_rear_centre_head",
                       (REAR_BIGHT_X - 0.19 - 0.04, 0.0, REAR_BIGHT_Z + 0.62), 0.24, 0.16, 0.080,
                       0.046, lib["leather_white"], -math.radians(18)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.18, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.62, 1.30, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["leather_taupe"], r=0.02))
    return made


def _seat_shroud(col, lib, origin, name):
    """The taupe shroud and rails under a front cushion, with its oval switch panel on the
    door side (c3_0002)."""
    x0, y0, z0 = origin
    made = [F.box(col, name, (x0 + 0.25, y0, 0.5 * (FLOOR_Z + z0 - 0.07)),
                  (0.56, 0.42, z0 - 0.07 - FLOOR_Z), lib["leather_taupe"], r=0.04)]
    side = 1.0 if y0 > 0 else -1.0
    made.append(F.box(col, name + "_sw", (x0 + 0.20, y0 + side * 0.212, z0 - 0.055),
                      (0.130, 0.012, 0.045), lib["piano"], r=0.014))
    return made


# ---------------------------------------------------------------- console
# Top centreline height, rear to front: the armrest lid, the step down to the pad deck and
# the crystal selector between them, the pad deck, the ramp up to the key row under the
# screen (c10_0046, c10_0048).
CONSOLE_TOP = Curve([
    (-0.235, 0.770), (-0.222, 0.830), (-0.205, 0.856), (-0.170, 0.866), (0.100, 0.868),
    (0.300, 0.868), (0.400, 0.862), (0.430, 0.852), (0.446, 0.832), (0.460, 0.810),
    (0.475, 0.801), (0.560, 0.800), (0.760, 0.801), (0.880, 0.804), (0.915, 0.820),
    (0.940, 0.846), (0.958, 0.862),
], mode="pchip")
CONSOLE_HW = 0.124
CONSOLE_X0, CONSOLE_X1 = -0.235, 0.958


def _console_stations():
    xs = []
    x = CONSOLE_X0
    while x < CONSOLE_X1:
        xs.append(x)
        dense = (x < -0.19) or (0.42 < x < 0.49) or (0.87 < x < 0.96)
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


def build_console(col, lib):
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _console_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_white"])
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.70)))
    made.append(ob)
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in
                                                      _console_section(xs[0])],
                           lib["leather_white"], (-1.0, 0.0, 0.0)))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.0015 * (1.0 - (y / (CONSOLE_HW - 0.020)) ** 2) + lift)

    # the black piano frame round the wireless pad, and the pad inside it
    outer = F.round_rect_xy(0.488, 0.892, -0.108, 0.108, 0.030)
    inner = F.round_rect_xy(0.502, 0.878, -0.094, 0.094, 0.022)
    frame = [top(x, y, 0.0016) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0016)]
    made.append(tube("int_console_frame", frame, ellipse(0.0032, 0.0028, 8), col, lib["piano"],
                     lateral=(0.0, 0.0, 1.0)))
    pad = [top(x, y, 0.0006) for (x, y) in inner]
    verts = [top(0.690, 0.0, 0.0006)] + pad
    faces = [[0, 1 + j, 1 + (j + 1) % len(pad)] for j in range(len(pad))]
    pd = M.obj("int_console_pad", verts, faces, col, lib["charge"])
    M.orient(pd.data, lambda c: (0.0, 0.0, 1.0))
    made.append(pd)
    # the crystal selector: a knurled glass bar across the step between pad and armrest
    made.append(F.box(col, "int_console_selector", (0.452, 0.0, CONSOLE_TOP(0.452) + 0.008),
                      (0.020, 0.118, 0.012), lib["brushed"], r=0.004))
    # the black frame round the armrest lid (c10_0046: a dark bezel round the cream lid)
    outer = F.round_rect_xy(-0.222, 0.420, -0.112, 0.112, 0.030)
    frame = [top(x, y, 0.0016) for (x, y) in outer] + [top(outer[0][0], outer[0][1], 0.0016)]
    made.append(tube("int_console_lid_frame", frame, ellipse(0.0022, 0.0022, 8), col, lib["piano"],
                     lateral=(0.0, 0.0, 1.0)))
    return made
