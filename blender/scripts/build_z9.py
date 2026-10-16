"""One entry point for the Denza Z9 build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_z9; build_z9.main()

Modules:
    z9_surface      profile curves of the flank loft (carkit LoftBody)
    z9_nose         nose and tail caps (carkit WrapCap) and the CarBody
    z9_panels       panel layout, window lines, openings
    z9_front        Corona split headlamps, lower DRL blade, side curtains, grille, emblem
    z9_rear         tail fascia, Time Hourglass two-piece LED tail lamps, bumper apron, diffuser
    z9_side         mirrors, flush handles, fender camera blade, Z-line door trim, chrome DLO
    z9_wheels       21-inch 14-spoke luxury machined alloy wheels and staggered corner placement
    z9_materials    Denza Night Purple (暗夜紫) and factory finishes
"""
import os
import sys
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = (
    "z9_surface", "z9_nose", "z9_panels", "z9_front", "z9_rear", "z9_side",
    "z9_wheels", "z9_materials", "scene_setup",
)
COLLECTIONS = ("Z9_Body", "Z9_Details", "Z9_Wheels")
PARTS = ("z9_front", "z9_rear", "z9_side")


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
    import z9_surface as S
    import z9_panels as P
    import z9_materials as MT

    body = B.fresh_collection("Z9_Body")
    dcol = B.fresh_collection("Z9_Details")
    wcol = B.fresh_collection("Z9_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()

    with guard("building z9_panels"):
        P.build_all(body, lib)

    for name in parts:
        try:
            mod = __import__(name)
        except ImportError:
            continue
        with guard("building " + name):
            mod.build_all(dcol, lib)

    if wheels:
        try:
            import z9_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building z9_wheels"):
                W.build_all(wcol, S, lib)

    if scene:
        try:
            import scene_setup as SC
            SC.main()
        except Exception as e:
            print("Scene setup notice:", e)

    B.ensure_uvs([body, dcol, wcol])
    objs = [o for c in (body, dcol, wcol) for o in c.objects]
    tris = M.tri_count(objs)
    print("Denza Z9 build complete: %d objects, %d tris (evaluated)" % (len(objs), tris))
    print("dims:", S.dims_report())
    return {"body": body, "wheels": wcol, "details": dcol, "lib": lib, "tris": tris}


if __name__ == "__main__":
    main()
