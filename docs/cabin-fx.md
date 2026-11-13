# Cabin FX (2026-11-13)

The Interior tab's look upgrade, built on the BYD Seal first. Code: `src/components/viewer/cabinfx/`, Blender: `blender/scripts/seal_polish.py`.

## Switches

| URL | Effect |
| --- | --- |
| `?debug=true` | lil-gui panel: tone mode / exposure / saturation / contrast, N8AO (radius in metres, falloff, intensity, samples, denoise), bloom (threshold, smoothing, strength, radius, ambient strip multiplier), footwell light and height, gloss environment, leather normal scale / roughness / sheen, procedural-leather comparison, seat FOV. "copy values (JSON)" puts the numbers on the clipboard to paste into `FX_DEFAULTS` in `cabinfx/settings.ts`. The flag is kept for the browser session. |
| `?cabinfx=0` | Everything below off (before / after). |

## Scope

Everything runs only in the seat: `cameraMode === 'interior' && tab === 'interior'`.

- **Composer** (`InteriorFx.tsx`) is mounted only then. @react-three/postprocessing takes the renderer's tone mapping over while it is mounted, so the exterior (Neutral, exposure 0.92, the paint calibration) is never touched; it also restores both on unmount. The Canvas re-applies its own tone-map props when the showroom re-renders, so the composer sets exposure every frame.
- **Materials** (`materials.ts`): `upgradeInteriorMaterials` (standard to physical, kind per material name) runs in `useClonedScene`'s prepare step, before `useTrim` looks for the leathers; `retuneInteriorMaterials` applies the numbers while seated and restores the exported values elsewhere. It never writes `.color` (the theme switcher's), and `syncSheenTint` keeps the sheen a lighter version of the live colour.
- **Footwell**: `hallLighting` in `CarModel.tsx` multiplies the environment light by a height ramp from the cabin's own floor (its carpet). A baked light map (the 06T) holds its own shade and skips it.
- **Camera**: `driverView` is unchanged (46 degrees). Measured on the Seal: 52 degrees stretches the passenger headrest into the picture's edge, and an eye further back than about 5 cm is inside the driver's headrest. The portrait widening of the seat's lens is capped at 56 degrees.

## Seal-only (benchmark)

- Live cluster: `cabinfx/cluster.ts` (`LIVE_CLUSTER`), a 2048 x 768 canvas with the speedometer, P R N D (live from the store), battery and range, ADAS lane view, tyre pressures.
- Icon decals: `cabinfx/icons.ts` (`WITH_ICONS`) draws an 8 x 4 atlas; the Blender cabin carries flat quads in material `M_Icons` whose UVs point into it (`seal_polish.ICONS` and `icons.ts` `ICONS` are the same list). The driver's door-card icons ride with the door.
- `seal_polish.py`: cluster stood proud of the band glass (it was buried 11.5 mm) with a bezel, key collars, screen-neck collar, ADAS housing, wipers, B-pillar belt loops and webbing, icon quads. Hooked in last by `seal_interior_shell.main`. The stalks and the hub pad got finer tessellation in `seal_wheel.py`.
- Export: `blender -b --factory-startup --python <launcher calling export_seal.web_cabin(look="hall", outside=False)>`, about 6 minutes.

## Already in place before this work

Bevel + weighted normals (`carkit.mesh.bevel`, `F.box` radii), a 192-sample rim, the frameless rear-view mirror, the 2048 AO atlas on UV1 (the "UV2 bake"), clearcoat / sheen / normal maps in the Seal's GLB, the inside glass at 12 % opacity.
