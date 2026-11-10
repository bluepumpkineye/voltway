// Renders the Compare view's model list: each car in side view (nose to the right), in a light paint so that it reads on the list's pale
// cards, on a transparent background, from the dev server's capture route (src/app/capture/lineup/[slug]), trimmed and written to
// public/compare/<slug>.webp.
//
//   npm run dev -- -p 3100            (in another terminal)
//   node scripts/compare-shots.mjs [slug ...]        BASE=http://localhost:3100 WIDTH=1400 HEIGHT=520
//
// Needs Playwright (not a dependency of the site: `npx playwright install chromium`, then `NODE_PATH` or a local install) and the
// `sharp` that ships with Next.
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const sharp = require('sharp');

const BASE = process.env.BASE ?? 'http://localhost:3100';
const W = Number(process.env.WIDTH ?? 1400);
const H = Number(process.env.HEIGHT ?? 520);
const out = fileURLToPath(new URL('../public/compare/', import.meta.url));
mkdirSync(out, { recursive: true });

// slug and a light paint (src/data/vehicles/*.ts): white or silver, so that no car is dark on the list
const SHOTS = [
  { slug: 'xiaomi-su7-ultra', paint: 'space-silver' },
  { slug: 'nio-es8', paint: 'cloud-white' },
  { slug: 'xpeng-g9l', paint: 'everest-white' },
  { slug: 'voyah-passion-s', paint: 'starlight-silver' },
  { slug: 'zeekr-7x', paint: 'glacier-silver' },
  { slug: 'avatr-06t', paint: 'snow-white' },
  { slug: 'byd-seal', paint: 'aurora-white' },
  { slug: 'denza-z9', paint: 'aurora-silver' },
  { slug: 'luxeed-rx', paint: 'warm-cloud-white' },
];

const only = process.argv.slice(2);
const todo = only.length ? SHOTS.filter((s) => only.includes(s.slug)) : SHOTS;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const s of todo) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.setDefaultTimeout(240000);
  // a dev server that recompiles reloads an open page: the render takes minutes, so the page does not listen for it
  await page.routeWebSocket(/webpack-hmr/, () => {});
  await page.goto(`${BASE}/capture/lineup/${s.slug}?yaw=90&pitch=3&fill=0.96&paint=${s.paint}`, { waitUntil: 'domcontentloaded', timeout: 240000 });
  await page.waitForFunction(() => window.__lineupReady === true, null, { timeout: 240000 });
  await page.waitForTimeout(800);
  const png = await page.screenshot({ omitBackground: true, timeout: 240000 });
  await page.close();
  const clear = { r: 0, g: 0, b: 0, alpha: 0 };
  const trimmed = await sharp(png).trim({ background: clear, threshold: 8 }).extend({ top: 6, bottom: 6, left: 6, right: 6, background: clear }).resize({ width: 640, withoutEnlargement: true }).toBuffer({ resolveWithObject: true });
  await sharp(trimmed.data).webp({ quality: 88, alphaQuality: 95, effort: 5 }).toFile(`${out}${s.slug}.webp`);
  console.log(`${s.slug}: ${trimmed.info.width}x${trimmed.info.height}`);
}
await browser.close();
