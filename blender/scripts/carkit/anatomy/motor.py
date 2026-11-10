"""A drive unit: casing, stator, rotor, reducer with its gears, and the inverter on top.

Sized from the motor's torque (stator diameter and stack length scale with its cube root), so a
bigger motor is a bigger part. The rotor is a laminated core with eight V-pairs of magnets
(alternate poles in two materials, so the web can colour north and south), a splined shaft, bearings, a resolver
ring and one end plate; the other end stays open so the magnets show when the rotor is drawn out. The stator is a
slotted lamination stack with a copper winding that comes out of the slots as woven hairpin crowns, welded at the tips.

Axis: the motor and the output shaft lie along Y. `sgn` +1 puts the unit on the left (and the
front, centred), -1 on the right; the reducer is always on the outboard side. The output axis
passes through the wheel's hub centre, so the half-shaft is a straight line to the hub.
Rear units are parallel-axis (pinion and output gear, the motor offset behind and above the
output); the front unit is coaxial with a planetary stage.
"""
import math

from mathutils import Matrix, Vector

from . import detail as D
from .prim import MB, X, Y, Z, ccw, circle, frame_q, gear_outline, group, round_path, solid


def centre(mb):
    xs = [v[0] for v in mb.v]
    ys = [v[1] for v in mb.v]
    zs = [v[2] for v in mb.v]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)


def sizes(m):
    k = (m.nm / 635.0) ** (1.0 / 3.0)
    Ro = 0.095 * k
    return dict(k=k, Ro=Ro, Rc=Ro + 0.014, Ls=0.21 * k, Rr=0.56 * Ro, rs=0.016 * k)


def _basis(axis):
    q = frame_q(axis)
    return q, q @ X, q @ Y


def _radial_box(mb, centre_pt, ex, ey, ax, ang, rad, tang, length, mi, r_mid):
    """A box at radius r_mid and angle `ang` (about `ax`) with its long side axial."""
    r_hat = ex * math.cos(ang) + ey * math.sin(ang)
    t_hat = ax.cross(r_hat)
    M = Matrix((r_hat, t_hat, ax)).transposed()
    mb.box(Vector(centre_pt) + r_hat * r_mid, rad, tang, length, mi, M.to_quaternion())


def build(spec, motor, coll, root, M):
    """Build one motor's unit. Returns {'group', 'casing', 'stator', 'rotor', 'reducer', 'gears', 'inverter', ...}."""
    S = sizes(motor)
    k, Ro, Rc, Ls, Rr, rs = S["k"], S["Ro"], S["Rc"], S["Ls"], S["Rr"], S["rs"]
    left = motor.side != "right"
    sgn = 1.0 if left else -1.0
    front = motor.axle == "front"
    # one motor across the axle (either axle): coaxial with the half-shafts, centred, a planetary stage on its left
    coax = motor.side is None
    hx, hy, hz = spec.hub_f if front else spec.hub_r
    ax = Vector((0, sgn, 0))
    q, ex, ey = _basis(ax)

    # where the motor sits relative to the output axis (through the hub centre)
    if coax:
        off = Vector((0.0, 0.0, 0.0))
        ym = 0.0
    else:
        off = Vector((-0.06, 0.0, 0.08)) * k
        ym = 0.17
    O = Vector((hx, sgn * (0.0 if coax else ym), hz))       # on the output axis, at the motor's y
    Cm = Vector((hx + off.x, sgn * ym if not coax else 0.0, hz + off.z))   # motor centre
    uid = motor.id
    g = group("XR_Drive_%s" % uid, coll, tuple(Cm), root, sys="drive", id=uid, kw=motor.kw, nm=motor.nm, rpm=motor.rpm)
    out = {"group": g, "centre": tuple(Cm), "sizes": S, "ax": tuple(ax)}

    def at(d):
        return Cm + ax * d

    def radial(a):
        return ex * math.cos(a) + ey * math.sin(a)

    # ---- casing -------------------------------------------------------------------
    # materials: Casing 0, Alu_Machined 1, Coolant 2, Bolt 3, Rubber 4, Label 5, Plastic_Black 6, Alu_Cast 7
    d0, d1 = -(Ls / 2 + 0.02), Ls / 2 + 0.012
    mb = MB()
    mb.lathe([(Ro + 0.0008, d0), (Rc, d0), (Rc, d1), (Ro + 0.0008, d1), (Ro + 0.0008, d0)], Cm, ax, 64, 0)
    # the water jacket's rings: thin ones between wide, chamfered ones
    span = d1 - d0 - 0.03
    for i in range(9):
        d = d0 + 0.012 + i * span / 8
        wide = i % 4 == 0
        w = 0.011 if wide else 0.005
        h = 0.0085 if wide else 0.0055
        mb.lathe([(Rc, d), (Rc + h * 0.6, d), (Rc + h, d + w * 0.25), (Rc + h, d + w * 0.75), (Rc + h * 0.6, d + w), (Rc, d + w)], Cm, ax, 64, 0)
    for a_i in range(10):                         # axial ribs between the rings
        a = 2 * math.pi * a_i / 10 + 0.15
        if a_i in (2, 7):
            continue
        r_hat = radial(a)
        mb.box_between(Cm + ax * (d0 + 0.02) + r_hat * (Rc + 0.002), Cm + ax * (d1 - 0.02) + r_hat * (Rc + 0.002), 0.006, 0.004, up=r_hat, mi=0)
    # the rear end bell: a stepped cap, bolt ring, seal and the resolver plug
    mb.cyl(at(d0 - 0.028), at(d0), Rc - 0.002, seg=56, mi=0)
    mb.lathe([(0.0, d0 - 0.047), (0.044 * k + 0.004, d0 - 0.047), (0.044 * k + 0.006, d0 - 0.043), (0.044 * k + 0.006, d0 - 0.028)], Cm, ax, 40, 1)
    mb.torus(at(d0 - 0.0285), ax, Rc - 0.012, 0.0028, 40, 6, 4)
    D.bolt_ring(mb, at(d0 - 0.028), -ax, Rc - 0.022, 8, 0.0062, 0.005, 0.1, 3, 3)
    pcs = Cm + ax * (d0 - 0.028) + radial(math.pi * 0.5 - 0.35) * (Rc - 0.04)
    mb.box(pcs + ex * 0.0, 0.034, 0.018, 0.026, 6, None)
    mb.box(pcs + ax * (-0.005) + Vector((0, 0, 0.014)), 0.026, 0.012, 0.006, 6, None)
    # the front flange (to the reducer): a plate with a ring of bolts and two dowels
    mb.lathe([(Ro * 0.6, d1), (Rc + 0.012, d1), (Rc + 0.012, d1 + 0.012), (Ro * 0.6, d1 + 0.012), (Ro * 0.6, d1)], Cm, ax, 64, 1)
    D.bolt_ring(mb, at(d1 + 0.012), ax, Rc + 0.0, 12, 0.0072, 0.0058, 0.05, 3, 3)
    for a in (0.9, 0.9 + math.pi):
        p = Cm + radial(a) * (Rc + 0.004)
        mb.cyl(p + ax * (d1 + 0.012), p + ax * (d1 + 0.021), 0.0045, seg=10, mi=1)
    # the feet: a base plate with gussets, four bolts and a data plate
    zb = -Rc - 0.008
    mb.box(Cm + Vector((0, 0, zb)), 0.17, Ls * 0.98, 0.02, 7)
    for sx in (1, -1):
        for sy in (1, -1):
            mb.bolt(Cm + Vector((sx * 0.062, sy * Ls * 0.4, zb + 0.01)), Vector((0, 0, 1)), 0.0082, 0.0066, 3, 3, True)
        mb.box_between(Cm + Vector((sx * 0.08, 0, zb + 0.01)), Cm + Vector((sx * 0.035, 0, -Rc * 0.6)), 0.02, 0.014, up=Y, mi=7)
    D.sticker(mb, Cm + Vector((0.0, sgn * 0.0, zb)) + Vector((0.0855, 0.0, 0.0)), Vector((0, 1, 0)), Z, 0.07, 0.016, "plate", 5)
    # the coolant ports on top: barbed fittings, a hose elbow and clamps
    for s2 in (-1, 1):
        base = Cm + Vector((s2 * 0.045, 0, Rc + 0.004))
        D.fitting(mb, base, base + Vector((0, 0, 0.036)), 0.0105, 1, 1)
        hose_pts = [base + Vector((0, 0, 0.026)), base + Vector((0, 0, 0.056)), base + Vector((s2 * 0.03, 0, 0.074))]
        mb.tube(round_path(hose_pts, 0.018, 6), 0.0125, seg=14, mi=2)
        D.clamp(mb, base + Vector((0, 0, 0.034)), Vector((0, 0, 1)), 0.0122, 1, 1)
    out["casing"] = solid("XR_Drive_%s_Casing" % uid, mb,
                          [M["XR_Casing"], M["XR_Alu_Machined"], M["XR_Coolant"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Plastic_Black"], M["XR_Alu_Cast"]],
                          coll, g, Cm, bevel=0.0, sys="drive", id="casing", unit=uid)

    # ---- stator -------------------------------------------------------------------
    # materials: Lamination 0, Copper_U 1, Copper_V 2, Copper_W 3, Brass 4 (the welded tips), Steel 5
    Rb = Rr + 0.0015
    Rs = Ro - 0.018
    n_sl = 48
    th = 2 * math.pi / n_sl
    bore = []
    for i in range(n_sl):
        a = i * th
        bore += [(Rb * math.cos(a), Rb * math.sin(a)), (Rb * math.cos(a + 0.5 * th), Rb * math.sin(a + 0.5 * th)),
                 (Rs * math.cos(a + 0.5 * th), Rs * math.sin(a + 0.5 * th)), (Rs * math.cos(a + th), Rs * math.sin(a + th))]
    mb = MB()
    mb.prism(circle(Ro, 96), [bore], -Ls / 2, Ls / 2, Cm, ax, 0)
    rm = (Rb + Rs) / 2
    for i in range(n_sl):
        a = i * th + 0.75 * th
        ph = 1 + (i % 3)          # the three phases, U V W, in separate materials so the clip can light them in turn
        _radial_box(mb, Cm, ex, ey, ax, a, Rs - Rb - 0.002, 0.4 * th * rm, Ls + 0.006, ph, rm)
        # the hairpin crowns: two layers, woven in opposite senses on the two ends, a bright welded tip on each
        for sd in (-1, 1):
            for layer, (dr, twist) in enumerate(((-0.0050, 1.0), (0.0050, -1.0))):
                d_a = sd * (Ls / 2 + 0.003)
                d_b = sd * (Ls / 2 + 0.026 + 0.0018 * layer)
                a2 = a + sd * twist * 3.0 * th
                p0 = Cm + ax * d_a + radial(a) * (rm + dr)
                p1 = Cm + ax * d_b + radial(a2) * (rm + dr)
                mb.box_between(p0, p1, 0.0046, 0.0062, up=radial(a), mi=ph)
                mb.box(p1 + ax * (0.0008 * sd), 0.0062, 0.0062, 0.0042, 4, (Matrix((radial(a2), ax.cross(radial(a2)), ax)).transposed().to_quaternion()))
    for sd in (-1, 1):                                                       # the winding's retaining ring at each end
        mb.lathe([(Rb + 0.003, sd * (Ls / 2 + 0.030)), (Rs - 0.002, sd * (Ls / 2 + 0.030)), (Rs - 0.002, sd * (Ls / 2 + 0.0336)), (Rb + 0.003, sd * (Ls / 2 + 0.0336))], Cm, ax, 64, 5)
    for a_i in range(6):                                                     # tie bars through the stack
        a = 2 * math.pi * a_i / 6 + 0.1
        p = Cm + radial(a) * (Ro - 0.0035)
        mb.cyl(p + ax * (-Ls / 2 - 0.008), p + ax * (Ls / 2 + 0.008), 0.0034, seg=8, mi=5)
    out["stator"] = solid("XR_Drive_%s_Stator" % uid, mb, [M["XR_Lamination"], M["XR_Copper_U"], M["XR_Copper_V"], M["XR_Copper_W"], M["XR_Brass"], M["XR_Steel"]],
                          coll, g, Cm, bevel=0.0, sys="drive", id="stator", unit=uid)

    # ---- rotor --------------------------------------------------------------------
    # materials: Lamination 0, Magnet_N 1, Magnet_S 2, Shaft 3, Alu_Machined 4, Steel 5
    n_p = 8
    holes = [circle(rs, 24)]
    mags = []
    r_in, r_out, delta, t = 0.55 * Rr, 0.88 * Rr, math.radians(17), 0.0045 * k
    for p in range(n_p):
        phi = 2 * math.pi * p / n_p + math.pi / n_p
        A = (r_in * math.cos(phi), r_in * math.sin(phi))
        for sd in (-1, 1):
            B = (r_out * math.cos(phi + sd * delta), r_out * math.sin(phi + sd * delta))
            dx, dy = B[0] - A[0], B[1] - A[1]
            L2 = math.hypot(dx, dy)
            nx, ny = -dy / L2, dx / L2
            holes.append(ccw([(A[0] - nx * t / 2, A[1] - ny * t / 2), (A[0] + nx * t / 2, A[1] + ny * t / 2),
                              (B[0] + nx * t / 2, B[1] + ny * t / 2), (B[0] - nx * t / 2, B[1] - ny * t / 2)]))
            f = 0.86
            Am = (A[0] + dx * (1 - f) / 2, A[1] + dy * (1 - f) / 2)
            Bm = (B[0] - dx * (1 - f) / 2, B[1] - dy * (1 - f) / 2)
            tt = t * 0.78
            mags.append((p % 2, ccw([(Am[0] - nx * tt / 2, Am[1] - ny * tt / 2), (Am[0] + nx * tt / 2, Am[1] + ny * tt / 2),
                                      (Bm[0] + nx * tt / 2, Bm[1] + ny * tt / 2), (Bm[0] - nx * tt / 2, Bm[1] - ny * tt / 2)])))
    mb = MB()
    mb.prism(circle(Rr, 96), holes, -Ls / 2, Ls / 2, Cm, ax, 0)
    for pol, rect in mags:
        mb.prism(rect, [], -Ls * 0.49, Ls * 0.49, Cm, ax, 1 + pol)
    # shaft: bearing seats, bearings and a splined output end
    sd0, sd1 = -Ls / 2 - 0.075 * k, Ls / 2 + 0.2 * k
    mb.cyl(at(sd0), at(sd1), rs, seg=24, mi=3)
    for dd in (sd0 + 0.004, Ls / 2 + 0.018):                                  # a bearing at each end: races and a ring of balls
        w = 0.016
        mb.lathe([(rs * 1.02, dd), (rs * 1.55, dd), (rs * 1.55, dd + w), (rs * 1.02, dd + w)], Cm, ax, 40, 5)
        mb.lathe([(rs * 2.05, dd), (rs * 2.2, dd), (rs * 2.2, dd + w), (rs * 2.05, dd + w)], Cm, ax, 40, 5)
        for bI in range(10):
            a = 2 * math.pi * bI / 10
            mb.sphere(Cm + ax * (dd + w / 2) + radial(a) * (rs * 1.8), rs * 0.22, 6, 4, 4)
    mb.lathe([(rs * 1.02, Ls / 2 + 0.04), (rs * 1.35, Ls / 2 + 0.04), (rs * 1.35, Ls / 2 + 0.050), (rs * 1.02, Ls / 2 + 0.050)], Cm, ax, 32, 5)    # a retaining nut
    mb.prism(ccw(gear_outline(rs * 1.55, rs * 1.9, 24)), [circle(rs * 1.0, 20)], sd0 + 0.024, sd0 + 0.030, Cm, ax, 5)                               # the resolver's toothed ring
    spl = []
    ds = sd1 - 0.07 * k
    for i in range(14):
        spl.append((rs * (1.0 if i % 2 == 0 else 0.9), ds + i * 0.005))
    mb.lathe(spl, Cm, ax, 24, 3)
    # the one end plate, with balance holes and a ring of drilled lightening holes
    ep = [circle(0.025 * k + 0.0001, 6, cx=0.7 * Rr * math.cos(2 * math.pi * i / 8), cy=0.7 * Rr * math.sin(2 * math.pi * i / 8)) for i in range(8)]
    mb.prism(circle(0.98 * Rr, 64), [circle(rs * 1.1, 24)] + ep, Ls / 2, Ls / 2 + 0.007, Cm, ax, 4)
    D.bolt_ring(mb, at(Ls / 2 + 0.007), ax, 0.84 * Rr, 8, 0.0036, 0.003, 0.2, 5, 5, False)
    out["rotor"] = solid("XR_Drive_%s_Rotor" % uid, mb,
                         [M["XR_Lamination"], M["XR_Magnet_N"], M["XR_Magnet_S"], M["XR_Shaft"], M["XR_Alu_Machined"], M["XR_Steel"]],
                         coll, g, Cm, bevel=0.0, sys="drive", id="rotor", unit=uid)

    # ---- reducer and gears --------------------------------------------------------
    # reducer materials: Alu_Cast 0, Alu_Machined 1, Bolt 2, Casing 3, Rubber 4
    dr0 = d1 + 0.012
    mb = MB()
    gb = MB()      # the rest of the gears (the output side)
    gp = MB()      # what turns with the rotor: the pinion, or the sun
    gpiv = Cm      # the output gear turns about the half-shaft's axis (the planetary's about the motor's)
    if coax:
        # planetary stage, coaxial: a drum round the shaft, a ring gear, three planets and a sun
        Rd = Rc + 0.012
        mb.lathe([(Rd - 0.012, dr0), (Rd, dr0), (Rd, dr0 + 0.085), (Rd - 0.012, dr0 + 0.085), (Rd - 0.012, dr0)], Cm, ax, 64, 0)
        mb.cyl(at(dr0 + 0.085), at(dr0 + 0.097), Rd, seg=64, mi=0)
        mb.cyl(at(dr0 + 0.097), at(dr0 + 0.13), 0.04, seg=32, mi=1)
        mb.torus(at(dr0 + 0.126), ax, 0.043, 0.0026, 32, 5, 4)
        D.bolt_ring(mb, at(dr0 + 0.085), ax, Rd - 0.004, 10, 0.0068, 0.0055, 0.0, 2, 2)
        D.bolt_ring(mb, at(dr0 + 0.0), ax, Rd - 0.004, 10, 0.0068, 0.0055, 0.3, 2, 2)
        for i in range(12):                                                  # radial ribs on the drum
            a = 2 * math.pi * i / 12 + 0.26
            r_hat = radial(a)
            mb.box_between(Cm + ax * (dr0 + 0.014) + r_hat * (Rd + 0.003), Cm + ax * (dr0 + 0.074) + r_hat * (Rd + 0.003), 0.007, 0.0045, up=r_hat, mi=0)
        p = Cm + radial(1.2) * (Rd + 0.0) + ax * (dr0 + 0.04)               # a fill plug
        mb.bolt(p, radial(1.2), 0.0085, 0.0075, 2, 2, True)
        ring = ccw(gear_outline(0.074, 0.082, 38))
        gb.prism(circle(0.098, 64), [ring], dr0 + 0.02, dr0 + 0.055, Cm, ax, 0, twist=-0.10, steps=3)
        gp.prism(ccw(gear_outline(0.020, 0.026, 12)), [circle(rs * 1.05, 20)], dr0 + 0.02, dr0 + 0.055, Cm, ax, 0, twist=0.22, steps=3)
        for i in range(3):
            a = 2 * math.pi * i / 3 + 0.5
            c = (0.048 * math.cos(a), 0.048 * math.sin(a))
            gb.prism(ccw([(c[0] + x, c[1] + y) for (x, y) in gear_outline(0.020, 0.026, 12, phase=0.3)]), [circle(0.006, 14)],
                     dr0 + 0.02, dr0 + 0.055, Cm, ax, 0, twist=-0.22, steps=3)
        out_pt = Cm + ax * (dr0 + 0.13)
    else:
        # parallel-axis: a drum over the output gear, a smaller one over the pinion, a web between
        O3 = Vector((hx, sgn * ym, hz))
        gpiv = O3
        Rg, Rp = 0.092, 0.052
        mb.cyl(O3 + ax * dr0, O3 + ax * (dr0 + 0.11), Rg, seg=64, mi=0)
        mb.cyl(Cm + ax * dr0, Cm + ax * (dr0 + 0.11), Rp, seg=40, mi=0)
        a_dir = (O3 - Cm)
        mb.box_between(Cm + ax * (dr0 + 0.055), O3 + ax * (dr0 + 0.055), 0.1, 0.11, up=ax, mi=0)
        mb.cyl(O3 + ax * (dr0 + 0.11), O3 + ax * (dr0 + 0.125), 0.084, seg=48, mi=1)
        mb.cyl(O3 + ax * (dr0 + 0.125), O3 + ax * (dr0 + 0.158), 0.034, seg=32, mi=1)
        mb.torus(O3 + ax * (dr0 + 0.124), ax, 0.037, 0.0024, 32, 5, 4)
        D.bolt_ring(mb, O3 + ax * (dr0 + 0.125), ax, 0.084 - 0.012, 10, 0.0062, 0.0052, 0.0, 2, 2)
        D.bolt_ring(mb, Cm + ax * (dr0 + 0.11), ax, Rp - 0.012, 6, 0.0055, 0.0046, 0.2, 2, 2)
        for i in range(14):                                                  # radial ribs on the big drum, a few on the small
            a = 2 * math.pi * i / 14 + 0.2
            r_hat = radial(a)
            mb.box_between(O3 + ax * (dr0 + 0.012) + r_hat * (Rg + 0.003), O3 + ax * (dr0 + 0.098) + r_hat * (Rg + 0.003), 0.007, 0.0045, up=r_hat, mi=0)
        for i in range(8):
            a = 2 * math.pi * i / 8 + 0.1
            r_hat = radial(a)
            mb.box_between(Cm + ax * (dr0 + 0.012) + r_hat * (Rp + 0.003), Cm + ax * (dr0 + 0.098) + r_hat * (Rp + 0.003), 0.006, 0.004, up=r_hat, mi=0)
        for (pt, rad) in ((O3 + ax * (dr0 + 0.055) + radial(0.4) * Rg, radial(0.4)), (O3 + ax * (dr0 + 0.03) + radial(-0.8) * Rg, radial(-0.8))):
            mb.bolt(pt, rad, 0.0085, 0.0075, 2, 2, True)                      # drain and fill plugs
        bp = O3 + ax * (dr0 + 0.11) + Vector((0, 0, 0)) + radial(math.pi / 2) * 0.0
        mb.cyl(Cm + ax * (dr0 + 0.11) + Vector((0, 0, Rp)), Cm + ax * (dr0 + 0.11) + Vector((0, 0, Rp + 0.012)), 0.007, seg=10, mi=1)         # breather
        mb.cyl(Cm + ax * (dr0 + 0.11) + Vector((0, 0, Rp + 0.012)), Cm + ax * (dr0 + 0.11) + Vector((0, 0, Rp + 0.018)), 0.010, seg=12, mi=3)
        # gears: helical, a pinion on the motor shaft, an output gear (with lightening holes) on the half-shaft's axis
        gp.prism(ccw(gear_outline(0.026, 0.033, 16)), [circle(rs * 1.05, 20)], dr0 + 0.04, dr0 + 0.075, Cm, ax, 0, twist=0.42, steps=5)
        lh = [circle(0.0105, 14, cx=0.044 * math.cos(2 * math.pi * i / 6), cy=0.044 * math.sin(2 * math.pi * i / 6)) for i in range(6)]
        gb.prism(ccw(gear_outline(0.066, 0.074, 40)), [circle(0.02, 20)] + lh, dr0 + 0.04, dr0 + 0.075, O3, ax, 0, twist=-0.17, steps=5)
        gb.cyl(O3 + ax * (dr0 + 0.02), O3 + ax * (dr0 + 0.158), 0.02, seg=24, mi=1)
        out_pt = O3 + ax * (dr0 + 0.158)
    out["reducer"] = solid("XR_Drive_%s_Reducer" % uid, mb, [M["XR_Alu_Cast"], M["XR_Alu_Machined"], M["XR_Bolt"], M["XR_Casing"], M["XR_Rubber"]], coll, g, centre(mb),
                           bevel=0.0, sys="drive", id="reducer", unit=uid)
    out["pinion"] = solid("XR_Drive_%s_Pinion" % uid, gp, [M["XR_Steel"], M["XR_Shaft"]], coll, g, Cm, bevel=0.0, sys="drive", id="pinion", unit=uid)
    out["gears"] = solid("XR_Drive_%s_Gears" % uid, gb, [M["XR_Steel"], M["XR_Shaft"]], coll, g, gpiv, bevel=0.0, sys="drive", id="gears", unit=uid)
    out["output"] = tuple(out_pt)

    # ---- inverter on top ----------------------------------------------------------
    # materials: Plastic_Black 0, Alu_Machined 1, Copper 2, HV_Orange 3, Casing 4, Bolt 5, Label 6, Coolant 7, Rubber 8, Alu_Cast 9
    iz = Cm.z + Rc + 0.0475
    ilen = Ls + 0.05
    mb = MB()
    mb.box((Cm.x, Cm.y + sgn * 0.005, iz), 0.24, ilen, 0.075, 4)
    mb.box((Cm.x, Cm.y + sgn * 0.005, iz + 0.0395), 0.248, ilen + 0.008, 0.008, 4)                       # the cover's flange
    for j in range(8):
        mb.box((Cm.x - 0.09 + j * 0.0257, Cm.y + sgn * 0.005, iz + 0.0475), 0.011, ilen * 0.9, 0.014, 1)
    mb.box((Cm.x, Cm.y + sgn * 0.005, iz + 0.0415), 0.21, ilen * 0.96, 0.002, 0)                           # between the fins
    for sx_ in (1, -1):
        D.bolt_line(mb, (Cm.x + sx_ * 0.116, Cm.y + sgn * 0.005 - ilen * 0.44, iz + 0.0435), (Cm.x + sx_ * 0.116, Cm.y + sgn * 0.005 + ilen * 0.44, iz + 0.0435), 5,
                    Vector((0, 0, 1)), 0.0058, 0.005, 5, 5)
    for sx_ in (1, -1):                                                                                      # mounting ears
        mb.box((Cm.x + sx_ * 0.135, Cm.y + sgn * 0.005, iz - 0.03), 0.04, ilen * 0.5, 0.012, 9)
        mb.bolt((Cm.x + sx_ * 0.135, Cm.y + sgn * 0.005, iz - 0.024), Vector((0, 0, 1)), 0.0075, 0.006, 5, 5, True)
    for j in range(3):
        px_ = Cm.x - 0.055
        py_ = Cm.y + sgn * (-0.07 + j * 0.07 + 0.07)
        mb.box((px_, py_, iz - 0.04 - 0.012), 0.022, 0.012, 0.04, 2)
        mb.bolt((px_, py_, iz - 0.0545), Vector((0, 0, -1)), 0.0046, 0.0038, 5, 5, False)
    hv_x = Cm.x + (-0.07 if front else 0.07)
    hv_y = Cm.y + sgn * 0.02
    nose = D.hv_connector(mb, (hv_x, hv_y, iz + 0.0545), Vector((0, 0, 1)), 3, 3, 1, 0, 0.7, Vector((1, 0, 0)))
    for s3 in (-1, 1):                                                                                       # coolant fittings on the end
        D.fitting(mb, (Cm.x + s3 * 0.05, Cm.y + sgn * 0.005 + sgn * ilen / 2, iz - 0.012), (Cm.x + s3 * 0.05, Cm.y + sgn * 0.005 + sgn * (ilen / 2 + 0.032), iz - 0.012), 0.0085, 7, 7)
    D.sticker(mb, (Cm.x + 0.062, Cm.y + sgn * 0.005, iz + 0.0435 + 0.0003), X, Y, 0.045, 0.045, "hv", 6)
    out["inverter"] = solid("XR_Drive_%s_Inverter" % uid, mb,
                            [M["XR_Plastic_Black"], M["XR_Alu_Machined"], M["XR_Copper"], M["XR_HV_Orange"], M["XR_Casing"], M["XR_Bolt"], M["XR_Label"], M["XR_Coolant"],
                             M["XR_Rubber"], M["XR_Alu_Cast"]],
                            coll, g, centre(mb), bevel=0.002, bevel_seg=1, sys="drive", id="inverter", unit=uid)
    out["hv_port"] = tuple(nose)
    return out
