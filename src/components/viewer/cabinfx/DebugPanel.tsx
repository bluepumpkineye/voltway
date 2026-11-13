'use client';

import React from 'react';
import { DEBUG_UI, FX, FX_DEFAULTS, touchFx } from './settings';

type Rec = Record<string, unknown>;

function deepAssign(to: Rec, from: Rec) {
  for (const k of Object.keys(from)) {
    const v = from[k];
    if (v && typeof v === 'object') deepAssign(to[k] as Rec, v as Rec);
    else to[k] = v;
  }
}

/**
 * The tuning panel (lil-gui), only with `?debug=true` in the address and only in the browser: every slider writes the
 * live settings (settings.ts) and asks for a frame. Nothing is stored; "copy values" puts the current numbers on the
 * clipboard as JSON, to be locked into FX_DEFAULTS.
 */
export function CabinFxDebugPanel() {
  // false on the server and the first client render, the module's one read of the address after that
  const [on, setOn] = React.useState(false);
  React.useEffect(() => setOn(DEBUG_UI), []);
  React.useEffect(() => {
    if (!on) return;
    let gui: { destroy: () => void } | null = null;
    let dead = false;
    void import('lil-gui').then(({ default: GUI }) => {
      if (dead) return;
      const g = new GUI({ title: 'Cabin FX (debug)', width: 280 });
      g.domElement.style.zIndex = '60';
      g.domElement.style.maxHeight = '92vh';
      g.domElement.style.overflowY = 'auto';
      const on = (c: { onChange: (f: () => void) => unknown }) => c.onChange(() => touchFx());

      g.add(FX, 'enabled').name('cabin FX on').onChange(() => touchFx());

      const t = g.addFolder('Tone mapping');
      on(t.add(FX.tone, 'mode', ['agx', 'neutral', 'aces']));
      on(t.add(FX.tone, 'exposure', 0.5, 2, 0.01));
      on(t.add(FX.tone, 'saturation', -0.5, 1, 0.01));
      on(t.add(FX.tone, 'contrast', -0.5, 0.5, 0.01));

      const ao = g.addFolder('N8AO');
      on(ao.add(FX.ao, 'enabled'));
      on(ao.add(FX.ao, 'radius', 0.02, 1.2, 0.01).name('aoRadius (m)'));
      on(ao.add(FX.ao, 'distanceFalloff', 0.05, 3, 0.01));
      on(ao.add(FX.ao, 'intensity', 0, 8, 0.05));
      on(ao.add(FX.ao, 'samples', 4, 64, 1).name('aoSamples'));
      on(ao.add(FX.ao, 'denoiseSamples', 1, 16, 1));
      on(ao.add(FX.ao, 'denoiseRadius', 1, 30, 1));
      on(ao.add(FX.ao, 'halfRes'));

      const b = g.addFolder('Bloom');
      on(b.add(FX.bloom, 'enabled'));
      on(b.add(FX.bloom, 'threshold', 0.2, 6, 0.01).name('luminanceThreshold'));
      on(b.add(FX.bloom, 'smoothing', 0, 1, 0.01).name('luminanceSmoothing'));
      on(b.add(FX.bloom, 'intensity', 0, 3, 0.01).name('strength'));
      on(b.add(FX.bloom, 'radius', 0, 1, 0.01));
      on(b.add(FX, 'ambientGain', 0.5, 8, 0.05).name('ambient strip x'));

      const f = g.addFolder('Footwell');
      on(f.add(FX.footwell, 'enabled'));
      on(f.add(FX.footwell, 'light', 0, 1, 0.01).name('light at the floor'));
      on(f.add(FX.footwell, 'height', 0.1, 1.2, 0.01).name('falloff height (m)'));

      const e = g.addFolder('Gloss environment');
      on(e.add(FX.gloss, 'envIntensity', 0, 4, 0.05).name('glass / piano env'));
      on(e.add(FX.gloss, 'chromeEnv', 0, 4, 0.05).name('chrome envMapIntensity'));
      on(e.add(FX.gloss, 'softbox').name('softbox room (off = hall)'));

      const m = g.addFolder('Materials');
      on(m.add(FX.materials, 'leatherNormal', 0, 2, 0.01).name('leather normalScale'));
      on(m.add(FX.materials, 'leatherRoughness', 0.2, 1, 0.01));
      on(m.add(FX.materials, 'leatherSheen', 0, 1, 0.01));
      on(m.add(FX.materials, 'alcantaraSheen', 0, 1, 0.01));
      on(m.add(FX.materials, 'proceduralLeather').name('procedural leather grain'));

      const c = g.addFolder('Camera');
      on(c.add(FX, 'fov', 0, 90, 0.5).name('fov (0 = pose)'));

      g.add(
        {
          copy: () => {
            void navigator.clipboard?.writeText(JSON.stringify(FX, null, 2));
          },
        },
        'copy',
      ).name('copy values (JSON)');
      g.add(
        {
          reset: () => {
            // in place: the sliders hold the nested objects themselves
            deepAssign(FX as unknown as Rec, FX_DEFAULTS as unknown as Rec);
            g.controllersRecursive().forEach((ct) => ct.updateDisplay());
            touchFx();
          },
        },
        'reset',
      ).name('reset to defaults');
      gui = g;
    });
    return () => {
      dead = true;
      gui?.destroy();
    };
  }, [on]);
  return null;
}
