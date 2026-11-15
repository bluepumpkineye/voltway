import type { PaintFinish, PaintKind, PaintOption } from './schema';

/**
 * Voltway's own paints: neutral and muted / dark colours, and the matt finishes, that the nine
 * makers' palettes (mostly white, silver, grey, black, blue and purple) do not carry.
 *
 * None of these is a maker's colour. Each one is flagged `ours`, has no `nameZh`, and the showroom says
 * "Voltway colour" beside its name, so a visitor is never told a maker sells it. They always follow the
 * maker's own paints in a car's list (the swatch row draws a hairline between the two).
 *
 * A car picks the few it carries with `ownPaints(...)`; the options differ from car to car so the nine
 * rows do not repeat each other. The finish values are the same `PaintFinish` the maker colours use.
 *
 * What the first round taught (2026-11-11): bright, fully saturated gloss colours (a signal red, a
 * lime, a lemon) render garishly under the studio's white cove and the owner rejected nearly all of
 * them. What reads well is DEEP colour under the same glossy, part-metallic coat as the Voyah's
 * Sunleap Red (metalness 0.40, roughness 0.26, full clear coat): the burnt orange, saffron gold, racing
 * green and sapphire blue below are that recipe in the other hues (hand-tuned on the Voyah, 2026-11-16),
 * and the neutrals are metallic greys, tans and browns.
 *
 * A matt paint drops the clear coat to nothing and roughens a part-metallic base. Why part-metallic: a
 * fully dielectric rough paint turns flat in the studio (the diffuse light of its white cove is even all
 * round, so the shape disappears); a little metalness lets the softboxes' blurred reflections model the
 * bonnet, shoulders and flanks, which is what a frozen or matt-wrapped car shows.
 */

/** Sunleap Red's coat (voyah-passion-s.ts): the deep, glossy, part-metallic look the owner liked. */
const DEEP = { roughness: 0.26, metalness: 0.4, clearcoat: 1, clearcoatRoughness: 0.03 } as const;
const METALLIC = { roughness: 0.28, metalness: 0.5, clearcoat: 1, clearcoatRoughness: 0.03 } as const;
const SATIN_METAL = { roughness: 0.3, metalness: 0.4, clearcoat: 1, clearcoatRoughness: 0.03 } as const;
const PEARL = { roughness: 0.28, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.035 } as const;

/**
 * A matt paint: no clear coat to speak of and a rough part-metallic base. No sheen lobe: at the weight a matt paint
 * would use it is invisible, and a car whose own paint has none would recompile its shader the first time it
 * was picked.
 */
function matt(color: string): PaintFinish {
  return { color, roughness: 0.5, metalness: 0.35, clearcoat: 0, clearcoatRoughness: 0.5 };
}

interface Own {
  name: string;
  kind: PaintKind;
  finish: PaintFinish;
}

const own = (name: string, kind: PaintKind, finish: PaintFinish): Own => ({ name, kind, finish });

export const OWN_PAINTS = {
  // ---- deep colours in Sunleap Red's coat
  'ember-orange': own('Ember Orange', 'metallic', { color: '#a84a14', ...DEEP }),
  'saffron-gold': own('Saffron Gold', 'metallic', { color: '#b38512', ...DEEP }),
  'racing-green': own('Racing Green', 'metallic', { color: '#0c4a2f', ...DEEP }),
  'sapphire-blue': own('Sapphire Blue', 'metallic', { color: '#112a66', ...DEEP }),
  'garnet-red': own('Garnet Red', 'metallic', { color: '#7d1219', ...DEEP }),
  // kept from the first round (the owner marked them Keep)
  'candy-red': own('Candy Red', 'metallic', { color: '#a40d24', ...METALLIC }),
  'amber-orange': own('Amber Orange', 'metallic', { color: '#ff8f00', ...METALLIC }),
  // ---- neutral and muted / dark
  graphite: own('Graphite', 'metallic', { color: '#3b3f45', ...METALLIC, metalness: 0.55 }),
  'stone-taupe': own('Stone Taupe', 'metallic', { color: '#7d7367', ...SATIN_METAL }),
  'champagne-sand': own('Champagne Sand', 'metallic', { color: '#b5a98f', ...METALLIC }),
  'mocha-brown': own('Mocha Brown', 'metallic', { color: '#4a3629', ...METALLIC, metalness: 0.45 }),
  'petrol-teal': own('Petrol Teal', 'metallic', { color: '#1f4a52', ...METALLIC, metalness: 0.45 }),
  aubergine: own('Aubergine', 'metallic', { color: '#2d1936', ...METALLIC, metalness: 0.45 }),
  'ceramic-ivory': own('Ceramic Ivory', 'pearl', { color: '#e6e0d0', ...PEARL }),
  // ---- matt
  'matt-grey': own('Matt Cement Grey', 'matt', matt('#7c7f84')),
  'matt-black': own('Matt Black', 'matt', matt('#1a1b1d')),
  'matt-white': own('Matt White', 'matt', matt('#e4e4e0')),
  'matt-olive': own('Matt Olive Green', 'matt', matt('#5c6742')),
  'matt-red': own('Matt Red', 'matt', matt('#b1111b')),
  'matt-orange': own('Matt Orange', 'matt', matt('#ea5a0c')),
  'matt-yellow': own('Matt Yellow', 'matt', matt('#e8b100')),
} satisfies Record<string, Own>;

export type OwnPaintId = keyof typeof OWN_PAINTS;

/** The chosen own paints as the car's `PaintOption`s, in the order given (the ids are prefixed `voltway-`). */
export function ownPaints(...ids: OwnPaintId[]): PaintOption[] {
  return ids.map((id) => {
    const o: Own = OWN_PAINTS[id];
    return {
      id: `voltway-${id}`,
      name: o.name,
      swatch: o.finish.color,
      finish: o.finish,
      ours: true,
      kind: o.kind,
    };
  });
}
