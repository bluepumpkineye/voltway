"""BYD Seal 07 EV openings: the four doors split out of their mirrored panels as
nodes of their own, origin on the hinge, and the dark hull opened behind them.

Built from the BYD Seal 07 EV cabin & door photographs (blender/reference/byd-seal/cabin/
c3_0001..0012): hinged at their leading edge, the front pair about 72 degrees open,
the rear pair about 66; a painted inner frame round the card with a black seal bead
along its edge.

    import seal_openings as OP
    OP.cut_underlay()         # the door windows out of the black greenhouse sheet
    OP.split_doors()          # Seal_Door_FL/FR/RL/RR in the Seal_DoorGrp_* collections
    OP.open_hull()            # the hull behind the doors, so the cabin shows
    OP.set_angle("FL", 72.0)  # preview a door open (degrees)

Car axes: +x forward, +y left, z up.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector

import seal_panels as PN
import seal_surface as S

DOORS = {
    "FL": dict(side=1.0, row="front", card="int_door_L_", deg=72.0),
    "FR": dict(side=-1.0, row="front", card="int_door_R_", deg=72.0),
    "RL": dict(side=1.0, row="rear", card="int_rdoor_L_", deg=66.0),
    "RR": dict(side=-1.0, row="rear", card="int_rdoor_R_", deg=66.0),
}
ROWS = {
    "front": ("Seal_Door_Front", "Seal_Glass_DoorFront", "Seal_Handle_F", "Seal_Handle_Rim_F",
              "Seal_Mirror_Head", "Seal_Mirror_Stalk", "Seal_Mirror_Glass", "Seal_Mirror_Cam_Pod",
              "Seal_Ocean_Wave_Line_F"),
    "rear": ("Seal_Door_Rear", "Seal_Glass_DoorRear", "Seal_Handle_R", "Seal_Handle_Rim_R",
             "Seal_Ocean_Wave_Line_R"),
}
HINGE_Z = 0.60
PAINT = "M_Paint_Seal_Blue"


def hinge(key):
    """The hinge axis point: the door's leading edge at mid height, on the skin."""
    from carkit.interior import cabin as CB
    d = DOORS[key]
    if d["row"] == "front":
        x = PN._DOOR_F_EDGE(HINGE_Z)
    else:
        x = PN.X_BPILLAR_F - 0.012
    return Vector((x, d["side"] * CB.section_y_at(S.BODY, x, HINGE_Z), HINGE_Z))


def _side_object(src, side, name):
    """One side of a mirrored object with its modifiers baked (a new object, not yet linked)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    me.transform(src.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    dead = [f for f in bm.faces if f.calc_center_median().y * side < 0.0]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me)
    bm.free()
    me.name = name + "_mesh"
    return bpy.data.objects.new(name, me)


def door_groups():
    """The export groups: a glTF node per door, BYDSeal_Door_<key>, and per open-door frame,
    BYDSeal_DoorFrame_<key>."""
    return ([("BYDSeal_Door_" + k, "Seal_DoorGrp_" + k) for k in DOORS] +
            [("BYDSeal_DoorFrame_" + k, "Seal_DoorFrameGrp_" + k) for k in DOORS])


def _group(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


TRIM = ("Seal_Ocean_Wave_Line",)
X_FRONT_EDGE = 0.882
X_REAR_EDGE = -1.075


def split_trim():
    import seal_gate as RG
    for n in TRIM:
        if bpy.data.objects.get(n + "_F") is None:
            RG._split_off(n, n + "_F", [((PN.X_BPILLAR_F, 0.0, 0.0), (1.0, 0.0, 0.0)),
                                        ((X_FRONT_EDGE, 0.0, 0.0), (1.0, 0.0, 0.0))],
                          lambda c: PN.X_BPILLAR_F < c.x < X_FRONT_EDGE)
            RG._split_off(n, n + "_R", [((PN.X_BPILLAR_F, 0.0, 0.0), (1.0, 0.0, 0.0)),
                                        ((X_REAR_EDGE, 0.0, 0.0), (1.0, 0.0, 0.0))],
                          lambda c: X_REAR_EDGE < c.x < PN.X_BPILLAR_F)


def split_doors():
    """Per door: its skin, glass, handle and mirror parts, one side each, joined into
    Seal_Door_<key> with the origin on the hinge, in a collection of its own (Seal_DoorGrp_<key>)."""
    from carkit import export as X
    made = {}
    for key, d in DOORS.items():
        src0 = bpy.data.objects[ROWS[d["row"]][0]]
        loop = [src0.matrix_world @ p for p in max(_loops(src0.data), key=_length)]
        build_frame(key, loop)
        col = _group("Seal_DoorGrp_" + key)
        parts = []
        for n in ROWS[d["row"]]:
            src = bpy.data.objects[n]
            ob = _side_object(src, d["side"], "%s_%s" % (n, key))
            col.objects.link(ob)
            parts.append(ob.name)
        door = X.join("Seal_Door_" + key, parts)
        door["outline"] = [c for p in loop for c in (p.x, p.z)]
        h = hinge(key)
        door.data.transform(Matrix.Translation(-h))
        door.matrix_world = Matrix.Translation(h)
        door["hinge"] = tuple(h)
        door["open_deg"] = d["deg"]
        made[key] = door
    for row in ROWS.values():
        for n in row:
            ob = bpy.data.objects.get(n)
            if ob is not None:
                me = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                if me.users == 0:
                    bpy.data.meshes.remove(me)
    return made


def join_cards(collection="Seal_Interior"):
    """Each door card's parts -> one object (int_door_L/R, int_rdoor_L/R), origin on the hinge."""
    from carkit import export as X
    col = bpy.data.collections[collection]
    for key, d in DOORS.items():
        pre = d["card"]
        names = [o.name for o in col.objects if o.type == 'MESH' and o.name.startswith(pre)]
        ob = X.join(pre.rstrip("_"), names)
        if ob is None:
            continue
        h = hinge(key)
        ob.data.transform(Matrix.Translation(ob.matrix_world.translation - h))
        ob.matrix_world = Matrix.Translation(h)


# ------------------------------------------------- the open door's inner frame
def _loops(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    adj = {}
    for e in bm.edges:
        if e.is_boundary:
            a, b = e.verts[0].index, e.verts[1].index
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for start in list(adj):
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while cur is not None and cur not in seen:
            seen.add(cur)
            loop.append(bm.verts[cur].co.copy())
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            prev, cur = cur, (nxt[0] if nxt else None)
        out.append(loop)
    bm.free()
    return out


def _length(loop):
    return sum((loop[i] - loop[i - 1]).length for i in range(len(loop)))


def _area_xz(loop):
    return 0.5 * sum(loop[i - 1].x * loop[i].z - loop[i].x * loop[i - 1].z
                     for i in range(len(loop)))


def _ccw(loop):
    return loop if _area_xz(loop) >= 0.0 else loop[::-1]


def _card_loop(dc, n=36):
    zb = dc.zb

    def top(x):
        return dc.zt(x) - 0.002

    def corner(edge):
        z = zb + 0.5
        for _ in range(8):
            z = top(edge(z))
        return z
    zr, zf = corner(dc.xr), corner(dc.xf)
    pts = []
    for k in range(n):
        pts.append((dc.xf(zb) + (dc.xr(zb) - dc.xf(zb)) * k / n, zb))
    for k in range(n):
        z = zb + (zr - zb) * k / n
        pts.append((dc.xr(z), z))
    for k in range(2 * n):
        x = dc.xr(zr) + (dc.xf(zf) - dc.xr(zr)) * k / (2 * n)
        pts.append((x, top(x)))
    for k in range(n):
        z = zf - (zf - zb) * k / n
        pts.append((dc.xf(z), z))
    return pts


def _seg_dist(px, pz, poly):
    best = 1e9
    for i in range(len(poly)):
        ax, az = poly[i - 1]
        bx, bz = poly[i]
        dx, dz = bx - ax, bz - az
        l2 = dx * dx + dz * dz
        t = 0.0 if l2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
        best = min(best, math.hypot(px - (ax + t * dx), pz - (az + t * dz)))
    return best


def build_frame(key, skin_loop):
    """The painted inner frame of a door, seen only when it is open."""
    import seal_interior_doors as DR
    from carkit.interior.sweep import tube, ellipse
    d = DOORS[key]
    side = d["side"]
    dc = DR.front_card(side) if d["row"] == "front" else DR.rear_card(side)
    col = _group("Seal_DoorFrameGrp_" + key)

    def depth(z):
        return (dc.th(max(z, dc.zb)) - 0.012) * (0.6 + 0.4 * min(1.0, max(0.0, (z - 0.30) / 0.10)))

    card = _ccw([Vector(dc.point(x, z, -0.012)) for (x, z) in _card_loop(dc, n=20)])
    skin = _ccw([Vector((p.x, side * abs(p.y), p.z)) for p in skin_loop])[::2]
    rim_out = [Vector((p.x, p.y - side * 0.003, p.z)) for p in skin]
    rim_in = [Vector((p.x, p.y - side * depth(p.z), p.z)) for p in skin]

    bm = bmesh.new()
    va = [bm.verts.new(p) for p in card]
    vb = [bm.verts.new(p) for p in rim_in]
    ea = [bm.edges.new((va[i - 1], va[i])) for i in range(len(va))]
    eb = [bm.edges.new((vb[i - 1], vb[i])) for i in range(len(vb))]
    bmesh.ops.bridge_loops(bm, edges=ea + eb, use_pairs=False, use_cyclic=False)
    vc = [bm.verts.new(p) for p in rim_out]
    for i in range(len(vc)):
        j = (i + 1) % len(vc)
        bm.faces.new((vc[i], vc[j], vb[j], vb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Seal_DoorRing_" + key + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials[PAINT])
    ring = bpy.data.objects.new("Seal_DoorRing_" + key, me)
    col.objects.link(ring)

    outer = [(p.x, p.z) for p in skin]
    n = len(card)
    gaps = [_seg_dist(card[i].x, card[i].z, outer) for i in range(n)]
    k = 4
    gaps = [sum(gaps[(i + j) % n] for j in range(-k, k + 1)) / (2 * k + 1) for i in range(n)]
    path, radii = [], []
    for i in range(n):
        a, b = card[i - 1], card[(i + 1) % n]
        t = Vector((b.x - a.x, 0.0, b.z - a.z))
        t.normalize()
        nx, nz = t.z, -t.x
        gap = gaps[i]
        r = max(0.003, min(0.012, 0.45 * gap))
        off = min(0.014, 0.5 * gap)
        path.append((card[i].x + nx * off, card[i].y - side * 0.004, card[i].z + nz * off))
        radii.append(r / 0.012)
    bead = tube("Seal_DoorBead_" + key, path, ellipse(0.012, 0.010, 10), col,
                bpy.data.materials["M_Black_Satin"], closed=True, lateral=(0.0, 1.0, 0.0),
                scale=lambda s: (radii[int(round(s * n)) % n],) * 2)
    from carkit import export as X
    frame = X.join("Seal_DoorFrame_" + key, [ring.name, bead.name])
    h = hinge(key)
    frame.data.transform(Matrix.Translation(-h))
    frame.matrix_world = Matrix.Translation(h)
    return frame


def set_angle(key, deg, card=True):
    """Swing a door (and its cabin card) `deg` open about its hinge's vertical axis."""
    d = DOORS[key]
    rot = Matrix.Rotation(math.radians(-d["side"] * deg), 4, 'Z')
    names = ["Seal_Door_" + key, "Seal_DoorFrame_" + key]
    if card:
        names.append(d["card"].rstrip("_"))
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        h = Vector(ob.matrix_world.translation) if n.startswith(("Seal_Door_", "Seal_DoorFrame_")) else hinge(key)
        ob.matrix_world = Matrix.Translation(h) @ rot


def open_hull(hull="Seal_Shell_Shadow"):
    """Cut the hull away behind every door, so the cabin shows through an open doorway."""
    from carkit import cut as C
    ob = bpy.data.objects[hull]
    sheet = C.sheet_bvh(ob)
    cutters = []
    for key, d in DOORS.items():
        door = bpy.data.objects.get("Seal_Door_" + key)
        flat = door.get("outline") if door is not None else None
        if not flat:
            continue
        pts = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
        y0, y1 = (0.40, 1.10) if d["side"] > 0 else (-1.10, -0.40)
        cutters.append(C.prism_y("_hullcut_" + key, pts, y0, y1))
    before, after = C.difference(ob, cutters, "door_")
    pruned = C.prune_off_sheet(ob, sheet)
    return before, after, pruned


def _glass_cutter(key, inset, front=0.03, back=0.06, drop=0.05):
    from carkit import cut as C
    d = DOORS[key]
    src = bpy.data.objects[ROWS[d["row"]][1]]
    tmp = _side_object(src, d["side"], "_cut_" + key)
    me = tmp.data
    loop = max(_loops(me), key=_length)
    n = Vector()
    for p in me.polygons:
        n += p.normal * p.area
    n.normalize()
    if n.y * d["side"] < 0.0:
        n = -n
    centre = sum(loop, Vector()) / len(loop)
    m = len(loop)
    pts = []
    for i, p in enumerate(loop):
        t = (loop[(i + 1) % m] - loop[i - 1]).normalized()
        w = n.cross(t).normalized()
        if w.dot(centre - p) < 0.0:
            w = -w
        q = p + w * inset
        if w.z > 0.7:
            q.z -= drop
        pts.append(tuple(q))
    bpy.data.meshes.remove(me)
    return C.prism_dir("_glasscut_" + key, pts, tuple(n), back=back, front=front)


def cut_underlay(under="Seal_Greenhouse_Black", inset=0.0025, hull="Seal_Shell_Shadow"):
    """Take the door windows out of the greenhouse's black underlay."""
    from carkit import cut as C
    from carkit import mesh as M
    ob = bpy.data.objects[under]
    M.apply_modifiers(ob)
    sheet = C.sheet_bvh(ob)
    cutters = [_glass_cutter(key, inset) for key in DOORS]
    before, after = C.difference(ob, cutters, "win_")
    pruned = C.prune_off_sheet(ob, sheet)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    shell = bpy.data.objects.get(hull)
    if shell is not None:
        M.apply_modifiers(shell)
        sheet = C.sheet_bvh(shell)
        C.difference(shell, [_glass_cutter(key, 0.002) for key in DOORS], "winhull_")
        C.prune_off_sheet(shell, sheet)
    return before, after, pruned
