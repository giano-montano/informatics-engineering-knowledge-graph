<script>
  // The panel of the focus (C4: focusPanel): the element read as a record,
  // with the same sections the header offers as lenses. It is also the text
  // alternative to the canvas: everything drawn is listed here (AN-02).
  import { tick } from 'svelte';

  import { fetchSubgraph } from '../lib/api-client.js';
  import { exploration, relationOf } from '../lib/exploration-state.svelte.js';
  import {
    connections, countByClass, documentOfEdge, justifyStop, kindsOf, learningOrder, locationChains, nodeByKey,
    partsOf, containsTarget, prerequisitesByDepth, previousCourses, resourcesOf, sourcesOf,
  } from '../lib/graph-reading.js';
  import {
    GRAINS, KNOWLEDGE_ELEMENTS, LENSES, RELATIONS, classColor, className, layerOf, lensApplies, plural,
  } from '../lib/vocabulary.js';
  import DocLink from './DocLink.svelte';
  import Icon from './Icon.svelte';
  import LayerMark from './LayerMark.svelte';
  import NodeLink from './NodeLink.svelte';
  import RelationCard from './RelationCard.svelte';

  const node = $derived(exploration.focusNode);
  const key = $derived(exploration.focusKey);
  const detail = $derived(exploration.detail);

  // Up to five calls in parallel, all to existing routes; the client reuses
  // the one the active lens already made.
  let facts = $state.raw({ key: null, status: 'loading' });
  $effect(() => {
    const focus = node;
    if (!focus) return;
    const wanted = focus.key;
    facts = { key: wanted, status: 'loading' };
    const ask = (applies, path) => (applies ? fetchSubgraph(path, wanted).catch(() => null) : null);
    Promise.all([
      ask(KNOWLEDGE_ELEMENTS.includes(focus.label), '/api/elements/location'),
      ask(lensApplies('prerequisites', focus), '/api/concepts/prerequisites'),
      ask(lensApplies('resources', focus), '/api/elements/resources'),
      ask(lensApplies('courses', focus), '/api/courses/prerequisites'),
      ask(lensApplies('kinds', focus), '/api/concepts/specializations'),
    ]).then(([location, prerequisites, resources, courses, kinds]) => {
      if (exploration.focusKey !== wanted) return;
      facts = { key: wanted, status: 'ready', location, prerequisites, resources, courses, kinds };
    });
  });
  const ready = $derived(facts.status === 'ready' && facts.key === key);

  const sources = $derived(node && detail ? (node.label === 'LearningResource' ? [node] : sourcesOf(detail, key)) : []);
  const groups = $derived(detail && key ? connections(detail, key) : []);
  const chains = $derived(ready && facts.location && lensApplies('location', node) ? locationChains(facts.location, key) : []);
  const contents = $derived.by(() => {
    if (!ready || !facts.location || !lensApplies('contents', node)) return null;
    const counts = countByClass(partsOf(facts.location, key));
    const order = learningOrder(facts.location, key);
    const steps = order.steps
      .map((step) => (node.label === 'Topic' ? step : step.filter((concept) => order.related.has(concept.key))))
      .filter((step) => step.length);
    const figures = [['KnowledgeUnit', 'unidad', 'unidades'], ['Topic', 'tema', 'temas'], ['Concept', 'concepto', 'conceptos']]
      .filter(([label]) => (label !== 'KnowledgeUnit' || node.label === 'KnowledgeArea') && (label !== 'Topic' || node.label !== 'Topic'))
      .map(([label, one, many]) => ({ count: counts[label] ?? 0, word: (counts[label] ?? 0) === 1 ? one : many }));
    return { counts, order, steps, figures, parts: partsOf(facts.location, key) };
  });
  const before = $derived(ready && facts.prerequisites ? prerequisitesByDepth(facts.prerequisites, key) : null);
  const dependents = $derived(groups.find((group) => group.id === 'HAS_PREREQUISITE:in')?.items ?? []);
  const courses = $derived(ready && facts.courses ? previousCourses(facts.courses, key) : null);
  const kinds = $derived(ready && facts.kinds ? kindsOf(facts.kinds, key) : null);
  const material = $derived(ready && facts.resources ? resourcesOf(facts.resources) : null);
  const ownTopic = $derived(chains[0]?.find((link) => link.label === 'Topic') ?? null);

  const why = $derived.by(() => {
    if (!exploration.whyStop || exploration.lens !== 'path' || !exploration.response) return null;
    const response = exploration.response;
    const stop = nodeByKey(response, exploration.whyStop);
    if (!stop) return null;
    return {
      stop,
      own: containsTarget(response, stop.key, key),
      steps: justifyStop(response, stop.key, key).map((edge) => relation(edge, response)),
    };
  });

  function relation(edge, subgraph) {
    return relationOf(edge, nodeByKey(subgraph, edge.source), nodeByKey(subgraph, edge.target), documentOfEdge(subgraph, edge));
  }

  async function showSource(edge, subgraph) {
    exploration.selectRelation(relation(edge, subgraph));
    await tick();
    document.getElementById('selected-relation')?.focus();
  }

  // A card that opens from the map is brought into view.
  $effect(() => {
    if (exploration.selectedRelation || why) {
      tick().then(() => document.querySelector('.card')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }));
    }
  });

  let scroller = $state(null);
  $effect(() => {
    key;
    if (scroller) scroller.scrollTop = 0;
  });
</script>

{#snippet heading(title, lens)}
  <h3>
    <span>{title}</span>
    {#if lens && lensApplies(lens, node)}
      {#if exploration.lens === lens}
        <span class="on-map"><Icon name="map" size={13} />En el mapa</span>
      {:else}
        <button class="text-button see" type="button" onclick={() => exploration.setLens(lens)}>Ver en el mapa</button>
      {/if}
    {/if}
  </h3>
{/snippet}

{#snippet sourceButton(edge, subgraph, name)}
  <button class="source" type="button" aria-label={`Ver la fuente de la relación con ${name}`} onclick={() => showSource(edge, subgraph)}>fuente</button>
{/snippet}

{#snippet row(item, subgraph)}
  <li><NodeLink node={item.node} />{@render sourceButton(item.edge, subgraph, item.node.name_es)}</li>
{/snippet}

<aside class="panel" id="focus-panel" aria-label="Ficha del elemento en foco" bind:this={scroller} tabindex="-1">
  {#if node && detail}
    <header class="record" style:--c={classColor(node)}>
      <p class="chips">
        <span class="class-chip">{className(node)}</span>
        <span class="layer"><LayerMark {node} />{layerOf(node).name}</span>
      </p>
      <h2>{node.name_es}</h2>
      {#if node.name_en}<p class="english" lang="en">{node.name_en}</p>{/if}
      {#if node.course_code}<p class="code">Código {node.course_code}</p>{/if}
      {#if node.description}<p class="description">{node.description}</p>{/if}
      <div class="origin">
        <span class="by">{node.label === 'LearningResource' ? 'Documento' : 'Fuente'}</span>
        {#each sources as source (source.key)}
          <DocLink document={source} text={node.label === 'LearningResource' ? `Abrir ${source.name_es}` : undefined} />
        {:else}
          <span class="note">no se registró de dónde sale</span>
        {/each}
      </div>
      <p class="note">{layerOf(node).detail}</p>
    </header>

    {#if exploration.selectedRelation}
      <section class="card" id="selected-relation" tabindex="-1" aria-label="Relación seleccionada">
        <h3>
          <span>Relación seleccionada</span>
          <button class="close" type="button" aria-label="Cerrar la relación seleccionada" onclick={() => exploration.clearRelation()}><Icon name="close" size={14} /></button>
        </h3>
        <RelationCard relation={exploration.selectedRelation} focusKey={key} />
      </section>
    {/if}

    {#if why}
      <section class="card" aria-label={`Por qué pasar por ${why.stop.name_es}`}>
        <h3>
          <span>¿Por qué pasar por «{why.stop.name_es}»?</span>
          <button class="close" type="button" aria-label="Cerrar" onclick={() => exploration.toggleWhy(why.stop.key)}><Icon name="close" size={14} /></button>
        </h3>
        {#if why.own}<p class="note">Lo que se necesita antes está en {GRAINS[exploration.grain].same} que la meta.</p>{/if}
        {#if why.steps.length}
          <ol class="why-steps">
            {#each why.steps as step (step.id)}
              <li><RelationCard relation={step} focusKey={key} /></li>
            {/each}
          </ol>
        {:else}
          <p class="note">La respuesta no trae las relaciones que unen esta parada con la meta.</p>
        {/if}
      </section>
    {/if}

    {#if !ready}
      <div class="loading" aria-hidden="true">
        {#each [70, 52, 84, 44, 66] as width (width)}<span class="skeleton" style:width={`${width}%`}></span>{/each}
      </div>
      <p class="sr-only" role="status">Cargando la ficha</p>
    {:else}
      {#if chains.length}
        <section class:active={exploration.lens === 'location'}>
          {@render heading('Dónde está en la carrera', 'location')}
          {#each chains as chain, index (index)}
            <ol class="chain" aria-label="De lo más general a lo más específico">
              {#each chain as link (link.key)}
                <li><span class="level">{className(link)}</span><NodeLink node={link} /></li>
              {/each}
              <li><span class="level">{className(node)}</span><NodeLink {node} current /></li>
            </ol>
          {/each}
        </section>
      {:else if node.label === 'Course'}
        <section>
          {@render heading('Dónde está en la carrera')}
          <p class="note">Un curso no es parte de CS2023: se ubica por lo que enseña, que está en «Conexiones», más abajo.</p>
        </section>
      {/if}

      {#if contents}
        <section class:active={exploration.lens === 'contents'}>
          {@render heading('Qué contiene', 'contents')}
          <p class="figures">
            {#each contents.figures as figure (figure.word)}<span><b>{figure.count}</b> {figure.word}</span>{/each}
          </p>
          {#if !contents.counts.Topic && node.label !== 'Topic'}
            <p class="note">Esta parte de CS2023 todavía no aparece en ningún sílabo cargado.</p>
          {/if}
          {#if contents.order.related.size}
            <h4>En qué orden aprenderlo{node.label === 'Topic' ? '' : ' (solo los conceptos que dependen entre sí)'}</h4>
            <ol class="steps">
              {#each contents.steps as step, index (index)}
                <li>
                  <span class="step">Paso {index + 1}</span>
                  <ul>{#each step as concept (concept.key)}<li><NodeLink node={concept} /></li>{/each}</ul>
                </li>
              {/each}
            </ol>
          {:else if contents.order.concepts.length}
            <p class="note">Sus conceptos no dependen entre sí: se pueden aprender en cualquier orden.</p>
            <ul class="list">{#each contents.order.concepts as concept (concept.key)}<li><NodeLink node={concept} /></li>{/each}</ul>
          {/if}
          {#if node.label !== 'Topic' && contents.parts.some((part) => part.label !== 'Concept')}
            <details>
              <summary>Unidades y temas<span class="count">{contents.parts.filter((part) => part.label !== 'Concept').length}</span></summary>
              <ul class="list">
                {#each contents.parts.filter((part) => part.label !== 'Concept').sort((a, b) => a.label.localeCompare(b.label) || a.name_es.localeCompare(b.name_es, 'es')) as part (part.key)}
                  <li><NodeLink node={part} /></li>
                {/each}
              </ul>
            </details>
          {/if}
        </section>
      {/if}

      {#if before}
        <section class:active={exploration.lens === 'prerequisites'}>
          {@render heading('Qué necesitas antes', 'prerequisites')}
          {#each before as group (group.depth)}
            <h4>{group.depth === 1 ? 'Justo antes' : `${group.depth} pasos antes`}</h4>
            <ul class="list">
              {#each group.items as item (item.node.key)}
                <li><NodeLink node={item.node} />{#if item.edge}{@render sourceButton(item.edge, facts.prerequisites, item.node.name_es)}{/if}</li>
              {/each}
            </ul>
          {:else}
            <p class="note">No necesita nada antes, según los sílabos cargados.</p>
            {#if dependents.length}
              <h4>Se necesita para</h4>
              <ul class="list">{#each dependents as item (item.node.key)}{@render row(item, detail)}{/each}</ul>
            {/if}
          {/each}
        </section>
      {/if}

      {#if courses}
        <section class:active={exploration.lens === 'courses'}>
          {@render heading('Cursos que conviene llevar antes', 'courses')}
          {#each courses.previous as previous (previous.course.key)}
            <div class="previous">
              <NodeLink node={previous.course} />
              <h4>porque enseña lo que este curso pide</h4>
              <ul class="list">{#each previous.evidence as item (item.node.key)}{@render row(item, facts.courses)}{/each}</ul>
            </div>
          {:else}
            <p class="note">Ningún otro curso cargado enseña lo que este pide.</p>
          {/each}
          <h4>Lo que pide · {courses.required.length}</h4>
          {#if courses.required.length}
            <ul class="list">{#each courses.required as item (item.node.key)}{@render row(item, facts.courses)}{/each}</ul>
          {:else}
            <p class="note">No pide conceptos previos.</p>
          {/if}
          <details open={exploration.lens === 'courses'}>
            <summary>Lo que enseña<span class="count">{courses.taught.length}</span></summary>
            <ul class="list">{#each courses.taught as item (item.node.key)}{@render row(item, facts.courses)}{/each}</ul>
          </details>
        </section>
      {/if}

      {#if kinds}
        <section class:active={exploration.lens === 'kinds'}>
          {@render heading('Tipos', 'kinds')}
          {#if kinds.general.length}
            <h4>Es un tipo de</h4>
            <ul class="list">{#each kinds.general as item (item.node.key)}{@render row(item, facts.kinds)}{/each}</ul>
          {/if}
          {#if kinds.kinds.length}
            <h4>Sus tipos</h4>
            <ul class="list">{#each kinds.kinds as item (item.node.key)}{@render row(item, facts.kinds)}{/each}</ul>
          {/if}
          {#if !kinds.all.length}
            <p class="note">No es un tipo de otro concepto ni tiene tipos registrados.</p>
          {/if}
        </section>
      {/if}

      {#if material}
        <section class:active={exploration.lens === 'resources'}>
          {@render heading('Material de estudio', 'resources')}
          {#each material as entry (entry.resource.key)}
            <div class="resource">
              <DocLink document={entry.resource} text={`Abrir ${entry.resource.name_es}`} />
              <span class="kind">{entry.type?.name_es ?? 'Recurso'}</span>
              {#if entry.about.some((element) => element.key !== key)}
                <p class="about">
                  Llega por
                  {#each entry.about.filter((element) => element.key !== key) as element, index (element.key)}{index ? ', ' : ' '}<button class="text-button" type="button" onclick={() => exploration.focus(element.key)}>{element.name_es}</button>{/each}
                </p>
              {/if}
            </div>
          {:else}
            {#if node.label === 'Concept'}
              <p class="note">Un concepto no tiene material propio: los sílabos describen temas.</p>
              {#if ownTopic}
                <button class="button" type="button" onclick={() => exploration.focus(ownTopic.key, { lens: 'resources' })}>
                  Ver el material de su tema, «{ownTopic.name_es}»
                </button>
              {/if}
            {:else}
              <p class="note">Ningún sílabo cargado trata sobre este elemento ni sobre sus partes.</p>
            {/if}
          {/each}
        </section>
      {/if}
    {/if}

    <section class:active={exploration.lens === 'neighborhood'}>
      {@render heading('Conexiones', 'neighborhood')}
      {#each groups as group (group.id)}
        <details open={group.items.length <= 8}>
          <summary>
            <span class="relation" style:--c={RELATIONS[group.type].color}>{group.title}</span>
            <span class="count">{group.items.length}</span>
          </summary>
          <ul class="list">{#each group.items as item (item.node.key)}{@render row(item, detail)}{/each}</ul>
        </details>
      {:else}
        <p class="note">No tiene conexiones registradas.</p>
      {/each}
      {#if node.more_neighbors}
        <p class="note">Se muestran hasta 25 conexiones directas.</p>
      {/if}
      {#if exploration.lens === 'neighborhood' && exploration.scene?.info}
        {@const info = exploration.scene.info}
        {#if info.brought?.length}
          <details open>
            <summary>Lo que trajiste con +<span class="count">{info.brought.length}</span></summary>
            <ul class="list">
              {#each info.brought as item (item.node.key)}
                <li><NodeLink node={item.node} /><span class="through">de {item.through.name_es}</span></li>
              {/each}
            </ul>
          </details>
        {/if}
        {#if info.farItems?.length}
          <details>
            <summary>Un paso más lejos<span class="count">{info.farItems.length}</span></summary>
            <ul class="list">
              {#each info.farItems as item (item.node.key)}
                <li><NodeLink node={item.node} /><span class="through">por {item.through.name_es}</span></li>
              {/each}
            </ul>
            {#if info.farTotal > info.farItems.length}
              <p class="note">Hay {info.farTotal - info.farItems.length} más a un paso: entra a un vecino o tráelos con +.</p>
            {/if}
          </details>
        {/if}
      {/if}
    </section>
  {/if}
</aside>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding: 20px 20px 32px;
    overflow-y: auto;
    border-left: 1px solid var(--line);
    background: var(--surface);
    outline: none;
  }

  .record {
    display: grid;
    gap: 6px;
    padding-bottom: 18px;
  }

  .chips {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .layer {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--text-2);
    font-size: var(--step--1);
  }

  h2 {
    margin-top: 4px;
    font-size: var(--step-3);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.01em;
    text-wrap: balance;
  }

  .english {
    color: var(--text-2);
    font-style: italic;
  }

  .code {
    color: var(--text-2);
  }

  .origin {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
  }

  .by {
    color: var(--text-2);
  }

  .note {
    color: var(--text-3);
    font-size: var(--step--1);
  }

  section {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 6px;
    padding: 16px 0;
    border-top: 1px solid var(--line);
  }

  section.active {
    margin: 0 -20px;
    padding: 16px 20px;
    background: var(--raised);
  }

  section.active + section {
    border-top-color: transparent;
  }

  h3 {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
    font-size: var(--step-1);
    font-weight: 650;
  }

  .see,
  .on-map {
    flex: none;
    font-size: var(--step--1);
    font-weight: 500;
  }

  .on-map {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: var(--text-2);
  }

  h4 {
    margin: 8px 0 0;
    color: var(--text-3);
    font-size: var(--step--1);
    font-weight: 500;
  }

  ul,
  ol {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .list > li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 30px;
  }

  .source {
    flex: none;
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--text-2);
    font-size: var(--step--1);
    text-decoration: underline;
    text-decoration-color: var(--text-3);
    text-underline-offset: 3px;
  }

  .source:hover {
    color: var(--text);
    background: var(--hover);
  }

  .through {
    flex: none;
    max-width: 45%;
    overflow: hidden;
    color: var(--text-3);
    font-size: var(--step--1);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .card {
    display: grid;
    gap: 10px;
    margin: 0 -8px 16px;
    padding: 14px;
    border: 1px solid var(--mark);
    border-radius: var(--radius);
    background: var(--ground);
    outline: none;
    animation: reveal 300ms var(--ease);
  }

  @keyframes reveal {
    from {
      opacity: 0;
      transform: translateY(-6px);
    }
  }

  .card h3 {
    align-items: center;
    margin: 0;
  }

  .close {
    display: flex;
    padding: 5px;
    border-radius: 4px;
    color: var(--text-2);
  }

  .close:hover {
    background: var(--hover);
    color: var(--text);
  }

  .why-steps {
    display: grid;
    gap: 14px;
  }

  .why-steps li + li {
    padding-top: 14px;
    border-top: 1px dashed var(--line-strong);
  }

  .chain {
    display: grid;
    gap: 2px;
  }

  .chain li {
    display: grid;
    grid-template-columns: 68px 1fr;
    align-items: center;
    min-height: 30px;
  }

  .level {
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .figures {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 18px;
    color: var(--text-2);
  }

  .figures b {
    color: var(--text);
    font-size: var(--step-2);
    font-weight: 700;
  }

  .steps {
    display: grid;
    gap: 8px;
    margin-top: 4px;
  }

  .steps > li {
    display: grid;
    grid-template-columns: 68px 1fr;
    align-items: start;
    padding-top: 8px;
    border-top: 1px dashed var(--line);
  }

  .steps > li:first-child {
    padding-top: 0;
    border-top: 0;
  }

  .step {
    padding-top: 5px;
    color: var(--r-prerequisite);
    font-size: var(--step--1);
    font-weight: 650;
  }

  .steps li li {
    min-height: 30px;
    display: flex;
    align-items: center;
  }

  .previous {
    display: grid;
    gap: 2px;
    margin-bottom: 6px;
  }

  .previous h4 {
    margin: 0;
  }

  details {
    margin-top: 2px;
  }

  summary {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 30px;
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

  .relation {
    color: var(--c);
  }

  .count {
    margin-left: auto;
    color: var(--text-3);
    font-size: var(--step--1);
    font-weight: 400;
  }

  .resource {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px 10px;
    padding: 4px 0;
  }

  .kind {
    color: var(--text-2);
    font-size: var(--step--1);
  }

  .about {
    flex-basis: 100%;
    color: var(--text-2);
    font-size: var(--step--1);
  }

  .loading {
    display: grid;
    gap: 14px;
    padding: 18px 0;
    border-top: 1px solid var(--line);
  }
</style>
