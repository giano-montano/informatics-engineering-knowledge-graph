/* Constelación (P1) · acceso a datos y lógica de presentación sin DOM.
 *
 * `api(ruta, params)` es la ÚNICA puerta a los datos. En la maqueta lee de
 * `window.IEKG_DATOS` (respuestas reales capturadas de R4); en R6 basta con
 * cambiar su cuerpo por el `fetch` comentado. Todo lo demás de este archivo
 * solo reordena lo que devuelve la API: no deriva aristas ni nodos nuevos.
 */
(function (raiz) {
  'use strict';

  // ---------------------------------------------------------------- vocabulario

  const CLASES = {
    KnowledgeArea:    { nombre: 'Área',            corto: 'Área',     color: '#b98cff' },
    KnowledgeUnit:    { nombre: 'Unidad',          corto: 'Unidad',   color: '#8b9bff' },
    Topic:            { nombre: 'Tema',            corto: 'Tema',     color: '#3fd8ff' },
    Concept:          { nombre: 'Concepto',        corto: 'Concepto', color: '#5cffc8' },
    Course:           { nombre: 'Curso',           corto: 'Curso',    color: '#ffbe55' },
    LearningResource: { nombre: 'Recurso',         corto: 'Recurso',  color: '#ff7ab8' },
    ResourceType:     { nombre: 'Tipo de recurso', corto: 'Tipo',     color: '#a9b0d6' },
  };

  /** Nombre de la clase en pantalla: un recurso de los sílabos se llama «sílabo». */
  function nombreClase(n) {
    if (n.label === 'LearningResource') return n.layer === 'institutional' ? 'Sílabo' : 'Documento';
    return CLASES[n.label].nombre;
  }

  const CAPAS = {
    reference:     { nombre: 'CS2023', detalle: 'estándar internacional del currículo de computación (ACM/IEEE)', forma: 'hexágono con contorno' },
    institutional: { nombre: 'Sílabo PUCP', detalle: 'lo que dicen los sílabos de los cursos', forma: 'círculo relleno' },
  };

  // Cómo se lee cada relación desde el origen (salida) o desde el destino (entrada).
  const RELACIONES = {
    PART_OF:           { salida: 'Es parte de',       entrada: 'Contiene',               frase: 'es parte de' },
    HAS_PREREQUISITE:  { salida: 'Necesita antes',    entrada: 'Se necesita para',       frase: 'necesita antes' },
    SPECIALIZES:       { salida: 'Es un tipo de',     entrada: 'Tipos',                  frase: 'es un tipo de' },
    TEACHES_CONCEPT:   { salida: 'Lo que enseña',     entrada: 'Lo enseña el curso',     frase: 'enseña' },
    REQUIRES_CONCEPT:  { salida: 'Lo que pide',       entrada: 'Lo pide el curso',       frase: 'pide' },
    IS_ABOUT:          { salida: 'Trata sobre',       entrada: 'Material de estudio',    frase: 'trata sobre' },
    HAS_RESOURCE_TYPE: { salida: 'Es de tipo',        entrada: 'Recursos de este tipo',  frase: 'es de tipo' },
    WAS_DERIVED_FROM:  { salida: 'Fuente',            entrada: 'Es fuente de',           frase: 'sale de' },
  };

  // Las vistas del mapa. Cada una responde una pregunta del estudiante sobre el elemento en foco,
  // y cuáles aplican lo decide la clase del nodo, sin llamar a la API.
  // `nombre` es el vocabulario común a las tres propuestas; `ayuda`, la pregunta en lenguaje llano.
  const ELEMENTOS = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept'];
  const LENTES = {
    vecindario:        { nombre: 'Lo que lo rodea', ruta: '/api/nodes', clases: null,
                         ayuda: '¿Con qué se relaciona directamente?' },
    prerrequisitos:    { nombre: 'Qué necesitas antes', ruta: '/api/concepts/prerequisites', clases: ['Concept'],
                         ayuda: '¿Qué conceptos conviene saber antes de aprender este?' },
    ruta:              { nombre: 'Camino hasta aquí', ruta: '/api/learning-path', clases: ELEMENTOS.concat('Course'),
                         ayuda: '¿Por qué temas, cursos o áreas conviene pasar antes de llegar aquí?' },
    cursos:            { nombre: 'Cursos que conviene llevar antes', ruta: '/api/courses/prerequisites', clases: ['Course'],
                         ayuda: '¿Qué pide este curso, qué enseña y qué curso conviene llevar antes?' },
    ubicacion:         { nombre: 'Dónde está en la carrera', ruta: '/api/elements/location', clases: ['KnowledgeUnit', 'Topic', 'Concept'],
                         ayuda: '¿A qué tema, unidad y área pertenece?' },
    contiene:          { nombre: 'Qué contiene', ruta: '/api/elements/location', clases: ['KnowledgeArea', 'KnowledgeUnit', 'Topic'],
                         ayuda: '¿De qué partes se compone y en qué orden conviene aprenderlas?' },
    recursos:          { nombre: 'Material de estudio', ruta: '/api/elements/resources', clases: ELEMENTOS.concat('Course'),
                         ayuda: '¿Con qué material se puede estudiar?' },
    especializaciones: { nombre: 'Tipos', ruta: '/api/concepts/specializations', clases: ['Concept'],
                         ayuda: '¿De qué concepto más general es un tipo y qué tipos tiene?' },
  };

  const GRANOS = {
    topic:  { nombre: 'tema',  plural: 'temas',  clase: 'Topic' },
    course: { nombre: 'curso', plural: 'cursos', clase: 'Course' },
    area:   { nombre: 'área',  plural: 'áreas',  clase: 'KnowledgeArea' },
  };

  // ---------------------------------------------------------------- utilidades

  function normalizar(texto) {
    return String(texto || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  }

  function clonar(valor) { return JSON.parse(JSON.stringify(valor)); }

  function nodoPorClave(resp, clave) {
    return resp && resp.nodes ? resp.nodes.find(n => n.key === clave) || null : null;
  }

  function lenteAplica(lente, nodo) {
    const def = LENTES[lente];
    return !!def && !!nodo && (def.clases === null || def.clases.includes(nodo.label));
  }

  // ---------------------------------------------------------------- api()

  /**
   * Devuelve una promesa de `{estado, cuerpo, simulado}`.
   * En R6:
   *   const url = BASE + ruta + '?' + new URLSearchParams(params);
   *   return fetch(url).then(async r => ({ estado: r.status, cuerpo: await r.json(), simulado: false }));
   */
  function api(ruta, params) {
    params = params || {};
    const D = raiz.IEKG_DATOS || {};
    let respuesta = null;
    let simulado = false;

    if (ruta === '/api/search') {
      const capturadas = D['/api/search'] || {};
      const q = String(params.q || '');
      const exacta = Object.keys(capturadas).find(k => k === q)
        || Object.keys(capturadas).find(k => normalizar(k) === normalizar(q));
      if (exacta !== undefined) {
        respuesta = capturadas[exacta];
      } else {
        // La búsqueda libre no está capturada: se filtra en cliente sobre los
        // nombres de los nodos reales y se marca como simulada en pantalla.
        simulado = true;
        const nq = normalizar(q);
        const nodos = [];
        if (nq.length >= 2) {
          for (const r of Object.values(D['/api/nodes'] || {})) {
            const n = r.nodes[0];
            if (normalizar(n.name_es).includes(nq) || normalizar(n.name_en).includes(nq)) {
              nodos.push({ key: n.key, label: n.label, name_es: n.name_es, name_en: n.name_en, layer: n.layer,
                course_code: n.course_code, locator: n.locator });
            }
            if (nodos.length >= 20) break;
          }
        }
        respuesta = { nodes: nodos, edges: [] };
      }
    } else if (ruta === '/api/learning-path') {
      const tabla = D['/api/learning-path?grain=' + (params.grain || 'topic')];
      respuesta = tabla ? tabla[params.key] : null;
    } else {
      const tabla = D[ruta];
      respuesta = tabla ? tabla[params.key] : null;
    }

    if (!respuesta) {
      return Promise.resolve({ estado: 404, cuerpo: { detail: 'not found' }, simulado: false });
    }
    return Promise.resolve({ estado: 200, cuerpo: clonar(respuesta), simulado });
  }

  /** Ruta NUEVA necesaria (no existe en R4): GET /api/overview. Simulada. */
  function apiPortada() {
    const S = raiz.IEKG_SIMULADO || { areas: [], courses: [] };
    return Promise.resolve({
      estado: 200,
      simulado: true,
      cuerpo: {
        areas: clonar(S.areas || []),
        courses: clonar(S.courses || []),
      },
    });
  }

  function busquedasCapturadas() {
    return Object.keys((raiz.IEKG_DATOS || {})['/api/search'] || {}).filter(q => q !== 'arbol');
  }

  // ---------------------------------------------------------------- lecturas de una respuesta

  /** Recursos de los que se derivó un nodo (su arista WAS_DERIVED_FROM). RF-21. */
  function procedenciaDe(resp, clave) {
    return resp.edges
      .filter(e => e.type === 'WAS_DERIVED_FROM' && e.source === clave)
      .map(e => nodoPorClave(resp, e.target))
      .filter(Boolean);
  }

  /** Documento que respalda una arista: su `provenance`; en la capa de referencia, el recurso del origen. */
  function documentoDeArista(resp, arista) {
    if (arista.provenance) return nodoPorClave(resp, arista.provenance);
    const fuentes = procedenciaDe(resp, arista.source);
    return fuentes[0] || null;
  }

  /** Vecinos directos de `clave`, agrupados por relación (sin WAS_DERIVED_FROM). */
  function conexiones(resp, clave) {
    const grupos = new Map();
    for (const e of resp.edges) {
      if (e.type === 'WAS_DERIVED_FROM') continue;
      let sentido = null, otro = null;
      if (e.source === clave) { sentido = 'salida'; otro = e.target; }
      else if (e.target === clave) { sentido = 'entrada'; otro = e.source; }
      if (!sentido) continue;
      const id = e.type + ':' + sentido;
      if (!grupos.has(id)) grupos.set(id, { tipo: e.type, sentido, rotulo: RELACIONES[e.type][sentido], items: [] });
      const nodo = nodoPorClave(resp, otro);
      if (nodo) grupos.get(id).items.push({ nodo, arista: e });
    }
    const orden = ['PART_OF:salida', 'HAS_PREREQUISITE:salida', 'SPECIALIZES:salida', 'REQUIRES_CONCEPT:salida',
      'HAS_PREREQUISITE:entrada', 'TEACHES_CONCEPT:entrada', 'REQUIRES_CONCEPT:entrada', 'SPECIALIZES:entrada',
      'PART_OF:entrada', 'TEACHES_CONCEPT:salida', 'IS_ABOUT:entrada', 'IS_ABOUT:salida',
      'HAS_RESOURCE_TYPE:salida', 'HAS_RESOURCE_TYPE:entrada'];
    return [...grupos.entries()]
      .sort((a, b) => orden.indexOf(a[0]) - orden.indexOf(b[0]))
      .map(([, g]) => {
        g.items.sort((x, y) => x.nodo.name_es.localeCompare(y.nodo.name_es, 'es'));
        return g;
      });
  }

  /** Cadenas de ubicación (de abajo hacia el área) siguiendo PART_OF en la respuesta de location. */
  function cadenasDeUbicacion(resp, clave) {
    const cadenas = [];
    function subir(actual, camino) {
      const padres = resp.edges.filter(e => e.type === 'PART_OF' && e.source === actual).map(e => e.target);
      if (!padres.length || camino.length > 6) { cadenas.push(camino); return; }
      for (const p of padres) {
        const nodo = nodoPorClave(resp, p);
        if (nodo) subir(p, camino.concat(nodo));
      }
    }
    subir(clave, []);
    return cadenas.filter(c => c.length).map(c => c.slice().reverse());
  }

  /** Conteo de la respuesta por clase, sin recursos de procedencia. */
  function conteoPorClase(resp) {
    const c = {};
    for (const n of resp.nodes) c[n.label] = (c[n.label] || 0) + 1;
    return c;
  }

  /** Prerrequisitos (PC1) agrupados por profundidad, con la arista que los justifica. */
  function prerrequisitosPorProfundidad(resp, clave) {
    const porProf = new Map();
    for (const n of resp.nodes) {
      if (n.key === clave || n.label !== 'Concept' || !(n.depth >= 1)) continue;
      if (!porProf.has(n.depth)) porProf.set(n.depth, []);
      const arista = resp.edges.find(e => e.type === 'HAS_PREREQUISITE' && e.target === n.key) || null;
      porProf.get(n.depth).push({ nodo: n, arista, documento: arista ? documentoDeArista(resp, arista) : null });
    }
    return [...porProf.entries()].sort((a, b) => a[0] - b[0])
      .map(([profundidad, items]) => ({ profundidad, items: items.sort((x, y) => x.nodo.name_es.localeCompare(y.nodo.name_es, 'es')) }));
  }

  /** Recursos (PC5): los nodos LearningResource unidos por IS_ABOUT; aparte, la procedencia. */
  function recursosDe(resp, clave) {
    const sobre = new Map();
    for (const e of resp.edges) {
      if (e.type !== 'IS_ABOUT') continue;
      const recurso = nodoPorClave(resp, e.source);
      const elemento = nodoPorClave(resp, e.target);
      if (!recurso) continue;
      if (!sobre.has(recurso.key)) sobre.set(recurso.key, { recurso, elementos: [], tipo: null });
      if (elemento) sobre.get(recurso.key).elementos.push(elemento);
    }
    for (const e of resp.edges) {
      if (e.type === 'HAS_RESOURCE_TYPE' && sobre.has(e.source)) sobre.get(e.source).tipo = nodoPorClave(resp, e.target);
    }
    return [...sobre.values()].sort((a, b) => a.recurso.name_es.localeCompare(b.recurso.name_es, 'es'));
  }

  /** Ruta elevada al grano (PC6): estaciones del grano ordenadas de la más lejana al objetivo. */
  function resumenRuta(resp, clave, grano) {
    const claseGrano = GRANOS[grano].clase;
    const objetivo = nodoPorClave(resp, clave);
    const estaciones = resp.nodes
      .filter(n => n.label === claseGrano && n.depth >= 1)
      .sort((a, b) => b.depth - a.depth || a.name_es.localeCompare(b.name_es, 'es'));
    const prerrequisitos = resp.nodes.filter(n => n.label === 'Concept' && n.depth >= 1);
    return { objetivo, estaciones, prerrequisitos, vacia: !resp.nodes.some(n => n.depth >= 1) };
  }

  /** Cursos previos (PC2): cursos que enseñan lo que el curso en foco requiere; la evidencia son esos conceptos. */
  function cursosPrevios(resp, clave) {
    const requeridos = resp.edges.filter(e => e.type === 'REQUIRES_CONCEPT' && e.source === clave).map(e => e.target);
    const porCurso = new Map();
    for (const e of resp.edges) {
      if (e.type !== 'TEACHES_CONCEPT' || e.source === clave || !requeridos.includes(e.target)) continue;
      const curso = nodoPorClave(resp, e.source);
      if (!curso) continue;
      if (!porCurso.has(curso.key)) porCurso.set(curso.key, { curso, evidencia: [] });
      porCurso.get(curso.key).evidencia.push({ nodo: nodoPorClave(resp, e.target), arista: e });
    }
    const listaEnsenados = resp.edges.filter(e => e.type === 'TEACHES_CONCEPT' && e.source === clave)
      .map(e => nodoPorClave(resp, e.target)).filter(Boolean)
      .sort((a, b) => a.name_es.localeCompare(b.name_es, 'es'));
    return {
      requeridos: requeridos.map(k => nodoPorClave(resp, k)).filter(Boolean),
      previos: [...porCurso.values()],
      ensenados: listaEnsenados.length,
      listaEnsenados,
    };
  }

  /** Especializaciones (PC7): de qué es tipo y qué tipos tiene. */
  function especializaciones(resp, clave) {
    const sp = resp.edges.filter(e => e.type === 'SPECIALIZES');
    return {
      generales: sp.filter(e => e.source === clave).map(e => nodoPorClave(resp, e.target)).filter(Boolean),
      tipos: sp.filter(e => e.target === clave).map(e => nodoPorClave(resp, e.source)).filter(Boolean),
      todas: sp,
    };
  }

  /** Partes de un elemento (bajando por PART_OF) dentro de la respuesta de location. */
  function descendientes(resp, clave) {
    const hijos = new Map();
    for (const e of resp.edges) {
      if (e.type !== 'PART_OF') continue;
      if (!hijos.has(e.target)) hijos.set(e.target, []);
      hijos.get(e.target).push(e.source);
    }
    const vistos = new Set();
    const cola = [clave];
    while (cola.length) {
      const k = cola.shift();
      for (const h of hijos.get(k) || []) if (!vistos.has(h) && h !== clave) { vistos.add(h); cola.push(h); }
    }
    return [...vistos].map(k => nodoPorClave(resp, k)).filter(Boolean);
  }

  /**
   * En qué orden aprender los conceptos de un elemento: pasos según los prerrequisitos
   * entre ellos (paso 1 = no necesita nada de dentro). Solo reordena lo que trajo la API.
   */
  function ordenDeAprendizaje(resp, clave) {
    const conceptos = descendientes(resp, clave).filter(n => n.label === 'Concept');
    const dentro = new Set(conceptos.map(n => n.key));
    const requiere = new Map(conceptos.map(n => [n.key, []]));
    const relacionados = new Set();
    for (const e of resp.edges) {
      if (e.type === 'HAS_PREREQUISITE' && dentro.has(e.source) && dentro.has(e.target)) {
        requiere.get(e.source).push(e.target);
        relacionados.add(e.source); relacionados.add(e.target);
      }
    }
    const paso = new Map();
    function calcular(k, pila) {
      if (paso.has(k)) return paso.get(k);
      if (pila.has(k)) return 1;
      pila.add(k);
      const p = 1 + Math.max(0, ...requiere.get(k).map(r => calcular(r, pila)));
      pila.delete(k);
      paso.set(k, p);
      return p;
    }
    conceptos.forEach(n => calcular(n.key, new Set()));
    const total = Math.max(0, ...paso.values());
    const pasos = [];
    for (let i = 1; i <= total; i++) {
      pasos.push(conceptos.filter(n => paso.get(n.key) === i).sort((a, b) => a.name_es.localeCompare(b.name_es, 'es')));
    }
    return { conceptos, pasos, paso, relacionados };
  }

  raiz.IEKG_P1 = {
    CLASES, CAPAS, RELACIONES, LENTES, GRANOS, nombreClase, descendientes, ordenDeAprendizaje,
    api, apiPortada, busquedasCapturadas, normalizar, nodoPorClave, lenteAplica,
    procedenciaDe, documentoDeArista, conexiones, cadenasDeUbicacion, conteoPorClase,
    prerrequisitosPorProfundidad, recursosDe, resumenRuta, cursosPrevios, especializaciones,
  };
})(typeof window !== 'undefined' ? window : globalThis);
