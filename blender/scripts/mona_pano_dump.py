"""Dump the Mona cabin's object boxes (model coordinates: x forward, y left, z up) for the pano comparison (Phase 0).

    blender -b --factory-startup --python blender/scripts/mona_pano_dump.py -- <out.json>

Builds only the interior (mona_interior.main, ~30 s) in an empty file, as export_mona.hmi_cabin does, and writes
{name: {min, max, tris, mats}} for every mesh in MONA_Interior plus the screen's four glass corners.
"""
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)


def main(out):
    bpy.ops.wm.read_homefile(use_empty=True)
    import mona_interior as RI
    RI.main(lights=False)
    dg = bpy.context.evaluated_depsgraph_get()
    res = {}
    for o in bpy.data.collections[RI.COLLECTION].all_objects:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        if not vs:
            ev.to_mesh_clear()
            continue
        res[o.name] = {
            "min": [round(min(v[i] for v in vs), 4) for i in range(3)],
            "max": [round(max(v[i] for v in vs), 4) for i in range(3)],
            "verts": len(vs),
            "mats": [m.name for m in o.data.materials if m],
        }
        if o.name in ("screen_main",):
            # glass corners: the 4 extreme vertices along the object's own X (width) and Z/Y (height)
            lv = [v.co for v in me.vertices]
            xs = sorted(lv, key=lambda c: c.x)
            res[o.name]["local_bbox"] = [[round(min(c[i] for c in lv), 4) for i in range(3)],
                                         [round(max(c[i] for c in lv), 4) for i in range(3)]]
            res[o.name]["matrix_world"] = [[round(x, 5) for x in row] for row in mw]
        ev.to_mesh_clear()
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print("dumped %d meshes -> %s" % (len(res), out))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv[0] if argv else os.path.join(HERE, "mona_pano_dump.json"))
