"""Nio ES8 front end: Shark-Nose X-Bar fascia, Double-Dash dual-layer crystal DRLs,
recessed vertical HDPL MicroLED projector headlamps, trapezoidal active lower grille,
full-width chrome lower chin blade, NIO Sky-and-Earth emblem, and Watchtower roof
LiDAR + corner camera pods.

The headlamps (the DRL, the pod and its two lens units, the vent under it) are read off the official front photograph
ext_front.jpg through its solved camera (es8_ref_match, es8_lampdata): every outline point is sent along the photo's own
ray onto the model's panels (carkit.photolay), so each lands where the real car has it. 2026-11-03, the owner: "our
headlight is cut in the middle" (the first build's DRL was four short strips with gaps, 0.14 m too far inboard and 0.1 m
too high; the real one is two dashes of one lens, a thin divider between them, running right round the corner).
"""
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import es8_surface as S
import es8_nose as N
import es8_panels as PN
import es8_lampdata as LD
import es8_ref_match as RM
from carkit import geom
from carkit import photolay as PL
from carkit import mesh as M
from carkit import cut as C
from carkit import place as P
from carkit.body import fascia as FA
from carkit.body import panels as BP
from carkit.parts import fittings, lamps

BODY = N.BODY
NOSE = N.NOSE
PLACER = P.Placer(BODY.proud)

# --------------------------------------------------------------- hardpoints
def _fx(pts):
    """Plan outlines read for the first build's nose, brought back by the nose squeeze (es8_surface.fx)."""
    return [(S.fx(x), y) for (x, y) in pts]


# Lower active grille opening (half-outline y, z). The first build's was a low strip (z 0.305 to 0.465); the real car's
# (Autohome 12707358, front) is a tall black opening from the bumper's chrome strip up to behind the plate (z 0.30 to
# 0.58), a little narrower at the top with chamfered corners, and it is what makes the nose read as an SUV's.
BAND_OUTLINE = [
    (-0.020, 0.585),
    ( 0.440, 0.585),
    ( 0.520, 0.540),
    ( 0.578, 0.440),
    ( 0.600, 0.350),
    ( 0.575, 0.305),
    (-0.020, 0.305),
]
BAND_RECESS = 0.030


# ----------------------------------------------------------------- helpers
def face(y, z, d=0.0):
    zc = max(NOSE.Z_LO + 0.005, min(NOSE.Z_HI - 0.002, z))
    w, v = NOSE.wv_at(abs(y), zc)
    w_safe = min(0.985, w)
    p, n = NOSE.point(w_safe, v), NOSE.normal(w_safe, v)
    if d:
        p = tuple(p[i] + n[i] * d for i in range(3))
    if y < 0.0:
        p, n = (p[0], -p[1], p[2]), (n[0], -n[1], n[2])
    return p, n


def _on_face(yz, n=32):
    path = geom.polyline([(0.0, y, z) for (y, z) in yz], n)
    return [face(y, z)[0] for (_x, y, z) in path]


def _place(p, d):
    return face(p[1], p[2], d)


def _cut_band(ob):
    c = C.prism_x("_band_" + ob.name, BAND_OUTLINE, S.X_FRONT + 0.35, S.X_FRONT - 0.65)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "band_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


# ---------------------------------------------------- the photo's rays onto the model's panels
# The lamp outlines are pixels of ext_front.jpg (es8_lampdata); each point goes along the photo's own ray (es8_ref_match
# "front", mirrored onto the half sheet y >= 0) to the first of the panels that meets it: the uncut fascia, the front
# fender and the hood, as they stand after the corner is smoothed (a part laid on the analytic nose would float over
# the smoothed paint). The point is the hit; the normal is the panels' own smooth vertex normals, interpolated.
SURF_PANELS = ("ES8_Fascia", "ES8_Fender_Front", "ES8_Hood")
_SURF = []
def _surf():
    if not _SURF:
        _SURF.append(PL.Surf(SURF_PANELS))
    return _SURF[0]


def _on_surface(u, v, cam="front", inset=0.0):
    """(point, outward normal) of the panels under pixel (u, v) of the photo's left half, on the half sheet. `inset`:
    how far a ray that misses the sheets' edge is pulled in, for the outlines the paint is cut along."""
    o, d = RM.ray(cam, u, v)
    o, d = Vector((o.x, -o.y, o.z)), Vector((d.x, -d.y, d.z))
    h = _surf().hit(o, d, inset)
    if h is None:
        raise RuntimeError("es8_front: the photo ray through (%g, %g) misses the nose" % (u, v))
    return h


LAY = PL.Lay(_on_surface, geom.away_from((1.90, 0.45, 0.60)))

# The DRL's outer end runs round the fender's corner: seen from the front it is edge-on (rays at 60 to 80 degrees to the
# surface, then none at all: the model's corner is a few cm narrower than the real car's), so the photo cannot place it.
# Past DRL_WRAP[0] the lamp is carried back along the wall instead: its x runs linearly from where the photo still places
# it to DRL_WRAP[2] at the tip (the side photographs and the top view, ext_hero / ext_drl, put the lamp's outer tip about
# 0.36 m behind its inner one, x 2.04), its height z is still the photo's (a ray's z at that x), and the point is the
# first panel met going outward from the car's centre at that (x, z).
DRL_WRAP = (905.0, 846.0, 2.04)


def _on_drl(u, v):
    u0, u1, x_tip = DRL_WRAP
    if u >= u0:
        return _on_surface(u, v)
    p0, _n0 = _on_surface(u0, v)
    k = min(1.0, (u0 - u) / (u0 - u1))
    k = k * k * (3.0 - 2.0 * k) * 0.35 + k * 0.65                 # eased at both ends, mostly linear
    x = p0.x + (x_tip - p0.x) * k
    o, d = RM.ray("front", u0, v)
    o, d = Vector((o.x, -o.y, o.z)), Vector((d.x, -d.y, d.z))
    z = o.z + d.z * ((o.x - x) / max(-d.x, 1e-6))
    sf = _surf()
    h = sf.tree.ray_cast(Vector((x, 0.30, z)), Vector((0.0, 1.0, 0.0)))
    if h[0] is None:
        raise RuntimeError("es8_front: no panel at x %.3f, z %.3f for the DRL's outer end" % (x, z))
    p = Vector(h[0])
    a, b, c = (sf.verts[i] for i in sf.tris[h[2]])
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01 or 1e-18
    wb, wc = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    wb, wc = min(1.0, max(0.0, wb)), min(1.0, max(0.0, wc))
    na, nb, nc = (sf.norms[i] for i in sf.tris[h[2]])
    n = na * (1.0 - wb - wc) + nb * wb + nc * wc
    n.normalize()
    return p, n


LAY_DRL = PL.Lay(_on_drl, geom.away_from((1.90, 0.45, 0.60)))


def _outline_loop(px, n):
    """The outline of a photo-pixel polygon on the panels: n points and the mean outward normal (a cut's direction)."""
    pts = PL.resample_loop(PL.smooth_loop(px, (), 3), max(4.0, PL.arc(px, True) / n))
    hits = [_on_surface(u, v, inset=0.004) for (u, v) in pts]
    d = sum((h[1] for h in hits), Vector())
    d.normalize()
    return [tuple(h[0]) for h in hits], tuple(d)


def _pocket_loop():
    return _outline_loop(LD.POD_OUT, 56)


def _vent_loop():
    return _outline_loop(LD.VENT_OUT, 44)


def _smooth_cut(ob):
    """First cut of the fascia, run on the uncut sheet: soften the nose corner's pleat (smooth_corner), then take
    the panels as they now stand for the photo's rays."""
    del _SURF[:]
    smooth_corner()
    _surf()


def _cut_pocket(ob):
    loop, d = _pocket_loop()
    c = C.prism_dir("_pocket_" + ob.name, loop, d, back=0.16, front=0.10)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "pocket_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _cut_vent(ob):
    loop, d = _vent_loop()
    c = C.prism_dir("_vent_" + ob.name, loop, d, back=0.16, front=0.10)
    sheet = C.sheet_bvh(ob)
    C.difference(ob, [c], "vent_", reset_materials=True)
    C.prune_off_sheet(ob, sheet)


def _tunnel(name, loop, d, depth, collection, mat, taper=0.88):
    c = [sum(p[i] for p in loop) / len(loop) for i in range(3)]
    rows = [[tuple(p[i] + d[i] * 0.002 for i in range(3)) for p in loop]]
    for t in (0.5, 1.0):
        k = 1.0 + (taper - 1.0) * t
        rows.append([tuple(c[i] + (p[i] - c[i]) * k - d[i] * depth * t for i in range(3))
                     for p in loop])
    back = [sum(p[i] for p in rows[-1]) / len(loop) for i in range(3)]
    rows.append([tuple(back[i] + (p[i] - back[i]) * 0.02 for i in range(3)) for p in rows[-1]])
    cols = [[rows[r][k] for r in range(len(rows))] for k in range(len(loop))]
    cols.append(cols[0])
    ob = M.mesh_from_rows(name, cols, collection)
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ fascia
def build_fascia(collection, lib):
    made = [FA.cap_panel(
        "ES8_Fascia", NOSE, collection, lib,
        N.NOSE_Z_LO + 0.001, N.NOSE_Z_HI - 0.0008, 0.0, 1.0, 48, 48,
        mat="paint", top_to_centre=True,
        cuts=(_smooth_cut, _cut_band, _cut_pocket, _cut_vent),
    )]

    # Recessed black grille panel behind the trapezoidal opening
    rows, _ = BP.cap_rows(NOSE, 0.295, 0.592, 0.0, 0.70, 24, 32, offset=-BAND_RECESS)
    band = M.mesh_from_rows("ES8_Band", rows, collection)
    M.orient(band.data, geom.axial(1.0))
    band.data.materials.append(lib["grille"])
    M.mirror_y(band)
    M.finish(band, thickness=0.0025, bevel=0.0)
    made.append(band)

    # Active horizontal louvers inside the lower grille: four heavy bars low, finer ones up behind the plate
    for idx, z_slat in enumerate((0.334, 0.370, 0.406, 0.442, 0.478, 0.512, 0.546)):
        wy = (0.0, 0.18, 0.36, 0.50, 0.57) if z_slat < 0.46 else (0.0, 0.18, 0.34, 0.46, 0.50)
        pts = [face(y, z_slat, -0.010)[0] for y in wy]
        slat_rows = [
            [(p[0] + 0.008, p[1], p[2] - 0.004) for p in pts],
            [(p[0] - 0.012, p[1], p[2] + 0.004) for p in pts],
        ]
        slat = M.grid(f"ES8_Grille_Slat_{idx}", slat_rows, collection, lib["black_gloss"],
                      geom.const((1.0, 0.0, 0.0)))
        M.mirror_y(slat)
        M.finish(slat, thickness=0.003, bevel=0.0)
        made.append(slat)

    # The dark face panel across the nose under the hood's lip (the real car's black shark-nose band, z 0.72 to 0.84)
    prow = []
    for z in (0.715, 0.745, 0.775, 0.805, 0.836):
        half = 0.475 + 0.055 * (z - 0.715) / 0.121
        prow.append([face(y, z, 0.0030)[0] for y in (0.0, 0.5 * half, 0.8 * half, half)])
    panel = M.grid("ES8_Face_Panel", prow, collection, lib["grille"], geom.axial(1.0))
    M.mirror_y(panel)
    M.finish(panel, thickness=0.003, bevel=0.0008)
    made.append(panel)

    # Central 4D mmWave radar module in lower grille
    made.append(fittings.rounded_panel(
        "ES8_Radar", (S.X_FRONT, 0.0, 0.385), 0.082, 0.050, 0.010,
        lambda p, d: face(p[1], p[2], d), S.X_FRONT, collection, lib["black_gloss"],
        d=-0.008, ny=16,
    ))
    return made


# --------------------------------------------------------------- chin lip
def build_chin(collection, lib):
    made = []
    # Full-width satin silver lower bumper blade
    ch_rows, _ = BP.cap_rows(NOSE, 0.296, 0.312, 0.0, 0.78, 4, 36, offset=0.0045)
    ch = M.grid("ES8_Chin_Strip", ch_rows, collection, lib["trim_silver"],
                geom.const((1.0, 0.0, 0.0)))
    M.mirror_y(ch)
    M.finish(ch, thickness=0.003, bevel=0.0008)
    made.append(ch)

    # Gloss-black aero chin splitter underneath
    lip_rows, _ = BP.cap_rows(NOSE, 0.280, 0.296, 0.0, 0.80, 4, 36, offset=0.0035)
    lip = M.grid("ES8_Chin_Lip", lip_rows, collection, lib["black_gloss"],
                 geom.const((1.0, 0.0, 0.0)))
    M.mirror_y(lip)
    M.finish(lip, thickness=0.003, bevel=0.001)
    made.append(lip)
    return made


# ----------------------------------------------------------- Double-Dash + HDPL lamps
# Depths are metres along the paint's normal (ext_front.jpg: 1 px is about 2 mm). The DRL stands proud of the paint as an
# applied lens (the sheets it crosses, hood, fender and fascia, are not cut for it): dark glass 1.4 mm up with a rounded
# edge, the two frosted dashes on it, the two bars lit white on their lower edges. Inside the pod everything stands in the
# opening, set back as the real units are.
GLASS_UP, GLASS_T = 0.0020, 0.0022
FROST_UP, BAR_UP = 0.0028, 0.0034
POD_BEZEL, POD_LENS, POD_SILL = -0.0140, -0.0125, -0.0100
VENT_SLAB_DEPTH = -0.030


def _px_inset(poly, d):
    return PL.grow(PL.smooth_loop(poly, (), 3), -d)


def _disc(c, r, n=24):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def build_drl(collection, lib):
    made = []
    # The Double-Dash DRL: ONE dark glass lens, two frosted dashes on it with a thin divider between, each with its
    #    bar lit along the lower edge (ext_front.jpg, traced: es8_lampdata)
    made.append(LAY_DRL.region("ES8_Lamp_Glass", PL.grow(LD.DRL_GLASS, 1.1), GLASS_UP, lib["lamp_frame"], collection,
                           step=7.0, thick=GLASS_T, bevel=0.0005))
    for nm, seg in (("O", LD.DRL_SEG_O), ("I", LD.DRL_SEG_I)):
        made.append(LAY_DRL.region("ES8_Lamp_Frost_" + nm, PL.grow(seg, -0.4), FROST_UP, lib["lamp_frost"], collection,
                               step=5.0, thick=0.0004))
    for nm, bar in (("O", LD.DRL_BAR_O), ("I", LD.DRL_BAR_I)):
        made.append(LAY_DRL.region("ES8_Lamp_DRL_" + nm, bar, BAR_UP, lib["led_white"], collection, step=3.2, thick=0.0004))
    return made


def build_headlamps(collection, lib):
    made = build_drl(collection, lib)

    # 2. The headlamp pod in the corner of the bumper: a tall "D" cut, its dark tunnel, the chrome sill, two lens units
    loop, d = _pocket_loop()
    tun = _tunnel("ES8_Pocket_Tunnel", loop, d, 0.075, collection, lib["black_gloss"])
    M.mirror_y(tun)
    made.append(tun)
    made.append(LAY.region("ES8_Pod_Sill", LD.POD_SILL, POD_SILL, lib["trim_silver"], collection, step=5.0, thick=0.0006))
    for nm, bez in (("U", LD.POD_BEZEL_U), ("L", LD.POD_BEZEL_L)):
        made.append(LAY.ribbon("ES8_Pod_Bezel_" + nm, bez, 0.0016, POD_BEZEL, lib["lamp_hair"], collection,
                               step=6.0, thick=0.0008, closed=True))
        made.append(LAY.region("ES8_Pod_Lens_" + nm, _px_inset(bez, 2.3), POD_LENS, lib["lamp_lens"], collection,
                               step=6.0, thick=0.0006))
    made.append(LAY.region("ES8_Pod_Projector", _disc(LD.POD_LENS_U[:2], LD.POD_LENS_U[2]), POD_LENS + 0.0016,
                           lib["lamp_lens"], collection, step=4.0, thick=0.0006))

    # 3. The air intake under it: a dark opening with a lighter slab recessed in its inner half
    vloop, vd = _vent_loop()
    vtun = _tunnel("ES8_Vent_Tunnel", vloop, vd, 0.060, collection, lib["black_gloss"])
    M.mirror_y(vtun)
    made.append(vtun)
    made.append(LAY.region("ES8_Vent_Slab", LD.VENT_SLAB, VENT_SLAB_DEPTH, lib["pod"], collection, step=6.0, thick=0.0008))
    return made


def relax_lamp_ao(ob, radius=0.040, ring=0.035):
    """Undo the baked occlusion's halo round the pod and the vent (see a06t_front.relax_lamp_ao). The bake darkens every
    skin vertex on a cut's rim and its smoothing carries that three rings out: a fuzzy grey border the photographs do
    not have. Every FRONT-SKIN vertex of `ob` (the nose, modifiers applied, both halves) within `radius` of an opening's
    outline takes the average of the front-skin ring `ring` beyond it."""
    import numpy as np
    from mathutils.kdtree import KDTree
    pts = []
    for px in (LD.POD_OUT, LD.VENT_OUT):
        for (u, v) in PL.resample_loop(PL.smooth_loop(px, (), 2), 12.0):
            p, _n = _on_surface(u, v)
            pts += [p, Vector((p.x, -p.y, p.z))]
    tree = KDTree(len(pts))
    for i, p in enumerate(pts):
        tree.insert(p, i)
    tree.balance()
    me = ob.data
    at = me.attributes.get("_BAKEDAO")
    if at is None:
        return 0
    ao = np.empty(len(at.data), np.float32)
    at.data.foreach_get("value", ao)
    skin_tree = _surf().tree
    mw = ob.matrix_world
    d = np.empty(len(me.vertices))
    skin = np.zeros(len(me.vertices), bool)
    for i, v in enumerate(me.vertices):
        w = mw @ v.co
        d[i] = tree.find(w)[2]
        if d[i] < radius + ring:
            hit = skin_tree.find_nearest(Vector((w.x, abs(w.y), w.z)))
            skin[i] = hit[0] is not None and hit[3] < 0.0014
    inner = (d < radius) & skin
    outer = (d >= radius) & (d < radius + ring) & skin
    if not inner.any() or not outer.any():
        return 0
    ref = float(ao[outer].mean())
    ao[inner] = np.maximum(ao[inner], ref)
    at.data.foreach_set("value", ao)
    me.update()
    print("lamp AO ring %.2f, %d skin vertices lifted" % (ref, int(inner.sum())))
    return int(inner.sum())


# ------------------------------------------------------- the nose corner's pleat
# Where the nose cap, the fender and the hood meet at the DRL's outer end the three panels' edges bend about 30 degrees
# against each other (the join ring turns 55 degrees in 12 cm there): a V-shaped pleat running down to the lamp pod, the
# "cavity" of the owner's screenshot (2026-11-03). The real car's corner is one convex roll. The panels are separate
# sheets, so smoothing each alone would open the gaps; the vertices of all three are smoothed as ONE cloud inside a
# window (each moves toward the mean of the cloud's vertices within `reach`, by a weight that fades to nothing at the
# window's edge), so a seam's two sides take nearly the same shift and the gap holds.
CORNER_CENTRE = (2.285, 0.800, 0.900)
CORNER_RADIUS = 0.095


def smooth_corner(names=("ES8_Fascia", "ES8_Fender_Front", "ES8_Hood"), centre=CORNER_CENTRE, radius=CORNER_RADIUS,
                  reach=0.020, passes=16, rate=0.7):
    import bpy
    from mathutils import Vector
    from mathutils.kdtree import KDTree
    c = Vector(centre)
    items = []
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        mw = ob.matrix_world
        for v in ob.data.vertices:
            if (mw @ v.co - c).length < radius + reach:
                items.append((ob, v.index))
    if not items:
        return 0
    moved = 0
    for _ in range(passes):
        pts = [items[i][0].matrix_world @ items[i][0].data.vertices[items[i][1]].co for i in range(len(items))]
        tree = KDTree(len(pts))
        for i, p in enumerate(pts):
            tree.insert(p, i)
        tree.balance()
        new = []
        for i, p in enumerate(pts):
            d = (p - c).length
            if d >= radius:
                new.append(p)
                continue
            f = 1.0 - d / radius
            w = rate * f * f * (3.0 - 2.0 * f)
            near = tree.find_range(p, reach)
            avg = sum((pts[j] for (_co, j, _d) in near), Vector()) / len(near)
            new.append(p + (avg - p) * w)
            moved += 1
        for (ob, vi), q in zip(items, new):
            ob.data.vertices[vi].co = ob.matrix_world.inverted() @ q
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.data.update()
    return moved


# ----------------------------------------------------------- emblem & plate
def build_emblem_and_plate(collection, lib):
    made = []
    # Nio Sky & Earth emblem on sloped upper Shark-Nose panel between DRLs
    emb = fittings.rounded_panel(
        "ES8_Emblem", (S.X_FRONT, 0.0, 0.902), 0.026, 0.019, 0.005,
        lambda p, d: face(p[1], p[2], d),
        S.X_FRONT, collection, lib["chrome"], d=0.0025, ny=14,
        outward=(0.82, 0.0, 0.57),
    )
    made.append(emb)

    # Front show plate aligned with the top of the trapezoidal lower grille
    p_pl, n_pl = face(0.0, 0.485, 0.002)
    made += fittings.plate(
        "ES8_Plate_Front", p_pl, n_pl, collection, lib, w=0.440, h=0.140,
        texts=[("NIO ES8", 0.0, 0.038, False, True)],
        mat="black_gloss", text_mat="machined",
    )
    return made


# ----------------------------------------------------------- Watchtower roof sensors
def build_watchtower(collection, lib):
    made = []
    # Central Aquila ultra-long-range LiDAR pod above windshield header
    cx = 0.460
    zc = S.Z_ROOF(cx) - 0.012
    made.append(fittings.lidar_pod(
        "ES8_Lidar", collection, lib["black_gloss"], cx, zc,
        a=0.075, b=0.112, c=0.042,
    ))
    # Two front corner 8MP Watchtower camera pods ("犄角" at y = +/- 0.49 m)
    cx_cam, cy_cam = 0.420, 0.490
    p_cam, _ = BODY.top_point(cx_cam, cy_cam, 0.0)
    z_cam = p_cam[2] - 0.006
    rows = []
    for dx, r_scale in ((-0.060, 0.35), (-0.020, 0.95), (0.028, 1.0), (0.050, 0.45)):
        x = cx_cam + dx
        row = []
        for ang in (-0.95, -0.45, 0.0, 0.45, 0.95):
            dy = 0.028 * r_scale * math.sin(ang)
            dz = 0.022 * r_scale * math.cos(ang)
            row.append((x, cy_cam + dy, z_cam + dz))
        rows.append(row)
    pod = M.grid("ES8_Watchtower_Cam", rows, collection, lib["black_gloss"],
                 geom.away_from((cx_cam, cy_cam, z_cam - 0.05)))
    M.solidify(pod, 0.004)
    M.mirror_y(pod)
    made.append(pod)
    made += lamps.projector(
        "ES8_Watchtower_Lens", (cx_cam + 0.044, cy_cam, z_cam + 0.007),
        (1.0, 0.0, 0.0), 0.010, collection, lib,
    )
    return made


def build_all(collection, lib):
    made = []
    made += build_fascia(collection, lib)
    made += build_chin(collection, lib)
    made += build_headlamps(collection, lib)
    made += build_emblem_and_plate(collection, lib)
    made += build_watchtower(collection, lib)
    return made
