"""Putting parts onto a body.

Three ways to find where a part sits, in order of preference:

1. Analytic - `CarBody.project` / `CarBody.side_point` evaluate the smooth
   master surface itself. Best for anything broad and smooth (fins, stripes,
   handles): no mesh gaps, no recesses, no facets.
2. Radial ray cast - `Placer.radial(p, centre, names)` casts from outside, back
   toward a point INSIDE the corner, onto the built meshes. Use it for parts
   that wrap a corner (headlamps, tail lamps): nearest-point projection snaps
   neighbouring points to different surfaces there and the part spans the
   corner as a flat chord that the body pokes through.
3. Fixed-direction ray cast - `Placer.along(p, d, names)`.

Rays can thread a shut line or land in a recess; for anything that spans
several meshes with gaps between them, prefer the analytic route.
"""
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import bpy


class Placer:
    """BVH ray casting onto named body meshes, with an analytic fallback.

    `fallback(p, d)` must return ((x, y, z), normal) - normally CarBody.proud.
    Trees are cached per tuple of names; call reset() after the meshes change.
    """

    def __init__(self, fallback):
        self.fallback = fallback
        self._bvh = {}

    def reset(self):
        self._bvh.clear()

    def trees(self, names):
        key = tuple(names)
        hit = self._bvh.get(key)
        if hit is None:
            dg = bpy.context.evaluated_depsgraph_get()
            hit = [BVHTree.FromObject(bpy.data.objects[n], dg)
                   for n in names if bpy.data.objects.get(n)]
            self._bvh[key] = hit
        return hit

    def radial(self, p, centre, names, d=0.0, reach=0.35):
        """Body point on the ray centre -> p, pushed d along its outward normal.

        The way to make a part follow a curved body corner (a lamp or light
        bar wrapping round the nose or tail, trim round a corner): cast from
        a centre inside the corner through each outline point, so the part
        hugs the surface instead of cutting across it as a chord."""
        c, pv = Vector(centre), Vector(p)
        ray = pv - c
        if ray.length < 1e-6:
            return self.fallback(p, d)
        ray.normalize()
        o = pv + ray * reach
        best = None
        for tr in self.trees(names):
            loc, nrm, _i, dist = tr.ray_cast(o, -ray, reach * 3.0)
            if loc is not None and (best is None or dist < best[2]):
                best = (loc, nrm, dist)
        if best is None:                       # threaded a shut line: fall back
            return self.fallback(p, d)
        loc, nrm = best[0], best[1].normalized()
        if nrm.dot(ray) < 0.0:
            nrm = -nrm
        q = loc + nrm * d
        return (q.x, q.y, q.z), (nrm.x, nrm.y, nrm.z)

    def along(self, p, d, names, reach=0.40):
        """Body point hit by a ray arriving along -d at p (None if it misses)."""
        o = Vector(p) + Vector(d) * reach
        best = None
        for tr in self.trees(names):
            loc, nrm, _i, dist = tr.ray_cast(o, -Vector(d), reach * 2.5)
            if loc is not None and (best is None or dist < best[1]):
                best = (loc, dist)
        return None if best is None else best[0]


def on_surface(ob, p, n, up_hint=(0.0, 0.0, 1.0)):
    """Orient a flat XY object so its +Z faces n and its +Y points up."""
    nz = Vector(n).normalized()
    upv = Vector(up_hint)
    xv = upv.cross(nz)
    if xv.length < 1e-6:
        xv = Vector((0, 1, 0))
    xv.normalize()
    yv = nz.cross(xv).normalized()
    Mx = Matrix((xv, yv, nz)).transposed().to_4x4()
    Mx.translation = Vector(p)
    ob.matrix_world = Mx
    return ob
