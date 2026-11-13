"""The generic interior polish for the cars whose cabin has no key layout of its own to place (yet): called last by each car's
cabin build, `__import__("car_polish").build("<key>", col, lib)`.

For every car: leftover helpers removed, hero curves smooth-shaded, Bevel (2 segments, 2 mm, 35 degrees, clamped) + Weighted
Normal on the screen housings and cluster bezels, a gasket ring where the steering column meets the dash, icons on the wheel's
round buttons where the wheel has any. Cars with their own layouts have their own module (seal_polish, zx_polish, g9l_polish);
a car that gains discrete keys, a charge-pad glyph or a light guide to spill from adds them in a module of its own, copying
seal_polish.py, and drops its entry here.

Table: key -> (the cabin module, the wheel spec's name in it or in carkit.interior.steering, icons for the wheel's buttons in order).
"""
import bpy

import bpy_interior_polish as BP
from bpy_interior_polish import guard as _guard
from carkit.interior import steering as ST

BEVEL = (r"^(int_screen_(body|stand|neck|arm.*)|int_cluster_(body|window|bezel)|int_console_(selector|lid_frame))$")
SMOOTH = r"int_wheel_(rim|stalk|mark|X\d|U)"

CARS = {
    "vps": ("vps_interior", "VOYAH_PASSION_S_WHEEL", ()),
    "rx": ("rx_interior", "LUXEED_RX", ("mode",)),                  # the BOOST button
    "es8": ("es8_interior", "NIO_ES8_WHEEL", ()),
    "z9": ("z9_interior", "DENZA_WHEEL", ()),
    "su7": ("su7_interior", "SU7_ULTRA", ("mode", "voice")),        # the red dial, the brushed key
    "a06t": ("a06t_interior", None, ()),
}


def build(key, col, lib):
    zi_name, spec_name, icons = CARS[key]
    made = []
    zi = __import__(zi_name)
    if spec_name:
        spec = getattr(zi, spec_name, None) or getattr(ST, spec_name)
        fr = ST.WheelFrame(zi.WHEEL_C, zi.WHEEL_TILT)
        made += _guard("column collar", lambda: [BP.column_collar(col, lib["satin"], fr)])
        if icons:
            made += _guard("wheel icons", BP.wheel_button_icons, col, fr, spec, icons)
    BP.polish(col, bevel_pattern=BEVEL, smooth_pattern=SMOOTH, width=0.002)
    print("car_polish[%s]: %d objects" % (key, len(made)))
    return made
