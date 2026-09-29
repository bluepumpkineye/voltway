"""One entry point for the Luxeed RX build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_rx; build_rx.main()

The RX is carkit's second car. Its modules hold only its data, in build
order:

    rx_surface     profile curves of the flank loft (carkit LoftBody)
    rx_nose        nose and tail caps (carkit WrapCap) and the CarBody
    rx_panels      panel layout, window lines, openings
    rx_front       fascia, headlamps, intakes, lower grille, badge, lidar
    rx_rear        tailgate, light bar, ducktail, bumper, lettering
    rx_side        mirrors, handles, arch cladding, skirts, vent, charge door
    rx_wheels      the 5-spoke wheel and the corner table
    rx_materials   the RX's finishes on carkit's material library
    rx_ref_match   the solved reference cameras (rx_camsolve: the readings)
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("rx_surface", "rx_nose", "rx_panels", "rx_front", "rx_rear", "rx_side",
           "rx_wheels", "rx_materials", "rx_ref_match", "rx_trace", "rx_preview",
           "scene_setup")
COLLECTIONS = ("RX_Body", "RX_Details", "RX_Wheels")
PARTS = ("rx_front", "rx_rear", "rx_side")


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
    import rx_surface as S
    import rx_panels as P
    import rx_materials as MT

    body = B.fresh_collection("RX_Body")
    dcol = B.fresh_collection("RX_Details")
    wcol = B.fresh_collection("RX_Wheels")

    from carkit.jev.triage import guard
    lib = MT.build_library()
    with guard("building rx_panels"):
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
            import rx_wheels as W
        except ImportError:
            W = None
        if W:
            with guard("building rx_wheels"):
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
    for m in tuple(names) + ("rx_materials",):
        sys.modules.pop(m, None)
    import rx_materials as MT
    from carkit import build as B
    dcol = bpy.data.collections.get("RX_Details") or B.fresh_collection("RX_Details")
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
    for m in ("rx_wheels", "rx_materials"):
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m.startswith("carkit.parts")]:
        sys.modules.pop(name, None)
    import rx_wheels as W
    import rx_surface as S
    import rx_materials as MT
    from carkit import build as B
    from carkit.jev.triage import guard
    wcol = B.fresh_collection("RX_Wheels")
    with guard("rebuilding rx_wheels"):
        return W.build_all(wcol, S, MT.build_library())


def body_part(fn_name, prefixes):
    """Rebuild one rx_panels builder (e.g. 'build_wheel_liners') in RX_Body,
    removing the objects whose names start with `prefixes` first."""
    for m in ("rx_panels", "rx_materials"):
        sys.modules.pop(m, None)
    import rx_panels as PN
    import rx_materials as MT
    col = bpy.data.collections["RX_Body"]
    for o in [o for o in col.objects if o.name.startswith(tuple(prefixes))]:
        bpy.data.objects.remove(o, do_unlink=True)
    return getattr(PN, fn_name)(col, MT.build_library())


PREFIXES = {
    "rx_front": ("RX_Fascia", "RX_Band", "RX_Intake", "RX_Radar", "RX_Chin", "RX_Lamp",
                 "RX_Emblem", "RX_Plate", "RX_Lidar"),
    "rx_rear": ("RX_Tail", "RX_Rear", "RX_Lightbar", "RX_Ducktail", "RX_Badge",
                "RX_Letter", "RX_Pod", "RX_Diffuser", "RX_Reflector", "RX_Spoiler", "RX_Glass_Rear",
                "RX_Roof_Blade"),
    "rx_side": ("RX_Mirror", "RX_Handle", "RX_Clad", "RX_Skirt", "RX_Vent", "RX_Charge",
                "RX_Script", "RX_DLO"),
}


def fingerprint():
    from carkit.qa import checks
    import rx_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=160, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
