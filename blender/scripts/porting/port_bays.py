"""Port blender/scripts/zx_bays.py to g9l_bays.py by substitution, with the G9L's measured numbers.
usage: python port_bays.py g9l"""
import io
import sys

car = sys.argv[1]
import os
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) + "/"
s = io.open(ROOT + "zx_bays.py", encoding="utf-8").read()

P = {"g9l": dict(PRE="G9L", GLTF="XpengG9L", NAME="XPeng G9L")}[car]


def sub(old, new, count=1):
    global s
    if s.count(old) < 1:
        raise SystemExit("missing: " + old[:60])
    s = s.replace(old, new) if count == 0 else s.replace(old, new, count)


# header
a = s.index('"""Zeekr 7X bays')
b = s.index('import math')
s = s[:a] + '''"""%(NAME)s bays: the frunk under the bonnet, from the opening photographs (Autohome series 8659,
cat 12: c12_0001-6 on the purple car, c12_0068-73 on the grey one; blender/reference/xpeng-g9l/openings).

What the photographs show, from the cowl forward: a black wiper well under the windscreen's foot with a
ribbed vent strip and the two wipers parked along the glass; a black moulded tray the whole width of the hood
with a thick seal round its rim; a deep rounded-rectangle storage tub in the middle; the blue washer-fluid cap
at the right rear (the passenger side); a rounded slot at each front corner; two gas struts at the cowl's
corners; the bonnet's underside lined with a black pad inside its painted frame.

    import %(P)s_bays as BY
    BY.build_frunk()      # the static bay (%(PRE)s_Details)
    BY.split_bonnet()     # %(PRE)s_Bonnet: hood + liner, origin on the hinge
    BY.open_hull()        # the hull's roof under the bonnet

Car axes +x forward, +y left, z up.
"""
''' % dict(P=car, PRE=P["PRE"], NAME=P["NAME"]) + s[b:]

# constants
a = s.index("# plan half-width of the hood by x")
b = s.index("def hood_half(x):")
s = s[:a] + '''# plan half-width of the hood by x, measured on the built panel (G9L_Hood)
HOOD_HALF = [(1.20, 0.919), (1.25, 0.951), (1.5, 0.942), (1.9, 0.912), (2.15, 0.862),
             (2.20, 0.866), (2.25, 0.706), (2.30, 0.212), (2.312, 0.0)]
HOOD_HINGE = (1.215, 1.247)    # (x, z) of the hinge axis, along y, under the rear edge
HOOD_DEG = 62.0
APRON_DROP = 0.080             # the tray's height under the hood's top surface
TUB_DEPTH = 0.225
# the tub's outline, half-width by x from its rear edge round the front (the +y half; mirrored): a wide
# rounded rectangle, about 1.0 m across and 0.5 m deep (c12_0002, c12_0070)
TUB = [(1.560, 0.0), (1.560, 0.400), (1.572, 0.465), (1.615, 0.505), (1.760, 0.520),
       (1.900, 0.500), (1.980, 0.460), (2.020, 0.385), (2.032, 0.220), (2.032, 0.0)]
# the tub wall's offsets (inward, down) from the rim
WALL = [(0.0, 0.0), (0.004, -0.006), (0.010, -0.018), (0.016, -0.065), (0.022, -0.140),
        (0.032, -0.200), (0.048, -0.225)]


''' + s[b:]

sub('"ZX_Hood") or bpy.data.objects["ZX_Bonnet"]', '"G9L_Hood") or bpy.data.objects["G9L_Bonnet"]')
# no divider in the G9L's tub: the block is removed
a = s.index("    # the divider: a low wall across the tub")
b = s.index("    # the washer cap, right rear of the tray")
s = s[:a] + s[b:]
sub("cx, cy = 1.545, -0.545", "cx, cy = 1.500, -0.775")
sub("""_rrect(2.00, sy * 0.600, 0.100, 0.130, 0.040)""", """_rrect(1.98, sy * 0.600, 0.100, 0.130, 0.040)""")
sub("""_rrect(2.01, sy * 0.600, 0.030, 0.012, 0.010)""", """_rrect(1.99, sy * 0.600, 0.030, 0.012, 0.010)""")
sub("((1.30, -0.700), (1.30, 0.700), (1.90, -0.735), (1.90, 0.735))", "((1.60, -0.860), (1.60, 0.860), (2.04, -0.300), (2.04, 0.300))")
sub("ctr = (1.64, 0.0)", "ctr = (1.80, 0.0)")
# the cowl
sub("    hw = 0.745\n", "    hw = 0.880\n")
sub("z = 1.092 + (zA(1.238, 0.0) - 1.092) * (t ** 1.3)", "z = 1.255 + (zA(1.238, 0.0) - 1.255) * (t ** 1.3)")
sub("z = 1.092 + (zA(1.238, 0.0) - 1.092) * (((x - 1.192) / 0.046) ** 1.3) + 0.0035", "z = 1.255 + (zA(1.238, 0.0) - 1.255) * (((x - 1.192) / 0.046) ** 1.3) + 0.0035")
sub("for k in range(7):\n        x = 1.204", "for k in range(7):\n        x = 1.204")
sub("-0.60 + 1.20 * j / 12.0", "-0.74 + 1.48 * j / 12.0")
sub('(("L", 0.620, 0.210, 0.640), ("R", 0.090, -0.560, -0.590))', '(("L", 0.800, 0.260, 0.820), ("R", 0.110, -0.740, -0.770))')
sub("        z = 1.098\n", "        z = 1.262\n")
# names
sub('"ZX_HoodLiner"', '"G9L_HoodLiner"')
sub('def build_frunk(collection="ZX_Details")', 'def build_frunk(collection="G9L_Details")')
sub('"ZX_BonnetGrp"', '"G9L_BonnetGrp"', 0)
sub('bpy.data.objects["ZX_Hood"]', 'bpy.data.objects["G9L_Hood"]')
sub('X.join("ZX_Bonnet"', 'X.join("G9L_Bonnet"')
sub('("Zeekr7X_Bonnet", "G9L_BonnetGrp")', '("XpengG9L_Bonnet", "G9L_BonnetGrp")')
sub('bpy.data.objects.get("ZX_Bonnet")', 'bpy.data.objects.get("G9L_Bonnet")')
sub('def open_hull(hull="ZX_Shell_Shadow")', 'def open_hull(hull="G9L_Shell_Shadow")')
sub('[(x, y, 1.30) for (x, y) in rim_outline(inset=0.050)],\n                         (0.0, 0.0, 1.0), back=0.60, front=0.0)', '[(x, y, 1.45) for (x, y) in rim_outline(inset=0.050)],\n                         (0.0, 0.0, 1.0), back=0.85, front=0.0)')
s = s.replace("ZX_", "G9L_")
io.open(ROOT + "%s_bays.py" % car, "w", encoding="utf-8", newline="\n").write(s)
print("wrote", car + "_bays.py", len(s.splitlines()), "lines")
