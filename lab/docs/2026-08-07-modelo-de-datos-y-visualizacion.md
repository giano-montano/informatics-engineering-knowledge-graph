# Modelo de datos en Neo4j y cómo ver el grafo

**Fecha: 2026-08-07. Registro congelado.**

Documento de aprendizaje. Explica el modelo de datos del grafo, cómo se puebla,
cómo abrirlo y qué consultar. Todo lo que dice se ejecutó ese día contra la
instancia del laboratorio; los números que aparecen son los que salieron, no
estimaciones.

Complementa a `2026-07-31-recorrido-neo4j-y-cypher.md`, que cubre la mecánica de
Cypher y del proyector. Aquí el foco está en **el modelo** y en **la vista**.

---

## 1. Qué se pidió y qué se hizo

El encargo tenía cuatro partes:

1. Modelo de datos de Neo4j pensado como capa operativa del producto.
2. Un script que pueble el grafo con las KA y las KU.
3. Poder abrirlo y verlo, y hacer consultas Cypher interesantes.
4. Este documento.

Lo que ya existía al empezar: el proyector (`src/iekg/projector.py`), el
intérprete de reglas (`src/iekg/rules.py`), el compilador de integridad
(`src/iekg/integrity.py`) y el script de carga (`lab/scripts/load_backbone.py`).
El modelo de datos, de hecho, **ya estaba decidido y codificado** en
`schema/schema_rules.yaml`, y ya cumplía los tres criterios del encargo: clases
como etiquetas, tipos de relación sin duplicar, inversas no materializadas. La
sección 3 lo explica; no se cambió nada de eso.

Lo que se agregó hoy:

| Archivo | Qué es |
|---|---|
| `src/iekg/tbox.py` | Lector de la T-box OWL + emisor de su diagrama |
| `lab/scripts/emit_tbox_diagram.py` | Script que genera el artefacto |
| `build/tbox.md` | La T-box entera, dibujada. Generado, no editado a mano |
| `lab/cypher/tour.cypher` | 15 consultas comentadas para pegar en el Browser |
| `lab/docs/2026-08-07-*.md` | Este documento |

### La decisión sobre la T-box, y su consecuencia

Se ofrecieron tres formas de meter la T-box (el esquema OWL: clases, jerarquía,
disyunciones, cardinalidades) dentro de Neo4j. **Elegiste no materializarla.**

La consecuencia, dicha sin adornos: dentro de la base **la T-box no se ve como
tal**. Neo4j puede dibujar un esquema con `CALL db.schema.visualization()`, pero
eso es un resumen inferido de los datos existentes, no tu ontología. No aparecen
las disyunciones, ni "una KU pertenece a exactamente un área", ni la
transitividad de `PART_OF`, ni las clases sin instancias.

Por eso la T-box se emite **fuera** de la base, en `build/tbox.md`, generada
desde el TTL y el YAML. Misma lógica que los `.cypher` de `build/integrity/`: el
intérprete emite artefactos, no ejecuta. La capa operativa queda con datos
puros; la ontología queda documentada, versionada y citable.

---

## 2. Levantar todo desde cero

Secuencia completa, verificada hoy. Desde la raíz del repositorio, en PowerShell:

```powershell
docker compose up -d
uv sync
uv run python lab/scripts/check_stack.py
uv run python lab/scripts/load_backbone.py --reset
uv run python lab/scripts/check_integrity.py
uv run python lab/scripts/emit_tbox_diagram.py
uv run pytest tests/ -q
```

Lo que debe salir:

```
Stack verified.
Backbone projected and verified.
Integrity satisfied.
Written build\tbox.md
13 passed
```

Si `docker compose up -d` falla con un error sobre `dockerDesktopLinuxEngine`,
Docker Desktop no está corriendo: hay que abrirlo y esperar a que el motor
arranque (unos 30-60 segundos). `docker compose ps` debe mostrar
`iekg-neo4j  Up (healthy)`.

La contraseña vive en `.env`, que git ignora.

---

## 3. El modelo de datos: de OWL a Neo4j

Esta es la parte conceptual. Vale la pena entenderla bien porque **todo lo demás
se sigue de aquí**.

### 3.1 El problema

OWL y Neo4j son dos modelos distintos y no hay traducción automática buena:

| | OWL / RDF | Neo4j / LPG |
|---|---|---|
| Unidad | triple `(sujeto, predicado, objeto)` | nodo con propiedades, arista con propiedades |
| Clases | de primera clase, con herencia y razonamiento | no existen: hay **etiquetas**, que son sólo tags |
| Semántica | mundo abierto, un razonador infiere | mundo cerrado, lo que no está no está |
| Inversas | se declaran y el razonador las usa | no existen: se recorre la arista al revés |

Hay herramientas que hacen la conversión sola (neosemantics / n10s). No se usa:
generan un grafo fiel a RDF pero incómodo de consultar, con nodos por cada
literal y URIs como identificadores en crudo. El proyector está escrito a mano y
la traducción está **declarada** en `schema/schema_rules.yaml`, no hardcodeada.

### 3.2 Las seis reglas de traducción

**Regla 1 — una clase OWL es una etiqueta.** No una tabla, no un nodo aparte.

```
:KA-AI a :KnowledgeArea      →      (:KnowledgeArea {iri: '...#KA-AI'})
```

**Regla 2 — la subclase se vuelve una etiqueta *adicional*.** En LPG no hay
herencia. Si `KnowledgeArea ⊑ KnowledgeElement`, el nodo lleva las dos:

```cypher
(:KnowledgeElement:KnowledgeArea {iri: '...#KA-AI'})
```

Lo que compra: puedes preguntar por el nivel general o por el específico, con la
misma sintaxis y ambas por índice.

```cypher
MATCH (n:KnowledgeElement)   // los 179: áreas y unidades
MATCH (n:KnowledgeArea)      // sólo las 17 áreas
```

`KnowledgeElement` nunca se instancia sola: es una unión disjunta. Aparece
siempre acompañada.

**Regla 3 — una propiedad de objeto es un tipo de arista, en UNA sola
dirección.** OWL declara `hasPart` como inversa de `isPartOf`. Guardar las dos
sería guardar el mismo hecho dos veces: el doble de aristas, y `MERGE` deja de
ser idempotente porque hay dos representaciones del mismo hecho. En Neo4j
recorrer una arista al revés cuesta **exactamente lo mismo**:

```cypher
MATCH (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea)   // de abajo a arriba
MATCH (ka:KnowledgeArea)<-[:PART_OF]-(ku:KnowledgeUnit)   // de arriba a abajo
```

Las dos consultas leen las mismas 162 aristas. La inversa se declara en el YAML
sólo como **nombre de lectura**, para que el pipeline sepa que si un sílabo
afirma `hasPart`, eso se normaliza a un `PART_OF` en la dirección canónica.

**Regla 4 — las tres subpropiedades de `isPartOf` colapsan en `PART_OF`.**
`conceptInTopic`, `topicInKnowledgeUnit` y `knowledgeUnitInKnowledgeArea` son
tres propiedades distintas en OWL. En el grafo son un solo tipo de arista,
porque **las etiquetas de los extremos ya determinan cuál es**: una arista de un
`:Topic` a una `:KnowledgeUnit` sólo puede ser `topicInKnowledgeUnit`. Un tipo
por cada una no agregaría información y sí obligaría a enumerarlos en cada
consulta de jerarquía. El colapso es reversible: la regla `part-of-pairs` del
YAML lista los pares permitidos y los verifica.

**Regla 5 — la transitividad no se materializa, se recorre.** `isPartOf` es
transitiva. La tentación es escribir las aristas inferidas (si A está en B y B
en C, escribir A→C). No se hace, por una razón que es contribución de la tesis:
**una arista inferida sería indistinguible de una afirmada**, y el pipeline tiene
que poder auditar exactamente qué propuso el LLM. La transitividad se pide en la
consulta con el asterisco:

```cypher
MATCH (n)-[:PART_OF*1..3]->(ka:KnowledgeArea)
```

**Regla 6 — la identidad es el IRI, y sólo la unicidad se garantiza nativamente.**
Cada nodo lleva la propiedad `iri`, que es su identificador OWL completo. Sobre
ella hay una restricción de unicidad por cada etiqueta raíz. Es la **única**
clase de restricción que sobrevive al pasar de Enterprise a Community
(`findings/0001`), así que es la única de la que el diseño puede depender. Todo
lo demás —cardinalidades, dominios, disyunciones— se verifica con las consultas
de `build/integrity/`.

Una restricción de unicidad **crea un índice por debajo**. De ahí una regla
práctica que atraviesa todo el código: **todo `MATCH` que busque por `iri` lleva
también la etiqueta**, o Neo4j no puede usar el índice y escanea la base entera.

### 3.3 El resultado

```
(:KnowledgeElement:KnowledgeArea)  x  17
(:KnowledgeElement:KnowledgeUnit)  x 162
(:LearningResource)                x   1     ← el documento CS2023

(:KnowledgeUnit)-[:PART_OF]->(:KnowledgeArea)                x 162
(:KnowledgeElement)-[:WAS_DERIVED_FROM]->(:LearningResource) x 179
```

180 nodos, 341 aristas. Cada elemento apunta a CS2023: esa arista de procedencia
es la que hará auditable, más adelante, de qué sílabo salió cada cosa.

---

## 4. Cómo puebla el script

`lab/scripts/load_backbone.py` es el script de población. Cinco etapas:

**1 · Cargar la especificación.** `rules.load()` lee `schema/schema_rules.yaml`.
Nada del mapeo está en el código Python: el código es un intérprete de ese
archivo.

**2 · Leer el Turtle.** `read_turtle()` usa rdflib sobre
`ontology/backbone_cs2023.ttl`. Recorre los `rdf:type` para saber qué etiquetas
lleva cada individuo, junta las propiedades de datos declaradas en el YAML, y
recorre las propiedades de objeto para armar las aristas. Las inversas que
aparezcan se voltean a la dirección canónica, y al final se deduplica: el mismo
hecho pudo llegar por la propiedad y por su inversa.

**3 · Validar ANTES de escribir.** `spec.validate()` corre los validadores
Python compilados desde el YAML: disyunción de etiquetas, cardinalidad
funcional, dominios y rangos. Si algo falla, **no se escribe nada**. Es
deliberado: es más barato rechazar en memoria que limpiar la base después.

**4 · Crear restricciones y escribir.** El patrón de escritura es el que usará
toda la ingesta:

```cypher
UNWIND $rows AS r
MERGE (x:KnowledgeElement:KnowledgeUnit {iri: r.iri})
SET x += r.props
RETURN count(x) AS n
```

- `$rows` es un **parámetro**: una lista de diccionarios que viaja desde Python.
  Los datos nunca se concatenan dentro del texto de la consulta.
- `UNWIND` desarma la lista en filas: una sola consulta escribe 162 nodos.
- `MERGE` es "buscá y si no está, creá". Por eso correrlo dos veces deja el
  mismo estado que correrlo una.
- `SET x += r.props` actualiza propiedades sin borrar las que no vengan.

Las etiquetas se **interpolan** en el texto (`:KnowledgeElement:KnowledgeUnit`)
porque Cypher no admite parámetros para etiquetas ni para tipos de relación.
Por eso se validan antes contra la especificación: es la superficie donde una
inyección sería posible.

Los nodos se agrupan por juego de etiquetas y las aristas por
`(tipo, etiqueta del origen, etiqueta del destino)`, para que cada `MATCH` entre
por índice.

**5 · Probar la idempotencia.** El script proyecta **dos veces** y compara los
censos. Si `MERGE` es idempotente, la segunda pasada no cambia ningún número.
Eso es la prueba; no alcanza con afirmarlo.

Salida real de hoy:

```
Pass 1  read {'nodes': 180, 'edges': 341}  written {'nodes': 180, 'edges': 341}
        constraints: 4
Pass 2  read {'nodes': 180, 'edges': 341}  written {'nodes': 180, 'edges': 341}
  OK         :KnowledgeArea = 17 (expected 17)
  OK         :KnowledgeUnit = 162 (expected 162)
  OK         :LearningResource = 1 (expected 1)
  OK         :KnowledgeElement = 179 (expected 179)
  OK         -[:PART_OF]-> = 162 (expected 162)
  OK         -[:WAS_DERIVED_FROM]-> = 179 (expected 179)
  OK         the second pass changed nothing
```

`--reset` vacía la base antes (`MATCH (n) DETACH DELETE n`). Sin la bandera, la
carga es incremental.

---

## 5. Abrir el grafo y verlo

Hay dos clientes. **Empieza por el Browser**: viene con el contenedor y no
requiere configurar nada.

### 5.1 Neo4j Browser (recomendado para empezar)

1. Con el contenedor arriba, abre **http://localhost:7474**.
2. Login: `Connect URL` en `bolt://localhost:7687`, usuario `neo4j`, contraseña
   la de `.env`.
3. Pega esta consulta en la barra de arriba y dale **Ctrl+Enter**:

```cypher
MATCH p = (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea)
RETURN p;
```

Eso dibuja el backbone entero: 17 racimos, uno por área, con sus unidades
alrededor. Es *la* foto.

Cosas útiles de la vista de grafo:

- **Clic en un nodo** → se despliega abajo un panel con sus propiedades y sus
  etiquetas.
- **Doble clic en un nodo** → expande sus vecinos aunque no estuvieran en el
  resultado.
- **Clic en una etiqueta** en el panel superior (`KnowledgeArea`,
  `KnowledgeUnit`) → elige color y qué propiedad se muestra como texto del
  nodo. Ponlo en `prefLabel`; por defecto muestra el `iri`, que es larguísimo.
- Arriba a la derecha se alterna entre vista **Graph**, **Table** y **Text**.
  Las consultas que devuelven agregados (números, conteos) sólo tienen sentido
  en Table.

> **Por qué `RETURN p` y no `RETURN ku, ka`.** El Browser dibuja lo que le
> devuelves. Si devuelves dos nodos sueltos, dibuja nodos sueltos. `p = (...)`
> captura el **camino**, es decir nodos *más* la arista, y entonces sí aparece
> la flecha.

### 5.2 Neo4j Desktop

Tienes instalada la versión **2.1.1**, sin ninguna conexión registrada todavía
(`~/.Neo4jDesktop2/Data/connections` está vacío).

Lo importante de entender: **Desktop no adopta el Neo4j de Docker como instancia
propia**. Desktop sabe crear y administrar instancias que él mismo instala; a la
tuya sólo se puede *conectar* como instancia remota. La configuración, los
plugins (APOC, GDS) y la versión los sigue mandando `docker-compose.yml`. Eso es
lo correcto para el proyecto: la instancia debe ser reproducible desde el
repositorio, no depender de lo que tengas clicado en una GUI.

Pasos:

1. Abre Neo4j Desktop.
2. Busca la opción de **agregar una instancia remota** — es la que pide una URL
   de conexión en vez de crear una base nueva (según la versión aparece como
   *Connect to remote instance*, *Add connection* o *Remote connection*).
3. Datos:
   - URL: `bolt://localhost:7687`
   - Usuario: `neo4j`
   - Contraseña: la de `.env`
4. Una vez conectada, la instancia aparece como una tarjeta más y desde ahí se
   abre la herramienta de consulta, donde va el mismo Cypher.

Si la conexión falla, el orden de revisión es: ¿está el contenedor arriba
(`docker compose ps`)? ¿responde el puerto (`http://localhost:7474` abre)? ¿la
contraseña es la de `.env`?

---

## 6. El recorrido de consultas

`lab/cypher/tour.cypher` tiene 15 consultas comentadas, de menor a mayor. Las 15
se ejecutaron hoy contra la base y todas corren. Un resumen de qué enseña cada
una:

| # | Qué hace | Qué enseña |
|---|---|---|
| 0-1 | Censo por etiqueta y por tipo de arista | Un nodo tiene varias etiquetas: la suma da más que el total |
| 2 | El backbone entero | `RETURN p` de un camino es lo que dibuja aristas |
| 3 | `db.schema.visualization()` | El esquema **inferido**, y en qué se diferencia de la T-box |
| 4 | `SHOW CONSTRAINTS` | Las 4 restricciones de unicidad y su índice |
| 5 | Un área con sus unidades | Recorrer la arista al revés sin costo |
| 6 | Ranking de áreas por tamaño | Primer agregado con `count` |
| 7 | Lo mismo con `OPTIONAL MATCH` | Que un `MATCH` normal **borra** las filas con cero |
| 8 | Búsqueda por texto | `CONTAINS`, y por qué aquí no hace falta índice |
| 9 | Ascenso transitivo `*1..3` | Por qué no se materializa la clausura |
| 10 | Procedencia desde CS2023 | La arista que hará auditable la ingesta |
| 11 | Vecindario de un nodo | `-[r]-` sin flecha recorre en ambos sentidos |
| 12 | Unidades huérfanas o duplicadas | La regla de integridad, en versión legible |
| 13 | Juegos de etiquetas | La subclase OWL convertida en etiqueta |
| 14 | Propiedades crudas de un nodo | Cómo se ve un nodo por dentro |

Algunos resultados reales, para que sepas qué esperar:

**Las áreas más grandes de CS2023** (consulta 6):

```
Foundations of Programming Languages          22
Operating Systems                             14
Data Management                               13
Artificial Intelligence                       12
Graphics and Interactive Techniques           12
```

**Las más chicas** (consulta 7, con `OPTIONAL MATCH`):

```
Algorithmic Foundations                        5
Mathematical and Statistical Foundations       5
Parallel and Distributed Computing             5
```

**Buscar "machine"** (consulta 8) devuelve tres, y muestra algo lindo: el mismo
término cae en dos áreas distintas, que es exactamente el problema de
desambiguación que tendrá el enlace de entidades:

```
Assembly Level Machine Organization    Architecture and Organization
Machine-Level Data Representation      Architecture and Organization
Machine Learning                       Artificial Intelligence
```

**Unidades mal colgadas** (consulta 12): **cero filas**. Como debe ser.

> Recuerda lo que dice `estandares-de-codigo.md`: que una consulta de validación
> no encuentre nada en datos limpios **no prueba nada**. Lo que prueba que la
> regla funciona es la prueba negativa de `tests/test_integrity.py`, que inyecta
> la violación a propósito dentro de una transacción que se revierte.

---

## 7. Dónde está la T-box

En **`build/tbox.md`**. Se regenera con:

```powershell
uv run python lab/scripts/emit_tbox_diagram.py
```

Lee `ontology/ontologia_informatica.ttl` con rdflib y lo cruza con
`schema/schema_rules.yaml`, así que el diagrama muestra a la vez el axioma OWL y
**a qué se proyecta en el grafo**. Contiene:

1. La jerarquía de clases, con el juego de etiquetas de cada una.
2. Las propiedades de objeto como aristas entre clases, con su tipo LPG.
3. La tabla completa OWL → LPG, marcando cuáles se escriben y cuáles sólo se
   recorren al revés.
4. Los axiomas **sin contraparte nativa** en Neo4j: las dos disyunciones, las
   cuatro propiedades transitivas, la funcional, y los tres existenciales de la
   jerarquía de cuatro niveles.

Los diagramas están en Mermaid. Se ven en VS Code (vista previa de Markdown) y
en GitHub sin instalar nada.

### Qué muestra Neo4j por su cuenta, y qué no

`CALL db.schema.visualization()` hoy devuelve esto:

```
Etiquetas:  KnowledgeArea, KnowledgeElement, KnowledgeUnit,
            LearningResource, Course, ResourceType
Aristas:    KnowledgeUnit    -[:PART_OF]->          KnowledgeArea
            KnowledgeElement -[:PART_OF]->          KnowledgeElement
            KnowledgeElement -[:WAS_DERIVED_FROM]-> LearningResource
```

Dos observaciones que valen como aprendizaje:

- **`Course` y `ResourceType` aparecen sin tener un solo nodo.** No es magia: es
  que hay restricciones de unicidad declaradas sobre esas etiquetas, y eso basta
  para que Neo4j las conozca. Confirma que el esquema que muestra sale de los
  metadatos y de los datos, no de la ontología.
- **La misma arista aparece varias veces** con distintas combinaciones de
  etiquetas (`KnowledgeUnit→KnowledgeArea` y `KnowledgeElement→KnowledgeElement`)
  porque cada nodo tiene dos etiquetas y Neo4j enumera las combinaciones
  observadas. No son aristas distintas: son 162 aristas vistas de varias formas.

Lo que **no** aparece por ningún lado: `Concept`, `Topic` (no hay instancias ni
restricciones), la disyunción de las cuatro subclases, la cardinalidad "una KU
en exactamente un área", la transitividad, y los existenciales. Todo eso vive
en `build/tbox.md` y se hace cumplir con `build/integrity/`.

---

## 8. Qué NO está todavía

Para que quede registrado y no se confunda un hueco con un error:

- **No hay `Topic` ni `Concept`.** Los acuña el pipeline de ingesta desde los
  sílabos; el backbone llega hasta las KU. Por eso la jerarquía tiene dos
  niveles visibles y no cuatro.
- **No hay `Course` ni `ResourceType`.** Entran con la capa institucional.
- **No hay ninguna arista `HAS_PREREQUISITE`.** CS2023 no las da a nivel de KU y
  el modelo las define entre `Concept`, que aún no existen. Por eso el recorrido
  no trae consultas de prerrequisitos: hoy sólo devolverían vacío. El tipo de
  arista está declarado y su regla de aciclicidad ya se verifica.
- **El intérprete sólo implementa la cardinalidad `exactly_one`.** Un `Topic`
  acuñado va a necesitar `at_least_one`.
- **Nada de esto depende de multi-base.** Todo vive en la base `neo4j`, porque
  el despliegue final va a Community.

---

## 9. Resumen de una pantalla

```powershell
# levantar y poblar
docker compose up -d
uv run python lab/scripts/load_backbone.py --reset

# verificar
uv run python lab/scripts/check_integrity.py
uv run pytest tests/ -q

# regenerar la documentación del esquema
uv run python lab/scripts/emit_tbox_diagram.py

# ver
start http://localhost:7474
```

Y en el Browser, la consulta que lo muestra todo:

```cypher
MATCH p = (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea)
RETURN p;
```
