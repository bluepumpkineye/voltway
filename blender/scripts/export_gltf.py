"""Merge the SU7 build for the draw-call budget and export it to the web app.

Two files, so the exterior stays inside the hero budget (150-400k tris) and
the cabin streams in only when a visitor goes inside:

    su7-ultra.glb            exterior, ~375k tris
    su7-ultra-interior.glb   the cabin, lighting baked (carkit.bake)
    su7-ultra-cabin.hdr      the cabin reflection probe

Machinery in carkit.export. Objects stay separate where the web app
addresses them by name:

    screen_main              the quad the live HMI is mounted onto
    int_door_L/R, int_rdoor_L/R
                             door cards, origin on the hinge axis
    int_trunk                the felt under the trunk lid, origin on its hinge
    SU7Ultra_Blackout        the black glass underlay and inner shadow shell:
                             they make the glass read deep from outside and
                             would wall the camera in - hidden in the cabin view
    SU7Ultra_Body            the paint, visible from inside through the glass
    SU7Ultra_Door_FL/FR/RL/RR, SU7Ultra_DoorFrame_*
                             the four doors and the inside of each, origin on
                             the hinge (su7_openings)
    SU7Ultra_Bonnet          the clamshell bonnet and its underside (su7_bays)
    SU7Ultra_Trunk           the trunk lid, wing and all, and SU7Ultra_TrunkArms,
                             its gooseneck arms (su7_trunk)
    SU7Ultra_Greenhouse      the roof rail and glass above the belt: the X-ray's
                             ghost

Everything else is merged, so the app finds live surfaces (ambient strips,
headlamps, screens) by MATERIAL name rather than mesh name.

Runs without the MCP, in a background Blender that starts from an empty scene,
so the open session is left alone:

    blender -b --factory-startup --python-expr
        "import sys; sys.path.append(r'<repo>/blender/scripts');
         import export_gltf as X; X.web_ext()"      # exterior only, ~1 min

    ... X.web()                                     # exterior + cabin, baked, ~12 min
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
DEST_SHADOW = os.path.join(MODELS, "su7-ultra-shadow.webp")

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

PROTECTED = {"screen_main", "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
             # the lid's liner swings with it (su7_trunk)
             "int_trunk",
             # the X-ray tab takes the headliner away
             "int_headliner"}
BLACKOUT = ("SU7Ultra_Shell_Shadow", "SU7Ultra_Greenhouse_Black", "SU7Ultra_Roof_Rear_Black")
# the roof rail and the panes above the belt: the X-ray tab's ghost
GREENHOUSE = ("SU7Ultra_Roof_Rail", "SU7Ultra_Glass_Windshield", "SU7Ultra_Glass_Quarter",
              "SU7Ultra_Glass_Rear")
GREENHOUSE_GROUP = ("SU7Ultra_Greenhouse", "SU7_GreenhouseGrp")
# the exterior's ambient occlusion (carkit.bake.ambient_occlusion): how far a
# surface looks for shade
AO_DISTANCE = 1.0
# the published size in metres (length, width, height): the studio stills' framing
DIMS = (5.070, 1.970, 1.465)

# joined name -> collection
GROUPS = [
    ("SU7Ultra_Body", "SU7_Body"),
    ("SU7Ultra_Wheels", "SU7_Wheels"),
    ("SU7Ultra_Details", "SU7_Details"),
    ("SU7Ultra_Blackout", "SU7_Blackout"),
]
INTERIOR_GROUPS = [("SU7Ultra_Cabin", "SU7_Interior")]

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


def check_transmission():
    """KHR_materials_transmission blanks the three.js frame: after
    export_safe() no exported material may transmit."""
    bad = []
    for _, cname in GROUPS:
        col = bpy.data.collections.get(cname)
        for o in (col.objects if col else ()):
            for m in (o.data.materials if o.type == 'MESH' else ()):
                if m is None or not m.use_nodes:
                    continue
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                t = b.inputs.get("Transmission Weight") if b else None
                if t is not None and (t.is_linked or t.default_value > 0.0):
                    bad.append(m.name)
    if bad:
        raise RuntimeError("transmissive materials left: %s" % sorted(set(bad)))


def split_greenhouse():
    """The roof rail and the panes of glass above the belt become a node of
    their own, so the viewer's X-ray tab can turn it to a ghost."""
    col = bpy.data.collections.get(GREENHOUSE_GROUP[1]) or bpy.data.collections.new(GREENHOUSE_GROUP[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in GREENHOUSE:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("greenhouse part %s missing from the build" % n)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    return col


def prepare_exterior():
    """Everything the exterior needs before it is merged and exported: the
    blackout layer split off, the bonnet, the four doors and the trunk lid made
    hinged nodes, the hull opened behind them, the greenhouse its own node. Once
    per build (SU7_Trunk marks it done); the cabin's open-state bake wants the
    parts split, so web() calls it before that bake."""
    if bpy.data.objects.get("SU7_Trunk") is not None:
        return
    from carkit import materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import su7_bays as BY
    import su7_openings as OP
    import su7_trunk as TR
    BY.build_frunk()          # the bay under the bonnet, then the bonnet as a hinged node
    BY.split_bonnet()
    BY.open_hull()
    OP.build_sill()           # the painted sill, carbon plates and seal bead of the doorways
    OP.cut_underlay()         # the windows out of the black underlay: it must not stay behind
    TR.build_seal()           # a black bead behind the trunk lid's shut line
    TR.build_cups()           # the cups its gooseneck arms end in
    OP.split_doors()          # a hinged node per door (the cabin's cards: join_doors)
    OP.open_hull()            # the hull behind them, so the cabin shows when one is open
    TR.split_lid()            # the lid: skin, deck, wing, lamps' inner halves - one node
    TR.build_arms()           # its arms, shown while it is open
    split_greenhouse()        # roof rail and glass above the belt: the X-ray's ghost


def exterior_groups():
    import su7_bays as BY
    import su7_openings as OP
    import su7_trunk as TR
    return GROUPS + OP.door_groups() + BY.bonnet_groups() + TR.trunk_groups() + [GREENHOUSE_GROUP]


def open_all(on=True):
    """Every door, the bonnet and the trunk lid swung open (or shut again)."""
    import su7_bays as BY
    import su7_openings as OP
    import su7_trunk as TR
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0, card=False)
    BY.set_bonnet(BY.OPEN_DEG if on else 0.0)
    TR.set_lid(TR.OPEN_DEG if on else 0.0, card=False)


def bake_exterior_ao(samples=512):
    """Ambient occlusion per vertex on every exterior mesh (_BAKEDAO).

    With every opening OPEN: the jambs, the frunk and the boot are inside a
    closed car and would bake black, and the outer skins do not change. The
    cabin is left out so the result does not depend on whether this build made
    it. Before the merge, where the parts have their own names."""
    from carkit import bake as BK
    prepare_exterior()
    objs = []
    for _, cname in exterior_groups():
        col = bpy.data.collections.get(cname)
        objs += [o for o in (col.objects if col else ()) if o.type == 'MESH']
    hide = [o for cname in ("SU7_Interior",)
            for o in (bpy.data.collections[cname].all_objects if cname in bpy.data.collections else ())]
    ground = bpy.data.objects.get("Ground")
    if ground is not None:
        hide.append(ground)
    open_all(True)
    try:
        return BK.ambient_occlusion(objs, samples=samples, distance=AO_DISTANCE, hide=hide)
    finally:
        open_all(False)


def merge_for_export():
    prepare_exterior()
    return _X.merge_for_export(exterior_groups(), PROTECTED)


def export(path=DEST, draco=True, attributes=True):
    return _X.export(path, exterior_groups(), "SU7Ultra_Body", draco=draco, attributes=attributes)


def bake_ground_shadow():
    """The car's shadow on the studio floor (carkit.studio), as the WebP the
    showroom lays under it. Its size and centre are printed: they go in the
    vehicle data (assets.studioShadow). Run on the merged exterior, shut."""
    from carkit import studio
    car = []
    for _, cname in exterior_groups():
        col = bpy.data.collections.get(cname)
        car += [o for o in (col.objects if col else ()) if o.type == 'MESH']
    hide = [o for o in (bpy.data.collections["SU7_Interior"].all_objects
                        if "SU7_Interior" in bpy.data.collections else ())]
    png = os.path.normpath(os.path.join(os.path.dirname(DEST_SHADOW), "..", "..", "blender", "renders",
                                        "su7-ultra-shadow.png"))
    os.makedirs(os.path.dirname(png), exist_ok=True)
    info = studio.ground_shadow(png, car, hide=hide)
    studio.to_webp(png, DEST_SHADOW)
    return info


def stills(shots=("hero", "side", "front", "rear34"), samples=256, res=(1920, 1080), out_dir=None):
    """Cycles stills of the car in the web's studio (carkit.rig): the rig in
    src/data/studio/rig.ts as emissive panels, the white floor with the baked
    ground shadow, the camera at each of the showroom's named poses. The
    reference the web view is checked against (docs/3d-pipeline.md, studio
    stills). Fresh build, exterior only, as the web ships it:

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_gltf as X; X.stills()"

    Written to blender/renders/studio/su7-ultra_<shot>.png (gitignored)."""
    for m in [m for m in sys.modules if m.startswith("su7_") or m == "build_su7"]:
        sys.modules.pop(m, None)
    import build_su7
    from carkit import materials as MB
    from carkit import rig, studio
    build_su7.main(interior=False)
    MB.export_safe()
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    car = [o for _, cname in exterior_groups() for o in
           (bpy.data.collections[cname].objects if cname in bpy.data.collections else ()) if o.type == 'MESH']
    png = os.path.join(rig.RENDER_DIR, "su7-ultra-shadow.png")
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    info = studio.ground_shadow(png, car)
    rig.build_studio(shadow=(png, info["size"], info["centre"]))
    d = out_dir or rig.RENDER_DIR
    return [rig.still(s, os.path.join(d, "su7-ultra_%s.png" % s), dims=DIMS, res=res, samples=samples)
            for s in shots]


def main(draco=True, ao=True, ao_samples=512, shadow=True):
    """The exterior only (the scene must hold a fresh build_su7.main())."""
    prepare_exterior()
    open_all(False)           # every part at its hinge, as the closed car (the arms start elsewhere)
    if ao:
        bake_exterior_ao(ao_samples)
    merge_for_export()
    if shadow:
        bake_ground_shadow()
    return export(draco=draco, attributes=ao)


def web_ext(draco=True):
    """Fresh build -> merged exterior GLB (no cabin)."""
    for m in [m for m in sys.modules if m.startswith("su7_") or m == "build_su7"]:
        sys.modules.pop(m, None)
    import build_su7
    from carkit import materials as MB
    build_su7.main(interior=False)
    MB.export_safe()
    return main(draco=draco)


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
    """Each door card's parts (front and rear) -> one object, origin on the
    hinge (su7_openings)."""
    import su7_openings as OP
    OP.join_cards(collection)


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


def bake_cabin_open(samples=256):
    """The same vertex lighting with every door and the trunk lid open: the
    second set of light the viewer blends in as a part swings open (the cabin
    is lit by the doorways, the boot by the sky). Needs prepare_exterior()
    first, so the parts are split and hinged."""
    from carkit import bake as BK
    import su7_openings as OP
    import su7_trunk as TR
    col = bpy.data.collections["SU7_Interior"]
    OP.join_cards()
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"])
    TR.set_lid(TR.OPEN_DEG)
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col, attr=BK.ATTR_OPEN)
            stats = BK.vertex_lighting(objs, samples=samples, attr=BK.ATTR_OPEN)
            BK.smooth(objs, attr=BK.ATTR_OPEN)
            BK.to_generic(objs, BK.ATTR_OPEN, BK.EXPORT_ATTR_OPEN)
    finally:
        for ob in hidden:
            ob.hide_render = False
        for key in OP.DOORS:
            OP.set_angle(key, 0.0)
        TR.set_lid(0.0)
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


def cabin_screens():
    """The generated instrument cluster on its display, as cabin_lighting() puts it for the bake (the hall look has no
    bake, but the cluster must still ship lit). screen_main ships plain: the app draws the live HMI over it."""
    import su7_interior as IN
    from carkit.qa import hmi_capture as HC
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, IN.cluster_image(), 1.3)


def atlas_cabin(samples=512):
    """The cabin's occlusion atlas (carkit.aoatlas): a second UV set, a 2048 x 2048 Cycles AO bake with the exterior and
    the glass out of the way, and the glTF occlusion wired into every cabin material. Runs on the merged export meshes."""
    from carkit import aoatlas as AA
    return AA.atlas_for("SU7_Interior", samples=samples)


def export_interior(draco=True, look="baked"):
    """look="baked": per-vertex Cycles light under the outdoor world (bake_cabin and bake_cabin_open first).
    look="hall": HIMA's cabin light - no vertex light, a 2048 occlusion atlas on a second UV set, lit in the viewer by
    the shared hall environment (public/models/cabin-hall.hdr, carkit.hall_env; export_zx.web_cabin writes it)."""
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
    if look == "hall":
        atlas_cabin()
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "SU7Ultra_Cabin", draco=draco,
                     attributes=True, image_format='WEBP' if look == "hall" else 'AUTO')


def web_cabin(draco=True, look="baked"):
    """The cabin alone: fresh build of body and cabin -> the interior GLB, with the exterior, the probe and the
    backdrop left as they are.

    look="hall" (about 4 min in a background Blender): no vertex light, no probe and no second (doors open) set; the
    cabin ships with its occlusion atlas and the viewer lights it from public/models/cabin-hall.hdr. look="baked" is
    web()'s bake and cabin export, ~10 min."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("su7_") or m == "build_su7"]:
        sys.modules.pop(m, None)
    import build_su7
    build_su7.main(interior=False)
    import su7_interior as IN
    IN.main()
    import su7_trunk as TR
    TR.build_boot()           # the boot behind the lid, and the lid's liner
    TR.build_liner()
    print("build: %.0f s" % (time.time() - t))
    if look == "hall":
        prepare_exterior()    # the doors are hinged nodes before join_doors() makes the cards
        cabin_screens()
        res = {"interior": export_interior(draco=draco, look="hall")}
        print("web_cabin (hall): %.0f s" % (time.time() - t))
        return res
    stats = bake_cabin(probe_samples=384)
    prepare_exterior()
    stats_open = bake_cabin_open()
    res = {"bake": stats, "bake_open": stats_open, "interior": export_interior(draco=draco)}
    print("web_cabin: %.0f s" % (time.time() - t))
    return res


def web(samples=256, probe_samples=384):
    """Full rebuild -> baked cabin (shut, then every opening open) -> both GLBs,
    the probe and the backdrop. In a background Blender (module docstring)."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("su7_") or m == "build_su7"]:
        sys.modules.pop(m, None)
    import build_su7
    build_su7.main(interior=False)
    import su7_interior as IN
    IN.main()
    import su7_trunk as TR
    TR.build_boot()           # the boot behind the lid, and the lid's liner
    TR.build_liner()
    print("build: %.0f s" % (time.time() - t))
    stats = bake_cabin(samples, probe_samples)
    print("bake: %.0f s" % (time.time() - t))
    prepare_exterior()
    stats_open = bake_cabin_open(samples)
    print("bake open: %.0f s" % (time.time() - t))
    out = {"bake": stats, "bake_open": stats_open, **exports()}
    print("web: %.0f s" % (time.time() - t))
    return out


def exports():
    """Everything web() writes after the bake."""
    out_i = export_interior()
    from carkit import materials as MB
    MB.export_safe()
    out_e = main()
    return {"interior": out_i, "exterior": out_e, "backdrop": export_outside()}


if __name__ == "__main__":
    web()
