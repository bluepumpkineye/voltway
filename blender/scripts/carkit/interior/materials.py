"""Interior trim materials: leather, Alcantara, carbon, metals, carpet, thread.

What makes a cabin read as photographed rather than modelled is almost
entirely the TRIM: each material's surface structure under a soft light.

    Nappa leather   a dielectric with a low clearcoat and a pebbled grain
                    normal map; roughness ~0.40 so seams and bolsters catch
                    a soft highlight
    Alcantara       very rough (0.9+) with a strong SHEEN lobe - the velvety
                    grazing-angle glow is the whole look (KHR_materials_sheen
                    in glTF) - and a fine fibre normal map
    carbon          the baked 2x2 twill under a full clearcoat
    brushed metal   metallic with a streak normal map; chrome is a mirror
    carpet          black, near-Lambertian, loop-pile normal map
    thread          stitching is geometry (see stitch.py) in its own colour

All maps come from carkit.surfacemaps (tileable pixels) and are sampled with
world-space UVs in metres (carkit.build.ensure_uvs(force_all=True)), scaled by
1 / TILE, so a 1.5 mm grain is 1.5 mm on every part.

    lib = build_library(accent=ACCENTS["xiaomi_yellow"])
"""
from .. import materials as MB
from .. import surfacemaps as SM

# accent leather colours (linear RGB), back-solved from reference photographs
ACCENTS = {
    # SU7 Ultra Nappa. Lit, the press render reads sRGB ~165/137/57: a golden
    # yellow with real blue in it - at blue 0.018 it rendered orange-mustard.
    "xiaomi_yellow": (0.480, 0.330, 0.058),
    "tan": (0.300, 0.150, 0.060),
    "red": (0.330, 0.020, 0.018),
    "white": (0.620, 0.600, 0.560),
    "grey": (0.110, 0.110, 0.115),
}


def _textured(nt, bsdf, img, tile, strength=1.0, socket="Normal"):
    """UV -> Mapping (1 / tile) -> image -> Normal Map -> the BSDF socket."""
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    k = 1.0 / tile
    mp.inputs["Scale"].default_value = (k, k, k)
    nt.links.new(coord.outputs["UV"], mp.inputs["Vector"])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Linear'
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs[socket])
    return tex


def leather(name, color, maps, roughness=0.40, coat=0.12, strength=1.0):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=roughness, specular=0.5,
                  coat=coat, coat_rough=0.25, ior=1.45, sheen=0.0)
    _textured(nt, b, maps["leather"], SM.TILE["leather"], strength)
    return m


def alcantara(name, color, maps, sheen=0.85, sheen_rough=0.45, tint=(0.40, 0.42, 0.48),
              strength=1.0):
    m, nt, b = MB.mat(name)
    MB.set_inputs(b, base=color, metallic=0.0, roughness=0.94, specular=0.25,
                  coat=0.0, sheen=sheen)
    MB.set_inputs(b, **{"Sheen Roughness": sheen_rough})
    MB.set_inputs(b, **{"Sheen Tint": tint})
    _textured(nt, b, maps["alcantara"], SM.TILE["alcantara"], strength)
    return m


def build_library(accent=ACCENTS["xiaomi_yellow"], maps=None, carbon=None,
                  stitch=None):
    """Every interior role. `carbon`: an existing carbon material to reuse."""
    maps = maps or SM.build_all()
    lib = {}
    lib["leather_accent"] = leather("INT_Leather_Accent", accent, maps)
    lib["leather_black"] = leather("INT_Leather_Black", (0.014, 0.014, 0.015), maps,
                                   roughness=0.42)
    lib["alcantara"] = alcantara("INT_Alcantara", (0.0105, 0.0105, 0.0115), maps)
    lib["headliner"] = alcantara("INT_Headliner", (0.016, 0.016, 0.018), maps,
                                 sheen=0.6)

    m, nt, b = MB.mat("INT_Thread_Accent")
    MB.set_inputs(b, base=stitch or tuple(c * 1.15 for c in accent), metallic=0.0,
                  roughness=0.55, sheen=0.3)
    lib["thread_accent"] = m
    m, nt, b = MB.mat("INT_Thread_Grey")
    MB.set_inputs(b, base=(0.12, 0.12, 0.12), metallic=0.0, roughness=0.6)
    lib["thread_grey"] = m

    m, nt, b = MB.mat("INT_Satin_Black")          # moulded trim, switch bezels
    MB.set_inputs(b, base=(0.018, 0.018, 0.020), metallic=0.0, roughness=0.52,
                  specular=0.4)
    lib["satin"] = m
    m, nt, b = MB.mat("INT_Piano_Black")
    MB.set_inputs(b, base=(0.008, 0.008, 0.009), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.5)
    lib["piano"] = m
    m, nt, b = MB.mat("INT_Chrome")
    MB.set_inputs(b, base=(0.90, 0.90, 0.91), metallic=1.0, roughness=0.07)
    lib["chrome"] = m
    m, nt, b = MB.mat("INT_Brushed")
    MB.set_inputs(b, base=(0.72, 0.72, 0.74), metallic=1.0, roughness=0.26)
    _textured(nt, b, maps["brushed"], SM.TILE["brushed"], 0.8)
    lib["brushed"] = m
    m, nt, b = MB.mat("INT_Gunmetal")
    MB.set_inputs(b, base=(0.20, 0.20, 0.21), metallic=1.0, roughness=0.32)
    lib["gunmetal"] = m
    # black loop pile is not black paint: the press render's floor reads
    # sRGB ~11 where 0.016 gave 2-3 through the matched camera
    m, nt, b = MB.mat("INT_Carpet")
    MB.set_inputs(b, base=(0.034, 0.034, 0.036), metallic=0.0, roughness=0.96,
                  specular=0.2, sheen=0.4)
    _textured(nt, b, maps["carpet"], SM.TILE["carpet"], 1.0)
    lib["carpet"] = m
    m, nt, b = MB.mat("INT_Rubber")
    MB.set_inputs(b, base=(0.012, 0.012, 0.012), metallic=0.0, roughness=0.8)
    lib["rubber"] = m
    m, nt, b = MB.mat("INT_Speaker")
    MB.set_inputs(b, base=(0.02, 0.02, 0.022), metallic=0.3, roughness=0.5)
    _textured(nt, b, maps["perforation"], SM.TILE["perforation"], 1.0)
    lib["speaker"] = m
    m, nt, b = MB.mat("INT_Button_Red")
    MB.set_inputs(b, base=(0.50, 0.025, 0.018), metallic=0.0, roughness=0.25,
                  coat=1.0, coat_rough=0.05)
    lib["button_red"] = m
    m, nt, b = MB.mat("INT_Screen_Glass")         # a display that is off
    MB.set_inputs(b, base=(0.004, 0.004, 0.005), metallic=0.0, roughness=0.03,
                  coat=1.0, coat_rough=0.01, ior=1.5)
    lib["screen_glass"] = m
    m, nt, b = MB.mat("INT_Webbing")              # seat belts
    MB.set_inputs(b, base=(0.02, 0.02, 0.022), metallic=0.0, roughness=0.7, sheen=0.5)
    lib["webbing"] = m
    m, nt, b = MB.mat("INT_Tag_Orange")           # seat-belt buckle tags
    MB.set_inputs(b, base=(0.60, 0.12, 0.01), metallic=0.0, roughness=0.5)
    lib["tag"] = m
    # Ambient light guides. Dark and inert here: the web app finds every
    # material with "ambient" in its name and drives its emission from the
    # HMI (colour, brightness, on/off).
    m, nt, b = MB.mat("INT_Ambient")
    MB.set_inputs(b, base=(0.05, 0.05, 0.055), metallic=0.0, roughness=0.3)
    lib["ambient"] = m
    if carbon is not None:
        lib["carbon"] = carbon
    return lib
