# ADR-017: Framework de la aplicación web: Svelte 5 con Vite, como SPA estática

**Estado:** Aceptada
**Fecha:** 2026-11
**Atributos:** AN-01 (principal)

## Contexto

La aplicación web es una SPA que se sirve aparte, con nginx (ADR-007), y solo presenta: la lógica
de navegación vive en la API. El estado que maneja es pequeño, pero lo comparten el lienzo, el
panel, la cabecera y el rastro: foco, lente, grano y expansiones. De que ese estado sea uno solo depende que todas las
preguntas se respondan desde el mismo lugar (AN-01). El lienzo es de D3 (ADR-018), que
necesita controlar su propio SVG.

La tesis deja el framework «a definir» en la Tabla 5, en la fila de R6.

## Decisión

- **Svelte 5.57.3 con Vite 8.3.8 y `@sveltejs/vite-plugin-svelte` 7.3.1, sin SvelteKit**:
  compilado estático, sin servidor de Node en producción. El plugin admite Vite 8 y Svelte desde
  la 5.46.4, y pide Node 20.19, 22.12 o 24 en adelante en la máquina de desarrollo.
- **El lienzo es un componente que le entrega a D3 un nodo del DOM**, con `$effect`, y Svelte no
  lo toca.
- **Las versiones se fijan exactas** en `package.json` y en el archivo de bloqueo de R6.

La maqueta de R5 usa JS sin framework: el diseño no depende de él.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| React 19.3.1 | Su DOM virtual compite con D3 por el mismo SVG, y hay que aislarlo con `ref`. Además pesa más en tiempo de ejecución. |
| Vue 3.5.45 | Viable y cercano: un empate técnico. Se prefiere Svelte por la menor carga en tiempo de ejecución y porque su reactividad no envuelve en *proxies* los objetos que D3 muta. Era el framework de P2 y P3. |
| JS sin framework, como la maqueta | Alcanza para la maqueta. En R6, con el panel del operador y el estado reflejado en la URL, el estado repartido a mano se vuelve frágil. |
| SvelteKit | Agrega enrutado y renderizado en un servidor de Node que una SPA estática detrás de nginx no usa. |

## Consecuencias

- La salida es un paquete estático chico, que nginx sirve tal cual.
- Los componentes de la vista de nivel 3 de la aplicación web (`docs/architecture/model.c4`)
  pasan casi uno a uno a componentes `.svelte`.
- Negativa: hay paso de compilación, con Node en la máquina de desarrollo, y Svelte 5 (*runes*)
  tiene menos material de consulta que React.

## Fuentes

- Registro de npm (`registry.npmjs.org`), consultado el 2026-11-15 (oficial). Última versión
  estable y su fecha de publicación: `svelte` 5.57.3 (2026-10-26); `vite` 8.3.8 (2026-11-11);
  `@sveltejs/vite-plugin-svelte` 7.3.1 (2026-09-23), con `peerDependencies` `vite ^8.0.0` y
  `svelte ^5.46.4`; `react` 19.3.1 (2026-10-14); `vue` 3.5.45 (2026-11-05).
- La comparación de R5 se hizo el 2026-10-29 con Vite 8.3.5 y Vue 3.5.44. Las versiones nuevas
  son de parche y no cambian el análisis.
