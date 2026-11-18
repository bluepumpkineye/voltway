"""Render OUR Mona cabin from where XPENG's Cabin 360 cameras stood (Phase 1 of the xpeng.guru benchmark).

    # once (about 4 min): build the whole car (body, glass, cabin) in an empty file and save it
    blender -b --factory-startup --python blender/scripts/mona_pano_ab.py -- build <cabin.blend>
    # after editing the cabin code: rebuild only the cabin inside that file (about 50 s)
    blender -b --factory-startup --python blender/scripts/mona_pano_ab.py -- reint <cabin.blend>
    # then, per camera (about 35 s at 2048 x 1024, 128 samples): an equirectangular Cycles render
    blender -b --factory-startup --python blender/scripts/mona_pano_ab.py -- render <cabin.blend> <front|back> <out.png> [width=2048] [samples=96]

Camera poses come from mona_pano_cams.json (solved by scripts/photo-tools/pano_solve.cjs). The equirect centre is straight
ahead (+x), like the xpeng.guru panoramas, so `scripts/photo-tools/pano_ab.cjs` can cut both into the same rectilinear
views and lay them side by side. Light = our hall probe (public/models/cabin-hall.hdr); camera rays see a flat hazy grey
(the target shows a misty mountain plate through the glass, we have no glass in this file).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
HALL = os.path.join(ROOT, "public", "models", "cabin-hall.hdr")
HAZE = (0.20, 0.235, 0.25)      # what the camera rays see outside (linear), a misty blue-grey


def build(path):
    """The whole car, as export_mona.web_cabin builds it: the cabin file alone is a sealed box (its black leak fillers sit
    where the exterior's glazing lets the light and the view in), so the body and glass have to be there too."""
    import export_mona as EM
    import build_mona
    build_mona.main(reset=True, scene=True)
    import mona_interior as RI
    RI.main(lights=False)
    import mona_gate as RG
    RG.build_boot()
    RG.build_boot_details()
    RG.build_liner()
    EM.prepare_exterior()
    EM.cabin_screens()
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    print("pano_ab: built and saved", path)


def reint(blend):
    """Rebuild only the cabin inside a saved full-car blend (about 50 s, not 4 min) and save it back."""
    bpy.ops.wm.open_mainfile(filepath=blend)
    import mona_interior as RI
    RI.main(lights=False)
    import mona_gate as RG
    RG.build_boot()
    RG.build_boot_details()
    RG.build_liner()
    import export_mona as EM
    EM.cabin_screens()
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("pano_ab: cabin rebuilt in", blend)


def _world():
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W_PanoAB")
    scn.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(HALL, check_existing=True)
    lit = nt.nodes.new('ShaderNodeBackground')
    lit.inputs["Strength"].default_value = 1.0
    flat = nt.nodes.new('ShaderNodeBackground')
    flat.inputs["Color"].default_value = HAZE + (1.0,)
    flat.inputs["Strength"].default_value = 1.0
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(env.outputs["Color"], lit.inputs["Color"])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(lit.outputs["Background"], mix.inputs[1])
    nt.links.new(flat.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def render(blend, which, out_png, width=2048, samples=96):
    from carkit import scene as SC
    bpy.ops.wm.open_mainfile(filepath=blend)
    scn = bpy.context.scene
    cams = json.load(open(os.path.join(HERE, "mona_pano_cams.json")))
    pos = Vector(cams[which]["pos"])
    cd = bpy.data.cameras.new("CAM_pano")
    try:
        cd.panorama_type = 'EQUIRECTANGULAR'
    except Exception:
        cd.cycles.panorama_type = 'EQUIRECTANGULAR'
    cd.type = 'PANO'
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("CAM_pano", cd)
    scn.collection.objects.link(cam)
    cam.location = pos
    yaw = math.radians(cams[which].get("yaw_offset_deg", 0.0))
    fwd = Vector((math.cos(yaw), math.sin(yaw), 0.0))          # model +x = straight ahead
    cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
    scn.camera = cam
    _world()
    scn.render.resolution_x, scn.render.resolution_y = int(width), int(width) // 2
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.look = 'None'
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    SC.use_cycles(samples, denoise=True)
    scn.render.filepath = out_png
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    # what the web cabin's own light passes hide: the black underlays behind the glass and the ground
    import export_mona as EM
    for n in EM.BLACKOUT + ("XpengMonaL05_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob is not None:
            ob.hide_render = True
    # The solved camera can stand INSIDE one of our parts (the front camera is in the driver's headrest: our seat is too far
    # forward against the screen). Hide whatever contains the camera point, and say so: that overlap is itself a finding.
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = [min(c[i] for c in cs) - 0.03 for i in range(3)]
        hi = [max(c[i] for c in cs) + 0.03 for i in range(3)]
        # compact parts only (a headrest): a pillar's or headliner's box wraps the whole cabin and must stay
        if max(hi[i] - lo[i] for i in range(3)) < 0.6 and all(lo[i] <= pos[i] <= hi[i] for i in range(3)):
            ob.hide_render = True
            print("pano_ab: camera inside %s (hidden for the render, with its posts and sleeves)" % ob.name)
            for o2 in bpy.data.objects:                   # its posts and sleeves are named after it
                if o2.name.startswith(ob.name):
                    o2.hide_render = True
    from carkit import bake as BK
    with BK.thin_glass():
        bpy.ops.render.render(write_still=True)
    print("pano_ab: rendered", out_png)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if a and a[0] == "build":
        build(a[1])
    elif a and a[0] == "reint":
        reint(a[1])
    elif a and a[0] == "render":
        render(a[1], a[2], a[3], *(int(x) for x in a[4:6]))
    else:
        print(__doc__)
