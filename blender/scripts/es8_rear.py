"""Nio ES8 rear end: upright SUV tailgate with Super-Red illumiBlade full-width
tail lightbar (split at the tailgate shut line into Gate and Out units), overhanging
roof spoiler with CHMSL, gloss-black lower valance with full-width satin-chrome strip
and slim red reflectors, shark-fin antenna, and NIO / ES8 badging.
"""
import math
import os

import bpy
from mathutils import Vector

import es8_surface as S
import es8_nose as N
import es8_panels as PN
from carkit import geom
from carkit.geom import Curve
from carkit import mesh as M
from carkit import cut as C
from carkit.body import fascia as FA
from carkit.body import panels as BP
from carkit.parts import aero, fittings, lamps

BODY = N.BODY
TAIL = N.TAIL
FONT_DIR = os.path.join(os.path.dirname(bpy.app.binary_path), "%d.%d" % bpy.app.version[:2],
                        "datafiles", "fonts")

# --------------------------------------------------------------- hardpoints
GATE_Y = 0.785
GATE_Z_BOT = 0.640

Z_BLACK = 0.560
BLACK_CORNER_DROP = 0.060

# Super-Red illumiBlade lightbar (full width across tailgate + wraparound to quarters)
BAR_Z_UP = Curve([
    (0.000, 1.082),
    (0.450, 1.082),
    (0.750, 1.078),
    (0.785, 1.075),
    (0.828, 1.072),
], mode="pchip")

BAR_Z_LO = Curve([
    (0.000, 1.050),
    (0.450, 1.050),
    (0.750, 1.046),
    (0.785, 1.043),
    (0.828, 1.040),
], mode="pchip")


# ----------------------------------------------------------------- helpers
def on_tail(y, z, d=0.0):
    zc = max(TAIL.Z_LO + 0.005, min(TAIL.Z_HI - 0.002, z))
    w, v = TAIL.wv_at(abs(y), zc)
    p, n = TAIL.point(w, v), TAIL.normal(w, v)
    p = (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


class _RearView:
    """Ray-cast along +x from behind the car onto the full tail cap + rear quarter flank."""

    def __init__(self):
        from mathutils.bvhtree import BVHTree
        rows, _ = BP.cap_rows(TAIL, TAIL.Z_LO + 0.015, TAIL.Z_HI - 0.0008, 0.0, 1.0,
                              110, 84, top_to_centre=True)
        verts, faces = [], []
        nv = len(rows[0])
        for r in rows:
            verts.extend(r)
        for i in range(len(rows) - 1):
            a, b = i * nv, (i + 1) * nv
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(nv - 1)]
        base = len(verts)
        vs = [0.18 + 0.68 * k / 60.0 for k in range(61)]
        for i in range(61):
            t = i / 60.0
            verts.extend(S.surface(N.JOIN_R(v) + (-1.40 - N.JOIN_R(v)) * t, v) for v in vs)
        for i in range(60):
            a, b = base + i * 61, base + (i + 1) * 61
            faces += [[a + j, a + j + 1, b + j + 1, b + j] for j in range(60)]
        self.tree = BVHTree.FromPolygons(verts, faces)

    def hit(self, y, z):
        loc, nrm, _i, _d = self.tree.ray_cast(Vector((-3.6, abs(y), z)), Vector((1.0, 0.0, 0.0)), 3.0)
        if loc is None:
            return None
        n = nrm.normalized()
        if n.x > 0.0:
            n = -n
        p, n = tuple(loc), tuple(n)
        if y < 0.0:
            p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
        return p, n


_REAR = None


def rear_view():
    global _REAR
    if _REAR is None:
        _REAR = _RearView()
    return _REAR


def on_rear(y, z, d=0.0):
    h = rear_view().hit(y, z)
    if h is None:
        return on_tail(y, max(TAIL.Z_LO + 0.02, min(TAIL.Z_HI - 0.002, z)), d)
    p, n = h
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d), n


# ---------------------------------------------------------------- tailgate cuts
def gate_path():
    ring = [
        (-0.020, GATE_Z_BOT),
        ( 0.360, GATE_Z_BOT),
        ( 0.710, GATE_Z_BOT + 0.004),
        ( 0.755, GATE_Z_BOT + 0.025),
        ( 0.780, GATE_Z_BOT + 0.075),
        ( GATE_Y, 0.820),
        ( GATE_Y, 0.980),
        ( 0.770, 1.114),
    ]
    pts, nrm = [], []
    for (_x, y, z) in geom.polyline([(0.0, y, z) for (y, z) in ring], 80):
        p, n = on_rear(max(0.0, y), z)
        pts.append(p)
        nrm.append(n)
    return pts, nrm


def _cut_gate(ob):
    pts, nrm = gate_path()
    c = C.slot("_gate_" + ob.name, pts, nrm, PN.GAP, out=0.03, inside=0.03)
    C.difference(ob, [c], "gate_", reset_materials=True)


def black_top(w):
    return Z_BLACK - BLACK_CORNER_DROP * geom.smoothstep((w - 0.80) / 0.20)


def black_stand(w):
    return 0.006 - 0.003 * geom.smoothstep((w - 0.82) / 0.18)


def build_tail(collection, lib):
    made = []
    made.append(FA.cap_panel(
        "ES8_Tail_Upper", TAIL, collection, lib,
        Z_BLACK - BLACK_CORNER_DROP, N.TAIL_Z_HI - 0.0008, 0.0, 1.0, 48, 48,
        mat="paint", top_to_centre=True,
        cuts=(_cut_gate,),
    ))
    made += FA.valance(
        "ES8_Tail_Valance", TAIL, collection, lib,
        black_top, stand=black_stand, nw=46, nz=26,
        mat="black_gloss", thickness=0.0030,
    )

    # Full-width satin-chrome horizontal rear bumper blade (built on cap_rows)
    ch_rows, _ = BP.cap_rows(TAIL, 0.425, 0.443, 0.0, 0.82, 4, 36, offset=0.0075)
    ch = M.grid("ES8_Rear_Chrome_Strip", ch_rows, collection, lib["trim_silver"],
                geom.const((-1.0, 0.0, 0.0)))
    M.mirror_y(ch)
    M.finish(ch, thickness=0.0025, bevel=0.0008)
    made.append(ch)

    # Slim horizontal red rear reflectors above the chrome strip
    ref_lo = [on_rear(y, 0.478)[0] for y in (0.520, 0.650, 0.780, 0.835)]
    ref_up = [on_rear(y, 0.494)[0] for y in (0.520, 0.650, 0.780, 0.835)]
    out = geom.away_from((-2.15, 0.40, 0.45))
    made.append(lamps.lens(
        "ES8_Reflector",
        geom.polyline(ref_lo, 22), geom.polyline(ref_up, 22),
        lambda p, d: on_rear(p[1], p[2], d + 0.005),
        collection, lib["reflector"], 4,
        lambda k, nk: 0.0030 + 0.0010 * math.sin(math.pi * k / nk),
        out, thickness=0.0025, bevel=(0.0008, 2, 30),
    ))

    # Rear ultrasonic parking sensors
    for idx, (ys, zs) in enumerate(((0.28, 0.515), (0.68, 0.510))):
        made.append(fittings.rounded_panel(
            f"ES8_Sensor_{idx}", (-S.HALF_L, ys, zs), 0.011, 0.011, 0.011,
            lambda q, d: on_rear(q[1], q[2], d), -S.HALF_L, collection,
            lib["black_gloss"], d=0.005, ny=14, outward=(-1.0, 0.0, 0.0),
        ))
    return made


# --------------------------------------------------- Super-Red illumiBlade lightbar
def _lamp_place(p, d):
    return on_rear(p[1], p[2], d)


def _bar_segment(tag, y0, y1, n, collection, lib):
    made = []
    ys = [y0 + (y1 - y0) * i / float(n) for i in range(n + 1)]
    lo = [on_rear(y, BAR_Z_LO(y))[0] for y in ys]
    up = [on_rear(y, BAR_Z_UP(y))[0] for y in ys]
    out = geom.away_from((-2.15, 0.35, 1.08))
    crown = lambda k, nk: 0.0040 + 0.0014 * math.sin(math.pi * k / nk)
    made.append(lamps.lens(
        f"ES8_Lightbar_{tag}_Lens", lo, up, _lamp_place, collection,
        lib["lamp_red_lens"], 5, crown, out, thickness=0.003, bevel=(0.0010, 2, 30),
    ))
    # Bright inner Super-Red LED blade
    glow_lo = [on_rear(y, 0.62 * BAR_Z_LO(y) + 0.38 * BAR_Z_UP(y))[0] for y in ys]
    glow_up = [on_rear(y, 0.38 * BAR_Z_LO(y) + 0.62 * BAR_Z_UP(y))[0] for y in ys]
    made.append(lamps.lens(
        f"ES8_Lightbar_{tag}_Glow", glow_lo, glow_up, _lamp_place, collection,
        lib["led_red"], 3, lambda k, nk: 0.0048, out, thickness=0.002,
    ))
    made += lamps.seals(
        f"ES8_Lightbar_{tag}_Seal", lo, up, _lamp_place, collection,
        lib["black_gloss"], out, width=0.0035, d=0.0008,
    )
    return made


def build_lightbar(collection, lib):
    made = []
    # Tailgate-mounted inner segment (moves with tailgate)
    made += _bar_segment("Gate", 0.0, GATE_Y - 0.003, 36, collection, lib)
    # Quarter-mounted outer wraparound segment (stays on body, wraps corner to y = 0.828)
    made += _bar_segment("Out", GATE_Y + 0.003, 0.828, 12, collection, lib)
    return made


# --------------------------------------------------- overhanging roof spoiler & shark fin
def build_spoiler_and_fin(collection, lib):
    made = []
    # Overhanging roof spoiler at X_KNEE (-2.180), using aero.roof_spoiler
    def _roof_edge(y):
        p, _ = BODY.top_point(S.KNEE_X, min(0.58, y), 0.002)
        return (p[0], p[2])

    made.append(aero.roof_spoiler(
        "ES8_Roof_Blade", collection, lib, _roof_edge,
        half_span=0.585, chord=0.145, angle_deg=-5.0,
        thickness=0.022, tip_taper=0.75, n=22, mat="paint", lift=0.002,
    ))

    # Shark-fin roof antenna just ahead of spoiler
    x_fin = -1.940
    z_fin = S.Z_ROOF(x_fin) - 0.004
    fin_rows = [
        [(x_fin + 0.065, 0.0, z_fin), (x_fin, 0.016, z_fin), (x_fin - 0.065, 0.004, z_fin)],
        [(x_fin + 0.015, 0.0, z_fin + 0.056), (x_fin - 0.025, 0.004, z_fin + 0.060),
         (x_fin - 0.060, 0.001, z_fin + 0.052)],
    ]
    fin = M.grid("ES8_Shark_Fin", fin_rows, collection, lib["black_gloss"],
                 geom.const((0.0, 1.0, 0.0)))
    M.mirror_y(fin)
    M.finish(fin, thickness=0.003, bevel=0.001)
    made.append(fin)
    return made


# --------------------------------------------------- emblem, plate & 3D lettering
def _font(fn):
    for candidate in (fn, "Inter.woff2", "DejaVuSansMono.woff2", "bmonofont-i18n.ttf", "droidsans.ttf"):
        p = os.path.join(FONT_DIR, candidate)
        if os.path.isfile(p):
            try:
                return bpy.data.fonts.load(p, check_existing=True)
            except Exception:
                pass
    return None


def _badge_text(name, text, y_c, z_c, size, collection, mat):
    fnt = _font("bmonofont-i18n.ttf") or _font("droidsans.ttf")
    ob = M.text_mesh(name, text, size, collection, mat, extrude=0.0022, font=fnt)
    p, n = on_rear(y_c, z_c, 0.003)
    ob.rotation_euler = (0.5 * math.pi, 0.0, -0.5 * math.pi)
    ob.location = p
    return ob


def build_badges_and_plate(collection, lib):
    made = []
    # Rear NIO Sky & Earth chrome emblem centered above the illumiBlade
    emb = fittings.rounded_panel(
        "ES8_Rear_Emblem", (-S.HALF_L, 0.0, 1.110), 0.028, 0.020, 0.006,
        lambda p, d: on_rear(p[1], p[2], d), -S.HALF_L, collection, lib["chrome"],
        d=0.003, ny=14, outward=(-1.0, 0.0, 0.0),
    )
    made.append(emb)

    # ES8 badge on right tailgate (y = -0.54, z = 0.965)
    made.append(_badge_text("ES8_Badge_Model", "ES8", -0.540, 0.965, 0.032,
                            collection, lib["chrome"]))
    # NIO badge on left tailgate (y = +0.54, z = 0.965)
    made.append(_badge_text("ES8_Badge_Maker", "NIO", 0.540, 0.965, 0.026,
                            collection, lib["chrome"]))

    # Rear license plate in the smooth zone with clean proud plinth
    p_pl, n_pl = on_rear(0.0, 0.800, 0.006)
    made += fittings.plate(
        "ES8_Plate_Rear", p_pl, n_pl, collection, lib, w=0.440, h=0.140, depth=0.008,
        texts=[("NIO ES8", 0.0, 0.038, False, True)],
        mat="black_gloss", text_mat="machined",
    )
    return made


def build_all(collection, lib):
    made = []
    made += build_tail(collection, lib)
    made += build_lightbar(collection, lib)
    made += build_spoiler_and_fin(collection, lib)
    made += build_badges_and_plate(collection, lib)
    return made
