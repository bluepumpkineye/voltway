"""One entry point for the BYD Seal 07 EV (比亚迪 海豹07 EV, 2026/2027) build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_seal; build_seal.main()

Modules:
    seal_surface      profile curves of the flank loft (carkit LoftBody, 4995 x 1910 x 1495 mm)
    seal_nose         nose and tail caps (carkit WrapCap) and the CarBody
    seal_panels       panel layout, window lines, openings
    seal_front        Ocean X fascia, double-U hook headlamps, roof LiDAR pod, grille, BYD emblem
    seal_rear         tail fascia, Ocean water-drop through-type tail lamp + chrome bar, badges
    seal_side         mirrors, flush handles, fender camera blade, rising door crease, chrome DLO
    seal_wheels       18-inch 5-petal dual-tone aero blade alloy wheels (225/50 R18)
    seal_materials    Sky Purple (天空紫) and BYD Ocean factory finishes
"""
import os
import sys
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = (
    "seal_surface", "seal_nose", "seal_panels", "seal_front", "seal_rear", "seal_side",
    "seal_wheels", "seal_materials", "scene_setup",
)
COLLECTIONS = ("Seal_Body", "Seal_Details", "Seal_Wheels")
PARTS = ("seal_front", "seal_rear", "seal_side")


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
    import seal_surface as S
    import seal_panels as P
    import seal_materials as MT

    body = B.fresh_collection("Seal_Body")
    dcol = B.fresh_collection("Seal_Details")
    wcol = B.fresh_collection("Seal_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()

    with guard("building seal_panels"):
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
            import seal_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building seal_wheels"):
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
    print("BYD Seal build complete: %d objects, %d tris (evaluated)" % (len(objs), tris))
    print("dims:", S.dims_report())
    return {"body": body, "wheels": wcol, "details": dcol, "lib": lib, "tris": tris}


if __name__ == "__main__":
    main()
