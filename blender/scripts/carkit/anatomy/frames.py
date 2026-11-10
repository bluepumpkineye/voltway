"""The structure the hardware hangs on: the floor frame (multi-chamber sills, bulkhead cross-members, shock towers), the front
subframe (a cast plate with lightening pockets and rims), the rear casting (a ribbed one-piece casting) and the two crash
beams with their crush cans. Positions come from the spec's hubs, the floor and the pack, so a longer or wider car gets
longer, wider frames.
"""
import math

from mathutils import Vector

from . import detail as D
from .prim import MB, X, Y, Z, circle, group, rrect, solid
from .suspension import _bush, hardpoints

Zv = Vector((0, 0, 1))


def centre(mb):
    xs = [v[0] for v in mb.v]
    ys = [v[1] for v in mb.v]
    zs = [v[2] for v in mb.v]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)


def extrusion(mb, a, b, w, h, axis_name, chambers=3, wall=0.0042, mi=0, r=0.008):
    """A multi-chamber aluminium extrusion from a to b, `h` tall and `w` wide (across the beam's run: y for a beam running along x,
    x for one running along y), with `chambers` hollow cells that show at the open ends."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    pitch = (w - wall) / chambers
    holes = []
    for k in range(chambers):
        c = -w / 2 + wall / 2 + pitch * (k + 0.5)
        if axis_name == 'x':      # the profile's local X is world Z (up), its local Y the width
            holes.append(rrect(h - 2 * wall, pitch - wall, 0.003, 2, 0.0, c))
        else:                     # a beam running along y: local X is world X (the width), local Y is -Z (up)
            holes.append(rrect(pitch - wall, h - 2 * wall, 0.003, 2, c, 0.0))
    outer = rrect(h, w, r) if axis_name == 'x' else rrect(w, h, r)
    mb.prism(outer, holes, 0.0, L, a, (b - a), mi)


def build(spec, coll, root, M):
    out = {}
    hfx, hfy, hfz = spec.hub_f
    hrx, hry, hrz = spec.hub_r
    p = spec.pack

    # ---- floor frame: multi-chamber sills, the bulkheads fore and aft of the pack (the shock towers belong to the corners, see tower())
    # materials: Alu_Cast 0, Bolt 1, Alu_Machined 2
    g = group("XR_Frame_Floor_G", coll, (0, 0, 0), root, sys="chassis", id="floor")
    mb = MB()
    xa, xb = hrx - 0.12, hfx - 0.34
    zs = (spec.under_z + 0.02 + spec.floor_z + 0.015) / 2
    hs = spec.floor_z + 0.015 - (spec.under_z + 0.02)
    for s in (1, -1):
        extrusion(mb, (xa, s * spec.sill_y, zs), (xb, s * spec.sill_y, zs), 0.11, hs, 'x', 3, 0.0042, 0)
        # corner plates and bolts down the sill's top
        for k in range(14):
            x = xa + 0.12 + (xb - xa - 0.24) * k / 13
            mb.bolt((x, s * spec.sill_y, zs + hs / 2), Zv, 0.0068, 0.0056, 1, 1, True)
        for x in (xa, xb):
            mb.box((x + (0.012 if x == xa else -0.012), s * spec.sill_y, zs), 0.008, 0.124, hs + 0.012, 2)
    for x in (p["x1"] + 0.12, p["x0"] - 0.1):
        zc = spec.floor_z + 0.02
        extrusion(mb, (x, -spec.sill_y, zc), (x, spec.sill_y, zc), 0.08, 0.10, 'y', 2, 0.0042, 0, 0.007)
        for k in range(9):
            y = -spec.sill_y + 0.12 + (2 * spec.sill_y - 0.24) * k / 8
            mb.bolt((x, y, zc + 0.05), Zv, 0.0062, 0.005, 1, 1, True)
    # four pairs of body mounts along the sills: a bracket with a bolt
    for k in range(4):
        x = xa + 0.25 + (xb - xa - 0.5) * k / 3
        for s in (1, -1):
            mb.box((x, s * (spec.sill_y + 0.07), zs), 0.07, 0.05, 0.012, 0)
            mb.bolt((x, s * (spec.sill_y + 0.07), zs + 0.006), Zv, 0.008, 0.0065, 1, 1, True)
    out["floor"] = solid("XR_Frame_Floor", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Alu_Machined"]], coll, g, centre(mb), bevel=0.0035, bevel_seg=1, sys="chassis", id="floor")

    # ---- front subframe: a cast plate with lightening pockets, a rim, bosses, bushings with bolts at the lower-arm pickups
    g = group("XR_Frame_SubF_G", coll, (hfx, 0, 0.21), root, sys="chassis", id="subframe_f")
    mb = MB()
    zf = 0.215
    xr0, xr1 = hfx - 0.40, hfx + 0.38
    Lf, Wf = xr1 - xr0, 0.88
    cx = (xr0 + xr1) / 2
    zp0, zp1 = zf - 0.036, zf - 0.024
    holes = []
    for k in range(3):                                           # three big pockets along the car, two small beside the rack
        hx_ = xr0 + 0.10 + k * (Lf - 0.2) / 3
        holes.append(rrect((Lf - 0.2) / 3 - 0.07, 0.30, 0.05, 4, hx_ + ((Lf - 0.2) / 3 - 0.07) / 2, 0.20))
        holes.append(rrect((Lf - 0.2) / 3 - 0.07, 0.30, 0.05, 4, hx_ + ((Lf - 0.2) / 3 - 0.07) / 2, -0.20))
    mb.prism(rrect(Lf, Wf, 0.05, 5, cx, 0.0), holes, zp0, zp1, (0, 0, 0), Zv, 0)
    # the rim: a wall round the plate and round each pocket (cast ribs), tall at the pickups
    mb.prism(rrect(Lf, Wf, 0.05, 5, cx, 0.0), [rrect(Lf - 0.024, Wf - 0.024, 0.04, 5, cx, 0.0)], zp1, zf + 0.04, (0, 0, 0), Zv, 0)
    for hl in holes:
        mb.prism([(x * 1.0, y * 1.0) for (x, y) in _grow(hl, 0.012)], [hl], zp1, zf + 0.022, (0, 0, 0), Zv, 0)
    for s in (1, -1):                                            # rails below the plate, fore-and-aft, with bolt bosses at the ends
        extrusion(mb, (xr0, s * 0.40, zf - 0.065), (xr1, s * 0.40, zf - 0.065), 0.07, 0.05, 'x', 2, 0.005, 0, 0.006)
        for x in (xr0 + 0.02, xr1 - 0.02):
            mb.cyl((x, s * 0.40, zf - 0.095), (x, s * 0.40, zf - 0.04), 0.03, seg=18, mi=0)
            mb.bolt((x, s * 0.40, zf - 0.095), -Zv, 0.0105, 0.009, 1, 1, True)
    mb.box_between((hfx - 0.16, -0.40, zf + 0.04), (hfx - 0.16, 0.40, zf + 0.04), 0.06, 0.05, mi=0)    # the rack's cross-member
    for c in ("FL", "FR"):
        h = hardpoints(spec, c)
        for k in ("LF", "LR"):
            mb.box(Vector(h[k]) + Vector((0, -h["s"] * 0.03, 0)), 0.07, 0.06, 0.08, 0)
            _bush(mb, h[k], X, 0.026, 0.032, 2, 1, 1, False)
    for (x, y) in ((xr0 + 0.07, 0.0), (xr1 - 0.07, 0.0), (hfx - 0.16, 0.20), (hfx - 0.16, -0.20)):          # bolts on the plate
        mb.bolt((x, y, zp1), Zv, 0.0075, 0.006, 1, 1, True)
    D.bolt_line(mb, (xr0 + 0.05, -0.43, zf + 0.04), (xr1 - 0.05, -0.43, zf + 0.04), 7, Zv, 0.006, 0.005, 1, 1)
    D.bolt_line(mb, (xr0 + 0.05, 0.43, zf + 0.04), (xr1 - 0.05, 0.43, zf + 0.04), 7, Zv, 0.006, 0.005, 1, 1)
    out["sub_f"] = solid("XR_Frame_SubF", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, centre(mb), bevel=0.003, bevel_seg=1, sys="chassis", id="subframe_f")

    # ---- crash beam, front: an extrusion with crush cans (square tubes with a honeycomb of cells) and a bolted plate on each
    g = group("XR_Frame_CrashF_G", coll, (hfx + 0.6, 0, 0.45), root, sys="chassis", id="crash_f")
    mb = MB()
    xc = hfx + 0.60
    extrusion(mb, (xc, -0.74, 0.45), (xc, 0.74, 0.45), 0.09, 0.11, 'y', 3, 0.0045, 0, 0.008)
    for s in (1, -1):
        a, b = Vector((xc, s * 0.35, 0.43)), Vector((xr1 + 0.02, s * 0.35, 0.33))
        _can(mb, a, b, 0.085, 0.07, 3)
        mb.box(b + Vector((0.006, 0, 0)), 0.012, 0.13, 0.12, 0)
        D.bolt_ring(mb, b + Vector((0.012, 0, 0)), X, 0.045, 6, 0.0075, 0.006, 0.4, 1, 1)
    D.bolt_line(mb, (xc + 0.056, -0.66, 0.45), (xc + 0.056, 0.66, 0.45), 9, X, 0.0068, 0.0056, 1, 1)
    out["crash_f"] = solid("XR_Frame_CrashF", mb, [M["XR_Alu_Cast"], M["XR_Bolt"]], coll, g, centre(mb), bevel=0.003, bevel_seg=1, sys="chassis", id="crash_f")

    # ---- rear casting: a ribbed plate behind the pack, carrying the rear motors and the rear links
    xr_a, xr_b = hrx - 0.55, p["x0"] - 0.08
    wy = 0.72
    cx, L = (xr_a + xr_b) / 2, xr_b - xr_a
    g = group("XR_Frame_SubR_G", coll, (cx, 0, 0.2), root, sys="chassis", id="subframe_r")
    mb = MB()
    hl = []
    for cy in (-0.47, 0.47):
        hl.append([(cx + x, cy + y) for (x, y) in rrect(0.30, 0.20, 0.03)])
    mb.prism([(cx + x, y) for (x, y) in rrect(L, 2 * wy, 0.07)], hl, 0.195, 0.202, (0, 0, 0), Zv, 0)
    for y in (-0.12, 0.12, -0.34, 0.34):
        mb.box((cx, y, 0.2275), L - 0.06, 0.012, 0.055, 0)
    for k in range(4):
        mb.box((xr_a + 0.06 + k * (L - 0.12) / 3, 0, 0.2275), 0.012, 2 * wy - 0.1, 0.055, 0)
    mb.box((cx, wy - 0.01, 0.2275), L, 0.014, 0.06, 0)
    mb.box((cx, -wy + 0.01, 0.2275), L, 0.014, 0.06, 0)
    # diagonal ribs between the long ones: the casting's honeycomb
    for y0, y1 in ((-0.12, 0.12), (-0.34, -0.12), (0.12, 0.34)):
        for k in range(4):
            xa_ = xr_a + 0.06 + k * (L - 0.12) / 3
            xb_ = xr_a + 0.06 + (k + 1) * (L - 0.12) / 3
            if k < 3:
                mb.box_between((xa_, y0, 0.2275), (xb_, y1, 0.2275), 0.007, 0.05, up=Zv, mi=0)
                mb.box_between((xa_, y1, 0.2275), (xb_, y0, 0.2275), 0.007, 0.05, up=Zv, mi=0)
    for c in ("RL", "RR"):
        h = hardpoints(spec, c)
        for k in ("LF", "LR"):
            mb.box(Vector(h[k]) + Vector((0, 0, -0.01)), 0.07, 0.06, 0.07, 0)
            _bush(mb, h[k], X, 0.026, 0.032, 2, 1, 1, False)
        mb.box(Vector(h["TI"]) + Vector((0, 0, 0.0)), 0.05, 0.05, 0.05, 0)
    # the motor openings' bolt rings, and bolts along the ribs
    for cy in (-0.47, 0.47):
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                mb.bolt((cx + sx_ * 0.178, cy + sy_ * 0.118, 0.202), Zv, 0.0085, 0.007, 1, 1, True)
        for sx_ in (-0.5, 0, 0.5):
            for sy_ in (-1, 1):
                mb.bolt((cx + sx_ * 0.30 * 0.9, cy + sy_ * 0.118, 0.202), Zv, 0.0085, 0.007, 1, 1, True)
    for k in range(4):
        for y in (-0.24, 0.24):
            mb.bolt((xr_a + 0.06 + k * (L - 0.12) / 3, y, 0.2552), Zv, 0.007, 0.0058, 1, 1, True)
    out["sub_r"] = solid("XR_Frame_SubR", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, centre(mb), bevel=0.0025, bevel_seg=1, sys="chassis", id="subframe_r")

    # ---- crash beam, rear
    xe = spec.rear_x - 0.9
    g = group("XR_Frame_CrashR_G", coll, (xe, 0, 0.36), root, sys="chassis", id="crash_r")
    mb = MB()
    extrusion(mb, (xe, -0.70, 0.36), (xe, 0.70, 0.36), 0.09, 0.11, 'y', 3, 0.0045, 0, 0.008)
    for s in (1, -1):
        a, b = Vector((xe, s * 0.30, 0.34)), Vector((xr_a - 0.02, s * 0.30, 0.26))
        _can(mb, a, b, 0.085, 0.07, 3)
        mb.box(b + Vector((-0.006, 0, 0)), 0.012, 0.13, 0.12, 0)
        D.bolt_ring(mb, b + Vector((-0.012, 0, 0)), -X, 0.045, 6, 0.0075, 0.006, 0.4, 1, 1)
    D.bolt_line(mb, (xe - 0.056, -0.62, 0.36), (xe - 0.056, 0.62, 0.36), 9, -X, 0.0068, 0.0056, 1, 1)
    out["crash_r"] = solid("XR_Frame_CrashR", mb, [M["XR_Alu_Cast"], M["XR_Bolt"]], coll, g, centre(mb), bevel=0.003, bevel_seg=1, sys="chassis", id="crash_r")
    return out


def _grow(poly, d):
    """A polygon pushed outward by d about its centroid (enough for the convex rounded pockets used here)."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for (x, y) in poly:
        vx, vy = x - cx, y - cy
        L = math.hypot(vx, vy) or 1.0
        out.append((x + vx / L * d, y + vy / L * d))
    return out


def _can(mb, a, b, w, h, mi):
    """A crush can from a to b: a square tube with a honeycomb of cells showing at its open end (walls only: the front is the beam)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    u = d / L
    nx = 4
    mb.prism(rrect(h, w, 0.006), [rrect(h - 0.008, w - 0.008, 0.004)], 0.0, L, a, d, mi)
    for k in range(1, nx):
        yy = -w / 2 + w * k / nx
        mb.box_between(a + Vector((0, yy, 0)), b + Vector((0, yy, 0)), 0.003, h - 0.006, up=Zv, mi=mi)
    mb.box_between(a + Vector((0, 0, 0)), b + Vector((0, 0, 0)), w - 0.006, 0.003, up=Zv, mi=mi)
    # bead rings: the folds that start the crumple
    for t in (0.3, 0.55, 0.8):
        mb.prism(rrect(h + 0.006, w + 0.006, 0.007), [rrect(h - 0.002, w - 0.002, 0.005)], 0.0, 0.006, a + u * (L * t), d, mi)


def tower(spec, corner, coll, parent, M):
    """The shock tower over a wheel: a ribbed cone up to a bolted plate with a locking nut, braced to the sill. It rides with its corner."""
    h = hardpoints(spec, corner)
    top = h["ST"]
    base = Vector((top.x, top.y, 0.40))
    mb = MB()
    mb.cyl(base, top - Vector((0, 0, 0.012)), 0.105, 0.078, seg=32, mi=0)
    mb.cyl(top - Vector((0, 0, 0.012)), top, 0.098, seg=32, mi=0)
    # stamped bead rings round the cone and radial gusset ribs from the cone to a foot flange
    for t in (0.35, 0.62):
        zc = base.z + (top.z - 0.012 - base.z) * t
        r_ = 0.105 + (0.078 - 0.105) * t
        mb.torus(Vector((top.x, top.y, zc)), Zv, r_ + 0.001, 0.004, 32, 5, 0)
    mb.cyl(base - Vector((0, 0, 0.01)), base + Vector((0, 0, 0.004)), 0.135, seg=32, mi=0)
    for k in range(6):
        a = k * math.pi / 3 + 0.2
        c, s_ = math.cos(a), math.sin(a)
        p0 = Vector((top.x + c * 0.122, top.y + s_ * 0.122, base.z + 0.004))
        p1 = Vector((top.x + c * 0.0805, top.y + s_ * 0.0805, base.z + 0.075))
        mb.box_between(p0, p1, 0.007, 0.022, up=Vector((-s_, c, 0)), mi=0)
        mb.bolt(Vector((top.x + c * 0.119, top.y + s_ * 0.119, base.z + 0.004)), Zv, 0.007, 0.0058, 1, 1, True)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        q = top + Vector((0.07 * math.cos(a), 0.07 * math.sin(a), 0))
        mb.bolt(q, Zv, 0.0085, 0.0072, 1, 1, True)
    mb.cyl(top, top + Vector((0, 0, 0.006)), 0.036, seg=24, mi=0)
    mb.bolt(top + Vector((0, 0, 0.006)), Zv, 0.0135, 0.012, 1, 1, True)
    mb.box_between(Vector((top.x, top.y, 0.46)), Vector((top.x, h["s"] * spec.sill_y, spec.floor_z + 0.05)), 0.05, 0.05, mi=0)
    return solid("XR_Susp_%s_Tower" % corner, mb, [M["XR_Alu_Cast"], M["XR_Bolt"]], coll, parent, centre(mb), bevel=0.004, bevel_seg=1, sys="suspension", id="tower")
