"""Merge for the draw-call budget, then export to glTF 2.0 (GLB, Draco).

Every glTF primitive is a draw call, and a merged object still emits one
primitive per material slot - so joining costs nothing visually and buys back
all the per-object overhead. A parametric build makes ~150 objects; this
collapses them to a handful (the SU7: 7 nodes, ~40 draw calls).

Objects the web app addresses by name stay separate (`protected`): the HMI
screen quad, animated door cards. Everything else is found by MATERIAL name.

    groups = [(joined_name, collection_name), ...]
    export_car(groups, dest, protected=("screen_main",), draco=True)

Run materials.export_safe() first: transmission blanks the three.js frame.
"""
import os

import bpy


def bake_modifiers(ob):
    """Collapse an object's modifier stack into its mesh data.

    Must happen BEFORE any join: object.join keeps only the active object's
    stack and throws the others away, so the first member's Mirror/Solidify
    would be applied to the whole merged mesh (the SU7 came out 18 m tall).
    """
    if not ob.modifiers:
        return ob
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = baked
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def join(name, member_names):
    """Join the named objects into one called `name`.

    Takes names, not references: join deletes the merged-away objects and a
    held reference becomes a removed StructRNA. Uses an explicit context
    override - driven from outside the UI (the MCP runs code from a timer)
    there is no 3D viewport and join's poll fails on an empty context.
    """
    members = [bpy.data.objects[n] for n in member_names
               if n in bpy.data.objects and bpy.data.objects[n].type == 'MESH']
    if not members:
        return None
    for o in members:
        bake_modifiers(o)
    if len(members) == 1:
        members[0].name = name
        return members[0]
    target = members[0]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in members:
        o.select_set(True)
    bpy.context.view_layer.objects.active = target
    with bpy.context.temp_override(active_object=target, object=target,
                                   selected_objects=members,
                                   selected_editable_objects=members):
        bpy.ops.object.join()
    target.name = name
    return target


def merge_for_export(groups, protected=()):
    """Join each collection into one object; report objects, slots, tris."""
    protected = set(protected)
    before = 0
    for _, cname in groups:
        col = bpy.data.collections.get(cname)
        if col:
            before += len([o for o in col.objects if o.type == 'MESH'])

    for name, cname in groups:
        col = bpy.data.collections.get(cname)
        if not col:
            continue
        names = [o.name for o in col.objects
                 if o.type == 'MESH' and o.name not in protected]
        join(name, names)
    for n in protected:
        if n in bpy.data.objects:
            bake_modifiers(bpy.data.objects[n])

    after, prims = [], 0
    for _, cname in groups:
        col = bpy.data.collections.get(cname)
        if not col:
            continue
        for o in col.objects:
            if o.type != 'MESH':
                continue
            after.append(o)
            prims += max(1, len(o.data.materials))

    print("objects %d -> %d" % (before, len(after)))
    for o in sorted(after, key=lambda x: x.name):
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        mult = 2 if any(m.type == 'MIRROR' for m in o.modifiers) else 1
        print("  %-22s %2d slot(s)  %7d tris" %
              (o.name, max(1, len(o.data.materials)), tris * mult))
    # Tangents cannot be computed on n-gons, and triangulating here means what
    # ships is exactly what was measured.
    for o in after:
        o.data.name = o.name + "_mesh"
        if not any(m.type == 'TRIANGULATE' for m in o.modifiers):
            t = o.modifiers.new("Triangulate", 'TRIANGULATE')
            t.quad_method = 'SHORTEST_DIAGONAL'
            t.keep_custom_normals = True
    print("glTF primitives (~ draw calls): %d" % prims)
    return after


# the custom "_NAME" attributes that ship (the baked light and occlusion); the
# build's own working attributes (panels' "_butt" marks) are not for the viewer
SHIPPED_ATTRIBUTES = ("_BAKEDLIGHT", "_BAKEDLIGHT_OPEN", "_BAKEDAO")


def weld_normals(objects, box, tol=0.008, min_dot=0.35):
    """Give the surfaces that meet along a seam between two objects one shared normal there.

    Panels built apart (the G9L's tail cap and its quarter panel) shade each side of their join with their own normals, so
    a corner that turns 30 degrees reads as a crease that breaks every reflection. Here every corner of every object's mesh
    inside `box` ((x0, x1), (y0, y1), (z0, z1) in the world frame; the y range is tested on |y|) that has a corner of
    ANOTHER object within `tol` metres, facing about the same way (dot > min_dot: the far side of a thin shell, and its
    rim, do not), takes the average of them. Corner normals are replaced as custom normals; nothing moves.
    Returns the number of corners changed."""
    import numpy as np
    from mathutils import kdtree

    (x0, x1), (y0, y1), (z0, z1) = box
    rows = []                                   # (object index, loop index, world position, world normal)
    infos = []
    for oi, ob in enumerate(objects):
        me = ob.data
        nl = len(me.loops)
        if not nl:
            infos.append(None)
            continue
        vi = np.empty(nl, dtype=np.int32)
        me.loops.foreach_get("vertex_index", vi)
        co = np.empty(len(me.vertices) * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        mw = np.array(ob.matrix_world)
        world = co @ mw[:3, :3].T + mw[:3, 3]
        nr = np.empty(nl * 3, dtype=np.float32)
        me.corner_normals.foreach_get("vector", nr)
        nr = nr.reshape(-1, 3).astype(np.float64)
        nw = nr @ mw[:3, :3].T
        nw /= np.maximum(np.linalg.norm(nw, axis=1, keepdims=True), 1e-12)
        pos = world[vi]
        inside = ((pos[:, 0] >= x0) & (pos[:, 0] <= x1) & (np.abs(pos[:, 1]) >= y0) & (np.abs(pos[:, 1]) <= y1)
                  & (pos[:, 2] >= z0) & (pos[:, 2] <= z1))
        infos.append((nr, mw, nw))
        for li in np.nonzero(inside)[0]:
            rows.append((oi, int(li), pos[li], nw[li]))
    if not rows:
        return 0
    tree = kdtree.KDTree(len(rows))
    for i, r in enumerate(rows):
        tree.insert(tuple(r[2]), i)
    tree.balance()
    new = {}
    for i, (oi, li, p, n) in enumerate(rows):
        acc, other = n.copy(), False
        for (_, j, d) in tree.find_range(tuple(p), tol):
            rj = rows[j]
            if j == i or rj[0] == oi or float(np.dot(rj[3], n)) <= min_dot:
                continue
            acc += rj[3]
            other = True
        if other:
            new.setdefault(oi, {})[li] = acc / np.linalg.norm(acc)
    changed = 0
    for oi, per_loop in new.items():
        ob = objects[oi]
        me = ob.data
        nr, mw, nw = infos[oi]
        out = nr.copy()                          # local-space normals as they are now
        inv = np.linalg.inv(mw[:3, :3]).T        # world normal -> local
        for li, n in per_loop.items():
            v = inv @ n
            out[li] = v / np.linalg.norm(v)
        me.normals_split_custom_set([tuple(v) for v in out])
        changed += len(per_loop)
    return changed


def strip_attributes(objects, keep=SHIPPED_ATTRIBUTES):
    """Drop every "_"-prefixed attribute that is not in `keep`: the glTF
    exporter ships them all, at 4 bytes a vertex a piece."""
    for o in objects:
        if o.type != 'MESH':
            continue
        for a in [a for a in o.data.attributes if a.name.startswith("_") and a.name not in keep]:
            o.data.attributes.remove(a)


def export(path, groups, active_name, draco=None, draco_level=6, vertex_color=None,
           attributes=False, image_format='AUTO'):
    """Export the groups' meshes as GLB. draco=None: only if over 20 MB.
    vertex_color: a colour attribute to ship as COLOR_0 (first primitive only
    in Blender 5.2 - see carkit.bake.EXPORT_ATTR); attributes: ship custom
    "_NAME" attributes (SHIPPED_ATTRIBUTES: the baked light and occlusion);
    image_format: 'AUTO' keeps each texture's own format, 'WEBP' re-encodes them all (the cabin's
    occlusion atlas is a 2048 x 2048 picture)."""
    bpy.ops.object.select_all(action='DESELECT')
    n = 0
    for _, cname in groups:
        col = bpy.data.collections.get(cname)
        if not col:
            continue
        for o in col.objects:
            if o.type != 'MESH':
                continue
            o.hide_render = False
            o.hide_set(False)
            o.select_set(True)
            if attributes:
                strip_attributes([o])
            n += 1
    if n == 0:
        raise RuntimeError("nothing selected to export")
    active = bpy.data.objects[active_name]
    bpy.context.view_layer.objects.active = active

    os.makedirs(os.path.dirname(path), exist_ok=True)
    kwargs = dict(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,           # bake mirror / solidify / bevel / boolean
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_tangents=True,
        export_normals=True,
        export_extras=False,
        export_image_format=image_format,
    )
    if vertex_color:
        kwargs.update(export_vertex_color='NAME', export_vertex_color_name=vertex_color,
                      export_all_vertex_colors=False)
    else:
        kwargs.update(export_vertex_color='NONE')
    if attributes:
        kwargs.update(export_attributes=True)
    sel = [o for o in bpy.context.view_layer.objects if o.select_get()]

    def _run(**kw):
        # the exporter reads context.active_object, which does not exist when
        # the build is driven from outside the UI
        win = bpy.context.window or (bpy.context.window_manager.windows[0] if len(bpy.context.window_manager.windows) else None)
        override = dict(active_object=active, object=active,
                        selected_objects=sel,
                        selected_editable_objects=sel)
        if win:
            override["window"] = win
        with bpy.context.temp_override(**override):
            bpy.ops.export_scene.gltf(**kw)

    _run(**kwargs)
    size = os.path.getsize(path)
    if draco is None:
        draco = size > 20 * 1024 * 1024
    if draco:
        kwargs["export_draco_mesh_compression_enable"] = True
        kwargs["export_draco_mesh_compression_level"] = draco_level
        # baked lighting lives in COLOR_0: at the default 10 bits the dark
        # footwell values (~0.004 stored) band visibly
        kwargs["export_draco_color_quantization"] = 14
        kwargs["export_draco_generic_quantization"] = 14
        _run(**kwargs)
        size = os.path.getsize(path)
    print("exported: %s  %.2f MB  draco=%s" % (path, size / 1048576.0, draco))
    check_paint(path)
    return path, size, draco


def glb_json(path):
    """The JSON chunk of a GLB (materials, nodes, extensions)."""
    import json
    import struct
    with open(path, "rb") as f:
        head = f.read(20)
        n = struct.unpack_from("<I", head, 12)[0]
        return json.loads(f.read(n))


def check_paint(path):
    """Paint must ship as a dielectric. A metallicFactor the exporter left out
    (a procedural Metallic input) reads as 1.0 in glTF: the RX's flaked paint
    came out solid dark metal in three.js. materials.export_safe() fixes it."""
    bad = []
    for m in glb_json(path).get("materials", []):
        if m.get("name", "").startswith("M_Paint"):
            if m.get("pbrMetallicRoughness", {}).get("metallicFactor", 1.0) > 0.2:
                bad.append(m["name"])
    if bad:
        raise RuntimeError("paint exported as metal (run materials.export_safe first): %s" % bad)


def export_car(groups, dest, protected=(), draco=None):
    """merge_for_export + export, the first group's object as the active one."""
    merge_for_export(groups, protected)
    return export(dest, groups, groups[0][0], draco=draco)
