# P3-0018 · Con un curso como destino, la ruta se apoya en PC2, no en PC6

**Contexto.** Con objetivo curso, `learning-path` sale vacía para los 4 cursos: los prerrequisitos de lo que enseña cada uno quedan dentro del mismo curso. El prerrequisito real entre cursos está en `/api/courses/prerequisites`: INF144 requiere conceptos que enseña 1INF01, y 1INF35 requiere conceptos que enseña INF238.
**Decisión.** Para un curso, la pestaña por omisión es «Cursos que conviene llevar antes» (PC2): estaciones = conceptos que el curso declara como requeridos («Lo que pide»), sobre la línea del curso que los enseña, con transbordo al curso meta. Un aviso fijo explica de dónde sale. La pestaña «Camino hasta la meta» (PC6) sigue disponible y explica por qué sale vacía.
**Descartadas.**
- Mostrar solo PC6: el estudiante vería «sin prerrequisitos» en INF144, que es falso según su sílabo.
- Presentar PC2 como si fuera PC6: mezcla dos derivaciones distintas (tesis, Paso 5) y confunde al validar.
- Pedir a R4 que PC6 use `REQUIRES_CONCEPT`: el diseño de las rutas ya lo descartó (cambia la derivación del Paso 5).
**Consecuencias.**
- Las dos derivaciones quedan visibles y nombradas por su patrón.
- Un curso sin conceptos requeridos (1INF01, INF238) se presenta como punto de partida.
- Negativa: el control de grano no aplica a esta vista, y la interfaz tiene que explicar por qué.

**Fila para la Tabla 20.** Ruta de un curso desde PC2, con aviso · PC6 de un curso sale vacía y el prerrequisito real entre cursos está en los conceptos requeridos.
