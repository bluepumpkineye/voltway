"""Port blender/scripts/zx_bays.py to z9_bays.py with the Denza Z9's measured numbers (probe_z9.log HOODX, c12_0001/2/64)."""
import io

import os
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) + "/"
s = io.open(ROOT + "zx_bays.py", encoding="utf-8").read()


def sub(old, new, count=1):
    global s
    if s.count(old) < 1:
        raise SystemExit("missing: " + old[:60])
    s = s.replace(old, new) if count == 0 else s.replace(old, new, count)


a = s.index('"""Zeekr 7X bays')
b = s.index('import math')
s = s[:a] + '''"""Denza Z9 bays: the frunk under the bonnet, from the opening photographs (Autohome series 7838,
cat 12: c12_0001/2/7 on the black car, c12_0063-68 on the purple one; blender/reference/denza-z9/openings).

What the photographs show, from the cowl forward: a black wiper well under the windscreen's foot with a ribbed
vent strip and the two wipers parked along the glass; a black moulded tray the whole width of the hood with a seal
round its rim; in the middle a wide, shallow, rounded cover over the drive unit; a washer-fluid filler at the
left rear, a round cap at each front corner and the latch at the front; two thin gas struts at the cowl's
corners; the bonnet's underside lined with a black pad inside its painted frame. The bonnet stands about 76 deg
open (c12_0001/2).

    import z9_bays as BY
    BY.build_frunk()      # the static bay (Z9_Details)
    BY.split_bonnet()     # Z9_Bonnet: hood + liner, origin on the hinge
    BY.open_hull()        # the hull's roof under the bonnet

Car axes +x forward, +y left, z up.
"""
''' + s[b:]

a = s.index("# plan half-width of the hood by x")
b = s.index("def hood_half(x):")
s = s[:a] + '''# plan half-width of the hood by x, measured on the built panel (Z9_Hood)
HOOD_HALF = [(0.99, 0.754), (1.19, 0.792), (1.39, 0.819), (1.59, 0.821), (1.79, 0.796), (1.89, 0.818),
             (2.04, 0.883), (2.14, 0.853), (2.19, 0.647), (2.24, 0.479), (2.29, 0.339), (2.34, 0.201),
             (2.376, 0.0)]
HOOD_HINGE = (1.000, 0.985)    # (x, z) of the hinge axis, along y, under the rear edge
HOOD_DEG = 76.0
APRON_DROP = 0.060             # the tray's height under the hood's top surface
TUB_DEPTH = 0.095
# the cover's outline, half-width by x from its rear edge round the front (the +y half; mirrored): a wide, low
# rounded shape about 1.2 m across and 0.5 m deep (c12_0064)
TUB = [(1.140, 0.0), (1.140, 0.420), (1.160, 0.520), (1.220, 0.580), (1.340, 0.600), (1.500, 0.580),
       (1.580, 0.520), (1.620, 0.400), (1.640, 0.200), (1.640, 0.0)]
# the cover's wall offsets (inward, down) from the rim
WALL = [(0.0, 0.0), (0.004, -0.006), (0.010, -0.018), (0.016, -0.045), (0.022, -0.075), (0.032, -0.090),
        (0.048, -0.095)]


''' + s[b:]

sub('"ZX_Hood") or bpy.data.objects["ZX_Bonnet"]', '"Z9_Hood") or bpy.data.objects["Z9_Bonnet"]')
# no divider in the Z9's cover
a = s.index("    # the divider: a low wall across the tub")
b = s.index("    # the washer cap, right rear of the tray")
s = s[:a] + s[b:]
sub("x0, x1 = 1.236, 2.185", "x0, x1 = 1.030, 2.190")
sub("cx, cy = 1.545, -0.545", "cx, cy = 1.080, 0.600")
sub("""_rrect(2.00, sy * 0.600, 0.100, 0.130, 0.040)""", """_rrect(1.96, sy * 0.640, 0.090, 0.100, 0.045)""")
sub("""_rrect(2.01, sy * 0.600, 0.030, 0.012, 0.010)""", """_rrect(1.97, sy * 0.640, 0.030, 0.012, 0.010)""")
sub("((1.30, -0.700), (1.30, 0.700), (1.90, -0.735), (1.90, 0.735))", "((1.10, -0.700), (1.10, 0.700), (1.80, -0.760), (1.80, 0.760))")
sub("ctr = (1.64, 0.0)", "ctr = (1.40, 0.0)")
# the cowl
sub("    hw = 0.745\n", "    hw = 0.700\n")
sub("x = 1.192 + 0.046 * t", "x = 0.975 + 0.046 * t")
sub("z = 1.092 + (zA(1.238, 0.0) - 1.092) * (t ** 1.3)", "z = 1.002 + (zA(1.021, 0.0) - 1.002) * (t ** 1.3)")
sub("x = 1.204 + 0.006 * k", "x = 0.987 + 0.006 * k")
sub("z = 1.092 + (zA(1.238, 0.0) - 1.092) * (((x - 1.192) / 0.046) ** 1.3) + 0.0035", "z = 1.002 + (zA(1.021, 0.0) - 1.002) * (((x - 0.975) / 0.046) ** 1.3) + 0.0035")
sub("-0.60 + 1.20 * j / 12.0", "-0.56 + 1.12 * j / 12.0")
sub("[(1.244, -hw", "[(1.027, -hw")
sub("zA(1.244, 0.0)", "zA(1.027, 0.0)")
sub('(("L", 0.620, 0.210, 0.640), ("R", 0.090, -0.560, -0.590))', '(("L", 0.600, 0.200, 0.620), ("R", 0.080, -0.520, -0.550))')
sub("        z = 1.098\n", "        z = 1.008\n")
sub("(1.172, y0", "(0.955, y0")
sub("(1.168, y1", "(0.951, y1")
sub("(1.17, yp", "(0.953, yp")
# names
sub('"ZX_HoodLiner"', '"Z9_HoodLiner"')
sub('def build_frunk(collection="ZX_Details")', 'def build_frunk(collection="Z9_Details")')
sub('"ZX_BonnetGrp"', '"Z9_BonnetGrp"', 0)
sub('bpy.data.objects["ZX_Hood"]', 'bpy.data.objects["Z9_Hood"]')
sub('X.join("ZX_Bonnet"', 'X.join("Z9_Bonnet"')
sub('("Zeekr7X_Bonnet", "ZX_BonnetGrp")', '("DenzaZ9_Bonnet", "Z9_BonnetGrp")') if '("Zeekr7X_Bonnet", "ZX_BonnetGrp")' in s else None
sub('bpy.data.objects.get("ZX_Bonnet")', 'bpy.data.objects.get("Z9_Bonnet")')
sub('def open_hull(hull="ZX_Shell_Shadow")', 'def open_hull(hull="Z9_Shell_Shadow")')
sub('[(x, y, 1.30) for (x, y) in rim_outline(inset=0.050)],\n                         (0.0, 0.0, 1.0), back=0.60, front=0.0)',
    '[(x, y, 1.10) for (x, y) in rim_outline(inset=0.050)],\n                         (0.0, 0.0, 1.0), back=0.70, front=0.0)')
s = s.replace('("Zeekr7X_Bonnet", "Z9_BonnetGrp")', '("DenzaZ9_Bonnet", "Z9_BonnetGrp")')
s = s.replace("ZX_", "Z9_")
io.open(ROOT + "z9_bays.py", "w", encoding="utf-8", newline="\n").write(s)
print("wrote z9_bays.py", len(s.splitlines()), "lines")
