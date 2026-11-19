"""Overlay of z9_front.blend through the photo camera. blender -b z9_front.blend --python dev_overlay2.py -- TAG"""
import os, sys
import bpy

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SP = os.environ.get("Z9DEV") or os.path.join(REPO, "blender", "renders", "z9_dev")
os.makedirs(SP, exist_ok=True)
sys.path.append(os.path.join(REPO, "blender", "scripts"))
TAG = sys.argv[sys.argv.index("--") + 1]
import z9_ref_match as RM
RM._R.PP["front_black"] = (17.0, 0.0)
print("OUT", RM.overlay("front_black", TAG))
