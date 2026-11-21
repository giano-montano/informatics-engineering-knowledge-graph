<script>
  // The header over the canvas (C4: contextHeader): it names the focus, offers
  // the lenses that apply to its class and answers the chosen one in a
  // sentence, with another that says how to read the drawing (ADR-016).
  import { exploration } from '../lib/exploration-state.svelte.js';
  import { lensSummary, overviewSummary } from '../lib/lens-summary.js';
  import { GRAINS, GRAIN_ORDER, LENSES, LENS_ORDER, classColor, className, layerOf, lensApplies } from '../lib/vocabulary.js';
  import Icon from './Icon.svelte';
  import LayerMark from './LayerMark.svelte';
  import StopsLine from './StopsLine.svelte';

  const node = $derived(exploration.focusNode);
  const lenses = $derived(node ? LENS_ORDER.filter((lens) => lensApplies(lens, node)) : []);
  const summary = $derived.by(() => {
    const scene = exploration.scene;
    if (!scene) return { answer: '', how: '' };
    if (!node) return overviewSummary(scene.info);
    return lensSummary({ lens: exploration.lens, grain: exploration.grain, node, response: exploration.response, scene });
  });
  // The note on how to read the drawing shows open the first time a view is
  // seen in this tab, and folded behind «Cómo leerlo» from then on. A view is
  // a lens on a class of element, because the drawing of «Qué contiene»
  // differs between an area and a topic.
  const READ_KEY = 'infoknows.read-views';
  function firstReading(view) {
    try {
      const read = JSON.parse(window.sessionStorage.getItem(READ_KEY) ?? '[]');
      if (read.includes(view)) return false;
      window.sessionStorage.setItem(READ_KEY, JSON.stringify([...read, view]));
    } catch {
      // Without session storage the note stays folded, still a click away.
      return false;
    }
    return true;
  }

  const view = $derived(node ? `${exploration.lens}:${node.label}` : 'overview');
  const hasHow = $derived(Boolean(summary.how));
  let howOpen = $state(false);
  $effect(() => {
    exploration.focusKey;
    howOpen = hasHow && firstReading(view);
  });

  // On a phone the chosen question stays in sight in its strip.
  let strip = $state(null);
  $effect(() => {
    exploration.lens;
    exploration.focusKey;
    const chosen = strip?.querySelector('[aria-selected="true"]');
    if (chosen && strip.scrollWidth > strip.clientWidth) {
      const left = chosen.offsetLeft - strip.offsetLeft;
      if (left < strip.scrollLeft || left + chosen.offsetWidth > strip.scrollLeft + strip.clientWidth) {
        strip.scrollTo({ left: Math.max(0, left - 14), behavior: 'smooth' });
      }
    }
  });

  const stops = $derived(exploration.lens === 'path' && exploration.scene?.info?.stops?.length ? exploration.scene.info.stops : null);

  // Tabs: the arrows move between the lenses, and choosing follows the focus.
  function onTabKey(event, index) {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
    let next = null;
    if (step) next = (index + step + lenses.length) % lenses.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = lenses.length - 1;
    if (next === null) return;
    event.preventDefault();
    exploration.setLens(lenses[next]);
    event.currentTarget.parentElement.children[next]?.focus();
  }

  function onGrainKey(event, index) {
    const step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = (index + step + GRAIN_ORDER.length) % GRAIN_ORDER.length;
    exploration.setGrain(GRAIN_ORDER[next]);
    event.currentTarget.parentElement.querySelectorAll('button')[next]?.focus();
  }
</script>

<header class="context" style:--c={node ? classColor(node) : null}>
  {#if !node}
    <h1>Elige por dónde empezar</h1>
  {:else}
    <div class="title">
      <button class="button quiet home" type="button" onclick={() => exploration.goHome()}>
        <Icon name="home" /> <span class="home-word">Inicio</span>
      </button>
      <span class="class-chip" style:--c={classColor(node)}>{className(node)}</span>
      <h1 title={node.name_es}>{node.name_es}</h1>
      {#if node.course_code}<span class="code">{node.course_code}</span>{/if}
      <span class="layer"><LayerMark {node} />{layerOf(node).name}</span>
    </div>

    <div class="lenses" bind:this={strip} role="tablist" aria-label="Qué preguntar sobre este elemento">
      {#each lenses as lens, index (lens)}
        <button
          type="button"
          role="tab"
          id={`lens-${lens}`}
          aria-selected={exploration.lens === lens}
          aria-controls="canvas-region"
          tabindex={exploration.lens === lens ? 0 : -1}
          title={LENSES[lens].question}
          onclick={() => exploration.setLens(lens)}
          onkeydown={(event) => onTabKey(event, index)}
        >{LENSES[lens].name}</button>
      {/each}
    </div>
  {/if}

  <div class="answer">
    <div aria-live="polite">
      {#if summary.answer}
        <p class="says">
          {@html summary.answer}
          {#if summary.offer}
            <button class="text-button" type="button" onclick={() => exploration.setLens(summary.offer)}>
              Ver «{LENSES[summary.offer].name}»
            </button>
          {/if}
        </p>
      {:else if exploration.status !== 'error'}
        <p class="says"><span class="skeleton" style:width="62%"></span></p>
      {/if}
    </div>
    {#if summary.how}
      <button class="text-button how-toggle" type="button" aria-expanded={howOpen} aria-controls="how-to-read"
        onclick={() => (howOpen = !howOpen)}>{howOpen ? 'Ocultar' : 'Cómo leerlo'}</button>
    {/if}
    {#if node && exploration.expansions.size && exploration.lens === 'neighborhood'}
      <button class="text-button" type="button" onclick={() => exploration.clearExpansions()}>Quitar lo que trajiste con +</button>
    {/if}
  </div>

  {#if node && exploration.lens === 'path'}
    <div class="path-tools">
      <div class="grains" role="radiogroup" aria-label="Ver el camino por">
        <span class="grains-label" aria-hidden="true">Ver por</span>
        {#each GRAIN_ORDER as grain, index (grain)}
          <button
            type="button"
            role="radio"
            aria-checked={exploration.grain === grain}
            tabindex={exploration.grain === grain ? 0 : -1}
            onclick={() => exploration.setGrain(grain)}
            onkeydown={(event) => onGrainKey(event, index)}
          >{GRAINS[grain].name}</button>
        {/each}
      </div>
      {#if stops}<StopsLine {stops} />{/if}
    </div>
  {/if}

  {#if summary.how}
    <p class="how" id="how-to-read" hidden={!howOpen}>{@html summary.how}</p>
  {/if}
</header>

<style>
  .context {
    display: grid;
    gap: 8px;
    padding: 14px 24px 10px;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .home {
    margin-left: -10px;
    min-height: 30px;
    padding: 0 10px;
  }

  h1 {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--step-3);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.01em;
  }

  .code {
    color: var(--text-2);
    font-size: var(--step-1);
  }

  .layer {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-left: 2px;
    color: var(--text-2);
    font-size: var(--step--1);
    white-space: nowrap;
  }

  .lenses {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 2px 0;
  }

  /* The questions are pills; the chosen one is filled with the color of the
     class in focus, so the question and its subject read as one thing. */
  .lenses button {
    padding: 5px 14px;
    border: 1px solid var(--line-strong);
    border-radius: 999px;
    background: oklch(0.16 0.035 275 / 0.7);
    color: var(--text-2);
    font-weight: 550;
    transition: color 160ms, background 160ms, border-color 160ms;
  }

  .lenses button:hover {
    background: var(--hover);
    color: var(--text);
  }

  .lenses button[aria-selected='true'] {
    border-color: color-mix(in oklch, var(--c) 75%, transparent);
    background: color-mix(in oklch, var(--c) 26%, var(--ground));
    color: var(--mark);
    font-weight: 650;
  }

  .says {
    max-width: 96ch;
    font-size: var(--step-1);
    line-height: 1.45;
    text-wrap: pretty;
  }

  .says :global(strong) {
    font-weight: 700;
  }

  .path-tools {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 18px;
  }

  .grains {
    display: inline-flex;
    align-items: center;
    padding: 2px;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius-small);
  }

  .grains-label {
    padding: 0 9px 0 8px;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .grains button {
    padding: 3px 12px;
    border-radius: 4px;
    color: var(--text-2);
    font-weight: 550;
  }

  .grains button:hover {
    color: var(--text);
  }

  .grains button[aria-checked='true'] {
    background: var(--text);
    color: var(--ground-deep);
  }

  .how {
    color: var(--text-3);
    font-size: var(--step--1);
    text-wrap: pretty;
  }

  .how :global(.plus-sign) {
    display: inline-grid;
    place-items: center;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: var(--mark);
    color: var(--ground-deep);
    font-size: 12px;
    line-height: 1;
    vertical-align: 1px;
  }

  /* The answer, and beside it the controls that belong to it: the note on how
     to read the drawing and, after a +, the way back. */
  .answer {
    display: flex;
    align-items: baseline;
    gap: 14px;
  }

  /* The sentence wraps inside its own box, so the controls never take a line
     of their own. */
  .answer > div {
    min-width: 0;
  }

  .how-toggle {
    flex: none;
    color: var(--text-2);
    font-size: var(--step--1);
    white-space: nowrap;
  }

  /* A phone: one line of title and the questions in a strip that scrolls
     sideways. */
  @media (max-width: 900px) {
    .context {
      grid-template-columns: minmax(0, 1fr);
      gap: 7px;
      padding: 10px 14px 8px;
    }

    .title {
      gap: 8px;
    }

    .home {
      flex: none;
      justify-content: center;
      width: 36px;
      min-height: 36px;
      margin-left: -6px;
      padding: 0;
    }

    .home-word {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip-path: inset(50%);
    }

    h1 {
      flex: 1;
      font-size: var(--step-2);
    }

    .title .class-chip {
      order: 3;
      flex: none;
    }

    .code {
      flex: none;
      font-size: var(--step-0);
    }

    .layer {
      display: none;
    }

    .lenses {
      flex-wrap: nowrap;
      margin: 0 -14px;
      padding: 2px 14px;
      overflow-x: auto;
      scroll-padding-inline: 14px;
      scrollbar-width: none;
      -webkit-mask-image: linear-gradient(to right, transparent, black 14px, black calc(100% - 22px), transparent);
      mask-image: linear-gradient(to right, transparent, black 14px, black calc(100% - 22px), transparent);
    }

    .lenses::-webkit-scrollbar {
      display: none;
    }

    .lenses button {
      flex: none;
      min-height: 38px;
      white-space: nowrap;
    }

    .says {
      font-size: 0.9375rem;
      line-height: 1.42;
    }

    .path-tools {
      gap: 8px;
    }

    .grains button {
      min-height: 32px;
    }

    .path-tools :global(.stops) {
      flex-wrap: nowrap;
      width: calc(100% + 28px);
      margin: 0 -14px;
      padding: 2px 14px;
      overflow-x: auto;
      scrollbar-width: none;
    }

    .path-tools :global(.stops .group) {
      flex-wrap: nowrap;
    }

    .path-tools :global(.stops > li) {
      flex: none;
    }

    .path-tools :global(.stops .go),
    .path-tools :global(.stops .why) {
      min-height: 36px;
      white-space: nowrap;
    }

    .how-toggle {
      min-height: 32px;
    }
  }
</style>
