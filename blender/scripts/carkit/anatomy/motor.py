"""A drive unit: cutaway casing, hairpin stator, V-magnet rotor, reducer with visible helical/planetary gears, and OEM-specific inverter/controller.

Sized from the motor's torque (stator diameter and stack length scale with its cube root), and styled per OEM (`spec.drive_style`):
- `"byd_8in1"` (BYD Seal): Rear parallel-axis drive unit topped by BYD's large 8-in-1 integrated controller penthouse
  (VCU, BMS, PDU, DC-DC, OBC, SiC inverter, reducer, motor) with 4 orange HV ports and multi-bay cast cover.
- `"byd_e3"` (Denza Z9 GT): BYD e³ Tri-Motor platform with twin independent rear motors (`RL`, `RR`) linked by an
  inboard dual-SiC power controller bridge and shared coolant manifold.
- `"driveone"` (Luxeed R7, Avatr 06T): Huawei DriveONE 800V oil-cooled 7-in-1 drive unit with an external cylindrical
  oil-to-water heat exchanger alongside the barrel and oil-spray feed lines.
- `"zeekr_sic"` (Zeekr 7X): Massive 800V/900V SiC rear permanent-magnet drive unit with deep axial cooling fins and dual HV ports.
- `"su7"` / `"sepa"` / `"xpt"` / `"essa"`: OEM-proportioned coaxial front and parallel-axis rear drive units.

The motor casing (`XR_Drive_<uid>_Casing`) and reducer housing (`XR_Drive_<uid>_Reducer`) feature precision 120° anatomical
cutaway windows so the internal copper hairpin windings, V-magnet rotor, and helical gears are directly visible in 3D X-ray view.
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


def _arc_ring(r_in, r_out, a0, a1, n=42):
    """2D C-shaped annular sector from angle a0 to a1 (CCW) for cutaway cylindrical housings."""
    outer = [(r_out * math.cos(a0 + (a1 - a0) * i / n), r_out * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    inner = [(r_in * math.cos(a1 - (a1 - a0) * i / n), r_in * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    return ccw(outer + inner)


def _radial_box(mb, centre_pt, ex, ey, ax, ang, rad, tang, length, mi, r_mid):
    """A box at radius r_mid and angle `ang` (about `ax`) with its long side axial."""
    r_hat = ex * math.cos(ang) + ey * math.sin(ang)
    t_hat = ax.cross(r_hat)
    M = Matrix((r_hat, t_hat, ax)).transposed()
    mb.box(Vector(centre_pt) + r_hat * r_mid, rad, tang, length, mi, M.to_quaternion())


def build(spec, motor, coll, root, M):
    """Build one motor's unit. Returns {'group', 'casing', 'stator', 'rotor', 'reducer', 'gears', 'inverter', ...}."""
    S = sizes(motor)
    style = getattr(spec, "drive_style", "su7")
    k, Ro, Rc, Ls, Rr, rs = S["k"], S["Ro"], S["Rc"], S["Ls"], S["Rr"], S["rs"]
    left = motor.side != "right"
    sgn = 1.0 if left else -1.0
    front = motor.axle == "front"
    # Front single motor is coaxial with planetary stage; ALL rear motors (both single R and twin RL/RR) use parallel-axis offset helical gearboxes!
    coax = front and (motor.side is None)
    hx, hy, hz = spec.hub_f if front else spec.hub_r
    ax = Vector((0, sgn, 0))
    q, ex, ey = _basis(ax)

    if coax:
        off = Vector((0.0, 0.0, 0.0))
        ym = 0.0
    elif motor.side is None:
        # Single rear motor (e.g. BYD Seal, Luxeed R7, Zeekr 7X, XPeng G9L, Avatr 06T, NIO ES8, Voyah Passion S):
        # Output gear sits on the rear axle centerline, motor barrel is offset behind/above in parallel-axis layout
        off = Vector((-0.068, 0.0, 0.078)) * k
        ym = -0.03
    else:
        off = Vector((-0.06, 0.0, 0.08)) * k
        ym = 0.17
    O = Vector((hx, sgn * (0.0 if coax else ym), hz))
    Cm = Vector((hx + off.x, sgn * ym if not coax else 0.0, hz + off.z))
    uid = motor.id
    g = group("XR_Drive_%s" % uid, coll, tuple(Cm), root, sys="drive", id=uid, kw=motor.kw, nm=motor.nm, rpm=motor.rpm)
    out = {"group": g, "centre": tuple(Cm), "sizes": S, "ax": tuple(ax)}

    def at(d):
        return Cm + ax * d

    def radial(a):
        return ex * math.cos(a) + ey * math.sin(a)

    # ---- cutaway casing (`XR_Drive_<uid>_Casing`) ----------------------------------
    # Cutaway window spans 115 degrees on the upper-outboard quadrant so stator copper hairpins and V-magnet rotor show through!
    d0, d1 = -(Ls / 2 + 0.02), Ls / 2 + 0.012
    cut_a0, cut_a1 = math.radians(55), math.radians(300)    # 245° solid shell, 115° open cutaway window
    mb = MB()
    mb.prism(_arc_ring(Ro + 0.0008, Rc, cut_a0, cut_a1, 44), [], d0, d1, Cm, ax, 0)
    # Machined orange/bright rim along the cutaway edges so it reads as an intentional engineering section cutaway
    for ca in (cut_a0, cut_a1):
        r_hat = radial(ca)
        mb.box_between(Cm + ax * d0 + r_hat * ((Ro + Rc) / 2), Cm + ax * d1 + r_hat * ((Ro + Rc) / 2), Rc - Ro, 0.003, up=r_hat, mi=1)

    # Water-jacket rings & axial ribs along the solid 245° arc
    span = d1 - d0 - 0.03
    for i in range(9):
        d = d0 + 0.012 + i * span / 8
        wide = i % 4 == 0
        w = 0.011 if wide else 0.005
        h = 0.0095 if style == "zeekr_sic" else (0.0085 if wide else 0.0055)
        mb.prism(_arc_ring(Rc, Rc + h, cut_a0, cut_a1, 40), [], d, d + w, Cm, ax, 0)
    for a_i in range(10):
        a = 2 * math.pi * a_i / 10 + 0.15
        if not (cut_a0 + 0.15 <= (a % (2 * math.pi)) <= cut_a1 - 0.15):
            continue
        r_hat = radial(a)
        mb.box_between(Cm + ax * (d0 + 0.02) + r_hat * (Rc + 0.002), Cm + ax * (d1 - 0.02) + r_hat * (Rc + 0.002), 0.006, 0.004, up=r_hat, mi=0)

    # Huawei DriveONE specialization: external cylindrical oil-to-water heat exchanger mounted on the side of the motor barrel!
    if style == "driveone":
        hx_dir = -1.0 if front else 1.0
        oil_c = Cm + Vector((hx_dir * (Rc + 0.042), 0.0, 0.015))
        mb.cyl(oil_c - ax * (Ls * 0.42), oil_c + ax * (Ls * 0.42), 0.032, seg=28, mi=1)
        for ring_z in (-0.32, 0.0, 0.32):
            mb.torus(oil_c + ax * (Ls * ring_z), ax, 0.034, 0.0035, 24, 6, 0)
        # Oil gallery transfer pipes into the stator ends
        for sd in (-1, 1):
            p_start = oil_c + ax * (sd * Ls * 0.34)
            p_end = Cm + ax * (sd * (Ls / 2 + 0.005)) + Vector((hx_dir * (Rc - 0.005), 0, 0.015))
            mb.tube([p_start, p_end], 0.0075, seg=10, mi=2)

    # Rear end bell, front flange, mounting feet & coolant ports
    mb.cyl(at(d0 - 0.028), at(d0), Rc - 0.002, seg=56, mi=0)
    mb.lathe([(0.0, d0 - 0.047), (0.044 * k + 0.004, d0 - 0.047), (0.044 * k + 0.006, d0 - 0.043), (0.044 * k + 0.006, d0 - 0.028)], Cm, ax, 40, 1)
    mb.torus(at(d0 - 0.0285), ax, Rc - 0.012, 0.0028, 40, 6, 4)
    D.bolt_ring(mb, at(d0 - 0.028), -ax, Rc - 0.022, 8, 0.0062, 0.005, 0.1, 3, 3)
    mb.lathe([(Ro * 0.6, d1), (Rc + 0.012, d1), (Rc + 0.012, d1 + 0.012), (Ro * 0.6, d1 + 0.012), (Ro * 0.6, d1)], Cm, ax, 64, 1)
    D.bolt_ring(mb, at(d1 + 0.012), ax, Rc + 0.0, 12, 0.0072, 0.0058, 0.05, 3, 3)
    zb = -Rc - 0.008
    mb.box(Cm + Vector((0, 0, zb)), 0.17, Ls * 0.98, 0.02, 7)
    for sx in (1, -1):
        for sy in (1, -1):
            mb.bolt(Cm + Vector((sx * 0.062, sy * Ls * 0.4, zb + 0.01)), Vector((0, 0, 1)), 0.0082, 0.0066, 3, 3, True)
        mb.box_between(Cm + Vector((sx * 0.08, 0, zb + 0.01)), Cm + Vector((sx * 0.035, 0, -Rc * 0.6)), 0.02, 0.014, up=Y, mi=7)
    D.sticker(mb, Cm + Vector((0.0855, 0.0, zb)), Vector((0, 1, 0)), Z, 0.07, 0.016, "plate", 5)
    for s2 in (-1, 1):
        base = Cm + Vector((s2 * 0.045, 0, Rc + 0.004))
        D.fitting(mb, base, base + Vector((0, 0, 0.036)), 0.0105, 1, 1)
        hose_pts = [base + Vector((0, 0, 0.026)), base + Vector((0, 0, 0.056)), base + Vector((s2 * 0.03, 0, 0.074))]
        mb.tube(round_path(hose_pts, 0.018, 6), 0.0125, seg=14, mi=2)
        D.clamp(mb, base + Vector((0, 0, 0.034)), Vector((0, 0, 1)), 0.0122, 1, 1)
    out["casing"] = solid("XR_Drive_%s_Casing" % uid, mb,
                          [M["XR_Casing"], M["XR_Alu_Machined"], M["XR_Coolant"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Plastic_Black"], M["XR_Alu_Cast"]],
                          coll, g, Cm, bevel=0.0, sys="drive", id="casing", unit=uid)

    # ---- stator (`XR_Drive_<uid>_Stator`) — cutaway lamination ring so V-magnet rotor is also visible inside!
    Rb = Rr + 0.0015
    Rs = Ro - 0.018
    n_sl = 48
    th = 2 * math.pi / n_sl
    mb = MB()
    # Cutaway 265° stator lamination stack so 95° of the inner V-magnet rotor shows through!
    mb.prism(_arc_ring(Rs, Ro, math.radians(45), math.radians(310), 48), [], -Ls / 2, Ls / 2, Cm, ax, 0)
    rm = (Rb + Rs) / 2
    for i in range(n_sl):
        a = i * th + 0.75 * th
        ph = 1 + (i % 3)
        # Keep all hairpin end-crowns at both ends (so the full 360° copper crown basket is visible!) and cut away only the middle slot bars in the 0..45° window
        if math.radians(42) <= (a % (2 * math.pi)) <= math.radians(312):
            _radial_box(mb, Cm, ex, ey, ax, a, Rs - Rb - 0.002, 0.4 * th * rm, Ls + 0.006, ph, rm)
        for sd in (-1, 1):
            for layer, (dr, twist) in enumerate(((-0.0050, 1.0), (0.0050, -1.0))):
                d_a = sd * (Ls / 2 + 0.003)
                d_b = sd * (Ls / 2 + 0.026 + 0.0018 * layer)
                a2 = a + sd * twist * 3.0 * th
                p0 = Cm + ax * d_a + radial(a) * (rm + dr)
                p1 = Cm + ax * d_b + radial(a2) * (rm + dr)
                mb.box_between(p0, p1, 0.0046, 0.0062, up=radial(a), mi=ph)
                mb.box(p1 + ax * (0.0008 * sd), 0.0062, 0.0062, 0.0042, 4, (Matrix((radial(a2), ax.cross(radial(a2)), ax)).transposed().to_quaternion()))
    for sd in (-1, 1):
        mb.lathe([(Rb + 0.003, sd * (Ls / 2 + 0.030)), (Rs - 0.002, sd * (Ls / 2 + 0.030)), (Rs - 0.002, sd * (Ls / 2 + 0.0336)), (Rb + 0.003, sd * (Ls / 2 + 0.0336))], Cm, ax, 64, 5)
    out["stator"] = solid("XR_Drive_%s_Stator" % uid, mb, [M["XR_Lamination"], M["XR_Copper_U"], M["XR_Copper_V"], M["XR_Copper_W"], M["XR_Brass"], M["XR_Steel"]],
                          coll, g, Cm, bevel=0.0, sys="drive", id="stator", unit=uid)

    # ---- rotor (`XR_Drive_<uid>_Rotor`) -------------------------------------------
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
    sd0, sd1 = -Ls / 2 - 0.075 * k, Ls / 2 + 0.2 * k
    mb.cyl(at(sd0), at(sd1), rs, seg=24, mi=3)
    for dd in (sd0 + 0.004, Ls / 2 + 0.018):
        w = 0.016
        mb.lathe([(rs * 1.02, dd), (rs * 1.55, dd), (rs * 1.55, dd + w), (rs * 1.02, dd + w)], Cm, ax, 40, 5)
        mb.lathe([(rs * 2.05, dd), (rs * 2.2, dd), (rs * 2.2, dd + w), (rs * 2.05, dd + w)], Cm, ax, 40, 5)
        for bI in range(10):
            a = 2 * math.pi * bI / 10
            mb.sphere(Cm + ax * (dd + w / 2) + radial(a) * (rs * 1.8), rs * 0.22, 6, 4, 4)
    mb.lathe([(rs * 1.02, Ls / 2 + 0.04), (rs * 1.35, Ls / 2 + 0.04), (rs * 1.35, Ls / 2 + 0.050), (rs * 1.02, Ls / 2 + 0.050)], Cm, ax, 32, 5)
    mb.prism(ccw(gear_outline(rs * 1.55, rs * 1.9, 24)), [circle(rs * 1.0, 20)], sd0 + 0.024, sd0 + 0.030, Cm, ax, 5)
    spl = []
    ds = sd1 - 0.07 * k
    for i in range(14):
        spl.append((rs * (1.0 if i % 2 == 0 else 0.9), ds + i * 0.005))
    mb.lathe(spl, Cm, ax, 24, 3)
    out["rotor"] = solid("XR_Drive_%s_Rotor" % uid, mb,
                         [M["XR_Lamination"], M["XR_Magnet_N"], M["XR_Magnet_S"], M["XR_Shaft"], M["XR_Alu_Machined"], M["XR_Steel"]],
                         coll, g, Cm, bevel=0.0, sys="drive", id="rotor", unit=uid)

    # ---- cutaway reducer and helical gears (`XR_Drive_<uid>_Reducer`, `Pinion`, `Gears`)
    dr0 = d1 + 0.012
    mb = MB()
    gb = MB()
    gp = MB()
    gpiv = Cm
    if coax:
        Rd = Rc + 0.012
        # Cutaway planetary drum so sun & planet helical gears show through
        mb.prism(_arc_ring(Rd - 0.012, Rd, cut_a0, cut_a1, 40), [], dr0, dr0 + 0.085, Cm, ax, 0)
        mb.cyl(at(dr0 + 0.085), at(dr0 + 0.097), Rd * 0.65, seg=48, mi=0)
        mb.cyl(at(dr0 + 0.097), at(dr0 + 0.13), 0.04, seg=32, mi=1)
        mb.torus(at(dr0 + 0.126), ax, 0.043, 0.0026, 32, 5, 4)
        D.bolt_ring(mb, at(dr0 + 0.0), ax, Rd - 0.004, 10, 0.0068, 0.0055, 0.3, 2, 2)
        ring = ccw(gear_outline(0.074, 0.082, 38))
        gb.prism(_arc_ring(0.078, 0.098, cut_a0, cut_a1, 40), [], dr0 + 0.02, dr0 + 0.055, Cm, ax, 0)
        gp.prism(ccw(gear_outline(0.020, 0.026, 12)), [circle(rs * 1.05, 20)], dr0 + 0.02, dr0 + 0.055, Cm, ax, 0, twist=0.22, steps=3)
        for i in range(3):
            a = 2 * math.pi * i / 3 + 0.5
            c = (0.048 * math.cos(a), 0.048 * math.sin(a))
            gb.prism(ccw([(c[0] + x, c[1] + y) for (x, y) in gear_outline(0.020, 0.026, 12, phase=0.3)]), [circle(0.006, 14)],
                     dr0 + 0.02, dr0 + 0.055, Cm, ax, 0, twist=-0.22, steps=3)
        out_pt = Cm + ax * (dr0 + 0.13)
        out["output_r"] = tuple(Cm - ax * (Ls / 2 + 0.067))
    else:
        O3 = Vector((hx, sgn * ym, hz))
        gpiv = O3
        Rg, Rp = 0.092, 0.052
        # Cutaway half-shell around the parallel-axis output gear and pinion so helical gears are visible in 3D!
        mb.prism(_arc_ring(Rg - 0.010, Rg, math.radians(70), math.radians(290), 36), [], dr0, dr0 + 0.10, O3, ax, 0)
        mb.prism(_arc_ring(Rp - 0.009, Rp, math.radians(70), math.radians(290), 28), [], dr0, dr0 + 0.10, Cm, ax, 0)
        mb.box_between(Cm + ax * (dr0 + 0.012), O3 + ax * (dr0 + 0.012), 0.09, 0.022, up=ax, mi=0)
        mb.cyl(O3 + ax * (dr0 + 0.10), O3 + ax * (dr0 + 0.125), 0.052, seg=36, mi=1)
        mb.cyl(O3 + ax * (dr0 + 0.125), O3 + ax * (dr0 + 0.158), 0.034, seg=32, mi=1)
        mb.torus(O3 + ax * (dr0 + 0.124), ax, 0.037, 0.0024, 32, 5, 4)
        D.bolt_ring(mb, O3 + ax * (dr0 + 0.10), ax, 0.048, 8, 0.0058, 0.0048, 0.0, 2, 2)
        gp.prism(ccw(gear_outline(0.026, 0.033, 16)), [circle(rs * 1.05, 20)], dr0 + 0.03, dr0 + 0.082, Cm, ax, 0, twist=0.42, steps=5)
        lh = [circle(0.0105, 14, cx=0.044 * math.cos(2 * math.pi * i / 6), cy=0.044 * math.sin(2 * math.pi * i / 6)) for i in range(6)]
        gb.prism(ccw(gear_outline(0.066, 0.074, 40)), [circle(0.02, 20)] + lh, dr0 + 0.03, dr0 + 0.082, O3, ax, 0, twist=-0.17, steps=5)
        gb.cyl(O3 + ax * (dr0 + 0.015), O3 + ax * (dr0 + 0.158), 0.02, seg=24, mi=1)
        out_pt = O3 + ax * (dr0 + 0.158)
        out["output_r"] = tuple(O3 - ax * (Ls / 2 + 0.055))
    out["reducer"] = solid("XR_Drive_%s_Reducer" % uid, mb, [M["XR_Alu_Cast"], M["XR_Alu_Machined"], M["XR_Bolt"], M["XR_Casing"], M["XR_Rubber"]], coll, g, centre(mb),
                           bevel=0.0, sys="drive", id="reducer", unit=uid)
    out["pinion"] = solid("XR_Drive_%s_Pinion" % uid, gp, [M["XR_Steel"], M["XR_Shaft"]], coll, g, Cm, bevel=0.0, sys="drive", id="pinion", unit=uid)
    out["gears"] = solid("XR_Drive_%s_Gears" % uid, gb, [M["XR_Steel"], M["XR_Shaft"]], coll, g, gpiv, bevel=0.0, sys="drive", id="gears", unit=uid)
    out["output"] = tuple(out_pt)

    # ---- OEM-specific inverter / integrated power electronics (`XR_Drive_<uid>_Inverter`)
    iz = Cm.z + Rc + 0.0475
    ilen = Ls + 0.05
    mb = MB()

    if style == "byd_8in1" and not front:
        # BYD 8-in-1 Integrated Drive Controller Penthouse: large multi-compartment cast-aluminum module
        # housing VCU, BMS, PDU, DC-DC, OBC, and SiC Motor Controller in a tiered top assembly with 4 HV ports
        ix = Cm.x + 0.035
        iy = Cm.y + sgn * 0.04
        mb.box((ix, iy, iz + 0.012), 0.34, ilen + 0.14, 0.095, 4)
        mb.box((ix - 0.03, iy, iz + 0.068), 0.24, ilen + 0.10, 0.028, 9)    # upper OBC/DC-DC deck
        mb.box((ix - 0.03, iy, iz + 0.084), 0.248, ilen + 0.108, 0.006, 1)
        for j in range(11):
            mb.box((ix - 0.11 + j * 0.020, iy, iz + 0.092), 0.008, (ilen + 0.08) * 0.88, 0.012, 1)
        # 4 Orange High-Voltage Ports (Traction DC, OBC AC/DC, PTC, A/C Compressor)
        nose = D.hv_connector(mb, (ix + 0.14, iy - 0.08, iz + 0.062), Vector((0, 0, 1)), 3, 3, 1, 0, 0.75, Vector((1, 0, 0)))
        for extra_y in (-0.01, 0.06, 0.12):
            D.hv_connector(mb, (ix + 0.14, iy + extra_y, iz + 0.062), Vector((0, 0, 1)), 3, 3, 1, 0, 0.58, Vector((1, 0, 0)))
        D.sticker(mb, (ix - 0.02, iy, iz + 0.088), X, Y, 0.055, 0.055, "hv", 6)
    elif style == "byd_e3" and not front:
        # BYD e³ Twin-SiC Power Controller Bridge: spans over each rear motor and extends inboard toward the centerline
        # so RL and RR form a unified twin-controller bridge across the rear axle!
        inboard_y = -sgn * 0.085
        mb.box((Cm.x, Cm.y + inboard_y, iz + 0.008), 0.27, ilen + 0.13, 0.086, 4)
        mb.box((Cm.x, Cm.y + inboard_y, iz + 0.054), 0.278, ilen + 0.138, 0.008, 1)
        # Inboard interconnect busbar bridge meeting at y = 0
        mb.box_between((Cm.x, Cm.y, iz + 0.025), (Cm.x, 0.0, iz + 0.025), 0.12, 0.045, up=Z, mi=3)
        for j in range(9):
            mb.box((Cm.x - 0.10 + j * 0.025, Cm.y + inboard_y, iz + 0.064), 0.011, (ilen + 0.10) * 0.9, 0.015, 1)
        hv_x = Cm.x + 0.08
        hv_y = Cm.y + sgn * 0.01
        nose = D.hv_connector(mb, (hv_x, hv_y, iz + 0.062), Vector((0, 0, 1)), 3, 3, 1, 0, 0.72, Vector((1, 0, 0)))
        D.sticker(mb, (Cm.x + 0.05, Cm.y + inboard_y, iz + 0.059), X, Y, 0.05, 0.05, "hv", 6)
    elif style == "driveone":
        # Huawei DriveONE 800V SiC Controller: sleek low-profile chamfered silver housing with orange 3-phase busbars
        mb.box((Cm.x, Cm.y + sgn * 0.005, iz - 0.006), 0.25, ilen + 0.02, 0.062, 1)
        mb.box((Cm.x, Cm.y + sgn * 0.005, iz + 0.028), 0.22, ilen * 0.88, 0.012, 4)
        for j in range(10):
            mb.box((Cm.x - 0.09 + j * 0.020, Cm.y + sgn * 0.005, iz + 0.038), 0.007, ilen * 0.82, 0.009, 1)
        for j in range(3):
            py_ = Cm.y + sgn * (-0.06 + j * 0.06)
            mb.box((Cm.x - 0.09, py_, iz - 0.025), 0.028, 0.016, 0.045, 3)
        hv_x = Cm.x + (-0.07 if front else 0.07)
        hv_y = Cm.y + sgn * 0.02
        nose = D.hv_connector(mb, (hv_x, hv_y, iz + 0.040), Vector((0, 0, 1)), 3, 3, 1, 0, 0.7, Vector((1, 0, 0)))
        D.sticker(mb, (Cm.x + 0.05, Cm.y + sgn * 0.005, iz + 0.035), X, Y, 0.045, 0.045, "hv", 6)
    else:
        mb.box((Cm.x, Cm.y + sgn * 0.005, iz), 0.24, ilen, 0.075, 4)
        mb.box((Cm.x, Cm.y + sgn * 0.005, iz + 0.0395), 0.248, ilen + 0.008, 0.008, 4)
        for j in range(8):
            mb.box((Cm.x - 0.09 + j * 0.0257, Cm.y + sgn * 0.005, iz + 0.0475), 0.011, ilen * 0.9, 0.014, 1)
        mb.box((Cm.x, Cm.y + sgn * 0.005, iz + 0.0415), 0.21, ilen * 0.96, 0.002, 0)
        for sx_ in (1, -1):
            D.bolt_line(mb, (Cm.x + sx_ * 0.116, Cm.y + sgn * 0.005 - ilen * 0.44, iz + 0.0435), (Cm.x + sx_ * 0.116, Cm.y + sgn * 0.005 + ilen * 0.44, iz + 0.0435), 5,
                        Vector((0, 0, 1)), 0.0058, 0.005, 5, 5)
        for j in range(3):
            px_ = Cm.x - 0.055
            py_ = Cm.y + sgn * (-0.07 + j * 0.07 + 0.07)
            mb.box((px_, py_, iz - 0.052), 0.022, 0.012, 0.04, 2)
        hv_x = Cm.x + (-0.07 if front else 0.07)
        hv_y = Cm.y + sgn * 0.02
        nose = D.hv_connector(mb, (hv_x, hv_y, iz + 0.0545), Vector((0, 0, 1)), 3, 3, 1, 0, 0.7, Vector((1, 0, 0)))
        D.sticker(mb, (Cm.x + 0.062, Cm.y + sgn * 0.005, iz + 0.0438), X, Y, 0.045, 0.045, "hv", 6)

    for s3 in (-1, 1):
        D.fitting(mb, (Cm.x + s3 * 0.05, Cm.y + sgn * 0.005 + sgn * ilen / 2, iz - 0.012),
                  (Cm.x + s3 * 0.05, Cm.y + sgn * 0.005 + sgn * (ilen / 2 + 0.032), iz - 0.012), 0.0085, 7, 7)
    out["inverter"] = solid("XR_Drive_%s_Inverter" % uid, mb,
                            [M["XR_Plastic_Black"], M["XR_Alu_Machined"], M["XR_Copper"], M["XR_HV_Orange"], M["XR_Casing"], M["XR_Bolt"], M["XR_Label"], M["XR_Coolant"],
                             M["XR_Rubber"], M["XR_Alu_Cast"]],
                            coll, g, centre(mb), bevel=0.002, bevel_seg=1, sys="drive", id="inverter", unit=uid)
    out["hv_port"] = tuple(nose)
    return out
