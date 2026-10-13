"""Zeekr 7X tailgate and boot.

The hatch is the tail cap inside the shut line (zx_rear.GATE_PX, run on up the cap's side to
its top) with everything that sits in it: the backlight and its wedge, the lamp bar and its
camera pod, the lettering. It hangs from the roof's trailing edge and swings up about a lateral
axis (c3_0047: ~80 degrees on two gas struts). The boot behind it is new, from the opening
photographs (c3_0050-58: black loop-pile carpet on the floor, the walls and the rear seat
backs, a ribbed sill plate, a lid pull, a bag hook, a 12 V socket, a lamp, speaker grilles).

    import zx_gate as RG
    RG.cut_underlay()        # the backlight's footprint out of the roof's black underlay
    RG.split_tail()          # ZX_Tailgate off the cap; the node Zeekr7X_Tailgate
    RG.open_hull()           # the dark hull behind it
    RG.set_hatch(80.0)       # preview it open (degrees)

Car axes: +x forward, +y left, z up. The hatch opens by rotating about +y.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HINGE = Vector((-1.930, 0.0, 1.385))     # the roof's trailing edge, on the centreline
OPEN_DEG = 80.0
GROUP = ("Zeekr7X_Tailgate", "ZX_GateGrp")
PAINT = "M_Paint_ZX_Blue"

# whole objects that live in the hatch (each holds both sides)
PARTS = (
    "ZX_Glass_Rear", "ZX_Glass_Wedge_Rear",
    "ZX_Lightbar_Lens_C", "ZX_Lightbar_Edge_C", "ZX_Lightbar_SealLow_C", "ZX_Lightbar_SealUp_C",
    "ZX_Lightbar_Pod", "ZX_Rear_Camera", "ZX_Badge_Maker", "ZX_Badge_Model",
)
# the lamp bar's pieces: it sweeps round each corner onto the quarter panel, beyond the hatch's
# side edge (y 0.795): only its middle goes with the hatch
LAMP = ("ZX_Lightbar_Lens", "ZX_Lightbar_Edge", "ZX_Lightbar_SealLow", "ZX_Lightbar_SealUp")
Y_SHUT = 0.795


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


def _link_only(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)


def _group(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def _gate_faces(bm, probe=(0.15, 0.92)):
    """The faces of the hatch's skin in the cap's sheet. The exact boolean that cut the shut line
    left its walls and floor, a groove 30 mm deep that ties hatch and body together: those go
    (bm is changed), keeping what lies on the cap's own surface; the shut line then separates
    the sheet in two."""
    from zx_rear import rear_view
    tree = rear_view().tree
    bmesh.ops.delete(bm, geom=[f for f in bm.faces
                               if tree.find_nearest(f.calc_center_median())[3] > 0.002],
                     context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.faces.ensure_lookup_table()
    comps = [c for c in _components(bm) if len(c) > 8]
    if len(comps) < 2:
        raise RuntimeError("the shut line does not separate the hatch's skin: %d piece(s)" % len(comps))

    def dist(c):
        return min(math.hypot(f.calc_center_median().y - probe[0],
                              f.calc_center_median().z - probe[1]) for f in c)
    return min(comps, key=dist)


# ------------------------------------------- panes and bars, split at the hatch's edges
def _split_off(name, new_name, cut_planes, keep):
    """Cut the object `name` (modifiers baked) along `cut_planes` ((point, normal) pairs) and
    move the faces `keep(centre)` selects to a new object `new_name` (same transform and
    materials, same collections). Returns the new object."""
    from carkit import mesh as M
    src = bpy.data.objects[name]
    M.apply_modifiers(src)
    bm = bmesh.new()
    bm.from_mesh(src.data)
    for co, no in cut_planes:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    take = [f for f in bm.faces if keep(f.calc_center_median())]
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


def split_wedge(name="ZX_Glass_Wedge", x_cut=None):
    """The dark glass wedge along the C-pillar runs on forward of the hatch's hinge, under the
    roof rail: only the part behind the hinge goes with the hatch. The object is cut at the
    hinge's x into ZX_Glass_Wedge (stays) and ZX_Glass_Wedge_Rear (the hatch's)."""
    x_cut = HINGE.x if x_cut is None else x_cut
    return _split_off(name, name + "_Rear", [((x_cut, 0.0, 0.0), (1.0, 0.0, 0.0))],
                      lambda c: c.x < x_cut)


def split_lamp(y_cut=Y_SHUT):
    """The lamp bar's middle (|y| < y_cut) becomes <name>_C, the hatch's; its swept ends stay on
    the quarter panels."""
    made = []
    for n in LAMP:
        if bpy.data.objects.get(n + "_C") is None:
            made.append(_split_off(n, n + "_C",
                                   [((0.0, y_cut, 0.0), (0.0, 1.0, 0.0)),
                                    ((0.0, -y_cut, 0.0), (0.0, 1.0, 0.0))],
                                   lambda c: abs(c.y) < y_cut))
    return made


def split_tail(cap="ZX_Tail_Upper"):
    """Cut the hatch's skin off the tail cap, gather everything that sits in the hatch into one
    node with its origin on the hinge."""
    from carkit import export as X
    if bpy.data.objects.get("ZX_Glass_Wedge_Rear") is None:
        split_wedge()
    split_lamp()
    src = bpy.data.objects[cap]
    bm = bmesh.new()
    bm.from_mesh(src.data)
    faces = _gate_faces(bm)
    rim = rim_wall(bm, faces)
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
    me = bpy.data.meshes.new("ZX_Tail_Gate_mesh")
    me.from_pydata(verts, [], polys)
    for p, m, s in zip(me.polygons, mats, smooth):
        p.material_index = m
        p.use_smooth = s
    for m in src.data.materials:
        me.materials.append(m)
    gate = bpy.data.objects.new("ZX_Tail_Gate", me)
    gate.matrix_world = src.matrix_world
    _copy_modifiers(src, gate)
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(src.data)
    bm.free()
    col = _group(GROUP[1])
    col.objects.link(gate)
    names = [gate.name, rim.name]
    _link_only(rim, col)
    for n in PARTS:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("hatch part %s missing from the build" % n)
        _link_only(ob, col)
        names.append(ob.name)
    hatch = X.join("ZX_Tailgate", names)
    hatch.data.transform(Matrix.Translation(-HINGE))
    hatch.matrix_world = Matrix.Translation(HINGE)
    hatch["hinge"] = tuple(HINGE)
    hatch["open_deg"] = OPEN_DEG
    return hatch


def set_hatch(deg, card=True):
    """Swing the hatch (and its liner, if built) `deg` open about its hinge."""
    rot = Matrix.Rotation(math.radians(deg), 4, 'Y')
    for n in ("ZX_Tailgate", "int_tailgate"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n == "ZX_Tailgate"):
            ob.matrix_world = Matrix.Translation(HINGE) @ rot


def open_hull(hulls=("ZX_Shell_Shadow", "ZX_Shell_Shadow_R"), reach=0.45, x_max=-1.8):
    """Delete the hull faces that sit in front of the hatch's skin (a ray straight back along -x
    hits it), so the boot shows through an open hatch."""
    gate = bpy.data.objects["ZX_Tailgate"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = gate.evaluated_get(dg)
    me = ev.to_mesh()
    mw = Matrix.Translation(Vector(gate.get("hinge", HINGE)))     # the closed pose
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices],
                                [list(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    back = Vector((-1.0, 0.0, 0.0))
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
            if p.x > x_max or abs(p.y) > 0.78:
                continue
            if tree.ray_cast(p, back, reach)[0] is not None:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(sh.data)
        bm.free()
        total += len(dead)
    return total


def _outline_cutter(name_obj, inset, front=0.03, back=0.06):
    """Prisms of a pane's outlines (one per boundary loop), `inset` smaller, swept along the
    pane's outward normal: the cutters for the sheet behind it."""
    from carkit import cut as C
    import zx_openings as OP
    src = bpy.data.objects[name_obj]
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    me.transform(src.matrix_world)
    cutters = []
    for loop in OP._loops(me):
        if len(loop) < 8:
            continue
        # this loop's own faces: the normal is read off the whole pane, outward = away from
        # the cabin's middle
        n = Vector()
        for p in me.polygons:
            n += p.normal * p.area
        n.normalize()
        centre = sum(loop, Vector()) / len(loop)
        if n.dot(centre - Vector((-0.6, 0.0, 0.9))) < 0.0:
            n = -n
        m = len(loop)
        pts = []
        for i, p in enumerate(loop):
            t = (loop[(i + 1) % m] - loop[i - 1]).normalized()
            w = n.cross(t).normalized()
            if w.dot(centre - p) < 0.0:
                w = -w
            pts.append(tuple(p + w * inset))
        cutters.append(C.prism_dir("_glasscut_%s_%d" % (name_obj, len(cutters)), pts, tuple(n),
                                   back=back, front=front))
    bpy.data.meshes.remove(me)
    return cutters


def cut_underlay(under="ZX_Roof_Rear_Black", inset=0.0025):
    """Take the backlight's and the wedge's footprints out of the roof's black underlay, which
    would otherwise stay where the glass was when the hatch swings up (the same pane left behind
    as the doors'). Exact cuts with the panes' own outlines. Run before split_tail().
    Returns (faces before, faces after, faces pruned)."""
    from carkit import cut as C
    from carkit import mesh as M
    if bpy.data.objects.get("ZX_Glass_Wedge_Rear") is None:
        split_wedge()
    ob = bpy.data.objects[under]
    M.apply_modifiers(ob)
    sheet = C.sheet_bvh(ob)
    cutters = _outline_cutter("ZX_Glass_Rear", inset)
    cutters += _outline_cutter("ZX_Glass_Wedge_Rear", inset)
    before, after = C.difference(ob, cutters, "bw_")
    pruned = C.prune_off_sheet(ob, sheet)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    return before, after, pruned


# ------------------------------------------------------------------- the boot
Z_FLOOR = 0.665
X_SEAT = -1.286                  # the rear seat backs' rear face
X_MOUTH = -2.318                 # the sill plate's inner edge
WALL_Y = None


def _wall_y():
    """The boot's half-width by x: the wheelhouses' inner face (|y| 0.672) from the seats back
    to the arch's end, a bulge behind it, a pinch at the opening."""
    global WALL_Y
    if WALL_Y is None:
        from carkit.geom import Curve
        WALL_Y = Curve([(-2.34, 0.692), (-2.28, 0.726), (-2.15, 0.746), (-2.02, 0.736),
                        (-1.94, 0.706), (-1.88, 0.674), (-1.30, 0.674)], mode="pchip")
    return WALL_Y


def _mat(name, base, rough=0.6, **kw):
    from carkit import materials as MB
    m = bpy.data.materials.get(name)
    if m is None:
        m, nt, b = MB.mat(name)
        MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=rough, **kw)
    return m


def build_boot(col=None, lib=None):
    """The boot behind the hatch, in the cabin's collection (baked with it): black loop-pile
    carpet on the floor, the walls and the seat backs' rear faces, the ribbed sill plate. Hidden
    behind the closed hatch."""
    from carkit import mesh as M
    from carkit.interior import cabin as CB
    from carkit.interior.sweep import grid_mesh
    col = col or bpy.data.collections["ZX_Interior"]
    carpet = _mat("INT_Boot_Carpet", (0.026, 0.026, 0.028), 0.96, specular=0.2)
    plate = _mat("INT_Boot_Plate", (0.030, 0.030, 0.034), 0.55, specular=0.35)
    wy = _wall_y()
    made = []
    # floor
    xs = [X_MOUTH + (X_SEAT - X_MOUTH) * k / 44.0 for k in range(45)]
    rows = [[(x, wy(x) * j / 12.0, Z_FLOOR) for j in range(13)] for x in xs]
    fl = grid_mesh("int_boot_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)
    # side walls: carpet from the floor up to the C-pillar trim's lower edge
    pts = [(X_MOUTH + (X_SEAT - X_MOUTH) * k / 44.0, 0.0) for k in range(45)]
    pts = [(x, wy(x)) for (x, _) in pts]
    made.append(CB.wall(col, carpet, pts, lambda x, y: Z_FLOOR, lambda x, y: 1.00, nz=4,
                        name="int_boot_wall", facing=(0.0, -1.0, 0.0)))
    # the rear faces of the seat backs, in carpet, hugging the seats' shells
    made.append(_seatback_carpet(col, carpet))
    # the sill plate: ribbed black plastic along the opening's bottom edge (c3_0053)
    ys = [-0.62 + 1.24 * k / 40.0 for k in range(41)]
    rows = []
    for y in ys:
        row = []
        for (dx, dz) in ((0.000, 0.0), (0.020, 0.0030), (0.080, 0.0050), (0.130, 0.0020), (0.150, -0.002)):
            row.append((X_MOUTH - 0.062 + dx, y, Z_FLOOR + 0.004 + dz))
        rows.append(row)
    sp = grid_mesh("int_boot_sill", rows, col, plate)
    M.orient(sp.data, lambda c: (0.0, 0.0, 1.0))
    made.append(sp)
    return made


def _seatback_carpet(col, mat):
    """A carpet panel on the rear seats' rear faces: shrink-wrapped by rays from behind."""
    from carkit.interior.sweep import grid_mesh
    from carkit import mesh as M
    shells = [o for o in col.objects if o.type == 'MESH' and o.name.startswith("int_seat_R")
              and "_Back_" in o.name] + [o for o in col.objects if o.name == "int_rear_centre_back"]
    verts, polys = [], []
    for o in shells:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    tree = BVHTree.FromPolygons(verts, polys)
    rows = []
    zs = [Z_FLOOR + (1.215 - Z_FLOOR) * k / 14.0 for k in range(15)]
    ys = [-0.660 + 1.320 * j / 33.0 for j in range(34)]
    for z in zs:
        row = []
        for y in ys:
            h = tree.ray_cast(Vector((-1.80, y, z)), Vector((1.0, 0.0, 0.0)), 1.0)[0]
            x = (h.x - 0.006) if h is not None else X_SEAT
            row.append((min(x, X_SEAT + 0.01), y, z))
        rows.append(row)
    ob = grid_mesh("int_boot_seatback", rows, col, mat)
    M.orient(ob.data, lambda c: (-1.0, 0.0, 0.0))
    return ob


# ------------------------------------------------------ the hatch's inner side
RIM_DEPTH = 0.034
INSIDE = Vector((-1.9, 0.0, 0.95))       # a point in the cabin, for "outward"


def _outward(bm, faces):
    """Vertex normals of the hatch's skin, outward, keyed by vertex index."""
    vn = {}
    for f in faces:
        a = f.calc_area()
        for v in f.verts:
            vn[v.index] = vn.get(v.index, Vector()) + f.normal * a
    sgn = 1.0 if sum((f.calc_center_median() - INSIDE).dot(f.normal) for f in faces) > 0 else -1.0
    return {k: n.normalized() * sgn for k, n in vn.items()}


def _snap(co):
    """Pull the centreline's vertices onto y = 0 so the Mirror welds them."""
    q = co.copy()
    if abs(q.y) < 0.008:
        q.y = 0.0
    return q


def _is_window(m):
    """A boundary point of the skin that borders the backlight (the rest of the boundary is the
    shut line)."""
    return m.z > 1.05 and abs(m.y) < 0.76


def _boundary(faces):
    out = []
    for f in faces:
        for e in f.edges:
            if e.is_boundary and e not in out:
                a, b = e.verts
                if abs(a.co.y) < 0.008 and abs(b.co.y) < 0.008:
                    continue                           # the centreline seam
                out.append(e)
    return out


def _wall(out, edges, vn, depth, keep, vcache_s, vcache_l, inward_ref):
    """Quads from the skin's boundary edges `keep` selects, back by `depth`."""
    def S(v):
        if v.index not in vcache_s:
            vcache_s[v.index] = out.verts.new(_snap(v.co))
        return vcache_s[v.index]

    def Lv(v):
        if v.index not in vcache_l:
            vcache_l[v.index] = out.verts.new(_snap(v.co - vn[v.index] * depth))
        return vcache_l[v.index]
    n = 0
    for e in edges:
        a, b = e.verts
        m = (a.co + b.co) * 0.5
        if not keep(m):
            continue
        q = [S(a), S(b), Lv(b), Lv(a)]
        face = out.faces.new(q)
        cen = face.calc_center_median()
        if face.normal.dot(inward_ref(cen)) < 0.0:
            face.normal_flip()
        n += 1
    return n


def rim_wall(bm, faces, collection=None, depth=RIM_DEPTH):
    """The hatch's return flange: the skin's outer edge turned in by `depth`, painted. (The
    window's reveal is the liner's.)"""
    vn = _outward(bm, faces)
    out = bmesh.new()
    hc = sum((f.calc_center_median() for f in faces), Vector()) / len(faces)
    _wall(out, _boundary(faces), vn, depth, lambda m: not _is_window(m), {}, {},
          lambda c: hc - c)
    me = bpy.data.meshes.new("ZX_Tail_Rim_mesh")
    out.to_mesh(me)
    out.free()
    me.materials.append(bpy.data.materials[PAINT])
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("ZX_Tail_Rim", me)
    from carkit import mesh as M
    M.mirror_y(ob)
    return ob


def build_liner(col=None, depth=RIM_DEPTH):
    """The hatch's inside, for the cabin's GLB: a dark liner `depth` behind the skin's whole
    sheet, round the backlight, with the window's reveal. Its origin is the hinge, so it swings
    with the hatch (int_tailgate)."""
    from carkit import mesh as M
    col = col or bpy.data.collections["ZX_Interior"]
    src = bpy.data.objects["ZX_Tail_Upper"]
    bm = bmesh.new()
    bm.from_mesh(src.data)
    faces = _gate_faces(bm)
    vn = _outward(bm, faces)
    out = bmesh.new()
    lv, sv = {}, {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v.index not in lv:
                lv[v.index] = out.verts.new(_snap(v.co - vn[v.index] * depth))
            vs.append(lv[v.index])
        out.faces.new(vs[::-1])
    edges = _boundary(faces)
    ring = [(e.verts[0].co + e.verts[1].co) * 0.5 for e in edges
            if _is_window((e.verts[0].co + e.verts[1].co) * 0.5)]
    wc = sum(ring, Vector()) / len(ring)
    _wall(out, edges, vn, depth, _is_window, sv, lv, lambda c: wc - c)
    me = bpy.data.meshes.new("int_tailgate_mesh")
    out.to_mesh(me)
    out.free()
    bm.free()
    liner = _mat("INT_Hatch_Liner", (0.026, 0.026, 0.030), 0.7, specular=0.3)
    me.materials.append(liner)
    for p in me.polygons:
        p.use_smooth = True
    me.transform(Matrix.Translation(-HINGE))
    ob = bpy.data.objects.new("int_tailgate", me)
    ob.matrix_world = Matrix.Translation(HINGE)
    col.objects.link(ob)
    M.mirror_y(ob)
    return ob


# ------------------------------------------------------- boot fittings and seal
def _box(name, x0, x1, y0, y1, z0, z1, mat, col, smooth=False):
    from carkit import mesh as M
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, v, f, col, mat, smooth=smooth)
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    M.orient(ob.data, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))
    return ob


def build_boot_details(col=None):
    """Small things on the boot's walls and floor (c3_0053, c3_0055): on the left wall a module
    with a bag hook, a 12 V socket and a lit lamp; a speaker grille low on each wall; two
    tie-down hooks; the floor's recessed lid pull."""
    col = col or bpy.data.collections["ZX_Interior"]
    satin = bpy.data.materials["INT_Satin_Black"]
    rubber = bpy.data.materials["INT_Rubber"]
    steel = bpy.data.materials["INT_Boot_Plate"]
    spk = bpy.data.materials["INT_Speaker"] if "INT_Speaker" in bpy.data.materials else satin
    lamp = bpy.data.materials.get("INT_Boot_Lamp")
    if lamp is None:
        lamp = _mat("INT_Boot_Lamp", (0.9, 0.9, 0.9), 0.4)
        b = next(n for n in lamp.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Emission Color"].default_value = (1.0, 0.98, 0.94, 1.0)
        b.inputs["Emission Strength"].default_value = 7.0
    wy = _wall_y()
    made = []
    xm, zm = -2.020, 0.905
    y = wy(xm + 0.08) - 0.003
    # left: the module, the hook's slot, the socket's cap, the lamp
    made.append(_box("int_boot_module", xm, xm + 0.200, y - 0.006, y + 0.012, zm - 0.036, zm + 0.036,
                     satin, col))
    made.append(_box("int_boot_hook", xm + 0.014, xm + 0.060, y - 0.012, y - 0.004, zm - 0.026,
                     zm + 0.020, rubber, col))
    made.append(_box("int_boot_socket", xm + 0.090, xm + 0.116, y - 0.009, y - 0.004, zm - 0.013,
                     zm + 0.013, rubber, col))
    made.append(_box("int_boot_lamp", xm + 0.140, xm + 0.186, y - 0.007, y - 0.004, zm - 0.022,
                     zm + 0.020, lamp, col))
    # a speaker grille low on each wall, behind the arch (c3_0053)
    for s in (1.0, -1.0):
        xg = -2.080
        yg = s * (wy(xg + 0.09) - 0.003)
        y0, y1 = (yg - 0.004, yg + 0.004) if s > 0 else (yg - 0.004, yg + 0.004)
        made.append(_box("int_boot_speaker%s" % ("L" if s > 0 else "R"), xg, xg + 0.180,
                         min(y0, y1), max(y0, y1), 0.700, 0.860, spk, col))
    # tie-down hooks on the floor's edge and the wall (the two L-shaped hooks)
    for s in (1.0, -1.0):
        yh = s * (wy(-1.70) - 0.002)
        made.append(_box("int_boot_tie%s" % ("L" if s > 0 else "R"), -1.760, -1.722,
                         min(yh, yh - s * 0.006), max(yh, yh - s * 0.006), Z_FLOOR + 0.020,
                         Z_FLOOR + 0.058, steel, col))
    # the floor's lid pull: a recessed rounded grip near the sill
    made.append(_box("int_boot_pull", -2.225, -2.170, -0.062, 0.062, Z_FLOOR - 0.003, Z_FLOOR + 0.0015,
                     rubber, col))
    return made


def build_seal(collection="ZX_Details"):
    """A black bead behind the shut line the whole way round the hatch, which shows when it is
    open and fills the gap when it is shut."""
    import zx_rear as RR
    from carkit.interior.sweep import tube, ellipse
    col = bpy.data.collections[collection]
    pts, nrm = RR.gate_path()
    if pts[0][1] > pts[1][1]:                  # the slot starts across the centreline
        pts, nrm = pts[1:], nrm[1:]
    path = [tuple(Vector(p) - Vector(n).normalized() * 0.011) for p, n in zip(pts, nrm)]
    satin = bpy.data.materials["M_Black_Satin"]
    half = tube("ZX_Boot_SealHalf", path, ellipse(0.0075, 0.0075, 10), col, satin,
                closed=False, lateral=(1.0, 0.0, 0.0))
    other = tube("ZX_Boot_SealHalfR", [(x, -y, z) for (x, y, z) in path], ellipse(0.0075, 0.0075, 10),
                 col, satin, closed=False, lateral=(1.0, 0.0, 0.0))
    return [half, other]


# ----------------------------------------------------------------- the greenhouse
GREENHOUSE = ("ZX_Roof_Paint", "ZX_Roof_Rail", "ZX_Glass_Roof", "ZX_Glass_Windshield",
              "ZX_Glass_Quarter", "ZX_Glass_Wedge", "ZX_Quarter_Pillar", "ZX_Pillar_Foot")
GREENHOUSE_GROUP = ("Zeekr7X_Greenhouse", "ZX_GreenhouseGrp")


def split_greenhouse():
    """The roof, the A-pillars and rails and the panes of glass above the belt become a node of
    their own, so the viewer's X-ray tab can turn it to a ghost the way HIMA's showroom does (a
    pre-split twin of the upper body)."""
    col = _group(GREENHOUSE_GROUP[1])
    for n in GREENHOUSE:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("greenhouse part %s missing from the build" % n)
        _link_only(ob, col)
    return col
