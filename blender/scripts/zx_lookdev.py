"""A white-studio lookdev for the Zeekr 7X, to compare lit renders with the
Autohome studio photographs through the same solved cameras.

    import zx_lookdev as LD
    LD.setup()                        # world, floor, softboxes, Cycles
    LD.compare("f34_left", "v01")     # photo | render, one image
"""
import os

import bpy
import numpy as np

import zx_ref_match as RM
from carkit.qa import refmatch as R

OUT = R.OUT_DIR
CROPS = {   # photo crop (l, t, r, b) shown in a comparison
    "side_left": (330, 1050, 3600, 2330),
    "front": (900, 820, 2940, 2330),
    "f34_left": (300, 850, 3600, 2500),
    "f34_right": (300, 850, 3600, 2500),
    "r34_left": (300, 850, 3600, 2500),
    "r34_right": (300, 850, 3600, 2500),
}


def _plane(name, size=1.0):
    """A unit-ish plane object linked to the scene (no operators: they need a context)."""
    me = bpy.data.meshes.new(name)
    h = 0.5 * size
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _mat_floor():
    m = bpy.data.materials.get("M_LD_Floor") or bpy.data.materials.new("M_LD_Floor")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.78, 0.80, 0.82, 1.0)
    b.inputs["Roughness"].default_value = 0.18
    # the photographs' floor is a bright white: the car's lower body reflects it
    for key, val in (("Emission Color", (0.82, 0.84, 0.87, 1.0)), ("Emission Strength", 0.55)):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def _softbox(name, loc, size, power, aim):
    from mathutils import Vector
    ob = bpy.data.objects.get(name)
    if ob is None:
        ld = bpy.data.lights.new(name, 'AREA')
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
    ob.data.shape = 'RECTANGLE'
    ob.data.size, ob.data.size_y = size
    ob.data.energy = power
    ob.location = loc
    d = Vector(aim) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def setup(exposure=0.0):
    scn = bpy.context.scene
    w = scn.world or bpy.data.worlds.new("W_LD")
    scn.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new('ShaderNodeBackground')
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg.inputs["Color"].default_value = (0.90, 0.92, 0.95, 1.0)
    bg.inputs["Strength"].default_value = 0.12
    nt.links.new(bg.outputs[0], out.inputs[0])
    if not bpy.data.objects.get("LD_Floor"):
        fl = _plane("LD_Floor", 80.0)
        fl.data.materials.append(_mat_floor())
    _softbox("LD_Top", (0.0, 0.0, 5.5), (7.0, 5.0), 2200.0, (0, 0, 0.8))
    _softbox("LD_Key", (8.0, 6.0, 3.0), (6.0, 3.0), 1500.0, (0, 0, 0.9))
    _softbox("LD_Fill", (-8.0, -6.0, 3.0), (6.0, 3.0), 900.0, (0, 0, 0.9))
    try:
        scn.render.engine = 'CYCLES'
    except TypeError:
        pass
    scn.cycles.samples = 64
    scn.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                for d in prefs.devices:
                    d.use = d.type != 'CPU'
                scn.cycles.device = 'GPU'
                break
            except Exception:
                continue
    except Exception:
        pass
    scn.view_settings.view_transform = 'Khronos PBR Neutral'
    scn.view_settings.exposure = exposure
    scn.render.film_transparent = False


def _wall(cam_xy):
    """A bright cyc wall opposite the camera (the photographs' white studio); the
    camera's side stays dark, as it is in the photographs, so black parts read black."""
    import math
    from mathutils import Vector
    ob = bpy.data.objects.get("LD_Wall")
    if ob is None:
        ob = _plane("LD_Wall", 1.0)
        m = bpy.data.materials.get("M_LD_Wall") or bpy.data.materials.new("M_LD_Wall")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission')
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em.inputs["Color"].default_value = (0.92, 0.94, 0.97, 1.0)
        em.inputs["Strength"].default_value = 1.5
        nt.links.new(em.outputs[0], out.inputs[0])
        ob.data.materials.append(m)
    ob.scale = (30.0, 12.0, 1.0)
    d = Vector((cam_xy[0], cam_xy[1], 0.0))
    d.normalize()
    ob.location = (-d.x * 14.0, -d.y * 14.0, 5.0)
    # face the car: the plane's +Z towards the origin
    ob.rotation_euler = (math.radians(90.0), 0.0, math.atan2(d.y, d.x) - math.radians(90.0) + math.pi)
    return ob


def shot(name, tag, res=(1280, 960), samples=64):
    scn = bpy.context.scene
    ref, (w, h), *_ = RM.CAMERAS[name]
    cam = R.camera(name)
    _wall((cam.location.x, cam.location.y))
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.cycles.samples = samples
    scn.render.image_settings.file_format = 'PNG'
    path = os.path.join(OUT, "ld_%s_%s.png" % (name, tag))
    scn.render.filepath = path
    hidden = []
    for o in bpy.data.objects:
        if o.name.startswith("ZX_Shell") or o.name in ("ZX_Underbody",):
            pass
    bpy.ops.render.render(write_still=True)
    return path


def _clay_material(rgb=(0.50, 0.52, 0.56), rough=0.45):
    m = bpy.data.materials.get("M_LD_Clay") or bpy.data.materials.new("M_LD_Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = rgb + (1.0,)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0
    return m


def _id_material():
    """Flat emission in each object's own viewport colour (set by color_ids)."""
    m = bpy.data.materials.get("M_LD_Ids")
    if m is None:
        m = bpy.data.materials.new("M_LD_Ids")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        em = nt.nodes.new('ShaderNodeEmission')
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(oi.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs[0])
    return m


def color_ids(objs=None):
    """Give each object a well separated hue (golden-ratio steps over the sorted names)."""
    import colorsys
    objs = sorted(objs or [o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
    for i, o in enumerate(objs):
        h = (i * 0.61803398875) % 1.0
        sat = 0.85 if i % 2 else 0.55
        r, g, b = colorsys.hsv_to_rgb(h, sat, 0.95 if (i // 2) % 2 else 0.7)
        o.color = (r, g, b, 1.0)


def clay(name, tag, res=(1280, 960), samples=32, rgb=(0.50, 0.52, 0.56), rough=0.45):
    """Every surface one matte grey: the form alone (normals, seams, tears show)."""
    vl = bpy.context.view_layer
    vl.material_override = _clay_material(rgb, rough)
    try:
        return shot(name, "clay_" + tag, res, samples)
    finally:
        vl.material_override = None


def view(loc, aim, lens, tag, res=(1280, 960), samples=32, mode="clay", clip=0.05, only=None, colors=None, skip=()):
    """A free camera (metres, model coordinates) looking at `aim`. mode: "clay" (one
    matte grey), "ids" (a flat colour per object) or None (the scene's materials)."""
    from mathutils import Vector
    scn = bpy.context.scene
    cd = bpy.data.cameras.get("CAM_ld_free") or bpy.data.cameras.new("CAM_ld_free")
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = clip
    cd.clip_end = 400.0
    cam = bpy.data.objects.get("CAM_ld_free")
    if cam is None:
        cam = bpy.data.objects.new("CAM_ld_free", cd)
        scn.collection.objects.link(cam)
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    _wall((cam.location.x, cam.location.y))
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.cycles.samples = samples
    scn.render.image_settings.file_format = 'PNG'
    path = os.path.join(OUT, "ld_free_%s.png" % tag)
    scn.render.filepath = path
    vl = bpy.context.view_layer
    if mode == "clay":
        vl.material_override = _clay_material()
    elif mode == "ids":
        color_ids()
        for pre, rgb in (colors or {}).items():
            for o in bpy.data.objects:
                if o.name.startswith(pre):
                    o.color = tuple(rgb) + (1.0,)
        vl.material_override = _id_material()
        old_vt = scn.view_settings.view_transform
        scn.view_settings.view_transform = 'Standard'
    hid = []
    if only:
        for o in bpy.data.objects:
            if o.type == 'MESH' and not o.name.startswith("LD_") and not o.name.startswith(tuple(only)) and not o.hide_render:
                o.hide_render = True
                hid.append(o)
    if skip:
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith(tuple(skip)) and not o.hide_render:
                o.hide_render = True
                hid.append(o)
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        vl.material_override = None
        if mode == "ids":
            scn.view_settings.view_transform = old_vt
        for o in hid:
            o.hide_render = False
    return path


def compare(name, tag, res=(1280, 960), samples=64):
    path = shot(name, tag, res, samples)
    ren = R.load(path)[..., :3]
    ph = R.load(RM.CAMERAS[name][0])[..., :3]
    l, t, r, b = CROPS.get(name, (0, 0, 3840, 2880))
    sx = res[0] / 3840.0
    ph_c = ph[t:b, l:r]
    ren_c = ren[int(t * sx):int(b * sx), int(l * sx):int(r * sx)]
    # photo down to the render's scale
    k = max(1, int(round(1.0 / sx)))
    ph_c = ph_c[::k, ::k]
    h = min(ph_c.shape[0], ren_c.shape[0])
    w = min(ph_c.shape[1], ren_c.shape[1])
    out = np.concatenate([ph_c[:h, :w], ren_c[:h, :w]], axis=1)
    cmp_path = os.path.join(OUT, "cmp_%s_%s.png" % (name, tag))
    R.save(np.concatenate([out, np.ones(out.shape[:2] + (1,), np.float32)], axis=2), cmp_path)
    return cmp_path


# ------------------------------------------------------------------ the cabin
def cabin_view(loc, aim, lens, tag, res=(1500, 1125), samples=48, mode="clay",
               only=("int_", "screen_"), exposure=0.0, strength=1.0, skip=()):
    """A clay (or lit, mode=None) render from inside the cabin under a uniform soft sky:
    forms read as in an ambient-occlusion render. The lookdev studio is hidden."""
    from mathutils import Vector
    scn = bpy.context.scene
    w = scn.world
    old = None
    if w is not None and w.use_nodes:
        bg = next((n for n in w.node_tree.nodes if n.type == 'BACKGROUND'), None)
        if bg is not None:
            old = (tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value)
            bg.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1.0)
            bg.inputs["Strength"].default_value = strength
    hid = []
    for o in bpy.data.objects:
        if o.name.startswith("LD_") and not o.hide_render:
            o.hide_render = True
            hid.append(o)
    try:
        return view(loc, aim, lens, tag, res=res, samples=samples, mode=mode, only=only, skip=skip)
    finally:
        for o in hid:
            o.hide_render = False
        if old is not None:
            bg.inputs["Color"].default_value = old[0]
            bg.inputs["Strength"].default_value = old[1]
