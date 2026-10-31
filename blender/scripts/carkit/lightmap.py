"""A cabin's diffuse light as one texture: the step past the occlusion atlas (2026-10-31, the Rivian benchmark).

The hall look (aoatlas) lights a cabin with an environment map and darkens it with ambient occlusion: every surface sees
the same hall, a seat is as bright as the dash top, and a footwell is only "a bit occluded". Rivian's configurator
stills (offline Unreal renders) owe most of their finish to real light: the cabin is bright where the glass lets the
studio in, dark under the dash and in the footwells, and light bounces from the white seats onto the trim beside them.
This module bakes that light, irradiance only (no albedo, so a trim swap still recolours the materials), on the same
second UV set the occlusion atlas uses:

    img, scale = lightmap.bake(objs, path, world=..., hide=())     # after aoatlas.unwrap(objs)

The exterior stays in the scene so the body shades the cabin and the light comes in through the windows; the glazing is
made thin for the pass (carkit.bake.thin_glass), or Cycles lets no daylight through it. The result is stored as an
8-bit sRGB image of irradiance / scale; the viewer reads it as the material's lightMap on TEXCOORD_1 with intensity
`scale` (vehicle data: assets.interiorLightMap {url, intensity}).
"""
import bpy
import numpy as np

from .aoatlas import UV_NAME, _bake_targets, _dilate

IMAGE = "Cabin_Light"


def bake(objs, path, size=2048, samples=384, hide=(), margin=8, name=UV_NAME, dilate=24, pct=99.5, blur=1):
    """Cycles diffuse light (direct + indirect, no colour) of `objs` into a size x size image saved to `path`.

    Returns (image, scale): the stored value is (irradiance / scale) ** (1 / 2.2), scale = the `pct` percentile of the
    covered texels, so the brightest few texels clip and the rest keep their range in 8 bits."""
    from . import scene as SC
    from . import bake as BK
    scn = bpy.context.scene
    SC.use_cycles(samples=samples, denoise=False)
    scn.cycles.samples = samples
    img = bpy.data.images.get(IMAGE)
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(IMAGE, size, size, alpha=True, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    img.generated_color = (0.0, 0.0, 0.0, 0.0)
    hidden = []
    for o in hide:
        if not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    targets = _bake_targets(objs, img)
    bk = scn.render.bake
    try:
        bk.use_pass_direct = True
        bk.use_pass_indirect = True
        bk.use_pass_color = False
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for o in objs:
            o.hide_set(False)
            o.select_set(True)
            o.data.uv_layers.active = o.data.uv_layers[name]
        active = objs[0]
        bpy.context.view_layer.objects.active = active
        with BK.thin_glass():
            with bpy.context.temp_override(active_object=active, object=active, selected_objects=objs,
                                           selected_editable_objects=objs):
                bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, target='IMAGE_TEXTURES',
                                    margin=margin, margin_type='EXTEND', use_clear=True)
    finally:
        for nt, n in targets:
            nt.nodes.remove(n)
        for o in hidden:
            o.hide_render = False
    px = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(size, size, 4)
    rgb = px[..., :3].copy()
    cov = px[..., 3] > 0.5
    if cov.all() or not cov.any():
        cov = rgb.mean(axis=2) > 1e-5
    # a light 3x3 blur inside the covered texels: Monte Carlo grain at 384 samples, not detail
    for _ in range(blur):
        acc = np.zeros_like(rgb)
        wsum = np.zeros(cov.shape, np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                c = np.roll(np.roll(cov, dy, 0), dx, 1).astype(np.float32)
                acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * c[..., None]
                wsum += c
        rgb = np.where(cov[..., None], acc / np.maximum(wsum, 1.0)[..., None], rgb)
    lum = rgb.mean(axis=2)
    scale = float(np.percentile(lum[cov], pct)) if cov.any() else 1.0
    scale = max(scale, 1e-4)
    out = np.empty_like(rgb)
    for c in range(3):
        ch, grown = _dilate(rgb[..., c], cov, dilate)
        out[..., c] = np.where(grown, ch, np.median(lum[cov]))
    enc = np.clip(out / scale, 0.0, 1.0) ** (1.0 / 2.2)
    img8 = bpy.data.images.get(IMAGE + "_8") or bpy.data.images.new(IMAGE + "_8", size, size, alpha=False)
    img8.colorspace_settings.name = 'Non-Color'
    pix = np.ones((size, size, 4), np.float32)
    pix[..., :3] = enc
    img8.pixels.foreach_set(pix.ravel())
    img8.filepath_raw = path
    img8.file_format = 'WEBP' if path.lower().endswith(".webp") else 'PNG'
    img8.save()
    print("lightmap: baked %dx%d, covered %.0f%%, scale %.4f, p5 %.4f p50 %.4f" % (
        size, size, 100.0 * cov.mean(), scale, float(np.percentile(lum[cov], 5)), float(np.percentile(lum[cov], 50))))
    return img8, scale
