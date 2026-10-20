"""Cabin parts shared by the Denza Z9 and XPeng G9L interiors (and any car built on carkit.interior):
a puffed headrest, a seat shroud, a rear-view mirror, pedals, an image-as-pixels helper and the
generic closing trims. Pure functions of their arguments: no car's surface module is imported here.
"""
import math

import bpy
from mathutils import Vector

from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


POLE = 0.04          # a pillow's pole ring, as a fraction of its rim


def pillow(col, name, c, w, h, t, r, mat, tilt, n_in=6):
    """A puffed rounded-rectangle cushion (a headrest) centred at c, facing +x tilted by `tilt`
    (negative: its face looks up as the seat reclines): rings from a small pole ring out to the rim
    and back, each pole closed by a polygon."""
    loop = F.round_rect_xy(-w / 2, w / 2, -h / 2, h / 2, r)
    ct, st = math.cos(tilt), math.sin(tilt)

    def ring(s, d):
        return [(c[0] + d * ct + v * s * st, c[1] - u * s, c[2] - d * st + v * s * ct)
                for (u, v) in loop]
    half = 0.5 * t
    rings = []
    for k in range(n_in + 1):                       # front: centre -> rim
        s = k / float(n_in)
        rings.append(ring(s, half * (0.62 + 0.38 * (1.0 - s * s))))
    rings[0] = ring(POLE, half * (0.62 + 0.38 * (1.0 - POLE * POLE)))      # a tiny ring, closed below by a polygon
    rings.append(ring(1.012, 0.20 * half))
    rings.append(ring(1.016, 0.0))
    rings.append(ring(1.012, -0.20 * half))
    for k in range(n_in + 1):                       # back: rim -> centre
        s = 1.0 - k / float(n_in)
        rings.append(ring(s, -half * (0.62 + 0.38 * (1.0 - s * s))))
    rings[-1] = ring(POLE, -half * (0.62 + 0.38 * (1.0 - POLE * POLE)))
    ob = grid_mesh(name, rings, col, mat, wrap_t=True)
    # the two poles are polygons, not points: a point makes a fan of zero-area quads whose tangents are undefined, and the
    # normal map there drew a smooth, dot-free square on the back of every headrest
    import bmesh
    n = len(loop)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    last = len(bm.verts) - n
    bm.faces.new([bm.verts[j] for j in reversed(range(n))])
    bm.faces.new([bm.verts[last + j] for j in range(n)])
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda q: (q[0] - c[0], q[1] - c[1], q[2] - c[2]))
    return ob


def headrest(col, lib, spec, origin, name, role="leather_seat", post_role="piano", recline=22.0):
    """A seat's separate headrest: the pillow, two posts to the backrest. `spec["headrest"]` is in
    seat-local coordinates (x back negative, z up from the bight)."""
    hr = spec["headrest"]
    xt, zt = hr["top"]
    rec = math.radians(recline)
    dz = hr["gap"] + 0.5 * hr["h"]
    cx, cz = xt - dz * math.tan(rec), zt + dz
    c = (origin[0] + cx, origin[1], origin[2] + cz)
    made = [pillow(col, name + "_Head", c, hr["w"], hr["h"], hr["t"], hr["r"], lib[role], -rec)]
    for k, sy in enumerate((-1.0, 1.0)):
        z0 = zt - 0.03
        z1 = cz - 0.5 * hr["h"] + 0.03
        q = (origin[0] + xt - 0.5 * (z1 + z0 - 2 * zt) * math.tan(rec) - 0.005,
             origin[1] + sy * 0.060, origin[2] + 0.5 * (z0 + z1))
        made.append(F.box(col, "%s_Post%d" % (name, k), q, (0.014, 0.014, z1 - z0), lib[post_role],
                          r=0.004, pitch=rec))
    return made


def seat_shroud(col, lib, origin, name, floor_z, role="leather_seat"):
    """The shroud and rails under a front cushion, with its oval switch panel on the door side."""
    x0, y0, z0 = origin
    made = [F.box(col, name, (x0 + 0.25, y0, 0.5 * (floor_z + z0 - 0.07)),
                  (0.56, 0.42, z0 - 0.07 - floor_z), lib[role], r=0.04)]
    side = 1.0 if y0 > 0 else -1.0
    made.append(F.box(col, name + "_sw", (x0 + 0.20, y0 + side * 0.212, z0 - 0.055),
                      (0.130, 0.012, 0.045), lib["piano"], r=0.014))
    return made


def pedals(col, lib, floor_z, specs, tilt_deg=38.0):
    """Each pedal a metal pad on its arm: specs = [(name, y, x, z, w, h, strips)], strips of rubber
    across the pad ("rest" gets vertical slots instead)."""
    made = []
    p = math.radians(tilt_deg)
    a = Vector((math.sin(p), 0.0, math.cos(p)))
    n = Vector((-math.cos(p), 0.0, math.sin(p)))
    for name, y, x, z, w, h, strips in specs:
        c = Vector((x, y, z))
        made.append(F.box(col, "int_pedal_" + name, tuple(c), (0.010, w, h), lib["brushed"],
                          r=0.003, pitch=p))
        if name == "rest":
            for k in range(strips):
                q = c + n * 0.006 + Vector((0.0, (k - 2) * w * 0.18, 0.0))
                made.append(F.box(col, "int_pedal_%s_slot%d" % (name, k), tuple(q),
                                  (0.004, 0.006, h * 0.85), lib["rubber"], r=0.0015, pitch=p))
        else:
            for k in range(strips):
                q = c + n * 0.006 + a * ((k - 1) * h * 0.28)
                made.append(F.box(col, "int_pedal_%s_strip%d" % (name, k), tuple(q),
                                  (0.004, w * 0.82, 0.008), lib["rubber"], r=0.0015, pitch=p))
    return made


def rear_view_mirror(col, lib, centre, zg, w=0.250, h=0.062, t=0.016):
    """The frameless rear-view mirror hung from the header on a short stem."""
    made = [F.round_slab(col, "int_rvmirror", centre, w, h, t, 0.024, lib["piano"],
                         tilt=math.radians(8.0))]
    mg = bpy.data.materials.get("INT_Mirror") or bpy.data.materials.new("INT_Mirror")
    mg.use_nodes = True
    bm = next(n for n in mg.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bm.inputs["Base Color"].default_value = (0.30, 0.31, 0.32, 1.0)
    bm.inputs["Metallic"].default_value = 1.0
    bm.inputs["Roughness"].default_value = 0.05
    made.append(F.round_slab(col, "int_rvmirror_glass", (centre[0] - t * 0.5 - 0.0008, 0.0, centre[2]),
                             w - 0.006, h - 0.006, 0.0008, 0.021, mg, tilt=math.radians(8.0)))
    stem = smooth_path([(centre[0] + 0.02, 0.0, centre[2] + 0.02),
                        (centre[0] + 0.045, 0.0, 0.5 * (centre[2] + zg) + 0.01),
                        (centre[0] + 0.07, 0.0, zg)], 8)
    made.append(tube("int_rvmirror_stem", stem, ellipse(0.016, 0.010, 10), col, lib["satin"],
                     lateral=(0.0, 1.0, 0.0)))
    return made


def image_from_pixels(name, rgb, path):
    """Write a float RGB array (h, w, 3), top row first, as a PNG Blender image (used for the
    cluster and passenger displays' resting pictures)."""
    import numpy as np
    h, w = rgb.shape[:2]
    im = bpy.data.images.get(name) or bpy.data.images.new(name, w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = rgb[::-1]
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    return path
