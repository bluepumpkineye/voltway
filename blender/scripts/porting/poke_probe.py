"""Which cabin vertices stand outside the exterior's skin? usage: blender -b --python poke_probe.py -- g9l|z9"""
import sys, traceback, collections
sys.path.append(__import__("os").path.normpath(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..")))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
CAR = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "g9l"
try:
    b = __import__("build_" + CAR)
    b.main(reset=True, scene=True)
    SH = __import__(CAR + "_interior_shell")
    SH.main(lights=False)
    P = CAR.upper()
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for cn in (P + "_Body", P + "_Details"):
        for ob in bpy.data.collections[cn].objects:
            if ob.type != 'MESH':
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
    out = collections.defaultdict(list)
    for ob in bpy.data.collections[P + "_Interior"].objects:
        if ob.type != 'MESH':
            continue
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(ob.matrix_world)
        for v in me.vertices:
            p = v.co
            if abs(p.y) < 0.45:
                continue
            # from the centreline straight out to the vertex's height: the first exterior surface it meets is the skin there;
            # a vertex beyond it (|y| larger) is outside the body. (A ray from the vertex outward grazes a tapering tail and
            # reports escapes that are not; no hit at all = a window or an arch, left alone.)
            d = Vector((0.0, 1.0 if p.y > 0 else -1.0, 0.0))
            hit = tree.ray_cast(Vector((p.x, 0.0, p.z)), d, 3.0)
            if hit[0] is not None and abs(p.y) > abs(hit[0].y) + 0.002:
                out[ob.name].append((round(p.x, 2), round(p.y, 2), round(p.z, 2)))
        bpy.data.meshes.remove(me)
    for n, pts in sorted(out.items(), key=lambda kv: -len(kv[1])):
        xs = [p[0] for p in pts]; ys = [abs(p[1]) for p in pts]; zs = [p[2] for p in pts]
        print("POKE %-34s %5d verts  x %.2f..%.2f  |y| %.2f..%.2f  z %.2f..%.2f" % (n, len(pts), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print("POKE done")
except Exception:
    traceback.print_exc()
    raise
