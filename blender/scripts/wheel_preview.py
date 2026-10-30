"""One RX wheel rendered face-on and orthographic, to be laid over the unwarped
photograph it was traced from.

    blender -b --factory-startup --python-expr "import sys;
        sys.path.append(r'<repo>/blender/scripts'); import wheel_preview as P;
        P.face_on('yufeng', 'blender/renders/wheel_yufeng.png')"

The image is square with the wheel's lip circle at 0.45 of its width and the
axle through the centre - the convention of the polar-grid tool the photographs
are read with, so the same grid can be drawn over both. `side` is the side of
the car the wheel is on, seen from OUTSIDE: 'left' looks at it as the
photographs do (they all show the car's left), with the face as traced.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)


def _fresh():
    bpy.ops.wm.read_homefile(use_empty=True)
    for name in [m for m in sys.modules if m in ("rx_wheels", "rx_materials", "su7_wheels", "su7_materials", "zx_wheels", "zx_materials", "z9_wheels", "z9_materials", "g9l_wheels", "g9l_materials", "seal_wheels", "seal_materials", "a06t_wheels", "a06t_materials", "es8_wheels", "es8_materials")
                 or m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)


def build_one(design="yufeng", side="left", tag="T", front=True):
    """The wheel alone at the origin, axle along +Z (outboard up). design: an RX design
    (rx_wheels.DESIGNS) or "su7" for the SU7 Ultra's."""
    _fresh()
    from carkit import build as B
    from carkit.parts import wheels as W
    sign = 1 if side == "left" else -1
    if design == "su7":
        import su7_materials as MT
        import su7_wheels as SW
        lib = MT.build_library()
        col = B.fresh_collection("SU7_Wheels")
        prefix, spec = "SU7Ultra_", SW.SPEC
        spec.pop("_faces", None)
        w, r, dr = (0.265, 0.3595, 0.215) if front else (0.305, 0.3582, 0.205)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, w, r, dr, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design == "seal" or design.startswith("seal:"):
        import seal_materials as MT
        import seal_wheels as ZW
        prefix, spec = ZW.DESIGNS[design.split(":")[1] if ":" in design else "turbine_5"]
        lib = MT.build_library()
        col = B.fresh_collection("Wheels_seal")
        spec.pop("_faces", None)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, 0.235, 0.343, 0.178, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design.startswith("es8:"):
        # the Nio ES8's 22 in wheels: "es8:multi22" (standard) and "es8:lanyue"
        import es8_materials as MT
        import es8_wheels as ZW
        prefix, spec = ZW.DESIGNS[design.split(":")[1]]
        lib = MT.build_library()
        col = B.fresh_collection("Wheels_es8")
        spec.pop("_faces", None)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, 0.265, 0.385, 0.192, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design == "a06t" or design.startswith("a06t:"):
        # the Avatr 06T's 20 in turbine (traced from c1_0004's rear wheel); "a06t:star5" the Knight edition's Y spokes
        import a06t_materials as MT
        import a06t_wheels as ZW
        prefix, spec = ZW.DESIGNS[design.split(":")[1] if ":" in design else "turbine5"]
        lib = MT.build_library()
        col = B.fresh_collection("Wheels_a06t")
        spec.pop("_faces", None)
        w, r, dr = (0.255, 0.369, 0.190) if front else (0.255, 0.369, 0.180)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, w, r, dr, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design == "g9l_turbine":
        # the XPeng G9L's 21 in turbine (traced from c1_0053's right front wheel); the left wheels are the mirror image
        import g9l_materials as MT
        import g9l_wheels as ZW
        prefix, right, left = ZW.DESIGNS["turbine"]
        spec = right if sign < 0 else left
        lib = MT.build_library()
        col = B.fresh_collection("Wheels_g9l_turbine")
        spec.pop("_faces", None)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, 0.265, 0.377, 0.185, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design in ("z9", "g9l") or design.startswith("z9:"):
        # the Denza Z9's 21 in multi-spoke ("z9:pro20": the Pro's 20 in six-Y) and the XPeng G9L's 22 in five-spoke
        # (traced from c1_0036 / c1_0028)
        if design.startswith("z9"):
            import z9_materials as MT
            import z9_wheels as ZW
            prefix, spec = ZW.DESIGNS[design.split(":")[1] if ":" in design else "luxury"]
            w, r, dr = (0.275, 0.362, 0.185) if not front else (0.255, 0.362, 0.195)
        else:
            import g9l_materials as MT
            import g9l_wheels as ZW
            prefix, spec = ZW.DESIGNS["aero"]
            w, r, dr = (0.265, 0.377, 0.185)
        lib = MT.build_library()
        col = B.fresh_collection("Wheels_" + design)
        spec.pop("_faces", None)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, w, r, dr, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    if design == "zx" or design.startswith("zx:"):
        # the Zeekr 7X: "zx" is the six-Y, "zx:multi" and "zx:fork" the 20 in designs (zx_wheels.DESIGNS)
        import zx_materials as MT
        import zx_wheels as ZW
        lib = MT.build_library()
        col = B.fresh_collection("ZX_Wheels")
        prefix, spec = ZW.DESIGNS[design.split(":")[1] if ":" in design else "y"]
        spec.pop("_faces", None)
        w, r, dr = (0.265, 0.3647, 0.190) if front else (0.265, 0.3647, 0.180)
        empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, w, r, dr, 180.0)
        empty.matrix_world = Matrix.Identity(4)
        return spec, col, empty, parts, lib
    import rx_materials as MT
    import rx_wheels as RW
    lib = MT.build_library()
    col = B.fresh_collection("RX_Wheels")
    prefix, spec = RW.DESIGNS[design]
    spec.pop("_faces", None)
    w, r, dr = (0.255, 0.369, 0.190) if front else (0.275, 0.378, 0.180)
    empty, parts = W.build_wheel(col, prefix, tag, (0.0, 0.0, 0.0), sign, lib, spec, w, r, dr, 180.0)
    empty.matrix_world = Matrix.Identity(4)
    return spec, col, empty, parts, lib


def _stats(parts):
    out = {}
    for p in parts:
        dg = bpy.context.evaluated_depsgraph_get()
        me = p.evaluated_get(dg).to_mesh()
        out[p.name] = (len(me.vertices), sum(len(q.vertices) - 2 for q in me.polygons))
        p.evaluated_get(dg).to_mesh_clear()
    return out


def face_on(design="yufeng", out=None, side="left", size=1400, samples=48, front=True,
            hide=("Tyre",), accent=None, only=None, flat=False, dark=False, pitch=0.0,
            accent_pbr=None):
    """Build and render. hide: name fragments of parts to leave out of the picture;
    only: if given, the parts that are drawn, all others hidden; flat: draw them as
    plain white on a transparent ground (a mask of the face, to lay over the
    photograph); dark: a dark studio instead of the white overcast;
    accent: an (r, g, b) the accent material is painted (the blue variant), accent_pbr its
    (metallic, roughness) (the 7X twin-fork's silver: (1.0, 0.2));
    pitch: degrees the camera is lowered below the axle's line and aimed back up at it, which
    moves a deep part (the hub) down the picture by depth x tan(pitch) as in a photograph taken
    from a little off the axis (the 7X twin-fork's: 2.9, the lug nuts 15 px low)."""
    import time
    t = time.time()
    spec, col, empty, parts, lib = build_one(design, side, front=front)
    print("built %s in %.1f s" % (design, time.time() - t))
    for k, (nv, nt) in sorted(_stats(parts).items()):
        print("  %-24s %6d verts %6d tris" % (k, nv, nt))
    if accent is not None and "accent" in lib:
        b = next(n for n in lib["accent"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = tuple(accent) + (1.0,)
        if accent_pbr is not None:
            b.inputs["Metallic"].default_value = accent_pbr[0]
            b.inputs["Roughness"].default_value = accent_pbr[1]
    for p in parts:
        if any(h in p.name for h in hide) or (only and not any(h in p.name for h in only)):
            p.hide_render = True
    scn = bpy.context.scene
    if flat:
        white = bpy.data.materials.new("M_Flat")
        white.use_nodes = True
        nt = white.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        outn = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(em.outputs[0], outn.inputs[0])
        for p in parts:
            p.data.materials.clear()
            p.data.materials.append(white)
        scn.render.film_transparent = True
    big_r = spec["rim_d"] / 2.0
    # the camera above the face, looking down: up is +Y for the right wheel (the
    # local frame is the view from outside), -Y for the left (half a turn)
    cd = bpy.data.cameras.new("CAM")
    cd.type = 'ORTHO'
    cd.ortho_scale = 2.0 * big_r / 0.9
    cd.clip_start, cd.clip_end = 0.05, 5.0
    cam = bpy.data.objects.new("CAM", cd)
    scn.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 1.0)
    cam.rotation_euler = (0.0, 0.0, math.pi if side == "left" else 0.0)
    if pitch:
        # image up u0 and right r0 of the face-on camera, then the whole camera turned about r0
        a = math.radians(pitch)
        u0 = Vector((0.0, -1.0, 0.0)) if side == "left" else Vector((0.0, 1.0, 0.0))
        v0 = Vector((0.0, 0.0, -1.0))
        r0 = v0.cross(u0)
        v = v0 * math.cos(a) + r0.cross(v0) * math.sin(a)
        u = u0 * math.cos(a) + r0.cross(u0) * math.sin(a)
        m = Matrix(((r0.x, u.x, -v.x, 0.0), (r0.y, u.y, -v.y, 0.0), (r0.z, u.z, -v.z, 0.0),
                    (0.0, 0.0, 0.0, 1.0)))
        m.translation = -v * 1.0
        cam.matrix_world = m
    scn.camera = cam
    # a soft overcast and one key from upper left, as the photographs have
    w = bpy.data.worlds.new("W")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.82, 0.84, 0.88, 1.0)
    bg.inputs["Strength"].default_value = 0.9
    if dark:
        bg.inputs["Color"].default_value = (0.05, 0.055, 0.065, 1.0)
        bg.inputs["Strength"].default_value = 1.0
    ld = bpy.data.lights.new("KEY", 'AREA')
    ld.energy = 120.0
    ld.size = 1.2
    key = bpy.data.objects.new("KEY", ld)
    scn.collection.objects.link(key)
    key.location = (-0.5, 0.7, 0.9)
    key.rotation_euler = (Vector((0.0, 0.0, 0.0)) - key.location).to_track_quat('-Z', 'Y').to_euler()
    from carkit import scene as SC
    SC.use_cycles(samples)
    scn.view_settings.view_transform = 'Standard'
    scn.render.resolution_x = scn.render.resolution_y = size
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'
    if flat:
        scn.render.image_settings.color_mode = 'RGBA'
    out = out or os.path.join(_HERE, "..", "renders", "wheel_%s_%s.png" % (design, side))
    out = os.path.normpath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out, "%.1f s" % (time.time() - t))
    return out


def oblique(design="yufeng", out=None, side="left", az=35.0, el=8.0, size=1200, samples=64,
            accent=None, dist=2.0, lens=70.0, front=True, dark=True, accent_pbr=None):
    """The wheel from outside at `az` degrees to its axle (to the car's front, in the
    plane of the ground) and `el` above the horizon, a few lights and a dark ground:
    the way it is looked at in the showroom. The ground is not drawn."""
    spec, col, empty, parts, lib = build_one(design, side, front=front)
    if accent is not None and "accent" in lib:
        b = next(n for n in lib["accent"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = tuple(accent) + (1.0,)
        if accent_pbr is not None:
            b.inputs["Metallic"].default_value = accent_pbr[0]
            b.inputs["Roughness"].default_value = accent_pbr[1]
    scn = bpy.context.scene
    # car up in the wheel's frame: the left wheel's local +Y is down
    up = Vector((0.0, -1.0 if side == "left" else 1.0, 0.0))
    fwd = Vector((1.0, 0.0, 0.0))                       # local +X is the car's front
    a, e = math.radians(az), math.radians(el)
    pos = (Vector((0, 0, 1.0)) * math.cos(a) * math.cos(e) + fwd * math.sin(a) * math.cos(e)
           + up * math.sin(e)) * dist
    f = (Vector((0, 0, 0.03)) - pos).normalized()
    right = f.cross(up).normalized()
    up2 = right.cross(f)
    cd = bpy.data.cameras.new("CAM")
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.05, 20.0
    cam = bpy.data.objects.new("CAM", cd)
    scn.collection.objects.link(cam)
    m = Matrix(((right.x, up2.x, -f.x, pos.x), (right.y, up2.y, -f.y, pos.y),
                (right.z, up2.z, -f.z, pos.z), (0, 0, 0, 1)))
    cam.matrix_world = m
    scn.camera = cam
    w = bpy.data.worlds.new("W")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.35, 0.37, 0.40, 1.0) if not dark else (0.10, 0.11, 0.12, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    for name, loc, energy, sz in (("KEY", (1.2, 1.4, 2.4), 260.0, 1.6), ("FILL", (-1.6, -0.6, 1.8), 90.0, 2.0),
                                  ("TOP", (0.2, 1.8, 0.6), 120.0, 1.2)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = sz
        lo = bpy.data.objects.new(name, ld)
        scn.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0.0, 0.0, 0.0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
    from carkit import scene as SC
    SC.use_cycles(samples)
    scn.view_settings.view_transform = 'Standard'
    scn.render.resolution_x = scn.render.resolution_y = size
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'
    out = os.path.normpath(out or os.path.join(_HERE, "..", "renders", "wheel_%s_obl.png" % design))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)
    return out
