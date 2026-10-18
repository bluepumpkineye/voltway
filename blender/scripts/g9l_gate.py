"""XPeng G9L tailgate and boot.

The hatch is the whole rear of the car above the smile shut line: the backlight with the roof spoiler
overhanging it, the lamp bar's middle (the bar sweeps round each corner onto the quarter panels,
beyond the hatch's side edge), the painted gate with its lettering, camera and plate. It hangs from
the roof's trailing edge and swings up about a lateral axis on two gas struts (Autohome c3_0156/57:
about 80 degrees, the struts at its sides, a black rubber seal round the opening, a ribbed steel sill
plate, black carpet, a lamp and switches on the left wall). The G9L's tail is built as bands of the
tail cap (g9l_rear.band), so the hatch's parts already are separate objects: the gate, the lamp bar
and its lens are cut at the side shut line and the rest is gathered.

    import g9l_gate as RG
    RG.cut_underlay()        # the backlight's black underlay goes (it is the pane's own footprint)
    RG.build_seal()          # a black bead behind the shut line
    RG.split_tail()          # the node XpengG9L_Tailgate
    RG.open_hull()           # the dark hull behind it
    RG.set_hatch(82.0)       # preview it open (degrees)
    RG.build_liner(col)      # the hatch's inside, in the cabin (int_tailgate), before split_tail()

Car axes: +x forward, +y left, z up. The hatch opens by rotating about +y.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HINGE = Vector((-1.970, 0.0, 1.700))     # the roof's trailing edge (g9l_surface.KNEE_X), on the centreline
OPEN_DEG = 82.0
GROUP = ("XpengG9L_Tailgate", "G9L_GateGrp")
PAINT = "M_Paint_G9L_Purple"

# whole objects that live in the hatch (each holds both sides)
PARTS = (
    "G9L_Glass_Rear", "G9L_Spoiler",
    "G9L_Letter_X", "G9L_Letter_P", "G9L_Letter_E", "G9L_Letter_N", "G9L_Letter_G",
    "G9L_Badge_Brand", "G9L_Badge_Model", "G9L_Rear_Camera_House", "G9L_Rear_Camera_Lens",
    "G9L_Plate_Rear", "G9L_Plate_Rear_XPENGG9",
)
# the bands the shut line cuts: only the middle (|y| < Y_SHUT) goes with the hatch, the swept ends stay on the
# quarter panels
CUT = ("G9L_Tailgate", "G9L_Tail_Lamp_Cap", "G9L_Tail_Lamp_Lip", "G9L_Tail_Lens",
       "G9L_Tail_Strip_Main", "G9L_Tail_Strip_Low")
Y_SHUT = 0.775
UNDERLAY = "G9L_Roof_Rear_Black"


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
    """Cut the object `name` (modifiers baked) along `cut_planes` ((point, normal) pairs) and move the faces
    `keep(centre)` selects to a new object `new_name` (same transform and materials, same collections)."""
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


def split_bands(y_cut=Y_SHUT):
    """Each band's middle (|y| < y_cut) becomes <name>_C, the hatch's; its swept ends stay on the quarter
    panels."""
    made = []
    for n in CUT:
        if bpy.data.objects.get(n + "_C") is None:
            made.append(_split_off(n, n + "_C",
                                   [((0.0, y_cut, 0.0), (0.0, 1.0, 0.0)),
                                    ((0.0, -y_cut, 0.0), (0.0, 1.0, 0.0))],
                                   lambda c: abs(c.y) < y_cut))
    return made


def split_tail():
    """Gather everything that sits in the hatch into one node with its origin on the hinge."""
    from carkit import export as X
    split_bands()
    col = _group(GROUP[1])
    names = []
    for n in PARTS + tuple(c + "_C" for c in CUT):
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("hatch part %s missing from the build" % n)
        _link_only(ob, col)
        names.append(ob.name)
    hatch = X.join("G9L_Tailgate_Node", names)
    hatch.name = "G9L_Tailgate_Node"
    hatch.data.transform(Matrix.Translation(-HINGE))
    hatch.matrix_world = Matrix.Translation(HINGE)
    hatch["hinge"] = tuple(HINGE)
    hatch["open_deg"] = OPEN_DEG
    return hatch


def set_hatch(deg, card=True):
    """Swing the hatch (and its liner, if built) `deg` open about its hinge."""
    rot = Matrix.Rotation(math.radians(deg), 4, 'Y')
    for n in ("G9L_Tailgate_Node", "int_tailgate"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n == "G9L_Tailgate_Node"):
            ob.matrix_world = Matrix.Translation(HINGE) @ rot


def open_hull(hulls=("G9L_Shell_Shadow", "G9L_Shell_Shadow_R"), reach=0.45, x_max=-1.8):
    """Delete the hull faces that sit in front of the hatch's skin (a ray straight back along -x hits it), so the
    boot shows through an open hatch."""
    gate = bpy.data.objects["G9L_Tailgate_Node"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = gate.evaluated_get(dg)
    me = ev.to_mesh()
    mw = Matrix.Translation(Vector(gate.get("hinge", HINGE)))     # the closed pose
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
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
            if p.x > x_max or abs(p.y) > Y_SHUT + 0.005:
                continue
            if tree.ray_cast(p, back, reach)[0] is not None:
                dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(sh.data)
        bm.free()
        total += len(dead)
    return total


def cut_underlay(under=UNDERLAY):
    """The backlight's black underlay is the pane's own footprint (x -2.51..-1.97, |y| < 0.64: the glass is
    -2.52..-1.98, |y| < 0.65), so there is nothing of it left to stay on the body when the hatch swings up: it goes. The
    cabin shows through the privacy glass as it does through the quarter windows. Run before split_tail()."""
    ob = bpy.data.objects.get(under)
    if ob is None:
        return 0
    n = len(ob.data.polygons)
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)
    return n


# ------------------------------------------------------- the hatch's inner side (the cabin's int_tailgate)
LINER_DEPTH = 0.040
INSIDE = Vector((-1.9, 0.0, 0.95))       # a point in the cabin, for "outward"


def _mat(name, base, rough=0.6, **kw):
    from carkit import materials as MB
    m = bpy.data.materials.get(name)
    if m is None:
        m, nt, b = MB.mat(name)
        MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=rough, **kw)
    return m


def _glass_loop():
    """The backlight's outline (one boundary loop, world frame) and its outward normal."""
    import g9l_openings as OP
    src = bpy.data.objects["G9L_Glass_Rear"]
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    me.transform(src.matrix_world)
    loop = max(OP._loops(me), key=len)
    n = Vector()
    for p in me.polygons:
        n += p.normal * p.area
    n.normalize()
    centre = sum(loop, Vector()) / len(loop)
    if n.dot(centre - INSIDE) < 0.0:
        n = -n
    bpy.data.meshes.remove(me)
    return loop, n, centre


def build_liner(col=None, depth=LINER_DEPTH):
    """The hatch's inside, for the cabin's GLB: a dark liner `depth` behind the gate's skin from the smile up to
    the glass, and a bezel round the backlight (a reveal down to the liner's plane and a flange out over the
    painted frame). Its origin is the hinge, so it swings with the hatch (int_tailgate)."""
    import g9l_rear as RR
    from carkit import export as X
    from carkit import geom
    from carkit import mesh as M
    col = col or bpy.data.collections["G9L_Interior"]
    liner = _mat("INT_Hatch_Liner", (0.024, 0.024, 0.028), 0.7, specular=0.3)
    tail = RR.TAIL
    made = []
    # the lower panel: the tail cap's own surface, `depth` in, from the smile to the cap's top
    ny, nz = 40, 14
    ymax = Y_SHUT - 0.010
    cols = []
    for i in range(ny + 1):
        y = ymax * i / float(ny)
        zlo = RR.gate_low(y) + 0.020
        zhi = RR.CAP_HIGH
        c = []
        for k in range(nz + 1):
            z = zlo + (zhi - zlo) * k / float(nz)
            w, v = tail.wv_at(y, z)
            c.append(tail.offset(w, v, -depth))
        cols.append(c)
    low = M.mesh_from_rows("int_tailgate_low", cols, col)
    M.orient(low.data, geom.axial(1.0))
    low.data.materials.append(liner)
    M.mirror_y(low)
    made.append(low.name)
    # the bezel round the glass (a cabin built alone has no exterior to read it from: the lower panel only)
    if bpy.data.objects.get("G9L_Glass_Rear") is None:
        ob = X.join("int_tailgate", made)
        ob.data.transform(Matrix.Translation(-HINGE))
        ob.matrix_world = Matrix.Translation(HINGE)
        return ob
    loop, n, centre = _glass_loop()
    m = len(loop)
    verts, faces = [], []
    for i, p in enumerate(loop):
        t = (loop[(i + 1) % m] - loop[i - 1]).normalized()
        w = n.cross(t).normalized()
        if w.dot(p - centre) < 0.0:
            w = -w                                       # out of the pane, in its plane
        # no flange where the glass meets the lamp bar (z < 1.22): it would stand out behind the lamp's lens
        k = max(0.0, min(1.0, (p.z - 1.22) / 0.10))
        verts += [tuple(p + w * 0.070 * k - n * depth), tuple(p - n * depth), tuple(p - n * 0.004)]
    for i in range(m):
        j = (i + 1) % m
        for r in (0, 1):
            faces.append([3 * i + r, 3 * j + r, 3 * j + r + 1, 3 * i + r + 1])
    bz = M.obj("int_tailgate_bezel", verts, faces, col, liner, smooth=False)
    M.orient(bz.data, lambda c: tuple(-n * 0.6 + (centre - Vector(c)).normalized() * 0.4))
    made.append(bz.name)
    ob = X.join("int_tailgate", made)
    ob.data.transform(Matrix.Translation(-HINGE))
    ob.matrix_world = Matrix.Translation(HINGE)
    return ob


# ------------------------------------------------------------------------------ seal
def build_seal(collection="G9L_Details"):
    """A black bead behind the shut line along the gate's lower edge and up its sides, which shows when the hatch is
    open and fills the gap when it is shut."""
    import g9l_rear as RR
    from carkit.interior.sweep import tube, ellipse
    col = bpy.data.collections[collection]
    path = []
    n_low = 30
    for i in range(n_low + 1):
        y = Y_SHUT * i / float(n_low)
        p, nn = RR.face(y, RR.gate_low(y) + 0.020, -0.011)
        path.append(tuple(p))
    n_side = 8
    z0 = RR.gate_low(Y_SHUT) + 0.020
    for k in range(1, n_side + 1):
        z = z0 + (RR.CAP_HIGH - 0.010 - z0) * k / float(n_side)
        p, nn = RR.face(Y_SHUT - 0.004, z, -0.011)
        path.append(tuple(p))
    satin = bpy.data.materials["M_Black_Satin"]
    half = tube("G9L_Boot_SealHalf", path, ellipse(0.0075, 0.0075, 10), col, satin, closed=False,
                lateral=(1.0, 0.0, 0.0))
    other = tube("G9L_Boot_SealHalfR", [(x, -y, z) for (x, y, z) in path], ellipse(0.0075, 0.0075, 10), col,
                 satin, closed=False, lateral=(1.0, 0.0, 0.0))
    return [half, other]


# ---------------------------------------------------------------------- boot fittings
def _box(name, x0, x1, y0, y1, z0, z1, mat, col, smooth=False):
    from carkit import mesh as M
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, v, f, col, mat, smooth=smooth)
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    M.orient(ob.data, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))
    return ob


Z_CARGO = 0.780                  # the cargo floor, at the sill plate (c3_0157: the carpet runs flush to it)
X_SILL = -2.455                  # the sill plate's rear edge


def build_boot_details(col, lib, wall_y):
    """What c3_0157/58 show in the boot: a ribbed steel sill plate with a lock slot in the middle across the
    opening's lower edge, a switch module with a lit lamp on the left wall, a vent grille low on each wall, a
    tie-down hook on each wall and the folded seat backs' carpet (the bay's own front wall)."""
    satin = lib["satin"]
    steel = _mat("INT_Boot_Plate", (0.30, 0.30, 0.31), 0.35, metallic=0.9)
    rubber = lib.get("rubber", satin)
    lamp = bpy.data.materials.get("INT_Boot_Lamp")
    if lamp is None:
        lamp = _mat("INT_Boot_Lamp", (0.9, 0.9, 0.9), 0.4)
        b = next(n for n in lamp.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Emission Color"].default_value = (1.0, 0.98, 0.94, 1.0)
        b.inputs["Emission Strength"].default_value = 7.0
    made = []
    # the sill plate: a ribbed strip along the opening's lower edge, with the lid-lock's slot
    ys = [-0.70 + 1.40 * k / 56.0 for k in range(57)]
    from carkit.interior.sweep import grid_mesh
    from carkit import mesh as M
    rows = []
    for y in ys:
        rows.append([(X_SILL + dx, y, Z_CARGO + dz)
                     for (dx, dz) in ((0.000, -0.004), (0.020, 0.002), (0.085, 0.004), (0.130, 0.001))])
    sp = grid_mesh("int_boot_sill", rows, col, steel)
    M.orient(sp.data, lambda c: (0.0, 0.0, 1.0))
    made.append(sp)
    # the lock: a small dark housing in the plate's middle
    made.append(_box("int_boot_lock", X_SILL + 0.030, X_SILL + 0.100, -0.060, 0.060, Z_CARGO + 0.001,
                     Z_CARGO + 0.008, satin, col))
    # the left wall: one recessed module with a bag hook (max 3 kg), a 12 V socket and the lit lamp (c3_0158)
    xm, zm = -2.34, 1.00
    y = wall_y(xm) - 0.002
    made.append(_box("int_boot_module", xm, xm + 0.190, y - 0.004, y + 0.012, zm - 0.040, zm + 0.040, satin, col))
    made.append(_box("int_boot_hook", xm + 0.012, xm + 0.040, y - 0.010, y - 0.004, zm - 0.030, zm + 0.026,
                     rubber, col))
    made.append(_box("int_boot_socket", xm + 0.056, xm + 0.092, y - 0.009, y - 0.004, zm - 0.018, zm + 0.020,
                     rubber, col))
    made.append(_box("int_boot_lamp", xm + 0.110, xm + 0.176, y - 0.008, y - 0.004, zm - 0.020, zm + 0.020,
                     lamp, col))
    # a vent grille low on each wall at the rear corner (c3_0157)
    for s in (1.0, -1.0):
        xg = -2.34
        yg = s * (wall_y(xg) - 0.003)
        made.append(_box("int_boot_vent%s" % ("L" if s > 0 else "R"), xg, xg + 0.120,
                         min(yg, yg - s * 0.006), max(yg, yg - s * 0.006), Z_CARGO + 0.060, Z_CARGO + 0.210,
                         satin, col))
    return made


def boot_carpet():
    """The boot's black loop-pile carpet (c3_0157/161): near-black and rough, darker than the cabin's footwell carpet."""
    return _mat("INT_Boot_Carpet", (0.020, 0.020, 0.022), 0.96, specular=0.15)


X_SEAT = -1.43                   # the rear seats' backs' rear face


def build_seatback_carpet(col, mat, z_top=1.22):
    """A black carpet panel on the folded seat backs' rear faces: the bay's front wall, shrink-wrapped to the seat
    shells by rays from behind (c3_0157: the backs are black felt up to the shoulders)."""
    from carkit.interior.sweep import grid_mesh
    from carkit import mesh as M
    shells = [o for o in col.objects if o.type == 'MESH' and o.name.startswith("int_seat_R") and "_Back_" in o.name]
    shells += [o for o in col.objects if o.name == "int_rear_centre_back"]
    verts, polys = [], []
    for o in shells:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    if not polys:
        return None
    tree = BVHTree.FromPolygons(verts, polys)
    rows = []
    zs = [Z_CARGO + (z_top - Z_CARGO) * k / 14.0 for k in range(15)]
    ys = [-0.660 + 1.320 * j / 33.0 for j in range(34)]
    for z in zs:
        row = []
        for y in ys:
            h = tree.ray_cast(Vector((-1.90, y, z)), Vector((1.0, 0.0, 0.0)), 1.0)[0]
            x = (h.x - 0.006) if h is not None else X_SEAT
            row.append((min(x, X_SEAT + 0.01), y, z))
        rows.append(row)
    ob = grid_mesh("int_cargo_seatback", rows, col, mat)
    M.orient(ob.data, lambda c: (-1.0, 0.0, 0.0))
    return ob
