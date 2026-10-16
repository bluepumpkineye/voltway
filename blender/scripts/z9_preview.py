"""Render preview shots of the Denza Z9 model for visual verification."""
import os
import sys
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

import build_z9
import scene_setup as SC


def render_current():
    out_dir = os.path.normpath(os.path.join(_HERE, "..", "renders"))
    os.makedirs(out_dir, exist_ok=True)
    views = [
        ("hero_f34", "z9_preview_f34.png"),
        ("front",    "z9_preview_front.png"),
        ("side",     "z9_preview_side.png"),
        ("rear",     "z9_preview_rear.png"),
        ("rear_34",  "z9_preview_r34.png"),
        ("top",      "z9_preview_top.png"),
    ]
    for cam, fname in views:
        print(f"Rendering {cam} -> {fname}...")
        SC.render(cam, fname, samples=64, res=(1280, 720), engine="BLENDER_EEVEE", out_dir=out_dir)
        print(f"Done {fname}")
    print("All Z9 preview renders completed.")


def main():
    print("Building Denza Z9 for preview...")
    build_z9.main(reset=True, scene=True)
    render_current()


if __name__ == "__main__":
    main()
