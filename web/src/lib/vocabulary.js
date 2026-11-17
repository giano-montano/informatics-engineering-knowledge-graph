// What the interface calls each thing of the graph. Identifiers are the
// graph's; the text is the common vocabulary of docs/r5/README.md.

export const CLASSES = {
  KnowledgeArea: { name: 'Área', plural: 'áreas', article: 'un área', color: 'var(--c-area)' },
  KnowledgeUnit: { name: 'Unidad', plural: 'unidades', article: 'una unidad', color: 'var(--c-unit)' },
  Topic: { name: 'Tema', plural: 'temas', article: 'un tema', color: 'var(--c-topic)' },
  Concept: { name: 'Concepto', plural: 'conceptos', article: 'un concepto', color: 'var(--c-concept)' },
  Course: { name: 'Curso', plural: 'cursos', article: 'un curso', color: 'var(--c-course)' },
  LearningResource: { name: 'Documento', plural: 'documentos', article: 'un documento', color: 'var(--c-resource)' },
  ResourceType: { name: 'Tipo de recurso', plural: 'tipos de recurso', article: 'un tipo de recurso', color: 'var(--c-type)' },
};

export const CLASS_ORDER = Object.keys(CLASSES);
export const KNOWLEDGE_ELEMENTS = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept'];

/** A syllabus is a learning resource of the institutional layer. */
export function className(node) {
  if (node.label === 'LearningResource') return node.layer === 'institutional' ? 'Sílabo' : 'Documento';
  return CLASSES[node.label]?.name ?? node.label;
}

export function classArticle(node) {
  if (node.label === 'LearningResource') return node.layer === 'institutional' ? 'un sílabo' : 'un documento';
  return CLASSES[node.label]?.article ?? 'un elemento';
}

export function classColor(node) {
  return CLASSES[node.label]?.color ?? 'var(--c-type)';
}

// The layer is told by shape and by text, never by color alone (ADR-019).
export const LAYERS = {
  reference: {
    name: 'CS2023',
    of: 'de CS2023',
    shape: 'hexágono',
    detail: 'Viene de CS2023, el estándar internacional del currículo de computación (ACM/IEEE).',
  },
  institutional: {
    name: 'Sílabo PUCP',
    of: 'de un sílabo',
    shape: 'círculo',
    detail: 'Viene del sílabo de un curso de la especialidad.',
  },
};

export function layerOf(node) {
  return LAYERS[node.layer] ?? LAYERS.institutional;
}

/** What a screen reader says of a node: class, name and layer. */
export function accessibleName(node) {
  const code = node.course_code ? ` (${node.course_code})` : '';
  return `${className(node)} ${node.name_es ?? node.key}${code}, ${layerOf(node).of}`;
}

// How each relationship reads from its source (out) and from its target (in).
export const RELATIONS = {
  PART_OF: { out: 'Es parte de', in: 'Contiene', phrase: 'es parte de', color: 'var(--r-part)' },
  HAS_PREREQUISITE: { out: 'Necesita antes', in: 'Se necesita para', phrase: 'necesita antes', color: 'var(--r-prerequisite)' },
  SPECIALIZES: { out: 'Es un tipo de', in: 'Tipos', phrase: 'es un tipo de', color: 'var(--r-kind)' },
  TEACHES_CONCEPT: { out: 'Lo que enseña', in: 'Lo enseña el curso', phrase: 'enseña', color: 'var(--r-teaches)' },
  REQUIRES_CONCEPT: { out: 'Lo que pide', in: 'Lo pide el curso', phrase: 'pide', color: 'var(--r-requires)' },
  IS_ABOUT: { out: 'Trata sobre', in: 'Material de estudio', phrase: 'trata sobre', color: 'var(--r-about)' },
  HAS_RESOURCE_TYPE: { out: 'Es de tipo', in: 'Recursos de este tipo', phrase: 'es de tipo', color: 'var(--r-type)' },
  WAS_DERIVED_FROM: { out: 'Fuente', in: 'Es fuente de', phrase: 'sale de', color: 'var(--r-source)' },
};

// In the order a student reads a neighborhood: what it belongs to and needs
// first, then what hangs from it.
export const CONNECTION_ORDER = [
  'PART_OF:out', 'HAS_PREREQUISITE:out', 'SPECIALIZES:out', 'REQUIRES_CONCEPT:out',
  'HAS_PREREQUISITE:in', 'TEACHES_CONCEPT:in', 'REQUIRES_CONCEPT:in', 'SPECIALIZES:in',
  'PART_OF:in', 'TEACHES_CONCEPT:out', 'IS_ABOUT:in', 'IS_ABOUT:out',
  'HAS_RESOURCE_TYPE:out', 'HAS_RESOURCE_TYPE:in',
];

// The eight lenses (ADR-016). Each one is a question about the element in
// focus; which ones apply is decided by its class, without asking the API.
// `slug` is what the URL shows.
const WITH_COURSE = [...KNOWLEDGE_ELEMENTS, 'Course'];
export const LENSES = {
  neighborhood: { slug: 'rodea', name: 'Lo que lo rodea', path: '/api/nodes', classes: null,
    question: '¿Con qué se relaciona directamente?' },
  prerequisites: { slug: 'antes', name: 'Qué necesitas antes', path: '/api/concepts/prerequisites', classes: ['Concept'],
    question: '¿Qué conceptos conviene saber antes de aprender este?' },
  path: { slug: 'camino', name: 'Camino hasta aquí', path: '/api/learning-path', classes: WITH_COURSE,
    question: '¿Por qué temas, cursos o áreas conviene pasar antes de llegar aquí?' },
  courses: { slug: 'cursos', name: 'Cursos que conviene llevar antes', path: '/api/courses/prerequisites', classes: ['Course'],
    question: '¿Qué pide este curso, qué enseña y qué curso conviene llevar antes?' },
  location: { slug: 'ubicacion', name: 'Dónde está en la carrera', path: '/api/elements/location',
    classes: ['KnowledgeUnit', 'Topic', 'Concept'], question: '¿A qué tema, unidad y área pertenece?' },
  contents: { slug: 'contiene', name: 'Qué contiene', path: '/api/elements/location',
    classes: ['KnowledgeArea', 'KnowledgeUnit', 'Topic'], question: '¿De qué partes se compone y en qué orden conviene aprenderlas?' },
  resources: { slug: 'material', name: 'Material de estudio', path: '/api/elements/resources', classes: WITH_COURSE,
    question: '¿Con qué material se puede estudiar?' },
  kinds: { slug: 'tipos', name: 'Tipos', path: '/api/concepts/specializations', classes: ['Concept'],
    question: '¿De qué concepto más general es un tipo y qué tipos tiene?' },
};

export const LENS_ORDER = Object.keys(LENSES);

export function lensApplies(lens, node) {
  const definition = LENSES[lens];
  return Boolean(definition && node && (definition.classes === null || definition.classes.includes(node.label)));
}

export function lensFromSlug(slug) {
  return LENS_ORDER.find((lens) => LENSES[lens].slug === slug) ?? null;
}

export const GRAINS = {
  topic: { slug: 'tema', name: 'tema', plural: 'temas', label: 'Topic', another: 'otro tema', same: 'el mismo tema' },
  course: { slug: 'curso', name: 'curso', plural: 'cursos', label: 'Course', another: 'otro curso', same: 'el mismo curso' },
  area: { slug: 'area', name: 'área', plural: 'áreas', label: 'KnowledgeArea', another: 'otra área', same: 'la misma área' },
};

export const GRAIN_ORDER = Object.keys(GRAINS);

export function grainFromSlug(slug) {
  return GRAIN_ORDER.find((grain) => GRAINS[grain].slug === slug) ?? null;
}

export function plural(count, one, many) {
  return `${count} ${count === 1 ? one : many}`;
}

export function byName(a, b) {
  return (a.name_es ?? '').localeCompare(b.name_es ?? '', 'es');
}
