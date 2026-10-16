"""Denza Z9 side details: door-mounted aerodynamic mirrors, 4 flush pop-out
door handles, front fender camera garnish blade, sculpted Z-line lower door
channel accent, gloss-black rocker panels with chrome blade, full chrome window
surround (upper arch + beltline), rear quarter charge flap, and roof shark-fin
antenna.

Calibrated directly against Autohome studio side reference c1_0040.jpg and
c1_0044.jpg.
"""
import math
import bpy

import z9_surface as S
import z9_nose as N
import z9_panels as P
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
MIRROR_REAR = (0.695, 1.015, 0.995)
MIRROR_SIZE = (0.215, 0.130, 0.105)
MIRROR_ARM = (0.755, 0.945, 0.935)


def build_mirrors(collection, lib):
    made = fittings.mirror_cap(
        "Z9_Mirror", collection, lib, rear=MIRROR_REAR,
        size=MIRROR_SIZE, arm_base=MIRROR_ARM, proud=proud, arm_t=0.028,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"),
    )
    cx, cy, cz = MIRROR_REAR[0] + 0.035, MIRROR_REAR[1] - 0.055, MIRROR_REAR[2] - 0.060
    pod = _box("Z9_Mirror_Cam_Pod", (cx, cy, cz), (0.024, 0.022, 0.014), collection, lib["black_gloss"])
    M.mirror_y(pod)
    made.append(pod)
    return made


# ------------------------------------------------------------------ handles
HANDLES = (("F", -0.05, 0.17, 0.835), ("R", -1.06, -0.84, 0.852))


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        handle = fittings.flush_handle(
            "Z9_Handle_" + nm, x0, x1, zc, proud, collection,
            lib["paint"], h=0.019, d=0.0012, y_ref=0.92,
        )
        made.append(handle)
        ring = fittings.outline_ring(
            "Z9_Handle_Rim_" + nm, x0 - 0.002, x1 + 0.002,
            zc - 0.022, zc + 0.022, 0.022, proud, collection,
            lib["black_gloss"], width=0.0012, d=0.0010, y_ref=0.92,
            mirror=True,
        )
        made.append(ring)
    return made


# ----------------------------------------- fender camera & Z-line door trim
def build_fender_and_z_line(collection, lib):
    """Horizontal front fender camera garnish blade at x 0.985..1.250, z ~ 0.655
    (c1_0040.jpg), plus the sculpted diagonal-to-horizontal Z-line accent on
    the doors from (x=0.985, z=0.652) -> (x=0.38, z=0.355) -> (x=-1.00, z=0.365).
    """
    made = []
    # 1. Front fender camera garnish blade (chrome + gloss black, at beltline level c1_0004.jpg)
    nf = 16
    f_cols = []
    c_cols = []
    for i in range(nf + 1):
        u = i / float(nf)
        x = 1.040 + (1.340 - 1.040) * u
        p_lo, _ = BODY.side_point(x, 0.722)
        p_hi, _ = BODY.side_point(x, 0.744)
        f_cols.append([(p_lo[0], p_lo[1] + 0.003, p_lo[2]), (p_hi[0], p_hi[1] + 0.003, p_hi[2])])
        p_c0, _ = BODY.side_point(x, 0.728)
        p_c1, _ = BODY.side_point(x, 0.738)
        c_cols.append([(p_c0[0], p_c0[1] + 0.0048, p_c0[2]), (p_c1[0], p_c1[1] + 0.0048, p_c1[2])])

    f_base = M.mesh_from_rows("Z9_Fender_Cam_Base", f_cols, collection)
    f_base.data.materials.append(lib["black_gloss"])
    M.mirror_y(f_base)
    M.finish(f_base, thickness=0.002, bevel=0.0)
    made.append(f_base)

    f_chr = M.mesh_from_rows("Z9_Fender_Cam_Chrome", c_cols, collection)
    f_chr.data.materials.append(lib["trim_chrome"])
    M.mirror_y(f_chr)
    M.finish(f_chr, thickness=0.002, bevel=0.0)
    made.append(f_chr)

    # 2. Diagonal-to-horizontal Z-line door sculpture accent (c1_0040.jpg, c1_0044.jpg)
    # Starts at fender camera blade (x 1.04, z 0.72), sweeps down across front door to sill,
    # runs horizontal, and curves up into rear door
    z_pts = [
        (1.040, 0.722), (0.850, 0.605), (0.620, 0.475), (0.350, 0.365),
        (0.100, 0.315), (-0.300, 0.305), (-0.700, 0.312), (-1.020, 0.365),
    ]
    z_curve = S.Curve(sorted(z_pts, key=lambda p: p[0]), mode="pchip")
    nz = 40
    z_cols = []
    for i in range(nz + 1):
        x = -1.020 + (1.040 - (-1.020)) * (i / float(nz))
        zc = z_curve(x)
        p0, _ = BODY.side_point(x, zc - 0.008)
        p1, _ = BODY.side_point(x, zc + 0.008)
        z_cols.append([(p0[0], p0[1] + 0.0035, p0[2]), (p1[0], p1[1] + 0.0035, p1[2])])
    z_trim = M.mesh_from_rows("Z9_Door_Z_Crease", z_cols, collection)
    z_trim.data.materials.append(lib["paint"])
    M.mirror_y(z_trim)
    M.finish(z_trim, thickness=0.003, bevel=0.0)
    made.append(z_trim)

    # Crisp shadow groove along the Z-line center
    z_sh_cols = []
    for i in range(nz + 1):
        x = -1.020 + (1.040 - (-1.020)) * (i / float(nz))
        zc = z_curve(x)
        p0, _ = BODY.side_point(x, zc - 0.002)
        p1, _ = BODY.side_point(x, zc + 0.002)
        z_sh_cols.append([(p0[0], p0[1] + 0.0045, p0[2]), (p1[0], p1[1] + 0.0045, p1[2])])
    z_sh = M.mesh_from_rows("Z9_Door_Z_Shadow", z_sh_cols, collection)
    z_sh.data.materials.append(lib["shadow"])
    M.mirror_y(z_sh)
    M.finish(z_sh, thickness=0.0015, bevel=0.0)
    made.append(z_sh)

    return made


# --------------------------------------------------------------- rockers
def build_rockers(collection, lib):
    made = []
    nx = 36
    r_cols = []
    b_cols = []
    for i in range(nx + 1):
        x = -1.02 + (1.14 - (-1.02)) * (i / float(nx))
        p_lo, _ = BODY.side_point(x, 0.165)
        p_up, _ = BODY.side_point(x, 0.245)
        r_cols.append([(p_lo[0], p_lo[1] + 0.003, p_lo[2]), (p_up[0], p_up[1] + 0.003, p_up[2])])

        p_b0, _ = BODY.side_point(x, 0.195)
        p_b1, _ = BODY.side_point(x, 0.208)
        b_cols.append([(p_b0[0], p_b0[1] + 0.005, p_b0[2]), (p_b1[0], p_b1[1] + 0.005, p_b1[2])])

    rocker = M.mesh_from_rows("Z9_Rocker_Panel", r_cols, collection)
    rocker.data.materials.append(lib["black_gloss"])
    M.mirror_y(rocker)
    M.finish(rocker, thickness=0.003, bevel=0.0)
    made.append(rocker)

    blade = M.mesh_from_rows("Z9_Rocker_Blade", b_cols, collection)
    blade.data.materials.append(lib["trim_chrome"])
    M.mirror_y(blade)
    M.finish(blade, thickness=0.002, bevel=0.0)
    made.append(blade)

    return made


# ----------------------------------------------------------- window trim
def build_window_trim(collection, lib):
    """Full bright anodized chrome DLO surround (upper window arch + lower beltline)
    as seen on Denza Z9 in c1_0040.jpg and c1_0044.jpg.
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

    arch = M.mesh_from_rows("Z9_Window_Arch_Chrome", arch_cols, collection)
    arch.data.materials.append(lib["trim_chrome"])
    M.mirror_y(arch)
    M.finish(arch, thickness=0.002, bevel=0.0)
    made.append(arch)

    belt = M.mesh_from_rows("Z9_Window_Belt_Chrome", belt_cols, collection)
    belt.data.materials.append(lib["trim_chrome"])
    M.mirror_y(belt)
    M.finish(belt, thickness=0.002, bevel=0.0)
    made.append(belt)

    return made


# ------------------------------------------- charge door & roof shark fin
def build_charge_and_antenna(collection, lib):
    made = []
    # Rear quarter charge flap outline (c1_0040.jpg: x -1.88..-1.62, z 0.78..0.90)
    made.append(
        fittings.outline_ring(
            "Z9_ChargeDoor_Line", -1.88, -1.62, 0.785, 0.905, 0.026,
            proud, collection, lib["shadow"],
        )
    )
    # Sleek roof shark-fin antenna at rear of roof header (x = -1.16, y = 0, c1_0040.jpg)
    x_fin = -1.16
    z_roof = S.Z_ROOF(x_fin)
    fin = _box("Z9_Shark_Fin", (x_fin, 0.0, z_roof + 0.018), (0.115, 0.026, 0.042), collection, lib["black_gloss"])
    made.append(fin)
    return made


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_fender_and_z_line(collection, lib)
    made += build_rockers(collection, lib)
    made += build_window_trim(collection, lib)
    made += build_charge_and_antenna(collection, lib)
    return made
