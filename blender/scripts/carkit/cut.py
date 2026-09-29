"""Openings: cutting prisms and exact booleans.

Rule from the SU7 build: an opening whose edge does not follow the panel's own
grid lines - a wheel arch, a quarter light, a vent slot, an intake - is CUT
with an exact boolean on the HALF sheet, before the Mirror modifier. Trimming
it in the grid instead leaves the columns either side of the opening with
different row spacings, and the sheared quads show as a line across the panel;
cutting after the mirror only ever cuts one side.

A cutter is a closed prism swept from an outline:

    prism_y    side-elevation (x, z) outline swept across the car
    prism_x    front-elevation (y, z) outline swept along the car
    prism_dir  any 3D loop swept along a direction (e.g. a surface normal)
    slot       a thin tube swept along a 3D path over a curved surface: a
               shut line that turns a corner (a decklid's edge running down
               a tail and over onto the deck)
"""
import math

import bpy

from . import mesh as M


def _prism(name, verts, n, centre):
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(n, 2 * n)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # make the prism's normals point outward, whatever the outline's winding
    M.orient(me, lambda c: (c[0] - centre[0], c[1] - centre[1], c[2] - centre[2]))
    return ob


def prism_y(name, outline_xz, y0, y1):
    """Sweep a side-elevation outline along Y into a closed cutting prism."""
    n = len(outline_xz)
    verts = [(x, y0, z) for (x, z) in outline_xz] + [(x, y1, z) for (x, z) in outline_xz]
    cx = sum(p[0] for p in outline_xz) / n
    cz = sum(p[1] for p in outline_xz) / n
    cy = 0.5 * (y0 + y1)
    return _prism(name, verts, n, (cx, cy, cz))


def prism_x(name, outline_yz, x_front, x_back):
    """Sweep a front-elevation outline along X into a closed cutting prism."""
    n = len(outline_yz)
    verts = [(x_front, y, z) for (y, z) in outline_yz]
    verts += [(x_back, y, z) for (y, z) in outline_yz]
    cx = 0.5 * (x_front + x_back)
    cy = sum(p[0] for p in outline_yz) / n
    cz = sum(p[1] for p in outline_yz) / n
    return _prism(name, verts, n, (cx, cy, cz))


def prism_dir(name, loop, d, back=0.25, front=0.25):
    """Sweep a 3D loop along direction d (front ahead of it, back behind it)."""
    n = len(loop)
    verts = [(p[0] + d[0] * front, p[1] + d[1] * front, p[2] + d[2] * front) for p in loop]
    verts += [(p[0] - d[0] * back, p[1] - d[1] * back, p[2] - d[2] * back) for p in loop]
    c = tuple(sum(v[k] for v in verts) / len(verts) for k in range(3))
    return _prism(name, verts, n, c)


def slot(name, path, normals, width, out=0.02, inside=0.02):
    """A closed tube of rectangular section swept along a 3D polyline: the
    cutter for a shut line that follows a curved surface (a decklid's edge
    running down a tail face and over onto the deck), where no single sweep
    direction suits a prism.

    normals[i] is the surface normal at path[i]; the slot is `width` wide
    across the path in the surface and reaches `out` above and `inside` below
    it.
    """
    import bmesh
    from mathutils import Vector
    n = len(path)
    P = [Vector(p) for p in path]
    verts = []
    for i in range(n):
        t = (P[min(n - 1, i + 1)] - P[max(0, i - 1)]).normalized()
        nv = Vector(normals[i]).normalized()
        b = nv.cross(t).normalized() * (0.5 * width)
        for s_b, s_n in ((1, out), (-1, out), (-1, -inside), (1, -inside)):
            verts.append(tuple(P[i] + b * s_b + nv * s_n))
    faces = []
    for i in range(n - 1):
        a, c = 4 * i, 4 * (i + 1)
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append([a + k, c + k, c + k2, a + k2])
    faces.append([3, 2, 1, 0])
    e = 4 * (n - 1)
    faces.append([e, e + 1, e + 2, e + 3])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def difference(ob, cutters, modifier_prefix="cut_", reset_materials=False):
    """Boolean every cutter out of `ob` (EXACT, hole tolerant), apply, clean up.

    Returns (faces before, faces after). The cutters are deleted.

    reset_materials: an applied boolean on a sheet that had no material yet
    leaves an empty slot at index 0 that every face points at - the material
    appended afterwards lands in slot 1 and the panel renders white. Pass True
    whenever the sheet's material is added after the cut.
    """
    if not cutters:
        return len(ob.data.polygons), len(ob.data.polygons)
    for c in cutters:
        b = ob.modifiers.new(modifier_prefix + c.name, 'BOOLEAN')
        b.operation = 'DIFFERENCE'
        b.solver = 'EXACT'
        try:
            b.use_hole_tolerant = True
        except Exception:
            pass
        b.object = c
    before = len(ob.data.polygons)
    M.apply_modifiers(ob)
    weld(ob)
    after = len(ob.data.polygons)
    for c in cutters:
        d = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    if reset_materials:
        ob.data.materials.clear()
        for p in ob.data.polygons:
            p.material_index = 0
    return before, after


def weld(ob, dist=2e-4):
    """Merge vertices closer than `dist` and dissolve the degenerate edges and
    faces an EXACT boolean leaves where a cutter grazes a vertex. A Bevel
    modifier later in the stack turns such a sliver into vertices at 1e30 m:
    the RX's front fender threw streaks four metres ahead of the car.
    Returns the number of vertices removed."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
    removed = n - len(bm.verts)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return removed


def sheet_bvh(ob):
    """A BVH of an open sheet as it is now - take it BEFORE cutting."""
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromPolygons([v.co.copy() for v in ob.data.vertices],
                                [list(p.vertices) for p in ob.data.polygons])


def prune_off_sheet(ob, bvh, tol=0.003):
    """Delete faces that do not lie on the original sheet.

    An open panel cut with hole-tolerant EXACT booleans keeps pieces of the
    cutter it considers "inside" - for the SU7's quarter light, the prism's
    lower wall: a painted shelf from the skin in to y 0.30, hidden from
    outside but a paint sheet from the rear seats (found with
    carkit.qa.leaks). Returns the number of faces removed.
    """
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    dead = []
    for f in bm.faces:
        c = f.calc_center_median()
        hit = bvh.find_nearest(c)
        if hit[0] is None or hit[3] > tol:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return len(dead)


# ------------------------------------------------------------- wheel arches
ARCH_OPEN = 0.0021            # half a shut line outside the modelled arch


def arch_outline(axle, arch_r, wheel_r, open_=ARCH_OPEN, seg=72, floor=-0.05):
    """Wheel opening in side elevation: the arch, then straight down past the
    floor - the lip runs vertically into the sill, as on most cars."""
    r = arch_r + open_
    pts = [(axle + r, floor)]
    for i in range(seg + 1):
        a = math.pi * i / seg
        pts.append((axle + r * math.cos(a), wheel_r + r * math.sin(a)))
    pts.append((axle - r, floor))
    return pts


def cut_arches(ob, body, y0=0.35, y1=1.40, open_=ARCH_OPEN):
    """Boolean both wheel openings through a flank half-sheet (before mirror).

    `body` supplies FRONT_AXLE, REAR_AXLE, ARCH_R and WHEEL_R. Only the
    openings that overlap the sheet are cut. Returns the number cut.
    """
    xs = [v.co.x for v in ob.data.vertices]
    lo, hi = min(xs), max(xs)
    cutters = []
    for axle in (body.FRONT_AXLE, body.REAR_AXLE):
        r = body.ARCH_R + open_
        if axle + r < lo or axle - r > hi:
            continue
        cutters.append(prism_y("_arch_%s_%.2f" % (ob.name, axle),
                               arch_outline(axle, body.ARCH_R, body.WHEEL_R, open_),
                               y0, y1))
    if cutters:
        difference(ob, cutters, "arch_", reset_materials=True)
    return len(cutters)
