"""Denza Z9 front end, rebuilt from the black car's straight-on photograph (c1_0034.jpg) through its solved camera.

What the photograph shows (z9_frontdata has the outlines):
    * the headlamp is ONE swept blade, blunt and tall at the fender's crown and running down to a sharp tip beside the
      emblem; under it a slim dark "eyebrow" DRL (a glass wedge that goes on as a black spear)
    * the bumper is a painted fascia with parking sensors, the washer jet's cap and a long hairline-outlined bar above the
      plate; its lower edge sweeps down from each outer corner to the plate, and under that edge one dark opening holds a
      sensor module in each pocket and the four-row radiator grille with its radar pod; a body-colour "wing" crosses each
      pocket's foot (fixed at the outer end, pointing at the centre); a black chip lip runs along the bottom

Every outline is read in photo pixels and laid on the model through the photo's own rays (carkit.photolay).
"""
import math
import bpy
from mathutils import Vector, Euler

import z9_surface as S
import z9_nose as N
import z9_frontdata as FD
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit import photolay as PL
from carkit.body import fascia as FA
from carkit.parts import fittings

NOSE = N.NOSE

# ------------------------------------------------------------------ the photo's camera
# c1_0034.jpg through z9_ref_match "front_black": 8.107 m ahead, 0.516 m up, pitched up 3.67 deg, f 5561 px (3840 x 2880).
FRONT_CAM = dict(loc=(8.107, 0.0, 0.516), rot=(93.67, 0.0, 90.0), f=5561.0)
_RM = Euler(tuple(math.radians(a) for a in FRONT_CAM["rot"]), 'XYZ').to_matrix()
_LOC = Vector(FRONT_CAM["loc"])


def _ray(u, v):
    """The world ray through pixel (u, v) of the photograph's LEFT half, put on the car's +y half: the nose's centre line
    is at FD.UC in the photograph, 17 px right of the picture's own centre column (the camera stands a little off axis), so
    the column is taken from there and mirrored."""
    f = FRONT_CAM["f"]
    um = 1920.0 + (FD.UC - u)
    d = _RM @ Vector(((um - 1920.0) / f, -(v - 1440.0) / f, -1.0))
    return _LOC.copy(), d.normalized()


def _px_yz(u, v):
    """(|y|, z) of the nose surface under the photo pixel: the ray, the nose's x there, again."""
    o, d = _ray(u, v)
    x = 2.5
    y = z = 0.0
    for _ in range(5):
        p = o + d * ((x - o.x) / d.x)
        y, z = p.y, p.z
        x = NOSE.x_at(abs(y), max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z)))
    return (abs(y), z)


def _skin_x(y, z):
    return NOSE.x_at(abs(y), max(NOSE.Z_LO + 0.004, min(NOSE.Z_HI - 0.004, z)))


# the painted panels the photo's rays meet: the uncut fascia, the front fender, the hood
SURF_PANELS = ("Z9_Fascia", "Z9_Fender_Front", "Z9_Hood")
_SURF = []


def _surf():
    if not _SURF:
        _SURF.append(PL.Surf(SURF_PANELS, inside=(1.2, 0.0, 0.6), x_range=(2.65, 1.70)))
    return _SURF[0]


def _on_surface(u, v, inset=0.0):
    s = _surf()
    # a ray that grazes past the body's limb (the model's corner is a few mm narrower than the photographed car's) is moved
    # inboard, 3 px at a time, until it meets the panels: the point is then on the limb, not on a closest-approach guess
    for k in range(0, 60, 3):
        o, d = _ray(u + k, v)
        if s.tree.ray_cast(o, d)[0] is not None:
            break
    else:
        o, d = _ray(u, v)
    h = s.hit(o, d, inset)
    if h is None:
        raise RuntimeError("z9_front: the photo ray through (%g, %g) misses the nose" % (u, v))
    return h


LAY = PL.Lay(_on_surface, geom.away_from((1.90, 0.45, 0.65)))


def _surf_cut(ob):
    """First cut of the fascia, run on the uncut sheet: the panels as they stand for the photo's rays."""
    del _SURF[:]
    _surf()


# ------------------------------------------------------------------ small helpers
def _face(y, z, d=0.0):
    w, v = NOSE.wv_at(abs(y), z)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _boxes(name, boxes, collection, mat):
    """Many axis-aligned boxes as one mesh: boxes = [(x0, x1, y0, y1, z0, z1)]."""
    verts, faces = [], []
    for (x0, x1, y0, y1, z0, z1) in boxes:
        k = len(verts)
        for sx in (x0, x1):
            for sy in (y0, y1):
                for sz in (z0, z1):
                    verts.append((sx, sy, sz))
        faces += [[k + a, k + b, k + c, k + d] for (a, b, c, d) in
                  ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    # every face is wound outward for x0 < x1, y0 < y1, z0 < z1
    return M.obj(name, verts, faces, collection, mat, smooth=False)


def _circle(c, r, n=20):
    return [(c[0] + r * math.cos(2.0 * math.pi * i / n), c[1] + r * math.sin(2.0 * math.pi * i / n)) for i in range(n)]


def _ellipse(c, a, b, ang, n=28):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        x, y = a * math.cos(t), b * math.sin(t)
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


def _rrect(u0, v0, u1, v1, r, k=4):
    pts = []
    for (cx, cy, a0) in ((u1 - r, v0 + r, -90.0), (u1 - r, v1 - r, 0.0), (u0 + r, v1 - r, 90.0), (u0 + r, v0 + r, 180.0)):
        for i in range(k + 1):
            a = math.radians(a0 + 90.0 * i / k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _dist_fn(poly, base, peak, reach):
    """depth(u, v) = base + peak * smoothstep(distance from the polygon's edge / reach): a convex lens."""
    import numpy as np
    P = np.array(list(poly) + [poly[0]], float)
    A, B = P[:-1], P[1:]
    AB = B - A
    L2 = (AB ** 2).sum(axis=1) + 1e-9

    def f(u, v):
        p = np.array([u, v], float)
        t = np.clip(((p - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        d = float(np.sqrt(((A + AB * t[:, None] - p) ** 2).sum(axis=1)).min())
        s = min(1.0, d / reach)
        return base + peak * s * s * (3.0 - 2.0 * s)
    return f


# ------------------------------------------------------------------ the cavity (cut, back, walls)
_CAV_CORNERS = (0, 10, 11, 12, 13, 17)      # the pocket's outer tip, the centre-line ends, the wing's lower corner and tip


def _cavity_px():
    """The cavity's outline in photo pixels: the read points joined by splines, sharp only at the corners."""
    return PL.smooth_loop(FD.CAVITY, _CAV_CORNERS, 5)


def _cavity_yz(cut):
    """The cavity's outline as (y, z) of the nose; its centre-line edge crosses the centre (y -0.02) for the cut so the two
    halves meet, and is on it (y 0) for the parts that are mirrored."""
    pts = []
    for (u, v) in _cavity_px():
        y, z = _px_yz(u, v)
        if u >= FD.UC - 2.0:
            y = -0.02 if cut else 0.0
        pts.append((y, z))
    return pts


def _depth(y, z):
    """How far behind the skin the cavity's back wall stands: 4.5 cm in the pockets, 13 cm behind the radiator."""
    t = geom.smoothstep((abs(y) - 0.30) / 0.10)
    return 0.045 + 0.085 * (1.0 - t)


def _back_x(y, z):
    return _skin_x(y, z) - _depth(y, z)


def _cut_fascia(ob):
    cutters = [C.prism_x("_cut_cavity_" + ob.name, _cavity_yz(True), S.HALF_L + 0.30, S.HALF_L - 0.60)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_fascia(collection, lib):
    fascia = FA.cap_panel(
        "Z9_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.002, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 40, 44, mat="paint", top_to_centre=True, cuts=(_surf_cut, _cut_fascia),
    )
    return [fascia]


def build_cavity(collection, lib):
    """The dark opening's inside: a back wall (4.5 cm behind the skin in the pockets, 13 cm behind the radiator), a wall
    all round the cut's edge, the radiator (four rows of fin stacks between ribs) and the radar pod, and in each pocket the
    sensor module and the small square cover."""
    made = []
    poly = _cavity_yz(False)
    poly_back = [(y, max(z, N.NOSE_Z_LO + 0.003)) for (y, z) in poly]
    # 1. the back wall: a fill of the outline in (y, z) lifted onto x = skin - depth
    pts_mm = [(1000.0 * y, 1000.0 * z) for (y, z) in poly_back]
    pts2, tris = PL.fill(pts_mm, 16.0)
    verts = []
    for (ym, zm) in pts2:
        y, z = 0.001 * ym, 0.001 * zm
        verts.append((_back_x(y, z), y, z))
    back = M.obj("Z9_Cavity_Back", verts, [list(t) for t in tris], collection, lib["shadow"])
    M.orient(back.data, lambda c: (1.0, 0.0, 0.0))
    M.mirror_y(back)
    made.append(back)

    # 2. the wall round the cut: from the wing's lower corner round the pockets to the plate, a strip from the skin back to
    # the wall (resampled to 9 mm so it follows the curve the cut leaves on the curved nose)
    n = len(poly)
    px = _cavity_px()
    i0 = min(range(n), key=lambda i: (px[i][0] - 1349.0) ** 2 + (px[i][1] - 2150.0) ** 2)
    i1 = min(range(n), key=lambda i: (px[i][0] - 1937.0) ** 2 + (px[i][1] - 1994.0) ** 2)
    path = [poly[(i0 + k) % n] for k in range(((i1 - i0) % n) + 1)]
    dense = [path[0]]
    for a, b in zip(path, path[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        m = max(1, int(L / 0.014))
        for k in range(1, m + 1):
            dense.append((a[0] + (b[0] - a[0]) * k / m, a[1] + (b[1] - a[1]) * k / m))
    top, bot = [], []
    for (y, z) in dense:
        x = _skin_x(y, z)
        top.append((x - 0.0005, max(0.0, y), z))
        bot.append((_back_x(y, z), max(0.0, y), z))
    wall = M.strip("Z9_Cavity_Wall", top, bot, collection, lib["shadow"])
    M.orient(wall.data, lambda c: (-0.2, -0.3 * (1.0 if c[1] > 0 else -1.0), 0.0))
    M.mirror_y(wall)
    M.finish(wall, thickness=0.002, bevel=0.0)
    made.append(wall)

    # 3. the radiator
    x_g = _skin_x(0.0, 0.25) - 0.085
    boxes = []
    for (v0, v1, uend) in FD.GRILLE_ROWS:
        z_lo = _px_yz(FD.GRILLE_U0, v1)[1]
        z_hi = _px_yz(FD.GRILLE_U0, v0)[1]
        cuts_u = [FD.GRILLE_U0] + [r + s * 2.5 for r in FD.GRILLE_RIBS for s in (-1, 1)] + [uend]
        spans = [(cuts_u[0], cuts_u[1]), (cuts_u[2], cuts_u[3]), (cuts_u[4], cuts_u[5])]
        for (ua, ub) in spans:
            ya, yb = _px_yz(ub, v0)[0], _px_yz(ua, v0)[0]
            nb = 5
            h = (z_hi - z_lo) / nb
            for k in range(nb):
                za, zb = z_lo + k * h + 0.0004, z_lo + (k + 1) * h - 0.0004
                boxes.append((x_g - 0.014, x_g, min(ya, yb), max(ya, yb), za, zb))
    rad = _boxes("Z9_Radiator", boxes, collection, lib["radiator"])
    M.mirror_y(rad)
    made.append(rad)
    # the ribs between the sections, and the grey end caps
    z_top = _px_yz(FD.GRILLE_U0, FD.GRILLE_ROWS[0][0] - 4)[1]
    z_bot = _px_yz(FD.GRILLE_U0, FD.GRILLE_ROWS[-1][1] + 4)[1]
    ribs = []
    for r in FD.GRILLE_RIBS:
        y = _px_yz(r, 2060)[0]
        ribs.append((x_g - 0.018, x_g + 0.004, y - 0.0028, y + 0.0028, z_bot, z_top))
    yc = _px_yz(FD.GRILLE_U0 - 12, 2060)[0]
    y0 = _px_yz(FD.GRILLE_U0, 2060)[0]
    ribs.append((x_g - 0.018, x_g + 0.002, min(y0, yc), max(y0, yc), z_bot, z_top))
    made.append(_boxes("Z9_Radiator_Frame", ribs, collection, lib["shadow"]))
    M.mirror_y(made[-1])

    # 4. the radar pod: a rounded box in front of the radiator's middle
    u0, v0, u1, v1 = FD.POD
    hy = _px_yz(u0, 0.5 * (v0 + v1))[0]
    z_lo, z_hi = _px_yz(u0, v1)[1], _px_yz(u0, v0)[1]
    pod = _boxes("Z9_Radar_Pod", [(x_g - 0.010, x_g + 0.036, -hy, hy, z_lo, z_hi)], collection, lib["radar"])
    M.bevel(pod, 0.011, 3, 40.0)
    made.append(pod)
    # the little lens that hangs under the plate
    cu, cv, cr = FD.CAMERA
    yy, zz = _px_yz(cu, cv)
    made.append(_boxes("Z9_Front_Camera", [(x_g + 0.020, x_g + 0.036, -0.012, 0.012, zz - 0.007, zz + 0.007)], collection,
                       lib["cap_black"]))
    M.bevel(made[-1], 0.005, 2, 40.0)

    # 5. a pocket's sensor module and its cover
    mu0, mv0, mu1, mv1 = FD.MODULE
    ya, yb = _px_yz(mu1, mv0)[0], _px_yz(mu0, mv0)[0]
    za, zb = _px_yz(mu0, mv1)[1], _px_yz(mu0, mv0)[1]
    yc, zc = 0.5 * (ya + yb), 0.5 * (za + zb)
    xb = _back_x(yc, zc)
    mod = _boxes("Z9_Module", [(xb, xb + 0.034, ya, yb, za, zb)], collection, lib["black_gloss"])
    M.bevel(mod, 0.004, 2, 40.0)
    M.mirror_y(mod)
    made.append(mod)
    # the white-grey window cylinder and the dark lens beside it
    cyu, cyv, chw, chh = FD.MODULE_CYL
    ycy, zcy = _px_yz(cyu, cyv)
    made += _cyl("Z9_Module_Window", (xb + 0.034, ycy, zcy), 0.0105, 0.0185, 0.010, collection, lib["lamp_window"])
    lu, lv, lr = FD.MODULE_LENS
    yl, zl = _px_yz(lu, lv)
    made += _cyl("Z9_Module_Lens", (xb + 0.034, yl, zl), 0.0075, 0.0075, 0.004, collection, lib["lamp_smoked"], axis_x=True)
    # the square cover beside it (flush with the back wall, a satin plate with a bevel)
    cu0, cv0, cu1, cv1 = FD.COVER
    yca, ycb = _px_yz(cu1, cv0)[0], _px_yz(cu0, cv0)[0]
    zca, zcb = _px_yz(cu0, cv1)[1], _px_yz(cu0, cv0)[1]
    xc = _back_x(0.5 * (yca + ycb), 0.5 * (zca + zcb))
    cov = _boxes("Z9_Module_Cover", [(xc, xc + 0.008, yca, ycb, zca, zcb)], collection, lib["cap_black"])
    M.bevel(cov, 0.003, 2, 40.0)
    M.mirror_y(cov)
    made.append(cov)
    return made


def _cyl(name, c, r_y, r_z, h, collection, mat, axis_x=False, seg=20):
    """A short cylinder facing forward (+x) at c = (x of its back, y, z): an ellipse of radii (r_y, r_z), h long."""
    verts = []
    for k in range(seg):
        a = 2.0 * math.pi * k / seg
        verts.append((c[0], c[1] + r_y * math.cos(a), c[2] + r_z * math.sin(a)))
    for k in range(seg):
        a = 2.0 * math.pi * k / seg
        verts.append((c[0] + h, c[1] + r_y * math.cos(a), c[2] + r_z * math.sin(a)))
    faces = [[k, (k + 1) % seg, seg + (k + 1) % seg, seg + k] for k in range(seg)]
    faces.append(list(range(seg, 2 * seg)))
    ob = M.obj(name, verts, faces, collection, mat)
    M.orient(ob.data, lambda p, c0=c: (p[0] - (c0[0] + 0.5 * h), p[1] - c0[1], p[2] - c0[2]))
    M.mirror_y(ob)
    return [ob]


# ------------------------------------------------------------------ painted fascia details
def build_fascia_details(collection, lib):
    made = []
    # the long bar above the plate: a body-colour pad a little proud of the paint, outlined by a hairline
    pad = FD.PAD
    made.append(LAY.region("Z9_Pad", PL.grow(pad, -0.5), 0.0008, lib["paint"], collection, step=14.0, thick=0.0010))
    path = pad[0:7][::-1] + pad[7:][::-1]
    made.append(LAY.ribbon("Z9_Pad_Line", path, 0.0008, 0.0006, lib["shadow"], collection, step=14.0, thick=0.0008))
    # the parking sensors: a dark disc in a thin ring
    for k, (u, v) in enumerate(FD.SENSORS):
        made.append(LAY.region("Z9_Sensor_Disc_%d" % k, _circle((u, v), 8.0, 16), 0.0004, lib["cap_black"], collection,
                               step=3.0, thick=0.0006))
        made.append(LAY.ribbon("Z9_Sensor_Ring_%d" % k, _circle((u, v), 9.5, 18), 0.0009, 0.0005, lib["black_gloss"], collection,
                               step=4.0, thick=0.0006, closed=True))
    # the washer jet's cap: a lozenge outlined by a hairline
    wu, wv, wa, wb, wang = FD.WASHER
    made.append(LAY.ribbon("Z9_Washer_Cap", _ellipse((wu, wv), wa, wb, wang), 0.0007, 0.0005, lib["shadow"], collection,
                           step=8.0, thick=0.0006, closed=True))
    return made


def build_chin(collection, lib):
    """The black chip lip along the bottom edge, full width, standing a little proud of the cut's lower edge."""
    ns = 36
    ch_lo, ch_up = [], []
    for i in range(ns + 1):
        y = 0.88 * i / float(ns)
        ch_lo.append(_face(y, 0.1445, d=0.007)[0])
        ch_up.append(_face(y, 0.176, d=0.007)[0])
    cols = [[ch_lo[c], ch_up[c]] for c in range(ns + 1)]
    chin = M.mesh_from_rows("Z9_Chin_Lip", cols, collection)
    chin.data.materials.append(lib["black_trim"])
    M.mirror_y(chin)
    M.finish(chin, thickness=0.003, bevel=0.0)
    return [chin]


# ------------------------------------------------------------------ the headlamp and the eyebrow DRL
LAMP_UP = 0.0014


def _smooth_loop(pts, corners, step):
    return PL.resample_loop(PL.smooth_loop(pts, corners, 4), step)


def _scan_columns(poly, n, edge=0.6):
    """Columns across a closed outline that is one blade along u: for n values of u (clustered at both ends) the first and last
    crossing of the vertical line with the outline, as (u, v_top, v_bottom)."""
    us = [p[0] for p in poly]
    u0, u1 = min(us) + edge, max(us) - edge
    m = len(poly)
    cols = []
    for i in range(n):
        s = 0.5 - 0.5 * math.cos(math.pi * i / float(n - 1))
        u = u0 + (u1 - u0) * s
        vs = []
        for k in range(m):
            (ua, va), (ub, vb) = poly[k], poly[(k + 1) % m]
            if ua != ub and (ua <= u < ub or ub <= u < ua):
                vs.append(va + (vb - va) * (u - ua) / (ub - ua))
        if len(vs) >= 2:
            cols.append((u, min(vs), max(vs)))
    return cols


def _lens_grid(name, poly, depth, mat, collection, ncol=56, nk=12, thick=0.0):
    """The outline as a quad grid laid on the body (columns across the blade): a glossy convex lens built from long quads
    shades smoothly; a Delaunay fill's skinny triangles zigzag in the studio's reflections."""
    rows = []
    for (u, vt, vb) in _scan_columns(poly, ncol):
        row = []
        for k in range(nk + 1):
            v = vt + (vb - vt) * k / float(nk)
            p, n = _on_surface(u, v)
            d = depth(u, v) if callable(depth) else depth
            row.append(tuple(p + n * d))
        rows.append(row)
    ob = M.mesh_from_rows(name, rows, collection)
    ob.data.materials.append(mat)
    M.orient(ob.data, LAY.outward)
    if thick:
        M.solidify(ob, thick)
    M.mirror_y(ob)
    return ob


def build_lamps(collection, lib):
    """The headlamp as a CLEAR glass cover over a real inside, as photographed (the photo shows the projector modules, the silver
    reflector and the light guide through the lens): a black rim, a dark floor, a silver reflector, three bezelled LED units and the
    light guide, all under a convex lens that is mostly transparent (alpha-blended, M_Z9_Lamp_Lens). Depths are metres above the
    paint: the rim 1.4 mm, the floor 1.8, the reflector 2.1, the units 2.4-2.9, the guide 3.0, the lens 3.6 + a 4 mm dome."""
    made = []
    out = _smooth_loop(FD.LAMP_OUT, (11,), 9.0)
    lens_poly = PL.grow(out, -5.0)
    bulge = _dist_fn(lens_poly, 0.0036, 0.0040, 46.0)
    made.append(_lens_grid("Z9_Lamp_Rim", PL.grow(out, 0.8), LAMP_UP, lib["lamp_frame"], collection, ncol=24, nk=6, thick=0.0016))
    made.append(_lens_grid("Z9_Lamp_Floor", PL.grow(out, -3.0), 0.0018, lib["lamp_floor"], collection, ncol=22, nk=6))
    made.append(_lens_grid("Z9_Lamp_Reflector", PL.grow(out, -9.0), 0.0021, lib["lamp_reflector"], collection, ncol=22, nk=6))
    # the LED units: a bezel and a pad each, standing on the floor under the lens (lit with the low beam)
    for k, (cu, cv, hw, hh) in enumerate(FD.LAMP_MODULES):
        hw, hh = 0.72 * hw, 0.72 * hh
        pts = _rrect(cu - hw, cv - hh, cu + hw, cv + hh, 4.0, 3)
        made.append(LAY.ribbon("Z9_Lamp_Bezel_%d" % k, _rrect(cu - hw - 2, cv - hh - 2, cu + hw + 2, cv + hh + 2, 5.0, 3), 0.0016,
                               0.0024, lib["lamp_hair"], collection, step=5.0, thick=0.0008, closed=True))
        made.append(LAY.region("Z9_Lamp_Module_%d" % k, pts, 0.0029, lib["lamp_module"], collection, step=5.0, thick=0.0004))
    # the light guide along the upper rim and the silver hairline along the lower, both inside
    made.append(LAY.ribbon("Z9_Lamp_DRL", FD.LAMP_DRL, 0.0017, 0.0031, lib["led_white"], collection, step=9.0, thick=0.0006))
    made.append(LAY.ribbon("Z9_Lamp_Hair", FD.LAMP_HAIR, 0.0007, 0.0027, lib["lamp_hair"], collection, step=9.0, thick=0.0005))
    # the glass: a thin silver edge, then the lens
    made.append(LAY.ribbon("Z9_Lamp_Edge", lens_poly, 0.0007, 0.0037, lib["lamp_hair"], collection, step=8.0, thick=0.0005,
                           closed=True))
    made.append(_lens_grid("Z9_Lamp_Lens", lens_poly, bulge, lib["lamp_lens"], collection, ncol=56, nk=14))
    # the eyebrow: a clear wedge over a black floor (its rim), the spear that runs on to its point, a blue-white line under the glass
    g = PL.resample_loop(PL.smooth_loop(FD.DRL_GLASS, (4,), 4), 7.0)
    gb = _dist_fn(g, 0.0026, 0.0026, 14.0)
    made.append(_lens_grid("Z9_Eyebrow_Rim", PL.grow(g, 1.5), 0.0010, lib["lamp_frame"], collection, ncol=36, nk=6, thick=0.0014))
    made.append(LAY.ribbon("Z9_Eyebrow_Line", FD.DRL_LINE, 0.0010, 0.0019, lib["led_white"], collection, step=8.0, thick=0.0005))
    made.append(_lens_grid("Z9_Eyebrow_Glass", g, gb, lib["lamp_lens"], collection, ncol=40, nk=8))
    made.append(LAY.ribbon("Z9_Eyebrow_Spear", FD.DRL_SPEAR, lambda t: 0.0036 * (1.0 - t) + 0.0005, 0.0012, lib["lamp_frame"],
                           collection, step=9.0, thick=0.0010))
    return made


# --------------------------------------------------------------- emblem
def build_emblem(collection, lib):
    """The Denza badge on the nose, under the hood's edge (c1_0034: centre u 1943, v 1727, 74 px across = 72 mm)."""
    import z9_logo as LG
    eu, ev, er = FD.EMBLEM
    y, z = _px_yz(eu, ev)
    p, n = _face(0.0, z, 0.0)
    centre = tuple(p[i] - n[i] * 0.0015 for i in range(3))
    return LG.build("Z9_Emblem_Front_", collection, lib, centre, n, er * 0.00098)


# -------------------------------------------------------- plate
PLATE_PITCH = 25.0


def build_plate(collection, lib):
    """The front plate: the 480 x 140 mm sign (c1_0034: 493 px wide, its bottom edge z 0.31). A flat board: it takes the nose's
    pitch there and none of its yaw, on a mount block as deep as the nose's recession across the plate's width."""
    pitch = math.radians(PLATE_PITCH)
    n_plate = (math.cos(pitch), 0.0, -math.sin(pitch))
    p_c, _ = _face(0.0, 0.400, d=0.006)
    p_plate_f = (p_c[0], 0.0, p_c[2])
    p_mount = tuple(p_plate_f[i] - n_plate[i] * 0.003 for i in range(3))
    made = []
    made += fittings.plate("Z9_Plate_Mount_Front", p_mount, n_plate, collection, lib, w=0.500, h=0.150, depth=0.080,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Z9_Plate_Front", p_plate_f, n_plate, collection, lib, w=0.480, h=0.140, depth=0.004,
                           texts=[("DENZA Z9", 0.0, 0.038, False, True)],
                           mat="black_gloss", text_mat="machined")
    return made


# -------------------------------------------------------- hood ridges
RIDGE_X0 = 1.02          # a little ahead of the cowl
RIDGE_X1 = 2.56          # where the sweep would end if the hood went on (it does not: see _ridge_end)


def _ridge_xy(t):
    """The ridge's centreline on the plan, one side (+y): from the cowl at y 0.44 forward and inwards."""
    return RIDGE_X0 + (RIDGE_X1 - RIDGE_X0) * t, 0.44 - 0.22 * (t ** 1.2)


def _ridge_end(inset=0.012):
    """The sweep parameter at which the ridge reaches the hood's front edge (the shut line to the nose cap,
    N.JOIN_F at the hood's own v there), stopped `inset` short of it."""
    for k in range(401):
        t = k / 400.0
        x, y = _ridge_xy(t)
        if x >= N.JOIN_F(S.v_at_y_upper(x, y)) - inset:
            return t
    return 1.0


def build_hood_features(collection, lib):
    """Twin soft ridges on the front hood (c1_0002.jpg: two creases that bound a central panel and run to the lamps' inner
    tips), sweeping forward from the cowl and stopping at the hood's front edge. They lie ON the hood's own surface and
    rise and fall along their length, so they end flush; one side is built and mirrored. They join the bonnet
    (z9_bays.split_bonnet) and swing with it."""
    t_end = _ridge_end()
    nc = 40
    cols = []
    for i in range(nc + 1):
        s = i / float(nc)
        x, y_c = _ridge_xy(t_end * s)
        env = geom.smoothstep(s / 0.10) * geom.smoothstep((1.0 - s) / 0.18)
        row = []
        for dy in (-0.020, -0.012, -0.005, 0.0, 0.005, 0.012, 0.020):
            v = S.v_at_y_upper(x, y_c + dy)
            y_s, z_s = S.section_v(x, v)
            lift = 0.0060 * env * math.cos(0.5 * math.pi * dy / 0.020) ** 2.0
            row.append((x, y_s, z_s + lift - 0.0006))
        cols.append(row)
    ob = M.mesh_from_rows("Z9_Hood_Ridge", cols, collection)
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0016, bevel=0.0)
    return [ob]


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    del _SURF[:]
    made += build_fascia(collection, lib)
    made += build_cavity(collection, lib)
    made += build_fascia_details(collection, lib)
    made += build_chin(collection, lib)
    made += build_lamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_plate(collection, lib)
    made += build_hood_features(collection, lib)
    return made
