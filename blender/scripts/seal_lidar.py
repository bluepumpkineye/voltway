"""BYD Seal roof lidar: the low black "watchtower" on the windscreen header of the 2025.02 smart-driving trims
(650智驾 / 600四驱智驾, DiPilot 300). The 智航 trims and every earlier Seal have none.

Read from Autohome's gallery for series 6394, spec 71665 (the 改款 650智驾; blender/reference/byd-seal-ev/lidar):
    front view   a trapezoid housing about 0.275 m wide at the roof, 0.15 m across its flat top, 0.055 m high, with one
                 dark trapezoid window on its front face (about 0.17 m wide at the foot, 0.14 m at the top, 0.04 m high)
                 and two small round cameras under it on the glass (inside, not modelled)
    side view    its front edge stands on the header 1.22 m behind the front axle, nearly upright (12 degrees of rake);
                 the top is level and runs back about 0.19 m, melting into the roof as that rises
    3/4 views    a rounded plan: the front corners curve back, the cheeks flare out and the tail fades into the roof

Scale: the side photograph's wheelbase (2.92 m) gives 676 px/m in the original; the front photograph's body width at
the nose gives 919 px/m, a little less at the pod's depth. Good to about 1 cm. Its place along the car is set by the
model's own windscreen edge, not by the photograph's scale: the front edge stands 2.6 cm ahead of the glass's top edge.

The pod is one gloss black shell plus a separate window panel (own material, so it can be coloured or lit later).
Everything sits on the Seal's own roof curve (seal_surface.Z_ROOF).
"""
import math

import seal_surface as S
from carkit import geom
from carkit import mesh as M

NAME = "Seal_Lidar"
X_F = 0.256                 # the front edge, 2.6 cm ahead of the windscreen's top edge (x 0.23 in the model; side photograph)
LEN = 0.192                 # to where the tail has melted into the roof
H = 0.057                   # the front edge's height above the roof
FOOT = 0.008                # the base goes this far below the glass at the centre line (no more: the glass is clear)
CAMBER = 0.28               # the roof glass falls away from the centre line by CAMBER * y^2 (measured by ray)
R_TOP = 0.014               # radius of the rounded top corners
CHEEK_IN = 0.012            # how far the cheeks are drawn in at mid height
W_B = (0.152, 0.130)        # half width at the foot, front and tail
W_T = (0.078, 0.062)        # half width of the flat top, front and tail
RAKE = 0.21                 # how far the foot of the front face stands ahead of its top, per metre of height
PLAN_CURVE = 0.035          # how far the front's corners curve back in plan
N_ST = 26
WIN = dict(z0=0.007, z1=0.049, hw0=0.085, hw1=0.069)      # above the roof at the front edge, half widths foot / top


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _fillet(p0, p1, p2, r, n):
    """Points of an arc of radius r rounding the corner p1 between p0 and p2 (a quadratic Bezier between its two tangent points)."""
    a = (p0[0] - p1[0], p0[1] - p1[1])
    b = (p2[0] - p1[0], p2[1] - p1[1])
    la, lb = math.hypot(*a), math.hypot(*b)
    a, b = (a[0] / la, a[1] / la), (b[0] / lb, b[1] / lb)
    theta = math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1])))
    d = min(r / max(math.tan(0.5 * theta), 1e-4), 0.45 * min(la, lb))
    t1 = (p1[0] + a[0] * d, p1[1] + a[1] * d)
    t2 = (p1[0] + b[0] * d, p1[1] + b[1] * d)
    out = []
    for k in range(n):
        t = k / float(n - 1)
        out.append(((1 - t) ** 2 * t1[0] + 2 * (1 - t) * t * p1[0] + t * t * t2[0],
                    (1 - t) ** 2 * t1[1] + 2 * (1 - t) * t * p1[1] + t * t * t2[1]))
    return out


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _cheek(p, q, t):
    """A point on a cheek: the cheeks sweep up concave, as in the front photograph (the outline is drawn in a little at mid height)."""
    y, z = _lerp(p, q, t)
    return (y - math.copysign(CHEEK_IN * math.sin(math.pi * t), y), z)


def _trapezoid(wb, wt, z_b, z_top):
    """The cross-section: sharp at the foot, the top corners rounded, always the same number of points (30)."""
    bl, tl, tr, br = (-wb, z_b), (-wt, z_top), (wt, z_top), (wb, z_b)
    al = _fillet(bl, tl, tr, R_TOP, 7)
    ar = _fillet(tl, tr, br, R_TOP, 7)
    ring = [bl]
    ring += [_cheek(bl, al[0], k / 5.0) for k in range(1, 5)]
    ring += al
    ring += [_lerp(al[-1], ar[0], k / 4.0) for k in range(1, 4)]
    ring += ar
    ring += [_cheek(ar[-1], br, k / 5.0) for k in range(1, 5)]
    ring += [br]
    ring += [_lerp(br, bl, k / 4.0) for k in range(1, 4)]
    return ring


def _top(u, z_roof_f):
    """Height of the flat top at station u (0 front .. 1 tail): level, then eased down into the roof."""
    z_t = z_roof_f + H
    x_r = X_F - LEN
    z_end = S.Z_ROOF(x_r) + 0.002
    return z_t - (z_t - z_end) * _smooth((u - 0.68) / 0.32)


def _station(u, z_roof_f):
    x0 = X_F - LEN * u
    z_top = _top(u, z_roof_f)
    wb = W_B[0] + (W_B[1] - W_B[0]) * u
    wt = (W_T[0] + (W_T[1] - W_T[0]) * u) * (1.0 - 0.55 * _smooth((u - 0.7) / 0.3))
    z_b = S.Z_ROOF(x0) - FOOT - CAMBER * wb * wb          # the foot's corners on the cambered glass
    pts = []
    for (y, z) in _trapezoid(wb, wt, z_b, z_top):
        x = x0 + RAKE * (z_top - z) * max(0.0, 1.0 - u / 0.2)
        x -= PLAN_CURVE * max(0.0, 1.0 - u / 0.3) * (abs(y) / W_B[0]) ** 2
        pts.append((x, y, z))
    return pts


def front_x(y, z, z_roof_f):
    """x of the front face at (y, z), for the window panel."""
    z_top = z_roof_f + H
    return X_F + RAKE * (z_top - z) - PLAN_CURVE * (abs(y) / W_B[0]) ** 2


def build_all(collection, lib):
    z_roof_f = S.Z_ROOF(X_F)
    stations = [_station(i / float(N_ST), z_roof_f) for i in range(N_ST + 1)]
    nv = len(stations[0])
    verts, faces = [], []
    for st in stations:
        verts.extend(st)
    for i in range(N_ST):
        a, b = i * nv, (i + 1) * nv
        for j in range(nv):
            j2 = (j + 1) % nv
            faces.append([a + j, a + j2, b + j2, b + j])
    faces.append(list(range(nv))[::-1])                                  # the front face
    faces.append([N_ST * nv + j for j in range(nv)])                     # the tail, inside the roof
    ob = M.obj(NAME, verts, faces, collection, lib["black_gloss"])
    cx = X_F - 0.5 * LEN
    M.orient(ob.data, geom.away_from((cx, 0.0, z_roof_f + 0.01)))

    # the window on the front face: a trapezoid, a hair proud of it, a little domed
    nz, ny = 6, 9
    rows = []
    for k in range(nz + 1):
        t = k / float(nz)
        z = z_roof_f + WIN["z0"] + t * (WIN["z1"] - WIN["z0"])
        hw = WIN["hw0"] + (WIN["hw1"] - WIN["hw0"]) * t
        row = []
        for m in range(ny + 1):
            s = -1.0 + 2.0 * m / float(ny)
            y = s * hw
            dome = 0.0035 * (1.0 - s * s) * math.sin(math.pi * (0.1 + 0.8 * t))
            row.append((front_x(y, z, z_roof_f) + 0.0012 + dome, y, z))
        rows.append(row)
    win = M.mesh_from_rows(NAME + "_Window", rows, collection)
    win.data.materials.append(lib["lidar_window"])
    M.orient(win.data, lambda c: (1.0, 0.0, 0.0))
    return [ob, win]
