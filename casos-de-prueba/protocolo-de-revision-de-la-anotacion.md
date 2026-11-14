# Protocolo de revisión independiente de la anotación de referencia

## Propósito

La anotación de referencia la produjo un modelo de lenguaje siguiendo la guía
v2.1 (tesis, §5.2.5.2). Este protocolo la compara con la extracción de una
persona que trabaja **sin la guía y sin ver la anotación**, de modo que el
juicio humano no quede anclado al del modelo.

Se escribe antes de recibir la extracción, para que ninguna regla se decida
después de ver los resultados.

Es un documento interno del repositorio, no un entregable. La tesis resume en
§5.2.5.2 lo que cambia la lectura de los números; el detalle está aquí.

## Alcance

- **Sílabos:** 1INF37 (CP-11, 89 entradas) y 1INF27 (CP-02, 39 entradas).
  Se eligieron antes de la extracción por ser los extremos de la anotación
  entre los cursos que no son de proyecto: el de más entradas y el de mayor
  proporción de aceptables (10 de 39). Se excluyen los cursos de proyecto
  (1INF47 y 1INF54) porque su sílabo describe sobre todo el proyecto del curso
  y nombra pocos saberes. Juntos suman 128 entradas, el 17 % del total.
- **Revisor:** una persona ajena a la elaboración de la anotación, con los
  cursos aprobados. Es una sola persona, y eso se declara como limitación.
- **Cuándo:** antes de ejecutar los casos de prueba y antes de cualquier ajuste
  del prompt contra la anotación. El revisor no ve las salidas del pipeline.

## Qué recibe el revisor

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
- Se muestra la hoja y se llenan dos filas de práctica con un sílabo de
  `data/raw`, que no pertenece a los 13. La práctica es solo del formato: el
  autor no comenta qué se extrajo, y esas filas no se registran.
- A una pregunta de criterio («¿esto cuenta?», «¿lo parto en dos?») se
  responde siempre «usa tu criterio».

Toda pregunta que el revisor haga, durante la sesión o durante la tarea, se
anota en la sección «Preguntas del revisor» del registro, con la respuesta
que se le dio.

## Comparación

El autor es el instrumento de la comparación. Se hace por sílabo y por
noción, **sin tomar en cuenta el tipo ni el nivel**: el revisor no tiene la
guía, y el emparejamiento de los casos de prueba tampoco usa el tipo
(§5.2.5.4).

### Emparejamiento automático

Lo calcula el evaluador, con la misma normalización de los casos de prueba
(`iekg.ingestion.normalization.normalize_label`):

- Las filas del revisor que normalizan igual dentro de un mismo sílabo cuentan
  una sola vez.
- Una fila del revisor **coincide** con una noción de la anotación si su
  etiqueta normalizada está entre los nombres de una noción con al menos una
  entrada en ese sílabo. Los nombres de una noción son las etiquetas y los
  alias de todas sus entradas, en cualquier sílabo, como en §5.2.5.4.

### Adjudicación

El autor clasifica cada fila del revisor y cada noción de la anotación que el
emparejamiento automático no unió. Lo hace con una de las categorías de
abajo, que quedan fijadas aquí. Cada clasificación lleva una frase que la
justifica y, cuando corresponde, la regla de la guía v2.1 que aplica.

**Filas del revisor sin noción de la anotación:**

| Categoría | Significado |
|---|---|
| `misma_nocion` | Nombra lo mismo que una noción de la anotación, con otra redacción. Se registra con qué noción. |
| `omision` | El sílabo la sustenta y la guía v2.1 la incluiría, pero la anotación no la registró. |
| `criterio` | La guía v2.1 la excluye o la parte de otra forma (actividad, competencia genérica, herramienta usada solo como equipo, otra granularidad). |
| `no_sustentada` | El sílabo no la sustenta. |

**Nociones de la anotación sin fila del revisor:**

| Categoría | Significado |
|---|---|
| `misma_nocion` | Ya emparejada con una fila del revisor de la tabla anterior. |
| `no_extraida` | El sílabo la nombra y la guía v2.1 la incluye; el revisor no la registró. |
| `inclusion_indebida` | La guía v2.1 la excluye y la anotación la registró igual. |
| `criterio` | La guía v2.1 la incluye; el revisor la habría excluido o partido de otra forma. |

Un par `misma_nocion` en el que la redacción del revisor es una variante que
la regla de alias de la guía exige registrar (sigla, traducción, singular o
variante de uso común que nombra exactamente lo mismo) se marca además como
**alias faltante**. Si no se marca, el pipeline podría acertar con esa
redacción y el acierto contaría como falso positivo.

## Corrección de lo sistemático

Se corrige en la anotación solo un **error de aplicación sistemático**, es
decir, un patrón que cumple las tres condiciones:

1. Su categoría es `omision`, `inclusion_indebida` o alias faltante. Las
   categorías `criterio`, `no_sustentada` y `no_extraida` nunca se corrigen.
2. Aparece en los dos sílabos.
3. Se enuncia como una sola regla de la guía v2.1 que la anotación no aplicó.

Cada patrón que cumple las tres condiciones es una **clase**.

Las clases se escriben en el registro, con su regla y sus instancias en los
dos sílabos, **antes** de buscarlas en los otros once.

**Tope:** como máximo **2 clases** y como máximo **75 entradas cambiadas** en
total en los 13 sílabos (el 10 % de 745). Si se encuentran más clases, o si al
aplicarlas se pasa de 75 entradas, no se corrige nada: todo se reporta y la
limitación se declara.

Dentro del tope, la corrección se hace así:

1. El autor busca cada clase, a mano, en los 13 sílabos, aplicando solo la
   regla escrita. Puede apoyarse en un modelo de lenguaje para listar
   candidatos, pero cada cambio lo decide él.
2. Cada cambio se registra en `gold/consolidacion_changelog.tsv`, con
   `categoria=revision_independiente` y `motivo=clase C<n>: <regla>`. Una
   entrada nueva recibe el siguiente identificador libre de su sílabo.
3. Se vuelven a ejecutar los scripts de consolidación (`idglobal.py`,
   `validate.py`), y los identificadores globales se asignan con las reglas
   de la guía.
4. Se actualizan la Tabla 22 y las cifras de §5.2.5.2: entradas, nociones y
   nociones compartidas.

Las discrepancias que no forman una clase no se corrigen en ningún sílabo, ni
siquiera en los dos revisados. Así, ningún sílabo queda con un tratamiento
distinto al de los demás.

La guía no cambia: sigue en la v2.1. Lo que el revisor ve distinto de la guía
cae en `criterio` y se reporta.

**La anotación se congela con un tag de git** al terminar este paso, haya o
no correcciones. Ese tag es la referencia de la medición de R4, y la
anotación no cambia después de él.

## Qué se reporta

Todas las medidas de acuerdo se calculan contra la anotación **anterior** a
la corrección; si no, la comparación sería circular.

Por sílabo y en total:

- La proporción de filas del revisor que coinciden con una noción de la
  anotación, antes y después de la adjudicación.
- La proporción de nociones de la anotación que el revisor extrajo, separando
  las obligatorias de las aceptables.
- El conteo de cada categoría y los alias faltantes.
- La concordancia de tipo de los pares emparejados, según el tipo que asignó
  el revisor. Es descriptiva: el revisor no tiene la regla de tipo de la guía.
- El tiempo que el revisor dedicó a cada sílabo.
- Las preguntas del revisor.
- Las clases encontradas, las entradas que cambió cada una o, si se superó el
  tope, la razón por la que no se corrigió nada.

Después de la corrida final, la **precisión del pipeline contra la extracción
del revisor** en los dos sílabos. Un ítem del lote aceptado acierta si su
nombre normalizado coincide con el de una fila del revisor, o si el autor
adjudica que nombra lo mismo que una fila (`misma_nocion`, con el mismo
criterio que la regla de alias de la guía). Esta medida no pasa por la
anotación, así que ningún modelo de lenguaje evalúa a otro.

No hay umbral. Es un indicador **no concluyente**: hay un solo revisor y dos
sílabos, y el revisor no comparte el criterio de la guía. Un acuerdo alto no
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

En `casos-de-prueba/revision/`:

| Archivo | Contenido |
|---|---|
| `hoja-de-extraccion.xlsx` | La plantilla vacía, con la consigna. |
| `extraccion_<sílabo>.tsv` | La extracción del revisor tal como la entregó, exportada sin cambios. El Excel original se guarda aparte. |
| `comparacion_<sílabo>.tsv` | La salida del evaluador, con las columnas de adjudicación llenadas por el autor. |
| `comparacion_pipeline_<sílabo>.tsv` | Tras la corrida final, el lote aceptado contra la extracción del revisor, con la adjudicación `misma_nocion` del autor. |
| `registro-de-la-revision.md` | Fechas, las preguntas del revisor con sus respuestas, las clases (escritas antes de aplicarlas) y los cambios resultantes. |

La constancia firmada **no se versiona**, porque lleva el nombre del revisor.
Va en el anexo de la tesis.

## Constancia

Texto propuesto, para el anexo:

> Yo, [nombre], identificado con [código PUCP o DNI], estudiante de
> Ingeniería Informática de la PUCP con los cursos Ingeniería de Software
> (1INF37) y Algoritmia (1INF27) aprobados, dejo
> constancia de que el [fecha] extraje, por mi cuenta, los temas y conceptos
> de los sílabos 2026-2 de esos dos cursos. Trabajé solo con los PDF de los
> sílabos y la consigna adjunta. No conocía la guía de anotación ni la
> anotación del autor, y no usé herramientas de inteligencia artificial. Mi
> extracción es la que se adjunta.
>
> [firma] · [fecha]

El anexo lleva la constancia, la consigna, la extracción de los dos sílabos y
la tabla resumen de la comparación.
