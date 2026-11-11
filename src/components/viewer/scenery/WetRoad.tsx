'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { Reflector } from 'three/examples/jsm/objects/Reflector.js';
import type { CarRig } from '@/lib/tech/rig';
import { weather } from '@/lib/tech/weather';
import { motionOk } from '../configurator';
import { STAGE_LAYER } from '../StudioShowroom';

/**
 * A wet road: a true mirror. The scene is drawn a second time from under the road (three's Reflector: the camera mirrored in the
 * road's plane, the road clipped away) into a render target, and the road's wet sheet shows that picture where water lies on
 * it: the car, its lamps, the trees, the barriers, the street lamps and the grey sky are all in it, as they are on a wet road.
 * The sheet is transparent over the asphalt (which the rain has darkened), so the road's own wear and paint stay:
 *
 * - how much it shows is Fresnel's: a lot at a low angle, little looking straight down; a thin film everywhere, a mirror in the
 *   puddles that lie in the wheel tracks and the low patches (a noise that rolls with the road, so they pass under the car);
 * - the film is rough: the reflection is smeared a little up and down, so a lamp's reflection is a streak, and sharp in a puddle;
 * - rain falls into the puddles and rings spread from every drop (a grid of rings with their own phases), which ripple the picture.
 *
 * Drawn only while it rains (`weather.level`), and the reflection pass is skipped when it does not.
 */

const VERTEX = /* glsl */ `
  uniform mat4 textureMatrix;
  varying vec4 vUv;
  varying vec3 vLocal;
  varying vec3 vWorld;
  varying vec3 vWorldN;
  void main() {
    vUv = textureMatrix * vec4( position, 1.0 );
    vLocal = position;
    vec4 wp = modelMatrix * vec4( position, 1.0 );
    vWorld = wp.xyz;
    vWorldN = normalize( mat3( modelMatrix ) * vec3( 0.0, 0.0, 1.0 ) );
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const FRAGMENT = /* glsl */ `
  uniform vec3 color;
  uniform sampler2D tDiffuse;
  uniform float uTime;
  uniform float uScroll;
  uniform float uLevel;
  uniform float uHalfLen;
  uniform float uFade;
  uniform float uHalfW;
  uniform float uLanesHalf;
  uniform float uLaneW;
  varying vec4 vUv;
  varying vec3 vLocal;
  varying vec3 vWorld;
  varying vec3 vWorldN;

  float hash21( vec2 p ) {
    p = fract( p * vec2( 123.34, 456.21 ) );
    p += dot( p, p + 45.32 );
    return fract( p.x * p.y );
  }
  float vnoise( vec2 p ) {
    vec2 i = floor( p );
    vec2 f = fract( p );
    f = f * f * ( 3.0 - 2.0 * f );
    float a = hash21( i );
    float b = hash21( i + vec2( 1.0, 0.0 ) );
    float c = hash21( i + vec2( 0.0, 1.0 ) );
    float d = hash21( i + vec2( 1.0, 1.0 ) );
    return mix( mix( a, b, f.x ), mix( c, d, f.x ), f.y );
  }
  float fbm( vec2 p ) {
    float s = 0.0;
    float a = 0.5;
    for ( int i = 0; i < 4; i ++ ) {
      s += a * vnoise( p );
      p = p * 2.03 + vec2( 11.7, 5.3 );
      a *= 0.5;
    }
    return s;
  }
  // rings spreading from raindrops: two grids of cells, each cell a ring with its own phase, the gradient of the wave as the normal's lean
  vec2 ripples( vec2 p, float t ) {
    vec2 acc = vec2( 0.0 );
    for ( int k = 0; k < 2; k ++ ) {
      float sc = 4.0 + 2.6 * float( k );
      vec2 q = p * sc + 19.7 * float( k );
      vec2 id = floor( q );
      vec2 f = fract( q ) - 0.5;
      float h = hash21( id + 3.1 * float( k ) );
      vec2 jit = ( vec2( hash21( id + 7.7 ), hash21( id + 13.3 ) ) - 0.5 ) * 0.5;
      vec2 d = f - jit;
      float r = length( d );
      float ph = fract( t * ( 0.7 + 0.5 * h ) + h * 9.0 );
      float x = r - ph * 0.5;
      float wave = sin( x * 55.0 ) * exp( - x * x / 0.0036 ) * ( 1.0 - ph ) * ( 1.0 - ph );
      acc += ( d / max( r, 1e-3 ) ) * wave * step( h, 0.72 );
    }
    return acc;
  }

  void main() {
    // the road's own frame: it rolls under the car, so the puddles and the rings roll with it
    vec2 p = vec2( vLocal.x + uScroll, vLocal.y );
    float inLane = 1.0 - smoothstep( uLanesHalf - 0.2, uLanesHalf + 0.2, abs( vLocal.y ) );
    float ly = mod( vLocal.y + uLanesHalf, uLaneW ) - 0.5 * uLaneW;
    float rut = max( exp( - pow( ( ly - 0.85 ) / 0.4, 2.0 ) ), exp( - pow( ( ly + 0.85 ) / 0.4, 2.0 ) ) ) * inLane;
    float n = fbm( p * vec2( 0.16, 0.5 ) + 3.0 );
    float puddle = smoothstep( 0.50 - 0.16 * rut, 0.64 - 0.16 * rut, n + 0.10 * rut );

    vec2 rip = ripples( p, uTime ) * ( 0.30 + 0.70 * puddle );
    vec2 micro = vec2( vnoise( p * 9.0 + uTime * 0.3 ) - 0.5, vnoise( p * 9.0 + 17.0 - uTime * 0.3 ) - 0.5 );

    vec2 uv = vUv.xy / vUv.w;
    uv += rip * 0.016 + micro * 0.004 * mix( 1.0, 0.2, puddle );
    // the film is rough: a short smear up and down, so a lamp's reflection is a streak; a puddle is nearly sharp
    float sm = mix( 0.018, 0.0025, puddle );
    vec3 refl = vec3( 0.0 );
    float wsum = 0.0;
    for ( int i = - 3; i <= 3; i ++ ) {
      float w = exp( - float( i * i ) * 0.35 );
      refl += texture2D( tDiffuse, uv + vec2( float( i ) * 0.5 * sm, float( i ) * sm ) ).rgb * w;
      wsum += w;
    }
    refl /= wsum;

    vec3 V = normalize( cameraPosition - vWorld );
    float ndv = clamp( dot( normalize( vWorldN ), V ), 0.0, 1.0 );
    float F = mix( 0.10, 1.0, pow( 1.0 - ndv, 4.5 ) );
    float gloss = mix( 0.62, 1.0, puddle );
    float ends = 1.0 - smoothstep( uHalfLen - uFade, uHalfLen, abs( vLocal.x ) );
    float sides = 1.0 - smoothstep( uHalfW - 1.0, uHalfW, abs( vLocal.y ) );
    float a = clamp( F * gloss * 1.3, 0.0, 0.93 ) * uLevel * ends * sides;

    gl_FragColor = vec4( refl, a );
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

const SHADER = {
  name: 'WetRoad',
  uniforms: {
    color: { value: null },
    tDiffuse: { value: null },
    textureMatrix: { value: null },
    uTime: { value: 0 },
    uScroll: { value: 0 },
    uLevel: { value: 0 },
    uHalfLen: { value: 100 },
    uFade: { value: 50 },
    uHalfW: { value: 7 },
    uLanesHalf: { value: 5.6 },
    uLaneW: { value: 3.75 },
  },
  vertexShader: VERTEX,
  fragmentShader: FRAGMENT,
};

interface WetRoadProps {
  rig: CarRig;
  /** the strip's middle along the road, its length and width, m */
  x: number;
  length: number;
  width: number;
  lanes: { count: number; width: number };
  /** the asphalt's fade at its ends, m */
  fadeEnd: number;
}

export function WetRoad({ rig, x, length, width, lanes, fadeEnd }: WetRoadProps) {
  const reflector = React.useMemo(() => {
    const r = new Reflector(new THREE.PlaneGeometry(length, width), {
      textureWidth: 960,
      textureHeight: 600,
      clipBias: 0.0005,
      multisample: 0,
      shader: SHADER,
    });
    r.rotation.x = -Math.PI / 2;
    // above the paint and the wear (3 mm), so everything of the road is under the plane the scene is mirrored in
    r.position.set(x, 0.004, 0);
    r.renderOrder = -0.35;
    r.layers.set(STAGE_LAYER);
    const m = r.material as THREE.ShaderMaterial;
    m.transparent = true;
    m.depthWrite = false;
    m.polygonOffset = true;
    m.polygonOffsetFactor = -8;
    m.polygonOffsetUnits = -8;
    const u = m.uniforms;
    u.uHalfLen.value = length / 2;
    u.uFade.value = fadeEnd;
    u.uHalfW.value = width / 2;
    u.uLanesHalf.value = (lanes.count * lanes.width) / 2;
    u.uLaneW.value = lanes.width;
    // the mirror sees what the camera sees (the car, its lamps, the stage's scenery, the hardware), whenever the camera's layers change
    const own = r.getReflectionCamera.bind(r);
    r.getReflectionCamera = (camera: THREE.Camera) => {
      const rc = own(camera);
      rc.layers.mask = camera.layers.mask;
      return rc;
    };
    return r;
  }, [x, length, width, lanes.count, lanes.width, fadeEnd]);
  React.useEffect(() => () => reflector.dispose(), [reflector]);

  const time = React.useRef(0);
  useFrame((_, dt) => {
    const u = (reflector.material as THREE.ShaderMaterial).uniforms;
    if (motionOk()) time.current += Math.min(dt, 0.1);
    u.uTime.value = time.current;
    u.uScroll.value = rig.state.scroll;
    u.uLevel.value = weather.level;
    // dry: no sheet, and no second picture of the scene
    reflector.visible = weather.level > 0.01;
  });
  return <primitive object={reflector} />;
}
