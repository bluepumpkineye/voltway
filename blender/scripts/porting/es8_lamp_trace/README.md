# Reading the Nio ES8's headlamp off the front photograph

How `blender/scripts/es8_lampdata.py` was made (2026-11-03). The reference photographs are local only
(`blender/reference/nio-es8/official`, not in git); everything the build needs is the generated data module and the solved
camera in `es8_ref_match.py`.

Run in Blender, `blender -b --factory-startup --python gen_es8_lampdata.py` (it borrows `lampseg.py` from
`../a06t_lamp_trace`).

**What is traced and what is read by hand.** The DRL's lens (the whole lit outline), its two dashes and its two bars are
traced from `ext_front.jpg` (luminance threshold, closing to fill the crystal's speckle, pixel-exact boundary chains,
Gaussian-smoothed 2.4-2.8 px, split at the divider u 926-934). The pod, its two bezels, the chrome sill and the vent are
hand readings of 7x crops with a labelled grid (the dark glass has no edge a threshold finds; good to about 1 px = 2 mm).

**The camera** (`es8_ref_match.py`) is a long lens 16 m from the nose, f 7805 px, 1.61 m up, 2.4 degrees down. A head-on
photograph fixes the horizontal and vertical scale at the nose, not the lens' distance; the scale came from the body's
widest section (0.996 m a side) and the nose's own landmarks on the centre line, the height from the windscreen's base.
Check it by projecting the model's vertices onto the photograph (scratch script: the objects' vertices as coloured dots
over a gridded crop): emblem, face-panel edges, plate and chin blade land within 10 px = 2 cm.

**Lessons.** (1) The ES8's first DRL was four short strips, 0.14 m too far inboard and 0.1 m too high, because it had been
placed by eye from a 3/4 photo. The real one is ONE lens, two frosted dashes with a bar lit along each lower edge and a
thin divider, and it runs right round the hood's corner. (2) The photo's rays do not all land on a sheet: a ray through a
shut line's gap, or just outside a sheet's edge (this nose's corner turns up to 2 cm earlier than the real car's), takes
the nearest surface point; pull it inboard only for the outline a boolean cuts along (a cut on a sheet's very edge tears it).
(3) Parts laid on a smoothed corner must take their surface from the SMOOTHED panels (the BVH is built after
`smooth_corner`), not from the analytic cap. (4) Parts inside an opening must stand IN the opening, not on its far wall:
the vent's lighter slab pierced the tunnel's tapered wall until it was inset.
