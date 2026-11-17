// Development aid: opens a list of URLs and saves a screenshot of each.
//   node tests/shots.mjs <out-dir> name=url [name=url ...]
import { mkdirSync } from 'node:fs';
import { chromium } from 'playwright';

const [out, ...targets] = process.argv.slice(2);
const base = process.env.INFOKNOWS_URL ?? 'http://localhost:5173';
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on('console', (message) => {
  if (message.type() === 'error') console.log('console error:', message.text());
});
page.on('pageerror', (error) => console.log('page error:', error.message));
for (const target of targets) {
  const [name, ...rest] = target.split('=');
  await page.goto(base + rest.join('='));
  await page.waitForTimeout(1600);
  await page.screenshot({ path: `${out}/${name}.png` });
  console.log('saved', name);
}
await browser.close();
