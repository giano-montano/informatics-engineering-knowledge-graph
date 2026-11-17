// Technical walkthrough of CA-11 (the operator panel). It uploads a document,
// so it WRITES IN THE GRAPH: run it on a rehearsal graph, and load and
// reapply afterwards (see the acceptance test plan, CA-11).
//
//   INFOKNOWS_OPERATOR_TOKEN=… node tests/operator-walkthrough.mjs <pdf> <course code> <course name> [--shots <dir>]

import { mkdirSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.INFOKNOWS_URL ?? 'http://localhost:5173';
const TOKEN = process.env.INFOKNOWS_OPERATOR_TOKEN;
const [pdf, code, name, ...rest] = process.argv.slice(2);
const SHOTS = rest.includes('--shots') ? rest[rest.indexOf('--shots') + 1] : null;
if (!TOKEN || !pdf || !code || !name) {
  console.error('usage: INFOKNOWS_OPERATOR_TOKEN=… node tests/operator-walkthrough.mjs <pdf> <course code> <course name> [--shots <dir>]');
  process.exit(2);
}
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const OUT = new URL('./output/', import.meta.url);
mkdirSync(OUT, { recursive: true });

const FINAL = ['completed', 'rejected', 'failed', 'written_not_persisted', 'stopped_by_audit'];
const results = [];
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

async function check(step, expected, probe) {
  let ok = false;
  let seen = '';
  try {
    const result = await probe();
    ok = Boolean(result.ok);
    seen = result.seen;
  } catch (error) {
    seen = error.message.split('\n')[0];
  }
  results.push({ step, expected, ok, seen });
  console.log(`${ok ? 'ok  ' : 'FAIL'} CA-11.${step} ${expected} -> ${String(seen).slice(0, 300)}`);
}

const shot = async (file) => SHOTS && page.screenshot({ path: `${SHOTS}/${file}.png` });
const authorized = (path) => context.request.get(`${BASE}${path}`, { headers: { Authorization: `Bearer ${TOKEN}` } }).then((r) => r.json());

await page.goto(`${BASE}/?panel=operador`);
await check(1, 'Un token inválido se rechaza y no da acceso', async () => {
  await page.fill('#operator-token', 'un-token-que-no-es');
  await page.keyboard.press('Enter');
  const error = await page.locator('#access-error').innerText();
  await shot('O1-acceso-rechazado');
  return { ok: error.includes('rechazó') && (await page.locator('.access').isVisible()) && !(await page.locator('.page').count()), seen: error };
});

await check(2, 'El token del operador da acceso y muestra el estado de la compuerta de auditoría', async () => {
  await page.fill('#operator-token', TOKEN);
  await page.keyboard.press('Enter');
  await page.locator('.gate').waitFor();
  const gate = (await page.locator('.gate').innerText()).replace(/\s+/g, ' ');
  const latest = await authorized('/api/audit-reports/latest');
  await shot('O2-panel-del-operador');
  return { ok: gate.includes(latest.gate.state === 'open' ? 'abierta' : 'cerrada'), seen: gate };
});

let runId = null;
await check(3, 'Subir el sílabo con su tipo, código y nombre de curso registra una corrida nueva, pendiente', async () => {
  const before = (await authorized('/api/runs')).length;
  await page.setInputFiles('#run-file', pdf);
  await page.fill('#run-code', code);
  await page.fill('#run-name', name);
  await page.getByRole('button', { name: 'Registrar la corrida' }).click();
  const banner = await page.locator('.upload .banner').innerText();
  runId = Number(banner.match(/Corrida (\d+)/)?.[1]);
  const runs = await authorized('/api/runs');
  await shot('O3-corrida-registrada');
  return { ok: banner.includes('registrada como pendiente') && runs.length === before + 1 && runs.at(-1).id === runId, seen: banner };
});

await check(4, 'La corrida avanza hasta un estado final, con su duración', async () => {
  const row = page.locator('table.runs tbody tr', { has: page.getByRole('button', { name: `Ver la corrida ${runId}` }) });
  const seen = new Set();
  const started = Date.now();
  // The panel refreshes itself: nothing is clicked while waiting.
  while (Date.now() - started < 20 * 60 * 1000) {
    const status = await row.locator('.badge code').innerText();
    seen.add(status);
    if (FINAL.includes(status)) break;
    await page.waitForTimeout(3000);
  }
  const cells = await row.locator('td').allInnerTexts();
  return { ok: FINAL.includes([...seen].at(-1)) && /\d+ (s|min)/.test(cells.at(-1)), seen: `estados vistos: ${[...seen].join(' → ')}; duración ${cells.at(-1)}` };
});

await check(5, 'La corrida muestra sus descartes, o el aviso de que no hubo, y su reporte de auditoría regla por regla; el estado final es el del almacén operacional', async () => {
  await page.getByRole('button', { name: `Ver la corrida ${runId}` }).click();
  await page.locator('.detail .facts').waitFor();
  const stored = await authorized(`/api/runs/${runId}`);
  const shown = await page.locator('.detail h2 .badge code').innerText();
  await shot('O4-detalle-de-la-corrida');
  await page.getByRole('tab', { name: 'Auditoría de cierre' }).click();
  const rules = await page.locator('.detail table.rules tbody tr').count();
  const audit = await page.locator('.detail').innerText();
  await shot('O5-auditoria-de-cierre');
  await page.getByRole('tab', { name: /Descartes/ }).click();
  const discards = (await page.locator('.detail').innerText()).replace(/\s+/g, ' ');
  const rows = await page.locator('.detail table.rules tbody tr').count();
  await shot('O6-descartes');
  const expectedRules = stored.audit_report ? stored.audit_report.rules.length : 0;
  const stored2 = await authorized(`/api/runs/${runId}/discards`);
  return {
    ok: shown === stored.status && rules === expectedRules && (stored.audit_report ? true : audit.includes('no tiene reporte'))
      && (stored2.discards.length ? rows === stored2.discards.length : /No hubo descartes|sin descartes/.test(discards)),
    seen: `estado ${shown} (almacén: ${stored.status}); ${rules} reglas en la auditoría de cierre; ${stored2.discards.length} descartes`,
  };
});

await browser.close();
const passed = results.filter((r) => r.ok).length;
writeFileSync(new URL('operator-walkthrough.md', OUT), [
  `Recorrido técnico de CA-11 contra ${BASE}: ${passed} de ${results.length}. Corrida ${runId}.`, '',
  '| Paso | Resultado esperado | Resultado | Lo que se vio |', '|---|---|---|---|',
  ...results.map((r) => `| ${r.step} | ${r.expected} | ${r.ok ? 'cumple' : '**no cumple**'} | ${String(r.seen).replace(/\|/g, '/').replace(/\n/g, ' ')} |`),
].join('\n'));
process.exit(passed === results.length ? 0 : 1);
