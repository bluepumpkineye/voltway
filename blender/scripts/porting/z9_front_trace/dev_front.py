"""Fast loop: z9_built.blend (old front) -> remove the front end -> rebuild it with the current z9_front -> z9_front.blend.
blender -b <SP>/z9_full.blend --python dev_front.py"""
import os
import sys
import time
import traceback

import bpy

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SP = os.environ.get("Z9DEV") or os.path.join(REPO, "blender", "renders", "z9_dev")
os.makedirs(SP, exist_ok=True)

sys.path.append(os.path.join(REPO, "blender", "scripts"))

PREFIX = ("Z9_Fascia", "Z9_Apron", "Z9_Grille", "Z9_Headlamp", "Z9_Lower_DRL", "Z9_Chin_Lip", "Z9_Brow_Bar", "Z9_Front_",
          "Z9_Plate_Mount_Front", "Z9_Plate_Front", "Z9_Emblem_Front", "Z9_Hood_Ridge", "Z9_Lamp_", "Z9_Eyebrow", "Z9_Cavity",
          "Z9_Radiator", "Z9_Radar", "Z9_Module", "Z9_Pad", "Z9_Sensor_Disc", "Z9_Sensor_Ring", "Z9_Washer")
t = time.time()
for ob in list(bpy.data.objects):
    if ob.name.startswith(PREFIX):
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
print("removed old front %.1f s" % (time.time() - t))

for m in [m for m in sys.modules if m.startswith("z9_") or m == "carkit" or m.startswith("carkit.")]:
    sys.modules.pop(m, None)
try:
    import z9_materials as MT
    import z9_front as ZF
    from carkit import build as B
    lib = MT.build_library()
    col = bpy.data.collections["Z9_Details"]
    made = ZF.build_all(col, lib)
    B.ensure_uvs([col])
    from carkit import mesh as M
    tri = M.tri_count([o for o in made if o is not None])
    print("FRONT built: %d objects, %d tris, %.1f s" % (len(made), tri, time.time() - t))
    for o in made:
        print("  OBJ %-28s %6d" % (o.name, M.tri_count([o])))
except Exception:
    traceback.print_exc()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SP, "z9_front.blend"))
print("SAVED")
