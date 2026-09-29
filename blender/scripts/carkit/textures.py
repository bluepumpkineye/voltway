"""Procedural maps baked to real image datablocks.

A Checker or Noise node wired into Base Color looks right in Blender and then
vanishes on glTF export - the exporter cannot evaluate procedural nodes, so
the socket falls back to its default and carbon fibre ships as 0.8 grey
plastic. These build the maps as actual pixels and save them next to the
.blend, so what the browser gets is what the render showed.
"""
import math
import os

import bpy

TEX_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "textures"))


def _save(img, filename):
    os.makedirs(TEX_DIR, exist_ok=True)
    path = os.path.join(TEX_DIR, filename)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return path


def carbon_weave(size=512, twill=2, weave_px=32):
    """2x2 twill carbon: base colour plus a matching normal map.

    One weave cell is `weave_px` pixels; with world-space UVs (build.ensure_uvs)
    and uv_scale 21, a tow comes out at about 3 mm - real 3k twill.
    """
    name_c, name_n = "T_Carbon_BaseColor", "T_Carbon_Normal"
    for n in (name_c, name_n):
        old = bpy.data.images.get(n)
        if old:
            bpy.data.images.remove(old)

    col = bpy.data.images.new(name_c, size, size, alpha=False)
    nrm = bpy.data.images.new(name_n, size, size, alpha=False, is_data=True)

    cpix = [0.0] * (size * size * 4)
    npix = [0.0] * (size * size * 4)

    for y in range(size):
        for x in range(size):
            cx, cy = x // weave_px, y // weave_px
            # 2x2 twill: the over/under pattern steps one cell per row
            over = ((cx + cy) // twill) % 2 == 0
            fx = (x % weave_px) / float(weave_px)
            fy = (y % weave_px) / float(weave_px)
            t = fx if over else fy
            bulge = math.sin(math.pi * t)

            base = 0.016 + 0.052 * (bulge ** 2)
            if not over:
                base *= 0.72
            i = (y * size + x) * 4
            cpix[i] = base
            cpix[i + 1] = base
            cpix[i + 2] = base * 1.04      # a faint cool cast, as woven tow has
            cpix[i + 3] = 1.0

            slope = math.cos(math.pi * t) * 0.55
            nx = slope if over else 0.0
            ny = 0.0 if over else slope
            npix[i] = nx * 0.5 + 0.5
            npix[i + 1] = ny * 0.5 + 0.5
            npix[i + 2] = 1.0
            npix[i + 3] = 1.0

    col.pixels.foreach_set(cpix)
    nrm.pixels.foreach_set(npix)
    col.update()
    nrm.update()
    _save(col, "carbon_basecolor.png")
    _save(nrm, "carbon_normal.png")
    return col, nrm


def apply_carbon(mat, uv_scale=20.0):
    """Wire the baked weave into a material so it survives glTF export."""
    col, nrm = carbon_weave()
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    for n in list(nt.nodes):
        if n.type in ('TEX_CHECKER', 'TEX_NOISE', 'BUMP', 'TEX_IMAGE',
                      'MAPPING', 'TEX_COORD'):
            nt.nodes.remove(n)

    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])

    tex_c = nt.nodes.new('ShaderNodeTexImage')
    tex_c.image = col
    nt.links.new(mapping.outputs["Vector"], tex_c.inputs["Vector"])
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])

    tex_n = nt.nodes.new('ShaderNodeTexImage')
    tex_n.image = nrm
    tex_n.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(mapping.outputs["Vector"], tex_n.inputs["Vector"])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nmap.inputs["Strength"].default_value = 0.85
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat
