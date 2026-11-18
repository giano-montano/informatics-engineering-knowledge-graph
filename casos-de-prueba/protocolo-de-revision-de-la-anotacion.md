# Protocolo del contraste de la anotación con extracciones humanas independientes

## Propósito

La anotación de referencia la produjo un modelo de lenguaje siguiendo la guía
v2.1 (tesis, §5.2.5.2). Este protocolo la compara con la extracción de
personas que trabajan **sin la guía y sin ver la anotación**, de modo que el
juicio humano no quede anclado al del modelo.

Se escribe antes de recibir la extracción, para que ninguna regla se decida
después de ver los resultados.

Hasta el 2026-11-15 se llamó «revisión independiente», y a las personas,
«revisores»: de ahí los nombres de archivos, carpetas y columnas, que se
conservan. Es un documento interno del repositorio, no un entregable. La tesis resume en
§5.2.5.2 lo que cambia la lectura de los números; el detalle está aquí.

## Alcance

- **Sílabos:** 1INF37 (CP-11, 89 entradas) y 1INF27 (CP-02, 39 entradas).
  Se eligieron antes de la extracción por ser los extremos de la anotación
  entre los cursos que no son de proyecto: el de más entradas y el de mayor
  proporción de aceptables (10 de 39). Se excluyen los cursos de proyecto
  (1INF47 y 1INF54) porque su sílabo describe sobre todo el proyecto del curso
  y nombra pocos saberes. Juntos suman 128 entradas, el 17 % del total.
- **Participantes:** dos personas ajenas a la elaboración de la anotación, con
  los cursos aprobados, que trabajan por separado y no hablan entre sí de la
  tarea. Cada una tiene su carpeta (`revision/revisor-1/`,
  `revision/revisor-2/`). Lo que este protocolo dice del participante vale para
  cada uno.
- **Cuándo:** antes de ejecutar los casos de prueba y antes de cualquier ajuste
  del prompt contra la anotación. El participante no ve las salidas del pipeline.

## Qué recibe el participante

1. Los PDF de los dos sílabos, tal como están en
   `casos-de-prueba/silabos-en-orden/`.
2. La hoja de extracción (`revision/hoja-de-extraccion.xlsx`): la consigna y
   una hoja vacía por sílabo.

No recibe la guía de anotación, ni el Anexo L, ni la anotación, ni ejemplos
tomados de los 13 sílabos.

## La consigna

Es el texto de la hoja «Consigna» del Excel. Se le entrega tal cual:

> Este ejercicio compara lo que una persona extrae de un sílabo con lo que
> extrae una máquina. No hay una respuesta correcta fijada de antemano: lo que
> interesa es tu criterio.
>
> Lee el sílabo completo y registra los temas y conceptos que encuentres en
> él, una fila por cada uno.
>
> - **Tema o concepto:** escríbelo como aparece en el sílabo. Si lo
>   identificas sin que el sílabo lo nombre de forma literal, escríbelo con el
>   nombre que usarías.
> - **Tipo:** tema o concepto, según tu criterio.
> - **Texto del sílabo:** copia el fragmento donde aparece, o del que lo
>   deduces.
> - **Página:** la del PDF.
> - **Comentario:** opcional. Cualquier duda o decisión que quieras dejar
>   anotada.
>
> Trabaja solo con el PDF: no uses otros documentos ni herramientas de
> inteligencia artificial. Al terminar cada sílabo, anota cuánto tiempo te
> tomó.

## Sesión de explicación

Antes de empezar, una sesión de unos 15 minutos con el autor:

- Se explica el propósito del experimento con las palabras de la consigna.
- El participante puede conocer el propósito general de la tesis (el
  segundo lo conocía por conversaciones previas); si no lo conoce, no se le
  explica en la sesión. Nunca se le dice cómo extraer: nada de secciones,
  encabezados, literalidad ni tipos.
- Desde el 2026-11-15, el participante no anota su tiempo: avisa al autor al
  empezar y al terminar cada sílabo, y el autor lo registra.
- Se muestra la hoja y se llenan dos filas de práctica con un sílabo de
  `data/raw`, que no pertenece a los 13. La práctica es solo del formato: el
  autor no comenta qué se extrajo, y esas filas no se registran.
- A una pregunta de criterio («¿esto cuenta?», «¿lo parto en dos?») se
  responde siempre «usa tu criterio».

Toda pregunta que el participante haga, durante la sesión o durante la tarea, se
anota en la sección «Preguntas del participante» del registro, con la respuesta
que se le dio.

## Comparación

El autor es el instrumento de la comparación. Se hace por sílabo y por
noción, **sin tomar en cuenta el tipo ni el nivel**: el participante no tiene la
guía, y el emparejamiento de los casos de prueba tampoco usa el tipo
(§5.2.5.4).

### Emparejamiento automático

Lo calcula el evaluador, con la misma normalización de los casos de prueba
(`iekg.ingestion.normalization.normalize_label`):

- Las filas del participante que normalizan igual dentro de un mismo sílabo cuentan
  una sola vez.
- Una fila del participante **coincide** con una noción de la anotación si su
  etiqueta normalizada está entre los nombres de una noción con al menos una
  entrada en ese sílabo. Los nombres de una noción son las etiquetas y los
  alias de todas sus entradas, en cualquier sílabo, como en §5.2.5.4.

### Adjudicación

El autor clasifica cada fila del participante y cada noción de la anotación que el
emparejamiento automático no unió. Lo hace con una de las categorías de
abajo, que quedan fijadas aquí. Cada clasificación lleva una frase que la
justifica y, cuando corresponde, la regla de la guía v2.1 que aplica.

Se adjudica la extracción del segundo participante (decidido el 2026-11-15, antes
de comparar). La del primero se reporta solo con el emparejamiento
automático, como cota inferior del acuerdo. La adjudicación se termina antes
de ingestar 1INF37 y 1INF27 en la medición, para que la salida del pipeline
no influya en las categorías.

**Filas del participante sin noción de la anotación:**

| Categoría | Significado |
|---|---|
| `misma_nocion` | Nombra lo mismo que una noción de la anotación, con otra redacción. Se registra con qué noción. |
| `omision` | El sílabo la sustenta y la guía v2.1 la incluiría, pero la anotación no la registró. |
| `criterio` | La guía v2.1 la excluye o la parte de otra forma (actividad, competencia genérica, herramienta usada solo como equipo, otra granularidad). |
| `no_sustentada` | El sílabo no la sustenta. |

**Nociones de la anotación sin fila del participante:**

| Categoría | Significado |
|---|---|
| `misma_nocion` | Ya emparejada con una fila del participante de la tabla anterior. |
| `no_extraida` | El sílabo la nombra y la guía v2.1 la incluye; el participante no la registró. |
| `inclusion_indebida` | La guía v2.1 la excluye y la anotación la registró igual. |
| `criterio` | La guía v2.1 la incluye; el participante la habría excluido o partido de otra forma. |

Un par `misma_nocion` en el que la redacción del participante es una variante que
la regla de alias de la guía exige registrar (sigla, traducción, singular o
variante de uso común que nombra exactamente lo mismo) se marca además como
**alias faltante**. Si no se marca, el pipeline podría acertar con esa
redacción y el acierto contaría como falso positivo.

## La anotación no se corrige

Decidido el 2026-11-15, antes de comparar ninguna extracción con la
anotación. La anotación se congela con un tag de git **antes** de la
comparación, y el contraste no cambia ninguna entrada: las discrepancias se
reportan por categoría, y su efecto en la precisión se discute (ver abajo).
Así la referencia de la medición de R4 queda fijada antes de cualquier
contraste. La guía sigue en la v2.1.

### Enmienda del 2026-11-16: una corrección tras la adjudicación

Se revierte en parte la decisión anterior, después de terminar la
adjudicación del segundo participante (commit `fac0e8c`) y antes de ingestar
1INF37 y 1INF27 en la medición:

- Se corrige solo lo que la adjudicación clasificó como falla de la
  anotación (`omision`, `inclusion_indebida`, alias faltante), solo en los
  dos sílabos del contraste, y cada corrección se apoya en una regla de la
  guía v2.1. Los 11 sílabos del ajuste del prompt no se tocan, porque su
  ajuste se hizo viendo las salidas del pipeline.
- La adjudicación dio 0 omisiones, 0 alias faltantes y 1 inclusión indebida:
  se retira 1INF27-033 «Notación O grande» (G-0110), un implícito no
  inequívoco de «Medidas asintóticas» (L.4). Queda registrada en
  `gold/consolidacion_changelog.tsv`. La anotación pasa de 745 a 744
  entradas y de 664 a 663 nociones.
- El contraste se sigue reportando contra la versión congelada (tag
  `anotacion-congelada-2026-11-15`): medirlo contra la corregida sería
  circular, porque la corrección sale del mismo contraste. La medición de
  R4 usa la versión corregida (tag `anotacion-corregida-2026-11-16`).
- Las cifras del alcance (39 entradas de 1INF27, 10 aceptables, 128 en
  total) son las de la versión congelada, con la que se eligieron los
  sílabos.

Para reportar el contraste contra la versión congelada:

```powershell
git show anotacion-congelada-2026-11-15:casos-de-prueba/gold/gold_consolidado.tsv > var/gold-congelada.tsv
uv run python scripts/evaluate_ingestion.py review --gold var/gold-congelada.tsv --review-dir casos-de-prueba/revision/revisor-2 --operational-db var/no-existe.sqlite
```

## Qué se reporta

Por sílabo y en total, para cada participante:

- La proporción de filas del participante que coinciden con una noción de la
  anotación, antes y después de la adjudicación.
- La proporción de nociones de la anotación que el participante extrajo, separando
  las obligatorias de las aceptables.
- El conteo de cada categoría y los alias faltantes.
- La concordancia de tipo de los pares emparejados, según el tipo que asignó
  el participante. Es descriptiva: el participante no tiene la regla de tipo de la guía.
- El tiempo que el participante dedicó a cada sílabo.
- Las preguntas del participante.

Entre los dos participantes, el acuerdo por nombre normalizado, en las dos
direcciones y sin adjudicar (`evaluate_ingestion.py agreement`): es la
referencia para leer el acuerdo de cada participante con la anotación.

Después de la corrida final, la **precisión del pipeline contra la extracción
del participante** en los dos sílabos. Un ítem del lote aceptado acierta si su
nombre normalizado coincide con el de una fila del participante, o si el autor
adjudica que nombra lo mismo que una fila (`misma_nocion`, con el mismo
criterio que la regla de alias de la guía). Esta medida no pasa por la
anotación, así que ningún modelo de lenguaje evalúa a otro.

No hay umbral. Es un indicador **no concluyente**: hay dos participantes y dos
sílabos, y los participantes no comparten el criterio de la guía. Un acuerdo alto no
prueba que la anotación sea correcta; un acuerdo bajo se interpreta por
categorías.

Para la discusión de R4, el efecto de cada categoría en la precisión:

- `omision` y alias faltante: una extracción correcta cuenta como falso
  positivo, así que la precisión real es mayor que la medida.
- `inclusion_indebida`: un ítem indebido que el pipeline extrae cuenta como
  acierto, así que la precisión real es menor que la medida.
- `criterio`: no mueve la precisión, porque la anotación define qué es
  correcto según la guía. Muestra cuánto depende la medida de ese criterio.

## Registro

En `casos-de-prueba/revision/`, y los archivos de cada participante en su carpeta:

| Archivo | Contenido |
|---|---|
| `hoja-de-extraccion.xlsx` | La plantilla vacía, con la consigna. |
| `extraccion_<sílabo>.tsv` | La extracción del participante tal como la entregó, exportada sin cambios. El Excel original se guarda aparte. |
| `comparacion_<sílabo>.xlsx` | La salida del evaluador, con las columnas de adjudicación llenadas por el autor. |
| `comparacion_pipeline_<sílabo>.xlsx` | Tras la corrida final, el lote aceptado contra la extracción del participante, con la adjudicación `misma_nocion` del autor. |
| `registro-de-la-revision.md` | Fechas y tiempos de cada participante. |

La constancia firmada **no se versiona**, porque lleva el nombre del participante.
Va en el anexo de la tesis.

## Constancia

Texto propuesto, para el anexo:

> Yo, [nombre], identificado con [código PUCP o DNI], estudiante de
> Ingeniería Informática de la PUCP con los cursos Ingeniería de Software
> (1INF37) y Algoritmia y Estructura de Datos (1INF27), o sus equivalentes
> del plan anterior, aprobados, dejo
> constancia de que el [fecha] extraje, por mi cuenta, los temas y conceptos
> de los sílabos 2026-2 de esos dos cursos. Trabajé solo con los PDF de los
> sílabos y la consigna adjunta. No conocía la guía de anotación ni la
> anotación del autor, y no usé herramientas de inteligencia artificial. Mi
> extracción es la que se adjunta.
>
> [firma] · [fecha]

Un solo anexo lleva las dos constancias, la consigna, la extracción de cada
participante y la tabla resumen de la comparación.
