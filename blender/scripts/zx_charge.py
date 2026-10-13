"""Zeekr 7X charge port: the flap on the left rear quarter, the pocket behind it with its two sockets,
the light strip above them, the badge beside it and the two tethered dust caps.

Read from the Autohome photographs of the built variant (blender/reference/zeekr-7x/tech/charge,
board T3c): c12_0046 the flap shut, c12_0048 it swung out, c12_0049 and c12_0050 the pocket from in
front. The photographs show

    flap      a rounded oblong over the left rear quarter, above the wheel, hinged at its FRONT edge
              (it swings out and forward on a short arm), black inside with a warning label
    pocket    a black plastic tub with a rubber seal round its mouth, an oval light strip across the
              top, and, in one housing, two sockets side by side: DC to the front (two big power
              sleeves, a small earth sleeve and six signal sockets) and AC behind it (three power
              sleeves, two signal sockets and two empty rings), each under a small hinged cover
    badge     a white-outlined square with a Z, on the skin just behind the pocket
    caps      two black dust caps on one cord that leaves the pocket's floor, hanging below it

The outline of the flap (x -1.620..-1.358, z 0.903..1.075) was solved on the side photograph
(zx_side); the sockets' sizes and places are read off c12_0048 / c12_0049 against it (the DC cup
about 65 mm across, the AC 59 mm). Depths are ours: no photograph shows the pocket from the side.

    import zx_charge as CH
    CH.build()            # the hole in the quarter and the hull, the flap node, the port node
    CH.set_flap(105.0)    # preview the flap open (degrees)

Car axes: +x forward, +y left, z up. The flap opens by rotating about its hinge's vertical axis by a
NEGATIVE angle (its rear edge swings to +y), like the left doors. The web's nodes: Zeekr7X_ChargeFlap
(origin on the hinge) and Zeekr7X_ChargePort (the pocket, the sockets, the strip, the badge and the
caps; shown only while the flap is open: it is the opening's `frameNode`).
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector

import zx_nose as N
from carkit import cut as C
from carkit import materials as _M
from carkit import mesh as M

BODY = N.BODY

# the flap's outline in side elevation (zx_side.build_charge_door): x0, x1, z0, z1, corner radius
X0, X1, Z0, Z1, RC = -1.620, -1.358, 0.903, 1.075, 0.040
XC, ZC = 0.5 * (X0 + X1), 0.5 * (Z0 + Z1)
HA, HB = 0.5 * (X1 - X0), 0.5 * (Z1 - Z0)
GAP = 0.0012                  # half the shut line's width
OPEN_DEG = 105.0
GROUP_FLAP = ("Zeekr7X_ChargeFlap", "ZX_ChargeFlapGrp")
GROUP_PORT = ("Zeekr7X_ChargePort", "ZX_ChargePortGrp")
FLAP = "ZX_ChargeFlap"
SEG = 28
FLOOR = 0.078                 # the pocket's floor, m under the skin
PLATEAU = 0.062               # the housing the cups stand on


# --------------------------------------------------------------------- the frame of the opening
def frame():
    """The flap's centre on the skin and its axes: forward (a), up (b), outward (c)."""
    p, n = BODY.side_point(XC, ZC)
    p, n = Vector(p), Vector(n).normalized()
    ef = (Vector((1.0, 0.0, 0.0)) - n * n.x).normalized()
    eu = ef.cross(n).normalized()
    return p, ef, eu, n


_F = None


def P(a, b, c=0.0):
    """A point in the opening's frame: a forward, b up, c outward from the skin at its centre."""
    global _F
    if _F is None:
        _F = frame()
    p, ef, eu, n = _F
    return p + ef * a + eu * b + n * c


def _loop(shrink, per=7):
    """The mouth as a loop of (a, b), `shrink` smaller all round, counter-clockwise."""
    ha, hb = HA - shrink, HB - shrink
    r = max(RC - shrink, 0.004)
    pts = []
    for cx, cy, a0 in ((ha - r, hb - r, 0.0), (-ha + r, hb - r, 0.5 * math.pi),
                       (-ha + r, -hb + r, math.pi), (ha - r, -hb + r, 1.5 * math.pi)):
        for k in range(per):
            t = a0 + 0.5 * math.pi * k / float(per - 1)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def _skin(a, b, c=0.0):
    """The skin at the opening's (a, b), moved `c` along the centre normal (the walls follow the skin)."""
    q = P(a, b, 0.0)
    p, _ = BODY.side_point(q.x, q.z)
    return Vector(p) + _F[3] * c


# ------------------------------------------------------------------------------ materials
def _mat(name, **kw):
    m = bpy.data.materials.get(name)
    if m is None:
        m, _nt, b = _M.mat(name)
        _M.set_inputs(b, **kw)
    return m


def materials():
    plastic = bpy.data.materials.get("M_Cladding") or _mat("M_Cladding", base=(0.020, 0.021, 0.024), roughness=0.52)
    return dict(
        plastic=plastic,
        gloss=bpy.data.materials.get("M_Black_Gloss") or _mat("M_Black_Gloss", base=(0.01, 0.01, 0.012), roughness=0.1),
        satin=bpy.data.materials.get("M_Black_Satin") or plastic,
        brass=_mat("M_Charge_Brass", base=(0.50, 0.33, 0.10), metallic=0.9, roughness=0.34),
        silver=_mat("M_Charge_Silver", base=(0.62, 0.63, 0.65), metallic=0.9, roughness=0.28),
        led=_mat("M_Charge_LED", base=(0.80, 0.78, 0.92), roughness=0.3, emission=(0.80, 0.74, 1.0),
                 emission_strength=5.0),
        white=_mat("M_Charge_White", base=(0.70, 0.70, 0.69), roughness=0.4),
        yellow=_mat("M_Charge_Yellow", base=(0.80, 0.55, 0.02), roughness=0.4),
        paint=bpy.data.materials.get("M_Paint_ZX_Blue"),
    )


# ------------------------------------------------------------------------------ mesh builder
class Mesher:
    """Faces with the direction each must point: the opening's frame is left-handed, so winding is
    settled afterwards by comparing a face's normal with the direction it was given."""

    def __init__(self):
        self.v, self.f, self.want, self.mi = [], [], [], []

    def vert(self, p):
        self.v.append(tuple(p))
        return len(self.v) - 1

    def face(self, ids, want, mi=0):
        self.f.append(list(ids))
        self.want.append(Vector(want))
        self.mi.append(mi)

    def ring(self, pts):
        return [self.vert(p) for p in pts]

    def bridge(self, ra, rb, want, closed=True, mi=0):
        """Quads between two equal rings of vertex ids; `want(i)` the direction of quad i."""
        n = len(ra)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            self.face([ra[i], ra[j], rb[j], rb[i]], want(i), mi)

    def fan(self, ring, want, mi=0):
        c = self.vert(sum((Vector(self.v[i]) for i in ring), Vector()) / len(ring))
        for i in range(len(ring)):
            self.face([c, ring[i], ring[(i + 1) % len(ring)]], want, mi)

    def box(self, a0, a1, b0, b1, c0, c1, skip=()):
        """An axis-aligned box in the opening's frame."""
        _, ef, eu, n = _F
        v = {}
        for ia, a in enumerate((a0, a1)):
            for ib, b in enumerate((b0, b1)):
                for ic, c in enumerate((c0, c1)):
                    v[(ia, ib, ic)] = self.vert(P(a, b, c))
        sides = (
            ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1), -ef, 'a0'),
            ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1), ef, 'a1'),
            ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), -eu, 'b0'),
            ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1), eu, 'b1'),
            ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1), n, 'c1'),
            ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), -n, 'c0'),
        )
        for k0, k1, k2, k3, want, tag in sides:
            if tag in skip:
                continue
            self.face([v[k0], v[k1], v[k2], v[k3]], want)

    def build(self, name, mat, col, mats=None):
        faces = []
        for ids, want in zip(self.f, self.want):
            pts = [Vector(self.v[i]) for i in ids]
            nrm = Vector()
            for k in range(len(pts)):
                nrm += pts[k].cross(pts[(k + 1) % len(pts)])        # Newell's normal (twice the area)
            faces.append(ids if nrm.dot(want) >= 0.0 else ids[::-1])
        me = bpy.data.meshes.new(name + "_mesh")
        me.from_pydata(self.v, [], faces)
        me.update()
        for poly, mi in zip(me.polygons, self.mi):
            poly.use_smooth = False
            poly.material_index = mi
        for m_ in (mats if mats is not None else [mat]):
            if m_ is not None:
                me.materials.append(m_)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        return ob


def _tube(mesh, a, b, r_out, r_in, c_top, c_floor, floor_mesh=None, n=SEG, c_base=None):
    """A hollow cup standing on the opening's frame: outer wall, rim, inner wall and floor. The
    floor can go to another mesh (a brass contact in a black sleeve)."""
    _, ef, eu, nn = _F

    def pts(r, c):
        return [P(a + r * math.cos(2 * math.pi * i / n), b + r * math.sin(2 * math.pi * i / n), c) for i in range(n)]

    def radial(i):
        t = 2 * math.pi * (i + 0.5) / n
        return ef * math.cos(t) + eu * math.sin(t)

    bottom = mesh.ring(pts(r_out, c_floor - 0.001 if c_base is None else c_base))
    top_o = mesh.ring(pts(r_out, c_top))
    top_i = mesh.ring(pts(r_in, c_top))
    deep_i = mesh.ring(pts(r_in, c_floor))
    mesh.bridge(bottom, top_o, radial)
    mesh.bridge(top_o, top_i, lambda i: nn)
    mesh.bridge(top_i, deep_i, lambda i: -radial(i))
    if floor_mesh is None:
        mesh.fan(deep_i, nn)
    else:
        floor_mesh.fan(floor_mesh.ring(pts(r_in, c_floor)), nn)


# ---------------------------------------------------------------------------- the sockets
# Photograph c12_0049, in units of the cup's radius from its centre, photograph axes (right, down);
# the photograph looks at the car's left side, so right is REARWARD: a = -x * R, b = -y * R.
DC_CUP = dict(a=0.030, b=-0.004, R=0.0325, depth=0.024)
AC_CUP = dict(a=-0.044, b=-0.012, R=0.0295, depth=0.022)
# (x, y, radius) in units of R
DC_BIG = ((-0.29, -0.19, 0.32), (0.65, 0.00, 0.32))
DC_EARTH = ((0.10, 0.50, 0.19),)
DC_SIGNAL = ((0.02, -0.84, 0.12), (0.32, -0.81, 0.12), (0.68, -0.74, 0.12), (0.32, -0.45, 0.12),
             (-0.16, 0.37, 0.12), (0.63, 0.55, 0.12))
AC_POWER = ((-0.56, -0.29, 0.22), (0.03, -0.20, 0.22), (0.62, -0.09, 0.22))
AC_SIGNAL = ((-0.19, -0.60, 0.15), (0.35, -0.49, 0.15))
AC_EMPTY = ((-0.33, 0.33, 0.24), (0.27, 0.44, 0.24))


def _socket(m, cup, col_mats):
    """One cup and everything in it. `m` is the dict of meshers by material."""
    R, a0, b0 = cup["R"], cup["a"], cup["b"]
    c_mouth = -0.020
    _tube(m["plastic"], a0, b0, R, R * 0.90, c_mouth, c_mouth - cup["depth"], c_base=-PLATEAU)
    return R, a0, b0, c_mouth - cup["depth"]


def _contacts(m, cup, R, floor_c, big=(), small=(), rings=()):
    a0, b0 = cup["a"], cup["b"]
    for items, r_scale, bore, brass in ((big, 1.0, 0.55, True), (small, 1.0, 0.0, False)):
        for (x, y, r) in items:
            a, b = a0 - x * R, b0 - y * R
            rr = r * R
            if brass:
                _tube(m["satin"], a, b, rr, rr * 0.62, floor_c + 0.012, floor_c, floor_mesh=m["brass"])
            else:
                _tube(m["gloss"], a, b, rr, rr * 0.45, floor_c + 0.006, floor_c, floor_mesh=m["brass"], n=16)
    for (x, y, r) in rings:
        a, b = a0 - x * R, b0 - y * R
        rr = r * R
        _tube(m["satin"], a, b, rr, rr * 0.72, floor_c + 0.010, floor_c, n=20)


def build_port(col):
    """The pocket, the sockets, the strip, the badge and the caps, as one set of meshes in `col`."""
    mats = materials()
    m = {k: Mesher() for k in ("plastic", "gloss", "satin", "brass", "silver", "led", "white", "yellow")}
    _, ef, eu, n = _F

    # --- the pocket: a rubber seal round the mouth, the walls going down, the floor
    seal_top = [(a, b) for a, b in _loop(0.0020)]
    seal_in = _loop(0.0120)
    wall_in = _loop(0.0230)
    r_seal_top = m["gloss"].ring([_skin(a, b, -0.0006) for a, b in seal_top])
    r_seal_in = m["gloss"].ring([_skin(a, b, -0.0050) for a, b in seal_in])
    r_wall = m["plastic"].ring([_skin(a, b, -FLOOR) for a, b in wall_in])
    r_wall_top = m["plastic"].ring([_skin(a, b, -0.0050) for a, b in seal_in])
    k = len(seal_top)
    centre = P(0, 0, -0.03)

    def into(p_idx, mesher):
        return lambda i: centre - Vector(mesher.v[p_idx[i]])

    m["gloss"].bridge(r_seal_top, r_seal_in, lambda i: n)             # the seal's lip, facing out
    m["plastic"].bridge(r_wall_top, r_wall, into(r_wall_top, m["plastic"]))      # the walls, facing in
    m["plastic"].fan(r_wall, n)                                          # the floor

    # --- the housing: a low plateau the cups stand on
    plate = _loop(0.0230 + 0.020)
    plate = [(a * 0.96, b * 0.78 - 0.006) for a, b in plate]
    lo = m["satin"].ring([P(a, b, -FLOOR) for a, b in plate])
    hi = m["satin"].ring([P(a, b, -PLATEAU) for a, b in plate])
    m["satin"].bridge(lo, hi, lambda i: Vector(m["satin"].v[hi[i]]) - P(0, -0.006, -PLATEAU))
    m["satin"].fan(hi, n)

    # --- the two cups, each under its small hinged cover
    for cup, big, small, rings, earth in ((DC_CUP, DC_BIG, DC_SIGNAL, (), DC_EARTH),
                                          (AC_CUP, AC_POWER, AC_SIGNAL, AC_EMPTY, ())):
        R, a0, b0, floor_c = _socket(m, cup, mats)
        _contacts(m, cup, R, floor_c, big=big + earth, small=small, rings=rings)
        # the cover: a low wedge over the cup's upper edge, with a silver hinge line
        w = R * 0.86
        m["satin"].box(a0 - w, a0 + w, b0 + R * 0.92, b0 + R * 1.62, -PLATEAU, -0.026)
        m["silver"].box(a0 - R * 0.42, a0 + R * 0.42, b0 + R * 0.93, b0 + R * 1.02, -0.0262, -0.0236)

    # --- the light strip, across the top of the pocket (lit: it is lit in the photographs)
    m["led"].box(-0.024, 0.040, 0.0585, 0.0655, -0.0200, -0.0140)

    # --- the anchor of the caps' cord, at the pocket's lower edge
    _tube(m["gloss"], -0.006, -0.064, 0.0085, 0.0, -0.058, -FLOOR, n=18)

    # --- the badge, on the skin behind the opening: a white-outlined square with a Z
    badge(m)

    objs = []
    for key, mesher in m.items():
        if mesher.f:
            objs.append(mesher.build("ZX_ChargePort_" + key, mats[key], col))
    objs += build_caps(col, mats)
    return objs


def badge(m):
    """A 24 mm square, white outline, black field, a Z, on the skin 30 mm behind the opening."""
    a0, b0, s = -(HA + 0.0290), -0.004, 0.012
    pts = lambda a, b: _skin(a0 + a, b0 + b, 0.0005)
    out = [(-s, -s), (s, -s), (s, s), (-s, s)]
    inn = [(-s + 0.0020, -s + 0.0020), (s - 0.0020, -s + 0.0020), (s - 0.0020, s - 0.0020), (-s + 0.0020, s - 0.0020)]
    _, ef, eu, n = _F
    ro = m["white"].ring([pts(a, b) for a, b in out])
    ri = m["white"].ring([pts(a, b) for a, b in inn])
    m["white"].bridge(ro, ri, lambda i: n)
    fi = m["gloss"].ring([pts(a, b) for a, b in inn])
    m["gloss"].fan(fi, n)
    # the Z: three bars (top, diagonal, bottom), 1.6 mm wide
    w = 0.0016
    z = [
        [(-0.0065, 0.0065), (0.0065, 0.0065), (0.0065, 0.0065 - w), (-0.0065, 0.0065 - w)],
        [(0.0065, 0.0065 - w), (0.0065 - w * 1.4, 0.0065 - w), (-0.0065, -0.0065 + w), (-0.0065 + w * 1.4, -0.0065 + w)],
        [(-0.0065, -0.0065), (0.0065, -0.0065), (0.0065, -0.0065 + w), (-0.0065, -0.0065 + w)],
    ]
    for quad in z:
        ids = m["white"].ring([_skin(a0 + a, b0 + b, 0.0009) for a, b in quad])
        m["white"].face(ids, n)


CAPS = ((0.040, -0.128, 0.0290), (-0.034, -0.136, 0.0260))      # where each hangs (a, b) and its radius


def build_caps(col, mats):
    """Two dust caps on one cord, hanging below the pocket (c12_0048): each a black cup with its open
    face out, its back against the body, hung on the cord's two ends."""
    m = {k: Mesher() for k in ("plastic", "gloss")}
    _, ef, eu, n = _F
    for (a, b, R) in CAPS:
        o = _skin(a, b, 0.0)

        def pts(r, c, o=o):
            return [o + ef * (r * math.cos(2 * math.pi * i / 24)) + eu * (r * math.sin(2 * math.pi * i / 24)) + n * c
                    for i in range(24)]

        def radial(i):
            t = 2 * math.pi * (i + 0.5) / 24
            return ef * math.cos(t) + eu * math.sin(t)

        back = m["plastic"].ring(pts(R, 0.003))
        lip_o = m["plastic"].ring(pts(R, 0.028))
        lip_i = m["plastic"].ring(pts(R * 0.80, 0.028))
        deep = m["plastic"].ring(pts(R * 0.80, 0.012))
        m["plastic"].bridge(back, lip_o, radial)
        m["plastic"].bridge(lip_o, lip_i, lambda i: n)
        m["plastic"].bridge(lip_i, deep, lambda i: -radial(i))
        m["plastic"].fan(deep, n)
        m["plastic"].fan(back, -n)
        # the cord's eye on the cap's side
    # the cord: from the anchor on the pocket's floor over its lower lip, then down to each cap
    for (a, b, R) in CAPS:
        o = _skin(a, b, 0.0)
        ctrl = [P(-0.006, -0.064, -0.056), P(-0.006, -0.074, -0.024), P(-0.006, -0.090, 0.006),
                P(-0.006 + (a + 0.006) * 0.35, -0.100 + (b + 0.100) * 0.30, 0.012),
                P(a, b + R * 0.9, 0.011) + (o - P(a, b, 0.0)), o + eu * R * 0.55 + n * 0.012]
        _sweep(m["gloss"], _smooth(ctrl, 6), 0.0016)
    objs = []
    for key, mesher in m.items():
        if mesher.f:
            objs.append(mesher.build("ZX_ChargeCaps_" + key, mats[key], col))
    return objs


def _smooth(ctrl, per):
    """A Catmull-Rom curve through the control points."""
    out = []
    m = len(ctrl)
    for i in range(m - 1):
        p0, p1, p2, p3 = ctrl[max(0, i - 1)], ctrl[i], ctrl[i + 1], ctrl[min(m - 1, i + 2)]
        for k in range(per):
            t = k / float(per)
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(ctrl[-1])
    return out


def _sweep(mesher, pts, r, n=8):
    """A thin round tube along a polyline."""
    rings, centres = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-4:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        w = t.cross(u).normalized()
        rings.append(mesher.ring([p + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * r
                                  for k in range(n)]))
        centres.append(p)
    for j in range(len(rings) - 1):
        a, b, c = rings[j], rings[j + 1], centres[j]
        mesher.bridge(a, b, lambda i, a=a, c=c: Vector(mesher.v[a[i]]) - c)


# ---------------------------------------------------------------- the hole, the flap, the hull
def _outline(grow):
    """The flap's outline in side elevation, `grow` larger (negative: smaller), as (x, z) points."""
    from carkit import geom
    return [(x, z) for x, z in geom.rounded_loop(X0 - grow, X1 + grow, Z0 - grow, Z1 + grow, max(RC + grow, 0.004), 8,
                                                 closed=False)]


def _wall_faces_black(ob, black):
    """The faces a cut left standing on the rim (they look across the opening) take the black."""
    me = ob.data
    if black.name not in [m.name for m in me.materials if m]:
        me.materials.append(black)
    idx = [m.name for m in me.materials if m].index(black.name)
    _, ef, eu, n = _F
    lo = Vector((X0 - 0.008, 0.0, Z0 - 0.008))
    hi = Vector((X1 + 0.008, 0.0, Z1 + 0.008))
    for poly in me.polygons:
        c = poly.center
        if lo.x <= c.x <= hi.x and lo.z <= c.z <= hi.z and c.y > 0.5:
            # a wall looks across the skin: judged against the skin's own normal here (the panel bends
            # at its rear edge, where the centre normal of the opening is no guide)
            _, sn = BODY.side_point(c.x, c.z)
            if abs(poly.normal.dot(Vector(sn))) < 0.5:
                poly.material_index = idx


def _boolean(ob, op, cutter):
    """One exact, hole-tolerant boolean on `ob`, applied (the sheets are open surfaces)."""
    b = ob.modifiers.new("charge_" + op.lower(), 'BOOLEAN')
    b.operation = op
    b.solver = 'EXACT'
    try:
        b.use_hole_tolerant = True
    except Exception:
        pass
    b.object = cutter
    M.apply_modifiers(ob)


def _thicken(ob, like, plain=False):
    """Give a sheet the skin `like` has: every modifier of its stack after the Mirror (the flap goes
    without the weighted normals: its big flat liner shaded across fan triangles came out banded)."""
    for m in list(like.modifiers)[1:]:
        if plain and m.type == 'WEIGHTED_NORMAL':
            continue
        n = ob.modifiers.new(m.name, m.type)
        for p in m.bl_rna.properties:
            if p.is_readonly or p.identifier in ("name", "type", "rna_type"):
                continue
            try:
                setattr(n, p.identifier, getattr(m, p.identifier))
            except (AttributeError, TypeError):
                pass
    M.apply_modifiers(ob)


THICK = 0.0030                # the skin's thickness
RINGS = 9


def build_flap(mats, col):
    """The flap: a skin on the flank's own surface (BODY.side_point, the surface the quarter panel
    is built on), a black liner under it, a rim of the skin's thickness. Built from the surface and
    not cut out of the quarter's mesh: there the quarter's grid pinches into a band of slivers a few
    centimetres inside the flap's rear edge (the loft's tail seam), and the exact boolean left a crack
    along it. Origin on the hinge: the front edge, mid height."""
    outline = _outline(-GAP)
    cx, cz = XC, ZC
    hp, _ = BODY.side_point(X1 - GAP, ZC)
    hinge = Vector(hp)
    m = Mesher()
    sk, rings_o, rings_i = [], [], []
    for k in range(RINGS + 1):
        f = 1.0 - k / float(RINGS)
        ro, ri = [], []
        for (x, z) in outline:
            xs, zs = cx + (x - cx) * f, cz + (z - cz) * f
            p, nrm = BODY.side_point(xs, zs)
            p, nrm = Vector(p), Vector(nrm).normalized()
            ro.append(m.vert(p - hinge))
            ri.append(m.vert(p - nrm * THICK - hinge))
        rings_o.append(ro)
        rings_i.append(ri)
    n_seg = len(outline)
    _, nn = BODY.side_point(cx, cz)
    nn = Vector(nn)
    for k in range(RINGS - 1):
        m.bridge(rings_o[k], rings_o[k + 1], lambda i: nn, mi=0)
        m.bridge(rings_i[k], rings_i[k + 1], lambda i: -nn, mi=1)
    m.fan(rings_o[RINGS - 1], nn, mi=0)
    m.fan(rings_i[RINGS - 1], -nn, mi=1)
    # the rim, a hair of black round the edge
    cen = Vector(BODY.side_point(cx, cz)[0]) - hinge
    m.bridge(rings_o[0], rings_i[0], lambda i: Vector(m.v[rings_o[0][i]]) - cen, mi=1)
    ob = m.build(FLAP, None, col, mats=[mats["paint"], mats["plastic"]])
    ob.location = hinge
    # the liner and the rim are flat shaded
    for poly in ob.data.polygons:
        poly.use_smooth = poly.material_index == 0
    return ob


def build_flap_and_hole():
    """Cut the flap's outline out of the rear quarter (a 2.4 mm shut line) and build the flap that
    fills it, origin on the hinge. The cut is made on the mirrored SHEET, before it is given its
    thickness (an exact boolean on the thin solid with its bevels came out wrong: half the panel
    went). Once (ZX_ChargeFlap marks it done)."""
    if bpy.data.objects.get(FLAP) is not None:
        return None
    mats = materials()
    quarter = bpy.data.objects["ZX_Quarter"]
    if not quarter.modifiers or quarter.modifiers[0].type != 'MIRROR':
        raise RuntimeError("ZX_Quarter's stack does not start with its mirror: %s" % [m.type for m in quarter.modifiers])
    sheet = quarter.copy()
    sheet.data = quarter.data.copy()
    bpy.context.scene.collection.objects.link(sheet)
    while len(sheet.modifiers) > 1:
        sheet.modifiers.remove(sheet.modifiers[-1])
    M.apply_modifiers(sheet)                    # the mirrored sheet, both sides
    hole = C.prism_y("_flaphole", _outline(GAP), 0.70, 1.00)
    _boolean(sheet, 'DIFFERENCE', hole)
    bpy.data.objects.remove(hole, do_unlink=True)
    print("charge: quarter sheet", len(sheet.data.polygons), "faces")
    _thicken(sheet, quarter)
    # the quarter takes the cut sheet's mesh (its own stack is spent: the thickness is in the mesh)
    old = quarter.data
    quarter.modifiers.clear()
    quarter.data = sheet.data
    bpy.data.objects.remove(sheet, do_unlink=True)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    _wall_faces_black(quarter, mats["gloss"])
    col = bpy.data.collections.get(GROUP_FLAP[1]) or bpy.data.collections.new(GROUP_FLAP[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    flap = build_flap(mats, col)
    _label(flap, mats, flap.location.copy())
    # the old painted outline (zx_side) is replaced by the real gap
    old = bpy.data.objects.get("ZX_Charge_Line")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    # and out of the hull behind it, and the lamp bar's tip, so the pocket shows
    open_hull()
    trim_neighbours()
    return flap


def _label(flap, mats, hinge):
    """The warning label on the flap's inside (c12_0048): a white strip with a yellow triangle."""
    _, ef, eu, n = _F
    m = {"white": Mesher(), "yellow": Mesher()}
    # on the inner skin, 3.2 mm under the outer one, facing inward
    inward = -n
    a0, b0 = 0.040, 0.0

    def Q(da, db):
        return _skin(a0 + da, b0 + db, -0.0034) - hinge

    r = m["white"].ring([Q(-0.011, -0.040), Q(0.011, -0.040), Q(0.011, 0.040), Q(-0.011, 0.040)])
    m["white"].face(r, inward)
    t = m["yellow"].ring([Q(-0.0075, 0.018), Q(0.0075, 0.018), Q(0.0, 0.0345)])
    m["yellow"].face(t, inward)
    # lift each label a hair off the liner
    for key, mesher in m.items():
        mesher.v = [tuple(Vector(v) + inward * 0.0003) for v in mesher.v]
        ob = mesher.build("ZX_ChargeFlap_Label_" + key, mats[key], bpy.context.scene.collection)
        ob.location = hinge
        # merge into the flap's mesh by parenting for now: joined at export
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col = bpy.data.collections.get(GROUP_FLAP[1]) or bpy.data.collections.new(GROUP_FLAP[1])
        if col.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(col)
        col.objects.link(ob)


def trim_neighbours():
    """The tail lamp's bar sweeps round the corner and its tip reaches into the opening: the
    opening is cut out of it too (the same outline, a little larger)."""
    lo = Vector((X0 - 0.01, 0.45, Z0 - 0.01))
    hi = Vector((X1 + 0.01, 1.1, Z1 + 0.01))
    for name in ("ZX_Lightbar_Edge", "ZX_Lightbar_Lens", "ZX_Lightbar_SealLow", "ZX_Lightbar_SealUp"):
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        M.apply_modifiers(ob)
        if not any(lo.x <= v.co.x <= hi.x and lo.y <= v.co.y <= hi.y and lo.z <= v.co.z <= hi.z for v in ob.data.vertices):
            continue
        cut = C.prism_y("_lampcut", _outline(0.003), 0.40, 1.10)
        before, after = C.difference(ob, [cut], "charge_")
        print("charge: %s cut %d -> %d faces" % (name, before, after))


def open_hull():
    """The hull behind the flap: the same outline cut out of the shadow shells, so the pocket is not
    walled by them."""
    for name in ("ZX_Shell_Shadow", "ZX_Shell_Shadow_F", "ZX_Shell_Shadow_R"):
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        M.apply_modifiers(ob)
        sheet = C.sheet_bvh(ob)
        cut = C.prism_y("_hullcut_charge", _outline(0.004), 0.40, 1.10)
        C.difference(ob, [cut], "charge_")
        C.prune_off_sheet(ob, sheet)


# ------------------------------------------------------------------------ the whole thing
def build():
    """Everything: once per build (ZX_ChargeFlap marks it done)."""
    if bpy.data.objects.get(FLAP) is not None:
        return
    frame_ready()
    col = bpy.data.collections.get(GROUP_PORT[1]) or bpy.data.collections.new(GROUP_PORT[1])
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    build_flap_and_hole()
    build_port(col)


def frame_ready():
    global _F
    _F = frame()


def groups():
    return [GROUP_FLAP, GROUP_PORT]


def set_flap(deg):
    """Swing the flap `deg` open about its hinge's vertical axis (the left side: a negative turn)."""
    rot = Matrix.Rotation(math.radians(-deg), 4, 'Z')
    for ob in bpy.data.collections[GROUP_FLAP[1]].objects:
        ob.matrix_world = Matrix.Translation(bpy.data.objects[FLAP].location.copy()) @ rot
