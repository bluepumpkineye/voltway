"""Merge the Luxeed RX build for the draw-call budget and export it to the web app.

    luxeed-rx.glb               exterior, ~383k tris, Draco
    luxeed-rx-interior.glb      the cabin (rx_interior), Cycles light baked per
                                vertex (_BAKEDLIGHT), ~200k tris
    luxeed-rx-cabin.hdr         the cabin's reflection probe
    luxeed-rx-outside.jpg/.hdr  the world the car stands in and the cabin
                                looks out on (Beijing, carkit.bake.backdrop)

Machinery in carkit.export, as for the SU7 (export_gltf.py). Nodes:

    LuxeedRX_Body            the painted shell, glass, lamps' surrounds
    LuxeedRX_Details         fascia, lamps, trim, mirrors, badges
    LuxeedRX_Fengying_Wheels_<FL|FR|RL|RR>  the wheels (22 in, the default), one node per corner
    LuxeedRX_Fengying_Wheels_Caliper_<tag>  and their calipers (these steer, they do not spin);
    LuxeedRX_Yufeng_Wheels_*, _Sport_Wheels_*  the 21 in designs (rx_wheels), hidden until chosen.
                                            See CORNERS and split_wheels.
    LuxeedRX_Blackout        the black glass underlay and inner shadow shell
                             (the viewer hides any "*_blackout" node inside)

Runs without the MCP, in a background Blender that starts from an empty
scene, so the open session is left alone:

    blender -b --factory-startup --python-expr
        "import sys; sys.path.append(r'<repo>/blender/scripts');
         import export_rx; export_rx.web()"      # exterior only, ~1 min

    ... export_rx.web_full()                     # body + cabin, baked, ~8 min
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit import export as _X                  # noqa: E402

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
DEST = os.path.join(MODELS, "luxeed-rx.glb")
DEST_INTERIOR = os.path.join(MODELS, "luxeed-rx-interior.glb")
DEST_PROBE = os.path.join(MODELS, "luxeed-rx-cabin.hdr")
DEST_OUTSIDE = os.path.join(MODELS, "luxeed-rx-outside.jpg")
DEST_OUTSIDE_LIGHT = os.path.join(MODELS, "luxeed-rx-outside-light.hdr")
DEST_SHADOW = os.path.join(MODELS, "luxeed-rx-shadow.webp")

# The world the car stands in, baked into the cabin and seen from it: Beijing,
# the paved square at Zhengyang Gate (Qianmen) on a clear spring morning
# (Poly Haven "Zhengyang Gate", Greg Zaal, CC0; the SU7 has the Shanghai
# riverside). Measured off the HDRI (hdri_an): the sun at image angle -35.9
# deg, 37.8 deg up; the gate tower at -74 .. -131, the Great Hall of the
# People at ~+160. Turned so the sun is behind-left of the car (135 deg) and
# the gate stands off the driver's side, the Great Hall ahead-right - no sun
# through the windscreen. Clamped out of the bake as the SU7's.
OUTSIDE = dict(
    path=os.path.join(_HERE, "..", "textures", "hdri", "zhengyang_gate_4k.hdr"),
    strength=1.0, rotation=189.0, clamp=8.0)
WEB_EXPOSURE = 0.92          # the viewer's toneMappingExposure
RIG_FILL = 0.5               # the cabin rig as a fill under the daylight (export_gltf)
PROTECTED = {"screen_main", "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
             # the hatch's liner swings with it; the shelf and sill under the
             # backlight go while it is open (rx_gate)
             "int_tailgate", "int_parcel_shelf", "int_rear_sill",
             # the X-ray tab takes the headliner away
             "int_headliner",
             # the rear pillar trims, whose ragged rear edges show from the open boot
             "int_cpillar", "int_cpillar_flange", "int_qtr_lower"}
INTERIOR_GROUPS = [("LuxeedRX_Cabin", "RX_Interior")]
# between the front seats at head height
PROBE_AT = (-0.40, 0.0, 1.20)
PROBE_LIGHT_MIX = 0.3

BLACKOUT = ("RX_Shell_Shadow", "RX_Greenhouse_Black", "RX_Roof_Rear_Black", "RX_Glass_RearBack")
# the exterior's ambient occlusion (carkit.bake.ambient_occlusion): how far a
# surface looks for shade, and how far the bonnet opens for the bake (as in the
# vehicle data)
AO_DISTANCE = 1.0
BONNET_DEG = 62.0
# the published size in metres (length, width, height): the studio stills' framing
DIMS = (5.020, 2.007, 1.585)

# joined name -> collection
GROUPS = [
    ("LuxeedRX_Body", "RX_Body"),
    ("LuxeedRX_Fengying_Wheels", "RX_Wheels"),
    ("LuxeedRX_Details", "RX_Details"),
    ("LuxeedRX_Blackout", "RX_Blackout"),
]
# the other wheel designs (rx_wheels.DESIGNS): built beside the default for the
# export only, each a node of its own; the viewer shows one at a time
WHEEL_GROUPS = [
    ("LuxeedRX_Yufeng_Wheels", "RX_Wheels_Yufeng"),
    ("LuxeedRX_Sport_Wheels", "RX_Wheels_Sport"),
]

# The wheels ship one NODE PER CORNER, so the showroom's tech demos can steer and
# roll them (src/lib/tech/rig.ts). Per design: <node>_<tag> holds everything that
# turns with the wheel (tyre, rim, face, disc) and <node>_Caliper_<tag> the caliper,
# which steers but does not spin. Each node's origin is the hub centre, its local
# frame the wheel's own (the build's wheel empty carries the placement), so a node
# spins about its axle. The viewer groups the four of a design back under <node>.
CORNERS = ("FL", "FR", "RL", "RR")


def _corner_col(cname, kind, tag):
    """The collection of one corner's wheel ('W') or caliper ('C') parts."""
    return "%s_%s_%s" % (cname, kind, tag)


def wheels_split():
    return bpy.data.collections.get(_corner_col(GROUPS[1][1], "W", "FL")) is not None


def split_wheels():
    """Re-collect every wheel design's parts by corner (see CORNERS). Once, after
    the ambient occlusion has been baked (it is per design, with the four wheels
    together) and before the merge."""
    if wheels_split():
        return
    for _, cname in [GROUPS[1]] + WHEEL_GROUPS:
        src = bpy.data.collections.get(cname)
        if src is None:
            continue
        for ob in list(src.objects):
            if ob.type != 'MESH':
                continue
            # a part is named <prefix><Part>_<tag> and parented to the corner's empty
            who = (ob.parent.name if ob.parent is not None else ob.name).split(".")[0]
            tag = who.rsplit("_", 1)[-1]
            if tag not in CORNERS:
                raise RuntimeError("wheel part %s has no corner (%s)" % (ob.name, who))
            kind = "C" if "_Caliper_" in ob.name else "W"
            name = _corner_col(cname, kind, tag)
            dst = bpy.data.collections.get(name) or bpy.data.collections.new(name)
            if dst.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(dst)
            src.objects.unlink(ob)
            dst.objects.link(ob)


def wheel_corner_groups(options=True):
    """(node, collection) per corner of the default design, and of the others."""
    out = []
    for node, cname in [GROUPS[1]] + (WHEEL_GROUPS if options else []):
        for tag in CORNERS:
            out.append(("%s_%s" % (node, tag), _corner_col(cname, "W", tag)))
            out.append(("%s_Caliper_%s" % (node, tag), _corner_col(cname, "C", tag)))
    return out


def split_blackout():
    """Move the blackout layer into its own collection (its own glTF node)."""
    col = bpy.data.collections.get("RX_Blackout") or bpy.data.collections.new("RX_Blackout")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in BLACKOUT:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("blackout object %s missing from the build" % n)
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


def prepare_exterior():
    """Everything the exterior needs before it is merged and exported: the
    blackout layer split off, the doors, the bonnet and the hatch made hinged
    nodes, the hull opened behind them, the greenhouse its own node. Once per
    build (RX_Tailgate marks it done); the cabin's open-state bake wants the
    parts split, so web_full() calls it before that bake."""
    if bpy.data.objects.get("RX_Tailgate") is not None:
        return
    from carkit import materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import rx_openings as OP
    import rx_bays as BY
    import rx_gate as RG
    BY.build_frunk()          # the bay under the bonnet, then the bonnet as a hinged node
    BY.split_bonnet()
    BY.open_hull()
    OP.build_sill()           # the painted sill, RX plates and seal bead of the doorways
    OP.cut_underlay()         # the windows out of the black underlay: it must not stay behind
    RG.cut_underlay()         # the backlight's footprint too
    RG.build_seal()           # a black bead behind the hatch's shut line
    OP.split_doors()          # a hinged node per door (the cabin's cards: join_doors)
    OP.open_hull()            # the hull behind them, so the cabin shows when one is open
    RG.split_tail()           # the hatch: skin, backlight, light bar, lettering - one node
    RG.open_hull()            # the hull behind it
    RG.split_greenhouse()     # roof, rails and glass above the belt: the X-ray's ghost


def exterior_groups(options=True):
    """Every exterior group; options=False leaves out the extra wheel designs."""
    import rx_openings as OP
    import rx_bays as BY
    import rx_gate as RG
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return (core + wheel_corner_groups(options) + OP.door_groups() + BY.bonnet_groups()
                + [RG.GROUP, RG.GREENHOUSE_GROUP])
    return (GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP, RG.GREENHOUSE_GROUP]
            + (WHEEL_GROUPS if options else []))


def build_wheel_options(lib):
    """The other wheel designs (rx_wheels), one collection each, on the car's own
    material library - before prepare_exterior(): rebuilding the library after it
    would undo export_safe(). Their ambient occlusion is baked one design at a
    time (bake_exterior_ao), since they stand in the same place."""
    if bpy.data.collections.get(WHEEL_GROUPS[0][1]) is not None:
        return
    import rx_surface as S
    import rx_wheels as RW
    from carkit import build as B
    cols = []
    for (_, cname), name in zip(WHEEL_GROUPS, [n for n in RW.DESIGNS if n != RW.DEFAULT]):
        col = B.fresh_collection(cname)
        RW.build_design(col, S, lib, name)
        cols.append(col)
    B.ensure_uvs(cols)
    return cols


def open_all(on=True):
    """Every door, the bonnet and the hatch swung open (or shut again)."""
    import rx_openings as OP
    import rx_bays as BY
    import rx_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0, card=False)
    BY.set_bonnet(BONNET_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0, card=False)


def bake_exterior_ao(samples=512):
    """Ambient occlusion per vertex on every exterior mesh (_BAKEDAO).

    With every opening OPEN: the jambs, the bay under the bonnet and the boot
    are inside a closed car and would bake black, and the outer skins do not
    change. The cabin is left out so the result does not depend on whether
    this build made it. Before the merge, where the parts have their own names."""
    from carkit import bake as BK
    prepare_exterior()

    def meshes(groups):
        return [o for _, cname in groups for o in
                (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
                if o.type == 'MESH']

    objs = meshes(exterior_groups(options=False))
    extra = [(cname, meshes([(n, cname)])) for n, cname in WHEEL_GROUPS if cname in bpy.data.collections]
    hide = [o for cname in ("RX_Interior",)
            for o in (bpy.data.collections[cname].all_objects if cname in bpy.data.collections else ())]
    ground = bpy.data.objects.get("Ground")
    if ground is not None:
        hide.append(ground)
    open_all(True)
    try:
        # the car with its own wheels, the other designs not there ...
        stats = BK.ambient_occlusion(objs, samples=samples, distance=AO_DISTANCE,
                                     hide=hide + [o for _, ms in extra for o in ms])
        # ... then each other design alone in the default wheels' place
        own = meshes([GROUPS[1]])
        for cname, ms in extra:
            gone = own + [o for c, other in extra if c != cname for o in other]
            BK.ambient_occlusion(ms, samples=samples, distance=AO_DISTANCE, hide=hide + gone)
        return stats
    finally:
        open_all(False)


def bake_ground_shadow():
    """The car's shadow on the studio floor (carkit.studio), as the WebP the
    showroom lays under it. Its size and centre are printed: they go in the
    vehicle data (assets.studioShadow). Run on the merged exterior, shut."""
    from carkit import studio
    car = []
    for _, cname in exterior_groups(options=False):
        col = bpy.data.collections.get(cname)
        car += [o for o in (col.objects if col else ()) if o.type == 'MESH']
    hide = [o for o in (bpy.data.collections["RX_Interior"].all_objects
                        if "RX_Interior" in bpy.data.collections else ())]
    png = os.path.join(os.path.dirname(DEST_SHADOW), "..", "..", "blender", "renders", "luxeed-rx-shadow.png")
    png = os.path.normpath(png)
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
            sys.path.append(r'<repo>/blender/scripts'); import export_rx; export_rx.stills()"

    Written to blender/renders/studio/luxeed-rx_<shot>.png (gitignored)."""
    import os
    sys.modules.pop("build_rx", None)
    import build_rx
    from carkit import rig, studio
    build_rx.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    car = [o for _, cname in exterior_groups() for o in
           (bpy.data.collections[cname].objects if cname in bpy.data.collections else ()) if o.type == 'MESH']
    png = os.path.join(rig.RENDER_DIR, "luxeed-rx-shadow.png")
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    info = studio.ground_shadow(png, car)
    rig.build_studio(shadow=(png, info["size"], info["centre"]))
    d = out_dir or rig.RENDER_DIR
    return [rig.still(s, os.path.join(d, "luxeed-rx_%s.png" % s), dims=DIMS, res=res, samples=samples)
            for s in shots]


def hmi_art(res=(1800, 900), samples=256):
    """The car as a cut-out for the infotainment's cards and pages
    (public/hmi/luxeed-rx/car34.webp): the studio rig on the car alone, front
    three-quarter, the floor lights it but is not drawn, transparent. Fresh build, exterior only:

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_rx; export_rx.hmi_art()"
    """
    import os
    sys.modules.pop("build_rx", None)
    import build_rx
    from carkit import rig, studio
    build_rx.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    rig.build_studio()
    # the floor lights the car's lower body but is not in the picture
    bpy.data.objects["StudioFloor"].visible_camera = False
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    png = rig.still("card", os.path.join(rig.RENDER_DIR, "luxeed-rx_card.png"), dims=DIMS, res=res,
                    samples=samples, transparent=True)
    out = os.path.normpath(os.path.join(MODELS, "..", "hmi", "luxeed-rx", "car34.webp"))
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    top = rig.top_view(os.path.join(rig.RENDER_DIR, "luxeed-rx_top.png"), dims=DIMS, samples=samples)
    studio.to_webp(top, os.path.join(os.path.dirname(out), "car-top.webp"), quality=88, trim=True, width=420)
    return out


def hmi_cabin(res=(1500, 940), samples=160, shots=("climate", "seats")):
    """Clay renders of the cabin for the infotainment's climate and seat pages
    (public/hmi/luxeed-rx/cabin-<shot>-<light|dark>.webp): every surface one
    matte colour under a uniform white sky, the centre screen black, on a
    transparent ground, so the picture is all form, as the car's own are. Cabin only, no exterior:

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_rx; export_rx.hmi_cabin()"
    """
    import math
    import os
    from mathutils import Vector
    from carkit import rig, scene as SC, studio
    bpy.ops.wm.read_homefile(use_empty=True)
    import rx_interior as RI
    RI.main(lights=False)
    scn = bpy.context.scene
    objs = [o for o in bpy.data.collections["RX_Interior"].all_objects if o.type == 'MESH']

    def flat(name, rgb, rough=0.9):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = rgb + (1.0,)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = 0.0
        return m, b

    clay, clay_bsdf = flat("M_Clay", (0.8, 0.8, 0.8))
    black, _ = flat("M_ScreenBlack", (0.004, 0.004, 0.005), 0.25)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(black if o.name.startswith("screen_") else clay)

    w = bpy.data.worlds.new("W_Clay")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')

    # (position, aim, focal length mm), the car's axes (x forward, y left, z up)
    CAMS = {
        "climate": ((-1.05, 0.0, 1.52), (1.10, 0.0, 0.70), 17.0),
        "seats": ((-1.45, -0.55, 1.78), (0.25, 0.22, 0.52), 19.0),
    }
    # the roof, the pillars and the passenger-side doors are out of the picture
    for o in objs:
        n = o.name.lower()
        if any(k in n for k in ("headliner", "pillar", "roof", "int_door_r", "int_rdoor_r", "qtr_lower", "parcel")):
            o.hide_render = True
        # anything wholly above the seats: the header trims, the visors, the mirror
        elif min((o.matrix_world @ Vector(c)).z for c in o.bound_box) > 1.22:
            o.hide_render = True
    out = []
    for tone, albedo, sky in (("light", 0.80, 1.05), ("dark", 0.040, 2.4)):
        clay_bsdf.inputs["Base Color"].default_value = (albedo, albedo, albedo * 1.02, 1.0)
        bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bg.inputs["Strength"].default_value = sky
        for name in shots:
            pos, aim, lens = CAMS[name]
            cd = bpy.data.cameras.new("CAM_" + name)
            cd.lens = lens
            cd.clip_start = 0.02
            cam = bpy.data.objects.new("CAM_" + name, cd)
            scn.collection.objects.link(cam)
            cam.location = Vector(pos)
            cam.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
            scn.camera = cam
            scn.render.resolution_x, scn.render.resolution_y = res
            scn.render.resolution_percentage = 100
            SC.use_cycles(samples)
            scn.view_settings.view_transform = 'Standard'
            # the sky lights the cabin but is not in the picture: the page behind it shows
            scn.render.film_transparent = True
            scn.render.image_settings.file_format = 'PNG'
            scn.render.image_settings.color_mode = 'RGBA'
            png = os.path.join(rig.RENDER_DIR, "luxeed-rx_cabin_%s_%s.png" % (name, tone))
            os.makedirs(rig.RENDER_DIR, exist_ok=True)
            scn.render.filepath = png
            bpy.ops.render.render(write_still=True)
            webp = os.path.normpath(os.path.join(MODELS, "..", "hmi", "luxeed-rx", "cabin-%s-%s.webp" % (name, tone)))
            studio.to_webp(png, webp, quality=80, width=res[0])
            out.append(webp)
            bpy.data.objects.remove(cam, do_unlink=True)
    return out


def main(draco=True, ao=True, ao_samples=512, shadow=True):
    """The exterior (the scene must hold a fresh build_rx.main())."""
    prepare_exterior()
    open_all(False)           # every part at its hinge, as the closed car
    if ao:
        bake_exterior_ao(ao_samples)
    split_wheels()            # one node per corner, after the per-design AO bake
    groups = exterior_groups()
    _X.merge_for_export(groups)
    if shadow:
        bake_ground_shadow()
    return _X.export(DEST, groups, "LuxeedRX_Body", draco=draco, attributes=ao)


def web(draco=True):
    """Fresh build -> merged exterior GLB."""
    sys.modules.pop("build_rx", None)
    import build_rx
    out = build_rx.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"])
    return main(draco=draco)


# ------------------------------------------------------------------ cabin
def hinge():
    """The front doors' hinge axis: the leading edge at mid height, on the skin."""
    import rx_panels as PN
    import rx_surface as S
    from carkit.interior import cabin as CB
    x = PN._DOOR_F_EDGE(0.60)
    return (x, CB.section_y_at(S.BODY, x, 0.60), 0.60)


def cabin_lighting():
    """The OUTSIDE world, the cabin rig at RIG_FILL, the generated cluster on
    its display, and the blackout layer and lookdev floor hidden so daylight
    comes in through the glass. Wrap bakes in carkit.bake.thin_glass()."""
    import rx_interior as RI
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    SC.hdri_world(**OUTSIDE)
    col = bpy.data.collections.get("RX_Interior")
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * RIG_FILL
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, RI.cluster_image(), 1.2)
    hidden = []
    for n in BLACKOUT + ("LuxeedRX_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def join_doors(collection="RX_Interior"):
    """Each door card's parts (front and rear) -> one object, origin on the
    hinge (rx_openings)."""
    import rx_openings as OP
    OP.join_cards(collection)


def bake_cabin(samples=256, probe_samples=384):
    """Vertex lighting on every cabin mesh + the reflection probe."""
    from carkit import bake as BK
    col = bpy.data.collections["RX_Interior"]
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col)
            stats = BK.vertex_lighting(objs, samples=samples)
            BK.smooth(objs)
            BK.to_generic(objs)
            lights = [o for o in col.objects if o.type == 'LIGHT' and o.visible_glossy]
            BK.probe_mix(PROBE_AT, DEST_PROBE, lights, mix=PROBE_LIGHT_MIX,
                         samples=probe_samples)
    finally:
        for ob in hidden:
            ob.hide_render = False
    return stats


def bake_cabin_open(samples=256):
    """The same vertex lighting with every door and the tailgate open: the
    second set of light the viewer blends in as a part swings open (the
    cabin is lit by the doorways, the boot by the sky). Needs
    prepare_exterior() first, so the parts are split and hinged."""
    from carkit import bake as BK
    import rx_openings as OP
    import rx_gate as RG
    col = bpy.data.collections["RX_Interior"]
    OP.join_cards()
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"])
    RG.set_hatch(RG.OPEN_DEG)
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
        RG.set_hatch(0.0)
    return stats


def export_outside():
    """The view out (JPEG, tone mapped as the viewer does) and its light (HDR)."""
    from carkit import bake as BK
    o = OUTSIDE
    view = BK.backdrop(o["path"], DEST_OUTSIDE, rotation=o["rotation"],
                       strength=o["strength"], exposure=WEB_EXPOSURE)
    light = BK.backdrop_light(o["path"], DEST_OUTSIDE_LIGHT, rotation=o["rotation"],
                              strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def export_interior(draco=True):
    from carkit import build as B
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections["RX_Interior"]
    # the app draws the live HMI over screen_main: ship the plain screen
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if m.name.startswith("INT_")
        and m.name != "INT_Screen" and not m.name.startswith("INT_Display")))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    join_doors()
    _X.merge_for_export(INTERIOR_GROUPS, PROTECTED)
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "LuxeedRX_Cabin", draco=draco,
                     attributes=True)


def web_full(samples=256, probe_samples=384, draco=True):
    """Fresh build of body and cabin -> baked cabin -> both GLBs, the probe
    and the outside world. In a background Blender (module docstring)."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("rx_") or m == "build_rx"]:
        sys.modules.pop(m, None)
    import build_rx
    out = build_rx.main(reset=True, scene=True)
    build_wheel_options(out["lib"])
    import rx_interior as RI
    RI.main()
    import rx_gate as RG
    RG.build_boot()           # the boot behind the hatch, and the hatch's liner
    RG.build_boot_details()
    RG.build_liner()
    print("build: %d exterior tris, %.0f s" % (out["tris"], time.time() - t))
    stats = bake_cabin(samples, probe_samples)
    print("bake: %.0f s" % (time.time() - t))
    prepare_exterior()
    stats_open = bake_cabin_open(samples)
    print("bake open: %.0f s" % (time.time() - t))
    res = {"bake": stats, "bake_open": stats_open, "interior": export_interior(draco=draco)}
    res["exterior"] = main(draco=draco)
    res["outside"] = export_outside()
    print("web_full: %.0f s" % (time.time() - t))
    return res


if __name__ == "__main__":
    web()
