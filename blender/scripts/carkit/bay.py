"""Geometry helpers for the bays under a bonnet: closed plan outlines (x, y)
and the pads, rings and skins built on them. Shared by rx_bays and su7_bays.

Car axes +x forward, +y left, z up. An outline is a closed polygon of (x, y).
"""
import math

import bpy
import bmesh


def smooth(pts, per):
    """Catmull-Rom through pts, `per` samples a span."""
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t +
                                    (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3)
                             for j in range(2)))
    out.append(pts[-1])
    return out


def inset_poly(poly, d):
    """Offset a closed (x, y) polygon inward by d along its vertex normals."""
    n = len(poly)
    area = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0       # ccw => inward is to the left
    out = []
    for i in range(n):
        ax, ay = poly[i - 1]
        bx, by = poly[(i + 1) % n]
        tx, ty = bx - ax, by - ay
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L * sgn, tx / L * sgn
        out.append((poly[i][0] + nx * d, poly[i][1] + ny * d))
    return out


def is_cw(poly):
    return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1]
               for i in range(len(poly))) < 0


def radial(poly, c, n=200):
    """A star-shaped closed outline resampled at n equal angles about c: the
    same angles on two outlines pair their points with no twist."""
    out = []
    m = len(poly)
    for k in range(n):
        a = 2.0 * math.pi * k / n
        dx, dy = math.cos(a), math.sin(a)
        best = None
        for i in range(m):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % m]
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((x0 - c[0]) * ey - (y0 - c[1]) * ex) / den
            u = ((x0 - c[0]) * dy - (y0 - c[1]) * dx) / den
            if t > 0.0 and -1e-9 <= u <= 1.0 + 1e-9 and (best is None or t < best):
                best = t
        out.append((c[0] + dx * best, c[1] + dy * best))
    return out


def bridge(bm, a, b):
    """Skin between two closed 3D loops (lists of Vectors)."""
    va = [bm.verts.new(p) for p in a]
    vb = [bm.verts.new(p) for p in b]
    ea = [bm.edges.new((va[i - 1], va[i])) for i in range(len(va))]
    eb = [bm.edges.new((vb[i - 1], vb[i])) for i in range(len(vb))]
    bmesh.ops.bridge_loops(bm, edges=ea + eb, use_pairs=False, use_cyclic=False)


def finish(bm, name, col, mat, smooth_shade=True, recalc=True):
    """The bmesh as an object in `col`: normals outward (unless the faces were
    wound the right way round already: recalc=False), one material."""
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth_shade
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def prism(name, outline, z_of, th, col, mat, lift=0.0):
    """A thin pad: `outline` (x, y) on a surface, `th` thick, its top at
    z_of(x, y) + lift."""
    bm = bmesh.new()
    top = [bm.verts.new((x, y, z_of(x, y) + lift)) for (x, y) in outline]
    bot = [bm.verts.new((x, y, z_of(x, y) + lift - th)) for (x, y) in outline]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(len(top)):
        j = (i + 1) % len(top)
        bm.faces.new((top[i], top[j], bot[j], bot[i]))
    return finish(bm, name, col, mat, smooth_shade=False)


def rrect(cx, cy, hx, hy, r, n=6):
    """A rounded rectangle about (cx, cy), half sizes hx, hy, corner radius r."""
    r = min(r, hx, hy)
    pts = []
    for (cxx, cyy, a0) in ((cx + hx - r, cy + hy - r, 0.0), (cx - hx + r, cy + hy - r, 90.0),
                           (cx - hx + r, cy - hy + r, 180.0), (cx + hx - r, cy - hy + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cxx + r * math.cos(a), cyy + r * math.sin(a)))
    return pts


def disc(name, cx, cy, r, z_of, h, col, mat, n=16, lift=None):
    """A round stud of height h on a surface (default: standing a little proud)."""
    return prism(name, [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
                        for k in range(n)], z_of, h, col, mat,
                 lift=h * 0.55 if lift is None else lift)


def inside(poly, x, y):
    """Point in polygon."""
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c
