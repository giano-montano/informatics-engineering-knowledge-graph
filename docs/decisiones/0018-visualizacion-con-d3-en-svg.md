# ADR-018: Librería de visualización: D3 en SVG

**Estado:** Aceptada
**Fecha:** 2026-11
**Atributos:** ninguno de AC-01 a AC-05. Lo motivan RF-19 y RF-22.

## Contexto

El lienzo dibuja lo que devuelven las rutas, no el grafo entero. Medido sobre los datos de
desarrollo: `/api/nodes` trae a lo sumo 84 nodos; la ubicación del área de Redes y Comunicación,
158, y los cursos previos de Redes de Computadoras, 142. Cada lente pide una disposición distinta
(columnas por profundidad, árbol, dos alas alrededor del foco), y RF-22 pide forma por capa:
hexágono y círculo.

La tesis deja la librería «a definir según evaluación técnica» en la Tabla 5, en la fila de R6, y
§1.3.1.5 nombra entre los criterios la escalabilidad de nodos y la interacción de tipo
*drill-down*.

## Decisión

- **D3 7.9.2, en un solo paquete**, que incluye d3-force 3.0.1, d3-hierarchy y d3-zoom, dibujando
  en SVG. En R6 se importa desde npm y lo empaqueta Vite.
- **Una sola simulación de fuerzas.** Cada lente le fija posiciones objetivo, calculadas a mano,
  hacia las que los nodos se animan. Las etiquetas se colocan sobre esas posiciones, evitando
  encimarse.
- **Cada nodo es un botón en el DOM,** con texto accesible (clase, nombre y capa) y foco de
  teclado.
- **El *drill-down* es el cambio de foco y la expansión con +**, y lo que no cabe se resume
  (ADR-016).

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Cytoscape.js 3.35.0 | Trae el modelo de grafo y las disposiciones listos, pero dibuja en canvas con estilos propios: las formas por capa y el brillo cuestan más que en SVG, y los nodos no quedan en el DOM. Es la segunda opción si D3 resultara lento de programar. |
| Sigma.js 4.0.6 con graphology 0.26.0 | Dibuja con WebGL, para miles de nodos, que aquí no hay. Las formas propias por capa exigen programas de WebGL, y el control del texto es menor. |
| vis-network 10.1.5 | Rápido de montar, pero centrado en su física: las disposiciones por lente y la estética quedan muy restringidas. |

## Consecuencias

- Control total de forma, color, texto y transición: RF-22 y la estética se cumplen sin pelear con
  la librería.
- El SVG queda en el DOM, así que el lienzo se puede recorrer con teclado y leer con un lector de
  pantalla. No se ha comprobado con uno real.
- Negativa: es más código propio. En la maqueta, unas 420 líneas de disposiciones y 1100 del
  lienzo en total.
- Negativa: pasados unos 1000 nodos en pantalla, el SVG se pone lento. Hoy está lejos, por las
  cotas de la API; si R4 las quita, habría que pasar a canvas.

## Fuentes

- Registro de npm (`registry.npmjs.org`), consultado el 2026-11-15 (oficial). Última versión
  estable y su fecha de publicación: `d3` 7.9.2 (2026-11-03), `d3-force` 3.0.1 (2026-11-03),
  `cytoscape` 3.35.0 (2026-11-10), `sigma` 4.0.6 (2026-11-10), `graphology` 0.26.0 (2025-01-26)
  y `vis-network` 10.1.5 (2026-11-08).
- Notas de versión de D3 en GitHub, consultadas el 2026-11-15 (oficial del proyecto): la 7.9.1
  (2026-11-03) actualiza dependencias y publica un módulo ES empaquetado en vez de archivos
  sueltos; la 7.9.2, del mismo día, revierte un arreglo de d3-delaunay. El paquete conserva
  `dist/d3.min.js`. <https://github.com/d3/d3/releases>
- La maqueta de R5 carga D3 7.9.0 desde jsDelivr: era la última estable el 2026-10-29.
- Tamaño de las respuestas: medición propia sobre los datos capturados el 2026-10-29
  (`docs/r5/datos/`).
