# Tracing the 06T's headlamp from a photograph

How `blender/scripts/a06t_lampdata.py` was made (2026-11-03). The reference photographs are local only
(`blender/reference/avatr-06t`, not in git); everything the build needs is the generated data module.

Run each in Blender, `blender -b --factory-startup --python <script>`, with `A06T_TRACE_DIR` naming a scratch folder
the scripts exchange json through. Order:

1. `seg2.py`          dark-glass contours (the whole "7", the slit) in the close-up `details/c12_0011.jpg` and in `exterior/c1_0002.jpg`
                      (pixel-exact boundary chains of a thresholded, opened mask: `lampseg.py`) -> `loops2.json`
2. `icp_cam.py`       the close-up's camera, solved by fitting the model's own lamp outlines (3D, from c1_0002 through
                      `a06t_front._on_paint`) onto the close-up's contours (iterated closest points + `refmatch.solve_camera`):
                      the turntable camera 16 m away, f 59879 px, yawed 2.8 degrees; median 3 px = 0.7 mm -> `cam_c12_0011_icp.json`
3. `extract_lamp.py`  simplified silhouette and slit (spurs removed) and the stem's outer edge -> `lamp_data.json`
4. `gen_lampdata.py`  adds the light-guide strip (the silhouette's chain offset inward: 44 px from the edge, a width read off
                      luminance profiles across the arm: black band 40 px, lens, lower band 28-70 px; 34 px along the stem)
                      and writes `blender/scripts/a06t_lampdata.py`

The pocket's insides (separators, units, slats, LED line) are hand readings of brightened crops, in `a06t_cam.POCKET_*`.

Lessons: (1) threshold the dark glass, open it by a few pixels, trace the boundary chain; never hand-read an outline off a
crop (the first version was 3-5 px out everywhere). (2) A thin dark line along a paint edge joins the contour as a spur: cut
dead ends where the chain comes back within 3.5 px of itself (`remove_spurs`). (3) A 4.6x close-up from the same turntable
camera has almost no perspective: solve it from contours, not from a few hand-picked points (rms 17 px -> 6 px, median 3).
(4) Offsetting a curve inward by more than its corner radius makes loops: round the path first (gen_lampdata: `gsmooth`).
