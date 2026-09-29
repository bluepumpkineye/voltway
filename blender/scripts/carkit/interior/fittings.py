"""Small cabin parts every car needs: rounded boxes and slabs, the screen quad
(the web app's HMI anchor), flat plates with holes, round grilles, and the
render rig.

    box(col, name, centre, size, mat, r, pitch)       a bevelled block
    slab(name, centre, w, h, depth, r, tilt, col, mat) a rounded display slab
    screen_quad(name, centre, w, h, tilt, col)        ONE flat quad, planar UV
    screen_material()                                 INT_Screen
    round_rect_xy / shrink / inside / plate_with_hole  2D outlines and plates
    round_slab(col, name, c, w, h, t, r, mat, tilt)    a thin rounded slab
    disc(col, name, centre, normal, r, mat, ...)       a round grille or cap
    lights(col, specs)                                 area lights, camera-invisible

Slabs and quads face -X (toward the occupants) and lean back by `tilt` (the
top further forward); u runs to the viewer's right (world -Y).
"""
import math

import bpy
from mathutils import Vector

from .. import mesh as M
from .sweep import grid_mesh


def box(col, name, c, size, mat, r=0.01, pitch=0.0, yaw=0.0):
    """A bevelled block centred at c, size (dx, dy, dz), pitched about Y
    (positive pitch tips its +X end down) and yawed about Z."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    verts = []
    for (x, y, z) in pts:
        x, z = x * cp + z * sp, -x * sp + z * cp
        x, y = x * cy - y * sy, x * sy + y * cy
        verts.append((c[0] + x, c[1] + y, c[2] + z))
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    if r > 0:
        M.bevel(ob, r, 3, 40)
    return ob


def round_rect_xy(x0, x1, y0, y1, r, n=6):
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0.0), (x0 + r, y1 - r, 0.5 * math.pi),
                       (x0 + r, y0 + r, math.pi), (x1 - r, y0 + r, 1.5 * math.pi)):
        for k in range(n + 1):
            a = a0 + 0.5 * math.pi * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def shrink(loop, k):
    cx = sum(p[0] for p in loop) / len(loop)
    cy = sum(p[1] for p in loop) / len(loop)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for (x, y) in loop]


def inside(p, loop):
    """Point-in-polygon (even-odd) for a 2D loop."""
    x, y = p
    c = False
    n = len(loop)
    for i in range(n):
        (x1, y1), (x2, y2) = loop[i], loop[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def plate_with_hole(name, outer, holes, z_fn, col, mat, nx=120, ny=64, normal=(0.0, 0.0, 1.0)):
    """A plate inside `outer` with `holes` removed: a fine grid keeping the
    faces whose centre is inside the outline and outside every hole. The
    ragged edges (< 3 mm) sit under frames and rims. z_fn(x, y) -> height,
    or a number."""
    import bmesh
    if holes and isinstance(holes[0][0], (int, float)):
        holes = [holes]
    zf = z_fn if callable(z_fn) else (lambda x, y, _z=z_fn: _z)
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    verts = []
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            verts.append((x, y, zf(x, y)))
    faces = []
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (x1 - x0) * (i + 0.5) / nx
            cy = y0 + (y1 - y0) * (j + 0.5) / ny
            if inside((cx, cy), outer) and not any(inside((cx, cy), h) for h in holes):
                a = i * (ny + 1) + j
                faces.append([a, a + ny + 1, a + ny + 2, a + 1])
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: normal)
    return ob


def slab(name, centre, w, h, depth, r, tilt, col, mat, nseg=6, bevel=0.003):
    """A rounded-rectangle slab facing -X (toward the occupants), leaning
    back by `tilt` (top further forward)."""
    loop = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0.0), (-w / 2 + r, h / 2 - r, 0.5 * math.pi),
                       (-w / 2 + r, -h / 2 + r, math.pi), (w / 2 - r, -h / 2 + r, 1.5 * math.pi)):
        for k in range(nseg + 1):
            a = a0 + 0.5 * math.pi * k / nseg
            loop.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    n = len(loop)
    ct, st = math.cos(tilt), math.sin(tilt)

    def P(u, v, d):
        x = d * ct + v * st
        z = -d * st + v * ct
        return (centre[0] + x, centre[1] - u, centre[2] + z)
    verts = [P(u, v, 0.0) for (u, v) in loop] + [P(u, v, depth) for (u, v) in loop]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda c: (c[0] - centre[0] - 0.5 * depth, 0.0, 0.0))
    if bevel:
        M.bevel(ob, min(bevel, depth * 0.3), 3, 30)
    return ob


def screen_quad(name, centre, w, h, tilt, col, lift=0.0006, facing_y=0.0):
    """A display: ONE flat quad with a planar UV, facing the occupants
    (-X), leaning back by `tilt`. `screen_main` is a contract with the web
    app (the live HMI is mounted on it): name, size and facing."""
    ct, st = math.cos(tilt), math.sin(tilt)

    def P(u, v):
        x = -lift * ct + v * st
        z = lift * st + v * ct
        return (centre[0] + x, centre[1] - u, centre[2] + z)
    verts = [P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2, h / 2)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [[0, 1, 2, 3]])
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for i, co in enumerate([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        uv.data[i].uv = co
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    M.orient(ob.data, lambda c: (-1.0, 0.0, 0.0))
    return ob


def screen_material():
    m = bpy.data.materials.get("INT_Screen") or bpy.data.materials.new("INT_Screen")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (0.004, 0.006, 0.010, 1.0)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Emission Color"].default_value = (0.10, 0.16, 0.30, 1.0)
    b.inputs["Emission Strength"].default_value = 0.6
    return m


def round_slab(col, name, c, w, h, t, r, mat, tilt=0.0):
    """A thin rounded slab (mirror, badge) facing -X."""
    loop = round_rect_xy(-w / 2, w / 2, -h / 2, h / 2, r)
    ct, st = math.cos(tilt), math.sin(tilt)
    verts = []
    for d in (-t / 2, t / 2):
        for (u, v) in loop:
            verts.append((c[0] + d * ct + v * st, c[1] - u, c[2] - d * st + v * ct))
    n = len(loop)
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda q: (q[0] - c[0], 0.0, 0.0))
    return ob


def disc(col, name, centre, normal, r, mat, dome=0.0, rings=5, n=32, rim=None, rim_mat=None):
    """A round cap or grille facing `normal`, optionally domed and with a
    rim tube (r, profile radius) in rim_mat."""
    from .sweep import tube, ellipse
    N = Vector(normal).normalized()
    e1 = N.orthogonal().normalized()
    e2 = N.cross(e1).normalized()
    C = Vector(centre)
    rows = []
    for k in range(rings + 1):
        s = 1.0 - k / float(rings)
        h = dome * (1.0 - s * s)
        rows.append([tuple(C + (e1 * math.cos(2 * math.pi * j / n) + e2 * math.sin(2 * math.pi * j / n))
                           * (r * max(s, 1e-4)) + N * h) for j in range(n)])
    ob = grid_mesh(name, rows, col, mat, wrap_t=True)
    M.orient(ob.data, lambda c: tuple(N))
    made = [ob]
    if rim:
        path = [tuple(C + (e1 * math.cos(2 * math.pi * j / n) + e2 * math.sin(2 * math.pi * j / n)) * r)
                for j in range(n)]
        path.append(path[0])
        made.append(tube(name + "_Rim", path, ellipse(rim, rim, 8), col, rim_mat or mat,
                         lateral=tuple(N)))
    return made


def ngon_cap(col, name, pts, mat, normal):
    """A flat cap over a closed outline of 3D points (a section's end),
    ear-clip triangulated, facing `normal`."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    M.orient(ob.data, lambda c: tuple(normal))
    return ob


def lights(col, specs):
    """Area lights for renders: (name, location, aim, (w, h), power, colour,
    glossy). Invisible to the camera; glossy=False keeps a light out of
    mirrors and screens (a light behind the viewer read as a white card)."""
    made = []
    for name, loc, aim, size, power, colour, glossy in specs:
        d = bpy.data.lights.new(name, 'AREA')
        d.shape = 'RECTANGLE'
        d.size, d.size_y = size
        d.energy = power
        d.color = colour
        ob = bpy.data.objects.new(name, d)
        col.objects.link(ob)
        ob.location = loc
        v = Vector(aim) - Vector(loc)
        ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
        ob.visible_camera = False
        ob.visible_glossy = glossy
        made.append(ob)
    return made
