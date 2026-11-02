# P1-0016 · Framework de R6: Svelte 5 con Vite, como SPA estática

**Contexto.** R6 es una SPA servida por nginx (ADR-007) que solo presenta: la lógica de navegación vive en R4. El estado que se maneja es pequeño pero compartido entre lienzo, panel, lentes y rastro (foco, lente, grano, expansiones). El lienzo es de D3, que necesita controlar su propio SVG.

**Decisión.** Svelte **5.57.3** con Vite **8.3.5** y `@sveltejs/vite-plugin-svelte` **7.3.1**, sin SvelteKit: compilado estático, sin servidor de Node (versiones verificadas el 2026-10-29 en registry.npmjs.org). El lienzo es un componente que le entrega a D3 un nodo del DOM (con `$effect`), y Svelte no lo toca. La maqueta usa JS sin framework: demuestra que el diseño no depende de él.

**Descartadas.**
- React 19.3.1: su DOM virtual compite con D3 por el mismo SVG, y hay que aislarlo con `ref`. Además pesa más en tiempo de ejecución.
- Vue 3.5.44: viable y cercano (empate técnico). Se prefiere Svelte por la menor carga en tiempo de ejecución y por su reactividad sin envoltorios (*proxies*) sobre los objetos que D3 muta.
- JS sin framework, como la maqueta: alcanza para la maqueta. En R6, con el panel del operador y las rutas de URL, el estado repartido a mano se vuelve frágil.

**Consecuencias.**
- La salida es un paquete estático chico, que nginx sirve tal cual.
- Los componentes de la tabla del README pasan casi uno a uno a componentes `.svelte`.
- Negativa: hay paso de compilación (Node en la máquina de desarrollo), y Svelte 5 (*runes*) tiene menos material de consulta que React.

**Fila para la Tabla 20.** Svelte 5 + Vite, SPA estática · runtime chico y convive sin fricción con el SVG que controla D3.
