# P1-0017 · Librería de visualización: D3 (d3-force, d3-hierarchy, d3-zoom) en SVG

**Contexto.** El lienzo dibuja lo que devuelven las rutas, no el grafo entero. Medido sobre los datos capturados: `/api/nodes` trae a lo sumo 84 nodos; la ubicación de KA-NC, 158; los cursos previos de INF238, 142. Cada lente pide una disposición distinta (columnas por profundidad, árbol, dos alas alrededor del foco) y RF-22 pide forma por capa (hexágono y círculo).

**Decisión.** D3 **7.9.0** en un solo paquete (incluye d3-force 3.0.0), dibujando en SVG: verificado el 2026-10-29 en registry.npmjs.org, y servido desde jsDelivr. Una sola simulación de fuerzas, y cada lente le fija posiciones objetivo, calculadas a mano, hacia las que los nodos se animan; las etiquetas se colocan sobre esas posiciones, evitando encimarse. El brillo neón de los nodos sale de un filtro SVG y el de las flechas, de `drop-shadow` de CSS, porque un filtro SVG no pinta un trazo exactamente horizontal.

**Descartadas.**
- Cytoscape.js 3.34.4: modelo de grafo y disposiciones listos, pero dibuja en canvas con estilos propios. El neón y la doble línea del hexágono cuestan más que en SVG. Es la segunda opción, si D3 resultara lento de programar.
- Sigma.js 4.0.4 con graphology 0.26.0: WebGL, para miles de nodos, que aquí no hay. Formas propias por capa exigen programas de WebGL, y el control del texto es menor.
- vis-network 10.1.4: rápido de montar, pero centrado en su física; las disposiciones por lente y la estética quedan muy restringidas.

**Consecuencias.**
- Control total de forma, color, texto y transición: RF-22 y la estética se cumplen sin pelear con la librería.
- El SVG queda en el DOM: cada nodo es un botón con `aria-label` y foco de teclado.
- Negativa: es más código propio: en la maqueta, unas 420 líneas de disposiciones y 1100 del lienzo en total. Pasados unos 1000 nodos en pantalla, el SVG se pone lento. Hoy está lejos por las cotas de la API, pero, si R4 las quita, habría que pasar a canvas.

**Fila para la Tabla 20.** D3 7.9.0 en SVG · las respuestas de la API son de decenas a ~160 nodos; SVG da formas por capa, accesibilidad y una disposición por lente.
