"""The white studio the showroom stands a car in, as Blender sees it.

What the web viewer draws live (a procedural white cove, a mirror floor, the
dark light rig of src/data/studio/rig.ts) has a Blender half here:

    ground_shadow(...)   the car's shadow on the studio floor, baked: ambient
                         occlusion of the floor from the car, as an RGBA image
                         whose alpha is the shade. The viewer lays it on the
                         floor as one quad (StudioShowroom.tsx, GroundShadow)
                         instead of rendering a blurred shadow every time.

A baked shadow costs one texture and nothing per frame, and shows what a
projected one cannot: the dark core under the sills, the tyres' contact patches
and the soft fall-off of a white room, all from the car's real geometry.

    from carkit import studio
    studio.ground_shadow(r"public/models/luxeed-rx-shadow.png", car_objects,
                         hide=cabin_objects)
"""
import math
import os
import shutil
import subprocess

import bpy
import bmesh
import numpy as np

# the repo's scripts/to-webp.mjs (sharp, from Next.js's own install)
TO_WEBP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "..", "..", "scripts", "to-webp.mjs"))

# an 8-bit RGBA PNG; sharp turns it into the WebP the viewer loads
SHADOW_TINT = (0.035, 0.040, 0.055)


def footprint(objects):
    """The (min x, min y, max x, max y) of the objects' bounding boxes."""
    from mathutils import Vector
    lo = [1e9, 1e9]
    hi = [-1e9, -1e9]
    for o in objects:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = [min(lo[0], p.x), min(lo[1], p.y)]
            hi = [max(hi[0], p.x), max(hi[1], p.y)]
    return lo[0], lo[1], hi[0], hi[1]


def _floor(name, size, centre=(0.0, 0.0), z=0.0):
    """A rectangle of `size` (x, y) metres about `centre`, UV-mapped 0..1."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    hx, hy = size[0] / 2.0, size[1] / 2.0
    cx, cy = centre
    vs = [bm.verts.new(p) for p in ((cx - hx, cy - hy, z), (cx + hx, cy - hy, z),
                                    (cx + hx, cy + hy, z), (cx - hx, cy + hy, z))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _bake_ao(floor, image, distance, samples):
    """Bake the floor's ambient occlusion out to `distance` metres into `image`."""
    scn = bpy.context.scene
    scn.world.light_settings.distance = distance
    scn.cycles.samples = samples
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    floor.select_set(True)
    bpy.context.view_layer.objects.active = floor
    mat = floor.data.materials[0]
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            n.image = image
            mat.node_tree.nodes.active = n
    with bpy.context.temp_override(active_object=floor, object=floor, selected_objects=[floor],
                                   selected_editable_objects=[floor]):
        bpy.ops.object.bake(type='AO', target='IMAGE_TEXTURES', use_clear=True, margin=4)
    w, h = image.size
    px = np.empty(w * h * 4, np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[:, :, 0]          # rows bottom-up, as Blender keeps them


def _blur(a, sigma):
    """Separable Gaussian blur of a 2D array."""
    r = int(math.ceil(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, ((r, r), (r, r)), mode="edge")
    p = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, p)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, p)[:a.shape[0], :a.shape[1]]


def ground_shadow(path, car, margin=1.5, ppm=125, far=1.3, near=0.25, gain=0.9,
                  gamma=1.4, samples=192, hide=()):
    """Bake the car's shadow on the studio floor to a PNG: RGB a cool near-black,
    alpha the shade.

    car      the exterior's mesh objects, in the pose to cast from (shut, merged)
    margin   how far past the car's footprint the image reaches, m; `ppm` is
             its pixels to the metre
    far      occlusion distance of the broad soft shade, m; `near` that of the
             contact shade at the tyres and under the sills. The two multiply.
    gain, gamma   the darkest the shade gets, and how fast it falls away

    The floor is the only thing lit: ambient occlusion ignores materials and
    lights, so the result is the car's geometry alone. Returns the image's size
    and centre in metres (the build's axes, x forward and y left: the viewer
    needs both to lay the quad) and its size in pixels.
    """
    scn = bpy.context.scene
    try:
        scn.render.engine = 'CYCLES'
    except TypeError:
        pass
    made_world = None
    if scn.world is None:
        made_world = scn.world = bpy.data.worlds.new("W_Shadow")
    saved = (scn.world.light_settings.distance,)

    x0, y0, x1, y1 = footprint(car)
    size = (x1 - x0 + 2.0 * margin, y1 - y0 + 2.0 * margin)
    centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    res = (int(round(size[0] * ppm)), int(round(size[1] * ppm)))
    floor = _floor("ShadowFloor", size, centre)
    mat = bpy.data.materials.new("M_ShadowFloor")
    mat.use_nodes = True
    mat.node_tree.nodes.new('ShaderNodeTexImage')
    floor.data.materials.append(mat)
    image = bpy.data.images.new("ShadowBake", res[0], res[1], alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'

    hidden = []
    for o in list(hide) + [bpy.data.objects.get("Ground")]:
        if o is not None and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    for o in car:
        o.hide_render = False
        o.hide_set(False)
    try:
        ao_far = _bake_ao(floor, image, far, samples)
        ao_near = _bake_ao(floor, image, near, samples)
    finally:
        for o in hidden:
            o.hide_render = False
        scn.world.light_settings.distance = saved[0]
        bpy.data.objects.remove(floor, do_unlink=True)
        bpy.data.materials.remove(mat)
        bpy.data.images.remove(image)
        if made_world is not None:
            scn.world = None
            bpy.data.worlds.remove(made_world)

    shade = 1.0 - np.clip(ao_far, 0, 1) * np.clip(ao_near, 0, 1)
    shade = _blur(shade, 2.0)
    # zero at the image's edge, so no rectangle shows
    h, w = shade.shape
    ex = np.minimum(np.arange(w), np.arange(w)[::-1]) / (0.35 * margin * ppm)
    ey = np.minimum(np.arange(h), np.arange(h)[::-1]) / (0.35 * margin * ppm)
    t = np.clip(np.minimum(ey[:, None], ex[None, :]), 0.0, 1.0)
    shade *= t * t * (3.0 - 2.0 * t)
    alpha = np.clip(gain * np.power(np.clip(shade, 0, 1), gamma), 0.0, 1.0)

    out = np.empty((h, w, 4), np.float32)
    out[..., 0], out[..., 1], out[..., 2] = SHADOW_TINT
    out[..., 3] = alpha
    img = bpy.data.images.new("ShadowOut", w, h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = 'sRGB'
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    print("ground shadow: %s  %dx%d px, %.3f x %.3f m about (%.3f, %.3f), alpha max %.2f mean %.3f" % (
        path, w, h, size[0], size[1], centre[0], centre[1], float(alpha.max()), float(alpha.mean())))
    return dict(size=tuple(round(v, 3) for v in size), centre=tuple(round(v, 3) for v in centre),
                px=(w, h))


def to_webp(png, webp, quality=82, trim=False, width=None):
    """The baked PNG as the WebP the viewer loads (scripts/to-webp.mjs, needs
    node). `trim` cuts a cut-out's transparent margin, `width` resizes.
    Returns the path, or None with a warning if node is not there."""
    node = shutil.which("node")
    if node is None:
        print("WARNING: node not found - %s stays a PNG, convert it with scripts/to-webp.mjs" % png)
        return None
    os.makedirs(os.path.dirname(webp), exist_ok=True)
    cmd = [node, TO_WEBP, png, webp, str(quality)]
    if trim:
        cmd.append("--trim")
    if width:
        cmd += ["--width", str(width)]
    subprocess.run(cmd, check=True)
    return webp
