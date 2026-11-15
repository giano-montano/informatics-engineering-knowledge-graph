<script>
  // One statement of the graph with the document that makes it (CU-10).
  import { RELATIONS } from '../lib/vocabulary.js';
  import DocLink from './DocLink.svelte';
  import NodeLink from './NodeLink.svelte';

  let { relation, focusKey = null } = $props();
</script>

<div class="relation">
  <p class="statement">
    <NodeLink node={relation.source} current={relation.source.key === focusKey} />
    <span class="phrase" style:--c={RELATIONS[relation.edge.type].color}>{RELATIONS[relation.edge.type].phrase}</span>
    <NodeLink node={relation.target} current={relation.target.key === focusKey} />
  </p>
  <p class="said">
    {#if relation.document}
      <span class="by">{relation.edge.provenance ? 'Lo dice' : 'Lo define'}</span>
      <DocLink document={relation.document} />
    {:else}
      <span class="by">Sin fuente registrada</span>
    {/if}
  </p>
</div>

<style>
  .relation {
    display: grid;
    gap: 8px;
  }

  .statement {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 2px 10px;
    padding-left: 8px;
  }

  .phrase {
    color: var(--c);
    font-weight: 600;
  }

  .said {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .by {
    color: var(--text-2);
  }
</style>
