"""One entry point for the 2026 XPeng Mona L05 (岚图追光S, Autohome Series 8534) build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_mona; build_mona.main()

Modules in build order:
    mona_surface     profile curves of the coupe-SUV flank loft
    mona_nose        nose and tail caps (WrapCap / TaperedWrapCap) and CarBody
    mona_panels      panel layout, window lines, panoramic roof, openings
    mona_front       fascia with lower aero fangs, winged DRLs, Kunpeng emblem, twin projectors, LiDAR
    mona_rear        tailgate, smoked VOYAH taillight, twin-pod aero spoiler, diffuser, badges
    mona_side        door-mounted flag mirrors, flush pocket handles, arch cladding, fender gill
    mona_wheels      21-inch Feichi & Starlight Obsidian wheels over forward-mounted amber calipers
    mona_materials   Rosy Mist Pink hero finish & Passion S material library
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("mona_cam", "mona_ref_match", "mona_surface", "mona_nose", "mona_panels",
           "mona_front", "mona_rear", "mona_side", "mona_wheels", "mona_materials", "scene_setup")
COLLECTIONS = ("MONA_Body", "MONA_Details", "MONA_Wheels")
PARTS = ("mona_front", "mona_rear", "mona_side")


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
    import mona_surface as S
    import mona_panels as P
    import mona_materials as MT

    body = B.fresh_collection("MONA_Body")
    dcol = B.fresh_collection("MONA_Details")
    wcol = B.fresh_collection("MONA_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building mona_panels"):
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
            import mona_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building mona_wheels"):
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


def parts_only(names=PARTS):
    for m in tuple(names) + ("mona_materials",):
        sys.modules.pop(m, None)
    import mona_materials as MT
    from carkit import build as B
    from carkit.jev.triage import guard
    dcol = B.fresh_collection("MONA_Details")
    lib = MT.build_library()
    made = []
    for m in names:
        with guard("rebuilding " + m):
            made += __import__(m).build_all(dcol, lib)
    return made


def fingerprint():
    from carkit.qa import checks
    import mona_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=128, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
