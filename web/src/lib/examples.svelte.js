// The example searches of the start screen and of a search without results.
//
// No example is written in the application: they are names taken at random
// from the loaded graph. Two courses are drawn from the overview, and the
// topics and concepts next to each one give the names; with no course loaded,
// the names are those of the areas.

import { fetchOverview, fetchSubgraph } from './api-client.js';

const WANTED = 6;
const COURSES_ASKED = 2;

export const examples = $state({ names: [] });

function sample(list, count) {
  const pool = [...list];
  const taken = [];
  while (pool.length && taken.length < count) {
    taken.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
  }
  return taken;
}

let pending = null;

/** Draws the examples once per visit; a failure leaves the list empty. */
export function loadExamples() {
  pending ??= draw().catch(() => {
    pending = null;
  });
  return pending;
}

async function draw() {
  const overview = await fetchOverview();
  const courses = overview.nodes.filter((node) => node.label === 'Course');
  const drawn = sample(courses, COURSES_ASKED);
  const neighborhoods = await Promise.all(drawn.map((course) => fetchSubgraph('/api/nodes', course.key)));
  const names = new Set();
  for (const neighborhood of neighborhoods) {
    const taught = neighborhood.nodes.filter((node) => node.label === 'Topic' || node.label === 'Concept');
    for (const node of sample(taught, WANTED / COURSES_ASKED)) names.add(node.name_es);
  }
  if (names.size < WANTED) {
    const areas = overview.nodes.filter((node) => node.label === 'KnowledgeArea');
    for (const area of sample(areas, WANTED - names.size)) names.add(area.name_es);
  }
  examples.names = [...names];
}
