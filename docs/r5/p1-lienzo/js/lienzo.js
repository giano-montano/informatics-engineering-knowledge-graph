/* Constelación (P1) · el lienzo del grafo, con D3 (d3-force + d3-hierarchy + d3-zoom).
 *
 * El lienzo guarda el subgrafo acumulado en pantalla (nodos y aristas por clave),
 * lo dibuja en SVG y lo dispone según la lente activa. No llama a la API: la app
 * le pasa las respuestas `{nodes, edges}` tal como llegan.
 */
(function (raiz) {
  'use strict';
  const P = raiz.IEKG_P1;

  const COLOR_ARISTA = {
    PART_OF: '#8b9bff', HAS_PREREQUISITE: '#e8ff6b', SPECIALIZES: '#ff9df0', TEACHES_CONCEPT: '#ffbe55',
    REQUIRES_CONCEPT: '#ff8a65', IS_ABOUT: '#ff7ab8', HAS_RESOURCE_TYPE: '#a9b0d6', WAS_DERIVED_FROM: '#ff7ab8',
  };
  const DISTANCIA = {
    PART_OF: 80, HAS_PREREQUISITE: 95, SPECIALIZES: 90, TEACHES_CONCEPT: 120, REQUIRES_CONCEPT: 120,
    IS_ABOUT: 110, HAS_RESOURCE_TYPE: 90, WAS_DERIVED_FROM: 160,
  };
  const RADIO = { KnowledgeArea: 22, KnowledgeUnit: 16, Topic: 15, Concept: 9.5, Course: 20, LearningResource: 13, ResourceType: 10 };

  // ------------------------------------------------------------------ formas (RF-22)

  function trazoCirculo(r) {
    return `M${r},0A${r},${r} 0 1 1 ${-r},0A${r},${r} 0 1 1 ${r},0Z`;
  }
  function trazoHexagono(r) {
    const p = [];
    for (let i = 0; i < 6; i++) {
      const a = Math.PI / 3 * i + Math.PI / 6;
      p.push((r * Math.cos(a)).toFixed(2) + ',' + (r * Math.sin(a)).toFixed(2));
    }
    return 'M' + p.join('L') + 'Z';
  }
  function trazoForma(n, r) { return n.layer === 'reference' ? trazoHexagono(r * 1.12) : trazoCirculo(r); }
  // Ícono de documento para los recursos (sílabos y CS2023).
  function trazoDocumento(r) {
    const w = r * 0.62, h = r * 0.8, f = r * 0.26;
    return `M${-w / 2},${-h / 2}H${w / 2 - f}L${w / 2},${-h / 2 + f}V${h / 2}H${-w / 2}Z` +
      `M${-w / 4},${-h / 8}H${w / 4}M${-w / 4},${h / 8}H${w / 4}M${-w / 4},${h * 0.32}H${w / 8}`;
  }

  function recortar(texto, max) {
    return texto.length > max ? texto.slice(0, max - 1).trimEnd() + '…' : texto;
  }

  // ------------------------------------------------------------------ disposiciones por lente

  /** Columnas: el elemento más lejano a la izquierda, el foco a la derecha (PC1). */
  function disponerPorProfundidad(resp, foco) {
    const obj = new Map();
    const conceptos = resp.nodes.filter(n => n.label === 'Concept' && n.depth !== undefined && n.depth !== null);
    const maxD = Math.max(0, ...conceptos.map(n => n.depth));
    const porD = d3.group(conceptos, n => n.depth);
    for (const [d, lista] of porD) {
      lista.sort((a, b) => a.name_es.localeCompare(b.name_es, 'es'));
      lista.forEach((n, i) => obj.set(n.key, { x: (maxD / 2 - d) * 250, y: (i - (lista.length - 1) / 2) * 74 }));
    }
    return { objetivos: obj, anillos: [], columnas: [...porD.keys()].sort().map(d => ({ x: (maxD / 2 - d) * 250, rotulo: d === 0 ? 'En foco' : (d === 1 ? 'Directo' : `A ${d} pasos`) })) };
  }

  /** Ruta elevada (PC6): conceptos abajo, estaciones del grano arriba, alineados por distancia. */
  function disponerRuta(resp, foco, grano) {
    const obj = new Map();
    const fila = {
      Concept: 150, Topic: grano === 'topic' ? -140 : 40, KnowledgeUnit: -60,
      Course: -140, KnowledgeArea: -160,
    };
    const conD = resp.nodes.filter(n => n.depth !== undefined && n.depth !== null && fila[n.label] !== undefined);
    const maxD = Math.max(0, ...conD.map(n => n.depth));
    const x = new Map();
    for (const n of conD) x.set(n.key, (maxD / 2 - n.depth) * 280);
    // Los intermedios sin distancia (tema y unidad del grano área) toman la x de sus vecinos.
    for (let vuelta = 0; vuelta < 4; vuelta++) {
      for (const n of resp.nodes) {
        if (x.has(n.key) || fila[n.label] === undefined) continue;
        const xs = resp.edges.filter(e => e.type !== 'WAS_DERIVED_FROM' && (e.source === n.key || e.target === n.key))
          .map(e => x.get(e.source === n.key ? e.target : e.source)).filter(v => v !== undefined);
        if (xs.length) x.set(n.key, d3.mean(xs));
      }
    }
    // Conceptos apilados en vertical; estaciones del grano repartidas en horizontal, para que no se pisen sus nombres.
    const grupos = d3.group(resp.nodes.filter(n => x.has(n.key)), n => fila[n.label] + '|' + Math.round(x.get(n.key)));
    for (const lista of grupos.values()) {
      lista.sort((a, b) => a.name_es.localeCompare(b.name_es, 'es'));
      lista.forEach((n, i) => {
        const off = i - (lista.length - 1) / 2;
        obj.set(n.key, n.label === 'Concept'
          ? { x: x.get(n.key), y: fila[n.label] + off * 62 }
          : { x: x.get(n.key) + off * 250, y: fila[n.label] + (lista.length > 1 ? (i % 2) * 46 : 0) });
      });
    }
    return { objetivos: obj, anillos: [], columnas: [] };
  }

  /** Dónde está en la carrera (PC3): la cadena tema › unidad › área sobre el foco. */
  function disponerCadena(resp, foco) {
    const obj = new Map([[foco, { x: 0, y: 60 }]]);
    const resaltar = new Set([foco]);
    const cadenas = P.cadenasDeUbicacion(resp, foco);
    cadenas.forEach((c, i) => {
      const x = (i - (cadenas.length - 1) / 2) * 300;
      c.forEach((n, j) => {
        if (!obj.has(n.key)) obj.set(n.key, { x, y: 60 - (c.length - j) * 125 });
        resaltar.add(n.key);
      });
    });
    return { objetivos: obj, anillos: [], columnas: [], resaltar };
  }

  /**
   * Qué contiene (PC4): las partes del foco. Un tema muestra sus conceptos en pasos
   * («en qué orden aprenderlo»); una unidad o un área, sus partes en anillos.
   */
  function disponerComposicion(resp, foco) {
    const obj = new Map();
    const partes = P.descendientes(resp, foco).filter(n => P.CLASES[n.label] && n.label !== 'LearningResource');
    const resaltar = new Set([foco].concat(partes.map(n => n.key)));
    const nodoFoco = P.nodoPorClave(resp, foco);
    if (nodoFoco && nodoFoco.label === 'Topic') {
      const orden = P.ordenDeAprendizaje(resp, foco);
      const n = orden.pasos.length;
      const sep = 250;
      const alto = Math.max(1, ...orden.pasos.map(l => l.length));
      const paso = alto > 8 ? 50 : 62;
      obj.set(foco, { x: -((n - 1) / 2 + 1) * sep, y: 0 });
      orden.pasos.forEach((lista, i) => {
        lista.forEach((c, j) => obj.set(c.key, { x: (i - (n - 1) / 2) * sep, y: (j - (lista.length - 1) / 2) * paso }));
      });
      const arriba = -((alto - 1) / 2) * paso - 50;
      const columnas = orden.pasos.map((l, i) => ({ x: (i - (n - 1) / 2) * sep, y: arriba, rotulo: `Paso ${i + 1}` }));
      return { objetivos: obj, anillos: [], columnas, resaltar };
    }
    const claves = new Set(resaltar);
    const padre = new Map();
    for (const e of resp.edges) {
      if (e.type === 'PART_OF' && claves.has(e.source) && claves.has(e.target) && e.source !== foco && !padre.has(e.source)) padre.set(e.source, e.target);
    }
    const datos = [{ key: foco, name_es: nodoFoco ? nodoFoco.name_es : '' }].concat(partes.filter(x => padre.has(x.key)));
    let arbol;
    try {
      arbol = d3.stratify().id(d => d.key).parentId(d => (d.key === foco ? null : padre.get(d.key)))(datos);
    } catch (err) {
      return { objetivos: new Map([[foco, { x: 0, y: 0 }]]), anillos: [], columnas: [], resaltar };
    }
    arbol.sort((a, b) => (b.height - a.height) || a.data.name_es.localeCompare(b.data.name_es, 'es'));
    const anillos = [];
    if (datos.length <= 8 || arbol.leaves().length <= 3) {
      d3.tree().nodeSize([190, 120])(arbol);
      arbol.each(d => obj.set(d.data.key, { x: d.x, y: d.y - arbol.height * 60 }));
    } else {
      const sep = datos.length > 40 ? 150 : 135;
      d3.tree().size([2 * Math.PI, arbol.height * sep]).separation((a, b) => (a.parent === b.parent ? 1 : 1.6) / Math.max(1, a.depth))(arbol);
      const radiales = datos.length > 24;
      arbol.each(d => {
        const theta = d.x - Math.PI / 2;
        obj.set(d.data.key, {
          x: d.y * Math.cos(theta), y: d.y * Math.sin(theta),
          theta: radiales && d.depth === arbol.height && d.height === 0 ? theta : undefined,
        });
      });
      const rotulos = nodoFoco && nodoFoco.label === 'KnowledgeArea' ? ['', 'Unidades', 'Temas', 'Conceptos'] : ['', 'Temas', 'Conceptos'];
      for (let i = 1; i <= arbol.height; i++) anillos.push({ r: i * sep, rotulo: rotulos[i] || '' });
    }
    return { objetivos: obj, anillos, columnas: [], resaltar };
  }

  /** Recursos (PC5): columnas de elementos, recursos y tipo de recurso. */
  function disponerRecursos(resp, foco) {
    const obj = new Map();
    const orden = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept', 'Course', 'LearningResource', 'ResourceType'];
    const visibles = resp.nodes.filter(n => n.label !== 'LearningResource' ||
      resp.edges.some(e => (e.type === 'IS_ABOUT' || e.type === 'HAS_RESOURCE_TYPE') && e.source === n.key));
    const porClase = d3.group(visibles, n => n.label);
    const presentes = orden.filter(c => porClase.has(c));
    presentes.forEach((c, i) => {
      const lista = porClase.get(c).sort((a, b) => a.name_es.localeCompare(b.name_es, 'es'));
      const paso = lista.length > 10 ? 40 : 64;
      lista.forEach((n, j) => obj.set(n.key, { x: (i - (presentes.length - 1) / 2) * 260, y: (j - (lista.length - 1) / 2) * paso }));
    });
    return { objetivos: obj, anillos: [], columnas: [] };
  }

  /** Especializaciones (PC7): lo general arriba, sus tipos abajo. */
  function disponerEspecializaciones(resp, foco) {
    const obj = new Map();
    const sp = resp.edges.filter(e => e.type === 'SPECIALIZES');
    const generales = [...new Set(sp.map(e => e.target))];
    const tipos = [...new Set(sp.map(e => e.source))].filter(k => !generales.includes(k));
    if (!sp.length) obj.set(foco, { x: 0, y: 0 });
    generales.forEach((k, i) => obj.set(k, { x: (i - (generales.length - 1) / 2) * 220, y: -110 }));
    tipos.forEach((k, i) => obj.set(k, { x: (i - (tipos.length - 1) / 2) * 210, y: 100 }));
    return { objetivos: obj, anillos: [], columnas: [] };
  }

  /** Cursos previos (PC2): cursos previos y conceptos requeridos a la izquierda; lo que enseña, en arco. */
  function disponerCursos(resp, foco) {
    const obj = new Map();
    obj.set(foco, { x: 0, y: 0 });
    const req = resp.edges.filter(e => e.type === 'REQUIRES_CONCEPT' && e.source === foco).map(e => e.target);
    const previos = [...new Set(resp.edges.filter(e => e.type === 'TEACHES_CONCEPT' && e.source !== foco && req.includes(e.target)).map(e => e.source))];
    req.forEach((k, i) => obj.set(k, { x: -330, y: (i - (req.length - 1) / 2) * 70 }));
    previos.forEach((k, i) => obj.set(k, { x: -620, y: (i - (previos.length - 1) / 2) * 110 }));
    const ensena = resp.edges.filter(e => e.type === 'TEACHES_CONCEPT' && e.source === foco && !req.includes(e.target))
      .map(e => P.nodoPorClave(resp, e.target)).filter(Boolean)
      .sort((a, b) => a.name_es.localeCompare(b.name_es, 'es'));
    const n = ensena.length;
    const arco = 1.45 * Math.PI;
    const R = Math.max(210, (n * 17) / arco);
    ensena.forEach((nodo, i) => {
      const theta = -arco / 2 + arco * (i + 0.5) / Math.max(1, n);
      obj.set(nodo.key, { x: R * Math.cos(theta), y: R * Math.sin(theta), theta: n > 14 ? theta : undefined });
    });
    const columnas = [];
    if (previos.length) columnas.push({ x: -620, y: -Math.max(1, previos.length) * 55 - 60, rotulo: 'Conviene llevar antes' });
    if (req.length) columnas.push({ x: -330, y: -Math.max(1, req.length) * 35 - 60, rotulo: 'Lo que pide' });
    return { objetivos: obj, anillos: n ? [{ r: R, rotulo: '', arco }] : [], columnas };
  }

  function disponer(lente, resp, foco, grano) {
    switch (lente) {
      case 'prerrequisitos': return disponerPorProfundidad(resp, foco);
      case 'ruta': return disponerRuta(resp, foco, grano);
      case 'ubicacion': return disponerCadena(resp, foco);
      case 'contiene': return disponerComposicion(resp, foco);
      case 'recursos': return disponerRecursos(resp, foco);
      case 'especializaciones': return disponerEspecializaciones(resp, foco);
      case 'cursos': return disponerCursos(resp, foco);
      default: return null;
    }
  }

  // ------------------------------------------------------------------ el lienzo

  function crearLienzo(contenedor, cb) {
    const nodos = new Map();
    const aristas = new Map();
    let foco = null;
    let resaltados = null;      // Set de claves o null (todo normal)
    let disposicion = null;     // {objetivos, anillos, columnas} o null (fuerzas libres)
    let verProcedencia = false;
    let portada = false;
    let seleccion = null;       // id de arista
    let saltos = new Map();
    const reducido = raiz.matchMedia && raiz.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const svg = d3.select(contenedor).append('svg')
      .attr('class', 'lienzo-svg')
      .attr('role', 'group')
      .attr('aria-label', 'Mapa de conceptos. Cada punto es un botón: Enter lo pone en foco y la tecla + muestra más conexiones.');

    const defs = svg.append('defs');
    const brillo = defs.append('filter').attr('id', 'brillo').attr('x', '-80%').attr('y', '-80%').attr('width', '260%').attr('height', '260%');
    brillo.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', 5).attr('result', 'b1');
    brillo.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', 1.6).attr('result', 'b2');
    const mezcla = brillo.append('feMerge');
    mezcla.append('feMergeNode').attr('in', 'b1');
    mezcla.append('feMergeNode').attr('in', 'b2');
    mezcla.append('feMergeNode').attr('in', 'SourceGraphic');
    const brilloLinea = defs.append('filter').attr('id', 'brillo-linea').attr('x', '-20%').attr('y', '-20%').attr('width', '140%').attr('height', '140%');
    brilloLinea.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', 2.2).attr('result', 'b');
    const m2 = brilloLinea.append('feMerge');
    m2.append('feMergeNode').attr('in', 'b');
    m2.append('feMergeNode').attr('in', 'SourceGraphic');
    for (const [clase, def] of Object.entries(P.CLASES)) {
      const g = defs.append('radialGradient').attr('id', 'g-' + clase).attr('cx', '35%').attr('cy', '32%').attr('r', '75%');
      g.append('stop').attr('offset', '0%').attr('stop-color', '#ffffff').attr('stop-opacity', 0.95);
      g.append('stop').attr('offset', '28%').attr('stop-color', def.color).attr('stop-opacity', 1);
      g.append('stop').attr('offset', '100%').attr('stop-color', def.color).attr('stop-opacity', 0.55);
    }
    for (const [tipo, color] of Object.entries(COLOR_ARISTA)) {
      defs.append('marker').attr('id', 'flecha-' + tipo).attr('viewBox', '0 -5 10 10').attr('refX', 9).attr('refY', 0)
        .attr('markerWidth', 7).attr('markerHeight', 7).attr('orient', 'auto')
        .append('path').attr('d', tipo === 'SPECIALIZES' ? 'M0,-4L9,0L0,4Z' : 'M0,-4L9,0L0,4L2.5,0Z')
        .attr('fill', tipo === 'SPECIALIZES' ? 'none' : color).attr('stroke', color).attr('stroke-width', tipo === 'SPECIALIZES' ? 1.4 : 0);
    }

    const raizG = svg.append('g').attr('class', 'mundo');
    const capaGuias = raizG.append('g').attr('class', 'guias');
    const capaAristas = raizG.append('g').attr('class', 'aristas');
    const capaToques = raizG.append('g').attr('class', 'toques');
    const capaNodos = raizG.append('g').attr('class', 'nodos');

    const zoom = d3.zoom().scaleExtent([0.15, 4]).on('zoom', ev => {
      raizG.attr('transform', ev.transform);
      svg.classed('lejos', ev.transform.k < 0.55).classed('cerca', ev.transform.k > 1.7);
      if (cb.alZoom) cb.alZoom(ev.transform.k);
    });
    svg.call(zoom).on('dblclick.zoom', null);
    svg.on('click', ev => { if (ev.target === svg.node() && cb.alClicVacio) cb.alClicVacio(); });

    const sim = d3.forceSimulation().alphaDecay(0.03).velocityDecay(0.38).on('tick', tic);
    sim.stop();

    // ---------------------------------------------------------------- modelo

    function idArista(e) { return e.type + '|' + e.source + '|' + e.target; }

    function incorporar(resp, origen) {
      const ancla = origen ? nodos.get(origen) : null;
      for (const n of resp.nodes) {
        const previo = nodos.get(n.key);
        if (previo) {
          for (const [k, v] of Object.entries(n)) if (v !== undefined && k !== 'depth' && k !== 'score') previo[k] = v;
        } else {
          const base = ancla || nodos.get(foco) || { x: 0, y: 0 };
          const a = Math.random() * Math.PI * 2;
          nodos.set(n.key, Object.assign({}, n, { x: (base.x || 0) + Math.cos(a) * 40, y: (base.y || 0) + Math.sin(a) * 40 }));
        }
      }
      for (const e of resp.edges) {
        const id = idArista(e);
        if (!aristas.has(id)) aristas.set(id, Object.assign({ id }, e));
      }
    }

    /** Reemplaza el contenido por una respuesta, conservando la posición de lo que sigue en pantalla. */
    function establecer(resp, claveFoco) {
      const posiciones = new Map([...nodos.values()].map(n => [n.key, { x: n.x, y: n.y }]));
      const anteriorFoco = foco;
      nodos.clear();
      aristas.clear();
      foco = claveFoco;
      portada = false;
      seleccion = null;
      incorporar(resp, null);
      // Lo nuevo nace en espiral alrededor del foco (ángulo áureo): se reparte parejo desde el primer cuadro.
      const ref = posiciones.get(claveFoco) || posiciones.get(anteriorFoco) || { x: 0, y: 0 };
      let i = 0;
      for (const n of nodos.values()) {
        const p = posiciones.get(n.key);
        if (p) { n.x = p.x; n.y = p.y; continue; }
        if (n.key === claveFoco) { n.x = ref.x; n.y = ref.y; continue; }
        const a = i * 2.39996, r = 90 + 9 * Math.sqrt(i);
        n.x = ref.x + Math.cos(a) * r; n.y = ref.y + Math.sin(a) * r;
        i++;
      }
    }

    function agregar(resp, origen) { incorporar(resp, origen); }

    function marcarExpandido(clave) { const n = nodos.get(clave); if (n) n.expandido = true; }

    function mostrarPortada(lista) {
      nodos.clear(); aristas.clear(); foco = null; portada = true; seleccion = null;
      const obj = new Map();
      const areas = lista.filter(n => n.label === 'KnowledgeArea');
      const cursos = lista.filter(n => n.label === 'Course');
      areas.forEach((n, i) => {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / areas.length;
        obj.set(n.key, { x: Math.cos(a) * 520, y: Math.sin(a) * 330 });
      });
      cursos.forEach((n, i) => {
        obj.set(n.key, { x: (i % 2 ? 1 : -1) * 150, y: (i < 2 ? -1 : 1) * 85 });
      });
      for (const n of lista) nodos.set(n.key, Object.assign({}, n, { x: obj.get(n.key).x * 0.2, y: obj.get(n.key).y * 0.2 }));
      resaltados = null;
      disposicion = { objetivos: obj, anillos: [], columnas: [] };
    }

    // ---------------------------------------------------------------- visibilidad

    function nodosVisibles() {
      const conRelacion = new Set();
      for (const e of aristas.values()) {
        if (e.type === 'WAS_DERIVED_FROM') continue;
        conRelacion.add(e.source); conRelacion.add(e.target);
      }
      return [...nodos.values()].filter(n => n.label !== 'LearningResource' || portada || n.key === foco ||
        verProcedencia || conRelacion.has(n.key));
    }

    function aristasVisibles(visibles) {
      const claves = new Set(visibles.map(n => n.key));
      return [...aristas.values()].filter(e => claves.has(e.source) && claves.has(e.target) &&
        (e.type !== 'WAS_DERIVED_FROM' || verProcedencia));
    }

    /** Vecindario: árbol radial por recorrido en anchura desde el foco; un anillo por distancia. */
    function disponerVecindario(visibles, lineas) {
      const claves = new Set(visibles.map(n => n.key));
      if (!foco || !claves.has(foco)) return null;
      const ORDEN = ['PART_OF', 'HAS_PREREQUISITE', 'SPECIALIZES', 'REQUIRES_CONCEPT', 'TEACHES_CONCEPT', 'IS_ABOUT', 'HAS_RESOURCE_TYPE'];
      const ady = new Map(visibles.map(n => [n.key, []]));
      for (const e of lineas) {
        if (e.type === 'WAS_DERIVED_FROM') continue;
        ady.get(e.source).push({ k: e.target, t: e.type, s: 0 });
        ady.get(e.target).push({ k: e.source, t: e.type, s: 1 });
      }
      const nombre = k => (nodos.get(k) || {}).name_es || '';
      const padre = new Map([[foco, null]]);
      const cola = [foco];
      while (cola.length) {
        const k = cola.shift();
        const vecinos = ady.get(k).slice().sort((a, b) =>
          (ORDEN.indexOf(a.t) * 2 + a.s) - (ORDEN.indexOf(b.t) * 2 + b.s) || nombre(a.k).localeCompare(nombre(b.k), 'es'));
        for (const v of vecinos) if (!padre.has(v.k)) { padre.set(v.k, k); cola.push(v.k); }
      }
      const datos = [...padre.keys()].map(k => ({ key: k }));
      const arbol = d3.stratify().id(d => d.key).parentId(d => padre.get(d.key))(datos);
      d3.tree().size([2 * Math.PI, 1]).separation((a, b) => (a.parent === b.parent ? 1 : 1.5) / a.depth)(arbol);
      const n1 = arbol.children ? arbol.children.length : 0;
      const r1 = Math.max(170, (n1 * 52) / (2 * Math.PI));
      const radioDe = p => (p === 0 ? 0 : r1 + (p - 1) * 175);
      const obj = new Map();
      arbol.each(d => {
        const th = d.x - Math.PI / 2;
        const r = radioDe(d.depth);
        const radial = (d.height === 0 && d.depth >= 2 && datos.length > 22) || (d.depth === 1 && n1 > 12);
        obj.set(d.data.key, { x: r * Math.cos(th), y: r * Math.sin(th), theta: radial ? th : undefined });
      });
      const anillos = d3.range(1, arbol.height + 1).map(p => ({ r: radioDe(p), rotulo: '' }));
      return { objetivos: obj, anillos, columnas: [] };
    }
    let vecindario = null;
    function objetivosActuales() {
      if (disposicion) return disposicion.objetivos;
      return vecindario ? vecindario.objetivos : null;
    }

    function calcularSaltos(visibles, lineas) {
      const ady = new Map(visibles.map(n => [n.key, []]));
      for (const e of lineas) {
        if (e.type === 'WAS_DERIVED_FROM') continue;
        ady.get(e.source).push(e.target); ady.get(e.target).push(e.source);
      }
      const dist = new Map();
      if (!foco || !ady.has(foco)) return dist;
      dist.set(foco, 0);
      const cola = [foco];
      while (cola.length) {
        const k = cola.shift();
        for (const v of ady.get(k)) if (!dist.has(v)) { dist.set(v, dist.get(k) + 1); cola.push(v); }
      }
      return dist;
    }

    function radio(n) {
      if (n.key === foco) return 30;
      if (portada) return n.label === 'KnowledgeArea' ? (n.concepts > 0 ? 26 : 19) : 22;
      const r = RADIO[n.label] || 10;
      if (disposicion && disposicion.objetivos.size > 60 && n.label === 'Concept') return 5.5;
      return r;
    }

    // ---------------------------------------------------------------- dibujo

    let selNodos = capaNodos.selectAll('g.nodo');
    let selAristas = capaAristas.selectAll('path.arista');
    let selToques = capaToques.selectAll('path.toque');

    function dibujar(opciones) {
      opciones = opciones || {};
      const visibles = nodosVisibles();
      const lineas = aristasVisibles(visibles);
      saltos = calcularSaltos(visibles, lineas);
      vecindario = (!disposicion && !portada) ? disponerVecindario(visibles, lineas) : null;
      const obj = objetivosActuales();
      const muchos = (resaltados ? resaltados.size : visibles.length) > 46;

      // Guías (anillos de la ubicación, arco de lo que enseña un curso, columnas de profundidad).
      const guias = disposicion ? disposicion.anillos : (vecindario ? vecindario.anillos : []);
      const selG = capaGuias.selectAll('g.anillo').data(guias, d => d.rotulo + d.r);
      selG.exit().remove();
      const gEnt = selG.enter().append('g').attr('class', 'anillo');
      gEnt.append('circle');
      gEnt.append('text');
      gEnt.merge(selG).select('circle').attr('r', d => d.r);
      gEnt.merge(selG).select('text').attr('x', 6).attr('y', d => -d.r - 6).text(d => d.rotulo);
      const cols = disposicion ? disposicion.columnas || [] : [];
      const selC = capaGuias.selectAll('text.columna').data(cols, d => d.rotulo);
      selC.exit().remove();
      selC.enter().append('text').attr('class', 'columna').merge(selC)
        .attr('x', d => d.x).attr('y', d => (d.y !== undefined ? d.y : -170)).attr('text-anchor', 'middle').text(d => d.rotulo);

      // Aristas.
      selAristas = selAristas.data(lineas, d => d.id);
      selAristas.exit().remove();
      selAristas = selAristas.enter().append('path')
        .attr('class', d => 'arista t-' + d.type)
        .attr('stroke', d => COLOR_ARISTA[d.type])
        .attr('marker-end', d => (d.type === 'HAS_PREREQUISITE' || d.type === 'SPECIALIZES') ? `url(#flecha-${d.type})` : null)
        .merge(selAristas);
      selAristas
        .classed('atenuada', d => !!resaltados && !(resaltados.has(d.source) && resaltados.has(d.target)))
        .classed('viva', d => d.type === 'HAS_PREREQUISITE' && !reducido && (!resaltados || (resaltados.has(d.source) && resaltados.has(d.target))))
        .classed('sel', d => d.id === seleccion);

      selToques = selToques.data(lineas, d => d.id);
      selToques.exit().remove();
      selToques = selToques.enter().append('path').attr('class', 'toque')
        .on('mouseenter', (ev, d) => { marcarIncidente(d, true); if (cb.alPasarArista) cb.alPasarArista(d, ev); })
        .on('mousemove', (ev, d) => { if (cb.alPasarArista) cb.alPasarArista(d, ev); })
        .on('mouseleave', (ev, d) => { marcarIncidente(d, false); if (cb.alPasarArista) cb.alPasarArista(null, ev); })
        .on('click', (ev, d) => { ev.stopPropagation(); if (cb.alClicArista) cb.alClicArista(d); })
        .merge(selToques);

      // Nodos.
      selNodos = selNodos.data(visibles, d => d.key);
      selNodos.exit().interrupt().remove();
      const ent = selNodos.enter().append('g')
        .attr('class', 'nodo')
        .attr('tabindex', 0)
        .attr('role', 'button')
        .attr('transform', d => `translate(${d.x},${d.y})`)
        .on('click', (ev, d) => { ev.stopPropagation(); if (cb.alClicNodo) cb.alClicNodo(d); })
        .on('mouseenter', (ev, d) => { iluminarVecinos(d.key, true); if (cb.alPasarNodo) cb.alPasarNodo(d, ev); })
        .on('mousemove', (ev, d) => { if (cb.alPasarNodo) cb.alPasarNodo(d, ev); })
        .on('mouseleave', (ev, d) => { iluminarVecinos(d.key, false); if (cb.alPasarNodo) cb.alPasarNodo(null, ev); })
        .on('keydown', (ev, d) => {
          if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); if (cb.alClicNodo) cb.alClicNodo(d); }
          if ((ev.key === '+' || ev.key === 'Add') && d.more_neighbors && cb.alExpandir) { ev.preventDefault(); cb.alExpandir(d); }
        })
        .call(d3.drag()
          .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.15).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
          .on('end', (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));
      ent.append('circle').attr('class', 'halo');
      ent.append('path').attr('class', 'forma');
      ent.append('path').attr('class', 'contorno');
      ent.append('path').attr('class', 'glifo');
      const exp = ent.append('g').attr('class', 'expandir')
        .on('click', (ev, d) => { ev.stopPropagation(); if (cb.alExpandir) cb.alExpandir(d); });
      exp.append('circle').attr('r', 7.5);
      exp.append('path').attr('d', 'M-3.5,0H3.5M0,-3.5V3.5');
      exp.append('title').text('Ver más: agrega sus conexiones al lienzo');
      ent.append('text').attr('class', 'etq');
      ent.append('text').attr('class', 'sub');
      selNodos = ent.merge(selNodos);

      selNodos
        .attr('class', d => {
          const c = ['nodo', 'c-' + d.label, 'capa-' + d.layer];
          if (d.key === foco) c.push('foco');
          const at = !!resaltados && !resaltados.has(d.key) && d.key !== foco;
          if (at) c.push('atenuado');
          if (!at && (d.key === foco || (!muchos && resaltados && resaltados.has(d.key)) || (portada && d.concepts > 0))) c.push('brilla');
          return c.join(' ');
        })
        .attr('aria-label', d => `${P.nombreClase(d)}: ${d.name_es}. Origen: ${P.CAPAS[d.layer].nombre} (${P.CAPAS[d.layer].forma}).` +
          (d.more_neighbors && !d.expandido ? ' Tiene más conexiones: tecla + para verlas.' : ''));

      selNodos.select('.halo').attr('r', d => radio(d) + 9);
      selNodos.select('.forma').attr('d', d => trazoForma(d, radio(d)))
        .attr('fill', d => d.layer === 'reference' ? hexRelleno(d) : `url(#g-${d.label})`)
        .attr('stroke', d => P.CLASES[d.label].color);
      selNodos.select('.contorno').attr('d', d => d.layer === 'reference' && radio(d) > 8 ? trazoHexagono(radio(d) * 0.7) : null)
        .attr('stroke', d => P.CLASES[d.label].color);
      selNodos.select('.glifo').attr('d', d => d.label === 'LearningResource' ? trazoDocumento(radio(d)) : null);
      selNodos.select('.expandir')
        .attr('transform', d => `translate(${radio(d) * 0.8 + 3},${-radio(d) * 0.8 - 3})`)
        .style('display', d => (!portada && d.more_neighbors && !d.expandido && d.key !== foco && !(resaltados && !resaltados.has(d.key))) ? null : 'none');

      selNodos.select('.etq')
        .attr('class', d => 'etq ' + claseEtiqueta(d, obj, muchos))
        .text(d => recortar(d.name_es + (d.course_code ? ' · ' + d.course_code : ''), d.key === foco ? 44 : 32))
        .each(function (d) {
          const o = obj && obj.get(d.key);
          const t = d3.select(this);
          if (o && o.theta !== undefined && d.key !== foco) {
            const grados = o.theta * 180 / Math.PI;
            const vuelta = Math.cos(o.theta) < 0;
            t.attr('transform', `rotate(${grados}) translate(${radio(d) + 5},0)${vuelta ? ' rotate(180)' : ''}`)
              .attr('text-anchor', vuelta ? 'end' : 'start').attr('dy', '0.32em').attr('y', 0);
          } else {
            t.attr('transform', null).attr('text-anchor', 'middle').attr('dy', null).attr('y', radio(d) + 15);
          }
        });
      selNodos.select('.sub')
        .text(d => d.sub || '')
        .attr('text-anchor', 'middle').attr('y', d => radio(d) + 29);

      configurarFuerzas(visibles, lineas);
      if (reducido || opciones.instantaneo) {
        sim.alpha(1);
        for (let i = 0; i < 260; i++) sim.tick();
        tic();
        sim.stop();
      } else {
        sim.alpha(0.9).restart();
      }
    }

    function hexRelleno(d) {
      const c = d3.color(P.CLASES[d.label].color);
      c.opacity = d.key === foco ? 0.3 : 0.14;
      return c.formatRgb();
    }

    function claseEtiqueta(d, obj, muchos) {
      if (d.key === foco) return 'etq-foco';
      if (resaltados && !resaltados.has(d.key)) return 'etq-oculta';
      if (portada) return '';
      if (obj && obj.get(d.key) && obj.get(d.key).theta !== undefined) return 'etq-radial';
      if (resaltados) return muchos && d.label === 'Concept' ? 'etq-menor' : '';
      const s = saltos.get(d.key);
      if (s === 1) return '';
      if (s === 2) return 'etq-menor';
      return 'etq-oculta';
    }

    function configurarFuerzas(visibles, lineas) {
      const obj = objetivosActuales();
      const enlaces = lineas.filter(e => e.type !== 'WAS_DERIVED_FROM' || verProcedencia)
        .map(e => ({ source: e.source, target: e.target, tipo: e.type }));
      let exterior = 520;
      if (obj && obj.size) {
        let m = 0;
        for (const o of obj.values()) m = Math.max(m, Math.hypot(o.x, o.y));
        exterior = m + 220;
      }
      sim.nodes(visibles);
      sim.force('enlace', d3.forceLink(enlaces).id(d => d.key)
        .distance(l => DISTANCIA[l.tipo] || 90)
        .strength(l => (obj ? 0.015 : ((l.source.key === foco || l.target.key === foco) ? 0.35 : 0.07))));
      sim.force('carga', d3.forceManyBody()
        .strength(d => (obj ? (obj.has(d.key) ? -12 : -50) : (d.key === foco ? -900 : -240)))
        .distanceMax(500));
      sim.force('choque', d3.forceCollide(d => radio(d) + (obj && obj.has(d.key) ? 2.5 : 12)));
      if (obj) {
        sim.force('x', d3.forceX(d => (obj.has(d.key) ? obj.get(d.key).x : 0)).strength(d => (obj.has(d.key) ? 0.55 : 0)));
        sim.force('y', d3.forceY(d => (obj.has(d.key) ? obj.get(d.key).y : 0)).strength(d => (obj.has(d.key) ? 0.55 : 0)));
        sim.force('radial', d3.forceRadial(exterior, 0, 0).strength(d => (obj.has(d.key) ? 0 : 0.1)));
      } else {
        sim.force('x', d3.forceX(0).strength(d => (d.key === foco ? 0.6 : 0.015)));
        sim.force('y', d3.forceY(0).strength(d => (d.key === foco ? 0.6 : 0.015)));
        sim.force('radial', d3.forceRadial(d => Math.min(saltos.has(d.key) ? saltos.get(d.key) : 3, 3) * 165, 0, 0)
          .strength(d => (d.key === foco ? 0 : 0.42)));
      }
    }

    function tic() {
      selNodos.attr('transform', d => `translate(${d.x},${d.y})`);
      const trazo = d => {
        // La arista HAS_PREREQUISITE se dibuja del prerrequisito al concepto que lo necesita.
        const invertir = d.type === 'HAS_PREREQUISITE';
        const a = nodos.get(invertir ? d.target : d.source);
        const b = nodos.get(invertir ? d.source : d.target);
        if (!a || !b) return null;
        const dx = b.x - a.x, dy = b.y - a.y;
        const L = Math.hypot(dx, dy) || 1;
        const ux = dx / L, uy = dy / L;
        const ra = radio(a) + 2, rb = radio(b) + (d.type === 'HAS_PREREQUISITE' || d.type === 'SPECIALIZES' ? (b.key === foco ? 12 : 5) : 2);
        if (L < ra + rb) return null;
        return `M${a.x + ux * ra},${a.y + uy * ra}L${b.x - ux * rb},${b.y - uy * rb}`;
      };
      selAristas.attr('d', trazo);
      selToques.attr('d', trazo);
    }

    function marcarIncidente(d, si) {
      selAristas.filter(a => a.id === d.id).classed('encima', si);
    }

    function iluminarVecinos(clave, si) {
      selAristas.classed('incidente', a => si && (a.source === clave || a.target === clave));
    }

    // ---------------------------------------------------------------- cámara

    function encuadrar(claves, ms) {
      const rect = svg.node().getBoundingClientRect();
      if (!rect.width) return;
      const obj = objetivosActuales();
      const puntos = [];
      const lista = claves ? claves.map(k => nodos.get(k)).filter(Boolean) : nodosVisibles();
      for (const n of lista) {
        const o = obj && obj.get(n.key);
        puntos.push(o ? [o.x, o.y] : [n.x, n.y]);
      }
      if (!puntos.length) return;
      const xs = puntos.map(p => p[0]), ys = puntos.map(p => p[1]);
      const margen = 110;
      const x0 = Math.min(...xs) - margen, x1 = Math.max(...xs) + margen;
      const y0 = Math.min(...ys) - margen, y1 = Math.max(...ys) + margen;
      const arriba = portada ? 60 : 150, abajo = 80;
      const alto = rect.height - arriba - abajo;
      const k = Math.max(0.2, Math.min(1.25, Math.min(rect.width / (x1 - x0), alto / (y1 - y0))));
      const t = d3.zoomIdentity.translate(rect.width / 2, arriba + alto / 2).scale(k).translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
      svg.transition().duration(reducido ? 0 : (ms === undefined ? 800 : ms)).call(zoom.transform, t);
    }

    function zoomPor(f) { svg.transition().duration(reducido ? 0 : 250).call(zoom.scaleBy, f); }

    // ---------------------------------------------------------------- interfaz pública

    return {
      establecer, agregar, marcarExpandido, mostrarPortada, dibujar, encuadrar, zoomPor,
      configurar(o) {
        if ('resaltados' in o) resaltados = o.resaltados;
        if ('disposicion' in o) disposicion = o.disposicion;
        if ('verProcedencia' in o) verProcedencia = o.verProcedencia;
        if ('seleccion' in o) seleccion = o.seleccion;
      },
      seleccionar(id) {
        seleccion = id;
        selAristas.classed('sel', d => d.id === seleccion);
      },
      contenido() { return { nodes: [...nodos.values()], edges: [...aristas.values()] }; },
      nodo(clave) { return nodos.get(clave) || null; },
      /** Claves a lo sumo a `max` saltos del foco (para encuadrar el vecindario cercano). */
      cercanas(max) { return [...saltos.entries()].filter(([, s]) => s <= max).map(([k]) => k); },
      arista(id) { return aristas.get(id) || null; },
      get foco() { return foco; },
    };
  }

  raiz.IEKG_LIENZO = { crearLienzo, disponer, COLOR_ARISTA };
})(typeof window !== 'undefined' ? window : globalThis);
