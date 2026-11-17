<script>
  // The operator panel (C4: operatorPanel): upload a document, follow its
  // run, review its discards and read the audit report. It talks to the
  // operation routes on its own, with the token the operator types: the token
  // lives in this tab only and is in no file of the build (ADR-013).
  import { onDestroy } from 'svelte';

  import Icon from './Icon.svelte';

  const TOKEN_KEY = 'infoknows.operator.token';
  const POLL_MS = 5000;

  // What the API returns as codes, in the words of the thesis (ADR-010).
  const STATES = {
    pending: { text: 'Pendiente', tone: 'neutral', icon: 'clock', means: 'Registrada; espera a que el worker la tome.' },
    running: { text: 'En curso', tone: 'info', icon: 'spinner', means: 'El worker extrae, valida o escribe el documento.' },
    completed: { text: 'Terminada', tone: 'ok', icon: 'check', means: 'Todo se escribió y la auditoría no encontró violaciones.' },
    rejected: { text: 'Rechazada', tone: 'error', icon: 'close', means: 'Salida no conforme o violaciones del validador: no se escribe nada y se registran los descartes.' },
    failed: { text: 'Fallida', tone: 'error', icon: 'alert', means: 'El proveedor no respondió o la escritura no produjo lo esperado. Sin descartes.' },
    written_not_persisted: { text: 'Escrita sin persistir', tone: 'warning', icon: 'alert', means: 'El worker se interrumpió tras escribir y antes de guardar el lote en el almacén de hechos.' },
    stopped_by_audit: { text: 'Detenida por auditoría', tone: 'warning', icon: 'shield', means: 'La auditoría halló una violación tras escribir: la compuerta suspende las pendientes.' },
  };
  const OPEN_STATES = ['pending', 'running'];
  const ORIGINS = { load: 'carga', ingestion: 'ingesta', reapplication: 'reaplicación' };
  const GATE_REASONS = {
    'no report recorded': 'No hay ningún reporte de auditoría registrado.',
    'latest report still open': 'El último reporte sigue abierto: un camino de escritura se detuvo antes de auditar.',
    'latest report with violations': 'El último reporte tiene violaciones.',
  };
  // The API returns only the code of each rule; the statements are those of
  // the thesis (integrity rules, module rules) and of ADR-010 (output checks).
  const RULES = {
    'RI-01': 'Todo nodo tiene clave no nula, y no hay dos nodos con la misma clave.',
    'RI-02': 'Todo nodo lleva la etiqueta de su clase; los cuatro niveles de conocimiento llevan además la etiqueta KnowledgeElement.',
    'RI-03': 'Todo nodo lleva exactamente una etiqueta de clase de primer nivel, y todo elemento de conocimiento exactamente un nivel.',
    'RI-04': 'Toda arista es de uno de los ocho tipos declarados.',
    'RI-05': 'Cada arista une un par de etiquetas admitido para su tipo, en la dirección de la propiedad afirmada.',
    'RI-06': 'Entre dos nodos hay como máximo una arista de cada tipo en cada dirección.',
    'RI-07': 'Ninguna unidad tiene aristas de partonomía hacia más de un área.',
    'RI-08': 'Todo concepto es parte de un tema; todo tema, de una unidad; toda unidad, de un área.',
    'RI-09': 'Todo nodo y toda arista tiene solo propiedades declaradas.',
    'RI-10': 'Si un recurso de aprendizaje tiene localizador, es un URI absoluto con esquema http o https.',
    'RM-01': 'Todo nodo tiene marca de capa, de referencia o institucional.',
    'RM-02': 'Ninguna arista sale de un nodo de referencia hacia uno institucional.',
    'RM-03': 'Todo tema, concepto y curso institucional deriva de un recurso, y toda arista de la ingesta lleva su procedencia.',
    'RM-04': 'No existen ciclos de prerrequisito ni de especialización.',
    'RM-05': 'Todo recurso de aprendizaje tiene localizador.',
    'EX-01': 'La salida del modelo no se ajusta al esquema de salida.',
    'EX-02': 'Una mención enlazada trae una clave que no está en la instantánea.',
    'EX-03': 'Una clave existente es, en la instantánea, de otra clase que la que exige su lugar en la salida.',
  };
  // The MVP admits one resource type; the API does not list them.
  const RESOURCE_TYPES = ['Sílabo'];

  function storedToken() {
    try {
      return window.sessionStorage.getItem(TOKEN_KEY) ?? '';
    } catch {
      return '';
    }
  }

  let token = $state(storedToken());
  let typed = $state('');
  // svelte-ignore state_referenced_locally
  let access = $state(token ? 'checking' : 'asking');
  let accessError = $state('');

  let runs = $state.raw([]);
  let latest = $state.raw(null);
  let problem = $state('');
  let refreshing = $state(false);
  let updatedAt = $state(null);

  let selectedId = $state(null);
  let detail = $state.raw(null);
  let discards = $state.raw(null);
  let detailStatus = $state('idle');
  let tab = $state('summary');

  let form = $state({ file: null, resourceType: RESOURCE_TYPES[0], courseCode: '', courseName: '' });
  let formErrors = $state({});
  let sending = $state(false);
  let sent = $state.raw(null);
  let fileInput = $state(null);
  let timer = null;

  class Unauthorized extends Error {}

  async function call(path, options = {}) {
    let response;
    try {
      response = await fetch(path, { ...options, headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' } });
    } catch {
      throw new Error('No se pudo conectar con el sistema.');
    }
    if (response.status === 401) throw new Unauthorized();
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const reason = typeof body?.detail === 'string' ? body.detail : `error ${response.status}`;
      const error = new Error(reason);
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function leave(message = '') {
    clearTimeout(timer);
    try {
      window.sessionStorage.removeItem(TOKEN_KEY);
    } catch { /* nothing to forget */ }
    token = '';
    typed = '';
    runs = [];
    latest = null;
    selectedId = null;
    detail = null;
    access = 'asking';
    accessError = message;
  }

  async function enter(event) {
    event?.preventDefault();
    if (event) {
      if (!typed.trim()) {
        accessError = 'Escribe el token del operador.';
        return;
      }
      token = typed.trim();
    }
    access = 'checking';
    accessError = '';
    try {
      // Listing the runs is what checks the token.
      runs = await call('/api/runs');
      try {
        window.sessionStorage.setItem(TOKEN_KEY, token);
      } catch { /* stays in memory */ }
      typed = '';
      access = 'inside';
      await refresh();
    } catch (error) {
      if (error instanceof Unauthorized) leave('El sistema rechazó ese token. Revísalo y vuelve a intentarlo.');
      else {
        token = '';
        access = 'asking';
        accessError = error.message;
      }
    }
  }

  async function refresh() {
    clearTimeout(timer);
    refreshing = true;
    try {
      [runs, latest] = await Promise.all([call('/api/runs'), call('/api/audit-reports/latest')]);
      problem = '';
      updatedAt = new Date();
      if (selectedId !== null) await loadDetail(selectedId, true);
    } catch (error) {
      if (error instanceof Unauthorized) return leave('La sesión dejó de ser válida: el sistema rechazó el token.');
      problem = error.message;
    } finally {
      refreshing = false;
    }
    // Polls only while a run can still change.
    if (access === 'inside' && runs.some((run) => OPEN_STATES.includes(run.status))) timer = setTimeout(refresh, POLL_MS);
  }

  async function loadDetail(id, quiet = false) {
    selectedId = id;
    if (!quiet) {
      detailStatus = 'loading';
      tab = 'summary';
    }
    try {
      [detail, discards] = await Promise.all([call(`/api/runs/${id}`), call(`/api/runs/${id}/discards`)]);
      detailStatus = 'ready';
    } catch (error) {
      if (error instanceof Unauthorized) return leave('La sesión dejó de ser válida: el sistema rechazó el token.');
      detailStatus = 'error';
    }
  }

  async function validate() {
    const errors = {};
    const file = form.file;
    if (!file) errors.file = 'Elige el PDF del documento.';
    else if (!file.name.toLowerCase().endsWith('.pdf')) errors.file = 'El documento tiene que ser un PDF.';
    else {
      const head = new TextDecoder().decode(await file.slice(0, 5).arrayBuffer());
      if (head !== '%PDF-') errors.file = 'El archivo no es un PDF válido.';
    }
    if (!form.courseCode.trim()) errors.courseCode = 'Escribe el código del curso, por ejemplo 1INF33.';
    if (!form.courseName.trim()) errors.courseName = 'Escribe el nombre del curso.';
    return errors;
  }

  async function submit(event) {
    event.preventDefault();
    sent = null;
    formErrors = await validate();
    if (Object.keys(formErrors).length) return;
    sending = true;
    const body = new FormData();
    body.append('file', form.file);
    body.append('resource_type', form.resourceType);
    body.append('course_code', form.courseCode.trim());
    body.append('course_name', form.courseName.trim());
    try {
      const created = await call('/api/runs', { method: 'POST', body });
      sent = { ok: true, id: created.run_id, launched: created.worker_launched };
      form = { file: null, resourceType: RESOURCE_TYPES[0], courseCode: '', courseName: '' };
      if (fileInput) fileInput.value = '';
      await refresh();
      await loadDetail(created.run_id);
    } catch (error) {
      if (error instanceof Unauthorized) return leave('La sesión dejó de ser válida: el sistema rechazó el token.');
      sent = { ok: false, message: error.status === 503
        ? 'No se pudo lanzar el worker: no se registró nada. Vuelve a subir el documento.'
        : `El sistema no aceptó el documento: ${error.message}` };
    } finally {
      sending = false;
    }
  }

  // svelte-ignore state_referenced_locally
  if (token) enter();
  onDestroy(() => clearTimeout(timer));

  const stateOf = (status) => STATES[status] ?? { text: status, tone: 'neutral', icon: 'clock', means: '' };
  const dateFormat = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'medium' });
  const when = (iso) => (iso ? dateFormat.format(new Date(iso)) : '—');

  function duration(from, to) {
    if (!from || !to) return '—';
    const seconds = Math.max(0, Math.round((new Date(to) - new Date(from)) / 1000));
    return seconds < 60 ? `${seconds} s` : `${Math.floor(seconds / 60)} min ${seconds % 60} s`;
  }

  const gate = $derived(latest?.gate ?? null);
  const families = $derived.by(() => {
    const rules = latest?.report?.rules ?? [];
    return [['RI', 'Reglas de integridad del grafo'], ['RM', 'Reglas del módulo']]
      .map(([prefix, title]) => ({ title, rules: rules.filter((rule) => rule.rule.startsWith(prefix)) }))
      .filter((family) => family.rules.length);
  });
</script>

{#snippet badge(status)}
  {@const state = stateOf(status)}
  <span class={`badge ${state.tone}`} title={state.means}><Icon name={state.icon} size={13} />{state.text}<code>{status}</code></span>
{/snippet}

{#snippet rulesTable(rules)}
  <table class="rules">
    <thead><tr><th scope="col">Regla</th><th scope="col">Enunciado</th><th scope="col" class="number">Violaciones</th></tr></thead>
    <tbody>
      {#each rules as rule (rule.rule)}
        <tr class:broken={rule.violations > 0}>
          <th scope="row"><code>{rule.rule}</code></th>
          <td>
            {RULES[rule.rule] ?? 'Regla sin enunciado en el panel.'}
            {#if rule.sample.length}
              <ul class="sample">{#each rule.sample as sample (sample)}<li><code>{sample}</code></li>{/each}</ul>
            {/if}
          </td>
          <td class="number">
            {#if rule.violations > 0}<span class="verdict bad"><Icon name="alert" size={13} />{rule.violations}</span>
            {:else}<span class="verdict good"><Icon name="check" size={13} />0</span>{/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
{/snippet}

<main class="operator">
  {#if access !== 'inside'}
    <form class="access" onsubmit={enter} novalidate>
      <h1>Acceso del operador</h1>
      <p>Las funciones de operación cargan documentos y escriben en el grafo. Escribe el token que te dio el administrador del sistema.</p>
      <label for="operator-token">Token del operador</label>
      <input id="operator-token" type="password" autocomplete="off" spellcheck="false" bind:value={typed}
        aria-invalid={Boolean(accessError)} aria-describedby={accessError ? 'access-error' : undefined} disabled={access === 'checking'} />
      {#if accessError}<p class="field-error" id="access-error" role="alert"><Icon name="alert" size={14} />{accessError}</p>{/if}
      <button class="button primary" type="submit" disabled={access === 'checking'}>
        {#if access === 'checking'}<Icon name="spinner" /> Comprobando…{:else}Entrar{/if}
      </button>
      <p class="hint">El token se guarda solo en esta pestaña y se borra al cerrarla o al salir.</p>
    </form>
  {:else}
    <div class="page">
      <header class="head">
        <h1>Panel del operador</h1>
        <p class="updated" role="status">
          {#if updatedAt}Actualizado a las {updatedAt.toLocaleTimeString('es-PE')}{/if}
          {#if runs.some((run) => OPEN_STATES.includes(run.status))} · se actualiza solo cada 5 s mientras haya corridas sin terminar{/if}
        </p>
        <button class="button" type="button" onclick={refresh} disabled={refreshing}><Icon name={refreshing ? 'spinner' : 'refresh'} /> Actualizar</button>
        <button class="button quiet" type="button" onclick={() => leave()}>Salir</button>
      </header>

      {#if problem}<p class="banner error" role="alert"><Icon name="alert" />No se pudo actualizar: {problem}</p>{/if}

      {#if gate}
        <section class={`gate ${gate.state}`} aria-label="Compuerta de auditoría">
          <Icon name="shield" size={22} />
          <div>
            <h2>Compuerta de auditoría: {gate.state === 'open' ? 'abierta' : 'cerrada'} <code>{gate.state}</code></h2>
            {#if gate.state === 'open'}
              <p>El worker toma las corridas pendientes.{#if latest.report}{' '}El último reporte ({ORIGINS[latest.report.origin] ?? latest.report.origin}, {when(latest.report.created_at)}) no tiene violaciones.{/if}</p>
            {:else}
              <p>{GATE_REASONS[gate.reason] ?? gate.reason} Las corridas nuevas quedan pendientes hasta que una carga o una reaplicación deje un reporte limpio.</p>
            {/if}
          </div>
        </section>
      {/if}

      <div class="columns">
        <section class="block" aria-labelledby="upload-title">
          <h2 id="upload-title">Cargar un documento</h2>
          <form class="upload" onsubmit={submit} novalidate>
            <div class="field">
              <label for="run-file">Documento (PDF)</label>
              <input id="run-file" type="file" accept="application/pdf,.pdf" bind:this={fileInput}
                onchange={(event) => { form.file = event.currentTarget.files[0] ?? null; }}
                aria-invalid={Boolean(formErrors.file)} aria-describedby={formErrors.file ? 'run-file-error' : undefined} />
              {#if formErrors.file}<p class="field-error" id="run-file-error"><Icon name="alert" size={14} />{formErrors.file}</p>{/if}
            </div>
            <div class="field">
              <label for="run-type">Tipo de recurso</label>
              <select id="run-type" bind:value={form.resourceType}>
                {#each RESOURCE_TYPES as type (type)}<option>{type}</option>{/each}
              </select>
            </div>
            <div class="field">
              <label for="run-code">Código del curso</label>
              <input id="run-code" type="text" autocomplete="off" spellcheck="false" placeholder="1INF33" bind:value={form.courseCode}
                aria-invalid={Boolean(formErrors.courseCode)} aria-describedby="run-code-help" />
              {#if formErrors.courseCode}<p class="field-error"><Icon name="alert" size={14} />{formErrors.courseCode}</p>{/if}
              <p class="hint" id="run-code-help">Identifica al curso: un código mal escrito crea otro curso.</p>
            </div>
            <div class="field">
              <label for="run-name">Nombre del curso</label>
              <input id="run-name" type="text" autocomplete="off" placeholder="Bases de Datos" bind:value={form.courseName}
                aria-invalid={Boolean(formErrors.courseName)} />
              {#if formErrors.courseName}<p class="field-error"><Icon name="alert" size={14} />{formErrors.courseName}</p>{/if}
            </div>
            <button class="button primary" type="submit" disabled={sending}>
              <Icon name={sending ? 'spinner' : 'upload'} /> {sending ? 'Enviando…' : 'Registrar la corrida'}
            </button>
            {#if sent?.ok}
              <p class="banner ok" role="status"><Icon name="check" />Corrida {sent.id} registrada como pendiente. {sent.launched ? 'Se lanzó el worker.' : 'El worker ya estaba activo: la tomará en su turno.'}</p>
            {:else if sent}
              <p class="banner error" role="alert"><Icon name="alert" />{sent.message}</p>
            {/if}
          </form>
        </section>

        <section class="block" aria-labelledby="runs-title">
          <h2 id="runs-title">Corridas de ingesta <span class="count">{runs.length}</span></h2>
          {#if runs.length}
            <table class="runs">
              <thead><tr><th scope="col">N.º</th><th scope="col">Curso</th><th scope="col">Estado</th><th scope="col">Registrada</th><th scope="col" class="number">Duración</th></tr></thead>
              <tbody>
                {#each [...runs].reverse() as run (run.id)}
                  <tr class:selected={run.id === selectedId}>
                    <th scope="row">
                      <button type="button" class="text-button" aria-label={`Ver la corrida ${run.id}`} aria-pressed={run.id === selectedId} onclick={() => loadDetail(run.id)}>{run.id}</button>
                    </th>
                    <td><strong>{run.course_code ?? '—'}</strong> {run.course_name ?? ''}<span class="file">{run.file_name}</span></td>
                    <td>{@render badge(run.status)}</td>
                    <td>{when(run.created_at)}</td>
                    <td class="number">{duration(run.created_at, run.finished_at)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
            <details class="states">
              <summary>Qué significa cada estado</summary>
              <dl>{#each Object.entries(STATES) as [code, state] (code)}<dt>{@render badge(code)}</dt><dd>{state.means}</dd>{/each}</dl>
            </details>
          {:else}
            <p class="empty">Todavía no hay corridas. Sube un sílabo para registrar la primera.</p>
          {/if}
        </section>
      </div>

      {#if selectedId !== null}
        <section class="block detail" aria-labelledby="detail-title">
          <h2 id="detail-title">
            Corrida {selectedId}
            {#if detail && detailStatus === 'ready'}{@render badge(detail.status)}{/if}
            <button class="button quiet close" type="button" onclick={() => { selectedId = null; detail = null; }}><Icon name="close" /> Cerrar</button>
          </h2>
          {#if detailStatus === 'loading'}
            <p class="empty"><Icon name="spinner" /> Cargando la corrida…</p>
          {:else if detailStatus === 'error' || !detail}
            <p class="banner error" role="alert"><Icon name="alert" />No se pudo leer la corrida.</p>
          {:else}
            <div class="tabs" role="tablist" aria-label="Partes de la corrida">
              {#each [['summary', 'Resumen'], ['audit', 'Auditoría de cierre'], ['discards', `Descartes · ${discards?.discards.length ?? 0}`]] as [id, title] (id)}
                <button type="button" role="tab" aria-selected={tab === id} onclick={() => (tab = id)}>{title}</button>
              {/each}
            </div>

            {#if tab === 'summary'}
              <p class="meaning">{stateOf(detail.status).means}</p>
              <dl class="facts">
                <dt>Documento</dt>
                <dd>{detail.file_name} · <a href={`/resources/${detail.resource_key}`} target="_blank" rel="noopener">Abrir el documento</a>
                  <span class="hint">Se sirve solo mientras el grafo tiene su recurso.</span></dd>
                <dt>Curso</dt><dd>{detail.course_code ?? '—'} · {detail.course_name ?? '—'} ({detail.resource_type})</dd>
                <dt>Registrada</dt><dd>{when(detail.created_at)}</dd>
                <dt>Iniciada</dt><dd>{when(detail.started_at)}</dd>
                <dt>Terminada</dt><dd>{when(detail.finished_at)} · duró {duration(detail.started_at ?? detail.created_at, detail.finished_at)}</dd>
                <dt>Modelo</dt><dd>{detail.model ?? '—'}{#if detail.model_settings} <code>{JSON.stringify(detail.model_settings)}</code>{/if}</dd>
                <dt>Versión del prompt</dt><dd>{detail.prompt_version ?? '—'}</dd>
                <dt>Reintentos de contenido</dt><dd>{detail.content_retries ?? '—'} (se permite 1)</dd>
                <dt>Tokens</dt><dd>{detail.input_tokens ?? '—'} de entrada · {detail.output_tokens ?? '—'} de salida</dd>
                {#if detail.error}<dt>Error</dt><dd class="error-text">{detail.error}</dd>{/if}
              </dl>
            {:else if tab === 'audit'}
              {#if detail.audit_report}
                <p class="meaning">
                  Reporte {detail.audit_report.id}, de {when(detail.audit_report.created_at)}:
                  {#if !detail.audit_report.completed}sigue abierto.
                  {:else if detail.audit_report.violations}{detail.audit_report.violations} violaciones.
                  {:else}sin violaciones.{/if}
                </p>
                {@render rulesTable(detail.audit_report.rules)}
              {:else}
                <p class="empty">Esta corrida no tiene reporte de auditoría: solo lo tiene una corrida que llegó a escribir en el grafo.</p>
              {/if}
            {:else if discards?.discards.length}
              <table class="rules">
                <thead><tr><th scope="col">Regla</th><th scope="col">Hecho descartado</th><th scope="col">Motivo</th></tr></thead>
                <tbody>
                  {#each discards.discards as discard, index (index)}
                    <tr class="broken">
                      <th scope="row"><code>{discard.rule}</code></th>
                      <td><code>{discard.fact}</code><span class="hint">{RULES[discard.rule] ?? ''}</span></td>
                      <td>{discard.message}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
              {#if discards.batch}
                <details><summary>Lote candidato completo ({discards.batch.nodes?.length ?? 0} nodos, {discards.batch.edges?.length ?? 0} aristas)</summary><pre>{JSON.stringify(discards.batch, null, 2)}</pre></details>
              {/if}
              {#if discards.raw_output}
                <details><summary>Salida del modelo, tal como llegó</summary><pre>{discards.raw_output}</pre></details>
              {/if}
            {:else}
              <p class="empty">
                {#if detail.status === 'rejected'}La corrida se rechazó sin descartes registrados.
                {:else if OPEN_STATES.includes(detail.status)}La corrida todavía no terminó: si se rechaza, sus descartes aparecerán aquí.
                {:else}No hubo descartes: solo una corrida rechazada los registra.{/if}
              </p>
            {/if}
          {/if}
        </section>
      {/if}

      <section class="block" aria-labelledby="report-title">
        <h2 id="report-title">Último reporte de auditoría</h2>
        {#if latest?.report}
          <p class="meaning">
            Reporte {latest.report.id}, abierto por {ORIGINS[latest.report.origin] ?? latest.report.origin}{latest.report.run_id ? ` (corrida ${latest.report.run_id})` : ''} el {when(latest.report.created_at)}:
            {#if !latest.report.completed}sigue abierto.
            {:else}{latest.report.rules.length} reglas, {latest.report.violations} violaciones.{/if}
          </p>
          {#each families as family (family.title)}
            <h3>{family.title}</h3>
            {@render rulesTable(family.rules)}
          {/each}
        {:else}
          <p class="empty">Todavía no hay ningún reporte. Lo deja la carga del estándar CS2023.</p>
        {/if}
      </section>
    </div>
  {/if}
</main>

<style>
  .operator {
    min-height: 0;
    overflow-y: auto;
    background: var(--ground-deep);
  }

  .access {
    display: grid;
    gap: 12px;
    width: min(420px, calc(100% - 40px));
    margin: 12vh auto 0;
    padding: 28px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
  }

  h1 {
    font-size: var(--step-3);
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  .access p {
    color: var(--text-2);
  }

  .access .button {
    justify-content: center;
    min-height: 38px;
  }

  label {
    font-weight: 600;
  }

  input[type='text'],
  input[type='password'],
  input[type='file'],
  select {
    width: 100%;
    min-height: 38px;
    padding: 0 11px;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius-small);
    background: var(--ground-deep);
    color: var(--text);
    font: inherit;
  }

  input[type='file'] {
    padding: 6px;
  }

  input::file-selector-button {
    margin-right: 10px;
    padding: 4px 10px;
    border: 1px solid var(--line-strong);
    border-radius: 4px;
    background: var(--raised);
    color: var(--text);
    font: inherit;
    cursor: pointer;
  }

  input::placeholder {
    color: var(--text-3);
  }

  input:focus-visible,
  select:focus-visible {
    outline-offset: 0;
  }

  input[aria-invalid='true'] {
    border-color: var(--danger);
  }

  .field-error {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--danger) !important;
    font-size: var(--step--1);
  }

  .hint {
    display: block;
    color: var(--text-3) !important;
    font-size: var(--step--1);
  }

  .page {
    display: grid;
    gap: 20px;
    max-width: 1280px;
    margin: 0 auto;
    padding: 28px 28px 56px;
  }

  .head {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .updated {
    margin: 0 auto 0 8px;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .banner {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 10px 12px;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius-small);
    background: var(--surface);
  }

  .banner.error {
    border-color: var(--danger);
  }

  .banner.error :global(.icon) {
    color: var(--danger);
  }

  .banner.ok {
    border-color: var(--success);
  }

  .banner.ok :global(.icon) {
    color: var(--success);
  }

  .gate {
    display: flex;
    gap: 14px;
    padding: 16px 18px;
    border: 1px solid var(--success);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .gate :global(.icon) {
    margin-top: 2px;
    color: var(--success);
  }

  .gate.closed {
    border-color: var(--warning);
  }

  .gate.closed :global(.icon) {
    color: var(--warning);
  }

  .gate p {
    color: var(--text-2);
  }

  h2 {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: var(--step-2);
    font-weight: 650;
  }

  h3 {
    margin-top: 6px;
    color: var(--text-2);
    font-size: var(--step-0);
    font-weight: 600;
  }

  code {
    padding: 1px 5px;
    border-radius: 4px;
    background: var(--raised);
    color: var(--text-2);
    font-family: var(--mono);
    font-size: 0.8em;
    font-weight: 400;
  }

  .columns {
    display: grid;
    grid-template-columns: 340px minmax(0, 1fr);
    gap: 20px;
    align-items: start;
  }

  .block {
    display: grid;
    gap: 14px;
    padding: 20px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .count {
    color: var(--text-3);
    font-size: var(--step-0);
    font-weight: 400;
  }

  .upload {
    display: grid;
    gap: 14px;
  }

  .field {
    display: grid;
    gap: 5px;
  }

  .upload .button {
    justify-self: start;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th,
  td {
    padding: 9px 10px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }

  thead th {
    color: var(--text-3);
    font-size: var(--step--1);
    font-weight: 500;
  }

  tbody th {
    font-weight: 400;
    white-space: nowrap;
  }

  tbody tr:last-child > * {
    border-bottom: 0;
  }

  .number {
    text-align: right;
    white-space: nowrap;
  }

  tr.selected {
    background: var(--raised);
  }

  .file {
    display: block;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 9px 2px 7px;
    border: 1px solid var(--line-strong);
    border-radius: 999px;
    font-size: var(--step--1);
    font-weight: 600;
    white-space: nowrap;
  }

  .badge code {
    padding: 0;
    background: none;
    color: var(--text-3);
  }

  .badge.ok {
    border-color: var(--success);
  }

  .badge.ok :global(.icon) {
    color: var(--success);
  }

  .badge.error {
    border-color: var(--danger);
  }

  .badge.error :global(.icon) {
    color: var(--danger);
  }

  .badge.warning {
    border-color: var(--warning);
  }

  .badge.warning :global(.icon) {
    color: var(--warning);
  }

  .states summary,
  details summary {
    color: var(--text-2);
    cursor: pointer;
  }

  .states dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 8px 14px;
    margin: 12px 0 0;
    color: var(--text-2);
    font-size: var(--step--1);
  }

  dd {
    margin: 0;
  }

  .empty {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-3);
  }

  .detail .close {
    margin-left: auto;
    font-size: var(--step-0);
  }

  .tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid var(--line);
  }

  .tabs button {
    padding: 7px 14px 9px;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    color: var(--text-2);
    font-weight: 550;
  }

  .tabs button:hover {
    color: var(--text);
  }

  .tabs button[aria-selected='true'] {
    border-bottom-color: var(--mark);
    color: var(--mark);
  }

  .meaning {
    color: var(--text-2);
  }

  .facts {
    display: grid;
    grid-template-columns: 190px 1fr;
    gap: 8px 16px;
    margin: 0;
  }

  .facts dt {
    color: var(--text-3);
  }

  .error-text {
    color: var(--danger);
  }

  .rules tr.broken th code {
    color: var(--danger);
  }

  .verdict {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .verdict.good :global(.icon) {
    color: var(--success);
  }

  .verdict.bad {
    color: var(--danger);
    font-weight: 650;
  }

  .sample {
    margin: 6px 0 0;
    padding: 0;
    list-style: none;
  }

  pre {
    max-height: 320px;
    margin: 10px 0 0;
    padding: 12px;
    overflow: auto;
    border-radius: var(--radius-small);
    background: var(--ground-deep);
    color: var(--text-2);
    font-family: var(--mono);
    font-size: 0.78rem;
  }

  @media (max-width: 1080px) {
    .columns {
      grid-template-columns: 1fr;
    }
  }
</style>
