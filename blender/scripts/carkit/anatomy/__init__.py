"""carkit.anatomy - the parts under the skin, built from a car's measured dimensions.

    spec        CarSpec / Motor: the dimensions a car provides (hubs, floor, pack, motors)
    prim        mesh builder, materials, outlines, object helpers
    battery     the traction pack: tray, cold plate, cell blocks, busbars, insulator, lid, PDU
    motor       a drive unit: casing, stator, rotor, reducer and gears, inverter
    frames      floor frame, subframes, crash beams, shock towers
    suspension  double-wishbone / multi-link corners, anti-roll bars, steering rack, half-shafts
    cables      the HV harness
    build       assemble a car, write the explode plan, export the GLB

The part builders take a `CarSpec`, so the same code makes a longer, wider or heavier car's
parts. Nodes are named `XR_<System>_<Part>`; each carries an `xr` JSON extra that the web
viewer reads (system, explode offset, timing, pivots), see build.py.
"""
import sys


def reload():
    for name in [m for m in sys.modules if m.startswith("carkit.anatomy")]:
        sys.modules.pop(name, None)
