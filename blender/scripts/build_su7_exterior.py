"""Parametric Xiaomi SU7 Ultra exterior.

Real dimensions: 5115 x 1970 x 1465 mm, 3000 mm wheelbase.
Axes: +X front, +Y left, +Z up, origin on the ground at the car's centre.
"""
import bpy
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else r"C:\Users\User\Documents\4 - Website_ WebApp Project\Chinese EV Configurator\blender\scripts"
if _HERE not in sys.path:
    sys.path.append(_HERE)

import lib_build as L
import parts_su7 as P
import importlib
importlib.reload(L)
importlib.reload(P)

# ------------------------------------------------------------------ constants
LENGTH, WIDTH, HEIGHT = 5.115, 1.970, 1.465
HALF_L = LENGTH / 2.0
FRONT_AXLE = 1.5575          # 1000 mm front overhang
REAR_AXLE = -1.4425          # 1115 mm rear overhang
WHEEL_R = 0.362              # 21" rim + 35-series tyre
TYRE_W_F, TYRE_W_R = 0.265, 0.305

RING = 56                    # points around each cross-section
STATIONS = 78                # slices along the body

# --------------------------------------------------------------- body profile
# Each is a list of (x, value) control points, front to rear.
Z_TOP = [
    (-HALF_L, 0.988), (-2.36, 1.046), (-2.10, 1.108), (-1.78, 1.192),
    (-1.34, 1.318), (-0.88, 1.428), (-0.36, 1.465), (0.00, 1.452),
    (0.30, 1.404), (0.62, 1.286), (0.80, 1.152), (1.02, 1.062),
    (1.34, 1.020), (1.5575, 0.998), (1.92, 0.948), (2.22, 0.882),
    (2.40, 0.820), (HALF_L, 0.716),
]
Z_BOT = [
    (-HALF_L, 0.430), (-2.30, 0.246), (-1.98, 0.186), (-1.4425, 0.156),
    (0.00, 0.146), (1.5575, 0.158), (2.02, 0.196), (2.32, 0.258),
    (HALF_L, 0.352),
]
W_MAX = [
    (-HALF_L, 0.742), (-2.34, 0.852), (-2.02, 0.926), (-1.72, 0.968),
    (-1.4425, 0.985), (-1.06, 0.972), (-0.40, 0.958), (0.36, 0.952),
    (1.02, 0.962), (1.5575, 0.985), (1.86, 0.968), (2.16, 0.918),
    (2.38, 0.836), (HALF_L, 0.612),
]
Z_BELT = [
    (-HALF_L, 0.700), (-2.10, 0.716), (-1.4425, 0.688), (-0.40, 0.700),
    (0.60, 0.696), (1.5575, 0.652), (2.16, 0.606), (HALF_L, 0.566),
]
W_TOP = [
    (-HALF_L, 0.586), (-2.36, 0.702), (-2.12, 0.782), (-1.80, 0.760),
    (-1.36, 0.668), (-0.90, 0.578), (-0.36, 0.566), (0.10, 0.586),
    (0.42, 0.634), (0.66, 0.706), (0.86, 0.772), (1.16, 0.818),
    (1.5575, 0.806), (1.94, 0.752), (2.22, 0.650), (2.40, 0.548),
    (HALF_L, 0.360),
]


_C_ZTOP = L.Curve(Z_TOP)
_C_ZBOT = L.Curve(Z_BOT)
_C_WMAX = L.Curve(W_MAX)
_C_ZBELT = L.Curve(Z_BELT)
_C_WTOP = L.Curve(W_TOP)


def half_section(x):
    """Return the +Y half of the cross-section at station x, bottom to top."""
    zb = _C_ZBOT(x)
    zt = _C_ZTOP(x)
    wm = _C_WMAX(x)
    zbelt = _C_ZBELT(x)
    wt = _C_WTOP(x)
    zbelt = min(max(zbelt, zb + 0.05), zt - 0.05)

    key = [
        (0.0, zb),
        (wm * 0.42, zb + 0.004),
        (wm * 0.88, zb + (zbelt - zb) * 0.34),
        (wm, zbelt),
        (wm * 0.52 + wt * 0.48, zbelt + (zt - zbelt) * 0.54),
        (wt * 1.015, zt - (zt - zbelt) * 0.12),
        (wt * 0.62, zt - (zt - zbelt) * 0.012),
        (0.0, zt),
    ]
    return L.catmull_rom(key, RING)


def ring_at(x):
    """Closed cross-section ring (mirrored), as 3D points."""
    half = half_section(x)
    pts = [(x, y, z) for (y, z) in half]
    # mirror back down the -Y side, skipping the two shared poles
    for (y, z) in reversed(half[1:-1]):
        pts.append((x, -y, z))
    return pts


def build_body(col):
    # cluster stations toward the ends, where curvature is highest
    xs = []
    for i in range(STATIONS):
        u = i / (STATIONS - 1.0)
        u = 0.5 - 0.5 * math.cos(math.pi * u)
        xs.append(HALF_L - LENGTH * u)          # front to rear
    stations = [ring_at(x) for x in xs]
    ob = L.loft(stations, col, "SU7_Body", cap_front=True, cap_rear=True)
    L.merge_doubles(ob, 0.0006)
    cut_wheel_arches(ob, col)
    L.merge_doubles(ob, 0.0006)
    L.shade_smooth(ob)
    L.add_subsurf(ob, levels=1, render_levels=2)
    return ob


def _arch_cutter(col, name, cx, sgn):
    """Half-cylinder along Y that carves an arch recess into one flank only."""
    seg = 48
    r = WHEEL_R + 0.052
    y_in, y_out = 0.60, WIDTH / 2 + 0.12
    verts, faces = [], []
    for y in (sgn * y_in, sgn * y_out):
        base = len(verts)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((cx + r * math.cos(a), y, WHEEL_R + r * math.sin(a)))
        c = len(verts)
        verts.append((cx, y, WHEEL_R))
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([base + i, base + j, c])
    off = seg + 1
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([i, j, off + j, off + i])
    ob = L.new_mesh_object(name, verts, faces, col)
    L.merge_doubles(ob, 0.0005)
    return ob


def cut_wheel_arches(body, col):
    cutters = []
    for tag, cx in (("F", FRONT_AXLE), ("R", REAR_AXLE)):
        for side, sgn in (("L", 1), ("R", -1)):
            cutters.append(_arch_cutter(col, f"_cut_{tag}{side}", cx, sgn))
    for c in cutters:
        m = body.modifiers.new(f"arch_{c.name}", 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
        m.object = c
    # bake the booleans down so the export is a plain mesh
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
    old = body.data
    body.modifiers.clear()
    body.data = baked
    if old.users == 0:
        bpy.data.meshes.remove(old)
    for c in cutters:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    return body


# ------------------------------------------------------------------- wheels
def build_wheels(col):
    made = []
    for sgn, side in ((1, "L"), (-1, "R")):
        made += P.build_wheel_assembly(
            col, "SU7_W_F" + side, FRONT_AXLE,
            sgn * (WIDTH / 2 - TYRE_W_F / 2 - 0.030), sgn, WHEEL_R, TYRE_W_F)
        made += P.build_wheel_assembly(
            col, "SU7_W_R" + side, REAR_AXLE,
            sgn * (WIDTH / 2 - TYRE_W_R / 2 - 0.018), sgn, WHEEL_R, TYRE_W_R)
    return made


# ---------------------------------------------------------------- materials
def build_materials():
    return {
        "paint": L.make_material("SU7_Paint", (0.784, 0.588, 0.020),
                                 roughness=0.215, metallic=0.70, coat=1.0),
        "glass": L.make_material("SU7_Glass", (0.022, 0.026, 0.032),
                                 roughness=0.045, metallic=0.0,
                                 transmission=0.88, ior=1.52),
        "carbon": L.make_material("SU7_Carbon", (0.017, 0.017, 0.019),
                                  roughness=0.255, metallic=0.30, coat=0.85),
        "gloss_black": L.make_material("SU7_GlossBlack", (0.010, 0.010, 0.012),
                                       roughness=0.105, metallic=0.0, coat=1.0),
        "tyre": L.make_material("SU7_Tyre", (0.0165, 0.0165, 0.018), roughness=0.815),
        "rim": L.make_material("SU7_Rim", (0.028, 0.028, 0.031),
                               roughness=0.235, metallic=0.88, coat=0.4),
        "disc": L.make_material("SU7_Disc", (0.155, 0.152, 0.150),
                                roughness=0.375, metallic=0.92),
        "caliper": L.make_material("SU7_Caliper", (0.760, 0.545, 0.055),
                                   roughness=0.315, metallic=0.55),
        "head": L.make_material("SU7_HeadLamp", (0.72, 0.76, 0.82), roughness=0.075,
                                transmission=0.55, ior=1.5,
                                emission=(0.85, 0.90, 1.0), emission_strength=2.4),
        "tail": L.make_material("SU7_TailLamp", (0.42, 0.030, 0.030), roughness=0.115,
                                transmission=0.35, ior=1.5,
                                emission=(1.0, 0.055, 0.045), emission_strength=3.1),
    }


def apply_materials(mats):
    def pick(name):
        n = name.lower()
        if "_tyre" in n:
            return mats["tyre"]
        if "_rim" in n or "_spoke" in n:
            return mats["rim"]
        if "_disc" in n:
            return mats["disc"]
        if "_caliper" in n:
            return mats["caliper"]
        if "glass" in n:
            return mats["glass"]
        if "headlight" in n:
            return mats["head"]
        if "taillight" in n or "rearrefl" in n:
            return mats["tail"]
        if any(k in n for k in ("splitter", "skirt", "diffuser", "wing")):
            return mats["carbon"]
        if "mirror" in n:
            return mats["gloss_black"] if "pod" in n else mats["carbon"]
        return mats["paint"]

    col = bpy.data.collections["SU7_Exterior"]
    for ob in col.objects:
        L.assign(ob, pick(ob.name))


def body_y_at(x, z):
    """Half-width of the body at station x and height z.

    w_max is the width at the beltline, so anchoring a rocker-height part to it
    leaves the part hanging outside the bodywork. This walks the actual section
    and returns the widest y that the surface reaches at the requested height.
    """
    sec = half_section(x)
    best = 0.0
    for i in range(len(sec) - 1):
        y0, z0 = sec[i]
        y1, z1 = sec[i + 1]
        if (z0 - z) * (z1 - z) <= 0.0 and z1 != z0:
            t = (z - z0) / (z1 - z0)
            best = max(best, y0 + (y1 - y0) * t)
    if best == 0.0:                      # z outside the section: fall back
        best = max(y for (y, _) in sec)
    return best


CURVES = {
    "z_top": _C_ZTOP, "z_bot": _C_ZBOT, "w_max": _C_WMAX,
    "z_belt": _C_ZBELT, "w_top": _C_WTOP, "y_at": body_y_at,
}


def main():
    col = L.purge("SU7_Exterior")
    body = build_body(col)
    build_wheels(col)
    P.build_glass(col, half_section, x_front=1.105, x_rear=-2.045)
    P.build_lights(col, HALF_L, CURVES)
    P.build_aero(col, HALF_L, REAR_AXLE, CURVES)
    P.build_mirrors(col, CURVES)
    apply_materials(build_materials())

    tris = 0
    for ob in col.objects:
        tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print("objects: %d   base tris: %d" % (len(col.objects), tris))
    return col


if __name__ == "__main__":
    main()
