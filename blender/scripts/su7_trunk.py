"""Xiaomi SU7 Ultra trunk lid and boot. (The Luxeed RX's rx_gate.py is the
template; the lid itself is not a hatch - it is the deck, the tail cap's upper
face and the wing, hung on two gooseneck arms.)

Built from the opening photographs (blender/reference/xiaomi-su7-ultra/openings/
trunk, 22-32): the lid is the cap inside the shut line (su7_panels.lid_edge_path)
and the deck behind it, with the wing, the duck tail, the stripes, the badges and
the inner halves of the tail lamps; its underside is black felt inside a painted
return flange. It is hinged just behind the backlight and stands nearly upright
on two black gooseneck arms that end in cups at the boot's upper corners. The
boot behind it is carpeted, with a sill ledge, a 12 V socket and a bag hook.

    import su7_trunk as TR
    TR.build_boot()           # the boot, in the cabin's collection (baked with it)
    TR.build_liner()          # int_trunk: the felt under the lid, likewise
    TR.build_seal()           # a black bead behind the shut line (SU7_Details)
    TR.build_cups()           # the cups the arms end in
    TR.split_lid()            # SU7_Trunk: the lid, origin on the hinge; the hull opened
    TR.build_arms()           # SU7_TrunkArms: the gooseneck arms (shown while open)
    TR.set_lid(82.0)          # preview it open (degrees)

The cabin's parts (boot, liner) are built with the cabin, before it is baked; the
rest once per export (export_gltf.prepare_exterior).

Car axes: +x forward, +y left, z up. The lid opens by rotating about +y.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import su7_nose as N
import su7_panels as PN

# The hinge axis, lateral, as a point (x, z): not at the lid's front edge but a
# little ahead of and above it, so the edge rises ~0.2 m as it swings, clear of
# the glass (in the photographs the lid hangs well above the backlight's foot).
HINGE = Vector((-1.805, 0.0, 1.218))
OPEN_DEG = 82.0
GROUP = ("SU7Ultra_Trunk", "SU7_TrunkGrp")
ARMS_GROUP = ("SU7Ultra_TrunkArms", "SU7_TrunkArmsGrp")
Y_CUT = PN.Y_LID                           # the lid's side edge across the lamps
FLANGE = 0.030                             # depth of the lid's return flange
INSIDE = Vector((-2.1, 0.0, 0.85))         # a point in the boot, for "outward"

# whole objects that sit on the lid (each holds both sides, or one badge)
PARTS = (
    "SU7Ultra_Decklid", "SU7Ultra_Ducktail", "SU7Ultra_Wing_Blade", "SU7Ultra_Wing_Pylon",
    "SU7Ultra_Stripes_Deck", "SU7Ultra_Badge_Xiaomi", "SU7Ultra_Badge_Mi",
    "SU7Ultra_Badge_SU7", "SU7Ultra_Badge_Ultra", "SU7Ultra_Tail_LensInner",
)
# the lamp parts the lid's side edge crosses: the inner pieces go with the lid
CROSSING = (
    "SU7Ultra_Tail_Housing", "SU7Ultra_Tail_Pipe", "SU7Ultra_Tail_PipeUp",
    "SU7Ultra_Tail_Guide", "SU7Ultra_Tail_SealLow", "SU7Ultra_Tail_SealUp",
)


def hinge():
    return Vector(HINGE)


def _link_only(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)


def _group(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def _components(bm):
    """Connected pieces of a sheet, as lists of faces."""
    seen, comps = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        comps.append(comp)
    return comps


def _copy_modifiers(src, dst):
    for m in src.modifiers:
        n = dst.modifiers.new(m.name, m.type)
        for p in m.bl_rna.properties:
            if p.is_readonly or p.identifier in ("name", "type", "rna_type"):
                continue
            try:
                setattr(n, p.identifier, getattr(m, p.identifier))
            except (AttributeError, TypeError):
                pass


# ------------------------------------------------------------- the lid's skin
def _nominal_tail():
    """A BVH of the tail cap as it was built, before the shut line cut it."""
    rows, _ = PN.cap_rows(False, 0.250, N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 120, 90,
                          top_to_centre=True)
    verts, faces = [], []
    nv = len(rows[0])
    for r in rows:
        verts.extend(r)
    for i in range(len(rows) - 1):
        a, b = i * nv, (i + 1) * nv
        faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(nv - 1)]
    return BVHTree.FromPolygons(verts, faces)


def _lid_faces(bm, probe=(0.15, 0.90)):
    """The faces of the lid's skin in the cap's sheet. The exact boolean that
    cut the shut line left its walls and floor, a groove 30 mm deep that ties
    lid and body together: those go (bm is changed), keeping what lies on the
    cap's own surface; the shut line then separates the sheet in two."""
    tree = _nominal_tail()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces
                               if tree.find_nearest(f.calc_center_median())[3] > 0.002],
                     context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.faces.ensure_lookup_table()
    comps = [c for c in _components(bm) if len(c) > 8]
    if len(comps) < 2:
        raise RuntimeError("the shut line does not separate the lid's skin: %d piece(s)" % len(comps))

    def dist(c):
        return min(math.hypot(f.calc_center_median().y - probe[0],
                              f.calc_center_median().z - probe[1]) for f in c)
    return min(comps, key=dist)


def _lid_piece(cap="SU7Ultra_Tail_Upper"):
    """The lid's half sheet as a bmesh of its own, the cap left as it is."""
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[cap].data)
    keep = {f.index for f in _lid_faces(bm)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    return bm


def split_cap(cap="SU7Ultra_Tail_Upper"):
    """Cut the lid's skin off the tail cap: SU7_Lid_Skin (the half sheet, with the
    cap's modifiers), and the cap without it."""
    src = bpy.data.objects[cap]
    bm = bmesh.new()
    bm.from_mesh(src.data)
    faces = _lid_faces(bm)
    vmap, verts, polys, mats, smooth = {}, [], [], [], []
    for f in faces:
        idx = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = len(verts)
                verts.append(v.co.copy())
            idx.append(vmap[v.index])
        polys.append(idx)
        mats.append(f.material_index)
        smooth.append(f.smooth)
    me = bpy.data.meshes.new("SU7_Lid_Skin_mesh")
    me.from_pydata(verts, [], polys)
    for p, m, s in zip(me.polygons, mats, smooth):
        p.material_index = m
        p.use_smooth = s
    for m in src.data.materials:
        me.materials.append(m)
    skin = bpy.data.objects.new("SU7_Lid_Skin", me)
    skin.matrix_world = src.matrix_world
    _copy_modifiers(src, skin)
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(src.data)
    bm.free()
    return skin


def _cut_at_y(name, y_cut=Y_CUT):
    """A lamp part (both sides) cut at the lid's side edge: the original keeps
    the outer pieces, the inner piece is returned as a new object."""
    from carkit import export as X
    ob = bpy.data.objects[name]
    X.bake_modifiers(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for sgn in (1.0, -1.0):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0.0, sgn * y_cut, 0.0), plane_no=(0.0, 1.0, 0.0))
    inner = [f for f in bm.faces if abs(f.calc_center_median().y) < y_cut]
    outer = [f for f in bm.faces if abs(f.calc_center_median().y) >= y_cut]

    def sub(faces, keep):
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        ids = {f.index for f in faces}
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if (f.index in ids) != keep], context='FACES')
        bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
        return b2
    b_in, b_out = sub(inner, True), sub(inner, False)
    bm.free()
    me_in = bpy.data.meshes.new(name + "_lid_mesh")
    b_in.to_mesh(me_in)
    b_in.free()
    for m in ob.data.materials:
        me_in.materials.append(m)
    for p in me_in.polygons:
        p.use_smooth = True
    old = ob.data
    b_out.to_mesh(old)
    b_out.free()
    old.update()
    new = bpy.data.objects.new(name + "_lid", me_in)
    new.matrix_world = ob.matrix_world
    for c in ob.users_collection:
        c.objects.link(new)
    return new, len(inner), len(outer)


# ------------------------------------------------------------ flange and liner
def _outward(bm):
    """Vertex normals of a sheet, outward, keyed by vertex index."""
    vn = {}
    for f in bm.faces:
        a = f.calc_area()
        for v in f.verts:
            vn[v.index] = vn.get(v.index, Vector()) + f.normal * a
    sgn = 1.0 if sum((f.calc_center_median() - INSIDE).dot(f.normal) for f in bm.faces) > 0 else -1.0
    return {k: n.normalized() * sgn for k, n in vn.items()}


def _snap(co):
    """Pull the centreline's vertices onto y = 0 so the Mirror welds them."""
    q = co.copy()
    if abs(q.y) < 0.008:
        q.y = 0.0
    return q


def _flange_and_liner(pieces, depth=FLANGE):
    """From the lid's half sheets (the skin on the tail cap, the deck): the
    return flange turned in from the lid's free edge (not where the two sheets
    meet), painted, and the felt liner `depth` behind the whole of both. Returns
    (flange bmesh, liner bmesh), halves to be mirrored."""
    flange, liner = bmesh.new(), bmesh.new()
    trees = [BVHTree.FromBMesh(bm) for bm in pieces]
    for k, bm in enumerate(pieces):
        others = [t for j, t in enumerate(trees) if j != k]
        bm.normal_update()
        vn = _outward(bm)
        lv, tv, bv = {}, {}, {}

        def L(v):
            if v.index not in lv:
                lv[v.index] = liner.verts.new(_snap(v.co - vn[v.index] * depth))
            return lv[v.index]
        for f in bm.faces:
            liner.faces.new([L(v) for v in f.verts][::-1])
        centre = sum((f.calc_center_median() for f in bm.faces), Vector()) / len(bm.faces)

        def top(v):
            if v.index not in tv:
                tv[v.index] = flange.verts.new(_snap(v.co - vn[v.index] * 0.0025))
            return tv[v.index]

        def low(v):
            if v.index not in bv:
                bv[v.index] = flange.verts.new(_snap(v.co - vn[v.index] * depth))
            return bv[v.index]
        for e in bm.edges:
            if not e.is_boundary:
                continue
            a, b = e.verts
            if abs(a.co.y) < 0.008 and abs(b.co.y) < 0.008:
                continue                                           # the centreline seam
            mid = (a.co + b.co) * 0.5
            if any(t.find_nearest(mid)[3] < 0.006 for t in others):
                continue                                           # where the two sheets meet
            q = [top(a), top(b), low(b), low(a)]
            face = flange.faces.new(q)
            if face.normal.dot(centre - face.calc_center_median()) < 0.0:
                face.normal_flip()
    return flange, liner


def _pieces(skin=None, deck="SU7Ultra_Decklid"):
    """The lid's two half sheets as bmeshes: the skin on the tail cap (an object
    already split off, or cut from the cap on the fly) and the deck."""
    if skin is None:
        first = _lid_piece()
    else:
        first = bmesh.new()
        first.from_mesh(skin.data)
    second = bmesh.new()
    second.from_mesh(bpy.data.objects[deck].data)
    return [first, second]


def build_liner():
    """The felt liner under the lid, int_trunk, in the cabin's collection (so it
    is baked with it): its origin is the hinge and it swings with the lid. Built
    from the cap as it is, before or after the lid is split off."""
    from carkit import materials as MB
    from carkit import mesh as M
    pieces = _pieces(bpy.data.objects.get("SU7_Lid_Skin"))
    flange_bm, liner_bm = _flange_and_liner(pieces)
    for bm in pieces + [flange_bm]:
        bm.free()
    felt = MB.ensure("INT_Hatch_Liner", (0.030, 0.030, 0.033), 0.9, specular=0.2)
    me = bpy.data.meshes.new("int_trunk_mesh")
    liner_bm.to_mesh(me)
    liner_bm.free()
    me.materials.append(felt)
    for p in me.polygons:
        p.use_smooth = True
    h = hinge()
    me.transform(Matrix.Translation(-h))
    liner = bpy.data.objects.new("int_trunk", me)
    liner.matrix_world = Matrix.Translation(h)
    bpy.data.collections["SU7_Interior"].objects.link(liner)
    M.mirror_y(liner)
    return liner


def build_flange(skin, col):
    """The painted return flange, an object for the lid's node (the skin is
    the lid's half sheet on the tail cap, already split off)."""
    from carkit import mesh as M
    pieces = _pieces(skin)
    flange_bm, liner_bm = _flange_and_liner(pieces)
    for bm in pieces + [liner_bm]:
        bm.free()
    me = bpy.data.meshes.new("SU7_Trunk_Rim_mesh")
    flange_bm.to_mesh(me)
    flange_bm.free()
    me.materials.append(bpy.data.materials["M_Paint_Yellow"])
    for p in me.polygons:
        p.use_smooth = False
    rim = bpy.data.objects.new("SU7_Trunk_Rim", me)
    col.objects.link(rim)
    M.mirror_y(rim)
    return rim


# ------------------------------------------------------------- the hull behind
def _open_hull(skins, hulls=("SU7Ultra_Shell_Shadow", "SU7Ultra_Shell_Shadow_R"), x_max=-1.85):
    """Delete the hull faces that sit behind the lid's skin (straight under the
    deck, or straight in front of the tail face), so the boot shows through an
    open lid. `skins` are the lid's skin objects, still in the closed pose."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for ob in skins:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(ob.matrix_world)
        base = len(verts)
        verts += [v.co.copy() for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromPolygons(verts, polys)
    down, back = Vector((0.0, 0.0, -1.0)), Vector((1.0, 0.0, 0.0))
    total = 0
    for name in hulls:
        sh = bpy.data.objects.get(name)
        if sh is None:
            continue
        from carkit import mesh as M
        M.apply_modifiers(sh)
        bm = bmesh.new()
        bm.from_mesh(sh.data)
        dead = []
        for f in bm.faces:
            p = sh.matrix_world @ f.calc_center_median()
            if p.x > x_max or abs(p.y) > Y_CUT + 0.08:
                continue
            h = tree.ray_cast(p + Vector((0.0, 0.0, 0.25)), down, 0.28)[0]
            if h is not None and -0.02 <= h.z - p.z <= 0.06:
                dead.append(f)
                continue
            h = tree.ray_cast(p + Vector((-0.25, 0.0, 0.0)), back, 0.28)[0]
            if h is not None and -0.02 <= p.x - h.x <= 0.06:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(sh.data)
        bm.free()
        total += len(dead)
    return total


def split_lid():
    """Gather the lid into one node with its origin on the hinge: the skin cut
    from the tail cap, the deck and everything on them, the inner pieces of the
    lamps the shut line crosses, the painted return flange. Opens the hull behind
    it. Returns the node."""
    from carkit import export as X
    col = _group(GROUP[1])
    skin = split_cap()
    col.objects.link(skin)
    rim = build_flange(skin, col)
    removed = _open_hull([skin, bpy.data.objects["SU7Ultra_Decklid"]])
    names = [skin.name, rim.name]
    for n in PARTS:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("lid part %s missing from the build" % n)
        _link_only(ob, col)
        names.append(ob.name)
    for n in CROSSING:
        inner, n_in, n_out = _cut_at_y(n)
        if not n_in or not n_out:
            raise RuntimeError("%s is not crossed by the lid's side edge (%d / %d faces)" % (n, n_in, n_out))
        _link_only(inner, col)
        names.append(inner.name)
    lid = X.join("SU7_Trunk", names)
    h = hinge()
    lid.data.transform(Matrix.Translation(-h))
    lid.matrix_world = Matrix.Translation(h)
    lid["hinge"] = tuple(h)
    lid["open_deg"] = OPEN_DEG
    lid["hull_faces_removed"] = removed
    return lid


def trunk_groups():
    return [GROUP, ARMS_GROUP]


def set_lid(deg, card=True):
    """Preview: swing the lid (and its liner and arms, if built) `deg` open."""
    rot = Matrix.Rotation(math.radians(deg), 4, 'Y')
    for n in ("SU7_Trunk", "SU7_TrunkArms", "int_trunk"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n != "int_trunk"):
            ob.matrix_world = Matrix.Translation(hinge()) @ rot


# ------------------------------------------------------- arms, cups and the seal
ARM_Y = 0.28
# the arm's spine as photographed, lid open: from the bracket on the lid's
# underside, bulging back, down to the hook that ends in the cup (x, z)
ARM_OPEN = [(-2.000, 1.398), (-2.036, 1.330), (-2.052, 1.240), (-2.036, 1.140),
            (-1.996, 1.060), (-1.958, 1.012), (-1.940, 1.000)]
CUP = (-1.950, 1.000)


def _to_closed(p):
    """A point in the lid-open pose -> the closed pose the node's mesh is in."""
    h = hinge()
    q = Matrix.Rotation(math.radians(-OPEN_DEG), 3, 'Y') @ (Vector(p) - h)
    return h + q


def _box(name, x0, x1, y0, y1, z0, z1, mat, col, smooth=False):
    from carkit import mesh as M
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, v, f, col, mat, smooth=smooth)
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    M.orient(ob.data, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))
    return ob


def build_arms():
    """The two gooseneck arms and the brackets that hold them to the lid, as
    one node on the lid's hinge (SU7_TrunkArms). The arms are designed in the
    pose of the photographs and turned back into the closed pose; the viewer
    shows the node only while the lid is open (it is the lid's 'frame')."""
    from carkit.interior.sweep import smooth_path, tube, ellipse
    col = _group(ARMS_GROUP[1])
    satin = bpy.data.materials["M_Black_Satin"]
    names = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        ctrl = [tuple(_to_closed((x, side * ARM_Y, z))) for (x, z) in ARM_OPEN]
        path = smooth_path(ctrl, 48)
        arm = tube("SU7_TrunkArm" + tag, path, ellipse(0.0175, 0.0175, 12), col, satin,
                   closed=False, lateral=(0.0, 1.0, 0.0))
        names.append(arm.name)
        # the bracket: a black block on the lid's underside, where the arm starts
        b = _to_closed((ARM_OPEN[0][0] - 0.02, side * ARM_Y, ARM_OPEN[0][1] + 0.012))
        blk = _box("SU7_TrunkBracket" + tag, b.x - 0.040, b.x + 0.040, b.y - 0.040, b.y + 0.040,
                   b.z - 0.026, b.z + 0.026, satin, col)
        names.append(blk.name)
    from carkit import export as X
    arms = X.join("SU7_TrunkArms", names)
    h = hinge()
    arms.data.transform(Matrix.Translation(-h))
    arms.matrix_world = Matrix.Translation(h)
    arms["hinge"] = tuple(h)
    return arms


def build_cups(collection="SU7_Details"):
    """The black cups at the boot's upper front corners that the arms end in."""
    col = bpy.data.collections[collection]
    satin = bpy.data.materials["M_Black_Satin"]
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        y = side * ARM_Y
        made.append(_box("SU7_TrunkCup" + tag, CUP[0] - 0.040, CUP[0] + 0.030, y - 0.034, y + 0.034,
                         CUP[1] - 0.045, CUP[1] + 0.012, satin, col))
    return made


def build_seal(collection="SU7_Details"):
    """A black bead behind the lid's shut line all the way round the opening:
    up the tail, over the top, along the deck's sides and across the front. It
    shows when the lid is open and fills the gap when it is shut."""
    from carkit.interior.sweep import tube, ellipse
    col = bpy.data.collections[collection]
    pts, nrm = PN.lid_edge_path()
    path = [Vector(p) - Vector(n).normalized() * 0.011 for p, n in zip(pts, nrm)]
    # along the deck: the decklid's own boundary (its half sheet), side and front
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects["SU7Ultra_Decklid"].data)
    bm.verts.ensure_lookup_table()
    edge = {v.index for e in bm.edges if e.is_boundary for v in e.verts}
    pts_b = [bm.verts[i].co.copy() for i in edge]
    bm.free()
    front = max((p for p in pts_b if abs(p.y) < 0.004), key=lambda p: p.x)    # the nose on the centreline
    deck = [p for p in pts_b if p.y > 0.004 and p.x > path[-1].x + 0.001] + [front]
    deck.sort(key=lambda p: math.atan2(abs(p.y), p.x - (-2.2)), reverse=True)
    top = [p - Vector((0.0, 0.0, 0.011)) for p in deck]
    # three beads end to end: a tube's profile is swept about a fixed side vector, which
    # must not run along the path (x on the vertical tail run, z over the deck), so the
    # tail's two sides and the deck's U each get their own
    side = [Vector(p) for p in path[:36]]
    rest = [Vector(p) for p in path[36:]] + top
    mirror = lambda pts: [Vector((p.x, -p.y, p.z)) for p in pts]
    from carkit.interior.sweep import resample
    satin = bpy.data.materials["M_Black_Satin"]
    made = []
    for name, pts_, lat in (("SU7_Boot_SealL", side, (1.0, 0.0, 0.0)),
                            ("SU7_Boot_SealR", mirror(side), (1.0, 0.0, 0.0)),
                            ("SU7_Boot_SealTop", mirror(rest) + rest[::-1][1:], (0.0, 0.0, 1.0))):
        n = max(8, int(sum((pts_[i] - pts_[i - 1]).length for i in range(1, len(pts_))) / 0.018))
        made.append(tube(name, resample([tuple(p) for p in pts_], n), ellipse(0.0100, 0.0100, 8), col,
                         satin, closed=False, lateral=lat))
    return made


# ----------------------------------------------------------------- the boot
Z_FLOOR = 0.585
X_MOUTH, X_WALL, X_BULK = -2.36, -2.42, -1.525
# the deck's height on the centreline ahead of the tail cap (the decklid, measured)
DECK_Z = [(-2.10, 1.045), (-2.00, 1.074), (-1.92, 1.092)]
_WALL, _TAIL = None, None


def _tail():
    global _TAIL
    if _TAIL is None:
        _TAIL = _nominal_tail()
    return _TAIL


def _skin_y(x, z):
    """Half the body's width at (x, z): the tail cap as built where it is
    round (a little lower if the cap ends below z), the body's section ahead
    of it."""
    if x < -2.10:
        for dz in (0.0, 0.02, 0.04, 0.06, 0.08, 0.12, 0.18):
            h = _tail().ray_cast(Vector((x, 0.0, z - dz)), Vector((0.0, 1.0, 0.0)), 2.0)[0]
            if h is not None:
                return h.y
        return 0.05
    import su7_surface as S
    from carkit.interior import cabin as CB
    return CB.section_y_at(S.BODY, x, z)


def _top(x):
    """The lid's height over the boot, a little off the centreline (the cap's
    chart collapses to a point on it)."""
    h = _tail().ray_cast(Vector((x, 0.12, 1.6)), Vector((0.0, 0.0, -1.0)), 2.0)[0]
    if h is not None:
        return h.z
    (x0, z0), (x1, z1) = DECK_Z[0], DECK_Z[-1]
    return z0 + (z1 - z0) * max(0.0, min(1.0, (x - x0) / (x1 - x0)))


def _wall_y(x, z=0.80):
    """Half the boot's width at (x, z): the skin's inside where the tail is
    round (a 65 mm wall that leans in with the tail's tumblehome), widening
    behind the wheel arches and pinching to the wheelhouse trims' inner face
    (int_quarter, 0.70)."""
    global _WALL
    if _WALL is None:
        from carkit.geom import Curve
        _WALL = Curve([(-2.46, 0.800), (-2.12, 0.800), (-1.96, 0.780), (-1.88, 0.720),
                       (-1.80, 0.700), (-1.52, 0.700)], mode="pchip")
    return max(0.03, min(_WALL(x), _skin_y(x, z) - 0.065))


def _gate_bottom(y):
    """z of the lid's shut line at |y|, along the bottom run and its corner."""
    y = abs(y)
    y_c = PN.Y_LID - PN.R_LID
    if y <= y_c:
        return PN.Z_LID
    d = min(PN.R_LID, y - y_c)
    return PN.Z_LID + PN.R_LID - math.sqrt(max(0.0, PN.R_LID ** 2 - d ** 2))


def _x_tail(y, z):
    """x of the tail cap's face at (y, z), seen from behind. A ray, not the cap's
    (w, v) chart, which fails where the cap turns into the flank."""
    h = _tail().ray_cast(Vector((-3.2, abs(y), z)), Vector((1.0, 0.0, 0.0)), 3.0)[0]
    if h is None:
        raise RuntimeError("tail cap: nothing seen from behind at (y %.3f, z %.3f)" % (y, z))
    return h.x


def build_boot(col=None):
    """The boot behind the lid, in the cabin's collection (baked with it):
    carpeted floor and side walls under a trim, the sill ledge with its plate,
    a 12 V socket and a bag hook (photographs 25-32)."""
    from carkit import materials as MB
    from carkit import mesh as M
    from carkit.interior import cabin as CB
    from carkit.interior.sweep import grid_mesh
    col = col or bpy.data.collections["SU7_Interior"]
    carpet = MB.ensure("INT_Boot_Carpet", (0.030, 0.030, 0.032), 0.96, specular=0.2)
    trim = MB.ensure("INT_Boot_Trim", (0.040, 0.040, 0.044), 0.62, specular=0.35)
    # a metal would reflect the cabin's probe and read black: light satin instead
    plate = MB.ensure("INT_Boot_Plate", (0.075, 0.077, 0.082), 0.45, specular=0.5)
    wy = _wall_y
    made = []
    xs = [X_MOUTH + (X_BULK - X_MOUTH) * k / 44.0 for k in range(45)]
    rows = [[(x, wy(x, 0.62) * j / 12.0, Z_FLOOR) for j in range(13)] for x in xs]
    fl = grid_mesh("int_boot_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)

    def side(name, mat, z_lo, z_hi, nz):
        stations = [X_WALL + (X_BULK - X_WALL) * k / 48.0 for k in range(49)]
        rws = []
        for x in stations:
            a, b = z_lo(x), z_hi(x)
            rws.append([(x, wy(x, a + (b - a) * k / nz), a + (b - a) * k / nz) for k in range(nz + 1)])
        ob = grid_mesh(name, rws, col, mat)
        M.orient(ob.data, lambda c: (0.0, -1.0, 0.0))
        M.mirror_y(ob)
        return ob
    made.append(side("int_boot_wall", carpet, lambda x: Z_FLOOR, lambda x: 0.80, 3))
    made.append(side("int_boot_trim", trim, lambda x: 0.80, lambda x: min(1.03, _top(x) - 0.045), 4))
    # the sill ledge along the shut line's U: a flat step in from the cap, with a
    # riser down to the floor
    ys = [0.46 * k / 40.0 for k in range(41)]
    shelf, strip = [], []
    for y in ys:
        zg = _gate_bottom(y)
        xo = _x_tail(y, zg) + 0.012
        zs = max(Z_FLOOR + 0.012, zg - 0.026)
        shelf.append([(xo, y, zs), (xo + 0.100, y, zs), (xo + 0.100, y, Z_FLOOR)])
        if 0.07 <= y <= 0.42:
            strip.append([(xo + 0.020, y, zs + 0.003), (xo + 0.088, y, zs + 0.003)])
    sh = grid_mesh("int_boot_sill", shelf, col, trim)
    M.orient(sh.data, lambda c: (0.6, 0.0, 1.0))
    M.mirror_y(sh)
    made.append(sh)
    pl = grid_mesh("int_boot_plate", strip, col, plate)
    M.orient(pl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(pl)
    made.append(pl)
    # small things on the walls: a bag hook on the left, the 12 V socket on the right
    rubber = bpy.data.materials["INT_Rubber"]
    xm, zm = -2.10, 0.790
    yl = wy(xm) - 0.003
    made.append(_box("int_boot_hook", xm, xm + 0.024, yl - 0.012, yl - 0.003, zm - 0.020, zm + 0.020,
                     rubber, col))
    made.append(_box("int_boot_socket", xm + 0.20, xm + 0.236, -yl + 0.003, -yl + 0.014, zm - 0.018,
                     zm + 0.018, rubber, col))
    return made
