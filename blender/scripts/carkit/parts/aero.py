"""Aero parts: wings, roof spoilers, ducktails, splitters, diffusers, fins, skirts.

All built on the left half and mirrored. Hardpoints are in car coordinates
(x forward, z up, metres), read off camera-matched photographs - a wing read
off a photo by eye was 200 mm too high on the SU7.

    rear_wing      cambered aerofoil blade + endplates + pylons
                   pylon styles: "triangle_cutout" (SU7 Ultra), "plate"
    roof_spoiler   a blade continuing the roof past a hatch/tailgate (SUVs)
    ducktail       an upturned lip along the rear edge of a decklid
    splitter       a front splitter from a measured leading edge, in zones
                   (e.g. carbon centre, body-colour wings)
    diffuser       rear deck ramping up to the bumper, with vertical fins
    corner_fin     an air-curtain fin standing off the body at a front corner
    side_skirt     a sill blade along the flank
"""
import math

from mathutils import Vector

from .. import geom
from .. import mesh as M


# --------------------------------------------------------------- rear wing
def rear_wing(prefix, collection, lib, le, te, half_span, thickness=0.093,
              camber=0.040, camber_pos=0.40, n=22, ny=24, mat="carbon",
              bevel=(0.0015, 2, 40), endplate=None, pylons=None, tip=None):
    """A fixed wing. le/te are (x, z) of the leading and trailing edges; put
    the trailing edge HIGHER - an inverted wing makes downforce trailing edge up.

    endplate: dict(pts=[(x, z)...], t=0.006, mat="carbon", bevel=0.0018)
    tip:      dict(radius=0.05, drop=0.04, n=6) - the blade itself curls down
              at the tip, round a bend of `radius`, then runs `drop` further
              down: a downturned tip in place of a bolted-on endplate
    pylons:   dict(style="triangle_cutout"|"plate", y=0.40, t=0.010,
                   x_deck=(xa, xb), x_wing=(xc, xd), deck_z=f(x, y),
                   cutout=0.55, below=0.016, mat="black_gloss", bevel=0.0025)
    Returns [blade, endplate?, pylon?].
    """
    made = []
    up, lo = geom.aerofoil(thickness, camber, camber_pos, n)
    chord_dx = te[0] - le[0]
    chord_dz = te[1] - le[1]
    c = math.hypot(chord_dx, chord_dz)
    ux, uz = chord_dx / c, chord_dz / c
    nx, nz = -uz, ux
    if nz < 0:
        nx, nz = -nx, -nz

    def sect(pts):
        return [(le[0] + ux * s * c + nx * t * c,
                 le[1] + uz * s * c + nz * t * c) for (s, t) in pts]

    loop = sect(up) + list(reversed(sect(lo)))[1:-1]
    ys = [half_span * j / float(ny) for j in range(ny + 1)]
    rings = [[(x, y, z) for (x, z) in loop] for y in ys]
    if tip:
        # Bend the span down about an axis along x under the tip: a point's
        # offset from the chord line becomes its offset from the bend's arc,
        # so the upper surface runs round the outside of the bend.
        R, drop, nt = tip.get("radius", 0.05), tip.get("drop", 0.04), tip.get("n", 6)

        def zc(x):
            return le[1] + chord_dz * (x - le[0]) / chord_dx

        steps = [(0.5 * math.pi * k / nt, 0.0) for k in range(1, nt + 1)]
        steps += [(0.5 * math.pi, drop * k / 2.0) for k in (1, 2)]
        for th, dz in steps:
            ring = []
            for (x, z) in loop:
                rr = R + (z - zc(x))
                ring.append((x, half_span + rr * math.sin(th),
                             zc(x) - R + rr * math.cos(th) - dz))
            rings.append(ring)
    verts, faces = [], []
    nl = len(loop)
    for ring in rings:
        verts.extend(ring)
    nr = len(rings)
    for j in range(nr - 1):
        a, b = j * nl, (j + 1) * nl
        for i in range(nl):
            i2 = (i + 1) % nl
            faces.append([a + i, a + i2, b + i2, b + i])
    faces.append([(nr - 1) * nl + i for i in range(nl)])    # tip cap
    blade = M.obj(prefix + "_Blade", verts, faces, collection, lib[mat])
    M.bevel(blade, bevel[0], bevel[1], bevel[2])
    M.mirror_y(blade)
    made.append(blade)

    if endplate:
        ye = half_span
        pts = endplate["pts"]
        t = endplate.get("t", 0.006)
        verts = [(x, ye, z) for (x, z) in pts] + [(x, ye + t, z) for (x, z) in pts]
        k = len(pts)
        faces = [list(range(k)), list(range(2 * k - 1, k - 1, -1))]
        faces += [[i, (i + 1) % k, k + (i + 1) % k, k + i] for i in range(k)]
        plate = M.obj(prefix + "_Endplate", verts, faces, collection,
                      lib[endplate.get("mat", mat)], smooth=False)
        M.bevel(plate, endplate.get("bevel", 0.0018), 2)
        M.mirror_y(plate)
        made.append(plate)

    if pylons:
        made.append(_pylon(prefix + "_Pylon", collection, lib, le, chord_dx, chord_dz,
                           pylons))
    return made


def _pylon(name, collection, lib, le, chord_dx, chord_dz, spec):
    """A bracket from the deck to the wing's underside, in the XZ plane at y."""
    below = spec.get("below", 0.016)

    def under(x):
        s = (x - le[0]) / chord_dx
        return le[1] + chord_dz * s - below

    deck = spec["deck_z"]
    yp, th = spec.get("y", 0.40), spec.get("t", 0.010)
    xa, xb = spec["x_deck"]
    xc, xd = spec["x_wing"]
    outer = [(xa, deck(xa, yp)), (xb, deck(xb, yp)), (xc, under(xc)), (xd, under(xd))]
    style = spec.get("style", "triangle_cutout")
    n = len(outer)
    mat = lib[spec.get("mat", "black_gloss")]
    if style == "triangle_cutout":
        cx = sum(p[0] for p in outer) / 4.0
        cz = sum(p[1] for p in outer) / 4.0
        k = spec.get("cutout", 0.55)
        inner = [(cx + (x - cx) * k, cz + (z - cz) * k) for (x, z) in outer]
        verts = []
        for loop in (outer, inner):
            for side in (-0.5, 0.5):
                verts += [(x, yp + th * side, z) for (x, z) in loop]
        O0, O1, I0, I1 = 0, n, 2 * n, 3 * n
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces.append([O0 + i, O0 + j, I0 + j, I0 + i])     # face -y
            faces.append([O1 + j, O1 + i, I1 + i, I1 + j])     # face +y
            faces.append([O0 + j, O0 + i, O1 + i, O1 + j])     # outer wall
            faces.append([I0 + i, I0 + j, I1 + j, I1 + i])     # inner wall
    elif style == "plate":
        verts = [(x, yp - th * 0.5, z) for (x, z) in outer] + \
                [(x, yp + th * 0.5, z) for (x, z) in outer]
        faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
        faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    else:
        raise ValueError("unknown pylon style: " + style)
    py = M.obj(name, verts, faces, collection, mat, smooth=False)
    M.bevel(py, spec.get("bevel", 0.0025), 2)
    M.mirror_y(py)
    return py


# ------------------------------------------------------------ roof spoiler
def roof_spoiler(name, collection, lib, roof_edge, half_span, chord=0.16,
                 angle_deg=-6.0, thickness=0.018, tip_taper=0.6, n=20,
                 mat="paint", lift=0.0):
    """A blade continuing the roof rearward over a tailgate.

    roof_edge(y) -> (x, z) is where the roof ends at lateral offset y (read it
    from the loft: the roof's rear edge above the backlight). The blade leaves
    at `angle_deg` below horizontal (negative droops, positive kicks up),
    `chord` long at the centre and tapering to tip_taper * chord at the tip.
    """
    rows = []
    a = math.radians(angle_deg)
    for i in range(n + 1):
        y = half_span * i / float(n)
        x0, z0 = roof_edge(y)
        z0 += lift
        f = i / float(n)
        ch = chord * (1.0 - (1.0 - tip_taper) * f * f)
        xt, zt = x0 - ch * math.cos(a), z0 + ch * math.sin(a)
        th = thickness * (1.0 - 0.4 * f * f)
        rows.append([(x0 + 0.02, y, z0 - 0.002), (xt, y, zt), (xt + 0.004, y, zt - th * 0.6),
                     (x0 + 0.01, y, z0 - th)])
    ob = M.grid(name, rows, collection, lib[mat], lambda c: (-0.3, 0.0, 1.0))
    M.bevel(ob, 0.0015, 2, 40)
    M.mirror_y(ob)
    return ob


# ----------------------------------------------------------------- ducktail
def ducktail(name, collection, lib, z_deck, x_edge, half_width=0.80, n=26,
             root=0.110, sink=(0.002, 0.02), lip=(0.020, 0.012),
             under=(0.020, 0.004, 0.006, 0.050, 0.02, 0.060), mat="paint",
             outward=(-0.5, 0.0, 0.8)):
    """A crisp upturned lip along the rear edge of a decklid.

    z_deck(x): the deck height (the loft's Z_ROOF). x_edge(y): the lip's plan
    line - pull it forward toward the corners. Without a lip the deck rolls
    into the tail face like a bustle.
    """
    rows = []
    e_in, e_up, u_in, u_down, r_in, r_down = under
    for i in range(n + 1):
        y = half_width * i / float(n)
        xe = x_edge(y)
        x_root = xe + root
        z_root = z_deck(x_root) - sink[0] - sink[1] * (y / half_width) ** 2
        z_lip = z_root + lip[0] - lip[1] * (y / half_width) ** 2
        rows.append([(x_root, y, z_root), (xe + e_in, y, z_lip + e_up),
                     (xe, y, z_lip), (xe + u_in, y, z_lip - u_down),
                     (x_root - r_in, y, z_root - r_down)])
    ob = M.grid(name, rows, collection, lib[mat], geom.const(outward))
    M.mirror_y(ob)
    return ob


# ----------------------------------------------------------------- splitter
def _interp_table(table, y):
    for j in range(len(table) - 1):
        a, b = table[j], table[j + 1]
        if a[0] <= y <= b[0] + 1e-9:
            t = (y - a[0]) / (b[0] - a[0])
            return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t
    a = table[-1]
    return a[1], a[2]


def splitter(prefix, collection, lib, le_table, zones, x_te, thickness=0.014,
             bevel=(0.0035, 3, 30), n_y=18, n_x=6):
    """A splitter from its measured leading edge.

    le_table: [(y, x_leading_edge, z_top), ...] from the centreline out.
    zones:    [(suffix, y0, y1, material role), ...] e.g. a carbon centre
              and body-colour wings.
    x_te(y, x_le): the trailing edge (the deck runs back under the bumper).
    """
    made = []
    for part, y0, y1, role in zones:
        rows = []
        ys = [y0 + (y1 - y0) * i / float(n_y) for i in range(n_y + 1)]
        for y in ys:
            xle, zt = _interp_table(le_table, y)
            xte = x_te(y, xle)
            row = []
            for k in range(n_x + 1):
                t = k / float(n_x)
                x = xle + (xte - xle) * t
                row.append((x, y, zt))
            rows.append(row)
        ob = M.grid(prefix + part, rows, collection, lib[role], geom.const((0.0, 0.0, 1.0)))
        M.solidify(ob, thickness, -1.0)
        M.bevel(ob, bevel[0], bevel[1], bevel[2])
        M.mirror_y(ob)
        made.append(ob)
    return made


# ----------------------------------------------------------------- diffuser
def diffuser(prefix, collection, lib, x_rear, x_front=-2.200, half_width=0.66,
             n=12, z=(0.150, 0.180, 0.240), thickness=0.006,
             fins=(0.0, 0.150, 0.300, 0.450, 0.600), fin_t=(0.004, 0.005),
             fin_z=(0.150, 0.245, 0.330, 0.165), fin_back=0.004, mat="carbon"):
    """A ramped rear deck with vertical fins.

    x_rear(y): the deck's rear edge - follow the bumper's plan (cap.x_at) a
    little proud of it; straight, the outer fins stick out of the silhouette.
    fins: lateral positions; a fin at y = 0 is built once, the rest mirrored.
    """
    made = []
    rows = []
    for i in range(n + 1):
        y = half_width * i / float(n)
        xr = x_rear(y)
        rows.append([(x_front, y, z[0]), (0.5 * (x_front + xr), y, z[1]), (xr, y, z[2])])
    deck = M.grid(prefix, rows, collection, lib[mat], geom.const((0.0, 0.0, -1.0)))
    M.solidify(deck, thickness)
    M.mirror_y(deck)
    made.append(deck)
    for k, yf in enumerate(fins):
        t = fin_t[1] if yf else fin_t[0]
        xr = x_rear(yf) + fin_back
        prof = [(x_front, fin_z[0]), (xr, fin_z[1]), (xr, fin_z[2]), (x_front, fin_z[3])]
        verts = [(x, yf - t, zz) for (x, zz) in prof] + [(x, yf + t, zz) for (x, zz) in prof]
        faces = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2],
                 [2, 6, 7, 3], [3, 7, 4, 0]]
        fin = M.obj(prefix + "_Fin%d" % k, verts, faces, collection, lib[mat], smooth=False)
        M.bevel(fin, 0.0015, 2)
        if yf:
            M.mirror_y(fin)
        made.append(fin)
    return made


# --------------------------------------------------------------- corner fin
def corner_fin(name, collection, lib, top, z0, stand, side_point, n=30, nk=7,
               smooth_passes=2, thickness_extra=0.003, bevel=(0.0020, 2, 40),
               mat="paint", outward=(0.3, 1.0, 0.0), y_ref=0.95):
    """An air-curtain fin: the body's smooth surface pushed out `stand` and
    made solid, from z0 up to the top line `top` [(x, z), ...].

    side_point(x, z) -> (point, normal) must be ANALYTIC (CarBody.side_point):
    rays onto the meshes hit the painted cheek, a recessed mouth and a lower lip
    in turn at the bottom of a corner, and the fin crumples.
    """
    tl = geom.polyline([(x, y_ref, z) for (x, z) in top], n)
    rows = []
    for i in range(n):
        x, _, zt = tl[i]
        col = []
        for k in range(nk + 1):
            zz = z0 + (zt - z0) * k / float(nk)
            p, nrm = side_point(x, zz)
            # push out mostly sideways: a fin is a vertical plate
            d = Vector((nrm[0] * 0.5, max(0.3, nrm[1]), 0.0)).normalized()
            col.append(tuple(Vector(p) + d * stand))
        rows.append(col)
    rows = M.smooth_grid(rows, smooth_passes)
    fin = M.grid(name, rows, collection, lib[mat], geom.const(outward))
    M.solidify(fin, stand + thickness_extra, -1.0)
    M.bevel(fin, bevel[0], bevel[1], bevel[2])
    M.mirror_y(fin)
    return fin


# ---------------------------------------------------------------- side skirt
def flank_rows(proud, y_guess, x0, x1, z0, z1, nx, nz, d):
    """Rows of points d proud of the flank between two stations and heights."""
    rows = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / float(nx)
        row = []
        for k in range(nz + 1):
            z = z0 + (z1 - z0) * k / float(nz)
            row.append(proud((x, y_guess(x), z), d)[0])
        rows.append(row)
    return rows


def side_skirt(name, collection, lib, proud, y_guess, x0, x1, z0, z1, nx=60, nz=8,
               d=0.009, thickness=0.008, bevel=(0.002, 2, 35), mat="carbon"):
    """A sill blade standing d off the flank between two stations."""
    rows = flank_rows(proud, y_guess, x0, x1, z0, z1, nx, nz, d)
    ob = M.grid(name, rows, collection, lib[mat], geom.const((0.0, 1.0, 0.0)))
    M.solidify(ob, thickness)
    M.bevel(ob, bevel[0], bevel[1], bevel[2])
    M.mirror_y(ob)
    return ob
