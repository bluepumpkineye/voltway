# Reading the Voyah Passion S's front end off the studio photograph

How `blender/scripts/vps_lampdata.py` was made (2026-11-03). The reference photographs are local only
(`blender/reference/voyah-passion-s`, not in git); the build needs only the generated data module.

Run in Blender, `blender -b --factory-startup --python gen_vps_lampdata.py` (it borrows `lampseg.py` from
`../a06t_lamp_trace`). Source: `exterior/c1_0002.jpg`, 3840 x 2880, through `vps_cam.FRONT_CAM` (1.1 mm per pixel); the
photograph's LEFT half (the car's right) is read, the centre line is u = 1920.

- Traced (luminance threshold, pixel-exact boundary chains, Gaussian-smoothed, resampled): the lamp's outline (`LAMP_OUT`,
  dark closed with `closing r=4`, cut at the seam u 1408 where the channel starts), the channel's edges (`CH_TOP/CH_BOT`, per
  column), the cheek-and-grille recess (`CHEEK_OUT`, the biggest dark component below the nose, up to the centre line), the
  emblem (`EMB_*`: the dark loop is the shield, its holes the white blades, clipped at the centre line), the intake body
  (`BULK`: the recess right of a hand-read curve).
- Read by hand from 3-8x gridded crops (a labelled grid over the photograph): the DRL line, the smoked panel, the two bezels,
  the slat, the fin, the round cover.

Lessons: (1) a per-column "brightest pixel" ridge follows the LED rows, not the hairline: read the line by hand. (2) Check every
trace by drawing it over the photograph before building from it. (3) The pale paint against black parts is the easiest threshold
there is: trace shapes, do not read them. (4) A hole in the dark mask is a lit part (the emblem's blades).
