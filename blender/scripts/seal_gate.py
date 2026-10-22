"""BYD Seal EV trunk lid and boot.

The lid is the rear decklid above the bumper: the decklid with its ducktail,
the tail cap's upper band and tailgate panel, the middle section of the full-width
Ocean water-drop tail lamp bar (including its bisecting chrome bar), and the "BYD",
"比亚迪", and "海豹" badges. It hangs from the backlight's base (x = -2.040: glass
stays on body) and swings up about a lateral axis (80 deg).
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HINGE_X = -2.000                          # decklid hinge axis (the backlight's foot) synchronized with int_tailgate in byd-seal-interior.glb
OPEN_DEG = 80.0
GROUP = ("BYDSeal_Tailgate", "Seal_GateGrp")
NODE = "BYDSeal_Tailgate"

# Whole objects that live in the lid (each holds both sides)
PARTS = (
    "Seal_Decklid", "Seal_Ducktail_Lip", "Seal_Ducktail_Trim",
    "Seal_Badge_BYD_Zh", "Seal_Badge_EV", "Seal_Badge_Seal",
)
SLOGAN = "Seal_Slogan_"                   # the BUILD YOUR DREAMS letters (one object each)
# The bands the shut line cuts: only the middle (|y| < Y_SHUT) goes with the lid; the rest stays on the quarters
CUT = (
    "Seal_Tail_Upper", "Seal_Tailgate_Skin", "Seal_Tail_Housing", "Seal_Tail_Lens",
    "Seal_Tail_Through_Bar", "Seal_Tail_Chrome_Bar",
    "Seal_Tail_Dot_Matrix", "Seal_Lid_ShutLine_Arc",
)
Y_SHUT = 0.600                            # the lid's side shut line at the tail (c1_0515: y 0.58-0.60)

_HINGE = []


def hinge():
    """The hinge axis point: on the centreline at the decklid's height at HINGE_X."""
    if _HINGE:
        return _HINGE[0]
    ob = bpy.data.objects.get("Seal_Decklid") or bpy.data.objects.get(NODE)
    if ob is not None:
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        mw = ob.matrix_world
        tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
        h = tree.ray_cast(Vector((HINGE_X, 0.0, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        z = h.z if h is not None else 0.985
    else:
        z = 0.985
    _HINGE.append(Vector((HINGE_X, 0.0, z - 0.004)))
    return _HINGE[0]


def _link_only(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)


def _group(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def _split_off(name, new_name, cut_planes, keep):
    """Cut the object `name` along `cut_planes` and move the faces `keep(centre)` selects to `new_name`."""
    from carkit import mesh as M
    src = bpy.data.objects.get(name)
    if not src:
        return None
    M.apply_modifiers(src)
    bm = bmesh.new()
    bm.from_mesh(src.data)
    for co, no in cut_planes:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    take = [f for f in bm.faces if keep(f.calc_center_median())]
    if not take:
        bm.free()
        return None
    me2 = bpy.data.meshes.new(new_name + "_mesh")
    vmap, verts, polys, mats, smooth = {}, [], [], [], []
    for f in take:
        idx = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = len(verts)
                verts.append(v.co.copy())
            idx.append(vmap[v.index])
        polys.append(idx)
        mats.append(f.material_index)
        smooth.append(f.smooth)
    me2.from_pydata(verts, [], polys)
    for p, mi, sm in zip(me2.polygons, mats, smooth):
        p.material_index = mi
        p.use_smooth = sm
    for m in src.data.materials:
        me2.materials.append(m)
    bmesh.ops.delete(bm, geom=take, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(src.data)
    bm.free()
    ob2 = bpy.data.objects.new(new_name, me2)
    ob2.matrix_world = src.matrix_world
    for c in src.users_collection:
        c.objects.link(ob2)
    return ob2


def split_bands(y_cut=Y_SHUT):
    made = []
    for n in CUT:
        if bpy.data.objects.get(n + "_C") is None and bpy.data.objects.get(n) is not None:
            sp = _split_off(n, n + "_C",
                            [((0.0, y_cut, 0.0), (0.0, 1.0, 0.0)),
                             ((0.0, -y_cut, 0.0), (0.0, 1.0, 0.0))],
                            lambda c: abs(c.y) < y_cut)
            if sp:
                made.append(sp)
    return made


def split_tail():
    """Hinges the tailgate as BYDSeal_Tailgate with origin at hinge."""
    deck = bpy.data.objects.get("Seal_Decklid")
    if deck is None:
        return bpy.data.objects.get(NODE)

    h = hinge()
    origin = Vector((h.x, 0.0, h.z))

    col_gate = _group(GROUP[1])
    split_bands()

    # Gather lid parts
    lid_obs = []
    for p in PARTS:
        ob = bpy.data.objects.get(p)
        if ob:
            lid_obs.append(ob)
    lid_obs += [o for o in bpy.data.objects if o.name.startswith(SLOGAN)]
    for c in CUT:
        ob = bpy.data.objects.get(c + "_C")
        if ob:
            lid_obs.append(ob)

    from carkit import export as X
    names = []
    for ob in lid_obs:
        _link_only(ob, col_gate)
        names.append(ob.name)
    lid = X.join(NODE, names)
    lid.name = NODE
    lid.data.transform(Matrix.Translation(-origin))
    lid.matrix_world = Matrix.Translation(origin)
    lid["hinge"] = tuple(origin)
    lid["open_deg"] = OPEN_DEG
    return lid


def open_hull(hulls=("Seal_Shell_Shadow",), reach=0.5, x_max=-1.6):
    """Deletes blackout shell behind trunk lid so boot interior is visible."""
    gate = bpy.data.objects.get(NODE)
    if gate is None:
        return 0
    h = hinge()
    mw = Matrix.Translation(Vector(gate.get("hinge", h)))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = gate.evaluated_get(dg)
    me = ev.to_mesh()
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    back = Vector((-1.0, 0.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    total = 0
    for name in hulls:
        sh = bpy.data.objects.get(name)
        if sh is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(sh.data)
        dead = []
        for f in bm.faces:
            p = sh.matrix_world @ f.calc_center_median()
            if p.x > x_max or abs(p.y) > Y_SHUT + 0.005:
                continue
            if tree.ray_cast(p, back, reach)[0] is not None or tree.ray_cast(p, up, reach)[0] is not None:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(sh.data)
        bm.free()
        total += len(dead)
    return total


def set_hatch(deg, card=False):
    """Rotates tailgate node around lateral y axis."""
    h = hinge()
    rot = Matrix.Rotation(math.radians(-deg), 4, 'Y')
    for n in (NODE, "int_tailgate"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n != "int_tailgate"):
            ob.matrix_world = Matrix.Translation(h) @ rot


def build_seal(collection=None, lib=None):
    """Rubber weatherstrip bead surrounding the trunk opening."""
    if collection is None:
        collection = bpy.data.collections.get("Seal_Details") or bpy.context.scene.collection
    if lib is None:
        import seal_materials as MT
        lib = MT.build_library()

    h = hinge()
    pts = [
        (h.x, 0.0, h.z - 0.015),
        (h.x, Y_SHUT - 0.020, h.z - 0.015),
        (-2.360, Y_SHUT - 0.015, 0.760),
        (-2.380, 0.0, 0.760),
    ]
    bm = bmesh.new()
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i+1]
        v0 = bm.verts.new(p0)
        v1 = bm.verts.new(p1)
        bm.edges.new((v0, v1))
        # mirror right
        v0_r = bm.verts.new((p0[0], -p0[1], p0[2]))
        v1_r = bm.verts.new((p1[0], -p1[1], p1[2]))
        bm.edges.new((v0_r, v1_r))

    me = bpy.data.meshes.new("Seal_Trunk_Seal_mesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Seal_Trunk_Seal", me)
    ob.data.materials.append(lib["black_trim"])
    collection.objects.link(ob)

    # Boot compartment carpet liner
    c_bm = bmesh.new()
    b_pts = [
        (-1.600, 0.480, 0.380), (-1.600, -0.480, 0.380),
        (-2.280, -0.480, 0.380), (-2.280, 0.480, 0.380),
    ]
    v_flr = [c_bm.verts.new(p) for p in b_pts]
    c_bm.faces.new(v_flr)
    me_c = bpy.data.meshes.new("Seal_Boot_Floor_mesh")
    c_bm.to_mesh(me_c)
    c_bm.free()
    b_ob = bpy.data.objects.new("Seal_Boot_Floor", me_c)
    b_ob.data.materials.append(lib["black_trim"])
    collection.objects.link(b_ob)

    return [ob, b_ob]


def build_boot(col, lib, half):
    """The boot compartment carpet, side walls, and stainless steel sill plate."""
    from carkit.interior.sweep import grid_mesh
    from carkit import mesh as M
    made = []
    carpet = lib.get("carpet") or lib.get("black_trim")
    steel = lib.get("logo_chrome") or lib.get("trim_chrome")

    X_BULKHEAD = -1.25
    X_MOUTH = -1.92
    Z_TRUNK = 0.40
    Z_DECK = 0.68
    xs = [X_BULKHEAD + (X_MOUTH - X_BULKHEAD) * k / 20.0 for k in range(21)]
    rows = [[(x, min(0.48, half(x, Z_TRUNK)) * j / 10.0, Z_TRUNK) for j in range(11)] for x in xs]
    fl = grid_mesh("int_boot_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)

    w_rows = []
    for x in xs:
        zt = Z_DECK if x > -1.75 else Z_DECK - 0.12 * min(1.0, (-1.75 - x) / 0.17)
        hw = min(0.48, half(x, Z_TRUNK))
        w_rows.append([(x, hw, Z_TRUNK + (zt - Z_TRUNK) * k / 8.0) for k in range(9)])
    wall = grid_mesh("int_boot_wall", w_rows, col, carpet)
    M.orient(wall.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(wall)
    made.append(wall)

    # Rear trunk wall connecting the two side walls at X_MOUTH
    hw_mouth = min(0.48, half(X_MOUTH, Z_TRUNK))
    zt_mouth = Z_DECK - 0.12
    rear_rows = []
    for k in range(9):
        z_curr = Z_TRUNK + (zt_mouth - Z_TRUNK) * k / 8.0
        rear_rows.append([(X_MOUTH, hw_mouth * (1.0 - 2.0 * j / 10.0), z_curr) for j in range(11)])
    rear_wall = grid_mesh("int_boot_rear_wall", rear_rows, col, carpet)
    M.orient(rear_wall.data, lambda c: (-1.0, 0.0, 0.0))
    made.append(rear_wall)

    # Sill plate at the mouth
    ys = [-hw_mouth + 2.0 * hw_mouth * k / 30.0 for k in range(31)]
    s_rows = [[(X_MOUTH + dx, y, Z_TRUNK + dz) for (dx, dz) in ((0.0, -0.003), (0.012, 0.002), (0.035, 0.003))] for y in ys]
    sp = grid_mesh("int_boot_sill", s_rows, col, steel)
    M.orient(sp.data, lambda c: (0.0, 0.0, 1.0))
    made.append(sp)
    return made


def build_liner(col=None, depth=0.015):
    """The lid's inside, for the cabin's GLB (int_tailgate)."""
    from carkit import export as X
    from carkit import mesh as M
    import bmesh
    deck = bpy.data.objects.get("Seal_Decklid") or bpy.data.objects.get("Seal_Rear_Deck")
    if deck is None:
        return None
    col = col or bpy.data.collections.get("Seal_Interior") or bpy.context.scene.collection
    import seal_materials as MT
    lib = MT.build_library()
    liner = lib.get("black_trim") or lib.get("carpet")
    h = hinge()

    dg = bpy.context.evaluated_depsgraph_get()
    me = deck.evaluated_get(dg).to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    deck.to_mesh_clear()
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for v in bm.verts:
        v.co += v.normal * (-depth)
    me_liner = bpy.data.meshes.new("int_tailgate_liner_mesh")
    bm.to_mesh(me_liner)
    bm.free()
    ob = bpy.data.objects.new("int_tailgate", me_liner)
    ob.data.materials.append(liner)
    col.objects.link(ob)
    ob.data.transform(Matrix.Translation(-h))
    ob.matrix_world = Matrix.Translation(h)
    return ob
