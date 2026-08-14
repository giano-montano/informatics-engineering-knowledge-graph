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
| `internal-notes/2026-07-31-handoff.md` | Estado detallado al cerrar julio, con la tabla larga de decisiones. Ignorado por git. |
| `lab/findings/000{1,2,3}-*.md` | Por qué solo unicidad, por qué no SHACL, arquitectura de ingesta contra la literatura. |
| `lab/docs/2026-08-07-*.md` | El modelo de datos vigente y qué se ve (y qué no) dentro de Neo4j. |

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
src/iekg/rules.py             Intérprete del YAML + validadores pre-escritura.
src/iekg/projector.py         RDF -> LPG con MERGE idempotente.
src/iekg/integrity.py         Reglas -> Cypher. Emite, no ejecuta.
src/iekg/tbox.py              Lector de la T-box OWL -> diagrama Mermaid.
src/iekg/db.py                Conexión al driver.
lab/scripts/                  Scripts ejecutables del laboratorio.
lab/cypher/tour.cypher        Consultas comentadas para el Browser. Español.
lab/findings/                 Hallazgos numerados y fechados. CONGELADOS.
lab/docs/                     Registros de aprendizaje fechados. CONGELADOS.
tests/                        Pruebas negativas de integridad y de T-box.
build/                        Artefactos generados desde schema/. Versionados.
internal-notes/               Notas privadas. Ignorado por git.
```

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

## 7. Estado al 2026-08-14

Backbone cargado y verificado: 17 `KnowledgeArea` + 162 `KnowledgeUnit` + 1
`LearningResource`, 4 restricciones de unicidad sobre `iri`, 9 reglas de esquema,
20 pruebas (13 de integridad + 7 de T-box).

Trabajo **sin commitear** en la rama `lab`: `src/iekg/tbox.py`, `tests/test_tbox.py`,
`lab/scripts/emit_tbox_diagram.py`, `build/tbox.md`, `lab/cypher/tour.cypher` y los
dos documentos nuevos de `lab/docs/`.

Huecos conocidos, para no confundirlos con errores:

- **No hay `Topic` ni `Concept` todavía**: los acuña la ingesta. El backbone
  llega hasta las KU, por eso la jerarquía se ve con dos niveles y no cuatro.
- **No hay `Course` ni `ResourceType`**: entran con la capa institucional.
- **No hay ninguna arista `HAS_PREREQUISITE`**: CS2023 no las da a nivel de KU y
  el modelo las define entre `Concept`. El tipo y su regla de aciclicidad ya
  existen; las consultas de prerrequisitos hoy devolverían vacío.
- **El intérprete solo implementa la cardinalidad `exactly_one`.** Un `Topic`
  acuñado necesitará `at_least_one` para exigir su ancla a la `KnowledgeUnit`.

## 8. Lo siguiente: el vertical slice

Un solo sílabo atravesando todas las fases de punta a punta, aunque cada una esté
a medias. **Hace falta un sílabo en PDF**; no hay ninguno en el repo y `data/raw/`
está en `.gitignore`.

Lo difícil, todavía abierto (ver `findings/0003` y `lab/docs/research_pipelines.md`):

1. **Qué significa "coincide"** en el enlace de entidades: coincidencia léxica,
   similitud de embeddings, o umbral combinado. De esto depende toda la precisión.
2. **Deduplicación dentro de la capa institucional.** El backbone es estático,
   pero los `Topic` y `Concept` de un sílabo deben reconciliarse contra los de
   otro, y ese conjunto crece con cada ingesta.
3. **Umbral de decisión y salida a revisión humana** cuando nada lo supera.

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

## 10. Al escribir documentación

- `lab/findings/NNNN-*.md`: hallazgos numerados, con **fecha**, **sustentabilidad**
  marcada fuente por fuente, y **a qué resultado afecta**. Español. Congelados.
- `lab/docs/AAAA-MM-DD-*.md`: registros de aprendizaje fechados. Español.
  Congelados.
- **Un documento obsoleto que aparenta estar vigente es peor que ninguno.** Si
  algo cambia, se escribe un documento nuevo; no se reescribe el viejo. La
  excepción es este archivo y `docs/estandares-de-codigo.md`, que sí son vivos.
