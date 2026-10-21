"""BYD Seal EV rear end, calibrated against Autohome Series 6394 studio rear
photographs and official technical specs.

Features:
    seamless wrap   Uses robust (w, v) band projection and decklid blending so all
                    rear body panels wrap 100% seamlessly to the quarter shut lines (JOIN_R)
                    with zero holes or gaps.
    tail lamps      Full-width continuous through-type LED light bar with sharp angular
                    outer graphics, continuous red through-bar, bisecting chrome strip,
                    and water-drop matrix LED elements.
    ducktail        Integrated ducktail spoiler lip across the decklid trailing edge.
    badges          Chrome "BYD" wordmark centered on the tailgate, "比亚迪" on the left,
                    and "海豹" on the right.
    plate tray      Recessed trapezoid pocket with "BYD SEAL" license plate and camera pod.
    bumper          Corner C-shaped vertical air outlets, parking sensors, and sculpted
                    gloss-black aerodynamic rear diffuser with vertical fins.
"""
import math

import seal_surface as S
import seal_nose as N
from carkit import geom
from carkit import mesh as M

BODY = N.BODY
TAIL = N.TAIL
CAP_LOW = TAIL.Z_LO + 0.004
CAP_HIGH = TAIL.Z_HI - 0.002
GAP = 0.0042


def face(y, z, d=0.0):
    """Point on the tail cap at elevation (y, z) (left half), and normal."""
    z = max(CAP_LOW, min(CAP_HIGH, z))
    w, v = TAIL.wv_at(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _lerp(pts, y):
    pts = sorted(pts)
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


# ------------------------------------------------------------------ hardpoints
# Thin blade-shaped taillight housings connected by a slim full-width light bar,
# curving downward at the outer tips (fishtail profile)
LAMP_TOP = [
    (0.000, 0.906), (0.200, 0.908), (0.380, 0.912), (0.540, 0.914),
    (0.660, 0.904), (0.755, 0.884), (0.830, 0.858),
]
LAMP_BOT = [
    (0.000, 0.882), (0.200, 0.880), (0.380, 0.872), (0.540, 0.862),
    (0.660, 0.846), (0.755, 0.822), (0.830, 0.794),
]

BUMPER_TOP = [
    (0.000, 0.560), (0.260, 0.564), (0.500, 0.578), (0.700, 0.602), (0.840, 0.628),
]

# Slim horizontal red reflector integrated cleanly into the lower bumper
REFLECTOR_LOOP = [
    (0.520, 0.296), (0.710, 0.302), (0.715, 0.284), (0.520, 0.278),
]
Z_PLATE = 0.475


def bumper_top(y):
    if y <= BUMPER_TOP[-1][0]:
        return _lerp(BUMPER_TOP, y)
    return BUMPER_TOP[-1][1] + (y - BUMPER_TOP[-1][0]) * 0.28


def lamp_top(y):
    return _lerp(LAMP_TOP, y)


def lamp_bot(y):
    return _lerp(LAMP_BOT, y)


# ----------------------------------------------------------- band construction
_GRID = {}


def _grid():
    if not _GRID:
        import numpy as np
        ws = np.linspace(0.0, 1.0, 65)
        vs = np.linspace(0.0, 1.0, 129)
        W, V = np.meshgrid(ws, vs)
        P = np.array([[TAIL.point(float(w), float(v)) for w in ws] for v in vs])
        _GRID.update(W=W.ravel(), V=V.ravel(), Y=P[:, :, 1].ravel(), Z=P[:, :, 2].ravel())
    return _GRID


def wv_of(y, z):
    """(w, v, miss) of the tail cap point nearest elevation (y, z)."""
    import numpy as np
    G = _grid()
    k = int(np.argmin((G["Y"] - y) ** 2 + (G["Z"] - z) ** 2))
    w, v = float(G["W"][k]), float(G["V"][k])
    for _ in range(8):
        p = TAIL.point(w, v)
        fy, fz = p[1] - y, p[2] - z
        if abs(fy) < 2e-5 and abs(fz) < 2e-5:
            break
        h = 1e-4
        pw = TAIL.point(min(1.0, w + h), v)
        pv = TAIL.point(w, min(1.0, v + h))
        a11, a21 = (pw[1] - p[1]) / h, (pw[2] - p[2]) / h
        a12, a22 = (pv[1] - p[1]) / h, (pv[2] - p[2]) / h
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-9:
            break
        dw = (a22 * fy - a12 * fz) / det
        dv = (-a21 * fy + a11 * fz) / det
        w = min(1.0, max(0.0, w - dw))
        v = min(1.0, max(0.0, v - dv))
    p = TAIL.point(w, v)
    return w, v, math.hypot(p[1] - y, p[2] - z)


def wv(y, z):
    w, v = TAIL.wv_at(y, z)
    p = TAIL.point(w, v)
    if abs(p[2] - z) > 0.006 or abs(p[1] - y) > 0.006:
        w, v, _ = wv_of(y, z)
    return w, v


_ZTOP = {}


def _reach_at(i):
    hit = _ZTOP.get(i)
    if hit is None:
        y = 0.02 * i
        z = CAP_HIGH
        while z > CAP_LOW and wv_of(y, z)[2] > 0.0015:
            z -= 0.004
        hit = z
        _ZTOP[i] = hit
    return hit


def z_reach(y):
    f = abs(y) / 0.02
    i = int(f)
    a, b = _reach_at(i), _reach_at(i + 1)
    return a + (b - a) * (f - i)


def edge_y(z):
    """Half-width of the tail cap at height z: meeting the quarter join ring."""
    return TAIL.half_width(max(CAP_LOW, min(CAP_HIGH, z))) * 0.9995


def band(name, zlo, zhi, ny, nz, collection, mat, offset=0.0, thickness=M.SKIN, y_max=None, ymin=0.0,
         off_fn=None, bevel=0.0, cut=False, hold=False):
    """A strip of the tail cap wrapping all the way around to JOIN_R."""
    cols = []
    if y_max is None:
        zs = [zlo(0.4) + (zhi(0.4) - zlo(0.4)) * k / 12.0 for k in range(13)]
        ymax = max(edge_y(z) for z in zs)
    else:
        ymax = y_max
    if cut:
        y_cut = ymax
        while y_cut > ymin + 0.02 and z_reach(y_cut) - 0.002 < zlo(y_cut) + 0.008:
            y_cut -= 0.005
        ymax = min(ymax, y_cut)

    def row_z(y, fr):
        z1 = min(zhi(y), z_reach(y) - 0.002) if (cut or hold) else zhi(y)
        z0 = min(zlo(y), z1 - 0.004) if (cut or hold) else zlo(y)
        return max(CAP_LOW, min(CAP_HIGH, z0 + (z1 - z0) * fr))

    for i in range(ny + 1):
        s = i / float(ny)
        s = 1.0 - (1.0 - s) ** 1.30
        col = []
        for k in range(nz + 1):
            fr = k / float(nz)
            if y_max is None and ymin == 0.0:
                w = s
                z_lo_w = TAIL.point(w, 0.0)[2] + 0.002
                z_hi_w = TAIL.point(w, 1.0)[2] - 0.001
                y = TAIL.point(w, 0.55)[1]
                for _ in range(2):
                    z1 = min(zhi(y), z_hi_w)
                    z0 = min(zlo(y), z1 - 0.003)
                    z = max(z_lo_w, min(z_hi_w, z0 + (z1 - z0) * fr))
                    v = TAIL.v_at_z(z, w=w)
                    y = TAIL.point(w, v)[1]
            else:
                y = ymin + (ymax - ymin) * s
                z = row_z(y, fr)
                w, v = wv(y, z) if (cut or hold) else TAIL.wv_at(y, z)
            d = off_fn(y, fr) if off_fn else offset
            col.append(TAIL.offset(w, v, d) if d else TAIL.point(w, v))
        cols.append(col)
    ob = M.mesh_from_rows(name, cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(mat)
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=bevel)
    return ob


# ------------------------------------------------------------------ the tail
def build_tail(collection, lib):
    made = []
    # 1. Upper tail band: goes from bumper_top ALL THE WAY UP to CAP_HIGH at the outer corners
    # and from lamp_bot up to CAP_HIGH across the width so there is NEVER any gap around the fishtail tips!
    made.append(band("Seal_Tail_Upper", lambda y: lamp_bot(min(y, 0.825)) - 0.002, lambda y: CAP_HIGH, 56, 12,
                     collection, lib["paint"], hold=True))
    # 2. Tailgate panel between bumper and tail lamps (meets Tail_Upper cleanly at lamp_bot)
    made.append(band("Seal_Tailgate_Skin", lambda y: bumper_top(y) + 0.5 * GAP, lambda y: lamp_bot(min(y, 0.825)) + 0.001,
                     56, 14, collection, lib["paint"]))
    # 3. Upper rear bumper skin
    made.append(band("Seal_Bumper_Upper", lambda y: 0.420, lambda y: bumper_top(y) + 0.001, 56, 8, collection,
                     lib["paint"], thickness=0.003))
    # 4. Lower bumper & diffuser panel
    made.append(band("Seal_Bumper_Lower", lambda y: CAP_LOW, lambda y: 0.422, 56, 10, collection,
                     lib["black_trim"], thickness=0.003))
    return made


# ---------------------------------------------------------- tail lamps
def build_tail_lamps(collection, lib):
    """Thin blade-shaped taillight housings curving downward at the outer tips (fishtail),
    connected by a slim full-width light bar, and populated with an internal dot-matrix/pixel
    circular red LED pattern.
    """
    from mathutils import Vector
    made = []

    def lens_band(name, zlo, zhi, mat, off, ny=64, nz=3, y0=0.0, y1=None, y_max=None, thickness=0.002):
        y_hi = y1 if y_max is None else y_max
        return band(name, zlo, zhi, ny, nz, collection, mat, off_fn=off, ymin=y0, y_max=y_hi, thickness=thickness)

    # 1. Dark smoked ruby blade lens & housing pocket conformal to the tail cap wrapping to JOIN_R
    made.append(lens_band("Seal_Tail_Housing", lambda y: lamp_bot(y) - 0.0025, lambda y: lamp_top(y) + 0.0025,
                          lib["black_gloss"], lambda y, k: 0.0012, thickness=0.0025, y_max=None))
    made.append(lens_band("Seal_Tail_Lens", lamp_bot, lamp_top, lib["lamp_red_lens"],
                          lambda y, k: 0.0018 * math.sin(math.pi * k) + 0.0020,
                          y_max=None, thickness=0.0020))

    # 2. Slim full-width continuous glowing red LED light bar along the upper spine of the blade
    bar_c = lambda y: lamp_bot(y) + 0.66 * (lamp_top(y) - lamp_bot(y))
    made.append(lens_band("Seal_Tail_Through_Bar", lambda y: bar_c(y) - 0.0026, lambda y: bar_c(y) + 0.0026,
                          lib["led_red"], lambda y, k: 0.0046, y0=0.0, y1=0.812, nz=2))

    # 3. Thin satin chrome accent line underscoring the full-width light bar
    made.append(lens_band("Seal_Tail_Chrome_Bar", lambda y: bar_c(y) - 0.0046, lambda y: bar_c(y) - 0.0028,
                          lib["logo_chrome"], lambda y, k: 0.0048, y0=0.0, y1=0.808, nz=2))

    # 4. Outer fishtail red blade contours (upper & lower edge glow guides)
    made.append(lens_band("Seal_Tail_Red_Upper", lambda y: lamp_top(y) - 0.0038, lambda y: lamp_top(y) - 0.0012,
                          lib["tail_lamp"], lambda y, k: 0.0044, y0=0.0, y1=0.812, nz=2))
    made.append(lens_band("Seal_Tail_Red_Lower", lambda y: lamp_bot(y) + 0.0012, lambda y: lamp_bot(y) + 0.0038,
                          lib["tail_lamp"], lambda y, k: 0.0044, y0=0.0, y1=0.812, nz=2))

    # 5. Dense dot-matrix / pixel LED pattern (many small circular red LEDs visible on the smoked ruby lens)
    dot_verts = []
    dot_faces = []
    n_cols = 26
    n_sides = 8  # octagonal circular LED pixel
    for col_i in range(n_cols):
        u = col_i / float(n_cols - 1)
        y_d = 0.055 + u * 0.735
        zb = lamp_bot(y_d)
        zt = lamp_top(y_d)
        h_span = zt - zb
        # 3 staggered rows of circular pixel LEDs filling the fishtail blade
        for row_k, frac in enumerate((0.22, 0.42, 0.82)):
            # Graduated circular pixel radius (larger toward outer fishtail blade, smaller toward center)
            r_dot = (0.0024 + 0.0022 * (u ** 0.65)) * (0.85 if row_k == 2 else 1.0)
            y_jit = y_d + (0.005 if row_k == 1 else 0.0)
            if y_jit > 0.802:
                continue
            z_d = zb + frac * h_span
            p_c, n_c = face(y_jit, z_d, 0.0048)
            nvec = Vector(n_c).normalized()
            upv = Vector((0, 0, 1)) if abs(nvec.z) < 0.9 else Vector((1, 0, 0))
            t1 = nvec.cross(upv).normalized()
            t2 = nvec.cross(t1).normalized()
            c_vec = Vector(p_c)
            base_idx = len(dot_verts)
            for s_i in range(n_sides):
                ang = 2.0 * math.pi * (s_i / float(n_sides))
                pt = c_vec + t1 * (math.cos(ang) * r_dot) + t2 * (math.sin(ang) * r_dot)
                dot_verts.append((pt.x, pt.y, pt.z))
            dot_faces.append([base_idx + s_i for s_i in range(n_sides)])

    dots_ob = M.obj("Seal_Tail_Dot_Matrix", dot_verts, dot_faces, collection, lib["led_red"])
    M.orient(dots_ob.data, geom.axial(-1.0))
    M.mirror_y(dots_ob)
    M.finish(dots_ob, thickness=0.0014, bevel=0.0)
    made.append(dots_ob)

    return made


# ------------------------------------------------------------- rear deck & ducktail
def build_deck(collection, lib):
    """The rear deck sheet, joining the tail cap seamlessly to the backlight base."""
    S_ = S.BODY
    v_a = 0.0
    for k in range(401):
        v = k / 400.0
        if S_.section_v(TAIL.JOIN(v), v)[1] >= CAP_HIGH - 0.012:
            v_a = v
            break
    nw, nv = 36, 24
    cols = []
    for i in range(nw + 1):
        w = i / float(nw)
        w = 1.0 - (1.0 - w) ** 1.25
        cols.append([TAIL.offset(w, v_a + (1.0 - v_a) * j / float(nv), 0.0006) for j in range(nv + 1)])
    ob = M.mesh_from_rows("Seal_Rear_Deck", cols, collection)
    M.orient(ob.data, geom.axial(-1.0))
    ob.data.materials.append(lib["paint"])
    M.mirror_y(ob)
    M.finish(ob, thickness=M.SKIN, bevel=0.0)
    return [ob]


def build_ducktail(collection, lib):
    """Subtle aerodynamic ducktail spoiler lip at the trunk trailing edge."""
    return [band("Seal_Ducktail_Lip", lambda y: CAP_HIGH - 0.016, lambda y: CAP_HIGH, 48, 3, collection, lib["paint"], cut=True,
                 off_fn=lambda y, k: 0.0085 * (k ** 1.15) * (1.0 - geom.smoothstep((y - 0.46) / 0.20)) + 0.0008,
                 y_max=0.64, thickness=0.0025)]


# ------------------------------------------------------------- bumper details
def build_bumper(collection, lib):
    """Clean rear lower bumper with minimal integrated diffuser using light vertical slats,
    slim flush horizontal reflectors, and rear license plate pocket (no leftover corner vents or spikes).
    """
    made = []

    # 1. Slim flush horizontal red reflector strip integrated along the lower bumper crease
    ref_verts = [face(y, z, 0.0028)[0] for (y, z) in REFLECTOR_LOOP]
    ref_ob = M.obj("Seal_Rear_Reflector", ref_verts, [list(range(len(REFLECTOR_LOOP)))], collection, lib["reflector_red"])
    M.orient(ref_ob.data, geom.axial(-1.0))
    M.solidify(ref_ob, 0.0018)
    M.mirror_y(ref_ob)
    made.append(ref_ob)

    # 2. Minimal integrated lower diffuser panel (smooth conformal lower apron)
    d_rows = []
    for i in range(29):
        y = 0.68 * (i / 28.0)
        col = []
        for k in range(5):
            fr = k / 4.0
            z = 0.158 + (0.272 - 0.158) * fr
            # Smooth recessed channel for the minimal diffuser
            d_off = 0.0025 - 0.0085 * math.sin(math.pi * fr) * (1.0 - 0.35 * (y / 0.68) ** 2)
            col.append(face(y, z, d_off)[0])
        d_rows.append(col)
    diff = M.mesh_from_rows("Seal_Rear_Diffuser", d_rows, collection)
    M.orient(diff.data, geom.axial(-1.0))
    diff.data.materials.append(lib["black_gloss"])
    M.mirror_y(diff)
    M.finish(diff, thickness=0.0025, bevel=0.0)
    made.append(diff)

    # Subtle satin silver upper trim blade framing the minimal diffuser
    trim_rows = []
    for i in range(29):
        y = 0.68 * (i / 28.0)
        trim_rows.append([face(y, 0.268, 0.0032)[0], face(y, 0.276, 0.0032)[0]])
    diff_trim = M.mesh_from_rows("Seal_Diffuser_Trim", trim_rows, collection)
    M.orient(diff_trim.data, geom.axial(-1.0))
    diff_trim.data.materials.append(lib["trim_chrome"])
    M.mirror_y(diff_trim)
    M.finish(diff_trim, thickness=0.0018, bevel=0.0)
    made.append(diff_trim)

    # 3. Light vertical slats conformal to the minimal integrated diffuser (zero boxy spikes)
    for idx, y_slat in enumerate((0.11, 0.23, 0.35, 0.47, 0.59)):
        s_cols = []
        for dy in (-0.0020, 0.0020):
            col = []
            for k in range(7):
                fr = k / 6.0
                z = 0.164 + (0.262 - 0.164) * fr
                # Light vertical slat rises smoothly by up to 8 mm inside the diffuser channel and tapers to 0 at ends
                d_slat = 0.0020 + 0.0065 * math.sin(math.pi * fr)
                col.append(face(y_slat + dy, z, d_slat)[0])
            s_cols.append(col)
        slat = M.mesh_from_rows(f"Seal_Diffuser_Slat_{idx}", s_cols, collection)
        M.orient(slat.data, geom.axial(-1.0))
        slat.data.materials.append(lib["black_gloss"])
        M.mirror_y(slat)
        M.finish(slat, thickness=0.0022, bevel=0.0)
        made.append(slat)

    # 4. License plate tray & "BYD SEAL" plate
    p_plat, n_plat = face(0.0, Z_PLATE, 0.004)
    from carkit.parts import fittings
    made += fittings.plate("Seal_Plate_Mount_Rear", p_plat, n_plat, collection, lib,
                           w=0.480, h=0.140, depth=0.035, mat="black_gloss", bevel=(0.003, 2, 30))
    made += fittings.plate("Seal_Plate_Rear", p_plat, n_plat, collection, lib,
                           w=0.460, h=0.135, depth=0.004,
                           texts=[("BYD SEAL", 0.0, 0.036, False, True)],
                           mat="black_gloss", text_mat="machined")

    return made


# ------------------------------------------------------------------ badges
def _font(fn):
    import os, bpy
    d = os.path.join(os.path.dirname(bpy.app.binary_path), bpy.app.version_string.rsplit(".", 1)[0],
                     "datafiles", "fonts")
    try:
        return bpy.data.fonts.load(os.path.join(d, fn), check_existing=True)
    except Exception:
        return None


def build_badges(collection, lib):
    """Polished chrome 'BYD' centered under light bar, '比亚迪' left, '海豹' right."""
    made = []
    inter = _font("Inter.woff2")
    import carkit.place as P

    # 1. "BYD" wordmark centered
    p_byd, n_byd = face(0.0, 0.795, 0.0025)
    byd = M.text_mesh("Seal_Badge_BYD", "BYD", 0.028, collection, lib["logo_chrome"],
                      extrude=0.0016, font=inter, resolution=4)
    P.on_surface(byd, p_byd, n_byd)
    made.append(byd)

    # 2. "比亚迪" on left (y = +0.46 m)
    p_l, n_l = face(0.46, 0.760, 0.0025)
    bl = M.text_mesh("Seal_Badge_BYD_Zh", "比亚迪", 0.020, collection, lib["logo_chrome"],
                     extrude=0.0014, resolution=4)
    P.on_surface(bl, p_l, n_l)
    made.append(bl)

    # 3. "海豹" on right (y = -0.46 m)
    p_r, n_r = face(-0.46, 0.760, 0.0025)
    br = M.text_mesh("Seal_Badge_Seal", "海豹", 0.020, collection, lib["logo_chrome"],
                     extrude=0.0014, resolution=4)
    P.on_surface(br, p_r, n_r)
    made.append(br)

    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_tail_lamps(collection, lib)
    made += build_deck(collection, lib)
    made += build_ducktail(collection, lib)
    made += build_bumper(collection, lib)
    made += build_badges(collection, lib)
    return made
