/* Acceso a datos de la maqueta P3 · Itinerario.
 *
 * Toda lectura pasa por api(ruta, params). En la maqueta lee de window.IEKG_DATOS
 * (respuestas reales capturadas de la API de R4). En R6 basta reemplazar el cuerpo
 * por el fetch comentado: la forma de las respuestas es la misma.
 *
 * Dos rutas NO existen todavía en R4 y se simulan aquí, marcadas con _simulado:
 *   GET /api/learning-path/targets   destinos con ruta no vacía (sale de las respuestas reales de learning-path)
 *   GET /api/courses                 lista de cursos (sale de IEKG_SIMULADO.courses)
 *   GET /api/areas                   las 17 áreas con sus cuentas (sale de IEKG_SIMULADO.areas)
 */
(function (root) {
  'use strict';

  const BASE = 'http://localhost:8000'; // solo para R6
  const RUTAS_POR_CLAVE = [
    '/api/nodes',
    '/api/concepts/prerequisites',
    '/api/concepts/specializations',
    '/api/courses/prerequisites',
    '/api/elements/location',
    '/api/elements/resources'
  ];
  const RUTAS_NUEVAS = ['/api/learning-path/targets', '/api/courses', '/api/areas'];

  function D() { return root.IEKG_DATOS || {}; }
  function S() { return root.IEKG_SIMULADO || { areas: [], courses: [] }; }

  function noEncontrado(ruta, params) {
    return { status: 404, detail: 'not found', ruta: ruta, params: params };
  }

  function leer(ruta, params) {
    const datos = D();
    if (ruta === '/api/search') {
      return (datos['/api/search'] || {})[params.q];
    }
    if (ruta === '/api/learning-path') {
      return (datos['/api/learning-path?grain=' + params.grain] || {})[params.key];
    }
    if (RUTAS_POR_CLAVE.indexOf(ruta) >= 0) {
      return (datos[ruta] || {})[params.key];
    }
    if (ruta === '/api/learning-path/targets') return simularDestinos();
    if (ruta === '/api/courses') return simularCursos();
    if (ruta === '/api/areas') return simularAreas();
    return undefined;
  }

  /** api(ruta, params) -> Promise<respuesta>. Rechaza con {status: 404} si la API respondería 404. */
  function api(ruta, params) {
    params = params || {};
    // R6:
    // const qs = new URLSearchParams(params).toString();
    // return fetch(`${BASE}${ruta}${qs ? '?' + qs : ''}`).then(r => r.ok ? r.json() : Promise.reject({status: r.status}));
    return new Promise(function (resolve, reject) {
      const r = leer(ruta, params);
      if (r === undefined) reject(noEncontrado(ruta, params));
      else resolve(r);
    });
  }

  /* ---------- rutas nuevas (simuladas) ---------- */

  // GET /api/learning-path/targets -> {targets: [{key, label, name_es, layer, max_depth, courses[], areas[]}], _simulado}
  let cacheDestinos = null;
  function simularDestinos() {
    if (cacheDestinos) return cacheDestinos;
    const datos = D();
    const topic = datos['/api/learning-path?grain=topic'] || {};
    const course = datos['/api/learning-path?grain=course'] || {};
    const area = datos['/api/learning-path?grain=area'] || {};
    const targets = [];
    Object.keys(topic).forEach(function (k) {
      const r = topic[k];
      let max = 0;
      r.nodes.forEach(function (n) { if (n.label === 'Concept' && n.depth > max) max = n.depth; });
      if (max === 0) return;
      const obj = r.nodes.find(function (n) { return n.key === k; });
      const cursos = ((course[k] || { nodes: [] }).nodes)
        .filter(function (n) { return n.label === 'Course' && n.depth !== undefined; })
        .map(function (n) { return n.course_code; });
      const areas = ((area[k] || { nodes: [] }).nodes)
        .filter(function (n) { return n.label === 'KnowledgeArea' && n.depth !== undefined; })
        .map(function (n) { return n.key.split('#KA-')[1]; });
      targets.push({ key: k, label: obj.label, name_es: obj.name_es, layer: obj.layer, max_depth: max, courses: cursos, areas: areas });
    });
    targets.sort(function (a, b) { return a.name_es.localeCompare(b.name_es, 'es'); });
    cacheDestinos = { targets: targets, _simulado: true };
    return cacheDestinos;
  }

  // GET /api/courses -> {nodes: [{key, label:'Course', name_es, course_code, layer}], _simulado}
  function simularCursos() {
    return {
      nodes: S().courses.map(function (c) {
        return { key: c.key, label: 'Course', name_es: c.name_es, name_en: null, layer: 'institutional', course_code: c.code };
      }),
      _simulado: true
    };
  }

  // GET /api/areas -> {nodes: [{key, label:'KnowledgeArea', name_es, name_en, layer, units, topics, concepts}], edges: [], _simulado}
  function simularAreas() {
    return {
      nodes: S().areas.map(function (a) {
        return { key: a.key, label: 'KnowledgeArea', name_es: a.name_es, name_en: a.name_en, layer: 'reference', units: a.units, topics: a.topics, concepts: a.concepts };
      }).sort(function (x, y) { return (y.topics > 0) - (x.topics > 0) || x.name_es.localeCompare(y.name_es, 'es'); }),
      edges: [],
      _simulado: true
    };
  }

  /* ---------- búsqueda ---------- */

  function sinTildes(s) {
    return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  }

  /**
   * Usa /api/search si el texto está entre las búsquedas capturadas; si no, filtra en
   * cliente sobre los nombres de /api/nodes y lo marca como simulado.
   * -> Promise<{nodes, simulada}>
   */
  function buscar(texto) {
    const q = String(texto || '').trim();
    if (!q) return Promise.resolve({ nodes: [], simulada: false });
    const capturadas = Object.keys(D()['/api/search'] || {});
    const exacta = capturadas.find(function (c) { return c.toLowerCase() === q.toLowerCase(); });
    if (exacta !== undefined) {
      return api('/api/search', { q: exacta }).then(function (r) { return { nodes: r.nodes, simulada: false }; });
    }
    const nq = sinTildes(q);
    const nodos = D()['/api/nodes'] || {};
    const res = [];
    Object.keys(nodos).forEach(function (k) {
      const n = nodos[k].nodes[0];
      if (n.label === 'ResourceType') return;
      const nombre = sinTildes(n.name_es) + ' ' + sinTildes(n.name_en) + ' ' + sinTildes(n.course_code);
      const i = nombre.indexOf(nq);
      if (i >= 0) res.push({ n: n, rank: (i === 0 ? 0 : 1) + nombre.length / 1000 });
    });
    res.sort(function (a, b) { return a.rank - b.rank; });
    return Promise.resolve({
      nodes: res.slice(0, 20).map(function (x) {
        return { key: x.n.key, label: x.n.label, name_es: x.n.name_es, name_en: x.n.name_en, layer: x.n.layer, course_code: x.n.course_code };
      }),
      simulada: true
    });
  }

  const exportado = {
    api: api,
    buscar: buscar,
    sinTildes: sinTildes,
    BASE: BASE,
    RUTAS_NUEVAS: RUTAS_NUEVAS,
    busquedasCapturadas: function () { return Object.keys(D()['/api/search'] || {}); }
  };
  root.IEKG_API = exportado;
  if (typeof module !== 'undefined' && module.exports) module.exports = exportado;
})(typeof window !== 'undefined' ? window : globalThis);
