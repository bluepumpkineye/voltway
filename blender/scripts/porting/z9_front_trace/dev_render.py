"""Cycles stills of the built Z9. blender -b z9_front.blend --python dev_render.py -- VIEWS TAG [PAINT] [RES] [SAMP]
VIEWS: comma list of names from CAMS below ("front" = the solved photo camera front_black)."""
import math
import os
import sys

import bpy
from mathutils import Vector

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SP = os.environ.get("Z9DEV") or os.path.join(REPO, "blender", "renders", "z9_dev")
os.makedirs(SP, exist_ok=True)

sys.path.append(os.path.join(REPO, "blender", "scripts"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VIEWS = (argv[0] if len(argv) > 0 else "front").split(",")
TAG = argv[1] if len(argv) > 1 else "x"
PAINT = argv[2] if len(argv) > 2 else "black"
RES = int(argv[3]) if len(argv) > 3 else 1600
SAMP = int(argv[4]) if len(argv) > 4 else 48

# name: (location, target, lens mm at 36 mm sensor)
CAMS = {
    "f34l": ((5.2, 3.6, 1.05), (2.2, 0.2, 0.55), 55.0),        # front, car's left (+y) side
    "f34r": ((5.2, -3.6, 1.05), (2.2, -0.2, 0.55), 55.0),
    "f34c": ((4.6, 2.4, 0.75), (2.4, 0.35, 0.55), 70.0),
    "lamp": ((4.2, 2.0, 0.95), (2.3, 0.62, 0.72), 100.0),
    "lampend": ((3.0, 2.6, 1.05), (2.15, 0.88, 0.72), 110.0),
    "corner1": ((2.9, 1.9, 1.5), (2.05, 0.86, 0.80), 120.0),
    "corner2": ((1.3, 2.0, 1.4), (2.05, 0.86, 0.80), 120.0),
    "corner3": ((2.0, 2.0, 1.6), (2.05, 0.86, 0.80), 130.0),
    "low": ((3.6, 1.6, 0.18), (2.4, 0.35, 0.22), 60.0),
    "sidefront": ((2.45, 4.5, 0.55), (2.35, 0.3, 0.45), 90.0),
    "lampside": ((2.2, 3.4, 0.8), (2.15, 0.88, 0.70), 110.0),
    "pocket": ((4.2, 2.4, 0.5), (2.35, 0.7, 0.38), 120.0),
    "grille": ((4.0, 0.9, 0.45), (2.4, 0.15, 0.25), 110.0),
    "bump": ((4.0, 1.1, 0.55), (2.4, 0.45, 0.42), 100.0),
    "r34": ((-5.2, 3.6, 1.1), (-2.3, 0.0, 0.62), 55.0),
    "rear": ((-8.0, 0.0, 0.7), (-2.4, 0.0, 0.62), 85.0),
    "rplate": ((-4.2, 1.8, 0.8), (-2.5, 0.1, 0.5), 80.0),
    "plan": ((2.4, 0.0, 7.0), (2.4, 0.0, 0.0), 60.0),
    "side": ((2.1, 12.0, 0.65), (2.1, 0.0, 0.62), 90.0),
}


def gpu():
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    try:
        pref = bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX', 'CUDA'):
            try:
                pref.compute_device_type = t
                pref.get_devices()
                if any(d.type == t for d in pref.devices):
                    for d in pref.devices:
                        d.use = (d.type == t)
                    scn.cycles.device = 'GPU'
                    break
            except Exception:
                continue
    except Exception as e:
        print("gpu notice", e)
    scn.cycles.samples = SAMP
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = 6
    scn.view_settings.view_transform = 'Khronos PBR Neutral' if 'Khronos PBR Neutral' in [
        i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Standard'


def world():
    scn = bpy.context.scene
    w = bpy.data.worlds.new("W_dev")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    grad = nt.nodes.new('ShaderNodeTexGradient')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.55, 0.57, 0.6, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.15
    nt.links.new(bg.outputs[0], out.inputs[0])
    scn.world = w
    # a soft key from above-front
    for nm, loc, e, size in (("L_top", (1.0, 0.0, 6.0), 900.0, 6.0), ("L_front", (9.0, 3.0, 3.0), 500.0, 4.0)):
        ld = bpy.data.lights.new(nm, 'AREA')
        ld.energy = e
        ld.size = size
        ob = bpy.data.objects.new(nm, ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = loc
        d = Vector((1.5, 0.0, 0.5)) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    # floor
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.name = "DEV_Floor"
    m = bpy.data.materials.new("M_DEV_Floor")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.8, 0.8, 0.82, 1)
    b.inputs['Roughness'].default_value = 0.35
    fl.data.materials.append(m)


def paint():
    if PAINT == "keep":
        return
    cols = {"black": (0.006, 0.006, 0.008, 1), "white": (0.8, 0.8, 0.78, 1), "grey": (0.07, 0.075, 0.09, 1)}
    for m in bpy.data.materials:
        if m.name.startswith("M_Paint") and m.use_nodes:
            b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if b:
                b.inputs['Base Color'].default_value = cols.get(PAINT, cols["black"])
                print("paint override:", m.name)


def cam_obj(name):
    scn = bpy.context.scene
    if name == "front":
        import z9_ref_match as RM
        cam = RM.camera("front_black")
        scn.render.resolution_x, scn.render.resolution_y = 3840, 2880
        scn.render.resolution_percentage = int(100 * RES / 3840.0)
        return cam
    if name == "rearblack":
        import z9_ref_match as RM
        cam = RM.camera("rear_black")
        scn.render.resolution_x, scn.render.resolution_y = 3840, 2880
        scn.render.resolution_percentage = int(100 * RES / 3840.0)
        return cam
    loc, tgt, lens = CAMS[name]
    cd = bpy.data.cameras.new("C_" + name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.05
    cd.clip_end = 200
    ob = bpy.data.objects.new("C_" + name, cd)
    scn.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scn.render.resolution_x, scn.render.resolution_y = RES, int(RES * 0.5625)
    scn.render.resolution_percentage = 100
    return ob


gpu()
world()
paint()
scn = bpy.context.scene
for o in scn.objects:
    if o.name in ("Ground",):
        o.hide_render = True
for v in VIEWS:
    cam = cam_obj(v)
    scn.camera = cam
    path = os.path.join(SP, "r_%s_%s.png" % (TAG, v))
    scn.render.filepath = path
    scn.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)
