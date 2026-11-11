'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { rigOf } from '@/lib/tech/rig';
import { useRuntime } from '@/lib/tech/session';
import { stepWeather, weather } from '@/lib/tech/weather';
import { motionOk } from './configurator';
import { useDusk } from './Lights';
import { hazeUniforms } from './scenery/kit';
import { onStage } from './scenery/Scenery';

/**
 * The rain of the Drive tab's wet road. Three parts, all drawn by the stage's camera and nothing else:
 *
 * - `WeatherDriver` follows the Road chip: it takes the room toward an overcast grey (src/lib/tech/weather.ts, which `useDusk` reads),
 *   thickens the haze, and keeps frames coming while it rains (the drops move even when the run is paused). It asks for no frames when
 *   dry, as the rest of the viewer.
 * - `Rainfall`: a few thousand streaks in a box about the camera, each falling at its own speed, a ribbon turned to the camera, with the
 *   car's speed leaning them back (in the car's frame the air rushes past) and lengthening them (motion blur). They come down to the
 *   road and fade at the box's edge.
 * - `Spray`: the plume each tyre throws up on a wet road, fading back behind the car, stronger with speed.
 * The wet road itself (the mirror, the puddles, the rings) is `scenery/WetRoad.tsx`.
 */

const HAZE = 0.0042;

export function WeatherDriver() {
  const rt = useRuntime();
  const wet = Boolean(rt?.road?.lanes && rt.launch?.drive?.env.wet);
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    weather.target = wet ? 1 : 0;
    invalidate();
  }, [wet, invalidate]);
  React.useEffect(
    () => () => {
      weather.target = 0;
      weather.level = 0;
      hazeUniforms.uHazeDensity.value = HAZE;
    },
    [],
  );
  useFrame((_, dt) => {
    const moving = stepWeather(dt);
    hazeUniforms.uHazeDensity.value = HAZE * (1 + 1.1 * weather.level);
    // the rain falls whether or not the run plays: frames while it rains (a viewer with reduced motion sees it still)
    if (moving || (weather.level > 0.01 && motionOk())) invalidate();
  }, -20);
  return null;
}

/** Rain and spray belong to the Drive tab's road, which is the only wet one. */
export function TechRain({ vehicle }: { vehicle: Vehicle }) {
  const rt = useRuntime();
  if (!(rt?.road?.lanes && rt.launch?.drive)) return null;
  return <Rainfall vehicle={vehicle} />;
}

// ---------------------------------------------------------------------------------------------- streaks

const BOX = new THREE.Vector3(38, 24, 38);

const STREAK_VERT = /* glsl */ `
  uniform float uTime;
  uniform vec3 uCam;
  uniform vec3 uBox;
  uniform vec3 uVel;
  uniform float uLenK;
  uniform float uWidth;
  attribute vec4 aSeed;
  varying float vA;
  varying float vT;
  void main() {
    float spd = 0.85 + 0.3 * aSeed.w;
    vec3 vel = uVel * spd;
    vec3 p0 = aSeed.xyz * uBox;
    // the box follows the camera sideways, and runs from the road up: a streak that falls out of its bottom comes in again at the top
    vec3 head;
    head.x = uCam.x + ( mod( p0.x + vel.x * uTime - uCam.x, uBox.x ) - 0.5 * uBox.x );
    head.z = uCam.z + ( mod( p0.z + vel.z * uTime - uCam.z, uBox.z ) - 0.5 * uBox.z );
    head.y = mod( p0.y + vel.y * uTime, uBox.y );
    float len = ( 0.35 + uLenK * length( vel ) ) * ( 0.8 + 0.4 * aSeed.w );
    vec3 tail = head - normalize( vel ) * len;
    vec4 mvH = viewMatrix * vec4( head, 1.0 );
    vec4 mvT = viewMatrix * vec4( tail, 1.0 );
    vec3 mv = mix( mvH.xyz, mvT.xyz, position.y );
    vec3 dirV = mvT.xyz - mvH.xyz;
    vec3 side = normalize( cross( dirV, mv ) );
    // at least a pixel and a bit wide at any distance
    float w = max( uWidth * ( 0.7 + 0.6 * aSeed.w ), - mv.z * 0.0016 );
    mv += side * position.x * w;
    gl_Position = projectionMatrix * vec4( mv, 1.0 );
    float edge = 1.0 - smoothstep( 0.55, 1.0, length( ( head.xz - uCam.xz ) / ( 0.5 * uBox.xz ) ) );
    float ground = smoothstep( 0.0, 0.6, head.y );
    vA = edge * ground * ( 0.35 + 0.65 * aSeed.w );
    vT = position.y;
  }
`;

const STREAK_FRAG = /* glsl */ `
  uniform vec3 uColor;
  uniform float uLevel;
  varying float vA;
  varying float vT;
  void main() {
    gl_FragColor = vec4( uColor, vA * ( 1.0 - vT * 0.8 ) * uLevel * 0.95 );
  }
`;

function makeStreaks(n: number): THREE.BufferGeometry {
  const pos = new Float32Array(n * 4 * 3);
  const seed = new Float32Array(n * 4 * 4);
  const idx = new Uint32Array(n * 6);
  const corner = [
    [-1, 0],
    [1, 0],
    [1, 1],
    [-1, 1],
  ];
  // a fixed run of numbers (mulberry32), so the rain is the same every time
  let a = 20250611;
  const rnd = () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  for (let i = 0; i < n; i++) {
    const s = [rnd(), rnd(), rnd(), rnd()];
    for (let k = 0; k < 4; k++) {
      const v = i * 4 + k;
      pos[v * 3] = corner[k][0];
      pos[v * 3 + 1] = corner[k][1];
      seed.set(s, v * 4);
    }
    const b = i * 4;
    idx.set([b, b + 1, b + 2, b, b + 2, b + 3], i * 6);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 4));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  return g;
}

// ------------------------------------------------------------------------------------------------ spray

const SPRAY_VERT = /* glsl */ `
  uniform float uTime;
  uniform float uSpeed;
  uniform float uAmt;
  uniform vec3 uWheel[4];
  attribute vec4 aSeed;
  attribute float aWheel;
  varying float vA;
  varying vec2 vUv;
  void main() {
    float life = 1.1;
    float age = fract( aSeed.x + uTime / life );
    float t = age * life;
    vec3 w = uWheel[ int( aWheel + 0.5 ) ];
    float back = uSpeed * 0.2 * t * ( 0.55 + 0.45 * aSeed.y );
    float rise = 0.12 + 1.1 * age * ( 0.35 + 0.65 * aSeed.z );
    float side = ( aSeed.w - 0.5 ) * ( 0.4 + 1.6 * age );
    vec3 c = w + vec3( - 0.35 - back, rise, side );
    float size = ( 0.4 + 2.0 * age ) * ( 0.7 + 0.6 * aSeed.y );
    vec4 mv = viewMatrix * vec4( c, 1.0 );
    mv.xy += position.xy * size;
    gl_Position = projectionMatrix * mv;
    float fade = 1.0 - age;
    vA = fade * fade * uAmt * ( 0.4 + 0.6 * aSeed.z );
    vUv = position.xy + 0.5;
  }
`;

const SPRAY_FRAG = /* glsl */ `
  uniform vec3 uColor;
  varying float vA;
  varying vec2 vUv;
  void main() {
    float d = length( vUv - 0.5 ) * 2.0;
    float a = pow( max( 1.0 - d, 0.0 ), 2.0 );
    gl_FragColor = vec4( uColor, a * vA * 0.62 );
  }
`;

const SPRAY_REAR = 64;
const SPRAY_FRONT = 36;

function makeSpray(): THREE.BufferGeometry {
  const counts = [SPRAY_FRONT, SPRAY_FRONT, SPRAY_REAR, SPRAY_REAR];
  const n = counts.reduce((s, c) => s + c, 0);
  const pos = new Float32Array(n * 4 * 3);
  const seed = new Float32Array(n * 4 * 4);
  const wheel = new Float32Array(n * 4);
  const idx = new Uint32Array(n * 6);
  const corner = [
    [-0.5, -0.5],
    [0.5, -0.5],
    [0.5, 0.5],
    [-0.5, 0.5],
  ];
  let a = 777;
  const rnd = () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  let i = 0;
  counts.forEach((c, w) => {
    for (let j = 0; j < c; j++, i++) {
      const s = [(j + rnd()) / c, rnd(), rnd(), rnd()];
      for (let k = 0; k < 4; k++) {
        const v = i * 4 + k;
        pos[v * 3] = corner[k][0];
        pos[v * 3 + 1] = corner[k][1];
        seed.set(s, v * 4);
        wheel[v] = w;
      }
      const b = i * 4;
      idx.set([b, b + 1, b + 2, b, b + 2, b + 3], i * 6);
    }
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 4));
  g.setAttribute('aWheel', new THREE.BufferAttribute(wheel, 1));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  return g;
}

const CORNERS = ['FL', 'FR', 'RL', 'RR'] as const;

function Rainfall({ vehicle }: { vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const streakGeo = React.useMemo(() => makeStreaks(5200), []);
  const sprayGeo = React.useMemo(() => makeSpray(), []);
  const mats = React.useMemo(() => {
    const streak = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uCam: { value: new THREE.Vector3() },
        uBox: { value: BOX },
        uVel: { value: new THREE.Vector3(0, -9.5, 0) },
        uLenK: { value: 0.03 },
        uWidth: { value: 0.016 },
        uColor: { value: new THREE.Color(0.8, 0.85, 0.92) },
        uLevel: { value: 0 },
      },
      vertexShader: STREAK_VERT,
      fragmentShader: STREAK_FRAG,
      transparent: true,
      depthWrite: false,
    });
    const spray = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uSpeed: { value: 0 },
        uAmt: { value: 0 },
        uWheel: { value: [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()] },
        uColor: { value: new THREE.Color(0.78, 0.82, 0.88) },
      },
      vertexShader: SPRAY_VERT,
      fragmentShader: SPRAY_FRAG,
      transparent: true,
      depthWrite: false,
    });
    return { streak, spray };
  }, []);
  React.useEffect(
    () => () => {
      streakGeo.dispose();
      sprayGeo.dispose();
      mats.streak.dispose();
      mats.spray.dispose();
    },
    [streakGeo, sprayGeo, mats],
  );

  // the air's brightness: the streaks are as light as the room is
  const bright = React.useRef(1);
  useDusk((d) => {
    bright.current = Math.pow(Math.max(d.room.g, 0.001), 1 / 2.2);
  });

  const streakMesh = React.useRef<THREE.Mesh>(null);
  const sprayMesh = React.useRef<THREE.Mesh>(null);
  const time = React.useRef(0);
  const last = React.useRef<number | null>(null);
  const speed = React.useRef(0);
  useFrame(({ camera }, dt) => {
    const on = weather.level > 0.01;
    if (streakMesh.current) streakMesh.current.visible = on;
    if (sprayMesh.current) sprayMesh.current.visible = on;
    if (!on) {
      last.current = null;
      return;
    }
    const step = Math.min(dt, 0.1);
    if (motionOk()) time.current += step;
    // the car's speed from how far the road has rolled: the air rushes back past a car that is going
    const s = rig.state.scroll;
    if (last.current !== null && step > 1e-4) {
      const inst = Math.max(0, (s - last.current) / step);
      speed.current += (Math.min(inst, 80) - speed.current) * (1 - Math.exp(-step * 8));
    }
    last.current = s;
    const v = speed.current;
    const col = bright.current;

    const su = mats.streak.uniforms;
    su.uTime.value = time.current;
    su.uCam.value.copy(camera.position);
    su.uVel.value.set(-v * 0.55, -9.5, 0);
    su.uColor.value.setRGB(0.8 * col, 0.85 * col, 0.92 * col);
    su.uLevel.value = weather.level;

    const pu = mats.spray.uniforms;
    pu.uTime.value = time.current;
    pu.uSpeed.value = v;
    pu.uAmt.value = Math.min(1, Math.max(0, (v - 3) / 18)) * weather.level;
    pu.uColor.value.setRGB(0.78 * col, 0.82 * col, 0.88 * col);
    const L = rig.layout;
    if (L) {
      const st = rig.state;
      const c = Math.cos(st.yaw);
      const n = Math.sin(st.yaw);
      const rac = rig.rac;
      CORNERS.forEach((k, i) => {
        // the wheel's place in the model's frame is the rear axle's (rac) plus its own offset in the axle's frame (x ahead, y to the left)
        const mx = rac.x + L.wheels[k].x;
        const my = rac.y + L.wheels[k].y;
        pu.uWheel.value[i].set(st.x + c * mx - n * my, 0.05, st.z - (n * mx + c * my));
      });
    }
  });

  return (
    <>
      <mesh ref={(m) => { sprayMesh.current = m; onStage(m); }} geometry={sprayGeo} material={mats.spray} frustumCulled={false} renderOrder={4} />
      <mesh ref={(m) => { streakMesh.current = m; onStage(m); }} geometry={streakGeo} material={mats.streak} frustumCulled={false} renderOrder={5} />
    </>
  );
}
