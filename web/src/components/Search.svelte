<script>
  // The entry point by name (C4: search): a combobox driven from the
  // keyboard, with the class and the layer of every result, and an empty
  // state that offers to walk the areas.
  import { searchByName } from '../lib/api-client.js';
  import { exploration } from '../lib/exploration-state.svelte.js';
  import { examples, loadExamples } from '../lib/examples.svelte.js';
  import { screen } from '../lib/screen.svelte.js';
  import { classColor, className, layerOf } from '../lib/vocabulary.js';
  import Icon from './Icon.svelte';
  import LayerMark from './LayerMark.svelte';

  let input = $state(null);
  let text = $state('');
  let open = $state(false);
  let status = $state('idle');
  let results = $state.raw([]);
  let asked = $state('');
  let active = $state(-1);
  let pending = null;
  let timer = null;
  loadExamples();

  export function focusInput() {
    input?.focus();
    input?.select();
  }

  /** Fills the box and searches at once: the example searches use it. */
  export function searchFor(query) {
    text = query;
    input?.focus();
    run(query);
  }

  async function run(query) {
    pending?.abort();
    const wanted = query.trim();
    if (!wanted) {
      status = 'idle';
      results = [];
      open = false;
      return;
    }
    pending = new AbortController();
    status = 'loading';
    open = true;
    try {
      const response = await searchByName(wanted, pending.signal);
      // Only what matched carries a score; the rest is the provenance of the matches.
      results = response.nodes.filter((node) => node.score !== undefined);
      asked = wanted;
      active = results.length ? 0 : -1;
      status = 'ready';
    } catch (error) {
      if (error.name === 'AbortError') return;
      status = 'error';
    }
  }

  function onInput() {
    clearTimeout(timer);
    timer = setTimeout(() => run(text), 160);
  }

  function choose(node) {
    open = false;
    text = '';
    status = 'idle';
    input?.blur();
    exploration.focus(node.key);
  }

  function seeAreas() {
    open = false;
    text = '';
    exploration.goHome();
  }

  function onKeydown(event) {
    if (event.key === 'Escape') {
      if (open) open = false;
      else {
        text = '';
        input?.blur();
      }
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!open && text.trim()) return run(text);
      if (!results.length) return;
      const step = event.key === 'ArrowDown' ? 1 : -1;
      active = (active + step + results.length) % results.length;
      document.getElementById(`search-option-${active}`)?.scrollIntoView({ block: 'nearest' });
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (open && results[active]) choose(results[active]);
      else run(text);
    }
  }

  function onFocusOut(event) {
    if (!event.currentTarget.contains(event.relatedTarget)) open = false;
  }
</script>

<div class="search" onfocusout={onFocusOut}>
  <label class="sr-only" for="search-input">Buscar un tema, un concepto, una unidad, un área o un curso por nombre</label>
  <span class="lens"><Icon name={status === 'loading' ? 'spinner' : 'search'} /></span>
  <input
    id="search-input"
    bind:this={input}
    bind:value={text}
    type="text"
    enterkeyhint="search"
    role="combobox"
    autocomplete="off"
    spellcheck="false"
    placeholder={screen.compact ? 'Busca un tema o un curso' : 'Busca un tema, un concepto o un curso'}
    aria-expanded={open}
    aria-controls="search-results"
    aria-autocomplete="list"
    aria-activedescendant={open && active >= 0 ? `search-option-${active}` : undefined}
    oninput={onInput}
    onkeydown={onKeydown}
    onfocus={() => { if (text.trim() && status !== 'idle') open = true; }}
  />
  <kbd aria-hidden="true">Ctrl K</kbd>

  {#if open}
    <div class="results" id="search-results">
      {#if status === 'error'}
        <div class="state" role="alert">
          <p>No se pudo buscar: el sistema no respondió.</p>
          <button class="button" type="button" onclick={() => run(text)}>Reintentar</button>
        </div>
      {:else if status === 'ready' && !results.length}
        <div class="state" role="status">
          <p class="lead">Ningún sílabo cargado trata «{asked}»</p>
          <p>Tampoco hay un área o una unidad de CS2023 con ese nombre. Prueba con otra palabra o recorre las áreas.</p>
          <div class="actions">
            <button class="button primary" type="button" onclick={seeAreas}>Ver las áreas</button>
            {#each examples.names.slice(0, 4) as example (example)}
              <button class="button" type="button" onclick={() => searchFor(example)}>{example}</button>
            {/each}
          </div>
        </div>
      {:else if results.length}
        <p class="count" role="status">
          {results.length === 1 ? '1 resultado' : `${results.length} resultados`} para «{asked}»{results.length === 20 ? ' (los 20 primeros)' : ''}
        </p>
        <ul role="listbox" aria-label="Resultados de la búsqueda">
          {#each results as node, index (node.key)}
            <!-- The keyboard drives the list from the input (aria-activedescendant). -->
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <li
              id={`search-option-${index}`}
              role="option"
              aria-selected={index === active}
              class:active={index === active}
              onpointermove={() => (active = index)}
              onmousedown={(event) => event.preventDefault()}
              onclick={() => choose(node)}
            >
              <LayerMark {node} size={15} />
              <span class="name">{node.name_es}{#if node.course_code}<span class="code">{node.course_code}</span>{/if}</span>
              <span class="class-chip" style:--c={classColor(node)}>{className(node)}</span>
              <span class="layer">{layerOf(node).name}</span>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="count" role="status">Buscando…</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .search {
    position: relative;
    flex: 1;
    max-width: 620px;
  }

  .lens {
    position: absolute;
    left: 13px;
    top: 50%;
    display: flex;
    transform: translateY(-50%);
    color: var(--text-3);
    pointer-events: none;
  }

  input {
    width: 100%;
    height: 38px;
    padding: 0 70px 0 38px;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    background: var(--ground-deep);
    color: var(--text);
    caret-color: var(--mark);
    font: inherit;
    font-size: var(--step-1);
    outline: none;
    transition: border-color 160ms, box-shadow 160ms;
  }

  input::placeholder {
    color: var(--text-3);
  }

  input:focus {
    border-color: var(--mark);
    box-shadow: 0 0 0 3px oklch(0.99 0 0 / 0.14);
  }

  kbd {
    position: absolute;
    right: 10px;
    top: 50%;
    padding: 1px 7px;
    border: 1px solid var(--line-strong);
    border-radius: 5px;
    transform: translateY(-50%);
    color: var(--text-3);
    font: inherit;
    font-size: 0.75rem;
    pointer-events: none;
  }

  .results {
    position: absolute;
    z-index: 40;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    max-height: min(70vh, 560px);
    overflow-y: auto;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    background: var(--surface);
    box-shadow: var(--shadow);
  }

  .count {
    padding: 10px 14px 6px;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  ul {
    margin: 0;
    padding: 0 6px 6px;
    list-style: none;
  }

  li {
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: var(--radius-small);
    cursor: pointer;
  }

  li.active {
    background: var(--hover);
  }

  .name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--step-1);
  }

  .code {
    margin-left: 8px;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .layer {
    min-width: 84px;
    color: var(--text-2);
    font-size: var(--step--1);
    text-align: right;
  }

  .state {
    display: grid;
    gap: 8px;
    padding: 18px;
    color: var(--text-2);
  }

  .state .lead {
    color: var(--text);
    font-size: var(--step-1);
    font-weight: 650;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
  }

  @media (max-width: 900px), (pointer: coarse) {
    input {
      padding-right: 12px;
    }

    kbd {
      display: none;
    }
  }

  /* A phone: the results take the width of the screen, under the bar. */
  @media (max-width: 900px) {
    input {
      height: 40px;
    }

    .results {
      position: fixed;
      top: 60px;
      left: 8px;
      right: 8px;
      max-height: calc(100dvh - 76px);
    }

    li {
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 10px;
      min-height: 48px;
      padding: 10px;
    }

    .name {
      overflow: visible;
      white-space: normal;
      text-wrap: pretty;
      line-height: 1.3;
    }

    .layer {
      display: none;
    }

    .actions .button {
      min-height: 40px;
    }
  }
</style>
