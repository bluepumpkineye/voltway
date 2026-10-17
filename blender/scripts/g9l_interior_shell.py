"""XPeng G9L cabin: what closes it - the headliner round the panoramic glass, the pillar trims, the
floor and sills, the kick panels, the rear wheelhouses, the cargo bay with its floor, walls and rear
wall - plus the pedals, the roof fittings and the render rig; `main()` builds the whole cabin.

Every enclosing surface is an offset of the exterior loft (carkit.interior.cabin), so the inside
always agrees with the outside. cabin_tools.leaks finds what is still missing.
"""
import math

import bpy
from mathutils import Vector

import g9l_surface as S
import g9l_panels as PN
import g9l_interior as ZI
import g9l_interior_doors as DR
import g9l_gate as GT
import cabin_parts as CP
from g9l_interior import FLOOR_Z, MIRROR_C, z_glass
from cabin_parts import smooth as _smooth
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path

# ---------------------------------------------------------------- the shell
# The panoramic glass (G9L_Glass_Roof, x -0.344 .. 0.50) shows through an opening in the headliner:
# a black suede band at the front (visors, overhead console, mirror) and a closed headliner behind
# it back to the roof's end.
X_OPEN_F, X_OPEN_R = 0.400, -0.320
Y_OPEN = 0.540                           # the opening's half-width
X_HEADLINER_R = -2.040                   # the roof's trailing edge
X_A_FOOT = 1.280
Z_CARGO = GT.Z_CARGO                     # the cargo floor, flush with the sill plate (c3_0157)


def glass_top(x):
    """The side glazing's top edge (door glass and quarter light share the curve)."""
    return PN.V_GT(max(PN.X_DLO_TIP, min(x, 1.05))) - 0.004


def v_head_edge(x):
    """The headliner's outer edge: 60 mm above the side glass's top."""
    return S.v_along(x, glass_top(x), 0.050)


def _head_rows(x0, x1, nx, v_in, v_out=v_head_edge, inset=0.045, nv=22):
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
    bands = (("int_headliner_F", PN.X_ROOF_F + 0.030, X_OPEN_F, 12),
             ("int_headliner_R", X_OPEN_R, X_HEADLINER_R, 70))
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
    rows = [[S.surface_offset(x, v, -0.045), S.surface_offset(x, v, -0.004)] for (x, v) in loop]
    rv = grid_mesh("int_headliner_reveal", rows, col, lib["headliner"])
    M.orient(rv.data, lambda c: (0.0, -1.0 if c[1] > 0 else 1.0, 0.0))
    M.mirror_y(rv)
    made.append(rv)
    for x, nm in ((X_OPEN_F, "F"), (X_OPEN_R, "R")):
        rows = []
        v0 = open_v(x)
        for j in range(13):
            v = v0 + (0.9995 - v0) * j / 12.0
            rows.append([S.surface_offset(x, v, -0.045), S.surface_offset(x, v, -0.004)])
        rows[-1] = [(p[0], 0.0, p[2]) for p in rows[-1]]
        ev = grid_mesh("int_headliner_reveal" + nm, rows, col, lib["headliner"])
        M.orient(ev.data, lambda c, s=(-1.0 if nm == "F" else 1.0): (s, 0.0, 0.0))
        M.mirror_y(ev)
        made.append(ev)
    return made


def _a_door(x):
    return (x, S.v_along(x, PN.V_GT(min(x, 1.28)) - 0.004, -0.020))


def _a_screen(x):
    return (x, S.v_along(x, PN.V_A(x) + 0.001, 0.018))


def build_shell(col, lib):
    made = build_headliner(col, lib)
    # A-pillars: across from the door glass's edge to the windscreen's side edge, down to the foot
    xs = [X_A_FOOT - (X_A_FOOT - (PN.X_ROOF_F - 0.03)) * k / 56.0 for k in range(57)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs, _a_door, _a_screen, depth=0.010,
                             bulge=0.034, name="int_apillar"))
    for side in (1.0, -1.0):                       # the tweeter low on each A-pillar (c10_0002)
        x = 1.150
        a = Vector(S.BODY.surface(*_a_door(x)))
        b = Vector(S.BODY.surface(*_a_screen(x)))
        n = (Vector(S.BODY.surface_normal(*_a_door(x))) + Vector(S.BODY.surface_normal(*_a_screen(x)))).normalized()
        c = a.lerp(b, 0.5) - n * (0.010 + 0.034 + 0.002)
        c.y *= side
        nn = Vector((-n.x, -n.y * side, -n.z))
        made += F.disc(col, "int_apillar_tweeter%s" % ("L" if side > 0 else "R"), tuple(c),
                       tuple(nn), 0.024, lib["mesh_silver"], dome=0.002, rim=0.0018,
                       rim_mat=lib["chrome"])
    # roof rails over the side glass, back to the quarter light's tip
    xs = [PN.X_ROOF_F - 0.02 - (PN.X_ROOF_F - 0.02 - PN.X_DLO_TIP) * k / 60.0 for k in range(61)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, glass_top(x), -0.030)),
        lambda x: (x, S.v_along(x, glass_top(x), 0.110)),
        depth=0.016, bulge=0.024, name="int_roofrail"))
    # B-pillar: between the door glasses, belt to rail
    vb0 = PN.V_BELT(0.0) + 0.002
    vb1 = PN.V_GT(-0.12) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 24.0 for k in range(25)]
    made.append(CB.edge_band(
        S.BODY, col, lib["leather_door"], vs,
        lambda v: (PN.GB_F + 0.012, v), lambda v: (PN.GB_R - 0.012, v),
        depth=0.012, bulge=0.016, name="int_bpillar"))
    # the D-pillar and the corner behind the quarter light: an offset trim from the belt up under the
    # headliner and, behind the roof's end, round the backlight's side edge
    xs = [PN.X_DLO_TIP + 0.040 - (PN.X_DLO_TIP + 0.040 + 2.48) * k / 30.0 for k in range(31)]

    def c_lo(x):
        return PN.V_BELT(x) - 0.020

    def c_hi(x):
        a = v_head_edge(max(x, X_HEADLINER_R)) + 0.010
        if x >= PN.X_KNEE:
            return a
        b = PN.V_REARGLASS(x) + 0.012
        t = _smooth((PN.X_KNEE - x) / 0.06)
        return a + (b - a) * t
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.030,
                               bulge=0.020, nt=18, name="int_cpillar", overlap=0.010))
    x0 = xs[0]
    a, b = S.v_along(x0, c_lo(x0), -0.010), S.v_along(x0, c_hi(x0), 0.010)
    rows = []
    for j in range(17):
        t = j / 16.0
        v = a + (b - a) * t
        d = 0.030 + 0.020 * math.sin(math.pi * t) ** 0.7
        rows.append([S.surface_offset(x0, v, -d), S.surface_offset(x0, v, -0.004)])
    fl = grid_mesh("int_cpillar_flange", rows, col, lib["headliner"])
    M.orient(fl.data, lambda c: (1.0, 0.0, 0.0))
    M.mirror_y(fl)
    made.append(fl)
    made += build_roof_fittings(col, lib)
    # floor and sills
    made.append(CB.floor(col, lib["carpet"], -1.34, 1.20, 1.32, FLOOR_Z, 0.70,
                         lambda x: 0.77 - 0.06 * _smooth((x - 1.0) / 0.12), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.30, 1.10, 0.74, 0.88, FLOOR_Z, 0.415, name="int_sill"))
    made += build_sill_plates(col, lib)
    return made


# --------------------------------------------------------------- sill plates
def build_sill_plates(col, lib):
    """The brushed scuff plate on each doorway's sill (c3_0001: a steel plate with the model's name)."""
    from mathutils import Matrix
    made = []
    z0 = 0.4155
    ink = bpy.data.materials.get("INT_Trim_Dark") or lib["satin"]
    for tag, (x0, x1) in (("F", (-0.020, 0.980)), ("R", (-1.120, -0.250))):
        for side, st in ((1.0, "L"), (-1.0, "R")):
            y0, y1 = 0.775, 0.860
            made.append(F.box(col, "int_sillplate_%s%s" % (tag, st),
                              (0.5 * (x0 + x1), side * 0.5 * (y0 + y1), z0 + 0.0016),
                              (x1 - x0, y1 - y0, 0.0032), lib["brushed"], r=0.0012))
            txt = M.text_mesh("int_sillplate_%s%s_text" % (tag, st), "G9L", 0.028, col, ink,
                              extrude=0.0004, bold=True, resolution=3, spacing=1.7)
            xc = 0.5 * (x0 + x1)
            rot = Matrix.Rotation(math.pi if side > 0 else 0.0, 4, 'Z')
            txt.matrix_world = Matrix.Translation((xc + (0.045 if side > 0 else -0.045),
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
                     for z in [0.42 + (DR._belt_z(x) - 0.42) * k / 12.0 for k in range(13)]])
    seal = grid_mesh("int_bpillar_seal", rows, col, lib["satin"])
    M.orient(seal.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(seal)
    made.append(seal)
    # kick panels: the side walls ahead of the door opening, floor to dash
    yk = 0.775
    x_open = PN.X_DOOR_F(0.5) - 0.040
    kick_y = Curve([(x_open, yk), (x_open + 0.030, 0.620), (1.34, 0.620)], mode="pchip")
    made.append(CB.wall(col, lib["lower_card"],
                        [(x_open + (1.34 - x_open) * k / 16.0, kick_y(x_open + (1.34 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.12, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    kick_y = [(x_open, yk + (0.93 - yk) * k / 10.0) for k in range(11)]
    kick_top = lambda x, y: 1.06 + 0.10 * _smooth((y - 0.80) / 0.04)
    # black plastic low down, the door card's red leather above the sill line (c10_0002: the dash runs into the card)
    made.append(CB.wall(col, lib["lower_card"], kick_y, lambda x, y: FLOOR_Z, lambda x, y: 0.80,
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))
    made.append(CB.wall(col, lib["leather_dash"], kick_y, lambda x, y: 0.795, kick_top,
                        name="int_kick_front_up", facing=(-1.0, 0.0, 0.0)))
    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = DR.rear_card(1.0)
    vq = PN.V_BELT(0.0) + 0.10
    x_trail = lambda z: max(PN.X_DOOR_R(0.5) + 0.010, DR._arch_front(z, 0.0) - 0.002)
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["lower_card"], x_trail, -1.40,
        FLOOR_Z + 0.02, 0.740, 0.980, 1.200, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(x_trail(z), z) - rc.th(z) + 0.010)
    made += build_cowl_side(col, lib)
    made += build_cargo(col, lib)
    return made


def build_cowl_side(col, lib):
    """The A-pillar's foot: a wall from the dash's end out to the skin ahead of the front door, floor of
    the pillar band to the footwell, so the fender's inside does not show between them."""
    xs = [1.04 + 0.27 * k / 12.0 for k in range(13)]
    pts = [(x, CB.skin_offset_y(S.BODY, x, 1.05, 0.050, 0.99)) for x in xs]
    made = [CB.wall(col, lib["leather_dash"], pts, lambda x, y: 0.90, lambda x, y: 1.22,
                    nz=8, name="int_cowl_side", facing=(0.0, -1.0, 0.0))]
    # the A-pillar's foot: a band under the body's upper surface from the windscreen's corner out over the fender's
    # crown, or the fender's top shows between the pillar band and that wall (seen from the seat at z 1.25)
    xs_c = [1.00 + 0.31 * k / 24.0 for k in range(25)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs_c,
                             lambda x: (x, S.v_at_y_upper(x, 0.69)), lambda x: (x, S.v_at_y_upper(x, 0.86)),
                             depth=0.012, bulge=0.0, nt=8, name="int_cowl_top"))
    # and the slit between the dash's front end and the windscreen's lower edge: a plate on the pad's end up to the glass
    x_c = 1.2815
    rows = []
    for k in range(25):
        y = -0.80 + 1.60 * k / 24.0
        zg = z_glass(x_c, y)
        rows.append([(x_c, y, zg - 0.022), (x_c, y, zg + 0.006)])
    plate = grid_mesh("int_cowl_closure", rows, col, lib["lower_card"])
    M.orient(plate.data, lambda c: (-1.0, 0.0, 0.0))
    made.append(plate)
    return made


def _skin_y(x, z, depth=0.045):
    return CB.skin_offset_y(S.BODY, x, z, depth, 0.99)


def build_cargo(col, lib):
    """Behind the rear bench: the cargo bay (a carpeted floor, side walls to the belt) open at the back: the tailgate
    swings up (g9l_gate), so there is no rear wall, only the sill plate and the boot's fittings."""
    made = []
    x0, x1 = -1.34, -2.46
    xs = [x0 + (x1 - x0) * k / 20.0 for k in range(21)]
    # the bay's half-width at height z, `depth` inboard of the body's skin; the tail's skin closes in behind x -2.30
    # and the opening's mouth is 0.78 wide (c3_0157), so neither is passed
    def half(x, z, depth=0.062):
        return min(0.78, CB.skin_offset_y(S.BODY, max(x, -2.30), z, depth, 0.99))
    rows = []
    for x in xs:
        hw = half(x, Z_CARGO)
        rows.append([(x, hw * j / 12.0, Z_CARGO) for j in range(13)])
    carpet = GT.boot_carpet()
    fl = grid_mesh("int_cargo_floor", rows, col, carpet)
    M.orient(fl.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(fl)
    made.append(fl)
    # the side walls, up to the glass's lower edge: they follow the skin at every height (the sail leans in above the
    # belt, a wall at the floor's width stands outside the body), and the belt's height is read at the last x the
    # belt line is defined for, not extrapolated to the tail, where it climbs to the roof
    rows = []
    for x in xs:
        zt = DR._belt_z(max(x, -1.80)) + 0.040
        rows.append([(x, half(x, Z_CARGO + (zt - Z_CARGO) * k / 10.0), Z_CARGO + (zt - Z_CARGO) * k / 10.0)
                     for k in range(11)])
    wall = grid_mesh("int_cargo_wall", rows, col, lib["lower_card"])
    M.orient(wall.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(wall)
    made.append(wall)
    # the seat backs' rear faces are the front wall of the bay (the rear seat's shell); a back panel
    # closes the gap between the seats and the floor
    made.append(CB.bulkhead(col, carpet, [(x0, FLOOR_Z + 0.02), (x0, Z_CARGO)],
                            lambda x, z: 0.74, n=14, name="int_cargo_front", facing=(1.0, 0.0, 0.0)))
    sb = GT.build_seatback_carpet(col, carpet)
    if sb is not None:
        made.append(sb)
    made += GT.build_boot_details(col, lib, lambda x: half(x, 1.0))
    return made


# ------------------------------------------------------------------ pedals
def build_pedals(col, lib):
    return CP.pedals(col, lib, FLOOR_Z, [("rest", 0.570, 1.200, 0.540, 0.080, 0.190, 5),
                                         ("brake", 0.400, 1.160, 0.580, 0.100, 0.100, 3),
                                         ("accel", 0.250, 1.185, 0.540, 0.055, 0.190, 0)])


# ------------------------------------------------------------ roof fittings
def build_roof_fittings(col, lib):
    made = []
    zg = S.surface_offset(MIRROR_C[0] + 0.05, S.v_at_y_upper(MIRROR_C[0] + 0.05, 0.0), -0.006)[2]
    made += CP.rear_view_mirror(col, lib, MIRROR_C, zg)
    # the overhead console on the front band (c3_0072: a dark panel with the lamps and keys)
    xs = [0.500 - 0.100 * k / 8.0 for k in range(9)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.115 * (1 - 2 * j / 10.0), zr - 0.014 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["piano"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    # sun visors folded against the front band either side
    for side in (1.0, -1.0):
        rows = []
        for i in range(7):
            x = PN.X_ROOF_F + 0.02 - 0.12 * i / 6.0
            zr = S.surface_offset(x, S.v_at_y_upper(x, 0.35), -0.046)[2]
            rows.append([(x, side * (0.150 + 0.40 * j / 8.0),
                          zr - 0.002 * math.sin(math.pi * j / 8) - 0.020 * (j / 8.0) ** 2)
                         for j in range(9)])
        vz = grid_mesh("int_visor_%s" % ("L" if side > 0 else "R"), rows, col, lib["headliner"])
        M.orient(vz.data, lambda c: (0.0, 0.0, -1.0))
        M.solidify(vz, 0.014, 1.0)
        M.bevel(vz, 0.005, 2, 40)
        made.append(vz)
    return made


# ---------------------------------------------------------------- lighting
def cabin_lights(col):
    return F.lights(col, [
        ("int_L_Roof", (-0.20, 0.0, 1.85), (-0.20, 0.0, 0.50), (1.8, 1.30), 10.0,
         (0.90, 0.94, 1.00), True),
        ("int_L_Back", (-1.55, 0.0, 1.50), (0.60, 0.0, 0.95), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.55, 1.40), (0.0, 0.0, 0.90), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
        ("int_L_Right", (0.0, -1.55, 1.40), (0.0, 0.0, 0.90), (2.2, 0.6), 2.5,
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
