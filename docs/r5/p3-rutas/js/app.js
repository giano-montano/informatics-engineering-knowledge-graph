/* Aplicación de la maqueta P3 · Itinerario (Vue 3, variante sin compilación). */
(function () {
  'use strict';
  const { createApp, markRaw, nextTick } = Vue;
  const { api, buscar } = window.IEKG_API;
  const M = window.IEKG_MODELO;

  const K = {
    contradiccion: 'ce8cd4d1-77f1-4ec1-b10f-d8b87dabe678',
    archivosES: '9a161bca-1a01-43de-8875-7bdfb53ebd84',
    archivos: 'ef4e82d7-f047-4074-a7da-ca1e0442eeea',
    zonasDNS: '39173978-d32d-4b06-9883-f5edc303456c',
    inf144: 'b2d9c106-684d-58b8-8462-4dc0c3b8d90c',
    logica: '40347f92-1123-45ef-8225-b77837c551d7',
    cadenas: 'd5e9e453-6464-42a1-be2d-b4795527d532',
    tabla: '29a47e34-1d18-4962-9501-c4f5b960003c'
  };

  // Recorrido común a las tres propuestas: el texto es fijo; la acción es la de esta interfaz.
  const RECORRIDO = [
    { titulo: 'Busca «lógica» y abre el tema «Lógica proposicional».', cu: 'CU-1',
      accion: { buscar: 'lógica', destino: K.logica, pestana: 'pc6', texto: 'Escribe «lógica» en el buscador y elige el tema. Como no necesita nada de fuera, la pantalla lo dice y abre su ficha.' } },
    { titulo: 'Mira qué contiene, en qué orden conviene aprenderlo y su material de estudio.', cu: 'CU-6 · CU-7',
      accion: { destino: K.logica, pestana: 'pc4', ficha: K.logica, texto: 'Pestaña «Qué contiene y en qué orden»: el mapa agrupa sus conceptos en pasos; la ficha de la derecha muestra el material de estudio.' } },
    { titulo: 'Abre «Contradicción»: ¿qué necesitas saber antes?', cu: 'CU-3',
      accion: { destino: K.contradiccion, grano: 'topic', texto: 'Tres conceptos de partida confluyen en «Tabla de verdad», que es directo; las indicaciones repiten el camino como lista.' } },
    { titulo: '¿De dónde sale que «Contradicción» requiere «Tabla de verdad»? Ver la fuente.', cu: 'CU-10',
      accion: { destino: K.contradiccion, grano: 'topic', tramo: K.tabla + '>' + K.contradiccion, texto: 'Es el «?» del último tramo: cada relación lleva su fuente, y «Ver fuente» abre el sílabo.' } },
    { titulo: 'El camino hasta «Entrada y salida de datos desde archivos», visto por cursos.', cu: 'CU-8',
      accion: { destino: K.archivosES, grano: 'course', texto: '«Ver por: curso». «Archivos» es un transbordo: se enseña en INF144 y en 1INF35.' } },
    { titulo: '«Técnicas de Programación»: qué pide y qué curso conviene llevar antes.', cu: 'CU-4',
      accion: { destino: K.inf144, pestana: 'pc2', ficha: K.inf144, texto: 'Pide tres conceptos que enseña 1INF01, que es el curso que conviene llevar antes. La ficha lista lo que pide y lo que enseña.' } }
  ];

  const RELACION = {
    'PART_OF:out': 'Es parte de', 'PART_OF:in': 'Contiene',
    'HAS_PREREQUISITE:out': 'Requiere', 'HAS_PREREQUISITE:in': 'Lo necesitan antes',
    'TEACHES_CONCEPT:in': 'Lo enseña', 'TEACHES_CONCEPT:out': 'Lo que enseña',
    'REQUIRES_CONCEPT:in': 'Lo pide el curso', 'REQUIRES_CONCEPT:out': 'Lo que pide',
    'SPECIALIZES:out': 'Es un tipo de', 'SPECIALIZES:in': 'Tipos',
    'IS_ABOUT:in': 'Material que trata sobre esto', 'IS_ABOUT:out': 'Trata sobre',
    'HAS_RESOURCE_TYPE:out': 'Tipo de material', 'HAS_RESOURCE_TYPE:in': 'Material de este tipo'
  };
  const ORDEN_RELACION = ['HAS_PREREQUISITE:out', 'HAS_PREREQUISITE:in', 'PART_OF:out', 'PART_OF:in', 'TEACHES_CONCEPT:in', 'REQUIRES_CONCEPT:in',
    'SPECIALIZES:out', 'SPECIALIZES:in', 'TEACHES_CONCEPT:out', 'REQUIRES_CONCEPT:out', 'IS_ABOUT:in', 'IS_ABOUT:out', 'HAS_RESOURCE_TYPE:out', 'HAS_RESOURCE_TYPE:in'];

  let metro = null;

  function caminosAscendentes(resp, key) {
    const by = M.indice(resp);
    const sale = {};
    resp.edges.forEach(function (e) { if (e.type === 'PART_OF') (sale[e.source] = sale[e.source] || []).push(e); });
    const out = [];
    (function rec(k, acc) {
      const es = sale[k] || [];
      if (!es.length) { out.push(acc.slice().reverse()); return; }
      es.forEach(function (e) { if (acc.length < 6) rec(e.target, acc.concat([{ nodo: by[e.target], arista: e }])); });
    })(key, [{ nodo: by[key], arista: null }]);
    return out;
  }

  createApp({
    data() {
      return {
        pantalla: 'inicio',
        consulta: '', resultados: [], busquedaSimulada: false, mostrarResultados: false, buscando: false,
        destinos: [], cursos: [], areas: [], destinosSimulados: false, traza: false,
        destino: null, pestana: 'pc6', grano: 'topic', modelo: null, cargando: false, extraVacia: null,
        seleccion: null, ficha: null, pilaFichas: [], cargandoFicha: false,
        evidencia: null,
        recorridoAbierto: true, recorrido: RECORRIDO, pasoRecorrido: 0,
        leyendaAbierta: false, cs2023: null, verEnsena: false, verSinOrden: false,
        GRANOS: [
          { id: 'topic', nombre: 'tema', ayuda: 'Cada línea es un tema de los sílabos.' },
          { id: 'course', nombre: 'curso', ayuda: 'Cada línea es un curso que enseña esos conceptos.' },
          { id: 'area', nombre: 'área', ayuda: 'Cada línea es un área de CS2023.' }
        ]
      };
    },

    computed: {
      destinosTemas() { return this.destinos.filter(function (d) { return d.label === 'Topic'; }); },
      destinosConceptos() { return this.destinos.filter(function (d) { return d.label === 'Concept'; }); },
      destinosCruzan() { return this.destinos.filter(function (d) { return d.courses.length > 1 || d.areas.length > 1; }); },
      clavesConRuta() { const m = {}; this.destinos.forEach(function (d) { m[d.key] = true; }); return m; },
      pestanas() {
        if (!this.destino) return [];
        const l = this.destino.label;
        const camino = { id: 'pc6', nombre: 'Camino hasta la meta', traza: 'CU-8 · PC6 · RF-15' };
        if (l === 'Course') return [{ id: 'pc2', nombre: 'Cursos que conviene llevar antes', traza: 'CU-4 · PC2 · RF-12' }, camino];
        if (l === 'Concept') return [camino];
        if (l === 'Topic' || l === 'KnowledgeUnit' || l === 'KnowledgeArea') return [camino, { id: 'pc4', nombre: 'Qué contiene y en qué orden', traza: 'CU-6 · PC4 · RF-13' }];
        return [];
      },
      tituloLineas() {
        if (!this.modelo) return '';
        if (this.modelo.tipo === 'pc2') return 'Cursos que enseñan lo que pide';
        if (this.modelo.tipo === 'pc4') return this.destino.label === 'Topic' ? 'Línea del tema' : 'Temas con un orden';
        return 'Líneas del camino · por ' + M.GRANO[this.grano].nombre.toLowerCase();
      },
      resumen() {
        const m = this.modelo;
        if (!m || m.vacia) return '';
        if (m.tipo === 'pc2') {
          const cursos = m.lineas.map(function (l) { return l.codigo; }).join(' y ');
          return 'Su sílabo pide ' + m.requeridas.length + ' conceptos que enseña ' + cursos + ': ese es el curso que conviene llevar antes.';
        }
        if (m.tipo === 'pc4') return m.estaciones.length + ' conceptos que los sílabos piden unos antes que otros, en ' + m.pasos.length + ' pasos.';
        const previos = m.estaciones.filter(function (s) { return s.depth > 0; }).length;
        const n = m.lineas.length;
        return previos + (previos === 1 ? ' concepto que conviene saber antes' : ' conceptos que conviene saber antes') + (m.maxDepth === 1 ? ', todos directos' : ', hasta a ' + m.maxDepth + ' pasos') +
          ', en ' + n + ' ' + (n === 1 ? M.GRANO[this.grano].nombre.toLowerCase() : M.GRANO[this.grano].plural) + '.';
      },
      lineasPorKey() { const m = {}; (this.modelo ? this.modelo.lineas : []).forEach(function (l) { m[l.key] = l; }); return m; }
    },

    methods: {
      /* ---------- utilidades de vista ---------- */
      etiqueta(n) { if (!n) return ''; if (n.label === 'LearningResource') return n.layer === 'reference' ? 'Documento' : 'Sílabo'; return M.ETIQUETA[n.label] || n.label; },
      esRef(n) { return n && n.layer === 'reference'; },
      capa(n) { return this.esRef(n) ? 'CS2023' : 'Sílabo PUCP'; },
      codigoArea(k) { return M.codigoArea(k); },
      verAreas() { this.mostrarResultados = false; if (this.pantalla !== 'inicio') this.volverInicio(); this.$nextTick(function () { const el = document.getElementById('areas'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }); },
      codigoFuente(r) { return M.codigoFuente(r); },
      pasosTexto(d) { return d === 1 ? 'directo' : 'a ' + d + ' pasos'; },
      lineaDe(k) { return this.lineasPorKey[k]; },
      nombres(lista) { return (lista || []).map(function (n) { return n ? n.name_es : ''; }).join(', '); },
      nombresLineas(s) { return s.lineas.map((k) => this.lineasPorKey[k].nombre).join(' y '); },
      esDestinable(n) { return n && ['Concept', 'Topic', 'KnowledgeUnit', 'KnowledgeArea', 'Course'].indexOf(n.label) >= 0; },
      colorCurso(c) { return M.COLOR_CURSO[c] || '#15171C'; },
      abrirPdf(r) { if (r && r.locator) window.open(r.locator, '_blank', 'noopener'); },

      /* ---------- búsqueda ---------- */
      async alBuscar() {
        const q = this.consulta;
        if (!q.trim()) { this.resultados = []; this.mostrarResultados = false; return; }
        this.buscando = true;
        const r = await buscar(q);
        if (q !== this.consulta) return;
        this.resultados = r.nodes.filter(function (n) { return n.label !== 'LearningResource' && n.label !== 'ResourceType'; });
        this.busquedaSimulada = r.simulada;
        this.mostrarResultados = true;
        this.buscando = false;
      },
      elegirResultado(n) { this.mostrarResultados = false; this.consulta = ''; this.abrirDestino(n.key); },
      sugerir(q) { this.consulta = q; this.alBuscar(); },
      enterBusqueda() { if (this.resultados.length) this.elegirResultado(this.resultados[0]); },

      /* ---------- destino y ruta ---------- */
      async abrirDestino(key, op) {
        op = op || {};
        const det = await api('/api/nodes', { key: key });
        const n = det.nodes[0];
        if (n.label === 'LearningResource' || n.label === 'ResourceType') { this.abrirFicha(key); return; }
        this.destino = n;
        this.pantalla = 'ruta';
        this.pestana = op.pestana || (n.label === 'Course' ? 'pc2' : (n.label === 'KnowledgeArea' || n.label === 'KnowledgeUnit' ? 'pc4' : 'pc6'));
        if (op.grano) this.grano = op.grano;
        this.ficha = null; this.pilaFichas = []; this.seleccion = null; this.evidencia = null;
        this.verEnsena = false; this.verSinOrden = false;
        await this.cargarModelo();
        window.scrollTo(0, 0);
      },
      async cambiarPestana(id) { this.pestana = id; this.ficha = null; this.seleccion = null; await this.cargarModelo(); },
      async cambiarGrano(id) { this.grano = id; await this.cargarModelo(true); },
      async cargarModelo(mantenerSeleccion) {
        const d = this.destino; if (!d) return;
        this.cargando = true; this.extraVacia = null;
        let modelo = null;
        try {
          if (this.pestana === 'pc2') {
            modelo = M.rutaEntreCursos(await api('/api/courses/prerequisites', { key: d.key }), d.key);
          } else if (this.pestana === 'pc4') {
            modelo = M.ordenInterno(await api('/api/elements/location', { key: d.key }), d.key);
          } else {
            modelo = M.rutaElevada(await api('/api/learning-path', { key: d.key, grain: this.grano }), d.key, this.grano);
          }
        } catch (e) {
          modelo = { tipo: this.pestana, vacia: true, error: true, objetivo: d, estaciones: [], tramos: [], lineas: [], pasos: [] };
        }
        this.modelo = markRaw(modelo);
        if (modelo.vacia) { await this.prepararVacia(modelo); if (!this.ficha) this.abrirFicha(d.key); }
        this.cargando = false;
        if (!mantenerSeleccion) { this.seleccion = null; }
        await nextTick();
        this.dibujar();
      },
      async prepararVacia(modelo) {
        const d = this.destino; const extra = {};
        if (modelo.tipo === 'pc6' && d.label === 'Concept') {
          const det = await api('/api/nodes', { key: d.key });
          const by = M.indice(det);
          extra.base = det.edges.filter(function (e) { return e.type === 'HAS_PREREQUISITE' && e.target === d.key; })
            .map(function (e) { return by[e.source]; }).filter(Boolean);
        }
        if (modelo.tipo === 'pc6' && (d.label === 'Topic' || d.label === 'KnowledgeUnit' || d.label === 'KnowledgeArea')) {
          try {
            const pc4 = M.ordenInterno(await api('/api/elements/location', { key: d.key }), d.key);
            extra.conOrden = !pc4.vacia;
            extra.temas = pc4.temas; extra.conceptos = pc4.conceptos.length;
          } catch (e) { extra.conOrden = false; }
        }
        if (modelo.tipo === 'pc6' && d.label === 'Course') {
          const pc2 = M.rutaEntreCursos(await api('/api/courses/prerequisites', { key: d.key }), d.key);
          extra.pc2 = !pc2.vacia;
        }
        this.extraVacia = extra;
      },
      dibujar() {
        if (!this.modelo || this.modelo.vacia || this.pantalla !== 'ruta') return;
        if (!metro) {
          metro = window.IEKG_METRO.crear(document.getElementById('mapa'), {
            onEstacion: (k) => this.abrirFicha(k),
            onTramo: (t) => this.evidenciaTramo(t),
            onLinea: (l) => this.evidenciaLinea(l)
          });
        }
        metro.dibujar(this.modelo, M.disponer(this.modelo), this.seleccion);
      },
      encajar() { metro && metro.encajar(); },
      acercar(f) { metro && metro.acercar(f); },
      volverInicio() { this.pantalla = 'inicio'; this.destino = null; this.modelo = null; this.ficha = null; this.evidencia = null; if (metro) metro.limpiar(); window.scrollTo(0, 0); },

      /* ---------- evidencia ---------- */
      evidenciaTramo(t) {
        const by = M.indice(this.modelo.resp);
        const titulo = M.nombre(by[t.desde]) + ' → ' + M.nombre(by[t.hasta]);
        const lineas = t.lineas.map((k) => this.lineasPorKey[k]);
        let sub;
        if (this.modelo.tipo === 'pc2') sub = 'El sílabo del curso meta pide este concepto, y otro curso lo enseña.';
        else if (lineas.length) sub = 'Tramo de la línea ' + lineas.map(function (l) { return l.insignia + ' (' + l.nombre + ')'; }).join(' y ') + '.';
        else sub = 'Cambio de línea: los dos extremos no comparten ' + M.GRANO[this.modelo.modo].nombre.toLowerCase() + '.';
        const traza = this.modelo.tipo === 'pc2' ? 'CU-4 · CU-10 · RF-21' : (this.modelo.tipo === 'pc4' ? 'CU-6 · CU-10 · RF-21' : 'CU-3 · CU-8 · CU-10 · RF-21');
        this.evidencia = { titulo: titulo, subtitulo: sub, items: M.evidenciaTramo(this.modelo, t, this.cs2023), lineas: lineas, traza: traza };
      },
      evidenciaPaso(i) {
        const p = this.modelo.pasos[i];
        const tramos = this.modelo.tramos.filter((t) => p.estaciones.some(function (s) { return s.key === t.desde; }));
        let items = [];
        tramos.forEach((t) => { items = items.concat(M.evidenciaTramo(this.modelo, t, this.cs2023)); });
        const visto = {};
        items = items.filter(function (x) { if (visto[x.id]) return false; visto[x.id] = true; return true; });
        this.evidencia = { titulo: p.titulo + ' → ' + (this.modelo.pasos[i + 1] ? this.modelo.pasos[i + 1].titulo : ''), subtitulo: 'Todas las relaciones que unen este paso con el siguiente, cada una con su fuente.', items: items, lineas: [], traza: 'CU-8 · CU-10 · RF-21' };
      },
      evidenciaLinea(l) {
        let sub;
        if (this.modelo.tipo === 'pc2') sub = l.codigo + ' enseña conceptos que pide el curso meta.';
        else if (this.modelo.tipo === 'pc4') sub = 'Conceptos de esta línea que tienen un orden.';
        else sub = 'Está en el camino porque contiene o enseña algo que conviene saber antes de la meta; lo más cercano ' + (l.depth === 1 ? 'es directo' : 'está a ' + l.depth + ' pasos') + '.';
        this.evidencia = { titulo: 'Línea ' + l.insignia + ' · ' + l.nombre, subtitulo: sub, items: M.evidenciaLinea(this.modelo, l, this.cs2023), lineas: [l], linea: l, traza: 'CU-8 · CU-10 · PC6 · RF-21' };
      },
      cerrarEvidencia() { this.evidencia = null; },

      /* ---------- ficha de estación ---------- */
      async abrirFicha(key, apilar) {
        if (apilar && this.ficha) this.pilaFichas.push(this.ficha.key);
        if (!apilar) this.pilaFichas = [];
        this.cargandoFicha = true;
        this.seleccion = key;
        if (metro) metro.seleccionar(key);
        try { this.ficha = markRaw(await this.construirFicha(key)); } finally { this.cargandoFicha = false; }
      },
      fichaAtras() {
        const k = this.pilaFichas.pop();
        if (k) { this.abrirFicha(k, false); } else this.cerrarFicha();
      },
      cerrarFicha() { this.ficha = null; this.pilaFichas = []; this.seleccion = null; if (metro) metro.seleccionar(null); },
      async construirFicha(key) {
        const det = await api('/api/nodes', { key: key });
        const n = det.nodes[0];
        const by = M.indice(det);
        const cs = this.cs2023;
        const f = { key: key, nodo: n, procedencia: M.procedencia(det, key), grupos: [], ubicaciones: [], recursos: null, recursosTema: [], especial: null, prerrequisitos: null, curso: null, estacion: null };
        if (this.modelo && !this.modelo.vacia) f.estacion = this.modelo.estaciones.find(function (s) { return s.key === key; }) || null;

        // RF-19: vecinos directos agrupados por relación, con el sílabo de cada arista (RF-21)
        const grupos = {};
        det.edges.forEach(function (e) {
          if (e.type === 'WAS_DERIVED_FROM') return;
          let dir = null; let otro = null;
          if (e.source === key) { dir = 'out'; otro = e.target; } else if (e.target === key) { dir = 'in'; otro = e.source; }
          if (!dir || !by[otro]) return;
          const id = e.type + ':' + dir;
          (grupos[id] = grupos[id] || []).push({ nodo: by[otro], fuente: M.fuenteDeArista(det, e, cs), mas: !!by[otro].more_neighbors });
        });
        f.grupos = ORDEN_RELACION.filter(function (id) { return grupos[id]; }).map(function (id) {
          return { id: id, titulo: RELACION[id], items: grupos[id].sort(function (a, b) { return M.nombre(a.nodo).localeCompare(M.nombre(b.nodo), 'es'); }) };
        });

        // PC3: ubicación
        if (['Concept', 'Topic', 'KnowledgeUnit', 'KnowledgeArea'].indexOf(n.label) >= 0) {
          try {
            const loc = await api('/api/elements/location', { key: key });
            f.ubicaciones = caminosAscendentes(loc, key).map(function (c) {
              return c.map(function (p) { return { nodo: p.nodo, fuente: p.arista ? M.fuenteDeArista(loc, p.arista, cs) : null }; });
            });
            f.temasPadre = loc.edges.filter(function (e) { return e.type === 'PART_OF' && e.source === key; }).map(function (e) { return e.target; });
          } catch (e) { /* 404: sin ubicación */ }
        }
        // PC5: recursos
        try {
          const rr = await api('/api/elements/resources', { key: key });
          f.recursos = this.recursosDe(rr);
          if (!f.recursos.length && n.label === 'Concept' && f.temasPadre) {
            for (const t of f.temasPadre) {
              try {
                const rt = await api('/api/elements/resources', { key: t });
                f.recursosTema.push({ tema: M.indice(rt)[t], recursos: this.recursosDe(rt) });
              } catch (e) { /* sin recursos */ }
            }
          }
        } catch (e) { f.recursos = null; }
        // PC7 y PC1
        if (n.label === 'Concept') {
          try {
            const sp = await api('/api/concepts/specializations', { key: key });
            const spBy = M.indice(sp);
            const arriba = []; const abajo = [];
            const sube = {}; const baja = {};
            sp.edges.forEach(function (e) { if (e.type === 'SPECIALIZES') { (sube[e.source] = sube[e.source] || []).push(e); (baja[e.target] = baja[e.target] || []).push(e); } });
            (function rec(k, v) { (sube[k] || []).forEach(function (e) { if (!v[e.target]) { v[e.target] = 1; arriba.push({ nodo: spBy[e.target], fuente: M.fuenteDeArista(sp, e, cs) }); rec(e.target, v); } }); })(key, {});
            (function rec(k, v) { (baja[k] || []).forEach(function (e) { if (!v[e.source]) { v[e.source] = 1; abajo.push({ nodo: spBy[e.source], fuente: M.fuenteDeArista(sp, e, cs) }); rec(e.source, v); } }); })(key, {});
            if (arriba.length || abajo.length) f.especial = { arriba: arriba, abajo: abajo };
          } catch (e) { /* sin especializaciones */ }
          try {
            const pr = await api('/api/concepts/prerequisites', { key: key });
            f.prerrequisitos = pr.nodes.filter(function (x) { return x.label === 'Concept' && x.depth > 0; })
              .sort(function (a, b) { return (a.depth - b.depth) || a.name_es.localeCompare(b.name_es, 'es'); });
          } catch (e) { f.prerrequisitos = []; }
        }
        if (n.label === 'Course') {
          const pc2 = await api('/api/courses/prerequisites', { key: key });
          const m = M.rutaEntreCursos(pc2, key);
          f.curso = { ensena: m.ensena.length, ensenaLista: m.ensena, requiere: m.vacia ? [] : m.estaciones.filter(function (s) { return !s.destino; }).map(function (s) {
            return { nodo: s.nodo, cursos: s.lineas.map(function (k) { return M.indice(pc2)[k].course_code; }) };
          }) };
        }
        return f;
      },
      recursosDe(rr) {
        const by = M.indice(rr);
        const porRecurso = {};
        rr.edges.forEach(function (e) {
          if (e.type === 'IS_ABOUT') (porRecurso[e.source] = porRecurso[e.source] || { recurso: by[e.source], sobre: [], tipo: null }).sobre.push(by[e.target]);
        });
        rr.edges.forEach(function (e) {
          if (e.type === 'HAS_RESOURCE_TYPE' && porRecurso[e.source]) porRecurso[e.source].tipo = by[e.target];
        });
        return Object.keys(porRecurso).map(function (k) { return porRecurso[k]; });
      },

      /* ---------- recorrido sugerido ---------- */
      async irPaso(i) {
        if (i < 0 || i >= this.recorrido.length) return;
        this.pasoRecorrido = i;
        const a = this.recorrido[i].accion;
        await this.abrirDestino(a.destino, { grano: a.grano, pestana: a.pestana });
        this.consulta = a.buscar || '';
        if (a.tramo) {
          const t = this.modelo.tramos.find(function (x) { return x.id === a.tramo; });
          if (t) this.evidenciaTramo(t);
        }
        if (a.ficha) await this.abrirFicha(a.ficha);
      }
    },

    async mounted() {
      try { this.cs2023 = (await api('/api/nodes', { key: M.CS2023_KEY })).nodes[0]; } catch (e) { this.cs2023 = null; }
      const t = await api('/api/learning-path/targets');
      this.destinos = t.targets; this.destinosSimulados = !!t._simulado;
      try { this.areas = (await api('/api/areas')).nodes; } catch (e) { this.areas = []; }
      const c = await api('/api/courses');
      const cursos = [];
      for (const n of c.nodes) {
        const m = M.rutaEntreCursos(await api('/api/courses/prerequisites', { key: n.key }), n.key);
        cursos.push({ nodo: n, ensena: m.ensena.length, previos: m.vacia ? [] : m.lineas.map(function (l) { return { codigo: l.codigo, color: l.color }; }), requeridos: m.vacia ? 0 : m.requeridas.length });
      }
      cursos.sort(function (a, b) { return String(a.nodo.course_code).localeCompare(String(b.nodo.course_code)); });
      this.cursos = cursos;
      window.addEventListener('resize', () => { if (metro) metro.encajar(); });
      // Enlaces directos (también sirven para capturar los wireframes):
      //   #paso=N                                 abre el paso N del recorrido
      //   #destino=<clave>&grano=area&pestana=pc4 abre un destino; en R6 lo haría el enrutador
      const h = new URLSearchParams(location.hash.slice(1));
      if (h.get('recorrido') === 'no') this.recorridoAbierto = false;
      if (h.get('traza') === 'si') this.traza = true;
      if (h.get('paso') && this.recorrido[+h.get('paso') - 1]) await this.irPaso(+h.get('paso') - 1);
      else if (h.get('destino')) {
        await this.abrirDestino(h.get('destino'), { grano: h.get('grano') || undefined, pestana: h.get('pestana') || undefined });
        if (h.get('ficha')) await this.abrirFicha(h.get('ficha'));
      } else if (h.get('buscar')) { this.consulta = h.get('buscar'); await this.alBuscar(); }
      document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') { if (this.evidencia) this.evidencia = null; else if (this.ficha) this.cerrarFicha(); } });
    }
  }).mount('#app');
})();
