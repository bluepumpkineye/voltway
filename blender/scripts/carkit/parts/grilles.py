"""Grille and intake fills: meshes of thin bars that follow a surface.

Every pattern is laid out in the front (or rear) elevation (y, z) inside a box
and pushed onto a surface by `x_of(y, z)` - usually the cap, or the recessed
mouth behind it (fascia.recessed_x), minus a set-back. Bars have a little
depth so they catch light on their edges.

    diamond     two families of bars at +/- atan(d_v / d_h) (SU7 Ultra)
    hexagon     honeycomb
    slats       horizontal (or angled) louvres
    dots        a field of round studs - closed "grilles" with a pattern

Put intake fills in a satin black, never gloss, and never invent one: the
SU7's first build had a slatted grille the real car does not have, and it was
the single most criticised feature.
"""
import math

from .. import mesh as M


def _bar(verts, faces, a, b, half_w, depth):
    """A thin bar from a to b (points (x, y, z)), width across the elevation."""
    (xa, ya, za), (xb, yb, zb) = a, b
    dy, dz = yb - ya, zb - za
    L = math.hypot(dy, dz) or 1.0
    ny, nz = -dz / L * half_w, dy / L * half_w
    base = len(verts)
    for (xx, yy, zz) in ((xa, ya, za), (xb, yb, zb)):
        for dx in (0.0, -depth):
            verts.append((xx + dx, yy + ny, zz + nz))
            verts.append((xx + dx, yy - ny, zz - nz))
    b0 = base
    faces += [[b0, b0 + 1, b0 + 5, b0 + 4], [b0 + 2, b0 + 6, b0 + 7, b0 + 3],
              [b0, b0 + 4, b0 + 6, b0 + 2], [b0 + 1, b0 + 3, b0 + 7, b0 + 5]]


def _clip(y0, y1, z0, z1, p, q):
    """Clip segment p-q (in (y, z)) to the box (Liang-Barsky); None if outside."""
    (ya, za), (yb, zb) = p, q
    dy, dz = yb - ya, zb - za
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dy, ya - y0), (dy, y1 - ya), (-dz, za - z0), (dz, z1 - za)):
        if abs(pp) < 1e-12:
            if qq < 0:
                return None
            continue
        r = qq / pp
        if pp < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    return (ya + dy * t0, za + dz * t0), (ya + dy * t1, za + dz * t1)


def diamond(name, y0, y1, z0, z1, x_of, set_back, collection, mat,
            d_h=0.028, d_v=0.018, wire=0.0032, depth=0.006):
    """Rhombic mesh: two families of thin bars at +/- atan(d_v / d_h)."""
    m = d_v / d_h
    verts, faces = [], []
    for sgn in (1.0, -1.0):
        c_lo = z0 - (m * y1 if sgn > 0 else -m * y0)
        c_hi = z1 - (m * y0 if sgn > 0 else -m * y1)
        k = math.floor(c_lo / d_v)
        while k * d_v <= c_hi:
            c = k * d_v
            k += 1
            # clip the line z = sgn*m*y + c to the box
            pts = []
            for yy in (y0, y1):
                zz = sgn * m * yy + c
                if z0 <= zz <= z1:
                    pts.append((yy, zz))
            for zz in (z0, z1):
                yy = (zz - c) / (sgn * m)
                if y0 <= yy <= y1:
                    pts.append((yy, zz))
            if len(pts) < 2:
                continue
            pts.sort()
            (ya, za), (yb, zb) = pts[0], pts[-1]
            if math.hypot(yb - ya, zb - za) < 0.004:
                continue
            xa = x_of(ya, za) - set_back
            xb = x_of(yb, zb) - set_back
            base = len(verts)
            nz = wire * 0.5 / math.sqrt(1 + m * m)
            ny = -sgn * m * nz
            for (xx, yy, zz) in ((xa, ya, za), (xb, yb, zb)):
                for dx in (0.0, -depth):
                    verts.append((xx + dx, yy + ny, zz + nz))
                    verts.append((xx + dx, yy - ny, zz - nz))
            b = base
            faces += [[b, b + 1, b + 5, b + 4], [b + 2, b + 6, b + 7, b + 3],
                      [b, b + 4, b + 6, b + 2], [b + 1, b + 3, b + 7, b + 5]]
    return M.obj(name, verts, faces, collection, mat, smooth=False)


def _segments_to_mesh(name, segs, x_of, set_back, collection, mat, wire, depth,
                      y0, y1, z0, z1, min_len=0.003):
    verts, faces = [], []
    for p, q in segs:
        c = _clip(y0, y1, z0, z1, p, q)
        if c is None:
            continue
        (ya, za), (yb, zb) = c
        if math.hypot(yb - ya, zb - za) < min_len:
            continue
        a = (x_of(ya, za) - set_back, ya, za)
        b = (x_of(yb, zb) - set_back, yb, zb)
        _bar(verts, faces, a, b, wire * 0.5, depth)
    return M.obj(name, verts, faces, collection, mat, smooth=False)


def hexagon(name, y0, y1, z0, z1, x_of, set_back, collection, mat,
            cell=0.030, wire=0.0030, depth=0.006, pointy=False):
    """Honeycomb: hexagons of across-flats size `cell`."""
    r = cell / math.sqrt(3.0)                    # circumradius
    segs, seen = [], set()
    if pointy:
        dy, dz = cell, 1.5 * r
    else:
        dy, dz = 1.5 * r, cell
    ny = int((y1 - y0) / dy) + 3
    nz = int((z1 - z0) / dz) + 3
    for i in range(-1, ny):
        for j in range(-1, nz):
            if pointy:
                cy = y0 + i * dy + (0.5 * cell if j % 2 else 0.0)
                cz = z0 + j * dz
                a0 = math.pi / 6.0
            else:
                cy = y0 + i * dy
                cz = z0 + j * dz + (0.5 * cell if i % 2 else 0.0)
                a0 = 0.0
            corners = [(cy + r * math.cos(a0 + k * math.pi / 3.0),
                        cz + r * math.sin(a0 + k * math.pi / 3.0)) for k in range(6)]
            for k in range(6):
                p, q = corners[k], corners[(k + 1) % 6]
                key = tuple(sorted(((round(p[0], 5), round(p[1], 5)),
                                    (round(q[0], 5), round(q[1], 5)))))
                if key in seen:
                    continue
                seen.add(key)
                segs.append((p, q))
    return _segments_to_mesh(name, segs, x_of, set_back, collection, mat, wire,
                             depth, y0, y1, z0, z1)


def slats(name, y0, y1, z0, z1, x_of, set_back, collection, mat, count=6,
          blade=0.008, depth=0.020, angle_deg=0.0, n=12):
    """Horizontal louvres: `count` blades `blade` tall, `depth` deep, tilted
    angle_deg (positive = leading edge up), each following the surface."""
    verts, faces = [], []
    a = math.radians(angle_deg)
    for k in range(count):
        zc = z0 + (z1 - z0) * (k + 0.5) / count
        rows = []
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / float(n)
            x = x_of(y, zc) - set_back
            dz = 0.5 * blade
            rows.append([(x, y, zc + dz), (x - depth * math.cos(a), y, zc + dz - depth * math.sin(a)),
                         (x - depth * math.cos(a), y, zc - dz - depth * math.sin(a)), (x, y, zc - dz)])
        base = len(verts)
        for r in rows:
            verts.extend(r)
        for i in range(n):
            s, t = base + i * 4, base + (i + 1) * 4
            for j in range(4):
                j2 = (j + 1) % 4
                faces.append([s + j, s + j2, t + j2, t + j])
    return M.obj(name, verts, faces, collection, mat, smooth=False)


def dots(name, y0, y1, z0, z1, x_of, set_back, collection, mat, pitch=0.024,
         r=0.0045, height=0.003, seg=8, stagger=True):
    """A field of round studs standing `height` off the surface."""
    verts, faces = [], []
    j = 0
    z = z0 + pitch * 0.5
    while z <= z1 - pitch * 0.25:
        off = 0.5 * pitch if (stagger and j % 2) else 0.0
        y = y0 + pitch * 0.5 + off
        while y <= y1 - pitch * 0.25:
            x = x_of(y, z) - set_back
            base = len(verts)
            verts.append((x + height, y, z))
            for k in range(seg):
                ang = 2.0 * math.pi * k / seg
                verts.append((x + height, y + r * math.cos(ang), z + r * math.sin(ang)))
            for k in range(seg):
                ang = 2.0 * math.pi * k / seg
                verts.append((x, y + r * 1.15 * math.cos(ang), z + r * 1.15 * math.sin(ang)))
            for k in range(seg):
                k2 = (k + 1) % seg
                faces.append([base, base + 1 + k, base + 1 + k2])
                faces.append([base + 1 + k, base + 1 + seg + k, base + 1 + seg + k2,
                              base + 1 + k2])
            y += pitch
        z += pitch * (0.866 if stagger else 1.0)
        j += 1
    return M.obj(name, verts, faces, collection, mat, smooth=False)


PATTERNS = {"diamond": diamond, "hexagon": hexagon, "slats": slats, "dots": dots}
