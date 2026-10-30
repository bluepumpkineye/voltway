"""Brake calipers: one two-piece monobloc, built once for every car.

    build(collection, prefix, tag, lib, mats, cs, ca, span, disc_r, d_disc, th, rim_r)

The caliper straddles the disc, which passes through a slot between its two halves:

    outboard half   a plate over the disc's outer face, with raised pot covers (two lobes, or
                    three for a six-piston front) stepped twice, a low rib across the bridge
                    between them, two bolt heads, a hose fitting and two bleed screws
    inboard half    a plate behind the disc, hidden except at the ends
    bridge          joins the halves over the disc's edge (the "C" of a monobloc)
    pads            the friction material, a recessed plate either side of the disc, seen as a
                    dark line inside the slot at the caliper's two ends

so from the side the disc visibly goes into the caliper, which a solid block cannot show. The
body is the car's own "caliper" material (the showroom recolours it by name); bolts, screws and
the fitting are "caliper_hw", the pads "caliper_pad", which the swatches leave alone.

Every part's name holds "_Caliper_", which the exporters use to put it in the corner's caliper
node (it steers with the wheel but does not spin); a name without it spins with the wheel.

The envelope is the one the old slab had, so no face clears less than it did: the radial range
cs["r_inner"] .. min(disc_r + cs["r_out"], rim_r - cs["rim_clear"]), the outer surface cs["d_out"]
over the disc's face (covers cs["bulge"] higher), the back cs["d_in"] behind it. Frame: the
wheel's own (axle along Z, outboard positive); `ca` is the centre angle, `span` the half-angle.
Optional cs keys: lobes (2 or 3; lobes_rear for the rear axle), bevel (metres, 0.0022).
"""
import math

from .. import mesh as M


def _pol(ca, phi, r, z):
    a = ca + phi
    return (r * math.cos(a), r * math.sin(a), z)


def _line(p0, p1, step_deg=7.0):
    """(phi, r) points from p0 to p1, ends included, cut every `step_deg` of arc so a constant-radius
    edge stays an arc once it is x, y."""
    n = max(1, int(math.ceil(abs(math.degrees(p1[0] - p0[0])) / step_deg)))
    return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]


def _join(*runs):
    out = []
    for run in runs:
        for p in run:
            if not out or abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
                out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9:
        out.pop()
    return out


def _octagon(pc, rc, hp, hr, kp, kr):
    """A chamfered rectangle round (phi, r) = (pc, rc), half-sizes hp (radians) and hr (metres), the
    corners cut by kp and kr: the outline of a pot cover. Its radial edges are arcs."""
    return _join(
        _line((pc - hp + kp, rc - hr), (pc + hp - kp, rc - hr)),
        _line((pc + hp - kp, rc - hr), (pc + hp, rc - hr + kr)),
        _line((pc + hp, rc - hr + kr), (pc + hp, rc + hr - kr)),
        _line((pc + hp, rc + hr - kr), (pc + hp - kp, rc + hr)),
        _line((pc + hp - kp, rc + hr), (pc - hp + kp, rc + hr)),
        _line((pc - hp + kp, rc + hr), (pc - hp, rc + hr - kr)),
        _line((pc - hp, rc + hr - kr), (pc - hp, rc - hr + kr)),
        _line((pc - hp, rc - hr + kr), (pc - hp + kp, rc - hr)))


def _plate(span, r0, r1, c):
    """The sector's outline with its four corners cut by c metres."""
    cp0, cp1 = c / r0, c / r1
    return _join(
        _line((-span + cp0, r0), (span - cp0, r0)),
        [(span - cp0, r0), (span, r0 + c), (span, r1 - c), (span - cp1, r1)],
        _line((span - cp1, r1), (-span + cp1, r1)),
        [(-span + cp1, r1), (-span, r1 - c), (-span, r0 + c)])


def _prism(ca, loop, z0, z1):
    """Vertices and faces of the closed prism over a (phi, r) loop, from z0 up to z1 (normals are
    fixed for the whole mesh afterwards)."""
    n = len(loop)
    verts = [_pol(ca, p, r, z1) for (p, r) in loop] + [_pol(ca, p, r, z0) for (p, r) in loop]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def _tube(base, axis, radius, length, n=8, tip=0.0):
    """A cylinder (a hex bolt head for n = 6) from `base` along the unit vector `axis`; `tip` pulls the top
    ring in by that fraction of the radius, a chamfer."""
    ax, ay, az = axis
    # any vector not parallel to the axis, then two perpendiculars
    ref = (0.0, 0.0, 1.0) if abs(az) < 0.9 else (1.0, 0.0, 0.0)
    ux, uy, uz = ay * ref[2] - az * ref[1], az * ref[0] - ax * ref[2], ax * ref[1] - ay * ref[0]
    ul = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / ul, uy / ul, uz / ul
    vx, vy, vz = ay * uz - az * uy, az * ux - ax * uz, ax * uy - ay * ux
    verts = []
    for (d, k) in ((0.0, 1.0), (length, 1.0 - tip)):
        for i in range(n):
            t = 2.0 * math.pi * i / n
            c, s = math.cos(t) * radius * k, math.sin(t) * radius * k
            verts.append((base[0] + ax * d + ux * c + vx * s,
                          base[1] + ay * d + uy * c + vy * s,
                          base[2] + az * d + uz * c + vz * s))
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return verts, faces


def _object(name, parts, collection, mat, smooth):
    import bmesh
    v, f = M.merge_parts(parts)
    ob = M.obj(name, v, f, collection, mat, smooth=smooth)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def build(collection, prefix, tag, lib, mats, cs, ca, span, disc_r, d_disc, th, rim_r):
    """The caliper's objects (body, hardware, pads), unparented; see the module docstring."""
    r0 = cs["r_inner"] if "r_inner" in cs else disc_r - cs.get("r_in", 0.058)
    r1 = min(disc_r + cs.get("r_out", 0.020), rim_r - cs.get("rim_clear", 0.034))
    z_top = d_disc + cs.get("d_out", 0.046)            # the outboard plate's outer face
    z_cover = z_top + cs.get("bulge", 0.012)           # the highest the covers go
    z_back = d_disc - cs.get("d_in", 0.080)
    z_slot_hi = d_disc + 0.004                         # the slot the disc runs in, 4 mm clear each side
    z_slot_lo = d_disc - th - 0.004
    rb = r1 - 0.009                                    # the plate's outer edge; bleed screws go the rest
    rbridge = min(disc_r + 0.003, rb - 0.010)          # the bridge's inner edge, just over the disc's rim
    rc = 0.5 * (r0 + rb)
    hr = 0.5 * (rb - r0)
    lobes = int(cs.get("lobes_rear", cs.get("lobes", 2)) if tag.startswith("R") else cs.get("lobes", 2))
    c = 0.007                                          # corner cut of the plates

    # ---- the body: plates, bridge, rib, covers in two steps
    plate = _plate(span, r0, rb, c)
    parts = [
        _prism(ca, plate, z_slot_hi, z_top),                              # outboard half
        _prism(ca, plate, z_back, z_slot_lo),                             # inboard half
        _prism(ca, _plate(span, rbridge, rb, c), z_back, z_top),          # the bridge over the disc's rim
    ]
    # lobes: centre and half-width as fractions of the half-span
    if lobes == 3:
        centres, half = (-0.665, 0.0, 0.665), 0.245
    else:
        centres, half = (-0.50, 0.50), 0.375
    rib = 0.0
    for pc in centres:
        hp = half * span
        kp, kr = 0.20 * hp, 0.20 * (hr - 0.007)
        outline = _octagon(pc * span, rc, hp, hr - 0.007, kp, kr)
        parts.append(_prism(ca, outline, z_top - 0.002, z_cover - 0.0016))
        # a second, smaller step on top, the panel's inset
        inner = _octagon(pc * span, rc, 0.70 * hp, 0.66 * (hr - 0.007), 0.70 * kp, 0.66 * kr)
        parts.append(_prism(ca, inner, z_cover - 0.0028, z_cover))
    # the rib across each gap between covers (and the end margins stay at plate height)
    gaps = [0.5 * (centres[i] + centres[i + 1]) for i in range(len(centres) - 1)]
    for g in gaps:
        w = 0.5 * ((centres[1] - centres[0]) - 2.0 * half) * 0.62 * span
        rib_loop = _octagon(g * span, rc, w, hr - 0.012, 0.3 * w, 0.006)
        parts.append(_prism(ca, rib_loop, z_top - 0.002, z_top + 0.0045))
    body = _object(prefix + "Caliper_" + tag, parts, collection, lib[mats["caliper"]], True)
    M.bevel(body, cs.get("bevel", 0.0022), 2, 35, harden=True)
    made = [body]

    # ---- hardware: a bolt head at each end, the hose fitting on the rib, two bleed screws on the outer edge
    hw = []
    for sgn in (-1.0, 1.0):
        x, y, _ = _pol(ca, sgn * 0.935 * span, rc, 0.0)
        hw.append(_tube((x, y, z_top - 0.001), (0.0, 0.0, 1.0), 0.0050, 0.0058, n=6, tip=0.12))
    x, y, _ = _pol(ca, 0.0, rb - 0.016, 0.0)
    hw.append(_tube((x, y, z_top + 0.002), (0.0, 0.0, 1.0), 0.0045, 0.0080, n=10, tip=0.18))
    for pc in (centres[0], centres[-1]):
        a = ca + pc * span
        x, y, _ = _pol(ca, pc * span, rb - 0.002, 0.0)
        z = 0.5 * (z_slot_hi + z_top)
        hw.append(_tube((x, y, z), (math.cos(a), math.sin(a), 0.0), 0.0050, 0.0030, n=6))
        hw.append(_tube((x + math.cos(a) * 0.003, y + math.sin(a) * 0.003, z),
                        (math.cos(a), math.sin(a), 0.0), 0.0028, 0.0065, n=8, tip=0.25))
    made.append(_object(prefix + "Caliper_Hw_" + tag, hw, collection, lib[mats.get("hw", "caliper_hw")], True))

    # ---- pads: a dark plate either side of the disc, set back so the slot shows a dark line at the ends
    pad_loop = _plate(0.925 * span, r0 + 0.012, rb - 0.016, 0.004)
    pads = [_prism(ca, pad_loop, d_disc + 0.0004, z_slot_hi - 0.0004),
            _prism(ca, pad_loop, z_slot_lo + 0.0004, d_disc - th - 0.0004)]
    made.append(_object(prefix + "Caliper_Pad_" + tag, pads, collection, lib[mats.get("pad", "caliper_pad")], False))
    return made
