# P3-0015 · Enfoque de navegación: centrado en rutas, dibujadas como líneas de metro

**Contexto.** La función más valorada en E16 es «ver qué conceptos previos necesito» (83,1 %). PC6 ya devuelve la ruta elevada a tema, curso o área, con su evidencia. Las rutas reales son cortas (profundidad máxima 2) y solo 35 objetivos tienen una no vacía.
**Decisión.** La entrada es una meta («¿Qué quieres aprender?»). La pantalla principal es el camino hasta ella («Camino hasta la meta»): estaciones = conceptos ordenados por `depth`; líneas = temas, cursos o áreas del grano, que el estudiante cambia con «Ver por: tema · curso · área». Cada tramo tiene un «?» con la evidencia y su fuente (RF-21). El mismo camino se repite como lista ordenada («Indicaciones») en el panel lateral, que es la alternativa accesible al dibujo. Al tocar una estación se abre su ficha: «Qué necesitas antes» (PC1), «Dónde está en la carrera» (PC3), «Material de estudio» (PC5), «Es un tipo de y tipos» (PC7) y «Alrededor» (RF-19). Los códigos de trazabilidad solo se ven con el interruptor «Ver trazabilidad».
**Descartadas.**
- Lienzo de grafo libre como pantalla principal (P1): contesta «cómo se conecta», no «qué necesito antes», y con rutas de 2 pasos desperdicia el espacio.
- Catálogo de fichas (P2): la ruta queda a dos clics y pierde el orden visual.
- Línea de avance con progreso y marcas de completado: exige cuentas y progreso, fuera de alcance.
**Consecuencias.**
- Los casos vacíos son la mayoría (450 de 485 metas): cada uno tiene un mensaje propio (concepto, tema, unidad o área sin contenido de los sílabos, curso).
- La ruta de un curso no sale de PC6 sino de PC2 (ver P3-0018).
- Negativa: la exploración libre de vecinos queda en segundo plano, dentro de la ficha, y sin vecinos de segundo nivel.

**Fila para la Tabla 20.** Navegación centrada en rutas, con el grano como control · contesta la necesidad más valorada (E16, 83,1 %) con la ruta que R4 ya calcula (PC6).
