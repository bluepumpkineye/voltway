"""Material library for BYD Seal 07 EV: carkit's library in BYD Ocean factory finishes.

Signature hero colour: Sky Purple (天空紫, swatch #C6BED8), the signature pearlescent
lavender-violet hero launch colour of the 2026/2027 BYD Seal 07 EV (c53_0001..0013),
paired with Atlantis Grey (亚特兰蒂斯灰, swatch #465462, c1_0001..0016),
Whale Shark Grey (鲸鲨灰), and Snow White (雪域白) in the showroom configurator.
Metallic is capped at 0.19 to respect the export quality gate (metallic <= 0.20).
"""
from carkit import materials as _M

LIGHTS_ON = False
TAIL_LIGHTS = 1.3

# Arctic Blue (北冰蓝): the Seal's signature blue-grey. Read from the maker's studio photograph (the
# owner's first reference): body mid-tones sRGB (81,103,123), light panels (120,145,173), shade (55,71,86)
# - a dusty steel blue with a cool pearl, NOT a sky blue. The base is the mid-tone over the viewer's
# ~1.35x brightening: viewer door median read (110,127,145) from (60,82,104) so the base went to
# sRGB (48,71,97) = #304761 -> linear below (target viewer median ~ (88,110,134)).
SEAL_ARCTIC_BLUE = dict(
    name="M_Paint_Seal_Blue",
    base=(0.0296, 0.0630, 0.1195),
    roughness=0.30,
    specular=0.25,
    coat_rough=0.04,
    peel=0.008,
    flake=None,
)
PAINT_METALLIC = 0.16            # strictly under the export gate's 0.20 ceiling
PAINT_COAT = 0.55
SHEEN = dict(weight=0.05, tint=(0.62, 0.76, 0.92), roughness=0.30)

_M.CALIPERS.setdefault("seal_silver", dict(
    base=(0.48, 0.50, 0.54),
    metallic=0.80,
    roughness=0.26,
    coat=0.8,
    coat_rough=0.08,
))
_M.RIMS.setdefault("seal_aero_alloy", dict(
    base=(0.80, 0.81, 0.84),
    metallic=0.92,
    roughness=0.18,
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


def build_library():
    # SEAL_PAINT_GAIN: the dashboard's car pictures are rendered in Blender's studio rig, which is about
    # 1.5x darker than the web viewer's light on the same base colour; they are shot with the gain set
    import os
    gain = float(os.environ.get("SEAL_PAINT_GAIN", "1.0"))
    paint = dict(SEAL_ARCTIC_BLUE)
    paint["base"] = tuple(min(1.0, c * gain) for c in SEAL_ARCTIC_BLUE["base"])
    lib = _M.build_library(
        paint=paint,
        rim="seal_aero_alloy",
        caliper="seal_silver",
        lights_on=LIGHTS_ON,
        tail_lights=TAIL_LIGHTS,
    )
    _sheen(lib["paint"])
    pb = next(n for n in lib["paint"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    _M.set_inputs(pb, metallic=PAINT_METALLIC, coat=PAINT_COAT)

    # Front lamp smoked crystal lens (deep glossy dark housing lens so projectors & DRLs pop crisply)
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.014, 0.016, 0.020), metallic=0.0, roughness=0.04,
                  coat=1.0, coat_rough=0.015, ior=1.52, specular=0.65)
    lib["lamp_clear"] = m

    # Tail lamp deep smoked ruby lens
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.012, 0.0025, 0.004), metallic=0.0, roughness=0.04,
                  coat=1.0, coat_rough=0.015, ior=1.52, specular=0.65)
    lib["lamp_red_lens"] = m

    # Ocean double-U front DRL & projector emission
    m, nt, b = _M.mat("M_LED_White")
    _M.set_inputs(b, base=(0.95, 0.97, 1.00), metallic=0.0, roughness=0.12,
                  emission=(0.95, 0.97, 1.00), emission_strength=1.6)
    lib["led_white"] = m

    # Ocean water-drop matrix through-type tail light LED emission
    m, nt, b = _M.mat("M_LED_Red")
    _M.set_inputs(b, base=(0.90, 0.02, 0.03), metallic=0.0, roughness=0.12,
                  emission=(0.95, 0.02, 0.03), emission_strength=1.5)
    lib["led_red"] = m

    # Bright anodized chrome / satin silver trim (window surround, tail lamp bisecting bar, chin accent)
    m, nt, b = _M.mat("M_Trim_Chrome")
    _M.set_inputs(b, base=(0.86, 0.87, 0.90), metallic=0.95, roughness=0.12)
    lib["trim_chrome"] = m

    # Machined alloy face (18-inch 5-petal aero wheel bright face)
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.84, 0.85, 0.87), metallic=1.0, roughness=0.16)
    lib["machined"] = m

    # Satin silver wheel blade finish & center cap
    m, nt, b = _M.mat("M_Wheel_Silver")
    _M.set_inputs(b, base=(0.56, 0.58, 0.62), metallic=0.95, roughness=0.22)
    lib["wheel_silver"] = m
    m, nt, b = _M.mat("M_Wheel_Cap")
    _M.set_inputs(b, base=(0.04, 0.04, 0.05), metallic=0.2, roughness=0.20, coat=0.8, coat_rough=0.06)
    lib["wheel_cap"] = m

    # Gloss black body trim (fender camera blade, B-pillar, side air curtains, lower grille slats, aero wheel inserts)
    m, nt, b = _M.mat("M_Black_Gloss")
    _M.set_inputs(b, base=(0.010, 0.010, 0.012), metallic=0.0, roughness=0.10,
                  coat=1.0, coat_rough=0.03)
    lib["black_gloss"] = m

    # Matte/satin black bumper & diffuser trim
    m, nt, b = _M.mat("M_Cap_Black")
    _M.set_inputs(b, base=(0.012, 0.012, 0.014), metallic=0.0, roughness=0.32, specular=0.30)
    lib["cap_black"] = m

    # BYD logo chrome
    m, nt, b = _M.mat("M_Logo_Chrome")
    _M.set_inputs(b, base=(0.89, 0.90, 0.93), metallic=1.0, roughness=0.10)
    lib["logo_chrome"] = m

    # Brake discs
    m, nt, b = _M.mat("M_Disc_Iron")
    _M.set_inputs(b, base=(0.140, 0.120, 0.105), metallic=0.1, roughness=0.52)
    lib["iron"] = m

    # Wheel arch cladding & underbody liner
    m, nt, b = _M.mat("M_Cladding")
    _M.set_inputs(b, base=(0.018, 0.019, 0.022), metallic=0.0, roughness=0.50, specular=0.30)
    lib["cladding"] = m

    # Ceramic frit border behind glass
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07, specular=0.30, coat=0.0)
    lib["frit"] = m

    # License plate white
    m, nt, b = _M.mat("M_License_Plate_White")
    _M.set_inputs(b, base=(0.92, 0.93, 0.95), metallic=0.0, roughness=0.35, specular=0.35)
    lib["plate_white"] = m

    # Satin black plastic trim (lower intakes, aprons, rocker strips, bumper blacks)
    m, nt, b = _M.mat("M_Black_Trim")
    _M.set_inputs(b, base=(0.012, 0.012, 0.013), metallic=0.0, roughness=0.30, coat=0.0)
    lib["black_trim"] = m

    # Convenient aliases for parts
    lib["tail_lamp"] = lib["led_red"]
    lib["lamp_red"] = lib["led_red"]
    lib["reflector_red"] = lib["lamp_red_lens"]
    lib["brake_disc"] = lib["iron"]
    lib["brake_caliper"] = lib.get("caliper") or lib["trim_chrome"]

    return lib


GLASS_SAFE = {
    "M_Glass": (0.015, 0.018, 0.024),
    "M_Glass_Privacy": (0.007, 0.009, 0.012),
}


def export_safe():
    """carkit's export_safe, then BYD Seal glass tints."""
    _M.export_safe()
    import bpy
    for name, base in GLASS_SAFE.items():
        m = bpy.data.materials.get(name)
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
        if b is not None:
            _M.set_inputs(b, base=base)
