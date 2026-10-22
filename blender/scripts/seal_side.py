"""BYD Seal side details, read from the side photographs (seal_cam: WHITE c1_0506 for the lines and
trim, BLUE c1_0513 with its contrast stretched for the surface):

- ONE Ocean Wave character line: a sharp ridge that runs from the fender gill along the doors
  (z 0.75 at the gill, 0.862 over the door split) and fades over the rear haunch toward the lamp
- the fender gill: a black arrow behind the front wheel
- slim aerodynamic mirrors, flush black pull handles
- the black sill with its aero fins
- thin black window frames; the quarter glass's perforated vent (hex-pitched white dots)
- the charge flap's shut line on the rear quarter
"""
import math
import bpy

import seal_surface as S
import seal_nose as N
import seal_panels as P
import seal_cam as CAM
from carkit import geom
from carkit import mesh as M
from carkit.parts import fittings

BODY = N.BODY
proud = BODY.proud


def _xz(px, y=CAM.Y_SKIN):
    return [CAM.side_xz(u, v, y, "white") for (u, v) in px]


# ------------------------------------------------------------------ mirrors
# the head spans x 0.58-0.79 and z 0.98-1.13 in the side photograph, its outer edge at y 1.035 in the
# front one; made slimmer and more blade-like than the egg the photograph shows, as asked
MIRROR_REAR = (0.600, 0.968, 1.060)
MIRROR_SIZE = (0.190, 0.125, 0.104)
MIRROR_ARM = (0.800, 0.860, 0.985)


def build_mirrors(collection, lib):
    return fittings.mirror_cap(
        "Seal_Mirror", collection, lib, rear=MIRROR_REAR,
        size=MIRROR_SIZE, arm_base=MIRROR_ARM, proud=proud, arm_t=0.014, nose=0.16, drop=0.34,
        mats=("paint", "mirror_glass", "black_gloss", "black_gloss"),
    )


# ------------------------------------------------------------------ handles
# front door x -0.106..0.130 at z 0.870, rear door x -1.135..-0.906 at z 0.918 (c1_0506)
HANDLES = (("F", -0.106, 0.130, 0.870), ("R", -1.135, -0.906, 0.918))


def build_handles(collection, lib):
    made = []
    for nm, x0, x1, zc in HANDLES:
        handle = fittings.flush_handle(
            "Seal_Handle_" + nm, x0, x1, zc, proud, collection,
            lib["black_gloss"], h=0.014, d=0.0022, y_ref=0.88,
        )
        made.append(handle)
        ring = fittings.outline_ring(
            "Seal_Handle_Rim_" + nm, x0 - 0.004, x1 + 0.004,
            zc - 0.026, zc + 0.020, 0.018, proud, collection,
            lib["shadow"], width=0.0012, d=0.0008, y_ref=0.88, mirror=True,
        )
        made.append(ring)
    return made


# ------------------------------------------------------------ fender gill
def _patch(name, pts_xz, d, collection, mat):
    """A polygon laid on the flank (analytic side_point), d proud, mirrored."""
    verts = []
    for (x, z) in pts_xz:
        p, n = BODY.side_point(x, z)
        verts.append((p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d))
    ob = M.obj(name, verts, [list(range(len(verts)))], collection, mat, smooth=False)
    M.orient(ob.data, geom.const((0.0, 1.0, 0.0)))
    M.mirror_y(ob)
    return ob


def build_gill(collection, lib):
    """The black arrow behind the front wheel (c1_0506: x 1.0-1.15, z 0.63-0.80): an upper wedge
    and a lower one, split by a thin diagonal of body colour."""
    made = []
    upper = _xz([(1150, 1722), (1262, 1724), (1214, 1790), (1186, 1768), (1150, 1772)])
    lower = _xz([(1196, 1802), (1262, 1838), (1150, 1838), (1150, 1796)])
    made.append(_patch("Seal_Gill_Upper", upper, 0.0020, collection, lib["black_trim"]))
    made.append(_patch("Seal_Gill_Lower", lower, 0.0020, collection, lib["black_trim"]))
    return made


# ---------------------------------------------------- the Ocean Wave line
# crest of the door crease, x -> z. The line is the hip (S.Z_HIP) over the doors and fades over the
# rear haunch toward the lamp's tip (x -1.82, z 0.935)
WAVE_PTS = [(1.000, 0.748), (0.550, 0.790), (0.100, 0.830), (-0.300, 0.860), (-0.600, 0.862),
            (-1.000, 0.835), (-1.200, 0.800), (-1.500, 0.850), (-1.820, 0.930)]


def _amp(x):
    """Ridge height 0..1: grows from the gill, full across the doors, fades over the haunch."""
    a = min(1.0, max(0.0, (1.0 - x) / 0.25 + 0.0))
    b = 1.0 if x > -1.15 else max(0.0, 1.0 - (-1.15 - x) / 0.66)
    return min(a if x > 0.75 else 1.0, b)


def build_ocean_wave(collection, lib):
    made = []
    wave = S.Curve(sorted(WAVE_PTS), mode="pchip")
    x0, x1 = -1.82, 1.00
    nw = 90
    cols = []
    for i in range(nw + 1):
        x = x0 + (x1 - x0) * i / float(nw)
        zc = wave(x)
        amp = _amp(x)
        p_lo, _ = BODY.side_point(x, zc - 0.0070)
        p_mid, _ = BODY.side_point(x, zc)
        p_hi, _ = BODY.side_point(x, zc + 0.0070)
        cols.append([
            (p_lo[0], p_lo[1] + 0.0005, p_lo[2]),
            (p_mid[0], p_mid[1] + 0.0030 * amp + 0.0005, p_mid[2]),
            (p_hi[0], p_hi[1] + 0.0005, p_hi[2]),
        ])
    ob = M.mesh_from_rows("Seal_Ocean_Wave_Line", cols, collection)
    M.orient(ob.data, lambda c: (0.0, 1.0, 0.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=0.0016, bevel=0.0)
    made.append(ob)
    return made


# --------------------------------------------------------------- rockers
def build_rockers(collection, lib):
    """The black sill from behind the front wheel to the rear wheel's arch: its top edge is the doors'
    lower edge (z 0.25-0.29), its bottom z 0.185 (c1_0506); a thin bright line along its top."""
    made = []
    nx = 40
    r_cols, b_cols = [], []
    for i in range(nx + 1):
        x = -0.95 + (1.10 - (-0.95)) * (i / float(nx))
        p_lo, _ = BODY.side_point(x, 0.186)
        p_up, _ = BODY.side_point(x, 0.262)
        r_cols.append([(p_lo[0], p_lo[1] + 0.003, p_lo[2]), (p_up[0], p_up[1] + 0.003, p_up[2])])
        p_b0, _ = BODY.side_point(x, 0.258)
        p_b1, _ = BODY.side_point(x, 0.264)
        b_cols.append([(p_b0[0], p_b0[1] + 0.0042, p_b0[2]), (p_b1[0], p_b1[1] + 0.0042, p_b1[2])])
    rocker = M.mesh_from_rows("Seal_Rocker_Panel", r_cols, collection)
    rocker.data.materials.append(lib["black_trim"])
    M.mirror_y(rocker)
    M.finish(rocker, thickness=0.003, bevel=0.0)
    made.append(rocker)
    blade = M.mesh_from_rows("Seal_Rocker_Blade", b_cols, collection)
    blade.data.materials.append(lib["trim_chrome"])
    M.mirror_y(blade)
    M.finish(blade, thickness=0.0016, bevel=0.0)
    made.append(blade)
    return made


# ----------------------------------------------------------- window trim
def build_window_trim(collection, lib):
    """Thin gloss-black frames along the glass's top edge and the belt, and the quarter glass's
    perforated vent: ~30 white dots on a hex pitch inside the rear tip of the quarter window
    (c1_0506: x -1.30..-1.51, z 1.10..1.15)."""
    made = []
    nw = 56
    arch_cols, belt_cols = [], []
    for i in range(nw + 1):
        x = P.X_QTR_R + (P.X_COWL - 0.03 - P.X_QTR_R) * (i / float(nw))
        v_top = P.V_GLASS_TOP(x)
        y_t, z_t = S.BODY.section_v(x, v_top)
        arch_cols.append([(x, y_t + 0.0025, z_t - 0.003), (x, y_t + 0.0025, z_t + 0.009)])
        v_bot = P.V_QTR_LOW(x) if x < P.X_QTR_F else P.V_BELT
        y_b, z_b = S.BODY.section_v(x, v_bot)
        belt_cols.append([(x, y_b + 0.0025, z_b - 0.005), (x, y_b + 0.0025, z_b + 0.005)])
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

    # the vent's dots: a hex lattice clipped to the triangle at the quarter glass's tip
    tri = [CAM.side_xz(u, v, 0.64, "white") for (u, v) in ((2832, 1396), (2992, 1486), (2858, 1496))]

    def inside(x, z):
        s = []
        for a, b in zip(tri, tri[1:] + tri[:1]):
            s.append((b[0] - a[0]) * (z - a[1]) - (b[1] - a[1]) * (x - a[0]))
        return all(t >= 0 for t in s) or all(t <= 0 for t in s)

    pitch, r = 0.0155, 0.0042
    xs = [min(t[0] for t in tri) + 0.004 + pitch * k for k in range(14)]
    z_lo = min(t[1] for t in tri)
    verts, faces = [], []
    for row in range(6):
        zr = z_lo + 0.004 + row * pitch * 0.866
        for k, x in enumerate(xs):
            xx = x + (0.5 * pitch if row % 2 else 0.0)
            if not inside(xx, zr):
                continue
            v = S.v_at_z(xx, zr, S.V_SHOULDER, 1.0)
            p0, n = (xx,) + S.section_v(xx, v), S.surface_normal(xx, v)
            c = (p0[0], p0[1] + n[1] * 0.0030, p0[2] + n[2] * 0.0030)
            base = len(verts)
            for j in range(8):
                a = 2.0 * math.pi * j / 8
                verts.append((c[0] + r * math.cos(a), c[1], c[2] + r * math.sin(a)))
            faces.append([base + j for j in range(8)])
    if faces:
        dots = M.obj("Seal_Quarter_Vent_Dots", verts, faces, collection, lib["plate_white"], smooth=False)
        M.orient(dots.data, geom.const((0.0, 1.0, 0.0)))
        M.mirror_y(dots)
        made.append(dots)
    return made


# --------------------------------------------------------- charge flap
def build_charge(collection, lib):
    """The rear-left quarter's round flap, a dark shut line (c1_0506: x -1.45..-1.68, z 0.83..0.96)."""
    return [fittings.outline_ring("Seal_ChargeDoor_Line", -1.69, -1.45, 0.828, 0.958, 0.045,
                                  proud, collection, lib["shadow"])]


# ------------------------------------------------------------- build all
def build_all(collection, lib):
    made = []
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_gill(collection, lib)
    made += build_ocean_wave(collection, lib)
    made += build_rockers(collection, lib)
    made += build_window_trim(collection, lib)
    made += build_charge(collection, lib)
    return made
