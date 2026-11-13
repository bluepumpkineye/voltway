'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { BrightnessContrast, EffectComposer, HueSaturation, N8AO, SMAA, SelectiveBloom, ToneMapping } from '@react-three/postprocessing';
import { ToneMappingMode } from 'postprocessing';
import { cabinFxExcluded } from '@/lib/showroom/interiorPreset';
import { useVehicleStore } from '@/store/vehicle-store';
import { FX, bindFrame, fxVersion, subscribeFx } from './settings';

/**
 * The interior's post-processing: screen-space ambient occlusion tuned for a cabin (N8AO), a bloom that only the
 * ambient strips can reach, and the tone map, all in one composer that exists ONLY while the visitor sits in the
 * cabin on the Interior tab.
 *
 * Scoping is by mounting. The composer takes over the renderer's tone mapping while it is mounted
 * (@react-three/postprocessing's toneMappingGuard) and gives it back when it unmounts, so the outside, with its
 * Neutral curve and the paint calibrated against it, is never touched: leaving the seat, switching tabs or toggling
 * Studio | City just removes this component. (The cabin's own HMI window, the stencil of the clear glass and every
 * other exterior-only pass are not part of this path.)
 */

export function useCabinFx() {
  React.useSyncExternalStore(subscribeFx, fxVersion, fxVersion);
  return FX;
}

/** The showroom's own curve (ShowroomViewer's Canvas props), which every exterior view is calibrated in. */
const EXTERIOR_TONE = THREE.NeutralToneMapping;

const MODES: Record<typeof FX.tone.mode, ToneMappingMode> = {
  agx: ToneMappingMode.AGX,
  neutral: ToneMappingMode.NEUTRAL,
  aces: ToneMappingMode.ACES_FILMIC,
};

/** True while the visitor is in the cabin on the Interior tab with the upgrade switched on, for a car that has it (not cabinFxExcluded). */
export function useCabinFxOn(slug: string): boolean {
  const fx = useCabinFx();
  const seated = useVehicleStore((s) => s.cameraMode === 'interior' && s.tab === 'interior');
  return fx.enabled && seated && !cabinFxExcluded(slug);
}

export function InteriorFx({ slug }: { slug: string }) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => bindFrame(invalidate), [invalidate]);
  const on = useCabinFxOn(slug);
  const cabinReady = useVehicleStore((s) => s.cabinReady);
  return on && cabinReady ? <Composer /> : null;
}

/** The meshes drawn in an ambient light guide's material: the only things that may glow. */
function useGuideMeshes(): THREE.Object3D[] {
  const scene = useThree((s) => s.scene);
  return React.useMemo(() => {
    const out: THREE.Object3D[] = [];
    scene.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      if (mats.some((m) => /ambient/i.test(m.name))) out.push(mesh);
    });
    return out;
  }, [scene]);
}

function Composer() {
  const fx = useCabinFx();
  const gl = useThree((s) => s.gl);
  const guides = useGuideMeshes();

  // three's exposure is what the composer's tone-mapping pass reads (its shader includes three's own AgX / Neutral / ACES).
  // Set every frame, before the composer's render: the Canvas re-applies its own `gl` props (Neutral, 0.92) whenever the
  // showroom re-renders, which would otherwise put the exterior's exposure back under a composer that is still running.
  const was = React.useRef<number | null>(null);
  useFrame(() => {
    was.current ??= gl.toneMappingExposure;
    gl.toneMappingExposure = FX.tone.exposure;
    gl.toneMapping = THREE.NoToneMapping;
  });
  React.useEffect(
    () => () => {
      // the exterior's own exposure comes back with the composer's removal (the renderer's tone mapping, with the Canvas's props)
      if (was.current !== null) gl.toneMappingExposure = was.current;
      gl.toneMapping = EXTERIOR_TONE;
    },
    [gl],
  );

  return (
    // MSAA off: N8AO reads the depth of the scene's own render, which a multisampled buffer cannot give it (SMAA closes the edges)
    <EffectComposer multisampling={0} frameBufferType={THREE.HalfFloatType}>
      <N8AO
        enabled={fx.ao.enabled}
        aoRadius={fx.ao.radius}
        distanceFalloff={fx.ao.distanceFalloff}
        intensity={fx.ao.intensity}
        aoSamples={fx.ao.samples}
        denoiseSamples={fx.ao.denoiseSamples}
        denoiseRadius={fx.ao.denoiseRadius}
        halfRes={fx.ao.halfRes}
        quality="medium"
      />
      {/* selective: only the ambient light guides are in the mask, so a chrome ring's glint never glows (a plain Bloom hazed
          every bright reflection, which read as a white outline round the wheel's rings) */}
      {guides.length > 0 && (
        <SelectiveBloom
          selection={guides}
          selectionLayer={11}
          luminanceThreshold={fx.bloom.threshold}
          luminanceSmoothing={fx.bloom.smoothing}
          intensity={fx.bloom.enabled ? fx.bloom.intensity : 0}
          radius={fx.bloom.radius}
          mipmapBlur
        />
      )}
      <ToneMapping mode={MODES[fx.tone.mode]} />
      <HueSaturation saturation={fx.tone.saturation} />
      <BrightnessContrast contrast={fx.tone.contrast} />
      <SMAA />
    </EffectComposer>
  );
}
