import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';

/**
 * Ambient spill: the soft light of a light guide on the leather beside it.
 *
 * The cabin shader ignores the scene's lamps (the light is the environment and the occlusion atlas), so a real light would do
 * nothing. Instead the Blender cabin carries a ribbon along the surface next to each light guide (`M_Glow`: UV v 0 against the
 * guide, 1 where the glow has faded; blender/scripts/bpy_interior_polish.glow_ribbon) and the web draws it additively in the live
 * ambient colour. The bloom does the halo; this is the light on the leather.
 */
const GLOW = /^m_glow$/i;

/** One column of pixels along the ribbon's width: bright at the light guide (the bottom of the image, glTF's v = 1), black at the far edge. */
function gradient(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 4;
  c.height = 128;
  const ctx = c.getContext('2d')!;
  const g = ctx.createLinearGradient(0, 0, 0, 128);
  g.addColorStop(0, 'rgb(0,0,0)');
  g.addColorStop(0.55, 'rgb(20,20,20)');
  g.addColorStop(0.85, 'rgb(120,120,120)');
  g.addColorStop(1, 'rgb(255,255,255)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 4, 128);
  const t = new THREE.CanvasTexture(c);
  t.flipY = false; // glTF addressing
  t.colorSpace = THREE.SRGBColorSpace;
  t.needsUpdate = true;
  return t;
}

/** Dresses the cabin's `M_Glow` ribbons; `intensity` is the spill per unit of the HMI's brightness (0 turns them off). */
export function useAmbientSpill(model: THREE.Object3D, on: boolean, hue: number, brightness: number, gain: number) {
  const invalidate = useThree((s) => s.invalidate);
  const mats = React.useMemo(() => {
    const out = new Set<THREE.MeshStandardMaterial>();
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (GLOW.test(m.name) && m instanceof THREE.MeshStandardMaterial) out.add(m);
      }
    });
    return [...out];
  }, [model]);

  React.useEffect(() => {
    if (!mats.length) return;
    const tex = gradient();
    for (const m of mats) {
      m.color.set('#000000');
      m.emissiveMap = tex;
      m.blending = THREE.AdditiveBlending;
      m.transparent = true;
      m.depthWrite = false;
      m.side = THREE.DoubleSide;
      m.polygonOffset = true;
      m.polygonOffsetFactor = -1;
      m.polygonOffsetUnits = -1;
      m.toneMapped = false;
      m.roughness = 1;
      m.metalness = 0;
      m.needsUpdate = true;
    }
    return () => {
      for (const m of mats) {
        m.emissiveMap = null;
        m.needsUpdate = true;
      }
      tex.dispose();
    };
  }, [mats]);

  React.useEffect(() => {
    if (!mats.length) return;
    const col = new THREE.Color().setHSL(hue / 360, 0.92, 0.5);
    for (const m of mats) {
      m.emissive.copy(col);
      m.emissiveIntensity = on ? brightness * gain : 0;
      m.visible = on;
    }
    invalidate();
  }, [mats, on, hue, brightness, gain, invalidate]);
}
