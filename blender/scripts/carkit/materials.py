"""The material library: one Principled BSDF per role, glTF-safe.

Every material uses only inputs that survive glTF 2.0 - base colour, metallic,
roughness, normal, emission, coat, IOR, transmission - and anything procedural
is baked to pixels (carkit.textures) so the browser gets what the render shows.

    build_library(paint="xiaomi_yellow", rim="gloss_black", caliper="gold",
                  lights_on=False, overrides=None) -> {role: material}

Roles every part in the catalogue uses:

    paint, black_gloss, grille (satin black), stripe, carbon,
    glass, glass_dark, lens, lamp_housing, lamp_bowl, lamp_smoked,
    led_white, led_red, led_red_tail (lit when tail_lights > 0), reflector,
    plate, text_dark,
    rim, rim_lip, chrome, disc, caliper, rubber, shadow, interior

Three rules that mattered more than the rest on the SU7:

* Car paint is NOT a metal. Metallic stays 0: colour in a dielectric base
  coat, gloss in a separate clearcoat, and for metallic paints the sparkle in
  a sparse masked flake layer on the BASE normal, never the coat normal.
* Carbon-ceramic discs are a dark matte composite, not polished steel.
* Real transmission only in Cycles. KHR_materials_transmission blanks the
  three.js frame, so export_safe() swaps glass for dark opaque glass just
  before export.

Paint values are starting points. Back-solve each car's colour from its
reference photographs under the studio rig and add it to PAINTS.
"""
import bpy

TRANSMISSIVE = ("M_Glass", "M_Glass_Privacy", "M_Lamp_Cover")

# ------------------------------------------------------------------- paints
# base: linear RGB of the colour coat. flake: None for solid colours, or
# dict(scale, bump, metal_max) for metallics. peel: orange-peel strength.
PAINTS = {
    # Xiaomi SU7 Ultra launch yellow - solid, no flake: at render resolution a
    # flake layer only adds sparkle noise to every softbox reflection.
    "xiaomi_yellow": dict(name="M_Paint_Yellow", base=(0.760, 0.485, 0.005),
                          roughness=0.28, specular=0.08, coat_rough=0.035,
                          peel=0.012, flake=None),
    "solid_white": dict(name="M_Paint_White", base=(0.780, 0.780, 0.770),
                        roughness=0.30, specular=0.10, coat_rough=0.035,
                        peel=0.012, flake=None),
    "solid_black": dict(name="M_Paint_Black", base=(0.011, 0.011, 0.012),
                        roughness=0.20, specular=0.25, coat_rough=0.030,
                        peel=0.020, flake=None),
    "solid_red": dict(name="M_Paint_Red", base=(0.420, 0.018, 0.016),
                      roughness=0.28, specular=0.08, coat_rough=0.035,
                      peel=0.012, flake=None),
    "pearl_white": dict(name="M_Paint_PearlWhite", base=(0.760, 0.760, 0.740),
                        roughness=0.26, specular=0.10, coat_rough=0.030,
                        peel=0.012, flake=dict(scale=3200.0, bump=0.02, metal_max=0.05)),
    "metallic_silver": dict(name="M_Paint_Silver", base=(0.330, 0.340, 0.350),
                            roughness=0.32, specular=0.20, coat_rough=0.030,
                            peel=0.012, flake=dict(scale=2600.0, bump=0.04, metal_max=0.18)),
    "metallic_grey": dict(name="M_Paint_Grey", base=(0.085, 0.090, 0.095),
                          roughness=0.30, specular=0.20, coat_rough=0.030,
                          peel=0.012, flake=dict(scale=2600.0, bump=0.04, metal_max=0.12)),
    "metallic_blue": dict(name="M_Paint_Blue", base=(0.010, 0.032, 0.095),
                          roughness=0.30, specular=0.15, coat_rough=0.030,
                          peel=0.012, flake=dict(scale=2600.0, bump=0.04, metal_max=0.12)),
    "metallic_green": dict(name="M_Paint_Green", base=(0.020, 0.075, 0.050),
                           roughness=0.30, specular=0.15, coat_rough=0.030,
                           peel=0.012, flake=dict(scale=2600.0, bump=0.04, metal_max=0.10)),
    "matte_grey": dict(name="M_Paint_MatteGrey", base=(0.120, 0.124, 0.128),
                       roughness=0.55, specular=0.10, coat_rough=0.42,
                       peel=0.0, flake=None),
}

# rim finishes: kwargs for the "rim" role
RIMS = {
    # Deep gloss black: at 0.028 under a full coat the SU7's spoke faces
    # mirrored the grey studio and read gunmetal.
    "gloss_black": dict(base=(0.010, 0.010, 0.011), metallic=0.0, roughness=0.20,
                        coat=1.0, coat_rough=0.05, ior=1.45),
    "satin_black": dict(base=(0.014, 0.014, 0.015), metallic=0.0, roughness=0.45,
                        coat=0.0),
    "gunmetal": dict(base=(0.090, 0.092, 0.098), metallic=0.85, roughness=0.30,
                     coat=1.0, coat_rough=0.06),
    "silver": dict(base=(0.560, 0.570, 0.590), metallic=0.90, roughness=0.26,
                   coat=1.0, coat_rough=0.05),
}

# caliper paints: kwargs for the "caliper" role (painted, so dielectric)
CALIPERS = {
    "gold": dict(base=(0.620, 0.360, 0.035), metallic=0.0, roughness=0.26,
                 coat=1.0, coat_rough=0.06),
    "red": dict(base=(0.520, 0.020, 0.018), metallic=0.0, roughness=0.26,
                coat=1.0, coat_rough=0.06),
    "yellow": dict(base=(0.760, 0.520, 0.010), metallic=0.0, roughness=0.26,
                   coat=1.0, coat_rough=0.06),
    "black": dict(base=(0.014, 0.014, 0.015), metallic=0.0, roughness=0.30,
                  coat=1.0, coat_rough=0.06),
    "silver": dict(base=(0.420, 0.425, 0.430), metallic=0.8, roughness=0.32),
}


# ------------------------------------------------------------------ helpers
def mat(name):
    """A material with exactly one Principled BSDF wired to the output."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            nt.nodes.remove(n)
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf


ALIAS = {
    "base": "Base Color", "metallic": "Metallic", "roughness": "Roughness",
    "coat": "Coat Weight", "coat_rough": "Coat Roughness", "ior": "IOR",
    "coat_ior": "Coat IOR", "coat_tint": "Coat Tint",
    "transmission": "Transmission Weight", "emission": "Emission Color",
    "emission_strength": "Emission Strength", "alpha": "Alpha",
    "specular": "Specular IOR Level", "aniso": "Anisotropic",
    "sheen": "Sheen Weight",
}


def set_inputs(bsdf, **kw):
    """Set Principled inputs by short name (ALIAS) or by socket name."""
    for k, v in kw.items():
        key = ALIAS.get(k, k)
        if key not in bsdf.inputs:
            continue
        sock = bsdf.inputs[key]
        if isinstance(v, (tuple, list)) and len(v) == 3:
            sock.default_value = (v[0], v[1], v[2], 1.0)
        else:
            sock.default_value = v


def flake(m, nt, bsdf, scale=2600.0, bump=0.04, metal_max=0.09):
    """Metallic flake, driven into the BASE layer.

    One Voronoi in OBJECT space (cell size fixed in metres regardless of UVs)
    drives a fine normal perturbation and a sparse metallic mask. The ramp is
    CONSTANT so only the brightest ~6 % of cells go metallic - that sparseness
    reads as flake rather than as shimmer.
    """
    coord = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.inputs["Scale"].default_value = scale
    if "Randomness" in vor.inputs:
        vor.inputs["Randomness"].default_value = 1.0
    nt.links.new(coord.outputs["Object"], vor.inputs["Vector"])

    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = 0.00002
    nt.links.new(vor.outputs["Color"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.94
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = metal_max
    nt.links.new(ramp.outputs["Color"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Metallic"])
    return m


def orange_peel(m, nt, bsdf, scale=260.0, strength=0.05, dist=0.00004):
    """Clear-coat orange peel, into the COAT normal.

    Cured clearcoat ripples on a 3-5 mm cell with an amplitude of microns;
    without it a reflected strip light is a razor-straight line and the panel
    reads as moulded plastic. Get the scale right: 1.1 mm cells with a 1.2 mm
    bump behaved like a very rough coat and smeared every softbox reflection.
    """
    if "Coat Normal" not in bsdf.inputs:
        return m
    coord = nt.nodes.new('ShaderNodeTexCoord')
    tex = nt.nodes.new('ShaderNodeTexNoise')
    try:
        tex.noise_dimensions = '4D'
    except Exception:
        pass
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 2.0
    tex.inputs["Roughness"].default_value = 0.42
    nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.inputs["Strength"].default_value = strength
    bmp.inputs["Distance"].default_value = dist
    nt.links.new(tex.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Coat Normal"])
    return m


def paint_material(spec):
    """Body paint from a PAINTS entry: dielectric colour coat + clearcoat
    (+ flake) (+ orange peel)."""
    m, nt, b = mat(spec["name"])
    # Base specular nearly off: the clearcoat does the reflecting; a specular
    # lobe on the pigment underneath lays a white sheen over every lit panel.
    set_inputs(b, base=spec["base"], metallic=0.0, roughness=spec["roughness"],
               ior=1.45, specular=spec["specular"], coat=1.0,
               coat_rough=spec["coat_rough"], coat_ior=1.5, coat_tint=(1.0, 1.0, 1.0),
               sheen=0.0, aniso=0.0)
    if spec.get("flake"):
        flake(m, nt, b, **spec["flake"])
    if spec.get("peel"):
        orange_peel(m, nt, b, strength=spec["peel"])
    return m


# ------------------------------------------------------------------ library
def build_library(paint="xiaomi_yellow", rim="gloss_black", caliper="gold",
                  lights_on=False, overrides=None, carbon_uv_scale=21.0,
                  tail_lights=0.0):
    """Every role's material. `paint` is a PAINTS key or a PAINTS-style dict.

    tail_lights: emission strength of the tail-lamp pipes (0 = off).
    overrides: {role: {input: value}} applied last, for one-off changes.
    """
    lib = {}
    lib["paint"] = paint_material(PAINTS[paint] if isinstance(paint, str) else paint)

    # gloss black: roofs, mirror caps, DLO surrounds, light-bar panels
    m, nt, b = mat("M_Black_Gloss")
    set_inputs(b, base=(0.013, 0.013, 0.014), metallic=0.0, roughness=0.09,
               coat=1.0, coat_rough=0.03, ior=1.45)
    orange_peel(m, nt, b, strength=0.04)
    lib["black_gloss"] = m

    # satin black: meshes, arch liners, trims. The gloss-vs-satin contrast is
    # what separates the aero from the body.
    m, nt, b = mat("M_Black_Satin")
    set_inputs(b, base=(0.016, 0.016, 0.017), metallic=0.0, roughness=0.42, coat=0.0)
    lib["grille"] = m

    m, nt, b = mat("M_Stripe_Silver")
    set_inputs(b, base=(0.215, 0.222, 0.236), metallic=0.0, roughness=0.34,
               coat=1.0, coat_rough=0.05)
    orange_peel(m, nt, b, strength=0.10)
    lib["stripe"] = m

    # carbon: baked 2x2 twill, ~3 mm per tow on world-space UVs
    m, nt, b = mat("M_Carbon")
    set_inputs(b, base=(0.021, 0.021, 0.023), metallic=0.0, roughness=0.28,
               coat=1.0, coat_rough=0.085, ior=1.5)
    try:
        from . import textures
        textures.apply_carbon(m, uv_scale=carbon_uv_scale)
    except Exception as e:
        print("carbon weave bake skipped:", e)
    lib["carbon"] = m

    # glazing: green-biased, heavily tinted, real transmission (see export_safe)
    m, nt, b = mat("M_Glass")
    set_inputs(b, base=(0.021, 0.026, 0.018), metallic=0.0, roughness=0.030,
               transmission=0.92, ior=1.52, coat=0.0)
    lib["glass"] = m

    m, nt, b = mat("M_Glass_Privacy")
    set_inputs(b, base=(0.010, 0.013, 0.009), metallic=0.0, roughness=0.038,
               transmission=0.62, ior=1.52, coat=0.0)
    lib["glass_dark"] = m

    # ---- lamps
    m, nt, b = mat("M_Lamp_Cover")
    set_inputs(b, base=(0.050, 0.050, 0.055), metallic=0.0, roughness=0.035,
               transmission=0.85, ior=1.52, coat=1.0, coat_rough=0.02)
    lib["lens"] = m

    m, nt, b = mat("M_Lamp_Housing")
    set_inputs(b, base=(0.008, 0.008, 0.009), metallic=0.0, roughness=0.30)
    lib["lamp_housing"] = m

    # a dark satin surround, not chrome: metal projector rims caught the key
    # light and read as white donuts in every close-up
    m, nt, b = mat("M_Lamp_Reflector")
    set_inputs(b, base=(0.035, 0.036, 0.040), metallic=0.0, roughness=0.35)
    lib["lamp_bowl"] = m

    # ~4000 K warm white. Lamps are OFF by default, as in reference photographs:
    # unlit, a DRL guide is a pale milky strip and a tail pipe deep red.
    m, nt, b = mat("M_LED_White")
    set_inputs(b, base=(0.92, 0.88, 0.76) if lights_on else (0.46, 0.46, 0.46),
               emission=(1.00, 0.94, 0.80), emission_strength=6.0 if lights_on else 0.0,
               roughness=0.20 if lights_on else 0.32)
    lib["led_white"] = m

    m, nt, b = mat("M_LED_Red")
    set_inputs(b, base=(0.42, 0.030, 0.022) if lights_on else (0.110, 0.006, 0.005),
               emission=(1.0, 0.055, 0.035), emission_strength=22.0 if lights_on else 0.0,
               roughness=0.20 if lights_on else 0.12)
    lib["led_red"] = m

    # Tail-lamp light pipes at position-light level, on independently of the
    # headlamps: in most rear photographs the tails are lit and the car reads
    # by them. tail_lights=0 turns them off.
    m, nt, b = mat("M_LED_Red_Tail")
    set_inputs(b, base=(0.42, 0.030, 0.022) if tail_lights else (0.110, 0.006, 0.005),
               emission=(1.0, 0.022, 0.012), emission_strength=float(tail_lights),
               roughness=0.20)
    lib["led_red_tail"] = m

    # Retro-reflectors: deep red prismatic plastic - they return light, they
    # do not emit it.
    m, nt, b = mat("M_Reflector_Red")
    set_inputs(b, base=(0.30, 0.012, 0.010), metallic=0.0, roughness=0.16,
               coat=1.0, coat_rough=0.04)
    lib["reflector"] = m

    # smoked lamp glass over a black mask; opaque on purpose (paint behind it)
    m, nt, b = mat("M_Lamp_Smoked")
    set_inputs(b, base=(0.008, 0.008, 0.009), metallic=0.0, roughness=0.10,
               specular=0.45, coat=1.0, coat_rough=0.03, ior=1.52)
    lib["lamp_smoked"] = m

    m, nt, b = mat("M_Plate_White")
    set_inputs(b, base=(0.80, 0.80, 0.79), metallic=0.0, roughness=0.32,
               coat=0.6, coat_rough=0.08)
    lib["plate"] = m

    m, nt, b = mat("M_Text_Dark")
    set_inputs(b, base=(0.020, 0.020, 0.022), metallic=0.0, roughness=0.30)
    lib["text_dark"] = m

    # ---- wheels and brakes
    m, nt, b = mat("M_Rim_Black" if rim == "gloss_black" else "M_Rim_" + rim.title().replace("_", ""))
    set_inputs(b, **RIMS[rim])
    lib["rim"] = m

    m, nt, b = mat("M_Rim_Pinstripe")
    set_inputs(b, base=(0.780, 0.520, 0.005), metallic=0.0, roughness=0.20,
               coat=1.0, coat_rough=0.04)
    lib["rim_lip"] = m

    m, nt, b = mat("M_Rim_Machined")
    set_inputs(b, base=(0.55, 0.56, 0.58), metallic=1.0, roughness=0.14, aniso=0.35)
    lib["chrome"] = m

    # carbon-ceramic: a dark matte composite, emphatically not polished steel
    m, nt, b = mat("M_Disc_CCB")
    set_inputs(b, base=(0.070, 0.068, 0.066), metallic=0.0, roughness=0.50)
    lib["disc"] = m

    m, nt, b = mat("M_Caliper_" + caliper.title())
    set_inputs(b, **CALIPERS[caliper])
    lib["caliper"] = m

    # tyre rubber: warm dark grey, no sheen (a sheen lobe made whitewalls)
    m, nt, b = mat("M_Tyre")
    set_inputs(b, base=(0.014, 0.013, 0.012), metallic=0.0, roughness=0.84,
               sheen=0.0, specular=0.10)
    lib["rubber"] = m

    # shadow shell behind every gap: no specular at all, or it fills in
    m, nt, b = mat("M_Shadow")
    set_inputs(b, base=(0.018, 0.018, 0.019), metallic=0.0, roughness=0.92,
               specular=0.0, coat=0.0)
    lib["shadow"] = m

    m, nt, b = mat("M_Interior_Base")
    set_inputs(b, base=(0.030, 0.030, 0.032), metallic=0.0, roughness=0.55)
    lib["interior"] = m

    # Mirror glass: silvered glass is a dim, cool mirror, not polished metal.
    # On the machined-rim chrome the door mirrors read, from the driver's
    # seat, as two bright discs mirroring the web viewer's white room.
    m, nt, b = mat("M_Mirror_Glass")
    set_inputs(b, base=(0.20, 0.21, 0.22), metallic=1.0, roughness=0.03)
    lib["mirror_glass"] = m

    for role, kw in (overrides or {}).items():
        b = next(n for n in lib[role].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        set_inputs(b, **kw)
    return lib


def export_safe():
    """Convert transmissive materials to an opaque approximation for glTF,
    and procedural metallic (the paint flake) to a plain value.

    KHR_materials_transmission blanks the whole frame in three.js. The
    replacement is dark tinted glass with a moderate clear reflection, set to
    absolute values: brightened glass mirrored the web viewer's white room
    across every window and the greenhouse read grey-white.
    """
    safe = {
        "M_Glass": (0.018, 0.022, 0.016),
        "M_Glass_Privacy": (0.009, 0.011, 0.008),
        "M_Lamp_Cover": (0.030, 0.030, 0.033),
    }
    changed = []
    for name, base in safe.items():
        m = bpy.data.materials.get(name)
        if m is None or not m.use_nodes:
            continue
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b is None:
            continue
        set_inputs(b, base=base, transmission=0.0, specular=0.35, roughness=0.04,
                   metallic=0.0, coat=0.0, coat_rough=0.02)
        changed.append(name)
    print("export_safe: transmission cleared on", changed)
    # A procedural Metallic (the flake mask) cannot be exported: the glTF
    # exporter then omits metallicFactor, which glTF reads as 1.0, and three.js
    # showed the RX's flaked paint as solid dark metal. The mask is ~6 % of
    # cells at metal_max, a mean of under 0.01: ship the paint's dielectric 0.
    flaked = []
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        sock = b.inputs.get("Metallic") if b else None
        if sock is None or not sock.is_linked:
            continue
        if any(l.from_node.type == 'TEX_IMAGE' for l in sock.links):
            continue
        for l in list(sock.links):
            m.node_tree.links.remove(l)
        sock.default_value = 0.0
        flaked.append(m.name)
    if flaked:
        print("export_safe: procedural metallic set to 0 on", flaked)
    # glTF sheen has no weight, only a colour, and the exporter writes the
    # Sheen Tint alone: the RX's lilac sheen at weight 0.28 shipped at full
    # strength and three.js painted the whole car pastel lavender. Fold the
    # weight into the tint.
    sheened = []
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        w = b.inputs.get("Sheen Weight") if b else None
        t = b.inputs.get("Sheen Tint") if b else None
        if w is None or t is None or w.is_linked or t.is_linked:
            continue
        if 0.0 < w.default_value < 1.0:
            k = w.default_value
            c = t.default_value
            t.default_value = (c[0] * k, c[1] * k, c[2] * k, c[3])
            w.default_value = 1.0
            sheened.append(m.name)
    if sheened:
        print("export_safe: sheen weight folded into the tint on", sheened)
    return changed + flaked + sheened
