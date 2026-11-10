"""Shared hardware for the anatomy parts: bolt rings, hose clamps, barbed fittings, corrugated hoses, HV connectors, labels.

All of it adds faces to an `MB` (prim.py) in WORLD coordinates and takes the material INDEX of the mesh it goes into, so a
part decides its own slots (its `solid(..., mats)` list) and passes the indices in.
"""
import math

from mathutils import Vector

from .prim import MB, X, Y, Z, ccw, frame_q, gear_outline, round_path

# the label atlas (texgen.labels): cell (column, row)
LABEL = {"hv": (0, 0), "qr": (1, 0), "bar": (2, 0), "plate": (3, 0), "flow": (0, 1), "earth": (1, 1), "hazard": (2, 1), "hot": (3, 1)}


def label_rect(name, inset=0.006):
    i, j = LABEL[name]
    return (i / 4 + inset, j / 4 + inset, (i + 1) / 4 - inset, (j + 1) / 4 - inset)


def ring_basis(axis):
    """Two unit vectors perpendicular to `axis` (and to each other)."""
    q = frame_q(axis)
    return q @ X, q @ Y


def bolt_ring(mb, centre, axis, R, n, r=0.0065, h=0.0055, phase=0.0, mi=0, mi_w=None, washer=True):
    """`n` hex bolts on a circle of radius R about `axis`, heads pointing along it."""
    ex, ey = ring_basis(axis)
    c = Vector(centre)
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        mb.bolt(c + (ex * math.cos(a) + ey * math.sin(a)) * R, axis, r, h, mi, mi_w, washer)


def bolt_line(mb, a, b, n, axis, r=0.0065, h=0.0055, mi=0, mi_w=None, washer=True):
    a, b = Vector(a), Vector(b)
    for i in range(n):
        t = i / max(1, n - 1)
        mb.bolt(a + (b - a) * t, axis, r, h, mi, mi_w, washer)


def clamp(mb, c, axis, R, mi_band, mi_screw, w=0.011):
    """A hose clamp: a thin steel band round a hose of radius R with a screw housing."""
    q = frame_q(axis)
    c = Vector(c)
    d = Vector(axis).normalized()
    mb.cyl(c - d * (w / 2), c + d * (w / 2), R + 0.0016, seg=24, mi=mi_band, caps=False)
    side = q @ X
    mb.box(c + side * (R + 0.007), 0.012, w * 0.7, 0.008, mi_screw, q)
    mb.cyl(c + side * (R + 0.007) - (q @ Y) * 0.005, c + side * (R + 0.007) + (q @ Y) * 0.005, 0.0032, seg=6, mi=mi_screw)


def fitting(mb, p0, p1, r, mi_body, mi_ring, barbs=2):
    """A barbed hose fitting from p0 to p1: a body, a flange at p0 and `barbs` rings along the nose."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    L = d.length
    u = d / L
    mb.cyl(p0, p0 + u * L * 0.28, r * 1.45, seg=14, mi=mi_body)
    mb.cyl(p0 + u * L * 0.28, p1, r, seg=14, mi=mi_body)
    for k in range(barbs):
        t = 0.45 + 0.4 * k / max(1, barbs)
        mb.cyl(p0 + u * L * t, p0 + u * L * (t + 0.16), r * 1.22, r * 0.98, seg=14, mi=mi_ring)
    mb.torus(p0 + u * L * 0.28, u, r * 1.2, r * 0.18, 16, 5, mi_ring)


def corrugated(path, r, amp, pitch, n_per=4):
    """Resample a polyline and give each sample a radius that rises and falls with the distance along it (a convoluted hose or
    bellows): returns (points, radii) for `MB.tube`."""
    pts = [Vector(p) for p in path]
    out, rs = [], []
    run = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = (b - a).length
        n = max(1, int(L / (pitch / n_per)))
        for k in range(n):
            t = k / n
            out.append(a + (b - a) * t)
            rs.append(r + amp * (0.5 - 0.5 * math.cos(2 * math.pi * (run + L * t) / pitch)))
        run += L
    out.append(pts[-1])
    rs.append(r + amp * (0.5 - 0.5 * math.cos(2 * math.pi * run / pitch)))
    return out, rs


def hose(mb, pts, r, mi, bend=0.04, seg=12, corrugate=None, caps=True):
    """A rounded-corner hose through `pts`; `corrugate=(amp, pitch)` makes it convoluted."""
    path = round_path(pts, bend, 6)
    if corrugate:
        path, rs = corrugated(path, r, corrugate[0], corrugate[1])
        mb.tube(path, rs, seg=seg, mi=mi, caps=caps)
    else:
        mb.tube(path, r, seg=seg, mi=mi, caps=caps)


def hv_connector(mb, p, axis, mi_body, mi_lever, mi_metal, mi_black, scale=1.0, lever_dir=None):
    """A round high-voltage connector standing on a surface at `p`, pointing along `axis`: a flange with four screws, a seal, an
    orange body, a knurled coupling ring, a locking lever and a shielded nose."""
    s = scale
    u = Vector(axis).normalized()
    ex, ey = ring_basis(axis)
    p = Vector(p)
    mb.cyl(p, p + u * 0.007 * s, 0.040 * s, seg=20, mi=mi_black)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        mb.bolt(p + (ex * math.cos(a) + ey * math.sin(a)) * 0.0315 * s + u * 0.007 * s, u, 0.0032 * s, 0.003 * s, mi_metal, mi_metal, False)
    mb.torus(p + u * 0.0085 * s, u, 0.027 * s, 0.0018 * s, 24, 5, mi_black)
    mb.cyl(p + u * 0.007 * s, p + u * 0.030 * s, 0.025 * s, seg=24, mi=mi_body)
    # knurled coupling ring
    mb.prism(ccw(gear_outline(0.0285 * s, 0.0315 * s, 22)), [], 0.030 * s, 0.046 * s, p, u, mi_metal)
    mb.cyl(p + u * 0.046 * s, p + u * 0.050 * s, 0.027 * s, seg=24, mi=mi_metal)
    mb.cyl(p + u * 0.050 * s, p + u * 0.062 * s, 0.021 * s, seg=24, mi=mi_body)
    mb.cyl(p + u * 0.062 * s, p + u * 0.064 * s, 0.0165 * s, seg=20, mi=mi_black)
    # locking lever
    ld = Vector(lever_dir).normalized() if lever_dir is not None else ex
    mb.box_between(p + u * 0.034 * s + ld * 0.0, p + u * 0.034 * s + ld * 0.052 * s, 0.014 * s, 0.006 * s, up=u, mi=mi_lever)
    mb.box(p + u * 0.034 * s + ld * 0.052 * s, 0.010 * s, 0.020 * s, 0.010 * s, mi_lever)
    return p + u * 0.064 * s


def sticker(mb, c, right, up, w, h, name, mi, lift=0.0):
    mb.sticker(c, right, up, w, h, label_rect(name), mi, lift)


def fin_bank(mb, c, n, pitch, length, width, h, along, mi, t=0.0028):
    """`n` straight fins centred on `c`, spaced `pitch` apart across `across`... along X or Y: `along` = 'x' (fins run along x, stacked in y)."""
    c = Vector(c)
    for k in range(n):
        off = (k - (n - 1) / 2) * pitch
        if along == 'x':
            mb.box(c + Vector((0, off, 0)), length, t, h, mi)
        else:
            mb.box(c + Vector((off, 0, 0)), t, length, h, mi)


def flat_prof(h, w, r=0.0):
    """A rectangle profile for MB.sweep: x (the frame's up-ish normal) is `h` tall, y is `w` wide."""
    a, b = h / 2, w / 2
    return [(-a, -b), (a, -b), (a, b), (-a, b)]
