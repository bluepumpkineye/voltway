"""Shared helpers for parametric vehicle construction in Blender."""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix


# ---------------------------------------------------------------- scene utils

def purge(collection_name):
    """Remove a collection and everything in it, so a rebuild is idempotent."""
    col = bpy.data.collections.get(collection_name)
    if col:
        for ob in list(col.objects):
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
        bpy.data.collections.remove(col)
    col = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(col)
    return col


def new_mesh_object(name, verts, faces, collection):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- curve maths

def lerp(a, b, t):
    return a + (b - a) * t


class Curve:
    """Monotone cubic (PCHIP) interpolation through control points.

    Plain piecewise-linear-plus-smoothstep is only C0 at the control points,
    which shows up as visible ripples along a car's flank. PCHIP is C1 and,
    unlike uniform Catmull-Rom, will not overshoot between points - so a
    profile never bulges where the control points say it should be flat.
    """

    def __init__(self, points):
        pts = sorted(points, key=lambda p: p[0])
        self.xs = [p[0] for p in pts]
        self.ys = [p[1] for p in pts]
        n = len(pts)
        h = [self.xs[i + 1] - self.xs[i] for i in range(n - 1)]
        d = [(self.ys[i + 1] - self.ys[i]) / h[i] for i in range(n - 1)]

        m = [0.0] * n
        if n == 2:
            m[0] = m[1] = d[0]
        else:
            m[0] = d[0]
            m[-1] = d[-1]
            for i in range(1, n - 1):
                if d[i - 1] * d[i] <= 0.0:
                    m[i] = 0.0            # local extremum: flatten, never overshoot
                else:
                    w1 = 2.0 * h[i] + h[i - 1]
                    w2 = h[i] + 2.0 * h[i - 1]
                    m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.h, self.d, self.m = h, d, m

    def __call__(self, x):
        xs, ys, m, h = self.xs, self.ys, self.m, self.h
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        lo, hi = 0, len(xs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        t = (x - xs[lo]) / h[lo]
        t2, t3 = t * t, t * t * t
        h00 = 2 * t3 - 3 * t2 + 1
        h10 = t3 - 2 * t2 + t
        h01 = -2 * t3 + 3 * t2
        h11 = t3 - t2
        return (h00 * ys[lo] + h10 * h[lo] * m[lo] +
                h01 * ys[lo + 1] + h11 * h[lo] * m[lo + 1])


def catmull_rom(pts, samples):
    """Sample a Catmull-Rom spline through a list of 2D points."""
    if len(pts) < 2:
        return list(pts)
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    segs = len(ext) - 3
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        n = max(2, int(round(samples / segs)))
        last = (i == segs - 1)
        for j in range(n + (1 if last else 0)):
            t = j / float(n)
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def loft(stations, collection, name, cap_front=True, cap_rear=True):
    """Bridge equal-length rings of 3D points into a surface.

    `stations` is ordered front-to-rear; each is a list of Vectors forming an
    open half-ring that will be mirrored, or a closed ring.
    """
    verts, faces = [], []
    ring = len(stations[0])
    for st in stations:
        assert len(st) == ring, "all stations need the same point count"
        verts.extend([tuple(p) for p in st])

    for s in range(len(stations) - 1):
        a = s * ring
        b = (s + 1) * ring
        for i in range(ring - 1):
            faces.append([a + i, a + i + 1, b + i + 1, b + i])

    if cap_front:
        faces.append(list(range(ring - 1, -1, -1)))
    if cap_rear:
        base = (len(stations) - 1) * ring
        faces.append(list(range(base, base + ring)))

    return new_mesh_object(name, verts, faces, collection)


# ---------------------------------------------------------------- mesh finish

def shade_smooth(ob, angle_deg=36.0):
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    mod = ob.modifiers.new("Smooth by Angle", 'SMOOTH_BY_ANGLE') if hasattr(bpy.types, 'SmoothByAngleModifier') else None
    if mod is None:
        try:
            me.use_auto_smooth = True
            me.auto_smooth_angle = math.radians(angle_deg)
        except AttributeError:
            pass


def add_subsurf(ob, levels=1, render_levels=2):
    m = ob.modifiers.new("Subdivision", 'SUBSURF')
    m.levels = levels
    m.render_levels = render_levels
    return m


def merge_doubles(ob, dist=0.0008):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()


def mirror_y(ob):
    m = ob.modifiers.new("Mirror", 'MIRROR')
    m.use_axis = (False, True, False)
    m.use_clip = True
    m.merge_threshold = 0.001
    return m


def solidify(ob, thickness):
    m = ob.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = thickness
    m.offset = 0.0
    return m


# ---------------------------------------------------------------- materials

def _principled(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def make_material(name, base_color, roughness=0.5, metallic=0.0,
                  coat=0.0, ior=1.45, transmission=0.0, emission=None,
                  emission_strength=0.0, anisotropic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = _principled(mat)
    b.inputs["Base Color"].default_value = (*base_color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    for key, val in (("Coat Weight", coat), ("IOR", ior),
                     ("Transmission Weight", transmission),
                     ("Anisotropic", anisotropic)):
        if key in b.inputs:
            b.inputs[key].default_value = val
    if emission is not None and "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (*emission, 1.0)
        b.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob
