# P2-0016 · Framework de R6: Vue 3 con Vue Router, compilado con Vite

**Contexto.** R6 es una SPA, servida por nginx (`kms.web`), que solo presenta lo que calcula R4. El catálogo se organiza en páginas con URL propia (portada, búsqueda, ficha); el panel del operador es común a las tres propuestas. La maqueta tenía que abrirse sin compilar.

**Decisión.** **Vue 3.5.44** con **Vue Router 5.4.0**, en componentes `.vue` compilados con **Vite** (rama 8; la vigente es 8.3.5, publicada el 2026-10-21; se fija la versión exacta al crear el proyecto). En R6, `createWebHistory` con `try_files $uri /index.html` en nginx. La maqueta usa los *builds* globales de los mismos paquetes, sin compilación y con `createWebHashHistory` para que funcione en `file://`. Versiones verificadas el 2026-10-29 en el registro de npm (`registry.npmjs.org`, campo `dist-tags.latest` y su fecha) y en jsDelivr (archivos `dist/*.global.prod.js`).

**Descartadas.**
- SvelteKit 3.1.0: enrutado por archivos muy cómodo, pero no tiene variante sin compilación con la que hacer la maqueta, y su modo SPA estática (`adapter-static`) es un caso secundario de un framework pensado para servidor.
- Nuxt 4.6.3 / Astro 7.4.4: orientados a renderizar en servidor o a sitios estáticos; aquí todo dato llega en vivo desde la API y no hay contenido que pre-renderizar.
- React 19.3.1 con React Router 8.5.1: equivalente en capacidad, pero sin plantillas HTML legibles sin JSX; obliga a compilar desde el primer día.
- JavaScript sin framework: alcanza para la maqueta, pero en R6 obliga a escribir a mano el enrutado, la reactividad y el estado de la ficha.

**Consecuencias.**
- Las plantillas de la maqueta pasan casi tal cual a archivos `.vue`: la maqueta ya es un esbozo del código de R6.
- `api(ruta, params)` es la única puerta a R4: en R6 cambia su cuerpo por `fetch`, y nada más se toca.
- Negativa: Vue Router 5 es reciente (la rama 5 salió el 2026-01-29). Hay menos ejemplos de ella que de la 4, aunque `createRouter` y los modos de historial no cambiaron.

**Fila para la Tabla 20.** Vue 3 + Vue Router (SPA compilada con Vite) · enrutado por páginas con URL por ficha, plantillas legibles y una maqueta sin compilación con el mismo código.
