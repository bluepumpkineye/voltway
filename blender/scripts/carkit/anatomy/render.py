"""Stills of the anatomy's parts for the web card of each part: a transparent background, soft studio light, EEVEE.

    from carkit.anatomy import render as R
    R.part("pack", ["XR_Battery"], OUT + "/pack.png", offsets=R.layers(...), view=(1, -1, 0.8))

A part's nodes (and everything under them) are shown, the rest hidden; `offsets` moves nodes for the shot (the pack's layers
apart, the rotor out of its stator) and puts them back; the camera frames what is shown. The film is transparent, so the card
shows the picture over its own surface. Everything the shot changed (engine, camera, visibility, positions) is restored.
"""
import math
import os

import bpy
from mathutils import Vector

COL = "XR_ANATOMY"


def _subtree(ob):
    out = [ob]
    for c in ob.children:
        out += _subtree(c)
    return out


def _bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(min(a, b) for a, b in zip(lo, w))
            hi = Vector(max(a, b) for a, b in zip(hi, w))
    return lo, hi


def _rig(scene, centre, size):
    """A studio of three area lights and a pale gradient world, scaled to the thing in the shot."""
    for n in [o.name for o in bpy.data.objects if o.name.startswith("XRR_")]:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    col = bpy.data.collections.get("XR_RENDER") or bpy.data.collections.new("XR_RENDER")
    if col.name not in [c.name for c in scene.collection.children]:
        scene.collection.children.link(col)

    def area(name, loc, power, w, colour=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy = power
        d.size = w
        d.color = colour
        o = bpy.data.objects.new(name, d)
        col.objects.link(o)
        o.location = centre + Vector(loc) * size
        direction = centre - o.location
        o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        return o
    area("XRR_key", (1.2, -1.4, 1.5), 420 * size * size, size * 1.6)
    area("XRR_fill", (-1.6, -0.8, 0.5), 120 * size * size, size * 2.2, (0.85, 0.92, 1.0))
    area("XRR_rim", (-0.4, 1.8, 1.0), 300 * size * size, size * 1.2, (1.0, 0.95, 0.9))
    w = bpy.data.worlds.get("XRR_world") or bpy.data.worlds.new("XRR_world")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.86, 0.9, 0.97, 1)
    bg.inputs['Strength'].default_value = 0.38
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w


def part(name, nodes, path, offsets=None, view=(1.0, -1.0, 0.75), res=(720, 480), focal=62, pad=1.18, samples=40):
    """Render one part. `nodes` are object names; `offsets` maps an object name to a Blender-axes offset for the shot."""
    scene = bpy.context.scene
    col = bpy.data.collections[COL]
    all_xr = list(col.objects)
    was_hidden = {o.name: (o.hide_viewport, o.hide_render) for o in all_xr}
    was_loc = {}
    shown = []
    for n in nodes:
        shown += _subtree(bpy.data.objects[n])
    shown_names = {o.name for o in shown}
    for o in all_xr:
        vis = o.name in shown_names
        o.hide_viewport = not vis
        o.hide_render = not vis
    for n, off in (offsets or {}).items():
        o = bpy.data.objects[n]
        was_loc[n] = o.location.copy()
        o.location = o.location + Vector(off)
    bpy.context.view_layer.update()
    lo, hi = _bbox([o for o in shown if o.type == 'MESH'])
    centre = (lo + hi) / 2
    diag = (hi - lo).length
    cam_data = bpy.data.cameras.new("XRCAM")
    cam_data.lens = focal
    cam = bpy.data.objects.new("XRCAM", cam_data)
    scene.collection.objects.link(cam)
    # distance so the diagonal fits the narrower side with padding
    fov = 2 * math.atan((cam_data.sensor_width / 2) / focal)
    dist = (diag * 0.5 * pad) / math.tan(fov / 2) * 1.05
    d = Vector(view).normalized()
    cam.location = centre + d * dist
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    keep = dict(
        engine=scene.render.engine, camera=scene.camera, world=scene.world, res=(scene.render.resolution_x, scene.render.resolution_y),
        pct=scene.render.resolution_percentage, alpha=scene.render.film_transparent, path=scene.render.filepath,
        fmt=scene.render.image_settings.file_format, mode=scene.render.image_settings.color_mode,
        view=scene.view_settings.view_transform,
    )
    try:
        _rig(scene, centre, max(diag, 0.4))
        scene.camera = cam
        scene.render.engine = 'BLENDER_EEVEE'
        try:
            scene.eevee.taa_render_samples = samples
        except Exception:
            pass
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        try:
            scene.view_settings.view_transform = 'Khronos PBR Neutral'
        except Exception:
            pass
        os.makedirs(os.path.dirname(path), exist_ok=True)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        scene.render.engine = keep["engine"]
        scene.camera = keep["camera"]
        scene.world = keep["world"]
        scene.render.resolution_x, scene.render.resolution_y = keep["res"]
        scene.render.resolution_percentage = keep["pct"]
        scene.render.film_transparent = keep["alpha"]
        scene.render.filepath = keep["path"]
        scene.render.image_settings.file_format = keep["fmt"]
        scene.render.image_settings.color_mode = keep["mode"]
        scene.view_settings.view_transform = keep["view"]
        for n, loc in was_loc.items():
            bpy.data.objects[n].location = loc
        for o in all_xr:
            o.hide_viewport, o.hide_render = was_hidden[o.name]
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cam_data)
        for n in [o.name for o in bpy.data.objects if o.name.startswith("XRR_")]:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    print("rendered", name, path)
    return path
