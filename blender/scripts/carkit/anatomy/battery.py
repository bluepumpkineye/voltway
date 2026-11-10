"""The traction pack, built from the spec's pack box: tray with its gasket and bolted flange, cold plate with a rounded serpentine
channel, twelve blocks of individual cells (printed wrap, foam spacers, terminals, vents, end plates, straps), busbars, the
sensing flex circuits and BMS boards, a ribbed bolted lid with its labels, vent and valve, and the high-voltage junction boxes.

Layers from the floor up (heights above `p['z0']`): tray floor 0.012, cold plate 0.020 (channels to 0.0265), cells 0.022 to 0.094,
cell shoulders to 0.104, terminals to 0.1105, busbars to 0.1125, flex circuits 0.1155, lid 0.125 to 0.1295 (ribs to 0.1345).
The cells are thin standing slabs in two columns of six blocks, like a cell-to-body pack seen with the lid off: the shapes are
ours, the card says so.
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
    x0, x1, hw, z0 = p["x0"], p["x1"], p["hw"], p["z0"]
    L, W = x1 - x0, 2 * hw
    xc = (x0 + x1) / 2
    g = group("XR_Battery", coll, (xc, 0, z0), root, sys="battery", id="battery")
    out = {"group": g}
    corner = 0.07
    zw = z0 + 0.120                      # the tray wall's top
    flange = _flange_points(x0, x1, hw, zw)

    # ---- tray: floor, walls, a rolled flange with bolts, a rubber gasket bead, cross beams, body lugs, underside stiffeners
    mb = MB()
    mb.prism(rrect(L, W, corner), [], z0, z0 + 0.012, (xc, 0, 0), mi=0)
    mb.prism(rrect(L, W, corner), [rrect(L - 0.036, W - 0.036, corner - 0.012)], z0 + 0.012, zw, (xc, 0, 0), mi=0)
    mb.prism(rrect(L + 0.07, W + 0.07, 0.09), [rrect(L - 0.01, W - 0.01, corner)], zw - 0.008, zw, (xc, 0, 0), mi=0)
    mb.prism(rrect(L + 0.048, W + 0.048, 0.08), [rrect(L + 0.036, W + 0.036, 0.075)], zw, zw + 0.0032, (xc, 0, 0), mi=2)      # gasket bead
    pitch = (L - 0.04) / 6
    for i in range(1, 6):
        mb.box((x0 + 0.02 + i * pitch, 0, z0 + 0.0495), 0.014, W - 0.036, 0.075, 4)
        mb.box((x0 + 0.02 + i * pitch, 0, z0 + 0.088), 0.026, W - 0.2, 0.0035, 0)         # the beam's cap
    mb.box((xc, 0, z0 + 0.0495), L - 0.036, 0.018, 0.075, 4)
    for i in range(1, 6):
        for s in (-1, 1):
            mb.bolt((x0 + 0.02 + i * pitch, s * (W / 2 - 0.20), z0 + 0.0905), Zv, 0.0058, 0.005, 1, 1, True)
    for (x, y, z) in flange:
        mb.bolt((x, y, z), Zv, 0.0068, 0.0056, 1, 1, True)
    # body lugs: ears on the long sides with a bolt through each
    for i in range(4):
        x = x0 + 0.18 + (L - 0.36) * i / 3
        for s in (1, -1):
            mb.prism(rrect(0.07, 0.05, 0.02), [circle(0.012, 14)], zw - 0.016, zw - 0.006, (x, s * (hw + 0.058), 0), mi=0)
            mb.bolt((x, s * (hw + 0.058), zw - 0.006), Zv, 0.0085, 0.007, 1, 1, True)
    # the underside: stiffening strips and bolts
    for k in range(-3, 4):
        mb.box((xc, k * 0.17, z0 - 0.0035), L - 0.12, 0.022, 0.007, 4)
    for i in range(7):
        for k in (-2, 0, 2):
            mb.bolt((x0 + 0.02 + i * pitch, k * 0.17 + 0.085, z0 - 0.007), (0, 0, -1), 0.006, 0.005, 1, 1, True)
    D.sticker(mb, (x1 - 0.30, hw, z0 + 0.062), Vector((-1, 0, 0)), Z, 0.07, 0.045, "plate", 3)         # a data plate on the tray's left wall
    out["tray"] = solid("XR_Battery_Tray", mb, [M["XR_Sheet"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Alu_Cast"]], coll, g, centre(mb),
                        bevel=0.0018, bevel_seg=1, sys="battery", id="tray")

    # ---- cold plate: a flat plate, a rounded serpentine channel wall, coolant manifold with barbed fittings
    mb = MB()
    mb.prism(rrect(L - 0.04, W - 0.04, 0.05), [], z0 + 0.012, z0 + 0.020, (xc, 0, 0), mi=0)
    zr = z0 + 0.0235
    xa, xb = x0 + 0.12, x1 - 0.12
    heads = []
    for s in (1, -1):
        ys = [s * (0.07 + k * 0.115) for k in range(6)]
        path = []
        for k, y in enumerate(ys):
            path += [(xa, y, zr), (xb, y, zr)] if k % 2 == 0 else [(xb, y, zr), (xa, y, zr)]
        pts = D.round_path(path, 0.05, 6)
        mb.sweep(pts, D.flat_prof(0.0065, 0.018), mi=0, up=Zv)
        heads.append((s, ys, path))
        # inlet / outlet: a pipe out through the front edge with a barbed fitting and a clamped stub of hose
        yy = ys[0]
        mb.tube(D.round_path([(x1 - 0.12, yy, zr), (x1 - 0.06, yy, zr), (x1 + 0.02, yy, zr)], 0.03, 5), 0.0105, seg=14, mi=2)
        D.fitting(mb, (x1 - 0.005, yy, zr), (x1 + 0.062, yy, zr), 0.0108, 1, 2)
        D.clamp(mb, (x1 + 0.052, yy, zr), X, 0.0112, 2, 2)
    # a bolted cross plate between the two serpentines
    for k in range(6):
        for s in (1, -1):
            mb.bolt((x0 + 0.06 + k * (L - 0.12) / 5, s * 0.0, z0 + 0.020), Zv, 0.0045, 0.004, 2, 2, False)
    out["plate"] = solid("XR_Battery_Plate", mb, [M["XR_Alu_Cast"], M["XR_Coolant"], M["XR_Alu_Machined"]], coll, g, centre(mb), bevel=0.001, bevel_seg=1,
                         sys="battery", id="plate")

    # ---- cell blocks: six along the car, two across, slabs standing on the plate
    slab_t, slab_pitch = 0.0145, 0.0185
    zc0 = z0 + 0.022
    zf = z0 + 0.094
    slab_len = hw - 0.018 - 0.009 - 0.02
    # one cell, built once at the origin: a wrapped can with rounded corners, an aluminium shoulder, two terminals and a vent
    cell = MB()
    cell.prism(rrect(slab_t, slab_len, 0.0032, 2), [], zc0, zf, (0, 0, 0), mi=0)
    cell.prism(rrect(slab_t + 0.0004, slab_len * 0.97, 0.0032, 2), [], zf, zf + 0.010, (0, 0, 0), mi=1)
    for s in (1, -1):
        cell.cyl((0, s * slab_len * 0.36, zf + 0.010), (0, s * slab_len * 0.36, zf + 0.0165), 0.0042, seg=8, mi=2)
    cell.box((0, 0, zf + 0.0104), slab_t * 0.62, slab_len * 0.09, 0.0016, 3)
    out["cells"] = []
    bi = 0
    bus = MB()
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
                    mb.box((xj + slab_pitch / 2, yc, (zc0 + zf) / 2), 0.0036, slab_len * 0.95, zf - zc0 - 0.006, 3)       # foam between cells
            xa_, xb_ = xs + 0.0, xs + n_s * slab_pitch
            for sx_, xe in ((1, xb_), (-1, xa_)):                      # end plates
                mb.box((xe + sx_ * 0.0025, yc, (zc0 + zf) / 2 + 0.003), 0.005, slab_len + 0.008, zf - zc0 + 0.012, 1)
            for s in (1, -1):                                           # steel straps over the tops, down the end plates
                ys_ = yc + s * slab_len * 0.22
                mb.box(((xa_ + xb_) / 2, ys_, zf + 0.0112), xb_ - xa_ + 0.012, 0.012, 0.0012, 4)
                for xe in (xa_ - 0.0058, xb_ + 0.0058):
                    mb.box((xe, ys_, zf + 0.0006 - 0.0), 0.0012, 0.012, 0.0215, 4)
            bi += 1
            nm = "XR_Battery_Cells_%02d" % bi
            ob = solid(nm, mb, [M["XR_Cell"], M["XR_Cell_Top"], M["XR_Brass"], M["XR_Plastic_Black"], M["XR_Steel"]], coll, g, centre(mb), bevel=0.0,
                       sys="battery", id="cells", n=bi)
            out["cells"].append(ob)
            # busbars over each block's two terminal rows, with a nut every third cell, and a braid to the next block
            for s in (1, -1):
                yb = yc + s * slab_len * 0.36
                bus.box(((xa_ + xb_) / 2, yb, zf + 0.0165 + 0.0009), xb_ - xa_ - 0.004, 0.0115, 0.0018, 0)
                for j in range(1, n_s, 3):
                    bus.bolt((xs + (j + 0.5) * slab_pitch, yb, zf + 0.0165 + 0.0018), Zv, 0.0036, 0.0028, 1, 1, False)
                if i < 5:
                    bus.tube(D.round_path([(xb_ - 0.006, yb, zf + 0.0182), (xb_ + 0.002, yb, zf + 0.0235), (xb_ + 0.016, yb, zf + 0.0235),
                                           (xb_ + 0.024, yb, zf + 0.0182)], 0.004, 4), 0.0034, seg=8, mi=0)
    # the main bar along the centre beam, in an insulating shroud with bolts at each cross beam
    zb = z0 + 0.112
    bus.box((xc, 0.0, zb), L - 0.4, 0.030, 0.006, 0)
    for i in range(0, 7):
        xi = x0 + 0.02 + i * pitch
        if x0 + 0.2 < xi < x1 - 0.2:
            bus.box((xi, 0.0, zb + 0.0045), 0.060, 0.044, 0.005, 2)
            for s in (-1, 1):
                bus.bolt((xi, s * 0.012, zb + 0.007), Zv, 0.0048, 0.0042, 1, 1, True)
    out["bus"] = solid("XR_Battery_Busbars", bus, [M["XR_Copper"], M["XR_Steel"], M["XR_Plastic_Black"]], coll, g, centre(bus), bevel=0.0008, bevel_seg=1,
                       sys="battery", id="busbars")

    # ---- insulation film, the sensing flex circuits and the BMS boards
    mb = MB()
    mb.prism(rrect(L - 0.03, W - 0.03, 0.05), [], z0 + 0.1160, z0 + 0.1176, (xc, 0, 0), mi=0)
    zfc = z0 + 0.1176
    for col in (1, -1):
        yc = col * (0.009 + 0.01 + slab_len / 2)
        for i in range(6):
            bx0 = x0 + 0.02 + i * pitch + 0.011
            ln = pitch - 0.036
            mb.box((bx0 + ln / 2 + 0.01, yc + 0.0, zfc + 0.0004), ln, 0.016, 0.0008, 1)               # a flex strip along the block, between the terminal rows
            for k in range(7):
                mb.box((bx0 + 0.02 + k * (ln - 0.03) / 6, yc, zfc + 0.0011), 0.007, 0.011, 0.0006, 4)    # solder pads
            mb.box((bx0 + 0.011, yc + col * slab_len * 0.18, zfc + 0.0020), 0.012, 0.016, 0.0036, 3)     # its connector
    # the trunk and the BMS boards at the front end
    mb.box((xc + 0.4, 0.0, zfc + 0.0004), L * 0.5, 0.020, 0.0008, 1)
    for k, (bx, by) in enumerate(((x1 - 0.20, 0.30), (x1 - 0.20, -0.30), (x1 - 0.55, 0.0))):
        mb.box((bx, by, zfc + 0.0009), 0.17, 0.11, 0.0016, 2)
        for q_ in range(5):
            mb.box((bx - 0.05 + q_ * 0.025, by + 0.02, zfc + 0.0028), 0.014, 0.014, 0.0024, 3)             # chips
        mb.box((bx + 0.05, by - 0.03, zfc + 0.0035), 0.03, 0.02, 0.0045, 3)                                # a connector
        for bx_, by_ in ((bx - 0.075, by - 0.045), (bx + 0.075, by - 0.045), (bx - 0.075, by + 0.045), (bx + 0.075, by + 0.045)):
            mb.bolt((bx_, by_, zfc + 0.0017), Zv, 0.0033, 0.0028, 4, 4, False)
    out["film"] = solid("XR_Battery_Film", mb, [M["XR_Insulator"], M["XR_FPC"], M["XR_PCB"], M["XR_Plastic_Black"], M["XR_Brass"]], coll, g, centre(mb),
                        sys="battery", id="film")

    # ---- lid: a stamped plate with ribs, a rolled edge, flange bolts, a burst vent, a breather valve, labels
    zl = z0 + 0.125
    zt = zl + 0.0045
    mb = MB()
    mb.prism(rrect(L - 0.01, W - 0.01, 0.06), [], zl, zt, (xc, 0, 0), mi=0)
    mb.prism(rrect(L + 0.088, W + 0.088, 0.095), [rrect(L + 0.06, W + 0.06, 0.082)], zl - 0.014, zl + 0.0035, (xc, 0, 0), mi=0)      # the rolled edge over the tray flange
    mb.prism(rrect(L + 0.088, W + 0.088, 0.095), [rrect(L - 0.01, W - 0.01, 0.06)], zl, zl + 0.0035, (xc, 0, 0), mi=0)
    zr = zt + 0.0025
    for y in (-0.5, -0.25, 0.0, 0.25, 0.5):
        if abs(y) < hw - 0.1:
            mb.box((xc, y, zr), L - 0.2, 0.014, 0.005, 0)
    for i in range(0, 7):
        mb.box((x0 + 0.02 + i * pitch, 0, zr), 0.014, W - 0.2, 0.005, 0)
    for (x, y, z) in flange:
        mb.bolt((x, y, zl + 0.0035), Zv, 0.0068, 0.0056, 1, 1, True)
    # the burst vent (a domed disc in a ring) and a breather valve with a mesh cap
    vx, vy = x0 + 0.30, 0.0
    mb.lathe([(0.0, 0.0), (0.040, 0.0), (0.046, 0.003), (0.046, 0.007), (0.034, 0.008), (0.030, 0.011), (0.0, 0.0125)], (vx, vy, zt), Zv, 36, 4)
    mb.torus((vx, vy, zt + 0.0075), Zv, 0.040, 0.0028, 28, 6, 4)
    D.bolt_ring(mb, (vx, vy, zt + 0.0008), Zv, 0.060, 6, 0.0045, 0.0038, 0.3, 1, 1)
    bx_, by_ = x1 - 0.30, 0.42
    mb.cyl((bx_, by_, zt), (bx_, by_, zt + 0.013), 0.017, seg=18, mi=1)
    mb.cyl((bx_, by_, zt + 0.013), (bx_, by_, zt + 0.019), 0.012, seg=18, mi=2)
    mb.torus((bx_, by_, zt + 0.0132), Zv, 0.0175, 0.0024, 18, 5, 2)
    # a hazard strip along the front edge, and the stickers
    mb.box((x1 - 0.045, 0.0, zr + 0.0003), 0.036, 0.9, 0.0006, 5)
    D.sticker(mb, (x1 - 0.20, 0.55, zr + 0.0025), X, Y, 0.075, 0.075, "hv", 3)
    D.sticker(mb, (x1 - 0.20, -0.55, zr + 0.0025), X, Y, 0.075, 0.075, "hv", 3)
    D.sticker(mb, (xc + 0.30, 0.38, zr + 0.0025), X, Y, 0.082, 0.082, "qr", 3)
    D.sticker(mb, (xc + 0.30, -0.38, zr + 0.0025), X, Y, 0.10, 0.10, "plate", 3)
    D.sticker(mb, (x0 + 0.55, 0.55, zr + 0.0025), X, Y, 0.09, 0.045, "bar", 3)
    D.sticker(mb, (x0 + 0.55, -0.55, zr + 0.0025), X, Y, 0.06, 0.06, "earth", 3)
    out["lid"] = solid("XR_Battery_Lid", mb, [M["XR_Sheet"], M["XR_Bolt"], M["XR_Rubber"], M["XR_Label"], M["XR_Alu_Machined"], M["XR_Hazard"]], coll, g,
                       centre(mb), bevel=0.0014, bevel_seg=1, sys="battery", id="lid")

    # ---- the junction box on the front edge: finned, bolted, two HV connectors, a signal connector and a coolant fitting
    mb = MB()
    px = x1 + 0.155
    pz = z0 + 0.065
    mb.box((px, 0, pz), 0.31, 0.42, 0.11, 3)
    mb.box((px, 0, pz + 0.0585), 0.318, 0.428, 0.007, 3)                                              # the cover's flange
    D.bolt_line(mb, (px - 0.135, -0.185, pz + 0.062), (px + 0.135, -0.185, pz + 0.062), 6, Zv, 0.0058, 0.005, 4, 4)
    D.bolt_line(mb, (px - 0.135, 0.185, pz + 0.062), (px + 0.135, 0.185, pz + 0.062), 6, Zv, 0.0058, 0.005, 4, 4)
    for k in range(11):
        mb.box((px - 0.01, -0.155 + k * 0.031, pz + 0.0725), 0.22, 0.0042, 0.016, 1)               # cooling fins
    mb.box((px - 0.01, 0.0, pz + 0.0615), 0.23, 0.33, 0.003, 0)                                        # the fins' base
    for s in (1, -1):                                                                                   # body ears
        mb.box((px + 0.02, s * 0.235, pz - 0.035), 0.1, 0.05, 0.016, 3)
        mb.bolt((px + 0.02, s * 0.235, pz - 0.027), Zv, 0.0085, 0.007, 4, 4, True)
    nose = []
    for s in (1, -1):
        nose.append(D.hv_connector(mb, (px + 0.155, s * 0.09, pz), X, 2, 2, 1, 0, 1.0, Vector((0, 0, 1))))
    # a signal connector (a black block with a latch), and a coolant stub
    mb.box((px + 0.158, 0.16, pz - 0.012), 0.016, 0.05, 0.034, 0)
    mb.box((px + 0.168, 0.16, pz + 0.002), 0.008, 0.044, 0.006, 3)
    D.fitting(mb, (px + 0.155, -0.165, pz - 0.014), (px + 0.215, -0.165, pz - 0.014), 0.0095, 1, 1)
    D.sticker(mb, (px - 0.01, 0.0, pz + 0.0625 + 0.0003), X, Y, 0.06, 0.06, "hv", 5)
    out["pdu"] = solid("XR_Battery_PDU", mb, [M["XR_Plastic_Black"], M["XR_Alu_Machined"], M["XR_HV_Orange"], M["XR_Casing"], M["XR_Bolt"], M["XR_Label"]], coll, g, centre(mb),
                       bevel=0.0028, bevel_seg=1, sys="battery", id="pdu")

    # ---- the rear connector box, where the harness leaves for the rear drive units
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
