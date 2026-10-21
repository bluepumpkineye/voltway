"""BYD Seal EV front end: Ocean X shark-nose closed upper fascia, signature
hook-shaped double-U LED headlamps (with multi-segment jewel-faceted crystalline
LED projector cubes and lower hook DRL extension), roof-mounted God's Eye LiDAR
pod, deep aggressive vertical side air intakes with geometric diamond mesh and
wave-gill LED strips, sculpted X-crease bumper surfacing, deep central trapezoidal
lower grille with horizontal slats and millimeter-wave radar, and aerodynamic chin
splitter with satin silver accent blade.

Calibrated directly against Autohome Series 6394 studio turnarounds and photos.
"""
import math
import bpy
from mathutils import Vector

import seal_surface as S
import seal_nose as N
from carkit import geom
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.body import panels as BP
import carkit.place as P
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE

PLACER = P.Placer(N.BODY.proud)
LAMP_BODY = ("Seal_Fascia", "Seal_Fender_Front", "Seal_Hood")
LAMP_CENTRE = (1.92, 0.44, 0.65)


def _lamp_place(p, d=0.0):
    return PLACER.radial(p, LAMP_CENTRE, LAMP_BODY, d)


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# Crisp hexagonal/angular fog-lamp & side air-intake housing
POCKET = [
    (0.515, 0.340),
    (0.575, 0.448),
    (0.718, 0.448),
    (0.775, 0.340),
    (0.718, 0.225),
    (0.575, 0.225),
]

# Deeper, wider sculpted lower central trapezoidal grille
GRILLE = [(-0.02, 0.325), (0.460, 0.325), (0.480, 0.280), (0.455, 0.160), (-0.02, 0.160)]

PLATE_PITCH = 24.0


# ------------------------------------------------------------------ helpers
def _face(y, z, d=0.0):
    z_clamped = max(NOSE.Z_LO + 0.003, min(NOSE.Z_HI - 0.003, z))
    w, v = NOSE.wv_at(abs(y), z_clamped)
    p, n = NOSE.point(w, v), NOSE.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _box(name, c, size, collection, mat):
    x, y, z = c
    hx, hy, hz = (0.5 * t for t in size)
    v = [(x + sx * hx, y + sy * hy, z + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    ob = M.obj(name, v, f, collection, mat)
    return ob


# ------------------------------------------------------------------ fascia
def _cut_fascia(ob):
    cutters = [C.prism_x("_cut_pocket_" + ob.name, POCKET, S.HALF_L + 0.30, S.HALF_L - 0.60),
               C.prism_x("_cut_grille_" + ob.name, GRILLE, S.HALF_L + 0.30, S.HALF_L - 0.60)]
    sheet = C.sheet_bvh(ob)
    C.difference(ob, cutters, "front_cuts_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def build_fascia(collection, lib):
    made = []
    # 1. Painted Ocean X front nose & bumper skin with sharp angular creases
    fascia = FA.cap_panel(
        "Seal_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.002, N.NOSE_Z_HI - 0.0008,
        0.0, 1.0, 44, 48, mat="paint", top_to_centre=True, cuts=(_cut_fascia,),
    )
    made.append(fascia)

    # Deep recessed dark backing apron behind grille and side air-intakes
    rows, _ = BP.cap_rows(NOSE, 0.140, 0.565, 0.0, 1.0, 26, 42, offset=-0.024)
    ap = M.mesh_from_rows("Seal_Apron", rows, collection)
    M.orient(ap.data, geom.axial(1.0))
    ap.data.materials.append(lib["black_trim"])
    M.mirror_y(ap)
    M.finish(ap, thickness=0.0025, bevel=0.0)
    made.append(ap)

    # 2. Deep sculpted central lower trapezoidal grille with horizontal slats & radar
    ny, nz = 26, 12
    g_cols = []
    for i in range(ny + 1):
        y = 0.465 * i / float(ny)
        col = []
        for j in range(nz + 1):
            z = 0.160 + (0.330 - 0.160) * j / float(nz)
            col.append(_face(y, z, d=-0.028)[0])
        g_cols.append(col)
    grille = M.mesh_from_rows("Seal_Grille_Mesh", g_cols, collection)
    grille.data.materials.append(lib["black_trim"])
    M.mirror_y(grille)
    M.finish(grille, thickness=0.0025, bevel=0.0)
    made.append(grille)

    # Horizontal grille slats (gloss black)
    for idx, z_slat in enumerate((0.195, 0.242, 0.290)):
        s_lo, s_up = [], []
        for i in range(18):
            y = 0.44 * (i / 17.0)
            s_lo.append(_face(y, z_slat - 0.0075, d=-0.016)[0])
            s_up.append(_face(y, z_slat + 0.0075, d=-0.016)[0])
        s_cols = [[s_lo[c], s_up[c]] for c in range(18)]
        slat = M.mesh_from_rows(f"Seal_Grille_Slat_{idx}", s_cols, collection)
        slat.data.materials.append(lib["black_gloss"])
        M.mirror_y(slat)
        M.finish(slat, thickness=0.002, bevel=0.0)
        made.append(slat)

    # Millimeter-wave ADAS radar unit
    p_rad, _ = _face(0.0, 0.242, d=-0.006)
    made.append(_box("Seal_Front_Radar", p_rad, (0.012, 0.150, 0.082), collection, lib["black_gloss"]))

    # 3. Hexagonal / angular fog-lamp housings with 3D chevron/sunburst parallel chrome lines
    hex_pts = POCKET + [POCKET[0]]
    bezel_cols = []
    frame_cols = []
    yc_hex, zc_hex = 0.645, 0.3365
    for (yp, zp) in hex_pts:
        # Outer perimeter bezel (gloss black) wrapping from flush surface into the pocket
        p_out = _face(yp, zp, d=0.0025)[0]
        y_in = yc_hex + (yp - yc_hex) * 0.86
        z_in = zc_hex + (zp - zc_hex) * 0.86
        p_in = _face(y_in, z_in, d=-0.018)[0]
        bezel_cols.append([p_in, p_out])

        # Thin angular chrome surround rim on the hexagonal housing edge
        y_rim = yc_hex + (yp - yc_hex) * 0.94
        z_rim = zc_hex + (zp - zc_hex) * 0.94
        frame_cols.append([_face(y_rim, z_rim, d=0.0032)[0], _face(yp, zp, d=0.0032)[0]])

    hex_bezel = M.mesh_from_rows("Seal_Hex_Fog_Bezel", bezel_cols, collection)
    hex_bezel.data.materials.append(lib["black_gloss"])
    M.mirror_y(hex_bezel)
    M.finish(hex_bezel, thickness=0.0025, bevel=0.0)
    made.append(hex_bezel)

    hex_frame = M.mesh_from_rows("Seal_Hex_Fog_Chrome_Frame", frame_cols, collection)
    hex_frame.data.materials.append(lib["trim_chrome"])
    M.mirror_y(hex_frame)
    M.finish(hex_frame, thickness=0.0018, bevel=0.0)
    made.append(hex_frame)

    # Multiple thin parallel chrome lines in a 3D chevron/sunburst geometric pattern inside the hexagonal housing
    chevron_offsets = (-0.078, -0.052, -0.026, 0.000, 0.026, 0.052, 0.078)
    for c_idx, dz_apex in enumerate(chevron_offsets):
        z_apex = zc_hex + dz_apex * 0.68
        z_outer_up = zc_hex + dz_apex * 1.12 + 0.036
        z_outer_lo = zc_hex + dz_apex * 1.12 - 0.036
        # Each chevron line starts near the inner hexagon edge (y=0.545), peaks in 3D depth at the chevron vertex
        # (y=0.615, d=0.001), and fans outward to the outer hexagon edge (y=0.745, d=-0.016)
        chev_pts = [
            (0.548, z_apex + 0.018, -0.014),
            (0.608, z_apex,          0.001),
            (0.680, 0.5 * (z_apex + z_outer_up), -0.007),
            (0.745, max(0.240, min(0.432, z_outer_up)), -0.016),
        ]
        c_cols = []
        for (yy, zz, dd) in chev_pts:
            p_lo = _face(yy, zz - 0.0026, d=dd)[0]
            p_hi = _face(yy, zz + 0.0026, d=dd)[0]
            c_cols.append([p_lo, p_hi])
        ch_ob = M.mesh_from_rows(f"Seal_Chevron_Chrome_{c_idx}", c_cols, collection)
        ch_ob.data.materials.append(lib["logo_chrome"])
        M.mirror_y(ch_ob)
        M.finish(ch_ob, thickness=0.0018, bevel=0.0)
        made.append(ch_ob)

        # Secondary lower sunburst fin completing the 3D chevron V-pattern
        if abs(dz_apex) <= 0.055:
            sub_pts = [
                (0.608, z_apex, 0.001),
                (0.675, 0.5 * (z_apex + z_outer_lo), -0.007),
                (0.742, max(0.240, min(0.432, z_outer_lo)), -0.016),
            ]
            s_cols = []
            for (yy, zz, dd) in sub_pts:
                s_cols.append([_face(yy, zz - 0.0022, d=dd)[0], _face(yy, zz + 0.0022, d=dd)[0]])
            sub_ob = M.mesh_from_rows(f"Seal_Chevron_Sunburst_{c_idx}", s_cols, collection)
            sub_ob.data.materials.append(lib["trim_chrome"])
            M.mirror_y(sub_ob)
            M.finish(sub_ob, thickness=0.0016, bevel=0.0)
            made.append(sub_ob)

    # Subtle horizontal LED guide bar at the center apex of the hexagonal chevron housing
    led_cols = []
    for s_step in range(9):
        y_g = 0.555 + 0.175 * (s_step / 8.0)
        d_g = 0.002 - 0.012 * abs((s_step / 8.0) - 0.35)
        led_cols.append([_face(y_g, zc_hex - 0.0030, d=d_g)[0],
                         _face(y_g, zc_hex + 0.0030, d=d_g)[0]])
    gill = M.mesh_from_rows("Seal_Hex_Fog_LED", led_cols, collection)
    gill.data.materials.append(lib["led_white"])
    M.mirror_y(gill)
    M.finish(gill, thickness=0.0015, bevel=0.0)
    made.append(gill)

    # 4. Subtle center power-dome crease on the hood from windshield base to front edge
    nh_c = 40
    hc_cols = []
    for i in range(nh_c + 1):
        u = i / float(nh_c)
        x = (S.COWL_X + 0.020) + (2.265 - (S.COWL_X + 0.020)) * u
        # Smoothly tapered ridge that sinks slightly below the hood at both ends and along its flanks
        # so there is zero visible step or cap at the front/rear tips
        taper = math.sin(math.pi * u) ** 1.4
        w_half = 0.0070 * taper + 0.0015
        lift = 0.0024 * taper - 0.0004 * (1.0 - taper)
        _, z_c = S.section_v(x, 1.0)
        v_s = S.v_at_y_upper(x, w_half)
        y_s, z_s = S.section_v(x, v_s)
        hc_cols.append([
            (x, -y_s, z_s - 0.0005),
            (x,  0.0, z_c + lift),
            (x,  y_s, z_s - 0.0005),
        ])
    hood_crease = M.mesh_from_rows("Seal_Hood_Center_Crease", hc_cols, collection)
    M.orient(hood_crease.data, lambda c: (0.0, 0.0, 1.0))
    hood_crease.data.materials.append(lib["paint"])
    M.finish(hood_crease, thickness=0.0, bevel=0.0)
    made.append(hood_crease)

    # 5. Full-width lower front chin splitter lip + central satin silver blade
    ns = 32
    ch_lo, ch_up = [], []
    for i in range(ns + 1):
        t = i / float(ns)
        y = 0.83 * t
        ch_lo.append(_face(y, 0.140, d=0.008)[0])
        ch_up.append(_face(y, 0.160, d=0.008)[0])
    ch_cols = [[ch_lo[c], ch_up[c]] for c in range(ns + 1)]
    chin = M.mesh_from_rows("Seal_Chin_Lip", ch_cols, collection)
    chin.data.materials.append(lib["black_trim"])
    M.mirror_y(chin)
    M.finish(chin, thickness=0.003, bevel=0.0)
    made.append(chin)

    sv_cols = []
    for i in range(21):
        y = 0.46 * (i / 20.0)
        sv_cols.append([_face(y, 0.146, d=0.010)[0], _face(y, 0.160, d=0.010)[0]])
    chin_sv = M.mesh_from_rows("Seal_Chin_Silver", sv_cols, collection)
    chin_sv.data.materials.append(lib["trim_chrome"])
    M.mirror_y(chin_sv)
    M.finish(chin_sv, thickness=0.002, bevel=0.0)
    made.append(chin_sv)

    # 6. Front license plate mount & "BYD SEAL" plate
    pitch = math.radians(16.0)
    n_plate = (math.cos(pitch), 0.0, -math.sin(pitch))
    p_c, _ = _face(0.0, 0.380, d=0.003)
    p_plate_f = (p_c[0], 0.0, p_c[2])
    p_mount = tuple(p_plate_f[i] - n_plate[i] * 0.002 for i in range(3))
    made += fittings.plate("Seal_Plate_Mount_Front", p_mount, n_plate, collection, lib, w=0.480, h=0.140, depth=0.030,
                           mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Seal_Plate_Front", p_plate_f, n_plate, collection, lib, w=0.460, h=0.135, depth=0.004,
                           texts=[("BYD SEAL", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="machined")

    return made


# ------------------------------------------------------------- headlamps
# Structured Dragon Face 3.0 headlamp units with sharper upper crease, defined inner projector graphics,
# and a pronounced outer hook curving downward and inward
LAMP_UPPER = [
    (2.300, 0.280, 0.648),
    (2.248, 0.405, 0.684),
    (2.165, 0.535, 0.722),
    (2.060, 0.665, 0.758),
    (1.965, 0.768, 0.786),
    (1.895, 0.842, 0.806),    # Crisp Dragon Face 3.0 upper outer apex
]

LAMP_LOWER = [
    (2.300, 0.280, 0.648),
    (2.255, 0.395, 0.620),
    (2.178, 0.520, 0.630),
    (2.075, 0.650, 0.652),
    (1.978, 0.758, 0.692),
    (1.928, 0.818, 0.742),
    (1.895, 0.842, 0.806),
]

# Pronounced Dragon Face 3.0 outer hook wrapping around the outer corner and sweeping inward
HOOK_UPPER = [
    (1.915, 0.830, 0.765),
    (1.965, 0.782, 0.692),
    (2.055, 0.680, 0.638),
    (2.165, 0.548, 0.608),
    (2.255, 0.422, 0.592),
    (2.295, 0.335, 0.582),
]

HOOK_LOWER = [
    (1.915, 0.830, 0.765),
    (1.950, 0.792, 0.668),
    (2.042, 0.690, 0.614),
    (2.152, 0.556, 0.586),
    (2.245, 0.428, 0.570),
    (2.295, 0.335, 0.582),
]


def _projector_unit(name, c, n, size, collection, lib):
    """Structured Dragon Face 3.0 projector lens unit with satin chrome bezel, dark optical barrel,
    and glowing white LED projector core, recessed cleanly inside the headlamp housing."""
    nvec = Vector(n).normalized()
    upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
    t1 = nvec.cross(upv).normalized()
    t2 = nvec.cross(t1).normalized()
    hx, hy = size[0] * 0.5, size[1] * 0.5
    c_pt = Vector(c)
    made = []

    # 1. Structured hexagonal/octagonal chrome projector bezel ring
    seg = 12
    ring_cols = []
    for i in range(seg + 1):
        ang = 2.0 * math.pi * (i / float(seg))
        ca, sa = math.cos(ang), math.sin(ang)
        # Squircle/structured rectangular-oval projector profile
        rx = hx * (0.88 + 0.12 * abs(ca))
        ry = hy * (0.88 + 0.12 * abs(sa))
        d_out = t1 * (ca * rx) + t2 * (sa * ry)
        d_in = d_out * 0.72
        p_in = tuple(c_pt + nvec * 0.0005 + d_in)
        p_out = tuple(c_pt + d_out)
        ring_cols.append([p_in, p_out])
    ob_ring = M.mesh_from_rows(name + "_Bezel", ring_cols, collection)
    ob_ring.data.materials.append(lib["logo_chrome"])
    M.mirror_y(ob_ring)
    M.finish(ob_ring, thickness=0.0022, bevel=0.0)
    made.append(ob_ring)

    # 2. Glowing white LED optical projector lens core
    core_cols = []
    for i in range(seg + 1):
        ang = 2.0 * math.pi * (i / float(seg))
        ca, sa = math.cos(ang), math.sin(ang)
        rx = hx * 0.66
        ry = hy * 0.66
        d_rim = t1 * (ca * rx) + t2 * (sa * ry)
        p_center = tuple(c_pt + nvec * 0.0014 + d_rim * 0.12)
        p_edge = tuple(c_pt + nvec * 0.0008 + d_rim)
        core_cols.append([p_center, p_edge])
    ob_core = M.mesh_from_rows(name + "_Core", core_cols, collection)
    ob_core.data.materials.append(lib["led_white"])
    M.mirror_y(ob_core)
    M.finish(ob_core, thickness=0.0012, bevel=0.0)
    made.append(ob_core)

    return made


def build_headlamps(collection, lib):
    """Structured Dragon Face 3.0 LED headlamps:
    1. Main angular cluster with sharper upper crease:
       - Dark gloss housing backing & perimeter gasket seal
       - Sharper upper crease DRL light blade + satin chrome brow strip along LAMP_UPPER
       - 3 defined inner projector graphics (twin main beam projectors + inner high-beam projector)
         separated by crisp angled divider fins
       - Smoked clear outer polycarbonate lens
    2. Pronounced outer hook DRL extension:
       - Wraps around outer fender corner and hooks sharply inward along the bumper crease
       - Continuous glowing white LED hook blade + internal segmented chrome/LED optics
    """
    made = []
    PLACER.reset()
    NS, NK = 64, 8
    lo = geom.polyline(LAMP_LOWER, NS)
    up = geom.polyline(LAMP_UPPER, NS)
    out = geom.away_from((1.95, 0.46, 0.66))

    def _crown(k, extra=0.0):
        return 0.0032 + 0.0014 * math.sin(math.pi * max(0.0, min(1.0, k))) + extra

    # 1. Dark smoked headlamp lens & housing base
    made.append(lamps.lens(
        "Seal_Headlamp_Lens", lo, up, _lamp_place, collection, lib["lamp_clear"],
        NK, lambda k, nk: _crown(k / float(nk)), out,
        thickness=0.0022, bevel=(0.0010, 2, 30)
    ))

    # 2. Outer seal gasket band
    made += lamps.seals(
        "Seal_Headlamp_Seal", lo, up, _lamp_place, collection, lib["grille"], out,
        width=0.0045, d=0.0012
    )

    # 3. Sharper upper crease DRL brow & chrome accent blade along upper contour (proud of smoked lens so clearly visible)
    made.append(lamps.band_between(
        "Seal_Headlamp_Upper_Crease", lo, up, range(1, int(NS * 0.98)),
        [0.82, 0.90, 0.97],
        _lamp_place, lambda k: _crown(k, 0.0010), collection, lib["led_white"], out
    ))
    made.append(lamps.band_between(
        "Seal_Headlamp_Brow_Chrome", lo, up, range(2, int(NS * 0.96)),
        [0.72, 0.80],
        _lamp_place, lambda k: _crown(k, 0.0008), collection, lib["logo_chrome"], out
    ))

    # 4. Lower contour DRL signature guide feeding into the outer hook
    made.append(lamps.band_between(
        "Seal_Headlamp_DRL", lo, up, range(2, int(NS * 0.96)),
        [0.05, 0.13, 0.21],
        _lamp_place, lambda k: _crown(k, 0.0010), collection, lib["led_white"], out
    ))

    # 5. Defined inner projector graphics (3 structured Dragon Face 3.0 projector modules + divider fins)
    projector_specs = [
        (0.42, 0.658, (0.042, 0.028)),
        (0.55, 0.692, (0.048, 0.032)),
        (0.68, 0.728, (0.050, 0.034)),
    ]
    for idx, (yy, zz, p_size) in enumerate(projector_specs):
        best = lamps.station_nearest_y(lo, up, yy)
        zl, zu = lo[best][2], up[best][2]
        k = max(0.32, min(0.68, (zz - zl) / max(1e-4, zu - zl)))
        c, n = _lamp_place(geom.lerp(lo[best], up[best], k), _crown(k, 0.0014))
        made += _projector_unit(
            f"Seal_Headlamp_Projector_{idx}", c, n, p_size, collection, lib
        )

    # Angled chrome divider fins between the projector units
    for f_idx, yy_div in enumerate((0.36, 0.485, 0.615, 0.745)):
        best = lamps.station_nearest_y(lo, up, yy_div)
        p_bot, _ = _lamp_place(geom.lerp(lo[best], up[best], 0.25), _crown(0.25, 0.0010))
        p_top, _ = _lamp_place(geom.lerp(lo[best], up[best], 0.72), _crown(0.72, 0.0010))
        div_cols = [
            [(p_bot[0], p_bot[1] - 0.0022, p_bot[2]), (p_top[0], p_top[1] - 0.0022, p_top[2])],
            [(p_bot[0], p_bot[1] + 0.0022, p_bot[2]), (p_top[0], p_top[1] + 0.0022, p_top[2])],
        ]
        div_ob = M.mesh_from_rows(f"Seal_Headlamp_Divider_{f_idx}", div_cols, collection)
        div_ob.data.materials.append(lib["trim_chrome"])
        M.mirror_y(div_ob)
        M.finish(div_ob, thickness=0.0015, bevel=0.0)
        made.append(div_ob)

    # 7. Pronounced Outer Hook DRL Extension (Dragon Face 3.0 C-hook wrapping downward & inward)
    lo_hook = geom.polyline(HOOK_LOWER, 40)
    up_hook = geom.polyline(HOOK_UPPER, 40)
    out_hook = geom.away_from((1.95, 0.46, 0.58))

    made.append(lamps.lens(
        "Seal_Hook_DRL_Housing", lo_hook, up_hook, _lamp_place, collection,
        lib["black_gloss"], 4, lambda k, nk: 0.0018, out_hook,
        thickness=0.0022, bevel=0.0
    ))

    # Continuous glowing white LED blade inside the pronounced outer hook
    made.append(lamps.band_between(
        "Seal_Hook_DRL_Blade", lo_hook, up_hook, range(len(lo_hook)),
        [0.22, 0.50, 0.78], _lamp_place, lambda k: 0.0038, collection,
        lib["led_white"], out_hook
    ))

    # Crisp chrome accent trim framing the lower edge of the hook
    made.append(lamps.band_between(
        "Seal_Hook_Chrome_Trim", lo_hook, up_hook, range(2, len(lo_hook) - 2),
        [0.05, 0.18], _lamp_place, lambda k: 0.0034, collection,
        lib["logo_chrome"], out_hook
    ))

    return made


# --------------------------------------------------- BYD emblem & roof LiDAR
def _font(fn):
    import os
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_emblem_and_lidar(collection, lib):
    """1. Polished chrome 'BYD' wordmark emblem centered on the upper front nose at z=0.640.
    2. Roof-mounted God's Eye (天神之眼) LiDAR pod above the windscreen header at x=0.210.
    """
    made = []
    inter = _font("Inter.woff2")
    p_emb, n_emb = _face(0.0, 0.640, d=0.0025)
    emb = M.text_mesh("Seal_Emblem_Front", "BYD", 0.032, collection, lib["logo_chrome"],
                      extrude=0.0018, font=inter, resolution=4)
    P.on_surface(emb, p_emb, n_emb)
    made.append(emb)

    # Watchtower roof LiDAR pod (God's Eye DiPilot 300)
    x_lidar = 0.210
    z_lidar = S.Z_ROOF(x_lidar)
    c_pod = (x_lidar, 0.0, z_lidar + 0.018)
    pod = _box("Seal_Roof_LiDAR_Pod", c_pod, (0.090, 0.125, 0.032), collection, lib["paint"])
    made.append(pod)

    c_win = (x_lidar + 0.040, 0.0, z_lidar + 0.020)
    win = _box("Seal_Roof_LiDAR_Glass", c_win, (0.012, 0.105, 0.022), collection, lib["black_gloss"])
    made.append(win)

    return made


def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_emblem_and_lidar(collection, lib)
    return made
