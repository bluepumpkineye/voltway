"""The Denza emblem, front and rear, drawn from the car's own badges: the rear one at 6x (c1_0046, the white car, a 140 px
badge; also c1_0038) and the front one (c1_0042, c1_0034, c1_0010), and checked against the brand's artwork (a silver sphere with
an hourglass-shaped opening and a blue drop).

What the badge on the car is (~93 mm across at the tail, ~100 mm on the nose):
    a thick black ring (0.15 of the radius); inside it a silver disc that is not whole: an hourglass-shaped opening is cut from the
    disc's top edge to its lower third. Two silver "hands" (left and right) frame it. Each hand's inner edge is two straight
    runs: from the disc's top edge (u +-0.47, v 0.885) down 45 degrees to a sharp beak at the neck (u +-0.155, v 0.455), then
    out and down to the lower corner (u +-0.625, v -0.32), from where the opening's rounded foot (v -0.755) closes it. The
    hands join below the foot as a silver crescent. The opening is deep navy enamel (it photographs near black).
    (The artwork's edges are curved; the badge's are straight: the badge is what the car wears, so it is what is built.)

Three meshes share one frame (centre, normal, up): the ring (black), the disc (silver: the face with the opening cut out, plus
a small chamfer round the opening) and the enamel. `build()` returns them in that order.
"""
import math

import bmesh
import bpy
from mathutils import Vector

from carkit import mesh as M

SILVER_R = 0.85                  # the silver disc's radius as a share of the badge radius (the black ring is the rest)
H_SILVER = 0.0032                # the silver face's height above the badge's back (m)
H_ENAMEL = 0.0010                # the enamel's: 2 mm under the silver
BEVEL = 0.030                    # the chamfer round the opening, in silver-disc radii

TR = (0.470, 0.885)              # where the opening meets the disc's top edge (right)
BEAK = (0.155, 0.455)            # the hand's sharp point at the neck
CORNER = (0.625, -0.320)         # the opening's widest point, where the lower edge meets the foot
FOOT = [(0.625, -0.320), (0.588, -0.440), (0.505, -0.575), (0.365, -0.685), (0.185, -0.742), (0.000, -0.757)]


def _line(a, b, n):
    return [(a[0] + (b[0] - a[0]) * k / float(n), a[1] + (b[1] - a[1]) * k / float(n)) for k in range(n)]


def _catmull(pts, per=4):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / float(per)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(tuple(pts[-1]))
    return out


def opening():
    """The opening's outline in silver-disc units, from the top-left corner down the left hand's top edge to its beak, down to the
    corner, round the foot and up the right side to the top-right corner (counter-clockwise)."""
    right = _line(TR, BEAK, 8) + _line(BEAK, CORNER, 12) + _catmull(FOOT)       # top corner -> foot (u >= 0)
    left = [(-u, v) for (u, v) in right]
    return left + [(u, v) for (u, v) in reversed(right)][1:]


def _tri(poly):
    """Triangles (index triples) of a simple polygon given as 2-D points, by ear clipping."""
    bm = bmesh.new()
    vs = [bm.verts.new((u, v, 0.0)) for (u, v) in poly]
    f = bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=[f], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    idx = {v: i for i, v in enumerate(vs)}
    out = [tuple(idx[v] for v in face.verts) for face in bm.faces]
    bm.free()
    return out


def _frame(normal, up):
    n = Vector(normal).normalized()
    ev = (Vector(up) - n * Vector(up).dot(n)).normalized()
    eu = (-n).cross(ev).normalized()                     # the viewer's right, looking at the badge
    return eu, ev, n


def build(prefix, collection, lib, centre, normal, radius, up=(0.0, 0.0, 1.0)):
    """The emblem at `centre` facing `normal`, `radius` m to the outside of the black ring. -> [ring, disc, enamel]."""
    eu, ev, n = _frame(normal, up)
    c = Vector(centre)
    Rs = radius * SILVER_R

    def W(u, v, w):                                      # silver-disc units
        return tuple(c + eu * (u * Rs) + ev * (v * Rs) + n * w)

    def Wb(u, v, w):                                     # badge units (the ring's)
        return tuple(c + eu * (u * radius) + ev * (v * radius) + n * w)

    d_out = tuple(n)

    # ---- the ring: a rounded black band round the silver
    prof = [(SILVER_R - 0.006, 0.0), (SILVER_R - 0.006, 0.0026), (SILVER_R + 0.012, 0.0033), (0.955, 0.0033),
            (0.992, 0.0024), (1.0, 0.0011), (1.0, 0.0)]
    seg = 56
    rv, rf = [], []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        for (r, h) in prof:
            rv.append(Wb(r * ca, r * sa, h))
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(len(prof) - 1):
            rf.append([i * len(prof) + k, i * len(prof) + k + 1, j * len(prof) + k + 1, j * len(prof) + k])
    ring = M.obj(prefix + "Ring", rv, rf, collection, lib["badge_black"])
    M.orient(ring.data, lambda cc: d_out)

    # ---- the opening, the chamfer round it and the silver face
    op = opening()                                       # TL -> foot -> TR
    n_op = len(op)

    def seg_n(a, b):
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        return ty / L, -tx / L                           # right of the travel direction = away from the opening

    off = []                                             # the outline pushed into the silver: the mean of its two edges' normals
    for i in range(n_op):
        n0 = seg_n(op[i - 1], op[i]) if i > 0 else None
        n1 = seg_n(op[i], op[i + 1]) if i < n_op - 1 else None
        if n0 is None:
            nx, ny = n1
        elif n1 is None:
            nx, ny = n0
        else:
            nx, ny = n0[0] + n1[0], n0[1] + n1[1]
            L = math.hypot(nx, ny) or 1.0
            nx, ny = nx / L, ny / L
        u, v = op[i][0] + nx * BEVEL, op[i][1] + ny * BEVEL
        r = math.hypot(u, v)
        if r > 0.995:
            u, v = u * 0.995 / r, v * 0.995 / r
        off.append((u, v))
    # the disc's edge, from the offset outline's top-right end clockwise round the bottom to its top-left end
    a_r, a_l = math.atan2(off[-1][1], off[-1][0]), math.atan2(off[0][1], off[0][0])
    a1 = a_l - 2.0 * math.pi
    n_arc = 72
    arc = [(math.cos(a_r + (a1 - a_r) * k / n_arc), math.sin(a_r + (a1 - a_r) * k / n_arc)) for k in range(0, n_arc)]
    top_poly = off + arc
    verts = [W(u, v, H_SILVER) for (u, v) in top_poly]
    faces = [list(t) for t in _tri(top_poly)]
    base = len(verts)                                    # the chamfer: the offset outline (high) down to the opening's edge (low)
    verts += [W(u, v, H_SILVER) for (u, v) in off] + [W(u, v, H_ENAMEL) for (u, v) in op]
    for i in range(n_op - 1):
        faces.append([base + i, base + i + 1, base + n_op + i + 1, base + n_op + i])
    disc = M.obj(prefix + "Disc", verts, faces, collection, lib["badge_silver"], smooth=False)
    M.orient(disc.data, lambda cc: d_out)

    # ---- the enamel in the opening (its top edge is the disc's own arc between the two top corners)
    t_r, t_l = math.atan2(op[-1][1], op[-1][0]), math.atan2(op[0][1], op[0][0])
    top_arc = [(math.cos(t_r + (t_l - t_r) * k / 14.0), math.sin(t_r + (t_l - t_r) * k / 14.0)) for k in range(1, 14)]
    epoly = op + top_arc
    enamel = M.obj(prefix + "Enamel", [W(u, v, H_ENAMEL) for (u, v) in epoly], [list(t) for t in _tri(epoly)], collection,
                   lib["badge_blue"], smooth=False)
    M.orient(enamel.data, lambda cc: d_out)
    return [ring, disc, enamel]
