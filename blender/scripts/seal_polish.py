"""BYD Seal cabin polish (2026-11-13): the parts that make the cabin read as assembled and engineered.

Added on top of the finished cabin (seal_interior_shell.main calls build() last):

    cluster     the instrument cluster stood proud of the dash band's glass (the glass bulged in front of the
                quad and hid its top rows) and framed by a glossy bezel collar
    collars     a 2 mm dark recess under every steering-wheel key, a collar where the screen's neck meets the
                shelf, and a shroud ring where the column meets the dash
    adas        the camera / sensor housing on the windscreen behind the frameless mirror
    wipers      the two blades parked at the foot of the windscreen
    belts       the B-pillar's belt loop and the retracted webbing under it, both sides
    icons       flat decal quads over the steering-wheel keys, the driver's window switches, the wireless charger
                pad and the selector's Park / Start / Hazard keys. They carry UVs into an 8 x 4 icon atlas that the
                web app draws (src/components/viewer/cabinfx/icons.ts: ICONS is the same list, in the same order)

Every step is guarded: a failure prints and the cabin still exports.
"""
import math

import bpy
from mathutils import Matrix, Vector

import seal_interior as ZI
import seal_wheel as SW
from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior import steering as ST
from carkit.interior.sweep import ellipse, grid_mesh, smooth_path, tube

# the atlas: 8 columns x 4 rows, row 0 at the top. Keep in step with icons.ts.
ICON_COLS, ICON_ROWS = 8, 4
ICONS = [
    "vol_plus", "vol_minus", "mute", "next", "voice", "phone", "cruise", "adas_distance",
    "lane", "arrow_up", "arrow_down", "win_up", "win_down", "lock", "fold", "hazard",
    "charger", "park", "start", "autohold", "regen", "defrost", "fan", "mode",
    "back", "ok", "camera", "horn", "boot", "child", "light", "unused",
]
MAT_NAME = "M_Icons"


def _guard(label, fn, *a):
    try:
        return fn(*a)
    except Exception as exc:  # noqa: BLE001 - a polish step must never stop the export
        import traceback
        print("seal_polish: %s failed: %r" % (label, exc))
        traceback.print_exc()
        return []


# ------------------------------------------------------------------ icons
def _icon_material():
    m = bpy.data.materials.get(MAT_NAME) or bpy.data.materials.new(MAT_NAME)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    for attr, val in (("surface_render_method", 'BLENDED'), ("blend_method", 'BLEND')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


def icon_quad(col, mat, name, centre, up, normal, size, icon):
    """A square decal of `size` metres lying on a surface: centred at `centre`, facing `normal`, its top toward `up`."""
    n = Vector(normal).normalized()
    u = (Vector(up) - n * Vector(up).dot(n)).normalized()
    r = u.cross(n)                       # right as the viewer in front of the surface sees it
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


def build_icons(col, lib):
    mat = _icon_material()
    made = []

    # ---- steering wheel: the keys stand 4 mm proud of the plate (the roller 5.5 mm)
    fr = ST.WheelFrame(ZI.WHEEL_C, ZI.WHEEL_TILT)
    up = Vector(fr.V)
    nrm = Vector(fr.A)
    lift = 0.0004
    layout = {
        "L": {"key": ["cruise", "adas_distance", "lane"], "small": ["arrow_up", "arrow_down"]},
        "R": {"key": ["vol_plus", "next", "vol_minus"], "small": ["voice", "phone"]},
    }
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        for j, (u, v) in enumerate(SW.LEFT_KEYS):
            uu = -u if side > 0 else u
            c = fr.p(uu, v, SW.PLATE_W1 + 0.0040 + lift)
            made.append(icon_quad(col, mat, "int_icon_wheel%s%d" % (tag, j), c, up, nrm, 0.0115, layout[tag]["key"][j]))
        for j, (u, v) in enumerate(SW.LEFT_SMALL):
            uu = -u if side > 0 else u
            c = fr.p(uu, v, SW.PLATE_W1 + 0.0040 + lift)
            made.append(icon_quad(col, mat, "int_icon_wheelS%s%d" % (tag, j), c, up, nrm, 0.0080, layout[tag]["small"][j]))

    # ---- wireless charger pad (flat on the felt) and the selector's keys
    import seal_console as SC
    xa, xb = SC.PAD_X
    zpad = SC.TOP(0.5 * (xa + xb)) - SC.PAD_DEPTH + 0.0015 + 0.00175 + lift
    made.append(icon_quad(col, mat, "int_icon_charger", (0.5 * (xa + xb) + 0.002, 0.0, zpad), (1.0, 0.0, 0.0),
                          (0.0, 0.0, 1.0), 0.050, "charger"))
    cx, cy = SC.DIAL_C
    z0 = SC.TOP(cx) - 0.0035
    names = ("Start", "Park", "AutoHold", "Regen", "Hazard", "Mode", "Defrost", "Fan")
    icons = {"Start": "start", "Park": "park", "AutoHold": "autohold", "Regen": "regen", "Hazard": "hazard"}
    for k, nm in enumerate(names):
        if nm not in icons:
            continue
        a = math.radians(SC_ANG0 + 38.0 * k + 2.0 + 17.0)
        rr = 0.5 * (0.028 + SC.DIAL_R - 0.006)
        c = (cx + rr * math.cos(a), cy + rr * math.sin(a), z0 + 0.0006 + 0.0016 + lift)
        made.append(icon_quad(col, mat, "int_icon_key" + nm, c, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.0130, icons[nm]))
    return made


SC_ANG0 = 28.0


def pack_icons(col, pre, n, up, at):
    """The driver's window switches and the lock / mirror-fold keys, in the card's own frame. seal_interior_doors.build_pack
    calls this with its frame (n toward the cabin, up, and `at(du, dv, lift)`), so the decals carry the card's name prefix
    and ride with the door in the web app."""
    mat = _icon_material()
    made = []
    for i, du in enumerate((-0.017, 0.017)):
        for j, (dv, ic) in enumerate(((0.012, "win_up"), (-0.012, "win_down"))):
            c = at(du, dv + (0.006 if i else -0.002), 0.0160)
            made.append(icon_quad(col, mat, pre + "Icon%d%d" % (i, j), c, up, n, 0.0095, ic))
    for j, (dv, ic) in enumerate(((0.015, "lock"), (-0.002, "fold"))):
        made.append(icon_quad(col, mat, pre + "IconS%d" % j, at(-0.060, dv, 0.0124), up, n, 0.0085, ic))
    return made


# ------------------------------------------------------------------ cluster
def fix_cluster(col, lib):
    """Stand the cluster's quad proud of the band glass, and frame it."""
    import mathutils.bvhtree as bvhtree
    quad = bpy.data.objects.get("screen_cluster")
    band = bpy.data.objects.get("int_dash_Band")
    if quad is None or band is None:
        print("seal_polish: cluster or band missing")
        return []
    t = ZI.CLUSTER_TILT
    n = Vector((-math.cos(t), 0.0, math.sin(t)))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = bvhtree.BVHTree.FromObject(band, dg)
    verts = [quad.matrix_world @ v.co for v in quad.data.vertices]
    a, b, c, d = verts[0], verts[1], verts[2], verts[3]
    worst = 0.0
    probe = 0.040
    for i in range(17):
        for j in range(7):
            p = a.lerp(b, i / 16.0).lerp(d.lerp(c, i / 16.0), j / 6.0)
            hit = bvh.ray_cast(p + n * probe, -n, probe * 2.0)
            if hit[0] is not None:
                worst = max(worst, probe - hit[3])      # how far the glass stands in front of the quad's plane
    print("seal_polish: the band's glass stands %.1f mm in front of the cluster plane" % (worst * 1000.0))
    lift = worst + 0.0016
    for v in quad.data.vertices:
        v.co += quad.matrix_world.inverted().to_3x3() @ (n * lift)
    quad.data.update()
    cx, cy, cz = ZI._cluster_centre()
    centre = Vector((cx, cy, cz)) + n * (lift - 0.0004)
    w, h = ZI.CLUSTER_W + 0.010, ZI.CLUSTER_H + 0.010
    bezel = F.slab("int_cluster_bezel", tuple(centre), w, h, 0.016, 0.008, t, col, lib["piano"])
    return [bezel]


# ------------------------------------------------------------------ collars
def build_collars(col, lib):
    made = []
    fr = ST.WheelFrame(ZI.WHEEL_C, ZI.WHEEL_TILT)
    k = 0
    # a recess of dark satin under every key, 2 mm wider than the cap, the edge a shadow seam
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        for (u, v) in SW.LEFT_KEYS:
            uu = -u if side > 0 else u
            made.append(SW._key(fr, col, lib, "int_wheel_collar%s%d" % (tag, k), uu, v, SW.PLATE_W1 - 0.0004,
                                0.034, 0.0205, mat="satin", h=0.0012))
            k += 1
        for (u, v) in SW.LEFT_SMALL:
            uu = -u if side > 0 else u
            made.append(SW._key(fr, col, lib, "int_wheel_collar%s%d" % (tag, k), uu, v, SW.PLATE_W1 - 0.0004,
                                0.018, 0.015, mat="satin", h=0.0012))
            k += 1
    # the screen's neck into the shelf: a flat dark collar
    ctr = ZI.SCREEN_C
    made.append(F.box(col, "int_screen_collar", (ctr[0] + 0.016, 0.0, 0.8985), (0.050, 0.044, 0.0035),
                      lib["satin"], r=0.0012))
    return made


# ------------------------------------------------------------------ housing and wipers
def build_adas(col, lib):
    made = []
    x0 = ZI.MIRROR_C[0] + 0.082
    za = ZI.z_glass(x0 - 0.025, 0.0)
    zb = ZI.z_glass(x0 + 0.025, 0.0)
    pitch = math.atan2(za - zb, 0.050)
    zc = 0.5 * (za + zb) - 0.016
    made.append(F.box(col, "int_adas_housing", (x0, 0.0, zc), (0.056, 0.140, 0.030), lib["satin"], r=0.009, pitch=pitch))
    made.append(F.box(col, "int_adas_visor", (x0 + 0.020, 0.0, zc - 0.012), (0.026, 0.084, 0.010), lib["piano"], r=0.004,
                      pitch=pitch))
    for k, y in enumerate((-0.030, 0.030)):
        made += F.disc(col, "int_adas_lens%d" % k, (x0 + 0.030, y, zc - 0.014), (0.9, 0.0, -0.4), 0.0085,
                       lib["screen_glass"], dome=0.0012, rim=0.0010, rim_mat=lib["gunmetal"])
    return made


def build_wipers(col, lib):
    made = []
    mat = lib.get("rubber") or lib["satin"]
    x = 1.012
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        ys = [side * (0.060 + 0.560 * k / 14.0) for k in range(15)]
        path = [(x, y, ZI.z_glass(x, y) + 0.0105) for y in ys]
        made.append(tube("int_wiper_blade" + tag, path, ellipse(0.0125, 0.0036, 8), col, mat, lateral=(1.0, 0.0, 0.0)))
        # the arm: a thin bar from the blade's inner end to its pivot under the cowl
        arm = smooth_path([(x + 0.002, side * 0.075, ZI.z_glass(x, side * 0.075) + 0.0125),
                           (x + 0.030, side * 0.060, ZI.z_glass(x + 0.030, side * 0.060) + 0.0140),
                           (x + 0.062, side * 0.050, ZI.z_glass(x + 0.062, side * 0.050) + 0.0100)], 8)
        made.append(tube("int_wiper_arm" + tag, arm, ellipse(0.0042, 0.0020, 6), col, lib["satin"],
                         lateral=(1.0, 0.0, 0.0)))
    return made


# ------------------------------------------------------------------ belts
def build_belts(col, lib):
    """The B-pillar's belt loop (a D-ring plate) and, under it, the retracted webbing: a dark strip 47 mm wide
    lying against the pillar down to the retractor's slot."""
    import seal_interior_doors as DR
    from carkit.interior import cabin as CB
    import seal_surface as S
    import seal_panels as PN
    made = []
    mat = lib.get("rubber") or lib["satin"]
    xb = DR.X_B - 0.060
    vh = DR._v_top_front() + 0.10
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        def ypos(z):
            return CB.skin_offset_y(S.BODY, xb, z, 0.030, vh) - 0.004
        zt, zb = 1.060, 0.640
        zs = [zb + (zt - zb) * k / 12.0 for k in range(13)]
        rows = []
        for xx in (xb - 0.0235, xb + 0.0235):
            rows.append([(xx, side * ypos(z), z) for z in zs])
        web = grid_mesh("int_belt_web" + tag, rows, col, mat)
        M.orient(web.data, lambda c, s=side: (0.0, -s, 0.0))
        made.append(web)
        # the loop: a rounded plate and the bar the webbing runs through
        made.append(F.box(col, "int_belt_loop" + tag, (xb, side * (ypos(zt + 0.012) - 0.002), zt + 0.012),
                          (0.010, 0.006, 0.062), lib["gunmetal"], r=0.0025))
        made.append(F.box(col, "int_belt_slot" + tag, (xb, side * (ypos(zb - 0.006) - 0.001), zb - 0.006),
                          (0.062, 0.004, 0.012), lib["satin"], r=0.0025))
    return made


# --------------------------------------------------------------------- build
def build(col, lib):
    made = []
    made += _guard("cluster", fix_cluster, col, lib)
    made += _guard("collars", build_collars, col, lib)
    made += _guard("adas", build_adas, col, lib)
    made += _guard("wipers", build_wipers, col, lib)
    made += _guard("belts", build_belts, col, lib)
    made += _guard("icons", build_icons, col, lib)
    print("seal_polish: %d objects" % len(made))
    return made
