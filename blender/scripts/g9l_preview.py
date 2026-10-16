"""Render 4 preview shots of the rebuilt XPeng G9L model for visual verification.
"""
import os
import sys
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

import build_g9l
import scene_setup as SC

def main():
    print("Building G9L for preview...")
    build_g9l.main(reset=True, scene=True)
    
    out_dir = os.path.normpath(os.path.join(_HERE, "..", "renders"))
    os.makedirs(out_dir, exist_ok=True)
    
    views = [
        ("hero_f34", "g9l_preview_f34.png"),
        ("front", "g9l_preview_front.png"),
        ("side", "g9l_preview_side.png"),
        ("rear_34", "g9l_preview_r34.png"),
    ]
    
    for cam, fname in views:
        print(f"Rendering {cam} -> {fname}...")
        SC.render(cam, fname, samples=64, res=(1280, 720), engine='BLENDER_EEVEE', out_dir=out_dir)
        print(f"Done {fname}")
        
    print("All preview renders completed.")

if __name__ == "__main__":
    main()
