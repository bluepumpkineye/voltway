"""The bumper kit: fascia regions cut from the nose and tail caps.

Most modern fronts and rears decompose into the same few pieces. From the SU7:

    split_nose      painted upper fascia above a split height; painted cheeks
                    outboard of a fence line; a RECESSED mouth between the
                    cheeks set back behind the lip, with intakes cut through it
    mouth_walls     return walls closing the step - under the lip, and the
                    inner face of each fence - so the mouth reads as a mouth,
                    not a two-tone paint split
    intake_tunnel   a tapered tunnel with a floor behind each intake opening
    blade           a painted lip standing on the mouth under an intake
    cap_panel       any other region of a cap as its own panel
    valance         a lower panel standing proud of the cap, with a top edge
                    that can vary across the car, and its return wall

Outlines are front-elevation (y, z) loops on the LEFT half; an opening that
crosses the centreline should use geom.round_rect(open_inboard=True).
"""
from .. import cut
from .. import geom
from .. import mesh as M
from .panels import cap_rows


def cut_elevation(ob, outlines, x_front, x_back):
    """Boolean front-elevation outlines through a half sheet (before mirror).

    The material must already be on the sheet (it is kept). Returns
    (faces before, faces after).
    """
    cutters = [cut.prism_x("_cut_%s_%d" % (ob.name, k), outline, x_front, x_back)
               for k, outline in enumerate(outlines)]
    return cut.difference(ob, cutters, "cut_", reset_materials=False)


def split_nose(prefix, cap, collection, lib, z_split, w_fence, recess,
               intakes=(), x_cut=None, grid=(34, 40, 36, 10, 36, 44),
               mats=("paint", "paint", "black_gloss"), thickness=(M.SKIN, M.SKIN, 0.0025),
               names=("_Upper", "_Cheek", "_U"), log=True):
    """Upper fascia, cheeks and a recessed mouth with intakes cut through it.

    Returns (upper, cheek, mouth, vs_cheek) - vs_cheek are the cheek's row
    parameters, which mouth_walls needs for the fence wall.
    grid = (upper nz, upper nw, lower nz, cheek nw, mouth nz, mouth nw).
    """
    zl, zh = cap.Z_LO, cap.Z_HI
    sign = 1.0 if cap.front else -1.0
    nz_u, nw_u, nz_l, nw_c, nz_m, nw_m = grid

    rows, _ = cap_rows(cap, z_split, zh - 0.0008, 0.0, 1.0, nz_u, nw_u,
                       top_to_centre=True)
    up = M.mesh_from_rows(prefix + names[0], rows, collection)
    M.orient(up.data, geom.axial(sign))
    up.data.materials.append(lib[mats[0]])
    M.mirror_y(up)
    M.finish(up, thickness=thickness[0], bevel=0.0)

    rows, vs_lo = cap_rows(cap, zl + 0.0008, z_split, w_fence, 1.0, nz_l, nw_c)
    ch = M.mesh_from_rows(prefix + names[1], rows, collection)
    M.orient(ch.data, geom.axial(sign))
    ch.data.materials.append(lib[mats[1]])
    M.mirror_y(ch)
    M.finish(ch, thickness=thickness[1], bevel=0.0)

    rows, _ = cap_rows(cap, zl + 0.0008, z_split, 0.0, w_fence, nz_m, nw_m,
                       offset=-recess)
    u = M.mesh_from_rows(prefix + names[2], rows, collection)
    M.orient(u.data, geom.axial(sign))
    u.data.materials.append(lib[mats[2]])
    if intakes:
        if x_cut is None:
            L = cap.loft.HALF_L
            x_cut = (L + 0.39, L - 0.86) if cap.front else (-L - 0.39, -L + 0.86)
        before, after = cut_elevation(u, list(intakes), x_cut[0], x_cut[1])
        if log:
            print("  %s: %d -> %d faces after intake cuts" % (u.name, before, after))
    M.mirror_y(u)
    M.finish(u, thickness=thickness[2], bevel=0.0)
    return up, ch, u, vs_lo


def mouth_walls(prefix, cap, collection, lib, z_split, w_fence, recess, vs_cheek,
                n=40, mat="paint", names=("_LipWall", "_FenceWall")):
    """Return walls under the painted lip and on the inner face of each fence."""
    made = []
    v_s = cap.v_at_z(z_split, 0.0)
    ws = [w_fence * i / float(n) for i in range(n + 1)]
    a = [cap.point(w, v_s) for w in ws]
    b = [cap.offset(w, v_s, -recess) for w in ws]
    lip = M.strip(prefix + names[0], a, b, collection, lib[mat])
    M.mirror_y(lip)
    made.append(lip)

    a = [cap.point(w_fence, v) for v in vs_cheek]
    b = [cap.offset(w_fence, v, -recess) for v in vs_cheek]
    fence = M.strip(prefix + names[1], a, b, collection, lib[mat])
    M.mirror_y(fence)
    made.append(fence)
    return made


def intake_tunnel(name, outline, collection, mat, cap=None, x_surface=None,
                  depth=0.10, taper=0.94, lip=0.004):
    """Tunnel back from an intake outline, tapering, closed by a floor.

    x_surface(y, z) gives the depth of the surface the opening is cut in
    (default: the cap itself). Give the tunnel an unlit material - a satin
    wall catches the key light and the mouth reads as a flat panel.
    """
    front = cap.front if cap is not None else True
    sgn = 1.0 if front else -1.0
    cy = sum(p[0] for p in outline) / len(outline)
    cz = sum(p[1] for p in outline) / len(outline)
    ring0 = []
    for (y, z) in outline:
        x = x_surface(y, z) if x_surface else cap.x_at(max(0.0, y), z)
        ring0.append((x + sgn * lip, y, z))
    rows = [ring0]
    for t in (0.5, 1.0):
        k = 1.0 + (taper - 1.0) * t
        rows.append([(p[0] - sgn * depth * t, cy + (p[1] - cy) * k,
                      cz + (p[2] - cz) * k) for p in ring0])
    xf = min(p[0] for p in rows[-1]) if front else max(p[0] for p in rows[-1])
    rows.append([(xf, cy + (p[1] - cy) * 0.02, cz + (p[2] - cz) * 0.02)
                 for p in rows[-1]])
    ob = M.mesh_from_rows(name, rows, collection)
    ob.data.materials.append(mat)
    return ob


def recessed_x(cap, recess):
    """x_surface for tunnels cut in a recessed mouth: the cap set back.
    `recess` may be a function of w (a panel whose stand varies)."""
    def f(y, z):
        w, v = cap.wv_at(max(0.0, y), z)
        return cap.offset(w, v, -(recess(w) if callable(recess) else recess))[0]
    return f


def blade(name, cap, collection, lib, w0, w1, top, z_bottom=None, nw=24, nz=6,
          mat="paint", wall=True, recess=None, thickness=M.SKIN):
    """A painted lip on the cap between w0 and w1, from z_bottom up to top(w).

    With `recess` set, a return wall runs from its top edge back to the
    recessed mouth behind it. Returns [blade, wall].
    """
    sign = 1.0 if cap.front else -1.0
    zl = cap.Z_LO if z_bottom is None else z_bottom
    rows = []
    for i in range(nw + 1):
        w = w0 + (w1 - w0) * i / float(nw)
        ztop = top(w)
        col = []
        for k in range(nz + 1):
            z = (zl + 0.0008) + (ztop - zl - 0.0008) * k / float(nz)
            col.append(cap.point(w, cap.v_at_z(z, w)))
        rows.append(col)
    bl = M.mesh_from_rows(name, rows, collection)
    M.orient(bl.data, geom.axial(sign))
    bl.data.materials.append(lib[mat])
    M.mirror_y(bl)
    M.finish(bl, thickness=thickness, bevel=0.0)
    made = [bl]
    if wall and recess:
        tops = [rows[i][-1] for i in range(nw + 1)]
        back = [cap.offset(w0 + (w1 - w0) * i / float(nw),
                           cap.v_at_z(tops[i][2], w0 + (w1 - w0) * i / float(nw)),
                           -recess) for i in range(nw + 1)]
        bw = M.strip(name + "Wall", tops, back, collection, lib[mat])
        M.mirror_y(bw)
        made.append(bw)
    return made


def cap_panel(name, cap, collection, lib, z_lo, z_hi, w_lo=0.0, w_hi=1.0, nz=34,
              nw=40, mat="paint", top_to_centre=False, offset=0.0,
              thickness=M.SKIN, cuts=()):
    """A region of a cap as its own finished panel.

    `cuts` are functions of the half sheet run before the material goes on
    (they must reset materials - carkit.cut.difference(reset_materials=True)).
    """
    sign = 1.0 if cap.front else -1.0
    rows, _ = cap_rows(cap, z_lo, z_hi, w_lo, w_hi, nz, nw, offset=offset,
                       top_to_centre=top_to_centre)
    ob = M.mesh_from_rows(name, rows, collection)
    M.orient(ob.data, geom.axial(sign))
    for fn in cuts:
        fn(ob)
    ob.data.materials.append(lib[mat])
    M.mirror_y(ob)
    M.finish(ob, thickness=thickness, bevel=0.0)
    return ob


def valance(name, cap, collection, lib, z_top, stand=0.010, z_bottom=None,
            nw=40, nz=24, mat="black_gloss", thickness=0.0030, cuts=(), wall=True):
    """A lower panel standing `stand` proud of the cap, with a return wall.

    z_top(w) is its top edge across the car - it may drop at the corners so
    body colour shows round a vent. `stand` may be a function of w too, to
    run the panel down onto the flank where it meets a sill trim instead of
    ending in a step. Returns [valance, wall].
    """
    sign = 1.0 if cap.front else -1.0
    zl = cap.Z_LO if z_bottom is None else z_bottom
    st = stand if callable(stand) else (lambda w, s=stand: s)
    # columns packed toward the joint, as cap_rows packs the painted cap's:
    # the wrap turns hardest there. Evenly spaced, the SU7's last column
    # spanned 50 mm of the corner as a flat chord that dipped under the paint
    # behind it, and a yellow tab showed through the bumper under each vent.
    ws = [1.0 - (1.0 - i / float(nw)) ** 1.35 for i in range(nw + 1)]
    rows = []
    for w in ws:
        zt = z_top(w) - 0.0008
        col = []
        for k in range(nz + 1):
            z = (zl + 0.0008) + (zt - zl - 0.0008) * k / float(nz)
            col.append(cap.offset(w, cap.v_at_z(z, w), st(w)))
        rows.append(col)
    val = M.mesh_from_rows(name, rows, collection)
    M.orient(val.data, geom.axial(sign))
    for fn in cuts:
        fn(val)
    val.data.materials.append(lib[mat])
    M.mirror_y(val)
    M.finish(val, thickness=thickness, bevel=0.0)
    made = [val]
    if wall:
        a_pts, b_pts = [], []
        for w in ws:
            v = cap.v_at_z(z_top(w) - 0.0008, w)
            a_pts.append(cap.point(w, v))
            b_pts.append(cap.offset(w, v, st(w)))
        wl = M.strip(name + "Wall", a_pts, b_pts, collection, lib[mat])
        M.mirror_y(wl)
        made.append(wl)
    return made
