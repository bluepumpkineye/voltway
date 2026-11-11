"""Suspension corners, anti-roll bars, front/rear steering racks, and half-shafts (`spec.susp_style`):
- `"su7"` (Xiaomi SU7 Ultra): Forged double-wishbone front, multi-link rear, dual-chamber air bellows + gold piggyback reservoir damper.
- `"disus_c_coil"` (BYD Seal): Helical steel coilover springs (wound 3D coil spring + perches) over BYD DiSus-C adaptive
  solenoid-valve dampers; double-wishbone front and 5-link separated rear control links.
- `"disus_a"` (Denza Z9 GT): BYD DiSus-A dual-chamber stepped air spring domes + CDC dampers; virtual-kingpin separated
  dual-ball-joint lower front links and 5-link rear suspension with active rear steering.
- `"vkp_air"` (Luxeed R7, Zeekr 7X, Avatr 06T): Virtual-kingpin separated dual lower front links, 5-link separated rear links,
  and closed-chamber air springs with compact CDC/CCD solenoid dampers.
- `"air_cdc"` (XPeng G9L, NIO ES8, Voyah Passion S): Forged front double wishbone, 5-link separated rear links, dual-chamber
  air springs and continuous-damping-control (CDC) valve struts.
"""
import json
import math

from mathutils import Matrix, Quaternion, Vector

from . import detail as D
from .prim import MB, X, Y, Z, basis_q, group, profile_I, round_path, solid, to_gltf, wloc


def hardpoints(spec, corner):
    front = corner[0] == "F"
    s = 1.0 if corner[1] == "L" else -1.0
    hx, hy, hz = spec.hub_f if front else spec.hub_r

    def P(dx, dy, dz):
        return Vector((hx + dx, s * (hy + dy), hz + dz))

    def W(x, y, z):
        return Vector((x, s * y, z))

    h = {"s": s, "front": front, "H": P(0, 0, 0)}
    zl = 0.205 if front else 0.21
    h["LBJ"] = P(0.0, -0.105, -0.165)
    h["UBJ"] = P(-0.01, -0.11, 0.152)
    h["LF"] = W(hx + (0.20 if front else 0.19), 0.40 if front else 0.42, zl)
    h["LR"] = W(hx - (0.20 if front else 0.17), 0.40 if front else 0.42, zl - 0.005)
    h["UF"] = W(hx + 0.13, 0.50, 0.585)
    h["UR"] = W(hx - 0.13, 0.50, 0.58)
    h["TO"] = P(-0.095, -0.115, -0.04)
    h["TI"] = W(hx - 0.16, 0.34, 0.31) if front else W(hx - 0.17, 0.40, 0.235)
    link = h["LF"] if front else h["LR"]
    h["SB"] = link + (h["LBJ"] - link) * 0.62
    h["ST"] = Vector((h["SB"].x, s * 0.50, 0.76))
    h["ABAR"] = Vector((hx - 0.10, s * 0.56, 0.255))
    h["ALINK"] = Vector((hx - 0.10, s * 0.56, zl - 0.005))
    return h


def _place(ob, loc, q=None):
    ob.location = Vector(loc) - (wloc(ob.parent) if ob.parent else Vector())
    if q is not None:
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = q


def _aimed(name, mb, mats, coll, parent, frm, to, bevel=0.001, **meta):
    """A part built along +Z from its origin, rotated to point from `frm` toward `to`."""
    ob = solid(name, mb, mats, coll, parent, pivot=(0, 0, 0), bevel=bevel, bevel_seg=1, **meta)
    d = Vector(to) - Vector(frm)
    _place(ob, frm, Z.rotation_difference(d.normalized()))
    ob["aim"] = json.dumps([to_gltf(frm), to_gltf(to)], separators=(",", ":"))
    return ob


def _bush(mb, p, axis, r_out, half, mi_rubber, mi_steel, mi_bolt, bolt=True):
    p = Vector(p)
    u = Vector(axis).normalized()
    mb.cyl(p - u * half, p + u * half, r_out, seg=18, mi=mi_rubber)
    mb.cyl(p - u * (half + 0.0015), p + u * (half + 0.0015), r_out * 0.46, seg=14, mi=mi_steel)
    mb.torus(p + u * half, u, r_out * 0.99, r_out * 0.07, 18, 4, mi_steel)
    mb.torus(p - u * half, u, r_out * 0.99, r_out * 0.07, 18, 4, mi_steel)
    if bolt:
        mb.bolt(p + u * (half + 0.0015), u, r_out * 0.36, r_out * 0.34, mi_bolt, mi_bolt, True)
        mb.bolt(p - u * (half + 0.0015), -u, r_out * 0.36, r_out * 0.34, mi_bolt, mi_bolt, True)


def _ball_joint(mb, c, axis, r, mi_steel, mi_rubber, mi_bolt, boot_len=0.034):
    c = Vector(c)
    u = Vector(axis).normalized()
    mb.sphere(c, r * 0.8, 12, 7, mi_steel)
    prof = [(r * 1.15, 0.0)]
    n = 6
    for i in range(n):
        t = boot_len * (i + 0.5) / n
        prof.append((r * (1.18 if i % 2 == 0 else 0.92) - 0.001 * i * 0.3, t))
    prof.append((r * 0.62, boot_len))
    mb.lathe(prof, c + u * (r * 0.5), u, 18, mi_rubber)
    top = c + u * (r * 0.5 + boot_len)
    mb.cyl(top, top + u * (r * 1.7), r * 0.42, seg=10, mi=mi_steel)
    mb.bolt(top + u * (r * 0.2), u, r * 0.62, r * 0.78, mi_bolt, mi_bolt, False)
    mb.cyl(top + u * (r * 0.4), top + u * (r * 1.7), r * 0.07, seg=6, mi=mi_bolt)


def corner(spec, name, coll, root, M):
    """One wheel corner. Returns {'group', parts...}."""
    style = getattr(spec, "susp_style", "su7")
    h = hardpoints(spec, name)
    s, front = h["s"], h["front"]
    H = h["H"]
    g = group("XR_Susp_%s" % name, coll, tuple(H), root, sys="suspension", id=name)
    out = {"group": g, "hp": h}
    Zv = Vector((0, 0, 1))

    def forged_link(mb, a, b, w, hh, mi, swell=1.6, up=Zv):
        n = 10
        pts = [Vector(a).lerp(Vector(b), i / (n - 1)) for i in range(n)]
        sc = [1.0 + (swell - 1.0) * (abs(2 * i / (n - 1) - 1) ** 4) for i in range(n)]
        mb.sweep(pts, profile_I(hh, w, w * 0.22, hh * 0.20), mi=mi, scales=sc, up=up)

    # =========================================================================
    # 1. LOWER ARM (`XR_Susp_<name>_LowerArm`)
    # =========================================================================
    mb = MB()
    if front and style in ("disus_a", "vkp_air"):
        # Virtual-Kingpin Double Wishbone Front: two SEPARATE forged lower links with dual lower ball joints!
        lbj_f = h["LBJ"] + Vector((0.038, s * 0.012, 0.0))
        lbj_r = h["LBJ"] + Vector((-0.036, -s * 0.008, -0.004))
        forged_link(mb, h["LF"], lbj_f, 0.042, 0.025, 0, 1.5)
        forged_link(mb, h["LR"], lbj_r, 0.040, 0.024, 0, 1.5)
        _bush(mb, h["LF"], X, 0.028, 0.035, 1, 2, 3)
        _bush(mb, h["LR"], X, 0.028, 0.035, 1, 2, 3)
        _ball_joint(mb, lbj_f, Zv, 0.019, 2, 1, 3)
        _ball_joint(mb, lbj_r, Zv, 0.019, 2, 1, 3)
    elif not front and style != "su7":
        # True 5-Link Rear Lower Assembly: separated lower front camber link + deep cast/forged lower rear spring-carrier link!
        lbj_f = h["LBJ"] + Vector((0.055, s * 0.015, 0.012))
        lbj_r = h["LBJ"] + Vector((-0.025, 0.0, -0.008))
        mb.tube([h["LF"], lbj_f], 0.016, seg=14, mi=2)                            # tubular steel/forged front lower link
        forged_link(mb, h["LR"], lbj_r, 0.052, 0.034, 0, 1.55)                    # heavy forged spring-pan lower rear link
        _bush(mb, h["LF"], X, 0.025, 0.030, 1, 2, 3)
        _bush(mb, h["LR"], X, 0.030, 0.038, 1, 2, 3)
        _bush(mb, lbj_f, X, 0.022, 0.026, 1, 2, 3)
        _ball_joint(mb, lbj_r, Zv, 0.021, 2, 1, 3)
    else:
        for a in (h["LF"], h["LR"]):
            forged_link(mb, a, h["LBJ"], 0.040, 0.024, 0, 1.45)
            _bush(mb, a, X, 0.027, 0.034, 1, 2, 3)
        mb.box_between(h["LF"] + Vector((0, 0, -0.012)), h["LR"] + Vector((0, 0, -0.012)), 0.014, 0.006, up=Zv, mi=0)
        mb.cyl(h["LF"], h["LR"], 0.0075, seg=8, mi=2)
        _ball_joint(mb, h["LBJ"], Zv, 0.021, 2, 1, 3)

    sb = h["SB"]
    mb.box(sb + Vector((0, 0, 0.012)), 0.05, 0.06, 0.016, 0)
    mb.bolt(sb + Vector((0, s * 0.015, 0.02)), Zv, 0.007, 0.006, 3, 3, True)
    pivot = (h["LF"] + h["LR"]) / 2
    out["lower"] = solid("XR_Susp_%s_LowerArm" % name, mb, [M["XR_Arm"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, pivot, bevel=0.0012, bevel_seg=1,
                         sys="suspension", id="lower_arm")

    # =========================================================================
    # 2. UPPER ARM / MULTI-LINK UPPER RODS (`XR_Susp_<name>_UpperArm`)
    # =========================================================================
    mb = MB()
    if not front and style != "su7":
        # True 5-Link Rear Upper Assembly: two distinct separated upper links (upper front tension link + upper rear camber link)
        ubj_f = h["UBJ"] + Vector((0.045, s * 0.01, 0.006))
        ubj_r = h["UBJ"] + Vector((-0.040, -s * 0.005, -0.006))
        forged_link(mb, h["UF"], ubj_f, 0.028, 0.018, 0, 1.45)
        forged_link(mb, h["UR"], ubj_r, 0.032, 0.020, 0, 1.45)
        for pt in (h["UF"], h["UR"], ubj_f, ubj_r):
            _bush(mb, pt, X, 0.021, 0.026, 1, 2, 3)
    else:
        for a in (h["UF"], h["UR"]):
            forged_link(mb, a, h["UBJ"], 0.032, 0.020, 0, 1.4)
            _bush(mb, a, X, 0.023, 0.030, 1, 2, 3)
        mb.cyl(h["UF"], h["UR"], 0.0065, seg=8, mi=2)
        _ball_joint(mb, h["UBJ"], -Zv, 0.018, 2, 1, 3)
    pivot = (h["UF"] + h["UR"]) / 2
    out["upper"] = solid("XR_Susp_%s_UpperArm" % name, mb, [M["XR_Arm"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, pivot, bevel=0.0012, bevel_seg=1,
                         sys="suspension", id="upper_arm")

    # =========================================================================
    # 3. KNUCKLE / HUB CARRIER (`XR_Susp_<name>_Knuckle`)
    # =========================================================================
    def P(dx, dy, dz):
        return Vector((H.x + dx, s * (abs(H.y) + dy), H.z + dz))
    out_dir = Vector((0, s, 0))
    mb = MB()
    mb.cyl(P(0, -0.10, 0), P(0, -0.03, 0), 0.052, seg=32, mi=0)
    mb.cyl(P(0, -0.03, 0), P(0, -0.016, 0), 0.046, seg=32, mi=1)
    mb.torus(P(0, -0.0165, 0), out_dir, 0.040, 0.004, 32, 6, 4)
    mb.cyl(P(0, -0.016, 0), P(0, -0.006, 0), 0.062, seg=36, mi=1)
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 2
        st = P(0, -0.006, 0) + Vector((math.cos(a) * 0.0465, 0, math.sin(a) * 0.0465))
        mb.cyl(st, st + out_dir * 0.018, 0.0052, seg=8, mi=2)
        mb.bolt(st, out_dir, 0.0075, 0.007, 3, 3, False)
    mb.tube([P(0, -0.06, 0), P(0, -0.105, -0.165)], 0.024, seg=14, mi=0, r_end=0.018)
    mb.tube([P(0, -0.06, 0), P(-0.01, -0.11, 0.152)], 0.019, seg=14, mi=0, r_end=0.016)
    mb.box_between(P(-0.03, -0.075, 0.03), P(-0.03, -0.075, -0.13), 0.026, 0.012, up=Y * s, mi=0)
    mb.tube([P(-0.02, -0.075, -0.02), h["TO"]], 0.012, seg=10, mi=0)
    mb.box(P(-0.13, -0.075, 0.0), 0.07, 0.02, 0.2, 0)
    for dz in (-0.07, 0.07):
        mb.cyl(P(-0.12, -0.075, dz), P(-0.12, -0.04, dz), 0.016, seg=14, mi=0)
        mb.bolt(P(-0.12, -0.04, dz), out_dir, 0.009, 0.0075, 3, 3, True)
    mb.box(P(0.03, -0.075, 0.05), 0.02, 0.014, 0.02, 2)
    mb.cyl(P(0.03, -0.068, 0.05), P(0.03, -0.045, 0.05), 0.006, seg=8, mi=2)
    mb.sphere(h["TO"], 0.015, 10, 6, 2)
    out["knuckle"] = solid("XR_Susp_%s_Knuckle" % name, mb, [M["XR_Knuckle"], M["XR_Alu_Machined"], M["XR_Steel"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, H,
                           bevel=0.0015, bevel_seg=1, sys="suspension", id="knuckle")

    # =========================================================================
    # 4. TIE ROD / TOE LINK (`XR_Susp_<name>_TieRod` / `ToeLink`)
    # =========================================================================
    mb = MB()
    d = h["TO"] - h["TI"]
    L = d.length
    mb.cyl((0, 0, 0), (0, 0, L), 0.0095, seg=12, mi=0)
    mb.cyl((0, 0, L * 0.30), (0, 0, L * 0.62), 0.0135, seg=14, mi=1)
    mb.bolt((0, 0, L * 0.30), -Z, 0.0112, 0.007, 3, 3, False)
    mb.bolt((0, 0, L * 0.62), Z, 0.0112, 0.007, 3, 3, False)
    mb.sphere((0, 0, 0), 0.015, 10, 6, 1)
    mb.lathe([(0.013, 0.006), (0.017, 0.016), (0.012, 0.026), (0.017, 0.036), (0.011, 0.046)], (0, 0, 0), Z, 14, 2)
    out["tie"] = _aimed("XR_Susp_%s_%s" % (name, "TieRod" if front else "ToeLink"), mb, [M["XR_Arm"], M["XR_Steel"], M["XR_Rubber"], M["XR_Bolt"]], coll, g, h["TI"], h["TO"],
                        0.0006, sys="suspension", id="tie_rod" if front else "toe_link")

    # =========================================================================
    # 5. SPRING & DAMPER (`XR_Susp_<name>_Spring`, `Damper`, `Rod`)
    # =========================================================================
    top, bot = h["ST"], h["SB"]
    Lsd = (bot - top).length

    mb = MB()
    if style == "disus_c_coil":
        # BYD Seal Coilover Spring: wound 3D helical steel coil spring (7.5 turns) between upper & lower spring perches!
        mb.cyl((0, 0, -0.012), (0, 0, 0.015), 0.062, seg=28, mi=3)
        D.bolt_ring(mb, (0, 0, -0.012), -Z, 0.048, 6, 0.0065, 0.0058, 0.2, 3, 3)
        # Upper and lower spring seats
        z_s0, z_s1 = Lsd * 0.14, Lsd * 0.68
        mb.cyl((0, 0, z_s0 - 0.012), (0, 0, z_s0), 0.056, seg=28, mi=0)
        mb.cyl((0, 0, z_s1), (0, 0, z_s1 + 0.014), 0.056, seg=28, mi=0)
        turns = 6.5
        n_pts = 78
        r_coil = 0.046
        helix = []
        for i in range(n_pts + 1):
            t_f = i / n_pts
            ang = 2 * math.pi * turns * t_f
            zz = z_s0 + (z_s1 - z_s0) * t_f
            helix.append(Vector((r_coil * math.cos(ang), r_coil * math.sin(ang), zz)))
        mb.tube(helix, 0.0072, seg=10, mi=2)
    elif style == "disus_a":
        # BYD DiSus-A Dual-Chamber Stepped Air Spring Dome
        mb.cyl((0, 0, -0.012), (0, 0, 0.0), 0.065, seg=28, mi=3)
        mb.cyl((0, 0, 0.0), (0, 0, Lsd * 0.28), 0.060, seg=32, mi=0)       # large upper dual-chamber aluminum dome
        mb.torus((0, 0, Lsd * 0.14), Z, 0.062, 0.004, 32, 6, 2)
        D.bolt_ring(mb, (0, 0, -0.012), -Z, 0.050, 6, 0.0065, 0.0058, 0.2, 3, 3)
        prof = []
        nb = 6
        for i in range(nb * 2 + 1):
            t = Lsd * (0.28 + 0.34 * i / (nb * 2))
            prof.append((0.055 if i % 2 == 0 else 0.043, t))
        mb.lathe(prof, (0, 0, 0), Z, 36, 1)
        mb.cyl((0, 0, Lsd * 0.62), (0, 0, Lsd * 0.75), 0.048, seg=32, mi=0)
    else:
        # Standard / Closed-Chamber Air Spring Bellows
        mb.cyl((0, 0, -0.012), (0, 0, 0.0), 0.062, seg=28, mi=3)
        mb.cyl((0, 0, 0.0), (0, 0, Lsd * 0.18), 0.052, seg=32, mi=0)
        D.bolt_ring(mb, (0, 0, -0.012), -Z, 0.048, 6, 0.0065, 0.0058, 0.2, 3, 3)
        prof = []
        nb = 9
        for i in range(nb * 2 + 1):
            t = Lsd * (0.18 + 0.44 * i / (nb * 2))
            prof.append((0.052 if i % 2 == 0 else 0.039, t))
        mb.lathe(prof, (0, 0, 0), Z, 36, 1)
        for zc in (Lsd * 0.18, Lsd * 0.62):
            mb.torus((0, 0, zc), Z, 0.0525, 0.0032, 32, 5, 2)
        mb.cyl((0, 0, Lsd * 0.62), (0, 0, Lsd * 0.74), 0.046, seg=32, mi=0)
        mb.cyl((0, 0, Lsd * 0.74), (0, 0, Lsd * 0.755), 0.052, seg=32, mi=3)
    out["spring"] = _aimed("XR_Susp_%s_Spring" % name, mb, [M["XR_Spring_Can"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, top, bot, 0.0015, sys="suspension", id="spring")

    # Damper body (`XR_Susp_<name>_Damper`)
    mb = MB()
    if style == "su7":
        # Xiaomi SU7 Ultra: gold body + external piggyback reservoir cylinder
        mb.cyl((0, 0, -0.03), (0, 0, Lsd * 0.62), 0.0265, seg=24, mi=0)
        mb.cyl((0, 0, -0.03), (0, 0, 0.0), 0.034, seg=24, mi=1)
        mb.cyl((0, 0, Lsd * 0.62), (0, 0, Lsd * 0.7), 0.014, seg=14, mi=1)
        rx = Vector((0.052, 0, 0.0))
        mb.cyl(rx + Vector((0, 0, 0.05)), rx + Vector((0, 0, Lsd * 0.42)), 0.0155, seg=18, mi=0)
        mb.cyl(rx + Vector((0, 0, Lsd * 0.42)), rx + Vector((0, 0, Lsd * 0.45)), 0.0115, seg=14, mi=1)
        for zz in (0.07, Lsd * 0.38):
            mb.tube([Vector((0.02, 0, zz)), Vector((0.052, 0, zz))], 0.0075, seg=10, mi=1)
        mb.cyl(rx + Vector((0, 0, Lsd * 0.45)), rx + Vector((0, 0, Lsd * 0.45 + 0.022)), 0.011, seg=12, mi=2)
        d_mats = [M["XR_Damper"], M["XR_Alu_Machined"], M["XR_Plastic_Black"]]
    else:
        # Machined aluminum CDC / DiSus-C / CCD adaptive damper with side-mounted proportional solenoid valve & sensor harness
        mb.cyl((0, 0, -0.03), (0, 0, Lsd * 0.65), 0.0275, seg=24, mi=1)
        mb.cyl((0, 0, -0.03), (0, 0, 0.0), 0.034, seg=24, mi=0)
        mb.cyl((0, 0, Lsd * 0.65), (0, 0, Lsd * 0.72), 0.015, seg=14, mi=1)
        # Compact side-mounted CDC electronic proportional damping solenoid valve near the lower strut body
        vz = Lsd * 0.52
        mb.cyl(Vector((0.022, 0, vz)), Vector((0.054, 0, vz)), 0.016, seg=18, mi=1)
        mb.cyl(Vector((0.054, 0, vz)), Vector((0.068, 0, vz)), 0.012, seg=14, mi=2)
        mb.tube(round_path([Vector((0.066, 0, vz)), Vector((0.072, 0.02, vz - 0.04)), Vector((0.03, 0.04, 0.05))], 0.015, 4), 0.0028, seg=6, mi=2)
        d_mats = [M["XR_Spring_Can"], M["XR_Alu_Machined"], M["XR_Plastic_Black"]]
    out["damper"] = _aimed("XR_Susp_%s_Damper" % name, mb, d_mats, coll, g, top, bot, 0.001, sys="suspension", id="damper")

    mb = MB()
    mb.cyl((0, 0, 0.012), (0, 0, Lsd * 0.36), 0.0105, seg=16, mi=0)
    mb.lathe([(0.0125, 0.02), (0.019, 0.04), (0.013, 0.058), (0.019, 0.076), (0.013, 0.094), (0.019, 0.112), (0.0125, 0.13)], (0, 0, 0), Z, 18, 2)
    mb.cyl((0, 0, -0.025), (0, 0, 0.015), 0.022, seg=18, mi=1)
    mb.bolt((0, 0, -0.025), -Z, 0.0105, 0.009, 1, 1, True)
    out["rod"] = _aimed("XR_Susp_%s_Rod" % name, mb, [M["XR_Alu_Machined"], M["XR_Steel"], M["XR_Rubber"]], coll, g, bot, top, 0.0008, sys="suspension", id="damper_rod")

    kin = {k: to_gltf(v) for k, v in h.items() if isinstance(v, Vector)}
    kin["aim"] = {o.name: json.loads(o["aim"]) for o in (out["tie"], out["spring"], out["damper"], out["rod"])}
    kin["front"] = bool(front)
    g["kin"] = json.dumps(kin, separators=(",", ":"))
    return out


def halfshaft(spec, name, out_pt, coll, root, M):
    h = hardpoints(spec, name)
    s = h["s"]
    H = h["H"]
    p_in = Vector(out_pt)
    p_out = Vector((H.x, s * (abs(H.y) - 0.12), H.z))
    d = p_out - p_in
    L = d.length
    mb = MB()
    mb.cyl((0, 0, 0), (0, 0, L), 0.0165, seg=18, mi=0)

    def boot(z0, z1, rb):
        n = 9
        prof = [(0.017, z0)]
        for i in range(n):
            t = z0 + (z1 - z0) * (i + 0.5) / n
            prof.append((rb if i % 2 == 0 else rb * 0.74, t))
        prof.append((0.017, z1))
        mb.lathe(prof, (0, 0, 0), Z, 24, 1)
        D.clamp(mb, (0, 0, z0 + 0.003), Z, 0.018, 2, 2, 0.008)
        D.clamp(mb, (0, 0, z1 - 0.003), Z, 0.018, 2, 2, 0.008)
    boot(0.0, 0.085, 0.036)
    boot(L - 0.08, L, 0.034)
    mb.cyl((0, 0, -0.012), (0, 0, 0.004), 0.034, seg=22, mi=2)
    mb.cyl((0, 0, L - 0.004), (0, 0, L + 0.025), 0.03, seg=22, mi=2)
    for z in (-0.012, L + 0.0):
        for k in range(6):
            a = 2 * math.pi * k / 6
            mb.sphere(Vector((0.026 * math.cos(a), 0.026 * math.sin(a), z)), 0.0062, 6, 4, 0)
    mb.cyl((0, 0, L * 0.45), (0, 0, L * 0.55), 0.0215, seg=18, mi=2)
    ob = solid("XR_Susp_%s_Halfshaft" % name, mb, [M["XR_Shaft"], M["XR_Rubber"], M["XR_Steel"]], coll, h_group(root, name), pivot=(0, 0, 0), bevel=0.0008, bevel_seg=1, sys="suspension", id="halfshaft")
    _place(ob, p_in, Z.rotation_difference(d.normalized()))
    ob["aim"] = json.dumps([to_gltf(p_in), to_gltf(p_out)], separators=(",", ":"))
    return ob


def h_group(root, name):
    for c in root.children:
        if c.name == "XR_Susp_%s" % name:
            return c
    return root


def anti_roll_bar(spec, axle, coll, root, M):
    front = axle == "front"
    hx, hy, hz = spec.hub_f if front else spec.hub_r
    xb = hx - 0.30
    zb = 0.255
    mb = MB()
    half = [(xb, 0.0, zb), (xb, 0.44, zb), (xb + 0.03, 0.48, zb), (hx - 0.10, 0.56, zb)]
    pts = [(p[0], -p[1], p[2]) for p in reversed(half)] + half[1:]
    mb.tube(round_path(pts, 0.05, 7), 0.0125, seg=16, mi=0)
    for s in (1, -1):
        yb = s * 0.30
        mb.cyl((xb, yb - 0.025, zb), (xb, yb + 0.025, zb), 0.0215, seg=18, mi=2)
        mb.box((xb, yb, zb + 0.0245), 0.05, 0.062, 0.006, 1)
        mb.box((xb, yb, zb + 0.015), 0.036, 0.062, 0.026, 1)
        for sy in (-1, 1):
            mb.bolt((xb, yb + sy * 0.025, zb + 0.0275), Vector((0, 0, 1)), 0.0062, 0.0055, 1, 1, True)
        mb.cyl((hx - 0.10, s * 0.56, zb), (hx - 0.10, s * 0.56, zb - 0.052), 0.0075, seg=10, mi=1)
        mb.sphere((hx - 0.10, s * 0.56, zb), 0.014, 8, 5, 1)
        mb.sphere((hx - 0.10, s * 0.56, zb - 0.052), 0.014, 8, 5, 1)
        mb.bolt((hx - 0.10, s * 0.56, zb + 0.012), Vector((0, 0, 1)), 0.0072, 0.0065, 1, 1, True)
        mb.bolt((hx - 0.10, s * 0.56, zb - 0.066), Vector((0, 0, -1)), 0.0072, 0.0065, 1, 1, True)
    return solid("XR_Susp_ARB_%s" % ("F" if front else "R"), mb, [M["XR_Arm"], M["XR_Steel"], M["XR_Rubber"]], coll, root, (xb, 0, zb), bevel=0.0006, bevel_seg=1, sys="suspension",
                 id="arb_" + ("f" if front else "r"))


def steering_rack(spec, coll, root, M):
    hx, hy, hz = spec.hub_f
    xr = hx - 0.16
    zr = 0.31
    mb = MB()
    mb.cyl((xr, -0.34, zr), (xr, 0.34, zr), 0.0145, seg=18, mi=0)
    mb.cyl((xr, -0.12, zr), (xr, 0.12, zr), 0.034, seg=24, mi=1)
    for yy in (-0.12, 0.12):
        mb.torus((xr, yy, zr), Y, 0.034, 0.003, 24, 5, 1)
    mb.box((xr + 0.0, 0.0, zr + 0.052), 0.07, 0.07, 0.06, 1)
    D.bolt_ring(mb, (xr, 0.0, zr + 0.082), Vector((0, 0, 1)), 0.026, 4, 0.0055, 0.0048, math.pi / 4, 0, 0)
    mb.cyl((xr - 0.07, 0.0, zr + 0.05), (xr - 0.145, 0.0, zr + 0.05), 0.033, seg=24, mi=1)
    mb.cyl((xr - 0.145, 0.0, zr + 0.05), (xr - 0.165, 0.0, zr + 0.05), 0.028, seg=24, mi=1)
    mb.box((xr - 0.105, 0.0, zr + 0.086), 0.034, 0.03, 0.02, 3)
    for sy in (-1, 1):
        mb.box((xr, sy * 0.098, zr - 0.04), 0.04, 0.034, 0.02, 1)
        mb.bolt((xr, sy * 0.098, zr - 0.03), Vector((0, 0, 1)), 0.0075, 0.0065, 0, 0, True)
    for s in (1, -1):
        prof = [(0.0145, 0.0)]
        for i in range(9):
            prof.append((0.0245 if i % 2 == 0 else 0.0175, 0.095 * (i + 0.5) / 9))
        prof.append((0.0145, 0.095))
        mb.lathe(prof, (xr, s * 0.12, zr), Y * s, 22, 2)
        mb.cyl((xr, s * 0.215, zr), (xr, s * 0.34, zr), 0.0095, seg=12, mi=2)
        mb.sphere((xr, s * 0.34, zr), 0.016, 10, 6, 2)
        mb.bolt((xr, s * 0.325, zr), Y * s, 0.0105, 0.0065, 0, 0, False)
        D.clamp(mb, (xr, s * 0.125, zr), Y * s, 0.0147, 0, 0, 0.008)
        D.clamp(mb, (xr, s * 0.212, zr), Y * s, 0.0147, 0, 0, 0.008)
    return solid("XR_Steering_Rack", mb, [M["XR_Steel"], M["XR_Alu_Cast"], M["XR_Rubber"], M["XR_Plastic_Black"]], coll, root, (xr, 0, zr), bevel=0.001, bevel_seg=1, sys="steering", id="rack")


def rear_steering_rack(spec, coll, root, M):
    """Rear-axle active steering actuator across the rear subframe (Denza Z9 e³ dual-actuator RWS or XPeng G9L RWS)."""
    hx, hy, hz = spec.hub_r
    xr = hx - 0.17
    zr = 0.235
    mb = MB()
    mb.cyl((xr, -0.40, zr), (xr, 0.40, zr), 0.0135, seg=18, mi=0)
    mb.cyl((xr, -0.18, zr), (xr, 0.18, zr), 0.032, seg=24, mi=1)
    for yy in (-0.18, 0.0, 0.18):
        mb.torus((xr, yy, zr), Y, 0.033, 0.003, 24, 5, 1)
    for sy in (-1, 1):
        mb.cyl((xr - 0.055, sy * 0.085, zr + 0.038), (xr - 0.125, sy * 0.085, zr + 0.038), 0.026, seg=22, mi=1)
        mb.box((xr - 0.085, sy * 0.085, zr + 0.068), 0.028, 0.024, 0.016, 3)
        mb.box((xr, sy * 0.135, zr - 0.035), 0.036, 0.030, 0.018, 1)
        mb.bolt((xr, sy * 0.135, zr - 0.026), Vector((0, 0, 1)), 0.007, 0.006, 0, 0, True)
    for s in (1, -1):
        prof = [(0.0135, 0.0)]
        for i in range(8):
            prof.append((0.022 if i % 2 == 0 else 0.016, 0.095 * (i + 0.5) / 8))
        prof.append((0.0135, 0.095))
        mb.lathe(prof, (xr, s * 0.18, zr), Y * s, 20, 2)
        mb.cyl((xr, s * 0.275, zr), (xr, s * 0.40, zr), 0.009, seg=12, mi=2)
        mb.sphere((xr, s * 0.40, zr), 0.015, 10, 6, 2)
    return solid("XR_Steering_RearRack", mb, [M["XR_Steel"], M["XR_Alu_Cast"], M["XR_Rubber"], M["XR_Plastic_Black"]], coll, root, (xr, 0, zr), bevel=0.001, bevel_seg=1, sys="steering", id="rear_rack")
