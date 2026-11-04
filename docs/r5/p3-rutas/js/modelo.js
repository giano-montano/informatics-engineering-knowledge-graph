/* Modelo de presentación de P3 · Itinerario.
 *
 * Convierte respuestas {nodes, edges} de la API en un "mapa de metro":
 *   estaciones = conceptos de la ruta; líneas = temas, cursos o áreas del grano;
 *   tramos = aristas HAS_PREREQUISITE (o REQUIRES_CONCEPT en la ruta entre cursos).
 * No calcula navegación: solo reordena lo que la API ya devolvió. La única cuenta
 * propia es la columna de cada estación (de depth) y, en el orden interno (PC4),
 * la capa por camino más largo, que es disposición gráfica.
 * Funciones puras: se prueban en node sin DOM.
 */
(function (root) {
  'use strict';

  const ETIQUETA = {
    KnowledgeArea: 'Área', KnowledgeUnit: 'Unidad', Topic: 'Tema', Concept: 'Concepto',
    Course: 'Curso', LearningResource: 'Sílabo', ResourceType: 'Tipo de material'
  };
  const GRANO = {
    topic: { label: 'Topic', nombre: 'Tema', plural: 'temas' },
    course: { label: 'Course', nombre: 'Curso', plural: 'cursos' },
    area: { label: 'KnowledgeArea', nombre: 'Área', plural: 'áreas' }
  };
  const VERBO = {
    HAS_PREREQUISITE: 'requiere',
    PART_OF: 'es parte de',
    TEACHES_CONCEPT: 'enseña',
    REQUIRES_CONCEPT: 'pide',
    SPECIALIZES: 'es un tipo de',
    IS_ABOUT: 'trata sobre',
    HAS_RESOURCE_TYPE: 'es de tipo',
    WAS_DERIVED_FROM: 'se derivó de'
  };
  // Paleta de señalética: tonos saturados, distinguibles sobre blanco.
  const PALETA = ['#D7263D', '#0B5FBF', '#00875A', '#E87B00', '#7B3FA0', '#008C99', '#A0522D', '#C2186B', '#5A6B00', '#3D4DB7'];
  const COLOR_CURSO = { '1INF01': '#D7263D', 'INF144': '#0B5FBF', 'INF238': '#00875A', '1INF35': '#E87B00' };
  const CS2023_KEY = 'http://www.informatics-engineering-kms.org/ontology/informatic-engineering#CS2023';

  /* ---------- utilidades ---------- */

  function indice(resp) {
    const m = {};
    (resp.nodes || []).forEach(function (n) { m[n.key] = n; });
    return m;
  }
  function nombre(n) { return n ? (n.name_es || n.name_en || n.key) : '—'; }
  function porNombre(a, b) { return nombre(a).localeCompare(nombre(b), 'es'); }
  function hash(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    return Math.abs(h);
  }
  function codigoArea(key) { const p = String(key).split('#KA-'); return p.length > 1 ? p[1] : null; }
  function codigoUnidad(key) { const p = String(key).split('#KU-'); return p.length > 1 ? p[1] : null; }

  /** Recursos de los que se derivó un nodo (sus aristas WAS_DERIVED_FROM). RF-21. */
  function procedencia(resp, key) {
    const by = indice(resp);
    return resp.edges
      .filter(function (e) { return e.type === 'WAS_DERIVED_FROM' && e.source === key; })
      .map(function (e) { return by[e.target]; })
      .filter(Boolean);
  }

  /** Recurso que respalda una arista: su provenance, o CS2023 si es de referencia. RF-21. */
  function fuenteDeArista(resp, arista, cs2023) {
    const by = indice(resp);
    if (arista.provenance) return by[arista.provenance] || { key: arista.provenance, name_es: 'Sílabo', layer: 'institutional' };
    return by[CS2023_KEY] || cs2023 || null;
  }

  /** "INF144" para "Sílabo INF144"; "CS2023" para el currículo de referencia. */
  function codigoFuente(recurso) {
    if (!recurso) return '';
    if (recurso.layer === 'reference') return 'CS2023';
    const n = nombre(recurso);
    return n.indexOf('Sílabo ') === 0 ? n.slice(7) : n;
  }

  /** Camino de aristas PART_OF desde `desde` hasta `hasta` (BFS), o null. */
  function cadenaPartOf(resp, desde, hasta) {
    const sale = {};
    resp.edges.forEach(function (e) { if (e.type === 'PART_OF') (sale[e.source] = sale[e.source] || []).push(e); });
    const previo = {}; const cola = [desde]; const visto = {}; visto[desde] = true;
    while (cola.length) {
      const x = cola.shift();
      if (x === hasta) break;
      (sale[x] || []).forEach(function (e) {
        if (!visto[e.target]) { visto[e.target] = true; previo[e.target] = e; cola.push(e.target); }
      });
    }
    if (!visto[hasta] || desde === hasta) return null;
    const camino = []; let k = hasta;
    while (k !== desde) { const e = previo[k]; camino.unshift(e); k = e.source; }
    return camino;
  }

  /** Aristas que prueban que un concepto pertenece a una línea (tema, curso o área). */
  function pertenencia(resp, modo, concepto, linea) {
    if (modo === 'course') {
      return resp.edges.filter(function (e) {
        return e.type === 'TEACHES_CONCEPT' && e.source === linea && e.target === concepto;
      });
    }
    return cadenaPartOf(resp, concepto, linea) || [];
  }

  function asignarColores(lineas) {
    const usados = {};
    lineas.forEach(function (l) {
      let c = null;
      if (l.nodo.label === 'Course' && COLOR_CURSO[l.nodo.course_code] && !usados[COLOR_CURSO[l.nodo.course_code]]) {
        c = COLOR_CURSO[l.nodo.course_code];
      } else {
        let i = hash(l.key) % PALETA.length;
        for (let t = 0; t < PALETA.length && usados[PALETA[i]]; t++) i = (i + 1) % PALETA.length;
        c = PALETA[i];
      }
      usados[c] = true;
      l.color = c;
    });
  }

  function crearLineas(nodos) {
    let num = 0;
    const lineas = nodos.map(function (n) {
      let codigo; let insignia;
      if (n.label === 'Course') { codigo = n.course_code; insignia = n.course_code; }
      else if (n.label === 'KnowledgeArea') { codigo = codigoArea(n.key); insignia = codigo; }
      else { num += 1; codigo = String(num); insignia = String(num); }
      return {
        key: n.key, nodo: n, nombre: nombre(n), codigo: codigo, insignia: insignia,
        referencia: n.layer === 'reference', depth: n.depth, color: null, estaciones: []
      };
    });
    asignarColores(lineas);
    return lineas;
  }

  function interseccion(a, b) { return a.filter(function (x) { return b.indexOf(x) >= 0; }); }

  function pasosPorColumna(estaciones, titulo) {
    const cols = {};
    estaciones.forEach(function (s) { (cols[s.col] = cols[s.col] || []).push(s); });
    return Object.keys(cols).map(Number).sort(function (a, b) { return a - b; }).map(function (c) {
      return { col: c, titulo: titulo(c, cols[c]), estaciones: cols[c] };
    });
  }

  /* ---------- PC6: ruta elevada al grano ---------- */

  function rutaElevada(resp, objKey, grano) {
    const by = indice(resp);
    const obj = by[objKey];
    const conceptos = resp.nodes.filter(function (n) { return n.label === 'Concept' && n.depth !== undefined; });
    let max = 0;
    conceptos.forEach(function (n) { if (n.depth > max) max = n.depth; });
    const base = { tipo: 'pc6', modo: grano, grano: grano, objetivo: obj, resp: resp };
    if (max === 0) return Object.assign(base, { vacia: true, estaciones: [], tramos: [], lineas: [], pasos: [] });

    const grupos = resp.nodes
      .filter(function (n) { return n.label === GRANO[grano].label && n.depth !== undefined && n.key !== objKey; })
      .sort(function (a, b) { return (a.depth - b.depth) || porNombre(a, b); });
    const lineas = crearLineas(grupos);
    const lineaPorKey = {}; lineas.forEach(function (l) { lineaPorKey[l.key] = l; });
    // Una línea puede contener a la propia meta: el prerrequisito está en el mismo tema
    // (o curso, o área). Es correcto (PC6 sube cada prerrequisito a su grano); se marca.
    lineas.forEach(function (l) { l.contieneMeta = pertenencia(resp, grano, objKey, l.key).length > 0; });

    const estaciones = conceptos.map(function (n) {
      const suyas = lineas.filter(function (l) { return pertenencia(resp, grano, n.key, l.key).length > 0; }).map(function (l) { return l.key; });
      return {
        key: n.key, nombre: nombre(n), nodo: n, depth: n.depth, col: max - n.depth, lineas: suyas,
        destino: n.key === objKey, interior: n.depth === 0 && n.key !== objKey,
        fuente: procedencia(resp, n.key)[0] || null
      };
    });
    const porKey = {}; estaciones.forEach(function (s) { porKey[s.key] = s; });
    estaciones.forEach(function (s) { s.lineas.forEach(function (k) { lineaPorKey[k].estaciones.push(s.key); }); });

    const tramos = resp.edges
      .filter(function (e) { return e.type === 'HAS_PREREQUISITE' && porKey[e.source] && porKey[e.target]; })
      .map(function (e) {
        return {
          id: e.target + '>' + e.source, desde: e.target, hasta: e.source, arista: e,
          lineas: interseccion(porKey[e.target].lineas, porKey[e.source].lineas)
        };
      });

    const terminal = obj.label === 'Concept'
      ? { tipo: 'estacion', key: objKey, nodo: obj }
      : { tipo: 'anden', key: objKey, nodo: obj, col: max };

    const pasos = pasosPorColumna(estaciones, function (c) {
      const d = max - c;
      if (d === 0) return obj.label === 'Concept' ? 'Meta' : 'Dentro de la meta';
      return d === 1 ? 'Directo' : 'A ' + d + ' pasos';
    });

    return Object.assign(base, {
      vacia: false, maxDepth: max, estaciones: estaciones, tramos: tramos, lineas: lineas,
      terminal: terminal, pasos: pasos, unirColumna: false
    });
  }

  /* ---------- PC2: ruta entre cursos por conceptos requeridos ---------- */

  function rutaEntreCursos(resp, cursoKey) {
    const by = indice(resp);
    const curso = by[cursoKey];
    const requeridas = resp.edges.filter(function (e) { return e.type === 'REQUIRES_CONCEPT' && e.source === cursoKey; });
    const ensena = resp.edges
      .filter(function (e) { return e.type === 'TEACHES_CONCEPT' && e.source === cursoKey; })
      .map(function (e) { return by[e.target]; }).filter(Boolean).sort(porNombre);
    const base = { tipo: 'pc2', modo: 'course', grano: 'course', objetivo: curso, resp: resp, ensena: ensena, requeridas: requeridas };
    if (!requeridas.length) return Object.assign(base, { vacia: true, estaciones: [], tramos: [], lineas: [], pasos: [] });

    const otros = resp.nodes
      .filter(function (n) { return n.label === 'Course' && n.key !== cursoKey; })
      .sort(function (a, b) { return String(a.course_code).localeCompare(String(b.course_code)); });
    const lineas = crearLineas(otros);
    const lineaPorKey = {}; lineas.forEach(function (l) { lineaPorKey[l.key] = l; });

    const estaciones = requeridas.map(function (e) {
      const n = by[e.target];
      const suyas = resp.edges
        .filter(function (x) { return x.type === 'TEACHES_CONCEPT' && x.target === n.key && x.source !== cursoKey && lineaPorKey[x.source]; })
        .map(function (x) { return x.source; });
      suyas.forEach(function (k) { lineaPorKey[k].estaciones.push(n.key); });
      return { key: n.key, nombre: nombre(n), nodo: n, depth: 1, col: 0, lineas: suyas, destino: false, interior: false, fuente: procedencia(resp, n.key)[0] || null };
    });
    estaciones.push({
      key: cursoKey, nombre: nombre(curso), nodo: curso, depth: 0, col: 1, lineas: [], destino: true,
      esCurso: true, interior: false, fuente: procedencia(resp, cursoKey)[0] || null
    });
    const tramos = requeridas.map(function (e) {
      return { id: e.target + '>' + cursoKey, desde: e.target, hasta: cursoKey, arista: e, lineas: [] };
    });
    const pasos = [
      { col: 0, titulo: 'Lo que pide', estaciones: estaciones.slice(0, -1) },
      { col: 1, titulo: 'Meta', estaciones: [estaciones[estaciones.length - 1]] }
    ];
    return Object.assign(base, {
      vacia: false, maxDepth: 1, estaciones: estaciones, tramos: tramos, lineas: lineas,
      terminal: { tipo: 'estacion', key: cursoKey, nodo: curso }, pasos: pasos, unirColumna: true
    });
  }

  /* ---------- PC4: orden interno de un tema, unidad o área ---------- */

  function ordenInterno(resp, key) {
    const by = indice(resp);
    const obj = by[key];
    const hijos = {};
    resp.edges.forEach(function (e) { if (e.type === 'PART_OF') (hijos[e.target] = hijos[e.target] || []).push(e.source); });
    const desc = {}; const pila = [key];
    while (pila.length) {
      const x = pila.pop();
      (hijos[x] || []).forEach(function (h) { if (!desc[h]) { desc[h] = true; pila.push(h); } });
    }
    const conceptos = Object.keys(desc).map(function (k) { return by[k]; }).filter(function (n) { return n && n.label === 'Concept'; }).sort(porNombre);
    const temas = Object.keys(desc).map(function (k) { return by[k]; }).filter(function (n) { return n && n.label === 'Topic'; }).sort(porNombre);
    const unidades = Object.keys(desc).map(function (k) { return by[k]; }).filter(function (n) { return n && n.label === 'KnowledgeUnit'; }).sort(porNombre);
    const hp = resp.edges.filter(function (e) { return e.type === 'HAS_PREREQUISITE' && desc[e.source] && desc[e.target]; });
    const base = { tipo: 'pc4', modo: 'topic', grano: 'topic', objetivo: obj, resp: resp, temas: temas, unidades: unidades, conceptos: conceptos, arbol: arbolContenido(resp, key) };
    if (!hp.length) return Object.assign(base, { vacia: true, estaciones: [], tramos: [], lineas: [], pasos: [], sinOrden: conceptos });

    const implicados = {};
    hp.forEach(function (e) { implicados[e.source] = true; implicados[e.target] = true; });
    const capa = {};
    function calcular(k, enCurso) {
      if (capa[k] !== undefined) return capa[k];
      if (enCurso[k]) return 0; // defensa ante ciclos
      enCurso[k] = true;
      const previos = hp.filter(function (e) { return e.source === k; }).map(function (e) { return e.target; });
      const v = previos.length ? 1 + Math.max.apply(null, previos.map(function (p) { return calcular(p, enCurso); })) : 0;
      capa[k] = v;
      return v;
    }
    Object.keys(implicados).forEach(function (k) { calcular(k, {}); });

    let lineasNodos;
    if (obj.label === 'Topic') lineasNodos = [obj];
    else {
      const ts = {};
      resp.edges.forEach(function (e) {
        if (e.type === 'PART_OF' && implicados[e.source] && by[e.target] && by[e.target].label === 'Topic') ts[e.target] = true;
      });
      lineasNodos = Object.keys(ts).map(function (k) { return by[k]; }).sort(porNombre);
    }
    const lineas = crearLineas(lineasNodos);
    const lineaPorKey = {}; lineas.forEach(function (l) { lineaPorKey[l.key] = l; });

    const estaciones = Object.keys(implicados).map(function (k) {
      const n = by[k];
      const suyas = lineas.filter(function (l) { return pertenencia(resp, 'topic', k, l.key).length > 0; }).map(function (l) { return l.key; });
      suyas.forEach(function (lk) { lineaPorKey[lk].estaciones.push(k); });
      return { key: k, nombre: nombre(n), nodo: n, depth: null, col: capa[k], lineas: suyas, destino: false, interior: false, fuente: procedencia(resp, k)[0] || null };
    });
    const porKey = {}; estaciones.forEach(function (s) { porKey[s.key] = s; });
    const tramos = hp.map(function (e) {
      return { id: e.target + '>' + e.source, desde: e.target, hasta: e.source, arista: e, lineas: interseccion(porKey[e.target].lineas, porKey[e.source].lineas) };
    });
    const pasos = pasosPorColumna(estaciones, function (c) { return c === 0 ? 'Primero' : 'Paso ' + (c + 1); });
    return Object.assign(base, {
      vacia: false, estaciones: estaciones, tramos: tramos, lineas: lineas, terminal: null, pasos: pasos,
      unirColumna: false, sinOrden: conceptos.filter(function (c) { return !implicados[c.key]; })
    });
  }

  /* ---------- CU-6: composición anidada (unidad › tema › conceptos) ---------- */

  /** Orden de aprendizaje dentro de un tema: pasos por camino más largo entre sus
   *  conceptos (solo los HAS_PREREQUISITE con ambos extremos en el tema). */
  function ordenDeTema(resp, conceptos) {
    const dentro = {}; conceptos.forEach(function (c) { dentro[c.key] = true; });
    const hp = resp.edges.filter(function (e) { return e.type === 'HAS_PREREQUISITE' && dentro[e.source] && dentro[e.target] && e.source !== e.target; });
    const implicados = {};
    hp.forEach(function (e) { implicados[e.source] = true; implicados[e.target] = true; });
    const capa = {};
    function calcular(k, enCurso) {
      if (capa[k] !== undefined) return capa[k];
      if (enCurso[k]) return 0;
      enCurso[k] = true;
      const previos = hp.filter(function (e) { return e.source === k; }).map(function (e) { return e.target; });
      capa[k] = previos.length ? 1 + Math.max.apply(null, previos.map(function (p) { return calcular(p, enCurso); })) : 0;
      return capa[k];
    }
    Object.keys(implicados).forEach(function (k) { calcular(k, {}); });
    const pasos = [];
    conceptos.forEach(function (c) {
      if (!implicados[c.key]) return;
      (pasos[capa[c.key]] = pasos[capa[c.key]] || []).push(c);
    });
    return {
      pasos: pasos.filter(Boolean).map(function (lista, i) { return { num: i + 1, conceptos: lista.sort(porNombre) }; }),
      sinOrden: conceptos.filter(function (c) { return !implicados[c.key]; }).sort(porNombre),
      tramos: hp.length
    };
  }

  /** Árbol de lo que contiene un tema, una unidad o un área, desde /api/elements/location.
   *  grupos: una unidad cada uno (o uno sin unidad si la meta es un tema); cada grupo
   *  lleva sus temas y cada tema sus conceptos en pasos. vacias: unidades sin temas. */
  function arbolContenido(resp, key) {
    const by = indice(resp);
    const obj = by[key];
    const hijos = {};
    resp.edges.forEach(function (e) {
      if (e.type !== 'PART_OF' || e.source === e.target || !by[e.source]) return;
      const l = (hijos[e.target] = hijos[e.target] || []);
      if (l.indexOf(e.source) < 0) l.push(e.source);
    });
    function de(k, label) { return (hijos[k] || []).map(function (h) { return by[h]; }).filter(function (n) { return n.label === label; }).sort(porNombre); }
    function tema(t) {
      const cs = de(t.key, 'Concept');
      const o = ordenDeTema(resp, cs);
      return { nodo: t, conceptos: cs.length, pasos: o.pasos, sinOrden: o.sinOrden };
    }
    function unidad(u) { return { nodo: u, temas: de(u.key, 'Topic').map(tema) }; }
    let grupos;
    if (obj.label === 'Topic') grupos = [{ nodo: null, temas: [tema(obj)] }];
    else if (obj.label === 'KnowledgeUnit') grupos = [unidad(obj)];
    else grupos = de(key, 'KnowledgeUnit').map(unidad);
    const conTemas = grupos.filter(function (g) { return g.temas.length; });
    return {
      grupos: conTemas,
      vacias: grupos.filter(function (g) { return !g.temas.length; }).map(function (g) { return g.nodo; }),
      temas: conTemas.reduce(function (a, g) { return a + g.temas.length; }, 0)
    };
  }

  /** Relaciones de `key` dentro de una respuesta, vistas desde `key`; omite `excluir`
   *  (el elemento de la ficha) y WAS_DERIVED_FROM. CU-2, segundo nivel. */
  function relacionesDe(resp, key, excluir, cs2023) {
    const by = indice(resp);
    const out = [];
    resp.edges.forEach(function (e) {
      if (e.type === 'WAS_DERIVED_FROM') return;
      let dir = null; let otro = null;
      if (e.source === key) { dir = 'out'; otro = e.target; } else if (e.target === key) { dir = 'in'; otro = e.source; }
      if (!dir || otro === key || otro === excluir || !by[otro]) return;
      out.push({ id: e.type + ':' + dir, clave: e.type + ':' + dir + ':' + otro, nodo: by[otro], fuente: fuenteDeArista(resp, e, cs2023) });
    });
    return out;
  }

  /* ---------- evidencia ("¿Por qué?") ---------- */

  function itemDeArista(resp, e, cs2023) {
    const by = indice(resp);
    const s = by[e.source]; const t = by[e.target];
    const fuente = fuenteDeArista(resp, e, cs2023);
    return {
      id: e.type + '|' + e.source + '|' + e.target,
      tipo: e.type, verbo: VERBO[e.type] || e.type,
      desde: nombre(s), hasta: nombre(t), desdeKey: e.source, hastaKey: t ? t.key : e.target,
      desdeRef: s && s.layer === 'reference', hastaRef: t && t.layer === 'reference',
      fuente: fuente, codigoFuente: codigoFuente(fuente),
      cypher: '(:' + (s ? s.label : '?') + ')-[:' + e.type + ']->(:' + (t ? t.label : '?') + ')'
    };
  }

  function dedupe(items) {
    const visto = {};
    return items.filter(function (i) { if (visto[i.id]) return false; visto[i.id] = true; return true; });
  }

  function modoPertenencia(modelo) { return modelo.tipo === 'pc2' ? 'course' : modelo.modo; }

  function evidenciaTramo(modelo, tramo, cs2023) {
    const resp = modelo.resp;
    const porKey = {}; modelo.estaciones.forEach(function (s) { porKey[s.key] = s; });
    const items = [itemDeArista(resp, tramo.arista, cs2023)];
    const modo = modoPertenencia(modelo);
    const lineasA = tramo.lineas.length ? tramo.lineas : (porKey[tramo.desde].lineas.concat(porKey[tramo.hasta].lineas));
    [tramo.desde, tramo.hasta].forEach(function (k) {
      porKey[k].lineas.forEach(function (lk) {
        if (lineasA.indexOf(lk) < 0) return;
        pertenencia(resp, modo, k, lk).forEach(function (e) { items.push(itemDeArista(resp, e, cs2023)); });
      });
    });
    return dedupe(items);
  }

  function evidenciaLinea(modelo, linea, cs2023) {
    const resp = modelo.resp;
    const modo = modoPertenencia(modelo);
    let items = [];
    linea.estaciones.forEach(function (k) {
      pertenencia(resp, modo, k, linea.key).forEach(function (e) { items.push(itemDeArista(resp, e, cs2023)); });
    });
    return dedupe(items);
  }

  /* ---------- disposición (layout por capas) ---------- */

  const DISPO = { COLW: 260, ROWH: 128, IZQ: 120, ARRIBA: 150, DER: 150, ABAJO: 120 };

  function disponer(modelo) {
    const est = modelo.estaciones;
    const pos = {};
    if (!est.length) return { pos: pos, ancho: 400, alto: 200, columnas: [] };
    const cols = {};
    est.forEach(function (s) { (cols[s.col] = cols[s.col] || []).push(s); });
    const nCol = Math.max.apply(null, est.map(function (s) { return s.col; })) + 1;
    const previos = {};
    modelo.tramos.forEach(function (t) { (previos[t.hasta] = previos[t.hasta] || []).push(t.desde); });
    const ordenLinea = {}; modelo.lineas.forEach(function (l, i) { ordenLinea[l.key] = i; });
    function rango(s) { return s.lineas.length ? Math.min.apply(null, s.lineas.map(function (k) { return ordenLinea[k]; })) : 99; }

    for (let c = 0; c < nCol; c++) {
      const lista = (cols[c] || []).slice();
      const x = DISPO.IZQ + c * DISPO.COLW;
      lista.forEach(function (s) {
        const ps = (previos[s.key] || []).filter(function (p) { return pos[p]; });
        s._bary = ps.length ? ps.reduce(function (a, p) { return a + pos[p].y; }, 0) / ps.length : null;
      });
      lista.sort(function (a, b) {
        if (a._bary !== null && b._bary !== null && a._bary !== b._bary) return a._bary - b._bary;
        if (a._bary === null && b._bary !== null) return 1;
        if (b._bary === null && a._bary !== null) return -1;
        return (rango(a) - rango(b)) || a.nombre.localeCompare(b.nombre, 'es');
      });
      let prev = -Infinity;
      const yIniciales = lista.map(function (s, i) { return s._bary !== null ? s._bary : i * DISPO.ROWH; });
      // centra el bloque de la columna alrededor de la media de sus baricentros
      lista.forEach(function (s, i) {
        let y = yIniciales[i];
        if (y < prev + DISPO.ROWH) y = prev + DISPO.ROWH;
        pos[s.key] = { x: x, y: y };
        prev = y;
      });
      const conBary = lista.filter(function (s) { return s._bary !== null; });
      if (conBary.length && lista.length > 1) {
        const objetivo = conBary.reduce(function (a, s) { return a + s._bary; }, 0) / conBary.length;
        const media = lista.reduce(function (a, s) { return a + pos[s.key].y; }, 0) / lista.length;
        const d = objetivo - media;
        lista.forEach(function (s) { pos[s.key].y += d; });
      }
      lista.forEach(function (s) { delete s._bary; });
    }
    let minY = Infinity; let maxY = -Infinity;
    Object.keys(pos).forEach(function (k) { minY = Math.min(minY, pos[k].y); maxY = Math.max(maxY, pos[k].y); });
    Object.keys(pos).forEach(function (k) { pos[k].y += DISPO.ARRIBA - minY; });
    maxY += DISPO.ARRIBA - minY;

    const columnas = [];
    for (let c = 0; c < nCol; c++) {
      const p = (modelo.pasos || []).find(function (x) { return x.col === c; });
      columnas.push({ col: c, x: DISPO.IZQ + c * DISPO.COLW, titulo: p ? p.titulo : '' });
    }
    let anden = null;
    if (modelo.terminal && modelo.terminal.tipo === 'anden') {
      const dentro = est.filter(function (s) { return s.col === modelo.terminal.col; });
      const ys = dentro.map(function (s) { return pos[s.key].y; });
      const x = DISPO.IZQ + modelo.terminal.col * DISPO.COLW;
      anden = { x: x - 98, y: Math.min.apply(null, ys) - 64, ancho: 196, alto: (Math.max.apply(null, ys) - Math.min.apply(null, ys)) + 156 };
      maxY = Math.max(maxY, anden.y + anden.alto - 60);
    }
    return {
      pos: pos, columnas: columnas, anden: anden,
      ancho: DISPO.IZQ + (nCol - 1) * DISPO.COLW + DISPO.DER,
      alto: maxY + DISPO.ABAJO
    };
  }

  const exportado = {
    ETIQUETA: ETIQUETA, GRANO: GRANO, VERBO: VERBO, CS2023_KEY: CS2023_KEY, DISPO: DISPO, COLOR_CURSO: COLOR_CURSO,
    indice: indice, nombre: nombre, procedencia: procedencia, fuenteDeArista: fuenteDeArista,
    codigoFuente: codigoFuente, codigoArea: codigoArea, codigoUnidad: codigoUnidad, cadenaPartOf: cadenaPartOf,
    rutaElevada: rutaElevada, rutaEntreCursos: rutaEntreCursos, ordenInterno: ordenInterno,
    arbolContenido: arbolContenido, ordenDeTema: ordenDeTema, relacionesDe: relacionesDe,
    evidenciaTramo: evidenciaTramo, evidenciaLinea: evidenciaLinea, itemDeArista: itemDeArista,
    disponer: disponer
  };
  root.IEKG_MODELO = exportado;
  if (typeof module !== 'undefined' && module.exports) module.exports = exportado;
})(typeof window !== 'undefined' ? window : globalThis);
