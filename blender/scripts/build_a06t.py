"""One entry point for the Avatr 06T build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_a06t; build_a06t.main()

The 06T is carkit's sixth car, built on the Luxeed RX's structure. Its
modules hold only its data, in build order:

    a06t_surface     profile curves of the shooting-brake flank loft
    a06t_nose        nose and tail caps (carkit WrapCap) and the CarBody
    a06t_panels      panel layout, window lines, openings
    a06t_front       fascia, F-type headlamps, grille, chin, badge, lidar
    a06t_rear        tailgate, star-ring lamps, roof spoiler, diffuser, badges
    a06t_side        e-mirrors, handles, rocker, roof rails, fender blade
    a06t_wheels      the 5-twin-spoke wheel and the corner table
    a06t_materials   the 06T's finishes on carkit's material library
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("a06t_surface", "a06t_nose", "a06t_panels", "a06t_front", "a06t_rear",
           "a06t_side", "a06t_wheels", "a06t_materials", "scene_setup")
COLLECTIONS = ("A06T_Body", "A06T_Details", "A06T_Wheels")
PARTS = ("a06t_front", "a06t_rear", "a06t_side")


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
    import a06t_surface as S
    import a06t_panels as P
    import a06t_materials as MT

    body = B.fresh_collection("A06T_Body")
    dcol = B.fresh_collection("A06T_Details")
    wcol = B.fresh_collection("A06T_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building a06t_panels"):
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
            import a06t_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building a06t_wheels"):
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
    """Rebuild only the detail modules `names` on the existing body."""
    for m in tuple(names) + ("a06t_materials",):
        sys.modules.pop(m, None)
    import a06t_materials as MT
    from carkit import build as B
    dcol = B.fresh_collection("A06T_Details")
    from carkit.jev.triage import guard
    lib = MT.build_library()
    made = []
    for m in names:
        with guard("rebuilding " + m):
            made += __import__(m).build_all(dcol, lib)
    return made


def wheels():
    """Rebuild the four wheels only."""
    for m in ("a06t_wheels", "a06t_materials"):
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m.startswith("carkit.parts")]:
        sys.modules.pop(name, None)
    import a06t_wheels as W
    import a06t_surface as S
    import a06t_materials as MT
    from carkit import build as B
    from carkit.jev.triage import guard
    wcol = B.fresh_collection("A06T_Wheels")
    with guard("rebuilding a06t_wheels"):
        return W.build_all(wcol, S, MT.build_library())


def fingerprint():
    from carkit.qa import checks
    import a06t_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=160, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
