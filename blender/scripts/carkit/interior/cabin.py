"""The cabin enclosure, built from the car's own body surface.

Everything that closes the cabin is an OFFSET of the exterior loft, so the
inside always agrees with the outside: move a roof control point and the
headliner follows. From inside, the body panels are hidden behind these trims,
and the window openings are simply the gaps between them.

    headliner     the roof inner surface, `inset` below the skin, between the
                  windscreen header and the backlight header
    pillar_trim   a rounded trim along a pillar, spanning between two glass
                  edges given as section parameters v0(x), v1(x)
    floor         carpeted floor with the front toe board rising to the firewall
    sill          the step along a door opening
    bulkhead      a closing panel across the car (parcel shelf, rear wall)

Offsets use the loft's outward normal, so `inset` is a real thickness.
"""
import math

from mathutils import Vector

from .. import mesh as M
from .sweep import grid_mesh, Sweep


def headliner(loft, collection, mat, x_front, x_rear, v_edge, inset=0.045, nx=48, nv=22,
              name="int_headliner"):
    """Roof inner surface from v_edge(x) (its side edge, near the rail) to the
    centreline, mirrored. x_front/x_rear: headliner ends (a little past the
    glass headers, so the trim overlaps the glass edge as on a real car)."""
    rows = []
    for i in range(nx + 1):
        x = x_front + (x_rear - x_front) * i / float(nx)
        v0 = v_edge(x)
        row = [loft.surface_offset(x, v0 + (0.9995 - v0) * j / float(nv), -inset)
               for j in range(nv + 1)]
        # land the centre column ON the mirror plane, or a hairline shows
        row[-1] = (row[-1][0], 0.0, row[-1][2])
        rows.append(row)
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))      # faces down, into the cabin
    M.mirror_y(ob)
    return ob


def pillar_trim(loft, collection, mat, xs, v0, v1, inset=0.030, bulge=0.030, nt=10,
                name="int_pillar", overlap=0.010):
    """A rounded trim covering a pillar between two glass edges.

    xs: stations along the pillar (in order); v0(x), v1(x): the section
    parameters of the two edges it spans. The trim sits `inset` inside the
    skin at its edges (overlapping each glass edge by `overlap` metres along
    the section) and bulges `bulge` further into the cabin at its middle.
    """
    rows = []
    for x in xs:
        a = loft.v_along(x, v0(x), -overlap)
        b = loft.v_along(x, v1(x), overlap)
        row = []
        for j in range(nt + 1):
            t = j / float(nt)
            v = a + (b - a) * t
            d = inset + bulge * math.sin(math.pi * t) ** 0.7
            row.append(loft.surface_offset(x, v, -d))
        rows.append(row)
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -c[1], -(c[2] - 0.9)))   # into the cabin
    M.mirror_y(ob)
    return ob


def edge_band(loft, collection, mat, stations, edge_a, edge_b, depth=0.012, bulge=0.030,
              nt=12, name="int_trim", mirror=True):
    """A rounded trim spanning between two glass edges - pillars, roof rails.

    stations: a list of station parameters q; edge_a(q), edge_b(q) -> (x, v)
    of the two edges on the body surface. Each cross-band is the CHORD between
    the two edge points, pushed into the cabin by `depth` at its edges and
    `depth + bulge` at its middle (a D profile). Offsetting the body surface
    itself folds wherever the pillar's radius is smaller than the offset -
    the first A-pillar came out twisted.
    """
    rows = []
    for q in stations:
        xa, va = edge_a(q)
        xb, vb = edge_b(q)
        A = Vector(loft.surface(xa, va))
        B = Vector(loft.surface(xb, vb))
        n = (Vector(loft.surface_normal(xa, va)) + Vector(loft.surface_normal(xb, vb))).normalized()
        row = []
        for j in range(nt + 1):
            t = j / float(nt)
            d = depth + bulge * math.sin(math.pi * t) ** 0.6
            row.append(tuple(A.lerp(B, t) - n * d))
        rows.append(row)
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -c[1], -(c[2] - 0.9)))
    if mirror:
        M.mirror_y(ob)
    return ob


def floor(collection, mat, x_rear, x_toe, x_fire, z_floor, z_fire, half_w_fn, n=40,
          name="int_floor"):
    """A flat carpeted floor from x_rear to the toe board at x_toe, rising to
    the firewall at (x_fire, z_fire). half_w_fn(x) -> half-width at x."""
    prof = []
    for i in range(n + 1):
        x = x_rear + (x_toe - x_rear) * i / float(n)
        prof.append((x, z_floor))
    for i in range(1, 11):
        t = i / 10.0
        # toe board: a soft S from the floor up to the firewall
        s = t * t * (3 - 2 * t)
        prof.append((x_toe + (x_fire - x_toe) * t, z_floor + (z_fire - z_floor) * s))
    rows = []
    for (x, z) in prof:
        hw = half_w_fn(x)
        rows.append([(x, hw * j / 12.0, z) for j in range(13)])
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (-0.3, 0.0, 1.0))
    M.mirror_y(ob)
    return ob


def sill(collection, mat, x0, x1, y_in, y_out, z_floor, z_top, r=0.020, name="int_sill"):
    """The trim along a door opening's bottom: a rounded step from the floor up
    to the sill top, outboard of y_in."""
    prof = [(y_in, z_floor), (y_in, z_top - r), (y_in + r * 0.3, z_top - r * 0.3),
            (y_in + r, z_top), (y_out, z_top)]
    rows = [[(x0 + (x1 - x0) * i / 20.0, y, z) for (y, z) in prof] for i in range(21)]
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -1.0, 0.6))
    M.mirror_y(ob)
    return ob


def bulkhead(collection, mat, pts, half_w_fn, n=12, name="int_bulkhead", facing=(1, 0, 0)):
    """A panel across the car along a centreline profile pts [(x, z)...], out
    to half_w_fn(x, z) either side (mirrored)."""
    rows = []
    for (x, z) in pts:
        hw = half_w_fn(x, z)
        rows.append([(x, hw * j / float(n), z) for j in range(n + 1)])
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: facing)
    M.mirror_y(ob)
    return ob


def skin_offset_y(loft, x, z, depth, v_hi):
    """|y| of a point `depth` inboard of the flank skin at (x, z)."""
    v = loft.v_at_z(x, z, 0.02, v_hi)
    return loft.section_v(x, v)[0] - depth


def wheelhouse_trim(loft, collection, mat, x_front, x_back, z_floor, y_hump, z_hump,
                    z_top, depth_top, v_hi, nx=36, name="int_quarter", mirror=True,
                    close_to=None):
    """The side trim behind a rear door: a wall at |y| = y_hump over the
    wheelhouse, rolling over at z_hump onto an upper panel `depth_top` inside
    the skin, up to z_top (tuck it under the next trim up).

    x_front(z): the door's trailing edge (the trim's front edge follows it);
    x_back: a fixed station behind the seat back. close_to(z) -> |y|: if
    given, a forward-facing strip closes the front edge out to that line (the
    rear door card), so the shut gap shows trim, not paint.
    """
    def profile(x):
        pts = [(y_hump, z_floor + (z_hump - 0.05 - z_floor) * k / 5.0) for k in range(6)]
        pts += [(y_hump + 0.006, z_hump - 0.022), (y_hump + 0.020, z_hump - 0.004)]
        yu = skin_offset_y(loft, x, z_hump + 0.03, depth_top, v_hi)
        pts.append((0.5 * (y_hump + 0.020 + yu), z_hump + 0.010))
        for k in range(5):
            z = z_hump + 0.03 + (z_top - z_hump - 0.03) * k / 4.0
            pts.append((skin_offset_y(loft, x, z, depth_top, v_hi), z))
        return pts

    nprof = len(profile(x_back))
    rows = []
    for i in range(nx + 1):
        t = i / float(nx)
        row = []
        for k in range(nprof):
            # the front edge follows the door's trailing edge, which moves with z
            x = x_back
            for _ in range(3):
                z = profile(x)[k][1]
                x = x_back + (x_front(z) - x_back) * t
            y, z = profile(x)[k]
            row.append((x, y, z))
        rows.append(row)
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: (0.0, -1.0, 0.2))
    made = [ob]
    if close_to is not None:
        edge = rows[-1]
        strip = [[(x + 0.001, y, z), (x + 0.001, max(y, close_to(z)), z)] for (x, y, z) in edge]
        cl = grid_mesh(name + "_Close", strip, collection, mat)
        M.orient(cl.data, lambda c: (1.0, 0.0, 0.0))
        made.append(cl)
    if mirror:
        for o in made:
            M.mirror_y(o)
    return made


def wall(collection, mat, pts_xy, z_lo, z_hi, nz=8, name="int_wall", facing=(0, -1, 0),
         mirror=True):
    """A vertical panel along a plan polyline pts_xy [(x, y)...] from z_lo(x, y)
    to z_hi(x, y) - kick panels, closing faces. Mirrored to the other side."""
    rows = []
    for (x, y) in pts_xy:
        a, b = z_lo(x, y), z_hi(x, y)
        rows.append([(x, y, a + (b - a) * k / float(nz)) for k in range(nz + 1)])
    ob = grid_mesh(name, rows, collection, mat)
    M.orient(ob.data, lambda c: facing)
    if mirror:
        M.mirror_y(ob)
    return ob


def section_y_at(loft, x, z, v_lo=0.02, v_hi=None):
    """Half-width of the body's inner... outer skin at (x, z) on the flank
    below the shoulder (bisection on v)."""
    v_hi = loft.V_SHOULDER if v_hi is None else v_hi
    v = loft.v_at_z(x, z, v_lo, v_hi)
    return loft.section_v(x, v)[0]
