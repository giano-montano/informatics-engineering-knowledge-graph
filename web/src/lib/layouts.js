// One layout per lens (ADR-016, ADR-018). Each takes a response as it came
// and returns a scene: the target position of every node that answers the
// question, the edges between them and the captions that say how to read it.
// What does not answer the question is not drawn; what does not fit with a
// legible name is summarized, and stays complete in the panel.

import {
  DERIVATION, childrenOf, connections, containsTarget, documentOfEdge, edgeId, kindsOf, learningOrder,
  locationChains, nodeByKey, partsOf, pathSummary, prerequisitesByDepth, previousCourses, resourcesOf, sourcesOf,
} from './graph-reading.js';
import { CLASSES, GRAINS, RELATIONS, byName, className, plural } from './vocabulary.js';

// Thresholds of the summaries. They come from the four development syllabi
// and are to be reviewed with the thirteen (ADR-016).
export const MAX_NAMED_IN_GROUP = 14;
export const MAX_CONCEPTS_IN_TREE = 24;
export const MAX_BARE_UNITS = 4;
export const MAX_FAR_NODES = 10;

const COLUMN = 250;
const RADIUS = { KnowledgeArea: 17, KnowledgeUnit: 14, Topic: 12, Concept: 9, Course: 15, LearningResource: 12, ResourceType: 9 };
const FOCUS_RADIUS = 24;
const DOT_RADIUS = 5;
const LEVEL = { KnowledgeArea: 0, KnowledgeUnit: 1, Topic: 2, Concept: 3 };

// --- Pieces of a scene ------------------------------------------------------------

export function wrap(text, width = 22, maxLines = 2) {
  const words = String(text ?? '').split(/\s+/).filter(Boolean);
  const lines = [];
  let line = '';
  for (const word of words) {
    if (!line) line = word;
    else if ((line + ' ' + word).length <= width) line += ' ' + word;
    else {
      lines.push(line);
      line = word;
    }
  }
  if (line) lines.push(line);
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    const last = kept[maxLines - 1];
    kept[maxLines - 1] = (last.length > width - 1 ? last.slice(0, width - 1) : last).replace(/[\s,;:]+$/, '') + '…';
    return kept;
  }
  return lines.map((l) => (l.length > width + 6 ? l.slice(0, width + 5) + '…' : l));
}

class Scene {
  constructor(subgraph, focusKey) {
    this.subgraph = subgraph;
    this.focusKey = focusKey;
    this.nodes = [];
    this.edges = [];
    this.captions = [];
    this.boxes = [];
    this.byKey = new Map();
    this.info = {};
  }

  has(key) {
    return this.byKey.has(key);
  }

  at(key) {
    return this.byKey.get(key);
  }

  /** Places a node once; a second call returns the first placement. */
  put(node, x, y, options = {}) {
    if (this.byKey.has(node.key)) return this.byKey.get(node.key);
    const tone = options.tone ?? (node.key === this.focusKey ? 'focus' : 'main');
    const base = tone === 'focus' ? FOCUS_RADIUS : tone === 'dot' ? DOT_RADIUS : (RADIUS[node.label] ?? 10);
    const side = options.side ?? 'below';
    const width = options.width ?? (side === 'left' || side === 'right' ? 26 : 20);
    const placed = {
      key: node.key,
      node,
      x,
      y,
      r: tone === 'far' ? Math.round(base * 0.8) : base,
      tone,
      label: tone === 'dot' ? null : {
        side,
        lines: wrap(node.name_es ?? node.key, width, options.lines ?? 2),
        sub: options.sub ?? node.course_code ?? null,
      },
      expandable: Boolean(options.expandable),
      // Lit: what the map wants seen first besides the focus.
      lit: Boolean(options.lit),
      // Where the lines to its parts start when its name sits on their way.
      out: options.out ?? 0,
    };
    this.nodes.push(placed);
    this.byKey.set(node.key, placed);
    return placed;
  }

  /**
   * Draws an edge of the response from `from` to `to`, which may run against
   * the edge's own direction: a prerequisite is drawn from what is learned
   * first to what needs it.
   */
  link(edge, from, to, options = {}) {
    if (!this.has(from) || !this.has(to)) return;
    const id = edgeId(edge);
    if (this.edges.some((drawn) => drawn.id === id)) return;
    this.edges.push({
      id,
      edge,
      from,
      to,
      type: edge.type,
      tone: options.tone ?? 'main',
      arrow: Boolean(options.arrow),
      curve: options.curve ?? 'line',
      document: documentOfEdge(options.subgraph ?? this.subgraph, edge),
    });
  }

  /** A line that stands for a whole group, towards its box; it is not one edge of the graph. */
  bundle(from, point, type) {
    this.edges.push({ id: `bundle|${type}|${from}`, edge: null, from, to: null, point, type, tone: 'main', curve: 'line' });
  }

  caption(x, y, text, options = {}) {
    this.captions.push({ x, y, text, anchor: options.anchor ?? 'middle', kind: options.kind ?? 'column', color: options.color ?? null });
  }

  box(x, y, w, h, label = null) {
    this.boxes.push({ x, y, w, h, label });
  }
}

function labelWidth(placed) {
  return Math.max(...placed.label.lines.map((line) => line.length)) * 6.9 + 16;
}

function centered(count, gap) {
  return (index) => (index - (count - 1) / 2) * gap;
}

/** A grid of unnamed dots in a box: a group too large to name on the map. */
function dotBox(scene, items, left, centerY, title, color) {
  const perRow = Math.min(9, Math.ceil(Math.sqrt(items.length * 1.6)));
  const gap = 22;
  const rows = Math.ceil(items.length / perRow);
  const width = perRow * gap + 18;
  const height = rows * gap + 18;
  const top = centerY - height / 2;
  items.forEach((item, index) => {
    const column = index % perRow;
    const row = Math.floor(index / perRow);
    scene.put(item.node, left + 9 + gap / 2 + column * gap, top + 9 + gap / 2 + row * gap, { tone: 'dot' });
  });
  scene.box(left, top, width, height, null);
  scene.caption(left, top - 12, title, { anchor: 'start', kind: 'relation', color });
  return { left, top, width, height };
}

// --- Start: the areas around, the courses in the middle ---------------------------

export function layoutOverview(overview) {
  const scene = new Scene(overview, null);
  const areas = overview.nodes.filter((node) => node.label === 'KnowledgeArea').sort(byName);
  const courses = overview.nodes.filter((node) => node.label === 'Course')
    .sort((a, b) => (a.course_code ?? '').localeCompare(b.course_code ?? ''));
  // The canvas is wider than tall: the grid of courses is too.
  const columns = Math.max(1, Math.min(6, Math.ceil(Math.sqrt(courses.length * 1.6))));
  const rows = Math.ceil(courses.length / columns);
  const cellX = 184;
  const cellY = 124;
  const ringX = Math.max(430, (columns * cellX) / 2 + 190);
  const ringY = Math.max(280, (rows * cellY) / 2 + 150);
  courses.forEach((course, index) => {
    const row = Math.floor(index / columns);
    const inRow = Math.min(columns, courses.length - row * columns);
    const x = ((index % columns) - (inRow - 1) / 2) * cellX;
    const y = (row - (rows - 1) / 2) * cellY;
    scene.put(course, x, y, { side: 'below', width: 20 });
  });
  if (courses.length) scene.caption(0, -(rows * cellY) / 2 - 22, 'Cursos con sílabo', { kind: 'row' });
  areas.forEach((area, index) => {
    const angle = -Math.PI / 2 + (index / areas.length) * 2 * Math.PI;
    const x = Math.cos(angle) * ringX;
    const y = Math.sin(angle) * ringY;
    const filled = area.topics > 0;
    const side = Math.abs(Math.cos(angle)) < 0.25 ? (y < 0 ? 'above' : 'below') : x < 0 ? 'left' : 'right';
    scene.put(area, x, y, {
      tone: filled ? 'main' : 'far',
      lit: filled,
      side,
      width: 24,
      sub: filled ? `${plural(area.topics, 'tema', 'temas')} · ${plural(area.concepts, 'concepto', 'conceptos')}` : null,
    });
  });
  // Thirty names in one view: here they shrink less than anywhere else.
  scene.labelFloor = 0.7;
  scene.info = {
    areas: areas.length,
    filled: areas.filter((area) => area.topics > 0).length,
    courses: courses.length,
  };
  return scene;
}

// --- Lo que lo rodea --------------------------------------------------------------

const LEFT_WING = new Set([
  'PART_OF:out', 'HAS_PREREQUISITE:out', 'SPECIALIZES:out', 'REQUIRES_CONCEPT:out',
  'TEACHES_CONCEPT:in', 'REQUIRES_CONCEPT:in', 'IS_ABOUT:in', 'HAS_RESOURCE_TYPE:out',
]);

export function layoutNeighborhood(detail, focusKey, expansions = new Map()) {
  const scene = new Scene(detail, focusKey);
  const focus = nodeByKey(detail, focusKey);
  if (!focus) return scene;
  scene.put(focus, 0, 0, { side: 'below', width: 24, lines: 3 });

  const groups = connections(detail, focusKey);
  const wings = { left: groups.filter((g) => LEFT_WING.has(g.id)), right: groups.filter((g) => !LEFT_WING.has(g.id)) };
  // Two wings even when every relationship reads the same way.
  for (const [full, empty] of [['left', 'right'], ['right', 'left']]) {
    if (!wings[empty].length && wings[full].length > 1) {
      wings[empty] = wings[full].splice(Math.ceil(wings[full].length / 2));
    }
  }

  const rowGap = 44;
  const wingX = 310;
  const direct = new Set();
  let clusters = 0;
  const extent = { top: -60, bottom: 90 };
  for (const [name, list] of Object.entries(wings)) {
    const sign = name === 'left' ? -1 : 1;
    const heights = list.map((group) => (group.items.length > MAX_NAMED_IN_GROUP
      ? Math.ceil(group.items.length / 9) * 22 + 40
      : group.items.length * rowGap));
    const total = heights.reduce((sum, h) => sum + h, 0) + Math.max(0, list.length - 1) * 46;
    let y = -total / 2;
    list.forEach((group, index) => {
      const color = RELATIONS[group.type].color;
      const title = group.items.length > 1 ? `${group.title} · ${group.items.length}` : group.title;
      group.items.forEach((item) => direct.add(item.node.key));
      if (group.items.length > MAX_NAMED_IN_GROUP) {
        clusters += 1;
        const centerY = y + heights[index] / 2 + 10;
        const width = Math.min(9, Math.ceil(Math.sqrt(group.items.length * 1.6))) * 22 + 18;
        const box = dotBox(scene, group.items, sign < 0 ? -wingX - width + 40 : wingX - 40, centerY, title, color);
        scene.bundle(focusKey, { x: sign < 0 ? box.left + box.width : box.left, y: centerY }, group.type);
      } else {
        scene.caption(sign * (wingX - 18), y - 2, title, { anchor: sign < 0 ? 'start' : 'end', kind: 'relation', color });
        group.items.forEach((item, row) => {
          scene.put(item.node, sign * wingX, y + 22 + row * rowGap, {
            side: sign < 0 ? 'left' : 'right',
            expandable: item.node.more_neighbors && !expansions.has(item.node.key),
          });
          scene.link(item.edge, focusKey, item.node.key);
        });
      }
      y += heights[index] + 46;
    });
    extent.top = Math.min(extent.top, -total / 2 - 30);
    extent.bottom = Math.max(extent.bottom, total / 2 + 20);
  }

  // What each expanded neighbor brought, below, with its name.
  let bandY = extent.bottom + 110;
  const brought = [];
  for (const [key, response] of expansions) {
    if (!scene.has(key)) continue;
    const fresh = connections(response, key)
      .flatMap((group) => group.items.map((item) => ({ ...item, group })))
      .filter((item) => item.node.key !== focusKey && !direct.has(item.node.key) && !scene.has(item.node.key));
    if (!fresh.length) continue;
    const perRow = 6;
    const gapX = 184;
    const origin = scene.at(key);
    scene.caption(0, bandY - 44, `Conexiones de «${origin.node.name_es}» · ${fresh.length}`, { kind: 'row' });
    fresh.forEach((item, index) => {
      const row = Math.floor(index / perRow);
      const inRow = Math.min(perRow, fresh.length - row * perRow);
      const x = ((index % perRow) - (inRow - 1) / 2) * gapX;
      scene.put(item.node, x, bandY + row * 104, { side: 'below', width: 22, lines: 3 });
      scene.link(item.edge, key, item.node.key, { subgraph: response, tone: 'far' });
      brought.push({ node: item.node, edge: item.edge, through: origin.node, title: item.group.title, subgraph: response });
    });
    bandY += Math.ceil(fresh.length / perRow) * 104 + 80;
  }

  // Some neighbors of the neighbors, dimmed, above.
  const farCandidates = new Map();
  for (const edge of detail.edges) {
    if (edge.type === DERIVATION) continue;
    for (const [near, far] of [[edge.source, edge.target], [edge.target, edge.source]]) {
      if (!direct.has(near) || direct.has(far) || far === focusKey || scene.has(far)) continue;
      // A neighbor drawn as an unnamed dot has no room for what hangs from it.
      if (scene.at(near)?.tone === 'dot') continue;
      if (!farCandidates.has(near)) farCandidates.set(near, []);
      farCandidates.get(near).push({ node: nodeByKey(detail, far), edge, through: scene.at(near)?.node });
    }
  }
  const far = [];
  const taken = new Set();
  const queues = [...farCandidates.values()].map((list) => list.filter((item) => item.node && item.through).sort((a, b) => byName(a.node, b.node)));
  const farTotal = new Set(queues.flat().map((item) => item.node.key)).size;
  while (far.length < MAX_FAR_NODES && queues.some((queue) => queue.length)) {
    for (const queue of queues) {
      const item = queue.shift();
      if (!item || taken.has(item.node.key)) continue;
      taken.add(item.node.key);
      far.push(item);
      if (far.length >= MAX_FAR_NODES) break;
    }
  }
  // Each one above the wing of the neighbor it hangs from, joined by the edge that brought it.
  for (const sign of [-1, 1]) {
    const side = far.filter((item) => Math.sign(scene.at(item.through.key).x) === sign)
      .sort((x, y) => byName(x.through, y.through) || byName(x.node, y.node));
    const perRow = 4;
    const rows = Math.ceil(side.length / perRow);
    side.forEach((item, index) => {
      const row = Math.floor(index / perRow);
      const inRow = Math.min(perRow, side.length - row * perRow);
      const x = sign * (wingX + 30) + ((index % perRow) - (inRow - 1) / 2) * 176;
      scene.put(item.node, x, extent.top - 64 - (rows - 1 - row) * 84, { tone: 'far', side: 'above', width: 20 });
      scene.link(item.edge, item.edge.source, item.edge.target, { tone: 'far' });
    });
  }

  scene.info = { direct: direct.size, far: far.length, farTotal, clusters, expansions: brought.length, farItems: far, brought };
  return scene;
}

// --- Qué necesitas antes ----------------------------------------------------------

function column(scene, items, x, gap, options = {}) {
  const y = centered(items.length, gap);
  items.forEach((item, index) => scene.put(item.node ?? item, x, y(index), options));
}

function depthCaption(depth) {
  return depth === 1 ? 'Justo antes' : `${depth} pasos antes`;
}

export function layoutPrerequisites(response, focusKey, detail) {
  const scene = new Scene(response, focusKey);
  const focus = nodeByKey(response, focusKey);
  if (!focus) return scene;
  const groups = prerequisitesByDepth(response, focusKey);
  const gap = 84;
  const tallest = Math.max(1, ...groups.map((group) => group.items.length));
  const top = -((tallest - 1) * gap) / 2 - 62;
  scene.put(focus, 0, 0, { side: 'below', width: 24, lines: 3 });
  if (!groups.length) {
    // Nothing before it: what depends on it, from its neighborhood.
    const dependents = detail ? connections(detail, focusKey).find((group) => group.id === 'HAS_PREREQUISITE:in') : null;
    if (dependents) {
      column(scene, dependents.items, COLUMN, gap);
      dependents.items.forEach((item) => scene.link(item.edge, focusKey, item.node.key, { arrow: true, curve: 'h', subgraph: detail }));
      scene.caption(COLUMN, -((dependents.items.length - 1) * gap) / 2 - 62, 'Se necesita para');
    }
    scene.info = { total: 0, dependents: dependents?.items.map((item) => item.node) ?? [] };
    return scene;
  }
  for (const group of groups) {
    column(scene, group.items, -group.depth * COLUMN, gap);
    scene.caption(-group.depth * COLUMN, top, depthCaption(group.depth));
  }
  scene.caption(0, top, 'Lo que quieres aprender');
  for (const edge of response.edges) {
    if (edge.type === 'HAS_PREREQUISITE') scene.link(edge, edge.target, edge.source, { arrow: true, curve: 'h' });
  }
  scene.info = { total: groups.reduce((sum, group) => sum + group.items.length, 0), maxDepth: groups.at(-1).depth };
  return scene;
}

// --- Camino hasta aquí ------------------------------------------------------------

/** Spreads sorted positions so that neighbors keep at least `gap` between them. */
function spread(placed, gap) {
  placed.sort((a, b) => a.x - b.x);
  for (let i = 1; i < placed.length; i += 1) {
    if (placed[i].x - placed[i - 1].x < gap) placed[i].x = placed[i - 1].x + gap;
  }
  return placed;
}

export function layoutPath(response, focusKey, grain) {
  const scene = new Scene(response, focusKey);
  const target = nodeByKey(response, focusKey);
  if (!target) return scene;
  const summary = pathSummary(response, focusKey, grain);
  if (summary.empty) {
    scene.put(target, 0, 0, { side: 'below', width: 24, lines: 3 });
    scene.info = { empty: true, stops: [], prerequisites: [] };
    return scene;
  }
  const slot = 190;
  const rowGap = grain === 'area' ? 112 : 150;

  // Bottom row: the concepts, from the farthest on the left to the target on the right.
  const frontier = response.nodes.filter((node) => node.label === 'Concept' && node.depth === 0 && node.key !== focusKey).sort(byName);
  const ends = target.label === 'Concept' ? [target] : frontier;
  let x = 0;
  ends.forEach((node, index) => scene.put(node, index * slot, 0, { side: 'below', width: 20, lines: 3 }));
  const depths = [...new Set(summary.prerequisites.map((node) => node.depth))].sort((a, b) => a - b);
  for (const depth of depths) {
    const group = summary.prerequisites.filter((node) => node.depth === depth).sort(byName).reverse();
    x -= 60;
    const right = x - slot;
    for (const node of group) {
      x -= slot;
      scene.put(node, x, 0, { side: 'below', width: 20, lines: 3 });
    }
    scene.caption((right + x) / 2, 96, depthCaption(depth), { kind: 'row' });
  }
  for (const edge of response.edges) {
    if (edge.type === 'HAS_PREREQUISITE') scene.link(edge, edge.target, edge.source, { arrow: true, curve: 'arc' });
  }

  // Above each concept, what holds it up to the grain: its topic, its course, or topic, unit and area.
  const holders = new Map();
  const levelOf = (node) => (grain === 'course' ? 1 : grain === 'topic' ? 1 : 3 - LEVEL[node.label]);
  const up = (edge) => (edge.type === 'TEACHES_CONCEPT' ? [edge.target, edge.source] : edge.type === 'PART_OF' ? [edge.source, edge.target] : null);
  const prerequisiteKeys = new Set(summary.prerequisites.map((node) => node.key));
  let frontierKeys = [...prerequisiteKeys];
  const visited = new Set(frontierKeys);
  while (frontierKeys.length) {
    const next = [];
    for (const edge of response.edges) {
      const ends2 = up(edge);
      if (!ends2 || !frontierKeys.includes(ends2[0])) continue;
      const holder = nodeByKey(response, ends2[1]);
      if (!holder || holder.key === focusKey || holder.label === 'Concept') continue;
      if (grain === 'course' ? holder.label !== 'Course' : holder.label === 'Course') continue;
      if (grain === 'topic' && holder.label !== 'Topic') continue;
      if (holder.depth === 0) continue;
      if (!holders.has(holder.key)) holders.set(holder.key, { node: holder, below: [] });
      holders.get(holder.key).below.push(ends2[0]);
      if (!visited.has(holder.key)) {
        visited.add(holder.key);
        next.push(holder.key);
      }
    }
    frontierKeys = next;
  }
  const levels = new Map();
  for (const holder of holders.values()) {
    const level = levelOf(holder.node);
    if (!levels.has(level)) levels.set(level, []);
    levels.get(level).push(holder);
  }
  const left = Math.min(...scene.nodes.map((placed) => placed.x));
  for (const level of [...levels.keys()].sort((a, b) => a - b)) {
    const placed = levels.get(level).map((holder) => {
      const xs = holder.below.map((key) => scene.at(key)?.x).filter((value) => value !== undefined);
      return { holder, x: xs.length ? xs.reduce((sum, value) => sum + value, 0) / xs.length : 0 };
    });
    for (const item of spread(placed, slot)) {
      const isStop = item.holder.node.label === GRAINS[grain].label;
      scene.put(item.holder.node, item.x, -level * rowGap, { side: 'above', width: 22, tone: isStop ? 'main' : 'far' });
    }
    const label = levels.get(level)[0].node.label;
    scene.caption(left - 150, -level * rowGap + 4, CLASSES[label].plural.replace(/^./, (c) => c.toUpperCase()), { anchor: 'end', kind: 'row' });
  }
  scene.caption(left - 150, 4, 'Conceptos', { anchor: 'end', kind: 'row' });
  for (const edge of response.edges) {
    const ends2 = up(edge);
    if (ends2 && holders.has(ends2[1]) && (prerequisiteKeys.has(ends2[0]) || holders.has(ends2[0]))) {
      scene.link(edge, ends2[1], ends2[0], { tone: 'far' });
    }
  }

  // A target that is not a concept sits to the right of the concepts it holds.
  if (target.label !== 'Concept') {
    const within = response.nodes.filter((node) => node.depth === 0 && node.key !== focusKey && node.label !== 'Concept' && !holders.has(node.key));
    const baseX = (ends.length - 1) * slot;
    const ranks = [...new Set(within.map((node) => LEVEL[node.label]))].sort((a, b) => b - a);
    ranks.forEach((rank, index) => {
      const list = within.filter((node) => LEVEL[node.label] === rank).sort(byName);
      const y = centered(list.length, 84);
      list.forEach((node, i) => scene.put(node, baseX + (index + 1) * 210, -90 + y(i), { side: 'right', tone: 'far' }));
    });
    scene.put(target, baseX + (ranks.length + 1) * 210 + 30, -90, { side: 'right', width: 24, lines: 3 });
    for (const edge of response.edges) {
      const ends2 = up(edge);
      if (ends2 && scene.has(ends2[0]) && scene.has(ends2[1]) && !holders.has(ends2[1])) scene.link(edge, ends2[0], ends2[1], { tone: 'far' });
    }
  }

  scene.info = {
    empty: false,
    stops: summary.stops,
    prerequisites: summary.prerequisites,
    own: summary.stops.find((stop) => containsTarget(response, stop.key, focusKey)) ?? null,
  };
  return scene;
}

// --- Cursos que conviene llevar antes ---------------------------------------------

export function layoutCourses(response, focusKey) {
  const scene = new Scene(response, focusKey);
  const course = nodeByKey(response, focusKey);
  if (!course) return scene;
  const reading = previousCourses(response, focusKey);
  const gap = 84;
  const tallest = Math.max(1, reading.required.length, reading.previous.length);
  const top = -((tallest - 1) * gap) / 2 - 62;
  scene.put(course, 0, 0, { side: 'below', width: 24, lines: 3 });
  scene.caption(0, top, 'El curso');
  if (reading.required.length) {
    column(scene, reading.required, -COLUMN, gap);
    scene.caption(-COLUMN, top, 'Lo que pide');
    reading.required.forEach((item) => scene.link(item.edge, item.node.key, focusKey, { arrow: true, curve: 'h' }));
  }
  if (reading.previous.length) {
    column(scene, reading.previous.map((entry) => entry.course), -2 * COLUMN, gap, { width: 22 });
    scene.caption(-2 * COLUMN, top, 'Conviene llevar antes');
    for (const entry of reading.previous) {
      entry.evidence.forEach((item) => scene.link(item.edge, entry.course.key, item.node.key, { arrow: true, curve: 'h' }));
    }
  }
  const taught = reading.taught.filter((item) => !scene.has(item.node.key));
  if (taught.length > MAX_NAMED_IN_GROUP) {
    const box = dotBox(scene, taught, COLUMN - 60, 0, `Lo que enseña · ${plural(taught.length, 'concepto', 'conceptos')}`, RELATIONS.TEACHES_CONCEPT.color);
    scene.bundle(focusKey, { x: box.left, y: 0 }, 'TEACHES_CONCEPT');
  } else if (taught.length) {
    const y = centered(taught.length, 44);
    taught.forEach((item, index) => {
      scene.put(item.node, COLUMN, y(index), { side: 'right' });
      scene.link(item.edge, focusKey, item.node.key, { curve: 'h' });
    });
    scene.caption(COLUMN, -((taught.length - 1) * 44) / 2 - 40, `Lo que enseña · ${taught.length}`, { anchor: 'start' });
  }
  scene.info = { ...reading, boxed: taught.length > MAX_NAMED_IN_GROUP };
  return scene;
}

// --- Dónde está en la carrera -----------------------------------------------------

export function layoutLocation(response, focusKey) {
  const scene = new Scene(response, focusKey);
  const focus = nodeByKey(response, focusKey);
  if (!focus) return scene;
  const chains = locationChains(response, focusKey);
  const gap = 128;
  const longest = Math.max(0, ...chains.map((chain) => chain.length));
  chains.forEach((chain, index) => {
    const x = (index - (chains.length - 1) / 2) * 340;
    chain.forEach((node, level) => scene.put(node, x, (level - longest) * gap + (longest - chain.length) * gap, { side: 'right', width: 30 }));
  });
  scene.put(focus, 0, 0, { side: 'right', width: 30, lines: 3 });
  const leftmost = Math.min(0, ...scene.nodes.map((placed) => placed.x));
  for (const placed of [...scene.nodes]) {
    if (placed.x === leftmost || placed.key === focusKey) {
      scene.caption(leftmost - 56, placed.y + 4, className(placed.node), { anchor: 'end', kind: 'row' });
    }
  }
  for (const edge of response.edges) {
    if (edge.type === 'PART_OF' && scene.has(edge.source) && scene.has(edge.target)) scene.link(edge, edge.target, edge.source);
  }
  scene.info = { chains };
  return scene;
}

// --- Qué contiene -----------------------------------------------------------------

function layoutSteps(scene, response, focusKey, topic) {
  const order = learningOrder(response, focusKey);
  const gapY = 86;
  if (!order.related.size) {
    const perRow = Math.min(5, Math.max(1, Math.ceil(Math.sqrt(order.concepts.length))));
    const rows = Math.ceil(order.concepts.length / perRow);
    order.concepts.sort(byName).forEach((node, index) => {
      scene.put(node, COLUMN + (index % perRow) * 190, (Math.floor(index / perRow) - (rows - 1) / 2) * gapY, { width: 20 });
    });
    if (order.concepts.length) {
      scene.box(COLUMN - 100, -((rows - 1) * gapY) / 2 - 50, (perRow - 1) * 190 + 200, (rows - 1) * gapY + 130);
    }
  } else {
    const tallest = Math.max(...order.steps.map((step) => step.length));
    const top = -((tallest - 1) * gapY) / 2;
    order.steps.forEach((step, index) => {
      const y = centered(step.length, gapY);
      step.forEach((node, row) => scene.put(node, COLUMN + index * COLUMN, y(row), { width: 20 }));
      scene.caption(COLUMN + index * COLUMN, top - 62, `Paso ${index + 1}`);
    });
    scene.box(COLUMN - 110, top - 90, (order.steps.length - 1) * COLUMN + 220, (tallest - 1) * gapY + 190);
    order.edges.forEach((edge) => scene.link(edge, edge.target, edge.source, { arrow: true, curve: 'h' }));
  }
  scene.put(topic, 0, 0, { side: 'below', width: 24, lines: 3 });
  scene.info = { kind: 'steps', concepts: order.concepts.length, steps: order.steps.length, ordered: order.related.size > 0 };
}

function layoutTree(scene, response, focusKey, root) {
  const parts = partsOf(response, focusKey);
  const counts = { units: 0, topics: 0, concepts: 0 };
  for (const node of parts) {
    if (node.label === 'KnowledgeUnit') counts.units += 1;
    if (node.label === 'Topic') counts.topics += 1;
    if (node.label === 'Concept') counts.concepts += 1;
  }
  const withConcepts = counts.concepts > 0 && counts.concepts <= MAX_CONCEPTS_IN_TREE;
  const leafGap = 34;
  const depthGap = [0, 250, 590, 960];
  let nextY = 0;
  const bare = [];
  const conceptsUnder = (node) => (node.label === 'Concept' ? 1 : childrenOf(response, node.key).reduce((sum, child) => sum + conceptsUnder(child), 0));
  const place = (node, depth) => {
    let children = childrenOf(response, node.key);
    if (!withConcepts) children = children.filter((child) => child.label !== 'Concept');
    if (depth === 0 && root.label === 'KnowledgeArea') {
      const empty = children.filter((child) => !childrenOf(response, child.key).length);
      if (empty.length) {
        bare.push(...empty);
        children = children.filter((child) => !empty.includes(child));
      }
    }
    const ys = children.map((child) => place(child, depth + 1));
    const y = ys.length ? (ys[0] + ys.at(-1)) / 2 : (nextY += leafGap);
    const total = node.label === 'Topic' && !withConcepts ? conceptsUnder(node) : 0;
    const placed = scene.put(node, depthGap[depth] ?? depth * 300, y, {
      side: depth === 0 ? 'left' : 'right',
      width: depth === 0 ? 22 : 40,
      lines: depth === 0 ? 3 : 1,
      sub: total ? plural(total, 'concepto', 'conceptos') : null,
    });
    if (depth > 0 && children.length) placed.out = labelWidth(placed);
    return y;
  };
  place(root, 0);
  let summarized = 0;
  if (bare.length > MAX_BARE_UNITS) {
    summarized = bare.length;
    scene.caption(depthGap[1] - 14, nextY + 58, `+ ${bare.length} unidades de CS2023 que ningún sílabo cargado trata todavía`, { anchor: 'start', kind: 'note' });
  } else {
    bare.forEach((unit) => {
      nextY += leafGap;
      scene.put(unit, depthGap[1], nextY, { side: 'right', width: 36, lines: 1, tone: 'far', sub: 'solo en CS2023' });
    });
  }
  // The root goes back to the middle of what was finally drawn.
  const ys = scene.nodes.filter((placed) => placed.key !== focusKey).map((placed) => placed.y);
  if (ys.length) scene.at(focusKey).y = (Math.min(...ys) + Math.max(...ys)) / 2;
  const top = Math.min(...scene.nodes.map((placed) => placed.y)) - 48;
  const titles = { KnowledgeUnit: 'Unidades de CS2023', Topic: 'Temas de los sílabos', Concept: 'Conceptos' };
  for (const [label, title] of Object.entries(titles)) {
    const first = scene.nodes.find((placed) => placed.node.label === label && placed.key !== focusKey);
    if (first) scene.caption(first.x - 14, top, title, { anchor: 'start' });
  }
  for (const edge of response.edges) {
    if (edge.type === 'PART_OF' && scene.has(edge.source) && scene.has(edge.target)) {
      scene.link(edge, edge.target, edge.source, { curve: 'h', tone: scene.at(edge.source).tone === 'far' ? 'far' : 'main' });
    }
  }
  scene.info = { kind: 'tree', ...counts, withConcepts, summarized, bare: bare.length };
}

export function layoutContents(response, focusKey) {
  const scene = new Scene(response, focusKey);
  const root = nodeByKey(response, focusKey);
  if (!root) return scene;
  if (root.label === 'Topic') layoutSteps(scene, response, focusKey, root);
  else layoutTree(scene, response, focusKey, root);
  return scene;
}

// --- Material de estudio ----------------------------------------------------------

export function layoutResources(response, focusKey) {
  const scene = new Scene(response, focusKey);
  const focus = nodeByKey(response, focusKey);
  if (!focus) return scene;
  const found = resourcesOf(response);
  const leafGap = 40;
  let nextY = 0;
  let deepest = 0;
  const place = (node, depth) => {
    deepest = Math.max(deepest, depth);
    const ys = childrenOf(response, node.key).map((child) => place(child, depth + 1));
    const y = ys.length ? (ys[0] + ys.at(-1)) / 2 : (nextY += leafGap);
    const placed = scene.put(node, depth * 290, y, { side: depth === 0 ? 'left' : 'right', width: depth === 0 ? 22 : 38, lines: depth === 0 ? 3 : 1 });
    if (depth > 0) placed.out = labelWidth(placed);
    return y;
  };
  place(focus, 0);
  const resourceX = (deepest + 1) * 290 + 70;
  const placed = found.map((entry) => {
    const ys = entry.about.map((element) => scene.at(element.key)?.y).filter((value) => value !== undefined);
    return { entry, x: ys.length ? ys.reduce((sum, value) => sum + value, 0) / ys.length : 0 };
  });
  for (const item of spread(placed, 96)) {
    scene.put(item.entry.resource, resourceX, item.x, { side: 'right', width: 26 });
    if (item.entry.type) scene.put(item.entry.type, resourceX + 200, item.x, { side: 'right', tone: 'far' });
  }
  const typed = scene.nodes.filter((p) => p.node.label === 'ResourceType');
  if (typed.length) {
    // One node per type, in the middle of the resources of that type.
    for (const type of typed) {
      const ys = found.filter((entry) => entry.type?.key === type.key).map((entry) => scene.at(entry.resource.key).y);
      type.y = ys.reduce((sum, value) => sum + value, 0) / ys.length;
    }
  }
  if (found.length) {
    const top = Math.min(...scene.nodes.map((p) => p.y)) - 52;
    scene.caption(resourceX - 14, top, 'Sílabos que tratan sobre ellas', { anchor: 'start' });
    if (deepest > 0) scene.caption(290 - 14, top, 'Sus partes', { anchor: 'start' });
    if (typed.length) scene.caption(resourceX + 200 - 14, top, 'Tipo', { anchor: 'start' });
  }
  for (const edge of response.edges) {
    if (edge.type === 'PART_OF') scene.link(edge, edge.target, edge.source, { curve: 'h', tone: 'far' });
    if (edge.type === 'IS_ABOUT') scene.link(edge, edge.target, edge.source, { curve: 'h' });
    if (edge.type === 'HAS_RESOURCE_TYPE') scene.link(edge, edge.source, edge.target, { curve: 'h', tone: 'far' });
  }
  scene.info = { resources: found };
  return scene;
}

// --- Tipos -----------------------------------------------------------------------

export function layoutKinds(response, focusKey) {
  const scene = new Scene(response, focusKey);
  const focus = nodeByKey(response, focusKey);
  if (!focus) return scene;
  const reading = kindsOf(response, focusKey);
  scene.put(focus, 0, 0, { side: 'right', width: 26, lines: 3 });
  const walk = (start, direction) => {
    let front = [start];
    const seen = new Set(front);
    let level = 0;
    while (front.length) {
      level += 1;
      const next = [];
      for (const edge of reading.all) {
        const [from, to] = direction < 0 ? [edge.source, edge.target] : [edge.target, edge.source];
        if (front.includes(from) && !seen.has(to)) {
          seen.add(to);
          next.push(to);
        }
      }
      const list = next.map((key) => nodeByKey(response, key)).filter(Boolean).sort(byName);
      const x = centered(list.length, 210);
      list.forEach((node, index) => scene.put(node, x(index), direction * level * 150, { side: 'below', width: 20 }));
      front = next;
    }
    return level - 1;
  };
  const above = walk(focusKey, -1);
  const below = walk(focusKey, 1);
  const left = Math.min(...scene.nodes.map((placed) => placed.x)) - 70;
  if (above > 0) scene.caption(left, -150 + 4, 'Es un tipo de', { anchor: 'end', kind: 'row' });
  if (below > 0) scene.caption(left, 150 + 4, 'Sus tipos', { anchor: 'end', kind: 'row' });
  reading.all.forEach((edge) => scene.link(edge, edge.source, edge.target, { arrow: true }));
  scene.info = reading;
  return scene;
}

// --- Fuentes: every element joined to its document, in a row apart (ADR-019) -------

export function withSources(scene, subgraphs) {
  const visible = scene.nodes.filter((placed) => placed.node.label !== 'LearningResource');
  if (!visible.length) return scene;
  const documents = new Map();
  const lines = [];
  for (const subgraph of subgraphs) {
    if (!subgraph) continue;
    for (const placed of visible) {
      for (const document of sourcesOf(subgraph, placed.key)) {
        documents.set(document.key, document);
        const edge = subgraph.edges.find((e) => e.type === DERIVATION && e.source === placed.key && e.target === document.key);
        lines.push({ edge, subgraph });
      }
    }
  }
  if (!documents.size) return scene;
  const bottom = Math.max(...scene.nodes.map((placed) => placed.y)) + 170;
  const xs = scene.nodes.map((placed) => placed.x);
  const middle = (Math.min(...xs) + Math.max(...xs)) / 2;
  const list = [...documents.values()].sort(byName);
  const x = centered(list.length, 230);
  list.forEach((document, index) => {
    if (!scene.has(document.key)) scene.put(document, middle + x(index), bottom, { side: 'below', width: 22, tone: 'main' });
  });
  scene.caption(middle, bottom - 44, 'Fuentes', { kind: 'row' });
  for (const { edge, subgraph } of lines) scene.link(edge, edge.source, edge.target, { tone: 'source', subgraph });
  return scene;
}
