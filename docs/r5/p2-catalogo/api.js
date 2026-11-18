// Acceso a datos de la maqueta P2.
//
// Toda la aplicación pide datos solo por `api(ruta, params, opciones)`. En la
// maqueta, `api` lee las respuestas reales capturadas en `IEKG_DATOS` (y las de
// operación en `IEKG_OPERACION`). En R6 basta con cambiar el cuerpo por un
// fetch a la API de R4:
//
//   const r = await fetch(`/api${ruta}?${new URLSearchParams(params)}`,
//                         { headers: token ? { Authorization: `Bearer ${token}` } : {} });
//   if (!r.ok) throw { status: r.status, body: await r.json() };
//   return r.json();
//
// Lo que ninguna ruta de R4 devuelve hoy (`/api/catalog`) sale de
// `IEKG_SIMULADO` y la respuesta lleva `_simulado: true`, para que la pantalla
// lo marque.
(function (global) {
  'use strict';

  const DATOS = global.IEKG_DATOS || {};
  const OPERACION = global.IEKG_OPERACION || {};
  const SIMULADO = global.IEKG_SIMULADO || { areas: [], courses: [] };

  // Rutas de navegación de R4 que toman una clave (`?key=`).
  const RUTAS_POR_CLAVE = [
    '/api/nodes',
    '/api/concepts/prerequisites',
    '/api/concepts/specializations',
    '/api/courses/prerequisites',
    '/api/elements/location',
    '/api/elements/resources',
  ];

  function quitarTildes(texto) {
    return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function noEncontrado(ruta, params) {
    return { status: 404, body: { detail: `sin respuesta capturada para ${ruta} ${JSON.stringify(params)}` } };
  }

  // Búsqueda: las 15 consultas capturadas son reales. Para cualquier otro texto,
  // la maqueta filtra en cliente sobre los nombres de los 491 nodos y lo marca
  // como simulado (en R6 lo resuelve el índice de texto completo de R4).
  function buscar(q) {
    const texto = (q || '').trim().toLowerCase();
    const capturadas = DATOS['/api/search'] || {};
    if (Object.prototype.hasOwnProperty.call(capturadas, texto)) {
      return capturadas[texto];
    }
    const palabras = quitarTildes(texto).split(/[^a-z0-9.]+/).filter(Boolean);
    const nodos = [];
    if (palabras.length) {
      for (const clave of Object.keys(DATOS['/api/nodes'] || {})) {
        const n = DATOS['/api/nodes'][clave].nodes[0];
        if (n.label === 'ResourceType') continue;
        const nombre = quitarTildes(`${n.name_es || ''} ${n.name_en || ''} ${n.course_code || ''}`);
        const enNombre = nombre.split(/[^a-z0-9.]+/);
        if (palabras.every((p) => enNombre.some((w) => w.startsWith(p)))) {
          nodos.push({ key: n.key, label: n.label, name_es: n.name_es, name_en: n.name_en,
                       layer: n.layer, course_code: n.course_code });
        }
        if (nodos.length >= 20) break;
      }
    }
    return { nodes: nodos, edges: [], _simulado: true };
  }

  function operacion(ruta, opciones) {
    if (!opciones || !opciones.token) {
      const [status, body] = OPERACION['GET /api/runs (sin token)'] || [401, { detail: 'missing or wrong operator token' }];
      return { status, body };
    }
    const cuerpo = OPERACION[`GET ${ruta}`];
    return cuerpo === undefined ? { status: 404, body: { detail: 'Not Found' } } : cuerpo;
  }

  function resolver(ruta, params, opciones) {
    params = params || {};
    if (ruta === '/api/search') return buscar(params.q);
    if (ruta === '/api/learning-path') {
      const porGrano = DATOS[`/api/learning-path?grain=${params.grain}`];
      return porGrano && porGrano[params.key] ? porGrano[params.key] : noEncontrado(ruta, params);
    }
    if (RUTAS_POR_CLAVE.includes(ruta)) {
      const tabla = DATOS[ruta] || {};
      return tabla[params.key] || noEncontrado(ruta, params);
    }
    if (ruta === '/api/catalog') {
      // RUTA NUEVA NECESARIA (ver README §5). Simulada desde IEKG_SIMULADO.
      return { areas: SIMULADO.areas, courses: SIMULADO.courses, _simulado: true };
    }
    if (ruta.startsWith('/api/runs') || ruta.startsWith('/api/audit-reports')) {
      return operacion(ruta, opciones);
    }
    return noEncontrado(ruta, params);
  }

  // Misma firma asíncrona que tendrá el fetch de R6. Rechaza con {status, body}.
  function api(ruta, params, opciones) {
    const r = resolver(ruta, params, opciones);
    if (r && typeof r.status === 'number' && r.body !== undefined) return Promise.reject(r);
    return Promise.resolve(r);
  }

  // Ruta de documentos (RF-21, RF-24): el localizador ya es la URL completa.
  function urlDocumento(nodoRecurso) {
    return nodoRecurso && nodoRecurso.locator ? nodoRecurso.locator : null;
  }

  global.IEKG_API = { api, urlDocumento, quitarTildes, busquedasCapturadas: Object.keys(DATOS['/api/search'] || {}) };
})(typeof window !== 'undefined' ? window : globalThis);
