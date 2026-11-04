# P2-0018 · Procedencia como marca de fuente por fila, y la capa por forma, filete y texto

**Contexto.** RF-21 (firme) pide llegar desde cada afirmación institucional al documento del que sale, y RF-22 (firme), distinguir las capas de forma perceptible. En una ficha, cada fila es una arista (un «forma parte de», un «necesita antes», un «lo enseña»), y cada arista lleva su `provenance`.

**Decisión.** Cada fila lleva una **marca de fuente** con el código del documento (`↗ 1INF01`, `↗ CS2023`) que abre el sílabo (su `locator`) en una pestaña nueva, como una nota al pie de enciclopedia; su texto de ayuda dice «Ver fuente». Al final de la ficha, «Fuentes de esta ficha» lista los documentos citados, y la sección «Fuente», el del elemento (`WAS_DERIVED_FROM`). La capa se distingue por tres canales además del color: la **insignia textual** («CS2023 · estándar internacional (ACM/IEEE)» o «Sílabo PUCP · de un curso de la carrera»), la **forma** (cuadrado o círculo, en listas, migas y mapa) y el **filete** de la ficha y de su tarjeta (doble arriba para referencia, lateral para institucional).

**Descartadas.**
- Notas numeradas [1], [2]: más clásicas, pero la ruta de aprendizaje se carga aparte y tendría su propia numeración; el código dice además de qué sílabo sale sin ir al pie.
- Procedencia solo en un bloque al pie: cumple RF-21 para el nodo, pero no para cada arista mostrada.
- Distinguir capas solo por color: no cumple RF-22 para quien no distingue colores.

**Consecuencias.**
- Un estudiante ve de qué curso sale cada dato sin abrir nada: «Matemática Discreta ↗ 1INF01» dice que fue ese sílabo el que ubicó el tema en la unidad.
- Las filas de referencia (área ← unidad) citan a CS2023 con un marco punteado, distinto del institucional.
- Negativa: las marcas son pequeñas (12 px) y se repiten en cada fila. Una fila que resume varias aristas (un curso previo, con lo que enseña uno y asume el otro) lleva varias marcas, y en un móvil bajan a su propia línea.

**Fila para la Tabla 20.** Marca de fuente por fila y capa por insignia, forma y filete · cumple RF-21 en cada arista mostrada y RF-22 sin depender del color.
