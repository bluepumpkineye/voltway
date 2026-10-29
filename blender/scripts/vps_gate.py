"""Voyah Passion S (岚图追光S) liftback tailgate, carpeted boot, and X-ray greenhouse.

Splits the liftback hatch inside `vps_rear.GATE_EDGE` together with its raked
backlight, twin-pod aero spoiler, smoked centre taillight bar with illuminated
'V O Y A H' script, rear LiDAR pill, and CJK/red-S badges into `VoyahPassionS_Tailgate`.
Also builds the carpeted boot (`Z_FLOOR = 0.715`), `int_tailgate` inner liner,
weatherseal, and `VoyahPassionS_Greenhouse` X-ray node.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HINGE = Vector((-1.735, 0.0, 1.522))
OPEN_DEG = 78.0
GROUP = ("VoyahPassionS_Tailgate", "VPS_GateGrp")

PARTS = (
    "VPS_Glass_Wedge", "VPS_Glass_Rear", "VPS_Glass_RearBack", "VPS_Glass_Frit",
    "VPS_Spoiler_Bridge", "VPS_Spoiler_BridgeUnder",
    "VPS_Roof_Blade", "VPS_Roof_BladeShadow", "VPS_Spoiler_Lip", "VPS_Spoiler_Camera",
    "VPS_Lightbar_Housing", "VPS_Lightbar_SealLow", "VPS_Lightbar_SealUp",
    "VPS_Lightbar_Pipe", "VPS_Lightbar_Lens",
    "VPS_Lightbar_Script_V", "VPS_Lightbar_Script_O", "VPS_Lightbar_Script_Y",
    "VPS_Lightbar_Script_A", "VPS_Lightbar_Script_H",
    "VPS_Rear_LidarPill", "VPS_Badge_Brand", "VPS_Badge_Model", "VPS_Badge_SportS",
)


def _components(bm):
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


def _gate_faces(bm, probe=(0.15, 0.96)):
    from vps_rear import rear_view
    tree = rear_view().tree
    bmesh.ops.delete(bm, geom=[f for f in bm.faces
                               if tree.find_nearest(f.calc_center_median())[3] > 0.002],
                     context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.faces.ensure_lookup_table()
    comps = [c for c in _components(bm) if len(c) > 8]
    if len(comps) < 2:
        raise RuntimeError("shut line does not separate the hatch skin: %d piece(s)" % len(comps))

    def dist(c):
        return min(math.hypot(f.calc_center_median().y - probe[0],
                              f.calc_center_median().z - probe[1]) for f in c)
    return min(comps, key=dist)


def split_tail(cap="VPS_Tail_Upper"):
    from carkit import export as X
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
    me = bpy.data.meshes.new("VPS_Tail_Gate_mesh")
    me.from_pydata(verts, [], polys)
    for p, m, s in zip(me.polygons, mats, smooth):
        p.material_index = m
        p.use_smooth = s
    for m in src.data.materials:
        me.materials.append(m)
    gate = bpy.data.objects.new("VPS_Tail_Gate", me)
    gate.matrix_world = src.matrix_world
    _copy_modifiers(src, gate)
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(src.data)
    bm.free()
    col = bpy.data.collections.get(GROUP[1]) or bpy.data.collections.new(GROUP[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    col.objects.link(gate)
    names = [gate.name, rim.name]
    _link_only(rim, col)
    for n in PARTS:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        _link_only(ob, col)
        names.append(ob.name)
    hatch = X.join("VPS_Tailgate", names)
    hatch.data.transform(Matrix.Translation(-HINGE))
    hatch.matrix_world = Matrix.Translation(HINGE)
    hatch["hinge"] = tuple(HINGE)
    hatch["open_deg"] = OPEN_DEG
    return hatch


def set_hatch(deg, card=True):
    rot = Matrix.Rotation(math.radians(deg), 4, 'Y')
    for n in ("VPS_Tailgate", "int_tailgate"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n == "VPS_Tailgate"):
            ob.matrix_world = Matrix.Translation(HINGE) @ rot


def open_hull(hulls=("VPS_Shell_Shadow", "VPS_Shell_Shadow_R"), reach=0.88, x_max=-1.68):
    gate = bpy.data.objects.get("VPS_Tailgate")
    if gate is None:
        return 0
    dg = bpy.context.evaluated_depsgraph_get()
    ev = gate.evaluated_get(dg)
    me = ev.to_mesh()
    mw = Matrix.Translation(Vector(gate.get("hinge", HINGE)))
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices],
                                [list(p.vertices) for p in me.polygons])
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
            if p.x > x_max or abs(p.y) > 0.72 or p.z < 0.70:
                continue
            if tree.ray_cast(p, back, reach)[0] is not None or tree.ray_cast(p, up, 0.55)[0] is not None:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(sh.data)
        bm.free()
        total += len(dead)
    return total


def cut_underlay(under="VPS_Roof_Rear_Black", x_front=-1.72, half=0.62):
    from carkit import mesh as M
    ob = bpy.data.objects.get(under)
    if ob is None:
        return 0
    M.apply_modifiers(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for co, no in (((x_front, 0.0, 0.0), (1.0, 0.0, 0.0)),
                   ((0.0, half, 0.0), (0.0, 1.0, 0.0)),
                   ((0.0, -half, 0.0), (0.0, 1.0, 0.0))):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    dead = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.x < x_front and abs(c.y) < half:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    for poly in ob.data.polygons:
        poly.use_smooth = True
    return len(dead)


# ------------------------------------------------------------------- the boot
Z_FLOOR = 0.715
X_MOUTH, X_BULK = -2.42, -1.56
WALL_Y = None


def _wall_y():
    global WALL_Y
    if WALL_Y is None:
        from carkit.geom import Curve
        WALL_Y = Curve([
            (-2.44, 0.595), (-2.33, 0.680), (-2.20, 0.775), (-2.06, 0.812),
            (-1.96, 0.778), (-1.88, 0.705), (-1.82, 0.675), (-1.54, 0.675),
        ], mode="pchip")
    return WALL_Y


def _mat(name, base, rough=0.6, **kw):
    from carkit import materials as MB
    m = bpy.data.materials.get(name)
    if m is None:
        m, nt, b = MB.mat(name)
        MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=rough, **kw)
    return m


def _gate_bottom(y):
    import vps_rear as RR
    pts = [(0.0, 0.743)] + list(RR.GATE_EDGE)
    y = abs(y)
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1 and y1 > y0:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def build_boot(col=None, lib=None):
    import vps_rear as RR
    from carkit import mesh as M
    from carkit.interior import cabin as CB
    from carkit.interior.sweep import grid_mesh
    col = col or bpy.data.collections["VPS_Interior"]
    carpet = _mat("INT_Boot_Carpet", (0.030, 0.030, 0.032), 0.96, specular=0.2)
    trim = _mat("INT_Boot_Trim", (0.040, 0.040, 0.044), 0.62, specular=0.35)
    steel = _mat("INT_Boot_Plate", (0.26, 0.27, 0.285), 0.38, specular=0.5)
    wy = _wall_y()
    made = []
    xs = [X_MOUTH + (X_BULK - X_MOUTH) * k / 44.0 for k in range(45)]
    rows = [[(x, wy(x) * j / 12.0, Z_FLOOR) for j in range(13)] for x in xs]
    fl = grid_mesh("int_boot_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)
    pts = [(-2.43 + (-1.56 + 2.43) * k / 44.0, 0.0) for k in range(45)]
    pts = [(x, wy(x)) for (x, _) in pts]
    made.append(CB.wall(col, carpet, pts, lambda x, y: Z_FLOOR, lambda x, y: 0.92, nz=3,
                        name="int_boot_wall", facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, trim, pts, lambda x, y: 0.92, lambda x, y: 1.12, nz=3,
                        name="int_boot_trim", facing=(0.0, -1.0, 0.0)))
    ys = [0.62 * k / 40.0 for k in range(41)]
    shelf, plate = [], []
    for y in ys:
        zg = _gate_bottom(y)
        p, _n = RR.on_tail(y, zg + 0.004)
        xo = p[0] + 0.012
        zs = max(Z_FLOOR + 0.012, zg - 0.024)
        shelf.append([(xo, y, zs), (xo + 0.105, y, zs), (xo + 0.105, y, Z_FLOOR)])
        if 0.064 <= y <= 0.56:
            plate.append([(xo + 0.020, y, zs + 0.003), (xo + 0.092, y, zs + 0.003)])
    sh = grid_mesh("int_boot_sill", shelf, col, trim)
    M.orient(sh.data, lambda c: (0.6, 0.0, 1.0))
    M.mirror_y(sh)
    made.append(sh)
    pl = grid_mesh("int_boot_plate", plate, col, steel)
    M.orient(pl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(pl)
    made.append(pl)
    return made


# ------------------------------------------------------ the hatch's inner side
RIM_DEPTH = 0.034
INSIDE = Vector((-1.90, 0.0, 1.05))


def _outward(bm, faces):
    vn = {}
    for f in faces:
        a = f.calc_area()
        for v in f.verts:
            vn[v.index] = vn.get(v.index, Vector()) + f.normal * a
    sgn = 1.0 if sum((f.calc_center_median() - INSIDE).dot(f.normal) for f in faces) > 0 else -1.0
    return {k: n.normalized() * sgn for k, n in vn.items()}


def _snap(co):
    q = co.copy()
    if abs(q.y) < 0.008:
        q.y = 0.0
    return q


def _is_window(m):
    return m.z > 1.18 and abs(m.y) < 0.60


def _boundary(faces):
    out = []
    for f in faces:
        for e in f.edges:
            if e.is_boundary and e not in out:
                a, b = e.verts
                if abs(a.co.y) < 0.008 and abs(b.co.y) < 0.008:
                    continue
                out.append(e)
    return out


def _wall(out, edges, vn, depth, keep, vcache_s, vcache_l, inward_ref):
    def S_v(v):
        if v.index not in vcache_s:
            vcache_s[v.index] = out.verts.new(_snap(v.co))
        return vcache_s[v.index]

    def L_v(v):
        if v.index not in vcache_l:
            vcache_l[v.index] = out.verts.new(_snap(v.co - vn[v.index] * depth))
        return vcache_l[v.index]

    n = 0
    for e in edges:
        a, b = e.verts
        m = (a.co + b.co) * 0.5
        if not keep(m):
            continue
        q = [S_v(a), S_v(b), L_v(b), L_v(a)]
        face = out.faces.new(q)
        cen = face.calc_center_median()
        if face.normal.dot(inward_ref(cen)) < 0.0:
            face.normal_flip()
        n += 1
    return n


def rim_wall(bm, faces, collection=None, depth=RIM_DEPTH):
    vn = _outward(bm, faces)
    out = bmesh.new()
    hc = sum((f.calc_center_median() for f in faces), Vector()) / len(faces)
    _wall(out, _boundary(faces), vn, depth, lambda m: not _is_window(m), {}, {},
          lambda c: hc - c)
    me = bpy.data.meshes.new("VPS_Tail_Rim_mesh")
    out.to_mesh(me)
    out.free()
    me.materials.append(bpy.data.materials["M_Paint_VPS_RosyMistPink"])
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("VPS_Tail_Rim", me)
    from carkit import mesh as M
    M.mirror_y(ob)
    return ob


def build_liner(col=None, depth=RIM_DEPTH):
    from carkit import mesh as M
    col = col or bpy.data.collections["VPS_Interior"]
    src = bpy.data.objects["VPS_Tail_Upper"]
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
    ring = [(e.verts[0].co + e.verts[1].co) * 0.5 for e in edges if _is_window((e.verts[0].co + e.verts[1].co) * 0.5)]
    wc = sum(ring, Vector()) / max(1, len(ring))
    _wall(out, edges, vn, depth, _is_window, sv, lv, lambda c: wc - c)
    me = bpy.data.meshes.new("int_tailgate_mesh")
    out.to_mesh(me)
    out.free()
    bm.free()
    liner = _mat("INT_Hatch_Liner", (0.030, 0.030, 0.033), 0.7, specular=0.3)
    me.materials.append(liner)
    for p in me.polygons:
        p.use_smooth = True
    me.transform(Matrix.Translation(-HINGE))
    ob = bpy.data.objects.new("int_tailgate", me)
    ob.matrix_world = Matrix.Translation(HINGE)
    col.objects.link(ob)
    M.mirror_y(ob)
    return ob


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
    col = col or bpy.data.collections["VPS_Interior"]
    satin = bpy.data.materials["INT_Satin_Black"]
    rubber = bpy.data.materials["INT_Rubber"]
    steel = bpy.data.materials["INT_Boot_Plate"]
    lamp = bpy.data.materials.get("INT_Boot_Lamp")
    if lamp is None:
        lamp = _mat("INT_Boot_Lamp", (0.9, 0.9, 0.9), 0.4)
        b = next(n for n in lamp.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Emission Color"].default_value = (1.0, 0.98, 0.94, 1.0)
        b.inputs["Emission Strength"].default_value = 7.0
    wy = _wall_y()
    made = []
    xm, zm = -2.06, 0.855
    y = wy(xm + 0.08) - 0.003
    made.append(_box("int_boot_module", xm, xm + 0.160, y - 0.006, y + 0.012, zm - 0.040, zm + 0.040, satin, col))
    made.append(_box("int_boot_hook", xm + 0.014, xm + 0.038, y - 0.010, y - 0.004, zm - 0.028, zm + 0.022, rubber, col))
    made.append(_box("int_boot_socket", xm + 0.062, xm + 0.086, y - 0.009, y - 0.004, zm - 0.012, zm + 0.012, rubber, col))
    made.append(_box("int_boot_lamp", xm + 0.104, xm + 0.150, y - 0.007, y - 0.004, zm - 0.022, zm + 0.020, lamp, col))
    yr = -(wy(xm + 0.08) - 0.003)
    made.append(_box("int_boot_lamp_R", xm + 0.104, xm + 0.150, yr + 0.004, yr + 0.007, zm - 0.022, zm + 0.020, lamp, col))
    made.append(_box("int_boot_pull", -2.24, -2.19, -0.050, 0.050, Z_FLOOR - 0.004, Z_FLOOR + 0.0015, rubber, col))
    made.append(_box("int_boot_latch", -2.44, -2.37, -0.056, 0.056, 0.718, 0.735, steel, col))
    return made


def build_seal(collection="VPS_Details"):
    import vps_rear as RR
    from carkit.interior.sweep import tube, ellipse
    col = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
    pts, nrm = RR.gate_path()
    while len(pts) > 2 and pts[0][1] < 0.0:
        pts, nrm = pts[1:], nrm[1:]
    path = [tuple(Vector(p) - Vector(n).normalized() * 0.011) for p, n in zip(pts, nrm)]
    satin = bpy.data.materials["M_Black_Satin"]
    half = tube("VPS_Boot_SealHalf", path, ellipse(0.0075, 0.0075, 10), col, satin,
                closed=False, lateral=(1.0, 0.0, 0.0))
    other = tube("VPS_Boot_SealHalfR", [(x, -y, z) for (x, y, z) in path], ellipse(0.0075, 0.0075, 10),
                 col, satin, closed=False, lateral=(1.0, 0.0, 0.0))
    return [half, other]


# ----------------------------------------------------------------- the greenhouse
GREENHOUSE = (
    "VPS_Roof_Paint", "VPS_Roof_Rail", "VPS_Roof_Edge",
    "VPS_Glass_Roof", "VPS_Glass_Windshield", "VPS_Glass_Quarter",
)
GREENHOUSE_GROUP = ("VoyahPassionS_Greenhouse", "VPS_GreenhouseGrp")


def split_greenhouse():
    col = bpy.data.collections.get(GREENHOUSE_GROUP[1]) or bpy.data.collections.new(GREENHOUSE_GROUP[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in GREENHOUSE:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        _link_only(ob, col)
    return col


def tailgate_groups():
    return [GROUP]


def greenhouse_groups():
    return [GREENHOUSE_GROUP]
