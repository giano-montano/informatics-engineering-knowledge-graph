# P2-0017 · Librería del mini mapa: D3.js (d3-force sobre SVG)

**Contexto.** En P2 el grafo es secundario: un recuadro con el vecindario de `/api/nodes` (como mucho, 1 + 25 + 25×5 nodos), que se agranda en un diálogo con zoom. La librería tiene que dibujar formas distintas por capa (RF-22), dejar navegar con teclado y no imponer su propio estilo.

**Decisión.** **D3.js 7.9.0** (la vigente; verificada el 2026-10-29 en `registry.npmjs.org/d3`: sin versión nueva desde el 2024-03-12). Se usan `d3-force`, `d3-selection` y `d3-zoom`. La simulación se corre de antemano (300 pasos, foco fijo en el centro) y se dibuja estática en SVG: es determinista, no se mueve y no consume CPU mientras se lee la ficha. En R6 se importan solo esos módulos.

**Descartadas.**
- Cytoscape.js 3.34.4: muy completa (diseños, estilos, selección), pero dibuja en canvas, así que cada nodo no es un elemento accesible con foco de teclado, y trae mucho más de lo que pide un mapa de 25 vecinos.
- Sigma.js 4.0.4 (con graphology 0.26.0): WebGL pensado para miles de nodos; aquí sobra, y su estilo de nodos es más rígido para mostrar cuadrado frente a círculo.
- vis-network: también dibuja en canvas, y su estilo propio cuesta llevarlo a la estética editorial (no se evaluó más a fondo).
- SVG a mano sin librería: posible, pero habría que reescribir el diseño de fuerzas y el zoom.

**Consecuencias.**
- Cada nodo es un `<g>` con `role="link"`, `aria-label` y `<title>`; en el mapa agrandado se recorre con Tab y Enter abre la ficha.
- La forma lleva la capa: cuadrado para CS2023, círculo para sílabo, rombo para documento. El color solo refuerza.
- Negativa: D3 es de bajo nivel. Cada interacción nueva (resaltar un camino, expandir con `more_neighbors`) es código propio que se escribe y se prueba.

**Fila para la Tabla 20.** D3.js 7.9.0 (d3-force, SVG) para el mini mapa · SVG accesible, formas libres por capa y peso proporcional a un vecindario de a lo sumo 25 vecinos.
