'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle, XrayPart } from '@/data/vehicles/schema';
import { layoutLabels, type LabelAnchor } from '@/lib/xray/labels';
import { smooth, xrayOf } from '@/lib/xray/rig';
import { useVehicleStore } from '@/store/vehicle-store';
import { labelLayer } from '@/components/showroom/XrayLabels';

/**
 * Puts the exploded view's labels on the screen, every frame: each part's point (the middle of its nodes' box, wherever the rig has
 * flown them) is projected through the camera, the pills are laid out in their two columns (src/lib/xray/labels.ts) and the
 * leader lines drawn from the pills to the points. A label comes up as the level reaches the part's (`minLevel`) and goes when a
 * system is picked that it does not belong to. Writes straight to the DOM elements of showroom/XrayLabels.tsx.
 */
export function XrayLabelDriver({ vehicle }: { vehicle: Vehicle }) {
  const rig = xrayOf(vehicle);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const parts = vehicle.xray?.anatomy?.parts ?? [];
  const store = React.useRef({
    nodes: new Map<string, THREE.Object3D[]>(),
    anatomy: undefined as THREE.Object3D | undefined,
    exterior: undefined as THREE.Object3D | undefined,
    dims: new Map<string, [number, number]>(),
  });
  const tmp = React.useMemo(() => ({ box: new THREE.Box3(), part: new THREE.Box3(), v: new THREE.Vector3() }), []);

  const nodesOf = (p: XrayPart): THREE.Object3D[] => {
    const c = store.current;
    // the scenes are mounted and unmounted with the tab: a new root means the nodes found before are gone
    if (c.anatomy !== rig.roots.anatomy || c.exterior !== rig.roots.exterior) {
      c.nodes.clear();
      c.anatomy = rig.roots.anatomy;
      c.exterior = rig.roots.exterior;
    }
    let list = c.nodes.get(p.id);
    if (!list) {
      const root = p.scene === 'exterior' ? rig.roots.exterior : rig.roots.anatomy;
      list = root ? p.nodes.map((n) => root.getObjectByName(n)).filter((o): o is THREE.Object3D => !!o) : [];
      if (list.length) c.nodes.set(p.id, list);
    }
    return list;
  };

  useFrame(() => {
    const layer = labelLayer.current;
    if (!layer) return;
    const st = useVehicleStore.getState();
    const W = size.width;
    const H = size.height;
    const on = st.tab === 'xray' && W >= 760;
    const hide = (id: string) => {
      const e = layer.els.get(id);
      if (!e) return;
      if (e.pill && e.pill.style.opacity !== '0') {
        e.pill.style.opacity = '0';
        e.pill.style.pointerEvents = 'none';
      }
      e.path?.setAttribute('stroke-opacity', '0');
      e.dot?.setAttribute('opacity', '0');
    };
    const items: LabelAnchor[] = [];
    const alpha = new Map<string, number>();
    const screen = new Map<string, [number, number]>();
    for (const p of parts) {
      const e = layer.els.get(p.id);
      if (!e?.pill) continue;
      const minLvl = Math.min(p.minLevel ?? 0.85, 0.85);
      let a = smooth((rig.level - (minLvl - 0.12)) / 0.25);
      if (!on || !st.xraySystem || st.xraySystem !== p.system) a = 0;
      const nodes = a > 0.01 ? nodesOf(p) : [];
      if (!nodes.length) {
        hide(p.id);
        continue;
      }
      tmp.box.makeEmpty();
      for (const n of nodes) {
        n.updateWorldMatrix(true, true);
        tmp.box.union(tmp.part.setFromObject(n));
      }
      if (tmp.box.isEmpty()) {
        hide(p.id);
        continue;
      }
      tmp.box.getCenter(tmp.v).project(camera);
      if (tmp.v.z > 1 || tmp.v.z < -1) {
        hide(p.id);
        continue;
      }
      const x = (tmp.v.x * 0.5 + 0.5) * W;
      const y = (-tmp.v.y * 0.5 + 0.5) * H;
      let d = store.current.dims.get(p.id);
      if (!d || !d[0]) {
        d = [e.pill.offsetWidth, e.pill.offsetHeight];
        if (d[0]) store.current.dims.set(p.id, d);
      }
      items.push({ id: p.id, x, y, w: d[0] || 150, h: d[1] || 26 });
      alpha.set(p.id, a);
      screen.set(p.id, [x, y]);
    }
    const free = st.deviceInset;
    const placed = layoutLabels(items, {
      left: 16,
      right: W * (1 - free.right) - 12,
      top: 92 + st.uiTop * H,
      bottom: H * (1 - Math.max(free.bottom, 0.0)) - 150,
    });
    for (const pl of placed) {
      const e = layer.els.get(pl.id);
      const [ax, ay] = screen.get(pl.id)!;
      const a = alpha.get(pl.id) ?? 0;
      if (!e?.pill) continue;
      e.pill.style.transform = `translate(${pl.px.toFixed(1)}px, ${pl.py.toFixed(1)}px)`;
      e.pill.style.opacity = String(a);
      e.pill.style.pointerEvents = a > 0.5 ? 'auto' : 'none';
      // the leader: out of the pill's inner edge, one short level step, then straight to the part
      const step = pl.side === 'left' ? 14 : -14;
      e.path?.setAttribute('d', `M${pl.ex.toFixed(1)} ${pl.ey.toFixed(1)}h${step}L${ax.toFixed(1)} ${ay.toFixed(1)}`);
      e.path?.setAttribute('stroke-opacity', String(0.75 * a));
      e.dot?.setAttribute('cx', ax.toFixed(1));
      e.dot?.setAttribute('cy', ay.toFixed(1));
      e.dot?.setAttribute('opacity', String(a));
    }
  });
  return null;
}
