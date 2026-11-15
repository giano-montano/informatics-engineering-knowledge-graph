<script>
  import ContextHeader from './components/ContextHeader.svelte';
  import FocusPanel from './components/FocusPanel.svelte';
  import GraphCanvas from './components/GraphCanvas.svelte';
  import Home from './components/Home.svelte';
  import Icon from './components/Icon.svelte';
  import OperatorPanel from './components/OperatorPanel.svelte';
  import Search from './components/Search.svelte';
  import { exploration } from './lib/exploration-state.svelte.js';

  let search = $state(null);
  exploration.start();

  function onKeydown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      if (exploration.view !== 'explore') exploration.goHome();
      search?.focusInput();
    } else if (event.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName) && exploration.view === 'explore') {
      event.preventDefault();
      search?.focusInput();
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="app">
  <a class="skip" href="#focus-panel">Saltar a la ficha en texto</a>
  <header class="top">
    <button class="brand" type="button" onclick={() => exploration.goHome()} aria-label="InfoKnows: ir al inicio">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
        <path d="M16 3.5 26.8 9.75v12.5L16 28.5 5.2 22.25V9.75Z" fill="none" stroke="var(--c-unit)" stroke-width="1.8" stroke-linejoin="round" />
        <circle cx="16" cy="16" r="5" fill="var(--c-concept)" />
      </svg>
      <span class="name">InfoKnows</span>
      <span class="tagline">Mapa de conocimientos de Ingeniería Informática</span>
    </button>

    {#if exploration.view === 'explore'}
      <Search bind:this={search} />
      <button class="button quiet" type="button" onclick={() => exploration.openOperator()}>
        <Icon name="key" /> Operador
      </button>
    {:else}
      <span class="where">Panel del operador</span>
      <button class="button" type="button" onclick={() => exploration.goHome()}>
        <Icon name="back" /> Volver al mapa
      </button>
    {/if}
  </header>

  {#if exploration.view === 'operator'}
    <OperatorPanel />
  {:else}
    <main class="explore">
      <div class="map">
        <ContextHeader />
        <GraphCanvas />
      </div>
      {#if exploration.focusKey}
        <FocusPanel />
      {:else}
        <Home onsearch={(text) => search?.searchFor(text)} />
      {/if}
    </main>
  {/if}
</div>

<style>
  .app {
    display: grid;
    grid-template-rows: 56px minmax(0, 1fr);
    height: 100%;
  }

  .skip {
    position: absolute;
    z-index: 100;
    top: 8px;
    left: 8px;
    padding: 8px 14px;
    border-radius: var(--radius-small);
    background: var(--text);
    color: var(--ground-deep);
    font-weight: 600;
    transform: translateY(-200%);
  }

  .skip:focus {
    transform: none;
  }

  .top {
    position: relative;
    z-index: 30;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 0 20px;
    border-bottom: 1px solid var(--line);
    background: var(--ground);
  }

  .brand {
    display: grid;
    grid-template-columns: auto auto;
    grid-template-rows: auto auto;
    align-items: center;
    column-gap: 10px;
    text-align: left;
    border-radius: var(--radius-small);
  }

  .brand svg {
    grid-row: 1 / 3;
  }

  .name {
    font-size: var(--step-2);
    font-weight: 750;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }

  .tagline {
    color: var(--text-3);
    font-size: 0.75rem;
    line-height: 1.2;
    white-space: nowrap;
  }

  .where {
    margin-right: auto;
    padding-left: 24px;
    border-left: 1px solid var(--line-strong);
    font-size: var(--step-1);
    font-weight: 600;
  }

  .explore {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 400px;
    min-height: 0;
  }

  .map {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    min-width: 0;
    min-height: 0;
  }

  @media (max-width: 1180px) {
    .explore {
      grid-template-columns: minmax(0, 1fr) 340px;
    }

    .tagline {
      display: none;
    }
  }
</style>
