// The example searches and the suggested tour of the start screen.
//
// These are the only examples written in the application, and they depend on
// the graph: they come from the development graph (4 syllabi) and are to be
// fixed with the final one, like the examples of the acceptance test plan.
// Every step looks its element up by name through the search, so a key is
// never written here; a step whose element is not in the graph says so.

import { searchByName } from './api-client.js';

export const EXAMPLE_SEARCHES = ['lógica', 'redes', 'programación', 'archivos', 'ethernet', 'seguridad', 'INF144'];

const fold = (text) => String(text ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

async function find(query, label, name) {
  const response = await searchByName(query);
  return response.nodes.find((node) => node.score !== undefined && node.label === label && fold(node.name_es) === fold(name)) ?? null;
}

const step = (text, query, label, name, lens, grain) => ({ text, query, label, name, lens, grain });

export const TOUR = [
  step('Busca «lógica» y abre el tema «Lógica proposicional».', 'lógica proposicional', 'Topic', 'Lógica proposicional', 'neighborhood'),
  step('Mira qué contiene y en qué orden conviene aprenderlo.', 'lógica proposicional', 'Topic', 'Lógica proposicional', 'contents'),
  step('Abre «Contradicción»: ¿qué necesitas saber antes?', 'contradicción', 'Concept', 'Contradicción', 'prerequisites'),
  step('El camino hasta «Entrada y salida de datos desde archivos», visto por cursos.', 'entrada y salida de datos desde archivos', 'Concept', 'Entrada y salida de datos desde archivos', 'path', 'course'),
  step('«Técnicas de Programación»: qué pide y qué curso conviene llevar antes.', 'técnicas de programación', 'Course', 'Técnicas de Programación', 'courses'),
  step('¿Qué tipos de Ethernet hay?', 'ethernet', 'Concept', 'Ethernet IEEE 802.3', 'kinds'),
];

/** Puts the element of a step in focus with its lens; false if the graph does not have it. */
export async function runStep(index, exploration) {
  const wanted = TOUR[index];
  const node = await find(wanted.query, wanted.label, wanted.name);
  if (!node) return false;
  await exploration.focus(node.key, { lens: wanted.lens, grain: wanted.grain });
  return true;
}
