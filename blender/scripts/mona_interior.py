"""XPeng Mona L05 (岚图追光S) cabin — calibrated to Autohome Series 8534 interior photos.

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

import mona_surface as S
import mona_panels as PN
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "MONA_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.420                 # SUV cabin floor above 800V battery pack (underbody 0.252)
DRIVER_Y = 0.410
PASS_Y = -0.410

# One centred 17.3" landscape screen (c10_0001 / c10_0004: 1.74:1, centre on the car's centre line, standing on the dash top)
SCREEN_TILT = math.radians(12.0)
SCREEN_W, SCREEN_H = 0.383, 0.215
SCREEN_BORDER = 0.006
# The FRONT COCKPIT GROUP (dash face, screen, wheel, console) stands FRONT_DX further forward than the first build had it.
# Measured against XPENG's Cabin 360 panoramas, relative to the screen: the real seats' headrests and the real B-pillar's front
# edge are both 13-17 cm further back than ours, the real eye point (the front camera) is 0.70 m from the screen where our
# driverEye was 0.49 m, while wheel, console and screen agree with each other. One translation of the group explains all of
# them and leaves the seats where the owner's seat rule put them (docs/xpeng-pano-benchmark.md). Set 0.0 to undo.
FRONT_DX = 0.17
SCREEN_C = (0.548 + FRONT_DX, 0.0, 1.135)
PASS_SCREEN_C = SCREEN_C        # (no passenger display: kept so the donor's names resolve)
DUAL_SLAB_C = SCREEN_C
DUAL_SLAB_W = SCREEN_W

# The wheel's centre line is y 0.366, not the seat's 0.410: triangulated from both Cabin 360 panoramas (the logo lands at
# 0.332 / 0.366 / 1.111; the old x and z were right to 6 mm), docs/xpeng-pano-benchmark.md.
WHEEL_Y = 0.366
WHEEL_C = (0.355 + FRONT_DX, WHEEL_Y, 1.095)
WHEEL_TILT = math.radians(20.0)

DASH_HALF = 0.738
# Seats: the front seat sits IN the front door (door x +0.95 .. the B-pillar's front edge -0.16), its cushion centre at the door's
# middle and the backrest's rear face 4 cm ahead of the B-pillar (bight = split + 0.19); the rear bench in the rear door (x -0.15 .. -1.27). The first build
# copied the Voyah's -0.24 / -1.16 (its B-pillar was 0.15 further back): the owner saw the front seats under the rear door glass
# (2026-11-17, and on most earlier cars, see docs/3d-pipeline.md 'Seat position').
FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.030, 0.655
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -0.940, 0.675, 0.375

MIRROR_C = (0.340, 0.000, 1.430)       # 2026-11-19: 10 cm further forward (the Cabin 360 mirror hangs right under the header, which our body has at x 0.38)

def _lin8(r, g, b):
    """sRGB 0-255 -> linear albedo."""
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# The real LIGHT GREY interior, measured from XPENG's Cabin 360 panorama (scripts/photo-tools/pano_probe.cjs, 2026-11-18; the
# other four trims are recolours of these materials in the vehicle data): a dark steel-grey dash and wheel, pale cool-grey
# leather seats and console, dark grey seat shells, lime piping. The viewer shows an albedo at about its own sRGB value
# (measured on the Cabin FX path: leather 188 -> 193), so these are the panorama's displayed colours, nudged between a
# patch's lit and shaded values (the panorama lights the dash top 2.5x brighter than its face; our light is flatter).
# Names kept from the first (lavender) build so the shared polish tables and trim tables still resolve.
# Second pass, from a per-material ID pass in the viewer at the two solved cameras (what each material DISPLAYS vs the
# panorama's patch): leather displayed 217,222,226 for a target 205,212,223 (red/green down 5%); the dash matched (55,64,73 vs
# 54,61,69); the wheel read 10-19% high; the headliner 63 for 42 (the alcantara's sheen lifts it 1.5x); the seat shells 25 for
# 46 (the viewer's light is weak on vertical backs: a lighting gap, so only part of it is taken up here).
CLOUD_BEIGE = _lin8(190, 199, 217)           # pale leather (headrest 189,199,214 / shoulder 220,224,232 in the panorama)
ACCENT_TAN = (0.150, 0.160, 0.215)           # thread accent
DASH_LAVENDER = _lin8(53, 60, 67)            # dash top pad 86,95,107, face 34,39,45
SHELL_LAVENDER = _lin8(58, 59, 64)           # seat shells / base shrouds (panorama 46,47,51; displays at about 0.55 of this)
PERIWINKLE = _lin8(60, 67, 77)               # the ribbed band round the dash and the upper doors: the dash tone, a step lighter
WHEEL_GREY = _lin8(61, 66, 73)               # wheel rim 83,90,97, hub 64,70,78
LIME = _lin8(201, 224, 74)                   # seat piping and the lit slits (the calipers' fluorescent yellow-green)


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
    msk = maps["perf_mona_mask"]
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


def perforation_maps(size=512, pitch_px=32, radius=0.105, strength=6.0):
    """Seat leather's fine perforation. 2026-11-19: radius 0.14 -> 0.105 and strength 10 -> 6, the mask's darkness 0.80 -> 0.55 (the
    panorama's holes are small and pale: they read as a fine dotting on the cushion, not as polka dots)."""
    import numpy as np
    from carkit import surfacemaps as SM
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.04, 0.0, 1.0)
    nrm = SM._image("T_PerfMONA_Normal", SM.height_to_normal(-hole, strength / size * 60.0),
                    filename="t_perf_mona_normal.png")
    mask = np.repeat((1.0 - 0.55 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_PerfMONA_Mask", mask, non_color=True, filename="t_perf_mona_mask.png")
    return nrm, msk


def pleat_map(size=512, n=22, strength=16.0):
    """Fine vertical pleats for the door cards' upper fabric (Cabin 360: dark pleated cloth between the sill and the pale pod):
    a soft ridge every 8 mm (0.18 m tile / 22), faded slowly down the panel so it is not a comb."""
    import numpy as np
    from carkit import surfacemaps as SM
    u = np.arange(size, dtype=np.float32) / size
    v = np.arange(size, dtype=np.float32) / size
    ridge = (0.5 - 0.5 * np.cos(2.0 * math.pi * n * u)) ** 0.8
    h = ridge[None, :] * (0.80 + 0.20 * np.sin(2.0 * math.pi * 2.0 * v))[:, None]
    return SM._image("T_PleatMONA_Normal", SM.height_to_normal(h.astype(np.float32), strength / size * 60.0),
                     filename="t_pleat_mona_normal.png")


def perforated(name, color, maps, tile=0.064):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.56, specular=0.5, coat=0.10,
                  coat_rough=0.30, ior=1.45, sheen=0.0)
    IM._textured(nt, b, maps["perf_vps"], tile, 0.7)
    _mapped_image(nt, b, _perf_image("T_Perf_MONA_" + name[4:], color, maps), tile, "Base Color")
    return m


def speaker_grille(maps):
    """The door speakers' finely perforated grey metal (Cabin 360 front close-ups: a round grille of tiny holes, silver-grey, with a
    soft dome). The seat perforation maps at a 10 mm tile give ~0.6 mm holes on a 0.6 mm pitch at the speaker's scale."""
    m, nt, b = MB.mat("INT_Speaker_Grille")
    col = _lin8(150, 156, 163)
    MB.set_inputs(b, base=col, metallic=0.85, roughness=0.38, specular=0.5)
    IM._textured(nt, b, maps["perf_vps"], 0.010, 1.0)
    _mapped_image(nt, b, _perf_image("T_Perf_MONA_Grille", col, maps), 0.010, "Base Color")
    return m


def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    maps["perf_vps"], maps["perf_mona_mask"] = perforation_maps()
    maps["pleat_mona"] = pleat_map()
    lib = IM.build_library(accent=ACCENT_TAN, maps=maps)
    lib["leather_white"] = perforated("INT_Leather_White", CLOUD_BEIGE, maps)
    lib["band_fabric"] = IM.alcantara("INT_Band_Fabric", PERIWINKLE, maps, sheen=0.7)
    # the door cards' upper cloth: the band's colour with fine vertical pleats (its own name so a trim recolours it with the band)
    m, nt, b = MB.mat("INT_Door_Pleat")
    MB.set_inputs(b, base=PERIWINKLE, metallic=0.0, roughness=0.90, specular=0.25, coat=0.0, sheen=0.55)
    IM._textured(nt, b, maps["pleat_mona"], 0.18, 0.6)           # (strength 1.0 read as hard stripes in the viewer)
    lib["door_pleat"] = m
    lib["speaker"] = speaker_grille(maps)
    # the wheel's silver (pod bezels, satellite-button rings, the rim clamp): a soft satin silver, grey not white (the shared
    # "brushed" metal blew out to white under the cabin's chrome environment and read as a bright plastic loop in the viewer)
    m, nt, b = MB.mat("INT_Silver_Satin")
    MB.set_inputs(b, base=_lin8(150, 155, 160), metallic=0.65, roughness=0.42, specular=0.5)
    lib["silver_satin"] = m
    # smooth (unperforated) pale grey: the console lid, the door pods, the cup recess (c3_0011, c10_0002)
    lib["leather_smooth"] = IM.leather("INT_Leather_Smooth", CLOUD_BEIGE, maps, roughness=0.52, coat=0.04, strength=0.45)
    # the lavender-grey dash and its lower face: soft-touch, one colour from the windscreen to the console (c10_0002/0004)
    lib["dash_lav"] = IM.leather("INT_Dash_Lav", DASH_LAVENDER, maps, roughness=0.70, coat=0.02, strength=0.35)
    # seat side shells and base shrouds: tone on tone with the dash (c3_0042: lavender; the dark trim recolours it)
    lib["seat_shell"] = IM.leather("INT_Seat_Shell", SHELL_LAVENDER, maps, roughness=0.50, coat=0.05, strength=0.6)
    # steering wheel: smooth grey suede-like fabric (c10_0002: not perforated, darker than the seats)
    lib["wheel_fabric"] = IM.alcantara("INT_Wheel_Fabric", WHEEL_GREY, maps, sheen=0.35, strength=0.6)
    lib["leather_black"] = lib["leather_white"]       # (donor name; the seat shells and ends use seat_shell / dash_lav below)
    lib["wheel_leather"] = lib["wheel_fabric"]
    lib["headliner"] = IM.alcantara("INT_Headliner", _lin8(27, 30, 36), maps, sheen=0.6)
    # piping along the seat seams and the slits on the console and door pods: ONE material so a trim recolours them together
    # (lime on the light and dark greys, teal on the titanium green, purple on the star purple: the panoramas)
    m, nt, b = MB.mat("INT_Piping_Accent")
    MB.set_inputs(b, base=LIME, metallic=0.0, roughness=0.46, specular=0.45, sheen=0.25)
    lib["piping_accent"] = m

    m, nt, b = MB.mat("INT_Charge_Grey")                # the wireless-charging tray pad: a light rubbery plastic (c10_0002)
    MB.set_inputs(b, base=(0.27, 0.275, 0.30), metallic=0.0, roughness=0.62, specular=0.35)     # (displayed 225 vs 175 in the panorama)
    lib["charge"] = m
    m, nt, b = MB.mat("INT_Thread_Pale")                # the seats' fine tone-on-tone stitching
    MB.set_inputs(b, base=(0.34, 0.35, 0.40), metallic=0.0, roughness=0.6, sheen=0.3)
    lib["thread_pale"] = m

    lib["dash_top"] = lib["dash_lav"]
    lib["band_glass"] = lib["band_fabric"]           # the dash's band is the ribbed periwinkle fabric
    return lib


# ------------------------------------------------------------------- dash
# The top pad is a low shelf from the windscreen's base (the cowl at x 1.04-1.15, z 1.11-1.13) back to the screens' face (x 0.66,
# z 1.196). It used to hug the glass from x 0.84 (z 1.25) up to x 0.685 (z 1.34) and drop 14 cm to the face: from outside it
# filled the windscreen as a tall grey slab and, from above, left a hole between the cowl and its front edge (the owner,
# 2026-11-03; the Avatr 06T had the same, see docs: "never let the dash top hug the windscreen"). Now only the first four
# points differ: x 1.10 / 0.96 / 0.82 / 0.685 on a gentle ramp, always below the glass by GLASS_GAP.
_DASH_FACE = [
    (0.658, 1.196), (0.636, 1.174), (0.622, 1.160),
    (0.612, 1.116), (0.602, 1.072),
    (0.594, 1.048), (0.584, 1.022), (0.576, 1.004),
    (0.580, 0.990), (0.588, 0.974),
    (0.614, 0.916), (0.656, 0.835), (0.728, 0.745), (0.820, 0.670), (0.965, 0.610),
]
# the ramp from the cowl (x 1.10, fixed: it is the body's) down to the face, then the face profile moved forward by FRONT_DX
DASH_SECTION = [(1.100, None), (1.045, None), (0.960, None), (0.690 + FRONT_DX, None)] + [(x + FRONT_DX, z) for (x, z) in _DASH_FACE]
DASH_COUNTS = [8, 6, 4, 4, 4, 3, 5, 5, 3, 3, 3, 2, 2, 5, 6, 6, 6, 8]
# c10_0002/0004: a ribbed periwinkle band along the dash's far edge (points 0-2), lavender soft-touch from there to the knees,
# a black shadow gap under the chrome strip (points 11-13)
DASH_PANELS = [("Band", 0, 2, "band_glass"), ("TopPad", 2, 6, "dash_top"), ("Face", 6, 8, "dash_lav"),
               ("White", 8, 11, "dash_lav"), ("Recess", 11, 13, "satin"),
               ("Lower", 13, 18, "dash_lav")]
GLASS_GAP = (0.016, 0.014, 0.014, 0.020)


def _pad_ramp(x):
    """The top pad's height: flat at the cowl's z 1.116, rising on a smooth ramp to the face's top (1.198) at x 0.685."""
    t = _smooth((1.05 - x) / (0.365 - FRONT_DX))
    return 1.116 + 0.082 * t


END_TAPER = 0.15         # the dash's last 15 cm at each door roll into it instead of ending in a flat block


def dash_section(i, s):
    """The dash's cross-section at the spine point s. 2026-11-19: over the last END_TAPER at each door the section's lower face
    rises toward the top pad and pulls forward toward the cowl, so the dash narrows to a soft ear that tucks into the door card
    (the brief's "smooth, continuous wrap-around": the first build ended in a flat 90-degree block, visible as a hard seam at the
    door's top). Cabin 360: dash and door are one continuous sweep."""
    y = DASH_HALF * (1.0 - 2.0 * s)
    out = []
    for k, (x, z) in enumerate(DASH_SECTION):
        if z is None:
            z = min(_pad_ramp(x), z_glass(x, y) - GLASS_GAP[k])
        out.append((x, z))
    t = _smooth((abs(y) - (DASH_HALF - END_TAPER)) / END_TAPER)
    if t > 0.0:
        ztop = max(z for (_, z) in out)
        out = [(x + t * 0.12 * (1.10 - x), z + t * 0.30 * (ztop - z)) for (x, z) in out]
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
    return [F.ngon_cap(col, "int_dash_End" + tag, list(sw.pts[idx]), lib["dash_lav"],
                       (0.0, s, 0.0))
            for idx, tag, s in ((0, "L", 1.0), (len(sw.pts) - 1, "R", -1.0))]


def build_dash_speaker(col, lib):
    """The Voyah's tweeter dome behind its screens: the Mona has none."""
    return []
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
    # the long brushed-silver strip under the screen (c10_0002/0004: from the screen's left edge to the right end, plus a short
    # piece left of the steering wheel; a black gap underneath, where the ambient light line runs)
    for nm, y0, y1 in (("R", -0.585, 0.176), ("L", 0.520, 0.655)):
        made.append(F.box(col, "int_dash_Chrome" + nm, (0.5775 + FRONT_DX, 0.5 * (y0 + y1), 1.000),
                          (0.013, y1 - y0, 0.019), lib["brushed"], r=0.0055))
    y_end = DASH_HALF - END_TAPER + 0.02         # (the dash's ends rise and pull forward: the line stops where they start to)
    ys = [y_end - 2 * y_end * k / 80.0 for k in range(81)]
    made.append(tube("int_dash_Ambient", [(0.580 + FRONT_DX, y, 0.984) for y in ys],
                     ellipse(0.0016, 0.0016, 6), col, lib["ambient"], lateral=(1.0, 0.0, 0.0)))
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
    # the single 17.3" screen in a slim black frame, on an arm out of the dash top
    made.append(F.slab("int_dualscreen_body", SCREEN_C, SCREEN_W + 2 * b, SCREEN_H + 2 * b,
                       0.016, 0.012, SCREEN_TILT, col, lib["piano"]))
    made.append(F.screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col, lift=0.0012))
    made[-1].data.materials.append(F.screen_material())
    ct, st = math.cos(SCREEN_TILT), math.sin(SCREEN_TILT)
    back = Vector((SCREEN_C[0] + 0.016 * ct, 0.0, SCREEN_C[2] - 0.016 * st))
    made.append(F.box(col, "int_screen_arm_C", tuple(back.lerp(Vector((0.640 + FRONT_DX, 0.0, 1.105)), 0.5)),
                      (0.640 + FRONT_DX - back.x, 0.110, 0.060), lib["piano"], r=0.010))
    return made


# ---------------------------------------------------------- steering wheel & seats
MONA_WHEEL = dict(
    # 0.148 (was 0.176): the panorama's rim spans +-17.8 deg from 0.5 m, 0.30 m outer width; ours measured 0.36 (A/B sheet)
    radius=0.148, flat_bottom=-0.122, flat_top=0.134, section=(0.0165, 0.0200),
    grip_swell=0.12,
    segments=[(30.0, 210.0, "wheel_fabric"), (210.0, 390.0, "wheel_fabric")],
    marker=None,
    hub=dict(w=0.140, h=0.120, sides=4, r_corner=0.042, dome=0.010, depth=0.050, pad_role="wheel_fabric"),
    # (c10_0002: a silver-ringed button pod on each spoke, grey pad inside)
    spokes=dict(v=-0.004, h=0.050, t=0.024, u_in=0.058, pad=(0.062, 0.040), body_role="wheel_fabric",
                pad_role="wheel_fabric", frame="silver_satin"),
    lower_spoke=None,
    # two round satellite buttons under the horizontal spokes (Cabin 360 wheel close-up: silver-ringed, dark cap, 8 cm either side of
    # the centre line and 4 cm below the hub's centre); (u, v, r, cap role, ring role)
    buttons=[(0.082, -0.040, 0.0072, "satin", "silver_satin"), (-0.082, -0.040, 0.0072, "satin", "silver_satin")],
    logo=None,                  # the letter X (9 mm) is replaced by the XPENG emblem below (34 mm wide in the panorama)
)
VOYAH_PASSION_S_WHEEL = MONA_WHEEL        # (the donor's name, kept for the shared polish tables)

# The XPENG X: the left half of the badge traced on the nose (mona_front._LOGO_LEFT, photo px), mirrored for the right half.
_X_HALF = [
    (1837.5, 1520.0), (1851.0, 1520.0), (1912.0, 1541.5), (1914.0, 1545.0),
    (1914.0, 1554.0), (1912.0, 1557.5), (1851.0, 1579.0), (1837.5, 1579.0), (1869.0, 1549.5),
]
_X_CX, _X_CY, _X_WIDTH = 1915.5, 1549.5, 156.0        # px centre and full width of the traced badge


def build_wheel_emblem(fr, col, lib, width=0.034, v_stretch=1.29, v_off=0.004, w_off=0.0330):
    """The X on the hub pad. The panorama shows it 34 mm wide and about 2.0:1 (the nose trace is 2.64:1, hence the stretch)."""
    from carkit import photolay as PL
    s = width / _X_WIDTH
    verts, faces = [], []
    for sign in (1.0, -1.0):
        half = [(sign * (x - _X_CX), -(y - _X_CY)) for (x, y) in _X_HALF]
        pts, tris = PL.fill(half, 5.0)
        base = len(verts)
        for (x, y) in pts:
            verts.append(fr.p(x * s, y * s * v_stretch + v_off, w_off))
        faces += [[base + a, base + b, base + c] for (a, b, c) in tris]
    ob = M.obj("int_wheel_logo", verts, faces, col, lib["brushed"])
    M.orient(ob.data, lambda c: tuple(fr.A))                 # faces the driver
    M.solidify(ob, 0.0009)
    M.bevel(ob, 0.00025, 2, 50.0)
    return [ob]


def build_wheel(col, lib):
    """The wheel is mona_wheel.py (2026-11-21): traced from the Cabin 360 front panorama and the Autohome close-ups, like the
    Avatr 06T's a06t_wheel.py. MONA_WHEEL above is kept for the shared polish tables only."""
    import mona_wheel as MW
    made, _fr = MW.build(col, lib, WHEEL_C, WHEEL_TILT)
    return made


def _front_spec():
    """The Mona's front seat (c3_0042/0063): a wide near-upright bucket ending at the shoulders (a separate pillow headrest
    stands above it), pale perforated leather all over, lavender side shells, no centre stripe, tone-on-tone stitching."""
    import copy
    from carkit.interior import seat as SE
    sp = copy.deepcopy(SE.LUXEED_RX_FRONT)
    sp["mats"] = dict(centre="leather_white", crown="leather_white", face="leather_white", shell="seat_shell",
                      piping="piping_accent", stitch="thread_pale", base="satin", cap="leather_white")
    sp.pop("stripe", None)
    sp["cap_from"] = None
    sp["stitch_half_gap"] = 0.030
    sp["cushion"]["half_w"] = Curve([(0.0, 0.268), (0.5, 0.274), (1.0, 0.264)])
    sp["backrest"] = dict(
        # (15 degrees back at the top, as c3_0042/0063 show it; the backrest's rear face then stands at the B-pillar)
        spine=[(0.00, 0.00), (-0.020, 0.092), (-0.058, 0.275), (-0.105, 0.440), (-0.128, 0.505)],
        # (the first build ran 0.25-0.28 all the way up: a slab. The Cabin 360 seat narrows to the shoulders, half width ~0.215)
        half_w=Curve([(0.0, 0.268), (0.42, 0.276), (0.68, 0.258), (0.86, 0.232), (1.0, 0.212)], mode="pchip"),
        bolster=Curve([(0.0, 0.55), (0.30, 1.0), (0.62, 0.72), (0.88, 0.30), (1.0, 0.12)], mode="pchip"),
        bolster_h=0.086,                   # (0.070: a stronger crest on the side bolsters, the brief's "smoother, pillowy" seat)
        centre_half=Curve([(0.0, 0.170), (0.55, 0.165), (1.0, 0.150)], mode="pchip"),
        depth=0.088, end_cap=True)
    return sp


def _rear_spec():
    sp = _front_spec()
    sp["backrest"]["spine"] = [(x * 0.95, z * 0.88) for (x, z) in sp["backrest"]["spine"]]
    return sp


def _headrest(col, lib, name, top, lean, w=0.285, h=0.195, t=0.104, r=0.050, gap=0.050, post_y=0.066):
    """A pillow headrest on two posts a hand's width above the backrest's top point `top` (world), the back leaning by
    `lean` (negative: the top is further back).

    Cabin 360 (2026-11-18): the real front pillow is smooth leather (no perforation, which sits on the seat below), about 15 %
    bigger than the first build's 0.250 x 0.172 and 6 cm higher (z 1.256-1.438 against 1.193-1.374)."""
    import cabin_parts as CP
    k = Vector((math.sin(lean), 0.0, math.cos(lean)))
    nrm = Vector((math.cos(lean), 0.0, -math.sin(lean)))
    centre = top + k * (0.0255 + gap + 0.5 * h) - nrm * (0.5 * t - 0.018)
    made = [CP.pillow(col, name, tuple(centre), w, h, t, r, lib["leather_smooth"], 0.7 * lean)]
    p0 = top - k * 0.020 - nrm * (0.5 * t - 0.018)
    n_len = (centre - p0).length
    mid = 0.5 * (centre + p0)
    for i, sy in enumerate((-1.0, 1.0)):
        made.append(F.box(col, "%s_Post%d" % (name, i), (mid.x, top.y + sy * post_y, mid.z),
                          (0.013, 0.013, n_len), lib["piano"], r=0.003, pitch=lean))
        sl = top + k * 0.014 - nrm * (0.5 * t - 0.018)
        made.append(F.box(col, "%s_Sleeve%d" % (name, i), (sl.x, top.y + sy * post_y, sl.z),
                          (0.030, 0.030, 0.022), lib["seat_shell"], r=0.006, pitch=lean))
    return made


def _backrest_top(spec, origin, y):
    sp = spec["backrest"]["spine"]
    top = Vector((origin[0] + sp[-1][0], y, origin[2] + sp[-1][1]))
    lean = math.atan2(sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1])
    return top, lean


def _seatback_pocket(col, lib, spec, org, y, tag, z_rel=0.30, w=0.28, h=0.30):
    """A raised rounded pocket panel on the backrest's rear face (Cabin 360 back view: a big rounded pocket in the dark shell,
    its top about 2 cm under the shoulder piping). The shell's rear face stands 0.097 behind the spine."""
    sp = spec["backrest"]["spine"]
    sx, lean = sp[-1][0], 0.0
    for i in range(len(sp) - 1):
        if sp[i][1] <= z_rel <= sp[i + 1][1]:
            t = (z_rel - sp[i][1]) / (sp[i + 1][1] - sp[i][1])
            sx = sp[i][0] + t * (sp[i + 1][0] - sp[i][0])
            lean = math.atan2(sp[i + 1][0] - sp[i][0], sp[i + 1][1] - sp[i][1])
            break
    x_rear = org[0] + sx - 0.097
    # (a step lighter than the shell, the band's dark steel: the same colour vanished into the shell in the renders)
    return [F.box(col, "int_seat_%s_Pocket" % tag, (x_rear - 0.002, y, org[2] + z_rel), (0.014, w, h),
                  lib["band_fabric"], r=0.045, pitch=lean)]


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    front = _front_spec()
    shroud = dict(lib, satin=lib["seat_shell"])
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        org = (FRONT_BIGHT_X, y, FRONT_BIGHT_Z)
        parts, _cush, _back = SE.seat(col, lib, front, org, name="int_seat_" + tag)
        for ob in parts:                                  # soften the backrest's hard planar edges (the Cabin 360 seat is all curves)
            if ob.name.endswith(("_Back_Top", "_Back_Shell")):
                M.bevel(ob, 0.012, 3, 40.0)
        made += parts
        top, lean = _backrest_top(front, org, y)
        made += _headrest(col, lib, "int_seat_%s_Head" % tag, top, lean)
        made += _seatback_pocket(col, lib, front, org, y, tag)
        made.append(SE.base(col, shroud, org, FLOOR_Z, name="int_seat_%s_base" % tag))
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        org = (REAR_BIGHT_X, y, REAR_BIGHT_Z)
        parts, _cush, _back = SE.seat(col, lib, rear, org, name="int_seat_" + tag)
        made += parts
        top, lean = _backrest_top(rear, org, y)
        made += _headrest(col, lib, "int_seat_%s_Head" % tag, top, lean, w=0.222, h=0.140, t=0.082, r=0.038, gap=0.030)
    made.append(F.box(col, "int_rear_centre", (REAR_BIGHT_X + 0.20, 0.0, REAR_BIGHT_Z - 0.03),
                      (0.46, 0.21, 0.12), lib["leather_white"], r=0.03))
    made.append(F.box(col, "int_rear_centre_back",
                      (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.27), (0.12, 0.21, 0.50),
                      lib["leather_white"], r=0.03, pitch=math.radians(-18)))
    # the real rear seat is a three-seat bench: the middle place gets its own headrest (Cabin 360 rear view)
    lean_c = math.radians(-18)
    top_c = Vector((REAR_BIGHT_X - 0.16 + math.sin(lean_c) * 0.25, 0.0, REAR_BIGHT_Z + 0.27 + math.cos(lean_c) * 0.25))
    made += _headrest(col, lib, "int_seat_RC_Head", top_c, lean_c, w=0.200, h=0.120, t=0.076, r=0.034, gap=0.020)
    made.append(F.box(col, "int_rear_bench_base",
                      (REAR_BIGHT_X + 0.15, 0.0, 0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                      (0.56, 1.32, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["satin"], r=0.02))
    return made


# ---------------------------------------------------------------- console
# The lid's centre line, re-read from the Cabin 360 front panorama (2026-11-18): the lid's pull tab, just behind the cup pocket,
# is at x 0.147, z 0.915 (the ray from the driver's head meets the y = 0 plane there); the front block's top edge at about
# x 0.38, z 0.943. The first build had a 4 cm dip (z 0.872) where the cup recess sits; the real lid is smooth and gently rising.
CONSOLE_TOP = Curve([
    (-0.255, 0.770), (-0.245, 0.855), (-0.230, 0.888), (-0.205, 0.905), (-0.095, 0.909),
    (-0.035, 0.912), (-0.018, 0.913), (-0.008, 0.914), (0.000, 0.914),
    (0.145, 0.914), (0.155, 0.916), (0.165, 0.919), (0.180, 0.922),
    (0.250, 0.928), (0.340, 0.936), (0.430, 0.942), (0.485, 0.946),
    # the nose (2026-11-19): the first build climbed 5 cm onto a front block that ran into the screen's chrome strip (z 0.99). The
    # Cabin 360 console ends under the dash's overhang with a dark gap between it and the dash face; its nose rolls over and stops
    # at x 0.535 (0.705 with FRONT_DX), 8 cm short of the face at that height.
    (0.505, 0.941), (0.520, 0.930), (0.535, 0.912),
], mode="pchip")
CUP_Z = 0.9145                                          # the cup recess's rim height (the lid's, over x 0..0.145)
CONSOLE_HW = 0.130
CONSOLE_X1 = 0.535                                      # the nose (see CONSOLE_TOP)
TRAY_DEPTH = 0.022                                      # the charging pad sits this far below its surround (Cabin 360: ~2 cm, a soft well)
# c10_0002/0004, c3_0011/0042: a wireless-charging tray at the front (silver rim, raised front lip), ONE rounded cup recess
# behind it, then the smooth armrest lid with a black gloss strip down each side; the lower box is dark under the lid
# (the console floats on its front pillar)
CUP_RECESS = (0.0775, 0.0, 0.0630, 0.094, 0.030)       # centre x, centre y, half x, half y, corner radius (on the flat dip x 0..0.145)
TRAY = (0.222, 0.462, 0.100, 0.020)                     # x0, x1, half y, corner radius
Z_UNDER = 0.675                                         # below this (behind the pillar) the box is dark


def _console_stations():
    xs = []
    x = -0.255
    while x < CONSOLE_X1:
        xs.append(x)
        dense = (-0.26 < x < -0.20) or (-0.04 < x < 0.18) or (0.20 < x < 0.54)      # (0.20-0.48: the charging well's edge)
        x += 0.005 if dense else 0.014
    xs.append(CONSOLE_X1)
    return xs


def _hw(x):
    """The console's half width: 0.130 under the lid and the pockets, narrowing to 0.108 at the rear end (Cabin 360 rear
    view: the rear block is about 20 % narrower than the lid) and rounding in over the last 6 cm of the nose."""
    return CONSOLE_HW * (1.0 - 0.17 * _smooth((0.0 - x) / 0.25)) * (1.0 - 0.30 * _smooth((x - 0.470) / 0.065))


def _console_bottom(x):
    """The console floats: its rear block ends 0.165 m above the floor (the first build ran it down to the carpet)."""
    return FLOOR_Z + (0.585 - FLOOR_Z) * _smooth((0.06 - x) / 0.18)


def _console_section(x, n_arc=5):
    zt = CONSOLE_TOP(x)
    hw, r = _hw(x), 0.016
    zb = _console_bottom(x)
    pts = [(-hw, zb), (-hw, zt - 0.10), (-hw, zt - r)]
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
    pts += [(hw, zt - r), (hw, zt - 0.10), (hw, zb)]
    return pts


def _rr_pts(cx, cy, hx, hy, r, n_arc=6):
    """A rounded rectangle in the XY plane, counter-clockwise, 4 * (n_arc + 1) points."""
    r = min(r, hx - 1e-4, hy - 1e-4)
    out = []
    for (sx, sy, a0) in ((1.0, 1.0, 0.0), (-1.0, 1.0, 90.0), (-1.0, -1.0, 180.0), (1.0, -1.0, 270.0)):
        for k in range(n_arc + 1):
            a = math.radians(a0 + 90.0 * k / n_arc)
            out.append((cx + sx * (hx - r) + r * math.cos(a), cy + sy * (hy - r) + r * math.sin(a)))
    return out


def _in_rr(x, y, cx, cy, hx, hy, r):
    dx = max(abs(x - cx) - (hx - r), 0.0)
    dy = max(abs(y - cy) - (hy - r), 0.0)
    return dx * dx + dy * dy < r * r


def build_console(col, lib):
    import bmesh
    made = []
    xs = _console_stations()
    rows = [[(x, y, z) for (y, z) in _console_section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["leather_smooth"])
    ob.data.materials.append(lib["satin"])
    cx0, cy0, hx0, hy0, r0 = CUP_RECESS
    tx0, tx1, thy, tr = TRAY
    tcx, thx = 0.5 * (tx0 + tx1), 0.5 * (tx1 - tx0)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.z > 0.85 and _in_rr(c.x, c.y, cx0, cy0, hx0 - 0.0015, hy0 - 0.0015, r0):
            kill.append(f)
        elif c.z > 0.85 and _in_rr(c.x, c.y, tcx, 0.0, thx - 0.0015, thy - 0.0015, tr):
            kill.append(f)                           # the charging well (below)
        elif c.z < Z_UNDER:
            f.material_index = 1
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.76)))
    made.append(ob)

    # the nose: a smooth cap (the console's front end, under the dash's overhang)
    made.append(F.ngon_cap(col, "int_console_nose", [(CONSOLE_X1 + 0.0005, y, z) for (y, z) in _console_section(CONSOLE_X1)],
                           lib["leather_smooth"], (1.0, 0.0, 0.0)))

    # the rear face: a smooth cap with a small rounded switch panel and a USB-C pill (c3_0011 #26-27)
    rr = _console_section(xs[0])
    made.append(F.ngon_cap(col, "int_console_rear", [(xs[0] - 0.0005, y, z) for (y, z) in rr],
                           lib["leather_smooth"], (-1.0, 0.0, 0.0)))
    # the rear vent panel (Cabin 360 rear close-up): a black pill slot with four silver pill buttons in it
    made.append(F.box(col, "int_console_rear_screen", (xs[0] - 0.004, 0.0, 0.790),
                      (0.006, 0.170, 0.050), lib["satin"], r=0.022))
    for k, yb in enumerate((-0.054, -0.018, 0.018, 0.054)):
        made.append(F.box(col, "int_console_rear_btn%d" % k, (xs[0] - 0.0075, yb, 0.790),
                          (0.004, 0.030, 0.014), lib["brushed"], r=0.0055))
    made.append(F.box(col, "int_console_rear_usb", (xs[0] - 0.0045, 0.0, 0.738),
                      (0.006, 0.040, 0.016), lib["satin"], r=0.006))

    def top(x, y, lift):
        return (x, y, CONSOLE_TOP(x) + 0.001 * (1.0 - (y / (CONSOLE_HW - 0.016)) ** 2) + lift)

    # the wireless-charging tray: a soft well (TRAY_DEPTH deep, walls leaning in) with a light rubbery pad at its floor, inside a
    # silver rim, and a raised front lip. Cabin 360: the pad sits about 2 cm below the lid, not flush with it.
    rows = [[top(tx0 + (tx1 - tx0) * i / 16.0, y, 0.0014 - TRAY_DEPTH) for y in
             [thy - 2 * thy * j / 20.0 for j in range(21)]] for i in range(17)]
    pn = grid_mesh("int_console_charge", rows, col, lib["charge"])
    M.orient(pn.data, lambda c: (0.0, 0.0, 1.0))
    made.append(pn)
    rings = []
    for d, s in ((0.0, 1.0), (0.003, 0.988), (TRAY_DEPTH - 0.007, 0.972), (TRAY_DEPTH - 0.002, 0.950), (TRAY_DEPTH, 0.935)):
        rings.append([top(x, y, -d) for (x, y) in _rr_pts(tcx, 0.0, thx * s, thy * s, tr * s)])
    wl = grid_mesh("int_console_chargewell", rings, col, lib["leather_smooth"], wrap_t=True)
    M.orient(wl.data, lambda c: (tcx - c[0], -c[1], 0.5))
    made.append(wl)
    rim = [top(x, y, 0.0030) for (x, y) in _rr_pts(tcx, 0.0, thx + 0.0050, thy + 0.0050, tr)]
    rim.append(rim[0])
    # Cabin 360 close-up: the tray's bezel is a slim satin-metal frame (about 7 mm), the pad has one dark slit along its length
    made.append(tube("int_console_frame", rim, ellipse(0.0070, 0.0030, 10), col, lib["brushed"],
                     lateral=(0.0, 0.0, 1.0)))
    made.append(F.box(col, "int_console_charge_slit", top(tcx - 0.010, 0.016, 0.0016 - TRAY_DEPTH),
                      (0.100, 0.0020, 0.0012), lib["satin"], r=0.0005))
    lip = [top(tx1 + 0.004, y, 0.0050) for y in [thy - 2 * thy * k / 14.0 for k in range(15)]]
    made.append(tube("int_console_lip", lip, ellipse(0.0050, 0.0060, 8), col, lib["brushed"],
                     lateral=(0.0, 0.0, 1.0)))

    # the cup recess: one rounded well, light plastic inside, a thin silver rim
    rings = []
    for d, s in ((0.0, 1.0), (0.004, 0.985), (0.058, 0.95), (0.071, 0.86), (0.073, 0.0)):
        rings.append([(x, y, CUP_Z - d) for (x, y) in _rr_pts(cx0, cy0, hx0 * s, hy0 * s, r0 * s)
                      ] if s > 0.0 else [(cx0, cy0, CUP_Z - d)] * (4 * 7))
    well = grid_mesh("int_console_cup0", rings, col, lib["leather_smooth"], wrap_t=True)
    M.orient(well.data, lambda c: (cx0 - c[0], cy0 - c[1], 0.5))
    made.append(well)
    # the cup pocket's bezel is a thick satin-metal frame (about 14 mm wide, chamfered) round the opening, with a pill pull tab
    # on the lid just behind it (Cabin 360 front panorama, close-up)
    ring = [(x, y, CUP_Z + 0.001) for (x, y) in _rr_pts(cx0, cy0, hx0 + 0.0050, hy0 + 0.0050, r0 + 0.005)]
    ring.append(ring[0])
    made.append(tube("int_console_cup_rim0", ring, ellipse(0.0075, 0.0030, 10), col, lib["brushed"],
                     lateral=(0.0, 0.0, 1.0)))
    made.append(F.box(col, "int_console_cup_tab", top(cx0 - hx0 - 0.030, 0.0, 0.0018), (0.014, 0.046, 0.0036),
                      lib["brushed"], r=0.0055))
    # three small rubber fins up the wall of the pocket (Cabin 360 close-up: they split it into two cup slots)
    for k, yf in enumerate((-0.052, 0.0, 0.052)):
        made.append(F.box(col, "int_console_cup_fin%d" % k, (cx0 + hx0 - 0.018, cy0 + yf, CUP_Z - 0.073 + 0.011),
                          (0.010, 0.012, 0.022), lib["leather_smooth"], r=0.0045))

    # the black gloss strip down each side of the lid
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        path = [(-0.170 + 0.200 * k / 14.0, side * (_hw(-0.170 + 0.200 * k / 14.0) + 0.0006), 0.832 - 0.030 * k / 14.0)
                for k in range(15)]
        made.append(tube("int_console_strip" + tag, path, ellipse(0.0068, 0.0026, 8), col, lib["piping_accent"],
                         lateral=(0.0, 0.0, 1.0)))
    # the console belongs to the front cockpit group (see FRONT_DX); every part is baked in model coordinates
    for ob in made:
        ob.location.x += FRONT_DX
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
    ob = grid_mesh(name, rows, col, lib["leather_smooth"])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    nrm = [(0.0, 0.0, 1.0)] * len(edge)
    st = stitches(name + "Stitch", edge[3:-3], nrm[3:-3], col, lib["thread_accent"])
    # the lit slit on the pod's inboard face (Cabin 360: a long dark slot with a thin lime line in it): a black tube, a lime
    # tube on it, over the straight middle of the armrest (its ends taper), in the piping accent so a trim recolours it
    i0, i1 = int(0.18 * n), int(0.80 * n)
    slot, line = [], []
    for k in range(i0, i1 + 1):
        x, z = path[k][0], path[k][2]
        y0 = dc.skin_y(x, z) - dc.th(z)
        slot.append((x, side * (y0 - width * 0.985), z - 0.020))
        line.append((x, side * (y0 - width * 0.985 - 0.0020), z - 0.020))
    sl = tube(name + "Slot", slot, ellipse(0.0042, 0.0042, 8), col, lib["satin"], lateral=(0.0, 0.0, 1.0))
    li = tube(name + "Slit", line, ellipse(0.0016, 0.0016, 6), col, lib["piping_accent"], lateral=(0.0, 0.0, 1.0))
    return [ob, st, sl, li]


PLEAT_H = 0.095          # the pleated strip's height under the belt line (Cabin 360 door close-up: a narrow band, not the whole upper door)


def _speaker(col, name, centre, normal, r, lib):
    """A door speaker: a softly domed round grille of fine perforated grey metal in a thin brushed rim (Cabin 360: finely perforated,
    silver-grey, not a black hole), with the fine concentric ridges the close-ups show (c3_0001: rings like a record's), which the
    perforation map alone never showed at the viewer's scale (2026-11-21). The disc's UVs are laid planar in metres so the
    perforation map tiles evenly."""
    from carkit.interior.sweep import grid_mesh as _grid
    N = Vector(normal).normalized()
    e1 = N.orthogonal().normalized()
    e2 = N.cross(e1).normalized()
    C = Vector(centre)
    n_rings, n_around = 30, 56
    rows = []
    for k in range(n_rings + 1):
        s_ = 1.0 - k / float(n_rings)
        h = 0.004 * (1.0 - s_ * s_) + (0.0007 if (k % 2 == 0 and 0 < k < n_rings) else 0.0)
        rows.append([tuple(C + (e1 * math.cos(2 * math.pi * j / n_around) + e2 * math.sin(2 * math.pi * j / n_around))
                           * (r * max(s_, 1e-4)) + N * h) for j in range(n_around)])
    ob = _grid(name, rows, col, lib["speaker"], wrap_t=True)
    M.orient(ob.data, lambda c: tuple(N))
    made = [ob]
    path = [tuple(C + (e1 * math.cos(2 * math.pi * j / n_around) + e2 * math.sin(2 * math.pi * j / n_around)) * r)
            for j in range(n_around)]
    path.append(path[0])
    made.append(tube(name + "_Rim", path, ellipse(0.0024, 0.0024, 8), col, lib["brushed"], lateral=tuple(N)))
    me = ob.data
    uv = me.uv_layers.active
    if uv is None:
        uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            d = Vector(me.vertices[me.loops[li].vertex_index].co) - C
            uv.data[li].uv = (e1.dot(d), e2.dot(d))
    return made


def build_doors(col, lib):
    """Front & rear door cards styled after cabin_tail_1.jpg #60 and cabin_1.jpg #3-10.

    2026-11-19: the pleated cloth is a narrow strip under the belt line (PLEAT_H), the door's main body between that strip and the
    pale pod is smooth matte soft-touch (the wheel's fabric, a step lighter than the pleats: Cabin 360 door close-up), the speakers
    are perforated grey metal, the window switches sit flush in a dark slot in the armrest."""
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = front_card(side)
        pre = "int_door_%s_" % tag
        xr, xf = dc.xr, dc.xf
        # c10_0001/0004, c3_0003/0044: a pale pod round the armrest with a black pocket window in it, the ribbed periwinkle
        # fabric above it up to the belt, a round speaker on the fabric near the A-pillar
        pod_bot = lambda x: 0.640 + 0.020 * _smooth((x - 0.10) / 0.65)
        pod_top = lambda x: 0.826 + 0.055 * _smooth((x + 0.08) / 0.72)
        rail_bot = pod_top
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(1.21) + 0.004, xf(1.19) - 0.004, _belt_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.495,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_smooth"], lambda x: 0.495, pod_bot,
                            x0=xr, x1=xf, nx=52, nz=18, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["door_pleat"], lambda x: _belt_z(x) - PLEAT_H,
                            lambda x: _belt_z(x) - 0.002, proud=0.002, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        made.append(dc.band(pre + "Body", col, lib["wheel_fabric"], pod_top,
                            lambda x: _belt_z(x) - PLEAT_H + 0.001, proud=0.0015, x0=xr, x1=xf, nz=10,
                            edge_round=0.004, mirror=False))
        made.append(dc.band(pre + "White", col, lib["leather_smooth"], pod_bot,
                            lambda x: pod_top(x) - 0.002, proud=0.006, x0=xr, x1=xf,
                            nx=52, nz=14, mirror=False))
        made.append(dc.band(pre + "Pocket", col, lib["satin"], lambda x: pod_bot(x) + 0.030,
                            lambda x: pod_bot(x) + 0.125, proud=0.0075, x0=lambda z: -0.02,
                            x1=lambda z: 0.58, nx=30, nz=6, edge_round=0.0, mirror=False))
        pts = dc.curve([(0.78 - 0.88 * k / 24.0, rail_bot(0.78 - 0.88 * k / 24.0) - 0.004)
                        for k in range(25)], proud=0.007)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
        made += _speaker(col, pre + "Speaker", dc.point(0.64, 0.965, 0.0045), (0.0, -side, 0.0), 0.038, lib)
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-0.08, 0.805), (0.16, 0.822), (0.42, 0.842), (0.64, 0.862)])
        # the window switches: a dark slot let into the armrest's top and three pale keys flush in it (the armrest's top at x is
        # 0.842 + 0.020 (x - 0.42) / 0.22; keys stand 1.5 mm proud, the old black blocks stood 10 mm)
        zt = lambda x: 0.842 + 0.020 * (x - 0.42) / 0.22
        xs0 = 0.44 + 0.048
        ys0 = side * (dc.skin_y(xs0, 0.855) - dc.th(0.855) - 0.036)
        made.append(F.box(col, pre + "SwitchSlot", (xs0, ys0, zt(xs0) - 0.0008), (0.150, 0.026, 0.0024),
                          lib["satin"], r=0.0045))
        for k in range(3):
            xk = 0.44 + 0.048 * k
            made.append(F.box(col, pre + "Switch%d" % k, (xk, ys0, zt(xk) + 0.0004), (0.030, 0.018, 0.0032),
                              lib["brushed"], r=0.0035))

    # Rear door cards
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        rb = lambda x: 0.862 + 0.020 * _smooth((x + 1.0) / 0.6)          # the pod's top, just above the armrest
        wb = lambda x: 0.650
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(1.27) + 0.008, xf(1.21) - 0.004,
                                _rear_top_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.495,
                               lambda x: _rear_top_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_smooth"], lambda x: 0.495, wb,
                            x0=xr, x1=xf, nz=16, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["door_pleat"], lambda x: _rear_top_z(x) - PLEAT_H,
                            lambda x: _rear_top_z(x) - 0.002, proud=0.002, x0=xr, x1=xf, nz=6,
                            edge_round=0.006, mirror=False))
        made.append(dc.band(pre + "Body", col, lib["wheel_fabric"], rb,
                            lambda x: _rear_top_z(x) - PLEAT_H + 0.001, proud=0.0015, x0=xr, x1=xf, nz=8,
                            edge_round=0.004, mirror=False))
        made.append(dc.band(pre + "White", col, lib["leather_smooth"], wb,
                            lambda x: rb(x) - 0.002, proud=0.006, x0=xr, x1=xf, nz=12, mirror=False))
        made.append(dc.band(pre + "Pocket", col, lib["satin"], lambda x: wb(x) + 0.035,
                            lambda x: wb(x) + 0.125, proud=0.0075, x0=lambda z: -0.95,
                            x1=lambda z: -0.40, nx=24, nz=6, edge_round=0.0, mirror=False))
        pts = dc.curve([(-0.26 - 0.82 * k / 20.0, rb(-0.26 - 0.82 * k / 20.0) - 0.004)
                        for k in range(21)], proud=0.006)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0018, lateral=(0.0, 0.0, 1.0)))
        made += _door_armrest(dc, pre + "Armrest", col, lib, side,
                              [(-1.02, 0.815), (-0.74, 0.825), (-0.42, 0.835)], width=0.060)
        made += _speaker(col, pre + "Speaker", dc.point(-0.52, 0.940, 0.0045), (0.0, -side, 0.0), 0.034, lib)
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
    # Cabin 360: a wide, slim, frameless mirror (about 21 x 8 cm) whose glass reads silver-white against the glass behind it
    w, h, t = 0.215, 0.074, 0.014
    made.append(F.round_slab(col, "int_rvmirror", MIRROR_C, w, h, t, 0.024, lib["piano"],
                             tilt=math.radians(8.0)))
    mg = bpy.data.materials.get("INT_Mirror") or bpy.data.materials.new("INT_Mirror")
    mg.use_nodes = True
    bm = next(n for n in mg.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bm.inputs["Base Color"].default_value = (0.62, 0.64, 0.66, 1.0)
    bm.inputs["Metallic"].default_value = 1.0
    bm.inputs["Roughness"].default_value = 0.10
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
    xs = [0.26 - 0.16 * k / 10.0 for k in range(11)]       # (0.10 further forward with the mirror: the lamp unit sits just behind it)
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.12 * (1 - 2 * j / 10.0), zr - 0.015 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["piano"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    # the lamp unit in its underside (Cabin 360 roof views: a silver-rimmed pill with a few small dark buttons in it)
    xl = 0.180
    zl = S.Z_ROOF(xl) - 0.0615
    ring = [(x, y, zl) for (x, y) in _rr_pts(xl, 0.0, 0.052, 0.021, 0.019)]
    ring.append(ring[0])
    made.append(tube("int_overhead_rim", ring, ellipse(0.0026, 0.0020, 8), col, lib["brushed"], lateral=(0.0, 0.0, 1.0)))
    for k, yb in enumerate((-0.026, 0.0, 0.026)):
        made.append(F.box(col, "int_overhead_btn%d" % k, (xl, yb, zl - 0.0004), (0.022, 0.016, 0.0030),
                          lib["satin"], r=0.0035))

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

    # 2026-11-19: a contoured trim panel, not a tube: the band is 1.5 cm wider and its crown a third as high (bulge 0.034 -> 0.010: it
    # read as a fat round cylinder in the viewer; the Cabin 360 A-pillar is a wide, flat, soft-edged panel with a vent slot and the
    # camera pod low on it)
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs,
                             lambda x: (x, S.v_along(x, PN.v_up(x, max(PN.BELT_Z(0.68), PN.z_a(min(x, PN.A_FOOT[0])))), -0.040)),
                             lambda x: (x, S.v_along(x, PN.V_A(x), 0.018)),
                             depth=0.010, bulge=0.010, nt=16, name="int_apillar"))
    # Driver A-pillar DMS camera pod (cabin_tail_1.jpg #50; Cabin 360: a small pod about 2.5 cm wide, low on the pillar)
    made.append(F.box(col, "int_apillar_dms", (0.560, 0.675, 1.290), (0.020, 0.024, 0.016),
                      lib["satin"], r=0.004))

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

    xs = [PN.X_DLO_TIP + 0.030 - (PN.X_DLO_TIP + 0.030 + 2.05) * k / 24.0 for k in range(25)]

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

    import mona_rear as RR
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
    # the gold-standard pass for the Mona's own keys: collars, bevels, wheel and door icons (mona_polish.py)
    __import__("mona_polish").build(col, lib)
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
