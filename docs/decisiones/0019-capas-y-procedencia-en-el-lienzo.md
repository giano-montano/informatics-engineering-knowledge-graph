# ADR-019: Capas y procedencia en el lienzo

**Estado:** Aceptada
**Fecha:** 2026-11
**Atributos:** AC-03 (principal)

## Contexto

RF-22 pide distinguir la capa de referencia (CS2023) de la institucional (los sílabos) de forma
perceptible, y no solo por color. RF-21 pide llegar al documento del que procede cada afirmación
institucional (CU-10). Los dos derivan de AC-03, y la Tabla 23 de la tesis cierra AC-03 en R6 con
una prueba de aceptación que abre ese documento.

Toda respuesta de la API trae aristas `WAS_DERIVED_FROM`. Dibujarlas todas haría de cada sílabo un
erizo que tapa el resto.

## Decisión

- **Capa por forma.** Hexágono con doble contorno y relleno translúcido para CS2023; círculo
  relleno para los sílabos. Se repite con ícono y texto en el panel («CS2023», «Sílabo PUCP»), en
  la leyenda y en el texto accesible de cada nodo. El color queda para la clase: área, tema,
  concepto…
- **Fuente sin aristas dibujadas.** `WAS_DERIVED_FROM` no se dibuja por omisión. El panel muestra
  la fuente del foco con su enlace, y cada relación, la suya. Al pasar el cursor sobre una arista
  se ve su fuente; un clic o un toque la fija en el panel, con el enlace al documento. El
  interruptor «Fuentes» dibuja esas aristas, con los documentos en una fila aparte.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Capa solo por color | No cumple RF-22 y falla con daltonismo. |
| Dos lienzos o dos bandas, uno por capa | Parten lo que interesa ver junto: un tema de un sílabo dentro de su unidad de CS2023. |
| Fuentes siempre dibujadas | El sílabo concentra decenas de aristas y oculta la estructura. |

## Consecuencias

- RF-21 y RF-22 se ven en todas las pantallas, sin depender de una lente.
- El documento de un sílabo se abre en `/resources/{clave}`, la dirección que guarda su
  localizador (ADR-009). El de CS2023 abre la publicación de ACM.
- Negativa: la fuente de una arista pide pasar el cursor, hacer clic o tocarla. En pantalla
  táctil depende del toque, con un área de 24 px, y de la lista «Conexiones» del panel.
