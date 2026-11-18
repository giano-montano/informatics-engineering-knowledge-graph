# ADR-016: Enfoque de navegación: lienzo del grafo con un foco, lentes y panel lateral

**Estado:** Aceptada
**Fecha:** 2026-11
**Atributos:** AN-01 (principal), AN-02

## Contexto

El mecanismo de navegación tiene que permitir explorar el grafo de vecino en vecino y mostrar,
para el elemento en foco, sus prerrequisitos, su ubicación y sus recursos (AN-01, definido en
`docs/r5/atributos-de-calidad.md`). Los once casos de uso de
`docs/r5/casos-de-uso.md`, diez del estudiante y uno del operador, son comunes a las tres
propuestas que se evaluaron en la Fase 1 de R5. En la pregunta E16 de la encuesta, el 83,1 %
quiere ver qué conceptos previos necesita; el 72,1 %, encontrar recursos de estudio; el 61 %,
entender cómo se conectan las áreas, y el 52,6 %, descubrir temas que no conocía.

Se construyeron tres maquetas sobre los mismos datos reales, la API de R4 con el backbone y los
4 sílabos de desarrollo, capturada el 2026-10-29, y con el mismo recorrido de seis pasos, para
compararlas sobre la misma historia. Están en `docs/r5/`. El autor eligió P1, y el asesor dio su
visto bueno preliminar.

## Decisión

- **El lienzo ocupa el centro, y siempre hay un elemento en foco.** Su vecindario
  (`/api/nodes`) se dibuja en dos alas, a sus lados. Un clic en un vecino lo vuelve el foco, y
  **+** agrega las conexiones de un vecino sin perder lo anterior.
- **Ocho lentes reordenan el mismo lienzo** con la respuesta de una ruta de R4 y dibujan solo lo
  que la responde: Lo que lo rodea, Qué necesitas antes, Camino hasta aquí, Cursos que conviene
  llevar antes, Dónde está en la carrera, Qué contiene, Material de estudio y Tipos.
- **Una cabecera sobre el lienzo** nombra el foco, ofrece solo las lentes que aplican a su clase
  y responde la elegida en una frase, con otra que dice cómo leer el dibujo. La interfaz no
  muestra códigos de casos de uso ni de requisitos.
- **Un panel lateral lee el foco como ficha:** fuente, ubicación, contenido y orden,
  prerrequisitos, cursos, tipos, material y conexiones. Un rastro de focos permite volver.
- **Lo que no cabe con nombre legible se resume**, con un conteo o un recuadro de puntos sin
  nombre, y el detalle queda a un clic. Los umbrales de la maqueta (24 conceptos en un árbol, 14
  vecinos por grupo, 4 unidades sin temas) salen de los 4 sílabos de desarrollo y se revisan con
  los 13.

Cómo resuelve esta interfaz cada caso de uso, con sus pantallas, está en
`docs/r5/p1-lienzo/README.md`, §2 y §3.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| **P2 · Catálogo de fichas**, con URL propia y el grafo como mini mapa secundario (`docs/r5/p2-catalogo/`) | Era la más barata de construir y la más accesible, y responde mejor la necesidad de encontrar recursos. Pero deja el grafo en segundo plano: la exploración visual del grafo recae en un mapa acotado a 25 vecinos, y la expansión a pedido (CU-2) solo existe en el mapa agrandado. Responde «qué hay sobre esto», no «cómo se conecta con lo demás». |
| **P3 · Itinerario**: la meta como entrada y el camino hasta ella como mapa de metro (`docs/r5/p3-rutas/`) | Responde en una pantalla la necesidad más votada (83,1 %). Pero su pantalla principal depende de que haya rutas, y con los datos de desarrollo solo 35 de 485 metas tienen una, de profundidad 2 como máximo; en las demás sale vacía. La exploración libre de vecinos queda dentro de una ficha, sin vecinos de segundo nivel. |
| Lienzo sin foco, con todo el grafo de una vez | Con 491 nodos no se lee nada, y la API está acotada a propósito: 25 vecinos directos y 5 de segundo nivel por cada uno. |
| Una pantalla por caso de uso | Rompe la continuidad entre preguntas sobre el mismo elemento, que es lo que contesta «¿cómo se conecta esto?». |
| Panel flotante sobre el nodo, en vez de lateral | Tapa justo lo que se quiere ver y no admite listas largas. |

## Consecuencias

- Los diez casos de uso del estudiante se resuelven sobre el mismo lienzo, sin pantallas nuevas,
  y todos con rutas que R4 ya tiene, salvo el inicio sin buscar.
- El panel es también la alternativa en texto al lienzo (ADR-018).
- R4 suma una ruta, `GET /api/overview`, para el inicio: las áreas con sus conteos y los cursos.
  Su forma se decide al agregarla a R4.
- Negativa: es la propuesta que más le exige al estudiante, porque tiene que leer un grafo, y la
  más cara de construir: una disposición por lente, colocación de etiquetas, expansión
  incremental y una alternativa accesible. Para encontrar material de estudio (CU-7) es más lenta
  que un catálogo.
- Se declaran como limitaciones la escala y la accesibilidad. Un área con decenas de temas alarga
  el árbol, y «Qué necesitas antes» y «Camino hasta aquí» no tienen regla de resumen, porque las
  rutas de hoy no pasan de 2 pasos. La accesibilidad no se ha comprobado con un lector de
  pantalla real.

## Fuentes

- Encuesta de orientación del aprendizaje, pregunta E16 (Anexo D de la tesis; medición propia).
- Maquetas P1, P2 y P3, su comparación y sus conteos: `docs/r5/README.md` y el README de cada
  propuesta (medición propia sobre los datos capturados el 2026-10-29).
- Cotas de la respuesta de `/api/nodes`: `docs/diseño-de-las-rutas-de-navegación.md`.
