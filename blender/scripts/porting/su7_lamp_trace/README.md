# Reading the SU7 Ultra's headlamp and hood edge off the maker's head-on photograph

How `blender/scripts/su7_lampdata.py` and the front camera `head_on` (`ref_match.py`) were made (2026-11-03). The reference
photographs are local only (`blender/reference/xiaomi-su7-ultra/lights/cat53/big_023.jpg`, not in git); the build needs only
the generated data module.

Run in Blender, `blender -b --factory-startup --python gen_su7_lampdata.py` (it borrows `lampseg.py` from
`../a06t_lamp_trace`). Source: `big_023.jpg`, 1600 x 1200, the yellow car square-on from the front. The photograph's LEFT half
is the car's RIGHT; the left lamp (u 403..556) is read and the build mirrors the rays onto the half sheet (y >= 0).

**Camera `head_on`**: f 3860 px (about 100 mm in 35 mm terms), 8.3 m from the nose (x 2.4), 1.16 m up, tipped 2.55 degrees
down, on the centre line. A long lens' distance is not fixed by the picture, so it was solved from what is: the fender
silhouette (0.995 m a side) for the scale, the corner blades' bottoms and the hood's crown for height and pitch. Check = project
the built panels' vertices over the photograph (`su7_dots`-style dots over a gridded crop): the fender outline and the blades land
within 2-3 px (5 mm) at the nose's depth.

- Traced (R - B < 0.22 against the saturated yellow paint, closed r=3, the loop that holds the lamp's centre, Gaussian-smoothed
  1.6 px, resampled every 4 px): the almond outline `LAMP_OUT`.
- Read by hand from a 9x gridded crop (the DRL is on in this photograph): `DRL_UP/DRL_LO` (the bar's two edges), `SILVER` (the grey
  reflector above the bar), `MODULES` (three projector centres + radii).
- The hood's front edge (`su7_panels.HOOD_ARC_PX`) is read the same way from a 4x crop of the thin black shut line; it is cast onto
  the upper-fascia sheet by the photo's own rays (`su7_panels.hood_arc_path`) and cut as a 4.2 mm slot. Cast onto the finished body
  it gave the 3D arc used for `Y_HOOD` (x 1.42 y 0.78; x 2.24 y 0.60; across the nose at z 0.641).

Lessons: (1) a long-lens head-on photograph puts the lamp's outline inside 1 cm of where the model has it once the camera is
checked by dots; read the lamp from this picture, not from the 3/4 photographs. (2) The cap's `wv_at(y, z)` is unreliable on the nose's
top (z is not monotone in v above the join ring's crown): lay a line there by photo rays onto the sheet's own BVH. (3) A lamp
that is lit in the photograph shows its DRL bar plainly: read the bar, not the glow (the glow is ~3 px wider each side).
