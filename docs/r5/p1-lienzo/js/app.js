/* Constelación (P1) · estado, panel del foco, buscador, lentes, rastro, trazabilidad y recorrido. */
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

  // Orden de las lentes en el riel.
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
    aristaSel: null,
    turno: 0,           // descarta respuestas viejas si el estudiante hace clic rápido
  };

  // ------------------------------------------------------------------ utilidades de presentación

  function esc(t) {
    return String(t === undefined || t === null ? '' : t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /** Insignia de trazabilidad: invisible salvo con «Ver trazabilidad» activo. */
  function traza(codigos, detalle) {
    return `<span class="traza"${detalle ? ` title="${esc(detalle)}"` : ''}>${esc(codigos)}</span>`;
  }

  const ARTICULO = { Área: 'un área', Unidad: 'una unidad', Tema: 'un tema', Concepto: 'un concepto', Curso: 'un curso',
    Sílabo: 'un sílabo', Documento: 'un documento', 'Tipo de recurso': 'un tipo de recurso' };
  function conArticulo(n) { return ARTICULO[P.nombreClase(n)] || P.nombreClase(n).toLowerCase(); }
  function plural(n, uno, varios) { return `${n} ${n === 1 ? uno : varios}`; }

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
    return `<a class="enlace-doc capa-${doc.layer}" href="${esc(doc.locator)}" target="_blank" rel="noopener">` +
      `<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 1.5h6l4 4v9H3z M9 1.5v4h4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>` +
      `<span>${esc(texto || ('Ver fuente · ' + (ref ? 'CS2023' : doc.name_es)))}</span><span class="sale" aria-hidden="true">↗</span>` +
      `<span class="sr">(abre ${ref ? 'CS2023 en la biblioteca digital de ACM' : 'el PDF del sílabo'} en una pestaña nueva)</span></a>`;
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
  });

  function infoNodo(n) {
    return `<strong>${esc(n.name_es)}</strong>${n.name_en ? `<span class="en" lang="en">${esc(n.name_en)}</span>` : ''}` +
      `<span class="linea">${chipClase(n)} ${iconoCapa(n.layer, 11)} ${esc(P.CAPAS[n.layer].nombre)}</span>` +
      (estado.foco === null ? '<span class="pista">Clic: empezar aquí</span>' :
        (n.key === estado.foco ? '<span class="pista">En foco</span>' :
          `<span class="pista">Clic: poner en foco${n.more_neighbors && !n.expandido ? ' · <b>+</b>: ver más conexiones' : ''}</span>`));
  }

  function infoArista(a) {
    const cont = lienzo.contenido();
    const s = P.nodoPorClave(cont, a.source), t = P.nodoPorClave(cont, a.target);
    const doc = P.documentoDeArista(cont, a);
    return `<span class="linea"><b>${esc(s ? s.name_es : '')}</b> ${esc(P.RELACIONES[a.type].frase)} <b>${esc(t ? t.name_es : '')}</b></span>` +
      `<span class="pista">${doc ? 'Fuente: ' + esc(doc.layer === 'reference' ? 'CS2023' : doc.name_es) : 'Sin fuente en la respuesta'} · clic: ver la fuente</span>`;
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

  // ------------------------------------------------------------------ portada (ruta nueva, simulada)

  async function mostrarPortada() {
    estado.turno++;
    estado.foco = null; estado.nodoFoco = null; estado.respFoco = null; estado.respLente = null;
    estado.aristaSel = null; estado.lente = 'vecindario';
    const r = await P.apiPortada();
    const lista = r.cuerpo.areas.map(a => ({
      key: a.key, label: 'KnowledgeArea', name_es: a.name_es, name_en: a.name_en, layer: 'reference',
      concepts: a.concepts, sub: a.concepts > 0 ? `${plural(a.topics, 'tema', 'temas')} · ${a.concepts} conceptos` : 'solo en CS2023',
    })).concat(r.cuerpo.courses.map(c => ({
      key: c.key, label: 'Course', name_es: c.name_es, layer: 'institutional', course_code: c.code, sub: 'curso con sílabo',
    })));
    lienzo.mostrarPortada(lista);
    lienzo.dibujar();
    setTimeout(() => lienzo.encuadrar(null, 900), 50);
    $('#escena').classList.add('en-portada');
    pintarRiel();
    pintarBarraLente();
    pintarFranja();
    pintarRastro();
    pintarPanel();
  }

  // ------------------------------------------------------------------ foco, lentes y expansión

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
      if (lente !== 'vecindario') aviso(`«${P.LENTES[lente].nombre}» no aplica a ${conArticulo(estado.nodoFoco)}: vuelves al vecindario.`);
      lente = 'vecindario';
    }
    await aplicarLente(lente, turno);
    pintarRastro();
  }

  async function aplicarLente(lente, turno) {
    turno = turno || ++estado.turno;
    estado.lente = lente;
    estado.respLente = null;
    if (lente === 'vecindario' || !estado.foco) {
      lienzo.configurar({ resaltados: null, disposicion: null, verProcedencia: estado.verProcedencia });
      lienzo.dibujar();
      setTimeout(() => { if (turno === estado.turno) lienzo.encuadrar(estado.foco ? lienzo.cercanas(1) : null, 800); }, 120);
    } else {
      const def = P.LENTES[lente];
      const params = { key: estado.foco };
      if (lente === 'ruta') params.grain = estado.grano;
      const r = await P.api(def.ruta, params);
      if (turno !== estado.turno) return;
      if (r.estado !== 200) { aviso('Esta vista no tiene datos para el elemento en foco.'); return aplicarLente('vecindario'); }
      estado.respLente = r.cuerpo;
      lienzo.agregar(r.cuerpo, estado.foco);
      const disp = L.disponer(lente, r.cuerpo, estado.foco, estado.grano);
      const resaltados = disp && disp.resaltar ? new Set(disp.resaltar) : new Set(r.cuerpo.nodes.map(n => n.key));
      resaltados.add(estado.foco);
      lienzo.configurar({ resaltados, disposicion: disp, verProcedencia: estado.verProcedencia });
      lienzo.dibujar();
      const claves = disp && disp.objetivos.size ? [...disp.objetivos.keys()] : [...resaltados];
      setTimeout(() => { if (turno === estado.turno) lienzo.encuadrar(claves, 850); }, 60);
    }
    pintarRiel();
    pintarBarraLente();
    pintarFranja();
    pintarPanel();
  }

  async function expandir(clave) {
    const r = await P.api('/api/nodes', { key: clave });
    if (r.estado !== 200) return;
    const nombre = r.cuerpo.nodes[0].name_es;
    lienzo.agregar(r.cuerpo, clave);
    lienzo.marcarExpandido(clave);
    if (estado.lente !== 'vecindario') {
      aviso(`Se agregaron las conexiones de «${nombre}». Vuelves al vecindario para verlas junto al foco.`);
      await aplicarLente('vecindario');
    } else {
      lienzo.dibujar();
      setTimeout(() => lienzo.encuadrar(null, 700), 700);
      aviso(`Se agregaron las conexiones de «${nombre}». El foco no cambió.`);
    }
  }

  function limpiar() {
    if (!estado.foco || !estado.respFoco) return;
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

  // ------------------------------------------------------------------ riel de lentes

  const ICONOS_LENTE = {
    vecindario: '<circle cx="12" cy="12" r="3.2"/><circle cx="4.5" cy="6" r="1.8"/><circle cx="19.5" cy="6" r="1.8"/><circle cx="5" cy="18.5" r="1.8"/><circle cx="19" cy="18.5" r="1.8"/><path d="M9.4 10.4L6 7.2M14.6 10.4L18 7.2M9.6 13.8L6.4 17.2M14.4 13.8L17.6 17.2"/>',
    prerrequisitos: '<circle cx="4.5" cy="12" r="2"/><circle cx="12" cy="7" r="2"/><circle cx="12" cy="17" r="2"/><circle cx="19.5" cy="12" r="2.6"/><path d="M6.3 11L10.2 8M6.3 13L10.2 16M13.9 7.9L17.2 10.7M13.9 16.1L17.2 13.3"/>',
    ruta: '<circle cx="4.5" cy="18" r="2"/><circle cx="12" cy="9" r="2"/><circle cx="19.5" cy="15" r="2.6"/><path d="M6 16.4l4.6-5.6M13.8 10.3l3.7 3"/>',
    cursos: '<rect x="2.5" y="5" width="7" height="14" rx="1.5"/><rect x="14.5" y="5" width="7" height="14" rx="1.5"/><path d="M9.5 12h5M12.5 10l2 2-2 2"/>',
    ubicacion: '<path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    contiene: '<circle cx="12" cy="12" r="2.2"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="9.8" stroke-dasharray="2 2.5"/>',
    recursos: '<path d="M6 2.8h8l4 4v14.4H6z M14 2.8v4h4 M9 12h6M9 15.5h6M9 9h3"/>',
    especializaciones: '<circle cx="12" cy="5" r="2.4"/><circle cx="5" cy="18" r="2"/><circle cx="12" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="M12 7.4V16M10.6 6.9L6 16.2M13.4 6.9L18 16.2"/>',
  };

  function pintarRiel() {
    const n = estado.nodoFoco;
    $('#lentes').innerHTML = ORDEN_LENTES.map(id => {
      const def = P.LENTES[id];
      const aplica = !!n && P.lenteAplica(id, n);
      const motivo = !n ? 'Elige primero un elemento en el mapa' : (aplica ? def.ayuda : `No aplica a ${conArticulo(n)}`);
      return `<button class="lente${estado.lente === id && n ? ' activa' : ''}" data-lente="${id}" ${aplica ? '' : 'disabled'} ` +
        `aria-pressed="${estado.lente === id && !!n}" title="${esc(motivo)}">` +
        `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONOS_LENTE[id]}</svg>` +
        `<span class="nombre">${esc(def.corto)}</span>${traza(def.traza.split(' · ')[0])}</button>`;
    }).join('');
  }

  // ------------------------------------------------------------------ barra de la lente y franja de ruta

  function cadenaTexto(resp, clave) {
    const c = P.cadenasDeUbicacion(resp, clave)[0] || [];
    return c.map(x => `<b>${esc(x.name_es)}</b>`).join(' › ');
  }

  function resumenLente() {
    const n = estado.nodoFoco, r = estado.respLente;
    if (!n) return '';
    const nombre = `<b>${esc(n.name_es)}</b>`;
    switch (estado.lente) {
      case 'vecindario':
        return `${nombre} y lo que lo rodea. Haz clic en un punto para moverte hacia él; el <b>+</b> muestra más conexiones sin perder el foco.`;
      case 'prerrequisitos': {
        const g = P.prerrequisitosPorProfundidad(r, estado.foco);
        const total = g.reduce((s, x) => s + x.items.length, 0);
        if (!total) {
          const dependen = P.conexiones(estado.respFoco, estado.foco).find(x => x.tipo === 'HAS_PREREQUISITE' && x.sentido === 'entrada');
          return `${nombre} no necesita nada antes, según los sílabos cargados.` +
            (dependen ? ` Se necesita para: ${dependen.items.map(i => `<b>${esc(i.nodo.name_es)}</b>`).join(', ')}.` : '');
        }
        const max = g[g.length - 1].profundidad;
        return `Para aprender ${nombre} conviene saber antes ${plural(total, 'concepto', 'conceptos')}, ${max > 1 ? `hasta <b>a ${max} pasos</b>` : 'todos <b>directos</b>'}. Se lee de izquierda a derecha.`;
      }
      case 'ruta': {
        const s = P.resumenRuta(r, estado.foco, estado.grano);
        const g = P.GRANOS[estado.grano];
        if (s.vacia) {
          return n.label === 'Course'
            ? `El camino hasta un curso sale vacío: lo que ${nombre} pide se aprende dentro del mismo curso. Para saber qué curso conviene llevar antes, abre <button class="enlace-lente" data-lente="cursos">Cursos que conviene llevar antes</button>.`
            : `${nombre} no tiene nada que aprender antes, visto por ${g.nombre}.`;
        }
        return `Para llegar a ${nombre} conviene pasar antes por <b>${plural(s.estaciones.length, g.nombre, g.plural)}</b>, por ${plural(s.prerrequisitos.length, 'concepto que lo justifica', 'conceptos que lo justifican')}.`;
      }
      case 'cursos': {
        const c = P.cursosPrevios(r, estado.foco);
        if (!c.previos.length) return `${nombre} enseña ${c.ensenados} conceptos y no pide ninguno que enseñe otro curso cargado.`;
        return `${nombre} pide ${plural(c.requeridos.length, 'concepto', 'conceptos')} que enseña ${c.previos.map(p => `<b>${esc(p.curso.name_es)}</b>`).join(' y ')}: conviene llevarlo antes. En arco, los ${c.ensenados} que enseña.`;
      }
      case 'ubicacion':
        return `${nombre} está en ${cadenaTexto(r, estado.foco) || 'el nivel más alto'}.`;
      case 'contiene': {
        if (n.label === 'Topic') {
          const o = P.ordenDeAprendizaje(r, estado.foco);
          return `${nombre} tiene ${plural(o.conceptos.length, 'concepto', 'conceptos')}. Las columnas dicen en qué orden aprenderlos: cada paso usa lo del anterior.`;
        }
        const c = P.conteoPorClase({ nodes: P.descendientes(r, estado.foco) });
        const partes = [['KnowledgeUnit', 'unidad', 'unidades'], ['Topic', 'tema', 'temas'], ['Concept', 'concepto', 'conceptos']]
          .filter(([k]) => c[k]).map(([k, s, p]) => `<b>${plural(c[k], s, p)}</b>`);
        if (!c.Topic) return `${nombre} contiene ${partes.join(', ') || 'nada todavía'}. Ningún sílabo cargado trata esta área por ahora.`;
        return `${nombre} contiene ${partes.join(', ')}.` + ((c.Concept || 0) > 40 ? ' Acerca el zoom para leer el anillo exterior.' : '');
      }
      case 'recursos': {
        const rec = P.recursosDe(r, estado.foco);
        if (!rec.length) return `Un concepto no tiene material propio: los sílabos describen temas. En el panel tienes el de su tema.`;
        return `${plural(rec.length, 'sílabo trata', 'sílabos tratan')} sobre ${nombre} o sus partes.`;
      }
      case 'especializaciones': {
        const e = P.especializaciones(r, estado.foco);
        if (!e.todas.length) return `${nombre} no es un tipo de otro concepto ni tiene tipos. Hay pocos casos en los sílabos cargados: prueba con «ethernet».`;
        return `${nombre}${e.generales.length ? ` es un tipo de <b>${esc(e.generales.map(x => x.name_es).join(', '))}</b>` : ''}${e.generales.length && e.tipos.length ? ' y' : ''}${e.tipos.length ? ` tiene ${plural(e.tipos.length, 'tipo', 'tipos')}` : ''}.`;
      }
      default: return '';
    }
  }

  function pintarBarraLente() {
    const barra = $('#barra-lente');
    if (!estado.nodoFoco) { barra.hidden = true; return; }
    barra.hidden = false;
    const def = P.LENTES[estado.lente];
    $('#lente-titulo').innerHTML = `${esc(def.nombre)} ${traza(def.traza, def.ruta)}`;
    $('#lente-resumen').innerHTML = resumenLente();
    const granos = $('#granos');
    granos.hidden = estado.lente !== 'ruta';
    granos.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.grano === estado.grano)));
    $('#ver-procedencia').checked = estado.verProcedencia;
  }

  function pintarFranja() {
    const f = $('#franja');
    const r = estado.respLente;
    let html = '';
    if (estado.lente === 'ruta' && r) {
      const s = P.resumenRuta(r, estado.foco, estado.grano);
      if (!s.vacia) {
        const pasos = s.estaciones.map(n => `<button class="parada" data-ir="${esc(n.key)}" style="--c:${P.CLASES[n.label].color}">${iconoCapa(n.layer, 11)}<span>${esc(n.name_es)}</span></button>`);
        pasos.push(`<span class="parada destino" style="--c:${P.CLASES[s.objetivo.label].color}">${iconoCapa(s.objetivo.layer, 11)}<span>${esc(s.objetivo.name_es)}</span></span>`);
        html = `<span class="franja-titulo">Camino hasta aquí · por ${esc(P.GRANOS[estado.grano].plural)}</span><div class="paradas">${pasos.join('<span class="flecha" aria-hidden="true"></span>')}</div>`;
      }
    } else if (estado.lente === 'cursos' && r) {
      const c = P.cursosPrevios(r, estado.foco);
      if (c.previos.length) {
        const pasos = c.previos.map(p => `<button class="parada" data-ir="${esc(p.curso.key)}" style="--c:${P.CLASES.Course.color}">${iconoCapa('institutional', 11)}<span>${esc(p.curso.name_es)} <em>${esc(p.curso.course_code || '')}</em></span></button>`);
        pasos.push(`<span class="parada destino" style="--c:${P.CLASES.Course.color}">${iconoCapa('institutional', 11)}<span>${esc(estado.nodoFoco.name_es)} <em>${esc(estado.nodoFoco.course_code || '')}</em></span></span>`);
        html = `<span class="franja-titulo">Curso que conviene llevar antes</span><div class="paradas">${pasos.join('<span class="flecha" aria-hidden="true"></span>')}</div>`;
      }
    }
    f.innerHTML = html;
    f.hidden = !html;
  }

  // ------------------------------------------------------------------ rastro

  function pintarRastro() {
    const el = $('#rastro-lista');
    if (!estado.rastro.length) { el.innerHTML = '<span class="vacio">Lo que visites aparecerá aquí, para volver.</span>'; }
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

  function tituloSeccion(texto, lente, extra) {
    const def = lente ? P.LENTES[lente] : null;
    return `<h3 class="sec-titulo"><span>${esc(texto)} ${def ? traza(def.traza, def.ruta) : (extra || '')}</span>` +
      `${lente && estado.lente !== lente && P.lenteAplica(lente, estado.nodoFoco) ? `<button class="enlace-lente" data-lente="${lente}">Ver en el mapa</button>` : ''}</h3>`;
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

    // Cabecera.
    s.push(`<header class="ficha" style="--c:${P.CLASES[n.label].color}">
      <div class="ficha-chips">${chipClase(n)} ${insigniaCapa(n)}</div>
      <h2>${esc(n.name_es)}</h2>
      ${n.name_en ? `<p class="en" lang="en">${esc(n.name_en)}</p>` : ''}
      ${n.course_code ? `<p class="codigo">Código ${esc(n.course_code)}</p>` : ''}
      ${n.description ? `<p class="descripcion">${esc(n.description)}</p>` : ''}
    </header>`);

    // Relación seleccionada: su fuente.
    if (estado.aristaSel) {
      const a = lienzo.arista(estado.aristaSel);
      if (a) {
        const cont = lienzo.contenido();
        const o = P.nodoPorClave(cont, a.source), d = P.nodoPorClave(cont, a.target);
        const doc = P.documentoDeArista(cont, a);
        s.push(`<section class="tarjeta-arista" id="tarjeta-arista" aria-live="polite">
          <div class="sec-titulo"><span>Relación seleccionada ${traza('CU-10 · RF-21 · ' + a.type)}</span><button class="cerrar-mini" data-cerrar-arista aria-label="Cerrar">×</button></div>
          <p class="afirmacion">${o ? botonNodo(o) : ''}<span class="rel" style="--c:${L.COLOR_ARISTA[a.type]}">${esc(P.RELACIONES[a.type].frase)}</span>${d ? botonNodo(d) : ''}</p>
          <div class="procedencia">${doc ? `<span class="rotulo">${a.provenance ? 'Lo dice' : 'Lo define'}</span>${enlaceDocumento(doc)}` : '<span class="rotulo">Sin fuente en la respuesta</span>'}</div>
        </section>`);
      }
    }

    // Fuente del foco.
    const fuentes = n.label === 'LearningResource' ? [n] : P.procedenciaDe(rf, clave);
    s.push(`<section class="sec sec-procedencia">
      <h3 class="sec-titulo"><span>${n.label === 'LearningResource' ? 'Documento' : 'Fuente'} ${traza('CU-10 · RF-21')}</span></h3>
      ${fuentes.length ? fuentes.map(f => `<div class="procedencia">${enlaceDocumento(f, n.label === 'LearningResource' ? 'Abrir ' + f.name_es : null)}</div>`).join('') : '<p class="nota">No se registró de dónde sale.</p>'}
      <p class="nota">${n.layer === 'reference' ? 'Viene de CS2023, el estándar internacional del currículo de computación (ACM/IEEE).' : 'Viene del sílabo del curso. El PDF se abre cuando el sistema está en marcha.'}</p>
    </section>`);

    // Dónde está en la carrera.
    if (loc && loc.estado === 200 && P.lenteAplica('ubicacion', n)) {
      const cadenas = P.cadenasDeUbicacion(loc.cuerpo, clave);
      if (cadenas.length) {
        s.push(`<section class="sec">${tituloSeccion('Dónde está en la carrera', 'ubicacion')}
          ${cadenas.map(c => `<nav class="migas" aria-label="Dónde está en la carrera">${c.map(x => botonNodo(x)).join('<span class="sep" aria-hidden="true">›</span>')}<span class="sep" aria-hidden="true">›</span><span class="aqui">${esc(n.name_es)}</span></nav>`).join('')}
        </section>`);
      }
    } else if (n.label === 'Course') {
      s.push(`<section class="sec">${tituloSeccion('Dónde está en la carrera', null, traza('CU-5 · PC3'))}<p class="nota">Un curso no es parte de CS2023: se ubica por los temas que enseña. Los ves en «Conexiones».</p></section>`);
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
      s.push(`<section class="sec">${tituloSeccion('Qué contiene', 'contiene')}
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
      s.push(`<section class="sec">${tituloSeccion('Qué necesitas antes', grupos.length ? 'prerrequisitos' : null, grupos.length ? '' : traza(P.LENTES.prerrequisitos.traza))}
        ${grupos.length ? grupos.map(g => `<div class="grupo"><p class="grupo-titulo">${g.profundidad === 1 ? 'Directo' : `A ${g.profundidad} pasos`}</p>
          ${g.items.map(it => `<div class="fila-item">${botonNodo(it.nodo)}${it.arista ? `<button class="mini-arista" data-arista="${esc(it.arista.type + '|' + it.arista.source + '|' + it.arista.target)}" title="De dónde sale esta relación">Ver fuente</button>` : ''}</div>`).join('')}</div>`).join('') : vacio}
      </section>`);
    }

    // Cursos que conviene llevar antes: lo que pide y lo que enseña.
    if (cur && cur.estado === 200) {
      const c = P.cursosPrevios(cur.cuerpo, clave);
      s.push(`<section class="sec">${tituloSeccion('Cursos que conviene llevar antes', 'cursos')}
        ${c.previos.length ? c.previos.map(p => `<div class="grupo">${botonNodo(p.curso)}<p class="grupo-titulo">porque enseña lo que este curso pide:</p>${p.evidencia.map(e => `<div class="fila-item">${botonNodo(e.nodo)}<button class="mini-arista" data-arista="${esc(e.arista.type + '|' + e.arista.source + '|' + e.arista.target)}" title="De dónde sale esta relación">Ver fuente</button></div>`).join('')}</div>`).join('')
          : '<p class="nota">Ningún otro curso cargado enseña lo que este pide.</p>'}
        <p class="grupo-titulo">Lo que pide (${c.requeridos.length})</p>
        ${c.requeridos.length ? c.requeridos.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('') : '<p class="nota">No pide conceptos previos.</p>'}
        <details><summary><span class="rel" style="--c:${L.COLOR_ARISTA.TEACHES_CONCEPT}">Lo que enseña</span><span class="cuenta">${c.ensenados}</span></summary>
          <div class="lista">${c.listaEnsenados.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}</div></details>
      </section>`);
    }

    // Es un tipo de / Tipos.
    if (esp && esp.estado === 200) {
      const e = P.especializaciones(esp.cuerpo, clave);
      if (e.todas.length) {
        s.push(`<section class="sec">${tituloSeccion('Tipos', 'especializaciones')}
          ${e.generales.length ? `<p class="grupo-titulo">Es un tipo de</p>${e.generales.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}` : ''}
          ${e.tipos.length ? `<p class="grupo-titulo">Tipos</p>${e.tipos.map(x => `<div class="fila-item">${botonNodo(x)}</div>`).join('')}` : ''}
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
      s.push(`<section class="sec">${tituloSeccion('Material de estudio', lista.length ? 'recursos' : null, lista.length ? '' : traza(P.LENTES.recursos.traza))}
        ${lista.length ? lista.map(x => `<div class="recurso">${enlaceDocumento(x.recurso, 'Abrir ' + x.recurso.name_es)}<span class="tipo">${esc(x.tipo ? x.tipo.name_es : 'Recurso')}</span>
          ${x.elementos.length && !(x.elementos.length === 1 && x.elementos[0].key === clave) ? `<p class="sobre">trata sobre ${x.elementos.slice(0, 4).map(el => `<button class="enlace-texto" data-ir="${esc(el.key)}">${esc(el.name_es)}</button>`).join(', ')}${x.elementos.length > 4 ? ` y ${x.elementos.length - 4} más` : ''}</p>` : ''}</div>`).join('')
          : `<p class="nota">Un ${esc(P.nombreClase(n).toLowerCase())} no tiene material propio: los sílabos describen temas.</p>${extra}`}
      </section>`);
    }

    // Conexiones: alternativa en texto al mapa.
    const grupos = P.conexiones(rf, clave);
    s.push(`<section class="sec"><h3 class="sec-titulo"><span>Conexiones ${traza(P.LENTES.vecindario.traza, '/api/nodes')}</span><span class="cuenta">${grupos.reduce((t, g) => t + g.items.length, 0)}</span></h3>
      ${grupos.length ? grupos.map(g => `<details ${g.items.length <= 8 ? 'open' : ''}><summary><span class="rel" style="--c:${L.COLOR_ARISTA[g.tipo]}">${esc(g.rotulo)}</span><span class="cuenta">${g.items.length}</span></summary>
        <div class="lista">${g.items.map(it => `<div class="fila-item">${botonNodo(it.nodo)}<button class="mini-arista" data-arista="${esc(it.arista.type + '|' + it.arista.source + '|' + it.arista.target)}" title="De dónde sale esta relación" aria-label="Ver la fuente de la relación con ${esc(it.nodo.name_es)}">Ver fuente</button></div>`).join('')}</div></details>`).join('')
        : '<p class="nota">No tiene conexiones registradas.</p>'}
      ${n.more_neighbors ? '<p class="nota">Se muestran hasta 25 conexiones directas. Los puntos con <b>+</b> tienen más: haz clic en el + para verlas.</p>' : ''}
    </section>`);

    panel.innerHTML = s.join('');
  }

  function panelPortada() {
    const sugeridas = P.busquedasCapturadas().slice(0, 12);
    return `<header class="ficha bienvenida">
        <p class="sobretitulo">Bienvenida ${traza('CU-1 · RF-18 · RF-19')}</p>
        <h2>Explora cómo se conecta la carrera</h2>
        <p class="descripcion">Explora cómo se conectan los conceptos de Ingeniería Informática: qué necesitas saber antes, dónde está cada tema en la carrera y con qué material estudiarlo.</p>
        <p class="descripcion">Elige un área o un curso en el mapa, o busca un tema arriba. Desde ahí, salta de punto en punto y usa las <b>lentes</b> de la izquierda: cada una muestra el mapa desde una pregunta distinta.</p>
      </header>
      <section class="sec"><h3 class="sec-titulo"><span>Dos orígenes, dos formas ${traza('RF-22')}</span></h3>
        <div class="capa-explica capa-reference">${iconoCapa('reference', 26)}<div><b>CS2023</b><p>Hexágono con contorno. Estándar internacional del currículo de computación (ACM/IEEE): sus áreas y unidades.</p></div></div>
        <div class="capa-explica capa-institutional">${iconoCapa('institutional', 26)}<div><b>Sílabo PUCP</b><p>Círculo relleno. Temas, conceptos y cursos que salen de los sílabos; cada uno enlaza a su PDF.</p></div></div>
      </section>
      <section class="sec"><h3 class="sec-titulo"><span>Empieza con una búsqueda</span></h3>
        <div class="sugerencias">${sugeridas.map(q => `<button class="chip-busqueda" data-buscar="${esc(q)}">${esc(q)}</button>`).join('')}</div>
        <p class="nota">Estas búsquedas tienen respuesta real. Otra palabra se busca de forma aproximada en esta maqueta.</p>
      </section>
      <section class="sec"><h3 class="sec-titulo"><span>En el mapa ${traza('CU-1 · ruta nueva: GET /api/overview')}</span></h3>
        <p class="nota">Las 17 áreas de CS2023 y los 4 cursos con sílabo cargado. Las áreas que brillan ya tienen temas de los sílabos; las demás existen solo en CS2023. <span class="etiqueta-simulado" title="El sistema todavía no entrega esta vista de inicio">simulado</span> Esta vista de inicio todavía no la entrega el sistema.</p>
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
      ? `<p class="res-cab">Búsqueda aproximada <span class="etiqueta-simulado">simulada</span>: en esta maqueta se filtra sobre los nombres reales. ${traza('CU-1 · RF-18', '/api/search')}</p>`
      : `<p class="res-cab">${plural(resultados.length, 'resultado', 'resultados')} ${traza('CU-1 · RF-18', '/api/search')}</p>`;
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
    const t = ev.target.closest('[data-ir],[data-lente],[data-buscar],[data-arista],[data-cerrar-arista],[data-grano],[data-paso],[data-portada],[data-ver-pasos]');
    if (!t) return;
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
    if (t.dataset.arista) { seleccionarArista(t.dataset.arista); return; }
    if (t.dataset.cerrarArista !== undefined) { estado.aristaSel = null; lienzo.seleccionar(null); pintarPanel(); return; }
    if (t.dataset.verPasos !== undefined) { $('#recorrido').classList.add('desplegado'); pintarRecorrido(); return; }
    if (t.dataset.paso !== undefined) { hacerPaso(Number(t.dataset.paso)); }
  });

  function atras() {
    const i = estado.rastro.findIndex(x => x.key === estado.foco);
    if (i > 0) irA(estado.rastro[i - 1].key, { rastro: false });
  }

  $('#atras').addEventListener('click', atras);
  $('#inicio').addEventListener('click', mostrarPortada);
  $('#marca').addEventListener('click', mostrarPortada);
  $('#limpiar').addEventListener('click', limpiar);
  $('#ver-procedencia').addEventListener('change', ev => {
    estado.verProcedencia = ev.target.checked;
    lienzo.configurar({ verProcedencia: estado.verProcedencia });
    lienzo.dibujar();
  });
  $('#zoom-mas').addEventListener('click', () => lienzo.zoomPor(1.3));
  $('#zoom-menos').addEventListener('click', () => lienzo.zoomPor(1 / 1.3));
  $('#encuadrar').addEventListener('click', () => lienzo.encuadrar(null));
  $('#leyenda-boton').addEventListener('click', () => {
    const l = $('#leyenda');
    l.hidden = !l.hidden;
    $('#leyenda-boton').setAttribute('aria-expanded', String(!l.hidden));
  });

  // ------------------------------------------------------------------ «Ver trazabilidad»

  function ponerTrazabilidad(si) {
    document.body.classList.toggle('ver-traza', si);
    $('#ver-traza').checked = si;
    try { sessionStorage.setItem('p1-traza', si ? '1' : '0'); } catch (e) { /* sin almacenamiento */ }
  }
  $('#ver-traza').addEventListener('change', ev => ponerTrazabilidad(ev.target.checked));

  // ------------------------------------------------------------------ recorrido sugerido (común a las tres propuestas)

  const PASOS = [
    { t: 'Busca «lógica» y abre el tema «Lógica proposicional».', cu: 'CU-1',
      hacer: async () => { buscador.value = 'lógica'; await buscar('lógica'); cerrarResultados(); await irA(CLAVES.logica, { lente: 'vecindario' }); } },
    { t: 'Mira qué contiene, en qué orden conviene aprenderlo y su material de estudio.', cu: 'CU-6 · CU-7',
      hacer: () => irA(CLAVES.logica, { lente: 'contiene' }) },
    { t: 'Abre «Contradicción»: ¿qué necesitas saber antes?', cu: 'CU-3',
      hacer: () => irA(CLAVES.contradiccion, { lente: 'prerrequisitos' }) },
    { t: '¿De dónde sale que «Contradicción» requiere «Tabla de verdad»? Ver la fuente.', cu: 'CU-10',
      hacer: async () => {
        if (estado.foco !== CLAVES.contradiccion || estado.lente !== 'prerrequisitos') await irA(CLAVES.contradiccion, { lente: 'prerrequisitos' });
        seleccionarArista(`HAS_PREREQUISITE|${CLAVES.contradiccion}|${CLAVES.tablaVerdad}`);
      } },
    { t: 'El camino hasta «Entrada y salida de datos desde archivos», visto por cursos.', cu: 'CU-8',
      hacer: () => irA(CLAVES.archivos, { lente: 'ruta', grano: 'course' }) },
    { t: '«Técnicas de Programación»: qué pide y qué curso conviene llevar antes.', cu: 'CU-4',
      hacer: () => irA(CLAVES.inf144, { lente: 'cursos' }) },
  ];

  // Tras ejecutar un paso, el recorrido se pliega a una barra compacta para no tapar el mapa.
  let pasoActual = -1;
  function pintarRecorrido() {
    const caja = $('#recorrido');
    const compacto = pasoActual >= 0 && !caja.classList.contains('desplegado');
    caja.classList.toggle('compacto', compacto);
    if (compacto) {
      const p = PASOS[pasoActual];
      $('#recorrido-pasos').innerHTML = `<li class="actual"><span class="num">${pasoActual + 1}</span><span><b>${esc(p.t)}</b>${traza(p.cu)}</span></li>
        <li class="nav-pasos"><button data-paso="${Math.max(0, pasoActual - 1)}" ${pasoActual === 0 ? 'disabled' : ''}>‹ Anterior</button>
        <span>${pasoActual + 1} de ${PASOS.length}</span>
        ${pasoActual < PASOS.length - 1 ? `<button data-paso="${pasoActual + 1}" class="siguiente">Siguiente ›</button>` : '<button data-ver-pasos>Ver todos</button>'}</li>`;
    } else {
      $('#recorrido-pasos').innerHTML = PASOS.map((p, i) => `<li${i === pasoActual ? ' class="actual"' : ''}><button data-paso="${i}"><span class="num">${i + 1}</span><span><b>${esc(p.t)}</b>${traza(p.cu)}</span></button></li>`).join('');
    }
  }
  function hacerPaso(i) {
    pasoActual = i;
    $('#recorrido').classList.remove('desplegado');
    pintarRecorrido();
    return PASOS[i].hacer();
  }
  $('#recorrido-titulo').addEventListener('click', () => {
    $('#recorrido').classList.toggle('desplegado');
    pintarRecorrido();
  });
  $('#recorrido-cerrar').addEventListener('click', () => {
    $('#recorrido').hidden = true; $('#recorrido-abrir').hidden = false;
    try { sessionStorage.setItem('p1-recorrido', 'cerrado'); } catch (e) { /* sin almacenamiento */ }
  });
  $('#recorrido-abrir').addEventListener('click', () => {
    $('#recorrido').hidden = false; $('#recorrido-abrir').hidden = true;
    try { sessionStorage.removeItem('p1-recorrido'); } catch (e) { /* sin almacenamiento */ }
  });

  // ------------------------------------------------------------------ arranque

  if (!window.IEKG_DATOS) {
    document.body.insertAdjacentHTML('afterbegin', '<p class="error-datos">No se cargaron los datos (<code>../datos/datos.js</code>). Abre este archivo desde su carpeta, sin moverlo.</p>');
    return;
  }
  if (!window.d3) {
    document.body.insertAdjacentHTML('afterbegin', '<p class="error-datos">No se pudo cargar la librería del mapa. La maqueta necesita conexión a internet.</p>');
    return;
  }
  pintarRecorrido();
  try {
    if (sessionStorage.getItem('p1-recorrido') === 'cerrado') { $('#recorrido').hidden = true; $('#recorrido-abrir').hidden = false; }
    if (sessionStorage.getItem('p1-traza') === '1') ponerTrazabilidad(true);
  } catch (e) { /* sin almacenamiento */ }
  // Enlaces directos: #paso=N abre un paso del recorrido; #traza activa «Ver trazabilidad» (útil para capturas).
  if (/traza/.test(location.hash)) ponerTrazabilidad(true);
  mostrarPortada().then(() => {
    const m = /paso=(\d+)/.exec(location.hash);
    if (m && PASOS[Number(m[1]) - 1]) setTimeout(() => hacerPaso(Number(m[1]) - 1), 300);
  });
})();
