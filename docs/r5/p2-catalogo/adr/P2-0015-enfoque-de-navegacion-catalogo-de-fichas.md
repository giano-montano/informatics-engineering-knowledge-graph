# P2-0015 · Enfoque de navegación: catálogo de fichas con mini mapa secundario

**Contexto.** RF-19 y RF-20 piden un punto de entrada y, para el elemento en foco, sus prerrequisitos, su ubicación y sus recursos. En E16, el 72,1 % quiere encontrar recursos de un concepto y el 83,1 %, saber qué necesita antes. Casi ningún nodo tiene `description` (1 de 491).

**Decisión.** Cada elemento tiene una **ficha** con URL propia (`/ficha?key=`), con migas de ubicación y secciones por clase. Cada sección sale de una ruta de R4 (PC1 a PC7) y resuelve un caso de uso del catálogo común (`../../casos-de-uso.md`). Se entra desde una portada con las 17 áreas y los cursos, o desde el buscador. El grafo aparece solo como un **mini mapa** del vecindario (`/api/nodes`) en el lateral, que se puede agrandar. La ficha se arma con lo que sí existe: ubicación, conteos, relaciones y procedencia, y una frase de entrada armada con ellos. Los códigos de trazabilidad (CU, PC, RF) solo se ven al encender «Ver trazabilidad».

**Descartadas.**
- Lienzo del grafo como protagonista (P1): responde «cómo se conecta», pero para leer recursos y prerrequisitos hay que pasar por un panel lateral, y con 25 vecinos el lienzo se satura.
- Ruta de aprendizaje como pantalla principal (P3): responde «qué necesito antes», pero 35 de los 485 objetivos tienen ruta no vacía; en el resto, la pantalla principal saldría vacía.
- Ficha sin mapa: cumple RF-20, pero deja corto el «visual e interactiva» de RF-19.

**Consecuencias.**
- Atrás y adelante del navegador funcionan, y cada ficha se puede enlazar o citar.
- Las listas largas (KA-NC: 158 nodos) se pliegan; la ficha de un área es pesada, pero se lee.
- Negativa: lo que mejor responde esta propuesta es «qué hay sobre esto», no «cómo se conecta con lo demás». El mapa es secundario, así que la exploración visual de RF-19 recae en una vista acotada al vecindario; la expansión a pedido (CU-2) solo está en el mapa agrandado.

**Fila para la Tabla 20.** Enfoque de navegación por fichas, con mini mapa secundario · responde la necesidad más votada de recursos y prerrequisitos (E16) y no depende de descripciones que el grafo no tiene.
