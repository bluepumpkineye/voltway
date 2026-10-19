"""One entry point for the Nio ES8 build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_es8; build_es8.main()
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("es8_surface", "es8_nose", "es8_panels", "es8_front", "es8_rear", "es8_side",
           "es8_wheels", "es8_materials", "scene_setup")
COLLECTIONS = ("ES8_Body", "ES8_Details", "ES8_Wheels")
PARTS = ("es8_front", "es8_rear", "es8_side")


def _reload():
    for m in MODULES:
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)


def main(reset=True, parts=PARTS, wheels=True, scene=True):
    if reset:
        bpy.ops.wm.read_homefile(use_empty=True)
    _reload()
    from carkit import build as B
    from carkit import mesh as M
    import es8_surface as S
    import es8_panels as P
    import es8_materials as MT

    body = B.fresh_collection("ES8_Body")
    dcol = B.fresh_collection("ES8_Details")
    wcol = B.fresh_collection("ES8_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building es8_panels"):
        P.build_all(body, lib)
    for name in parts:
        try:
            mod = __import__(name)
        except ImportError:
            continue
        with guard("building " + name):
            mod.build_all(dcol, lib)
    shell = bpy.data.objects.get("ES8_Shell_Shadow")
    fascia = bpy.data.objects.get("ES8_Fascia")
    if shell is not None and fascia is not None:
        P.clear_shell(shell, [fascia], gap=0.020)
    if wheels:
        import es8_wheels as W
        with guard("building es8_wheels"):
            W.build_all(wcol, S, lib)
    if scene:
        import scene_setup as SC
        SC.main()

    B.ensure_uvs([body, dcol, wcol])
    objs = [o for c in (body, dcol, wcol) for o in c.objects]
    tris = M.tri_count(objs)
    print("objects: %d   tris (evaluated): %d" % (len(objs), tris))
    print("dims:", S.dims_report())
    return {"body": body, "wheels": wcol, "details": dcol, "lib": lib, "tris": tris}


def fingerprint():
    from carkit.qa import checks
    import es8_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=160, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
