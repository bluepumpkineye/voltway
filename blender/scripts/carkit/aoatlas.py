"""A cabin's ambient occlusion as one texture, not a colour per vertex.

HIMA lights a cabin with a soft hall environment and shades it with ONE 2048 x 2048 occlusion atlas on a second UV set
(docs/hima-benchmark.md, "The cabin"). Per texel it shows what a per-vertex bake cannot: the dark line where a seat
meets its trim, a shut line, the crease under a visor. This module makes that atlas for any cabin:

    objs = aoatlas.cabin_objects(collection)        # the cabin's meshes, modifiers applied
    aoatlas.unwrap(objs)                            # a second UV set, smart-projected, packed in one square
    img = aoatlas.bake(objs, path, hide=exterior)   # Cycles AO into a 2048 x 2048 image, saved as PNG
    aoatlas.attach(objs, img)                       # the glTF exporter ships it as every material's occlusionTexture

The viewer reads it as `aoMap` on the second UV set (TEXCOORD_1) and multiplies the hall environment's diffuse and
specular light by it (CarModel.tsx). UV 0 is untouched: it is the world-space projection the leather and carbon use.
"""
import math

import bpy
import numpy as np

UV_NAME = "UV_AO"
IMAGE = "AO_Atlas"
GROUP = "glTF Material Output"


def cabin_objects(collection):
    """The collection's meshes with their modifiers applied, ready to unwrap."""
    from .export import bake_modifiers
    col = bpy.data.collections[collection] if isinstance(collection, str) else collection
    objs = [o for o in col.objects if o.type == 'MESH' and len(o.data.polygons)]
    for o in objs:
        bake_modifiers(o)
    return objs


def unwrap(objs, margin=0.003, angle=66.0, name=UV_NAME):
    """A second UV set on every object: smart-projected islands, all packed into one 0-1 square.

    One multi-object edit session, so the packer sees every island of every object at once and they share the
    atlas without overlap. UV 0 stays the first layer."""
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        me = o.data
        layer = me.uv_layers.get(name) or me.uv_layers.new(name=name)
        me.uv_layers.active = layer
        o.hide_set(False)
        o.select_set(True)
    active = objs[0]
    bpy.context.view_layer.objects.active = active
    with bpy.context.temp_override(active_object=active, object=active, selected_objects=objs,
                                   selected_editable_objects=objs, objects_in_mode=objs):
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin,
                                     area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, margin_method='SCALED',
                                    margin=margin)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
    n_islands = 0
    cover = 0.0
    for o in objs:
        uv = o.data.uv_layers[name]
        co = np.empty(len(uv.data) * 2, np.float32)
        uv.data.foreach_get("uv", co)
        co = co.reshape(-1, 2)
        n_islands += 1
        cover = max(cover, float(co.max()))
    print("aoatlas: unwrapped %d objects, uv max %.3f" % (len(objs), cover))
    return objs


def _bake_targets(objs, image):
    """An active, unlinked image node in every material the objects use (what Cycles bakes into)."""
    made = []
    mats = {s.material for o in objs for s in o.material_slots if s.material}
    for m in mats:
        if not m.use_nodes:
            m.use_nodes = True
        nt = m.node_tree
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = image
        n.select = True
        nt.nodes.active = n
        made.append((nt, n))
    return made


def bake(objs, path, size=2048, samples=512, distance=(0.25, 1.1), mix=0.40, hide=(), margin=8, name=UV_NAME,
         dilate=24):
    """Cycles ambient occlusion of the cabin into a size x size image, saved to `path` (PNG).

    The cabin's own geometry is the only occluder (`hide`: every other object, the exterior shell and glass, so the
    windscreen is an opening and the dash top is lit by the sky it would see). `distance` is how far a surface looks
    for shade, metres: one value, or two - a short one for the creases and seams and a long one for the footwell and the
    shade under the dash. The two are multiplied, the long one only by `mix` (1 = as strong as the short one).

    The texels no island covers are NOT left black: a leather panel is a strip a few texels wide, and the viewer's mip
    levels average its edge with whatever lies beside it, so a black background showed as dark stains on the seats.
    The baked texels are grown outward `dilate` texels (the mean of their covered neighbours) and the rest is white."""
    if isinstance(distance, (int, float)):
        near, cov = _bake_once(objs, size, samples, float(distance), hide, margin, name)
        ao = near
    else:
        near, cov = _bake_once(objs, size, samples, float(distance[0]), hide, margin, name)
        far, cov_far = _bake_once(objs, size, samples, float(distance[1]), hide, margin, name)
        ao = near * (1.0 - mix + mix * far)
        cov = cov | cov_far
    ao, grown = _dilate(ao.reshape(size, size), cov.reshape(size, size), dilate)
    ao = np.where(grown, ao, 1.0).astype(np.float32).ravel()
    covered = cov.ravel()
    g = ao
    img = bpy.data.images.get(IMAGE)
    px = np.ones((size * size, 4), np.float32)
    px[:, :3] = ao.reshape(-1, 1)
    img.pixels.foreach_set(px.ravel())
    print("aoatlas: baked %dx%d, covered %.0f%%  mean %.3f  p5 %.3f  p50 %.3f" % (
        size, size, 100.0 * covered.mean(), float(g[covered].mean()), float(np.percentile(g[covered], 5)),
        float(np.percentile(g[covered], 50))))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return img


def _dilate(a, cov, iters):
    """Grow the covered texels of `a` outward by `iters` texels (the mean of the covered neighbours)."""
    a = a.copy()
    cov = cov.copy()
    for _ in range(iters):
        if cov.all():
            break
        tot = np.zeros_like(a)
        cnt = np.zeros(a.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                sc = np.roll(cov, (dy, dx), (0, 1))
                tot += np.where(sc, np.roll(a, (dy, dx), (0, 1)), 0.0)
                cnt += sc
        grow = (~cov) & (cnt > 0)
        a[grow] = tot[grow] / cnt[grow]
        cov |= grow
    return a, cov


def _bake_once(objs, size, samples, distance, hide, margin, name):
    """One Cycles AO bake of the cabin at `distance`; returns the size x size red channel as float and a mask of the texels
    the bake wrote (its alpha; the texels beyond the islands' margins stay clear)."""
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    try:
        from . import scene as SC
        SC.use_cycles(samples=samples, denoise=False)
    except Exception as e:
        print("aoatlas: cycles setup:", e)
    scn.cycles.samples = samples
    world = scn.world
    made_world = None
    if world is None:
        made_world = world = bpy.data.worlds.new("W_AO")
        scn.world = world
    prev = world.light_settings.distance
    world.light_settings.distance = distance

    img = bpy.data.images.get(IMAGE)
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(IMAGE, size, size, alpha=True, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color'
    img.generated_color = (0.0, 0.0, 0.0, 0.0)

    hidden = []
    for o in hide:
        if not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    targets = _bake_targets(objs, img)
    try:
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for o in objs:
            o.hide_set(False)
            o.select_set(True)
            o.data.uv_layers.active = o.data.uv_layers[name]
        active = objs[0]
        bpy.context.view_layer.objects.active = active
        with bpy.context.temp_override(active_object=active, object=active, selected_objects=objs,
                                       selected_editable_objects=objs):
            bpy.ops.object.bake(type='AO', target='IMAGE_TEXTURES', margin=margin, margin_type='EXTEND',
                                use_clear=True)
    finally:
        for nt, n in targets:
            nt.nodes.remove(n)
        for o in hidden:
            o.hide_render = False
        world.light_settings.distance = prev
        if made_world is not None:
            scn.world = None
            bpy.data.worlds.remove(made_world)
    px = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    ao = px[:, :3].mean(axis=1)
    cov = px[:, 3] > 0.5
    if cov.all() or not cov.any():          # a bake that wrote no alpha: fall back to "not black"
        cov = ao > 0.004
    return ao, cov


def attach(objs, image, name=UV_NAME):
    """Wire `image` (its red channel) into every material of `objs` as the glTF occlusion, through the exporter's
    "glTF Material Output" group, read off UV layer `name`. The exporter then ships one occlusionTexture on
    TEXCOORD_1."""
    grp = bpy.data.node_groups.get(GROUP)
    if grp is None:
        grp = bpy.data.node_groups.new(GROUP, 'ShaderNodeTree')
        grp.interface.new_socket("Occlusion", socket_type='NodeSocketFloat', in_out='INPUT')
    mats = {s.material for o in objs for s in o.material_slots if s.material}
    for m in mats:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        for n in [n for n in nt.nodes if n.get("ao_atlas")]:
            nt.nodes.remove(n)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = image
        tex["ao_atlas"] = True
        tex.interpolation = 'Linear'
        uvn = nt.nodes.new('ShaderNodeUVMap')
        uvn.uv_map = name
        uvn["ao_atlas"] = True
        gn = nt.nodes.new('ShaderNodeGroup')
        gn.node_tree = grp
        gn["ao_atlas"] = True
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], gn.inputs["Occlusion"])
    print("aoatlas: occlusion attached to %d materials" % len(mats))
    return mats


def atlas_for(collection, samples=512, path=None):
    """The whole recipe for one car's cabin collection, run on its merged export meshes: unwrap, bake (everything outside
    the collection hidden), attach. Returns the image. A car's `export_interior(look="hall")` calls this once, after
    merge_for_export and before the glTF export, which must then be given `image_format='WEBP'`."""
    import os
    import tempfile
    col = bpy.data.collections[collection] if isinstance(collection, str) else collection
    objs = cabin_objects(col)
    unwrap(objs)
    inside = set(col.objects)
    outside = [o for o in bpy.data.objects if o not in inside and o.type in ('MESH', 'CURVE', 'SURFACE', 'FONT')]
    img = bake(objs, path or os.path.join(tempfile.gettempdir(), "cabin_ao_atlas.png"), samples=samples, hide=outside)
    attach(objs, img)
    return img
