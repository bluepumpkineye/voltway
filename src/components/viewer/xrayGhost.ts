import * as THREE from 'three';

/**
 * The shell's ghost, as a shader patch rather than a material swap, so it can fade: every paint, trim and lamp material of the
 * exterior carries `uGhostK` (0 solid, 1 ghost), and the fragment shader turns its colour toward a cool pane and its alpha toward a
 * face-on opacity plus a rim that grows at the silhouette (Fresnel), which is what makes a see-through car read as a car. The
 * uniforms are shared by every patched material, so one write moves them all. The patch leaves the renderer's own `OPAQUE`
 * define alone (toggling `transparent` at run time would not rebuild the program): the replacement below does what the chunk
 * does and then mixes the ghost in. Blending itself is switched by `setGhost`.
 *
 * The wheels (tyres, discs, calipers), the lamps' LEDs and the glass are not patched: the wheels stay solid in an X-ray, and
 * the panes have their own opacity logic (useGlass in Openings.tsx), which follows the same level.
 */
export const GHOST = {
  k: { value: 0 },
  alpha: { value: 0.2 },
  rim: { value: 0.5 },
  color: { value: new THREE.Color('#9fb2c8') },
  /** how far the colour goes to the ghost's (the rest stays the paint's): 0.85 in the X-ray tab, less in the Drive tab's reveal, where the car stays its own colour */
  mix: { value: 0.85 },
};

const SKIP = /tyre|tire|disc|caliper|wheel|rim_|led_|reflector|lamp_clear|m_glass|m_shadow|frit|screen/i;

/** Patch a material for the ghost; false when it is one the ghost leaves alone. */
export function ghostable(m: THREE.Material): m is THREE.MeshStandardMaterial {
  if (!(m instanceof THREE.MeshStandardMaterial)) return false;
  if (m.userData.ghostable) return true;
  if (SKIP.test(m.name) || m.transparent) return false;
  m.userData.ghostable = true;
  const chained = m.onBeforeCompile;
  const keyed = m.customProgramCacheKey;
  m.onBeforeCompile = (shader, renderer) => {
    chained.call(m, shader, renderer);
    shader.uniforms.uGhostK = GHOST.k;
    shader.uniforms.uGhostAlpha = GHOST.alpha;
    shader.uniforms.uGhostRim = GHOST.rim;
    shader.uniforms.uGhostColor = GHOST.color;
    shader.uniforms.uGhostMix = GHOST.mix;
    shader.fragmentShader = shader.fragmentShader
      .replace(
        'void main() {',
        'uniform float uGhostK;\nuniform float uGhostAlpha;\nuniform float uGhostRim;\nuniform vec3 uGhostColor;\nuniform float uGhostMix;\nvoid main() {',
      )
      .replace(
        '#include <opaque_fragment>',
        `#ifdef OPAQUE
        diffuseColor.a = 1.0;
        #endif
        if ( uGhostK > 0.001 ) {
          float ghostFres = pow( 1.0 - clamp( abs( dot( normalize( normal ), normalize( vViewPosition ) ) ), 0.0, 1.0 ), 2.2 );
          vec3 ghostCol = uGhostColor * ( 0.55 + 0.9 * ghostFres );
          outgoingLight = mix( outgoingLight, ghostCol + outgoingLight * 0.3, uGhostK * uGhostMix );
          diffuseColor.a = mix( diffuseColor.a, clamp( uGhostAlpha + ghostFres * uGhostRim, 0.0, 1.0 ), uGhostK );
        }
        gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,
      );
  };
  m.customProgramCacheKey = () => `${keyed.call(m)}|ghost-v2`;
  m.needsUpdate = true;
  return true;
}

/** Switch the patched materials between opaque and blended for a ghost amount `k`. */
export function setGhost(mats: Iterable<THREE.Material>, k: number) {
  const on = k > 0.02;
  for (const m of mats) {
    if (m.transparent !== on) m.transparent = on;
    if (m.depthWrite === on) m.depthWrite = !on;
  }
  GHOST.k.value = k;
}
