# P3-0016 · Framework de R6: Vue 3 con Vite

**Contexto.** R6 es una SPA que solo presenta: la lógica de navegación vive en R4. La vista tiene poco estado (destino, grano, pestaña, estación en foco, ficha, diálogo) y un único dibujo a medida. Hay que reunir en la misma app la navegación y el panel del operador.
**Decisión.** Vue 3 (**3.5.44**) con componentes de un solo archivo, compilados con Vite (**8.3.5**, `@vitejs/plugin-vue` **6.0.10**) y enrutado con `vue-router` (**5.4.0**). Versiones verificadas el 2026-10-29 en `registry.npmjs.org` (3.5.44 se publicó el 2026-10-13). La maqueta usa la variante sin compilación (`vue.global.prod.js` desde jsDelivr), con la misma API de opciones, así que su código se traslada a componentes casi sin cambios.
**Descartadas.**
- React 19 (19.3.1): sin variante sin compilación cómoda para la maqueta (JSX); más piezas que elegir (enrutador, estado) para una app de este tamaño.
- Svelte 5 (5.57.3): exige compilador incluso para prototipar; ecosistema más chico.
- JS sin framework: viable en la maqueta, pero el estado de la ficha, las pestañas y el panel del operador acaba en un mini framework propio.
- Angular: demasiado para una SPA de presentación.
**Consecuencias.**
- La maqueta ya es el primer borrador de los componentes (ver el C4 del README).
- La ruta actual se refleja en la URL (`#destino=…&grano=…`): con `vue-router` pasa a ser una ruta real, compartible.
- Negativa: Vite trae un paso de compilación y una cadena de Node al despliegue (la imagen de nginx sirve el compilado).

**Fila para la Tabla 20.** Vue 3.5 + Vite para R6 · SPA de presentación con poco estado; la maqueta sin compilación ya usa la misma API.
