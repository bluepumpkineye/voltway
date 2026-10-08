"""One entry point for the Zeekr 7X build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_zx; build_zx.main()

The 7X is carkit's fourth car, built from the RX's modules. Its modules hold only its data, in build
order:

    zx_surface     profile curves of the flank loft (carkit LoftBody)
    zx_nose        nose and tail caps (carkit WrapCap) and the CarBody
    zx_panels      panel layout, window lines, openings
    zx_front       fascia, headlamps, intakes, lower grille, badge, lidar
    zx_rear        tailgate, light bar, ducktail, bumper, lettering
    zx_side        mirrors, handles, arch cladding, skirts, vent, charge door
    zx_wheels      the 5-spoke wheel and the corner table
    zx_materials   the RX's finishes on carkit's material library
    zx_ref_match   the solved reference cameras (zx_camsolve: the readings)
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("zx_surface", "zx_nose", "zx_panels", "zx_front", "zx_rear", "zx_side",
           "zx_wheels", "zx_materials", "zx_ref_match", "zx_preview",
           "scene_setup")
COLLECTIONS = ("ZX_Body", "ZX_Details", "ZX_Wheels")
PARTS = ("zx_front", "zx_rear", "zx_side")


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
    import zx_surface as S
    import zx_panels as P
    import zx_materials as MT

    body = B.fresh_collection("ZX_Body")
    dcol = B.fresh_collection("ZX_Details")
    wcol = B.fresh_collection("ZX_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building zx_panels"):
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
            import zx_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building zx_wheels"):
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


def parts(names=PARTS, keep=()):
    """Rebuild only the detail modules `names` on the existing body: their
    objects (by name prefix, see PREFIXES) are removed first. Much faster than
    main() while a module is being worked on."""
    for m in tuple(names) + ("zx_materials",):
        sys.modules.pop(m, None)
    import zx_materials as MT
    from carkit import build as B
    dcol = bpy.data.collections.get("ZX_Details") or B.fresh_collection("ZX_Details")
    doomed = set()
    for m in names:
        for pre in PREFIXES.get(m, ()):
            doomed |= {o for o in dcol.objects if o.name.startswith(pre)}
    for o in doomed:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if d is not None and d.users == 0 and isinstance(d, bpy.types.Mesh):
            bpy.data.meshes.remove(d)
    from carkit.jev.triage import guard
    lib = MT.build_library()
    made = []
    for m in names:
        with guard("rebuilding " + m):
            made += __import__(m).build_all(dcol, lib)
    return made


def wheels():
    """Rebuild the four wheels only."""
    for m in ("zx_wheels", "zx_materials"):
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m.startswith("carkit.parts")]:
        sys.modules.pop(name, None)
    import zx_wheels as W
    import zx_surface as S
    import zx_materials as MT
    from carkit import build as B
    from carkit.jev.triage import guard
    wcol = B.fresh_collection("ZX_Wheels")
    with guard("rebuilding zx_wheels"):
        return W.build_all(wcol, S, MT.build_library())


def body_part(fn_name, prefixes):
    """Rebuild one zx_panels builder (e.g. 'build_wheel_liners') in ZX_Body,
    removing the objects whose names start with `prefixes` first."""
    for m in ("zx_panels", "zx_materials"):
        sys.modules.pop(m, None)
    import zx_panels as PN
    import zx_materials as MT
    col = bpy.data.collections["ZX_Body"]
    for o in [o for o in col.objects if o.name.startswith(tuple(prefixes))]:
        bpy.data.objects.remove(o, do_unlink=True)
    return getattr(PN, fn_name)(col, MT.build_library())


PREFIXES = {
    "zx_front": ("ZX_Fascia", "ZX_Band", "ZX_Intake", "ZX_Lamp", "ZX_Lightbar", "ZX_Chin",
                 "ZX_Emblem", "ZX_Grille", "ZX_Sensor", "ZX_Lidar", "ZX_Hoodline"),
    "zx_rear": ("ZX_Tail", "ZX_Rear", "ZX_Lightbar_R", "ZX_Ducktail", "ZX_Badge",
                "ZX_Letter", "ZX_Reflector", "ZX_Spoiler", "ZX_Glass_Rear", "ZX_Diffuser",
                "ZX_Camera_R", "ZX_Roof_Blade"),
    "zx_side": ("ZX_Mirror", "ZX_Handle", "ZX_Clad", "ZX_Skirt", "ZX_Gill", "ZX_Charge",
                "ZX_Script", "ZX_Sill", "ZX_Rail"),
}


def fingerprint():
    from carkit.qa import checks
    import zx_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=160, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
