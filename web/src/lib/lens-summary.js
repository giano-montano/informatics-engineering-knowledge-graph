// What the header says of the active lens: the answer in one sentence and how
// to read the drawing (ADR-016). The sentences count what the response
// brought; they state nothing the graph does not.

import { countByClass, kindsOf, locationChains, partsOf, previousCourses, resourcesOf } from './graph-reading.js';
import { MAX_CONCEPTS_IN_TREE } from './layouts.js';
import { GRAINS, plural } from './vocabulary.js';

const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };

export function escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"]/g, (c) => ENTITIES[c]);
}

const strong = (text) => `<strong>${escapeHtml(text)}</strong>`;

// The title right above already names the focus, so a sentence that would only
// repeat it leaves the name to the screen reader, which announces the sentence
// on its own.
const unseen = (node) => `<span class="sr-only">${escapeHtml(node.name_es)}: </span>`;

function joined(parts) {
  if (parts.length < 2) return parts.join('');
  return `${parts.slice(0, -1).join(', ')} y ${parts.at(-1)}`;
}

export function overviewSummary(info) {
  return {
    answer: `Alrededor, las ${strong(plural(info.areas, 'área', 'áreas'))} de CS2023; las ${info.filled} encendidas ya tienen temas de los sílabos. `
      + `Al centro, ${info.courses === 1 ? 'el' : 'los'} ${strong(plural(info.courses, 'curso', 'cursos'))} con sílabo.`,
    how: 'Elige un área o un curso, o busca por nombre arriba.',
  };
}

export function lensSummary({ lens, grain, node, response, scene }) {
  if (!node || !scene) return { answer: '', how: '' };
  const name = strong(node.name_es);
  const info = scene.info ?? {};
  switch (lens) {
    case 'neighborhood': {
      if (!info.direct) return { answer: `${name} todavía no tiene relaciones registradas.`, how: '' };
      const how = ['A la izquierda, de qué es parte y qué necesita; a la derecha, lo que contiene y lo que sigue. Elige un punto para ir a él.'];
      if (info.clusters) how.push('Un grupo grande va en un recuadro de puntos sin nombre: la lista está en «Conexiones», en la ficha.');
      if (info.far) how.push('Los puntos apagados de arriba están un paso más lejos.');
      how.push('El <b class="plus-sign">+</b> trae las conexiones de un punto sin cambiar de lugar.');
      return {
        answer: `${unseen(node)}${plural(info.direct, 'elemento conectado', 'elementos conectados')} directamente, agrupados por tipo de relación.`,
        how: how.join(' '),
      };
    }
    case 'prerequisites': {
      if (!info.total) {
        const needed = info.dependents?.length ? ` Se necesita para ${joined(info.dependents.map((n) => strong(n.name_es)))}.` : '';
        return { answer: `${name} no necesita nada antes, según los sílabos cargados: puedes empezar por aquí.${needed}`, how: '' };
      }
      const distance = info.maxDepth > 1 ? `, el más lejano a ${info.maxDepth} pasos.` : info.total > 1 ? ', todos justo antes.' : ', justo antes.';
      return {
        answer: `${unseen(node)}Necesitas saber antes ${plural(info.total, 'concepto', 'conceptos')}${distance}`,
        how: 'Se lee de izquierda a derecha: cada flecha sale de lo que se aprende primero y llega a lo que lo necesita. Elige una flecha, o «fuente» en la ficha, para ver qué sílabo lo dice.',
      };
    }
    case 'path': {
      const g = GRAINS[grain];
      if (info.empty) {
        return node.label === 'Course'
          ? { answer: `Lo que ${name} enseña no necesita antes nada de fuera del curso, según los sílabos cargados: no hay camino previo por ${g.plural}. Lo que el curso pide de entrada es otra pregunta.`, how: '', offer: 'courses' }
          : { answer: `Para llegar a ${name} no hace falta pasar antes por ${g.another}, según los sílabos cargados.`, how: '' };
      }
      const where = grain === 'course' ? 'se enseña' : 'está';
      const rows = grain === 'area' ? 'las áreas, con su unidad y su tema,' : `los ${g.plural}`;
      // A course has two answers that differ: this one follows what its
      // concepts need before; the other, what the course itself asks for.
      const course = node.label === 'Course';
      return {
        answer: `${unseen(node)}Conviene pasar antes por ${plural(info.stops.length, g.name, g.plural)}: ahí ${where} lo que necesitas saber antes (${plural(info.prerequisites.length, 'concepto', 'conceptos')}).`
          + (course ? ' Sale de lo que necesitan antes los conceptos que el curso enseña; lo que el curso pide de entrada es otra pregunta.' : ''),
        offer: course ? 'courses' : undefined,
        how: `Abajo, los conceptos que necesitas antes; arriba, ${rows} donde se aprenden. «¿Por qué?» muestra la relación exacta y su fuente.`
          + (info.own ? ` «${escapeHtml(info.own.name_es)}» cuenta aunque también contiene a la meta: lo que se necesita antes es el concepto.` : ''),
      };
    }
    case 'courses': {
      const reading = previousCourses(response, node.key);
      const taught = plural(reading.taught.length, 'concepto', 'conceptos');
      const list = info.boxed ? 'En el recuadro, lo que el curso enseña: la lista con nombres está en la ficha.' : '';
      if (!reading.previous.length) {
        return {
          answer: `${name} enseña ${taught}` + (reading.required.length
            ? ` y pide ${reading.required.length} que ningún otro curso cargado enseña.`
            : ' y no pide ninguno de otro curso cargado: no hay curso que convenga llevar antes.'),
          how: list,
        };
      }
      return {
        answer: `${name} pide ${plural(reading.required.length, 'concepto', 'conceptos')} que enseña ${joined(reading.previous.map((p) => strong(p.course.name_es)))}: conviene llevarlo antes.`,
        how: `De izquierda a derecha: el curso que conviene llevar antes, lo que este curso pide y los ${taught} que enseña. ${list}`,
      };
    }
    case 'location': {
      const chain = locationChains(response, node.key)[0] ?? [];
      return {
        answer: chain.length ? `${name} está en ${chain.map((n) => strong(n.name_es)).join(' › ')}.` : `${name} está en el nivel más alto.`,
        how: 'De arriba abajo, de lo más general a lo más específico. Los hexágonos son del estándar CS2023; los círculos, de los sílabos. Elige cualquiera para ir a él.',
      };
    }
    case 'contents': {
      if (info.kind === 'steps') {
        if (!info.concepts) return { answer: `${name} todavía no tiene conceptos registrados.`, how: '' };
        if (!info.ordered) {
          return { answer: `${name} tiene ${plural(info.concepts, 'concepto', 'conceptos')}. Ninguno depende de otro: se pueden aprender en cualquier orden.`, how: 'Elige un concepto para ver qué necesita antes.' };
        }
        return {
          answer: `${unseen(node)}${plural(info.concepts, 'concepto', 'conceptos')}, que conviene aprender en ${plural(info.steps, 'paso', 'pasos')}.`,
          how: 'Cada columna es un paso: lo de una columna usa lo de la anterior. Las flechas dicen exactamente qué necesita qué.',
        };
      }
      const counts = countByClass(partsOf(response, node.key));
      const parts = [['KnowledgeUnit', 'unidad', 'unidades'], ['Topic', 'tema', 'temas'], ['Concept', 'concepto', 'conceptos']]
        .filter(([label]) => counts[label]).map(([label, one, many]) => strong(plural(counts[label], one, many)));
      if (!counts.Topic) {
        return { answer: `${name} contiene ${joined(parts) || 'nada todavía'}. Ningún sílabo cargado trata esta parte de CS2023 por ahora.`, how: '' };
      }
      const how = info.withConcepts
        ? 'De izquierda a derecha, de lo más general a lo más específico. Entra a un tema para ver en qué orden aprender sus conceptos.'
        : `Con más de ${MAX_CONCEPTS_IN_TREE} conceptos, el mapa llega hasta los temas para que se pueda leer. Entra a un tema para ver sus conceptos y en qué orden aprenderlos.`;
      return {
        answer: `${unseen(node)}Contiene ${joined(parts)}.`,
        how: how + (info.summarized ? ' Las unidades sin temas están en «Conexiones», en la ficha.' : ''),
      };
    }
    case 'resources': {
      const found = resourcesOf(response);
      if (!found.length) {
        return node.label === 'Concept'
          ? { answer: `${name} no tiene material propio: los sílabos describen temas, no conceptos sueltos. En la ficha tienes el de su tema.`, how: '' }
          : { answer: `Ningún sílabo cargado trata sobre ${name} ni sobre sus partes.`, how: '' };
      }
      return {
        answer: `${plural(found.length, 'sílabo trata', 'sílabos tratan')} sobre ${name} o sobre sus partes.`,
        how: 'De izquierda a derecha: el elemento, sus partes y los sílabos que tratan sobre ellas. El enlace para abrir cada sílabo está en la ficha.',
      };
    }
    case 'kinds': {
      const reading = kindsOf(response, node.key);
      if (!reading.all.length) {
        return { answer: `${name} no es un tipo de otro concepto ni tiene tipos registrados en los sílabos cargados.`, how: '' };
      }
      const of = reading.general.length ? ` es un tipo de ${joined(reading.general.map((i) => strong(i.node.name_es)))}` : '';
      const has = reading.kinds.length ? ` tiene ${plural(reading.kinds.length, 'tipo', 'tipos')}` : '';
      return {
        answer: `${name}${of}${of && has ? ' y' : ''}${has}.`,
        how: 'Arriba, el concepto más general; abajo, sus tipos. La flecha se lee «es un tipo de».',
      };
    }
    default:
      return { answer: '', how: '' };
  }
}
