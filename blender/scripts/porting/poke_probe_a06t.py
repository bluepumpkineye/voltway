"""Which A06T cabin vertices stand outside the exterior's skin?

    blender -b --factory-startup --python blender/scripts/porting/poke_probe_a06t.py

Builds the body (no wheels) and the cabin in one scene and lists, per cabin object, the vertices that lie outside the body:
  SIDE  from the centreline out along +-y at the vertex's height, the first exterior surface it meets is the skin there; a
        vertex with larger |y| is outside (no hit at all = a window or an arch: left alone), and
  TAIL  from far behind along +x at the vertex's (y, z), the first exterior surface is the tail's skin; a vertex behind it
        (x less than the hit's) is outside. The side test cannot see the tail: nothing is hit at an x beyond the car's end.
A cabin piece that stands outside the paint shows only when an opening is open (the cabin is stencilled to the glass while
the car is shut, clearGlass.ts), so a shut-car check never sees it: run this after any change to the exterior's length.
Found on 2026-10-28: the C-pillar trim (x to -2.44) and the parcel shelf (to -2.46) stood 6-12 cm out of the 4-6 cm shorter tail
as two grey plates, visible in the viewer with any door open.
"""
import sys, os, collections, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.normpath(os.path.join(HERE, "..")))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

try:
    import build_a06t
    build_a06t.main(scene=False, parts=("a06t_rear", "a06t_side", "a06t_front"), wheels=False)
    import a06t_interior as I
    I.main(lights=False)
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for cn in ("A06T_Body", "A06T_Details"):
        for ob in bpy.data.collections[cn].objects:
            if ob.type != 'MESH' or any(k in ob.name for k in ("Shadow", "Liner", "Underbody", "Glass_RearBack")):
                continue
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            me.transform(ob.matrix_world)
            base = len(verts)
            verts += [v.co.copy() for v in me.vertices]
            me.calc_loop_triangles()
            polys += [[base + i for i in t.vertices] for t in me.loop_triangles]
            bpy.data.meshes.remove(me)
    tree = BVHTree.FromPolygons(verts, polys)
    print("exterior tris", len(polys))
    side, tail = collections.defaultdict(list), collections.defaultdict(list)
    for ob in bpy.data.collections["A06T_Interior"].objects:
        if ob.type != 'MESH':
            continue
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(ob.matrix_world)
        for v in me.vertices:
            p = v.co
            if abs(p.y) > 0.45 and p.x < 1.0:
                d = Vector((0.0, 1.0 if p.y > 0 else -1.0, 0.0))
                hit = tree.ray_cast(Vector((p.x, 0.0, p.z)), d, 3.0)
                if hit[0] is not None and abs(p.y) > abs(hit[0].y) + 0.002:
                    side[ob.name].append((round(p.x, 2), round(p.y, 2), round(p.z, 2)))
            if p.x < -2.0 and p.z > 0.5:
                hit = tree.ray_cast(Vector((-3.5, p.y, p.z)), Vector((1.0, 0.0, 0.0)), 3.0)
                if hit[0] is not None and p.x < hit[0].x - 0.002:
                    tail[ob.name].append((round(p.x, 3), round(p.y, 2), round(p.z, 2), round(hit[0].x - p.x, 3)))
        bpy.data.meshes.remove(me)
    for tag, d in (("SIDE", side), ("TAIL", tail)):
        for n, pts in sorted(d.items(), key=lambda kv: -len(kv[1])):
            xs = [p[0] for p in pts]; ys = [abs(p[1]) for p in pts]; zs = [p[2] for p in pts]
            extra = ("  worst %.3f m behind the skin" % max(p[3] for p in pts)) if tag == "TAIL" else ""
            print("POKE %s %-30s %5d verts  x %.2f..%.2f  |y| %.2f..%.2f  z %.2f..%.2f%s" % (
                tag, n, len(pts), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), extra))
    print("POKE done")
except Exception:
    traceback.print_exc()
    raise
