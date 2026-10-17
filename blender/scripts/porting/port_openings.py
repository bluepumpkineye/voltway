"""Port blender/scripts/zx_openings.py to g9l_openings.py (or z9_openings.py) by name substitution.
usage: python port_openings.py g9l|z9"""
import io
import sys

car = sys.argv[1]
import os
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) + "/"
src = io.open(ROOT + "zx_openings.py", encoding="utf-8").read()

CFG = {
    "g9l": dict(
        P="g9l", PREFIX="G9L", GLTF="XpengG9L", NAME="XPeng G9L", PAINT="M_Paint_G9L_Purple",
        door_f_row=('"G9L_Door_Front", "G9L_Glass_DoorFront", "G9L_Handle_F", "G9L_Handle_Rim_F",\n'
                    '              "G9L_Mirror_Head", "G9L_Mirror_Stalk", "G9L_Mirror_Glass"'),
        door_r_row='"G9L_Door_Rear", "G9L_Glass_DoorRear", "G9L_Handle_R", "G9L_Handle_Rim_R"',
    ),
    "z9": dict(
        P="z9", PREFIX="Z9", GLTF="DenzaZ9", NAME="Denza Z9", PAINT="M_Paint_Z9_Purple",
        door_f_row=('"Z9_Door_Front", "Z9_Glass_DoorFront", "Z9_Handle_F", "Z9_Handle_Rim_F",\n'
                    '              "Z9_Mirror_Head", "Z9_Mirror_Stalk", "Z9_Mirror_Glass", "Z9_Mirror_Cam_Pod"'),
        door_r_row='"Z9_Door_Rear", "Z9_Glass_DoorRear", "Z9_Handle_R", "Z9_Handle_Rim_R"',
    ),
}[car]

s = src
s = s.replace('"""Zeekr 7X openings:', '"""%s openings:' % CFG["NAME"])
s = s.replace("import zx_panels as PN", "import %s_panels as PN" % CFG["P"])
s = s.replace("import zx_surface as S", "import %s_surface as S" % CFG["P"])
s = s.replace("import zx_openings as OP", "import %s_openings as OP" % CFG["P"])
s = s.replace("OP.", "OP.")
# rows
a = s.index("ROWS = {")
b = s.index("HINGE_Z")
rows = (
    "ROWS = {\n"
    '    "front": (' + CFG["door_f_row"] + "),\n"
    '    "rear": (' + CFG["door_r_row"] + "),\n"
    "}\n"
)
s = s[:a] + rows + s[b:]
s = s.replace('PAINT = "M_Paint_ZX_Blue"', 'PAINT = "%s"' % CFG["PAINT"])
# hinge
s = s.replace("x = PN._DOOR_F_EDGE(HINGE_Z)", "x = PN._DOOR_F_EDGE(HINGE_Z)")
s = s.replace("x = PN._DOOR_B_EDGE(HINGE_Z) - 0.012",
              "x = PN._DOOR_SPLIT(HINGE_Z) - 0.012" if car == "g9l" else "x = PN.X_BPILLAR_F - 0.012")
# names
s = s.replace("ZX_DoorGrp_", "%s_DoorGrp_" % CFG["PREFIX"])
s = s.replace("ZX_DoorFrameGrp_", "%s_DoorFrameGrp_" % CFG["PREFIX"])
s = s.replace("ZX_Door_", "%s_Door_" % CFG["PREFIX"])
s = s.replace("ZX_DoorFrame_", "%s_DoorFrame_" % CFG["PREFIX"])
s = s.replace("ZX_DoorRing_", "%s_DoorRing_" % CFG["PREFIX"])
s = s.replace("ZX_DoorBead_", "%s_DoorBead_" % CFG["PREFIX"])
s = s.replace('"Zeekr7X_Door_"', '"%s_Door_"' % CFG["GLTF"])
s = s.replace('"Zeekr7X_DoorFrame_"', '"%s_DoorFrame_"' % CFG["GLTF"])
s = s.replace("ZX_Greenhouse_Black", "%s_Greenhouse_Black" % CFG["PREFIX"])
s = s.replace("ZX_Shell_Shadow", "%s_Shell_Shadow" % CFG["PREFIX"])
s = s.replace('collection="ZX_Interior"', 'collection="%s_Interior"' % CFG["PREFIX"])
s = s.replace("import zx_interior_doors as DR", "import %s_interior_doors as DR" % CFG["P"])
s = s.replace('"ZX_Door_Front"', '"%s_Door_Front"' % CFG["PREFIX"])
s = s.replace("ZX_", CFG["PREFIX"] + "_")
io.open(ROOT + "%s_openings.py" % CFG["P"], "w", encoding="utf-8", newline="\n").write(s)
print("wrote", CFG["P"] + "_openings.py", len(s.splitlines()), "lines")
