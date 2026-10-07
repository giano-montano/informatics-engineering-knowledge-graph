# Revisión de la carga del backbone

**Fecha:** 2026-10-05 · **Commit revisado:** `1100451` · **Método:** solo
lectura del código y de la documentación; no se ejecutaron pruebas ni la carga.

**Estado:** atendida el 2026-10-07. Cada punto lleva su respuesta.

Es una foto de ese commit, no un documento vivo. Las contradicciones directas
están en `DEUDA_PRIMERA_IMPL_CARGA_BACKBONE.md` (D-01 a D-08) y aquí no se
repiten. Lo que sigue son observaciones de diseño, olores de código y una
opinión sobre la forma de las reglas. Ninguna es una decisión.

---

## 1. Lo que sí es coherente

Para no repetirlo en cada punto:

- **Esquema del grafo.** `graph_schema.py` reproduce las Tablas 1, 2 y 17. Los
  8 tipos de arista coinciden, con sus pares, la expansión de las uniones y la
  dirección afirmada. También las propiedades por etiqueta y el colapso de la
  partonomía.
- **Proyección.** Rechaza todo constructo sin fila en la Tabla 1, como pide la
  nota del anexo. También rechaza ninguna clase o dos clases (RI-03 en la
  carga), las inversas, las etiquetas sin idioma y una capa distinta de
  `reference`.
- **Orden de la carga.** Valida antes de tocar la base y deja el código 2 si
  rechaza. Las reglas de la carga coinciden con la Tabla 3 del anexo (RI-08
  queda solo para la auditoría).
- **Repositorio.** Las plantillas son de forma fija y se generan del esquema.
  Usan `MERGE` con `ON CREATE`, buscan los extremos por una etiqueta con
  restricción y comprueban los contadores (condición 3 del anexo). Exigen que
  la escritura institucional lleve procedencia y que la de referencia no la
  lleve.
- **Auditoría.** Hace una consulta por regla en una sola transacción de
  lectura y deja el reporte en SQLite, fuera del grafo, como pide ADR-007.
- **Pruebas negativas.** Hay una por cada forma de violar cada una de las 15
  reglas, como piden los estándares §6, y una prueba de que lo que escribe el
  repositorio no da falsos positivos.
- **C4.** Los componentes del núcleo y los comandos de construcción
  corresponden a los módulos.

**Respuesta:** sin cambios.

## 2. Olores y cosas que se verían raras en una sustentación

En orden de gravedad.

### 2.1 Las reglas no están unificadas

Lo que el sistema sabe de una regla está repartido en cinco sitios:

| Qué | Dónde |
|---|---|
| Código y enunciado | `core/rules.py` |
| Parámetros declarados como dato | `core/rules.py` (`REQUIRED_PARENT`, `ACYCLIC_EDGE_TYPES`) |
| Comprobación previa | `core/validator.py` (`_CHECKS`) |
| Qué reglas valida cada camino | `core/validator.py` (`LOAD_RULES`, `INGESTION_RULES`) |
| Consulta de auditoría | `core/auditor.py` (`_QUERIES`) |
| Qué regla impide la forma de la escritura | Solo en el docstring de `repository.py` |

Hay dos consecuencias concretas.

1. **La parametrización es desigual.** El anclaje y los ciclos sacaron sus
   parámetros a datos. Otras reglas, en cambio, los llevan escritos dentro de
   la consulta Cypher:
   - RM-03, la lista de clases que deben derivar de un recurso:
     `(n:Topic OR n:Concept OR n:Course)`;
   - RI-07, el par unidad → área;
   - RM-02, la dirección de la frontera.

   Esa desigualdad es lo que hace que «no todas están unificadas». Los nombres
   salen del esquema, pero la estructura de esas reglas no se declara en
   ningún sitio.

   **Respuesta:** la lista de RM-03 pasó a `rules.py`
   (`DERIVED_FROM_RESOURCE`). RI-07 y RM-02 siguen igual.
2. **El reparto de mecanismos (Tabla 3 del anexo y Tabla 21 de la tesis) no
   existe en el código salvo por las dos tuplas del validador.** Ninguna prueba
   puede comprobar que cada regla tenga, en cada camino, exactamente un
   mecanismo. Por eso D-02 y D-03 pasaron sin que nada fallara.

   **Respuesta:** ADR-014 lo declara como limitación. D-02 y D-03 están
   cerradas.

**Alternativa.** Un registro de reglas: un objeto inmutable por regla, con
código, enunciado, origen, el mecanismo por camino (carga, ingesta) y,
opcionalmente, la comprobación y la consulta. Sobre él se pueden probar las
Tablas 3 y 20:

- toda regla tiene un mecanismo por camino;
- las que dicen «validador» tienen comprobación;
- las que dicen «no aplica» llevan su motivo.

Ver §3.

**Respuesta:** el registro no se decidió; queda abierto.

### 2.2 `write_batch` toma la capa de referencia por omisión

`GraphRepository.write_batch(..., layer=REFERENCE, provenance=None)` hace que,
si la ingesta olvida pasar la capa, escriba hechos institucionales como
referencia y sin procedencia. La comprobación de la línea 374 no lo detecta:
`reference` sin procedencia es una combinación válida. La auditoría tampoco lo
detectaría:

- RM-03 solo mira nodos institucionales;
- RM-01 acepta `reference`.

`write_batch_in` ya exige `layer`. Que el método público no lo exija es una
asimetría sin motivo. Lo natural es quitar el valor por omisión.

**Respuesta:** hecho: `write_batch` exige `layer`.

### 2.3 El patrón del localizador no significa lo mismo en Python que en Cypher

`graph_schema.py:107-110` afirma que el mismo patrón sirve a `re.fullmatch` y
a `=~`. Hay un caso en el que no:

- Cypher usa la sintaxis de expresiones regulares de Java (documentación
  oficial de Neo4j). En Java, `\s` es solo espacio ASCII por omisión.
- En Python, sobre `str`, `\s` incluye el espacio Unicode, como U+00A0.

Un localizador con un espacio duro lo rechaza el validador y lo acepta la
auditoría. El validador es el más estricto, así que no produce un falso
negativo en la carga. Pero la afirmación del comentario es falsa, y cuando la
auditoría y el validador discrepan, AC-02 pierde fuerza. Basta con una clase
explícita, `[^ \t\n\r\f\v]` o similar, que valga igual en ambos motores.

**Respuesta:** pospuesto: los localizadores los acuña el sistema.

### 2.4 La consulta de ciclos de RM-04 enumera caminos

`MATCH (n) WHERE EXISTS { (n)-[:T*1..]->(n) }` termina, porque un camino no
repite aristas, como dice el anexo. Pero enumera caminos, no nodos. En un grafo
**sin** ciclos, que es el caso normal tras una ingesta correcta, `EXISTS` no
encuentra nada que lo corte y recorre todos los caminos desde cada nodo. En un
DAG de prerrequisitos con muchos rombos, eso crece exponencialmente.

Con el backbone no se nota: no tiene aristas de esos tipos. Con trece sílabos
de conceptos y prerrequisitos podría notarse. Hay que medirlo antes de la
ingesta, con un DAG sintético del tamaño esperado. Si duele, hay una forma
polinómica: para cada arista `a→b`, buscar con `shortestPath` un camino
`b→a` (búsqueda en anchura), y tratar los bucles aparte. Es una hipótesis sin
medir, no un hecho.

**Respuesta:** para la ingesta: se mide antes de ingestar.

### 2.5 Un conflicto de contenido termina como «fallida» en lugar de «rechazada»

ADR-010 separa *rechazada* (contenido) de *fallida* (ejecución), y solo la
rechazada alimenta la medida de AC-01. Dos casos de contenido terminan hoy
como excepción.

- **Mismo hecho, otra clase.** Si un lote trae `NodeFact(k, Topic)` y la
  instantánea tiene `k` como `KnowledgeUnit`, el validador usa la clase de la
  instantánea y descarta en silencio la del lote (`batch.py:label_of`).
  Después, el `MERGE (:Topic {key:k})` crea un segundo nodo con la misma
  clave, porque las restricciones son por etiqueta. El contador de nodos lo
  detecta, salta `WriteMismatch` y la corrida queda *fallida*, sin descarte.
- **Claves repetidas.** Un lote con claves repetidas lanza `ValueError` al
  construirse (`Batch.__post_init__`), antes de llegar al validador.

Ninguno de los dos afecta a la carga. Se vuelven relevantes con el extractor:
¿qué código de regla llevan esas violaciones?

**Respuesta:** el primer caso lo cubre el requisito anotado en la descripción del
extractor (`model.c4`). El segundo queda para el diseño de la ingesta.

### 2.6 RI-01 descansa en algo más que «la restricción de unicidad»

La Tabla 21 asigna RI-01 a la restricción de unicidad. En Community, esa
restricción es por etiqueta (8 restricciones), así que no impide que un
`Course` y un `ResourceType` compartan clave. La unicidad global descansa en
tres cosas:

1. la construcción de las claves (Tabla 4 del anexo: IRI en la capa de
   referencia y uuid en la institucional);
2. el `MERGE` por clave;
3. la comprobación de contadores del repositorio.

Hay un supuesto débil. ADR-009 deriva las claves del curso y del tipo de
recurso de su código y de su nombre. Si la derivación no distingue la clase
(por ejemplo, un uuid5 con el mismo espacio de nombres para ambas), la
colisión deja de ser «imposible por construcción». Es una pregunta para cuando
se diseñe la derivación de claves.

**Respuesta:** para el diseño de la derivación de claves, con la ingesta.

### 2.7 La carga escribe primero y audita después lo que podría rechazar antes

`LOAD_RULES` excluye RI-08 porque así lo dice la Tabla 3 del anexo. Pero el
motivo del anexo («HermiT no detecta ausencias bajo mundo abierto») explica
por qué **R2** no cubre la regla, no por qué la **carga** no debería
impedirla. La comprobación ya existe y no cuesta nada aplicarla.

Con ella, un backbone con una unidad huérfana se rechazaría antes de vaciar
la base (código 2). Sin ella, se escribe y cierra la compuerta (código 1). Lo
mismo vale para RI-07 si se agrega su comprobación (D-01). Cambiarlo toca la
Tabla 3 del anexo, así que va en un ADR nuevo.

**Respuesta:** no se atiende, con el mismo criterio que D-01. La Tabla 3 queda como
está.

### 2.8 Errores sin capturar al final de la carga

`repository.count_elements()` (línea 113) y `OperationalStore(...)` (línea
124) están fuera de todo `try`. Un fallo ahí deja una traza de Python en lugar
de un mensaje y un código de salida. Esto se relaciona con D-04.

**Respuesta:** resuelto con D-04.

### 2.9 `reset()` borra todos los índices

Hoy no hay otros, así que no hace daño. Pero la búsqueda por nombre de la
navegación (rutas de navegación del C4) probablemente necesite un índice de
texto completo. `reset()` lo borraría en cada carga. Cuando exista, debe
declararse en el esquema del grafo y crearse en la carga, junto con las
restricciones.

**Respuesta:** para la navegación, cuando exista el índice.

### 2.10 `docker-compose.yml` sigue siendo el del laboratorio

Lo delatan cuatro cosas:

- el nombre del proyecto, `iekg-lab`;
- el comentario «Neo4j del laboratorio»;
- los plugins APOC y GDS, que el código no usa;
- `procedures_unrestricted` abierto para ambos.

El `pyproject.toml` declara el principio contrario: «una dependencia declarada
y no usada es una decisión tomada por inercia». La edición Enterprise en
desarrollo es una decisión conocida, pero tiene un costo: ninguna prueba
demuestra que el núcleo corra en Community. Revisé las construcciones que usa
el núcleo, como `CALL () { }`, `IS :: STRING`, `SHOW CONSTRAINTS` y las
restricciones de unicidad, y ninguna es exclusiva de Enterprise según la
documentación. Aun así, conviene una corrida contra la imagen Community antes
del despliegue.

**Respuesta:** hecho: el proyecto se llama `iekg`, sin plugins ni permisos, y con el
comentario corregido. La corrida contra Community queda para el despliegue.

### 2.11 Menores

- **`REQUIRED_PARENT` repite los tres pares de `ADMITTED_PAIRS[PART_OF]`.**
  Que sea explícito es correcto: viene de otro axioma, la restricción
  existencial, no del dominio y el rango. Pero ninguna prueba exige que cada
  padre requerido sea un par admitido. **Respuesta:** sin atender.
- **Los enunciados de `STATEMENTS` parafrasean en inglés las tablas en
  español.** Es aceptable por los estándares, porque la consola va en inglés,
  pero pueden desalinearse. Conviene citar la tabla de origen.
  **Respuesta:** sin atender.
- **`Tx = Transaction | ManagedTransaction` está definido en dos módulos.**
  **Respuesta:** sin atender.
- **ADR-011 pide en la instantánea «clave, etiqueta, clase, área y capa».**
  `SnapshotNode` tiene clase y capa, que es lo que necesita el validador. Lo
  que necesita el extractor llegará con la lectura desde la base.
  **Respuesta:** para la ingesta.
- **La prueba de la declaración contra el TTL (ADR-008) sigue pendiente.**
  `check_tbox` comprueba qué tipos de constructo aparecen, no su contenido.
  **Respuesta:** sigue pendiente, como prevé ADR-008.

## 3. Opinión: ¿YAML, SHACL o código?

### Lo que exige la restricción del asesor

La restricción pide «especificación declarativa más intérprete pequeño; nada
hardcodeado». No prescribe formato. La pregunta es qué parte del sistema es la
especificación y qué parte el intérprete, y si lo que queda fuera de la
especificación se puede defender.

**Lo que hoy es especificación declarativa:** el esquema del grafo, es decir,
etiquetas, tipos de arista, pares, propiedades y capas. Las plantillas de
escritura y buena parte de las consultas (RI-02, 03, 04, 05, 06, 09, 10 y
RM-01) se generan o se parametrizan desde él. En esa parte, el diseño cumple
bien la restricción.

**Lo que no:** el catálogo de reglas como tal y la estructura de cinco de
ellas (RI-07, RI-08, RM-02, RM-03 y RM-04). Eso es código.

### Las opciones

**YAML para las reglas.** No lo recomiendo. Para el esquema, el argumento de
ADR-008 («solo lo lee Python») sigue valiendo. Para las reglas es peor, porque
cinco de ellas tienen estructura (anclaje, ciclos, frontera, procedencia,
funcionalidad). Para expresarlas en YAML hay dos caminos:

- un mini-lenguaje propio, con un intérprete que hay que escribir, probar y
  defender. El laboratorio tenía 11 reglas así;
- incrustar Cypher como texto dentro del YAML, que es código disfrazado de
  configuración.

Ninguno reduce lo que hay que defender.

**SHACL.** Es el estándar W3C para restricciones en mundo cerrado sobre RDF:
Recomendación de 2017. SHACL 1.2 Core sigue como borrador de trabajo en 2026.
Es lo que un jurado de ingeniería del conocimiento esperaría ver mencionado.
Tiene ventajas y costos reales.

- **Ventaja.** Formas SHACL sobre el **TTL del backbone**, validadas con
  pySHACL antes de proyectar, cubrirían justo lo que HermiT no ve bajo mundo
  abierto: ausencias (RI-08) y conteos (RI-07). Le darían a R2 una validación
  en mundo cerrado con un estándar.
- **Costo 1.** No valida el grafo de propiedades salvo con n10s. n10s es un
  plugin de Neo4j Labs, sin soporte comercial y con compatibilidad de
  versiones que hay que verificar, y ADR-002 ya lo descartó para la
  proyección.
- **Costo 2.** SHACL Core no expresa aciclicidad. RM-04 exigiría
  SHACL-SPARQL.
- **Costo 3.** El validador de la ingesta trabaja sobre un lote y una
  instantánea en memoria, no sobre RDF.
- **Costo 4.** Las reglas pasarían a vivir en tres lenguajes en lugar de dos.

**Graph types de GQL.** Son exclusivos de Enterprise, solo existen en Cypher
25 y llegaron en Neo4j 2026.02. Ya están descartados en ADR-002 y ADR-005, y
la razón sigue vigente.

### Recomendación

Mantener las reglas como código en Python y Cypher, pero:

1. **Registrar las alternativas que faltan (D-06).** ADR-008 ya deja la
   lógica de las reglas en el código. Falta escribir qué parte es
   especificación (el esquema y el catálogo de reglas con sus mecanismos) y
   qué parte es intérprete (las plantillas, las comprobaciones y las
   consultas), y registrar YAML para las reglas y SHACL como alternativas
   descartadas, con sus motivos reales.

   **Respuesta:** hecho en ADR-014. No usa la compatibilidad de n10s como
   motivo, porque n10s publicó la 5.26.0. El motivo sobre la aciclicidad lo
   apoya en la Recomendación W3C de 2017.
2. **Unificar las reglas en un registro (§2.1).** El catálogo de reglas pasa
   a ser dato declarativo: qué regla, de dónde viene, qué mecanismo la impide
   en cada camino. Las Tablas 3 y 20 se vuelven comprobables. Así se responde
   al asesor sin un lenguaje nuevo: lo declarativo es *qué se cumple y quién
   lo garantiza*. El *cómo se comprueba*, para 15 reglas, es más corto y más
   fácil de defender como código que como un intérprete genérico.

   **Respuesta:** no se decidió; queda abierto.
3. **Dejar SHACL sobre el TTL como trabajo futuro o como extensión de R2.**
   Sirve como respuesta a la pregunta previsible del jurado: «¿por qué no
   SHACL?».

   **Respuesta:** hecho: ADR-014 lo registra como alternativa descartada y
   como trabajo futuro.

## 4. Fuentes

Sustentables (documentación oficial y estándares):

- Neo4j, *String operators* (Cypher Manual): `=~` usa la sintaxis de Java.
  <https://neo4j.com/docs/cypher-manual/current/expressions/predicates/string-operators/>
- Neo4j, *Graph types* (Cypher Manual 25): Cypher 25, Enterprise, desde
  2026.02. <https://neo4j.com/docs/cypher-manual/current/schema/graph-types/>
- W3C, *SHACL 1.2 Core*, borrador de trabajo (historial).
  <https://www.w3.org/standards/history/shacl12-core/>

Documentación oficial de un proyecto de Neo4j Labs, sin soporte comercial.
Sirve para describir la herramienta, con esa salvedad:

- Neo4j Labs, *Validating Neo4j graphs against SHACL* (neosemantics 5.14).
  <https://neo4j.com/labs/neosemantics/5.14/validation/>

Fuente gris, solo para decidir qué probar:

- Foro de la comunidad de Neo4j: incompatibilidades de versión de n10s con
  Neo4j 5.27. <https://community.neo4j.com/t/neosemantics-in-neo4j-desktop/73017>

No verificado con una fuente, por depender del comportamiento de Python y Java
y no haberse ejecutado nada en esta revisión: la diferencia de `\s` entre
ambos motores (§2.3). Se comprueba con dos líneas en cada motor.
