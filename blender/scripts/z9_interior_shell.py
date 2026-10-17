"""Denza Z9 cabin: what closes it - the headliner round the glass roof, the pillar trims, the floor
and sills, the kick panels, the rear wheelhouses, the parcel shelf and bulkhead - plus the pedals,
the roof fittings and the render rig; `main()` builds the whole cabin.

Every enclosing surface is an offset of the exterior loft (carkit.interior.cabin), so the inside
always agrees with the outside. cabin_tools.leaks finds what is still missing.
"""
import math

import bpy
from mathutils import Vector

import z9_surface as S
import z9_panels as PN
import z9_interior as ZI
import z9_interior_doors as DR
import z9_gate as GT
import cabin_parts as CP
from z9_interior import FLOOR_Z, MIRROR_C, z_glass
from cabin_parts import smooth as _smooth
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path

# ---------------------------------------------------------------- the shell
# The panoramic glass (Z9_Glass_Roof, x -1.25 .. 0.265) shows through an opening in the headliner:
# a suede band at the front (visors, overhead console, mirror) and a closed headliner behind the
# glass back to the backlight.
X_OPEN_F, X_OPEN_R = 0.040, -1.060
Y_OPEN = 0.440                           # the opening's half-width
X_HEADLINER_R = -1.935                   # the headliner runs back to the backlight's top
X_A_FOOT = 1.000


def glass_top(x):
    """The side glazing's top edge: the door glass's, and behind the rear door the quarter light's
    (it drops toward the tip, below V_GT)."""
    return PN.V_GLASS_TOP(max(x, PN.X_QTR_R))


def v_head_edge(x):
    """The headliner's outer edge: 60 mm above the side glass's top."""
    return S.v_along(x, glass_top(x), 0.060)


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
    # the side rails of the opening
    rows = _head_rows(X_OPEN_F + 0.002, X_OPEN_R - 0.002, 40, open_v, nv=10)
    ob = grid_mesh("int_headliner_side", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, -c[1], -1.0))
    M.mirror_y(ob)
    made.append(ob)
    # the opening's reveal, all round, up to the glass
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
    """The A-pillar's door-glass edge: 20 mm over the glass's top edge."""
    return (x, S.v_along(x, min(PN.V_A(x) - 0.020, PN.V_GT(x)), -0.020))


def _a_screen(x):
    return (x, S.v_along(x, PN.V_A(x) + 0.020, 0.018))


def build_shell(col, lib):
    made = build_headliner(col, lib)
    # A-pillars: across from the door glass's front edge to the windscreen's side edge, down to the
    # dash's corner at the foot and on past the header under the headliner
    xs = [X_A_FOOT - (X_A_FOOT - (PN.X_ROOF_F - 0.03)) * k / 48.0 for k in range(49)]
    made.append(CB.edge_band(S.BODY, col, lib["headliner"], xs, _a_door, _a_screen, depth=0.010,
                             bulge=0.034, name="int_apillar"))
    # the tweeter low on each A-pillar, over the dash's end (c10_0001: a round perforated grille)
    for side in (1.0, -1.0):
        x = 0.930
        a = Vector(S.BODY.surface(*_a_door(x)))
        b = Vector(S.BODY.surface(*_a_screen(x)))
        n = (Vector(S.BODY.surface_normal(*_a_door(x))) + Vector(S.BODY.surface_normal(*_a_screen(x)))).normalized()
        c = a.lerp(b, 0.5) - n * (0.010 + 0.034 + 0.002)
        c.y *= side
        nn = Vector((-n.x, -n.y * side, -n.z))
        made += F.disc(col, "int_apillar_tweeter%s" % ("L" if side > 0 else "R"), tuple(c),
                       tuple(nn), 0.024, lib["speaker"], dome=0.002, rim=0.0018,
                       rim_mat=lib["chrome"])
    # roof rails over the side glass, back to the quarter light's tip
    xs = [PN.X_ROOF_F + 0.04 - (PN.X_ROOF_F + 0.04 - PN.X_QTR_R) * k / 44.0 for k in range(45)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, glass_top(x), -0.012)),
        lambda x: (x, S.v_along(x, glass_top(x), 0.085)),
        depth=0.012, bulge=0.020, name="int_roofrail"))
    # B-pillar: between the door glasses, belt to rail
    vb0 = PN.V_BELT - 0.006
    vb1 = PN.V_GT(-0.22) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(
        S.BODY, col, lib["leather_door"], vs,
        lambda v: (PN.GB_F(v) + 0.012, v), lambda v: (PN.GB_R(v) - 0.012, v),
        depth=0.012, bulge=0.016, name="int_bpillar"))
    # C-pillar: the sail behind the quarter light, an offset trim from under the shoulder up under the
    # headliner, back to the backlight's side edge
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
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.030,
                               bulge=0.020, nt=16, name="int_cpillar", overlap=0.010))
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
    # under the quarter light: an offset trim from below the shoulder up onto the glass's lower edge
    xs = [PN.X_QTR_F + 0.060 - (PN.X_QTR_F + 0.060 - (PN.X_QTR_R - 0.020)) * k / 10.0 for k in range(11)]
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs,
                               lambda x: S.v_at_z(x, 0.980, 0.30, 0.99),
                               lambda x: max(PN.V_BELT, PN.V_QTR_LOW(x)) + 0.012, inset=0.014, bulge=0.004, nt=16,
                               name="int_qtr_lower", overlap=0.008))
    made += build_roof_fittings(col, lib)
    # floor and sills
    made.append(CB.floor(col, lib["carpet"], -1.60, 0.98, 1.19, FLOOR_Z, 0.60,
                         # out to 0.80 at the toe board: the footwell's outboard corner was open below the floor line
                         # (the underbody showed as a white triangle ahead of the sill)
                         lambda x: 0.73 + 0.07 * _smooth((x - 0.85) / 0.05), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.30, 1.02, 0.72, 0.86, FLOOR_Z, 0.340, name="int_sill"))
    made += build_sill_plates(col, lib)
    return made


# --------------------------------------------------------------- sill plates
def build_sill_plates(col, lib):
    """The brushed scuff plate on each doorway's sill with the maker's name in it (c3_0001, c3_0003:
    DENZA in a steel plate)."""
    from mathutils import Matrix
    made = []
    z0 = 0.3405
    ink = bpy.data.materials.get("INT_Trim_Dark") or lib["satin"]
    for tag, (x0, x1) in (("F", (-0.020, 0.880)), ("R", (-1.200, -0.320))):
        for side, st in ((1.0, "L"), (-1.0, "R")):
            y0, y1 = 0.745, 0.826
            made.append(F.box(col, "int_sillplate_%s%s" % (tag, st),
                              (0.5 * (x0 + x1), side * 0.5 * (y0 + y1), z0 + 0.0016),
                              (x1 - x0, y1 - y0, 0.0032), lib["brushed"], r=0.0012))
            txt = M.text_mesh("int_sillplate_%s%s_text" % (tag, st), "DENZA", 0.028, col, ink,
                              extrude=0.0004, bold=True, resolution=3, spacing=1.7)
            xc = 0.5 * (x0 + x1)
            rot = Matrix.Rotation(math.pi if side > 0 else 0.0, 4, 'Z')
            txt.matrix_world = Matrix.Translation((xc + (0.045 if side > 0 else -0.045),
                                                   side * 0.5 * (y0 + y1), z0 + 0.0036)) @ rot
            made.append(txt)
    return made


# ------------------------------------------------------------ closing trims
def build_closures(col, lib):
    """What stops the painted body showing from inside: B-pillar seals, footwell kick panels, the
    rear wheelhouse trims, the parcel shelf and bulkhead."""
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
    # kick panels: the side walls ahead of the door opening, floor to dash
    yk = 0.745
    x_open = DR._door_f_edge(0.60) - 0.040
    kick_y = Curve([(x_open, yk), (x_open + 0.030, 0.662), (1.16, 0.662)], mode="pchip")
    made.append(CB.wall(col, lib["leather_door"],
                        [(x_open + (1.16 - x_open) * k / 16.0, kick_y(x_open + (1.16 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.93, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["leather_door"],
                        [(x_open, yk + (0.90 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.00 + 0.10 * _smooth((y - 0.78) / 0.04),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))
    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = DR.rear_card(1.0)
    vq = max(PN.V_BELT, PN.V_BELT) + 0.10
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_door"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.88,
        FLOOR_Z + 0.02, 0.690, 0.985, 1.215, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)
    made += build_rear_closure(col, lib)
    return made


def build_rear_closure(col, lib):
    """Behind the rear seats: a bulkhead from the floor to the parcel shelf, and the shelf back to the
    backlight's lower edge, and the boot behind the bulkhead (the lid opens, see z9_gate)."""
    made = []
    # the bulkhead behind the rear seat backs
    xb = -1.395
    made.append(CB.bulkhead(col, lib["carpet"], [(xb, FLOOR_Z + 0.02), (xb, 0.99)],
                            lambda x, z: 0.72, n=14, name="int_bulkhead", facing=(1.0, 0.0, 0.0)))
    # the parcel shelf: flat at z 0.99 to x -1.62, then rising with the deck to the backlight's edge

    def shelf_z(x):
        return 0.995 + 0.09 * _smooth((-1.62 - x) / 0.32)
    xs = [xb + (X_HEADLINER_R - xb) * k / 24.0 for k in range(25)]
    rows = []
    for x in xs:
        hw = min(0.80, S.section_v(x, S.v_at_z(x, shelf_z(x), 0.30, 0.99))[0] - 0.040)
        rows.append([(x, hw * j / 12.0, shelf_z(x)) for j in range(13)])
    ob = grid_mesh("int_parcel_shelf", rows, col, lib["headliner"])
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    M.mirror_y(ob)
    made.append(ob)

    # the boot: the walls follow the skin at every height, the tail's closes in behind x -2.30, the mouth is 0.74 wide
    def half(x, z, depth=0.062):
        return min(0.74, CB.skin_offset_y(S.BODY, max(x, -2.30), z, depth + 0.012, 0.99))
    made += GT.build_boot(col, lib, half)
    return made


# ------------------------------------------------------------------ pedals
def build_pedals(col, lib):
    """c10_0002: the brake (a wide silver plate) ahead of the driver, the accelerator (tall, narrow)
    beside the console, a dead pedal far left."""
    return CP.pedals(col, lib, FLOOR_Z, [("rest", 0.612, 0.985, 0.440, 0.080, 0.200, 5),
                                         ("brake", 0.392, 0.950, 0.490, 0.100, 0.130, 3),
                                         ("accel", 0.245, 0.985, 0.445, 0.050, 0.205, 0)])


# ------------------------------------------------------------ roof fittings
def build_roof_fittings(col, lib):
    made = []
    zg = z_glass(MIRROR_C[0] + 0.07, 0.0) - 0.006
    made += CP.rear_view_mirror(col, lib, MIRROR_C, zg)
    # the overhead console on the front band (c10_0001: a black glass panel with lamps and keys)
    xs = [0.230 - 0.150 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.115 * (1 - 2 * j / 10.0), zr - 0.014 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["piano"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    # sun visors folded against the front band either side: broad suede pads
    for side in (1.0, -1.0):
        rows = []
        for i in range(9):
            x = PN.X_ROOF_F + 0.04 - 0.19 * i / 8.0
            zr = S.surface_offset(x, S.v_at_y_upper(x, 0.35), -0.046)[2]
            rows.append([(x, side * (0.150 + 0.40 * j / 8.0),
                          zr - 0.002 * math.sin(math.pi * j / 8) - 0.020 * (j / 8.0) ** 2)
                         for j in range(9)])
        vz = grid_mesh("int_visor_%s" % ("L" if side > 0 else "R"), rows, col, lib["headliner"])
        M.orient(vz.data, lambda c: (0.0, 0.0, -1.0))
        M.solidify(vz, 0.014, 1.0)
        M.bevel(vz, 0.005, 2, 40)
        made.append(vz)
    # the two round speaker grilles in the front band
    for side in (1.0, -1.0):
        x = 0.200
        v = S.v_at_y_upper(x, 0.50)
        p = Vector(S.surface_offset(x, v, -0.0465))
        nrm = -Vector(S.surface_normal(x, v))
        made += F.disc(col, "int_head_speaker%s" % ("L" if side > 0 else "R"),
                       (p.x, side * p.y, p.z), (nrm.x, side * nrm.y, nrm.z), 0.030,
                       lib["speaker"], rim=0.0022, rim_mat=lib["chrome"])
    return made


# ---------------------------------------------------------------- lighting
def cabin_lights(col):
    """The render rig: a soft box over the cabin, a fill from behind kept out of glossy rays, two
    weak side fills."""
    return F.lights(col, [
        ("int_L_Roof", (-0.30, 0.0, 1.45), (-0.30, 0.0, 0.40), (1.7, 1.25), 10.0,
         (0.90, 0.94, 1.00), True),
        ("int_L_Back", (-1.15, 0.0, 1.25), (0.60, 0.0, 0.85), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.50, 1.20), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
        ("int_L_Right", (0.0, -1.50, 1.20), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
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
