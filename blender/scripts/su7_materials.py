"""Material library for the SU7 Ultra: carkit's library in the SU7's finishes.

Launch yellow (solid, no flake), gloss black forged wheels with a gold
pinstripe, gold Akebono calipers. Every value is back-solved from the
reference photography under the studio rig; see carkit/materials.py for the
roles and the rules behind them.
"""
from carkit import materials as _M
from carkit.materials import export_safe      # noqa: F401  (re-exported)

# Headlamps are OFF by default, as in every front reference photograph; the
# tail lamps' light pipes are ON at position-light level, as in the rear ones.
LIGHTS_ON = False
TAIL_LIGHTS = 1.3


def build_library():
    return _M.build_library(paint="xiaomi_yellow", rim="gloss_black", caliper="gold",
                            lights_on=LIGHTS_ON, tail_lights=TAIL_LIGHTS)
