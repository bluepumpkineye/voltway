"""XPeng Mona L05 cabin polish (2026-11-21): the gold-standard pass (seal_polish.py / zx_polish.py are the pattern) for the Mona's own
keys and trims. It replaces the generic car_polish entry the Mona had.

    collars     a gasket where the steering column meets the dash
    icons       the wheel's two pods (a chevron at each end of the roller; the right pod's are skip-track marks), the two lower
                glass buttons (the cruise key and MODE), and the three window / lock keys on the driver's and the passenger's
                door (dark glyphs on the pale keys)
    bevel       Bevel (2 segments, 2 mm, 35 degrees, clamped) + Weighted Normal on the screen housing and arm, the console's
                frame, lip and nose, the dash's chrome strips and the wheel's silver parts; shade smooth on the rim, the clamp,
                the spokes and the bosses
    spill       an ambient glow ribbon down the dash face under the light line (M_Glow)
    helpers     leftover curves / wire / cutter objects and unapplied booleans removed

Every step is guarded: a failure prints and the cabin still exports.
"""
import bpy
from mathutils import Vector

import bpy_interior_polish as BP
import mona_interior as MI
import mona_wheel as MW
from bpy_interior_polish import guard as _guard, icon_quad, icon_material
from carkit.interior import steering as ST

BEVEL = (r"^(int_screen_(body|arm_C)|int_console_(frame|lip|nose)|int_dash_Chrome[LR]"
         r"|int_wheel_(podframe[LR]|btnring[LR]|roller[LR]|spoke[LR]|boss[LR]))$")
SMOOTH = r"int_wheel_(rim|clamp|stalk|spoke|boss|column)"


def _frame():
    return ST.WheelFrame(MI.WHEEL_C, MI.WHEEL_TILT)


def build_collars(col, lib):
    """A gasket where the column meets the dash, sized to the Mona's slim column (r 0.034-0.039 at its far end, centre 3 cm below the
    rim's centre: mona_wheel.build_column), not the shared 0.074 x 0.066 ring that floated round it."""
    import math
    fr = _frame()
    ring = []
    for t in range(33):
        a = 2.0 * math.pi * t / 32.0
        ring.append(fr.p(0.0405 * math.cos(a), -0.030 + 0.0345 * math.sin(a), -0.034 - 0.200 + 0.006))
    return [BP.collar_loop(col, "int_column_collar", ring, lib["satin"], 0.0045, 0.0028, lateral=tuple(fr.A))]


def build_wheel_icons(col, lib):
    mat = icon_material()
    made = []
    fr = _frame()
    U, V, A = Vector(fr.U), Vector(fr.V), Vector(fr.A)
    lift = 0.0004
    w_pad = MW.POD_Z - 0.0050 + lift
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        uc, vc = side * MW.POD_UV[0], MW.POD_UV[1]
        if side < 0:
            # the left pod: a chevron each side of the roller (the volume / page rocker)
            made.append(icon_quad(col, mat, "int_icon_wheel%sA" % tag, fr.p(uc - 0.0166, vc, w_pad), -U, A, 0.0075, "arrow_up"))
            made.append(icon_quad(col, mat, "int_icon_wheel%sB" % tag, fr.p(uc + 0.0166, vc, w_pad), U, A, 0.0075, "arrow_up"))
        else:
            # the right pod: previous and next
            made.append(icon_quad(col, mat, "int_icon_wheel%sA" % tag, fr.p(uc - 0.0166, vc, w_pad), -V, A, 0.0080, "next"))
            made.append(icon_quad(col, mat, "int_icon_wheel%sB" % tag, fr.p(uc + 0.0166, vc, w_pad), V, A, 0.0080, "next"))
    # the two lower glass buttons
    for side, tag, ic, k in ((-1.0, "L", "cruise", 0.0150), (1.0, "R", "mode", 0.0165)):
        c = fr.p(side * MW.BTN_UV[0], MW.BTN_UV[1], 0.0166 + lift)
        made.append(icon_quad(col, mat, "int_icon_wheelBtn" + tag, c, V, A, k, ic))
    return made


def build_door_icons(col, lib):
    """Glyphs on the three keys flush in each front door's switch slot (the keys' tops are at the card's armrest)."""
    dark = icon_material("dark")
    made = []
    for pre in ("int_door_L_", "int_door_R_"):
        keys = sorted((o for o in bpy.data.objects if o.name.startswith(pre + "Switch") and "Slot" not in o.name
                       and o.type == 'MESH'), key=lambda o: o.name)
        glyphs = ("win_up", "win_down", "lock")
        for k, ob in enumerate(keys[:3]):
            vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
            cx = sum(v.x for v in vs) / len(vs)
            cy = sum(v.y for v in vs) / len(vs)
            zt = max(v.z for v in vs)
            dx = max(v.x for v in vs) - min(v.x for v in vs)
            dy = max(v.y for v in vs) - min(v.y for v in vs)
            made.append(icon_quad(col, dark, pre + "Icon%d" % k, (cx, cy, zt + 0.0004), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0),
                                  0.8 * min(dx, dy), glyphs[k]))
    return made


def build_spill(col, lib):
    """Ambient spill: a ribbon down the dash's lavender face from the dark gap under the silver strip, where the ambient line runs
    (mona_interior.build_dash: x 0.580 + FRONT_DX, z 0.984). The web draws it additively in the live ambient colour (M_Glow, a
    gradient along UV v: 0 at the light guide, 1 where it has faded)."""
    face = [(0.588 + MI.FRONT_DX, 0.974), (0.614 + MI.FRONT_DX, 0.916), (0.656 + MI.FRONT_DX, 0.835)]

    def x_at(z):
        for (xa, za), (xb, zb) in zip(face[:-1], face[1:]):
            if zb <= z <= za:
                return xa + (xb - xa) * (za - z) / (za - zb)
        return face[-1][0]

    y_end = MI.DASH_HALF - MI.END_TAPER + 0.02
    ys = [y_end - 2 * y_end * k / 80.0 for k in range(81)]
    rows = []
    for z in (0.9705, 0.9560, 0.9390, 0.9200, 0.9000):
        rows.append([(x_at(z) - 0.0009, y, z) for y in ys])
    return [BP.glow_ribbon(col, "int_dash_Glow", rows)]


def build(col, lib):
    made = []
    made += _guard("collars", build_collars, col, lib)
    made += _guard("wheel icons", build_wheel_icons, col, lib)
    made += _guard("door icons", build_door_icons, col, lib)
    made += _guard("spill", build_spill, col, lib)
    BP.polish(col, bevel_pattern=BEVEL, smooth_pattern=SMOOTH, width=0.002)
    print("mona_polish: %d objects" % len(made))
    return made
