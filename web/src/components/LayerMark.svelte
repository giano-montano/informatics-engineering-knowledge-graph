<script>
  // The shape of the layer next to a name: hexagon for CS2023, circle for the
  // syllabi; the color is that of the class (ADR-019).
  import { classColor } from '../lib/vocabulary.js';

  let { node, size = 13 } = $props();
</script>

<svg class="mark" width={size} height={size} viewBox="-8 -8 16 16" style:--c={classColor(node)} aria-hidden="true">
  {#if node.layer === 'reference'}
    <path class="outer" d="M0,-7 6.06,-3.5 6.06,3.5 0,7 -6.06,3.5 -6.06,-3.5Z" />
    <path class="inner" d="M0,-3.4 2.94,-1.7 2.94,1.7 0,3.4 -2.94,1.7 -2.94,-1.7Z" />
  {:else}
    <circle r="5.6" />
  {/if}
</svg>

<style>
  .mark {
    flex: none;
  }

  circle {
    fill: var(--c);
  }

  .outer {
    fill: color-mix(in oklch, var(--c) 18%, transparent);
    stroke: var(--c);
    stroke-width: 1.5;
    stroke-linejoin: round;
  }

  .inner {
    fill: var(--c);
  }
</style>
