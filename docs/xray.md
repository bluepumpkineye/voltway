# The X-ray tab and the Drive tab's live motors

The X-ray tab shows a model of every car's underlying hardware: a slider from **Solid** (`0`) to **X-ray** (`1`), labels on every part, a card with what the part does, and a short clip of it working. The same hardware is reused by the Drive tab (camera "X-ray"), where each motor's rotor and windings light up with the torque it is delivering.

All 9 vehicles in the showcase (`xiaomi-su7-ultra`, `byd-seal`, `denza-z9`, `luxeed-rx`, `zeekr-7x`, `xpeng-g9l`, `avatr-06t`, `nio-es8`, `voyah-passion-s`) ship with a tailored anatomy GLB (`public/models/<slug>-xray.glb`) and sourced `xray.anatomy` part definitions. (`Exploded` mode and `Blueprint` mode have been decommissioned so all parts remain in their anatomical positions inside the ghosted body shell.)

## 0. Honesty rules (they decide how everything below is written)

- **The shapes are ours.** No maker publishes the geometry of a cell block or a wishbone. Every part card says "a modelled view, not the
  maker's drawing", and the card's picture is a render of our model, never a maker photo.
- **Every figure has a basis.** Each part carries `basis`: `published` (the maker's own figure), `reported` (a credible outlet, named in the
  card's source line) or `illustrative` ("Our drawing": no figure is claimed). A label never states more than its basis.
- **The clips are procedural 3D animation, not footage.** The rotor spins up while three phases chase round the stator; the pack's cells
  light in a wave; a wheel rides a bump on a solved linkage; the rack turns the wheels. They say what they show in a caption.
- No part, system or number is added because it looks plausible. The SU7 Ultra's list is in `src/data/vehicles/xiaomi-su7-ultra.ts`
  (`xray.anatomy.parts`, 18 parts, each with its source).

Facts the SU7 anatomy rests on, and where they come from: motors front 288 kW / 500 N·m, rear two of 425 kW / 635 N·m (850 kW / 1,270 N·m
together), V8s up to 27,200 rpm and V6s 21,000 rpm (Xiaomi, via CarNewsChina's database and Gasgoo); a SiC control module (Gasgoo); the
CATL Qilin 2.0 pack, 93.7 kWh, 5.2C, 16C peak (CarNewsChina, electrive); double-wishbone front, multi-link rear, air springs with
electronically controlled dampers (CarNewsChina, EVKX); carbon-ceramic discs 430 x 40 front / 410 x 32 rear (CarNewsChina); tyres 265/35
R21 and 305/30 R21; the 9,100 t Hyper Die-Casting press behind the rear casting (Gasgoo).

## 1. What the visitor gets

| Where | What |
| --- | --- |
| X-ray tab, slider | 0 Solid, 1 X-ray (the paint fades to a ghost, the hardware shows through), 2 Exploded (the shell lifts away, the doors, bonnet and tail open out, the wheels move out, then the hardware flies apart in a staggered order). A click on a stop flies there; dragging scrubs. |
| System chips | All, Battery, Motors, Chassis, Suspension, Steering, Brakes and wheels. A system picked stays lit, the rest dims; the camera goes to it. |
| Labels | Two columns of pills with leader lines, ordered by height and pushed apart so none overlap (wide windows only, 760 px and up). A pill picks the part. |
| Click in the 3D view | Picks the part under the pointer (the same as a pill or a list row). |
| Part card | A render of our model, the part's text, its figures with their basis, the source link, and a clip with Play/Stop and a live caption. At the right of a wide window; a sheet over the lower 42% of a narrow one (the car is framed above it, the labels step aside). |
| Blueprint | The G-buffer pass of section 6 plus a thin frame and a title block with the published dimensions. Works on every car. |
| Drive tab, every camera but the driver's seat | The car stays solid; as each performance card opens, the paint goes to a ghost for a few seconds and the parts the card is about light up (the rotors for the power and motors cards, the pack for the energy card), then the car is solid again (section 9). |
| Drive tab, camera "X-ray" | The always see-through version: the shell is a ghost, each motor's rotor and windings glow with its share of the output, kW and share tags float at the motors, and the high-voltage cables pulse. Rear right at the launch run reads, for instance, 266 kW, 42%. |

## 2. Where things are

Blender (the parts library, reusable across cars): `blender/scripts/carkit/anatomy/`

| File | Holds |
| --- | --- |
| `spec.py` | `CarSpec`, `Motor`, `CarSpec.from_dims(...)`, `derive()`: a car is its hubs, tyre, floor and underbody heights, size, pack and motors. |
| `prim.py` | The mesh builder: box, cylinder, sphere, tube, general-profile `sweep`, lathe, prism with holes (and a `twist` for helical gears), torus, hex `bolt`, `sticker`, instancing (`append`), rounded paths; every face carries UVs in metres of surface. Material and group helpers, glTF axis conversion. |
| `detail.py` | Shared hardware: bolt rings and lines, hose clamps, barbed fittings, corrugated hoses, the round HV connector, the label atlas rectangles. |
| `texgen.py` | The procedural, tileable PBR texture families (numpy): cast and brushed aluminium, forged, steel, laminations, copper strands, printed cell wrap, rubber, plastic, cable sheath, polyimide film, circuit boards, stickers. |
| `materials.py` | The `XR_*` material library: each a texture family plus a tint and a tile size; `tmat()` builds the node tree the glTF exporter understands. |
| `ao.py` | The baked ambient-occlusion atlas (one 2048 image, a second UV set, every part baked alone): section 10. |
| `battery.py` | Tray (gasket, flange, bolts), cold plate with a rounded serpentine channel, 12 blocks of individual cells, busbars, flex circuits and BMS boards, bolted ribbed lid with vent, valve and labels, junction box (PDU) and the rear HV port. |
| `motor.py` | Casing (jacket rings, ribs, bolted flanges, hoses and clamps), stator with hairpin crowns in three phase materials, rotor with V-magnets, bearings and a resolver ring, reducer with helical gears, inverter with its HV connector. One motor across the axle (`side=None`) or one per wheel. |
| `frames.py` | Floor (multi-chamber extrusions), front subframe (cast plate with pockets), rear casting (ribs, honeycomb, bosses), crash beams with crush cans, spring towers (ribs, flange, locknut). |
| `suspension.py` | Double-wishbone and multi-link corners (forged I-section arms, bushes with through-bolts, boots and castle nuts, knuckle with hub flange, damper with reservoir and cable, bellows), half-shafts, anti-roll bar, steering rack with assist motor; the hardpoints go in the corner group's `kin` extra. |
| `build.py` | `build(spec)` assembles the `XR_ANATOMY` collection; `explode_plan` writes each node's offset and flight window; `export_glb(path)` writes the Draco GLB with extras. The plan scales with the wheelbase (k = wheelbase/3). |
| `render.py` | Transparent EEVEE stills of a part, for the cards. |

Per car: `su7_anatomy.py` (its `CarSpec`, measured off the shipped exterior), `su7_anatomy_renders.py` (the 16 card shots), `zx_anatomy.py`
(the Zeekr 7X, built from its measured hubs to prove the parts rescale; **not wired to the web**), and `su7_anatomy_export.py`, the headless
entry: `blender -b --factory-startup --python blender/scripts/su7_anatomy_export.py -- [--out PATH] [--ao] [--cards] [--blend PATH]`
builds, optionally bakes the AO atlas, writes the GLB (default `public/models/su7-ultra-xray.glb`) and the card stills. The build is
about 15 s without `--ao`.

Web: `src/lib/xray/` (no React)

| File | Holds |
| --- | --- |
| `rig.ts` | `XrayRig`: the one animated number `level` (0..2), the movers and their windows, clips state, the Drive tab's live motors. `xrayOf(vehicle)`. |
| `plan.ts` | How the car's own parts (shell, doors, bonnet, tail, wheels, cabin) come apart, derived from the car's size and the shared node names, so a new car needs no list. |
| `fx.ts` | `AnatomyFx`: the clips, the dimming, the Drive tab's glow; per-mesh materials; remembers rest poses so a stopped clip restores exactly. |
| `wishbone.ts` | The linkage solver (Newton for the upper arm, bisection for the lower); checked by `scripts/xray-tools/wishbone-test.mjs`. |
| `clips.ts` | The clip list (`rotor`, `battery`, `suspension`, `steering`), lengths and captions. |
| `labels.ts` | Pure label layout. |

`src/components/viewer/`: `XrayDirector.tsx` (drives the rig from the store, the focus camera, the Drive tab's live lights and tags, the
cable harness, click-to-pick), `XrayLabelDriver.tsx` (projects the labels each frame), `Blueprint.tsx` (the drawing pass), `xrayGhost.ts`
(the ghost's shader patch), `Xray.tsx` (the legacy ghost kept for cars without an anatomy), `CarModel.tsx` and `Openings.tsx` (honour the rig).
`src/components/showroom/Xray.tsx` (dock, part list and card, blueprint sheet) and `XrayLabels.tsx` (the DOM pills).
Store: `xrayLevel`, `xrayScrub`, `xraySystem`, `xrayPart`, `xrayBlueprint` in `src/store/vehicle-store.ts`.
Camera: anchor `xrayWide` (used from level 1.5) in `src/lib/showroom/anchors.ts`.

## 3. The anatomy GLB and its extras

`public/models/su7-ultra-xray.glb` (Draco, about 1 MB class; fetched when the page is quiet so the tab opens on it). Every node's extras
carry JSON strings, because Blender's custom properties do not serialise arrays:

- `xr`: `{ sys, id, ex, t0, t1 }`. `sys` is battery, drive, chassis, suspension or steering; `ex` the flight offset in glTF axes, metres,
  relative to the node's **parent** (so a group's offset carries its parts); `t0`..`t1` the window of the exploded phase it flies in.
- `kin` on a corner group: the hardpoints `LF LR LBJ UF UR UBJ H TI TO SB ST` for the linkage solver. `aim` on a link: its two ends.
- `ports`: the HV connectors the cables join.

Blender to glTF axes: (x, y, z) becomes (x, z, -y).

## 4. Adding a car

1. Measure the hubs off the car's shipped exterior (`node scripts/xray-tools/hubs.mjs public/models/<car>.glb` prints them in both axes).
2. Write `blender/scripts/<car>_anatomy.py` with a `CarSpec.from_dims(...)` (hubs, tyre, body size, kWh, motors; give the floor and the
   underbody heights if known, otherwise the SU7's proportions are used). Look at `zx_anatomy.py`.
3. In Blender: `import carkit.anatomy.build as B; B.build(spec); B.export_glb(".../public/models/<car>-xray.glb")`. Check the tree with
   `node scripts/glb-tree.mjs public/models/<car>-xray.glb --extras`.
4. Render the cards (`su7_anatomy_renders.py` as the pattern, `node scripts/xray-tools/render-cards.mjs blender/renders/xray public/xray/<car>`;
   `contact.mjs` makes a contact sheet to review them at once).
5. In `src/data/vehicles/<car>.ts` add `xray.anatomy` (`url`, `parts`, `note`, `lift`): for every part its `system`, `nodes`, `scene`
   (the camera's view), `text`, `facts`, `source`, `basis`, `clip` and `image`. **Only what you can source**; mark the rest `illustrative`.

The 7X, the RX and the others need their own labels and sources before they are wired; the motor and battery figures in `zx_anatomy.py`
are placeholders for the geometry only.

## 5. Clips

Each clip is `playClip(vehicle, id)` on the rig. While one plays, the system it works on is assembled in place (a linkage can only work as a
linkage), then comes apart again when it stops. `rotor`: the rotor spins up with the phases chasing round the stator. `battery`: cells charge
in a wave and the current runs the busbars to the junction box. `suspension`: a wheel travels on the solved wishbone, the spring and damper
aim from tower to arm, the exterior's wheel rises with the hub. `steering`: the rack slides, the tie rods swing the knuckles, the wheels
steer (the wheels' Y is owned by the steering, hence `keepY` on the wheel movers).

## 6. Blueprint mode

`Blueprint.tsx` takes over the canvas (a positive `useFrame` priority makes react-three-fiber stop drawing the scene) and draws it twice into
G-buffers with an override material: view normal, part id and depth, once for the hardware and cabin (layer 4), once for the shell (layer 5).
A full-screen pass turns them into the drawing: a paper field with a perspective floor grid, each part washed and cross-hatched at three
angles by how it faces the light, outlined where depth, normal or part id changes (Roberts cross on all three), the shell as faint
line work only so the hardware reads through it, and each system in its own ink. A system picked in the panel stays lit. Nothing of the
studio (floor, shadow, lamp glow) is in it. `window.__bp` (dev) exposes the uniforms (line weight `uThick`).

## 7. Checks and gotchas

- `node scripts/xray-tools/wishbone-test.mjs` (the solver closes its loops across the travel).
- Idle frames must be 0: the canvas is `frameloop="demand"` and the director asks for frames only while something moves
  (`gl.info.render.frame` must not advance at rest).
- **A hidden Browser pane drops the WebGL context** (and throttles timers): when testing in the desktop app, bring the preview pane to the
  front first, or you will chase a "context lost" that is not in the code. A Fast Refresh remount in dev can do the same; reload.
- Do not run `npm run build` in the repo while a dev server runs (they share `.next`); build in a copy.
- Shell commands over about 6 KB are silently truncated; write large files with the editor tool.
- `blender/renders/`, `.blend` files and the reference photos are gitignored; the card images that ship are `public/xray/su7-ultra/*.webp`
  (about 300 KB in all).

## 8. Not built, on purpose

- No wiring for the other cars (needs their own sourced labels).
- The exploded view is not shown on the phone-width layout's labels (a part is picked by tapping it in the view or in the card's list).
- The Drive tab has no Blueprint look.
- Parts are modelled for shape and proportion and, since 2026-11-11, with the *kind* of detail a real unit has (bolts, ribs, fins, boots,
  clamps, connectors, hairpin crowns, helical gears), not the maker's drawing: the fasteners, the cell can, the crush-can folds and the
  boards are ours and carry no figure. There is still no wiring beyond the HV harness, the flex strips and a damper's valve cable.

## 9. The Drive tab's lens

The Drive tab keeps the car solid and reveals the hardware behind the performance cards: `lensAt` (src/lib/tech/drive-beats.ts) says, from the
card plan and the playhead, which system is revealed and how far; the director (`XrayDirector.tsx`) turns that into the rig's level
(`rig.setLevel`, at most 0.88), the focus on the system, the parts' live lights (`AnatomyFx.live`, `liveBattery`) and a lift of the camera.
The hardware is on layer 3 there so that the floor's mirror does not draw it. The SU7's run is 20 s (`DriveSpec.runS`) so that every card has
its turn. The whole story, with the numbers, is in docs/tech-showcase.md section 21.

## 10. How the hardware looks: texture, detail, contact shading (2026-11-11)

The first version was flat: one colour per material, boxes and tubes, no UVs. The look now comes from four layers, all made in
Blender and shipped in the one GLB (about 4 MB; the textures are WebP, `EXT_texture_webp`).

1. **Real detail in the geometry** (`battery.py`, `motor.py`, `suspension.py`, `frames.py`, with the shared hardware in `detail.py`).
   Every system carries what the real unit has: the pack's tray gasket and about 70 flange bolts, 216 individual cells (printed wrap,
   shoulder, two terminals, a vent, foam between cells, end plates, straps), copper busbars with nuts and braids, sensing flex strips and
   BMS boards, a ribbed bolted lid with a burst vent, a breather valve, stickers and a hazard strip; motor casings with jacket rings,
   axial ribs, bolted flanges, feet and hoses with clamps; stators whose copper leaves the slots as woven hairpin crowns with bright welded
   tips; rotors with bearings (balls included), a resolver ring and a splined shaft; helical gears; inverters with fins, bolted covers and
   a round HV connector (knurled coupling ring, locking lever); forged I-section arms, bushes with through-bolts, ball joints with
   convoluted boots and castle nuts, a knuckle with a hub flange and studs, dampers with a reservoir and valve cable, air-spring bellows with
   crimp rings, steering rack with its boots, assist motor and lugs; multi-chamber floor extrusions, a cast subframe plate with pockets,
   a honeycomb-ribbed rear casting, crush cans, ribbed spring towers. The part ids, node names, pivots and material names did not change.
2. **Textured PBR materials** (`texgen.py`, `materials.py`). Each material is a procedural, tileable texture family (a tangent normal map,
   a roughness/metal image in glTF's layout, and an albedo where the pattern carries colour: copper strands, laminations, the printed cell
   wrap, boards, stickers) times a tint, at a physical tile size. `prim.py` gives every face UVs in metres of surface (a box's own edges, a
   cylinder's circumference and length, a sweep's arc length) and `solid()` divides them by the material's `xr_tile`, so the grain on a
   casing is millimetres whatever the part's size and brushing runs along a beam's length. Keep the maps *subtle*: the first versions
   (mottled albedo, strong brushing) read as camouflage and rain streaks.
3. **Contact shading per vertex** (`ao.py`): modifiers applied, every edge longer than 4 cm cut (so a lid has vertices near its bolts), 24
   cosine-weighted rays per vertex against the part itself, written as the custom attribute `_XRAO`. Each part is baked alone, so the
   shade stays true when the parts are drawn apart (the shade one part throws on another is left out on purpose). The web multiplies the
   environment's diffuse and specular light by it (`useVertexAo` in `src/lib/xray/fx.ts`); lamps are untouched. An atlas was tried first
   and dropped: 150 m of surface in one 2048 square leaves a texel the size of a bolt.
4. **The harness** (`XrayDirector.tsx`, `Harness`): the three HV cables get a corrugated sheath (one canvas ring pattern as bump and colour,
   its repeat following each cable's length).

Rebuild: `blender -b --factory-startup --python blender/scripts/su7_anatomy_export.py -- --ao --cards` (about 5 minutes: the build is 15 s,
the rays about 2 minutes, the 16 card stills the rest; leave `--ao` and `--cards` off while iterating on shapes, and run
`node scripts/xray-tools/render-cards.mjs blender/renders/xray public/xray/su7-ultra` after `--cards`). `XR_TEX_SCALE=0.25` makes quick, small
textures.

Budget (measured in the viewer, X-ray tab): the GLB is 3.5 MB (about 1.4 MB of it WebP textures) with 353 primitives and about 0.3 M
triangles, against 0.7 MB, 203 primitives and 60 k before; the hardware adds about 700 draw calls and 0.6 M triangles to a frame (it is drawn
twice there: the floor's mirror draws it again; in the Drive tab it is on the mirror-skip layer and is drawn once). Two things keep the
triangle count down: bevels go only on sharp edges of shapes bigger than 3 cm (a bevel weight set in `solid()`; bevelling bolts and
terminals doubled their faces), and only the big plates with things on them are cut finer for the shade (`ao.TESSELLATE`). Blueprint mode
gains from the detail (bolts, fins and ribs become linework).

Gotchas: a *generated* Blender image exports as a blank texture (write a PNG and load it back); changing `colorspace_settings` after
writing pixels resets the buffer (set it first); the exporter reads `Mix(Multiply)` of an albedo and a constant colour as the base-colour
factor, a Normal Map node as the normal texture, and roughness (G) / metal (B) of one ORM image as the metallic-roughness texture.
