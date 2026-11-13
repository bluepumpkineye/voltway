"""Shared Blender-side interior polish: the parts of the BYD Seal's gold-standard pass that every car reuses.

A car's own module (seal_polish.py is the reference) knows where its keys, trays and screens are; this module knows HOW to
polish them, so none of it is written twice:

    remove_helpers(col)          delete leftover curve / wire / cutter helpers, apply unapplied modifiers (booleans)
    bevel_hard_surfaces(...)     Bevel (2 segments, 1.5-2.5 mm, angle limited, clamped) + Weighted Normal, applied
    shade_smooth(...)            smooth shading for hero curves (rim, stalks, handles, speaker rings)
    collar_loop / tray_path      a thin dark collar (2 mm) where one part meets another: the shadow seam
    icon_quad(...)               a flat decal square whose UVs point into the shared 8 x 4 icon atlas
    glow_ribbon(...)             a soft strip of ambient spill laid on the leather next to a light guide
    export_names_ok(...)         check the material names the web's upgrader expects are present and unique

Names the web app relies on (src/components/viewer/cabinfx/):
    materials   INT_Leather_*, INT_Headliner / INT_Suede_* / INT_Alcantara, INT_Piano_Black, INT_Chrome, INT_Brushed,
                INT_Screen_Glass, INT_Display_screen_cluster, INT_Ambient      (classified by cabinfx/materials.ts kindOf)
    decals      M_Icons   (UVs into the atlas, ICONS below == cabinfx/icons.ts ICONS, same order)
    spill       M_Glow    (UV v 0 at the light guide, 1 at the edge of the spill)

Every function is safe to call on a collection that lacks what it looks for.
"""
import math
import re

import bpy
from mathutils import Vector

# the 8 x 4 icon atlas, row 0 at the top. Keep in step with src/components/viewer/cabinfx/icons.ts.
ICON_COLS, ICON_ROWS = 8, 4
ICONS = [
    "vol_plus", "vol_minus", "mute", "next", "voice", "phone", "cruise", "adas_distance",
    "lane", "arrow_up", "arrow_down", "win_up", "win_down", "lock", "fold", "hazard",
    "charger", "park", "start", "autohold", "regen", "defrost", "fan", "mode",
    "back", "ok", "camera", "horn", "boot", "child", "light", "unused",
]
ICON_MAT = "M_Icons"
GLOW_MAT = "M_Glow"


def guard(label, fn, *a, **k):
    """Run a polish step; a failure prints and returns [] so the cabin still exports."""
    try:
        return fn(*a, **k) or []
    except Exception as exc:  # noqa: BLE001 - a polish step must never stop an export
        import traceback
        print("polish: %s failed: %r" % (label, exc))
        traceback.print_exc()
        return []


# ------------------------------------------------------------------ helpers
def remove_helpers(col):
    """Delete what a build leaves behind that is not part of the cabin: Bezier / surface helpers, wire or bounds objects
    (cutters and guides), and apply any modifier still on a mesh (unapplied booleans). Returns the names it removed."""
    gone = []
    for ob in list(col.objects):
        helper = ob.type in {"CURVE", "SURFACE", "META", "LATTICE", "GPENCIL", "ARMATURE"} or (
            ob.type == "MESH" and ob.display_type in {"WIRE", "BOUNDS"})
        if helper:
            gone.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    from carkit import mesh as M
    bpy.context.view_layer.update()
    for ob in col.objects:
        if ob.type == "MESH" and ob.modifiers:
            # only a boolean is a leftover: Mirror / Bevel stacks are the build's own and the export applies them
            if any(m.type == "BOOLEAN" for m in ob.modifiers):
                M.apply_modifiers(ob)
    return gone


def shade_smooth(col, pattern):
    """Smooth shading on the objects whose name matches `pattern`; returns how many."""
    rx = re.compile(pattern)
    n = 0
    for ob in col.objects:
        if ob.type == "MESH" and rx.search(ob.name):
            for p in ob.data.polygons:
                p.use_smooth = True
            n += 1
    return n


def bevel_hard_surfaces(col, pattern, width=0.002, segments=2, angle=35.0):
    """Bevel (angle limited, overlap clamped) then Weighted Normal (keep sharp) on the objects whose name matches
    `pattern`, applied so the export carries real geometry. Returns the objects done."""
    from carkit import mesh as M
    rx = re.compile(pattern)
    done = []
    bpy.context.view_layer.update()
    for ob in list(col.objects):
        if ob.type != "MESH" or not rx.search(ob.name) or len(ob.data.polygons) < 4:
            continue
        for m in [m for m in ob.modifiers if m.type in {"BEVEL", "WEIGHTED_NORMAL"}]:
            ob.modifiers.remove(m)
        b = ob.modifiers.new("PolishBevel", "BEVEL")
        b.width = width
        b.segments = segments
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(angle)
        b.use_clamp_overlap = True
        try:
            b.harden_normals = True
        except Exception:
            pass
        w = ob.modifiers.new("PolishWeighted", "WEIGHTED_NORMAL")
        w.mode = "FACE_AREA_WITH_ANGLE"
        w.weight = 50
        w.keep_sharp = True
        w.thresh = 0.01
        M.apply_modifiers(ob)
        done.append(ob)
    return done


def rounded_rect_path(x0, x1, y0, y1, z_of, r=0.012, n=6):
    """A closed rounded-rectangle loop of 3D points in plan (x, y), at height z_of(x, y): the outline of a tray."""
    pts = []
    for (cx, cy, a0) in ((x1 - r, y1 - r, 0.0), (x0 + r, y1 - r, 90.0), (x0 + r, y0 + r, 180.0), (x1 - r, y0 + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            pts.append((x, y, z_of(x, y)))
    pts.append(pts[0])
    return pts


def collar_loop(col, name, path, mat, rx=0.0022, ry=0.0012, lateral=(0.0, 0.0, 1.0)):
    """A thin collar swept along a closed path: a dark seam round a tray, a screen mount or a column."""
    from carkit.interior.sweep import ellipse, tube
    return tube(name, path, ellipse(rx, ry, 8), col, mat, lateral=lateral, closed=True)


# ------------------------------------------------------------------ materials
def _plain_material(name, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


def icon_material():
    return _plain_material(ICON_MAT, 0.5)


def glow_material():
    return _plain_material(GLOW_MAT, 0.8)


# ------------------------------------------------------------------ decals
def icon_quad(col, mat, name, centre, up, normal, size, icon):
    """A square decal of `size` metres lying on a surface: centred at `centre`, facing `normal`, its top toward `up`, its
    UVs on the atlas cell of `icon` (an entry of ICONS)."""
    n = Vector(normal).normalized()
    u = (Vector(up) - n * Vector(up).dot(n)).normalized()
    r = u.cross(n)                       # right, as a viewer in front of the surface sees it
    c = Vector(centre)
    h = size / 2.0
    verts = [c - r * h - u * h, c + r * h - u * h, c + r * h + u * h, c - r * h + u * h]
    idx = ICONS.index(icon)
    cx, cy = idx % ICON_COLS, idx // ICON_COLS
    pad = 0.04 / ICON_COLS
    u0, u1 = cx / ICON_COLS + pad, (cx + 1) / ICON_COLS - pad
    v1, v0 = 1.0 - cy / ICON_ROWS - pad / 2, 1.0 - (cy + 1) / ICON_ROWS + pad / 2
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [[0, 1, 2, 3]])
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for li, (a, b) in zip(me.polygons[0].loop_indices, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        uv.data[li].uv = (a, b)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    me.materials.append(mat)
    return ob


def place_icons(col, layout):
    """layout: [(name, centre, up, normal, size, icon), ...] -> the quads. One call places a car's whole button set."""
    mat = icon_material()
    return [icon_quad(col, mat, nm, c, up, n, size, ic) for (nm, c, up, n, size, ic) in layout]


# ------------------------------------------------------------------ spill
def glow_ribbon(col, name, rows):
    """A soft ribbon of ambient spill. `rows` are lists of points (equal length): row 0 lies against the light guide, the last
    row is where the glow has faded out; UV v runs 0 -> 1 across them, u along. The web draws it additively in the ambient
    colour with a gradient (cabinfx/icons.ts useGlowRibbons)."""
    nr, nc = len(rows), len(rows[0])
    verts = [tuple(p) for r in rows for p in r]
    faces = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            a, b = i * nc + j, (i + 1) * nc + j
            faces.append([a, a + 1, b + 1, b])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi % nc) / max(1, nc - 1), (vi // nc) / max(1, nr - 1))
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    me.materials.append(glow_material())
    return ob


def finish_decals(col):
    """Join the decal quads and glow ribbons into a few objects that the export keeps APART from the cabin's merge, named
    `decal_<where>` and flagged `decal`:

        decal_int_door_L (..R, int_rdoor_L, ..)   the icons on that door card: the web re-parents the node under the card's own
                                                   node, so they swing with the door
        decal_cabin                                every other icon (wheel, console, boot)
        decal_glow                                 the ambient spill ribbons

    Why apart: the AO atlas bake would otherwise treat a decal 0.4 mm over a surface as an occluder and darken a square of the
    surface under it (carkit.aoatlas skips flagged objects and hides them from the rays), and `cabin_tools.export_interior`
    keeps them out of the merge (it adds them to `protected`)."""
    from carkit.export import join
    groups = {}
    for ob in list(col.objects):
        if ob.type != "MESH" or not ob.data.materials:
            continue
        mats = {m.name for m in ob.data.materials if m}
        if mats and mats <= {ICON_MAT, GLOW_MAT}:
            m = re.match(r"^(int_r?door_[LR])_", ob.name)
            key = m.group(1) if m else ("glow" if mats == {GLOW_MAT} else "cabin")
            groups.setdefault(key, []).append(ob.name)
    out = []
    for key, names in groups.items():
        ob = join("decal_" + key, names)
        if ob is not None:
            ob["decal"] = True
            out.append(ob)
    print("bpy_interior_polish: decals -> %s" % ", ".join("%s(%d)" % (o.name, len(o.data.polygons)) for o in out))
    return out


# ------------------------------------------------------------------ checks
# (INT_Display_screen_cluster is made later, by cabin_screens, at export)
EXPECTED = ("INT_Piano_Black", "INT_Chrome", "INT_Screen_Glass", "INT_Ambient")


def export_names_ok():
    """Print which of the materials the web upgrader expects are missing (a car may legitimately lack some)."""
    have = {m.name for m in bpy.data.materials}
    missing = [n for n in EXPECTED if n not in have]
    if missing:
        print("polish: materials the web upgrader expects but this car lacks: %s" % ", ".join(missing))
    return missing


def polish(col, bevel_pattern=None, smooth_pattern=None, width=0.002):
    """The generic pass for any car's cabin collection: helper cleanup, smooth hero curves, bevel + weighted normals."""
    out = {}
    out["removed"] = guard("remove_helpers", remove_helpers, col)
    if smooth_pattern:
        out["smoothed"] = guard("shade_smooth", shade_smooth, col, smooth_pattern)
    if bevel_pattern:
        out["bevelled"] = [o.name for o in guard("bevel", bevel_hard_surfaces, col, bevel_pattern, width)]
    out["decals"] = guard("finish_decals", finish_decals, col)
    export_names_ok()
    print("bpy_interior_polish: removed %d helpers, smoothed %s, bevelled %d" % (
        len(out["removed"]), out.get("smoothed"), len(out.get("bevelled", []))))
    return out
