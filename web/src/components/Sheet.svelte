<script>
  // On a phone, the record (the home or the focus panel) rides over the map in
  // a sheet: a peek with its first lines, or the whole height. It goes back to
  // the peek whenever the map changes, so what the visitor asked is in sight,
  // and rises when a relation or a «¿Por qué?» opens in it.
  import { untrack } from 'svelte';

  import { exploration } from '../lib/exploration-state.svelte.js';

  let { children } = $props();

  let level = $state('peek');
  let height = $state(0);
  let peekHeight = $state(0);
  let drag = $state(null);
  let sheet = $state(null);

  const peekOffset = $derived(Math.max(0, height - peekHeight));
  const offset = $derived(drag?.moved ? drag.offset : level === 'full' ? 0 : peekOffset);

  // The map changed: back to the peek.
  $effect(() => {
    exploration.focusKey;
    exploration.lens;
    untrack(() => {
      level = 'peek';
      sheet?.querySelector('.panel')?.scrollTo?.({ top: 0 });
    });
  });

  // Something opened in the record that the map points to: up.
  $effect(() => {
    if (exploration.selectedRelation || exploration.whyStop) untrack(() => (level = 'full'));
  });

  function toggle() {
    level = level === 'full' ? 'peek' : 'full';
  }

  // In the peek the whole sheet is a handle; at full height only the grip is,
  // so the record scrolls.
  function onPointerDown(event) {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    const fromGrip = event.target.closest('.grip');
    if (level === 'full' && !fromGrip) return;
    drag = { id: event.pointerId, y: event.clientY, start: offset, offset, moved: false, t: performance.now(), v: 0, fromGrip };
  }

  function onPointerMove(event) {
    if (!drag || event.pointerId !== drag.id) return;
    const dy = event.clientY - drag.y;
    if (!drag.moved && Math.abs(dy) < 6) return;
    if (!drag.moved) sheet.setPointerCapture(event.pointerId);
    const now = performance.now();
    const next = Math.min(peekOffset, Math.max(0, drag.start + dy));
    drag = { ...drag, moved: true, v: (next - drag.offset) / Math.max(1, now - drag.t), offset: next, t: now };
  }

  function onPointerUp(event) {
    if (!drag || event.pointerId !== drag.id) return;
    const { moved, offset: at, v, fromGrip } = drag;
    drag = null;
    if (moved) {
      // A flick decides; otherwise the nearer end.
      if (Math.abs(v) > 0.4) level = v < 0 ? 'full' : 'peek';
      else level = at < peekOffset / 2 ? 'full' : 'peek';
      return;
    }
    // A tap: on the grip it toggles; on the peek's text, it opens.
    if (fromGrip) return;
    if (level === 'peek' && !event.target.closest('a, button, summary, input, label')) level = 'full';
  }

  function onFocusIn(event) {
    if (level === 'peek' && event.target.matches?.(':focus-visible') && !event.target.closest('.grip')) level = 'full';
  }

  function onKeydown(event) {
    if (event.key === 'Escape' && level === 'full') {
      level = 'peek';
      sheet?.querySelector('.grip')?.focus();
    }
  }
</script>

<div
  class="sheet"
  class:dragging={drag?.moved}
  data-level={level}
  bind:this={sheet}
  bind:clientHeight={height}
  style:transform={`translateY(${offset}px)`}
  onpointerdown={onPointerDown}
  onpointermove={onPointerMove}
  onpointerup={onPointerUp}
  onpointercancel={() => (drag = null)}
  onfocusin={onFocusIn}
  onkeydown={onKeydown}
  role="presentation"
>
  <span class="peek-probe" aria-hidden="true" bind:clientHeight={peekHeight}></span>
  <button class="grip" type="button" aria-expanded={level === 'full'} onclick={toggle}
    aria-label={level === 'full' ? 'Bajar la ficha y ver el mapa' : 'Subir la ficha'}>
    <span class="bar" aria-hidden="true"></span>
  </button>
  <div class="content">
    {@render children()}
  </div>
</div>

<style>
  .sheet {
    position: absolute;
    z-index: 20;
    inset: 8px 0 0;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    border: 1px solid var(--line-strong);
    border-bottom: 0;
    border-radius: 18px 18px 0 0;
    background: var(--surface);
    box-shadow: 0 -10px 32px -12px oklch(0.05 0.02 275 / 0.85);
    transition: transform 380ms var(--ease);
    will-change: transform;
  }

  .sheet.dragging {
    transition: none;
  }

  .sheet[data-level='peek'] {
    touch-action: none;
  }

  /* Measures the peek: the same height the map leaves free below it. */
  .peek-probe {
    position: absolute;
    visibility: hidden;
    height: var(--peek);
    pointer-events: none;
  }

  .grip {
    display: grid;
    place-items: center;
    height: 26px;
    border-radius: 18px 18px 0 0;
    touch-action: none;
  }

  .grip:focus-visible {
    outline-offset: -3px;
  }

  .bar {
    width: 40px;
    height: 4px;
    border-radius: 999px;
    background: var(--line-strong);
  }

  .content {
    display: grid;
    min-height: 0;
  }

  .content :global(.panel) {
    padding-top: 2px;
    padding-bottom: calc(32px + env(safe-area-inset-bottom));
    border-left: 0;
    background: none;
    overscroll-behavior: contain;
  }

  /* In the peek the record does not scroll, and fades out where it is cut. */
  .sheet[data-level='peek'] .content :global(.panel),
  .sheet[data-level='peek'] .content :global(.panel *) {
    touch-action: none;
  }

  .sheet[data-level='peek'] .content :global(.panel) {
    overflow: hidden;
    -webkit-mask-image: linear-gradient(to bottom, black calc(var(--peek) - 72px), transparent calc(var(--peek) - 30px));
    mask-image: linear-gradient(to bottom, black calc(var(--peek) - 72px), transparent calc(var(--peek) - 30px));
  }
</style>
