"""Parametric SU7 Ultra cockpit.

This is the part of the car the user actually sits in and touches, so it is
built as real geometry rather than generated: flat panels, screen bezels,
console and seats are exactly what parametric construction is good at.

The single most important object here is `screen_main` - a flat quad with a
clean planar UV, sized to the real 16.1" central display. The web app anchors
its live HMI to that quad, so its name, size and orientation are a contract.

Axes: +X front, +Y left (driver's side, China is LHD), +Z up.
"""
import bpy
import math
import os
import sys

_HERE = r"C:\Users\User\Documents\4 - Website_ WebApp Project\Chinese EV Configurator\blender\scripts"
if _HERE not in sys.path:
    sys.path.append(_HERE)

import lib_build as L
import parts_su7 as P
import importlib
importlib.reload(L)
importlib.reload(P)

from mathutils import Matrix

# ------------------------------------------------------------------ geometry
FLOOR_Z = 0.335
CABIN_HALF_W = 0.775
DASH_FACE_X = 1.010          # base of the windscreen
DASH_TOP_Z = 0.952
CONSOLE_TOP_Z = 0.665
DRIVER_Y = 0.378
PASS_Y = -0.378
HEADLINER_Z = 1.352

# 16.1" 3K central display, 16:10 -> 347 x 217 mm
SCREEN_W, SCREEN_H = 0.347, 0.217
SCREEN_X, SCREEN_Y, SCREEN_Z = 0.688, 0.018, 0.958
SCREEN_TILT = math.radians(9.0)      # leans back toward the occupants
SCREEN_YAW = math.radians(4.0)       # angled a touch toward the driver

# 7.1" cluster, 16:9 -> 157 x 88 mm
CLUSTER_W, CLUSTER_H = 0.157, 0.088


def _panel(col, name, cx, cy, cz, w, h, tilt=0.0, yaw=0.0, axis='YZ'):
    """A single flat quad with a planar UV in [0,1]. Used for every display."""
    hw, hh = w / 2.0, h / 2.0
    if axis == 'YZ':                       # faces +X (toward the occupants)
        pts = [(0, hw, -hh), (0, -hw, -hh), (0, -hw, hh), (0, hw, hh)]
    else:                                  # faces +Z
        pts = [(-hw, hh, 0), (-hw, -hh, 0), (hw, -hw, 0), (hw, hh, 0)]

    ct, st = math.cos(tilt), math.sin(tilt)
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    verts = []
    for (x, y, z) in pts:
        x, z = x * ct + z * st, -x * st + z * ct
        x, y = x * cy_ - y * sy_, x * sy_ + y * cy_
        verts.append((cx + x, cy + y, cz + z))

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [[0, 1, 2, 3]])
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    # (0,0) bottom-left as seen by someone sitting in the car
    for i, co in enumerate([(1.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)]):
        uv.data[i].uv = co
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


# --------------------------------------------------------------------- shell
def build_shell(col):
    made = []

    floor = P.box(col, "int_floor", -0.30, 0.0, FLOOR_Z - 0.02,
                  2.70, CABIN_HALF_W * 2, 0.04)
    made.append(floor)

    # Follow the roofline. A flat slab cannot work: the crown is at 1.465 but
    # the roof has already fallen to 1.09 by the windscreen header, so a level
    # headliner punches straight out through the glass.
    import su7_surface as SURF
    nx = 26
    hverts, hfaces = [], []
    for i in range(nx + 1):
        x = -1.62 + (1.62 + 0.30) * (i / nx)
        z = SURF.Z_ROOF(x) - 0.055
        half = min(CABIN_HALF_W * 0.92, SURF.Y_ROOF(x) * 0.86)
        hverts.append((x, half, z))
        hverts.append((x, -half, z))
    for i in range(nx):
        a = i * 2
        hfaces.append([a, a + 2, a + 3, a + 1])
    import bpy as _bpy
    hme = _bpy.data.meshes.new("int_headliner")
    hme.from_pydata(hverts, [], hfaces)
    hme.validate()
    hme.update()
    headliner = _bpy.data.objects.new("int_headliner", hme)
    col.objects.link(headliner)
    made.append(headliner)

    # main dash body and the softer lower section beneath it.
    # Clearance only (the cockpit is refitted in the interior round): the
    # exterior's cowl moved 145 mm forward and down, and the old dash stood
    # 40 mm proud of the new hood line. Top now 955 mm, front at x = 0.955.
    dash = P.box(col, "int_dash", 0.830, 0.0, 0.838, 0.250, CABIN_HALF_W * 2, 0.235)
    P.bevel(dash, 0.030, 3)
    made.append(dash)

    lower = P.box(col, "int_dash_lower", 0.958, 0.0, 0.735, 0.185, CABIN_HALF_W * 1.94, 0.235)
    P.bevel(lower, 0.026, 3)
    made.append(lower)

    # dark upper pad that runs the width of the car
    pad = P.box(col, "int_dash_pad", 0.800, 0.0, 0.925,
                0.300, CABIN_HALF_W * 2.02, 0.040)
    P.bevel(pad, 0.018, 3)
    made.append(pad)

    # door cards
    for sgn, tag in ((1, "L"), (-1, "R")):
        d = P.box(col, "int_door_" + tag, 0.005, sgn * (CABIN_HALF_W + 0.018),
                  0.690, 1.90, 0.075, 0.500)
        P.bevel(d, 0.028, 3)
        made.append(d)
        arm = P.box(col, "int_armrest_" + tag, 0.325, sgn * (CABIN_HALF_W - 0.045),
                    0.815, 0.52, 0.115, 0.075)
        P.bevel(arm, 0.024, 3)
        made.append(arm)

    # A-pillars, angled back to meet the roof
    import su7_surface as SURF2
    for sgn, tag in ((1, "L"), (-1, "R")):
        x_p = 0.640
        # the screen is a wraparound: its A-pillars sit ~30 mm below the
        # centreline, so follow the pillar, not the centreline
        z_p = SURF2.Z_ROOF(x_p) + SURF2.Z_CREST(x_p) - 0.185
        a = P.box(col, "int_apillar_" + tag, x_p, sgn * (CABIN_HALF_W - 0.075),
                  z_p, 0.085, 0.095, 0.235, rot_y=math.radians(38))
        P.bevel(a, 0.018, 2)
        made.append(a)

    return made


# ------------------------------------------------------------------- console
def build_console(col):
    made = []

    body = P.box(col, "int_console", 0.155, 0.0, 0.515, 1.36, 0.395, 0.365)
    P.bevel(body, 0.030, 3)
    made.append(body)

    top = P.box(col, "int_console_top", 0.155, 0.0, CONSOLE_TOP_Z + 0.010,
                1.34, 0.375, 0.026)
    P.bevel(top, 0.014, 2)
    made.append(top)

    # the physical toggle row that sits directly under the main screen
    for i in range(11):
        u = (i - 5) / 5.0
        b = P.box(col, "int_hardkey_%d" % i, 0.706, u * 0.148, 0.882,
                  0.052, 0.020, 0.030)
        P.bevel(b, 0.005, 1)
        made.append(b)

    # rotary control in the middle of that row
    knob = P.box(col, "int_rotary", 0.706, 0.0, 0.882, 0.052, 0.048, 0.034)
    P.bevel(knob, 0.014, 3)
    made.append(knob)

    start = P.box(col, "int_start_stop", 0.400, 0.118, CONSOLE_TOP_Z + 0.020,
                  0.070, 0.048, 0.016)
    P.bevel(start, 0.007, 2)
    made.append(start)

    pad = P.box(col, "int_wireless_pad", 0.395, -0.085, CONSOLE_TOP_Z + 0.012,
                0.185, 0.115, 0.010)
    P.bevel(pad, 0.006, 2)
    made.append(pad)

    return made


# ------------------------------------------------------------------- screens
def build_screens(col):
    """The displays. `screen_main` is the anchor the web HMI mounts to."""
    made = {}

    bezel = P.box(col, "int_screen_bezel", SCREEN_X - 0.012, SCREEN_Y, SCREEN_Z,
                  0.026, SCREEN_W + 0.024, SCREEN_H + 0.024,
                  rot_y=SCREEN_TILT, rot_z=SCREEN_YAW)
    P.bevel(bezel, 0.008, 3)
    made["bezel"] = bezel

    main = _panel(col, "screen_main", SCREEN_X, SCREEN_Y, SCREEN_Z,
                  SCREEN_W, SCREEN_H, tilt=SCREEN_TILT, yaw=SCREEN_YAW)
    made["main"] = main

    stalk = P.box(col, "int_screen_stalk", SCREEN_X + 0.030, SCREEN_Y,
                  SCREEN_Z - SCREEN_H / 2 - 0.090, 0.070, 0.090, 0.170)
    P.bevel(stalk, 0.014, 2)
    made["stalk"] = stalk

    cluster_bezel = P.box(col, "int_cluster_bezel", 0.735, DRIVER_Y, 1.000,
                          0.022, CLUSTER_W + 0.020, CLUSTER_H + 0.020,
                          rot_y=math.radians(11))
    P.bevel(cluster_bezel, 0.006, 2)
    made["cluster_bezel"] = cluster_bezel

    cluster = _panel(col, "screen_cluster", 0.723, DRIVER_Y, 1.000,
                     CLUSTER_W, CLUSTER_H, tilt=math.radians(11))
    made["cluster"] = cluster

    # the 56" HUD lives on the windscreen; represented as a floating plane
    # projected onto the windscreen, so it has to sit under the glass line
    import su7_surface as SURF3
    hud_x = 0.800
    hud = _panel(col, "screen_hud", hud_x, DRIVER_Y,
                 SURF3.Z_ROOF(hud_x) - 0.082, 0.290, 0.100,
                 tilt=math.radians(26))
    made["hud"] = hud

    return made


# --------------------------------------------------------------- wheel, vents
def build_steering(col):
    made = []
    # 60 mm further back than before: the exterior rebuild moved the windscreen
    # base to the measured cowl at x = 0.800, and the rim's top grazed the glass.
    # and another 38 mm back and 28 mm down for the v3 body's lower screen
    cx, cy, cz = 0.550, DRIVER_Y, 0.930
    tilt = math.radians(24)
    r_out, r_sec = 0.178, 0.019
    major, minor = 36, 12

    # torus with its axis along local X, then pitched back about Y
    verts, faces = [], []
    ct, st = math.cos(tilt), math.sin(tilt)
    for i in range(major):
        a = 2 * math.pi * i / major
        squash = 1.0 if math.sin(a) > -0.55 else 0.86
        for j in range(minor):
            b = 2 * math.pi * j / minor
            rr = r_out + r_sec * math.cos(b)
            lx = r_sec * math.sin(b)
            ly = rr * math.cos(a)
            lz = rr * math.sin(a) * squash
            # rotate about Y
            wx = lx * ct + lz * st
            wz = -lx * st + lz * ct
            verts.append((cx + wx, cy + ly, cz + wz))
    for i in range(major):
        for j in range(minor):
            a0 = i * minor + j
            a1 = i * minor + (j + 1) % minor
            b0 = ((i + 1) % major) * minor + j
            b1 = ((i + 1) % major) * minor + (j + 1) % minor
            faces.append([a0, a1, b1, b0])
    rim = L.new_mesh_object("int_wheel_rim", verts, faces, col)
    L.merge_doubles(rim, 0.0005)
    L.shade_smooth(rim)
    made.append(rim)

    hub = P.box(col, "int_wheel_hub", cx - 0.012, cy, cz, 0.048, 0.128, 0.098,
                rot_y=tilt)
    P.bevel(hub, 0.018, 3)
    made.append(hub)

    for sgn in (1, -1):
        sp = P.box(col, "int_wheel_spoke_%s" % ('L' if sgn > 0 else 'R'),
                   cx - 0.004, cy + sgn * 0.098, cz - 0.012,
                   0.030, 0.115, 0.036, rot_y=tilt)
        P.bevel(sp, 0.010, 2)
        made.append(sp)

    col_shroud = P.box(col, "int_wheel_column", cx - 0.145, cy, cz - 0.062,
                       0.235, 0.105, 0.095, rot_y=tilt)
    P.bevel(col_shroud, 0.022, 3)
    made.append(col_shroud)

    drive_btn = P.box(col, "int_drive_mode_btn", cx + 0.010, cy - 0.058, cz - 0.040,
                      0.020, 0.034, 0.034, rot_y=tilt)
    P.bevel(drive_btn, 0.008, 3)
    made.append(drive_btn)

    return made


def build_vents_and_trim(col):
    made = []
    # horizontal vent slots either side of the centre stack
    for sgn in (1, -1):
        v = P.box(col, "int_vent_%s" % ('L' if sgn > 0 else 'R'),
                  0.800, sgn * 0.470, 0.902, 0.024, 0.300, 0.036)
        P.bevel(v, 0.008, 2)
        made.append(v)

    # ambient light strip running the width of the dash
    strip = P.box(col, "int_ambient_strip", 0.798, 0.0, 0.858,
                  0.014, CABIN_HALF_W * 1.92, 0.010)
    made.append(strip)

    for sgn in (1, -1):
        d = P.box(col, "int_ambient_door_%s" % ('L' if sgn > 0 else 'R'),
                  0.075, sgn * (CABIN_HALF_W - 0.022), 0.905,
                  1.72, 0.014, 0.011)
        made.append(d)

    trim = P.box(col, "int_dash_trim", 0.797, 0.0, 0.820,
                 0.018, CABIN_HALF_W * 1.96, 0.028)
    P.bevel(trim, 0.009, 2)
    made.append(trim)
    return made


# --------------------------------------------------------------------- seats
def _seat(col, tag, cx, cy, recline=math.radians(14)):
    made = []
    base = P.box(col, "int_seat_base_" + tag, cx, cy, FLOOR_Z + 0.165,
                 0.520, 0.520, 0.145)
    P.bevel(base, 0.055, 3)
    made.append(base)

    back = P.box(col, "int_seat_back_" + tag, cx - 0.255, cy, FLOOR_Z + 0.545,
                 0.150, 0.500, 0.640, rot_y=-recline)
    P.bevel(back, 0.055, 3)
    made.append(back)

    head = P.box(col, "int_seat_head_" + tag, cx - 0.335, cy, FLOOR_Z + 0.945,
                 0.130, 0.250, 0.185, rot_y=-recline)
    P.bevel(head, 0.048, 3)
    made.append(head)

    # bolsters
    for sgn in (1, -1):
        b = P.box(col, "int_seat_bolster_%s%d" % (tag, sgn),
                  cx - 0.245, cy + sgn * 0.225, FLOOR_Z + 0.520,
                  0.135, 0.075, 0.560, rot_y=-recline)
        P.bevel(b, 0.038, 3)
        made.append(b)
    return made


def build_seats(col):
    made = []
    made += _seat(col, "FL", 0.115, DRIVER_Y)
    made += _seat(col, "FR", 0.115, PASS_Y)

    bench = P.box(col, "int_rear_bench", -0.885, 0.0, FLOOR_Z + 0.155,
                  0.560, CABIN_HALF_W * 1.80, 0.135)
    P.bevel(bench, 0.055, 3)
    made.append(bench)

    rback = P.box(col, "int_rear_back", -1.185, 0.0, FLOOR_Z + 0.520,
                  0.145, CABIN_HALF_W * 1.80, 0.600, rot_y=math.radians(-17))
    P.bevel(rback, 0.055, 3)
    made.append(rback)
    return made


# ----------------------------------------------------------------- materials
def build_materials():
    return {
        "alcantara": L.make_material("INT_Alcantara", (0.0245, 0.0248, 0.0268),
                                     roughness=0.885),
        "leather": L.make_material("INT_Leather", (0.372, 0.288, 0.142),
                                   roughness=0.560),
        "leather_dark": L.make_material("INT_LeatherDark", (0.042, 0.040, 0.044),
                                        roughness=0.620),
        "alu": L.make_material("INT_Aluminium", (0.615, 0.618, 0.625),
                               roughness=0.265, metallic=0.94),
        "plastic": L.make_material("INT_Plastic", (0.0185, 0.0185, 0.0205),
                                   roughness=0.435),
        "gloss": L.make_material("INT_GlossBlack", (0.0105, 0.0105, 0.0120),
                                 roughness=0.095, coat=1.0),
        "screen": L.make_material("INT_Screen", (0.006, 0.008, 0.014),
                                  roughness=0.055,
                                  emission=(0.10, 0.16, 0.30),
                                  emission_strength=1.35),
        "ambient": L.make_material("INT_Ambient", (0.02, 0.02, 0.02),
                                   roughness=0.5,
                                   emission=(1.0, 0.42, 0.06),
                                   emission_strength=5.5),
    }


def apply_materials(col, mats):
    def pick(name):
        n = name.lower()
        if n.startswith("screen_"):
            return mats["screen"]
        if "ambient" in n:
            return mats["ambient"]
        if "seat" in n or "bench" in n or "rear_back" in n:
            return mats["leather"]
        if "armrest" in n:
            return mats["leather"]
        if "trim" in n or "console_top" in n or "rotary" in n or "wireless" in n:
            return mats["alu"]
        if "hardkey" in n or "start_stop" in n or "vent" in n:
            return mats["alu"]
        if "bezel" in n or "stalk" in n or "gloss" in n:
            return mats["gloss"]
        if "wheel_rim" in n or "wheel_spoke" in n or "wheel_hub" in n:
            return mats["leather_dark"]
        if "drive_mode" in n:
            return mats["gloss"]
        if "dash_pad" in n or "headliner" in n or "apillar" in n:
            return mats["alcantara"]
        if "door" in n or "dash" in n or "console" in n or "floor" in n:
            return mats["plastic"]
        return mats["plastic"]

    for ob in col.objects:
        if ob.type == 'MESH':
            L.assign(ob, pick(ob.name))


def add_cabin_lights(col):
    """Soft fill inside the cabin - the body shell blocks nearly all HDRI."""
    made = []
    specs = [
        ("int_light_key", (0.35, 0.55, 1.36), 42.0, (1.0, 0.97, 0.92)),
        ("int_light_fill", (0.30, -0.55, 1.36), 26.0, (0.86, 0.90, 1.0)),
        ("int_light_screen", (0.45, 0.02, 1.10), 9.0, (0.72, 0.82, 1.0)),
    ]
    for name, loc, power, colr in specs:
        ld = bpy.data.lights.new(name, type='AREA')
        ld.energy = power
        ld.size = 0.55
        ld.color = colr
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        col.objects.link(ob)
        made.append(ob)
    return made


def main():
    col = L.purge("SU7_Interior")
    build_shell(col)
    build_console(col)
    build_screens(col)
    build_steering(col)
    build_vents_and_trim(col)
    build_seats(col)
    apply_materials(col, build_materials())
    add_cabin_lights(col)

    tris = 0
    for ob in col.objects:
        if ob.type != 'MESH':
            continue
        tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print("interior objects: %d   base tris: %d" % (len(col.objects), tris))
    assert "screen_main" in bpy.data.objects, "screen_main is the HMI anchor"
    return col


if __name__ == "__main__":
    main()
