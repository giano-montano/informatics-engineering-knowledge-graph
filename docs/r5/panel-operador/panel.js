/* Panel del operador (RF-23). JS sin framework, sin compilación.
 *
 * Capas, de abajo arriba (son los componentes del README):
 *   Sesion        el token tecleado, solo en esta pestaña (ADR-013).
 *   api()         cliente de las rutas de operación. Hoy lee IEKG_OPERACION;
 *                 en R6 se cambia su cuerpo por un fetch con "Authorization: Bearer".
 *   Vistas        acceso, compuerta, carga, lista, detalle, descartes, reglas.
 */
(function (global) {
  'use strict';

  // ── Constantes que salen del código de R4, no de la API ──────────────────

  // Dirección del documento de un recurso: GET /resources/{resource_key} (ADR-009).
  // Es la misma URL que el localizador del nodo LearningResource en el grafo.
  var API_BASE = 'http://localhost:8000';

  // Estados de una corrida (ADR-010; RUN_STATES en src/iekg/operational_store.py).
  // Significado: tesis, §«flujo de la ingesta» (l. 1217).
  var ESTADOS = {
    pending: { texto: 'Pendiente', tono: 'neutro', icono: 'reloj',
      significado: 'Registrada; espera a que el worker la tome.' },
    running: { texto: 'En curso', tono: 'info', icono: 'curso',
      significado: 'El worker extrae, valida o escribe el documento.' },
    completed: { texto: 'Terminada', tono: 'ok', icono: 'check',
      significado: 'Todo se escribió y la auditoría no encontró violaciones.' },
    rejected: { texto: 'Rechazada', tono: 'error', icono: 'cruz',
      significado: 'Salida no conforme o violaciones del validador: no se escribe nada; se registran los descartes.' },
    failed: { texto: 'Fallida', tono: 'error', icono: 'alerta',
      significado: 'El proveedor no respondió o la escritura no produjo lo esperado. Sin descartes.' },
    written_not_persisted: { texto: 'Escrita sin persistir', tono: 'aviso', icono: 'alerta',
      significado: 'El worker se interrumpió tras escribir y antes de guardar el lote en el almacén de hechos.' },
    stopped_by_audit: { texto: 'Detenida por auditoría', tono: 'aviso', icono: 'escudo',
      significado: 'La auditoría halló una violación tras escribir: la compuerta suspende las pendientes.' }
  };
  var ESTADOS_FINALES = ['completed', 'rejected', 'failed', 'written_not_persisted', 'stopped_by_audit'];

  var ORIGENES = { load: 'carga', ingestion: 'ingesta', reapplication: 'reaplicación' };

  // Motivos de compuerta cerrada (src/iekg/ingestion/orchestrator.py).
  var MOTIVOS = {
    'no report recorded': 'No hay ningún reporte de auditoría registrado.',
    'latest report still open': 'El último reporte sigue abierto: un camino de escritura se detuvo antes de auditar.',
    'latest report with violations': 'El último reporte tiene violaciones.'
  };

  // Enunciados de las reglas: Tablas 18 y 19 de la tesis; códigos EX: enmienda de ADR-010.
  // La API devuelve solo el código; ver «campo nuevo opcional» en el README.
  var REGLAS = {
    'RI-01': 'Todo nodo tiene clave no nula, y no hay dos nodos con la misma clave.',
    'RI-02': 'Todo nodo lleva la etiqueta de su clase; los nodos KnowledgeArea, KnowledgeUnit, Topic y Concept llevan además la etiqueta KnowledgeElement.',
    'RI-03': 'Todo nodo lleva exactamente una de las etiquetas KnowledgeElement, Course, LearningResource y ResourceType, y todo nodo KnowledgeElement exactamente una de KnowledgeArea, KnowledgeUnit, Topic y Concept.',
    'RI-04': 'Toda arista es de uno de los ocho tipos de la Tabla 16.',
    'RI-05': 'Cada arista une un par de etiquetas admitido para su tipo en la Tabla 16, en la dirección de la propiedad afirmada.',
    'RI-06': 'Entre dos nodos hay como máximo una arista de cada tipo en cada dirección.',
    'RI-07': 'Ninguna unidad tiene aristas de partonomía hacia más de un área.',
    'RI-08': 'Todo concepto tiene al menos una arista de partonomía hacia un tema; todo tema, hacia una unidad; toda unidad, hacia un área.',
    'RI-09': 'Todo nodo y toda arista tiene solo propiedades declaradas en la Tabla 17.',
    'RI-10': 'Si un recurso de aprendizaje tiene localizador, su valor es un URI absoluto con esquema http o https.',
    'RM-01': 'Todo nodo tiene marca de capa, con valor de referencia o institucional.',
    'RM-02': 'Ninguna arista sale de un nodo de la capa de referencia hacia uno de la capa institucional.',
    'RM-03': 'Todo tema, concepto y curso institucional tiene al menos una arista de procedencia hacia un recurso de aprendizaje, y toda arista que escribe la ingesta lleva su procedencia.',
    'RM-04': 'No existen ciclos de prerrequisito ni de especialización.',
    'RM-05': 'Todo recurso de aprendizaje tiene localizador.',
    'EX-01': 'La salida del modelo no se ajusta al esquema de salida.',
    'EX-02': 'Una mención enlazada trae una clave que no está en la instantánea.',
    'EX-03': 'Una clave existente es, en la instantánea, de otra clase que la que exige su lugar en la salida.'
  };

  // Tipos de recurso del MVP (RESOURCE_TYPES en src/iekg/ingestion/declared.py).
  // La API no los expone; ver la decisión 1 del README.
  var TIPOS_DE_RECURSO = ['Sílabo'];

  // Reintentos de contenido permitidos por corrida (ADR-010).
  var MAX_REINTENTOS_CONTENIDO = 1;

  // Ejemplos de la documentación de la API (src/iekg/api/models.py). NO son datos reales.
  var EJEMPLO_DESCARTES = {
    discards: [{ rule: 'RI-05', fact: '(a)-[:PART_OF]->(b)', message: 'Concept PART_OF Course' }],
    batch: { nodes: [], edges: [] },
    raw_output: null
  };
  var EJEMPLO_COMPUERTA_CERRADA = {
    gate: { state: 'closed', reason: 'latest report with violations' },
    report: { id: 12, created_at: '2026-10-08T15:03:38+00:00', origin: 'ingestion', run_id: '7',
      completed: true, violations: 1,
      rules: [{ rule: 'RI-08', violations: 1, sample: ['x (Topic) is not part of any KnowledgeUnit'] }] }
  };

  // ── Sesión: el token tecleado (ADR-013) ──────────────────────────────────

  var Sesion = {
    clave: 'iekg.operador.token',
    memoria: null,
    leer: function () {
      try { var v = global.sessionStorage && global.sessionStorage.getItem(this.clave); if (v) return v; } catch (e) { /* sin almacenamiento */ }
      return this.memoria;
    },
    guardar: function (token) {
      this.memoria = token;
      try { global.sessionStorage && global.sessionStorage.setItem(this.clave, token); } catch (e) { /* queda en memoria */ }
    },
    olvidar: function () {
      this.memoria = null;
      try { global.sessionStorage && global.sessionStorage.removeItem(this.clave); } catch (e) { /* nada */ }
    }
  };

  // ── Cliente de las rutas de operación ────────────────────────────────────

  function copia(x) { return x == null ? x : JSON.parse(JSON.stringify(x)); }

  var Maqueta = {
    rechazarToken: false,   // «probar token inválido» / «simular token rechazado»
    simuladas: []           // corridas creadas con el formulario: solo en esta página
  };

  /**
   * Una petición a la API de operación. Devuelve una promesa de {status, body, simulada}.
   * En R6 el cuerpo es, en esencia:
   *   return fetch(API_BASE + ruta, { method: metodo, body: cuerpo,
   *     headers: { Authorization: 'Bearer ' + Sesion.leer() } })
   *     .then(function (r) { return r.json().then(function (b) { return { status: r.status, body: b }; }); });
   */
  function api(metodo, ruta, cuerpo) {
    var OP = global.IEKG_OPERACION || {};
    var token = Sesion.leer();
    return new Promise(function (resolver) {
      if (!token || Maqueta.rechazarToken) {
        var r401 = OP['GET /api/runs (sin token)'];   // respuesta real capturada
        return resolver({ status: r401[0], body: copia(r401[1]) });
      }
      if (metodo === 'POST' && ruta === '/api/runs') return resolver(simularAlta(cuerpo));

      var m = /^\/api\/runs\/(\d+)(\/discards)?$/.exec(ruta);
      var simulada = m && Maqueta.simuladas.filter(function (c) { return c.id === Number(m[1]); })[0];
      if (simulada) {
        return resolver({ status: 200, simulada: true,
          body: m[2] ? { discards: [], batch: null, raw_output: null } : copia(simulada) });
      }

      var clave = metodo + ' ' + ruta;
      if (Object.prototype.hasOwnProperty.call(OP, clave)) {
        var body = copia(OP[clave]);
        if (ruta === '/api/runs') body = body.concat(Maqueta.simuladas.map(resumenDe));
        return resolver({ status: 200, body: body });
      }
      if (m) return resolver({ status: 404, body: { detail: 'run ' + m[1] + ' does not exist' } });
      resolver({ status: 404, body: { detail: 'Not Found' } });
    });
  }

  function resumenDe(detalle) {
    var r = {};
    ['id', 'status', 'created_at', 'finished_at', 'resource_type', 'course_code', 'course_name', 'file_name']
      .forEach(function (k) { r[k] = detalle[k]; });
    r._simulada = true;
    return r;
  }

  // Lo que haría POST /api/runs: 202 con {run_id, worker_launched} y una corrida pendiente.
  function simularAlta(datos) {
    var OP = global.IEKG_OPERACION || {};
    var ids = (OP['GET /api/runs'] || []).map(function (c) { return c.id; })
      .concat(Maqueta.simuladas.map(function (c) { return c.id; }));
    var id = Math.max.apply(null, ids.concat([0])) + 1;
    var archivo = leerCampo(datos, 'file');
    Maqueta.simuladas.push({
      id: id, status: 'pending', created_at: new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00'),
      started_at: null, finished_at: null,
      resource_key: null,  // la acuña la API (uuid4) al registrar
      resource_type: leerCampo(datos, 'resource_type'),
      course_code: String(leerCampo(datos, 'course_code')).trim().toUpperCase(),
      course_name: String(leerCampo(datos, 'course_name')).trim(),
      file_name: archivo && archivo.name ? archivo.name : String(archivo),
      model: null, model_settings: null, prompt_version: null, content_retries: null, error: null,
      audit_report: null, _simulada: true
    });
    return { status: 202, simulada: true, body: { run_id: id, worker_launched: true } };
  }

  function leerCampo(datos, nombre) {
    if (datos && typeof datos.get === 'function') return datos.get(nombre);
    return datos ? datos[nombre] : undefined;
  }

  // Validación previa, espejo de los 422 de POST /api/runs (src/iekg/ingestion/submission.py).
  function validarAlta(campos) {
    var errores = {};
    var archivo = campos.file;
    if (!archivo) errores.file = 'Elige el PDF del documento.';
    else if (!/\.pdf$/i.test(archivo.name || '')) errores.file = 'La API solo acepta archivos .pdf.';
    else if (campos.cabeceraPdf === false) errores.file = 'El archivo no empieza como un PDF (%PDF-): la API lo rechazaría.';
    if (TIPOS_DE_RECURSO.indexOf(campos.resource_type) < 0) errores.resource_type = 'Tipo de recurso desconocido.';
    if (!String(campos.course_code || '').trim()) errores.course_code = 'Un sílabo necesita el código de su curso.';
    if (!String(campos.course_name || '').trim()) errores.course_name = 'Un sílabo necesita el nombre de su curso.';
    return errores;
  }

  // ── Formato ──────────────────────────────────────────────────────────────

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fecha(iso) {
    if (!iso) return '—';
    var d = new Date(iso);
    if (isNaN(d)) return esc(iso);
    return d.toLocaleString('es-PE', { day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  function fechaCorta(iso) {
    if (!iso) return '—';
    var d = new Date(iso);
    return isNaN(d) ? esc(iso) : d.toLocaleString('es-PE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  }
  function duracion(desde, hasta) {
    if (!desde || !hasta) return null;
    var s = Math.round((new Date(hasta) - new Date(desde)) / 1000);
    if (!(s >= 0)) return null;
    return s < 60 ? s + ' s' : Math.floor(s / 60) + ' min ' + (s % 60) + ' s';
  }
  function enmascarar(token) {
    return token.length <= 4 ? '••••' : '••••' + token.slice(-4);
  }

  // ── Íconos (SVG en línea; el estado nunca depende solo del color) ────────

  var ICONOS = {
    check: '<path d="M3.5 8.5l3 3 6-7"/>',
    cruz: '<path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/>',
    alerta: '<path d="M8 2.5l6 11H2z"/><path d="M8 7v3M8 12v.01"/>',
    reloj: '<circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 1.5"/>',
    curso: '<path d="M8 2.5a5.5 5.5 0 1 1-5.5 5.5"/><path d="M8 5.5v2.5h2.5"/>',
    escudo: '<path d="M8 2l5 2v4c0 3-2.2 5.2-5 6-2.8-.8-5-3-5-6V4z"/><path d="M6 8h4"/>',
    candado: '<rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2"/>',
    abierto: '<rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 4.9-.7"/>',
    bandeja: '<path d="M2.5 9.5l1.8-5.5h7.4l1.8 5.5v3.5h-11z"/><path d="M2.5 9.5h3.2l.8 1.5h3l.8-1.5h3.2"/>',
    documento: '<path d="M4 2h5l3 3v9H4z"/><path d="M9 2v3h3"/>',
    externo: '<path d="M9 3h4v4M13 3L7.5 8.5M12 9.5V13H3V4h3.5"/>'
  };
  function icono(nombre) {
    return '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONOS[nombre] || '') + '</svg>';
  }
  function etiquetaEstado(status) {
    var e = ESTADOS[status] || { texto: status, tono: 'neutro', icono: 'alerta' };
    return '<span class="etiqueta e-' + e.tono + '" title="' + esc(e.significado || '') + '">' + icono(e.icono) +
      esc(e.texto) + ' <span class="cod">' + esc(status) + '</span></span>';
  }
  var SIMULADO = '<span class="simulado" title="No viene de la API: lo genera la maqueta">simulado</span>';
  var EJEMPLO = '<span class="simulado" title="Ejemplo de la documentación de la API (models.py)">ejemplo · no real</span>';

  // Exporta lo puro para probarlo en node sin DOM.
  var nucleo = { api: api, Sesion: Sesion, Maqueta: Maqueta, validarAlta: validarAlta, ESTADOS: ESTADOS,
    REGLAS: REGLAS, MOTIVOS: MOTIVOS, duracion: duracion, enmascarar: enmascarar };
  if (typeof module !== 'undefined' && module.exports) module.exports = nucleo;
  if (typeof document === 'undefined') return;

  // ═════════════════════════════════════════════════════════════════════════
  // Vistas
  // ═════════════════════════════════════════════════════════════════════════

  var $ = function (id) { return document.getElementById(id); };
  var estado = {
    corridas: [], reporte: null, seleccion: null, detalle: null, descartes: null,
    pestana: 'resumen', ejemploDescartes: false, ejemploCompuerta: false, actualizado: null, envio: null
  };

  function anunciar(texto) { $('anuncio').textContent = texto; }

  // ── Acceso ───────────────────────────────────────────────────────────────

  function mostrarAcceso(respuesta401, motivo) {
    $('vista-panel').classList.add('oculto');
    $('nav').classList.add('oculto');
    $('sesion-activa').classList.add('oculto');
    $('vista-acceso').classList.remove('oculto');
    var error = '';
    if (respuesta401) {
      error = '<div class="respuesta-401" role="alert">' +
        '<strong>La API rechazó el token · ' + respuesta401.status + ' Unauthorized</strong>' +
        (motivo ? '<div>' + esc(motivo) + '</div>' : '') +
        '<pre>' + esc(JSON.stringify(respuesta401.body)) + '</pre>' +
        '<div class="nota">Respuesta real capturada de <code>GET /api/runs</code> sin token. ' +
        'El token falta o no coincide con <code>IEKG_OPERATOR_TOKEN</code> del servidor; si lo cambiaron, la API se reinició (ADR-013).</div>' +
        '</div>';
    }
    $('vista-acceso').innerHTML =
      '<section class="tarjeta" aria-labelledby="t-acceso"><div class="cuerpo">' +
      '<h1 id="t-acceso">Acceso del operador</h1>' +
      '<p>Las rutas de operación exigen el token fijo configurado en el servidor. Se guarda solo en esta pestaña y se envía en cada petición.</p>' +
      error +
      '<form id="form-acceso" class="campo" novalidate>' +
      '<label for="in-token">Token del operador</label>' +
      '<div class="fila-token"><input type="password" id="in-token" autocomplete="off" spellcheck="false" required aria-describedby="ayuda-token">' +
      '<button class="btn btn-chico" type="button" id="btn-ver-token" aria-pressed="false">Mostrar</button></div>' +
      '<span class="error-campo oculto" id="err-token">Escribe el token.</span>' +
      '<span class="ayuda" id="ayuda-token">Maqueta: acepta cualquier token no vacío. En R6 lo valida la API.</span>' +
      '<div style="display:flex;align-items:center;gap:14px;margin-top:6px">' +
      '<button class="btn btn-primario" type="submit">Entrar</button>' +
      '<button class="btn-enlace btn" type="button" id="btn-token-invalido">Probar token inválido</button></div>' +
      '</form></div></section>';

    $('in-token').focus();
    $('btn-ver-token').onclick = function () {
      var inp = $('in-token'), ver = inp.type === 'password';
      inp.type = ver ? 'text' : 'password';
      this.textContent = ver ? 'Ocultar' : 'Mostrar';
      this.setAttribute('aria-pressed', String(ver));
    };
    $('form-acceso').onsubmit = function (ev) {
      ev.preventDefault();
      var t = $('in-token').value.trim();
      if (!t) { $('err-token').classList.remove('oculto'); $('in-token').setAttribute('aria-invalid', 'true'); return; }
      Sesion.guardar(t);
      entrar();
    };
    $('btn-token-invalido').onclick = function () {
      Sesion.guardar($('in-token').value.trim() || 'token-de-prueba');
      Maqueta.rechazarToken = true;
      entrar();
    };
  }

  // Carga lo que la pantalla necesita; ante un 401 vuelve al acceso.
  function entrar(motivo401) {
    return Promise.all([api('GET', '/api/runs'), api('GET', '/api/audit-reports/latest')]).then(function (rs) {
      var rechazo = rs.filter(function (r) { return r.status === 401; })[0];
      if (rechazo) {
        Maqueta.rechazarToken = false;
        Sesion.olvidar();
        mostrarAcceso(rechazo, motivo401);
        return;
      }
      estado.corridas = rs[0].body;
      estado.reporte = rs[1].body;
      estado.actualizado = new Date();
      if (estado.seleccion == null && estado.corridas.length) {
        estado.seleccion = estado.corridas.reduce(function (a, b) { return b.id > a.id ? b : a; }).id;
      }
      mostrarPanel();
      return seleccionar(estado.seleccion, true);
    });
  }

  // ── Panel ────────────────────────────────────────────────────────────────

  function mostrarPanel() {
    $('vista-acceso').classList.add('oculto');
    $('vista-panel').classList.remove('oculto');
    $('nav').classList.remove('oculto');
    $('sesion-activa').classList.remove('oculto');
    $('token-enmascarado').textContent = enmascarar(Sesion.leer() || '');
    pintarCompuerta();
    pintarCarga();
    pintarLista();
    pintarAuditoria();
  }

  // ── Compuerta (resumen arriba) ──────────────────────────────────────────

  function bloqueCompuerta(dato, ejemplo) {
    var abierta = dato.gate.state === 'open';
    var r = dato.report;
    var tono = abierta ? 'e-ok' : 'e-error';
    return '<div class="compuerta">' +
      '<div class="compuerta-estado"><span class="compuerta-icono ' + tono + '">' + icono(abierta ? 'abierto' : 'candado') + '</span>' +
      '<div><strong>Compuerta ' + (abierta ? 'abierta' : 'cerrada') + ' <span class="cod mono" style="font-weight:400;font-size:12px;color:var(--texto-3)">gate.state = ' + esc(dato.gate.state) + '</span></strong>' +
      '<p>' + (abierta
        ? 'El worker puede tomar las corridas pendientes.'
        : esc(MOTIVOS[dato.gate.reason] || dato.gate.reason) + ' Las corridas pendientes esperan hasta que un camino de escritura posterior complete un reporte limpio (ADR-007).') +
      '</p>' + (!abierta ? '<p class="nota mono">reason = "' + esc(dato.gate.reason) + '"</p>' : '') + '</div></div>' +
      (r ? '<dl class="datos">' +
        '<dt>Último reporte</dt><dd>#' + esc(r.id) + '</dd>' +
        '<dt>Origen</dt><dd>' + esc(ORIGENES[r.origin] || r.origin) + (r.run_id ? ' · corrida ' + esc(r.run_id) : '') + '</dd>' +
        '<dt>Fecha</dt><dd>' + fecha(r.created_at) + '</dd>' +
        '<dt>Resultado</dt><dd>' + (r.completed
          ? (r.violations === 0 ? 'Completo · <strong>0 violaciones</strong> en ' + r.rules.length + ' reglas'
            : 'Completo · <strong style="color:var(--error)">' + r.violations + ' violación' + (r.violations === 1 ? '' : 'es') + '</strong>')
          : 'Abierto: el camino de escritura no auditó') + '</dd>' +
        '</dl>' : '<p class="nota">Ningún camino de escritura ha registrado un reporte.</p>') +
      '</div>';
  }

  function pintarCompuerta() {
    $('zona-compuerta').innerHTML =
      '<header><h2 id="t-compuerta">Compuerta de auditoría</h2><span class="ruta">GET /api/audit-reports/latest</span></header>' +
      '<div class="cuerpo">' + bloqueCompuerta(estado.reporte, false) +
      '<p class="nota" style="margin:14px 0 0"><a href="#sec-auditoria">Ver las ' + (estado.reporte.report ? estado.reporte.report.rules.length : 0) + ' reglas del último reporte ↓</a></p></div>';
  }

  // ── Carga de un documento ───────────────────────────────────────────────

  function pintarCarga() {
    $('zona-carga').innerHTML =
      '<header><h2 id="t-carga">Cargar un documento</h2><span class="ruta">POST /api/runs · multipart</span></header>' +
      '<div class="cuerpo">' +
      '<form class="form-carga" id="form-carga" novalidate>' +
      '<div class="campo ancho"><label for="f-file">Documento (PDF) <span class="mono nota">file</span></label>' +
      '<input type="file" id="f-file" name="file" accept=".pdf,application/pdf" aria-describedby="e-file">' +
      '<span class="error-campo" id="e-file"></span></div>' +
      '<div class="campo"><label for="f-tipo">Tipo de recurso <span class="mono nota">resource_type</span></label>' +
      '<select id="f-tipo" name="resource_type">' + TIPOS_DE_RECURSO.map(function (t) { return '<option>' + esc(t) + '</option>'; }).join('') + '</select>' +
      '<span class="ayuda">El MVP admite solo sílabos.</span><span class="error-campo" id="e-resource_type"></span></div>' +
      '<div class="campo"><label for="f-codigo">Código del curso <span class="mono nota">course_code</span></label>' +
      '<input type="text" id="f-codigo" name="course_code" placeholder="1INF33" autocomplete="off" aria-describedby="e-course_code">' +
      '<span class="error-campo" id="e-course_code"></span></div>' +
      '<div class="campo ancho"><label for="f-nombre">Nombre del curso <span class="mono nota">course_name</span></label>' +
      '<input type="text" id="f-nombre" name="course_name" placeholder="Bases de Datos" autocomplete="off" aria-describedby="e-course_name">' +
      '<span class="error-campo" id="e-course_name"></span></div>' +
      '<div class="acciones"><button class="btn btn-primario" type="submit">Registrar corrida</button>' +
      '<span class="nota">La maqueta no envía nada: muestra lo que haría la API.</span></div>' +
      '</form>' +
      '<div id="resultado-envio">' + (estado.envio || '') + '</div>' +
      '</div>';

    $('form-carga').onsubmit = function (ev) {
      ev.preventDefault();
      var form = ev.target;
      var archivo = form.file.files[0];
      leerCabecera(archivo).then(function (esPdf) {
        var campos = { file: archivo, cabeceraPdf: esPdf, resource_type: form.resource_type.value,
          course_code: form.course_code.value, course_name: form.course_name.value };
        var errores = validarAlta(campos);
        ['file', 'resource_type', 'course_code', 'course_name'].forEach(function (k) {
          $('e-' + k).textContent = errores[k] || '';
          var el = form.elements[k]; if (el) el.setAttribute('aria-invalid', errores[k] ? 'true' : 'false');
        });
        if (Object.keys(errores).length) { anunciar('El formulario tiene errores.'); return; }
        var datos = new FormData(form);
        return api('POST', '/api/runs', datos).then(function (r) {
          estado.envio = resultadoEnvio(campos, r);
          estado.seleccion = r.body.run_id;
          form.reset();
          return entrar().then(function () { anunciar('Corrida ' + r.body.run_id + ' registrada como pendiente (simulado).'); });
        });
      });
    };
  }

  function leerCabecera(archivo) {
    if (!archivo || !archivo.slice) return Promise.resolve(null);
    return archivo.slice(0, 5).arrayBuffer().then(function (buf) {
      return String.fromCharCode.apply(null, new Uint8Array(buf)) === '%PDF-';
    }).catch(function () { return null; });
  }

  function resultadoEnvio(campos, r) {
    var kb = campos.file.size != null ? ' (' + Math.max(1, Math.round(campos.file.size / 1024)) + ' KB)' : '';
    var pedido =
      'POST /api/runs\n' +
      'Authorization: Bearer ' + enmascarar(Sesion.leer() || '') + '\n' +
      'Content-Type: multipart/form-data\n' +
      '  file           = ' + campos.file.name + kb + '\n' +
      '  resource_type  = ' + campos.resource_type + '\n' +
      '  course_code    = ' + campos.course_code.trim() + '\n' +
      '  course_name    = ' + campos.course_name.trim() + '\n\n' +
      '← ' + r.status + ' Accepted\n' + JSON.stringify(r.body);
    return '<div class="resultado-envio marco-simulado" role="status">' +
      SIMULADO + ' <strong>Nada se envió.</strong> Así respondería la API: registra la corrida ' + r.body.run_id +
      ' como <em>pendiente</em> y lanza el worker si no hay uno activo. En R6 el panel la sigue pidiendo hasta un estado final.' +
      '<pre>' + esc(pedido) + '</pre></div>';
  }

  // ── Lista de corridas ───────────────────────────────────────────────────

  function pintarLista() {
    $('corridas-actualizado').textContent = estado.actualizado
      ? 'Actualizado ' + estado.actualizado.toLocaleTimeString('es-PE') : '';
    var filas = estado.corridas.slice().sort(function (a, b) { return b.id - a.id; });
    var cuerpo = filas.length ? filas.map(function (c) {
      return '<tr tabindex="0" data-id="' + c.id + '" aria-selected="' + (c.id === estado.seleccion) + '">' +
        '<td class="num mono">' + c.id + '</td>' +
        '<td><span class="curso">' + esc(c.course_code || '—') + '</span> ' + (c._simulada ? SIMULADO : '') +
        '<span class="sub">' + esc(c.course_name || '') + '</span></td>' +
        '<td>' + etiquetaEstado(c.status) + '</td>' +
        '<td class="nota" style="white-space:nowrap">' + fechaCorta(c.created_at) +
        (duracion(c.created_at, c.finished_at) ? '<span class="sub">' + duracion(c.created_at, c.finished_at) + '</span>' : '') + '</td>' +
        '</tr>';
    }).join('') : '';
    $('zona-lista').innerHTML = filas.length
      ? '<div class="envoltura-tabla"><table class="tabla-corridas" aria-label="Corridas de ingesta">' +
        '<thead><tr><th class="num">#</th><th>Curso</th><th>Estado</th><th>Creada · duración</th></tr></thead>' +
        '<tbody>' + cuerpo + '</tbody></table></div>' + leyendaEstados()
      : '<div class="cuerpo"><div class="vacio"><span class="icono-vacio">' + icono('bandeja') + '</span>' +
        '<strong>Aún no hay corridas</strong><p>Sube el primer sílabo con el formulario de arriba.</p></div></div>';

    Array.prototype.forEach.call(document.querySelectorAll('.tabla-corridas tbody tr'), function (tr) {
      var ir = function () { seleccionar(Number(tr.getAttribute('data-id'))); };
      tr.onclick = ir;
      tr.onkeydown = function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); ir(); }
        if (ev.key === 'ArrowDown' && tr.nextElementSibling) { ev.preventDefault(); tr.nextElementSibling.focus(); }
        if (ev.key === 'ArrowUp' && tr.previousElementSibling) { ev.preventDefault(); tr.previousElementSibling.focus(); }
      };
    });
  }

  function leyendaEstados() {
    var presentes = {};
    estado.corridas.forEach(function (c) { presentes[c.status] = true; });
    return '<details class="leyenda"><summary>Los 7 estados posibles de una corrida (ADR-010)</summary><ul>' +
      Object.keys(ESTADOS).map(function (k) {
        return '<li>' + etiquetaEstado(k) + '<span>' + esc(ESTADOS[k].significado) +
          (presentes[k] ? '' : ' <em class="nota">(ninguna hoy)</em>') + '</span></li>';
      }).join('') + '</ul></details>';
  }

  // ── Detalle de una corrida ──────────────────────────────────────────────

  function seleccionar(id, conservarPestana) {
    if (id == null) { $('zona-detalle').innerHTML = '<div class="vacio-detalle">Elige una corrida.</div>'; return Promise.resolve(); }
    estado.seleccion = id;
    if (!conservarPestana) { estado.pestana = 'resumen'; estado.ejemploDescartes = false; }
    Array.prototype.forEach.call(document.querySelectorAll('.tabla-corridas tbody tr'), function (tr) {
      tr.setAttribute('aria-selected', String(Number(tr.getAttribute('data-id')) === id));
    });
    return Promise.all([api('GET', '/api/runs/' + id), api('GET', '/api/runs/' + id + '/discards')]).then(function (rs) {
      if (rs[0].status === 401 || rs[1].status === 401) { Sesion.olvidar(); mostrarAcceso(rs[0], 'La sesión se cerró.'); return; }
      if (rs[0].status !== 200) {
        $('zona-detalle').innerHTML = '<div class="vacio-detalle">' + esc(rs[0].status + ' · ' + rs[0].body.detail) + '</div>';
        return;
      }
      estado.detalle = rs[0].body;
      estado.detalle._simulada = !!rs[0].simulada;
      estado.descartes = rs[1].body;
      pintarDetalle();
    });
  }

  function pintarDetalle() {
    var d = estado.detalle;
    var n = estado.descartes.discards.length;
    var pestanas = [
      ['resumen', 'Resumen', null],
      ['auditoria', 'Auditoría de cierre', null],
      ['descartes', 'Descartes', n]
    ];
    $('zona-detalle').innerHTML =
      '<div class="detalle-cabecera"><h2>Corrida ' + d.id + '</h2>' + etiquetaEstado(d.status) +
      (d._simulada ? SIMULADO : '') +
      '<span class="ruta" style="margin-left:auto">GET /api/runs/' + d.id + '</span></div>' +
      '<div class="pestanas" role="tablist" aria-label="Detalle de la corrida">' +
      pestanas.map(function (p) {
        return '<button role="tab" type="button" id="tab-' + p[0] + '" aria-controls="panel-detalle" data-p="' + p[0] + '" aria-selected="' + (estado.pestana === p[0]) + '"' +
          (estado.pestana === p[0] ? '' : ' tabindex="-1"') + '>' + p[1] +
          (p[2] != null ? '<span class="contador">' + p[2] + '</span>' : '') + '</button>';
      }).join('') + '</div>' +
      '<div class="panel-pestana" role="tabpanel" id="panel-detalle" aria-labelledby="tab-' + estado.pestana + '">' + contenidoPestana(d) + '</div>';

    var tabs = document.querySelectorAll('.pestanas [role="tab"]');
    Array.prototype.forEach.call(tabs, function (b, i) {
      b.onclick = function () { estado.pestana = b.getAttribute('data-p'); pintarDetalle(); $('tab-' + estado.pestana).focus(); };
      b.onkeydown = function (ev) {
        var j = ev.key === 'ArrowRight' ? i + 1 : ev.key === 'ArrowLeft' ? i - 1 : null;
        if (j == null) return;
        var t = tabs[(j + tabs.length) % tabs.length];
        estado.pestana = t.getAttribute('data-p'); pintarDetalle(); $('tab-' + estado.pestana).focus();
      };
    });
    var bEj = $('btn-ejemplo-descartes');
    if (bEj) bEj.onclick = function () { estado.ejemploDescartes = !estado.ejemploDescartes; pintarDetalle(); };
  }

  function contenidoPestana(d) {
    if (estado.pestana === 'auditoria') return pestanaAuditoria(d);
    if (estado.pestana === 'descartes') return pestanaDescartes(d, estado.descartes);
    return pestanaResumen(d);
  }

  function pestanaResumen(d) {
    var dur = duracion(d.started_at, d.finished_at);
    var espera = duracion(d.created_at, d.started_at);
    var pdf = d.resource_key
      ? '<a href="' + esc(API_BASE + '/resources/' + encodeURIComponent(d.resource_key)) + '" target="_blank" rel="noopener">' +
        icono('documento').replace('<svg', '<svg style="width:13px;height:13px;vertical-align:-2px"') + ' Abrir el documento</a>' +
        ' <span class="nota">(abre solo con la API en :8000)</span>'
      : '<span class="nota">Se acuña al registrar.</span>';
    var ajustes = d.model_settings
      ? Object.keys(d.model_settings).sort().map(function (k) {
          return '<dt class="mono">' + esc(k) + '</dt><dd class="mono">' + esc(JSON.stringify(d.model_settings[k])) + '</dd>';
        }).join('')
      : '<dt>—</dt><dd class="nota">Aún sin extracción.</dd>';
    var seguimiento = ESTADOS_FINALES.indexOf(d.status) < 0
      ? '<div class="marco-simulado" style="padding:10px 12px;margin-bottom:16px;font-size:12.5px">' + SIMULADO +
        ' Corrida aún no terminada. En R6 el panel vuelve a pedir <code>GET /api/runs/' + d.id + '</code> cada pocos segundos mientras esté <em>pendiente</em> o <em>en curso</em>.</div>'
      : '';
    return seguimiento + '<div class="bloques">' +
      '<section><h3>Fechas</h3><dl class="datos">' +
      '<dt>Creada</dt><dd>' + fecha(d.created_at) + '</dd>' +
      '<dt>Iniciada</dt><dd>' + fecha(d.started_at) + (espera && espera !== '0 s' ? ' <span class="nota">(esperó ' + espera + ')</span>' : '') + '</dd>' +
      '<dt>Terminada</dt><dd>' + fecha(d.finished_at) + '</dd>' +
      '<dt>Duración</dt><dd>' + (dur || '—') + '</dd></dl></section>' +
      '<section><h3>Documento</h3><dl class="datos">' +
      '<dt>Archivo</dt><dd class="mono">' + esc(d.file_name) + '</dd>' +
      '<dt>Tipo</dt><dd>' + esc(d.resource_type) + '</dd>' +
      '<dt>Curso</dt><dd>' + esc(d.course_code || '—') + ' · ' + esc(d.course_name || '—') + '</dd>' +
      '<dt>Recurso</dt><dd class="mono" style="font-size:11.5px">' + esc(d.resource_key || '—') + '</dd>' +
      '<dt>PDF</dt><dd>' + pdf + '</dd></dl></section>' +
      '<section><h3>Extracción (RF-25)</h3><dl class="datos">' +
      '<dt>Modelo</dt><dd class="mono">' + esc(d.model || '—') + '</dd>' +
      '<dt>Prompt</dt><dd class="mono">' + esc(d.prompt_version || '—') + '</dd>' +
      '<dt>Reintentos de contenido</dt><dd>' + (d.content_retries == null ? '—' : d.content_retries + ' de ' + MAX_REINTENTOS_CONTENIDO + ' permitido') + '</dd>' +
      '<dt>Error</dt><dd>' + (d.error ? '<span style="color:var(--error)">' + esc(d.error) + '</span>' : '—') + '</dd></dl></section>' +
      '<section><h3>Ajustes del modelo</h3><dl class="datos">' + ajustes + '</dl></section>' +
      '</div>';
  }

  function pestanaAuditoria(d) {
    var r = d.audit_report;
    if (!r) {
      return vacio('escudo', 'Sin reporte de cierre',
        d.status === 'pending' || d.status === 'running'
          ? 'La corrida aún no escribe: el reporte se abre al escribir y se completa con la auditoría.'
          : 'Esta corrida no escribió en el grafo, así que no la cerró ninguna auditoría (ADR-005).');
    }
    return '<p class="nota" style="margin:0 0 12px">Reporte #' + esc(r.id) + ' · ' + esc(ORIGENES[r.origin] || r.origin) + ' · ' + fecha(r.created_at) +
      ' · ' + (r.completed ? (r.violations + ' violaciones') : 'abierto') + '</p>' + tablaReglas(r.rules);
  }

  function pestanaDescartes(d, x) {
    var html = '';
    if (x.discards.length || x.raw_output || x.batch) {
      html = vistaDescartes(x, false);
    } else {
      var motivo;
      if (d.status === 'pending' || d.status === 'running') motivo = 'La corrida aún no termina.';
      else if (d.status === 'failed') motivo = 'Una corrida fallida no genera descartes: falló la ejecución, no el contenido (ADR-010). Mira el error en el resumen.';
      else if (d.status === 'rejected') motivo = 'La corrida está rechazada pero no tiene descartes registrados: revisar el almacén operacional.';
      else motivo = 'La corrida no fue rechazada: todo lo que extrajo pasó la validación y se escribió. Los descartes solo existen en corridas rechazadas (ADR-010).';
      html = vacio('check', 'Sin descartes', motivo) +
        '<p class="nota" style="text-align:center;margin:10px 0 0"><code>{"discards": [], "batch": null, "raw_output": null}</code></p>';
    }
    html += '<div style="text-align:center;margin-top:12px"><button class="btn btn-chico" type="button" id="btn-ejemplo-descartes" aria-expanded="' + estado.ejemploDescartes + '">' +
      (estado.ejemploDescartes ? 'Ocultar el ejemplo' : 'Ver cómo se ve una corrida con descartes') + '</button></div>';
    if (estado.ejemploDescartes) {
      html += '<div class="ejemplo marco-ejemplo"><div class="titulo-ejemplo">' + EJEMPLO +
        '<span>Ejemplo de la documentación de la API (<code>RunDiscards</code>, models.py). No corresponde a ninguna corrida.</span></div>' +
        vistaDescartes(EJEMPLO_DESCARTES, true) + '</div>';
    }
    return html;
  }

  function vistaDescartes(x, ejemplo) {
    var html = '';
    if (x.discards.length) {
      html += '<p style="margin:0 0 8px"><strong>' + x.discards.length + ' violación' + (x.discards.length === 1 ? '' : 'es') +
        '</strong> · el documento entero se rechazó: no se escribió nada (ADR-010).</p>' +
        '<div class="envoltura-tabla"><table class="tabla-reglas"><thead><tr><th>Regla</th><th>Hecho</th><th>Mensaje</th></tr></thead><tbody>' +
        x.discards.map(function (v) {
          return '<tr><td class="cod" title="' + esc(REGLAS[v.rule] || '') + '">' + esc(v.rule) + '</td>' +
            '<td class="mono">' + esc(v.fact) + '</td><td>' + esc(v.message) +
            (REGLAS[v.rule] ? '<span class="sub nota" style="display:block">' + esc(REGLAS[v.rule]) + '</span>' : '') + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    }
    if (x.raw_output) {
      html += '<h3 style="margin:14px 0 6px">Salida cruda del modelo (EX-01)</h3><pre class="bloque-json">' + esc(x.raw_output) + '</pre>';
    }
    if (x.batch) {
      var nn = (x.batch.nodes || []).length, ne = (x.batch.edges || []).length;
      html += '<details style="margin-top:12px"><summary>Lote candidato completo (RF-05): ' + nn + ' nodos, ' + ne + ' aristas</summary>' +
        '<pre class="bloque-json">' + esc(JSON.stringify(x.batch, null, 2)) + '</pre></details>';
    }
    return html;
  }

  function vacio(ic, titulo, texto) {
    return '<div class="vacio"><span class="icono-vacio">' + icono(ic) + '</span><strong>' + esc(titulo) + '</strong><p>' + esc(texto) + '</p></div>';
  }

  // ── Reglas (compartido: detalle y último reporte) ───────────────────────

  function tablaReglas(reglas) {
    var grupos = [['RI', 'Reglas de integridad (de la ontología, Tabla 18)'], ['RM', 'Reglas del módulo (Tabla 19)']];
    var filas = '';
    grupos.forEach(function (g) {
      var deGrupo = reglas.filter(function (r) { return r.rule.indexOf(g[0] + '-') === 0; });
      if (!deGrupo.length) return;
      filas += '<tr class="grupo"><td colspan="4">' + esc(g[1]) + '</td></tr>';
      filas += deGrupo.map(function (r) {
        var limpia = r.violations === 0;
        return '<tr class="' + (limpia ? '' : 'con-violaciones') + '"><td class="cod">' + esc(r.rule) + '</td>' +
          '<td>' + esc(REGLAS[r.rule] || '') + '</td>' +
          '<td class="num">' + (limpia
            ? '<span class="etiqueta e-ok">' + icono('check') + '0</span>'
            : '<span class="etiqueta e-error">' + icono('cruz') + r.violations + '</span>') + '</td>' +
          '<td>' + (r.sample.length ? '<ul class="muestra">' + r.sample.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>' : '<span class="nota">—</span>') + '</td></tr>';
      }).join('');
    });
    return '<div class="envoltura-tabla"><table class="tabla-reglas"><thead><tr><th>Código</th><th>Regla</th><th class="num">Violaciones</th><th>Muestra</th></tr></thead>' +
      '<tbody>' + filas + '</tbody></table></div>' +
      '<p class="nota" style="margin:8px 0 0">Enunciados: Tablas 18 y 19 de la tesis. La API devuelve solo el código, las violaciones y la muestra.</p>';
  }

  // ── Último reporte de auditoría (abajo) ─────────────────────────────────

  function pintarAuditoria() {
    var dato = estado.ejemploCompuerta ? EJEMPLO_COMPUERTA_CERRADA : estado.reporte;
    var r = dato.report;
    $('sec-auditoria').innerHTML =
      '<header><h2 id="t-auditoria">Último reporte de auditoría</h2>' +
      (estado.ejemploCompuerta ? EJEMPLO : '') +
      '<button class="btn btn-chico" type="button" id="btn-ejemplo-compuerta" aria-pressed="' + estado.ejemploCompuerta + '" style="margin-left:auto">' +
      (estado.ejemploCompuerta ? 'Volver al reporte real' : 'Ver un ejemplo con la compuerta cerrada') + '</button>' +
      '<span class="ruta" style="margin-left:0">GET /api/audit-reports/latest</span></header>' +
      '<div class="cuerpo' + (estado.ejemploCompuerta ? ' marco-ejemplo' : '') + '" style="display:grid;gap:16px">' +
      (estado.ejemploCompuerta
        ? '<p class="nota" style="margin:0">' + EJEMPLO + ' Ejemplo de la documentación de la API (<code>LatestAuditReport</code>, models.py): trae una sola regla. No es el estado real del sistema.</p>' : '') +
      (estado.ejemploCompuerta ? bloqueCompuerta(dato, true) : lineaReporte(r)) +
      (r ? tablaReglas(r.rules) : '') + '</div>';
    $('btn-ejemplo-compuerta').onclick = function () { estado.ejemploCompuerta = !estado.ejemploCompuerta; pintarAuditoria(); };
  }

  // La compuerta ya está arriba: aquí basta una línea con el reporte.
  function lineaReporte(r) {
    if (!r) return '<p class="nota" style="margin:0">Ningún camino de escritura ha registrado un reporte.</p>';
    return '<p style="margin:0;display:flex;gap:10px;flex-wrap:wrap;align-items:center">' +
      '<strong>Reporte #' + esc(r.id) + '</strong>' +
      '<span class="nota">' + esc(ORIGENES[r.origin] || r.origin) + (r.run_id ? ' · corrida ' + esc(r.run_id) : '') + ' · ' + fecha(r.created_at) + '</span>' +
      (r.completed
        ? (r.violations === 0 ? '<span class="etiqueta e-ok">' + icono('check') + 'Completo, sin violaciones</span>'
          : '<span class="etiqueta e-error">' + icono('cruz') + r.violations + ' violaciones</span>')
        : '<span class="etiqueta e-aviso">' + icono('alerta') + 'Abierto</span>') +
      '<a class="nota" href="#sec-estado" style="margin-left:auto">Estado de la compuerta ↑</a></p>';
  }

  // ── Cabecera, guía y arranque ───────────────────────────────────────────

  function menu(abrir) {
    $('menu-lista').classList.toggle('oculto', !abrir);
    $('btn-menu').setAttribute('aria-expanded', String(abrir));
  }
  function guia(ver) {
    $('guia').classList.toggle('oculto', !ver);
    try { global.localStorage.setItem('iekg.panel.guia', ver ? '1' : '0'); } catch (e) { /* nada */ }
  }

  function iniciar() {
    $('btn-menu').onclick = function (ev) { ev.stopPropagation(); menu($('menu-lista').classList.contains('oculto')); };
    document.addEventListener('click', function () { menu(false); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') menu(false); });
    $('btn-actualizar').onclick = function () { entrar().then(function () { anunciar('Datos actualizados.'); }); };
    $('btn-simular-401').onclick = function () {
      Maqueta.rechazarToken = true;
      entrar('La sesión se cerró: la API dejó de aceptar el token de esta pestaña.');
    };
    $('btn-salir').onclick = function () { Sesion.olvidar(); estado.seleccion = null; mostrarAcceso(null); };
    $('btn-guia').onclick = function () { guia(true); };
    $('btn-cerrar-guia').onclick = function () { guia(false); };

    var verGuia = true;
    try { verGuia = global.localStorage.getItem('iekg.panel.guia') !== '0'; } catch (e) { /* nada */ }
    guia(verGuia);

    if (!global.IEKG_OPERACION) {
      document.body.insertAdjacentHTML('beforeend', '<p style="padding:24px;color:var(--error)">No se cargó ../datos/datos.js.</p>');
      return;
    }
    if (Sesion.leer()) entrar(); else mostrarAcceso(null);
  }

  iniciar();
})(typeof window !== 'undefined' ? window : globalThis);
