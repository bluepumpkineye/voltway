"""Luxeed RX cabin - hardpoints from the camera-matched cabin photograph,
built with carkit.interior.

References (blender/reference/luxeed-rx/interior/):

    cabin_front_black.jpg      Luxeed's straight-on press render (black and
                               tan trim), solved as camera "cabin_front"
                               (rx_ref_match, rx_camsolve.solve_cabin)
    passenger34_high_white.jpg showroom, from over the passenger door
    cabin_wide_rear_white.jpg  motor show, ultra-wide from the rear seat
    driver34_night_white.jpg   the driver's side at night (ambient light)
    seats_rear34_cream.webp    the seats from the rear door (cream/burgundy)

The trim built is the white-and-red one (three of the five photographs):
white perforated Nappa (dash band, door bands, seats), a red leather roll
under it running door to door, red piping and a red band down each seat,
black leather and soft-touch elsewhere, a dark suede headliner round a
panoramic glass roof.

Read through cabin_front (refmatch.on_plane / on_mesh; the numbers are in
rx_camsolve.solve_cabin's notes):

    centre screen   (0.446, 0, 1.077), 16.1 in 16:10, leaning back 9.9 deg:
                    solved with the camera, from its corners
    black band      the dash's glass band ends at the doors 0.61 (top, z 1.10)
                    and 0.59 (bottom, z 1.01) - a face leaning back ~10 deg
    upper dash      it rises steeply from the band's lip to the windscreen:
                    the visible glass ends at z 1.17-1.18 (cast onto the glass)
    accent roll     z ~0.93 at the doors (0.555)
    steering wheel  rim top (0.366, 1.195) and bottom (0.292, 0.845) on the
                    plane y 0.41 (a 376 mm rim at 0.41 fits its image width)
    console         the vent under the screen, the charging area, the lever,
                    a brushed band and the forged panel read on assumed
                    heights (camera rays through the centreline)

Axes: +X forward, +Y left (the driver's side - China is LHD), +Z up.
"""
import math

import bpy
from mathutils import Vector

import rx_surface as S
import rx_panels as PN
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "RX_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.360                 # underbody 0.195 + the SU7's 0.17 of floor structure
DRIVER_Y = 0.410
PASS_Y = -0.410

SCREEN_C = (0.446, 0.000, 1.077)
SCREEN_W, SCREEN_H = 0.347, 0.217          # 16.1 in, 16:10 active area
SCREEN_TILT = math.radians(9.9)            # top leans away from the occupants
SCREEN_BORDER = 0.006

WHEEL_C = (0.330, DRIVER_Y, 1.020)
WHEEL_TILT = math.radians(20.0)

DASH_HALF = 0.760               # the dash's ends, at the door cards
BAND_TILT = math.radians(9.9)   # the black glass band leans back like the screen

CLUSTER_C = (0.6085, DRIVER_Y, 1.059)      # 8.88 in, in the band behind the wheel
PASSENGER_C = (0.6085, -0.460, 1.059)      # 8.88 in, in the band ahead of the passenger
SMALL_W, SMALL_H = 0.205, 0.078

FRONT_BIGHT_X, FRONT_BIGHT_Z = -0.260, 0.585
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.200, 0.610, 0.370

MIRROR_C = (0.250, 0.000, 1.350)           # frameless, 225 mm (cabin_front: u 663-930)

ACCENT_RED = (0.300, 0.018, 0.026)         # Luxeed red Nappa, a crimson (#C8102E family)
WHITE = (0.660, 0.640, 0.600)              # white Nappa


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_glass(x, y):
    """Height of the windscreen (the body's upper surface) at (x, |y|)."""
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.68)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def _perf_image(name, color, maps):
    """White perforated Nappa's base colour: the colour with the holes
    darkened (carkit.surfacemaps' perforation mask), baked to pixels so it
    survives glTF."""
    import numpy as np
    from carkit.textures import TEX_DIR
    import os
    msk = maps["perf_rx_mask"]
    w, h = msk.size
    a = np.array(msk.pixels[:], np.float32).reshape(h, w, 4)
    out = np.ones_like(a)
    for c in range(3):
        # linear colour x mask, stored sRGB so the PNG holds it faithfully
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
    """Perforated Nappa's holes: ~1.1 mm round holes on a 4 mm hex pitch (the
    catalogue's speaker perforation is 2.4 mm holes - far too coarse for
    leather)."""
    import numpy as np
    from carkit import surfacemaps as SM
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.04, 0.0, 1.0)
    nrm = SM._image("T_PerfRX_Normal", SM.height_to_normal(-hole, strength / size * 60.0),
                    filename="t_perf_rx_normal.png")
    mask = np.repeat((1.0 - 0.80 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_PerfRX_Mask", mask, non_color=True, filename="t_perf_rx_mask.png")
    return nrm, msk


def perforated(name, color, maps, tile=0.064):
    """Perforated Nappa: ~4 mm hole pitch (the SU7 perforation map is 16
    holes a tile), holes darkened in the base colour and dimpled in the
    normal map."""
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.44, specular=0.5, coat=0.10,
                  coat_rough=0.30, ior=1.45, sheen=0.0)
    IM._textured(nt, b, maps["perf_rx"], tile, 0.7)
    _mapped_image(nt, b, _perf_image("T_Perf_" + name[4:], color, maps), tile, "Base Color")
    return m


def forged_image(name="T_Forged", size=1024, seed=5):
    """The console's forged panel: dark grey stone with light grey patches
    and fine silver flakes (passenger34_high_white, cabin_wide_rear_white;
    the black car's press render shows the same flakes on black)."""
    import numpy as np
    import os
    from carkit import surfacemaps as SM
    from carkit.textures import TEX_DIR
    big = SM.band_noise(size, 6.0, 18.0, seed)
    mid = SM.band_noise(size, 30.0, 70.0, seed + 1)
    fine = SM.band_noise(size, 120.0, 260.0, seed + 2)
    patch = np.clip((big + 0.45 * mid - 0.55) / 0.35, 0.0, 1.0)
    flake = np.clip((fine + 0.6 * mid - 2.1) / 0.3, 0.0, 1.0)
    v = 0.030 + 0.090 * patch + 0.30 * flake
    rgb = np.stack([v, v * 1.01, v * 1.04], axis=-1)
    srgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)
    im = bpy.data.images.get(name) or bpy.data.images.new(name, size, size)
    if tuple(im.size) != (size, size):
        im.scale(size, size)
    px = np.ones((size, size, 4), np.float32)
    px[..., :3] = srgb
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = os.path.join(TEX_DIR, "forged_rx.png")
    im.file_format = 'PNG'
    im.save()
    return im


def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    maps["perf_rx"], maps["perf_rx_mask"] = perforation_maps()
    lib = IM.build_library(accent=ACCENT_RED, maps=maps)
    lib["leather_white"] = perforated("INT_Leather_White", WHITE, maps)
    lib["wheel_leather"] = lib["leather_black"]
    # the headliner and pillars: a dark grey suede, lighter than the SU7's
    lib["headliner"] = IM.alcantara("INT_Headliner", (0.030, 0.030, 0.033), maps, sheen=0.6)
    m, nt, b = MB.mat("INT_Forged")
    MB.set_inputs(b, base=(0.08, 0.08, 0.085), metallic=0.0, roughness=0.18, coat=1.0,
                  coat_rough=0.04, ior=1.5)
    _mapped_image(nt, b, forged_image(), 0.22, "Base Color")
    lib["forged"] = m
    m, nt, b = MB.mat("INT_Charge_Grey")          # the phone pad area, satin mid grey
    MB.set_inputs(b, base=(0.10, 0.10, 0.105), metallic=0.0, roughness=0.45, specular=0.4)
    lib["charge"] = m
    # the dash top: a dark matte soft-touch skin (passenger34_high: no sheen,
    # a fine grain), not the gloss-coated Nappa
    m, nt, b = MB.mat("INT_Dash_Top")
    MB.set_inputs(b, base=(0.018, 0.018, 0.019), metallic=0.0, roughness=0.78, specular=0.35,
                  coat=0.0, sheen=0.15)
    IM._textured(nt, b, maps["leather"], 0.10, 0.6)
    lib["dash_top"] = m
    # the dash's black glass band: glass, but not a mirror - in the photographs
    # it holds soft reflections, where the screen glass (INT_Screen_Glass)
    # mirrored the sky through the side windows as a white slab
    m, nt, b = MB.mat("INT_Band_Glass")
    MB.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.10, coat=0.5,
                  coat_rough=0.08, ior=1.5)
    lib["band_glass"] = m
    return lib


# ------------------------------------------------------------------- dash
# Section in (x, z) at |y| < DASH_HALF, from the windscreen down to the
# firewall. Control points 0-2 follow the glass 14-16 mm under it (they are
# computed per station, see dash_section); 3 is the brow, 3-6 the steep upper
# face, 6-8 the black glass band, 8-11 the white band, 11-13 the recess behind
# the red roll, 13-18 the lower dash.
DASH_SECTION = [
    (0.800, None), (0.740, None), (0.690, None), (0.668, None),
    (0.645, 1.138), (0.626, 1.116), (0.616, 1.105),
    (0.608, 1.059), (0.600, 1.013),
    (0.593, 0.990), (0.583, 0.966), (0.574, 0.950),
    (0.578, 0.936), (0.586, 0.920),
    (0.610, 0.862), (0.650, 0.780), (0.720, 0.690), (0.810, 0.620), (0.960, 0.560),
]
DASH_COUNTS = [8, 6, 4, 4, 4, 3, 5, 5, 3, 3, 3, 2, 2, 5, 6, 6, 6, 8]
DASH_PANELS = [("TopPad", 0, 6, "dash_top"), ("Band", 6, 8, "band_glass"),
               ("White", 8, 11, "leather_white"), ("Recess", 11, 13, "satin"),
               ("Lower", 13, 18, "leather_black")]
GLASS_GAP = (0.016, 0.014, 0.014, 0.020)


def dash_section(i, s):
    y = DASH_HALF * (1.0 - 2.0 * s)
    out = []
    for k, (x, z) in enumerate(DASH_SECTION):
        if z is None:
            z = z_glass(x, y) - GLASS_GAP[k]
            if k == 3:
                z = max(z, 1.128)
        out.append((x, z))
    return out


def dash_y(sw, i):
    return sw.spine[i][1]


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 96, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        made.append(sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1)))
    # chrome line along the band's bottom edge
    p, n = sw.iso_col(sw.col(8), lift=0.0012)
    made.append(piping("int_dash_Chrome", p, col, lib["chrome"], r=0.0018,
                       lateral=(1.0, 0.0, 0.0)))
    # the red roll: a padded welt ~22 mm tall under the white band, door to door
    roll = [(0.566, y, 0.939) for y in [DASH_HALF - 2 * DASH_HALF * k / 80.0 for k in range(81)]]
    made.append(tube("int_dash_Roll", roll, ellipse(0.0105, 0.0112, 16), col,
                     lib["leather_accent"], lateral=(1.0, 0.0, 0.0)))
    # at each end it turns down the dash's end beside the door
    # (passenger34_high_white), following the lower dash's face
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        yy = side * (DASH_HALF - 0.012)
        path = smooth_path([(0.566, side * (DASH_HALF - 0.030), 0.939), (0.568, yy, 0.925),
                            (0.584, yy, 0.880), (0.612, yy, 0.820), (0.648, yy, 0.755),
                            (0.700, yy, 0.690)], 24)
        made.append(tube("int_dash_RollEnd" + tag, path, ellipse(0.0105, 0.0105, 16), col,
                         lib["leather_accent"], lateral=(0.0, 1.0, 0.0)))
    # stitching along the roll's crown, and the ambient light guide under it
    made.append(tube("int_dash_Ambient", [(0.580, y, 0.9255) for (_, y, _) in roll],
                     ellipse(0.0016, 0.0016, 6), col, lib["ambient"], lateral=(1.0, 0.0, 0.0)))
    # the HUD's window on the upper face ahead of the driver (driver34_night:
    # a wide dark rectangle close to the glass)
    ys = [sw.spine[i][1] for i in range(len(sw.spine))]
    i0 = min(range(len(ys)), key=lambda i: abs(ys[i] - 0.545))
    i1 = min(range(len(ys)), key=lambda i: abs(ys[i] - 0.275))
    made.append(sw.mesh("int_dash_HUD", col, lib["screen_glass"], i0=i0, i1=i1,
                        j0=sw.col(3) + 1, j1=sw.col(5) - 1, offset=0.0015))
    made += build_band_vents(col, lib, sw)
    made += build_dash_ends(col, lib, sw)
    # the red "RX" on the white band at the passenger's end (passenger34_high)
    made.append(_badge_rx(col, lib, (0.5855, -0.655, 0.978)))
    # the round dome and speaker grille on the dash top right of the screen
    # (passenger34_high_white)
    made += build_dash_speaker(col, lib)
    return made, sw


def build_band_vents(col, lib, sw):
    """A vertical vent at each end of the black band (passenger34_high:
    chrome surround, vertical vanes)."""
    made = []
    ys = [sw.spine[i][1] for i in range(len(sw.spine))]
    for side in (1.0, -1.0):
        ya, yb = side * 0.668, side * 0.724
        ia = min(range(len(ys)), key=lambda i: abs(ys[i] - ya))
        ib = min(range(len(ys)), key=lambda i: abs(ys[i] - yb))
        i0, i1 = min(ia, ib), max(ia, ib)
        j0, j1 = sw.col(6) + 1, sw.col(8) - 1
        made.append(sw.mesh("int_dash_Vent%s" % ("L" if side > 0 else "R"), col, lib["satin"],
                            i0=i0, i1=i1, j0=j0, j1=j1, offset=0.0010))
        # the chrome surround round the vent's opening
        loop = ([sw.pts[i][j0] for i in range(i0, i1 + 1)] +
                [sw.pts[i1][j] for j in range(j0, j1 + 1)] +
                [sw.pts[i][j1] for i in range(i1, i0 - 1, -1)] +
                [sw.pts[i0][j] for j in range(j1, j0 - 1, -1)])
        loop = [tuple(Vector(q) + Vector((-0.0022, 0.0, 0.0))) for q in loop]
        made.append(tube("int_dash_VentRim%s" % ("L" if side > 0 else "R"), loop,
                         ellipse(0.0022, 0.0022, 6), col, lib["chrome"], lateral=(1.0, 0.0, 0.0)))
        for k in range(1, 4):
            i = i0 + (i1 - i0) * k // 4
            a = Vector(sw.pts[i][j0]) + Vector((-0.004, 0.0, -0.004))
            b = Vector(sw.pts[i][j1]) + Vector((-0.004, 0.0, 0.004))
            made.append(tube("int_dash_Vane%s%d" % ("L" if side > 0 else "R", k),
                             [tuple(a.lerp(b, t / 8.0)) for t in range(9)],
                             [(p[0] * 0.0008, p[1] * 0.006) for p in ellipse(1.0, 1.0, 8)], col,
                             lib["chrome"], lateral=(1.0, 0.0, 0.0)))
    return made


def build_dash_ends(col, lib, sw):
    """Close the dash's ends against the door cards."""
    return [F.ngon_cap(col, "int_dash_End" + tag, list(sw.pts[idx]), lib["leather_black"],
                       (0.0, s, 0.0))
            for idx, tag, s in ((0, "L", 1.0), (len(sw.pts) - 1, "R", -1.0))]


def _badge_rx(col, lib, at):
    t = M.text_mesh("int_dash_RX", "RX", 0.024, col, lib["leather_accent"], extrude=0.0006,
                    bold=True, italic=True, resolution=4)
    # face the occupants (-X), reading left to right from the cabin
    from mathutils import Matrix
    U = Vector((0.0, -1.0, 0.0))                       # text +X -> world -Y
    Vv = Vector((math.sin(math.radians(24.0)), 0.0, math.cos(math.radians(24.0))))
    A = U.cross(Vv)
    Mx = Matrix((tuple(U), tuple(Vv), tuple(A))).transposed().to_4x4()
    Mx.translation = Vector(at)
    t.matrix_world = Mx
    return t


def build_dash_speaker(col, lib):
    made = []
    # the oval grille lying on the pad under the glass, outboard of the dome
    x, y = 0.708, -0.300
    rows = []
    for k in range(6):
        s = 1.0 - k / 5.0
        ring = []
        for j in range(32):
            px = x + 0.040 * s * math.cos(2 * math.pi * j / 32)
            py = y + 0.100 * s * math.sin(2 * math.pi * j / 32)
            ring.append((px, py, z_glass(px, py) - 0.0120))
        rows.append(ring)
    g = grid_mesh("int_dash_Grille", rows, col, lib["speaker"], wrap_t=True)
    M.orient(g.data, lambda c: (0.0, 0.0, 1.0))
    made.append(g)
    # the dome: a short chrome-rimmed cylinder with a dark glass top, on the
    # steep upper face where there is room under the glass
    xd, yd = 0.640, -0.205
    zb = 1.128
    made += F.disc(col, "int_dash_Dome", (xd, yd, zb + 0.034), (0.0, 0.0, 1.0), 0.024,
                   lib["screen_glass"], dome=0.004, rim=0.0028, rim_mat=lib["chrome"])
    made.append(tube("int_dash_DomeBody", [(xd, yd, zb - 0.012 + 0.046 * t / 6.0) for t in range(7)],
                     ellipse(0.0255, 0.0255, 24), col, lib["satin"], lateral=(1.0, 0.0, 0.0)))
    return made


# ---------------------------------------------------------------- screens
def build_screens(col, lib):
    made = []
    b = SCREEN_BORDER
    made.append(F.slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b,
                       0.018, 0.010, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(F.screen_material())
    # the rotating screen's hub behind its centre, on an arm to the band
    ct, st = math.cos(SCREEN_TILT), math.sin(SCREEN_TILT)
    back = Vector((SCREEN_C[0] + 0.018 * ct, 0.0, SCREEN_C[2] - 0.018 * st))
    made.append(F.box(col, "int_screen_arm", tuple(back.lerp(Vector((0.600, 0.0, 1.062)), 0.5)),
                      (0.600 - back.x, 0.090, 0.060), lib["piano"], r=0.012))
    # the cluster and the passenger display, flush in the black band; the
    # passenger display is off, as in the press render (dark glass)
    for name, c, mat in (("screen_cluster", CLUSTER_C, F.screen_material()),
                         ("screen_passenger", PASSENGER_C, lib["screen_glass"])):
        q = F.screen_quad(name, c, SMALL_W, SMALL_H, BAND_TILT, col, lift=0.0010)
        q.data.materials.append(mat)
        made.append(q)
    return made


def cluster_image(path=None, w=640, h=244):
    """The 8.88 in cluster's resting display, laid out as in the press render:
    dark, a gear block and speed on the left, a range bar, the car on the
    right. Generated pixels (no third-party UI is copied)."""
    import os
    import numpy as np
    from carkit.textures import TEX_DIR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[...] = (0.010, 0.013, 0.022)
    img += (0.012 * (1.0 - yy / h))[..., None] * np.array([0.6, 0.8, 1.0])
    white = np.array([0.86, 0.88, 0.92])

    def rect(x0, x1, y0, y1, c):
        img[(xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)] = c
    # the gear letter P (block strokes)
    gx, gy, s = 0.12 * w, 0.30 * h, 0.05 * h
    rect(gx, gx + s * 0.55, gy, gy + 7 * s, white)
    rect(gx, gx + 3 * s, gy, gy + s * 0.55, white)
    rect(gx, gx + 3 * s, gy + 3.2 * s, gy + 3.75 * s, white)
    rect(gx + 2.45 * s, gx + 3 * s, gy, gy + 3.75 * s, white)
    # speed "0" and its unit bar
    sx = 0.28 * w
    rect(sx, sx + 3 * s, gy, gy + s * 0.55, white)
    rect(sx, sx + 3 * s, gy + 6.45 * s, gy + 7 * s, white)
    rect(sx, sx + s * 0.55, gy, gy + 7 * s, white)
    rect(sx + 2.45 * s, sx + 3 * s, gy, gy + 7 * s, white)
    rect(sx + 3.6 * s, sx + 5.4 * s, gy + 6.2 * s, gy + 6.6 * s, white * 0.55)
    # range bar, part full, in the accent red
    rect(0.12 * w, 0.44 * w, 0.80 * h, 0.80 * h + 4, white * 0.25)
    rect(0.12 * w, 0.34 * w, 0.80 * h, 0.80 * h + 4, (0.78, 0.07, 0.12))
    # the car, side on: a low body and two wheels
    cx, cy = 0.73 * w, 0.58 * h
    body = (((xx - cx) / (0.17 * w)) ** 2 + ((yy - cy) / (0.085 * h)) ** 2 < 1.0) & (yy < cy + 0.05 * h)
    roof = (((xx - cx - 0.01 * w) / (0.09 * w)) ** 2 + ((yy - cy + 0.06 * h) / (0.08 * h)) ** 2 < 1.0)
    img[body | roof] = white * 0.75
    for wx in (cx - 0.105 * w, cx + 0.105 * w):
        img[((xx - wx) ** 2 + (yy - cy - 0.06 * h) ** 2) < (0.045 * h) ** 2] = (0.05, 0.05, 0.06)
    out = path or os.path.join(TEX_DIR, "cluster_rx.png")
    im = bpy.data.images.get("T_Cluster_RX") or bpy.data.images.new("T_Cluster_RX", w, h)
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
def build_wheel(col, lib):
    from carkit.interior import steering as ST
    made, fr = ST.wheel(col, lib, ST.LUXEED_RX, WHEEL_C, WHEEL_TILT)
    # stalks either side of the column (cabin_front: a wiper stalk left, the
    # gear stalk right, under the spokes)
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        a = Vector(fr.p(side * -0.045, 0.030, -0.070))
        b = Vector(fr.p(side * -0.125, 0.036, -0.045))
        made.append(tube("int_wheel_stalk" + tag, [tuple(a.lerp(b, t / 8.0)) for t in range(9)],
                         ellipse(0.0065, 0.0065, 10), col, lib["piano"], lateral=tuple(fr.A),
                         scale=lambda s: (1.0 - 0.25 * s, 1.0 - 0.25 * s)))
    return made


# ------------------------------------------------------------------ seats
def _rear_spec():
    """The rear seats: the front seat, backrest 16 % shorter so the head
    restraint clears the falling roof."""
    import copy
    from carkit.interior import seat as SE
    sp = copy.deepcopy(SE.LUXEED_RX_FRONT)
    sp["backrest"]["spine"] = [(x * 0.95, z * 0.84) for (x, z) in sp["backrest"]["spine"]]
    return sp


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        parts, cush, back = SE.seat(col, lib, SE.LUXEED_RX_FRONT,
                                    (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), name="int_seat_" + tag)
        made += parts
        made.append(SE.base(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), FLOOR_Z,
                            name="int_seat_%s_base" % tag))
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, cush, back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
    # the rear centre place between the two, and the bench's base
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.20, 0.0, REAR_BIGHT_Z - 0.03),
                      (0.46, 0.20, 0.12), lib["leather_white"], r=0.03))
    made.append(F.box(col, "int_rear_centre_back",
                      (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.27), (0.12, 0.20, 0.50),
                      lib["leather_white"], r=0.03, pitch=math.radians(-18)))
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.15, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.56, 1.30, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["satin"], r=0.02))
    return made


# ---------------------------------------------------------------- console
# Top centreline height, front to rear (cabin_front rays at y = 0 with
# heights chosen to suit the white car's photographs): the steep vent face
# under the screen, the charging area falling rearward past the lever, the
# brushed band and forged panel, a step down to the cupholders, the armrest.
CONSOLE_TOP = Curve([
    (-0.455, 0.700), (-0.445, 0.790), (-0.430, 0.818), (-0.405, 0.830), (-0.100, 0.833),
    (-0.040, 0.831), (-0.022, 0.823), (-0.013, 0.810), (-0.006, 0.801), (0.000, 0.800),
    (0.112, 0.800), (0.120, 0.803), (0.126, 0.812), (0.132, 0.824), (0.150, 0.830),
    (0.220, 0.845), (0.300, 0.856), (0.380, 0.866), (0.450, 0.875), (0.482, 0.879),
    (0.491, 0.886), (0.496, 0.903), (0.503, 0.918), (0.515, 0.925), (0.560, 0.928),
    (0.640, 0.930),
], mode="pchip")
CONSOLE_HW = 0.125
CUPS = [(0.058, 0.056, 0.041), (0.058, -0.056, 0.041)]      # (x, y, r)


def _console_stations():
    xs = []
    x = -0.455
    while x < 0.640:
        xs.append(x)
        dense = (-0.46 < x < -0.40) or (-0.05 < x < 0.14) or (0.47 < x < 0.53)
        x += 0.004 if dense else 0.012
    xs.append(0.640)
    return xs


def _console_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = CONSOLE_HW, 0.016
    pts = [(-hw, FLOOR_Z), (-hw, zt - 0.10), (-hw, zt - r)]
    for k in range(1, n_arc):
        a = math.pi - 0.5 * math.pi * k / n_arc
        pts.append((-hw + r + r * math.cos(a), zt - r + r * math.sin(a)))
    ny = 40
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
    ob = grid_mesh("int_console_body", rows, col, lib["leather_black"])
    # open the cupholders: drop top faces inside each cup circle
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.z > 0.78 and any((c.x - cx) ** 2 + (c.y - cy) ** 2 < (r - 0.0015) ** 2
                              for (cx, cy, r) in CUPS):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.70)))
    made.append(ob)
    # the rear face, with the rear vents
    rr = _console_section(xs[0])
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in rr],
                           lib["leather_black"], (-1.0, 0.0, 0.0)))
    zv = 0.64
    made.append(F.box(col, "int_console_rear_vent", (xs[0] - 0.004, 0.0, zv), (0.006, 0.17, 0.035),
                      lib["satin"], r=0.004))
    rim = [(xs[0] - 0.0075, y, z) for (y, z) in
           F.round_rect_xy(-0.088, 0.088, zv - 0.020, zv + 0.020, 0.010)]
    made.append(tube("int_console_rear_vent_rim", rim + [rim[0]], ellipse(0.0022, 0.0022, 6), col,
                     lib["chrome"], lateral=(1.0, 0.0, 0.0)))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.001 * (1.0 - (y / (CONSOLE_HW - 0.016)) ** 2) + lift)

    # the vent under the screen, with the hazard button
    xa, xb = 0.5005, 0.4935
    rows = []
    for t in range(7):
        x = xa + (xb - xa) * t / 6.0
        rows.append([(x - 0.0020, y, CONSOLE_TOP(x)) for y in [0.094 - 0.188 * j / 20.0
                                                              for j in range(21)]])
    vt = grid_mesh("int_console_vent", rows, col, lib["satin"])
    M.orient(vt.data, lambda c: (-1.0, 0.0, 0.4))
    made.append(vt)
    rim = ([rows[0][j] for j in range(21)] + [rows[t][20] for t in range(7)] +
           [rows[6][j] for j in range(20, -1, -1)] + [rows[t][0] for t in range(6, -1, -1)])
    rim = [tuple(Vector(p) + Vector((-0.0015, 0.0, 0.0))) for p in rim]
    made.append(tube("int_console_vent_rim", rim, ellipse(0.0020, 0.0020, 6), col, lib["chrome"],
                     lateral=(1.0, 0.0, 0.0)))
    xm = 0.5 * (xa + xb)
    made += F.disc(col, "int_console_hazard", (xm - 0.0045, 0.0, CONSOLE_TOP(xm)),
                   (-0.93, 0.0, 0.37), 0.0085, lib["button_red"], dome=0.002)
    # the chrome frame round the charging area and the forged panel
    outline = F.round_rect_xy(0.134, 0.506, -0.109, 0.109, 0.024)
    frame = [top(x, y, 0.0020) for (x, y) in outline] + [top(outline[0][0], outline[0][1], 0.0020)]
    made.append(tube("int_console_frame", frame, ellipse(0.0030, 0.0030, 8), col, lib["chrome"],
                     lateral=(0.0, 0.0, 1.0)))
    # charging area (the phone pad), the brushed band, the forged panel
    for name, x0, x1, role, lift in (("int_console_charge", 0.290, 0.478, "charge", 0.0012),
                                     ("int_console_band", 0.262, 0.286, "brushed", 0.0014),
                                     ("int_console_forged", 0.142, 0.259, "forged", 0.0012)):
        rows = [[top(x0 + (x1 - x0) * i / 16.0, y, lift) for y in
                 [0.101 - 0.202 * j / 20.0 for j in range(21)]] for i in range(17)]
        pn = grid_mesh(name, rows, col, lib[role])
        M.orient(pn.data, lambda c: (0.0, 0.0, 1.0))
        made.append(pn)
    # the crystal gear selector: a capsule lying along the console's axis on
    # the pad (passenger34_high and the wide photo show it end-on and side-on)
    x0, x1 = 0.405, 0.340
    path = [(x0 + (x1 - x0) * t / 16.0, 0.0, CONSOLE_TOP(x0 + (x1 - x0) * t / 16.0) + 0.0105)
            for t in range(17)]
    made.append(tube("int_console_lever", path, ellipse(0.0062, 0.0075, 16), col, lib["chrome"],
                     lateral=(0.0, 0.0, 1.0),
                     scale=lambda s: (0.30 + 0.70 * math.sin(math.pi * s) ** 0.35,
                                      0.30 + 0.70 * math.sin(math.pi * s) ** 0.35)))
    # cupholders: wells and chrome rims
    for k, (cx, cy, r) in enumerate(CUPS):
        rings = []
        for d, s in ((0.0, 1.0), (0.004, 0.99), (0.060, 0.96), (0.074, 0.90), (0.076, 0.0)):
            rings.append([(cx + r * s * math.cos(2 * math.pi * j / 32),
                           cy + r * s * math.sin(2 * math.pi * j / 32), 0.8005 - d) for j in range(32)])
        well = grid_mesh("int_console_cup%d" % k, rings, col, lib["satin"], wrap_t=True)
        M.orient(well.data, lambda c, cx=cx, cy=cy: (cx - c[0], cy - c[1], 0.5))
        made.append(well)
        ring = [(cx + r * math.cos(2 * math.pi * j / 32), cy + r * math.sin(2 * math.pi * j / 32), 0.8015)
                for j in range(33)]
        made.append(tube("int_console_cup_rim%d" % k, ring, ellipse(0.0035, 0.0028, 8), col,
                         lib["chrome"], lateral=(0.0, 0.0, 1.0)))
    return made


# ------------------------------------------------------------- door cards
def _belt_z(x):
    return PN.BELT_Z(max(PN.X_DLO_TIP, min(0.80, x)))


# skin-to-card depth by height: the dash's ends (|y| 0.76) meet the card at
# ~0.78; the belt cap closes the 5-8 cm to the glass
DOOR_TH = Curve([(0.40, 0.115), (0.60, 0.150), (0.75, 0.172), (0.90, 0.168), (1.00, 0.148),
                 (1.08, 0.102), (1.14, 0.070)], mode="pchip")


def _v_top_front():
    return max(PN.V_BELT(x) for x in (-0.35, 0.0, 0.3, 0.7)) + 0.015


def front_card(side):
    from carkit.interior.door import DoorCard
    return DoorCard(S.BODY, lambda z: PN._DOOR_F_EDGE(z) - 0.022,
                    lambda z: PN.X_BPILLAR + 0.006, 0.40, _belt_z, DOOR_TH,
                    v_top=_v_top_front(), side=side)


# In side elevation (cabin_wide_rear_white, passenger34_high_white): under the
# rail a white perforated band carries the dash's white band back into the
# door, narrowing and ending in a round nose above the armrest; under it a
# red roll, thin where it leaves the dash and swelling rearward to its own
# round end; a chrome-framed pocket (speaker grille, window switches) leaning
# back under the red; a long armrest rising forward to the pocket.
WHITE_END = -0.060
RED_END = -0.200


def _rail_bot(x):
    return _belt_z(x) - 0.036


def _red_top(x):
    t = _smooth((0.62 - x) / 0.80)
    return 0.952 - 0.022 * t


def _red_bot(x):
    t = _smooth((0.62 - x) / 0.80)
    return 0.927 - 0.062 * t


def _round_end(x_end, z_lo, z_hi, lead=0.07):
    """x0(z) for a band whose rear end is a round nose between z_lo(x) and
    z_hi(x) at x_end: an elliptical end `lead` long."""
    def f(z):
        a, b = z_lo(x_end + lead), z_hi(x_end + lead)
        m, h = 0.5 * (a + b), max(1e-4, 0.5 * (b - a))
        u = max(-1.0, min(1.0, (z - m) / h))
        return x_end + lead * (1.0 - math.sqrt(max(0.0, 1.0 - u * u)))
    return f


# the pocket: a parallelogram leaning forward, corners (x, z) top-rear,
# top-front, bottom-front, bottom-rear, rounded by the closed spline
POCKET_CORNERS = [(0.300, 0.905), (0.520, 0.912), (0.440, 0.765), (0.160, 0.765)]
POCKET = [(0.320, 0.906), (0.500, 0.912), (0.515, 0.894), (0.452, 0.785), (0.420, 0.765),
          (0.180, 0.765), (0.170, 0.783), (0.288, 0.890)]


def _pocket_edge(z, front):
    """x of the pocket's rear (front=False) or front edge at height z."""
    (xa, za), (xb, zb) = ((POCKET_CORNERS[3], POCKET_CORNERS[0]) if not front else
                          (POCKET_CORNERS[2], POCKET_CORNERS[1]))
    t = (z - za) / (zb - za)
    return xa + (xb - xa) * t


def build_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr = lambda z: PN.X_BPILLAR + 0.006
        xf = lambda z: PN._DOOR_F_EDGE(z) - 0.022
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(1.0), _belt_z,
                                mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.40, _rail_bot,
                            x0=xr, x1=xf, nx=64, nz=24, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"], _rail_bot,
                            lambda x: _belt_z(x) - 0.002, proud=-0.004, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        # the white band: rail to the red roll, round nose at WHITE_END
        made.append(dc.band(pre + "White", col, lib["leather_white"], _red_top,
                            lambda x: _rail_bot(x) - 0.002, proud=0.006,
                            x0=_round_end(WHITE_END, _red_top, _rail_bot), x1=xf, nx=48, nz=10,
                            mirror=False))
        # the red roll, swelling rearward to its round end
        made.append(dc.band(pre + "Red", col, lib["leather_accent"], _red_bot, _red_top,
                            proud=0.011, x0=_round_end(RED_END, _red_bot, _red_top, 0.05), x1=xf,
                            nx=48, nz=8, edge_round=0.008, mirror=False))
        # ambient light guide along the red roll's lower edge
        pts = dc.curve([(x, _red_bot(x) - 0.002) for x in [0.70 - 0.86 * k / 24.0
                                                          for k in range(25)]], proud=0.006)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0016,
                           lateral=(0.0, 0.0, 1.0)))
        # the pocket: a chrome frame, the speaker grille and switch panel in it
        path = smooth_path([(x, 0.0, z) for (x, z) in POCKET], 96, closed=True)
        pts = [dc.point(p[0], p[2], 0.010) for p in path]
        made.append(tube(pre + "PocketRim", pts + [pts[0]], ellipse(0.0032, 0.0032, 8), col,
                         lib["chrome"], lateral=(0.0, 1.0, 0.0)))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.795, lambda x: 0.899,
                            proud=0.003, x0=lambda z: _pocket_edge(z, False) + 0.022,
                            x1=lambda z: _pocket_edge(z, True) - 0.018,
                            nx=24, nz=8, edge_round=0.0, mirror=False))
        made.append(dc.band(pre + "Switches", col, lib["piano"], lambda x: 0.769, lambda x: 0.792,
                            proud=0.005, x0=lambda z: _pocket_edge(z, False) + 0.020,
                            x1=lambda z: _pocket_edge(z, True) - 0.016, nx=16, nz=3,
                            edge_round=0.002, mirror=False))
        for k in range(4):
            xk = 0.230 + 0.045 * k
            yk = side * (dc.skin_y(xk, 0.781) - DOOR_TH(0.781) - 0.010)
            made.append(F.box(col, pre + "Switch%d" % k, (xk, yk, 0.786), (0.026, 0.016, 0.010),
                              lib["satin"], r=0.002))
        # the armrest, rising forward to the pocket
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-0.300, 0.700), (-0.050, 0.718), (0.180, 0.742), (0.430, 0.756)])
    made += build_rear_doors(col, lib)
    return made


def _door_armrest(dc, name, col, lib, side, path_xz, width=0.070, height=0.050, n=40):
    """A padded bar along the card through side-elevation points (x, z of
    its top), its ends tapering into the card; red stitching along its
    inner top edge."""
    path = smooth_path([(x, 0.0, z) for (x, z) in path_xz], n + 1)
    rows = []
    edge = []
    for k, p in enumerate(path):
        s = k / float(n)
        e = min(1.0, min(s, 1.0 - s) * 7.0)
        e = e * e * (3 - 2 * e)
        w = 0.004 + (width - 0.004) * e
        x, z = p[0], p[2]
        y0 = dc.skin_y(x, z) - dc.th(z)
        prof = [(0.0, -height), (w * 0.55, -height * 0.92), (w * 0.95, -height * 0.55),
                (w, -0.012), (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)]
        from carkit.interior.sweep import cr_segments
        sec = cr_segments(prof, 4)
        rows.append([(x, side * (y0 - a), z + b) for (a, b) in sec])
        edge.append((x, side * (y0 - w * 0.80), z + 0.0002))
    ob = grid_mesh(name, rows, col, lib["leather_black"])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    made = ob
    nrm = [(0.0, 0.0, 1.0)] * len(edge)
    st = stitches(name + "Stitch", edge[3:-3], nrm[3:-3], col, lib["thread_accent"])
    return [made, st]


def _rear_top_z(x):
    return _belt_z(x)


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.40, 0.095), (0.60, 0.125), (0.75, 0.140), (0.90, 0.130), (1.05, 0.100),
                (1.20, 0.072), (1.30, 0.060)], mode="pchip")
    return DoorCard(S.BODY, lambda z: PN.X_BPILLAR - 0.006,
                    lambda z: PN._DOOR_R_EDGE(z) + 0.006, 0.40, _rear_top_z, th,
                    v_top=max(PN.V_BELT(x) for x in (-1.39, -1.0, -0.4)) + 0.015, side=side)


def build_rear_doors(col, lib):
    """The rear cards, from seats_rear34 and the wide cabin photo's edges:
    the front cards' bands without the pocket - a white band under the
    rail with the red roll under it, black below, an armrest and pull."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        rb = lambda x: _rear_top_z(x) - 0.036
        rt = lambda x: 0.972 + 0.040 * _smooth((-0.40 - x) / 0.9)
        rl = lambda x: 0.948 + 0.040 * _smooth((-0.40 - x) / 0.9)
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.40, rb,
                            x0=xr, x1=xf, nz=20, mirror=False))
        made.append(dc.band(pre + "White", col, lib["leather_white"], rt, lambda x: rb(x) - 0.002,
                            proud=0.006, x0=xr, x1=xf, nz=10, mirror=False))
        made.append(dc.band(pre + "Red", col, lib["leather_accent"], rl, rt, proud=0.010,
                            x0=xr, x1=xf, nz=6, edge_round=0.007, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"], rb,
                            lambda x: _rear_top_z(x) - 0.002, proud=-0.004, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004,
                                xf(0.95), _rear_top_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _rear_top_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        pts = dc.curve([(x, rl(x) - 0.002) for x in [-0.40 - 0.75 * k / 20.0 for k in range(21)]],
                       proud=0.005)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0016,
                           lateral=(0.0, 0.0, 1.0)))
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-1.05, 0.690), (-0.80, 0.700), (-0.52, 0.712)], width=0.060)
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.47,
                            lambda x: 0.57, proud=0.003, x0=lambda z: -0.62,
                            x1=lambda z: -0.40, nx=14, nz=6, mirror=False))
    return made


# ---------------------------------------------------------------- the shell
X_OPEN_F, X_OPEN_R = -0.200, -1.430      # the glass roof's opening in the headliner
# The exterior's roof glass now stops at the B-pillar (rx_panels.
# X_ROOF_GLASS_R: the owner's review wanted body colour over the rear seats),
# so the opening over the rear seats would look up at painted metal: the
# headliner closes, one piece from the header to the backlight.
ROOF_OPENING = False
Y_OPEN = 0.470                           # its half-width
X_HEADLINER_R = -2.180                   # the headliner runs back to the backlight's top


def v_head_edge(x):
    """The headliner's outer edge: 50 mm above the side glass's top."""
    return S.v_along(x, PN.V_GT(max(x, PN.X_DLO_TIP)), 0.050)


def _head_rows(x0, x1, nx, v_in, v_out=v_head_edge, inset=0.045, nv=22):
    rows = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / float(nx)
        a, b = v_out(x), v_in(x)
        row = [S.surface_offset(x, a + (b - a) * j / float(nv), -inset) for j in range(nv + 1)]
        rows.append(row)
    return rows


def build_headliner(col, lib):
    """A suede frame round the panoramic roof's opening: a front band (visors,
    overhead console, speakers), side rails and a rear band back to the
    tailgate (cabin_wide_rear_white shows the glass from the front band
    back; seats_rear34 shows it over the rear seats)."""
    made = []
    centre = lambda x: 0.9995
    open_v = lambda x: S.v_at_y_upper(x, Y_OPEN)
    bands = (("int_headliner_F", PN.X_ROOF_F + 0.030, X_OPEN_F, 16),
             ("int_headliner_R", X_OPEN_R, X_HEADLINER_R, 30))
    if not ROOF_OPENING:
        bands = (("int_headliner", PN.X_ROOF_F + 0.030, X_HEADLINER_R, 60),)
    for name, x0, x1, nx in bands:
        rows = _head_rows(x0, x1, nx, centre)
        for r in rows:
            r[-1] = (r[-1][0], 0.0, r[-1][2])
        ob = grid_mesh(name, rows, col, lib["headliner"])
        M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
        M.mirror_y(ob)
        made.append(ob)
    if not ROOF_OPENING:
        return made
    rows = _head_rows(X_OPEN_F + 0.002, X_OPEN_R - 0.002, 48, open_v, nv=10)
    ob = grid_mesh("int_headliner_side", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
    M.mirror_y(ob)
    made.append(ob)
    # the opening's reveal: from the headliner's edge up to the glass, all
    # round, so no gap shows the roof's paint beyond the glass edge
    loop = []
    for k in range(40):
        x = X_OPEN_F + (X_OPEN_R - X_OPEN_F) * k / 39.0
        loop.append((x, open_v(x)))
    rows = [[S.surface_offset(x, v, -0.045), S.surface_offset(x, v, -0.004)] for (x, v) in loop]
    rv = grid_mesh("int_headliner_reveal", rows, col, lib["headliner"])
    M.orient(rv.data, lambda c: (0.0, -1.0 if c[1] > 0 else 1.0, 0.0))
    M.mirror_y(rv)
    made.append(rv)
    for x, nm in ((X_OPEN_F, "F"), (X_OPEN_R, "R")):
        rows = []
        v0 = open_v(x)
        for j in range(13):
            v = v0 + (0.9995 - v0) * j / 12.0
            rows.append([S.surface_offset(x, v, -0.045), S.surface_offset(x, v, -0.004)])
        for r in rows:
            pass
        rows[-1] = [(p[0], 0.0, p[2]) for p in rows[-1]]
        ev = grid_mesh("int_headliner_reveal" + nm, rows, col, lib["headliner"])
        M.orient(ev.data, lambda c, s=(-1.0 if nm == "F" else 1.0): (s, 0.0, 0.0))
        M.mirror_y(ev)
        made.append(ev)
    return made


def build_shell(col, lib):
    made = build_headliner(col, lib)
    # A-pillars: across from the door glass's front edge to the windscreen's
    # side edge, 20 mm over each glass; into the dash at the foot and on past
    # the header under the headliner
    xs = [0.700 - (0.700 - (PN.X_ROOF_F - 0.03)) * k / 28.0 for k in range(29)]

    def a_door(x):
        return (x, S.v_along(x, PN.v_up(x, max(PN.BELT_Z(0.62), PN.z_a(min(x, PN.A_FOOT[0])))), -0.020))
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs, a_door,
        lambda x: (x, S.v_along(x, PN.V_A(x), 0.018)),
        depth=0.010, bulge=0.034, name="int_apillar"))
    # the tweeter on each A-pillar's foot (cabin_front: an oval grille)
    for side in (1.0, -1.0):
        x = 0.500
        a = Vector(S.BODY.surface(*a_door(x)))
        b = Vector(S.BODY.surface(x, S.v_along(x, PN.V_A(x), 0.018)))
        n = (Vector(S.BODY.surface_normal(*a_door(x))) +
             Vector(S.BODY.surface_normal(x, S.v_along(x, PN.V_A(x), 0.018)))).normalized()
        c = a.lerp(b, 0.5) - n * (0.010 + 0.034 + 0.002)
        c.y *= side
        nn = Vector((-n.x, -n.y * side, -n.z))
        made += F.disc(col, "int_apillar_tweeter%s" % ("L" if side > 0 else "R"), tuple(c),
                       tuple(nn), 0.024, lib["speaker"], dome=0.002, rim=0.0018,
                       rim_mat=lib["satin"])
    # roof rails over the side glass, back to the quarter light's tip
    xs = [PN.X_ROOF_F + 0.04 - (PN.X_ROOF_F + 0.04 - PN.X_DLO_TIP) * k / 44.0 for k in range(45)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, PN.V_GT(x), -0.010)),
        lambda x: (x, S.v_along(x, PN.V_GT(x), 0.070)),
        depth=0.012, bulge=0.020, name="int_roofrail"))
    # B-pillar: between the door glasses, belt to rail
    vb0 = PN.V_BELT(PN.X_BPILLAR) - 0.006
    vb1 = PN.V_GT(PN.X_BPILLAR) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], vs,
        lambda v: (PN.GB_F + 0.012, v), lambda v: (PN.GB_R - 0.012, v),
        depth=0.012, bulge=0.032, name="int_bpillar"))
    # C-pillar: the broad sail behind the quarter light, as an offset trim,
    # from under the belt up under the headliner, and behind the knee up to
    # the backlight's side edge
    xs = [PN.X_DLO_TIP + 0.030 - (PN.X_DLO_TIP + 0.030 + 2.44) * k / 24.0 for k in range(25)]

    def c_lo(x):
        # down over the quarter trim's top (1.205); in the luggage area down
        # below the parcel shelf's edge
        z = max(1.06, min(_belt_z(x) - 0.06, 1.17))
        z += (1.02 - z) * _smooth((-1.70 - x) / 0.15)
        return S.v_at_z(x, z, 0.30, 0.99)

    def c_hi(x):
        a = v_head_edge(max(x, X_HEADLINER_R)) + 0.010
        if x >= PN.X_KNEE:
            return a
        b = PN.V_REARGLASS(x) + 0.012
        t = _smooth((PN.X_KNEE - x) / 0.05)
        return a + (b - a) * t
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.030,
                               bulge=0.020, nt=16, name="int_cpillar", overlap=0.010))
    # a flange from the trim's front edge out to the skin: from the rear seat
    # you looked past that edge, into the 3-5 cm between trim and body
    x0 = xs[0]
    a, b = S.v_along(x0, c_lo(x0), -0.010), S.v_along(x0, c_hi(x0), 0.010)
    rows = []
    for j in range(17):
        t = j / 16.0
        v = a + (b - a) * t
        d = 0.030 + 0.020 * math.sin(math.pi * t) ** 0.7
        rows.append([S.surface_offset(x0, v, -d), S.surface_offset(x0, v, -0.004)])
    fl = grid_mesh("int_cpillar_flange", rows, col, lib["headliner"])
    M.orient(fl.data, lambda c: (1.0, 0.0, 0.0))
    M.mirror_y(fl)
    made.append(fl)
    # under the quarter light: an OFFSET trim from below the shoulder up onto
    # the glass's lower edge. The body steps in here - a flat ledge ~18 cm wide
    # at z 1.19, then a rounded rise to the glass (the greenhouse tapering on
    # the haunches, rx_surface Y_GLASS) - and a chord across it left the
    # rise's inner wall in view from the rear seat
    xs = [PN.X_DOOR_R_TOP + 0.010 - (PN.X_DOOR_R_TOP + 0.010 - (PN.X_DLO_TIP - 0.020)) * k / 10.0
          for k in range(11)]
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs,
                               lambda x: S.v_at_z(x, 1.100, 0.30, 0.99),
                               lambda x: PN.V_BELT(x), inset=0.014, bulge=0.004, nt=16,
                               name="int_qtr_lower", overlap=0.008))
    made += build_roof_fittings(col, lib)
    # floor and sills
    made.append(CB.floor(col, lib["carpet"], -1.62, 0.74, 1.02, FLOOR_Z, 0.66,
                         lambda x: 0.73 - 0.05 * _smooth((x - 0.84) / 0.06), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.40, 0.77, 0.72, 0.86, FLOOR_Z, 0.445,
                        name="int_sill"))
    return made


# ------------------------------------------------------------ closing trims
def build_closures(col, lib):
    """What stops the painted body showing from inside: B-pillar seals,
    footwell kick panels, the rear wheelhouse trims, parcel shelf and
    bulkhead (carkit.qa.leaks finds the rest)."""
    made = []
    vh = _v_top_front() + 0.10
    xs = [PN.X_BPILLAR - 0.030 + 0.060 * k / 6.0 for k in range(7)]
    rows = []
    for x in xs:
        rows.append([(x, CB.skin_offset_y(S.BODY, x, z, 0.030, vh), z)
                     for z in [0.40 + (_belt_z(x) - 0.40) * k / 12.0 for k in range(13)]])
    seal = grid_mesh("int_bpillar_seal", rows, col, lib["satin"])
    M.orient(seal.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(seal)
    made.append(seal)
    # kick panels: the side walls ahead of the door opening, floor to dash
    # (inboard of the front wheel liner, which reaches |y| 0.70 at x 0.9: the
    # footwell narrows ahead of the door opening)
    yk = 0.745
    x_open = PN._DOOR_F_EDGE(0.60) - 0.010
    kick_y = Curve([(x_open, yk), (0.84, yk), (0.90, 0.685), (1.06, 0.680)], mode="pchip")
    made.append(CB.wall(col, lib["leather_black"],
                        [(x_open + (1.06 - x_open) * k / 16.0, kick_y(x_open + (1.06 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.93, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["leather_black"],
                        [(x_open, yk + (0.90 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.00 + 0.10 * _smooth((y - 0.78) / 0.04),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))
    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = rear_card(1.0)
    vq = max(PN.V_BELT(x) for x in (-1.40, -1.55)) + 0.10
    # the hump wall stands inboard of the wheel liner's inner wall (|y| 0.70)
    # and rolls over above its top (0.93): lower, the liner showed behind the
    # rear door from both rows (carkit.qa.leaks)
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_black"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.82,
        FLOOR_Z + 0.02, 0.672, 0.975, 1.205, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)
    # the parcel shelf: from behind the rear seat backs to the backlight's base
    # its rear end rises to the backlight's clear glass: the glass's lower
    # part is backed by the painted tail cap (rx_rear), which showed over a
    # flat shelf from the rear seats
    pts = []
    for k in range(17):
        x = -1.56 - (2.46 - 1.56) * k / 16.0
        pts.append((x, 1.050 + 0.105 * (k / 16.0) ** 1.8 + 0.035 * _smooth((x + 2.30) / -0.14)))
    made.append(CB.bulkhead(col, lib["headliner"], pts,
                            lambda x, z: CB.skin_offset_y(S.BODY, x, z, 0.070, 0.80),
                            name="int_parcel_shelf", facing=(0.0, 0.0, 1.0)))
    # the rear window's sill: from the shelf up to the clear glass's lower
    # edge, which rises from z 1.19 on the centreline to 1.28 at its corners
    # (the tail cap's painted top comes up round it - RX_Glass_Rear measured)
    xe = Curve([(0.00, -2.426), (0.12, -2.391), (0.24, -2.357), (0.36, -2.322), (0.48, -2.293),
                (0.62, -2.268)])
    ze = Curve([(0.00, 1.187), (0.12, 1.209), (0.24, 1.233), (0.36, 1.258), (0.48, 1.284),
                (0.62, 1.290)])
    rows = []
    for j in range(17):
        y = 0.62 * j / 16.0
        xa, za = -2.200, 1.112
        xb, zb = xe(y) + 0.006, ze(y) - 0.010
        rows.append([(xa + (xb - xa) * t, y, za + (zb - za) * (t ** 0.6)) for t in
                     [k / 6.0 for k in range(7)]])
    sl = grid_mesh("int_rear_sill", rows, col, lib["headliner"])
    M.orient(sl.data, lambda c: (0.3, 0.0, 1.0))
    M.mirror_y(sl)
    made.append(sl)
    made.append(CB.bulkhead(col, lib["satin"],
                            [(-1.575, FLOOR_Z + (1.052 - FLOOR_Z) * k / 10.0) for k in range(11)],
                            lambda x, z: 0.70 if z < 0.80 else CB.skin_offset_y(S.BODY, x, z, 0.075, 0.80),
                            name="int_rear_bulkhead", facing=(1.0, 0.0, 0.0)))
    return made


# ------------------------------------------------------------------ pedals
def build_pedals(col, lib):
    """cabin_front and cabin_wide_rear: a tall slotted dead pedal far left,
    the brake (a square pad with rubber strips) ahead of the driver, the
    accelerator (tall, narrow) to its right beside the console."""
    made = []
    p = math.radians(40.0)
    a = Vector((math.sin(p), 0.0, math.cos(p)))
    n = Vector((-math.cos(p), 0.0, math.sin(p)))
    for name, y, x, z, w, h, strips in (("rest", 0.640, 0.840, 0.470, 0.075, 0.210, 5),
                                        ("brake", 0.390, 0.815, 0.500, 0.092, 0.078, 3),
                                        ("accel", 0.235, 0.860, 0.450, 0.055, 0.200, 0)):
        c = Vector((x, y, z))
        made.append(F.box(col, "int_pedal_" + name, tuple(c), (0.010, w, h), lib["brushed"],
                          r=0.003, pitch=p))
        if name == "rest":
            for k in range(strips):
                q = c + n * 0.006 + Vector((0.0, (k - 2) * w * 0.18, 0.0))
                made.append(F.box(col, "int_pedal_%s_slot%d" % (name, k), tuple(q),
                                  (0.004, 0.006, h * 0.85), lib["rubber"], r=0.0015, pitch=p))
        else:
            for k in range(strips):
                q = c + n * 0.006 + a * ((k - 1) * h * 0.28)
                made.append(F.box(col, "int_pedal_%s_strip%d" % (name, k), tuple(q),
                                  (0.004, w * 0.82, 0.008), lib["rubber"], r=0.0015, pitch=p))
    return made


# ------------------------------------------------------------ roof fittings
def build_roof_fittings(col, lib):
    made = []
    # the frameless rear-view mirror, hung from the header on a short stem
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
    # the overhead console on the front band, with the red-framed in-cabin
    # camera module (cabin_wide_rear_white)
    xs = [0.02 - 0.16 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.12 * (1 - 2 * j / 10.0), zr - 0.016 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["satin"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    xm = -0.02
    zm = S.Z_ROOF(xm) - 0.064
    made.append(F.box(col, "int_overhead_cam", (xm, 0.0, zm), (0.060, 0.090, 0.008),
                      lib["screen_glass"], r=0.003))
    loop = [(xm + a, b, zm - 0.004) for (a, b) in F.round_rect_xy(-0.032, 0.032, -0.048, 0.048, 0.012)]
    loop.append(loop[0])
    made.append(tube("int_overhead_cam_rim", loop, ellipse(0.0025, 0.0025, 6), col,
                     lib["leather_accent"], lateral=(0.0, 0.0, 1.0)))
    # sun visors folded against the front band either side
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
    # the two round speaker grilles in the front band
    for side in (1.0, -1.0):
        x = -0.150
        v = S.v_at_y_upper(x, 0.36)
        p = Vector(S.surface_offset(x, v, -0.0465))
        nrm = -Vector(S.surface_normal(x, v))
        made += F.disc(col, "int_head_speaker%s" % ("L" if side > 0 else "R"),
                       (p.x, side * p.y, p.z), (nrm.x, side * nrm.y, nrm.z), 0.030,
                       lib["speaker"], rim=0.0022, rim_mat=lib["chrome"])
    return made


# ---------------------------------------------------------------- lighting
def cabin_lights(col):
    """The render rig (SU7's, moved for the RX's taller cabin): a soft box
    under the glass roof, a fill from behind the viewer kept out of glossy
    rays (mirror, screens), two weak side fills."""
    return F.lights(col, [
        ("int_L_Roof", (-0.30, 0.0, 1.40), (-0.30, 0.0, 0.40), (1.7, 1.25), 10.0,
         (0.90, 0.94, 1.00), True),
        ("int_L_Back", (-1.15, 0.0, 1.30), (0.60, 0.0, 0.85), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.50, 1.25), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
        ("int_L_Right", (0.0, -1.50, 1.25), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
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
    # world-space UVs for every textured trim (the perforation, grain and the
    # forged panel sample one texel without them); screen_main keeps its own
    from carkit import build as B
    B.ensure_uvs([col], force=tuple(m.name for m in bpy.data.materials
                                    if m.name.startswith("INT_") and m.name != "INT_Screen"))
    assert bpy.data.objects.get("screen_main"), "screen_main is the HMI anchor"
    n = len([o for o in col.objects if o.type == 'MESH'])
    print("interior: %d meshes, %d tris" % (n, M.tri_count([o for o in col.objects
                                                           if o.type == 'MESH'])))
    return col
