"""Xiaomi SU7 Ultra frunk: the bay under the bonnet, and the bonnet itself as a
hinged node. (The Luxeed RX's rx_bays.py is the template; this is its SU7 fit.)

Built from the opening photographs (blender/reference/xiaomi-su7-ultra/openings/
frunk, 33-42). From the windscreen forward they show: a black cowl panel with the
wipers parked across it, two grille vents and a small plate; a thick black seal
round a deep, rounded tub whose floor has a ribbed tray between two raised covers;
and the bonnet, one clamshell hinged at the cowl and held up by two near-vertical
gas struts. Its underside is a painted inner panel with a honeycomb of hexagons,
four black plugs, two flat pockets and cast hinge brackets.

    import su7_bays as BY
    BY.build_frunk()      # the static bay and the wipers (SU7_Details)
    BY.split_bonnet()     # SU7_Bonnet: hood, stripes, inner panel - origin on the hinge
    BY.open_hull()        # the hull's roof under the bonnet
    BY.set_bonnet(78.0)   # preview it open (degrees)

Car axes +x forward, +y left, z up. The bonnet opens by rotating about -y.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit.bay import (inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, inside as _inside)

HOOD = "SU7Ultra_Hood"
STRIPES = "SU7Ultra_Stripes_Hood"
HINGE = (0.958, 0.945)         # (x, z) of the hinge axis, along y, under the cowl edge
OPEN_DEG = 78.0
GROUP = ("SU7Ultra_Bonnet", "SU7_BonnetGrp")
X_COWL = 0.951                 # the hood's rear edge (the surface starts here)
X_REAR = 1.40                  # the tub's rear edge
SEAL_INSET = 0.075             # the gasket's centre line, in from the hood's edge
FLOOR_Z = 0.505                # the tub's floor
INNER_DROP = 0.022             # the inner panel under the hood's top surface
# the tub wall, rim to floor: (inward offset from the gasket, fraction of the depth)
WALL = [(0.0, 0.0), (0.004, 0.03), (0.012, 0.10), (0.030, 0.34), (0.060, 0.68),
        (0.100, 0.89), (0.150, 0.98), (0.190, 1.0)]
CENTRE = (1.78, 0.0)
_OUTLINE = None


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class Hood:
    """The built hood's top surface, for heights under and along it."""

    def __init__(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects[HOOD]
        self.tree = BVHTree.FromObject(ob.evaluated_get(dg), dg)

    def z(self, x, y):
        h = self.tree.ray_cast(Vector((max(x, X_COWL), y, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        return h.z if h is not None else None

    def zc(self, x, y):
        """Top height, from the nearest point toward the centreline that has one."""
        sgn = 1.0 if y >= 0 else -1.0
        for dy in (0.0, 0.03, 0.06, 0.10, 0.20, 0.40):
            v = self.z(x, y - sgn * min(abs(y), dy))
            if v is not None:
                return v
        return self.z(x, 0.0)


def _resample(poly, n):
    """A closed polygon at n points evenly spaced along its length."""
    m = len(poly)
    d = [math.hypot(poly[(i + 1) % m][0] - poly[i][0], poly[(i + 1) % m][1] - poly[i][1])
         for i in range(m)]
    total = sum(d)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        t = total * k / n
        while acc + d[i] < t:
            acc += d[i]
            i += 1
        f = (t - acc) / (d[i] or 1.0)
        a, b = poly[i], poly[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def hood_outline(refresh=False):
    """The hood's plan outline, a closed polygon of (x, y): the panel's own
    boundary on its left half (rear centre, round the corner, to the nose),
    mirrored. Read once from the panel (build_frunk refreshes it); the bonnet
    node that replaces the panel keeps it valid."""
    global _OUTLINE
    if _OUTLINE is not None and not refresh:
        return _OUTLINE
    ob = bpy.data.objects[HOOD]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    adj = {}
    for e in bm.edges:
        a, b = e.verts
        if not e.is_boundary or (abs(a.co.y) < 0.002 and abs(b.co.y) < 0.002):
            continue                                   # the mirror seam
        adj.setdefault(a.index, []).append(b.index)
        adj.setdefault(b.index, []).append(a.index)
    ends = [i for i, nb in adj.items() if len(nb) == 1]
    bm.verts.ensure_lookup_table()
    cur = min(ends, key=lambda i: bm.verts[i].co.x)
    line, prev = [], None
    while cur is not None:
        co = bm.verts[cur].co
        line.append((co.x, abs(co.y)))
        nxt = [n for n in adj[cur] if n != prev]
        prev, cur = cur, (nxt[0] if nxt else None)
    bm.free()
    _OUTLINE = _resample(line + [(x, -y) for (x, y) in reversed(line)], 240)
    return _OUTLINE


def seal_poly(outline):
    """The gasket's closed outline: the hood's plan inset by SEAL_INSET at the
    sides and nose, closed across at X_REAR with rounded corners."""
    r = 0.10
    base = _resample(inset_poly(outline, SEAL_INSET), 400)
    side = [(x, y) for (x, y) in base if y >= 0.0 and x >= X_REAR + r]
    side.sort(key=lambda p: math.atan2(p[1], p[0] - CENTRE[0]), reverse=True)
    y0 = side[0][1]
    arc = [(X_REAR + r - r * math.sin(a), y0 - r + r * math.cos(a))
           for a in (math.radians(90.0 * k / 6) for k in range(7))]
    left = [(X_REAR, 0.0)] + arc[::-1] + side
    left[-1] = (left[-1][0], 0.0)                       # the nose, on the centreline
    right = [(x, -y) for (x, y) in reversed(left[1:-1])]
    return _resample(left + right, 120)


def _drop(x):
    """How far the apron lies under the hood's top line: close to the glass
    at the cowl, 55 mm down by the time it reaches the tub."""
    return 0.014 + 0.041 * _smoothstep((x - 0.95) / 0.16)


# ------------------------------------------------------------------ the bay
def _mat(name):
    return bpy.data.materials[name]


def _mats():
    """(felt, plastic, grille): the tub is black felt-lined, the cowl and gasket black
    plastic and rubber - duller than M_Black_Satin, which mirrors the studio."""
    from carkit import materials as MB
    return (MB.ensure("M_Frunk_Felt", (0.020, 0.020, 0.022), 0.95, specular=0.15),
            MB.ensure("M_Frunk_Plastic", (0.032, 0.032, 0.035), 0.72, specular=0.3),
            MB.ensure("M_Grille_Grey", (0.060, 0.062, 0.066), 0.55, specular=0.4))


def _box(name, x0, x1, y0, y1, z0, z1, mat, col):
    from carkit import mesh as M
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, v, f, col, mat, smooth=False)
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    M.orient(ob.data, lambda p: (p[0] - c[0], p[1] - c[1], p[2] - c[2]))
    return ob


def build_frunk(collection="SU7_Details"):
    """The static bay: the cowl panel with its vents, plate and wipers, the
    gasketed tub with its covers and ribbed tray. Needs the hood (for the
    heights under it)."""
    from carkit import mesh as M
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    col = bpy.data.collections[collection]
    hood = Hood()
    felt, plastic, grille = _mats()
    satin = _mat("M_Black_Satin")
    silver = _mat("M_Stripe_Silver")

    def zA(x, y):
        return hood.zc(x, y) - _drop(x)

    outline = hood_outline(refresh=True)
    rim = inset_poly(outline, 0.030)
    rim = [(0.936 if x < 1.0 else x, y) for (x, y) in rim]
    seal = seal_poly(outline)
    made = []
    # the apron: from the hood-side rim in to the gasket, paired along rays
    ro, so = radial(rim, CENTRE, 128), radial(seal, CENTRE, 128)
    rows = []
    for k in range(6):
        t = k / 5.0
        rows.append([(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                      zA(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                     for a, b in zip(ro, so)])
    ap = grid_mesh("SU7_Frunk_Apron", rows, col, plastic, wrap_t=True)
    M.orient(ap.data, lambda c: (0.0, 0.0, 1.0))
    made.append(ap)
    # the gasket, a thick black bead on the apron's inner edge
    path = [(x, y, zA(x, y) + 0.008) for (x, y) in seal]
    made.append(tube("SU7_Frunk_Seal", path, ellipse(0.0165, 0.0115, 8), col, plastic, closed=True,
                     lateral=(0.0, 0.0, 1.0)))
    # the tub: rings inward from the gasket and down to a flat floor
    rings = []
    for (d, f) in WALL:
        poly = inset_poly(seal, d)
        rings.append([(x, y, zA(sx, sy) * (1.0 - f) + FLOOR_Z * f)
                      for (x, y), (sx, sy) in zip(poly, seal)])
    tub = grid_mesh("SU7_Frunk_Tub", rings, col, felt, wrap_t=True)
    M.orient(tub.data, lambda c: (CENTRE[0] - c[0], -c[1], 0.9 - c[2]))
    made.append(tub)
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in rings[-1]])
    fl = _finish(bm, "SU7_Frunk_Floor", col, felt, smooth_shade=False)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    made.append(fl)

    # the ribbed tray on the floor's nose half, ribs running fore and aft
    X0, X1, HY = 1.80, 2.10, 0.40
    rows = []
    for i in range(13):
        x = X0 + (X1 - X0) * i / 12.0
        row = []
        for j in range(49):
            y = -HY + 2 * HY * j / 48.0
            edge = min(x - X0, X1 - x, HY - abs(y))
            f = _smoothstep(edge / 0.016)
            rib = 0.5 * (1.0 + math.cos(2 * math.pi * y / 0.044))
            row.append((x, y, FLOOR_Z + 0.002 + f * (0.009 + 0.004 * rib)))
        rows.append(row)
    tray = grid_mesh("SU7_Frunk_Tray", rows, col, plastic)
    M.orient(tray.data, lambda c: (0.0, 0.0, 1.0))
    made.append(tray)
    # the two raised covers over the wheelhouses, in the floor's rear corners
    for k, sy in enumerate((-1.0, 1.0)):
        rows = []
        for i in range(21):
            x = 1.44 + 0.34 * i / 20.0
            row = []
            for j in range(21):
                y = sy * (0.26 + 0.26 * j / 20.0)
                edge = min(x - 1.44, 1.78 - x, (y - sy * 0.26) * sy, (sy * 0.52 - y) * sy)
                f = _smoothstep(edge / 0.07)
                row.append((x, y, FLOOR_Z + 0.001 + 0.055 * f))
            rows.append(row)
        cv = grid_mesh("SU7_Frunk_Cover%d" % k, rows, col, felt)
        M.orient(cv.data, lambda c: (0.0, 0.0, 1.0))
        made.append(cv)

    # on the cowl: two grille vents, the plate between the tub and the wipers
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("SU7_Frunk_Vent%d" % k, _rrect(1.15, sy * 0.40, 0.040, 0.100, 0.008),
                           zA, 0.006, col, grille, 0.004))
    made.append(_prism("SU7_Frunk_Plate", _rrect(1.325, 0.0, 0.015, 0.058, 0.004), zA, 0.004, col,
                       silver, 0.0025))
    # the wipers, parked across the cowl: the passenger's blade runs from the
    # right pillar past the centre, the driver's from the left to just short of it
    for tag, y0, y1, dx in (("P", -0.62, 0.08, 0.0), ("D", -0.10, 0.64, -0.024)):
        zc = zA(0.992 + dx, 0.5 * (y0 + y1))
        made.append(_box("SU7_Wiper_Blade" + tag, 0.984 + dx, 0.998 + dx, y0, y1, zc + 0.004, zc + 0.017,
                         satin, col))
        made.append(_box("SU7_Wiper_Arm" + tag, 0.972 + dx, 0.982 + dx, y0 + 0.02, y1 - 0.02, zc + 0.013,
                         zc + 0.021, satin, col))
        yp = y0 if tag == "P" else y1
        made.append(_disc("SU7_Wiper_Pivot" + tag, 0.977 + dx, yp, 0.017, zA, 0.020, col, satin, n=14))
    return made


# ---------------------------------------------------------------- the bonnet
def _inner_z(hood):
    return lambda x, y: hood.zc(x, y) - INNER_DROP


def _hex_cells(col, hood, R=0.105, h=0.007):
    """The honeycomb on the inner panel (photographs 33, 39, 42): flat-topped
    hexagons, pointed across the car, each a low frustum, in a rounded field."""
    zi = _inner_z(hood)
    field = _rrect(1.70, 0.0, 0.31, 0.68, 0.10)
    bm = bmesh.new()
    n = 0
    for j in range(-5, 6):
        for i in range(-3, 4):
            cx = 1.70 + i * math.sqrt(3.0) * R + (0.5 * math.sqrt(3.0) * R if j % 2 else 0.0)
            cy = j * 1.5 * R
            if not _inside(field, cx, cy):
                continue
            bot, top = [], []
            for k in range(6):
                a = math.radians(60.0 * k)
                ux, uy = math.sin(a), math.cos(a)
                px, py = cx + (R - 0.004) * ux, cy + (R - 0.004) * uy
                qx, qy = cx + (R - 0.016) * ux, cy + (R - 0.016) * uy
                bot.append(bm.verts.new((px, py, zi(px, py) - 0.0005)))
                top.append(bm.verts.new((qx, qy, zi(qx, qy) - h)))
            for k in range(6):
                bm.faces.new((bot[k], bot[(k + 1) % 6], top[(k + 1) % 6], top[k]))
            bm.faces.new(top)
            n += 1
    ob = _finish(bm, "SU7_Bonnet_Hex", col, _mat("M_Paint_Yellow"), smooth_shade=False, recalc=False)
    return ob, n


def build_hood_underside(col):
    """What shows under the open bonnet: the return flange, the painted inner
    panel, the honeycomb, the pockets, plugs and cast hinge brackets. In the
    bonnet's closed pose."""
    from carkit import mesh as M
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    paint, satin = _mat("M_Paint_Yellow"), _mat("M_Black_Satin")
    zi = _inner_z(hood)
    outline = hood_outline()
    edge = inset_poly(outline, 0.003)
    inner = inset_poly(outline, 0.012)
    made = []
    # the flange: from just under the skin's edge down to the inner panel
    wall = [[(x, y, hood.zc(x, y) - 0.0025) for (x, y) in edge],
            [(x, y, zi(x, y)) for (x, y) in inner]]
    fl = grid_mesh("SU7_Bonnet_Flange", wall, col, paint, wrap_t=True)
    M.orient(fl.data, lambda c: (1.65 - c[0], -c[1], 0.4 - c[2]))
    made.append(fl)
    # the inner panel: the outline scaled in about the centre, ring by ring
    c = (1.65, 0.0)
    rows = []
    for k in range(7):
        s = 1.0 - 0.97 * k / 6.0
        rows.append([(c[0] + (x - c[0]) * s, c[1] + (y - c[1]) * s,
                      zi(c[0] + (x - c[0]) * s, c[1] + (y - c[1]) * s))
                     for (x, y) in _resample(inner, 96)])
    pn = grid_mesh("SU7_Bonnet_Panel", rows, col, paint, wrap_t=True)
    M.orient(pn.data, lambda p: (0.0, 0.0, -1.0))
    made.append(pn)
    hexes, ncell = _hex_cells(col, hood)
    made.append(hexes)
    # two flat pockets at the rear centre
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("SU7_Bonnet_Pocket%d" % k, _rrect(1.20, sy * 0.115, 0.050, 0.068, 0.012),
                           zi, 0.0065, col, paint, 0.001))
    # the plugs: two large at the nose, two cone-like stops at its corners, a few dots
    for k, sy in enumerate((-1, 1)):
        made.append(_disc("SU7_Bonnet_Plug%d" % k, 2.135, sy * 0.25, 0.030, zi, 0.014, col, satin, n=18,
                          lift=0.002))
        made.append(_disc("SU7_Bonnet_Stop%d" % k, 2.060, sy * 0.58, 0.017, zi, 0.020, col, satin, n=14,
                          lift=0.002))
        made.append(_disc("SU7_Bonnet_Dot%d" % k, 1.30, sy * 0.745, 0.008, zi, 0.008, col, satin, n=10,
                          lift=0.001))
        made.append(_disc("SU7_Bonnet_Dot%d" % (k + 2), 2.00, sy * 0.70, 0.008, zi, 0.008, col, satin,
                          n=10, lift=0.001))
        # the cast bracket the strut's head ends in
        made.append(_prism("SU7_Bonnet_Bracket%d" % k, _rrect(1.14, sy * 0.690, 0.034, 0.042, 0.010),
                           zi, 0.032, col, paint, 0.001))
    return made


def bonnet_hinge():
    return Vector((HINGE[0], 0.0, HINGE[1]))


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


def split_stripes(x_cut=2.0):
    """The silver racing stripes run on over the nose: cut them along the hood's
    shut line (an exact boolean with a slot as wide as the gap) and keep the
    hood's part as SU7Ultra_Stripes_Hood, the nose's as SU7Ultra_Stripes_Nose.
    Returns the two objects."""
    from carkit import cut as C
    from carkit import mesh as M
    import su7_panels as PN
    ob = bpy.data.objects[STRIPES]
    M.apply_modifiers(ob)
    hood = Hood()
    # the hood's front edge across the stripes' width, from the panel's boundary
    line = sorted(((x, y) for (x, y) in hood_outline() if x > 2.2 and abs(y) < 0.17), key=lambda p: p[1])
    path, nrm = [], []
    for (x, y) in line:
        z = hood.zc(x - 0.002, y) + 0.0
        path.append((x + 0.5 * PN.GAP, y, z))
        nrm.append((0.0, 0.0, 1.0))
    sheet = C.sheet_bvh(ob)
    slot = C.slot("_stripe_cut", path, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [slot], "stripe_")
    C.prune_off_sheet(ob, sheet)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    comps = [c for c in _components(bm) if len(c) > 3]
    mine = [c for c in comps if min(f.calc_center_median().x for f in c) < x_cut]
    other = [c for c in comps if c not in mine]
    if not mine or not other:
        raise RuntimeError("the shut line did not split the bonnet stripes (%d / %d pieces)" % (len(mine), len(other)))

    def piece(name, comps_):
        keep = {f.index for c in comps_ for f in c}
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        dead = [f for f in b2.faces if f.index not in keep]
        bmesh.ops.delete(b2, geom=dead, context='FACES')
        bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
        me = bpy.data.meshes.new(name + "_mesh")
        b2.to_mesh(me)
        b2.free()
        for m in ob.data.materials:
            me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
        new = bpy.data.objects.new(name, me)
        new.matrix_world = ob.matrix_world
        return new
    hood_part = piece("SU7Ultra_Stripes_Hood_part", mine)
    nose_part = piece("SU7Ultra_Stripes_Nose", other)
    cols = list(ob.users_collection)
    bm.free()
    old = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    for c in cols:
        c.objects.link(hood_part)
        c.objects.link(nose_part)
    return hood_part, nose_part


def split_bonnet():
    """SU7_Bonnet: the hood, its stripes and everything under it as a node of
    its own, origin on the hinge axis (which runs along y)."""
    from carkit import export as X
    col = bpy.data.collections.get(GROUP[1]) or bpy.data.collections.new(GROUP[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    under = build_hood_underside(col)
    stripes, _nose = split_stripes()
    hood = bpy.data.objects[HOOD]
    names = [o.name for o in under]
    for ob in (hood, stripes):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
        names.append(ob.name)
    bonnet = X.join("SU7_Bonnet", [hood.name] + [n for n in names if n != hood.name])
    h = bonnet_hinge()
    bonnet.data.transform(Matrix.Translation(-h))
    bonnet.matrix_world = Matrix.Translation(h)
    bonnet["hinge"] = tuple(h)
    bonnet["open_deg"] = OPEN_DEG
    return bonnet


def bonnet_groups():
    return [GROUP]


def set_bonnet(deg):
    """Preview: swing the bonnet `deg` open (nose up)."""
    ob = bpy.data.objects.get("SU7_Bonnet")
    if ob is not None:
        h = bonnet_hinge()
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')


def open_hull(hull="SU7Ultra_Shell_Shadow"):
    """Cut the hull's roof away under the bonnet (an exact boolean with a prism
    of the bay's plan, like the other hull cuts), so the tub has room."""
    from carkit import cut as C
    from carkit import mesh as M
    ob = bpy.data.objects[hull]
    M.apply_modifiers(ob)
    sheet = C.sheet_bvh(ob)
    plan = _resample(inset_poly(hood_outline(), 0.045), 160)
    cutter = C.prism_dir("_bay", [(x, y, 1.30) for (x, y) in plan], (0.0, 0.0, 1.0),
                         back=0.75, front=0.0)
    before, after = C.difference(ob, [cutter], "bay_")
    removed = C.prune_off_sheet(ob, sheet)
    return before, after, removed
