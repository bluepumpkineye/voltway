import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from eval_blender import eval_code

code = """
import sys, os, time
p = r'c:\\Users\\User\\Documents\\4 - Website_ WebApp Project\\Chinese EV Configurator\\blender\\scripts'
if p not in sys.path:
    sys.path.insert(0, p)

for mod in list(sys.modules):
    if mod.startswith('seal_') or mod in ('build_seal', 'export_seal', 'cabin_parts', 'cabin_tools'):
        del sys.modules[mod]

import export_seal, cabin_tools as CT, seal_cabin as C, build_seal

# 1. Export exterior
t0 = time.time()
res_ext = export_seal.web(draco=True)
print(f"EXTERIOR EXPORT: {res_ext} in {time.time()-t0:.1f}s")

# 2. Export interior
t1 = time.time()
build_seal.main(reset=True, scene=True)
import seal_interior_shell as SH
SH.main()
export_seal.prepare_exterior()
CT.cabin_screens(C.CFG)
res_cab = CT.export_interior(C.CFG, draco=True, look='direct')
print(f"CABIN EXPORT: {res_cab} in {time.time()-t1:.1f}s")

# 3. Render verification views
exec(open(r'c:\\Users\\User\\Documents\\4 - Website_ WebApp Project\\Chinese EV Configurator\\blender\\scripts\\render_verify_views.py').read())
print("MASTER_BUILD_SUCCESS")
"""

print("Executing master build, export, and render in Blender...")
res = eval_code(code, timeout=600)
print("Response from Blender:")
print(json.dumps(res, indent=2))
