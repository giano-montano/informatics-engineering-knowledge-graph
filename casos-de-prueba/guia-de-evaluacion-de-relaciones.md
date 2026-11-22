# Guía de evaluación de relaciones (CP-15 y CP-16)

## Propósito

Fija cómo se juzgan a mano las relaciones del grafo final en CP-15 y CP-16
(tesis, §5.2.5.6): qué aristas se juzgan, con qué criterio cada una cae en
correcta, aceptable o incorrecta, y qué se registra por cada juicio. Así el
juicio se puede repetir y revisar.

Esta guía se escribe y se versiona antes del primer juicio.

## Qué se juzga

- **El grafo** es el de la medición final de R4: las 13 corridas de
  `var/medicion-r4/operational.sqlite` del 2026-11-16, con el código del tag
  `codigo-congelado-2026-11-16`. No se juzga sobre otro grafo.
- **La planilla** es `relaciones/juicio-de-relaciones-semilla-20261116.xlsx`.
  `relaciones/build_sheets.py` la armó desde ese grafo el 2026-11-16, y
  `relaciones/add_cs2023_topics.py` agregó a la hoja CP-15 los tópicos de cada
  unidad, copiados del documento CS2023 (Kumar et al., 2024). El grafo solo
  tiene el nombre de cada unidad. Para juzgar no hace falta Neo4j.
- **La muestra de CP-16:** las aristas de cada tipo, ordenadas por la clave de
  sus extremos y numeradas desde 0; se eligen los índices con
  `random.Random(20261116).sample(range(N), 30)`, o todas si N ≤ 30. La hoja
  «Muestra» lista los índices. La semilla es la fecha de la corrida final y se
  fijó al armar la planilla, antes de abrirla para juzgar.

| Caso | Arista | En el grafo | Se juzgan |
|---|---|---|---|
| CP-15 | `(Tema)-[:PART_OF]->(Unidad)` | 78 | 78 |
| CP-16 | `(A)-[:HAS_PREREQUISITE]->(B)` | 499 | 30 |
| CP-16 | `(A)-[:SPECIALIZES]->(B)` | 94 | 30 |
| CP-16 | `(Curso)-[:REQUIRES_CONCEPT]->(X)` | 38 | 30 |

Fuentes abiertas al lado: los sílabos de `silabos-en-orden/` y, si hace falta
más contexto de una unidad, el documento CS2023.

## Criterios (tesis, §5.2.5.6)

- **CP-15.** La arista es correcta si la descripción o los tópicos de la
  unidad cubren el contenido del tema; aceptable, si otra unidad lo cubre mejor
  pero la asignada lo cubre en parte; e incorrecta, en otro caso.
- **CP-16, prerrequisito.** Correcta si comprender el concepto de origen exige
  conocer el de destino.
- **CP-16, especialización.** Correcta si el concepto de origen es un tipo del
  de destino.
- **CP-16, concepto requerido.** Correcta si el curso necesita ese concepto
  como entrada y no lo enseña.

En CP-16 no hay «aceptable»: lo que no es correcta es incorrecta.

## Reglas para los casos dudosos

### CP-15

1. **El contenido del tema es su nombre más sus conceptos.** Si el nombre es
   genérico o administrativo («SISTEMAS OPERATIVOS», «PRESENTACIÓN DEL
   CURSO…»), se juzga por los conceptos y se anota en observaciones.
2. **Tema mixto:** correcta si la unidad cubre el saber principal del tema, el
   que agrupa la mayoría de sus conceptos; aceptable si solo cubre uno
   secundario.
3. **Tópicos de la unidad:** cuentan todos los de la columna, sean CS Core,
   KA Core o Non-core.
4. **Antes de cerrar como correcta, mirar las vecinas.** Si otra unidad lo
   cubre claramente mejor y la asignada solo en parte, es aceptable.
5. **Aceptable no es «no estoy seguro».** Una duda entre correcta e incorrecta
   se resuelve con estas reglas y se anota en observaciones.

### CP-16

1. **La flecha va del origen al destino.** `A → B` se lee «A tiene como
   prerrequisito a B» o «A es un tipo de B». Si la relación vale al revés, es
   incorrecta, con el motivo «dirección invertida».
2. **Prerrequisito:** ¿se puede entender A sin conocer B? Se juzga la
   dependencia conceptual, no el orden del sílabo: que B se enseñe antes no
   basta.
3. **Especialización:** vale la prueba literal «todo A es un B». «Es parte
   de» o «usa la técnica» son incorrectas: por ejemplo, Quicksort → Divide y
   vencerás.
4. **Concepto requerido**, en este orden:
   - Si la columna «el curso también lo enseña» dice «sí», es incorrecta, con
     el motivo «el curso lo enseña».
   - Si dice «no», se abre el sílabo. Si lo enseña con otras palabras, es
     incorrecta, con el motivo «enseñado con otras palabras».
   - Si no lo enseña, es correcta si el sílabo lo usa como entrada (en la
     sumilla, en los requisitos o en los capítulos), aunque el concepto sea
     genérico («Programación»). Si no aparece, es incorrecta, con el motivo
     «no lo necesita».
   - La columna «lo enseñan» es contexto, no criterio. Una arista puede ser
     correcta aunque ningún curso del grafo enseñe el concepto.

## Qué se registra

| Columna | Qué va | Cuándo |
|---|---|---|
| `juicio` | correcta, aceptable (solo en CP-15) o incorrecta | Siempre |
| `motivo` | Una frase | Siempre en las incorrectas; recomendable en las aceptables |
| `unidad_mejor` (CP-15) | La unidad que lo cubre mejor, p. ej. `KU-SE-Validation` | En las aceptables, y en las incorrectas si existe |
| `topico_cs2023` (CP-15) | El número y el texto del tópico que lo cubre | En las correctas y las aceptables |

## Reporte

- Un reporte por caso, con la forma de `formato-de-reporte-de-prueba.md`. En
  CP-16 va un resumen por tipo, no uno mezclado.
- En la cabecera van la fecha, el evaluador, el grafo (la medición del
  2026-11-16) y el commit de esta guía.
- Las observaciones recogen los patrones de los errores, no la lista de
  errores.
- Son medidas descriptivas, sin umbral: no cambian el indicador de R4.
- La planilla llena y los reportes van a `relaciones/`, con su commit.
