// Whether the page is laid out for a phone: the map first and the record in a
// sheet over it. The width is the one of the media queries in the components.
const query = typeof matchMedia === 'function' ? matchMedia('(max-width: 900px)') : null;

export const screen = $state({ compact: query?.matches ?? false });

query?.addEventListener('change', (event) => {
  screen.compact = event.matches;
});
