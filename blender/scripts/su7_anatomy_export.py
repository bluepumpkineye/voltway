"""Headless entry: build the SU7's anatomy and write the web GLB (and optionally a .blend to look at).

    blender -b --factory-startup --python blender/scripts/su7_anatomy_export.py -- [--out PATH] [--blend PATH]

Default output is public/models/su7-ultra-xray.glb. Run from anywhere: the repo is found from __file__.
"""
import importlib
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
if _HERE not in sys.path:
    sys.path.append(_HERE)


def _arg(name, default=None):
    a = sys.argv
    if "--" in a:
        a = a[a.index("--") + 1:]
        if name in a and a.index(name) + 1 < len(a):
            return a[a.index(name) + 1]
    return default


def main():
    import bpy
    import su7_anatomy
    import carkit.anatomy.build as B
    importlib.reload(B)
    t0 = time.time()
    for o in list(bpy.data.objects):          # the factory scene's cube, light and camera would be in every card render
        bpy.data.objects.remove(o, do_unlink=True)
    B.build(su7_anatomy.spec())
    print("built in %.1fs" % (time.time() - t0))
    out = _arg("--out", os.path.join(_REPO, "public", "models", "su7-ultra-xray.glb"))
    if "--ao" in sys.argv:
        from carkit.anatomy import ao
        importlib.reload(ao)
        only = _arg("--ao-only")
        ao.run(rays=int(_arg("--ao-rays", "24")), only=only.split(",") if only else None)
    B.export_glb(out)
    if "--cards" in sys.argv:
        # the stills for the part cards (blender/renders/xray/<id>.png); then `node scripts/xray-tools/render-cards.mjs blender/renders/xray public/xray/su7-ultra`
        import su7_anatomy_renders as R
        importlib.reload(R)
        only = _arg("--only")
        print("cards:", R.render_all(only=only.split(",") if only else None))
    blend = _arg("--blend")
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True)
    print("done in %.1fs" % (time.time() - t0))


main()
