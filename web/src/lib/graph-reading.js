// Readings of a subgraph `{nodes, edges}`. Everything here only reorders what
// the API returned: no edge and no node is derived.

import { CONNECTION_ORDER, GRAINS, RELATIONS, byName } from './vocabulary.js';

export const DERIVATION = 'WAS_DERIVED_FROM';

export function edgeId(edge) {
  return `${edge.type}|${edge.source}|${edge.target}`;
}

export function nodeByKey(subgraph, key) {
  return subgraph?.nodes.find((node) => node.key === key) ?? null;
}

function indexOf(subgraph) {
  return new Map(subgraph.nodes.map((node) => [node.key, node]));
}

/** The documents a node was derived from. */
export function sourcesOf(subgraph, key) {
  const nodes = indexOf(subgraph);
  return subgraph.edges
    .filter((edge) => edge.type === DERIVATION && edge.source === key)
    .map((edge) => nodes.get(edge.target))
    .filter(Boolean);
}

/** The document that backs an edge: its provenance or, in the reference layer, the source of its origin. */
export function documentOfEdge(subgraph, edge) {
  if (edge.provenance) return nodeByKey(subgraph, edge.provenance);
  return sourcesOf(subgraph, edge.source)[0] ?? null;
}

/** Direct neighbors of `key`, grouped by relationship and direction, without derivations. */
export function connections(subgraph, key) {
  const nodes = indexOf(subgraph);
  const groups = new Map();
  for (const edge of subgraph.edges) {
    if (edge.type === DERIVATION) continue;
    const direction = edge.source === key ? 'out' : edge.target === key ? 'in' : null;
    if (!direction) continue;
    const other = nodes.get(direction === 'out' ? edge.target : edge.source);
    if (!other || other.key === key) continue;
    const id = `${edge.type}:${direction}`;
    if (!groups.has(id)) {
      groups.set(id, { id, type: edge.type, direction, title: RELATIONS[edge.type][direction], items: [] });
    }
    groups.get(id).items.push({ node: other, edge });
  }
  const rank = (id) => (CONNECTION_ORDER.indexOf(id) + 1) || 99;
  return [...groups.values()]
    .sort((a, b) => rank(a.id) - rank(b.id))
    .map((group) => ({ ...group, items: group.items.sort((a, b) => byName(a.node, b.node)) }));
}

/** Chains from the area down to the parent of `key`, following PART_OF. */
export function locationChains(subgraph, key) {
  const nodes = indexOf(subgraph);
  const chains = [];
  const climb = (current, path) => {
    const parents = subgraph.edges
      .filter((edge) => edge.type === 'PART_OF' && edge.source === current)
      .map((edge) => nodes.get(edge.target))
      .filter(Boolean);
    if (!parents.length || path.length > 6) {
      if (path.length) chains.push([...path].reverse());
      return;
    }
    for (const parent of parents) climb(parent.key, [...path, parent]);
  };
  climb(key, []);
  return chains;
}

/** What is part of `key`, at any depth, within a location response. */
export function partsOf(subgraph, key) {
  const nodes = indexOf(subgraph);
  const children = new Map();
  for (const edge of subgraph.edges) {
    if (edge.type !== 'PART_OF') continue;
    if (!children.has(edge.target)) children.set(edge.target, []);
    children.get(edge.target).push(edge.source);
  }
  const seen = new Set();
  const queue = [key];
  while (queue.length) {
    for (const child of children.get(queue.shift()) ?? []) {
      if (child !== key && !seen.has(child)) {
        seen.add(child);
        queue.push(child);
      }
    }
  }
  return [...seen].map((k) => nodes.get(k)).filter(Boolean);
}

export function childrenOf(subgraph, key) {
  const nodes = indexOf(subgraph);
  return subgraph.edges
    .filter((edge) => edge.type === 'PART_OF' && edge.target === key)
    .map((edge) => nodes.get(edge.source))
    .filter(Boolean)
    .sort(byName);
}

export function countByClass(nodes) {
  const counts = {};
  for (const node of nodes) counts[node.label] = (counts[node.label] ?? 0) + 1;
  return counts;
}

/**
 * In which order to learn the concepts of an element: steps by the
 * prerequisites among them (step 1 needs nothing from inside).
 */
export function learningOrder(subgraph, key) {
  const concepts = partsOf(subgraph, key).filter((node) => node.label === 'Concept');
  const inside = new Set(concepts.map((node) => node.key));
  const needs = new Map(concepts.map((node) => [node.key, []]));
  const related = new Set();
  const edges = [];
  for (const edge of subgraph.edges) {
    if (edge.type === 'HAS_PREREQUISITE' && inside.has(edge.source) && inside.has(edge.target)) {
      needs.get(edge.source).push(edge.target);
      related.add(edge.source);
      related.add(edge.target);
      edges.push(edge);
    }
  }
  const stepOf = new Map();
  const compute = (k, stack) => {
    if (stepOf.has(k)) return stepOf.get(k);
    if (stack.has(k)) return 1;
    stack.add(k);
    const step = 1 + Math.max(0, ...needs.get(k).map((required) => compute(required, stack)));
    stack.delete(k);
    stepOf.set(k, step);
    return step;
  };
  concepts.forEach((node) => compute(node.key, new Set()));
  const total = Math.max(0, ...stepOf.values());
  const steps = [];
  for (let i = 1; i <= total; i += 1) {
    steps.push(concepts.filter((node) => stepOf.get(node.key) === i).sort(byName));
  }
  return { concepts, steps, stepOf, related, edges };
}

/** The prerequisites of a concept by distance, each with an edge that justifies it. */
export function prerequisitesByDepth(subgraph, key) {
  const byDepth = new Map();
  for (const node of subgraph.nodes) {
    if (node.key === key || node.label !== 'Concept' || !(node.depth >= 1)) continue;
    if (!byDepth.has(node.depth)) byDepth.set(node.depth, []);
    const edge = subgraph.edges.find((e) => e.type === 'HAS_PREREQUISITE' && e.target === node.key && e.source === key)
      ?? subgraph.edges.find((e) => e.type === 'HAS_PREREQUISITE' && e.target === node.key)
      ?? null;
    byDepth.get(node.depth).push({ node, edge });
  }
  return [...byDepth.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([depth, items]) => ({ depth, items: items.sort((a, b) => byName(a.node, b.node)) }));
}

/** The resources about an element or its parts, with the parts each one reaches it by, and its type. */
export function resourcesOf(subgraph) {
  const nodes = indexOf(subgraph);
  const found = new Map();
  for (const edge of subgraph.edges) {
    if (edge.type !== 'IS_ABOUT') continue;
    const resource = nodes.get(edge.source);
    if (!resource) continue;
    if (!found.has(resource.key)) found.set(resource.key, { resource, about: [], type: null });
    const element = nodes.get(edge.target);
    if (element) found.get(resource.key).about.push(element);
  }
  for (const edge of subgraph.edges) {
    if (edge.type === 'HAS_RESOURCE_TYPE' && found.has(edge.source)) {
      found.get(edge.source).type = nodes.get(edge.target) ?? null;
    }
  }
  return [...found.values()]
    .map((entry) => ({ ...entry, about: entry.about.sort(byName) }))
    .sort((a, b) => byName(a.resource, b.resource));
}

/** The lifted path: the stops of the grain, farthest first, and the prerequisites under them. */
export function pathSummary(subgraph, key, grain) {
  const label = GRAINS[grain].label;
  const stops = subgraph.nodes
    .filter((node) => node.label === label && node.depth >= 1 && node.key !== key)
    .sort((a, b) => b.depth - a.depth || byName(a, b));
  const prerequisites = subgraph.nodes.filter((node) => node.label === 'Concept' && node.depth >= 1);
  return { stops, prerequisites, empty: !subgraph.nodes.some((node) => node.depth >= 1) };
}

/** Whether `target` is part of `stop`, at any height: its own topic or area. */
export function containsTarget(subgraph, stop, target) {
  let front = [target];
  const seen = new Set(front);
  while (front.length) {
    const next = [];
    for (const key of front) {
      for (const edge of subgraph.edges) {
        if (edge.type !== 'PART_OF' || edge.source !== key || seen.has(edge.target)) continue;
        if (edge.target === stop) return true;
        seen.add(edge.target);
        next.push(edge.target);
      }
    }
    front = next;
  }
  return false;
}

/**
 * The edges of the response that join a stop with the target: the shortest
 * way that reaches the target by a prerequisite, not by «is part of».
 */
export function justifyStop(subgraph, stop, target) {
  const adjacent = new Map();
  const put = (from, to, edge) => {
    if (!adjacent.has(from)) adjacent.set(from, []);
    adjacent.get(from).push({ key: to, edge });
  };
  for (const edge of subgraph.edges) {
    if (edge.type === DERIVATION) continue;
    put(edge.source, edge.target, edge);
    put(edge.target, edge.source, edge);
  }
  const previous = new Map([[stop, null]]);
  const queue = [stop];
  while (queue.length) {
    const key = queue.shift();
    if (key === target) break;
    for (const step of adjacent.get(key) ?? []) {
      if (previous.has(step.key)) continue;
      if (step.key === target && step.edge.type !== 'HAS_PREREQUISITE') continue;
      previous.set(step.key, { key, edge: step.edge });
      queue.push(step.key);
    }
  }
  if (!previous.get(target)) return [];
  const edges = [];
  for (let key = target; previous.get(key); key = previous.get(key).key) edges.unshift(previous.get(key).edge);
  return edges;
}

/** What a course requires and teaches, and the courses that teach what it requires, with the evidence. */
export function previousCourses(subgraph, key) {
  const nodes = indexOf(subgraph);
  const requiredEdges = subgraph.edges.filter((edge) => edge.type === 'REQUIRES_CONCEPT' && edge.source === key);
  const required = new Set(requiredEdges.map((edge) => edge.target));
  const byCourse = new Map();
  for (const edge of subgraph.edges) {
    if (edge.type !== 'TEACHES_CONCEPT' || edge.source === key || !required.has(edge.target)) continue;
    const course = nodes.get(edge.source);
    const concept = nodes.get(edge.target);
    if (!course || !concept) continue;
    if (!byCourse.has(course.key)) byCourse.set(course.key, { course, evidence: [] });
    byCourse.get(course.key).evidence.push({ node: concept, edge });
  }
  return {
    required: requiredEdges.map((edge) => ({ node: nodes.get(edge.target), edge })).filter((item) => item.node)
      .sort((a, b) => byName(a.node, b.node)),
    previous: [...byCourse.values()].sort((a, b) => byName(a.course, b.course)),
    taught: subgraph.edges.filter((edge) => edge.type === 'TEACHES_CONCEPT' && edge.source === key)
      .map((edge) => ({ node: nodes.get(edge.target), edge })).filter((item) => item.node)
      .sort((a, b) => byName(a.node, b.node)),
  };
}

/** What a concept is a kind of and which kinds it has, directly; `all` is the whole closure. */
export function kindsOf(subgraph, key) {
  const nodes = indexOf(subgraph);
  const all = subgraph.edges.filter((edge) => edge.type === 'SPECIALIZES');
  const item = (edge, end) => ({ node: nodes.get(edge[end]), edge });
  return {
    general: all.filter((edge) => edge.source === key).map((edge) => item(edge, 'target')).filter((i) => i.node),
    kinds: all.filter((edge) => edge.target === key).map((edge) => item(edge, 'source')).filter((i) => i.node)
      .sort((a, b) => byName(a.node, b.node)),
    all,
  };
}
