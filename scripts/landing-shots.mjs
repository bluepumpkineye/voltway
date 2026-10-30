// Renders the landing page's line-up: each car on a transparent background, from the angle of its place in the fan, with the paint
// chosen for it, from the dev server's capture route (src/app/capture/lineup/[slug]), trimmed and written to public/landing/<slug>.webp.
//
//   npm run dev            (in another terminal)
//   node scripts/landing-shots.mjs [slug ...]        BASE=http://localhost:3100 WIDTH=1500 HEIGHT=900
//
// Needs Playwright (not a dependency of the site: `npx playwright install chromium`, then `NODE_PATH` or a local install) and the
// `sharp` that ships with Next. Prints each picture's size and where the car stands in it, which src/lib/landing/lineup.ts records.
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const sharp = require('sharp');

const BASE = process.env.BASE ?? 'http://localhost:3100';
const W = Number(process.env.WIDTH ?? 1500);
const H = Number(process.env.HEIGHT ?? 900);
const out = fileURLToPath(new URL('../public/landing/', import.meta.url));
mkdirSync(out, { recursive: true });

// slug, camera yaw (degrees; the nose points to the right of the picture when positive), pitch (degrees above the horizon), paint (src/data/vehicles/*.ts)
// The fan faces outward: the cars on the left of it have their noses to the left, the ones on the right to the right, and the hero in front
// faces the camera.
const SHOTS = [
  { slug: 'xiaomi-su7-ultra', yaw: 0, pitch: 12, paint: 'lightning-yellow' },
  { slug: 'nio-es8', yaw: -36, paint: 'southern-star-blue' },
  { slug: 'xpeng-g9l', yaw: -28, paint: 'fjord-grey' },
  { slug: 'voyah-passion-s', yaw: 28, paint: 'sunleap-red' },
  { slug: 'zeekr-7x', yaw: 36, paint: 'night-purple' },
  { slug: 'avatr-06t', yaw: -24, paint: 'snow-white' },
  { slug: 'byd-seal', yaw: -14, paint: 'mystic-green' },
  { slug: 'denza-z9', yaw: 14, paint: 'skyline-blue' },
  { slug: 'luxeed-rx', yaw: 24, paint: 'titanium-silver' },
];

const only = process.argv.slice(2);
const todo = only.length ? SHOTS.filter((s) => only.includes(s.slug)) : SHOTS;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const s of todo) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.setDefaultTimeout(240000);
  // a dev server that recompiles reloads an open page: the render takes minutes, so the page does not listen for it
  await page.routeWebSocket(/webpack-hmr/, () => {});
  const url = `${BASE}/capture/lineup/${s.slug}?yaw=${s.yaw}&pitch=${s.pitch ?? 9}&paint=${s.paint}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 240000 });
  await page.waitForFunction(() => window.__lineupReady === true, null, { timeout: 240000 });
  await page.waitForTimeout(800);
  const png = await page.screenshot({ omitBackground: true, timeout: 240000 });
  await page.close();
  // trim to the car (with a little room), so that every picture stands on its own bottom edge
  const trimmed = await sharp(png).trim({ background: { r: 0, g: 0, b: 0, alpha: 0 }, threshold: 8 }).extend({ top: 6, bottom: 6, left: 6, right: 6, background: { r: 0, g: 0, b: 0, alpha: 0 } }).toBuffer({ resolveWithObject: true });
  await sharp(trimmed.data).webp({ quality: 90, alphaQuality: 95, effort: 5 }).toFile(`${out}${s.slug}.webp`);
  console.log(`${s.slug}: ${trimmed.info.width}x${trimmed.info.height}`);
}
await browser.close();
