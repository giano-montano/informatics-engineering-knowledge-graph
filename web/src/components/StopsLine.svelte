<script>
  // The path in one line (C4: stopsLine): the stops in the order to go
  // through them, each with its «¿Por qué?», up to the goal.
  import { exploration } from '../lib/exploration-state.svelte.js';
  import { containsTarget } from '../lib/graph-reading.js';
  import { GRAINS, accessibleName } from '../lib/vocabulary.js';
  import LayerMark from './LayerMark.svelte';

  let { stops } = $props();

  // Stops at the same distance have no order among them: they go together.
  const groups = $derived.by(() => {
    const list = [];
    for (const stop of stops) {
      const last = list.at(-1);
      if (last && last.depth === stop.depth) last.items.push(stop);
      else list.push({ depth: stop.depth, items: [stop] });
    }
    return list;
  });

  const same = $derived(GRAINS[exploration.grain].same);
</script>

<ol class="stops" aria-label="Paradas del camino, de la más lejana a la meta">
  {#each groups as group, index (group.depth)}
    {#if index > 0}<li class="arrow" aria-hidden="true"><svg width="28" height="10" viewBox="0 0 28 10"><path class="shaft" d="M0 5h21" /><path d="M20 1.4 27 5l-7 3.6Z" /></svg></li>{/if}
    <li class="group">
      {#each group.items as stop (stop.key)}
        {@const own = containsTarget(exploration.response, stop.key, exploration.focusKey)}
        {@const openWhy = exploration.whyStop === stop.key}
        <span class="stop" class:open={openWhy}>
          <button class="go" type="button" aria-label={accessibleName(stop)} onclick={() => exploration.focus(stop.key)}>
            <LayerMark node={stop} />
            <span>{stop.name_es}</span>
            {#if stop.course_code}<span class="code">{stop.course_code}</span>{/if}
          </button>
          {#if own}<span class="own" title={`Lo que se necesita antes está en ${same} que la meta`}>{same}</span>{/if}
          <button
            class="why"
            type="button"
            aria-expanded={openWhy}
            aria-label={`¿Por qué pasar por ${stop.name_es}? Ver la relación y su fuente`}
            onclick={() => exploration.toggleWhy(stop.key)}
          >¿Por qué?</button>
        </span>
      {/each}
    </li>
  {/each}
  <li class="arrow" aria-hidden="true"><svg width="28" height="10" viewBox="0 0 28 10"><path class="shaft" d="M0 5h21" /><path d="M20 1.4 27 5l-7 3.6Z" /></svg></li>
  <li class="goal">y de ahí a la meta</li>
</ol>

<style>
  .stops {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 10px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .stop {
    display: inline-flex;
    align-items: stretch;
    border: 1px solid var(--line-strong);
    border-radius: 999px;
    background: var(--surface);
    overflow: hidden;
  }

  .stop.open {
    border-color: var(--mark);
  }

  .go {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 4px 6px 4px 11px;
    font-weight: 600;
  }

  .go:hover,
  .why:hover {
    background: var(--hover);
  }

  .code {
    color: var(--text-3);
    font-size: var(--step--1);
    font-weight: 400;
  }

  .own {
    align-self: center;
    margin-right: 6px;
    padding: 0 7px;
    border-radius: 999px;
    background: var(--raised);
    color: var(--text-2);
    font-size: 0.75rem;
    white-space: nowrap;
  }

  .why {
    padding: 4px 12px 4px 9px;
    border-left: 1px solid var(--line);
    color: var(--text-2);
    font-size: var(--step--1);
    text-decoration: underline;
    text-decoration-color: var(--text-3);
    text-underline-offset: 3px;
  }

  .stop.open .why {
    color: var(--mark);
  }

  .arrow {
    display: flex;
  }

  .arrow path {
    fill: var(--r-prerequisite);
  }

  .arrow .shaft {
    fill: none;
    stroke: var(--r-prerequisite);
    stroke-width: 1.5;
  }

  .goal {
    color: var(--text-2);
    font-size: var(--step--1);
  }
</style>
