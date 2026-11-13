"""Zeekr 7X cabin polish: the Seal's gold-standard pass (seal_polish.py is the pattern) for the 7X's own keys and trims.

    collars     a gasket where the steering column meets the dash
    icons       the two wheel pods (rocker, two keys each), the five knurled keys under the centre screen, the wireless pad
    bevel       Bevel (2 segments, 2 mm, 35 degrees, clamped) + Weighted Normal on the screen housing, its arm and key bar, the
                cluster body and the console's selector and lid frame; shade smooth on the rim, stalks, U and mark
    helpers     leftover curves / wire / cutter objects and unapplied booleans removed

Not done, and why: the door switch pack is a single moulded band (no discrete keys to put icons on) and the 7X's light guides are
the door pods' piping only (no dash guide for a spill ribbon).
"""
import bpy
from mathutils import Vector

import bpy_interior_polish as BP
import zx_interior as ZI
from bpy_interior_polish import guard as _guard, icon_quad, icon_material
from carkit.interior import steering as ST

BEVEL = r"^(int_screen_body|int_screen_arm|int_screen_keys|int_cluster_body|int_console_selector|int_console_lid_frame)$"
SMOOTH = r"int_wheel_(rim|stalk|U|mark)"


def _frame():
    return ST.WheelFrame(ZI.WHEEL_C, ZI.WHEEL_TILT)


def build_collars(col, lib):
    return [BP.column_collar(col, lib["satin"], _frame())]


def build_icons(col, lib):
    mat = icon_material()
    dark = icon_material("dark")           # glyphs on the light keys and the cream pad
    made = []
    fr = _frame()
    up, nrm = Vector(fr.V), Vector(fr.A)
    w0 = 0.0198
    lift = 0.0004
    # the pods: a rocker with its roller nearest the hub, two small keys toward the rim
    layout = {
        1.0: {"rocker": ("vol_minus", "vol_plus"), "keys": ("voice", "phone")},          # the right pod: media
        -1.0: {"rocker": ("arrow_down", "arrow_up"), "keys": ("cruise", "adas_distance")},  # the left pod: driver assistance
    }
    for s, tag in ((1.0, "R"), (-1.0, "L")):
        lay = layout[s]
        for j, (du, ic) in enumerate(((-0.019, lay["rocker"][0]), (0.019, lay["rocker"][1]))):
            c = fr.p(s * (0.098 + du), 0.0, w0 + 0.0052 + lift)
            made.append(icon_quad(col, mat, "int_icon_wheel%sRocker%d" % (tag, j), c, up, nrm, 0.0130, ic))
        for k, (vk, ic) in enumerate(((0.0105, lay["keys"][0]), (-0.0105, lay["keys"][1]))):
            c = fr.p(s * 0.139, vk, w0 + 0.0048 + lift)
            made.append(icon_quad(col, mat, "int_icon_wheel%sKey%d" % (tag, k), c, up, nrm, 0.0105, ic))
    # the five knurled keys under the centre screen, facing the driver
    zb = ZI.SCREEN_C[2] - ZI.SCREEN_H / 2 - 0.030
    for k, ic in enumerate(("defrost", "fan", "hazard", "camera", "mode")):
        yk = ZI.SCREEN_Y + 0.080 - 0.040 * k
        made.append(icon_quad(col, dark, "int_icon_screenKey%d" % k, (ZI.SCREEN_C[0] - 0.0165, yk, zb),
                              (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), 0.0130, ic))
    # the wireless pad's glyph
    x = 0.690
    z = ZI.CONSOLE_TOP(x) + 0.0015 + 0.0006 + lift
    made.append(icon_quad(col, dark, "int_icon_charger", (x, 0.0, z), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.075, "charger"))
    return made


def build(col, lib):
    made = []
    made += _guard("collars", build_collars, col, lib)
    made += _guard("icons", build_icons, col, lib)
    BP.polish(col, bevel_pattern=BEVEL, smooth_pattern=SMOOTH, width=0.002)
    print("zx_polish: %d objects" % len(made))
    return made
