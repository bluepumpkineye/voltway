"""Shared cabin tooling for the cars whose cabin is built from carkit.interior (the Denza Z9 and
the XPeng G9L): a fast compare render, the leak QA from the viewer's eyes, and the cabin bake and
export, each taking a small config dict instead of a copy per car.

A car's config (see z9_cabin.CFG):

    slug        'denza-z9'
    interior    module name of the cabin ('z9_interior_shell': main(lights, parts))
    collection  the cabin's collection ('Z9_Interior')
    node        the glTF root node's name ('DenzaZ9_Cabin')
    exterior    the build's collections (leak QA treats their meshes as painted exterior)
    blackout    the exterior's black underlay objects (hidden while the cabin is lit, so daylight
                comes in through the glass)
    hdri        dict(path, strength, rotation, clamp) of the world the cabin stands in
    probe_at    where the reflection probe is shot from
    skip_leak   name fragments the leak QA ignores
    protected   cabin nodes that stay separate in the glTF (merge_for_export)
    cluster     callable() -> the cluster's resting image path (or None)
    join_cards  callable() joining each door card's parts into one node on its hinge (optional: a car whose
                doors open)
    set_open    callable(on) swinging every door and the tailgate open (True) or shut (False), cabin parts
                included (optional: the second, "open" bake needs it)

Run a script in a background Blender (never the user's open session, see docs/3d-pipeline.md):

    blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); \\
        import cabin_tools as CT, z9_cabin as C; CT.compare(C.CFG, 'tag')"
"""
import math
import os
import sys

import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
OUT = os.path.normpath(os.path.join(_HERE, "..", "renders", "cabincmp"))
WEB_EXPOSURE = 0.92          # the viewer's toneMappingExposure


# ------------------------------------------------------------ compare render
def camera_at(name, pos, aim, fov_h, res):
    cd = bpy.data.cameras.new("CAM_" + name)
    cd.sensor_fit = 'HORIZONTAL'
    cd.sensor_width = 36.0
    cd.lens = 18.0 / math.tan(math.radians(fov_h) / 2.0)
    cd.clip_start = 0.02
    cam = bpy.data.objects.new("CAM_" + name, cd)
    bpy.context.scene.collection.objects.link(cam)
    p, a = Vector(pos), Vector(aim)
    cam.location = p
    cam.rotation_euler = (a - p).to_track_quat('-Z', 'Y').to_euler()
    scn = bpy.context.scene
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    return cam


def compare(cfg, tag="cmp", parts=None, cams=None, samples=32, dump=None, world=1.1, fill=0.5):
    """Build the cabin alone (no exterior: seconds) and render each camera in `cams`
    ({name: dict(pos, aim, fov_h, res)}, default cfg['cameras']) with Cycles under a white world into
    blender/renders/cabincmp/<tag>_<name>.png. Prints the bounding boxes of the objects whose names
    contain one of `dump`."""
    import importlib
    from carkit import scene as SC
    bpy.ops.wm.read_homefile(use_empty=True)
    SH = importlib.import_module(cfg["interior"])
    SH.main(lights=True, parts=list(parts) if parts else None)
    col = bpy.data.collections[cfg["collection"]]
    rows = []
    for o in col.all_objects:
        if o.type != 'MESH' or not dump or not any(k in o.name.lower() for k in dump):
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = [min(v[i] for v in bb) for i in range(3)]
        hi = [max(v[i] for v in bb) for i in range(3)]
        rows.append("%-34s x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
                    % (o.name, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    print("\n".join(sorted(rows)))
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W_cmp")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = world
    for o in col.objects:
        if o.type == 'LIGHT':
            o.data.energy *= fill
    os.makedirs(OUT, exist_ok=True)
    out = []
    for name, c in (cams or cfg["cameras"]()).items():
        cam = camera_at(name, c["pos"], c["aim"], c["fov_h"], c["res"])
        SC.use_cycles(samples)
        scn.view_settings.view_transform = 'Standard'
        scn.render.image_settings.file_format = 'PNG'
        scn.render.filepath = os.path.join(OUT, "%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)
        out.append(scn.render.filepath)
        bpy.data.objects.remove(cam, do_unlink=True)
    print("compare:", out)
    return out


# ------------------------------------------------------------------ leak QA
def aim_point(eye, yaw, pitch):
    """A point 1 m from the eye: yaw 0 forward (+x), +90 left (+y); pitch up positive."""
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)))
    return tuple(Vector(eye) + d)


def leaks(cfg, eye, tag, yaws=(0, 45, 90, 135, 180, -135, -90, -45), pitches=(0, 45, -40),
          lens=16.0, res=(192, 108), top=25):
    """Rays from a seat's eye (16 mm lens = the viewer's 64 deg vertical field): any that reach
    painted exterior without first crossing glass is a gap in the cabin's trim. Needs the build and
    the cabin in one scene, BEFORE the parts are split for export."""
    from carkit.qa import leaks as LK
    specs = {}
    for yw in yaws:
        for pt in pitches:
            specs["%s_y%d_p%d" % (tag, yw, pt)] = (eye, aim_point(eye, yw, pt), lens)
    cams = LK.cameras(specs)
    rep = LK.find(cams, interior=cfg["collection"], exterior=cfg["exterior"], see_through=("Glass",),
                  skip=cfg["skip_leak"], res=res)
    LK.print_report(rep, top=top)
    W, H = rep["res"]
    worst = max(rep["per_camera"].values()) * 100.0 / (W * H)
    print("LEAK %s worst %.3f %%" % (tag, worst))
    return rep, worst


def all_leaks(cfg, **kw):
    out = {}
    for name, eye in cfg["eyes"].items():
        print("=====", name)
        out[name] = leaks(cfg, eye, name[:3], **kw)
    return out


# ------------------------------------------------------------ bake and export
def cabin_lighting(cfg):
    """The world, the cabin rig as a fill, the generated cluster on its display, and the blackout
    layer and lookdev floor hidden so daylight comes in through the glass. Wrap bakes in
    carkit.bake.thin_glass()."""
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    SC.hdri_world(**cfg["hdri"])
    col = bpy.data.collections.get(cfg["collection"])
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * cfg.get("rig_fill", 0.8)
    for nm, fn in cfg.get("displays", {}).items():
        ob = bpy.data.objects.get(nm)
        path = fn()
        if ob is not None and path and not ob.get("plain_material"):
            HC.apply(ob, path, 1.2)
    hidden = []
    for n in tuple(cfg["blackout"]) + (cfg["node_blackout"], "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def bake_cabin(cfg, samples=256, probe_samples=384, probe=True):
    """Vertex lighting on every cabin mesh + the reflection probe (probe=False keeps the file on
    disk, for a rebuild that touched only the cabin's geometry)."""
    import time
    from carkit import bake as BK
    col = bpy.data.collections[cfg["collection"]]
    hidden = cabin_lighting(cfg)
    for o in [o for o in col.objects if o.type == 'MESH' and not len(o.data.polygons)]:
        print("cabin: removed empty mesh", o.name)
        bpy.data.objects.remove(o, do_unlink=True)
    t = time.time()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col)
            print("  cabin bake: prepared %d meshes, %.0f s" % (len(objs), time.time() - t))
            stats = BK.vertex_lighting(objs, samples=samples,
                                       scale=BK.STORE_SCALE * cfg.get("gain", 1.0))
            print("  cabin bake: vertex light, %.0f s" % (time.time() - t))
            BK.smooth(objs)
            BK.to_generic(objs)
            if probe:
                lights = [o for o in col.objects if o.type == 'LIGHT' and o.visible_glossy]
                BK.probe_mix(cfg["probe_at"], os.path.join(MODELS, cfg["slug"] + "-cabin.hdr"), lights,
                             mix=cfg.get("probe_mix", 0.3), samples=probe_samples)
                print("  cabin bake: probe, %.0f s" % (time.time() - t))
    finally:
        for ob in hidden:
            ob.hide_render = False
    return stats


def bake_cabin_open(cfg, samples=256):
    """The same vertex lighting with every door and the tailgate open: the second set of light the viewer blends in
    as a part swings open (the cabin is lit by the doorways, the boot by the sky). Needs the exterior's parts split
    and hinged (the car's prepare_exterior) and cfg['join_cards'] / cfg['set_open']."""
    from carkit import bake as BK
    col = bpy.data.collections[cfg["collection"]]
    cfg["join_cards"]()
    cfg["set_open"](True)
    hidden = cabin_lighting(cfg)
    try:
        with BK.thin_glass():
            objs = BK.prepare(col, attr=BK.ATTR_OPEN)
            stats = BK.vertex_lighting(objs, samples=samples, attr=BK.ATTR_OPEN,
                                       scale=BK.STORE_SCALE * cfg.get("gain", 1.0))
            BK.smooth(objs, attr=BK.ATTR_OPEN)
            BK.to_generic(objs, BK.ATTR_OPEN, BK.EXPORT_ATTR_OPEN)
    finally:
        for ob in hidden:
            ob.hide_render = False
        cfg["set_open"](False)
    return stats


def export_outside(cfg):
    """The view out (JPEG, tone mapped as the viewer does) and its light (HDR)."""
    from carkit import bake as BK
    o = cfg["hdri"]
    view = BK.backdrop(o["path"], os.path.join(MODELS, cfg["slug"] + "-outside.jpg"),
                       rotation=o["rotation"], strength=o["strength"], exposure=WEB_EXPOSURE)
    light = BK.backdrop_light(o["path"], os.path.join(MODELS, cfg["slug"] + "-outside-light.hdr"),
                              rotation=o["rotation"], strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def clean_degenerate(objs, dist=1e-7, area=1e-12):
    import bmesh
    from carkit import export as _X
    n = 0
    for o in objs:
        if o.type != 'MESH':
            continue
        _X.bake_modifiers(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        before = len(bm.faces)
        bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
        bad = [f for f in bm.faces if f.calc_area() < area]
        if bad:
            bmesh.ops.delete(bm, geom=bad, context='FACES')
        n += before - len(bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    print("degenerate faces removed:", n)
    return n


def join_prefix(collection, prefix, name):
    """Every mesh of the collection whose name starts with `prefix` -> one object `name`."""
    from carkit import export as _X
    col = bpy.data.collections[collection]
    names = [o.name for o in col.objects if o.type == 'MESH' and o.name.startswith(prefix)
             and o.name != name]
    return _X.join(name, names) if names else None


def export_interior(cfg, draco=True):
    from carkit import build as B
    from carkit import export as _X
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections[cfg["collection"]]
    # the app draws the live HMI over screen_main: ship the plain screen
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if m.name.startswith("INT_")
        and m.name != "INT_Screen" and not m.name.startswith("INT_Display")))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    if cfg.get("join_cards"):
        cfg["join_cards"]()
    join_prefix(cfg["collection"], "int_headliner", "int_headliner")
    groups = [(cfg["node"], cfg["collection"])]
    merged = _X.merge_for_export(groups, cfg["protected"])
    clean_degenerate(merged)
    dest = os.path.join(MODELS, cfg["slug"] + "-interior.glb")
    return _X.export(dest, groups, cfg["node"], draco=draco, attributes=True)
