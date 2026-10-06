"""Luxeed RX openings: the four doors split out of their mirrored panels as
nodes of their own, origin on the hinge, and the dark hull opened behind them.

Built from the opening photographs (blender/reference/luxeed-rx/openings):
frameless glass on all four doors, front-hinged, about 70-80 degrees open.

    import rx_openings as OP
    OP.split_doors()          # RX_Door_FL/FR/RL/RR in the RX_Doors collection
    OP.open_hull()            # the hull behind the doors, so the cabin shows
    OP.set_angle("FL", 70.0)  # preview a door open (degrees)

Car axes: +x forward, +y left, z up. The left door opens by rotating about
its hinge's vertical axis by a NEGATIVE angle (its rear edge swings to +y).
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import rx_panels as PN
import rx_surface as S

# key -> side (+1 left), the mirrored objects that make the door (each holds
# both sides), the cabin card prefix, the hinge row and the open angle
DOORS = {
    "FL": dict(side=1.0, row="front", card="int_door_L_", deg=75.0),
    "FR": dict(side=-1.0, row="front", card="int_door_R_", deg=75.0),
    "RL": dict(side=1.0, row="rear", card="int_rdoor_L_", deg=68.0),
    "RR": dict(side=-1.0, row="rear", card="int_rdoor_R_", deg=68.0),
}
ROWS = {
    "front": ("RX_Door_Front", "RX_Glass_DoorFront", "RX_Handle_F",
              "RX_Mirror_Head", "RX_Mirror_Stalk", "RX_Mirror_Glass"),
    "rear": ("RX_Door_Rear", "RX_Glass_DoorRear", "RX_Handle_R"),
}
HINGE_Z = 0.60


def hinge(key):
    """The hinge axis point: the door's leading edge at mid height, on the
    skin (the cabin's front cards already use it: export_rx.hinge)."""
    from carkit.interior import cabin as CB
    d = DOORS[key]
    if d["row"] == "front":
        x = PN._DOOR_F_EDGE(HINGE_Z)
    else:
        x = PN.X_BPILLAR - 0.012
    return Vector((x, d["side"] * CB.section_y_at(S.BODY, x, HINGE_Z), HINGE_Z))


def _side_object(src, side, name):
    """One side of a mirrored object with its modifiers baked (a new object,
    not yet linked)."""
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
    """The export groups: a glTF node per door, LuxeedRX_Door_<key>, and per
    open-door frame, LuxeedRX_DoorFrame_<key>."""
    return ([("LuxeedRX_Door_" + k, "RX_DoorGrp_" + k) for k in DOORS] +
            [("LuxeedRX_DoorFrame_" + k, "RX_DoorFrameGrp_" + k) for k in DOORS])


def split_doors():
    """Per door: its skin, glass, handle and mirror parts, one side each,
    joined into RX_Door_<key> with the origin on the hinge, in a collection
    of its own (RX_DoorGrp_<key>). The mirrored originals are removed."""
    from carkit import export as X
    made = {}
    for key, d in DOORS.items():
        base = bpy.data.objects[ROWS[d["row"]][0]].data
        loop = max(_loops(base), key=_length)
        build_frame(key, loop)
        col = bpy.data.collections.get("RX_DoorGrp_" + key) or bpy.data.collections.new("RX_DoorGrp_" + key)
        if col.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(col)
        parts = []
        for n in ROWS[d["row"]]:
            src = bpy.data.objects[n]
            ob = _side_object(src, d["side"], "%s_%s" % (n, key))
            col.objects.link(ob)
            parts.append(ob.name)
        door = X.join("RX_Door_" + key, parts)
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


def join_cards(collection="RX_Interior"):
    """Each door card's parts -> one object (int_door_L/R, int_rdoor_L/R),
    origin on the hinge: the cabin's half of a door, swung with the skin."""
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
    """Ordered boundary loops of a mesh, as lists of Vectors."""
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
    """The door card's boundary in (x, z): bottom, rear edge, belt, front edge."""
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


def build_frame(key, skin_loop):
    """The painted inner frame of a door, seen only when it is open (photo 7):
    a ring in the plane of the card's carrier, a rim wall out to the skin edge,
    and the black seal bead along the card's edge. In the door's closed pose."""
    import rx_interior as RI
    from carkit.interior.sweep import tube, ellipse
    d = DOORS[key]
    side = d["side"]
    dc = RI.front_card(side) if d["row"] == "front" else RI.rear_card(side)
    col = bpy.data.collections.get("RX_DoorFrameGrp_" + key) or         bpy.data.collections.new("RX_DoorFrameGrp_" + key)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)

    def depth(z):
        # the door's depth at its edge: the carrier plane, easing in below the card
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
    me = bpy.data.meshes.new("RX_DoorRing_" + key + "_mesh")
    bm.to_mesh(me)
    bm.free()
    paint = bpy.data.materials["M_Paint_RX_ShiftBlue"]
    me.materials.append(paint)
    ring = bpy.data.objects.new("RX_DoorRing_" + key, me)
    col.objects.link(ring)

    # the bead: on the ring, just outside the card's edge, thinning where the ring does
    outer = [(p.x, p.z) for p in skin]
    path, radii = [], []
    n = len(card)
    for i in range(n):
        a, b = card[i - 1], card[(i + 1) % n]
        t = Vector((b.x - a.x, 0.0, b.z - a.z))
        t.normalize()
        nx, nz = t.z, -t.x                      # outward in (x, z) for a ccw loop
        gap = min(math.hypot(card[i].x - ox, card[i].z - oz) for (ox, oz) in outer)
        r = max(0.003, min(0.012, 0.45 * gap))
        off = min(0.014, 0.5 * gap)
        path.append((card[i].x + nx * off, card[i].y - side * 0.004, card[i].z + nz * off))
        radii.append(r / 0.012)
    # the gap to the skin's edge is read off discrete points: smooth the bead's
    # radius round the loop (a moving average) so its outline is not a saw
    k = 4
    radii = [sum(radii[(i + j) % n] for j in range(-k, k + 1)) / (2 * k + 1) for i in range(n)]
    bead = tube("RX_DoorBead_" + key, path, ellipse(0.012, 0.010, 10), col,
                bpy.data.materials["M_Black_Satin"], closed=True, lateral=(0.0, 1.0, 0.0),
                scale=lambda s: (radii[int(round(s * n)) % n],) * 2)
    from carkit import export as X
    frame = X.join("RX_DoorFrame_" + key, [ring.name, bead.name])
    h = hinge(key)
    frame.data.transform(Matrix.Translation(-h))
    frame.matrix_world = Matrix.Translation(h)
    return frame


# ----------------------------------------------------------- the doorway's sill
SILL_X = (-1.02, 0.77)
# across the sill, measured from the outer face's plane: (dy, z) from the cabin
# sill's outer edge, over the top (with the plate on it), down the painted face
SILL_PROF = [(-0.056, 0.4440), (-0.030, 0.4400), (-0.010, 0.4355), (-0.002, 0.4290),
             (0.0, 0.4180), (0.0, 0.3300)]
# the RX plates: (x from, x to) of the front and the rear doorway; the lettering
# stands at the front end of each (photos 17-21)
SILL_PLATES = ((-0.30, 0.62), (-0.96, -0.44))


def _sill_y(x):
    """The sill's outer face: 12 mm inside the skin."""
    from carkit.interior import cabin as CB
    return CB.section_y_at(S.BODY, x, 0.38) - 0.012


def _sill_z(dy):
    """The painted top's height at dy from the outer face (the plate's seat)."""
    (d0, z0), (d1, z1) = SILL_PROF[0], SILL_PROF[2]
    t = max(0.0, min(1.0, (dy - d0) / (d1 - d0)))
    return z0 + (z1 - z0) * t


def _recalc(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()


def _rrect(x0, x1, y0, y1, r, n=8):
    pts = []
    for (cx, cy, a0) in ((x1 - r, y1 - r, 0.0), (x0 + r, y1 - r, 90.0),
                         (x0 + r, y0 + r, 180.0), (x1 - r, y0 + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_sill(collection="RX_Details"):
    """The painted sill under both doorways with the RX scuff plates on it and
    the seal bead beside them (opening photos 17-21). Static body parts: they
    are hidden behind a closed door and seen from the seat."""
    from carkit import mesh as M
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    col = bpy.data.collections[collection]
    paint = bpy.data.materials["M_Paint_RX_ShiftBlue"]
    satin = bpy.data.materials["M_Black_Satin"]
    ink = bpy.data.materials["M_Text_Dark"]
    made = []
    xs = [SILL_X[0] + (SILL_X[1] - SILL_X[0]) * k / 72.0 for k in range(73)]
    yo = {x: _sill_y(x) for x in xs}
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        rows = [[(x, side * (yo[x] + dy), z) for (dy, z) in SILL_PROF] for x in xs]
        ob = grid_mesh("RX_Sill_" + tag, rows, col, paint)
        M.orient(ob.data, lambda c, s=side: (0.0, s, 0.6))
        made.append(ob)
        for i, (xa, xb) in enumerate(SILL_PLATES):
            outline = _rrect(xa, xb, -0.050, -0.014, 0.012)
            top, bot = [], []
            for (x, dy) in outline:
                y = side * (_sill_y(x) + dy)
                z = _sill_z(dy)
                top.append((x, y, z + 0.0022))
                bot.append((x, y, z - 0.0020))
            n = len(top)
            faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
            faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
            pl = M.obj("RX_SillPlate_%s%d" % (tag, i), top + bot, faces, col, satin, smooth=False)
            _recalc(pl)
            made.append(pl)
            # "RX" at the plate's front end, reading rearward from outside
            xc, dyc = xb - 0.13, -0.032
            txt = M.text_mesh("RX_SillText_%s%d" % (tag, i), "RX", 0.017, col, ink,
                              extrude=0.0008, bold=True, italic=True, resolution=4)
            q = Vector((xc, side * (_sill_y(xc) + dyc), _sill_z(dyc) + 0.0030))
            rot = Matrix.Rotation(math.pi if side > 0 else 0.0, 4, 'Z')
            txt.matrix_world = Matrix.Translation(q) @ rot
            made.append(txt)
        # the seal bead along the cabin sill's outer edge
        path = [(x, side * (yo[x] - 0.060), 0.4525) for x in xs[2:-2]]
        made.append(tube("RX_SillBead_" + tag, path, ellipse(0.0105, 0.0095, 10), col, satin,
                         lateral=(0.0, 1.0, 0.0),
                         scale=lambda s: (min(1.0, 8.0 * s, 8.0 * (1.0 - s)),) * 2))
    return made


def set_angle(key, deg, card=True):
    """Swing a door (and its cabin card, if joined as int_door_*/int_rdoor_*)
    `deg` open about its hinge's vertical axis."""
    d = DOORS[key]
    rot = Matrix.Rotation(math.radians(-d["side"] * deg), 4, 'Z')
    names = ["RX_Door_" + key]
    if card:
        names.append(d["card"].rstrip("_"))
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        h = Vector(ob.matrix_world.translation) if n.startswith("RX_Door_") else hinge(key)
        ob.matrix_world = Matrix.Translation(h) @ rot


def open_hull(hull="RX_Shell_Shadow", core_z=0.70):
    """Delete the hull faces that sit behind a door skin (along rays from the
    core line), so the cabin shows through an open doorway."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, faces = [], []
    for key in DOORS:
        ob = bpy.data.objects.get("RX_Door_" + key)
        if ob is None:
            continue
        skin = ob.evaluated_get(dg)
        me = skin.to_mesh()
        base = len(verts)
        h = Vector(ob.get("hinge", (0, 0, 0)))
        # the door is built with its origin on the hinge: back to the closed pose
        mw = Matrix.Translation(h)
        verts += [mw @ v.co for v in me.vertices]
        faces += [[base + i for i in p.vertices] for p in me.polygons]
        skin.to_mesh_clear()
    tree = BVHTree.FromPolygons(verts, faces)
    sh = bpy.data.objects[hull]
    me = sh.data
    mw = sh.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    dead = []
    for f in bm.faces:
        p = mw @ f.calc_center_median()
        if abs(p.y) < 0.55:
            continue
        c = Vector((p.x, 0.0, core_z))
        d = p - c
        n = d.length
        if n < 1e-6:
            continue
        hit = tree.ray_cast(c, d / n, n + 0.40)[0]
        if hit is not None:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me)
    bm.free()
    return len(dead)


# ------------------------------------------------- the window's black underlay
def _glass_cutter(key, inset, front=0.03, back=0.06, drop=0.05):
    """A prism of one door glass's outline, `inset` smaller, swept along the
    glass's outward normal: the cutter for the sheet behind it. The glass's
    lower edge is taken `drop` further down, to the door skin's top edge: the
    sheet's strip between the two (about 2 cm, the window sill) would stay
    behind as a glossy black bar that mirrors the studio white."""
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
        if w.z > 0.7:                      # on the lower edge (w points into the glass)
            q.z -= drop
        pts.append(tuple(q))
    bpy.data.meshes.remove(me)
    return C.prism_dir("_glasscut_" + key, pts, tuple(n), back=back, front=front)


def cut_underlay(under="RX_Greenhouse_Black", inset=0.0025):
    """Take the door windows out of the greenhouse's black underlay.

    The underlay is one black sheet 3 mm under the glass, across the A-pillar,
    the B-pillar and every side window, and the glass is opaque, so a door
    swung open carried its pane away and left the sheet standing in the window:
    a black pane that did not move. Each door glass's outline (inset, so the
    shut pane still covers the edge) is cut out of it with an exact boolean;
    the pillars and the surround stay. Run before split_doors().
    Returns (faces before, faces after, faces pruned)."""
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
    return before, after, pruned
