"""Assemble a car's anatomy, write the explode plan into the nodes and export the GLB.

    import carkit.anatomy.build as B
    B.build(spec)                         # into the XR_ANATOMY collection
    B.export_glb(path)                    # Draco GLB, node extras on

Each node's `xr` extra (JSON) holds what the viewer needs: `sys` (battery, drive, chassis,
suspension, steering), `id`, and the exploded-view plan `ex` = offset in glTF axes (metres,
relative to the node's PARENT, so a group's offset carries its parts), `t0`/`t1` = the part of
the explode phase (0..1) it flies in. The plan scales with the car's wheelbase, so another car
spreads out in proportion. `kin` (a corner group) and `aim` (an aimed link) carry the linkage's
hardpoints for the live suspension solver; `ports` are the HV connectors the cables join.
"""
import json
import os

import bpy
from mathutils import Vector

from . import battery, frames, materials, motor, suspension
from .prim import collection, group, to_gltf, tri_count

CORNERS = ("FL", "FR", "RL", "RR")


def _clear(col):
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)


def build(spec, clean=True):
    col = collection("XR_ANATOMY")
    if clean:
        _clear(col)
    M = materials.library()
    root = group("XR_Anatomy", col, (0, 0, 0), None, car=spec.name, kwh=spec.kwh)
    parts = {"root": root}
    parts["battery"] = battery.build(spec, col, root, M)
    parts["units"] = {m.id: motor.build(spec, m, col, root, M) for m in spec.motors}
    parts["frames"] = frames.build(spec, col, root, M)
    parts["corners"] = {}
    for c in CORNERS:
        k = suspension.corner(spec, c, col, root, M)
        parts["corners"][c] = k
        frames.tower(spec, c, col, k["group"], M)
    # half-shafts: each drive unit's output (the front unit has one on each side)
    parts["shafts"] = {}
    for m in spec.motors:
        u = parts["units"][m.id]
        if m.side is None:
            # one motor across the axle: a half-shaft out of each side of it
            pre = "F" if m.axle == "front" else "R"
            hx, _, hz = spec.hub_f if m.axle == "front" else spec.hub_r
            parts["shafts"][pre + "L"] = suspension.halfshaft(spec, pre + "L", u["output"], col, root, M)
            right = u.get("output_r", (hx, -(u["sizes"]["Ls"] / 2 + 0.067), hz))
            parts["shafts"][pre + "R"] = suspension.halfshaft(spec, pre + "R", right, col, root, M)
        else:
            c = "RL" if m.side == "left" else "RR"
            parts["shafts"][c] = suspension.halfshaft(spec, c, u["output"], col, root, M)
    parts["arb_f"] = suspension.anti_roll_bar(spec, "front", col, root, M)
    parts["arb_r"] = suspension.anti_roll_bar(spec, "rear", col, root, M)
    parts["rack"] = suspension.steering_rack(spec, col, root, M)
    if getattr(spec, "rear_steer", False):
        parts["rear_rack"] = suspension.rear_steering_rack(spec, col, root, M)
    _ports(spec, parts)
    plan = explode_plan(spec, parts)
    apply_plan(plan)
    print("anatomy: %d objects, %d tris" % (len(col.objects), tri_count(col.objects)))
    return parts


def _ports(spec, parts):
    """Where the HV harness joins, in each owner's local frame (glTF axes): the web draws the cables."""
    owner = {}
    b = parts["battery"]
    for k, nm in (("pdu_l", "pdu"), ("pdu_r", "pdu"), ("rear_l", "rear_port"), ("rear_r", "rear_port")):
        owner[k] = (b[nm], b["ports"][k])
    for m in spec.motors:
        u = parts["units"][m.id]
        owner["inv_" + m.id] = (u["inverter"], u["hv_port"])
    for name, (ob, p) in owner.items():
        d = json.loads(ob["ports"]) if "ports" in ob else {}
        loc = Vector(p) - _wloc(ob)
        d[name] = to_gltf(loc)
        ob["ports"] = json.dumps(d, separators=(",", ":"))


def _wloc(ob):
    s = Vector((0, 0, 0))
    while ob is not None:
        s += ob.location
        ob = ob.parent
    return s


# ----------------------------------------------------------------- explode plan
def explode_plan(spec, parts):
    """name -> (offset in Blender axes relative to the parent, t0, t1). Scales with the wheelbase."""
    k = spec.wheelbase / 3.0
    P = {}

    def put(ob, dx, dy, dz, t0, t1):
        P[ob.name] = ((dx, dy, dz), t0, t1)

    b = parts["battery"]
    put(b["group"], 0, 0, -0.34, 0.20, 0.70)
    put(b["tray"], 0, 0, 0.0, 0.3, 0.8)
    put(b["plate"], 0, 0, 0.075, 0.34, 0.82)
    for i, c in enumerate(b["cells"]):
        put(c, 0, 0, 0.17 + 0.0 * i, 0.38 + 0.01 * i, 0.86)
    put(b["bus"], 0, 0, 0.25, 0.42, 0.88)
    put(b["film"], 0, 0, 0.31, 0.46, 0.9)
    put(b["lid"], 0, 0, 0.42, 0.5, 0.95)
    put(b["pdu"], 0.42 * k, 0, 0.03, 0.4, 0.9)
    put(b["rear_port"], -0.42 * k, 0, 0.0, 0.4, 0.9)

    for m in spec.motors:
        u = parts["units"][m.id]
        ax = Vector(u["ax"])
        front = m.axle == "front"
        put(u["group"], (0.85 if front else -0.80) * k, 0, 0.30, 0.30, 0.85)
        o = lambda a: tuple(ax * a)
        put(u["casing"], *o(-0.34), 0.5, 0.95)
        put(u["stator"], 0, 0, 0, 0.5, 0.95)
        put(u["rotor"], *o(0.24), 0.55, 0.98)
        put(u["reducer"], *o(0.50), 0.55, 0.98)
        put(u["gears"], *o(0.56), 0.6, 1.0)
        put(u["pinion"], *o(0.5), 0.58, 1.0)
        put(u["inverter"], 0, 0, 0.30, 0.45, 0.92)

    f = parts["frames"]
    put(f["floor"], 0, 0, 0.30, 0.25, 0.75)
    put(f["sub_f"], 0.50 * k, 0, -0.08, 0.35, 0.85)
    put(f["crash_f"], 0.95 * k, 0, 0.0, 0.4, 0.9)
    put(f["sub_r"], -0.50 * k, 0, -0.08, 0.35, 0.85)
    put(f["crash_r"], -0.95 * k, 0, 0.0, 0.4, 0.9)
    put(parts["rack"], 0.42 * k, 0, 0.13, 0.45, 0.9)
    if "rear_rack" in parts:
        put(parts["rear_rack"], -0.42 * k, 0, 0.10, 0.45, 0.9)
    put(parts["arb_f"], -0.30 * k, 0, -0.07, 0.45, 0.9)
    put(parts["arb_r"], -0.62 * k, 0, -0.06, 0.45, 0.9)

    for c, kk in parts["corners"].items():
        s = kk["hp"]["s"]
        front = kk["hp"]["front"]
        put(kk["group"], (0.14 if front else -0.14) * k, s * 0.60, 0.04, 0.35, 0.85)
        put(kk["spring"], 0, 0, 0.20, 0.5, 0.95)
        put(kk["damper"], 0, 0, 0.30, 0.5, 0.95)
        put(kk["rod"], 0, 0, 0.0, 0.5, 0.95)
        put(kk["upper"], 0, 0, 0.12, 0.55, 0.95)
        put(kk["lower"], 0, 0, -0.02, 0.55, 0.95)
        put(kk["tie"], 0, 0, -0.04, 0.55, 0.95)
        put(kk["knuckle"], 0, s * 0.10, 0.0, 0.55, 0.95)
    for c, ob in parts["shafts"].items():
        s = 1 if c[1] == "L" else -1
        put(ob, 0, s * 0.30, 0.04, 0.35, 0.85)
    return P


def apply_plan(plan):
    for name, ((dx, dy, dz), t0, t1) in plan.items():
        ob = bpy.data.objects[name]
        d = json.loads(ob["xr"]) if "xr" in ob else {}
        d["ex"] = to_gltf((dx, dy, dz))
        d["t0"] = t0
        d["t1"] = t1
        ob["xr"] = json.dumps(d, separators=(",", ":"))


# --------------------------------------------------------------------- export
def export_glb(path, draco=True):
    col = bpy.data.collections["XR_ANATOMY"]
    bpy.ops.object.select_all(action='DESELECT')
    objs = list(col.objects)
    for o in objs:
        o.hide_set(False)
        o.hide_viewport = False
        o.select_set(True)
    active = bpy.data.objects["XR_Anatomy"]
    bpy.context.view_layer.objects.active = active
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_cameras=False, export_lights=False, export_tangents=False, export_normals=True,
              export_extras=True, export_image_format='WEBP', export_vertex_color='NONE', export_attributes=True,
              export_image_webp_fallback=False, export_jpeg_quality=86)
    if draco:
        kw.update(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                  export_draco_position_quantization=14, export_draco_normal_quantization=10,
                  export_draco_generic_quantization=12)
    win = bpy.context.window or (bpy.context.window_manager.windows[0] if len(bpy.context.window_manager.windows) else None)
    override = dict(active_object=active, object=active, selected_objects=objs, selected_editable_objects=objs)
    if win:
        override["window"] = win
    with bpy.context.temp_override(**override):
        bpy.ops.export_scene.gltf(**kw)
    print("exported %s %.2f MB" % (path, os.path.getsize(path) / 1048576.0))
    return path
