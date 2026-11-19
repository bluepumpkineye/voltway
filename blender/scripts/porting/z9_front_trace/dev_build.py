"""Headless Z9 build -> z9_full.blend (the fast loop). Usage: blender -b --factory-startup --python dev_build.py"""
import os
import sys
import time

sys.path.append(os.path.join(REPO, "blender", "scripts"))
import bpy

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SP = os.environ.get("Z9DEV") or os.path.join(REPO, "blender", "renders", "z9_dev")
os.makedirs(SP, exist_ok=True)

t = time.time()
import build_z9
out = build_z9.main(reset=True, scene=False, wheels=True)
print("BUILD tris", out["tris"], "%.0f s" % (time.time() - t))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SP, "z9_full.blend"))
print("SAVED %.0f s" % (time.time() - t))
