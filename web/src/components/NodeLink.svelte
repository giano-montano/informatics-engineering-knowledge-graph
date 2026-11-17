<script>
  // A node as text: the alternative to its point on the map (AN-02).
  import { exploration } from '../lib/exploration-state.svelte.js';
  import { accessibleName } from '../lib/vocabulary.js';
  import LayerMark from './LayerMark.svelte';

  let { node, lens = undefined, grain = undefined, current = false } = $props();
</script>

{#if current}
  <span class="node-link current" aria-current="true">
    <LayerMark {node} /><span class="name">{node.name_es}</span>
  </span>
{:else}
  <button class="node-link" type="button" aria-label={accessibleName(node)} title={node.name_es}
    onclick={() => exploration.focus(node.key, { lens, grain })}>
    <LayerMark {node} /><span class="name">{node.name_es}</span>
    {#if node.course_code}<span class="code">{node.course_code}</span>{/if}
  </button>
{/if}

<style>
  .node-link {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    max-width: 100%;
    padding: 4px 8px;
    margin-left: -8px;
    border-radius: var(--radius-small);
    text-align: left;
    line-height: 1.3;
  }

  button.node-link:hover {
    background: var(--raised);
  }

  .name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .code {
    flex: none;
    color: var(--text-3);
    font-size: var(--step--1);
  }

  .current .name {
    font-weight: 650;
  }
</style>
