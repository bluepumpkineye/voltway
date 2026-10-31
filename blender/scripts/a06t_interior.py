"""Avatr 06T cabin: the Misty Purple / Cotton White interior, built from the 06T's own photographs.

References: blender/reference/avatr-06t/interior (_sources.md; Autohome series 8538, the board R1_interior_refs.jpg
approved by the owner 2026-10-31). Hardpoints come from the solved camera of c10_0001 (a06t_cabinsolve) and the
open-door photographs (c3_0001, c3_0041):

    15.6 in screen  centre (0.372, 0, 1.058), upright, on the console's arch          a06t_cockpit
    display band    x ~0.58, z 1.124 .. 1.218; the 35.4 in display and two 6.7 in e-mirror displays in it
    wheel           centre (0.25, 0.39, 1.045), a 0.385 x 0.31 squircle
    front seats     the cushion's crest at x ~0.42, z ~0.70-0.73 through the camera: the bight at x -0.03,
                    z 0.605 (it was -0.175 / 0.585 with the Luxeed RX seat, whose backrest then stood behind the
                    B-pillar - the owner's "front seats too far back")                  a06t_seats
    console         a floating white bridge, the screen on its arch                     a06t_console

The shell (floor, pillars, headliner, closures, boot side) is fitted to the 06T body and kept from the first build;
its trims now wear the 06T's materials.

Axes: +X forward, +Y left (the driver's side - China is LHD), +Z up.
"""
import math

import bpy
from mathutils import Matrix, Vector

import a06t_surface as S
import a06t_panels as PN
from carkit import mesh as M
from carkit import materials as MB
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "A06T_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.360                 # underbody 0.195 + the SU7's 0.17 of floor structure
DRIVER_Y = 0.400
PASS_Y = -0.400

FRONT_BIGHT_X, FRONT_BIGHT_Z = 0.150, 0.605
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.200, 0.610, 0.370

MIRROR_C = (0.250, 0.000, 1.350)           # frameless, 225 mm

# the palette, linear, read against the Cotton White seat in c3_0001 / c10_0001 (sample.cjs)
WHITE = (0.600, 0.590, 0.565)              # Cotton White Nappa
PURPLE = (0.165, 0.152, 0.212)             # Misty Purple Nappa (the seat's yoke: 0.18, 0.17, 0.23 lit)
TRIM = (0.205, 0.192, 0.262)               # the dash / door soft-touch, a shade lighter than the Nappa
CARPET = (0.050, 0.040, 0.046)
HEADLINER = (0.120, 0.112, 0.142)


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def z_glass(x, y):
    """Height of the windscreen (the body's upper surface) at (x, |y|)."""
    v = S.v_at_y_upper(x, max(0.0, min(abs(y), 0.68)))
    return S.section_v(x, v)[1]


# -------------------------------------------------------------- materials
def _perf_image(name, color, maps):
    """Perforated Nappa's base colour: the colour with the holes darkened, baked to pixels so it survives glTF."""
    import numpy as np
    from carkit.textures import TEX_DIR
    import os
    msk = maps["perf_mask"]
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


def perforation_maps(size=512, pitch_px=32, radius=0.13, strength=10.0):
    """Perforated Nappa's holes: ~1 mm round holes on a 4 mm hex pitch (c3_0012: fine, dense perforation)."""
    import numpy as np
    from carkit import surfacemaps as SM
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    row = np.floor(yy / (pitch_px * 0.866))
    cx = (xx + (row % 2) * pitch_px * 0.5) % pitch_px - pitch_px * 0.5
    cy = (yy % (pitch_px * 0.866)) - pitch_px * 0.433
    d = np.sqrt(cx * cx + cy * cy) / pitch_px
    hole = np.clip((radius - d) / 0.04, 0.0, 1.0)
    nrm = SM._image("T_PerfA06T_Normal", SM.height_to_normal(-hole, strength / size * 60.0),
                    filename="t_perf_a06t_normal.png")
    mask = np.repeat((1.0 - 0.70 * hole)[..., None], 3, axis=2)
    msk = SM._image("T_PerfA06T_Mask", mask, non_color=True, filename="t_perf_a06t_mask.png")
    return nrm, msk


def perforated(name, color, maps, tile=0.064):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.44, specular=0.5, coat=0.08, coat_rough=0.30, ior=1.45,
                  sheen=0.0)
    IM._textured(nt, b, maps["perf"], tile, 0.7)
    _mapped_image(nt, b, _perf_image("T_Perf_" + name[4:], color, maps), tile, "Base Color")
    return m


def _plain(name, base, roughness, maps=None, grain=None, tile=0.10, **kw):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=roughness, **kw)
    if grain:
        IM._textured(nt, b, maps[grain], tile, kw.get("strength", 0.6))
    return m


def build_library():
    from carkit import surfacemaps as SM
    maps = SM.build_all()
    maps["perf"], maps["perf_mask"] = perforation_maps()
    lib = IM.build_library(accent=PURPLE, maps=maps, stitch=(0.30, 0.28, 0.36))
    # the two trim-swap hooks (avatr-06t.ts trims[].colors): INT_Leather_White and INT_Leather_Purple
    lib["leather_white"] = IM.leather("INT_Leather_White", WHITE, maps, roughness=0.42, coat=0.08)
    lib["leather_white_perf"] = perforated("INT_Leather_White_Perf", tuple(c * 0.97 for c in WHITE), maps)
    lib["leather_purple"] = IM.leather("INT_Leather_Purple", PURPLE, maps, roughness=0.40, coat=0.10)
    lib["leather_accent"] = lib["leather_purple"]
    lib["wheel_leather"] = lib["leather_purple"]
    lib["trim_purple"] = _plain("INT_Trim_Purple", TRIM, 0.62, maps, "leather", 0.06, specular=0.40, sheen=0.10)
    # the dash's top under the windscreen: a dark matte skin (c10_0001: sRGB ~50 where the face reads ~160; every car's is
    # dark, or the windscreen mirrors it). In the face's lilac it showed from outside as a pale slab filling the windscreen
    lib["dash_top"] = _plain("INT_Dash_Top", (0.010, 0.009, 0.012), 0.98, maps, "leather", 0.06, specular=0.04)
    lib["plastic_white"] = _plain("INT_Plastic_White", tuple(c * 0.98 for c in WHITE), 0.34, specular=0.45)
    lib["plastic_grey"] = _plain("INT_Plastic_Grey", (0.30, 0.29, 0.30), 0.40)
    # champagne satin: at 0.66 the hall's bright room made it read as white plastic
    lib["satin_metal"] = _plain("INT_Satin_Silver", (0.50, 0.48, 0.44), 0.32, metallic=1.0)
    lib["thread_white"] = _plain("INT_Thread_White", (0.50, 0.49, 0.47), 0.6)
    lib["thread_purple"] = _plain("INT_Thread_Purple", (0.26, 0.24, 0.32), 0.6)
    lib["headliner"] = IM.alcantara("INT_Headliner", HEADLINER, maps, sheen=0.35, tint=(0.40, 0.38, 0.46))
    m = lib["carpet"]
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = CARPET + (1.0,)
    # the Meridian grilles: satin, half metallic - a full metal mirrored the dark cabin and read black
    lib["speaker_silver"] = _plain("INT_Speaker_Silver", (0.62, 0.61, 0.60), 0.42, maps, "perforation",
                                   SM.TILE["perforation"], metallic=0.5)
    # the e-mirror displays show the camera picture: a pale lavender-grey glow (c10_0001: sRGB 184, 180, 210)
    m, nt, b = MB.mat("INT_Display_Mirror")
    MB.set_inputs(b, base=(0.30, 0.29, 0.40), metallic=0.0, roughness=0.08, coat=1.0, coat_rough=0.02)
    b.inputs["Emission Color"].default_value = (0.42, 0.40, 0.56, 1.0)
    b.inputs["Emission Strength"].default_value = 1.0
    lib["display_mirror"] = m
    return lib



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


def _rear_top_z(x):
    return _belt_z(x)


def rear_card(side):
    from carkit.interior.door import DoorCard
    th = Curve([(0.40, 0.095), (0.60, 0.125), (0.75, 0.140), (0.90, 0.130), (1.05, 0.100),
                (1.20, 0.072), (1.30, 0.060)], mode="pchip")
    return DoorCard(S.BODY, lambda z: PN.X_BPILLAR - 0.006,
                    lambda z: PN._DOOR_R_EDGE(z) + 0.006, 0.40, _rear_top_z, th,
                    v_top=max(PN.V_BELT(x) for x in (-1.39, -1.0, -0.4)) + 0.015, side=side)


# ---------------------------------------------------------------- the shell
X_OPEN_F, X_OPEN_R = -0.200, -1.430      # the glass roof's opening in the headliner
# The exterior's roof glass now stops at the B-pillar (a06t_panels.
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
    # (ends at x -2.24: the loft runs on to -2.47 but the body behind the cap's join is the tail cap, 4-6 cm shorter since
    # 2026-10-28; the trim used to run to -2.44 and stood out of the paint as a grey plate with any door open: porting/poke_probe_a06t.py)
    xs = [PN.X_DLO_TIP + 0.030 - (PN.X_DLO_TIP + 0.030 + 2.24) * k / 24.0 for k in range(25)]

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
    # the haunches, a06t_surface Y_GLASS) - and a chord across it left the
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
    made.append(CB.wall(col, lib["trim_purple"],
                        [(x_open + (1.06 - x_open) * k / 16.0, kick_y(x_open + (1.06 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.93, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["trim_purple"],
                        [(x_open, yk + (0.90 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.00 + 0.10 * _smooth((y - 0.78) / 0.04),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))
    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = rear_card(1.0)
    vq = max(PN.V_BELT(x) for x in (-1.40, -1.55)) + 0.10
    # the hump wall stands inboard of the wheel liner's inner wall (|y| 0.670: y_outer 0.920 less its 0.250 depth)
    # and rolls over above its top (0.93): lower, the liner showed behind the
    # rear door from both rows (carkit.qa.leaks)
    # (the rear door's trailing edge now stands level with the wheel arch's rear half, so the arch liner's front
    # quarter, x -0.96 .. -1.17, stood inboard of the door card, in the cabin: below z 0.70 the trim runs forward
    # over it)
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["trim_purple"],
        lambda z: PN._DOOR_R_EDGE(z) - 0.002 + 0.25 * (1.0 - _smooth((z - 0.70) / 0.25)), -1.82,
        FLOOR_Z + 0.02, 0.650, 0.975, 1.205, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)
    # the parcel shelf: from behind the rear seat backs to the backlight's base.
    # The backlight's clear pane (a06t_rear.pane()) slopes down toward the tail: z 1.20 at x -2.21, 1.13 at -2.31, 1.00 at
    # the tail (-2.47). The shelf and the sill below stay behind it: they were once built to a pane that rose toward the
    # tail, so their rear ends stood 10-16 cm out of the glass, and with a door open (the cabin no longer stencilled to
    # the glass) they showed as black wings either side of the rear window
    import a06t_rear as RR
    pane = RR.pane()
    x_of0, z_a0 = pane.column(0.0)
    pane_z = Curve([(pane.corner(x_of0(z), 0.0, z, z_a0), z) for z in
                    [pane.z_bot(0.0) + (pane.z_top(0.0) - pane.z_bot(0.0)) * k / 24.0 for k in range(25)]],
                   mode="pchip")
    pts = []
    for k in range(17):
        # ends at x -2.235, a few cm inside the glass's foot (x -2.283 at z 1.093); it ran to -2.46, up to 16 cm behind the tail
        x = -1.56 - (2.235 - 1.56) * k / 16.0
        z = 1.050 + 0.105 * (k / 16.0) ** 1.8 + 0.035 * _smooth((x + 2.30) / -0.14)
        pts.append((x, min(z, pane_z(x) - 0.014) if x < -2.10 else z))
    made.append(CB.bulkhead(col, lib["headliner"], pts,
                            lambda x, z: CB.skin_offset_y(S.BODY, x, z, 0.070, 0.80),
                            name="int_parcel_shelf", facing=(0.0, 0.0, 1.0)))
    # the rear window's sill: from the shelf down to the pane's lower edge (which meets the tail cap at x -2.47 on the
    # centreline), a hand's breadth inside the glass and no wider than the pane
    rows = []
    for j in range(17):
        y = min(0.53, pane.y_w - 0.015) * j / 16.0
        x_of, z_a = pane.column(y)
        zb = pane.z_bot(y) + 0.004
        xb = pane.corner(x_of(zb), y, zb, z_a) + 0.014
        # its start 6 cm ahead of its end at every y (a fixed -2.200 stood up to 5 cm behind the glass at the pane's sides,
        # where the glass curves forward to x -2.15)
        xa, za = xb + 0.060, 1.100
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


def cluster_image(path=None):
    """The 35.4 in panoramic display's picture (a06t_cockpit), for export_a06t."""
    import a06t_cockpit as CK
    return CK.cluster_image(path)


def main(lights=True):
    col = bpy.data.collections.get(COLLECTION)
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(col)
    col = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(col)
    import a06t_cockpit as CK
    import a06t_console as CO
    import a06t_seats as SE
    lib = build_library()
    build_shell(col, lib)
    CK.build_dash(col, lib)
    CK.build_screens(col, lib)
    CK.build_wings(col, lib)
    CK.build_wheel(col, lib)
    SE.build_front(col, lib, FRONT_BIGHT_X, FRONT_BIGHT_Z, (DRIVER_Y, PASS_Y), FLOOR_Z)
    SE.build_rear(col, lib, REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y, FLOOR_Z)
    CO.build(col, lib)
    import a06t_doorcards as DC
    DC.build(col, lib)
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
