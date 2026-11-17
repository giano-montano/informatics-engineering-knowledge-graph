<script>
  // One drawn set, one stroke: 16 px grid, 1.6 px line.
  const PATHS = {
    search: 'M7.2 12.4a5.2 5.2 0 1 0 0-10.4 5.2 5.2 0 0 0 0 10.4ZM11 11l3.2 3.2',
    home: 'M2.5 7.6 8 2.8l5.5 4.8M4 6.6v6.6h8V6.6',
    back: 'M9.8 3.2 5 8l4.8 4.8',
    external: 'M6.4 3.4H3.4v9.2h9.2V9.6M9 3h4v4M13 3 7.6 8.4',
    document: 'M4 2h5.2L12 4.8V14H4ZM9 2v3h3',
    plus: 'M8 3.2v9.6M3.2 8h9.6',
    minus: 'M3.2 8h9.6',
    fit: 'M2.8 6V2.8H6M10 2.8h3.2V6M13.2 10v3.2H10M6 13.2H2.8V10',
    close: 'M3.6 3.6l8.8 8.8M12.4 3.6l-8.8 8.8',
    chevron: 'M5.8 3.4 10.4 8l-4.6 4.6',
    map: 'M8 14s4.4-4 4.4-7.4A4.4 4.4 0 0 0 3.6 6.6C3.6 10 8 14 8 14ZM8 8.2a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2Z',
    key: 'M9.9 9.3a3.6 3.6 0 1 0-3.2-3.2L2.2 10.6v3.2h3.2v-2h2v-2Z',
    upload: 'M8 10.6V2.8M4.8 5.8 8 2.6l3.2 3.2M2.8 10.2v3h10.4v-3',
    refresh: 'M13 8a5 5 0 1 1-1.5-3.6M13 2.6v2.6h-2.6',
    check: 'M3 8.4 6.4 11.8 13 4.6',
    alert: 'M8 2.4 14 13H2ZM8 6.4v3.2M8 11.3v.1',
    clock: 'M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12ZM8 4.8V8l2.2 1.6',
    list: 'M5.6 4h8M5.6 8h8M5.6 12h8M2.6 4h.1M2.6 8h.1M2.6 12h.1',
    shield: 'M8 2 13 4v4.2c0 2.9-2 4.9-5 5.8-3-.9-5-2.9-5-5.8V4Z',
    spinner: 'M8 2.2a5.8 5.8 0 1 0 5.8 5.8',
  };
  let { name, size = 16 } = $props();
</script>

<svg class="icon" class:spin={name === 'spinner'} width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
  <path d={PATHS[name]} />
</svg>

<style>
  .icon {
    flex: none;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .spin {
    animation: spin 0.9s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
