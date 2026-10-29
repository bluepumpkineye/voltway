"""One entry point for the 2026 Voyah Passion S (岚图追光S, Autohome Series 8534) build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_vps; build_vps.main()

Modules in build order:
    vps_surface     profile curves of the coupe-SUV flank loft
    vps_nose        nose and tail caps (WrapCap / TaperedWrapCap) and CarBody
    vps_panels      panel layout, window lines, panoramic roof, openings
    vps_front       fascia with lower aero fangs, winged DRLs, Kunpeng emblem, twin projectors, LiDAR
    vps_rear        tailgate, smoked VOYAH taillight, twin-pod aero spoiler, diffuser, badges
    vps_side        door-mounted flag mirrors, flush pocket handles, arch cladding, fender gill
    vps_wheels      21-inch Feichi & Starlight Obsidian wheels over forward-mounted amber calipers
    vps_materials   Rosy Mist Pink hero finish & Passion S material library
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("vps_cam", "vps_ref_match", "vps_surface", "vps_nose", "vps_panels",
           "vps_front", "vps_rear", "vps_side", "vps_wheels", "vps_materials", "scene_setup")
COLLECTIONS = ("VPS_Body", "VPS_Details", "VPS_Wheels")
PARTS = ("vps_front", "vps_rear", "vps_side")


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
    import vps_surface as S
    import vps_panels as P
    import vps_materials as MT

    body = B.fresh_collection("VPS_Body")
    dcol = B.fresh_collection("VPS_Details")
    wcol = B.fresh_collection("VPS_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building vps_panels"):
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
            import vps_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building vps_wheels"):
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
    for m in tuple(names) + ("vps_materials",):
        sys.modules.pop(m, None)
    import vps_materials as MT
    from carkit import build as B
    from carkit.jev.triage import guard
    dcol = B.fresh_collection("VPS_Details")
    lib = MT.build_library()
    made = []
    for m in names:
        with guard("rebuilding " + m):
            made += __import__(m).build_all(dcol, lib)
    return made


def fingerprint():
    from carkit.qa import checks
    import vps_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=128, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
