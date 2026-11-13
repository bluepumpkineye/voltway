"""XPeng G9L cabin polish: the Seal's gold-standard pass (seal_polish.py is the pattern) for the G9L's own parts.

    collars     a gasket where the steering column meets the dash
    icons       the two round dials at the wheel's lower sides (drive mode, voice)
    spill       a glow ribbon on the red leather under the lit vent slot, the purple horizontal bar (M_Glow, additive in the
                web in the live ambient colour)
    bevel       Bevel (2 segments, 2 mm, 35 degrees, clamped) + Weighted Normal on the screen housing, its stand and the
                cluster window; shade smooth on the rim, the X, the stalks
    helpers     leftover curves / wire / cutter objects and unapplied booleans removed

Not done: the spoke pads are leather plates with no discrete keys (no icons to place), the console has no keys of its own.
"""
import bpy

import bpy_interior_polish as BP
import g9l_interior as ZI
from bpy_interior_polish import guard as _guard
from carkit.interior import steering as ST

BEVEL = r"^(int_screen_body|int_screen_stand|int_cluster_window)$"
SMOOTH = r"int_wheel_(rim|X\d)|stalk"


def _frame():
    return ST.WheelFrame(ZI.WHEEL_C, ZI.WHEEL_TILT)


def spill(col, sw):
    """The glow under the purple slot: from the slot's foot across the upper face's leather."""
    n = len(sw.pts)
    i0, i1 = int(n * 0.05), int(n * 0.95)
    rows = []
    for j in range(sw.col(6), sw.col(8) + 1):
        pts, _ = sw.iso_col(j, i0, i1, lift=0.0009)
        rows.append(pts)
    return [BP.glow_ribbon(col, "int_dash_Glow", rows)]


def build(col, lib):
    made = []
    fr = _frame()
    made += _guard("collar", lambda: [BP.column_collar(col, lib["satin"], fr)])
    made += _guard("icons", BP.wheel_button_icons, col, fr, ZI.G9L_WHEEL, ("mode", "voice"))
    BP.polish(col, bevel_pattern=BEVEL, smooth_pattern=SMOOTH, width=0.002)
    print("g9l_polish: %d objects" % len(made))
    return made
