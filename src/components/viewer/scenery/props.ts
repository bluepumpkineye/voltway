import * as THREE from 'three';
import { Builder, cached, hex, placement, type V3 } from './kit';
import { CELL, cellUV } from './textures';

/**
 * Street furniture, each one merged geometry with vertex colours (one draw call a kind, instanced where it repeats):
 * the lamp post with its bracket and lantern, a bench, a bin, bollards, a bus shelter, a signpost, a hydrant, a planter,
 * a row of shared bikes, the crash barrier of an expressway and its delineator posts. Standing on y = 0, the lamp's arm
 * toward +x, the bench and shelter facing +z.
 */
export type PropKind = 'lamp' | 'bench' | 'bin' | 'bollard' | 'shelter' | 'sign' | 'hydrant' | 'planter' | 'bikes' | 'guardrail' | 'delineator' | 'cone' | 'kmpost' | 'streetsign' | 'barrierPost' | 'personA' | 'personB' | 'personC' | 'scooter';

const cyl = (rt: number, rb: number, h: number, seg = 10, open = false) => new THREE.CylinderGeometry(rt, rb, h, seg, 1, open);
const box = (x: number, y: number, z: number, sx: number, sy: number, sz: number) => new THREE.BoxGeometry(sx, sy, sz).translate(x, y, z);

function mk(fn: (b: Builder) => void): THREE.BufferGeometry {
  const b = new Builder();
  fn(b);
  return b.build();
}

const S = '#9aa0a8'; // steel
const SD = '#6f757d';
const WHITE = '#eceae4';

function lamp(): THREE.BufferGeometry {
  return mk((b) => {
    // a tapered pole with a base plate and a hand-hole, a curved bracket and a flat LED lantern
    b.add(cyl(0.05, 0.085, 6.0, 12), placement(0, 3.0, 0), hex(S));
    b.add(cyl(0.12, 0.15, 0.55, 12), placement(0, 0.275, 0), hex(SD));
    b.add(cyl(0.18, 0.18, 0.05, 12), placement(0, 0.03, 0), hex('#6b6f76'));
    b.add(box(0, 0.9, 0.08, 0.09, 0.28, 0.02), placement(0, 0, 0), hex('#4a4e55'));
    // the bracket: a quarter curve
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 8; i++) {
      const a = (i / 8) * (Math.PI / 2);
      pts.push(new THREE.Vector3(Math.sin(a) * 1.5, 6.0 + (1 - Math.cos(a)) * 0.0 + Math.sin(a) * 0.05 + (1 - Math.cos(a)) * 0.1, 0));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    b.add(new THREE.TubeGeometry(curve, 10, 0.04, 6, false), placement(0, 0, 0), hex(S));
    b.add(box(1.5, 6.1, 0, 0.9, 0.1, 0.34), placement(0, 0, 0), hex('#b3b8be'));
    b.add(box(1.5, 6.04, 0, 0.8, 0.03, 0.26), placement(0, 0, 0), hex('#fff6dc'));
    b.add(box(1.05, 6.15, 0, 0.12, 0.1, 0.2), placement(0, 0, 0), hex('#7d838b'));
  });
}

function bench(): THREE.BufferGeometry {
  return mk((b) => {
    // a slatted park bench: two cast legs, six slats, a back
    for (const sx of [-0.7, 0.7]) {
      b.add(box(sx, 0.22, 0, 0.06, 0.44, 0.42), placement(0, 0, 0), hex('#33373d'));
      b.add(box(sx, 0.6, -0.17, 0.06, 0.6, 0.06), placement(0, 0, 0), hex('#33373d'));
    }
    for (let i = 0; i < 4; i++) b.add(box(0, 0.45, -0.17 + i * 0.12, 1.7, 0.035, 0.09), placement(0, 0, 0), hex('#a9825a'));
    for (let i = 0; i < 3; i++) b.add(box(0, 0.62 + i * 0.12, -0.2, 1.7, 0.09, 0.03), placement(0, 0, 0), hex('#a9825a'));
  });
}

function bin(): THREE.BufferGeometry {
  return mk((b) => {
    // a two-stream recycling bin: grey and green bodies with an opening each, on a steel frame
    b.add(box(-0.26, 0.5, 0, 0.5, 0.9, 0.5), placement(0, 0, 0), hex('#3d6a86'));
    b.add(box(0.26, 0.5, 0, 0.5, 0.9, 0.5), placement(0, 0, 0), hex('#7a7f86'));
    b.add(box(-0.26, 0.97, 0, 0.54, 0.05, 0.54), placement(0, 0, 0), hex('#2e3338'));
    b.add(box(0.26, 0.97, 0, 0.54, 0.05, 0.54), placement(0, 0, 0), hex('#2e3338'));
    b.add(box(-0.26, 0.82, 0.256, 0.3, 0.1, 0.02), placement(0, 0, 0), hex('#0b0c0e'));
    b.add(box(0.26, 0.82, 0.256, 0.3, 0.1, 0.02), placement(0, 0, 0), hex('#0b0c0e'));
    b.add(box(0, 0.04, 0, 1.06, 0.08, 0.56), placement(0, 0, 0), hex('#44484f'));
  });
}

function bollard(): THREE.BufferGeometry {
  return mk((b) => {
    b.add(cyl(0.085, 0.095, 0.82, 14), placement(0, 0.41, 0), hex('#8b9097'));
    b.add(cyl(0.087, 0.087, 0.12, 14), placement(0, 0.66, 0), hex(WHITE));
    b.add(cyl(0.087, 0.087, 0.05, 14), placement(0, 0.5, 0), hex('#d9402f'));
    b.add(new THREE.SphereGeometry(0.087, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), placement(0, 0.82, 0), hex('#8b9097'));
  });
}

function shelter(): THREE.BufferGeometry {
  return mk((b) => {
    // a bus shelter: a flat roof on four posts, glass back and sides, a timetable board, a bench, an advertising case
    const w = 4.0;
    const d = 1.6;
    const h = 2.7;
    for (const [px, pz] of [[-w / 2, -d / 2], [w / 2, -d / 2], [-w / 2, d / 2], [w / 2, d / 2]]) b.add(cyl(0.045, 0.045, h, 8), placement(px, h / 2, pz), hex('#9aa0a8'));
    b.add(box(0, h + 0.06, 0, w + 0.4, 0.1, d + 0.4), placement(0, 0, 0), hex('#7b8088'));
    b.add(box(0, h + 0.14, 0, w + 0.5, 0.05, d + 0.5), placement(0, 0, 0), hex('#2f6aa8'));
    // glass panels, slightly green
    b.add(box(0, 1.3, -d / 2, w - 0.1, 2.2, 0.03), placement(0, 0, 0), hex('#a9c4c0'));
    b.add(box(-w / 2, 1.3, 0, 0.03, 2.2, d - 0.1), placement(0, 0, 0), hex('#a9c4c0'));
    b.add(box(w / 2, 1.3, 0, 0.03, 2.2, d - 0.1), placement(0, 0, 0), hex('#a9c4c0'));
    // the bench, the advert case and a route board
    b.add(box(0, 0.5, -0.5, 2.6, 0.05, 0.4), placement(0, 0, 0), hex('#c9ccd0'));
    b.add(box(-1.2, 0.25, -0.5, 0.05, 0.5, 0.35), placement(0, 0, 0), hex('#6f757d'));
    b.add(box(1.2, 0.25, -0.5, 0.05, 0.5, 0.35), placement(0, 0, 0), hex('#6f757d'));
    b.add(box(w / 2 + 0.28, 1.15, 0, 0.14, 2.0, 1.2), placement(0, 0, 0), hex('#e9ecef'));
    b.add(box(w / 2 + 0.36, 1.15, 0, 0.02, 1.8, 1.0), placement(0, 0, 0), hex('#e6a21a'));
    b.add(box(-0.6, 1.5, -d / 2 + 0.03, 1.4, 0.7, 0.04), placement(0, 0, 0), hex('#d6dbe0'));
  });
}

function sign(): THREE.BufferGeometry {
  return mk((b) => {
    // a round regulatory sign (speed limit): a red ring, white face
    b.add(cyl(0.035, 0.035, 2.8, 8), placement(0, 1.4, 0), hex('#8b9097'));
    b.add(cyl(0.3, 0.3, 0.03, 20), placement(0, 2.65, 0.05).multiply(new THREE.Matrix4().makeRotationX(Math.PI / 2)), hex('#d1352b'));
    b.add(cyl(0.23, 0.23, 0.034, 20), placement(0, 2.65, 0.055).multiply(new THREE.Matrix4().makeRotationX(Math.PI / 2)), hex('#f4f3ee'));
    b.add(box(0, 2.65, 0.075, 0.12, 0.22, 0.01), placement(0, 0, 0), hex('#20232a'));
    b.add(box(0, 2.2, 0.05, 0.5, 0.22, 0.02), placement(0, 0, 0), hex('#2f6aa8'));
  });
}

function streetsign(): THREE.BufferGeometry {
  return mk((b) => {
    // a street-name plate on a pole: blue board, white band
    b.add(cyl(0.035, 0.035, 3.1, 8), placement(0, 1.55, 0), hex('#8b9097'));
    b.add(box(0, 3.0, 0.04, 1.3, 0.3, 0.03), placement(0, 0, 0), hex('#1f5fa8'));
    b.add(box(0, 3.0, 0.062, 1.2, 0.04, 0.01), placement(0, 0, 0), hex('#f1f3f4'));
    b.add(box(0, 2.62, 0.04, 0.9, 0.24, 0.03), placement(0, 0, 0), hex('#2c7d4f'));
  });
}

function hydrant(): THREE.BufferGeometry {
  return mk((b) => {
    b.add(cyl(0.1, 0.12, 0.7, 12), placement(0, 0.35, 0), hex('#b73a2c'));
    b.add(new THREE.SphereGeometry(0.1, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), placement(0, 0.7, 0), hex('#b73a2c'));
    b.add(cyl(0.06, 0.06, 0.3, 8), placement(0, 0.45, 0).multiply(new THREE.Matrix4().makeRotationZ(Math.PI / 2)), hex('#a8a9aa'));
    b.add(cyl(0.13, 0.13, 0.05, 12), placement(0, 0.025, 0), hex('#7a7f86'));
  });
}

function planter(): THREE.BufferGeometry {
  return mk((b) => {
    // a long concrete trough with soil and a low planting on it (the planting is leaf cards in the scene; here the soil only)
    b.add(box(0, 0.33, 0, 2.2, 0.66, 0.7), placement(0, 0, 0), hex('#b9b6ae'));
    b.add(box(0, 0.66, 0, 2.28, 0.07, 0.78), placement(0, 0, 0), hex('#d2d0c9'));
    b.add(box(0, 0.62, 0, 2.0, 0.05, 0.5), placement(0, 0, 0), hex('#4a3a2c'));
  });
}

/** Shared bikes parked in a row on the footway (a Chinese street's most familiar sight): wheels, frames, baskets, in three colours. */
function bikes(): THREE.BufferGeometry {
  return mk((b) => {
    const cols = ['#f0b323', '#2b8ed6', '#e4503a', '#2f9e6a', '#f0b323', '#2b8ed6'];
    const n = 6;
    for (let i = 0; i < n; i++) {
      const z = (i - (n - 1) / 2) * 0.55;
      const c = hex(cols[i % cols.length]);
      const lean = (i % 2 ? 1 : -1) * 0.04;
      // two wheels
      for (const x of [-0.46, 0.46]) {
        b.add(new THREE.TorusGeometry(0.31, 0.035, 6, 18), placement(x, 0.35, z, 0, 1, 1, 1, lean, 0), hex('#1b1c20'));
      }
      // frame: a top tube, a down tube, a seat tube and a basket
      b.add(cyl(0.02, 0.02, 0.9, 6), placement(0, 0.58, z).multiply(new THREE.Matrix4().makeRotationZ(Math.PI / 2 - 0.18)), c);
      b.add(cyl(0.02, 0.02, 0.5, 6), placement(0.12, 0.45, z).multiply(new THREE.Matrix4().makeRotationZ(0.55)), c);
      b.add(cyl(0.02, 0.02, 0.5, 6), placement(-0.2, 0.55, z), c);
      b.add(box(0.5, 0.86, z, 0.04, 0.24, 0.04), placement(0, 0, 0), hex('#2a2c31'));
      b.add(box(0.5, 1.0, z, 0.06, 0.04, 0.5), placement(0, 0, 0), hex('#2a2c31'));
      b.add(box(0.56, 0.83, z, 0.3, 0.22, 0.34), placement(0, 0, 0), c);
      b.add(box(-0.22, 0.9, z, 0.24, 0.05, 0.14), placement(0, 0, 0), hex('#27292e'));
    }
  });
}

/**
 * A figure standing, from the feet up: trousers, a jacket or coat, arms a little away from the body, a head with hair. Low-polygon
 * and still (the scene is drawn on demand, not animated); `style` picks the clothes and the build. Facing +z.
 */
function person(style: 0 | 1 | 2): THREE.BufferGeometry {
  const looks = [
    { trousers: '#2f3440', top: '#2f5d8a', hair: '#1b1a1a', skin: '#d9ae8a', h: 1.0, bag: '#8a3b2e' },
    { trousers: '#d8d2c6', top: '#c75a6e', hair: '#2a1d16', skin: '#e2b896', h: 0.93, bag: '#2b2b30' },
    { trousers: '#3b3f35', top: '#e0b642', hair: '#3a2c20', skin: '#cfa27c', h: 1.05, bag: '#2f5d8a' },
  ] as const;
  const L = looks[style];
  return mk((b) => {
    const k = L.h;
    const legH = 0.86 * k;
    for (const x of [-0.085, 0.085]) {
      b.add(cyl(0.062, 0.07, legH, 8), placement(x, legH / 2, 0), hex(L.trousers));
      b.add(new THREE.BoxGeometry(0.1, 0.06, 0.2), placement(x, 0.03, 0.04), hex('#1c1c20'));
    }
    const torsoH = 0.62 * k;
    b.add(cyl(0.2, 0.16, torsoH, 10), placement(0, legH + torsoH / 2, 0), hex(L.top));
    b.add(new THREE.SphereGeometry(0.2, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), placement(0, legH + torsoH, 0, 0, 1, 0.45, 0.8), hex(L.top));
    for (const x of [-1, 1]) {
      b.add(cyl(0.045, 0.04, 0.58 * k, 7), placement(x * 0.235, legH + torsoH - 0.3 * k, 0, 0, 1, 1, 1, 0, x * 0.1), hex(L.top, 0.92));
      b.add(new THREE.SphereGeometry(0.045, 6, 5), placement(x * 0.255, legH + torsoH - 0.6 * k, 0), hex(L.skin));
    }
    b.add(cyl(0.05, 0.055, 0.09, 8), placement(0, legH + torsoH + 0.05, 0), hex(L.skin));
    b.add(new THREE.SphereGeometry(0.115, 10, 8), placement(0, legH + torsoH + 0.17, 0, 0, 0.92, 1.05, 1), hex(L.skin));
    b.add(new THREE.SphereGeometry(0.122, 10, 6, 0, Math.PI * 2, 0, Math.PI * 0.55), placement(0, legH + torsoH + 0.19, -0.01, 0, 0.95, 1, 1.05), hex(L.hair));
    // a bag on the shoulder
    b.add(new THREE.BoxGeometry(0.26, 0.2, 0.09), placement(0.27, legH + 0.12, 0.02), hex(L.bag));
  });
}

/** A shared e-scooter parked on its stand with its rider's yellow helmet box on the back (the delivery rider's look, with no brand on it). */
function scooter(): THREE.BufferGeometry {
  return mk((b) => {
    const body = hex('#e9edf0');
    for (const x of [-0.5, 0.5]) b.add(new THREE.TorusGeometry(0.16, 0.06, 8, 16), placement(x, 0.22, 0, 0, 1, 1, 1, 0, 0), hex('#1a1b1e'));
    b.add(box(0, 0.32, 0, 1.0, 0.16, 0.26), placement(0, 0, 0), body);
    b.add(box(-0.42, 0.52, 0, 0.5, 0.28, 0.3), placement(0, 0, 0), body);
    b.add(box(-0.1, 0.62, 0, 0.62, 0.08, 0.3), placement(0, 0, 0), hex('#25272c'));
    b.add(box(0.5, 0.52, 0, 0.1, 0.5, 0.08), placement(0, 0, 0), body);
    b.add(box(0.5, 0.82, 0, 0.1, 0.05, 0.5), placement(0, 0, 0), hex('#25272c'));
    b.add(box(-0.62, 0.88, 0, 0.42, 0.42, 0.42), placement(0, 0, 0), hex('#f0b323'));
    b.add(box(0.55, 0.78, 0, 0.18, 0.1, 0.2), placement(0, 0, 0), hex('#dfe3e6'));
  });
}

function guardrail(): THREE.BufferGeometry {
  return mk((b) => {
    // an expressway's W-beam rail, 4 m a bay: posts at each end, two corrugations, a reflector
    const L = 4;
    for (const x of [0, L]) b.add(box(x, 0.4, 0, 0.12, 0.8, 0.08), placement(0, 0, 0), hex('#8b9097'));
    b.add(box(L / 2, 0.62, 0.1, L, 0.1, 0.03), placement(0, 0, 0), hex('#c9ced3'));
    b.add(box(L / 2, 0.5, 0.115, L, 0.1, 0.03), placement(0, 0, 0), hex('#b3b8be'));
    b.add(box(L / 2, 0.74, 0.1, L, 0.05, 0.03), placement(0, 0, 0), hex('#d6dadd'));
    b.add(box(L / 2, 0.38, 0.1, L, 0.05, 0.03), placement(0, 0, 0), hex('#9aa0a6'));
    b.add(box(1, 0.56, 0.135, 0.12, 0.07, 0.01), placement(0, 0, 0), hex('#f0b323'));
  });
}

function barrierPost(): THREE.BufferGeometry {
  return mk((b) => {
    // a concrete median barrier segment (New Jersey profile), 4 m
    const L = 4;
    b.add(box(L / 2, 0.15, 0, L, 0.3, 0.6), placement(0, 0, 0), hex('#c4c5c4'));
    b.add(box(L / 2, 0.58, 0, L, 0.56, 0.32), placement(0, 0, 0), hex('#cdcecd'));
    b.add(box(L / 2, 0.92, 0, L, 0.14, 0.24), placement(0, 0, 0), hex('#d6d7d5'));
    b.add(box(L / 2, 0.6, 0.165, L, 0.04, 0.01), placement(0, 0, 0), hex('#a8a9a8'));
  });
}

function delineator(): THREE.BufferGeometry {
  return mk((b) => {
    b.add(cyl(0.03, 0.035, 1.2, 8), placement(0, 0.6, 0), hex('#eceae4'));
    b.add(box(0, 0.95, 0.04, 0.11, 0.2, 0.01), placement(0, 0, 0), hex('#f0b323'));
    b.add(box(0, 0.7, 0.04, 0.11, 0.1, 0.01), placement(0, 0, 0), hex('#1c1d20'));
  });
}

function cone(): THREE.BufferGeometry {
  return mk((b) => {
    b.add(cyl(0.05, 0.15, 0.7, 12), placement(0, 0.38, 0), hex('#e8541f'));
    b.add(cyl(0.11, 0.11, 0.1, 12), placement(0, 0.45, 0), hex(WHITE));
    b.add(box(0, 0.025, 0, 0.42, 0.05, 0.42), placement(0, 0, 0), hex('#2b2d31'));
  });
}

function kmpost(): THREE.BufferGeometry {
  return mk((b) => {
    // a kilometre marker: a small white post with a green face
    b.add(box(0, 0.5, 0, 0.18, 1.0, 0.1), placement(0, 0, 0), hex('#eef0ee'));
    b.add(box(0, 0.78, 0.055, 0.15, 0.3, 0.01), placement(0, 0, 0), hex('#2c7d4f'));
  });
}

/**
 * What lights on a sign at night: its faces only, a hair thicker than the sign's own, drawn additively over them (Scenery's `Props`), so the
 * dimmed board and ring come back to something near their daytime colours, as a reflective sign does in a street lamp's or a headlamp's light.
 */
export function signFaces(kind: 'sign' | 'streetsign'): THREE.BufferGeometry {
  return cached(`faces-${kind}`, () =>
    mk((b) => {
      if (kind === 'sign') {
        const R = new THREE.Matrix4().makeRotationX(Math.PI / 2);
        b.add(cyl(0.3, 0.3, 0.04, 20), placement(0, 2.65, 0.05).multiply(R), hex('#d1352b', 0.8));
        b.add(cyl(0.23, 0.23, 0.044, 20), placement(0, 2.65, 0.055).multiply(R), hex('#f4f3ee', 0.85));
        b.add(box(0, 2.2, 0.05, 0.5, 0.22, 0.03), placement(0, 0, 0), hex('#2f6aa8', 0.85));
      } else {
        b.add(box(0, 3.0, 0.04, 1.3, 0.3, 0.036), placement(0, 0, 0), hex('#1f5fa8', 0.85));
        b.add(box(0, 3.0, 0.062, 1.2, 0.04, 0.014), placement(0, 0, 0), hex('#f1f3f4', 0.85));
        b.add(box(0, 2.62, 0.04, 0.9, 0.24, 0.036), placement(0, 0, 0), hex('#2c7d4f', 0.85));
      }
    }),
  );
}

/** the radius of the soft contact shadow under a prop, m */
export const PROP_DOT: Partial<Record<PropKind, number>> = { lamp: 0.28, bollard: 0.18, bench: 0.9, bin: 0.55, shelter: 2.3, sign: 0.2, streetsign: 0.2, hydrant: 0.25, planter: 1.3, bikes: 1.9, personA: 0.32, personB: 0.32, personC: 0.34, scooter: 0.8 };

const MAKERS: Record<PropKind, () => THREE.BufferGeometry> = {
  lamp,
  bench,
  bin,
  bollard,
  shelter,
  sign,
  streetsign,
  hydrant,
  planter,
  bikes,
  guardrail,
  personA: () => person(0),
  personB: () => person(1),
  personC: () => person(2),
  scooter,
  delineator,
  cone,
  kmpost,
  barrierPost,
};

export function propGeometry(kind: PropKind): THREE.BufferGeometry {
  return cached(`prop-${kind}`, () => MAKERS[kind]());
}

/**
 * A big green overhead sign on a gantry across an expressway: the gantry's frame (two posts, two chords, the bracing), the board's
 * green body, and the board's face as its own uv quad (painted by `gantrySign` in textures.ts). In its own frame the gantry spans x
 * and the face looks toward +z.
 */
export function gantry(span: number, height = 6.2): { frame: THREE.BufferGeometry; board: THREE.BufferGeometry; face: THREE.BufferGeometry; faceW: number; faceH: number } {
  return cached(`gantry-${span}-${height}`, () => {
    const f = new Builder();
    const steel = hex('#9aa0a8');
    for (const x of [-span / 2, span / 2]) {
      f.add(cyl(0.2, 0.26, height + 0.8, 12), placement(x, (height + 0.8) / 2, 0), steel);
      f.add(cyl(0.32, 0.32, 0.12, 12), placement(x, 0.06, 0), hex('#6f757d'));
    }
    f.add(cyl(0.16, 0.16, span, 10), placement(0, height + 0.3, 0).multiply(new THREE.Matrix4().makeRotationZ(Math.PI / 2)), steel);
    f.add(cyl(0.12, 0.12, span, 8), placement(0, height - 0.15, 0).multiply(new THREE.Matrix4().makeRotationZ(Math.PI / 2)), steel);
    for (let i = 0; i <= 14; i++) {
      const x = -span / 2 + (i * span) / 14;
      f.add(cyl(0.04, 0.04, 0.55, 6), placement(x, height + 0.075, 0), steel);
    }
    const bw = Math.min(span * 0.7, 13);
    const bh = 2.5;
    const bd = new Builder();
    bd.box(-bw / 2, height - bh - 0.25, -0.09, bw, bh, 0.14, hex('#1f7a4d'), 0, ['+z']);
    const face = new Builder();
    face.rect([-bw / 2, height - bh - 0.25, 0.052], [1, 0, 0], [0, 1, 0], bw, bh, [1, 1, 1], 0, 0, 0, [0, 0, 1, 1]);
    return { frame: f.build(), board: bd.build(), face: face.build(), faceW: bw, faceH: bh };
  });
}

/** A uv-mapped atlas quad for a shop sign standing alone, for the lot (a signboard on a pole). */
export function signBoard(cell: number): THREE.BufferGeometry {
  return cached(`signboard-${cell}`, () => {
    const b = new Builder();
    b.rect([-0.9, 2.2, 0], [1, 0, 0], [0, 1, 0], 1.8, 1.0, [1, 1, 1], 0, 0, 0, cellUV(cell));
    b.box(-0.04, 0, -0.04, 0.08, 2.2, 0.08, hex('#8b9097'), 0);
    return b.build();
  });
}
export { CELL as SIGN_CELLS };
export type { V3 };
