"""Build plumbing shared by every car: collections, reloads, UVs, the checks.

A car's build script (build_su7.py is the reference) does:

    carkit.build.reload(["su7_surface", ...])   # fresh modules, fresh caches
    body = fresh_collection("SU7_Body") ...     # one collection per group
    lib = materials.build_library(...)
    <car>.panels / front / rear / side / wheels .build_all(...)
    scene.main()
    ensure_uvs([...]); report(...)              # UVs, envelope, budget
"""
import sys

import bpy

from .qa import checks


def reload(module_names):
    """Drop the car's modules AND carkit from sys.modules.

    Blender keeps modules loaded between runs, and the surface caches live in
    them - a stale module silently builds yesterday's car.
    """
    for m in module_names:
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)


def fresh_collection(name):
    """An empty collection called `name`, linked to the scene."""
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def ensure_uvs(collections, scale=1.0, force=("M_Carbon",)):
    """Cube-project world-space UVs onto every mesh built without them.

    Parts made straight from vertex lists have no UV layer, so a texture
    samples one texel (the carbon read flat black) and glTF has nothing to map.
    World-space projection along each face's dominant axis keeps the texel
    size the same on every part - a 3 mm twill is 3 mm everywhere.
    """
    import bmesh
    n = 0
    for c in collections:
        for o in c.objects:
            if o.type != 'MESH':
                continue
            forced = any(m and m.name in force for m in o.data.materials)
            if len(o.data.uv_layers) and not forced:
                continue
            me = o.data
            for layer in list(me.uv_layers):
                me.uv_layers.remove(layer)
            bm = bmesh.new()
            bm.from_mesh(me)
            uv = bm.loops.layers.uv.new("UVMap")
            mw = o.matrix_world
            for f in bm.faces:
                nrm = f.normal
                ax = max(range(3), key=lambda i: abs(nrm[i]))
                for loop in f.loops:
                    p = mw @ loop.vert.co
                    if ax == 0:
                        loop[uv].uv = (p.y * scale, p.z * scale)
                    elif ax == 1:
                        loop[uv].uv = (p.x * scale, p.z * scale)
                    else:
                        loop[uv].uv = (p.x * scale, p.y * scale)
            bm.to_mesh(me)
            bm.free()
            n += 1
    print("uvs: cube-projected on %d meshes" % n)
    return n


def report(collections, loft, interior=None, allowance=0.012):
    """The standard post-build checks. Prints warnings; returns a dict."""
    out = {}
    bad = checks.envelope(collections, loft.HALF_L, loft.HALF_W)
    if bad:
        print("WARNING - geometry outside the car's envelope:")
        for b in bad:
            print("   ", b)
    out["envelope"] = bad
    if interior:
        through = checks.cabin_clearance(loft, interior, allowance)
        if through:
            print("WARNING - interior parts through the body skin (m past allowance):")
            for b in through:
                print("   ", b)
        out["clearance"] = through
    return out
