# P1-0018 · Capas y fuentes en el lienzo (RF-21, RF-22)

**Contexto.** RF-22 (firme) pide distinguir la capa de referencia (CS2023) de la institucional (sílabos) de forma perceptible, y no solo por color. RF-21 (firme) pide llegar al documento de cada afirmación institucional (CU-10). Toda respuesta trae aristas `WAS_DERIVED_FROM`, y dibujarlas todas haría de cada sílabo un erizo que tapa el resto.

**Decisión.**
- **Capa por forma:** hexágono con doble contorno y relleno translúcido para CS2023; círculo relleno con brillo para los sílabos. Se repite en el panel con ícono y texto («CS2023», «Sílabo PUCP») y en la leyenda, que aclara qué es CS2023: el estándar internacional del currículo de computación (ACM/IEEE). El color queda para la clase (área, tema, concepto…).
- **Fuente sin aristas:** `WAS_DERIVED_FROM` no se dibuja por omisión. El panel muestra la fuente del foco con su enlace («Ver fuente»), y cada prerrequisito, la de su arista. Al pasar el cursor sobre una arista se ve su fuente; un clic la fija en el panel con el enlace. El interruptor «Mostrar fuentes» dibuja esas aristas.

**Descartadas.**
- Capa solo por color: no cumple RF-22, y falla con daltonismo.
- Dos lienzos o dos bandas, uno por capa: parten lo que interesa ver junto, un tema de un sílabo dentro de su unidad de CS2023.
- Fuentes siempre dibujadas: el sílabo concentra decenas de aristas y oculta la estructura.

**Consecuencias.**
- RF-21 y RF-22 quedan visibles en todas las pantallas sin depender de una lente.
- Negativa: la fuente de una arista pide pasar el cursor o hacer clic. En pantallas táctiles depende del clic y de la lista «Conexiones» del panel (botón «Ver fuente»).

**Fila para la Tabla 20.** Forma por capa y fuente en el panel y bajo demanda · cumple RF-21 y RF-22 sin saturar el lienzo con `WAS_DERIVED_FROM`.
