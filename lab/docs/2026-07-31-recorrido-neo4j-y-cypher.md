# Recorrido de lo construido: Neo4j, Cypher y el proyector

**Fecha: 2026-07-31. Registro congelado.**

Este documento describe el estado del laboratorio el día que se escribió. **No se
mantiene actualizado.** Si algo cambia, se escribe un documento nuevo con otra
fecha. Está pensado para reconsultarlo mientras aprendes Neo4j, no como fuente de
verdad del proyecto: esa es el código.

---

## 1. Qué hay levantado

Todo vive en Docker, declarado en `docker-compose.yml`:

| | |
|---|---|
| Neo4j | 5.26.28 Enterprise (licencia de evaluación) |
| APOC | 5.26.28 |
| GDS | 2.13.11 |
| Base de datos | `neo4j` (una sola, porque el despliegue final va a Community) |
| Browser | http://localhost:7474 |
| Bolt (driver Python) | `bolt://localhost:7687` |

```powershell
docker compose up -d       # levantar
docker compose ps          # ver estado
docker compose logs neo4j  # ver el arranque
docker compose down        # parar (los volúmenes sobreviven)
```

La contraseña está en `.env`, que git ignora. `.env.example` es la plantilla.

---

## 2. El modelo de datos en el grafo

El backbone CS2023 proyectado son **180 nodos y 341 aristas**:

```
(:KnowledgeElement:KnowledgeArea)   x 17
(:KnowledgeElement:KnowledgeUnit)   x 162
(:LearningResource)                 x 1     <- el documento CS2023
```

```
(:KnowledgeUnit)-[:PART_OF]->(:KnowledgeArea)              x 162
(:KnowledgeElement)-[:WAS_DERIVED_FROM]->(:LearningResource) x 179
```

Tres cosas que conviene entender del modelo, porque no son obvias viniendo de OWL:

**Las etiquetas múltiples reemplazan la jerarquía de clases.** En OWL,
`KnowledgeArea ⊑ KnowledgeElement`. En LPG no hay herencia, así que el nodo lleva
**las dos etiquetas**. Eso permite consultar por el nivel general
(`MATCH (n:KnowledgeElement)`) o por el específico (`MATCH (n:KnowledgeArea)`).

**Las inversas no se guardan.** OWL declara `hasPart` como inversa de `isPartOf`.
En Neo4j se guarda **una sola** dirección, porque recorrer una relación al revés
cuesta lo mismo que recorrerla hacia adelante:

```cypher
MATCH (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea)  // hacia arriba
MATCH (ka:KnowledgeArea)<-[:PART_OF]-(ku:KnowledgeUnit)  // hacia abajo, mismo costo
```

Guardar las dos duplicaría el hecho y rompería la idempotencia.

**La transitividad no se materializa, se recorre.** `isPartOf` es transitiva en
OWL. En Cypher eso es el asterisco:

```cypher
MATCH (n {iri: $iri})-[:PART_OF*]->(ka:KnowledgeArea)
RETURN ka.prefLabel
```

---

## 3. El Cypher, explicado

### 3.1 Restricciones

Solo la unicidad, porque es la única que sobrevive al pasar a Community
(ver `findings/0001`):

```cypher
CREATE CONSTRAINT unique_iri_KnowledgeElement IF NOT EXISTS
FOR (n:KnowledgeElement) REQUIRE n.iri IS UNIQUE;
```

Una restricción de unicidad **crea un índice por debajo**. Por eso todo `MATCH`
que busque un nodo por `iri` debe llevar también la etiqueta: sin etiqueta,
Neo4j no puede usar el índice y escanea la base entera.

> **Trampa encontrada.** `IF NOT EXISTS` compara el **esquema**, no el nombre.
> Al renombrar las restricciones de `iri_unica_*` a `unique_iri_*`, Neo4j vio que
> ya existía una equivalente y no creó nada: la base se quedó con los nombres
> viejos mientras el archivo generado decía otros. Para renombrar hay que
> `DROP CONSTRAINT` primero.

```cypher
SHOW CONSTRAINTS;                     // ver las que hay
DROP CONSTRAINT nombre IF EXISTS;     // borrar una
```

### 3.2 Escritura idempotente: `UNWIND` + `MERGE`

Este es el patrón central de toda la ingesta:

```cypher
UNWIND $rows AS r
MERGE (x:KnowledgeElement:KnowledgeUnit {iri: r.iri})
SET x += r.props
RETURN count(x) AS n
```

Qué hace cada pieza:

- **`$rows`** es un parámetro: una lista de diccionarios enviada desde Python. Los
  datos **nunca** se concatenan dentro del texto de la consulta.
- **`UNWIND`** convierte esa lista en filas. Una sola consulta procesa 162 nodos
  en vez de mandar 162 consultas.
- **`MERGE`** es *encuentra o crea*. Si ya existe un nodo con ese `iri` y esas
  etiquetas, lo reutiliza; si no, lo crea. Es lo que hace que correr la ingesta
  dos veces deje el mismo resultado.
- **`SET x += r.props`** fusiona propiedades sin borrar las que no vengan en el
  diccionario. Con `=` en vez de `+=` se reemplazaría el mapa entero.

Cuidado con `MERGE`: **coincide con el patrón completo**. `MERGE (x:A:B {iri: ...})`
y `MERGE (x:A {iri: ...})` no son lo mismo, y el segundo podría crear un nodo
duplicado si el primero ya existe con otra combinación de etiquetas. Por eso el
proyector agrupa los nodos por conjunto de etiquetas y emite un `MERGE` por grupo.

Para las aristas:

```cypher
UNWIND $rows AS r
MATCH (a:KnowledgeElement {iri: r.source})
MATCH (b:KnowledgeElement {iri: r.target})
MERGE (a)-[rel:PART_OF]->(b)
RETURN count(rel) AS n
```

Los dos `MATCH` llevan etiqueta a propósito, para ir por el índice de la
restricción de unicidad. Sin ella sería un escaneo completo por cada arista.

### 3.3 Las consultas de integridad

Se generan desde `schema/schema_rules.yaml` y quedan en `build/integrity/`.
Todas devuelven la misma forma: `(rule, entity, detail)`. **Cero filas significa
regla satisfecha.**

**Etiquetas disjuntas.** La ontología dice que `KnowledgeElement` es la unión
disjunta de cuatro clases, o sea exactamente una etiqueta, ni cero ni dos:

```cypher
MATCH (n:KnowledgeElement)
WITH n, [l IN labels(n) WHERE l IN ['Concept','KnowledgeArea','KnowledgeUnit','Topic']] AS found
WHERE size(found) <> 1
RETURN n.iri AS entity;
```

`labels(n)` devuelve la lista de etiquetas del nodo. La comprensión de lista
`[x IN lista WHERE cond]` funciona como en Python.

**Relación funcional.** Cada unidad pertenece a exactamente un área:

```cypher
MATCH (a:KnowledgeUnit)
OPTIONAL MATCH (a)-[:PART_OF]->(b:KnowledgeArea)
WITH a, count(DISTINCT b) AS targets
WHERE targets <> 1
RETURN a.iri AS entity;
```

El **`OPTIONAL MATCH`** es la clave. Con un `MATCH` normal, una unidad sin área
simplemente no aparecería en el resultado y la violación pasaría inadvertida.
`OPTIONAL MATCH` la conserva con `b = null`, y `count(DISTINCT b)` da 0.

**Dominio y rango.** Qué pares de etiquetas puede unir una relación:

```cypher
MATCH (a)-[:PART_OF]->(b)
WHERE NOT ((a:Concept AND b:Topic)
        OR (a:Topic AND b:KnowledgeUnit)
        OR (a:KnowledgeUnit AND b:KnowledgeArea))
RETURN a.iri + ' -> ' + b.iri AS entity;
```

`a:Concept` dentro de un `WHERE` es una **expresión booleana**: "¿tiene este nodo
esta etiqueta?".

**Aciclicidad.** Un ciclo es un camino que vuelve al mismo nodo:

```cypher
MATCH cycle = (n)-[:PART_OF*1..6]->(n)
RETURN n.iri AS entity, length(cycle) AS detail
LIMIT 25;
```

La misma variable `n` en los dos extremos es lo que expresa "vuelve a sí mismo".
No hay bucle infinito porque Cypher no repite la misma relación dentro de un
camino; la cota `*1..6` es por eficiencia, no por seguridad.

### 3.4 Dos limitaciones de Cypher 5 que costaron tiempo

**No hay función de lista a cadena, y `toString()` rechaza listas.** La solución
sin depender de APOC:

```cypher
reduce(acc = '', x IN labels(n) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x)
```

**Las etiquetas y los tipos de relación no admiten parámetros.** No se puede
escribir `MATCH (n:$label)`. Hay que interpolarlos en el texto de la consulta, y
por eso el código los valida contra la especificación antes de construir nada.
Todo lo demás sí va parametrizado.

---

## 4. Consultas útiles para explorar

```cypher
// Censo de etiquetas
MATCH (n) UNWIND labels(n) AS label
RETURN label, count(*) AS n ORDER BY n DESC;

// Censo de relaciones
MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS n;

// Las unidades de un área
MATCH (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea {prefLabel:'Artificial Intelligence'})
RETURN ku.prefLabel ORDER BY ku.prefLabel;

// Áreas ordenadas por número de unidades
MATCH (ka:KnowledgeArea)<-[:PART_OF]-(ku:KnowledgeUnit)
RETURN ka.prefLabel, count(ku) AS unidades ORDER BY unidades DESC;

// Ver el esquema que Neo4j infiere de los datos
CALL db.schema.visualization();

// Plan de ejecución: comprobar si usa índice o escanea
EXPLAIN MATCH (n:KnowledgeElement {iri:'...'}) RETURN n;
```

`EXPLAIN` muestra el plan sin ejecutar; `PROFILE` lo ejecuta y añade contadores
reales. Si aparece `NodeByLabelScan` donde esperabas `NodeIndexSeek`, falta un
índice o falta la etiqueta en el patrón.

---

## 5. Reproducir todo desde cero

```powershell
docker compose up -d
uv sync
uv run python lab/scripts/check_stack.py         # driver + parseo de Turtle
uv run python lab/scripts/load_backbone.py --reset  # proyectar y verificar
uv run python lab/scripts/check_integrity.py     # emitir Cypher y ejecutarlo
uv run pytest tests/ -q                          # prueba negativa: 13 pruebas
```

Y la sonda de restricciones, que fue el origen de `findings/0001`:

```powershell
docker compose exec -T neo4j bash -s < lab/scripts/probe_constraints.sh
```

---

## 6. Decisiones tomadas ese día

| Decisión | Dónde está el argumento |
|---|---|
| Neo4j 5.26 LTS en vez de la 2026.06 vigente | comentario de `docker-compose.yml` |
| Enterprise en desarrollo, Community al desplegar | `findings/0001` |
| Solo la unicidad como restricción nativa | `findings/0001` |
| Formato propio en YAML en vez de SHACL | `findings/0002` |
| Las tres subpropiedades de `isPartOf` colapsan en `PART_OF` | `schema/schema_rules.yaml` |
| Las inversas no se materializan | `schema/schema_rules.yaml` |
| La clausura transitiva no se materializa | `schema/schema_rules.yaml` |
| Arquitectura del pipeline validada contra la literatura | `findings/0003` |
| Código en inglés, prosa en español | `docs/estandares-de-codigo.md` |

## 7. Lo que quedaba pendiente al cerrar el día

El paso 4 del plan: el vertical slice de un sílabo de punta a punta. Y dentro de
él, lo que `findings/0003` señala como la parte difícil — la función de
emparejamiento del enlace de entidades, la deduplicación dentro de la capa
institucional, y el umbral que decide cuándo hace falta revisión humana.
