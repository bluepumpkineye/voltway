"""The showroom's studio as Cycles renders it: the web's light rig, floor and cameras.

The showroom (src/components/viewer/StudioShowroom.tsx) lights a car with a
dark room holding a few bright shapes, the rig in src/data/studio/rig.ts. This
module builds that same list in Blender - emissive panels over a dark world, a
white floor, a camera at each of the web's named poses - so a Cycles still and
the web view are two renderings of one set, and any difference between them is
a bug to find rather than a taste to argue.

    from carkit import rig
    r = rig.read_rig()                         # parses rig.ts, the single source
    rig.build_studio(r)                        # panels, world, floor
    rig.still("hero", "out.png", dims=(4.97, 1.98, 1.65))

Axes: the web's (+x forward, +y up, +z toward the passenger side) become
Blender's (x, -z, y). Radiance: a Lightformer's colour x intensity is what
the web's cube map holds, and what the web lights the car with is that x
STUDIO_GAIN (environmentIntensity); the emission strength here is the same
product, so the two agree in scene-linear units. The web's floor panels (the
white floor as the paint sees it) are left out: Blender has the real floor.
"""
import math
import os
import re

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

RIG_TS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "..", "src", "data", "studio", "rig.ts"))
RENDER_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "..", "..", "renders", "studio"))

# StudioShowroom.tsx: the room as the camera sees it, and the floor
FLOOR_HEX = "#e9eaed"
FLOOR_RADIUS = 22.0
COVE = ("#e2e4e8", "#eff1f3", "#fafbfc")        # low, mid, high
VIEWER_EXPOSURE = 0.92                           # ShowroomViewer: toneMappingExposure

# web -> Blender axes
_C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def srgb_hex(h):
    """'#rrggbb' as scene-linear (r, g, b), as three.js reads a Color."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def _num(expr):
    """A number or an expression of numbers and Math.PI, as rig.ts writes them."""
    e = expr.strip().replace("Math.PI", repr(math.pi))
    if not re.fullmatch(r"[0-9eE+\-*/(). ]+", e):
        raise ValueError("unexpected expression in rig.ts: %r" % expr)
    return float(eval(e, {"__builtins__": {}}))


def _vec(s):
    return tuple(_num(p) for p in s.split(","))


def read_rig(path=RIG_TS):
    """src/data/studio/rig.ts as {void, gain, panels}: STUDIO_VOID as linear
    rgb, STUDIO_GAIN, and each panel's id, form, position, size, intensity,
    colour (linear rgb) and rotation (the web's Euler XYZ, or None)."""
    s = open(path, encoding="utf-8").read()
    void = re.search(r"STUDIO_VOID\s*=\s*'(#[0-9a-fA-F]{6})'", s).group(1)
    gain = float(re.search(r"STUDIO_GAIN\s*=\s*([0-9.]+)", s).group(1))
    consts = {m.group(1): _vec(m.group(2)) for m in
              re.finditer(r"const\s+(\w+)\s*:\s*V3\s*=\s*\[([^\]]+)\]", s)}
    body = s[s.index("STUDIO_RIG"):]
    panels = []
    for m in re.finditer(r"\{\s*id:\s*'([^']+)'(.*?)\}\s*,", body, re.S):
        f = m.group(2)

        def field(name, pat):
            r = re.search(name + r"\s*:\s*" + pat, f)
            return r.group(1) if r else None

        rot = field("rotation", r"(\w+|\[[^\]]+\])")
        if rot is not None:
            rot = consts[rot] if rot in consts else _vec(rot.strip("[]"))
        panels.append(dict(
            id=m.group(1),
            form=field("form", r"'(rect|circle)'"),
            position=_vec(field("position", r"\[([^\]]+)\]")),
            size=_vec(field("size", r"\[([^\]]+)\]")),
            intensity=_num(field("intensity", r"([0-9.]+)")),
            color=srgb_hex(field("color", r"'(#[0-9a-fA-F]{6})'") or "#ffffff"),
            rotation=rot))
    if not panels:
        raise RuntimeError("no panels found in " + path)
    return dict(void=srgb_hex(void), gain=gain, panels=panels)


def _rot_web(panel):
    """The panel's orientation as a 3x3 in WEB axes, as three.js would set it:
    an explicit Euler XYZ (R = Rx Ry Rz), or a look at the origin with +y up."""
    if panel["rotation"] is not None:
        rx, ry, rz = panel["rotation"]
        return (Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @
                Matrix.Rotation(rz, 3, 'Z'))
    p = Vector(panel["position"])
    z = (-p).normalized()                                # +z of the object faces the target
    x = Vector((0, 1, 0)).cross(z).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


def _panel_matrix(panel):
    """World matrix in Blender axes of the panel's plane (local +z the normal),
    turned to face the origin: a panel is a light for the car, whichever side
    the web's double-sided plane was drawn from."""
    r = _C @ _rot_web(panel) @ _C.inverted()
    pos = _C @ Vector(panel["position"])
    if r.col[2].dot(-pos) < 0:                           # facing away: spin 180 deg about local x
        r = r @ Matrix.Rotation(math.pi, 3, 'X')
    m = r.to_4x4()
    m.translation = pos
    return m


def _plane(name, form, size, col):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    w, h = size
    if form == "circle":
        n = 64
        vs = [bm.verts.new((0.5 * w * math.cos(2 * math.pi * i / n), 0.5 * w * math.sin(2 * math.pi * i / n), 0))
              for i in range(n)]
    else:
        vs = [bm.verts.new(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0),
                                        (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def build_rig(rig, skip=("floor", "floor-near"), collection="STUDIO_RIG"):
    """One emissive plane per panel, each facing the car and invisible to the
    camera and to shadow rays (a light, not a wall). Returns the objects."""
    col = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    made = []
    for p in rig["panels"]:
        if p["id"] in skip:
            continue
        ob = _plane("RIG_" + p["id"], p["form"], p["size"], col)
        ob.matrix_world = _panel_matrix(p)
        mat = bpy.data.materials.new("M_RIG_" + p["id"])
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs["Color"].default_value = tuple(p["color"]) + (1.0,)
        em.inputs["Strength"].default_value = p["intensity"] * rig["gain"]
        nt.links.new(em.outputs[0], out.inputs[0])
        ob.data.materials.append(mat)
        ob.visible_camera = False
        ob.visible_shadow = False
        made.append(ob)
    return made


def studio_world(rig):
    """The dark room the paint reflects (STUDIO_VOID x STUDIO_GAIN), with what the
    CAMERA sees swapped for the white cove, as on the web."""
    w = bpy.data.worlds.get("W_StudioRig") or bpy.data.worlds.new("W_StudioRig")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    dark = nt.nodes.new('ShaderNodeBackground')
    dark.inputs["Color"].default_value = tuple(rig["void"]) + (1.0,)
    dark.inputs["Strength"].default_value = rig["gain"]
    room = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mp = nt.nodes.new('ShaderNodeMapRange')
    mp.inputs["From Min"].default_value = -0.05
    mp.inputs["From Max"].default_value = 0.9
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = srgb_hex(COVE[0]) + (1.0,)
    ramp.color_ramp.elements[1].color = srgb_hex(COVE[2]) + (1.0,)
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = srgb_hex(COVE[1]) + (1.0,)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"])
    nt.links.new(mp.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], room.inputs["Color"])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(dark.outputs["Background"], mix.inputs[1])
    nt.links.new(room.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return w


def studio_floor(rig, shadow=None, radius=FLOOR_RADIUS):
    """The white floor. The web's floor is two panels in the rig (the paint sees
    a bright floor: radiance 1.25 near the car, 0.55 far) and a flat white for
    the camera, so here it is one disc that EMITS those radiances - it lights
    the car's lower body as the web's does and reads as white to the camera.

    shadow   (png path, (w, h) metres, (cx, cy) centre in Blender axes): the
             baked ground shadow (carkit.studio.ground_shadow), multiplied in as
             the web lays it on the floor, so both views have the same shade."""
    ob = bpy.data.objects.get("StudioFloor")
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    me = bpy.data.meshes.new("StudioFloor")
    bm = bmesh.new()
    n = 96
    vs = [bm.verts.new((radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n), 0.0))
          for i in range(n)]
    bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("StudioFloor", me)
    bpy.context.scene.collection.objects.link(ob)

    zones = sorted((p for p in rig["panels"] if p["id"].startswith("floor")), key=lambda p: p["size"][0])
    near, far = zones[0], zones[-1]
    near_r = near["size"][0] / 2.0
    mat = bpy.data.materials.get("M_StudioFloor") or bpy.data.materials.new("M_StudioFloor")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    mp = nt.nodes.new('ShaderNodeMapRange')
    mp.inputs["From Min"].default_value = near_r - 0.5
    mp.inputs["From Max"].default_value = near_r + 0.5
    mp.inputs["To Min"].default_value = near["intensity"] * rig["gain"]
    mp.inputs["To Max"].default_value = far["intensity"] * rig["gain"]
    nt.links.new(ln.outputs["Value"], mp.inputs["Value"])
    nt.links.new(mp.outputs["Result"], em.inputs["Strength"])
    colour = None
    if shadow:
        png, size, centre = shadow
        img = bpy.data.images.load(png, check_existing=True)
        img.colorspace_settings.name = 'sRGB'
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = img
        tex.extension = 'CLIP'
        mpn = nt.nodes.new('ShaderNodeMapping')
        mpn.inputs["Location"].default_value = (0.5 - centre[0] / size[0], 0.5 - centre[1] / size[1], 0.0)
        mpn.inputs["Scale"].default_value = (1.0 / size[0], 1.0 / size[1], 1.0)
        nt.links.new(tc.outputs["Object"], mpn.inputs["Vector"])
        nt.links.new(mpn.outputs["Vector"], tex.inputs["Vector"])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.inputs[6].default_value = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(tex.outputs["Color"], mix.inputs[7])
        nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
        colour = mix.outputs[2]
    if colour is not None:
        nt.links.new(colour, em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    # what the CAMERA sees is the web's flat floor colour, not the radiance the
    # car is lit by (1.75 would clip to pure white and bury the shadow)
    seen = nt.nodes.new('ShaderNodeEmission')
    seen.inputs["Strength"].default_value = srgb_hex(FLOOR_HEX)[0] / VIEWER_EXPOSURE
    if colour is not None:
        nt.links.new(colour, seen.inputs["Color"])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"])
    nt.links.new(em.outputs[0], mx.inputs[1])
    nt.links.new(seen.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    ob.data.materials.append(mat)
    return ob


def drop_lookdev():
    """Remove the old lookdev scene (scene_setup: the L_* softboxes, the dark
    Ground, the camera book, the reflector card): the studio replaces it."""
    for o in list(bpy.data.objects):
        if o.name.startswith(("L_", "CAM_")) or o.name in ("Ground", "REFL_Windscreen"):
            bpy.data.objects.remove(o, do_unlink=True)


def build_studio(rig=None, floor=True, shadow=None):
    """The whole set: the rig's panels, the world, the floor (see studio_floor)."""
    rig = rig or read_rig()
    objs = build_rig(rig)
    studio_world(rig)
    if floor:
        studio_floor(rig, shadow)
    return rig, objs


# ----------------------------------------------------------------- cameras
# anchors.ts SHOTS: azimuth from +x toward the driver's side, elevation, vertical
# field of view, breathing room, and the picture's lift (multiples of the dock)
SHOTS = {
    "hero": dict(az=36, el=11, fov=30, margin=1.3, lift=1.0),
    "doorsL": dict(az=124, el=10, fov=28, margin=1.2, lift=1.0),
    "side": dict(az=90, el=8, fov=20, margin=1.4, lift=1.15),
    "front": dict(az=0, el=9, fov=26, margin=1.85, lift=1.5),
    "rear": dict(az=180, el=9, fov=26, margin=1.85, lift=1.5),
    "rear34": dict(az=-148, el=12, fov=30, margin=1.3, lift=1.0),
    # the car alone, for the infotainment's cards and pages (hmi_art): tight, no dock lift
    "card": dict(az=34, el=7, fov=20, margin=1.04, lift=0.0),
}
REF_ASPECT = 1.78
LIFT_PX = 66
DOCK_PX = 605        # the viewport the dock's 66 px was composed in


def anchor_pose(name, dims, cx=0.0, aspect=REF_ASPECT):
    """anchors.ts resolveAnchor() for an exterior pose: returns (position,
    target, vertical fov in degrees, shift_y) in BLENDER axes. `dims` is the
    car's (length, width, height) in metres, `cx` its centre along x."""
    L, W, H = dims
    s = SHOTS[name]
    az, el = math.radians(s["az"]), math.radians(s["el"])
    across = L * abs(math.sin(az)) + W * abs(math.cos(az))
    depth = L * abs(math.cos(az)) + W * abs(math.sin(az))
    tall = H * math.cos(el) + depth * math.sin(el)
    half = math.tan(math.radians(s["fov"]) / 2.0)
    dist = max(across * s["margin"] / (2 * half * REF_ASPECT), tall * s["margin"] / (2 * half)) + depth * 0.25
    dist *= max(1.0, REF_ASPECT / max(aspect, 0.2))
    target_w = Vector((cx, H * 0.4, 0.0))
    d = Vector((math.cos(az) * math.cos(el), math.sin(el), -math.sin(az) * math.cos(el)))
    pos_w = target_w + d * dist
    shift = (LIFT_PX * s["lift"]) / DOCK_PX / aspect
    return _C @ pos_w, _C @ target_w, s["fov"], shift


def camera_at(name, dims, cx=0.0, aspect=REF_ASPECT):
    """A Blender camera at one of the web's poses."""
    pos, target, fov, shift = anchor_pose(name, dims, cx, aspect)
    cname = "CAM_studio_" + name
    cam = bpy.data.objects.get(cname)
    if cam is None:
        cam = bpy.data.objects.new(cname, bpy.data.cameras.new(cname))
        bpy.context.scene.collection.objects.link(cam)
    d = cam.data
    d.sensor_fit = 'VERTICAL'
    d.sensor_height = 24.0
    d.lens = 12.0 / math.tan(math.radians(fov) / 2.0)
    d.clip_start, d.clip_end = 0.05, 300.0
    d.shift_y = -shift          # the web lifts the picture; a negative shift moves the frame down
    cam.location = pos
    cam.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler()
    return cam


def top_view(path, dims, cx=0.0, res=(700, 1500), samples=192, exposure=VIEWER_EXPOSURE):
    """The car from straight above, nose up the picture, as an orthographic
    cut-out (the 360 camera's top-down car). Cycles with the studio rig."""
    from . import scene as SC
    scn = bpy.context.scene
    cd = bpy.data.cameras.new("CAM_studio_top")
    cd.type = 'ORTHO'
    cd.ortho_scale = dims[0] * 1.06
    cd.clip_start, cd.clip_end = 0.05, 100.0
    cam = bpy.data.objects.new("CAM_studio_top", cd)
    scn.collection.objects.link(cam)
    cam.location = Vector((cx, 0.0, 12.0))
    # image up is the car's +x: turn the downward camera a quarter about z
    cam.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.color_mode = 'RGBA'
    SC.use_cycles(samples)
    SC.colour_management(exposure=math.log2(exposure))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scn.render.filepath = path
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    return path


def still(name, path, dims, cx=0.0, res=(1600, 900), samples=256, exposure=VIEWER_EXPOSURE,
          transparent=False):
    """Render one pose to `path` with the viewer's tone mapping (Khronos PBR
    Neutral at its exposure). Blender's exposure is in stops. `transparent`: a
    cut-out of the car (no floor, no cove) as an RGBA PNG."""
    from . import scene as SC
    scn = bpy.context.scene
    cam = camera_at(name, dims, cx, res[0] / res[1])
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = transparent
    if transparent:
        scn.render.image_settings.color_mode = 'RGBA'
    SC.use_cycles(samples)
    SC.colour_management(exposure=math.log2(exposure))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scn.render.filepath = path
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '8'
    bpy.ops.render.render(write_still=True)
    return path
