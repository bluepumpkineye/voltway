"""Baked ambient occlusion for the anatomy, per vertex, shipped as the custom attribute `_XRAO` (the web multiplies its environment
light by it: src/lib/xray/fx.ts).

The hardware is hundreds of small, close-set shapes (cells beside cells, bolts on plates, fins on a lid): without contact shading it
looks like clay. An atlas does not suit it (150 m of surface in one 2048 square leaves a texel the size of a bolt), so the
shade is stored at the vertices instead, and the big flat faces are cut into cells about 4 cm across first so that a plate gets
the shade of the bolts and ribs standing on it.

Each part is baked ALONE: the parts come apart in the exploded view, so what a part gets is its own creases and cavities (the depth
of a slot, the gap between cells, a bolt's seat, the inside of a casing), which stay true however far the parts are drawn from each
other. The shade one part throws on another (the lid on the cells) is left out on purpose.

    ao.run()        # on the XR_ANATOMY collection: modifiers applied, big faces cut, rays cast, `_XRAO` written
"""
import math
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ATTR = "_XRAO"


def parts(collection="XR_ANATOMY"):
    col = bpy.data.collections[collection]
    return [o for o in col.objects if o.type == 'MESH' and len(o.data.polygons)]


def prepare(objs):
    """Apply every modifier (bevels, edge splits) so the baked surface is the exported one."""
    from ..export import bake_modifiers
    for o in objs:
        bake_modifiers(o)


def tessellate(ob, lmax=0.06, rounds=6, fat=0.02):
    """Cut the long edges of the BIG, FAT faces (a lid, a plate: 2 x area / perimeter above `fat`) until none is longer than `lmax`, so
    that a plate has vertices near the bolts and ribs standing on it. Thin strips (a rib, a rim) are left alone: they need no more."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for _ in range(rounds):
        edges = set()
        for f in bm.faces:
            per = f.calc_perimeter()
            if per > 1e-9 and 2.0 * f.calc_area() / per > fat:
                for e in f.edges:
                    if e.calc_length() > lmax:
                        edges.add(e)
        if not edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True, quad_corner_type='STRAIGHT_CUT')
    bm.to_mesh(me)
    bm.free()
    me.update()


def _dirs(k):
    """k cosine-weighted directions about +Z (a Fibonacci spiral)."""
    i = np.arange(k) + 0.5
    r = np.sqrt(i / k)
    a = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([r * np.cos(a), r * np.sin(a), np.sqrt(np.maximum(0.0, 1 - r * r))], -1)


def vertex_ao(ob, rays=24, near=0.022, far=0.22, mix=0.30, inset=0.45, seed=7):
    """Occlusion at every vertex of `ob` against the part itself: the share of `rays` cosine-weighted rays that hit it within `near`
    (creases, seats) and, weighted by `mix`, within `far` (cavities). 1 = open, 0 = shut."""
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nr = np.empty(n * 3, np.float64)
    me.vertices.foreach_get("normal", nr)
    nr = nr.reshape(-1, 3)
    # sample from a point moved `inset` of the way toward the centre of the vertex's own faces (along the surface): a vertex that sits
    # in a crease (the foot of a rib) would otherwise see only the wall beside it, and linear interpolation would spread that dark
    # across the whole groove floor
    nloop = len(me.loops)
    lv = np.empty(nloop, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_total", lt)
    cen = np.zeros((len(me.polygons), 3))
    pid = np.repeat(np.arange(len(me.polygons)), lt)
    np.add.at(cen, pid, co[lv])
    cen /= lt[:, None]
    acc = np.zeros((n, 3))
    cnt = np.zeros(n)
    np.add.at(acc, lv, cen[pid])
    np.add.at(cnt, lv, 1.0)
    cmean = acc / np.maximum(cnt, 1.0)[:, None]
    d = cmean - co
    d -= nr * (d * nr).sum(1, keepdims=True)
    cosamp = co + d * inset
    mw = np.array(ob.matrix_world)
    P = cosamp @ mw[:3, :3].T + mw[:3, 3]
    N = nr @ np.linalg.inv(mw[:3, :3]).T
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(ob.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    rng = np.random.default_rng(seed)
    base = _dirs(rays)
    # a tangent frame per vertex, turned by a random angle so the pattern does not band
    helper = np.where(np.abs(N[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
    T = np.cross(helper, N)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    B = np.cross(N, T)
    ang = rng.random(n) * 2 * np.pi
    ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
    T2 = T * ca + B * sa
    B2 = -T * sa + B * ca
    hit_near = np.zeros(n)
    hit_far = np.zeros(n)
    eps = 0.0008
    for (x, y, z) in base:
        D = T2 * x + B2 * y + N * z
        O = P + N * eps
        for i in range(n):
            res = bvh.ray_cast(Vector(O[i]), Vector(D[i]), far)
            d = res[3]
            if d is not None:
                if d < near:
                    hit_near[i] += 1.0
                hit_far[i] += 1.0
    near_o = 1.0 - hit_near / rays
    far_o = 1.0 - hit_far / rays
    return np.clip(near_o * (1.0 - mix + mix * far_o), 0.0, 1.0)


# the parts that are big plates with things standing on them: only these are cut finer (cells, busbars, extrusions and the like are not)
TESSELLATE = ("XR_Battery_Tray", "XR_Battery_Lid", "XR_Battery_Plate", "XR_Frame_SubF", "XR_Frame_SubR")


def run(rays=24, lmax=0.06, only=None):
    """The whole recipe on the XR_ANATOMY collection."""
    objs = parts()
    t0 = time.time()
    prepare(objs)
    n0 = sum(len(o.data.polygons) for o in objs)
    for o in objs:
        if only and o.name not in only:
            continue
        if o.name in TESSELLATE:
            tessellate(o, lmax)
    n1 = sum(len(o.data.polygons) for o in objs)
    print("ao: modifiers applied and big faces cut: %d -> %d faces (%.0fs)" % (n0, n1, time.time() - t0))
    allv = []
    for k, o in enumerate(objs):
        if only and o.name not in only:
            continue
        a = vertex_ao(o, rays)
        me = o.data
        at = me.attributes.get(ATTR) or me.attributes.new(ATTR, 'FLOAT', 'POINT')
        at.data.foreach_set("value", a.astype(np.float32))
        allv.append(a)
        if k % 10 == 0:
            print("ao: %d/%d  %s  verts %d  mean %.2f  (%.0fs)" % (k, len(objs), o.name, len(a), a.mean(), time.time() - t0))
    v = np.concatenate(allv)
    print("ao: %d vertices, mean %.3f  p5 %.3f  p50 %.3f  (%.0fs)" % (len(v), v.mean(), np.percentile(v, 5), np.percentile(v, 50), time.time() - t0))
