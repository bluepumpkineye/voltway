"""BYD Seal EV side details:
- Continuous 'Ocean Wave' upper character line flowing from front fender camera through
  the door panels to the rear haunch
- Front fender camera arrow badge (gloss black with chrome blade)
- Sculpted Ocean rising lower-door Z-crease with shadow undercut
- Gloss-black aerodynamic rocker panels with satin silver blade
- Sleek high-gloss black DLO window surround trim (upper arch + beltline)
- Distinctive C-pillar water-drop textured garnish on rear quarter glass apex
- Door-mounted aerodynamic mirrors with 360-degree camera pods
- 4 flush pop-out door handles with recessed outline rings
- Rear-right quarter charge flap outline and roof shark-fin antenna

Calibrated directly against Autohome Series 6394 studio side references.
"""
import math
import bpy

import seal_surface as S
import seal_nose as N
import seal_panels as P
from carkit import geom
from carkit import mesh as M
from carkit.parts import fittings

BODY = N.BODY
proud = BODY.proud


def _box(name, c, size, collection, mat):
    x, y, z = c
    hx, hy, hz = (0.5 * t for t in size)
    v = [(x + sx * hx, y + sy * hy, z + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    ob = M.obj(name, v, f, collection, mat)
    M.orient(ob.data, lambda cc, c0=c: (cc[0] - c0[0], cc[1] - c0[1], cc[2] - c0[2]))
    return ob


# ------------------------------------------------------------------ mirrors
# Slim, aerodynamic blade-style side mirror housings
MIRROR_REAR = (0.585, 0.938, 0.948)
MIRROR_SIZE = (0.180, 0.106, 0.068)
MIRROR_ARM = (0.645, 0.878, 0.902)


def build_mirrors(collection, lib):
    made = fittings.mirror_cap(
        "Seal_Mirror", collection, lib, rear=MIRROR_REAR,
        size=MIRROR_SIZE, arm_base=MIRROR_ARM, proud=proud, arm_t=0.018,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"),
    )
    cx, cy, cz = MIRROR_REAR[0] + 0.028, MIRROR_REAR[1] - 0.044, MIRROR_REAR[2] - 0.036
    pod = _box("Seal_Mirror_Cam_Pod", (cx, cy, cz), (0.018, 0.016, 0.010), collection, lib["black_gloss"])
    M.mirror_y(pod)
    made.append(pod)
    return made


# ------------------------------------------------------------------ handles
HANDLES = (("F", -0.04, 0.15, 0.805), ("R", -0.90, -0.70, 0.820))


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        handle = fittings.flush_handle(
            "Seal_Handle_" + nm, x0, x1, zc, proud, collection,
            lib["paint"], h=0.018, d=0.0012, y_ref=0.86,
        )
        made.append(handle)
        ring = fittings.outline_ring(
            "Seal_Handle_Rim_" + nm, x0 - 0.002, x1 + 0.002,
            zc - 0.020, zc + 0.020, 0.020, proud, collection,
            lib["black_gloss"], width=0.0012, d=0.0010, y_ref=0.86,
            mirror=True,
        )
        made.append(ring)
    return made


# -------------------------------- character line: single clean Ocean Wave line
def build_ocean_wave_and_fender(collection, lib):
    """1. Single clean 'Ocean Wave' character line running continuously from front fender
          (x = 1.380, z = 0.748) through both doors to the rear taillight tip (x = -2.020, z = 0.888).
       2. Sleek front fender side-camera blade garnish at the leading end of the character line.
    """
    made = []

    # 1. Single clean Ocean Wave character line from front fender through doors to rear taillight
    wave_pts = [
        ( 1.380, 0.748), ( 1.050, 0.766), ( 0.700, 0.784), ( 0.300, 0.802),
        (-0.110, 0.820), (-0.550, 0.838), (-1.000, 0.856), (-1.420, 0.872),
        (-1.750, 0.882), (-2.020, 0.888),
    ]
    wave_curve = S.Curve(sorted(wave_pts, key=lambda p: p[0]), mode="pchip")
    nw = 76
    w_cols = []
    for i in range(nw + 1):
        u = i / float(nw)
        x = -2.020 + (1.380 - (-2.020)) * u
        zc = wave_curve(x)
        taper = math.sin(math.pi * u) ** 0.45
        p_lo, _ = BODY.side_point(x, zc - 0.0055)
        p_mid, _ = BODY.side_point(x, zc)
        p_hi, _ = BODY.side_point(x, zc + 0.0055)
        w_cols.append([
            (p_lo[0],  p_lo[1]  + 0.0006, p_lo[2]),
            (p_mid[0], p_mid[1] + 0.0028 * taper + 0.0006, p_mid[2]),
            (p_hi[0],  p_hi[1]  + 0.0006, p_hi[2]),
        ])
    wave_ob = M.mesh_from_rows("Seal_Ocean_Wave_Line", w_cols, collection)
    M.orient(wave_ob.data, lambda c: (0.0, 1.0, 0.0))
    wave_ob.data.materials.append(lib["paint"])
    M.mirror_y(wave_ob)
    M.finish(wave_ob, thickness=0.0016, bevel=0.0)
    made.append(wave_ob)

    # 2. Front fender camera arrow badge integrated cleanly at the front fender origin of the line
    nf = 16
    f_cols = []
    c_cols = []
    for i in range(nf + 1):
        u = i / float(nf)
        x = 0.920 + (1.180 - 0.920) * u
        zc = wave_curve(x)
        p_lo, _ = BODY.side_point(x, zc - 0.008)
        p_hi, _ = BODY.side_point(x, zc + 0.008)
        f_cols.append([(p_lo[0], p_lo[1] + 0.0025, p_lo[2]), (p_hi[0], p_hi[1] + 0.0025, p_hi[2])])
        p_c0, _ = BODY.side_point(x, zc - 0.003)
        p_c1, _ = BODY.side_point(x, zc + 0.003)
        c_cols.append([(p_c0[0], p_c0[1] + 0.0040, p_c0[2]), (p_c1[0], p_c1[1] + 0.0040, p_c1[2])])

    f_base = M.mesh_from_rows("Seal_Fender_Cam_Base", f_cols, collection)
    f_base.data.materials.append(lib["black_gloss"])
    M.mirror_y(f_base)
    M.finish(f_base, thickness=0.0018, bevel=0.0)
    made.append(f_base)

    f_chr = M.mesh_from_rows("Seal_Fender_Cam_Chrome", c_cols, collection)
    f_chr.data.materials.append(lib["trim_chrome"])
    M.mirror_y(f_chr)
    M.finish(f_chr, thickness=0.0016, bevel=0.0)
    made.append(f_chr)

    return made


# --------------------------------------------------------------- rockers
def build_rockers(collection, lib):
    made = []
    nx = 36
    r_cols = []
    b_cols = []
    for i in range(nx + 1):
        x = -0.92 + (1.02 - (-0.92)) * (i / float(nx))
        p_lo, _ = BODY.side_point(x, 0.156)
        p_up, _ = BODY.side_point(x, 0.228)
        r_cols.append([(p_lo[0], p_lo[1] + 0.003, p_lo[2]), (p_up[0], p_up[1] + 0.003, p_up[2])])

        p_b0, _ = BODY.side_point(x, 0.185)
        p_b1, _ = BODY.side_point(x, 0.198)
        b_cols.append([(p_b0[0], p_b0[1] + 0.005, p_b0[2]), (p_b1[0], p_b1[1] + 0.005, p_b1[2])])

    rocker = M.mesh_from_rows("Seal_Rocker_Panel", r_cols, collection)
    rocker.data.materials.append(lib["black_trim"])
    M.mirror_y(rocker)
    M.finish(rocker, thickness=0.003, bevel=0.0)
    made.append(rocker)

    blade = M.mesh_from_rows("Seal_Rocker_Blade", b_cols, collection)
    blade.data.materials.append(lib["trim_chrome"])
    M.mirror_y(blade)
    M.finish(blade, thickness=0.002, bevel=0.0)
    made.append(blade)

    return made


# ----------------------------------------------------------- window trim
def build_window_trim(collection, lib):
    """High-gloss black DLO window surround and C-pillar water-drop textured trim
    matching BYD Seal AWD Performance trim.
    """
    made = []
    nw = 56
    arch_cols = []
    belt_cols = []
    for i in range(nw + 1):
        x = P.X_QTR_R + (P.X_COWL - 0.03 - P.X_QTR_R) * (i / float(nw))
        v_top = P.V_GLASS_TOP(x)
        y_t, z_t = S.BODY.section_v(x, v_top)
        arch_cols.append([(x, y_t + 0.0025, z_t - 0.004), (x, y_t + 0.0025, z_t + 0.010)])

        v_bot = P.V_QTR_LOW(x) if x < P.X_QTR_F else P.V_BELT
        y_b, z_b = S.BODY.section_v(x, v_bot)
        belt_cols.append([(x, y_b + 0.0025, z_b - 0.006), (x, y_b + 0.0025, z_b + 0.006)])

    arch = M.mesh_from_rows("Seal_Window_Arch_Trim", arch_cols, collection)
    arch.data.materials.append(lib["black_gloss"])
    M.mirror_y(arch)
    M.finish(arch, thickness=0.002, bevel=0.0)
    made.append(arch)

    belt = M.mesh_from_rows("Seal_Window_Belt_Trim", belt_cols, collection)
    belt.data.materials.append(lib["black_gloss"])
    M.mirror_y(belt)
    M.finish(belt, thickness=0.002, bevel=0.0)
    made.append(belt)

    # BYD Seal distinctive C-pillar water-drop pattern garnish on rear quarter glass apex
    qtr_cols = []
    for i in range(12):
        x = P.X_QTR_R + (P.X_QTR_F - P.X_QTR_R) * (i / 11.0) * 0.45
        v_bot = P.V_QTR_LOW(x)
        y_b, z_b = S.BODY.section_v(x, v_bot)
        qtr_cols.append([(x, y_b + 0.0035, z_b), (x, y_b + 0.0035, z_b + 0.035)])
    qtr_trim = M.mesh_from_rows("Seal_CPillar_Waterdrop_Trim", qtr_cols, collection)
    qtr_trim.data.materials.append(lib["black_gloss"])
    M.mirror_y(qtr_trim)
    M.finish(qtr_trim, thickness=0.0018, bevel=0.0)
    made.append(qtr_trim)

    return made


# ------------------------------------------- charge door & roof shark fin
def build_charge_and_antenna(collection, lib):
    made = []
    # Rear quarter charge flap outline (x -1.72..-1.50, z 0.75..0.865)
    made.append(
        fittings.outline_ring(
            "Seal_ChargeDoor_Line", -1.72, -1.50, 0.750, 0.865, 0.024,
            proud, collection, lib["shadow"],
        )
    )
    # Roof shark-fin antenna at rear of roof header (x = -1.05, y = 0)
    x_fin = -1.05
    z_roof = S.Z_ROOF(x_fin)
    fin = _box("Seal_Shark_Fin", (x_fin, 0.0, z_roof + 0.018), (0.105, 0.024, 0.038), collection, lib["black_gloss"])
    made.append(fin)
    return made


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_ocean_wave_and_fender(collection, lib)
    made += build_rockers(collection, lib)
    made += build_window_trim(collection, lib)
    made += build_charge_and_antenna(collection, lib)
    return made
