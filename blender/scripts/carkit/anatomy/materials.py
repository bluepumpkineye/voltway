"""The anatomy's material library. Every name starts with XR_ so the web viewer can find them
(blueprint mode and the clips tint materials by name). Colours are sRGB hex.

Most materials are textured: a family of procedural maps from `texgen` (albedo, tangent-space normal, and an
occlusion-roughness-metal image in glTF's layout), a tint multiplied into the albedo, and a tile size in metres (the
builders' UVs are metres of surface, `solid()` divides them by `xr_tile`). A material with `tint=None` takes its colour
from the texture alone (the printed cell wrap, the circuit boards, the label atlas). Plain materials (the magnets, the
coolant) are single colours.

Set XR_TEX_SCALE (0.25 .. 1) in the environment for quicker, smaller textures while iterating.
"""
import os

import bpy
import numpy as np

from . import texgen
from .prim import mat, rgb

_SETS = {}
# families whose albedo is flat (the tint carries the colour): their image is not made or shipped
PLAIN_COLOUR = {"cast", "machined", "forged", "steel", "rubber", "plastic"}


def _scale():
    try:
        return max(0.125, min(1.0, float(os.environ.get("XR_TEX_SCALE", "1"))))
    except ValueError:
        return 1.0


def _image(name, arr, data):
    n = arr.shape[0]
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name + "_gen", n, n, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'      # BEFORE the pixels: changing it afterwards resets the buffer
    px = np.ones((n, n, 4), np.float32)
    px[..., :3] = np.clip(arr, 0.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    # the glTF exporter reads file-backed images (a generated image comes out blank): write a PNG and load it back
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "xr_tex")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name + ".png")
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.name = name
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    return img


def tex_set(fam):
    """The three images of a texture family (made once per session)."""
    s = _SETS.get(fam)
    if s is None or any(i is not None and i.name not in bpy.data.images for i in s):
        fn = texgen.FAMILIES[fam]
        import inspect
        default = inspect.signature(fn).parameters["n"].default
        n = max(64, int(default * _scale()))
        alb, nrm, orm = fn(n)
        a_img = None if fam in PLAIN_COLOUR else _image("XRT_%s_albedo" % fam, alb, False)
        s = (a_img, _image("XRT_%s_normal" % fam, nrm, True), _image("XRT_%s_orm" % fam, orm, True))
        _SETS[fam] = s
    return s


def tmat(name, tint, fam, tile, normal=1.0):
    """A textured Principled material the glTF exporter understands: base colour (albedo x tint), normal map, and roughness/metal
    from one ORM image."""
    m = bpy.data.materials.get(name)
    if m is not None:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    alb, nrm, orm = tex_set(fam)

    def tex(img, data, x, y):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        n.interpolation = 'Linear'
        n.extension = 'REPEAT'
        n.location = (x, y)
        return n
    if fam in PLAIN_COLOUR and tint is not None:
        # near-uniform albedo: no image (it only costs file size), the tint is the colour
        b.inputs['Base Color'].default_value = (*rgb(tint), 1.0)
    elif tint is None:
        ta = tex(alb, False, -700, 300)
        nt.links.new(ta.outputs['Color'], b.inputs['Base Color'])
    else:
        ta = tex(alb, False, -700, 300)
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*rgb(tint), 1.0)
        nt.links.new(ta.outputs['Color'], mix.inputs[6])
        nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    tn = tex(nrm, True, -700, 0)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.space = 'TANGENT'
    nm.inputs['Strength'].default_value = normal
    nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    to = tex(orm, True, -700, -300)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(to.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], b.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
    m["xr_tile"] = float(tile)
    m["xr_family"] = fam
    return m


def library():
    L = {}

    def m(name, col, metal=0.0, rough=0.5, **kw):
        L[name] = mat(name, col, metal, rough, **kw)

    def t(name, tint, fam, tile, normal=1.0):
        L[name] = tmat(name, tint, fam, tile, normal)

    # cast and machined aluminium, steel
    t("XR_Casing", "#7a7e84", "cast", 0.50)               # drive-unit casings (dark cast aluminium)
    t("XR_Sheet", "#83878d", "machined", 0.40)            # the pack's tray and lid (satin sheet aluminium)
    t("XR_Alu_Cast", "#a6aab1", "cast", 0.50)             # castings: subframes, reducer
    t("XR_Alu_Machined", "#d3d6db", "machined", 0.25)     # machined faces, fins, end plates
    t("XR_Steel", "#898d93", "steel", 0.30)               # fasteners, tubes
    t("XR_Bolt", "#aaaeb4", "steel", 0.06)
    t("XR_Shaft", "#c5c9ce", "machined", 0.12)
    t("XR_Arm", "#9ca0a7", "forged", 0.50)                # forged aluminium links
    t("XR_Knuckle", "#898d94", "cast", 0.50)              # cast knuckles
    t("XR_Spring_Can", "#60646a", "cast", 0.50)           # air-spring canisters
    t("XR_Damper", "#e2b13a", "machined", 0.16)           # damper bodies (gold anodised)
    t("XR_Brass", "#d8b25a", "machined", 0.10)            # terminals
    # electrical steel, copper
    t("XR_Lamination", "#a9adb3", "lam", 0.08)            # electrical-steel stacks
    t("XR_Copper", "#f08c3c", "copper", 0.06)             # windings, busbars
    t("XR_Copper_U", "#f08c3c", "copper", 0.06)           # the three phases of the stator winding: one copper, three materials
    t("XR_Copper_V", "#f08c3c", "copper", 0.06)
    t("XR_Copper_W", "#f08c3c", "copper", 0.06)
    m("XR_Magnet_N", "#d8bdb6", 1.0, 0.24)                # permanent magnets, one pole ...
    m("XR_Magnet_S", "#b4c4d9", 1.0, 0.24)                # ... and the other
    # the pack
    t("XR_Cell", None, "cellfilm", 0.30)                  # cell wrap (printed)
    t("XR_Cell_Top", "#c8cfd8", "machined", 0.12)         # cell lids and terminals
    t("XR_Insulator", None, "insulator", 0.30)            # pack insulation film
    # plastics, rubber, cable
    t("XR_Plastic_Black", "#2a2d33", "plastic", 0.05)
    t("XR_HV_Orange", "#ff7a24", "hvsheath", 0.06)        # high-voltage cable and connectors
    t("XR_Coolant", "#3aa0f0", "plastic", 0.05)           # coolant fittings
    t("XR_Rubber", "#303238", "rubber", 0.05)             # boots, bushings, air-spring bellows
    # boards, labels
    t("XR_PCB", None, "pcb", 0.08)
    t("XR_FPC", None, "fpc", 0.08)
    t("XR_Label", None, "labels", 1.0)
    t("XR_Hazard", None, "hazard", 0.08)
    return L
