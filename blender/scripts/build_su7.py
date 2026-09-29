"""One entry point for the whole SU7 Ultra build.

Run inside Blender:

    import sys; sys.path.append(r"<repo>/blender/scripts")
    import build_su7; build_su7.main()

The SU7 is the first car built on carkit (blender/scripts/carkit). Its
modules hold only this car's data - hardpoints, curves, panel layout - in
build order:

    su7_surface    profile curves of the flank loft (carkit LoftBody)
    su7_nose       nose and tail caps (carkit WrapCap) and the CarBody
    su7_panels     panel layout, openings, fascia (carkit.body.panels/fascia)
    su7_front      headlamps, splitter, intake mesh, plate, stripes, lidar, fins
    su7_rear       light bar, wing, ducktail, diffuser, badges, vent fins
    su7_side       mirrors, flush handles, skirts, side stripe and script
    su7_wheels     the forged hairpin wheel preset and the corner table
    su7_materials  the SU7's finishes on carkit's material library
    scene_setup    studio rig, cameras, Cycles, colour (carkit.scene)

The interior (build_su7_interior) carries ``screen_main``, the quad the web app
mounts its live HMI onto. It is off by default while the exterior is being
worked on, and must be on for any export that ships to the web app.
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODULES = ("su7_surface", "su7_nose", "su7_panels", "su7_front", "su7_rear",
           "su7_side", "su7_wheels", "su7_materials", "su7_textures",
           "scene_setup", "ref_match", "surface_qa", "export_gltf",
           "build_su7_interior")
COLLECTIONS = ("SU7_Body", "SU7_Details", "SU7_Wheels")


def _reload():
    for m in MODULES:
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)


def main(interior=False, reset=True):
    if reset:
        bpy.ops.wm.read_homefile(use_empty=True)
        try:
            bpy.context.scene.blendermcp_use_polyhaven = True
        except Exception:
            pass
    _reload()
    from carkit import build as B
    from carkit import mesh as M
    import su7_surface as S
    import su7_panels as P
    import su7_front as F
    import su7_rear as R
    import su7_side as D
    import su7_wheels as W
    import su7_materials as MT
    import scene_setup as SC

    body = B.fresh_collection("SU7_Body")
    dcol = B.fresh_collection("SU7_Details")
    wcol = B.fresh_collection("SU7_Wheels")

    lib = MT.build_library()
    P.build_all(body, lib)
    F.build_all(dcol, lib)
    R.build_all(dcol, lib)
    D.build_all(dcol, lib)
    W.build_all(wcol, S, lib)
    SC.main()

    if interior:
        import build_su7_interior as I
        I.main()
        icol = bpy.data.collections.get("SU7_Interior")
        if icol:
            for ob in icol.objects:
                if ob.type == 'LIGHT':
                    ob.hide_render = True

    B.ensure_uvs([body, dcol, wcol])
    B.report([body, dcol, wcol], S.BODY, "SU7_Interior" if interior else None)

    objs = [o for c in (body, dcol, wcol) for o in c.objects]
    icol = bpy.data.collections.get("SU7_Interior")
    if icol:
        objs += [o for o in icol.objects if o.type == 'MESH']
    tris = M.tri_count(objs)
    print("objects: %d   tris (evaluated): %d" % (len(objs), tris))
    print("dims:", S.dims_report())
    return {"body": body, "wheels": wcol, "details": dcol, "lib": lib, "tris": tris}


# ------------------------------------------------ old names, still importable
def ensure_uvs(collections, scale=1.0, force=("M_Carbon",)):
    from carkit import build as B
    return B.ensure_uvs(collections, scale, force)


def check_envelope(collections, margin=0.10):
    from carkit.qa import checks
    import su7_surface as S
    return checks.envelope(collections, S.HALF_L, S.HALF_W, margin)


def check_cabin_clearance(collection_name="SU7_Interior", allowance=0.012):
    from carkit.qa import checks
    import su7_surface as S
    return checks.cabin_clearance(S.BODY, collection_name, allowance)


def fingerprint():
    """The build's fingerprint (carkit.qa.checks) - take one before a refactor."""
    from carkit.qa import checks
    import su7_nose as N
    return checks.fingerprint(COLLECTIONS, body=N.BODY)


def shots(prefix, names=("hero_f34", "side", "front", "rear_34"),
          samples=160, res=(1920, 1080)):
    import scene_setup as SC
    return [SC.render(n, "%s_%s.png" % (prefix, n), samples=samples, res=res)
            for n in names]


if __name__ == "__main__":
    main()
