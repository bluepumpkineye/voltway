"""Build checks, and build fingerprints for safe refactoring.

Checks that run on every build (see carkit.build.report):

    envelope    every evaluated vertex inside the car's bounding box. A
                modifier that goes singular (Solidify with even offset on a
                fold, Bevel with arc mitres on a sliver) throws vertices to
                absurd coordinates; the first sign is a stray line in a render.
    clearance   interior parts stay inside the body's upper skin.
    budget      evaluated triangle count against the web budget.

Fingerprints record a build - vertex and face counts, a hash of sampled
evaluated positions, the modifier stacks, material slots and material values,
and samples of the analytic surfaces - so a refactor can be proved to change
nothing: fingerprint before, change the code, rebuild, compare.
"""
import hashlib
import json

import bpy

WEB_TRI_BUDGET = (150000, 400000)


# ------------------------------------------------------------------ checks
def envelope(collections, half_l, half_w, margin=0.10, side_extra=0.12, z_max=1.60):
    """Objects with an evaluated vertex outside the car's box, with the vertex."""
    dg = bpy.context.evaluated_depsgraph_get()
    lim_x = half_l + margin
    lim_y = half_w + side_extra + margin
    bad = []
    for c in collections:
        for o in c.objects:
            if o.type != 'MESH':
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            for v in me.vertices:
                p = o.matrix_world @ v.co
                if abs(p.x) > lim_x or abs(p.y) > lim_y or p.z < -0.01 or p.z > z_max:
                    bad.append((o.name, tuple(round(c_, 3) for c_ in p)))
                    break
            ev.to_mesh_clear()
    return bad


def cabin_clearance(loft, collection_name, allowance=0.012, first_upper_index=44,
                    x_range=(-2.4, 2.4)):
    """Interior parts must stay `allowance` inside the body's upper skin.

    Checks every interior vertex against the section's upper surface at its
    (x, y) and returns (object, metres past the allowance) for offenders. When
    the SU7's cowl moved 145 mm forward and down, the dash, door cards,
    A-pillar trims and wheel rim all came through the new hood and screen.
    """
    col = bpy.data.collections.get(collection_name)
    if col is None:
        return []
    dg = bpy.context.evaluated_depsgraph_get()
    bad = []
    for o in col.objects:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        peak = 0.0
        for v in me.vertices:
            p = o.matrix_world @ v.co
            x, y = p.x, abs(p.y)
            if not (x_range[0] < x < x_range[1]):
                continue
            pts = loft.section(x)
            zs = None
            for i in range(first_upper_index, len(pts) - 1):
                (y0, z0), (y1, z1) = pts[i], pts[i + 1]
                if (y0 - y) * (y1 - y) <= 0.0 and abs(y1 - y0) > 1e-9:
                    zs = z0 + (z1 - z0) * (y - y0) / (y1 - y0)
            if zs is not None:
                peak = max(peak, p.z - (zs - allowance))
        ev.to_mesh_clear()
        if peak > 0.0:
            bad.append((o.name, round(peak, 4)))
    return bad


def budget(tris, lo=WEB_TRI_BUDGET[0], hi=WEB_TRI_BUDGET[1]):
    """'ok', 'under' or 'over' against the web hero-LOD budget."""
    return "under" if tris < lo else ("over" if tris > hi else "ok")


# ------------------------------------------------------------- fingerprint
def _bsdf_values(m):
    out = {}
    if not m or not m.use_nodes:
        return out
    for n in m.node_tree.nodes:
        if n.type != 'BSDF_PRINCIPLED':
            continue
        for inp in n.inputs:
            if inp.is_linked or not hasattr(inp, "default_value"):
                continue
            v = inp.default_value
            try:
                v = [round(float(c), 5) for c in v]
            except TypeError:
                try:
                    v = round(float(v), 5)
                except (TypeError, ValueError):
                    continue
            out[inp.name] = v
    return out


def _material_key(m):
    if m is None:
        return None
    nodes = sorted(n.type for n in m.node_tree.nodes) if m.use_nodes else []
    links = len(m.node_tree.links) if m.use_nodes else 0
    return {"nodes": nodes, "links": links, "bsdf": _bsdf_values(m)}


def _modifier_key(md):
    keys = {"type": md.type}
    for attr in ("thickness", "offset", "use_even_offset", "width", "segments",
                 "angle_limit", "harden_normals", "miter_outer", "use_clip",
                 "merge_threshold", "weight", "mode", "keep_sharp", "thresh"):
        if hasattr(md, attr):
            v = getattr(md, attr)
            if isinstance(v, float):
                v = round(v, 6)
            elif not isinstance(v, (int, bool, str)):
                v = str(v)
            keys[attr] = v
    return keys


def fingerprint(collections, body=None, section_x=None, stride=400, points=True):
    """A JSON-able record of a build. See the module docstring.

    points=True also stores the sampled positions (0.01 mm), so two builds
    can be compared to a tolerance with max_deviation() as well as exactly.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    objects, slots, mods, used, pos = {}, {}, {}, set(), {}
    for c in collections:
        col = bpy.data.collections.get(c)
        if col is None:
            continue
        for o in col.objects:
            if o.type != 'MESH':
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            mw = o.matrix_world
            pts = [mw @ v.co for v in me.vertices]
            h = hashlib.md5()
            picked = pts[::max(1, len(pts) // stride)]
            for p in picked:
                h.update(("%.4f,%.4f,%.4f;" % (p.x, p.y, p.z)).encode())
            objects[o.name] = [len(me.vertices), len(me.polygons), h.hexdigest()[:10]]
            if points:
                pos[o.name] = [round(c, 5) for p in picked for c in (p.x, p.y, p.z)]
            ev.to_mesh_clear()
            slots[o.name] = [m.name if m else None for m in o.data.materials]
            used.update(m.name for m in o.data.materials if m)
            mods[o.name] = [_modifier_key(md) for md in o.modifiers]
    materials = {n: _material_key(bpy.data.materials.get(n)) for n in sorted(used)}

    samples = {}
    if body is not None:
        loft = body.loft
        if section_x is None:
            e = round(loft.HALF_L - 0.05, 1)
            section_x = (-e, e)
        a, b = section_x
        for i in range(41):
            x = a + (b - a) * i / 40
            samples["sec%.3f" % x] = [round(c, 6) for p in loft.section(x)[::7] for c in p]
        for w in (0.0, 0.3, 0.6, 0.9, 1.0):
            for v in (0.1, 0.4, 0.7, 0.95):
                samples["capF%.1f_%.2f" % (w, v)] = [round(c, 6) for c in body.nose.point(w, v)]
                samples["capR%.1f_%.2f" % (w, v)] = [round(c, 6) for c in body.tail.point(w, v)]
    out = {"objects": objects, "samples": samples, "slots": slots,
           "modifiers": mods, "materials": materials}
    if points:
        out["points"] = pos
    return out


def max_deviation(a, b):
    """Per-object largest coordinate difference (metres) between two
    fingerprints taken with points=True, for objects with matching counts.
    Returns (worst, {name: deviation}) - sorted report of what moved."""
    pa, pb = a.get("points", {}), b.get("points", {})
    dev = {}
    for k in set(pa) & set(pb):
        if len(pa[k]) != len(pb[k]):
            dev[k] = float("inf")
            continue
        dev[k] = max((abs(x - y) for x, y in zip(pa[k], pb[k])), default=0.0)
    worst = max(dev.values(), default=0.0)
    return worst, dict(sorted(dev.items(), key=lambda kv: -kv[1]))


def save(fp, path):
    with open(path, "w") as fh:
        json.dump(fp, fh, indent=0, sort_keys=True)
    return path


def load(path):
    with open(path) as fh:
        return json.load(fh)


def compare(a, b, sections=("objects", "samples", "slots", "modifiers", "materials")):
    """Differences between two fingerprints, as readable lines ([] = identical).

    Sections missing from either side are skipped, so an older, partial
    fingerprint can still be compared on what it has.
    """
    out = []
    for sec in sections:
        if sec not in a or sec not in b:
            continue
        da, db = a[sec], b[sec]
        for k in sorted(set(da) | set(db)):
            if k not in da:
                out.append("%s: + %s (new)" % (sec, k))
            elif k not in db:
                out.append("%s: - %s (missing)" % (sec, k))
            elif da[k] != db[k]:
                out.append("%s: ~ %s  %s -> %s" % (sec, k, str(da[k])[:120], str(db[k])[:120]))
    return out
