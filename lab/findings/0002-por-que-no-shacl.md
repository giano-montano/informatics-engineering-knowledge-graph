# 0002 — Por qué las reglas de esquema no van en SHACL

- **Fecha:** 2026-07-31
- **Sustentabilidad:** alta. SHACL 1.0 es Recomendación W3C desde 2017 y es citable sin reservas. SHACL 1.2 está en Working Draft (Core con fecha del 30 de junio de 2026) y **no debe citarse como estable**. El resto es razonamiento de diseño propio, sustentable en tanto quede argumentado.
- **Afecta a:** R4 (pipeline de ingesta), archivo declarativo de reglas de esquema.
- **Pregunta que responde:** "¿por qué inventaste un formato propio en vez de usar el estándar?" — que va a salir en la defensa.

---

## Parte 1. Qué es SHACL, en simple

### El hueco que existe

Una ontología OWL dice **qué puede existir**: que hay `KnowledgeUnit`, que cada una pertenece a un `KnowledgeArea`, que `Concept` y `Topic` son clases disjuntas. Pero OWL razona bajo **mundo abierto**: lo que no está afirmado no es falso, solo desconocido. Si una `KnowledgeUnit` no tiene área, OWL no concluye "esto está mal", concluye "debe tener una, aunque no sepamos cuál".

Eso es exactamente lo que dice el comentario de tu propia ontología:

> "Bajo mundo abierto, HermiT no detecta su incumplimiento; los nodos huérfanos se verifican mediante consultas de integridad en R3."

Ya habías identificado el hueco. La pregunta es con qué lo tapas.

### Qué hace SHACL

SHACL es el estándar del W3C para tapar ese hueco. En una frase: **un lenguaje para describir la forma que tus datos deben tener, y un validador que te dice dónde no la tienen.**

Trabaja al revés que OWL. Donde OWL infiere, SHACL verifica. Donde OWL asume mundo abierto, SHACL asume **mundo cerrado**: si el dato no está, falta, y eso es una violación.

Escribes "formas" (*shapes*): "todo nodo de tipo `KnowledgeUnit` debe tener exactamente una arista `knowledgeUnitInKnowledgeArea`, y lo que esté al otro lado debe ser un `KnowledgeArea`". Le pasas tus datos y las formas a un validador —pySHACL en Python— y te devuelve un informe: qué nodo, qué regla, qué falló.

Un detalle que lo hace elegante: **las formas se escriben en RDF**, en el mismo Turtle que tus datos. No hay lenguaje nuevo que aprender ni formato inventado. Las reglas son datos.

### La limitación que decide todo

**SHACL solo entiende RDF.** No sabe qué es un nodo de Neo4j, no puede leer un grafo de propiedades y no puede emitir Cypher. Vive enteramente del lado RDF de tu pipeline.

---

## Parte 2. Las dos opciones, a alto nivel

Tu pipeline tiene **dos momentos** donde algo debe validarse, y están en mundos distintos:

- **Antes de escribir**, sobre lo que el LLM extrajo (todavía es un objeto Python, no está en la base).
- **Después de escribir**, sobre el grafo ya proyectado en Neo4j (para atrapar lo que se rompió al proyectar).

### Opción A — un archivo propio, dos compilaciones

```
reglas.yaml   (una sola fuente de verdad)
     |
     +--> constraints.cypher      -> se aplica una vez a la base
     +--> validadores Python      -> corren ANTES de escribir
     +--> integrity/*.cypher      -> corren DESPUES de escribir
```

Y el pipeline queda:

```
PDF -> Docling -> anclaje -> LLM -> Pydantic
                                       |
                                [validador Python]   <- de reglas.yaml
                                       |
                                  enlace + MERGE
                                       |
                              [consultas de integridad]  <- de reglas.yaml
```

Una regla escrita una vez cubre los dos momentos. Eso es lo que compra tener un intérprete.

### Opción B — SHACL

```
shapes.ttl  (RDF)
     |
     +--> pySHACL -> informe de violaciones
```

Y el pipeline:

```
PDF -> Docling -> anclaje -> LLM -> Pydantic
                                       |
                            [serializar Pydantic a RDF]   <- paso extra
                                       |
                              [pySHACL contra shapes.ttl]
                                       |
                                  proyectar a LPG
                                       |
                            [ ... nada valida aqui ... ]
```

**La flecha de SHACL se detiene antes del LPG.** Cubre el primer momento —y bien— pero no llega al segundo. Y el segundo es justamente donde se detectan los errores del proyector, que es código tuyo y nuevo, o sea lo más probable de fallar.

---

## Parte 3. Lo concreto

### Cobertura de las cinco reglas en SHACL

| Regla | En SHACL | Comentario |
|---|---|---|
| Dominio / rango | Core, `sh:targetObjectsOf` + `sh:class` | limpio |
| Relación funcional | Core, `sh:minCount 1` + `sh:maxCount 1` | limpio |
| Etiquetas disjuntas | Core, `sh:xone` / `sh:not` | verboso pero funciona |
| Clave única | **fuera de Core** | necesita SHACL-SPARQL |
| Aciclicidad | **fuera de Core** | SHACL-SPARQL con camino recursivo, incómodo |

Tres de cinco salen limpias. Las otras dos obligan a bajar a SPARQL incrustado, que es justamente donde SHACL deja de ser declarativo y legible.

### Cómo se ve la misma regla en cada opción

`ku-en-una-sola-ka`, que sale del axioma `:knowledgeUnitInKnowledgeArea rdf:type owl:FunctionalProperty`.

**En SHACL:**

```turtle
:KnowledgeUnitShape a sh:NodeShape ;
    sh:targetClass :KnowledgeUnit ;
    sh:property [
        sh:path :knowledgeUnitInKnowledgeArea ;
        sh:class :KnowledgeArea ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] .
```

**En el YAML propio:**

```yaml
- id: ku-en-una-sola-ka
  type: relacion_funcional
  relationship: KNOWLEDGE_UNIT_IN_KNOWLEDGE_AREA
  from: KnowledgeUnit
  to: KnowledgeArea
  cardinality: exactly_one
  enforcement: [pre_escritura, consulta_integridad]
  origen_owl: "owl:FunctionalProperty sobre :knowledgeUnitInKnowledgeArea"
```

Que el intérprete compila a **dos** artefactos. Consulta de integridad:

```cypher
// regla: ku-en-una-sola-ka
MATCH (ku:KnowledgeUnit)
OPTIONAL MATCH (ku)-[:PART_OF]->(ka:KnowledgeArea)
WITH ku, count(DISTINCT ka) AS areas
WHERE areas <> 1                      // atrapa tanto 0 como 2 o más
RETURN 'ku-en-una-sola-ka' AS regla, ku.iri AS entidad, areas AS encontradas;
```

Y validador previo a la escritura:

```python
def check_ku_en_una_sola_ka(candidato, catalogo):
    areas = catalogo.destinos(candidato.iri, "KNOWLEDGE_UNIT_IN_KNOWLEDGE_AREA")
    if len(areas) != 1:
        yield Violacion("ku-en-una-sola-ka", candidato.iri, encontradas=len(areas))
```

La versión SHACL es más corta y es estándar. La versión propia es más larga y no lo es, pero **cubre los dos momentos del pipeline con una sola declaración**.

---

## Decisión

Se usa el **archivo YAML propio con intérprete de dos backends**. No por desconocer SHACL, sino por una razón concreta:

> La restricción acordada con el asesor es que **una sola fuente declarativa alimente al proyector y a los validadores**. Los validadores viven en dos mundos: Python sobre objetos Pydantic antes de escribir, y Cypher sobre el LPG después. SHACL no puede emitir Cypher ni leer un grafo de propiedades, así que es estructuralmente incapaz de ser esa fuente única. Además, dos de las cinco reglas se salen de SHACL Core y obligan a SPARQL incrustado.

Esa es la respuesta corta cuando pregunten en la defensa.

## Qué haría revisar esta decisión

- Si la capa operativa dejara de ser LPG y el sistema viviera en un triplestore. Entonces SHACL es la respuesta obvia y el YAML sobra.
- Si se quisiera **publicar** las restricciones para que terceros validen sus propios currículos contra el modelo. Un `shapes.ttl` es reutilizable e interoperable; un YAML propio no.
- Si apareciera una capa SHACL adicional sobre el RDF de entrada. Es compatible con lo decidido y añade una red de seguridad antes de proyectar. No se hace ahora por sobreingeniería, no por incompatibilidad.

## Fuentes

- [SHACL 1.2 Core (W3C Working Draft, 30 jun 2026)](https://www.w3.org/TR/shacl12-core/) — no citar como estable
- [SHACL 1.2 SPARQL Extensions (W3C Working Draft)](https://www.w3.org/TR/shacl12-sparql/)
- [pySHACL, releases](https://github.com/RDFLib/pySHACL/releases) — v0.31.0, enero 2026
- Para citar en la tesis: SHACL 1.0, Recomendación W3C del 20 de julio de 2017.
