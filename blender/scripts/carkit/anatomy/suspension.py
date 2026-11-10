"""Suspension corners, anti-roll bars, the steering rack and the half-shafts.

`hardpoints(spec, corner)` is the single source of every pickup and joint: the frames build their
bushings from it, the corner builds its arms from it, and it is written into the corner's `kin`
extra so the web viewer can solve the linkage as the wheel moves (src/lib/xray/wishbone.ts).

All positions are offsets from the hub in the wheel's frame, so a wider, longer or taller car
only changes the hub. The wheel itself is the exterior's (its disc sits at the hub plane, the
caliper trails the axle), so the knuckle stays inboard of the disc.

Front: double wishbone with a rack-and-pinion tie rod. Rear: the same two A-arms plus a toe
link (the five links). Both carry an air spring over a damper on the lower arm.

Detail: the arms are forged I-section links that swell at the ball joint and the bushing eyes; every bushing is a steel sleeve in
rubber with its through-bolt and nut; ball joints wear a convoluted dust boot and a castle nut with its cotter pin; the damper
has a gold anodised body, a reservoir with its valve and cable, the air spring a convoluted bellows with crimp rings.
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

    def P(dx, dy, dz):  # relative to the hub, dy outward
        return Vector((hx + dx, s * (hy + dy), hz + dz))

    def W(x, y, z):     # absolute, y given for the left side
        return Vector((x, s * y, z))

    h = {"s": s, "front": front, "H": P(0, 0, 0)}
    zl = 0.205 if front else 0.21
    h["LBJ"] = P(0.0, -0.105, -0.165)
    h["UBJ"] = P(-0.01, -0.11, 0.152)
    h["LF"] = W(hx + (0.20 if front else 0.19), 0.40 if front else 0.42, zl)
    h["LR"] = W(hx - (0.20 if front else 0.17), 0.40 if front else 0.42, zl - 0.005)
    h["UF"] = W(hx + 0.13, 0.50, 0.585)
    h["UR"] = W(hx - 0.13, 0.50, 0.58)
    h["TO"] = P(-0.095, -0.115, -0.04)                      # tie rod / toe link, outer
    h["TI"] = W(hx - 0.16, 0.34, 0.31) if front else W(hx - 0.17, 0.40, 0.235)   # rack end / casting
    # spring-damper: on the lower arm's near link, up to the tower
    link = h["LF"] if front else h["LR"]
    h["SB"] = link + (h["LBJ"] - link) * 0.62
    h["ST"] = Vector((h["SB"].x + (0.0 if front else 0.0), s * 0.50, 0.76))
    h["ABAR"] = Vector((hx - 0.10, s * 0.56, 0.255))       # where the anti-roll bar's drop link meets the lower arm's link
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
    """A pivot bush with its through-bolt: rubber in a steel shell round a steel sleeve, a hex bolt head and a nut."""
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
    """A ball joint: a dome on the arm, a convoluted dust boot up the stud, a castle nut and its cotter pin."""
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
    h = hardpoints(spec, name)
    s, front = h["s"], h["front"]
    H = h["H"]
    g = group("XR_Susp_%s" % name, coll, tuple(H), root, sys="suspension", id=name)
    out = {"group": g, "hp": h}
    Zv = Vector((0, 0, 1))

    def forged_link(mb, a, b, w, hh, mi, swell=1.6, up=Zv):
        """A forged I-section link from a to b whose ends swell into the eyes."""
        n = 10
        pts = [Vector(a).lerp(Vector(b), i / (n - 1)) for i in range(n)]
        sc = [1.0 + (swell - 1.0) * (abs(2 * i / (n - 1) - 1) ** 4) for i in range(n)]
        mb.sweep(pts, profile_I(hh, w, w * 0.22, hh * 0.20), mi=mi, scales=sc, up=up)

    # ---- lower arm: two forged links to one ball joint, bushes with through-bolts at the body end
    # materials: Arm 0, Rubber 1, Steel 2, Bolt 3
    mb = MB()
    for a in (h["LF"], h["LR"]):
        forged_link(mb, a, h["LBJ"], 0.040, 0.024, 0, 1.45)
        _bush(mb, a, X, 0.027, 0.034, 1, 2, 3)
    mb.box_between(h["LF"] + Vector((0, 0, -0.012)), h["LR"] + Vector((0, 0, -0.012)), 0.014, 0.006, up=Zv, mi=0)           # a brace between the bushes
    mb.cyl(h["LF"], h["LR"], 0.0075, seg=8, mi=2)
    # the spring-damper's lower mount and the anti-roll link pad on the near link, drawn as a clevis
    sb = h["SB"]
    mb.box(sb + Vector((0, 0, 0.012)), 0.05, 0.06, 0.016, 0)
    mb.bolt(sb + Vector((0, s * 0.015, 0.02)), Zv, 0.007, 0.006, 3, 3, True)
    _ball_joint(mb, h["LBJ"], Zv, 0.021, 2, 1, 3)
    pivot = (h["LF"] + h["LR"]) / 2
    out["lower"] = solid("XR_Susp_%s_LowerArm" % name, mb, [M["XR_Arm"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, pivot, bevel=0.0012, bevel_seg=1,
                         sys="suspension", id="lower_arm")

    # ---- upper arm
    mb = MB()
    for a in (h["UF"], h["UR"]):
        forged_link(mb, a, h["UBJ"], 0.032, 0.020, 0, 1.4)
        _bush(mb, a, X, 0.023, 0.030, 1, 2, 3)
    mb.cyl(h["UF"], h["UR"], 0.0065, seg=8, mi=2)
    _ball_joint(mb, h["UBJ"], -Zv, 0.018, 2, 1, 3)
    pivot = (h["UF"] + h["UR"]) / 2
    out["upper"] = solid("XR_Susp_%s_UpperArm" % name, mb, [M["XR_Arm"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, pivot, bevel=0.0012, bevel_seg=1,
                         sys="suspension", id="upper_arm")

    # ---- knuckle: a hub carrier behind the disc (bearing housing with a wheel-stud flange and a sensor), legs to the two ball joints, a steering/toe arm and the caliper bridge
    # materials: Knuckle 0, Alu_Machined 1, Steel 2, Bolt 3, Rubber 4
    def P(dx, dy, dz):
        return Vector((H.x + dx, s * (abs(H.y) + dy), H.z + dz))
    out_dir = Vector((0, s, 0))
    mb = MB()
    mb.cyl(P(0, -0.10, 0), P(0, -0.03, 0), 0.052, seg=32, mi=0)
    mb.cyl(P(0, -0.03, 0), P(0, -0.016, 0), 0.046, seg=32, mi=1)
    mb.torus(P(0, -0.0165, 0), out_dir, 0.040, 0.004, 32, 6, 4)
    # the hub flange with its five wheel studs (nuts are on the wheel)
    mb.cyl(P(0, -0.016, 0), P(0, -0.006, 0), 0.062, seg=36, mi=1)
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 2
        st = P(0, -0.006, 0) + Vector((math.cos(a) * 0.0465, 0, math.sin(a) * 0.0465))
        mb.cyl(st, st + out_dir * 0.018, 0.0052, seg=8, mi=2)
        mb.bolt(st + out_dir * 0.0, out_dir, 0.0075, 0.007, 3, 3, False)
    mb.tube([P(0, -0.06, 0), P(0, -0.105, -0.165)], 0.024, seg=14, mi=0, r_end=0.018)
    mb.tube([P(0, -0.06, 0), P(-0.01, -0.11, 0.152)], 0.019, seg=14, mi=0, r_end=0.016)
    mb.box_between(P(-0.03, -0.075, 0.03), P(-0.03, -0.075, -0.13), 0.026, 0.012, up=Y * s, mi=0)           # a web joining the legs
    mb.tube([P(-0.02, -0.075, -0.02), h["TO"]], 0.012, seg=10, mi=0)
    mb.box(P(-0.13, -0.075, 0.0), 0.07, 0.02, 0.2, 0)
    for dz in (-0.07, 0.07):                                                                               # the caliper's two mounting bosses and their bolts
        mb.cyl(P(-0.12, -0.075, dz), P(-0.12, -0.04, dz), 0.016, seg=14, mi=0)
        mb.bolt(P(-0.12, -0.04, dz), out_dir, 0.009, 0.0075, 3, 3, True)
    mb.box(P(0.03, -0.075, 0.05), 0.02, 0.014, 0.02, 2)                                                    # the wheel-speed sensor on its bracket
    mb.cyl(P(0.03, -0.068, 0.05), P(0.03, -0.045, 0.05), 0.006, seg=8, mi=2)
    mb.sphere(h["TO"], 0.015, 10, 6, 2)
    out["knuckle"] = solid("XR_Susp_%s_Knuckle" % name, mb, [M["XR_Knuckle"], M["XR_Alu_Machined"], M["XR_Steel"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, H,
                           bevel=0.0015, bevel_seg=1, sys="suspension", id="knuckle")

    # ---- tie rod (front) / toe link (rear): from the rack end or the casting out to the knuckle, with an adjusting sleeve and lock nuts
    # materials: Arm 0, Steel 1, Rubber 2, Bolt 3
    mb = MB()
    d = h["TO"] - h["TI"]
    L = d.length
    mb.cyl((0, 0, 0), (0, 0, L), 0.0095, seg=12, mi=0)
    mb.cyl((0, 0, L * 0.30), (0, 0, L * 0.62), 0.0135, seg=14, mi=1)                                       # the adjusting sleeve
    mb.bolt((0, 0, L * 0.30), -Z, 0.0112, 0.007, 3, 3, False)
    mb.bolt((0, 0, L * 0.62), Z, 0.0112, 0.007, 3, 3, False)
    mb.sphere((0, 0, 0), 0.015, 10, 6, 1)
    mb.lathe([(0.013, 0.006), (0.017, 0.016), (0.012, 0.026), (0.017, 0.036), (0.011, 0.046)], (0, 0, 0), Z, 14, 2)                           # an inner joint's boot
    out["tie"] = _aimed("XR_Susp_%s_%s" % (name, "TieRod" if front else "ToeLink"), mb, [M["XR_Arm"], M["XR_Steel"], M["XR_Rubber"], M["XR_Bolt"]], coll, g, h["TI"], h["TO"],
                        0.0006, sys="suspension", id="tie_rod" if front else "toe_link")

    # ---- spring and damper, built along +Z from the top mount down to the arm
    top, bot = h["ST"], h["SB"]
    Lsd = (bot - top).length
    # air spring: a top plate with a bolted mount, a rolling convoluted bellows with crimp rings, a piston cup
    mb = MB()
    mb.cyl((0, 0, -0.012), (0, 0, 0.0), 0.062, seg=28, mi=3)
    mb.cyl((0, 0, 0.0), (0, 0, Lsd * 0.18), 0.052, seg=32, mi=0)
    D.bolt_ring(mb, (0, 0, -0.012), -Z, 0.048, 6, 0.0065, 0.0058, 0.2, 3, 3)
    prof = []
    nb = 9
    for i in range(nb * 2 + 1):
        t = Lsd * (0.18 + 0.44 * i / (nb * 2))
        prof.append((0.052 if i % 2 == 0 else 0.039, t))
    mb.lathe(prof, (0, 0, 0), Z, 36, 1)
    for zc in (Lsd * 0.18, Lsd * 0.62):                                                                    # crimp rings at both ends of the bellows
        mb.torus((0, 0, zc), Z, 0.0525, 0.0032, 32, 5, 2)
    mb.cyl((0, 0, Lsd * 0.62), (0, 0, Lsd * 0.74), 0.046, seg=32, mi=0)
    mb.cyl((0, 0, Lsd * 0.74), (0, 0, Lsd * 0.755), 0.052, seg=32, mi=3)
    out["spring"] = _aimed("XR_Susp_%s_Spring" % name, mb, [M["XR_Spring_Can"], M["XR_Rubber"], M["XR_Steel"], M["XR_Bolt"]], coll, g, top, bot, 0.0015, sys="suspension", id="spring")
    # damper: a gold body with a reservoir and its electronic valve, a cable and a dust boot on the rod
    mb = MB()
    mb.cyl((0, 0, -0.03), (0, 0, Lsd * 0.62), 0.0265, seg=24, mi=0)
    mb.cyl((0, 0, -0.03), (0, 0, 0.0), 0.034, seg=24, mi=1)
    mb.cyl((0, 0, Lsd * 0.62), (0, 0, Lsd * 0.7), 0.014, seg=14, mi=1)
    for zc in (0.05, Lsd * 0.3, Lsd * 0.55):
        mb.torus((0, 0, zc), Z, 0.0268, 0.0015, 24, 4, 1)
    # the reservoir: a smaller gold cylinder alongside, joined by two crossovers, with the valve on top
    rx = Vector((0.052, 0, 0.0))
    mb.cyl(rx + Vector((0, 0, 0.05)), rx + Vector((0, 0, Lsd * 0.42)), 0.0155, seg=18, mi=0)
    mb.cyl(rx + Vector((0, 0, Lsd * 0.42)), rx + Vector((0, 0, Lsd * 0.45)), 0.0115, seg=14, mi=1)
    for zz in (0.07, Lsd * 0.38):
        mb.tube([Vector((0.02, 0, zz)), Vector((0.052, 0, zz))], 0.0075, seg=10, mi=1)
    mb.cyl(rx + Vector((0, 0, Lsd * 0.45)), rx + Vector((0, 0, Lsd * 0.45 + 0.022)), 0.011, seg=12, mi=2)
    mb.tube(round_path([rx + Vector((0, 0, Lsd * 0.45 + 0.022)), rx + Vector((0, 0.03, Lsd * 0.45 + 0.06)), Vector((0.02, 0.05, Lsd * 0.2)), Vector((0.0, 0.05, -0.02))], 0.012, 4),
            0.0026, seg=6, mi=2)
    out["damper"] = _aimed("XR_Susp_%s_Damper" % name, mb, [M["XR_Damper"], M["XR_Alu_Machined"], M["XR_Plastic_Black"]], coll, g, top, bot, 0.001, sys="suspension", id="damper")
    mb = MB()      # damper rod and its clevis, built from the bottom mount up toward the top
    mb.cyl((0, 0, 0.012), (0, 0, Lsd * 0.36), 0.0105, seg=16, mi=0)
    mb.lathe([(0.0125, 0.02), (0.019, 0.04), (0.013, 0.058), (0.019, 0.076), (0.013, 0.094), (0.019, 0.112), (0.0125, 0.13)], (0, 0, 0), Z, 18, 2)       # the rod's dust boot
    mb.cyl((0, 0, -0.025), (0, 0, 0.015), 0.022, seg=18, mi=1)
    mb.bolt((0, 0, -0.025), -Z, 0.0105, 0.009, 1, 1, True)
    out["rod"] = _aimed("XR_Susp_%s_Rod" % name, mb, [M["XR_Alu_Machined"], M["XR_Steel"], M["XR_Rubber"]], coll, g, bot, top, 0.0008, sys="suspension", id="damper_rod")

    # ---- kinematics for the web (glTF axes)
    kin = {k: to_gltf(v) for k, v in h.items() if isinstance(v, Vector)}
    kin["aim"] = {o.name: json.loads(o["aim"]) for o in (out["tie"], out["spring"], out["damper"], out["rod"])}
    kin["front"] = bool(front)
    g["kin"] = json.dumps(kin, separators=(",", ":"))
    return out


def halfshaft(spec, name, out_pt, coll, root, M):
    """The half-shaft from a drive unit's output to the hub: splined shaft, a tulip housing at each end, convoluted boots with clamps."""
    h = hardpoints(spec, name)
    s = h["s"]
    H = h["H"]
    p_in = Vector(out_pt)
    p_out = Vector((H.x, s * (abs(H.y) - 0.12), H.z))       # the outer joint, behind the knuckle
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
    # a tulip housing at each end with a row of balls showing through the cage's windows
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
    """A U-shaped bar across the axle, behind it, with a drop link to each lower arm, held by two bushed brackets."""
    front = axle == "front"
    hx, hy, hz = spec.hub_f if front else spec.hub_r
    xb = hx - 0.30
    zb = 0.255
    mb = MB()
    half = [(xb, 0.0, zb), (xb, 0.44, zb), (xb + 0.03, 0.48, zb), (hx - 0.10, 0.56, zb)]
    pts = [(p[0], -p[1], p[2]) for p in reversed(half)] + half[1:]
    mb.tube(round_path(pts, 0.05, 7), 0.0125, seg=16, mi=0)
    for s in (1, -1):
        # the bracket: a rubber bush round the bar held by a pressed-steel strap with two bolts
        yb = s * 0.30
        mb.cyl((xb, yb - 0.025, zb), (xb, yb + 0.025, zb), 0.0215, seg=18, mi=2)
        mb.box((xb, yb, zb + 0.0245), 0.05, 0.062, 0.006, 1)
        mb.box((xb, yb, zb + 0.015), 0.036, 0.062, 0.026, 1)
        for sy in (-1, 1):
            mb.bolt((xb, yb + sy * 0.025, zb + 0.0275), Vector((0, 0, 1)), 0.0062, 0.0055, 1, 1, True)
        # the drop link: a rod with a ball joint and a nut at each end
        mb.cyl((hx - 0.10, s * 0.56, zb), (hx - 0.10, s * 0.56, zb - 0.052), 0.0075, seg=10, mi=1)
        mb.sphere((hx - 0.10, s * 0.56, zb), 0.014, 8, 5, 1)
        mb.sphere((hx - 0.10, s * 0.56, zb - 0.052), 0.014, 8, 5, 1)
        mb.bolt((hx - 0.10, s * 0.56, zb + 0.012), Vector((0, 0, 1)), 0.0072, 0.0065, 1, 1, True)
        mb.bolt((hx - 0.10, s * 0.56, zb - 0.066), Vector((0, 0, -1)), 0.0072, 0.0065, 1, 1, True)
    return solid("XR_Susp_ARB_%s" % ("F" if front else "R"), mb, [M["XR_Arm"], M["XR_Steel"], M["XR_Rubber"]], coll, root, (xb, 0, zb), bevel=0.0006, bevel_seg=1, sys="suspension",
                 id="arb_" + ("f" if front else "r"))


def steering_rack(spec, coll, root, M):
    """The rack across the front subframe, ahead of nothing and behind the front axle: a housing with an assist motor, bellows boots, inner joints, mounting lugs."""
    hx, hy, hz = spec.hub_f
    xr = hx - 0.16
    zr = 0.31
    mb = MB()
    mb.cyl((xr, -0.34, zr), (xr, 0.34, zr), 0.0145, seg=18, mi=0)
    mb.cyl((xr, -0.12, zr), (xr, 0.12, zr), 0.034, seg=24, mi=1)
    for yy in (-0.12, 0.12):
        mb.torus((xr, yy, zr), Y, 0.034, 0.003, 24, 5, 1)
    mb.box((xr + 0.0, 0.0, zr + 0.052), 0.07, 0.07, 0.06, 1)                                              # the pinion housing
    D.bolt_ring(mb, (xr, 0.0, zr + 0.082), Vector((0, 0, 1)), 0.026, 4, 0.0055, 0.0048, math.pi / 4, 0, 0)
    mb.cyl((xr - 0.07, 0.0, zr + 0.05), (xr - 0.145, 0.0, zr + 0.05), 0.033, seg=24, mi=1)               # the assist motor beside it
    mb.cyl((xr - 0.145, 0.0, zr + 0.05), (xr - 0.165, 0.0, zr + 0.05), 0.028, seg=24, mi=1)
    mb.box((xr - 0.105, 0.0, zr + 0.086), 0.034, 0.03, 0.02, 3)                                           # its connector
    for sy in (-1, 1):                                                                                     # mounting lugs on the housing
        mb.box((xr, sy * 0.098, zr - 0.04), 0.04, 0.034, 0.02, 1)
        mb.bolt((xr, sy * 0.098, zr - 0.03), Vector((0, 0, 1)), 0.0075, 0.0065, 0, 0, True)
    for s in (1, -1):
        # bellows boot from the housing to the tie rod's inner joint, a joint housing, a lock nut
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
