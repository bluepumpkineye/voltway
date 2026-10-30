# Silhouette comparison: the model against a level side picture

When a car "looks wrong" to the eye (an SUV that reads as an estate), measure it before moving anything.

1. Find a level, long-lens side picture of the real car: the maker's configurator render (the Nio ES8's is
   `blender/reference/nio-es8/official/color_white.jpg`) or a studio photograph from far away. Check it: the wheels must be
   round, and the wheelbase and the height, scaled from the wheels' published outer diameter, must come out at the published
   figures to 1 %. A photograph shot close up is in perspective and cannot be read this way (the near side is magnified).
2. Read its outline:

       node scripts/silhouette/side-silhouette.cjs side.jpg <px per metre> <front axle px> <ground px> > real.txt

3. Read the shipped model's outline in the same frame and lay the two tables side by side (`paste real.txt model.txt`):

       node scripts/silhouette/glb-silhouette.cjs public/models/<car>.glb > model.txt

   For a quick look at a build that is not exported yet, a Blender script can print the same two tables from the evaluated meshes
   (the ES8's `es8_probe.py` did: build, then max z per 0.1 m of x and min/max x per 0.05 m of z).
4. Change the profile curves (`*_surface.py`: `Z_ROOF`, `Z_SHOULDER`, the nose caps) until the tables agree, then the stations that
   hang on them (door cuts, belt, pillars, hood, frunk). Overlay a metric grid on the picture to read those off (the ES8's
   `es8_grid.cjs`: a grid every 0.25 m of x and 0.1 m of z in the build frame, lines every 0.5 m and 0.2 m heavy).

Finding that justified this folder: the ES8's tail agreed with its render to 1 cm and its nose stood 0.25 m too far forward (the
build had the published 5280 mm length; the render, whose wheelbase and height match the published 3130 and 1800 mm, is 5.05 m
long), its hood was 8 to 10 cm low, its windscreen 39 degrees against 31 with its base 0.12 m too far forward, its roof flat and
5 to 10 cm too high over the front seats, and its beltline 8 cm low: a tall band of glass over a shallow body.
