"""One entry point for the XPeng G9L build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_g9l; build_g9l.main()

Modules:
    g9l_surface     profile curves of the flank loft (carkit LoftBody)
    g9l_nose        nose and tail caps (carkit WrapCap) and the CarBody
    g9l_panels      panel layout, window lines, openings
    g9l_front       fascia, Robot Face LED bar, vertical headlamps, lower grille, chin, emblem
    g9l_rear        tailgate, Horizon tail light bar, spoiler, diffuser, lettering
    g9l_side        mirrors, flush handles, fender cameras, rocker blades, window trim
    g9l_wheels      20-inch Aero turbine wheels and corner placement table
    g9l_materials   XPeng Provence Purple and factory finishes
"""
import os
import sys
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = (
    "g9l_surface", "g9l_nose", "g9l_panels", "g9l_front", "g9l_rear", "g9l_side",
    "g9l_wheels", "g9l_materials", "scene_setup"
)
COLLECTIONS = ("G9L_Body", "G9L_Details", "G9L_Wheels")
PARTS = ("g9l_front", "g9l_rear", "g9l_side")


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
    import g9l_surface as S
    import g9l_panels as P
    import g9l_materials as MT

    body = B.fresh_collection("G9L_Body")
    dcol = B.fresh_collection("G9L_Details")
    wcol = B.fresh_collection("G9L_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()

    with guard("building g9l_panels"):
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
            import g9l_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building g9l_wheels"):
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
    print("XPeng G9L build complete: %d objects, %d tris (evaluated)" % (len(objs), tris))
    print("dims:", S.dims_report())
    return {"body": body, "wheels": wcol, "details": dcol, "lib": lib, "tris": tris}


if __name__ == "__main__":
    main()
