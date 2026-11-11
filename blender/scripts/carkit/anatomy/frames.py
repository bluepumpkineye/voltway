"""The structure the hardware hangs on (`spec.chassis_style`):
- `"su7"`: Xiaomi SU7 Ultra — 9,100t rear Hyper Die-Casting with twin V8s motor bays, multi-chamber sills, front cast subframe.
- `"ctb"`: BYD Seal (e-Platform 3.0 Evo CTB) — Cell-to-Body integrated transverse floor crossbeams over the Blade pack,
  forked front load-path rails, and a hollow perimeter 5-link rear cradle around the single 8-in-1 drive unit.
- `"e3_ctb"`: Denza Z9 GT (BYD e³ CTB) — CTB floor crossbeams + heavy e³ rear cradle with twin motor bays and an aft
  mounting bridge for the dual rear-wheel steering actuators.
- `"cib_megacast"`: XPeng G9L (SEPA 2.0) — CIB floor + BOTH front and rear 12,000t one-piece aluminum megacastings with
  integrated high-rising shock-tower truss webs and a single central rear motor bay.
- `"sea_dome"`: Zeekr 7X (SEA PMA2+) — 7,200t one-piece rear underbody megacasting (single motor bay) + 2,000 MPa central
  B-pillar "Safety Dome" structural arch ring across the floor frame.
- `"nt2_swap"`: NIO ES8 (NT2.0 All-Aluminum) — deep extruded aluminum sills with 10 Power Swap bayonet receiver housings,
  cast front/rear torque boxes, and hollow cast rear subframe cradle.
- `"tuling"` / `"chn"` / `"essa"`: Luxeed R7 (E0X Tuoling), Avatr 06T (CHN), and Voyah Passion S (ESSA) single-rear-motor
  cast subframes and reinforced floor structures.
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
    """A multi-chamber aluminium extrusion from a to b, `h` tall and `w` wide."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    pitch = (w - wall) / chambers
    holes = []
    for k in range(chambers):
        c = -w / 2 + wall / 2 + pitch * (k + 0.5)
        if axis_name == 'x':
            holes.append(rrect(h - 2 * wall, pitch - wall, 0.003, 2, 0.0, c))
        else:
            holes.append(rrect(pitch - wall, h - 2 * wall, 0.003, 2, c, 0.0))
    outer = rrect(h, w, r) if axis_name == 'x' else rrect(w, h, r)
    mb.prism(outer, holes, 0.0, L, a, (b - a), mi)


def build(spec, coll, root, M):
    out = {}
    style = getattr(spec, "chassis_style", "su7")
    hfx, hfy, hfz = spec.hub_f
    hrx, hry, hrz = spec.hub_r
    p = spec.pack
    twin_rear = sum(1 for m in spec.motors if m.axle == "rear") >= 2

    # =========================================================================
    # 1. FLOOR FRAME (`XR_Frame_Floor`)
    # =========================================================================
    g = group("XR_Frame_Floor_G", coll, (0, 0, 0), root, sys="chassis", id="floor")
    mb = MB()
    xa, xb = hrx - 0.12, hfx - 0.34
    zs = (spec.under_z + 0.02 + spec.floor_z + 0.015) / 2
    hs = spec.floor_z + 0.015 - (spec.under_z + 0.02)
    sill_w = 0.135 if style in ("ctb", "e3_ctb", "cib_megacast", "nt2_swap") else 0.11
    sill_ch = 4 if style in ("ctb", "e3_ctb", "cib_megacast", "nt2_swap") else 3

    for s in (1, -1):
        extrusion(mb, (xa, s * spec.sill_y, zs), (xb, s * spec.sill_y, zs), sill_w, hs, 'x', sill_ch, 0.0042, 0)
        for k in range(14):
            x = xa + 0.12 + (xb - xa - 0.24) * k / 13
            mb.bolt((x, s * spec.sill_y, zs + hs / 2), Zv, 0.0068, 0.0056, 1, 1, True)
        for x in (xa, xb):
            mb.box((x + (0.012 if x == xa else -0.012), s * spec.sill_y, zs), 0.008, sill_w + 0.014, hs + 0.012, 2)

    # Fore and aft bulkhead cross-members
    for x in (p["x1"] + 0.12, p["x0"] - 0.1):
        zc = spec.floor_z + 0.02
        extrusion(mb, (x, -spec.sill_y, zc), (x, spec.sill_y, zc), 0.08, 0.10, 'y', 2, 0.0042, 0, 0.007)
        for k in range(9):
            y = -spec.sill_y + 0.12 + (2 * spec.sill_y - 0.24) * k / 8
            mb.bolt((x, y, zc + 0.05), Zv, 0.0062, 0.005, 1, 1, True)

    if style in ("ctb", "e3_ctb"):
        # BYD CTB (Cell-to-Body): 3 heavy extruded seat/floor cross-beams bridging sill-to-sill directly above the Blade pack
        # plus dual-path front torque-box fork rails tying the sills into the front subframe
        z_ctb = spec.floor_z + 0.032
        for frac in (0.26, 0.52, 0.74):
            x_beam = p["x0"] + (p["x1"] - p["x0"]) * frac
            extrusion(mb, (x_beam, -spec.sill_y, z_ctb), (x_beam, spec.sill_y, z_ctb), 0.072, 0.042, 'y', 2, 0.004, 2, 0.006)
            for s in (1, -1):
                mb.box((x_beam, s * (spec.sill_y - 0.04), z_ctb - 0.015), 0.11, 0.09, 0.045, 0)
        for s in (1, -1):
            mb.box_between((xb, s * spec.sill_y, zs), (hfx - 0.36, s * 0.42, 0.23), 0.075, 0.065, up=Zv, mi=0)
    elif style == "sea_dome":
        # Zeekr 7X "Safety Dome": arched B-pillar ring frame rising over the center cabin floor + central backbone tunnel
        x_dome = (p["x0"] + p["x1"]) * 0.52
        z_base = spec.floor_z + 0.02
        mb.box_between((p["x0"] - 0.08, 0.0, z_base + 0.025), (p["x1"] + 0.10, 0.0, z_base + 0.025), 0.12, 0.055, up=Zv, mi=2)
        extrusion(mb, (x_dome, -spec.sill_y, z_base + 0.04), (x_dome, spec.sill_y, z_base + 0.04), 0.095, 0.065, 'y', 3, 0.0045, 2, 0.008)
        for s in (1, -1):
            # B-pillar lower structural arch gussets rising from the sill
            mb.box_between((x_dome, s * spec.sill_y, zs), (x_dome, s * (spec.sill_y + 0.03), zs + 0.34), 0.09, 0.065, up=X, mi=2)
            mb.box_between((x_dome - 0.18, s * spec.sill_y, zs + 0.04), (x_dome, s * spec.sill_y, zs + 0.28), 0.05, 0.045, up=Y, mi=0)
    elif style == "nt2_swap":
        # NIO NT2.0 All-Aluminum Floor: 10 cast bayonet swap-lock receiver housings along the sills + triangulated front/rear torque boxes
        L_pack = p["x1"] - p["x0"]
        for i in range(5):
            x_sw = p["x0"] + 0.14 + (L_pack - 0.28) * i / 4
            for s in (1, -1):
                yb_ = s * (p["hw"] + 0.068)
                mb.cyl((x_sw, yb_, zs - hs / 2 - 0.015), (x_sw, yb_, zs + hs / 2 + 0.01), 0.034, seg=20, mi=2)
                mb.box_between((x_sw, yb_, zs), (x_sw, s * spec.sill_y, zs), 0.075, hs * 0.85, up=Zv, mi=0)
        for s in (1, -1):
            mb.box_between((xb, s * spec.sill_y, zs), (p["x1"] + 0.12, s * 0.44, zs), 0.085, hs * 0.9, up=Zv, mi=0)
            mb.box_between((xa, s * spec.sill_y, zs), (p["x0"] - 0.10, s * 0.44, zs), 0.085, hs * 0.9, up=Zv, mi=0)
    elif style == "cib_megacast":
        # XPeng G9L SEPA 2.0 CIB: integrated grid of 3 transverse cross-members and central spine
        z_cib = spec.floor_z + 0.025
        for frac in (0.25, 0.50, 0.75):
            xb_ = p["x0"] + (p["x1"] - p["x0"]) * frac
            extrusion(mb, (xb_, -spec.sill_y, z_cib), (xb_, spec.sill_y, z_cib), 0.065, 0.038, 'y', 2, 0.004, 0, 0.005)
    elif style in ("tuling", "chn", "essa"):
        # Multi-ring floor reinforcement cross-member + diagonal front torque struts
        x_mid = (p["x0"] + p["x1"]) * 0.5
        extrusion(mb, (x_mid, -spec.sill_y, spec.floor_z + 0.025), (x_mid, spec.sill_y, spec.floor_z + 0.025), 0.075, 0.045, 'y', 2, 0.004, 0, 0.006)
        for s in (1, -1):
            mb.box_between((xb, s * spec.sill_y, zs), (p["x1"] + 0.12, s * 0.46, zs), 0.068, hs * 0.8, up=Zv, mi=0)

    for k in range(4):
        x = xa + 0.25 + (xb - xa - 0.5) * k / 3
        for s in (1, -1):
            mb.box((x, s * (spec.sill_y + 0.07), zs), 0.07, 0.05, 0.012, 0)
            mb.bolt((x, s * (spec.sill_y + 0.07), zs + 0.006), Zv, 0.008, 0.0065, 1, 1, True)
    out["floor"] = solid("XR_Frame_Floor", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Alu_Machined"]], coll, g, centre(mb), bevel=0.0035, bevel_seg=1, sys="chassis", id="floor")

    # =========================================================================
    # 2. FRONT SUBFRAME (`XR_Frame_SubF`)
    # =========================================================================
    g = group("XR_Frame_SubF_G", coll, (hfx, 0, 0.21), root, sys="chassis", id="subframe_f")
    mb = MB()
    zf = 0.215
    xr0, xr1 = hfx - 0.40, hfx + 0.38
    Lf, Wf = xr1 - xr0, 0.88
    cx = (xr0 + xr1) / 2
    zp0, zp1 = zf - 0.036, zf - 0.024
    holes = []
    for k in range(3):
        hx_ = xr0 + 0.10 + k * (Lf - 0.2) / 3
        holes.append(rrect((Lf - 0.2) / 3 - 0.07, 0.30, 0.05, 4, hx_ + ((Lf - 0.2) / 3 - 0.07) / 2, 0.20))
        holes.append(rrect((Lf - 0.2) / 3 - 0.07, 0.30, 0.05, 4, hx_ + ((Lf - 0.2) / 3 - 0.07) / 2, -0.20))
    mb.prism(rrect(Lf, Wf, 0.05, 5, cx, 0.0), holes, zp0, zp1, (0, 0, 0), Zv, 0)
    mb.prism(rrect(Lf, Wf, 0.05, 5, cx, 0.0), [rrect(Lf - 0.024, Wf - 0.024, 0.04, 5, cx, 0.0)], zp1, zf + 0.04, (0, 0, 0), Zv, 0)
    for hl in holes:
        mb.prism([(x * 1.0, y * 1.0) for (x, y) in _grow(hl, 0.012)], [hl], zp1, zf + 0.022, (0, 0, 0), Zv, 0)
    for s in (1, -1):
        extrusion(mb, (xr0, s * 0.40, zf - 0.065), (xr1, s * 0.40, zf - 0.065), 0.07, 0.05, 'x', 2, 0.005, 0, 0.006)
        for x in (xr0 + 0.02, xr1 - 0.02):
            mb.cyl((x, s * 0.40, zf - 0.095), (x, s * 0.40, zf - 0.04), 0.03, seg=18, mi=0)
            mb.bolt((x, s * 0.40, zf - 0.095), -Zv, 0.0105, 0.009, 1, 1, True)
    mb.box_between((hfx - 0.16, -0.40, zf + 0.04), (hfx - 0.16, 0.40, zf + 0.04), 0.06, 0.05, mi=0)

    if style in ("cib_megacast", "tuling", "sea_dome"):
        # Integrated front megacasting / high-mount aluminum tower trusses rising from the front rails to the upper wishbone mounts
        for s in (1, -1):
            mb.box_between((hfx + 0.16, s * 0.42, zf + 0.02), (hfx + 0.05, s * 0.48, 0.56), 0.055, 0.042, up=Y * s, mi=0)
            mb.box_between((hfx - 0.18, s * 0.42, zf + 0.02), (hfx - 0.05, s * 0.48, 0.56), 0.055, 0.042, up=Y * s, mi=0)
            # Honeycomb cross-web between the two rising struts
            mb.box_between((hfx + 0.10, s * 0.45, 0.36), (hfx - 0.10, s * 0.45, 0.46), 0.035, 0.018, up=Y * s, mi=0)
            mb.box_between((hfx - 0.10, s * 0.45, 0.36), (hfx + 0.10, s * 0.45, 0.46), 0.035, 0.018, up=Y * s, mi=0)

    for c in ("FL", "FR"):
        h = hardpoints(spec, c)
        for k in ("LF", "LR"):
            mb.box(Vector(h[k]) + Vector((0, -h["s"] * 0.03, 0)), 0.07, 0.06, 0.08, 0)
            _bush(mb, h[k], X, 0.026, 0.032, 2, 1, 1, False)
    D.bolt_line(mb, (xr0 + 0.05, -0.43, zf + 0.04), (xr1 - 0.05, -0.43, zf + 0.04), 7, Zv, 0.006, 0.005, 1, 1)
    D.bolt_line(mb, (xr0 + 0.05, 0.43, zf + 0.04), (xr1 - 0.05, 0.43, zf + 0.04), 7, Zv, 0.006, 0.005, 1, 1)
    out["sub_f"] = solid("XR_Frame_SubF", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, centre(mb), bevel=0.003, bevel_seg=1, sys="chassis", id="subframe_f")

    # =========================================================================
    # 3. FRONT CRASH BEAM (`XR_Frame_CrashF`)
    # =========================================================================
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

    # =========================================================================
    # 4. REAR SUBFRAME / MEGACASTING (`XR_Frame_SubR`)
    # =========================================================================
    xr_a, xr_b = hrx - 0.55, p["x0"] - 0.08
    wy = 0.72
    cx, L = (xr_a + xr_b) / 2, xr_b - xr_a
    g = group("XR_Frame_SubR_G", coll, (cx, 0, 0.2), root, sys="chassis", id="subframe_r")
    mb = MB()

    if style in ("ctb", "tuling", "chn", "essa", "nt2_swap"):
        # Hollow Perimeter Multi-Link Rear Cradle Frame (used on BYD Seal, Luxeed R7, Avatr 06T, NIO ES8, Voyah Passion S)
        # Two longitudinal hydroformed/cast side rails + front & rear arched cross-members framing a SINGLE central motor bay!
        for s in (1, -1):
            extrusion(mb, (xr_a + 0.04, s * 0.43, 0.225), (xr_b - 0.02, s * 0.43, 0.225), 0.085, 0.065, 'x', 2, 0.0045, 0, 0.008)
            # Outrigger body-mount arms with large subframe isolation bushings
            for xm in (xr_a + 0.08, xr_b - 0.08):
                mb.box_between((xm, s * 0.43, 0.225), (xm, s * 0.58, 0.255), 0.075, 0.052, up=Zv, mi=0)
                _bush(mb, (xm, s * 0.58, 0.255), Zv, 0.036, 0.028, 2, 1, 1, True)
        # Front & rear cradle cross-members around the central drive unit
        extrusion(mb, (xr_b - 0.07, -0.46, 0.225), (xr_b - 0.07, 0.46, 0.225), 0.085, 0.06, 'y', 2, 0.0045, 0, 0.007)
        extrusion(mb, (xr_a + 0.09, -0.46, 0.225), (xr_a + 0.09, 0.46, 0.225), 0.085, 0.06, 'y', 2, 0.0045, 0, 0.007)
        # Diagonal torque-reaction struts from side rails to the front cross-member
        for s in (1, -1):
            mb.box_between((xr_a + 0.12, s * 0.41, 0.22), (xr_b - 0.07, s * 0.16, 0.22), 0.055, 0.038, up=Zv, mi=0)
    else:
        # Ribbed Megacasting / e³ Tri-Motor Rear Underbody Casting (`su7`, `e3_ctb`, `cib_megacast`, `sea_dome`)
        hl = []
        if twin_rear:
            # Twin motor openings (`RL` and `RR` on Xiaomi SU7 Ultra & Denza Z9 GT e³)
            for cy in (-0.47, 0.47):
                hl.append([(cx + x, cy + y) for (x, y) in rrect(0.30, 0.20, 0.03)])
        else:
            # Single central motor opening + outboard lightening pockets (`cib_megacast` XPeng G9L & `sea_dome` Zeekr 7X)
            hl.append([(cx + x, y) for (x, y) in rrect(0.36, 0.30, 0.04)])
            for cy in (-0.48, 0.48):
                hl.append([(cx + x, cy + y) for (x, y) in rrect(0.24, 0.16, 0.03)])
        mb.prism([(cx + x, y) for (x, y) in rrect(L, 2 * wy, 0.07)], hl, 0.195, 0.202, (0, 0, 0), Zv, 0)
        for y in (-0.18, 0.18, -0.36, 0.36):
            mb.box((cx, y, 0.2275), L - 0.06, 0.012, 0.055, 0)
        for k in range(4):
            mb.box((xr_a + 0.06 + k * (L - 0.12) / 3, 0, 0.2275), 0.012, 2 * wy - 0.1, 0.055, 0)
        mb.box((cx, wy - 0.01, 0.2275), L, 0.014, 0.06, 0)
        mb.box((cx, -wy + 0.01, 0.2275), L, 0.014, 0.06, 0)
        # Diagonal honeycomb ribs
        for y0, y1 in ((-0.36, -0.18), (0.18, 0.36)):
            for k in range(3):
                xa_ = xr_a + 0.06 + k * (L - 0.12) / 3
                xb_ = xr_a + 0.06 + (k + 1) * (L - 0.12) / 3
                mb.box_between((xa_, y0, 0.2275), (xb_, y1, 0.2275), 0.007, 0.05, up=Zv, mi=0)
                mb.box_between((xa_, y1, 0.2275), (xb_, y0, 0.2275), 0.007, 0.05, up=Zv, mi=0)
        if style in ("cib_megacast", "sea_dome"):
            # High-rising rear megacasting side rails & shock-tower truss webs (12,000t XPeng G9L / 7,200t Zeekr 7X)
            for s in (1, -1):
                mb.box_between((xr_a + 0.06, s * 0.52, 0.24), (xr_b - 0.04, s * 0.52, 0.34), 0.085, 0.095, up=Zv, mi=0)
                mb.box_between((hrx + 0.14, s * 0.50, 0.26), (hrx + 0.04, s * 0.50, 0.54), 0.055, 0.042, up=Y * s, mi=0)
                mb.box_between((hrx - 0.16, s * 0.50, 0.26), (hrx - 0.04, s * 0.50, 0.54), 0.055, 0.042, up=Y * s, mi=0)
        if style == "e3_ctb":
            # Denza Z9 GT e³: dedicated aft cross-beam cradle supporting the dual rear-steering actuators
            mb.box_between((hrx - 0.17, -0.48, 0.205), (hrx - 0.17, 0.48, 0.205), 0.095, 0.048, up=Zv, mi=0)

    for c in ("RL", "RR"):
        h = hardpoints(spec, c)
        for k in ("LF", "LR"):
            mb.box(Vector(h[k]) + Vector((0, 0, -0.01)), 0.07, 0.06, 0.07, 0)
            _bush(mb, h[k], X, 0.026, 0.032, 2, 1, 1, False)
        mb.box(Vector(h["TI"]), 0.05, 0.05, 0.05, 0)
    out["sub_r"] = solid("XR_Frame_SubR", mb, [M["XR_Alu_Cast"], M["XR_Bolt"], M["XR_Rubber"]], coll, g, centre(mb), bevel=0.0025, bevel_seg=1, sys="chassis", id="subframe_r")

    # =========================================================================
    # 5. REAR CRASH BEAM (`XR_Frame_CrashR`)
    # =========================================================================
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
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for (x, y) in poly:
        vx, vy = x - cx, y - cy
        L = math.hypot(vx, vy) or 1.0
        out.append((x + vx / L * d, y + vy / L * d))
    return out


def _can(mb, a, b, w, h, mi):
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
    for t in (0.3, 0.55, 0.8):
        mb.prism(rrect(h + 0.006, w + 0.006, 0.007), [rrect(h - 0.002, w - 0.002, 0.005)], 0.0, 0.006, a + u * (L * t), d, mi)


def tower(spec, corner, coll, parent, M):
    """The shock tower over a wheel: a ribbed cone up to a bolted plate with a locking nut, braced to the sill."""
    h = hardpoints(spec, corner)
    top = h["ST"]
    base = Vector((top.x, top.y, 0.40))
    mb = MB()
    mb.cyl(base, top - Vector((0, 0, 0.012)), 0.105, 0.078, seg=32, mi=0)
    mb.cyl(top - Vector((0, 0, 0.012)), top, 0.098, seg=32, mi=0)
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
