"""Cabin leak finder: which exterior surfaces can be seen from inside the car.

From a seat, every surface you see must be interior trim - or exterior seen
THROUGH glass (the hood through the windscreen, a mirror through the side
window). A painted panel seen directly means a gap in the trim: the inside of
a door, the roof between the headliner and the glass header, the shut face at
a B-pillar. In the web viewer those gaps show as bright paint slivers.

    rep = find(cameras, interior="SU7_Interior", exterior=("SU7_Body", ...),
               see_through=("Glass", "Greenhouse_Black", ...), res=(320, 180))
    print_report(rep)

Casts one ray per sample pixel from each camera (no render needed). A ray
that reaches an exterior object WITHOUT first crossing a see-through object is
a leak; results are grouped by object and 10 cm cell so each line is one gap
to close. Pair with a magenta render (every exterior material swapped for
flat magenta, glass hidden) to see them.
"""
from collections import defaultdict

import bpy
from mathutils import Vector


def cameras(specs, prefix="CAM_leak_"):
    """specs: {name: ((x, y, z) eye, (x, y, z) aim, lens_mm)} -> camera objects."""
    scn = bpy.context.scene
    out = []
    for name, (loc, aim, lens) in specs.items():
        cn = prefix + name
        cam = bpy.data.objects.get(cn) or bpy.data.objects.new(cn, bpy.data.cameras.new(cn))
        if cam.name not in scn.collection.objects:
            scn.collection.objects.link(cam)
        cam.data.lens = lens
        cam.data.sensor_width = 36.0
        cam.data.clip_start = 0.02
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(aim) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        out.append(cam)
    bpy.context.view_layer.update()
    return out


def _rays(cam, res):
    scn = bpy.context.scene
    tr, br, bl, tl = cam.data.view_frame(scene=scn)
    m3 = cam.matrix_world.to_3x3()
    o = cam.matrix_world.translation.copy()
    W, H = res
    for py in range(H):
        v = (py + 0.5) / H
        for px in range(W):
            u = (px + 0.5) / W
            p = tl.lerp(tr, u).lerp(bl.lerp(br, u), v)
            yield px, py, o, (m3 @ p).normalized()


def find(cameras, interior, exterior, see_through, skip=(), res=(320, 180), max_hops=12):
    scn = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    col_of = {}
    for cname in (interior,) + tuple(exterior):
        col = bpy.data.collections.get(cname)
        if col:
            for ob in col.all_objects:
                col_of[ob.name] = cname
    cells = defaultdict(lambda: [0, None])
    per_cam = {}
    for cam in cameras:
        n_leak = 0
        for px, py, o, d in _rays(cam, res):
            crossed = False
            p = o
            for _ in range(max_hops):
                ok, loc, nor, idx, ob, mw = scn.ray_cast(dg, p, d)
                if not ok:
                    break
                name = ob.name
                if any(s in name for s in skip) or not ob.visible_get():
                    p = loc + d * 0.0005
                    continue
                if any(s in name for s in see_through):
                    crossed = True
                    p = loc + d * 0.0005
                    continue
                if col_of.get(name) == interior:
                    break
                if col_of.get(name) in exterior and not crossed:
                    key = (name, tuple(round(c * 10.0) / 10.0 for c in loc))
                    cells[key][0] += 1
                    cells[key][1] = cam.name
                    n_leak += 1
                break
        per_cam[cam.name] = n_leak
    return {"cells": dict(cells), "per_camera": per_cam, "res": res}


def print_report(rep, top=30):
    W, H = rep["res"]
    for cam, n in rep["per_camera"].items():
        print("%-28s %6d leak px (%.2f%%)" % (cam, n, 100.0 * n / (W * H)))
    items = sorted(rep["cells"].items(), key=lambda kv: -kv[1][0])
    for (name, cell), (n, cam) in items[:top]:
        print("  %5d  %-28s at %s  (%s)" % (n, name, cell, cam))
