"""BYD Seal 07 EV cabin shell: headliner around the panoramic glass roof, pillar trims,
floor and sills with "BYD" scuff plates, kick panels, rear wheelhouses, parcel shelf,
bulkhead, pedals, and roof fittings.
"""
import math
import bpy
from mathutils import Vector

import seal_surface as S
import seal_panels as PN
import seal_interior as ZI
import seal_interior_doors as DR
import seal_gate as GT
import cabin_parts as CP
from seal_interior import FLOOR_Z, MIRROR_C, z_glass
from cabin_parts import smooth as _smooth
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path

# ---------------------------------------------------------------- the shell
X_OPEN_F, X_OPEN_R = 0.020, -1.050
Y_OPEN = 0.400
X_HEADLINER_R = -1.780
X_A_FOOT = 0.815


def glass_top(x):
    return PN.V_GLASS_TOP(max(x, PN.X_QTR_R))


def v_head_edge(x):
    return S.v_along(x, glass_top(x), 0.058)


def _head_rows(x0, x1, nx, v_in, v_out=v_head_edge, inset=0.042, nv=22):
    rows = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / float(nx)
        a, b = v_out(x), v_in(x)
        row = [S.surface_offset(x, a + (b - a) * j / float(nv), -inset) for j in range(nv + 1)]
        rows.append(row)
    return rows


def build_headliner(col, lib):
    made = []
    centre = lambda x: 0.9995
    open_v = lambda x: S.v_at_y_upper(x, Y_OPEN)
    bands = (("int_headliner_F", PN.X_ROOF_F + 0.030, X_OPEN_F, 16),
             ("int_headliner_R", X_OPEN_R, X_HEADLINER_R, 60))
    for name, x0, x1, nx in bands:
        rows = _head_rows(x0, x1, nx, centre)
        for r in rows:
            r[-1] = (r[-1][0], 0.0, r[-1][2])
        ob = grid_mesh(name, rows, col, lib["headliner"])
        M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
        M.mirror_y(ob)
        made.append(ob)

    rows = _head_rows(X_OPEN_F + 0.002, X_OPEN_R - 0.002, 40, open_v, nv=10)
    ob = grid_mesh("int_headliner_side", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
    M.mirror_y(ob)
    made.append(ob)

    loop = []
    for k in range(40):
        x = X_OPEN_F + (X_OPEN_R - X_OPEN_F) * k / 39.0
        loop.append((x, open_v(x)))
    rows = [[S.surface_offset(x, v, -0.042), S.surface_offset(x, v, -0.004)] for (x, v) in loop]
    rv = grid_mesh("int_headliner_reveal", rows, col, lib["headliner"])
    M.orient(rv.data, lambda c: (0.0, -1.0 if c[1] > 0 else 1.0, 0.0))
    M.mirror_y(rv)
    made.append(rv)

    for x, nm in ((X_OPEN_F, "F"), (X_OPEN_R, "R")):
        rows = []
        v0 = open_v(x)
        for j in range(13):
            v = v0 + (0.9995 - v0) * j / 12.0
            rows.append([S.surface_offset(x, v, -0.042), S.surface_offset(x, v, -0.004)])
        rows[-1] = [(p[0], 0.0, p[2]) for p in rows[-1]]
        ev = grid_mesh("int_headliner_reveal" + nm, rows, col, lib["headliner"])
        M.orient(ev.data, lambda c, s=(-1.0 if nm == "F" else 1.0): (s, 0.0, 0.0))
        M.mirror_y(ev)
        made.append(ev)
    return made


def _a_door(x):
    return (x, S.v_along(x, min(PN.V_A(x) - 0.020, PN.V_GT(x)), -0.020))


def _a_screen(x):
    return (x, S.v_along(x, PN.V_A(x) + 0.020, 0.018))


def build_shell(col, lib):
    made = build_headliner(col, lib)
    xs = [X_A_FOOT - (X_A_FOOT - (PN.X_ROOF_F - 0.03)) * k / 48.0 for k in range(49)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs, _a_door, _a_screen, depth=0.016,
                             bulge=0.024, name="int_apillar"))

    for side in (1.0, -1.0):
        x = 0.850
        a = Vector(S.BODY.surface(*_a_door(x)))
        b = Vector(S.BODY.surface(*_a_screen(x)))
        n = (Vector(S.BODY.surface_normal(*_a_door(x))) + Vector(S.BODY.surface_normal(*_a_screen(x)))).normalized()
        c = a.lerp(b, 0.5) - n * (0.016 + 0.024 + 0.002)
        c.y *= side
        nn = Vector((-n.x, -n.y * side, -n.z))
        made += F.disc(col, "int_apillar_tweeter%s" % ("L" if side > 0 else "R"), tuple(c),
                       tuple(nn), 0.024, lib["speaker"], dome=0.002, rim=0.0018,
                       rim_mat=lib["chrome"])

    xs = [PN.X_ROOF_F + 0.04 - (PN.X_ROOF_F + 0.04 - PN.X_QTR_R) * k / 44.0 for k in range(45)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, glass_top(x), -0.012)),
        lambda x: (x, S.v_along(x, glass_top(x), 0.082)),
        depth=0.014, bulge=0.016, name="int_roofrail"))

    vb0 = PN.V_BELT - 0.006
    vb1 = PN.V_GT(-0.20) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(
        S.BODY, col, lib["leather_door"], vs,
        lambda v: (PN.GB_F(v) + 0.012, v), lambda v: (PN.GB_R(v) - 0.012, v),
        depth=0.016, bulge=0.012, name="int_bpillar"))

    xs = [PN.X_QTR_R + 0.040 - (PN.X_QTR_R + 0.040 - X_HEADLINER_R) * k / 24.0 for k in range(25)]

    def c_lo(x):
        z = max(0.95, min(DR._belt_z(x) - 0.06, 1.10))
        return S.v_at_z(x, z, 0.30, 0.99)

    def c_hi(x):
        a = v_head_edge(max(x, X_HEADLINER_R)) + 0.010
        if x >= PN.X_ROOF_R:
            return a
        b = PN.V_REARGLASS + 0.012
        t = _smooth((PN.X_ROOF_R - x) / 0.05)
        return a + (b - a) * t

    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.035,
                               bulge=0.016, nt=16, name="int_cpillar", overlap=0.010))

    x0 = xs[0]
    a, b = S.v_along(x0, c_lo(x0), -0.010), S.v_along(x0, c_hi(x0), 0.010)
    rows = []
    for j in range(17):
        t = j / 16.0
        v = a + (b - a) * t
        d = 0.035 + 0.016 * math.sin(math.pi * t) ** 0.7
        rows.append([S.surface_offset(x0, v, -d), S.surface_offset(x0, v, -0.004)])
    fl = grid_mesh("int_cpillar_flange", rows, col, lib["headliner"])
    M.orient(fl.data, lambda c: (1.0, 0.0, 0.0))
    M.mirror_y(fl)
    made.append(fl)

    xs = [PN.X_QTR_F + 0.060 - (PN.X_QTR_F + 0.060 - (PN.X_QTR_R - 0.020)) * k / 10.0 for k in range(11)]
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs,
                               lambda x: S.v_at_z(x, 0.975, 0.30, 0.99),
                               lambda x: max(PN.V_BELT, PN.V_QTR_LOW(x)) + 0.012, inset=0.018, bulge=0.004, nt=16,
                               name="int_qtr_lower", overlap=0.008))
    made += build_roof_fittings(col, lib)

    made.append(CB.floor(col, lib["carpet"], -1.48, 0.90, 1.10, FLOOR_Z, 0.54,
                         lambda x: 0.68 + 0.06 * _smooth((x - 0.78) / 0.05), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.18, 0.92, 0.68, 0.82, FLOOR_Z, 0.330, name="int_sill"))
    made += build_sill_plates(col, lib)
    return made


# --------------------------------------------------------------- sill plates
def build_sill_plates(col, lib):
    """Brushed stainless steel scuff plate on each doorway's sill reading 'BYD'."""
    from mathutils import Matrix
    made = []
    z0 = 0.3305
    ink = bpy.data.materials.get("INT_Trim_Dark") or lib["satin"]
    inter = ZI._font("Inter.woff2")
    for tag, (x0, x1) in (("F", (-0.020, 0.800)), ("R", (-1.100, -0.320))):
        for side, st in ((1.0, "L"), (-1.0, "R")):
            y0, y1 = 0.700, 0.780
            made.append(F.box(col, "int_sillplate_%s%s" % (tag, st),
                              (0.5 * (x0 + x1), side * 0.5 * (y0 + y1), z0 + 0.0016),
                              (x1 - x0, y1 - y0, 0.0032), lib["brushed"], r=0.0012))
            txt = M.text_mesh("int_sillplate_%s%s_text" % (tag, st), "BYD", 0.026, col, ink,
                              extrude=0.0004, font=inter, resolution=3)
            xc = 0.5 * (x0 + x1)
            rot = Matrix.Rotation(math.pi if side > 0 else 0.0, 4, 'Z')
            txt.matrix_world = Matrix.Translation((xc + (0.040 if side > 0 else -0.040),
                                                   side * 0.5 * (y0 + y1), z0 + 0.0036)) @ rot
            made.append(txt)
    return made


# ------------------------------------------------------------ closing trims
def build_closures(col, lib):
    made = []
    vh = DR._v_top_front() + 0.10
    xb = DR.X_B
    xs = [xb - 0.030 + 0.060 * k / 6.0 for k in range(7)]
    rows = []
    for x in xs:
        rows.append([(x, CB.skin_offset_y(S.BODY, x, z, 0.030, vh), z)
                     for z in [0.40 + (DR._belt_z(x) - 0.40) * k / 12.0 for k in range(13)]])
    seal = grid_mesh("int_bpillar_seal", rows, col, lib["satin"])
    M.orient(seal.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(seal)
    made.append(seal)

    yk = 0.705
    x_open = DR._door_f_edge(0.60) - 0.040
    kick_y = Curve([(x_open, yk), (x_open + 0.030, 0.630), (1.08, 0.630)], mode="pchip")
    made.append(CB.wall(col, lib["leather_door"],
                        [(x_open + (1.08 - x_open) * k / 16.0, kick_y(x_open + (1.08 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.820, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["leather_door"],
                        [(x_open, yk + (0.755 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.820,
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))

    rc = DR.rear_card(1.0)
    vq = max(PN.V_BELT, PN.V_BELT) + 0.10
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_door"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.75,
        FLOOR_Z + 0.02, 0.660, 0.950, 1.150, 0.060, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)
    made += build_rear_closure(col, lib)
    return made


def build_rear_closure(col, lib):
    made = []
    xb = -1.280
    made.append(CB.bulkhead(col, lib["carpet"], [(xb, FLOOR_Z + 0.02), (xb, 0.96)],
                            lambda x, z: 0.68, n=14, name="int_bulkhead", facing=(1.0, 0.0, 0.0)))

    def shelf_z(x):
        # up to the backlight's foot (x -2.0, z 1.086 on this body: the glass runs down to the boot lid)
        return 0.975 + 0.100 * _smooth((-1.45 - x) / 0.55)
    xs = [xb + (-1.99 - xb) * k / 30.0 for k in range(31)]
    rows = []
    for x in xs:
        hw = min(0.74, S.section_v(x, S.v_at_z(x, shelf_z(x), 0.30, 0.99))[0] - 0.040)
        rows.append([(x, hw * j / 12.0, shelf_z(x)) for j in range(13)])
    ob = grid_mesh("int_parcel_shelf", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(ob)
    made.append(ob)

    def half(x, z, depth=0.060):
        return min(0.70, CB.skin_offset_y(S.BODY, max(x, -2.20), z, depth + 0.012, 0.99))
    made += GT.build_boot(col, lib, half)
    return made


# ------------------------------------------------------------------ pedals
def build_pedals(col, lib):
    return CP.pedals(col, lib, FLOOR_Z, [("rest", 0.560, 0.920, 0.435, 0.078, 0.195, 5),
                                         ("brake", 0.355, 0.890, 0.480, 0.095, 0.125, 3),
                                         ("accel", 0.225, 0.920, 0.438, 0.048, 0.200, 0)])


# ------------------------------------------------------------ roof fittings
def build_roof_fittings(col, lib):
    made = []
    zg = z_glass(MIRROR_C[0] + 0.07, 0.0) - 0.006
    made += CP.rear_view_mirror(col, lib, MIRROR_C, zg)

    xs = [0.200 - 0.140 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.044
        rows.append([(x, 0.110 * (1 - 2 * j / 10.0), zr - 0.014 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["piano"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)

    for side in (1.0, -1.0):
        rows = []
        for i in range(9):
            x = PN.X_ROOF_F + 0.04 - 0.18 * i / 8.0
            zr = S.surface_offset(x, S.v_at_y_upper(x, 0.33), -0.044)[2]
            rows.append([(x, side * (0.140 + 0.36 * j / 8.0),
                          zr - 0.002 * math.sin(math.pi * j / 8) - 0.020 * (j / 8.0) ** 2)
                         for j in range(9)])
        vz = grid_mesh("int_visor_%s" % ("L" if side > 0 else "R"), rows, col, lib["headliner"])
        M.orient(vz.data, lambda c: (0.0, 0.0, -1.0))
        M.solidify(vz, 0.014, 1.0)
        M.bevel(vz, 0.005, 2, 40)
        made.append(vz)

    for side in (1.0, -1.0):
        x = 0.180
        v = S.v_at_y_upper(x, 0.46)
        p = Vector(S.surface_offset(x, v, -0.0450))
        nrm = -Vector(S.surface_normal(x, v))
        made += F.disc(col, "int_head_speaker%s" % ("L" if side > 0 else "R"),
                       (p.x, side * p.y, p.z), (nrm.x, side * nrm.y, nrm.z), 0.028,
                       lib["speaker"], rim=0.0022, rim_mat=lib["chrome"])
    return made


# ---------------------------------------------------------------- lighting
def cabin_lights(col):
    return F.lights(col, [
        ("int_L_Roof", (-0.28, 0.0, 1.40), (-0.28, 0.0, 0.40), (1.5, 1.15), 10.0,
         (0.90, 0.94, 1.00), True),
        ("int_L_Back", (-1.05, 0.0, 1.20), (0.55, 0.0, 0.80), (1.2, 0.48), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.40, 1.15), (0.0, 0.0, 0.75), (2.0, 0.55), 2.5,
         (0.85, 0.90, 1.00), True),
        ("int_L_Right", (0.0, -1.40, 1.15), (0.0, 0.0, 0.75), (2.0, 0.55), 2.5,
         (0.85, 0.90, 1.00), True),
    ])


def main(lights=True, parts=None):
    from carkit import build as B
    from carkit.jev.triage import guard
    col = B.fresh_collection(ZI.COLLECTION)
    lib = ZI.build_library()
    builders = (("dash", lambda: ZI.build_dash(col, lib)),
                ("screens", lambda: ZI.build_screens(col, lib)),
                ("wheel", lambda: ZI.build_wheel(col, lib)),
                ("seats", lambda: ZI.build_seats(col, lib)),
                ("console", lambda: ZI.build_console(col, lib)),
                ("doors", lambda: DR.build_doors(col, lib)),
                ("shell", lambda: build_shell(col, lib)),
                ("closures", lambda: build_closures(col, lib)),
                ("gate", lambda: GT.build_liner(col)),
                ("pedals", lambda: build_pedals(col, lib)))
    for name, fn in builders:
        if parts and name not in parts:
            continue
        with guard("building the cabin's " + name):
            fn()
    if lights:
        cabin_lights(col)
    B.ensure_uvs([col], force=tuple(m.name for m in bpy.data.materials
                                    if m.name.startswith("INT_") and m.name != "INT_Screen"))
    n = len([o for o in col.objects if o.type == 'MESH'])
    print("interior: %d meshes, %d tris" % (n, M.tri_count([o for o in col.objects
                                                           if o.type == 'MESH'])))
    return col
