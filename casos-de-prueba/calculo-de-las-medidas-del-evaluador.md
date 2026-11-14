# Cómo calcula el evaluador cada medida

**Fecha:** 2026-11-14. **Estado:** escrito antes del código e implementado
el mismo día. Las elecciones de la sección 1 siguen pendientes de la revisión
de Giano: cambiar una es cambiar pocas líneas y su prueba.

Documentación interna del repositorio. Dice cómo `scripts/evaluate_ingestion.py`
aplica las reglas de la sección «Casos de prueba de la ingesta automatizada» de
la tesis (§5.2.5). Donde la tesis ya fija algo, aquí solo se dice cómo se
ejecuta. Donde no lo fija, se dice qué se eligió y por qué, y queda marcado
como **elección**: son los puntos que hay que revisar.

**Costo documental:** ninguna edición de entregables. Todo lo de abajo es la
salida 1 de `CLAUDE.md` §8 (el código cumple lo escrito) o un matiz declarado
en este archivo (salida 2). Las elecciones 1 a 6 no contradicen la tesis; la
precisan.

## 1. Lo que la tesis no fija

Se empieza por aquí porque es lo que puede mover una cifra.

**Elección 1. El orden en que se recorren los ítems.** La regla de uno a uno
hace que el resultado dependa del orden: si dos ítems pueden consumir la misma
entrada, el primero la toma y el segundo queda como falso positivo o toma
otra. La tesis no dice en qué orden van. Se usa el del lote: primero los nodos
que crea, en el orden del archivo, y después los nodos existentes que enlaza,
en el orden en que aparecen por primera vez en las aristas. El orden del
archivo es el de la salida del modelo y no se reordena.

Para saber si el orden importó, el evaluador calcula además, por caso, el
máximo de aciertos que daría cualquier orden (un emparejamiento máximo entre
ítems y entradas). Si coincide con los aciertos obtenidos, el orden no cambió
nada. Si no coincide, la diferencia se reporta; la cifra oficial sigue siendo
la del orden del lote.

Tamaño del riesgo, medido sobre la anotación con `normalize_label`: en los 13
sílabos hay 21 pares (nombre, sílabo) en los que un mismo nombre alcanza
entradas de dos nociones distintas del mismo sílabo. Están en 1INF33 (1),
1INF49 (1), 1INF29 (5), 1INF24 (5), 1INF37 (6) y 1INF54 (3). Casi todos son
las partes de un encabezado que nombra más de un saber, y el desempate por
etiqueta los resuelve.

**Elección 2. Un nombre que pertenece a más de una noción.** 47 nombres
normalizados figuran en dos o más nociones. La regla de acierto habla de «una
noción»; aquí un ítem puede emparejar con cualquiera de las nociones que
tienen ese nombre y una entrada en el sílabo. Las candidatas son todas las
entradas libres de esas nociones en el sílabo, y entre ellas decide el
desempate de la tesis, sin cambios.

**Elección 3. El total de la exhaustividad.** La tesis la pide «por caso y en
total» sin definir el total. Se calcula igual que la precisión: suma de
nociones obligatorias recuperadas entre suma de nociones obligatorias de cada
caso. Una noción obligatoria en dos sílabos cuenta dos veces, una por caso.
La F1 total sale de la precisión total y la exhaustividad total.

**Elección 4. Un sílabo sin lote aceptado.** No aporta ítems ni aciertos a la
precisión, que es lo que dice la tesis («queda fuera del grafo»). Sus nociones
obligatorias **sí** entran al denominador de la exhaustividad total, como no
recuperadas: el sistema no las extrajo. Es la lectura conservadora. El caso
aparece en el reporte con su número de intentos y cero ítems.

Esto vale para un sílabo que se intentó y se rechazó todas las veces. Un
sílabo **sin ninguna corrida** en la ventana no se ingestó: no entra en
ningún total y el reporte lo nombra como no ejecutado. Mientras falte alguno
de los 13, no hay veredicto del indicador.

**Elección 5. Cómo se cuentan duplicados y nociones partidas.** La tesis los
define por pares («dos nodos…»). Contar pares infla la cifra cuando hay tres
nodos. Se reporta por noción: cuántos identificadores globales tienen un
duplicado y cuántos nodos sobran (los del mismo tipo menos uno); y cuántos
identificadores globales están partidos. Los nodos de cada grupo se listan.

**Elección 6. La segunda parte compara por nombre, sin uno a uno.** Ver la
sección 7. La regla de uno a uno existe para castigar un nodo repetido en una
ingesta; al ignorar el tipo, un tema y un concepto con el mismo nombre no son
una repetición que castigar.

**Hueco que no se resuelve aquí: la lista de encabezados que nombran más de un
saber.** La excepción de las medidas de fusión la necesita, y hoy vive solo
como constante (`COMPUESTOS`, 27 entradas, todas temas) dentro de
`gold/scripts_consolidacion/idglobal.py`. La anotación no la trae como
columna. El evaluador la lee de ese archivo, que es el que asignó los
identificadores globales: así hay una sola lista. Alternativa descartada por
ahora: copiarla a un archivo de datos, que duplica; o deducirla de la
estructura (alias que también es noción propia), que puede no dar las mismas
27. **Pregunta:** ¿se queda así, o la lista pasa a un archivo de datos de
`gold/` que lean los dos?

**Hueco: el protocolo de revisión no está en el árbol.** El registro de la
revisión y la tesis remiten a
`casos-de-prueba/protocolo-de-revision-de-la-anotacion.md`, que no existe en
la rama ni en el directorio de trabajo (2026-11-14). La segunda parte se
diseñó con lo que dice la tesis en «Anotación de referencia» y con la hoja de
extracción. Las categorías de discrepancia no se conocen aquí; el evaluador
lista las discrepancias y deja la categoría en blanco.

## 2. Entradas

**La anotación.** `casos-de-prueba/gold/gold_consolidado.tsv`: es el único
archivo que trae el identificador global. El número de caso sale del orden en
que aparece cada sílabo en él, que es el orden de ingesta. Una prueba
comprueba que sus filas coinciden con las de los 13 archivos por caso.

**Los lotes.** El almacén de hechos (`var/facts/`, un archivo por corrida
escrita) y el almacén operacional (`var/operational.sqlite`), que dice de qué
curso es cada corrida, en qué estado terminó, con qué modelo y con qué
versión del prompt.

**Los ítems de un lote (D3).** Todo tema o concepto que el lote crea o enlaza:

- los nodos del lote con clase `Topic` o `Concept`;
- los extremos de sus aristas que no son nodos del lote y cuya clase es
  `Topic` o `Concept`. Entran por cualquier tipo de arista, incluido el
  concepto requerido por el curso.

Cada nodo cuenta una vez por lote, aunque aparezca en varias aristas.

**La etiqueta de un nodo existente.** El lote no la trae. Se toma de un índice
de claves que se arma con la capa de referencia (la misma proyección del
backbone que usa la carga) y con los lotes aceptados anteriores de la cadena.
Los nodos de la capa de referencia son áreas y unidades de CS2023: sirven para
reconocer que un extremo no es ítem. Si un extremo no está ni en el lote ni en
el índice, el evaluador se detiene con error: significa que se le dio una
cadena incompleta, y seguir daría una precisión mal calculada sin avisar.

## 3. Qué corridas se miden

Dos modos.

**Cadena** (por defecto). Es la medición de CP-01 a CP-14. Se le indica desde
qué corrida empieza la cadena (`--from-run`), porque el almacén de hechos
acumula también las corridas de ajuste. Dentro de la ventana, por cada sílabo:

- las corridas **rechazadas** anteriores a la aceptada son intentos;
- la primera corrida con archivo de hechos es la aceptada, y es la que se
  mide;
- las **fallidas** no cuentan como intento;
- intentos = rechazadas + 1 si hubo aceptada;
- una corrida posterior a la aceptada del mismo sílabo es un error de la
  cadena: se reporta como advertencia y no se mide.

El índice de claves crece con cada lote aceptado, en el orden de las corridas.

**Corrida suelta** (`--isolated`). Para el ajuste de D1: cada corrida se mide
sola, como hecha sobre la capa de referencia. El índice de claves de cada una
contiene la capa de referencia y su propio lote, nada más. Se miden todas las
corridas aceptadas de la ventana, aunque un sílabo tenga varias (una por
versión del prompt), y cada fila lleva el modelo y la versión del prompt. No
hay CP-14, porque no hay grafo final, ni veredicto del indicador. El total
usa la última corrida de cada sílabo.

**Los dos sílabos reservados.** 1INF27 y 1INF37 no se usan para ajustar.

- En el reporte hay tres totales: los 13 (el del indicador), los 11 usados
  para ajustar y los 2 reservados.
- Con `--hide-held-out`, los dos reservados no se evalúan ni se escriben: el
  reporte los nombra como ocultos y solo trae el total de los otros. Sirve
  para correr el evaluador durante el ajuste sin ver, ni por descuido, una
  cifra de los reservados. En modo cadena, sus lotes sí alimentan el índice
  de claves.

## 4. Emparejamiento (CP-01 a CP-13)

**Normalización.** `iekg.ingestion.normalization.normalize_label`, sobre la
etiqueta en español del ítem y sobre cada etiqueta y nombre alternativo de la
anotación. Es la función del enlace, sin copia.

**Nombres de una noción.** La unión de las etiquetas y los nombres
alternativos de todas las entradas con ese identificador global, en los 13
sílabos.

**Recorrido.** Para cada ítem, en el orden de la elección 1:

1. Candidatas: las entradas **del sílabo del caso**, todavía libres, cuya
   noción tiene el nombre del ítem entre sus nombres.
2. Sin candidatas: falso positivo. Esto cubre los dos casos de la tesis: el
   nombre no es de ninguna noción del sílabo, o lo es pero sus entradas ya se
   consumieron (un nodo repetido en la ingesta).
3. Con candidatas: se elige una y se marca consumida. Orden de preferencia:
   primero la entrada cuya etiqueta normalizada es igual al nombre del ítem;
   después, la del mismo tipo que el ítem (`Topic` con tema, `Concept` con
   concepto); después, la de menor identificador de entrada.

Una entrada aceptable se consume igual que una obligatoria y cuenta como
acierto. El tipo solo interviene como segundo criterio del desempate, que es
lo que dice la tesis.

## 5. Medidas por caso y totales

| Medida | Cálculo |
|---|---|
| Ítems | Ítems del lote aceptado (sección 2). |
| Aciertos | Ítems que consumieron una entrada. |
| Falsos positivos | Ítems − aciertos. |
| Precisión | Aciertos / ítems. |
| Nociones obligatorias | Identificadores globales con al menos una entrada obligatoria en el sílabo. |
| Recuperadas | De esas, las que tienen consumida alguna de sus entradas en el sílabo, obligatoria o aceptable. |
| Exhaustividad | Recuperadas / nociones obligatorias. |
| F1 | 2 · P · E / (P + E); 0 si ambas son 0. |
| Concordancia de tipo | Aciertos cuyo tipo es el de la entrada consumida / aciertos. |
| Intentos | Sección 3. |
| Máximo de aciertos | Elección 1; solo diagnóstico. |

Si un denominador es 0, la medida se reporta vacía, no como 0.

**Total.** Sumas de numeradores y denominadores, nunca promedios de
porcentajes. La precisión del indicador de R4 es la suma de aciertos entre la
suma de ítems de los 13 casos; el conjunto se aprueba si es mayor o igual a
75 %. El veredicto solo se emite en modo cadena, sin ocultar nada y con los
13 casos en la ventana; en cualquier otro caso queda vacío.

El reporte lista cada falso positivo (nombre y tipo) y cada noción
obligatoria no recuperada, por caso: son lo que se lee para entender una
cifra.

## 6. Intentos rechazados

De cada corrida rechazada de la cadena se lee el lote candidato que guarda el
almacén operacional. Si existe, se mide con el mismo emparejamiento y el
índice de claves del momento (los lotes aceptados anteriores), y se reporta
aparte: ítems, aciertos y precisión. No entra en ningún total. Si la corrida
se rechazó porque la salida del modelo nunca llegó a ser un lote (EX-01), no
hay lote que leer y se reporta como ilegible.

## 7. CP-14: medidas de fusión

Solo en modo cadena. Se calcula con los lotes, no con Neo4j: el grafo final
es la unión de los lotes aceptados.

Cada nodo, identificado por su clave, acumula los identificadores globales de
las entradas que consumió en cada caso donde fue ítem. Un nodo que fue falso
positivo en todos sus casos no acumula ninguno y no participa.

- **Duplicado:** un identificador global que acumularon dos o más nodos del
  mismo tipo.
- **Noción partida:** un identificador global que acumularon nodos de los dos
  tipos. No es error.
- **Fusión errónea:** un nodo con dos o más identificadores globales.
  **Excepción:** se descuentan los identificadores de los encabezados que
  nombran más de un saber; si queda exactamente uno, el nodo no es fusión
  errónea y se lista aparte como exceptuado. Si quedan dos o más, o ninguno
  (el nodo solo acumuló encabezados de ese tipo, y más de uno), es fusión
  errónea.

Un identificador global puede estar a la vez duplicado y partido; se cuenta
en las dos.

Con `--hide-held-out` CP-14 no se calcula: sin los dos casos, el grafo no es
el final. Si falta algún caso en la ventana se calcula igual, con una
advertencia.

## 8. Segunda parte: la extracción del revisor

Entrada: `casos-de-prueba/revision/hoja-de-extraccion.xlsx`, una hoja por
sílabo (`1INF37`, `1INF27`), encabezados en la fila 3, una fila por tema o
concepto desde la fila 4. Se lee la columna «Tema o concepto»; las filas sin
nombre se saltan. El tipo que anotó el revisor no se usa.

Todo se compara por nombre normalizado, sin tipo, sin nivel y sin uno a uno
(elección 6). Los nombres repetidos del revisor cuentan una vez; cuántas filas
se colapsaron se reporta.

**Revisor contra anotación, en las dos direcciones**, por sílabo y en total:

- *Lo que extrajo el revisor y la anotación registra:* nombres del revisor
  que están entre los nombres de alguna noción con entrada en ese sílabo,
  entre los nombres del revisor.
- *Las nociones de la anotación que el revisor extrajo:* nociones con entrada
  en ese sílabo, de cualquier nivel, que tienen entre sus nombres algún
  nombre del revisor, entre las nociones del sílabo.

Las discrepancias salen en un TSV aparte, una por fila, con la categoría en
blanco: los nombres del revisor que la anotación no registra (con el texto
del sílabo y el comentario que escribió) y las nociones que el revisor no
extrajo (con su etiqueta, nivel y evidencia). La adjudicación es de Giano; el
evaluador no clasifica.

La proporción de nociones se cuenta por noción y no por entrada, así que el
denominador es menor que las entradas del sílabo: 39 nociones en 1INF27 y 85
en 1INF37 (89 entradas), 124 en total frente a las 128 entradas que cita la
tesis.

Como la comparación exige coincidencia de nombres y el revisor no escribe
nombres alternativos, las dos proporciones son cotas inferiores, y más
bajas que las del pipeline contra la anotación.

**Pipeline contra revisor.** Para el lote aceptado de cada uno de los dos
sílabos, en la cadena: ítems cuyo nombre normalizado está entre los nombres
del revisor, entre los ítems del lote. Se lista lo que no coincide. Mide la
precisión del pipeline sin pasar por la anotación.

## 9. Salidas

En `var/measurements/`, como `scripts/measure_navigation.py`: un JSON con todo
el detalle y, por consola, las tablas en Markdown.

- `cp-extraction-<fecha-hora>.json`: modo, ventana de corridas, anotación
  usada (ruta y su línea de metadatos), casos, totales, intentos rechazados,
  CP-14 y advertencias.
- `review-<fecha-hora>.json` y `review-discrepancies-<fecha-hora>.tsv`.

Código de salida de la primera parte: 0 si el indicador se aprueba o si no
corresponde veredicto; 1 si hay veredicto y la precisión es menor que 75 %.

## 10. Pruebas

Sin Neo4j. Una negativa por regla, con una anotación mínima escrita en la
prueba:

- **Uno a uno:** dos ítems con nombres de la misma noción y una sola entrada
  dan un acierto y un falso positivo.
- **Desempate:** con dos entradas candidatas gana la de etiqueta igual; sin
  etiqueta igual, la del mismo tipo; con todo igual, la de menor
  identificador. Cada criterio, con un caso donde el siguiente habría elegido
  otra entrada.
- **Aceptables:** una aceptable extraída es acierto; una aceptable que falta
  no baja la exhaustividad; una obligatoria que falta sí.
- **Tipo:** un `Topic` cuyo nombre es el de una entrada concepto es acierto,
  y baja la concordancia de tipo.
- **Fusión:** un caso por cada situación y uno por cada lado de la excepción.
- **Ítems:** un nodo existente enlazado es ítem con la etiqueta del lote
  anterior; una unidad de CS2023 no lo es; un extremo desconocido detiene la
  evaluación.

**Propiedad:** con la anotación real, un lote armado por sílabo con una
etiqueta por entrada y su tipo da 100 % de precisión, de exhaustividad y de
concordancia de tipo en los 13 casos, y el máximo de aciertos coincide.
