<script>
  // The entry point without a name (C4: home): it asks for the areas and the
  // courses, hands them to the canvas and lists them as text, telling apart
  // the areas that already have topics from the syllabi.
  import { ApiError, fetchOverview } from '../lib/api-client.js';
  import { exploration } from '../lib/exploration-state.svelte.js';
  import { examples, loadExamples } from '../lib/examples.svelte.js';
  import { byName, plural } from '../lib/vocabulary.js';
  import Icon from './Icon.svelte';
  import NodeLink from './NodeLink.svelte';

  let { onsearch } = $props();
  let status = $state('loading');
  let message = $state('');

  async function load() {
    status = 'loading';
    try {
      exploration.overview = await fetchOverview();
      exploration.status = 'ready';
      status = 'ready';
      loadExamples();
    } catch (error) {
      message = error instanceof ApiError ? error.message : 'No se pudo cargar el inicio.';
      status = 'error';
      exploration.status = 'ready';
    }
  }
  load();

  const areas = $derived((exploration.overview?.nodes ?? []).filter((node) => node.label === 'KnowledgeArea').sort(byName));
  const filled = $derived(areas.filter((area) => area.topics > 0));
  const bare = $derived(areas.filter((area) => !area.topics));
  const courses = $derived((exploration.overview?.nodes ?? []).filter((node) => node.label === 'Course')
    .sort((a, b) => (a.course_code ?? '').localeCompare(b.course_code ?? '')));
  const empty = $derived(status === 'ready' && !areas.length);

</script>

<aside class="panel" id="focus-panel" aria-label="Por dónde empezar" tabindex="-1">
  <header>
    <h2>Explora cómo se conecta la carrera</h2>
    <p>
      InfoKnows une lo que dicen los sílabos de Ingeniería Informática con CS2023, el estándar internacional
      del currículo de computación. Sirve para ver qué necesitas saber antes de un concepto, dónde está cada tema
      en la carrera y con qué material estudiarlo.
    </p>
  </header>

  {#if status === 'error'}
    <section role="alert" class="problem">
      <p><Icon name="alert" /> {message}</p>
      <button class="button primary" type="button" onclick={load}>Reintentar</button>
    </section>
  {:else if status === 'loading'}
    <section aria-hidden="true" class="loading">
      {#each [60, 82, 48, 70] as width (width)}<span class="skeleton" style:width={`${width}%`}></span>{/each}
    </section>
  {:else if empty}
    <section>
      <h3>El grafo está vacío</h3>
      <p class="note">Todavía no se cargó el estándar CS2023 ni ningún sílabo. El operador tiene que ejecutar la carga.</p>
    </section>
  {:else}
    {#if examples.names.length}
      <section>
        <h3>Busca por nombre</h3>
        <p class="note">Algunos nombres del grafo, al azar:</p>
        <div class="chips">
          {#each examples.names as example (example)}
            <button class="button" type="button" onclick={() => onsearch?.(example)}>{example}</button>
          {/each}
        </div>
      </section>
    {/if}

    <section>
      <h3>Cursos con sílabo <span class="count">{courses.length}</span></h3>
      {#if courses.length}
        <ul>{#each courses as course (course.key)}<li><NodeLink node={course} /></li>{/each}</ul>
      {:else}
        <p class="note">Todavía no se cargó ningún sílabo.</p>
      {/if}
    </section>

    <section>
      <h3>Áreas con temas de los sílabos <span class="count">{filled.length} de {areas.length}</span></h3>
      <ul>
        {#each filled as area (area.key)}
          <li><NodeLink node={area} /><span class="figures">{plural(area.topics, 'tema', 'temas')} · {plural(area.concepts, 'concepto', 'conceptos')}</span></li>
        {/each}
      </ul>
      {#if bare.length}
        <details>
          <summary>Áreas que ningún sílabo cargado trata todavía<span class="count">{bare.length}</span></summary>
          <ul>
            {#each bare as area (area.key)}
              <li><NodeLink node={area} /><span class="figures">{plural(area.units, 'unidad', 'unidades')} de CS2023</span></li>
            {/each}
          </ul>
        </details>
      {/if}
    </section>
  {/if}
</aside>

<style>
  .panel {
    min-height: 0;
    padding: 24px 20px 32px;
    overflow-y: auto;
    border-left: 1px solid var(--line);
    background: var(--surface);
    outline: none;
  }

  header {
    display: grid;
    gap: 10px;
    margin-bottom: 4px;
    padding: 16px;
    border: 1px solid color-mix(in oklch, var(--c-unit) 40%, transparent);
    border-radius: 14px;
    background: color-mix(in oklch, var(--c-unit) 9%, var(--surface));
  }

  header + :global(section) {
    border-top: 0;
  }

  h2 {
    font-size: var(--step-3);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.01em;
    text-wrap: balance;
  }

  header p {
    color: var(--text-2);
    text-wrap: pretty;
  }

  section {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    padding: 16px 0;
    border-top: 1px solid var(--line);
  }

  h3 {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    font-size: var(--step-1);
    font-weight: 650;
  }

  .count {
    margin-left: auto;
    color: var(--text-3);
    font-size: var(--step--1);
    font-weight: 400;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chips .button {
    min-height: 30px;
    border-radius: 999px;
    font-weight: 500;
  }

  ul,
  ol {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  ul li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-height: 32px;
  }

  .figures {
    flex: none;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .note {
    color: var(--text-3);
    font-size: var(--step--1);
  }

  summary {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    margin-left: -6px;
    padding: 0 6px;
    border-radius: var(--radius-small);
    cursor: pointer;
    font-weight: 600;
    list-style: none;
  }

  summary::-webkit-details-marker {
    display: none;
  }

  summary::before {
    content: '';
    width: 6px;
    height: 6px;
    border: solid var(--text-3);
    border-width: 0 1.6px 1.6px 0;
    transform: rotate(-45deg);
    transition: transform 160ms;
  }

  details[open] > summary::before {
    transform: rotate(45deg);
  }

  summary:hover {
    background: var(--hover);
  }

  .problem p {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .problem .button {
    justify-self: start;
  }

  .loading {
    gap: 14px;
  }
</style>
