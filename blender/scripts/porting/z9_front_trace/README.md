# The Denza Z9's front end: the loop (2026-11-19)

How `z9_front.py` / `z9_frontdata.py` were made and how to iterate on them. The reference photographs are local only
(`blender/reference/denza-z9/exterior`, not in git). Method and lessons: docs/3d-pipeline.md, "The Denza Z9's front end and rear plate".

All outputs go to `$Z9DEV` (default `blender/renders/z9_dev`, git-ignored). Blender 5.2, always in a BACKGROUND instance.

1. Full build once (2 min): `blender -b --factory-startup --python dev_build.py` -> `z9_full.blend`.
2. Fast loop (about 25 s): `blender -b z9_full.blend --python dev_front.py` removes the front end's objects, rebuilds them with the
   current `z9_front` (it reloads the modules) and saves `z9_front.blend`. A new object name prefix must be added to `PREFIX`.
3. Stills: `blender -b z9_front.blend --python dev_render.py -- front,f34l,lamp,pocket,low a1 keep 1400 32`
   (views from `CAMS`, a tag, paint `keep|black|white|grey`, width, samples). `front` is the photograph's own camera.
4. Over the photograph: `blender -b z9_front.blend --python dev_overlay.py -- a1` -> `blender/renders/match/front_black_a1_overlay.png`
   (the model's panel lines in cyan, its outline in magenta). The nose is drawn with the principal point shifted 17 px (see `UC`).
5. Reading a photograph: `node scripts/photo-tools/gridcrop-clahe.cjs photo.jpg out.png x y w h outW clahe 25 [overlay.json]`.
   Check a read outline by drawing it (overlay.json) before building from it.

Not here: the export. `export_z9.web()` writes the GLB twice to the same path (plain, then Draco); set `export_z9.DEST` and
`DEST_SHADOW` to a scratch folder first and copy the result, or a locked file in `public/models` ends the run with an 18 MB GLB.
