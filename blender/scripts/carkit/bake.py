"""Carry Cycles' lighting into the real-time viewer.

three.js has no global illumination. Inside a cabin its image-based light
reaches every surface as if roof, doors and seats were not there: footwells
light up like the dash top, and every glossy trim reflects the studio
environment instead of the cabin. Two bakes fix that:

    vertex_lighting(objects)   Cycles' DIFFUSE lighting (direct + indirect,
                               no colour: the light a surface receives, as in
                               the render) into a float colour attribute per
                               vertex. Exported as COLOR_0; the viewer uses it
                               in place of image-based diffuse light
                               (CarModel.tsx, bakedLighting()).
    probe(location, path)      an equirectangular HDR panorama from inside the
                               cabin - what the trim should reflect. The
                               viewer loads it as the interior materials'
                               envMap.

Vertex baking needs final topology (modifiers applied) and enough vertices:
sweeps and grids at 1-3 cm spacing carry soft shadows well; a big flat box
face just interpolates its corners.

    objs = prepare(collection)            # apply modifiers, add the attribute
    stats = vertex_lighting(objs)         # ~1 min for 150k tris at 256 spp
    probe((-0.35, 0, 1.10), "cabin_probe.hdr")
"""
import contextlib
import os

import bpy
import numpy as np

ATTR = "BakedLight"
# What ships: a generic float3 attribute. Blender 5.2's glTF exporter writes
# a colour attribute correctly for the FIRST material's primitive only and
# fills every other primitive's COLOR_0 with white (seen as a flat, bright
# cabin in the viewer); custom "_" attributes export per primitive intact.
# GLTFLoader names it "_bakedlight".
EXPORT_ATTR = "_BAKEDLIGHT"
# stored = lighting * STORE_SCALE; the viewer multiplies back
# (uBakeGain = pi / STORE_SCALE)
STORE_SCALE = 0.25


def prepare(collection, skip=()):
    """Apply modifiers on the collection's meshes and give each a float
    colour attribute to bake into. Returns the meshes."""
    from .export import bake_modifiers
    objs = [o for o in collection.all_objects if o.type == 'MESH'
            and not any(s in o.name for s in skip)]
    for o in objs:
        bake_modifiers(o)
        me = o.data
        ca = me.color_attributes.get(ATTR) or me.color_attributes.new(ATTR, 'FLOAT_COLOR', 'POINT')
        me.color_attributes.active_color = ca
        me.color_attributes.render_color_index = me.color_attributes.active_color_index
    return objs


@contextlib.contextmanager
def bake_overrides(materials):
    """Material tweaks for the duration of the bake.

    Normal maps off: a vertex samples ONE texel of the grain, so a mapped
    normal turns into per-vertex speckle. Metallic to 0: a metal has no
    diffuse closure, so Cycles reports no diffuse light on it at all and the
    viewer's chrome and brushed trim came out black."""
    saved = []
    for m in materials:
        if not (m and m.use_nodes):
            continue
        for n in m.node_tree.nodes:
            if n.type == 'NORMAL_MAP':
                saved.append((n.inputs["Strength"], n.inputs["Strength"].default_value))
                n.inputs["Strength"].default_value = 0.0
            elif n.type == 'BSDF_PRINCIPLED' and not n.inputs["Metallic"].is_linked:
                saved.append((n.inputs["Metallic"], n.inputs["Metallic"].default_value))
                n.inputs["Metallic"].default_value = 0.0
    try:
        yield
    finally:
        for sock, v in saved:
            sock.default_value = v


# Light transmission per glazing material for the cabin passes. The modelled
# tints are near-black, since from outside the glass has to read deep, and
# Principled glass tints what it transmits by its base colour. Real glazing:
# windscreen and front door glass at least 70 % (GB 7258), privacy glass on
# the rear doors, quarters and backlight about 25 %.
GLASS_VLT = {"M_Glass": (0.80, 0.84, 0.80), "M_Glass_Privacy": (0.24, 0.26, 0.24)}


@contextlib.contextmanager
def thin_glass(tints=None):
    """The glazing as thin panes for the duration of a lighting pass: Fresnel
    reflection over straight-through tinted transmission.

    As built, the glass let no daylight into the cabin. The sheets are
    single-sided with refractive Principled glass, and Cycles treats
    refraction as opaque to shadow rays; with refractive caustics off, a
    diffuse path through the glass is dropped too. A Transparent BSDF passes
    both. Without this the cabin is lit only by lights placed inside it."""
    tints = GLASS_VLT if tints is None else tints
    saved = []
    for name, tint in tints.items():
        m = bpy.data.materials.get(name)
        if not (m and m.use_nodes):
            continue
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
        if out is None:
            continue
        surf = out.inputs["Surface"]
        src = surf.links[0].from_socket if surf.is_linked else None
        b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        rough = b.inputs["Roughness"].default_value if b else 0.03
        ior = b.inputs["IOR"].default_value if b else 1.52
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        tr.inputs["Color"].default_value = tuple(tint) + (1.0,)
        try:
            gl = nt.nodes.new('ShaderNodeBsdfGlossy')
        except RuntimeError:
            gl = nt.nodes.new('ShaderNodeBsdfAnisotropic')
        gl.inputs["Roughness"].default_value = rough
        # A pane reflects alike from both sides, but the Fresnel node inverts
        # the IOR on a back face (light leaving glass): from inside, the
        # windscreen went totally reflective past 41 degrees and mirrored the
        # dash where the road should be. Feed 1/IOR on back faces to cancel it.
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        eta = nt.nodes.new('ShaderNodeMath')
        eta.operation = 'MULTIPLY_ADD'
        eta.inputs[1].default_value = 1.0 / ior - ior
        eta.inputs[2].default_value = ior
        nt.links.new(geo.outputs["Backfacing"], eta.inputs[0])
        fr = nt.nodes.new('ShaderNodeFresnel')
        nt.links.new(eta.outputs["Value"], fr.inputs["IOR"])
        mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(fr.outputs["Fac"], mx.inputs[0])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[1])
        nt.links.new(gl.outputs["BSDF"], mx.inputs[2])
        nt.links.new(mx.outputs["Shader"], surf)
        saved.append((nt, surf, src, (tr, gl, geo, eta, fr, mx)))
    try:
        yield
    finally:
        for nt, surf, src, nodes in saved:
            if src is not None:
                nt.links.new(src, surf)
            for n in nodes:
                nt.nodes.remove(n)


def to_generic(objects):
    """Copy the baked colour attribute into the float3 EXPORT_ATTR."""
    for o in objects:
        me = o.data
        ca = me.color_attributes.get(ATTR)
        if ca is None:
            continue
        c = np.empty(len(ca.data) * 4, np.float32)
        ca.data.foreach_get("color", c)
        at = me.attributes.get(EXPORT_ATTR) or me.attributes.new(EXPORT_ATTR, 'FLOAT_VECTOR',
                                                                 'POINT')
        at.data.foreach_set("vector", c.reshape(-1, 4)[:, :3].ravel())


def vertex_lighting(objects, samples=256, scale=STORE_SCALE):
    """Bake the diffuse lighting into ATTR on every object. Returns stats."""
    scn = bpy.context.scene
    try:
        scn.render.engine = 'CYCLES'
    except TypeError:
        pass
    scn.cycles.samples = samples
    scn.render.bake.target = 'VERTEX_COLORS'
    scn.render.bake.use_clear = True
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objects:
        o.hide_set(False)
        o.select_set(True)
    active = objects[0]
    bpy.context.view_layer.objects.active = active
    mats = {s.material for o in objects for s in o.material_slots if s.material}
    with bake_overrides(mats):
        with bpy.context.temp_override(active_object=active, object=active,
                                       selected_objects=objects,
                                       selected_editable_objects=objects):
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'},
                                target='VERTEX_COLORS', use_clear=True)
    lo, hi, total = 1e9, 0.0, []
    for o in objects:
        ca = o.data.color_attributes[ATTR]
        a = np.empty(len(ca.data) * 4, np.float32)
        ca.data.foreach_get("color", a)
        a = a.reshape(-1, 4)
        a[:, :3] *= scale
        a[:, 3] = 1.0
        ca.data.foreach_set("color", a.ravel())
        lum = a[:, :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        total.append(lum)
        lo, hi = min(lo, float(lum.min())), max(hi, float(lum.max()))
    allv = np.concatenate(total)
    stats = {"objects": len(objects), "verts": int(allv.size), "min": lo, "max": hi,
             "p50": float(np.percentile(allv, 50)), "p99": float(np.percentile(allv, 99)),
             "clipped": int((allv > 1.0).sum()), "scale": scale}
    print("vertex lighting:", stats)
    return stats


def smooth(objects, iterations=2, keep=0.5):
    """Average each vertex's baked light with its edge neighbours.

    Every vertex is an independent Monte Carlo estimate, so a vertex bake
    carries per-vertex speckle (~1/sqrt(samples)); two passes of
    neighbour averaging remove it without blurring shadows wider than a
    couple of vertices."""
    for o in objects:
        me = o.data
        ca = me.color_attributes.get(ATTR)
        if ca is None or ca.domain != 'POINT' or len(me.edges) == 0:
            continue
        n = len(me.vertices)
        col = np.empty(n * 4, np.float32)
        ca.data.foreach_get("color", col)
        col = col.reshape(-1, 4)
        e = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", e)
        e = e.reshape(-1, 2)
        deg = np.bincount(e.ravel(), minlength=n).astype(np.float32)
        for _ in range(iterations):
            acc = np.zeros((n, 3), np.float32)
            np.add.at(acc, e[:, 0], col[e[:, 1], :3])
            np.add.at(acc, e[:, 1], col[e[:, 0], :3])
            nb = acc / np.maximum(deg, 1.0)[:, None]
            has = deg > 0
            col[has, :3] = keep * col[has, :3] + (1.0 - keep) * nb[has]
        ca.data.foreach_set("color", col.ravel())


def probe_mix(location, path, lights, mix=0.3, **kw):
    """A probe with the rig's lights at `mix` of their real brightness.

    One probe serves every surface, so a softbox 20 cm above it covers half
    the sky: at full strength the pedals, console carbon and mirror all
    mirrored it white; with no lights at all the leather and wheel lost every
    highlight. Renders the cabin with the lights camera-visible and without,
    and blends: probe = without + mix * (with - without).

    The lookdev softboxes outside the car stay out of it too: shown at full
    strength they mirrored white in the SU7's console carbon, and did not
    lift the leather that lacked sheen (that is the probe's parallax - one
    point between the seats sees the wrong part of the cabin from the far
    side of the dash)."""
    base, ext = os.path.splitext(path)
    a = probe(location, base + "_dark" + ext, **kw)
    b = probe(location, base + "_lit" + ext, show_lights=lights, **kw)
    ia = bpy.data.images.load(a, check_existing=False)
    ib = bpy.data.images.load(b, check_existing=False)
    w, h = ia.size
    pa = np.empty(w * h * 4, np.float32)
    pb = np.empty(w * h * 4, np.float32)
    ia.pixels.foreach_get(pa)
    ib.pixels.foreach_get(pb)
    out = pa + mix * (pb - pa)
    write_hdr(path, out.reshape(h, w, 4)[::-1, :, :3])
    for i in (ia, ib):
        bpy.data.images.remove(i)
    for p in (a, b):
        os.remove(p)
    return path


def probe(location, path, res=(1024, 512), samples=256, show_lights=(), hide=()):
    """Render an equirectangular HDR panorama at `location`.

    show_lights: light objects to make camera-visible for the shot (lights
    kept out of the camera in renders still belong in reflections);
    hide: objects to hide from the render."""
    scn = bpy.context.scene
    cam_data = bpy.data.cameras.get("CAM_probe") or bpy.data.cameras.new("CAM_probe")
    cam_data.type = 'PANO'
    try:
        cam_data.panorama_type = 'EQUIRECTANGULAR'
    except (AttributeError, TypeError):
        cam_data.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam = bpy.data.objects.get("CAM_probe") or bpy.data.objects.new("CAM_probe", cam_data)
    if cam.name not in scn.collection.objects:
        scn.collection.objects.link(cam)
    cam.location = location
    # equirect camera looking down +X with Z up: rotate so the image's centre
    # is +X (forward) and its top is +Z
    cam.rotation_euler = (1.5707963, 0.0, -1.5707963)
    saved = []
    for o in show_lights:
        saved.append((o, "visible_camera", o.visible_camera))
        o.visible_camera = True
    for o in hide:
        saved.append((o, "hide_render", o.hide_render))
        o.hide_render = True
    prev = (scn.camera, scn.render.resolution_x, scn.render.resolution_y,
            scn.render.resolution_percentage, scn.render.image_settings.file_format,
            scn.render.filepath, scn.view_settings.view_transform)
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.resolution_percentage = 100
    scn.cycles.samples = samples
    # the viewer tone-maps, so the probe must be scene-linear
    scn.view_settings.view_transform = 'Standard'
    scn.render.image_settings.file_format = 'HDR'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scn.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for o, attr, v in saved:
            setattr(o, attr, v)
        (scn.camera, scn.render.resolution_x, scn.render.resolution_y,
         scn.render.resolution_percentage, scn.render.image_settings.file_format,
         scn.render.filepath, scn.view_settings.view_transform) = prev
    return path


# ---------------------------------------------------------------- HDR files
def _rle(ch):
    """Radiance run-length encoding of one channel of one scanline."""
    out = bytearray()
    n = len(ch)
    i = 0
    while i < n:
        j = i + 1
        while j < n and j - i < 127 and ch[j] == ch[i]:
            j += 1
        if j - i >= 3:
            out.append(128 + j - i)
            out.append(int(ch[i]))
            i = j
            continue
        k = i
        while k < n and k - i < 128:
            if k + 2 < n and ch[k] == ch[k + 1] == ch[k + 2]:
                break
            k += 1
        out.append(k - i)
        out.extend(ch[i:k].tobytes())
        i = k
    return out


def write_hdr(path, rgb):
    """Write linear float RGB (rows top-down, H x W x 3) as Radiance RGBE.

    Not Image.save(): Blender 5.2 writes a float image to .hdr through the
    sRGB curve whatever the view transform (0.18 comes back as 0.461), so the
    probe and the outside light shipped display-referred for a while. The
    viewer reads .hdr as linear light."""
    rgb = np.maximum(np.asarray(rgb, np.float32), 0.0)
    h, w = rgb.shape[:2]
    v = rgb.max(axis=-1)
    m, e = np.frexp(v)
    scale = np.where(v > 1e-32, m * 256.0 / np.maximum(v, 1e-32), 0.0)
    rgbe = np.zeros((h, w, 4), np.uint8)
    rgbe[..., :3] = np.clip(rgb * scale[..., None], 0, 255).astype(np.uint8)
    rgbe[..., 3] = np.where(v > 1e-32, e + 128, 0).astype(np.uint8)
    with open(path, "wb") as f:
        f.write(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n")
        f.write(("-Y %d +X %d\n" % (h, w)).encode("ascii"))
        rle = 8 <= w < 32768
        for y in range(h):
            row = rgbe[y]
            if not rle:
                f.write(row.tobytes())
                continue
            f.write(bytes((2, 2, w >> 8, w & 255)))
            for c in range(4):
                f.write(_rle(row[:, c]))
    return path


def srgb_decode(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, np.power((np.maximum(c, 0) + 0.055) / 1.055, 2.4))


def relinearise_hdr(path):
    """Undo the sRGB curve on an .hdr that Image.save() wrote (see write_hdr)."""
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    rgb = srgb_decode(px.reshape(h, w, 4)[::-1, :, :3])
    return write_hdr(path, rgb)


# ------------------------------------------------------------------ backdrop
def neutral_tonemap(c):
    """THREE.NeutralToneMapping (Khronos PBR Neutral) on linear RGB, last
    axis = channels. Exposure is applied by the caller."""
    start = 0.8 - 0.04
    desat = 0.15
    x = c.min(axis=-1, keepdims=True)
    c = c - np.where(x < 0.08, x - 6.25 * x * x, 0.04)
    peak = c.max(axis=-1, keepdims=True)
    d = 1.0 - start
    new_peak = 1.0 - d * d / (peak + d - start)
    scaled = c * (new_peak / np.maximum(peak, 1e-9))
    g = 1.0 - 1.0 / (desat * (peak - new_peak) + 1.0)
    return np.where(peak < start, c, scaled * (1.0 - g) + new_peak * g)


def srgb_encode(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def backdrop(hdri_path, out_path, rotation=0.0, strength=1.0, exposure=1.0, quality=86):
    """The world as the viewer's view out: an equirect JPEG of the HDRI,
    turned by `rotation` as in scene.hdri_world() and tone mapped exactly as
    three.js would (x strength x exposure, NeutralToneMapping, sRGB).

    The viewer shows it as an sRGB scene.background, which three.js does not
    tone map again, so it matches the bake at the viewer's exposure. A JPEG
    rather than the HDR: 4k HDR is 25 MB, and the backdrop lights nothing.
    three.js' equirect mapping agrees with Blender's in world axes (centre
    column +X), so no flip."""
    img = bpy.data.images.load(hdri_path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3]
    px = np.roll(px, int(round(rotation / 360.0 * w)), axis=1)
    rgb = srgb_encode(neutral_tonemap(px * (strength * exposure)))
    out = bpy.data.images.new("_backdrop", w, h, alpha=False, float_buffer=False)
    rgba = np.concatenate([rgb, np.ones((h, w, 1), np.float32)], axis=-1).astype(np.float32)
    out.pixels.foreach_set(rgba.ravel())
    out.filepath_raw = out_path
    out.file_format = 'JPEG'
    try:
        out.save(quality=quality)
    except TypeError:            # older Blender: no quality argument
        out.save()
    bpy.data.images.remove(out)
    return out_path


def backdrop_light(hdri_path, out_path, rotation=0.0, strength=1.0, clamp=None, width=512):
    """The same world as a small linear HDR, for the viewer to light what it
    sees through the glass (mirror heads, bonnet) by.

    The backdrop JPEG cannot do it: tone mapped, its brightest sky sits at
    1.0, and the mirror housings' clear coat, which in Cycles mirrors a sky
    several times brighter, came out near-black (sRGB 9-26 against ~100).
    Clamped like the bake's world, then box-filtered to `width`."""
    img = bpy.data.images.load(hdri_path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3]
    px = np.roll(px, int(round(rotation / 360.0 * w)), axis=1) * strength
    if clamp:
        px = np.minimum(px, clamp * strength)
    f = max(1, w // width)
    hh, ww = h // f, w // f
    small = px[:hh * f, :ww * f].reshape(hh, f, ww, f, 3).mean(axis=(1, 3))
    # Blender's pixel rows run bottom-up; the file's top-down
    return write_hdr(out_path, small[::-1])


def sun_from_hdri(hdri_path, clamp=8.0, rotation=0.0, turn=0.0, cone=3.0):
    """The sun that `clamp` takes out of an HDRI, as the viewer's exterior
    DirectionalLight (the `outside.sun` of the vehicle data).

    The sun is the brightest pixel; everything above the clamp within `cone`
    degrees of it is what the light HDR loses. Its irradiance on a plane
    facing the sun gives the colour (normalised, sRGB hex, as three.js reads
    a Color) and the intensity (the brightest channel). `rotation` is the
    world's turn in Blender (scene.hdri_world, the cabin's), `turn` the
    exterior's extra turn (exteriorTurnDeg): the direction comes back in the
    viewer's axes [x forward, y up, z = -Blender y].

    Checked on the SU7's Shanghai riverside (rotation 153.6, turn 147.6): 20.3
    deg up, irradiance 1.51 (luminance), #ffdfae, 1.96, [0.6959, 0.3477,
    0.6284] - the values the viewer has shipped with."""
    import math
    img = bpy.data.images.load(hdri_path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[::-1, :, :3]              # rows top-down
    lum = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
    a = (0.5 - (ix + 0.5) / w) * 360.0                 # image angle: centre column +X
    e = (0.5 - (iy + 0.5) / h) * 180.0
    el = (0.5 - (np.arange(h) + 0.5) / h) * math.pi
    az = (0.5 - (np.arange(w) + 0.5) / w) * 2.0 * math.pi
    d = np.stack([np.cos(el)[:, None] * np.cos(az)[None, :],
                  np.cos(el)[:, None] * np.sin(az)[None, :],
                  np.sin(el)[:, None] * np.ones((1, w))], -1)
    s = np.array([math.cos(math.radians(e)) * math.cos(math.radians(a)),
                  math.cos(math.radians(e)) * math.sin(math.radians(a)),
                  math.sin(math.radians(e))])
    cos_s = d @ s
    dom = (2.0 * math.pi / w) * (math.pi / h) * np.cos(el)[:, None]
    weight = np.where(cos_s > math.cos(math.radians(cone)), cos_s, 0.0) * dom
    irr = (np.maximum(px - clamp, 0.0) * weight[..., None]).sum(axis=(0, 1))
    lin = irr / max(1e-9, float(irr.max()))
    hexc = "#" + "".join("%02x" % int(round(float(c) * 255)) for c in srgb_encode(lin))
    # where the viewer sees it: the cabin's turn, then the exterior's
    azv = math.radians(a - rotation + turn)
    ce = math.cos(math.radians(e))
    direction = (ce * math.cos(azv), math.sin(math.radians(e)), -ce * math.sin(azv))
    return dict(image_angle=round(float(a), 2), elevation=round(float(e), 2), colour=hexc,
                intensity=float(irr.max()),
                irradiance=float(irr @ np.array([0.2126, 0.7152, 0.0722])),
                direction=tuple(round(c, 4) for c in direction))
