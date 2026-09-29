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


def export(path, groups, active_name, draco=None, draco_level=6, vertex_color=None,
           attributes=False):
    """Export the groups' meshes as GLB. draco=None: only if over 20 MB.
    vertex_color: a colour attribute to ship as COLOR_0 (first primitive only
    in Blender 5.2 - see carkit.bake.EXPORT_ATTR); attributes: ship custom
    "_NAME" attributes (the baked lighting)."""
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
        export_image_format='AUTO',
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
        with bpy.context.temp_override(active_object=active, object=active,
                                       selected_objects=sel,
                                       selected_editable_objects=sel):
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
