"""Material library for XPeng G9L: carkit's library in the G9L's factory finishes.

The flagship model in the Autohome studio photographs (blender/reference/xpeng-g9l)
is painted Provence Purple (普罗旺斯紫): a deep blue-violet (the photographed panels read 44,43,72 to 48,40,88 sRGB
in the studio's mid-tones against the violet backdrop, lavender in the highlights; the first guess, #4E2C3C, was
wine-red).
Metallic is capped at 0.19 to respect the export quality gate (metallic <= 0.20).
"""
from carkit import materials as _M

LIGHTS_ON = False
TAIL_LIGHTS = 1.3

# Provence Purple (普罗旺斯紫): sRGB #271E45, tuned in the showroom viewer, which brightens a paint
# about 1.5x over its base colour (the photographed mid-tones are 44,43,72 to 48,40,88)
# In linear RGB space: (0.0203, 0.0130, 0.0595)
G9L_PURPLE = dict(
    name="M_Paint_G9L_Purple",
    base=(0.0203, 0.0130, 0.0595),
    roughness=0.38,
    specular=0.25,
    coat_rough=0.05,
    peel=0.008,
    flake=None,
)
PAINT_METALLIC = 0.19            # strictly under the export gate's 0.20 ceiling
PAINT_COAT = 0.40
SHEEN = dict(weight=0.02, tint=(0.60, 0.55, 0.95), roughness=0.30)

_M.CALIPERS.setdefault("gunmetal", dict(
    base=(0.20, 0.21, 0.22),
    metallic=0.75,
    roughness=0.28,
    coat=0.8,
    coat_rough=0.08,
))
_M.RIMS.setdefault("aero_two_tone", dict(
    base=(0.020, 0.021, 0.024),
    metallic=0.0,
    roughness=0.20,
    coat=1.0,
    coat_rough=0.04,
))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def _bar_film_png():
    """A 1024 x 64 rainbow smear: pale silver with soft violet / teal / amber blobs, like the unlit
    light guide in c1_0026 (blender/textures/g9l_bar_film.png, regenerated each build)."""
    import os
    import numpy as np
    import bpy
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(here, "..", "textures", "g9l_bar_film.png"))
    w, h = 1024, 64
    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]
    rng = np.random.default_rng(9)
    base = np.array([0.60, 0.62, 0.66])
    img = np.ones((h, w, 3)) * base
    # wide hue bands drifting along the bar, stronger toward the ends
    for c, (cx, wd, col) in enumerate((
            (0.08, 0.05, (0.78, 0.42, 0.62)), (0.17, 0.05, (0.36, 0.52, 0.78)), (0.30, 0.07, (0.84, 0.70, 0.40)),
            (0.43, 0.05, (0.40, 0.66, 0.74)), (0.56, 0.06, (0.62, 0.40, 0.78)), (0.68, 0.05, (0.84, 0.72, 0.42)),
            (0.80, 0.06, (0.36, 0.56, 0.78)), (0.92, 0.05, (0.78, 0.44, 0.62)))):
        g = np.exp(-((x - cx) / wd) ** 2) * (0.35 + 0.65 * np.exp(-((y - 0.55) / 0.35) ** 2))
        img = img * (1 - 0.30 * g[..., None]) + np.array(col) * 0.30 * g[..., None]     # the photographs' film is a pale silver with soft tints
    # a dark lower third (the light guide's shadow side) and a pale highlight line near the top
    img *= (1.0 - 0.45 * np.clip((y - 0.55) / 0.45, 0, 1))[..., None]
    img += 0.14 * np.exp(-((y - 0.16) / 0.05) ** 2)[..., None]
    img += rng.normal(0, 0.01, img.shape)
    img = np.clip(img, 0, 1)
    im = bpy.data.images.new("g9l_bar_film", w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = img
    im.pixels.foreach_set(rgba[::-1].reshape(-1))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    return path


def _bar_film():
    import bpy
    path = _bar_film_png()
    m, nt, b = _M.mat("M_Bar_Film")
    _M.set_inputs(b, base=(0.8, 0.82, 0.86), metallic=0.0, roughness=0.14, coat=1.0, coat_rough=0.03)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    return m


def build_library():
    lib = _M.build_library(
        paint=G9L_PURPLE,
        rim="aero_two_tone",
        caliper="gunmetal",
        lights_on=LIGHTS_ON,
        tail_lights=TAIL_LIGHTS,
    )
    _sheen(lib["paint"])
    pb = next(n for n in lib["paint"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    _M.set_inputs(pb, metallic=PAINT_METALLIC, coat=PAINT_COAT)

    # Front lamp clear outer lens: the photographs show a smoky grey cover over a lit reflector, not a black pane (c1_0026: the lens
    # reads 60-90 sRGB against 25 for the black plastic around it)
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.050, 0.054, 0.064), metallic=0.0, roughness=0.12,
                  coat=0.8, coat_rough=0.03, ior=1.52, specular=0.5)
    lib["lamp_clear"] = m

    # The turbine wheel's black arms: painted black, but not a mirror: in the white studio the glossy black arms reflected the floor and
    # one read as polished chrome (c1_0043/0053: the arms are dark with a soft sheen)
    m, nt, b = _M.mat("M_Wheel_Black")
    _M.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.30, specular=0.30, coat=0.25, coat_rough=0.16)
    lib["wheel_black"] = m

    # Recessed black panels (the front grille's rows, the rear bumper's panel and vents): a hair lighter and rougher than the
    # satin trim around them, so their edges read without turning them grey (the first cladding-grey version read as a tray)
    m, nt, b = _M.mat("M_Black_Panel")
    _M.set_inputs(b, base=(0.0095, 0.0095, 0.0115), metallic=0.0, roughness=0.36, specular=0.20, coat=0.0)
    lib["black_panel"] = m

    # Tail lamp red lens
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.100, 0.003, 0.005), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m

    # Full-width Robot Face continuous LED light strip
    m, nt, b = _M.mat("M_LED_White")
    _M.set_inputs(b, base=(0.95, 0.96, 1.00), metallic=0.0, roughness=0.15)
    lib["led_white"] = m

    # Robot Face light guide: the thin-film rainbow seen on the unlit bar in the photographs
    lib["bar_film"] = _bar_film()

    # Horizon full-width tail light bar LED emission
    m, nt, b = _M.mat("M_LED_Red")
    _M.set_inputs(b, base=(1.00, 0.02, 0.02), metallic=0.0, roughness=0.15)
    lib["led_red"] = m

    # Chrome / Satin Silver trim (window frames, floating D-pillar blade)
    m, nt, b = _M.mat("M_Trim_Chrome")
    _M.set_inputs(b, base=(0.85, 0.86, 0.88), metallic=0.95, roughness=0.12)
    lib["trim_chrome"] = m

    # Machined alloy face (wheel spokes)
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.64, 0.65, 0.67), metallic=1.0, roughness=0.30)
    lib["machined"] = m

    # Gloss black body trim (lower aero chin, rocker blades, rear diffuser)
    m, nt, b = _M.mat("M_Black_Gloss")
    # (coat 1.0 / rough 0.10 mirrored the hall: the greenhouse underlay and the pillars showed white streaks like chrome)
    _M.set_inputs(b, base=(0.006, 0.006, 0.008), metallic=0.0, roughness=0.16, specular=0.30,
                  coat=0.45, coat_rough=0.06)
    lib["black_gloss"] = m

    # Wheel hub cap & XPeng logo
    m, nt, b = _M.mat("M_Cap_Black")
    _M.set_inputs(b, base=(0.012, 0.012, 0.014), metallic=0.0, roughness=0.32, specular=0.30)
    lib["cap_black"] = m

    # Satin graphite aluminium (the rear diffuser's blade): chrome mirrors the white studio and read as a white slab; the photographs
    # show a mid-grey satin blade (c1_0030)
    m, nt, b = _M.mat("M_Diffuser_Satin")
    _M.set_inputs(b, base=(0.060, 0.062, 0.068), metallic=0.85, roughness=0.42, coat=0.0)
    lib["diffuser_satin"] = m

    m, nt, b = _M.mat("M_Logo_Chrome")
    _M.set_inputs(b, base=(0.88, 0.89, 0.92), metallic=1.0, roughness=0.10)
    lib["logo_chrome"] = m

    # Brake discs
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.052, 0.045, 0.040), metallic=0.12, roughness=0.55)
    lib["iron"] = m

    # Wheel arch cladding & underbody liner
    m, nt, b = _M.mat("M_Cladding")
    _M.set_inputs(b, base=(0.018, 0.019, 0.022), metallic=0.0, roughness=0.50, specular=0.30)
    lib["cladding"] = m

    # Ceramic frit border behind glass
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07, specular=0.30, coat=0.0)
    lib["frit"] = m

    # Black plastic trim (the lower intakes, aprons, rocker strips, bumper blacks): a soft satin black. A piano-black
    # (coat 1) panel facing the camera mirrors the studio's white room and reads mid-grey in the showroom (95 sRGB
    # against 60 for this); real trim is not a mirror either (c1_0002/c1_0034: dark, with a soft sheen).
    m, nt, b = _M.mat("M_Black_Trim")
    # the showroom's white hall lifted the satin (rough 0.30, specular 0.5) to sRGB 74-83 on the front apron; the photographs'
    # black plastic reads about 25-30: less specular and a rougher lobe, a darker base
    _M.set_inputs(b, base=(0.005, 0.005, 0.006), metallic=0.0, roughness=0.42, specular=0.14, coat=0.0)
    lib["black_trim"] = m

    return lib


GLASS_SAFE = {
    "M_Glass": (0.015, 0.018, 0.024),
    "M_Glass_Privacy": (0.007, 0.009, 0.012),
}


def export_safe():
    """carkit's export_safe, then G9L glass tints."""
    _M.export_safe()
    import bpy
    for name, base in GLASS_SAFE.items():
        m = bpy.data.materials.get(name)
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
        if b is not None:
            _M.set_inputs(b, base=base)
