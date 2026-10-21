"""Denza Z9 trunk lid and boot.

The lid is the whole short rear above the bumper's top edge: the decklid with its ducktail, the tail cap's upper band
and the gate under it, the middle of the two leaf-shaped lamps (they sweep round each corner onto the quarter, beyond
the lid's side shut line), the roundel and the model badges. It hangs from the backlight's base (x -2.26: the glass
stays on the body) and swings up about a lateral axis (Autohome c3_0179/229/230: about 80 degrees on two black
swan-neck hinge arms that stand at the opening's front corners). The plate tray, the camera and the bumper stay on the
body. The boot behind it is new, from the same photographs: black loop-pile carpet on the floor and walls, a ribbed
steel sill plate with the lock in its middle, a speaker grille on the left wall, tie-down hooks, a seal all round.

    import z9_gate as RG
    RG.build_seal()          # a black bead behind the shut line
    RG.split_tail()          # the node DenzaZ9_Tailgate
    RG.open_hull()           # the dark hull behind and under it
    RG.set_hatch(80.0)       # preview it open (degrees)
    RG.build_liner(col)      # the lid's inside, in the cabin (int_tailgate), before split_tail()

Car axes: +x forward, +y left, z up. The lid opens by rotating about +y.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HINGE_X = -2.185                          # the decklid's front end (x -2.32..-2.16), under the backlight's base (-2.24)
OPEN_DEG = 80.0
GROUP = ("DenzaZ9_Tailgate", "Z9_GateGrp")
NODE = "Z9_Tailgate_Node"

# whole objects that live in the lid (each holds both sides)
PARTS = (
    "Z9_Decklid", "Z9_Ducktail_Lip",
    "Z9_Roundel_Ring", "Z9_Roundel_Disc", "Z9_Roundel_Mark_0", "Z9_Roundel_Mark_1",
    "Z9_Badge_Model", "Z9_Badge_E3",
)
# the bands the shut line cuts: only the middle (|y| < Y_SHUT) goes with the lid; the rest stays on the quarters
CUT = ("Z9_Tail_Upper", "Z9_Tailgate", "Z9_Tail_Lamp_Back", "Z9_Tail_Lamp_Lens", "Z9_Tail_Lamp_Row_Up",
       "Z9_Tail_Lamp_Row_Low")
Y_SHUT = 0.700                            # the lid's side shut line at the tail (the decklid itself is 0.59 wide)

_HINGE = []


def hinge():
    """The hinge axis point: on the centreline at the decklid's height at HINGE_X (read off the built panel)."""
    if _HINGE:
        return _HINGE[0]
    ob = bpy.data.objects.get("Z9_Decklid") or bpy.data.objects[NODE]
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    mw = ob.matrix_world
    tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
    h = tree.ray_cast(Vector((HINGE_X, 0.0, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
    z = h.z if h is not None else 1.0
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
    made = []
    for n in CUT:
        if bpy.data.objects.get(n + "_C") is None:
            made.append(_split_off(n, n + "_C",
                                   [((0.0, y_cut, 0.0), (0.0, 1.0, 0.0)),
                                    ((0.0, -y_cut, 0.0), (0.0, 1.0, 0.0))],
                                   lambda c: abs(c.y) < y_cut))
    return made


def split_tail():
    """Gather everything that sits in the lid into one node with its origin on the hinge."""
    from carkit import export as X
    h = hinge()
    split_bands()
    col = _group(GROUP[1])
    names = []
    for n in PARTS + tuple(c + "_C" for c in CUT):
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("lid part %s missing from the build" % n)
        _link_only(ob, col)
        names.append(ob.name)
    lid = X.join(NODE, names)
    lid.name = NODE
    lid.data.transform(Matrix.Translation(-h))
    lid.matrix_world = Matrix.Translation(h)
    lid["hinge"] = tuple(h)
    lid["open_deg"] = OPEN_DEG
    return lid


def set_hatch(deg, card=True):
    """Swing the lid (and its liner, if built) `deg` open about its hinge."""
    h = hinge() if bpy.data.objects.get(NODE) is None else Vector(bpy.data.objects[NODE].get("hinge", hinge()))
    rot = Matrix.Rotation(math.radians(deg), 4, 'Y')
    for n in (NODE, "int_tailgate"):
        ob = bpy.data.objects.get(n)
        if ob is not None and (card or n == NODE):
            ob.matrix_world = Matrix.Translation(h) @ rot


def open_hull(hulls=("Z9_Shell_Shadow",), reach=0.5, x_max=-1.6):
    """Delete the hull faces that stand under or in front of the lid's skin (a ray straight up, or straight back, hits
    it), so the boot shows through an open lid."""
    gate = bpy.data.objects[NODE]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = gate.evaluated_get(dg)
    me = ev.to_mesh()
    mw = Matrix.Translation(Vector(gate.get("hinge", hinge())))     # the closed pose
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
            if p.x < X_BULKHEAD - 0.01 and p.z > Z_TRUNK - 0.03:
                dead.append(f)          # the boot's volume is the cabin's carpeted box now: the hull's walls and roof there stand in it
                continue
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


# ---------------------------------------------------------------- the lid's inside (the cabin's int_tailgate)
LINER_DEPTH = 0.014
LINER_SHEETS = ("Z9_Decklid", "Z9_Ducktail_Lip", "Z9_Tail_Upper", "Z9_Tailgate")


def _mat(name, base, rough=0.6, **kw):
    from carkit import materials as MB
    m = bpy.data.materials.get(name)
    if m is None:
        m, nt, b = MB.mat(name)
        MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=rough, **kw)
    return m


def build_liner(col=None, depth=LINER_DEPTH):
    """The lid's inside, for the cabin's GLB: a dark charcoal liner `depth` under the lid's own skin, with the origin on the
    hinge, so it swings with the lid (int_tailgate).

    It is an inward copy of the lid's paint sheets (the decklid, its ducktail lip and the two tail bands), cut at the lid's side
    shut lines: whatever the lid's skin covers the liner covers, up to its edges. (The first version was built from the tail's
    analytic surface and the decklid's top by rays, in two separate strips with a gap between them, and under an open lid the
    paint's black back and two floating dark bands showed instead of one inner panel: reported 2026-10-21.)"""
    from carkit import export as X
    if bpy.data.objects.get("Z9_Decklid") is None:          # a cabin built alone has no exterior to read
        return None
    col = col or bpy.data.collections["Z9_Interior"]
    liner = _mat("INT_Hatch_Liner", (0.060, 0.060, 0.066), 0.85, specular=0.2)
    h = hinge()
    inside = Vector((-1.9, 0.0, 0.70))                     # a point in the cabin: the skin's outside is away from it
    dg = bpy.context.evaluated_depsgraph_get()
    made = []
    for name in LINER_SHEETS:
        src = bpy.data.objects.get(name)
        if src is None:
            continue
        me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
        me.transform(src.matrix_world)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        # the lid's middle only (the bands run on round the quarters)
        ym = Y_SHUT - 0.012
        for sign in (1.0, -1.0):
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0.0, sign * ym, 0.0), plane_no=(0.0, 1.0, 0.0),
                                   clear_outer=sign > 0, clear_inner=sign < 0)
        # only the outer skin (a sheet that was thickened has an inner skin too: its faces look at the cabin)
        bm.normal_update()
        dead = [f for f in bm.faces if f.normal.dot(f.calc_center_median() - inside) <= 0.0]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.normal_update()
        for v in bm.verts:
            n = v.normal.copy()
            if n.dot(v.co - inside) < 0.0:
                n = -n
            v.co -= n * depth
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        me2 = bpy.data.meshes.new("int_tailgate_%s_mesh" % name)
        bm.to_mesh(me2)
        nf = len(bm.faces)
        bm.free()
        if not nf:
            bpy.data.meshes.remove(me2)
            continue
        me2.materials.append(liner)
        for p in me2.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new("int_tailgate_" + name, me2)
        col.objects.link(ob)
        made.append(ob.name)
    ob = X.join("int_tailgate", made)
    ob.data.transform(Matrix.Translation(-h))
    ob.matrix_world = Matrix.Translation(h)
    return ob


# ------------------------------------------------------------------------------ seal
def build_seal(collection="Z9_Details"):
    """A black bead behind the shut line along the lid's lower edge and up its sides, which shows when the lid is open
    and fills the gap when it is shut."""
    import z9_rear as RR
    from carkit.interior.sweep import tube, ellipse
    col = bpy.data.collections[collection]
    path = []
    n_low = 30
    for i in range(n_low + 1):
        y = Y_SHUT * i / float(n_low)
        p, nn = RR.face(y, RR.bumper_top(y) + 0.020, -0.011)
        path.append(tuple(p))
    z0 = RR.bumper_top(Y_SHUT) + 0.020
    n_side = 8
    for k in range(1, n_side + 1):
        z = z0 + (RR.CAP_HIGH - 0.010 - z0) * k / float(n_side)
        p, nn = RR.face(Y_SHUT - 0.004, z, -0.011)
        path.append(tuple(p))
    satin = bpy.data.materials["M_Black_Satin"]
    half = tube("Z9_Boot_SealHalf", path, ellipse(0.0075, 0.0075, 10), col, satin, closed=False,
                lateral=(1.0, 0.0, 0.0))
    other = tube("Z9_Boot_SealHalfR", [(x, -y, z) for (x, y, z) in path], ellipse(0.0075, 0.0075, 10), col,
                 satin, closed=False, lateral=(1.0, 0.0, 0.0))
    return [half, other]


# ---------------------------------------------------------------------- the boot
Z_TRUNK = 0.620                  # the boot floor, level with the lid's lower shut line (the bumper's top 0.588 + 0.02) and the sill plate
X_BULKHEAD = -1.395              # the rear seats' bulkhead (z9_interior_shell.build_rear_closure)
X_MOUTH = -2.52                  # the sill plate's rear edge (read off the built tail where there is one: build_boot)
Z_SHELF = 0.995                  # the parcel shelf's height behind the seats; it rises with the deck behind x -1.62
# (The floor used to be at 0.72, 11 cm above the lid's lower edge: an open lid showed a hollow under the sill plate, a bright
# plank floating across the opening with the cabin's mauve bulkhead under it. And the walls stopped at 1.0 with no ceiling, so
# over them the cabin's trim and the roof's underside stood in the boot. Reported 2026-10-21.)


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _box(name, x0, x1, y0, y1, z0, z1, mat, col, smooth=False):
    from carkit import mesh as M
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, v, f, col, mat, smooth=smooth)
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    M.orient(ob.data, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))
    return ob


def _exterior_tree():
    """A BVH of the exterior's own skin (Z9_Body, Z9_Details), or None in a cabin built alone."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for cn in ("Z9_Body", "Z9_Details"):
        col = bpy.data.collections.get(cn)
        for ob in (col.objects if col else ()):
            if ob.type != 'MESH':
                continue
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            me.transform(ob.matrix_world)
            base = len(verts)
            verts += [v.co.copy() for v in me.vertices]
            me.calc_loop_triangles()
            polys += [[base + i for i in t.vertices] for t in me.loop_triangles]
            bpy.data.meshes.remove(me)
    return BVHTree.FromPolygons(verts, polys) if polys else None


def boot_carpet():
    """The boot's charcoal loop-pile carpet (black in the photographs' shade, but lit: a true black reads as a hole)."""
    return _mat("INT_Boot_Carpet", (0.055, 0.055, 0.060), 0.96, specular=0.15)


def _trim_quarter_behind(x_cut, z_cut):
    """The cabin's quarter / wheelhouse trim (mauve door leather) runs on behind the bulkhead to x -1.88 and 5 cm into the
    boot's sides: in the boot it showed as pink patches up the walls. Cut it off at the end wall, below the shelf."""
    ob = bpy.data.objects.get("int_quarter")
    if ob is None:
        return 0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for co, no in (((x_cut, 0.0, 0.0), (1.0, 0.0, 0.0)), ((0.0, 0.0, z_cut), (0.0, 0.0, 1.0))):
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=co, plane_no=no)
    dead = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.x < x_cut and c.z < z_cut:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    return len(dead)


def build_boot(col, lib, half):
    """What c3_0229/30 show behind the lid: a charcoal loop-pile carpeted box (floor, walls, a ceiling under the parcel shelf,
    an end wall in front of the seats' bulkhead), a ribbed steel sill plate with the lock in its middle flush with the
    floor, a speaker grille on the left wall and a tie-down hook on each. `half(x, z)` is the bay's half-width inboard of
    the skin. Every face a camera looking in through the open lid can see is the boot's own: none of the cabin's trim."""
    from carkit.interior.sweep import grid_mesh
    from carkit import mesh as M
    _trim_quarter_behind(X_BULKHEAD - 0.004, Z_SHELF - 0.005)
    steel = _mat("INT_Boot_Plate", (0.13, 0.13, 0.14), 0.65, metallic=0.35)    # a flat bright plate mirrors the hall's lamps white
    satin = lib["satin"]
    speaker = lib.get("speaker", satin)
    carpet = boot_carpet()
    made = []
    tree = _exterior_tree()

    def hw(x, z):
        """The bay's half-width: `half`, and where the built exterior is there to be read, no wider than its skin read by
        a ray from the centreline out sideways, less 3 cm (a wall built from the flank's width stands outside the tail's
        corner: black slabs at the rear quarters when a door is open)."""
        y = half(x, z)
        if tree is not None:
            hit = tree.ray_cast(Vector((x, 0.0, z)), Vector((0.0, 1.0, 0.0)), 2.0)[0]
            if hit is not None:
                y = min(y, hit.y - 0.030)
        return max(0.40, y)

    def roof(x, y):
        """The ceiling: just under the parcel shelf, and where the built exterior is there, 3.5 cm under its top (the
        decklid and the glass), so it never stands through the body. A ray that misses the skin or lands on something
        under the boot's reach (the ground-hugging underbody, past the tail's corner) is not the deck: the next column in
        takes its place, else the ceiling dips there in a drip."""
        z = Z_SHELF + 0.09 * _smooth((-1.62 - x) / 0.32) - 0.012
        if tree is not None:
            yy = abs(y)
            while yy >= -1e-6:
                hit = tree.ray_cast(Vector((x, yy, 2.5)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
                if hit is not None and hit.z > Z_TRUNK + 0.28:
                    z = min(z, hit.z - 0.035)
                    break
                yy -= 0.05
        return max(Z_TRUNK + 0.20, z)

    # the mouth: the sill plate's rear edge, 2 cm inside the tail's skin at the floor's height
    x_mouth = X_MOUTH
    if tree is not None:
        xs_hit = []
        for y in (0.0, 0.25, 0.45):
            hit = tree.ray_cast(Vector((-4.0, y, Z_TRUNK + 0.012)), Vector((1.0, 0.0, 0.0)), 4.0)[0]
            if hit is not None:
                xs_hit.append(hit.x)
        if xs_hit:
            x_mouth = max(xs_hit) + 0.020
    xs = [X_BULKHEAD + (x_mouth + 0.04 - X_BULKHEAD) * k / 24.0 for k in range(25)]

    # the floor
    rows = [[(x, hw(x, Z_TRUNK) * j / 12.0, Z_TRUNK) for j in range(13)] for x in xs]
    fl = grid_mesh("int_boot_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)
    # the walls, up to the ceiling
    rows = []
    for x in xs:
        zt = roof(x, hw(x, Z_TRUNK + 0.3))
        rows.append([(x, hw(x, Z_TRUNK + (zt - Z_TRUNK) * k / 10.0), Z_TRUNK + (zt - Z_TRUNK) * k / 10.0)
                     for k in range(11)])
    wall = grid_mesh("int_boot_wall", rows, col, carpet)
    M.orient(wall.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(wall)
    made.append(wall)
    # the ceiling: the underside of the parcel shelf and the deck behind it
    rows = []
    for x in xs:
        yw = hw(x, roof(x, 0.0))
        rows.append([(x, yw * j / 12.0, roof(x, yw * j / 12.0)) for j in range(13)])
    rf = grid_mesh("int_boot_roof", rows, col, carpet)
    M.orient(rf.data, lambda c: (0.0, 0.0, -1.0))
    M.mirror_y(rf)
    made.append(rf)
    # the end wall, just in front of the bulkhead's boot face (which is the cabin's mauve carpet): charcoal like the rest
    xe = X_BULKHEAD - 0.004
    rows = []
    for k in range(9):
        z = Z_TRUNK + (roof(xe, 0.0) - Z_TRUNK) * k / 8.0
        rows.append([(xe, hw(xe, z) * j / 12.0, z) for j in range(13)])
    en = grid_mesh("int_boot_end", rows, col, carpet)
    M.orient(en.data, lambda c: (-1.0, 0.0, 0.0))
    M.mirror_y(en)
    made.append(en)
    # the sill plate: a ribbed strip along the opening's lower edge, flush with the floor
    ys = [-0.66 + 1.32 * k / 56.0 for k in range(57)]
    # the tail closes in sharply (its skin is 0.39 either side of the centreline at x -2.48), so the plate narrows with it
    cols = ((0.000, -0.004), (0.020, 0.002), (0.085, 0.004), (0.130, 0.001))
    kx = [min(1.0, hw(x_mouth + dx, Z_TRUNK) / 0.66) for (dx, dz) in cols]
    rows = [[(x_mouth + dx, y * kx[i], Z_TRUNK + dz) for i, (dx, dz) in enumerate(cols)] for y in ys]
    sp = grid_mesh("int_boot_sill", rows, col, steel)
    M.orient(sp.data, lambda c: (0.0, 0.0, 1.0))
    made.append(sp)
    made.append(_box("int_boot_lock", x_mouth + 0.030, x_mouth + 0.100, -0.060, 0.060, Z_TRUNK + 0.001,
                     Z_TRUNK + 0.008, satin, col))
    # the left wall's speaker grille (c3_0230: a black mesh panel at the corner), a hook on each wall
    xg = -1.80
    yg = hw(xg, Z_TRUNK + 0.20)
    made.append(_box("int_boot_speaker", xg, xg + 0.200, yg - 0.004, yg + 0.002, Z_TRUNK + 0.050, Z_TRUNK + 0.230,
                     speaker, col))
    for s in (1.0, -1.0):
        yh = s * hw(-2.05, Z_TRUNK + 0.06)
        made.append(_box("int_boot_tie%s" % ("L" if s > 0 else "R"), -2.07, -2.03, min(yh, yh - s * 0.006),
                         max(yh, yh - s * 0.006), Z_TRUNK + 0.030, Z_TRUNK + 0.070, steel, col))
    return made
