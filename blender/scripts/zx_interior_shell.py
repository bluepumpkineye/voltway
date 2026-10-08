"""Zeekr 7X cabin: what closes it - the headliner round the glass roof, the pillar trims, the
floor and sills, the kick panels, the rear wheelhouses, the parcel shelf - plus the pedals,
the roof fittings and the render rig; `main()` builds the whole cabin.

Every enclosing surface is an offset of the exterior loft (carkit.interior.cabin), so the
inside always agrees with the outside. carkit.qa.leaks finds what is still missing.
"""
import math

import bpy
from mathutils import Vector

import zx_surface as S
import zx_panels as PN
import zx_interior as ZI
import zx_interior_doors as DR
from zx_interior import FLOOR_Z, MIRROR_C, _smooth, z_glass
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import cabin as CB
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path

# ---------------------------------------------------------------- the shell
# The roof's glass (ZX_Glass_Roof, x -0.094 .. 0.41) shows through an opening in the
# headliner: a suede frame at the front (visors, overhead console, speakers) and a closed
# headliner behind the glass back to the backlight (c3_0017).
X_OPEN_F, X_OPEN_R = 0.225, -0.085
Y_OPEN = 0.500                           # the opening's half-width
X_HEADLINER_R = -1.930                   # the headliner runs back to the backlight's top
X_DOOR_R_TOP = -1.22                     # the rear door's trailing edge at the belt


def v_head_edge(x):
    """The headliner's outer edge: 50 mm above the side glass's top."""
    return S.v_along(x, PN.V_GT(max(x, PN.X_DLO_TIP)), 0.050)


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


def build_shell(col, lib):
    made = build_headliner(col, lib)
    # A-pillars: across from the door glass's front edge to the windscreen's side edge, 20 mm
    # over each glass; down to the dash's corner at the foot (x 1.15: the web's driver eye saw
    # the painted rail below the old end at x 0.70) and on past the header under the headliner
    X_A_FOOT = 1.150
    xs = [X_A_FOOT - (X_A_FOOT - (PN.X_ROOF_F - 0.03)) * k / 48.0 for k in range(49)]

    def a_door(x):
        return (x, S.v_along(x, PN.v_up(x, max(PN.BELT_Z(0.62), PN.z_a(min(x, PN.A_FOOT[0])))), -0.020))
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs, a_door,
        lambda x: (x, S.v_along(x, PN.V_A(x), 0.018)),
        depth=0.010, bulge=0.034, name="int_apillar"))
    # the tweeter low on each A-pillar, over the dash's end (c10_0002: a round perforated grille)
    for side in (1.0, -1.0):
        x = 0.950
        a = Vector(S.BODY.surface(*a_door(x)))
        b = Vector(S.BODY.surface(x, S.v_along(x, PN.V_A(x), 0.018)))
        n = (Vector(S.BODY.surface_normal(*a_door(x))) +
             Vector(S.BODY.surface_normal(x, S.v_along(x, PN.V_A(x), 0.018)))).normalized()
        c = a.lerp(b, 0.5) - n * (0.010 + 0.034 + 0.002)
        c.y *= side
        nn = Vector((-n.x, -n.y * side, -n.z))
        made += F.disc(col, "int_apillar_tweeter%s" % ("L" if side > 0 else "R"), tuple(c),
                       tuple(nn), 0.024, lib["speaker"], dome=0.002, rim=0.0018,
                       rim_mat=lib["satin"])
    # roof rails over the side glass, back to the quarter light's tip
    xs = [PN.X_ROOF_F + 0.04 - (PN.X_ROOF_F + 0.04 - PN.X_DLO_TIP) * k / 44.0 for k in range(45)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, PN.V_GT(x), -0.010)),
        lambda x: (x, S.v_along(x, PN.V_GT(x), 0.070)),
        depth=0.012, bulge=0.020, name="int_roofrail"))
    # B-pillar: between the door glasses, belt to rail
    xb = PN._DOOR_B_EDGE(1.2)
    vb0 = PN.V_BELT(xb) - 0.006
    vb1 = PN.V_GT(xb) + 0.014
    vs = [vb0 + (vb1 - vb0) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(
        S.BODY, col, lib["leather_taupe"], vs,
        lambda v: (PN.GB_F + 0.012, v), lambda v: (PN.GB_R - 0.012, v),
        depth=0.012, bulge=0.016, name="int_bpillar"))
    # C-pillar: the broad sail behind the quarter light, as an offset trim, from under the belt
    # up under the headliner, and behind the knee up to the backlight's side edge
    xs = [PN.X_DLO_TIP + 0.030 - (PN.X_DLO_TIP + 0.030 + 2.26) * k / 24.0 for k in range(25)]

    def c_lo(x):
        z = max(1.06, min(DR._belt_z(x) - 0.06, 1.17))
        z += (1.02 - z) * _smooth((-1.70 - x) / 0.15)
        return S.v_at_z(x, z, 0.30, 0.99)

    def c_hi(x):
        a = v_head_edge(max(x, X_HEADLINER_R)) + 0.010
        if x >= PN.X_KNEE:
            return a
        b = PN.V_REARGLASS(x) + 0.012
        t = _smooth((PN.X_KNEE - x) / 0.05)
        return a + (b - a) * t
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs, c_lo, c_hi, inset=0.030,
                               bulge=0.020, nt=16, name="int_cpillar", overlap=0.010))
    # a flange from the trim's front edge out to the skin
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
    # under the quarter light: an offset trim from below the shoulder up onto the glass's
    # lower edge
    xs = [X_DOOR_R_TOP + 0.010 - (X_DOOR_R_TOP + 0.010 - (PN.X_DLO_TIP - 0.020)) * k / 10.0
          for k in range(11)]
    made.append(CB.pillar_trim(S.BODY, col, lib["headliner"], xs,
                               lambda x: S.v_at_z(x, 1.100, 0.30, 0.99),
                               lambda x: PN.V_BELT(x), inset=0.014, bulge=0.004, nt=16,
                               name="int_qtr_lower", overlap=0.008))
    made += build_roof_fittings(col, lib)
    # floor and sills
    made.append(CB.floor(col, lib["carpet"], -1.55, 1.00, 1.19, FLOOR_Z, 0.62,
                         lambda x: 0.73 - 0.05 * _smooth((x - 0.88) / 0.10), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.30, 1.02, 0.72, 0.86, FLOOR_Z, 0.445,
                        name="int_sill"))
    made += build_sill_plates(col, lib)
    return made


# --------------------------------------------------------------- sill plates
def build_sill_plates(col, lib):
    """The brushed scuff plate on each doorway's sill with the maker's name engraved in it
    (c3_0001, c3_0009): a slim steel plate along the front doorway and another along the
    rear."""
    from mathutils import Matrix
    made = []
    z0 = 0.4455
    ink = bpy.data.materials.get("INT_Trim_Dark") or lib["trim_dark"]
    for tag, (x0, x1) in (("F", (-0.020, 0.880)), ("R", (-1.120, -0.250))):
        for side, st in ((1.0, "L"), (-1.0, "R")):
            y0, y1 = 0.745, 0.826
            made.append(F.box(col, "int_sillplate_%s%s" % (tag, st),
                              (0.5 * (x0 + x1), side * 0.5 * (y0 + y1), z0 + 0.0016),
                              (x1 - x0, y1 - y0, 0.0032), lib["brushed"], r=0.0012))
            txt = M.text_mesh("int_sillplate_%s%s_text" % (tag, st), "ZEEKR", 0.028, col, ink,
                              extrude=0.0004, bold=True, resolution=3, spacing=1.7)
            xc = 0.5 * (x0 + x1)
            rot = Matrix.Rotation(math.pi if side > 0 else 0.0, 4, 'Z')
            txt.matrix_world = Matrix.Translation((xc + (0.045 if side > 0 else -0.045),
                                                   side * 0.5 * (y0 + y1) + (0.0), z0 + 0.0036)) @ rot
            made.append(txt)
    return made


# ------------------------------------------------------------ closing trims
def build_closures(col, lib):
    """What stops the painted body showing from inside: B-pillar seals, footwell kick panels,
    the rear wheelhouse trims, the parcel shelf and bulkhead."""
    made = []
    vh = DR._v_top_front() + 0.10
    xb = PN._DOOR_B_EDGE(0.8)
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
    x_open = PN._DOOR_F_EDGE(0.60) - 0.040     # overlaps the door card's front end
    # the front wheelhouse's inner wall stands at |y| 0.675 from x 1.026 (ZX_Liner_F): the
    # wall steps in to 0.662 before it, or the dark liner shows beside the pedals
    kick_y = Curve([(x_open, yk), (x_open + 0.030, 0.662), (1.16, 0.662)], mode="pchip")
    made.append(CB.wall(col, lib["leather_taupe"],
                        [(x_open + (1.16 - x_open) * k / 16.0, kick_y(x_open + (1.16 - x_open) * k / 16.0))
                         for k in range(17)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.93, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    made.append(CB.wall(col, lib["leather_taupe"],
                        [(x_open, yk + (0.90 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z, lambda x, y: 1.00 + 0.10 * _smooth((y - 0.78) / 0.04),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))
    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = DR.rear_card(1.0)
    vq = max(PN.V_BELT(x) for x in (-1.40, -1.55)) + 0.10
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_taupe"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.88,
        FLOOR_Z + 0.02, 0.690, 0.995, 1.215, 0.062, vq, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)
    # (behind the rear seats is the boot: zx_gate.build_boot, built with the openings; with the
    # hatch shut it sits dark behind the seat backs, as in the car)
    return made


# ------------------------------------------------------------------ pedals
def build_pedals(col, lib):
    """c10_0002: the brake (a wide rubber pad) ahead of the driver, the accelerator (tall,
    narrow) to its right beside the console, a dead pedal far left."""
    made = []
    p = math.radians(38.0)
    a = Vector((math.sin(p), 0.0, math.cos(p)))
    n = Vector((-math.cos(p), 0.0, math.sin(p)))
    for name, y, x, z, w, h, strips in (("rest", 0.612, 1.000, 0.470, 0.075, 0.210, 5),
                                        ("brake", 0.392, 0.985, 0.500, 0.100, 0.082, 3),
                                        ("accel", 0.245, 1.020, 0.450, 0.058, 0.205, 0)):
        c = Vector((x, y, z))
        made.append(F.box(col, "int_pedal_" + name, tuple(c), (0.010, w, h), lib["brushed"],
                          r=0.003, pitch=p))
        if name == "rest":
            for k in range(strips):
                q = c + n * 0.006 + Vector((0.0, (k - 2) * w * 0.18, 0.0))
                made.append(F.box(col, "int_pedal_%s_slot%d" % (name, k), tuple(q),
                                  (0.004, 0.006, h * 0.85), lib["rubber"], r=0.0015, pitch=p))
        else:
            for k in range(strips):
                q = c + n * 0.006 + a * ((k - 1) * h * 0.28)
                made.append(F.box(col, "int_pedal_%s_strip%d" % (name, k), tuple(q),
                                  (0.004, w * 0.82, 0.008), lib["rubber"], r=0.0015, pitch=p))
    return made


# ------------------------------------------------------------ roof fittings
def build_roof_fittings(col, lib):
    made = []
    # the frameless rear-view mirror, hung from the header on a short stem (c10_0001)
    w, h, t = 0.250, 0.062, 0.016
    made.append(F.round_slab(col, "int_rvmirror", MIRROR_C, w, h, t, 0.024, lib["piano"],
                             tilt=math.radians(8.0)))
    mg = bpy.data.materials.get("INT_Mirror") or bpy.data.materials.new("INT_Mirror")
    mg.use_nodes = True
    bm = next(n for n in mg.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bm.inputs["Base Color"].default_value = (0.30, 0.31, 0.32, 1.0)
    bm.inputs["Metallic"].default_value = 1.0
    bm.inputs["Roughness"].default_value = 0.05
    made.append(F.round_slab(col, "int_rvmirror_glass",
                             (MIRROR_C[0] - t * 0.5 - 0.0008, 0.0, MIRROR_C[2]), w - 0.006,
                             h - 0.006, 0.0008, 0.021, mg, tilt=math.radians(8.0)))
    zg = z_glass(MIRROR_C[0] + 0.07, 0.0) - 0.006
    stem = smooth_path([(MIRROR_C[0] + 0.02, 0.0, MIRROR_C[2] + 0.02),
                        (MIRROR_C[0] + 0.045, 0.0, 0.5 * (MIRROR_C[2] + zg) + 0.01),
                        (MIRROR_C[0] + 0.07, 0.0, zg)], 8)
    made.append(tube("int_rvmirror_stem", stem, ellipse(0.016, 0.010, 10), col, lib["satin"],
                     lateral=(0.0, 1.0, 0.0)))
    # the overhead console on the front band, in a rose-gold ring (c10_0001)
    xs = [0.395 - 0.170 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.046
        rows.append([(x, 0.115 * (1 - 2 * j / 10.0), zr - 0.014 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["leather_white"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    loop = [(0.31 + a, b, S.Z_ROOF(0.31) - 0.062) for (a, b) in
            F.round_rect_xy(-0.050, 0.050, -0.112, 0.112, 0.020)]
    loop.append(loop[0])
    made.append(tube("int_overhead_ring", loop, ellipse(0.0022, 0.0022, 6), col, lib["rose"],
                     lateral=(0.0, 0.0, 1.0)))
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
        x = 0.250
        v = S.v_at_y_upper(x, 0.50)
        p = Vector(S.surface_offset(x, v, -0.0465))
        nrm = -Vector(S.surface_normal(x, v))
        made += F.disc(col, "int_head_speaker%s" % ("L" if side > 0 else "R"),
                       (p.x, side * p.y, p.z), (nrm.x, side * nrm.y, nrm.z), 0.030,
                       lib["speaker"], rim=0.0022, rim_mat=lib["chrome"])
    return made


# ---------------------------------------------------------------- lighting
def cabin_lights(col):
    """The render rig: a soft box over the cabin, a fill from behind kept out of glossy
    rays, two weak side fills."""
    return F.lights(col, [
        ("int_L_Roof", (-0.30, 0.0, 1.50), (-0.30, 0.0, 0.40), (1.7, 1.25), 10.0,
         (0.90, 0.94, 1.00), True),
        ("int_L_Back", (-1.15, 0.0, 1.30), (0.60, 0.0, 0.85), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00), False),
        ("int_L_Left", (0.0, 1.50, 1.25), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
        ("int_L_Right", (0.0, -1.50, 1.25), (0.0, 0.0, 0.80), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00), True),
    ])


def build_boot(col, lib):
    """The cargo area behind the rear seats and the hatch's inner liner (zx_gate): the cabin's
    half of the tailgate. Needs the exterior's tail cap whole (before zx_gate.split_tail)."""
    import zx_gate as RG
    made = RG.build_boot(col, lib) + RG.build_boot_details(col)
    if bpy.data.objects.get("ZX_Tailgate") is None:
        made.append(RG.build_liner(col))
    return made


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
                ("pedals", lambda: build_pedals(col, lib)),
                ("boot", lambda: build_boot(col, lib)))
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
