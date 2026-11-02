// Aplicación de la maqueta P2: Vue 3 + Vue Router en su variante sin
// compilación (build global desde CDN). En R6 cada componente pasa a un
// archivo .vue y se compila con Vite (ver adr/P2-0016).
(function () {
  'use strict';

  const { createApp, reactive } = Vue;
  const { createRouter, createWebHashHistory } = VueRouter;
  const { api, busquedasCapturadas } = IEKG_API;
  const M = IEKG_MODELO;

  const aFicha = (clave) => ({ path: '/ficha', query: { key: clave } });
  const clase = (label) => M.CLASES[label] || { nombre: label, corto: label, plural: label };

  const DEMO = {
    contradiccion: 'ce8cd4d1-77f1-4ec1-b10f-d8b87dabe678',
    tablaDeVerdad: '29a47e34-1d18-4962-9501-c4f5b960003c',
    logica: '40347f92-1123-45ef-8225-b77837c551d7',
    inf144: 'b2d9c106-684d-58b8-8462-4dc0c3b8d90c',
    archivos: '9a161bca-1a01-43de-8875-7bdfb53ebd84',
  };

  // Recorrido sugerido, común a las tres propuestas. Cada paso deja la pantalla
  // en el estado que describe; también se abre con `index.html#paso=N`.
  const PASOS = [
    { titulo: 'Busca «lógica» y abre el tema «Lógica proposicional».', cu: 'CU-1',
      accion: 'Estos son los resultados de «lógica». El tema está resaltado: ábrelo.',
      ruta: { path: '/buscar', query: { q: 'lógica', resaltar: DEMO.logica } } },
    { titulo: 'Mira qué contiene, en qué orden conviene aprenderlo y su material de estudio.', cu: 'CU-6 · CU-7',
      accion: 'En «Qué contiene y en qué orden aprenderlo», sus conceptos van en tres pasos. Más abajo, «Material de estudio».',
      ruta: { path: '/ficha', query: { key: DEMO.logica, ir: 'contiene' } } },
    { titulo: 'Abre «Contradicción»: ¿qué necesitas saber antes?', cu: 'CU-3',
      accion: '«Qué necesitas antes»: «Tabla de verdad», directo, y tres conceptos a 2 pasos.',
      ruta: { path: '/ficha', query: { key: DEMO.contradiccion, ir: 'necesitas-antes' } } },
    { titulo: '¿De dónde sale que «Contradicción» requiere «Tabla de verdad»? Ver la fuente.', cu: 'CU-10',
      accion: 'La marca ↗ 1INF01 de la fila resaltada abre el sílabo de Fundamentos de Programación.',
      ruta: { path: '/ficha', query: { key: DEMO.contradiccion, ir: 'necesitas-antes', resaltar: DEMO.tablaDeVerdad } } },
    { titulo: 'El camino hasta «Entrada y salida de datos desde archivos», visto por cursos.', cu: 'CU-8',
      accion: '«Camino hasta aquí», con «Ver por: curso»: dos cursos enseñan «Archivos», que se necesita antes.',
      ruta: { path: '/ficha', query: { key: DEMO.archivos, grano: 'course', ir: 'ruta' } } },
    { titulo: '«Técnicas de Programación»: qué pide y qué curso conviene llevar antes.', cu: 'CU-4',
      accion: '«Lo que pide» y, debajo, «Cursos que conviene llevar antes»: Fundamentos de Programación, con los tres conceptos que lo justifican.',
      ruta: { path: '/ficha', query: { key: DEMO.inf144, ir: 'asume' } } },
  ];

  function rutaDePaso(n) {
    const p = PASOS[n - 1] || PASOS[0];
    return { path: p.ruta.path, query: Object.assign({}, p.ruta.query, { paso: String(n) }) };
  }

  // Dónde se intercala el camino hasta aquí en cada clase de ficha.
  const RUTA_DESPUES = {
    Concept: 'necesitas-antes', Course: 'ensena', Topic: 'contiene', KnowledgeUnit: 'contiene', KnowledgeArea: 'contiene',
  };

  function guardado(clave, valor) {
    try {
      if (valor === undefined) return sessionStorage.getItem(clave);
      if (valor === null) sessionStorage.removeItem(clave); else sessionStorage.setItem(clave, valor);
    } catch (e) { /* sin almacenamiento: la maqueta funciona igual */ }
    return null;
  }

  // «Ver trazabilidad»: apagado por omisión. `index.html?traza#/…` lo enciende
  // (para las capturas).
  const estado = reactive({
    traza: (typeof location !== 'undefined' && /[?&]traza\b/.test(location.search)) || guardado('iekg.traza') === '1',
  });

  function irASeccion(id) {
    const el = document.getElementById(`s-${id}`);
    if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.focus({ preventScroll: true }); }
  }

  // ── Piezas pequeñas ────────────────────────────────────────────────────────

  const Traza = {
    props: ['c'],
    template: '<span v-if="$estado.traza && c" class="traza" :title="\'Trazabilidad: \' + c">{{ c }}</span>',
  };

  const Glifo = {
    props: ['capa', 'label'],
    computed: {
      tipo() { return ['LearningResource', 'ResourceType'].includes(this.label) ? 'doc' : this.capa; },
    },
    template: '<span class="glifo" :class="\'glifo--\' + tipo" aria-hidden="true"></span>',
  };

  const Insignia = {
    props: ['capa', 'larga'],
    template: `
      <span class="insignia" :class="'insignia--' + capa">
        <glifo :capa="capa"/>{{ capa === 'reference' ? 'CS2023' : 'Sílabo PUCP' }}<span v-if="larga" class="insignia-capa">&nbsp;· {{ capa === 'reference' ? 'estándar internacional (ACM/IEEE)' : 'de un curso de la carrera' }}</span>
      </span>`,
  };

  const Nota = {
    props: ['nota'],
    template: `
      <a class="nota" :class="'nota--' + nota.capa" :href="nota.locator" target="_blank" rel="noopener"
         :title="'Ver fuente: ' + nota.nombre + ' (se abre en otra pestaña)'"
         :aria-label="'Ver fuente: ' + nota.nombre">{{ nota.corto }}</a>`,
  };

  const Simulado = {
    props: ['texto'],
    template: '<span class="simulado" :title="texto || \'Simulado: el sistema todavía no ofrece esto; se muestra con datos reales preparados aparte.\'">simulado</span>',
  };

  const Fila = {
    name: 'Fila',
    props: ['fila', 'abiertaInicial'],
    data() { return { abierta: !!this.abiertaInicial }; },
    computed: {
      textoSub() {
        const s = this.fila.sub || [];
        if (!s.length) return '';
        const labels = new Set(s.map((x) => x.label));
        if (labels.size !== 1) return s.length === 1 ? 'elemento' : 'elementos';
        const c = clase(s[0].label);
        return (s.length === 1 ? c.corto : c.plural).toLowerCase();
      },
      resaltada() { return this.$route.query.resaltar === this.fila.clave; },
    },
    template: `
      <li class="fila" :class="['fila--' + fila.capa, { 'fila--resaltada': resaltada }]">
        <div class="fila-linea">
          <glifo :capa="fila.capa" :label="fila.label"/>
          <router-link class="fila-nombre" :to="$aFicha(fila.clave)">{{ fila.nombre }}</router-link>
          <span class="fila-clase">{{ $clase(fila.label).corto }}</span>
          <span v-if="fila.nombreEn" class="fila-en" lang="en">{{ fila.nombreEn }}</span>
          <span v-if="fila.notas && fila.notas.length" class="fila-notas"><nota v-for="n in fila.notas" :key="n.clave" :nota="n"/></span>
        </div>
        <div v-if="fila.detalle" class="fila-detalle">{{ fila.detalle }}</div>
        <p v-if="resaltada && fila.notas && fila.notas.length" class="fila-aviso">
          Fuente: <b>{{ fila.notas[0].nombre }}</b>. Pulsa la marca <span class="nota" :class="'nota--' + fila.notas[0].capa">{{ fila.notas[0].corto }}</span> para abrir el documento.
        </p>
        <a v-if="fila.enlace" class="boton-doc" :href="fila.enlace" target="_blank" rel="noopener">{{ fila.textoEnlace }} <span aria-hidden="true">↗</span></a>
        <template v-if="fila.sub && fila.sub.length">
          <button class="fila-abrir" type="button" @click="abierta = !abierta" :aria-expanded="abierta ? 'true' : 'false'">
            <span aria-hidden="true">{{ abierta ? '−' : '+' }}</span> {{ abierta ? 'Ocultar' : 'Ver' }} {{ fila.sub.length }} {{ textoSub }}
          </button>
          <ul v-if="abierta" class="fila-sub"><fila v-for="s in fila.sub" :key="s.clave" :fila="s"/></ul>
        </template>
      </li>`,
  };

  const Grupo = {
    props: ['grupo'],
    data() { return { todo: false, limite: 8 }; },
    computed: {
      visibles() { return this.todo ? this.grupo.filas : this.grupo.filas.slice(0, this.limite); },
    },
    template: `
      <div class="grupo" :class="{ 'grupo--tenue': grupo.tenue }">
        <h3 v-if="grupo.titulo" class="grupo-titulo">
          <router-link v-if="grupo.clave" :to="$aFicha(grupo.clave)">{{ grupo.titulo }}</router-link><template v-else>{{ grupo.titulo }}</template>
          <span class="grupo-n">{{ grupo.filas.length }}</span>
        </h3>
        <ul class="filas"><fila v-for="f in visibles" :key="f.clave" :fila="f" :abierta-inicial="grupo.abierta"/></ul>
        <button v-if="grupo.filas.length > limite" class="mas" type="button" @click="todo = !todo">
          {{ todo ? 'Mostrar menos' : 'Mostrar los ' + (grupo.filas.length - limite) + ' restantes' }}
        </button>
      </div>`,
  };

  const Seccion = {
    props: ['s'],
    template: `
      <section class="seccion" :id="'s-' + s.id" tabindex="-1" :aria-labelledby="'t-' + s.id">
        <header class="seccion-cabecera">
          <h2 :id="'t-' + s.id">{{ s.titulo }}</h2>
          <traza :c="s.traza"/>
        </header>
        <p v-if="s.ayuda" class="seccion-ayuda">{{ s.ayuda }}
          <router-link v-if="s.desdeTema" :to="$aFicha(s.desdeTema.clave)">Ir al tema →</router-link></p>
        <p v-if="s.vacio" class="vacio">{{ s.vacio }}</p>
        <grupo v-for="(g, i) in s.grupos" :key="i" :grupo="g"/>
      </section>`,
  };

  const SeccionRuta = {
    props: ['clave', 'label'],
    data() {
      // El agrupamiento va en la URL (`&grano=course`): el camino elegido se puede enlazar.
      const pedido = this.$route.query.grano;
      const grano = M.GRANOS[pedido] ? pedido : (this.label === 'Course' ? 'course' : 'topic');
      return { grano, ruta: null, error: null, granos: M.GRANOS, demo: DEMO.archivos };
    },
    watch: {
      clave() { this.cargar(); },
      grano(g) {
        this.cargar();
        if (this.$route.query.grano !== g) this.$router.replace({ query: Object.assign({}, this.$route.query, { grano: g }) });
      },
      '$route.query.grano'(g) { if (g && M.GRANOS[g]) this.grano = g; },
    },
    mounted() { this.cargar(); },
    methods: {
      async cargar() {
        this.ruta = null;
        this.error = null;
        try { this.ruta = await M.construirRuta(api, this.clave, this.grano); } catch (e) { this.error = e; }
      },
      ir: irASeccion,
    },
    template: `
      <section class="seccion seccion-ruta" id="s-ruta" tabindex="-1" aria-labelledby="t-ruta">
        <header class="seccion-cabecera">
          <h2 id="t-ruta">Camino hasta aquí</h2>
          <traza c="CU-8 · PC6 · RF-15"/>
        </header>
        <p class="seccion-ayuda">Lo que conviene aprender antes de llegar aquí, agrupado como elijas. Debajo de cada paso, el concepto que lo justifica y su fuente.</p>
        <div class="granos" role="radiogroup" aria-label="Ver el camino por">
          <span class="granos-rotulo">Ver por</span>
          <button v-for="(g, k) in granos" :key="k" type="button" role="radio" :aria-checked="grano === k ? 'true' : 'false'"
                  :class="{ activo: grano === k }" @click="grano = k">{{ g.etiqueta.toLowerCase() }}</button>
        </div>
        <p v-if="error" class="vacio">No se pudo calcular el camino hasta aquí.</p>
        <div v-else-if="ruta && ruta.vacia" class="vacio">
          <template v-if="label === 'Course'">El camino hasta este curso sale vacío: lo que necesitan sus conceptos se enseña dentro del mismo curso. Para saber qué curso conviene llevar antes, mira <button type="button" class="enlace-texto" @click="ir('cursos-previos')">«Cursos que conviene llevar antes»</button>.</template>
          <template v-else>No hay nada registrado que convenga aprender antes, fuera de esto mismo: se puede empezar por aquí.</template>
          <span class="vacio-sugerencia">Un camino que pasa por varios cursos: <router-link :to="{ path: '/ficha', query: { key: demo, grano: 'course' } }">Entrada y salida de datos desde archivos</router-link>.</span>
        </div>
        <ol v-else-if="ruta" class="etapas">
          <li v-for="e in ruta.etapas" :key="e.profundidad" class="etapa">
            <div class="etapa-titulo">{{ e.titulo }}</div>
            <ul class="filas"><fila v-for="f in e.filas" :key="f.clave" :fila="f" :abierta-inicial="true"/></ul>
          </li>
          <li class="etapa etapa--objetivo">
            <div class="etapa-titulo">Aquí</div>
            <div class="objetivo"><glifo :capa="ruta.objetivo.capa" :label="ruta.objetivo.label"/>{{ ruta.objetivo.nombre }}</div>
          </li>
        </ol>
        <p v-else class="cargando">Calculando el camino…</p>
      </section>`,
  };

  const Leyenda = {
    template: `
      <ul class="leyenda">
        <li><svg viewBox="-8 -8 16 16" aria-hidden="true"><path class="ley-ref" d="M-5,-5H5V5H-5Z"/></svg> CS2023, estándar internacional (ACM/IEEE)</li>
        <li><svg viewBox="-8 -8 16 16" aria-hidden="true"><circle class="ley-inst" r="5"/></svg> Sílabo PUCP</li>
        <li><svg viewBox="-8 -8 16 16" aria-hidden="true"><path class="ley-doc" d="M0,-6L6,0L0,6L-6,0Z"/></svg> Documento</li>
        <li><svg viewBox="0 0 26 10" aria-hidden="true"><line x1="1" y1="5" x2="20" y2="5" class="ley-pre"/><path d="M18,1L25,5L18,9" class="ley-pre-f"/></svg> necesita antes / es un tipo de</li>
        <li><svg viewBox="0 0 26 10" aria-hidden="true"><line x1="1" y1="5" x2="25" y2="5" class="ley-parte"/></svg> está dentro de</li>
        <li><svg viewBox="0 0 26 10" aria-hidden="true"><line x1="1" y1="5" x2="25" y2="5" class="ley-curso"/></svg> lo enseña / lo pide</li>
        <li><svg viewBox="-8 -8 16 16" aria-hidden="true"><circle class="ley-mas" r="6"/><circle class="ley-inst" r="3"/></svg> tiene más relaciones: su ficha las muestra</li>
      </ul>`,
  };

  const MiniMapa = {
    props: ['detalle'],
    data() { return { info: null }; },
    mounted() { this.pintar(); },
    watch: { detalle() { this.pintar(); } },
    methods: {
      pintar() {
        this.$nextTick(() => {
          this.info = IEKG_MINIMAPA.dibujar(this.$refs.svg, this.detalle, { grande: false, alElegir: (k) => this.$router.push(aFicha(k)) });
        });
      },
      abrir() {
        const d = this.$refs.dialogo;
        if (d.showModal) d.showModal(); else d.setAttribute('open', '');
        this.$nextTick(() => IEKG_MINIMAPA.dibujar(this.$refs.svgGrande, this.detalle, {
          grande: true,
          alElegir: (k) => { this.cerrar(); this.$router.push(aFicha(k)); },
        }));
      },
      cerrar() { const d = this.$refs.dialogo; if (d.close) d.close(); else d.removeAttribute('open'); },
    },
    template: `
      <figure class="minimapa caja">
        <figcaption class="caja-cabecera">
          <span class="caja-titulo">Mapa: lo que lo rodea <traza c="CU-2 · RF-19"/></span>
          <button type="button" class="boton-mini" @click="abrir">Agrandar <span aria-hidden="true">⤢</span></button>
        </figcaption>
        <svg ref="svg" class="mm-svg" role="img" :aria-label="'Mapa con ' + (info ? info.nodos : 0) + ' elementos alrededor de ' + detalle.nodes[0].name_es + '. Las mismas relaciones están escritas en las secciones de la ficha.'"></svg>
        <p class="mm-pie">{{ info ? info.nodos : 0 }} elementos · cuadrado: CS2023 · círculo: sílabo · clic para abrir su ficha</p>
        <dialog ref="dialogo" class="dialogo-mapa" aria-labelledby="titulo-mapa" @click.self="cerrar">
          <div class="dialogo-interior">
            <header class="dialogo-cabecera">
              <h2 id="titulo-mapa">Lo que rodea a «{{ detalle.nodes[0].name_es }}»</h2>
              <button type="button" class="boton-mini" @click="cerrar">Cerrar <span aria-hidden="true">×</span></button>
            </header>
            <svg ref="svgGrande" class="mm-svg-grande" role="img" aria-label="Mapa ampliado. La rueda o el pellizco acercan; Tab recorre los elementos y Enter abre su ficha."></svg>
            <footer class="dialogo-pie"><leyenda/><span class="tenue">Se muestran hasta 25 vecinos y algunos vecinos de cada uno. Los documentos están en «Fuentes de esta ficha».</span></footer>
          </div>
        </dialog>
      </figure>`,
  };

  const Buscador = {
    props: ['grande'],
    data() { return { q: (this.$route.query.q || ''), id: `q${Math.random().toString(36).slice(2, 7)}` }; },
    watch: { '$route.query.q'(v) { this.q = v || ''; } },
    methods: {
      enviar() { const q = this.q.trim(); if (q) this.$router.push({ path: '/buscar', query: { q } }); },
    },
    template: `
      <form class="buscador" :class="{ 'buscador--grande': grande }" role="search" @submit.prevent="enviar">
        <label class="sr" :for="id">Buscar en el catálogo</label>
        <input :id="id" v-model="q" type="search" placeholder="Busca un concepto, tema, curso o área…" autocomplete="off">
        <button type="submit">Buscar</button>
      </form>`,
  };

  // ── Vistas ─────────────────────────────────────────────────────────────────

  const VistaPortada = {
    data() { return { catalogo: null, sugerencias: ['redes', 'lógica', 'INF144', 'puntero', 'subred', 'árbol'] }; },
    computed: {
      conContenido() { return this.catalogo ? this.catalogo.areas.filter((a) => a.topics > 0).sort((a, b) => b.concepts - a.concepts) : []; },
      soloCs() { return this.catalogo ? this.catalogo.areas.filter((a) => a.topics === 0).sort((a, b) => a.name_es.localeCompare(b.name_es, 'es')) : []; },
      cursos() { return this.catalogo ? this.catalogo.courses.slice().sort((a, b) => a.code.localeCompare(b.code)) : []; },
      maxConceptos() { return Math.max(1, ...this.conContenido.map((a) => a.concepts)); },
    },
    watch: { '$route.query.ver'() { this.desplazar(); } },
    async mounted() {
      document.title = 'Catálogo del conocimiento · Ingeniería Informática';
      this.catalogo = await api('/api/catalog');
      this.desplazar();
    },
    methods: {
      desplazar() {
        const v = this.$route.query.ver;
        if (v) this.$nextTick(() => { const el = document.getElementById(v); if (el) el.scrollIntoView({ behavior: 'smooth' }); });
      },
    },
    template: `
      <div class="portada">
        <section class="portada-hero">
          <p class="kicker">Ingeniería Informática · CS2023 y sílabos de la PUCP <traza c="CU-1 · RF-18 · RF-19"/></p>
          <h1>Lo que se aprende en la carrera, ficha por ficha</h1>
          <p class="hero-lede">Explora cómo se conectan los conceptos de Ingeniería Informática: qué necesitas saber antes, dónde está cada tema en la carrera y con qué material estudiarlo. Cada área, tema, concepto y curso tiene su ficha, y cada dato dice de qué documento sale.</p>
          <buscador :grande="true"/>
          <p class="sugerencias">Prueba con
            <template v-for="s in sugerencias" :key="s"><router-link :to="{ path: '/buscar', query: { q: s } }" class="chip">{{ s }}</router-link></template>
          </p>
        </section>

        <section id="cursos" class="bloque">
          <header class="bloque-cabecera">
            <h2>Cursos con sílabo cargado</h2>
            <span class="bloque-sub">{{ cursos.length }} cursos</span>
            <simulado texto="Simulado: el sistema todavía no ofrece la lista de cursos; aquí se muestra con datos reales preparados aparte."/>
            <traza c="CU-1 · CU-4"/>
          </header>
          <ul class="tarjetas tarjetas-cursos">
            <li v-for="c in cursos" :key="c.key">
              <router-link :to="$aFicha(c.key)" class="tarjeta tarjeta--institutional">
                <span class="codigo">{{ c.code }}</span>
                <span class="tarjeta-titulo">{{ c.name_es }}</span>
                <insignia capa="institutional"/>
              </router-link>
            </li>
          </ul>
        </section>

        <section id="areas" class="bloque">
          <header class="bloque-cabecera">
            <h2>Áreas de conocimiento</h2>
            <span class="bloque-sub">las 17 de CS2023, el estándar internacional del currículo de computación (ACM/IEEE)</span>
            <simulado texto="Simulado: el sistema todavía no ofrece la lista de áreas con sus cifras; aquí se muestra con datos reales preparados aparte."/>
            <traza c="CU-1 · CU-6"/>
          </header>
          <h3 class="subbloque">Con contenido de los sílabos <span class="n">{{ conContenido.length }}</span></h3>
          <ul class="tarjetas tarjetas-areas">
            <li v-for="a in conContenido" :key="a.key">
              <router-link :to="$aFicha(a.key)" class="tarjeta tarjeta--reference">
                <span class="tarjeta-titulo">{{ a.name_es }}</span>
                <span class="tarjeta-en" lang="en">{{ a.name_en }}</span>
                <span class="tarjeta-cifras"><b>{{ a.concepts }}</b> conceptos · {{ a.topics }} {{ a.topics === 1 ? 'tema' : 'temas' }} · {{ a.units }} unidades</span>
                <span class="regleta" aria-hidden="true"><span :style="{ width: (100 * a.concepts / maxConceptos) + '%' }"></span></span>
                <insignia capa="reference"/>
              </router-link>
            </li>
          </ul>
          <h3 class="subbloque">Por ahora, solo en CS2023 <span class="n">{{ soloCs.length }}</span></h3>
          <ul class="lista-compacta">
            <li v-for="a in soloCs" :key="a.key">
              <router-link :to="$aFicha(a.key)"><glifo capa="reference"/>{{ a.name_es }}<span class="tenue">{{ a.units }} unidades</span></router-link>
            </li>
          </ul>
        </section>

        <section class="bloque como-leer" aria-labelledby="t-leer">
          <h2 id="t-leer">Cómo leer el catálogo <traza c="RF-22 · RF-21"/></h2>
          <div class="como-leer-rejilla">
            <div><insignia capa="reference" :larga="true"/><p>Áreas y unidades de CS2023, el estándar internacional del currículo de computación (ACM/IEEE). Marca cuadrada y filete doble.</p></div>
            <div><insignia capa="institutional" :larga="true"/><p>Temas, conceptos y cursos que salen de los sílabos de la PUCP cargados. Marca circular y filete lateral.</p></div>
            <div><p class="como-leer-nota"><span class="nota nota--institutional" aria-hidden="true">1INF01</span> <span class="nota nota--reference" aria-hidden="true">CS2023</span></p><p>Ver fuente: junto a cada dato, una marca con el documento del que sale. Un clic lo abre en otra pestaña.</p></div>
          </div>
        </section>
      </div>`,
  };

  const VistaBusqueda = {
    data() { return { resultado: null, orden: ['Course', 'KnowledgeArea', 'KnowledgeUnit', 'Topic', 'Concept', 'LearningResource'], capturadas: busquedasCapturadas }; },
    computed: {
      q() { return this.$route.query.q || ''; },
      grupos() {
        if (!this.resultado) return [];
        return this.orden.map((label) => ({
          titulo: clase(label).plural,
          filas: this.resultado.nodes.filter((n) => n.label === label).map((n) => ({
            clave: n.key, nombre: M.nombreDe(n), label: n.label, capa: n.layer, notas: [], nombreEn: n.name_en,
            detalle: n.layer === 'reference' ? 'de CS2023' : 'de un sílabo PUCP',
          })),
        })).filter((g) => g.filas.length);
      },
    },
    watch: { '$route.query.q': { immediate: true, handler() { this.buscar(); } } },
    methods: {
      async buscar() {
        if (!this.q) { this.resultado = { nodes: [] }; return; }
        document.title = `«${this.q}» · Catálogo del conocimiento`;
        this.resultado = await api('/api/search', { q: this.q });
        if (this.$route.query.resaltar) {
          setTimeout(() => { const el = document.querySelector('.fila--resaltada'); if (el) el.scrollIntoView({ block: 'center' }); }, 80);
        }
      },
    },
    template: `
      <div class="pagina busqueda">
        <p class="kicker">Búsqueda <traza c="CU-1 · RF-18"/></p>
        <h1 class="pagina-titulo">Resultados para «{{ q }}»</h1>
        <p v-if="resultado && resultado._simulado" class="aviso-simulado"><simulado texto="Búsqueda simulada en esta maqueta"/> Este texto no está entre las búsquedas de ejemplo, así que la maqueta busca entre los nombres en tu propio navegador. El sistema real busca en todo el catálogo.</p>
        <p v-if="resultado && resultado.nodes.length" class="tenue">{{ resultado.nodes.length }} {{ resultado.nodes.length === 1 ? 'resultado' : 'resultados' }}{{ resultado.nodes.length >= 20 ? ' (se muestran como máximo 20)' : '' }}.</p>
        <div v-if="resultado && !resultado.nodes.length" class="vacio vacio--grande">
          <p><b>Ningún elemento se llama así.</b> La búsqueda recorre las 17 áreas y 162 unidades de CS2023 y lo que enseñan los 4 sílabos cargados; ninguno trata todavía «{{ q }}».</p>
          <p>Puedes recorrer las <router-link :to="{ path: '/', query: { ver: 'areas' } }">áreas de conocimiento</router-link> o probar con
            <router-link :to="{ path: '/buscar', query: { q: 'redes' } }">redes</router-link>,
            <router-link :to="{ path: '/buscar', query: { q: 'programación' } }">programación</router-link> o
            <router-link :to="{ path: '/buscar', query: { q: 'seguridad' } }">seguridad</router-link>.</p>
        </div>
        <section v-for="g in grupos" :key="g.titulo" class="seccion">
          <grupo :grupo="g"/>
        </section>
        <p class="capturadas tenue">Búsquedas de ejemplo: <template v-for="c in capturadas" :key="c"><router-link :to="{ path: '/buscar', query: { q: c } }" class="chip chip--chico">{{ c }}</router-link></template></p>
      </div>`,
  };

  const VistaFicha = {
    data() { return { ficha: null, error: null }; },
    computed: {
      rutaDespues() { return this.ficha && this.ficha.ruta ? RUTA_DESPUES[this.ficha.foco.label] : null; },
    },
    watch: {
      '$route.query.key': { immediate: true, handler(k) { this.cargar(k); } },
      '$route.query.ir'() { this.situar(); },
      '$route.query.resaltar'() { this.situar(); },
    },
    methods: {
      async cargar(k) {
        if (!k) return;
        this.error = null;
        try {
          this.ficha = await M.construirFicha(api, k);
          document.title = `${this.ficha.foco.name_es} · Catálogo del conocimiento`;
          this.situar();
        } catch (e) {
          this.error = e;
          this.ficha = null;
        }
      },
      // Lleva la vista a la sección pedida (`&ir=`) o a la fila resaltada (`&resaltar=`).
      situar() {
        const { ir, resaltar } = this.$route.query;
        if (!ir && !resaltar) return;
        setTimeout(() => {
          const fila = resaltar && document.querySelector('.fila--resaltada');
          if (fila) fila.scrollIntoView({ block: 'center' });
          else if (ir) { const el = document.getElementById(`s-${ir}`); if (el) el.scrollIntoView({ block: 'start' }); }
        }, 120);
      },
      ir: irASeccion,
    },
    template: `
      <div v-if="error" class="pagina"><p class="vacio vacio--grande">No hay ninguna ficha con esta dirección. <router-link to="/">Volver a la portada</router-link></p></div>
      <article v-else-if="ficha" class="ficha" :class="'ficha--' + ficha.foco.layer" :key="ficha.foco.key">
        <nav class="migas" aria-label="Dónde está en la carrera">
          <router-link to="/">Portada</router-link>
          <template v-for="(m, i) in ficha.migas" :key="i">
            <span class="migas-sep" aria-hidden="true">›</span>
            <router-link v-if="m.clave" :to="$aFicha(m.clave)"><glifo :capa="m.capa" :label="m.label"/>{{ m.nombre }}</router-link>
            <router-link v-else :to="{ path: '/', query: { ver: m.label === 'Course' ? 'cursos' : 'areas' } }">{{ m.nombre }}</router-link>
          </template>
          <span class="migas-sep" aria-hidden="true">›</span>
          <span aria-current="page" class="migas-actual">{{ ficha.foco.name_es }}</span>
          <traza c="CU-5 · PC3"/>
        </nav>

        <header class="ficha-cabecera">
          <div class="ficha-kicker">
            <span class="ficha-clase">{{ ficha.clase.nombre }}</span>
            <insignia :capa="ficha.foco.layer" :larga="true"/>
            <traza c="CU-2 · RF-20 · RF-22"/>
          </div>
          <h1 class="ficha-titulo"><span v-if="ficha.foco.course_code" class="codigo codigo--titulo">{{ ficha.foco.course_code }}</span>{{ ficha.foco.name_es }}</h1>
          <p v-if="ficha.foco.name_en" class="ficha-en" lang="en">{{ ficha.foco.name_en }}</p>
          <p class="ficha-lede">{{ ficha.lede }}</p>
          <div v-if="ficha.documento && ficha.documento.locator" class="documento">
            <a class="boton-primario" :href="ficha.documento.locator" target="_blank" rel="noopener">{{ ficha.foco.layer === 'reference' ? 'Ver CS2023 en la ACM' : 'Abrir el sílabo (PDF)' }} <span aria-hidden="true">↗</span></a>
            <span v-if="ficha.foco.layer !== 'reference'" class="tenue">En esta maqueta, el sílabo se abre si el sistema está corriendo en este equipo.</span>
          </div>
          <ul class="cifras" aria-label="Resumen">
            <li v-for="c in ficha.cifras" :key="c.etiqueta">
              <button type="button" @click="ir(c.ir)"><span class="cifra-valor">{{ c.valor }}</span><span class="cifra-etiqueta">{{ c.etiqueta }}</span></button>
            </li>
          </ul>
        </header>

        <div class="ficha-cuerpo">
          <div class="ficha-principal">
            <template v-for="s in ficha.secciones" :key="s.id">
              <seccion :s="s"/>
              <seccion-ruta v-if="s.id === rutaDespues" :clave="ficha.foco.key" :label="ficha.foco.label"/>
            </template>
            <section class="seccion fuentes" id="s-fuentes" tabindex="-1" aria-labelledby="t-fuentes">
              <header class="seccion-cabecera"><h2 id="t-fuentes">Fuentes de esta ficha</h2><traza c="CU-10 · RF-21"/></header>
              <p class="seccion-ayuda">Cada marca (↗) de esta ficha abre el documento del que sale el dato. En esta maqueta, los sílabos se abren si el sistema está corriendo en este equipo.</p>
              <ol class="lista-fuentes">
                <li v-for="f in ficha.fuentes" :key="f.clave">
                  <span class="nota" :class="'nota--' + f.capa" aria-hidden="true">{{ f.corto }}</span>
                  <router-link :to="$aFicha(f.clave)">{{ f.nombre }}</router-link>
                  <a v-if="f.locator" :href="f.locator" target="_blank" rel="noopener" class="enlace-externo">Ver fuente{{ f.capa === 'reference' ? ' (ACM)' : ' (PDF)' }} <span aria-hidden="true">↗</span></a>
                </li>
              </ol>
            </section>
          </div>

          <aside class="ficha-lateral" aria-label="Orientación">
            <mini-mapa :detalle="ficha.detalle"/>
            <nav class="caja indice" aria-label="En esta ficha">
              <div class="caja-cabecera"><span class="caja-titulo">En esta ficha</span></div>
              <ol>
                <template v-for="s in ficha.secciones" :key="s.id">
                  <li><button type="button" @click="ir(s.id)">{{ s.titulo }}</button></li>
                  <li v-if="s.id === rutaDespues"><button type="button" @click="ir('ruta')">Camino hasta aquí</button></li>
                </template>
                <li><button type="button" @click="ir('fuentes')">Fuentes de esta ficha</button></li>
              </ol>
            </nav>
            <div class="caja tecnica">
              <div class="caja-cabecera"><span class="caja-titulo">Datos de la ficha</span></div>
              <dl>
                <dt>Tipo</dt><dd>{{ ficha.clase.nombre }}</dd>
                <dt>Origen</dt><dd><insignia :capa="ficha.foco.layer"/></dd>
                <dt>Alrededor</dt><dd>{{ ficha.detalle.nodes.length - 1 }} elementos relacionados<span v-if="ficha.incompleto">; tiene más de los que caben, así que algunas listas pueden estar recortadas</span>.</dd>
                <template v-if="$estado.traza">
                  <dt>Clave</dt><dd><code class="clave">{{ ficha.foco.key }}</code> <span class="traza">{{ ficha.foco.label }}</span></dd>
                </template>
              </dl>
            </div>
          </aside>
        </div>
      </article>
      <p v-else class="cargando pagina">Cargando la ficha…</p>`,
  };

  const GuiaRecorrido = {
    emits: ['cerrar'],
    data() { return { pasos: PASOS, todos: false }; },
    computed: {
      actual() { const n = Number(this.$route.query.paso); return n >= 1 && n <= PASOS.length ? n : 0; },
      visibles() {
        // Con un paso en curso, el recorrido se pliega a ese paso para no tapar la ficha.
        return this.pasos.map((p, i) => ({ p, n: i + 1 })).filter((x) => this.todos || !this.actual || x.n === this.actual);
      },
    },
    watch: { actual() { this.todos = false; } },
    methods: { ir(n) { this.$router.push(rutaDePaso(n)); } },
    template: `
      <aside class="guia" aria-label="Recorrido sugerido">
        <header class="guia-cabecera"><span>Recorrido sugerido</span>
          <button type="button" class="boton-mini" @click="$emit('cerrar')" aria-label="Cerrar el recorrido">×</button></header>
        <ol class="guia-pasos">
          <li v-for="x in visibles" :key="x.n" :class="{ actual: actual === x.n }">
            <button type="button" @click="ir(x.n)" :aria-current="actual === x.n ? 'step' : null">
              <span class="guia-num">{{ x.n }}</span>
              <span class="guia-texto"><b>{{ x.p.titulo }}</b> <traza :c="x.p.cu"/><small v-if="actual === x.n">{{ x.p.accion }}</small></span>
            </button>
          </li>
        </ol>
        <footer class="guia-pie">
          <button type="button" class="boton-mini" :disabled="actual <= 1" @click="ir(actual - 1)">‹ Anterior</button>
          <button v-if="actual" type="button" class="enlace-texto" @click="todos = !todos">{{ todos ? 'Plegar' : 'Ver los ' + pasos.length + ' pasos' }}</button>
          <span v-else class="tenue">{{ pasos.length }} pasos</span>
          <button type="button" class="boton-mini siguiente" :disabled="actual >= pasos.length" @click="ir(actual + 1)">{{ actual ? 'Siguiente ›' : 'Empezar ›' }}</button>
        </footer>
      </aside>`,
  };

  const App = {
    data() {
      // En pantallas estrechas el recorrido empieza cerrado; un `#paso=N` lo abre siempre.
      const estrecha = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(max-width: 700px)').matches;
      // `index.html?singuia#/…` lo oculta (para sacar capturas limpias).
      const sinGuia = typeof location !== 'undefined' && /[?&]singuia\b/.test(location.search);
      return { guia: !estrecha && !sinGuia && guardado('iekg.guia') !== 'cerrada' };
    },
    watch: { '$route.query.paso'(p) { if (p) this.guia = true; } },
    created() { if (this.$route.query.paso) this.guia = true; },
    methods: {
      cerrarGuia() { this.guia = false; guardado('iekg.guia', 'cerrada'); },
      alternarGuia() { this.guia = !this.guia; guardado('iekg.guia', this.guia ? null : 'cerrada'); },
      alternarTraza() { estado.traza = !estado.traza; guardado('iekg.traza', estado.traza ? '1' : null); },
      saltar() { const m = document.getElementById('contenido'); if (m) m.focus(); },
    },
    template: `
      <a class="saltar" href="#" @click.prevent="saltar">Saltar al contenido</a>
      <header class="barra">
        <div class="barra-interior">
          <router-link to="/" class="marca"><span class="marca-sello" aria-hidden="true">§</span><span>Catálogo<span class="marca-sub"> del conocimiento</span></span></router-link>
          <buscador v-if="$route.path !== '/'" class="barra-buscador"/>
          <nav class="barra-nav" aria-label="Principal">
            <router-link :to="{ path: '/', query: { ver: 'areas' } }">Áreas</router-link>
            <router-link :to="{ path: '/', query: { ver: 'cursos' } }">Cursos</router-link>
            <a href="../panel-operador/index.html">Operador</a>
            <button type="button" class="boton-guia" @click="alternarGuia" :aria-pressed="guia ? 'true' : 'false'">Recorrido sugerido</button>
            <button type="button" class="interruptor" role="switch" :aria-checked="$estado.traza ? 'true' : 'false'" @click="alternarTraza">
              <span class="interruptor-pista" aria-hidden="true"><span></span></span>Ver trazabilidad
            </button>
          </nav>
        </div>
      </header>
      <main id="contenido" tabindex="-1"><router-view/></main>
      <footer class="pie">
        <p><b>Catálogo del conocimiento · maqueta.</b> Datos reales: el estándar CS2023 y los sílabos de 4 cursos de la PUCP. Lo marcado <span class="simulado">simulado</span> todavía no lo ofrece el sistema.</p>
      </footer>
      <guia-recorrido v-if="guia" @cerrar="cerrarGuia"/>`,
  };

  // `index.html#paso=N`: se traduce al estado del paso antes de arrancar el
  // enrutador; la ruta `/paso=N` cubre el cambio a mano con la página abierta.
  const m = /^#\/?paso=(\d+)$/.exec(typeof location !== 'undefined' ? location.hash : '');
  if (m && PASOS[Number(m[1]) - 1]) {
    const r = rutaDePaso(Number(m[1]));
    history.replaceState(null, '', `${location.pathname}${location.search}#${r.path}?${new URLSearchParams(r.query)}`);
  }

  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: VistaPortada },
      { path: '/buscar', component: VistaBusqueda },
      { path: '/ficha', component: VistaFicha },
      { path: '/paso=:n(\\d+)', redirect: (to) => rutaDePaso(Math.min(PASOS.length, Math.max(1, Number(to.params.n)))) },
      { path: '/:resto(.*)*', redirect: '/' },
    ],
    scrollBehavior(to, from) {
      if (to.path === '/' && to.query.ver) return false;
      // Cambiar solo el agrupamiento del camino, o la fila resaltada, no mueve la página.
      if (to.path === from.path && to.query.key === from.query.key && to.query.q === from.query.q) return false;
      return { top: 0 };
    },
  });

  const app = createApp(App);
  app.config.globalProperties.$aFicha = aFicha;
  app.config.globalProperties.$clase = clase;
  app.config.globalProperties.$estado = estado;
  const piezas = { Traza, Glifo, Insignia, Nota, Simulado, Fila, Grupo, Seccion, SeccionRuta, Leyenda, MiniMapa, Buscador, GuiaRecorrido };
  for (const [nombre, c] of Object.entries(piezas)) app.component(nombre, c);
  app.use(router);
  app.mount('#app');
})();
