/* Constelación (P1) · el lienzo del grafo, con D3 (d3-force + d3-zoom).
 *
 * El lienzo guarda el subgrafo acumulado (nodos y aristas por clave), lo dibuja en SVG
 * y lo dispone según la vista activa. No llama a la API: la app le pasa las respuestas
 * `{nodes, edges}` tal como llegan.
 *
 * Tres reglas sostienen la legibilidad:
 *   1. Cada vista dibuja solo lo que responde su pregunta: los nodos sin lugar en la
 *      disposición y las aristas ajenas a la pregunta no se pintan.
 *   2. Las etiquetas van en horizontal, partidas en dos líneas, y se colocan evitando
 *      encimarse (`colocarEtiquetas`).
 *   3. Lo que no cabe con nombre legible se resume (conteos, puntos sin etiqueta) y el
 *      detalle queda a un clic.
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
  const RADIO = { KnowledgeArea: 20, KnowledgeUnit: 14, Topic: 13, Concept: 9, Course: 18, LearningResource: 12, ResourceType: 9 };
  const RADIO_FOCO = 26;
  const INTERLINEA = 15;
  const PLURAL_CLASE = { KnowledgeArea: 'Áreas', KnowledgeUnit: 'Unidades', Topic: 'Temas', Concept: 'Conceptos', Course: 'Cursos', LearningResource: 'Sílabos', ResourceType: 'Tipo de recurso' };

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

  // ------------------------------------------------------------------ texto

  function recortar(texto, max) {
    return texto.length > max ? texto.slice(0, max - 1).trimEnd() + '…' : texto;
  }

  /** Parte un nombre en líneas de a lo sumo `ancho` caracteres; lo que sobra de la última se recorta. */
  function partir(texto, ancho, maxLineas) {
    const lineas = [''];
    for (const palabra of String(texto).split(/\s+/)) {
      const ultima = lineas[lineas.length - 1];
      if (!ultima) lineas[lineas.length - 1] = palabra;
      else if ((ultima + ' ' + palabra).length <= ancho) lineas[lineas.length - 1] = ultima + ' ' + palabra;
      else lineas.push(palabra);
    }
    if (lineas.length > maxLineas) {
      const r = lineas.slice(0, maxLineas);
      r[maxLineas - 1] = recortar(r[maxLineas - 1] + ' ' + lineas.slice(maxLineas).join(' '), ancho);
      return r;
    }
    return lineas.map(l => recortar(l, ancho + 4));
  }

  const nombreDe = n => n.name_es;
  const porNombre = (a, b) => a.name_es.localeCompare(b.name_es, 'es');

  // ------------------------------------------------------------------ disposiciones por vista
  //
  // Una disposición es {objetivos, anillos, rotulos, cajas, conectores, aristas, sub, sinEtiqueta, tenue, curva}:
  //   objetivos    Map clave → {x, y, etq, ancho, lineas}: dónde va cada nodo y hacia dónde su etiqueta.
  //   aristas      función: qué relaciones se dibujan en esta vista (las demás no responden la pregunta).
  //   rotulos      textos de guía (cabeceras de columna, notas, nombre de un grupo de líneas).
  //   cajas        recuadros que agrupan («lo que contiene», «lo que enseña»).
  //   conectores   líneas de guía que no son relaciones del grafo (foco → recuadro).
  //   sub          Map clave → texto secundario (p. ej. «10 conceptos»).
  //   sinEtiqueta  Set de claves que solo muestran su nombre al pasar el cursor.
  //   tenue        Set de claves dibujadas apagadas.

  function vacia() {
    return { objetivos: new Map(), anillos: [], rotulos: [], cajas: [], conectores: [], sub: new Map(), sinEtiqueta: new Set(), tenue: new Set() };
  }

  /** Qué necesitas antes: columnas por distancia, lo más lejano a la izquierda y el foco a la derecha. */
  function disponerPorProfundidad(resp, foco) {
    const d = vacia();
    const conceptos = resp.nodes.filter(n => n.label === 'Concept' && n.depth !== undefined && n.depth !== null);
    const maxD = Math.max(0, ...conceptos.map(n => n.depth));
    const porD = d3.group(conceptos, n => n.depth);
    const alto = Math.max(1, ...[...porD.values()].map(l => l.length));
    const sep = 270, paso = 72;
    for (const [prof, lista] of porD) {
      lista.sort(porNombre);
      const x = (maxD / 2 - prof) * sep;
      lista.forEach((n, i) => d.objetivos.set(n.key, { x, y: (i - (lista.length - 1) / 2) * paso, etq: ['abajo', 'arriba', 'der', 'izq'] }));
      if (prof > 0) {
        d.rotulos.push({ x, y: -((alto - 1) / 2) * paso - 46, texto: prof === 1 ? 'Justo antes' : `${prof} pasos antes`, clase: 'cabecera' });
      }
    }
    if (!d.objetivos.has(foco)) d.objetivos.set(foco, { x: 0, y: 0 });
    d.aristas = e => e.type === 'HAS_PREREQUISITE';
    return d;
  }

  /**
   * Camino hasta aquí: abajo, la cadena de conceptos que la meta necesita; arriba, los temas,
   * cursos o áreas donde esos conceptos se aprenden. Solo entra lo que justifica el camino.
   */
  function disponerRuta(resp, foco, grano) {
    const d = vacia();
    const previos = resp.nodes.filter(n => n.label === 'Concept' && n.depth >= 1).map(n => n.key);
    const utiles = new Set([foco].concat(previos));
    let frente = previos.slice();
    while (frente.length) {
      const sig = [];
      for (const k of frente) {
        for (const e of resp.edges) {
          let otro = null;
          if (e.type === 'PART_OF' && e.source === k) otro = e.target;
          else if (e.type === 'TEACHES_CONCEPT' && e.target === k) otro = e.source;
          if (otro && !utiles.has(otro)) { utiles.add(otro); sig.push(otro); }
        }
      }
      frente = sig;
    }
    const fila = { Concept: 105, Topic: grano === 'topic' ? -105 : 15, KnowledgeUnit: -75, Course: -105, KnowledgeArea: -165 };
    const nodos = resp.nodes.filter(n => utiles.has(n.key) && fila[n.label] !== undefined);
    const conD = nodos.filter(n => n.depth !== undefined && n.depth !== null);
    const maxD = Math.max(0, ...conD.map(n => n.depth));
    // Lo que tiene distancia va en columnas; las paradas a la misma distancia se abren en horizontal.
    const grupos = d3.group(conD, n => fila[n.label] + '|' + n.depth);
    for (const lista of grupos.values()) {
      lista.sort(porNombre);
      lista.forEach((n, i) => {
        const off = i - (lista.length - 1) / 2, base = (maxD / 2 - n.depth) * 300;
        d.objetivos.set(n.key, n.label === 'Concept'
          ? { x: base, y: fila[n.label] + off * 66, etq: ['abajo', 'der', 'izq'] }
          : { x: base + off * 290, y: fila[n.label], etq: ['arriba', 'der', 'izq'] });
      });
    }
    // Los intermedios sin distancia (unidad y tema, al ver por área) cuelgan de lo que los contiene:
    // cada parada queda como una columna, de arriba abajo.
    for (let vuelta = 0; vuelta < 4; vuelta++) {
      for (const n of nodos) {
        if (d.objetivos.has(n.key)) continue;
        const xs = resp.edges.filter(e => e.type === 'PART_OF' && e.source === n.key && d.objetivos.has(e.target))
          .map(e => d.objetivos.get(e.target).x);
        if (xs.length) d.objetivos.set(n.key, { x: d3.mean(xs), y: fila[n.label], etq: ['der', 'izq', 'arriba'], ancho: 24 });
      }
    }
    if (!d.objetivos.has(foco)) d.objetivos.set(foco, { x: 0, y: 0 });
    if (previos.length) {
      const xs = [...d.objetivos.values()].map(o => o.x);
      const izq = Math.min(...xs) - 150;
      const filas = new Set(nodos.filter(n => d.objetivos.has(n.key)).map(n => n.label));
      for (const clase of filas) {
        d.rotulos.push({ x: izq, y: fila[clase] + 4, texto: PLURAL_CLASE[clase], clase: 'cabecera', ancla: 'end' });
      }
    }
    d.aristas = e => {
      if (!d.objetivos.has(e.source) || !d.objetivos.has(e.target)) return false;
      if (e.type === 'HAS_PREREQUISITE') return true;
      // Lo que agrupa a la meta misma no es parte del camino: lo que se necesita antes es el concepto.
      if (e.type === 'PART_OF') return e.source !== foco;
      if (e.type === 'TEACHES_CONCEPT') return e.target !== foco;
      return false;
    };
    return d;
  }

  /** Dónde está en la carrera: la cadena área › unidad › tema › elemento, de arriba abajo. */
  function disponerCadena(resp, foco) {
    const d = vacia();
    const cadenas = P.cadenasDeUbicacion(resp, foco);
    const largo = Math.max(0, ...cadenas.map(c => c.length));
    d.objetivos.set(foco, { x: 0, y: (largo / 2) * 100, etq: ['der', 'abajo'] });
    cadenas.forEach((c, i) => {
      const x = (i - (cadenas.length - 1) / 2) * 340;
      c.forEach((n, j) => {
        if (!d.objetivos.has(n.key)) d.objetivos.set(n.key, { x, y: (largo / 2 - (c.length - j)) * 100, etq: ['der', 'izq'], ancho: 30 });
      });
    });
    const izq = Math.min(...[...d.objetivos.values()].map(o => o.x)) - 54;
    const vistos = new Set();
    for (const [k, o] of d.objetivos) {
      const n = P.nodoPorClave(resp, k);
      if (!n || vistos.has(o.y)) continue;
      vistos.add(o.y);
      d.rotulos.push({ x: izq, y: o.y + 4, texto: P.nombreClase(n), clase: 'cabecera', ancla: 'end' });
    }
    d.aristas = e => e.type === 'PART_OF' && d.objetivos.has(e.source) && d.objetivos.has(e.target);
    return d;
  }

  /**
   * Qué contiene. Un tema muestra sus conceptos en pasos («en qué orden aprenderlos»), dentro de
   * un recuadro. Una unidad o un área, un árbol de izquierda a derecha que llega hasta los temas;
   * los conceptos solo entran si son pocos.
   */
  function disponerComposicion(resp, foco) {
    const nodoFoco = P.nodoPorClave(resp, foco);
    const partes = P.descendientes(resp, foco).filter(n => P.CLASES[n.label] && n.label !== 'LearningResource');
    if (nodoFoco && nodoFoco.label === 'Topic') return disponerPasos(resp, foco, nodoFoco);
    return disponerArbol(resp, foco, nodoFoco, partes);
  }

  function disponerPasos(resp, foco, nodoFoco) {
    const d = vacia();
    const orden = P.ordenDeAprendizaje(resp, foco);
    const hayOrden = orden.relacionados.size > 0;
    const MAX = 8, sepSub = 190, sepPaso = 270, paso = 60;
    // Un paso con muchos conceptos se reparte en subcolumnas para no estirar la vista.
    let x = 0;
    const columnas = [];
    orden.pasos.forEach((lista, i) => {
      const sub = Math.max(1, Math.ceil(lista.length / MAX));
      const filas = Math.ceil(lista.length / sub);
      const x0 = x;
      lista.forEach((c, j) => {
        const col = Math.floor(j / filas), f = j % filas;
        const enCol = Math.min(filas, lista.length - col * filas);
        d.objetivos.set(c.key, { x: x0 + col * sepSub, y: (f - (enCol - 1) / 2) * paso, etq: ['abajo', 'der', 'izq', 'arriba'] });
      });
      columnas.push({ x: x0 + (sub - 1) * sepSub / 2, filas, rotulo: hayOrden ? `Paso ${i + 1}` : '' });
      x = x0 + (sub - 1) * sepSub + sepPaso;
    });
    const ancho = x - sepPaso;
    const alto = Math.max(1, ...columnas.map(c => c.filas));
    for (const o of d.objetivos.values()) o.x -= ancho / 2;
    const arriba = -((alto - 1) / 2) * paso - 52;
    const abajo = ((alto - 1) / 2) * paso + 58;
    for (const c of columnas) {
      if (c.rotulo) d.rotulos.push({ x: c.x - ancho / 2, y: arriba, texto: c.rotulo, clase: 'cabecera' });
    }
    const caja = { x0: -ancho / 2 - 115, y0: arriba - 34, x1: ancho / 2 + 115, y1: abajo };
    d.cajas.push(caja);
    d.rotulos.push({ x: caja.x0 + 14, y: caja.y0 - 10, texto: `Los ${orden.conceptos.length} conceptos de este tema` + (hayOrden ? '' : ' · sin orden entre sí'), clase: 'nota', ancla: 'start' });
    d.objetivos.set(foco, { x: caja.x0 - 110, y: 0, etq: ['abajo', 'arriba'] });
    d.conectores.push({ x0: caja.x0 - 110 + RADIO_FOCO + 8, y0: 0, x1: caja.x0, y1: 0 });
    d.aristas = e => e.type === 'HAS_PREREQUISITE' && d.objetivos.has(e.source) && d.objetivos.has(e.target);
    d.pasos = orden.paso;
    return d;
  }

  const MAX_CONCEPTOS_EN_ARBOL = 24;

  function disponerArbol(resp, foco, nodoFoco, partes) {
    const d = vacia();
    const porClave = new Map(partes.map(n => [n.key, n]));
    const dentro = new Set([foco].concat(partes.map(n => n.key)));
    const padre = new Map(), hijos = new Map();
    for (const e of resp.edges) {
      if (e.type !== 'PART_OF' || !dentro.has(e.source) || !dentro.has(e.target) || e.source === foco || padre.has(e.source)) continue;
      padre.set(e.source, e.target);
      if (!hijos.has(e.target)) hijos.set(e.target, []);
      hijos.get(e.target).push(e.source);
    }
    for (const e of resp.edges) {
      if (e.type === 'PART_OF' && e.target === foco && porClave.has(e.source) && !padre.has(e.source)) {
        padre.set(e.source, foco);
        if (!hijos.has(foco)) hijos.set(foco, []);
        hijos.get(foco).push(e.source);
      }
    }
    const conceptos = partes.filter(n => n.label === 'Concept');
    d.verConceptos = conceptos.length <= MAX_CONCEPTOS_EN_ARBOL;
    const conceptosBajo = k => {
      let total = 0;
      for (const h of hijos.get(k) || []) total += (porClave.get(h) || {}).label === 'Concept' ? 1 : conceptosBajo(h);
      return total;
    };
    const hijosDe = k => (hijos.get(k) || []).map(h => porClave.get(h)).filter(n => n && (n.label !== 'Concept' || d.verConceptos));
    // Las unidades de CS2023 que ningún sílabo trata todavía van al final; si son muchas, se resumen en una nota.
    const sinTemas = new Set(partes.filter(n => n.label === 'KnowledgeUnit' && !(hijos.get(n.key) || []).length).map(n => n.key));
    const resumir = sinTemas.size > 4;
    d.unidadesResumidas = resumir ? sinTemas.size : 0;
    const SEP = 250;
    let fila = 0, hondo = 0;
    const niveles = new Map();
    function poner(n, prof) {
      const hs = hijosDe(n.key).filter(h => !(resumir && sinTemas.has(h.key)))
        .sort((a, b) => (sinTemas.has(a.key) - sinTemas.has(b.key)) || porNombre(a, b));
      let y;
      if (!hs.length) { y = fila; fila += n.label === 'Concept' ? 28 : 34; }
      else { const ys = hs.map(h => poner(h, prof + 1)); y = (ys[0] + ys[ys.length - 1]) / 2; }
      hondo = Math.max(hondo, prof);
      if (prof > 0 && !niveles.has(prof)) niveles.set(prof, n.label);
      d.objetivos.set(n.key, {
        x: prof * SEP, y,
        etq: prof === 0 ? ['izq', 'arriba', 'abajo'] : ['der'],
        ancho: prof === 0 ? 22 : (hs.length ? 22 : 42), lineas: n.label === 'Concept' ? 1 : 2, subEnLinea: true,
      });
      if (n.label === 'Topic' && !d.verConceptos) d.sub.set(n.key, `${conceptosBajo(n.key)} conceptos`);
      if (sinTemas.has(n.key)) { d.tenue.add(n.key); d.sub.set(n.key, 'solo en CS2023'); }
      return y;
    }
    poner(nodoFoco || { key: foco, label: 'KnowledgeArea' }, 0);
    const medio = (fila - 34) / 2;
    for (const o of d.objetivos.values()) { o.y -= medio; o.x -= hondo * SEP / 2; }
    const arriba = -medio - 44;
    for (const [prof, clase] of niveles) {
      d.rotulos.push({ x: prof * SEP - hondo * SEP / 2 - 10, y: arriba, texto: PLURAL_CLASE[clase] + (clase === 'Topic' ? ' de los sílabos' : (clase === 'KnowledgeUnit' ? ' de CS2023' : '')), clase: 'cabecera', ancla: 'start' });
    }
    if (resumir) {
      d.rotulos.push({ x: SEP - hondo * SEP / 2 - 10, y: fila - medio + 6, texto: `+ ${sinTemas.size} unidades de CS2023 que ningún sílabo cargado trata todavía`, clase: 'nota', ancla: 'start' });
    }
    d.aristas = e => e.type === 'PART_OF' && d.objetivos.has(e.source) && d.objetivos.has(e.target);
    d.curva = true;
    return d;
  }

  /** Material de estudio: columnas por clase, del elemento hacia los sílabos que tratan sobre él. */
  function disponerRecursos(resp, foco) {
    const d = vacia();
    const orden = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept', 'Course', 'LearningResource', 'ResourceType'];
    const visibles = resp.nodes.filter(n => n.label !== 'LearningResource' ||
      resp.edges.some(e => (e.type === 'IS_ABOUT' || e.type === 'HAS_RESOURCE_TYPE') && e.source === n.key));
    const porClase = d3.group(visibles, n => n.label);
    const presentes = orden.filter(c => porClase.has(c));
    let alto = 1;
    presentes.forEach((c, i) => {
      const lista = porClase.get(c).sort(porNombre);
      const paso = lista.length > 9 ? 36 : 60;
      alto = Math.max(alto, (lista.length - 1) * paso);
      lista.forEach((n, j) => d.objetivos.set(n.key, {
        x: (i - (presentes.length - 1) / 2) * 290, y: (j - (lista.length - 1) / 2) * paso,
        etq: lista.length > 9 ? ['der'] : ['abajo', 'der'], ancho: 26, lineas: lista.length > 9 ? 1 : 2,
      }));
    });
    presentes.forEach((c, i) => {
      d.rotulos.push({ x: (i - (presentes.length - 1) / 2) * 290, y: -alto / 2 - 46, texto: PLURAL_CLASE[c], clase: 'cabecera' });
    });
    if (!d.objetivos.has(foco)) d.objetivos.set(foco, { x: 0, y: 0 });
    d.aristas = e => (e.type === 'IS_ABOUT' || e.type === 'PART_OF' || e.type === 'HAS_RESOURCE_TYPE') && d.objetivos.has(e.source) && d.objetivos.has(e.target);
    return d;
  }

  /** Tipos: el concepto más general arriba, sus tipos abajo. */
  function disponerEspecializaciones(resp, foco) {
    const d = vacia();
    const sp = resp.edges.filter(e => e.type === 'SPECIALIZES');
    const generales = [...new Set(sp.map(e => e.target))];
    const tipos = [...new Set(sp.map(e => e.source))].filter(k => !generales.includes(k));
    generales.forEach((k, i) => d.objetivos.set(k, { x: (i - (generales.length - 1) / 2) * 240, y: -100, etq: ['arriba', 'der'] }));
    tipos.forEach((k, i) => d.objetivos.set(k, { x: (i - (tipos.length - 1) / 2) * 200, y: 100, etq: ['abajo', 'der'] }));
    if (!d.objetivos.has(foco)) d.objetivos.set(foco, { x: 0, y: 0 });
    d.aristas = e => e.type === 'SPECIALIZES';
    return d;
  }

  /**
   * Cursos que conviene llevar antes, de izquierda a derecha: el curso previo, lo que este
   * curso pide, el curso y, en un recuadro, lo que enseña.
   */
  function disponerCursos(resp, foco) {
    const d = vacia();
    d.objetivos.set(foco, { x: 0, y: 0, etq: ['abajo', 'arriba'] });
    const req = resp.edges.filter(e => e.type === 'REQUIRES_CONCEPT' && e.source === foco).map(e => e.target);
    const previos = [...new Set(resp.edges.filter(e => e.type === 'TEACHES_CONCEPT' && e.source !== foco && req.includes(e.target)).map(e => e.source))];
    req.forEach((k, i) => d.objetivos.set(k, { x: -250, y: (i - (req.length - 1) / 2) * 70, etq: ['abajo', 'arriba'] }));
    previos.forEach((k, i) => d.objetivos.set(k, { x: -500, y: (i - (previos.length - 1) / 2) * 120, etq: ['abajo', 'arriba'] }));
    if (previos.length) d.rotulos.push({ x: -500, y: -Math.max(1, previos.length) * 60 - 20, texto: 'Conviene llevar antes', clase: 'cabecera' });
    if (req.length) d.rotulos.push({ x: -250, y: -Math.max(1, req.length) * 35 - 30, texto: 'Lo que pide', clase: 'cabecera' });

    const ensena = resp.edges.filter(e => e.type === 'TEACHES_CONCEPT' && e.source === foco && !req.includes(e.target))
      .map(e => P.nodoPorClave(resp, e.target)).filter(Boolean).sort(porNombre);
    const n = ensena.length;
    if (n) {
      let caja;
      if (n <= 12) {
        ensena.forEach((nodo, i) => d.objetivos.set(nodo.key, { x: 250, y: (i - (n - 1) / 2) * 32, etq: ['der'], ancho: 30, lineas: 1 }));
        caja = { x0: 215, y0: -((n - 1) / 2) * 32 - 30, x1: 500, y1: ((n - 1) / 2) * 32 + 30 };
      } else {
        // Muchos conceptos no caben con nombre: una rejilla de puntos, y la lista en el panel.
        const filas = 7, paso = 30, cols = Math.ceil(n / filas);
        ensena.forEach((nodo, i) => {
          const col = Math.floor(i / filas), f = i % filas;
          d.objetivos.set(nodo.key, { x: 250 + col * paso, y: (f - (filas - 1) / 2) * paso });
          d.sinEtiqueta.add(nodo.key);
        });
        caja = { x0: 222, y0: -((filas - 1) / 2) * paso - 30, x1: 250 + (cols - 1) * paso + 28, y1: ((filas - 1) / 2) * paso + 30 };
        d.rotulos.push({ x: caja.x0, y: caja.y1 + 22, texto: 'El nombre de cada punto, al pasar el cursor', clase: 'nota', ancla: 'start' });
      }
      d.cajas.push(caja);
      d.rotulos.push({ x: caja.x0, y: caja.y0 - 12, texto: `Lo que enseña · ${n} concepto${n === 1 ? '' : 's'}`, clase: 'cabecera', ancla: 'start' });
      d.conectores.push({ x0: RADIO_FOCO + 8, y0: 0, x1: caja.x0, y1: 0, color: COLOR_ARISTA.TEACHES_CONCEPT });
    }
    d.aristas = e => (e.type === 'REQUIRES_CONCEPT' && e.source === foco) ||
      (e.type === 'TEACHES_CONCEPT' && e.source !== foco && req.includes(e.target));
    return d;
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

  // ------------------------------------------------------------------ colocación de etiquetas

  function solape(a, b) {
    const w = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0);
    const h = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
    return w > 0 && h > 0 ? w * h : 0;
  }

  /** Caja de una etiqueta puesta hacia `lado` de un nodo en (x, y) de radio r. */
  function cajaEtiqueta(x, y, r, lado, ancho, alto) {
    switch (lado) {
      case 'arriba': return { x0: x - ancho / 2, y0: y - r - 7 - alto, x1: x + ancho / 2, y1: y - r - 5 };
      case 'der': return { x0: x + r + 6, y0: y - alto / 2, x1: x + r + 8 + ancho, y1: y + alto / 2 };
      case 'izq': return { x0: x - r - 8 - ancho, y0: y - alto / 2, x1: x - r - 6, y1: y + alto / 2 };
      default: return { x0: x - ancho / 2, y0: y + r + 4, x1: x + ancho / 2, y1: y + r + 6 + alto };
    }
  }

  // ------------------------------------------------------------------ el lienzo

  function crearLienzo(contenedor, cb) {
    const nodos = new Map();
    const aristas = new Map();
    let foco = null;
    let disposicion = null;     // disposición de la vista, o null: «lo que lo rodea»
    let actual = null;          // disposición en uso (la de la vista o la del vecindario), con los objetivos finales
    let verProcedencia = false;
    let portada = false;
    let seleccion = null;       // id de arista
    let saltos = new Map();
    let etiquetas = new Map();  // clave → {lado, lineas, sub, caja, oculta}
    let margen = { arriba: 150, abajo: 110 };
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
    const capaToques = raizG.append('g').attr('class', 'toques').style('stroke-width', '24px');
    const capaNodos = raizG.append('g').attr('class', 'nodos');
    const capaRotulos = raizG.append('g').attr('class', 'rotulos');

    const zoom = d3.zoom().scaleExtent([0.15, 4]).on('zoom', ev => {
      raizG.attr('transform', ev.transform);
      // Área de toque de las líneas: 24 px en pantalla, sea cual sea el zoom.
      capaToques.style('stroke-width', (24 / ev.transform.k) + 'px');
      svg.classed('cerca', ev.transform.k > 1.6);
      if (cb.alZoom) cb.alZoom(ev.transform.k);
    });
    svg.call(zoom).on('dblclick.zoom', null);
    svg.on('click', ev => { if (ev.target === svg.node() && cb.alClicVacio) cb.alClicVacio(); });

    const sim = d3.forceSimulation().alphaDecay(0.04).velocityDecay(0.42).on('tick', tic);
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

    /** Portada: las áreas en un óvalo y los cursos al centro. */
    function mostrarPortada(lista) {
      nodos.clear(); aristas.clear(); foco = null; portada = true; seleccion = null;
      const d = vacia();
      const areas = lista.filter(n => n.label === 'KnowledgeArea');
      const cursos = lista.filter(n => n.label === 'Course');
      areas.forEach((n, i) => {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / areas.length;
        const c = Math.cos(a), s = Math.sin(a);
        const etq = Math.abs(c) > 0.45 ? (c > 0 ? ['der', 'abajo', 'arriba'] : ['izq', 'abajo', 'arriba']) : (s < 0 ? ['arriba', 'der', 'izq'] : ['abajo', 'der', 'izq']);
        d.objetivos.set(n.key, { x: c * 400, y: s * 232, etq, ancho: 22 });
        if (!(n.concepts > 0)) d.tenue.add(n.key);
      });
      cursos.forEach((n, i) => {
        d.objetivos.set(n.key, { x: (i % 2 ? 1 : -1) * 120, y: (i < 2 ? -70 : 52), etq: ['abajo', 'arriba'], ancho: 22 });
      });
      for (const n of lista) {
        if (n.sub) d.sub.set(n.key, n.sub);
        nodos.set(n.key, Object.assign({}, n, { x: d.objetivos.get(n.key).x * 0.2, y: d.objetivos.get(n.key).y * 0.2 }));
      }
      if (cursos.length) d.rotulos.push({ x: 0, y: -116, texto: 'Cursos con sílabo cargado', clase: 'cabecera' });
      disposicion = d;
    }

    // ---------------------------------------------------------------- visibilidad

    function nodosVisibles() {
      if (portada) return [...nodos.values()];
      const esFuente = new Set();
      if (verProcedencia) for (const e of aristas.values()) if (e.type === 'WAS_DERIVED_FROM') esFuente.add(e.target);
      if (disposicion) {
        // En una vista solo se dibuja lo que tiene lugar en ella: nada flota sin explicación.
        const base = [...nodos.values()].filter(n => disposicion.objetivos.has(n.key) || n.key === foco);
        if (!verProcedencia) return base;
        const claves = new Set(base.map(n => n.key));
        const fuentes = new Set();
        for (const e of aristas.values()) if (e.type === 'WAS_DERIVED_FROM' && claves.has(e.source)) fuentes.add(e.target);
        return base.concat([...nodos.values()].filter(n => fuentes.has(n.key) && !claves.has(n.key)));
      }
      const conRelacion = new Set();
      for (const e of aristas.values()) {
        if (e.type === 'WAS_DERIVED_FROM') continue;
        conRelacion.add(e.source); conRelacion.add(e.target);
      }
      return [...nodos.values()].filter(n => n.label !== 'LearningResource' || n.key === foco || esFuente.has(n.key) || conRelacion.has(n.key));
    }

    function aristasVisibles(visibles) {
      const claves = new Set(visibles.map(n => n.key));
      return [...aristas.values()].filter(e => {
        if (!claves.has(e.source) || !claves.has(e.target)) return false;
        if (e.type === 'WAS_DERIVED_FROM') return verProcedencia;
        return !disposicion || !disposicion.aristas || disposicion.aristas(e);
      });
    }

    /**
     * Lo que lo rodea: los vecinos directos en dos alas, a izquierda y derecha del foco, con el
     * nombre en horizontal; cada tramo de un ala es un tipo de relación, con su rótulo. Lo que
     * está a dos saltos va arriba y abajo, pequeño y apagado.
     */
    function disponerVecindario(visibles, lineas) {
      const claves = new Set(visibles.map(n => n.key));
      if (!foco || !claves.has(foco)) return null;
      const d = vacia();
      const ORDEN = ['PART_OF', 'HAS_PREREQUISITE', 'SPECIALIZES', 'REQUIRES_CONCEPT', 'TEACHES_CONCEPT', 'IS_ABOUT', 'HAS_RESOURCE_TYPE'];
      const ady = new Map(visibles.map(n => [n.key, []]));
      for (const e of lineas) {
        if (e.type === 'WAS_DERIVED_FROM') continue;
        ady.get(e.source).push({ k: e.target, t: e.type, s: 0 });
        ady.get(e.target).push({ k: e.source, t: e.type, s: 1 });
      }
      const nombre = k => (nodos.get(k) || {}).name_es || '';
      const ordenar = k => ady.get(k).slice().sort((a, b) =>
        (ORDEN.indexOf(a.t) * 2 + a.s) - (ORDEN.indexOf(b.t) * 2 + b.s) || nombre(a.k).localeCompare(nombre(b.k), 'es'));
      const padre = new Map([[foco, null]]);
      const directos = [];
      for (const v of ordenar(foco)) if (!padre.has(v.k)) { padre.set(v.k, foco); directos.push(v); }
      const lejanos = [];
      const cola = directos.map(v => v.k);
      const rama = new Map(directos.map(v => [v.k, v.k]));   // de qué vecino directo cuelga cada nodo lejano
      while (cola.length) {
        const k = cola.shift();
        for (const v of ordenar(k)) {
          if (padre.has(v.k)) continue;
          padre.set(v.k, k); rama.set(v.k, rama.get(k)); lejanos.push(v.k); cola.push(v.k);
        }
      }

      // Tramos de relación. Uno con muchos elementos no cabe con nombre: va como racimo de puntos
      // con su rótulo y su cuenta; los nombres salen al pasar el cursor y están en la ficha.
      const LIMITE = 14, S = 46, PASO = 24;
      const tramos = [];
      for (const v of directos) {
        const u = tramos[tramos.length - 1];
        if (u && u.t === v.t && u.s === v.s) u.items.push(v.k); else tramos.push({ t: v.t, s: v.s, items: [v.k] });
      }
      const huecos = [];
      for (const t of tramos) {
        if (t.items.length > LIMITE) {
          const filas = Math.min(6, Math.ceil(Math.sqrt(t.items.length / 1.6)));
          huecos.push({ racimo: true, t: t.t, s: t.s, items: t.items, filas, alto: filas * PASO + 58 });
        } else {
          for (const k of t.items) huecos.push({ k, t: t.t, s: t.s, alto: S });
        }
      }
      // El corte entre las dos alas reparte la altura lo más parejo posible.
      const total = d3.sum(huecos, h => h.alto);
      let corte = 1, acumulado = 0, mejor = Infinity;
      huecos.forEach((h, i) => {
        acumulado += h.alto;
        if (i < huecos.length - 1 && Math.abs(acumulado - total / 2) < mejor) { mejor = Math.abs(acumulado - total / 2); corte = i + 1; }
      });
      const alaDer = huecos.slice(0, corte);
      // El ala izquierda se recorre de abajo arriba, para que los tramos sigan contiguos en el sentido del reloj.
      const alaIzq = huecos.slice(corte).reverse();
      const altoAla = Math.max(d3.sum(alaDer, h => h.alto), d3.sum(alaIzq, h => h.alto), S);
      const R = Math.max(220, (altoAla / 2) / 0.8);
      const enRacimo = new Set();
      d.racimos = 0;
      const ponerAla = (ala, lado) => {
        let y = -d3.sum(ala, h => h.alto) / 2;
        for (const h of ala) {
          const yc = y + h.alto / 2;
          y += h.alto;
          const x0 = Math.sqrt(Math.max(0, R * R - yc * yc));
          if (!h.racimo) {
            d.objetivos.set(h.k, { x: lado * x0, y: yc, etq: lado > 0 ? ['der', 'abajo', 'arriba'] : ['izq', 'abajo', 'arriba'] });
            h.x = lado * x0; h.y = yc;
            continue;
          }
          const cols = Math.ceil(h.items.length / h.filas);
          const arriba = yc - ((h.filas - 1) * PASO) / 2 + 10;
          h.items.forEach((k, i) => {
            d.objetivos.set(k, { x: lado * (x0 + Math.floor(i / h.filas) * PASO), y: arriba + (i % h.filas) * PASO });
            d.sinEtiqueta.add(k); enRacimo.add(k);
          });
          const xa = lado * (x0 - 16), xb = lado * (x0 + (cols - 1) * PASO + 16);
          const caja = { x0: Math.min(xa, xb), y0: arriba - 16, x1: Math.max(xa, xb), y1: arriba + (h.filas - 1) * PASO + 16 };
          d.cajas.push(caja);
          d.rotulos.push({ x: lado > 0 ? caja.x0 : caja.x1, y: caja.y0 - 9, texto: `${P.RELACIONES[h.t][h.s === 0 ? 'salida' : 'entrada']} · ${h.items.length}`, clase: 'relacion', color: COLOR_ARISTA[h.t], ancla: lado > 0 ? 'start' : 'end' });
          d.conectores.push({ x0: lado * (RADIO_FOCO + 8), y0: 0, x1: xa, y1: (caja.y0 + caja.y1) / 2, color: COLOR_ARISTA[h.t] });
          d.racimos++;
        }
      };
      ponerAla(alaDer, 1); ponerAla(alaIzq, -1);
      d.objetivos.set(foco, { x: 0, y: 0, etq: ['abajo', 'arriba'] });
      d.anillos.push({ r: R });
      // Las líneas del foco a cada punto de un racimo se resumen en una sola, hasta el recuadro.
      d.aristas = e => !((e.source === foco && enRacimo.has(e.target)) || (e.target === foco && enRacimo.has(e.source)));

      // Rótulo de cada tramo con nombre, a medio camino entre el foco y su grupo de vecinos.
      const puestos = [{ x0: -120, y0: 26, x1: 120, y1: 84 }, { x0: -34, y0: -34, x1: 34, y1: 34 }];
      const rotular = (ala) => {
        const lista = ala.filter(h => !h.racimo);
        let i = 0;
        while (i < lista.length) {
          let j = i;
          while (j + 1 < lista.length && lista[j + 1].t === lista[i].t && lista[j + 1].s === lista[i].s) j++;
          const grupo = lista.slice(i, j + 1);
          const mx = d3.mean(grupo, h => h.x), my = d3.mean(grupo, h => h.y);
          // Sin conteo: un tramo puede repartirse entre las dos alas, y el total ya está en la frase de arriba.
          const texto = P.RELACIONES[lista[i].t][lista[i].s === 0 ? 'salida' : 'entrada'];
          const ancho = texto.length * 6.4 + 12;
          let elegido = null, menor = Infinity;
          for (const f of [0.5, 0.62, 0.38, 0.72]) {
            const c = { x0: mx * f - ancho / 2, y0: my * f - 10, x1: mx * f + ancho / 2, y1: my * f + 10 };
            const sol = puestos.reduce((t, p) => t + solape(c, p), 0);
            if (sol < menor) { menor = sol; elegido = c; }
            if (!sol) break;
          }
          puestos.push(elegido);
          d.rotulos.push({ x: (elegido.x0 + elegido.x1) / 2, y: (elegido.y0 + elegido.y1) / 2 + 4, texto, clase: 'relacion', color: COLOR_ARISTA[lista[i].t], caja: elegido });
          i = j + 1;
        }
      };
      rotular(alaDer); rotular(alaIzq);

      // A dos saltos o más: rejillas arriba y abajo. Con nombre si son pocos o si se pidieron con «+».
      const alto = altoAla / 2 - S / 2;
      const conNombre = k => lejanos.length <= 12 || (nodos.get(padre.get(k)) || {}).expandido;
      const arriba = [], abajo = [];
      lejanos.forEach((k, i) => {
        const y = (d.objetivos.get(rama.get(k)) || { y: 0 }).y;
        (y < 0 || (y === 0 && i % 2 === 0) ? arriba : abajo).push(k);
      });
      const rejilla = (lista, signo) => {
        const nombrados = lista.filter(conNombre), mudos = lista.filter(k => !conNombre(k));
        let y = Math.max(alto, signo > 0 ? 70 : 40) + 92;
        const COLS = 5;
        nombrados.forEach((k, i) => {
          const f = Math.floor(i / COLS), enFila = Math.min(COLS, nombrados.length - f * COLS);
          d.objetivos.set(k, { x: ((i % COLS) - (enFila - 1) / 2) * 168, y: signo * (y + f * 62), etq: signo < 0 ? ['arriba', 'abajo'] : ['abajo', 'arriba'], ancho: 20 });
        });
        y += Math.ceil(nombrados.length / COLS) * 62;
        const MUDOS = 16;
        mudos.forEach((k, i) => {
          const f = Math.floor(i / MUDOS), enFila = Math.min(MUDOS, mudos.length - f * MUDOS);
          d.objetivos.set(k, { x: ((i % MUDOS) - (enFila - 1) / 2) * 26, y: signo * (y + f * 26) });
          d.sinEtiqueta.add(k);
        });
      };
      rejilla(arriba, -1); rejilla(abajo, 1);
      for (const k of lejanos) if (!(nodos.get(padre.get(k)) || {}).expandido) d.tenue.add(k);
      d.lejanos = lejanos.length;
      d.directos = directos.length;
      return d;
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
      if (n.key === foco) return RADIO_FOCO;
      if (portada) return n.label === 'KnowledgeArea' ? (n.concepts > 0 ? 22 : 13) : 19;
      const r = RADIO[n.label] || 9;
      if (actual && actual.sinEtiqueta.has(n.key)) return Math.min(r, 6);
      if (actual && actual.tenue.has(n.key)) return Math.max(6, r * 0.7);
      return r;
    }

    /** Las fuentes que se muestran con «Mostrar fuentes» y no tienen lugar propio van en una fila, debajo. */
    function ubicarSueltos(d, visibles) {
      const sueltos = visibles.filter(n => !d.objetivos.has(n.key)).sort(porNombre);
      if (!sueltos.length) return;
      let abajo = 0;
      for (const o of d.objetivos.values()) abajo = Math.max(abajo, o.y);
      for (const c of d.cajas) abajo = Math.max(abajo, c.y1);
      sueltos.forEach((n, i) => d.objetivos.set(n.key, { x: (i - (sueltos.length - 1) / 2) * 230, y: abajo + 130, etq: ['abajo'] }));
      d.rotulos.push({ x: 0, y: abajo + 84, texto: sueltos.length === 1 ? 'Fuente' : 'Fuentes', clase: 'cabecera' });
    }

    function colocarEtiquetas(visibles) {
      const res = new Map();
      if (!actual) return res;
      const obj = actual.objetivos;
      const cajas = [];
      const pos = n => obj.get(n.key) || { x: n.x, y: n.y };
      for (const n of visibles) {
        const p = pos(n), r = radio(n) + 2;
        cajas.push({ x0: p.x - r, y0: p.y - r, x1: p.x + r, y1: p.y + r, de: n.key });
      }
      for (const t of actual.rotulos) {
        if (t.caja) { cajas.push(t.caja); continue; }
        const w = t.texto.length * 6.6, x = t.ancla === 'start' ? t.x : (t.ancla === 'end' ? t.x - w : t.x - w / 2);
        cajas.push({ x0: x, y0: t.y - 13, x1: x + w, y1: t.y + 4 });
      }
      const orden = visibles.slice().sort((a, b) => (b.key === foco) - (a.key === foco) || radio(b) - radio(a));
      for (const n of orden) {
        const o = obj.get(n.key) || {};
        const esFoco = n.key === foco;
        const oculta = actual.sinEtiqueta.has(n.key);
        const lineas = partir(nombreDe(n), o.ancho || (esFoco ? 24 : 21), o.lineas || (esFoco ? 3 : 2));
        const sub = actual.sub.get(n.key) || n.course_code || '';
        const cuerpo = esFoco ? 15.5 : (portada ? 13.5 : 12.5);
        const p = pos(n), r = radio(n);
        if (oculta) { res.set(n.key, { lado: 'abajo', lineas, sub: '', oculta: true }); continue; }
        let mejor = null, menor = Infinity;
        for (const lado of (o.etq || ['abajo', 'der', 'izq', 'arriba'])) {
          const lateral = lado === 'der' || lado === 'izq';
          const largo = Math.max(...lineas.map(l => l.length));
          const enLinea = lateral && !!o.subEnLinea;
          const ancho = enLinea
            ? Math.max(largo * cuerpo * 0.56, (lineas[lineas.length - 1].length * cuerpo * 0.56) + (sub ? sub.length * 6 + 10 : 0))
            : Math.max(largo * cuerpo * (esFoco ? 0.6 : 0.56), sub.length * 6);
          const alto = (lineas.length + (sub && !enLinea ? 1 : 0)) * INTERLINEA + (esFoco ? 6 : 0);
          const caja = cajaEtiqueta(p.x, p.y, r, lado, ancho, alto);
          const s = cajas.reduce((t, c) => t + (c.de === n.key ? 0 : solape(caja, c)), 0);
          if (s < menor) { menor = s; mejor = { lado, lineas, sub, caja, enLinea }; }
          if (!s) break;
        }
        cajas.push(mejor.caja);
        res.set(n.key, mejor);
      }
      return res;
    }

    // ---------------------------------------------------------------- dibujo

    let selNodos = capaNodos.selectAll('g.nodo');
    let selAristas = capaAristas.selectAll('path.arista');
    let selToques = capaToques.selectAll('path.toque');

    function dibujar(opciones) {
      opciones = opciones || {};
      const visibles = nodosVisibles();
      let lineas = aristasVisibles(visibles);
      saltos = calcularSaltos(visibles, lineas);
      const base = disposicion || (portada ? null : disponerVecindario(visibles, lineas));
      if (!disposicion && base && base.aristas) lineas = lineas.filter(e => e.type === 'WAS_DERIVED_FROM' || base.aristas(e));
      // Copia de trabajo: las fuentes sueltas se le agregan sin tocar la disposición de la vista.
      actual = base ? Object.assign({}, base, { objetivos: new Map(base.objetivos), rotulos: base.rotulos.slice() }) : null;
      if (actual) ubicarSueltos(actual, visibles);
      etiquetas = colocarEtiquetas(visibles);
      const enVecindario = !disposicion && !portada;
      svg.classed('en-vecindario', enVecindario);

      // Guías: anillo, recuadros, conectores y rótulos.
      const guias = actual || vacia();
      const selA = capaGuias.selectAll('circle.anillo').data(guias.anillos);
      selA.exit().remove();
      selA.enter().append('circle').attr('class', 'anillo').merge(selA).attr('r', d => d.r);
      const selCaja = capaGuias.selectAll('rect.caja').data(guias.cajas);
      selCaja.exit().remove();
      selCaja.enter().append('rect').attr('class', 'caja').attr('rx', 18).merge(selCaja)
        .attr('x', d => d.x0).attr('y', d => d.y0).attr('width', d => d.x1 - d.x0).attr('height', d => d.y1 - d.y0);
      const selCon = capaGuias.selectAll('path.conector').data(guias.conectores);
      selCon.exit().remove();
      selCon.enter().append('path').attr('class', 'conector').merge(selCon)
        .attr('d', d => `M${d.x0},${d.y0}L${d.x1},${d.y1}`).style('stroke', d => d.color || null);
      const selR = capaRotulos.selectAll('text.rotulo').data(guias.rotulos);
      selR.exit().remove();
      selR.enter().append('text').merge(selR)
        .attr('class', d => 'rotulo rotulo-' + (d.clase || 'cabecera'))
        .attr('x', d => d.x).attr('y', d => d.y)
        .attr('text-anchor', d => d.ancla || 'middle')
        .style('fill', d => d.color || null)
        .text(d => d.texto);

      // Aristas.
      selAristas = selAristas.data(lineas, d => d.id);
      selAristas.exit().remove();
      selAristas = selAristas.enter().append('path')
        .attr('stroke', d => COLOR_ARISTA[d.type])
        .attr('marker-end', d => (d.type === 'HAS_PREREQUISITE' || d.type === 'SPECIALIZES') ? `url(#flecha-${d.type})` : null)
        .merge(selAristas);
      const tocaFoco = d => d.source === foco || d.target === foco;
      selAristas
        .attr('class', d => 'arista t-' + d.type)
        .classed('lejana', d => enVecindario && !tocaFoco(d))
        .classed('viva', d => d.type === 'HAS_PREREQUISITE' && !reducido && (!enVecindario || tocaFoco(d)))
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
      exp.append('title').text('Traer sus conexiones al mapa, sin cambiar de lugar');
      ent.append('text').attr('class', 'etq');
      selNodos = ent.merge(selNodos);

      const esTenue = d => !!actual && actual.tenue.has(d.key);
      const esMudo = d => !!actual && actual.sinEtiqueta.has(d.key);
      selNodos
        .attr('class', d => {
          const c = ['nodo', 'c-' + d.label, 'capa-' + d.layer];
          if (d.key === foco) c.push('foco');
          if (esTenue(d)) c.push('tenue');
          if (esMudo(d)) c.push('mudo');
          if (d.key === foco || (portada && d.concepts > 0) || (!portada && !esTenue(d) && !esMudo(d) && visibles.length <= 40)) c.push('brilla');
          return c.join(' ');
        })
        .attr('aria-label', d => `${P.nombreClase(d)}: ${d.name_es}. Origen: ${P.CAPAS[d.layer].nombre} (${P.CAPAS[d.layer].forma}).` +
          (actual && actual.pasos && actual.pasos.has(d.key) ? ` Paso ${actual.pasos.get(d.key)} de su tema.` : '') +
          (actual && actual.sub.has(d.key) ? ` ${actual.sub.get(d.key)}.` : '') +
          (d.more_neighbors && !d.expandido ? ' Tiene más conexiones: tecla + para verlas.' : ''));

      selNodos.select('.halo').attr('r', d => radio(d) + 9);
      selNodos.select('.forma').attr('d', d => trazoForma(d, radio(d)))
        .attr('fill', d => d.layer === 'reference' ? hexRelleno(d) : `url(#g-${d.label})`)
        .attr('stroke', d => P.CLASES[d.label].color);
      selNodos.select('.contorno').attr('d', d => d.layer === 'reference' && radio(d) > 9 ? trazoHexagono(radio(d) * 0.7) : null)
        .attr('stroke', d => P.CLASES[d.label].color);
      selNodos.select('.glifo').attr('d', d => d.label === 'LearningResource' ? trazoDocumento(radio(d)) : null);
      selNodos.select('.expandir')
        .attr('transform', d => `translate(${radio(d) * 0.8 + 3},${-radio(d) * 0.8 - 3})`)
        .style('display', d => (enVecindario && d.more_neighbors && !d.expandido && d.key !== foco && !esMudo(d) && !esTenue(d)) ? null : 'none');

      selNodos.select('.etq').each(function (d) { pintarEtiqueta(d3.select(this), d); });

      configurarFuerzas(visibles, lineas);
      if (reducido || opciones.instantaneo) {
        sim.alpha(1);
        for (let i = 0; i < 260; i++) sim.tick();
        tic();
        sim.stop();
      } else {
        sim.alpha(0.9).restart();
      }
      if (cb.alDibujar) cb.alDibujar({ nodos: visibles, aristas: lineas, disposicion: actual });
    }

    function pintarEtiqueta(t, d) {
      const e = etiquetas.get(d.key) || { lado: 'abajo', lineas: partir(nombreDe(d), 21, 2), sub: '' };
      const r = radio(d), n = e.lineas.length;
      const lateral = e.lado === 'der' || e.lado === 'izq';
      const total = n + (e.sub && !e.enLinea ? 1 : 0);
      t.attr('class', 'etq' + (d.key === foco ? ' etq-foco' : '') + (e.oculta ? ' etq-oculta' : ''))
        .attr('text-anchor', e.lado === 'der' ? 'start' : (e.lado === 'izq' ? 'end' : 'middle'));
      const x = e.lado === 'der' ? r + 8 : (e.lado === 'izq' ? -(r + 8) : 0);
      const lh = d.key === foco ? INTERLINEA + 3 : INTERLINEA;
      let y0;
      if (e.lado === 'arriba') y0 = -(r + 9) - (total - 1) * lh;
      else if (lateral) y0 = -((total - 1) * lh) / 2 + 4.5;
      else y0 = r + (d.key === foco ? 20 : 16);
      t.selectAll('tspan').remove();
      e.lineas.forEach((l, i) => {
        const ts = t.append('tspan').attr('x', x).attr('y', y0 + i * lh).text(l);
        if (e.sub && e.enLinea && i === n - 1) ts.append('tspan').attr('class', 'sub').attr('dx', 7).text(e.sub);
      });
      if (e.sub && !e.enLinea) t.append('tspan').attr('class', 'sub').attr('x', x).attr('y', y0 + n * lh).text(e.sub);
    }

    function hexRelleno(d) {
      const c = d3.color(P.CLASES[d.label].color);
      c.opacity = d.key === foco ? 0.3 : 0.14;
      return c.formatRgb();
    }

    function configurarFuerzas(visibles, lineas) {
      const obj = actual ? actual.objetivos : null;
      const enlaces = lineas.map(e => ({ source: e.source, target: e.target, tipo: e.type }));
      sim.nodes(visibles);
      sim.force('enlace', d3.forceLink(enlaces).id(d => d.key)
        .distance(l => DISTANCIA[l.tipo] || 90)
        .strength(obj ? 0 : 0.2));
      sim.force('carga', d3.forceManyBody().strength(d => (obj && obj.has(d.key) ? 0 : -160)).distanceMax(400));
      sim.force('choque', obj ? null : d3.forceCollide(d => radio(d) + 10));
      // Cada nodo va a su lugar en la disposición: las etiquetas ya se colocaron contando con eso.
      sim.force('x', d3.forceX(d => (obj && obj.has(d.key) ? obj.get(d.key).x : 0)).strength(d => (obj && obj.has(d.key) ? 0.6 : 0.05)));
      sim.force('y', d3.forceY(d => (obj && obj.has(d.key) ? obj.get(d.key).y : 0)).strength(d => (obj && obj.has(d.key) ? 0.6 : 0.05)));
      sim.force('radial', null);
    }

    function tic() {
      selNodos.attr('transform', d => `translate(${d.x},${d.y})`);
      const curva = !!actual && actual.curva;
      const trazo = d => {
        // La arista HAS_PREREQUISITE se dibuja del prerrequisito al concepto que lo necesita.
        const invertir = d.type === 'HAS_PREREQUISITE';
        const a = nodos.get(invertir ? d.target : d.source);
        const b = nodos.get(invertir ? d.source : d.target);
        if (!a || !b) return null;
        if (curva && d.type === 'PART_OF') {
          const [i, f] = a.x <= b.x ? [a, b] : [b, a];
          // Las ramas salen del final del nombre del padre, para no tacharlo.
          const ei = etiquetas.get(i.key);
          const x0 = ei && ei.lado === 'der' && ei.caja ? i.x + (ei.caja.x1 - actual.objetivos.get(i.key).x) + 6 : i.x + radio(i) + 2;
          const x1 = f.x - radio(f) - 2, xm = (x0 + x1) / 2;
          return `M${x0},${i.y}C${xm},${i.y} ${xm},${f.y} ${x1},${f.y}`;
        }
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

    /** Encuadra todo lo dibujado, contando etiquetas, recuadros y rótulos, dentro del área libre del lienzo. */
    function encuadrar(_claves, ms) {
      const rect = svg.node().getBoundingClientRect();
      if (!rect.width) return;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      const sumar = (ax, ay, bx, by) => { x0 = Math.min(x0, ax); y0 = Math.min(y0, ay); x1 = Math.max(x1, bx); y1 = Math.max(y1, by); };
      const obj = actual ? actual.objetivos : null;
      for (const n of nodosVisibles()) {
        const o = (obj && obj.get(n.key)) || n, r = radio(n) + 10;
        sumar(o.x - r, o.y - r, o.x + r, o.y + r);
      }
      for (const e of etiquetas.values()) if (e.caja && !e.oculta) sumar(e.caja.x0, e.caja.y0, e.caja.x1, e.caja.y1);
      if (actual) {
        for (const c of actual.cajas) sumar(c.x0, c.y0, c.x1, c.y1);
        for (const t of actual.rotulos) {
          const w = t.texto.length * 6.8;
          const ax = t.ancla === 'start' ? t.x : (t.ancla === 'end' ? t.x - w : t.x - w / 2);
          sumar(ax, t.y - 14, ax + w, t.y + 6);
        }
      }
      if (!isFinite(x0)) return;
      const aire = 30;
      x0 -= aire; x1 += aire; y0 -= aire; y1 += aire;
      const alto = Math.max(120, rect.height - margen.arriba - margen.abajo);
      const k = Math.max(0.2, Math.min(1.1, Math.min(rect.width / (x1 - x0), alto / (y1 - y0))));
      const t = d3.zoomIdentity.translate(rect.width / 2, margen.arriba + alto / 2).scale(k).translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
      svg.transition().duration(reducido ? 0 : (ms === undefined ? 700 : ms)).call(zoom.transform, t);
    }

    function zoomPor(f) { svg.transition().duration(reducido ? 0 : 250).call(zoom.scaleBy, f); }

    // ---------------------------------------------------------------- interfaz pública

    return {
      establecer, agregar, marcarExpandido, mostrarPortada, dibujar, encuadrar, zoomPor,
      configurar(o) {
        if ('disposicion' in o) disposicion = o.disposicion;
        if ('verProcedencia' in o) verProcedencia = o.verProcedencia;
        if ('seleccion' in o) seleccion = o.seleccion;
        if ('margen' in o) margen = o.margen;
      },
      seleccionar(id) {
        seleccion = id;
        selAristas.classed('sel', d => d.id === seleccion);
      },
      contenido() { return { nodes: [...nodos.values()], edges: [...aristas.values()] }; },
      nodo(clave) { return nodos.get(clave) || null; },
      arista(id) { return aristas.get(id) || null; },
      /** La disposición en uso, para que la app describa lo que se ve (p. ej. cuántos puntos van sin nombre). */
      get disposicion() { return actual; },
      get foco() { return foco; },
    };
  }

  raiz.IEKG_LIENZO = { crearLienzo, disponer, COLOR_ARISTA, MAX_CONCEPTOS_EN_ARBOL };
})(typeof window !== 'undefined' ? window : globalThis);
