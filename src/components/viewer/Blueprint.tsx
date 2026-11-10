'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { xrayOf } from '@/lib/xray/rig';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * Blueprint mode: the car as an engineering drawing. The scene is not re-lit or re-skinned; it is drawn again as a G-buffer (view
 * normal, part id and depth) by an override material, twice: once for the hardware and the cabin, once for the shell's paint. A
 * full-screen pass then turns the two buffers into the drawing: a drafting-paper field with a perspective floor grid; each
 * part filled with a dark wash and cross-hatched by how it faces the light (one set of lines for the lighter half-tones, a
 * second across them, a third for the darkest), outlined where depth, normal or part changes between neighbouring pixels (the
 * silhouettes, the creases and the joints between parts), and the shell drawn over everything as faint line work only, so that
 * the hardware reads through it. A system picked in the panel stays lit, the rest fall back.
 *
 * It takes over the canvas's rendering while it is on (a positive `useFrame` priority tells react-three-fiber to stop drawing the
 * scene itself) and gives it back when it unmounts; the meshes it draws are tagged on layers 4 and 5, which only its own passes
 * look at, so nothing of the studio (the floor, the shadows, the lamps' glow) is in the drawing.
 */

const L_INNER = 4;
const L_SHELL = 5;

/** The id each part of the scene is drawn with: 0 is the paper. */
const SYSTEM_ID: Record<string, number> = { shell: 1, cabin: 2, wheels: 3, battery: 4, drive: 5, chassis: 6, suspension: 7, steering: 8, harness: 9, root: 6, brakes: 3 };

/** The ink of each id (sRGB): the paper's blue stays, the systems get a colour of their own, quietly. */
const INK = [
  '#000000',
  '#8fb8ee', // shell
  '#9ab4d6', // cabin
  '#b7d0f0', // wheels
  '#4fdcff', // battery
  '#ffb454', // drive
  '#e9f3ff', // chassis
  '#9dffc4', // suspension
  '#ffe27a', // steering
  '#ff8a5c', // harness
  '#ffffff',
  '#ffffff',
];

const G_VERT = /* glsl */ `
varying vec3 vN;
void main() {
  vN = normalize( normalMatrix * normal );
  gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`;

const G_FRAG = /* glsl */ `
uniform float uId;
varying vec3 vN;
void main() {
  vec3 n = normalize( vN );
  if ( ! gl_FrontFacing ) n = -n;
  gl_FragColor = vec4( n.xy * 0.5 + 0.5, uId / 255.0, 1.0 );
}`;

const C_VERT = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4( position.xy, 0.0, 1.0 );
}`;

const C_FRAG = /* glsl */ `
precision highp float;
uniform sampler2D tA;
uniform sampler2D dA;
uniform sampler2D tB;
uniform sampler2D dB;
uniform vec2 uRes;
uniform float uPx;
uniform float uThick;
uniform float uNear;
uniform float uFar;
uniform mat4 uInvViewProj;
uniform vec3 uCam;
uniform float uFocus;
uniform vec3 uInk[12];
varying vec2 vUv;

const vec3 LIGHT = vec3( -0.42, 0.66, 0.62 );

float lin( float d ) {
  float z = d * 2.0 - 1.0;
  return 2.0 * uNear * uFar / ( uFar + uNear - z * ( uFar - uNear ) );
}
vec3 nrm( vec4 c ) {
  vec2 xy = c.xy * 2.0 - 1.0;
  return vec3( xy, sqrt( max( 0.0, 1.0 - dot( xy, xy ) ) ) );
}
float idOf( vec4 c ) { return floor( c.b * 255.0 + 0.5 ); }

float gridLine( vec2 p, float s ) {
  vec2 q = p / s;
  vec2 g = abs( fract( q - 0.5 ) - 0.5 ) / max( fwidth( q ), vec2( 1e-5 ) );
  return 1.0 - min( min( g.x, g.y ), 1.0 );
}

float hatchLine( vec2 p, float ang, float spacing, float width ) {
  float c = cos( ang );
  float s = sin( ang );
  float d = ( p.x * c + p.y * s ) / spacing;
  float f = abs( fract( d + 0.5 ) - 0.5 );
  float w = width / spacing;
  return 1.0 - smoothstep( w * 0.5, w * 0.5 + fwidth( d ) + 1e-4, f );
}

vec3 paper( vec2 uv ) {
  vec3 top = vec3( 0.030, 0.105, 0.215 );
  vec3 bot = vec3( 0.060, 0.205, 0.385 );
  vec3 c = mix( bot, top, smoothstep( 0.0, 1.0, uv.y ) );
  vec2 q = uv * 2.0 - 1.0;
  c *= 1.0 - 0.28 * dot( q, q ) * 0.5;
  vec2 p = gl_FragCoord.xy / uPx;
  c += vec3( 0.45, 0.72, 1.0 ) * ( gridLine( p, 24.0 ) * 0.035 + gridLine( p, 120.0 ) * 0.07 );
  // the floor, in perspective: a metre and five metres, fading with distance
  vec4 w = uInvViewProj * vec4( uv * 2.0 - 1.0, 1.0, 1.0 );
  vec3 dir = normalize( w.xyz / w.w - uCam );
  if ( dir.y < -0.002 ) {
    float t = -uCam.y / dir.y;
    vec3 hit = uCam + dir * t;
    float fade = exp( -t * 0.05 ) * smoothstep( 0.0, 0.08, -dir.y * 6.0 );
    float g = gridLine( hit.xz, 1.0 ) * 0.14 + gridLine( hit.xz, 5.0 ) * 0.26;
    c = mix( c, vec3( 0.50, 0.76, 1.0 ), g * fade );
  }
  return c;
}

// line work where depth, normal or part changes between neighbouring pixels; also hands back the ink of the part it belongs to
float edgeOf( sampler2D t, sampler2D d, vec2 uv, float w, out float inkId ) {
  vec2 px = w / uRes;
  vec2 o0 = uv + vec2( -1.0, -1.0 ) * px;
  vec2 o1 = uv + vec2( 1.0, -1.0 ) * px;
  vec2 o2 = uv + vec2( -1.0, 1.0 ) * px;
  vec2 o3 = uv + vec2( 1.0, 1.0 ) * px;
  vec4 c0 = texture2D( t, o0 );
  vec4 c1 = texture2D( t, o1 );
  vec4 c2 = texture2D( t, o2 );
  vec4 c3 = texture2D( t, o3 );
  float z0 = lin( texture2D( d, o0 ).r );
  float z1 = lin( texture2D( d, o1 ).r );
  float z2 = lin( texture2D( d, o2 ).r );
  float z3 = lin( texture2D( d, o3 ).r );
  float dz = abs( z0 - z3 ) + abs( z1 - z2 );
  float e = smoothstep( 0.035, 0.09, dz / max( 0.5, min( min( z0, z1 ), min( z2, z3 ) ) ) * 4.0 );
  float both03 = c0.a * c3.a;
  float both12 = c1.a * c2.a;
  float en = ( 1.0 - dot( nrm( c0 ), nrm( c3 ) ) ) * both03 + ( 1.0 - dot( nrm( c1 ), nrm( c2 ) ) ) * both12;
  e = max( e, smoothstep( 0.22, 0.55, en ) );
  float ei = max( both03 * abs( idOf( c0 ) - idOf( c3 ) ), both12 * abs( idOf( c1 ) - idOf( c2 ) ) );
  e = max( e, min( 1.0, ei ) );
  inkId = c3.a > 0.5 ? idOf( c3 ) : c0.a > 0.5 ? idOf( c0 ) : c1.a > 0.5 ? idOf( c1 ) : idOf( c2 );
  return e;
}

void main() {
  vec2 uv = vUv;
  vec3 col = paper( uv );
  vec4 a = texture2D( tA, uv );
  vec4 b = texture2D( tB, uv );
  vec3 L = normalize( LIGHT );
  vec2 p = gl_FragCoord.xy / uPx;

  // the shell: a faint wash, a few hatch lines in its shade
  if ( b.a > 0.5 ) {
    float tone = 1.0 - clamp( dot( nrm( b ), L ), 0.0, 1.0 );
    float h = hatchLine( p, 0.785, 7.0, 0.8 ) * step( 0.42, tone ) * 0.5;
    col = mix( col, uInk[1], 0.045 + h * 0.22 );
  }

  // the hardware and the cabin: a dark wash and cross-hatching
  if ( a.a > 0.5 ) {
    float id = idOf( a );
    vec3 ink = uInk[int( id )];
    float dim = ( uFocus >= 0.0 && abs( id - uFocus ) > 0.5 && id > 2.5 ) ? 0.28 : 1.0;
    float tone = clamp( 1.0 - dot( nrm( a ), L ) * 0.92 - 0.06, 0.0, 1.0 );
    float h = hatchLine( p, 0.785, 5.5, 0.85 ) * step( 0.22, tone );
    h = max( h, hatchLine( p, -0.785, 5.5, 0.85 ) * step( 0.46, tone ) );
    h = max( h, hatchLine( p, 0.0, 5.5, 0.85 ) * step( 0.7, tone ) );
    vec3 fill = mix( vec3( 0.035, 0.125, 0.25 ), ink, 0.07 + 0.06 * ( 1.0 - tone ) );
    vec3 part = mix( fill, ink, h * 0.62 );
    col = mix( col, part, dim );
  }

  // outlines: the hardware's at full strength, the shell's over everything, lighter
  float iA;
  float eA = edgeOf( tA, dA, uv, uThick, iA );
  float dimA = ( uFocus >= 0.0 && abs( iA - uFocus ) > 0.5 && iA > 2.5 ) ? 0.3 : 1.0;
  col = mix( col, uInk[int( iA )], eA * dimA * 0.95 );
  float iB;
  float eB = edgeOf( tB, dB, uv, uThick * 0.9, iB );
  col = mix( col, uInk[1], eB * 0.5 );

  gl_FragColor = vec4( col, 1.0 );
}`;

function srgb(hex: string): THREE.Vector3 {
  const c = new THREE.Color(hex);
  // the colours are written straight to the canvas: sRGB values, not linear
  c.convertLinearToSRGB();
  return new THREE.Vector3(c.r, c.g, c.b);
}

/** Mounts the pass while the blueprint is on (the X-ray tab's switch). */
export function Blueprint({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.tab === 'xray' && s.xrayBlueprint);
  return on ? <BlueprintPass vehicle={vehicle} /> : null;
}

function BlueprintPass({ vehicle }: { vehicle: Vehicle }) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const invalidate = useThree((s) => s.invalidate);
  const rig = xrayOf(vehicle);

  const parts = React.useMemo(() => {
    const gMat = new THREE.ShaderMaterial({ vertexShader: G_VERT, fragmentShader: G_FRAG, uniforms: { uId: { value: 0 } }, side: THREE.DoubleSide });
    gMat.toneMapped = false;
    const make = () => {
      const rt = new THREE.WebGLRenderTarget(4, 4, { type: THREE.UnsignedByteType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
      rt.depthTexture = new THREE.DepthTexture(4, 4, THREE.UnsignedIntType);
      rt.depthTexture.minFilter = THREE.NearestFilter;
      rt.depthTexture.magFilter = THREE.NearestFilter;
      return rt;
    };
    const a = make();
    const b = make();
    const comp = new THREE.ShaderMaterial({
      vertexShader: C_VERT,
      fragmentShader: C_FRAG,
      uniforms: {
        tA: { value: a.texture },
        dA: { value: a.depthTexture },
        tB: { value: b.texture },
        dB: { value: b.depthTexture },
        uRes: { value: new THREE.Vector2(1, 1) },
        uPx: { value: 1 },
        uThick: { value: 1.0 },
        uNear: { value: 0.1 },
        uFar: { value: 100 },
        uInvViewProj: { value: new THREE.Matrix4() },
        uCam: { value: new THREE.Vector3() },
        uFocus: { value: -1 },
        uInk: { value: INK.map(srgb) },
      },
      depthTest: false,
      depthWrite: false,
    });
    comp.toneMapped = false;
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), comp);
    quad.frustumCulled = false;
    const compScene = new THREE.Scene();
    compScene.add(quad);
    const compCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    return { gMat, a, b, comp, quad, compScene, compCam };
  }, []);

  // tag the meshes the passes draw: the hardware and the cabin on one layer, the shell on the other, each with its part id
  const tagged = React.useRef(new Set<THREE.Mesh>());
  const tag = React.useCallback(() => {
    const hook = function (this: THREE.Mesh, _r: unknown, _s: unknown, _c: unknown, _g: unknown, material: THREE.Material) {
      const u = (material as THREE.ShaderMaterial).uniforms;
      if (u?.uId) {
        u.uId.value = this.userData.bpId ?? 0;
        (material as THREE.ShaderMaterial).uniformsNeedUpdate = true;
      }
    };
    const apply = (root: THREE.Object3D | undefined, kind: 'exterior' | 'cabin' | 'anatomy') => {
      root?.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh || tagged.current.has(m)) return;
        let id = 0;
        let layer = L_INNER;
        if (kind === 'cabin') id = SYSTEM_ID.cabin;
        else if (kind === 'exterior') {
          let wheel = false;
          for (let p: THREE.Object3D | null = m; p; p = p.parent) if (/wheels/i.test(p.name)) wheel = true;
          id = wheel ? SYSTEM_ID.wheels : SYSTEM_ID.shell;
          layer = wheel ? L_INNER : L_SHELL;
        } else {
          let sys: string | undefined;
          for (let p: THREE.Object3D | null = m; p && !sys; p = p.parent) {
            const raw = p.userData?.xr;
            if (typeof raw === 'string') {
              try {
                sys = (JSON.parse(raw) as { sys?: string }).sys;
              } catch {
                /* skip */
              }
            }
          }
          id = SYSTEM_ID[sys ?? 'chassis'] ?? SYSTEM_ID.chassis;
          if (m.parent?.name === 'XR_Harness') id = SYSTEM_ID.harness;
        }
        m.userData.bpId = id;
        m.layers.enable(layer);
        m.userData.bpLayer = layer;
        m.onBeforeRender = hook as unknown as THREE.Mesh['onBeforeRender'];
        tagged.current.add(m);
      });
    };
    apply(rig.roots.exterior, 'exterior');
    apply(rig.roots.cabin, 'cabin');
    apply(rig.roots.anatomy, 'anatomy');
  }, [rig]);

  React.useEffect(() => {
    invalidate();
    const set = tagged.current;
    return () => {
      for (const m of set) {
        m.layers.disable(m.userData.bpLayer ?? L_INNER);
        m.onBeforeRender = THREE.Object3D.prototype.onBeforeRender as unknown as THREE.Mesh['onBeforeRender'];
      }
      set.clear();
      parts.a.dispose();
      parts.b.dispose();
      parts.comp.dispose();
      parts.gMat.dispose();
      parts.quad.geometry.dispose();
      invalidate();
    };
  }, [parts, invalidate]);

  // dev: window.__bp.thick, to tune the line weight by eye
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') (window as unknown as { __bp?: unknown }).__bp = parts.comp.uniforms;
  }, [parts]);

  const clear = React.useMemo(() => new THREE.Color(), []);
  const focusOf = (s: string | null) => (s ? (SYSTEM_ID[s] ?? -1) : -1);
  useFrame(() => {
    tag();
    const dpr = gl.getPixelRatio();
    const w = Math.max(2, Math.floor(size.width * dpr));
    const h = Math.max(2, Math.floor(size.height * dpr));
    if (parts.a.width !== w || parts.a.height !== h) {
      parts.a.setSize(w, h);
      parts.b.setSize(w, h);
    }
    const cam = camera as THREE.PerspectiveCamera;
    const u = parts.comp.uniforms;
    u.uRes.value.set(w, h);
    u.uPx.value = dpr;
    u.uThick.value = Math.max(1, dpr * 0.85);
    u.uNear.value = cam.near;
    u.uFar.value = cam.far;
    u.uInvViewProj.value.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse).invert();
    u.uCam.value.copy(cam.position);
    u.uFocus.value = focusOf(useVehicleStore.getState().xraySystem);

    const prevTarget = gl.getRenderTarget();
    const prevMask = camera.layers.mask;
    const prevBg = scene.background;
    const prevOverride = scene.overrideMaterial;
    const prevShadow = gl.shadowMap.autoUpdate;
    const prevAlpha = gl.getClearAlpha();
    gl.getClearColor(clear);
    gl.shadowMap.autoUpdate = false;
    scene.background = null;
    scene.overrideMaterial = parts.gMat;
    gl.setClearColor(0x000000, 0);
    for (const [layer, rt] of [[L_INNER, parts.a], [L_SHELL, parts.b]] as const) {
      camera.layers.set(layer);
      gl.setRenderTarget(rt);
      gl.render(scene, camera);
    }
    scene.overrideMaterial = prevOverride;
    scene.background = prevBg;
    camera.layers.mask = prevMask;
    gl.setRenderTarget(null);
    gl.render(parts.compScene, parts.compCam);
    gl.setClearColor(clear, prevAlpha);
    gl.shadowMap.autoUpdate = prevShadow;
    gl.setRenderTarget(prevTarget);
  }, 1);
  return null;
}
