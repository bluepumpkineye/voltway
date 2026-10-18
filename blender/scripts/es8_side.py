"""Nio ES8 side details: two-tone mirrors with ADAS camera pods, flush door handles,
front-fender vertical wide-angle side-LiDAR & camera blade (双侧广角激光雷达),
gloss-black wheel arch cladding, gloss-black rocker skirts with horizontal satin-chrome
door spear, flush roof luggage rails, and left-rear power-swap/charging flap.
"""
import math

import es8_surface as S
import es8_nose as N
import es8_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.parts import aero, fittings, lamps

BODY = N.BODY
proud = BODY.proud

# ------------------------------------------------------------------ mirrors
MIRROR_REAR = (0.815, 0.965, 1.155)
MIRROR_SIZE = (0.180, 0.155, 0.138)
MIRROR_ARM = (0.905, 0.905, 1.088)


def build_mirrors(collection, lib):
    made = fittings.mirror_cap(
        "ES8_Mirror", collection, lib,
        rear=MIRROR_REAR, size=MIRROR_SIZE, arm_base=MIRROR_ARM,
        proud=proud, arm_t=0.032,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"),
    )
    # Lower ADAS surround-view camera pod under mirror arm
    x0, x1, z0, z1 = 0.835, 1.005, 1.022, 1.082
    cx, cy = 0.5 * (x0 + x1), 0.925
    rows = []
    for (x, dz) in ((x1, 0.0), (0.5 * (x0 + x1), 0.012), (x0, 0.004)):
        rows.append([(x, cy + dy, z0 + dz + (z1 - z0) * f)
                     for dy, f in ((-0.058, 0.45), (-0.038, 0.0), (0.038, 0.0), (0.058, 0.45))])
    pod = M.grid("ES8_Mirror_Pod", rows, collection, lib["black_gloss"],
                 geom.away_from((cx, 0.82, 1.08)))
    M.solidify(pod, 0.012)
    M.mirror_y(pod)
    made.append(pod)
    made += lamps.projector("ES8_Mirror_Cam", (cx + 0.018, cy, z0 + 0.008),
                            (0.0, 0.0, -1.0), 0.011, collection, lib)
    return made


# ------------------------------------------------------------------ handles
HANDLES = (
    ("F",  0.110,  0.340, 0.995),
    ("R", -0.960, -0.730, 1.005),
)


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        made.append(fittings.flush_handle(
            "ES8_Handle_" + nm, x0, x1, zc, proud, collection,
            lib["paint"], h=0.019, d=0.0014, y_ref=0.92,
        ))
        made.append(fittings.outline_ring(
            "ES8_Handle_Rim_" + nm, x0 - 0.002, x1 + 0.002,
            zc - 0.022, zc + 0.022, 0.022, proud, collection,
            lib["chrome"], width=0.0014, d=0.0012, y_ref=0.92, mirror=True,
        ))
    return made


# ----------------------------------------- front fender side-LiDAR & camera blade
# Vertical gloss-black sensor blade on the trailing edge of the front fender ahead of the front door
GILL_UP = [(1.145, 0.945), (1.115, 0.948), (1.082, 0.945)]
GILL_LO = [(1.115, 0.695), (1.085, 0.692), (1.055, 0.695)]


def build_fender_lidar(collection, lib):
    made = [fittings.side_patch(
        "ES8_Gill", GILL_LO, GILL_UP, BODY.side_point, collection,
        lib["black_gloss"], d=0.0028, n=24, nk=5, y_ref=0.92,
        outward=(0.0, 1.0, 0.0),
    )]
    # Wide-angle solid-state side LiDAR window + ADAS rear-facing camera
    p, n = BODY.side_point(1.105, 0.865)
    c = (p[0] + n[0] * 0.005, p[1] + n[1] * 0.005, p[2] + n[2] * 0.005)
    made += lamps.projector("ES8_Gill_Cam", c, n, 0.013, collection, lib)
    return made


# ------------------------------------------------------------ charge flap
def build_charge_door(collection, lib):
    return [fittings.outline_ring(
        "ES8_Charge_Line", -1.960, -1.710, 0.885, 1.035, 0.032,
        proud, collection, lib["shadow"], y_ref=0.90,
    )]


# ----------------------------------------------------------- arch cladding
CLAD = (
    ("F", S.FRONT_AXLE, 0.072, 0.250, 0.996, 0.982),
    ("R", S.REAR_AXLE,  0.074, 0.250, 0.998, 0.985),
)


def _on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _arch_path(axle, r, z_bot, n_arc=48, n_leg=6):
    zc = S.WHEEL_R
    pts = [(axle + r, z_bot + (zc - z_bot) * i / float(n_leg)) for i in range(n_leg)]
    pts += [(axle + r * math.cos(math.pi * i / n_arc), zc + r * math.sin(math.pi * i / n_arc))
            for i in range(n_arc + 1)]
    pts += [(axle - r, zc - (zc - z_bot) * i / float(n_leg)) for i in range(1, n_leg + 1)]
    return pts


def build_cladding(collection, lib):
    made = []
    for tag, axle, width, z_bot, y_leg, y_top in CLAD:
        r_out = S.ARCH_R + 0.012
        r_in = S.ARCH_R - width
        outer = _arch_path(axle, r_out, z_bot)
        inner = _arch_path(axle, r_in, z_bot)
        rows = []
        m = len(outer)
        for i in range(m):
            s = i / float(m - 1)
            po, _ = _on_flank(outer[i][0], outer[i][1], 0.0025)
            pb, _ = _on_flank(inner[i][0], inner[i][1], 0.0)
            k = (1.0 - math.sin(math.pi * s)) ** 1.3
            yt = y_top + (y_leg - y_top) * k
            pi = (pb[0], max(pb[1] + 0.015, yt), pb[2])
            lip = (pi[0], pi[1] - 0.048, pi[2])
            rows.append([po, pi, lip])
        ob = M.grid("ES8_Clad_" + tag, rows, collection, lib["black_gloss"],
                    geom.const((0.0, 1.0, 0.0)))
        M.solidify(ob, 0.003)
        M.mirror_y(ob)
        made.append(ob)
    return made


# ------------------------------------------------------------------ sills
X_SKIRT_F = S.FRONT_AXLE - S.ARCH_R + 0.008
X_SKIRT_R = S.REAR_AXLE + S.ARCH_R - 0.008


def build_sills(collection, lib):
    made = [aero.side_skirt(
        "ES8_Skirt", collection, lib, proud,
        lambda x: S.Y_ROCKER(x) + 0.018, X_SKIRT_R, X_SKIRT_F,
        0.200, 0.345, nx=64, nz=6, d=0.006, mat="black_gloss",
    )]
    # Horizontal satin-chrome lower door spear across the rocker skirt
    made.append(fittings.surface_band(
        "ES8_Skirt_Line",
        lambda k: X_SKIRT_R + 0.03,
        lambda k: X_SKIRT_F - 0.03,
        lambda x: 0.278 + (1.05 - x) * 0.008,
        lambda x: 0.298 + (1.05 - x) * 0.008,
        lambda p, d: proud(p, 0.0095),
        collection, lib["trim_silver"], 60, nk=3, y_ref=0.92,
    ))
    return made


# ------------------------------------------------------------------ roof rails
def build_roof_rails(collection, lib):
    made = []
    # Flush low-profile roof luggage rails along the roof cantrail
    x0, x1 = -1.720, 0.180
    nx = 32
    rows = []
    for i in range(nx + 1):
        t = i / float(nx)
        x = x0 + (x1 - x0) * t
        taper = math.sin(math.pi * t) ** 0.35
        y_c = S.Y_ROOF(x) - 0.042
        p_base, _ = BODY.top_point(x, y_c, 0.0)
        z_b = p_base[2]
        h = 0.018 * taper
        w = 0.016 * (0.65 + 0.35 * taper)
        rows.append([
            (x, y_c + w, z_b - 0.002),
            (x, y_c + w * 0.85, z_b + h),
            (x, y_c - w * 0.85, z_b + h),
            (x, y_c - w, z_b - 0.002),
        ])
    rail = M.grid("ES8_RoofRail", rows, collection, lib["black_gloss"],
                  geom.const((0.0, 0.0, 1.0)))
    M.mirror_y(rail)
    M.finish(rail, thickness=0.002, bevel=0.001)
    made.append(rail)
    return made


def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_fender_lidar(collection, lib)
    made += build_charge_door(collection, lib)
    made += build_cladding(collection, lib)
    made += build_sills(collection, lib)
    made += build_roof_rails(collection, lib)
    return made
