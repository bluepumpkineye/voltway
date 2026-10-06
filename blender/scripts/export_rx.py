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
    LuxeedRX_Wheels          the four wheels
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

# joined name -> collection
GROUPS = [
    ("LuxeedRX_Body", "RX_Body"),
    ("LuxeedRX_Wheels", "RX_Wheels"),
    ("LuxeedRX_Details", "RX_Details"),
    ("LuxeedRX_Blackout", "RX_Blackout"),
]


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


def main(draco=True):
    """The exterior (the scene must hold a fresh build_rx.main())."""
    prepare_exterior()
    import rx_openings as OP
    import rx_bays as BY
    import rx_gate as RG
    groups = GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP, RG.GREENHOUSE_GROUP]
    _X.merge_for_export(groups)
    return _X.export(DEST, groups, "LuxeedRX_Body", draco=draco)


def web(draco=True):
    """Fresh build -> merged exterior GLB."""
    sys.modules.pop("build_rx", None)
    import build_rx
    out = build_rx.main(reset=True, scene=False)
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
