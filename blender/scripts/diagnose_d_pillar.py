import sys
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

import bpy
import build_g9l

def diagnose():
    build_g9l.main(reset=True, scene=False)
    print("=== OBJECTS NEAR D-PILLAR (x in [-2.1, -1.7], z in [1.1, 1.7]) ===")
    for o in bpy.data.objects:
        if o.type == 'MESH':
            coords = [v.co for v in o.data.vertices if -2.15 < v.co.x < -1.70 and 0.5 < abs(v.co.y) < 1.0 and 1.1 < v.co.z < 1.75]
            if coords:
                mats = [m.name for m in o.data.materials if m]
                print(f"  {o.name}: count={len(coords)}, mats={mats}, visible={not o.hide_render}")

    print("\n=== HOOD CENTERLINE PROFILE (y ~ 0.0) ===")
    hood = bpy.data.objects.get('G9L_Hood')
    if hood:
        center_pts = sorted([v.co for v in hood.data.vertices if abs(v.co.y) < 0.05], key=lambda c: c.x)
        print(f"Hood center points (x, z):")
        for pt in center_pts[::max(1, len(center_pts)//10)]:
            print(f"  x={pt.x:.3f}, y={pt.y:.3f}, z={pt.z:.3f}")
            
    print("\n=== FASCIA / APRON NEAR HOOD ===")
    for name in ['G9L_RobotFace_LED', 'G9L_Nose_Cap', 'G9L_Lower_Apron']:
        o = bpy.data.objects.get(name)
        if o:
            pts = sorted([v.co for v in o.data.vertices if abs(v.co.y) < 0.05], key=lambda c: c.z)
            if pts:
                print(f"{name} at center: z min={pts[0].z:.3f}, z max={pts[-1].z:.3f}, x min={pts[0].x:.3f}")

if __name__ == "__main__":
    diagnose()
