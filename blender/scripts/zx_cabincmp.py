"""Zeekr 7X cabin: a fast look at the cabin from any camera, to hold beside a reference photograph.

The cabin's parts build in seconds when the exterior is left out (only the boot and the hatch
liner read the exterior's tail cap), so a hardpoint can be changed and judged in half a minute
instead of a 15 minute bake:

    blender -b --factory-startup --python-expr "import sys; \\
        sys.path.append(r'<repo>/blender/scripts'); import zx_cabincmp as CC; CC.run('tag')"

It builds the cabin (default parts: dash, screens, wheel, seats, console, doors, shell,
pedals), prints the bounding box of the parts named in `DUMP` (the numbers to put beside the
photographs' measurements), and renders each camera in CAMS with Cycles under a white world
into blender/renders/cabincmp/<tag>_<camera>.png. Compose that beside the photograph with any
image tool at one width (the 2000 px display frame the photographs were read in) and compare
sizes, gaps and heights, not shading.

The cameras (car axes: +x forward, +y left, +z up; fov_h is the horizontal field of view):

    axis      on the steering wheel's axis, 0.95 m back (c10_0002)
    centre    behind the console, at the rear seats' head height, looking at the screen
              (c10_0001; leave "seats" out of PARTS or they block the view)
    viewer    the showroom's driver eye (zeekr-7x.ts assets.driverEye) at 1280 x 720

What it found (2026-10-08): the first wheel was a circle sliced flat top and bottom, 0.39 wide
and 0.32 tall (the photographs: 0.39 x 0.37, a squircle), 3 cm too low, and the cluster 3 cm
too high under a visor that hid it, so the wheel's top bar sat inside the visor ("smashed")
and its right rim overlapped the screen's left edge from the driver's seat.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

OUT = os.path.normpath(os.path.join(_HERE, "..", "renders", "cabincmp"))
PARTS = ("dash", "screens", "wheel", "seats", "console", "doors", "shell", "pedals")
DUMP = ("wheel", "cluster", "screen", "dash", "visor", "vent", "tweeter", "pillar")


def cameras():
    import zx_interior as ZI
    t = ZI.WHEEL_TILT
    n = Vector((-math.cos(t), 0.0, math.sin(t)))
    return {
        "axis": dict(pos=tuple(Vector(ZI.WHEEL_C) + n * 0.95), aim=tuple(ZI.WHEEL_C), fov_h=58.0,
                     res=(1000, 750)),
        "centre": dict(pos=(-0.80, 0.0, 1.25), aim=(0.93, 0.0, 0.99), fov_h=57.8, res=(1000, 750)),
        "viewer": dict(pos=(0.16, 0.385, 1.22), aim=(0.302, 0.354, 1.182), fov_h=96.6,
                       res=(1280, 720)),
    }


def run(tag="cmp", parts=PARTS, cams=None, samples=32, dump=DUMP):
    from carkit import scene as SC
    bpy.ops.wm.read_homefile(use_empty=True)
    import zx_interior_shell as SH
    SH.main(lights=False, parts=list(parts))
    col = bpy.data.collections["ZX_Interior"]
    rows = []
    for o in col.all_objects:
        if o.type != 'MESH' or not any(k in o.name.lower() for k in dump):
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = [min(v[i] for v in bb) for i in range(3)]
        hi = [max(v[i] for v in bb) for i in range(3)]
        rows.append("%-34s x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
                    % (o.name, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    print("\n".join(sorted(rows)))
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W_cmp")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 1.1
    for o in col.objects:
        if o.type == 'LIGHT':
            o.data.energy *= 0.5
    os.makedirs(OUT, exist_ok=True)
    out = []
    for name, c in (cams or cameras()).items():
        cd = bpy.data.cameras.new("CAM_" + name)
        cd.sensor_fit = 'HORIZONTAL'
        cd.sensor_width = 36.0
        cd.lens = 18.0 / math.tan(math.radians(c["fov_h"]) / 2.0)
        cd.clip_start = 0.02
        cam = bpy.data.objects.new("CAM_" + name, cd)
        scn.collection.objects.link(cam)
        pos, aim = Vector(c["pos"]), Vector(c["aim"])
        cam.location = pos
        cam.rotation_euler = (aim - pos).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = c["res"]
        scn.render.resolution_percentage = 100
        SC.use_cycles(samples)
        scn.view_settings.view_transform = 'Standard'
        scn.render.image_settings.file_format = 'PNG'
        scn.render.filepath = os.path.join(OUT, "%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)
        out.append(scn.render.filepath)
        bpy.data.objects.remove(cam, do_unlink=True)
    return out
