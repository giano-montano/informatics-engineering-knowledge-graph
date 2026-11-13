/* Constelación (P1) · estado, cabecera de contexto, panel del foco, buscador, rastro y recorrido. */
(function () {
  'use strict';
  const P = window.IEKG_P1;
  const L = window.IEKG_LIENZO;
  const $ = sel => document.querySelector(sel);

  const CLAVES = {
    contradiccion: 'ce8cd4d1-77f1-4ec1-b10f-d8b87dabe678',
    tablaVerdad: '29a47e34-1d18-4962-9501-c4f5b960003c',
    logica: '40347f92-1123-45ef-8225-b77837c551d7',
    inf144: 'b2d9c106-684d-58b8-8462-4dc0c3b8d90c',
    archivos: '9a161bca-1a01-43de-8875-7bdfb53ebd84',
  };

  // Orden de las vistas en la cabecera. Solo se ofrecen las que aplican al elemento en foco.
  const ORDEN_LENTES = ['vecindario', 'prerrequisitos', 'ruta', 'cursos', 'ubicacion', 'contiene', 'recursos', 'especializaciones'];

  const estado = {
    foco: null,
    nodoFoco: null,
    lente: 'vecindario',
    grano: 'course',
    rastro: [],
    verProcedencia: false,
    respLente: null,
    respFoco: null,
    disp: null,         // disposición de la vista activa (lo que el mapa decidió mostrar)
    expansiones: 0,     // cuántas veces se usó «+» desde el último foco
    aristaSel: null,
    porque: null,       // parada del camino cuyo «¿Por qué?» está abierto
    turno: 0,           // descarta respuestas viejas si el estudiante hace clic rápido
  };

  // ------------------------------------------------------------------ utilidades de presentación

  function esc(t) {
    return String(t === undefined || t === null ? '' : t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  const ARTICULO = { Área: 'un área', Unidad: 'una unidad', Tema: 'un tema', Concepto: 'un concepto', Curso: 'un curso',
    Sílabo: 'un sílabo', Documento: 'un documento', 'Tipo de recurso': 'un tipo de recurso' };
  function conArticulo(n) { return ARTICULO[P.nombreClase(n)] || P.nombreClase(n).toLowerCase(); }
  function plural(n, uno, varios) { return `${n} ${n === 1 ? uno : varios}`; }

  const ICONO = {
    sale: '<svg class="ico" width="11" height="11" viewBox="0 0 12 12" aria-hidden="true"><path d="M4 2h6v6M10 2L2.5 9.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    cerrar: '<svg class="ico" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 2.5l7 7M9.5 2.5l-7 7" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    antes: '<svg class="ico" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M7.5 2L3.5 6l4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    despues: '<svg class="ico" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M4.5 2l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    doc: '<svg class="ico" width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 1.5h6l4 4v9H3z M9 1.5v4h4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    mapa: '<svg class="ico" width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="2.2" fill="currentColor"/><circle cx="2.8" cy="4" r="1.4" fill="currentColor"/><circle cx="13.2" cy="4.6" r="1.4" fill="currentColor"/><circle cx="12" cy="13" r="1.4" fill="currentColor"/><path d="M4 4.8l2.3 1.9M11.9 5.3L9.8 6.9M11 12l-1.6-2.3" stroke="currentColor" stroke-width="1"/></svg>',
  };

  function iconoCapa(capa, tam) {
    tam = tam || 14;
    if (capa === 'reference') {
      return `<svg class="ico-capa" width="${tam}" height="${tam}" viewBox="-8 -8 16 16" aria-hidden="true"><path d="M0,-7L6.1,-3.5V3.5L0,7L-6.1,3.5V-3.5Z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M0,-4L3.5,-2V2L0,4L-3.5,2V-2Z" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/></svg>`;
    }
    return `<svg class="ico-capa" width="${tam}" height="${tam}" viewBox="-8 -8 16 16" aria-hidden="true"><circle r="6.2" fill="currentColor"/></svg>`;
  }

  function chipClase(n) {
    const c = P.CLASES[n.label];
    return `<span class="chip-clase" style="--c:${c.color}">${esc(P.nombreClase(n))}</span>`;
  }

  function insigniaCapa(n) {
    return `<span class="insignia-capa capa-${n.layer}" title="${esc(P.CAPAS[n.layer].detalle)}">${iconoCapa(n.layer)}<span>${esc(P.CAPAS[n.layer].nombre)}</span></span>`;
  }

  function botonNodo(n, extra) {
    const c = P.CLASES[n.label];
    return `<button class="item-nodo" data-ir="${esc(n.key)}" style="--c:${c.color}" title="${esc(P.nombreClase(n))} · ${esc(P.CAPAS[n.layer].nombre)}">` +
      `<span class="marca capa-${n.layer}">${iconoCapa(n.layer, 12)}</span><span class="nombre">${esc(n.name_es)}${n.course_code ? ` <em>${esc(n.course_code)}</em>` : ''}</span>${extra || ''}</button>`;
  }

  function enlaceDocumento(doc, texto) {
    if (!doc || !doc.locator) return '';
    const ref = doc.layer === 'reference';
    return `<a class="enlace-doc capa-${doc.layer}" href="${esc(doc.locator)}" target="_blank" rel="noopener">${ICONO.doc}` +
      `<span>${esc(texto || (ref ? 'CS2023' : doc.name_es))}</span>${ICONO.sale}` +
      `<span class="sr">(abre ${ref ? 'CS2023 en la biblioteca digital de ACM' : 'el PDF del sílabo'} en una pestaña nueva)</span></a>`;
  }

  function botonFuente(arista, nombre) {
    return `<button class="mini-arista" data-arista="${esc(idDeArista(arista))}" title="Ver qué documento afirma esta relación"` +
      `${nombre ? ` aria-label="Ver la fuente de la relación con ${esc(nombre)}"` : ''}>fuente</button>`;
  }

  let temporizadorAviso = null;
  function aviso(texto) {
    const el = $('#aviso');
    el.textContent = texto;
    el.classList.add('visible');
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => el.classList.remove('visible'), 3800);
  }

  // ------------------------------------------------------------------ lienzo

  const lienzo = L.crearLienzo($('#escena-lienzo'), {
    alClicNodo: n => { if (n.key !== estado.foco) irA(n.key); },
    alExpandir: n => expandir(n.key),
    alClicArista: a => seleccionarArista(a.id),
    alClicVacio: () => { if (estado.aristaSel) { estado.aristaSel = null; lienzo.seleccionar(null); pintarPanel(); } },
    alPasarNodo: (n, ev) => mostrarInfo(n ? infoNodo(n) : null, ev),
    alPasarArista: (a, ev) => mostrarInfo(a ? infoArista(a) : null, ev),
    alZoom: k => { $('#zoom-valor').textContent = Math.round(k * 100) + ' %'; },
    alDibujar: pintarLeyendaViva,
  });

  function infoNodo(n) {
    return `<strong>${esc(n.name_es)}</strong>${n.name_en ? `<span class="en" lang="en">${esc(n.name_en)}</span>` : ''}` +
      `<span class="linea">${chipClase(n)} ${iconoCapa(n.layer, 11)} ${esc(P.CAPAS[n.layer].nombre)}</span>` +
      (estado.foco === null ? '<span class="pista">Clic para empezar aquí</span>' :
        (n.key === estado.foco ? '<span class="pista">Es el elemento en foco</span>' :
          `<span class="pista">Clic para ir a él${n.more_neighbors && !n.expandido && estado.lente === 'vecindario' ? ' · <b>+</b> para traer sus conexiones' : ''}</span>`));
  }

  function infoArista(a) {
    const cont = lienzo.contenido();
    const s = P.nodoPorClave(cont, a.source), t = P.nodoPorClave(cont, a.target);
    const doc = P.documentoDeArista(cont, a);
    return `<span class="linea"><b>${esc(s ? s.name_es : '')}</b> ${esc(P.RELACIONES[a.type].frase)} <b>${esc(t ? t.name_es : '')}</b></span>` +
      `<span class="pista">${doc ? 'Lo dice: ' + esc(doc.layer === 'reference' ? 'CS2023' : doc.name_es) : 'Sin fuente registrada'} · clic para ver la fuente</span>`;
  }

  function mostrarInfo(html, ev) {
    const el = $('#info-flotante');
    if (!html) { el.classList.remove('visible'); return; }
    el.innerHTML = html;
    el.classList.add('visible');
    const caja = $('#escena').getBoundingClientRect();
    let x = ev.clientX - caja.left + 16, y = ev.clientY - caja.top + 14;
    if (x + 290 > caja.width) x = ev.clientX - caja.left - 300;
    if (y + 110 > caja.height) y = ev.clientY - caja.top - 110;
    el.style.transform = `translate(${x}px, ${y}px)`;
  }

  /** El mapa se encuadra en el hueco que dejan la cabecera y el pie. */
  function medirMargen() {
    lienzo.configurar({ margen: { arriba: $('#contexto').offsetHeight + 14, abajo: $('#pie-escena').offsetHeight + 26 } });
  }

  function encuadrarLuego(turno, ms) {
    setTimeout(() => { if (turno === estado.turno) { medirMargen(); lienzo.encuadrar(null, ms); } }, 60);
  }

  // ------------------------------------------------------------------ por qué de cada tramo del camino (CU-8)

  /** ¿La meta es parte (por PART_OF, a cualquier altura) de esta parada? Pasa con su propio tema. */
  function contieneLaMeta(resp, estacion, meta) {
    let frente = [meta];
    const vistos = new Set(frente);
    while (frente.length) {
      const sig = [];
      for (const k of frente) {
        for (const e of resp.edges) {
          if (e.type !== 'PART_OF' || e.source !== k || vistos.has(e.target)) continue;
          if (e.target === estacion) return true;
          vistos.add(e.target); sig.push(e.target);
        }
      }
      frente = sig;
    }
    return false;
  }

  /**
   * Relaciones de la respuesta que unen una parada con la meta: el camino más corto que llega
   * a la meta por «necesita antes» (no por «es parte de»). Solo lee aristas que trajo la API.
   */
  function justificarEstacion(resp, estacion, meta) {
    const ady = new Map();
    const poner = (k, v) => { if (!ady.has(k)) ady.set(k, []); ady.get(k).push(v); };
    for (const e of resp.edges) {
      if (e.type === 'WAS_DERIVED_FROM') continue;
      poner(e.source, { k: e.target, e }); poner(e.target, { k: e.source, e });
    }
    const previo = new Map([[estacion, null]]);
    const cola = [estacion];
    while (cola.length) {
      const k = cola.shift();
      if (k === meta) break;
      for (const v of ady.get(k) || []) {
        if (previo.has(v.k)) continue;
        if (v.k === meta && v.e.type !== 'HAS_PREREQUISITE') continue;
        previo.set(v.k, { k, e: v.e });
        cola.push(v.k);
      }
    }
    if (!previo.has(meta)) return [];
    const tramo = [];
    for (let k = meta; previo.get(k); k = previo.get(k).k) tramo.unshift(previo.get(k).e);
    return tramo;
  }

  function idDeArista(e) { return e.type + '|' + e.source + '|' + e.target; }

  /** «el mismo tema» / «la misma área» / «el mismo curso», según por qué se agrupa el camino. */
  function mismoGrupo(grano) {
    return grano === 'topic' ? 'el mismo tema' : (grano === 'area' ? 'la misma área' : 'el mismo curso');
  }

  // ------------------------------------------------------------------ portada (ruta nueva, simulada)

  async function mostrarPortada() {
    const turno = ++estado.turno;
    estado.foco = null; estado.nodoFoco = null; estado.respFoco = null; estado.respLente = null;
    estado.aristaSel = null; estado.lente = 'vecindario'; estado.disp = null; estado.expansiones = 0;
    const r = await P.apiPortada();
    const lista = r.cuerpo.areas.map(a => ({
      key: a.key, label: 'KnowledgeArea', name_es: a.name_es, name_en: a.name_en, layer: 'reference',
      concepts: a.concepts, sub: a.concepts > 0 ? `${plural(a.topics, 'tema', 'temas')} · ${a.concepts} conceptos` : '',
    })).concat(r.cuerpo.courses.map(c => ({
      key: c.key, label: 'Course', name_es: c.name_es, layer: 'institutional', course_code: c.code,
    })));
    estado.portada = { areas: r.cuerpo.areas.length, conTemas: r.cuerpo.areas.filter(a => a.concepts > 0).length, cursos: r.cuerpo.courses.length };
    $('#escena').classList.add('en-portada');
    buscador.value = '';
    lienzo.mostrarPortada(lista);
    lienzo.dibujar();
    pintarContexto();
    pintarRastro();
    pintarRecorrido();
    pintarPanel();
    encuadrarLuego(turno, 800);
  }

  // ------------------------------------------------------------------ foco, vistas y expansión

  async function irA(clave, opciones) {
    opciones = opciones || {};
    const turno = ++estado.turno;
    const r = await P.api('/api/nodes', { key: clave });
    if (turno !== estado.turno) return;
    if (r.estado !== 200) { aviso('No se encontró ese elemento.'); return; }
    $('#escena').classList.remove('en-portada');
    estado.foco = clave;
    estado.respFoco = r.cuerpo;
    estado.nodoFoco = r.cuerpo.nodes[0];
    estado.aristaSel = null;
    estado.porque = null;
    estado.expansiones = 0;
    $('#panel').scrollTop = 0;
    lienzo.establecer(r.cuerpo, clave);
    if (opciones.rastro !== false) {
      estado.rastro = estado.rastro.filter(x => x.key !== clave);
      estado.rastro.push({ key: clave, name_es: estado.nodoFoco.name_es, label: estado.nodoFoco.label, layer: estado.nodoFoco.layer });
      if (estado.rastro.length > 9) estado.rastro.shift();
    }
    let lente = opciones.lente || estado.lente;
    if (opciones.grano) estado.grano = opciones.grano;
    if (!P.lenteAplica(lente, estado.nodoFoco)) {
      if (lente !== 'vecindario') aviso(`«${P.LENTES[lente].nombre}» no aplica a ${conArticulo(estado.nodoFoco)}: ves lo que lo rodea.`);
      lente = 'vecindario';
    }
    await aplicarLente(lente, turno);
    pintarRastro();
  }

  async function aplicarLente(lente, turno) {
    turno = turno || ++estado.turno;
    estado.lente = lente;
    estado.respLente = null;
    estado.disp = null;
    estado.porque = null;
    if (lente !== 'vecindario' && estado.foco) {
      const def = P.LENTES[lente];
      const params = { key: estado.foco };
      if (lente === 'ruta') params.grain = estado.grano;
      const r = await P.api(def.ruta, params);
      if (turno !== estado.turno) return;
      if (r.estado !== 200) { aviso('Esta vista no tiene datos para el elemento en foco.'); return aplicarLente('vecindario'); }
      estado.respLente = r.cuerpo;
      lienzo.agregar(r.cuerpo, estado.foco);
      estado.disp = L.disponer(lente, r.cuerpo, estado.foco, estado.grano);
    }
    lienzo.configurar({ disposicion: estado.disp, verProcedencia: estado.verProcedencia });
    lienzo.dibujar();
    pintarContexto();
    pintarRecorrido();
    pintarPanel();
    encuadrarLuego(turno, 750);
  }

  async function expandir(clave) {
    const r = await P.api('/api/nodes', { key: clave });
    if (r.estado !== 200) return;
    const nombre = r.cuerpo.nodes[0].name_es;
    lienzo.agregar(r.cuerpo, clave);
    lienzo.marcarExpandido(clave);
    estado.expansiones++;
    aviso(`Se trajeron las conexiones de «${nombre}»: están arriba o abajo, con su nombre. Sigues en el mismo lugar.`);
    await aplicarLente('vecindario');
  }

  function limpiar() {
    if (!estado.foco || !estado.respFoco) return;
    estado.expansiones = 0;
    lienzo.establecer(estado.respFoco, estado.foco);
    aplicarLente(estado.lente);
  }

  function seleccionarArista(id) {
    estado.aristaSel = id;
    lienzo.seleccionar(id);
    pintarPanel().then(() => {
      const tarjeta = $('#tarjeta-arista');
      if (tarjeta) tarjeta.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
  }

  /** Abre el «¿Por qué?» de una parada: la tarjeta en el panel y la línea que llega a la meta, marcada en el mapa. */
  function abrirPorque(clave) {
    estado.porque = estado.porque === clave ? null : clave;
    const tramo = estado.porque ? justificarEstacion(estado.respLente, clave, estado.foco) : [];
    lienzo.seleccionar(tramo.length ? idDeArista(tramo[tramo.length - 1]) : null);
    pintarFranja();
    pintarPanel().then(() => {
      const tarjeta = $('#tarjeta-porque');
      if (tarjeta) tarjeta.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
  }

  // ------------------------------------------------------------------ cabecera de contexto: qué se ve y cómo leerlo

  function cadenaTexto(resp, clave) {
    const c = P.cadenasDeUbicacion(resp, clave)[0] || [];
    return c.map(x => `<b>${esc(x.name_es)}</b>`).join(' › ');
  }

  /** La respuesta de la vista en una frase (`r`) y cómo leer el dibujo (`leer`). */
  function resumenLente() {
    const n = estado.nodoFoco, r = estado.respLente, disp = estado.disp;
    if (!n) return { r: '', leer: '' };
    const nombre = `<b>${esc(n.name_es)}</b>`;
    switch (estado.lente) {
      case 'vecindario': {
        const d = lienzo.disposicion;
        // Se cuenta lo que el mapa dibuja: tras pasar por otra vista puede haber más que en la primera respuesta.
        const directos = d && d.directos !== undefined ? d.directos : P.conexiones(estado.respFoco, estado.foco).reduce((t, g) => t + g.items.length, 0);
        const lejanos = d && d.lejanos ? ' Los puntos apagados de arriba y abajo están un paso más lejos.' : '';
        const racimos = d && d.racimos ? ' Un grupo grande va en un recuadro de puntos: el nombre de cada uno sale al pasar el cursor, y la lista está en «Conexiones», en la ficha.' : '';
        return {
          r: directos ? `Aquí ves con qué se relaciona ${nombre}: ${plural(directos, 'elemento conectado', 'elementos conectados')} directamente, agrupados por tipo de relación.`
            : `${nombre} todavía no tiene relaciones registradas.`,
          leer: `Haz clic en un punto para ir a él.${racimos}${lejanos} El <b class="mas">+</b> trae las conexiones de un punto sin cambiar de lugar.` +
            (estado.expansiones ? ' <button class="enlace-lente" id="limpiar">Quitar lo que trajiste con +</button>' : ''),
        };
      }
      case 'prerrequisitos': {
        const g = P.prerrequisitosPorProfundidad(r, estado.foco);
        const total = g.reduce((s, x) => s + x.items.length, 0);
        if (!total) {
          const dependen = P.conexiones(estado.respFoco, estado.foco).find(x => x.tipo === 'HAS_PREREQUISITE' && x.sentido === 'entrada');
          return {
            r: `${nombre} no necesita nada antes, según los sílabos cargados: puedes empezar por aquí.` +
              (dependen ? ` Se necesita para ${dependen.items.map(i => `<b>${esc(i.nodo.name_es)}</b>`).join(', ')}.` : ''),
            leer: '',
          };
        }
        const max = g[g.length - 1].profundidad;
        return {
          r: `Aquí ves lo que te falta saber antes de aprender ${nombre}: ${plural(total, 'concepto', 'conceptos')}` +
            (max > 1 ? `, el más lejano a ${max} pasos.` : (total > 1 ? ', todos justo antes.' : ', justo antes.')),
          leer: 'Se lee de izquierda a derecha: cada flecha sale de lo que se aprende primero y llega a lo que lo necesita. Haz clic en una flecha para ver qué sílabo lo dice.',
        };
      }
      case 'ruta': {
        const s = P.resumenRuta(r, estado.foco, estado.grano);
        const g = P.GRANOS[estado.grano];
        if (s.vacia) {
          return n.label === 'Course'
            ? { r: `Lo que ${nombre} pide se aprende dentro del mismo curso, así que no hay camino previo por ${g.plural}. Para saber qué curso conviene llevar antes, abre <button class="enlace-lente" data-lente="cursos">Cursos que conviene llevar antes</button>.`, leer: '' }
            : { r: `Para llegar a ${nombre} no hace falta pasar antes por ${g.nombre === 'área' ? 'otra área' : 'otro ' + g.nombre}, según los sílabos cargados.`, leer: '' };
        }
        const propia = s.estaciones.find(x => contieneLaMeta(r, x.key, estado.foco));
        const verbo = estado.grano === 'course' ? 'se enseña' : 'está';
        return {
          r: `Para llegar a ${nombre} conviene pasar antes por ${plural(s.estaciones.length, g.nombre, g.plural)}: ahí ${verbo} lo que necesitas saber antes (${plural(s.prerrequisitos.length, 'concepto', 'conceptos')}).`,
          leer: `En el mapa: abajo, los conceptos que necesitas antes; arriba, ${estado.grano === 'area' ? 'las áreas' : 'los ' + g.plural} donde se aprenden. <b>¿Por qué?</b> muestra la relación exacta y su fuente.` +
            (propia ? ` «${esc(propia.name_es)}» cuenta aunque también contiene a la meta: lo que se necesita antes es el concepto.` : ''),
        };
      }
      case 'cursos': {
        const c = P.cursosPrevios(r, estado.foco);
        const ensena = `${plural(c.ensenados, 'concepto', 'conceptos')}`;
        if (!c.previos.length) {
          return {
            r: `${nombre} enseña ${ensena}` + (c.requeridos.length ? ` y pide ${c.requeridos.length} que ningún otro curso cargado enseña.` : ' y no pide ninguno de otro curso cargado: no hay curso que convenga llevar antes.'),
            leer: 'En el recuadro, lo que el curso enseña. La lista con nombres está en la ficha de la derecha.',
          };
        }
        return {
          r: `${nombre} pide ${plural(c.requeridos.length, 'concepto', 'conceptos')} que enseña ${c.previos.map(p => `<b>${esc(p.curso.name_es)}</b>`).join(' y ')}: conviene llevarlo antes.`,
          leer: `De izquierda a derecha: el curso que conviene llevar antes, lo que este curso pide y, en el recuadro, los ${ensena} que enseña (la lista con nombres está en la ficha).`,
        };
      }
      case 'ubicacion':
        return {
          r: `${nombre} está en ${cadenaTexto(r, estado.foco) || 'el nivel más alto'}.`,
          leer: 'De arriba abajo, de lo más general a lo más específico. Los hexágonos son del estándar CS2023; los círculos, de los sílabos. Haz clic en cualquiera para ir a él.',
        };
      case 'contiene': {
        if (n.label === 'Topic') {
          const o = P.ordenDeAprendizaje(r, estado.foco);
          if (!o.relacionados.size) {
            return { r: `${nombre} tiene ${plural(o.conceptos.length, 'concepto', 'conceptos')}. Ninguno depende de otro: se pueden aprender en cualquier orden.`, leer: 'Haz clic en un concepto para ver qué necesita antes.' };
          }
          return {
            r: `${nombre} tiene ${plural(o.conceptos.length, 'concepto', 'conceptos')}, y conviene aprenderlos en ${plural(o.pasos.length, 'paso', 'pasos')}.`,
            leer: 'Cada columna es un paso: lo de una columna usa lo de la anterior. Las flechas dicen exactamente qué necesita qué.',
          };
        }
        const c = P.conteoPorClase({ nodes: P.descendientes(r, estado.foco) });
        const partes = [['KnowledgeUnit', 'unidad', 'unidades'], ['Topic', 'tema', 'temas'], ['Concept', 'concepto', 'conceptos']]
          .filter(([k]) => c[k]).map(([k, s, p]) => `<b>${plural(c[k], s, p)}</b>`);
        if (!c.Topic) return { r: `${nombre} contiene ${partes.join(', ') || 'nada todavía'}. Ningún sílabo cargado trata esta parte de CS2023 por ahora.`, leer: '' };
        const hastaTemas = disp && !disp.verConceptos;
        return {
          r: `${nombre} contiene ${partes.join(', ').replace(/, ([^,]*)$/, ' y $1')}.`,
          leer: (hastaTemas
            ? `Con más de ${L.MAX_CONCEPTOS_EN_ARBOL} conceptos, el mapa llega hasta los temas para que se pueda leer. Entra a un tema para ver sus conceptos y en qué orden aprenderlos.`
            : 'De izquierda a derecha, de lo más general a lo más específico. Entra a un tema para ver en qué orden aprender sus conceptos.') +
            (disp && disp.unidadesResumidas ? ' Las unidades sin temas están en «Conexiones», en la ficha.' : ''),
        };
      }
      case 'recursos': {
        const rec = P.recursosDe(r, estado.foco);
        if (!rec.length) return { r: `${nombre} no tiene material propio: los sílabos describen temas, no conceptos sueltos. En la ficha tienes el de su tema.`, leer: '' };
        return {
          r: `${plural(rec.length, 'sílabo trata', 'sílabos tratan')} sobre ${nombre} o sobre sus partes.`,
          leer: 'De izquierda a derecha: el elemento, sus partes y los sílabos que tratan sobre ellas. El enlace para abrir cada sílabo está en la ficha.',
        };
      }
      case 'especializaciones': {
        const e = P.especializaciones(r, estado.foco);
        if (!e.todas.length) return { r: `${nombre} no es un tipo de otro concepto ni tiene tipos registrados. Hay pocos casos en los sílabos cargados: prueba con «ethernet».`, leer: '' };
        return {
          r: `${nombre}${e.generales.length ? ` es un tipo de <b>${esc(e.generales.map(x => x.name_es).join(', '))}</b>` : ''}${e.generales.length && e.tipos.length ? ' y' : ''}${e.tipos.length ? ` tiene ${plural(e.tipos.length, 'tipo', 'tipos')}` : ''}.`,
          leer: 'Arriba, el concepto más general; abajo, sus tipos. La flecha se lee «es un tipo de».',
        };
      }
      default: return { r: '', leer: '' };
    }
  }

  function pintarContexto() {
    const n = estado.nodoFoco;
    const vistas = $('#vistas'), granos = $('#granos');
    $('#inicio').hidden = !n;
    if (!n) {
      const p = estado.portada || { areas: 17, conTemas: 0, cursos: 4 };
      $('#contexto-foco').innerHTML = '<h1 class="contexto-titulo">Elige por dónde empezar</h1>';
      vistas.hidden = true; granos.hidden = true;
      $('#vista-respuesta').innerHTML = `Alrededor, las <b>${p.areas} áreas</b> de la carrera según el estándar CS2023: las ${p.conTemas} que brillan ya tienen temas de los sílabos cargados. Al centro, los <b>${p.cursos} cursos</b> con sílabo.`;
      $('#vista-leer').innerHTML = 'Haz clic en un área o en un curso, o busca por nombre arriba. <span class="etiqueta-simulado" title="El sistema todavía no entrega esta vista de inicio: necesita una ruta nueva">vista simulada</span>';
      pintarFranja();
      return;
    }
    $('#contexto-foco').innerHTML = `${chipClase(n)}<h1 class="contexto-titulo">${esc(n.name_es)}${n.course_code ? ` <em>${esc(n.course_code)}</em>` : ''}</h1>`;
    vistas.hidden = false;
    vistas.innerHTML = ORDEN_LENTES.filter(id => P.lenteAplica(id, n)).map(id => {
      const def = P.LENTES[id];
      const activa = estado.lente === id;
      return `<button class="vista${activa ? ' activa' : ''}" data-lente="${id}" aria-pressed="${activa}" title="${esc(def.ayuda)}">${esc(def.nombre)}</button>`;
    }).join('');
    const res = resumenLente();
    $('#vista-respuesta').innerHTML = res.r;
    $('#vista-leer').innerHTML = res.leer;
    $('#vista-leer').hidden = !res.leer;
    granos.hidden = estado.lente !== 'ruta';
    granos.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.grano === estado.grano)));
    pintarFranja();
  }

  /** El camino en una línea: las paradas, en el orden en que conviene pasar, hasta la meta. */
  function pintarFranja() {
    const f = $('#franja');
    const r = estado.respLente;
    let html = '';
    const parada = (n, extra) => `<button class="parada" data-ir="${esc(n.key)}" style="--c:${P.CLASES[n.label].color}">${iconoCapa(n.layer, 11)}<span>${esc(n.name_es)}${n.course_code ? ` <em>${esc(n.course_code)}</em>` : ''}</span>${extra || ''}</button>`;
    const flecha = '<span class="flecha" aria-hidden="true"></span>';
    // Solo el camino lleva franja: en las demás vistas, el mapa ya dice lo mismo.
    if (estado.lente === 'ruta' && r && estado.nodoFoco) {
      const s = P.resumenRuta(r, estado.foco, estado.grano);
      if (!s.vacia) {
        // Las paradas a la misma distancia no tienen orden entre sí: van juntas, sin flecha.
        const grupos = [];
        for (const n of s.estaciones) {
          const u = grupos[grupos.length - 1];
          if (u && u.d === n.depth) u.items.push(n); else grupos.push({ d: n.depth, items: [n] });
        }
        html = grupos.map(g => `<span class="grupo-paradas">${g.items.map(n => {
          const propia = contieneLaMeta(r, n.key, estado.foco);
          return `<span class="estacion">${parada(n, propia ? `<em class="marca-propia" title="Lo que se necesita antes está en ${esc(mismoGrupo(estado.grano))} que la meta">${esc(mismoGrupo(estado.grano))}</em>` : '')}` +
            `<button class="porque${estado.porque === n.key ? ' activo' : ''}" data-porque="${esc(n.key)}" aria-expanded="${estado.porque === n.key}" aria-label="¿Por qué pasar por ${esc(n.name_es)}? Ver la relación y su fuente">¿Por qué?</button></span>`;
        }).join('')}</span>`).join(flecha) + `<span class="llegada">${flecha}<span class="llegada-texto">y de ahí a la meta</span></span>`;
      }
    }
    f.innerHTML = html;
    f.hidden = !html;
  }

  // ------------------------------------------------------------------ leyenda de la vista: solo lo que hay en pantalla

  function pintarLeyendaViva(vista) {
    const el = $('#leyenda-viva');
    const orden = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept', 'Course', 'LearningResource', 'ResourceType'];
    const clases = new Map();
    const capas = new Set();
    for (const n of vista.nodos) { clases.set(n.label, P.nombreClase(n)); capas.add(n.layer); }
    const formas = [];
    if (capas.has('reference')) formas.push(`<span class="ley-item capa-reference">${iconoCapa('reference', 13)}de CS2023</span>`);
    if (capas.has('institutional')) formas.push(`<span class="ley-item capa-institutional">${iconoCapa('institutional', 13)}de un sílabo</span>`);
    const colores = orden.filter(c => clases.has(c)).map(c => `<span class="ley-item" style="--c:${P.CLASES[c].color}"><i></i>${esc(clases.get(c))}</span>`);
    el.innerHTML = formas.join('') + (formas.length && colores.length ? '<span class="ley-sep" aria-hidden="true"></span>' : '') + colores.join('');
  }

  // ------------------------------------------------------------------ rastro

  function pintarRastro() {
    const el = $('#rastro-lista');
    if (!estado.rastro.length) { el.innerHTML = '<span class="vacio">Lo que visites queda aquí, para volver.</span>'; }
    else {
      el.innerHTML = estado.rastro.map((x, i) => {
        const actual = x.key === estado.foco;
        return (i ? '<span class="sep" aria-hidden="true">›</span>' : '') +
          `<button class="miga${actual ? ' actual' : ''}" data-ir="${esc(x.key)}" data-rastro="1" style="--c:${P.CLASES[x.label].color}" ${actual ? 'aria-current="true"' : ''}>${iconoCapa(x.layer, 10)}<span>${esc(x.name_es)}</span></button>`;
      }).join('');
      el.scrollLeft = el.scrollWidth;
    }
    const i = estado.rastro.findIndex(x => x.key === estado.foco);
    $('#atras').disabled = i <= 0;
  }

  // ------------------------------------------------------------------ panel del foco

  /** Título de una sección de la ficha. Si tiene vista en el mapa, la ofrece o dice que es la que se está viendo. */
  function tituloSeccion(texto, lente, extra) {
    let lado = extra || '';
    if (lente && P.lenteAplica(lente, estado.nodoFoco)) {
      lado = estado.lente === lente
        ? `<span class="en-mapa">${ICONO.mapa}En el mapa</span>`
        : `<button class="enlace-lente" data-lente="${lente}">Ver en el mapa</button>`;
    }
    return `<h3 class="sec-titulo"><span>${esc(texto)}</span>${lado}</h3>`;
  }
  function claseSeccion(lente) { return 'sec' + (lente && estado.lente === lente ? ' sec-activa' : ''); }

  function tarjetaRelacion(resp, e, conMapa) {
    const o = P.nodoPorClave(resp, e.source), d = P.nodoPorClave(resp, e.target);
    const doc = P.documentoDeArista(resp, e);
    return `<p class="afirmacion">${o ? botonNodo(o) : ''}<span class="rel" style="--c:${L.COLOR_ARISTA[e.type]}">${esc(P.RELACIONES[e.type].frase)}</span>${d ? botonNodo(d) : ''}</p>
      <div class="procedencia">${doc ? `<span class="rotulo">${e.provenance ? 'Lo dice' : 'Lo define'}</span>${enlaceDocumento(doc)}` : '<span class="rotulo">Sin fuente registrada</span>'}
      ${conMapa ? `<button class="mini-arista" data-arista="${esc(idDeArista(e))}" title="Marcar esta línea en el mapa">ver en el mapa</button>` : ''}</div>`;
  }

  async function pintarPanel() {
    const panel = $('#panel-cuerpo');
    const n = estado.nodoFoco;
    if (!n) { panel.innerHTML = panelPortada(); return; }
    const turno = estado.turno;
    const clave = estado.foco;
    const esElemento = ['KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept'].includes(n.label);

    const [loc, pre, rec, cur, esp] = await Promise.all([
      esElemento ? P.api('/api/elements/location', { key: clave }) : null,
      P.lenteAplica('prerrequisitos', n) ? P.api('/api/concepts/prerequisites', { key: clave }) : null,
      P.lenteAplica('recursos', n) ? P.api('/api/elements/resources', { key: clave }) : null,
      P.lenteAplica('cursos', n) ? P.api('/api/courses/prerequisites', { key: clave }) : null,
      P.lenteAplica('especializaciones', n) ? P.api('/api/concepts/specializations', { key: clave }) : null,
    ]);
    if (turno !== estado.turno || clave !== estado.foco) return;
    const rf = estado.respFoco;
    const s = [];

    // Cabecera: qué es, de dónde viene y qué documento lo afirma.
    const fuentes = n.label === 'LearningResource' ? [n] : P.procedenciaDe(rf, clave);
    const origen = n.layer === 'reference'
      ? 'Viene de CS2023, el estándar internacional del currículo de computación (ACM/IEEE).'
      : 'Viene del sílabo del curso. En esta maqueta, el PDF abre solo con el sistema en marcha.';
    s.push(`<header class="ficha" style="--c:${P.CLASES[n.label].color}">
      <div class="ficha-chips">${chipClase(n)} ${insigniaCapa(n)}</div>
      <h2>${esc(n.name_es)}</h2>
      ${n.name_en ? `<p class="en" lang="en">${esc(n.name_en)}</p>` : ''}
      ${n.course_code ? `<p class="codigo">Código ${esc(n.course_code)}</p>` : ''}
      ${n.description ? `<p class="descripcion">${esc(n.description)}</p>` : ''}
      <div class="ficha-fuente" title="${esc(origen)}">
        <span class="rotulo">${n.label === 'LearningResource' ? 'Documento' : 'Fuente'}</span>
        ${fuentes.length ? fuentes.map(f => enlaceDocumento(f, n.label === 'LearningResource' ? 'Abrir ' + f.name_es : null)).join('') : '<span class="nota">no se registró de dónde sale</span>'}
      </div>
      <p class="nota">${origen}</p>
    </header>`);

    // Relación seleccionada: su fuente.
    if (estado.aristaSel) {
      const a = lienzo.arista(estado.aristaSel);
      if (a) {
        s.push(`<section class="tarjeta-arista" id="tarjeta-arista" aria-live="polite">
          <div class="sec-titulo"><span>Relación seleccionada</span><button class="cerrar-mini" data-cerrar-arista aria-label="Cerrar">${ICONO.cerrar}</button></div>
          ${tarjetaRelacion(lienzo.contenido(), a, false)}
        </section>`);
      }
    }

    // ¿Por qué este tramo del camino? (CU-8)
    if (estado.porque && estado.lente === 'ruta' && estado.respLente) {
      const r = estado.respLente;
      const est = P.nodoPorClave(r, estado.porque);
      const tramo = justificarEstacion(r, estado.porque, clave);
      const propia = contieneLaMeta(r, estado.porque, clave);
      if (est) {
        s.push(`<section class="tarjeta-arista tarjeta-porque" id="tarjeta-porque" aria-live="polite">
          <div class="sec-titulo"><span>¿Por qué pasar por «${esc(est.name_es)}»?</span><button class="cerrar-mini" data-cerrar-porque aria-label="Cerrar">${ICONO.cerrar}</button></div>
          ${propia ? `<p class="mismo-grupo">Lo que se necesita antes está en ${mismoGrupo(estado.grano)} que la meta.</p>` : ''}
          ${tramo.length ? `<ol class="tramo">${tramo.map(e => `<li>${tarjetaRelacion(r, e, true)}</li>`).join('')}</ol>` : '<p class="nota">La respuesta no trae las relaciones que unen esta parada con la meta.</p>'}
        </section>`);
      }
    }

    // Dónde está en la carrera.
    if (loc && loc.estado === 200 && P.lenteAplica('ubicacion', n)) {
      const cadenas = P.cadenasDeUbicacion(loc.cuerpo, clave);
      if (cadenas.length) {
        s.push(`<section class="${claseSeccion('ubicacion')}">${tituloSeccion('Dónde está en la carrera', 'ubicacion')}
          ${cadenas.map(c => `<nav class="migas" aria-label="Dónde está en la carrera">${c.map(x => botonNodo(x)).join('<span class="sep" aria-hidden="true">›</span>')}<span class="sep" aria-hidden="true">›</span><span class="aqui">${esc(n.name_es)}</span></nav>`).join('')}
        </section>`);
      }
    } else if (n.label === 'Course') {
      s.push(`<section class="sec">${tituloSeccion('Dónde está en la carrera')}<p class="nota">Un curso no es parte de CS2023: se ubica por los temas que enseña. Están en «Conexiones», más abajo.</p></section>`);
    }

    // Qué contiene y en qué orden aprenderlo.
    if (loc && loc.estado === 200 && P.lenteAplica('contiene', n)) {
      const partes = P.descendientes(loc.cuerpo, clave);
      const c = P.conteoPorClase({ nodes: partes });
      const orden = P.ordenDeAprendizaje(loc.cuerpo, clave);
      const cifras = [['KnowledgeUnit', 'unidades'], ['Topic', 'temas'], ['Concept', 'conceptos']]
        .filter(([k]) => (k !== 'KnowledgeUnit' || n.label === 'KnowledgeArea') && (k !== 'Topic' || n.label !== 'Topic'))
        .map(([k, t]) => `<span><b>${c[k] || 0}</b> ${t}</span>`).join('');
      let ordenHtml = '';
      const pasosMostrados = orden.pasos.map(l => (n.label === 'Topic' ? l : l.filter(x => orden.relacionados.has(x.key)))).filter(l => l.length);
      if (orden.relacionados.size) {
        ordenHtml = `<p class="grupo-titulo">En qué orden aprenderlo${n.label === 'Topic' ? '' : ' (solo los conceptos que dependen entre sí)'}</p>
          <ol class="pasos-orden">${pasosMostrados.map((l, i) => `<li><span class="num-paso">Paso ${i + 1}</span><div>${l.map(x => botonNodo(x)).join('')}</div></li>`).join('')}</ol>`;
      } else if (orden.conceptos.length) {
        ordenHtml = '<p class="nota">Sus conceptos no dependen entre sí: se pueden aprender en cualquier orden.</p>';
      }
      s.push(`<section class="${claseSeccion('contiene')}">${tituloSeccion('Qué contiene', 'contiene')}
        <p class="cifras">${cifras}</p>
        ${!c.Topic && n.label !== 'Topic' ? '<p class="nota">Esta parte de CS2023 todavía no aparece en ningún sílabo cargado.</p>' : ''}
        ${ordenHtml}</section>`);
    }

    // Qué necesitas antes.
    if (pre && pre.estado === 200) {
      const grupos = P.prerrequisitosPorProfundidad(pre.cuerpo, clave);
      let vacio = '';
      if (!grupos.length) {
        const dependen = P.conexiones(rf, clave).find(x => x.tipo === 'HAS_PREREQUISITE' && x.sentido === 'entrada');
        vacio = '<p class="nota">No necesita nada antes, según los sílabos cargados.</p>' +
          (dependen ? `<p class="grupo-titulo">Se necesita para</p>${dependen.items.map(it => `<div class="fila-item">${botonNodo(it.nodo)}</div>`).join('')}` : '');
      }
      s.push(`<section class="${claseSeccion('prerrequisitos')}">${tituloSeccion('Qué necesitas antes', 'prerrequisitos')}
        ${grupos.length ? grupos.map(g => `<div class="grupo"><p class="grupo-titulo">${g.profundidad === 1 ? 'Justo antes' : `${g.profundidad} pasos antes`}</p>
          ${g.items.map(it => `<div class="fila-item">${botonNodo(it.nodo)}${it.arista ? botonFuente(it.arista, it.nodo.name_es) : ''}</div>`).join('')}</div>`).join('') : vacio}
      </section>`);
    }

    // Cursos que conviene llevar antes: lo que pide y lo que enseña.
    if (cur && cur.estado === 200) {
      const c = P.cursosPrevios(cur.cuerpo, clave);
      s.push(`<section class="${claseSeccion('cursos')}">${tituloSeccion('Cursos que conviene llevar antes', 'cursos')}
        ${c.previos.length ? c.previos.map(p => `<div class="grupo">${botonNodo(p.curso)}<p class="grupo-titulo">porque enseña lo que este curso pide:</p>${p.evidencia.map(e => `<div class="fila-item">${botonNodo(e.nodo)}${botonFuente(e.arista, e.nodo.name_es)}</div>`).join('')}</div>`).join('')
          : '<p class="nota">Ningún otro curso cargado enseña lo que este pide.</p>'}
        <p class="grupo-titulo">Lo que pide (${c.requeridos.length})</p>
        ${c.requeridos.length ? c.requeridos.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('') : '<p class="nota">No pide conceptos previos.</p>'}
        <details ${estado.lente === 'cursos' ? 'open' : ''}><summary><span class="rel" style="--c:${L.COLOR_ARISTA.TEACHES_CONCEPT}">Lo que enseña</span><span class="cuenta">${c.ensenados}</span></summary>
          <div class="lista">${c.listaEnsenados.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}</div></details>
      </section>`);
    }

    // Es un tipo de / Tipos.
    if (esp && esp.estado === 200) {
      const e = P.especializaciones(esp.cuerpo, clave);
      if (e.todas.length) {
        s.push(`<section class="${claseSeccion('especializaciones')}">${tituloSeccion('Tipos', 'especializaciones')}
          ${e.generales.length ? `<p class="grupo-titulo">Es un tipo de</p>${e.generales.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}` : ''}
          ${e.tipos.length ? `<p class="grupo-titulo">Sus tipos</p>${e.tipos.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}` : ''}
        </section>`);
      }
    }

    // Material de estudio.
    if (rec && rec.estado === 200) {
      const lista = P.recursosDe(rec.cuerpo, clave);
      let extra = '';
      if (!lista.length && loc && loc.estado === 200) {
        const tema = (P.cadenasDeUbicacion(loc.cuerpo, clave)[0] || []).find(x => x.label === 'Topic');
        if (tema) extra = `<button class="accion" data-ir="${esc(tema.key)}" data-ir-lente="recursos">Ver el material de su tema, «${esc(tema.name_es)}»</button>`;
      }
      s.push(`<section class="${claseSeccion(lista.length ? 'recursos' : null)}">${tituloSeccion('Material de estudio', lista.length ? 'recursos' : null)}
        ${lista.length ? lista.map(x => `<div class="recurso">${enlaceDocumento(x.recurso, 'Abrir ' + x.recurso.name_es)}<span class="tipo">${esc(x.tipo ? x.tipo.name_es : 'Recurso')}</span>
          ${x.elementos.length && !(x.elementos.length === 1 && x.elementos[0].key === clave) ? `<p class="sobre">trata sobre ${x.elementos.slice(0, 4).map(el => `<button class="enlace-texto" data-ir="${esc(el.key)}">${esc(el.name_es)}</button>`).join(', ')}${x.elementos.length > 4 ? ` y ${x.elementos.length - 4} más` : ''}</p>` : ''}</div>`).join('')
          : `<p class="nota">Un ${esc(P.nombreClase(n).toLowerCase())} no tiene material propio: los sílabos describen temas.</p>${extra}`}
      </section>`);
    }

    // Conexiones: todo lo que rodea al foco, en texto. Es también la alternativa accesible al mapa.
    const grupos = P.conexiones(rf, clave);
    s.push(`<section class="${claseSeccion('vecindario')}">${tituloSeccion('Conexiones', 'vecindario')}
      ${grupos.length ? grupos.map(g => `<details ${g.items.length <= 8 ? 'open' : ''}><summary><span class="rel" style="--c:${L.COLOR_ARISTA[g.tipo]}">${esc(g.rotulo)}</span><span class="cuenta">${g.items.length}</span></summary>
        <div class="lista">${g.items.map(it => `<div class="fila-item">${botonNodo(it.nodo)}${botonFuente(it.arista, it.nodo.name_es)}</div>`).join('')}</div></details>`).join('')
        : '<p class="nota">No tiene conexiones registradas.</p>'}
      ${n.more_neighbors ? '<p class="nota">Se muestran hasta 25 conexiones directas. En el mapa, los puntos con <b>+</b> tienen más.</p>' : ''}
    </section>`);

    panel.innerHTML = s.join('');
  }

  function panelPortada() {
    const sugeridas = P.busquedasCapturadas().slice(0, 12);
    return `<header class="ficha bienvenida">
        <h2>Explora cómo se conecta la carrera</h2>
        <p class="descripcion">Este mapa une lo que dicen los sílabos de Ingeniería Informática con CS2023, el estándar internacional del currículo de computación. Sirve para ver qué necesitas saber antes de un concepto, dónde está cada tema en la carrera y con qué material estudiarlo.</p>
      </header>
      <section class="sec">${tituloSeccion('Busca por nombre')}
        <div class="sugerencias">${sugeridas.map(q => `<button class="chip-busqueda" data-buscar="${esc(q)}">${esc(q)}</button>`).join('')}</div>
        <p class="nota">Estas búsquedas tienen respuesta real del sistema. Cualquier otra palabra se busca de forma aproximada en esta maqueta.</p>
      </section>
      <section class="sec">${tituloSeccion('O sigue el recorrido sugerido')}
        <p class="nota">Seis pasos con un ejemplo real: cada uno muestra una pregunta que el mapa responde.</p>
        <ol class="pasos-recorrido">${PASOS.map((p, i) => `<li><button data-paso="${i}"><span class="num">${i + 1}</span><span>${esc(p.t)}</span></button></li>`).join('')}</ol>
      </section>
      <section class="sec">${tituloSeccion('Cómo leer el mapa')}
        <div class="capa-explica capa-reference">${iconoCapa('reference', 24)}<p><b>Hexágono: viene de CS2023.</b> Las áreas y unidades del estándar internacional (ACM/IEEE).</p></div>
        <div class="capa-explica capa-institutional">${iconoCapa('institutional', 24)}<p><b>Círculo relleno: viene de un sílabo PUCP.</b> Los temas, conceptos y cursos; cada uno enlaza a su PDF.</p></div>
        <p class="nota">Siempre hay un elemento en foco, al centro. Sobre el mapa eliges qué quieres saber de él, y una frase te dice qué estás viendo.</p>
      </section>`;
  }

  // ------------------------------------------------------------------ buscador

  const buscador = $('#buscar');
  const lista = $('#resultados');
  let indiceActivo = -1;
  let resultados = [];

  async function buscar(q) {
    q = q.trim();
    if (!q) { pintarSugerencias(); return; }
    const r = await P.api('/api/search', { q });
    if (buscador.value.trim() !== q) return;
    resultados = r.cuerpo.nodes;
    indiceActivo = resultados.length ? 0 : -1;
    const cab = r.simulado
      ? `<p class="res-cab">Búsqueda aproximada <span class="etiqueta-simulado">simulada</span>: en esta maqueta se filtra sobre los nombres reales.</p>`
      : `<p class="res-cab">${plural(resultados.length, 'resultado', 'resultados')}</p>`;
    if (!resultados.length) {
      lista.innerHTML = cab + `<div class="res-vacio"><b>Ningún sílabo cargado trata «${esc(q)}».</b><p>Prueba con otra palabra, o recorre las áreas de la carrera.</p>
        <div class="sugerencias"><button class="chip-busqueda destacado" data-portada>Ver las áreas</button>${['redes', 'lógica', 'puntero', 'ethernet'].map(s => `<button class="chip-busqueda" data-buscar="${s}">${s}</button>`).join('')}</div></div>`;
    } else {
      lista.innerHTML = cab + resultados.map((n, i) => `<button class="res${i === indiceActivo ? ' activo' : ''}" role="option" id="res-${i}" aria-selected="${i === indiceActivo}" data-ir="${esc(n.key)}" style="--c:${P.CLASES[n.label].color}">
        <span class="marca capa-${n.layer}">${iconoCapa(n.layer, 13)}</span><span class="nombre">${esc(n.name_es)}${n.course_code ? ` <em>${esc(n.course_code)}</em>` : ''}</span>${chipClase(n)}</button>`).join('');
    }
    lista.hidden = false;
    buscador.setAttribute('aria-expanded', 'true');
  }

  function pintarSugerencias() {
    resultados = []; indiceActivo = -1;
    lista.innerHTML = `<p class="res-cab">Búsquedas de ejemplo, con respuesta real</p><div class="sugerencias">${P.busquedasCapturadas().map(q => `<button class="chip-busqueda" data-buscar="${esc(q)}">${esc(q)}</button>`).join('')}</div>`;
    lista.hidden = false;
    buscador.setAttribute('aria-expanded', 'true');
  }

  function cerrarResultados() { lista.hidden = true; buscador.setAttribute('aria-expanded', 'false'); }

  buscador.addEventListener('focus', () => buscar(buscador.value));
  buscador.addEventListener('input', () => buscar(buscador.value));
  buscador.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      if (!resultados.length) return;
      ev.preventDefault();
      indiceActivo = (indiceActivo + (ev.key === 'ArrowDown' ? 1 : -1) + resultados.length) % resultados.length;
      lista.querySelectorAll('.res').forEach((b, i) => { b.classList.toggle('activo', i === indiceActivo); b.setAttribute('aria-selected', String(i === indiceActivo)); });
      buscador.setAttribute('aria-activedescendant', 'res-' + indiceActivo);
    } else if (ev.key === 'Enter' && indiceActivo >= 0) {
      ev.preventDefault();
      const n = resultados[indiceActivo];
      cerrarResultados(); buscador.blur();
      irA(n.key);
    } else if (ev.key === 'Escape') { cerrarResultados(); buscador.blur(); }
  });
  document.addEventListener('keydown', ev => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); buscador.focus(); buscador.select(); }
    if (ev.altKey && ev.key === 'ArrowLeft') { ev.preventDefault(); atras(); }
  });
  document.addEventListener('click', ev => {
    if (!ev.target.closest('.buscador')) cerrarResultados();
  });

  // ------------------------------------------------------------------ delegación de clics

  document.addEventListener('click', ev => {
    const t = ev.target.closest('[data-ir],[data-lente],[data-buscar],[data-arista],[data-cerrar-arista],[data-grano],[data-paso],[data-portada],[data-porque],[data-cerrar-porque],[data-cerrar-recorrido],#limpiar');
    if (!t) return;
    if (t.id === 'limpiar') { limpiar(); return; }
    if (t.dataset.buscar !== undefined) {
      ev.preventDefault();
      buscador.value = t.dataset.buscar;
      buscador.focus();
      buscar(t.dataset.buscar);
      return;
    }
    if (t.dataset.portada !== undefined) { cerrarResultados(); buscador.value = ''; mostrarPortada(); return; }
    if (t.dataset.ir) {
      ev.preventDefault();
      cerrarResultados();
      const lente = t.dataset.irLente;
      if (t.dataset.ir === estado.foco && lente) { aplicarLente(lente); return; }
      if (t.dataset.ir !== estado.foco) irA(t.dataset.ir, { lente, rastro: t.dataset.rastro ? false : undefined });
      return;
    }
    if (t.dataset.lente) {
      if (t.disabled) return;
      aplicarLente(t.dataset.lente);
      return;
    }
    if (t.dataset.grano) {
      estado.grano = t.dataset.grano;
      aplicarLente('ruta');
      return;
    }
    if (t.dataset.porque) { abrirPorque(t.dataset.porque); return; }
    if (t.dataset.cerrarPorque !== undefined) { estado.porque = null; lienzo.seleccionar(null); pintarFranja(); pintarPanel(); return; }
    if (t.dataset.arista) { seleccionarArista(t.dataset.arista); return; }
    if (t.dataset.cerrarArista !== undefined) { estado.aristaSel = null; lienzo.seleccionar(null); pintarPanel(); return; }
    if (t.dataset.cerrarRecorrido !== undefined) { pasoActual = -1; pintarRecorrido(); encuadrarLuego(estado.turno); return; }
    if (t.dataset.paso !== undefined) { hacerPaso(Number(t.dataset.paso)); }
  });

  function atras() {
    const i = estado.rastro.findIndex(x => x.key === estado.foco);
    if (i > 0) irA(estado.rastro[i - 1].key, { rastro: false });
  }

  $('#atras').addEventListener('click', atras);
  $('#inicio').addEventListener('click', mostrarPortada);
  $('#marca').addEventListener('click', mostrarPortada);
  $('#ver-procedencia').addEventListener('change', ev => {
    estado.verProcedencia = ev.target.checked;
    lienzo.configurar({ verProcedencia: estado.verProcedencia });
    lienzo.dibujar();
    encuadrarLuego(estado.turno);
  });
  $('#zoom-mas').addEventListener('click', () => lienzo.zoomPor(1.3));
  $('#zoom-menos').addEventListener('click', () => lienzo.zoomPor(1 / 1.3));
  $('#encuadrar').addEventListener('click', () => { medirMargen(); lienzo.encuadrar(null); });
  $('#leyenda-boton').addEventListener('click', () => {
    const l = $('#leyenda');
    l.hidden = !l.hidden;
    $('#leyenda-boton').setAttribute('aria-expanded', String(!l.hidden));
  });
  let temporizadorTam = null;
  window.addEventListener('resize', () => {
    clearTimeout(temporizadorTam);
    temporizadorTam = setTimeout(() => { medirMargen(); lienzo.encuadrar(null, 300); }, 180);
  });

  // ------------------------------------------------------------------ recorrido sugerido (común a las tres propuestas)

  const PASOS = [
    { t: 'Busca «lógica» y abre el tema «Lógica proposicional».',
      hacer: async () => { buscador.value = 'lógica'; await buscar('lógica'); cerrarResultados(); await irA(CLAVES.logica, { lente: 'vecindario' }); } },
    { t: 'Mira qué contiene, en qué orden conviene aprenderlo y su material de estudio.',
      hacer: () => irA(CLAVES.logica, { lente: 'contiene' }) },
    { t: 'Abre «Contradicción»: ¿qué necesitas saber antes?',
      hacer: () => irA(CLAVES.contradiccion, { lente: 'prerrequisitos' }) },
    { t: '¿De dónde sale que «Contradicción» requiere «Tabla de verdad»? Ver la fuente.',
      hacer: async () => {
        if (estado.foco !== CLAVES.contradiccion || estado.lente !== 'prerrequisitos') await irA(CLAVES.contradiccion, { lente: 'prerrequisitos' });
        seleccionarArista(`HAS_PREREQUISITE|${CLAVES.contradiccion}|${CLAVES.tablaVerdad}`);
      } },
    { t: 'El camino hasta «Entrada y salida de datos desde archivos», visto por cursos.',
      hacer: () => irA(CLAVES.archivos, { lente: 'ruta', grano: 'course' }) },
    { t: '«Técnicas de Programación»: qué pide y qué curso conviene llevar antes.',
      hacer: () => irA(CLAVES.inf144, { lente: 'cursos' }) },
  ];

  // En el inicio, la lista de pasos está en el panel. Al seguir uno, queda una barra de un renglón sobre el rastro.
  let pasoActual = -1;
  function pintarRecorrido() {
    const caja = $('#recorrido');
    if (pasoActual < 0 || !estado.nodoFoco) { caja.hidden = true; caja.innerHTML = ''; return; }
    const p = PASOS[pasoActual];
    caja.hidden = false;
    caja.innerHTML = `<span class="num">${pasoActual + 1}</span>
      <p><span class="recorrido-rotulo">Recorrido sugerido · paso ${pasoActual + 1} de ${PASOS.length}</span>${esc(p.t)}</p>
      <div class="nav-pasos">
        <button data-paso="${Math.max(0, pasoActual - 1)}" ${pasoActual === 0 ? 'disabled' : ''} aria-label="Paso anterior" title="Paso anterior">${ICONO.antes}</button>
        <button class="siguiente" data-paso="${Math.min(PASOS.length - 1, pasoActual + 1)}" ${pasoActual === PASOS.length - 1 ? 'disabled' : ''}>Siguiente${ICONO.despues}</button>
        <button data-cerrar-recorrido aria-label="Salir del recorrido" title="Salir del recorrido">${ICONO.cerrar}</button>
      </div>`;
  }
  function hacerPaso(i) {
    pintarRecorrido();
    pasoActual = i;
    return PASOS[i].hacer();
  }

  // ------------------------------------------------------------------ arranque

  if (!window.IEKG_DATOS) {
    document.body.insertAdjacentHTML('afterbegin', '<p class="error-datos">No se cargaron los datos (<code>../datos/datos.js</code>). Abre este archivo desde su carpeta, sin moverlo.</p>');
    return;
  }
  if (!window.d3) {
    document.body.insertAdjacentHTML('afterbegin', '<p class="error-datos">No se pudo cargar la librería del mapa. La maqueta necesita conexión a internet.</p>');
    return;
  }
  // Enlace directo: #paso=N abre un paso del recorrido (útil para capturas).
  mostrarPortada().then(() => {
    const m = /paso=(\d+)/.exec(location.hash);
    if (m && PASOS[Number(m[1]) - 1]) setTimeout(() => hacerPaso(Number(m[1]) - 1), 300);
  });
})();
