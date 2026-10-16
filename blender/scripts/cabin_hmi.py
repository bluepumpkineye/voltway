"""The art the infotainment skins draw from a car's build (public/hmi/<slug>/): the car cut out on a
transparent ground, its top view, and clay drawings of the cabin for the climate and seat pages. Each
function takes the car's cabin_tools config (z9_cabin.CFG) and runs in a background Blender:

    blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); \\
        import z9_cabin as C; C.hmi_art()"
"""
import importlib
import json
import os
import sys

import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
HMI_DIR = os.path.normpath(os.path.join(MODELS, "..", "hmi"))


def hmi_art(cfg, res=(1800, 900), samples=256, az=62.0, el=6.0, fov=20.0):
    """The car as a cut-out for the infotainment's home scene and 360 page (car34.webp, car-top.webp):
    the studio rig on the car alone, a three-quarter view from well round the side, the floor lights
    it but is not drawn, transparent. Fresh build, exterior only. Needs cfg: build_module,
    export_module (its prepare_exterior), dims."""
    from carkit import rig, studio
    B = importlib.import_module(cfg["build_module"])
    X = importlib.import_module(cfg["export_module"])
    B.main(reset=True, scene=False)
    X.prepare_exterior()
    rig.drop_lookdev()
    rig.build_studio()
    bpy.data.objects["StudioFloor"].visible_camera = False
    out_dir = os.path.join(HMI_DIR, cfg["slug"])
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    rig.SHOTS["hmi"] = dict(az=az, el=el, fov=fov, margin=1.04, lift=0.0)
    png = rig.still("hmi", os.path.join(rig.RENDER_DIR, cfg["slug"] + "_card.png"), dims=cfg["dims"],
                    res=res, samples=samples, transparent=True)
    out = os.path.join(out_dir, "car34.webp")
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    top = rig.top_view(os.path.join(rig.RENDER_DIR, cfg["slug"] + "_top.png"), dims=cfg["dims"],
                       samples=samples)
    studio.to_webp(top, os.path.join(out_dir, "car-top.webp"), quality=88, trim=True, width=420)
    return out


def hmi_cabin(cfg, samples=160, shots=("climate", "seats"), tones=("light", "dark"), shot_overrides=None):
    """Clay renders of the cabin for the infotainment's climate and seat pages (cabin-<shot>-
    <light|dark>.webp): every surface one matte colour under a uniform white sky, the centre screen
    black, on a transparent ground, so the picture is all form. Cabin only, no exterior. Needs cfg:
    interior, collection, hmi_parts, hmi_shots (name -> dict(pos, aim, lens, res, hide)),
    hmi_seat_points. Prints HMI_SEATS {shot: {seat: [x, y]}}: where each seat's button goes, as
    fractions of the picture."""
    from bpy_extras.object_utils import world_to_camera_view
    from carkit import rig, scene as SC, studio
    bpy.ops.wm.read_homefile(use_empty=True)
    SH = importlib.import_module(cfg["interior"])
    SH.main(lights=False, parts=list(cfg["hmi_parts"]))
    scn = bpy.context.scene
    objs = [o for o in bpy.data.collections[cfg["collection"]].all_objects if o.type == 'MESH']

    def flat(name, rgb, rough=0.9):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = rgb + (1.0,)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = 0.0
        return m, b

    clay, clay_bsdf = flat("M_Clay", (0.8, 0.8, 0.8))
    black, _ = flat("M_ScreenBlack", (0.004, 0.004, 0.005), 0.25)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(black if o.name.startswith("screen_") else clay)
    w = bpy.data.worlds.new("W_Clay")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    out_dir = os.path.join(HMI_DIR, cfg["slug"])
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    out, seats = [], {}
    for name in shots:
        shot = dict(cfg["hmi_shots"][name], **(shot_overrides or {}).get(name, {}))
        for o in objs:
            n = o.name.lower()
            hidden = any(k in n for k in shot["hide"])
            # anything wholly above the seats: the header trims, the visors, the mirror
            if not hidden and name == "climate":
                hidden = min((o.matrix_world @ Vector(c)).z for c in o.bound_box) > shot.get("above", 1.22)
            o.hide_render = hidden
        cd = bpy.data.cameras.new("CAM_" + name)
        cd.lens = shot["lens"]
        cd.clip_start = 0.02
        cam = bpy.data.objects.new("CAM_" + name, cd)
        scn.collection.objects.link(cam)
        cam.location = Vector(shot["pos"])
        cam.rotation_euler = (Vector(shot["aim"]) - Vector(shot["pos"])).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = shot["res"]
        scn.render.resolution_percentage = 100
        bpy.context.view_layer.update()
        if name == "seats":
            seats[name] = {}
            for k, pt in cfg["hmi_seat_points"].items():
                c = world_to_camera_view(scn, cam, Vector(pt))
                seats[name][k] = [round(c.x, 4), round(1.0 - c.y, 4)]
        for tone, albedo, sky in (("light", 0.80, 1.05), ("dark", 0.040, 2.4)):
            if tone not in tones:
                continue
            clay_bsdf.inputs["Base Color"].default_value = (albedo, albedo, albedo * 1.02, 1.0)
            bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            bg.inputs["Strength"].default_value = sky
            SC.use_cycles(samples)
            scn.view_settings.view_transform = 'Standard'
            # the sky lights the cabin but is not in the picture: the page behind it shows
            scn.render.film_transparent = True
            scn.render.image_settings.file_format = 'PNG'
            scn.render.image_settings.color_mode = 'RGBA'
            png = os.path.join(rig.RENDER_DIR, "%s_cabin_%s_%s.png" % (cfg["slug"], name, tone))
            scn.render.filepath = png
            bpy.ops.render.render(write_still=True)
            webp = os.path.join(out_dir, "cabin-%s-%s.webp" % (name, tone))
            studio.to_webp(png, webp, quality=80, width=shot["res"][0])
            out.append(webp)
        bpy.data.objects.remove(cam, do_unlink=True)
    print("HMI_SEATS", json.dumps(seats))
    return out
