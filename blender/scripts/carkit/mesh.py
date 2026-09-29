"""Mesh construction and modifier helpers.

Conventions used by every builder in carkit:

* Parts are built on the car's LEFT half (+Y) and mirrored with a Mirror
  modifier (`mirror_y`), so the two sides cannot drift apart.
* A sheet is a grid of rows of points (`grid`, `mesh_from_rows`); its normals
  are set by an "outward" function of the face centre (`orient`, and the
  helpers in geom: away_from, axial, radial, const).
* Thickness, edge rounding and normals come from modifiers, in a fixed order:
  Solidify, then Bevel, then Weighted Normal (`finish`). Solidify never uses
  even offset - on anything folded it divides by a near-zero cosine and throws
  vertices metres off the car.
"""
import math

import bpy

SKIN = 0.0028                # default panel sheet thickness, metres


# ------------------------------------------------------------ construction
def obj(name, verts, faces, collection, mat, smooth=True):
    """A mesh object from raw vertex and face lists."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def mesh_from_rows(name, rows, collection, sharp_rows=()):
    """A quad sheet from rows of points (every row the same length).

    Carries a UV map in grid space. `sharp_rows` marks the edges along those
    column indices sharp, so Weighted Normal keeps a crease crisp instead of
    averaging it into a soft roll.
    """
    verts, faces = [], []
    nv = len(rows[0])
    for r in rows:
        verts.extend(r)
    for i in range(len(rows) - 1):
        a, b = i * nv, (i + 1) * nv
        for j in range(nv - 1):
            faces.append([a + j, a + j + 1, b + j + 1, b + j])

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    ni, nj = max(1, len(rows) - 1), max(1, nv - 1)
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi // nv) / float(ni), (vi % nv) / float(nj))
    if sharp_rows:
        want = set(sharp_rows)
        for e in me.edges:
            a, b = e.vertices
            if (a % nv) == (b % nv) and (a % nv) in want:
                e.use_edge_sharp = True
    me.validate(verbose=False)
    me.update()

    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def grid(name, rows, collection, mat, outward=None):
    """mesh_from_rows + orient + one material: the everyday sheet builder."""
    ob = mesh_from_rows(name, rows, collection)
    if outward is not None:
        orient(ob.data, outward)
    ob.data.materials.append(mat)
    return ob


def strip(name, a_pts, b_pts, collection, mat):
    """A quad strip between two matching polylines - return walls, seals."""
    ob = mesh_from_rows(name, [a_pts, b_pts], collection)
    ob.data.materials.append(mat)
    return ob


def merge_parts(parts):
    """Concatenate (verts, faces) pairs into one pair."""
    verts, faces = [], []
    for (v, f) in parts:
        base = len(verts)
        verts += v
        faces += [[i + base for i in face] for face in f]
    return verts, faces


def revolve(profile, segments, closed=True):
    """Revolve (r, d) pairs about local Z: d is the offset along the axis.

    Wheels are built like this in their own frame and placed with one matrix.
    """
    verts, faces = [], []
    n = len(profile)
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        for (r, d) in profile:
            verts.append((r * ca, r * sa, d))
    for i in range(segments if closed else segments - 1):
        j = (i + 1) % segments
        for k in range(n - 1):
            a0 = i * n + k
            b0 = j * n + k
            faces.append([a0, a0 + 1, b0 + 1, b0])
    return verts, faces


def text_mesh(name, body, size, collection, mat, extrude=0.0008, bold=False,
              italic=False, font=None, resolution=None, spacing=None, weight=0.0):
    """Lettering as a real mesh (a font curve converted), centred on its origin.

    Mesh, not a text object, so it exports to glTF. Place it with
    place.on_surface. Never mirror lettering: a Mirror modifier renders the
    other side's text back to front - build one object per side instead.

    resolution: curve resolution (Blender's default 12 is ~3x the triangles
    a badge 30 mm tall needs); spacing: letter-spacing factor, for wide-set
    wordmarks; weight: outline offset in metres, to embolden a regular face.
    """
    cu = bpy.data.curves.new(name + "_curve", 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.shear = 0.18 if italic else 0.0
    if font is not None:
        cu.font = font
    if resolution is not None:
        cu.resolution_u = resolution
    if spacing is not None:
        cu.space_character = spacing
    if weight:
        cu.offset = weight
    tob = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tob.evaluated_get(dg))
    bpy.data.objects.remove(tob, do_unlink=True)
    bpy.data.curves.remove(cu)
    # CFF/OpenType outlines (Noto Sans CJK) wind the other way from TrueType
    # and fill with their faces inside out: the glyphs shaded pale
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.name = name
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


# -------------------------------------------------------------- orientation
def orient(me, outward):
    """Flip the mesh if its area-weighted normals disagree with `outward(c)`."""
    score = 0.0
    for poly in me.polygons:
        d = outward(poly.center)
        if d is None:
            continue
        n = poly.normal
        score += poly.area * (n[0] * d[0] + n[1] * d[1] + n[2] * d[2])
    if score < 0.0:
        me.flip_normals()
        me.update()
    return me


def orient_revolved(ob, r_c, d_c):
    """Point a revolved surface's normals away from its profile's core ring.

    A tyre that came out with every normal pointing inward rendered, under a
    sheen lobe, as a whitewall.
    """
    me = ob.data
    score = 0.0
    for p in me.polygons:
        c = p.center
        a = math.atan2(c.y, c.x)
        core = (r_c * math.cos(a), r_c * math.sin(a), d_c)
        d = (c.x - core[0], c.y - core[1], c.z - core[2])
        score += p.area * (p.normal.x * d[0] + p.normal.y * d[1] + p.normal.z * d[2])
    if score < 0.0:
        me.flip_normals()
        me.update()
    return ob


# ---------------------------------------------------------------- modifiers
def mirror_y(ob, clip=True, merge=0.0008):
    """Mirror across the car's centre plane (XZ)."""
    m = ob.modifiers.new("Mirror", 'MIRROR')
    m.use_axis = (False, True, False)
    m.use_clip = clip
    m.merge_threshold = merge
    return ob


def solidify(ob, t, offset=-1.0):
    m = ob.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = t
    m.offset = offset
    m.use_even_offset = False
    return ob


def bevel(ob, width, segments=2, angle=40.0, harden=False):
    b = ob.modifiers.new("Bevel", 'BEVEL')
    b.width = width
    b.segments = segments
    b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(angle)
    if harden:
        try:
            b.harden_normals = True
        except Exception:
            pass
    return ob


def finish(ob, thickness=SKIN, bevel=0.0012, weighted=True):
    """Solidify, Bevel, then Weighted Normal - the panel stack. Order matters.

    Solidify runs WITHOUT even offset: even offset divides by the cosine of the
    angle between neighbouring faces, which is fine on a clean surface and
    explosive on anything folded (it threw a fender 150 mm off the SU7).
    """
    if thickness > 0.0:
        sol = ob.modifiers.new("Solidify", 'SOLIDIFY')
        sol.thickness = thickness
        sol.offset = -1.0
        sol.use_even_offset = False
        sol.use_quality_normals = True
    if bevel > 0.0:
        bev = ob.modifiers.new("Bevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
        bev.angle_limit = math.radians(40)
        bev.miter_outer = 'MITER_ARC'
        try:
            bev.harden_normals = True
        except Exception:
            pass
    if weighted:
        wn = ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
        wn.mode = 'FACE_AREA_WITH_ANGLE'
        wn.weight = 50
        wn.keep_sharp = True
        wn.thresh = 0.01
    return ob


def apply_modifiers(ob):
    """Bake the evaluated modifier stack into the object's mesh."""
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = baked
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


# ------------------------------------------------------------------ grids
def smooth_grid(rows, passes=3):
    """Laplacian-smooth the interior of a rows x cols grid of 3-tuples."""
    from mathutils import Vector
    g = [[Vector(p) for p in r] for r in rows]
    R, C = len(g), len(g[0])
    for _ in range(passes):
        h = [[v.copy() for v in r] for r in g]
        for i in range(1, R - 1):
            for j in range(1, C - 1):
                avg = (g[i - 1][j] + g[i + 1][j] + g[i][j - 1] + g[i][j + 1]) * 0.25
                h[i][j] = g[i][j] * 0.5 + avg * 0.5
        g = h
    return [[tuple(v) for v in r] for r in g]


# ---------------------------------------------------------------- measuring
def tri_count(objs):
    """Evaluated triangle count (after every modifier) of a list of objects."""
    total = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return total
