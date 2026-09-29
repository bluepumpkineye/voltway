"""Lookdev scene: studio light rig, floor, camera book, render settings.

Why a rig and not just an HDRI
------------------------------
Lit by a Poly Haven HDRI alone the paint had nothing to reflect, and every
panel read as untextured clay. A car is a mirror with colour in it: what you
see on a flank is the reflected image of the light sources. So the rig is built
the way an automotive photographer builds one - a long strip to draw the
unbroken highlight down the flank, a top softbox so a black roof reads as a
roof, kickers to separate nose and tail, and a low bounce per wheel, because
dark wheels otherwise collapse to solid black. The strip is 9 m for a 5.1 m
car: the reflection of a finite strip foreshortens hard at both ends.

Light powers are calibrated so a lit panel's diffuse radiance sits near its
albedo at exposure 0. The first rig ran ~5x hotter and Khronos Neutral
desaturated the SU7's yellow to cream.

View transform: Khronos PBR Neutral, not AgX. AgX rolls saturation off with
the highlights, which turned racing yellow to mustard. PBR Neutral preserves
hue and saturation, and three.js implements it identically
(THREE.NeutralToneMapping), so the web view matches the renders.

Cameras and lights are placed for a ~5.1 m car. For a car of a different size
pass scale=length/5.115 to main(); for an SUV raise the aim points too.
"""
import math
import os

import bpy
from mathutils import Vector

RENDER_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "renders"))

# Camera book: (location, aim point, focal length mm), for the car's LEFT
# side facing the camera at -Y. Camera HEIGHT matters most: hero shots sit at
# shoulder height or below (~1.05 m) so the roofline reads long and low; a
# 2.7 m camera looks down and flattens the stance into a plan view.
CAMERAS = {
    "hero_f34":  ((10.34, -8.68, 1.05), (0.25, 0.0, 0.72), 100),
    "hero_low":  ((9.60, -8.05, 0.55), (0.20, 0.0, 0.80), 100),
    "side":      ((0.02, -26.0, 0.78), (0.02, 0.0, 0.70), 165),
    "front":     ((14.00, -0.22, 0.62), (0.0, 0.0, 0.64), 135),
    "front_34":  ((8.60, -6.10, 0.86), (0.55, 0.0, 0.68), 85),
    "rear_34":   ((-9.90, -8.30, 1.10), (0.10, 0.0, 0.76), 100),
    "rear":      ((-13.60, 0.20, 0.70), (0.0, 0.0, 0.72), 135),
    "top":       ((0.0, 0.0, 13.2), (0.0, 0.0, 0.70), 70),
    # detail cameras for the quality gates
    "det_lamp":  ((5.40, -3.05, 0.92), (2.16, -0.70, 0.66), 135),
    "det_nose":  ((6.30, -1.65, 0.80), (2.30, -0.15, 0.52), 120),
    "det_wheel": ((4.05, -4.35, 0.62), (1.53, -0.90, 0.38), 135),
    "det_paint": ((2.10, -5.05, 1.55), (0.20, -0.62, 0.90), 110),
    "det_rear":  ((-5.10, -4.35, 1.34), (-2.05, -0.50, 0.92), 120),
    "det_gap":   ((3.05, -4.90, 1.28), (0.55, -0.82, 0.86), 135),
}

# name, size_x, size_y, location, aim, power, spread degrees
RIG = [
    ("L_FlankKey",  9.0, 0.60, (0.30, -3.40, 3.20), (0.30, 0.00, 0.75), 160, 75),
    ("L_FarFill",   6.0, 0.45, (0.00, 3.00, 2.90), (0.00, 0.00, 0.80), 70, 90),
    ("L_TopBox",    6.0, 2.60, (0.00, 0.00, 4.20), (0.00, 0.00, 0.70), 90, 120),
    ("L_NoseKick",  2.4, 1.60, (5.60, -3.20, 1.90), (2.00, -0.50, 0.65), 65, 60),
    ("L_RearKick",  2.2, 1.40, (-5.60, -2.40, 2.10), (-2.00, -0.40, 0.80), 55, 60),
    ("L_RimEdge",   5.0, 0.35, (-2.00, 4.20, 2.60), (0.00, 0.00, 1.00), 95, 50),
    ("L_WheelF",    0.9, 0.30, (1.55, -2.40, 0.30), (1.55, -0.85, 0.36), 8, 80),
    ("L_WheelR",    0.9, 0.30, (-1.44, -2.40, 0.30), (-1.44, -0.85, 0.36), 8, 80),
]


def _scaled(p, s):
    return (p[0] * s, p[1] * s, p[2])


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def build_cameras(book=None, scale=1.0, prefix="CAM_"):
    made = {}
    for name, (loc, tgt, lens) in (book or CAMERAS).items():
        cname = prefix + name
        cam = bpy.data.objects.get(cname)
        if cam is None:
            data = bpy.data.cameras.new(cname)
            cam = bpy.data.objects.new(cname, data)
            bpy.context.scene.collection.objects.link(cam)
        cam.data.lens = lens
        cam.data.clip_start = 0.01
        cam.data.clip_end = 200.0
        cam.data.sensor_width = 36.0
        cam.data.dof.use_dof = False
        cam.location = Vector(_scaled(loc, scale) if scale != 1.0 else loc)
        aim(cam, _scaled(tgt, scale) if scale != 1.0 else tgt)
        made[name] = cam
    return made


def build_lights(rig=None, scale=1.0):
    made = []
    for name, sx, sy, loc, tgt, power, spread in (rig or RIG):
        d = bpy.data.lights.get(name)
        if d is None:
            d = bpy.data.lights.new(name, 'AREA')
        d.type = 'AREA'
        d.shape = 'RECTANGLE'
        d.size = sx * scale
        d.size_y = sy
        d.energy = power
        try:
            d.spread = math.radians(spread)
        except Exception:
            pass
        ob = bpy.data.objects.get(name)
        if ob is None:
            ob = bpy.data.objects.new(name, d)
            bpy.context.scene.collection.objects.link(ob)
        ob.data = d
        ob.location = Vector(_scaled(loc, scale) if scale != 1.0 else loc)
        aim(ob, _scaled(tgt, scale) if scale != 1.0 else tgt)
        made.append(ob)
    return made


def build_reflector_card(location=(2.2, -2.6, 3.50), target=(1.0, 0.0, 1.05)):
    """A white card the windscreen reflects instead of the room - invisible to
    camera, visible to glossy rays. Only for glazing close-ups: over the flank
    and hood it mirrors as a white wash."""
    name = "REFL_Windscreen"
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name)
        w, h = 3.0, 1.5
        me.from_pydata([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)],
                       [], [[0, 1, 2, 3]])
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(location)
    aim(ob, target)

    mat = bpy.data.materials.get("M_ReflCard")
    if mat is None:
        mat = bpy.data.materials.new("M_ReflCard")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    em.inputs["Strength"].default_value = 2.0
    nt.links.new(em.outputs[0], out.inputs[0])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.visible_camera = False
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = True
    return ob


def build_ground(radius=40.0, roughness=0.16):
    """A large dark disc. Roughness 0.16: the floor reflection under a car is
    the strongest product-shot cue there is, and a rough floor throws it away."""
    name = "Ground"
    g = bpy.data.objects.get(name)
    if g is not None:
        bpy.data.objects.remove(g, do_unlink=True)
    me = bpy.data.meshes.new(name)
    n = 96
    verts = [(0.0, 0.0, 0.0)]
    verts += [(radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n), 0.0)
              for i in range(n)]
    faces = [[0, 1 + i, 1 + (i + 1) % n] for i in range(n)]
    me.from_pydata(verts, [], faces)
    me.update()
    g = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(g)

    mat = bpy.data.materials.get("M_Ground")
    if mat is None:
        mat = bpy.data.materials.new("M_Ground")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs["Base Color"].default_value = (0.020, 0.020, 0.021, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    g.data.materials.clear()
    g.data.materials.append(mat)
    return g


def world_gradient(top=(0.115, 0.122, 0.135), bottom=(0.012, 0.012, 0.014),
                   strength=1.0):
    """A clean vertical gradient world - deliberately plain. A busy studio HDRI
    put wood-grain structure across the greenhouse: the glass mirrored it."""
    w = bpy.data.worlds.get("W_Studio")
    if w is None:
        w = bpy.data.worlds.new("W_Studio")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    tex = nt.nodes.new('ShaderNodeTexCoord')
    mapr = nt.nodes.new('ShaderNodeMapRange')
    mapr.inputs["From Min"].default_value = -0.35
    mapr.inputs["From Max"].default_value = 0.55
    ramp.color_ramp.elements[0].color = bottom + (1.0,)
    ramp.color_ramp.elements[1].color = top + (1.0,)
    bg.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def use_hdri(name, strength=0.35):
    """Swap the world for an already-loaded Poly Haven HDRI (outdoor shots)."""
    w = bpy.context.scene.world
    if not w or not w.use_nodes:
        return None
    nt = w.node_tree
    img = next((i for i in bpy.data.images if name.lower() in i.name.lower()), None)
    if img is None:
        return None
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = img
    bg.inputs["Strength"].default_value = strength
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return img


HDRI_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "textures", "hdri"))


def hdri_world(path, strength=1.0, rotation=0.0, clamp=None, name="W_HDRI"):
    """An equirect HDRI file as the world (the cabin's view out and light in).

    rotation  degrees about +Z. Blender puts the image's centre column
              (u = 0.5) straight ahead, +X, and u runs clockwise seen from
              above: u = 0.5 - atan2(y, x) / 2pi. A feature at image angle a
              (= atan2 of its direction) shows at a - rotation.
    clamp     caps each channel. A clear-sky sun is ~40 000x the sky in a
              few pixels; in a per-vertex bake it lands as hard-edged blotches
              (vertices either side of a shadow edge), so the bake takes the
              sky's soft light and leaves the sun out.

    The web app shows the same file, with the same rotation, as the view out
    (VehicleViewer.OutsideWorld); keep the two in step.
    """
    img = bpy.data.images.load(path, check_existing=True)
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = img
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rotation))
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    colour = env.outputs["Color"]
    if clamp:
        mn = nt.nodes.new('ShaderNodeVectorMath')
        mn.operation = 'MINIMUM'
        mn.inputs[1].default_value = (clamp, clamp, clamp)
        nt.links.new(colour, mn.inputs[0])
        colour = mn.outputs["Vector"]
    bg.inputs["Strength"].default_value = strength
    nt.links.new(colour, bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def set_world_strength(value=1.0):
    w = bpy.context.scene.world
    if not w or not w.use_nodes:
        return None
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs["Strength"].default_value = value
            return n
    return None


def use_cycles(samples=192, denoise=True):
    """GPU path tracing via OptiX, with the OptiX denoiser."""
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'OPTIX')
        scn.cycles.device = 'GPU'
    except Exception as e:
        print("cycles GPU setup skipped:", e)
        scn.cycles.device = 'CPU'
    c = scn.cycles
    c.samples = samples
    c.use_adaptive_sampling = True
    # 0.005, not 0.01: at 0.01 the top light's reflection on the hood kept
    # Monte Carlo grain that looked like a paint texture.
    c.adaptive_threshold = 0.005
    c.use_denoising = denoise
    try:
        c.denoiser = 'OPTIX'
        c.denoising_use_gpu = True
    except Exception:
        pass
    c.max_bounces = 16
    c.diffuse_bounces = 4
    c.glossy_bounces = 8
    c.transmission_bounces = 12
    c.transparent_max_bounces = 12
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 0.6
    return scn


def use_eevee(samples=96):
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    try:
        scn.eevee.taa_render_samples = samples
    except Exception:
        pass
    return scn


def colour_management(exposure=0.0, look='None'):
    vs = bpy.context.scene.view_settings
    try:
        vs.view_transform = 'Khronos PBR Neutral'
    except TypeError:
        vs.view_transform = 'Standard'
    vs.exposure = exposure
    try:
        vs.look = look
    except TypeError:
        pass
    bpy.context.scene.render.dither_intensity = 1.0
    return vs


def render(cam_name, filename, samples=192, res=(1920, 1080), engine='CYCLES',
           out_dir=None):
    """Render one camera of the book to <out_dir or RENDER_DIR>/filename."""
    scn = bpy.context.scene
    cam = bpy.data.objects.get("CAM_" + cam_name) or bpy.data.objects.get(cam_name)
    if cam is None:
        raise KeyError("no camera " + cam_name)
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    if engine == 'CYCLES':
        use_cycles(samples)
    else:
        use_eevee(samples)
    d = out_dir or RENDER_DIR
    os.makedirs(d, exist_ok=True)
    scn.render.filepath = os.path.join(d, filename)
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    return scn.render.filepath


def main(hdri=None, scale=1.0):
    world_gradient()
    if hdri:
        use_hdri(hdri)
    build_ground()
    build_lights(scale=scale)
    cams = build_cameras(scale=scale)
    colour_management()
    use_cycles()
    print("cameras:", sorted(cams))
    print("lights :", [n[0] for n in RIG])
    return cams
