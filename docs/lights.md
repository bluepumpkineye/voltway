# The car's lamps: LED light, and the Dashboard tab that switches it

The showroom lights the LED lines the cars are built with, at both ends, and takes the room to dusk so the
light has something to shine against. The lamps are switched from the car's own screen (the Dashboard
tab shows it live beside the car, and the Interior tab has it in the cabin), from the Dashboard tab's
dock, or by link. Everything here is **our rendering of a lit lamp, calibrated against the maker's lit
photographs, never the maker's footage**, and the tab's note says so.

## 1. What the visitor does

| Control | Where | What it does |
|---------|-------|--------------|
| Headlamp switch: Off, Position, Low beam, Auto | the car's screen (HarmonyOS: the bottom bar's lamp button, Vehicle control, Settings > Lights; HyperOS: the headlight on the car at the centre of its home screen, Settings > Lights; ZEEKR OS: Lights on the home screen), and the Dashboard dock | `Auto` is the car deciding for itself: the showroom is dim by design, so it lights the low beam |
| High beam | Dashboard dock | rides on the low beam (asking for it from off lights both); reaches further and narrows |
| Brake lights | Dashboard dock, hold | come on with the pedal, lamps or no lamps |
| Front / Rear | Dashboard dock | which end of the car the camera looks at (`dashFront`, `dashRear` in `src/lib/showroom/anchors.ts`) |

State is the link: `?tab=dashboard&lights=low&high=1&view=rear` (`lights` is `off|position|low|auto` and
rides on every tab, because the Interior tab's screen can set it too).

## 2. How it is built

```
store flags                lampTargets()          LightsRig             what reads the levels
lightMode, highBeam,  -->  levels to head for --> levels as drawn  -->  lamp materials, glow quads,
braking                    (src/lib/lights.ts)    (ramped, 6 numbers)   floor patches, the dusk
```

`src/lib/lights.ts` has no three.js in it, so its numbers are checkable on their own. A level is 0..1:

| Level | Off | Position | Low / Auto | High | Brake |
|-------|-----|----------|------------|------|-------|
| `front` (LED line) | 0 | 0.45 | 0.8 | 1 | |
| `projector` (lenses) | 0 | 0 | 0.8 | 1 | |
| `beam` / `reach` (floor) | 0 | 0 | 0.7 / 7 m | 1 / 12 m | |
| `rear` (tail) | 0 | 0.5 | 0.5 | 0.5 | 1 |
| `night` (the room) | 0 | 0.3 | 0.85 | 1 | unchanged |

`LightsRig` eases each level toward its goal with its own time constant, and an LED coming on stutters up
in a few tens of milliseconds (`wake()`), the tail lamps a beat after the front. It says whether
anything is still moving, so the demand canvas asks for frames only while it is: **an idle showroom,
lamps on or off, draws nothing**. `prefers-reduced-motion` snaps. A link that opens with the lamps on
shows them on at once.

`src/components/viewer/Lights.tsx` draws the levels, with no post-processing:

- **The LED materials** (found by material name) drive their emissive strength. An unlit rear lamp or
  projector is the build exactly (its own emissive colour and strength, tone-mapped like the car); the front
  LED's off state is the showroom's (a faint white, never tone-mapped).
- **The glow**: camera-facing quads, drawn additively after the car, at points thinned out of the lamp's
  own triangles (vertices and points along edges, merged into 12 mm cells). They are children of the lamp
  mesh, so a tailgate that swings takes its glow with it. Each is a tight bloom and a wider halo, blended
  in the framebuffer as display values, pulled 2 cm toward the camera so a lens in front of the LED does
  not hide it. The red lamps keep a red core (a saturated red driven hard rolls toward pink).
- **The floor**: the headlamps' beam ahead of the nose (two lobes, toed out, longer and narrower for the
  high beam) and the tail lamps' red wash behind the car, as additive patches in the car's own group, so
  a car that drives (the Tech tab) takes its light with it.
- **Dusk** (`useDusk`): the studio's walls, floor, rings and background, the Tech tab's asphalt, the
  city's photo and sun, and the image-based light the paint reflects, scale down with `night`. The
  dimming is worked out as it looks, then taken back to linear values.

Everything above lives on `LIGHT_LAYER` (2), which the view camera sees and ContactShadows' depth pass and
the floor mirror do not. All of it has raycasting switched off (a glow quad is a unit square at the mesh's
origin until the shader moves it), and the glow's bounding box is the real extent of its points.

**Why not a bloom pass.** Tried in design, rejected: an `EffectComposer` renders into a linear
half-float target, which changes how the sRGB-space glass blends, the studio's `toneMapped = false`
whites, and the exposure of the Neutral tone mapping (a visible pop on swapping the composer in). The
glow above stays in the same pass as everything else.

## 3. Per car

A car's export names its lit parts alike (docs/3d-pipeline.md, "Names the web app relies on"), so a car
needs no data unless it differs. `Vehicle.lights` (`LightsSpec` in `schema.ts`) overrides the material, the
colours and the strengths per lamp.

| Car | Front | Projector | Rear |
|-----|-------|-----------|------|
| Xiaomi SU7 Ultra | `M_LED_White`: the lightsaber lines | none | `M_LED_Red_Tail`: the bar and the end blocks (the lid's part follows the lid) |
| Luxeed RX | `M_LED_White`: the line and its dots | `M_Lamp_Reflector` (`projector: {}`): the two lenses, lit with the low beam | `M_LED_Red_Tail` |
| Zeekr 7X | `M_LED_White`: the twin bars | none | `M_Lamp_RedLens`, dark as built (`off: 0`): the tail is one red lens bar with no LED under it, so the lens is the lit part |

**No whole-lamp emission.** Only the light pipes emit; the housings, lenses and reflectors around them stay
inert, which is what stops a lamp reading as a glowing blob. The 7X's red lens is a 4 cm bar, not a lamp
body.

**Not modelled, so not lit:** the RX's blue upper lamp bar as seen in the maker's lit photographs, the 7X's
dotted matrix pattern (its bars light as plain lines), and the amber turn-signal lamps (there is no amber
material in any build). Add them to the build from approved reference photos first; then they are data.

## 4. The Dashboard tab

`src/components/showroom/Dashboard.tsx`. On a wide window (1024 px and up) the car's screen (`CarScreen`:
the live HMI in its bezel, scaled by `Fit`) stands in a column at the right and the camera frames the car
in what is left (`deviceInset`, which the Tech tab's devices use too); a line of guidance under the screen
says where the lamp control is on this car's screen. On a window of 700 px and up that is narrower, the
screen opens as a sheet over the car from the dock's "Car screen"; on a phone the dock's own lamp switch is
the control (the screen would be unreadable at that size).

**The camera is the exterior's.** The visitor orbits the car itself, with the exterior tabs' limits: the
orbit's centre is the middle of the car, and the car is placed in the free part of the window by sliding the
picture (a view offset, `AnchorPose.shiftFrac`, the way `liftPx` lifts it above the dock), not by moving the
target off the car. So a drag turns the car in place and it never swings behind the screen; zooming can come
as close to a lamp as on a tab with no device (the limit is worked out without the device's inset); and the
lift and the slide follow the window as it is, so a screen that comes or goes (the window crossing 1024 px)
re-centres the car even if it has been turned. The dock's Front and Rear fly to `dashFront` / `dashRear`
(asking for the end the camera is already at flies back to it: `anchorTick`), and follow the camera when the
visitor turns it past the side view (`syncLightsView`, on the controls' `rest`), so the lit chip is the end
on screen and the address says `view=rear`.

## 5. Checking and tuning

- `node` can run the ramp checks: the lamps' numbers have no three.js in them (a scratch test of 32
  checks was used: targets, the wake-up curve, settling, a long frame, the emissive maths).
- In development `window.__lights` holds the live knobs (`size`, `bias`, `peakW`, `peakT`, `beam`, `wash`,
  `dusk`, `envDim`) and the rig; change one, then `__viewer.invalidate()` (or, with the pane hidden,
  `__viewer.advance(performance.now())`).
- Calibrated against the maker's lit photographs of each car (Autohome's official galleries, kept out of
  the repo with the other reference photos): a crisp thin white DRL with a small bloom, a red tail bar
  with a hot centre and a tight halo, soft light pools on the floor.
- Idle frames stay at 0 with the lamps on or off; the floor mirror does not draw the glow.

## 6. Adding a car's lamps

1. The export's lit parts are materials of their own, named as above (or say otherwise in `lights`).
2. Look at the maker's lit photographs: where the light is, how crisp, what colour.
3. Switch the lamps on in the Dashboard tab and compare front and rear; tune `size`/`peakT` from the
   console if the lamp's geometry is thicker or thinner than the default.
