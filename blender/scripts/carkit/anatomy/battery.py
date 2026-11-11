"""The traction pack, built from the spec's pack box with OEM-specific architectures (`spec.pack_style`):
- `"blade"`: BYD LFP Blade Battery in CTB (Cell-to-Body) configuration — full-width sill-to-sill transverse blade cells,
  direct-refrigerant micro-channel cooling plate, and CTB cabin-floor structural crossbeams.
- `"swap"`: NIO Power Swap pack — perimeter frame with 10 quick-swap bayonet locking cones/receivers, guide pins, and CTP blocks.
- `"qilin"`: CATL Qilin CTP 3.0 — vertical liquid-cooled elastic interlayers between cell blocks and high-rate 5C+ busbars.
- `"whale_800v"`: Huawei Giant Whale / CATL Shenxing 800V — central orange-armored 800V busbar spine, aerogel firewalls, 800V BDU.
- `"cib"`: XPeng SEPA 2.0 CIB (Cell-Integrated-Body) — integrated structural cross-members and 5C twin copper busbars.
- `"mica"`: Voyah Cloud Mica / Amber semi-solid pack — amber mica thermal barriers framing 4-column modules.

The top lid (`XR_Battery_Lid`) and sensing film (`XR_Battery_Film`) are built as an architectural cutaway over the rear/middle
two-thirds of the pack so the internal cell technology, busbars, and cooling channels are directly visible in the 3D X-ray view.
"""
import math

from mathutils import Vector

from . import detail as D
from .prim import MB, X, Y, Z, circle, collection, group, rrect, solid

Zv = Vector((0, 0, 1))


def centre(mb):
    xs = [v[0] for v in mb.v]
    ys = [v[1] for v in mb.v]
    zs = [v[2] for v in mb.v]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)


def _flange_points(x0, x1, hw, z, step=0.11):
    """Bolt positions round the flange: along both long sides and across both ends (corners skipped)."""
    L, W = x1 - x0, 2 * hw
    xc = (x0 + x1) / 2
    pts = []
    n = int(L / step)
    for i in range(n + 1):
        x = x0 + 0.05 + (L - 0.10) * i / n
        for s in (1, -1):
            pts.append((x, s * (hw + 0.0175), z))
    m = int(W / step)
    for i in range(1, m):
        y = -hw + W * i / m
        for s in (1, -1):
            pts.append((xc + s * (L / 2 + 0.0175), y, z))
    return pts


def build(spec, coll, root, M):
    p = spec.pack
    style = getattr(spec, "pack_style", "blocks")
    x0, x1, hw, z0 = p["x0"], p["x1"], p["hw"], p["z0"]
    L, W = x1 - x0, 2 * hw
    xc = (x0 + x1) / 2
    g = group("XR_Battery", coll, (xc, 0, z0), root, sys="battery", id="battery")
    out = {"group": g}
    corner = 0.07
    zw = z0 + 0.120                      # the tray wall's top
    flange = _flange_points(x0, x1, hw, zw)
    pitch = (L - 0.04) / 6

    # ---- tray: floor, walls, flange, cross-partitions, and OEM-specific mounting hardware
    mb = MB()
    mb.prism(rrect(L, W, corner), [], z0, z0 + 0.012, (xc, 0, 0), mi=0)
    mb.prism(rrect(L, W, corner), [rrect(L - 0.036, W - 0.036, corner - 0.012)], z0 + 0.012, zw, (xc, 0, 0), mi=0)
    mb.prism(rrect(L + 0.07, W + 0.07, 0.09), [rrect(L - 0.01, W - 0.01, corner)], zw - 0.008, zw, (xc, 0, 0), mi=0)
    mb.prism(rrect(L + 0.048, W + 0.048, 0.08), [rrect(L + 0.036, W + 0.036, 0.075)], zw, zw + 0.0032, (xc, 0, 0), mi=2)

    if style == "blade":
        # BYD CTB Blade tray: no central longitudinal divider (cells span sill-to-sill), thicker side extrusion honeycomb walls
        for s in (1, -1):
            mb.box((xc, s * (hw + 0.028), (z0 + zw) / 2), L - 0.08, 0.038, zw - z0 - 0.01, 4)
        for i in range(1, 4):
            xb_ = x0 + i * L / 4
            mb.box((xb_, 0, z0 + 0.018), 0.022, W - 0.04, 0.010, 4)
    else:
        for i in range(1, 6):
            mb.box((x0 + 0.02 + i * pitch, 0, z0 + 0.0495), 0.014, W - 0.036, 0.075, 4)
            mb.box((x0 + 0.02 + i * pitch, 0, z0 + 0.088), 0.026, W - 0.2, 0.0035, 0)
        mb.box((xc, 0, z0 + 0.0495), L - 0.036, 0.018, 0.075, 4)
        for i in range(1, 6):
            for s in (-1, 1):
                mb.bolt((x0 + 0.02 + i * pitch, s * (W / 2 - 0.20), z0 + 0.0905), Zv, 0.0058, 0.005, 1, 1, True)

    for (x, y, z) in flange:
        mb.bolt((x, y, z), Zv, 0.0068, 0.0056, 1, 1, True)

    if style == "swap":
        # NIO Power Swap: 10 heavy machined bayonet quick-swap locking cones + 4 guide pins along the outer perimeter
        for i in range(5):
            x = x0 + 0.14 + (L - 0.28) * i / 4
            for s in (1, -1):
                yb_ = s * (hw + 0.068)
                mb.prism(rrect(0.11, 0.078, 0.028), [circle(0.020, 18)], z0 + 0.002, zw - 0.002, (x, yb_, 0), mi=4)
                mb.cyl((x, yb_, z0 - 0.012), (x, yb_, zw + 0.012), 0.024, seg=20, mi=1)
                mb.cyl((x, yb_, zw + 0.012), (x, yb_, zw + 0.026), 0.016, seg=18, mi=1)
                mb.bolt((x, yb_, z0 - 0.012), -Zv, 0.015, 0.010, 1, 1, True)
        # 2 front and 2 rear tapered swap station alignment cones
        for x_pin in (x0 + 0.06, x1 - 0.06):
            for s in (1, -1):
                mb.cyl((x_pin, s * (hw - 0.18), z0 - 0.022), (x_pin, s * (hw - 0.18), z0 + 0.005), 0.022, 0.008, seg=16, mi=1)
    else:
        for i in range(4):
            x = x0 + 0.18 + (L - 0.36) * i / 3
            for s in (1, -1):
                mb.prism(rrect(0.07, 0.05, 0.02), [circle(0.012, 14)], zw - 0.016, zw - 0.006, (x, s * (hw + 0.058), 0), mi=0)
                mb.bolt((x, s * (hw + 0.058), zw - 0.006), Zv, 0.0085, 0.007, 1, 1, True)

    for k in range(-3, 4):
        mb.box((xc, k * 0.17, z0 - 0.0035), L - 0.12, 0.022, 0.007, 4)
    D.sticker(mb, (x1 - 0.30, hw, z0 + 0.062), Vector((-1, 0, 0)), Z, 0.07, 0.045, "plate", 3)
    out["tray"] = solid("XR_Battery_Tray", mb, [M["XR_Sheet"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Alu_Cast"]], coll, g, centre(mb),
                        bevel=0.0018, bevel_seg=1, sys="battery", id="tray")

    # ---- cold plate / thermal management (`XR_Battery_Plate`)
    mb = MB()
    mb.prism(rrect(L - 0.04, W - 0.04, 0.05), [], z0 + 0.012, z0 + 0.020, (xc, 0, 0), mi=0)
    zr = z0 + 0.0235
    xa, xb = x0 + 0.10, x1 - 0.10

    if style == "blade":
        # BYD direct refrigerant cooling: parallel multi-port micro-channel flat rails + upper side refrigerant manifolds
        for k in range(10):
            yk = -hw + 0.09 + k * (W - 0.18) / 9
            mb.box((xc, yk, zr), L - 0.14, 0.024, 0.0055, 1)
        # Front & rear refrigerant collector headers + twin TXV expansion valves
        for xh in (xa, xb):
            mb.cyl((xh, -hw + 0.07, zr + 0.003), (xh, hw - 0.07, zr + 0.003), 0.012, seg=16, mi=2)
        for s in (1, -1):
            yy = s * (hw - 0.14)
            mb.box((x1 + 0.015, yy, zr + 0.006), 0.055, 0.042, 0.028, 2)     # TXV expansion block
            D.fitting(mb, (x1 + 0.042, yy, zr + 0.006), (x1 + 0.09, yy, zr + 0.006), 0.010, 1, 2)
    elif style == "qilin":
        # CATL Qilin CTP 3.0: vertical elastic liquid-cooled interlayers standing between the transverse cell blocks!
        for i in range(7):
            xi = x0 + 0.02 + i * pitch
            mb.box((xi, 0, z0 + 0.058), 0.009, W - 0.08, 0.074, 1)
            mb.box((xi, 0, z0 + 0.096), 0.014, W - 0.08, 0.005, 2)
        # Side manifold headers feeding all 7 vertical elastic cooling walls
        for s in (1, -1):
            ym = s * (hw - 0.032)
            mb.cyl((xa - 0.04, ym, z0 + 0.062), (xb + 0.06, ym, z0 + 0.062), 0.013, seg=16, mi=1)
            D.fitting(mb, (x1 - 0.01, ym, z0 + 0.062), (x1 + 0.065, ym, z0 + 0.062), 0.011, 1, 2)
    else:
        for s in (1, -1):
            ys = [s * (0.07 + k * 0.115) for k in range(6)]
            path = []
            for k, y in enumerate(ys):
                path += [(xa, y, zr), (xb, y, zr)] if k % 2 == 0 else [(xb, y, zr), (xa, y, zr)]
            pts = D.round_path(path, 0.05, 6)
            mb.sweep(pts, D.flat_prof(0.0065, 0.018), mi=0, up=Zv)
            yy = ys[0]
            mb.tube(D.round_path([(x1 - 0.12, yy, zr), (x1 - 0.06, yy, zr), (x1 + 0.02, yy, zr)], 0.03, 5), 0.0105, seg=14, mi=2)
            D.fitting(mb, (x1 - 0.005, yy, zr), (x1 + 0.062, yy, zr), 0.0108, 1, 2)
            D.clamp(mb, (x1 + 0.052, yy, zr), X, 0.0112, 2, 2)

    out["plate"] = solid("XR_Battery_Plate", mb, [M["XR_Alu_Cast"], M["XR_Coolant"], M["XR_Alu_Machined"]], coll, g, centre(mb), bevel=0.001, bevel_seg=1,
                         sys="battery", id="plate")

    # ---- cell blocks (`XR_Battery_Cells_01..12`) and busbars (`XR_Battery_Busbars`)
    zc0 = z0 + 0.022
    zf = z0 + 0.094
    out["cells"] = []
    bi = 0
    bus = MB()

    if style == "blade":
        # BYD Blade Battery (CTB): 12 groups of long flat LFP blades spanning the ENTIRE pack width from sill to sill
        blade_len = (hw - 0.026) * 2
        blade_t, blade_pitch = 0.0145, 0.0180
        blade = MB()
        # Extruded aluminum blade housing (mi=1) with cyan-blue end wrap (mi=0) and side-facing axial terminals (mi=2)
        blade.prism(rrect(blade_t, blade_len, 0.0025, 2), [], zc0, zf + 0.006, (0, 0, 0), mi=1)
        blade.box((0, 0, zf + 0.0075), blade_t * 0.86, blade_len * 0.92, 0.0022, 0)
        for s in (1, -1):
            blade.box((0, s * (blade_len * 0.485), (zc0 + zf) / 2 + 0.018), blade_t * 0.65, 0.018, 0.022, 2)
            blade.cyl((0, s * (blade_len * 0.475), zf + 0.006), (0, s * (blade_len * 0.475), zf + 0.0155), 0.0042, seg=8, mi=2)
        sec_pitch = (L - 0.05) / 12
        for i in range(12):
            bx0 = x0 + 0.025 + i * sec_pitch + 0.003
            inner = sec_pitch - 0.006
            n_s = max(4, int(inner // blade_pitch))
            xs = bx0 + (inner - n_s * blade_pitch) / 2
            mb = MB()
            for j in range(n_s):
                xj = xs + (j + 0.5) * blade_pitch
                mb.append(blade, (xj, 0.0, 0))
                if j < n_s - 1:
                    mb.box((xj + blade_pitch / 2, 0.0, (zc0 + zf) / 2), 0.0025, blade_len * 0.96, zf - zc0 - 0.004, 3)
            xa_, xb_ = xs, xs + n_s * blade_pitch
            # Transverse structural honeycomb partition between blade groups
            mb.box((xb_ + 0.002, 0.0, (zc0 + zf) / 2 + 0.004), 0.004, blade_len + 0.008, zf - zc0 + 0.010, 4)
            bi += 1
            nm = "XR_Battery_Cells_%02d" % bi
            ob = solid(nm, mb, [M["XR_Cell"], M["XR_Alu_Machined"], M["XR_Brass"], M["XR_Plastic_Black"], M["XR_Steel"]], coll, g, centre(mb), bevel=0.0,
                       sys="battery", id="cells", n=bi)
            out["cells"].append(ob)
            # Sill-side copper series busbars running along the left and right edges of the Blade array
            for s in (1, -1):
                yb = s * (blade_len * 0.475)
                bus.box(((xa_ + xb_) / 2, yb, zf + 0.0165), xb_ - xa_ - 0.002, 0.016, 0.0026, 0)
                for j in range(n_s):
                    bus.bolt((xs + (j + 0.5) * blade_pitch, yb, zf + 0.018), Zv, 0.0036, 0.0026, 1, 1, False)
        # Sill-side orange HV collector rails instead of a central spine
        for s in (1, -1):
            bus.box((xc, s * (blade_len * 0.43), z0 + 0.111), L - 0.16, 0.022, 0.0055, 0)
    elif style == "mica":
        # Voyah Cloud Mica / Amber 4-column module layout with golden/amber mica thermal-runaway barriers
        col_w = (hw - 0.045) / 2
        for col_idx, yc in enumerate((-hw * 0.72, -hw * 0.24, hw * 0.24, hw * 0.72)):
            for i in range(3):
                bx0 = x0 + 0.03 + i * (L - 0.06) / 3
                blen = (L - 0.06) / 3 - 0.024
                mb = MB()
                # Inner cell stack + amber mica protective shell around each module
                mb.prism(rrect(blen, col_w * 0.88, 0.012, 3), [], zc0, zf + 0.006, (bx0 + blen / 2, yc, 0), mi=0)
                mb.prism(rrect(blen + 0.008, col_w * 0.94, 0.014, 3), [rrect(blen - 0.002, col_w * 0.84, 0.010, 3)], zc0, zf + 0.012, (bx0 + blen / 2, yc, 0), mi=2)
                for k in range(6):
                    xk = bx0 + 0.03 + k * (blen - 0.06) / 5
                    mb.box((xk, yc, zf + 0.009), 0.004, col_w * 0.86, 0.004, 1)
                    for s in (-1, 1):
                        mb.cyl((xk, yc + s * col_w * 0.32, zf + 0.006), (xk, yc + s * col_w * 0.32, zf + 0.016), 0.0045, seg=8, mi=2)
                bi += 1
                nm = "XR_Battery_Cells_%02d" % bi
                ob = solid(nm, mb, [M["XR_Cell"], M["XR_Cell_Top"], M["XR_Brass"], M["XR_Plastic_Black"], M["XR_Steel"]], coll, g, centre(mb), bevel=0.0,
                           sys="battery", id="cells", n=bi)
                out["cells"].append(ob)
                bus.box((bx0 + blen / 2, yc, zf + 0.017), blen - 0.02, 0.018, 0.0025, 0)
        bus.box((xc, 0.0, z0 + 0.112), L - 0.25, 0.036, 0.006, 0)
    else:
        # 6x2 CTP / module blocks (used by Qilin, Swap, Whale 800V, CIB, and standard blocks)
        slab_t, slab_pitch = 0.0145, 0.0185
        slab_len = hw - 0.018 - 0.009 - 0.02
        cell = MB()
        cell.prism(rrect(slab_t, slab_len, 0.0032, 2), [], zc0, zf, (0, 0, 0), mi=0)
        cell.prism(rrect(slab_t + 0.0004, slab_len * 0.97, 0.0032, 2), [], zf, zf + 0.010, (0, 0, 0), mi=1)
        for s in (1, -1):
            cell.cyl((0, s * slab_len * 0.36, zf + 0.010), (0, s * slab_len * 0.36, zf + 0.0165), 0.0042, seg=8, mi=2)
        cell.box((0, 0, zf + 0.0104), slab_t * 0.62, slab_len * 0.09, 0.0016, 3)
        for col in (1, -1):
            yc = col * (0.009 + 0.01 + slab_len / 2)
            for i in range(6):
                bx0 = x0 + 0.02 + i * pitch + 0.007 + 0.004
                inner = pitch - 0.014 - 0.008
                n_s = int(inner // slab_pitch)
                xs = bx0 + (inner - n_s * slab_pitch) / 2
                mb = MB()
                for j in range(n_s):
                    xj = xs + (j + 0.5) * slab_pitch
                    mb.append(cell, (xj, yc, 0))
                    if j < n_s - 1:
                        mb.box((xj + slab_pitch / 2, yc, (zc0 + zf) / 2), 0.0036, slab_len * 0.95, zf - zc0 - 0.006, 3)
                xa_, xb_ = xs + 0.0, xs + n_s * slab_pitch
                for sx_, xe in ((1, xb_), (-1, xa_)):
                    mb.box((xe + sx_ * 0.0025, yc, (zc0 + zf) / 2 + 0.003), 0.005, slab_len + 0.008, zf - zc0 + 0.012, 1)
                for s in (1, -1):
                    ys_ = yc + s * slab_len * 0.22
                    mb.box(((xa_ + xb_) / 2, ys_, zf + 0.0112), xb_ - xa_ + 0.012, 0.012, 0.0012, 4)
                bi += 1
                nm = "XR_Battery_Cells_%02d" % bi
                ob = solid(nm, mb, [M["XR_Cell"], M["XR_Cell_Top"], M["XR_Brass"], M["XR_Plastic_Black"], M["XR_Steel"]], coll, g, centre(mb), bevel=0.0,
                           sys="battery", id="cells", n=bi)
                out["cells"].append(ob)
                for s in (1, -1):
                    yb = yc + s * slab_len * 0.36
                    bus.box(((xa_ + xb_) / 2, yb, zf + 0.0174), xb_ - xa_ - 0.004, 0.0115, 0.0018, 0)
                    for j in range(1, n_s, 3):
                        bus.bolt((xs + (j + 0.5) * slab_pitch, yb, zf + 0.0183), Zv, 0.0036, 0.0028, 1, 1, False)
                    if i < 5:
                        bus.tube(D.round_path([(xb_ - 0.006, yb, zf + 0.0182), (xb_ + 0.002, yb, zf + 0.0235), (xb_ + 0.016, yb, zf + 0.0235),
                                               (xb_ + 0.024, yb, zf + 0.0182)], 0.004, 4), 0.0034, seg=8, mi=0)
        zb = z0 + 0.112
        if style in ("whale_800v", "swap"):
            # Twin heavy 800V / Swap orange-insulated central high-voltage busbar trunks
            for sy_ in (-0.022, 0.022):
                bus.box((xc, sy_, zb + 0.002), L - 0.24, 0.022, 0.008, 0)
        else:
            bus.box((xc, 0.0, zb), L - 0.4, 0.030, 0.006, 0)
        for i in range(0, 7):
            xi = x0 + 0.02 + i * pitch
            if x0 + 0.2 < xi < x1 - 0.2:
                bus.box((xi, 0.0, zb + 0.0045), 0.060, 0.044, 0.005, 2)
                for s in (-1, 1):
                    bus.bolt((xi, s * 0.012, zb + 0.007), Zv, 0.0048, 0.0042, 1, 1, True)

    out["bus"] = solid("XR_Battery_Busbars", bus, [M["XR_Copper"], M["XR_Steel"], M["XR_Plastic_Black"]], coll, g, centre(bus), bevel=0.0008, bevel_seg=1,
                       sys="battery", id="busbars")

    # ---- sensing flex circuits and BMS boards (`XR_Battery_Film`) — cutaway so cells shine through!
    mb = MB()
    zfc = z0 + 0.1165
    # Front BMS electronics bay shelf (covers only the front 22% of the pack so the rear 78% of cells are unobstructed)
    xf_bms = x1 - L * 0.22
    mb.prism(rrect(L * 0.20, W - 0.06, 0.03), [], zfc - 0.0012, zfc, ((xf_bms + x1) / 2 - 0.01, 0, 0), mi=0)
    # Flexible printed circuit (FPC) yellow sensing strips running longitudinally without blocking the cells
    for sy_ in (-hw * 0.52, 0.0, hw * 0.52):
        mb.box((xc, sy_, zfc + 0.0005), L - 0.12, 0.018, 0.0008, 1)
        for k in range(12):
            xk = x0 + 0.08 + k * (L - 0.16) / 11
            mb.box((xk, sy_, zfc + 0.0012), 0.008, 0.012, 0.0006, 4)
    # Three green BMS slave/master PCBs at the front edge
    for k, (bx, by) in enumerate(((x1 - 0.16, 0.30), (x1 - 0.16, -0.30), (x1 - 0.16, 0.0))):
        mb.box((bx, by, zfc + 0.0012), 0.15, 0.11, 0.0018, 2)
        for q_ in range(5):
            mb.box((bx - 0.045 + q_ * 0.022, by + 0.02, zfc + 0.003), 0.013, 0.013, 0.0024, 3)
        mb.box((bx + 0.045, by - 0.03, zfc + 0.0035), 0.028, 0.02, 0.0045, 3)
    out["film"] = solid("XR_Battery_Film", mb, [M["XR_Insulator"], M["XR_FPC"], M["XR_PCB"], M["XR_Plastic_Black"], M["XR_Brass"]], coll, g, centre(mb),
                        sys="battery", id="film")

    # ---- structural lid / top cover (`XR_Battery_Lid`) — architectural cutaway with OEM-specific top structures!
    zl = z0 + 0.125
    zt = zl + 0.0045
    mb = MB()
    # Perimeter bolted flange ring around the entire pack + front cutaway hood (covers front 24% of pack, leaving 76% open window)
    mb.prism(rrect(L + 0.088, W + 0.088, 0.095), [rrect(L - 0.04, W - 0.04, 0.05)], zl - 0.012, zt, (xc, 0, 0), mi=0)
    hood_L = L * 0.24
    xh_c = x1 - hood_L / 2 - 0.01
    mb.prism(rrect(hood_L, W - 0.02, 0.04), [], zl, zt, (xh_c, 0, 0), mi=0)
    zr = zt + 0.0025

    if style == "blade":
        # BYD CTB (Cell-to-Body) Structural Floor Cover: 3 heavy transverse aluminum-honeycomb seat crossbeams bridging sill-to-sill
        for frac in (0.26, 0.52, 0.74):
            xb_ = x0 + L * frac
            mb.box((xb_, 0, zr + 0.012), 0.068, W + 0.06, 0.028, 4)
            mb.box((xb_, 0, zr + 0.027), 0.088, W + 0.04, 0.004, 4)
            for k in range(8):
                yk = -hw + 0.10 + k * (W - 0.20) / 7
                mb.bolt((xb_, yk, zr + 0.029), Zv, 0.0065, 0.0055, 1, 1, True)
    elif style == "cib":
        # XPeng G9L CIB: 4 wide structural cross-straps and a central tunnel spine
        mb.box((xc, 0, zr + 0.008), L - 0.06, 0.075, 0.018, 4)
        for frac in (0.22, 0.45, 0.68):
            xb_ = x0 + L * frac
            mb.box((xb_, 0, zr + 0.009), 0.052, W + 0.02, 0.020, 4)
    elif style == "whale_800v":
        # Huawei Giant Whale 800V: high-voltage orange central armor shield + transverse rib arches
        mb.box((xc, 0, zr + 0.006), L - 0.08, 0.055, 0.012, 5)
        for i in range(1, 5):
            mb.box((x0 + i * L / 5, 0, zr + 0.004), 0.024, W - 0.04, 0.009, 0)
    else:
        # Thin structural cross-ribs across the cutaway window
        for i in (1, 3):
            mb.box((x0 + 0.02 + i * pitch, 0, zr + 0.002), 0.022, W - 0.04, 0.007, 0)

    for (x, y, z) in flange:
        mb.bolt((x, y, zl + 0.0035), Zv, 0.0068, 0.0056, 1, 1, True)

    # Burst vent, breather valve, hazard strip and stickers on the front hood section
    vx, vy = xh_c, 0.0
    mb.lathe([(0.0, 0.0), (0.040, 0.0), (0.046, 0.003), (0.046, 0.007), (0.034, 0.008), (0.030, 0.011), (0.0, 0.0125)], (vx, vy, zt), Zv, 36, 4)
    D.bolt_ring(mb, (vx, vy, zt + 0.0008), Zv, 0.060, 6, 0.0045, 0.0038, 0.3, 1, 1)
    mb.box((x1 - 0.045, 0.0, zr + 0.0003), 0.036, 0.9, 0.0006, 5)
    D.sticker(mb, (x1 - 0.16, 0.48, zr + 0.0025), X, Y, 0.075, 0.075, "hv", 3)
    D.sticker(mb, (x1 - 0.16, -0.48, zr + 0.0025), X, Y, 0.075, 0.075, "hv", 3)
    D.sticker(mb, (x1 - 0.24, 0.25, zr + 0.0025), X, Y, 0.082, 0.082, "qr", 3)
    out["lid"] = solid("XR_Battery_Lid", mb, [M["XR_Sheet"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Alu_Machined"], M["XR_Hazard"]], coll, g,
                       centre(mb), bevel=0.0014, bevel_seg=1, sys="battery", id="lid")

    # ---- high-voltage junction box / BDU (`XR_Battery_PDU`)
    mb = MB()
    px = x1 + 0.155
    pz = z0 + 0.065
    mb.box((px, 0, pz), 0.31, 0.42, 0.11, 3)
    mb.box((px, 0, pz + 0.0585), 0.318, 0.428, 0.007, 3)
    D.bolt_line(mb, (px - 0.135, -0.185, pz + 0.062), (px + 0.135, -0.185, pz + 0.062), 6, Zv, 0.0058, 0.005, 4, 4)
    D.bolt_line(mb, (px - 0.135, 0.185, pz + 0.062), (px + 0.135, 0.185, pz + 0.062), 6, Zv, 0.0058, 0.005, 4, 4)
    for k in range(11):
        mb.box((px - 0.01, -0.155 + k * 0.031, pz + 0.0725), 0.22, 0.0042, 0.016, 1)
    mb.box((px - 0.01, 0.0, pz + 0.0615), 0.23, 0.33, 0.003, 0)
    for s in (1, -1):
        mb.box((px + 0.02, s * 0.235, pz - 0.035), 0.1, 0.05, 0.016, 3)
        mb.bolt((px + 0.02, s * 0.235, pz - 0.027), Zv, 0.0085, 0.007, 4, 4, True)
    nose = []
    for s in (1, -1):
        nose.append(D.hv_connector(mb, (px + 0.155, s * 0.09, pz), X, 2, 2, 1, 0, 1.0, Vector((0, 0, 1))))
    mb.box((px + 0.158, 0.16, pz - 0.012), 0.016, 0.05, 0.034, 0)
    mb.box((px + 0.168, 0.16, pz + 0.002), 0.008, 0.044, 0.006, 3)
    D.fitting(mb, (px + 0.155, -0.165, pz - 0.014), (px + 0.215, -0.165, pz - 0.014), 0.0095, 1, 1)
    D.sticker(mb, (px - 0.01, 0.0, pz + 0.0625 + 0.0003), X, Y, 0.06, 0.06, "hv", 5)
    out["pdu"] = solid("XR_Battery_PDU", mb, [M["XR_Plastic_Black"], M["XR_Alu_Machined"], M["XR_HV_Orange"], M["XR_Casing"], M["XR_Bolt"], M["XR_Label"]], coll, g, centre(mb),
                       bevel=0.0028, bevel_seg=1, sys="battery", id="pdu")

    # ---- rear HV port box (`XR_Battery_RearPort`)
    mb = MB()
    rx = x0 - 0.035
    rz = z0 + 0.065
    mb.box((rx, 0, rz), 0.07, 0.46, 0.09, 3)
    mb.box((rx - 0.0, 0, rz + 0.0475), 0.074, 0.464, 0.005, 3)
    D.bolt_line(mb, (rx, -0.20, rz + 0.050), (rx, 0.20, rz + 0.050), 6, Zv, 0.0048, 0.0042, 4, 4)
    rn = []
    for s in (1, -1):
        rn.append(D.hv_connector(mb, (rx - 0.035, s * 0.17, rz), Vector((-1, 0, 0)), 2, 2, 1, 0, 0.85, Vector((0, 0, 1))))
    out["rear_port"] = solid("XR_Battery_RearPort", mb, [M["XR_Plastic_Black"], M["XR_Alu_Machined"], M["XR_HV_Orange"], M["XR_Casing"], M["XR_Bolt"]], coll, g,
                             centre(mb), bevel=0.002, bevel_seg=1, sys="battery", id="rear_port")
    out["ports"] = {
        "pdu_l": tuple(nose[0]), "pdu_r": tuple(nose[1]),
        "rear_l": tuple(rn[0]), "rear_r": tuple(rn[1]),
    }
    return out
