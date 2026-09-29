"""The catalogue contact sheet: every standalone preset, built and rendered.

    import carkit.preview as PV
    PV.contact_sheet()        # resets the scene; -> renders/catalogue/contact_sheet.png

Each part is built exactly as a car would build it, in car coordinates, then
parented to an empty that spins it to a 3/4 view and places it in its cell.
Surface-bound parts are shown on a flat stand-in panel, which is enough to
judge proportions and detailing; on a car they follow its body.
"""
import math
import os

import bpy
from mathutils import Euler

from . import geom, materials, scene
from . import mesh as M
from .parts import aero, fittings, grilles, lamps, wheels

OUT_DIR = os.path.join(scene.RENDER_DIR, "catalogue")
CELL_W, CELL_H = 1.60, 1.25
COLS, ROWS = 6, 4


def _flat_proud(y0=0.95):
    """A stand-in flank: the plane y = y0, normal +Y."""
    def proud(p, d):
        return (p[0], y0 + d, p[2]), (0.0, 1.0, 0.0)
    return proud


def _flat_front(x0=0.0):
    """A stand-in nose face: the plane x = x0, normal +X."""
    def place(p, d):
        return (x0 + d, p[1], p[2]), (1.0, 0.0, 0.0)
    return place


def _panel(name, collection, mat, corners):
    return M.obj(name, corners, [[0, 1, 2, 3]], collection, mat, smooth=False)


def _label(text, collection, mat, loc, size=0.075):
    t = M.text_mesh("LBL_" + text.replace(" ", "_"), text, size, collection, mat)
    t.location = loc
    t.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    return t


def _place(objs, collection, name, loc, view=(0.0, 0.0), scale=1.0):
    """Parent a part to an empty that spins it to azimuth view[0] (about the
    vertical, degrees), tilts it view[1] toward the camera, and puts it at loc.

    Azimuths for common parts, with the camera looking along +Y:
        +45  rear-right 3/4 (wings, spoilers, ducktails, diffusers)
        -45  front-right 3/4 (splitters)
        -90  front face on (grilles, lamps, plates)
        180  left flank face on (flank fittings built on +Y)
    """
    e = bpy.data.objects.new("CELL_" + name, None)
    collection.objects.link(e)
    e.location = loc
    e.rotation_mode = 'ZXY'           # spin about Z first, then tilt about X
    e.rotation_euler = Euler((math.radians(view[1]), 0.0, math.radians(view[0])), 'ZXY')
    e.scale = (scale, scale, scale)
    for o in objs:
        if o.parent is None:
            o.parent = e
    return e


def _no_mirror(objs):
    for o in objs:
        for md in list(o.modifiers):
            if md.type == 'MIRROR':
                o.modifiers.remove(md)
    return objs


def _label_mat():
    m = bpy.data.materials.get("M_Label") or bpy.data.materials.new("M_Label")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs["Color"].default_value = (0.80, 0.80, 0.80, 1.0)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def build_sheet(lib, col):
    lab = _label_mat()
    cells = []

    def add(objs, name, text, c, r, view=(0.0, 0.0), scale=1.0, dz=0.0):
        x, z = c * CELL_W, -r * CELL_H
        _place(objs, col, name, (x, 0.0, z + dz), view, scale)
        _label(text, col, lab, (x, -1.2, z - 0.56))
        cells.append(name)

    # ---- row 0: wheels. sign -1 (a right-hand corner) faces the camera.
    for c, key in enumerate(("su7_ultra_hairpin", "aero_5window", "turbine_10",
                             "y_spoke_5", "twin_5", "multi_10")):
        e, parts = wheels.build_wheel(col, "CK_%s_" % key, "RR", (0.0, 0.0, 0.0), -1,
                                      lib, wheels.PRESETS[key], 0.265, 0.3595, 0.215, 150.0)
        add([e], "wheel_" + key, key, c, 0, view=(18.0, 0.0), scale=1.25, dz=0.06)

    # ---- row 1: aero
    wing = aero.rear_wing(
        "CK_Wing", col, lib, (0.15, 0.0), (-0.15, 0.036), 0.62,
        endplate=dict(pts=[(0.08, -0.08), (0.085, 0.012), (-0.115, 0.04),
                           (-0.155, 0.012), (-0.095, -0.028)]),
        pylons=dict(style="triangle_cutout", y=0.30, x_deck=(0.12, -0.03),
                    x_wing=(-0.08, 0.02), deck_z=lambda x, y: -0.16))
    add(wing, "rear_wing", "rear_wing", 0, 1, view=(40.0, 28.0), scale=0.95)

    spoiler = aero.roof_spoiler("CK_RoofSpoiler", col, lib,
                                lambda y: (0.0, -0.01 * (y / 0.60) ** 2), 0.60)
    add([spoiler], "roof_spoiler", "roof_spoiler", 1, 1, view=(40.0, 30.0))

    duck = aero.ducktail("CK_Ducktail", col, lib, lambda x: 0.0,
                         lambda y: -0.10 + 0.30 * (y / 0.60) ** 1.8, half_width=0.60)
    add([duck], "ducktail", "ducktail", 2, 1, view=(40.0, 30.0))

    le = [(0.000, 0.30, 0.0), (0.30, 0.27, 0.0), (0.55, 0.20, 0.01), (0.66, 0.10, 0.02)]
    spl = aero.splitter("CK_Splitter_", col, lib, le,
                        zones=(("Centre", 0.0, 0.40, "carbon"), ("Wing", 0.40, 0.66, "paint")),
                        x_te=lambda y, xle: xle - 0.16)
    add(spl, "splitter", "splitter", 3, 1, view=(-40.0, 32.0))

    dif = aero.diffuser("CK_Diffuser", col, lib, lambda y: -0.20 + 0.06 * (y / 0.6) ** 2,
                        x_front=0.20, half_width=0.60, z=(0.0, 0.03, 0.09),
                        fins=(0.0, 0.2, 0.4), fin_z=(0.0, 0.095, 0.18, 0.015))
    add(dif, "diffuser", "diffuser", 4, 1, view=(40.0, -22.0))

    skirt = aero.side_skirt("CK_Skirt", col, lib, _flat_proud(0.0), lambda x: 0.0,
                            -0.6, 0.6, -0.05, 0.06, nx=24, nz=4)
    add([skirt], "side_skirt", "side_skirt", 5, 1, view=(15.0, 12.0))

    # ---- row 2: grilles on a satin-black backing, and a lamp
    for c, (key, fn, kw) in enumerate((
            ("diamond", grilles.diamond, {}),
            ("hexagon", grilles.hexagon, dict(cell=0.034)),
            ("slats", grilles.slats, dict(count=6, angle_deg=-12.0)),
            ("dots", grilles.dots, dict(pitch=0.030, r=0.006)))):
        g = fn("CK_Grille_" + key, -0.30, 0.30, -0.16, 0.16, lambda y, z: 0.0, 0.0,
               col, lib["grille"], **kw)
        back = _panel("CK_GrilleBack_" + key, col, lib["shadow"],
                      [(-0.03, -0.33, -0.19), (-0.03, 0.33, -0.19), (-0.03, 0.33, 0.19),
                       (-0.03, -0.33, 0.19)])
        add([g, back], "grille_" + key, "grille " + key, c, 2, view=(-72.0, 6.0), scale=1.45)

    lo = geom.polyline([(0.0, -0.25, -0.02), (0.0, 0.0, -0.05), (0.0, 0.25, -0.01)], 40)
    up = geom.polyline([(0.0, -0.25, 0.02), (0.0, 0.0, 0.04), (0.0, 0.25, 0.07)], 40)
    place = _flat_front(0.0)
    out = geom.const((1.0, 0.0, 0.0))
    lmp = [lamps.lens("CK_Lamp_Lens", lo, up, place, col, lib["lamp_smoked"], 6,
                      lambda k, n: 0.004 + 0.0016 * math.sin(math.pi * k / n), out,
                      mirror=False)]
    lmp += lamps.seals("CK_Lamp_Seal", lo, up, place, col, lib["grille"], out, mirror=False)
    lmp.append(lamps.band_between("CK_Lamp_DRL", lo, up, range(2, 38), (0.18, 0.25, 0.32),
                                  place, lambda k: 0.0048, col, lib["led_white"], out,
                                  mirror=False))
    for i, y in enumerate((0.10, 0.16)):
        best = lamps.station_nearest_y(lo, up, y)
        c3 = geom.lerp(lo[best], up[best], 0.62)
        lmp += lamps.projector("CK_Lamp_Proj%d" % i, (0.0055, c3[1], c3[2]), (1, 0, 0),
                               0.014, col, lib, mirror=False)
    lmp.append(_panel("CK_LampBody", col, lib["paint"],
                      [(-0.001, -0.32, -0.12), (-0.001, 0.32, -0.12), (-0.001, 0.32, 0.14),
                       (-0.001, -0.32, 0.14)]))
    add(lmp, "lamp", "lamp between edges", 4, 2, view=(-72.0, 6.0), scale=1.7)

    # ---- row 3: fittings
    prd = _flat_proud(0.0)
    mir = _no_mirror(fittings.mirror_head("CK_Mirror", col, lib, (0.0, 0.10, 0.0),
                                          (0.235, 0.105, 0.095), (0.05, 0.0, -0.06), prd))
    add(mir, "mirror", "mirror_head", 0, 3, view=(125.0, 12.0), scale=2.6)

    door = [_panel("CK_Door", col, lib["paint"],
                   [(-0.55, -0.001, -0.25), (0.55, -0.001, -0.25), (0.55, -0.001, 0.25),
                    (-0.55, -0.001, 0.25)])]
    door.append(fittings.flush_handle("CK_Handle", 0.35, 0.05, 0.12, prd, col,
                                      lib["black_gloss"], y_ref=0.0))
    door += fittings.vent("CK_Vent", [(-0.10, -0.12), (-0.25, -0.13), (-0.42, -0.14)],
                          [(-0.10, -0.07), (-0.25, -0.05), (-0.42, -0.03)], prd, col, lib)
    door.append(fittings.outline_ring("CK_Flap", 0.10, 0.34, -0.20, -0.02, 0.028, prd, col,
                                      lib["shadow"], y_ref=0.0))
    add(_no_mirror(door), "flank_fittings", "handle, vent, flap ring", 1, 3, view=(165.0, 8.0))

    lid = fittings.lidar_pod("CK_Lidar", col, lib["black_gloss"], 0.0, 0.0)
    add([lid], "lidar", "lidar_pod", 2, 3, view=(30.0, 25.0), scale=2.4, dz=-0.1)

    pl = fittings.plate("CK_Plate", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), col, lib,
                        texts=(("CARKIT", 0.0, 0.070, False, True),))
    add(pl, "plate", "plate + badge", 3, 3, view=(-72.0, 6.0), scale=1.5)

    e, parts = wheels.build_wheel(col, "CK_Brake_", "RR", (0.0, 0.0, 0.0), -1, lib,
                                  wheels.preset("su7_ultra_hairpin"), 0.305, 0.3582, 0.205,
                                  150.0)
    for p in parts:
        if any(s in p.name for s in ("Tyre", "Spokes", "RimBarrel", "RimFlange",
                                     "RimStripe")):
            p.hide_render = True
    add([e], "brake", "disc + caliper", 4, 3, view=(18.0, 0.0), scale=1.25)
    return cells


def contact_sheet(path=None, samples=128, res=(2400, 1280), reset=True):
    """Build every preset on a grid and render it. Returns the image path."""
    if reset:
        bpy.ops.wm.read_homefile(use_empty=True)
    col = bpy.data.collections.new("CATALOGUE")
    bpy.context.scene.collection.children.link(col)
    lib = materials.build_library()
    cells = build_sheet(lib, col)
    from . import build
    build.ensure_uvs([col])           # the carbon weave needs world-space UVs

    scene.world_gradient(top=(0.15, 0.155, 0.165), bottom=(0.045, 0.045, 0.05))
    scene.colour_management()
    cx = (COLS - 1) * CELL_W * 0.5
    cz = -(ROWS - 1) * CELL_H * 0.5
    for name, size, loc, power in (
            ("PV_Key", (10.0, 4.0), (cx - 5.0, -8.0, cz + 6.0), 1900.0),
            ("PV_Fill", (16.0, 8.0), (cx + 3.0, -13.0, cz + 1.0), 1700.0),
            ("PV_Rim", (12.0, 2.0), (cx, 9.0, cz + 3.0), 260.0)):
        d = bpy.data.lights.new(name, 'AREA')
        d.shape = 'RECTANGLE'
        d.size, d.size_y = size
        d.energy = power
        ob = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = loc
        scene.aim(ob, (cx, 0.0, cz))

    cam = bpy.data.objects.new("PV_Cam", bpy.data.cameras.new("PV_Cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = COLS * CELL_W + 0.2
    zc = cz - 0.12
    cam.location = (cx, -20.0, zc)
    scene.aim(cam, (cx, 0.0, zc))
    scn = bpy.context.scene
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scene.use_cycles(samples)
    os.makedirs(OUT_DIR, exist_ok=True)
    scn.render.filepath = path or os.path.join(OUT_DIR, "contact_sheet.png")
    scn.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print("contact sheet: %d cells -> %s" % (len(cells), scn.render.filepath))
    return scn.render.filepath
