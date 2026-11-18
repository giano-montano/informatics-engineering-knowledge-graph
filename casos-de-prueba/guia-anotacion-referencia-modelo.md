
# Handoff — Anotación de referencia de temas y conceptos (R4, InfoKnows) · v2.1
 
## Contexto
 
- Tesis de pregrado (Ingeniería Informática PUCP): InfoKnows, un sistema de gestión del conocimiento sobre un grafo de propiedades (Neo4j) que representa el currículo de la especialidad.
- Un pipeline con LLM ingesta sílabos en PDF y escribe temas y conceptos en el grafo. Cada ingesta recibe en el prompt los nodos que ya existen, para enlazarlos o no duplicarlos. El pipeline asigna tema o concepto con la misma regla de estructura que esta guía.
- R4 compromete un indicador: precisión de extracción de entidades (≥ 75 %). Este proyecto construye la anotación de referencia contra la que se mide.
- **Corpus:** los 13 sílabos 2026-2 cargados en el proyecto. Si la descripción del proyecto dice otra cosa, manda esta guía.
- Tu papel es solo anotar. No diseñas el pipeline ni ves sus salidas.

## Decisiones cerradas (no las reabras)
 
- Solo se evalúan entidades (temas y conceptos). `tema_padre` se registra, pero no se evalúa.
- El emparejamiento por etiqueta y alias subestima la precisión. Se acepta y se reporta como cota inferior.
- Una aceptable extraída cuenta como acierto.
- El tipo se ignora al emparejar; la concordancia de tipo se reporta aparte.
- No hay anotación humana paralela; se declara como limitación.
- No hay registro de precedentes. La coherencia entre sílabos la dan las reglas por defecto de esta guía y una re-pasada en la consolidación.
- La dependencia del orden de ingesta la resuelve la regla de vocabulario por `id_global` (ver *Cómo se usará*).
## Reglas de independencia
 
1. Nunca uses salidas, prompts ni esquemas del pipeline. Si aparecen en el proyecto, avisa y no los uses.
2. El gold de cada sílabo describe **todo lo que el sílabo contiene**, aunque otro sílabo ya lo tenga. Si un concepto aparece en tres sílabos, va en los tres.
3. Esta guía describe qué es correcto, no qué le resulta fácil acertar a un LLM. No la relajes para facilitar coincidencias.
## Flujo
 
Un chat por sílabo y un chat final de consolidación.
 
En cada chat de sílabo:
 
1. Lee completo el sílabo que indica el mensaje. Si el mensaje no indica ninguno, toma el de menor numeración en el nombre de archivo que aún no tenga `gold_<código>.tsv` en el proyecto. Usa solo ese sílabo, aunque el proyecto contenga otros. Si solo te llegan fragmentos, pide el PDF adjunto y detente.
2. Anota aplicando las reglas de esta guía, sin preguntar lo que la guía ya resuelve.
3. Si un caso no está cubierto, decide según el espíritu de la guía, explica en una frase la decisión en la columna `nota` y lístalo al final, con el valor que aplicaste (máximo unas 6). El usuario solo responde lo que quiera cambiar.
4. Entrega `gold_<código>.tsv`. Si puedes escribir en el proyecto, escríbelo ahí; si no, entrégalo como archivo.
## Qué se anota
 
**Entidades:** solo temas y conceptos. No se anotan cursos, recursos ni unidades de conocimiento de CS2023; ignora que estas existen.
 
**Secciones:**
 
| Sección | Qué aporta |
|---|---|
| Sumilla y contenidos (unidades, capítulos) | Entidades obligatorias y aceptables |
| Otras secciones (resultados de aprendizaje, requisitos, metodología…) | Solo entidades aceptables |
| Bibliografía y sistema de evaluación | Nada |
 
**No son entidades:** actividades (laboratorio, exposición, proyecto como entregable), evaluaciones, títulos de libros, competencias genéricas (trabajo en equipo, comunicación oral), nombres o códigos de cursos, plataformas administrativas y encabezados genéricos ("Introducción", "Repaso", "Presentación del curso", "Unidad I").
 
## Tipo (por estructura del documento)
 
- **Tema:** título de unidad, capítulo o subunidad que agrupa ítems.
- **Concepto:** cada ítem listado dentro de un tema.
- **Dos niveles de encabezado:** es tema obligatorio el nivel que contiene directamente los ítems. El nivel superior es tema aceptable si nombra un saber; si es genérico, no es entidad.
- **Entidad que aparece solo en la sumilla:** concepto. Si coincide con un tema de los contenidos, es la misma fila.
- **Todo concepto lleva `tema_padre`.** Al que no tiene encabezado (viene de la sumilla o de otras secciones) asígnale el tema de los contenidos que mejor le corresponda. Si ninguno encaja, déjalo vacío y explícalo en `nota`.
## Granularidad y reglas por defecto
 
- **"Introducción a X", "Fundamentos de X":** la entidad es X.
- **Enumeraciones** ("1FN, 2FN, 3FN y FNBC"): una fila obligatoria por cada elemento que se pueda nombrar por sí solo. El agrupador ("formas normales") va como aceptable de tipo tema si no aparece literal; si aparece literal como encabezado, es tema obligatorio.
- **Ítem que nombra más de un saber** ("pilas y colas"): una fila por saber nombrable. Si juntos forman un solo saber con nombre propio, va una sola fila.
- **Encabezado que nombra más de un saber** ("Complejidad y eficiencia algorítmica"): una sola fila de tema con la etiqueta literal. Cada saber nombrable del encabezado va como alias ("complejidad algorítmica", "eficiencia algorítmica"); es una excepción deliberada a la regla de alias exactos. Si la sumilla nombra uno de esos saberes, es la misma fila.
- **Lenguajes, notaciones y estándares** (SQL, UML, HTTP): concepto, con el nivel que les corresponda.
- **Productos y herramientas concretas** (MySQL, Git, Eclipse): concepto aceptable cuando el curso los enseña o los usa como parte del contenido. Si solo aparecen como equipo o requisito para cursar (sistema operativo, IDE, computador), no son entidad.
- **Calificadores:** se conservan. "SQL avanzado" queda como "SQL avanzado"; no generalices ni especialices.
- **Fórmulas de actividad:** se quitan ("estudio de", "aplicaciones de") salvo que cambien el significado.
- **Repeticiones dentro del mismo sílabo:** una sola fila por noción y tipo. Si la misma noción aparece como encabezado y también como ítem, van dos filas: una de tema y otra de concepto.
## Niveles
 
- **Obligatoria:** nombrada literalmente en la sumilla o los contenidos.
- **Aceptable:**
  - (a) el agrupador de una enumeración partida;
  - (b) un concepto implícito inequívoco: el texto lo nombra de forma indirecta y cualquier lector del área lo identificaría igual;
  - (c) una entidad nombrada solo en otras secciones admitidas;
  - (d) los casos que las reglas por defecto marcan como aceptables.
- Un implícito que no es inequívoco no se anota.
## Etiqueta, alias y evidencia
 
- **etiqueta:** como figura en el sílabo, sin numeración, horas ni puntuación final, en el idioma del sílabo.
- **alias:** siglas, traducción al inglés o al español, plurales irregulares y variantes de uso común que nombran exactamente lo mismo (por ejemplo, "normalización de bases de datos" para "normalización" en un curso de bases de datos). Van separados por `|`. Como el emparejamiento es exacto, un alias que falta convierte un acierto en error. No pongas como alias algo más general ni más específico (salvo las mitades de un encabezado que nombra más de un saber; ver *Granularidad*). Si la etiqueta está en plural, su singular va como alias ("árboles" → "árbol", "funciones hash" → "función hash"), aunque la normalización ya lo cubra.
- **evidencia:** el fragmento literal mínimo del sílabo que sustenta la fila. Para la aceptable (b), el fragmento del que se infiere.
## Formato de salida
 
TSV, una fila por entidad. Primera línea de metadatos:
 
```
# silabo=<código> | curso=<nombre> | anotador=<modelo> | guia=v2.1 | fecha=<AAAA-MM-DD>
```
 
Columnas:
 
```
id	tipo	nivel	etiqueta	alias	tema_padre	seccion	evidencia	nota
```
 
- `id`: `<código>-NNN`
- `tipo`: `tema` | `concepto`
- `nivel`: `obligatoria` | `aceptable`
- `tema_padre`: id del tema del mismo sílabo al que pertenece el concepto; vacío en los temas
- `seccion`: `sumilla` | `contenidos` | `otra`
- `nota`: vacía, salvo en decisiones que la guía no cubre
- Sin tabulaciones dentro de los campos.
## Consolidación (chat final)
 
**Entradas:** los 13 TSV. Lee un sílabo solo si una corrección lo exige.
 
**Pasos:**
 
1. **Re-pasada de coherencia.** Comprueba que cada regla por defecto se aplicó igual en los 13 sílabos y que las decisiones de la columna `nota` no se contradicen entre sí. Corrige según la guía; si corregir exige agregar una fila, relee ese sílabo. Lista cada cambio al usuario.
2. **Asignación de `id_global`** con las reglas de abajo.
3. **Generación** de `gold_consolidado.tsv` con un script que una los 13 TSV y el mapeo `id_local → id_global`. No reescribas filas a mano.
**Salida:** `gold_consolidado.tsv`, con todas las filas de los 13 golds y dos columnas al inicio, `silabo` e `id_global`. Cada fila aparece exactamente una vez. Formato de `id_global`: `G-NNNN`.
 
**Normalizar** una etiqueta es pasarla a minúsculas, quitarle tildes y signos de puntuación, dejar un solo espacio entre palabras y quitar la s final de cada palabra. La evaluación usa la misma función.
 
> **Nota v2.1:** quitar solo la *s* final no iguala los plurales en *-es* ("árboles" → "arbole" frente a "árbol" → "arbol"; "funciones" frente a "función"). La implementación de la función de normalización lo corregirá. Mientras tanto, la regla de alias en singular (ver *Etiqueta, alias y evidencia*) cubre el hueco en los golds.
 
**Reglas de `id_global`:**
 
1. Mismo `id_global` si y solo si es la misma noción de conocimiento, **sin importar el tipo** ni la redacción. Un tema de un sílabo y un concepto de otro pueden compartir `id_global`.
2. Se fusiona por identidad, no por parentesco. Una generalización, una parte o un caso particular llevan ids distintos ("SQL" frente a "SQL avanzado"; "normalización" frente a "FNBC").
3. Si las etiquetas o alias coinciden tras normalizar, van al mismo id sin preguntar. Si la evidencia muestra significados distintos ("pruebas" de software frente a "pruebas" como demostraciones), sepáralas y escala.
4. Toda fusión sin coincidencia de etiqueta o alias se escala, agrupada en una tabla: pares propuestos, evidencia de cada lado y decisión aplicada. Esta regla importa más que las otras: cada fusión une vocabularios, y eso afecta directamente la precisión.
## Cómo se usará
 
- **Vocabulario de un `id_global`:** las etiquetas y alias de todas sus filas, de cualquier sílabo.
- **Precisión.** Se calcula por corrida, sobre el lote aceptado de esa corrida: nodos nuevos y referencias a nodos existentes.
  - Un ítem es acierto si su etiqueta normalizada pertenece al vocabulario de un `id_global` que tiene fila en el sílabo de esa corrida.
  - Cada acierto consume una fila de ese sílabo con ese id, empezando por la del mismo tipo. Si no queda fila disponible, el ítem es falso positivo.
  - No importa qué corrida creó el nodo ni cómo se evaluó allí.
  - Las aceptables cuentan como acierto. El tipo se ignora; la concordancia de tipo se reporta aparte. El resultado se reporta como cota inferior.
- **Fusión** (sobre el grafo final, como medida descriptiva). Cada nodo recibe los `id_global` de las filas que consumió en las corridas donde apareció.
  - Dos nodos del mismo tipo con el mismo id: duplicado.
  - Dos nodos de distinto tipo con el mismo id: noción partida, no es error.
  - Un nodo con dos ids distintos: fusión errónea.
- **Descripción en la tesis:** anotación de referencia hecha por un LLM con adjudicación humana de los casos escalados.
## Cambios v2 → v2.1
 
- Flujo: si el mensaje no indica sílabo, se toma el siguiente por numeración sin gold.
- Encabezados que nombran más de un saber: las mitades van como alias de la fila de tema.
- Plurales: el singular va siempre como alias. La normalización se corregirá para los plurales en *-es*.
- Productos y herramientas: no son entidad si solo aparecen como equipo o requisito para cursar.
- `gold_1INF27.tsv` se anotó con v2 y se actualizó a v2.1.