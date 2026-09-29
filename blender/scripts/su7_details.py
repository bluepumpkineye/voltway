"""Lamps, grille, aero and trim for the SU7 Ultra.

Two placement strategies, chosen per part because they fail in different ways:

* Anything on the FLANK (skirts, mirrors, handles, stripes) is mounted by
  querying the body surface - `surface_offset(x, v, d)` - so it hugs the
  curvature instead of floating.
* Anything on the NOSE or TAIL is placed in explicit (y, z) on the flat fascia
  plane. The surface function still describes the theoretical section out
  there, not the fascia face that actually closes it, so offsetting against it
  scattered shards across the front in the first attempt.

Lamps are assemblies, built the way a real one is: dark housing, chromed bowl,
a thin light-pipe that is the ONLY emissive mesh, projector barrels, and a
clear outer lens over the top. Emitting from the whole headlight body is one of
the loudest toy tells there is.
"""
import bpy
import math

import su7_surface as S

# The fascia faces sit a rim-depth inboard of the body's extreme.
FACE_F = S.HALF_L - 0.026
FACE_R = -S.HALF_L + 0.024


# ------------------------------------------------------------------ helpers
def _obj(name, verts, faces, collection, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def _mirror(ob, clip=False):
    m = ob.modifiers.new("Mirror", 'MIRROR')
    m.use_axis = (False, True, False)
    m.use_clip = clip
    m.merge_threshold = 0.0008
    return ob


def _bevel(ob, width=0.004, segments=2, angle=42.0):
    b = ob.modifiers.new("Bevel", 'BEVEL')
    b.width = width
    b.segments = segments
    b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(angle)
    return ob


def _solidify(ob, thickness, offset=1.0):
    s = ob.modifiers.new("Solidify", 'SOLIDIFY')
    s.thickness = thickness
    s.offset = offset
    s.use_even_offset = True
    return ob


def box(name, collection, c, size, mat=None, rot_y=0.0, rot_z=0.0, smooth=False):
    hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    verts = []
    for (x, y, z) in pts:
        x, z = x * cy + z * sy, -x * sy + z * cy
        x, y = x * cz - y * sz, x * sz + y * cz
        verts.append((c[0] + x, c[1] + y, c[2] + z))
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
             [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return _obj(name, verts, faces, collection, mat, smooth=smooth)


def stripe_on_top(name, collection, x0, x1, y0, y1, nx, mat=None, lift=0.0016):
    """A decal band on the hood or roof, spanning a real lateral range."""
    verts, faces = [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * (i / nx)
        for y in (y0, y1):
            v = S.v_at_y_upper(x, y)
            _, sy, sz = S.surface(x, v)
            verts.append((x, sy, sz + lift))
    for i in range(nx):
        a = i * 2
        faces.append([a, a + 2, a + 3, a + 1])
    return _obj(name, verts, faces, collection, mat)


def patch_up(name, collection, x0, x1, v0, v1, nx, nv, lift, mat=None):
    """Like `patch`, but lifted along +Z.

    Used for anything sitting on the hood or roof. Those run close to the
    section's top pole, where the surface normal degenerates and flips sign -
    which threw the hood stripes clean off the car as two floating spikes.
    """
    verts, faces = [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * (i / nx)
        for j in range(nv + 1):
            v = v0 + (v1 - v0) * (j / nv)
            px, py, pz = S.surface(x, v)
            verts.append((px, py, pz + lift))
    stride = nv + 1
    for i in range(nx):
        for j in range(nv):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    return _obj(name, verts, faces, collection, mat)


def patch(name, collection, x0, x1, v0, v1, nx, nv, offset, mat=None):
    """A shell that follows the body surface, offset proud of it."""
    verts, faces = [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * (i / nx)
        for j in range(nv + 1):
            v = v0 + (v1 - v0) * (j / nv)
            verts.append(S.surface_offset(x, v, offset))
    stride = nv + 1
    for i in range(nx):
        for j in range(nv):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    return _obj(name, verts, faces, collection, mat)


def _face_half_width(x_face, z):
    """How wide the fascia is at height z - so nothing overhangs the body."""
    v = S.v_at_z(x_face, z)
    return abs(S.section_v(x_face, v)[0]) * 0.972


def face_plate(name, collection, x_face, z0, z1, y0, y1, depth, mat,
               inward=True, bevel=0.004):
    """A slab on the fascia plane, spanning z0..z1 and y0..y1 on one side."""
    cz, cy = (z0 + z1) / 2.0, (y0 + y1) / 2.0
    d = -depth if inward else depth
    ob = box(name, collection, (x_face + d / 2.0, cy, cz),
             (abs(depth), abs(y1 - y0), abs(z1 - z0)), mat)
    if bevel > 0:
        _bevel(ob, bevel, 2)
    return ob


# --------------------------------------------------------------------- lamps
def build_headlamps(collection, lib):
    """Slim swept lamp band: recess, bowl, DRL blade, projectors, lens."""
    made = []
    z0, z1 = 0.686, 0.790
    y_in, y_out = 0.235, min(0.855, _face_half_width(FACE_F, 0.74) - 0.030)

    # the fascia carries a real aperture here, so the housing sits behind it
    recess = face_plate("SU7Ultra_Lamp_F_Housing", collection, FACE_F - 0.026,
                        z0 + 0.002, z1 - 0.002, y_in + 0.002, y_out - 0.002,
                        0.080, lib["lamp_housing"])
    _mirror(recess)
    made.append(recess)

    # the bowl is a small reflector around the projectors, set deep in the
    # cavity. Filling the whole aperture with it is what made the lamp read as
    # a flat grey slab bolted to the nose.
    bowl = face_plate("SU7Ultra_Lamp_F_Bowl", collection, FACE_F - 0.052,
                      z0 + 0.010, z0 + 0.062, y_in + 0.030, y_in + 0.290,
                      0.020, lib["lamp_bowl"], bevel=0.006)
    _mirror(bowl)
    made.append(bowl)

    # the light-pipe: the only emissive mesh in the whole assembly
    drl = face_plate("SU7Ultra_Lamp_F_DRL", collection, FACE_F - 0.011,
                     z1 - 0.032, z1 - 0.010, y_in + 0.012, y_out - 0.010,
                     0.010, lib["led_white"], bevel=0.003)
    _mirror(drl)
    made.append(drl)

    for k in range(2):
        yc = y_in + 0.085 + k * 0.145
        proj = box("SU7Ultra_Lamp_F_Proj%d" % k, collection,
                   (FACE_F - 0.046, yc, z0 + 0.034), (0.034, 0.050, 0.050),
                   lib["lamp_bowl"], smooth=True)
        _bevel(proj, 0.010, 3)
        _mirror(proj)
        made.append(proj)

    lens = face_plate("SU7Ultra_Lamp_F_Lens", collection, FACE_F + 0.0015,
                      z0 + 0.001, z1 - 0.001, y_in + 0.001, y_out - 0.001,
                      0.006, lib["lens"], bevel=0.002)
    _mirror(lens)
    made.append(lens)
    return made


def build_taillamps(collection, lib):
    """Full-width bar with a continuous red light-pipe."""
    made = []
    z0, z1 = 0.905, 0.980
    y_max = _face_half_width(FACE_R, 0.94) - 0.026

    housing = face_plate("SU7Ultra_Lamp_R_Housing", collection, FACE_R + 0.014,
                         z0 + 0.002, z1 - 0.002, -y_max + 0.002, y_max - 0.002,
                         -0.070, lib["lamp_housing"])
    made.append(housing)

    bar = face_plate("SU7Ultra_Lamp_R_Bar", collection, FACE_R + 0.018,
                     z0 + 0.022, z0 + 0.048, -y_max + 0.022, y_max - 0.022,
                     -0.014, lib["led_red"], bevel=0.004)
    made.append(bar)

    lens = face_plate("SU7Ultra_Lamp_R_Lens", collection, FACE_R - 0.0015,
                      z0 + 0.001, z1 - 0.001, -y_max + 0.001, y_max - 0.001,
                      -0.006, lib["lens"], bevel=0.002)
    made.append(lens)

    refl = face_plate("SU7Ultra_Refl_R", collection, FACE_R,
                      0.500, 0.545, 0.520, 0.720, -0.030, lib["led_red"],
                      bevel=0.005)
    _mirror(refl)
    made.append(refl)
    return made


# -------------------------------------------------------------------- grille
def build_intakes(collection, lib):
    """Real intake volumes with vanes, not a dark plane."""
    made = []

    # main lower intake
    z0, z1 = 0.300, 0.610
    y_max = min(0.700, _face_half_width(FACE_F, 0.45) - 0.090)
    # back wall of the cavity, set well behind the opening so the mouth reads
    # as a hole with depth instead of a dark rectangle painted on the nose
    mouth = face_plate("SU7Ultra_Intake_Main", collection, FACE_F - 0.092,
                       z0 - 0.012, z1 + 0.012, -y_max - 0.012, y_max + 0.012,
                       0.014, lib["grille"], bevel=0.004)
    made.append(mouth)

    for k in range(4):
        z = z0 + (z1 - z0) * (k + 0.5) / 4.0
        vane = face_plate("SU7Ultra_Intake_Vane%d" % k, collection, FACE_F - 0.018,
                          z - 0.008, z + 0.008, -y_max + 0.006, y_max - 0.006,
                          0.032, lib["grille"], bevel=0.002)
        made.append(vane)

    # outboard vertical intakes, canted outward
    y0 = y_max + 0.048
    y1 = min(_face_half_width(FACE_F, 0.42) - 0.020, y0 + 0.170)
    side = face_plate("SU7Ultra_Intake_Side", collection, FACE_F - 0.064,
                      0.330, 0.585, y0, y1, 0.014, lib["grille"], bevel=0.006)
    _mirror(side)
    made.append(side)

    # rear bumper outlets
    yr0 = 0.500
    yr1 = min(_face_half_width(FACE_R, 0.42) - 0.030, yr0 + 0.190)
    out = face_plate("SU7Ultra_Outlet_Rear", collection, FACE_R + 0.058,
                     0.340, 0.470, yr0, yr1, -0.014, lib["grille"], bevel=0.006)
    _mirror(out)
    made.append(out)
    return made


def build_plate(collection, lib):
    """Front number plate reading SU7 Ultra."""
    p = face_plate("SU7Ultra_Plate", collection, FACE_F + 0.006,
                   0.372, 0.482, -0.150, 0.150, 0.010, lib["chrome"],
                   inward=False, bevel=0.003)
    return [p]


# ---------------------------------------------------------------------- aero
def build_aero(collection, lib):
    made = []
    carbon = lib["carbon"]

    # ---- front splitter: a blade under the bumper, tucked inside the body line
    x0, x1 = S.HALF_L - 0.300, S.HALF_L + 0.052
    nx, ny = 18, 16
    verts, faces = [], []
    for i in range(nx + 1):
        t = i / nx
        x = x0 + (x1 - x0) * t
        xb = min(x, S.HALF_L - 0.001)
        half = _face_half_width(xb, S.Z_FLOOR(xb) + 0.045) * (1.0 - 0.16 * t * t)
        z = S.Z_FLOOR(xb) - 0.014 - 0.024 * t
        for j in range(ny + 1):
            y = -half + 2.0 * half * (j / ny)
            lift = 0.014 * (abs(y) / max(half, 1e-3)) ** 3
            verts.append((x, y, z + lift))
    stride = ny + 1
    for i in range(nx):
        for j in range(ny):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    sp = _obj("SU7Ultra_Splitter", verts, faces, collection, carbon)
    _solidify(sp, 0.013)
    _bevel(sp, 0.003, 2)
    made.append(sp)

    # ---- canards on the bumper corners
    for k in range(2):
        z = 0.400 + k * 0.078
        yb = _face_half_width(FACE_F, z) - 0.012
        c = box("SU7Ultra_Canard%d" % k, collection,
                (S.HALF_L - 0.075, yb - 0.020, z), (0.130, 0.090, 0.010),
                carbon, rot_y=math.radians(-8))
        _bevel(c, 0.003, 2)
        _mirror(c)
        made.append(c)

    # ---- side skirts along the rocker
    x0, x1 = -1.640, 1.600
    nx = 32
    verts, faces = [], []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * (i / nx)
        v_top = S.v_at_z(x, S.z_rocker(x) + 0.030, 0.0, S.V_SHOULDER)
        v_bot = max(0.035, S.v_at_z(x, S.z_rocker(x) - 0.052, 0.0, S.V_SHOULDER))
        verts.append(S.surface_offset(x, v_top, 0.003))
        verts.append(S.surface_offset(x, v_bot, 0.012))
    for i in range(nx):
        a = i * 2
        faces.append([a, a + 2, a + 3, a + 1])
    sk = _obj("SU7Ultra_Skirt", verts, faces, collection, carbon)
    _solidify(sk, 0.014)
    _bevel(sk, 0.003, 2)
    _mirror(sk)
    made.append(sk)

    # ---- rear diffuser with vertical fins
    x0, x1 = -S.HALF_L - 0.020, -S.HALF_L + 0.420
    nx, ny = 14, 14
    verts, faces = [], []
    for i in range(nx + 1):
        t = i / nx
        x = x0 + (x1 - x0) * t
        xb = max(x, -S.HALF_L + 0.001)
        half = _face_half_width(xb, S.Z_FLOOR(xb) + 0.050) * 0.94
        z = S.Z_FLOOR(xb) - 0.010 + 0.070 * t
        for j in range(ny + 1):
            y = -half + 2.0 * half * (j / ny)
            verts.append((x, y, z))
    stride = ny + 1
    for i in range(nx):
        for j in range(ny):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    df = _obj("SU7Ultra_Diffuser", verts, faces, collection, carbon)
    _solidify(df, 0.011)
    made.append(df)

    for k in range(4):
        y = (k + 0.5) * 0.145
        fin = box("SU7Ultra_DiffFin%d" % k, collection,
                  (-S.HALF_L + 0.155, y, S.Z_FLOOR(-S.HALF_L + 0.155) + 0.042),
                  (0.290, 0.013, 0.086), carbon, rot_y=math.radians(11))
        _mirror(fin)
        made.append(fin)

    # ---- rear wing: cambered blade on two swan-neck pylons
    x_w = -2.245
    z_deck = S.Z_ROOF(x_w)
    z_blade = z_deck + 0.205
    half_span = 0.760

    nx, ny = 12, 10
    chord = 0.290
    verts, faces = [], []
    for i in range(nx + 1):
        t = i / nx
        camber = math.sin(math.pi * t) * 0.030
        xx = x_w + chord * (t - 0.42)
        for j in range(ny + 1):
            y = -half_span + 2.0 * half_span * (j / ny)
            verts.append((xx, y, z_blade + camber * 0.30 - t * 0.036))
    stride = ny + 1
    for i in range(nx):
        for j in range(ny):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    blade = _obj("SU7Ultra_Wing_Blade", verts, faces, collection, carbon)
    _solidify(blade, 0.015)
    _bevel(blade, 0.003, 2)
    made.append(blade)

    ep = box("SU7Ultra_Wing_Endplate", collection,
             (x_w - 0.010, half_span + 0.009, z_blade - 0.040),
             (0.330, 0.014, 0.155), carbon)
    _bevel(ep, 0.006, 2)
    _mirror(ep)
    made.append(ep)

    pylon = box("SU7Ultra_Wing_Pylon", collection,
                (x_w + 0.040, half_span * 0.58, (z_blade + z_deck) * 0.5 - 0.004),
                (0.058, 0.026, z_blade - z_deck + 0.055), carbon,
                rot_y=math.radians(-15))
    _bevel(pylon, 0.005, 2)
    _mirror(pylon)
    made.append(pylon)

    # ---- ducktail lip on the decklid
    x0, x1 = -2.320, -2.070
    nx, ny = 12, 16
    verts, faces = [], []
    for i in range(nx + 1):
        t = i / nx
        x = x0 + (x1 - x0) * t
        half = S.Y_ROOF(x) * 0.90
        z = S.Z_ROOF(x) + 0.005 + 0.024 * (1.0 - t) ** 2
        for j in range(ny + 1):
            y = -half + 2.0 * half * (j / ny)
            drop = 0.026 * (abs(y) / max(half, 1e-3)) ** 2
            verts.append((x, y, z - drop))
    stride = ny + 1
    for i in range(nx):
        for j in range(ny):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append([a, a + 1, b + 1, b])
    lip = _obj("SU7Ultra_Ducktail", verts, faces, collection, lib["paint"])
    _solidify(lip, 0.009)
    made.append(lip)
    return made


# ---------------------------------------------------------------- side trim
def build_mirrors(collection, lib):
    made = []
    x_m = 0.930
    v_m = S.v_at_z(x_m, 0.920, 0.0, S.V_SHOULDER + 0.06)
    bx, by, bz = S.surface_offset(x_m, v_m, 0.008)

    arm = box("SU7Ultra_MirrorArm", collection,
              (bx - 0.014, by + 0.044, bz + 0.032), (0.042, 0.094, 0.028),
              lib["black_gloss"], rot_y=math.radians(-18))
    _bevel(arm, 0.007, 2)
    _mirror(arm)
    made.append(arm)

    pod = box("SU7Ultra_MirrorPod", collection,
              (bx - 0.040, by + 0.116, bz + 0.058), (0.128, 0.104, 0.058),
              lib["carbon"], rot_z=math.radians(-7))
    _bevel(pod, 0.019, 3)
    _mirror(pod)
    made.append(pod)
    return made


def build_handles(collection, lib):
    made = []
    for k, x in ((0, 0.520), (1, -0.560)):
        v = S.v_at_z(x, 0.892, 0.0, S.V_SHOULDER + 0.03)
        px, py, pz = S.surface_offset(x, v, 0.0015)
        h = box("SU7Ultra_Handle%d" % k, collection, (px, py, pz),
                (0.148, 0.016, 0.022), lib["chrome"])
        _bevel(h, 0.005, 2)
        _mirror(h)
        made.append(h)
    return made


def build_stripes(collection, lib):
    """Twin hood stripes and the lower body stripe, following the surface."""
    made = []
    # Two stripes running the length of the hood, positioned by real lateral
    # offset. Guessing a v put them within a whisker of the section's top pole,
    # where they collapsed to a hairline and flicked off the nose.
    for k, (y0, y1) in enumerate(((0.052, 0.128), (0.170, 0.246))):
        st = stripe_on_top("SU7Ultra_HoodStripe%d" % k, collection,
                           1.070, S.HALF_L - 0.085, y0, y1, 34, lib["stripe"])
        _solidify(st, 0.0008)
        _mirror(st)
        made.append(st)

    v_mid = S.V_SHOULDER - 0.128
    side = patch("SU7Ultra_SideStripe", collection,
                 -1.320, 1.020, v_mid, v_mid + 0.026, 34, 3, 0.0014, lib["stripe"])
    _solidify(side, 0.0008)
    _mirror(side)
    made.append(side)
    return made


def build_hood_vent(collection, lib):
    vent = patch("SU7Ultra_HoodVent", collection,
                 1.700, 2.030, 0.858, 0.898, 10, 4, -0.018, lib["grille"])
    _solidify(vent, 0.004)
    _mirror(vent)
    return [vent]


def build_all(collection, surface_mod, lib):
    made = []
    made += build_headlamps(collection, lib)
    made += build_taillamps(collection, lib)
    made += build_intakes(collection, lib)
    made += build_plate(collection, lib)
    made += build_aero(collection, lib)
    made += build_mirrors(collection, lib)
    made += build_handles(collection, lib)
    made += build_stripes(collection, lib)
    made += build_hood_vent(collection, lib)
    return made
