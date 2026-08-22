# Los cuatro pipelines de ingesta: qué son, cómo se miden y qué dijeron

**Fecha: 2026-08-15. Registro congelado.**

Documento de aprendizaje. Explica los cuatro pipelines de ingesta que ya corren
de punta a punta, las decisiones de modelo, de código y de framework que hay
detrás, cómo se producen los números, qué dicen esos números y qué queda
abierto.

Todo lo que aparece aquí se ejecutó ese día contra el sílabo real de 1INF33
(`lab/docs/syllabus/1INF33-2026-2-SILABO-BASES-DE-DATOS.PDF`). Las cifras salen
de los artefactos que quedaron en `build/runs/`; ninguna es estimada.

Complementa a `lab/findings/0005`, que registra la escalera y los techos de la
capa gratuita. Aquí el foco está en **entender el sistema completo** y en **leer
los resultados**, no en registrar el hallazgo.

---

## 0. La advertencia que va antes que los números

**Ninguna cifra de este documento es la precisión del resultado R4.** Hay dos
razones independientes, y las dos importan:

1. **La referencia no es el gold standard.** Se midió contra
   `lab/gold/1INF33-2026-2_annotation.claude-contraste.yaml`, una anotación de
   contraste escrita por un LLM, no por Giano. El campo `annotator` dice
   `claude-contraste`, y cada manifiesto de corrida lleva
   `reference_annotation.is_gold: false`. La compuerta se abrió a propósito,
   sabiendo el costo, para poder ver los pipelines funcionando.
2. **La comparación es automática, y por eso es una cota inferior.** Si el
   pipeline extrae algo correcto que la anotación no listó, el puntaje lo cuenta
   como error. El criterio de la tesis ("verificación manual de la precisión de
   entidades extraídas ≥ 75%") lo cuenta un humano leyendo el sílabo, y eso no
   se sustituye con esto.

Para qué sirven entonces: **para comparar corridas entre sí**. Con la misma
referencia y el mismo matcher, la diferencia entre dos corridas es atribuible
aunque el nivel absoluto esté desplazado hacia abajo. Eso es exactamente lo que
la escalera necesita.

Con una condición que en esta tanda **todavía no se cumple entera**, y es la
tercera advertencia: dos corridas solo son comparables si difieren en **una**
cosa. Los arreglos del día no llegaron a todas, así que parte de la tabla de §7
compara filas que difieren en tres. Cuáles sí y cuáles no, en **§7.0**; qué hacer
al respecto, en **§9**.

Consecuencia ya asumida: **1INF33 no puede ser el sílabo del gold ciego**, porque
en esta sesión se vieron sus extracciones. Queda como sílabo de desarrollo, y el
gold se levanta sobre otro documento.

---

## 1. Qué hace un pipeline aquí

Un pipeline convierte **un PDF de sílabo** en **un archivo Cypher listo para
revisar**, pasando por una extracción con LLM que está restringida por la
ontología.

```
PDF -> texto -> (ontología verbalizada) -> extracción tipada
    -> enlace de cada Tema contra el backbone CS2023
    -> A-box: acuñar IRIs, validar contra las reglas, emitir Cypher
```

Dos reglas estructurales que no se relitigan y que conviene tener presentes al
leer todo lo demás:

- **El LLM nunca escribe en la base.** Produce datos; el Cypher lo construye
  código determinista (`src/iekg/abox.py`). Es la respuesta estructural al modo
  de fallo que declara toda la literatura revisada, y es contribución nombrable
  de la tesis (`findings/0003`).
- **El pipeline emite, no carga.** Una corrida deja archivos en `build/runs/` y
  nadie los ejecuta contra Neo4j. Misma doctrina que `integrity.py`. Dos
  corridas se diffean; una extracción mala nunca es una base mala.

---

## 2. Los cuatro pipelines: una escalera, no cuatro sistemas

Están declarados en `lab/pipelines.yaml` y los ejecuta un intérprete pequeño,
`src/iekg/pipeline.py`. Un pipeline **es configuración**, no un módulo: por eso
no hay cuatro copias del mismo código divergiendo.

**Cada peldaño agrega exactamente una cosa al de abajo.** Esa es la razón de que
la comparación diga algo. Comparar SPIRES contra OneKE no diría nada, porque
difieren en veinte cosas a la vez; comparar "con y sin recuperación de
candidatos" sí.

| | Título | Qué agrega | Qué aísla | Etapas |
|---|---|---|---|---|
| **P0** | Sin esquema | Una llamada: "extrae conceptos y relaciones" | Cuánto vale restringir | `load → extract_free → build_abox` |
| **P1** | Una pasada restringida | T-box verbalizada + salida tipada | Conformidad por prompt | `load → verbalize → extract_typed → link_lexical → build_abox` |
| **P2** | Multi-etapa (SPIRES) | Temas primero, Conceptos por Tema después | Si escalonar mejora | `load → verbalize → extract_topics → extract_concepts → link_lexical → build_abox` |
| **P3** | + enlace por recuperación | Candidatos del backbone por embeddings, con umbral y margen | El eslabón frágil | `load → verbalize → extract_topics → extract_concepts → link_retrieval → build_abox` |

### 2.1 P0 — la línea base sin esquema

Una sola llamada, sin `output_type`, sin ontología en el prompt, sin vocabulario
cerrado. El prompt entero es: *"Extract the concepts taught by this course and
the relations between them. Return your answer as JSON."*

**No darle un modelo Pydantic es deliberado.** Entregarle un contrato tipado ya
sería la restricción cuyo valor esta línea base existe para medir; la comparación
empezaría en P1 sin piso debajo.

Como el modelo puede contestar JSON envuelto en prosa, en cercas de código o en
nada, `contracts.parse_unconstrained` intenta las tres formas y guarda lo que no
logra leer en `unparsed`. Así, **el costo de no restringir es un conteo, no una
opinión**: si el lector se rindiera fácil, P0 fallaría por culpa del lector y no
por falta de restricción.

### 2.2 P1 — una pasada restringida

Agrega dos cosas a la vez, y por eso aísla "conformidad por prompt" como un
bloque:

- **La ontología verbalizada** se antepone al prompt (`src/iekg/verbalize.py`).
- **La salida es tipada**: el agente devuelve un `TypedExtraction` de Pydantic.

El patrón "verbalizar la ontología completa en el prompt" es el de **Text2KGBench**
(Mihindukulasooriya et al., ISWC 2023 — *sustentable*: paper revisado). Es viable
aquí solo porque la T-box es chica: 8 clases y 17 propiedades de objeto —de las
que se verbalizan las 10 no inversas, porque una inversa afirmaría el mismo hecho
dos veces— caben enteras en 2.753 caracteres. No generaliza a ontologías de
cientos de clases.

### 2.3 P2 — multi-etapa, estilo SPIRES

Parte la extracción en dos preguntas: primero **qué Temas hay**, después, para
cada Tema, **qué Conceptos se enseñan dentro de él**. Una llamada para los temas
y N llamadas para los conceptos.

El patrón es el de **SPIRES/OntoGPT** (Caufield et al., *Bioinformatics* 40(3),
2024 — *sustentable*). Los conceptos que el modelo devuelva en la primera etapa
se descartan a propósito: esa etapa existe para preguntar solo por temas, y
guardar un subproducto emborronaría lo que P2 aísla.

### 2.4 P3 — el enlace por recuperación

Idéntico a P2 salvo la etapa de enlace: en vez de comparación léxica exacta, usa
embeddings para traer los 5 candidatos más cercanos del backbone y decide con
una regla de **umbral más margen**, con abstención. Es el peldaño que ataca el
eslabón que toda la literatura declara frágil.

### 2.5 Las nueve etapas, una por una

| Etapa | Llama a un modelo | Qué hace |
|---|---|---|
| `load` | no | PDF → Markdown con Docling (consciente de layout). Un `.txt`/`.md` se lee tal cual. |
| `verbalize` | no | T-box → prompt en inglés. Es una compilación, como el Cypher. |
| `extract_free` | sí (1) | La línea base sin contrato. |
| `extract_typed` | sí (1) | La partonomía entera en una llamada tipada. |
| `extract_topics` | sí (1) | Solo los Temas. |
| `extract_concepts` | sí (N) | Una llamada por Tema, sobre la ventana del documento que ese Tema ocupa. |
| `link_lexical` | no | Control: igualdad exacta tras plegar mayúsculas, tildes y espacios. |
| `link_retrieval` | sí (1, de embeddings) | Candidatos por coseno + regla de decisión. |
| `build_abox` | no | Acuñar IRIs, validar contra las reglas, emitir `graph.cypher`. |

**Que `verbalize` y `build_abox` no llamen a ningún modelo es el punto.** Son los
dos extremos deterministas que encierran al LLM: uno le dice qué esquema debe
obedecer, el otro comprueba si lo obedeció y traduce a Cypher.

---

## 3. Consideraciones sobre los modelos

### 3.1 El catálogo: ningún experimento nombra un proveedor

`lab/models.yaml` es una especificación declarativa e `src/iekg/llm.py` su
intérprete —el mismo patrón que `schema_rules.yaml` + `rules.py`—. Un pipeline
pide `workhorse` o `reasoner`; qué modelo es eso hoy lo decide el catálogo.
Cambiar de modelo es una edición del YAML, nunca un cambio en el código del
experimento.

Los `model_id` son configuración, no secretos, y por eso están versionados. Cada
entrada **nombra** la variable de `.env` donde vive su clave; las claves nunca
están en el YAML.

### 3.2 Los cupos son el cuello de botella real, no la calidad del modelo

Esto es lo más importante que salió de la sesión sobre modelos, y es un hallazgo
sobre la **capa gratuita**, no sobre los modelos en sí:

| Lo que decía el catálogo | Lo que contestó la API |
|---|---|
| `gemini-3.7-flash`: "15 RPM / 1500 RPD" | **20 peticiones por día y por modelo** |
| Cupo de embeddings por llamada | Cuenta **cada texto**, no cada llamada |

Un pipeline escalonado cuesta 1+N llamadas por sílabo. Veinte al día son **dos
corridas**. Por eso la iteración se mudó a Groq y Gemini quedó reservado para la
corrida final medida.

Groq tiene otro techo, y es de otra naturaleza: **8.000 tokens por minuto**. Un
prompt de 3K tokens es más de un tercio del presupuesto de un minuto. Los cupos
de Groq son **por modelo, no por cuenta**: cuando `openai/gpt-oss-120b` se agotó
(198.201 de 200.000 tokens diarios), `qwen/qwen3.6-27b` seguía teniendo bolsa
propia, y eso salvó la última corrida.

**Regla que quedó:** los cupos se miden, no se leen.

### 3.3 Esperar antes de llamar, no reintentar después

`RunContext._wait_for_budget` estima los tokens de un prompt (cuatro caracteres
por token, crudo a propósito) y **duerme antes de la llamada** si no cabe en el
presupuesto del minuto.

La alternativa —reintentar tras el 429— es activamente peor contra un techo de
tokens por minuto: reintentar un prompt idéntico de 3K tokens **gasta el
presupuesto que está esperando**. Así fue como una etapa se convirtió en una
espera de veintidós minutos.

### 3.4 El fallback declarado que era inerte

`workhorse` declara `fallback_to: workhorse_alt`. Estaba escrito, documentado en
`findings/0004`... y nunca se disparaba. La causa se explica en §5.4, porque es
un problema de framework, no de modelo.

De ahí una regla que vale la pena generalizar: **un fallback declarado no es un
fallback probado**. Y su consecuencia de diseño: cada manifiesto registra qué
modelo **contestó** (`answered_by`), no cuál se pidió. Una corrida atribuida al
modelo equivocado es peor que una corrida fallida.

### 3.5 Embeddings: un SDK que devuelve menos de lo pedido

Para el enlace de P3 se usa `gemini-embedding-001`, **no** el más nuevo
`gemini-embedding-2`, por una razón medida: el segundo devuelve **un solo vector**
sin importar cuántos textos se le manden, y sin lanzar error. Aparear la
respuesta con la entrada habría desplazado todos los vectores menos el primero
sobre la etiqueta equivocada, en silencio. `EmbeddingIndex._embed` comprueba el
largo de la respuesta contra el de la entrada y falla si no coinciden.

Dos decisiones más de la etapa de embeddings:

- **Tipos de tarea asimétricos**: la mención del sílabo va como `RETRIEVAL_QUERY`
  y la etiqueta del backbone como `RETRIEVAL_DOCUMENT`. Medido el 2026-08-14,
  separa mejor que `SEMANTIC_SIMILARITY`, cuyos puntajes se apelmazan cerca de 1.
- **El índice se cachea en disco**, con clave del `model_id` y del hash de los
  textos. Las 162 etiquetas no cambian entre corridas; re-embeberlas gastaría
  cupo midiendo nada.

---

## 4. Consideraciones sobre el código

### 4.1 Fuente única, cuatro backends

Todo lo que sea esquema vive en `schema/schema_rules.yaml` y en la ontología. Con
`verbalize.py` ya son **cuatro backends del mismo intérprete**:

| Backend | Compila a |
|---|---|
| `rules.py` | validadores de Python, previos a la escritura |
| `integrity.py` | consultas Cypher de integridad |
| `tbox.py` | diagrama Mermaid (`build/tbox.md`) |
| `verbalize.py` | **prompt en inglés para el LLM** |

Que el prompt sea *generado* y no una cadena escrita a mano es lo que impide que
se desvíe del esquema contra el cual la extracción se valida después. Si el
prompt fuera literal, alguien lo editaría y la validación empezaría a rechazar lo
que el prompt pedía.

### 4.2 El backbone es de solo lectura, por construcción

En `abox.py` los nodos acuñados se escriben con `MERGE` y los del backbone solo
se citan con `MATCH`. **El archivo Cypher no puede crear una `KnowledgeUnit`
aunque la extracción lo pida.** No es una advertencia en un comentario: es la
forma del archivo emitido.

### 4.3 La acuñación es determinista

El IRI de un Tema o Concepto sale de su etiqueta canónica a través de
`contracts.slug`. La misma etiqueta acuña el mismo IRI en toda corrida, así que
re-ejecutar una extracción idéntica hace `MERGE` sobre lo mismo en vez de
duplicar.

`normalise` pliega tildes, mayúsculas y **cualquier espacio Unicode** —los
modelos emiten U+202F y parientes entre palabras—, así que la clave de
comparación no depende de la tipografía que le dio la gana usar al modelo.

### 4.4 La compuerta ciega es código

`run_pipeline.py` **se niega a correr** sobre un documento cuya anotación de
referencia no esté sellada (rellenada y con `date`). Existe `--ungated`, y queda
escrito en el manifiesto.

El razonamiento: una regla que viva solo en un documento de handoff se olvida
exactamente una vez, y una vez basta para invalidar el gold standard. Cuando la
anotación existe pero su `annotator` no es el canónico, la compuerta se abre y el
runner lo grita por consola y lo escribe en el manifiesto —un archivo que se
comporta igual que el de verdad es el más fácil de confundir con el de verdad—.

### 4.5 La segmentación por encabezados, y su asimetría deliberada

`segments.py` corta el documento por sus propios encabezados Markdown y le manda
a cada llamada por tema solo la sección que ese tema ocupa.

```
antes:  82.233 caracteres enviados (9.137 × 9 llamadas)
ahora:   1.887 caracteres para los ocho temas reales
```

P3 pasó de **más de 30 minutos sin terminar** a **101 segundos**.

Hay una asimetría que conviene entender antes de tocar esto: al modelo se le dice
que **ignore** el andamiaje del documento (números de capítulo, horas) para
nombrar los temas, y el código **usa** ese mismo andamiaje para saber dónde
empieza y termina el capítulo. No es incoherencia: es la división que sostiene
todo el diseño. El LLM genera datos; el código determinista hace lo que se puede
hacer sin adivinar.

Si ninguna sección supera el umbral de coincidencia, la ventana cae al documento
entero **y lo reporta** (`how: "full"`). Una ventana encontrada por error
escondería medio sílabo del modelo, que es peor falla que una llamada lenta.

> **Esto dejó de ser una decisión cerrada.** La ventana resolvió un atasco de
> cuota, pero **cambia qué ve el modelo**, no solo cuánto tarda, y llegó a P3 sin
> llegar a P2. Es la tensión abierta de la sesión y tiene su propia sección: §9.

### 4.6 La forma común de comparación

`contracts.Extraction` es el formato al que convergen los cuatro pipelines. Sin
él, la salida libre de P0 y la escalonada de P3 no podrían puntuarse con el mismo
código, y cualquier diferencia entre ambas sería ilegible.

El anidamiento (`list[Topic]` con `list[Concept]` dentro) es deliberado: es la
forma que tiene una partonomía. Aplanarlo para esquivar el fallo de Groq con
`$defs` habría aplanado también el dominio.

---

## 5. Consideraciones sobre PydanticAI

PydanticAI es la capa de abstracción que fija la tesis (tabla de herramientas de
R4). Estas son las cinco cosas que hubo que entender de ella, y ninguna era
visible leyendo la documentación.

### 5.1 `output_type` es la restricción, y su ausencia es la línea base

Un `Agent(model, output_type=TypedExtraction)` obliga al modelo a contestar por
tool call conforme a un JSON Schema derivado del modelo Pydantic. Eso da
**conformidad sintáctica garantizada**, no semántica: el modelo puede devolver un
Tema perfectamente tipado que sea la línea del índice del documento.

P0 no pasa `output_type` a propósito. Es la única forma de tener un piso real.

### 5.2 El perfil de esquema se elige por el prefijo del `model_id`, no por quién sirve el modelo

PydanticAI escoge el transformador de JSON Schema mirando el prefijo del
identificador. `openai/gpt-oss-120b` **servido por Groq** recibe el transformador
de OpenAI, que conserva `$defs`/`$ref` porque OpenAI los soporta —y el tool
calling de Groq no puede resolverlos—.

Medido en `findings/0004`: **0/5 sin corregirlo, 5/5 con `inline_schema_defs:
true`** en el catálogo. `llm._profile_for` parte del perfil que el proveedor
habría elegido y sobrescribe **solo** lo que el catálogo pide; reconstruirlo
desde cero perdería en silencio los valores por defecto del proveedor.

### 5.3 `thinking: false` no es un ajuste fino, es carga estructural

Con el razonamiento activado, la salida estructurada de Qwen3 tuvo éxito 2 de 5
veces; desactivado, 5 de 5, y los tokens cayeron de 1.419 a 588. El flujo de
razonamiento interfiere con la emisión del tool call. Solo la familia qwen3
permite desactivarlo en Groq.

### 5.4 El 429 disfrazado de fallo de red — la trampa que más costó

Es el hallazgo de framework más caro de la sesión, y merece explicarse entero.

`llm.py` metía el código 429 en su conjunto de estados reintentables y lo lanzaba
**desde dentro del transporte async**. `AsyncTenacityTransport` cierra la
respuesta antes de re-lanzar, así que el SDK del proveedor **nunca ve un estado
HTTP** y reporta `APIConnectionError: Connection error`.

Medido lado a lado con el mismo prompt:

| camino | error | tiempo |
|---|---|---|
| sin el transporte con reintentos | `ModelHTTPError: status_code: 429` | 0,3 s |
| con el transporte con reintentos | `APIConnectionError` | 1,6 s |

Un límite de cuota llegando como fallo de red mandó el diagnóstico por el camino
equivocado durante casi una hora.

**El 429 salió de `_RETRYABLE_STATUS`**, por dos razones independientes: miente
(§ arriba) y hace daño (reintentar consume el presupuesto que espera). Y eso
arregló de paso el fallback: al aflorar como `ModelAPIError` —que es lo que
`FallbackModel` vigila— un Gemini sin cuota ahora cae a su suplente en vez de
reintentar contra la misma pared.

**Síntoma para reconocerlo en el futuro:** si un error de conexión aparece solo
con prompts grandes y no con pequeños, es cuota.

### 5.5 `run.all_messages()[-1]` no lleva `model_name` con salida tipada

Con `output_type`, el último mensaje de la conversación es **el retorno de la
herramienta**, que no carga el nombre del modelo. Tomar `[-1]` reportaba
`answered_by` vacío en **todos** los pipelines restringidos y correcto en el
único no restringido —justo el tipo de hueco que aparece donde menos importa—.
La corrección es recorrer los mensajes hacia atrás hasta encontrar el primero que
sí lo lleve.

Se ve en los artefactos: los manifiestos de P1, P2 y P3 de la primera tanda
tienen `answered_by: []`; los posteriores, el identificador correcto.

### 5.6 `usage` es propiedad, no método

Envolver la contabilidad en un `except` amplio convirtió una vez un `TypeError`
en una corrida que reportaba cero tokens para todo (`findings/0004`). La
contabilidad de una corrida es un dato del experimento: si falla, tiene que
fallar ruidosamente.

### 5.7 La reflexión estilo OneKE es una bandera, no un quinto pipeline

`agent.output_validator` + `ModelRetry` reintenta con el error de validación
adjunto. Es el mecanismo del **Reflection Agent** de OneKE (Luo et al., WWW 2025
companion — *sustentable*), y PydanticAI ya lo implementa.

Se expuso como opción `reflect: false`, no como pipeline P4, porque es **una
política de reintento**, no una arquitectura. El validador solo comprueba lo que
la etapa de extracción realmente controla (que `label_en` no sea copia de
`label_es`); exigirle ahí que el Tema esté anclado a una KU lo haría reintentar
para siempre contra una regla que todavía no puede satisfacer.

**Esta opción no se midió en esta sesión.** Está implementada y sin datos.

---

## 6. Cómo se obtienen los resultados, y qué son

### 6.1 Los comandos

```powershell
# ver las composiciones, sin correr nada
uv run python lab/scripts/run_pipeline.py --list

# correr los cuatro sobre un sílabo
uv run python lab/scripts/run_pipeline.py all `
    --document lab/docs/syllabus/1INF33-2026-2-SILABO-BASES-DE-DATOS.PDF `
    --model reasoner

# barrer un parámetro sin tocar el YAML, guardando la corrida aparte
uv run python lab/scripts/run_pipeline.py P3 `
    --document <pdf> --option label_style=knowledge --tag knowledge

# puntuar y comparar
uv run python lab/scripts/score_run.py build/runs/* `
    --annotation lab/gold/1INF33-2026-2_annotation.claude-contraste.yaml
```

`--option` es solo para barrer. **Lo que sobreviva al barrido va al YAML**, o la
corrida que produjo un resultado deja de ser reproducible desde el repositorio.
(`label_style=knowledge` ya es el valor por defecto tras esta sesión.)

### 6.2 Qué deja una corrida en disco

Cada corrida escribe un directorio `build/runs/<pipeline>-<modelo>-<documento>/`:

| Archivo | Qué contiene |
|---|---|
| `document.md` | El texto que Docling sacó del PDF |
| `ontology_prompt.md` | La T-box verbalizada que se le mandó al modelo |
| `prompts/*.txt` | **Cada prompt exactamente como se envió**, uno por llamada |
| `raw_free_output.txt` | Solo P0: lo que contestó el modelo sin contrato |
| `extraction.json` | La extracción en la forma común de comparación |
| `linking.json` | Cada decisión de enlace **con sus candidatos y el motivo** |
| `violations.json` | Conformidad, violaciones por regla y su detalle |
| `graph.cypher` | El Cypher que **se escribiría**. Nadie lo ejecuta |
| `manifest.json` | Modelo pedido y modelo que contestó, opciones, tiempos, tokens, SHA de git, versión de Docling, y si la compuerta se saltó |
| `score.json` | Lo escribe `score_run.py` después |

Que los candidatos descartados queden en `linking.json` permite **re-barrer un
umbral sin gastar una sola llamada**. Es lo que hizo posible el análisis de §8.

### 6.3 Qué mide cada número

**Precisión y recall, en dos sabores.** El scorer (`src/iekg/scoring.py`) reporta
los dos lado a lado a propósito:

- **exacto**: igualdad tras normalizar. Es el único que significa "el pipeline
  produjo la misma etiqueta que escribió el anotador".
- **relajado**: la mitad de las palabras con contenido en común. Perdona la cola
  descriptiva que arrastra una fila de cronograma ("Modelo relacional: estructura
  y operaciones" contra "Modelo relacional").

**La distancia entre los dos es la medida de granularidad de etiqueta.** Si
relajado está muy por encima de exacto, el pipeline **está encontrando lo
correcto y nombrándolo mal**, que es otro problema con otra solución.

**Enlace.** Se juzga solo sobre los Temas que hicieron match con un Tema de la
referencia. Juzgar el enlace de un Tema que la anotación nunca listó mediría la
extracción dos veces y el enlace ninguna.

**Ruido.** Cuántos Temas extraídos coinciden con algo que la anotación puso
explícitamente **fuera de alcance** (docentes, fórmulas de nota, bibliografía).

**Conformidad.** Proporción de elementos acuñados que no rompen ninguna regla del
esquema. Es la *Ontology Conformance* de Text2KGBench, adaptada: allá se calcula
sobre triples contra una ontología, aquí sobre nodos y aristas contra las reglas
compiladas desde esa ontología. Se reporta junto a la precisión porque **la
precisión sola premia a un pipeline que extraiga tres cosas obvias**.

---

## 7. Qué dicen los números

Referencia: 10 Temas, 41 Conceptos, 8 de los 10 Temas con unidad de conocimiento
esperada. Modelo: `openai/gpt-oss-120b` salvo la última fila.

| corrida | temas P/R exacto | ~relajado | conceptos P/R exacto | ~relajado | enlace | conformidad |
|---|---|---|---|---|---|---|
| P0 sin esquema | 0,06/0,20 | 0,29/0,80 | 0,00/0,00 | 0,00/0,00 | 1/10 | 0,507 |
| P1 etiqueta vieja | 0,00/0,00 | 0,50/0,40 | 0,03/0,02 | 0,85/0,54 | 2/4 | 0,931 |
| P2 etiqueta vieja | 0,00/0,00 | 0,50/0,40 | 0,46/0,51 | 1,00/0,88 | 2/4 | 0,948 |
| P3 etiqueta vieja | 0,00/0,00 | 0,40/0,40 | 0,47/0,51 | 1,00/0,88 | 2/4 | 0,936 |
| **P1 etiqueta corregida** | **0,38/0,30** | **0,88/0,60** | 0,47/0,39 | 0,94/0,66 | 2/7 | 0,933 |
| **P3 etiqueta corregida** (qwen) | 0,33/0,30 | 0,78/0,60 | **0,60/0,56** | 1,00/0,83 | 2/7 | 0,933 |

### 7.0 Esta tabla todavía no es una escalera comparable

**Léase antes que cualquier fila.** Los dos arreglos del día —la etiqueta y la
ventana— no llegaron a todas las corridas, así que las filas no difieren en una
sola cosa, que era el requisito entero de la escalera.

| corrida guardada | `label_style` | `focus_window` | modelo | ¿sirve? |
|---|---|---|---|---|
| P0 | n/a | n/a | gpt-oss-120b | **sí**, intacta |
| P1 vieja | verbatim | n/a | gpt-oss-120b | superada por la `-knowledge` |
| P1 `-knowledge` | knowledge | n/a | gpt-oss-120b | **sí** |
| P2 vieja | verbatim | **no** | gpt-oss-120b | **no**, rehacer |
| P3 vieja | verbatim | **no** | gpt-oss-120b | **no**, rehacer |
| P3 `-knowledge` | knowledge | **sí** | **qwen3.6-27b** | modelo distinto |

`focus_window` solo existe donde existe la etapa `extract_concepts`, es decir en
P2 y P3. Que P0 y P1 no la tengan no es un hueco: P0 no verbaliza nada y P1 hace
**una sola pasada**, así que ve el documento entero por definición. Eso es lo que
P1 *es*, no algo que haya que arreglarle.

Qué comparaciones sobreviven y cuáles no:

| comparación | ¿vale? | por qué |
|---|---|---|
| P0 vs. P1 (§7.1) | **sí** | mismo modelo, y la ventana no aplica a ninguno |
| P1 vs. P2 con etiqueta vieja (§7.2) | **sí** | mismo modelo, misma etiqueta, ninguno con ventana |
| etiqueta vieja vs. corregida en P1 (§7.3) | **sí** | única variable movida |
| **P2 vs. P3** | **no** | difieren en tres cosas: enlace, ventana y modelo |
| **P3 viejo vs. P3 `-knowledge`** (§7.5) | **no** | difieren en etiqueta, ventana y modelo |

El tercer eje es el más fácil de pasar por alto: **P3 `-knowledge` corrió con
`reasoner` (Qwen) y todo lo demás con `reasoner_fallback` (gpt-oss)**, porque era
el único cupo que quedaba a esa hora. Ahí el modelo y el pipeline están
confundidos: si P3 sale mejor que P2, con estos datos **no se puede decir si fue
por la recuperación o por el modelo**.

**Faltan dos corridas, no una:** P2 y P3 con `label_style: knowledge`,
`focus_window: true` y **el mismo modelo**. Es barato: con la ventana puesta, P3
completo gastó 17.725 tokens y 101 s.

Esto es verificable sin fiarse de la memoria: el manifiesto de cada corrida
guarda su bloque de opciones, y las corridas viejas **no tienen la clave
`focus_window`**, precisamente porque la opción no existía cuando se hicieron.

### 7.1 P0 no produce jerarquía

34 elementos planos, **cero Conceptos**, conformidad **0,507**. Sin esquema el
modelo no distingue un Tema de un Concepto: devolvió una lista única donde
"Modelo Relacional", "Normalización (1ª, 2ª y 3ª Forma Normal)" y "Operadores
SQL" están todos al mismo nivel.

Es el número que faltaba para responder *"¿cuánto vale restringir?"*. La
respuesta: **restringir es lo que produce la partonomía**. Sin restricción no hay
grafo de dos niveles que enlazar, y todo lo demás del pipeline queda sin objeto.

Detalle secundario, pero limpio: P0 tampoco tradujo, porque nadie se lo pidió
(`label_en == label_es` en las 34 filas). La traducción no es un extra del prompt
tipado; es parte del contrato.

### 7.2 Escalonar mejora los Conceptos, no los Temas

Es una de las tres comparaciones que sí sobreviven a §7.0: misma etiqueta vieja,
mismo modelo, y **ninguno de los dos con ventana**, porque las dos corridas son
anteriores a que `segments.py` existiera.

| | P1 | P2 |
|---|---|---|
| conceptos extraídos | 33 | 46 |
| precisión exacta de conceptos | 0,03 | **0,46** |
| recall relajado de conceptos | 0,54 | **0,88** |
| temas | idénticos | idénticos |

**Preguntar por los Conceptos de un Tema a la vez es mejor que pedir la
partonomía entera de una vez.** Los Temas no cambian, que es lo esperado: la
etapa que los produce es la misma llamada en los dos.

El costo es real y hay que decirlo: P2 gastó **9 peticiones y 35.909 tokens**
contra 1 petición y 6.028 de P1.

### 7.3 La etiqueta valía más que el pipeline

Con el prompt original, P1/P2/P3 devolvían Temas así:

```
CAPÍTULO 1 PRESENTACIÓN DEL CURSO Y CONCEPTOS BÁSICOS (6 horas)
CAPÍTULO 3 SQL DDL (3 horas)
```

Eso **es el índice del documento**, no una unidad de conocimiento. Ninguna KU del
backbone se llama así, y el daño es doble: el enlace léxico da 0/8 y el de
embeddings da algo **peor que cero**, porque el andamiaje domina el vector y
`CAPÍTULO 2 METODOLOGÍAS DE MODELAMIENTO` cae en `KU-GIT-Modeling`, que es
*Gráficos*. P3 abstuvo en los diez, que es la respuesta correcta: evitó escribir
diez enlaces falsos.

Corregir solo la redacción del prompt, sin tocar ninguna etapa, movió los Temas
de **0,00 a 0,38** exacto y de **0,50 a 0,88** relajado.

Se arregló como **opción medible** (`label_style: knowledge | verbatim`), no como
parche silencioso, para que el antes y el después existan como dato.

### 7.4 La distancia entre exacto y relajado dice qué está roto

Es la lectura que más rendimiento da y conviene interiorizarla:

- **0,00 exacto contra 0,50 relajado** (P1/P2/P3 con etiqueta vieja) significaba
  "encontró lo correcto y lo nombró mal". El fix era del prompt.
- **0,60 exacto contra 1,00 relajado** (P3 corregido, conceptos) significa
  "encuentra todo lo que dice la referencia; en el 40% le pone otras palabras".
  Ese resto ya no es andamiaje: es granularidad genuina, y el fix no es obvio.

### 7.5 El costo, medido

| corrida | tiempo | peticiones | tokens |
|---|---|---|---|
| P0 | 29 s | 1 | 5.396 |
| P1 | 31 s | 1 | 6.056 |
| P2 | 379 s | 9 | 35.909 |
| P3 (sin ventana, gpt-oss) | 574 s | 12 | 43.035 |
| **P3 (con ventana, qwen)** | **101 s** | 11 | **17.725** |

La segmentación por encabezados bajó P3 a **una sexta parte del tiempo** y a
**menos de la mitad de los tokens**. Pero las dos últimas filas difieren en tres
cosas a la vez (§7.0), así que ni el tiempo ni el conteo de tokens son
atribuibles solo a la ventana: un modelo distinto tiene otro tokenizador y otra
verbosidad.

**Lo único limpiamente atribuible a la ventana es el texto enviado**, porque no
depende del modelo: **82.233 caracteres contra 1.887**. Todo lo demás de esta
tabla espera a las dos corridas que faltan.

---

## 8. El enlace: lo que realmente pasa, y es distinto de lo que parecía

Esta sección es el resultado más fuerte de la sesión y **corrige la lectura
superficial de la columna "enlace" de la tabla**.

Es también la única parte que **no** queda invalidada por §7.0, y conviene ver
por qué: no compara pipelines entre sí. Toma las etiquetas que P3 `-knowledge`
produjo y examina qué hizo el enlace **con esas etiquetas**. Que vinieran de Qwen
y con ventana cambia cuáles son las etiquetas, no la aritmética de los cosenos
sobre ellas. Rehacer las corridas puede mover qué Temas se extraen; lo que
difícilmente moverá es la conclusión de §8.3, porque esa es sobre la forma de la
distribución de puntajes, no sobre estas nueve filas.

### 8.1 El "2/7" no es lo que parece

Los dos aciertos de P1 y P3 corregidos **no son enlaces correctos**. Son los dos
Temas donde la anotación dice "ninguna KU encaja" (`PL/SQL` y `Triggers`) y el
pipeline se abstuvo. El scorer los cuenta como acierto, y hace bien —abstenerse
donde la referencia también se abstiene es la respuesta correcta—, pero eso
oculta el número que importa:

**De los 5 Temas juzgados donde la referencia sí espera una unidad de
conocimiento, el pipeline enlazó correctamente 0.** Se abstuvo en los cinco.

| Tema extraído | KU esperada | KU obtenida |
|---|---|---|
| Metodologías de Modelamiento | `KU-DM-Modeling` | ninguna |
| SQL DDL | `KU-DM-Querying` | ninguna |
| SQL DML | `KU-DM-Querying` | ninguna |
| Normalización | `KU-DM-Relational` | ninguna |
| Transacciones | `KU-DM-Internals` | ninguna |

Que sean abstenciones y no errores es una buena noticia —no se escribió ni un
enlace falso—, pero **la tasa de enlace útil hoy es cero**.

### 8.2 La recuperación funciona; la regla de decisión no

Aquí está lo que no se veía. Mirando los cinco candidatos que `linking.json`
guardó para cada Tema:

| Tema | KU esperada | posición en el top-5 |
|---|---|---|
| Metodologías de Modelamiento | `KU-DM-Modeling` | **2** |
| SQL DDL | `KU-DM-Querying` | **2** |
| SQL DML | `KU-DM-Querying` | **1** |
| Normalización | `KU-DM-Relational` | **1** |
| Transacciones | `KU-DM-Internals` | **4** |

**La respuesta correcta está entre los 5 candidatos en los 5 casos: recall@5 =
100%.** En dos de ellos ya está en el primer puesto.

Eso reencuadra el problema entero. **No es un problema de recuperación, es un
problema de decisión.** El recuperador ya trae la respuesta; lo que falla es el
mecanismo que elige entre lo que trajo.

### 8.3 Por qué falla la regla, con los números

Los márgenes observados entre el primer y el segundo candidato, en los nueve
Temas:

```
Conceptos Básicos    0,0273      SQL DML          0,0044
Metodologías         0,0054      Normalización    0,0056
SQL DDL              0,0011      PL/SQL           0,0014
Transacciones        0,0046      Triggers         0,0025
```

**Ninguno alcanza el margen configurado de 0,03.** El máximo observado es 0,0273.
Con esta calibración, la regla abstiene el 100% de las veces sobre este
documento: es degenerada, y el umbral absoluto de 0,62 no está haciendo nada
porque todos los primeros candidatos lo superan.

Aflojar el margen tampoco sirve, y esto sí es concluyente. Con margen 0,005 se
aceptarían tres Temas: `Conceptos Básicos → KU-SF-Foundations` (mal),
`Metodologías → KU-FPL-Methodologies` (mal) y `Normalización → KU-DM-Relational`
(bien). **Un acierto y dos errores.** Barrer el umbral no arregla esto.

Peor aún para la idea de un umbral absoluto: los dos Temas que la referencia
declara **no cubiertos por CS2023** puntúan alto. `PL/SQL` saca 0,7084 con
`KU-FPL-Logic`, **más que el 0,6792 con que `Normalización` acierta**. No existe
un corte absoluto que separe "debe enlazar" de "no debe enlazar".

### 8.4 Qué le hizo la limpieza de etiquetas al enlace

Corregir la etiqueta arregló la extracción y **le quitó contexto al enlace**.
`Triggers` a secas no dice "base de datos", y cae en `KU-SEC-Coding` (seguridad).
`Conceptos Básicos` no dice nada en absoluto y cae en `KU-SF-Foundations`.

Es una tensión real entre dos etapas, no un defecto de una: **la etiqueta corta
es mejor para nombrar y peor para buscar.**

### 8.5 La hipótesis que sigue, y por qué es barata

La consulta del enlace no debe ser la etiqueta desnuda, sino la etiqueta **con su
contexto**: el nombre del curso, o el propio Tema acompañado de los Conceptos que
ya se extrajeron. Los Conceptos ya están, salen bien (0,60 exacto) y no cuestan
ni una llamada más. Es un cambio de una línea en `pipeline._link_query`.

La alternativa complementaria, ahora justificada por §8.2: **un re-ranqueador
sobre los 5 candidatos**. Como el recall@5 es 100%, un segundo paso que elija
entre cinco opciones tiene todo el techo disponible. Y encaja con la arquitectura
sin romperla: sería una llamada al LLM que **elige entre un conjunto cerrado**,
no una que inventa un identificador.

---

## 9. La ventana de segmentación: la decisión que quedó abierta

Es la tensión nueva de la sesión, y tiene dos partes que hay que resolver **en
orden**: primero igualar las corridas, después decidir si la ventana se queda.

### 9.1 Primero igualar, y recién entonces discutir

Mientras P2 corra sin ventana y P3 con ventana, la pregunta "¿la ventana mejora
o empeora la extracción?" no tiene datos, y la pregunta "¿escalonar con
recuperación mejora?" tampoco, porque las dos comparten las mismas filas sucias.

**Paso cero, y va antes que cualquier otra cosa:** rehacer P2 y P3 con
`label_style: knowledge`, `focus_window: true` y **el mismo modelo**. Eso vuelve
la tabla de §7 una escalera de verdad. Es también la corrida más barata que queda
por hacer.

```powershell
uv run python lab/scripts/run_pipeline.py P2 P3 `
    --document lab/docs/syllabus/1INF33-2026-2-SILABO-BASES-DE-DATOS.PDF `
    --model reasoner --tag v2
```

Solo después de eso tiene sentido el barrido de la propia ventana:

```powershell
uv run python lab/scripts/run_pipeline.py P2 P3 `
    --document <pdf> --model reasoner `
    --option focus_window=false --tag sin-ventana
```

Una nota que hace esta ablación viable hoy y no lo era ayer: **el atasco de 22
minutos ya no puede repetirse.** Aquello fue el transporte reintentando un prompt
idéntico contra un techo de tokens por minuto (§5.4). Con `_wait_for_budget` en
su sitio, la corrida sin ventana **espera a propósito** en vez de estrellarse:
son unos 27.600 tokens contra 8.000 por minuto, es decir del orden de cuatro o
cinco minutos de espera declarada. Lenta, pero acotada y sin sorpresas.

### 9.2 El argumento a favor de mantenerla

- **Resolvió un problema real y medido.** 82.233 → 1.887 caracteres enviados; P3
  de más de 30 minutos sin terminar a 101 s.
- **Hace estructural lo que antes era una instrucción.** El prompt le pide al
  modelo "ignora lo que la fuente diga de otros temas". Con la ventana, el modelo
  directamente no los tiene delante. Confiar en la geometría del prompt es más
  fuerte que confiar en la obediencia del modelo.
- **Es determinista y auditable.** Cada llamada registra `how: section | full` y
  el encabezado del que salió la ventana. No hay nada que adivinar después.

### 9.3 El argumento en contra, y no es débil

**a) Es una variable de extracción disfrazada de optimización.** Cambia qué ve el
modelo. Un P2 con ventana y uno sin ventana son dos mediciones distintas, no la
misma medición más rápida. Presentarla como mejora de rendimiento en la tesis
sería inexacto.

**b) Devuelve al pipeline la dependencia del andamiaje que el prompt le pide
ignorar.** La asimetría de §4.5 es defendible, pero tiene un costo: **el
comportamiento del pipeline pasa a depender de la calidad del layout del PDF**.
Si un sílabo no trae encabezados limpios, o si Docling no los emite como tales,
la ventana cae a `full` y esa corrida se comporta como la vieja — sin avisar más
que en un campo del registro. Los dos sílabos que faltan son exactamente la
prueba de esto, y todavía no se ha hecho.

**c) Puede recortar información legítima.** Un Concepto que se enseña en el
capítulo 5 pero se define en la sumilla o en el capítulo 1 ya no está en la
ventana. Cortar sube la precisión aparente y puede bajar el recall real, y con
un solo documento eso no se ve.

**d) El emparejamiento Tema → sección usa el mismo matcher frágil.**
`segments.window` decide por solapamiento de palabras con umbral 0,5, que es el
mismo mecanismo que en §10.1(c) empareja `SQL DML` con `SQL DDL`. **Un Tema mal
emparejado recibe la sección equivocada**, y eso es peor que mandarle el
documento entero: el modelo contestaría con seguridad sobre el capítulo que no
era. En esta corrida los nueve Temas encontraron sección (`9 windowed`), así que
el fallo no se manifestó — pero no se manifestó, no es que no pueda.

**e) Y la más incómoda: la ventana ya no es donde está el costo.** Medido sobre
esta corrida, un prompt de la etapa de conceptos se reparte así:

| parte | caracteres | del prompt |
|---|---|---|
| ontología verbalizada | 2.753 | **~84%** |
| texto de la tarea | ~400 | ~12% |
| **ventana del documento** | **142–479** | **~4–14%** |

Antes de la ventana, el documento era el 77% del prompt y cortarlo era
evidentemente lo correcto. **Después de la ventana, el término dominante es la
T-box, repetida entera en cada una de las N llamadas.** Si lo que se busca es
holgura de cuota, el siguiente recorte barato ya no es el documento: es no
reenviar la ontología completa en la llamada de conceptos, que solo necesita la
clase `Concept` y las reglas de alcance.

### 9.4 Recomendación

**Mantener la ventana, pero dejar de tratarla como un detalle de rendimiento.**
Tres cosas concretas, en orden de retorno:

1. **Medirla.** Correr la ablación de §9.1 sobre P2 y P3. Si sin ventana el
   recall de Conceptos sube, el punto (c) es real y la ventana está costando
   cobertura; si no se mueve, queda zanjado y deja de ser una duda.
2. **Endurecer el emparejamiento** Tema → sección antes de confiar en él con más
   documentos: un piso de palabras con contenido, no solo un porcentaje. Es el
   mismo arreglo que necesita el scorer (§10.1c), así que se hace una vez.
3. **Adelgazar la ontología en la llamada de conceptos**, que es donde está el
   84% del prompt. Da más holgura que cualquier ajuste adicional de la ventana.

**Volver atrás del todo no.** Sin ventana, la etapa de conceptos vuelve a mandar
el sílabo entero N veces, y eso no es solo lento: contra un techo de tokens por
minuto es la diferencia entre una corrida y una tarde. La ablación es para tener
el dato, no para volver a ese modo por defecto.

Lo que sí es innegociable: **`focus_window` es una variable declarada del
experimento y tiene que aparecer en cualquier tabla de resultados**, igual que el
modelo y `label_style`. La razón de que esta tensión exista es que durante unas
horas no apareció.

---

## 10. Tensiones e insights: lo que hay que decidir

### 10.1 Sobre la implementación

**La primera de todas está en §9** —qué hacer con la ventana de segmentación— y
por eso tiene sección propia. Lo que sigue es el resto.

**a) La conformidad, como está definida, premia extraer más.**
Es `1 − elementos_infractores / (nodos + aristas)`. Hoy la única regla que se
viola es `topic-in-ku` —un Tema sin unidad de conocimiento—, así que la fórmula
se reduce a `1 − temas_sin_enlazar / (nodos + aristas)`. Un pipeline que emita
más Conceptos sube su conformidad **sin haber enlazado ni un Tema más**. P2
"gana" a P1 en conformidad (0,948 contra 0,931) por eso, no por ser más conforme.
Hay que decidir: o se normaliza por clase de elemento, o se reporta la
conformidad por regla y no agregada. **Tal como está, no es comparable entre
pipelines de distinto tamaño.**

**b) Hay duplicados dentro de un mismo documento, no solo entre documentos.**
P3 corregido devolvió **dos Temas llamados "Conceptos Básicos"**, con etiquetas
inglesas distintas: `Database Fundamentals` y `Basic Concepts`. Como el IRI se
acuña desde `label_en`, son **dos nodos distintos para el mismo tema**, y las dos
llamadas de conceptos recibieron la misma ventana del documento. La deduplicación
estaba anotada como problema de la capa institucional entre sílabos; es también
un problema **dentro** de un sílabo. Barato de mitigar: detectar `label_es`
repetido antes de acuñar.

**c) El scorer tiene dos defectos medibles y visibles en los artefactos.**
El matcher relajado emparejó `SQL DML` con el Tema de referencia
`SQL Data Definition Language (DDL)` —comparten una sola palabra, "SQL", y con
etiquetas de dos palabras eso ya es el 50%—. Aquí no cambió el resultado porque
ambos esperaban `KU-DM-Querying`, pero **puede juzgar un enlace contra la KU
equivocada**. Y el detector de ruido marcó `Datos, Información y Bases de Datos`
como coincidencia con la entrada bibliográfica `Date, C.J. — Introducción a los
Sistemas de Bases de Datos`. **Las etiquetas cortas son las que rompen el
umbral de solapamiento**; hace falta un piso de palabras, o penalizar la
diferencia de longitud.

**d) La métrica de enlace mezcla dos cosas distintas.**
`accuracy = correctos / juzgados` suma en el mismo cajón "enlazó bien" y "se
abstuvo donde había que abstenerse". Son dos capacidades diferentes y hay que
reportarlas por separado, o la tabla seguirá diciendo 2/7 cuando el número
relevante es 0/5.

**e) Falta el paso de carga.** Los pipelines emiten `graph.cypher` y nadie lo
ejecuta. La base sigue teniendo solo el backbone: 17 KA + 162 KU, cero `Topic`.
Es deliberado, pero ya no es lo que bloquea nada más.

**f) Hay dos archivos describiendo la capa de referencia.** El backbone
monolingüe y `ontology/backbone_cs2023_es.ttl`. Son dos fuentes de verdad, justo
lo que el proyecto prohíbe en todo lo demás. Deben colapsar en uno.

**g) La opción `reflect` está implementada y sin medir.** También `scope_iris`.
Existen como opciones para poder medirlas; siguen sin dato.

### 10.2 Sobre la tesis

**a) El criterio de aceptación de R4 necesita una definición operativa.**
"Verificación manual de la precisión de entidades extraídas ≥ 75%" no dice sobre
qué se calcula. Con este sílabo, la precisión exacta de Conceptos es 0,60 y la
relajada 1,00; el criterio se cumple o no según cuál se elija, y **esa elección
hay que declararla antes de medir**, no después de ver los números. Lo mismo con
la unidad: ¿entidades son Temas, Conceptos, o ambos?

**b) La abstención necesita entrar en la tesis como resultado, no como falla.**
Hoy el sistema no escribe enlaces falsos porque prefiere no escribir ninguno.
Eso es defendible ante un jurado —y es la salida a revisión humana que el diseño
ya anticipaba—, pero **solo si está declarada como decisión de diseño con su
métrica propia**: cobertura de enlace, tasa de abstención, y precisión sobre lo
no abstenido. Si se presenta como "el enlace funciona", el 0/5 de §8.1 lo
desmiente en la defensa.

**c) El gold ciego se levanta sobre otro sílabo, y eso ya es decisión tomada.**
1INF33 queda como sílabo de desarrollo —cumplió ese papel y lo hizo bien—. El
gold va sobre uno de los dos sílabos adicionales que hacían falta igual (uno muy
teórico, uno muy práctico). Convierte una pérdida en una decisión de diseño.

**d) La tabla de R4 fija el LLM como "GPT-4o/Gemini", y la medición dice otra
cosa.** No sobre calidad: sobre **viabilidad**. Gemini da 20 peticiones al día en
capa gratuita, que es menos de una corrida P2 más una P3. La arquitectura es
agnóstica al modelo, así que esto no la toca; pero la tabla de la tesis sí hay
que revisarla, y el argumento correcto es de cupo, no de capacidad. *(Nota gris:
los cupos medidos son de la capa gratuita a agosto de 2026 y pueden cambiar sin
aviso; lo sustentable en la tesis es la arquitectura agnóstica, no el número.)*

**e) Un solo documento no permite concluir nada, y hay que decirlo así.**
Todo lo de §7 y §8 sale de **un** sílabo, contra **una** anotación de contraste,
con **dos** modelos. Sirve para decidir qué probar; no sirve como resultado. Con
los tres sílabos y el gold real, las mismas mediciones sí son citables.

**f) La cola descriptiva de la etiqueta sigue sin decidirse.** "Layer model:
encapsulation, protocols, data units" es fiel a la fila del cronograma que la
originó. Normalizarla o no, y si eso es tarea del prompt o de código
determinista, sigue abierto —y §8.4 acaba de mostrar que la decisión tiene un
efecto medible sobre el enlace, en dirección contraria al efecto que tiene sobre
la extracción—.

---

## 11. Estado verificable al cerrar

```
uv run pytest tests/ -q                      -> 77 passed
uv run python lab/scripts/check_integrity.py -> Integrity satisfied.
```

77 pruebas: 21 de pipeline, 17 de integridad, 13 de scoring, 10 del catálogo de
modelos, 8 de la anotación, 8 de la T-box.

Siete directorios en `build/runs/`, seis con corrida completa y uno truncado:
`P3-reasoner_fallback-...-knowledge` no tiene `manifest.json` ni
`extraction.json`, y su `prompts/` contiene **un solo archivo**,
`extract_topics.txt`. Es decir: se cayó en la **primera** llamada al modelo, con
el cupo diario de `gpt-oss-120b` agotado, antes de recibir una sola respuesta. El
prompt que quedó escrito es toda la evidencia que produjo, y es la razón de que
la corrida se relanzara cuarenta segundos después contra `reasoner` (Qwen). El
historial completo de qué modelo corrió cada cosa está en §11.1.

### 11.1 Qué modelo corrió cada intento

Los siete directorios salen de **cuatro invocaciones** del runner, todas sobre el
mismo sílabo y en la madrugada del 15:

| hora | invocación | modelo pedido | modelo que contestó | resultado |
|---|---|---|---|---|
| 00:37–00:54 | `all` | `reasoner_fallback` = `openai/gpt-oss-120b` | el mismo | P0, P1, P2 y P3 completos |
| 00:54–00:55 | `P1 --tag knowledge` | `reasoner_fallback` | el mismo | completa |
| 02:06 | `P3 --tag knowledge` | `reasoner_fallback` | **ninguno** | **truncada**: cupo diario agotado |
| 02:07–02:08 | `P3 --tag knowledge` | `reasoner` = `qwen/qwen3.6-27b` | el mismo | completa |

**Ningún `FallbackModel` intervino en ninguna corrida**, y eso es comprobable sin
fiarse del registro: en `lab/models.yaml` la única entrada que declara
`fallback_to` es `workhorse`, y `workhorse` no corrió ninguna de estas. Los
`answered_by: []` de tres manifiestos son el defecto de §5.5, no un cambio de
modelo silencioso.

**Un quinto modelo sí participó, y es fácil de olvidar porque no extrae nada:**
`gemini-embedding-001`, en la etapa `link_retrieval` de las dos corridas de P3.
Dejó dos índices en `build/embeddings/`, uno por idioma —162 vectores de 3.072
dimensiones cada uno—. El de español lo construyó P3 a las 00:54, que es por qué
esa etapa tardó 119 s; P3 `-knowledge` lo leyó de disco a las 02:07 y tardó
**2,55 s**. El caché es la diferencia entera.

---

## 12. Lo siguiente, en orden

0. **Rehacer P2 y P3** con `label_style: knowledge`, `focus_window: true` y el
   mismo modelo (§7.0 y §9.1). Va primero porque hasta que existan, la tabla de
   §7 no es una escalera comparable y cualquier conclusión sobre "si escalonar
   mejora" o "si la recuperación mejora" está confundida con otras dos variables.
   Es la corrida más barata que queda por hacer.
1. **Enlace con contexto** (§8.5): cambiar la consulta y, si hace falta,
   re-ranquear los 5 candidatos. Es la mejora de mayor retorno y la más barata.
   Sin ella, P3 no supera a P2 en nada visible. Va **después** del punto 0, o se
   añade una tercera variable a una comparación que ya tiene dos sueltas.
2. **La ablación de la ventana** (§9.1): P2 y P3 con `focus_window=false`, para
   decidir con datos si se queda o no. Puede ir en paralelo al punto 1 porque
   toca otra etapa, pero nunca en la misma corrida.
3. **Los dos sílabos que faltan**, uno teórico y uno práctico. Sobre uno de
   ellos, **la anotación ciega de verdad**. Son también la única forma de probar
   el punto (b) de §9.3: un sílabo con otro layout.
4. **Arreglar las tres cosas del scorer** de §10.1(c) y (d) antes de volver a
   medir, o los números siguientes heredarán los mismos sesgos. El mismo arreglo
   endurece el emparejamiento Tema → sección de §9.3(d).
5. **El paso de carga** a Neo4j.
6. **Colapsar los dos backbones en uno.**
7. Escribir `findings/0006` con lo de §8, que es lo único de aquí que ya está
   suficientemente medido para ser registro citable.
