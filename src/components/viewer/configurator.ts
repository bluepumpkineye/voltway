'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { ConfiguratorSpec, PaintFinish } from '@/data/vehicles/schema';

/**
 * Runtime paint and trim for the showroom.
 *
 * Both are material-parameter swaps on the cloned scene (CarModel's
 * useClonedScene makes the materials this car's own), tweened over a fraction
 * of a second. The glTF stays as exported: the first option of a spec is the
 * car as built and restores the material's own values, so a visitor who never
 * touches a swatch sees exactly what the Blender build shipped.
 *
 * Both hooks drive the animation from useFrame and keep asking for frames
 * while it runs, so they work under frameloop="demand".
 */

const DURATION = 0.7;
const ease = (t: number) => t * t * (3 - 2 * t);

/** The visitor's reduced-motion setting: swaps and camera flights then land at once. */
export function motionOk(): boolean {
  return typeof window === 'undefined' || !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

// ---------------------------------------------------------------------- paint

interface PaintParams {
  color: THREE.Color;
  roughness: number;
  metalness: number;
  clearcoat: number;
  clearcoatRoughness: number;
  sheen: number;
  sheenColor: THREE.Color;
  sheenRoughness: number;
}

function paintOf(m: THREE.MeshPhysicalMaterial): PaintParams {
  return {
    color: m.color.clone(),
    roughness: m.roughness,
    metalness: m.metalness,
    clearcoat: m.clearcoat,
    clearcoatRoughness: m.clearcoatRoughness,
    sheen: m.sheen,
    sheenColor: m.sheenColor.clone(),
    sheenRoughness: m.sheenRoughness,
  };
}

/**
 * Sheen is never driven fully to zero on a paint that has it: crossing zero
 * switches the sheen path out of the shader and recompiles the program, a
 * visible hitch the first time each way. A weight this small cannot be seen.
 */
const SHEEN_FLOOR = 0.001;

function paintTarget(built: PaintParams, finish: PaintFinish | undefined): PaintParams {
  if (!finish) return built;
  const sheen = finish.sheen;
  return {
    color: new THREE.Color(finish.color),
    roughness: finish.roughness ?? built.roughness,
    // the build's paint is dielectric; a finish says how metallic it is
    metalness: finish.metalness ?? 0,
    clearcoat: finish.clearcoat ?? built.clearcoat,
    clearcoatRoughness: finish.clearcoatRoughness ?? built.clearcoatRoughness,
    sheen: sheen ? (sheen.weight ?? 1) : built.sheen > 0 ? SHEEN_FLOOR : 0,
    sheenColor: sheen ? new THREE.Color(sheen.color) : built.sheenColor.clone(),
    sheenRoughness: sheen?.roughness ?? built.sheenRoughness,
  };
}

function applyPaint(m: THREE.MeshPhysicalMaterial, a: PaintParams, b: PaintParams, k: number) {
  m.color.copy(a.color).lerp(b.color, k);
  m.roughness = lerp(a.roughness, b.roughness, k);
  m.metalness = lerp(a.metalness, b.metalness, k);
  m.clearcoat = lerp(a.clearcoat, b.clearcoat, k);
  m.clearcoatRoughness = lerp(a.clearcoatRoughness, b.clearcoatRoughness, k);
  m.sheen = lerp(a.sheen, b.sheen, k);
  m.sheenColor.copy(a.sheenColor).lerp(b.sheenColor, k);
  m.sheenRoughness = lerp(a.sheenRoughness, b.sheenRoughness, k);
}

interface PaintSlot {
  m: THREE.MeshPhysicalMaterial;
  built: PaintParams;
}

/** The exterior's paint material(s), with their values as exported. */
export function usePaint(model: THREE.Object3D, spec: ConfiguratorSpec | undefined, paintId: string) {
  const invalidate = useThree((s) => s.invalidate);

  const slots = React.useMemo<PaintSlot[]>(() => {
    if (!spec) return [];
    const want = spec.paintMaterial.toLowerCase();
    const found: PaintSlot[] = [];
    const seen = new Set<THREE.Material>();
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of materialsOf(o)) {
        if (seen.has(m) || m.name.toLowerCase() !== want) continue;
        if (!(m instanceof THREE.MeshPhysicalMaterial)) continue;
        seen.add(m);
        found.push({ m, built: paintOf(m) });
      }
    });
    return found;
  }, [model, spec]);

  const option = spec?.paints.find((p) => p.id === paintId) ?? spec?.paints[0];
  const optionKey = option?.id;
  const anim = React.useRef<{ from: PaintParams; to: PaintParams; t: number } | null>(null);
  const touched = React.useRef(false);

  React.useEffect(() => {
    if (!slots.length || !option) return;
    // as built on first mount: leave the material exactly as exported
    if (!touched.current && !option.finish) return;
    touched.current = true;
    anim.current = {
      from: paintOf(slots[0].m),
      to: paintTarget(slots[0].built, option.finish),
      t: motionOk() ? 0 : 1,
    };
    invalidate();
    // keyed on the option id: its identity would restart the tween every render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots, optionKey, invalidate]);

  useFrame((_, dt) => {
    const a = anim.current;
    if (!a) return;
    a.t = Math.min(1, a.t + dt / DURATION);
    const k = ease(a.t);
    for (const s of slots) applyPaint(s.m, a.from, a.to, k);
    if (a.t >= 1) anim.current = null;
    else invalidate();
  });
}

// -------------------------------------------------------------------- caliper

/**
 * The brake calipers' paint, by material name: a colour swap on the exterior's
 * caliper material, tweened like the body paint. The first option is the car as
 * built and restores the material exactly as exported.
 */
export function useCaliper(model: THREE.Object3D, spec: ConfiguratorSpec | undefined, caliperId: string) {
  const invalidate = useThree((s) => s.invalidate);

  const slots = React.useMemo(() => {
    const found: { m: THREE.MeshStandardMaterial; built: THREE.Color }[] = [];
    if (!spec?.caliperMaterial) return found;
    const want = spec.caliperMaterial.toLowerCase();
    const seen = new Set<THREE.Material>();
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of materialsOf(o)) {
        if (seen.has(m) || m.name.toLowerCase() !== want || !(m instanceof THREE.MeshStandardMaterial)) continue;
        seen.add(m);
        found.push({ m, built: m.color.clone() });
      }
    });
    return found;
  }, [model, spec]);

  const option = spec?.calipers?.find((c) => c.id === caliperId) ?? spec?.calipers?.[0];
  const optionKey = option?.id;
  const anim = React.useRef<{ from: THREE.Color; to: THREE.Color; t: number } | null>(null);
  const touched = React.useRef(false);

  React.useEffect(() => {
    if (!slots.length || !option || !spec?.calipers) return;
    const asBuilt = option.id === spec.calipers[0].id;
    // as built on first mount: leave the material exactly as exported
    if (!touched.current && asBuilt) return;
    touched.current = true;
    anim.current = {
      from: slots[0].m.color.clone(),
      to: asBuilt ? slots[0].built.clone() : new THREE.Color(option.color),
      t: motionOk() ? 0 : 1,
    };
    invalidate();
    // keyed on the option id, as in usePaint
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots, optionKey, invalidate]);

  useFrame((_, dt) => {
    const a = anim.current;
    if (!a) return;
    a.t = Math.min(1, a.t + dt / DURATION);
    const k = ease(a.t);
    for (const s of slots) s.m.color.copy(a.from).lerp(a.to, k);
    if (a.t >= 1) anim.current = null;
    else invalidate();
  });
}

// --------------------------------------------------------------------- wheels

/**
 * The wheel designs, as nodes of the exterior: the chosen one is shown and the
 * others hidden (each design is a node holding all four wheels, so a change is a
 * handful of visibility flags). A design with an accent paint (the Sport's edges)
 * also sets that material's colour, tweened like the caliper's. The first option
 * is the car as built, and is shown on first mount without touching the material.
 */
export function useWheels(model: THREE.Object3D, spec: ConfiguratorSpec | undefined, wheelId: string) {
  const invalidate = useThree((s) => s.invalidate);

  const option = spec?.wheels?.find((w) => w.id === wheelId) ?? spec?.wheels?.[0];
  const optionKey = option?.id;

  // each design's node (by name, case-insensitive), found once
  const nodes = React.useMemo(() => {
    const found = new Map<string, THREE.Object3D>();
    if (!spec?.wheels) return found;
    const want = new Set(spec.wheels.map((w) => w.node.toLowerCase()));
    model.traverse((o) => {
      const n = o.name.toLowerCase();
      if (want.has(n) && !found.has(n)) found.set(n, o);
    });
    return found;
  }, [model, spec]);

  // the accent materials, by name, and their colour as built
  const accents = React.useMemo(() => {
    const out = new Map<string, { m: THREE.MeshStandardMaterial; built: THREE.Color }[]>();
    if (!spec?.wheels) return out;
    const want = new Set(spec.wheels.flatMap((w) => (w.accent ? [w.accent.material.toLowerCase()] : [])));
    if (!want.size) return out;
    const seen = new Set<THREE.Material>();
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of materialsOf(o)) {
        const n = m.name.toLowerCase();
        if (!want.has(n) || seen.has(m) || !(m instanceof THREE.MeshStandardMaterial)) continue;
        seen.add(m);
        const list = out.get(n) ?? [];
        list.push({ m, built: m.color.clone() });
        out.set(n, list);
      }
    });
    return out;
  }, [model, spec]);

  const anim = React.useRef<{ slots: { m: THREE.MeshStandardMaterial }[]; from: THREE.Color; to: THREE.Color; t: number } | null>(null);

  React.useEffect(() => {
    if (!spec?.wheels || !option) return;
    const shown = nodes.get(option.node.toLowerCase());
    for (const w of spec.wheels) {
      const o = nodes.get(w.node.toLowerCase());
      if (o) o.visible = o === shown;
    }
    const slots = option.accent ? accents.get(option.accent.material.toLowerCase()) : undefined;
    if (slots?.length && option.accent) {
      anim.current = {
        slots,
        from: slots[0].m.color.clone(),
        to: new THREE.Color(option.accent.color),
        t: motionOk() ? 0 : 1,
      };
    }
    invalidate();
    // keyed on the option id, as in useCaliper
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, accents, optionKey, invalidate]);

  useFrame((_, dt) => {
    const a = anim.current;
    if (!a) return;
    a.t = Math.min(1, a.t + dt / DURATION);
    const k = ease(a.t);
    for (const s of a.slots) s.m.color.copy(a.from).lerp(a.to, k);
    if (a.t >= 1) anim.current = null;
    else invalidate();
  });
}

// ----------------------------------------------------------------------- trim

interface TrimSlot {
  materials: THREE.MeshStandardMaterial[];
  built: THREE.Color;
}

/**
 * The cabin's trim materials, recoloured by name. The cabin's baked light is
 * light only (never albedo), so a new colour is shaded correctly.
 */
export function useTrim(model: THREE.Object3D, spec: ConfiguratorSpec | undefined, trimId: string) {
  const invalidate = useThree((s) => s.invalidate);

  /** lower-cased material name to the materials of that name and their built colour */
  const slots = React.useMemo(() => {
    const out = new Map<string, TrimSlot>();
    if (!spec) return out;
    const wanted = new Set<string>();
    for (const t of spec.trims) for (const n of Object.keys(t.colors ?? {})) wanted.add(n.toLowerCase());
    if (!wanted.size) return out;
    const seen = new Set<THREE.Material>();
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of materialsOf(o)) {
        const n = m.name.toLowerCase();
        if (!wanted.has(n) || seen.has(m) || !(m instanceof THREE.MeshStandardMaterial)) continue;
        seen.add(m);
        const slot = out.get(n);
        if (slot) slot.materials.push(m);
        else out.set(n, { materials: [m], built: m.color.clone() });
      }
    });
    return out;
  }, [model, spec]);

  const option = spec?.trims.find((t) => t.id === trimId) ?? spec?.trims[0];
  const optionKey = option?.id;
  const anim = React.useRef<{
    from: Map<string, THREE.Color>;
    to: Map<string, THREE.Color>;
    t: number;
  } | null>(null);
  const touched = React.useRef(false);

  React.useEffect(() => {
    if (!slots.size || !option) return;
    const colors = option.colors ?? {};
    const asBuilt = Object.keys(colors).length === 0;
    if (!touched.current && asBuilt) return;
    touched.current = true;
    const lower = new Map(Object.entries(colors).map(([n, c]) => [n.toLowerCase(), c]));
    const from = new Map<string, THREE.Color>();
    const to = new Map<string, THREE.Color>();
    for (const [n, slot] of slots) {
      from.set(n, slot.materials[0].color.clone());
      const hex = lower.get(n);
      to.set(n, hex ? new THREE.Color(hex) : slot.built.clone());
    }
    anim.current = { from, to, t: motionOk() ? 0 : 1 };
    invalidate();
    // keyed on the option id, as in usePaint
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots, optionKey, invalidate]);

  useFrame((_, dt) => {
    const a = anim.current;
    if (!a) return;
    a.t = Math.min(1, a.t + dt / DURATION);
    const k = ease(a.t);
    for (const [n, slot] of slots) {
      for (const m of slot.materials) m.color.copy(a.from.get(n)!).lerp(a.to.get(n)!, k);
    }
    if (a.t >= 1) anim.current = null;
    else invalidate();
  });
}
