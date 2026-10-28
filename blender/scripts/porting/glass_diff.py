"""Where do the model's windows and blacked-out parts sit against the photograph's?

Renders the built car through a matched camera (carkit.qa.refmatch) with every object painted by class
(Object Info colour into an emission shader, so paint still hides what is behind it) and draws the outlines
over the reference photograph:

    magenta line   outline of the model's WINDOWS (A06T_Glass_* except the roof glass)
    green line     outline of the model's black glass (roof glass, frit, rear roof / greenhouse black)
    cyan line      outline of the rails, mirrors and roof blade, with --black

A studio photograph shows the bright studio through its windows, so the photograph's own dark regions are
no use: compare the lines with the window frames and trim edges visible in the photo.

    blender -b --factory-startup --python blender/scripts/porting/glass_diff.py -- a06t side 1700 1180 1800 560
    blender -b --factory-startup --python blender/scripts/porting/glass_diff.py -- a06t rear 900 1000 2000 900

Arguments: car, camera name (as registered in <car>_ref_match), crop u0 v0 w h (photo px), optional
--open <blend> (a built scene saved earlier; builds the car if omitted), --out <png>, --scale <k>,
--black. Needs build_<car>.main. Output: blender/renders/match/<cam>_glassdiff.png
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.normpath(os.path.join(HERE, "..")))
import bpy
import numpy as np

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CAR, CAMNAME = ARGS[0], ARGS[1]
U0, V0, CW, CH = (int(a) for a in ARGS[2:6])


def _opt(name, default, cast=str):
    return cast(ARGS[ARGS.index(name) + 1]) if name in ARGS else default


SCALE = _opt("--scale", 1.0, float)
OPEN = _opt("--open", None)
OUT = _opt("--out", None)
BLACK = "--black" in ARGS

BLACKGLASS = ("Glass_Roof", "Frit", "Roof_Rear_Black", "Greenhouse_Black")
TRIM = ("RoofRail", "Roof_Rail", "Mirror", "Roof_Blade")


def classify(name):
    """0 paint/other, 1 window, 2 black glass, 3 trim"""
    if any(k in name for k in BLACKGLASS):
        return 2
    if "Glass_" in name:
        return 1
    if any(k in name for k in TRIM):
        return 3
    return 0


def render_classes(R, name):
    """[h, w] int map of classify() per pixel (-1 where nothing), paint occluding what it covers"""
    scn = bpy.context.scene
    ref, (w, h), *_ = R.CAMERAS[name]
    cam = R.camera(name)
    mat = bpy.data.materials.new("class_flat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(oi.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    palette = {0: (0.0, 0.0, 0.0, 1.0), 1: (1.0, 0.0, 0.0, 1.0), 2: (0.0, 1.0, 0.0, 1.0), 3: (0.0, 0.0, 1.0, 1.0)}
    hidden = []
    for o in scn.objects:
        if o.type != 'MESH':
            continue
        if o.hide_render or o.name == "Ground" or o.name.startswith("REFL"):
            continue
        if o.name.startswith("A06T_Shell_Shadow") or o.name.startswith("A06T_Liner") or o.name == "A06T_Underbody":
            o.hide_render = True
            hidden.append(o)
            continue
        o.color = palette[classify(o.name)]
    old = (scn.camera, scn.render.film_transparent, scn.render.resolution_x, scn.render.resolution_y,
           scn.view_layers[0].material_override, scn.cycles.samples, scn.cycles.use_denoising,
           scn.cycles.pixel_filter_type, scn.render.image_settings.color_mode)
    try:
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = w, h
        scn.render.resolution_percentage = 100
        scn.render.film_transparent = True
        scn.render.image_settings.file_format = 'PNG'
        scn.render.image_settings.color_mode = 'RGBA'
        scn.render.image_settings.color_management = 'OVERRIDE'
        scn.render.image_settings.view_settings.view_transform = 'Standard'
        scn.view_layers[0].material_override = mat
        scn.cycles.samples = 1
        scn.cycles.use_denoising = False
        scn.cycles.pixel_filter_type = 'BOX'
        path = os.path.join(R.OUT_DIR, "%s_class_tmp.png" % name)
        scn.render.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        (scn.camera, scn.render.film_transparent, scn.render.resolution_x, scn.render.resolution_y,
         scn.view_layers[0].material_override, scn.cycles.samples, scn.cycles.use_denoising,
         scn.cycles.pixel_filter_type, scn.render.image_settings.color_mode) = old
        for o in hidden:
            o.hide_render = False
    img = R.load(path)
    cls = np.full(img.shape[:2], -1, np.int8)
    a = img[..., 3] > 0.5
    r, g, b = img[..., 0] > 0.5, img[..., 1] > 0.5, img[..., 2] > 0.5
    cls[a] = 0
    cls[a & r & ~g & ~b] = 1
    cls[a & g & ~r & ~b] = 2
    cls[a & b & ~r & ~g] = 3
    return cls


def outline(m, width=2):
    e = np.zeros(m.shape, bool)
    e[:, 1:] |= m[:, 1:] != m[:, :-1]
    e[1:] |= m[1:] != m[:-1]
    for _ in range(width - 1):
        e2 = e.copy()
        e2[:, 1:] |= e[:, :-1]
        e2[1:] |= e[:-1]
        e = e2
    return e


def main():
    if OPEN:
        bpy.ops.wm.open_mainfile(filepath=OPEN)
    else:
        importlib.import_module("build_" + CAR).main(scene=False)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    importlib.import_module(CAR + "_ref_match")
    from carkit.qa import refmatch as R
    import photo_tools as PT
    photo = PT.load(R.CAMERAS[CAMNAME][0])
    cls = render_classes(R, CAMNAME)
    sl = (slice(V0, V0 + CH), slice(U0, U0 + CW))
    img = photo[sl].copy()
    c = cls[sl]
    img[outline(c == 1)] = (1.0, 0.0, 1.0)
    img[outline(c == 2)] = (0.0, 0.85, 0.0)
    if BLACK:
        img[outline(c == 3)] = (0.0, 1.0, 1.0)
    if SCALE != 1.0:
        img = PT._resize(img, SCALE)
    path = OUT or os.path.join(R.OUT_DIR, "%s_glassdiff.png" % CAMNAME)
    PT.save(img, path)
    np.save(os.path.join(R.OUT_DIR, "%s_classes.npy" % CAMNAME), cls)
    print("GLASSDIFF", path, "windows %d px, black glass %d px" % (int((c == 1).sum()), int((c == 2).sum())))


main()
