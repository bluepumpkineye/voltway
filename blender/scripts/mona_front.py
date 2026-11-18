"""XPeng Mona L05 (小鹏MONA L05) front end.

Built cleanly in 3D on the extended wrap-around fascia (`N.NOSE`), flush front fenders,
and flush hood:
  - `MONA_Fascia`: continuous pole-free wrap-around bumper with a pointed apex at badge/DRL height,
    backward-raked lower bumper, sleek sloped upper nose into the flush hood, and a widened
    trapezoidal central air intake whose outer edges angle outward toward the bottom corners.
  - `MONA_Apron`, `MONA_Intake_Tunnel`, `MONA_Intake_Shutter`, `MONA_Intake_Bar`: recessed
    gloss-black central air intake cavity with physical tunnel depth and louvers.
  - `MONA_Front_Lip`: solid integrated dark-grey lower lip connected directly to the bottom edge
    of the purple bumper and wrapping continuously around the bottom corners into `MONA_Clad_F`.
  - `MONA_Lamp_*`: T-shaped headlights projected via cylindrical surface coords (`theta_deg, z`)
    at ~4-5 mm resolution, sitting completely flat and flush inside the fender contour with an
    underlying paint pocket recess so no paint bleeds through.
  - `MONA_Emblem_X`, `MONA_Sensor_*`, `MONA_Camera_Dot`, `MONA_Hood_Line`.
"""
import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import mona_surface as S
import mona_nose as N
from carkit import geom
from carkit import photolay as PL
from carkit import mesh as M
from carkit import cut as C
from carkit.body import panels as BP
from carkit.parts import fittings
import carkit.place as P

BODY = N.BODY
NOSE = N.NOSE

PLACER = P.Placer(BODY.proud)


# ---------------------------------------------------- cylindrical projection on front skin
# Map `(u_mm, v_mm) = (deg * 15.0, z * 1000.0)` so 1 unit ~ 1 mm in surface arc length and height.
_CYL_OX = 1.75
_U_PER_DEG = 15.0
SURF_PANELS = ("MONA_Fascia", "MONA_Fender_Front", "MONA_Hood")
_SURF = []


def _C(pts):
    """Convert `(theta_deg, z_metres)` outline points to `(u_mm, v_mm)` cylindrical space."""
    return [(deg * _U_PER_DEG, z * 1000.0) for (deg, z) in pts]


class _CylSurf:
    """BVH over the uncut front half-sheets (+Y) queried by outward cylindrical rays."""

    def __init__(self, names=SURF_PANELS, inside=(1.2, 0.0, 0.6)):
        _INSIDE = Vector(inside)
        verts, tris, norms = [], [], []
        for nm in names:
            ob = bpy.data.objects[nm]
            me = ob.data
            me.calc_loop_triangles()
            mw = ob.matrix_world
            base = len(verts)
            wv = [mw @ v.co for v in me.vertices]
            acc = [Vector() for _ in wv]
            for poly in me.polygons:
                n = (mw.to_3x3() @ poly.normal) * poly.area
                for i in poly.vertices:
                    acc[i] += n
            out = sum(a.dot(w - _INSIDE) for a, w in zip(acc, wv))
            k = 1.0 if out >= 0.0 else -1.0
            for a in acc:
                if a.length > 0.0:
                    a.normalize()
            verts += wv
            norms += [a * k for a in acc]
            tris += [(base + t.vertices[0], base + t.vertices[1], base + t.vertices[2])
                     for t in me.loop_triangles]
        self.verts, self.tris, self.norms = verts, tris, norms
        self.tree = BVHTree.FromPolygons(verts, tris)

    def hit(self, u_mm, v_mm):
        rad = math.radians(u_mm / _U_PER_DEG)
        z = v_mm / 1000.0
        # Above z = 0.83 on the curving fender crown, point the ray gently down-out for normal incidence.
        tz = -0.14 * max(0.0, (z - 0.83) / 0.14)
        o = Vector((_CYL_OX, 0.0, z - tz * 0.68))
        d = Vector((math.cos(rad), math.sin(rad), tz)).normalized()
        h = self.tree.ray_cast(o, d, 2.2)
        if h[0] is None:
            # Fallback to nearest point along approximate corner radius ~0.86 m
            h = self.tree.find_nearest(Vector((_CYL_OX + 0.86 * math.cos(rad),
                                               0.86 * math.sin(rad), z)))
        p = Vector(h[0])
        a, b, c = (self.verts[i] for i in self.tris[h[2]])
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01 or 1e-18
        wb, wc = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
        wb, wc = min(1.0, max(0.0, wb)), min(1.0, max(0.0, wc))
        na, nb, nc = (self.norms[i] for i in self.tris[h[2]])
        n = (na * (1.0 - wb - wc) + nb * wb + nc * wc).normalized()
        return p, n


def _surf():
    if not _SURF:
        _SURF.append(_CylSurf())
    return _SURF[0]


def _hit(u_mm, v_mm):
    return _surf().hit(u_mm, v_mm)


LAY = PL.Lay(_hit, geom.away_from((1.90, 0.45, 0.65)))


# ------------------------------------------------------------ T-headlamp 3D cylindrical outlines
# Placed with clear painted fender margin ahead of MONA_Clad_F (x <= 2.049) while wrapping cleanly
# across the corner (deg 30..67.5) and centered vertically around the sharp nose apex (z ~ 0.785).
LAMP_OUT = _C([
    (30.0, 0.793), (38.0, 0.798), (46.0, 0.808), (51.5, 0.822),
    (55.5, 0.858), (59.8, 0.902), (63.4, 0.936), (65.0, 0.946),
    (63.4, 0.905), (61.6, 0.856), (60.2, 0.806), (59.5, 0.766),
    (59.2, 0.700), (58.8, 0.625), (58.4, 0.564), (57.4, 0.552),
    (54.8, 0.578), (52.2, 0.622), (49.6, 0.678), (47.8, 0.735),
    (46.0, 0.763), (38.0, 0.766), (30.4, 0.771),
])

LAMP_HORN = _C([
    (53.4, 0.818), (57.6, 0.864), (61.4, 0.904), (63.8, 0.928),
    (62.0, 0.880), (60.0, 0.834), (58.6, 0.804),
])

LAMP_LOWER = _C([
    (49.6, 0.740), (54.2, 0.740), (58.0, 0.748), (57.9, 0.630),
    (57.5, 0.570), (55.2, 0.592), (52.6, 0.636), (50.6, 0.688),
])

LAMP_BAR = _C([(47.2, 0.773), (53.6, 0.771), (58.9, 0.769)])
LAMP_LINE = _C([(30.8, 0.777), (38.0, 0.777), (45.0, 0.776), (48.5, 0.775)])
LAMP_HAIR_BLADE = _C([(31.2, 0.774), (38.0, 0.774), (45.0, 0.773), (48.0, 0.773)])

# Flush elevations above uncut skin (backed by cut lamp pocket in MONA_Fascia + MONA_Fender_Front)
LAMP_UP, LAMP_T = 0.0006, 0.0020
GLASS_UP, FROST_UP, RIB_UP, LINE_UP = 0.0010, 0.0013, 0.0015, 0.0017


# ------------------------------------------------------------------ fascia & wide gloss-black intake
_INTAKE_TOP_Z = 0.495
_INTAKE_BOT_Z = 0.328
_INTAKE_TOP_Y = 0.485
_INTAKE_BOT_Y = 0.720


def _intake_width_at_z(z):
    t = min(1.0, max(0.0, (_INTAKE_TOP_Z - z) / (_INTAKE_TOP_Z - _INTAKE_BOT_Z)))
    return _INTAKE_TOP_Y + (_INTAKE_BOT_Y - _INTAKE_TOP_Y) * t


def _intake_yz():
    """Widened central air intake trapezoid with outer edges angled outward to bottom corners."""
    return [
        (-0.025, _INTAKE_TOP_Z),
        (_INTAKE_TOP_Y, _INTAKE_TOP_Z),
        (_INTAKE_BOT_Y, _INTAKE_BOT_Z),
        (_INTAKE_BOT_Y + 0.020, 0.250),
        (-0.025, 0.250),
    ]


def _cyl_prism(name, poly_uv, r_in=0.50, r_out=1.40, step=4.0):
    """Build a manifold radial prism along cylindrical rays so headlamp holes cut cleanly."""
    bd = PL.resample_loop(poly_uv, step)
    if PL.area(bd) < 0.0:
        bd = bd[::-1]
    n = len(bd)
    verts_in, verts_out = [], []
    for (u_mm, v_mm) in bd:
        rad = math.radians(u_mm / _U_PER_DEG)
        z = v_mm / 1000.0
        tz = -0.14 * max(0.0, (z - 0.83) / 0.14)
        o = Vector((_CYL_OX, 0.0, z - tz * 0.68))
        d = Vector((math.cos(rad), math.sin(rad), tz)).normalized()
        verts_in.append(tuple(o + d * r_in))
        verts_out.append(tuple(o + d * r_out))
    bm = bmesh.new()
    vs_in = [bm.verts.new(p) for p in verts_in]
    vs_out = [bm.verts.new(p) for p in verts_out]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vs_in[i], vs_in[j], vs_out[j], vs_out[i]))
    bm.faces.new(list(reversed(vs_in)))
    bm.faces.new(vs_out)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cut_openings(ob):
    cut_intake = C.prism_x("_cut_intake_" + ob.name, _intake_yz(), S.X_FRONT + 0.30, S.X_FRONT - 0.65)
    cut_lamp = _cyl_prism("_cut_lamp_" + ob.name, PL.grow(LAMP_OUT, -2.5))
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [cut_intake, cut_lamp], "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _cap_pt(y, z, d=0.0):
    w, v = NOSE.wv_at(abs(y), z)
    return NOSE.offset(w, v, d)


def _cap_ribbon(name, yz, hw, d, mat, collection, thick=0.0008):
    P = [Vector(_cap_pt(y, z, d)) for (y, z) in yz]
    rows = []
    for i, p in enumerate(P):
        t = (P[min(len(P) - 1, i + 1)] - P[max(0, i - 1)]).normalized()
        w, v = NOSE.wv_at(yz[i][0], yz[i][1])
        n = Vector(NOSE.normal(w, v))
        side = n.cross(t).normalized()
        rows.append([tuple(p - side * hw), tuple(p + side * hw)])
    ob = M.mesh_from_rows(name, rows, collection)
    ob.data.materials.append(mat)
    M.orient(ob.data, geom.axial(1.0))
    if thick:
        M.solidify(ob, thick)
    M.mirror_y(ob)
    return ob


def _build_lower_lip(collection, lib):
    """Solid integrated dark-grey lower lip connected to the bumper bottom edge & wrapping to MONA_Clad_F."""
    cols = []
    nw = 36
    nx_side = 12
    # Part 1: wrap around nose from center (w=0) to fender corner JOIN_F (w=1)
    samples = []
    for i in range(nw + 1):
        w = 1.0 - (1.0 - i / float(nw)) ** 1.25
        v_top = NOSE.v_at_z(0.338, w)
        p_top = Vector(NOSE.point(w, v_top))
        n_top = Vector(NOSE.normal(w, v_top))
        v_mid = NOSE.v_at_z(0.304, w)
        p_mid = Vector(NOSE.point(w, v_mid))
        n_mid = Vector(NOSE.normal(w, v_mid))
        v_bot = NOSE.v_at_z(0.270, w)
        p_bot = Vector(NOSE.point(w, v_bot))
        n_bot = Vector(NOSE.normal(w, v_bot))
        samples.append((p_top, n_top, p_mid, n_mid, p_bot, n_bot))

    # Part 2: continue seamlessly back along S.BODY lower fender corner to meet MONA_Clad_F (x ~ 2.025)
    x_join_bot = samples[-1][4].x
    x_clad_overlap = 2.020
    for k in range(1, nx_side + 1):
        f = k / float(nx_side)
        x = x_join_bot + (x_clad_overlap - x_join_bot) * f
        pts_lvl = []
        for z_tgt in (0.338, 0.304, 0.270):
            v = S.BODY.v_at_z(x, z_tgt, 0.0, S.V_SHOULDER)
            p = Vector(S.BODY.surface(x, v))
            n = Vector(S.BODY.surface_normal(x, v))
            pts_lvl.append((p, n))
        samples.append((*pts_lvl[0], *pts_lvl[1], *pts_lvl[2]))

    for (p_top, n_top, p_mid, n_mid, p_bot, n_bot) in samples:
        # Horizontal outward vector in XY for clean bottom belly return
        h = Vector((n_bot.x, n_bot.y, 0.0))
        h = h.normalized() if h.length > 1e-6 else Vector((1.0, 0.0, 0.0))
        # Taper underbody belly return near wheel arch (x < 2.14) so nothing protrudes into wheel well
        belly_w = 0.012 + 0.056 * min(1.0, max(0.0, (p_bot.x - 2.04) / 0.14))
        p_b = Vector((p_bot.x, p_bot.y, max(0.272, p_bot.z)))
        col = [
            tuple(p_top - n_top * 0.0015 + Vector((0, 0, 0.002))),
            tuple(p_top + n_top * 0.0024),
            tuple(p_mid + n_mid * 0.0030),
            tuple(p_b + h * 0.0030),
            tuple(p_b - h * belly_w + Vector((0, 0, 0.004))),
        ]
        cols.append(col)

    lip = M.mesh_from_rows("MONA_Front_Lip", cols, collection)
    M.orient(lip.data, geom.away_from((1.75, 0.0, 0.45)))
    lip.data.materials.append(lib["lip_grey"])
    M.mirror_y(lip)
    M.finish(lip, thickness=0.0040, bevel=0.0010)
    return lip


def build_fascia(collection, lib):
    made = []
    del _SURF[:]
    rows = NOSE.rows(nw=52, n_lo=36, n_hi=18, z_lo=0.330)
    fascia = M.mesh_from_rows("MONA_Fascia", rows, collection)
    M.orient(fascia.data, geom.axial(1.0))
    # Populate uncut skin BVH for headlamp/trim laying before cutting intake opening
    _surf()
    _cut_openings(fascia)
    fascia.data.materials.append(lib["paint"])
    M.mirror_y(fascia)
    M.finish(fascia, thickness=M.SKIN, bevel=0.0)
    made.append(fascia)

    # Recessed intake apron backing sheet (-38 mm inside skin behind full trapezoidal mouth, tucked cleanly above z=0.295)
    ap_rows, _ = BP.cap_rows(NOSE, 0.295, 0.560, 0.0, 0.96, 20, 34, offset=-0.038)
    ap = M.mesh_from_rows("MONA_Apron", ap_rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["intake_black"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # Gloss-black perimeter tunnel wall around top and outward-angled side edges of widened mouth
    top_n = 16
    side_n = 12
    perim_yz = [(_INTAKE_TOP_Y * i / float(top_n), _INTAKE_TOP_Z) for i in range(top_n + 1)]
    perim_yz += [
        (_INTAKE_TOP_Y + (_INTAKE_BOT_Y - _INTAKE_TOP_Y) * k / float(side_n),
         _INTAKE_TOP_Z + (_INTAKE_BOT_Z - _INTAKE_TOP_Z) * k / float(side_n))
        for k in range(1, side_n + 1)
    ]
    tun_cols = []
    for (y, z) in perim_yz:
        w, v = NOSE.wv_at(y, z)
        p_out = Vector(NOSE.point(w, v))
        n = Vector(NOSE.normal(w, v))
        tun_cols.append([
            tuple(p_out + n * 0.0008),
            tuple(p_out - n * 0.034),
        ])
    tun = M.mesh_from_rows("MONA_Intake_Tunnel", tun_cols, collection)
    M.orient(tun.data, geom.away_from((2.10, 0.0, 0.41)))
    tun.data.materials.append(lib["black_gloss"])
    M.mirror_y(tun)
    M.finish(tun, thickness=0.0025, bevel=0.0005)
    made.append(tun)

    # Wide gloss-black recessed central intake shutter face + crisp gloss-black horizontal louver bar
    nz_sh = 8
    nw_sh = 18
    sh_rows = []
    for i in range(nw_sh + 1):
        u = i / float(nw_sh)
        col = []
        for k in range(nz_sh + 1):
            t = k / float(nz_sh)
            z = (_INTAKE_BOT_Z + 0.010) + ((_INTAKE_TOP_Z - 0.010) - (_INTAKE_BOT_Z + 0.010)) * t
            y = (_intake_width_at_z(z) - 0.018) * u
            col.append(_cap_pt(y, z, -0.026))
        sh_rows.append(col)
    pan = M.mesh_from_rows("MONA_Intake_Shutter", sh_rows, collection)
    M.orient(pan.data, geom.axial(1.0))
    pan.data.materials.append(lib["black_gloss"])
    M.mirror_y(pan)
    made.append(pan)

    # Crisp horizontal gloss-black center intake divider bar extending outward across widened trapezoid
    z_bar = 0.415
    y_bar = _intake_width_at_z(z_bar) - 0.012
    bar_pts = [(y_bar * i / 12.0, z_bar) for i in range(13)]
    made.append(_cap_ribbon("MONA_Intake_Bar", bar_pts, 0.0055, -0.018, lib["black_gloss"],
                            collection, thick=0.0025))

    # Integrated solid dark-grey lower lip
    made.append(_build_lower_lip(collection, lib))
    return made


# ----------------------------------------------------------------- flush T-headlamps
def _interp(pts, x):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]


def _cut_fender_lamp_hole(lib):
    """Cut the headlamp pocket out of MONA_Fender_Front cleanly after laying lamps on the uncut _surf()."""
    fender = bpy.data.objects.get("MONA_Fender_Front")
    if fender is None:
        return
    fender.modifiers.clear()
    cut_lamp = _cyl_prism("_cut_lamp_fender", PL.grow(LAMP_OUT, -2.5))
    sheet = C.sheet_bvh(fender)
    C.difference(fender, [cut_lamp], "fender_lamp_", reset_materials=True)
    C.prune_off_sheet(fender, sheet)
    if not fender.data.materials:
        fender.data.materials.append(lib["paint"])
    M.mirror_y(fender)
    M.finish(fender, thickness=M.SKIN)


def build_headlamps(collection, lib):
    made = []
    # Lay all T-headlamp layers conformal to the uncut skin surface at fine ~3.8-4.0 mm resolution
    made.append(LAY.region("MONA_Lamp_Body", LAMP_OUT, LAMP_UP, lib["lamp_frame"], collection,
                           step=4.0, thick=LAMP_T, bevel=0.0003))
    made.append(LAY.region("MONA_Lamp_Lens", PL.grow(LAMP_OUT, -2.5), GLASS_UP, lib["lamp_clear"],
                           collection, step=4.0, thick=0.0004))
    made.append(LAY.region("MONA_Lamp_Horn", LAMP_HORN, FROST_UP, lib["lamp_frost"],
                           collection, step=3.8, thick=0.0004))
    made.append(LAY.region("MONA_Lamp_Lower", LAMP_LOWER, FROST_UP, lib["lamp_frost"],
                           collection, step=3.8, thick=0.0004))

    # Fine vertical ribs inside lower triangle projector pod
    lower_deg_top = [(49.6, 0.740), (54.2, 0.740), (58.0, 0.748)]
    lower_deg_bot = [(50.6, 0.688), (52.6, 0.636), (55.2, 0.592), (57.5, 0.570)]
    for i, d_rib in enumerate((51.8, 53.3, 54.8, 56.3, 57.4)):
        zt = _interp(lower_deg_top, d_rib) - 0.006
        zb = _interp(lower_deg_bot, d_rib) + 0.006
        if zt - zb > 0.025:
            pts = _C([(d_rib, zt), (d_rib, zb)])
            made.append(LAY.ribbon("MONA_Lamp_Rib%d" % i, pts, 0.0006, RIB_UP, lib["lamp_frame"],
                                   collection, step=5.0, thick=0.0003, smooth=False))

    made.append(LAY.ribbon("MONA_Lamp_Hair", LAMP_BAR, 0.0014, GLASS_UP + 0.0005, lib["lamp_hair"],
                           collection, step=3.5, thick=0.0003))
    made.append(LAY.ribbon("MONA_Lamp_BladeTrim", LAMP_HAIR_BLADE, 0.0009, GLASS_UP + 0.00045, lib["lamp_hair"],
                           collection, step=3.5, thick=0.0003))
    made.append(LAY.ribbon("MONA_Lamp_Line", LAMP_LINE, 0.0017, LINE_UP, lib["led_white"],
                           collection, step=3.5, thick=0.0005))

    _cut_fender_lamp_hole(lib)
    return made


# -------------------------------------------------------------------- the X emblem & sensors
_LOGO_W = 0.130
_LOGO_LEFT = [
    (1837.5, 1520.0), (1851.0, 1520.0), (1912.0, 1541.5), (1914.0, 1545.0),
    (1914.0, 1554.0), (1912.0, 1557.5), (1851.0, 1579.0), (1837.5, 1579.0), (1869.0, 1549.5),
]
_LOGO_CX, _LOGO_CY = 1915.5, 1549.5


def build_emblem(collection, lib):
    """XPeng 'X' badge centered cleanly on the sloped upper nose above the pointed apex."""
    tau_logo = NOSE.TAU_APEX + 0.42 * (1.0 - NOSE.TAU_APEX)
    c = Vector(NOSE.surface_point(0.0, tau_logo))
    n = Vector(NOSE.surface_normal(0.0, tau_logo))
    right = (Vector((0.0, 1.0, 0.0)) - n * n.y).normalized()
    up = n.cross(right).normalized()
    s = _LOGO_W / (2.0 * (_LOGO_CX - 1837.5))
    left = [(x - _LOGO_CX, -(y - _LOGO_CY)) for (x, y) in _LOGO_LEFT]
    half = [(-x, y) for (x, y) in left]
    pts, tris = PL.fill(half, 5.0)
    verts = [tuple(c + right * (x * s) + up * (y * s) + n * 0.0018) for (x, y) in pts]
    ob = M.obj("MONA_Emblem_X", verts, [list(t) for t in tris], collection, lib["logo_grey"])
    M.orient(ob.data, geom.axial(1.0))
    M.solidify(ob, 0.0012)
    M.bevel(ob, 0.0003, 2, 50.0)
    M.mirror_y(ob)
    return [ob]


def _surface_disc(name, y, z, r, n_pts, proud_d, thick, mat, collection):
    w, v = NOSE.wv_at(abs(y), z)
    c = Vector(NOSE.point(w, v))
    n = Vector(NOSE.normal(w, v))
    right = (Vector((0.0, 1.0, 0.0)) - n * n.y).normalized()
    up = n.cross(right).normalized()
    ring = [
        tuple(c + n * proud_d + right * (r * math.cos(a)) + up * (r * math.sin(a)))
        for a in [2.0 * math.pi * k / n_pts for k in range(n_pts)]
    ]
    verts = ring + [tuple(c + n * proud_d)]
    faces = [[k, (k + 1) % n_pts, n_pts] for k in range(n_pts)]
    ob = M.obj(name, verts, faces, collection, mat)
    M.orient(ob.data, geom.axial(1.0))
    M.solidify(ob, thick)
    if abs(y) > 1e-4:
        M.mirror_y(ob)
    return ob


def build_sensors(collection, lib):
    """Flush front parking sensors and center camera dot on MONA_Fascia."""
    made = []
    # Two parking sensors per side: inner (y=0.31, z=0.56) and outer (y=0.69, z=0.51)
    for i, (ys, zs) in enumerate(((0.31, 0.56), (0.69, 0.51))):
        made.append(_surface_disc("MONA_Sensor_Ring%d" % i, ys, zs, 0.0092, 18,
                                  0.00045, 0.0003, lib["lamp_frame"], collection))
        made.append(_surface_disc("MONA_Sensor_Disc%d" % i, ys, zs, 0.0074, 16,
                                  0.00060, 0.0003, lib["black_gloss"], collection))
    # Center front camera dot cleanly above the front plate (z=0.692, y=0)
    made.append(_surface_disc("MONA_Camera_Dot", 0.0, 0.692, 0.0075, 16,
                              0.0008, 0.0006, lib["black_gloss"], collection))
    return made


def build_plate(collection, lib):
    """Front show plate ('Mona L05') with deep curved-bumper mounting plinth."""
    w_t, v_t = NOSE.wv_at(0.0, 0.660)
    p_top = NOSE.point(w_t, v_t)
    n_plate = Vector((0.990, 0.0, -0.140)).normalized()
    p_plate = Vector((p_top[0] - 0.003, 0.0, 0.590))
    p_mount = p_plate - n_plate * 0.002
    made = []
    made += fittings.plate("MONA_Plate_Mount_Front", tuple(p_mount), tuple(n_plate), collection, lib,
                           w=0.456, h=0.154, depth=0.072, mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("MONA_Plate_Front", tuple(p_plate), tuple(n_plate), collection, lib,
                           w=0.440, h=0.140, depth=0.004,
                           texts=[("Mona L05", 0.0, 0.042, False, True)],
                           mat="black_gloss", text_mat="machined")
    return made


def build_hood_line(collection, lib):
    """Flush recessed dark backing strip directly beneath the thin U-shaped hood panel gap line."""
    hood = bpy.data.objects.get("MONA_Hood")
    if hood is None:
        return []
    bm = bmesh.new()
    bm.from_mesh(hood.data)
    bm.normal_update()
    pts = {}
    for v in bm.verts:
        if (v.co.x > 2.02 and (v.co.y > 0.003 or v.co.x > 2.34)
                and any(e.is_boundary for e in v.link_edges)):
            key = round(v.co.y, 4)
            if key not in pts or v.co.x > pts[key][0].x:
                pts[key] = (Vector(v.co), Vector(v.normal))
    bm.free()
    keys = sorted(pts)
    if len(keys) < 6:
        return []
    P_pts = [pts[k] for k in keys]
    rows = []
    for i, (p, n) in enumerate(P_pts):
        t = (P_pts[min(len(P_pts) - 1, i + 1)][0] - P_pts[max(0, i - 1)][0]).normalized()
        side = n.cross(t).normalized()
        # Seated RECESSED (-2.0 mm) below surface so it only darkens the thin panel gap, never a raised ridge
        c = p - n * 0.0020
        rows.append([tuple(c - side * 0.0032), tuple(c + side * 0.0032)])
    ob = M.mesh_from_rows("MONA_Hood_Line", rows, collection)
    ob.data.materials.append(lib["shadow"])
    M.orient(ob.data, geom.away_from((1.8, 0.0, 0.5)))
    M.solidify(ob, 0.0006)
    M.mirror_y(ob)
    return [ob]


def build_all(collection, lib):
    PLACER.reset()
    made = []
    made += build_fascia(collection, lib)
    PLACER.reset()
    made += build_headlamps(collection, lib)
    made += build_emblem(collection, lib)
    made += build_sensors(collection, lib)
    made += build_plate(collection, lib)
    made += build_hood_line(collection, lib)
    return made
