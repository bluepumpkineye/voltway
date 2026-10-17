"""Build a car once, list its exterior objects and probe its hood. usage: blender -b --python probe_car.py -- z9"""
import sys
sys.path.append(__import__("os").path.normpath(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..")))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
CAR = sys.argv[sys.argv.index("--") + 1]
P = CAR.upper()
import importlib
b = importlib.import_module("build_" + CAR)
b.main(reset=True, scene=False)
for cn in (P + "_Body", P + "_Details", P + "_Wheels"):
    col = bpy.data.collections.get(cn)
    if col is None:
        continue
    print("=== ", cn, len(col.objects))
    for o in sorted(col.objects, key=lambda o: o.name):
        if o.type != 'MESH':
            continue
        mods = ",".join(m.type for m in o.modifiers)
        mats = ",".join(m.name for m in o.data.materials if m)
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = [min(v[i] for v in bb) for i in range(3)]
        hi = [max(v[i] for v in bb) for i in range(3)]
        print("OBJ %-34s v%-6d [%s] {%s} x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
            o.name, len(o.data.vertices), mods, mats, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
name = P + "_Hood"
ob = bpy.data.objects[name]
dg = bpy.context.evaluated_depsgraph_get()
me = ob.evaluated_get(dg).to_mesh()
mw = ob.matrix_world
verts = [mw @ v.co for v in me.vertices]
print("HOOD verts", len(verts), "bbox x", min(v.x for v in verts), max(v.x for v in verts), "y", min(v.y for v in verts), max(v.y for v in verts))
tree = BVHTree.FromPolygons(verts, [list(p.vertices) for p in me.polygons])
x = min(v.x for v in verts)
xmax = max(v.x for v in verts)
while x <= xmax + 0.01:
    sel = [v for v in verts if abs(v.x - x) < 0.025]
    if sel:
        ymax = max(abs(v.y) for v in sel)
        def top(y):
            h = tree.ray_cast(Vector((x, y, 2.5)), Vector((0, 0, -1)), 3.0)[0]
            return None if h is None else round(h.z, 3)
        print("HOODX x %.2f half %.3f  zTop(0) %s zTop(.4) %s zTop(.7) %s" % (x, ymax, top(0.0), top(0.4), top(0.7)))
    x += 0.05
