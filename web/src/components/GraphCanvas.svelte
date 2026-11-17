<script>
  // Hosts the canvas (C4: canvas) and what sits on it: the trail of visited
  // elements, the one-line legend of what is on screen, the «Fuentes» switch
  // and the zoom. D3 draws inside `host`; Svelte never touches it (ADR-017).
  import { onDestroy } from 'svelte';

  import { createCanvas } from '../lib/canvas-renderer.js';
  import { exploration, relationOf } from '../lib/exploration-state.svelte.js';
  import { nodeByKey } from '../lib/graph-reading.js';
  import { CLASSES, CLASS_ORDER, LAYERS, RELATIONS, className } from '../lib/vocabulary.js';
  import Icon from './Icon.svelte';
  import LayerMark from './LayerMark.svelte';

  let host = $state(null);
  let zoom = $state(1);
  let canvas = null;
  let lastFocus;

  $effect(() => {
    const scene = exploration.scene;
    if (!host) return;
    canvas ??= createCanvas(host, {
      onFocus: (key) => exploration.focus(key),
      onExpand: (key) => exploration.expand(key),
      onEdge: (drawn) => {
        const source = drawn.sourceNode ?? findNode(drawn.edge.source);
        const target = findNode(drawn.edge.target);
        if (source && target) exploration.selectRelation(relationOf(drawn.edge, source, target, drawn.document));
      },
      onZoom: (k) => (zoom = k),
    });
    if (scene) {
      canvas.render(scene, { instant: lastFocus === undefined });
      lastFocus = scene.focusKey;
    }
  });

  $effect(() => {
    const marked = exploration.markedEdge;
    // Runs after the render above, which redraws the edges.
    exploration.scene;
    canvas?.select(marked);
  });

  onDestroy(() => canvas?.destroy());

  function findNode(key) {
    for (const subgraph of [exploration.response, exploration.detail, ...exploration.expansions.values()]) {
      const found = subgraph && nodeByKey(subgraph, key);
      if (found) return found;
    }
    return null;
  }

  // The legend names only the shapes and the colors that are on screen.
  const legend = $derived.by(() => {
    const scene = exploration.scene;
    if (!scene) return { layers: [], classes: [] };
    const layers = new Set(scene.nodes.map((placed) => placed.node.layer));
    const classes = new Map();
    for (const placed of scene.nodes) classes.set(placed.node.label, placed.node);
    return {
      layers: Object.keys(LAYERS).filter((layer) => layers.has(layer)),
      classes: CLASS_ORDER.filter((label) => classes.has(label)).map((label) => classes.get(label)),
    };
  });

  const SAMPLE = {
    reference: { layer: 'reference', label: 'KnowledgeUnit' },
    institutional: { layer: 'institutional', label: 'Concept' },
  };
</script>

<section class="stage" id="canvas-region" aria-label="Mapa" aria-busy={exploration.status === 'loading'}>
  {#if exploration.status === 'loading'}<div class="progress" role="status"><span class="sr-only">Cargando</span></div>{/if}

  <div class="host" bind:this={host}></div>

  {#if exploration.status === 'error' && exploration.error}
    <div class="problem" role="alert">
      <Icon name="alert" size={20} />
      <div>
        <p class="what">{exploration.error.message}</p>
        <p>El mapa no cambió. Puedes volver a intentarlo o regresar al inicio.</p>
        <div class="actions">
          {#if exploration.error.retry}
            <button class="button primary" type="button" onclick={exploration.error.retry}>Reintentar</button>
          {/if}
          <button class="button" type="button" onclick={() => exploration.goHome()}>Ir al inicio</button>
        </div>
      </div>
    </div>
  {:else if !exploration.scene && exploration.status === 'loading'}
    <p class="waiting">Cargando el mapa…</p>
  {/if}

  {#if exploration.notice}
    {#key exploration.notice.id}
      <div class="notice" role="status">
        <span>{exploration.notice.text}</span>
        <button type="button" aria-label="Cerrar el aviso" onclick={() => exploration.dismissNotice()}><Icon name="close" size={14} /></button>
      </div>
    {/key}
  {/if}

  <div class="bar">
    <nav class="trail" aria-label="Visitado">
      <button class="step-back" type="button" disabled={!exploration.canGoBack} onclick={() => exploration.back()}
        aria-label="Volver al anterior (Alt + flecha izquierda)" title="Volver al anterior (Alt + ←)">
        <Icon name="back" />
      </button>
      <span class="trail-title">Visitado</span>
      {#if exploration.trail.length}
        <ol>
          {#each exploration.trail as visited (visited.key)}
            <li>
              <button type="button" class:current={visited.key === exploration.focusKey}
                aria-current={visited.key === exploration.focusKey ? 'true' : undefined}
                title={visited.name_es} onclick={() => exploration.focus(visited.key)}>
                <LayerMark node={visited} size={11} /><span>{visited.name_es}</span>
              </button>
            </li>
          {/each}
        </ol>
      {:else}
        <span class="trail-empty">Lo que visites queda aquí, para volver.</span>
      {/if}
    </nav>

    <div class="tools">
      {#if legend.classes.length}
        <ul class="legend" aria-label="Qué hay en el mapa">
          {#each legend.layers as layer (layer)}
            <li><LayerMark node={SAMPLE[layer]} />{LAYERS[layer].of}</li>
          {/each}
          <li class="divider" aria-hidden="true"></li>
          {#each legend.classes as sample (sample.label)}
            <li><i style:--c={CLASSES[sample.label].color}></i>{className(sample)}</li>
          {/each}
        </ul>
      {/if}

      <div class="controls">
        <button class="toggle" type="button" role="switch" aria-checked={exploration.showSources}
          title="Dibuja la línea de cada elemento a su documento" onclick={() => exploration.toggleSources()}>
          <span class="track"><span class="thumb"></span></span>Fuentes
        </button>
        <button class="tool wide" type="button" popovertarget="full-legend"><Icon name="list" />Leyenda</button>
        <span class="split" aria-hidden="true"></span>
        <button class="tool" type="button" aria-label="Alejar" title="Alejar" onclick={() => canvas?.zoomBy(1 / 1.3)}><Icon name="minus" /></button>
        <span class="zoom" aria-label={`Zoom ${Math.round(zoom * 100)} por ciento`}>{Math.round(zoom * 100)} %</span>
        <button class="tool" type="button" aria-label="Acercar" title="Acercar" onclick={() => canvas?.zoomBy(1.3)}><Icon name="plus" /></button>
        <button class="tool" type="button" aria-label="Encuadrar todo" title="Encuadrar todo" onclick={() => canvas?.fit()}><Icon name="fit" /></button>
      </div>
    </div>
  </div>

  <div id="full-legend" class="full-legend" popover>
    <h2>Cómo leer el mapa</h2>
    <h3>La forma dice de dónde viene</h3>
    <ul>
      <li><LayerMark node={SAMPLE.reference} size={16} /><span><b>Hexágono con contorno:</b> CS2023, el estándar internacional del currículo de computación (ACM/IEEE).</span></li>
      <li><LayerMark node={SAMPLE.institutional} size={16} /><span><b>Círculo relleno:</b> lo que dicen los sílabos de los cursos de la PUCP.</span></li>
    </ul>
    <h3>El color dice qué es</h3>
    <ul class="grid">
      {#each CLASS_ORDER as label (label)}
        <li><i style:--c={CLASSES[label].color}></i>{label === 'LearningResource' ? 'Sílabo o documento' : CLASSES[label].name}</li>
      {/each}
    </ul>
    <h3>Las líneas son relaciones</h3>
    <ul class="grid">
      {#each Object.entries(RELATIONS) as [type, relation] (type)}
        <li><span class="stroke" class:dashed={type === 'WAS_DERIVED_FROM'} style:--c={relation.color}></span>{relation.out}</li>
      {/each}
    </ul>
    <p>Una flecha sale de lo que se aprende primero. Elige una línea para ver qué documento la afirma.</p>
    <h3>Con el teclado</h3>
    <p>Tab recorre los puntos; las flechas pasan al punto más cercano; Enter pone un punto en foco y + trae sus conexiones. Ctrl K busca y Alt + ← vuelve al anterior.</p>
  </div>
</section>

<style>
  .stage {
    position: relative;
    min-height: 0;
    overflow: hidden;
    /* Deep space with one cloud of light, in the hue of the interface: the
       classes and the relations keep the color for themselves. */
    background:
      radial-gradient(ellipse 60% 52% at 38% 44%, oklch(0.34 0.13 285 / 0.62), transparent 72%),
      radial-gradient(ellipse 46% 42% at 74% 68%, oklch(0.34 0.1 245 / 0.42), transparent 72%),
      var(--space);
    border-top: 1px solid var(--line);
  }

  /* A few fixed stars. They do not move: the map is what moves. */
  .stage::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0.6;
    pointer-events: none;
    background-image:
      radial-gradient(1px 1px at 23px 41px, oklch(1 0 0 / 0.7), transparent 60%),
      radial-gradient(1px 1px at 127px 13px, oklch(0.9 0.04 275 / 0.6), transparent 60%),
      radial-gradient(1.5px 1.5px at 181px 157px, oklch(0.9 0.06 230 / 0.55), transparent 60%),
      radial-gradient(1px 1px at 61px 193px, oklch(1 0 0 / 0.45), transparent 60%),
      radial-gradient(1px 1px at 233px 97px, oklch(0.9 0.05 300 / 0.5), transparent 60%);
    background-size: 260px 230px;
  }

  .host {
    position: absolute;
    inset: 0;
  }

  .progress {
    position: absolute;
    z-index: 6;
    inset: 0 0 auto;
    height: 2px;
    overflow: hidden;
  }

  .progress::before {
    content: '';
    position: absolute;
    inset: 0;
    width: 38%;
    background: var(--mark);
    animation: slide 1.1s var(--ease) infinite;
  }

  @keyframes slide {
    from {
      transform: translateX(-100%);
    }
    to {
      transform: translateX(270%);
    }
  }

  .waiting {
    position: absolute;
    inset: 40% 0 auto;
    color: var(--text-3);
    text-align: center;
  }

  .problem {
    position: absolute;
    z-index: 7;
    top: 50%;
    left: 50%;
    display: flex;
    gap: 14px;
    width: min(460px, calc(100% - 48px));
    padding: 20px;
    border: 1px solid var(--danger);
    border-radius: var(--radius);
    background: var(--surface);
    box-shadow: var(--shadow);
    transform: translate(-50%, -50%);
    color: var(--text-2);
  }

  .problem :global(.icon) {
    margin-top: 2px;
    color: var(--danger);
  }

  .problem .what {
    margin-bottom: 4px;
    color: var(--text);
    font-size: var(--step-1);
    font-weight: 650;
  }

  .actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
  }

  /* Over the trail, where no layout draws: the fit keeps that strip clear. */
  .notice {
    position: absolute;
    z-index: 6;
    left: 16px;
    bottom: 64px;
    display: flex;
    align-items: center;
    gap: 12px;
    max-width: min(560px, calc(100% - 32px));
    padding: 9px 10px 9px 14px;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius-small);
    background: var(--raised);
    box-shadow: var(--shadow);
    animation: rise 320ms var(--ease);
  }

  .notice button {
    display: flex;
    padding: 4px;
    border-radius: 4px;
    color: var(--text-2);
  }

  .notice button:hover {
    background: var(--hover);
  }

  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
  }

  .bar {
    position: absolute;
    z-index: 4;
    inset: auto 16px 14px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 14px;
    pointer-events: none;
  }

  .bar > * {
    pointer-events: auto;
  }

  .trail,
  .controls,
  .legend {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: oklch(0.175 0.03 275 / 0.94);
  }

  .trail {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1 1 320px;
    max-width: 640px;
    height: 40px;
    padding: 0 10px 0 4px;
  }

  .step-back {
    display: grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border-radius: var(--radius-small);
  }

  .step-back:hover:not(:disabled) {
    background: var(--hover);
  }

  .step-back:disabled {
    color: var(--line-strong);
  }

  .trail-title {
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .trail-empty {
    overflow: hidden;
    color: var(--text-3);
    font-size: var(--step--1);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .trail ol {
    display: flex;
    gap: 4px;
    min-width: 0;
    margin: 0;
    padding: 0;
    overflow-x: auto;
    list-style: none;
    scrollbar-width: none;
  }

  .trail li button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    max-width: 190px;
    padding: 3px 9px;
    border: 1px solid transparent;
    border-radius: 999px;
    color: var(--text-2);
    font-size: var(--step--1);
    white-space: nowrap;
  }

  .trail li button span {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .trail li button:hover {
    background: var(--hover);
    color: var(--text);
  }

  .trail li button.current {
    border-color: var(--line-strong);
    color: var(--text);
    font-weight: 600;
  }

  .tools {
    position: relative;
    flex: none;
  }

  .tools .legend {
    position: absolute;
    right: 0;
    bottom: calc(100% + 8px);
  }

  .legend {
    display: flex;
    gap: 14px;
    margin: 0;
    padding: 7px 12px;
    white-space: nowrap;
    list-style: none;
    color: var(--text-2);
    font-size: var(--step--1);
  }

  .legend li,
  .full-legend li {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .legend .divider {
    width: 1px;
    background: var(--line-strong);
  }

  i {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--c);
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 2px;
    height: 40px;
    padding: 0 5px;
  }

  .tool,
  .toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    min-width: 30px;
    height: 30px;
    padding: 0 6px;
    border-radius: var(--radius-small);
    color: var(--text-2);
  }

  .tool.wide,
  .toggle {
    padding: 0 10px;
  }

  .tool:hover,
  .toggle:hover {
    background: var(--hover);
    color: var(--text);
  }

  .track {
    display: inline-flex;
    align-items: center;
    width: 28px;
    height: 16px;
    padding: 2px;
    border-radius: 999px;
    background: var(--line-strong);
    transition: background 160ms;
  }

  .thumb {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--text-2);
    transition: transform 200ms var(--ease), background 160ms;
  }

  .toggle[aria-checked='true'] {
    color: var(--text);
  }

  .toggle[aria-checked='true'] .track {
    background: var(--text);
  }

  .toggle[aria-checked='true'] .thumb {
    background: var(--ground-deep);
    transform: translateX(12px);
  }

  .split {
    width: 1px;
    height: 18px;
    margin: 0 4px;
    background: var(--line-strong);
  }

  .zoom {
    min-width: 46px;
    color: var(--text-2);
    font-size: var(--step--1);
    text-align: center;
  }

  .full-legend {
    inset: auto 24px 72px auto;
    width: 400px;
    max-height: calc(100vh - 160px);
    margin: 0;
    padding: 18px 20px;
    overflow-y: auto;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    background: var(--surface);
    box-shadow: var(--shadow);
    color: var(--text-2);
  }

  .full-legend h2 {
    color: var(--text);
    font-size: var(--step-2);
  }

  .full-legend h3 {
    margin: 16px 0 8px;
    color: var(--text);
    font-size: var(--step-0);
    font-weight: 650;
  }

  .full-legend ul {
    display: grid;
    gap: 7px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .full-legend ul.grid {
    grid-template-columns: 1fr 1fr;
  }

  .full-legend li {
    align-items: flex-start;
    gap: 9px;
  }

  .full-legend li :global(.mark),
  .full-legend i {
    margin-top: 4px;
  }

  .full-legend b {
    color: var(--text);
    font-weight: 600;
  }

  .full-legend p {
    margin-top: 10px;
    font-size: var(--step--1);
  }

  .stroke {
    flex: none;
    width: 22px;
    height: 0;
    margin-top: 10px;
    border-top: 2px solid var(--c);
  }

  .stroke.dashed {
    border-top-style: dotted;
  }
</style>
