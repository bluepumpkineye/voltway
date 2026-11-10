"""Primitives, materials and object helpers for the anatomy kit (carkit.anatomy).

Everything here works in METRES and Blender axes (+X forward, +Y left, +Z up). Parts are
described in WORLD coordinates and given a `pivot`: the mesh is stored around that point and
the object's origin sits on it, so a part that has to turn (a rotor, an arm, a damper) turns
about the right axis once it is a glTF node.

A part is a `MB` (mesh builder: plain lists of vertices, faces and material slots), turned
into an object by `solid()`. Parts are parented under empties made by `group()`, which carry
only a translation, so a child's local position is its world position minus its parent's.
"""
import json
import math

import bpy
import bmesh
from mathutils import Vector, Quaternion
from mathutils.geometry import tessellate_polygon

V = Vector
Z = Vector((0.0, 0.0, 1.0))
X = Vector((1.0, 0.0, 0.0))
Y = Vector((0.0, 1.0, 0.0))


# ------------------------------------------------------------------ materials
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(hexcol):
    h = hexcol.lstrip("#")
    return tuple(_lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat(name, hexcol, metal=0.0, rough=0.5, emit=None, emit_k=0.0, coat=0.0):
    """A Principled material that survives glTF (base colour, metallic, roughness, emission)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*rgb(hexcol), 1.0)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb(emit), 1.0)
        b.inputs['Emission Strength'].default_value = emit_k
    return m


# ------------------------------------------------------------- 2D outlines
def circle(r, n=48, phase=0.0, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n)) for i in range(n)]


def rrect(w, h, r, n=5, cx=0.0, cy=0.0):
    """A rounded rectangle, counter-clockwise, w x h with corner radius r."""
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6)
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = sx * (w / 2 - r), sy * (h / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((cx + ccx + r * math.cos(a), cy + ccy + r * math.sin(a)))
    return pts


def gear_outline(r_root, r_tip, teeth, phase=0.0):
    """A spur gear's outline: `teeth` trapezoid teeth between root and tip radius, counter-clockwise."""
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = phase + i * step
        for (f, r) in ((0.08, r_root), (0.30, r_tip), (0.52, r_tip), (0.74, r_root)):
            pts.append((r * math.cos(a + f * step), r * math.sin(a + f * step)))
    return pts


def ccw(pts):
    """The outline in counter-clockwise order."""
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if area > 0 else list(reversed(pts))


# --------------------------------------------------------------- mesh builder
def frame_q(direction):
    """Rotation taking local +Z to `direction`."""
    d = Vector(direction).normalized()
    return Z.rotation_difference(d)


def basis_q(right, up):
    """Rotation taking local X, Y, Z to `right`, `up` and their cross product."""
    from mathutils import Matrix
    r = Vector(right).normalized()
    u = (Vector(up) - r * Vector(up).dot(r)).normalized()
    return Matrix((r, u, r.cross(u))).transposed().to_quaternion()


def round_path(pts, rad, n=6):
    """A polyline with every interior corner rounded to a circular arc of (at most) radius `rad` (hoses, cables, bars)."""
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        da, dc = (a - b), (c - b)
        la, lc = da.length, dc.length
        if la < 1e-9 or lc < 1e-9:
            out.append(b)
            continue
        da, dc = da / la, dc / lc
        ang = da.angle(dc)
        if ang > math.pi - 1e-3 or ang < 1e-3:
            out.append(b)
            continue
        t = min(rad / math.tan(ang / 2.0), la * 0.48, lc * 0.48)
        p0, p2 = b + da * t, b + dc * t
        for k in range(n + 1):
            s = k / n
            q0, q1 = p0 + (b - p0) * s, b + (p2 - b) * s
            out.append(q0 + (q1 - q0) * s)
    out.append(pts[-1])
    return out


def profile_I(w, h, tw, tf, r=0.0):
    """An I-beam outline (CCW, x = flange width direction, y = depth), the web `tw` thick, the flanges `tf`."""
    a, b = w / 2, h / 2
    t = tw / 2
    return [(-a, -b), (a, -b), (a, -b + tf), (t, -b + tf), (t, b - tf), (a, b - tf), (a, b), (-a, b), (-a, b - tf), (-t, b - tf),
            (-t, -b + tf), (-a, -b + tf)]


def profile_oval(a, b, n=14):
    return [(a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n)) for i in range(n)]


class MB:
    """Vertices, faces, a material slot per face and (optionally) a UV per face corner, in world coordinates.

    UVs are in METRES of surface (a box face's own two edges, a cylinder's circumference and length, a sweep's arc length): the
    material's tile size (`xr_tile`) turns them into texture coordinates in `solid()`, so a texture's scale is physical. A face
    given no UV is box-projected there."""

    def __init__(self):
        self.v = []
        self.f = []
        self.m = []
        self.uv = []

    def add(self, verts, faces, mi=0, uvs=None):
        b = len(self.v)
        self.v += [tuple(p) for p in verts]
        for k, f in enumerate(faces):
            self.f.append([i + b for i in f])
            self.m.append(mi)
            self.uv.append(uvs[k] if uvs is not None else None)

    def _face(self, f, mi, uv=None):
        self.f.append(f)
        self.m.append(mi)
        self.uv.append(uv)

    def append(self, other, loc=(0, 0, 0), q=None, mi_map=None, scale=1.0):
        """Copy another builder in, rotated by `q`, scaled and moved to `loc` (instancing: a bolt, a terminal, a fin)."""
        loc = Vector(loc)
        b = len(self.v)
        for p in other.v:
            w = Vector(p) * scale
            self.v.append(tuple((q @ w if q else w) + loc))
        for f, m, u in zip(other.f, other.m, other.uv):
            self.f.append([i + b for i in f])
            self.m.append(mi_map[m] if mi_map else m)
            self.uv.append(u)

    # -- solids
    def box(self, c, sx, sy, sz, mi=0, q=None):
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        loc = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
               (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
        c = Vector(c)
        vs = [(q @ Vector(p) if q else Vector(p)) + c for p in loc]
        fs = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [3, 0, 4, 7]]
        ax = [(0, 1), (0, 1), (0, 2), (0, 2), (1, 2), (1, 2)]
        uvs = [[(loc[i][ax[k][0]], loc[i][ax[k][1]]) for i in f] for k, f in enumerate(fs)]
        self.add(vs, fs, mi, uvs)

    def box_between(self, a, b, w, h, up=Z, mi=0):
        """A beam from a to b, w wide (across `up` x length) and h tall (along `up`)."""
        a, b = Vector(a), Vector(b)
        d = (b - a)
        L = d.length
        zx = d.normalized()
        ux = Vector(up) - zx * Vector(up).dot(zx)
        if ux.length < 1e-6:
            ux = Y - zx * Y.dot(zx)
        ux.normalize()
        wy = ux.cross(zx).normalized()
        # local: x = length direction, y = across, z = up
        from mathutils import Matrix
        M = Matrix((zx, wy, ux)).transposed()
        self.box((a + b) / 2, L, w, h, mi, M.to_quaternion())

    def cyl(self, p0, p1, r0, r1=None, seg=24, mi=0, caps=True):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        q = frame_q(d)
        r1 = r0 if r1 is None else r1
        ring0, ring1 = [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ca, sa = math.cos(a), math.sin(a)
            ring0.append(p0 + q @ Vector((r0 * ca, r0 * sa, 0)))
            ring1.append(p0 + q @ Vector((r1 * ca, r1 * sa, L)))
        vs = ring0 + ring1
        fs = [[i, (i + 1) % seg, seg + (i + 1) % seg, seg + i] for i in range(seg)]
        circ = 2 * math.pi * max(r0, r1)
        uvs = [[(i * circ / seg, 0.0), ((i + 1) * circ / seg, 0.0), ((i + 1) * circ / seg, L), (i * circ / seg, L)] for i in range(seg)]
        if caps:
            vs += [p0, p1]
            c0, c1 = 2 * seg, 2 * seg + 1
            fs += [[(i + 1) % seg, i, c0] for i in range(seg)]
            fs += [[seg + i, seg + (i + 1) % seg, c1] for i in range(seg)]

            def pl(rr, i):
                a = 2 * math.pi * i / seg
                return (rr * math.cos(a), rr * math.sin(a))
            uvs += [[pl(r0, i + 1), pl(r0, i), (0.0, 0.0)] for i in range(seg)]
            uvs += [[pl(r1, i), pl(r1, i + 1), (0.0, 0.0)] for i in range(seg)]
        self.add(vs, fs, mi, uvs)

    def sphere(self, c, r, seg=14, rings=8, mi=0):
        c = Vector(c)
        vs = [c + Vector((0, 0, r)), c + Vector((0, 0, -r))]
        for k in range(1, rings):
            t = math.pi * k / rings
            for i in range(seg):
                a = 2 * math.pi * i / seg
                vs.append(c + Vector((r * math.sin(t) * math.cos(a), r * math.sin(t) * math.sin(a), r * math.cos(t))))
        fs = []
        uvs = []

        def uv(i, k):          # i: longitude index (may be seg), k: ring 0..rings
            return (2 * math.pi * r * i / seg, math.pi * r * k / rings)
        for i in range(seg):
            fs.append([0, 2 + (i + 1) % seg, 2 + i])
            uvs.append([(uv(i, 0)[0] + uv(1, 0)[0] / 2, 0.0), uv(i + 1, 1), uv(i, 1)])
        for k in range(rings - 2):
            for i in range(seg):
                a = 2 + k * seg + i
                b = 2 + k * seg + (i + 1) % seg
                fs.append([a, b, b + seg, a + seg])
                uvs.append([uv(i, k + 1), uv(i + 1, k + 1), uv(i + 1, k + 2), uv(i, k + 2)])
        last = 2 + (rings - 2) * seg
        for i in range(seg):
            fs.append([1, last + i, last + (i + 1) % seg])
            uvs.append([(uv(i, rings)[0] + uv(1, 0)[0] / 2, math.pi * r), uv(i, rings - 1), uv(i + 1, rings - 1)])
        self.add(vs, fs, mi, uvs)

    def tube(self, path, r, seg=10, mi=0, caps=True, r_end=None):
        """A circular section swept along a polyline (parallel-transport frames). `r` may be a list (one radius per point)."""
        pts = [Vector(p) for p in path]
        n = len(pts)
        rs = [r + (((r_end if r_end is not None else r) - r) * i / max(1, n - 1)) for i in range(n)] if not isinstance(r, (list, tuple)) else list(r)
        t0 = (pts[1] - pts[0]).normalized()
        nrm = X if abs(t0.dot(X)) < 0.9 else Y
        nrm = (nrm - t0 * nrm.dot(t0)).normalized()
        vs = []
        D = [0.0]
        for i in range(1, n):
            D.append(D[-1] + (pts[i] - pts[i - 1]).length)
        for i in range(n):
            t = ((pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])).normalized()
            nrm = (nrm - t * nrm.dot(t))
            if nrm.length < 1e-6:
                nrm = Y if abs(t.dot(Y)) < 0.9 else X
                nrm = nrm - t * nrm.dot(t)
            nrm.normalize()
            bn = t.cross(nrm)
            for k in range(seg):
                a = 2 * math.pi * k / seg
                vs.append(pts[i] + (nrm * math.cos(a) + bn * math.sin(a)) * rs[i])
        fs = []
        uvs = []
        rm = max(rs)
        for i in range(n - 1):
            for k in range(seg):
                a, b = i * seg + k, i * seg + (k + 1) % seg
                fs.append([a, a + seg, b + seg, b])
                v0, v1 = 2 * math.pi * rm * k / seg, 2 * math.pi * rm * (k + 1) / seg
                uvs.append([(D[i], v0), (D[i + 1], v0), (D[i + 1], v1), (D[i], v1)])
        if caps:
            vs += [pts[0], pts[-1]]
            c0, c1 = n * seg, n * seg + 1
            fs += [[(k + 1) % seg, k, c0] for k in range(seg)]
            fs += [[(n - 1) * seg + k, (n - 1) * seg + (k + 1) % seg, c1] for k in range(seg)]

            def pl(rr, k):
                a = 2 * math.pi * k / seg
                return (rr * math.cos(a), rr * math.sin(a))
            uvs += [[pl(rs[0], k + 1), pl(rs[0], k), (0.0, 0.0)] for k in range(seg)]
            uvs += [[pl(rs[-1], k), pl(rs[-1], k + 1), (0.0, 0.0)] for k in range(seg)]
        self.add(vs, fs, mi, uvs)

    def sweep(self, path, prof, mi=0, caps=True, scales=None, up=None):
        """A general 2D profile (CCW list of (x, y), x along the frame's normal, y along its binormal) swept along a polyline;
        `scales` scales the profile per point (a forged arm that swells at its ends). UV: u = distance along, v = round the profile."""
        pts = [Vector(p) for p in path]
        n, m = len(pts), len(prof)
        t0 = (pts[1] - pts[0]).normalized()
        ref = Vector(up) if up is not None else (X if abs(t0.dot(X)) < 0.9 else Y)
        nrm = ref - t0 * ref.dot(t0)
        if nrm.length < 1e-6:
            nrm = Y - t0 * Y.dot(t0)
        nrm.normalize()
        per = [0.0]
        for k in range(m):
            per.append(per[-1] + (Vector(prof[(k + 1) % m]) - Vector(prof[k])).length)
        D = [0.0]
        for i in range(1, n):
            D.append(D[-1] + (pts[i] - pts[i - 1]).length)
        vs = []
        for i in range(n):
            t = ((pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])).normalized()
            nrm = nrm - t * nrm.dot(t)
            if nrm.length < 1e-6:
                nrm = Y if abs(t.dot(Y)) < 0.9 else X
                nrm = nrm - t * nrm.dot(t)
            nrm.normalize()
            bn = t.cross(nrm)
            s = scales[i] if scales else 1.0
            for (px, py) in prof:
                vs.append(pts[i] + (nrm * px + bn * py) * s)
        fs, uvs = [], []
        for i in range(n - 1):
            for k in range(m):
                a, b = i * m + k, i * m + (k + 1) % m
                fs.append([a, a + m, b + m, b])
                uvs.append([(D[i], per[k]), (D[i + 1], per[k]), (D[i + 1], per[k + 1]), (D[i], per[k + 1])])
        if caps:
            c0 = Vector((0, 0, 0))
            for (px, py) in prof:
                c0 += Vector((px, py, 0))
            # a fan from the profile's centroid works for the star-shaped outlines used here (I-beams are not: triangulate those)
            flat = [Vector((px, py, 0)) for (px, py) in prof]
            tris = tessellate_polygon([flat])
            for (a, b, c) in tris:
                fs.append([a, c, b])
                uvs.append([prof[a], prof[c], prof[b]])
                fs.append([(n - 1) * m + a, (n - 1) * m + b, (n - 1) * m + c])
                uvs.append([prof[a], prof[b], prof[c]])
        self.add(vs, fs, mi, uvs)

    def lathe(self, profile, origin, axis, seg=48, mi=0):
        """Revolve (radius, distance-along-axis) pairs about the line through `origin` along `axis`."""
        o = Vector(origin)
        q = frame_q(axis)
        vs = []
        idx = []
        cum = [0.0]
        for k in range(1, len(profile)):
            cum.append(cum[-1] + math.hypot(profile[k][0] - profile[k - 1][0], profile[k][1] - profile[k - 1][1]))
        rref = max(r for r, _ in profile) or 1e-3
        for (r, d) in profile:
            if r < 1e-9:
                vs.append(o + q @ Vector((0, 0, d)))
                idx.append(('p', len(vs) - 1))
            else:
                base = len(vs)
                for i in range(seg):
                    a = 2 * math.pi * i / seg
                    vs.append(o + q @ Vector((r * math.cos(a), r * math.sin(a), d)))
                idx.append(('r', base))
        fs, uvs = [], []
        for k in range(len(profile) - 1):
            (ka, a), (kb, b) = idx[k], idx[k + 1]
            for i in range(seg):
                j = (i + 1) % seg
                ui, uj = 2 * math.pi * rref * i / seg, 2 * math.pi * rref * (i + 1) / seg
                um = (ui + uj) / 2
                if ka == 'r' and kb == 'r':
                    fs.append([a + i, a + j, b + j, b + i])
                    uvs.append([(ui, cum[k]), (uj, cum[k]), (uj, cum[k + 1]), (ui, cum[k + 1])])
                elif ka == 'p' and kb == 'r':
                    fs.append([a, b + j, b + i])
                    uvs.append([(um, cum[k]), (uj, cum[k + 1]), (ui, cum[k + 1])])
                elif ka == 'r' and kb == 'p':
                    fs.append([a + i, a + j, b])
                    uvs.append([(ui, cum[k]), (uj, cum[k]), (um, cum[k + 1])])
        self.add(vs, fs, mi, uvs)

    def prism(self, outer, holes, z0, z1, origin=(0, 0, 0), axis=Z, mi=0, mi_cap=None, caps=True, twist=0.0, steps=1):
        """Extrude a 2D outline (with holes) between local z0 and z1 of a frame at `origin` whose local +Z is `axis`. Local +X is
        whatever rotation_difference gives. `twist` (radians over the length, in `steps` slices) makes a helical extrusion: a
        helical gear."""
        o = Vector(origin)
        q = frame_q(axis)
        polys = [list(outer)] + [list(h) for h in holes]
        vs = []
        starts = []                       # [polygon][ring] -> first vertex
        for pl in polys:
            ring_start = []
            for r in range(steps + 1):
                ring_start.append(len(vs))
                z = z0 + (z1 - z0) * r / steps
                ang = twist * r / steps
                ca, sa = math.cos(ang), math.sin(ang)
                for (x, y) in pl:
                    vs.append(o + q @ Vector((x * ca - y * sa, x * sa + y * ca, z)))
            starts.append(ring_start)
        fs, uvs = [], []
        for pi, pl in enumerate(polys):
            n = len(pl)
            S = [0.0]
            for i in range(n):
                S.append(S[-1] + math.hypot(pl[(i + 1) % n][0] - pl[i][0], pl[(i + 1) % n][1] - pl[i][1]))
            for r in range(steps):
                s0, s1 = starts[pi][r], starts[pi][r + 1]
                za, zb = z0 + (z1 - z0) * r / steps, z0 + (z1 - z0) * (r + 1) / steps
                for i in range(n):
                    j = (i + 1) % n
                    fs.append([s0 + i, s0 + j, s1 + j, s1 + i])
                    uvs.append([(S[i], za), (S[i + 1], za), (S[i + 1], zb), (S[i], zb)])
        base = len(self.v)
        self.add(vs, fs, mi, uvs)
        if caps:
            flat = [[Vector((x, y, 0)) for (x, y) in pl] for pl in polys]
            tris = tessellate_polygon(flat)
            f_to = []
            for pi, pl in enumerate(polys):
                for k in range(len(pl)):
                    f_to.append((pi, k))
            cm = mi if mi_cap is None else mi_cap
            planar = [pt for pl in polys for pt in pl]
            for (a, b, c) in tris:
                pa, ka = f_to[a]
                pb, kb = f_to[b]
                pc, kc = f_to[c]
                bot = lambda pi, k: base + starts[pi][0] + k
                top = lambda pi, k: base + starts[pi][steps] + k
                self._face([bot(pa, ka), bot(pc, kc), bot(pb, kb)], cm, [planar[a], planar[c], planar[b]])
                self._face([top(pa, ka), top(pb, kb), top(pc, kc)], cm, [planar[a], planar[b], planar[c]])

    def torus(self, c, axis, R, r, seg=24, seg2=8, mi=0):
        """A ring (O-ring, clamp, cable tie) about the line through `c` along `axis`."""
        q = frame_q(axis)
        c = Vector(c)
        vs, fs, uvs = [], [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            for k in range(seg2):
                b = 2 * math.pi * k / seg2
                rr = R + r * math.cos(b)
                vs.append(c + q @ Vector((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        for i in range(seg):
            for k in range(seg2):
                a0, a1 = i * seg2 + k, ((i + 1) % seg) * seg2 + k
                b0, b1 = i * seg2 + (k + 1) % seg2, ((i + 1) % seg) * seg2 + (k + 1) % seg2
                fs.append([a0, a1, b1, b0])
                uvs.append([(2 * math.pi * R * i / seg, 2 * math.pi * r * k / seg2), (2 * math.pi * R * (i + 1) / seg, 2 * math.pi * r * k / seg2),
                            (2 * math.pi * R * (i + 1) / seg, 2 * math.pi * r * (k + 1) / seg2), (2 * math.pi * R * i / seg, 2 * math.pi * r * (k + 1) / seg2)])
        self.add(vs, fs, mi, uvs)

    # -- hardware
    def bolt(self, p, axis, r=0.0075, h=0.006, mi=0, mi_w=None, washer=True):
        """A hex-head bolt (or nut) sitting on a surface at `p` with its head pointing along `axis`: washer, hex head with a chamfered top."""
        proto = _bolt_proto(r, h, washer)
        self.append(proto, p, frame_q(axis), mi_map=[mi, mi if mi_w is None else mi_w])

    def sticker(self, c, right, up, w, h, rect, mi=0, lift=0.0):
        """A label, 0.5 mm thick, with `rect` = (u0, v0, u1, v1) of the label atlas on its face. Faces `right` x `up` outward."""
        q = basis_q(right, up)
        n = Vector(right).normalized().cross((Vector(up) - Vector(right).normalized() * Vector(up).dot(Vector(right).normalized())).normalized())
        c = Vector(c) + n * (0.00025 + lift)
        u0, v0, u1, v1 = rect
        hx, hy = w / 2, h / 2
        loc = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
        top = [(u0 + (x / w + 0.5) * (u1 - u0), v0 + (y / h + 0.5) * (v1 - v0)) for (x, y) in loc]
        t = 0.0005
        vs = [c + q @ Vector((x, y, z)) for z in (-t / 2, t / 2) for (x, y) in loc]
        fs = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [3, 0, 4, 7]]
        edge = [(u0, v0)] * 4
        uvs = [edge, top, edge, edge, edge, edge]
        self.add(vs, fs, mi, uvs)


_BOLTS = {}


def _bolt_proto(r, h, washer):
    key = (round(r, 5), round(h, 5), washer)
    pr = _BOLTS.get(key)
    if pr is None:
        pr = MB()
        wt = max(0.0016, r * 0.2)
        z = 0.0
        if washer:
            pr.cyl((0, 0, 0), (0, 0, wt), r * 1.55, seg=8, mi=1)
            z = wt
        pr.cyl((0, 0, z), (0, 0, z + h), r, r * 0.9, seg=6, mi=0)
        _BOLTS[key] = pr
    return pr


# ------------------------------------------------------------------- objects
def collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def wloc(ob):
    s = Vector((0, 0, 0))
    while ob is not None:
        s += ob.location
        ob = ob.parent
    return s


def group(name, coll, loc=(0, 0, 0), parent=None, **meta):
    """An empty carrying a translation (world `loc`) and, optionally, the export metadata."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.05
    coll.objects.link(e)
    if parent is not None:
        e.parent = parent
        e.location = Vector(loc) - wloc(parent)
    else:
        e.location = Vector(loc)
    if meta:
        e["xr"] = json.dumps(meta, separators=(",", ":"))
    return e


def _box_uv(pts):
    """Box-projected UVs (metres) for a face with no UVs of its own: the two axes across its dominant normal."""
    n = Vector((0, 0, 0))
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    ax = max(range(3), key=lambda k: abs(n[k]))
    a, b = [(1, 2), (0, 2), (0, 1)][ax]
    return [(p[a], p[b]) for p in pts]


def solid(name, mb, mats, coll, parent=None, pivot=None, bevel=0.0, angle=35.0, bevel_seg=2, **meta):
    """Turn a builder into an object: the origin on `pivot` (default the parent's origin)."""
    if pivot is None:
        pivot = wloc(parent) if parent is not None else Vector((0, 0, 0))
    pivot = Vector(pivot)
    vs = [(p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]) for p in mb.v]
    # drop degenerate faces (a repeated vertex) up front so the per-face arrays below stay in step with the mesh
    keep = [k for k, f in enumerate(mb.f) if len(set(f)) >= 3]
    faces = [mb.f[k] for k in keep]
    mids = [mb.m[k] for k in keep]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    for m in mats:
        me.materials.append(m)
    me.update()
    me.validate(verbose=False)
    for i, p in enumerate(me.polygons):
        if i < len(mids):
            p.material_index = min(mids[i], max(0, len(mats) - 1))
        p.use_smooth = True
    # UVs: the builder's own (metres of surface) divided by each face's material tile size; box-projected where it gave none
    if len(me.polygons) == len(faces):
        tiles = [float(m.get("xr_tile", 1.0)) if m is not None else 1.0 for m in mats] or [1.0]
        flat = []
        for k, f in zip(keep, faces):
            uv = mb.uv[k]
            if uv is None:
                uv = _box_uv([mb.v[i] for i in f])
            s = 1.0 / tiles[min(mb.m[k], len(tiles) - 1)]
            for (u, v) in uv:
                flat.append(u * s)
                flat.append(v * s)
        layer = me.uv_layers.new(name="UVMap")
        if len(flat) == 2 * len(me.loops):
            layer.data.foreach_set("uv", flat)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        ob.location = pivot - wloc(parent)
    else:
        ob.location = pivot
    if bevel > 0:
        # bevel only the sharp edges of BIG shapes (longer than 3 cm): a bolt, a fin tip or a terminal gains nothing from a bevel and
        # it doubles their faces (the first version bevelled everything: 600 k triangles)
        bm2 = bmesh.new()
        bm2.from_mesh(me)
        wl = bm2.edges.layers.float.get("bevel_weight_edge") or bm2.edges.layers.float.new("bevel_weight_edge")
        lim = math.radians(angle)
        for e in bm2.edges:
            if len(e.link_faces) == 2 and e.calc_length() > 0.03 and e.calc_face_angle(0.0) > lim:
                e[wl] = 1.0
        bm2.to_mesh(me)
        bm2.free()
        b = ob.modifiers.new("Bevel", 'BEVEL')
        b.width = bevel
        b.segments = bevel_seg
        b.limit_method = 'WEIGHT'
        b.edge_weight = "bevel_weight_edge"
    es = ob.modifiers.new("Edges", 'EDGE_SPLIT')
    es.split_angle = math.radians(angle)
    if meta:
        ob["xr"] = json.dumps(meta, separators=(",", ":"))
    return ob


def tri_count(objs):
    n = 0
    for o in objs:
        if o.type == 'MESH':
            n += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return n


def to_gltf(p):
    """Blender axes (x fwd, y left, z up) to glTF/viewer axes (x fwd, y up, z right)."""
    return [round(p[0], 4), round(p[2], 4), round(-p[1], 4)]
