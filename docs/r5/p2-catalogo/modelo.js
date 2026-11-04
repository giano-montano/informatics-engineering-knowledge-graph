// Modelo de las fichas de P2: convierte las respuestas {nodes, edges} de la API
// en lo que la ficha muestra. Sin DOM: se puede ejecutar en node para probarlo.
//
// La lógica de navegación vive en R4 (tesis, l. 538). Aquí solo se ordena y se
// agrupa lo que la API ya devolvió: quién va en qué sección, en qué orden y con
// qué nota de procedencia.
(function (global) {
  'use strict';

  const CLASES = {
    KnowledgeArea: { nombre: 'Área de conocimiento', corto: 'Área', plural: 'Áreas' },
    KnowledgeUnit: { nombre: 'Unidad de conocimiento', corto: 'Unidad', plural: 'Unidades' },
    Topic: { nombre: 'Tema', corto: 'Tema', plural: 'Temas' },
    Concept: { nombre: 'Concepto', corto: 'Concepto', plural: 'Conceptos' },
    Course: { nombre: 'Curso', corto: 'Curso', plural: 'Cursos' },
    LearningResource: { nombre: 'Recurso de estudio', corto: 'Recurso', plural: 'Recursos' },
    ResourceType: { nombre: 'Tipo de recurso', corto: 'Tipo de recurso', plural: 'Tipos de recurso' },
  };

  const CAPAS = {
    reference: { insignia: 'CS2023', nombre: 'Estándar internacional del currículo de computación (ACM/IEEE)', corto: 'CS2023' },
    institutional: { insignia: 'Sílabo PUCP', nombre: 'Sílabo de un curso de la carrera', corto: 'Sílabo PUCP' },
  };

  const CS2023 = 'http://www.informatics-engineering-kms.org/ontology/informatic-engineering#CS2023';
  const GRANOS = {
    topic: { etiqueta: 'Tema', label: 'Topic' },
    course: { etiqueta: 'Curso', label: 'Course' },
    area: { etiqueta: 'Área', label: 'KnowledgeArea' },
  };

  // Registro de recursos vistos en cualquier respuesta: la procedencia de una
  // arista es una clave, y el nodo del sílabo llega en la misma respuesta;
  // CS2023 (procedencia null) llega en casi todas.
  const recursosVistos = new Map();
  function recordar(respuesta) {
    for (const n of (respuesta && respuesta.nodes) || []) {
      if (n.label === 'LearningResource' && !recursosVistos.has(n.key)) recursosVistos.set(n.key, n);
    }
    return respuesta;
  }

  function indice(respuesta) {
    const m = new Map();
    for (const n of respuesta.nodes) m.set(n.key, n);
    return m;
  }

  function porNombre(a, b) {
    return (a.nombre || '').localeCompare(b.nombre || '', 'es');
  }

  function nombreDe(n) {
    if (!n) return '';
    return n.label === 'Course' && n.course_code ? `${n.name_es} (${n.course_code})` : n.name_es;
  }

  // Notas al pie: una por documento, numeradas en orden de aparición en la ficha.
  function crearFuentes() {
    const lista = [];
    const porClave = new Map();
    function de(arista) {
      const clave = arista.provenance || CS2023;
      if (!porClave.has(clave)) {
        const nodo = recursosVistos.get(clave) || { key: clave, name_es: clave === CS2023 ? 'CS2023' : 'Documento', layer: clave === CS2023 ? 'reference' : 'institutional' };
        // La marca muestra el código del documento («1INF01», «CS2023»): dice de
        // qué sílabo sale sin coordinar numeraciones entre secciones.
        const corto = clave === CS2023 ? 'CS2023' : String(nodo.name_es || 'Doc').replace(/^Sílabo\s+/i, '');
        const nota = { n: lista.length + 1, clave, nombre: nodo.name_es, corto, locator: nodo.locator || null, capa: nodo.layer };
        porClave.set(clave, nota);
        lista.push(nota);
      }
      return porClave.get(clave);
    }
    return { de, lista };
  }

  function fila(nodo, extra) {
    return Object.assign({
      clave: nodo.key,
      nombre: nombreDe(nodo),
      label: nodo.label,
      capa: nodo.layer,
      notas: [],
    }, extra || {});
  }

  function agregarNota(f, nota) {
    if (nota && !f.notas.some((x) => x.n === nota.n)) f.notas.push(nota);
    return f;
  }

  function seccion(id, titulo, traza, extra) {
    // `traza`: caso de uso y códigos; solo se ven con «Ver trazabilidad».
    return Object.assign({ id, titulo, traza, grupos: [], vacio: null, ayuda: null }, extra || {});
  }

  function contar(s) {
    return s.grupos.reduce((t, g) => t + g.filas.length, 0);
  }

  // ── Recorridos sobre una respuesta ya recibida ─────────────────────────────

  // Sube por PART_OF desde `clave`: [{nodo, arista}] del padre inmediato al área.
  function ancestros(resp, clave) {
    const idx = indice(resp);
    const cadena = [];
    let actual = clave;
    const vistos = new Set([clave]);
    for (;;) {
      const a = resp.edges.find((e) => e.type === 'PART_OF' && e.source === actual);
      if (!a || vistos.has(a.target)) break;
      cadena.push({ nodo: idx.get(a.target), arista: a });
      vistos.add(a.target);
      actual = a.target;
    }
    return cadena;
  }

  function hijos(resp, clave) {
    const idx = indice(resp);
    return resp.edges
      .filter((e) => e.type === 'PART_OF' && e.target === clave)
      .map((e) => ({ nodo: idx.get(e.source), arista: e }))
      .filter((x) => x.nodo);
  }

  // Aristas del foco en el detalle (`/api/nodes`), sin WAS_DERIVED_FROM.
  function aristasDelFoco(detalle, tipo, sentido) {
    const foco = detalle.nodes[0].key;
    return detalle.edges.filter((e) => e.type === tipo && (sentido === 'sale' ? e.source === foco : e.target === foco));
  }

  // Orden por prerrequisitos entre las partes (PC4): nivel 0 = no requiere a
  // ninguna otra parte; nivel k = 1 + el mayor nivel de lo que requiere.
  function niveles(claves, aristasPrereq) {
    const dentro = new Set(claves);
    const req = new Map(claves.map((k) => [k, []]));
    for (const e of aristasPrereq) {
      if (dentro.has(e.source) && dentro.has(e.target)) req.get(e.source).push(e);
    }
    const nivel = new Map();
    function calcular(k, pila) {
      if (nivel.has(k)) return nivel.get(k);
      if (pila.has(k)) return 0; // ciclo: no debería ocurrir (regla de integridad)
      pila.add(k);
      let n = 0;
      for (const e of req.get(k)) n = Math.max(n, 1 + calcular(e.target, pila));
      pila.delete(k);
      nivel.set(k, n);
      return n;
    }
    for (const k of claves) calcular(k, new Set());
    return { nivel, req };
  }

  // ── Secciones comunes ──────────────────────────────────────────────────────

  function seccionProcedencia(detalle, fuentes) {
    const idx = indice(detalle);
    const s = seccion('procedencia', 'Fuente', 'CU-10 · RF-21', {
      ayuda: 'El documento del que sale este elemento.',
    });
    const filas = aristasDelFoco(detalle, 'WAS_DERIVED_FROM', 'sale').map((e) => {
      const doc = idx.get(e.target) || recursosVistos.get(e.target);
      if (!doc) return null;
      const f = fila(doc, { enlace: doc.locator, textoEnlace: doc.layer === 'reference' ? 'Ver fuente: CS2023' : 'Ver fuente: el sílabo (PDF)' });
      return agregarNota(f, fuentes.de(e));
    }).filter(Boolean);
    s.grupos.push({ filas });
    if (!filas.length) s.vacio = 'No se encontró el documento del que sale.';
    return s;
  }

  // Recursos agregados (PC5): los que tratan sobre el elemento o sus partes.
  function filasRecursos(resp, focoClave, fuentes) {
    const idx = indice(resp);
    const porRecurso = new Map();
    for (const e of resp.edges) {
      if (e.type !== 'IS_ABOUT') continue;
      const rec = idx.get(e.source);
      if (!rec) continue;
      if (!porRecurso.has(rec.key)) {
        const tipos = resp.edges.filter((t) => t.type === 'HAS_RESOURCE_TYPE' && t.source === rec.key)
          .map((t) => (idx.get(t.target) || {}).name_es).filter(Boolean);
        porRecurso.set(rec.key, fila(rec, {
          enlace: rec.locator, textoEnlace: 'Abrir el sílabo (PDF)', tipos, via: [],
        }));
      }
      const f = porRecurso.get(rec.key);
      agregarNota(f, fuentes.de(e));
      if (e.target !== focoClave && idx.get(e.target)) f.via.push(nombreDe(idx.get(e.target)));
    }
    return [...porRecurso.values()].map((f) => {
      const partes = [...new Set(f.via)].sort((a, b) => a.localeCompare(b, 'es'));
      f.detalle = [f.tipos.join(', '), partes.length ? `llega por ${partes.length === 1 ? 'su parte' : 'sus partes'}: ${partes.join(', ')}` : 'trata directamente sobre esto']
        .filter(Boolean).join(' · ');
      return f;
    }).sort(porNombre);
  }

  async function seccionRecursos(api, foco, fuentes, temaDelConcepto) {
    const s = seccion('recursos', 'Material de estudio', 'CU-7 · PC5 · RF-14');
    const resp = recordar(await api('/api/elements/resources', { key: foco.key }));
    let filas = filasRecursos(resp, foco.key, fuentes);
    if (!filas.length && foco.label === 'Concept' && temaDelConcepto) {
      const delTema = recordar(await api('/api/elements/resources', { key: temaDelConcepto.key }));
      filas = filasRecursos(delTema, temaDelConcepto.key, fuentes);
      s.ayuda = `Un concepto no tiene material propio: este es el de su tema, «${temaDelConcepto.name_es}».`;
      s.desdeTema = { clave: temaDelConcepto.key, nombre: temaDelConcepto.name_es };
    } else {
      s.ayuda = 'Material que trata sobre esto o sobre alguna de sus partes.';
    }
    s.grupos.push({ filas });
    if (!filas.length) {
      s.vacio = foco.layer === 'reference'
        ? 'Todavía ningún sílabo trata sobre esto: está en CS2023, pero aún no en los cursos cargados.'
        : 'Todavía no hay material de estudio sobre esto.';
    }
    return s;
  }

  // ── Fichas por clase ───────────────────────────────────────────────────────

  async function fichaConcepto(api, f, detalle, fuentes) {
    const foco = f.foco;
    const loc = recordar(await api('/api/elements/location', { key: foco.key }));
    const cadena = ancestros(loc, foco.key);
    f.migas = cadena.slice().reverse().map((x) => ({ clave: x.nodo.key, nombre: nombreDe(x.nodo), label: x.nodo.label, capa: x.nodo.layer }));
    const tema = cadena.length ? cadena[0].nodo : null;

    // Forma parte de (PC3)
    const parte = seccion('parte-de', 'Dónde está en la carrera', 'CU-5 · PC3 · RF-13', { ayuda: 'Su tema, y la unidad y el área de CS2023 donde se ubica.' });
    parte.grupos.push({ filas: cadena.map((x) => agregarNota(fila(x.nodo), fuentes.de(x.arista))) });
    if (!cadena.length) parte.vacio = 'Este concepto todavía no está ubicado en ningún tema.';

    // Necesitas antes (PC1)
    const pre = recordar(await api('/api/concepts/prerequisites', { key: foco.key }));
    const idxPre = indice(pre);
    const necesitas = seccion('necesitas-antes', 'Qué necesitas antes', 'CU-3 · PC1 · RF-11', {
      ayuda: 'Lo que conviene saber antes, del más cercano al más lejano. Cada marca dice de qué sílabo sale.',
    });
    const profundidades = [...new Set(pre.nodes.filter((n) => n.label === 'Concept' && n.depth > 0).map((n) => n.depth))].sort();
    for (const d of profundidades) {
      const filas = pre.nodes.filter((n) => n.label === 'Concept' && n.depth === d).map((n) => {
        const llegan = pre.edges.filter((e) => e.type === 'HAS_PREREQUISITE' && e.target === n.key);
        const quienes = llegan.map((e) => idxPre.get(e.source)).filter((x) => x && x.key !== foco.key).map((x) => x.name_es);
        const fl = fila(n, { detalle: quienes.length ? `lo necesita ${quienes.join(', ')}` : null });
        llegan.forEach((e) => agregarNota(fl, fuentes.de(e)));
        return fl;
      }).sort(porNombre);
      necesitas.grupos.push({ titulo: d === 1 ? 'Directos' : `A ${d} pasos`, filas });
    }
    if (!profundidades.length) necesitas.vacio = 'Nada registrado: se puede empezar por aquí. Más abajo, en «Qué depende de él», está lo que se apoya en este concepto.';

    // Te prepara para (inverso, desde el detalle)
    const idxDet = indice(detalle);
    const prepara = seccion('prepara-para', 'Qué depende de él', 'CU-3 · CU-2', {
      ayuda: 'Conceptos que conviene aprender después de este, porque lo necesitan.',
    });
    const filasPrep = aristasDelFoco(detalle, 'HAS_PREREQUISITE', 'entra')
      .map((e) => agregarNota(fila(idxDet.get(e.source)), fuentes.de(e))).sort(porNombre);
    prepara.grupos.push({ filas: filasPrep });
    if (!filasPrep.length) prepara.vacio = 'Ningún concepto registrado lo necesita.';

    // Cursos (desde el detalle)
    const cursos = seccion('cursos', 'Cursos que lo enseñan o lo piden', 'CU-2', { ayuda: 'Cursos cuyo sílabo lo enseña, o lo pide como saber previo.' });
    for (const [tipo, titulo] of [['TEACHES_CONCEPT', 'Lo enseña'], ['REQUIRES_CONCEPT', 'Lo pide']]) {
      const filas = aristasDelFoco(detalle, tipo, 'entra').map((e) => agregarNota(fila(idxDet.get(e.source)), fuentes.de(e))).sort(porNombre);
      if (filas.length) cursos.grupos.push({ titulo, filas });
    }
    if (!cursos.grupos.length) cursos.vacio = 'Ningún curso cargado lo enseña ni lo pide.';

    // Tipos de / es un tipo de (PC7)
    const esp = recordar(await api('/api/concepts/specializations', { key: foco.key }));
    const idxEsp = indice(esp);
    const tipos = seccion('tipos', 'Es un tipo de · Tipos', 'CU-9 · PC7 · RF-16', { ayuda: 'De qué concepto más general es un tipo, y qué tipos tiene.' });
    const cerrar = (desde, siguiente) => {
      const out = [];
      const vistos = new Set([desde]);
      const cola = [desde];
      while (cola.length) {
        const k = cola.shift();
        for (const e of esp.edges.filter((x) => x.type === 'SPECIALIZES')) {
          const [de, a] = siguiente === 'arriba' ? [e.source, e.target] : [e.target, e.source];
          if (de === k && !vistos.has(a)) {
            vistos.add(a);
            cola.push(a);
            out.push(agregarNota(fila(idxEsp.get(a)), fuentes.de(e)));
          }
        }
      }
      return out;
    };
    const arriba = cerrar(foco.key, 'arriba');
    const abajo = cerrar(foco.key, 'abajo');
    if (arriba.length) tipos.grupos.push({ titulo: 'Es un tipo de', filas: arriba });
    if (abajo.length) tipos.grupos.push({ titulo: 'Tipos', filas: abajo });
    if (!tipos.grupos.length) tipos.vacio = 'No es un tipo de otro concepto ni tiene tipos registrados.';

    const recursos = await seccionRecursos(api, foco, fuentes, tema);

    f.lede = [
      tema ? `Concepto del tema «${tema.name_es}»` : 'Concepto sin tema',
      cadena[1] ? `, en la unidad «${cadena[1].nodo.name_es}»` : '',
      cadena[2] ? ` del área «${cadena[2].nodo.name_es}»` : '',
      '.',
    ].join('');
    const ens = cursos.grupos.find((g) => g.titulo === 'Lo enseña');
    if (ens) f.lede += ` Lo enseña ${ens.filas.map((x) => x.nombre).join(', ')}.`;

    f.cifras = [
      { etiqueta: 'necesitas antes', valor: contar(necesitas), ir: 'necesitas-antes' },
      { etiqueta: 'dependen de él', valor: contar(prepara), ir: 'prepara-para' },
      { etiqueta: 'cursos', valor: contar(cursos), ir: 'cursos' },
      { etiqueta: 'tipos', valor: contar(tipos), ir: 'tipos' },
      { etiqueta: recursos.desdeTema ? 'material del tema' : 'material', valor: contar(recursos), ir: 'recursos' },
    ];
    f.secciones = [parte, necesitas, prepara, cursos, tipos, recursos];
    f.ruta = true;
  }

  async function fichaTema(api, f, detalle, fuentes) {
    const foco = f.foco;
    const loc = recordar(await api('/api/elements/location', { key: foco.key }));
    const cadena = ancestros(loc, foco.key);
    f.migas = cadena.slice().reverse().map((x) => ({ clave: x.nodo.key, nombre: nombreDe(x.nodo), label: x.nodo.label, capa: x.nodo.layer }));

    const parte = seccion('parte-de', 'Dónde está en la carrera', 'CU-5 · PC3 · RF-13');
    parte.grupos.push({ filas: cadena.map((x) => agregarNota(fila(x.nodo), fuentes.de(x.arista))) });

    // Contiene, en orden de prerrequisitos (PC4)
    const partes = hijos(loc, foco.key);
    const idx = indice(loc);
    const prereq = loc.edges.filter((e) => e.type === 'HAS_PREREQUISITE');
    const { nivel, req } = niveles(partes.map((p) => p.nodo.key), prereq);
    const hayOrden = [...nivel.values()].some((n) => n > 0);
    const contiene = seccion('contiene', 'Qué contiene y en qué orden aprenderlo', 'CU-6 · PC4 · RF-13', {
      ayuda: hayOrden
        ? 'Sus conceptos en el orden que sugieren sus prerrequisitos: cada paso se apoya en los anteriores.'
        : 'Sus conceptos. No hay prerrequisitos registrados entre ellos, así que el orden es alfabético.',
      numerada: hayOrden,
    });
    const maxNivel = Math.max(0, ...nivel.values());
    for (let n = 0; n <= maxNivel; n++) {
      const filas = partes.filter((p) => nivel.get(p.nodo.key) === n).map((p) => {
        const necesita = req.get(p.nodo.key).map((e) => idx.get(e.target).name_es);
        const fl = agregarNota(fila(p.nodo, { detalle: necesita.length ? `se apoya en ${necesita.join(', ')}` : null }), fuentes.de(p.arista));
        req.get(p.nodo.key).forEach((e) => agregarNota(fl, fuentes.de(e)));
        return fl;
      }).sort(porNombre);
      if (filas.length) contiene.grupos.push({ titulo: hayOrden ? `Paso ${n + 1}` : null, filas });
    }
    if (!partes.length) contiene.vacio = 'Todavía no tiene conceptos registrados.';

    const recursos = await seccionRecursos(api, foco, fuentes, null);
    f.lede = `Tema de la unidad «${cadena[0] ? cadena[0].nodo.name_es : '—'}»${cadena[1] ? `, en el área «${cadena[1].nodo.name_es}»` : ''}. Reúne ${partes.length} ${partes.length === 1 ? 'concepto' : 'conceptos'}.`;
    f.cifras = [
      { etiqueta: 'conceptos', valor: partes.length, ir: 'contiene' },
      { etiqueta: 'relaciones de orden', valor: prereq.filter((e) => nivel.has(e.source) && nivel.has(e.target)).length, ir: 'contiene' },
      { etiqueta: 'pasos', valor: hayOrden ? maxNivel + 1 : 1, ir: 'contiene' },
      { etiqueta: 'recursos', valor: contar(recursos), ir: 'recursos' },
    ];
    f.secciones = [parte, contiene, recursos];
    f.ruta = true;
  }

  async function fichaUnidad(api, f, detalle, fuentes) {
    const foco = f.foco;
    const loc = recordar(await api('/api/elements/location', { key: foco.key }));
    const cadena = ancestros(loc, foco.key);
    f.migas = cadena.slice().reverse().map((x) => ({ clave: x.nodo.key, nombre: nombreDe(x.nodo), label: x.nodo.label, capa: x.nodo.layer }));
    const parte = seccion('parte-de', 'Dónde está en la carrera', 'CU-5 · PC3 · RF-13');
    parte.grupos.push({ filas: cadena.map((x) => agregarNota(fila(x.nodo), fuentes.de(x.arista))) });

    const temas = hijos(loc, foco.key);
    let totalConceptos = 0;
    const contiene = seccion('contiene', 'Qué contiene', 'CU-6 · PC4 · RF-13', { ayuda: 'Los temas de los sílabos que se ubican en esta unidad y, dentro de cada uno, sus conceptos.' });
    const filas = temas.map((t) => {
      const c = hijos(loc, t.nodo.key);
      totalConceptos += c.length;
      return agregarNota(fila(t.nodo, {
        detalle: `${c.length} ${c.length === 1 ? 'concepto' : 'conceptos'}`,
        sub: c.map((x) => agregarNota(fila(x.nodo), fuentes.de(x.arista))).sort(porNombre),
      }), fuentes.de(t.arista));
    }).sort(porNombre);
    contiene.grupos.push({ filas });
    if (!filas.length) contiene.vacio = 'Esta unidad está en CS2023, pero todavía ningún sílabo cargado la aborda.';

    const recursos = await seccionRecursos(api, foco, fuentes, null);
    f.lede = `Unidad de conocimiento de CS2023 en el área «${cadena[0] ? cadena[0].nodo.name_es : '—'}». ` +
      (temas.length ? `Los sílabos cargados ubican aquí ${temas.length} ${temas.length === 1 ? 'tema' : 'temas'} y ${totalConceptos} conceptos.` : 'Todavía no tiene contenido de los sílabos.');
    f.cifras = [
      { etiqueta: 'temas', valor: temas.length, ir: 'contiene' },
      { etiqueta: 'conceptos', valor: totalConceptos, ir: 'contiene' },
      { etiqueta: 'recursos', valor: contar(recursos), ir: 'recursos' },
    ];
    f.secciones = [parte, contiene, recursos];
    f.ruta = true;
  }

  async function fichaArea(api, f, detalle, fuentes) {
    const foco = f.foco;
    const loc = recordar(await api('/api/elements/location', { key: foco.key }));
    f.migas = [];
    const unidades = hijos(loc, foco.key);
    let temasTot = 0;
    let conceptosTot = 0;
    const con = [];
    const sin = [];
    for (const u of unidades) {
      const temas = hijos(loc, u.nodo.key);
      const conceptos = temas.reduce((t, x) => t + hijos(loc, x.nodo.key).length, 0);
      temasTot += temas.length;
      conceptosTot += conceptos;
      const fl = agregarNota(fila(u.nodo, {
        nombreEn: u.nodo.name_en,
        detalle: temas.length ? `${temas.length} ${temas.length === 1 ? 'tema' : 'temas'} · ${conceptos} conceptos` : 'por ahora, solo en CS2023',
        // Nivel por nivel (CU-6): unidad › tema › conceptos, cada nivel plegable.
        sub: temas.map((t) => {
          const cs = hijos(loc, t.nodo.key);
          return agregarNota(fila(t.nodo, {
            detalle: `${cs.length} ${cs.length === 1 ? 'concepto' : 'conceptos'}`,
            sub: cs.map((x) => agregarNota(fila(x.nodo), fuentes.de(x.arista))).sort(porNombre),
          }), fuentes.de(t.arista));
        }).sort(porNombre),
      }), fuentes.de(u.arista));
      (temas.length ? con : sin).push(fl);
    }
    const contiene = seccion('contiene', 'Qué contiene', 'CU-6 · PC4 · RF-13', { ayuda: 'Nivel por nivel: las unidades de CS2023 de esta área; dentro de cada una, los temas de los sílabos, y dentro de cada tema, sus conceptos. Abre cada nivel con «Ver».' });
    if (con.length) contiene.grupos.push({ titulo: 'Con contenido de los sílabos', filas: con.sort(porNombre) });
    if (sin.length) contiene.grupos.push({ titulo: 'Solo en CS2023', filas: sin.sort(porNombre), tenue: true });

    const recursos = await seccionRecursos(api, foco, fuentes, null);
    f.lede = `Área de conocimiento de CS2023 con ${unidades.length} unidades. ` +
      (con.length ? `${con.length === 1 ? 'Una de ellas tiene' : `${con.length} de ellas tienen`} contenido de los sílabos cargados: ${temasTot} ${temasTot === 1 ? 'tema' : 'temas'} y ${conceptosTot} conceptos.` : 'Ningún sílabo cargado aborda todavía esta área.');
    f.cifras = [
      { etiqueta: 'unidades', valor: unidades.length, ir: 'contiene' },
      { etiqueta: 'con contenido', valor: con.length, ir: 'contiene' },
      { etiqueta: 'temas', valor: temasTot, ir: 'contiene' },
      { etiqueta: 'conceptos', valor: conceptosTot, ir: 'contiene' },
      { etiqueta: 'recursos', valor: contar(recursos), ir: 'recursos' },
    ];
    f.secciones = [contiene, recursos];
    f.ruta = true;
  }

  async function fichaCurso(api, f, detalle, fuentes) {
    const foco = f.foco;
    f.migas = [{ clave: null, nombre: 'Cursos', label: 'Course', capa: 'institutional' }];
    const cp = recordar(await api('/api/courses/prerequisites', { key: foco.key }));
    const idx = indice(cp);
    const ensena = cp.edges.filter((e) => e.type === 'TEACHES_CONCEPT' && e.source === foco.key);
    const asume = cp.edges.filter((e) => e.type === 'REQUIRES_CONCEPT' && e.source === foco.key);

    // Cursos previos (PC2): X precede a este curso si enseña algo que este asume.
    const previos = new Map();
    for (const r of asume) {
      for (const t of cp.edges.filter((e) => e.type === 'TEACHES_CONCEPT' && e.target === r.target && e.source !== foco.key)) {
        if (!previos.has(t.source)) previos.set(t.source, { curso: idx.get(t.source), evidencia: [] });
        previos.get(t.source).evidencia.push({ concepto: idx.get(r.target), ensena: t, asume: r });
      }
    }
    const secPrev = seccion('cursos-previos', 'Cursos que conviene llevar antes', 'CU-4 · PC2 · RF-12', {
      ayuda: 'Cursos que enseñan algo de lo que este curso pide. Debajo de cada uno, los conceptos que lo justifican.',
    });
    const filasPrev = [...previos.values()].map((p) => {
      const fl = fila(p.curso, {
        detalle: `enseña ${p.evidencia.length} ${p.evidencia.length === 1 ? 'concepto' : 'conceptos'} que este curso pide`,
        sub: p.evidencia.map((ev) => {
          const s = fila(ev.concepto, { detalle: `lo enseña ${p.curso.course_code}; lo pide ${foco.course_code}` });
          agregarNota(s, fuentes.de(ev.ensena));
          agregarNota(s, fuentes.de(ev.asume));
          return s;
        }).sort(porNombre),
      });
      p.evidencia.forEach((ev) => { agregarNota(fl, fuentes.de(ev.ensena)); agregarNota(fl, fuentes.de(ev.asume)); });
      return fl;
    }).sort(porNombre);
    secPrev.grupos.push({ filas: filasPrev, abierta: true });
    if (!filasPrev.length) secPrev.vacio = 'Ningún otro curso cargado enseña lo que este curso pide.';

    // Lo que asume
    const secAsume = seccion('asume', 'Lo que pide', 'CU-4 · PC2 · RF-12', { ayuda: 'Lo que el sílabo da por sabido al empezar el curso.' });
    const filasAsume = asume.map((r) => {
      const quien = cp.edges.filter((e) => e.type === 'TEACHES_CONCEPT' && e.target === r.target && e.source !== foco.key).map((e) => idx.get(e.source).course_code);
      return agregarNota(fila(idx.get(r.target), { detalle: quien.length ? `lo enseña ${quien.join(', ')}` : 'ningún curso cargado lo enseña' }), fuentes.de(r));
    }).sort(porNombre);
    secAsume.grupos.push({ filas: filasAsume });
    if (!filasAsume.length) secAsume.vacio = 'El sílabo no pide conocimientos previos.';

    // Lo que enseña, agrupado por tema. Se sube cada concepto con RF-13 (una
    // llamada por concepto en la maqueta; ver README §5, ampliación sugerida).
    const secEnsena = seccion('ensena', 'Lo que enseña', 'CU-4 · PC2 · RF-12', { ayuda: 'Sus conceptos, agrupados por el tema del sílabo al que pertenecen.' });
    const grupos = new Map();
    for (const e of ensena) {
      const c = idx.get(e.target);
      let tema = null;
      try {
        const loc = recordar(await api('/api/elements/location', { key: c.key }));
        const cad = ancestros(loc, c.key);
        tema = cad.length ? cad[0].nodo : null;
      } catch (err) { tema = null; }
      const k = tema ? tema.key : '_';
      if (!grupos.has(k)) grupos.set(k, { titulo: tema ? tema.name_es : 'Sin tema', clave: tema ? tema.key : null, filas: [] });
      grupos.get(k).filas.push(agregarNota(fila(c), fuentes.de(e)));
    }
    secEnsena.grupos = [...grupos.values()].map((g) => Object.assign(g, { filas: g.filas.sort(porNombre) }))
      .sort((a, b) => a.titulo.localeCompare(b.titulo, 'es'));
    if (!ensena.length) secEnsena.vacio = 'Todavía no tiene conceptos registrados.';

    const recursos = await seccionRecursos(api, foco, fuentes, null);
    f.lede = `Curso con sílabo cargado. Enseña ${ensena.length} conceptos en ${grupos.size} temas y pide ${asume.length} como saber previo.` +
      (filasPrev.length ? ` Conviene llevar antes ${filasPrev.map((x) => x.nombre).join(', ')}.` : '');
    f.cifras = [
      { etiqueta: 'enseña', valor: ensena.length, ir: 'ensena' },
      { etiqueta: 'temas', valor: grupos.size, ir: 'ensena' },
      { etiqueta: 'pide', valor: asume.length, ir: 'asume' },
      { etiqueta: 'cursos antes', valor: filasPrev.length, ir: 'cursos-previos' },
    ];
    f.secciones = [secAsume, secPrev, secEnsena, recursos];
    f.ruta = true;
  }

  async function fichaRecurso(api, f, detalle, fuentes) {
    const foco = f.foco;
    f.migas = [{ clave: null, nombre: 'Recursos', label: 'LearningResource', capa: foco.layer }];
    const idx = indice(detalle);
    const trata = seccion('trata-sobre', 'Trata sobre', 'CU-7 · CU-2', { ayuda: 'El curso y los temas sobre los que trata este documento.' });
    for (const [label, titulo] of [['Course', 'Curso'], ['Topic', 'Temas']]) {
      const filas = aristasDelFoco(detalle, 'IS_ABOUT', 'sale').filter((e) => (idx.get(e.target) || {}).label === label)
        .map((e) => agregarNota(fila(idx.get(e.target)), fuentes.de(e))).sort(porNombre);
      if (filas.length) trata.grupos.push({ titulo, filas });
    }
    if (!trata.grupos.length) trata.vacio = foco.layer === 'reference'
      ? 'El documento de referencia del backbone: de él se derivan las 17 áreas y las 162 unidades.'
      : 'Sin elementos registrados.';
    const tipo = aristasDelFoco(detalle, 'HAS_RESOURCE_TYPE', 'sale').map((e) => idx.get(e.target)).filter(Boolean);
    f.documento = { locator: foco.locator, tipo: tipo.map((t) => t.name_es).join(', ') || null };
    f.lede = foco.description || (tipo.length ? `${tipo[0].name_es} cargado en el sistema.` : 'Documento del sistema.');
    f.cifras = [{ etiqueta: 'elementos', valor: contar(trata), ir: 'trata-sobre' }];
    f.secciones = [trata];
    f.ruta = false;
  }

  async function fichaTipo(api, f, detalle, fuentes) {
    f.migas = [{ clave: null, nombre: 'Recursos', label: 'ResourceType', capa: 'institutional' }];
    const idx = indice(detalle);
    const recursos = seccion('recursos', 'Recursos de este tipo', 'CU-7');
    const filas = aristasDelFoco(detalle, 'HAS_RESOURCE_TYPE', 'entra')
      .map((e) => agregarNota(fila(idx.get(e.source), { enlace: idx.get(e.source).locator, textoEnlace: 'Abrir el sílabo (PDF)' }), fuentes.de(e))).sort(porNombre);
    recursos.grupos.push({ filas });
    f.lede = 'Tipo de recurso de estudio. Por ahora, el sílabo es el único.';
    f.cifras = [{ etiqueta: 'recursos', valor: filas.length, ir: 'recursos' }];
    f.secciones = [recursos];
    f.ruta = false;
  }

  const SINGULAR = {
    cursos: 'curso', tipos: 'tipo', recursos: 'recurso', conceptos: 'concepto', 'cursos antes': 'curso antes',
    'relaciones de orden': 'relación de orden', pasos: 'paso', temas: 'tema', unidades: 'unidad', 'dependen de él': 'depende de él',
    elementos: 'elemento',
  };

  const POR_CLASE = {
    Concept: fichaConcepto, Topic: fichaTema, KnowledgeUnit: fichaUnidad, KnowledgeArea: fichaArea,
    Course: fichaCurso, LearningResource: fichaRecurso, ResourceType: fichaTipo,
  };

  async function construirFicha(api, clave) {
    const detalle = recordar(await api('/api/nodes', { key: clave }));
    const foco = detalle.nodes[0];
    const fuentes = crearFuentes();
    const f = {
      foco,
      clase: CLASES[foco.label] || { nombre: foco.label, corto: foco.label },
      capa: CAPAS[foco.layer] || { insignia: foco.layer, nombre: foco.layer },
      migas: [], lede: '', cifras: [], secciones: [], ruta: false,
      detalle,
      incompleto: !!foco.more_neighbors,
    };
    await POR_CLASE[foco.label](api, f, detalle, fuentes);
    if (foco.label !== 'LearningResource') f.secciones.push(seccionProcedencia(detalle, fuentes));
    for (const c of f.cifras) if (c.valor === 1 && SINGULAR[c.etiqueta]) c.etiqueta = SINGULAR[c.etiqueta];
    f.fuentes = fuentes.lista;
    return f;
  }

  // ── Ruta de aprendizaje (PC6) ──────────────────────────────────────────────

  async function construirRuta(api, clave, grano) {
    const resp = recordar(await api('/api/learning-path', { key: clave, grain: grano }));
    const idx = indice(resp);
    const fuentes = crearFuentes();
    const labelGrano = GRANOS[grano].label;
    const objetivo = resp.nodes.find((n) => n.key === clave) || resp.nodes[0];
    const prereqs = resp.nodes.filter((n) => n.label === 'Concept' && n.depth > 0);
    const padres = new Map();
    for (const e of resp.edges.filter((x) => x.type === 'PART_OF')) {
      if (!padres.has(e.source)) padres.set(e.source, []);
      padres.get(e.source).push(e);
    }

    function subeA(concepto) {
      const destinos = [];
      if (grano === 'course') {
        resp.edges.filter((e) => e.type === 'TEACHES_CONCEPT' && e.target === concepto).forEach((e) => destinos.push({ clave: e.source, aristas: [e] }));
      } else {
        // Un concepto puede estar en más de un tema: se siguen todas sus aristas PART_OF.
        const cola = [{ k: concepto, aristas: [] }];
        const vistos = new Set([concepto]);
        while (cola.length) {
          const { k, aristas } = cola.shift();
          for (const e of (padres.get(k) || [])) {
            if (vistos.has(e.target)) continue;
            vistos.add(e.target);
            const camino = aristas.concat([e]);
            if ((idx.get(e.target) || {}).label === labelGrano) destinos.push({ clave: e.target, aristas: camino });
            else cola.push({ k: e.target, aristas: camino });
          }
        }
      }
      return destinos;
    }

    // El tema (curso, área) del propio objetivo: si un prerrequisito cae ahí, la ruta
    // lo incluye porque el objetivo es el concepto, no su tema (diseño de las rutas, §6).
    const propios = new Set(subeA(objetivo.key).map((d) => d.clave));
    const items = new Map();
    for (const p of prereqs) {
      for (const d of subeA(p.key)) {
        const nodo = idx.get(d.clave);
        if (!nodo || nodo.key === objetivo.key) continue;
        if (!items.has(nodo.key)) items.set(nodo.key, { nodo, conceptos: [] });
        const porque = resp.edges.filter((e) => e.type === 'HAS_PREREQUISITE' && e.target === p.key);
        const fl = fila(p, { detalle: porque.length ? `lo necesita ${porque.map((e) => (idx.get(e.source) || {}).name_es).join(', ')}` : null, profundidad: p.depth });
        porque.forEach((e) => agregarNota(fl, fuentes.de(e)));
        d.aristas.forEach((e) => agregarNota(fl, fuentes.de(e)));
        items.get(nodo.key).conceptos.push(fl);
      }
    }
    const niveles = new Map();
    for (const it of items.values()) {
      const d = it.nodo.depth != null ? it.nodo.depth : Math.min(...it.conceptos.map((c) => c.profundidad));
      if (!niveles.has(d)) niveles.set(d, []);
      const propio = propios.has(it.nodo.key);
      const fl = fila(it.nodo, {
        sub: it.conceptos.sort(porNombre),
        propio,
        marca: propio ? { topic: 'su mismo tema', course: 'su mismo curso', area: 'su misma área' }[grano] : null,
        aviso: propio ? `El prerrequisito está en ${{ topic: 'el mismo tema', course: 'el mismo curso', area: 'la misma área' }[grano]}: se cuenta porque la meta es este ${(CLASES[objetivo.label] || { corto: 'elemento' }).corto.toLowerCase()}, no su ${{ topic: 'tema', course: 'curso', area: 'área' }[grano]}.` : null,
      });
      it.conceptos.forEach((c) => c.notas.forEach((n) => agregarNota(fl, n)));
      niveles.get(d).push(fl);
    }
    const etapas = [...niveles.keys()].sort((a, b) => b - a).map((d) => ({
      profundidad: d,
      titulo: d === 1 ? 'Directo' : `A ${d} pasos`,
      filas: niveles.get(d).sort(porNombre),
    }));
    return {
      objetivo: fila(objetivo),
      grano,
      etapas,
      prerrequisitos: prereqs.length,
      fuentes: fuentes.lista,
      vacia: etapas.length === 0,
    };
  }

  global.IEKG_MODELO = { CLASES, CAPAS, GRANOS, CS2023, construirFicha, construirRuta, recordar, nombreDe };
})(typeof window !== 'undefined' ? window : globalThis);
