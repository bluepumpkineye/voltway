"""Lamps built between two measured edges, conforming to the body.

A lamp on a modern car is a lens whose outline is two 3D edge curves (upper and
lower) that wrap round a corner. Everything here is built from those two edges
- resampled to the same number of stations with geom.polyline - and a `place`
function that puts a point on the body:

    place(p, d) -> ((x, y, z), normal)     e.g. a Placer.radial bound to the
                                           lamp's centre and body meshes

    lens           the lens sheet, crowned, solidified
    seals          thin satin bands just outside both edges, so the lens reads
                   as set into the body with a shadow gap, not a sticker
    band_between   a strip between the edges at fractions ks - DRL blades,
                   light pipes, chrome guides
    projector      a round module: reflector bowl plus dark lens

Lessons from the SU7:
* Emit only from what really lights (DRL blade, pipe). An emissive lens reads
  as a fluorescent tube.
* Opaque dark lens material, not transmission: the lamp sits proud of the body
  with paint behind it, and opaque dark glass is what exports to glTF.
* Wrap-round lamps must be placed with a radial ray cast from inside the
  corner. Nearest-point projection spans the corner as a chord.
"""
import math

from mathutils import Vector

from .. import geom
from .. import mesh as M


def lens(name, lo, up, place, collection, mat, nk, dist, outward,
         thickness=0.0035, bevel=(0.0012, 2, 30), mirror=True):
    """Lens sheet between edge polylines lo and up (same length).

    dist(k, nk) is how proud of the body row k sits - pass a crown, e.g.
    lambda k, nk: 0.004 + 0.0016 * sin(pi * k / nk).
    """
    rows = [[place(geom.lerp(lo[i], up[i], k / float(nk)), dist(k, nk))[0]
             for k in range(nk + 1)] for i in range(len(lo))]
    ob = M.grid(name, rows, collection, mat, outward)
    if thickness:
        M.solidify(ob, thickness)
    if bevel:
        M.bevel(ob, bevel[0], bevel[1], bevel[2])
    if mirror:
        M.mirror_y(ob)
    return ob


def seals(prefix, lo, up, place, collection, mat, outward, width=0.0055, d=0.0010,
          names=("Low", "Up"), mirror=True):
    """Satin bands `width` wide just outside each edge. Returns [low, up]."""
    made = []
    for nm, edge, other in ((names[0], lo, up), (names[1], up, lo)):
        cols = []
        for i in range(len(edge)):
            a = edge[i]
            dd = [a[k] - other[i][k] for k in range(3)]
            L = math.sqrt(sum(c * c for c in dd)) or 1.0
            b = tuple(a[k] + dd[k] / L * width for k in range(3))
            cols.append([place(a, d)[0], place(b, d)[0]])
        seal = M.grid(prefix + nm, cols, collection, mat, outward)
        if mirror:
            M.mirror_y(seal)
        made.append(seal)
    return made


def band_between(name, lo, up, stations, ks, place, dist, collection, mat,
                 outward, mirror=True):
    """A strip across the lamp at edge fractions ks, over the given stations.

    dist(k) is the offset for fraction k. For a DRL blade use two or three ks
    close together; for a light pipe ks around 0.5.
    """
    rows = [[place(geom.lerp(lo[i], up[i], k), dist(k))[0] for k in ks]
            for i in stations]
    ob = M.grid(name, rows, collection, mat, outward)
    if mirror:
        M.mirror_y(ob)
    return ob


def projector(name, c, n, r, collection, lib, seg=20, lens_ratio=0.62,
              lens_lift=0.0009, mats=("lamp_bowl", "lamp_smoked"), mirror=True):
    """A reflector bowl with a dark lens: bright rim, dark centre.

    Returns [bowl, lens]. Keep the bowl a dark satin, not chrome: metal rims
    catch the key light and read as white donuts in every close-up.
    """
    nvec = Vector(n).normalized()
    upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
    t1 = nvec.cross(upv).normalized()
    t2 = nvec.cross(t1).normalized()
    parts = []
    for tag, rad, lift, mat in (("Bowl", r, 0.0, lib[mats[0]]),
                                ("Lens", r * lens_ratio, lens_lift, lib[mats[1]])):
        cv = Vector(c) + nvec * lift
        verts = [tuple(cv)]
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append(tuple(cv + (t1 * math.cos(a) + t2 * math.sin(a)) * rad))
        faces = [[0, 1 + i, 1 + (i + 1) % seg] for i in range(seg)]
        ob = M.obj(name + tag, verts, faces, collection, mat)
        M.orient(ob.data, lambda cc, nv=nvec: tuple(nv))
        if mirror:
            M.mirror_y(ob)
        parts.append(ob)
    return parts


def station_nearest_y(lo, up, y):
    """Index of the lamp station whose mid-line is nearest lateral position y."""
    return min(range(len(lo)), key=lambda i: abs(0.5 * (lo[i][1] + up[i][1]) - y))
