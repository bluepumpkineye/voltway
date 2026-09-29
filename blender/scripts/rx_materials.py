"""Material library for the Luxeed RX: carkit's library in the RX's finishes.

The show car in the Autohome studio photographs (front34_blue, the
collage) is a colour-shift paint: deep royal blue where the surface faces
the camera (the nose, sRGB ~40/60/200), violet to lilac as it turns away
(the flanks and the hood top). Built glTF-safe as a blue colour coat with a
violet SHEEN lobe - sheen is strongest at grazing angles, which is where
the photographs go purple - under the clearcoat, with a fine flake.
KHR_materials_sheen carries it to three.js.

Wheels: machined-face 5-spoke over dark grey; orange calipers.
"""
from carkit import materials as _M
from carkit.materials import export_safe      # noqa: F401  (re-exported)

LIGHTS_ON = False
TAIL_LIGHTS = 1.3

RX_BLUE = dict(name="M_Paint_RX_ShiftBlue", base=(0.040, 0.025, 0.185),
               roughness=0.30, specular=0.18, coat_rough=0.030, peel=0.012,
               flake=dict(scale=2600.0, bump=0.035, metal_max=0.10))
# Patches off front34_blue (sRGB): nose face 69/56/151, rear door 104/88/140,
# door highlight 148/133/173 - red above green everywhere, i.e. violet, not
# the royal blue the first base gave (render 53/57/128). The base is a deep
# blue-violet; a lilac sheen of moderate weight lifts the flanks. Stronger
# or broader sheen (0.85 / 0.6) washed the car pastel lavender. In the
# lookdev rig a saturated base (0.030/0.015/0.270) put the doors at 58/30/179
# (photo 104/88/140): the base is desaturated towards the photo's pearl,
# and kept dark - lighter, the rig's big highlights read pastel lavender.
SHEEN = dict(weight=0.28, tint=(0.72, 0.52, 1.0), roughness=0.35)

_M.CALIPERS.setdefault("orange", dict(base=(0.780, 0.160, 0.012), metallic=0.0,
                                      roughness=0.26, coat=1.0, coat_rough=0.06))
_M.RIMS.setdefault("dark_grey", dict(base=(0.040, 0.041, 0.044), metallic=0.0,
                                     roughness=0.30, coat=1.0, coat_rough=0.06))


def _sheen(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, val in (("Sheen Weight", SHEEN["weight"]),
                     ("Sheen Tint", SHEEN["tint"] + (1.0,)),
                     ("Sheen Roughness", SHEEN["roughness"])):
        if key in b.inputs:
            b.inputs[key].default_value = val
    return m


def build_library():
    lib = _M.build_library(paint=RX_BLUE, rim="dark_grey", caliper="orange",
                           lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
    _sheen(lib["paint"])
    # The RX's headlamps read light grey through a clear lens (front34_blue):
    # a satin silver reflector field, not the SU7's smoked black.
    m, nt, b = _M.mat("M_Lamp_Clear")
    _M.set_inputs(b, base=(0.085, 0.088, 0.095), metallic=0.55, roughness=0.26,
                  coat=1.0, coat_rough=0.02, ior=1.52)
    lib["lamp_clear"] = m
    # tail-lamp lens: deep red smoked glass over the lit pipes (rear photo:
    # dark wine red where the pipes do not show)
    m, nt, b = _M.mat("M_Lamp_RedLens")
    _M.set_inputs(b, base=(0.090, 0.004, 0.006), metallic=0.0, roughness=0.06,
                  coat=1.0, coat_rough=0.02, ior=1.52, specular=0.5)
    lib["lamp_red_lens"] = m
    # the grey pods in the rear bumper: satin grey, a shade darker than the
    # grey car's paint (rear photo)
    m, nt, b = _M.mat("M_Pod_Grey")
    _M.set_inputs(b, base=(0.100, 0.104, 0.110), metallic=0.3, roughness=0.32,
                  coat=0.5, coat_rough=0.10)
    lib["pod"] = m
    # the black band across the rear glass's top: ceramic frit behind the
    # glass, so glass-smooth - one reflection, no clearcoat (a gloss black's
    # coat mirrored the web studio's ceiling grey). Matte, once the rear top
    # was crowned it read as a rubber mat laid over the glass.
    m, nt, b = _M.mat("M_Frit_Black")
    _M.set_inputs(b, base=(0.003, 0.003, 0.004), metallic=0.0, roughness=0.07,
                  specular=0.30, coat=0.0)
    lib["frit"] = m
    # the radar box in the lower grille: charcoal plastic, a shade lighter
    # than the gloss frame round it (front_silver)
    m, nt, b = _M.mat("M_Radar_Grey")
    _M.set_inputs(b, base=(0.035, 0.036, 0.038), metallic=0.0, roughness=0.40)
    lib["radar"] = m
    # the wheels' machined faces and lip ring: bright satin aluminium
    m, nt, b = _M.mat("M_Alu_Machined")
    _M.set_inputs(b, base=(0.78, 0.78, 0.80), metallic=1.0, roughness=0.20)
    lib["machined"] = m
    return lib
