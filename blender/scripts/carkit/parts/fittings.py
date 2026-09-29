"""Fittings and trim: mirrors, handles, vents, rings, badges, plates, stripes.

Surface-bound pieces take a placement function:

    proud(p, d)      -> ((x, y, z), normal)  nearest-point, d proud
                        (CarBody.proud) - for flank and hood trim
    side_point(x, z) -> ((x, y, z), normal)  analytic side elevation
                        (CarBody.side_point) - for patches across a corner
    place(p, d)      -> ((x, y, z), normal)  anything, e.g. Placer.radial

    mirror_head     teardrop wing mirror: head, glass, chunky stalk
    mirror_cap      wing mirror with a big rear glass face, a tapered nose and
                    a two-tone housing (painted cap over a black underside)
    flush_handle    a flush door handle blade with rounded ends
    flank_patch     a strip between two side-elevation edge lines
    vent            frame + dark opening + one slat (fender vents)
    outline_ring    a thin dark shut-line ring (charge flap, fuel door)
    side_patch      a patch placed with side_point (intakes round a corner)
    surface_band    a decal strip bounded by two height curves (side stripes)
    centre_stripes  racing stripes along a path over the car's centreline
    lidar_pod       a roof lidar bump
    rounded_panel   a rounded rectangle laid on a surface (plate recesses)
    text_badge      lettering placed on the surface (never mirrored)
    plate           a plate with lettering on it
"""
import math

from mathutils import Vector

from .. import geom
from .. import mesh as M
from .. import place as P


# ------------------------------------------------------------------ mirrors
def mirror_head(prefix, collection, lib, centre, size, stalk_base, proud,
                nu=20, nv=12, stalk_t=0.019, mats=("carbon", "chrome", "black_gloss")):
    """A teardrop head (blunt front, tapering rear face) on a short chunky arm.

    centre/size: head centre and (length, width, height). stalk_base: a point
    near the door skin where the arm starts. Returns [head, glass, stalk].
    A thin 20 mm stalk read as an insect antenna from the front - keep it short.
    """
    made = []
    cx, cy, cz = centre
    lx, ly, lz = size
    verts, faces = [], []
    for i in range(nu + 1):
        u = math.pi * i / nu                 # 0 = front of head, pi = rear
        for j in range(nv):
            a = 2 * math.pi * j / nv
            sx = -math.cos(u) * lx * 0.5
            taper = 0.55 + 0.45 * math.sin(u) ** 0.6
            sy = math.sin(u) * math.cos(a) * ly * 0.5 * taper
            sz = math.sin(u) * math.sin(a) * lz * 0.5 * taper
            verts.append((cx + sx, cy + sy, cz + sz))
    for i in range(nu):
        for j in range(nv):
            a0 = i * nv + j
            a1 = i * nv + (j + 1) % nv
            b0 = (i + 1) * nv + j
            b1 = (i + 1) * nv + (j + 1) % nv
            faces.append([a0, a1, b1, b0])
    head = M.obj(prefix + "_Head", verts, faces, collection, lib[mats[0]])
    M.orient(head.data, geom.away_from((cx, cy, cz)))
    M.mirror_y(head)
    made.append(head)

    g = []
    for j in range(16):
        a = 2 * math.pi * j / 16
        g.append((cx - lx * 0.47, cy + math.cos(a) * ly * 0.40,
                  cz + math.sin(a) * lz * 0.40))
    gv = [(cx - lx * 0.47, cy, cz)] + g
    gf = [[0, 1 + j, 1 + (j + 1) % 16] for j in range(16)]
    glass = M.obj(prefix + "_Glass", gv, gf, collection, lib[mats[1]])
    M.orient(glass.data, lambda c: (-1.0, 0.0, 0.0))
    M.mirror_y(glass)
    made.append(glass)

    base, n = proud(stalk_base, 0.0)
    top = (cx + 0.01, cy - 0.030, cz - lz * 0.25)
    t = stalk_t
    prof = [(base[0] + 0.035, base[2]), (top[0] + 0.030, top[2]),
            (top[0] - 0.030, top[2]), (base[0] - 0.045, base[2])]
    verts = []
    for (x, z), y in zip(prof, (base[1], top[1], top[1], base[1])):
        verts.append((x, y - t, z))
    for (x, z), y in zip(prof, (base[1], top[1], top[1], base[1])):
        verts.append((x, y + t, z))
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2],
             [2, 6, 7, 3], [3, 7, 4, 0]]
    stalk = M.obj(prefix + "_Stalk", verts, faces, collection, lib[mats[2]], smooth=False)
    M.bevel(stalk, 0.004, 2)
    M.mirror_y(stalk)
    made.append(stalk)
    return made


def mirror_cap(prefix, collection, lib, rear, size, arm_base, proud, nx=22, nr=24,
               nose=0.22, drop=0.30, split=-0.18, arm_t=0.016,
               mats=("paint", "mirror_glass", "black_gloss", "black_gloss")):
    """A wing mirror whose rear face is the glass: the housing is a sweep of
    rounded sections from the glass rim forward to a tapered nose.

    rear: centre of the glass face (x, y, z); size: (depth along x, width
    along y, height). nose: the front section's size as a fraction of the
    full one. drop: how far the nose sits below the rear's centre, as a
    fraction of the height (side view: a flat underside and a crown rising
    to the glass). split: height (fraction of the half height, from the
    centre) below which the housing takes mats[3] - a black underside under
    a painted cap. arm_base: a point near the door skin; a slim arm runs
    from there to the housing's inboard underside.
    Returns [housing, glass, arm], left side, mirrored.
    """
    made = []
    rx, ry, rz = rear
    lx, ly, lz = size
    verts, faces, fmat = [], [], []

    def section(t):
        """(half width, half height, z offset) at t: 0 = glass rim, 1 = nose."""
        if t < 0.10:                       # the rim rounds forward off the glass
            k = 0.94 + 0.06 * math.sin(0.5 * math.pi * t / 0.10)
        else:
            q = (t - 0.10) / 0.90
            k = 1.0 - (1.0 - nose) * q ** 1.7
        return 0.5 * ly * k, 0.5 * lz * k, -drop * lz * (t ** 1.4)

    for i in range(nx + 1):
        t = i / float(nx)
        hy, hz, dz = section(t)
        x = rx + lx * t
        for j in range(nr):
            a = 2.0 * math.pi * j / nr
            c, s_ = math.cos(a), math.sin(a)
            # a squarer section with a flatter underside
            e = 0.65
            sy = math.copysign(abs(c) ** e, c)
            sz = math.copysign(abs(s_) ** e, s_) * (1.0 if s_ > 0 else 0.80)
            verts.append((x, ry + hy * sy, rz + dz + hz * sz))
    for i in range(nx):
        for j in range(nr):
            a0, a1 = i * nr + j, i * nr + (j + 1) % nr
            b0, b1 = (i + 1) * nr + j, (i + 1) * nr + (j + 1) % nr
            faces.append([a0, a1, b1, b0])
            zc = 0.25 * sum(verts[k][2] for k in (a0, a1, b0, b1)) - rz
            fmat.append(0 if zc > split * 0.5 * lz else 1)
    tip = len(verts)
    hy, hz, dz = section(1.0)
    verts.append((rx + lx + 0.35 * nose * lx, ry, rz + dz))
    for j in range(nr):
        faces.append([nx * nr + j, nx * nr + (j + 1) % nr, tip])
        fmat.append(1 if j >= nr // 2 else 0)
    head = M.obj(prefix + "_Head", verts, faces, collection, lib[mats[0]])
    head.data.materials.append(lib[mats[3]])
    for poly, mi in zip(head.data.polygons, fmat):
        poly.material_index = mi
    M.orient(head.data, geom.away_from((rx + 0.5 * lx, ry, rz)))
    M.mirror_y(head)
    made.append(head)

    # the glass: flat, just inside the rim, facing aft
    g = [(rx + 0.004, ry, rz)]
    for j in range(nr):
        a = 2.0 * math.pi * j / nr
        c, s_ = math.cos(a), math.sin(a)
        sy = math.copysign(abs(c) ** 0.65, c)
        sz = math.copysign(abs(s_) ** 0.65, s_) * (1.0 if s_ > 0 else 0.80)
        g.append((rx + 0.004, ry + 0.43 * ly * sy, rz + 0.43 * lz * sz))
    gf = [[0, 1 + j, 1 + (j + 1) % nr] for j in range(nr)]
    glass = M.obj(prefix + "_Glass", g, gf, collection, lib[mats[1]])
    M.orient(glass.data, lambda c: (-1.0, 0.0, 0.0))
    M.mirror_y(glass)
    made.append(glass)

    # the arm: a slim blade from the door up to the housing's inboard underside
    base, _n = proud(arm_base, 0.0)
    top = (rx + 0.45 * lx, ry - 0.28 * ly, rz - 0.30 * lz)
    t = arm_t
    prof = [(base[0] + 0.030, base[2]), (top[0] + 0.035, top[2]),
            (top[0] - 0.035, top[2]), (base[0] - 0.035, base[2])]
    ys = (base[1], top[1], top[1], base[1])
    av = [(x, y - t, z) for (x, z), y in zip(prof, ys)] + [(x, y + t, z) for (x, z), y in zip(prof, ys)]
    af = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
    arm = M.obj(prefix + "_Stalk", av, af, collection, lib[mats[2]], smooth=False)
    M.bevel(arm, 0.004, 2)
    M.mirror_y(arm)
    made.append(arm)
    return made


# ------------------------------------------------------------------ handles
def flush_handle(name, x0, x1, zc, proud, collection, mat, h=0.016, n=16,
                 d=0.0008, y_ref=0.95, outward=(0.0, 1.0, 0.0)):
    """A flush handle: a blade from x0 to x1 at height zc, rounded ends."""
    rows = []
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        hh = h * max(0.05, (1.0 - abs(2.0 * t - 1.0) ** 6)) ** 0.5
        rows.append([proud((x, y_ref, zc + dz), d)[0] for dz in (-hh, 0.0, hh)])
    ob = M.grid(name, rows, collection, mat, geom.const(outward))
    M.mirror_y(ob)
    return ob


# ----------------------------------------------------------- flank patches
def flank_patch(name, lo, up, proud, collection, mat, d, nk=4, n=None, y_ref=0.97,
                outward=(0.0, 1.0, 0.0)):
    """A strip between two (x, z) edge polylines, projected onto the flank."""
    n = n or max(len(lo), len(up)) * 6
    lo3 = geom.polyline([(x, y_ref, z) for (x, z) in lo], n)
    up3 = geom.polyline([(x, y_ref, z) for (x, z) in up], n)
    rows = [[proud(geom.lerp(lo3[i], up3[i], k / float(nk)), d)[0]
             for k in range(nk + 1)] for i in range(n)]
    return M.grid(name, rows, collection, mat, geom.const(outward))


def vent(prefix, lo, up, proud, collection, lib, inset=0.16, slat=True,
         d=(0.0009, 0.0012, 0.0016), mats=("black_gloss", "shadow", "black_gloss")):
    """A side vent: gloss frame, dark opening inside it, one gloss slat.

    lo/up: the vent's lower and upper edges as (x, z) lists, same length.
    Returns [frame, hole, slat?].
    """
    frame = flank_patch(prefix + "_Frame", lo, up, proud, collection, lib[mats[0]], d[0])
    ilo, iup = geom.inset_edges(lo, up, inset)
    hole = flank_patch(prefix + "_Hole", ilo, iup, proud, collection, lib[mats[1]], d[1])
    made = [frame, hole]
    if slat:
        mid_lo = [(x, z0 + (z1 - z0) * 0.42) for (x, z0), (_, z1) in zip(ilo, iup)]
        mid_up = [(x, z0 + (z1 - z0) * 0.58) for (x, z0), (_, z1) in zip(ilo, iup)]
        made.append(flank_patch(prefix + "_Slat", mid_lo[1:], mid_up[1:], proud,
                                collection, lib[mats[2]], d[2], nk=2))
    for ob in made:
        M.mirror_y(ob)
    return made


def outline_ring(name, x0, x1, z0, z1, r, proud, collection, mat, width=0.0016,
                 d=0.0003, y_ref=0.95, per_corner=7, mirror=False):
    """A thin dark ring along a rounded rectangle in side elevation.

    The shut line of a charge flap or fuel door. Built on one side only by
    default - most cars have the flap on one side.
    """
    loop = geom.rounded_loop(x0, x1, z0, z1, r, per_corner)
    cx, cz = 0.5 * (x0 + x1), 0.5 * (z0 + z1)
    rows = []
    for (x, z) in loop:
        dx, dz = x - cx, z - cz
        L = math.hypot(dx, dz) or 1.0
        rows.append([proud((x - dx / L * w, y_ref, z - dz / L * w), d)[0]
                     for w in (width, -width)])
    ob = M.grid(name, rows, collection, mat, geom.const((0.0, 1.0, 0.0)))
    if mirror:
        M.mirror_y(ob)
    return ob


def side_patch(name, lo, up, side_point, collection, mat, d=0.0015, n=12, nk=3,
               y_ref=0.95, outward=(0.3, 1.0, 0.0), mirror=True):
    """A patch between two (x, z) polylines, placed with an analytic
    side_point - for dark inlays that wrap a corner (intakes beside a fin)."""
    lo3 = geom.polyline([(x, y_ref, z) for (x, z) in lo], n)
    up3 = geom.polyline([(x, y_ref, z) for (x, z) in up], n)
    rows = []
    for i in range(n):
        col = []
        for k in range(nk + 1):
            q = geom.lerp(lo3[i], up3[i], k / float(nk))
            p, nrm = side_point(q[0], q[2])
            col.append(tuple(Vector(p) + Vector(nrm) * d))
        rows.append(col)
    ob = M.grid(name, rows, collection, mat, geom.const(outward))
    if mirror:
        M.mirror_y(ob)
    return ob


# --------------------------------------------------------------- stripes
def surface_band(name, xa, xb, z_bot, z_top, proud, collection, mat, nx, nk=4,
                 d=0.0007, y_ref=0.95, outward=(0.0, 1.0, 0.0), mirror=True):
    """A decal band on the flank between height curves z_bot(x) and z_top(x).

    xa(k), xb(k): the band's ends as functions of k (0 bottom .. 1 top), so an
    end can be cut on a slant. Break decals at shut lines - build one band per
    panel.
    """
    rows = []
    for i in range(nx + 1):
        t = i / float(nx)
        row = []
        for j in range(nk + 1):
            k = j / float(nk)
            x = xa(k) + (xb(k) - xa(k)) * t
            z = z_bot(x) + (z_top(x) - z_bot(x)) * k
            row.append(proud((x, y_ref, z), d)[0])
        rows.append(row)
    ob = M.grid(name, rows, collection, mat, geom.const(outward))
    if mirror:
        M.mirror_y(ob)
    return ob


def centre_stripes(name, path_xz, y0, y1, proud, collection, mat, cols=4, lift=0.02,
                   d=0.0006, outward=(0.0, 0.0, 1.0)):
    """Racing stripes from y0 to y1 each side of the centreline, along a path
    of (x, z) points over the car's top (nose -> hood -> roof ...)."""
    rows = []
    for (x, z) in path_xz:
        row = []
        for c in range(cols):
            y = y0 + (y1 - y0) * c / float(cols - 1)
            row.append(proud((x, y, z + lift), d)[0])
        rows.append(row)
    ob = M.grid(name, rows, collection, mat, geom.const(outward))
    M.mirror_y(ob)
    return ob


# ------------------------------------------------------------------ lidar
def lidar_pod(name, collection, mat, cx, zc, a=0.105, b=0.088, c=0.058, nu=24, nv=10):
    """A half-ellipsoid bump on the roof centreline (x = cx, base at zc)."""
    verts = []
    for j in range(nv + 1):
        el = 0.5 * math.pi * j / nv                     # 0 at the equator
        for i in range(nu):
            az = 2.0 * math.pi * i / nu
            verts.append((cx + a * math.cos(el) * math.cos(az),
                          b * math.cos(el) * math.sin(az),
                          zc + c * math.sin(el)))
    faces = []
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            faces.append([j * nu + i, j * nu + i2, (j + 1) * nu + i2, (j + 1) * nu + i])
    ob = M.obj(name, verts, faces, collection, mat)
    M.orient(ob.data, geom.away_from((cx, 0.0, zc)))
    return ob


# ---------------------------------------------------------- panels, badges
def rounded_panel(name, centre, hw, hh, r, place, surf_x, collection, mat, d=0.0015,
                  ny=16, outward=(-1.0, 0.0, 0.0)):
    """A rounded rectangle in elevation (half-width hw, half-height hh, corner
    r), each point dropped onto the body by place(p, d) from x = surf_x.

    A plate recess, a sensor window, a closed-grille panel.
    """
    rows = []
    for i in range(ny + 1):
        y = centre[1] - hw + 2.0 * hw * i / float(ny)
        e = max(0.0, abs(y - centre[1]) - (hw - r)) / r
        hz = hh - r * (1.0 - math.sqrt(max(0.0, 1.0 - e * e)))
        rows.append([place((surf_x, y, centre[2] + dz * hz), d)[0]
                     for dz in (-1.0, -0.5, 0.0, 0.5, 1.0)])
    return M.grid(name, rows, collection, mat, geom.const(outward))


def text_badge(name, text, size, p, n, collection, mat, italic=False, bold=False,
               extrude=0.0008, up_hint=(0.0, 0.0, 1.0)):
    """Lettering on the surface at p facing n. One object per side - a Mirror
    modifier would render the other side's text back to front."""
    t = M.text_mesh(name, text, size, collection, mat, extrude=extrude, bold=bold,
                    italic=italic)
    P.on_surface(t, p, n, up_hint)
    return t


def plate(prefix, p, n, collection, lib, w=0.440, h=0.140, depth=0.006,
          texts=(), mat="plate", text_mat="text_dark", bevel=(0.004, 3, 30)):
    """A plate facing n at p, with texts [(body, dx, size, italic, bold)...]
    shifted along the plate's own width. Returns [plate, text...]."""
    made = []
    verts = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0),
             (-w / 2, h / 2, 0), (-w / 2, -h / 2, -depth), (w / 2, -h / 2, -depth),
             (w / 2, h / 2, -depth), (-w / 2, h / 2, -depth)]
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2],
             [2, 6, 7, 3], [3, 7, 4, 0]]
    pl = M.obj(prefix, verts, faces, collection, lib[mat], smooth=False)
    M.bevel(pl, bevel[0], bevel[1], bevel[2])
    P.on_surface(pl, p, n)
    made.append(pl)
    obs = []
    for (body, dx, size, italic, bold) in texts:
        obs.append((M.text_mesh(prefix + "_" + body.replace(" ", ""), body, size,
                                collection, lib[text_mat], bold=bold, italic=italic), dx))
    for ob, dx in obs:
        nvec = Vector(n).normalized()
        q = Vector(p) + nvec * 0.0012
        P.on_surface(ob, q, n)
        xv = Vector((0.0, 0.0, 1.0)).cross(nvec).normalized()
        ob.location = ob.matrix_world.translation + xv * dx
        made.append(ob)
    return made
