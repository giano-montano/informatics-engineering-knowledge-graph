# Atributos de calidad del mecanismo de navegación

Resultado R5. Los atributos AC-01 a AC-05 son del módulo del grafo (R3) y no alcanzan para motivar
las decisiones de la interfaz. Estos dos los completan, y son los que citan ADR-016 a ADR-018;
ADR-019 cita AC-03. En la tesis van en el capítulo de O3, junto a la tabla de esos ADR.

Vocabulario: ISO/IEC 25010:2023, característica «capacidad de interacción».

| ID | Propiedad | Origen | Prioridad | Cómo se comprueba |
|---|---|---|---|---|
| AN-01 | El estudiante responde sus preguntas sobre un elemento del grafo desde un mismo lugar, sin conocer el lenguaje de consulta y sin perder de vista el elemento | Necesidades de la encuesta de orientación del aprendizaje (Anexo D de la tesis): ver los conceptos previos, encontrar recursos y entender cómo se conectan las áreas | Alta | Casos CA-01 a CA-10 del plan de pruebas de aceptación de R6 |
| AN-02 | Lo que la interfaz muestra no depende de un solo canal: ni solo del color, ni solo del dibujo, ni solo del cursor | La capa de cada elemento y la fuente de cada afirmación tienen que poder leerse siempre (AC-03), por cualquier estudiante de la carrera | Media | La capa se distingue por forma y texto, y todo lo dibujado está también como lista en el panel (criterios de CA-01, CA-02 y CA-05) |

Cuando chocan, el dibujo puede resumir (AN-01), pero lo resumido queda completo en el panel
(AN-02).

**Correspondencia con ISO/IEC 25010:2023.** AN-01 corresponde a operabilidad y capacidad de
aprendizaje; AN-02, a inclusividad. La edición de 2023 renombra «usabilidad» como «capacidad de
interacción» y reparte la accesibilidad entre inclusividad y asistencia al usuario. Verificado el
2026-11-15 en fuentes secundarias (gris: arc42 y Sonar, que citan la norma). Antes de citarlo en
la tesis, comprobar los términos contra la norma, que ya está en sus referencias.
