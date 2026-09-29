"""Surface QA renders: zebra reflection lines and close detail cameras.

A highlight is the reflection of a light, so the quickest honest test of a body
surface is to reflect stripes in it. Straight, evenly spaced, unbroken bands
mean the surface is fair; a band that KINKS marks a tangent break, one that
WOBBLES marks a surface that ripples, and one that STEPS marks a position gap.
Every crease the SU7 shipped by accident - the nose/fender join, the fender
crown - showed up here first.

    render("nose_34", "v5", zebra=True)   -> renders/qa/v5_nose_34_zebra.png
    add_camera("rear_door", loc, aim, lens)
"""
import os

import bpy
from mathutils import Vector

from .. import scene as SC

QA_DIR = os.path.join(SC.RENDER_DIR, "qa")

# name: (location, aim, lens) - left side (+Y), where reference photos are
QA_CAMERAS = {
    "nose_34":  ((4.6, 2.9, 0.95), (2.15, 0.62, 0.64), 85),
    "nose_top": ((3.9, 1.1, 2.6), (1.95, 0.55, 0.72), 60),
    "tail_34":  ((-4.6, 3.1, 0.95), (-2.15, 0.62, 0.62), 70),
    "flank":    ((0.1, 6.2, 0.95), (0.1, 0.9, 0.62), 40),
}


def add_camera(name, loc, aim, lens):
    QA_CAMERAS[name] = (tuple(loc), tuple(aim), lens)


def zebra_material(freq=14.0):
    m = bpy.data.materials.get("M_Zebra") or bpy.data.materials.new("M_Zebra")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = freq
    sn = nt.nodes.new('ShaderNodeMath')
    sn.operation = 'SINE'
    gt = nt.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = 0.0
    nt.links.new(tc.outputs['Reflection'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], mul.inputs[0])
    nt.links.new(mul.outputs[0], sn.inputs[0])
    nt.links.new(sn.outputs[0], gt.inputs[0])
    nt.links.new(gt.outputs[0], em.inputs['Strength'])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _camera(name):
    loc, aim, lens = QA_CAMERAS[name]
    cname = "CAM_qa_" + name
    cam = bpy.data.objects.get(cname)
    if cam is None:
        cam = bpy.data.objects.new(cname, bpy.data.cameras.new(cname))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.sensor_width = 36.0
    cam.data.clip_start = 0.02
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(aim) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return cam


def render(name, tag, zebra=False, samples=48, res=(960, 640)):
    scn = bpy.context.scene
    vl = scn.view_layers[0]
    old = (scn.camera, vl.material_override)
    try:
        scn.camera = _camera(name)
        vl.material_override = zebra_material() if zebra else None
        SC.use_cycles(16 if zebra else samples)
        scn.render.resolution_x, scn.render.resolution_y = res
        scn.render.resolution_percentage = 100
        scn.render.image_settings.file_format = 'PNG'
        scn.render.image_settings.color_mode = 'RGB'
        os.makedirs(QA_DIR, exist_ok=True)
        scn.render.filepath = os.path.join(
            QA_DIR, "%s_%s%s.png" % (tag, name, "_zebra" if zebra else ""))
        bpy.ops.render.render(write_still=True)
    finally:
        scn.camera, vl.material_override = old
    return scn.render.filepath
