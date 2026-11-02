# P3-0017 · Visualización: D3.js con una disposición por capas propia

**Contexto.** El dibujo es un mapa de metro: columnas por distancia al destino, líneas gruesas paralelas, transbordos, tramos a 45°. La API ya entrega la capa de cada estación (`depth`); las rutas tienen a lo sumo 3 columnas y unos 7 conceptos, y el orden interno de un área (PC4) llega a 26.
**Decisión.** D3.js **7.9.0** (selección, transiciones y `d3-zoom`), verificada el 2026-10-29 en `registry.npmjs.org` (última versión estable, del 2024-03-12) y servida por jsDelivr. La disposición es propia y corta (`disponer()` en `modelo.js`): columna = `maxDepth − depth`, filas por baricentro de las estaciones previas. Solo en PC4, donde la API no da `depth`, la columna sale del camino más largo, que es cuenta gráfica, no navegación.
**Descartadas.**
- dagre (`@dagrejs/dagre` 3.1.3): recalcula los rangos y podría contradecir el `depth` de la API; sus aristas no son octilineales.
- elkjs (0.12.1): el mejor ruteo ortogonal, pero `elk.bundled.js` pesa 1,6 MB sin comprimir (medido en jsDelivr el 2026-10-29; D3 entero pesa 0,28 MB) y es asíncrono, para grafos de 7 nodos. Queda como plan B si las rutas crecen.
- Cytoscape.js (3.34.4): pensado para grafos libres; dibujar líneas paralelas y transbordos obliga a pelear con su modelo de estilos.
**Consecuencias.**
- El dibujo y su leyenda distinguen la capa por forma (círculo frente a cuadrado, línea llena frente a vía doble) y por texto, no solo por color (RF-22).
- La disposición es nuestra: hay que mantenerla y probarla (hoy se prueba en node con las 105 rutas no vacías y los 22 órdenes internos).
- Negativa: con rutas mucho más largas (más sílabos, cota mayor), el baricentro de una pasada puede cruzar tramos; ahí convendría elkjs.

**Fila para la Tabla 20.** D3.js 7.9 con disposición por capas propia · la API ya da la capa (`depth`) y el mapa de metro necesita un dibujo a medida.
