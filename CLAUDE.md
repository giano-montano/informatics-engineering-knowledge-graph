# CLAUDE.md

Instrucciones para sesiones de Claude Code en este repositorio.

**Documento vivo**, a diferencia de `lab/findings/` y `lab/docs/`, que son
registros congelados. Si algo aquí deja de ser cierto, se corrige aquí mismo.

---

## 1. Con quién trabajas y cómo

Giano, tesista de Ingeniería Informática (PUCP). Construye un sistema de gestión
de conocimiento basado en grafos para el currículo de la carrera. Está
aprendiendo Neo4j y Cypher sobre la marcha: no asumas fluidez, pero tampoco
expliques de menos.

Reglas de trabajo que él fijó:

- **Empezar por los huecos y los supuestos débiles. Sin halagos.**
- Proponer opciones **con recomendación explícita; él decide.** Antes de la
  pregunta, una explicación en prosa llana de cada opción y su consecuencia.
- Distinguir siempre lo que sirve para **decidir qué probar** (fuente gris:
  repos nuevos, foros, blogs, preprints) de lo que es **sustentable en la tesis**
  (estándar, paper revisado, documentación oficial). Marcar lo gris de forma
  explícita, fuente por fuente.
- Cuando una prueba **contradiga una decisión de diseño previa**, decírselo de
  frente para que quede registrado.
- **Verificar versiones y estado del arte antes de recomendar.** No de memoria.
- **Leer `docs/tesis.md` antes de señalar algo como hueco de diseño.** Muchas
  decisiones ya están tomadas y argumentadas ahí; tratarlas como omisiones le
  hace repetir trabajo. Ya pasó una vez.

Esto es un **laboratorio**, separado del trabajo formal de tesis: se experimenta,
se rompe y se rehace. Nada de ADRs formales aquí.

## 2. Antes de opinar, leer

| Archivo | Por qué |
|---|---|
| `docs/tesis.md` | Las decisiones de diseño ya tomadas. Obligatorio antes de llamar "hueco" a algo. |
| `docs/estandares-de-codigo.md` | Política de idioma, nomenclatura, escritura en la base, pruebas. **No dupliques sus reglas: síguelas.** |
| `internal-notes/2026-08-15-handoff.md` | **El más reciente.** Los pipelines corriendo, y cinco decisiones que la medición falsó. Ignorado por git. |
| `internal-notes/2026-08-14-handoff.md` | Arranque de O2: catálogo de modelos y especificación de los pipelines. Ignorado por git. |
| `internal-notes/2026-07-31-handoff.md` | Estado al cerrar julio, con la tabla larga de decisiones. Ignorado por git. |
| `lab/findings/000{1,2,3}-*.md` | Por qué solo unicidad, por qué no SHACL, arquitectura de ingesta contra la literatura. |
| `lab/findings/0004-*.md` | Qué modelos soportan salida tipada y con qué correcciones. |
| `lab/findings/0005-*.md` | **El más reciente.** La escalera de pipelines y tres decisiones previas que la medición falsó. |
| `lab/docs/2026-08-07-*.md` | El modelo de datos vigente y qué se ve (y qué no) dentro de Neo4j. |
| `lab/docs/2026-08-15-pipelines-*.md` | Los cuatro pipelines explicados de punta a punta: etapas, modelos, PydanticAI, cómo se puntúa y qué dijeron los números. |

## 3. El proyecto en una pantalla

Resultados de tesis: **R1** ontología OWL validada · **R2** backbone de 17 áreas
y 162 unidades de CS2023 en Turtle · **R3** documentación del módulo de KG ·
**R4** módulo de KG y pipeline de ingesta (*lo que se prototipa aquí*) · **R5**
documentación de navegación · **R6** prototipo de navegación.

Pipeline previsto (*Ontology Population*):

```
PDF -> Docling (consciente de layout)
    -> extracción con LLM de salida estructurada (Pydantic)
    -> validación contra la ontología
    -> enlace de entidades (mención -> candidatos -> desambiguación) vs. backbone
    -> fusión de conocimiento
    -> Cypher MERGE parametrizado, generado de forma determinista
    -> consultas de integridad
```

**El LLM nunca escribe en la base.** Genera datos; el Cypher lo construye código
determinista. Es una respuesta estructural al modo de fallo que declara toda la
literatura revisada, y es contribución nombrable de la tesis. Ver `findings/0003`.

## 4. Mapa del repositorio

```
docs/tesis.md                 El documento de tesis.
docs/estandares-de-codigo.md  Convenciones. Vinculantes.
ontology/*.ttl                R1 (esquema OWL) y R2 (backbone CS2023).
schema/schema_rules.yaml      Especificación declarativa. FUENTE ÚNICA.
lab/models.yaml               Catálogo de modelos y de embeddings.
lab/pipelines.yaml            Composición de los cuatro pipelines por etapas.
src/iekg/rules.py             Intérprete del YAML + validadores pre-escritura.
src/iekg/projector.py         RDF -> LPG con MERGE idempotente.
src/iekg/integrity.py         Reglas -> Cypher. Emite, no ejecuta.
src/iekg/tbox.py              Lector de la T-box OWL -> diagrama Mermaid.
src/iekg/verbalize.py         T-box -> prompt en inglés. Tercer backend.
src/iekg/llm.py               Catálogo -> modelo PydanticAI configurado.
src/iekg/pipeline.py          Intérprete de pipelines.yaml + las etapas.
src/iekg/contracts.py         Contratos Pydantic + forma común de comparación.
src/iekg/linking.py           Enlace léxico y por recuperación (embeddings).
src/iekg/abox.py              Extracción -> nodos/aristas -> Cypher. Emite.
src/iekg/gold.py              Anotación ciega de referencia: forma y validación.
src/iekg/db.py                Conexión al driver.
lab/scripts/                  Scripts ejecutables del laboratorio.
lab/gold/                     Anotación de referencia + catálogo del backbone.
lab/cypher/tour.cypher        Consultas comentadas para el Browser. Español.
lab/findings/                 Hallazgos numerados y fechados. CONGELADOS.
lab/docs/                     Registros de aprendizaje fechados. CONGELADOS.
tests/                        Pruebas negativas de integridad, T-box y pipeline.
build/                        Artefactos generados desde schema/. Versionados.
build/runs/                   Salida de cada corrida de pipeline.
internal-notes/               Notas privadas. Ignorado por git.
```

**Cuatro backends, un mismo patrón.** Todo lo que interpreta una especificación
declarativa vive igual: `rules.py` compila a validadores, `integrity.py` a
Cypher, `tbox.py` a diagrama, `verbalize.py` a prompt. Los cuatro leen
`schema_rules.yaml` y la ontología, así que un prompt no puede desviarse del
esquema contra el que después se valida la extracción.

**Regla de artefactos:** `build/` se genera, nunca se edita a mano; y se versiona
a propósito, porque los `.cypher` y el `tbox.md` son evidencia citable de cómo se
validó el grafo.

**Regla de fuente única:** todo lo que sea esquema —clases, propiedades,
inversas, reglas— vive en `schema/schema_rules.yaml`. Si te dan ganas de
codificar una etiqueta o una regla en Python, es señal de que falta una entrada
en el YAML. La restricción del asesor es explícita: **especificación declarativa
más intérprete pequeño; nada hardcodeado, nada de ORM.**

## 5. Comandos

Desde la raíz, en PowerShell:

```powershell
docker compose up -d
uv sync
uv run python lab/scripts/check_stack.py            # driver + parseo Turtle
uv run python lab/scripts/load_backbone.py --reset  # proyectar y verificar
uv run python lab/scripts/check_integrity.py        # emitir Cypher y ejecutar
uv run python lab/scripts/emit_tbox_diagram.py      # regenerar build/tbox.md
uv run pytest tests/ -q

# Anotación ciega de referencia (bloquea las corridas sobre ese sílabo)
uv run python lab/scripts/emit_annotation_template.py <pdf>
uv run python lab/scripts/emit_annotation_template.py <pdf> --check

# Pipelines de ingesta. Emiten a build/runs/, NO escriben en Neo4j.
uv run python lab/scripts/run_pipeline.py --list
uv run python lab/scripts/run_pipeline.py all --document <pdf> --model reasoner_fallback
uv run python lab/scripts/run_pipeline.py P3 --document <pdf> --option threshold=0.65
docker compose exec -T neo4j bash -s < lab/scripts/probe_constraints.sh
start http://localhost:7474                         # Browser
```

Esperado: `Stack verified.` · `Backbone projected and verified.` ·
`Integrity satisfied.`

La contraseña vive en `.env`, ignorado por git. Si falta: copiar `.env.example`,
poner una, `docker compose down -v` y volver a levantar.

## 6. Decisiones tomadas — no relitigar

| Decisión | Argumento |
|---|---|
| Neo4j 5.26 LTS, no la versión vigente | soporte hasta jun 2028; comentario en `docker-compose.yml` |
| Enterprise en desarrollo, Community al desplegar | **nada puede depender de multi-base ni de Enterprise** |
| Solo unicidad como restricción nativa | `findings/0001`: es la única que sobrevive a Community |
| YAML propio en vez de SHACL | `findings/0002`: SHACL no emite Cypher ni lee LPG |
| El intérprete **emite** artefactos, no ejecuta | dos backends: validadores Python y Cypher |
| Aciclicidad solo por consulta de integridad | no hay verificación previa por arista |
| Las 3 subpropiedades de `isPartOf` colapsan en `PART_OF` | las etiquetas de los extremos ya fijan el nivel |
| Inversas: una sola dirección materializada | recorrer al revés cuesta lo mismo |
| La clausura transitiva no se materializa | una arista inferida sería indistinguible de una afirmada |
| Subclase OWL -> etiqueta adicional | `(:KnowledgeElement:KnowledgeArea)` |
| La T-box no se materializa en Neo4j | se emite a `build/tbox.md`; la base queda con datos puros |
| Los `Topic` los **acuña el pipeline**, no el backbone | ya estaba en la tesis |
| Código en inglés, prosa en español | `docs/estandares-de-codigo.md` |
| Commits y ramas en inglés, asunto en imperativo | idem |
| Un pipeline es configuración, no un módulo | `lab/pipelines.yaml` + intérprete; evita cuatro copias divergentes |
| Los pipelines **emiten** a `build/runs/`, no cargan | misma doctrina que `integrity.py`; dos corridas se diffean |
| La compuerta ciega es **código**, no prosa | `run_pipeline.py` se niega sin anotación sellada; `--ungated` queda en el manifiesto |
| El enlace decide por umbral **y margen**, con abstención | `findings/0005`: el coseno absoluto no separa acierto de casi-acierto |
| Se registra qué modelo **contestó**, no cuál se pidió | un `FallbackModel` conmuta en silencio; ver `findings/0005` |
| Se itera en Groq; Gemini es para la corrida final | `findings/0005`: 20 peticiones por día en capa gratuita |

## 7. Estado al 2026-08-15 (cierre del día)

**Los cuatro pipelines corren sobre el sílabo real de punta a punta.** Ver el
handoff del 2026-08-15 para los números, los cupos gastados y lo que sigue.
**77 pruebas.**

Tres cosas que cambian el plan y no son negociables:

- **La anotación ciega de 1INF33 ya no es posible**: se vieron extracciones de
  ese sílabo. El gold debe levantarse sobre otro documento. 1INF33 queda como
  sílabo de desarrollo.
- **Los cupos gratuitos son el cuello de botella real**, no la calidad del
  modelo. Gemini da 20 peticiones al día por modelo; Groq, 200K tokens al día
  **por modelo** (bolsas separadas: cuando se agota uno, el otro sigue).
- **El enlace de entidades sigue sin resolverse.** Con etiquetas limpias, P3
  abstiene en todos los temas porque el margen entre el primer y el segundo
  candidato es de milésimas. La hipótesis a probar es dar contexto a la
  consulta, no la etiqueta desnuda.

### Estado anterior, al 2026-08-14

Backbone cargado y verificado: 17 `KnowledgeArea` + 162 `KnowledgeUnit` + 1
`LearningResource`, 4 restricciones de unicidad sobre `iri`, **11 reglas de
esquema**. **64 pruebas** (17 de integridad + 8 de T-box + 10 del catálogo +
8 de la anotación + 21 del pipeline).

**Los cuatro pipelines existen y corren de punta a punta.** Escalera declarada
en `lab/pipelines.yaml`, intérprete en `src/iekg/pipeline.py`, verificada sobre
texto **inventado** (nunca el sílabo real). Cifras y correcciones en
`findings/0005`.

Huecos conocidos, para no confundirlos con errores:

- **No hay `Topic` ni `Concept` todavía en la base**: los acuña la ingesta, y
  la ingesta todavía no ha cargado nada. El backbone llega hasta las KU, por eso
  la jerarquía se ve con dos niveles y no cuatro.
- **No hay `Course` ni `ResourceType`**: entran con la capa institucional.
- **No hay ninguna arista `HAS_PREREQUISITE`**: CS2023 no las da a nivel de KU y
  el modelo las define entre `Concept`. El tipo y su regla de aciclicidad ya
  existen; las consultas de prerrequisitos hoy devolverían vacío.
- **Falta el paso de carga.** Los pipelines emiten `graph.cypher`; nadie lo
  ejecuta todavía. Es deliberado y es lo siguiente después de la anotación.
- **Falta el scorer.** `gold.py` lee y valida la anotación; comparar una
  extracción contra ella todavía no está escrito.

## 8. Lo siguiente: sellar la anotación ciega

**Es el camino crítico, y ahora es una compuerta en código.** Mientras
`lab/gold/1INF33-2026-2.annotation.yaml` no esté rellenado y sellado (con
`date`), `run_pipeline.py` **se niega** a correr sobre ese sílabo. La plantilla
está generada y el catálogo del backbone también, en `lab/gold/`.

Después de sellarla, por orden: correr la matriz, escribir el scorer contra la
anotación, y recién entonces el paso de carga a Neo4j.

Lo difícil, todavía abierto (ver `findings/0003`, `findings/0005` y
`lab/docs/research_pipelines.md`):

1. **Qué significa "coincide"** en el enlace de entidades. Ya no está en blanco:
   hay dos mecanismos implementados (léxico como control, recuperación por
   embeddings) y una regla de decisión medida —umbral **más margen** sobre el
   segundo candidato—. Lo que falta es calibrarla contra la anotación.
2. **Deduplicación dentro de la capa institucional.** El backbone es estático,
   pero los `Topic` y `Concept` de un sílabo deben reconciliarse contra los de
   otro, y ese conjunto crece con cada ingesta. La opción `scope_iris` decide si
   dos sílabos que enseñan "Normalization" se funden o no; está sin decidir,
   como opción, para poder medirla.
3. **Umbral de decisión y salida a revisión humana** cuando nada lo supera. La
   abstención ya se produce sola y queda en `linking.json` con sus candidatos.
4. **La etiqueta de un Tema sale con su cola descriptiva** ("Layer model:
   encapsulation, protocols, data units"), fiel a la fila del cronograma que la
   originó. Decidir si se normaliza, y si eso es tarea del prompt o de código
   determinista. Una etiqueta larga desplaza el coseno, así que afecta al enlace.

Nota gris pendiente: la tabla de R4 en la tesis fija el LLM como "GPT-4o/Gemini".
Conviene revisar esa elección antes de implementar. No afecta a la arquitectura,
que es agnóstica al modelo, pero sí a los resultados.

## 9. Trampas ya encontradas — no repetirlas

- **`CREATE CONSTRAINT ... IF NOT EXISTS` compara el esquema, no el nombre.** Al
  renombrar restricciones Neo4j ve una equivalente y no crea nada: la base se
  queda con el nombre viejo mientras el artefacto generado dice otro. Hay que
  `DROP CONSTRAINT` primero.
- **Cypher 5 no tiene función de lista a cadena** y `toString()` rechaza listas.
  Se resuelve con `reduce(...)`, sin depender de APOC.
- **Las etiquetas y tipos de relación no admiten parámetros en Cypher.** Hay que
  interpolarlos, y validarlos antes contra la especificación.
- **`OPTIONAL MATCH` es imprescindible** en la regla de cardinalidad: con `MATCH`
  normal, un nodo con cero destinos desaparece del resultado y la violación pasa
  inadvertida.
- **Encadenar comandos con saltos de línea en PowerShell no corta ante un fallo.**
  Un borrado encadenado detrás de un `git mv` fallido se ejecutó igual y borró
  dos `.ttl` sin versionar. Usar `&&`, y **verificar siempre antes de borrar**.
- **Que una consulta de validación no encuentre nada en datos limpios no prueba
  nada.** Toda regla de integridad necesita su prueba negativa: se inyecta la
  violación a propósito, dentro de una transacción que se revierte.
- **Un límite de cuota puede llegar disfrazado de fallo de red.** Meter 429 en
  la política de reintentos del transporte hacía que `AsyncTenacityTransport`
  cerrara la respuesta antes de re-lanzar, y el SDK reportaba
  `APIConnectionError`. Si un error de conexión aparece solo con prompts
  grandes, es cuota. Ver `internal-notes/2026-08-15-handoff.md`.
- **Reenviar el documento entero en cada llamada por tema mata la corrida.**
  No es un derroche: contra un techo de tokens por minuto, es un atasco.
  `segments.py` recorta por los encabezados del propio documento.
- **`run.all_messages()[-1]` no lleva `model_name` con salida tipada.** El
  último mensaje es el retorno de la herramienta; hay que recorrer hacia atrás.
- **Un fallback declarado no es un fallback probado.** `fallback_to` estaba en
  el catálogo, documentado en `findings/0004`, y era inerte: `FallbackModel`
  conmuta ante `ModelAPIError` y el transporte con reintentos lanza
  `httpx.HTTPStatusError`. Solo se vio al agotar la cuota de verdad.
- **Los cupos se miden, no se leen.** El catálogo decía 1500 peticiones al día
  para Gemini; la API contestó 20. Y el cupo de embeddings cuenta **textos, no
  llamadas**: agrupar no compra holgura, hay que espaciar.
- **Un SDK puede devolver menos de lo que se le pidió sin lanzar error.**
  `gemini-embedding-2` devuelve un solo vector para un lote de N. Comprobar
  siempre el largo de la respuesta antes de aparearla con la entrada.
- **Google manda el tiempo de espera en el cuerpo, no en `Retry-After`.**
- **Docling no arranca en Windows sin MSVC**: `torch.compile` invoca `cl.exe`.
  Se resuelve con `TORCHDYNAMO_DISABLE=1`, ya fijado desde el código.

## 10. Al escribir documentación

- `lab/findings/NNNN-*.md`: hallazgos numerados, con **fecha**, **sustentabilidad**
  marcada fuente por fuente, y **a qué resultado afecta**. Español. Congelados.
- `lab/docs/AAAA-MM-DD-*.md`: registros de aprendizaje fechados. Español.
  Congelados.
- **Un documento obsoleto que aparenta estar vigente es peor que ninguno.** Si
  algo cambia, se escribe un documento nuevo; no se reescribe el viejo. La
  excepción es este archivo y `docs/estandares-de-codigo.md`, que sí son vivos.
