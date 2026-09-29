"""SU7 Ultra rear-end details: light bar and corner lamps, lettering and the
reversing camera, plate, the corner pods' blades and reflectors, diffuser,
wing, deck stripes and the black sill behind the rear wheel.

Hardpoints come from the three rear photographs in blender/reference/
su7-ultra/rear, with the plate (440 x 140 mm, z 0.39-0.53) as the ruler at the
tail face, and from the matched side photograph for anything on the flank.
The first rear was built from the side photograph alone, which cannot see
the tail face: it had the corner lamps only 0.12 m long at the extreme
corners, no lid, a smooth black band for a bumper and a slot for a vent.

What the photographs show, from the top:

    wing        carbon blade on two inverted-triangle uprights at y +/-0.31,
                its tips turned down into deep endplates
    lid         a concave band under the lip carrying the wordmark; a light
                bar 50 mm tall right across; below it both badges; the lid
                ends in a U-shaped shut line at z 0.68 (su7_panels)
    lamps       the bar grows into a corner lamp at y 0.45 with a hooked top
                (z 0.92), wraps the corner and ends in a point on the flank;
                lit, a red C in each corner lamp runs into the bar's line
    bumper      gloss black below z 0.58: the plate recessed between two big
                rounded pods, each with a body-colour L blade over a red
                reflector; a diffuser under it all (su7_panels cuts them)
"""
import math

import su7_surface as S
import su7_front as FR
import su7_panels as PN
import su7_nose as N
from carkit import geom
from carkit import mesh as M
from carkit import place as P
from carkit.parts import aero, fittings, lamps

proud = FR.proud
TAIL = N.TAIL
BODY = N.BODY

FONT_DIR = r"C:\Program Files\Blender Foundation\Blender 5.2\5.2\datafiles\fonts"


def on_tail(y, z, d=0.0):
    """The tail cap at rear-elevation (y, z) - exact, analytic - pushed d
    along its outward normal. Handles the right half (y < 0) by mirroring."""
    w, v = TAIL.wv_at(abs(y), z)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    p = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def on_flank(x, z, d=0.0):
    p, n = BODY.side_point(x, z)
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


def _font(fn):
    import os
    import bpy
    try:
        return bpy.data.fonts.load(os.path.join(FONT_DIR, fn), check_existing=True)
    except Exception as e:                      # another Blender: default font
        print("font %s not loaded (%s) - using Blender's default" % (fn, e))
        return None


# ---------------------------------------------------------------- the lamps
# One lens from the centreline round the corner to the tip on the flank, left
# half. Rear-face points are (y, z); round the corner and on the flank they
# are (x, y, z) near the surface, placed by their (x, z) (lamp_place).
LAMP_UPPER = [(0.000, 0.848), (0.250, 0.848), (0.395, 0.850), (0.425, 0.866),
              (0.442, 0.902), (0.466, 0.920), (0.570, 0.922), (0.680, 0.915),
              (0.760, 0.906),
              (-2.200, 0.846, 0.893), (-2.130, 0.906, 0.872), (-2.060, 0.925, 0.846),
              (-2.000, 0.930, 0.821)]
LAMP_LOWER = [(0.000, 0.800), (0.250, 0.800), (0.450, 0.799), (0.600, 0.797),
              (0.700, 0.794), (0.770, 0.791),
              (-2.200, 0.856, 0.787), (-2.130, 0.910, 0.788), (-2.060, 0.927, 0.797),
              (-2.000, 0.931, 0.817)]
Y_FACE = 0.785                  # placed by (y, z) up to here, by (x, z) beyond
LAMP_NS = 72


def _lamp_pt(q):
    """An authored lamp point as a 3D point near the surface."""
    if len(q) == 2:
        return on_tail(q[0], q[1])[0]
    return q


def lamp_place(p, d):
    """A point on the body, d proud, from the ANALYTIC surfaces: the tail
    cap at (y, z) on the face, the flank-or-cap side point at (x, z) round the
    corner. Ray cast onto the built meshes, the corner hit the quarter on one
    side of the join and the tail cap on the other, a millimetre apart, and
    the lens crown broke through the light pipes there."""
    if p[1] <= Y_FACE:
        return on_tail(p[1], p[2], d)
    return on_flank(p[0], p[2], d)


def lamp_edges(n=LAMP_NS):
    lo = geom.polyline([_lamp_pt(q) for q in LAMP_LOWER], n)
    up = geom.polyline([_lamp_pt(q) for q in LAMP_UPPER], n)
    return lo, up


def _split(lo, up, y_cut, gap):
    """Station index ranges either side of the lid's edge, `gap` apart."""
    mid = [0.5 * (lo[i][1] + up[i][1]) for i in range(len(lo))]
    a = max(i for i in range(len(lo)) if mid[i] <= y_cut - 0.5 * gap)
    b = min(i for i in range(len(lo)) if mid[i] >= y_cut + 0.5 * gap)
    return a, b


def build_taillamps(collection, lib):
    """Smoked lens in two pieces either side of the lid's shut line over a
    dark housing, lit red light pipes, a satin reflector strip in the corner
    lamps, satin seals round the edges."""
    made = []
    lo, up = lamp_edges()
    out = geom.away_from((-2.10, 0.35, 0.84))
    crown = (lambda k, n: 0.0034 + 0.0012 * math.sin(math.pi * k / n))
    # the lens stops either side of the lid's edge: the gap runs through the
    # lamp, as on the car, and the dark slot shows through it
    a, b = _split(lo, up, PN.Y_LID, 0.010)
    for tag, i0, i1 in (("Inner", 0, a), ("Outer", b, len(lo) - 1)):
        lo_p = geom.polyline(lo[i0:i1 + 1], 4 * (i1 - i0) // 3 + 2)
        up_p = geom.polyline(up[i0:i1 + 1], 4 * (i1 - i0) // 3 + 2)
        made.append(lamps.lens("SU7Ultra_Tail_Lens" + tag, lo_p, up_p, lamp_place,
                               collection, lib["lamp_smoked"], 6, crown, out,
                               thickness=0.003, bevel=(0.0010, 2, 30)))
    made += lamps.seals("SU7Ultra_Tail_Seal", lo, up, lamp_place, collection,
                        lib["grille"], out, width=0.005, d=0.0010)
    # a dark housing under the whole lens, in one piece: through the split at
    # the lid's edge the paint showed as a yellow tick
    rows = [[lamp_place(geom.lerp(lo[i], up[i], k), 0.0012)[0] for k in (0.0, 0.5, 1.0)]
            for i in range(0, len(lo), 2)]
    housing = M.grid("SU7Ultra_Tail_Housing", rows, collection, lib["lamp_housing"], out)
    M.mirror_y(housing)
    made.append(housing)

    # red light pipes: the bar's line runs out along the lower half of each
    # corner lamp; a second pipe under the top edge from the hook out; the two
    # joined at the outer end - the red "C" of the lit photographs
    ns = len(lo)
    mid = [0.5 * (lo[i][1] + up[i][1]) for i in range(ns)]
    hook = min(i for i in range(ns) if mid[i] >= 0.44)
    end = min(i for i in range(ns) if lo[i][0] >= -2.095 and mid[i] > 0.8)
    # Lit, as in the rear photographs: the tail lamps are the car's signature
    # from behind, and unlit they read as a black band.
    pipe = (lambda k: 0.0058)          # clear of the lens crown (<= 4.6 mm)
    red = lib["led_red_tail"]
    made.append(lamps.band_between("SU7Ultra_Tail_Pipe", lo, up, range(end + 1),
                                   (0.26, 0.36, 0.46, 0.54), lamp_place, pipe,
                                   collection, red, out))
    made.append(lamps.band_between("SU7Ultra_Tail_PipeUp", lo, up, range(hook, end + 1),
                                   (0.64, 0.73, 0.82, 0.89), lamp_place, pipe,
                                   collection, red, out))
    rows = [[lamp_place(geom.lerp(lo[i], up[i], k), 0.0058)[0]
             for k in (0.26, 0.42, 0.58, 0.74, 0.89)] for i in (end - 2, end)]
    made.append(M.grid("SU7Ultra_Tail_PipeEnd", rows, collection, red, out))
    M.mirror_y(made[-1])
    # a dark satin reflector strip under the pipes in the corner lamps - the
    # structure the unlit lamps show; chrome glared white under the sky
    made.append(lamps.band_between("SU7Ultra_Tail_Guide", lo, up, range(hook, ns - 2),
                                   (0.14, 0.20), lamp_place, lambda k: 0.0052,
                                   collection, lib["lamp_bowl"], out))
    return made


# -------------------------------------------------------------------- wing
# The MIIT filing gives the wing a 1560 mm span and a 240 mm chord; through
# the matched side camera it sits between x -2.07 and -2.36 (endplates
# included), barely clear of the deck. Each tip turns down into a deep
# endplate - in every rear photograph the tips hook ~0.1 m below the blade.
WING_LE = (-2.085, 1.116)     # (x, z) of the leading edge
WING_TE = (-2.325, 1.146)     # trailing edge - higher, for downforce
WING_SPAN = 0.773             # half span: 1560 mm over the endplates (MIIT)
WING_T = 0.093                # thickness / chord
# The uprights are inverted triangles: broad under the blade, narrowing to a
# foot on the deck, at y +/-0.31 (inboard of the lid's edges).
PYLON_Y = 0.310


def _deck_z(x, y):
    hit = FR._hit_along((x, y, 1.40), (0.0, 0.0, 1.0),
                        ("SU7Ultra_Tail_Upper", "SU7Ultra_Decklid"), reach=0.60)
    if hit is None:
        return proud((x, y, S.Z_ROOF(x) + 0.08), 0.0)[0][2] - 0.004
    return hit[2] - 0.004


def build_wing(collection, lib):
    # the tips are the blade itself curling down, not plates bolted to it:
    # flat endplates read as black slabs from every rear angle
    return aero.rear_wing(
        "SU7Ultra_Wing", collection, lib, WING_LE, WING_TE, WING_SPAN - 0.050,
        thickness=WING_T, camber=0.040, camber_pos=0.40,
        tip=dict(radius=0.050, drop=0.045, n=7),
        pylons=dict(style="triangle_cutout", y=PYLON_Y, t=0.010,
                    x_deck=(-2.214, -2.246), x_wing=(-2.300, -2.090),
                    deck_z=_deck_z, cutout=0.60, mat="carbon", bevel=0.0022))


# ---------------------------------------------------------------- lettering
def build_badges(collection, lib):
    """The wordmark on the lid band above the bar, 'xiaomi' lower case and
    set wide (230 x 33 mm); '小米' and 'SU7 Ultra' under the bar either side;
    the reversing camera's lens just under the lid's shut line.

    Fonts are the open ones Blender ships (Inter, Noto Sans CJK - OFL), so
    the glyph outlines baked into the model can ship with it."""
    made = []
    inter, cjk = _font("Inter.woff2"), _font("Noto Sans CJK Regular.woff2")
    mat = lib["text_dark"]

    def badge(name, body, size, y, z, font, **kw):
        p, n = on_tail(y, z, 0.0010)
        t = M.text_mesh(name, body, size, collection, mat, extrude=0.0010,
                        font=font, resolution=4, **kw)
        P.on_surface(t, p, n)
        made.append(t)
        return t

    badge("SU7Ultra_Badge_Xiaomi", "xiaomi", 0.066, 0.0, 0.905, inter,
          spacing=1.75, weight=0.0009)
    badge("SU7Ultra_Badge_Mi", "小米", 0.105, 0.400, 0.725, cjk, weight=0.0010)
    # 'SU7' upright and 'Ultra' slanted, as on the car (the plate style)
    badge("SU7Ultra_Badge_SU7", "SU7", 0.052, -0.300, 0.725, inter, weight=0.0013)
    badge("SU7Ultra_Badge_Ultra", "Ultra", 0.052, -0.414, 0.725, inter, italic=True,
          weight=0.0009)

    # reversing camera: a black bezel and a glass eye, centred under the lid
    p, n = on_tail(0.0, 0.645, 0.0006)
    made += _disc("SU7Ultra_RearCamera", p, n, 0.013, collection, lib["black_gloss"])
    p2 = tuple(p[i] + n[i] * 0.0012 for i in range(3))
    made += _disc("SU7Ultra_RearCamera_Lens", p2, n, 0.0065, collection, lib["lamp_smoked"])
    return made


def _disc(name, c, n, r, collection, mat, seg=20):
    from mathutils import Vector
    nv = Vector(n).normalized()
    t1 = nv.cross(Vector((0.0, 0.0, 1.0))).normalized()
    t2 = nv.cross(t1).normalized()
    cv = Vector(c)
    verts = [tuple(cv)] + [tuple(cv + (t1 * math.cos(2 * math.pi * i / seg) +
                                       t2 * math.sin(2 * math.pi * i / seg)) * r)
                           for i in range(seg)]
    faces = [[0, 1 + i, 1 + (i + 1) % seg] for i in range(seg)]
    ob = M.obj(name, verts, faces, collection, mat)
    M.orient(ob.data, lambda cc, v=tuple(nv): v)
    return [ob]


# --------------------------------------------------------------- the plate
def build_plate(collection, lib):
    """The 'SU7 Ultra' show plate at the back of its recess, leaning back 12
    degrees with the bumper - the plate reads as a parallelogram leaning the
    same way in all three rear photographs."""
    tilt = math.radians(12.0)
    z = 0.460
    x_face = FA_recess_x(0.0, z)
    p = (x_face + 0.046, 0.0, z)
    n = (-math.cos(tilt), 0.0, math.sin(tilt))
    return fittings.plate("SU7Ultra_RearPlate", p, n, collection, lib, w=0.440, h=0.140,
                          texts=(("SU7", -0.080, 0.070, False, True),
                                 ("Ultra", 0.080, 0.070, True, False)))


def FA_recess_x(y, z):
    """x of the black bumper's face at (y, z)."""
    return on_tail(y, z, PN.black_stand(TAIL.wv_at(abs(y), z)[0]))[0][0]


# ---------------------------------------------------------------- the pods
# In each pod (su7_panels.POD) a body-colour blade: a short upright at the
# plate end and a long leg out toward the corner, thinning to a round tip,
# with a red reflector under the leg. Rear elevation (y, z).
BLADE_LEG = dict(y0=0.268, y1=0.748, z_bot=0.347, top0=0.392, top1=0.370)
BLADE_UP = dict(y0=0.268, y1=0.306, z0=0.360, z1=0.472)
REFLECTOR = dict(y0=0.330, y1=0.735, z0=0.318, z1=0.336)
BLADE_SET = 0.006             # behind the black bumper's face
BLADE_DEEP = 0.030


def _on_bumper(y, z, back):
    """A point `back` behind the black bumper's face, and the face normal."""
    p, n = on_tail(y, z, PN.black_stand(TAIL.wv_at(abs(y), z)[0]) - back)
    return p, n


def build_pods(collection, lib):
    made = []
    L = BLADE_LEG
    rows = []
    for i in range(33):
        t = i / 32.0
        y = L["y0"] + (L["y1"] - L["y0"]) * t
        top = L["top0"] + (L["top1"] - L["top0"]) * t
        zb = L["z_bot"]
        if t > 0.94:                              # round the tip off
            e = (t - 0.94) / 0.06
            h = (top - zb) * 0.5
            c = 0.5 * (top + zb)
            s = math.sqrt(max(0.0, 1.0 - e * e))
            top, zb = c + h * s, c - h * s
        rows.append([_on_bumper(y, zb + (top - zb) * k / 3.0, BLADE_SET)[0]
                     for k in range(4)])
    leg = M.grid("SU7Ultra_PodBlade", rows, collection, lib["paint"],
                 geom.const((-1.0, 0.25, 0.0)))
    U = BLADE_UP
    rows = []
    for i in range(9):
        t = i / 8.0
        y = U["y0"] + (U["y1"] - U["y0"]) * t
        e = abs(2.0 * t - 1.0)
        z1 = U["z1"] - 0.5 * (U["y1"] - U["y0"]) * (1.0 - math.sqrt(max(0.0, 1.0 - e * e)))
        rows.append([_on_bumper(y, U["z0"] + (z1 - U["z0"]) * k / 6.0, BLADE_SET)[0]
                     for k in range(7)])
    up = M.grid("SU7Ultra_PodBladeUp", rows, collection, lib["paint"],
                geom.const((-1.0, 0.0, 0.0)))
    for ob in (leg, up):
        M.solidify(ob, BLADE_DEEP)
        M.bevel(ob, 0.0030, 2, 40)
        M.mirror_y(ob)
        made.append(ob)
    R = REFLECTOR
    rows = [[_on_bumper(R["y0"] + (R["y1"] - R["y0"]) * i / 16.0, z, 0.014)[0]
             for z in (R["z0"], R["z1"])] for i in range(17)]
    ref = M.grid("SU7Ultra_PodReflector", rows, collection, lib["reflector"],
                 geom.const((-1.0, 0.0, 0.0)))
    M.mirror_y(ref)
    made.append(ref)
    return made


# ---------------------------------------------------------------- diffuser
def _x_rear(y):
    # the deck's rear edge follows the bumper's plan, 5 mm inside its face
    return N.cap_x_at(y, 0.250, front=False) - 0.005


def build_diffuser(collection, lib):
    """Under the plate and pods: the ramped deck with fins under the plate's
    edges and under each pod, as the low rear photograph shows."""
    # satin, like the real unpainted diffuser: gloss black mirrored the bright
    # ground as a grey shelf under the bumper. Fins stay below the pods.
    return aero.diffuser("SU7Ultra_Diffuser", collection, lib, _x_rear,
                         x_front=-2.20, half_width=0.70,
                         z=(0.150, 0.190, 0.262), fins=(0.125, 0.330, 0.540),
                         fin_z=(0.150, 0.262, 0.276, 0.170), mat="grille")


# ------------------------------------------------------------ black sill
# The black lower bumper carries on along the bottom of each rear quarter to
# the wheel arch, its top edge rising from z 0.27 at the arch to 0.36 at the
# tail - the black band under the yellow in the side photograph.
# build_rear_sill moves the last point onto the join, at the bumper's top edge.
SILL_TOP = [(-1.852, 0.270), (-1.950, 0.290), (-2.030, 0.316), (-2.110, 0.340)]


def _x_join(z):
    """x of the tail cap's join with the flank at height z (it leans back
    toward the bottom: -2.110 at z 0.34, -2.124 at 0.22)."""
    x = -2.10
    for _ in range(3):
        x = N.JOIN_R(S.v_at_z(x, z, 0.0, S.V_SHOULDER))
    return x


def build_rear_sill(collection, lib):
    # the bottom edge runs 3 mm under the quarter's (PN.V_SILL, floor + 30 mm):
    # at floor + 34 mm a strip of yellow showed along the bottom
    lo = [(x, S.Z_FLOOR(x) + 0.027) for (x, _z) in SILL_TOP]
    lo[0] = (-1.826, lo[0][1])
    # both rear corners follow the join exactly, so the sill neither leaves
    # paint showing before the bumper nor overlaps it. The top one stopped
    # 24 mm short of it, and a sliver of yellow quarter showed down the join.
    # It ends level with the bumper's top edge there.
    z_lo = S.Z_FLOOR(-2.12) + 0.027
    lo[-1] = (_x_join(z_lo) - 0.004, z_lo)
    z_hi = PN.Z_BLACK(1.0) - 0.0008
    top = SILL_TOP[:-1] + [(_x_join(z_hi) - 0.004, z_hi)]
    # it stops at the cap join, where the black bumper (3 mm proud there,
    # su7_panels.black_stand) takes over: overlapping, the two z-fought in
    # the web viewer as black and white stripes
    return [fittings.side_patch("SU7Ultra_RearSill", lo, top, BODY.side_point,
                                collection, lib["black_gloss"], d=0.0025, n=16, nk=4)]


# ----------------------------------------------------------------- the lip
LIP_HALF = 0.520              # stops short of the lid's edges (Y_LID 0.55)


def build_ducktail(collection, lib):
    """The lid's crisp upper edge: a lip 8 mm high at the centre over the
    wordmark band, following the tail's plan and fading out at the lid's
    edges, where the corner lamps' hooks rise to meet it."""
    def x_edge(y):
        return on_tail(y, N.TAIL_Z_HI - 0.004)[0][0] + 0.003

    def z_deck(x):
        return _deck_z(x, 0.0) + 0.004

    return [aero.ducktail("SU7Ultra_Ducktail", collection, lib, z_deck, x_edge,
                          half_width=LIP_HALF, n=30, root=0.085, sink=(0.001, 0.004),
                          lip=(0.008, 0.006),
                          under=(0.012, 0.003, 0.004, 0.022, 0.012, 0.030))]


# ----------------------------------------------------------------- stripes
def build_stripes(collection, lib):
    """The twin stripes carry on over the deck and the lip, as on the hood
    (su7_front.STRIPE_Y), ray cast down onto the lid."""
    y0, y1 = FR.STRIPE_Y
    names = ("SU7Ultra_Decklid", "SU7Ultra_Tail_Upper", "SU7Ultra_Ducktail")
    # stop 6 mm short of the lip: a ray past it drops down the tail face and
    # hung the stripes over the wordmark like a curtain
    x_lip = N.TAIL_X_OF_Z(N.TAIL_Z_HI) + 0.006
    xs = [PN.X_BACKLIGHT - 0.030 + (x_lip - PN.X_BACKLIGHT + 0.030) * i / 40.0
          for i in range(41)]
    rows = []
    for x in xs:
        row = []
        for c in range(4):
            y = y0 + (y1 - y0) * c / 3.0
            hit = FR._hit_along((x, y, 1.40), (0.0, 0.0, 1.0), names, reach=0.60)
            if hit is None or hit[2] < N.TAIL_Z_HI - 0.02:
                break
            row.append((hit[0], hit[1], hit[2] + 0.0007))
        if len(row) == 4:
            rows.append(row)
    ob = M.grid("SU7Ultra_Stripes_Deck", rows, collection, lib["stripe"],
                geom.const((0.0, 0.0, 1.0)))
    M.mirror_y(ob)
    return [ob]


# ------------------------------------------------------------ vent pockets
def build_vent_pockets(collection, lib):
    """A dark pocket behind each rear vent (su7_panels.rear_vent_outline):
    through the bigger opening the inner face of the corner showed as paint."""
    loop, d = PN.rear_vent_outline(n=4)
    loop = list(loop) + [loop[0]]                 # close the tube
    cx = [sum(p[k] for p in loop[:-1]) / (len(loop) - 1) for k in range(3)]
    rings = []
    for depth, k in ((-0.004, 1.0), (0.030, 0.92), (0.055, 0.70)):
        rings.append([tuple(cx[j] + (p[j] - cx[j]) * k - d[j] * depth for j in range(3))
                      for p in loop])
    rings.append([tuple(cx[j] + (p[j] - cx[j]) * 0.25 - d[j] * 0.062 for j in range(3))
                  for p in loop])
    ob = M.mesh_from_rows("SU7Ultra_RearVent_Pocket", rings, collection)
    ob.data.materials.append(lib["shadow"])
    M.mirror_y(ob)
    return [ob]


def build_all(collection, lib):
    FR.reset_bvh()
    made = []
    made += build_taillamps(collection, lib)
    made += build_vent_pockets(collection, lib)
    made += build_wing(collection, lib)
    made += build_badges(collection, lib)
    made += build_plate(collection, lib)
    made += build_pods(collection, lib)
    made += build_diffuser(collection, lib)
    made += build_rear_sill(collection, lib)
    made += build_ducktail(collection, lib)
    FR.reset_bvh()                 # the stripes are cast onto the lip too
    made += build_stripes(collection, lib)
    return made
