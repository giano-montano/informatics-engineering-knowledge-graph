// Technical walkthrough of CA-01 to CA-10 of the acceptance test plan
// (casos-de-prueba/plan-de-pruebas-de-aceptacion-r6.md), against the real
// API, once with the pointer and once with the keyboard alone.
//
// It is a check before the acceptance test, not the test: that one is run
// with the advisor and three users. The cases are the generic ones of the
// plan and SHEET is its data sheet: with another graph, only SHEET changes.
//
//   node tests/walkthrough.mjs [--shots <dir>] [--only pointer|keyboard]
//
// INFOKNOWS_URL is where the application answers (default: the Vite server).

import { mkdirSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.INFOKNOWS_URL ?? 'http://localhost:5173';
const args = process.argv.slice(2);
const option = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
const SHOTS = option('--shots');
const ONLY = option('--only');
const CASE = option('--case');
const OUT = new URL('./output/', import.meta.url);
mkdirSync(OUT, { recursive: true });
if (SHOTS) mkdirSync(SHOTS, { recursive: true });

const results = [];
const notes = new Set();
let mode = 'pointer';
let page;
let context;

function record(id, step, expected, ok, seen = '') {
  results.push({ mode, id, step, expected, ok, seen: String(seen).slice(0, 320) });
  console.log(`${ok ? 'ok  ' : 'FAIL'} [${mode}] ${id}.${step} ${expected}${ok ? '' : ` -> ${String(seen).slice(0, 700)}`}`);
}

async function check(id, step, expected, probe) {
  try {
    const seen = await probe();
    record(id, step, expected, seen === true || (seen && seen.ok), seen === true ? '' : seen?.seen ?? seen);
  } catch (error) {
    record(id, step, expected, false, error.message.split('\n')[0]);
  }
}

const has = (text, ...parts) => ({ ok: parts.every((part) => text.includes(part)), seen: text });

// --- Driving the application ------------------------------------------------------

async function settle() {
  await page.waitForFunction(() => document.querySelector('#canvas-region')?.getAttribute('aria-busy') === 'false');
  await page.waitForFunction(() => !document.querySelector('#focus-panel .loading'));
  await page.waitForTimeout(900);
}

async function shot(name) {
  if (SHOTS && mode === 'pointer') await page.screenshot({ path: `${SHOTS}/${name}.png` });
}

/** Presses Tab until the element has the keyboard focus. */
async function tabTo(locator, limit = 400) {
  const handle = await locator.first().elementHandle();
  if (!handle) throw new Error(`no element to tab to: ${locator}`);
  for (let i = 0; i < limit; i += 1) {
    if (await handle.evaluate((element) => element === document.activeElement)) return;
    await page.keyboard.press('Tab');
  }
  throw new Error(`Tab never reached ${locator}`);
}

async function activate(locator) {
  if (mode === 'pointer') await locator.first().click();
  else {
    await tabTo(locator);
    await page.keyboard.press('Enter');
  }
}

async function goHome() {
  await page.goto(BASE);
  await page.waitForSelector('svg.graph g.node');
  await settle();
}

async function search(text) {
  if (mode === 'pointer') await page.click('#search-input');
  else await page.keyboard.press('Control+k');
  await page.keyboard.press('Control+a');
  await page.keyboard.type(text);
  await page.waitForFunction(() => {
    const box = document.querySelector('#search-results');
    return box && !box.textContent.includes('Buscando');
  });
  await page.waitForTimeout(350);
}

async function options() {
  return page.$$eval('#search-results [role=option]', (items) => items.map((item) => ({
    name: item.querySelector('.name').childNodes[0].textContent.trim(),
    kind: item.querySelector('.class-chip').textContent.trim(),
    layer: item.querySelector('.layer').textContent.trim(),
  })));
}

async function choose(name, kind) {
  const list = await options();
  const index = list.findIndex((item) => item.name === name && item.kind === kind);
  if (index < 0) throw new Error(`«${name}» (${kind}) is not among the results`);
  if (mode === 'pointer') await page.click(`#search-option-${index}`);
  else {
    for (let i = 0; i < index; i += 1) await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
  }
  await settle();
}

async function open(query, name, kind) {
  await search(query);
  await choose(name, kind);
}

async function lens(name) {
  const tab = page.getByRole('tab', { name, exact: true });
  if (mode === 'pointer') await tab.click();
  else {
    await tabTo(page.locator('.lenses [role=tab][aria-selected=true]'));
    for (let i = 0; i < 9 && (await tab.getAttribute('aria-selected')) !== 'true'; i += 1) {
      await page.keyboard.press('ArrowRight');
      await settle();
    }
  }
  await settle();
}

async function grain(name) {
  const radio = page.getByRole('radio', { name, exact: true });
  if (mode === 'pointer') await radio.click();
  else {
    await tabTo(page.locator('.grains [role=radio][aria-checked=true]'));
    for (let i = 0; i < 4 && (await radio.getAttribute('aria-checked')) !== 'true'; i += 1) {
      await page.keyboard.press('ArrowRight');
      await settle();
    }
  }
  await settle();
}

const node = (label) => page.locator(`svg.graph g.node[aria-label^="${label}"]`);

async function mapNodes() {
  return page.$$eval('svg.graph g.node', (items) => items.map((item) => ({
    label: item.getAttribute('aria-label'),
    name: item.__data__.node.name_es,
    tone: item.__data__.tone,
    layer: item.__data__.node.layer,
    kind: item.__data__.node.label,
  })));
}

const captions = () => page.$$eval('svg.graph .caption', (items) => items.map((item) => item.textContent));
const answer = () => page.locator('.context .says').innerText();
const how = () => page.locator('.context .how').innerText().catch(() => '');
const title = () => page.locator('.context h1').innerText();
const panel = () => page.locator('#focus-panel').innerText();
const section = (heading) => page.locator('#focus-panel section', { has: page.getByRole('heading', { name: heading }) });

async function clickEdge(sourceName, targetName) {
  const point = await page.evaluate(([source, target]) => {
    for (const element of document.querySelectorAll('svg.graph g.edge')) {
      const drawn = element.__data__;
      if (!drawn.edge) continue;
      const names = [...document.querySelectorAll('svg.graph g.node')].map((n) => n.__data__);
      const from = names.find((n) => n.key === drawn.edge.source)?.node.name_es;
      const to = names.find((n) => n.key === drawn.edge.target)?.node.name_es;
      if (from !== source || to !== target) continue;
      const path = element.querySelector('.edge-hit');
      const middle = path.getPointAtLength(path.getTotalLength() / 2);
      const matrix = path.getScreenCTM();
      return { x: middle.x * matrix.a + middle.y * matrix.c + matrix.e, y: middle.x * matrix.b + middle.y * matrix.d + matrix.f };
    }
    return null;
  }, [sourceName, targetName]);
  if (!point) throw new Error(`no line from «${sourceName}» to «${targetName}» on the map`);
  await page.mouse.click(point.x, point.y);
}

async function api(path, params = {}) {
  const response = await context.request.get(`${BASE}${path}?${new URLSearchParams(params)}`);
  return response.json();
}

async function keyOf(query, name, label) {
  const found = await api('/api/search', { q: query });
  return found.nodes.find((n) => n.name_es === name && n.label === label)?.key;
}

/** Opens a document link and says what the server answered at its address. */
async function openDocument(link) {
  const href = await link.first().getAttribute('href');
  const target = await link.first().getAttribute('target');
  const [popup] = await Promise.all([context.waitForEvent('page'), activate(link)]);
  // A headless browser does not render the PDF, so the new tab is checked by
  // its existence and the document by what the server answers at its address.
  await popup.close();
  const response = await context.request.get(new URL(href, BASE).href);
  return { href, tab: target === '_blank' && Boolean(popup), status: response.status(), type: response.headers()['content-type'] ?? '' };
}

// --- The data sheet ---------------------------------------------------------------

// Sheet 2 of the plan: the graph of the final run (CS2023 and the 13 syllabi).
// With another graph, this object is what changes; the cases below do not.
const SHEET = {
  search: 'memoria',
  noMatch: 'compiladores',
  topic: 'ADMINISTRACIÓN DE MEMORIA',
  concept: 'Memoria virtual',
  prerequisite: 'Paginación',
  free: 'Memoria',
  syllabus: 'Sílabo 1INF29',
  course: { name: 'Sistemas Operativos', code: '1INF29' },
  area: 'Sistemas Operativos',
  wideArea: { name: 'Fundamentos Algorítmicos', syllabi: ['Sílabo 1INF24', 'Sílabo 1INF27', 'Sílabo 1INF32'] },
  general: 'Llamadas al sistema',
  unit: 'Gestión de Memoria',
  chain: 'Sistemas Operativos › Gestión de Memoria › ADMINISTRACIÓN DE MEMORIA',
  whyStop: 'Programación 2',
  expected: { courses: 13, litAreas: 10, results: 11, neighbors: 9, concepts: 7, steps: 6 },
};

const sorted = (list) => [...list].sort((a, b) => a.localeCompare(b));
const same = (a, b) => JSON.stringify(sorted(a)) === JSON.stringify(sorted(b));
const openTopic = () => open(SHEET.search, SHEET.topic, 'Tema');
const openConcept = () => open(SHEET.concept.toLowerCase(), SHEET.concept, 'Concepto');
const openCourse = () => open(SHEET.course.name.toLowerCase(), SHEET.course.name, 'Curso');

// --- The cases --------------------------------------------------------------------

async function ca01() {
  await goHome();
  await shot('A-inicio');
  await check('CA-01', 1, 'El inicio muestra las 17 áreas y los cursos con sílabo; las áreas con temas se distinguen, con sus cifras', async () => {
    const nodes = await mapNodes();
    const areas = nodes.filter((n) => n.kind === 'KnowledgeArea');
    const courses = nodes.filter((n) => n.kind === 'Course');
    const lit = areas.filter((n) => n.tone === 'main');
    const overview = await api('/api/overview');
    const expected = overview.nodes.filter((n) => n.label === 'KnowledgeArea' && n.topics > 0);
    const figures = await page.$$eval('svg.graph g.node-main.class-KnowledgeArea .sub', (items) => items.map((i) => i.textContent));
    const text = await panel();
    return {
      ok: areas.length === 17 && courses.length === overview.nodes.filter((n) => n.label === 'Course').length
        && courses.length === SHEET.expected.courses && lit.length === expected.length && lit.length === SHEET.expected.litAreas
        && figures.length === lit.length && figures.every((f) => /tema.* · .*concepto/.test(f)) && text.includes(`${lit.length} de 17`),
      seen: `${areas.length} áreas, ${courses.length} cursos, ${lit.length} áreas con temas; ${figures[0]}`,
    };
  });
  await search(SHEET.search);
  await shot('B1-busqueda');
  await check('CA-01', 2, 'La búsqueda lista hasta 20 coincidencias, cada una con su clase y su origen en texto', async () => {
    const list = await options();
    return {
      ok: list.length === SHEET.expected.results && list.length <= 20 && list.every((item) => item.kind && /CS2023|Sílabo PUCP/.test(item.layer)),
      seen: `${list.length} resultados para «${SHEET.search}»: ${list.map((i) => `${i.name} (${i.kind}, ${i.layer})`).join('; ')}`,
    };
  });
  await check('CA-01', 3, 'Elegir el tema lo pone en foco, en el mapa y en la ficha', async () => {
    await choose(SHEET.topic, 'Tema');
    const focus = await page.locator('svg.graph g.node[aria-current=true]').getAttribute('aria-label');
    const heading = await page.locator('#focus-panel h2').innerText();
    return { ok: (await title()) === SHEET.topic && focus.startsWith(`Tema ${SHEET.topic}`) && heading === SHEET.topic, seen: focus };
  });
  await search(SHEET.noMatch);
  await shot('B2-busqueda-sin-resultados');
  await check('CA-01', 4, 'Un texto sin coincidencias: el sistema lo dice y ofrece ver las áreas', async () => {
    const text = await page.locator('#search-results').innerText();
    const offered = await page.getByRole('button', { name: 'Ver las áreas' }).isVisible();
    return { ok: text.includes(`Ningún sílabo cargado trata «${SHEET.noMatch}»`) && offered && (await options()).length === 0, seen: text };
  });
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
}

async function ca02() {
  await goHome();
  await openTopic();
  await shot('C-foco-lo-que-lo-rodea');
  await check('CA-02', 1, 'Vecinos directos con el nombre de cada relación, y algunos vecinos de esos vecinos, apagados; cada vecino del mapa está en «Conexiones»', async () => {
    const heads = await captions();
    const nodes = await mapNodes();
    const far = nodes.filter((n) => n.tone === 'far');
    const says = await answer();
    // Opens every group of the list, as a reader would to see it whole.
    await section('Conexiones').locator('details').evaluateAll((items) => items.forEach((item) => { item.open = true; }));
    const listed = await section('Conexiones').innerText();
    const missing = nodes.filter((n) => n.tone !== 'focus' && !listed.includes(n.name)).map((n) => n.name);
    return {
      ok: heads.some((h) => h.startsWith('Contiene')) && heads.includes('Es parte de') && heads.includes('Material de estudio')
        && far.length > 0 && missing.length === 0 && (await node(`Unidad ${SHEET.unit}`).count()) === 1
        && says.includes(`${SHEET.expected.neighbors} elementos`),
      seen: `${says} Rótulos: ${heads.join(', ')}. Apagados: ${far.length}. Fuera de «Conexiones»: ${missing.join(', ') || 'ninguno'}`,
    };
  });
  await check('CA-02', 2, 'Pasar a uno de sus conceptos lo pone en foco y lo visitado suma un paso', async () => {
    await activate(node(`Concepto ${SHEET.concept}`));
    await settle();
    const trail = await page.$$eval('.trail ol li', (items) => items.map((i) => i.textContent.trim()));
    return { ok: (await title()) === SHEET.concept && trail.length === 2, seen: `Visitado: ${trail.join(' › ')}` };
  });
  await check('CA-02', 3, 'Volver al tema lo pone otra vez en foco, con sus vecinos', async () => {
    if (mode === 'pointer') await page.click('.step-back');
    else await page.keyboard.press('Alt+ArrowLeft');
    await settle();
    const heads = await captions();
    return { ok: (await title()) === SHEET.topic && heads.some((h) => h.startsWith('Contiene')), seen: await title() };
  });
  await check('CA-02', 4, 'El + de un vecino agrega sus conexiones al mapa, con nombre, y el foco no cambia', async () => {
    const before = (await mapNodes()).length;
    const expandable = page.locator('svg.graph g.node:has(.plus)').first();
    const name = await expandable.evaluate((element) => element.__data__.node.name_es);
    if (mode === 'pointer') await expandable.locator('.plus').click();
    else {
      await tabTo(expandable);
      await page.keyboard.press('+');
    }
    await page.waitForFunction((count) => document.querySelectorAll('svg.graph g.node').length > count, before);
    await settle();
    const heads = await captions();
    const after = (await mapNodes()).length;
    await shot('C2-conexiones-traidas-con-mas');
    return {
      ok: after > before && (await title()) === SHEET.topic && heads.some((h) => h.startsWith(`Conexiones de «${name}»`)),
      seen: `+ en «${name}»: de ${before} a ${after} puntos; ${heads.find((h) => h.startsWith('Conexiones de'))}`,
    };
  });
}

async function ca03() {
  await goHome();
  await openConcept();
  await lens('Qué necesitas antes');
  await shot('D2-que-necesitas-antes');
  await check('CA-03', 1, 'Prerrequisitos ordenados por distancia, sin uno de más ni de menos frente a la API', async () => {
    const key = await keyOf(SHEET.concept, SHEET.concept, 'Concept');
    const response = await api('/api/concepts/prerequisites', { key });
    const expected = response.nodes.filter((n) => n.depth >= 1).map((n) => `${n.depth}:${n.name_es}`).sort();
    const groups = await section('Qué necesitas antes').evaluate((element) => {
      const found = [];
      let depth = 0;
      for (const child of element.children) {
        if (child.tagName === 'H4') depth = child.textContent.includes('Justo') ? 1 : Number.parseInt(child.textContent, 10);
        if (child.tagName === 'UL') for (const item of child.querySelectorAll('.name')) found.push(`${depth}:${item.textContent}`);
      }
      return found.sort();
    });
    const onMap = (await mapNodes()).filter((n) => n.tone !== 'focus').map((n) => n.name);
    const heads = await captions();
    return {
      ok: JSON.stringify(groups) === JSON.stringify(expected) && same(onMap, expected.map((e) => e.slice(2)))
        && expected.includes(`1:${SHEET.prerequisite}`) && expected.some((e) => !e.startsWith('1:')) && heads.includes('Justo antes'),
      seen: `Ficha: ${groups.join(', ')}. API: ${expected.join(', ')}. Columnas: ${heads.join(', ')}`,
    };
  });
  await check('CA-03', 2, 'Por qué su prerrequisito directo va antes: la relación con su fuente', async () => {
    if (mode === 'pointer') await clickEdge(SHEET.concept, SHEET.prerequisite);
    else await activate(page.getByRole('button', { name: `Ver la fuente de la relación con ${SHEET.prerequisite}` }));
    const card = page.locator('#selected-relation');
    await card.waitFor();
    await page.waitForTimeout(400);
    await shot('F1-relacion-seleccionada');
    const text = (await card.innerText()).replace(/\s+/g, ' ');
    return has(text, SHEET.concept, 'necesita antes', SHEET.prerequisite, 'Lo dice', SHEET.syllabus);
  });
  await check('CA-03', 3, 'Un concepto sin prerrequisitos: no necesita nada antes, y se muestra qué depende de él', async () => {
    await open(SHEET.free.toLowerCase(), SHEET.free, 'Concepto');
    await lens('Qué necesitas antes');
    const key = await keyOf(SHEET.free, SHEET.free, 'Concept');
    const around = await api('/api/nodes', { key });
    const dependents = around.edges.filter((e) => e.type === 'HAS_PREREQUISITE' && e.target === key)
      .map((e) => around.nodes.find((n) => n.key === e.source).name_es);
    const says = await answer();
    const drawn = (await mapNodes()).map((n) => n.name);
    return {
      ok: says.includes('no necesita nada antes') && dependents.length > 0 && dependents.every((name) => drawn.includes(name)),
      seen: `${says} Dependen de él: ${dependents.join(', ')}`,
    };
  });
}

async function ca04() {
  await goHome();
  await openCourse();
  await lens('Cursos que conviene llevar antes');
  await shot('D5-cursos-que-conviene-llevar-antes');
  const part = section('Cursos que conviene llevar antes');
  const key = await keyOf(SHEET.course.name, SHEET.course.name, 'Course');
  const response = await api('/api/courses/prerequisites', { key });
  const named = (k) => response.nodes.find((n) => n.key === k);
  await check('CA-04', 1, 'Lo que el curso pide y lo que enseña, con su nombre en la ficha', async () => {
    const names = (type) => response.edges.filter((e) => e.type === type && e.source === key).map((e) => named(e.target).name_es).sort();
    const text = await part.innerText();
    const required = names('REQUIRES_CONCEPT');
    const taught = names('TEACHES_CONCEPT');
    return {
      ok: required.length > 0 && required.every((name) => text.includes(name)) && taught.every((name) => text.includes(name))
        && text.includes(`Lo que pide · ${required.length}`) && (await how()).includes(`${taught.length} conceptos`),
      seen: `Pide: ${required.join(', ')}. Enseña: ${taught.length}, todos con nombre en la ficha`,
    };
  });
  await check('CA-04', 2, 'Los cursos que conviene llevar antes, cada uno con los conceptos que lo justifican y la fuente de cada uno', async () => {
    const expected = response.nodes.filter((n) => n.label === 'Course' && n.key !== key);
    const previous = part.locator('.previous');
    const blocks = (await previous.allInnerTexts()).map((t) => t.replace(/\s+/g, ' '));
    const counts = await previous.evaluateAll((items) => items.map((item) => [item.querySelectorAll('.list > li').length, item.querySelectorAll('.source').length]));
    await activate(previous.first().locator('.source'));
    const card = (await page.locator('#selected-relation').innerText()).replace(/\s+/g, ' ');
    return {
      ok: expected.length > 0 && blocks.length === expected.length
        && expected.every((course) => blocks.some((b) => b.includes(course.name_es) && b.includes(course.course_code)))
        && counts.every(([items, sources]) => items >= 1 && sources === items) && /Lo dice .*Sílabo/.test(card),
      seen: `${blocks.join(' · ')} · tarjeta: ${card}`,
    };
  });
}

async function ca05() {
  await goHome();
  await openConcept();
  await lens('Dónde está en la carrera');
  await shot('D3-donde-esta-en-la-carrera');
  await check('CA-05', 1, 'La cadena área › unidad › tema, y cada eslabón con su capa', async () => {
    const says = await answer();
    const nodes = await mapNodes();
    const layers = Object.fromEntries(nodes.map((n) => [n.kind, n.label]));
    const chain = await section('Dónde está en la carrera').locator('.chain li').allInnerTexts();
    return {
      ok: says.includes(SHEET.chain)
        && layers.KnowledgeArea.includes('de CS2023') && layers.KnowledgeUnit.includes('de CS2023')
        && layers.Topic.includes('de un sílabo') && layers.Concept.includes('de un sílabo')
        && nodes.filter((n) => n.layer === 'reference').length === 2 && chain.length === 4,
      seen: `${says} Mapa: ${nodes.map((n) => n.label.split('.')[0]).join(' | ')}`,
    };
  });
}

async function ca06() {
  await goHome();
  await openTopic();
  await lens('Qué contiene');
  await shot('D1-que-contiene-tema');
  await check('CA-06', 1, 'Los conceptos del tema', async () => {
    const concepts = (await mapNodes()).filter((n) => n.kind === 'Concept');
    return { ok: concepts.length === SHEET.expected.concepts && (await answer()).includes(`${SHEET.expected.concepts} conceptos`), seen: await answer() };
  });
  await check('CA-06', 2, 'Los conceptos en pasos según sus prerrequisitos internos; ninguno antes que uno de sus prerrequisitos', async () => {
    const steps = await section('Qué contiene').locator('.steps > li').evaluateAll((items) => items.map((item) => [...item.querySelectorAll('.name')].map((n) => n.textContent)));
    const key = await keyOf(SHEET.search, SHEET.topic, 'Topic');
    const response = await api('/api/elements/location', { key });
    const stepOf = new Map(steps.flatMap((names, index) => names.map((name) => [name, index])));
    const name = (k) => response.nodes.find((n) => n.key === k).name_es;
    const inside = response.edges.filter((e) => e.type === 'HAS_PREREQUISITE' && stepOf.has(name(e.source)) && stepOf.has(name(e.target)));
    const broken = inside.filter((e) => stepOf.get(name(e.source)) <= stepOf.get(name(e.target)));
    const heads = await captions();
    return {
      ok: steps.length === SHEET.expected.steps && stepOf.size === SHEET.expected.concepts && inside.length > 0 && broken.length === 0
        && heads.includes(`Paso ${steps.length}`),
      seen: steps.map((names, index) => `Paso ${index + 1}: ${names.join(', ')}`).join(' · '),
    };
  });
  await check('CA-06', 3, 'El área, nivel por nivel, con sus cifras; si no cabe, el mapa llega hasta los temas y lo dice', async () => {
    await open(SHEET.area.toLowerCase(), SHEET.area, 'Área');
    await lens('Qué contiene');
    await shot('D6-que-contiene-area');
    const says = await answer();
    const nodes = await mapNodes();
    const overview = await api('/api/overview');
    const area = overview.nodes.find((n) => n.name_es === SHEET.area && n.label === 'KnowledgeArea');
    const figures = `${area.units} unidades, ${area.topics} temas y ${area.concepts} conceptos`;
    const reading = await how();
    const whole = nodes.filter((n) => n.kind === 'Concept').length === area.concepts;
    const units = nodes.filter((n) => n.kind === 'KnowledgeUnit').length;
    // Many units without topics go in one line of the map, and the reading says so.
    return {
      ok: says.includes(figures) && (units === area.units || (units < area.units && reading.includes('unidades sin temas')))
        && nodes.filter((n) => n.kind === 'Topic').length === area.topics && (whole || reading.includes('llega hasta los temas')),
      seen: `${says} ${await how()}`,
    };
  });
}

async function ca07() {
  await goHome();
  await openTopic();
  const part = section('Material de estudio');
  await check('CA-07', 1, 'El material del tema, con su tipo', async () => has((await part.innerText()).replace(/\s+/g, ' '), `Abrir ${SHEET.syllabus}`, 'Sílabo'));
  await check('CA-07', 2, 'El PDF del sílabo abre en una pestaña nueva, y es el del curso indicado', async () => {
    const found = await api('/api/search', { q: SHEET.course.code });
    const course = found.nodes.find((n) => n.label === 'Course' && n.course_code === SHEET.course.code);
    const source = found.edges.find((e) => e.type === 'WAS_DERIVED_FROM' && e.source === course.key).target;
    const opened = await openDocument(part.locator('a.doc'));
    return {
      ok: opened.href === `/resources/${source}` && opened.status === 200 && opened.type.includes('application/pdf') && opened.tab,
      seen: `${opened.href} → ${opened.status} ${opened.type}; pestaña nueva: ${opened.tab ? 'sí' : 'no'}`,
    };
  });
  await check('CA-07', 3, 'Un concepto no tiene material propio: se ofrece el de su tema', async () => {
    await openConcept();
    const text = (await part.innerText()).replace(/\s+/g, ' ');
    const offer = page.getByRole('button', { name: /Ver el material de su tema/ });
    const visible = await offer.isVisible();
    await activate(offer);
    await settle();
    return { ok: text.includes('no tiene material propio') && visible && (await title()) === SHEET.topic, seen: text };
  });
  await check('CA-07', 4, 'Un área: los sílabos que tratan sobre sus partes, cada uno con el tema por el que llega', async () => {
    await open(SHEET.wideArea.name.toLowerCase(), SHEET.wideArea.name, 'Área');
    await lens('Material de estudio');
    await shot('D7-material-de-estudio');
    const entries = await part.locator('.resource').evaluateAll((items) => items.map((item) => ({
      name: item.querySelector('a.doc span').textContent, reached: item.querySelectorAll('.about button').length,
    })));
    return {
      ok: entries.length === SHEET.wideArea.syllabi.length && entries.every((e) => e.reached >= 1)
        && SHEET.wideArea.syllabi.every((n) => entries.some((e) => e.name.includes(n))),
      seen: entries.map((e) => `${e.name}, por ${e.reached} temas`).join(' · '),
    };
  });
}

async function ca08() {
  await goHome();
  await openConcept();
  await lens('Camino hasta aquí');
  await grain('curso');
  await shot('D4-camino-hasta-aqui-por-curso');
  const key = await keyOf(SHEET.concept, SHEET.concept, 'Concept');
  const stops = () => page.$$eval('.stops .stop', (items) => items.map((item) => item.innerText.replace(/\s+/g, ' ').replace(' ¿Por qué?', '')));
  const needed = async () => sorted((await mapNodes()).filter((n) => n.kind === 'Concept' && n.tone !== 'focus').map((n) => n.name)).join(', ');
  const lifted = async (grainName, label) => (await api('/api/learning-path', { key, grain: grainName })).nodes
    .filter((n) => n.label === label && n.depth >= 1).map((n) => n.name_es);
  const covers = (list, names) => list.length === names.length && names.every((name) => list.some((s) => s.includes(name)));
  const seenNeeded = [];
  await check('CA-08', 1, 'Por cursos: los cursos por los que conviene pasar, por distancia, y los conceptos que se necesitan antes', async () => {
    const list = await stops();
    seenNeeded.push(await needed());
    const path = await api('/api/learning-path', { key, grain: 'course' });
    const courses = path.nodes.filter((n) => n.label === 'Course' && n.depth >= 1);
    const concepts = sorted(path.nodes.filter((n) => n.label === 'Concept' && n.depth >= 1).map((n) => n.name_es)).join(', ');
    const groups = await page.locator('.stops .group').count();
    return {
      ok: courses.length > 1 && covers(list, courses.map((c) => c.name_es)) && courses.every((c) => list.some((s) => s.includes(c.course_code)))
        && groups === new Set(courses.map((c) => c.depth)).size && seenNeeded[0] === concepts,
      seen: `Paradas: ${list.join(' · ')} (${groups} distancias). Abajo: ${seenNeeded[0]}`,
    };
  });
  await check('CA-08', 2, 'Por temas y por áreas; una parada que contiene a la meta lo dice; los conceptos no cambian', async () => {
    await grain('tema');
    const topics = await stops();
    seenNeeded.push(await needed());
    await grain('área');
    const areas = await stops();
    seenNeeded.push(await needed());
    return {
      ok: covers(topics, await lifted('topic', 'Topic')) && topics.some((s) => s.includes(SHEET.topic) && s.includes('el mismo tema'))
        && covers(areas, await lifted('area', 'KnowledgeArea')) && areas.some((s) => s.includes(SHEET.area) && s.includes('la misma área'))
        && new Set(seenNeeded).size === 1,
      seen: `Temas: ${topics.join(' · ')}. Áreas: ${areas.join(' · ')}. Conceptos en las tres: ${[...new Set(seenNeeded)].join(' / ')}`,
    };
  });
  await check('CA-08', 3, 'Por qué pasar por un curso: las relaciones que lo justifican, cada una con su fuente', async () => {
    await grain('curso');
    await activate(page.getByRole('button', { name: new RegExp(`¿Por qué pasar por ${SHEET.whyStop}`) }));
    const card = page.locator('#focus-panel .card');
    await card.waitFor();
    await page.waitForTimeout(500);
    await shot('F2-por-que-de-una-parada');
    const flat = (await card.locator('.why-steps > li').allInnerTexts()).map((s) => s.replace(/\s+/g, ' '));
    return {
      ok: flat.length >= 2 && new RegExp(`${SHEET.whyStop}.*enseña.*Sílabo`).test(flat[0])
        && flat.slice(1).every((line) => /necesita antes.*Sílabo/.test(line)),
      seen: flat.join(' · '),
    };
  });
  await check('CA-08', 4, 'Con un curso como meta: el camino, o el aviso de que sale vacío, y la remisión a «Cursos que conviene llevar antes»', async () => {
    await openCourse();
    await lens('Camino hasta aquí');
    const says = await answer();
    const offer = page.getByRole('button', { name: /Ver «Cursos que conviene llevar antes»/ });
    const visible = await offer.isVisible();
    await activate(offer);
    await settle();
    const selected = await page.locator('.lenses [aria-selected=true]').innerText();
    return {
      ok: (says.includes('no hay camino previo') || says.includes('los conceptos que el curso enseña')) && says.includes('otra pregunta')
        && visible && selected === 'Cursos que conviene llevar antes',
      seen: says,
    };
  });
}

async function ca09() {
  await goHome();
  const key = await keyOf(SHEET.general, SHEET.general, 'Concept');
  const response = await api('/api/concepts/specializations', { key });
  const expected = response.edges.filter((e) => e.type === 'SPECIALIZES' && e.target === key)
    .map((e) => response.nodes.find((n) => n.key === e.source).name_es);
  await check('CA-09', 1, 'Buscar el concepto general y abrirlo lo pone en foco', async () => {
    await open(SHEET.general.toLowerCase(), SHEET.general, 'Concepto');
    return { ok: (await title()) === SHEET.general, seen: await title() };
  });
  await check('CA-09', 2, 'Sus tipos', async () => {
    await lens('Tipos');
    await shot('D8-tipos');
    const kinds = (await mapNodes()).filter((n) => n.tone !== 'focus').map((n) => n.name);
    const listed = await section('Tipos').innerText();
    return {
      ok: expected.length >= 2 && same(kinds, expected) && kinds.every((k) => listed.includes(k)),
      seen: `${await answer()} Mapa: ${sorted(kinds).join(', ')}`,
    };
  });
  await check('CA-09', 3, 'Pasar a uno de sus tipos: es un tipo del concepto general', async () => {
    const kind = sorted(expected)[0];
    await activate(node(`Concepto ${kind}`));
    await settle();
    const says = await answer();
    return { ok: (await title()) === kind && says.includes(`es un tipo de ${SHEET.general}`), seen: says };
  });
  await check('CA-09', 4, 'Un concepto sin tipos: el sistema dice que no tiene tipos registrados', async () => {
    await openConcept();
    await lens('Tipos');
    const says = await answer();
    return { ok: says.includes('ni tiene tipos registrados'), seen: says };
  });
}

async function ca10() {
  await goHome();
  await openConcept();
  await lens('Qué necesitas antes');
  const card = page.locator('#selected-relation');
  await check('CA-10', 1, 'De dónde sale la relación: nombra el documento que la afirma', async () => {
    if (mode === 'pointer') {
      // The point itself: the middle of a point with its name below is empty.
      await node(`Concepto ${SHEET.prerequisite}`).locator('.shape').hover();
      await clickEdge(SHEET.concept, SHEET.prerequisite);
    } else await activate(page.getByRole('button', { name: `Ver la fuente de la relación con ${SHEET.prerequisite}` }));
    await card.waitFor();
    const text = (await card.innerText()).replace(/\s+/g, ' ');
    const marked = await page.locator('svg.graph g.edge.is-selected').count();
    return { ok: text.includes('Lo dice') && text.includes(SHEET.syllabus) && marked === 1, seen: text };
  });
  await check('CA-10', 2, 'Abre el PDF de ese sílabo en una pestaña nueva', async () => {
    const opened = await openDocument(card.locator('a.doc'));
    return {
      ok: opened.href.startsWith('/resources/') && opened.status === 200 && opened.type.includes('application/pdf') && opened.tab,
      seen: `${opened.href} → ${opened.status} ${opened.type}; pestaña nueva: ${opened.tab ? 'sí' : 'no'}`,
    };
  });
  await check('CA-10', 3, 'Un elemento de CS2023, como la unidad: nombra CS2023 y enlaza su publicación de ACM', async () => {
    await open(SHEET.unit.toLowerCase(), SHEET.unit, 'Unidad');
    await shot('E-panel-del-foco-cs2023');
    const record = page.locator('#focus-panel .record');
    const text = (await record.innerText()).replace(/\s+/g, ' ');
    const href = await record.locator('a.doc').getAttribute('href');
    return { ok: text.includes('CS2023') && href.startsWith('https://dl.acm.org/'), seen: `${text} → ${href}` };
  });
  await check('CA-10', 4, 'El interruptor «Fuentes» dibuja la línea de cada elemento a su documento', async () => {
    await openConcept();
    await lens('Qué necesitas antes');
    const toggle = page.getByRole('switch', { name: 'Fuentes' });
    if (mode === 'pointer') await toggle.click();
    else {
      await tabTo(toggle);
      await page.keyboard.press('Space');
    }
    await settle();
    await shot('F3-fuentes-en-el-mapa');
    const lines = await page.locator('svg.graph g.edge-source').count();
    const documents = (await mapNodes()).filter((n) => n.kind === 'LearningResource').map((n) => n.name);
    return { ok: lines >= 5 && documents.includes(SHEET.syllabus), seen: `${lines} líneas de fuente hacia ${documents.join(', ')}` };
  });
}

// --- Run --------------------------------------------------------------------------

const browser = await chromium.launch();
for (const current of ['pointer', 'keyboard']) {
  if (ONLY && ONLY !== current) continue;
  mode = current;
  context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await context.newPage();
  page.on('pageerror', (error) => notes.add(`Error de página (${mode}): ${error.message}`));
  for (const run of [ca01, ca02, ca03, ca04, ca05, ca06, ca07, ca08, ca09, ca10]) {
    if (CASE && CASE !== run.name) continue;
    try {
      await run();
    } catch (error) {
      record(run.name.toUpperCase().replace('CA', 'CA-'), '—', 'El caso se recorre hasta el final', false, error.stack.split('\n').slice(0, 7).join(' // '));
    }
  }
  if (SHOTS && mode === 'pointer') {
    await goHome();
    await openTopic();
    await page.locator('#focus-panel').evaluate((element) => { element.scrollTop = 260; });
    await shot('E-panel-del-foco');
  }
  await context.close();
}
await browser.close();

const modes = [...new Set(results.map((r) => r.mode))];
const lines = ['| Caso | Paso | Resultado esperado | ' + modes.map((m) => (m === 'pointer' ? 'Con puntero' : 'Solo teclado')).join(' | ') + ' | Lo que se vio |', `|---|---|---|${modes.map(() => '---|').join('')}---|`];
for (const first of results.filter((r) => r.mode === modes[0])) {
  const verdicts = modes.map((m) => {
    const found = results.find((r) => r.mode === m && r.id === first.id && r.step === first.step);
    return found ? (found.ok ? 'cumple' : '**no cumple**') : '—';
  });
  const failed = results.find((r) => r.id === first.id && r.step === first.step && !r.ok);
  lines.push(`| ${first.id} | ${first.step} | ${first.expected} | ${verdicts.join(' | ')} | ${(failed ?? first).seen.replace(/\|/g, '/').replace(/\n/g, ' ')} |`);
}
const passed = results.filter((r) => r.ok).length;
const report = [`Recorrido técnico contra ${BASE}: ${passed} de ${results.length} comprobaciones cumplen.`, '', ...lines, '', 'Notas:', ...(notes.size ? [...notes].map((n) => `- ${n}`) : ['- ninguna'])].join('\n');
writeFileSync(new URL('walkthrough.md', OUT), report);
console.log(`\n${passed}/${results.length} ok`);
for (const note of notes) console.log('note:', note);
process.exit(passed === results.length ? 0 : 1);
