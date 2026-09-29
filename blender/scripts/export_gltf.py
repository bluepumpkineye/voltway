"""Merge the SU7 build for the draw-call budget and export it to the web app.

Two files, so the exterior stays inside the hero budget (150-400k tris) and
the cabin streams in only when a visitor goes inside:

    su7-ultra.glb            exterior, ~375k tris
    su7-ultra-interior.glb   the cabin, lighting baked (carkit.bake)
    su7-ultra-cabin.hdr      the cabin reflection probe

Machinery in carkit.export. Objects stay separate where the web app
addresses them by name:

    screen_main              the quad the live HMI is mounted onto
    int_door_L / int_door_R  door cards, origin on the hinge axis
    SU7Ultra_Blackout        the black glass underlay and inner shadow shell:
                             they make the glass read deep from outside and
                             would wall the camera in - hidden in the cabin view
    SU7Ultra_Body            the paint, visible from inside through the glass

Everything else is merged, so the app finds live surfaces (ambient strips,
headlamps, screens) by MATERIAL name rather than mesh name.

    import export_gltf as X
    X.web()        # full rebuild, bake, both exports (~6 min)
"""
import os
import sys

import bpy
from mathutils import Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit import export as _X                  # noqa: E402

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
DEST = os.path.join(MODELS, "su7-ultra.glb")
DEST_INTERIOR = os.path.join(MODELS, "su7-ultra-interior.glb")
DEST_PROBE = os.path.join(MODELS, "su7-ultra-cabin.hdr")
DEST_OUTSIDE = os.path.join(MODELS, "su7-ultra-outside.jpg")
DEST_OUTSIDE_LIGHT = os.path.join(MODELS, "su7-ultra-outside-light.hdr")

# What the parked car stands in: the daylight the cabin is baked under and,
# as the same image, the view out of it (the viewer's backdrop). Poly Haven
# "Shanghai Riverside" (CC0), a clear golden hour on the Huangpu, turned so
# the Lujiazui skyline is ahead-right through the windscreen and the low sun
# behind the car (unturned, it glared straight through the windscreen). The
# sun is clamped out of the bake (carkit.scene.hdri_world).
OUTSIDE = dict(
    path=os.path.join(_HERE, "..", "textures", "hdri", "shanghai_riverside_4k.hdr"),
    strength=1.0, rotation=153.6, clamp=8.0)
# the viewer's toneMappingExposure (VehicleViewer.tsx): the backdrop is tone
# mapped at build time, so it has to match
WEB_EXPOSURE = 0.92
# The cabin rig (calibrated alone against the press render's studio light)
# as a photographer's fill under the daylight: without it the pedals and the
# wheel hub sank to black; at full strength the cabin read studio-lit again.
RIG_FILL = 0.5

PROTECTED = {"screen_main", "int_door_L", "int_door_R"}
BLACKOUT = ("SU7Ultra_Shell_Shadow", "SU7Ultra_Greenhouse_Black", "SU7Ultra_Roof_Rear_Black")

# joined name -> collection
GROUPS = [
    ("SU7Ultra_Body", "SU7_Body"),
    ("SU7Ultra_Wheels", "SU7_Wheels"),
    ("SU7Ultra_Details", "SU7_Details"),
    ("SU7Ultra_Blackout", "SU7_Blackout"),
]
INTERIOR_GROUPS = [("SU7Ultra_Cabin", "SU7_Interior")]

# Front door hinge axis (vertical): the leading edge at mid height, on the skin
HINGE = (0.972, 0.930, 0.600)

# where the cabin probe is shot from: between the front seats at head height
PROBE_AT = (-0.35, 0.0, 1.10)
# how much of the render rig's lights the probe (the cabin's reflections) sees
PROBE_LIGHT_MIX = 0.3


def split_blackout():
    """Move the blackout layer into its own collection (its own glTF node)."""
    col = bpy.data.collections.get("SU7_Blackout") or bpy.data.collections.new("SU7_Blackout")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in BLACKOUT:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    return col


def merge_for_export():
    split_blackout()
    return _X.merge_for_export(GROUPS, PROTECTED)


def export(path=DEST, draco=True):
    return _X.export(path, GROUPS, "SU7Ultra_Body", draco=draco)


def main(draco=True):
    """The exterior only (the scene must hold a fresh build_su7.main())."""
    merge_for_export()
    return export(draco=draco)


# ------------------------------------------------------------------ cabin
def cabin_lighting():
    """The lighting the cabin is baked under: the OUTSIDE world (daylight
    through the glass), the cabin rig in su7_interior.cabin_lights turned
    down to a fill (RIG_FILL), the HMI and cluster images on the displays,
    and the blackout layer hidden so light comes in through the glass.

    Wrap renders and bakes in carkit.bake.thin_glass(): through the glazing
    as modelled, no daylight reaches the cabin at all."""
    import su7_interior as IN
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    from carkit.textures import TEX_DIR
    SC.hdri_world(**OUTSIDE)
    col = bpy.data.collections.get("SU7_Interior")
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * RIG_FILL
    # (after a merge the cluster lives inside the cabin, already lit)
    for name, image, strength in (
            ("screen_main", os.path.join(TEX_DIR, "hmi_xiaomi-su7-ultra.png"), 1.1),
            ("screen_cluster", None, 1.3)):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            HC.apply(ob, image or IN.cluster_image(), strength)
    hidden = []
    # and the lookdev floor: the HDRI brings its own ground (the plaza), which
    # is what the viewer shows through the glass - the studio floor mirrored
    # the skyline under the car like a river
    for n in BLACKOUT + ("SU7Ultra_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def join_doors(collection="SU7_Interior"):
    """Each front door card's parts -> one object, origin on the hinge, so
    the app can swing it (rotation about glTF +Y)."""
    col = bpy.data.collections[collection]
    for tag, sign in (("L", 1.0), ("R", -1.0)):
        names = [o.name for o in col.objects
                 if o.type == 'MESH' and o.name.startswith("int_door_%s_" % tag)]
        ob = _X.join("int_door_" + tag, names)
        if ob is None:
            continue
        h = Vector((HINGE[0], sign * HINGE[1], HINGE[2]))
        ob.data.transform(Matrix.Translation(ob.matrix_world.translation - h))
        ob.matrix_world = Matrix.Translation(h)


def bake_cabin(samples=256, probe_samples=384):
    """Vertex lighting on every cabin mesh + the reflection probe."""
    from carkit import bake as BK
    col = bpy.data.collections["SU7_Interior"]
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col)
            stats = BK.vertex_lighting(objs, samples=samples)
            BK.smooth(objs)
            BK.to_generic(objs)
            # The rig's lights go into the probe at 30 %: one probe serves
            # every surface, and from its spot between the seats the 1.7 m
            # roof softbox fills half the sky - at full strength the pedals,
            # the console carbon and the rear-view mirror mirrored it white; at
            # zero the leather and the wheel lost every highlight
            # (carkit.bake.probe_mix).
            lights = [o for o in col.objects if o.type == 'LIGHT' and o.visible_glossy]
            BK.probe_mix(PROBE_AT, DEST_PROBE, lights, mix=PROBE_LIGHT_MIX,
                         samples=probe_samples)
    finally:
        for ob in hidden:
            ob.hide_render = False
    return stats


def export_outside():
    """The world outside, for the viewer's cabin view: the backdrop JPEG (the
    view out) and a small HDR of the same world (the light on the bodywork
    seen through the glass). carkit.bake.backdrop / backdrop_light."""
    from carkit import bake as BK
    o = OUTSIDE
    view = BK.backdrop(o["path"], DEST_OUTSIDE, rotation=o["rotation"],
                       strength=o["strength"], exposure=WEB_EXPOSURE)
    # 1024 wide: it also lights the paint in the exterior view, whose clear
    # coat mirrors it sharply (at 512 the skyline smeared along the flanks)
    light = BK.backdrop_light(o["path"], DEST_OUTSIDE_LIGHT, rotation=o["rotation"],
                              strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def export_interior(draco=True):
    from carkit import bake as BK
    from carkit import build as B
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections["SU7_Interior"]
    # the app draws the live HMI over screen_main: ship the plain screen
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if (m.name.startswith("INT_") and m.name != "INT_Screen")
        or m.name == "M_Carbon"))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    join_doors()
    _X.merge_for_export(INTERIOR_GROUPS, PROTECTED)
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "SU7Ultra_Cabin", draco=draco,
                     attributes=True)


def web(samples=256, probe_samples=384):
    """Full rebuild -> baked cabin -> both GLBs, the probe and the backdrop.

    Through the MCP, run everything up to bake_cabin() on a persistent
    bpy.app.timers callback and the exports in a direct call (docs/3d-pipeline.md
    section 4)."""
    sys.modules.pop("build_su7", None)
    import build_su7
    build_su7.main(interior=False)
    import su7_interior as IN
    IN.main()
    stats = bake_cabin(samples, probe_samples)
    return {"bake": stats, **exports()}


def exports():
    """Everything web() writes after the bake."""
    out_i = export_interior()
    from carkit import materials as MB
    MB.export_safe()
    out_e = main()
    return {"interior": out_i, "exterior": out_e, "backdrop": export_outside()}


if __name__ == "__main__":
    web()
