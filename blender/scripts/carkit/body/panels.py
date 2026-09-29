"""Body panels cut as regions of the master surface, plus the hidden shell.

Flank panels
------------
A flank panel is a quad grid over a region of (x, v), inset by half a shut-line
width on every shared edge, so the gap between panels is real geometry with
real depth over a dark shell. Limits may be curves: x-limits as functions of v
(a fender that stops exactly on the bumper shut line), v-limits as functions of
x (a door that starts at the sill wherever the sill is). Openings are cut
afterwards by exact booleans (see carkit.cut), never trimmed in the grid.

A panel spec is a dict:

    name          object name
    x=(x0, x1)    numbers or callables of v
    v=(v0, v1)    numbers or callables of x
    nx, nv        grid density
    mat / glass   material role (glass gets no thickness and no bevel)
    gap           dict(x0=, x1=, v0=, v1=) - False where the edge butts
    offset        metres off the surface (an underlay sits at -0.003)
    thickness     sheet thickness (default mesh.SKIN)
    fixed_x       stations that must land on a column pair (limit jumps)
    <flag>=True   any key in the `cutters` passed to build_panels, e.g.
                  arch=True runs the wheel-arch cut on this panel

End caps are gridded with `cap_rows`, evenly in height across the face.
"""
import math

from .. import geom
from .. import mesh as M

GAP = 0.0042                 # 4.2 mm shut line
SHELL_INSET = 0.0072
SHELL_SHRINK = 0.982


def _lim(f, arg):
    return f(arg) if callable(f) else f


def panel_grid(loft, x0, x1, v0, v1, nx, nv, gap_x0=True, gap_x1=True,
               gap_v0=True, gap_v1=True, offset=0.0, fixed_x=(), gap=GAP,
               v_per_m=2.15):
    """Columns of surface points over a (possibly curved) region of (x, v).

    x0/x1 may be callables of v; v0/v1 may be callables of x. Because x-limits
    depend on v and v-limits depend on x, each point is solved by a damped
    fixed point (10 iterations, relaxed after the second). A limit that pinches
    to a point collapses the rows instead of inverting them.
    """
    hx = gap * 0.5
    hv = (gap * 0.5) / v_per_m

    ss = [i / float(nx) for i in range(nx + 1)]

    # Fixed-x columns: a pair either side of every place a v-limit jumps, so
    # the step lands on a real edge. Ordinary columns that stray near one at
    # any height are dropped - a column that crosses a fixed one folds the
    # sheet.
    specs = [("s", s) for s in ss]
    if fixed_x:
        probe = (0.05, 0.3, 0.5, 0.7, 0.9)
        keep = []
        for kind, s in specs:
            near = False
            for xe in fixed_x:
                for pv in probe:
                    xp = _lim(x0, pv) + (_lim(x1, pv) - _lim(x0, pv)) * s
                    if abs(xp - xe) < 0.018:
                        near = True
                        break
                if near:
                    break
            if not near:
                keep.append((kind, s))
        specs = keep + [("x", xe + d) for xe in fixed_x for d in (-0.0015, 0.0015)]

        def _key(c):
            if c[0] == "x":
                return c[1]
            return _lim(x0, 0.5) + (_lim(x1, 0.5) - _lim(x0, 0.5)) * c[1]
        specs.sort(key=_key)

    cols = []
    for kind, s in specs:
        col = []
        x = s if kind == "x" else _lim(x0, 0.5) + (_lim(x1, 0.5) - _lim(x0, 0.5)) * s
        for j in range(nv + 1):
            t = j / float(nv)
            v = 0.5
            for it in range(10):
                vlo = _lim(v0, x) + (hv if gap_v0 else 0.0)
                vhi = _lim(v1, x) - (hv if gap_v1 else 0.0)
                if vhi < vlo:                  # a limit pinched to a point
                    vlo = vhi = 0.5 * (vlo + vhi)
                v = vlo + (vhi - vlo) * t
                if kind == "x":
                    x = s
                else:
                    xlo = _lim(x0, v) + (hx if gap_x0 else 0.0)
                    xhi = _lim(x1, v) - (hx if gap_x1 else 0.0)
                    xn = xlo + (xhi - xlo) * s
                    x = xn if it < 2 else 0.5 * (x + xn)
            if offset:
                p = loft.surface_offset(x, v, offset)
            else:
                p = loft.surface(x, v)
            # A panel that runs to the centreline must END on the mirror
            # plane: stopping at v = 0.9995 left the mirrored halves of the
            # windscreen a hair apart, a bright line down the glass from inside.
            if j == nv and not gap_v1 and _lim(v1, x) >= 0.999:
                p = (p[0], 0.0, p[2])
            col.append(p)
        cols.append(col)
    return cols


def crease_row(v0, v1, nv, v_crease):
    """Index of the grid row nearest the shoulder crease, if the panel spans it."""
    if not (callable(v0) or callable(v1)):
        if v0 < v_crease < v1:
            return (int(round((v_crease - v0) / (v1 - v0) * nv)),)
    return ()


def build_panels(specs, loft, collection, lib, cutters=None, core_z=0.70,
                 bevel=0.0012, butt_bevel=True):
    """Build every flank panel spec. `cutters` maps a spec flag to a function
    of the half-sheet; they run in the dict's order, before the mirror.

    butt_bevel=False: edges that butt a neighbour with no gap (a hood running
    into the nose cap) are not rounded. A rounded rim catches the light as a
    line - a shut line the car does not have. Shut lines and cut openings
    keep their bevel."""
    cutters = cutters or {}
    outward = geom.radial(core_z)
    made = []
    for spec in specs:
        g = spec.get("gap", {})
        x0, x1 = spec["x"]
        v0, v1 = spec["v"]
        cols = panel_grid(
            loft, x0, x1, v0, v1, spec["nx"], spec["nv"],
            gap_x0=g.get("x0", True), gap_x1=g.get("x1", True),
            gap_v0=g.get("v0", True), gap_v1=g.get("v1", True),
            offset=spec.get("offset", 0.0), fixed_x=spec.get("fixed_x", ()))
        ob = M.mesh_from_rows(spec["name"], cols, collection,
                              sharp_rows=crease_row(v0, v1, spec["nv"], loft.V_SHOULDER))
        M.orient(ob.data, outward)
        butts = None
        if not butt_bevel:
            butts = _mark_butts(ob, len(cols), spec["nv"], g)
        for flag, fn in cutters.items():
            if spec.get(flag):
                fn(ob)
        if butts:
            _weight_gap_edges(ob)
        M.mirror_y(ob)
        if spec.get("glass"):
            ob.data.materials.append(lib[spec["glass"]])
            M.finish(ob, thickness=0.0, bevel=0.0, weighted=False)
        else:
            ob.data.materials.append(lib[spec["mat"]])
            M.finish(ob, thickness=spec.get("thickness", M.SKIN), bevel=bevel)
            if butts:
                ob.modifiers["Bevel"].limit_method = 'WEIGHT'
        made.append(ob)
    return made


def _mark_butts(ob, ncols, nv, g):
    """Flag the grid's vertices on sides that butt a neighbour (gap False).
    Returns True if any side does. mesh_from_rows orders vertices column by
    column, nv + 1 to a column."""
    sides = [k for k in ("x0", "x1", "v0", "v1") if g.get(k, True) is False]
    if not sides:
        return False
    flag = [0.0] * len(ob.data.vertices)
    for i in range(ncols):
        for j in range(nv + 1):
            if (("x0" in sides and i == 0) or ("x1" in sides and i == ncols - 1)
                    or ("v0" in sides and j == 0) or ("v1" in sides and j == nv)):
                flag[i * (nv + 1) + j] = 1.0
    a = ob.data.attributes.new("_butt", 'FLOAT', 'POINT')
    a.data.foreach_set("value", flag)
    return True


def _weight_gap_edges(ob):
    """Bevel weight 1 on every open edge except those between two butt
    vertices (after the cuts, so openings they made are included)."""
    me = ob.data
    butt = [0.0] * len(me.vertices)
    me.attributes["_butt"].data.foreach_get("value", butt)
    faces_of = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            faces_of[ek] = faces_of.get(ek, 0) + 1
    w = []
    for e in me.edges:
        a, b = e.vertices
        open_edge = faces_of.get(tuple(sorted((a, b))), 0) == 1
        w.append(1.0 if open_edge and not (butt[a] > 0.5 and butt[b] > 0.5) else 0.0)
    attr = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", 'FLOAT', 'EDGE')
    attr.data.foreach_set("value", w)


# ----------------------------------------------------------------- end caps
def cap_rows(cap, z_lo, z_hi, w_lo, w_hi, nz, nw, offset=0.0, top_to_centre=False):
    """Grid over part of a cap, v chosen so rows are even in height.

    top_to_centre: height stops being a usable parameter at the top of the
    nose - past the fender crowns every remaining v maps to the same tip
    height - so carry on in v to the centreline instead of stopping at the
    crown (which left the SU7's nose top unbuilt).
    """
    vs = [cap.v_at_z(z_lo + (z_hi - z_lo) * (k / float(nz)), 0.0)
          for k in range(nz + 1)]
    if top_to_centre and vs[-1] < 0.999:
        extra = max(6, int(round((1.0 - vs[-1]) * 60)))
        vs = vs[:-1] + [vs[-1] + (1.0 - vs[-1]) * (k / float(extra))
                        for k in range(extra + 1)]
        vs[-1] = 0.9995
    rows = []
    for i in range(nw + 1):
        s = i / float(nw)
        if w_hi >= 1.0:
            # denser toward the joint, where the wrap turns hardest
            s = 1.0 - (1.0 - s) ** 1.35
        w = w_lo + (w_hi - w_lo) * s
        if offset:
            rows.append([cap.offset(w, v, offset) for v in vs])
        else:
            rows.append([cap.point(w, v) for v in vs])
    return rows, vs


# -------------------------------------------------------------- the shell
def shadow_shell(body, collection, lib, name, nx=140, nv=56, core_z=0.70,
                 shrink=SHELL_SHRINK, inset=SHELL_INSET, end_offset=-0.075,
                 end_w=0.985, end_grid=(24, 16), mat="shadow"):
    """A dark closed volume inside the skin, behind every gap and opening.

    It has wheel openings of its own: without them the shell's flank, only
    17 mm inside the skin, ran straight through every wheel and hid the inner
    half of each spoke behind a flat grey disc.
    """
    loft, nose, tail = body.loft, body.nose, body.tail
    cols = []
    for i in range(nx + 1):
        t = i / float(nx)
        col = []
        x = 0.0
        for j in range(nv + 1):
            s = j / float(nv)
            # same fixed point as the panels: x depends on v through the joins,
            # the lower bound on v depends on x through the arches
            v = s
            for _ in range(3):
                lo = 0.0
                av = loft.arch_v(x)
                if av is not None:
                    lo = min(0.98, av + 0.012)
                v = lo + (1.0 - lo) * s
                x = tail.JOIN(v) + (nose.JOIN(v) - tail.JOIN(v)) * t
            y, z = loft.section_v(x, v)
            cz = core_z
            col.append((x, y * shrink, cz + (z - cz) * shrink - inset * 0.35))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.radial(core_z))
    ob.data.materials.append(lib[mat])
    M.mirror_y(ob)
    # close the ends so the nose and tail openings do not see through the car
    for cap in (nose, tail):
        rows, _ = cap_rows(cap, cap.Z_LO + 0.01, cap.Z_HI - 0.01, 0.0, end_w,
                           end_grid[0], end_grid[1], offset=end_offset)
        c = M.mesh_from_rows(name + ("_F" if cap.front else "_R"), rows, collection)
        c.data.materials.append(lib[mat])
        M.mirror_y(c)
    return ob


def wheel_liners(loft, collection, lib, prefix, y_outer=0.968, depth=0.250,
                 lip_in=0.003, flare=0.020, z_min=0.05, na=30, nd=8, mat="grille",
                 inner_wall=False, wall_z=0.12):
    """Wheel houses set back from the lip, so an arch is a cavity.

    inner_wall: close the house's inboard side (y_outer - depth) down to
    wall_z. Without it an arch seen from above looks under the car, out
    through the far arch to the floor (the RX's side views: white streaks
    through the front arch)."""
    made = []
    for tag, axle in (("F", loft.FRONT_AXLE), ("R", loft.REAR_AXLE)):
        cols = []
        for i in range(na + 1):
            a = math.pi * (i / float(na))
            col = []
            for j in range(nd + 1):
                d = j / float(nd)
                r = loft.ARCH_R - lip_in + flare * d
                x = axle - r * math.cos(a)
                z = loft.WHEEL_R + r * math.sin(a)
                y = y_outer - d * depth
                col.append((x, y, max(z_min, z)))
            cols.append(col)
        if inner_wall:
            # continue each column across the house's inboard face, down to
            # wall_z: the liner and its wall are one sheet
            y = y_outer - depth
            for col in cols:
                x, _y, z = col[-1]
                for k in range(1, 5):
                    col.append((x, y, z + (min(z, wall_z) - z) * k / 4.0))
        ob = M.mesh_from_rows(prefix + tag, cols, collection)
        ob.data.materials.append(lib[mat])
        M.mirror_y(ob)
        made.append(ob)
    return made


def underbody(loft, collection, lib, name, x0=-2.24, length=4.46, nx=34, ny=12,
              edge_in=0.03, lift=0.004, mat="shadow"):
    """A flat dark tray under the car, out to just inside the sills."""
    cols = []
    for i in range(nx + 1):
        x = x0 + length * (i / float(nx))
        col = []
        for j in range(ny + 1):
            y = (j / float(ny)) * (loft.Y_ROCKER(x) - edge_in)
            col.append((x, y, loft.Z_FLOOR(x) + lift))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(lib[mat])
    M.mirror_y(ob)
    return ob
