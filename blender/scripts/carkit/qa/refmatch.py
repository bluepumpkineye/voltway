"""Camera-matched comparison against reference photographs.

Why this exists
---------------
Reading hardpoints off a photograph by eye goes wrong in a way that looks
right. A showroom side shot is a ~50 mm lens from ~6.6 m, so the nose and tail
- a metre further from the lens than the wheels - are shrunk by 12 %, and a
feature lands in a different place depending on how far across the car it
sits. The SU7's first builds put the headlamps 182 mm and the wing 200 mm too
high that way, and compared an orthographic render against a perspective
photo, which made the whole front read long.

So the comparison runs the other way: solve the photographer's camera from
things that are certain (wheelbase, wheel centres, ground line), render the
model through that camera, and draw its outline and every panel boundary over
the photo. Whatever does not line up is a modelling error.

    solve_side_camera(...)          camera from wheel centres + ground line
    register(name, ref_path, ...)   add a solved camera
    overlay(name, tag)              -> renders/match/<name>_<tag>_overlay.png
    to_world(name, u, v, y)         photo pixel -> (x, z) at lateral depth y
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

_BLENDER = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REF_ROOT = os.path.join(_BLENDER, "reference")
OUT_DIR = os.path.join(_BLENDER, "renders", "match")

# name: (reference file path, image size, camera location, euler XYZ deg, f in px)
CAMERAS = {}


# name: (du, dv) principal-point offset from the image centre, px (v down).
# CG press renders often use a shifted lens to keep verticals upright; a
# pinhole fit without the shift leaves 10-20 px residuals everywhere.
PP = {}


def register(name, ref_path, size, loc, rot, f_px, pp=(0.0, 0.0)):
    """Add a solved camera. ref_path absolute, or relative to blender/reference."""
    if not os.path.isabs(ref_path):
        ref_path = os.path.join(REF_ROOT, ref_path)
    ref_path = os.path.normpath(ref_path)
    CAMERAS[name] = (ref_path, tuple(size), tuple(loc), tuple(rot), float(f_px))
    PP[name] = (float(pp[0]), float(pp[1]))
    return CAMERAS[name]


# ----------------------------------------------------------------- solving
def solve_side_camera(size, u_front, u_rear, v_axle, v_ground, wheelbase,
                      x_front_axle, wheel_r, y_wheel, f_px=None, check=None):
    """A side camera (looking along -Y at the car's left side) from photo
    measurements of certain things.

    size            (width, height) of the photo in px
    u_front/u_rear  image x of the front and rear wheel centres (hub caps)
    v_axle          image y of the wheel centres (their mean)
    v_ground        image y of the ground line under the tyres
    wheelbase, x_front_axle, wheel_r, y_wheel (lateral offset of the hub
    face, ~ track/2 + a little) in model metres.

    f_px: focal length in pixels if known (EXIF: f_mm / sensor_mm * width). If
    None, `check` = (u, v, (x, y, z)) - one known point at a DIFFERENT depth
    (the roof peak on the centreline is ideal) - fixes it; a single plane of
    features only determines f / distance.

    Returns dict(loc, rot, f_px, lens_mm, k_wb, k_r). k_wb and k_r are the
    px-per-metre scale from the wheelbase and from the wheel radius: if they
    disagree by more than ~1 % a measurement or y_wheel is wrong.
    """
    w, h = size
    cu, cv = 0.5 * w, 0.5 * h
    k_wb = (u_rear - u_front) / float(wheelbase)          # f / D
    k_r = (v_ground - v_axle) / float(wheel_r)
    k = k_wb
    cz = wheel_r + (v_axle - cv) / k
    cx = x_front_axle + (u_front - cu) / k

    def depth_for(f):
        return f / k

    if f_px is None:
        if check is None:
            raise ValueError("need f_px or a check point at another depth")
        (uc, vc, (xc, yc, zc)) = check

        def err(f):
            dc = y_wheel + depth_for(f) - yc
            uu = cu - f * (xc - cx) / dc
            vv = cv - f * (zc - cz) / dc
            return (uu - uc) ** 2 + (vv - vc) ** 2

        best = min((err(200.0 + 3.0 * i), 200.0 + 3.0 * i) for i in range(2001))
        f0 = best[1]                           # coarse: 200 .. 6200 px
        f_px = min((err(f0 - 3.0 + 0.01 * i), f0 - 3.0 + 0.01 * i) for i in range(601))[1]
    D = depth_for(f_px)
    loc = (cx, y_wheel + D, cz)
    return dict(loc=loc, rot=(90.0, 0.0, 180.0), f_px=f_px,
                lens_mm=36.0 * f_px / w, k_wb=k_wb, k_r=k_r)


def _project_raw(size, loc, rot, f_px, p, pp=(0.0, 0.0)):
    """project() for a camera that is not registered: (u, v) or None."""
    from mathutils import Euler
    w, h = size
    R = Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix()
    c = R.transposed() @ (Vector(p) - Vector(loc))
    if c.z >= 0:
        return None
    return (0.5 * w + pp[0] + f_px * c.x / -c.z, 0.5 * h + pp[1] - f_px * c.y / -c.z)


class Circle:
    """A 3D circle for solve_camera: centre, radius and axis (unit normal)."""

    def __init__(self, centre, radius, axis=(0.0, 1.0, 0.0), n=96):
        self.c = Vector(centre)
        self.r = float(radius)
        a = Vector(axis).normalized()
        e1 = a.orthogonal().normalized()
        self.e1, self.e2 = e1, a.cross(e1).normalized()
        self.n = n

    def points(self):
        return [self.c + (self.e1 * math.cos(2 * math.pi * k / self.n)
                          + self.e2 * math.sin(2 * math.pi * k / self.n)) * self.r
                for k in range(self.n)]


def circle(centre, radius, axis=(0.0, 1.0, 0.0)):
    return Circle(centre, radius, axis)


def solve_camera(size, pairs, loc, rot, f_px, fix=(), iters=200, weights=None,
                 extra=()):
    """General camera from 2D-3D correspondences (Levenberg-Marquardt).

    For photographs that are not square-on: a showroom "side" shot is often
    yawed a few degrees, which solve_side_camera cannot represent - on the
    Luxeed RX's side photo the rear rim is 11 % smaller than the front one.

    pairs      [((u, v), (x, y, z)), ...] photo pixel <-> model point, or
               [((u, v), circle(centre, radius, axis)), ...] a pixel anywhere
               on a known 3D circle (a rim lip: pick points round its edge,
               no need to know which angle each one is at)
    loc, rot   initial camera location and Blender euler XYZ (degrees)
    f_px       initial focal length in px
    fix        names to hold: any of "loc", "rot", "f", "x", "y", "z",
               "rx", "ry", "rz"
    weights    optional per-pair weights
    extra      initial values of unknown scene parameters, solved with the
               camera. A pair's model point may then be a function of them,
               lambda e: (e[0], 0.22, e[1]) - a plate corner whose plate
               centre is unknown, or one of a mirror pair (x, +/-y, z). A
               known-size object at another depth (a 440 mm plate on the
               nose) is what pins the focal length of a 3/4 shot.

    Returns dict(loc, rot, f_px, lens_mm, rms, resid[(du, dv), ...], extra).
    A single plane of points (a flank seen from the side) fixes f only
    weakly: add points at another depth (roof centreline, the far tyre,
    the nose tip) or hold f from EXIF.
    """
    names = ["x", "y", "z", "rx", "ry", "rz", "f"]
    held = set()
    for k in fix:
        held |= {"loc": {"x", "y", "z"}, "rot": {"rx", "ry", "rz"}}.get(k, {k})
    free = [i for i, n in enumerate(names) if n not in held]
    free += list(range(7, 7 + len(extra)))
    p = np.array(list(loc) + list(rot) + [f_px] + list(extra), float)
    wts = np.ones(len(pairs)) if weights is None else np.asarray(weights, float)

    def resid(q):
        r = []
        cache = {}
        ex = q[7:]
        for ((u, v), X), wt in zip(pairs, wts):
            if callable(X):
                X = X(ex)
            if isinstance(X, Circle):
                key = id(X)
                if key not in cache:
                    pts = [_project_raw(size, q[0:3], q[3:6], q[6], P) for P in X.points()]
                    cache[key] = np.array([p for p in pts if p is not None] or [(1e4, 1e4)])
                pp = cache[key]
                # distance to the projected polyline (segments, not vertices)
                a, b = pp, np.roll(pp, -1, axis=0)
                ab = b - a
                t = np.clip(((u - a[:, 0]) * ab[:, 0] + (v - a[:, 1]) * ab[:, 1])
                            / np.maximum((ab * ab).sum(1), 1e-12), 0.0, 1.0)
                d = np.hypot(a[:, 0] + ab[:, 0] * t - u, a[:, 1] + ab[:, 1] * t - v).min()
                r += [wt * d, 0.0]
                continue
            uv = _project_raw(size, q[0:3], q[3:6], q[6], X)
            if uv is None:
                r += [1e3, 1e3]
            else:
                r += [wt * (uv[0] - u), wt * (uv[1] - v)]
        return np.array(r)

    lam = 1e-3
    r = resid(p)
    cost = r @ r
    steps = np.array([1e-4, 1e-4, 1e-4, 1e-3, 1e-3, 1e-3, 1e-2] + [1e-4] * len(extra))
    for _ in range(iters):
        J = np.zeros((len(r), len(free)))
        for j, i in enumerate(free):
            q = p.copy()
            q[i] += steps[i]
            J[:, j] = (resid(q) - r) / steps[i]
        A = J.T @ J
        g = J.T @ r
        improved = False
        for _ in range(12):
            d = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            q = p.copy()
            q[free] += d
            rq = resid(q)
            cq = rq @ rq
            if cq < cost:
                p, r, cost = q, rq, cq
                lam = max(lam / 3.0, 1e-9)
                improved = True
                break
            lam *= 4.0
        if not improved or np.abs(d).max() < 1e-9:
            break
    w = size[0]
    res = [(r[2 * k] / max(wts[k], 1e-9), r[2 * k + 1] / max(wts[k], 1e-9))
           for k in range(len(pairs))]
    rms = math.sqrt(sum(a * a + b * b for a, b in res) / max(1, len(res)))
    return dict(loc=tuple(float(c) for c in p[0:3]), rot=tuple(float(c) for c in p[3:6]),
                f_px=float(p[6]), lens_mm=36.0 * p[6] / w, rms=rms, resid=res,
                extra=tuple(float(c) for c in p[7:]))


def camera(name):
    ref, (w, h), loc, rot, f_px = CAMERAS[name]
    cname = "CAM_match_" + name
    cam = bpy.data.objects.get(cname)
    if cam is None:
        cam = bpy.data.objects.new(cname, bpy.data.cameras.new(cname))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.sensor_width = 36.0
    cam.data.lens = 36.0 * f_px / w
    du, dv = PP.get(name, (0.0, 0.0))
    cam.data.shift_x = -du / float(max(w, h))
    cam.data.shift_y = dv / float(max(w, h))
    cam.data.clip_start = 0.05
    cam.location = Vector(loc)
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    return cam


def to_world(name, u, v, y):
    """Photo pixel (u, v) of a feature known to lie at lateral offset y -> (x, z).

    Side cameras only (looking along -Y).
    """
    _, (w, h), (cx_, cy_, cz_), _, f = CAMERAS[name]
    depth = cy_ - y
    return (cx_ + (0.5 * w - u) * depth / f, cz_ + (0.5 * h - v) * depth / f)


def ray(name, u, v):
    """World ray (origin, unit direction) through photo pixel (u, v)."""
    from mathutils import Euler
    _, (w, h), loc, rot, f = CAMERAS[name]
    du, dv = PP.get(name, (0.0, 0.0))
    d = Vector(((u - 0.5 * w - du) / f, -(v - 0.5 * h - dv) / f, -1.0))
    R = Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix()
    return Vector(loc), (R @ d).normalized()


def on_mesh(name, u, v, objects):
    """Where the ray through photo pixel (u, v) first hits any of `objects`
    (evaluated meshes): (x, y, z) or None. Read features off a photograph
    ONTO the model - the way to place a lamp edge or an intake outline that
    wraps a corner, which no single plane can."""
    from mathutils.bvhtree import BVHTree
    o, d = ray(name, u, v)
    best = None
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in objects:
        key = (ob.name, ob.data.name if ob.data else "")
        tree = _BVH.get(key)
        if tree is None:
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ob.matrix_world
            tree = BVHTree.FromPolygons([mw @ vv.co for vv in me.vertices],
                                        [list(p.vertices) for p in me.polygons])
            ev.to_mesh_clear()
            _BVH[key] = tree
        hit = tree.ray_cast(o, d)
        if hit[0] is not None and (best is None or hit[3] < best[1]):
            best = (tuple(hit[0]), hit[3])
    return best[0] if best else None


_BVH = {}


def clear_bvh():
    _BVH.clear()


def on_plane(name, u, v, point, normal):
    """Where the ray through pixel (u, v) meets a plane: e.g. the driver's
    seat centreline plane y = 0.37 (point (0, 0.37, 0), normal (0, 1, 0))."""
    o, d = ray(name, u, v)
    n = Vector(normal)
    den = d.dot(n)
    if abs(den) < 1e-9:
        return None
    t = (Vector(point) - o).dot(n) / den
    return tuple(o + d * t)


def project(name, p):
    """Photo pixel (u, v) of a world point (the inverse of ray)."""
    from mathutils import Euler
    _, (w, h), loc, rot, f = CAMERAS[name]
    du, dv = PP.get(name, (0.0, 0.0))
    R = Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix()
    c = R.transposed() @ (Vector(p) - Vector(loc))
    if c.z >= 0:
        return None
    return (0.5 * w + du + f * c.x / -c.z, 0.5 * h + dv - f * c.y / -c.z)


# ------------------------------------------------------------------ images
def load(path):
    """Image as float array [row, col, 4], row 0 at the TOP."""
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(img)
    return a


def save(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("_match_save", w, h, alpha=True)
    img.pixels[:] = np.ascontiguousarray(arr[::-1]).reshape(-1)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def _id_material():
    """Flat per-object colour: every object renders as its own solid swatch."""
    m = bpy.data.materials.get("M_MatchID")
    if m:
        return m
    m = bpy.data.materials.new("M_MatchID")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    info = nt.nodes.new('ShaderNodeObjectInfo')
    hsv = nt.nodes.new('ShaderNodeCombineColor')
    hsv.mode = 'HSV'
    hsv.inputs[1].default_value = 0.9
    hsv.inputs[2].default_value = 1.0
    nt.links.new(info.outputs["Random"], hsv.inputs[0])
    nt.links.new(hsv.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def render_passes(name, tag, hide=()):
    """Render a flat object-ID image (with alpha) through the matched camera.

    hide: substrings of object names to leave out - e.g. from INSIDE the car
    hide the glass and the hidden shell so the window openings, and the hood
    and mirrors seen through them, can be matched.
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    scn = bpy.context.scene
    ref, (w, h), *_ = CAMERAS[name]
    cam = camera(name)
    old = (scn.camera, scn.render.film_transparent, scn.render.resolution_x,
           scn.render.resolution_y, scn.view_layers[0].material_override,
           scn.cycles.samples, scn.cycles.use_denoising,
           scn.cycles.pixel_filter_type, scn.render.image_settings.color_mode)
    hidden = []
    for o in scn.objects:
        if o.type == 'MESH' and not o.hide_render and (
                o.name == "Ground" or o.name.startswith("REFL")
                or any(s in o.name for s in hide)):
            o.hide_render = True
            hidden.append(o)
    try:
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = w, h
        scn.render.resolution_percentage = 100
        scn.render.film_transparent = True
        scn.render.image_settings.file_format = 'PNG'
        scn.render.image_settings.color_mode = 'RGBA'
        scn.view_layers[0].material_override = _id_material()
        scn.cycles.samples = 1
        scn.cycles.use_denoising = False
        scn.cycles.pixel_filter_type = 'BOX'
        path = os.path.join(OUT_DIR, "%s_%s_id.png" % (name, tag))
        scn.render.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        (scn.camera, scn.render.film_transparent, scn.render.resolution_x,
         scn.render.resolution_y, scn.view_layers[0].material_override,
         scn.cycles.samples, scn.cycles.use_denoising,
         scn.cycles.pixel_filter_type, scn.render.image_settings.color_mode) = old
        for o in hidden:
            o.hide_render = False
    return path


def boundaries(id_img, tol=0.02):
    """Pixels where the object ID changes, plus the silhouette."""
    rgb = id_img[..., :3]
    a = id_img[..., 3] > 0.5
    e = np.zeros(a.shape, bool)
    d_r = np.abs(rgb[:, 1:] - rgb[:, :-1]).max(axis=2) > tol
    d_d = np.abs(rgb[1:] - rgb[:-1]).max(axis=2) > tol
    e[:, 1:] |= d_r | (a[:, 1:] != a[:, :-1])
    e[1:] |= d_d | (a[1:] != a[:-1])
    sil = np.zeros(a.shape, bool)
    sil[:, 1:] |= a[:, 1:] != a[:, :-1]
    sil[1:] |= a[1:] != a[:-1]
    return e & ~sil, sil


def silhouette_error(name, tag, polyline, reach=60):
    """Signed px distance from a TRACED photo outline to the model's outline.

    polyline: [(u, v), ...] along the photo's silhouette, in order. At each
    point the model's alpha mask (from the last render_passes(name, tag)) is
    searched along the polyline's normal: + means the model sticks OUT past
    the photo's outline there, - means it falls short. None where the
    model's edge is further than `reach` px away.
    """
    idp = os.path.join(OUT_DIR, "%s_%s_id.png" % (name, tag))
    a = load(idp)[..., 3] > 0.5
    h, w = a.shape
    pts = np.asarray(polyline, float)
    out = []
    # the model's inside at the start of the outline tells which normal
    # direction points outward
    for i, (u, v) in enumerate(pts):
        p0 = pts[max(0, i - 1)]
        p1 = pts[min(len(pts) - 1, i + 1)]
        t = p1 - p0
        t /= max(1e-9, np.hypot(*t))
        n = np.array([t[1], -t[0]])            # right-hand normal
        best = None
        inside0 = None
        for k in range(0, reach + 1):
            for sgn in ((1,) if k == 0 else (1, -1)):
                q = np.array([u, v]) + n * k * sgn
                qi, qj = int(round(q[1])), int(round(q[0]))
                ins = bool(a[qi, qj]) if (0 <= qi < h and 0 <= qj < w) else False
                if inside0 is None:
                    inside0 = ins
                elif ins != inside0 and best is None:
                    best = k * sgn
            if best is not None:
                break
        out.append((float(u), float(v), best, inside0))
    return out


def silhouette_report(name, tag, polyline, outward=None, reach=60):
    """silhouette_error as signed errors: + = model outside the photo outline.

    outward: a point well OUTSIDE the car in the photo (e.g. the sky), used
    to orient each normal; default: the image's top-centre.
    """
    res = silhouette_error(name, tag, polyline, reach)
    ref, (w, h), *_ = CAMERAS[name]
    ox, oy = outward or (0.5 * w, 0.0)
    pts = np.asarray(polyline, float)
    errs = []
    for i, (u, v, k, inside0) in enumerate(res):
        if k is None:
            errs.append(None)
            continue
        # the model outline is k px along +n from the photo point. The
        # photo point is on the car's outline: if the model covers it
        # (inside0) the model reaches past it -> positive.
        mag = abs(k)
        errs.append(mag if inside0 else -mag)
    return errs


def overlay(name, tag, hide=()):
    """Draw the model's panel lines (cyan) and outline (magenta) on the photo."""
    ref_file, *_ = CAMERAS[name]
    photo = load(ref_file)
    idp = render_passes(name, tag, hide)
    inner, sil = boundaries(load(idp))
    out = photo.copy()
    out[inner] = (0.0, 0.95, 1.0, 1.0)
    out[sil] = (1.0, 0.0, 1.0, 1.0)
    path = os.path.join(OUT_DIR, "%s_%s_overlay.png" % (name, tag))
    save(out, path)
    return path
